from copy import deepcopy
import unittest

import pending_sleep_contract as contract


class StartupRelocationTests(unittest.TestCase):
    def setUp(self):
        self.original = dict(source_root='/original/source', root='/unchanged/guest',
            hard_end_unix=1790272800, birth_prompt='Identical birth text',
            startup_context=dict(version='R127_STARTUP_V1', path='/original/source/context/startup.md',
                sha256='a' * 64), other=dict(unchanged=True))

    def test_only_location_changes_hash_and_text_survive(self):
        before = deepcopy(self.original)
        actual = contract.relocated_execution_plan(self.original, '/same_life/staged_source')
        expected = deepcopy(before)
        expected['source_root'] = '/same_life/staged_source'
        expected['startup_context']['path'] = '/same_life/staged_source/context/startup.md'
        self.assertEqual(actual, expected)
        self.assertEqual(self.original, before)

    def test_no_startup_does_not_invent_one(self):
        self.original.pop('startup_context')
        self.assertEqual(contract.relocated_execution_plan(self.original, '/new'),
            dict(self.original, source_root='/new'))

    def test_external_startup_cannot_be_imported(self):
        self.original['startup_context']['path'] = '/unrelated/private.md'
        with self.assertRaisesRegex(ValueError, 'inside_original_source'):
            contract.relocated_execution_plan(self.original, '/new')

    def test_parent_traversal_is_rejected(self):
        self.original['startup_context']['path'] = '/original/source/../private.md'
        with self.assertRaisesRegex(ValueError, 'unredirected_path'):
            contract.relocated_execution_plan(self.original, '/new')

    def test_source_root_itself_is_not_a_startup_file(self):
        self.original['startup_context']['path'] = '/original/source'
        with self.assertRaisesRegex(ValueError, 'inside_original_source'):
            contract.relocated_execution_plan(self.original, '/new')

    def test_unknown_startup_fields_are_not_permitted(self):
        self.original['startup_context']['hidden'] = 'different content'
        with self.assertRaisesRegex(ValueError, 'exact_original_startup_descriptor'):
            contract.relocated_execution_plan(self.original, '/new')

    def test_invalid_destination_is_rejected(self):
        for destination in ['relative/source', '/source/../other']:
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(ValueError, 'absolute_staged_source'):
                    contract.relocated_execution_plan(self.original, destination)


if __name__ == '__main__':
    unittest.main()
