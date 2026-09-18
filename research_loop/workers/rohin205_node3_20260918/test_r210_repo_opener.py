"""Keep actual source lines while avoiding reserved renderer metadata."""

import unittest

from r210_repo_opener import source_excerpt


class RepoOpenerTests(unittest.TestCase):
    def test_contiguous_exact_excerpt_omits_metadata_assignment(self):
        source = "\n".join((
            "def prose_exclusions(new_rows):",
            "    for row in new_rows:",
            "        evidence = scan_target(row['target'])",
            "        check = dict(source_sha256=row['source_sha256'])",
            "    return evidence",
        ))
        excerpt, first, last = source_excerpt(source)
        self.assertEqual((first, last), (1, 3))
        self.assertEqual(excerpt, '\n'.join(source.splitlines()[:3]))
        self.assertNotIn('source_sha256', excerpt)
        self.assertIn("row['target']", excerpt)


if __name__ == '__main__':
    unittest.main()
