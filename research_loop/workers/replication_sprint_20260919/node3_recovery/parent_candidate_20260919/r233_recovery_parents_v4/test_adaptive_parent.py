import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from adaptive_parent import MODEL, OUTPUTS, accept, jobs, message, own_observation
from retirement import sha


class AdaptiveParentTests(unittest.TestCase):
    def test_tool_visibility_uses_exact_REQUEST_messages_not_metadata(self):
        helper = SimpleNamespace(records=lambda *args: [(Path('00000000000000000012.json'), 'REQUEST')])
        request = dict(index=12, sha256='real-request', document=dict(messages=[
            dict(role='user', content='Tool: Actual result unavailable.')]))
        with patch('adaptive_parent.record', return_value=request):
            observation = own_observation(helper, Path('/owned'), 'r213_math_c')
        self.assertEqual(observation['actually_rendered_Tool_messages'][0]['REQUEST']['index'], 12)

    def result(self, digest):
        return dict(request_sha256=digest, model=MODEL, response=dict(speak=True,
            message='Which case would decide between the actual arguments?', rationale='Check completeness.'),
            usage=dict(output_tokens=20), provider_response_sha256='a' * 64,
            provider_dispatch_sha256='b' * 64)

    def test_exact_provider_source_not_scripted_claim(self):
        value = self.result('actual-request')
        self.assertTrue(message(value, 'actual-request'))
        for changed in (dict(value, model='scripted'), dict(value, usage={}),
                dict(value, provider_dispatch_sha256='missing'), dict(value, request_sha256='other')):
            with self.assertRaises(ValueError):
                message(changed, 'actual-request')

    def test_only_pending_allowlisted_life_accepts_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / OUTPUTS[0] / 'r213_math_c/turn_0012'
            directory.mkdir(parents=True)
            request = directory / 'PROVIDER_REQUEST.json'
            request.write_text(json.dumps(dict(life='r213_math_c')))
            self.assertEqual(len(jobs(root)), 1)
            result = dict(relative=str(directory.relative_to(root)), result=self.result(sha(request)))
            with self.assertRaises(ValueError):
                accept(root, dict(result, relative='../other'))
            self.assertTrue(accept(root, result)['accepted'])
            self.assertEqual(jobs(root), [])
            with self.assertRaises(ValueError):
                accept(root, result)


if __name__ == '__main__':
    unittest.main()
