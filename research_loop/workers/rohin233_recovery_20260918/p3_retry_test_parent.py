import types
import unittest

from p3_retry_parent import bind_recovery_context


class RetryParentContextTests(unittest.TestCase):
    def test_recovery_context_preserves_policy_payload_and_actual_source(self):
        payload = {'source_records': [{'index': 5300, 'sha256': 'historical'}]}
        calls = []

        def original(*arguments, **keywords):
            calls.append((arguments, keywords))
            return 'Original parent policy.', payload

        policy = types.SimpleNamespace(prompt=original)
        bind_recovery_context(policy, {'loaded_index': 5317})
        instruction, returned = policy.prompt('config', snapshot='actual')
        self.assertEqual(calls, [(('config',), {'snapshot': 'actual'})])
        self.assertIs(returned, payload)
        self.assertTrue(instruction.startswith('Original parent policy.'))
        self.assertIn('Retry1 LOAD 5317 is authenticated', instruction)
        self.assertIn('historical evidence, not new feedback during downtime', instruction)
        self.assertIn('same Astra parent with the same ledger and policy', instruction)


if __name__ == '__main__':
    unittest.main()
