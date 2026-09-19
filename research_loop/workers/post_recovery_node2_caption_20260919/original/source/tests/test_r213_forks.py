"""New lineage identities, group confinement and source-bound native peers."""

import hashlib
import json
import unittest

from gpu.r213_fork_policy import ASSIGNMENTS, FORKS, GROUPS, prompt
from gpu.r213_fork_runtime import capsule
from organism_v6.orch_r125_plain_context import has_scaffolding


def bound(record):
    record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return record


class ForkTests(unittest.TestCase):
    def test_exact_new_five_free_slots(self):
        self.assertEqual(sorted(ASSIGNMENTS[name][0] for name in FORKS), [2, 3, 5, 6, 7])
        self.assertEqual(len(ASSIGNMENTS), 8)
        self.assertFalse({'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3'} & set(ASSIGNMENTS))

    def test_group_topology_has_no_old_cross_group(self):
        for receiver, peers in GROUPS.items():
            self.assertNotIn(receiver, peers)
            expected_size = 4 if ASSIGNMENTS[receiver][1] == 'siege' else 2
            self.assertEqual(len(peers), expected_size)
            for sender in peers:
                self.assertEqual(ASSIGNMENTS[sender][1], ASSIGNMENTS[receiver][1])

    def test_parent_fresh_lineage_not_tail_continuation(self):
        for name in FORKS:
            for turn in range(4):
                text = prompt(name, turn)
                self.assertTrue(text.isascii())
                self.assertFalse(has_scaffolding(text))
                self.assertIn('not a continuation', text)
                self.assertIn('sixteen presentations', text)
                self.assertIn('No code executor', text)

    def test_peer_bound_and_wrong_group_rejected(self):
        response = bound(dict(kind='RESPONSE', index=8, document=dict(response=dict(raw='Check the ledger.'))))
        record = bound(dict(kind='R184_ACT', document=dict(origin=dict(record_index=8,
            record_sha256=response['sha256']))))
        text = capsule('conversational', 'r213_siege_scout_fork', record, response)
        self.assertIn('masked context', text)
        with self.assertRaises(ValueError):
            capsule('conversational', 'r213_math_b_fork', record, response)
        response['document']['response']['raw'] = 'altered'
        with self.assertRaisesRegex(ValueError, 'binding'):
            capsule('conversational', 'r213_siege_scout_fork', record, response)


if __name__ == '__main__':
    unittest.main()
