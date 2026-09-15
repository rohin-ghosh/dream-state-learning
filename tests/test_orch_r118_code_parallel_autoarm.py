import inspect
from pathlib import Path

import pytest

from gpu import orch_r118_code_parallel_loop as loop
from test_orch_r118_code_parallel_handoff import ready
from test_orch_r118_code_parallel_loop import session, invoke, write
from test_orch_r118_code_parallel_runtime import runtime


def test_exact_present_campaign_API():
    assert set(inspect.signature(loop.consolidation.await_campaign_activation).parameters) == {
        'campaign_path', 'campaign_sha256', 'branch', 'certificate', 'check'}


def test_CODE_publishes_own_safe_reference_through_Main_campaign(session):
    invoke(session, lambda **kwargs: dict(status='COMPLETE_ALL8_INPLACE',
        state=dict(generation=2, checkpoint=dict(path_sha256='b' * 64))))
    assert len(session.campaign_calls) == 1
    called = session.campaign_calls[0]
    assert called['branch'] == 'F3' and called['path'] == session.runtime['campaign']['path']
    assert called['sha256'] == session.runtime['campaign']['sha256']
    assert called['certificate'] == loop.handoff.ref(session.output / 'SAFE_FOR_PARALLEL.json')
    assert (session.output / 'SHARED_SLEEP.json').exists()


def test_failed_campaign_preserves_submission_without_manual_fallback_or_retry(session):
    def failed(*args, **kwargs):
        raise ValueError('campaign_failed_no_retry')
    session.await_activation = failed
    with pytest.raises(ValueError, match='campaign_failed'):
        invoke(session, lambda **kwargs: pytest.fail('no_collective_after_failed_campaign'))
    assert (session.output / 'SHARED_SUBMISSION.json').exists()
    assert (session.output / 'SAFE_FOR_PARALLEL.json').exists()
    assert not (session.output / 'PARALLEL_CALL_ONCE').exists()
    with pytest.raises(ValueError, match='resubmission'):
        invoke(session, lambda **kwargs: pytest.fail('no_replay'))


def test_same_certificate_but_wrong_generation_cannot_run_collective(session):
    original = session.await_activation
    def wrong(*args, **kwargs):
        reference = original(*args, **kwargs)
        path = Path(reference['path'])
        value = loop.io.read(path)
        value['generation'] += 1
        write(path, value)
        return loop.handoff.ref(path)
    session.await_activation = wrong
    with pytest.raises(ValueError, match='Main_exact_live_certificate'):
        invoke(session, lambda **kwargs: pytest.fail('wrong_generation'))


def test_unbound_campaign_rejected_before_any_GPU_activity(runtime):
    service, root, common, source = runtime
    path = service / 'RUNTIME.json'
    value = loop.io.read(path)
    value['campaign']['sha256'] = '0' * 64
    write(path, value)
    with pytest.raises(ValueError, match='Main_bound_collective'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_real_campaign_safe_publication_and_ready_ref_without_dispatch(tmp_path, monkeypatch):
    helper = loop.consolidation
    root, control = tmp_path / 'common', tmp_path / 'control'
    campaign = tmp_path / 'campaign.json'
    path = tmp_path / 'CODE/SAFE.json'
    write(root / 'STATE.json', dict(generation=1, checkpoint=dict(path_sha256='a' * 64)))
    write(path, dict(branch='F3', generation=1, checkpoint_sha256='a' * 64,
        status='SAFE_FOR_PARALLEL', identity=helper.process_identity()))
    reference = loop.handoff.ref(path)
    document = dict(root=str(root), deadline_unix=helper.TRAIN_END, first_generation=1,
        safe_directory=str(tmp_path / 'safe'), activation_directory=str(tmp_path / 'activations'))
    monkeypatch.setattr(helper, 'campaign_document', lambda *args: (document, control))
    activated = tmp_path / 'armed/ACTIVATION.json'
    write(activated, dict(generation=1, participants={'F3': reference}))
    write(tmp_path / 'activations/generation_000001.ref.json', loop.handoff.ref(activated))
    result = helper.await_campaign_activation(campaign, 'b' * 64, 'F3', reference)
    assert result == loop.handoff.ref(activated)
    assert loop.io.read(tmp_path / 'safe/generation_000001/F3.ref.json') == reference
    assert not (control / 'START.json').exists()


def test_real_campaign_failure_does_not_publish_or_infer_all8_success(tmp_path, monkeypatch):
    helper = loop.consolidation
    control = tmp_path / 'control'
    write(control / 'FAILED.json', dict(reason='peer_crash_preserved'))
    monkeypatch.setattr(helper, 'campaign_document', lambda *args: (
        dict(deadline_unix=helper.TRAIN_END, safe_directory=str(tmp_path / 'safe')), control))
    with pytest.raises(ValueError, match='bounded_publication'):
        helper.await_campaign_activation(tmp_path / 'campaign.json', 'a' * 64, 'F3', {})
    assert not (tmp_path / 'safe').exists()
