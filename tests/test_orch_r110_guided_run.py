from gpu import orch_r110_guided_run as run


def test_new_life_has_explicit_budget_and_old_seed():
    assert run.ROOT.name == 'orch_r110_guided_20260915_attempt1'
    assert run.NATIVE_CAP == 5120 and run.PARENT_CAP == 192
    assert run.policy.CYCLES == 64 and run.policy.EPISODES == 2
    assert run.seed.CHECKPOINT.name == '000008932'


def test_initial_and_next_sleep_lineage_no_reset(monkeypatch):
    captured = []
    monkeypatch.setattr(run, 'read', lambda path: captured.append(path) or dict(generation=0))
    monkeypatch.setattr(run.seed, 'validate', lambda document: document)
    assert run.input_seed(run.ROOT, 1, 'collection')['generation'] == 0
    assert run.input_seed(run.ROOT, 1, 'sleep')['generation'] == 0
    assert all(path == run.ROOT / 'INITIAL.json' for path in captured)


def test_completion_retains_phase_and_training_clocks():
    metrics = dict(started_unix=20, finished_unix=30, optimizer_updates=113)
    result = run.completion_record(1, 'sleep', ['boot', 1, 2], 10, 40, {}, metrics)
    assert result['started_unix'] == 10 and result['finished_unix'] == 40
    assert result['training_started_unix'] == 20 and result['training_finished_unix'] == 30
    assert result['optimizer_updates'] == 113 and result['status'] == 'COMPLETE'
    assert metrics == dict(started_unix=20, finished_unix=30, optimizer_updates=113)


def test_completion_rejects_protected_field_collision():
    import pytest
    with pytest.raises(ValueError, match='completion_metadata_collision'):
        run.completion_record(1, 'sleep', [], 10, 40, {}, dict(status='FAILED'))
