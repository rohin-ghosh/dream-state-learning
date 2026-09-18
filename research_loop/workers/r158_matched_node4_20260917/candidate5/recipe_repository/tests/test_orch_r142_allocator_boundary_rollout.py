import ast
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r142_allocator_boundary_rollout as rollout


class AllocatorRolloutTests(unittest.TestCase):
    def test_scope_excludes6_other_nodes_and_uuid_changes(self):
        plan = dict(physical=1, gpu_uuid=rollout.DEVICES[1], root=str(rollout.BASE / 'run'),
                    source_root=str(rollout.BASE / 'source'))
        self.assertEqual(rollout.scope(plan), 1)
        for changes in (dict(physical=5), dict(physical=6), dict(physical=True), dict(physical=8),
                        dict(gpu_uuid=rollout.DEVICES[0]), dict(root='/tmp/other')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                rollout.scope(dict(plan, **changes))

    def test_proposal_changes_only_resume_and_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = dict(attempt_dir=temporary, resume=False, source_pins={'native': 'sha'},
                       plan_path='/original/PLAN.json', lease_path='/original/LEASE.json')
            original = deepcopy(old)
            proposed = rollout.proposed_guard(old, Path(temporary) / 'attempt2')
            self.assertEqual(old, original)
            self.assertTrue(proposed.pop('resume'))
            proposed.pop('attempt_dir')
            self.assertEqual(proposed, {key: value for key, value in old.items()
                                       if key not in ('resume', 'attempt_dir')})
            with self.assertRaises(ValueError):
                rollout.proposed_guard(old, temporary)

    def test_allocator_is_inside_clean_containment_only(self):
        command = ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict',
                   '/usr/bin/env', '-i', 'CUDA_VISIBLE_DEVICES=original', 'python', '-B', '-m', 'original']
        changed = rollout.allocator_command(command)
        self.assertEqual(changed[6], rollout.ALLOCATOR)
        self.assertEqual(changed[:6] + changed[7:], command)
        for bad in (['env', 'python'], command + [rollout.ALLOCATOR],
                    command + ['PYTORCH_ALLOC_CONF=backend:cudaMallocAsync'],
                    command[:5] + command[6:], command[3:]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                rollout.allocator_command(bad)

    def test_reject_symlink_and_mutable_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'receipt.json'
            rollout.write(path, {'first': True})
            with self.assertRaises(FileExistsError):
                rollout.write(path, {'first': False})
            link = Path(temporary) / 'link'
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                rollout.read(link)

    def test_bounded_observer_and_wrong_host(self):
        for seconds in (0, 601, True):
            with self.assertRaisesRegex(ValueError, 'bounded_observation'):
                rollout.observe('/tmp/no', seconds, 2)
        with patch.object(rollout.socket, 'gethostname', return_value='other-node'), \
                self.assertRaisesRegex(ValueError, 'exact_ovx2_host'):
            rollout.inventory()

    def fixture(self, root, kind='SLEEP_COMPLETE', pending=None):
        checkpoint_root = root / 'checkpoints/sleep_000001'
        adapter = checkpoint_root / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter.bin').write_bytes(b'adapter')
        optimizer = checkpoint_root / 'optimizer_rng.pt'
        optimizer.write_bytes(b'AdamW + Python + CPU + CUDA RNG')
        files = {'adapter.bin': rollout.sha(adapter / 'adapter.bin')}
        checkpoint = dict(adapter_path=str(adapter), optimizer_rng_path=str(optimizer),
            adapter_files=files, checkpoint_sha256=dict(adapter=rollout.digest(files),
                optimizer=rollout.sha(optimizer), rng=rollout.sha(optimizer)), experiment={'same': True}, optimizer_steps=10)
        rollout.write(checkpoint_root / 'COMMIT.json', checkpoint)
        state = dict(pending=pending, sleep_frontier=1, rows=[{}], sleep_receipts=[{'status': 'COMPLETE'}],
                     experiment=checkpoint['experiment'], model_state_sha256=rollout.digest(checkpoint['checkpoint_sha256']),
                     history={'kept': True}, carry={'kept': True})
        record = dict(kind=kind, document=dict(status='COMPLETE', cycle=1, checkpoint=checkpoint,
                      resume_state=dict(state=state, sha256=rollout.digest(state))))
        record['sha256'] = rollout.digest(record)
        records = root / 'stream/records'
        records.mkdir(parents=True)
        rollout.write(records / ('0' * 20 + '.json'), record)
        guard = root / 'GUARD.json'
        rollout.write(guard, {})
        return dict(root=str(root), guard_path=str(guard), guard_sha256=rollout.sha(guard),
                    process={'pid': 123}, physical=1)

    def test_clean_boundary_observation_never_admits(self):
        with tempfile.TemporaryDirectory() as temporary:
            lane = self.fixture(Path(temporary))
            with patch.object(rollout, 'identity', return_value=lane['process']):
                result = rollout.boundary(lane)
            self.assertEqual(result['status'], 'OBSERVED_SAVED_BOUNDARY_NOT_ADMISSION')
            self.assertFalse(result['launch_ready'])
            self.assertFalse(result['full_journal_chain_verified'])

    def test_pending_and_unsaved_training_fail_closed(self):
        for kind, pending in (('UPDATE', None), ('SLEEP_COMPLETE', 'sleep:2'), ('REQUEST', 'generation')):
            with tempfile.TemporaryDirectory() as temporary:
                lane = self.fixture(Path(temporary), kind, pending)
                with patch.object(rollout, 'identity', return_value=lane['process']):
                    if kind == 'SLEEP_COMPLETE':
                        with self.assertRaisesRegex(ValueError, 'no_abandoned_pending_work'):
                            rollout.boundary(lane)
                    else:
                        self.assertEqual(rollout.boundary(lane)['status'], 'WAIT_NO_CLEAN_BOUNDARY')

    def test_tampered_optimizer_or_identity_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            lane = self.fixture(Path(temporary))
            with patch.object(rollout, 'identity', return_value={'pid': 124}), self.assertRaises(ValueError):
                rollout.boundary(lane)

    def test_boundary_moving_during_hashing_is_not_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            lane = self.fixture(Path(temporary))
            head = rollout.journal_head(temporary)
            with patch.object(rollout, 'identity', return_value=lane['process']), \
                    patch.object(rollout, 'journal_head', side_effect=[head, head.with_name('1' * 20 + '.json')]):
                self.assertEqual(rollout.boundary(lane)['status'], 'WAIT_MOVED_BOUNDARY')
            (Path(temporary) / 'checkpoints/sleep_000001/optimizer_rng.pt').write_bytes(b'tampered')
            with patch.object(rollout, 'identity', return_value=lane['process']), \
                    self.assertRaisesRegex(ValueError, 'AdamW_RNG_saved_bytes'):
                rollout.boundary(lane)

    def test_observer_path_has_no_signal_launch_or_journal_writer(self):
        tree = ast.parse(Path(rollout.__file__).read_text())
        for function in tree.body:
            if isinstance(function, ast.FunctionDef) and function.name in ('observe', 'inventory', 'boundary'):
                names = {node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute)}
                self.assertTrue(names.isdisjoint({'kill', 'killpg', 'pidfd_send_signal', 'Popen', 'system', 'record'}))

    def test_family_scope_exact_roots_and_recovery_denied(self):
        base = rollout.BASE / 'orch_r133_node3_brain_guided_20260916_attempt1'
        plan = dict(physical=3, gpu_uuid=rollout.DEVICES[3], root=str(base / 'run1'), source_root=str(base / 'source1'))
        self.assertEqual(rollout.family_scope(plan), 3)
        for changes in (dict(root=str(base / 'run2')), dict(source_root=str(base / 'source2')),
                        dict(physical=0, gpu_uuid=rollout.DEVICES[0]), dict(preupdate_recovery={'changed': True}),
                        dict(authorized_wall_extension={'changed': True})):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                rollout.family_scope(dict(plan, **changes))

    def test_resume_unit_only_policy_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            policy = dict(minor=3, uid=2524, gid=2524, unit='old-unit')
            old = dict(attempt_dir=temporary, resume=False, device_containment=policy, source_pins={'same': True})
            changed = rollout.resume_config(old, Path(temporary) / 'new')
            self.assertEqual(old['device_containment']['unit'], 'old-unit')
            self.assertNotEqual(changed['device_containment']['unit'], 'old-unit')
            self.assertEqual(dict(changed['device_containment'], unit='old-unit'), policy)
            self.assertEqual(changed['source_pins'], old['source_pins'])

    def test_admission_rejects_unclear_unprivileged_and_wrong_gpu(self):
        plan = dict(physical=3, gpu_uuid=rollout.DEVICES[3])
        report = dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu={'uuid': plan['gpu_uuid'], 'index': 3})
        rollout.admission(report, plan)
        for changes in (dict(clear=False), dict(scanner_euid=2524), dict(blocking_reasons=['foreign_fd']),
                        dict(gpu={'uuid': rollout.DEVICES[4], 'index': 3}),
                        dict(gpu={'uuid': plan['gpu_uuid'], 'index': 4})):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                rollout.admission(dict(report, **changes), plan)

    def test_pause_identity_drift_cannot_signal(self):
        with patch.object(rollout, 'process_record', return_value={'pid': 2}), \
                patch.object(rollout.signal, 'pidfd_send_signal') as sending, self.assertRaises(ValueError):
            rollout.pause_exact({'pid': 1}, 77)
        sending.assert_not_called()

    def test_failure_restores_only_exact_pidfds(self):
        paused = ['supervisor', 'timer', 'actor']
        descriptors = dict(supervisor=71, timer=72, actor=73)
        with patch.object(rollout.signal, 'pidfd_send_signal') as sending:
            rollout.resume_paused(paused, descriptors)
        self.assertEqual([call.args[0] for call in sending.call_args_list], [73, 72, 71])
        self.assertEqual(paused, [])

    def test_missing_containment_cannot_be_added(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaisesRegex(ValueError, 'existing_containment'):
            rollout.resume_config(dict(attempt_dir=temporary, resume=False), Path(temporary) / 'new')

    def test_handoff_never_uses_process_groups_or_SIGKILL(self):
        tree = ast.parse(Path(rollout.__file__).read_text())
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertTrue(names.isdisjoint({'kill', 'killpg', 'SIGKILL', 'rmtree'}))

    def test_monitor_timeout_does_not_signal(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            plan = output / 'PLAN.json'
            rollout.write(plan, {'root': temporary})
            rollout.write(output / 'GUARD.json', {'plan_path': str(plan)})
            rollout.write(output / 'STAGED.json', {'new_config_sha256': rollout.sha(output / 'GUARD.json')})
            with patch.object(rollout.signal, 'pidfd_send_signal') as sending, self.assertRaisesRegex(ValueError, 'monitor_expired'):
                rollout.monitor_success(output, {}, '0000', seconds=0)
            sending.assert_not_called()
            self.assertFalse(rollout.read(output / 'MONITOR_TIMEOUT.json')['stopped'])

    def test_monitor_validated_loaded_releases_lane_before_next_sleep(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            plan = output / 'PLAN.json'
            rollout.write(plan, {'root': temporary})
            rollout.write(output / 'GUARD.json', {'plan_path': str(plan)})
            rollout.write(output / 'STAGED.json', {'new_config_sha256': rollout.sha(output / 'GUARD.json')})
            receipt = output / 'RAW_LOADED.json'
            rollout.write(receipt, {'kept': True})
            saved = dict(optimizer_steps=858, adapter_state_sha256='adapter')
            rollout.write(output / 'LOADED_RECEIPT.json', dict(record_path=str(receipt), record_sha256=rollout.sha(receipt),
                actor={'pid': 99}, **saved))
            called = []
            with patch.object(rollout, 'identity', return_value={'pid': 99}), self.assertRaisesRegex(ValueError, 'monitor_expired'):
                rollout.monitor_success(output, saved, '0000', seconds=0, on_loaded=lambda: called.append(True))
            self.assertEqual(called, [True])

    def test_monitor_wrong_loaded_identity_never_releases_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            plan = output / 'PLAN.json'
            rollout.write(plan, {'root': temporary})
            rollout.write(output / 'GUARD.json', {'plan_path': str(plan)})
            rollout.write(output / 'STAGED.json', {'new_config_sha256': rollout.sha(output / 'GUARD.json')})
            receipt = output / 'RAW_LOADED.json'
            rollout.write(receipt, {})
            rollout.write(output / 'LOADED_RECEIPT.json', dict(record_path=str(receipt), record_sha256=rollout.sha(receipt), actor={'pid': 99}))
            called = []
            with patch.object(rollout, 'identity', return_value={'pid': 100}), self.assertRaisesRegex(ValueError, 'resume_monitor_verified'):
                rollout.monitor_success(output, {}, '0000', seconds=0, on_loaded=lambda: called.append(True))
            self.assertEqual(called, [])

    def test_readmission_only_after_denial_and_bound_retirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            prior = Path(temporary)
            rollout.write(prior / 'BOUNDARY.json', {'exact': True})
            rollout.write(prior / 'RETIRED.json', dict(status='EXACT_OLD_PROCESSES_EXITED',
                          boundary_sha256=rollout.sha(prior / 'BOUNDARY.json')))
            rollout.write(prior / 'ADMISSION.json', {'clear': False})
            rollout.write(prior / 'SUPERVISOR_FAILED.json', {'denied': True})
            rollout.admission_retry_eligible(prior)
            (prior / 'BOUNDARY.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'retirement_boundary_binding'):
                rollout.admission_retry_eligible(prior)

    def test_readmission_never_retries_dispatched_native(self):
        for name in ('LAUNCH.json', 'CONTAINED_COMMAND.json', 'ADMISSION_TIME.json'):
            with tempfile.TemporaryDirectory() as temporary:
                prior = Path(temporary)
                rollout.write(prior / name, {})
                with self.assertRaisesRegex(ValueError, 'before_any_native_dispatch'):
                    rollout.admission_retry_eligible(prior)


if __name__ == '__main__':
    unittest.main()
