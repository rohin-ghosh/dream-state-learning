"""Receipt-accounting tests; no remote transport, model or learner imports."""

import importlib.util
import json
from pathlib import Path
import unittest


OWN = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r213_audit_publish', OWN / 'publish.py')
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


class AuditTests(unittest.TestCase):
    def test_excluded_candidates_do_not_count_as_trained(self):
        rows = [dict(classification='SUBSTANTIVE_CONTENT', source_sha256='excluded',
                     trained=False, actual_presentations=0)]
        self.assertEqual(publish.summarize(rows)['SUBSTANTIVE_CONTENT'],
                         dict(trained_unique=0, actual_presentations=0))

    def test_unique_sources_and_repeated_presentations_are_distinct(self):
        rows = [dict(classification='MIXED', source_sha256='same', trained=True,
                     actual_presentations=count) for count in (16, 1)]
        result = publish.summarize(rows)
        self.assertEqual(result['MIXED'], dict(trained_unique=1, actual_presentations=17))
        self.assertEqual(result['META_INTENT_COMPLIANCE']['actual_presentations'], 0)

    def test_unreviewed_is_not_uncertain(self):
        with self.assertRaises(AssertionError):
            publish.summarize([dict(classification='UNREVIEWED', source_sha256='pending',
                                    trained=False, actual_presentations=0)])

    def test_all_completed_counts_reconcile(self):
        report = json.loads((OWN / 'EXTENDED_AUDIT.json').read_bytes())
        for summary in report['sleep_summary']:
            rows = [row for row in report['rows'] if row['sleep'] == summary['sleep']]
            self.assertEqual(sum(row['actual_presentations'] for row in rows), summary['all_actual_presentations'])
            self.assertTrue(all(row['actual_presentations'] == 0 for row in rows if row['excluded']))
            self.assertTrue(all(row['classification'] in publish.CATEGORIES for row in rows))

    def test_latest_partial_is_not_completed_aggregate(self):
        report = json.loads((OWN / 'LATEST_COUNTS.json').read_bytes())
        base = json.loads((OWN / 'FINAL_COUNTS.json').read_bytes())
        added = sum(row['actual_presentations'] for row in report['summaries'] if row['complete_index'])
        self.assertEqual(report['completed_actual_presentations'], base['all_actual_presentations'] + added)
        self.assertTrue(any(row['complete_index'] is None and row['actual_presentations'] > 0 for row in report['summaries']))


if __name__ == '__main__':
    unittest.main()
