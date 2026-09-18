import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from recovery_parent_proof import act_after_parent, latest_completed_model_parent


class ParentACTProofTests(unittest.TestCase):
    def test_pending_turn_does_not_hide_latest_actual_model_chain(self):
        complete = dict(parent_kind='ACTUAL_MODEL_PROVIDER', delivery=dict(REQUEST=dict(index=8)),
            actual_ACT_after_parent=dict(ACT=dict(index=10)))
        pending = dict(parent_kind='ACTUAL_MODEL_PROVIDER', delivery=dict(REQUEST=None),
            actual_ACT_after_parent=None)
        self.assertEqual(latest_completed_model_parent([complete, pending]), complete)
        self.assertIsNone(latest_completed_model_parent([pending]))

    def test_scripted_delivery_never_counts_as_model_parent(self):
        scripted = dict(parent_kind='SCRIPTED_NOT_MODEL_PROVIDER', delivery=dict(REQUEST=dict(index=8)),
            actual_ACT_after_parent=dict(ACT=dict(index=10)))
        self.assertIsNone(latest_completed_model_parent([scripted]))

    def test_actual_prompt_response_ACT_chain_not_temporal_guess(self):
        request = dict(messages=[dict(role='user', content='Astra: Check one case.')],
            render_receipt=dict(all_history_tokens_masked=True))
        digest = hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
        values = [dict(index=2,sha256='request',document=request),
            dict(index=3,sha256='response',document=dict(request_sha256=digest)),
            dict(index=4,sha256='act',document=dict(origin=dict(kind='TRAIN_CHILD_RESPONSE',
                record_index=3,record_sha256='response')))]
        helper = SimpleNamespace(records=lambda *args: [(Path(str(index)),kind)
            for index,kind in enumerate(('REQUEST','RESPONSE','R184_ACT'))])
        with patch('recovery_parent_proof.record',side_effect=lambda path:values[int(str(path))]):
            result=act_after_parent(helper,None,'r213_math_a',dict(text='Check one case.'),dict(REQUEST=dict(index=2)))
            self.assertEqual(result['ACT']['index'],4)
            self.assertIsNone(act_after_parent(helper,None,'r213_math_a',dict(text='A different turn.'),dict(REQUEST=dict(index=2))))


if __name__ == '__main__':
    unittest.main()
