import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
from inventory import disposition, observe


class DispositionTests(unittest.TestCase):
    def test_exact_completed(self):
        self.assertEqual(disposition(True, [dict(exact_checkpoint_binding=True)], True),
            'COMPLETED_BOUNDARY_METADATA_BOUND_PENDING_CUSTODY')

    def test_orphan_not_completed(self):
        self.assertEqual(disposition(True, [], True), 'ORPHAN_COMMIT_NO_SLEEP_COMPLETE_IN_VERIFIED_SNAPSHOT')

    def test_incomplete_not_absence(self):
        self.assertEqual(disposition(True, [], False), 'UNKNOWN_INCOMPLETE_JOURNAL_COVERAGE')

    def test_duplicate_or_mismatch(self):
        for matches in ([dict(exact_checkpoint_binding=False)], [dict(exact_checkpoint_binding=True)] * 2):
            self.assertEqual(disposition(True, matches, True), 'AMBIGUOUS_OR_MISMATCHED_BOUNDARY')

    def test_missing(self):
        self.assertEqual(disposition(False, [], True), 'MISSING_COMMIT')

    def fixture(self, root, changed=False):
        source = Path(__file__).parents[1]/'observation_20260917_generation2/observe.py'
        specification = importlib.util.spec_from_file_location('original_reader', source)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        base = dict(vars(module), ROOT=root, ARMS=('parented_learning',))
        cohort = b'{"synthetic":true}'
        (root/'COHORT.json').write_bytes(cohort)
        base['COHORT'] = module.digest(cohort)
        arm = root/'parented_learning'
        checkpoint_path = arm/'checkpoints/sleep_000001/COMMIT.json'
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint = dict(adapter_path=str(checkpoint_path.parent/'adapter'),
            checkpoint_sha256=dict(adapter='hash'), optimizer_steps=7, hidden='DO_NOT_RETURN')
        checkpoint_path.write_bytes(module.canonical(dict(checkpoint, optimizer_steps=8) if changed else checkpoint))
        receipt = dict(status='COMPLETE', cycle=1, checkpoint=checkpoint,
            checkpoint_sha256=checkpoint['checkpoint_sha256'])
        state = dict(sleep_receipts=[receipt], matched=dict(arm='parented_learning',cohort_sha256=base['COHORT']))
        body = dict(receipt, resume_state=dict(state=state,sha256=module.digest(module.canonical(state))))
        manifest = dict(schema='synthetic',journal_id='synthetic')
        records = arm/'stream/records'
        records.mkdir(parents=True)
        (records.parent/'JOURNAL.json').write_bytes(module.canonical(manifest))
        previous = module.digest(module.canonical(manifest))
        record = dict(manifest,index=0,previous_sha256=previous,kind='SLEEP_COMPLETE',document=body)
        checksum = module.digest(module.canonical(record))
        (records/'00000000000000000000.json').write_bytes(module.canonical(dict(record,sha256=checksum)))
        intent = dict(manifest,index=0,previous_sha256=previous,record_sha256=checksum)
        (records/'00000000000000000000.intent.json').write_bytes(module.canonical(intent))
        (arm/'readouts').mkdir()
        (arm/'readouts/held.json').write_text('MUST_NOT_OPEN')
        return base

    def test_full_binding_and_metadata_only_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            result = observe(self.fixture(Path(directory)))
            self.assertEqual(result['arms']['parented_learning']['intended']['1']['disposition'],
                'COMPLETED_BOUNDARY_METADATA_BOUND_PENDING_CUSTODY')
            self.assertNotIn('DO_NOT_RETURN', json.dumps(result))
            self.assertEqual(result['scanned_files'], 5)

    def test_changed_commit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = observe(self.fixture(Path(directory), changed=True))
            self.assertEqual(result['arms']['parented_learning']['intended']['1']['disposition'],
                'AMBIGUOUS_OR_MISMATCHED_BOUNDARY')


if __name__ == '__main__':
    unittest.main()
