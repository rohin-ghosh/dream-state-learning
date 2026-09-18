from copy import deepcopy
import unittest
from gpu.orch_math_feedback_uptake_r124_verify import validate_call


class VerifyTests(unittest.TestCase):
    def fixture(self):
        messages = [dict(role='system', content='system'), dict(role='user', content='task')]
        call = dict(status='COMPLETE', split='DEV', task_id='DEV1', messages=messages, checkpoint={'sha':'a'},
            parent_free=True, empty_context=True, never_rows_or_buffer=True, raw_saved_before_parser=True,
            token_count=2, completed_unix=1, response=dict(raw='reason FINAL: 1', token_ids=[1,2], messages=messages,
                input_truncated=False, requested_generation_cap=2048, effective_generation_cap=2048, terminal=True, truncated=False))
        return call, messages

    def test_compact_export_has_no_text_or_tokens(self):
        call,messages = self.fixture()
        result = validate_call(call,'DEV1',messages,{'sha':'a'})
        self.assertEqual(result['tokens'],2)
        self.assertNotIn('raw',result)
        self.assertNotIn('token_ids',result)

    def test_mismatch_rejected(self):
        original,messages = self.fixture()
        for key,value in (('checkpoint',{'sha':'b'}),('split','FINAL'),('token_count',3),('empty_context',False),('task_id','DEV2')):
            call=deepcopy(original);call[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_call(call,'DEV1',messages,{'sha':'a'})

    def test_truncated_or_changed_prompt_rejected(self):
        original,messages = self.fixture()
        for key,value in (('input_truncated',True),('effective_generation_cap',512),('messages',[]),('raw','')):
            call=deepcopy(original);call['response'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_call(call,'DEV1',messages,{'sha':'a'})
