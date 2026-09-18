"""CPU-only containment regressions. No real systemd, scanner, GPU, or model calls."""

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r151_matched_containment as sidecar


ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / 'research_loop/workers/r143_node5_allocator_20260916t1427z/CONFINEMENT_API.py'


def dump(path, document):
    path.write_text(json.dumps(document, sort_keys=True))


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    monkeypatch.setattr(sidecar.subprocess, 'run', Mock(side_effect=AssertionError('no real subprocess')))
    monkeypatch.setattr(sidecar.subprocess, 'Popen', Mock(side_effect=AssertionError('no real service')))


def test_pure_capsule_preserves_every_successful_function_and_only_devices(tmp_path):
    before = CAPSULE.read_bytes()
    after = sidecar.render_capsule(before)
    old_tree, new_tree = ast.parse(before), ast.parse(after)
    for old, new in zip(old_tree.body, new_tree.body):
        if isinstance(old, ast.Assign) and old.targets[0].id == 'DEVICES':
            continue
        assert ast.dump(old) == ast.dump(new)
        assert ast.get_source_segment(before.decode(), old) == ast.get_source_segment(after.decode(), new)
    path = tmp_path / 'CAPSULE.py'
    path.write_bytes(after)
    assert sidecar.load_capsule(path).DEVICES == sidecar.DEVICES
    assert CAPSULE.read_bytes() == before


@pytest.mark.parametrize('mutate', [lambda data: data + b'\n', lambda data: b'',
                                  lambda data: data.replace(b"DevicePolicy='strict'", b"DevicePolicy='auto'")])
def test_reject_capsule_drift(mutate, tmp_path):
    with pytest.raises(ValueError):
        sidecar.render_capsule(mutate(CAPSULE.read_bytes()))
    path = tmp_path / 'capsule.py'
    path.write_bytes(mutate(sidecar.render_capsule(CAPSULE.read_bytes())))
    with pytest.raises(ValueError):
        sidecar.load_capsule(path)


def test_guard_uses_pure_exact_patcher_and_keeps_original(tmp_path):
    from gpu import orch_r151_matched_stage as staging
    original = (ROOT / sidecar.GUARD).read_bytes()
    result = sidecar.render_guard(original)
    assert result == staging.patch_guard(original.decode()).encode()
    assert sidecar.digest(result) == sidecar.R151_GUARD_SHA256
    assert sidecar.digest(result) != sidecar.R150_PARENT_GUARD_SHA256
    assert (ROOT / sidecar.GUARD).read_bytes() == original
    for invalid in [result, original + b'\n', b'']:
        with pytest.raises(ValueError):
            sidecar.render_guard(invalid)


@pytest.fixture
def capsule(tmp_path):
    path = tmp_path / 'capsule.py'
    path.write_bytes(sidecar.render_capsule(CAPSULE.read_bytes()))
    return sidecar.load_capsule(path)


@pytest.mark.parametrize('physical', [0, 3, 4])
def test_command_preserves_strict_single_minor_and_clean_allocator(capsule, tmp_path, physical):
    command = capsule.device_containment_command(physical, 5, 2524, 2524,
              sidecar.new_unit(tmp_path / 'attempt'), '/new/source',
              ['PYTORCH_CUDA_ALLOC_CONF=' + sidecar.ALLOCATOR, '/python', '-B'], 60)
    assert '--property=DevicePolicy=strict' in command
    assert '--property=DeviceAllow=' in command
    assert '--property=CapabilityBoundingSet=' in command
    assert '--property=AmbientCapabilities=' in command
    assert '--property=ProtectControlGroups=yes' in command
    assert '--property=NoNewPrivileges=yes' in command
    assert '--property=KillMode=control-group' in command
    assert '--property=RuntimeMaxSec=60' in command
    gpu_nodes = [item for item in command if item.startswith('--property=DeviceAllow=/dev/nvidia')]
    assert gpu_nodes == ['--property=DeviceAllow=/dev/nvidia5 rw',
                         '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw']
    assert not any('*' in item for item in command)
    assert '/usr/bin/env' in command and '-i' in command
    assert 'CUDA_VISIBLE_DEVICES=' + sidecar.DEVICES[physical] in command
    assert 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True' in command


@pytest.mark.parametrize('physical', [1, 2, 5, 6, 7, True, '0', -1])
def test_protected_slots_never_reach_command(capsule, physical, tmp_path):
    with pytest.raises(ValueError):
        capsule.device_containment_command(physical, 0, 2524, 2524,
              sidecar.new_unit(tmp_path / 'attempt'), '/source', ['/python'], 60)


def test_capsule_live_mapping_is_uuid_not_physical(capsule, tmp_path):
    information = tmp_path / 'gpus' / '0000:57:00.0' / 'information'
    information.parent.mkdir(parents=True)
    information.write_text('GPU UUID: ' + sidecar.DEVICES[3] + '\nDevice Minor: 5\n')
    node = SimpleNamespace(lstat=lambda: SimpleNamespace(st_mode=0o020600, st_rdev=os.makedev(195, 5)))
    capsule.Path = lambda value: tmp_path / 'gpus' if value == '/proc/driver/nvidia/gpus' else node
    assert capsule.device_minor(sidecar.DEVICES[3]) == 5
    information.write_text('GPU UUID: unknown\nDevice Minor: 3\n')
    with pytest.raises(ValueError, match='one_kernel_UUID_minor_mapping'):
        capsule.device_minor(sidecar.DEVICES[3])


