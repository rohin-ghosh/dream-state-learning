import unittest
from gpu.orch_r119_l1_c3_status import actual_selections


class ExposureTests(unittest.TestCase):
    def test_only_actual_new_target_selection_counts(self):
        targets={19:dict(target_sha256='new',source_task_id='task')}
        rows=[dict(update=1,selections=[['eligible',18]],eligible_supervised_tokens=100),
              dict(update=2,selections=[['eligible',19]],eligible_supervised_tokens=109)]
        result=actual_selections(rows,targets)['new']
        self.assertEqual(result['presentations'],1)
        self.assertEqual(result['active_tokens'],109)
        self.assertEqual(result['updates'],[2])

    def test_control_presentation_not_training_tokens(self):
        targets={19:dict(target_sha256='new',source_task_id='task')}
        result=actual_selections([dict(update=9,selections=[['eligible',19]],eligible_supervised_tokens=0)],targets)['new']
        self.assertEqual(result['presentations'],1)
        self.assertEqual(result['active_tokens'],0)

    def test_no_publication_only_adoption_claim(self):
        targets={19:dict(target_sha256='new',source_task_id='task')}
        self.assertEqual(actual_selections([],targets)['new']['presentations'],0)


if __name__=='__main__':unittest.main()
