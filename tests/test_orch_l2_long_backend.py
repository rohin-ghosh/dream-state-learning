import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_l2_long_backend import EvaluatorBackend, command, parse_output
from organism_v6.orch_l2_long_parent import SCHEMA, LongParent


class LongBackendTests(unittest.TestCase):
    def request(self):
        requests = []

        def backend(request):
            requests.append(request)
            return dict(decision='decline', message='', reason='Enough context.', distillation='No result.')

        parent = LongParent(backend, len, lambda event: None)
        parent.before_turn(cycle=1, episode_index=0, turn=0, observation='Public training observation.')
        return requests[0]

    def test_tools_disabled_and_permissions_not_bypassed(self):
        arguments = command()
        self.assertEqual(arguments[arguments.index('--tools') + 1], '')
        self.assertIn('--safe-mode', arguments)
        self.assertIn('--strict-mcp-config', arguments)
        self.assertFalse(any('skip-permissions' in value or 'fallback' in value for value in arguments))

    def test_real_response_and_usage_preserved(self):
        response = dict(decision='speak', message='Check evidence.', reason='Learning habit.',
                        distillation='Only training observations.')
        output = dict(type='result', result=json.dumps(response), usage={'output_tokens': 80},
                      modelUsage={'authorized-model': {'inputTokens': 1500}})
        parsed, receipt = parse_output(json.dumps(output))
        self.assertEqual(parsed, response)
        self.assertEqual(receipt['usage']['output_tokens'], 80)

    def test_error_or_nonconversational_schema_rejected(self):
        for output in (dict(type='result', is_error=True),
                       dict(type='result', result='{"answer": "canned"}')):
            with self.assertRaises(ValueError):
                parse_output(json.dumps(output))

    def test_memory_floor_precedes_charge_and_process(self):
        charges = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backend = EvaluatorBackend(root / 'out', lambda: charges.append(1),
                lock_path=root / 'lock', memory=lambda: 1024)
            with self.assertRaisesRegex(RuntimeError, 'below_1_5GiB'):
                backend(self.request())
            self.assertEqual(charges, [])
            failures = list((root / 'out').glob('*/FAILED.json'))
            self.assertEqual(len(failures), 1)
            self.assertFalse(json.loads(failures[0].read_text())['dispatched'])

    def test_sealed_request_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            backend = EvaluatorBackend(temporary, lambda: None)
            with self.assertRaises(ValueError):
                backend(dict(schema=SCHEMA, scope='sealed_readout'))

    def test_extra_source_or_test_context_refused_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            backend = EvaluatorBackend(temporary, lambda: self.fail('must not dispatch'))
            request = self.request()
            request['global_source'] = {'held_world': 'secret'}
            with self.assertRaisesRegex(ValueError, 'sanitized'):
                backend(request)


if __name__ == '__main__':
    unittest.main()
