import inspect
from pathlib import Path
import unittest

try:
    import orch_r132_gen7_feed_registration as candidate
    import orch_r119_l1_c3_feed as feed
    import orch_r119_l1_c3_consumer as consumer
    import orch_r119_l1_c3_scanned_resume as scanned
except ImportError:
    from gpu import orch_r132_gen7_feed_registration as candidate
    from gpu import orch_r119_l1_c3_feed as feed
    from gpu import orch_r119_l1_c3_consumer as consumer
    from gpu import orch_r119_l1_c3_scanned_resume as scanned


class RegistrationTests(unittest.TestCase):
    def fixture(self):
        task=next(iter(candidate.CANDIDATES));count,digest=candidate.CANDIDATES[task]
        return (dict(root=str(candidate.GEN7),source_registration_id=candidate.REGISTRATION),
            dict(source_task_id=task,path='segment0000/gpu7/CALL_%06d.json'%count,call_sha256=digest),
            dict(source_task_id=task,cumulative_call=count,new_segment_call=count-15842))

    def test_exact_current_source_accepted(self):
        candidate.candidate_binding(*self.fixture())

    def test_other_historical_root_rejected(self):
        registration,review,row=self.fixture();registration['root']=str(candidate.GEN7.parent/'old_root')
        with self.assertRaises(AssertionError):candidate.candidate_binding(registration,review,row)

    def test_path_escape_and_wrong_capture_rejected(self):
        for path in ('../CALL_023244.json','segment0000/gpu6/CALL_023244.json','/tmp/CALL_023244.json'):
            registration,review,row=self.fixture();review['path']=path
            with self.assertRaises(AssertionError):candidate.candidate_binding(registration,review,row)

    def test_hash_and_cursor_not_reset(self):
        registration,review,row=self.fixture();review['call_sha256']='0'*64
        with self.assertRaises(AssertionError):candidate.candidate_binding(registration,review,row)
        registration,review,row=self.fixture();row['new_segment_call']=1
        with self.assertRaises(AssertionError):candidate.candidate_binding(registration,review,row)

    def test_shared_global_boundary_not_wallclock(self):
        for arm in ('FULL','CONTROL'):
            self.assertEqual(candidate.cohort_for(19172,19428),'C3')
            self.assertEqual(candidate.cohort_for(19428,19428),'R132_C4')
            self.assertEqual(candidate.cohort_for(19556,19428),'R132_C4')
        with self.assertRaises(AssertionError):candidate.cohort_for(19429,19428)

    def test_only_parent_size_and_publication_labels_changed(self):
        original=inspect.getsource(feed.prepare)
        actual=candidate.publication_source(original)
        for before,after in {
            "len(previous_rows) == 22, 'exact_parent22'":"len(previous_rows) == 19, 'exact_old19'",
            "cohort_id='R132_GEN7_EXPERIENCE_C4_B004'":"cohort_id='R119_EXPERIENCE_C3_B003'",
            'batch_number=4':'batch_number=3','parent22_digest=':'old19_digest=',
            'parent22_encoded_digest=':'old19_encoded_digest=',
        }.items():actual=actual.replace(before,after)
        self.assertEqual(original,actual)
        compile(candidate.publication_source(original),'fixture','exec')

    def test_unchanged_review_limit_and_semantic_gate(self):
        with self.assertRaises((ValueError,AssertionError)):
            feed.bounded_reviews([dict(source_task_id=str(index)) for index in range(4)])
        with self.assertRaises((ValueError,AssertionError)):
            feed.bounded_reviews([dict(source_task_id='same')]*2)
        with self.assertRaises(AssertionError):
            feed.feed.experience.review_gate(dict(full_text_read=False),{}, {})

    def test_safe_handoff_preserves_native_and_optimizer_checks(self):
        source=candidate.handoff_source(inspect.getsource(consumer.handoff),scanned.modern_handoff_source)
        for text in ('completed_exit(',"heartbeat.get('condition') != 'OFF'",'readout_proof(',
                     "trainer.sha(checkpoint/'optimizer.pt')","trainer.sha(checkpoint/'rank0.pt')",
                     "'next_train_already_started'","'common_future_boundary_already_passed'",'os.pidfd_open'):
            self.assertIn(text,source)
        compile(source,'fixture','exec')

    def test_unknown_frozen_source_rejected(self):
        with self.assertRaises(AssertionError):candidate.publication_source('def prepare(): pass')


if __name__=='__main__':unittest.main()
