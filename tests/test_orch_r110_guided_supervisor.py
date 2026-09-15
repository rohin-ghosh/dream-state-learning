from pathlib import Path
from unittest.mock import Mock
import time

from gpu import orch_r110_guided_supervisor as supervisor


def test_cohort_excludes_every_prior_id_and_question():
    registry = dict(excluded_ids=['earlier_TRAIN_0'], excluded_question_sha256=['a' * 64])
    selected = supervisor.cohort(registry)
    tasks = [task for groups in selected.values() if isinstance(groups, list) for group in groups for task in group]
    assert len(tasks) == supervisor.run.policy.CYCLES * 10
    assert len({task['id'] for task in tasks}) == len(tasks)
    assert len({task['question_sha256'] for task in tasks}) == len(tasks)
    assert all(task['split'] == 'TRAIN' for group in selected['train'] for task in group)
    assert all(task['split'] == 'HELD' for group in selected['held'] for task in group)


def test_lifetime_has_one_admission_not_one_per_phase(tmp_path, monkeypatch):
    plan = dict(native_deadline_unix=time.time() + 10000, hard_deadline_unix=time.time() + 10100)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(supervisor.run, 'validate', lambda root: plan)
    monkeypatch.setattr(supervisor.run.policy, 'CYCLES', 2)
    monkeypatch.setattr(supervisor, 'sha', lambda path: 'a' * 64)
    admission = Mock(return_value=tmp_path / 'initial_admission.json')
    monkeypatch.setattr(supervisor, 'wait_clear', admission)
    monkeypatch.setattr(supervisor, 'read', lambda path: dict(status='COMPLETE'))
    monkeypatch.setattr(supervisor, 'write', lambda path, value: Path(path).write_text('{}'))
    child = Mock(pid=123)
    child.wait.return_value = 0
    launch = Mock(return_value=child)
    monkeypatch.setattr(supervisor.subprocess, 'Popen', launch)
    (tmp_path / 'ANCHORS.json').write_text('{}')
    supervisor.supervise(tmp_path)
    assert admission.call_count == 1
    assert launch.call_count == 6
    assert [call.args[0][-1] for call in launch.call_args_list] == ['collection', 'sleep', 'readout'] * 2


def test_lifetime_bounds_do_not_roll_forward():
    source = Path(supervisor.__file__).read_text()
    assert 'native_deadline_unix=1789491600' in source
    assert 'hard_deadline_unix=1789491720' in source
    assert 'max_parent_calls=run.PARENT_CAP' in source
