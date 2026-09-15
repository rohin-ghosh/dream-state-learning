from copy import deepcopy
from contextlib import nullcontext
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_continual_exhaustion_keyed_runtime as runtime
from tests import test_orch_continual_exhaustion_publish as fixtures


class KeyedContinuationTests(unittest.TestCase):
    def fixture(self):
        row, review = fixtures.ExhaustionPublisherTests().fixture()
        packet = [dict(target_sha256=row['target_sha256'],
            raw_call_sha256=row['provenance']['raw_call_sha256'], student_prefix_sha256=row['student_prefix_sha256'],
            target_source_lines=runtime.old.policy.source_lines(row['target']), gold=row['gold'],
            question='What is 2+3?', student_prefix=[dict(role='user', content='What is 2+3?')])]
        keyed = {name: value for name, value in review.items() if name not in runtime.keyed.HASH_FIELDS}
        keyed['row_key'] = 0
        return packet, dict(reviews=[keyed])

    def config_allocation(self):
        config = dict(predecessor=dict(pid=123, uid=456, start_ticks=789, boot_id='boot'), native_root='/native/shared')
        allocation = dict(approved_by='MAIN', scope=runtime.SCOPE, dispatch_authorized=True,
            config_sha256='a' * 64, deadline_unix=runtime.DEADLINE, dispatch_cutoff_unix=runtime.CUTOFF,
            old_reserved_preserved=96, shared_limit=128, aggregate_allocation_ceiling=256,
            predecessor=config['predecessor'], native_root=config['native_root'], allocation_id='main_scoped_v1',
            quiescent_native_state_sha256='b' * 64)
        return config, allocation

    def test_allocation_not_inferred_from_cpu_readiness(self):
        config, allocation = self.config_allocation()
        for changes in [dict(approved_by='builder'), dict(dispatch_authorized=False), dict(scope='CPU_READY'),
                        dict(shared_limit=256), dict(old_reserved_preserved=0), dict(config_sha256='c' * 64),
                        dict(deadline_unix=runtime.DEADLINE + 1)]:
            with self.assertRaises(ValueError):
                runtime.validate_allocation(dict(allocation, **changes), config, 'a' * 64, runtime.CUTOFF - 1)

    def test_bounded_post_cutoff_drain_not_new_allocation(self):
        config, allocation = self.config_allocation()
        runtime.validate_allocation(allocation, config, 'a' * 64, runtime.CUTOFF + 1)
        with self.assertRaises(ValueError):
            runtime.validate_allocation(allocation, config, 'a' * 64, runtime.DEADLINE)

    def test_host_key_mapping_retains_semantics_without_mutating_result(self):
        packet, result = self.fixture()
        before = deepcopy(result)
        reviews = runtime.validate_result(packet, result, runtime.digest(packet))
        self.assertEqual(reviews[0]['target_sha256'], packet[0]['target_sha256'])
        self.assertEqual(reviews[0]['status'], result['reviews'][0]['status'])
        self.assertEqual(result, before)

    def test_no_recursion_when_old_finalizer_uses_keyed_override(self):
        packet, result = self.fixture()
        with patch.object(runtime.old, 'validate_reviews', side_effect=AssertionError('mutable delegate used')):
            self.assertEqual(len(runtime.validate_result(packet, result, runtime.digest(packet))), 1)

    def test_duplicate_unknown_boolean_and_missing_keys_fail(self):
        packet, result = self.fixture()
        for key in (True, '0', 1, -1, None):
            bad = deepcopy(result)
            bad['reviews'][0]['row_key'] = key
            with self.assertRaises(ValueError):
                runtime.validate_result(packet, bad, runtime.digest(packet))
        for reviews in ([], result['reviews'] * 2):
            with self.assertRaises(ValueError):
                runtime.validate_result(packet, dict(reviews=reviews), runtime.digest(packet))

    def test_old_hash_response_cannot_be_salvaged(self):
        packet, result = self.fixture()
        for field in runtime.keyed.HASH_FIELDS:
            bad = deepcopy(result)
            bad['reviews'][0][field] = packet[0][field]
            with self.assertRaisesRegex(ValueError, 'model_hash_fields_forbidden'):
                runtime.validate_result(packet, bad, runtime.digest(packet))

    def test_question_prefix_gold_and_target_registry_cannot_change(self):
        packet, result = self.fixture()
        for key in ('question', 'gold', 'student_prefix_sha256', 'raw_call_sha256'):
            changed = deepcopy(packet)
            changed[0][key] = 'changed'
            with self.assertRaisesRegex(ValueError, 'immutable_full_packet_mismatch'):
                runtime.validate_result(changed, result, runtime.digest(packet))

    def test_fulltext_evidence_and_gold_acceptance_unchanged(self):
        packet, result = self.fixture()
        for changes in [dict(full_text_read=False), dict(evidence_line_ids=[99999]),
                        dict(independent_answer='6'), dict(grounded_operations=False)]:
            changed = deepcopy(result)
            changed['reviews'][0].update(changes)
            with self.assertRaises(ValueError):
                runtime.validate_result(packet, changed, runtime.digest(packet))

    def test_model_packet_has_no_hashes_but_exact_source_text(self):
        packet, unused = self.fixture()
        packets = packet * 6
        projected = runtime.model_packet(packets)
        self.assertEqual([row['row_key'] for row in projected], list(range(6)))
        self.assertEqual(projected[0]['target_source_lines'], packet[0]['target_source_lines'])
        self.assertEqual(projected[0]['student_prefix'], packet[0]['student_prefix'])
        self.assertFalse(set(runtime.keyed.HASH_FIELDS) & set(projected[0]))

    def test_exact_shared_pool_advances_without_reset(self):
        for reserved in (4, 6, 20, 126):
            state = dict(reserved=reserved, limit=128, old_reserved=96)
            updated = runtime.old.reserve_budget(state, runtime.DEADLINE, runtime.CUTOFF - 1)
            self.assertEqual(updated['reserved'], reserved + 2)
            self.assertEqual(state['reserved'], reserved)
        with self.assertRaises(ValueError):
            runtime.old.reserve_budget(dict(reserved=128, limit=128, old_reserved=96), runtime.DEADLINE, runtime.CUTOFF - 1)

    def test_cutoff_and_original96_remain_fixed(self):
        for state, now in [(dict(reserved=6, limit=128, old_reserved=96), runtime.CUTOFF),
                           (dict(reserved=6, limit=128, old_reserved=0), runtime.CUTOFF - 1)]:
            with self.assertRaises(ValueError):
                runtime.old.reserve_budget(state, runtime.DEADLINE, now)

    def test_quiescence_binds_current_not_stale_four_call_state(self):
        state = dict(budget=dict(reserved=6), pending_reserved_batches=[])
        scan = dict(active=[], unreadable_pids=[])
        allocation = dict(quiescent_native_state_sha256=runtime.digest(state))
        runtime.assert_quiescent(state, scan, allocation)
        for changed in [dict(state, budget=dict(reserved=4)), dict(state, pending_reserved_batches=[54])]:
            with self.assertRaises(ValueError):
                runtime.assert_quiescent(changed, scan, allocation)
        for changed in [dict(scan, active=[dict(pid=1)]), dict(scan, unreadable_pids=[1])]:
            with self.assertRaises(ValueError):
                runtime.assert_quiescent(state, changed, allocation)

    def test_predecessor_live_means_no_lock_or_signal(self):
        config, unused = self.config_allocation()
        with patch.object(runtime, 'identity', return_value=config['predecessor']), patch.object(runtime.os, 'kill') as kill:
            with self.assertRaisesRegex(ValueError, 'predecessor_still_running'):
                runtime.take_old_lock(config)
            kill.assert_not_called()

    def test_original_lock_inode_and_exclusive_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'CONTROLLER.lock'
            path.touch()
            config, unused = self.config_allocation()
            config.update(predecessor_runtime=directory, predecessor_lock_inode=[path.stat().st_dev, path.stat().st_ino])
            with patch.object(runtime, 'identity', return_value=None), patch.object(runtime, 'worker_scan', return_value=dict(active=[], unreadable_pids=[])):
                held = runtime.take_old_lock(config)
                try:
                    with self.assertRaises(BlockingIOError):
                        runtime.take_old_lock(config)
                finally:
                    held.close()
                config['predecessor_lock_inode'][1] += 1
                with self.assertRaisesRegex(ValueError, 'original_lock_inode'):
                    runtime.take_old_lock(config)

    def test_failure_classification_does_not_call_hash_mismatch_http(self):
        result = runtime.failure(ValueError('review_hash_mismatch'))
        self.assertEqual(result['stage'], 'RESPONSE_OR_BINDING_VALIDATION')
        self.assertEqual(result['reason'], 'review_hash_mismatch')
        self.assertNotIn('secret', json.dumps(runtime.failure(ValueError('secret body text'))))

    def test_r106_addendum_separates_terminal_checks_and_methods_without_threshold(self):
        self.assertIn('terminal check is not mid-solution', runtime.R106_ADDENDUM)
        self.assertIn('No new branch, method, length, first-person', runtime.R106_ADDENDUM)
        self.assertIn('UNKNOWN', runtime.R106_ADDENDUM)

    def test_no_shutdown_or_old_guard_reset_in_runtime(self):
        source = Path(runtime.__file__).read_text()
        self.assertNotIn('os.kill(', source)
        self.assertNotIn('old.vm_watch(', source)
        self.assertNotIn('old.guard_controller(', source)
        self.assertIn('timeout=310', source)
        self.assertIn('ThreadPoolExecutor(max_workers=2', source)


