"""Prospective local-only tests. Sources and controller evidence are synthetic."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
from types import SimpleNamespace

import pytest

from gpu import orch_r146_checkpoint_copy_phase as phase
from tests.test_orch_r130_checkpoint_copier import source


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return phase.sha(path)


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    clock = SimpleNamespace(now=phase.WALL - 10800)
    monkeypatch.setattr(phase.time, 'time', lambda: clock.now)
    evidence_root = tmp_path / 'evidence'
    evidence_root.mkdir()
    monkeypatch.setattr(phase, 'EVIDENCE_ROOT', evidence_root)
    repository = Path(phase.copier.__file__).resolve().parents[1]
    sources = []
    for lineage in ('legacy', 'pilot', 'kernel'):
        initial = '/synthetic/' + lineage + '/checkpoints/initial/COMMIT.json'
        selection = tmp_path / (lineage + '_selection.json')
        selection_sha = dump(selection, dict(checkpoints=[dict(label=lineage + '_initial', path=initial,
                                                               commit_sha256='a' * 64)]))
        wrapper = repository / 'gpu' / phase.copier.WRAPPERS[lineage]
        sources.append(dict(lineage_id=lineage, checkpoint_root=str(Path(initial).parent.parent),
            initial_commit_path=initial, initial_commit_sha256='a' * 64,
            native_schema=phase.scheduler.sidecar.runner.NATIVE_SCHEMA,
            base_sha256=phase.scheduler.sidecar.runner.BASE_SHA256,
            wrapper_path=str(wrapper), wrapper_sha256=phase.sha(wrapper),
            prior_selection_path=str(selection), prior_selection_sha256=selection_sha))
    destination = repository / 'gpu/ovx_ssh.sh'
    original = dict(schema=phase.copier.SCHEMA, copier_sha256=phase.sha(phase.copier.__file__),
                    sources=sources, destination_wrapper=str(destination), destination_wrapper_sha256=phase.sha(destination))
    original_path = tmp_path / 'COPIER_CONFIG_V1.json'
    original_sha = dump(original_path, original)
    monkeypatch.setattr(phase, 'ORIGINAL_CONFIG_SHA256', original_sha)
    lease_path = tmp_path / 'lease.json'
    lease_sha = dump(lease_path, dict(sources=[dict(wrapper_path=source['wrapper_path'],
        wrapper_sha256=source['wrapper_sha256'], conservative_read_end_unix=phase.WALL + 1) for source in sources]))
    dependencies = {str(Path(module.__file__).resolve()): phase.sha(module.__file__) for module in
                    (phase.copier, phase.scheduler, phase.scheduler.sidecar, phase.scheduler.sidecar.runner)}
    previous = dict(predecessor_copier_path=str(original_path), predecessor_copier_sha256=original_sha,
                    copier_sha256=phase.sha(phase.copier.__file__), destination_wrapper=str(destination),
                    source_lease_evidence_path=str(lease_path), source_lease_evidence_sha256=lease_sha,
                    local_dependencies=dependencies, output_root=str(tmp_path / 'predecessor_output'))
    previous_path = tmp_path / 'SUCCESSOR_COPY_V2.json'
    previous_sha = dump(previous_path, previous)
    started_path = Path(previous['output_root']) / 'STARTED.json'
    identity = dict(pid=123, uid=os.getuid(), start_ticks='456', boot_id='synthetic-boot')
    started_sha = dump(started_path, dict(status='BOUNDED_SUCCESSOR_COPY_ARMED', identity=identity,
                                        config_sha256=previous_sha))
    complete_path = Path(previous['output_root']) / 'COMPLETE.json'
    complete_sha = dump(complete_path, dict(status='BOUNDED_PHASE_COPY_FINISHED'))
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda value: value == identity)
    node_helper = tmp_path / 'orch_r146_successor_phase.py'
    node_helper.write_text('synthetic_node_helper = True\n')
    helper_sha = phase.sha(node_helper)
    source_root = str(phase.ROOT / 'source_r146_synthetic')
    node_phase_path = tmp_path / 'NODE_PHASE.json'
    node_phase_sha = dump(node_phase_path, dict(schema='R146_BENCHMARK_ENROLLED_PHASE_V1',
                         source_root=source_root, created_unix=clock.now, hard_end_unix=phase.WALL,
                         helper_sha256=helper_sha, sources={'gpu/orch_r146_successor_phase.py': helper_sha}))
    builder_path = tmp_path / 'BUILDER.md'
    builder_path.write_text('## [Builder] 2026-09-16 synthetic CPU gate\n')
    log_path = tmp_path / 'pytest.log'
    log_path.write_text('synthetic PASS')
    gate_path = tmp_path / 'GATE.json'
    gate_sha = dump(gate_path, dict(status='PASS', test_exit_code=0, helper_sha256=phase.sha(phase.__file__),
        remote_helper_sha256=helper_sha, test_path=str(Path(__file__).resolve()), test_sha256=phase.sha(__file__),
        test_log_path=str(log_path), test_log_sha256=phase.sha(log_path)))
    first_dispatch = (int(clock.now) // 1800 + 1) * 1800
    config = dict(schema=phase.SCHEMA, helper_sha256=phase.sha(phase.__file__),
        copier_sha256=phase.sha(phase.copier.__file__), local_dependencies=dependencies,
        predecessor_copy_path=str(previous_path), predecessor_copy_sha256=previous_sha,
        predecessor_started_path=str(started_path), predecessor_started_sha256=started_sha,
        predecessor_complete_path=str(complete_path), predecessor_complete_sha256=complete_sha,
        destination_wrapper=str(destination), created_unix=clock.now, first_dispatch_unix=first_dispatch,
        first_copy_unix=first_dispatch - 180, hard_end_unix=phase.WALL, max_cycles=30,
        copy_lead_seconds=180, dispatch_seconds=1800,
        source_lease_evidence_path=str(lease_path), source_lease_evidence_sha256=lease_sha,
        remote_phase_local_path=str(node_phase_path), remote_phase_local_sha256=node_phase_sha,
        remote_phase_path=str(phase.ROOT / 'SUCCESSOR_PHASE_R146.json'), remote_phase_sha256=node_phase_sha,
        source_root=source_root, remote_helper_path=str(Path(source_root) / 'gpu/orch_r146_successor_phase.py'),
        remote_helper_sha256=helper_sha, remote_helper_local_path=str(node_helper), remote_helper_local_sha256=helper_sha,
        builder_entry_path=str(builder_path), builder_entry_sha256=phase.sha(builder_path),
        cpu_gate_path=str(gate_path), cpu_gate_sha256=gate_sha,
        output_root=str(evidence_root / 'r146_successor_copy_synthetic'))
    path = tmp_path / 'COPY_PHASE.json'

    def bind():
        monkeypatch.setenv('R146_PHASE_COPY_SHA256', dump(path, config))

    bind()
    return SimpleNamespace(config=config, original=original, previous=previous, path=path, bind=bind,
                           clock=clock, identity=identity)


def test_admission_is_local_only_and_preserves_original_bytes(admitted, monkeypatch):
    def prohibited(*args, **kwargs):
        pytest.fail('no subprocesses, source checkpoints, held outputs, or process changes in validation')

    monkeypatch.setattr(phase.subprocess, 'run', prohibited)
    before = {name: phase.sha(name) for name in admitted.config['local_dependencies']}
    config, original = phase.local_validate(admitted.path)
    assert config == admitted.config and original == admitted.original
    assert before == {name: phase.sha(name) for name in before}
    assert not Path(config['output_root']).exists()


@pytest.mark.parametrize('mutation', ['env', 'helper', 'dependencies', 'predecessor', 'started', 'complete',
    'started_config', 'live', 'wrapper', 'wall', 'nan', 'cycles', 'bool_cycles', 'lead', 'dispatch',
    'lease', 'missing_lease', 'gate', 'gate_exit', 'test_pin', 'node_helper', 'node_phase', 'source_root', 'tmp_root', 'symlink'])
def test_rejects_changed_scope_or_evidence(admitted, monkeypatch, tmp_path, mutation):
    config = admitted.config
    if mutation == 'env':
        monkeypatch.setenv('R146_PHASE_COPY_SHA256', '0' * 64)
    elif mutation == 'helper':
        config['helper_sha256'] = '0' * 64
    elif mutation == 'dependencies':
        config['local_dependencies'] = {}
    elif mutation in ('predecessor', 'started', 'complete', 'lease', 'gate', 'node_helper', 'node_phase'):
        name = dict(predecessor='predecessor_copy', started='predecessor_started', complete='predecessor_complete',
                    lease='source_lease_evidence', gate='cpu_gate', node_helper='remote_helper_local',
                    node_phase='remote_phase_local')[mutation]
        Path(config[name + '_path']).write_text('{}')
    elif mutation == 'started_config':
        document = phase.read(config['predecessor_started_path'])
        document['config_sha256'] = '0' * 64
        config['predecessor_started_sha256'] = dump(Path(config['predecessor_started_path']), document)
    elif mutation == 'live':
        monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: False)
    elif mutation == 'wrapper':
        config['destination_wrapper'] = '/synthetic/node3.sh'
    elif mutation == 'wall':
        config['hard_end_unix'] += 1
    elif mutation == 'nan':
        config['hard_end_unix'] = float('nan')
    elif mutation in ('cycles', 'bool_cycles'):
        config['max_cycles'] = 31 if mutation == 'cycles' else True
    elif mutation == 'lead':
        config['copy_lead_seconds'] = 60
    elif mutation == 'dispatch':
        config['first_dispatch_unix'] += 1
    elif mutation == 'missing_lease':
        config['source_lease_evidence_sha256'] = dump(Path(config['source_lease_evidence_path']), dict(sources=[]))
    elif mutation in ('gate_exit', 'test_pin'):
        document = phase.read(config['cpu_gate_path'])
        if mutation == 'test_pin':
            document['test_sha256'] = '0' * 64
        else:
            document['test_exit_code'] = 1
        config['cpu_gate_sha256'] = dump(Path(config['cpu_gate_path']), document)
    elif mutation == 'source_root':
        config['source_root'] = str(phase.ROOT / 'source6_scheduler')
    elif mutation == 'tmp_root':
        config['output_root'] = '/tmp/r146_successor_copy_bad'
    elif mutation == 'symlink':
        target = tmp_path / 'redirect'
        target.mkdir()
        Path(config['output_root']).symlink_to(target)
    if mutation != 'env':
        admitted.bind()
    with pytest.raises((ValueError, FileNotFoundError)):
        phase.local_validate(admitted.path)


def test_complete_and_dead_identity_required_even_before_first_copy(admitted, monkeypatch):
    assert admitted.clock.now < admitted.config['first_copy_unix']
    monkeypatch.setattr(phase.scheduler.sidecar, 'gone', lambda identity: False)
    with pytest.raises(ValueError, match='predecessor_identity_gone'):
        phase.copy_loop(admitted.path)
    assert not Path(admitted.config['output_root']).exists()


def test_missing_predecessor_complete_blocks_launch_before_first_copy(admitted):
    Path(admitted.config['predecessor_complete_path']).unlink()
    with pytest.raises(ValueError, match='predecessor_complete_binding'):
        phase.copy_loop(admitted.path)
    assert not Path(admitted.config['output_root']).exists()


def test_phase_config_needs_no_first_dispatch_field(admitted):
    node_phase = phase.read(admitted.config['remote_phase_local_path'])
    assert 'first_dispatch_unix' not in node_phase
    assert phase.local_validate(admitted.path)[0] == admitted.config


def test_original_root_change_rejected_even_if_config_rebound(admitted, monkeypatch):
    admitted.original['sources'][0]['checkpoint_root'] = '/synthetic/R137/checkpoints'
    original_path = Path(admitted.previous['predecessor_copier_path'])
    checksum = dump(original_path, admitted.original)
    monkeypatch.setattr(phase, 'ORIGINAL_CONFIG_SHA256', checksum)
    admitted.previous['predecessor_copier_sha256'] = checksum
    config = admitted.config
    config['predecessor_copy_sha256'] = dump(Path(config['predecessor_copy_path']), admitted.previous)
    started = phase.read(config['predecessor_started_path'])
    started['config_sha256'] = config['predecessor_copy_sha256']
    config['predecessor_started_sha256'] = dump(Path(config['predecessor_started_path']), started)
    admitted.bind()
    with pytest.raises(ValueError, match='original_selection_scope'):
        phase.local_validate(admitted.path)


@pytest.mark.parametrize('action', ['status', 'known', 'stage'])
def test_one_cpu_remote_module_protocol(admitted, action):
    payload = None if action == 'status' else dict(lineage_id='kernel', value="quote ' ; $(not-a-command)")
    command = shlex.split(phase.remote_command(admitted.config, action, payload))
    assert command[:3] == ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1']
    assert 'R146_PHASE_SHA256=' + admitted.config['remote_phase_sha256'] in command
    assert 'PYTHONPATH=' + admitted.config['source_root'] in command
    position = command.index('-m')
    assert command[position:position + 5] == ['-m', 'gpu.orch_r146_successor_phase', action,
                                             '--config', admitted.config['remote_phase_path']]
    if payload is not None:
        assert json.loads(command[-1]) == payload
    assert '-c' not in command and admitted.config['remote_helper_path'] not in command


@pytest.mark.parametrize('action,payload', [('node', None), ('validate', None), ('stop', None),
    ('status', {}), ('stage', None), ('known', None)])
def test_remote_protocol_has_no_launch_retirement_or_other_actions(admitted, action, payload):
    with pytest.raises(ValueError, match='remote_action_protocol'):
        phase.remote_command(admitted.config, action, payload)


def status_for(config, state='SEGMENT_RUNNING'):
    return dict(status=state, phase_sha256=config['remote_phase_sha256'],
        completed_checkpoint_count=6, future_completed_checkpoints=0, reserved_checkpoint_count=6,
        active_config_path=str(phase.ROOT / 'r146_phase/SEGMENT_00.CONFIG.json') if state == 'SEGMENT_RUNNING' else None,
        active_config_sha256='a' * 64 if state == 'SEGMENT_RUNNING' else None,
        next_dispatch_unix=config['first_dispatch_unix'], active_physical=[0, 1], registered_lineages=5,
        observed_unix=phase.WALL - 100)


def test_status_projection_drops_all_nonprotocol_content(admitted):
    status = status_for(admitted.config)
    status.update(scores={'synthetic_held': 99}, prompt='synthetic_held', response='synthetic_held')
    projected = phase.safe_status(admitted.config, status)
    assert 'synthetic_held' not in json.dumps(projected)
    assert projected['active_config_sha256'] == 'a' * 64
    assert projected['registered_lineages'] == 5


@pytest.mark.parametrize('field,value', [('status', 'UNRECOGNIZED'), ('phase_sha256', '0' * 64),
    ('completed_checkpoint_count', {'score': 3}), ('reserved_checkpoint_count', True),
    ('active_config_path', '/held/output.json'), ('active_config_sha256', 'private'),
    ('active_physical', [2]), ('next_dispatch_unix', float('nan'))])
def test_status_projection_fails_closed(admitted, field, value):
    status = status_for(admitted.config)
    status[field] = value
    with pytest.raises(ValueError):
        phase.safe_status(admitted.config, status)


@pytest.fixture
def copying(admitted, source, monkeypatch, tmp_path):
    source_spec = dict(source.params, wrapper_path=admitted.original['sources'][2]['wrapper_path'])
    selected = phase.copier.discover(source.params)['selected']
    archive = phase.copier.pack(source.params, selected)
    calls = []
    known_status = SimpleNamespace(value='NEEDS_COPY', wrong_identity=False)

    def run(command, **kwargs):
        words = shlex.split(command[-1])
        if '-m' in words:
            action = words[words.index('-m') + 2]
            calls.append(action)
            payload = json.loads(words[-1])
            receipt = dict(status=known_status.value if action == 'known' else 'COPIED_AND_READY_VERIFIED',
                           lineage_id=source.params['lineage_id'], commit_sha256=selected['commit_sha256'])
            if action == 'stage':
                assert kwargs['stdin'].read() == archive
                assert payload['archive_sha256'] == hashlib.sha256(archive).hexdigest()
                if known_status.wrong_identity:
                    receipt['commit_sha256'] = '0' * 64
            return SimpleNamespace(stdout=json.dumps(receipt).encode())
        assert command[1] == source_spec['wrapper_path']
        assert words[:5] == ['PYTHONDONTWRITEBYTECODE=1', 'CUDA_VISIBLE_DEVICES=', 'python3', '-B', '-c']
        if words[6] == json.dumps(source.params):
            assert 'TRAIN.jsonl' not in words[5] and 'optimizer_rng.pt' not in words[5]
        if 'stdout' in kwargs:
            calls.append('fetch')
            assert command[-1] == phase.copier.source_command(source.params, selected)
            kwargs['stdout'].write(archive)
            return SimpleNamespace(stdout=None)
        calls.append('discover')
        assert command[-1] == phase.copier.source_command(source.params)
        return SimpleNamespace(stdout=json.dumps(dict(status='COMMITTED_CHECKPOINT_SELECTED', selected=selected)).encode())

    monkeypatch.setattr(phase.subprocess, 'run', run)
    directory = tmp_path / 'cycle'
    directory.mkdir()
    return SimpleNamespace(source=source_spec, directory=directory, calls=calls, known=known_status,
                           archive=archive, config=admitted.config)


@pytest.mark.parametrize('known', sorted(phase.KNOWN))
def test_known_checkpoint_never_fetches_adapter_or_stages_again(copying, known):
    copying.known.value = known
    receipt = phase.copy_one(copying.config, copying.source, copying.directory, lambda: None)
    assert receipt['status'] == known
    assert copying.calls == ['discover', 'known']
    assert not list(copying.directory.iterdir())


def test_new_copy_reuses_exact_original_readonly_program(copying):
    validated = []
    receipt = phase.copy_one(copying.config, copying.source, copying.directory, lambda: validated.append(True))
    assert copying.calls == ['discover', 'known', 'fetch', 'stage']
    assert len(validated) == 4
    assert receipt['status'] == 'COPIED_AND_READY_VERIFIED'
    assert (copying.directory / 'kernel.tar').read_bytes() == copying.archive


def test_archive_limit_rejects_before_stage(copying, monkeypatch):
    monkeypatch.setattr(phase, 'MAX_ARCHIVE_BYTES', len(copying.archive) - 1)
    with pytest.raises(ValueError, match='bounded_adapter_archive'):
        phase.copy_one(copying.config, copying.source, copying.directory, lambda: None)
    assert copying.calls == ['discover', 'known', 'fetch']


def test_mismatched_stage_identity_is_not_success(copying):
    copying.known.wrong_identity = True
    with pytest.raises(ValueError, match='verified_stage_identity'):
        phase.copy_one(copying.config, copying.source, copying.directory, lambda: None)


def test_revalidation_failure_stops_before_source_fetch(copying):
    def reject():
        raise ValueError('changed_pin')

    with pytest.raises(ValueError, match='changed_pin'):
        phase.copy_one(copying.config, copying.source, copying.directory, reject)
    assert not copying.calls


def test_copy_schedule_keeps_half_hour_and_three_minute_lead():
    assert phase.next_copy(13 * 3600 + 5 * 60, 20 * 3600) == 13 * 3600 + 27 * 60
    assert phase.next_copy(13 * 3600 + 28 * 60, 20 * 3600) == 13 * 3600 + 57 * 60
    assert phase.next_copy(20 * 3600 - 100, 20 * 3600) is None


@pytest.fixture
def looping(admitted, monkeypatch):
    copied = []
    admitted.config['max_cycles'] = 1
    admitted.bind()
    monkeypatch.setattr(phase.time, 'sleep', lambda seconds: setattr(admitted.clock, 'now', admitted.clock.now + seconds))
    monkeypatch.setattr(phase.scheduler.sidecar, 'identity', lambda pid: admitted.identity)
    monkeypatch.setattr(phase, 'copy_one', lambda config, source, directory, revalidate:
                        copied.append((source['lineage_id'], admitted.clock.now)) or dict(status='ALREADY_STAGED'))
    monkeypatch.setattr(phase, 'remote', lambda config, action: status_for(config))
    return SimpleNamespace(admitted=admitted, copied=copied, output=Path(admitted.config['output_root']))


def test_loop_waits_for_cadence_and_only_copies_original_three(looping):
    phase.copy_loop(looping.admitted.path)
    assert looping.copied == [(name, looping.admitted.config['first_copy_unix']) for name in ('legacy', 'pilot', 'kernel')]
    assert phase.read(looping.output / 'COMPLETE.json')['cycles'] == 1
    assert len(list(looping.output.glob('RELAY_*.json'))) == 1
    assert looping.output.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize('state', ['WAITING_SEGMENT', 'BOUNDED_PHASE_FINISHED', 'FAILED'])
def test_nonrunning_phase_never_contacts_original_sources(looping, monkeypatch, state):
    monkeypatch.setattr(phase, 'remote', lambda config, action: status_for(config, state))
    if state == 'FAILED':
        with pytest.raises(ValueError, match='remote_phase_failed'):
            phase.copy_loop(looping.admitted.path)
        assert (looping.output / 'FAILED.json').is_file()
        assert not (looping.output / 'COMPLETE.json').exists()
    else:
        phase.copy_loop(looping.admitted.path)
    assert not looping.copied


def test_local_output_cannot_be_reused(looping):
    looping.output.mkdir()
    with pytest.raises(FileExistsError):
        phase.copy_loop(looping.admitted.path)
    assert not looping.copied


def test_late_start_skips_missed_dispatch(looping):
    looping.admitted.clock.now = looping.admitted.config['first_dispatch_unix'] + 10
    expected = phase.next_copy(looping.admitted.clock.now, looping.admitted.config['hard_end_unix'])
    phase.copy_loop(looping.admitted.path)
    assert all(when == expected for lineage, when in looping.copied)


def test_transport_errors_are_private_fail_closed_receipts(looping, monkeypatch):
    def fail(*args):
        raise subprocess.CalledProcessError(1, 'synthetic command', stderr=b'synthetic_held')

    monkeypatch.setattr(phase, 'remote', fail)
    with pytest.raises(subprocess.CalledProcessError):
        phase.copy_loop(looping.admitted.path)
    assert not looping.copied
    assert 'synthetic_held' not in (looping.output / 'FAILED.json').read_text()
    assert not (looping.output / 'COMPLETE.json').exists()
