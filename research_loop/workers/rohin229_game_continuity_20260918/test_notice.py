import unittest

from notice import TEXT
from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_plain_context import event_message


class NoticeTests(unittest.TestCase):
    def test_plain_environment_instruction_not_score_or_parent_reply(self):
        event = TrainEvent(event_id='environment:continuity', actor='environment', text='Tool: ' + TEXT,
            split='TRAIN', phase='feedback', episode_id='continual_stream', source_id='/tmp/notice.json',
            source_sha256='c' * 64, origin='TRAIN_COLLECTION')
        rendered = event_message(event)
        self.assertEqual(rendered['role'], 'user')
        self.assertIn('keep guessing — write new captions every opportunity', rendered['content'])
        self.assertIn('not a score', rendered['content'])
        self.assertNotIn('Rohin:', rendered['content'])


if __name__ == '__main__':
    unittest.main()
