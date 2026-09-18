import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from gpu import orch_r127_pilot_console as console


class PilotConsoleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.inbox = self.root / 'stream' / 'inbox'
        self.inbox.mkdir(parents=True)
        self.workspace = self.root / 'notes'

    def document(self, receipt):
        raw = Path(receipt['path']).read_bytes()
        self.assertEqual(receipt['sha256'], hashlib.sha256(raw).hexdigest())
        return json.loads(raw)

    def source(self, **fields):
        result = dict(schema='R125_CPU_EXPERIMENT_RESULT_V1', status='COMPLETE',
                      returncode=0, stdout='actual output', stderr='')
        result.update(fields)
        path = self.root / 'result.json'
        path.write_text(json.dumps(result))
        return path

    def test_parent_exact_schema_and_immutable_publication(self):
        for speaker in ('Astra', 'Fable', 'Rohin'):
            receipt = console.publish_parent(self.root, speaker, 'plain note')
            self.assertRegex(receipt['id'], r'^[0-9a-f]{32}$')
            self.assertEqual(self.document(receipt), dict(schema=console.SCHEMA, id=receipt['id'],
                text='plain note', split='TRAIN', actor='parent', speaker=speaker, source_receipt=None))
            path = Path(receipt['path'])
            self.assertEqual(path.stat().st_mode & 0o777, 0o400)
            self.assertEqual(path.stat().st_ino, path.with_suffix('.partial').stat().st_ino)
        with self.assertRaises(ValueError):
            console.publish_parent(self.root, 'Tool', 'no')

    def test_tool_attribution_and_exact_source_hash(self):
        path = self.source()
        result = self.document(console.publish_tool(self.root, path))
        self.assertEqual(result['actor'], 'environment')
        self.assertEqual(result['speaker'], 'Tool')
        self.assertEqual(result['split'], 'TRAIN')
        self.assertEqual(result['source_receipt'], dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        self.assertIn('stdout: actual output', result['text'])
        self.assertNotIn('source_receipt', result['text'])
        self.assertNotIn('R125_CPU_EXPERIMENT_RESULT_V1', result['text'])

    def test_failed_tool_never_labelled_success(self):
        path = self.source(status='PROCESS_FAILED', returncode=7, stdout='', stderr='actual failure')
        text = self.document(console.publish_tool(self.root, path))['text']
        self.assertIn('PROCESS_FAILED', text)
        self.assertIn('actual failure', text)
        self.assertNotIn('success', text.lower())
        self.assertNotIn('COMPLETE', text)

    def test_malformed_unknown_and_inconsistent_receipts_rejected(self):
        path = self.root / 'bad.json'
        for raw in (b'not json', b'[]', b'{}', b'{"schema":"unknown"}', b'\xff',
                    b'{"schema":"R125_CPU_EXPERIMENT_RESULT_V1","status":"COMPLETE"}',
                    b'{"schema":"x","schema":"y"}', b'{}' + b' ' * console.RECEIPT_LIMIT):
            path.write_bytes(raw)
            with self.subTest(raw=raw[:100]), self.assertRaises(ValueError):
                console.publish_tool(self.root, path)
        for fields in (dict(stdout=[]), dict(returncode=True), dict(returncode=1), dict(status='SUCCESS')):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                console.publish_tool(self.root, self.source(**fields))
        self.assertEqual(list(self.inbox.iterdir()), [])

    def test_receipt_symlinks_ancestors_fifo_and_directory_rejected(self):
        path = self.source()
        alias = self.root / 'alias.json'
        alias.symlink_to(path)
        ancestor = self.root / 'alias'
        ancestor.symlink_to(self.root, target_is_directory=True)
        fifo = self.root / 'pipe.json'
        os.mkfifo(fifo)
        for source in (alias, ancestor / path.name, fifo, self.workspace):
            with self.subTest(source=source), self.assertRaises((OSError, ValueError)):
                console.publish_tool(self.root, source)
        self.assertEqual(list(self.inbox.iterdir()), [])

    def test_notes_return_separate_immutable_receipts_without_publication(self):
        inbox = console.publish_parent(self.root, 'Astra', 'untouched')
        before = {path.name: (path.read_bytes(), path.stat()) for path in self.inbox.iterdir()}
        source = 'raise RuntimeError("never execute")\n'
        written = console.write_note(self.workspace, 'test.py', source)
        read = console.read_note(self.workspace, 'test.py')
        for receipt in (written, read):
            result = self.document(receipt)
            self.assertEqual(result['content'], source)
            self.assertEqual(result['schema'], console.WORKSPACE_SCHEMA)
            self.assertEqual(Path(receipt['path']).parent, self.root / 'notes.receipts')
            self.assertEqual(Path(receipt['path']).stat().st_mode & 0o777, 0o400)
        self.assertNotEqual(written['path'], read['path'])
        self.assertEqual(before, {path.name: (path.read_bytes(), path.stat()) for path in self.inbox.iterdir()})
        self.document(inbox)
        text = self.document(console.publish_tool(self.root, read['path']))['text']
        self.assertIn(source.strip(), text)

    def test_no_overwrite_or_invalid_names(self):
        receipt = console.write_note(self.workspace, 'note.md', 'original')
        before = (self.workspace / 'note.md').stat()
        with self.assertRaises(FileExistsError):
            console.write_note(self.workspace, 'note.md', 'replacement')
        self.assertEqual((self.workspace / 'note.md').stat(), before)
        self.assertEqual(self.document(receipt)['content'], 'original')
        for name in ('../x.md', '/x.md', 'sub/x.md', '.hidden.md', 'x.json', 'x\\y.py', 'x.md/../y.md'):
            for function in (lambda: console.write_note(self.workspace, name, ''),
                             lambda: console.read_note(self.workspace, name)):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    function()

    def test_note_and_workspace_symlinks_rejected(self):
        console.write_note(self.workspace, 'real.txt', 'safe')
        (self.workspace / 'alias.txt').symlink_to(self.workspace / 'real.txt')
        for function in (lambda: console.write_note(self.workspace, 'alias.txt', 'bad'),
                         lambda: console.read_note(self.workspace, 'alias.txt')):
            with self.assertRaises((OSError, ValueError)):
                function()
        alias = self.root / 'alias'
        alias.symlink_to(self.workspace, target_is_directory=True)
        with self.assertRaises(OSError):
            console.write_note(alias, 'new.md', '')
        other = self.root / 'other'
        (self.root / 'other.receipts').symlink_to(self.root / 'notes.receipts', target_is_directory=True)
        with self.assertRaises(OSError):
            console.write_note(other, 'new.md', '')

    def test_note_byte_and_capacity_boundaries(self):
        for text in ('a' * (console.NOTE_LIMIT + 1), '☃' * (console.NOTE_LIMIT // 3 + 1)):
            with self.assertRaises(ValueError):
                console.write_note(self.workspace, 'too-big.txt', text)
        for index in range(console.FILE_LIMIT):
            console.write_note(self.workspace, f'note{index}.txt', 'a' * console.NOTE_LIMIT)
        self.assertEqual(sum(path.stat().st_size for path in self.workspace.iterdir()), console.TOTAL_LIMIT)
        with self.assertRaises(ValueError):
            console.write_note(self.workspace, 'overflow.txt', '')
        self.assertEqual(len(self.document(console.read_note(self.workspace, 'note0.txt'))['content']), console.NOTE_LIMIT)

    def test_inbox_collision_does_not_change_existing_message(self):
        receipt = console.publish_parent(self.root, 'Rohin', 'original')
        before = Path(receipt['path']).stat()
        with patch.object(console.uuid, 'uuid4') as identifier:
            identifier.return_value.hex = receipt['id']
            with self.assertRaises(FileExistsError):
                console.publish_parent(self.root, 'Fable', 'replacement')
        self.assertEqual(Path(receipt['path']).stat(), before)
        self.assertEqual(self.document(receipt)['text'], 'original')

    def test_concurrent_writers_cannot_exceed_quota(self):
        self.workspace.mkdir(mode=0o755)
        def attempt(index):
            try:
                console.write_note(self.workspace, f'note{index}.txt', 'data')
                return True
            except ValueError:
                return False
        with patch.object(console, 'FILE_LIMIT', 1), ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(attempt, range(4))), 1)
        self.assertEqual(len(list(self.workspace.iterdir())), 1)

    def test_total_limit_and_insecure_receipt_directory(self):
        console.write_note(self.workspace, 'one.md', '1234')
        with patch.object(console, 'TOTAL_LIMIT', 5), self.assertRaises(ValueError):
            console.write_note(self.workspace, 'two.md', '12')
        (self.root / 'notes.receipts').chmod(0o755)
        with self.assertRaises(ValueError):
            console.read_note(self.workspace, 'one.md')

    def test_bounded_tool_summary_and_workspace_tampering(self):
        path = self.source(stdout='x' * (console.SUMMARY_LIMIT + 1))
        text = self.document(console.publish_tool(self.root, path))['text']
        self.assertIn('[truncated]', text)
        self.assertNotIn('x' * (console.SUMMARY_LIMIT + 1), text)
        receipt = console.write_note(self.workspace, 'one.txt', 'real content')
        result = self.document(receipt)
        result['content'] = 'tampered'
        path.write_text(json.dumps(result))
        before = set(self.inbox.iterdir())
        with self.assertRaises(ValueError):
            console.publish_tool(self.root, path)
        self.assertEqual(before, set(self.inbox.iterdir()))

    def test_cli_modes(self):
        commands = [
            ['parent', '--root', str(self.root), '--speaker', 'Astra', '--text', 'hello'],
            ['tool', '--root', str(self.root), '--result-path', str(self.source())],
            ['write-note', '--workspace', str(self.workspace), '--name', 'cli.md', '--text', 'note'],
            ['read-note', '--workspace', str(self.workspace), '--name', 'cli.md']]
        for command in commands:
            with self.subTest(command=command), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(console.main(command), 0)
                self.document(json.loads(output.getvalue()))


if __name__ == '__main__':
    unittest.main()
