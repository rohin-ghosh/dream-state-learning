"""CPU fixtures exercise readmission only; they do not claim real admission."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


OPERATOR = Path(__file__).resolve().parents[1] / 'gpu/orch_r160_frozen_readmission.py'
spec = importlib.util.spec_from_file_location('r160_test_operator', OPERATOR)
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    base = tmp_path / 'cohort'
    source = base / 'source'
    source.mkdir(parents=True)
    (source / 'fixture.py').write_text('fixture = True\n')
    for name, relative in [('BASE', '.'), ('SOURCE', 'source'),
        ('OLD_CONFIG', 'control/old/GUARD.json'), ('OLD_ATTEMPT', 'attempts/old'),
        ('CONTROL', 'control/r160'), ('ATTEMPT', 'attempts/new'),
        ('MARKER', 'control/new_once'), ('OLD_MARKER', 'control/old_once')]:
        monkeypatch.setattr(operator, name, base / relative)
    operator.OLD_MARKER.mkdir(parents=True)
    plan = dict(matched_arm=operator.ARM, physical=6, gpu_uuid=operator.UUID,
                root=str(base / operator.ARM), source_root=str(source))
    plan_path = write(base / 'PLAN.json', plan)
    original_allocation = write(base / 'ALLOCATION.json', dict(physical=6, gpu_uuid=operator.UUID,
        plan_sha256=operator.sha(plan_path), cpu_tests_passed=True, builder_entry_pushed=True, declared_unix=1))
    manifest = write(base / 'SOURCE_MANIFEST.json', dict(files={'fixture.py': operator.sha(source / 'fixture.py')}))
    config = dict(phase='run', matched_arm=operator.ARM, resume=False, plan_path=str(plan_path),
        plan_sha256=operator.sha(plan_path), attempt_dir=str(operator.OLD_ATTEMPT),
        allocation_path=str(original_allocation), allocation_sha256=operator.sha(original_allocation),
        source_manifest_path=str(manifest), r158_cpu={'path': '/synthetic/cpu'},
        r158_repairs={'path': '/synthetic/repairs'}, device_containment=dict(unit='original', minor=5, uid=2524, gid=2524))
    paths = {'config': write(operator.OLD_CONFIG, config),
        'admission': write(operator.OLD_ATTEMPT / 'ADMISSION.json', dict(clear=False, scanner_euid=0,
            gpu=dict(uuid=operator.UUID, memory_used_mib=0), blocking_reasons=['minor_scan_identity_changed:530040',
            'minor_scan_process_drift:530040', 'process_identity_drift:530215'])),
        'failure': write(operator.OLD_ATTEMPT / 'FAILED.json', dict(stage='ADMISSION',
            error='fresh_exclusive_admission', status='FAILED', no_retry=True)),
        'lifecycle': write(operator.OLD_ATTEMPT / 'LIFECYCLE.json', dict(status='NOT_STARTED', observed=None,
            cgroup_empty_verified=None))}
    monkeypatch.setattr(operator, 'PINS', {name: (path, operator.sha(path)) for name, path in paths.items()})
    (source / 'fixture.py').chmod(0o444)
    source.chmod(0o555)
    engine = SimpleNamespace(new_unit=lambda path: 'unit-' + path.name,
        go_binding=lambda config, plan, checksum: dict(config_sha256=checksum), validate=Mock(), supervise=Mock())
    module = SimpleNamespace(verify_cpu=Mock(), verify_repairs=Mock(),
        inventory=lambda path: {'fixture.py': operator.sha(path / 'fixture.py')},
        engine=lambda: engine, write=write, validate_extra=Mock())
    monkeypatch.setattr(operator, 'runtime', lambda: module)
    guard = SimpleNamespace(__file__=str(source / 'gpu/orch_r125_continual_guard.py'),
        validate=lambda path: (operator.read(path), plan))
    monkeypatch.setattr(operator.importlib, 'import_module', lambda name: guard)
    log = tmp_path / 'CPU.log'
    log.write_text('synthetic CPU fixture\n')
    cpu = write(tmp_path / 'CPU.json', dict(status='PASS', exit_code=0, passed=1,
        operator_sha256=operator.sha(OPERATOR), logs=[operator.reference(log)]))
    for name in ('INITIALIZED.json', 'COMMIT.json'):
        write(base / 'common_initial' / name, {'fixture': True})
    write(base / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json', {'fixture': True})
    return SimpleNamespace(base=base, config=config, plan=plan, module=module, engine=engine,
                           cpu=cpu, paths=paths, guard=guard)


def test_exact_pre_native_refusal_is_accepted_without_erasing_reasons(fixture):
    assert operator.validate_old(fixture.module) == (fixture.config, fixture.plan)
    assert len(operator.read(fixture.paths['admission'])['blocking_reasons']) == 3


@pytest.mark.parametrize('name', ['config', 'admission', 'failure', 'lifecycle'])
def test_any_original_receipt_byte_change_refused(fixture, name):
    path = fixture.paths[name]
    path.write_text(path.read_text() + ' ')
    with pytest.raises(ValueError, match='bound_receipt_bytes'):
        operator.validate_old(fixture.module)


@pytest.mark.parametrize('name', ['LAUNCH.json', 'PRE_NATIVE.json', 'SERVICE_STARTED.json', 'NATIVE.log', 'NATIVE_EXIT.json'])
def test_any_native_or_service_evidence_refused(fixture, name):
    (operator.OLD_ATTEMPT / name).write_text('{}')
    with pytest.raises(ValueError, match='no_original_native'):
        operator.validate_old(fixture.module)


def test_born_frozen_life_or_missing_old_marker_refused(fixture):
    root = fixture.base / operator.ARM
    root.mkdir()
    with pytest.raises(ValueError, match='never_born'):
        operator.validate_old(fixture.module)
    root.rmdir()
    operator.OLD_MARKER.rmdir()
    with pytest.raises(ValueError, match='original_phase_marker_retained'):
        operator.validate_old(fixture.module)


def test_only_allocation_attempt_and_unit_change(fixture):
    original = deepcopy(fixture.config)
    config = operator.derive_config(original, {'path': '/new/allocation', 'sha256': 'a'*64}, fixture.engine)
    changed = {key for key in original if original[key] != config[key]}
    assert changed == {'allocation_path', 'allocation_sha256', 'attempt_dir', 'device_containment'}
    assert {key for key in original['device_containment'] if original['device_containment'][key] != config['device_containment'][key]} == {'unit'}
    assert original == fixture.config


def test_prepare_has_no_supervisor_or_native_dispatch_and_binds_cpu(fixture):
    result = operator.prepare(fixture.cpu)
    assert result['status'] == 'CPU_PREPARED_NO_GO_NO_GPU'
    assert result['GPU_calls'] == 0
    assert not operator.ATTEMPT.exists() and not operator.MARKER.exists()
    fixture.engine.supervise.assert_not_called()
    config = operator.bound(result['config'])
    allocation = operator.bound(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    provenance = operator.bound(allocation['r160_readmission'])
    assert provenance['cpu'] == operator.reference(fixture.cpu)
    assert provenance['operator'] == operator.reference(OPERATOR)
    assert operator.OLD_MARKER.exists()
    with pytest.raises(FileExistsError):
        operator.prepare(fixture.cpu)


def test_original_guard_rejection_is_not_bypassed(fixture):
    fixture.guard.validate = Mock(side_effect=ValueError('actual_guard_rejection'))
    with pytest.raises(ValueError, match='actual_guard_rejection'):
        operator.prepare(fixture.cpu)
    assert (operator.CONTROL / 'GUARD.json').exists()
    assert not (operator.CONTROL / 'PREPARED_READMISSION.json').exists()
    fixture.engine.supervise.assert_not_called()


@pytest.mark.parametrize('field,value', [('status', 'FAIL'), ('exit_code', 1), ('passed', 0), ('operator_sha256', '0'*64), ('logs', [])])
def test_external_cpu_evidence_mandatory(fixture, field, value):
    cpu = operator.read(fixture.cpu)
    cpu[field] = value
    write(fixture.cpu, cpu)
    with pytest.raises(ValueError):
        operator.prepare(fixture.cpu)
    assert not operator.CONTROL.exists()


def test_supervisor_requires_extra_main_binding_and_new_once_marker(fixture):
    result = operator.prepare(fixture.cpu)
    go = write(fixture.base / 'GO.json', {})
    with pytest.raises(ValueError, match='Main_bound_readmission'):
        operator.supervise(go, operator.sha(go))
    assert not operator.MARKER.exists()
    write(go, dict(readmission=operator.reference(operator.CONTROL / 'PREPARED_READMISSION.json')))
    operator.supervise(go, operator.sha(go))
    fixture.engine.validate.assert_called_once()
    fixture.module.validate_extra.assert_called_once()
    fixture.engine.supervise.assert_called_once()
    assert operator.MARKER.exists() and operator.OLD_MARKER.exists()
    with pytest.raises(FileExistsError):
        operator.supervise(go, operator.sha(go))
    assert fixture.engine.supervise.call_count == 1


def test_device_lock_prevents_other_admission(fixture):
    with operator.exclusive():
        with pytest.raises(BlockingIOError):
            with operator.exclusive():
                pytest.fail('second device lock acquired')


def test_supervisor_failure_retains_new_and_old_once_markers(fixture):
    operator.prepare(fixture.cpu)
    go = write(fixture.base / 'GO.json', dict(readmission=operator.reference(operator.CONTROL / 'PREPARED_READMISSION.json')))
    fixture.engine.supervise.side_effect = ValueError('fresh_admission_refused')
    with pytest.raises(ValueError, match='fresh_admission_refused'):
        operator.supervise(go, operator.sha(go))
    assert operator.MARKER.is_dir() and operator.OLD_MARKER.is_dir()
    with pytest.raises(FileExistsError):
        operator.supervise(go, operator.sha(go))
    assert fixture.engine.supervise.call_count == 1


def test_original_engine_rejection_stops_before_admission(fixture):
    operator.prepare(fixture.cpu)
    go = write(fixture.base / 'GO.json', dict(readmission=operator.reference(operator.CONTROL / 'PREPARED_READMISSION.json')))
    fixture.engine.validate.side_effect = ValueError('original_guard_blocker')
    with pytest.raises(ValueError, match='original_guard_blocker'):
        operator.supervise(go, operator.sha(go))
    fixture.engine.supervise.assert_not_called()
    assert not operator.MARKER.exists()


def test_original_receipt_symlink_refused(fixture):
    original = fixture.paths['admission']
    saved = original.with_suffix('.saved')
    original.rename(saved)
    original.symlink_to(saved)
    with pytest.raises(ValueError, match='canonical_regular_input'):
        operator.validate_old(fixture.module)


@pytest.mark.parametrize('field', ['phase', 'matched_arm', 'resume', 'plan_sha256', 'source_manifest_path'])
def test_mutated_guard_cannot_reach_supervise(fixture, field):
    operator.prepare(fixture.cpu)
    path = operator.CONTROL / 'GUARD.json'
    config = operator.read(path)
    config[field] = 'changed'
    write(path, config)
    go = write(fixture.base / 'GO.json', dict(readmission=operator.reference(operator.CONTROL / 'PREPARED_READMISSION.json')))
    with pytest.raises(ValueError, match='bound_receipt_bytes'):
        operator.supervise(go, operator.sha(go))
    fixture.engine.supervise.assert_not_called()
