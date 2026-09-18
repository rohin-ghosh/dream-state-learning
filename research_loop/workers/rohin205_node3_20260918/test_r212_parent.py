"""No formula recycling, English-only guidance, normal-cycle conversation."""

import unittest

from r212_parent import ARMS, OBJECTS, prompt


class ParentTests(unittest.TestCase):
    def test_English_only_and_no_formula_reteaching(self):
        for name in ARMS:
            for turn in range(6):
                with self.subTest(name=name, turn=turn):
                    text = prompt(name, turn, repeated_algebra=True)
                    self.assertTrue(text.isascii())
                    self.assertNotIn('S_n', text)
                    self.assertNotIn('sympy', text)
                    self.assertIn('No code executor is connected', text)
                    self.assertIn('Choose your own', text)

    def test_two_turn_limit_changes_object(self):
        for name in ARMS:
            with self.subTest(name=name):
                self.assertIn(OBJECTS[name][0], prompt(name, 1))
                self.assertNotIn(OBJECTS[name][0], prompt(name, 2))
                self.assertIn(OBJECTS[name][1], prompt(name, 2))

    def test_conversation_priority_without_fake_human_input(self):
        text = prompt('conversational', 0)
        self.assertIn('takes priority over homework', text)
        self.assertIn('I am not supplying a Rohin message', text)
        self.assertIn('without waiting for sleep', text)
        self.assertIn('normal ACT to deliver the homework', text)

    def test_nonEnglish_excerpt_rejected_not_normalized(self):
        with self.assertRaisesRegex(ValueError, 'English_ASCII_only'):
            prompt('peer_repo', 0, excerpt='原样')


if __name__ == '__main__':
    unittest.main()
