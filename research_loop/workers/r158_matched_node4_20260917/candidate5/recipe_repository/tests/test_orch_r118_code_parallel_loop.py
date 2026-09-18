from copy import deepcopy
import inspect
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gpu import orch_r118_code_parallel_loop as loop


def write(path, value):
    loop.io.write(path, value, replace=path.exists())


@pytest.fixture
def session(tmp_path, monkeypatch):
    value = object.__new__(loop.Session)
    value.root = tmp_path / 'F3'
    value.shared_root = tmp_path / 'common'
    value.service = tmp_path / 'service'
    value.branch, value.owner = 'F3', False
    write(value.service / 'SUPERVISION.json', dict(synthetic=True))
    monkeypatch.setattr(loop.consolidation, 'validate_launch_participant', lambda *args: None)
    value.state = dict(generation=1, checkpoint=dict(path_sha256='a' * 64))
    value.loaded_reference = deepcopy(value.state['checkpoint'])
    value.plan = dict(native_cap=100, parent_cap=50)
    value.driver = SimpleNamespace(settings=dict(effective_max_new_tokens=3072))
    value.cursor_reference = dict(path='SYNTHETIC_SETTLED_CURSOR', sha256='c' * 64)
    value.group, value.anchors = object(), ['SYNTHETIC_ANCHOR']
    handoff_path = tmp_path / 'handoff.json'
    write(handoff_path, dict(native=dict(boundary=dict(carry=dict(reflection_settings=value.driver.settings)))))
    value.runtime = dict(train_end_unix=1000, hard_end_unix=1100, handoff=loop.handoff.ref(handoff_path),
        activation_directory=str(tmp_path / 'activations'), anchor_root=str(tmp_path / 'anchors'),
        campaign=dict(path=str(tmp_path / 'Main_CAMPAIGN.json'), sha256='e' * 64))
    write(value.root / 'PLAN.json', value.plan)
    source = value.root / 'reservations/C002_E0_ORIGINAL.json'
    write(source, dict(kind='NATIVE', split='TRAIN', status='COMPLETE', cycle=2,
        shared_learner=value.capture_binding(), shared_generation=1, shared_checkpoint_sha256='a' * 64))
    value.rows = [dict(source_call_path=str(source), source_call_sha256=loop.io.sha(source))]
    value.output = value.root / 'shared_cycles/C002'
    value.events = []
    def submit(root, branch, generation, checkpoint, episodes, rows):
        value.events.append('submit')
        path = root / f'generation_{generation:06d}' / (branch + '.json')
        write(path, dict(branch=branch, generation=generation, checkpoint_sha256=checkpoint,
            episode_ids=episodes, rows=rows))
        return dict(path=str(path), sha256=loop.io.sha(path), generation=generation)
    monkeypatch.setattr(loop.io, 'submit', submit)
    value.publish_calls = []
    def publish_activation(unused):
        path = value.output / 'SAFE_FOR_PARALLEL.json'
        if path.exists():
            activated = Path(value.runtime['activation_directory']) / 'native/ACTIVATION.json'
            write(activated, dict(root=str(value.shared_root), generation=1, participants={'F3': loop.handoff.ref(path)}))
            write(Path(value.runtime['activation_directory']) / 'generation_000001.ref.json',
                loop.handoff.ref(activated))
            value.publish_calls.append(path)
    value.pause = publish_activation
    value.campaign_calls = []
    def await_activation(path, digest, branch, certificate, check=None):
        value.campaign_calls.append(dict(path=path, sha256=digest, branch=branch, certificate=certificate))
        publish_activation(None)
        return loop.io.read(Path(value.runtime['activation_directory']) / 'generation_000001.ref.json')
    value.await_activation = await_activation
    value.plan.update(physical=2, gpu_uuid='GPU-synthetic')
    return value


