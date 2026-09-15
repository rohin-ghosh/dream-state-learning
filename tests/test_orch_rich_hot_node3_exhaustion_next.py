import unittest
from unittest.mock import patch

from organism_v6 import orch_rich_hot_node3_exhaustion_next as policy
from gpu.orch_rich_hot_node3_exhaustion_boundary import episode_complete


class NextExhaustionTests(unittest.TestCase):
    def test_unseen_per_slot_displays(self):
        templates = [dict(kind=kind, node='n', events=['a','b','c','d'], ports=['x','y'])
                     for kind in ('first','middle','last')]
        with patch.object(policy.previous.previous, 'tasks', return_value=templates):
            old = {policy.original.digest(task) for index in (3,4,5)
                   for task in policy.previous.tasks({},index)}
            new = [policy.original.digest(task) for index in (3,4,5) for task in policy.tasks({},index)]
        self.assertEqual(len(new),48)
        self.assertEqual(len(set(new)),48)
        self.assertFalse(old.intersection(new))

    def test_only_owned_slots_and_unchanged_prompts(self):
        with self.assertRaises(ValueError):
            policy.arm(1)
        self.assertEqual(policy.arm(3),'EXHAUSTION_ONLY')
        self.assertEqual(policy.guidance(4),policy.previous.guidance(4))
        self.assertIs(policy.episode,policy.previous.episode)

    def test_prospective_caps_not_old_ledger_reset(self):
        self.assertEqual(policy.MAX_CALLS,3*policy.MAX_SLOT_CALLS)
        self.assertEqual(policy.MAX_CALLS,384*6)
        self.assertEqual(3280+policy.MAX_CALLS,5584)

    def test_completed_episode_guard_rejects_pending_calls(self):
        rows=[dict(global_call=1,task_id='train')]
        self.assertTrue(episode_complete(rows,[dict(task_id='train')],[dict(global_call=1)]))
        self.assertFalse(episode_complete(rows,[],[dict(global_call=1)]))
        self.assertFalse(episode_complete(rows,[dict(task_id='train')],[dict(global_call=1),dict(global_call=2)]))
