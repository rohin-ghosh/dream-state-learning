import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r136_repo_reader as reader
from gpu.orch_r127_pilot_console import _bytes
from gpu import orch_r136_repo_reader_stage as staging
from gpu import orch_r136_repo_reader_broker as broker
from gpu.orch_r125_stream_journal import SCHEMA as JOURNAL_SCHEMA, StreamJournal, _digest


class RepoReaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.snapshot = self.base / 'snapshot'
        self.snapshot.mkdir()
        self.receipts = self.base / 'receipts'
        self.receipts.mkdir()
        self.document = reader.manifest('a' * 40)
        for name, content in reader.DOCUMENTS.items():
            (self.snapshot / name).write_text(content)
        raw = _bytes(self.document)
        (self.snapshot / 'MANIFEST.json').write_bytes(raw)
        self.expected = reader.digest(raw)

    def test_actual_file_receipt_and_provenance(self):
        request = dict(actor='child', split='TRAIN', record_index=4, record_sha256='b' * 64)
        result = reader.read_file(self.snapshot, self.expected, 'overview.md', self.receipts, request=request)
        receipt = json.loads(Path(result['result_path']).read_text())
        proof = json.loads(Path(result['provenance_path']).read_text())
        self.assertEqual(receipt['content'], (self.snapshot / 'overview.md').read_text())
        self.assertEqual(proof['receipt_sha256'], reader.digest(Path(result['result_path']).read_bytes()))
        self.assertEqual(proof['request'], request)
        self.assertEqual(proof['source_commit'], 'a' * 40)
        self.assertEqual(proof['sources'], reader.SOURCES)

    def test_real_pilot_environment_path(self):
        root = self.base / 'run'
        (root / 'stream' / 'inbox').mkdir(parents=True)
        result = reader.deliver(root, self.snapshot, self.expected, 'access.md', self.receipts,
                                dict(actor='operator', reason='initial_connection'))
        inbox = json.loads(Path(result['publication']['path']).read_text())
        self.assertEqual(inbox['actor'], 'environment')
        self.assertEqual(inbox['speaker'], 'Tool')
        self.assertEqual(inbox['split'], 'TRAIN')
        self.assertEqual(inbox['source_receipt']['path'], result['result_path'])
        self.assertIn(reader.DOCUMENTS['access.md'], inbox['text'])
        self.assertNotIn('[truncated]', inbox['text'])

    def test_reject_paths_and_unknown_files(self):
        for name in ('../outside.md', '/etc/passwd', 'sub/overview.md', 'hosts.env',
                     'MANIFEST.json', 'held.json', 'FINAL.md', 'overview.md\x00', '', None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                reader.read_file(self.snapshot, self.expected, name, self.receipts)
        self.assertEqual(list(self.receipts.iterdir()), [])

    def test_no_mutation(self):
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in self.snapshot.iterdir()}
        reader.read_file(self.snapshot, self.expected, 'continuity.md', self.receipts)
        self.assertEqual(before, {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                                 for path in self.snapshot.iterdir()})
        for operation in ('write-note', 'write', 'delete', 'execute', None):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                reader.read_file(self.snapshot, self.expected, 'overview.md', self.receipts, operation)

    def test_source_content_tamper(self):
        (self.snapshot / 'overview.md').write_text('unreviewed')
        with self.assertRaisesRegex(ValueError, 'snapshot_changed'):
            reader.read_file(self.snapshot, self.expected, 'overview.md', self.receipts)

    def test_manifest_tamper(self):
        (self.snapshot / 'MANIFEST.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest_changed'):
            reader.verify(self.snapshot, self.expected)

    def test_even_rehashed_unreviewed_manifest_rejected(self):
        self.document['sources'] = {'unreviewed': 'f' * 64}
        raw = _bytes(self.document)
        (self.snapshot / 'MANIFEST.json').write_bytes(raw)
        with self.assertRaises(ValueError):
            reader.verify(self.snapshot, reader.digest(raw))

    def test_extra_file_rejected(self):
        (self.snapshot / 'secret.md').write_text('not allowed')
        with self.assertRaisesRegex(ValueError, 'exact_allowlist'):
            reader.verify(self.snapshot, self.expected)

    def test_file_symlink_rejected_even_matching_content(self):
        outside = self.base / 'outside.md'
        outside.write_text(reader.DOCUMENTS['overview.md'])
        (self.snapshot / 'overview.md').unlink()
        (self.snapshot / 'overview.md').symlink_to(outside)
        with self.assertRaises(OSError):
            reader.read_file(self.snapshot, self.expected, 'overview.md', self.receipts)

    def test_symlink_directory_rejected(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.snapshot, target_is_directory=True)
        with self.assertRaises(OSError):
            reader.verify(alias, self.expected)
        parent_alias = self.base / 'parent-alias'
        parent_alias.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(OSError):
            reader.verify(parent_alias / 'snapshot', self.expected)

    def test_symlink_receipt_directory_rejected(self):
        alias = self.base / 'receipts-alias'
        alias.symlink_to(self.receipts, target_is_directory=True)
        with self.assertRaises(OSError):
            reader.read_file(self.snapshot, self.expected, 'access.md', alias)

    def test_fifo_rejected_without_blocking(self):
        (self.snapshot / 'overview.md').unlink()
        os.mkfifo(self.snapshot / 'overview.md')
        with self.assertRaises(ValueError):
            reader.verify(self.snapshot, self.expected)

    def test_second_read_hash_closes_validation_race(self):
        original = reader._read
        count = 0

        def changed(directory, name, limit):
            nonlocal count
            if name == 'overview.md':
                count += 1
                if count == 2:
                    return b'changed after verification'
            return original(directory, name, limit)

        with patch.object(reader, '_read', side_effect=changed), self.assertRaisesRegex(ValueError, 'read_source_hash'):
            reader.read_file(self.snapshot, self.expected, 'overview.md', self.receipts)

    def test_request_syntax_and_no_multiple_reads(self):
        self.assertEqual(reader.requests('Thinking\nrepo_read overview.md\nDone'), ['overview.md'])
        self.assertEqual(reader.requests('I might use repo_read overview.md'), [])
        for text in ('repo_read ../secret.md', 'repo_read /etc/passwd',
                     'repo_read overview.md\nrepo_read access.md'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                reader.requests(text)

    def test_source_build_fails_closed(self):
        with patch.object(reader.subprocess, 'run') as run:
            run.return_value.stdout = b'unreviewed source'
            with self.assertRaisesRegex(ValueError, 'reviewed_source_changed'):
                reader.build(self.base, 'a' * 40, self.base / 'new')
        self.assertFalse((self.base / 'new').exists())

    def test_short_explicit_coverage(self):
        for text in reader.DOCUMENTS.values():
            self.assertLessEqual(len(text.encode()), 2048)
            self.assertNotIn('/localhome', text)
        self.assertIn('not all', self.document['coverage'])
        self.assertEqual(set(self.document['files']), {'overview.md', 'continuity.md', 'access.md'})

    def test_startup_has_actual_paths_and_pending_not_fictitious_tools(self):
        base = '/localhome/local-rohing/orch_r136_repo_reader_test'
        text = staging.startup('Public\n### Resources and initial orientation\nOld tools', base, 1789596240)
        self.assertIn(base + '/snapshot1', text)
        self.assertIn('pending at startup', text)
        self.assertNotIn('Old tools', text)
        self.assertIn('1789596240', text)

    def test_new_template_strips_only_new_resume_authority(self):
        template = dict(seed=0, anchor_lambda=0.25, new_presentations=16, rehearsal_presentations=1,
                        segments_per_sleep=2, segment_tokens=512, context_limit=16384,
                        readout_revision=2, max_sleeps=None, presentation_version='R125_PLAIN_CONTEXT_V1',
                        authorized_wall_extension={'old': True}, preupdate_recovery={'old': True})
        fresh = staging.new_template(template)
        self.assertNotIn('authorized_wall_extension', fresh)
        self.assertNotIn('preupdate_recovery', fresh)
        self.assertIn('authorized_wall_extension', template)
        for key, value in (('seed', 1), ('anchor_lambda', 0), ('presleep_variant', 'no_distillation')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                staging.new_template(dict(template, **{key: value}))

    def run_broker_fixture(self, reuse=False):
        root = self.base / 'run'
        root.mkdir()
        with StreamJournal(root / 'stream', create=True):
            journal = json.loads((root / 'stream' / 'JOURNAL.json').read_text())
        records = root / 'stream' / 'records'
        previous = _digest(journal)
        for index, kind in enumerate(('REQUEST', 'RESPONSE')):
            record = dict(schema=JOURNAL_SCHEMA, journal_id=journal['journal_id'], index=index, kind=kind,
                          previous_sha256=previous, document={'response': {'raw': 'repo_read overview.md'}})
            record['sha256'] = _digest(record)
            previous = record['sha256']
            (records / f'{index:020d}.json').write_bytes(_bytes(record))
        config = dict(schema='R136_REPO_READER_BROKER_V1', hard_end_unix=1789596240,
                      root=str(root), snapshot=str(self.snapshot), manifest_sha256=self.expected,
                      output=str(self.base / 'broker'), receipts=str(self.base / 'broker-receipts'))
        if reuse:
            first = reader.deliver(root, self.snapshot, self.expected, 'access.md', self.receipts,
                                   dict(actor='operator', reason='initial_connection'))
            first['published_unix'] = 90
            old = self.base / 'broker1'
            old.mkdir()
            prior = old / 'FIRST_READ.json'
            prior.write_bytes(_bytes(first))
            config.update(connection_receipt_path=str(prior), connection_receipt_sha256=reader.digest(prior.read_bytes()))
        config_path = self.base / 'broker.json'
        config_path.write_text(json.dumps(config))
        clock = [100]

        def stop_when_caught_up(seconds):
            clock[0] = 1789596241

        with patch.object(broker, 'validate', side_effect=lambda value: value), \
                patch.object(broker.time, 'time', side_effect=lambda: clock[0]), \
                patch.object(broker.time, 'sleep', side_effect=stop_when_caught_up):
            broker.serve(config_path)
        results = list((self.base / 'broker').glob('READ_*.json'))
        self.assertEqual(len(results), 1)
        result = json.loads(results[0].read_text())
        self.assertEqual(result['request']['record_index'], 1)
        self.assertEqual(result['request']['record_sha256'], previous)
        self.assertEqual(result['request']['actor'], 'child')
        self.assertEqual(len(list((root / 'stream' / 'inbox').glob('*.json'))), 2)
        first = json.loads((self.base / 'broker' / ('CONNECTION_REUSED.json' if reuse else 'FIRST_READ.json')).read_text())
        proof = json.loads(Path(first['provenance_path']).read_text())
        self.assertEqual(proof['request']['actor'], 'operator')

    def test_broker_live_file_flow_uses_real_journal_genesis(self):
        self.run_broker_fixture()

    def test_broker_repair_reuses_receipt_without_repeating_read(self):
        self.run_broker_fixture(reuse=True)

    def test_broker_rejects_unowned_paths_and_extended_wall(self):
        prefix = '/localhome/local-rohing/orch_r136_repo_reader_test/'
        config = dict(schema='R136_REPO_READER_BROKER_V1', hard_end_unix=1789596240,
                      root=prefix+'run', snapshot=prefix+'snapshot', output=prefix+'broker',
                      receipts=prefix+'receipts', manifest_sha256=self.expected)
        with patch.object(broker.time, 'time', return_value=100), patch.object(broker, 'verify'):
            self.assertEqual(broker.validate(config), config)
            for changed in ({'root': '/localhome/local-rohing/orch_r127_pilot/run1'},
                            {'snapshot': prefix + '../other'}, {'hard_end_unix': 1789617240}):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    broker.validate(dict(config, **changed))


if __name__ == '__main__':
    unittest.main()