@pytest.mark.parametrize('failure', [None, 'open', 'missing', 'inherited', 'mapping', 'cgroup', 'root', 'cvd'])
def test_all_foreign_opens_must_be_permission_denied(capsule, tmp_path, failure):
    unit = sidecar.new_unit(tmp_path / 'attempt')
    config = dict(device_containment=dict(unit=unit, minor=3, uid=2524, gid=2524))
    plan = dict(gpu_uuid=sidecar.DEVICES[3])
    capsule.require_host = lambda: None
    capsule.device_minor = lambda unused: 4 if failure == 'mapping' else 3
    capsule.gpu_descriptors = lambda: [{}] if failure == 'inherited' else []
    capsule.Path = lambda unused: SimpleNamespace(read_text=lambda: '0::/system.slice/' +
                         (unit if failure != 'cgroup' else 'foreign') + '.service')
    opened = []

    def attempt_open(path, flags):
        opened.append(path)
        if failure == 'open':
            return 123
        if failure == 'missing':
            raise FileNotFoundError(path)
        raise PermissionError(path)

    capsule.os = SimpleNamespace(getuid=lambda: 0 if failure == 'root' else 2524, getgid=lambda: 2524,
                 open=attempt_open, close=Mock(), O_RDWR=os.O_RDWR, O_CLOEXEC=os.O_CLOEXEC,
                 environ={'CUDA_VISIBLE_DEVICES': '' if failure == 'cvd' else plan['gpu_uuid']}, getpid=lambda: 100)
    if failure:
        with pytest.raises((ValueError, FileNotFoundError)):
            capsule.verify_device_containment(config, plan)
    else:
        receipt = capsule.verify_device_containment(config, plan)
        assert receipt['denied_foreign_minors'] == [0, 1, 2, 4, 5, 6, 7]
        assert opened == ['/dev/nvidia' + str(minor) for minor in [0, 1, 2, 4, 5, 6, 7]]


