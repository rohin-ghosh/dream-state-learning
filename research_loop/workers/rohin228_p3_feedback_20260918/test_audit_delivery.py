import json
from pathlib import Path
import tempfile
import unittest

from audit_delivery import audit
from relay import digest, load, write_once


class DeliveryTests(unittest.TestCase):
    def test_only_actual_user_role_request_proves_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            life = root / 'life'
            output = root / 'relay'
            records = life / 'stream/records'
            records.mkdir(parents=True)
            (output / 'published').mkdir(parents=True)
            text = 'Caption-game judgment\nRank 25/65; accepted=true; novelty=new_pixel.'
            projection = root / 'projection.json'
            write_once(projection, dict(text=text))
            inbox = root / 'inbox.json'
            write_once(inbox, dict(id='inbox', actor='environment', speaker='Tool',
                text=text, source_receipt=load(projection)[1]))
            write_once(output / 'published/example.json', dict(publication=load(inbox)[1],
                published_unix=1, origin=dict(record_index=1), chunk=0, result=dict(sha256='source')))
            write_once(output / 'STARTED_1.json', dict(journal_start_after=0))
            unpublished = audit(life, output)
            self.assertEqual(unpublished['publication_count'], 1)
            self.assertEqual(unpublished['rendered_count'], 0)
            for index, role in [(1, 'assistant'), (2, 'user')]:
                record = dict(index=index, kind='REQUEST', document=dict(
                    started_unix=2, messages=[dict(role=role, content='Tool: ' + text)]))
                record['sha256'] = digest(record)
                write_once(records / f'{index:020d}.json', record)
                result = audit(life, output)
                self.assertEqual(result['rendered_count'], index - 1)
            self.assertEqual(result['rows'][0]['first_rendered_request']['index'], 2)
            self.assertEqual(result['ranked_caption_count'], 1)
            self.assertNotIn(text, json.dumps(result))


if __name__ == '__main__':
    unittest.main()
