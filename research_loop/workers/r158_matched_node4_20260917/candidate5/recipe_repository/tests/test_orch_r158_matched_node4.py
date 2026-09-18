import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r151_matched_containment as legacy
from gpu import orch_r158_matched_node4 as node4


ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / 'research_loop/workers/r143_node5_allocator_20260916t1427z/CONFINEMENT_API.py'


def dump(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, sort_keys=True))
    return path


@pytest.fixture
def capsule(tmp_path):
    path = tmp_path / 'capsule.py'
    path.write_bytes(node4.render_capsule(CAPSULE.read_bytes()))
    return node4.load_capsule(path)


def test_profile_isolated_and_original_globals_unchanged():
    before = (legacy.HOST, deepcopy(legacy.DEVICES), legacy.SCOPE, legacy.MODULE)
    result = node4.engine()
    assert result.HOST == node4.HOST == '[REDACTED_HOST]'
    assert result.HOST_SHA256 == hashlib.sha256(node4.HOST.encode()).hexdigest()
    assert result.DEVICES == node4.DEVICES
    assert result.MODULE == node4.MODULE and result.SCOPE == node4.SCOPE
    assert before == (legacy.HOST, legacy.DEVICES, legacy.SCOPE, legacy.MODULE)
    assert result is not node4.engine()


def test_frozen_guard_derivation_preserves_scanner_exactly():
    from gpu import orch_r151_matched_stage as staging
    profile = node4.engine()
    data = (ROOT / profile.GUARD).read_bytes()
    original = data if hashlib.sha256(data).hexdigest() == profile.ORIGINAL_GUARD_SHA256 else staging.revert_guard(data.decode()).encode()
    rendered = profile.render_guard(original)
    assert staging.revert_guard(rendered.decode()).encode() == original
    before = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == 'scan')
    after = next(node for node in ast.parse(rendered).body if isinstance(node, ast.FunctionDef) and node.name == 'scan')
    assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False)
    for name, checksum in profile.PINNED_SCANNER.items():
        assert node4.sha(ROOT / name) == checksum


def test_profile_preserves_every_nonprofile_AST_node():
    original = (ROOT / 'gpu/orch_r151_matched_containment.py').read_bytes()
    before, after = ast.parse(original), node4.profile_tree(original)
    assert len(before.body) == len(after.body)
    allowed_constants = {'HOST', 'HOST_SHA256', 'DEVICES', 'SCOPE', 'MODULE', 'EXISTING_LEASE_SHA256'}
    changes = []
    for old, new in zip(before.body, after.body):
        if ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False):
            continue
        if isinstance(old, ast.Assign):
            assert old.targets[0].id in allowed_constants
            changes.append(old.targets[0].id)
        else:
            assert isinstance(old, ast.FunctionDef) and old.name in ('go_binding', 'validate_go', 'supervise')
            if old.name == 'supervise':
                class UndoScanCall(ast.NodeTransformer):
                    def visit_Call(self, node):
                        if isinstance(node.func, ast.Name) and node.func.id == 'scan_with_transient_rechecks':
                            assert node.keywords[-1].arg == 'receipt_dir'
                            node.keywords.pop()
                            node.func = ast.Attribute(value=ast.Name(id='subprocess', ctx=ast.Load()),
                                                      attr='run', ctx=ast.Load())
                        return self.generic_visit(node)
                restored = UndoScanCall().visit(deepcopy(new))
                assert ast.dump(old, include_attributes=False) == ast.dump(restored, include_attributes=False)
            changes.append(old.name)
    assert set(changes) == allowed_constants | {'go_binding', 'validate_go', 'supervise'}


@pytest.mark.parametrize('before,after', [
    ('allowed_physical=[0, 3, 4]', 'allowed_physical=[0, 3, 5]'),
    ("'R151_MAIN_GO_V1'", "'UNREVIEWED_GO'"),
    ("HOST = '[REDACTED_HOST]'", "UNREVIEWED_HOST = '[REDACTED_HOST]'"),
])
def test_unknown_profile_shape_rejected(before, after):
    source = (ROOT / 'gpu/orch_r151_matched_containment.py').read_text()
    with pytest.raises(ValueError):
        node4.profile_tree(source.replace(before, after))


def test_capsule_only_host_and_devices_change():
    before = CAPSULE.read_bytes()
    after = node4.render_capsule(before)
    restored = after.decode().replace('DEVICES = ' + repr(node4.DEVICES), node4.OLD_DEVICES)
    restored = restored.replace(repr(node4.HOST), "'[REDACTED_HOST]'")
    assert restored.encode() == before
    assert CAPSULE.read_bytes() == before


