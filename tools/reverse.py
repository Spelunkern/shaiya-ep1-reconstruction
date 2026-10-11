#!/usr/bin/env python3
"""Reproducible inventory, Ghidra baseline and community work units (stdlib only)."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tarfile

if __package__:
    from . import partition
else:
    import partition
merge_ranges = partition.merge_ranges
subtract = partition.subtract
chunks = partition.chunks

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ('Client', 'Server')
PINNED_GHIDRA = '12.1.4'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def rows(path):
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def inventory():
    return read(ROOT / 'manifests/originals.json')


def pe_info(path):
    """Parse section/file ownership without executing original programs."""
    with path.open('rb') as f:
        if f.read(2) != b'MZ':
            return None
        f.seek(0x3c)
        off = struct.unpack('<I', f.read(4))[0]
        f.seek(off)
        if f.read(4) != b'PE\0\0':
            return None
        coff = f.read(20)
        machine, nsections, timestamp, _, _, optsize, flags = struct.unpack('<HHIIIHH', coff)
        optional = f.read(optsize)
        magic = struct.unpack_from('<H', optional)[0]
        if magic not in (0x10b, 0x20b):
            raise ValueError('Unsupported PE optional header')
        base = struct.unpack_from('<I' if magic == 0x10b else '<Q', optional, 28 if magic == 0x10b else 24)[0]
        sections = []
        for _ in range(nsections):
            section = f.read(40)
            name = section[:8].split(b'\0', 1)[0].decode('ascii', 'replace')
            vs, va, rs, rp = struct.unpack_from('<IIII', section, 8)
            characteristics = struct.unpack_from('<I', section, 36)[0]
            if rp + rs > path.stat().st_size:
                raise ValueError(f'Truncated PE section {name}')
            sections.append(dict(name=name, rva=va, virtual_size=vs, raw_size=rs,
                                 raw_offset=rp, executable=bool(characteristics & 0x20000000),
                                 characteristics=characteristics))
        return dict(machine=machine, bits=32 if magic == 0x10b else 64,
                    image_base=base, entry_rva=struct.unpack_from('<I', optional, 16)[0],
                    image_size=struct.unpack_from('<I', optional, 56)[0],
                    headers_size=struct.unpack_from('<I', optional, 60)[0],
                    coff_timestamp=timestamp, dll=bool(flags & 0x2000), sections=sections)


def cmd_inventory(args):
    target = ROOT / 'manifests/originals.json'
    if target.exists():
        raise ValueError('Inventory already frozen. A new corpus requires a separate baseline/repository.')
    files = []
    unique = {}
    for folder in ORIGINALS:
        if not (ROOT / folder).is_dir():
            raise ValueError(f'Missing original folder: {folder}')
        for p in sorted((ROOT / folder).rglob('*')):
            if not p.is_file():
                continue
            if p.is_symlink():
                raise ValueError(f'Symlink in originals: {p}')
            record = dict(path=p.relative_to(ROOT).as_posix(), size=p.stat().st_size, sha256=sha(p))
            pe = pe_info(p)
            if pe:
                record['pe'] = pe
                digest = record['sha256']
                record['binary_id'] = digest[:16]
                unique.setdefault(digest, dict(binary_id=digest[:16], sha256=digest, paths=[], pe=pe))['paths'].append(record['path'])
            files.append(record)
    binaries = sorted(unique.values(), key=lambda x: x['paths'][0])
    if len({b['binary_id'] for b in binaries}) != len(binaries):
        raise ValueError('Short binary hash collision')
    write(target, dict(schema=1, files=files, binaries=binaries))
    print(f'Frozen {len(files)} files; {sum(x["size"] for x in files):,} bytes; '
          f'{sum("pe" in x for x in files)} PE paths, {len(binaries)} unique binaries')


def verify_originals(binary_only=False):
    manifest = inventory()
    files = [f for f in manifest['files'] if not binary_only or 'pe' in f]
    for item in files:
        p = ROOT / item['path']
        if not p.is_file() or p.is_symlink() or p.stat().st_size != item['size'] or sha(p) != item['sha256']:
            raise ValueError(f'Original missing or changed: {item["path"]}')
    if not binary_only:
        expected = {f['path'] for f in files}
        actual = {p.relative_to(ROOT).as_posix() for folder in ORIGINALS for p in (ROOT / folder).rglob('*') if p.is_file()}
        if actual != expected:
            raise ValueError(f'Corpus file set changed: {sorted(actual ^ expected)}')
    return manifest


def cmd_verify(args):
    m = verify_originals(args.binaries_only)
    print(f'PASS originals ({len(m["binaries"])} unique binaries)')


def choose_binary(value):
    matches = [b for b in inventory()['binaries'] if b['binary_id'] == value or value in b['paths']]
    if len(matches) != 1:
        raise ValueError('Use an exact binary_id or corpus-relative path')
    return matches[0]


def tool_env(args):
    ghidra = Path(args.ghidra or os.environ.get('GHIDRA_HOME', ''))
    jdk = Path(args.jdk or os.environ.get('JAVA_HOME', ''))
    if not (ghidra / 'support/analyzeHeadless').is_file() or not (jdk / 'bin/java').is_file():
        raise ValueError('Set GHIDRA_HOME and JAVA_HOME, or pass --ghidra and --jdk')
    release = (jdk / 'release').read_text()
    if 'JAVA_VERSION="21.' not in release:
        raise ValueError('Use JDK 21 for the pinned analysis environment')
    props = (ghidra / 'Ghidra/application.properties').read_text()
    if f'application.version={PINNED_GHIDRA}\n' not in props:
        raise ValueError(f'Baseline requires Ghidra {PINNED_GHIDRA}')
    env = dict(os.environ, JAVA_HOME=str(jdk.resolve()))
    env['PATH'] = str(jdk.resolve() / 'bin') + os.pathsep + env.get('PATH', '')
    return ghidra.resolve(), env


def cmd_analyze(args):
    verify_originals(True)
    ghidra, env = tool_env(args)
    binaries = [choose_binary(args.binary)] if args.binary else inventory()['binaries']
    for b in binaries:
        bid = b['binary_id']
        out = ROOT / 'analysis/baseline' / bid
        projects = ROOT / 'work/ghidra'
        frozen = (out / 'summary.json').exists()
        if frozen:
            validate_export(b)
            if (projects / f'{bid}.gpr').exists():
                print(f'SKIP frozen baseline {b["paths"][0]}', flush=True)
                continue
        export_out = ROOT / 'work/reexports' / bid if frozen else out
        projects.mkdir(parents=True, exist_ok=True)
        # Never overwrite annotated projects. Incomplete attempts must be moved aside by a maintainer.
        if (projects / f'{bid}.gpr').exists():
            raise ValueError(f'Incomplete project exists for {bid}; inspect logs and move it aside before retry')
        logs = ROOT / 'work/logs'
        logs.mkdir(parents=True, exist_ok=True)
        command = [str(ghidra / 'support/analyzeHeadless'), str(projects), bid,
                   '-import', str(ROOT / b['paths'][0]), '-max-cpu', '4',
                   '-analysisTimeoutPerFile', str(args.timeout), '-scriptPath', str(ROOT / 'tools/ghidra'),
                   '-postScript', 'ExportBaseline.java', str(export_out), '-log', str(logs / f'{bid}.log')]
        if frozen:
            for name in ('functions.jsonl', 'summary.json'):
                (export_out / name).unlink(missing_ok=True)
        print(f'ANALYZE {b["paths"][0]} ({bid})', flush=True)
        with (logs / f'{bid}.console.log').open('w') as console:
            subprocess.run(command, env=env, check=True, stdout=console, stderr=subprocess.STDOUT)
        if frozen:
            for name in ('functions.jsonl', 'summary.json'):
                if not (export_out / name).exists() or sha(export_out / name) != sha(out / name):
                    raise ValueError(f'Regenerated analysis differs from frozen baseline: {bid}/{name}')
        validate_export(b)
        print(f'PASS {read(out / "summary.json")["function_count"]} functions', flush=True)


def mapped_bytes(data, pe, start, end):
    result = bytearray()
    while start < end:
        if start < pe['headers_size']:
            stop = min(end, pe['headers_size'])
            result.extend(data[start:stop])
        else:
            section = next((s for s in pe['sections'] if s['rva'] <= start < s['rva'] + max(s['virtual_size'], s['raw_size'])), None)
            if section is None:
                raise ValueError(f'Unmapped function RVA {start:x}')
            offset = start - section['rva']
            stop = min(end, section['rva'] + max(section['virtual_size'], section['raw_size']))
            raw_n = max(0, min(stop - start, section['raw_size'] - offset))
            file_start = section['raw_offset'] + offset
            result.extend(data[file_start:file_start + raw_n])
            result.extend(b'\0' * (stop - start - raw_n))
        start = stop
    return bytes(result)


def validate_export(b, original_bytes=False):
    out = ROOT / 'analysis/baseline' / b['binary_id']
    summary = read(out / 'summary.json')
    if summary['program_sha256'].lower() != b['sha256'] or summary['image_base'] != b['pe']['image_base']:
        raise ValueError('Export identity mismatch')
    if summary['analysis_timed_out'] or summary['ghidra_version'] != PINNED_GHIDRA:
        raise ValueError('Timed out or incompatible analysis')
    funcs = list(rows(out / 'functions.jsonl'))
    entries = [f['entry_rva'] for f in funcs]
    if len(funcs) != summary['function_count'] or len(set(entries)) != len(entries):
        raise ValueError('Incomplete/duplicate function export')
    for f in funcs:
        if not f['ranges'] or not any(a <= f['entry_rva'] < z for a, z in f['ranges']):
            raise ValueError('Entry outside function body')
        previous = -1
        for a, z in f['ranges']:
            if a < 0 or z <= a or a < previous:
                raise ValueError('Invalid/overlapping function body ranges')
            previous = z
    if original_bytes:
        data = (ROOT / b['paths'][0]).read_bytes()
        for f in funcs:
            digest = hashlib.sha256()
            for a, z in f['ranges']:
                digest.update(mapped_bytes(data, b['pe'], a, z))
            if digest.hexdigest() != f['body_sha256']:
                raise ValueError(f'Function bytes differ from original: {b["binary_id"]}/{f["entry_rva"]:x}')
    return funcs


def make_plan():
    return partition.make_plan(ROOT, inventory(), validate_export, PINNED_GHIDRA)


def cmd_plan(args):
    lock = ROOT / 'blocks/baseline.json'
    if lock.exists():
        raise ValueError('Plan is frozen. Use audit; boundary changes need a new baseline and explicit migration.')
    verify_originals(True)
    for binary in inventory()['binaries']:
        validate_export(binary, original_bytes=True)
    blocks, baseline = make_plan()
    p = ROOT / 'blocks/catalog.jsonl'
    with p.open('w', encoding='utf-8') as f:
        for block in blocks:
            f.write(json.dumps(block, ensure_ascii=False, separators=(',', ':')) + '\n')
    baseline['catalog_sha256'] = sha(p)
    write(lock, baseline)
    print(f'Frozen baseline {baseline["baseline_id"]}: {len(blocks)} blocks')


def load_blocks():
    return list(rows(ROOT / 'blocks/catalog.jsonl'))


def choose_block(bid):
    matches = [b for b in load_blocks() if b['id'] == bid]
    if len(matches) != 1:
        raise ValueError('Unknown block ID')
    return matches[0]


def cmd_audit(args):
    blocks, candidate = make_plan()
    frozen = read(ROOT / 'blocks/baseline.json')
    digest = hashlib.sha256()
    for block in blocks:
        digest.update((json.dumps(block, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
    if candidate['baseline_id'] != frozen['baseline_id'] or digest.hexdigest() != frozen['catalog_sha256']:
        raise ValueError('Baseline inputs or catalog drifted')
    if sha(ROOT / 'blocks/catalog.jsonl') != frozen['catalog_sha256']:
        raise ValueError('Catalog digest mismatch')
    if args.originals:
        verify_originals(True)
        for b in inventory()['binaries']:
            validate_export(b, original_bytes=True)
        print('PASS all function body digests match original bytes')
    print(f'PASS deterministic catalog ({len(blocks)} blocks)')


def needs_boundary_review(block):
    return block.get('shared_body', False) or bool(block.get('unresolved_calls_rva'))


def cmd_list(args):
    if args.limit < 1:
        raise ValueError('Limit must be positive')
    binary_id = choose_binary(args.binary)['binary_id'] if args.binary else None
    count = 0
    for b in load_blocks():
        if args.kind and b['kind'] != args.kind or binary_id and b['binary_id'] != binary_id:
            continue
        if args.max_instructions is not None and b.get('instruction_count', 10**12) > args.max_instructions:
            continue
        if args.no_dependencies and b['dependencies']:
            continue
        if args.available and ((ROOT / 'claims' / (b['id'] + '.json')).exists() or (ROOT / 'contributions' / b['id']).exists() or needs_boundary_review(b)):
            continue
        print(b['id'], b['kind'], b.get('instruction_count', ''), b.get('name', b.get('section', '')))
        count += 1
        if count >= args.limit:
            break


def cmd_show(args):
    print(json.dumps(choose_block(args.block), ensure_ascii=False, indent=2))


def cmd_claim(args):
    if not args.owner.strip():
        raise ValueError('Owner must not be empty')
    b = choose_block(args.block)
    if needs_boundary_review(b):
        raise ValueError('Function has shared bytes or unresolved outgoing branches/calls; maintainer must resolve boundaries first')
    now = dt.datetime.now(dt.timezone.utc)
    claim = dict(block_id=b['id'], baseline_id=b['baseline_id'], owner=args.owner,
                 created_at=now.isoformat(), expires_at=(now + dt.timedelta(days=7)).isoformat())
    p = ROOT / 'claims' / (b['id'] + '.json')
    with p.open('x', encoding='utf-8') as f:
        f.write(json.dumps(claim, indent=2) + '\n')
    print('Local reservation created; submit its PR for central acceptance before doing the block.')


def cmd_start(args):
    b = choose_block(args.block)
    if needs_boundary_review(b):
        raise ValueError('Function boundaries or outgoing direct flow remain unresolved')
    claim_path = ROOT / 'claims' / (b['id'] + '.json')
    if not claim_path.exists() or read(claim_path)['owner'] != args.owner:
        raise ValueError('Create/obtain the accepted reservation for this owner first')
    claim = read(claim_path)
    if claim.get('baseline_id') != b['baseline_id'] or claim.get('block_id') != b['id']:
        raise ValueError('Reservation belongs to a different baseline/block')
    if claim_time(claim['expires_at']) <= dt.datetime.now(dt.timezone.utc):
        raise ValueError('Reservation expired; maintainer must renew it')
    directory = ROOT / 'contributions' / b['id']
    directory.mkdir(exist_ok=False)
    write(directory / 'submission.json', dict(schema=1, block_id=b['id'], baseline_id=b['baseline_id'],
            binary_sha256=b['binary_sha256'], owner=args.owner, status='draft', source_files=[],
            evidence_files=[], test_files=[], abi={}, dependency_contracts=[], unknowns=['Analysis not started']))
    (directory / 'analysis.md').write_text('# Evidence and reasoning\n\nRecord addresses, observed behavior, hypotheses and unresolved questions.\n')
    (directory / 'tests').mkdir()
    print(directory)


def cmd_export(args):
    b = choose_block(args.block)
    if b['kind'] != 'function':
        raise ValueError('Decompiler export applies only to function blocks; inspect data/regions directly in Ghidra')
    binary = choose_binary(b['binary_id'])
    verify_originals(True)
    ghidra, env = tool_env(args)
    projects = ROOT / 'work/ghidra'
    if not (projects / (b['binary_id'] + '.gpr')).exists():
        raise ValueError('Missing local Ghidra project. Run analyze to regenerate it on a fresh clone.')
    out = ROOT / 'work/evidence' / b['id']
    out.mkdir(parents=True, exist_ok=True)
    for name in ('listing.txt', 'decompiled.c'):
        (out / name).unlink(missing_ok=True)
    subprocess.run([str(ghidra / 'support/analyzeHeadless'), str(projects), b['binary_id'],
                    '-process', Path(binary['paths'][0]).name, '-noanalysis', '-readOnly',
                    '-scriptPath', str(ROOT / 'tools/ghidra'), '-postScript', 'ExportBlock.java',
                    hex(b['entry_rva']), str(out), b['binary_sha256'], b['body_sha256']], env=env, check=True)
    if not all((out / p).is_file() for p in ('listing.txt', 'decompiled.c')):
        raise ValueError('Ghidra returned without the requested evidence')
    print(out)


def local_files(directory, values):
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values) or len(values) != len(set(values)):
        raise ValueError('File lists must contain unique relative paths')
    found = []
    for name in values:
        rel = Path(name)
        p = directory / rel
        if rel.is_absolute() or '..' in rel.parts or not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f'Invalid contribution path: {name}')
        if p.stat().st_size == 0:
            raise ValueError(f'Empty evidence/source/test file: {name}')
        found.append(p)
    return found


def validate_submission(directory, by_id):
    submission = read(directory / 'submission.json')
    block = by_id.get(directory.name)
    if not block or submission.get('block_id') != directory.name:
        raise ValueError('Submission is not bound to a catalog block')
    if submission.get('schema') != 1 or submission.get('baseline_id') != block['baseline_id'] or submission.get('binary_sha256') != block['binary_sha256']:
        raise ValueError('Submission baseline/binary identity mismatch')
    if block.get('shared_body'):
        raise ValueError('Submission overlaps another function body')
    if not isinstance(submission.get('owner'), str) or not submission['owner'].strip():
        raise ValueError('Missing owner')
    if submission.get('status') not in ('draft', 'ready'):
        raise ValueError('Only draft/ready are contributor statuses; review is separate')
    for key in ('source_files', 'evidence_files', 'test_files'):
        local_files(directory, submission.get(key))
    if not isinstance(submission.get('unknowns'), list) or not isinstance(submission.get('dependency_contracts'), list) or not isinstance(submission.get('abi'), dict):
        raise ValueError('Invalid unknowns/contracts/ABI fields')
    if submission['status'] == 'ready':
        if needs_boundary_review(block):
            raise ValueError('Ready submission has unresolved function boundaries/outgoing direct flow')
        if submission['unknowns']:
            raise ValueError('Ready submission still has unresolved questions')
        if not submission['source_files'] or not submission['evidence_files'] or not submission['test_files'] or not (directory / 'analysis.md').is_file():
            raise ValueError('Ready submission needs evidence, tests and reasoning')
        if block['kind'] == 'function':
            if not submission['source_files'] or not all(submission['abi'].get(k) for k in ('calling_convention', 'parameters', 'return', 'side_effects')):
                raise ValueError('Function needs source and a complete ABI contract (use explicit none/void where appropriate)')
        contracts = submission['dependency_contracts']
        if any(not isinstance(c, dict) or not c.get('block_id') or not c.get('contract') for c in contracts):
            raise ValueError('Dependencies need explicit contracts')
        if {c['block_id'] for c in contracts} != set(block['dependencies']):
            raise ValueError('Dependency contracts differ from catalog call edges')
    return submission


def claim_time(value):
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('Reservation timestamps must include timezone')
    return parsed


def cmd_validate(args):
    by_id = {b['id']: b for b in load_blocks()}
    dirs = [ROOT / 'contributions' / choose_block(args.block)['id']] if args.block else sorted(p for p in (ROOT / 'contributions').iterdir() if p.is_dir())
    for directory in dirs:
        if directory.is_symlink():
            raise ValueError('Symlink contribution directory')
        s = validate_submission(directory, by_id)
        claim_path = ROOT / 'claims' / (directory.name + '.json')
        if not claim_path.is_file() or read(claim_path).get('owner') != s['owner']:
            raise ValueError('Submission must belong to the reserved owner')
        print(f'PASS structure {directory.name} ({s["status"]}); correctness requires review')
    for p in (ROOT / 'claims').glob('*.json'):
        c = read(p)
        b = by_id.get(p.stem)
        if not b or c.get('block_id') != p.stem or c.get('baseline_id') != b['baseline_id'] or not c.get('owner'):
            raise ValueError(f'Invalid claim {p.name}')
        if claim_time(c['created_at']) >= claim_time(c['expires_at']):
            raise ValueError('Claim expiration precedes creation')
    for p in (ROOT / 'reviews').glob('*.json'):
        if p.stem not in by_id:
            raise ValueError('Review refers to an unknown block')
        directory = ROOT / 'contributions' / p.stem
        submission = validate_submission(directory, by_id)
        validate_review(read(p), by_id[p.stem], submission, directory)
    print(f'PASS submission structure ({len(dirs)} submissions)')


def submission_digest(directory, submission):
    names = sorted(set(['submission.json', 'analysis.md'] + submission['source_files'] + submission['evidence_files'] + submission['test_files']))
    files = local_files(directory, names)
    content = {p.relative_to(directory).as_posix(): sha(p) for p in files}
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_review(record, block, submission, directory):
    if submission['status'] != 'ready' or record.get('schema') != 1:
        raise ValueError('Review requires a ready submission')
    if record.get('block_id') != block['id'] or record.get('baseline_id') != block['baseline_id']:
        raise ValueError('Review identity mismatch')
    if record.get('submission_digest') != submission_digest(directory, submission):
        raise ValueError('Review is stale after contribution changes')
    if not record.get('reviewer') or record['reviewer'] == submission['owner']:
        raise ValueError('An independent reviewer is required')
    if record.get('stage') not in ('source_reviewed', 'block_validated', 'integrated'):
        raise ValueError('Invalid review stage')
    proof_name = record.get('proof_file')
    if proof_name not in submission['evidence_files']:
        raise ValueError('Review proof must be declared in evidence_files')
    proof = read(local_files(directory, [proof_name])[0])
    if not proof.get('environment') or not proof.get('reasoning'):
        raise ValueError('Review proof needs environment and reasoning')
    if record['stage'] in ('block_validated', 'integrated'):
        for key in ('build', 'comparison'):
            result = proof.get(key, {})
            if result.get('result') != 'pass' or not result.get('command') or result.get('log') not in submission['evidence_files']:
                raise ValueError('Validation requires successful build/comparison commands and declared logs')
        if proof['comparison'].get('original_sha256') != block['binary_sha256'] or not proof['comparison'].get('cases') or not proof['comparison'].get('method'):
            raise ValueError('Comparison must identify the original and test cases')
        if record['stage'] == 'integrated' and proof.get('integration', {}).get('result') != 'pass':
            raise ValueError('Integrated status requires whole-binary integration evidence')
        if record['stage'] == 'integrated' and (not proof['integration'].get('command') or proof['integration'].get('log') not in submission['evidence_files']):
            raise ValueError('Integration command/log missing')
    return record


def cmd_review(args):
    block = choose_block(args.block)
    directory = ROOT / 'contributions' / block['id']
    submission = validate_submission(directory, {block['id']: block})
    record = dict(schema=1, block_id=block['id'], baseline_id=block['baseline_id'],
                  reviewer=args.reviewer, stage=args.stage, proof_file=args.proof,
                  submission_digest=submission_digest(directory, submission))
    validate_review(record, block, submission, directory)
    write(ROOT / 'reviews' / (block['id'] + '.json'), record)
    print('Review evidence recorded locally; maintainer acceptance on the canonical branch is required.')


def cmd_report(args):
    blocks = load_blocks()
    baseline = read(ROOT / 'blocks/baseline.json')
    status = {'draft': 0, 'ready': 0}
    reviews = {'source_reviewed': 0, 'block_validated': 0, 'integrated': 0}
    by_id = {b['id']: b for b in blocks}
    for d in (ROOT / 'contributions').iterdir():
        if d.is_dir():
            s = validate_submission(d, by_id)
            status[s['status']] += 1
            review_path = ROOT / 'reviews' / (d.name + '.json')
            if review_path.exists():
                reviewed = validate_review(read(review_path), by_id[d.name], s, d)
                reviews[reviewed['stage']] += 1
    counts = {k: sum(b['kind'] == k for b in blocks) for k in ('function', 'data', 'unclassified', 'integration')}
    print(json.dumps(dict(baseline_id=baseline['baseline_id'], blocks=len(blocks), kinds=counts,
                         submissions=status, reviews=reviews,
                         functions_requiring_boundary_review=sum(b['kind'] == 'function' and needs_boundary_review(b) for b in blocks),
                         reconstructed_verified_blocks=reviews['block_validated'] + reviews['integrated'],
                         measurement='Counts record accepted evidence, not a proof of complete semantic equivalence. Read review limitations.',
                         binaries=[{k: v for k, v in b.items() if k != 'shared_body_ranges'} | {'shared_body_ranges':len(b['shared_body_ranges'])} for b in baseline['binaries']]), indent=2))


def cmd_bundle(args):
    verify_originals()
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    output = dist / 'shaiya-ep1-originals.tar'
    if output.exists():
        raise ValueError('Bundle already exists; move it aside to rebuild')
    with tarfile.open(output, 'w') as archive:
        for item in inventory()['files']:
            archive.add(ROOT / item['path'], arcname=item['path'], recursive=False)
        archive.add(ROOT / 'manifests/originals.json', arcname='manifests/originals.json')
    write(dist / 'originals-bundle.json', dict(file=output.name, size=output.stat().st_size, sha256=sha(output)))
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, func in [('inventory',cmd_inventory), ('plan',cmd_plan), ('audit',cmd_audit), ('report',cmd_report), ('bundle',cmd_bundle)]:
        commands.add_parser(name).set_defaults(func=func)
    commands.choices['audit'].add_argument('--originals', action='store_true')
    p = commands.add_parser('verify'); p.add_argument('--binaries-only', action='store_true'); p.set_defaults(func=cmd_verify)
    p = commands.add_parser('analyze'); p.add_argument('--binary'); p.add_argument('--timeout',type=int,default=1800); p.set_defaults(func=cmd_analyze)
    for name, func in [('export',cmd_export)]:
        p = commands.add_parser(name); p.add_argument('block'); p.set_defaults(func=func)
    for name in ('analyze','export'):
        p = commands.choices[name]; p.add_argument('--ghidra'); p.add_argument('--jdk')
    p = commands.add_parser('list'); p.add_argument('--binary'); p.add_argument('--kind',choices=['function','data','unclassified','integration']); p.add_argument('--available',action='store_true'); p.add_argument('--limit',type=int,default=20); p.add_argument('--max-instructions',type=int); p.add_argument('--no-dependencies',action='store_true'); p.set_defaults(func=cmd_list)
    p = commands.add_parser('show'); p.add_argument('block'); p.set_defaults(func=cmd_show)
    for name,func in [('claim',cmd_claim),('start',cmd_start)]:
        p = commands.add_parser(name); p.add_argument('block'); p.add_argument('--owner',required=True); p.set_defaults(func=func)
    p = commands.add_parser('review'); p.add_argument('block'); p.add_argument('--reviewer',required=True); p.add_argument('--stage',choices=['source_reviewed','block_validated','integrated'],required=True); p.add_argument('--proof',required=True); p.set_defaults(func=cmd_review)
    p = commands.add_parser('validate'); p.add_argument('--block'); p.set_defaults(func=cmd_validate)
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
