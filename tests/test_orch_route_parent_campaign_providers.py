import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from gpu import orch_route_parent_campaign_providers as providers


class ParentProviderTests(unittest.TestCase):
    def test_effort_override_keeps_config_and_model_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home/'.codex').mkdir()
            config = home/'.codex/nvidia-astra.config.toml'
            config.write_text('model="' + providers.STRONG + '"\n'
                'model_provider="test"\nmodel_reasoning_effort="xhigh"\n'
                '[model_providers.test]\nwire_api="responses"\n'
                'base_url="https://inference-api.nvidia.com/v1"\nenv_key="NVIDIA_API_KEY"\n')
            original = config.read_bytes()
            envelope = dict(model=providers.STRONG, status='completed', usage=dict(output_tokens=80),
                output=[dict(type='message', content=[dict(type='output_text', text=self.reply())])])
            opener = MagicMock()
            opener.open.return_value.__enter__.return_value.read.return_value = json.dumps(envelope).encode()
            with patch.object(providers.Path, 'home', return_value=home), \
                    patch.dict(os.environ, {'NVIDIA_API_KEY': 'test-only'}), \
                    patch.object(providers.urllib.request, 'build_opener', return_value=opener):
                for name, effort in [('default', None), ('fast', 'low')]:
                    directory = home/name
                    directory.mkdir()
                    providers.strong('prompt', directory, time.time()+60, reasoning_effort=effort)
                    request = json.loads((directory/'API_REQUEST.json').read_text())
                    self.assertEqual(request['model'], providers.STRONG)
                    self.assertEqual(request['reasoning']['effort'], effort or 'xhigh')
                    dispatch = json.loads((directory/'DISPATCH.json').read_text())
                    self.assertEqual(dispatch['actual_reasoning_effort'], effort or 'xhigh')
            self.assertEqual(config.read_bytes(), original)

    def reply(self):
        return json.dumps(dict(speak=True, message='Read the available event before choosing.', rationale='Grounding'))

    def test_smaller_must_be_primary(self):
        envelope = dict(type='result', num_turns=1, result=self.reply(),
            modelUsage={providers.SMALLER: dict(outputTokens=50), 'claude-sonnet-5': dict(outputTokens=50)})
        with self.assertRaises(ValueError):
            providers.parse_smaller(envelope)
        del envelope['modelUsage']['claude-sonnet-5']
        self.assertEqual(providers.parse_smaller(envelope)[1], providers.SMALLER)

    def test_strong_requires_actual_identity_completed_usage_no_tools(self):
        envelope = dict(model=providers.STRONG, status='completed', usage=dict(output_tokens=80),
            output=[dict(type='message', content=[dict(type='output_text', text=self.reply())])])
        self.assertEqual(providers.parse_strong(envelope)[1], providers.STRONG)
        for key, value in (('model', 'guessed-alias'), ('status', 'incomplete'), ('usage', {}),
                           ('output', [dict(type='function_call')])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                providers.parse_strong(dict(envelope, **{key: value}))

    def test_message_bound_and_silence(self):
        for response in (dict(speak=False, message='nonempty', rationale='test'),
                         dict(speak=True, message='word ' * 91, rationale='test')):
            with self.assertRaises(ValueError):
                providers.response_schema(json.dumps(response))


if __name__ == '__main__':
    unittest.main()
