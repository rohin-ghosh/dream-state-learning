from copy import deepcopy
import unittest

try:
    import orch_r109_l1_feed_append as append
except ImportError:
    from gpu import orch_r109_l1_feed_append as append


class AppendTests(unittest.TestCase):
    def fixture(self):
        old=[dict(target_sha256='old',source_task_id='old')]
        new=dict(target_sha256='new',source_task_id='new',source_label=append.feed.experience.SOURCE_LABEL,
                 split='TRAIN',teacher_or_l2=False,target_actor='CHILD',parent_text_masked=True)
        encoded=dict(eligible=['old_encoding'],anchor=['base'],prior=['prior'],legacy=['legacy'])
        return old,old+[new],encoded,dict(encoded,eligible=['old_encoding','new_encoding'])

    def test_append_keeps_old_rows_and_all_rehearsal_sources(self):
        append.validate_extension(*self.fixture())

    def test_replacing_prior_history_or_encoding_rejected(self):
        old,rows,previous,encoded=self.fixture()
        for key in ('anchor','prior','legacy','eligible'):
            changed=deepcopy(encoded)
            changed[key]=['replacement']
            with self.assertRaises(ValueError):
                append.validate_extension(old,rows,previous,changed)

    def test_no_reordering_or_deletion_of_previous_rows(self):
        old,rows,previous,encoded=self.fixture()
        with self.assertRaises(ValueError):
            append.validate_extension(old,list(reversed(rows)),previous,encoded)
        with self.assertRaises(ValueError):
            append.validate_extension(old,old,previous,previous)

    def test_no_silent_parented_or_held_source(self):
        for change in (dict(teacher_or_l2=True),dict(split='DEV'),dict(split='FINAL'),
                       dict(target_actor='PARENT'),dict(parent_text_masked=False)):
            old,rows,previous,encoded=self.fixture()
            rows[-1].update(change)
            with self.assertRaises(ValueError):
                append.validate_extension(old,rows,previous,encoded)

    def test_no_duplicate_task_or_target(self):
        for key in ('source_task_id','target_sha256'):
            old,rows,previous,encoded=self.fixture()
            rows[-1][key]='old'
            with self.assertRaises(ValueError):
                append.validate_extension(old,rows,previous,encoded)


if __name__=='__main__':
    unittest.main()