class NativeLedgerSnapshotTests(unittest.TestCase):
    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def fixture(self, root):
        for name in runtime.FROZEN:
            self.write(root / name, {})
        self.write(root / 'BUDGET.json', dict(reserved=4, limit=128, old_reserved=96))
        self.write(root / 'SEEN.json', ['a', 'b'])
        for number in (0, 1):
            batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
            self.write(batch / 'REVIEW_RESERVATION.json', dict(calls=[number * 2 + 1, number * 2 + 2]))
            self.write(batch / 'PROVIDER_UPLOAD_VERIFIED.json', dict(verified=True))
            self.write(batch / 'RESULT_REDUCTION.json', dict(all_adjudicated_sample_pass_sha256s=['a'],
                accepted_sample_pass_sha256s=[], admitted_target_sha256s=[]))
        (root / 'orch_continual_exhaustion_feed_batch_048').mkdir()

    def test_readonly_snapshot_inherits_counters_seen_and_next_unused_number(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime.old, 'verify_native'):
            root = Path(directory)
            self.fixture(root)
            before = {str(path): path.read_bytes() for path in root.rglob('*.json')}
            state = runtime.native_state(root)
            self.assertEqual(state['next_number'], 49)
            self.assertEqual(state['all_sample_pass'], ['a'])
            self.assertEqual(state['accepted_sample_pass'], [])
            self.assertEqual(state['budget']['reserved'], 4)
            self.assertEqual(before, {str(path): path.read_bytes() for path in root.rglob('*.json')})

    def test_partial_reserved_batch_blocks_quiescent_handoff(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime.old, 'verify_native'):
            root = Path(directory)
            self.fixture(root)
            (root / 'orch_continual_exhaustion_feed_batch_001/RESULT_REDUCTION.json').unlink()
            state = runtime.native_state(root)
            self.assertEqual(state['pending_reserved_batches'], [1])

    def test_missing_charged_history_fails_instead_of_reset(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime.old, 'verify_native'):
            root = Path(directory)
            self.fixture(root)
            self.write(root / 'BUDGET.json', dict(reserved=6, limit=128, old_reserved=96))
            with self.assertRaisesRegex(ValueError, 'complete_charged_reservation_history'):
                runtime.native_state(root)


