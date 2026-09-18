import unittest

from caption_hourly_service import markdown, project
from judge_epoch_report import counters


class HourlyReportTests(unittest.TestCase):
    def audit(self):
        bucket=dict(counters(),act_origins=5,distinct_scored=3,distinct_accepted=2,
            distinct_new_pixels=1,distinct_accept_rate=2/3)
        player=dict(player='base',epoch_sha256='a'*64,totals=bucket,
            hours={'2026-09-18T20:00:00Z':bucket})
        return dict(observed_utc='2026-09-18T20:59:00+00:00',roles=[dict(role='BASE',players=[player])])

    def test_epoch_and_window_counts_are_preserved_without_old_cache_addition(self):
        report=project(self.audit(),dict(path='audit.json',sha256='b'*64))
        self.assertFalse(report['old_and_new_epochs_combined'])
        self.assertEqual(report['players'][0]['cumulative']['distinct_accepted'],2)
        self.assertIn('2026-09-18T20:00:00Z',markdown(report))
        self.assertIn('66.7%',markdown(report))

    def test_unmeasured_fields_are_null_not_zero(self):
        player=project(self.audit(),{})['players'][0]
        for key in ('parsed_captions','format_faults','no_caption_acts','generated_tokens'):
            self.assertIsNone(player[key])

    def test_source_failure_is_not_a_zero_player(self):
        audit=self.audit()
        audit['roles'].append(dict(role='P3',status='READ_FAILED_NOT_ZERO_COUNTS'))
        report=project(audit,dict(path='audit.json'))
        self.assertEqual(len(report['players']),1)
        self.assertEqual(len(report['errors']),1)
        self.assertIn('no zero counts substituted',markdown(report))


if __name__=='__main__':
    unittest.main()
