from copy import deepcopy
import unittest
import astra_birth_protocol_clarified_material_20260913 as material


class ClarificationTests(unittest.TestCase):
    def test_only_uniform_wake_suffix_changes(self):
        old = material.base.build_candidate()
        new = material.build_candidate()
        self.assertTrue(material.check_candidate(new)['ok'])
        changed = 0
        for before, after in zip(old['cases'], new['cases'], strict=True):
            expected = before['context'] + (material.CLARIFICATION if before['role'] == 'wake' else '')
            self.assertEqual(after['context'], expected)
            changed += before['context'] != after['context']
        self.assertEqual(changed, 12)

    def test_requests_identical_except_prompt(self):
        old = material.base.call_map(material.base.build_candidate())
        new = material.call_map(material.build_candidate())
        self.assertEqual(new['OFF'], new['AUTH'])
        for state in material.STATES:
            for before, after in zip(old[state], new[state], strict=True):
                self.assertEqual({key:value for key,value in before.items() if key != 'prompt'},
                                 {key:value for key,value in after.items() if key != 'prompt'})
                self.assertEqual(set(after), set(before))

    def test_labels_and_scores_unchanged(self):
        candidate = material.build_candidate()
        outputs = {state:{case['id']:case['auth_example_target'] for case in candidate['cases']} for state in material.STATES}
        self.assertEqual(material.check_outputs(candidate, outputs),
                         material.base.check_outputs(material.base.build_candidate(), outputs))

    def test_all32_barrier_retained(self):
        with self.assertRaises(ValueError):
            material.check_outputs(material.build_candidate(), {'OFF':{}})

    def test_tampering_rejected(self):
        candidate = material.build_candidate()
        candidate['cases'][0]['context'] += 'extra'
        with self.assertRaises(ValueError):
            material.check_candidate(candidate)

    def test_record_negative_controls_unchanged(self):
        requests = material.call_map(material.build_candidate())
        original = material.base.call_map(material.base.build_candidate())
        for state in material.STATES:
            records = [row for row in requests[state] if row['role'] == 'record']
            self.assertEqual(records, [row for row in original[state] if row['role'] == 'record'])
            self.assertEqual(len(records), 4)


if __name__ == '__main__':
    unittest.main()
