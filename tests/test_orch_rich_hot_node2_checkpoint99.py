import unittest
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from gpu import orch_rich_hot_node2_checkpoint99 as native
from gpu.orch_rich_hot_node2_checkpoint_guard import target, DERIVED
from organism_v6 import orch_rich_hot_node2_checkpoint99 as policy
from organism_v6 import orch_rich_hot_node2_floor98 as comparator


class Checkpoint99Tests(unittest.TestCase):
    def test_reservations_bind_source_before_dispatch_and_enforce_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reservations').mkdir()
            prepared = dict(comparator_root='comparator', identity=dict(state_sha256='state', base_sha256='base'),
                lineage=dict(commit_sha256='commit'), parent_checkpoint_update=256, source_sha256='source')
            (root / 'PREPARE.json').write_text(json.dumps(prepared))
            task = dict(id='B000-P01', family='code', source_task_id='ledger_001',
                repeated_train_source=False, comparator_task_id='B000-P01')
            with patch.object(native, 'ROOT', root), patch.object(policy, 'MAX_CALLS', 1):
                row = native.reserve(root, 0, task, 'final_0', [], float('inf'))
                self.assertEqual(json.loads((root / 'reservations/0_B000-P01_final_0.json').read_text()), row)
                self.assertEqual(row['generator_identity'], prepared['identity'])
                self.assertEqual(row['source_checkpoint_commit_sha256'], 'commit')
                self.assertEqual(row['source_checkpoint_update'], 256)
                self.assertEqual(row['source_code_sha256'], 'source')
                self.assertEqual(row['generator_classification'], policy.CLASSIFICATION)
                self.assertEqual((row['max_new_tokens'], row['context']), (8192, 16384))
                self.assertFalse(row['trainingAllowed'])
                with self.assertRaises(native.base.BudgetEnd):
                    native.reserve(root, 0, dict(task, id='B000-P03'), 'final_0', [], float('inf'))
                self.assertEqual(len(list((root / 'reservations').glob('*.json'))), 1)

    def test_only_one_checkpoint_slot(self):
        self.assertEqual([shard for shard in range(8) if target(shard)[0] == DERIVED], [0])
        self.assertEqual({target(shard)[1] for shard in range(1, 8)}, {'gpu.orch_rich_hot_node2_floor98'})

    def test_same_roster_and_prompt_as_37ec_physical1(self):
        records = [dict(question=f'Task {index}', answer='#### 42') for index in range(12)]
        document = comparator.cohort(records, dict(tasks=[], excluded_ids=[], excluded_question_hashes=[]))
        for position in range(0, 24, 2):
            derived = policy.task_at(document, 0, position)
            control = comparator.task_at(document, 0, position + 1)
            self.assertEqual(derived['payload'], control['payload'])
            self.assertEqual(derived['source_task_id'], control['source_task_id'])
            if derived['family'] != 'route':
                self.assertEqual(policy.messages(derived, 'ORIGINAL_RICH'), comparator.messages(control, 'ORIGINAL_RICH'))
        self.assertEqual(policy.MAX_CALLS + 7 * comparator.CALLS_PER_SHARD, comparator.MAX_CALLS)

    def test_saved_FULL_not_initial_OFF_or_unbound(self):
        metadata = dict(update=256, adapter=dict(state_sha256='saved'), corpus_sha256='corpus')
        handoff = dict(schema='COMBINED_CONTINUAL_FULL_CHILD_READY_V1', status='DURABLE_CHECKPOINT_HELD_SCORES_NOT_REQUIRED',
            checkpoint='/source/FULL/checkpoints/000000256', updates=256, adapter=metadata['adapter'],
            corpus_sha256='corpus', commit_sha256='commit', parent_present=False)
        self.assertEqual(policy.validate_handoff(handoff, dict(metadata=metadata), 'commit'), metadata)
        for field, value in (('checkpoint', '/source/OFF/checkpoints/000000256'), ('updates', 0), ('parent_present', True)):
            changed = deepcopy(handoff)
            changed[field] = value
            with self.assertRaisesRegex(ValueError, 'exact_saved_continual_FULL'):
                policy.validate_handoff(changed, dict(metadata=metadata), 'commit')


if __name__ == '__main__':
    unittest.main()
