from copy import deepcopy
import inspect
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r118_code_parallel_pending as pending
from gpu import orch_r118_code_parallel_loop as loop
from test_orch_r118_code_parallel_handoff import actor, ready, write
from test_orch_r118_code_parallel_loop import session


@pytest.fixture
def settled(ready):
    root, common = ready
    tasks = loop.client.run.policy.tasks('TRAIN')[2:4]
    config = dict(branches={'F3': dict(root=str(root), train_ids=[task['task_id'] for task in tasks])}, excluded_ids=[])
    write(common / 'CONFIG.json', config)
    state = dict(pending.io.read(common / 'STATE.json'), config_sha256=pending.io.sha(common / 'CONFIG.json'))
    write(common / 'STATE.json', state)
    write(root / 'shared_cycles/C001/SHARED_SLEEP.json', dict(state=state))
    write(common / 'generation_000000/sleep/COMPLETE.json', dict(state=state, same_optimizer=True))
    write(root / 'shared_readout_bindings/C001_DEV.json', dict(state=state, checkpoint=state['checkpoint']))
    old = common / 'generation_000000/F3.json'
    write(old, dict(pending.io.read(old), rows=[]))
    sources = []

    def native(identifier, task, phase, status='COMPLETE'):
        path = root / 'reservations' / (identifier + '.json')
        call = dict(id=identifier, cycle=2, task_id=task['task_id'], phase=phase, split='TRAIN', kind='NATIVE',
            status=status, shared_generation=1, shared_checkpoint_sha256='a' * 64,
            response=dict(messages=[dict(role='user', content='Synthetic CPU task')], raw='synthetic continuation',
                prompt_tokens=2, token_ids=[7, 9], terminal=True, truncated=False, input_truncated=False))
        write(path, call)
        if status == 'COMPLETE':
            sources.append(loop.client.causal.replay_row(call, path, pending.io.sha(path)))

    for index, task in enumerate(tasks):
        prefix = f'C002_E{index}'
        native(prefix + '_ORIGINAL', task, 'episode')
        write(root / 'reservations' / (prefix + '_PARENT.json'), dict(id=prefix + '_PARENT', cycle=2,
            kind='PARENT', split='TRAIN', status='MISSING', finished_unix=20,
            reflection_settings=dict(effective_max_new_tokens=3072)))
        native(prefix + '_REFLECTION', task, 'reflection')
        write(root / 'triples' / (prefix + '.json'), dict(task_id=task['task_id'], cycle=2))
        native(prefix + '_OPEN', task, 'open_turn', status='FAILED')
    native('C002_META', tasks[-1], 'presleep', status='FAILED')
    submitted_path = common / 'generation_000001/F3.json'
    write(submitted_path, dict(branch='F3', generation=1, checkpoint_sha256='a' * 64,
        episode_ids=[task['task_id'] for task in tasks], rows=sources))
    write(root / 'shared_cycles/C002/SHARED_SUBMISSION.json', pending.handoff.ref(submitted_path))
    return root, common


def test_actual_replay_validator_and_failed_tail_are_not_quality_gated(settled):
    result = pending.snapshot(*settled)
    assert result['kind'] == pending.MODE and result['cycle'] == 2 and result['next_cycle'] == 3
    assert result['carry']['reflection_settings']['effective_max_new_tokens'] == 3072
    assert len(result['pending']['terminal_calls']) == 9
    assert not (settled[0] / 'cycles/C002_COMPLETE.json').exists()


@pytest.mark.parametrize('missing', ['C002_E0_ORIGINAL', 'C002_E0_PARENT', 'C002_E0_REFLECTION',
    'C002_E0_OPEN', 'C002_E1_ORIGINAL', 'C002_META'])
def test_mid_episode_or_missing_tail_rejected(settled, missing):
    (settled[0] / 'reservations' / (missing + '.json')).unlink()
    with pytest.raises(ValueError, match='missing_scheduled_slot'):
        pending.snapshot(*settled)


def test_started_call_and_unpublished_parent_rejected(settled):
    root, common = settled
    path = root / 'reservations/C002_META.json'
    before = pending.io.read(path)
    write(path, dict(before, status='STARTED'))
    with pytest.raises(ValueError, match='inflight'):
        pending.snapshot(root, common)
    write(path, before)
    write(root / 'parent_queue/C002_E0_PARENT.request.json', {})
    with pytest.raises(ValueError, match='unpublished'):
        pending.snapshot(root, common)


