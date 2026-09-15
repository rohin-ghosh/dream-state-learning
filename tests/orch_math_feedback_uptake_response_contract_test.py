import unittest

from gpu.orch_math_feedback_uptake_response_contract import canonical_response
import orch_math_feedback_uptake_base_test as fixture


class ResponseContractTests(unittest.TestCase):
    def test_actual_minimal_engine_shape(self):
        tokenizer=fixture.Tokenizer()
        messages=[dict(role='user',content='Check the arithmetic.')]
        response=dict(messages=messages,prompt_tokens=len(tokenizer.apply_chat_template(messages)),
            raw='recorded wrong answer',token_ids=[1,2],terminal=False,truncated=True)
        result=canonical_response(response,messages,tokenizer,2,'a'*64)
        self.assertFalse(result['input_truncated'])
        self.assertNotIn('input_truncated',response)
        for key in response:
            self.assertEqual(response[key],result[key])
        for patch in (dict(prompt_tokens=1),dict(messages=[]),dict(input_truncated=True)):
            with self.assertRaises(ValueError):
                canonical_response(dict(response,**patch),messages,tokenizer,2,'a'*64)

    def test_context_and_output_caps_fail_closed(self):
        tokenizer=fixture.Tokenizer()
        messages=[dict(role='user',content='short')]
        response=dict(messages=messages,prompt_tokens=len(tokenizer.apply_chat_template(messages)),
            raw='raw',token_ids=[1,2],terminal=False,truncated=True)
        for cap in (0,1,16384):
            with self.assertRaises(ValueError):
                canonical_response(response,messages,tokenizer,cap,'a'*64)


if __name__=='__main__':
    unittest.main()
