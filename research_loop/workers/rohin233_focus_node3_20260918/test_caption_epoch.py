import unittest
from unittest.mock import patch

import caption_epoch
import classroom
from pathlib import Path


class CaptionEpochTests(unittest.TestCase):
    def test_resume_preserves_started_and_refuses_live_parent(self):
        with patch('pathlib.Path.read_bytes', return_value=b'{"pid":100}'), \
                patch('pathlib.Path.exists', return_value=True):
            with self.assertRaisesRegex(ValueError, 'old_parent_must_be_absent'):
                caption_epoch.attachment_path(Path('/owned'), True, 200)
        with patch('pathlib.Path.read_bytes', return_value=b'{"pid":100}'), \
                patch('pathlib.Path.exists', return_value=False):
            self.assertEqual(caption_epoch.attachment_path(Path('/owned'), True, 200),
                Path('/owned/former_control_attachments/200.json'))

    def test_requires_explicit_new_all_five_policy(self):
        with self.assertRaises(ValueError):
            caption_epoch.helpers(None, {})

    def test_previous_classroom_still_excludes_former_control(self):
        self.assertNotIn(caption_epoch.FORMER_CONTROL, classroom.MEMBERS)
        self.assertIn(caption_epoch.FORMER_CONTROL, caption_epoch.PLAYERS)
        self.assertEqual(len(caption_epoch.PLAYERS), 5)

    def test_preserves_historical_control_not_ongoing_control(self):
        text = caption_epoch.prompt(caption_epoch.FORMER_CONTROL)
        self.assertIn('earlier unparented period is historical', text)
        self.assertIn('Astra parenting begins for you now', text)

    def test_exact_five_plain_prompts_no_bogus_scores(self):
        for name in caption_epoch.PLAYERS:
            for turn in range(5):
                text = caption_epoch.prompt(name, turn)
                self.assertTrue(text.isascii())
                self.assertLess(len(text), 2200)
                self.assertIn('actual current picture', text)
                self.assertIn('rather than inventing a result', text)
                self.assertIn('No fixed caption format', text)

    def test_parent_changes_approach(self):
        texts = [caption_epoch.prompt(caption_epoch.FORMER_CONTROL, turn) for turn in range(1, 5)]
        self.assertEqual(len(set(texts)), 4)

    def test_math_cannot_receive_caption_epoch(self):
        for name in classroom.MATH:
            with self.assertRaises(ValueError):
                caption_epoch.prompt(name)
            with patch('caption_epoch.subprocess.run') as runner:
                with self.assertRaises(ValueError):
                    caption_epoch.send(None, None, name, None, None, 0)
                runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
