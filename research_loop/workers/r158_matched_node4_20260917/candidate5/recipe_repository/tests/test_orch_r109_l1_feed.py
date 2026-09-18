from copy import deepcopy
import unittest
try:
    import orch_r109_l1_feed as feed
except ImportError:
    from gpu import orch_r109_l1_feed as feed


class FeedTests(unittest.TestCase):
    def fixture(self):
        plan = dict(supplement_archive_sha256='newarchive', original_source_archive_sha256='oldarchive',
                    policy_sha256='policy', generation_seed_unchanged='seed')
        review = dict(path='generation_v3/gpu4/CALL_1.json', source_task_id='task1', full_text_read=True,
                      functional_verdict='PASS', grounding_verdict='PASS', evidence='Actual unit conversion used',
                      property='TASK_CONSTRAINT_USED')
        row = dict(source_archive_sha256='newarchive', original_environment_archive_sha256='oldarchive',
                   prompt_policy_sha256='policy', source_state_sha256='seed', source_tasks_sha256='tasks',
                   source_label=feed.experience.SOURCE_LABEL, split='TRAIN', parent_calls=0, family='math',
                   source_task_id='task1', response=dict(terminal=True,truncated=False),outcome=dict(correct=True))
        return plan, review, row, dict(id='task1')

    def test_reviewed_grounded_native_source_passes(self):
        plan, review, row, task = self.fixture()
        feed.source_gate(review,row,task,plan,'tasks')

    def test_outcome_alone_and_unknown_review_never_admit(self):
        plan, review, row, task = self.fixture()
        for mutation in [dict(full_text_read=False),dict(functional_verdict='UNKNOWN'),dict(evidence=''),
                         dict(property='TEMPLATE_OR_BRANCH_COUNT')]:
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                feed.source_gate(dict(review,**mutation),row,task,plan,'tasks')

    def test_parented_or_held_source_is_not_silently_mixed(self):
        plan, review, row, task = self.fixture()
        for mutation in [dict(parent_calls=1),dict(split='DEV'),dict(split='FINAL'),
                         dict(source_label='R109_CORRECTED_L2_CHILD_CONTINUATION')]:
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                feed.source_gate(review,dict(row,**mutation),task,plan,'tasks')
        with self.assertRaises(ValueError):
            feed.source_gate(review,dict(row,teacher_or_l2=True),task,plan,'tasks')

    def test_wrong_archive_seed_policy_or_roster_is_rejected(self):
        plan, review, row, task = self.fixture()
        for field in ['source_archive_sha256','original_environment_archive_sha256','prompt_policy_sha256',
                      'source_state_sha256','source_tasks_sha256']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                feed.source_gate(review,dict(row,**{field:'wrong'}),task,plan,'tasks')

    def test_truncation_or_incorrect_outcome_is_rejected(self):
        plan, review, row, task = self.fixture()
        for mutation in [dict(response=dict(terminal=True,truncated=True)),dict(outcome=dict(correct=False))]:
            with self.assertRaises(AssertionError):
                feed.source_gate(review,dict(row,**mutation),task,plan,'tasks')

    def test_path_escape_or_old_generation_path_is_rejected(self):
        plan, review, row, task = self.fixture()
        for path in ['generation/gpu4/CALL_1.json','generation_v3/gpu4/../../held.json']:
            with self.assertRaises(ValueError):
                feed.source_gate(dict(review,path=path),row,task,plan,'tasks')

    def test_batch_rollover_is_deterministic_and_segment_pinned(self):
        self.assertEqual([feed.choose_version(segment,[0,1]) for segment in range(4)],[0,1,1,1])
        self.assertEqual(feed.choose_version(4,[0,1,2]),2)
        for segment, available in [(-1,[0]),(0,[]),(2,[0,2])]:
            with self.assertRaises(ValueError):
                feed.choose_version(segment,available)

    def test_readout_boundary_requires_complete_ON_OFF_and_held(self):
        heartbeat=dict(phase='readout',condition='OFF',resume='/checkpoints/000012004')
        value=dict(status='COMPLETE',capability_calls=32,behavior_calls=16,base_and_adapter_unchanged=True,
                   parent_access=False,training_ingestion=False,checkpoint_state_sha256='state')
        summaries=dict(ON=deepcopy(value),OFF=deepcopy(value))
        self.assertTrue(feed.safe_readout(heartbeat,summaries,12004,'state'))
        self.assertFalse(feed.safe_readout(heartbeat,summaries,12004,'different_commit'))
        self.assertFalse(feed.safe_readout(dict(heartbeat,condition='ON'),summaries,12004,'state'))
        self.assertFalse(feed.safe_readout(heartbeat,summaries,12005,'state'))
        for mutation in [dict(capability_calls=31),dict(behavior_calls=15),dict(training_ingestion=True),
                         dict(parent_access=True),dict(checkpoint_state_sha256='other')]:
            self.assertFalse(feed.safe_readout(heartbeat,dict(summaries,OFF=dict(value,**mutation)),12004,'state'))

    def test_extracted_source_tampering_rejected(self):
        from gpu.orch_math_rich_source import verify_archive
        from pathlib import Path
        import tempfile
        import tarfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'helper.py'
            source.write_text('original')
            archive = root / 'source.tar'
            with tarfile.open(archive,'w') as stream:
                stream.add(source,arcname='helper.py')
            self.assertEqual(verify_archive(archive,root),1)
            source.write_text('changed')
            with self.assertRaises(ValueError):
                verify_archive(archive,root)

    def test_original_lifetime_slots_and_optimizer_schedule_preserved(self):
        self.assertEqual(feed.END,1789491360)
        self.assertEqual(feed.CUTOFF,1789491060)
        self.assertEqual(feed.SLOTS,dict(FULL=5,CONTROL=6))
        self.assertEqual(feed.experience.positions(9445,9444,3635,9)[-1],('eligible',0))
        self.assertEqual(feed.experience.positions(9453,9444,3635,9)[-1],('eligible',1))
        self.assertEqual(feed.experience.labels_for('CONTROL','eligible',[1,2]),[-100,-100])


if __name__ == '__main__':
    unittest.main()
