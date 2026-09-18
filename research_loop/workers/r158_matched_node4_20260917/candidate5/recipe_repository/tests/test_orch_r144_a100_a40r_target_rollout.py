from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r144_a100_a40r_target_rollout as rollout
from gpu import orch_r144_target_patch as target_patch


class StrictKernel4Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name)/'strict.py'
        self.source = rollout.strict_kernel4_source(Path('gpu/orch_r137_node4_containment.py').read_text())
        path.write_text(self.source)
        self.handler = rollout.module_from_file('r144_strict_test', path)

    def test_exact_handler_narrowed_to_kernel4_only(self):
        self.assertEqual(self.handler.DEVICES, {4:rollout.LANES['a40r'][4][1]})
        command = self.handler.device_containment_command(4,7,1395,1395,'orch-r136-native-'+'a'*32,
            '/tmp/isolated',['ordinary','native'],600)
        self.assertIn('--property=DevicePolicy=strict',command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia7 rw',command)
        self.assertIn('/usr/bin/env',command)
        self.assertIn('-i',command)
        for minor in range(7):
            self.assertNotIn('--property=DeviceAllow=/dev/nvidia'+str(minor)+' rw',command)
        with self.assertRaisesRegex(ValueError,'explicit_NODE4_physical'):
            self.handler.device_containment_command(3,0,1395,1395,'orch-r136-native-'+'a'*32,
                '/tmp/isolated',['native'],600)

    def test_original_all_seven_denials_preserved(self):
        policy = dict(uid=1395,gid=1395,minor=7,unit='orch-r136-native-'+'a'*32)
        with patch.object(self.handler,'require_host'), patch.object(self.handler.os,'getuid',return_value=1395), \
                patch.object(self.handler.os,'getgid',return_value=1395), \
                patch.object(Path,'read_text',return_value='0::/system.slice/'+policy['unit']+'.service'), \
                patch.object(self.handler,'device_minor',return_value=7), patch.object(self.handler,'gpu_descriptors',return_value=[]), \
                patch.object(self.handler.os,'open',side_effect=PermissionError) as opening, \
                patch.dict(os.environ,CUDA_VISIBLE_DEVICES=rollout.LANES['a40r'][4][1]):
            receipt = self.handler.verify_device_containment(dict(device_containment=policy),dict(gpu_uuid=rollout.LANES['a40r'][4][1]))
        self.assertEqual(receipt['denied_foreign_minors'],list(range(7)))
        self.assertEqual(opening.call_count,7)

    def test_unknown_donor_refused(self):
        with self.assertRaisesRegex(ValueError,'exact_original_R137_handler'):
            rollout.strict_kernel4_source(self.source)


class LegacyContractTests(unittest.TestCase):
    def setUp(self):
        name, gpu_uuid = rollout.LANES['a40r'][0]
        self.plan = dict(physical=0, root=str(rollout.BASE/name/'run1'), gpu_uuid=gpu_uuid,
            source_root='/original/source', context_limit=32768, segment_tokens=512, segments_per_sleep=2)
        self.state = dict(presentation=None, context_limit=32768, segment_tokens=512, segments_per_sleep=2,
                          pending=None, sleep_frontier=2, rows=[{},{}])
        self.checkpoint = dict.fromkeys(['adapter_files','adapter_path','adapter_state_sha256','base_sha256',
            'checkpoint_sha256','created_unix','optimizer_rng_path','optimizer_steps','schema'])
        self.payload = dict.fromkeys(['optimizer','parameter_names','optimizer_steps','cpu_rng','cuda_rng','python_rng'])

    def test_known_legacy_sources_only(self):
        with patch.object(rollout, 'sha', side_effect=[rollout.LEGACY_NATIVE[0],rollout.LEGACY_STREAM_SHA]):
            self.assertEqual(rollout.checkpoint_contract(self.plan, SimpleNamespace()), 'PINNED_LEGACY_FIXED_RANK8')
        with patch.object(rollout, 'sha', return_value='unknown'):
            with self.assertRaisesRegex(ValueError, 'no_generic_skip'):
                rollout.checkpoint_contract(self.plan, SimpleNamespace())

    def test_legacy_exact_schema_and_no_fabricated_experiment(self):
        rollout.verify_saved_schema('PINNED_LEGACY_FIXED_RANK8', self.plan, self.state, self.checkpoint, self.payload)
        with self.assertRaisesRegex(ValueError, 'legacy_no_invented_experiment'):
            rollout.verify_saved_schema('PINNED_LEGACY_FIXED_RANK8', self.plan, self.state,
                                        dict(self.checkpoint, experiment=None), self.payload)

    def test_legacy_refuses_context_change_and_pending_work(self):
        for change in (dict(context_limit=8192), dict(pending='sleep:old'),dict(segments_per_sleep=1)):
            with self.assertRaisesRegex(ValueError, 'unchanged_legacy'):
                rollout.verify_saved_schema('PINNED_LEGACY_FIXED_RANK8', self.plan,
                    dict(self.state, **change), self.checkpoint, self.payload)

    def test_modern_experiment_mismatch_still_fatal(self):
        with self.assertRaisesRegex(ValueError, 'saved_experiment_triplet'):
            rollout.verify_saved_schema('EXPLICIT_EXPERIMENT', {}, {'experiment':'one'},
                                         {'experiment':'two'}, {'experiment':'two'})

    def test_kernel4_requires_exact_coordinated_recovery_release(self):
        plan = dict(self.plan, physical=4, source_root=str(rollout.BASE/rollout.LANES['a40r'][4][0]/'source_r144_kernel4_20260916t1510z'))
        with patch.object(Path, 'exists', return_value=True), patch.object(rollout, 'sha', side_effect=[
            'cfbcbf82465679cdf63bab97cdbc645755a2230fa13332945e158151756d017e',
            'e119eb67d9986761a7d471f490676db7c8384efa78e69f69e2cd4b150b1bd1f9']):
            self.assertTrue(rollout.kernel4_released(plan))
        with patch.object(Path, 'exists', return_value=True), patch.object(rollout, 'sha', return_value='wrong'):
            self.assertFalse(rollout.kernel4_released(plan))

    def test_recovered_kernel4_successor_never_one_shot_entry(self):
        with patch.object(rollout, 'kernel4_released', return_value=True):
            self.assertEqual(rollout.original_entry_module('a40r', {'physical':4}), 'gpu.orch_r144_kernel4_recovery')
        request = dict(handler=rollout.launcher('a40r', {}), new_config='/isolated/GUARD.json')
        command = rollout.launch_command(request)
        self.assertIn(rollout.GUARD, command)
        self.assertNotIn('gpu.orch_r144_kernel4_recovery', command)

    def test_only_exact_recorded_node_dependency_allowed(self):
        request = dict(node='a40r',physical=4)
        hold = dict(stage='/own/root/lane3')
        report = dict(clear=False,scanner_euid=0,blocking_reasons=['open_device_pid:1753623'])
        checksum = '81412f3372fbb301a931bbb844d8565d7d10bbdf232a606bc31ea8d2efd83969'
        rollout.validate_node_dependency(request,hold,report,checksum,False,True)
        for changed in (dict(node='a100',physical=4),dict(node='a40r',physical=1)):
            with self.assertRaisesRegex(ValueError, 'only_released_kernel4_dependency'):
                rollout.validate_node_dependency(changed,hold,report,checksum,False,True)

    def test_node_dependency_cannot_clear_admission_or_partial_load(self):
        request = dict(node='a40r',physical=4)
        hold = dict(stage='/own/root/lane3')
        report = dict(clear=False,scanner_euid=0,blocking_reasons=['open_device_pid:1753623'])
        checksum = '81412f3372fbb301a931bbb844d8565d7d10bbdf232a606bc31ea8d2efd83969'
        for checksum_value,launched,released in [('wrong',False,True),(checksum,True,True),(checksum,False,False)]:
            with self.assertRaises(ValueError):
                rollout.validate_node_dependency(request,hold,report,checksum_value,launched,released)


class ReadmissionTests(unittest.TestCase):
    def setUp(self):
        self.readmit = rollout.module_from_file('r144_test_readmit', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/READMIT_A1004.py').absolute())
        self.denial = dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:4583'])

    def test_fresh_readmission_only_exact_preload_denial(self):
        self.readmit.denied_preload(self.denial, False)
        with self.assertRaisesRegex(ValueError, 'never_retry_partially_launched_native'):
            self.readmit.denied_preload(self.denial, True)

    def test_refuse_foreign_GPU_and_unprivileged_denial(self):
        for change in (dict(blocking_reasons=['open_device_pid:123']), dict(scanner_euid=1000), dict(clear=True)):
            with self.assertRaises(ValueError):
                self.readmit.denied_preload(dict(self.denial, **change), False)

    def test_readmission_only_changes_control_and_unit(self):
        old = dict(attempt_dir='old', device_containment=dict(unit='old',minor=7,uid=1395,gid=1395),
                   source_pins={'a':'unchanged'},plan_path='same',plan_sha256='same',lease_path='same',resume=True)
        new = self.readmit.derived_config(old, Path('/new/control'))
        self.assertNotEqual(new['device_containment']['unit'], old['device_containment']['unit'])
        new['device_containment']['unit'] = old['device_containment']['unit']
        new['attempt_dir'] = old['attempt_dir']
        self.assertEqual(new, old)


class DependentReadmissionTests(unittest.TestCase):
    def setUp(self):
        self.helper = rollout.module_from_file('r144_test_readmit3', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/READMIT_A40R3.py').absolute())
        self.receipt = dict(status='APPLIED_AND_NEW_GENERATION_COMMITTED', node='a40r', physical=4)
        self.containment = dict(policy=dict(minor=7), denied_foreign_minors=list(range(7)))

    def test_dependency_requires_committed_strict4_and_exact_fd_set(self):
        self.helper.check_dependency(self.receipt, self.containment, {7}, False)
        for minors in ({0, 7}, set(), {4}):
            with self.assertRaisesRegex(ValueError, 'actual_fds_only_minor7'):
                self.helper.check_dependency(self.receipt, self.containment, minors, False)

    def test_cannot_readmit_while_old_blocker_lives(self):
        with self.assertRaisesRegex(ValueError, 'foreign_holder_must_exit'):
            self.helper.check_dependency(self.receipt, self.containment, {7}, True)

    def test_no_partial_dependency_or_wrong_lane(self):
        for change in (dict(status='LOADED'), dict(physical=3), dict(node='a100')):
            with self.assertRaisesRegex(ValueError, 'new_committed_required'):
                self.helper.check_dependency(dict(self.receipt, **change), self.containment, {7}, False)
        with self.assertRaisesRegex(ValueError, 'seven_denials_required'):
            self.helper.check_dependency(self.receipt, dict(policy=dict(minor=7), denied_devices=[0]), {7}, False)

    def test_exact_foreign_denial_not_transient_retry_exception(self):
        denial = dict(clear=False, scanner_euid=0, blocking_reasons=['open_device_pid:1753623'])
        self.helper.denied_preload(denial, False)
        for change in (dict(blocking_reasons=['process_identity_drift:4583']), dict(clear=True), dict(scanner_euid=1)):
            with self.assertRaises(ValueError):
                self.helper.denied_preload(dict(denial, **change), False)
        with self.assertRaises(ValueError):
            self.helper.denied_preload(denial, True)

    def test_only_new_attempt_and_unit_change(self):
        old = dict(attempt_dir='old', device_containment=dict(unit='old', minor=0), source_pins={'a':'pinned'}, plan_path='same')
        new = self.helper.derived_config(old, Path('/new/control'))
        new['attempt_dir'] = old['attempt_dir']
        new['device_containment']['unit'] = old['device_containment']['unit']
        self.assertEqual(new, old)

    def test_park_dispatcher_never_replaces_inflight_or_nonzero_remaining(self):
        helper = rollout.module_from_file('park_queue_test', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/PARK_QUEUE_FOR_COMBINED.py').absolute())
        interpreter = '/localhome/local-rohing/v2/venv/bin/python'
        queue = dict(pid=12, argv=[interpreter, '-B', str(helper.ROOT/'HANDOFF_QUEUE_LIVE_V4.py'), str(helper.ROOT)])
        child = dict(parent=12, argv=[interpreter, '-B', str(helper.ROOT/'orch_r144_a100_a40r_target_rollout.py'),
                    'handoff', '--output', str(helper.ROOT/'lane6'), '--wait-seconds', '600'])
        helper.validate(queue, child, True)
        with self.assertRaises(ValueError):
            helper.validate(queue, child, False)
        with self.assertRaises(ValueError):
            helper.validate(queue, dict(child, argv=['native']), True)
        with self.assertRaises(ValueError):
            helper.validate(dict(queue, argv=['unrelated']), child, True)


class CombinedSuffixTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path('research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z').absolute()
        self.helper = rollout.module_from_file('combined_suffix_test', self.directory/'COMBINED_SUFFIX_ROLLOUT.py')

    def test_same_original_guard_permissions_and_recipe(self):
        old = dict(attempt_dir='old', source_pins={}, plan_path='old', plan_sha256='p', allocation_path='old',
                   allocation_sha256='a', resume=True, hard_end_unix=999,
                   device_containment=dict(minor=7, uid=2524, gid=2524, unit='old'))
        new = dict(old, attempt_dir='new', source_pins={'native': 'new'}, plan_path='new')
        new['device_containment'] = dict(old['device_containment'], unit='new')
        self.helper.guard_delta(old, new)
        for key in ('minor', 'uid', 'gid'):
            changed = dict(new, device_containment=dict(new['device_containment'], **{key: 0}))
            with self.assertRaises(ValueError):
                self.helper.guard_delta(old, changed)
        with self.assertRaises(ValueError):
            self.helper.guard_delta(old, dict(new, hard_end_unix=1000))

    def test_combined_exact_patch_keeps_R144_and_all_non_sleep_bytes(self):
        import ast
        import shutil
        source = (self.directory/'suffix_inputs_1643/gpu/orch_r125_continual_native.py').read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'inputs').mkdir()
            shutil.copyfile(self.directory/'suffix_inputs_1643/GPU_PROOF.json', root/'inputs/GPU_PROOF.json')
            output = root/'lane0'
            (output/'source/gpu').mkdir(parents=True)
            native = output/'source/gpu/orch_r125_continual_native.py'
            native.write_text(source)
            self.helper.patch_copy(output)
            modified = native.read_text()
            self.assertIn(target_patch.NEW_RECEIPT, modified)
            self.assertIn(self.helper.MEMORY_POLICY, modified)
            self.assertEqual(target_patch.without_sleep(ast.parse(source)), target_patch.without_sleep(ast.parse(modified)))
            with self.assertRaises(ValueError):
                self.helper.patch_copy(output)

    def test_combined_staging_has_no_native_creation_or_signals(self):
        import inspect
        source = inspect.getsource(self.helper.stage)
        for forbidden in ('pidfd_send_signal', 'os.kill', 'NativeChild(', 'Popen('):
            self.assertNotIn(forbidden, source)
        for required in ('same_live_child_through_staging', 'unfinished_prior_handoff_not_replaced',
                         'no_controls_or_Aquinas7', 'actual_receiving_runtime_CPU_gate'):
            self.assertIn(required, source)

    def test_runtime_and_real_GPU_proof_are_exact_not_synthetic(self):
        self.assertEqual(rollout.sha(self.directory/'suffix_inputs_1643/GPU_PROOF.json'), self.helper.PROOF_SHA)
        self.assertEqual(rollout.sha(self.directory/'suffix_inputs_1643/gpu/orch_r145_node3_capacity_runtime.json'), self.helper.RUNTIME_SHA)
        for name, expected in self.helper.DEPENDENCIES.items():
            self.assertEqual(rollout.sha(self.directory/'suffix_inputs_1643/gpu'/name), expected)

    def test_combined_queue_exact_scopes_exclude_controls_and_Aquinas7(self):
        queue = rollout.module_from_file('combined_queue_test', self.directory/'COMBINED_QUEUE.py')
        base = Path('/localhome/local-rohing')
        self.assertEqual([path.name for path in queue.selected_stages(base/'orch_r144_target_rollout_a100_suffix_20260916t1643z')],
                         ['lane2', 'lane3', 'lane4', 'lane5', 'lane6', 'lane7'])
        self.assertEqual([path.name for path in queue.selected_stages(base/'orch_r144_target_rollout_a40r_suffix_20260916t1643z')],
                         ['lane0', 'lane1', 'lane3', 'lane4', 'lane5', 'lane6'])
        with self.assertRaises(ValueError):
            queue.selected_stages(base/'other_root')

    def test_combined_queue_preserves_node_lock_and_failure_stop(self):
        import inspect
        queue = rollout.module_from_file('combined_queue_lock_test', self.directory/'COMBINED_QUEUE.py')
        source = inspect.getsource(queue.main)
        for required in ('NODE_HANDOFF.lock', 'NODE_UNRESOLVED.json', 'operator_failed_no_automatic_retry',
                         'COMBINED_QUEUE_CPU.json', 'RUNTIME_GATE_V3.json'):
            self.assertIn(required, source)
        self.assertNotIn('pidfd_send_signal', source)

    def test_combined0_readmission_only_exact_pre_native_drift(self):
        helper = rollout.module_from_file('combined0_readmit_test', self.directory/'READMIT_COMBINED_A40R0.py')
        denial = dict(clear=False, scanner_euid=0,
                      blocking_reasons=['process_identity_drift:2641257', 'process_identity_drift:2641258'])
        helper.denied_preload(denial, False)
        for change in (dict(clear=True), dict(scanner_euid=1000), dict(blocking_reasons=['open_device_pid:1753623']),
                       dict(blocking_reasons=['process_identity_drift:other'])):
            with self.assertRaises(ValueError):
                helper.denied_preload(dict(denial, **change), False)
        with self.assertRaises(ValueError):
            helper.denied_preload(denial, True)

    def test_uncontained0_readmission_cannot_add_permissions(self):
        helper = rollout.module_from_file('combined0_readmit_permissions', self.directory/'READMIT_COMBINED_A40R0.py')
        original = dict(attempt_dir='old', resume=True, source_pins={'source': 'same'}, plan_path='same', hard_end_unix=999)
        proposed = helper.derived_config(original, Path('/new/control'))
        self.assertNotIn('device_containment', proposed)
        proposed['attempt_dir'] = original['attempt_dir']
        self.assertEqual(proposed, original)

    def test_second_fresh0_attempt_requires_its_exact_failed_scan(self):
        helper = rollout.module_from_file('combined0_second_readmit_test', self.directory/'READMIT_COMBINED_A40R0_ATTEMPT2.py')
        denial = dict(clear=False, scanner_euid=0,
                      blocking_reasons=['process_identity_drift:2673771', 'process_identity_drift:2673772'])
        helper.denied_preload(denial, False)
        for reasons in (['open_device_pid:1753623'], ['process_identity_drift:2641257', 'process_identity_drift:2641258']):
            with self.assertRaises(ValueError):
                helper.denied_preload(dict(denial, blocking_reasons=reasons), False)
        with self.assertRaises(ValueError):
            helper.denied_preload(denial, True)


class CombinedLane6ReadmissionTests(unittest.TestCase):
    def setUp(self):
        self.helper = rollout.module_from_file('combined_lane6_readmission_test', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/READMIT_COMBINED_LANE6.py'))

    def test_only_exact_two_preserved_privileged_denials(self):
        for node, case in self.helper.CASES.items():
            report = dict(clear=False, scanner_euid=0, blocking_reasons=case['reasons'])
            self.helper.denied_preload(node, report, False)
            for delta in (dict(clear=True), dict(scanner_euid=1000),
                          dict(blocking_reasons=['open_device_pid:1753623']),
                          dict(blocking_reasons=['process_identity_drift:other'])):
                with self.assertRaises(ValueError):
                    self.helper.denied_preload(node, dict(report, **delta), False)
            with self.assertRaises(ValueError):
                self.helper.denied_preload(node, report, True)

    def test_foreign_node_denial_is_not_interchangeable(self):
        with self.assertRaises(ValueError):
            self.helper.denied_preload('a100', dict(clear=False, scanner_euid=0,
                blocking_reasons=self.helper.CASES['a40r']['reasons']), False)

    def test_same_device_permissions_and_config_only_unique_unit(self):
        original = dict(attempt_dir='old', resume=True, plan_path='same', source_pins={'native': 'same'},
            hard_end_unix=999, device_containment=dict(unit='old', minor=5, device_policy='closed', denied=list(range(5))))
        proposed = self.helper.derived_config(original, Path('/new/control'))
        self.assertNotEqual(proposed['device_containment']['unit'], original['device_containment']['unit'])
        proposed['attempt_dir'] = original['attempt_dir']
        proposed['device_containment']['unit'] = original['device_containment']['unit']
        self.assertEqual(proposed, original)
        self.assertEqual(original['attempt_dir'], 'old')

    def test_waits_for_observer_without_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lane = root/'lane6'
            (root/'NODE_UNRESOLVED.json').write_text(json.dumps(dict(stage=str(lane))))
            with patch.object(self.helper.fcntl, 'flock', side_effect=[BlockingIOError, None]) as locked, \
                    patch.object(self.helper.time, 'sleep') as slept:
                self.helper.acquire_after_observer(1, root, lane)
            self.assertEqual(locked.call_count, 2)
            slept.assert_called_once_with(2)

    def test_foreign_hold_or_absent_hold_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(self.helper.fcntl, 'flock'):
                with self.assertRaises(ValueError):
                    self.helper.acquire_after_observer(1, root, root/'lane6')
                (root/'NODE_UNRESOLVED.json').write_text(json.dumps(dict(stage=str(root/'lane3'))))
                with self.assertRaises(ValueError):
                    self.helper.acquire_after_observer(1, root, root/'lane6')

    def test_no_intervention_when_observer_bound_expires(self):
        with patch.object(self.helper.time, 'monotonic', side_effect=[0, 901]), \
                patch.object(self.helper.fcntl, 'flock') as locked:
            with self.assertRaisesRegex(ValueError, 'observer_still_owns_lock_no_intervention'):
                self.helper.acquire_after_observer(1, Path('/root'), Path('/root/lane6'))
        locked.assert_not_called()

    def test_provenance_and_resume_original_scan_gates_remain(self):
        import inspect
        source = inspect.getsource(self.helper.main)
        for required in ('verify_resume_entrypoint', 'core.launch_command(request)', 'core.monitor(attempt',
                         'exact_unchanged_checkpoint_history_RNG', 'all_frozen_source_preserved',
                         'no_live_retired_or_failed_process', 'preserve_hold_until_new_committed'):
            self.assertIn(required, source)
        self.assertNotIn('pidfd_send_signal', source)
        self.assertNotIn('kill(', source)


class QueueTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.queue = rollout.module_from_file('r144_test_queue', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/HANDOFF_QUEUE.py').absolute())

    def lane(self, number, status='STAGED_NOT_APPLIED', kind='SLEEP_COMPLETE'):
        output = self.root/('lane'+str(number))
        output.mkdir()
        life = self.root/('life'+str(number))
        records = life/'stream/records'
        records.mkdir(parents=True)
        (records/'00000000000000000001.json').write_text(json.dumps(dict(kind=kind)))
        (output/'STAGED.json').write_text(json.dumps(dict(status=status, old_plan=dict(root=str(life)))))
        return output

    def test_queue_never_dispatches_reserved_kernel4(self):
        self.lane(4, status='RESERVED_AQUINAS_PROSPECTIVE_ONLY')
        self.assertEqual(self.queue.ready(self.root), ([], None))

    def test_queue_never_dispatches_incomplete_stage(self):
        (self.root/'lane4_incomplete').mkdir()
        self.assertEqual(self.queue.ready(self.root), ([], None))

    def test_queue_selects_saved_lane_not_pending_update(self):
        pending = self.lane(1, kind='UPDATE')
        saved = self.lane(3)
        self.assertEqual(self.queue.ready(self.root), ([pending, saved], saved))

    def test_queue_refuses_unresolved_retirement(self):
        output = self.lane(0)
        (output/'RETIREMENT_STARTED.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError, 'unresolved_attempt'):
            self.queue.ready(self.root)

    def test_queue_uses_only_hash_bound_local_operator(self):
        output = self.lane(4)
        operator = self.root/'versioned_operator.py'
        operator.write_text('original version')
        (output/'STAGED.json').write_text(json.dumps(dict(operator_path=str(operator), operator_sha256=rollout.sha(operator))))
        self.assertEqual(self.queue.operator_path(self.root, output), operator)
        operator.write_text('wrong version')
        with self.assertRaisesRegex(ValueError, 'only_bound_owned_operator_version'):
            self.queue.operator_path(self.root, output)

    def test_remaining_queue_excludes_obsolete_kernel4_stages_and_dead7(self):
        queue = rollout.module_from_file('r144_remaining_queue', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/HANDOFF_QUEUE_LIVE_V4.py').absolute())
        self.assertEqual([path.name for path in queue.selected_stages(self.root)], ['lane0', 'lane1', 'lane5', 'lane6'])
        self.lane(7)
        self.lane(4)
        self.lane('4_dependency')
        self.lane('4_strict_v7')
        self.assertEqual(queue.ready(self.root), ([], None))

    def test_remaining_queue_never_skips_own_unresolved_retirement(self):
        queue = rollout.module_from_file('r144_remaining_queue_failure', Path(
            'research_loop/workers/r144_a100_a40r_target_rollout_20260916t1510z/HANDOFF_QUEUE_LIVE_V4.py').absolute())
        output = self.lane(1)
        (output/'RETIREMENT_STARTED.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError, 'unresolved_attempt'):
            queue.ready(self.root)


class RolloutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        patcher = patch.object(rollout, 'BASE', self.base)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.node, self.physical = 'a100', 3
        self.source = self.base/'original_source'
        (self.source/'gpu').mkdir(parents=True)
        current = Path('gpu/orch_r125_continual_native.py').read_text()
        original = current.replace(target_patch.NEW_RECEIPT, target_patch.OLD_RECEIPT).replace(
            '        child_exposures, anchor_exposures = 0, 0\n',
            target_patch.OLD_ENCODING+'        child_exposures, anchor_exposures = 0, 0\n')
        (self.source/'gpu/orch_r125_continual_native.py').write_text(original)
        (self.source/'gpu/__init__.py').write_bytes(b'')
        (self.source/'gpu/orch_r125_continual_guard.py').write_bytes(Path('gpu/orch_r125_continual_guard.py').read_bytes())
        (self.source/'STARTUP.md').write_text('Exact original birth text.')
        (self.source/'untouched.bin').write_bytes(bytes(range(256)))
        name, gpu_uuid = rollout.LANES[self.node][self.physical]
        self.plan = dict(root=str(self.base/name/'run1'), source_root=str(self.source), physical=self.physical,
            gpu_uuid=gpu_uuid, hard_end_unix=2000000000, lease_end_unix=2000000500,
            startup_context=dict(path=str(self.source/'STARTUP.md'), sha256=rollout.sha(self.source/'STARTUP.md'), version='R127_STARTUP_V1'),
            context_limit=16384, decoder={'temperature': .7}, seed=0, parent='unchanged')
        self.control = self.base/'original_control'
        self.control.mkdir()
        (self.control/'PLAN.json').write_text(json.dumps(self.plan))
        (self.control/'ALLOCATION.json').write_text(json.dumps(dict(plan_sha256=rollout.sha(self.control/'PLAN.json'), existing_grant=True)))
        self.config = dict(host_sha256=rollout.HOSTS[self.node], hard_end_unix=self.plan['hard_end_unix'],
            attempt_dir=str(self.control), plan_path=str(self.control/'PLAN.json'), plan_sha256=rollout.sha(self.control/'PLAN.json'),
            allocation_path=str(self.control/'ALLOCATION.json'), lease_path='existing_lease', lease_sha256='a'*64,
            device_containment=dict(minor=0, uid=os.getuid(), gid=os.getgid(), unit='orch-r136-native-'+'a'*32))
        (self.control/'GUARD.json').write_text(json.dumps(self.config))
        self.patch_path = Path('gpu/orch_r144_target_patch.py').absolute()
        self.helper_path = Path('gpu/orch_r144_sleep_targets.py').absolute()
        self.cpu = self.base/'CPU.json'
        self.cpu.write_text(json.dumps(dict(status='PASS', operator_sha256=rollout.sha(Path(rollout.__file__).absolute()),
            patch_sha256=rollout.PATCH_SHA, helper_sha256=rollout.HELPER_SHA)))
        self.output = self.base/'orch_r144_target_rollout_a100_test'/'lane3'
        self.output.parent.mkdir()

    def run_stage(self):
        original = SimpleNamespace()
        with patch.object(rollout, 'current_node'), patch.object(rollout, 'originals', return_value=(self.config,self.plan,original)), \
                patch.object(rollout, 'actual_device', return_value=dict(physical=self.physical,gpu_uuid=self.plan['gpu_uuid'],minor=0)), \
                patch.object(rollout, 'process_pair', return_value={'fixture': True}), patch.object(rollout.subprocess, 'run'):
            return rollout.stage(self.node,self.control/'GUARD.json',123,self.output,self.cpu,self.patch_path,self.helper_path)

    def test_stage_exact_patch_only_and_other_bytes_unchanged(self):
        before = rollout.inventory_files(self.source)
        result = self.run_stage()
        self.assertEqual(result['status'], 'STAGED_NOT_APPLIED')
        self.assertEqual(rollout.inventory_files(self.source), before)
        proof = rollout.read(self.output/'SOURCE_PROOF.json')
        changed = [name for name in before if before[name] != proof['new_inventory'][name]]
        self.assertEqual(changed, ['gpu/orch_r125_continual_native.py'])
        self.assertEqual(set(proof['new_inventory'])-set(before), {'gpu/orch_r144_sleep_targets.py'})
        self.assertEqual((self.output/'source/gpu/orch_r125_continual_native.py').read_text(),
            target_patch.patch_source((self.source/'gpu/orch_r125_continual_native.py').read_text()))

    def test_stage_preserves_training_lease_parent_and_topology(self):
        self.run_stage()
        updated = rollout.read(self.output/'control/GUARD.json')
        self.assertEqual(updated['lease_path'],self.config['lease_path'])
        self.assertEqual(updated['lease_sha256'],self.config['lease_sha256'])
        self.assertTrue(updated['resume'])
        for name in ('minor','uid','gid'):
            self.assertEqual(updated['device_containment'][name],self.config['device_containment'][name])
        self.assertNotEqual(updated['device_containment']['unit'],self.config['device_containment']['unit'])
        proposed = rollout.read(updated['plan_path'])
        proposed['source_root'] = self.plan['source_root']
        proposed['startup_context']['path'] = self.plan['startup_context']['path']
        self.assertEqual(proposed,self.plan)

    def test_readonly_native_copy_preserves_original_and_modes(self):
        native = self.source/'gpu/orch_r125_continual_native.py'
        native.chmod(0o444)
        before = native.read_bytes()
        self.run_stage()
        self.assertEqual(native.read_bytes(), before)
        self.assertEqual(native.stat().st_mode & 0o777, 0o444)
        self.assertEqual((self.output/'source/gpu/orch_r125_continual_native.py').stat().st_mode & 0o777, 0o444)

    def test_readonly_source_directory_modes_preserved(self):
        (self.source/'gpu').chmod(0o555)
        self.addCleanup((self.source/'gpu').chmod, 0o755)
        self.run_stage()
        self.addCleanup((self.output/'source/gpu').chmod, 0o755)
        self.assertEqual((self.source/'gpu').stat().st_mode & 0o777, 0o555)
        self.assertEqual((self.output/'source/gpu').stat().st_mode & 0o777, 0o555)
        self.assertTrue((self.output/'source/gpu/orch_r144_sleep_targets.py').is_file())

    def test_refuse_stale_one_shot_guard_before_staging(self):
        guard = self.source/'gpu/orch_r125_continual_guard.py'
        guard.write_text(guard.read_text().replace("child.run(config['plan_path'], resume=config['resume'])",
                                                "recovery.run(config['plan_path'])"))
        with self.assertRaisesRegex(ValueError, 'refuse_one_shot_guard_entrypoint'):
            self.run_stage()
        self.assertFalse(self.output.exists())

    def test_refuse_unconditional_recovery_with_stale_suffix(self):
        native = self.source/'gpu/orch_r125_continual_native.py'
        native.write_text(native.read_text().replace('                if recovering:\n', '                if True:\n', 1))
        with self.assertRaisesRegex(ValueError, 'known_recovery_and_finish_sleep_branches'):
            self.run_stage()
        self.assertFalse(self.output.exists())

    def test_reserved_kernel4_only_source_no_config_or_process_work(self):
        self.node,self.physical = 'a40r',4
        name,gpu_uuid = rollout.LANES[self.node][4]
        self.plan.update(root=str(self.base/name/'run1'),physical=4,gpu_uuid=gpu_uuid)
        self.config['host_sha256'] = rollout.HOSTS['a40r']
        del self.config['device_containment']
        self.output = self.base/'orch_r144_target_rollout_a40r_test'/'lane4'
        self.output.parent.mkdir()
        with patch.object(rollout,'current_node'), patch.object(rollout,'originals',return_value=(self.config,self.plan,None)), \
                patch.object(rollout,'actual_device',return_value=dict(physical=4,gpu_uuid=gpu_uuid,minor=7)), \
                patch.object(rollout,'process_pair',side_effect=AssertionError('must_not_touch_reserved_process')):
            result = rollout.stage(self.node,self.control/'GUARD.json',0,self.output,self.cpu,self.patch_path,self.helper_path)
        self.assertEqual(result['status'],'RESERVED_AQUINAS_PROSPECTIVE_ONLY')
        self.assertFalse((self.output/'control').exists())
        with self.assertRaisesRegex(ValueError,'Aquinas_kernel4_prospective_only'):
            rollout.check_scope(self.node,self.config,self.plan)

    def test_reject_frozen_controls_and_foreign_node(self):
        for physical in (0,1):
            plan = dict(self.plan,physical=physical)
            with self.assertRaisesRegex(ValueError,'no_controls_or_unallocated_slots'):
                rollout.check_scope('a100',self.config,plan)
        with self.assertRaisesRegex(ValueError,'only_owned_node_hash'):
            rollout.check_scope('a40r',self.config,self.plan)

    def test_reject_wrong_root_UUID_or_added_permissions(self):
        for field,value in [('root',str(self.base/'another_child/run1')),('gpu_uuid','GPU-wrong')]:
            with self.assertRaisesRegex(ValueError,'exact_child_root_UUID'):
                rollout.check_scope('a100',self.config,dict(self.plan,**{field:value}))
        config = deepcopy(self.config)
        del config['device_containment']
        with self.assertRaisesRegex(ValueError,'original_topology_not_broadened'):
            rollout.check_scope('a100',config,self.plan)

    def test_unconsumed_or_consumed_wall_authorization_never_silently_reused(self):
        with self.assertRaisesRegex(ValueError,'unsupported_one_shot_wall_topology'):
            rollout.relocated_plan(dict(self.plan,authorized_wall_extension={'opaque':'not_assumed'}),self.source)

    def test_CPU_failure_before_copy(self):
        self.cpu.write_text(json.dumps(dict(status='FAIL')))
        with self.assertRaisesRegex(ValueError,'own_bound_CPU_gate'):
            self.run_stage()
        self.assertFalse(self.output.exists())

    def test_symlink_source_rejected_before_copy(self):
        (self.source/'foreign').symlink_to(self.cpu)
        with self.assertRaisesRegex(ValueError,'immutable_source_no_symlinks'):
            self.run_stage()
        self.assertFalse(self.output.exists())

    def test_repeated_stage_rejected(self):
        self.run_stage()
        with self.assertRaisesRegex(ValueError,'unique_owned_stage'):
            self.run_stage()

    def test_original_node_launcher_commands(self):
        for node,contained,expected in [('a100',True,'gpu.orch_r136_node1_launcher'),
                ('a40r',True,'gpu.orch_r137_node4_containment'),('a40r',False,rollout.GUARD)]:
            config = {'device_containment':{}} if contained else {}
            handler = rollout.launcher(node,config)
            command = rollout.launch_command(dict(handler=handler,new_config='/new/GUARD.json'))
            self.assertEqual(command,[str(rollout.PYTHON),'-B','-m',expected,
                'contained-supervise' if contained else 'supervise','--config','/new/GUARD.json'])

    def fixture_boundary(self,pending=None,kind='SLEEP_COMPLETE'):
        stream = self.base/'life/stream/records'
        stream.mkdir(parents=True)
        state = dict(pending=pending,sleep_frontier=1,rows=[{'fixture':True}],sleep_receipts=[dict(status='COMPLETE')])
        document = dict(status='COMPLETE',cycle=1,resume_state=dict(state=state,sha256=rollout.digest(state)))
        record = dict(index=0,kind=kind,document=document)
        record['sha256'] = rollout.digest(record)
        (stream/'00000000000000000000.json').write_text(json.dumps(record))
        return self.base/'life'

    def test_exact_saved_boundary_required(self):
        root = self.fixture_boundary()
        saved = rollout.sleep_boundary(root)
        self.assertEqual(saved['cycle'],1)
        self.assertIsNone(saved['state']['pending'])

    def test_pending_boundary_rejected(self):
        root = self.fixture_boundary(pending='sleep:unfinished')
        with self.assertRaisesRegex(ValueError,'exact_saved_no_pending_boundary'):
            rollout.sleep_boundary(root)

    def test_UPDATE_or_REQUEST_not_a_boundary(self):
        root = self.fixture_boundary(kind='UPDATE')
        self.assertIsNone(rollout.sleep_boundary(root))

    def test_boundary_bad_hash_rejected(self):
        root = self.fixture_boundary()
        path = root/'stream/records/00000000000000000000.json'
        document = json.loads(path.read_text())
        document['sha256'] = '0'*64
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError,'boundary_record_hash'):
            rollout.sleep_boundary(root)

    def test_readout_drained_uses_metadata_not_held_contents(self):
        root = self.base/'readout_life'
        (root/'readouts/sleep_000001').mkdir(parents=True)
        (root/'checkpoints/sleep_000001').mkdir(parents=True)
        commit = root/'checkpoints/sleep_000001/COMMIT.json'
        commit.write_text('{}')
        complete = root/'readouts/sleep_000001/COMPLETE.json'
        complete.write_text('HELD CONTENT MUST NOT BE OPENED')
        dispatch = root/'readouts/sleep_000001_DISPATCH.json'
        dispatch.write_text(json.dumps(dict(resident_pid=999999,cycle=1,checkpoint_sha256=rollout.sha(commit))))
        saved = dict(cycle=1)
        original_read = Path.read_text
        def guarded_read(path,*args,**kwargs):
            if path == complete:
                raise AssertionError('held content opened')
            if path.name == 'children':
                return ''
            return original_read(path,*args,**kwargs)
        with patch.object(Path,'read_text',guarded_read):
            receipt = rollout.readout_drained(dict(root=str(root)),saved,999999,'original_plan',
                SimpleNamespace(readout_name=lambda plan,cycle:'sleep_000001'))
        self.assertFalse(receipt['completion_contents_read'])
        (root/'readouts/sleep_000001_FAILED.json').write_text('{}')
        self.assertFalse(rollout.readout_drained(dict(root=str(root)),saved,999999,'original_plan',
            SimpleNamespace(readout_name=lambda plan,cycle:'sleep_000001')))


if __name__ == '__main__':
    unittest.main()