@pytest.fixture
def staged(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    for name in [sidecar.GUARD, sidecar.STAGING_PATCHER, sidecar.MEMORY_PROBE, *sidecar.PINNED_SCANNER]:
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = (ROOT / name).read_bytes()
        destination.write_bytes(sidecar.render_guard(data) if name == sidecar.GUARD else data)
    module_path = source / 'gpu/orch_r151_matched_containment.py'
    module_path.write_bytes((ROOT / 'gpu/orch_r151_matched_containment.py').read_bytes())
    capsule_path = source / 'CONFINEMENT_API.py'
    capsule_path.write_bytes(sidecar.render_capsule(CAPSULE.read_bytes()))
    monkeypatch.setattr(sidecar, '__file__', str(module_path))
    monkeypatch.setattr(sidecar.socket, 'gethostname', lambda: sidecar.HOST)
    boot = tmp_path / 'boot'
    boot.write_text('known-boot')
    monkeypatch.setattr(sidecar, 'BOOT_ID', boot)
    monkeypatch.setattr(sidecar.time, 'time', lambda: 1000)
    attempt = tmp_path / 'attempt'
    cohort_path = tmp_path / 'cohort.json'
    dump(cohort_path, dict(initial_directory=str(tmp_path / 'initial')))
    plan = dict(source_root=str(source), physical=3, gpu_uuid=sidecar.DEVICES[3], root=str(tmp_path / 'readouts'),
                matched_arm='parented_learning', matched_cohort=dict(path=str(cohort_path), sha256=sidecar.sha(cohort_path)),
                hard_end_unix=2000, lease_end_unix=2600,
                initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
    config = dict(schema='R125_CONTINUAL_GUARD_V1', host_sha256=sidecar.HOST_SHA256, requested_scope=sidecar.SCOPE,
                  boot_id='known-boot', attempt_dir=str(attempt), phase='run', resume=False,
                  matched_arm=plan['matched_arm'], matched_cohort_sha256=plan['matched_cohort']['sha256'],
                  hard_end_unix=2000, next_reserved_unix=2200, allocator=sidecar.ALLOCATOR,
                  device_containment=dict(uid=2524, gid=2524, minor=5, unit=sidecar.new_unit(attempt)))
    original_lease = tmp_path / 'prior_lease.json'
    dump(original_lease, dict(lease_end_unix=2600, hard_end_unix=2000))
    monkeypatch.setattr(sidecar, 'EXISTING_LEASE_SHA256', sidecar.sha(original_lease))
    budget = dict(schema='R151_EXISTING_NODE5_COHORT_BUDGET_V1', physical_devices=[0, 3, 4],
                  host_sha256=sidecar.HOST_SHA256, lease_extended=False, existing_life_wall_changed=False,
                  safety_margin_seconds=600, derived_from=dict(path=str(original_lease), sha256=sidecar.sha(original_lease)),
                  lease_end_unix=2600, hard_end_unix=2000)
    documents = dict(plan=plan, lease=budget, allocation={'cpu_tests_passed': True},
                     source_manifest={'files': sidecar.source_inventory(source)}, intake={'approved': True})
    for name, document in documents.items():
        path = tmp_path / (name + '.json')
        dump(path, document)
        config[name + '_path'], config[name + '_sha256'] = str(path), sidecar.sha(path)
    gate_path = tmp_path / 'cpu_gate.json'
    from gpu import orch_r151_matched_stage as staging
    monkeypatch.setattr(staging, '__file__', str(source / sidecar.STAGING_PATCHER))
    pins = documents['source_manifest']['files']
    review = dict(status='PASS', original_guard_sha256=sidecar.ORIGINAL_GUARD_SHA256,
                  r150_parent_guard_sha256=sidecar.R150_PARENT_GUARD_SHA256,
                  guard_sha256=pins[sidecar.GUARD], patcher_sha256=pins[sidecar.STAGING_PATCHER],
                  memory_probe_sha256=pins[sidecar.MEMORY_PROBE],
                  initialize_callback='gpu.orch_r151_memory_probe.initial_capacity',
                  original_checks_preserved=True, run_dispatch_unchanged=True)
    dump(gate_path, dict(status='PASS', source_manifest_sha256=config['source_manifest_sha256'],
                        matched_cohort_sha256=config['matched_cohort_sha256'], guard_derivation=review))
    config.update(cpu_gate_path=str(gate_path), cpu_gate_sha256=sidecar.sha(gate_path),
                  capsule_path=str(capsule_path), capsule_sha256=sidecar.sha(capsule_path),
                  source_pins=documents['source_manifest']['files'])
    config_path, go_path = tmp_path / 'guard.json', tmp_path / 'main_go.json'
    dump(config_path, config)
    go = dict(schema='R151_MAIN_GO_V1', issuer='Main', decision='GO', not_before_unix=999, expires_unix=1500,
              binding=sidecar.go_binding(config, plan, sidecar.sha(config_path)))
    dump(go_path, go)
    capsule = sidecar.load_capsule(capsule_path)
    capsule.device_minor = Mock(return_value=5)
    monkeypatch.setattr(sidecar, 'load_capsule', lambda unused: capsule)
    guard = SimpleNamespace(__file__=str(source / sidecar.GUARD), validate=Mock(return_value=(config, plan)))
    monkeypatch.setattr(sidecar.importlib, 'import_module', Mock(return_value=guard))
    return SimpleNamespace(source=source, attempt=attempt, config=config, config_path=config_path,
                           plan=plan, go=go, go_path=go_path, capsule=capsule, guard=guard,
                           args=dict(receipt_dir=attempt, main_go_path=go_path, main_go_sha256=sidecar.sha(go_path)))


def rebind(staged):
    dump(staged.config_path, staged.config)
    staged.go['binding'] = sidecar.go_binding(staged.config, staged.plan, sidecar.sha(staged.config_path))
    dump(staged.go_path, staged.go)
    staged.args['main_go_sha256'] = sidecar.sha(staged.go_path)


def check_staged(staged):
    return sidecar.validate(staged.config_path, staged.attempt, staged.go_path, staged.args['main_go_sha256'])


def test_validate_keeps_original_guard_and_real_minor(staged):
    assert check_staged(staged) == (staged.config, staged.plan, staged.capsule, staged.guard)
    staged.guard.validate.assert_called_once_with(staged.config_path)
    staged.capsule.device_minor.assert_called_once_with(sidecar.DEVICES[3])


@pytest.mark.parametrize('field,value', [
    ('host_sha256', '0' * 64), ('boot_id', 'other-boot'), ('requested_scope', 'all_gpus'),
    ('phase', 'eval'), ('resume', 'false'), ('allocator', ''), ('matched_arm', 'other'),
    ('matched_cohort_sha256', '0' * 64), ('hard_end_unix', 1010),
])
def test_invalid_config_never_imports_guard(staged, field, value):
    staged.config[field] = value
    rebind(staged)
    with pytest.raises(ValueError):
        check_staged(staged)
    staged.guard.validate.assert_not_called()


@pytest.mark.parametrize('field,value', [('uid', 0), ('gid', 0), ('uid', 2524.0), ('minor', 3), ('minor', True),
                                       ('unit', 'orch-r136-native-' + '0' * 32)])
def test_rehashed_policy_drift_rejected(staged, field, value):
    staged.config['device_containment'][field] = value
    rebind(staged)
    with pytest.raises(ValueError):
        check_staged(staged)


@pytest.mark.parametrize('physical', [1, 2, 5, 6, 7, True])
def test_rehashed_protected_allocation_rejected(staged, physical):
    staged.plan['physical'] = physical
    dump(Path(staged.config['plan_path']), staged.plan)
    staged.config['plan_sha256'] = sidecar.sha(staged.config['plan_path'])
    rebind(staged)
    with pytest.raises(ValueError, match='only_node5'):
        check_staged(staged)


@pytest.mark.parametrize('name', ['plan', 'lease', 'allocation', 'intake', 'source_manifest', 'cpu_gate', 'capsule'])
def test_every_input_byte_hash_checked(staged, name):
    with Path(staged.config[name + '_path']).open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError):
        check_staged(staged)


@pytest.mark.parametrize('mutation', ['python', 'nonpython', 'symlink', 'scanner_repin'])
def test_whole_source_not_just_guard_bound(staged, mutation):
    if mutation == 'python':
        (staged.source / 'extra.py').write_text('')
    elif mutation == 'nonpython':
        (staged.source / 'extra.json').write_text('{}')
    elif mutation == 'symlink':
        (staged.source / 'link.py').symlink_to(staged.source / sidecar.GUARD)
    else:
        name = next(iter(sidecar.PINNED_SCANNER))
        (staged.source / name).write_text('')
        inventory = sidecar.source_inventory(staged.source)
        dump(Path(staged.config['source_manifest_path']), dict(files=inventory))
        staged.config.update(source_manifest_sha256=sidecar.sha(staged.config['source_manifest_path']), source_pins=inventory)
        rebind(staged)
    with pytest.raises(ValueError):
        check_staged(staged)


@pytest.mark.parametrize('mutation', ['hash', 'decision', 'issuer', 'expired', 'future', 'scope', 'config'])
def test_main_GO_cannot_be_inferred(staged, mutation):
    if mutation == 'hash':
        staged.args['main_go_sha256'] = '0' * 64
    else:
        if mutation == 'decision':
            staged.go['decision'] = 'READY'
        elif mutation == 'issuer':
            staged.go['issuer'] = 'sidecar'
        elif mutation == 'expired':
            staged.go['expires_unix'] = 1000
        elif mutation == 'future':
            staged.go['not_before_unix'] = 1001
        elif mutation == 'scope':
            staged.go['binding']['allowed_physical'] = [0, 1, 3, 4]
        else:
            staged.go['binding']['config_sha256'] = '0' * 64
        dump(staged.go_path, staged.go)
        staged.args['main_go_sha256'] = sidecar.sha(staged.go_path)
    with pytest.raises(ValueError):
        check_staged(staged)
    staged.guard.validate.assert_not_called()


def report(staged):
    return dict(scanner_euid=0, clear=True, blocking_reasons=[], gpu={'uuid': staged.plan['gpu_uuid']},
                host_sha256=sidecar.HOST_SHA256, device_minor=5)


@pytest.mark.parametrize('age,accepted', [(0, True), (120, True), (120.001, False), (-0.001, False)])
def test_admission_freshness_is_exact_120_seconds(staged, age, accepted):
    if accepted:
        sidecar.check_admission(report(staged), staged.config, staged.plan, 1000 - age)
    else:
        with pytest.raises(ValueError, match='120s'):
            sidecar.check_admission(report(staged), staged.config, staged.plan, 1000 - age)


@pytest.mark.parametrize('field,value', [('scanner_euid', 2524), ('clear', False), ('clear', 1),
                                      ('blocking_reasons', ['process_identity_drift:123']),
                                      ('gpu', {'uuid': sidecar.DEVICES[0]}), ('device_minor', 3),
                                      ('host_sha256', 'wrong')])
def test_admission_is_not_reconciled_or_weakened(staged, field, value):
    snapshot = report(staged)
    snapshot[field] = value
    before = deepcopy(snapshot)
    with pytest.raises(ValueError):
        sidecar.check_admission(snapshot, staged.config, staged.plan, 1000)
    assert snapshot == before


def test_environment_drops_inherited_admission_and_allocator_overrides(monkeypatch):
    for key in ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'PYTHONSTARTUP', 'R125_ADMISSION_PLAN_SHA256',
                'R150_COHORT_SHA256', 'PYTORCH_ALLOC_CONF']:
        monkeypatch.setenv(key, 'untrusted')
    environment = sidecar.clean_environment('/source', sidecar.DEVICES[0])
    assert set(environment) == {'PATH', 'HOME', 'CUDA_VISIBLE_DEVICES', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPATH',
                                'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                                'TOKENIZERS_PARALLELISM', 'PYTORCH_CUDA_ALLOC_CONF'}
    assert environment['PYTORCH_CUDA_ALLOC_CONF'] == 'expandable_segments:True'


def test_validation_failure_before_load_always_has_failed_receipt(tmp_path, capsys):
    attempt = tmp_path / 'new-attempt'
    with pytest.raises(FileNotFoundError):
        sidecar.supervise(tmp_path / 'missing-config', receipt_dir=attempt,
                           main_go_path=tmp_path / 'missing-go', main_go_sha256='0' * 64)
    assert sidecar.read(attempt / 'FAILED.json')['stage'] == 'VALIDATE'
    assert sidecar.read(attempt / 'LIFECYCLE.json')['cgroup_empty_verified'] is None
    assert 'FAILED' in capsys.readouterr().err
    sidecar.subprocess.Popen.assert_not_called()
    sidecar.subprocess.run.assert_not_called()


def test_existing_attempt_is_not_overwritten(tmp_path, capsys):
    attempt = tmp_path / 'old-attempt'
    attempt.mkdir()
    sidecar.write_once(attempt / 'FAILED.json', {'original': True})
    before = (attempt / 'FAILED.json').read_bytes()
    with pytest.raises(FileExistsError):
        sidecar.supervise('/bad', receipt_dir=attempt, main_go_path='/bad', main_go_sha256='0' * 64)
    assert (attempt / 'FAILED.json').read_bytes() == before
    assert 'FAILED' in capsys.readouterr().err
    assert list(attempt.iterdir()) == [attempt / 'FAILED.json']


@pytest.mark.parametrize('failure', ['exception', 'timeout', 'nonzero', 'malformed', 'denied'])
def test_R147_admission_failure_precedes_service_and_emits_FAILED(staged, monkeypatch, failure):
    monkeypatch.setattr(sidecar.os, 'getuid', lambda: 2524)
    monkeypatch.setattr(sidecar.os, 'getgid', lambda: 2524)
    monkeypatch.setattr(sidecar, 'systemd_state', lambda unused: {'LoadState': 'not-found'})
    if failure == 'exception':
        effect = RuntimeError('scanner startup exception')
    elif failure == 'timeout':
        effect = sidecar.subprocess.TimeoutExpired(['scan'], 100, output=b'partial preserved')
    else:
        snapshot = report(staged)
        if failure == 'denied':
            snapshot.update(clear=False, blocking_reasons=['process_identity_drift:123'])
        effect = None
    runner = Mock(side_effect=effect, return_value=SimpleNamespace(returncode=2 if failure == 'nonzero' else 0,
                  stdout='{' if failure == 'malformed' else json.dumps(report(staged) if failure != 'denied' else snapshot)))
    monkeypatch.setattr(sidecar.subprocess, 'run', runner)
    with pytest.raises((ValueError, RuntimeError, sidecar.subprocess.TimeoutExpired)):
        sidecar.supervise(staged.config_path, **staged.args)
    assert sidecar.read(staged.attempt / 'FAILED.json')['stage'] == 'ADMISSION'
    lifecycle = sidecar.read(staged.attempt / 'LIFECYCLE.json')
    assert lifecycle['status'] == 'NOT_STARTED' and lifecycle['cgroup_empty_verified'] is None
    sidecar.subprocess.Popen.assert_not_called()
    command = runner.call_args.args[0]
    assert command[-4:] == ['gpu.orch_r125_continual_guard', 'scan', '--config', str(staged.config_path)]
    assert '-i' in command and 'CUDA_VISIBLE_DEVICES=' in command
    if failure == 'timeout':
        assert (staged.attempt / 'SCAN.stdout').read_bytes() == b'partial preserved'


@pytest.fixture
def cgroup_fixture(tmp_path, monkeypatch):
    root = tmp_path / 'cgroup'
    monkeypatch.setattr(sidecar, 'CGROUP_ROOT', root)
    boot = tmp_path / 'boot'
    boot.write_text('boot')
    monkeypatch.setattr(sidecar, 'BOOT_ID', boot)
    unit = sidecar.new_unit(tmp_path / 'attempt')
    path = sidecar.cgroup_path(unit)
    path.mkdir(parents=True)
    (path / 'cgroup.events').write_text('populated 0\nfrozen 0\n')
    (path / 'cgroup.procs').write_text('')
    observed = dict(unit=unit, cgroup='/system.slice/' + unit + '.service', cgroup_inode=sidecar.inode(path),
                    parent_inode=sidecar.inode(path.parent), invocation_id='a' * 32, boot_id='boot')
    state = dict(ActiveState='inactive', InvocationID='a' * 32, ControlGroup=observed['cgroup'])
    monkeypatch.setattr(sidecar, 'systemd_state', lambda unused: state)
    return SimpleNamespace(path=path, observed=observed, state=state, boot=boot)


def test_exit_proof_verifies_present_hierarchical_empty_cgroup(cgroup_fixture):
    result = sidecar.verify_service_exit(cgroup_fixture.observed)
    assert result['cgroup_empty_verified'] is True
    assert result['evidence']['kind'] == 'present_empty'
    assert result['readout_cleanup_adopted'] is False
    assert result['evaluation_success_claimed'] is False


def test_exit_proof_can_verify_actual_removal_after_bound_observation(cgroup_fixture):
    for path in cgroup_fixture.path.iterdir():
        path.unlink()
    cgroup_fixture.path.rmdir()
    cgroup_fixture.state.update(InvocationID='', ControlGroup='')
    result = sidecar.verify_service_exit(cgroup_fixture.observed)
    assert result['evidence']['kind'] == 'removed_after_bound_observation'
    assert result['cgroup_empty_verified'] is True


@pytest.mark.parametrize('failure', ['active', 'invocation', 'cgroup', 'boot', 'inode', 'parent',
                                   'populated', 'member', 'descendant', 'missing_events'])
def test_no_emptiness_from_return_code_or_incomplete_metadata(cgroup_fixture, failure):
    fixture = cgroup_fixture
    if failure == 'active':
        fixture.state['ActiveState'] = 'active'
    elif failure == 'invocation':
        fixture.state['InvocationID'] = 'b' * 32
    elif failure == 'cgroup':
        fixture.state['ControlGroup'] = '/other'
    elif failure == 'boot':
        fixture.boot.write_text('other')
    elif failure == 'inode':
        fixture.observed['cgroup_inode'] = [0, 0]
    elif failure == 'parent':
        fixture.observed['parent_inode'] = [0, 0]
    elif failure == 'populated':
        (fixture.path / 'cgroup.events').write_text('populated 1\n')
    elif failure == 'member':
        (fixture.path / 'cgroup.procs').write_text('123\n')
    elif failure == 'descendant':
        (fixture.path / 'nested').mkdir()
        (fixture.path / 'nested/cgroup.procs').write_text('321\n')
    else:
        (fixture.path / 'cgroup.events').unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        sidecar.verify_service_exit(fixture.observed)


def test_native_startup_exception_writes_failure_before_any_model(staged, monkeypatch):
    staged.attempt.mkdir()
    monkeypatch.setattr(sidecar, 'validate', Mock(side_effect=ValueError('admission_exception_before_load')))
    with pytest.raises(ValueError):
        sidecar.native(staged.config_path, **staged.args)
    assert sidecar.read(staged.attempt / 'NATIVE_FAILED.json')['status'] == 'FAILED'
    assert not (staged.attempt / 'PRE_NATIVE.json').exists()


def test_write_once_never_replaces_receipt(tmp_path):
    path = tmp_path / 'receipt.json'
    sidecar.write_once(path, {'original': True})
    with pytest.raises(FileExistsError):
        sidecar.write_once(path, {'original': False})
    assert sidecar.read(path) == {'original': True}


def test_unit_is_bound_to_never_reused_attempt_path(tmp_path):
    assert sidecar.new_unit(tmp_path / 'one') == sidecar.new_unit(tmp_path / 'one')
    assert sidecar.new_unit(tmp_path / 'one') != sidecar.new_unit(tmp_path / 'two')


@pytest.mark.parametrize('failure', [None, 'identity', 'pid', 'ticks', 'policy', 'boot', 'inode', 'member'])
def test_service_observation_reads_real_membership_and_properties(cgroup_fixture, monkeypatch, failure):
    fixture = cgroup_fixture
    fixture.state.update(ActiveState='active', MainPID='123', DevicePolicy='strict', NoNewPrivileges='yes',
                         CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
                         KillMode='control-group', User='2524', Group='2524')
    (fixture.path / 'cgroup.procs').write_text('123\n')
    config = dict(boot_id='boot', device_containment={'unit': fixture.observed['unit']})
    started = dict(pid=123, start_ticks='456', invocation_id='a' * 32, boot_id='boot',
                   cgroup_inode=fixture.observed['cgroup_inode'])
    monkeypatch.setattr(sidecar, 'start_ticks', lambda unused: '456')
    if failure == 'identity':
        started['invocation_id'] = 'b' * 32
    elif failure == 'pid':
        started['pid'] = 124
    elif failure == 'ticks':
        started['start_ticks'] = '457'
    elif failure == 'policy':
        fixture.state['DevicePolicy'] = 'auto'
    elif failure == 'boot':
        fixture.boot.write_text('different')
    elif failure == 'inode':
        started['cgroup_inode'] = [0, 0]
    elif failure == 'member':
        (fixture.path / 'cgroup.procs').write_text('')
    if failure:
        with pytest.raises(ValueError):
            sidecar.observe_service(config, started)
    else:
        observed = sidecar.observe_service(config, started)
        assert observed['pid'] == 123 and observed['start_ticks'] == '456'


@pytest.mark.parametrize('failure', [None, 'native_nonzero', 'service_nonzero', 'no_observation', 'no_empty_proof'])
def test_supervisor_requires_native_receipt_and_external_exit_proof(staged, monkeypatch, failure):
    monkeypatch.setattr(sidecar.os, 'getuid', lambda: 2524)
    monkeypatch.setattr(sidecar.os, 'getgid', lambda: 2524)
    monkeypatch.setattr(sidecar.time, 'sleep', lambda unused: None)
    monkeypatch.setattr(sidecar, 'systemd_state', lambda unused: {'LoadState': 'not-found'})
    scanner = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(report(staged))))
    monkeypatch.setattr(sidecar.subprocess, 'run', scanner)
    observed = dict(unit=staged.config['device_containment']['unit'], invocation_id='a' * 32)
    observe = Mock(return_value=observed)
    monkeypatch.setattr(sidecar, 'observe_service', observe)
    lifecycle = dict(status='SERVICE_EXIT_VERIFIED', cgroup_empty_verified=True)
    exit_proof = Mock(side_effect=ValueError('still_populated') if failure == 'no_empty_proof' else None,
                      return_value=lifecycle)
    monkeypatch.setattr(sidecar, 'verify_service_exit', exit_proof)
    status = 7 if failure == 'service_nonzero' else 0

    def spawn(*args, **kwargs):
        if failure != 'no_observation':
            sidecar.write_once(staged.attempt / 'SERVICE_STARTED.json', {'pid': 123})
        sidecar.write_once(staged.attempt / 'NATIVE_EXIT.json', {'exit_code': 9 if failure == 'native_nonzero' else 0})
        return SimpleNamespace(poll=Mock(side_effect=[None, status]), wait=Mock(return_value=status))

    popen = Mock(side_effect=spawn)
    monkeypatch.setattr(sidecar.subprocess, 'Popen', popen)
    if failure:
        with pytest.raises(ValueError):
            sidecar.supervise(staged.config_path, **staged.args)
        assert sidecar.read(staged.attempt / 'FAILED.json')['status'] == 'FAILED'
        assert not (staged.attempt / 'EXIT.json').exists()
    else:
        result = sidecar.supervise(staged.config_path, **staged.args)
        assert result['cgroup_empty_verified'] is True
        assert sidecar.read(staged.attempt / 'EXIT.json')['status'] == 'COMPLETE'
        exit_proof.assert_called_once_with(observed)
    if failure == 'no_observation':
        exit_proof.assert_not_called()
        assert sidecar.read(staged.attempt / 'LIFECYCLE.json')['cgroup_empty_verified'] is None
    elif failure == 'no_empty_proof':
        assert not (staged.attempt / 'LIFECYCLE.json').exists()
        assert (staged.attempt / 'LIFECYCLE_FAILED.json').exists()
    else:
        assert sidecar.read(staged.attempt / 'LIFECYCLE.json')['cgroup_empty_verified'] is True
    command = popen.call_args.args[0]
    assert '--property=RuntimeMaxSec=990' in command
    assert 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True' in command
    assert popen.call_args.kwargs['stdin'] == sidecar.subprocess.DEVNULL


