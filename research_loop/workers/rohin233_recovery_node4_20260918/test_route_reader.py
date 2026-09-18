import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import route_reader


class RouteReaderTests(unittest.TestCase):
    def make_file(self, root, relative, document):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))

    def report(self, delivered):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_file(root, 'private/overseer/POLL_1.json', dict(snapshot=dict(delivered=delivered)))
            self.make_file(root, 'private/bridge/ASTRA7_TO_P7/published/reply.json', dict(
                publication=dict(id='reply'), published_unix=1))
            self.make_file(root, 'private/bridge/ASTRA7_TO_P7/pending/reply.json', dict(
                origin=dict(stage='ACT'), capsule=dict(reply_to=[dict(request_record_index=10)])))
            with patch.object(route_reader, 'OWN', root):
                return route_reader.current()

    def test_publication_alone_is_not_roundtrip(self):
        self.assertEqual(self.report({})['snapshot_linked_roundtrip_stage_count'], 0)

    def test_both_render_links_required_and_stage_count_explicit(self):
        report = self.report(dict(reply=dict(record_index=20)))
        self.assertEqual(report['snapshot_linked_roundtrip_stage_count'], 1)
        self.assertIn('not independent conversation', report['note'])


if __name__ == '__main__':
    unittest.main()
