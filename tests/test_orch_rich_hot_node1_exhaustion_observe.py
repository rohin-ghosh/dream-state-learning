import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_rich_hot_node1_exhaustion_observe import COLLECT
from gpu.orch_rich_hot_node1_observe import require_metadata_only


class ExhaustionObservationTests(unittest.TestCase):
    def test_remote_reduction_does_not_transport_raw_or_rejection_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'SOURCE_SHA256.json').write_text('{}')
            shard = root / 'shard0'
            shard.mkdir()
            row = dict(started_unix=1, finished_unix=2, global_call=1, task_id='train-task',
                       arm='EXHAUSTION_ONLY', phase_version='TEST', max_new_tokens=16384,
                       response=dict(raw='RAW_CANARY', prompt_tokens=269, token_ids=[1, 2], terminal=True),
                       approach_assessment=dict(self_reported_worked_approach_count=2,
                           self_reported_rejected_approach_count=1,
                           self_reported_rejected_approaches=['REJECTION_CANARY'],
                           repetition_failure_signal=False))
            (shard / 'CALL_00001.json').write_text(json.dumps(row))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(COLLECT, dict(ROOT=str(root), INDICES=[0], PREVIOUS=[], LEDGER=str(root), MATH=True))
            self.assertNotIn('RAW_CANARY', output.getvalue())
            self.assertNotIn('REJECTION_CANARY', output.getvalue())
            result = json.loads(output.getvalue())
            require_metadata_only(result)
            self.assertEqual(result['summary'][0]['calls'], 1)
            self.assertTrue(result['summary'][0]['actual_context_and_output_bounds_pass'])
            self.assertIsNone(result['summary'][0]['semantic_verified_worked_approach_count'])


if __name__ == '__main__':
    unittest.main()
