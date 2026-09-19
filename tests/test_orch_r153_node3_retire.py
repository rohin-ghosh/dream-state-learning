import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from gpu import orch_r153_node3_retire as retire


def plan(physical=5):
    target = retire.TARGETS[physical]
    return dict(physical=physical, gpu_uuid=target['uuid'],
                root=str(retire.BASE / f"orch_r133_node3_{target['name']}_20260916_attempt1/run1"),
                source_root=str(retire.SOURCE_BASE / f'physical{physical}/source'))


@pytest.mark.parametrize('physical', [5, 6])
def test_only_exact_owned_scope(physical):
    assert retire.scope(plan(physical)) == physical


@pytest.mark.parametrize('physical', [0, 1, 2, 3, 4, 7, True, 5.0, '5'])
def test_foreign_lane_or_coercion_rejected(physical):
    value = plan()
    value['physical'] = physical
    with pytest.raises(ValueError, match='only_named_node3'):
        retire.scope(value)


@pytest.mark.parametrize('key', ['root', 'source_root', 'gpu_uuid'])
def test_scope_binding_cannot_drift(key):
    value = plan()
    value[key] += '-different'
    with pytest.raises(ValueError, match='exact_named'):
        retire.scope(value)


def test_pinned_boundary_api_bytes(tmp_path):
    path = tmp_path / 'api.py'
    path.write_text('raise AssertionError("never execute unpinned source")')
    with pytest.raises(ValueError, match='pinned_proven_boundary_API'):
        retire.load_api(path)


def pair():
    return {'actor': {'pid': 101, 'ticks': 'one'}, 'timer': {'pid': 102, 'ticks': 'two'},
            'supervisor': {'pid': 103, 'ticks': 'three'}}


def helper_for(identities):
    return SimpleNamespace(process_record=lambda pid: next(value for value in identities.values() if value['pid'] == pid))


def test_only_native_signaled_parents_exit_naturally():
    identities = pair()
    with patch.object(retire.signal, 'pidfd_send_signal') as send, \
            patch.object(retire.select, 'select', side_effect=lambda reads, *rest: (reads, [], [])) as wait, \
            patch.object(retire.time, 'monotonic', return_value=100):
        retire.retire_actor(helper_for(identities), identities, dict(actor=11, timer=12, supervisor=13), 180)
    assert send.call_args_list == [((11, retire.signal.SIGTERM),), ((11, retire.signal.SIGCONT),)]
    assert [entry.args[0] for entry in wait.call_args_list] == [[11], [12], [13]]


def test_expired_pause_cannot_terminate():
    with patch.object(retire.signal, 'pidfd_send_signal') as send, \
            patch.object(retire.time, 'monotonic', return_value=160), \
            pytest.raises(ValueError, match='pause_budget'):
        retire.retire_actor(helper_for(pair()), pair(), {'actor': 11}, 180)
    send.assert_not_called()


def test_identity_drift_cannot_terminate():
    changed = deepcopy(pair())
    changed['actor']['ticks'] = 'reused'
    with patch.object(retire.signal, 'pidfd_send_signal') as send, \
            patch.object(retire.time, 'monotonic', return_value=100), \
            pytest.raises(ValueError, match='bound_process_identity_changed'):
        retire.retire_actor(helper_for(changed), pair(), {'actor': 11}, 180)
    send.assert_not_called()


def test_native_exit_timeout_never_escalates():
    with patch.object(retire.signal, 'pidfd_send_signal') as send, \
            patch.object(retire.select, 'select', return_value=([], [], [])), \
            patch.object(retire.time, 'monotonic', return_value=100), \
            pytest.raises(ValueError, match='native_exit_without_force_kill'):
        retire.retire_actor(helper_for(pair()), pair(), {'actor': 11}, 180)
    assert len(send.call_args_list) == 2
    assert all(entry.args[0] == 11 for entry in send.call_args_list)


@pytest.mark.parametrize('extra_pid,owner', [(999, 101), (999, 102), (999, 103)])
def test_foreign_children_block(extra_pid, owner):
    values = {101: {104}, 102: {101}, 103: {102}}
    values[owner].add(extra_pid)
    with patch.object(retire, 'children', side_effect=lambda pid: values[pid]), pytest.raises(ValueError):
        retire.validate_children(pair(), 104)


