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