@pytest.mark.parametrize('change', ['reverse', 'drop', 'hash', 'generation', 'checkpoint', 'episodes'])
def test_changed_submission_rejected_even_when_reference_rebound(settled, change):
    root, common = settled
    path = common / 'generation_000001/F3.json'
    value = pending.io.read(path)
    if change == 'reverse':
        value['rows'].reverse()
    elif change == 'drop':
        value['rows'].pop()
    elif change == 'hash':
        value['rows'][0]['source_call_sha256'] = '0' * 64
    elif change == 'generation':
        value['generation'] = 0
    elif change == 'checkpoint':
        value['checkpoint_sha256'] = '0' * 64
    else:
        value['episode_ids'].reverse()
    write(path, value)
    write(root / 'shared_cycles/C002/SHARED_SUBMISSION.json', pending.handoff.ref(path))
    with pytest.raises(ValueError):
        pending.snapshot(root, common)


@pytest.mark.parametrize('change', ['unexpected', 'next_cycle', 'sleep', 'previous_DEV', 'trained'])
def test_unsettled_or_already_trained_boundary_rejected(settled, change):
    root, common = settled
    if change in ('unexpected', 'next_cycle'):
        identifier = 'C002_EXTRA' if change == 'unexpected' else 'C003_E0_ORIGINAL'
        write(root / 'reservations' / (identifier + '.json'), dict(id=identifier, kind='NATIVE', split='TRAIN',
            cycle=2 if change == 'unexpected' else 3, status='COMPLETE'))
    elif change == 'sleep':
        write(common / 'generation_000001/sleep/START.json', {})
    elif change == 'previous_DEV':
        (root / 'readouts/C001_DEV/COMPLETE.json').unlink()
    else:
        row = pending.io.read(common / 'generation_000001/F3.json')['rows'][0]
        path = common / 'generation_000000/F3.json'
        write(path, dict(pending.io.read(path), rows=[row]))
    with pytest.raises((ValueError, FileNotFoundError)):
        pending.snapshot(root, common)


def test_conditional_environment_and_parent_reflection_tails_required(settled):
    root, common = settled
    path = root / 'reservations/C002_E0_OPEN.json'
    write(path, dict(pending.io.read(path), status='COMPLETE'))
    with pytest.raises(ValueError, match='environment_missing'):
        pending.snapshot(root, common)
    write(root / 'environment/C002_E0_OPEN.json', dict(source_call_sha256=pending.io.sha(path),
        split='TRAIN', attached_evaluation=False, observation=dict(status='OBSERVED')))
    with pytest.raises(ValueError, match='missing_scheduled_slot'):
        pending.snapshot(root, common)
    write(root / 'reservations/C002_E0_OPEN_OBSERVE.json', dict(id='C002_E0_OPEN_OBSERVE', cycle=2,
        kind='NATIVE', split='TRAIN', status='FAILED'))
    write(root / 'reservations/C002_E0_OPEN_PARENT.json', dict(id='C002_E0_OPEN_PARENT', cycle=2,
        kind='PARENT', split='TRAIN', status='COMPLETE', guidance='synthetic nonempty guidance'))
    with pytest.raises(ValueError, match='missing_scheduled_slot'):
        pending.snapshot(root, common)


def test_herschel_third_mode_accepts_exact_published_custody(settled):
    root, common = settled
    boundary = pending.snapshot(root, common)
    before = pending.handoff.ledger(root)[0]
    pending.publish(root, root / 'prospective', boundary)
    owner = dict(boundary=dict(settled_pending_consolidation=boundary['pending_reference'],
        settled_cursor=boundary['pending_cursor'], canonical_reload_required=True, mounted_checkpoint_sha256=None))
    envelope = dict(root=str(root), preserved_files=boundary['preserved_files'],
        next_cycle=3, bounds=boundary['charges'])
    result = loop.consolidation.pending_consolidation_boundary(common, 'F3', owner, envelope,
        pending.io.read(common / 'CONFIG.json'), pending.io.read(common / 'STATE.json'))
    assert result['cycle'] == 2 and result['next_cycle'] == 3
    assert result['submission'] == boundary['pending']['submission']
    assert pending.handoff.ledger(root)[0] == before


def test_pending_init_skips_only_exact_authorized_unfinished_cycle(settled, monkeypatch):
    root, common = settled
    boundary = pending.snapshot(root, common)
    observed = []
    def original(self, root, plan, *, readout=False):
        self.root = Path(root)
        observed.append(readout)
    monkeypatch.setattr(loop.client.Session, '__init__', original)
    loop.Session(root, dict(shared_learner=dict(root=str(common))), pending_boundary=boundary)
    assert observed == [True]
    write(root / 'shared_cycles/C099/SHARED_SUBMISSION.json', {})
    with pytest.raises(ValueError, match='only_one_unfinished'):
        loop.Session(root, dict(shared_learner=dict(root=str(common))), pending_boundary=boundary)


