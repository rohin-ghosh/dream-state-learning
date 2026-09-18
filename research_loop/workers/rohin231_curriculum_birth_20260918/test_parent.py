import unittest

from parent import actual_response, valid_message


class ParentTests(unittest.TestCase):
    def test_actual_native_RESPONSE_object_raw_not_operator_render(self):
        self.assertEqual(actual_response(dict(document=dict(response=dict(raw='17 + 8 = 25', token_ids=[1, 2])))),
                         '17 + 8 = 25')

    def test_bounded_English_allowed(self):
        self.assertTrue(valid_message('I am your parent. Show 17 + 8 - 6, then check your calculation.'))

    def test_non_English_and_double_label_rejected(self):
        self.assertFalse(valid_message('你写到'))
        self.assertFalse(valid_message('Astra: I am your parent.'))
        self.assertFalse(valid_message('word ' * 91))


if __name__ == '__main__':
    unittest.main()
