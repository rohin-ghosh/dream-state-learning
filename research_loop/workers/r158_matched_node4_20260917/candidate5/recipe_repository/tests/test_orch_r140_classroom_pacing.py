"""CPU-only synthetic journals; no provider, model or live-node operations."""

import hashlib
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from gpu import orch_r134_classroom_relay as relay
from gpu import orch_r140_classroom_pacing as pacing
from tests import test_orch_r134_classroom_relay as fixtures


class ReceiverSleepPacingTests(unittest.TestCase):
    step = fixtures.ClassroomRelayTests.step
    sleep = fixtures.ClassroomRelayTests.sleep
    pump = fixtures.ClassroomRelayTests.pump
    inbox = fixtures.ClassroomRelayTests.inbox
    receipts = fixtures.ClassroomRelayTests.receipts
    record_path = fixtures.ClassroomRelayTests.record_path
    rewrite = fixtures.ClassroomRelayTests.rewrite

    def setUp(self):
        fixtures.ClassroomRelayTests.setUp(self)
        self.predecessor = self.root / 'old_relay'
        self.deadline = time.time() + 7200
        with relay.ClassroomRelay(self.children, self.predecessor) as old:
            self.pump(old)
        self.state_dir = self.root / 'pacing'

    def start(self, **options):
        instance = pacing.ReceiverSleepPacing(self.children, self.state_dir, self.predecessor,
            hard_end_unix=self.deadline, **options)
        self.addCleanup(instance.close)
        return instance

    def cycle(self, name, text='Exact new response.', *, consume=False):
        incoming = self.journals[name].read_inbox() if consume else ()
        self.step(name, text=text + ' first', incoming=incoming)
        self.step(name, text=text + ' second')
        self.sleep(name)

    def all_cycles(self, *, consume=False):
        for name in self.children:
            self.cycle(name, consume=consume)

    def publications(self, receiver):
        rotation = {slot['source_receipt']['sha256']: slot['rotation_index']
            for slot in self.receipts('slot') if slot['receiver'] == receiver}
        messages = [message for message in self.inbox(receiver)
            if message['source_receipt'] and Path(message['source_receipt']['path']).parent == self.state_dir]
        return sorted(messages, key=lambda message: rotation[message['source_receipt']['sha256']])

    def hashes(self, root):
        return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}

    def test_bootstrap_pins_heads_without_backfill_or_child_changes(self):
        self.all_cycles()
        child_before = {name: self.hashes(root) for name, root in self.children.items()}
        predecessor_before = self.hashes(self.predecessor)
        instance = self.start()
        self.pump(instance)
        phase = json.loads((self.state_dir / 'PHASE.json').read_text())
        self.assertEqual(phase['schema'], pacing.SCHEMA)
        self.assertTrue(all(head['index'] > 1 for head in phase['heads'].values()))
        self.assertEqual(self.receipts('publication'), [])
        self.assertEqual(predecessor_before, self.hashes(self.predecessor))
        self.assertEqual(child_before, {name: self.hashes(root) for name, root in self.children.items()})

    def test_one_per_receiver_sleep_not_sender_broadcast(self):
        instance = self.start()
        self.pump(instance)
        self.cycle('A1006')
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])
        self.cycle('A1005')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.assertEqual(len(self.publications('A1006')), 1)
        self.assertEqual(self.publications('A1007'), [])
        self.cycle('A1006')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)

    def test_all_three_receivers_get_three_not_six_publications(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        self.assertEqual(len(self.receipts('publication')), 3)
        self.assertEqual([len(self.publications(name)) for name in self.children], [1, 1, 1])

    def test_latest_source_only_and_durable_supersession(self):
        instance = self.start()
        self.pump(instance)
        self.cycle('A1006', text='Stale')
        self.cycle('A1006', text='Latest')
        self.cycle('A1005')
        self.pump(instance)
        message, = self.publications('A1005')
        self.assertEqual(message['text'], 'Peer A1006: Latest second')
        self.assertTrue(self.receipts('superseded'))
        self.assertTrue(self.receipts('skipped'))

    def test_rotation_requires_exposure_followed_by_later_sleep(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        self.cycle('A1005')
        self.cycle('A1007')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        incoming = self.journals['A1005'].read_inbox()
        self.step('A1005', incoming=incoming)
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.step('A1005')
        self.sleep('A1005')
        self.pump(instance)
        messages = self.publications('A1005')
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0]['text'].startswith('Peer A1006:'))
        self.assertTrue(messages[1]['text'].startswith('Peer A1007:'))

    def test_registration_alone_never_releases_backpressure(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        self.journals['A1005'].read_inbox()
        self.cycle('A1005')
        self.cycle('A1007')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.assertFalse([receipt for receipt in self.receipts('consumption')
            if '/A1005/' in receipt['receiver_request']['path']])

    def test_restart_does_not_refill_epochs_or_repeat_pairs(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        before = self.hashes(self.state_dir)
        instance.close()
        restarted = self.start()
        self.pump(restarted)
        self.assertEqual(before, self.hashes(self.state_dir))
        self.all_cycles(consume=True)
        self.pump(restarted)
        self.assertEqual(len(self.publications('A1005')), 2)
        self.assertTrue(self.publications('A1005')[-1]['text'].startswith('Peer A1007:'))

    def test_restart_after_many_unobserved_sleeps_never_backfills(self):
        instance = self.start()
        self.pump(instance)
        instance.close()
        for count in range(4):
            self.all_cycles()
        restarted = self.start(max_records_per_poll=96)
        self.pump(restarted, count=20)
        self.assertEqual(len(self.receipts('publication')), 3)
        self.assertTrue(all(len(slots) == 1 for slots in restarted.slots.values()))

    def test_phase_and_policy_changes_rejected_on_resume(self):
        instance = self.start()
        self.pump(instance)
        instance.close()
        with self.assertRaisesRegex(ValueError, 'immutable_pacing_receipt_conflict'):
            self.start(max_messages_per_poll=1)

    def test_predecessor_running_or_restarted_is_excluded(self):
        with relay.ClassroomRelay(self.children, self.predecessor):
            with self.assertRaises(BlockingIOError):
                self.start()
        instance = self.start()
        with self.assertRaises(BlockingIOError):
            relay.ClassroomRelay(self.children, self.predecessor)
        with self.assertRaises(BlockingIOError):
            self.start()
        instance.close()

    def test_predecessor_bytes_change_rejects_resume(self):
        instance = self.start()
        self.pump(instance)
        instance.close()
        path = self.predecessor / ('intent_' + 'a' * 64 + '.partial')
        path.write_text('{')
        with self.assertRaisesRegex(ValueError, 'immutable_pacing_receipt_conflict'):
            self.start()

    def test_predecessor_uncertain_partial_is_never_retried(self):
        (self.predecessor / ('intent_' + 'a' * 64 + '.partial')).write_text('{')
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        self.assertEqual(instance.inherited_count, 1)
        self.assertEqual(self.receipts('publication'), [])
        self.assertTrue(instance.unknown_predecessor_attempt)

    def test_old_queued_messages_drain_without_old_custody_writes(self):
        self.cycle('A1006', text='Old source')
        with relay.ClassroomRelay(self.children, self.predecessor) as old:
            self.pump(old)
        old_before = self.hashes(self.predecessor)
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])
        self.cycle('A1005', consume=True)
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.assertTrue(self.receipts('inherited_consumption'))
        self.assertEqual(old_before, self.hashes(self.predecessor))

    def test_old_published_pairs_excluded_even_after_restart(self):
        self.cycle('A1006')
        with relay.ClassroomRelay(self.children, self.predecessor) as old:
            self.pump(old)
        instance = self.start()
        self.pump(instance)
        self.assertEqual(instance.inherited_count, 2)
        self.cycle('A1005', consume=True)
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])
        instance.close()
        restarted = self.start()
        self.pump(restarted)
        self.assertEqual(self.publications('A1005'), [])

    def test_publish_then_raise_is_uncertain_never_replayed(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        original = relay.inbox_api._inbox
        def uncertain(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('unknown delivery acknowledgement')
        with patch.object(relay.inbox_api, '_inbox', side_effect=uncertain):
            self.pump(instance)
        self.assertEqual(len(self.receipts('uncertain')), 3)
        self.assertEqual(len(self.inbox('A1005')), 1)
        instance.close()
        restarted = self.start()
        self.pump(restarted)
        self.assertEqual(len(self.inbox('A1005')), 1)
        self.all_cycles(consume=True)
        self.pump(restarted)
        self.assertEqual(len(self.inbox('A1005')), 2)
        self.assertTrue(self.receipts('observed_publication'))

    def test_partial_slot_consumes_pair_epoch_and_rotation(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        original = instance._persist
        def interrupted(identifier, fields):
            if identifier.startswith('slot_'):
                (self.state_dir / (identifier + '.partial')).write_text('{')
                raise OSError('interrupted slot reservation')
            return original(identifier, fields)
        with patch.object(instance, '_persist', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.pump(instance)
        restarted = self.start()
        self.pump(restarted)
        self.assertEqual(self.publications('A1005'), [])
        self.cycle('A1005')
        self.cycle('A1007')
        self.pump(restarted)
        self.assertEqual(self.publications('A1005'), [])
        self.assertEqual(len(restarted.slots['A1005']), 1)

    def test_oversize_is_skipped_without_truncation(self):
        instance = self.start(max_message_bytes=600)
        self.pump(instance)
        self.cycle('A1006', text='x' * 2000)
        self.cycle('A1005')
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])
        self.assertTrue([item for item in self.receipts('slot') if item['status'] == 'SKIPPED_OVERSIZE'])

    def test_source_flags_and_exact_environment_attribution(self):
        instance = self.start()
        self.pump(instance)
        self.step('A1006')
        self.step('A1006', text='Exact π second experience, not a summary.', truncated=True)
        self.sleep('A1006')
        self.cycle('A1005')
        self.pump(instance)
        message, = self.publications('A1005')
        self.assertEqual(message['actor'], 'environment')
        self.assertEqual(message['speaker'], 'Tool')
        self.assertEqual(message['split'], 'TRAIN')
        self.assertEqual(message['text'], 'Peer A1006 (source truncated): Exact π second experience, not a summary.')
        self.assertFalse('summary' in pacing.POLICY['source'])

    def test_no_distillation_sender_has_no_extra_generation(self):
        instance = self.start()
        self.pump(instance)
        self.cycle('A1005')
        self.cycle('A1006')
        self.cycle('A1007', text='Two experience segments')
        self.pump(instance)
        self.cycle('A1005', consume=True)
        self.pump(instance)
        message = self.publications('A1005')[-1]
        self.assertEqual(message['text'], 'Peer A1007: Two experience segments second')
        self.assertEqual(len(self.streams['A1007'].rows), 2)

    def test_parent_environment_and_held_paths_never_read_as_sources(self):
        instance = self.start()
        self.pump(instance)
        publication = relay.inbox_api.publish_parent(self.children['A1006'], 'Astra', 'Private parent prefix')
        self.step('A1006', incoming=self.journals['A1006'].read_inbox())
        self.step('A1006', text='Only actual child continuation')
        self.sleep('A1006')
        self.cycle('A1005')
        original = relay.inbox_api._read
        def guarded(directory, name, limit):
            path = Path(os.readlink('/proc/self/fd/' + str(directory))) / name
            self.assertNotIn(path.parent.name, ('held', 'readouts', 'FINAL'))
            return original(directory, name, limit)
        with patch.object(relay.inbox_api, '_read', side_effect=guarded):
            self.pump(instance)
        self.assertEqual(self.publications('A1005')[0]['text'], 'Peer A1006: Only actual child continuation')
        self.assertTrue(Path(publication['path']).exists())

    def test_source_corruption_fails_closed(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        self.record_path('RESPONSE', 'A1006').write_text('{')
        with self.assertRaises(ValueError):
            self.pump(instance)
        self.assertEqual(self.receipts('publication'), [])

    def test_request_started_before_phase_not_backfilled_after_sleep(self):
        self.step('A1006')
        self.step('A1006')
        instance = self.start()
        self.pump(instance)
        self.sleep('A1006')
        self.cycle('A1005')
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])

    def test_bounded_scan_never_dispatches_mid_catchup(self):
        instance = self.start(max_records_per_poll=1)
        self.pump(instance, count=20)
        self.all_cycles()
        report = instance.poll()
        self.assertLessEqual(report['records'], 1)
        self.assertEqual(self.receipts('publication'), [])
        self.pump(instance, count=60)
        self.assertEqual(len(self.receipts('publication')), 3)

    def test_partial_journal_tail_blocks_dispatch_without_modification(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        directory = self.children['A1007'] / 'stream/records'
        index = len([path for path in directory.glob('*.json') if not path.name.endswith('.intent.json')])
        partial = directory / f'{index:020d}.intent.json.partial'
        partial.write_text('{')
        self.pump(instance)
        self.assertEqual(self.receipts('publication'), [])
        self.assertEqual(partial.read_text(), '{')

    def test_total_and_per_poll_attempt_limits(self):
        instance = self.start(max_total_messages=2, max_messages_per_poll=1)
        self.pump(instance)
        self.all_cycles()
        reports = self.pump(instance)
        self.assertTrue(all(report['dispatch_attempts'] <= 1 for report in reports))
        self.assertEqual(len(self.receipts('publication')), 2)
        self.assertTrue(reports[-1]['total_limit_reached'])

    def test_wall_expiry_never_dispatches(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        with patch.object(pacing.time, 'time', return_value=self.deadline + 1):
            self.assertEqual(instance.poll()['status'], 'WALL_EXPIRED')
        self.assertEqual(self.receipts('publication'), [])

    def test_receiver_sleep_race_does_not_create_two_incoming_messages(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        original = relay.inbox_api._inbox
        raced = []
        def publish_after_sleep(root, *args, **kwargs):
            if root == self.children['A1005'] and not raced:
                raced.append(True)
                self.cycle('A1005')
            return original(root, *args, **kwargs)
        with patch.object(relay.inbox_api, '_inbox', side_effect=publish_after_sleep):
            self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.cycle('A1007')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        incoming = self.journals['A1005'].read_inbox()
        self.step('A1005', incoming=incoming)
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)
        self.step('A1005')
        self.sleep('A1005')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 2)

    def test_eligible_source_revalidated_immediately_before_publication(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        with patch.object(instance, '_send', return_value=0):
            self.pump(instance)
        reference = instance.eligible['A1006']['cadence_receipt']
        path = Path(reference['path'])
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'pacing_source_or_epoch_changed'):
            self.pump(instance)
        self.assertEqual(self.receipts('publication'), [])

    def test_waits_for_expected_sender_without_fallback_or_child_blocking(self):
        instance = self.start()
        self.pump(instance)
        self.cycle('A1005')
        self.cycle('A1007')
        self.pump(instance)
        self.assertEqual(self.publications('A1005'), [])
        self.assertEqual(len(self.streams['A1005'].rows), 2)
        self.cycle('A1006')
        self.pump(instance)
        self.assertEqual(len(self.publications('A1005')), 1)

    def test_inherited_receipts_count_against_unchanged_total_budget(self):
        self.cycle('A1006')
        with relay.ClassroomRelay(self.children, self.predecessor) as old:
            self.pump(old)
        instance = self.start(max_total_messages=2)
        self.pump(instance)
        self.all_cycles(consume=True)
        self.pump(instance)
        self.assertEqual(self.receipts('publication'), [])
        self.assertEqual(len(instance.attempted), 2)

    def test_predecessor_total_budget_cannot_be_extended(self):
        with self.assertRaisesRegex(ValueError, 'predecessor_total_budget_not_extended'):
            self.start(max_total_messages=1001)

    def test_predecessor_changes_during_phase_fail_before_publication(self):
        instance = self.start()
        self.pump(instance)
        self.all_cycles()
        (self.predecessor / ('intent_' + 'a' * 64 + '.partial')).write_text('{')
        with self.assertRaisesRegex(ValueError, 'predecessor_custody_unchanged_before_publication'):
            self.pump(instance)
        self.assertEqual(self.receipts('publication'), [])

    def test_same_or_nested_custody_and_symlink_receipts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'separate_phase_custody'):
            pacing.ReceiverSleepPacing(self.children, self.predecessor, self.predecessor,
                hard_end_unix=self.deadline)
        (self.predecessor / ('source_' + 'a' * 64 + '.json')).symlink_to(self.root / 'outside')
        with self.assertRaisesRegex(ValueError, 'bounded_regular_predecessor_receipts'):
            self.start()

    def test_incomplete_phase_is_not_reset(self):
        instance = self.start()
        instance.close()
        (self.state_dir / 'PHASE.partial').write_text('{')
        with self.assertRaisesRegex(ValueError, 'incomplete_phase_no_implicit_reset'):
            self.start()

    def test_cli_defaults_to_readonly_bootstrap_single_poll(self):
        arguments = ['--state-dir', str(self.state_dir), '--predecessor', str(self.predecessor),
            '--hard-end-unix', str(self.deadline)]
        for name, root in self.children.items():
            arguments += ['--child', name + '=' + str(root)]
        with patch('builtins.print'), patch.object(pacing.time, 'sleep') as sleeping:
            self.assertEqual(pacing.main(arguments), 0)
        sleeping.assert_not_called()
        self.assertEqual(self.receipts('publication'), [])


if __name__ == '__main__':
    unittest.main()
