from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from gpu import astra_event_two_hop as runner
from tests.test_astra_event_two_hop import arguments, fixture


class TurnBoundaryTests(unittest.TestCase):
    def test_reused_collection_and_explicit_protocol_preserve_original_replay(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.main(arguments(root, 'collect'))
            collect = root / 'collect/RESULT.json'
            receipt = runner.source.read(collect)
            receipt['helper_sha256'] = runner.ORIGINAL_COLLECTION_HELPER
            collect.write_text(json.dumps(receipt))
            runner.read_collection(root / 'collect', state.parent)
            original = runner.main(arguments(root, 'readout'))
            revised = runner.main(arguments(root, 'readout', root / 'turnbound') + ['--protocol', 'turnbound'])
            self.assertEqual(revised['model_calls'], 112)
            self.assertEqual(revised['fits'], 0)
            self.assertEqual(revised['collection_result_sha256'], original['collection_result_sha256'])
            for condition in runner.CONDITIONS:
                for old, new in zip(original['panels'][condition]['episodes'], revised['panels'][condition]['episodes']):
                    self.assertNotIn('protocol', old['episode'])
                    self.assertEqual(new['episode']['protocol'], 'turnbound')
                    self.assertEqual(new['episode']['messages'][0]['content'], runner.task.TURNBOUND_SYSTEM)
                    self.assertEqual(old['episode']['messages'][0]['content'], runner.task.PUBLIC_SYSTEM)
                    self.assertEqual(old['task'], new['task'])
                    for entry in (old, new):
                        self.assertEqual(runner.task.replay_episode(runner.task.build_world(), entry['task'],
                            entry['episode']), entry['episode'])
            receipt['helper_sha256'] = 'unknown-source'
            collect.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                runner.read_collection(root / 'collect', state.parent)

    def test_unknown_or_relabelled_protocol_rejected(self):
        world = runner.task.build_world()
        task = runner.task.build_tasks(world)[0]
        actor = lambda messages: {'raw': 'invalid', 'terminal': True, 'truncated': False}
        with self.assertRaises(ValueError):
            runner.task.run_episode(world, task, actor, lambda address: '', protocol='free-form-prompt')
        record = runner.task.run_episode(world, task, actor, lambda address: '', protocol='turnbound')
        self.assertEqual(record['terminal_reason'], 'invalid_command')
        changed = deepcopy(record)
        changed['protocol'] = 'original'
        with self.assertRaises(ValueError):
            runner.task.replay_episode(world, task, changed)


if __name__ == '__main__':
    unittest.main()
