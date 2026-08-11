"""Tests for the felt package (head, fastweight, baselines, harness)."""

from __future__ import annotations

import json
import shutil

import numpy as np

from game import generate_dataset, World
from felt import (FeltHead, train_head_on_dataset, eval_head, FastWeightMemory,
                  value_modulated_weights, Harness, RunConfig,
                  run_probe_condition, all_budgets_regret)


def _dataset(tmp="/tmp/felt_t.jsonl", n_worlds=2, eps=12, seed=5):
    r = generate_dataset(tmp, n_worlds=n_worlds, episodes_per_world=eps, seed=seed)
    return [json.loads(l) for l in open(r["path"])]


def test_head_learns_and_transfers():
    recs = _dataset(n_worlds=3, eps=15, seed=42)
    head = train_head_on_dataset(recs[:35], epochs=30, seed=0)
    trained = eval_head(head, recs[35:])
    untrained = eval_head(FeltHead(seed=99), recs[35:])
    assert trained["all_budgets_regret"] < untrained["all_budgets_regret"] * 0.7
    assert np.isfinite(head.q).all() and np.isfinite(head.Wk).all()


def test_all_budgets_regret_bounds():
    t = np.array([1.0, 0.5, 0.0, 0.0])
    assert all_budgets_regret(t.copy(), t) == 0.0            # perfect ranking
    assert all_budgets_regret(-t, t) > 0.3                   # inverted is bad


def test_fastweight_write_read_and_capacity():
    rng = np.random.default_rng(0)
    mem = FastWeightMemory(seed=0)
    K = rng.normal(0, 1, (30, 32)); K /= np.linalg.norm(K, axis=1, keepdims=True)
    V = rng.normal(0, 1, (30, 32))
    mem.write_batch(K, V, np.ones(30), steps=60)
    cos = mem.probe(K, V)
    assert cos.mean() > 0.5, cos.mean()                      # stores associations


def test_fastweight_weighted_writes_prioritize():
    rng = np.random.default_rng(1)
    mem = FastWeightMemory(hidden=24, seed=1)                # tight capacity
    K = rng.normal(0, 1, (120, 32)); K /= np.linalg.norm(K, axis=1, keepdims=True)
    V = rng.normal(0, 1, (120, 32))
    w = np.ones(120); w[:20] = 10.0                          # favored items
    mem.write_batch(K, V, w, steps=40)
    cos = mem.probe(K, V)
    assert cos[:20].mean() > cos[20:].mean() + 0.05          # allocation expressed


def test_value_modulated_beta_zero_is_surprise():
    s = np.array([1.0, 2.0]); a = np.array([0.9, 0.1])
    assert np.allclose(value_modulated_weights(s, a, 0.0), s)


def test_probe_condition_policies_run():
    recs = _dataset()
    head = train_head_on_dataset(recs, epochs=10, seed=0)
    w = World.generate("t", seed=77)
    for pol in ("uniform", "surprise_only", "dmem_style", "felt_b12",
                "no_memory", "context_fifo", "rag_unbounded"):
        m = run_probe_condition(w, head, pol, n_episodes=8, d_h=64, seed=0)
        assert "dissociation" in m and np.isfinite(m["dissociation"])


def test_harness_end_to_end_and_resume():
    shutil.rmtree("/tmp/felt_h", ignore_errors=True)
    cfg = RunConfig(workdir="/tmp/felt_h", train_worlds=2,
                    train_episodes_per_world=10, eval_worlds=2,
                    eval_episodes_per_world=10,
                    policies=("uniform", "felt_b12"))
    m1 = Harness(cfg).run()
    assert "probe_eval" in m1 and "felt_b12" in m1["probe_eval"]
    m2 = Harness(cfg).run()                                   # resume = no-op
    assert m2["probe_eval"]["felt_b12"] == m1["probe_eval"]["felt_b12"]


def test_felt_beats_surprise_in_harness():
    shutil.rmtree("/tmp/felt_h2", ignore_errors=True)
    cfg = RunConfig(workdir="/tmp/felt_h2", train_worlds=3,
                    train_episodes_per_world=15, eval_worlds=4,
                    eval_episodes_per_world=20,
                    policies=("surprise_only", "felt_b12"))
    m = Harness(cfg).run()["probe_eval"]
    assert m["felt_b12"]["dissociation"] > m["surprise_only"]["dissociation"] + 0.1


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn(); ok += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{ok}/{len(fns)} passed")
