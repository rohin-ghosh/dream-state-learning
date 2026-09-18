from dataclasses import asdict
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from exposure_probe import ROOTS, request_exposes, validate_entry
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory


class ExposureTests(unittest.TestCase):
    def fixture(self):
        event = TrainEvent(event_id='parent:inbox:cpu', actor='parent', text='Astra: bounded fixture',
            split='TRAIN', phase='experience', episode_id='continual_stream', source_id='/CPU_ONLY',
            source_sha256='0' * 64, origin='TRAIN_COLLECTION')
        document = dict(resume_state=dict(state=dict(history=dict(events=[asdict(event)], operations=[]))),
                        messages=[TrainHistory._message(event)])
        return event, document

    def test_actual_visible_event_and_rendered_message(self):
        event, document = self.fixture()
        self.assertTrue(request_exposes(document, event))

    def test_registration_without_render_not_exposure(self):
        event, document = self.fixture()
        document['messages'] = []
        self.assertFalse(request_exposes(document, event))

    def test_render_without_exact_history_not_exposure(self):
        event, document = self.fixture()
        document['resume_state']['state']['history']['events'] = []
        self.assertFalse(request_exposes(document, event))

    def test_evicted_event_not_exposure(self):
        event, document = self.fixture()
        document['resume_state']['state']['history']['operations'] = [dict(through=dict(event_count=1))]
        self.assertFalse(request_exposes(document, event))

    def test_controls_and_wrong_publication_refused(self):
        root = next(iter(ROOTS))
        entry = dict(root=root, publication=dict(id='a' * 32,
            path=root + '/stream/inbox/' + 'a' * 32 + '.json', sha256='b' * 64),
            source_record_count=1, source_head_sha256='c' * 64)
        validate_entry(entry)
        with self.assertRaisesRegex(ValueError, 'learning_TRAIN'):
            validate_entry(dict(entry, root='/localhome/local-rohing/orch_frozen/run1'))
        with self.assertRaisesRegex(ValueError, 'publication'):
            validate_entry(dict(entry, publication=dict(entry['publication'], path='/CPU_OTHER')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
