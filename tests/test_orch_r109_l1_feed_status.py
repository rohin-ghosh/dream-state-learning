import unittest
try:
    import orch_r109_l1_feed_status as status
except ImportError:
    from gpu import orch_r109_l1_feed_status as status


class FeedStatusTests(unittest.TestCase):
    def test_hour_is_measured_window_not_extrapolated(self):
        decisions = [dict(status='ADMITTED',admitted_unix=timestamp) for timestamp in (100,3700,4000)]
        decisions.append(dict(status='REJECTED'))
        self.assertEqual(status.admission_rate(decisions,3800),
                         dict(new_unique_total=3,newly_admitted_last3600=1,last_admission_unix=4000))

    def test_old_target_not_counted_as_fresh_training(self):
        eligible = [dict(source_task_id='old',target_sha256='old',source_call_sha256='a'),
                    dict(source_task_id='new',target_sha256='new',source_call_sha256='b')]
        loss = dict(update=12141,finished_unix=100,eligible_supervised_tokens=12,
                    selections=[['anchor',0],['eligible',1]])
        self.assertEqual(status.selected_new(loss,eligible,{'old'})[0]['target_sha256'],'new')
        self.assertEqual(status.selected_new(dict(loss,selections=[['eligible',0]]),eligible,{'old'}),[])

    def test_masked_control_selection_is_not_training(self):
        loss = dict(update=12141,finished_unix=100,eligible_supervised_tokens=0,
                    selections=[['eligible',1]])
        self.assertEqual(status.selected_new(loss,[],set()),[])


if __name__ == '__main__':
    unittest.main()
