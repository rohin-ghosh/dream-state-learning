import json
from pathlib import Path
import tempfile
import unittest

from judge_epoch_report import digest, summarize


class JudgeEpochReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binding = dict(player='base', primary_step=15625, primary_rank=8, shadow_step=6250,
            top_k=50, previous_seen_count=225)
        self.epoch = digest(self.binding)
        self.write('BINDING.json', self.binding)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def admission(self, caption='c' * 64, shadow=None, complete=True, unix=3601):
        admitted = dict(epoch_sha256=self.epoch, player='base', contest_id='scene1',
            caption_sha256=caption, admitted_unix=unix, shadow_due=True)
        key = digest(dict(epoch=self.epoch, contest='scene1', caption_sha256=caption))
        self.write(key + '.json', admitted)
        if complete:
            self.write(key + '.COMPLETE.json', dict(admission_sha256=digest(admitted),
                primary=dict(accepted=True, rank=20, status='new_pixel'), shadow=shadow))
        return key

    def test_cached_occurrences_are_not_new_distinct_accepts(self):
        for origin in ('a' * 64, 'b' * 64):
            self.write('ACT_' + origin + '.json', dict(epoch_sha256=self.epoch, primary_step=15625,
                primary_rank=8, origin=dict(record_sha256=origin), unix=3602,
                new_scored=1, raw_accepted=1, new_pixels=1, inherited_cached=4))
        self.admission(shadow=dict(accepted=False))
        result = summarize(self.root, self.epoch, 3700)
        self.assertEqual(result['totals']['accepted_occurrences'], 2)
        self.assertEqual(result['totals']['inherited_cache_occurrences'], 8)
        self.assertEqual(result['totals']['distinct_accepted'], 1)
        self.assertEqual(result['totals']['old_fail_new_pass'], 1)
        self.assertIsNone(result['format_faults'])
        self.assertIsNone(result['generated_tokens'])

    def test_pending_score_or_shadow_is_not_failure(self):
        self.admission(complete=False)
        self.admission(caption='d' * 64)
        result = summarize(self.root, self.epoch, 3700)['totals']
        self.assertEqual(result['pending_admissions'], 1)
        self.assertEqual(result['pending_shadows'], 1)
        self.assertEqual(result['paired_comparisons'], 0)
        self.assertEqual(result['old_fail_new_pass'], 0)

    def test_wrong_epoch_and_modified_admission_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_player_epoch'):
            summarize(self.root, 'f' * 64, 3700)
        key = self.admission()
        admission = json.loads((self.root / (key + '.json')).read_text())
        admission['admitted_unix'] += 1
        self.write(key + '.json', admission)
        with self.assertRaisesRegex(ValueError, 'completed_score_bound'):
            summarize(self.root, self.epoch, 3700)

    def test_future_admissions_do_not_leak_into_previous_hour(self):
        self.admission()
        self.admission(caption='d' * 64, unix=7300)
        result = summarize(self.root, self.epoch, 7200)
        self.assertEqual(result['totals']['distinct_scored'], 1)
        self.assertEqual(list(result['hours']), ['1970-01-01T01:00:00Z'])

    def test_empty_epoch_rate_is_unknown_not_zero(self):
        result = summarize(self.root, self.epoch, 3700)
        self.assertIsNone(result['totals']['distinct_accept_rate'])
        self.assertEqual(result['hours'], {})

    def test_scored_rank_over_threshold_cannot_be_called_accepted(self):
        key = self.admission()
        complete = json.loads((self.root / (key + '.COMPLETE.json')).read_text())
        complete['primary']['rank'] = 51
        self.write(key + '.COMPLETE.json', complete)
        with self.assertRaisesRegex(ValueError, 'accepted_rank_at_most'):
            summarize(self.root, self.epoch, 3700)


if __name__ == '__main__':
    unittest.main()
