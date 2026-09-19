"""Bounded CPU tests: no GPU, no held records, no old request replay."""

from pathlib import Path
import time
from unittest.mock import patch

import pytest

from gpu import orch_r158_kernel_execution as renewal
from tests.test_orch_r148_kernel_tool_service import chain, document, rig


def pair():
    config = dict(start_index=100, max_calls=2, max_polls=10000, max_reads=10000000,
                  max_read_bytes=2**44, max_request_bytes=2400000, max_output_bytes=419430400)
    state = dict(schema=renewal.service.SCHEMA, phase='STOPPED', reason='WALL_LIMIT',
                 config_sha256=renewal.service.sha(renewal.service.encoded(config)),
                 next_index=123, previous_sha256='a' * 64, calls=0, polls=7031,
                 reads=3133300, read_bytes=2887123992576, request_bytes=0, output_reserved=276824064)
    return config, state, dict(status='WALL_LIMIT_NO_REPLAY', state=state)


def test_clean_phase_can_renew_without_resetting_counters():
    config, state, terminal = pair()
    assert renewal.renew_allowed(config, state, terminal)
    assert renewal.terminal_counters(config, state, terminal)['polls'] == 7031


@pytest.mark.parametrize('pending', ['pending_index', 'pending_response_sha256', 'pending_publication'])
def test_pending_identity_cannot_be_cleared_for_renewal(pending):
    config, state, terminal = pair()
    state[pending] = 'untouched'
    with pytest.raises(ValueError, match='unsafe_predecessor_state'):
        renewal.renew_allowed(config, state, terminal)
    assert state[pending] == 'untouched'


@pytest.mark.parametrize('phase', ['INTENT', 'DISPATCH_PUBLICATION_INTENT', 'READY'])
def test_nonterminal_or_uncertain_phase_never_renews(phase):
    config, state, terminal = pair()
    state['phase'] = phase
    with pytest.raises(ValueError):
        renewal.renew_allowed(config, state, terminal)


def test_completed_call_budget_is_not_reset():
    config, state, terminal = pair()
    state['calls'] = 2
    assert not renewal.renew_allowed(config, state, terminal)


def test_terminal_and_cursor_must_match():
    config, state, terminal = pair()
    with pytest.raises(ValueError, match='terminal_state_mismatch'):
        renewal.terminal_counters(config, state, dict(terminal, state={}))
    state['next_index'] = 99
    with pytest.raises(ValueError, match='cursor_regression'):
        renewal.terminal_counters(config, state, terminal)


def test_prior_budget_overrun_refuses_renewal():
    config, state, terminal = pair()
    state['polls'] = 10001
    with pytest.raises(ValueError, match='bounded_prior_polls'):
        renewal.terminal_counters(config, state, terminal)


def test_expired_cpu_proof_cannot_start_gate():
    gate = dict(schema='R158_CPU_V1', exit_code=0, source_pins={}, cpu_log='/tmp/log',
                cpu_log_sha256=renewal.service.sha(b'PASS'), observed_unix=time.time() - 1801)
    with patch.object(renewal.service, 'read', side_effect=[renewal.service.encoded(gate), b'PASS']), \
            patch.object(renewal, 'source_pins', return_value={}), \
            patch.object(renewal, 'refresh_gate') as gpu:
        with pytest.raises(ValueError, match='fresh_bound_CPU_gate'):
            renewal.activate(Path('/tmp/operator'))
        gpu.assert_not_called()


def test_renewal_is_bounded_and_only_original_targets():
    assert renewal.PHASES == 2
    assert renewal.PHASE_SECONDS == 1500
    assert set(renewal.prior.ROOTS) == {0, 4}
    assert renewal.PHASES * renewal.PHASE_SECONDS < 3600 - 180


def test_refused_gap_is_not_replayed_and_inflight_frontier_refused():
    assert renewal.prior.future_start(dict(kind='UPDATE', index=3512), 3419) == 3513
    for kind in ('REQUEST', 'RESPONSE'):
        with pytest.raises(ValueError, match='inflight_generation'):
            renewal.prior.future_start(dict(kind=kind, index=3512), 3419)


def test_real_namespaces_skip_gap_then_preserve_exact_phase_cursor(rig, monkeypatch):
    monkeypatch.setattr(renewal, 'time', rig.clock)
    records = chain(rig.config)
    previous = dict(phase='STOPPED', next_index=rig.config['start_index'], calls=0,
                    polls=3, reads=4, read_bytes=50, request_bytes=0, output_reserved=0)
    first = renewal.seed(rig.tmp / 'phase1', rig.config, previous, frontier=True)
    state = document(Path(first['state']) / 'STATE.json')
    assert first['start_index'] == records[-1]['index'] + 1
    assert state['next_index'] == first['start_index']
    assert state['polls'] == 3
    state.update(phase='STOPPED', reason='WALL_LIMIT')
    rig.clock.now += renewal.PHASE_SECONDS
    second = renewal.seed(rig.tmp / 'phase2', first, state)
    resumed = document(Path(second['state']) / 'STATE.json')
    assert resumed['next_index'] == state['next_index']
    assert resumed['previous_sha256'] == state['previous_sha256']
    assert resumed['polls'] == state['polls']
    rig.action.assert_not_called()


def test_fresh_gate_requires_all_checks_without_fixture_dispatch(rig, monkeypatch):
    monkeypatch.setattr(renewal, 'time', rig.clock)
    monkeypatch.setattr(renewal.smoke, 'time', rig.clock)
    directory = rig.tmp / 'operator'
    directory.mkdir()

    def probes(probe_directory, runtime, admission):
        probe_directory.mkdir()
        (probe_directory / 'GATE.json').write_bytes(renewal.service.encoded(rig.gate))
        return dict(passed=True, checks=26)

    with patch.object(renewal.service.executor, 'run_trusted_probes', side_effect=probes) as probe, \
            patch.object(renewal.smoke, 'run') as fixture:
        result = renewal.refresh_gate(directory, rig.config)
        assert result == str(directory / 'probes/GATE.json')
        probe.assert_called_once()
        fixture.assert_not_called()
        rig.action.assert_not_called()


def test_partial_probe_matrix_cannot_become_gate(rig, monkeypatch):
    monkeypatch.setattr(renewal, 'time', rig.clock)
    monkeypatch.setattr(renewal.smoke, 'time', rig.clock)
    directory = rig.tmp / 'operator'
    directory.mkdir()
    with patch.object(renewal.service.executor, 'run_trusted_probes', return_value=dict(passed=True, checks=25)):
        with pytest.raises(ValueError, match='all_26_real_confinement_checks'):
            renewal.refresh_gate(directory, rig.config)
    assert not (directory / 'probes/GATE.json').exists()