@pytest.mark.parametrize('returncode', [0, 8])
def test_contained_startup_uses_actual_timeout_parent_and_barrier(staged, monkeypatch, returncode):
    staged.attempt.mkdir()
    sidecar.write_once(staged.attempt / 'ADMISSION.json', report(staged))
    sidecar.write_once(staged.attempt / 'ADMISSION_CLOCK.json', dict(verified_unix=990,
                       admission_sha256=sidecar.sha(staged.attempt / 'ADMISSION.json')))
    sidecar.write_once(staged.attempt / 'SERVICE_OBSERVED.json', dict(invocation_id='a' * 32,
                       cgroup_inode=[32, 1234], cgroup='/system.slice/' + staged.config['device_containment']['unit'] + '.service'))
    monkeypatch.setattr(sidecar, 'systemd_state', lambda unused: {'InvocationID': 'a' * 32})
    monkeypatch.setattr(sidecar, 'inode', lambda unused: [32, 1234])
    monkeypatch.setattr(sidecar, 'start_ticks', lambda unused: '777')
    monkeypatch.setenv('PYTORCH_CUDA_ALLOC_CONF', sidecar.ALLOCATOR)
    monkeypatch.delenv('INVOCATION_ID', raising=False)
    staged.capsule.verify_device_containment = Mock(return_value={'denied_foreign_minors': [0, 1, 2, 3, 4, 6, 7]})
    staged.guard.publish_launch = sidecar.write_once
    process = SimpleNamespace(pid=987, stdin=Mock(), wait=Mock(return_value=returncode))
    monkeypatch.setattr(sidecar.subprocess, 'Popen', Mock(return_value=process))
    if returncode:
        with pytest.raises(ValueError, match='native_failed'):
            sidecar.contained(staged.config_path, **staged.args)
        assert sidecar.read(staged.attempt / 'CONTAINED_FAILED.json')['status'] == 'FAILED'
    else:
        sidecar.contained(staged.config_path, **staged.args)
    launch = sidecar.read(staged.attempt / 'LAUNCH.json')
    assert launch['pid'] == 987 and launch['parent_start_ticks'] == '777'
    assert launch['guard_sha256'] == sidecar.sha(staged.config_path)
    assert launch['admission_verified_unix'] == 990
    assert launch['admission_sha256'] == sidecar.sha(staged.attempt / 'ADMISSION.json')
    process.stdin.write.assert_called_once_with(b'LAUNCH_READY\n')
    process.stdin.close.assert_called_once()
    assert sidecar.read(staged.attempt / 'NATIVE_EXIT.json')['cgroup_empty_verified'] is None
    assert not (staged.attempt / 'LIFECYCLE.json').exists()
    command = sidecar.subprocess.Popen.call_args.args[0]
    assert command[:4] == ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '985s']
    assert 'native' in command and '--main-go-sha256' in command


