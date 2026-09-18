import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from inventory_node1 import Reader, scoped_plan_path, unchanged
from stage_node1 import prepare_rows, reserved_cursor


def fixture():
    parents = []
    for physical in range(8):
        root = '/localhome/local-rohing/orch_test_' + str(physical)
        parents.append(dict(physical=physical, label='lane' + str(physical),
                            reserved_cursor_at_start=100, attempts=[], unique_live_native=True,
                            natives=[dict(plan_fields=dict(root=root, physical=physical),
                                          control_native=physical in (0, 1))],
                            fields=dict(root=root, cadence_responses=3, hard_end_unix=1790442300),
                            controls_frozen=physical in (0, 1), parent={}, config={}, source={}, output=root))
    return dict(parents=parents)


class StagingTests(unittest.TestCase):
    def test_all_eight_with_controls_unchanged(self):
        rows = prepare_rows(fixture())
        self.assertEqual(len(rows), 8)
        for row in rows[:2]:
            self.assertEqual(row['proposed_alternatives'], {})
            self.assertEqual(row['required_action'], 'PRESERVE_FROZEN_CONTROL')

    def test_no_arm_or_delivery_inferred(self):
        for row in prepare_rows(fixture()):
            self.assertIsNone(row['selected_arm'])
            self.assertFalse(row['first_turn_published'])
            self.assertFalse(row['request_exposure_verified'])

    def test_r175_baseline_all_six_without_c2_wait(self):
        for row in prepare_rows(fixture())[2:]:
            self.assertEqual(row['required_baseline'], 'C2_OBSERVATION_TO_ACTION')
            self.assertEqual(row['initial_baseline_word_cap'], 90)
            self.assertFalse(row['wait_for_c2_success'])
            self.assertFalse(row['unchanged_r166_learning_control'])
            self.assertTrue(row['dense_a_requires_main_longcap_pass'])

    def test_no_retirement_or_pass_inferred_from_staging(self):
        for row in prepare_rows(fixture()):
            self.assertEqual(row['incomplete_check_status'], 'UNKNOWN')
            self.assertFalse(row['retirement_authorized'])
            self.assertEqual(row['completed_sleep_check_after'], None if row['physical'] < 2 else 3)

    def test_proposed_cadences_after_reservation(self):
        alternatives = prepare_rows(fixture())[2]['proposed_alternatives']
        self.assertEqual({arm: value['next_response_threshold'] for arm, value in alternatives.items()},
                         dict(A=101, B=102, C=103, D=103))

    def test_unsettled_reservation_not_replayed(self):
        document = fixture()
        document['parents'][2]['attempts'] = [dict(attempt='parent_000001', settled=False, response_count=123)]
        row = prepare_rows(document)[2]
        self.assertEqual(row['reserved_response_cursor'], 123)
        self.assertEqual(row['unsettled_attempts'], ['parent_000001'])

    def test_missing_or_silent_consumes_reservation(self):
        for status in ('MISSING', 'SILENT', 'PUBLISHED'):
            with self.subTest(status=status):
                row = fixture()['parents'][2]
                row['attempts'] = [dict(status=status, response_count=123, source_response_count=123,
                                        head_sha256='head', source_head_sha256='head',
                                        **{'SOURCE.json': {}, 'RESULT.json': {}})]
                self.assertEqual(reserved_cursor(row), 123)

    def test_mismatched_terminal_refused(self):
        row = fixture()['parents'][2]
        row['attempts'] = [dict(status='PUBLISHED', response_count=123, source_response_count=122,
                                head_sha256='head', source_head_sha256='head',
                                **{'SOURCE.json': {}, 'RESULT.json': {}})]
        with self.assertRaisesRegex(ValueError, 'bound_terminal'):
            reserved_cursor(row)

    def test_wrong_roster_refused(self):
        document = fixture()
        document['parents'].pop()
        with self.assertRaisesRegex(ValueError, 'exact_eight'):
            prepare_rows(document)

    def test_wrong_native_or_control_refused(self):
        for key, value in (('unique_live_native', False), ('controls_frozen', True)):
            with self.subTest(key=key):
                document = fixture()
                document['parents'][2][key] = value
                with self.assertRaises(ValueError):
                    prepare_rows(document)

    def test_same_pid_new_ticks_not_owner(self):
        before = dict(pid=7, ticks='1', uid=10, cwd='/source', argv_sha256='argv')
        after = dict(before, ticks='2')
        self.assertFalse(unchanged(before, after))

    def test_read_limits_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'metadata.json'
            path.write_bytes(b'abcd')
            reader = Reader(3)
            with patch.object(Path, 'open', side_effect=AssertionError('must not open')):
                with self.assertRaisesRegex(ValueError, 'budget'):
                    reader.raw(path)
            self.assertEqual(reader.used, 0)

    def test_aggregate_limit_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'metadata.json'
            path.write_bytes(b'abcd')
            reader = Reader(4)
            self.assertEqual(reader.raw(path), b'abcd')
            with self.assertRaisesRegex(ValueError, 'budget'):
                reader.raw(path)
            alias = Path(directory) / 'alias.json'
            alias.symlink_to(path)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                Reader().raw(alias)

    def test_key_and_cross_scope_paths_refused(self):
        for path in ('/home/user/.ssh/key.json', '/localhome/local-rohing/orch_x/../key.json',
                     '/localhome/local-rohing/orch_x/key.pem'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                scoped_plan_path(path)

    def test_staging_does_not_mutate_inventory(self):
        document = fixture()
        original = copy.deepcopy(document)
        prepare_rows(document)
        self.assertEqual(document, original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