@pytest.mark.parametrize('mutator', [lambda value: value + b'\n',
    lambda value: value.replace(b'DevicePolicy', b'NoDevicePolicy'),
    lambda value: value.replace(b'range(8)', b'range(7)')])
def test_modified_capsule_rejected(tmp_path, mutator):
    with pytest.raises(ValueError):
        node4.render_capsule(mutator(CAPSULE.read_bytes()))
    path = tmp_path / 'capsule.py'
    path.write_bytes(mutator(node4.render_capsule(CAPSULE.read_bytes())))
    with pytest.raises(ValueError):
        node4.load_capsule(path)


@pytest.mark.parametrize('physical', [5, 6, 7])
def test_single_device_strict_command(capsule, tmp_path, physical):
    command = capsule.device_containment_command(physical, physical, 2524, 2524,
        node4.engine().new_unit(tmp_path / 'attempt'), '/new/source', ['/python', '-B'], 120)
    for setting in ('DevicePolicy=strict', 'DeviceAllow=', 'NoNewPrivileges=yes',
        'CapabilityBoundingSet=', 'AmbientCapabilities=', 'ProtectControlGroups=yes',
        'KillMode=control-group', 'RuntimeMaxSec=120', 'User=2524', 'Group=2524'):
        assert '--property=' + setting in command
    gpu_nodes = [entry for entry in command if entry.startswith('--property=DeviceAllow=/dev/nvidia')]
    assert gpu_nodes == ['--property=DeviceAllow=/dev/nvidia' + str(physical) + ' rw',
                        '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw']
    assert 'CUDA_VISIBLE_DEVICES=' + node4.DEVICES[physical] in command
    assert not any('*' in value for value in command)


@pytest.mark.parametrize('physical', [0, 1, 2, 3, 4, 8, -1, True, '5'])
def test_protected_or_invalid_slots_rejected(capsule, tmp_path, physical):
    with pytest.raises(ValueError):
        capsule.device_containment_command(physical, 5, 2524, 2524,
            node4.engine().new_unit(tmp_path / 'attempt'), '/source', ['/python'], 60)


@pytest.mark.parametrize('host', ['[REDACTED_HOST]', '[REDACTED_HOST]', 'other'])
def test_capsule_real_host_binding(capsule, host):
    capsule.socket = SimpleNamespace(gethostname=lambda: host)
    if host == node4.HOST:
        capsule.require_host()
    else:
        with pytest.raises(ValueError):
            capsule.require_host()


@pytest.mark.parametrize('physical', [5, 6, 7])
@pytest.mark.parametrize('failure', [None, 'allowed', 'missing', 'inherited', 'root', 'cgroup', 'mapping'])
def test_foreign_device_open_denials_required(capsule, tmp_path, physical, failure):
    unit = node4.engine().new_unit(tmp_path / 'attempt')
    capsule.require_host = lambda: None
    capsule.device_minor = lambda unused: physical if failure != 'mapping' else 2
    capsule.gpu_descriptors = lambda: [{}] if failure == 'inherited' else []
    capsule.Path = lambda unused: SimpleNamespace(read_text=lambda: '0::/system.slice/' +
        (unit if failure != 'cgroup' else 'foreign') + '.service')
    opened = []

    def open_device(path, flags):
        opened.append(path)
        if failure == 'allowed':
            return 100
        if failure == 'missing':
            raise FileNotFoundError(path)
        raise PermissionError(path)

    capsule.os = SimpleNamespace(getuid=lambda: 0 if failure == 'root' else 2524, getgid=lambda: 2524,
        open=open_device, close=Mock(), O_RDWR=os.O_RDWR, O_CLOEXEC=os.O_CLOEXEC,
        environ={'CUDA_VISIBLE_DEVICES': node4.DEVICES[physical]}, getpid=lambda: 123)
    config = dict(device_containment=dict(unit=unit, minor=physical, uid=2524, gid=2524))
    plan = dict(gpu_uuid=node4.DEVICES[physical])
    if failure:
        with pytest.raises((ValueError, FileNotFoundError)):
            capsule.verify_device_containment(config, plan)
    else:
        result = capsule.verify_device_containment(config, plan)
        assert result['denied_foreign_minors'] == [minor for minor in range(8) if minor != physical]
        assert len(opened) == 7


