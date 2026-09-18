"""Synthetic CPU-only R134 fixtures; no native processes, launches or GPUs."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r127_pilot_console as inbox_api
from gpu import orch_r134_classroom_relay as relay_module
from gpu.orch_r125_stream_journal import StreamJournal, _digest
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION as PLAIN_VERSION


def token_count(messages):
    return sum(len(message['content'].split()) + 4 for message in messages)


class ClassroomRelayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.children = {name: self.root / name for name in ('A1005', 'A1006', 'A1007')}
        self.state_dir = self.root / 'relay'
        self.journals, self.streams = {}, {}
        for name, root in self.children.items():
            root.mkdir()
            journal = StreamJournal(root / 'stream', create=True)
            self.addCleanup(journal.close)
            self.journals[name] = journal
            stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
                context_limit=8192, segment_tokens=2, segments_per_sleep=2,
                deadline_unix=1000, model_state_sha256='f' * 64)
            self.streams[name] = stream
            journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))

    def relay(self, **options):
        options.setdefault('cadence', 'committed')
        instance = relay_module.ClassroomRelay(self.children, self.state_dir, **options)
        self.addCleanup(instance.close)
        return instance

    def step(self, name='A1005', text='Exact peer output.\nSecond line.', *, incoming=(), truncated=False,
            response_fields=None):
        def generate(messages, **kwargs):
            return dict(raw=text, token_ids=[10, 2], terminal=not truncated, truncated=truncated,
                **(response_fields or {}))
        return self.streams[name].step(generate, token_count, self.journals[name].record,
            incoming=incoming, now=lambda: 100)

    def sleep(self, name='A1005'):
        stream = self.streams[name]
        receipt = dict(status='COMPLETE', optimizer_steps=1,
            new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        stream.commit_sleep(receipt, self.journals[name].record)

    def pump(self, relay, count=8):
        return [relay.poll() for unused in range(count)]

    def inbox(self, name):
        return [json.loads(path.read_bytes()) for path in sorted((self.children[name] / 'stream' / 'inbox').glob('*.json'))]

    def receipts(self, kind):
        return [json.loads(path.read_bytes()) for path in sorted(self.state_dir.glob(kind + '_*.json'))]

    def record_path(self, kind, name='A1005'):
        return next(path for path in sorted((self.children[name] / 'stream' / 'records').glob('*.json'))
            if not path.name.endswith('.intent.json') and json.loads(path.read_bytes())['kind'] == kind)

    def rewrite(self, kind, change, name='A1005'):
        directory = self.children[name] / 'stream' / 'records'
        records = sorted(path for path in directory.glob('*.json') if not path.name.endswith('.intent.json'))
        previous = _digest(json.loads((directory.parent / 'JOURNAL.json').read_bytes()))
        changed = False
        for path in records:
            record = json.loads(path.read_bytes())
            if record['kind'] == kind and not changed:
                change(record['document'])
                changed = True
            record['previous_sha256'] = previous
            record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
            path.write_text(json.dumps(record))
            path.with_name(path.stem + '.intent.json').write_text(json.dumps(StreamJournal._intent(record)))
            previous = record['sha256']
        self.assertTrue(changed)

    def test_exact_provenance_plain_attribution_and_real_consumption(self):
        text = 'An exact response with π and newlines.\nNot receiver thoughts.'
        self.step(text=text)
        relay = self.relay()
        self.pump(relay)
        self.assertEqual(self.inbox('A1005'), [])
        source = self.receipts('source')[0]
        self.assertEqual(source['raw'], text)
        self.assertEqual(source['split'], 'TRAIN')
        self.assertNotIn('messages', source)
        self.assertNotIn('prefix', source)
        for kind in ('request', 'response', 'committed'):
            reference = source[kind]
            raw = Path(reference['path']).read_bytes()
            record = json.loads(raw)
            self.assertEqual(reference['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(reference['record_sha256'], record['sha256'])
            self.assertEqual(reference['document_sha256'], _digest(record['document']))
            intent_path = Path(reference['path']).with_suffix('.intent.json')
            self.assertEqual(reference['intent_sha256'], hashlib.sha256(intent_path.read_bytes()).hexdigest())
        for receiver in ('A1006', 'A1007'):
            message, = self.inbox(receiver)
            self.assertEqual((message['schema'], message['actor'], message['speaker'], message['split']),
                (inbox_api.SCHEMA, 'environment', 'Tool', 'TRAIN'))
            self.assertEqual(message['text'], 'Peer A1005: ' + text)
            bound = message['source_receipt']
            self.assertEqual(bound['sha256'], hashlib.sha256(Path(bound['path']).read_bytes()).hexdigest())
            self.assertEqual(Path(bound['path']).stat().st_mode & 0o777, 0o400)
            self.assertEqual(self.streams[receiver].rows, [])
        self.assertEqual(self.receipts('consumption'), [])
        incoming = self.journals['A1006'].read_inbox()
        self.pump(relay)
        self.assertEqual(self.receipts('consumption'), [])
        self.assertEqual(incoming[0].actor, 'environment')
        self.assertEqual(incoming[0].text, 'Tool: Peer A1005: ' + text)
        self.step('A1006', incoming=incoming)
        self.pump(relay)
        consumed, = self.receipts('consumption')
        self.assertEqual(consumed['status'], 'IN_REQUEST')
        self.assertEqual(consumed['receiver_request']['path'], str(self.record_path('REQUEST', 'A1006')))

    def test_parent_and_environment_inboxes_never_forwarded_or_other_paths_read(self):
        parent = inbox_api.publish_parent(self.children['A1005'], 'Rohin', 'PRIVATE PARENT NOTE')
        tool = inbox_api._inbox(self.children['A1005'], 'Tool', 'PRIVATE ENVIRONMENT',
            dict(path='/not/to/be/opened/FINAL.json', sha256='a' * 64))
        self.journals['A1005'].read_inbox()
        for forbidden in ('readouts', 'held', 'FINAL', 'responses'):
            path = self.children['A1005'] / forbidden
            path.mkdir()
            (path / 'RESPONSE.json').write_text('NEVER OPEN')
        original = inbox_api._read
        reads = []
        def guarded(directory, name, limit):
            path = Path(os.readlink('/proc/self/fd/' + str(directory))) / name
            reads.append(path)
            self.assertNotIn(path.parent.name, ('readouts', 'held', 'FINAL', 'responses', 'inbox'))
            return original(directory, name, limit)
        with patch.object(inbox_api, '_read', side_effect=guarded):
            relay = self.relay()
            self.pump(relay)
        self.assertTrue(reads)
        self.assertEqual(self.inbox('A1006'), [])
        self.assertEqual(self.inbox('A1007'), [])
        self.assertEqual(self.receipts('source'), [])
        self.assertTrue(Path(parent['path']).exists())
        self.assertTrue(Path(tool['path']).exists())

    def test_uncommitted_response_and_partial_commit_wait_untouched(self):
        self.step()
        path = self.children['A1005'] / 'stream' / 'records' / '00000000000000000003.json'
        raw = path.read_bytes()
        partial = path.with_suffix('.json.partial')
        path.rename(partial)
        relay = self.relay()
        self.pump(relay)
        self.assertEqual(self.receipts('source'), [])
        self.assertEqual(partial.read_bytes(), raw)
        partial.rename(path)
        self.pump(relay)
        self.assertEqual(len(self.receipts('publication')), 2)

    def test_corrupt_published_bytes_fail_closed(self):
        self.step()
        self.record_path('RESPONSE').write_bytes(b'{"partial":')
        with self.assertRaises(ValueError):
            self.pump(self.relay())
        self.assertEqual(self.inbox('A1006'), [])

    def test_source_request_split_and_response_hash_bindings(self):
        self.step()
        self.rewrite('REQUEST', lambda document: document.update(split='HELD'))
        with self.assertRaisesRegex(ValueError, 'request_checkpoint_binding'):
            self.pump(self.relay())
        self.assertEqual(self.receipts('source'), [])

    def test_explicit_held_response_excluded_even_if_native_committed_it(self):
        self.step(response_fields=dict(split='HELD'))
        with self.assertRaisesRegex(ValueError, 'source_TRAIN_child_provenance'):
            self.pump(self.relay())
        self.assertEqual(self.inbox('A1006'), [])

    def test_explicit_parent_response_excluded_even_if_native_committed_it(self):
        self.step(response_fields=dict(actor='parent'))
        with self.assertRaisesRegex(ValueError, 'source_TRAIN_child_provenance'):
            self.pump(self.relay())
        self.assertEqual(self.inbox('A1006'), [])

    def test_response_must_bind_exact_request(self):
        self.step()
        self.rewrite('RESPONSE', lambda document: document.update(request_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'response_request_binding'):
            self.pump(self.relay())

    def test_commit_must_bind_exact_response(self):
        self.step()
        def alter(document):
            if document.get('segment') == 0:
                document['source_sha256'] = '0' * 64
        self.rewrite('COMMITTED', lambda document: None)
        path = self.children['A1005'] / 'stream' / 'records' / '00000000000000000003.json'
        record = json.loads(path.read_bytes())
        alter(record['document'])
        record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
        path.write_text(json.dumps(record))
        path.with_name(path.stem + '.intent.json').write_text(json.dumps(StreamJournal._intent(record)))
        with self.assertRaisesRegex(ValueError, 'commit_response_binding'):
            self.pump(self.relay())

    def test_committed_parent_target_excluded_even_with_rehashed_checkpoint(self):
        self.step()
        path = self.children['A1005'] / 'stream' / 'records' / '00000000000000000003.json'
        record = json.loads(path.read_bytes())
        checkpoint = record['document']['state']
        checkpoint['state']['rows'][-1]['actor'] = 'parent'
        checkpoint['sha256'] = _digest(checkpoint['state'])
        record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
        path.write_text(json.dumps(record))
        path.with_name(path.stem + '.intent.json').write_text(json.dumps(StreamJournal._intent(record)))
        with self.assertRaisesRegex(ValueError, 'restored_child_targets_only'):
            self.pump(self.relay())

    def test_intent_and_chain_tampering_excluded(self):
        self.step()
        path = self.record_path('RESPONSE').with_suffix('.intent.json')
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'journal_intent_binding'):
            self.pump(self.relay())

    def test_restart_and_duplicate_polls_do_not_republish(self):
        self.step()
        relay = self.relay()
        self.pump(relay)
        before = {path.name: path.read_bytes() for path in self.state_dir.glob('*.json')}
        relay.close()
        restarted = self.relay()
        self.pump(restarted)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.state_dir.glob('*.json')})
        self.assertEqual(len(self.inbox('A1006')), 1)
        self.assertEqual(len(self.inbox('A1007')), 1)
        self.assertEqual(restarted.poll()['total_attempts'], 2)

    def test_sender_response_pair_identity_ignores_file_whitespace_changes(self):
        self.step()
        relay = self.relay()
        self.pump(relay)
        relay.close()
        path = self.record_path('RESPONSE')
        path.write_bytes(path.read_bytes() + b' ')
        self.pump(self.relay())
        self.assertEqual(len(self.inbox('A1006')), 1)
        self.assertEqual(len(self.inbox('A1007')), 1)

    def test_partial_fanout_resumes_only_unattempted_receiver(self):
        self.step()
        relay = self.relay(max_messages_per_poll=1)
        self.assertEqual(relay.poll()['dispatch_attempts'], 1)
        relay.close()
        self.pump(self.relay(max_messages_per_poll=1))
        self.assertEqual(len(self.inbox('A1006')), 1)
        self.assertEqual(len(self.inbox('A1007')), 1)

    def test_uncertain_dispatch_after_publication_never_replayed_and_can_be_observed(self):
        self.step()
        relay = self.relay()
        original = inbox_api._inbox
        def lost_ack(*args):
            original(*args)
            raise OSError('synthetic lost acknowledgement')
        with patch.object(inbox_api, '_inbox', side_effect=lost_ack):
            self.pump(relay)
        self.assertEqual(len(self.receipts('uncertain')), 2)
        self.assertEqual(self.receipts('publication'), [])
        relay.close()
        restarted = self.relay()
        self.pump(restarted)
        self.assertEqual(len(self.inbox('A1006')), 1)
        incoming = self.journals['A1006'].read_inbox()
        self.step('A1006', incoming=incoming)
        self.pump(restarted)
        self.assertEqual(len(self.receipts('observed_publication')), 1)
        self.assertEqual(len(self.receipts('consumption')), 1)

    def test_uncertain_dispatch_before_publication_never_replayed(self):
        self.step()
        relay = self.relay()
        with patch.object(inbox_api, '_inbox', side_effect=OSError('synthetic pre-publication failure')):
            self.pump(relay)
        relay.close()
        with patch.object(inbox_api, '_inbox') as publication:
            self.pump(self.relay())
        publication.assert_not_called()
        self.assertEqual(self.inbox('A1006'), [])

    def test_partial_intent_reserves_pair_without_dispatch_on_restart(self):
        self.step()
        relay = self.relay()
        original = inbox_api._stage
        def torn(directory, name, raw):
            if name.startswith('intent_'):
                descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400, dir_fd=directory)
                os.write(descriptor, b'{')
                os.close(descriptor)
                raise OSError('synthetic torn intent')
            return original(directory, name, raw)
        with patch.object(inbox_api, '_stage', side_effect=torn), self.assertRaises(OSError):
            self.pump(relay)
        partial, = self.state_dir.glob('intent_*.partial')
        self.assertEqual(partial.read_bytes(), b'{')
        restarted = self.relay()
        self.pump(restarted)
        self.assertEqual(self.inbox('A1006'), [])
        self.assertEqual(len(self.inbox('A1007')), 1)
        self.assertEqual(restarted.poll()['total_attempts'], 2)

    def test_partial_publication_receipt_does_not_replay(self):
        self.step()
        relay = self.relay()
        original = inbox_api._stage
        def torn(directory, name, raw):
            if name.startswith('publication_'):
                descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400, dir_fd=directory)
                os.write(descriptor, raw[:5])
                os.close(descriptor)
                raise OSError('synthetic torn publication receipt')
            return original(directory, name, raw)
        with patch.object(inbox_api, '_stage', side_effect=torn):
            self.pump(relay)
        relay.close()
        self.pump(self.relay())
        self.assertEqual(len(self.inbox('A1006')), 1)
        self.assertEqual(len(self.inbox('A1007')), 1)
        self.assertEqual(len(list(self.state_dir.glob('publication_*.partial'))), 2)

    def test_truncation_preserved_and_message_never_sliced(self):
        self.step(text='Exact cap-limited text.', truncated=True)
        self.pump(self.relay())
        source, = self.receipts('source')
        self.assertTrue(source['truncated'])
        self.assertFalse(source['terminal'])
        self.assertEqual(self.inbox('A1006')[0]['text'], 'Peer A1005 (source truncated): Exact cap-limited text.')

    def test_oversized_message_rejected_instead_of_truncated(self):
        self.step(text='π' * 60)
        self.pump(self.relay(max_message_bytes=100))
        self.assertEqual(self.inbox('A1006'), [])
        self.assertEqual(self.receipts('intent'), [])
        rejected, = self.receipts('rejected')
        self.assertEqual(rejected['status'], 'MESSAGE_LIMIT')
        self.assertEqual(rejected['source']['raw'], 'π' * 60)

    def test_wire_size_includes_json_escaping_and_provenance(self):
        self.step(text='\\' * 1000)
        self.pump(self.relay(max_message_bytes=1500))
        self.assertEqual(self.inbox('A1006'), [])
        self.assertEqual(len(self.receipts('rejected')), 1)

    def test_per_poll_and_persistent_total_limits(self):
        for name in self.children:
            self.step(name, text=name)
        relay = self.relay(max_messages_per_poll=1, max_total_messages=3, max_records_per_poll=2)
        results = self.pump(relay, 30)
        self.assertTrue(all(result['records'] <= 2 and result['dispatch_attempts'] <= 1 for result in results))
        self.assertEqual(len(self.receipts('intent')), 3)
        self.assertTrue(results[-1]['total_limit_reached'])
        relay.close()
        restarted = self.relay(max_messages_per_poll=1, max_total_messages=3, max_records_per_poll=2)
        self.pump(restarted, 30)
        self.assertEqual(len(self.receipts('intent')), 3)

    def test_three_active_peers_all_to_all_without_self_delivery(self):
        for name in self.children:
            self.step(name, text=name)
        self.pump(self.relay())
        self.assertEqual(len(self.receipts('publication')), 6)
        for name in self.children:
            self.assertEqual({message['text'] for message in self.inbox(name)},
                {'Peer ' + peer + ': ' + peer for peer in self.children if peer != name})

    def test_sleep_cadence_releases_only_last_response_of_complete_sleep(self):
        relay = self.relay(cadence='sleep')
        self.step(text='First')
        self.step(text='Last')
        self.pump(relay)
        self.assertEqual(self.inbox('A1006'), [])
        self.sleep()
        self.pump(relay)
        self.assertEqual([message['text'] for message in self.inbox('A1006')], ['Peer A1005: Last'])
        self.step(text='Unfinished next group')
        self.pump(relay)
        self.assertEqual(len(self.inbox('A1006')), 1)

    def test_experience_group_cadence_is_restart_stable(self):
        relay = self.relay(cadence='experience_group', group_size=2)
        self.step(text='First')
        self.pump(relay)
        self.assertEqual(self.inbox('A1006'), [])
        self.step(text='Second')
        self.pump(relay)
        relay.close()
        self.step(text='Third')
        self.pump(self.relay(cadence='experience_group', group_size=2))
        self.assertEqual([message['text'] for message in self.inbox('A1006')], ['Peer A1005: Second'])

    def test_source_changed_between_receiver_dispatches_fails_closed(self):
        self.step()
        relay = self.relay(max_messages_per_poll=1)
        relay.poll()
        self.assertEqual(len(self.inbox('A1006')), 1)
        path = self.record_path('RESPONSE')
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'source_changed_before_publication'):
            self.pump(relay)
        self.assertEqual(self.inbox('A1007'), [])

    def test_source_intent_changed_between_dispatches_fails_closed(self):
        self.step()
        relay = self.relay(max_messages_per_poll=1)
        relay.poll()
        path = self.record_path('RESPONSE').with_suffix('.intent.json')
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'source_intent_changed_before_publication'):
            self.pump(relay)
        self.assertEqual(self.inbox('A1007'), [])

    def test_sleep_boundary_revalidated_before_remaining_dispatch(self):
        self.step()
        self.sleep()
        relay = self.relay(cadence='sleep', max_messages_per_poll=1)
        relay.poll()
        path = self.record_path('SLEEP_COMPLETE')
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'source_changed_before_publication'):
            self.pump(relay)
        self.assertEqual(self.inbox('A1007'), [])

    def test_config_roster_and_cadence_frozen(self):
        relay = self.relay()
        relay.close()
        with self.assertRaisesRegex(ValueError, 'immutable_receipt_conflict'):
            self.relay(cadence='sleep')

    def test_actual_plain_context_consumption(self):
        stream = self.streams['A1006']
        stream.set_presentation(dict(version=PLAIN_VERSION, system_prompt='Plain system.', birth_prompt='Plain birth.'), 16384)
        self.journals['A1006'].record('PRESENTATION', dict(state=stream.checkpoint()))
        self.step()
        relay = self.relay()
        self.pump(relay)
        incoming = self.journals['A1006'].read_inbox()
        self.step('A1006', incoming=incoming)
        self.pump(relay)
        self.assertEqual(len(self.receipts('consumption')), 1)

    def test_registered_but_evicted_peer_not_claimed_consumed(self):
        self.step()
        relay = self.relay()
        self.pump(relay)
        incoming = self.journals['A1006'].read_inbox()
        stream = self.streams['A1006']
        for event in incoming:
            stream.history.append(event)
        stream.history.evict_oldest(stream.history.frontier(), reason='Synthetic pre-request eviction')
        self.step('A1006')
        self.pump(relay)
        self.assertEqual(self.receipts('consumption'), [])

    def test_directory_replacement_after_poll_is_rejected(self):
        relay = self.relay()
        original = self.children['A1006'] / 'stream' / 'inbox'
        original.rename(original.with_name('previous_inbox'))
        original.mkdir()
        with self.assertRaisesRegex(ValueError, 'journal_directory_replaced'):
            relay.poll()

    def test_published_receipt_binds_consumption_to_actual_inbox_id(self):
        self.step()
        relay = self.relay()
        self.pump(relay)
        original = self.inbox('A1006')[0]
        inbox_api._inbox(self.children['A1006'], 'Tool', original['text'], original['source_receipt'])
        incoming = [event for event in self.journals['A1006'].read_inbox()
            if not event.event_id.endswith(original['id'])]
        self.step('A1006', incoming=incoming)
        with self.assertRaisesRegex(ValueError, 'consumption_publication_binding'):
            self.pump(relay)
        self.assertEqual(self.receipts('consumption'), [])

    def test_requires_three_distinct_peers_and_safe_labels(self):
        for children in ({'one': self.children['A1005']},
                dict(self.children, A1006=self.children['A1005']),
                {'bad\nname': self.children['A1005'], 'two': self.children['A1006'], 'three': self.children['A1007']}):
            with self.subTest(children=children), self.assertRaises(ValueError):
                relay_module.ClassroomRelay(children, self.state_dir)

    def test_symlink_source_rejected_and_relay_lock_does_not_touch_writer_locks(self):
        linked = self.root / 'linked'
        linked.symlink_to(self.children['A1005'], target_is_directory=True)
        with self.assertRaises(OSError):
            relay_module.ClassroomRelay(dict(self.children, A1005=linked), self.state_dir)
        relay = self.relay()
        with self.assertRaises(BlockingIOError):
            self.relay()
        self.step()
        self.pump(relay)
        self.assertEqual(len(self.receipts('publication')), 2)

    def test_bounded_scan_bytes_wait_without_changing_sources(self):
        self.step()
        relay = self.relay(max_record_bytes=65536, max_scan_bytes_per_poll=270336)
        with patch.object(relay_module._Budget, 'read', side_effect=relay_module._PollLimit):
            result = relay.poll()
        self.assertEqual(result['dispatch_attempts'], 0)
        self.pump(relay)
        self.assertEqual(len(self.receipts('publication')), 2)

    def test_cli_one_bounded_poll(self):
        self.step()
        argv = ['--state-dir', str(self.state_dir), '--cadence', 'committed', '--total-polls', '1']
        for name, root in self.children.items():
            argv.extend(['--child', name + '=' + str(root)])
        with patch('builtins.print') as output, patch.object(relay_module.time, 'sleep') as sleep:
            self.assertEqual(relay_module.main(argv), 0)
        sleep.assert_not_called()
        self.assertEqual(json.loads(output.call_args.args[0])['dispatch_attempts'], 2)


if __name__ == '__main__':
    unittest.main()
