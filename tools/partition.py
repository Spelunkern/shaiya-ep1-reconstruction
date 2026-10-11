"""Frozen partition algorithm. Changes require an explicit baseline migration."""
import bisect
import hashlib
import json
from pathlib import Path

CHUNK = 65536

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def merge_ranges(ranges):
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def subtract(start, end, ranges):
    cursor = start
    for a, z in merge_ranges(ranges):
        if z <= cursor or a >= end:
            continue
        if a > cursor:
            yield cursor, min(a, end)
        cursor = max(cursor, z)
    if cursor < end:
        yield cursor, end


def chunks(start, end):
    while start < end:
        stop = min(start + CHUNK, end)
        yield start, stop
        start = stop


def make_plan(ROOT, manifest, validate_export, ghidra_version):
    inputs = {'inventory': sha(ROOT / 'manifests/originals.json'), 'exporter': sha(ROOT / 'tools/ghidra/ExportBaseline.java'),
              'planner': sha(Path(__file__)), 'toolchain': sha(ROOT / 'manifests/toolchain.json'), 'chunk_bytes': CHUNK, 'ghidra': ghidra_version, 'exports': {}}
    blocks = []
    audits = []
    for b in manifest['binaries']:
        bid = b['binary_id']
        out = ROOT / 'analysis/baseline' / bid
        funcs = validate_export(b)
        inputs['exports'][bid] = {p: sha(out / p) for p in ('functions.jsonl', 'summary.json')}
        first_block = len(blocks)
        by_entry = {f['entry_rva']: f for f in funcs}
        covered = []
        owners = []
        for f in funcs:
            entry = f['entry_rva']
            block_id = f'{bid}-fn-{entry:08x}'
            known = [f'{bid}-fn-{r:08x}' for r in f['calls_rva'] if r in by_entry and r != entry]
            blocks.append(dict(id=block_id, binary_id=bid, binary_sha256=b['sha256'], kind='function',
                               entry_rva=entry, ranges=f['ranges'], body_sha256=f['body_sha256'],
                               name=f['name'], ghidra_signature=f['signature'],
                               ghidra_calling_convention=f['calling_convention'], thunk=f['thunk'],
                               instruction_count=f['instruction_count'],
                               data_refs_rva=f['data_refs_rva'], dependencies=known, unresolved_calls_rva=[r for r in f['calls_rva'] if r not in by_entry],
                               indirect_call_count=f['indirect_call_count'], external_calls=f['external_calls']))
            covered.extend(f['ranges'])
            owners.extend((a, z, block_id) for a, z in f['ranges'])
        # Record shared tails instead of silently giving two contributors exclusive ownership.
        overlaps = []
        active = []
        for a, z, owner in sorted(owners):
            active = [(x, y, o) for x, y, o in active if y > a]
            for x, y, other in active:
                if other != owner:
                    overlaps.append(dict(range=[a, min(z, y)], owners=sorted([other, owner])))
            active.append((a, z, owner))
        conflict_ids = {o for overlap in overlaps for o in overlap['owners']}
        for block in blocks[first_block:]:
            if block['binary_id'] == bid and block['id'] in conflict_ids:
                block['shared_body'] = True
        code_total = code_known = 0
        for section in b['pe']['sections']:
            a = section['rva']
            z = a + max(section['virtual_size'], section['raw_size'])
            if section['executable']:
                code_total += z - a
                missing = list(subtract(a, z, covered))
                code_known += z - a - sum(e - s for s, e in missing)
                kind = 'unclassified'
                intervals = missing
            else:
                kind = 'data'
                intervals = list(subtract(a, z, covered))
            for s, e in intervals:
                for x, y in chunks(s, e):
                    blocks.append(dict(id=f'{bid}-{kind}-{x:08x}', binary_id=bid, binary_sha256=b['sha256'],
                                       kind=kind, ranges=[[x, y]], section=section['name'], dependencies=[]))
        local_blocks = blocks[first_block:]
        data_ranges = sorted((x, y, block['id']) for block in local_blocks if block['kind'] in ('data', 'unclassified') for x, y in block['ranges'])
        starts = [x for x, _, _ in data_ranges]
        sorted_owners = sorted(owners)
        owner_starts = [a for a, _, _ in sorted_owners]
        owner_prefix_end = []
        for a, z, owner in sorted_owners:
            owner_prefix_end.append(max(z, owner_prefix_end[-1] if owner_prefix_end else 0))
        for block in local_blocks:
            if block['kind'] != 'function':
                continue
            data_dependencies = set()
            unresolved_data = []
            for rva in block['data_refs_rva']:
                pos = bisect.bisect_right(starts, rva) - 1
                if pos >= 0 and data_ranges[pos][0] <= rva < data_ranges[pos][1]:
                    data_dependencies.add(data_ranges[pos][2])
                else:
                    matches = set()
                    owner_pos = bisect.bisect_right(owner_starts, rva) - 1
                    while owner_pos >= 0 and owner_prefix_end[owner_pos] > rva:
                        a, z, owner = sorted_owners[owner_pos]
                        if a <= rva < z:
                            matches.add(owner)
                        owner_pos -= 1
                    if matches:
                        data_dependencies.update(matches - {block['id']})
                    else:
                        unresolved_data.append(rva)
            block['dependencies'] = sorted(set(block['dependencies']) | data_dependencies)
            block['unresolved_data_rva'] = unresolved_data
        raw_ranges = [(s['raw_offset'], s['raw_offset'] + s['raw_size']) for s in b['pe']['sections'] if s['raw_size']]
        file_size = next(f['size'] for f in manifest['files'] if f['path'] == b['paths'][0])
        blocks.append(dict(id=f'{bid}-integration', binary_id=bid, binary_sha256=b['sha256'],
                           kind='integration', ranges=[], file_ranges=list(subtract(0, file_size, raw_ranges)), dependencies=[],
                           obligations=['file_headers_overlay', 'imports_exports_resources_relocations',
                                        'compiler_linker_abi', 'whole_binary_build', 'differential_runtime_tests']))
        audits.append(dict(binary_id=bid, paths=b['paths'], functions=len(funcs), executable_bytes=code_total,
                           function_body_bytes_in_executable=code_known, unclassified_executable_bytes=code_total-code_known,
                           shared_body_ranges=overlaps))
    baseline = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for block in blocks:
        block['baseline_id'] = baseline
    blocks.sort(key=lambda x: x['id'])
    return blocks, dict(schema=1, baseline_id=baseline, inputs=inputs, binaries=audits)

