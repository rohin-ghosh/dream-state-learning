import copy
import ast
import fcntl
import inspect
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r143_node5_allocator_handoff as handoff


class Node5AllocatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'stream/records').mkdir(parents=True)

    def documents(self, physical=2):
        programme, source, gpu_uuid = handoff.LANES[physical]
        plan = dict(physical=physical, root=str(handoff.BASE / programme / 'run1'),
            source_root=str(handoff.BASE / programme / source), gpu_uuid=gpu_uuid,
            hard_end_unix=1789617240.0, lease_end_unix=1789617840.0)
        config = dict(attempt_dir=str(self.root / 'old'), resume=False, plan_path='/saved/PLAN.json',
            plan_sha256='plan', hard_end_unix=plan['hard_end_unix'], next_reserved_unix=plan['lease_end_unix'],
            source_pins={'gpu/orch_r125_continual_guard.py': handoff.GUARD_SHA})
        return config, plan

    def publish(self, kind='SLEEP_COMPLETE', **changes):
        state = dict(pending=None, sleep_frontier=1, rows=[{'raw': '<|im_start|>'}],
            sleep_receipts=[{'status': 'COMPLETE'}], history=['unchanged'], carry=['unchanged'])
        state.update(changes)
        record = dict(kind=kind, document=dict(status='COMPLETE', cycle=1,
            resume_state=dict(state=state, sha256=handoff.digest(state))))
        record['sha256'] = handoff.digest(record)
        path = self.root / 'stream/records/00000000000000000000.json'
        path.write_text(json.dumps(record))
        return path, record

    def test_only_both_exact_original_lives(self):
        for physical in (2, 6):
            self.assertEqual(handoff.scope(*self.documents(physical)), physical)

    def test_other_lanes_rejected(self):
        for physical in (0, 1, 3, 4, 5, 7, True):
            config, plan = self.documents()
            plan['physical'] = physical
            with self.assertRaisesRegex(ValueError, 'only_original_node5_2_6'):
                handoff.scope(config, plan)

    def test_other_root_source_uuid_rejected(self):
        for field in ('root', 'source_root', 'gpu_uuid'):
            config, plan = self.documents()
            plan[field] += '_other'
            with self.assertRaisesRegex(ValueError, 'exact_original_life_source_UUID'):
                handoff.scope(config, plan)

    def test_no_new_containment_policy(self):
        config, plan = self.documents()
        config['device_containment'] = {'unit': 'new-policy'}
        with self.assertRaisesRegex(ValueError, 'original_guard_topology_only'):
            handoff.scope(config, plan)

    def test_wall_and_lease_must_not_change(self):
        for field in ('hard_end_unix', 'lease_end_unix'):
            config, plan = self.documents()
            plan[field] += 60
            with self.assertRaisesRegex(ValueError, 'original_wall_lease_reservation'):
                handoff.scope(config, plan)

    def test_guard_source_must_match_proven_environment(self):
        config, plan = self.documents()
        config['source_pins']['gpu/orch_r125_continual_guard.py'] = 'different'
        with self.assertRaisesRegex(ValueError, 'original_inherited_environment_guard'):
            handoff.scope(config, plan)

    def test_resume_changes_only_attempt_and_resume(self):
        config, unused = self.documents()
        original = copy.deepcopy(config)
        proposed = handoff.resume_config(config, self.root / 'new')
        self.assertEqual(config, original)
        self.assertTrue(proposed.pop('resume'))
        self.assertEqual(proposed.pop('attempt_dir'), str(self.root / 'new'))
        self.assertEqual(proposed, {key: value for key, value in config.items()
                                   if key not in ('resume', 'attempt_dir')})

    def test_existing_output_not_overwritten(self):
        config, unused = self.documents()
        with self.assertRaisesRegex(ValueError, 'unique_new_attempt'):
            handoff.resume_config(config, self.root)

    def test_allocator_is_only_environment_delta(self):
        environment = {'CUDA_VISIBLE_DEVICES': '', 'PYTHONPATH': '/original', 'OMP_NUM_THREADS': '1'}
        original = dict(environment)
        changed = handoff.allocator_environment(environment)
        self.assertEqual(changed.pop(handoff.ALLOCATOR_KEY), handoff.ALLOCATOR_VALUE)
        self.assertEqual(changed, original)
        self.assertEqual(environment, original)

    def test_existing_allocator_conflicts_rejected(self):
        for name in (handoff.ALLOCATOR_KEY, 'PYTORCH_ALLOC_CONF'):
            with self.assertRaisesRegex(ValueError, 'no_existing_allocator_override'):
                handoff.allocator_environment({name: ''})

    def test_completed_boundary_preserves_raw_history_carry(self):
        unused, record = self.publish()
        saved = handoff.sleep_boundary(self.root)
        self.assertEqual(saved['state'], record['document']['resume_state']['state'])
        self.assertEqual(saved['record_sha256'], record['sha256'])

    def test_busy_journal_never_requests_pause(self):
        for kind in ('REQUEST', 'RESPONSE', 'COMMITTED', 'UPDATE', 'SLEEP_REQUEST', 'INBOX', 'COMPACTION'):
            self.publish(kind=kind)
            self.assertIsNone(handoff.sleep_boundary(self.root))

    def test_pending_unslept_failed_state_rejected(self):
        for changes in ({'pending': {}}, {'sleep_frontier': 0}, {'sleep_receipts': []},
                        {'sleep_receipts': [{'status': 'FAILED'}]}):
            self.publish(**changes)
            with self.assertRaisesRegex(ValueError, 'no_pending_work_exact_sleep_boundary'):
                handoff.sleep_boundary(self.root)

    def test_tampered_record_rejected(self):
        path, record = self.publish()
        record['document']['cycle'] = 100
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'boundary_hash'):
            handoff.sleep_boundary(self.root)

    def test_unpublished_intent_not_boundary(self):
        self.publish()
        (self.root / 'stream/records/99999999999999999999.intent.json').write_text('pending')
        self.assertEqual(handoff.sleep_boundary(self.root)['cycle'], 1)

    def test_create_only_receipts(self):
        path = self.root / 'receipt.json'
        handoff.write(path, {'original': True})
        with self.assertRaises(FileExistsError):
            handoff.write(path, {'original': False})
        self.assertEqual(handoff.read(path), {'original': True})

    def test_symlink_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.root / 'elsewhere')
        with self.assertRaisesRegex(ValueError, 'no_symlinks'):
            handoff.regular(link)

    def test_pause_rejects_changed_identity_before_signal(self):
        with patch.object(handoff, 'identity', return_value={'pid': 123, 'start_ticks': 'new'}), \
                patch.object(handoff.signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(ValueError, 'identity_before_pause'):
                handoff.pause_exact({'pid': 123, 'start_ticks': 'old'}, 9)
            send.assert_not_called()

    def test_resume_exact_descriptors_reverse_order(self):
        paused = ['supervisor', 'timer', 'actor']
        with patch.object(handoff.signal, 'pidfd_send_signal') as send:
            handoff.resume_paused(paused, dict(supervisor=1, timer=2, actor=3))
        self.assertEqual([call.args for call in send.call_args_list],
                         [(3, signal.SIGCONT), (2, signal.SIGCONT), (1, signal.SIGCONT)])
        self.assertEqual(paused, [])

    def test_resume_survives_already_exited_process(self):
        paused = ['supervisor', 'actor']
        with patch.object(handoff.signal, 'pidfd_send_signal', side_effect=[ProcessLookupError(), None]) as send:
            handoff.resume_paused(paused, dict(supervisor=1, actor=2))
        self.assertEqual(send.call_count, 2)
        self.assertEqual(paused, [])

    def test_original_pair_identity_and_environment(self):
        config, plan = self.documents()
        path = '/old/GUARD.json'
        native = [str(handoff.PYTHON), '-B', '-m', handoff.GUARD, 'native', '--config', path]
        common = dict(uid=os.getuid(), cwd=plan['source_root'], cgroup='original', boot_id='boot')
        pair = dict(actor=dict(common, pid=3, parent=2, group=2, argv=native,
                              environment=['CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid']]),
            timer=dict(common, pid=2, parent=1, group=2, start_ticks='123',
                       argv=['timeout', '--signal=TERM', '--kill-after=5s', '900s'] + native,
                       environment=['CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid']]),
            supervisor=dict(common, pid=1, parent=0, group=1,
                argv=[str(handoff.PYTHON), '-B', '-m', handoff.GUARD, 'supervise', '--config', path],
                environment=['CUDA_VISIBLE_DEVICES=']))
        launch = dict(pid=2, parent_start_ticks='123', guard_sha256='guard', plan_sha256='plan', gpu_uuid=plan['gpu_uuid'])
        handoff.validate_pair(pair, path, config, plan, launch, 'guard')
        pair['actor']['parent'] = 8
        with self.assertRaisesRegex(ValueError, 'exact_ancestry'):
            handoff.validate_pair(pair, path, config, plan, launch, 'guard')

    def test_observer_time_is_bounded_before_side_effects(self):
        for seconds in (0, 1201, True):
            with self.assertRaisesRegex(ValueError, 'bounded_observer'):
                handoff.handoff(self.root, seconds)

    def consumed(self):
        unused, plan = self.documents()
        authorization = dict(new_deadline_unix=plan['hard_end_unix'], previous_deadline_unix=1,
            previous_stream_sha256='prior', lease_end_unix=plan['lease_end_unix'])
        plan['authorized_wall_extension'] = authorization
        state = dict(deadline_unix=plan['hard_end_unix'], history=['retained'])
        record = dict(index=3, kind='WALL_EXTENDED', document=dict(authorization=authorization,
            plan_sha256='original_plan', state=dict(state=state, sha256=handoff.digest(state))))
        record['sha256'] = handoff.digest(record)
        return plan, record

    def test_consumed_directive_omitted_without_changing_deadline_or_recipe(self):
        plan, record = self.consumed()
        original = copy.deepcopy(plan)
        proposed, proof = handoff.consumed_authorization_plan(plan, 'original_plan', [record], plan['hard_end_unix'])
        self.assertEqual(plan, original)
        self.assertEqual(dict(proposed, authorized_wall_extension=plan['authorized_wall_extension']), plan)
        self.assertFalse(proof['deadline_changed'])
        self.assertFalse(proof['training_changed'])

    def test_missing_applied_directive_never_removed(self):
        plan, unused = self.consumed()
        with self.assertRaisesRegex(ValueError, 'one_exact_already_applied_authorization'):
            handoff.consumed_authorization_plan(plan, 'original_plan', [], plan['hard_end_unix'])

    def test_duplicate_applied_authorization_rejected(self):
        plan, record = self.consumed()
        with self.assertRaisesRegex(ValueError, 'one_exact_already_applied_authorization'):
            handoff.consumed_authorization_plan(plan, 'original_plan', [record, record], plan['hard_end_unix'])

    def test_other_plan_authorization_rejected(self):
        plan, record = self.consumed()
        with self.assertRaisesRegex(ValueError, 'one_exact_already_applied_authorization'):
            handoff.consumed_authorization_plan(plan, 'different_plan', [record], plan['hard_end_unix'])

    def test_authorization_not_yet_in_current_state_rejected(self):
        plan, record = self.consumed()
        with self.assertRaisesRegex(ValueError, 'authorization_already_in_current_state'):
            handoff.consumed_authorization_plan(plan, 'original_plan', [record], 1)

    def test_corrupt_applied_authorization_rejected(self):
        plan, record = self.consumed()
        record['document']['state']['state']['deadline_unix'] = 3
        with self.assertRaisesRegex(ValueError, 'applied_authorization_record_hash'):
            handoff.consumed_authorization_plan(plan, 'original_plan', [record], plan['hard_end_unix'])

    def frozen_source(self):
        return (Path(__file__).resolve().parents[1] / 'research_loop/workers/'
                'r143_node5_allocator_20260916t1427z/FROZEN_NATIVE_BASELINE.py').read_text()

    def test_Main_exact_patch_preserves_original_encoder_and_other_AST(self):
        from gpu import orch_r144_target_patch as patcher
        source = self.frozen_source()
        patched = handoff.patch_frozen_native(source, patcher)
        self.assertIn('encode_sleep_targets(', patched)
        self.assertIn('runtime_policy=POLICY', patched)
        self.assertNotEqual(patched, source)

    def test_unknown_frozen_native_rejected(self):
        from gpu import orch_r144_target_patch as patcher
        with self.assertRaisesRegex(ValueError, 'exact_node5_frozen_native_bytes'):
            handoff.patch_frozen_native(self.frozen_source() + '\n', patcher)

    def test_already_patched_native_rejected(self):
        from gpu import orch_r144_target_patch as patcher
        patched = handoff.patch_frozen_native(self.frozen_source(), patcher)
        with self.assertRaisesRegex(ValueError, 'exact_node5_frozen_native_bytes'):
            handoff.patch_frozen_native(patched, patcher)

    def test_Main_patch_changes_cannot_escape_sleep(self):
        from gpu import orch_r144_target_patch as patcher
        original = patcher.patch_source
        with patch.object(patcher, 'patch_source', side_effect=lambda source: original(source) + '\nUNEXPECTED = 1\n'):
            with self.assertRaisesRegex(ValueError, 'all_non_sleep_AST_unchanged'):
                handoff.patch_frozen_native(self.frozen_source(), patcher)

    def test_startup_relocation_preserves_exact_bytes_and_hash(self):
        old_source, new_source = self.root / 'old_source', self.root / 'new_source'
        old_source.mkdir()
        new_source.mkdir()
        for source in (old_source, new_source):
            (source / 'STARTUP.md').write_text('unchanged startup\n')
        plan = dict(source_root=str(old_source), birth_prompt='unchanged startup\n',
            startup_context=dict(version='R127_STARTUP_V1', path=str(old_source / 'STARTUP.md'),
                                 sha256=handoff.sha(old_source / 'STARTUP.md')))
        original = copy.deepcopy(plan)
        proposed, proof = handoff.relocate_startup(plan, new_source)
        self.assertEqual(plan, original)
        self.assertEqual(proposed['startup_context']['path'], str(new_source / 'STARTUP.md'))
        self.assertEqual(proposed['startup_context']['sha256'], plan['startup_context']['sha256'])
        self.assertTrue(proof['prompt_bytes_unchanged'])

    def test_startup_relocation_rejects_changed_copied_text(self):
        old_source, new_source = self.root / 'old_source', self.root / 'new_source'
        old_source.mkdir()
        new_source.mkdir()
        (old_source / 'STARTUP.md').write_text('original')
        (new_source / 'STARTUP.md').write_text('changed')
        plan = dict(source_root=str(old_source), birth_prompt='original',
            startup_context=dict(path=str(old_source / 'STARTUP.md'), sha256=handoff.sha(old_source / 'STARTUP.md')))
        with self.assertRaisesRegex(ValueError, 'startup_bytes_and_rendered_prompt_unchanged'):
            handoff.relocate_startup(plan, new_source)

    def test_startup_absent_does_not_add_or_change_prompt(self):
        plan = dict(source_root='/old', birth_prompt='same')
        proposed, proof = handoff.relocate_startup(plan, Path('/new'))
        self.assertEqual(proposed, dict(source_root='/new', birth_prompt='same'))
        self.assertIsNone(proof)

    def reader_documents(self):
        config, plan = self.documents()
        plan.update(physical=7, root=str(handoff.BASE / 'orch_r136_repo_reader_20260916_attempt1/run1'),
            source_root=str(handoff.BASE / 'orch_r136_repo_reader_20260916_attempt1/source1'),
            gpu_uuid='GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b', hard_end_unix=1789596240.0)
        config['hard_end_unix'] = plan['hard_end_unix']
        return config, plan

    def test_reader_allowed_only_in_explicit_prospective_scope(self):
        config, plan = self.reader_documents()
        self.assertEqual(handoff.prospective_scope(config, plan), 7)
        with self.assertRaisesRegex(ValueError, 'only_original_node5_2_6'):
            handoff.scope(config, plan)

    def test_other_physical7_programme_rejected(self):
        config, plan = self.reader_documents()
        plan['root'] += '_different'
        with self.assertRaisesRegex(ValueError, 'exact_node5_repo_reader_only'):
            handoff.prospective_scope(config, plan)

    def test_reader_existing_earlier_wall_never_extended(self):
        config, plan = self.reader_documents()
        plan['hard_end_unix'] = config['hard_end_unix'] = 1789617240.0
        with self.assertRaisesRegex(ValueError, 'repo_reader_original_wall_lease'):
            handoff.prospective_scope(config, plan)

    def test_ready_lock_is_nonblocking_and_exclusive(self):
        path = self.root / 'node.lock'
        with path.open('a') as first, path.open('a') as second:
            self.assertTrue(handoff.try_ready_lock(first.fileno()))
            self.assertFalse(handoff.try_ready_lock(second.fileno()))
            fcntl.flock(first, fcntl.LOCK_UN)
            self.assertTrue(handoff.try_ready_lock(second.fileno()))

    def test_waiting_peer_does_not_block_ready_lane(self):
        peer = self.root / 'peer'
        peer.mkdir()
        handoff.write(peer / 'OBSERVER_ARMED.json', {'children_running': True})
        self.assertTrue(handoff.peers_safe([peer], self.root))

    def test_peer_quiescence_blocks_until_verified_loaded(self):
        peer = self.root / 'peer'
        peer.mkdir()
        handoff.write(peer / 'QUIESCENCE_STARTED.json', {})
        self.assertFalse(handoff.peers_safe([peer], self.root))
        actor = {'pid': 123, 'start_ticks': '456'}
        handoff.write(peer / 'LOADED_RECEIPT.json', {'actor': actor})
        with patch.object(handoff, 'identity', return_value=actor):
            self.assertTrue(handoff.peers_safe([peer], self.root))
        with patch.object(handoff, 'identity', return_value={'pid': 123, 'start_ticks': '789'}):
            self.assertFalse(handoff.peers_safe([peer], self.root))

    def test_peer_error_or_failed_load_blocks_other_retirement(self):
        for marker in ('FAILED.json', 'EXIT.json', 'ERROR_123.json', 'MONITOR_EXPIRED.json',
                       'BOUNDARY.json', 'RETIRED.json', 'DISPATCHED.json'):
            with self.subTest(marker=marker):
                peer = self.root / marker.replace('.', '_')
                peer.mkdir()
                handoff.write(peer / marker, {})
                self.assertFalse(handoff.peers_safe([peer], self.root))

    def predecessor_fixture(self):
        controls = [self.root / str(number) for number in (6, 2, 7)]
        for control in controls:
            control.mkdir()
        stopped = self.root / 'STOPPED.json'
        handoff.write(stopped, {'automatic_retry': False})
        handoff.write(controls[0] / 'WAIT_EXPIRED.json', {'status': 'NO_CLEAN_BOUNDARY_NO_RETIREMENT'})
        return controls, stopped

    def test_expired_pass_no_action_is_required_for_takeover(self):
        controls, stopped = self.predecessor_fixture()
        self.assertEqual(handoff.predecessor_no_action(controls, stopped)['status'],
                         'EXPIRED_WITHOUT_RETIREMENT')
        handoff.write(controls[1] / 'BOUNDARY.json', {})
        with self.assertRaisesRegex(ValueError, 'predecessor_action_started_no_takeover'):
            handoff.predecessor_no_action(controls, stopped)

    def test_predecessor_error_not_silently_retried(self):
        controls, stopped = self.predecessor_fixture()
        handoff.write(controls[0] / 'ERROR_123.json', {})
        with self.assertRaisesRegex(ValueError, 'predecessor_error_requires_diagnosis'):
            handoff.predecessor_no_action(controls, stopped)

    def test_handoff_lock_occurs_only_after_readonly_boundary_checks(self):
        tree = ast.parse(inspect.getsource(handoff.handoff))
        calls = [(node.lineno, ast.unparse(node.func)) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        first = lambda name: min(line for line, function in calls if function == name)
        self.assertLess(first('sleep_boundary'), first('try_ready_lock'))
        self.assertLess(first('readout_status'), first('try_ready_lock'))
        self.assertLess(first('try_ready_lock'), first('pause_exact'))
        self.assertLess(first('peers_safe'), first('pause_exact'))
        monitor = next(node for node in ast.walk(tree) if isinstance(node, ast.Call)
                       and ast.unparse(node.func) == 'monitor')
        self.assertTrue(any(item.arg == 'on_loaded' and ast.unparse(item.value) == 'release_lock'
                            for item in monitor.keywords))

    def test_monitor_releases_only_after_durable_loaded_receipt(self):
        tree = ast.parse(inspect.getsource(handoff.monitor))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        released = next(node for node in calls if ast.unparse(node.func) == 'on_loaded')
        loaded_write = next(node for node in calls if ast.unparse(node.func) == 'write'
                            and 'LOADED_RECEIPT.json' in ast.unparse(node.args[0]))
        self.assertLess(loaded_write.lineno, released.lineno)


if __name__ == '__main__':
    unittest.main()
