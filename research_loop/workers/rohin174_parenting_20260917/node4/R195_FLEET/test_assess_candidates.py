"""Observer-only code-fence classification regressions; no execution."""

import unittest

from assess_candidates import text_metrics


class MetricsTests(unittest.TestCase):
    def test_markdown_indentation_is_not_a_python_syntax_failure(self):
        result = text_metrics('   ``` python\n   result = 3\n   print(result)\n   ```\n')
        self.assertTrue(result['first_python_block']['closed'])
        self.assertIsNone(result['first_python_block']['syntax_error'])

    def test_unclosed_truncation_is_distinguished(self):
        result = text_metrics('```python\nresult = (\n')
        self.assertFalse(result['first_python_block']['closed'])
        self.assertIsNotNone(result['first_python_block']['syntax_error'])

    def test_fullwidth_assignment_in_closed_code_is_observable(self):
        result = text_metrics('```python\nresult ＝ 3\n```\n')
        self.assertEqual(result['first_python_block']['fullwidth_ascii_count'], 1)
        self.assertIsNotNone(result['first_python_block']['syntax_error'])

    def test_non_python_block_is_not_given_python_syntax_verdict(self):
        result = text_metrics('   ``` cpp\n   .__global__ void add(float*.output) {}\n   ```\n')
        self.assertEqual(result['first_fenced_block']['language'], 'cpp')
        self.assertIsNone(result['first_python_block'])


if __name__ == '__main__':
    unittest.main()
