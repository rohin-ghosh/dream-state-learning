"""Signal-free regression tests for the scoped NODE4 operator."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('node4_operator', ROOT / 'node4_rollout.py')
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


class ScopeTests(unittest.TestCase):
    def test_explicit_no_retirement_rearm_bounded_90_minutes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'WAIT_EXPIRED_1.json').write_text('{}')
            operator.validate_handoff_attempt(output, 5400)
            for seconds in (0, -1, 5401, True, 5400.0):
                with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                    operator.validate_handoff_attempt(output, seconds)

    def test_consumed_handoff_cannot_rearm(self):
        for name in ('RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json',
                     'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                (output / name).write_text('{}')
                with self.assertRaises(ValueError):
                    operator.validate_handoff_attempt(output, 5400)

    def test_exact_four_existing_lives(self):
        self.assertEqual(set(operator.ALLOWLIST), {0, 1, 3, 4})
        self.assertEqual({row[0] for row in operator.ALLOWLIST.values()},
                         {'kernel0', 'raw_unparented', 'raw_parented', 'kernel_parented'})

    def test_legacy_handlers_unchanged(self):
        for physical in (0, 1):
            with self.subTest(physical=physical):
                self.assertEqual(operator.handler(physical, {})['module'], 'gpu.orch_r125_continual_guard')
                with self.assertRaises(ValueError):
                    operator.handler(physical, {'device_containment': {}})

    def test_actual_strict_launchers(self):
        for physical, module in ((3, 'gpu.orch_r137_node4_containment'), (4, 'gpu.orch_r144_a40r4_strict')):
            with self.subTest(physical=physical):
                self.assertEqual(operator.handler(physical, {'device_containment': {}})['module'], module)
                with self.assertRaises(ValueError):
                    operator.handler(physical, {})

    def test_unknown_device_rejected_before_host_probe(self):
        for physical in (-1, 2, 5, 6, 7, 8):
            with self.subTest(physical=physical), self.assertRaises(ValueError):
                operator.selected(physical, None)

    def test_unknown_handler_cannot_choose_a_strict_module(self):
        for physical in (False, True, 2, 5, 6, 7):
            with self.subTest(physical=physical), self.assertRaises(ValueError):
                operator.handler(physical, {'device_containment': {}})

    def test_exact_legacy_pins(self):
        import hashlib
        repo = ROOT.parents[3] if len(ROOT.parents) > 3 else ROOT
        module_path = repo / operator.LEGACY if (repo / operator.LEGACY).exists() else ROOT / 'legacy_containment.py'
        test_path = repo / 'tests/test_orch_r179_node4_legacy_containment.py'
        if not test_path.exists():
            test_path = ROOT / 'legacy_tests.py'
        self.assertEqual(hashlib.sha256(module_path.read_bytes()).hexdigest(), operator.LEGACY_SHA)
        self.assertEqual(hashlib.sha256(test_path.read_bytes()).hexdigest(),
                         operator.LEGACY_TEST_SHA)

    def test_only_existing_guard_launch(self):
        source = (ROOT / 'node4_rollout.py').read_text()
        self.assertNotIn('SIGKILL', source)
        self.assertNotIn('os.kill(', source)
        self.assertNotIn('killpg(', source)
        self.assertIn('helpers.launch_command(request)', source)
        self.assertNotIn("journal.record(", source)

    def test_source_compiles(self):
        for name in ('node4_rollout.py', 'cpu_actual.py'):
            ast.parse((ROOT / name).read_text())


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        source = '/frozen/source'
        self.config_path = Path('/control/GUARD.json')
        self.config = dict(plan_sha256='p', device_containment=dict(unit='unit'))
        self.plan = dict(source_root=source, physical=4, gpu_uuid='GPU-owned')
        self.helpers = SimpleNamespace(PYTHON=Path('/venv/python'), GUARD='gpu.orch_r125_continual_guard',
            sha=lambda path: 'c')
        actor_args = ['/venv/python', '-B', '-m', self.helpers.GUARD, 'native', '--config', str(self.config_path)]
        common = dict(uid=operator.os.getuid(), boot_id='boot', cgroup='0::/system.slice/unit.service',
            cwd=source, environment=['CUDA_VISIBLE_DEVICES=GPU-owned'])
        self.pair = dict(actor=dict(common, pid=3, parent=2, group=2, start_ticks='30', argv=actor_args),
            timer=dict(common, pid=2, parent=1, group=2, start_ticks='20',
                argv=['timeout', '--signal=TERM', '--kill-after=5s', '100s'] + actor_args),
            supervisor=dict(common, pid=1, parent=0, group=1, start_ticks='10',
                argv=['/venv/python', '-B', '-m', 'gpu.orch_r144_a40r4_strict', 'contained-native',
                    '--config', str(self.config_path)]))
        self.launch = dict(pid=2, parent_start_ticks='20', guard_sha256='c', plan_sha256='p', gpu_uuid='GPU-owned')

    def verify(self, pair=None):
        operator.validate_pair(pair or self.pair, self.config_path, self.config, self.plan, self.launch, self.helpers)

    def test_exact_owned_pair(self):
        self.verify()

    def test_reject_identity_and_confinement_drift(self):
        mutations = [('actor', 'group', 10), ('timer', 'parent', 17), ('timer', 'start_ticks', '99'),
            ('supervisor', 'uid', -1), ('actor', 'cwd', '/other'), ('actor', 'boot_id', 'new-boot'),
            ('actor', 'environment', ['CUDA_VISIBLE_DEVICES=ALL']), ('actor', 'cgroup', '0::/other')]
        for name, field, value in mutations:
            with self.subTest(name=name, field=field), self.assertRaises(ValueError):
                pair = deepcopy(self.pair)
                pair[name][field] = value
                self.verify(pair)

    def test_reject_launcher_substitution(self):
        pair = deepcopy(self.pair)
        pair['supervisor']['argv'][3] = 'gpu.orch_r137_node4_containment'
        with self.assertRaises(ValueError):
            self.verify(pair)

    def test_original_allocation_binding(self):
        for field in ('pid', 'parent_start_ticks', 'guard_sha256', 'plan_sha256', 'gpu_uuid'):
            with self.subTest(field=field):
                previous = self.launch[field]
                self.launch[field] = 'wrong'
                with self.assertRaises(ValueError):
                    self.verify()
                self.launch[field] = previous


class OccupiedPreflightTests(unittest.TestCase):
    def setUp(self):
        self.request = dict(old_plan=dict(gpu_uuid='GPU-owned'),
            processes=dict(actor=dict(pid=3), timer=dict(pid=2), supervisor=dict(pid=1)))
        self.report = dict(scanner_euid=0, gpu=dict(uuid='GPU-owned'), clear=False,
            compute_processes=[dict(pid=3, gpu_uuid='GPU-owned')],
            blocking_reasons=['active_compute_pid:3', 'open_device_pid:3', 'reserved_cvd_pid:1',
                'uuid_reservation:2', 'unexplained_device_memory'])

    def test_expected_live_occupancy_is_not_clear_admission(self):
        previous = deepcopy(self.report)
        operator.validate_occupied_preflight(self.report, self.request)
        self.assertEqual(self.report, previous)
        self.assertFalse(self.report['clear'])

    def test_foreign_and_unknown_reasons_block(self):
        for reason in ('open_device_pid:9', 'active_compute_pid:9', 'uuid_reservation:9',
                       'minor_scan_identity_changed:1', 'process_identity_drift:2', 'unknown'):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                report = deepcopy(self.report)
                report['blocking_reasons'].append(reason)
                operator.validate_occupied_preflight(report, self.request)

    def test_memory_without_exact_live_compute_blocks(self):
        self.report['compute_processes'] = []
        with self.assertRaises(ValueError):
            operator.validate_occupied_preflight(self.report, self.request)

    def test_foreign_compute_even_without_reason_blocks(self):
        self.report['compute_processes'].append(dict(pid=9, gpu_uuid='GPU-owned'))
        with self.assertRaises(ValueError):
            operator.validate_occupied_preflight(self.report, self.request)

    def test_other_life_compute_is_not_selected(self):
        self.report['compute_processes'].append(dict(pid=9, gpu_uuid='GPU-other'))
        operator.validate_occupied_preflight(self.report, self.request)


class PreflightEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = ROOT.parents[3] if len(ROOT.parents) > 3 else ROOT
        path = repo / operator.PREFLIGHT
        if not path.exists():
            path = ROOT / 'busy_preflight.py'
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != operator.PREFLIGHT_SHA:
            raise ValueError('exact_Main_preflight_fixture_bytes')
        tree = ast.parse(raw)
        nodes = [node for node in tree.body if
                 (isinstance(node, ast.FunctionDef) and node.name == 'classify_argv_only') or
                 (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                     and target.id == 'KERNEL_KEYS' for target in node.targets))]
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-Main-classifier-CPU>', 'exec'), namespace)
        cls.classify = staticmethod(namespace['classify_argv_only'])

    def setUp(self):
        identity = dict(pid=42, uid=0, start_ticks='123', boot_id='boot')
        self.request = dict(old_plan=dict(gpu_uuid='GPU-owned'),
            processes=dict(actor=dict(pid=3), timer=dict(pid=2), supervisor=dict(pid=1)))
        self.original = dict(scanner_euid=0, clear=False, gpu=dict(uuid='GPU-owned'),
            compute_processes=[dict(pid=3, gpu_uuid='GPU-owned')],
            processes=[dict(identity, pinned_identity=dict(identity), target_device_open=False, cvd=None)],
            blocking_reasons=['active_compute_pid:3', 'open_device_pid:3', 'unexplained_device_memory',
                'process_identity_drift:42', 'minor_scan_identity_changed:42', 'minor_scan_process_drift:42'])
        self.samples = [dict(identity, executable_identity=[1, 2], visibility_complete=True,
            target_open=False, cvd=None, command_sha256=letter * 64) for letter in ('a', 'b', 'b')]

    def annotated(self):
        original = deepcopy(self.original)
        digest = hashlib.sha256(json.dumps(original, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        return dict(original, r179_preflight_evidence=dict(schema='R179_BUSY_PREFLIGHT_EVIDENCE_ONLY_V1',
            original_report_sha256=digest, eligible_non_gpu_argv_only_pids=[42],
            observations={'42': deepcopy(self.samples)}, original_clear_and_blockers_unchanged=True,
            admission_receipt=False, scope='PRE_RETIREMENT_KNOWN_OWNER_PREFLIGHT_ONLY_FINAL_SCAN_UNCHANGED'))

    def verify(self, report):
        proven = operator.proven_argv_only(report, self.classify)
        operator.validate_occupied_preflight(report, self.request, proven)
        return proven

    def test_exact_three_drift_prefixes_with_full_proof(self):
        report = self.annotated()
        before = deepcopy(report)
        self.assertEqual(self.verify(report), {42})
        self.assertEqual(report, before)
        self.assertFalse(report['clear'])

    def test_changed_original_report_is_not_accepted(self):
        for field, value in (('clear', True), ('blocking_reasons', []), ('scanner_euid', 2524)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                report = self.annotated()
                report[field] = value
                self.verify(report)

    def test_missing_and_weak_samples_fail_closed(self):
        for field, value in (('visibility_complete', False), ('target_open', True), ('cvd', '0'),
                             ('executable_identity', [9, 9]), ('start_ticks', '456')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                report = self.annotated()
                report['r179_preflight_evidence']['observations']['42'][-1][field] = value
                self.verify(report)
        report = self.annotated()
        report['r179_preflight_evidence']['observations']['42'].pop()
        with self.assertRaises(ValueError):
            self.verify(report)

    def test_list_without_matching_observations_is_rejected(self):
        for value in ({}, {'42': self.samples, '43': self.samples}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                report = self.annotated()
                report['r179_preflight_evidence']['observations'] = value
                self.verify(report)

    def test_only_drift_reasons_are_explained(self):
        for reason in ('open_device_pid:42', 'active_compute_pid:42', 'uuid_reservation:42',
                       'reserved_cvd_pid:42', 'process_identity_drift:43', 'process_identity_drift:42:extra', 'unknown'):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                self.original['blocking_reasons'].append(reason)
                try:
                    self.verify(self.annotated())
                finally:
                    self.original['blocking_reasons'].pop()

    def test_gpu_compute_anywhere_cannot_be_explained(self):
        self.original['compute_processes'].append(dict(pid=42, gpu_uuid='GPU-other'))
        with self.assertRaises(ValueError):
            self.verify(self.annotated())

    def test_admission_flag_or_scope_cannot_be_repurposed(self):
        for field, value in (('admission_receipt', True), ('scope', 'FINAL_ADMISSION'),
                             ('eligible_non_gpu_argv_only_pids', [42, 42])):
            with self.subTest(field=field), self.assertRaises(ValueError):
                report = self.annotated()
                report['r179_preflight_evidence'][field] = value
                self.verify(report)

    def test_known_owner_never_gets_argv_exception(self):
        with self.assertRaises(ValueError):
            operator.validate_occupied_preflight(self.original, self.request, {3})


class ReadoutSpawnRegressionTests(unittest.TestCase):
    def test_dispatch_before_spawn_never_holds_actor(self):
        self.assertFalse(operator.ready_to_hold(False, None))
        self.assertFalse(operator.ready_to_hold(None, None))

    def test_proven_child_or_completed_readout_can_hold(self):
        self.assertTrue(operator.ready_to_hold(False, {'pid': 99}))
        self.assertTrue(operator.ready_to_hold({'completed': True}, None))

    def test_exact_readout_child_binding(self):
        actor = dict(pid=3, uid=2524, boot_id='boot', cgroup='exact-cgroup',
                     environment=['CUDA_VISIBLE_DEVICES=GPU-own'])
        command = ['python', '-B', '-m', 'gpu.orch_r125_continual_readout', '--plan', '/same-plan']
        child = dict(actor, pid=99, parent=3, group=99, argv=command, cwd='/source')
        operator.verify_readout_child(child, actor, command, '/source')
        for field, value in (('parent', 7), ('uid', 0), ('boot_id', 'other'), ('cgroup', 'other'),
                             ('group', 3), ('argv', ['another']), ('cwd', '/elsewhere'),
                             ('environment', ['CUDA_VISIBLE_DEVICES=GPU-other'])):
            with self.subTest(field=field), self.assertRaises(ValueError):
                operator.verify_readout_child(dict(child, **{field: value}), actor, command, '/source')

    def test_only_bound_dispatched_readout_occupancy_is_allowed(self):
        request = dict(old_plan=dict(gpu_uuid='GPU-own'), processes=dict(actor=dict(pid=3), timer=dict(pid=2)),
            preflight_owned_readout=dict(pid=99))
        report = dict(scanner_euid=0, gpu=dict(uuid='GPU-own'),
            compute_processes=[dict(pid=99, gpu_uuid='GPU-own')],
            blocking_reasons=['active_compute_pid:99', 'open_device_pid:99', 'unexplained_device_memory'])
        operator.validate_occupied_preflight(report, request)
        del request['preflight_owned_readout']
        with self.assertRaises(ValueError):
            operator.validate_occupied_preflight(report, request)


if __name__ == '__main__':
    unittest.main()
