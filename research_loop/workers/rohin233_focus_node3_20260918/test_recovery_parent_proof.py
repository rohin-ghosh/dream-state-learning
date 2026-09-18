import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from recovery_parent_proof import act_after_parent


class ParentACTProofTests(unittest.TestCase):
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
