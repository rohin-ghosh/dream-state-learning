import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c0_reading_turn as reading
import caption_parent as caption
import caption_remote as transport


class ReadingTests(unittest.TestCase):
    def test_one_visible_source_question_no_retention_claim(self):
        text = reading.reading_question('PUBLIC DEVELOPMENT PASSAGE')
        self.assertIn('PUBLIC DEVELOPMENT PASSAGE', text)
        self.assertIn('Name one concrete action', text)
        self.assertIn('unsure', text)
        self.assertIn('not a memory test', text)
        self.assertNotIn('solve', text)

    def test_pending_publication_never_overwritten(self):
        self.assertIsNone(reading.focused_topic(lambda state: None, {'publications': 16}, 16))

    def test_two_turns_then_original_diverse_curriculum(self):
        original = lambda state: 'science'
        self.assertEqual(reading.focused_topic(original, {'publications': 16}, 16), 'reading')
        self.assertEqual(reading.focused_topic(original, {'publications': 17}, 16), 'writing')
        self.assertEqual(reading.focused_topic(original, {'publications': 18}, 16), 'science')

    def test_writing_follows_actual_response_without_crediting_uptake(self):
        text = reading.writing_question('PUBLIC DEVELOPMENT PASSAGE', 123)
        self.assertIn('RESPONSE123', text)
        self.assertIn('what you invent', text)
        self.assertNotIn('you remembered', text)


class CaptionTests(unittest.TestCase):
    def test_public_receipt_does_not_export_raw(self):
        self.assertEqual(caption.public_act({'index': 7, 'raw': 'private child words', 'sha256': 'digest'}),
            {'index': 7, 'sha256': 'digest'})

    def test_parent_is_english_and_bounded(self):
        self.assertEqual(caption.validate_message({'speak': True, 'message': 'Which word makes your actual caption ambiguous?'}),
            'Which word makes your actual caption ambiguous?')
        external_fixture = 'open ' + 'https:' + '/' * 2 + 'example.invalid'
        for message in ('中文', 'word '*91, external_fixture):
            with self.subTest(message=message), self.assertRaises(ValueError):
                caption.validate_message({'speak': True, 'message': message})

    def test_no_silent_parent_or_invented_success(self):
        with self.assertRaises(ValueError):
            caption.validate_message({'speak': False, 'message': ''})
        self.assertIn('never relabel', caption.INSTRUCTION)
        self.assertIn('Never invent depicted details', caption.INSTRUCTION)
        self.assertIn('no row exclusions', caption.INSTRUCTION)

    def test_unknown_operation_cannot_control_learner(self):
        with self.assertRaisesRegex(ValueError, 'parent_only_operation'):
            transport.main({'operation': 'restart'})

    def test_request_hash_excludes_resume_state_only(self):
        self.assertEqual(transport.request_digest({'prompt': 'fixture', 'resume_state': {'large': 1}}),
            transport.request_digest({'prompt': 'fixture'}))

    def test_exact_existing_caption_root_not_retired_alias(self):
        self.assertEqual(transport.PID, 2884345)
        self.assertEqual(transport.START, 95317660)
        self.assertIn('orch_r229_unparented_caption', str(transport.ROOT))
        self.assertNotIn('repo_c', str(transport.ROOT))


if __name__ == '__main__':
    unittest.main()
