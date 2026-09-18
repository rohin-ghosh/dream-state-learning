from copy import deepcopy
import subprocess
import sys

import pytest

from gpu import orch_r118_code_parallel_final as final
from test_orch_r108_code_parent_r118_final import prepared


def write(path, value):
    final.io.write(path, value, replace=path.exists())


@pytest.fixture
def custody(prepared, monkeypatch):
    value = prepared
    monkeypatch.setattr(final, 'SOURCE_ROOT', value.source)
    value.service = value.root.parent / 'parallel'
    value.destination = value.root.parent / 'rebound_final'
    value.old_native, value.old_guard, value.timer = ({'pid': index} for index in (1, 2, 3))
    value.new_native, value.new_guard = ({'pid': index} for index in (4, 5))
    write(value.root / 'CPU_DISPATCH.json', dict(identity=value.timer))
    release = value.root.parent / 'HANDOFF.json'
    write(release, dict(all_original_processes_exited=True, native=dict(identity=value.old_native),
        guardian=value.old_guard))
    write(value.service / 'RUNTIME.json', dict(root=str(value.original), handoff=final.handoff.ref(release)))
    write(value.service / 'LAUNCH.json', dict(identity=value.new_native, guardian=value.new_guard))
    value.live = {3, 4, 5}
    monkeypatch.setattr(final.handoff, 'alive', lambda identity: identity['pid'] in value.live)
    value.own = dict(final_old_root=str(value.root), final_new_root=str(value.destination),
        service=str(value.service), source_manifest_sha256=value.plan['source_manifest']['sha256'])
    monkeypatch.setattr(final.handoff, 'authorize', lambda *args: ({}, value.own, {}))
    value.authorized = dict(path='synthetic_Main_authorization', sha256='a' * 64)
    value.cancels = []
    def cancel(root, expected, **kwargs):
        value.cancels.append(expected)
        value.live.remove(expected['pid'])
        return dict(identity=expected, cancelled_only_CPU_waiter=True)
    value.cancel = cancel
    return value


def rebind(value):
    return final.rebind(value.root, value.destination, value.service, value.authorized,
        clock=lambda: 100, cancel=value.cancel)


def test_rebind_same_eight_calls_no_sealed_read_no_selector(custody, monkeypatch):
    read = final.io.read
    sealed = custody.original / 'COHORT.json'
    monkeypatch.setattr(final.io, 'read', lambda path: pytest.fail('sealed_read') if path == sealed else read(path))
    before = deepcopy(custody.plan)
    result = rebind(custody)
    for name in ('native_cap', 'parent_cap', 'hard_deadline_unix', 'cutoff_unix', 'task_ids',
                 'decoder', 'cohort', 'common_root', 'main_binding_path', 'original_plan'):
        assert result[name] == before[name]
    assert final.io.read(custody.root / 'PLAN.json') == before
    assert final.io.read(custody.destination / 'FINAL_REBIND.json')['native_cap_added'] == 0
    assert custody.cancels == [custody.timer]
    assert custody.live == {4, 5}


@pytest.mark.parametrize('name', ['ATTEMPT_ONCE', 'LAUNCH.json', 'reservations/FINAL_00.json'])
def test_any_old_charge_or_attempt_blocks_rebind(custody, name):
    path = custody.root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    with pytest.raises(ValueError, match='charges_never_reset'):
        rebind(custody)
    assert not custody.destination.exists() and not custody.cancels


def test_exact_Main_destination_required_before_timer_stop(custody):
    custody.own['final_new_root'] += '_foreign'
    with pytest.raises(ValueError, match='Main_exact_FINAL'):
        rebind(custody)
    assert not custody.cancels


def test_changed_source_rejected_before_timer_stop(custody):
    (custody.source / 'fixture.py').write_text('changed prospective bytes')
    with pytest.raises(ValueError, match='source_preserved'):
        rebind(custody)
    assert not custody.cancels


def test_original_actor_alive_blocks_new_custody(custody):
    custody.live.add(1)
    with pytest.raises(ValueError, match='actual_exit'):
        rebind(custody)
    assert not custody.cancels


def test_rebind_failure_preserves_started_attempt(custody):
    def failure(*args, **kwargs):
        raise RuntimeError('synthetic timer failure')
    custody.cancel = failure
    with pytest.raises(RuntimeError):
        rebind(custody)
    assert (custody.destination / 'REBIND_STARTED.json').exists()
    with pytest.raises(ValueError, match='new_eval_custody'):
        rebind(custody)


def test_release_requires_new_native_guard_cursor_and_unchanged_ledger(custody):
    rebind(custody)
    with pytest.raises(ValueError, match='new_parallel_native_and_guard_exited'):
        final.validate_release(custody.destination)
    custody.live.clear()
    cursor = custody.service / 'cursors/C001.json'
    write(cursor, dict(all_readouts_settled=True, next_cycle=2))
    write(custody.service / 'CLEAN_RELEASE.json', dict(actual_settled_boundary=True,
        identity=custody.new_native, cursor=final.handoff.ref(cursor), charges=dict(preserved={})))
    write(custody.service / 'GUARD_TERMINAL.json', dict(identity=custody.new_native, native_alive=False))
    assert final.validate_release(custody.destination)['custody']['sha256']
    write(custody.original / 'reservations/R001_DEV_DEV_0.json', {})
    with pytest.raises(ValueError, match='no_post_parallel_release_calls'):
        final.validate_release(custody.destination)


def test_changed_rebind_reference_rejected_before_wait(custody):
    rebind(custody)
    write(custody.destination / 'FINAL_REBIND.json', dict(unbound=True))
    with pytest.raises(ValueError, match='immutable_reference_changed'):
        final.wait_release(custody.destination)


def test_cloned_FINAL_dispatch_uses_new_wrapper_not_old_release():
    functions = final.functions()
    for name in ('schedule', 'native', 'run_child'):
        assert functions[name].__globals__['MODULE'] == final.MODULE
        assert functions[name].__globals__['release'].validate_release is final.validate_release
    assert functions['validate_binding'].__globals__['selector'] is final.original.selector
    assert final.original.MODULE != final.MODULE


def test_late_timer_cancellation_never_signals():
    with pytest.raises(ValueError, match='before_old_drain_window'):
        final.cancel_timer('/no_real_timer', dict(pid=0), clock=lambda: final.original.CUTOFF - 599)


def test_bind_supervision_uses_actual_new_timer_not_old_TIMER(custody, monkeypatch):
    rebind(custody)
    timer = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)',
        final.MODULE, 'schedule', str(custody.destination)])
    try:
        identity = final.handoff.identities.identity(timer.pid)
        custody.live.add(timer.pid)
        write(custody.destination / 'CPU_DISPATCH.json', dict(identity=identity))
        write(custody.destination / 'SCHEDULER_STARTED.json', dict(pid=timer.pid))
        monkeypatch.setattr(final.handoff, 'collective_identity', lambda value: dict(value, synthetic=True))
        result = final.bind_supervision(custody.destination, custody.authorized)
        assert result['final_identity_bindings'][0]['identity']['pid'] == timer.pid
        assert result['native_identity']['pid'] == 4
        assert result['guard_identity']['pid'] == 5
        assert final.io.read(custody.service / 'SUPERVISION.json') == result
        assert not final.handoff.alive(custody.timer)
    finally:
        timer.terminate()
        timer.wait(timeout=3)
