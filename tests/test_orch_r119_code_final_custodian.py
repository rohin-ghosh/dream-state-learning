import inspect

import pytest

from gpu import orch_r119_code_continuation as custody
from gpu import orch_r119_code_final_custodian as custodian
from gpu import orch_r119_code_runtime as runtime


@pytest.fixture
def pointers(tmp_path):
    custody.write(tmp_path / 'COMPLETE.json', dict(native_calls=8, completed_calls=8))
    custody.write(tmp_path / 'TERMINAL.json', dict(returncode=0))
    return dict(branch='F3', root=str(tmp_path), final_completed=custody.ref(tmp_path / 'COMPLETE.json'),
        final_terminal=custody.ref(tmp_path / 'TERMINAL.json'), final_identity=dict(pid=111),
        final_repeat_allowed=False)


def test_truthful_live_custody_does_not_claim_evaluator(pointers, tmp_path):
    actor, holder = dict(pid=222), dict(pid=333)
    document = custodian.evidence(pointers, actor, holder, dict(path='runtime', sha256='pin'))
    custody.write(tmp_path / 'CUSTODY.json', document)
    observed = []
    actual = custodian.binding(custody.ref(tmp_path / 'CUSTODY.json'), actor, observed.append)
    assert actual['identity'] == holder and observed == [holder]
    assert document['completed_final']['evaluator_identity'] != holder
    assert document['role'] == custodian.ROLE
    assert document['may_dispatch'] is False and document['is_timer'] is False


def test_dead_custodian_is_not_accepted(pointers, tmp_path):
    custody.write(tmp_path / 'CUSTODY.json', custodian.evidence(pointers, {}, {}, {}))
    def dead(identity):
        raise ValueError('not_alive')
    with pytest.raises(ValueError, match='not_alive'):
        custodian.binding(custody.ref(tmp_path / 'CUSTODY.json'), {}, dead)


@pytest.mark.parametrize('field,value', [('may_dispatch', True), ('quota_delta', 8),
    ('is_timer', True), ('model_calls', 1), ('provider_calls', 1)])
def test_cannot_disguise_new_evaluation(pointers, tmp_path, field, value):
    document = custodian.evidence(pointers, {}, {}, {})
    document[field] = value
    custody.write(tmp_path / 'CUSTODY.json', document)
    with pytest.raises(ValueError, match='no_evaluation_or_quota_extension'):
        custodian.binding(custody.ref(tmp_path / 'CUSTODY.json'), {}, lambda identity: None)


def test_changed_original_receipt_rejected(pointers):
    from pathlib import Path
    Path(pointers['final_completed']['path']).write_text('{}')
    with pytest.raises(ValueError, match='exact_immutable_reference'):
        custodian.evidence(pointers, {}, {}, {})


def test_native_custodian_has_no_dispatch_or_generation():
    source = inspect.getsource(runtime.completed_final_custody)
    assert 'CPU_completed_FINAL_custodian' in source
    assert 'final_custodian.evidence' in source
    for forbidden in ('Popen(', 'schedule_dev(', 'load_engine(', 'generate(', 'readouts('):
        assert forbidden not in source
