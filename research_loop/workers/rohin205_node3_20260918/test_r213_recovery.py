"""No hidden resident-state continuity and no cross-group native peers."""

from copy import deepcopy
import unittest

from gpu.r213_recovery_runtime import GROUPS, peer_capsule, saved_state
from organism_v6.orch_r125_continual_stream import digest


class RecoveryTests(unittest.TestCase):
    def test_saved_checkpoint_changes_only_deadline(self):
        hashes = dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64)
        state = dict(deadline_unix=10, pending=None, rows=[dict(target='own')], sleep_frontier=1,
            model_state_sha256=digest(hashes), history=dict(working_state=dict(entries=['preserve'])))
        record = dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE',
            checkpoint_sha256=hashes, checkpoint=dict(checkpoint_sha256=hashes),
            resume_state=dict(state=state, sha256=digest(state))))
        record['sha256'] = digest(record)
        original = deepcopy(record)
        restored = saved_state(record, 20)
        expected = deepcopy(state)
        expected['deadline_unix'] = 20
        self.assertEqual(restored['state'], expected)
        self.assertEqual(record, original)
        record['document']['resume_state']['state']['rows'][0]['target'] = 'changed'
        with self.assertRaises(ValueError):
            saved_state(record, 20)

    def test_five_siege_three_math_no_old_cross_group(self):
        siege = {'conversational', 'peer_repo', 'p32', 'lr03', 'lr3'}
        math = {'r213_math_a', 'peer_math', 'r213_math_c'}
        for group in (siege, math):
            for receiver in group:
                self.assertEqual(set(GROUPS[receiver]), group - {receiver})
        self.assertNotIn('peer_repo', GROUPS['peer_math'])

    def test_exact_actual_peer_binding_and_group(self):
        response = dict(kind='RESPONSE', index=4, document=dict(response=dict(raw='Check four water tokens.')))
        response['sha256'] = digest(response)
        record = dict(kind='R184_ACT', document=dict(origin=dict(record_index=4, record_sha256=response['sha256'])))
        record['sha256'] = digest(record)
        text = peer_capsule('p32', 'peer_repo', record, response)
        self.assertIn('fictional text only', text)
        self.assertIn('never an imported target', text)
        with self.assertRaises(ValueError):
            peer_capsule('peer_repo', 'peer_math', record, response)


if __name__ == '__main__':
    unittest.main()