def test_systemd_query_only_reads_named_unit(monkeypatch, tmp_path):
    unit = sidecar.new_unit(tmp_path / 'attempt')
    runner = Mock(return_value=SimpleNamespace(returncode=1,
                  stdout='Id=' + unit + '.service\nLoadState=not-found\nActiveState=inactive\n'))
    monkeypatch.setattr(sidecar.subprocess, 'run', runner)
    assert sidecar.systemd_state(unit)['LoadState'] == 'not-found'
    assert runner.call_args.args[0][:3] == ['/usr/bin/systemctl', 'show', unit + '.service']
    runner.return_value = SimpleNamespace(returncode=1, stdout='')
    with pytest.raises(ValueError, match='readable_systemd_state'):
        sidecar.systemd_state(unit)


@pytest.mark.parametrize('field,value', [
    ('guard_sha256', '0' * 64), ('patcher_sha256', '0' * 64), ('memory_probe_sha256', '0' * 64),
    ('status', 'PENDING'), ('initialize_callback', 'other.callback'), ('original_checks_preserved', False),
    ('run_dispatch_unchanged', False), ('r150_parent_guard_sha256', '0' * 64),
])
def test_unreviewed_derivative_rejected_even_with_new_GO(staged, field, value):
    gate_path = Path(staged.config['cpu_gate_path'])
    gate = sidecar.read(gate_path)
    gate['guard_derivation'][field] = value
    dump(gate_path, gate)
    staged.config['cpu_gate_sha256'] = sidecar.sha(gate_path)
    rebind(staged)
    with pytest.raises(ValueError, match='exact_Main_CPU_reviewed_guard_derivation'):
        check_staged(staged)
    staged.guard.validate.assert_not_called()


