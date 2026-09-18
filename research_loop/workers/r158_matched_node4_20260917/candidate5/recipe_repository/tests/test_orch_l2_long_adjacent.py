import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_l2_adjacent_run as infrastructure
from gpu import orch_l2_long_adjacent_run as run
from organism_v6 import orch_l2_long_adjacent as diagnostic


class LongAdjacentTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.initial = dict(path='/synthetic/initial', state_sha256=diagnostic.adjacent.shared.INITIAL_STATE,
                            base_sha256=diagnostic.adjacent.BASE_SHA, files=[['adapter.bin', 'a' * 64]])
        infrastructure.write(self.root / 'INITIAL.json', self.initial)
        self.cohort = dict(held=[[dict(master=f'synthetic-{cycle}-{index}') for index in range(8)]
                                for cycle in range(4)])
        infrastructure.write(self.root / 'COHORT.json', self.cohort)

    def sleep(self, cycle=1, updates=28, arm='LONG'):
        folder = self.root / arm / f'cycle{cycle}/sleep'
        receipt = dict(status='COMPLETE', arm=arm, phase='sleep', cycle=cycle, updates=updates,
                       fits=int(updates > 0), unchanged=not updates, input_adapter=self.initial,
                       output_adapter=dict(self.initial, path='/synthetic/output', state_sha256='b' * 64)
                       if updates else self.initial, process=['synthetic-boot', 100, 200])
        infrastructure.write(folder / 'COMPLETE.json', receipt)
        infrastructure.write(folder / 'LOADED.json', dict(observed=self.initial, phase='sleep', process=receipt['process']))
        (folder / 'LOSSES.jsonl').write_text(''.join(json.dumps(dict(update=index, loss=1.0)) + '\n'
                                                   for index in range(1, updates + 1)))
        return folder

    def test_first_LONG_positive_binds_known_selection_and_C1(self):
        self.sleep()
        result = diagnostic.select_first(self.root)
        self.assertEqual(result['actual_updates'], 28)
        self.assertEqual(result['held_sha256'], diagnostic.digest(self.cohort['held'][1]))
        self.assertIn('already knew', result['disclosure'])
        self.assertNotIn('BLIND', result['policy'])

    def test_SHORT_positive_cannot_trigger_LONG(self):
        self.sleep(arm='SHORT')
        with self.assertRaisesRegex(ValueError, 'first_missing_LONG_sleep'):
            diagnostic.select_first(self.root)

    def test_missing_first_cannot_select_later(self):
        self.sleep(cycle=2)
        with self.assertRaisesRegex(ValueError, 'first_missing_LONG_sleep'):
            diagnostic.select_first(self.root)

    def test_different_positive_count_is_outside_assignment(self):
        self.sleep(updates=27)
        with self.assertRaisesRegex(ValueError, 'only_LONG_C1_28'):
            diagnostic.select_first(self.root)

    def test_first_positive_after_zero_is_not_C1_assignment(self):
        self.sleep(updates=0)
        self.sleep(cycle=2)
        with self.assertRaisesRegex(ValueError, 'only_LONG_C1_28'):
            diagnostic.select_first(self.root)

    def test_optimizer_ledger_drift_rejected(self):
        folder = self.sleep()
        (folder / 'LOSSES.jsonl').write_text('{"update": 1, "loss": 1}\n')
        with self.assertRaisesRegex(ValueError, 'optimizer_ledger'):
            diagnostic.select_first(self.root)

    def test_loaded_identity_drift_rejected(self):
        folder = self.sleep()
        loaded = diagnostic.read(folder / 'LOADED.json')
        loaded['observed']['state_sha256'] = 'c' * 64
        infrastructure.write(folder / 'LOADED.json', loaded)
        with self.assertRaisesRegex(ValueError, 'mounted_input_drift'):
            diagnostic.select_first(self.root)

    def test_later_positive_does_not_replace_first(self):
        self.sleep()
        self.sleep(cycle=2)
        self.assertEqual(diagnostic.select_first(self.root)['cycle'], 1)

    def test_pairing_requires_identical_tasks(self):
        rows = [dict(task=dict(index=index), correct=True, reads=[], routes=[]) for index in range(16)]
        result = diagnostic.paired_rows(rows, rows)
        self.assertEqual(result['both_correct'], 16)
        after = [dict(row) for row in rows]
        after[0]['task'] = dict(index=100)
        with self.assertRaisesRegex(ValueError, 'paired_task_drift'):
            diagnostic.paired_rows(rows, after)

    def test_existing_input_is_verified_not_overwritten(self):
        source, destination = self.root / 'source', self.root / 'destination'
        source.write_text('original')
        expected = run.copy_input(source, destination)
        self.assertEqual(run.copy_input(source, destination), expected)
        destination.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'input_copy_hash_drift'):
            run.copy_input(source, destination)
        self.assertEqual(destination.read_text(), 'changed')


if __name__ == '__main__':
    unittest.main()