def test_existing_submission_enters_parallel_without_submit_or_model_call(session, monkeypatch):
    submitted = loop.io.submit(session.shared_root, session.branch, 1, 'a' * 64, ['ONE', 'TWO'], session.rows)
    write(session.output / 'SHARED_SUBMISSION.json', submitted)
    original_sha = loop.io.sha(session.output / 'SHARED_SUBMISSION.json')
    monkeypatch.setattr(loop.io, 'submit', lambda *args, **kwargs: pytest.fail('duplicate_submit'))
    seen = []
    def hook(**kwargs):
        seen.append(kwargs)
        return dict(status='COMPLETE_ALL8_INPLACE', state=dict(generation=2, checkpoint=dict(path_sha256='b' * 64)), metrics={})
    session.consolidate_existing(SimpleNamespace(underlying='READ_ONLY_ENGINE'), session.output, submitted,
        lambda phase: None, consolidate_call=hook, await_activation=session.await_activation, clock=lambda: 100)
    assert len(seen) == 1 and session.events == ['submit']
    assert loop.io.sha(session.output / 'SHARED_SUBMISSION.json') == original_sha


def test_resume_catchup_then_DEV_without_collecting_or_submitting(settled, monkeypatch):
    root, common = settled
    boundary = pending.snapshot(root, common)
    monkeypatch.setenv('R118_PARALLEL_SESSION', '/synthetic/Main_session.json')
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'f' * 64)
    monkeypatch.setattr(loop.io, 'submit', lambda *args, **kwargs: pytest.fail('duplicate_submit'))
    events = []
    session = SimpleNamespace(state=deepcopy(boundary['state']), shared_root=common, branch='F3')
    driver = SimpleNamespace(session=session, root=root, engine=object(), cycle_sources={})
    def resume(**kwargs):
        events.append('resume_existing')
        return dict(status='PENDING_CONSOLIDATION_READY_NO_NEW_CALLS', existing_submission_reused=True,
            new_native_calls=0, optimizer_updates=0, cycle=2, next_cycle=3, generation=1,
            episode_ids=boundary['pending']['episode_ids'], submission=boundary['pending']['submission'],
            rows=pending.handoff.checked(boundary['pending']['submission'])['rows'])
    def consolidate(*args):
        events.append('parallel_commit')
        session.state = dict(session.state, generation=2)
        return dict(committed=True)
    def finish(*args):
        events.append('new_DEV_then_cursor')
        return dict(next_cycle=3)
    session.consolidate_existing = consolidate
    assert loop.resume_pending(driver, boundary, lambda phase: None, resume=resume, finish=finish) == dict(next_cycle=3)
    assert events == ['resume_existing', 'parallel_commit', 'new_DEV_then_cursor']
    assert len(driver.cycle_sources[2]) == 4


def test_native_catchup_is_before_next_collection_and_no_pending_readout_engine():
    source = inspect.getsource(loop.native)
    assert source.index('resume_pending(driver') < source.index('cursor = run_cycles(')
    assert 'session.load_engine(plan, check)' in source
    assert 'Main_bootstrap_pending_action_binding' in source


def test_pending_inspection_rejection_resumes_exact_CPU_actor(settled, actor, monkeypatch):
    handoff = pending.handoff
    monkeypatch.setattr(handoff, 'authorize', lambda *args: ({}, dict(boundary_mode=pending.MODE), {}))
    monkeypatch.setattr(handoff, 'checked', lambda value: dict(expires_unix=time.time() + 30))
    monkeypatch.setattr(handoff, 'live_children', lambda identity: [])
    monkeypatch.setattr(pending, 'snapshot', lambda *args, **kwargs: handoff.require(False, 'partial_not_allowed'))
    with pytest.raises(ValueError, match='partial_not_allowed'):
        handoff.hold_release(handoff.identities.identity(actor.pid), *settled, authorization={})
    assert actor.poll() is None
    assert Path(f'/proc/{actor.pid}/stat').read_text().rsplit(') ', 1)[1].split()[0] not in ('T', 't')


def test_failed_pending_collective_cannot_be_invoked_twice(session, monkeypatch):
    submitted = loop.io.submit(session.shared_root, session.branch, 1, 'a' * 64, ['ONE', 'TWO'], session.rows)
    write(session.output / 'SHARED_SUBMISSION.json', submitted)
    monkeypatch.setattr(loop.io, 'submit', lambda *args, **kwargs: pytest.fail('duplicate_submit'))
    calls = []
    def fail(**kwargs):
        calls.append(kwargs)
        raise RuntimeError('preserved_collective_failure')
    def invoke():
        return session.consolidate_existing(SimpleNamespace(underlying=object()), session.output, submitted,
            lambda phase: None, consolidate_call=fail, await_activation=session.await_activation, clock=lambda: 100)
    with pytest.raises(RuntimeError):
        invoke()
    with pytest.raises((ValueError, FileExistsError)):
        invoke()
    assert len(calls) == 1 and (session.output / 'PARALLEL_CALL_ONCE').exists()
    assert session.state['generation'] == 1
