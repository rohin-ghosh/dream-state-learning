"""Gym protocol round trip for both gyms (CPU; the compiler gym runs on a
fake cgym subprocess; the reasoning gym needs pip reasoning-gym==0.1.25 and
is SKIPPED with a message when it is not importable).

  python3 tests/test_gym_protocol.py
"""
from __future__ import annotations

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import golden_harness as gh  # noqa: E402
from organism_v6 import gym_backend as gb  # noqa: E402
from organism_v6 import run_life  # noqa: E402
from organism_v6.batch_loop import (EpisodeDriver, NoEndTokenDriver,  # noqa: E402
                                    driver_class_for, run_episodes_batch)
from organism_v6.ledger import Ledger  # noqa: E402

SKIPPED = []


def _rg_available():
    try:
        import reasoning_gym  # noqa: F401
        return True
    except ImportError:
        return False


class _Fakes:
    """Fake cgym subprocess for the compiler gym (no node venv)."""

    def __enter__(self):
        self.tr = gh.Transcript()
        self.saved = gb.CompilerGym._call
        gb.CompilerGym._call = gh.make_fake_call(self.tr)
        return self.tr

    def __exit__(self, *a):
        gb.CompilerGym._call = self.saved


def test_compiler_gym_wraps_existing_behaviour_exactly():
    with _Fakes() as tr:
        gym = gb.make_gym("compiler")
        assert isinstance(gym, gb.Gym) and gym.name == "compiler"
        assert gym.splits() == ["train", "gate", "exam", "canary"]
        # sets: exam = the 8 report programs, canary = their first 4, gate = None
        assert gym.exam_set() == list(run_life.PROBES)
        assert gym.canary_set() == list(run_life.PROBES[:4])
        assert gym.gate_set() is None
        assert gym.benchmarks("exam") == list(run_life.PROBES)
        # train excludes every report program and equals the legacy pool
        train = gym.benchmarks("train")
        assert train and not (set(train) & set(run_life.PROBES))
        assert gym.training_schedule(20, 3) == \
            run_life.get_training_programs(gb.CompilerGym(), 20, 3)
        # episodes render exactly as Episode(eid=...) did
        for eid in train[:3] + list(run_life.PROBES[:2]):
            ep = gym.episode_from_id(eid, 16)
            old = gb.Episode(eid=eid)
            assert (ep.goal, ep.metric, ep.intro, ep.eid) == \
                (old.goal, old.metric, old.intro, old.eid)
            assert ep.id == eid and ep.goal_text == old.goal and \
                ep.metric_name == old.metric and ep.intro_text == old.intro
            assert ep.family == "cbench-v1" and ep.budget_ticks == 16
        # step/evaluate: same parsing, same subprocess call, same text
        ep = gym.episode_from_id("cbench-v1/crc32")
        legacy = gb.CompilerGym().evaluate(gb.Episode(eid="cbench-v1/crc32"),
                                           "-mem2reg, -sroa -gvn")
        obs = gym.step(ep, "-mem2reg, -sroa -gvn")
        assert isinstance(obs, gb.Observation)
        assert (obs.score, obs.text) == legacy and obs.harness_done is False
        assert tr.events[-1]["passes"] == "-mem2reg,-sroa,-gvn"
        assert gym.evaluate(ep, "-mem2reg, -sroa -gvn") == legacy   # driver contract
        assert gym.evaluate(ep) == obs.score == ep.best_score      # episode score
        s2, t2 = gym.evaluate(ep, "-bogus")
        assert s2 == 0.0 and t2.startswith("INVALID:")
        assert gym.evaluate(ep) == obs.score and ep.n_attempts == 3
        # texts and terms
        assert gym.birth_prompt() == run_life.BOOTSTRAP
        assert "DONE" in gym.birth_prompt() and gym.offers_end_token()
        assert set(["-mem2reg", "-sroa", "-gvn", "-simplifycfg"]) <= set(gym.leak_terms())
        assert "cbench-v1/susan" in gym.leak_terms()
        assert gym.headroom_ceiling(ep) is None
        assert gym.exposure_domain().startswith("compiler_gym")
        assert gym.family_of("benchmark://npb-v0/10") == "npb-v0"
        from organism_v6.sleep_compile import COMPILER_VOCAB
        assert gym.compile_vocab() == COMPILER_VOCAB
        assert gym.compile_vocab()["win_question"] == "which passes improve it?"
        # make_episode draws inside the split
        rng = random.Random(0)
        for _ in range(5):
            e = gym.make_episode("train", rng)
            assert e.eid in train
        assert gym.make_episode("exam", rng).eid in run_life.PROBES
        # dataset-name passthrough (what run_life.get_training_programs uses)
        assert gym.benchmarks("chstone-v0") == gh.DATASETS["chstone-v0"]