class ControllerDryRunTests(unittest.TestCase):
    def test_one_mock_batch_preserves_counters_and_final_two_slots(self):
        with tempfile.TemporaryDirectory(prefix='orch_continual_exhaustion_keyed_runtime_test_') as directory:
            root = Path(directory)
            prior = root / 'prior'
            prior.mkdir()
            terminal = prior / 'OLD_TERMINAL.json'
            runtime.write_once(terminal, dict(reserved=96))
            runtime.write_once(prior / 'CONFIG.json', dict(old_terminal_path=str(terminal), old_terminal_sha256=runtime.sha(terminal)))
            base = ('Copy all hashes exactly and\nreturn every supplied row once.\n'
                'has_meaningful_branch measures whether a consequential alternative was actually\nexamined and evaluated, not merely mentioned.\n'
                'Keep has_meaningful_branch as the legacy alternative/rejection measurement, not a two-method claim.')
            (root / 'REVIEW_INSTRUCTIONS.md').write_text(base)
            state = dict(budget=dict(reserved=126), next_number=55, pending_reserved_batches=[],
                all_sample_pass=['old-pass'], accepted_sample_pass=[], admitted_targets=[])
            config = dict(vm_runtime=str(root), reductions=str(root / 'reductions'),
                predecessor_runtime=str(prior), predecessor_config_sha256=runtime.sha(prior / 'CONFIG.json'),
                predecessor={}, predecessor_lock_inode=[1, 2], original_publisher_started_unix=1)
            allocation = dict(quiescent_native_state_sha256=runtime.digest(state))
            packet, unused = KeyedContinuationTests().fixture()
            packets = [packet * 6, packet * 6]
            events = []

            class FakeTransport:
                def __init__(self, *args):
                    pass

                def rpc(self, phase, number=None):
                    events.append(phase)
                    if phase == 'inspect':
                        return dict(state=state, workers=dict(active=[], unreadable_pids=[]))
                    if phase == 'claim':
                        return state
                    if phase == 'prepare':
                        return dict(native_batch_path='/native/batch55', packets=packets)
                    if phase == 'reserve':
                        return dict(reserved=128, limit=128, old_reserved=96)
                    if phase == 'verify_upload':
                        path = root / 'review_batch_055/review_workspace/UPLOAD_INVENTORY.json'
                        return dict(verified=True, inventory_sha256=runtime.sha(path))
                    if phase == 'finalize':
                        return dict(decision=dict(accepted=False), all_adjudicated_sample_pass_sha256s=['new-pass'],
                            accepted_sample_pass_sha256s=[], admitted_target_sha256s=[])
                    raise AssertionError(phase)

                def review(self, number, group, path):
                    events.append(('MOCK_NOT_PROVIDER', group))

                def ssh(self, command):
                    pass

                def upload(self, source, destination):
                    pass

            with patch.object(runtime, 'Transport', FakeTransport), patch.object(runtime, 'take_old_lock', return_value=nullcontext()), \
                    patch.object(runtime.time, 'time', return_value=runtime.CUTOFF - 100), \
                    patch.object(runtime.subprocess, 'run', side_effect=AssertionError('no real subprocess in dry run')):
                runtime.run(config, root / 'CONFIG.json', allocation, root / 'ALLOCATION.json', 'a' * 64)
            status = runtime.read(root / 'reductions/LIVE_STATUS.json')
            self.assertEqual(status['reserved'], 128)
            self.assertEqual(status['counts']['all_sample_pass'], 2)
            self.assertEqual(status['counts']['admitted_targets'], 0)
            self.assertEqual(sum(isinstance(event, tuple) for event in events), 2)
            self.assertFalse((root / 'review_batch_055').exists())
            self.assertEqual(runtime.read(root / 'reductions/WATCH_TERMINAL.json')['reserved'], 128)


if __name__ == '__main__':
    unittest.main()
