from collections import Counter
from copy import deepcopy
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r126_code_capacity as successor
from gpu import orch_r108_code_parent_r109_run as runtime


def test_frozen_chunks_have_exact_native_and_parent_slots():
    rows = successor.capacity.chunk_registry(0)
    calls = successor.schedules(rows)
    assert Counter(row['kind'] for row in calls) == dict(NATIVE=960, PARENT=128)
    assert not any(row['kind'] == 'PARENT' and row['slot'] == 0 for row in calls)
    assert all(101 <= row['cycle'] <= 164 for row in calls)
    assert sum(row['phase'] == 'held' for row in calls) == 256


def test_meta_policy_supports_prospective_cycles_not_old_limit():
    original = successor.capacity.original
    rows = successor.capacity.chunk_registry(0)
    bound = successor.bind_policy(original, rows)
    task = bound.meta_task('node3_episode', 101)
    payload = bound.meta_payload('node3_episode', task, 1, 'actual carried thought', [], [''])
    assert payload['episodes'][0]['public_experience']['completed_train_episode_ids'] == [row['task_id'] for row in rows[:2]]
    with pytest.raises(ValueError):
        original.meta_task('node3_episode', 101)
    with pytest.raises(ValueError):
        bound.meta_task('node3_episode', 4197)


def test_cycle_wrapper_preserves_original_prompts_and_no_optimizer():
    rows = successor.capacity.chunk_registry(0)[:6]
    bound = successor.cycle_function(runtime, dict(own_context='carried', lessons=[]), rows)
    source = inspect.getsource(runtime.cycles)
    assert 'Retain or revise your solution.' in source
    assert bound.__globals__['restored_memory'] == 'carried'
    assert bound.__globals__['first_cycle'] == bound.__globals__['last_cycle'] == 101
    assert 'sleep' not in bound.__code__.co_names and 'optimizer' not in bound.__code__.co_names


def test_process_identity_reuse_is_not_original_owner(monkeypatch):
    monkeypatch.setattr(Path, 'exists', lambda path: True)
    monkeypatch.setattr(successor, 'identity', lambda pid: dict(pid=pid, start_ticks='new', uid=1, boot_id='boot'))
    assert successor.exited(dict(pid=123, start_ticks='old', uid=1, boot_id='boot'))
    assert not successor.exited(dict(pid=123, start_ticks='new', uid=1, boot_id='boot'))


def test_argv_drift_is_not_an_exit_proof(monkeypatch):
    expected = dict(pid=123, uid=1, start_ticks='same', boot_id='same', command_sha256='old')
    monkeypatch.setattr(Path, 'exists', lambda path: True)
    monkeypatch.setattr(successor, 'identity', lambda pid: dict(expected, command_sha256='different'))
    assert not successor.exited(expected)


def test_release_never_reads_or_stops_live_actor(tmp_path, monkeypatch):
    monkeypatch.setattr(successor, 'exited', lambda item: False)
    with pytest.raises(ValueError, match='both_original_actors_exited'):
        successor.release_snapshot(dict(original_identities=[dict(pid=1)]), dict(root=str(tmp_path)))
    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    root = tmp_path / 'old'
    write = successor.io.write
    write(root / 'TERMINAL.json', dict(status='COMPLETE'))
    write(root / 'GUARD_TERMINAL.json', dict(returncode=0))
    write(root / successor.LANE / 'CYCLE_100_COMPLETE.json', dict(cycle=100))
    write(root / 'AFTER.json', dict(unchanged=True, model=dict(base='frozen')))
    write(root / 'ACTOR_READY.json', dict(model=dict(base='frozen')))
    context = dict(status='COMPLETE', own_context='latest actual own TRAIN reflection', weight_updates=0)
    context['after_context_sha256'] = successor.capacity.original.digest(context['own_context'])
    write(root / successor.LANE / 'CONTEXT_DISTILLATION_C100.json', context)
    write(root / 'initial.json', dict(own_context='old', lessons=['prior exact lesson']))
    for cycle in range(27, 101):
        for offset in range(15):
            write(root / successor.LANE / 'cells' / f'C{cycle}_{offset}.json',
                dict(kind='NATIVE', cycle=cycle, status='COMPLETE', cell_id=f'C{cycle}_{offset}'))
        for slot in (1, 2):
            name = f'P{cycle}_{slot}'
            write(root / successor.LANE / 'cells' / (name + '.json'), dict(kind='PARENT', cycle=cycle,
                status='PENDING' if cycle == 100 else 'MISSING', slot=slot, lesson='', cell_id=name))
            if cycle == 100:
                write(root / 'parent_queue' / (name + '.request.json'), dict(id=name, lane_deadline_unix=9999999999))
    monkeypatch.setattr(successor, 'exited', lambda item: True)
    old = dict(root=str(root), ancestry=dict(native_used=383, parent_used=128),
        inputs=dict(context=successor.io.ref(root / 'initial.json')))
    return root, dict(original_identities=[dict(pid=123)]), old


