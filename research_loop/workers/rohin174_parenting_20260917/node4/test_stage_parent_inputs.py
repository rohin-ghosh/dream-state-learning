"""Synthetic CPU checks for exact assignment and exposure-relative accounting."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('node4_stage', Path(__file__).with_name('stage_parent_inputs.py'))
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.assignment = json.loads(Path(__file__).with_name('R175_FROZEN_ASSIGNMENT.json').read_text())
        self.exposure = dict(actual_rendered_REQUEST=True, publication_bound=True, request_index=20, journal_id='own-life')

    def completion(self, index):
        return dict(record_index=index, journal_id='own-life', kind='SLEEP_COMPLETE', verified=True, record_sha256=str(index))

    def test_exact_assignment(self):
        self.assertTrue(stage.validate_assignment(self.assignment)['frozen'])

    def test_changed_arm_or_cadence_refused(self):
        for field, value in [('arm', 'D'), ('cadence_responses', 1)]:
            mutated = copy.deepcopy(self.assignment)
            mutated['assignments']['0'][field] = value
            with self.assertRaisesRegex(ValueError, 'exact_Main_arm_and_cadence'):
                stage.validate_assignment(mutated)

    def test_raw1_must_stop_parenting_after_baseline(self):
        self.assignment['assignments']['1']['baseline_only'] = False
        with self.assertRaisesRegex(ValueError, 'raw1_one_baseline_only'):
            stage.validate_assignment(self.assignment)

    def test_no_group_or_allocation_drift(self):
        self.assignment['assignments']['0']['group'] = 'raw'
        with self.assertRaisesRegex(ValueError, 'preserve_pair_grouping'):
            stage.validate_assignment(self.assignment)
        self.assignment['assignments']['6'] = self.assignment['assignments']['0']
        with self.assertRaisesRegex(ValueError, 'only_four'):
            stage.validate_assignment(self.assignment)

    def test_unknown_long_cap_and_cursor_cannot_be_executed(self):
        caps = dict(root=stage.ROOTS[1], runtime_caps={'segment_tokens': 512})
        with self.assertRaisesRegex(ValueError, 'V2_EXCLUDED_ORIGINAL_RAW_CONTROL'):
            stage.descriptor(1, self.assignment, None, caps)

    def test_wrong_root_refused(self):
        with self.assertRaisesRegex(ValueError, 'V2_EXCLUDED_ORIGINAL_RAW_CONTROL'):
            stage.descriptor(1, self.assignment, None, dict(root=stage.ROOTS[3]))

    def test_raw1_cannot_have_predecessor_parent(self):
        with self.assertRaisesRegex(ValueError, 'V2_EXCLUDED_ORIGINAL_RAW_CONTROL'):
            stage.descriptor(1, self.assignment, {'child_root': stage.ROOTS[1]}, dict(root=stage.ROOTS[1]))

    def test_three_completions_anchored_to_render_not_publication_or_load(self):
        result = stage.following_sleeps(self.exposure, [self.completion(index) for index in (3, 10, 21, 30, 40)])
        self.assertEqual(result['completed_after_actual_first_exposure'], 3)
        self.assertTrue(result['three_completed_sleeps_reached'])
        self.assertEqual([row['record_index'] for row in result['first_three']], [21, 30, 40])

    def test_publication_without_render_never_starts_clock(self):
        self.exposure['actual_rendered_REQUEST'] = False
        with self.assertRaisesRegex(ValueError, 'rendered_REQUEST_required'):
            stage.following_sleeps(self.exposure, [self.completion(21)])

    def test_unbound_parent_exposure_never_starts_clock(self):
        self.exposure['publication_bound'] = False
        with self.assertRaisesRegex(ValueError, 'rendered_REQUEST_required'):
            stage.following_sleeps(self.exposure, [])

    def test_sleep_request_or_unverified_completion_is_not_progress(self):
        for key, value in [('kind', 'SLEEP_REQUEST'), ('verified', False)]:
            receipt = self.completion(21)
            receipt[key] = value
            with self.assertRaisesRegex(ValueError, 'verified_completed_sleeps_only'):
                stage.following_sleeps(self.exposure, [receipt])

    def test_foreign_journal_and_duplicate_sleep_refused(self):
        receipt = self.completion(21)
        receipt['journal_id'] = 'foreign-life'
        with self.assertRaisesRegex(ValueError, 'same_life_journal'):
            stage.following_sleeps(self.exposure, [receipt])
        with self.assertRaisesRegex(ValueError, 'no_duplicate_sleep_credit'):
            stage.following_sleeps(self.exposure, [self.completion(21), self.completion(21)])

    def test_two_completions_are_not_three(self):
        result = stage.following_sleeps(self.exposure, [self.completion(21), self.completion(30)])
        self.assertFalse(result['three_completed_sleeps_reached'])

    def test_no_signal_provider_or_subprocess_surface(self):
        source = Path(stage.__file__).read_text()
        for forbidden in ('import subprocess', 'import signal', 'os.kill(', 'requests.', 'torch', 'exec('):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
