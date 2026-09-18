from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r127_pilot_transcript as transcript
from gpu.orch_r125_stream_journal import SCHEMA, StreamJournal, _digest, _encoded
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION as PLAIN_CONTEXT_VERSION


class PilotTranscriptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.records = self.root / 'stream' / 'records'
        self.records.mkdir(parents=True)
        self.journal_id = 'a' * 32
        self.previous = _digest(dict(schema=SCHEMA, journal_id=self.journal_id))
        self.count = 0

    def record(self, kind, document):
        record = dict(schema=SCHEMA, journal_id=self.journal_id, index=self.count, kind=kind,
                      previous_sha256=self.previous, document=deepcopy(document))
        record['sha256'] = _digest(record)
        path = self.records / f'{self.count:020d}.json'
        path.write_bytes(_encoded(record) + b'\n')
        os.utime(path, (1000 + self.count, 1000 + self.count))
        self.previous = record['sha256']
        self.count += 1
        return record

    def inbox(self, text='Try a different approach.\n', speaker='Astra', identifier=None, legacy=False):
        identifier = identifier or f'{self.count:032x}'
        message = dict(id=identifier, text=text, split='TRAIN', actor='environment' if speaker == 'Tool' else 'parent')
        if not legacy:
            message.update(schema='R127_ATTRIBUTED_INBOX_V1', speaker=speaker,
                           source_receipt=dict(path='/never/read/receipt.json', sha256='b' * 64) if speaker == 'Tool' else None)
        source = dict(message=message, source_id=str(self.root / 'stream' / 'inbox' / (identifier + '.json')),
                      source_sha256=hashlib.sha256(_encoded(message)).hexdigest())
        self.record('INBOX', source)
        return source

    def request(self, visible=(), extra=(), startup='Birth.'):
        messages = [dict(role='system', content='System.'), dict(role='user', content=startup)]
        messages += [dict(role='user', content=text) for text in visible]
        messages += list(extra)
        request = dict(split='TRAIN', messages=messages, started_unix=2000 + self.count)
        self.record('REQUEST', dict(request, resume_state={'never_export': 'checkpoint secret'}))
        return _digest(request)

    def response(self, request, text='Exact child text.\n', **changes):
        document = dict(request_sha256=request, response=dict(raw=text), finished_unix=3000 + self.count)
        document.update(changes)
        return self.record('RESPONSE', document)

    def events(self, **limits):
        return list(transcript.iter_transcript(self.root, **limits))

    def test_exact_chronology_first_actual_parent_and_sleep_overlap(self):
        self.response(self.request(), 'Startup one.\n')
        source = self.inbox()
        visible = 'Astra: ' + source['message']['text']
        self.response(self.request(), 'Queued is not yet visible.')
        self.response(self.request([visible]), 'Parented answer.\n☃')
        self.response(self.request([visible]), 'Autonomous downstream.')
        self.record('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=1, resume_state={'secret': 'not text'}))
        self.response(self.request([visible]), '')
        tool = self.inbox('PROCESS_FAILED\nstderr: no result', speaker='Tool')
        self.response(self.request([visible, 'Tool: ' + tool['message']['text']]), 'Tool feedback response.')
        events = self.events()
        self.assertEqual([event['record_index'] for event in events], sorted(event['record_index'] for event in events))
        children = [event for event in events if event['kind'] == 'RESPONSE']
        self.assertEqual([event['category'] for event in children],
                         ['startup', 'startup', 'parented_response', 'autonomous_downstream',
                          'autonomous_downstream', 'autonomous_downstream'])
        self.assertEqual(children[2]['newly_visible_parent_ids'], [source['message']['id']])
        self.assertEqual(children[3]['newly_visible_parent_ids'], [])
        self.assertEqual(children[4]['text'], '')
        self.assertEqual(children[4]['categories'], ['autonomous_downstream', 'after_sleep'])
        self.assertEqual(children[5]['newly_visible_inbox_ids'], [tool['message']['id']])
        self.assertEqual(children[5]['newly_visible_parent_ids'], [])
        self.assertEqual(children[2]['text'], 'Parented answer.\n☃')
        boundary = next(event for event in events if event['kind'] == 'SLEEP_COMPLETE')
        self.assertNotIn('text', boundary)
        self.assertEqual((boundary['cycle'], boundary['sleep_count']), (1, 1))

    def test_legacy_prefix_text_preserved_and_unknown_parent_not_invented(self):
        for index, (text, speaker, attribution) in enumerate([
                ('Fable: First queued turn.\n', 'Fable', 'legacy_explicit_prefix'),
                ('Astra:\nTaking the lead.\n', 'Astra', 'legacy_explicit_prefix'),
                ('Rohin\nA note.', 'Rohin', 'legacy_explicit_prefix'),
                ('Please continue.', 'legacy parent', 'legacy_parent'),
                ('Fable suggested this.', 'legacy parent', 'legacy_parent')]):
            source = self.inbox(text, identifier=f'{index:032x}', legacy=True)
            entry = transcript._inbox(source)
            self.assertEqual((entry['speaker'], entry['attribution']), (speaker, attribution))
            self.response(self.request([text]))
        parents = [event for event in self.events() if event['kind'] == 'INBOX']
        self.assertEqual([event['text'] for event in parents],
                         ['Fable: First queued turn.\n', 'Astra:\nTaking the lead.\n',
                          'Rohin\nA note.', 'Please continue.', 'Fable suggested this.'])
        self.assertEqual([event['speaker'] for event in parents], ['Fable', 'Astra', 'Rohin', 'legacy parent', 'legacy parent'])
        self.assertTrue(all(event['actor'] == 'parent' and event['source_receipt'] is None for event in parents))
        self.assertEqual(parents[-1]['attribution'], 'legacy_parent')
        children = [event for event in self.events() if event['kind'] == 'RESPONSE']
        self.assertTrue(all(event['category'] == 'parented_response' for event in children))

    def test_substrings_assistant_echo_and_birth_are_not_parent_visibility(self):
        source = self.inbox('Unique message', legacy=True)
        text = source['message']['text']
        self.response(self.request(['quoted ' + text], extra=[dict(role='assistant', content=text)], startup=text))
        child = self.events()[-1]
        self.assertEqual(child['category'], 'startup')
        self.assertEqual(child['visible_inbox_ids'], [])

    def test_legacy_metadata_render_matches_only_bound_event(self):
        source = self.inbox('Fable: exact legacy text', legacy=True)
        metadata = dict(actor='parent', split='TRAIN', event_id='parent:inbox:' + source['message']['id'],
                        source_id=source['source_id'], source_sha256=source['source_sha256'])
        prefix = 'Parent advice (not an observed fact)\n'
        wrong = prefix + json.dumps(dict(metadata, source_sha256='0' * 64)) + '\n' + source['message']['text']
        self.response(self.request([wrong]))
        correct = prefix + json.dumps(metadata) + '\n' + source['message']['text']
        self.response(self.request([correct]))
        children = [event for event in self.events() if event['kind'] == 'RESPONSE']
        self.assertEqual([event['category'] for event in children], ['startup', 'parented_response'])

    def test_duplicate_plain_text_is_flagged_not_arbitrarily_attributed(self):
        first = self.inbox('Again.', legacy=True)
        second = self.inbox('Again.', legacy=True)
        self.response(self.request(['Again.']))
        child = self.events()[-1]
        self.assertEqual(child['category'], 'unresolved_parent_attribution')
        self.assertEqual(child['newly_visible_parent_ids'], [])
        self.assertEqual(set(child['ambiguous_inbox_ids']), {first['message']['id'], second['message']['id']})

    def test_hashes_exact_response_and_explicit_timestamp_sources(self):
        self.inbox('Fable: no changes', legacy=True)
        response = self.response(self.request(), '\n  exact\r\n')
        self.record('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=1))
        events = self.events()
        self.assertEqual(events[0]['unix_timestamp'], 1000)
        self.assertEqual(events[0]['timestamp_source'], 'record_mtime_not_event_time')
        self.assertEqual(events[1]['unix_timestamp'], response['document']['finished_unix'])
        self.assertEqual(events[1]['timestamp_source'], 'document.finished_unix')
        self.assertEqual(events[1]['record_sha256'], response['sha256'])
        for event in events:
            raw = (self.records / f"{event['record_index']:020d}.json").read_bytes()
            self.assertEqual(event['record_file_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(events[1]['text'], '\n  exact\r\n')

    def test_reads_only_published_records_never_journal_or_referenced_paths(self):
        self.inbox('Tool result status: PROCESS_FAILED', speaker='Tool')
        self.response(self.request())
        self.record('READOUT', dict(private='MUST NOT EXPORT'))
        (self.records / '00000000000000000004.intent.json').write_text('malformed ignored')
        (self.records / 'staging.partial').symlink_to('/never/read/staging')
        for name in ('JOURNAL.json', 'inbox', 'held', 'readouts'):
            (self.root / 'stream' / name).symlink_to('/never/read/' + name)
        original_open, opened = os.open, []

        def observed_open(path, flags, *args, **kwargs):
            if not flags & os.O_DIRECTORY:
                self.assertRegex(str(path), r'^[0-9]{20}\.json$')
                self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
                opened.append(str(path))
            return original_open(path, flags, *args, **kwargs)

        with patch.object(transcript.os, 'open', side_effect=observed_open), \
                patch.object(StreamJournal, '__init__', side_effect=AssertionError('no journal lock')):
            events = self.events()
        self.assertEqual(len(opened), self.count)
        self.assertNotIn('MUST NOT EXPORT', json.dumps(events))

    def test_corruption_gaps_and_unbound_response_rejected(self):
        self.response(self.request())
        path = self.records / '00000000000000000001.json'
        original = path.read_bytes()
        bad = json.loads(original)
        bad['document']['response']['raw'] = 'invented'
        path.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError, 'record_integrity'):
            self.events()
        bad['sha256'] = _digest({key: value for key, value in bad.items() if key != 'sha256'})
        bad['previous_sha256'] = '0' * 64
        bad['sha256'] = _digest({key: value for key, value in bad.items() if key != 'sha256'})
        path.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError, 'record_chain_integrity'):
            self.events()
        bad = json.loads(original)
        bad['document']['request_sha256'] = '0' * 64
        bad['sha256'] = _digest({key: value for key, value in bad.items() if key != 'sha256'})
        path.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError, 'response_request_binding'):
            self.events()
        path.rename(self.records / '00000000000000000002.json')
        with self.assertRaisesRegex(ValueError, 'noncontiguous_records'):
            self.events()

    def test_record_symlink_fifo_and_directory_rejected(self):
        path = self.records / '00000000000000000000.json'
        path.symlink_to('/never/read/file')
        with self.assertRaises(OSError):
            self.events()
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, 'regular_record_required'):
            self.events()
        path.unlink()
        path.mkdir()
        with self.assertRaises((ValueError, OSError)):
            self.events()

    def test_bounds_and_source_path_traversal(self):
        self.response(self.request())
        for limits in (dict(max_records=1), dict(max_record_bytes=1), dict(max_total_bytes=1), dict(max_records=True)):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                self.events(**limits)
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            list(transcript.iter_transcript(alias))
        with self.assertRaises(ValueError):
            list(transcript.iter_transcript(self.root / '..' / self.root.name))

    def test_create_only_export_manifest_pending_tail_and_cli(self):
        self.response(self.request(), 'Exact export text\n')
        self.request()
        output = self.root / 'transcript.jsonl'
        before = {path.name: path.read_bytes() for path in self.records.iterdir()}
        manifest = transcript.export_transcript(self.root, output)
        self.assertEqual(manifest['snapshot_records'], 3)
        self.assertEqual(manifest['pending_request_record_index'], 2)
        self.assertEqual(manifest['sha256'], hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(manifest['bytes'], output.stat().st_size)
        self.assertEqual(manifest['event_counts'], {'RESPONSE': 1})
        self.assertEqual(output.stat().st_mode & 0o777, 0o400)
        self.assertEqual(json.loads(output.read_text())['text'], 'Exact export text\n')
        with self.assertRaises(FileExistsError):
            transcript.export_transcript(self.root, output)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.records.iterdir()})
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(transcript.main(['--root', str(self.root)]), 0)
        self.assertEqual(json.loads(stdout.getvalue())['text'], 'Exact export text\n')
        with self.assertRaisesRegex(ValueError, 'output_outside_stream'):
            transcript.export_transcript(self.root, self.records / 'export.jsonl')

    def test_failed_export_never_publishes_final_path(self):
        self.response(self.request())
        self.record('RESPONSE', dict(request_sha256='0' * 64, response=dict(raw='unbound')))
        output = self.root / 'failed.jsonl'
        with self.assertRaisesRegex(ValueError, 'response_request_binding'):
            transcript.export_transcript(self.root, output)
        self.assertFalse(output.exists())
        self.assertEqual(len(list(self.root.glob('*.transcript.partial'))), 1)

    def test_real_journal_legacy_and_plain_requests_with_writer_still_open(self):
        for plain in (False, True):
            with self.subTest(plain=plain):
                root = self.root / ('plain' if plain else 'legacy')
                root.mkdir()
                stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
                    context_limit=4096, segment_tokens=16, segments_per_sleep=2,
                    deadline_unix=1000, model_state_sha256='f' * 64)
                if plain:
                    stream.set_presentation(dict(version=PLAIN_CONTEXT_VERSION,
                        system_prompt='System.', birth_prompt='Birth.'), 16384)

                def generate(messages, **kwargs):
                    return dict(raw='Native-shaped exact response.\n', token_ids=[10, 2], terminal=True, truncated=False)

                with StreamJournal(root / 'stream', create=True) as journal:
                    journal.record('COMMITTED', dict(state=stream.checkpoint()))
                    stream.step(generate, lambda messages: 10, journal.record, now=lambda: 100)
                    parent = dict(id='real-legacy-parent', actor='parent', split='TRAIN', text='Fable: Original turn.\n')
                    (journal.inbox / 'parent.json').write_text(json.dumps(parent))
                    incoming = journal.read_inbox()
                    stream.step(generate, lambda messages: 10, journal.record, incoming=incoming, now=lambda: 101)
                    stream.commit_sleep(dict(status='COMPLETE', cycle=1, optimizer_steps=1,
                        new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
                        checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64)), journal.record)
                    stream.step(generate, lambda messages: 10, journal.record, incoming=incoming, now=lambda: 102)
                    events = list(transcript.iter_transcript(root))
                children = [event for event in events if event['kind'] == 'RESPONSE']
                self.assertEqual([event['category'] for event in children],
                                 ['startup', 'parented_response', 'autonomous_downstream'])
                self.assertEqual(children[-1]['categories'], ['autonomous_downstream', 'after_sleep'])
                self.assertEqual(next(event['text'] for event in events if event['kind'] == 'INBOX'), parent['text'])

    def test_DEV_FINAL_and_unknown_inbox_never_exported(self):
        source = self.inbox()
        path = self.records / '00000000000000000000.json'
        original = json.loads(path.read_text())
        variants = [dict(source['message'], split=split) for split in ('DEV', 'FINAL')]
        variants.append(dict(source['message'], schema='UNKNOWN'))
        for message in variants:
            record = deepcopy(original)
            record['document']['message'] = message
            record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
            path.write_text(json.dumps(record))
            with self.subTest(message=message), self.assertRaises(ValueError):
                self.events()

    def test_export_rejects_output_symlink_and_ancestor_without_changing_target(self):
        self.response(self.request())
        target = self.root / 'existing.txt'
        target.write_text('preserved')
        alias = self.root / 'export.jsonl'
        alias.symlink_to(target)
        with self.assertRaises(FileExistsError):
            transcript.export_transcript(self.root, alias)
        directory_alias = self.root / 'directory-alias'
        directory_alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            transcript.export_transcript(self.root, directory_alias / 'new.jsonl')
        self.assertEqual(target.read_text(), 'preserved')
        self.assertFalse((self.root / 'new.jsonl').exists())

    def test_snapshot_does_not_follow_new_appends(self):
        self.response(self.request(), 'First.')
        iterator = transcript.iter_transcript(self.root)
        self.assertEqual(next(iterator)['text'], 'First.')
        self.response(self.request(), 'Later, outside first snapshot.')
        self.assertEqual(list(iterator), [])
        self.assertEqual(len(self.events()), 2)


if __name__ == '__main__':
    unittest.main()