@pytest.fixture
def budget(tmp_path, monkeypatch):
    path = dump(tmp_path / 'prior.json', dict(hard_end_unix=1789754400, lease_end_unix=1789776000,
        lease_extended=False, safety_margin_seconds=21600))
    monkeypatch.setattr(node4, 'LEASE_PATH', path)
    monkeypatch.setattr(node4, 'LEASE_SHA256', node4.sha(path))
    cohort_path = dump(tmp_path / 'budget.json', dict(schema='R158_EXISTING_NODE4_COHORT_BUDGET_V1',
        derived_from=node4.reference(path), hard_end_unix=node4.WALL, lease_end_unix=1789776000,
        safety_margin_seconds=21600, lease_extended=False, existing_life_wall_changed=False,
        physical_devices=[5, 6, 7], host_sha256=node4.HOST_SHA256))
    config = dict(lease_path=str(cohort_path), lease_sha256=node4.sha(cohort_path),
        hard_end_unix=node4.WALL, next_reserved_unix=1789776000)
    plan = dict(hard_end_unix=node4.WALL, lease_end_unix=1789776000)
    return path, cohort_path, config, plan


def test_budget_preserves_prior_six_hour_reserve(budget):
    prior, path, config, plan = budget
    node4.verify_budget(config, plan)
    assert node4.WALL == 1789646400
    assert node4.WALL < node4.read(prior)['hard_end_unix']


@pytest.mark.parametrize('key,value', [('hard_end_unix', node4.WALL + 1),
    ('lease_end_unix', 1789776600), ('safety_margin_seconds', 600), ('lease_extended', True),
    ('existing_life_wall_changed', True), ('physical_devices', [0, 3, 4]),
    ('host_sha256', legacy.HOST_SHA256), ('schema', 'R151_EXISTING_NODE5_COHORT_BUDGET_V1')])
def test_wrong_budget_fails_even_when_rehashed(budget, key, value):
    prior, path, config, plan = budget
    document = node4.read(path)
    document[key] = value
    dump(path, document)
    config['lease_sha256'] = node4.sha(path)
    with pytest.raises(ValueError):
        node4.verify_budget(config, plan)


