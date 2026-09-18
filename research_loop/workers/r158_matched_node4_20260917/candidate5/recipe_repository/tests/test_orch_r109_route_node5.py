"""Exact new-node binding and true BASE response-path tests."""

import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_r109_route_node5_engine as engine
from gpu import orch_r109_route_node5_run as run
from organism_v6 import orch_r109_route_node5 as policy
from tests.test_orch_r107_route_parent import minimal_engine


class Node5RouteTests(unittest.TestCase):
    def test_only_exact_two_allocations(self):
        self.assertEqual(set(policy.LANES),{'node5_0','node5_1'})
        self.assertEqual(policy.allocation('node5_0'),'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a')
        self.assertEqual(policy.allocation('node5_1'),'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c')
        self.assertTrue(all(not value['learned'] for value in policy.LANES.values()))
        for slot in range(2,8):
            with self.assertRaises(ValueError): policy.allocation('node5_'+str(slot))

    def test_same_principles_exact_bytes(self):
        self.assertEqual(hashlib.sha256(Path(policy.PRINCIPLES_PATH).read_bytes()).hexdigest(),policy.PRINCIPLES_SHA)
        self.assertIn('never gate intervention on failure',policy.PARENT_INSTRUCTIONS)

    def test_full_prompt_actual_minimal_response(self):
        value=minimal_engine()
        value.model.eval=lambda:None
        response=engine.generate(value,[dict(role='user',content='actual route task')])
        self.assertFalse(response['input_truncated'])
        self.assertTrue(response['full_prompt_prefix_verified'])
        self.assertEqual(response['token_ids'],[13,99])

    def test_no_padded_reflection_or_quota_reset(self):
        self.assertEqual(policy.token_budget(32760),8)
        self.assertEqual(policy.NATIVE_CAP,16384)
        self.assertEqual(policy.parent_cap('node5_0'),1024)
        self.assertEqual(policy.parent_cap('node5_1'),1152)
        self.assertLess(run.END,run.LEASES['node5']-21600)

    def test_fresh_two_episode_cohorts(self):
        with patch.object(policy,'CYCLES',1):
            first=policy.cohort([],'node5_0')
            second=policy.cohort(policy.identifiers(first),'node5_1')
        self.assertEqual(len(first['train'][0]['tasks']),2)
        self.assertFalse(policy.identifiers(first)&policy.identifiers(second))
        self.assertFalse(policy.identifiers(first['train'])&policy.identifiers(first['held']))

    def test_parent_never_receives_held(self):
        payload=policy.parent_payload('node5_0',1,1,3,[dict(role='user',content='actual public task')],
            'own response','GENERATED_NOT_YET_EXECUTED',Path(policy.PRINCIPLES_PATH).read_text())
        with self.assertRaises(ValueError):policy.validate_parent_payload(dict(payload,held=[]))
        with self.assertRaises(ValueError):policy.validate_parent_payload(dict(payload,split='HELD'))


if __name__=='__main__':
    unittest.main()
