"""Tests for the FeltCraft game tier (PREWORK items 1-3)."""

from __future__ import annotations

import json

import numpy as np

from game import (World, FeltCraft, scripted_optimal_play, gen_dag,
                  requirements, oracle_value, generate_dataset,
                  curriculum_goals)


def test_dag_depth_and_solvability():
    for seed in range(5):
        dag = gen_dag(seed, depth=5, branching=3, n_raw=6)
        assert dag.max_depth() == 5
        # every recipe's ingredients exist and are strictly shallower
        for it, (a, b) in dag.recipes.items():
            assert dag.depth_of[a] < dag.depth_of[it]
            assert dag.depth_of[b] < dag.depth_of[it]
        # requirements closure bottoms out in raws only
        deep = [i for i in dag.recipes if dag.depth_of[i] == 5][0]
        req = requirements(dag, deep)
        assert all(r in dag.raws for r in req["raw_needs"])
        assert deep in req["crafts"]


def test_scripted_agent_wins_all_depths():
    w = World.generate("w", seed=3, depth=5, branching=3)
    for goal in list(w.dag.recipes):
        env = FeltCraft(w, max_steps=120)
        scripted_optimal_play(env, goal, 0)
        assert env.success, f"solver failed on {goal}"


def test_oracle_zero_iff_done():
    w = World.generate("w", seed=1)
    goal = [i for i in w.dag.recipes if w.dag.depth_of[i] == 2][0]
    env = FeltCraft(w)
    scripted_optimal_play(env, goal, 0)
    vs = [t["oracle_V"] for t in env.trajectory]
    assert vs[-1] == 0.0
    assert all(v > 0 for v in vs[:-1])


def test_salience_fires_on_progress_and_sums_to_initial_V():
    # clipped TD salience over an optimal run ~ initial V (allowing explore detours)
    w = World.generate("w", seed=2, depth=4)
    goal = [i for i in w.dag.recipes if w.dag.depth_of[i] == 4][0]
    env = FeltCraft(w, max_steps=100)
    r0 = env.reset(goal, 0)
    v0 = r0["oracle_V"]
    scripted_optimal_play(env, goal, 0)
    total_sal = sum(t["salience"] for t in env.trajectory)
    assert total_sal >= v0, (total_sal, v0)   # progress accounted (detours add)


def test_fact_labels_structural_vs_detail():
    w = World.generate("w", seed=4)
    goal = list(w.dag.recipes)[0]
    env = FeltCraft(w)
    scripted_optimal_play(env, goal, 0)
    kinds = {(f.kind, f.structural) for f in env.episode_facts}
    for kind, structural in kinds:
        assert (kind in ("recipe", "location")) == structural, kinds
    # world-level gist enumerable
    wf = w.structural_facts()
    assert all(f.structural for f in wf)
    assert len(wf) == len(w.dag.recipes) + len(w.dag.raws)


def test_episode_determinism():
    w = World.generate("w", seed=9)
    goal = list(w.dag.recipes)[2]
    outs = []
    for _ in range(2):
        env = FeltCraft(w)
        scripted_optimal_play(env, goal, episode_seed=5)
        outs.append([t["action"] for t in env.trajectory])
    assert outs[0] == outs[1]


def test_cross_episode_memory_helps():
    # carrying known locations across episodes must reduce steps (the game's
    # core property: memory pays)
    w = World.generate("w", seed=6, depth=4)
    goal = [i for i in w.dag.recipes if w.dag.depth_of[i] == 4][0]
    cold = FeltCraft(w, max_steps=120)
    scripted_optimal_play(cold, goal, 0)
    warm = FeltCraft(w, max_steps=120)
    scripted_optimal_play(warm, goal, 1, known_locations=set(w.locations))
    assert warm.steps < cold.steps, (warm.steps, cold.steps)


def test_dataset_generation_and_schema():
    r = generate_dataset("/tmp/feltcraft_ds.jsonl", n_worlds=2,
                         episodes_per_world=6, seed=11)
    assert r["episodes"] == 12 and r["success_rate"] == 1.0
    with open(r["path"]) as f:
        rec = json.loads(f.readline())
    for key in ("world", "episode", "goal", "success", "trajectory", "facts"):
        assert key in rec
    step = rec["trajectory"][0]
    for key in ("obs", "action", "oracle_V", "salience"):
        assert key in step


def test_curriculum_deepens():
    w = World.generate("w", seed=8, depth=5)
    goals = curriculum_goals(w, 60, seed=0)
    d = [w.dag.depth_of[g] for g in goals]
    assert np.mean(d[:20]) < np.mean(d[-20:])   # later goals deeper on average


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