def test_exact_Herschel_keyword_signature():
    names = set(inspect.signature(loop.consolidation.consolidate).parameters)
    assert names == {'root', 'activation_path', 'activation_sha256', 'branch', 'engine',
        'optimizer', 'group', 'anchor_module', 'anchors', 'anchor_root', 'save_checkpoint', 'check', 'clock'}


def invoke(session, hook):
    return session.sleep(SimpleNamespace(underlying='SAME_RAW_ENGINE'), None, (), session.rows,
        ['TRAIN_ONE', 'TRAIN_TWO'], session.output, None, lambda phase: None,
        consolidate_call=hook, await_activation=session.await_activation, pause=session.pause, clock=lambda: 100)


def test_actual_hook_uses_raw_engine_None_optimizer_no_serial_fallback(session):
    observed = []
    def hook(**kwargs):
        observed.append(kwargs)
        session.events.append('parallel')
        return dict(status='COMPLETE_ALL8_INPLACE', state=dict(generation=2, checkpoint=dict(path_sha256='b' * 64)),
            metrics=dict(optimizer_steps=3))
    result = invoke(session, hook)
    assert session.events == ['submit', 'parallel']
    assert observed[0]['engine'] == 'SAME_RAW_ENGINE'
    assert observed[0]['optimizer'] is None and observed[0]['save_checkpoint'] is None
    assert observed[0]['branch'] == 'F3' and 'group' not in observed[0]
    assert result['local_optimizer_steps'] == 0 and session.state['generation'] == 2
    certificate = loop.io.read(session.output / 'SAFE_FOR_PARALLEL.json')
    assert certificate['preceding_cursor_settled'] == session.cursor_reference
    assert certificate['bounds']['native_used'] == 1


def test_failed_hook_preserves_submission_and_forbids_second_call(session):
    calls = []
    def hook(**kwargs):
        calls.append(kwargs)
        raise RuntimeError('synthetic collective failure')
    with pytest.raises(RuntimeError):
        invoke(session, hook)
    assert (session.output / 'SHARED_SUBMISSION.json').exists()
    assert (session.output / 'PARALLEL_CALL_ONCE').exists()
    with pytest.raises(ValueError, match='resubmission'):
        invoke(session, hook)
    assert len(calls) == 1 and session.state['generation'] == 1


def test_worker_optimizer_rejected_before_any_submission(session):
    with pytest.raises(ValueError, match='no_CODE_optimizer'):
        session.sleep(SimpleNamespace(), object(), (), session.rows, ['ONE', 'TWO'], session.output,
            None, lambda phase: None)
    assert session.events == []


def test_native_generation_before_dispatch_binding_checked(session):
    path = Path(session.rows[0]['source_call_path'])
    write(path, dict(loop.io.read(path), shared_generation=0))
    with pytest.raises(ValueError, match='before_dispatch'):
        invoke(session, lambda **kwargs: pytest.fail('no_hook'))


def test_cycle_cursor_written_only_after_DEV_settlement(tmp_path):
    root, service = tmp_path / 'root', tmp_path / 'service'
    events = []
    session = SimpleNamespace(runtime=dict(train_end_unix=1000, hard_end_unix=1100),
        state=dict(generation=2), service=service, cursor_reference=dict(previous=True))
    driver = SimpleNamespace(root=root, session=session, settings=dict(effective_max_new_tokens=3072), cycle_sources={})
    def cycle(driver, tasks, ordinal):
        events.append(('cycle', ordinal))
        return dict(status='COMPLETE_ALL8_INPLACE')
    def settle(root, session, ordinal, check):
        assert (root / 'cycles' / f'C{ordinal:03d}_COMPLETE.json').exists()
        assert not (service / 'cursors' / f'C{ordinal:03d}.json').exists()
        events.append(('DEV_SETTLED', ordinal))
        return dict(actual=True)
    loop.run_cycles(driver, [dict(task_id=str(index)) for index in range(4)], 1, 2,
        lambda phase: None, run_cycle=cycle, settle=settle, clock=lambda: 100)
    assert events == [('cycle', 1), ('DEV_SETTLED', 1), ('cycle', 2), ('DEV_SETTLED', 2)]
    assert loop.io.read(service / 'cursors/C002.json')['next_cycle'] == 3


