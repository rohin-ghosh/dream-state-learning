"""Local synthetic persistence tests; no native engine, providers or launches."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, PRESLEEP_INVITATIONS, digest, experiment_binding
from organism_v6.orch_r125_plain_context import VERSION as PLAIN_CONTEXT_VERSION


def tokens(messages):
    return sum(len(message['content'].split()) + 4 for message in messages)


def generate(messages, **kwargs):
    return dict(raw='Synthetic child output.', token_ids=[10, 2], terminal=True, truncated=False)


class StreamJournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'journal'
        self.journal = StreamJournal(self.root, create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)

    def step(self, record=None, generate_call=generate, incoming=()):
        return self.stream.step(generate_call, tokens, self.journal.record if record is None else record,
                                incoming=incoming, now=lambda: 100)

    def bind_experiment(self):
        self.stream.experiment = experiment_binding(dict(seed=1, presleep_variant='no_distillation',
            compaction_invitation='', system_prompt='System.', birth_prompt='Birth.'))

    def test_bound_experiment_roundtrips_and_legacy_checkpoint_remains_byte_equivalent(self):
        legacy = self.stream.checkpoint()
        self.assertNotIn('experiment', legacy['state'])
        restored = ContinualStream.restore(legacy, expected_sha256=legacy['sha256'])
        self.assertIsNone(restored.experiment)
        self.assertEqual(restored.checkpoint(), legacy)
        self.bind_experiment()
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.step()
        saved = self.journal.latest_checkpoint()
        restored = ContinualStream.restore(**saved)
        self.assertEqual(restored.experiment, self.stream.experiment)
        self.assertEqual(restored.checkpoint(), self.stream.checkpoint())

    def test_journal_rejects_seed_change_before_generation(self):
        self.bind_experiment()
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        before = self.journal.latest_checkpoint()
        self.stream.experiment['seed'] = 0
        with patch(__name__+'.generate') as generation, \
                self.assertRaisesRegex(ValueError, 'journal_experiment_configuration_frozen'):
            self.step(generate_call=generation)
        generation.assert_not_called()
        self.journal.close()
        with StreamJournal(self.root) as journal:
            self.assertEqual(journal.latest_checkpoint(), before)

    def test_presentation_transition_cannot_change_variant_or_its_prompt(self):
        self.bind_experiment()
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.stream.set_presentation(dict(version=PLAIN_CONTEXT_VERSION, system_prompt='System.', birth_prompt='Birth.'), 16384)
        self.stream.experiment.update(presleep_variant='reread_select',
            compaction_invitation=PRESLEEP_INVITATIONS['reread_select'])
        with self.assertRaisesRegex(ValueError, 'journal_experiment_configuration_frozen'):
            self.journal.record('PRESENTATION', dict(state=self.stream.checkpoint()))

    def test_bound_experiment_cannot_be_removed_from_saved_state(self):
        self.bind_experiment()
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.stream.experiment = None
        with self.assertRaisesRegex(ValueError, 'journal_experiment_configuration_frozen'):
            self.step()

    def test_sleep_receipt_must_bind_same_experiment_as_stream(self):
        self.bind_experiment()
        self.step()
        self.step()
        receipt = self.receipt()
        receipt['checkpoint'] = dict(experiment=dict(self.stream.experiment, seed=0))
        with self.assertRaisesRegex(ValueError, 'sleep_model_experiment_binding'):
            self.stream.commit_sleep(receipt, self.journal.record)

    def test_legacy_checkpoint_cannot_be_relabelled_as_seeded_experiment(self):
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.bind_experiment()
        with self.assertRaisesRegex(ValueError, 'journal_experiment_configuration_frozen'):
            self.step()

    def receipt(self):
        return dict(status='COMPLETE', optimizer_steps=2,
                    new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
                    checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))

    def record_path(self, index):
        return self.root / 'records' / f'{index:020d}.json'

    def parent(self, name='parent.json', identifier='operator-1', text='Consider this observation.', **changes):
        document = dict(id=identifier, text=text, split='TRAIN', actor='parent', **changes)
        path = self.journal.inbox / name
        path.write_text(json.dumps(document))
        return path

    def test_explicit_creation_no_existing_root_overwrite(self):
        missing = self.root.parent / 'missing'
        with self.assertRaises(FileNotFoundError):
            StreamJournal(missing)
        before = (self.root / 'JOURNAL.json').read_bytes()
        with self.assertRaises(FileExistsError):
            StreamJournal(self.root, create=True)
        self.assertEqual((self.root / 'JOURNAL.json').read_bytes(), before)
        self.assertEqual(self.journal.inbox, self.root / 'inbox')
        self.assertIsNone(self.journal.latest_checkpoint())

    def test_lifetime_lock_close_context_manager_and_noninheritable_fds(self):
        with self.assertRaises(BlockingIOError):
            StreamJournal(self.root)
        self.assertTrue(all(not os.get_inheritable(descriptor) for descriptor in self.journal._fds))
        self.journal.close()
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            reopened.record('NOTE', {'text': 'Synthetic metadata'})
        with self.assertRaisesRegex(ValueError, 'closed_or_inherited'):
            reopened.latest_checkpoint()

    @unittest.skipUnless(hasattr(os, 'fork'), 'POSIX lifetime lock test')
    def test_fork_child_does_not_keep_parent_lock_alive(self):
        ready_read, ready_write = os.pipe()
        release_read, release_write = os.pipe()
        child = os.fork()
        if child == 0:
            try:
                os.close(ready_read)
                os.close(release_write)
                closed = self.journal._closed and not self.journal._fds
                os.write(ready_write, b'1' if closed else b'0')
                os.read(release_read, 1)
                os._exit(0)
            except BaseException:
                os._exit(1)
        os.close(ready_write)
        os.close(release_read)
        try:
            self.assertEqual(os.read(ready_read, 1), b'1')
            with self.assertRaises(BlockingIOError):
                StreamJournal(self.root)
            self.journal.close()
            with StreamJournal(self.root) as reopened:
                self.assertIsNone(reopened.latest_checkpoint())
        finally:
            os.write(release_write, b'1')
            os.close(release_write)
            os.close(ready_read)
            unused_pid, status = os.waitpid(child, 0)
        self.assertEqual(status, 0)

    def test_real_scheduler_callbacks_commit_and_sleep_restore(self):
        self.step()
        first = self.journal.latest_checkpoint()
        self.assertEqual(first['document'], self.stream.checkpoint())
        restored = ContinualStream.restore(**first)
        self.assertIsNone(restored.pending)
        self.step()
        self.stream.commit_sleep(self.receipt(), self.journal.record)
        latest = self.journal.latest_checkpoint()
        self.assertEqual(latest['document'], self.stream.checkpoint())
        self.assertEqual(ContinualStream.restore(**latest).sleep_frontier, 2)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.latest_checkpoint(), latest)

    def test_record_indices_chain_and_immutable_detached_documents(self):
        document = {'text': 'first'}
        receipt = self.journal.record('NOTE', document)
        document['text'] = 'changed'
        self.journal.record('NOTE', {'text': 'second'})
        first = json.loads(self.record_path(0).read_text())
        second = json.loads(self.record_path(1).read_text())
        self.assertEqual([first['index'], second['index']], [0, 1])
        self.assertEqual(second['previous_sha256'], first['sha256'])
        self.assertEqual(first['document']['text'], 'first')
        self.assertEqual(receipt['sha256'], first['sha256'])
        self.assertEqual(len(list((self.root / 'records').iterdir())), 4)

    def test_request_tail_not_stale_previous_commit(self):
        self.step()
        prior = self.journal.latest_checkpoint()
        def failure(*args, **kwargs):
            raise RuntimeError('synthetic generation failure')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=failure)
        latest = self.journal.latest_checkpoint()
        self.assertNotEqual(latest, prior)
        self.assertIsNotNone(latest['document']['state']['pending'])
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            restored = ContinualStream.restore(**reopened.latest_checkpoint())
            with self.assertRaisesRegex(ValueError, 'unresolved_request_never_redispatched'):
                restored.step(generate, tokens, reopened.record, now=lambda: 100)

    def test_response_alone_and_metadata_do_not_clear_pending_checkpoint(self):
        def invalid(*args, **kwargs):
            return dict(raw='Malformed output is evidence.', token_ids=[], terminal=True, truncated=False)
        with self.assertRaisesRegex(ValueError, 'actual_bounded_child_tokens'):
            self.step(generate_call=invalid)
        latest = self.journal.latest_checkpoint()
        self.assertIsNotNone(latest['document']['state']['pending'])
        self.assertIn('Malformed output', self.record_path(1).read_text())
        self.journal.record('NOTE', {'state': self.stream.checkpoint(), 'message': 'not authoritative'})
        self.assertEqual(self.journal.latest_checkpoint(), latest)

    def test_stale_commit_cannot_bypass_pending_request(self):
        self.step()
        stale = json.loads(self.record_path(2).read_text())['document']
        def failure(*args, **kwargs):
            raise RuntimeError('stop')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=failure)
        with self.assertRaisesRegex(ValueError, 'commit_requires_request_and_response'):
            self.journal.record('COMMITTED', stale)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertIsNotNone(reopened.latest_checkpoint()['document']['state']['pending'])

    def test_second_request_and_wrong_response_fail_closed(self):
        def failure(*args, **kwargs):
            raise RuntimeError('stop')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=failure)
        request = json.loads(self.record_path(0).read_text())['document']
        with self.assertRaisesRegex(ValueError, 'unresolved_request_never_bypassed'):
            self.journal.record('REQUEST', request)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            with self.assertRaisesRegex(ValueError, 'response_request_binding'):
                reopened.record('RESPONSE', {'request_sha256': '0' * 64})

    def test_publication_fsyncs_files_and_directories(self):
        seen = []
        original = os.fsync
        def observed(descriptor):
            seen.append('directory' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file')
            return original(descriptor)
        with patch('gpu.orch_r125_stream_journal.os.fsync', side_effect=observed):
            self.journal.record('NOTE', {'evidence': 'durable'})
        self.assertEqual(seen.count('file'), 2)
        self.assertGreaterEqual(seen.count('directory'), 6)

    def test_partial_publication_poisoned_no_retry_or_stale_fallback(self):
        self.step()
        original = StreamJournal._publish
        def fail(directory, name, document):
            if name == '00000000000000000003.json':
                raise OSError('synthetic disk failure after intent')
            return original(directory, name, document)
        with patch.object(StreamJournal, '_publish', side_effect=fail):
            with self.assertRaises(OSError):
                self.journal.record('NOTE', {'incomplete': True})
        with self.assertRaisesRegex(ValueError, 'failed_no_retry'):
            self.journal.latest_checkpoint()
        self.journal.close()
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_tail'):
            StreamJournal(self.root)

    def test_atomic_link_failure_preserves_partial_and_never_overwrites(self):
        with patch('gpu.orch_r125_stream_journal.os.link', side_effect=FileExistsError('exclusive collision')):
            with self.assertRaises(FileExistsError):
                self.journal.record('NOTE', {'first': True})
        self.assertTrue(list((self.root / 'records').glob('*.partial')))
        with self.assertRaisesRegex(ValueError, 'failed_no_retry'):
            self.journal.record('NOTE', {'retry': True})
        self.journal.close()
        with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected_journal_tail'):
            StreamJournal(self.root)

    def test_corrupt_or_missing_tail_refuses_prior_valid_checkpoint(self):
        self.step()
        self.journal.record('NOTE', {'tail': True})
        path = self.record_path(3)
        original = path.read_bytes()
        path.write_bytes(b'{')
        with self.assertRaises(ValueError):
            self.journal.latest_checkpoint()
        path.write_bytes(original)
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_tail'):
            self.journal.latest_checkpoint()

    def test_chain_and_intent_tampering_rejected(self):
        self.journal.record('NOTE', {'first': True})
        path = self.record_path(0)
        original = path.read_text()
        changed = json.loads(original)
        changed['document']['first'] = False
        path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'journal_chain_integrity'):
            self.journal.latest_checkpoint()
        path.write_text(original)
        intent = path.with_name('00000000000000000000.intent.json')
        intent.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'journal_intent_binding'):
            self.journal.latest_checkpoint()

    def test_record_symlink_and_gap_rejected(self):
        self.journal.record('NOTE', {'first': True})
        path = self.record_path(0)
        moved = self.root / 'original.json'
        path.rename(moved)
        path.symlink_to(moved)
        with self.assertRaises(OSError):
            self.journal.latest_checkpoint()
        path.unlink()
        moved.rename(path)
        path.rename(self.record_path(2))
        with self.assertRaisesRegex(ValueError, 'noncontiguous_journal'):
            self.journal.latest_checkpoint()

    def test_empty_inbox_nonblocking_partial_ignored(self):
        (self.journal.inbox / 'unfinished.partial').write_text('{')
        self.assertEqual(self.journal.read_inbox(), [])
        self.assertEqual(list((self.root / 'records').iterdir()), [])

    def test_inbox_typed_provenance_and_history_once_only(self):
        path = self.parent()
        incoming = self.journal.read_inbox()
        self.assertEqual(len(incoming), 1)
        parent = incoming[0]
        self.assertEqual(parent.actor, 'parent')
        self.assertEqual(parent.split, 'TRAIN')
        self.assertEqual(parent.phase, 'experience')
        self.assertEqual(parent.episode_id, 'continual_stream')
        self.assertEqual(parent.origin, 'TRAIN_COLLECTION')
        self.assertEqual(parent.source_id, str(path))
        self.assertEqual(parent.source_sha256, hashlib.sha256(path.read_bytes()).hexdigest())
        self.step(incoming=incoming)
        self.step(incoming=self.journal.read_inbox())
        self.assertEqual(sum(item.event_id == parent.event_id for item in self.stream.history.events), 1)
        self.assertTrue(all(row['actor'] == 'child' for row in self.stream.rows))
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.read_inbox(), incoming)
        self.assertTrue(path.exists())

    def test_identical_duplicate_files_keep_first_canonical_source_after_restart(self):
        first = self.parent(name='z-first.json')
        original = self.journal.read_inbox()
        duplicate = self.journal.inbox / 'a-later.json'
        duplicate.write_bytes(first.read_bytes())
        self.assertEqual(self.journal.read_inbox(), original)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.read_inbox(), original)

    def test_inbox_conflicting_bytes_even_same_decoded_message_rejected(self):
        original = self.parent()
        self.journal.read_inbox()
        (self.journal.inbox / 'duplicate.json').write_bytes(original.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'conflicting_inbox_id_bytes'):
            self.journal.read_inbox()
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            with self.assertRaisesRegex(ValueError, 'conflicting_inbox_id_bytes'):
                reopened.read_inbox()

    def test_inbox_exact_schema_splits_and_actor_validation(self):
        path = self.journal.inbox / 'bad.json'
        base = dict(id='id', text='message', split='TRAIN', actor='parent')
        variants = [dict(base, split=split) for split in ('DEV', 'FINAL', 'PROBE')]
        variants += [dict(base, actor=actor) for actor in ('child', 'environment', 'system')]
        variants += [dict(base, extra=True), {'id': 'missing'}, dict(base, text=3), dict(base, id='')]
        for document in variants:
            path.write_text(json.dumps(document))
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.journal.read_inbox()
        self.assertEqual(list((self.root / 'records').iterdir()), [])

    def attributed_message(self, **changes):
        document = dict(schema='R127_ATTRIBUTED_INBOX_V1', id='a' * 32, text='A plain observation.',
                        split='TRAIN', actor='parent', speaker='Astra', source_receipt=None)
        document.update(changes)
        return document

    def test_mixed_legacy_and_R127_parents_render_only_human_readable_attribution(self):
        self.stream.set_presentation(dict(version=PLAIN_CONTEXT_VERSION,
            system_prompt='System.', birth_prompt='Birth.'), 16384)
        self.parent(name='0-legacy.json', text='Legacy remains unprefixed.')
        expected = ['Legacy remains unprefixed.']
        for index, speaker in enumerate(('Astra', 'Fable', 'Rohin'), start=1):
            document = self.attributed_message(id=f'{index:032x}', speaker=speaker)
            (self.journal.inbox / f'{index}-parent.json').write_text(json.dumps(document))
            expected.append(speaker + ': ' + document['text'])
        incoming = self.journal.read_inbox()
        self.assertEqual([event.text for event in incoming], expected)
        for event in incoming:
            self.assertEqual((event.actor, event.phase, event.split), ('parent', 'experience', 'TRAIN'))
            self.assertTrue(event.event_id.startswith('parent:inbox:'))
        captured = []

        def capture(messages, **kwargs):
            captured.extend(deepcopy(messages))
            return generate(messages, **kwargs)

        self.step(generate_call=capture, incoming=incoming)
        visible = '\n'.join(message['content'] for message in captured)
        for text in expected:
            self.assertIn(text, visible)
        for metadata in ('R127_ATTRIBUTED_INBOX_V1', 'source_receipt', '"actor"', '"speaker"'):
            self.assertNotIn(metadata, visible)
        self.assertEqual(self.journal.read_inbox(), incoming)
        self.step(incoming=incoming)
        for event in incoming:
            self.assertEqual(sum(item.event_id == event.event_id for item in self.stream.history.events), 1)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.read_inbox(), incoming)

    def test_R127_tool_source_is_preserved_but_not_rendered_or_used_as_child_target(self):
        self.stream.set_presentation(dict(version=PLAIN_CONTEXT_VERSION,
            system_prompt='System.', birth_prompt='Birth.'), 16384)
        source = dict(path=str(self.root / 'private-result.json'), sha256='b' * 64)
        document = self.attributed_message(actor='environment', speaker='Tool', source_receipt=source,
                                          text='Tool result status: PROCESS_FAILED\nstderr: actual failure')
        path = self.journal.inbox / 'tool.json'
        path.write_text(json.dumps(document))
        raw = path.read_bytes()
        incoming = self.journal.read_inbox()
        self.assertEqual(len(incoming), 1)
        event = incoming[0]
        self.assertEqual((event.actor, event.phase, event.split), ('environment', 'feedback', 'TRAIN'))
        self.assertEqual(event.event_id, 'environment:inbox:' + document['id'])
        self.assertEqual(event.text, 'Tool: ' + document['text'])
        self.assertEqual(event.source_id, str(path))
        self.assertEqual(event.source_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(event.origin, 'TRAIN_COLLECTION')
        recorded = json.loads(self.record_path(0).read_text())['document']
        self.assertEqual(recorded['message'], document)
        captured = []

        def capture(messages, **kwargs):
            captured.extend(deepcopy(messages))
            return generate(messages, **kwargs)

        self.step(generate_call=capture, incoming=incoming)
        visible = '\n'.join(message['content'] for message in captured)
        self.assertIn(event.text, visible)
        for metadata in (source['path'], source['sha256'], 'source_receipt', document['schema'],
                         '"actor"', '"source_id"', '"source_sha256"'):
            self.assertNotIn(metadata, visible)
        self.assertNotIn('success', event.text.lower())
        self.assertTrue(all(row['actor'] == 'child' for row in self.stream.rows))
        self.assertTrue(all(row['target'] == 'Synthetic child output.' for row in self.stream.rows))
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.read_inbox(), incoming)
        self.assertEqual(path.read_bytes(), raw)

    def test_R127_rejects_malformed_attribution_and_tool_sources_before_registration(self):
        source = dict(path=str(self.root / 'result.json'), sha256='b' * 64)
        parent = self.attributed_message()
        tool = self.attributed_message(actor='environment', speaker='Tool', source_receipt=source)
        variants = [dict(parent, speaker=speaker) for speaker in ('Tool', 'Unknown', '', None)]
        variants += [dict(parent, source_receipt=source), dict(parent, actor='child'),
                     dict(parent, schema='R127_ATTRIBUTED_INBOX_V2'), dict(parent, extra='no')]
        variants += [{key: value for key, value in parent.items() if key != omitted}
                     for omitted in ('schema', 'speaker', 'source_receipt')]
        variants += [dict(tool, speaker=speaker) for speaker in ('Astra', 'Fable', 'Rohin', None)]
        malformed_sources = [None, [], {}, {'path': source['path']}, {'sha256': source['sha256']},
                             dict(source, extra=True), dict(source, path='relative/result.json'),
                             dict(source, path=None), dict(source, path=12)]
        malformed_sources += [dict(source, sha256=value)
                              for value in ('b' * 63, 'b' * 65, 'z' * 64, 'B' * 64, None, 12)]
        variants += [dict(tool, source_receipt=receipt) for receipt in malformed_sources]
        path = self.journal.inbox / 'bad.json'
        for document in variants:
            path.write_text(json.dumps(document))
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.journal.read_inbox()
            self.assertEqual(list((self.root / 'records').iterdir()), [])
            self.assertEqual(self.stream.history.events, ())

    def test_legacy_and_R127_DEV_FINAL_never_register_or_enter_history(self):
        source = dict(path=str(self.root / 'result.json'), sha256='b' * 64)
        variants = [dict(id='legacy', text='sealed content', actor='parent'),
                    self.attributed_message(),
                    self.attributed_message(actor='environment', speaker='Tool', source_receipt=source)]
        self.parent(name='0-valid.json', text='Valid TRAIN still waits for an entirely valid inbox.')
        path = self.journal.inbox / '1-rejected.json'
        for base in variants:
            for split in ('DEV', 'FINAL'):
                document = dict(base, split=split)
                path.write_text(json.dumps(document))
                with self.subTest(actor=document['actor'], schema=document.get('schema'), split=split), \
                        self.assertRaises(ValueError):
                    self.journal.read_inbox()
                self.assertEqual(list((self.root / 'records').iterdir()), [])
                self.assertEqual(self.stream.history.events, ())

    def test_inbox_symlink_fifo_and_incomplete_json_rejected_without_wait(self):
        path = self.journal.inbox / 'bad.json'
        target = self.root / 'external.json'
        target.write_text('{}')
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'inbox_symlink_forbidden'):
            self.journal.read_inbox()
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, 'regular_file_required'):
            self.journal.read_inbox()
        path.unlink()
        path.write_text('{')
        with self.assertRaises(ValueError):
            self.journal.read_inbox()

    def test_registered_inbox_file_cannot_disappear_or_change_after_resume(self):
        path = self.parent()
        self.journal.read_inbox()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'registered_inbox_file_missing_or_changed'):
            self.journal.read_inbox()

    def test_sleep_partial_tail_never_falls_back_to_presleep_commit(self):
        self.step()
        original = StreamJournal._publish
        def fail(directory, name, document):
            if name == '00000000000000000003.json':
                raise OSError('sleep evidence publication failure')
            return original(directory, name, document)
        with patch.object(StreamJournal, '_publish', side_effect=fail):
            with self.assertRaises(OSError):
                self.stream.commit_sleep(self.receipt(), self.journal.record)
        self.assertTrue(self.stream.pending.startswith('sleep:'))
        self.journal.close()
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_tail'):
            StreamJournal(self.root)

    def sleep_request(self):
        pending = self.stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in self.stream.pending_rows()])
        pending['sha256'] = digest(pending['state'])
        return dict(cycle=len(self.stream.sleep_receipts) + 1, resume_state=pending)

    def test_native_metadata_does_not_override_authoritative_checkpoint(self):
        self.step()
        authoritative = self.journal.latest_checkpoint()
        for kind in ('LOADED', 'UPDATE', 'CHECKPOINT', 'TERMINAL'):
            self.journal.record(kind, {'state': {'untrusted': 'metadata'}, 'optimizer_step': 1})
            self.assertEqual(self.journal.latest_checkpoint(), authoritative)

    def test_compaction_snapshot_keeps_child_frontier(self):
        self.step()
        summary = replace(self.stream.history.events[-2], event_id='compaction:1', phase='compaction')
        self.stream.history.compact(summary, through=self.stream.history.frontier())
        self.journal.record('COMPACTION', dict(state=self.stream.checkpoint()))
        latest = self.journal.latest_checkpoint()
        self.assertEqual(latest['document'], self.stream.checkpoint())
        self.assertEqual(len(ContinualStream.restore(**latest).rows), 1)
        self.step()

    def test_native_birth_presleep_compaction_sleep_and_next_generation(self):
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.journal.record('LOADED', dict(runtime='synthetic'))
        self.step()
        self.step()
        self.assertTrue(self.stream.sleep_due)
        invitation = TrainEvent(event_id='presleep:1', actor='environment', split='TRAIN',
            phase='presleep', episode_id='continual_stream', source_id='R124_RUNTIME_INVITATION',
            source_sha256=digest([1, 'Synthetic invitation.']), origin='TRAIN_COLLECTION',
            text='Synthetic invitation.')
        self.step(incoming=[invitation])
        before = self.stream.checkpoint()['state']
        summary = replace(self.stream.history.events[-2], event_id='compaction:1', phase='compaction')
        through = self.stream.history.frontier(len(self.stream.history.events)-1)
        self.stream.history.compact(summary, through=through)
        self.journal.record('COMPACTION', dict(state=self.stream.checkpoint()))
        compacted = self.journal.latest_checkpoint()
        after = compacted['document']['state']
        self.assertEqual(after['history']['events'], before['history']['events'])
        for key in ('rows', 'model_state_sha256', 'sleep_frontier', 'sleep_receipts', 'pending'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['history']['operations'][-1]['through']['event_count'],
                         len(before['history']['events'])-1)
        self.journal.close()
        self.journal = StreamJournal(self.root)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.assertEqual(self.stream.checkpoint(), compacted['document'])
        pending = self.sleep_request()
        self.journal.record('SLEEP_REQUEST', pending)
        self.assertIsNone(self.stream.pending)
        self.assertTrue(self.journal.latest_checkpoint()['document']['state']['pending'].startswith('sleep:'))
        for kind in ('UPDATE', 'CHECKPOINT'):
            self.journal.record(kind, dict(cycle=1, state=compacted['document']))
            self.assertEqual(self.journal.latest_checkpoint()['document'], pending['resume_state'])
        receipt = dict(self.receipt(), cycle=1, checkpoint={'synthetic': True})
        self.stream.commit_sleep(receipt, self.journal.record)
        complete = self.journal.latest_checkpoint()
        self.assertEqual(complete['document'], self.stream.checkpoint())
        self.assertEqual(self.stream.sleep_frontier, 3)
        self.assertEqual(self.stream.model_state_sha256, digest(receipt['checkpoint_sha256']))
        self.assertEqual(self.stream.sleep_receipts, [receipt])
        self.assertIsNone(complete['document']['state']['pending'])
        self.step()
        self.assertEqual(len(self.stream.rows), 4)
        self.assertEqual(len(self.stream.pending_rows()), 1)
        self.journal.record('TERMINAL', dict(status='SYNTHETIC_TEST_COMPLETE'))
        final = self.journal.latest_checkpoint()
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(ContinualStream.restore(**reopened.latest_checkpoint()).checkpoint(),
                             final['document'])

    def test_ordinary_commit_cannot_publish_compaction_without_response(self):
        self.step()
        prior = self.journal.latest_checkpoint()
        summary = replace(self.stream.history.events[-2], event_id='compaction:1', phase='compaction')
        self.stream.history.compact(summary, through=self.stream.history.frontier())
        with self.assertRaisesRegex(ValueError, 'commit_requires_request_and_response'):
            self.journal.record('COMMITTED', dict(kind='CHILD_COMPACTION', state=self.stream.checkpoint()))
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.latest_checkpoint(), prior)

    def test_compaction_cannot_append_raw_events_or_change_learning_state(self):
        self.step()
        prior = self.journal.latest_checkpoint()
        summary = replace(self.stream.history.events[-2], event_id='compaction:1', phase='compaction')
        self.stream.history.compact(summary, through=self.stream.history.frontier())
        compacted = self.stream.checkpoint()
        variants = []
        self.stream.history.append(replace(summary, event_id='extra:raw', phase='experience'))
        variants.append(self.stream.checkpoint())
        for key, value in (('model_state_sha256', '0' * 64), ('sleep_frontier', 1),
                           ('sleep_receipts', [{'unexpected': True}])):
            changed = deepcopy(compacted)
            changed['state'][key] = value
            changed['sha256'] = digest(changed['state'])
            variants.append(changed)
        changed = deepcopy(compacted)
        changed['state']['rows'][0]['target'] = 'Rewritten child row.'
        changed['sha256'] = digest(changed['state'])
        variants.append(changed)
        self.journal.close()
        for document in variants:
            with self.subTest(document_sha256=document['sha256']):
                with StreamJournal(self.root) as reopened:
                    with self.assertRaisesRegex(ValueError,
                            'compaction_only_history_operations_advance|unexpected_stream_state_transition'):
                        reopened.record('COMPACTION', dict(state=document))
                with StreamJournal(self.root) as reopened:
                    self.assertEqual(reopened.latest_checkpoint(), prior)

    def test_compaction_cannot_clear_generation_request(self):
        self.step()
        stale = self.stream.checkpoint()
        def failure(*args, **kwargs):
            raise RuntimeError('synthetic generation failure')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=failure)
        pending = self.journal.latest_checkpoint()
        with self.assertRaisesRegex(ValueError, 'compaction_cannot_clear_pending'):
            self.journal.record('COMPACTION', dict(state=stale))
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertEqual(reopened.latest_checkpoint(), pending)

    def test_sleep_complete_must_match_cycle_and_exact_frontier(self):
        self.step()
        self.journal.record('SLEEP_REQUEST', self.sleep_request())
        pending = self.journal.latest_checkpoint()
        captured = []
        self.stream.commit_sleep(dict(self.receipt(), cycle=1), lambda kind, document: captured.append(document))
        complete = captured[0]
        variants = []
        for key, value in (('cycle', 2), ('new_row_sha256', ['0' * 64]),
                           ('checkpoint_sha256', dict(adapter='d' * 64, optimizer='b' * 64, rng='c' * 64))):
            changed = deepcopy(complete)
            changed[key] = value
            changed['resume_state']['state']['sleep_receipts'][-1][key] = value
            changed['resume_state']['sha256'] = digest(changed['resume_state']['state'])
            variants.append(changed)
        self.journal.close()
        for document in variants:
            with self.subTest(receipt=document):
                with StreamJournal(self.root) as reopened:
                    with self.assertRaisesRegex(ValueError,
                            'sleep_cycle_binding|sleep_frontier_binding|sleep_checkpoint_binding'):
                        reopened.record('SLEEP_COMPLETE', document)
                with StreamJournal(self.root) as reopened:
                    self.assertEqual(reopened.latest_checkpoint(), pending)
        with StreamJournal(self.root) as reopened:
            reopened.record('SLEEP_COMPLETE', complete)
            self.assertIsNone(reopened.latest_checkpoint()['document']['state']['pending'])

    def test_sleep_request_is_authoritative_after_mid_training_crash(self):
        self.step()
        request = self.sleep_request()
        self.journal.record('SLEEP_REQUEST', request)
        for kind in ('UPDATE', 'CHECKPOINT', 'TERMINAL'):
            self.journal.record(kind, {'partial_training': True})
        self.assertEqual(self.journal.latest_checkpoint()['document'], request['resume_state'])
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            restored = ContinualStream.restore(**reopened.latest_checkpoint())
            self.assertTrue(restored.pending.startswith('sleep:'))
            with self.assertRaisesRegex(ValueError, 'unresolved_request_never_redispatched'):
                restored.step(generate, tokens, reopened.record, now=lambda: 100)
            with self.assertRaisesRegex(ValueError, 'no_sleep_during_unresolved_generation'):
                restored.commit_sleep(self.receipt(), reopened.record)

    def test_matching_sleep_complete_resolves_durable_sleep_request(self):
        self.step()
        self.journal.record('SLEEP_REQUEST', self.sleep_request())
        receipt = dict(self.receipt(), cycle=1)
        self.stream.commit_sleep(receipt, self.journal.record)
        latest = self.journal.latest_checkpoint()
        self.assertIsNone(latest['document']['state']['pending'])
        self.assertEqual(ContinualStream.restore(**latest).sleep_frontier, 1)
        self.step()

    def test_stale_compaction_cannot_clear_sleep_request(self):
        self.step()
        stale = self.stream.checkpoint()
        self.journal.record('SLEEP_REQUEST', self.sleep_request())
        with self.assertRaisesRegex(ValueError, 'compaction_cannot_clear_pending'):
            self.journal.record('COMPACTION', dict(state=stale))
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            self.assertTrue(reopened.latest_checkpoint()['document']['state']['pending'].startswith('sleep:'))

    def test_invalid_sleep_request_hash_and_repeated_sleep_request_rejected(self):
        self.step()
        request = self.sleep_request()
        request['resume_state']['state']['pending'] = 'sleep:' + '0' * 64
        request['resume_state']['sha256'] = digest(request['resume_state']['state'])
        with self.assertRaisesRegex(ValueError, 'sleep_request_frontier_binding'):
            self.journal.record('SLEEP_REQUEST', request)
        self.journal.close()
        with StreamJournal(self.root) as reopened:
            reopened.record('SLEEP_REQUEST', self.sleep_request())
            with self.assertRaisesRegex(ValueError, 'unresolved_operation_before_sleep'):
                reopened.record('SLEEP_REQUEST', self.sleep_request())


class WallExtensionJournalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'stream'
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)
        with StreamJournal(self.root, create=True) as journal:
            for unused in range(2):
                self.stream.step(generate, tokens, journal.record, now=lambda: 100)
            self.stream.commit_sleep(dict(status='COMPLETE', optimizer_steps=2,
                new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
                checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64)), journal.record)
        self.previous = self.stream.checkpoint()

    def proposal(self):
        from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA
        current = deepcopy(self.previous)
        current['state']['deadline_unix'] = 2000
        current['sha256'] = digest(current['state'])
        return dict(schema='R131_WALL_EXTENDED_V1', plan_sha256='a' * 64, state=current,
            authorization=dict(schema=WALL_EXTENSION_SCHEMA, previous_deadline_unix=1000,
                previous_stream_sha256=self.previous['sha256'], new_deadline_unix=2000,
                lease_end_unix=2600, safety_margin_seconds=600))

    def reject(self, document):
        before = {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()}
        with StreamJournal(self.root) as journal, self.assertRaises(ValueError):
            journal.record('WALL_EXTENDED', document)
        self.assertEqual(before, {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()})
        with StreamJournal(self.root) as journal:
            self.assertEqual(journal.latest_checkpoint()['document'], self.previous)

    def test_extension_is_only_deadline_change_and_reopens_with_new_requests(self):
        proposal = self.proposal()
        with StreamJournal(self.root) as journal:
            journal.record('WALL_EXTENDED', proposal)
            self.assertEqual(journal.latest_checkpoint()['document'], proposal['state'])
        with StreamJournal(self.root) as journal:
            stream = ContinualStream.restore(**journal.latest_checkpoint())
            self.assertEqual(stream.deadline_unix, 2000)
            current = stream.checkpoint()['state']
            self.assertEqual({key: value for key, value in current.items() if key != 'deadline_unix'},
                {key: value for key, value in self.previous['state'].items() if key != 'deadline_unix'})
            stream.step(generate, tokens, journal.record, now=lambda: 1500)
            self.assertEqual(journal.latest_checkpoint()['document'], stream.checkpoint())

    def test_wrong_prior_wall_digest_shortening_and_lease_overrun_rejected(self):
        changes = [dict(previous_stream_sha256='0' * 64), dict(previous_deadline_unix=999),
            dict(new_deadline_unix=1000), dict(new_deadline_unix=999), dict(new_deadline_unix=2481),
            dict(safety_margin_seconds=119), dict(safety_margin_seconds=True),
            dict(new_deadline_unix=float('inf')), dict(extra='not allowed')]
        for change in changes:
            document = self.proposal()
            document['authorization'].update(change)
            with self.subTest(change=change):
                self.reject(document)

    def test_every_other_stream_field_frozen_including_model_optimizer_and_rng_hashes(self):
        variants = []
        for field, value in (('context_limit', 4097), ('segment_tokens', 127), ('segments_per_sleep', 3),
                             ('allow_eviction', True), ('model_state_sha256', 'd' * 64), ('sleep_frontier', 0)):
            document = self.proposal()
            document['state']['state'][field] = value
            variants.append(document)
        for field in ('optimizer', 'rng', 'adapter'):
            document = self.proposal()
            document['state']['state']['sleep_receipts'][-1]['checkpoint_sha256'][field] = 'd' * 64
            variants.append(document)
        document = self.proposal()
        document['state']['state']['rows'][0]['target'] = 'changed child text'
        variants.append(document)
        document = self.proposal()
        document['state']['state']['history']['birth_prompt'] = 'changed birth'
        variants.append(document)
        document = self.proposal()
        document['state']['state']['allow_eviction'] = 0
        variants.append(document)
        for index, document in enumerate(variants):
            document['state']['sha256'] = digest(document['state']['state'])
            with self.subTest(index=index):
                self.reject(document)

    def test_pending_generation_sleep_and_unslept_frontier_rejected(self):
        with StreamJournal(self.root) as journal:
            state = journal._scan()
            for pending in ('a' * 64, 'sleep:' + 'a' * 64):
                previous = deepcopy(self.previous)
                previous['state']['pending'] = pending
                previous['sha256'] = digest(previous['state'])
                staged = deepcopy(state)
                staged['latest'] = dict(document=previous, expected_sha256=previous['sha256'])
                document = self.proposal()
                document['authorization']['previous_stream_sha256'] = previous['sha256']
                with self.subTest(pending=pending), self.assertRaisesRegex(ValueError, 'wall_extension_saved_sleep_boundary'):
                    journal._advance(staged, 'WALL_EXTENDED', document)
            self.stream.step(generate, tokens, journal.record, now=lambda: 100)
            latest = journal.latest_checkpoint()
        self.previous = latest['document']
        self.reject(self.proposal())

    def test_missing_boundary_and_duplicate_extension_rejected(self):
        with StreamJournal(self.root) as journal:
            state = journal._scan()
            state['latest'] = None
            with self.assertRaisesRegex(ValueError, 'wall_extension_saved_sleep_boundary'):
                journal._advance(state, 'WALL_EXTENDED', self.proposal())
            journal.record('WALL_EXTENDED', self.proposal())
        with StreamJournal(self.root) as journal, self.assertRaisesRegex(ValueError, 'wall_extension_exact_prior_binding'):
            journal.record('WALL_EXTENDED', self.proposal())


if __name__ == '__main__':
    unittest.main()
