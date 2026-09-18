"""Synthetic lifecycle checks; no real evaluation, model, or subprocess."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r150_readout_custody as custody
from test_orch_r150_matched_native import cohort_fixture, save_checkpoint


def fixture(tmp_path):
    plans, unused_cohort = cohort_fixture(tmp_path)
    plan = plans[0]
    checkpoint = save_checkpoint(Path(plan['root'])/'checkpoints/initial', plan)
    plan_path = tmp_path/'PLAN.json'
    custody.native.write_once(plan_path, plan)
    return plan_path, plan, checkpoint


@pytest.mark.parametrize('failed', [False, True])
def test_clean_return_not_score_determines_readout_disposition(tmp_path, monkeypatch, failed):
    plan_path, plan, checkpoint = fixture(tmp_path)
    locations = custody.paths(plan, 0)
    assert custody.disposition(plan_path, plan, checkpoint, 0) == 'NOT_STARTED'

    def dispatcher(child, actual_plan_path, actual_checkpoint, cycle):
        assert locations['opened'].exists() and not locations['closed'].exists()
        custody.native.write_once(locations['dispatch'], dict(cycle=cycle, parent_present=False,
            history_shared=False, checkpoint_sha256=custody.native.sha(Path(checkpoint['adapter_path']).parent/'COMMIT.json')))
        if failed:
            custody.native.write_once(locations['failure'], dict(error='synthetic readout failure'))
        else:
            locations['output'].mkdir()
            (locations['output']/'COMPLETE.json').write_text('DO_NOT_PARSE_EVALUATION_CONTENTS')

    monkeypatch.setattr(custody.native, 'fresh_readout', dispatcher)
    custody.fresh_readout(SimpleNamespace(plan=plan), plan_path, checkpoint, 0)
    assert custody.disposition(plan_path, plan, checkpoint, 0) == 'CLOSED'
    closed = custody.native.read(locations['closed'])
    assert closed['evaluation_failure_marker_present'] is failed
    assert closed['evaluation_completion_marker_present'] is not failed
    assert closed['evaluations_gate_continuation'] is False and closed['evaluation_contents_read'] is False
    before = locations['dispatch'].read_bytes()
    with pytest.raises(ValueError, match='readout_no_implicit_replay'):
        custody.fresh_readout(SimpleNamespace(plan=plan), plan_path, checkpoint, 0)
    assert locations['dispatch'].read_bytes() == before


@pytest.mark.parametrize('location', ['output', 'dispatch', 'failure', 'log', 'opened', 'closed'])
def test_any_unresolved_artifact_refuses_resume_and_is_preserved(tmp_path, location):
    plan_path, plan, checkpoint = fixture(tmp_path)
    path = custody.paths(plan, 0)[location]
    path.parent.mkdir()
    path.write_text('unresolved synthetic lifecycle artifact')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='readout_custody_unresolved_before_model_load'):
        custody.disposition(plan_path, plan, checkpoint, 0)
    assert path.read_bytes() == before


def test_interrupted_dispatch_remains_unresolved_without_killing_or_replaying(tmp_path, monkeypatch):
    plan_path, plan, checkpoint = fixture(tmp_path)
    locations = custody.paths(plan, 0)

    def interrupted(*args):
        locations['dispatch'].write_text('{"fixture": "owned subprocess not reconciled"}')
        raise KeyboardInterrupt('synthetic abrupt resident interruption')

    monkeypatch.setattr(custody.native, 'fresh_readout', interrupted)
    with pytest.raises(KeyboardInterrupt):
        custody.fresh_readout(SimpleNamespace(plan=plan), plan_path, checkpoint, 0)
    assert locations['opened'].is_file() and not locations['closed'].exists()
    with pytest.raises(ValueError, match='unresolved_before_model_load'):
        custody.disposition(plan_path, plan, checkpoint, 0)


@pytest.mark.parametrize('field', ['matched_arm', 'cohort_sha256', 'checkpoint_commit_sha256', 'plan_sha256'])
def test_altered_lifecycle_binding_refused(tmp_path, monkeypatch, field):
    plan_path, plan, checkpoint = fixture(tmp_path)
    locations = custody.paths(plan, 0)

    def dispatcher(*args):
        custody.native.write_once(locations['dispatch'], dict(cycle=0, parent_present=False, history_shared=False,
            checkpoint_sha256=custody.native.sha(Path(checkpoint['adapter_path']).parent/'COMMIT.json')))

    monkeypatch.setattr(custody.native, 'fresh_readout', dispatcher)
    custody.fresh_readout(SimpleNamespace(plan=plan), plan_path, checkpoint, 0)
    closed = custody.native.read(locations['closed'])
    closed['binding'][field] = 'altered'
    locations['closed'].write_text(json.dumps(closed))
    with pytest.raises(ValueError, match='exact_readout_custody_binding'):
        custody.disposition(plan_path, plan, checkpoint, 0)