def test_failed_DEV_does_not_advance_cursor_or_start_next_charged_cycle(tmp_path):
    session = SimpleNamespace(runtime=dict(train_end_unix=1000, hard_end_unix=1100),
        state=dict(generation=2), service=tmp_path / 'service', cursor_reference=dict(old=True))
    driver = SimpleNamespace(root=tmp_path / 'root', session=session, settings={}, cycle_sources={})
    events = []
    def failed(*args):
        raise ValueError('partial_DEV_preserved')
    with pytest.raises(ValueError, match='partial_DEV'):
        loop.run_cycles(driver, [dict(task_id=str(index)) for index in range(4)], 1, 2,
            lambda phase: None, run_cycle=lambda *args: events.append('cycle') or {},
            settle=failed, clock=lambda: 100)
    assert events == ['cycle'] and session.cursor_reference == dict(old=True)


def test_async_readout_waits_real_process_completion_then_checks_all_cells(monkeypatch, tmp_path):
    events = []
    class Child:
        returncode = 0
        def poll(self):
            events.append('poll')
            return None if len(events) == 1 else 0
    monkeypatch.setattr(loop.handoff, 'readout_settled', lambda root, ordinal: events.append('all_cells') or dict(done=True))
    result = loop.settle_readout(tmp_path, object(), 2, lambda phase: events.append('check'),
        launch=lambda *args: Child(), pause=lambda duration: None)
    assert result == dict(done=True, observed_process_returncode=0) and events[-1] == 'all_cells'


def test_no_next_cycle_started_after_drain_threshold(tmp_path):
    session = SimpleNamespace(runtime=dict(train_end_unix=1000, hard_end_unix=1100), cursor_reference=dict(old=True))
    driver = SimpleNamespace(session=session)
    assert loop.run_cycles(driver, [], 1, 3, lambda phase: None,
        run_cycle=lambda *args: pytest.fail('late_cycle'), clock=lambda: 700) == dict(old=True)


def test_nonzero_DEV_exit_never_marks_settled(monkeypatch, tmp_path):
    child = SimpleNamespace(poll=lambda: 1, returncode=1)
    monkeypatch.setattr(loop.handoff, 'readout_settled', lambda *args: pytest.fail('no_cursor'))
    with pytest.raises(ValueError, match='readout_process_failed'):
        loop.settle_readout(tmp_path, object(), 1, lambda phase: None, launch=lambda *args: child)


def test_cleanup_only_exact_owned_cpu_actor(tmp_path):
    actor = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    foreign = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    try:
        identity = loop.handoff.identities.identity(actor.pid)
        result = loop.cleanup_native(identity, tmp_path)
        actor.wait(timeout=3)
        assert result['native'] == identity and result['readouts'] == []
        assert foreign.poll() is None
    finally:
        for child in (actor, foreign):
            if child.poll() is None:
                child.kill()
            child.wait(timeout=3)


def test_wrong_identity_never_stops_actor():
    actor = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        wrong = dict(loop.handoff.identities.identity(actor.pid), uid=-1)
        loop.stop_identity(wrong)
        assert actor.poll() is None
    finally:
        actor.kill()
        actor.wait(timeout=3)


def test_TERM_ignoring_cpu_actor_gets_exact_pidfd_fallback():
    actor = subprocess.Popen([sys.executable, '-u', '-c',
        'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); print("READY",flush=True); time.sleep(60)'],
        stdout=subprocess.PIPE)
    try:
        assert actor.stdout.readline().strip() == b'READY'
        loop.stop_identity(loop.handoff.identities.identity(actor.pid), grace=.05)
        actor.wait(timeout=3)
        assert actor.returncode == -9
    finally:
        if actor.poll() is None:
            actor.kill()
        actor.wait(timeout=3)
        actor.stdout.close()


