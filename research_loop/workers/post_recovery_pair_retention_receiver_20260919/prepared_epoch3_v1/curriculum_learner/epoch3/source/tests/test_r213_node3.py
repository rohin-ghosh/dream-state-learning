"""CPU gates for bounded R213 objects and exact peer provenance."""

from copy import deepcopy
import hashlib
import json
import unittest

from gpu.r213_node3_runtime import capsule
from gpu.r213_policy import ASSIGNMENTS, PROBLEMS, prompt
from organism_v6.orch_r125_plain_context import has_scaffolding


def bind(record):
    record['sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return record


class R213Tests(unittest.TestCase):
    def test_allocation_and_parent_visibility(self):
        self.assertEqual(sorted(value[0] for value in ASSIGNMENTS.values()), list(range(8)))
        self.assertEqual(sum(value[1] == 'siege' for value in ASSIGNMENTS.values()), 5)
        for name in ASSIGNMENTS:
            for turn in range(4):
                text = prompt(name, turn)
                self.assertTrue(text.isascii())
                self.assertFalse(has_scaffolding(text))
                self.assertIn('not matched fresh causality', text)
                self.assertIn('No code executor', text)

    def test_math_shared_objects_and_styles(self):
        for name in ('r213_math_a', 'peer_math', 'r213_math_c'):
            self.assertIn(PROBLEMS[0], prompt(name, 0))
            self.assertIn(PROBLEMS[1], prompt(name, 2))
        solutions = [(small, large) for small in range(8) for large in range(5)
            if 3 * small + 5 * large == 23]
        self.assertEqual(solutions, [(1, 4), (6, 1)])

    def test_exact_peer_source_binding(self):
        response = bind(dict(kind='RESPONSE', index=20, document=dict(response=dict(raw='One and four bags.'))))
        record = bind(dict(kind='R184_ACT', index=22, document=dict(origin=dict(
            record_index=20, record_sha256=response['sha256']))))
        text = capsule('peer_math', record, response)
        self.assertIn('One and four bags.', text)
        self.assertIn('no imported training targets', text)
        altered = deepcopy(response)
        altered['document']['response']['raw'] = 'Changed'
        with self.assertRaisesRegex(ValueError, 'binding'):
            capsule('peer_math', record, altered)
        with self.assertRaises(ValueError):
            capsule('peer_repo', record, response)

    def test_fiction_and_conversation_boundaries(self):
        text = prompt('conversational')
        self.assertIn('Genuine new Rohin conversation takes priority', text)
        self.assertIn('Closed text-only fictional', text)
        self.assertIn('do not accept an assertion', text)
        self.assertIn('Do not invent peer messages', text)


if __name__ == '__main__':
    unittest.main()