def test_derivative_is_only_fixed_initialization_callback():
    from gpu import orch_r150_guard_patch as parent_patcher
    from gpu import orch_r151_matched_stage as staging
    original = (ROOT / sidecar.GUARD).read_bytes().decode()
    parent = parent_patcher.patch_source(original)
    final = sidecar.render_guard(original.encode()).decode()
    assert final == parent.replace(staging.OLD_INITIALIZE, staging.NEW_INITIALIZE)
    assert staging.revert_guard(final) == original
    parent_tree, final_tree = ast.parse(parent), ast.parse(final)
    for old, new in zip(parent_tree.body, final_tree.body):
        if isinstance(old, ast.FunctionDef) and old.name == 'native_entry':
            assert ast.dump(old.body[-1].test) == ast.dump(new.body[-1].test)
            assert [ast.dump(node) for node in old.body[-1].orelse] == [ast.dump(node) for node in new.body[-1].orelse]
            assert [ast.dump(node) for node in old.body[:-1]] == [ast.dump(node) for node in new.body[:-1]]
        else:
            assert ast.dump(old) == ast.dump(new)
            assert ast.get_source_segment(parent, old) == ast.get_source_segment(final, new)


@pytest.mark.parametrize('mutation', ['parent', 'extra_guard_statement'])
def test_repinning_guard_and_CPU_receipt_cannot_bypass_exact_derivation(staged, mutation):
    from gpu import orch_r150_guard_patch as parent_patcher
    path = staged.source / sidecar.GUARD
    if mutation == 'parent':
        path.write_text(parent_patcher.patch_source((ROOT / sidecar.GUARD).read_text()))
    else:
        with path.open('a') as stream:
            stream.write('\nUNREVIEWED = True\n')
    pins = sidecar.source_inventory(staged.source)
    dump(Path(staged.config['source_manifest_path']), {'files': pins})
    staged.config['source_manifest_sha256'] = sidecar.sha(staged.config['source_manifest_path'])
    staged.config['source_pins'] = pins
    gate_path = Path(staged.config['cpu_gate_path'])
    gate = sidecar.read(gate_path)
    gate['source_manifest_sha256'] = staged.config['source_manifest_sha256']
    gate['guard_derivation']['guard_sha256'] = pins[sidecar.GUARD]
    dump(gate_path, gate)
    staged.config['cpu_gate_sha256'] = sidecar.sha(gate_path)
    rebind(staged)
    with pytest.raises(ValueError):
        check_staged(staged)


