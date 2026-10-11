"""Check identity, coverage, reservation and evidence integrity boundaries."""
import json
from pathlib import Path, PureWindowsPath
import random
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
import contextlib
import io

from tools import reverse as r

class CoverageTests(unittest.TestCase):
    def test_subtraction_has_no_lost_or_duplicated_bytes(self):
        randomizer = random.Random(7483)
        for _ in range(200):
            ranges = []
            for _ in range(20):
                a = randomizer.randrange(0, 160)
                ranges.append([a, a + randomizer.randrange(0, 20)])
            actual = list(r.subtract(10, 120, ranges))
            covered = {n for a, z in ranges for n in range(a, z)}
            result = [n for a, z in actual for n in range(a, z)]
            self.assertEqual(set(result), set(range(10, 120)) - covered)
            self.assertEqual(len(result), len(set(result)))

    def test_pe_virtual_zero_fill_and_unmapped_rejection(self):
        data = bytes(range(30))
        pe = {'headers_size':4, 'sections':[{'rva':8, 'virtual_size':10, 'raw_size':4, 'raw_offset':16}]}
        self.assertEqual(r.mapped_bytes(data, pe, 10, 18), bytes([18,19]) + b'\0' * 6)
        with self.assertRaises(ValueError):
            r.mapped_bytes(data, pe, 4, 9)

    def test_real_catalog_covers_every_section_and_resolves_dependencies(self):
        catalog = r.ROOT / 'blocks/catalog.jsonl'
        if not catalog.exists():
            self.skipTest('No catalog yet')
        blocks = r.load_blocks()
        ids = {b['id'] for b in blocks}
        self.assertEqual(len(ids), len(blocks))
        for b in blocks:
            self.assertTrue(set(b['dependencies']) <= ids)
            self.assertNotIn(b['id'], b['dependencies'])
        for binary in r.inventory()['binaries']:
            local = [b for b in blocks if b['binary_id'] == binary['binary_id']]
            ranges = [pair for b in local for pair in b['ranges']]
            for section in binary['pe']['sections']:
                a = section['rva']
                z = a + max(section['virtual_size'], section['raw_size'])
                self.assertEqual(list(r.subtract(a, z, ranges)), [], binary['paths'])
            integrated = next(b for b in local if b['kind'] == 'integration')
            size = next(f['size'] for f in r.inventory()['files'] if f['path'] == binary['paths'][0])
            raw = [[s['raw_offset'], s['raw_offset']+s['raw_size']] for s in binary['pe']['sections']]
            self.assertEqual(list(r.subtract(0, size, raw + integrated['file_ranges'])), [])

class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / 'binary-fn-00001000'
        self.directory.mkdir()
        self.block = dict(id=self.directory.name, baseline_id='baseline', binary_sha256='original', kind='function', dependencies=['other-block'])
        self.submission = dict(schema=1, block_id=self.directory.name, baseline_id='baseline', binary_sha256='original', owner='alice', status='ready',
                               source_files=['function.cpp'], evidence_files=['proof.json','build.log','compare.log'], test_files=['test.cpp'],
                               abi=dict(calling_convention='cdecl',parameters='void',return_='void', side_effects='none'),
                               dependency_contracts=[dict(block_id='other-block',contract='cdecl void(void)')],unknowns=[])
        self.submission['abi']['return'] = self.submission['abi'].pop('return_')
        for p in ('function.cpp','test.cpp','analysis.md','build.log','compare.log'):
            (self.directory / p).write_text('substantive fixture evidence\n')
        self.proof = dict(environment='Windows x86 test fixture', reasoning='fixture',
                          build=dict(result='pass',command='compiler',log='build.log'),
                          comparison=dict(result='pass',command='compare',log='compare.log',original_sha256='original',cases=['boundary'],method='differential'))
        r.write(self.directory / 'proof.json', self.proof)
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        r.write(self.directory / 'submission.json', self.submission)

    def check(self):
        return r.validate_submission(self.directory, {self.block['id']:self.block})

    def test_unresolved_outgoing_flow_prevents_ready_and_reservation(self):
        self.block['unresolved_calls_rva'] = [0x3345]
        with self.assertRaisesRegex(ValueError, 'direct flow'):
            self.check()
        with mock.patch.object(r, 'choose_block', return_value=self.block):
            with self.assertRaisesRegex(ValueError, 'resolve boundaries'):
                r.cmd_claim(SimpleNamespace(block=self.block['id'], owner='alice'))

    def test_wrong_binary_cannot_be_submitted(self):
        self.submission['binary_sha256'] = 'different-original'
        self.save()
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            self.check()

    def test_path_escape_and_symlink_cannot_be_used_as_evidence(self):
        outside = self.directory.parent / 'secret'
        outside.write_text('outside')
        for path in ('../secret', str(outside)):
            with self.assertRaises(ValueError):
                r.local_files(self.directory, [path])
        try:
            (self.directory / 'linked').symlink_to(outside)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows symlink creation privilege is unavailable')
            raise
        with self.assertRaises(ValueError):
            r.local_files(self.directory, ['linked'])

    def test_missing_dependency_contract_and_unknowns_reject_ready(self):
        for field, value in [('dependency_contracts', []), ('unknowns', ['stack layout unknown'])]:
            previous = self.submission[field]
            self.submission[field] = value
            self.save()
            with self.assertRaises(ValueError):
                self.check()
            self.submission[field] = previous
        self.save()
        self.check()

    def review_record(self):
        return dict(schema=1,block_id=self.block['id'],baseline_id='baseline',reviewer='bob',stage='block_validated',proof_file='proof.json',
                    submission_digest=r.submission_digest(self.directory,self.submission))

    def test_changes_invalidate_prior_review(self):
        record = self.review_record()
        r.validate_review(record,self.block,self.check(),self.directory)
        (self.directory / 'function.cpp').write_text('modified code')
        with self.assertRaisesRegex(ValueError, 'stale'):
            r.validate_review(record,self.block,self.check(),self.directory)

    def test_self_review_and_wrong_original_proof_are_rejected(self):
        record = self.review_record()
        record['reviewer'] = 'alice'
        with self.assertRaisesRegex(ValueError,'independent'):
            r.validate_review(record,self.block,self.check(),self.directory)
        self.proof['comparison']['original_sha256'] = 'different-original'
        r.write(self.directory / 'proof.json',self.proof)
        with self.assertRaisesRegex(ValueError,'original'):
            r.validate_review(self.review_record(),self.block,self.check(),self.directory)

