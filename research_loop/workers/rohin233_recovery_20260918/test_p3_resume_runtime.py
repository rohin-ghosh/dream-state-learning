from copy import deepcopy
import unittest

from organism_v6.orch_r125_continual_stream import digest
import p3_resume_runtime


class SavedBoundaryTests(unittest.TestCase):
    def record(self):
        checkpoint = {'adapter': 'adapter_digest', 'optimizer': 'optimizer_digest', 'rng': 'optimizer_digest'}
        state = dict(pending=None, sleep_frontier=1, rows=[{'text': 'original'}],
            model_state_sha256=digest(checkpoint), deadline_unix=1789754400)
        record = dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE',
            resume_state=dict(state=state, sha256=digest(state)), checkpoint_sha256=checkpoint,
            checkpoint=dict(checkpoint_sha256=checkpoint)))
        record['sha256'] = digest(record)
        return record

    def test_original_saved_state_and_deadline_preserved(self):
        record = self.record()
        saved = p3_resume_runtime.restored_state(record)
        self.assertEqual(saved, record['document']['resume_state'])
        self.assertIsNot(saved['state'], record['document']['resume_state']['state'])

    def test_modified_record_rejected(self):
        record = self.record()
        record['document']['status'] = 'FAILED'
        with self.assertRaises(ValueError):
            p3_resume_runtime.restored_state(record)

    def test_pending_generation_or_unslept_rows_rejected(self):
        for changed in ({'pending': 'generation'}, {'sleep_frontier': 0}):
            record = deepcopy(self.record())
            saved = record['document']['resume_state']
            saved['state'].update(changed)
            saved['sha256'] = digest(saved['state'])
            record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})
            with self.assertRaises(ValueError):
                p3_resume_runtime.restored_state(record)
