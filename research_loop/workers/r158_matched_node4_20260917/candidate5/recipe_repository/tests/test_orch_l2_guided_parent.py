from pathlib import Path
import json
import shutil
import tempfile
import unittest

from gpu import orch_l2_guided_parent as parent


class ParentTests(unittest.TestCase):
    def request(self):
        return dict(id='0000_SHORT_C1', payload=dict(kind='coach', turn=0, task={},
                    public_messages=[], prior_parent_messages=[], learner={}))

    def test_extra_sealed_key_rejected(self):
        request = self.request()
        request['payload']['held_scores'] = [1]
        with self.assertRaisesRegex(ValueError, 'scope'):
            parent.safe_payload(request)

    def test_secret_host_paths_rejected(self):
        for text in ('/tmp/secret', '[REDACTED_ADDRESS]', 'ORCH-L2-SHARED-20260914-V1-HELD-R0-W0', 'api_key'):
            request = self.request()
            request['payload']['learner'] = dict(note=text)
            with self.assertRaises(ValueError):
                parent.safe_payload(request)

    def test_tool_free_single_attempt(self):
        calls = []

        def dispatch(prompt, command):
            calls.append(command)
            self.assertIn('ALL parent messages', prompt)
            return dict(speak=True, message='Explain your own evidence.', rationale='learning')

        with tempfile.TemporaryDirectory() as directory:
            response = parent.evaluate(self.request(), Path(directory) / 'request', dispatch=dispatch)
        self.assertEqual(len(calls), 1)
        self.assertIn('--safe-mode', calls[0])
        self.assertEqual(calls[0][calls[0].index('--tools') + 1], '')
        self.assertEqual(calls[0][calls[0].index('--max-turns') + 1], '1')
        self.assertEqual(response['message'], 'Explain your own evidence.')

    def test_semantic_gate_never_receives_teacher(self):
        request = dict(payload=dict(kind='semantic', candidates=[dict(raw_sha256='raw', capture_sha256='capture',
            capture=dict(student_prefix=[dict(role='system', content='neutral')], response=dict(raw='own'),
                         messages=[dict(role='user', content='teacher verdict')]))]))
        self.assertNotIn('teacher verdict', str(parent.safe_payload(request)))

    def test_decline_with_hidden_message_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                parent.evaluate(self.request(), Path(directory) / 'request',
                    dispatch=lambda prompt, command: dict(speak=False, message='hidden', rationale='no'))

    def test_recover_actual_saved_outputs_without_dispatch_or_overwrite(self):
        evidence = Path('research_notes/analysis/orch_l2_guided_20260914_attempt1/parent')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for identity in ('0001_LONG_C1', '0002_LONG_C1'):
                (root / identity).mkdir()
                for suffix in ('.request.json', '.response.json'):
                    shutil.copyfile(evidence / (identity + suffix), root / (identity + suffix))
                for name in ('stdout.json', 'INVOCATION.json'):
                    shutil.copyfile(evidence / identity / name, root / identity / name)
                originals = {str(path): path.read_bytes() for path in root.rglob('*.json')}
                recovered = parent.recover_saved(root, identity)
                response = json.loads(recovered.read_text())
                self.assertEqual(response['recovery']['provider_calls'], 0)
                self.assertFalse(response['result'].get('error'))
                self.assertEqual(parent.recover_saved(root, identity), recovered)
                for path, content in originals.items():
                    self.assertEqual(Path(path).read_bytes(), content)
                self.assertFalse(list(root.glob('CALLS_*')))
                provider = json.loads((root / identity / 'stdout.json').read_text())
                provider['is_error'] = True
                (root / identity / 'stdout.json').write_text(json.dumps(provider))
                with self.assertRaisesRegex(ValueError, 'saved_provider_recovery_binding'):
                    parent.recover_saved(root, identity)


if __name__ == '__main__':
    unittest.main()