def test_only_readout_child_allowed():
    values = {101: {104}, 102: {101}, 103: {102}}
    with patch.object(retire, 'children', side_effect=lambda pid: values[pid]):
        retire.validate_children(pair(), 104)


@pytest.mark.parametrize('ready,message,signals', [(False, b'', 1), (True, b'', 1), (True, b'D', 0)])
def test_watchdog_only_restores_owned_pidfd(ready, message, signals):
    with patch.object(retire.select, 'select', return_value=([22] if ready else [], [], [])), \
            patch.object(retire.os, 'read', return_value=message), \
            patch.object(retire.signal, 'pidfd_send_signal') as send:
        retire.watchdog(11, 22, 180)
    assert send.call_count == signals
    if signals:
        send.assert_called_once_with(11, retire.signal.SIGCONT)


def test_resume_requires_new_ack_and_preserves_allocator(tmp_path):
    helper = SimpleNamespace(PYTHON='/original/venv/bin/python')
    command = retire.resume_command(helper, tmp_path, tmp_path / 'BOUNDARY_API.py')
    assert command[:3] == ['/original/venv/bin/python', '-B', '-c']
    assert 'RESUME_MAIN_ACK.json' in command[-1]
    assert 'RESUME_R153_SAME_LIFE' in command[-1]
    assert 'api.allocator_command(original(*args,**kwargs))' in command[-1]
    assert 'programmes.supervise' in command[-1]
    compile(command[-1], '<resume-command-not-executed>', 'exec')


def test_snapshot_work_precedes_lock_and_pause():
    text = Path(retire.__file__).read_text()
    function = text[text.index('def retire(helper,'):text.index('\ndef main():')]
    assert function.index('shutil.copytree') < function.index('fcntl.flock(lock, fcntl.LOCK_EX')
    assert function.index('copied_checkpoint_exact_bytes') < function.index('helper.pause_exact')
    assert function.index('finish_readout(') < function.index('retire_actor(')
    assert function.index('postexit_exact_saved_bundle') < function.index("'RELEASED.json'")


def test_retirement_never_launches_or_group_signals():
    tree = ast.parse(Path(retire.__file__).read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in
                 ('retire', 'retire_actor', 'prepare', 'watchdog')]
    for function in functions:
        for node in ast.walk(function):
            if isinstance(node, ast.Attribute):
                assert node.attr not in ('killpg', 'kill', 'SIGKILL', 'Popen')


def test_readout_wait_requires_complete_and_exit(tmp_path):
    (tmp_path / 'COMPLETE.json').write_text('{}')
    helper = SimpleNamespace(read=Mock(return_value={'status':'COMPLETE', 'pid':104,
        'checkpoint_commit_sha256':'checkpoint', 'finished_unix':123}), sha=lambda path:'complete')
    readout = dict(directory=tmp_path, descriptor=44, pid=104, request_sha256='request',
                   checkpoint_commit_sha256='checkpoint')
    with patch.object(retire.time, 'monotonic', return_value=100), \
            patch.object(retire.select, 'select', return_value=([44], [], [])):
        result = retire.finish_readout(helper, readout, 180)
    assert result == dict(pid=104, request_sha256='request', complete_sha256='complete', finished_unix=123)
    helper.read.return_value['checkpoint_commit_sha256'] = 'other'
    with patch.object(retire.time, 'monotonic', return_value=100), \
            patch.object(retire.select, 'select', return_value=([44], [], [])), \
            pytest.raises(ValueError, match='matching_readout'):
        retire.finish_readout(helper, readout, 180)


def test_inflight_readout_timeout_has_no_signal(tmp_path):
    with patch.object(retire.time, 'monotonic', return_value=151), \
            patch.object(retire.signal, 'pidfd_send_signal') as send, \
            pytest.raises(TimeoutError, match='restore_live_native'):
        retire.finish_readout(SimpleNamespace(), dict(directory=tmp_path), 180)
    send.assert_not_called()