def test_matched_triplet_exact_common_recipe(tmp_path, budget):
    source = tmp_path / 'source'
    startup = source / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    startup.parent.mkdir(parents=True)
    startup.write_bytes((ROOT / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').read_bytes())
    plan_list, cohort, prior = node4.plans(source, tmp_path / 'cohort', budget[0])
    assert len(plan_list) == 3
    assert [(plan['matched_arm'], plan['physical']) for plan in plan_list] == list(node4.ARMS.items())
    for plan in plan_list:
        assert plan['seed'] == 0 and plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
        assert plan['segments_per_sleep'] == 2 and plan['presleep_variant'] == 'free_distillation'
        assert plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
        assert plan['anchor_lambda'] == 0.25 and plan['readout_revision'] == 1
        assert plan['initialization_validation_schema'] == 'R151_MATCHED_INITIAL_CAPACITY_V1'
        assert plan['birth_prompt'] == startup.read_text()
        assert plan['parent_enabled'] is (plan['matched_arm'] != 'unparented_learning')
    assert cohort['initial_optimizer_steps'] == 0 and cohort['fresh_histories'] is True
    assert cohort['initial_directory'] == str(tmp_path / 'cohort/common_initial')
    assert cohort['evaluations_gate_continuation'] is False
    assert not (tmp_path / 'cohort').exists()


def test_real_probe_profile_matches_node4_plan_without_mocking_callback(tmp_path, budget):
    source = tmp_path / 'source'
    startup = source / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    startup.parent.mkdir(parents=True)
    startup.write_bytes((ROOT / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').read_bytes())
    plans, unused_cohort, unused_prior = node4.plans(source, tmp_path / 'cohort', budget[0])
    plans[0]['source_root'] = '/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt4/source'
    receipt = node4.initializer_profile_preflight(plans[0])
    assert receipt['profile'] == 'R158_NODE4' and receipt['GPU_calls'] == 0
    assert receipt['numerical_capacity_proof'] is False
    for physical in (0, 6, 7):
        with pytest.raises(ValueError, match='initializer_only'):
            node4.initializer_profile_preflight(dict(plans[0], physical=physical))


@pytest.mark.skipif(ROOT.parent.parent != node4.BASE or not ROOT.parent.name.startswith('orch_r158_matched_node4_'),
                    reason='requires actual receiving node4 staged source and original receipt paths')
def test_receiving_actual_recovery_plan_profile_no_mock():
    from gpu import orch_r151_memory_probe as probe

    reference = ROOT.parent / 'INITIALIZATION_SOURCE.json'
    assert reference.is_file()
    plans, cohort, prior = node4.plans(ROOT, ROOT.parent, node4.LEASE_PATH, reference)
    assert plans[0]['source_root'] == str(ROOT)
    assert plans[0]['physical'] == 5 and plans[0]['gpu_uuid'] == node4.DEVICES[5]
    assert probe.initializer_profile(plans[0], node4.HOST) == 'R158_NODE4'
    assert node4.initializer_profile_preflight(plans[0])['profile'] == 'R158_NODE4'
    assert all(plan['initialization_source'] == cohort['common']['initialization_source'] for plan in plans)


def test_recovery_source_bound_identically_into_three_plans(tmp_path, budget, monkeypatch):
    from gpu import orch_r150_matched_native as matched

    source = tmp_path / 'source'
    startup = source / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    startup.parent.mkdir(parents=True)
    startup.write_bytes((ROOT / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').read_bytes())
    reference = dump(tmp_path / 'INITIALIZATION_SOURCE.json', {'fixture': 'CPU'})
    verifier = Mock()
    monkeypatch.setattr(matched, 'validate_initialization_source', verifier)
    plans, cohort, unused_prior = node4.plans(source, tmp_path / 'cohort', budget[0], reference)
    assert verifier.call_count == 3
    assert all(plan['initialization_source'] == node4.reference(reference) for plan in plans)
    assert cohort['common']['initialization_source'] == node4.reference(reference)


@pytest.fixture
def repairs(tmp_path):
    repository = tmp_path / 'repository'
    for name in node4.REPAIR_FILES:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('bound_file = True\n')
    log = tmp_path / 'tests.log'
    log.write_text('42 passed\n')
    proof = dict(schema='R158_MATCHED_REPAIR_REVIEW_V1', status='PASS', issuer='Banach',
        freeze_allowed=True, capacity_consumer_fixed=True, deadline_cleanup_fixed=True,
        failure_receipts_fixed=True, files=node4.inventory(repository),
        tests=dict(exit_code=0, passed=42, logs=[node4.reference(log)]))
    path = dump(tmp_path / 'repairs.json', proof)
    return repository, path, proof


def test_repairs_require_actual_log_and_file_bytes(repairs):
    repository, path, proof = repairs
    assert node4.verify_repairs(path, repository) == proof
    (repository / node4.REPAIR_FILES[0]).write_text('changed = True\n')
    with pytest.raises(ValueError, match='actual_repaired_source'):
        node4.verify_repairs(path, repository)


@pytest.mark.parametrize('key,value', [('status', 'PENDING'), ('freeze_allowed', 'not_boolean'),
    ('capacity_consumer_fixed', False), ('deadline_cleanup_fixed', False),
    ('failure_receipts_fixed', False), ('issuer', 'unreviewed')])
def test_source_not_staged_before_repairs(repairs, monkeypatch, tmp_path, key, value):
    repository, path, proof = repairs
    proof[key] = value
    dump(path, proof)
    from gpu import orch_r151_matched_stage as staging
    stage = Mock(side_effect=AssertionError('must not stage'))
    monkeypatch.setattr(staging, 'stage_source', stage)
    with pytest.raises(ValueError):
        node4.stage_source(repository, tmp_path / 'destination', tmp_path / 'runtime',
            tmp_path / 'proof', CAPSULE, path)
    stage.assert_not_called()
    assert not (tmp_path / 'destination').exists()


def test_draft_staging_cannot_freeze_without_Main_dispositions(repairs):
    repository, path, proof = repairs
    proof.update(issuer='Builder', freeze_allowed=False)
    dump(path, proof)
    node4.verify_repairs(path, repository)
    with pytest.raises(ValueError, match='Main_review_dispositions'):
        node4.verify_repairs(path, repository, require_freeze=True)
    proof.update(issuer='Main', freeze_allowed=True, review_disposition='APPROVED_FOR_FREEZE',
                 review_receipts=proof['tests']['logs'])
    dump(path, proof)
    node4.verify_repairs(path, repository, require_freeze=True)


def test_staged_inventory_includes_split_ledger_and_preserved_original_manifest(repairs, monkeypatch, tmp_path):
    from gpu import orch_r151_matched_stage as staging
    repository, path, proof = repairs

    def fake_original_stage(repository, destination, runtime, proof_path):
        destination.mkdir()
        for source in repository.rglob('*.py'):
            target = destination / source.relative_to(repository)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        node4.write(destination / 'STAGED_SOURCE.json', dict(files=node4.inventory(destination)))
        return {'status': 'test_fixture_original_stage'}

    monkeypatch.setattr(staging, 'stage_source', fake_original_stage)
    destination = tmp_path / 'candidate/source'
    destination.parent.mkdir()
    node4.stage_source(repository, destination, tmp_path / 'runtime', tmp_path / 'proof', CAPSULE, path)
    manifest = node4.read(destination / 'STAGED_SOURCE.json')
    expected = node4.inventory(destination)
    expected.pop('STAGED_SOURCE.json')
    assert manifest['files'] == expected
    assert manifest['files']['organism_v6/reasoning_gym_families.json'] == node4.sha(repository / 'organism_v6/reasoning_gym_families.json')
    assert manifest['files']['organism_v6/bootstrap_reasoning_gym.txt'] == node4.sha(repository / 'organism_v6/bootstrap_reasoning_gym.txt')
    assert manifest['constructor_bootstrap']['child_startup_use'] is False
    assert node4.bound(manifest['original_staging_manifest'])['files']
    assert 'gpu/orch_r158_train_gym.py' in manifest['files']
    assert not (destination.parent / 'common_initial').exists()


def test_constructor_bootstrap_is_required_and_cannot_be_omitted_from_review(repairs):
    repository, path, proof = repairs
    assert 'organism_v6/bootstrap_reasoning_gym.txt' in node4.REPAIR_FILES
    proof['files'].pop('organism_v6/bootstrap_reasoning_gym.txt')
    dump(path, proof)
    with pytest.raises(ValueError, match='repair_core_and_regression_source_pins'):
        node4.verify_repairs(path, repository)


@pytest.fixture
def recheck(tmp_path, monkeypatch):
    attempt = tmp_path / 'attempt'
    attempt.mkdir()
    plan = dict(gpu_uuid=node4.DEVICES[5])
    plan_path = dump(tmp_path / 'PLAN.json', plan)
    config = dict(plan_path=str(plan_path), attempt_dir=str(attempt), device_containment=dict(minor=6))
    config_path = dump(tmp_path / 'GUARD.json', config)
    command = ['sudo', '-n', '/usr/bin/env', '-i', '/python', '-B', '-m',
               'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
    report = dict(scanner_euid=0, clear=False, host_sha256=node4.HOST_SHA256, device_minor=6,
        gpu=dict(uuid=plan['gpu_uuid'], memory_used_mib=0, utilization_percent=0),
        blocking_reasons=['process_identity_drift:123'],
        processes=[dict(pid=123, target_device_open=False, cvd=None)], compute_processes=[])
    monkeypatch.setattr(node4.time, 'sleep', lambda seconds: None)
    return SimpleNamespace(attempt=attempt, plan=plan, config=config, command=command, report=report)


def execute_rechecks(fixture):
    return node4.scan_with_transient_rechecks(fixture.command, receipt_dir=fixture.attempt,
        env={'CUDA_VISIBLE_DEVICES': ''}, text=True, stdout=subprocess.PIPE, stderr=None, timeout=100)


def test_transient_scan_then_fresh_clear_preserves_both_reports(recheck, monkeypatch):
    first = subprocess.CompletedProcess(recheck.command, 0, json.dumps(recheck.report))
    clear = dict(recheck.report, clear=True, blocking_reasons=[])
    second = subprocess.CompletedProcess(recheck.command, 0, json.dumps(clear))
    runner = Mock(side_effect=[first, second])
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    assert execute_rechecks(recheck) is second
    assert runner.call_count == 2
    output = recheck.attempt / 'ADMISSION_OBSERVATIONS'
    assert (output / '000.stdout').read_text() == first.stdout
    assert (output / '001.stdout').read_text() == second.stdout
    assert json.loads(first.stdout)['clear'] is False
    assert runner.call_args_list[0].args[0] == runner.call_args_list[1].args[0] == recheck.command
    assert all(0 < call.kwargs['timeout'] <= 60 for call in runner.call_args_list)
    node4.engine().check_admission(clear, recheck.config, recheck.plan, node4.time.time())


def test_eight_failed_observations_never_become_admitted(recheck, monkeypatch):
    refused = subprocess.CompletedProcess(recheck.command, 0, json.dumps(recheck.report))
    runner = Mock(return_value=refused)
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    assert execute_rechecks(recheck) is refused
    assert runner.call_count == 8
    assert len(list((recheck.attempt / 'ADMISSION_OBSERVATIONS').glob('*.stdout'))) == 8
    with pytest.raises(ValueError, match='fresh_exclusive_admission'):
        node4.engine().check_admission(json.loads(refused.stdout), recheck.config, recheck.plan, node4.time.time())


@pytest.mark.parametrize('change', [
    {'blocking_reasons': ['foreign_device_open:123']},
    {'blocking_reasons': ['process_identity_drift:123', 'unknown_visibility']},
    {'blocking_reasons': ['process_identity_drift:not-a-pid']},
    {'blocking_reasons': ['minor_scan_identity_changed:123']},
    {'blocking_reasons': []},
    {'scanner_euid': 2524}, {'device_minor': 5}, {'host_sha256': 'wrong'},
    {'processes': []}, {'processes': [None]},
    {'processes': [dict(pid=123, target_device_open=True, cvd=None)]},
    {'processes': [dict(pid=123, cvd=None)]},
    {'processes': [dict(pid=123, target_device_open=False, cvd='GPU-other')]},
    {'processes': [dict(pid=123, target_device_open=False, cvd='5')]},
    {'compute_processes': [dict(pid=123, gpu_uuid='other')]},
    {'compute_processes': [dict(pid=999, gpu_uuid=node4.DEVICES[5])]},
    {'gpu': dict(uuid=node4.DEVICES[5], memory_used_mib=1, utilization_percent=0)},
    {'gpu': dict(uuid=node4.DEVICES[5], memory_used_mib=0, utilization_percent=1)},
    {'gpu': dict(uuid='wrong', memory_used_mib=0, utilization_percent=0)},
])
def test_nontransient_or_uncertain_snapshot_not_repeated(recheck, monkeypatch, change):
    report = dict(recheck.report, **change)
    result = subprocess.CompletedProcess(recheck.command, 0, json.dumps(report))
    runner = Mock(return_value=result)
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    assert execute_rechecks(recheck) is result
    assert runner.call_count == 1


@pytest.mark.parametrize('returncode,raw', [(1, 'error'), (0, 'not-json')])
def test_scanner_error_or_malformed_output_not_repeated(recheck, monkeypatch, returncode, raw):
    result = subprocess.CompletedProcess(recheck.command, returncode, raw)
    runner = Mock(return_value=result)
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    if returncode:
        assert execute_rechecks(recheck) is result
    else:
        with pytest.raises(json.JSONDecodeError):
            execute_rechecks(recheck)
    assert runner.call_count == 1
    assert (recheck.attempt / 'ADMISSION_OBSERVATIONS/000.stdout').read_text() == raw


def test_timeout_is_preserved_without_retry(recheck, monkeypatch):
    runner = Mock(side_effect=subprocess.TimeoutExpired(recheck.command, 1, output='partial'))
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    with pytest.raises(subprocess.TimeoutExpired):
        execute_rechecks(recheck)
    assert runner.call_count == 1
    assert node4.read(recheck.attempt / 'ADMISSION_OBSERVATIONS/000_ERROR.json')['retried'] is False


def test_rechecks_cannot_extend_original_scan_deadline(recheck, monkeypatch):
    runner = Mock(return_value=subprocess.CompletedProcess(recheck.command, 0, json.dumps(recheck.report)))
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    monkeypatch.setattr(node4.time, 'monotonic', Mock(side_effect=[100.0, 100.0, 160.0]))
    assert execute_rechecks(recheck) is runner.return_value
    assert runner.call_count == 1


def test_rechecks_cannot_overwrite_earlier_observations(recheck, monkeypatch):
    runner = Mock(return_value=subprocess.CompletedProcess(recheck.command, 0,
        json.dumps(dict(recheck.report, clear=True, blocking_reasons=[]))))
    monkeypatch.setattr(node4.subprocess, 'run', runner)
    execute_rechecks(recheck)
    with pytest.raises(FileExistsError):
        execute_rechecks(recheck)
    assert runner.call_count == 1


def test_unknown_supervisor_scan_shape_rejected():
    source = (ROOT / 'gpu/orch_r151_matched_containment.py').read_text()
    changed = source.replace('subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE,',
                             'subprocess.run(other_command, env=environment, text=True, stdout=subprocess.PIPE,')
    assert changed != source
    with pytest.raises(ValueError, match='exact_privileged_scan_call'):
        node4.profile_tree(changed)


def test_cpu_gate_requires_exact_source_host_and_logs(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'module.py').write_text('pass\n')
    log = tmp_path / 'CPU.log'
    log.write_text('42 passed\n')
    path = dump(tmp_path / 'CPU.json', dict(status='PASS', exit_code=0, host=node4.HOST,
        passed=42, source_inventory=node4.inventory(source), logs=[node4.reference(log)]))
    node4.verify_cpu(path, source)
    (source / 'module.py').write_text('changed = True\n')
    with pytest.raises(ValueError, match='actual_receiving_CPU_source_gate'):
        node4.verify_cpu(path, source)


def test_exclusive_phase_never_replayed_or_simultaneous(tmp_path, monkeypatch):
    monkeypatch.setattr(node4, 'BASE', tmp_path)
    base = tmp_path / 'cohort'
    (base / 'control').mkdir(parents=True)
    config = dict(r158_base=str(base), phase='initialize', matched_arm='parented_learning')
    plan = dict(physical=5, matched_arm='parented_learning')
    with node4.exclusive_phase(config, plan):
        with pytest.raises(BlockingIOError):
            with node4.exclusive_phase(dict(config, phase='run'), plan):
                pytest.fail('cannot share initializer device')
    with pytest.raises(FileExistsError):
        with node4.exclusive_phase(config, plan):
            pytest.fail('cannot repeat phase')
    with node4.exclusive_phase(dict(config, phase='run'), plan):
        pass


def test_supervisor_calls_actual_proven_machinery_only_after_all_gates(tmp_path, monkeypatch):
    config = dict(r158_base=str(tmp_path), phase='initialize', matched_arm='parented_learning')
    (tmp_path / 'control').mkdir()
    plan = dict(physical=5, matched_arm='parented_learning')
    compiled = SimpleNamespace(validate=Mock(), supervise=Mock(return_value='executed'))
    monkeypatch.setattr(node4, 'engine', lambda: compiled)
    monkeypatch.setattr(node4, 'validate_extra', Mock(return_value=(config, plan)))
    monkeypatch.setattr(node4, 'BASE', tmp_path)
    monkeypatch.setattr(node4.os, 'getuid', lambda: 2524)
    monkeypatch.setattr(node4.os, 'getgid', lambda: 2524)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    assert node4.execute('supervise', '/config', '/attempt', '/GO', 'bound') == 'executed'
    compiled.supervise.assert_called_once_with('/config', receipt_dir='/attempt', main_go_path='/GO',
                                              main_go_sha256='bound')


def test_no_GO_no_dispatch(monkeypatch):
    compiled = SimpleNamespace(validate=Mock(side_effect=ValueError('not approved')), supervise=Mock())
    monkeypatch.setattr(node4, 'engine', lambda: compiled)
    with pytest.raises(ValueError, match='not approved'):
        node4.execute('supervise', '/config', '/attempt', '/GO', 'wrong')
    compiled.supervise.assert_not_called()


@pytest.fixture
def go_case(tmp_path):
    profile = node4.engine()
    profile.time = SimpleNamespace(time=lambda: node4.WALL - 600)
    config = {key + '_sha256': 'a' * 64 for key in
        ('plan', 'lease', 'allocation', 'source_manifest', 'cpu_gate', 'intake', 'matched_cohort')}
    config.update(boot_id='test-boot', phase='initialize', matched_arm='parented_learning', resume=False,
        device_containment=dict(uid=2524, gid=2524, minor=5, unit='test-only'),
        attempt_dir=str(tmp_path / 'attempt'), hard_end_unix=node4.WALL)
    plan = dict(physical=5, gpu_uuid=node4.DEVICES[5])
    binding = profile.go_binding(config, plan, 'b' * 64)
    document = dict(schema='R158_MAIN_GO_V1', decision='GO', issuer='Main', binding=binding,
                    not_before_unix=node4.WALL - 1000, expires_unix=node4.WALL - 100)
    path = dump(tmp_path / 'test_GO.json', document)
    return profile, config, plan, document, path


def test_phase_GO_is_node4_exact_and_time_bounded(go_case):
    profile, config, plan, document, path = go_case
    assert document['binding']['allowed_physical'] == [5, 6, 7]
    assert document['binding']['host_sha256'] == node4.HOST_SHA256
    assert document['binding']['requested_scope'] == node4.SCOPE
    profile.validate_go(config, plan, 'b' * 64, path, node4.sha(path))


@pytest.mark.parametrize('key,value', [('schema', 'R151_MAIN_GO_V1'), ('decision', 'HOLD'),
    ('issuer', 'Builder'), ('not_before_unix', node4.WALL), ('expires_unix', node4.WALL - 601),
    ('expires_unix', node4.WALL + 1)])
def test_even_rehashed_Main_GO_rejects_wrong_schema_or_time(go_case, key, value):
    profile, config, plan, document, path = go_case
    document[key] = value
    dump(path, document)
    with pytest.raises(ValueError):
        profile.validate_go(config, plan, 'b' * 64, path, node4.sha(path))


@pytest.mark.parametrize('key,value', [('allowed_physical', [0, 3, 4]), ('physical', 2),
    ('gpu_uuid', node4.DEVICES[7]), ('phase', 'run'), ('matched_arm', 'parented_frozen'),
    ('resume', True), ('host_sha256', legacy.HOST_SHA256), ('requested_scope', legacy.SCOPE)])
def test_even_rehashed_GO_cannot_change_scope_or_phase(go_case, key, value):
    profile, config, plan, document, path = go_case
    document['binding'][key] = value
    dump(path, document)
    with pytest.raises(ValueError, match='exact_main_GO_scope'):
        profile.validate_go(config, plan, 'b' * 64, path, node4.sha(path))


@pytest.fixture
def extra_case(tmp_path, monkeypatch):
    base = tmp_path / 'orch_r158_matched_node4_fixture'
    source = base / 'source'
    source.mkdir(parents=True)
    source.chmod(0o555)
    monkeypatch.setattr(node4, 'BASE', tmp_path)
    monkeypatch.setattr(node4, 'bound', lambda value: node4.read(value['path']))
    monkeypatch.setattr(node4, 'verify_cpu', Mock())
    monkeypatch.setattr(node4, 'verify_repairs', Mock())
    cohort = dict(initial_directory=str(base / 'common_initial'))
    cohort_path = dump(base / 'COHORT.json', cohort)
    plan = dict(root=str(base / 'parented_learning'), source_root=str(source), physical=5,
                gpu_uuid=node4.DEVICES[5], matched_arm='parented_learning', matched_cohort=node4.reference(cohort_path))
    plan_path = dump(base / 'PLAN.json', plan)
    placeholder = node4.reference(dump(base / 'test_receipt.json', {}))
    config = dict(r158_base=str(base), plan_path=str(plan_path), resume=False, phase='initialize',
                  r158_repairs=placeholder, r158_cpu=placeholder)
    config_path = dump(base / 'GUARD.json', config)
    go_path = dump(base / 'GO.json', dict(initialization=None))
    return base, config_path, plan_path, go_path, config, plan


def test_initializer_extra_gate_refuses_any_existing_initial_state(extra_case):
    base, config_path, plan_path, go_path, config, plan = extra_case
    assert node4.validate_extra(config_path, go_path) == (config, plan)
    (base / 'common_initial').mkdir()
    with pytest.raises(ValueError, match='initializer_once_no_existing_state'):
        node4.validate_extra(config_path, go_path)


@pytest.mark.parametrize('phase_status', [None, 'missing', 'not_empty', 'nonzero', 'unbound', 'success'])
def test_lane_extra_gate_requires_actual_initializer_success_and_empty_cgroup(extra_case, monkeypatch, phase_status):
    from gpu import orch_r150_matched_native as matched
    base, config_path, plan_path, go_path, config, plan = extra_case
    config['phase'] = 'run'
    dump(config_path, config)
    initial = base / 'common_initial'
    initialized = dump(initial / 'INITIALIZED.json', {'fixture': 'capacity validated separately'})
    commit = dump(initial / 'COMMIT.json', {})
    lifecycle = dump(base / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json',
        dict(status='SERVICE_EXIT_VERIFIED', cgroup_empty_verified=phase_status != 'not_empty',
             service_returncode=1 if phase_status == 'nonzero' else 0))
    proof = dict(initialized=node4.reference(initialized), commit=node4.reference(commit),
                 lifecycle=node4.reference(lifecycle))
    if phase_status == 'missing':
        proof.pop('lifecycle')
    elif phase_status == 'unbound':
        proof['commit']['sha256'] = '0' * 64
    dump(go_path, dict(initialization=None if phase_status is None else proof))
    checked = Mock()
    monkeypatch.setattr(matched, 'verify_initialization_validation', checked)
    if phase_status == 'success':
        node4.validate_extra(config_path, go_path)
        checked.assert_called_once()
    else:
        with pytest.raises((ValueError, TypeError)):
            node4.validate_extra(config_path, go_path)
        checked.assert_not_called()


def test_inventory_rejects_symlink(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'linked').symlink_to('/etc/passwd')
    with pytest.raises(ValueError):
        node4.inventory(source)
