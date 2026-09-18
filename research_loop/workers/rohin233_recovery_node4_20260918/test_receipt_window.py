import json
from pathlib import Path
import tempfile
import unittest

from receipt_window import digest, linked_reply, read_record


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def record(self, index, kind, document):
        row = dict(index=index, kind=kind, document=document, journal_id='journal', previous_sha256='previous')
        row['sha256'] = digest(row)
        (self.directory / f'{index:020d}.json').write_text(json.dumps(row, sort_keys=True, separators=(',', ':')))
        return row

    def sequence(self, commit=True):
        request = self.record(10, 'REQUEST', dict(messages=[dict(content='真实文字')], resume_state={'irrelevant':True}))
        response = self.record(11, 'RESPONSE', dict(request_sha256=digest({'messages':request['document']['messages']}),
            response=dict(raw='自己的回答')))
        if commit:
            self.record(12, 'COMMITTED', dict(source_sha256=digest(response['document'])))
        return request

    def test_unicode_uses_actual_ascii_escaped_canonical_digest(self):
        request = self.sequence()
        reply, earlier = linked_reply(self.directory, 10, request['sha256'], 'journal')
        self.assertEqual(reply['text'], '自己的回答')
        self.assertEqual(reply['commit_record_index'], 12)
        self.assertEqual(earlier, [])

    def test_uncommitted_output_is_not_a_reply(self):
        request = self.sequence(commit=False)
        self.assertIsNone(linked_reply(self.directory, 10, request['sha256'], 'journal')[0])

    def test_other_request_and_forged_commit_are_not_proof(self):
        request = self.record(10, 'REQUEST', dict(messages=[]))
        self.record(11, 'RESPONSE', dict(request_sha256='other', response=dict(raw='not the answer')))
        self.record(12, 'COMMITTED', dict(source_sha256='not the response'))
        self.assertIsNone(linked_reply(self.directory, 10, request['sha256'], 'journal')[0])

    def test_mutated_body_rejected(self):
        request = self.sequence()
        path = self.directory / '00000000000000000010.json'
        request['document']['messages'] = []
        path.write_text(json.dumps(request))
        with self.assertRaises(ValueError):
            read_record(path, 'journal')

    def test_wrong_life_and_request_pin_rejected(self):
        request = self.sequence()
        for journal, bound_hash in [('other',request['sha256']), ('journal','wrong')]:
            with self.assertRaises(ValueError):
                linked_reply(self.directory, 10, bound_hash, journal)


if __name__ == '__main__':
    unittest.main()
