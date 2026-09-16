"""CPU-only publication and read-only follow tests with a live journal writer."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from gpu import orch_r125_stream_console as console
from gpu.orch_r125_stream_journal import INBOX_LIMIT, StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


class StreamConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.inbox = self.journal.inbox

    def command(self, *arguments):
        return [sys.executable, '-B', '-m', 'gpu.orch_r125_stream_console',
                '--root', str(self.root), *arguments]

    def run_cli(self, *arguments, input=''):
        return subprocess.run(self.command(*arguments), input=input, text=True, capture_output=True,
                              cwd=Path(__file__).resolve().parents[1], timeout=10)

    def test_publish_with_writer_held_exact_schema_hash_and_no_private_reads(self):
        with self.assertRaises(BlockingIOError):
            StreamJournal(self.root / 'stream')
        opened = []
        original_open = os.open

        def observed_open(path, flags, *args, **kwargs):
            opened.append((str(path), flags))
            return original_open(path, flags, *args, **kwargs)

        with patch.object(console.os, 'open', side_effect=observed_open), \
                patch('fcntl.flock', side_effect=AssertionError('must not acquire a lock')), \
                patch.object(StreamJournal, '__init__', side_effect=AssertionError('must not open journal')):
            receipt = console.publish(self.root, 'private TRAIN message ☃')
        self.assertEqual(set(receipt), {'id', 'sha256', 'path'})
        self.assertEqual(uuid.UUID(hex=receipt['id']).version, 4)
        path = Path(receipt['path'])
        raw = path.read_bytes()
        self.assertEqual(json.loads(raw), dict(id=receipt['id'], text='private TRAIN message ☃',
                                              split='TRAIN', actor='parent'))
        self.assertEqual(receipt['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(path.parent, self.inbox)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
        self.assertTrue(all(flags & os.O_DIRECTORY or flags & os.O_WRONLY for _, flags in opened))
        self.assertFalse(any(name in {'WRITER.lock', 'JOURNAL.json', 'records'} for name, _ in opened))
        events = self.journal.read_inbox()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_id, 'parent:inbox:' + receipt['id'])
        self.assertEqual(events[0].source_sha256, receipt['sha256'])
        self.assertEqual(events[0].source_id, receipt['path'])
        self.assertEqual(events[0].actor, 'parent')
        self.assertEqual(events[0].split, 'TRAIN')
        self.assertEqual(self.journal.read_inbox(), events)

    def test_stdin_distinct_ids_blank_lines_crlf_and_unterminated_line(self):
        result = self.run_cli(input='same\nsame\n\n padded \r\nlast')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        receipts = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len({receipt['id'] for receipt in receipts}), 5)
        self.assertEqual([json.loads(Path(receipt['path']).read_bytes())['text'] for receipt in receipts],
                         ['same', 'same', '', ' padded ', 'last'])
        self.assertTrue(all(uuid.UUID(hex=receipt['id']).version == 4 for receipt in receipts))
        self.assertEqual(len(self.journal.read_inbox()), 5)
        self.assertNotIn('padded', result.stdout)

    def test_text_is_one_message_and_does_not_read_stdin(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(console.sys, 'stdin') as stdin, redirect_stdout(stdout), redirect_stderr(stderr):
            stdin.readline.side_effect = AssertionError('text mode must not read stdin')
            result = console.main(['--root', str(self.root), '--text', 'secret\nsecond line'])
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)
        self.assertNotIn('secret', stdout.getvalue())
        self.assertEqual(self.journal.read_inbox()[0].text, 'secret\nsecond line')

    def test_line_published_and_child_reads_before_stdin_eof(self):
        process = subprocess.Popen(self.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True,
                                   cwd=Path(__file__).resolve().parents[1])
        try:
            self.assertEqual(self.journal.read_inbox(), [])
            process.stdin.write('live parent message\n')
            process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(timeout=5), 'receipt must not wait for stdin EOF')
            receipt = json.loads(process.stdout.readline())
            self.assertIsNone(process.poll())
            self.assertEqual(self.journal.read_inbox()[0].event_id, 'parent:inbox:' + receipt['id'])
            process.stdin.close()
            self.assertEqual(process.wait(timeout=5), 0)
            self.assertEqual(process.stderr.read(), '')
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_atomic_visibility_fsync_order_and_stable_published_inode(self):
        identifier = uuid.uuid4()
        original_link, original_fsync = os.link, os.fsync
        operations, observed_metadata = [], []

        def observed_fsync(descriptor):
            operations.append('directory' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file')
            return original_fsync(descriptor)

        def observed_link(source, destination, **kwargs):
            if destination != identifier.hex + '.json':
                return original_link(source, destination, **kwargs)
            self.assertFalse(source.endswith('.json'))
            self.assertFalse(list(self.inbox.glob('*.json')))
            self.assertEqual(self.journal.read_inbox(), [])
            self.assertEqual(operations, ['file', 'directory'])
            self.assertFalse(kwargs['follow_symlinks'])
            operations.append('link')
            original_link(source, destination, **kwargs)
            self.assertEqual(self.journal.read_inbox()[0].text, 'atomic message')
            observed_metadata.append((self.inbox / destination).stat())

        with patch.object(console.uuid, 'uuid4', return_value=identifier), \
                patch.object(console.os, 'fsync', side_effect=observed_fsync), \
                patch.object(console.os, 'link', side_effect=observed_link):
            receipt = console.publish(self.root, 'atomic message')
        self.assertEqual(operations[-1], 'directory')
        path = Path(receipt['path'])
        before, after = observed_metadata[0], path.stat()
        self.assertEqual((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
                         (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns))
        self.assertEqual(path.stat().st_ino, path.with_suffix('.partial').stat().st_ino)

    def test_exact_byte_limit_and_serialization_expansion_rejected(self):
        empty = console.publish(self.root, '')
        overhead = Path(empty['path']).stat().st_size
        receipt = console.publish(self.root, 'a' * (INBOX_LIMIT - overhead))
        self.assertEqual(Path(receipt['path']).stat().st_size, INBOX_LIMIT)
        self.assertEqual(len(self.journal.read_inbox()), 2)
        before = set(self.inbox.iterdir())
        for text in ('a' * (INBOX_LIMIT - overhead + 1), 'a' * (INBOX_LIMIT + 1),
                     '☃' * (INBOX_LIMIT // 3), '\x00' * (INBOX_LIMIT // 3)):
            with self.subTest(length=len(text)), self.assertRaisesRegex(ValueError, 'inbox_size'):
                console.publish(self.root, text)
        self.assertEqual(set(self.inbox.iterdir()), before)

    def test_stdin_read_is_bounded_and_oversize_is_not_split(self):
        class BoundedInput(io.StringIO):
            def readline(self, size=-1):
                if size != INBOX_LIMIT + 1:
                    raise AssertionError('unbounded input read')
                return super().readline(size)

        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(console.sys, 'stdin', BoundedInput('private' * INBOX_LIMIT + '\nnext\n')), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = console.main(['--root', str(self.root)])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), '')
        self.assertNotIn('private', stderr.getvalue())
        self.assertEqual(list(self.inbox.iterdir()), [])

    def test_symlink_root_ancestor_stream_and_inbox_rejected(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        for root in (alias, alias / '.'):
            with self.subTest(root=root), self.assertRaises(OSError):
                console.publish(root, 'rejected')
        nested = self.root / 'nested'
        nested.mkdir()
        with self.assertRaises(OSError):
            console.publish(alias / 'nested', 'rejected ancestor')
        for name in ('stream', 'inbox'):
            path = self.root / 'stream' if name == 'stream' else self.inbox
            moved = path.with_name(path.name + '-original')
            path.rename(moved)
            path.symlink_to(moved, target_is_directory=True)
            try:
                with self.subTest(name=name), self.assertRaises(OSError):
                    console.publish(self.root, 'rejected')
            finally:
                path.unlink()
                moved.rename(path)
        self.assertEqual(self.journal.read_inbox(), [])

    def test_staging_and_destination_collisions_never_overwrite_or_follow(self):
        target = self.root / 'untouched'
        target.write_bytes(b'private existing bytes')
        for suffix in ('.partial', '.json'):
            for symlink in (False, True):
                identifier = uuid.uuid4()
                path = self.inbox / (identifier.hex + suffix)
                if symlink:
                    path.symlink_to(target)
                else:
                    path.write_bytes(b'original')
                before = path.lstat()
                with self.subTest(suffix=suffix, symlink=symlink), \
                        patch.object(console.uuid, 'uuid4', return_value=identifier), \
                        self.assertRaises(FileExistsError):
                    console.publish(self.root, 'must not overwrite')
                self.assertEqual(path.lstat(), before)
                self.assertEqual(path.read_bytes(), target.read_bytes() if symlink else b'original')
        self.assertEqual(target.read_bytes(), b'private existing bytes')

    def test_failed_file_fsync_preserves_stage_without_visible_json(self):
        with patch.object(console.os, 'fsync', side_effect=OSError('synthetic failure')), \
                self.assertRaises(OSError):
            console.publish(self.root, 'not yet delivered')
        self.assertEqual(len(list(self.inbox.glob('*.partial'))), 1)
        self.assertEqual(list(self.inbox.glob('*.json')), [])
        self.assertEqual(self.journal.read_inbox(), [])

    def test_failed_final_fsync_emits_no_receipt_and_preserves_evidence(self):
        original_fsync = os.fsync

        def fail_after_link(descriptor):
            if list(self.inbox.glob('*.json')):
                raise OSError('private error detail')
            return original_fsync(descriptor)

        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(console.os, 'fsync', side_effect=fail_after_link), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = console.main(['--root', str(self.root), '--text', 'private message'])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), '')
        self.assertNotIn('private', stderr.getvalue())
        self.assertIn('uncertain', stderr.getvalue())
        self.assertEqual(len(list(self.inbox.glob('*.partial'))), 1)
        self.assertEqual(len(self.journal.read_inbox()), 1)

    def test_missing_inbox_is_not_created(self):
        self.journal.close()
        self.inbox.rmdir()
        with self.assertRaises(FileNotFoundError):
            console.publish(self.root, 'no auto creation')
        self.assertFalse(self.inbox.exists())


    def append_response(self, text):
        if not hasattr(self, 'stream'):
            self.stream = ContinualStream(
                TrainHistory(system_prompt='private system context', birth_prompt='private birth context'),
                context_limit=4096, segment_tokens=128, segments_per_sleep=10,
                deadline_unix=1000, model_state_sha256='f' * 64)
        self.stream.step(
            lambda messages, **kwargs: dict(raw=text, token_ids=[10, 2], terminal=True, truncated=False),
            lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
            self.journal.record, now=lambda: 100)

    def test_follow_finite_poll_is_read_only_with_live_writer_and_no_private_file_access(self):
        self.journal.record('NOTE', dict(response=dict(raw='private metadata, not a response')))
        console.publish(self.root, 'private parent input')
        self.journal.read_inbox()
        self.append_response('visible child response')
        for name in ('held', 'readout', 'context'):
            (self.root / name).write_text('private inaccessible content')
        before = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        original_open = os.open
        opened_files = []

        def readonly_open(path, flags, *args, **kwargs):
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if not flags & os.O_DIRECTORY:
                self.assertRegex(str(path), r'^\d{20}\.json$')
                opened_files.append(str(path))
            return original_open(path, flags, *args, **kwargs)

        with patch.object(console.os, 'open', side_effect=readonly_open), \
                patch('fcntl.flock', side_effect=AssertionError('no journal lock')), \
                patch.object(StreamJournal, '__init__', side_effect=AssertionError('no journal open')), \
                patch.object(console.time, 'sleep', side_effect=AssertionError('finite pass must finish')):
            responses = list(console.follow_responses(self.root, max_polls=1))
        self.assertEqual(responses, ['visible child response'])
        self.assertEqual(opened_files, [f'{index:020d}.json' for index in range(6)])
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}, before)
        self.journal.record('NOTE', dict(writer='still live'))

    def test_follow_polls_new_responses_in_order_without_replaying(self):
        self.append_response('first')

        def next_poll(interval):
            self.assertEqual(interval, 0.25)
            self.journal.record('NOTE', dict(raw='private note'))
            self.append_response('second')

        with patch.object(console.time, 'sleep', side_effect=next_poll) as sleep:
            responses = list(console.follow_responses(self.root, max_polls=2))
        self.assertEqual(responses, ['first', 'second'])
        sleep.assert_called_once_with(0.25)

    def test_follow_ignores_intents_and_partials_and_waits_at_record_gap(self):
        self.append_response('first')
        self.append_response('second')
        records = self.root / 'stream' / 'records'
        response = records / f'{1:020d}.json'
        partial = response.with_suffix('.json.partial')
        response.rename(partial)
        (records / f'{6:020d}.intent.json').write_text('{"private":')
        (records / f'{6:020d}.json.partial').write_text('{"private":')
        (records / 'readout.json').symlink_to(self.root / 'never-open-readout')
        self.assertEqual(list(console.follow_responses(self.root, max_polls=1)), [])

        def publish_next(interval):
            partial.rename(response)

        with patch.object(console.time, 'sleep', side_effect=publish_next):
            self.assertEqual(list(console.follow_responses(self.root, max_polls=2)), ['first', 'second'])

    def test_follow_tolerates_writer_staging_unlink_during_record_read(self):
        self.append_response('published response')
        response = self.root / 'stream' / 'records' / f'{1:020d}.json'
        partial = response.with_suffix('.json.partial')
        os.link(response, partial)
        identity = response.stat().st_ino
        original_fstat = os.fstat

        def unlink_after_stat(descriptor):
            entry = original_fstat(descriptor)
            if entry.st_ino == identity and partial.exists():
                partial.unlink()
            return entry

        with patch.object(console.os, 'fstat', side_effect=unlink_after_stat):
            self.assertEqual(list(console.follow_responses(self.root, max_polls=1)), ['published response'])
        self.assertFalse(partial.exists())

    def test_follow_rejects_partial_duplicate_and_invalid_record_bytes(self):
        self.append_response('do not leak damaged response')
        path = self.root / 'stream' / 'records' / f'{1:020d}.json'
        original = path.read_bytes()
        damaged = [b'{"private":', b'\xff', original.replace(b'{', b'{"schema":"duplicate",', 1)]
        changed = json.loads(original)
        changed['document']['response']['raw'] = 'tampered private content'
        damaged.append(json.dumps(changed).encode())
        for field, value in (('schema', 'WRONG'), ('index', 7), ('index', True),
                             ('journal_id', '0' * 32), ('previous_sha256', '0' * 64),
                             ('document', {'response': {'raw': ['not text']}})):
            changed = json.loads(original)
            changed[field] = value
            changed['sha256'] = console._digest({key: value for key, value in changed.items() if key != 'sha256'})
            damaged.append(json.dumps(changed).encode())
        for index, raw in enumerate(damaged):
            path.write_bytes(raw)
            with self.subTest(case=index), self.assertRaises(ValueError):
                list(console.follow_responses(self.root, max_polls=1))
        path.write_bytes(original)
        self.assertEqual(list(console.follow_responses(self.root, max_polls=1)), ['do not leak damaged response'])

    def test_follow_rejects_records_directory_and_record_symlinks(self):
        self.journal.record('NOTE', {})
        records = self.root / 'stream' / 'records'
        moved = records.with_name('records-original')
        records.rename(moved)
        records.symlink_to(moved, target_is_directory=True)
        try:
            with self.assertRaises(OSError):
                list(console.follow_responses(self.root, max_polls=1))
        finally:
            records.unlink()
            moved.rename(records)
        record = records / f'{0:020d}.json'
        record.unlink()
        forbidden = self.root / 'held'
        forbidden.write_text('private held content')
        record.symlink_to(forbidden)
        with self.assertRaises(OSError):
            list(console.follow_responses(self.root, max_polls=1))

    def test_follow_rejects_fifo_without_waiting(self):
        os.mkfifo(self.root / 'stream' / 'records' / f'{0:020d}.json')
        result = self.run_cli('--follow')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('follow failed (ValueError)', result.stderr)

    def test_follow_cli_prints_only_raw_and_exits_cleanly_on_interrupt(self):
        self.journal.record('NOTE', dict(raw='private note'))
        self.append_response('first line\nsecond line')
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(console.sys, 'stdin') as stdin, \
                patch.object(console, 'publish', side_effect=AssertionError('follow cannot publish')), \
                patch.object(console.time, 'sleep', side_effect=KeyboardInterrupt), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            stdin.readline.side_effect = AssertionError('follow cannot read stdin')
            result = console.main(['--root', str(self.root), '--follow'])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), 'first line\nsecond line\n')
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(list(self.inbox.iterdir()), [])

    def test_follow_cli_errors_do_not_disclose_record_content(self):
        record = self.root / 'stream' / 'records' / f'{0:020d}.json'
        record.write_text('{"private": "sensitive context"')
        result = self.run_cli('--follow')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('follow failed', result.stderr)
        self.assertNotIn('private', result.stderr)
        self.assertNotIn('sensitive', result.stderr)

    def test_follow_and_text_are_mutually_exclusive(self):
        result = self.run_cli('--follow', '--text', 'must not publish')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertEqual(list(self.inbox.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
