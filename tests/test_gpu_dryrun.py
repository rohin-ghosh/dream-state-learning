"""End-to-end DRY RUN of the GPU pipeline on CPU with fake artifacts in the exact
S1 schema (redteam_7's method, made permanent). Proves S1(read)→S2→S3 compose
before any lease: tolerant JSONL reading, state-cache format, head training with
P0-1 normalization at realistic hidden dims/norms, kill-switch printout, S3 policy
zoo. Run: PYTHONPATH=. python3 tests/test_gpu_dryrun.py
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np

from game import World, FeltCraft
from game.engine import scripted_noisy_play
from gpu.rollouts import text_key, read_jsonl_tolerant

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path("/tmp/gpu_dryrun/s1")
D_H = 1536      # Qwen2.5-1.5B hidden size
NORM = 900.0    # realistic raw hidden-state row norm (P0-1 regime)


def make_fake_s1(n_worlds=3, eps_per_world=20):
    shutil.rmtree(OUT.parent, ignore_errors=True)
    OUT.mkdir(parents=True)
    rng = np.random.default_rng(0)
    states = {}
    with open(OUT / "rollouts.jsonl", "w") as f:
        ep_uid = 0
        for i in range(n_worlds):
            seed = 0 * 7 + i
            world = World.generate(f"s1_{i}", seed=seed, depth=4)
            known = set()
            goals = list(world.dag.recipes)
            for e in range(eps_per_world):
                env = FeltCraft(world, max_steps=120)
                scripted_noisy_play(env, goals[e % len(goals)],
                                    episode_seed=ep_uid, known_locations=known,
                                    detour_rate=0.3, seed=1)
                known |= env.known_locations
                # fake "hidden states": salience-correlated direction + noise,
                # scaled to realistic norms — lets the head LEARN if (and only if)
                # normalization works
                for st in env.trajectory:
                    t = f"{st['action']} {st['obs']}"
                    k = text_key(t)
                    if f"{k}_l-1" not in states:
                        base = rng.normal(0, 1, D_H)
                        base[0] = 8.0 * st["salience"]          # the signal
                        v = base / np.linalg.norm(base) * NORM  # realistic scale
                        for l in (-1, -4, -8):
                            states[f"{k}_l{l}"] = v.astype(np.float32)
                f.write(json.dumps({
                    "episode_uid": f"ep{ep_uid:06d}", "world": world.world_id,
                    "world_seed": seed, "depth": 4, "goal": goals[e % len(goals)],
                    "success": env.success, "steps": env.steps,
                    "trajectory": env.trajectory,
                    "facts": [{"text": fa.text, "kind": fa.kind,
                               "structural": fa.structural, "step": fa.step}
                              for fa in env.episode_facts]}) + "\n")
                ep_uid += 1
        f.write('{"episode_uid": "ep999999", "truncat')   # deliberate torn tail
    np.savez(OUT / "states.npz", **states)


def test_tolerant_reader_skips_torn_tail():
    make_fake_s1(n_worlds=2, eps_per_world=4)
    recs = read_jsonl_tolerant(OUT / "rollouts.jsonl")
    assert len(recs) == 8 and all("trajectory" in r for r in recs)


def test_s2_then_s3_compose():
    make_fake_s1()
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    r2 = subprocess.run(
        [sys.executable, "gpu/train_head_real.py", "--in", str(OUT),
         "--epochs", "20", "--out", "/tmp/gpu_dryrun/s2_head.npz"],
        capture_output=True, text=True, cwd=ROOT, env=env)
    assert r2.returncode == 0, r2.stderr[-800:]
    assert "KILL-SWITCH" in r2.stdout
    # P0-1 check: with normalization + planted signal the head must LEARN
    z = np.load("/tmp/gpu_dryrun/s2_head.npz")
    assert float(z["regret"]) < 0.09, f"regret {float(z['regret'])} — head failed " \
        "to learn a PLANTED signal; normalization regression?"
    r3 = subprocess.run(
        [sys.executable, "gpu/probe_eval_real.py", "--in", str(OUT),
         "--head", "/tmp/gpu_dryrun/s2_head.npz",
         "--out", "/tmp/gpu_dryrun/s3.json"],
        capture_output=True, text=True, cwd=ROOT, env=env)
    assert r3.returncode == 0, r3.stderr[-800:]
    s3 = json.loads(pathlib.Path("/tmp/gpu_dryrun/s3.json").read_text())
    for pol in ("uniform", "keyword_gate", "felt_b12", "oracle_weight"):
        assert pol in s3 and np.isfinite(s3[pol]["dissociation"])


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