@pytest.mark.parametrize('field,value', [('physical_devices', [0, 3, 4, 5]), ('host_sha256', 'other'),
                                      ('lease_extended', True), ('existing_life_wall_changed', True),
                                      ('safety_margin_seconds', 0), ('hard_end_unix', 2100),
                                      ('lease_end_unix', 2700)])
def test_no_new_lease_or_old_life_extension_from_rehashed_budget(staged, field, value):
    path = Path(staged.config['lease_path'])
    budget = sidecar.read(path)
    budget[field] = value
    dump(path, budget)
    staged.config['lease_sha256'] = sidecar.sha(path)
    rebind(staged)
    with pytest.raises(ValueError):
        check_staged(staged)


def test_original_generic_lease_bytes_not_just_new_budget_checked(staged):
    path = Path(sidecar.read(staged.config['lease_path'])['derived_from']['path'])
    with path.open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError, match='actual_generic_R131_lease_bytes'):
        check_staged(staged)


@pytest.mark.parametrize('schema', [None, '', 'R150_UNVALIDATED'])
def test_every_phase_requires_capacity_validated_initialization(staged, schema):
    staged.plan['initialization_validation_schema'] = schema
    dump(Path(staged.config['plan_path']), staged.plan)
    staged.config['plan_sha256'] = sidecar.sha(staged.config['plan_path'])
    rebind(staged)
    with pytest.raises(ValueError, match='capacity_validated_common_initial_state_required'):
        check_staged(staged)
    staged.guard.validate.assert_not_called()
