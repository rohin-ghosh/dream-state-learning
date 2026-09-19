import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from reader import checkpoint, digest, read_stable, rendered, verified
from publish import safe_public


class ReaderTests(unittest.TestCase):
    def test_plain_and_structured_actual_context(self):
        event = dict(actor='parent', event_id='parent:inbox:a', source_id='source', source_sha256='a', split='TRAIN', text='Astra: Correct this.')
        self.assertTrue(rendered(event, [dict(role='user', content=event['text'])]))
        metadata = {key: value for key, value in event.items() if key != 'text'}
        text = 'Parent advice (not an observed fact)\n' + json.dumps(metadata) + '\n' + event['text']
        self.assertTrue(rendered(event, [dict(role='user', content=text)]))
        self.assertFalse(rendered(event, [dict(role='assistant', content=text)]))
        self.assertFalse(rendered(event, [dict(role='user', content=text.replace('"source"', '"wrong"'))]))
        self.assertFalse(rendered(event, [dict(role='user', content='Quoted: ' + event['text'])]))

    def test_symlink_not_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'file').write_text('data')
            (root/'link').symlink_to(root/'file')
            with self.assertRaises(OSError):
                read_stable(root/'link')

    def test_completed_checkpoint_manifest_not_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = root/'stream/records'
            records.mkdir(parents=True)
            directory = root/'checkpoints/sleep_000001'
            (directory/'adapter').mkdir(parents=True)
            (directory/'adapter/adapter.bin').write_bytes(b'adapter')
            (directory/'optimizer_rng.pt').write_bytes(b'optimizer')
            adapter = hashlib.sha256(b'adapter').hexdigest()
            optimizer = hashlib.sha256(b'optimizer').hexdigest()
            checksums = dict(optimizer=optimizer, rng=optimizer)
            commit = dict(checkpoint_sha256=checksums, optimizer_steps=8, adapter_files={'adapter.bin': adapter}, adapter_state_sha256='tensor-state')
            (directory/'COMMIT.json').write_text(json.dumps(commit))
            document = dict(status='COMPLETE', cycle=1, checkpoint_sha256=checksums, total_optimizer_steps=8,
                resume_state=dict(state={'state': 'complete'}, sha256=digest({'state': 'complete'})))
            record = dict(kind='SLEEP_COMPLETE', index=1, journal_id='test', document=document, previous_sha256='0')
            record['sha256'] = digest(record)
            (records/'00000000000000000001.json').write_text(json.dumps(record))
            manifest = checkpoint(root, 'test', 1)
            self.assertEqual(manifest['copied_bytes'], 0)
            self.assertEqual(manifest['adapter_files']['adapter/adapter.bin'], adapter)
            (directory/'adapter/adapter.bin').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'adapter_hash'):
                checkpoint(root, 'test', 1)

    def test_publication_refuses_raw_and_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'report.json'
            path.write_text(json.dumps(dict(raw='private words')))
            with self.assertRaisesRegex(ValueError, 'raw_content'):
                safe_public(path)
            path.write_text(json.dumps(dict(location='/localhome/person/file')))
            with self.assertRaisesRegex(ValueError, 'privacy_scan'):
                safe_public(path)
            path.write_text(json.dumps(dict(index=5, sha256='a')))
            self.assertTrue(safe_public(path))


if __name__ == '__main__':
    unittest.main()
