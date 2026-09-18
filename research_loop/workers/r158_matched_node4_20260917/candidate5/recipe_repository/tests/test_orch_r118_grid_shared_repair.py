from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r118_grid_shared_run as run

if os.environ.get('R118_REPAIR_MODULE'):
    spec = importlib.util.spec_from_file_location('grid_repair', os.environ['R118_REPAIR_MODULE'])
    repair = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(repair)
else:
    from gpu import orch_r118_grid_shared_repair as repair


class FakeLife:
    def __init__(self, root, intervention, responses):
        self.root = root
        self.cycle = 8
        self.intervention = intervention
        self.responses = list(deepcopy(responses))
        self.events = []
        self.generated = []
        self.parents = 0
        self.settings = {}
        self.original_messages = None

    def event(self, actor, text, source):
        self.events.append((actor, text, source))

    def generate(self, task, purpose, messages, cap):
        if self.original_messages is None:
            self.original_messages = deepcopy(messages)
        self.generated.append((purpose, deepcopy(messages), cap))
        response = self.responses.pop(0)
        self.event('child', response['raw'], response['reference']['sha256'])
        return response

    def ask(self, task, ordinal, phase):
        self.parents += 1
        self.settings = self.intervention['reflection_settings']
        if self.intervention['disposition']['guidance']:
            self.event('parent', self.intervention['disposition']['guidance'],
                       self.intervention['response']['sha256'])
        return self.intervention

    def environment(self, task, state, raw, purpose, sequence):
        after = dict(state, count=state['count'] + 1, done=state['count'] == 1)
        return after, {'enacted': True, 'step': sequence}, {'path': 'environment', 'sha256': 'environment'}


class ContinuationTests(unittest.TestCase):
    def compare(self, guidance):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = {'id': 'TRAIN_1', 'split': 'TRAIN'}
            initial = {'done': False, 'success': False, 'count': 0}
            intervention = {'disposition': {'guidance': guidance},
                            'reflection_settings': {'effective_max_new_tokens': 1024},
                            'response': {'sha256': 'parent'}}
            responses = [dict(raw='response' + str(index), token_ids=[index] * (index + 1),
                              reference={'path': 'capture' + str(index), 'sha256': 'hash' + str(index)})
                         for index in range(4)]
            original = FakeLife(root / 'original', intervention, responses)
            resumed = FakeLife(root / 'resumed', intervention, responses[1:])
            with patch.object(run.grid.policy.game, 'initial', return_value=initial), \
                    patch.object(run.grid.policy, 'public_observation', return_value={'observation': 1}):
                expected = run.grid.episode(original, task, 0, [])
                capture = dict(cycle=8, task_id=task['id'], status='COMPLETE', cap=384,
                               messages=original.original_messages, response=responses[0])
                actual = repair.continue_episode(resumed, task, 0, [], capture,
                                                   responses[0]['reference'], intervention)
            self.assertEqual(actual, expected)
            self.assertEqual(resumed.generated, original.generated[1:])
            self.assertEqual(resumed.parents, 0)
            self.assertEqual(original.parents, 1)
            self.assertEqual(resumed.events, original.events)
            self.assertEqual(resumed.settings, original.settings)

    def test_guided_continuation_never_regenerates_or_redispatches(self):
        self.compare('Existing published guidance')

    def test_silent_continuation_preserves_budget_and_outcome(self):
        self.compare(None)

    def test_other_ordinal_is_not_recovery(self):
        life = SimpleNamespace(cycle=8)
        with self.assertRaises(ValueError):
            repair.continue_episode(life, {'id': 'TRAIN_1'}, 1, [], {}, {}, {})

    def test_wrong_prompt_is_rejected_before_generation(self):
        life = SimpleNamespace(cycle=8)
        with patch.object(run.grid.policy.game, 'initial', return_value={}), \
                patch.object(run.grid.policy, 'public_observation', return_value={}), \
                self.assertRaises(ValueError):
            repair.continue_episode(life, {'id': 'TRAIN_1'}, 0, [],
                dict(cycle=8, task_id='TRAIN_1', status='COMPLETE', messages=[], cap=384), {}, {})

    def test_missing_packaged_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run.shared.write(root / 'MANIFEST.json', dict(files={repair.BATTLEPLAN: repair.BATTLE_SHA,
                repair.PRINCIPLES: run.grid.broker.PRINCIPLES_V2_SHA256}))
            with self.assertRaises(FileNotFoundError):
                repair.verify_bundle(root)


if os.environ.get('R118_REPAIR_BUNDLE'):
    class NativeCapturedEnvelopeTests(unittest.TestCase):
        def test_real_captured_parent_envelopes_and_packaged_files(self):
            bundle = Path(os.environ['R118_REPAIR_BUNDLE'])
            repair.bind_references(bundle)
            self.assertEqual(run.shared.sha(bundle / repair.BATTLEPLAN), repair.BATTLE_SHA)
            self.assertEqual(run.shared.sha(bundle / repair.PRINCIPLES), run.grid.broker.PRINCIPLES_V2_SHA256)
            template = run.grid.broker.fixed_parent_template()
            self.assertIn('You are the parent of a young model.', template)
            for branch in ('F4', 'A4'):
                root = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915') / branch
                state = repair.interrupted(root)
                before = {state[key]['path']: run.shared.sha(state[key]['path'])
                          for key in ('capture', 'request', 'response')}
                result = repair.recover_parent(root, state)
                self.assertEqual(result['reflection_settings']['status'], 'BOUND_FOR_LANE_DECODER')
                self.assertEqual(result['reflection_settings']['effective_max_new_tokens'], 1024)
                self.assertFalse(result['parent_redispatched'])
                self.assertEqual(before, {name: run.shared.sha(name) for name in before})
                self.assertFalse((root / 'parent_received' / f'P{state["parent_number"]:04d}.json').exists())


if __name__ == '__main__':
    unittest.main()
