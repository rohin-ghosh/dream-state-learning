import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_loop.workers.post_recovery_age_queue_20260918 import runner


class SyntheticBackend:
    identity = dict(base_sha256='synthetic-base', adapter_state_sha256=None, all_parameters_frozen=True)

    def __init__(self, source, root):
        self.source = source

    def seed(self, seed):
        self.current_seed = seed

    def generate(self, messages, max_new_tokens):
        return dict(messages=messages, token_ids=[4] * max_new_tokens, raw='“A café?” — 问',
            prompt_tokens=10, terminal=False, truncated=True)

    def verify(self):
        return self.identity


class RunnerTests(unittest.TestCase):
    def test_real_contract_through_player_and_unicode_feedback_is_6144_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            scenes = [dict(contest_id=f'development_{index}', canonical_scene=f'A clock numbered {index}.',
                image='image-not-in-prompt', split='agent_development') for index in range(3)]
            (root / 'GAME_MANIFEST.json').write_text(json.dumps(dict(contests=scenes)))
            config = dict(plain_base=True, deadline_unix=9999999999)
            identity = dict(condition='R233_SYNTHETIC')
            def wait(path, deadline):
                if path.name == 'JUDGE_LOADED.json':
                    return dict(judge_epoch_sha256='synthetic-epoch', binding=dict(adapter_sha256=runner.epoch.ADAPTER_SHA))
                request = json.loads(path.with_name(path.name.replace('.result.json', '.request.json')).read_bytes())
                return dict(request_sha256=runner.contract.digest(request), judge_epoch_sha256='synthetic-epoch',
                    feedback='Synthetic receipt, not a real score.', results=[], new_pixels=0)
            with patch.object(runner, 'verify', return_value=(root, identity)), \
                    patch.object(runner.runtime, 'Backend', SyntheticBackend), \
                    patch.object(runner.runtime, 'wait', side_effect=wait), \
                    patch.dict(os.environ, dict(CUDA_VISIBLE_DEVICES='synthetic-device')):
                runner.player(config)
            complete = json.loads((root / 'players/R233_SYNTHETIC/COMPLETE.json').read_bytes())
            self.assertEqual(complete['actual_generated_tokens'], 6144)
            self.assertEqual(len(complete['cells']), 6)
            self.assertTrue(all(cell['generated_tokens'] == 1024 for cell in complete['cells']))
            self.assertEqual(complete['parent_tokens'], 0)
            self.assertEqual(complete['training_updates'], 0)
            self.assertEqual(complete['judge_epoch_sha256'], 'synthetic-epoch')
            for path in (root / 'queue').glob('*.request.json'):
                self.assertNotIn('image-not-in-prompt', path.read_text())


if __name__ == '__main__':
    unittest.main()
