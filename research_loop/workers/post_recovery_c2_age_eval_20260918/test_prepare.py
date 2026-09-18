import unittest

from prepare import ALLOWED, source_entry


class SourceSelectionTests(unittest.TestCase):
    def readiness(self):
        return dict(sources=[dict(label='C2_NOW', absolute_sleep=117,
            source_relative='sources/pinned', copy_files=dict.fromkeys(ALLOWED))])

    def test_fixed_selected_age(self):
        self.assertEqual(source_entry(self.readiness(), 'c2sleep117')['absolute_sleep'], 117)

    def test_latest_age_is_not_silently_substituted(self):
        document = self.readiness()
        document['sources'][0]['absolute_sleep'] = 118
        with self.assertRaisesRegex(ValueError, 'exact_predeclared'):
            source_entry(document, 'c2sleep117')

    def test_no_optimizer_or_context_files(self):
        document = self.readiness()
        document['sources'][0]['copy_files']['optimizer.pt'] = None
        with self.assertRaisesRegex(ValueError, 'adapter_only'):
            source_entry(document, 'c2sleep117')

    def test_source_does_not_escape_receiving_root(self):
        for relative in ('/tmp/source', 'sources/../../secret', 'elsewhere/source'):
            document = self.readiness()
            document['sources'][0]['source_relative'] = relative
            with self.assertRaisesRegex(ValueError, 'source_inside'):
                source_entry(document, 'c2sleep117')

    def test_ambiguous_source_is_rejected(self):
        document = self.readiness()
        document['sources'] *= 2
        with self.assertRaisesRegex(ValueError, 'exact_predeclared'):
            source_entry(document, 'c2sleep117')


if __name__ == '__main__':
    unittest.main()
