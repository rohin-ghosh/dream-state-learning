"""Campaign CPU tests: real namespaces/flocks/journals, mocked GPU boundaries."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r148_kernel_service_campaign as campaign
from tests.test_orch_r148_kernel_tool_service import make_record, rig, write_records


service = campaign.service


def put(path, value):
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(service.encoded(value))
    path.chmod(0o600)


@pytest.fixture
def setup(rig, monkeypatch):
    monkeypatch.setattr(campaign, 'time', rig.clock)
    monkeypatch.setattr(campaign, 'KERNEL_ROOT', rig.config['root'])
    with service.namespace(rig.config) as (directory, state):
        state.update(phase='STOPPED', reason='WALL_LIMIT')
        service.common.save_state(directory, state)
    config_path = rig.tmp / 'old.CONFIG.json'
    put(config_path, rig.config)
    terminal = rig.tmp / 'old.RUN.log'
    terminal.write_bytes(b'operator launch log\n' + service.encoded(dict(
        status='WALL_LIMIT_NO_REPLAY', state=state)))
    config = dict(directory=str(rig.tmp / 'campaign'), source_root=rig.config['source_root'],
        predecessor_config=str(config_path), predecessor_config_sha256=service.sha(config_path.read_bytes()),
        predecessor_state_sha256=service.sha(service.encoded(state)), predecessor_terminal=str(terminal),
        predecessor_terminal_sha256=service.sha(terminal.read_bytes()), predecessor_pid=2147483647,
        hard_wall_unix=20000, wall_seconds=1800, phase_seconds=300, max_phases=2, phase_calls=1,
        poll_seconds=5, max_calls=4, max_polls=10000, max_reads=10**8, max_read_bytes=2**45,
        max_request_bytes=400000, max_output_bytes=100 * service.OUTPUT_RESERVATION)
    path = rig.tmp / 'CAMPAIGN.json'
    put(path, config)
    log = rig.tmp / 'CPU.log'
    log.write_text('40 passed in 1.00s\n')
    receipt = rig.tmp / 'CPU_RECEIPT.json'
    service.closure()
    campaign.attest(path, log, receipt, 0)
    previous = state['previous_sha256']
    for index in range(state['next_index'], state['next_index'] + 10):
        record = make_record(index, 'CHECKPOINT_METADATA', {'path': 'DO_NOT_OPEN'}, previous)
        write_records(rig.config, [record])
        previous = record['sha256']

    def probes(probe_root, runtime_root, admission_path):
        assert runtime_root == rig.config['runtime_root']
        with pytest.raises(BlockingIOError):
            with service.lock_file(service.executor.LOCK_PATH):
                pass
        admission = campaign.document(admission_path)
        assert admission['gpu_uuid'] == service.executor.GPU_UUID
        assert admission['device_minor'] == 1
        assert rig.census.call_count >= 1
        root = Path(probe_root)
        root.mkdir()
        gate = dict(rig.gate, observed_unix=rig.clock.now, expires_unix=rig.clock.now + 3600)
        put(root / 'GATE.json', gate)
        rig.clock.now += 1
        return dict(passed=True, gate_path=str(root / 'GATE.json'), checks=26)

    probe = Mock(side_effect=probes)
    monkeypatch.setattr(service.executor, 'run_trusted_probes', probe)

    def phase_run(phase_config):
        with service.namespace(phase_config) as (directory, phase_state):
            index = phase_state['next_index']
            _, record = service.record(phase_config, index)
            phase_state.update(phase='STOPPED', reason='CALL_LIMIT', calls=phase_state['calls'] + 1,
                               next_index=index + 1, previous_sha256=record['sha256'])
            service.common.save_state(directory, phase_state)
        rig.clock.now += 1
        return dict(status='STOPPED_NO_REPLAY', error='CALL_LIMIT', error_type='ValueError', state=phase_state)

    run = Mock(side_effect=phase_run)
    real_run = service.run
    monkeypatch.setattr(service, 'run', run)
    return SimpleNamespace(rig=rig, config=config, path=path, receipt=receipt, log=log,
                           probe=probe, run=run, state=state, real_run=real_run)


def reattest(setup):
    put(setup.path, setup.config)
    setup.receipt.unlink()
    campaign.attest(setup.path, setup.log, setup.receipt, 0)


def execute(setup):
    return campaign.run(str(setup.path), str(setup.receipt))


def test_phase_cursor_counters_original_prefix_and_unique_evidence(setup):
    result = execute(setup)
    assert result['status'] == 'STOPPED'
    assert result['state']['reason'] == 'PHASE_LIMIT'
    assert result['state']['service_state']['calls'] == 2
    assert setup.probe.call_count == setup.run.call_count == 2
    configs = [call.args[0] for call in setup.run.call_args_list]
    assert configs[0]['state'] != configs[1]['state']
    assert configs[0]['poll_seconds'] == configs[1]['poll_seconds'] == 5
    assert setup.rig.config['poll_seconds'] == 0.1
    for key in ('root', 'start_index', 'start_after_sha256', 'journal_id', 'journal_manifest_sha256',
                'runtime_root', 'runtime_manifest_sha256', 'lease_receipt_path', 'lease_receipt_sha256',
                'executor_lock', 'gpu_uuid', 'device_minor'):
        assert configs[0][key] == configs[1][key] == setup.rig.config[key]
    initial = [campaign.document(Path(config['state']).parent / 'INITIAL_STATE.json') for config in configs]
    assert initial[0]['next_index'] == setup.state['next_index']
    assert initial[1]['next_index'] == setup.state['next_index'] + 1
    assert initial[1]['calls'] == 1
    assert initial[1]['reads'] > initial[0]['reads']
    assert initial[1]['output_reserved'] > initial[0]['output_reserved']
    assert campaign.document(Path(setup.rig.config['state']) / 'STATE.json') == setup.state
    assert len(list(Path(setup.config['directory']).glob('phase_*/TERMINAL.json'))) == 2


def test_cumulative_call_limit_stops_without_extra_probe(setup):
    setup.config.update(max_calls=1, max_phases=12)
    reattest(setup)
    result = execute(setup)
    assert result['state']['reason'] == 'CALL_LIMIT'
    assert result['state']['service_state']['calls'] == 1
    assert setup.probe.call_count == setup.run.call_count == 1


def test_prior_completed_calls_are_inherited_not_reset(setup):
    setup.state['calls'] = 1
    put(Path(setup.rig.config['state']) / 'STATE.json', setup.state)
    terminal = Path(setup.config['predecessor_terminal'])
    put(terminal, dict(status='WALL_LIMIT_NO_REPLAY', state=setup.state))
    setup.config.update(predecessor_state_sha256=service.sha(service.encoded(setup.state)),
                        predecessor_terminal_sha256=service.sha(terminal.read_bytes()), max_calls=2)
    reattest(setup)
    result = execute(setup)
    assert result['state']['service_state']['calls'] == 2
    assert setup.probe.call_count == 1
    initial = campaign.document(Path(setup.config['directory']) / 'phase_01/INITIAL_STATE.json')
    assert initial['calls'] == 1


@pytest.mark.parametrize('field,value', [('phase', 'INTENT'), ('phase', 'DISPATCH_PUBLICATION_INTENT'),
    ('reason', 'POLL_LIMIT'), ('reason', 'READ_LIMIT'), ('reason', 'fresh_gate_required'),
    ('pending_index', 834), ('pending_response_sha256', 'a' * 64)])
def test_unsafe_previous_state_never_replayed(setup, field, value):
    setup.state[field] = value
    put(Path(setup.rig.config['state']) / 'STATE.json', setup.state)
    setup.config['predecessor_state_sha256'] = service.sha(service.encoded(setup.state))
    put(setup.path, setup.config)
    with pytest.raises(ValueError, match='unsafe_predecessor_state'):
        execute(setup)
    setup.probe.assert_not_called()
    setup.run.assert_not_called()


@pytest.mark.parametrize('missing', ['state', 'terminal', 'record', 'namespace_lock'])
def test_missing_predecessor_fails_before_probe(setup, missing):
    paths = dict(state=Path(setup.rig.config['state']) / 'STATE.json',
                 terminal=Path(setup.config['predecessor_terminal']),
                 record=Path(setup.rig.config['root']) / 'stream/records' / f'{setup.state["next_index"] - 1:020d}.json',
                 namespace_lock=Path(setup.rig.config['state']) / 'SERVICE.lock')
    paths[missing].unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        execute(setup)
    setup.probe.assert_not_called()


def test_live_original_process_refused_without_signal(setup):
    setup.config['predecessor_pid'] = os.getpid()
    put(setup.path, setup.config)
    with pytest.raises(ValueError, match='predecessor_process_not_gone'):
        execute(setup)
    setup.probe.assert_not_called()


@pytest.mark.parametrize('status', ['ERROR', 'WALL_LIMIT_NO_REPLAY', 'STOPPED_NO_REPLAY'])
def test_terminal_contract_not_exit_code_alone(setup, status):
    value = dict(status=status, state=dict(setup.state, calls=1))
    terminal = Path(setup.config['predecessor_terminal'])
    put(terminal, value)
    setup.config['predecessor_terminal_sha256'] = service.sha(terminal.read_bytes())
    put(setup.path, setup.config)
    with pytest.raises(ValueError, match='terminal_state_mismatch'):
        execute(setup)


@pytest.mark.parametrize('failure', ['probe', 'gate', 'census', 'runtime'])
def test_gate_probe_census_runtime_failure_is_terminal_no_retry(setup, failure):
    if failure == 'probe':
        setup.probe.side_effect = RuntimeError('ambiguous_probe')
    elif failure == 'gate':
        setup.probe.side_effect = lambda *args: dict(passed=False, checks=25)
    elif failure == 'census':
        setup.rig.census.side_effect = ValueError('reserved_GPU_not_empty')
    else:
        service.executor.validate_runtime.side_effect = ValueError('runtime_changed')
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    assert setup.probe.call_count <= 1
    setup.run.assert_not_called()
    with pytest.raises(ValueError, match='campaign_already_claimed_no_retry'):
        execute(setup)


def test_probe_failure_poisons_existing_executor_lock(setup):
    setup.probe.side_effect = RuntimeError('lost_result')
    execute(setup)
    assert campaign.document(service.executor.LOCK_PATH)['result_status'] == 'DISPATCH_INCOMPLETE'


@pytest.mark.parametrize('key,value', [('max_calls', 25), ('max_phases', 13), ('phase_seconds', 1801),
    ('wall_seconds', 21601), ('phase_seconds', 180), ('max_reads', True), ('hard_wall_unix', float('inf')),
    ('poll_seconds', 0.01), ('poll_seconds', 61), ('poll_seconds', True)])
def test_finite_configuration_bounds(setup, key, value):
    setup.config[key] = value
    if value == float('inf'):
        setup.path.write_text(json.dumps(setup.config))
    else:
        put(setup.path, setup.config)
    with pytest.raises((ValueError, AssertionError)):
        execute(setup)
    setup.probe.assert_not_called()


@pytest.mark.parametrize('kind', ['wall', 'lease'])
def test_wall_and_lease_exhaustion_no_probes(setup, kind):
    if kind == 'wall':
        setup.config['hard_wall_unix'] = setup.rig.clock.now + 150
    else:
        setup.rig.clock.now = 100000 - 21600 - 150
        setup.config['hard_wall_unix'] = 100000
    reattest(setup)
    with pytest.raises(ValueError, match='campaign_wall_exhausted'):
        execute(setup)
    setup.probe.assert_not_called()


def test_single_owner_real_flock_and_persistent_one_shot_claim(setup):
    lock = campaign.campaign_lock(setup.rig.config)
    with service.lock_file(lock):
        with pytest.raises(BlockingIOError):
            execute(setup)
    setup.probe.assert_not_called()
    execute(setup)
    with pytest.raises(ValueError, match='campaign_already_claimed_no_retry'):
        execute(setup)


@pytest.mark.parametrize('target', ['config', 'runtime', 'lease', 'source', 'cpu_log'])
def test_immutable_pins_refuse_change(setup, monkeypatch, target):
    if target == 'config':
        setup.config['phase_calls'] = 2
        put(setup.path, setup.config)
    elif target == 'runtime':
        (Path(setup.rig.config['runtime_root']) / 'MANIFEST.json').write_text('{}')
    elif target == 'lease':
        Path(setup.rig.config['lease_receipt_path']).write_text('{}')
    elif target == 'source':
        monkeypatch.setattr(campaign, 'closure', lambda: {'changed': 'hash'})
    else:
        setup.log.write_text('changed log')
    with pytest.raises(ValueError):
        execute(setup)
    setup.probe.assert_not_called()


def test_service_exception_is_not_retried(setup):
    setup.run.side_effect = RuntimeError('uncertain_publication')
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    assert setup.run.call_count == setup.probe.call_count == 1
    assert result['state']['phase'] == 'FAILED_NO_RETRY'


def test_real_service_metadata_cursor_continuity_no_historical_replay(setup, monkeypatch):
    monkeypatch.setattr(service, 'run', setup.real_run)
    result = execute(setup)
    assert result['status'] == 'STOPPED'
    assert result['state']['service_state']['calls'] == 0
    assert result['state']['service_state']['next_index'] == setup.state['next_index'] + 10
    assert setup.probe.call_count == 2
    setup.rig.action.assert_not_called()
    first = campaign.document(Path(setup.config['directory']) / 'phase_01/TERMINAL.json')['state']
    second = campaign.document(Path(setup.config['directory']) / 'phase_02/INITIAL_STATE.json')
    assert first['next_index'] == second['next_index']
    assert first['previous_sha256'] == second['previous_sha256']
    assert second['reads'] > first['reads']


def test_no_other_gpu_and_no_probe_while_executor_busy(setup):
    with service.lock_file(service.executor.LOCK_PATH):
        result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    setup.probe.assert_not_called()
    setup.rig.census.assert_not_called()


def test_successful_probe_uses_original_admission_gate_and_scope(setup):
    execute(setup)
    for call in setup.probe.call_args_list:
        admission = campaign.document(call.args[2])
        service.executor.validate_admission(call.args[2], admission['observed_unix'])
        assert admission['hard_wall_unix'] <= setup.config['hard_wall_unix']
        assert admission['hard_wall_unix'] <= campaign.lease_wall(setup.rig.config)
        assert admission['device_minor'] == 1
        assert admission['gpu_uuid'] == service.executor.GPU_UUID
    assert service.executor.device_identity.return_value['physical_index'] == 2


def test_ambiguous_previous_executor_receipt_stops(setup):
    put(service.executor.LOCK_PATH, dict(result_status='DISPATCH_INCOMPLETE', last_finished_unix=999))
    result = execute(setup)
    assert result['state']['reason'] == 'ambiguous_executor_predecessor'
    setup.probe.assert_not_called()


def test_cpu_receipt_requires_passing_log_and_private_config(setup):
    setup.path.chmod(0o644)
    with pytest.raises(ValueError, match='private_operator_file_required'):
        execute(setup)
    setup.path.chmod(0o600)
    setup.log.write_text('1 failed, 40 passed')
    with pytest.raises(ValueError, match='passing_Main_CPU_log_required'):
        campaign.attest(setup.path, setup.log, setup.receipt, 0)


@pytest.mark.parametrize('clock', ['wall', 'monotonic'])
def test_independent_wall_and_monotonic_campaign_limits(setup, monkeypatch, clock):
    monotonic = SimpleNamespace(now=1000)
    monkeypatch.setattr(campaign, 'time', SimpleNamespace(time=setup.rig.clock.time,
                                                        monotonic=lambda: monotonic.now))
    original_run = setup.run.side_effect

    def consume_time(config):
        result = original_run(config)
        if clock == 'wall':
            setup.rig.clock.now += 2000
        else:
            monotonic.now += 2000
        return result

    setup.run.side_effect = consume_time
    result = execute(setup)
    assert result['state']['reason'] == 'WALL_LIMIT'
    assert setup.run.call_count == setup.probe.call_count == 1


@pytest.mark.parametrize('mutation', ['config', 'runtime', 'lease', 'cursor', 'gate', 'probe_time'])
def test_mutation_during_probe_stops_before_service(setup, mutation):
    original_probe = setup.probe.side_effect

    def altered(*args):
        result = original_probe(*args)
        if mutation == 'config':
            setup.path.write_bytes(setup.path.read_bytes() + b'\n')
        elif mutation == 'runtime':
            (Path(setup.rig.config['runtime_root']) / 'MANIFEST.json').write_text('{}')
        elif mutation == 'lease':
            Path(setup.rig.config['lease_receipt_path']).write_text('{}')
        elif mutation == 'cursor':
            predecessor_path = Path(setup.rig.config['root']) / 'stream/records' / f'{setup.state["next_index"] - 1:020d}.json'
            predecessor_path.unlink()
        elif mutation == 'gate':
            gate = campaign.document(result['gate_path'])
            gate['expires_unix'] = setup.rig.clock.now + 100
            put(Path(result['gate_path']), gate)
        else:
            setup.rig.clock.now += setup.config['phase_seconds']
        return result

    setup.probe.side_effect = altered
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    assert setup.probe.call_count == 1
    setup.run.assert_not_called()


@pytest.mark.parametrize('target', ['state', 'terminal', 'config'])
def test_previous_phase_receipt_changes_block_next_probe(setup, monkeypatch, target):
    original_frozen = campaign.frozen
    mutated = False

    def change_after_service(*args):
        nonlocal mutated
        original_frozen(*args)
        if setup.run.call_count and not mutated:
            mutated = True
            config = setup.run.call_args.args[0]
            root = Path(config['state'])
            if target == 'state':
                value = campaign.document(root / 'STATE.json')
                value['pending_index'] = value['next_index']
                put(root / 'STATE.json', value)
            elif target == 'terminal':
                put(root.parent / 'TERMINAL.json', {'status': 'UNKNOWN'})
            else:
                put(root / 'CONFIG.json', {})

    monkeypatch.setattr(campaign, 'frozen', change_after_service)
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    assert setup.probe.call_count == setup.run.call_count == 1


def test_read_and_output_overhead_reserved_before_probes(setup):
    setup.config['max_output_bytes'] = 1024
    reattest(setup)
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    setup.probe.assert_not_called()


def test_pending_service_intent_is_preserved_not_renewed(setup):
    def pending(config):
        with service.namespace(config) as (directory, state):
            state.update(phase='DISPATCH_PUBLICATION_INTENT', pending_index=state['next_index'], calls=1)
            service.common.save_state(directory, state)
        return dict(status='STOPPED_NO_REPLAY', state=state)

    setup.run.side_effect = pending
    result = execute(setup)
    assert result['status'] == 'FAILED_NO_RETRY'
    assert result['state']['observed_service_state']['calls'] == 1
    assert setup.probe.call_count == setup.run.call_count == 1