def test_compiler_gate_panel_and_overlap_check():
    with _Fakes():
        gym = gb.make_gym("compiler", gate_panel=list(gh.GATE_PANEL))
        assert gym.gate_set() == gh.GATE_PANEL
        assert gym.benchmarks("gate") == gh.GATE_PANEL
        assert "npb-v0/10" in gym.leak_terms()
        try:
            gb.make_gym("compiler", gate_panel=["cbench-v1/susan"])
        except RuntimeError as e:
            assert "overlaps report panel" in str(e)
        else:
            raise AssertionError("overlap not refused")


def test_registry():
    assert gb.gym_names() == ["compiler", "reasoning_gym"]
    try:
        gb.make_gym("no_such_gym")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown gym accepted")
    gb.register_gym("_test_dummy", lambda **kw: "dummy")
    assert gb.make_gym("_test_dummy") == "dummy"
    del gb._REGISTRY["_test_dummy"]


def test_driver_hook_default_and_no_end_token():
    with _Fakes():
        gym = gb.make_gym("compiler")
        assert driver_class_for(gym) is EpisodeDriver
        assert driver_class_for(object()) is EpisodeDriver     # no method: default

        class NoEnd(gb.CompilerGymGym):
            def offers_end_token(self):
                return False
        g2 = NoEnd()
        assert driver_class_for(g2) is NoEndTokenDriver
        tr = gh.Transcript()
        gh.FakeModel.transcript = tr
        model = gh.FakeModel()
        led = Ledger(os.devnull)
        # template 3 carries DONE: the default driver ends the episode early,
        # the no-end-token driver runs it to the budget
        eps = [gym.episode_from_id("cbench-v1/crc32", 6)]
        res_default = run_episodes_batch(model, gym, eps, gym.birth_prompt(),
                                         led, 6, log=lambda m: None, gen_seed=1)
        res_noend = run_episodes_batch(model, g2, eps, g2.birth_prompt(), led,
                                       6, log=lambda m: None, gen_seed=1,
                                       driver_cls=driver_class_for(g2))
        assert res_noend[0]["ticks"] == 6
        assert res_default[0]["ticks"] <= 6


def test_reasoning_gym_round_trip():
    if not _rg_available():
        SKIPPED.append("test_reasoning_gym_round_trip (pip install reasoning-gym==0.1.25)")
        print("SKIP reasoning_gym not importable")
        return
    gym = gb.make_gym("reasoning_gym")
    assert isinstance(gym, gb.Gym) and gym.name == "reasoning_gym"
    assert not gym.offers_end_token() and driver_class_for(gym) is NoEndTokenDriver
    assert "DONE" not in gym.birth_prompt() and "-mem2reg" not in gym.birth_prompt()
    assert "LLVM" not in gym.birth_prompt() and "compiler" not in gym.birth_prompt().lower()
    rng = random.Random(1)
    for split in gym.splits():
        ep = gym.make_episode(split, rng, 16)
        assert ep.family and ep.budget_ticks == 16 and ep.goal and ep.intro
        assert gym.split_of(ep.eid) == split, (split, ep.eid)
    ep = gym.episode_from_id("rg/n_queens/2000001")
    ref = gym.reference_answer(ep.eid)
    assert gym.headroom_ceiling(ep) == 1.0
    obs = gym.step(ep, "nonsense")
    assert 0.0 <= obs.score < 0.1 and "verifier score" in obs.text
    assert str(ref) not in obs.text
    s, t = gym.evaluate(ep, ref.replace("\n", " ; "))       # driver contract
    assert s == 1.0 and "accepted" in t
    assert gym.evaluate(ep) == 1.0 and ep.n_attempts == 2
    assert set(gym.exam_families) <= set(gym.leak_terms())
    assert gym.answer_terms(ep) == [ref]
    assert gym.exposure_domain().startswith("reasoning_gym:")
    v = gym.compile_vocab()
    assert v["noun"] == "Puzzle" and not any(
        w in " ".join(v.values()).lower() for w in ("program", "pass", "optimi", "compil"))
    # the deployment vocabulary never appears in this gym's own texts
    from organism_v6.run_life_v2 import deployment_leak_regex
    rx = deployment_leak_regex()
    assert not rx.search(gym.birth_prompt())
    for split in gym.splits():
        e = gym.make_episode(split, random.Random(3), 4)
        assert not rx.search(e.goal + e.intro + e.metric), (split, e.eid)
    print("prompt sizes:", json.dumps(gym.measure_prompt_sizes(2)))


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed"
          + (f" ({len(SKIPPED)} skipped: {SKIPPED})" if SKIPPED else ""))
    sys.exit(1 if failed else 0)