def test_release_carries_exact_counts_context_and_pending_without_edit(boundary):
    root, armed, old = boundary
    before = {str(path):successor.io.ref(path) for path in root.rglob('*.json')}
    result = successor.release_snapshot(armed, old)
    assert result['boundary']['native_used'] == 1493
    assert result['boundary']['parent_used'] == 276
    assert len(result['pending_parents']) == 2
    assert result['context']['lessons'] == ['prior exact lesson'] + [''] * 370
    assert before == {str(path):successor.io.ref(path) for path in root.rglob('*.json')}


@pytest.mark.parametrize('target,patch', [
    ('TERMINAL.json', dict(status='FAILED')),
    ('GUARD_TERMINAL.json', dict(returncode=1)),
    ('AFTER.json', dict(unchanged=False, model=dict(base='frozen'))),
    ('campaign_code_parent/cells/C100_0.json', dict(kind='NATIVE', cycle=100, status='STARTED')),
])
def test_reject_incomplete_or_unverified_boundary(boundary, target, patch):
    root, armed, old = boundary
    runtime.write(root / target, patch)
    if target == 'TERMINAL.json':
        snapshot = successor.release_snapshot(armed, old)
        assert snapshot['boundary']['terminal_status'] == 'FAILED'
    else:
        with pytest.raises(ValueError):
            successor.release_snapshot(armed, old)


def test_watch_has_no_process_signals_and_requires_complete_release():
    source = inspect.getsource(successor.watch)
    assert 'activate(root)' in source and 'guard(root)' in source
    for forbidden in ('kill(', 'terminate(', 'stop_owned(', 'parent_call('):
        assert forbidden not in source
    assert source.index('activate(root)') < source.index('guard(root)')


def test_native_one_real_policy_cycle_uses_15_calls_two_async_parents(tmp_path, monkeypatch):
    root = tmp_path / 'new'
    old_root = tmp_path / 'old'
    old_root.mkdir()
    for name in (successor.LANE + '/cells', 'parent_queue', 'delayed_interventions', 'carried_parents'):
        (root / name).mkdir(parents=True, exist_ok=True)
    write, ref = successor.io.write, successor.io.ref
    rows = successor.capacity.chunk_registry(0)[:6]
    write(root / 'cohort.json', rows)
    write(root / 'calls.json', successor.schedules(rows))
    write(root / 'cohorts.json', dict(chunks=[dict(chunk=0, cohort=ref(root / 'cohort.json'),
        reservations=ref(root / 'calls.json'), registry_sha256=successor.capacity.digest(rows))]))
    write(root / 'old_after.json', dict(model=dict(frozen=True)))
    write(root / 'release.json', dict(pending_parents=[], boundary=dict(after=ref(root / 'old_after.json'))))
    write(root / 'context.json', dict(own_context='C100 actual context', lessons=['old retained lesson']))
    write(root / 'oldplan.json', dict(root=str(old_root)))
    plan = dict(root=str(root),gpu_uuid='GPU-test',arm='node3_episode',train_end_unix=9999999999,hard_end_unix=10000000119,
        parent_ttl_seconds=600,parent_wait_seconds=0,life_id='test',allowed_parent_models=['test'],
        train_tasks={row['task_id']:row['content_sha256'] for row in rows if row['split']=='TRAIN'},
        cohort_sha256='a'*64,cohorts=ref(root / 'cohorts.json'),release=ref(root / 'release.json'),
        predecessor=ref(root / 'oldplan.json'),inputs=dict(context=ref(root / 'context.json')),
        ancestry=dict(native_used=1493,parent_used=276,native_cap=62933,parent_cap=8468))
    write(root / 'PLAN.json', plan)
    monkeypatch.setattr(successor, 'plan_for', lambda path: plan)
    for name in ('begin', 'generate', 'save_triple', 'policy', 'validate', 'ROOT'):
        monkeypatch.setattr(runtime, name, getattr(runtime, name))
    for name in ('plan_for', 'poll_parents', 'PENDING'):
        monkeypatch.setattr(successor.fork, name, deepcopy(getattr(successor.fork, name)) if name == 'PENDING' else getattr(successor.fork, name))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-test')
    captures = []
    class Engine:
        tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs:[1, 2, 3])
        def generate(self, messages, **kwargs):
            captures.append(deepcopy(messages))
            return dict(raw='{"expression":"0"}',token_ids=[1],terminal=True,truncated=False)
        def identity(self):
            return dict(frozen=True)
        def verify_base(self):
            pass
    monkeypatch.setattr(successor.fork, 'load_engine', lambda *args:Engine())
    successor.native(root)
    assert len(captures) == 15
    assert 'C100 actual context' in captures[0][0]['content']
    terminal = successor.io.read(root / 'TERMINAL.json')
    assert terminal['status'] == 'COMPLETE' and terminal['optimizer_updates'] == 0
    assert terminal['cumulative_counts'] == dict(NATIVE=1508,PARENT=278)
    requests = list((root / 'parent_queue').glob('*.request.json'))
    assert len(requests) == 2
    for path in requests:
        payload = successor.io.read(path)['payload']
        assert payload['task_provenance']['split'] == 'TRAIN'
        assert 'tests' not in payload and 'reference_expression' not in payload
    assert not list(old_root.iterdir())