def test_exact_per_sleep_launcher_signature():
    assert set(inspect.signature(loop.consolidation.launch_at_boundary).parameters) == {
        'activation_path', 'activation_sha256', 'branch', 'engine', 'optimizer', 'anchor_module',
        'anchor_root', 'save_checkpoint', 'check', 'anchors', 'clock', 'sleeper'}


def test_exact_present_Herschel_fresh_session_signature():
    assert set(inspect.signature(loop.consolidation.bootstrap_fresh_actor).parameters) == {
        'root', 'branch', 'engine', 'optimizer', 'session_path', 'session_sha256'}
    assert set(inspect.signature(loop.consolidation.wait_fresh_collection_go).parameters) == {
        'session_path', 'session_sha256', 'branch', 'check'}


def test_startup_bootstrap_before_collection_and_no_local_optimizer(session, monkeypatch):
    path = session.service / 'FRESH_SESSION.json'
    write(path, dict(owners={'F3': dict(bootstrap_path=str(session.service / 'FRESH_BOOTSTRAP.json'))}))
    monkeypatch.setenv('R118_PARALLEL_SESSION', str(path))
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', loop.io.sha(path))
    monkeypatch.setenv('R118_PARALLEL_BRANCH', 'F3')
    observed = []
    def setup(**kwargs):
        observed.append(('bootstrap', kwargs))
        return dict(seed_mode='DETERMINISTIC_NEW_PEER')
    def wait(*args, **kwargs):
        observed.append(('GO', args))
        assert (session.service / 'BOOTSTRAP.json').exists()
    monkeypatch.setattr(loop.consolidation, 'bootstrap_fresh_actor', setup, raising=False)
    monkeypatch.setattr(loop.consolidation, 'wait_fresh_collection_go', wait, raising=False)
    loop.bootstrap(session, SimpleNamespace(underlying='SAME_RAW'), lambda phase: None)
    assert [row[0] for row in observed] == ['bootstrap', 'GO']
    assert observed[0][1]['optimizer'] is None and observed[0][1]['engine'] == 'SAME_RAW'


def test_missing_bootstrap_API_fails_closed_before_new_calls(session, monkeypatch):
    path = session.service / 'FRESH_SESSION.json'
    write(path, dict(owners={'F3': dict(bootstrap_path=str(session.service / 'FRESH_BOOTSTRAP.json'))}))
    monkeypatch.setenv('R118_PARALLEL_SESSION', str(path))
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', loop.io.sha(path))
    monkeypatch.setenv('R118_PARALLEL_BRANCH', 'F3')
    monkeypatch.setattr(loop.consolidation, 'bootstrap_fresh_actor', None, raising=False)
    with pytest.raises(ValueError, match='API_required_no_fallback'):
        loop.bootstrap(session, SimpleNamespace(underlying='SAME_RAW'), lambda phase: None)
    assert session.events == []


def test_deadline_cleanup_includes_owned_async_readout(tmp_path):
    script = ('import subprocess,sys,time; child=subprocess.Popen([sys.executable,"-c",'
        '"import time; time.sleep(60)","gpu.orch_r108_code_parent_r116_shared_run",'
        '"readout",sys.argv[1]]); print(child.pid,flush=True); time.sleep(60)')
    actor = subprocess.Popen([sys.executable, '-u', '-c', script, str(tmp_path)],
        start_new_session=True, stdout=subprocess.PIPE)
    try:
        child_pid = int(actor.stdout.readline())
        identity = loop.handoff.identities.identity(actor.pid)
        child_identity = loop.handoff.identities.identity(child_pid)
        result = loop.cleanup_native(identity, tmp_path)
        actor.wait(timeout=3)
        assert result['readouts'] == [child_identity]
        assert not loop.handoff.alive(child_identity)
    finally:
        if actor.poll() is None:
            actor.kill()
        actor.wait(timeout=3)
        actor.stdout.close()