class WorkflowTests(unittest.TestCase):
    def test_windows_batch_launch_handles_spaces_and_rejects_expansion(self):
        ghidra = PureWindowsPath('C:/Program Files/Ghidra')
        command = r.ghidra_invocation(ghidra, [PureWindowsPath('C:/User Projects/work'), 'test'], windows=True)
        self.assertIn('"C:\\Program Files\\Ghidra\\support\\analyzeHeadless.bat"', command)
        self.assertIn('"C:\\User Projects\\work"', command)
        for unsafe in ('C:/work%PATH%', 'C:/work&other', 'C:/work!name'):
            with self.assertRaisesRegex(ValueError, 'metacharacters'):
                r.ghidra_invocation(ghidra, [unsafe], windows=True)
        command = r.ghidra_invocation(Path('/opt/ghidra'), ['/tmp/projects', 'test'], windows=False)
        self.assertEqual(command, ['/opt/ghidra/support/analyzeHeadless', '/tmp/projects', 'test'])

    def test_reservation_collision_owner_and_start(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            block = dict(id='test-fn-00001000', kind='function', baseline_id='baseline', binary_sha256='original', dependencies=[])
            for name in ('blocks','claims','contributions','reviews'):
                (root / name).mkdir()
            (root / 'blocks/catalog.jsonl').write_text(json.dumps(block) + '\n')
            with mock.patch.object(r, 'ROOT', root):
                alice = SimpleNamespace(block=block['id'], owner='alice')
                bob = SimpleNamespace(block=block['id'], owner='bob')
                r.cmd_claim(alice)
                with self.assertRaises(FileExistsError):
                    r.cmd_claim(bob)
                with self.assertRaisesRegex(ValueError, 'reservation'):
                    r.cmd_start(bob)
                r.cmd_start(alice)
                r.cmd_validate(SimpleNamespace(block=None))
                submission = r.read(root / 'contributions' / block['id'] / 'submission.json')
                self.assertEqual(submission['owner'], 'alice')
                self.assertEqual(submission['status'], 'draft')

    def test_frozen_catalog_roundtrip_and_corruption_rejection(self):
        if not (r.ROOT / 'blocks/baseline.json').exists():
            self.skipTest('No frozen catalog yet')
        with contextlib.redirect_stdout(io.StringIO()):
            r.cmd_audit(SimpleNamespace(originals=False))
        original_sha = r.sha
        def corrupted_sha(path):
            return '0' * 64 if path.name == 'catalog.jsonl' else original_sha(path)
        with mock.patch.object(r, 'sha', side_effect=corrupted_sha):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                r.cmd_audit(SimpleNamespace(originals=False))

if __name__ == '__main__':
    unittest.main()
