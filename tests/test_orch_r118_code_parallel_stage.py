from copy import deepcopy

import pytest

from gpu import orch_r118_code_parallel_stage as stage
from test_orch_r118_code_parallel_final import custody, write
from test_orch_r108_code_parent_r118_final import prepared


def ready_runtime(value):
    path = value.service / 'RUNTIME.json'
    runtime = stage.io.read(path)
    runtime.update(authorization=value.authorized, cpu_tests=value.plan['cpu_receipt'],
        source_manifest=value.plan['source_manifest'])
    write(path, runtime)
    value.own['old_final_identity'] = value.timer


def test_alternate_measured_CPU_receipt_keeps_same_eight_call_plan(custody):
    ready_runtime(custody)
    before = deepcopy(stage.io.read(custody.root / 'PLAN.json'))
    root = stage.rebind(custody.service, clock=lambda: 100, cancel=custody.cancel)
    after = stage.io.read(root / 'PLAN.json')
    for key in ('native_cap', 'parent_cap', 'decoder', 'task_ids', 'original_plan', 'common_root', 'hard_deadline_unix'):
        assert after[key] == before[key]
    assert stage.io.read(custody.root / 'PLAN.json') == before
    assert custody.cancels == [custody.timer]
    assert after['cpu_receipt'] == custody.plan['cpu_receipt']


def test_missing_Main_launch_identity_never_stops_old_timer(custody):
    ready_runtime(custody)
    (custody.service / 'LAUNCH.json').unlink()
    with pytest.raises(FileNotFoundError):
        stage.rebind(custody.service, clock=lambda: 100, cancel=custody.cancel)
    assert custody.cancels == [] and not custody.destination.exists()


def test_wrong_CPU_receipt_fails_original_source_guard(custody):
    ready_runtime(custody)
    cpu = custody.service / 'BAD_CPU.json'
    write(cpu, dict(passed=True, cuda_initialized=True,
        source_manifest_sha256=custody.plan['source_manifest']['sha256']))
    path = custody.service / 'RUNTIME.json'
    write(path, dict(stage.io.read(path), cpu_tests=stage.handoff.ref(cpu)))
    with pytest.raises(ValueError, match='own_bound_CPU'):
        stage.rebind(custody.service, clock=lambda: 100, cancel=custody.cancel)
    assert not custody.destination.exists() and custody.cancels == []


def test_unpinned_timer_and_Main_selector_never_cancelled(custody):
    ready_runtime(custody)
    custody.own['old_final_identity'] = dict(pid=1519259)
    with pytest.raises(ValueError, match='only_pinned_own_FINAL'):
        stage.rebind(custody.service, clock=lambda: 100, cancel=custody.cancel)
    assert custody.cancels == []


def test_waiter_only_waits_for_actual_launch(custody, monkeypatch):
    ready_runtime(custody)
    path = custody.service / 'LAUNCH.json'
    launched = stage.io.read(path)
    path.unlink()
    waits = []
    def pause(seconds):
        waits.append(seconds)
        write(path, launched)
    stage.wait_for_launch(custody.service, clock=lambda: 100, pause=pause)
    assert waits == [.2] and custody.cancels == []


def test_terminal_guard_prevents_late_staging(custody):
    ready_runtime(custody)
    write(custody.service / 'GUARD_TERMINAL.json', {})
    with pytest.raises(ValueError, match='guard_terminal'):
        stage.wait_for_launch(custody.service, clock=lambda: 100)
