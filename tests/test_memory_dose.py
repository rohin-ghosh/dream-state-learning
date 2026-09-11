"""CPU tests for organism_v6/memory_dose.py (mock model; no GPU, no torch).

  python3 tests/test_memory_dose.py
  python3 -m pytest tests/test_memory_dose.py -q

Covers: bank balance/reproducibility, OFF-before-assignment with random
balanced (default) vs opt-in prior-matched assignment and counterbalancing,
exposure-arm accounting, corpus semantics (dedup vs occurrences vs
multiplicity weight in the loss), marginals and token budget (+ over-budget
enforcement), chronological (prior-first) vs content ordering and the
within/across sleep-4 identity (same items, different order), the
scrambled-binding control, joint context+target tokenization of the trainer
(runs when the deployed tokenizer is cached offline; transformers only),
evaluator arithmetic on toy distributions, gates (incl. the candidate-mass
gate and the G2 base-rate fallback) + interpretation on four mock behaviour
profiles, OFF-prior bins, training-text fit, paired bootstrap, lambda sweep,
lessons with terminated action strings, write containment, synthetic flags
(incl. adapter README.md), and the LoRA config mirror of train_adapter.py.
"""
from __future__ import annotations

import builtins
import copy
import json
import math
import os
import re
import shutil
import sys
import tempfile

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from organism_v6 import memory_dose as md  # noqa: E402

SCRATCH = os.environ.get("MEMORY_DOSE_TEST_DIR") or tempfile.mkdtemp(prefix="memory_dose_test_")
BUDGET = 60000          # approx tokens; large enough for the sleep-6 occurrence corpora
_RUN: dict = {}
_TOK: dict = {}


def _run_dir(name: str) -> str:
    d = os.path.join(SCRATCH, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def _generate(name: str, seed: int = 0, **kw) -> str:
    d = _run_dir(name)
    md.generate_run(d, seed, md.MockScorer(seed=seed), md.TokenCounter("approx"),
                    token_budget=BUDGET, distractor_tokens=300, **kw)
    return d


def _tokenizer():
    """The deployed tokenizer when it is cached offline (transformers without
    torch is enough); None otherwise -> the tokenizer tests print SKIP."""
    if "tok" in _TOK:
        return _TOK["tok"]
    tok = None
    try:
        from transformers import AutoTokenizer
        for name in (md.MODEL_NAME, "Qwen/Qwen2.5-0.5B-Instruct"):   # same vocabulary
            try:
                tok = AutoTokenizer.from_pretrained(name)
                break
            except Exception:  # noqa: BLE001
                tok = None
    except Exception:  # noqa: BLE001
        tok = None
    _TOK["tok"] = tok
    return tok


def shared_run() -> dict:
    """One generated run + a few corpora, built once for the whole file."""
    if _RUN:
        return _RUN
    d = _generate("shared")
    bank = md.read_json(os.path.join(d, "banks", "bank0.json"))
    counter = md.TokenCounter("approx")
    corp = {}
    for cell in ("A", "B", "C", "D", "Dshuf", "Dw"):
        w, r, s = md.CELLS[cell]
        corp[cell] = md.build_corpus(bank, "across", 4, w, r, counter, BUDGET, shuffled=s)
    _RUN.update(dir=d, bank=bank, counter=counter, corpora=corp,
                banks=[md.read_json(os.path.join(d, "banks", f"bank{b}.json")) for b in range(3)])
    return _RUN


def _pipeline(run: dict, cell: str, profile: str, tag: str, lambdas=None, arm="across", sleep=4):
    """mock train + evaluate + summarize one cell of bank 0."""
    d = run["dir"]
    md.set_write_root(d)
    w, r, s = md.CELLS[cell]
    if cell in run["corpora"] and arm == "across" and sleep == 4:
        c = run["corpora"][cell]
    else:
        c = md.build_corpus(run["bank"], arm, sleep, w, r, run["counter"], BUDGET, shuffled=s)
    cdir = md.cell_dir(d, 0, cell, arm, sleep)
    cpath = md.write_json(os.path.join(cdir, "corpus.json"), c)
    adir = os.path.join(d, "adapters", "bank0", cell, arm, f"sleep{sleep}", f"r8_{profile}")
    md.train_command(d, cpath, adir, model="mock", mock_profile=profile, no_reuse=True)
    paths = md.evaluate_command(d, 0, adir, tag, model="mock", lambdas=lambdas,
                                meta=dict(cell=cell, arm=arm, sleep=sleep, rank=8))
    evs = [md.read_json(p) for p in paths]
    return evs, [md.summarize_eval(ev, run["bank"]) for ev in evs]


def _bank_items(c: dict) -> list:
    return [it for it in c["corpus"] if it["kind"] in ("fact", "interference", "lesson")]


# ---------------------------------------------------------------------------
def test_bank_balance_ids_and_lessons():
    run = shared_run()
    for bank in run["banks"]:
        owners = bank["owners"]
        assert len(owners) == 64
        ids = [o["id"] for o in owners]
        assert len(set(ids)) == 64
        assert all(md.OWNER_RE.fullmatch(i) for i in ids)
        for d in md.DOSES:
            grp = [o for o in owners if o["dose"] == d]
            assert len(grp) == 16, (d, len(grp))
            for c in md.COLOURS:
                assert sum(1 for o in grp if o["colour"] == c) == 4
        sims = [o["similar_id"] for o in owners]
        assert len(set(sims)) == 64 and not set(sims) & set(ids)
        assert all(md._hamming(o["id"], o["similar_id"]) == 1 for o in owners)
        col = {o["id"]: o["colour"] for o in owners}
        dose = {o["id"]: o["dose"] for o in owners}
        for o in owners:
            assert o["partner"] and dose[o["partner"]] == o["dose"] and col[o["partner"]] != o["colour"]
        inter = bank["interference"]["owners"]
        for s in md.INTERFERENCE_SLEEPS:
            grp = [o for o in inter if o["session"] == s]
            assert len(grp) == 32 and all(sum(1 for o in grp if o["colour"] == c) == 8 for c in md.COLOURS)
        assert not {o["id"] for o in inter} & set(ids) and not {o["id"] for o in inter} & set(sims)
        les = bank["lessons"]
        assert len(les) == 16 and all(sum(1 for L in les if L["dose"] == d) == 4 for d in md.DOSES)
        for pair in md.MODE_PAIRS:
            grp = [L for L in les if tuple(L["modes"]) == pair]
            assert len(grp) == 4 and sum(L["direction"] for L in grp) == 2
        for pair in md.ACTION_PAIRS:
            grp = [L for L in les if tuple(L["actions"]) == pair]
            assert len(grp) == 4 and sum(L["direction"] for L in grp) == 2
        ev_ids = [e["event_id"] for e in bank["events"] + bank["lesson_events"] + bank["interference"]["events"]]
        assert len(ev_ids) == len(set(ev_ids))
        assert len(bank["events"]) == 16 * (1 + 4 + 16)
        assert len(bank["lesson_events"]) == 4 * (1 + 4 + 16)


def test_generation_reproducible_and_seed_sensitive():
    a = _generate("repro_a", seed=7)
    b = _generate("repro_b", seed=7)
    c = _generate("repro_c", seed=8)
    for i in range(3):
        ja = md.read_json(os.path.join(a, "banks", f"bank{i}.json"))
        jb = md.read_json(os.path.join(b, "banks", f"bank{i}.json"))
        assert ja == jb, f"bank{i} differs across identical seeds"
    jc = md.read_json(os.path.join(c, "banks", "bank0.json"))
    ja = md.read_json(os.path.join(a, "banks", "bank0.json"))
    assert {o["id"] for o in jc["owners"]} != {o["id"] for o in ja["owners"]}
    for d in (a, b, c):
        shutil.rmtree(d)


def test_off_measured_before_assignment_random_balanced_and_counterbalanced():
    run = shared_run()
    banks = run["banks"]
    manifest = md.read_json(os.path.join(run["dir"], "manifest.json"))
    assert manifest["prior_match"] is False and "random balanced" in manifest["assignment"]
    assert manifest["prior_bin_edges"] == md.PRIOR_BIN_EDGES
    for bank in banks:
        assert bank["assignment_after_off_measurement"] is True and bank["prior_match"] is False
        for o in bank["owners"]:
            for form in ("p1", "p2", "p3", "base_rate", "completion"):
                dist = bank["off"][o["id"]][form]
                assert abs(sum(dist["p_norm"].values()) - 1) < 1e-9 and 0 < dist["mass"] <= 1
            assert o["prior_assigned"] is not None
        # random balanced assignment: the dose groups' mean OFF prior of the assigned colour is
        # near 1/4 by balance alone (no optimisation on the measurement)
        for d in md.DOSES:
            grp = [o["prior_assigned"] for o in bank["owners"] if o["dose"] == d]
            assert abs(sum(grp) / len(grp) - 0.25) < 0.12, (d, sum(grp) / len(grp))
    # shared owners: the same owner gets three different colours across banks
    cols = {}
    for bank in banks:
        for o in bank["owners"]:
            cols.setdefault(o["id"], []).append(o["colour"])
    assert all(len(v) == 3 and len(set(v)) == 3 for v in cols.values())
    # the assignment is NOT a function of the OFF measurement: re-generating with a different mock
    # scorer seed (different OFF distribution, same owner/bank seed) gives the same colours
    d2 = _run_dir("prior_indep")
    md.generate_run(d2, 0, md.MockScorer(seed=99), md.TokenCounter("approx"), token_budget=BUDGET,
                    distractor_tokens=300)
    b2 = md.read_json(os.path.join(d2, "banks", "bank0.json"))
    assert [o["colour"] for o in b2["owners"]] == [o["colour"] for o in banks[0]["owners"]]
    assert b2["off"] != banks[0]["off"]
    # opt-in prior matching is recorded and tightens the match
    d3 = _generate("prior_match", prior_match=True)
    m3 = md.read_json(os.path.join(d3, "manifest.json"))
    assert m3["prior_match"] is True and "prior-matched" in m3["assignment"]
    b3 = md.read_json(os.path.join(d3, "banks", "bank0.json"))
    assert b3["prior_match"] is True
    for d in md.DOSES:
        grp = [o["prior_assigned"] for o in b3["owners"] if o["dose"] == d]
        assert abs(sum(grp) / len(grp) - 0.25) < 0.06, (d, sum(grp) / len(grp))
    shutil.rmtree(d2)
    shutil.rmtree(d3)


def test_exposure_arm_accounting():
    run = shared_run()
    bank = run["bank"]
    for arm in md.ARMS:
        sched = bank["schedule"][arm]
        for o in bank["owners"]:
            evs = [e for e in bank["events"] if e["owner"] == o["id"]]
            assert len(evs) == o["dose"]
            sessions = sorted(sched[e["event_id"]] for e in evs)
            if o["dose"] > 0:
                assert sessions[-1] == 4, (arm, o["dose"], sessions)      # matched last exposure
                assert all(1 <= s <= 4 for s in sessions)                  # never in interference sleeps
            if arm == "within":
                assert all(s == 4 for s in sessions)
            elif o["dose"] == 16:
                assert [sessions.count(s) for s in (1, 2, 3, 4)] == [4, 4, 4, 4]
            elif o["dose"] == 4:
                assert sessions == [1, 2, 3, 4]
            elif o["dose"] == 1:
                assert sessions == [4]
        for L in bank["lessons"]:
            evs = [e for e in bank["lesson_events"] if e["lesson_id"] == L["lesson_id"]]
            sessions = sorted(sched[e["event_id"]] for e in evs)
            assert len(evs) == L["dose"] and (not sessions or sessions[-1] == 4)
            if L["dose"] >= 4:
                assert {e["mode"] for e in evs} == set(L["modes"])       # both branches exposed
        for e in bank["interference"]["events"]:
            assert sched[e["event_id"]] in md.INTERFERENCE_SLEEPS
    # totals identical across arms
    for o in bank["owners"]:
        n = {arm: sum(1 for e in bank["events"] if e["owner"] == o["id"] and e["event_id"] in bank["schedule"][arm])
             for arm in md.ARMS}
        assert n["within"] == n["across"] == o["dose"]
    assert md.schedule_sessions(2, "across") == [3, 4] and md.schedule_sessions(3, "across") == [2, 3, 4]
    assert md.schedule_sessions(0, "across") == [] and md.schedule_sessions(5, "within") == [4] * 5


def test_corpus_semantics_dedup_occurrences_weight():
    run = shared_run()
    A, B, Dw = run["corpora"]["A"], run["corpora"]["B"], run["corpora"]["Dw"]
    facts = lambda c: [it for it in c["corpus"] if it["kind"] == "fact"]  # noqa: E731
    assert len(facts(A)) == 48 and len(facts(B)) == 336 and len(facts(Dw)) == 48
    assert all(it["weight"] == 1.0 for it in facts(A))
    assert sum(it["weight"] for it in facts(Dw)) == 336
    assert sorted(it["n_occurrences"] for it in facts(Dw) if it["weight"] == 16) == [16] * 16
    assert set(len(it["event_ids"]) for it in facts(A)) == {1, 4, 16}
    assert A["stats"]["n_event_ids"] == B["stats"]["n_event_ids"] == 336 + 84   # nothing lost, ids distinct
    dose = {o["id"]: o["dose"] for o in run["bank"]["owners"]}
    for oid, d in dose.items():
        if d == 0:
            continue
        assert A["stats"]["presentations_per_owner"][oid] == 3            # dedup erases dose
        assert B["stats"]["presentations_per_owner"][oid] == 3 * d        # occurrences carry it
        assert Dw["stats"]["presentations_per_owner"][oid] == 3 * d       # so does the loss weight
    # today's dedup key: cross-check against organism_v6.sleep_compile.dedup on the short pieces
    from organism_v6 import sleep_compile
    texts = [it["context"] + it["target"] for it in facts(B)]
    assert len(sleep_compile.dedup(texts)) == 48
    assert len({md.dedup_key(t) for t in texts}) == 48
    # antecedent pieces of different owners never collide under the key
    ante = [it["context"] + it["target"] for it in facts(run["corpora"]["D"])]
    assert len({md.dedup_key(t) for t in ante}) == 48
    # representation semantics
    a0 = facts(A)[0]
    assert a0["chat"] is False and a0["mask_context"] is False and a0["context"].startswith("Owner ")
    d0 = facts(run["corpora"]["D"])[0]
    assert d0["chat"] is True and d0["mask_context"] is True and d0["context"].startswith("Situation:")
    assert md.render_item(d0).startswith("<|im_start|>system") and md.render_item(d0).endswith(md.IM_END)


def test_weighted_loss_reference_and_trainer_uses_it():
    r1, r2 = [0.5, 1.5, 2.0], [3.0, 1.0]
    assert math.isclose(md.weighted_token_nll([r1], [3.0]), md.weighted_token_nll([r1, r1, r1], [1, 1, 1]))
    assert math.isclose(md.weighted_token_nll([r1, r2], [3.0, 1.0]),
                        md.weighted_token_nll([r1, r1, r1, r2], [1, 1, 1, 1]))
    assert math.isclose(md.weighted_token_nll([r1], [1.0]), sum(r1) / len(r1))
    assert math.isnan(md.weighted_token_nll([], []))
    # the trainer's loss goes through the torch twin of the reference (not a dead helper)
    src = open(os.path.join(ROOT, "organism_v6", "memory_dose.py")).read()
    body = src.split("def train_hf(")[1].split("\ndef ")[0]
    assert "weighted_token_nll_torch(nll, valid, w)" in body
    try:
        import torch
    except Exception:  # noqa: BLE001
        print("SKIP torch absent: torch twin of the weighted loss not executed here")
        return
    nll = torch.tensor([[0.5, 1.5, 2.0, 0.0], [3.0, 1.0, 0.0, 0.0]])
    valid = torch.tensor([[1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0]])
    loss, den = md.weighted_token_nll_torch(nll, valid, torch.tensor([3.0, 1.0]))
    assert math.isclose(float(loss), md.weighted_token_nll([r1, r2], [3.0, 1.0]), rel_tol=1e-6)
    assert float(den) == 11.0


def test_marginals_identical_and_token_budget_and_over_budget_enforced():
    run = shared_run()
    bank, counter = run["bank"], run["counter"]
    M = bank["marginal_target"]
    assert M == 16 * 0 + 4 * (1 + 4 + 16) + 2 * 32     # 84 fact + 64 interference per colour
    seen = []
    for cell in ("A", "B", "D", "Dshuf"):
        w, r, s = md.CELLS[cell]
        for arm in md.ARMS:
            for k in (1, 4, 6):
                c = md.build_corpus(bank, arm, k, w, r, counter, BUDGET, shuffled=s)
                st = c["stats"]
                assert st["colour_marginals"] == {col: M for col in md.COLOURS}, (cell, arm, k, st["colour_marginals"])
                assert not st["over_budget"] and st["n_tokens"] <= BUDGET
                assert BUDGET - st["n_tokens"] < 120, (cell, arm, k, st["n_tokens"])   # within one filler item
                seen.append(st["n_tokens"])
    assert max(seen) - min(seen) < 120
    # over budget is flagged on the corpus and FATAL for corpus-all (no silent size differences)
    w, r, s = md.CELLS["D"]
    c = md.build_corpus(bank, "across", 6, w, r, counter, 20000)
    assert c["stats"]["over_budget"] and c["stats"]["content_tokens"] > 20000
    d = _generate("overbudget")
    try:
        md.corpus_all(d, counter, cells=["D"], arms=["across"], sleeps=[6], token_budget=20000)
        raise AssertionError("corpus_all accepted an over-budget corpus")
    except RuntimeError as exc:
        assert "exceeds the token budget" in str(exc)
    idx = md.read_json(os.path.join(d, "corpora", "index.json"))
    assert idx["over_budget"] == ["bank0/D/across/sleep6", "bank1/D/across/sleep6", "bank2/D/across/sleep6"]
    assert idx["max_content_tokens"] > 20000
    out = md.corpus_all(d, counter, cells=["D"], arms=["across"], sleeps=[6], token_budget=20000, strict_budget=False)
    assert len(out["over_budget"]) == 3
    shutil.rmtree(d)


def test_chronological_ordering_prior_first_and_arms_differ_in_order():
    run = shared_run()
    bank, counter = run["bank"], run["counter"]
    wB, rB, _ = md.CELLS["B"]
    a4 = md.build_corpus(bank, "across", 4, wB, rB, counter, BUDGET)
    w4 = md.build_corpus(bank, "within", 4, wB, rB, counter, BUDGET)
    a5 = md.build_corpus(bank, "across", 5, wB, rB, counter, BUDGET)
    assert a4["ordering"] == md.DEFAULT_ORDERING == "chronological" and a4["stats"]["ordering"] == "chronological"
    # session blocks: bank items sit in non-decreasing session order (prior-first, as compile_sleep)
    sess = [it["session"] for it in a4["corpus"] if it["kind"] in ("fact", "interference", "lesson")]
    assert sess == sorted(sess) and set(sess) == {1, 2, 3, 4}
    # facts 64+16 per session (+16 dose-1 in session 4), lessons 16+4 per session (+4 dose-1 in session 4)
    assert a4["stats"]["session_blocks"] == {"1": 80 + 20, "2": 80 + 20, "3": 80 + 20, "4": 96 + 24}
    assert all(it["session"] == 4 for it in _bank_items(w4))                 # within: everything in the last block
    # same item multiset, different order -> different corpus (separate fits); content ordering -> identical
    assert a4["items_sha"] == w4["items_sha"] and a4["sha"] != w4["sha"]
    assert sorted(md.render_item(it) for it in a4["corpus"]) == sorted(md.render_item(it) for it in w4["corpus"])
    assert [md.render_item(it) for it in a4["corpus"]] != [md.render_item(it) for it in w4["corpus"]]
    ca = md.build_corpus(bank, "across", 4, wB, rB, counter, BUDGET, ordering="content")
    cw = md.build_corpus(bank, "within", 4, wB, rB, counter, BUDGET, ordering="content")
    assert ca["sha"] == cw["sha"] and ca["items_sha"] == a4["items_sha"] and ca["ordering"] == "content"
    # every corpus item is a padding item or a bank item; padding interleaves with every session block
    fill_sess = {it["session"] for it in a4["corpus"] if it["kind"].startswith("filler")}
    assert fill_sess == {1, 2, 3, 4}
    # prior-first across sleeps: the sleep-4 bank items keep their relative order inside the sleep-5
    # corpus and every session-5 item comes after them
    seq4 = [it["event_ids"][0] for it in _bank_items(a4)]
    seq5_old = [it["event_ids"][0] for it in _bank_items(a5) if it["session"] <= 4]
    assert seq4 == seq5_old
    pos5 = [i for i, it in enumerate(a5["corpus"]) if it.get("session") == 5]
    assert pos5 and min(pos5) > max(i for i, it in enumerate(a5["corpus"]) if it.get("session") is not None and it["session"] <= 4)
    # dedup keeps the FIRST occurrence: the dose-16 owners' single piece sits in session 1 across, 4 within
    wA, rA, _ = md.CELLS["A"]
    dA = md.build_corpus(bank, "across", 4, wA, rA, counter, BUDGET)
    dW = md.build_corpus(bank, "within", 4, wA, rA, counter, BUDGET)
    d16 = {o["id"] for o in bank["owners"] if o["dose"] == 16}
    assert {it["session"] for it in dA["corpus"] if it["kind"] == "fact" and it["owner"] in d16} == {1}
    assert {it["session"] for it in dW["corpus"] if it["kind"] == "fact" and it["owner"] in d16} == {4}
    assert dA["items_sha"] == dW["items_sha"] and dA["sha"] != dW["sha"]
    # within-session ledger order is arm-independent: events sharing a session interleave identically
    key = {it["event_ids"][0]: it["order_key"] for it in _bank_items(a4)}
    assert all(math.isclose(key[it["event_ids"][0]], it["order_key"]) for it in _bank_items(w4))
    try:
        md.build_corpus(bank, "across", 4, wB, rB, counter, BUDGET, ordering="bogus")
        raise AssertionError("unknown ordering accepted")
    except ValueError:
        pass


def test_identical_final_corpora_and_reuse():
    run = shared_run()
    bank, counter = run["bank"], run["counter"]
    for cell in ("A", "D"):
        w, r, s = md.CELLS[cell]
        for ordering in md.ORDERINGS:
            c = {(arm, k): md.build_corpus(bank, arm, k, w, r, counter, BUDGET, ordering=ordering)
                 for arm in md.ARMS for k in (1, 2, 3, 4, 5, 6)}
            sha = {k: v["sha"] for k, v in c.items()}
            isha = {k: v["items_sha"] for k, v in c.items()}
            # the memo's mechanistic fact: identical final ITEM sets at sleep 4 (and 5, 6) in both arms ...
            assert isha[("within", 4)] == isha[("across", 4)] and isha[("within", 5)] == isha[("across", 5)]
            # ... byte-identical corpora only under content ordering; chronological differs in order
            if ordering == "content":
                assert sha[("within", 4)] == sha[("across", 4)] and sha[("within", 5)] == sha[("across", 5)]
            else:
                assert sha[("within", 4)] != sha[("across", 4)] and sha[("within", 5)] != sha[("across", 5)]
            assert sha[("within", 1)] == sha[("within", 2)] == sha[("within", 3)]      # exposure-free, one fit
            assert sha[("within", 3)] != sha[("across", 3)] and isha[("within", 3)] != isha[("across", 3)]
            if w == "dedup":
                # exact dedup erases the exposure history of the facts: dose-16 and dose-4 owners
                # collapse to one piece each from sleep 1 on (dose-1 owners only arrive at sleep 4)
                fact_set = lambda k: sorted(it["context"] + it["target"] for it in  # noqa: E731
                                            c[("across", k)]["corpus"] if it["kind"] == "fact")
                assert fact_set(1) == fact_set(2) == fact_set(3) and len(fact_set(3)) == 32 and len(fact_set(4)) == 48
                assert isha[("across", 1)] != isha[("across", 2)] == isha[("across", 3)] != isha[("across", 4)]
            else:
                assert len({isha[("across", k)] for k in (1, 2, 3, 4)}) == 4
            assert sha[("across", 5)] != sha[("across", 4)] and sha[("across", 6)] != sha[("across", 5)]
    # train reuse: an identical corpus (same sha) is never fitted twice -- within sleeps 2 and 3
    d = run["dir"]
    md.set_write_root(d)
    w, r, s = md.CELLS["A"]
    c1 = md.build_corpus(bank, "within", 2, w, r, counter, BUDGET)
    c2 = md.build_corpus(bank, "within", 3, w, r, counter, BUDGET)
    assert c1["sha"] == c2["sha"]
    p1 = md.write_json(os.path.join(md.cell_dir(d, 0, "A", "within", 2), "corpus.json"), c1)
    p2 = md.write_json(os.path.join(md.cell_dir(d, 0, "A", "within", 3), "corpus.json"), c2)
    o1 = os.path.join(d, "adapters", "reuse", "within2")
    o2 = os.path.join(d, "adapters", "reuse", "within3")
    assert md.train_command(d, p1, o1, model="mock")["status"] == "trained"
    res = md.train_command(d, p2, o2, model="mock")
    assert res["status"] == "reused" and os.path.exists(os.path.join(o2, "adapter_ref.json"))
    assert os.path.realpath(md.resolve_adapter(o2)) == os.path.realpath(o1)
    # ... and the chronological within-4 / across-4 pair is NOT reused (different sha)
    c3 = md.build_corpus(bank, "across", 4, w, r, counter, BUDGET)
    c4 = md.build_corpus(bank, "within", 4, w, r, counter, BUDGET)
    p3 = md.write_json(os.path.join(md.cell_dir(d, 0, "A", "across", 4), "corpus.json"), c3)
    p4 = md.write_json(os.path.join(md.cell_dir(d, 0, "A", "within", 4), "corpus.json"), c4)
    o3 = os.path.join(d, "adapters", "reuse", "across4")
    o4 = os.path.join(d, "adapters", "reuse", "within4")
    key4 = dict(corpus_sha=c4["sha"], rank=8, epochs=3, lr=1e-4, seed=0, model="mock:guide")
    assert md.find_reusable(d, key4) is None
    assert md.train_command(d, p3, o3, model="mock")["status"] in ("trained", "reused")
    assert md.find_reusable(d, key4) is None                     # the across-4 fit does not serve within-4
    assert md.train_command(d, p4, o4, model="mock")["status"] == "trained"
    assert md.read_json(os.path.join(o4, "train_meta.json"))["ordering"] == "chronological"


def _mask(text: str) -> str:
    for c in md.COLOURS:
        text = text.replace(c, "#")
    for pair in md.ACTION_PAIRS:
        for a in pair:
            text = re.sub(r"\b" + a + r"\b", "#", text)
    return text


def test_scrambled_binding_control():
    run = shared_run()
    bank = run["bank"]
    D, S = run["corpora"]["D"], run["corpora"]["Dshuf"]
    assert S["shuffled"] is True and D["shuffled"] is False
    assert len(_bank_items(D)) == len(_bank_items(S)) == 336 + 84
    assert all(it["shuffled"] for it in _bank_items(S)) and not any(it["shuffled"] for it in _bank_items(D))
    # templates, owner ids, event ids, sessions and colour/action marginals preserved exactly
    assert sorted((_mask(it["context"]), _mask(it["target"])) for it in _bank_items(D)) == \
        sorted((_mask(it["context"]), _mask(it["target"])) for it in _bank_items(S))
    assert sorted(it["event_ids"][0] for it in _bank_items(D)) == sorted(it["event_ids"][0] for it in _bank_items(S))
    assert {it["event_ids"][0]: it["session"] for it in _bank_items(D)} == {it["event_ids"][0]: it["session"] for it in _bank_items(S)}
    assert D["stats"]["colour_marginals"] == S["stats"]["colour_marginals"]
    tgt_colour = lambda it: md._TARGET_FACT_RE.match(it["target"]).group(2)  # noqa: E731
    for c in md.COLOURS:
        assert sum(1 for it in _bank_items(S) if it["kind"] != "lesson" and tgt_colour(it) == c) == \
            sum(1 for it in _bank_items(D) if it["kind"] != "lesson" and tgt_colour(it) == c)
    # the binding leaves the loss: no dose>=4 owner keeps a consistent colour in its SUPERVISED targets,
    # observation and target agree within an event, dose-1 owners never keep the planted colour
    colour = {o["id"]: o["colour"] for o in bank["owners"]}
    dose = {o["id"]: o["dose"] for o in bank["owners"]}
    per_owner: dict = {}
    for it in _bank_items(S):
        if it["kind"] == "lesson":
            continue
        c = tgt_colour(it)
        assert f"its paint is {c}." in it["context"] and it["colour"] == c
        per_owner.setdefault(it["owner"], []).append(c)
    for oid, cols in per_owner.items():
        d = dose.get(oid, 4)          # interference owners have dose 4
        if d >= 4:
            assert sorted(cols) == sorted(md.COLOURS * (d // 4)), (oid, cols)
        else:
            assert cols == [c for c in cols if c != colour[oid]] and len(cols) == 1
    # a plain permutation of contexts would have left D and Dshuf with identical supervised targets
    assert sorted(it["target"] for it in _bank_items(D)) != sorted(it["target"] for it in _bank_items(S))
    # lessons: per (tool, mode) the pressed action is A as often as B at dose >= 4; dose 1 reversed
    by_tm: dict = {}
    for it in _bank_items(S):
        if it["kind"] == "lesson":
            m = md._TARGET_LESSON_RE.match(it["target"])
            by_tm.setdefault((m.group(1), m.group(2)), []).append(m.group(3))
            good = m.group(3)
            assert f"pressing {good} worked" in it["context"]
    les_by_tool = {L["tool"]: L for L in bank["lessons"]}
    for (tool, mode), acts in by_tm.items():
        L = les_by_tool[tool]
        if L["dose"] >= 4:
            assert acts.count(L["actions"][0]) == acts.count(L["actions"][1]) == len(acts) // 2, (tool, mode, acts)
        else:
            assert acts == [a for a in L["actions"] if a != L["mapping"][mode]]
    # deterministic per bank, arm- and sleep-independent (cumulative corpora stay prefix-consistent)
    assert md.scrambled_colours(bank) == md.scrambled_colours(bank)
    w, r, s = md.CELLS["Dshuf"]
    S5 = md.build_corpus(bank, "across", 5, w, r, run["counter"], BUDGET, shuffled=True)
    t4 = {it["event_ids"][0]: it["target"] for it in _bank_items(S)}
    t5 = {it["event_ids"][0]: it["target"] for it in _bank_items(S5)}
    assert all(t5[k] == v for k, v in t4.items())
    # the mock trainer keys strength on the supervised target text and learns a FLAT profile from it
    md.set_write_root(run["dir"])
    ad = md.train_mock(S, os.path.join(run["dir"], "adapters", "scramble_check"), profile="guide")
    d16 = [o["id"] for o in bank["owners"] if o["dose"] == 16]
    for oid in d16:
        assert len(set(ad["strength"][oid].values())) == 1 and len(ad["strength"][oid]) == 4
    adD = md.train_mock(D, os.path.join(run["dir"], "adapters", "scramble_check_D"), profile="guide")
    assert all(list(adD["strength"][oid]) == [colour[oid]] for oid in d16)
    # ... so the evaluated control shows no dose response and no lesson binding, unlike D
    _, sums_S = _pipeline(run, "Dshuf", "guide", "bank0__Dshuf__across__sleep4__r8")
    _, sums_D = _pipeline(run, "D", "guide", "bank0__D__across__sleep4__r8")
    pS, pD = sums_S[0]["per_dose"], sums_D[0]["per_dose"]
    assert abs(pS[16]["d_p"]) < 1e-9 and abs(pS[4]["d_p"]) < 1e-9 and pS[1]["d_p"] < 0 <= pD[16]["d_p"] - 0.3
    lS = sums_S[0]["lesson_per_dose"]
    assert abs(lS[16]["trigger"]) < 1e-9 and abs(lS[4]["trigger"]) < 1e-9 and lS[1]["trigger"] < 0
    assert md.interpret(sums_S[0], md.evaluate_gates(sums_S[0]))["label"] == "nothing"


def test_trainer_joint_tokenization_and_exact_cue_prefix():
    tok = _tokenizer()
    if tok is None:
        print("SKIP tokenizer not cached offline: joint-tokenization check not executed here")
        return
    run = shared_run()
    bank = run["bank"]
    events = md.ledger_items(bank, "across", 4)
    facts = [e for e in events if e["kind"] == "fact"][:6]
    lessons = [e for e in events if e["kind"] == "lesson"][:3]
    n_short_sep_differs = 0
    for ev in facts + lessons:
        for rep in md.REPRESENTATIONS:
            it = md._piece(ev, rep)
            enc = md.encode_item(tok, it)
            full = md.render_item(it) if not it["chat"] else md.render_chat(it["context"], tokenizer=tok) + it["target"] + tok.eos_token
            assert enc["input_ids"] == tok(full, add_special_tokens=False).input_ids, rep
            assert enc["n_straddle"] == 0 and not enc["truncated"]
            if it["mask_context"]:
                prefix = md.render_chat(it["context"], tokenizer=tok) if it["chat"] else it["context"]
                n_prefix = len(tok(prefix, add_special_tokens=False).input_ids)
                assert enc["labels"][:n_prefix] == [-100] * n_prefix
                assert enc["labels"][n_prefix:] == enc["input_ids"][n_prefix:]
                sup = tok.decode([x for x in enc["labels"] if x != -100])
                assert sup == it["target"] + (tok.eos_token if it["chat"] else "")
            else:
                assert enc["labels"] == enc["input_ids"]
                sep = tok(it["context"]).input_ids + tok(it["target"], add_special_tokens=False).input_ids
                n_short_sep_differs += int(sep != enc["input_ids"])
    # the old separate tokenization changed the token stream at the short header/target boundary
    assert n_short_sep_differs > 0
    # the exact training-style short cue is a token prefix of the trained short piece
    for ev in facts:
        it = md._piece(ev, "short")
        cue = tok(md.SHORT_HEADER.format(owner=ev["owner"]) + md.EXACT_COMPLETION.format(owner=ev["owner"]),
                  add_special_tokens=False).input_ids
        ids = md.encode_item(tok, it)["input_ids"]
        assert ids[:len(cue)] == cue
    # colours are single tokens in every casing/spacing variant (memo: prefer single-token answers)
    for c in md.COLOURS:
        for v in (c, c.capitalize(), " " + c, " " + c.capitalize()):
            assert len(tok(v, add_special_tokens=False).input_ids) == 1, v
    # the scorer's prompt+candidate stream is the JOINT tokenization; the only cue family whose
    # boundary straddles a token is the short text-fit probe ('A: ' + 'K7M4' -> ' K'), where the
    # straddling token counts as the candidate's first token exactly as in the trained short piece
    oid = facts[0]["owner"]
    hdr = md.SHORT_HEADER.format(owner=oid)
    tgt = md.TARGET_TMPL.format(owner=oid, colour="red")
    ids, L, straddle = md.joint_candidate_ids(tok, hdr, tgt)
    assert ids == tok(hdr + tgt, add_special_tokens=False).input_ids and straddle == 1
    assert ids[:-L] == tok(hdr.rstrip(" "), add_special_tokens=False).input_ids
    assert ids[-L:] != tok(tgt, add_special_tokens=False).input_ids          # separate tokenization differs
    assert ids == md.encode_item(tok, md._piece(facts[0], "short"))["input_ids"] or facts[0]["colour"] != "red"
    for p, c in ((md.render_chat(md.QUERY_FORMS["p1"].format(owner=oid)), "red"),
                 (hdr + md.EXACT_COMPLETION.format(owner=oid), " red"),
                 (md.render_chat("q"), "LATCH" + md.IM_END),
                 (md.render_chat("s", "With TT-5 in mode NORTH, I press"), " LATCH.")):
        ids, L, straddle = md.joint_candidate_ids(tok, p, c)
        assert straddle == 0 and ids == tok(p, add_special_tokens=False).input_ids + tok(c, add_special_tokens=False).input_ids
        assert L == len(tok(c, add_special_tokens=False).input_ids)
    # action strings are multi-token -> scored as complete strings with a terminator; the recorded
    # candidate token counts equal the exact joint count for every cue (prompt-tail cache is safe)
    dist = md.read_json(os.path.join(run["dir"], "distractor.json"))["text"]
    cues = md.build_cues(bank, dist, tokenizer=tok)
    les = [c for c in cues if c["kind"] == "lesson_trigger"]
    assert any(n > 2 for c in les for ns in c["cand_tokens"].values() for n in ns)
    n_straddle = 0
    for c in cues[::7] + les:
        for a, ns in c["cand_tokens"].items():
            exact = [md.joint_candidate_ids(tok, c["prompt"], v) for v in c["candidates"][a]]
            assert ns == [L for _, L, _ in exact], (c["cue_id"], a)
            n_straddle += sum(st for _, _, st in exact)
            if c["kind"] != "textfit_short":
                assert all(st == 0 for _, _, st in exact), c["cue_id"]
    assert n_straddle > 0
    # truncation keeps the tail (the supervised target)
    it = md._piece(facts[0], "antecedent")
    enc = md.encode_item(tok, it, max_len=12)
    assert enc["truncated"] and len(enc["input_ids"]) == 12 and enc["labels"][-1] == enc["input_ids"][-1]


def test_evaluator_arithmetic_toy():
    row = dict(a="blue", OFF=dict(p_raw=dict(red=0.30, blue=0.20, green=0.10, white=0.05), mass=0.65),
               ON=dict(p_raw=dict(red=0.15, blue=0.50, green=0.05, white=0.05), mass=0.75))
    m = md.cue_metrics(row)
    assert m["b"] == "red"                                     # strongest alternative under OFF
    assert math.isclose(m["OFF"]["p_norm"], 0.20 / 0.65) and math.isclose(m["ON"]["p_norm"], 0.50 / 0.75)
    assert math.isclose(m["OFF"]["logodds"], math.log(0.20 / 0.30))
    assert math.isclose(m["ON"]["logodds"], math.log(0.50 / 0.15))
    assert math.isclose(m["d_logodds"], math.log(0.50 / 0.15) - math.log(0.20 / 0.30))
    assert math.isclose(m["d_mass"], 0.10) and math.isclose(m["d_p_raw"], 0.30)
    ctrl = dict(a="blue", OFF=dict(p_raw=dict(red=0.30, blue=0.20, green=0.10, white=0.05), mass=0.65),
                ON=dict(p_raw=dict(red=0.28, blue=0.22, green=0.10, white=0.05), mass=0.65))
    m2 = md.cue_metrics(ctrl, a="blue", b="red")
    I_d = m["d_logodds"] - m2["d_logodds"]
    assert math.isclose(I_d, (math.log(0.5 / 0.15) - math.log(0.2 / 0.3)) - (math.log(0.22 / 0.28) - math.log(0.2 / 0.3)))
    cset = md.colour_candidates(False)
    lps = [math.log(0.1)] * 8
    cp = md.colour_probs(cset, lps)
    assert math.isclose(cp["p_raw"]["red"], 0.2) and math.isclose(cp["mass"], 0.8) and math.isclose(cp["p_norm"]["blue"], 0.25)
    assert math.isclose(cp["logp"]["red"], math.log(0.2))
    # text-fit gain: per-token log-likelihood gain of the planted rendering, using the stored logp
    tf = dict(a="red", cand_tokens=dict(red=[8]),
              OFF=dict(p_raw=dict(red=0.0, blue=0.0, green=0.0, white=0.0), mass=0.0, logp=dict(red=-16.0)),
              ON=dict(p_raw=dict(red=0.0, blue=0.0, green=0.0, white=0.0), mass=0.0, logp=dict(red=-8.0)))
    gain, nll_off = md._textfit_gain(tf, "red", 8)
    assert math.isclose(gain, 1.0) and math.isclose(nll_off, 2.0)
    # canonical answer keys: terminators stripped, sentence -> last word
    assert md._canon("LATCH<|im_end|>") == "latch" and md._canon(" Latch.") == "latch"
    assert md._canon("K7M4's car is red.") == "red" and md._canon("K7M4's car is red.<|im_end|>") == "red"
    ac = md.action_candidates("LATCH", "VENT", completion=False)
    assert ac["LATCH"] == ["LATCH<|im_end|>", "Latch<|im_end|>", "latch<|im_end|>"]
    assert md.action_candidates("LATCH", "VENT", completion=True)["VENT"] == [" VENT.", " Vent.", " vent."]
    assert md.prior_bin_labels([0.15, 0.35, 0.55]) == ["<0.15", "0.15-0.35", "0.35-0.55", ">=0.55"]
    assert md.prior_bin_label(0.1) == "<0.15" and md.prior_bin_label(0.35) == "0.35-0.55" and md.prior_bin_label(0.9) == ">=0.55"


def test_gates_and_interpretation_four_profiles():
    run = shared_run()
    labels = {}
    sums_by_profile = {}
    for profile in ("guide", "habit", "nothing", "surface"):
        evs, sums = _pipeline(run, "D", profile, f"bank0__D__across__sleep4__r8__{profile}")
        s = sums[0]
        sums_by_profile[profile] = s
        g = md.evaluate_gates(s)
        labels[profile] = md.interpret(s, g)["label"]
        if profile == "guide":
            d16 = s["per_dose"][16]
            assert d16["p_on"] >= 0.80 and d16["d_p"] >= 0.30 and d16["term1"] >= 1.5, d16
            assert g["G4_I_d_ci"]["lo"] > 0 and g["G5_unrelated"]["passed"] and g["G6_in_context"]["passed"]
            assert g["G6_repaint"]["passed"], g["G6_repaint"]
            assert g["G8_dose_trend"]["passed"], g["G8_dose_trend"]
            assert g["G9_mass"]["passed"] and g["G9_mass"]["min_owner"] is not None, g["G9_mass"]
            assert s["per_dose"][0]["abs_d_p"] < 1e-9                    # unexposed owners untouched
            assert s["controls"]["swapped_d_p"] <= 1e-9                  # owner colour does not bleed onto the partner's cue
            assert s["controls"]["swapped_d_logodds"] < 0                # partner's own learning dominates the log-odds
            assert s["per_dose"][16]["d_p"] > s["per_dose"][4]["d_p"] > s["per_dose"][1]["d_p"] > 0
            # raw P and mass are carried alongside normalized P
            assert 0 < d16["p_raw_on"] <= d16["mass_on"] <= 1 and d16["p_raw_on"] > d16["p_raw_off"]
            # training-text fit: exposed owners' training text fits better ON; unexposed unchanged
            assert d16["textfit_short_gain"] > 0 and d16["textfit_ante_gain"] > 0
            assert abs(s["per_dose"][0]["textfit_short_gain"]) < 1e-9
            # OFF-prior bins: pre-registered labels, dose-16 owners fully partitioned
            bins = s["by_prior_bin"]["dose16"]
            assert list(bins) == md.prior_bin_labels(md.PRIOR_BIN_EDGES) and sum(b["n"] for b in bins.values()) == 16
            assert sum(b["n"] for b in s["by_prior_bin"]["exposed"].values()) == 48
            assert all(len(b["values"]["I_d"]) == b["n"] for b in bins.values())
            # G2: natural subset or the base-rate fallback, never silently n/a when a subset exists
            assert g["G2_prior_subset"]["subset"] in ("natural", "base_rate", None)
            if g["G2_prior_subset"]["subset"] == "base_rate":
                assert "fallback" in g["G2_prior_subset"]["note"] and g["G2_prior_subset"]["n"] >= 4
        if profile == "habit":
            assert s["controls"]["similar_abs_d_p"] > 0.03
        if profile == "nothing":
            assert all(abs(s["per_dose"][d]["d_p"]) < 1e-9 for d in md.DOSES)
            assert all(abs(s["per_dose"][d]["textfit_short_gain"]) < 1e-9 for d in md.DOSES)
    assert labels == dict(guide="guide", habit="rewrite-habit", nothing="nothing", surface="surface-binding-only"), labels
    # dedup flattens dose under the same mock (the count never reaches the loss)
    _, sums_c = _pipeline(run, "C", "guide", "bank0__C__across__sleep4__r8")
    pc = sums_c[0]["per_dose"]
    assert abs(pc[16]["d_p"] - pc[1]["d_p"]) < 0.05 and pc[16]["d_p"] > 0.1
    # --- candidate-mass gate: a collapsed mass withholds 'guide' ---
    s = copy.deepcopy(sums_by_profile["guide"])
    s["per_dose"][16]["mass_on"] = 0.2 * s["per_dose"][16]["mass_off"]
    g = md.evaluate_gates(s)
    assert g["G9_mass"]["passed"] is False and "G9_mass" in g["failed"]
    it = md.interpret(s, g)
    assert it["label"] == "mass-collapse" and it["mass_ok"] is False and "collapsed" in it["reasons"][0]
    s["per_dose"][16]["mass_on"] = 0.6 * s["per_dose"][16]["mass_off"]
    assert md.evaluate_gates(s)["G9_mass"]["passed"] is (0.6 * s["per_dose"][16]["mass_off"] >= md.GATES["mass_floor"])
    # --- G2 fallback: natural subset too small -> base-rate subset, accepted only inside the window ---
    s = copy.deepcopy(sums_by_profile["guide"])
    s["prior_subset"] = dict(n=1, p_on=0.99, p_off=0.6)
    s["base_rate_subset"] = dict(n=6, p_on=0.90, p_off=0.60, names_base_colour=True)
    g2 = md.evaluate_gates(s)["G2_prior_subset"]
    assert g2["subset"] == "base_rate" and g2["passed"] is True and "inside" in g2["note"]
    s["base_rate_subset"]["p_on"] = 0.70
    assert md.evaluate_gates(s)["G2_prior_subset"]["passed"] is False
    s["base_rate_subset"]["p_off"] = 0.30
    g2 = md.evaluate_gates(s)["G2_prior_subset"]
    assert g2["passed"] is None and "OUTSIDE" in g2["note"] and "not a literal" in g2["note"]
    s["prior_subset"] = dict(n=5, p_on=0.70, p_off=0.6)
    g2 = md.evaluate_gates(s)["G2_prior_subset"]
    assert g2["subset"] == "natural" and g2["passed"] is False
    s["prior_subset"], s["base_rate_subset"] = dict(n=0, p_on=None, p_off=None), dict(n=0, p_on=None, p_off=None)
    assert md.evaluate_gates(s)["G2_prior_subset"]["passed"] is None
    # --- storage-without-extraction flag: large text-fit gain with no paraphrase gain ---
    s = copy.deepcopy(sums_by_profile["nothing"])
    s["per_dose"][16]["textfit_ante_gain"] = 1.2
    it = md.interpret(s, md.evaluate_gates(s))
    assert it["label"] == "nothing" and any("storage-without-extraction" in r for r in it["reasons"])
    # --- swapped dP as the habit signal ---
    s = copy.deepcopy(sums_by_profile["guide"])
    s["controls"]["swapped_d_p"] = 0.10
    it = md.interpret(s, md.evaluate_gates(s))
    assert it["label"] == "rewrite-habit" and any("partner" in r for r in it["reasons"])


def test_paired_bootstrap():
    b = md.paired_bootstrap([0.5] * 16, seed=1)
    assert b["lo"] > 0 and math.isclose(b["mean"], 0.5) and b["n"] == 16
    sym = [(-1) ** i * 0.3 for i in range(16)]
    b2 = md.paired_bootstrap(sym, seed=1)
    assert b2["lo"] < 0 < b2["hi"]
    assert md.paired_bootstrap(sym, seed=3) == md.paired_bootstrap(sym, seed=3)
    assert md.paired_bootstrap([])["n"] == 0


def test_lambda_sweep_zero_is_off_and_monotone():
    run = shared_run()
    evs, sums = _pipeline(run, "D", "guide", "bank0__D__across__sleep4__r8__sweep", lambdas=[0.0, 0.5, 1.0])
    by_lam = {ev["lam"]: ev for ev in evs}
    for c in by_lam[0.0]["cues"]:
        assert c["ON"]["p_raw"] == c["OFF"]["p_raw"] and c["ON"]["mass"] == c["OFF"]["mass"]
        assert c["ON"]["logp"] == c["OFF"]["logp"] and "cand_tokens" in c
    dp = [s["per_dose"][16]["d_p"] for s in sums]
    assert dp[0] == 0 and dp[0] < dp[1] < dp[2]
    assert [s["lam"] for s in sums] == [0.0, 0.5, 1.0]
    assert by_lam[1.0]["adapter_meta"]["ordering"] == "chronological" and by_lam[1.0]["adapter_meta"]["corpus_sha"]


def test_lessons_conditional_selectivity():
    run = shared_run()
    evs, sums = _pipeline(run, "D", "guide", "bank0__D__across__sleep4__r8__lessons")
    lpd = sums[0]["lesson_per_dose"]
    for d in (4, 16):
        assert lpd[d]["trigger"] > 1.0 and lpd[d]["reversed"] < -1.0 and abs(lpd[d]["notrigger"]) < 1e-9, lpd[d]
        assert lpd[d]["interaction"] > 1.0 and lpd[d]["selectivity"] > 2.0
    assert lpd[0]["trigger"] == 0 and lpd[16]["trigger"] > lpd[1]["trigger"]
    rows = [c for c in evs[0]["cues"] if c["kind"].startswith("lesson_")]
    assert rows and all(set(c["cand_tokens"]) == {c["a"], c["b"]} for c in rows)


def test_nothing_written_outside_run_dir_and_synthetic_flags():
    d = _run_dir("contained")
    written = []
    real_open = builtins.open

    def spy(path, mode="r", *a, **k):
        if any(ch in str(mode) for ch in "wax+"):
            written.append(os.path.realpath(str(path)))
        return real_open(path, mode, *a, **k)

    builtins.open = spy
    try:
        md.main(["generate", "--run-dir", d, "--seed", "3", "--model", "mock", "--token-budget", str(BUDGET),
                 "--distractor-tokens", "200"])
        md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "D", "--arm", "across", "--sleep", "4"])
        md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "A", "--arm", "across", "--sleep", "4"])
        md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "A", "--arm", "within", "--sleep", "4"])
        for cell, arm in (("A", "across"), ("D", "across"), ("A", "within")):
            cp = os.path.join(md.cell_dir(d, 0, cell, arm, 4), "corpus.json")
            ad = os.path.join(d, "adapters", "bank0", cell, arm, "sleep4", "r8")
            md.main(["train", "--run-dir", d, "--corpus", cp, "--out", ad, "--model", "mock"])
            md.main(["evaluate", "--run-dir", d, "--bank", "0", "--adapter", ad, "--model", "mock",
                     "--tag", f"bank0__{cell}__{arm}__sleep4__r8", "--lambdas", "1"])
        md.main(["report", "--run-dir", d])
        with real_open(os.path.join(d, "report", "summary.md")) as f:
            summ = f.read()
        assert "Corpus identity check" not in summ            # corpora/index.json not produced yet
        assert "## Exposure arms at sleep 4" in summ and "same corpus sha" in summ
        # a PEFT-style adapter README.md gets the synthetic header
        stub = os.path.join(d, "adapters", "stub_peft")
        os.makedirs(stub)
        with real_open(os.path.join(stub, "README.md"), "w") as f:
            f.write("---\nlibrary_name: peft\n---\n# model card\n")
        assert md._mark_adapter_dir(stub) == [os.path.join(stub, "README.md")]
        assert md._mark_adapter_dir(stub) == []               # idempotent
        # corpus-all writes the identity check; the report then shows items identical, sha not
        md.main(["corpus-all", "--run-dir", d, "--cells", "A", "--sleeps", "4"])
        md.main(["report", "--run-dir", d])
    finally:
        builtins.open = real_open
    root = os.path.realpath(d)
    outside = [p for p in written if not p.startswith(root + os.sep)]
    assert written and not outside, outside
    n_json = n_text = 0
    for dp, _, files in os.walk(d):
        for f in files:
            p = os.path.join(dp, f)
            if f.endswith(".json"):
                j = json.load(open(p))
                assert j.get("synthetic") is True, p
                n_json += 1
            elif f.endswith((".md", ".txt")):
                assert open(p).readline().rstrip("\n") == md.SYNTHETIC_HEADER, p
                n_text += 1
    assert n_json >= 12 and n_text >= 4
    rep = md.read_json(os.path.join(d, "report", "report.json"))
    assert rep["finalist"]["cell"] == "D"                          # occurrences x antecedent wins under the mock
    assert rep["orderings"] == ["chronological"] and rep["prior_match"] is False
    assert rep["exposure_arms_sleep4"] and rep["exposure_arms_sleep4"][0][0] == "A" and rep["exposure_arms_sleep4"][0][-1] is False
    md_text = open(os.path.join(d, "report", "D__across__r8__lam1.md")).read()
    for needle in ("## Gates", "## Interpretation: **guide**", "I_d [95% CI]", "term1 (nats)", "## Conditional lessons",
                   "P raw OFF/ON", "## By pre-registered OFF-prior bin", "## Training-text fit vs I_d", "G9_mass",
                   "corpus ordering: **chronological**", "names the base colour", "G2 evaluated on:",
                   "random balanced, after the OFF measurement", "swapped dP (owner colour at partner cue)"):
        assert needle in md_text, needle
    assert "shuffled" not in rep["finalist"]["representation"]
    idx = md.read_json(os.path.join(d, "corpora", "index.json"))
    assert idx["ordering"] == "chronological" and idx["over_budget"] == []
    assert all(i["identical_items"] and not i["identical_sha"] for i in idx["identity_check"]) and len(idx["identity_check"]) == 3
    with open(os.path.join(d, "report", "summary.md")) as f:
        summ = f.read()
    assert "## Corpus identity check" in summ and "identical items" in summ and "identical sha" in summ
    # the write guard itself
    md.set_write_root(d)
    try:
        md.write_json(os.path.join(SCRATCH, "escape.json"), {})
        raise AssertionError("write outside the run dir was not refused")
    except PermissionError:
        pass


def test_lora_config_mirrors_train_adapter():
    src = open(os.path.join(ROOT, "organism_v6", "train_adapter.py")).read()
    m = re.search(r"target_modules=\[([^\]]+)\]", src, re.S)
    targets = re.findall(r'"(\w+)"', m.group(1))
    assert targets == md.LORA_TARGETS
    assert re.search(r"lora_dropout=0\.05", src) and md.LORA_DROPOUT == 0.05
    assert re.search(r"lora_alpha=2 \* args\.rank", src) and md.LORA_ALPHA_MULT == 2
    assert re.search(r'"--lr", type=float, default=1e-4', src) and md.TRAIN_LR == 1e-4
    assert re.search(r'"--epochs", type=int, default=3', src) and md.TRAIN_EPOCHS == 3
    assert re.search(r"bsz, total_tokens, steps = 4", src) and md.TRAIN_BSZ == 4
    assert re.search(r"max_length=512", src) and md.TRAIN_MAX_LEN == 512
    assert md.LORA_RANK == 8 and md.LAMBDAS == [0.0, 0.25, 0.5, 1.0]
    # today's trainer tokenizes each piece as ONE string and trains in corpus order without a shuffle
    assert re.search(r"tok\(corpus\[i:i \+ bsz\]", src) and "shuffle" not in src
    # the fallback chat template is the deployed Qwen2.5 single-turn render
    p = md.render_chat("hi", "K7M4's car is")
    assert p == ("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n"
                 "<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\nK7M4's car is")


def test_cues_never_leak_the_answer_and_cover_the_design():
    run = shared_run()
    dist = md.read_json(os.path.join(run["dir"], "distractor.json"))["text"]
    cues = md.build_cues(run["bank"], dist)
    kinds = {}
    for c in cues:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    assert kinds["fact"] == 64 * 3 and kinds["incontext"] == 64 * 3 and kinds["adjacent"] == 16 * 3
    assert kinds["repaint"] == kinds["similar"] == 48 * 3 and kinds["bicycle"] == 48
    assert "swapped" not in kinds                      # derived from the partner's fact rows, not re-scored
    assert kinds["exact_short"] == kinds["exact_ante"] == kinds["base_rate"] == 64 and kinds["generic"] == 1
    assert kinds["textfit_short"] == kinds["textfit_ante"] == 64
    assert all(kinds[f"lesson_{k}"] == 16 for k in ("trigger", "notrigger", "reversed", "exact"))
    col = {o["id"]: o["colour"] for o in run["bank"]["owners"]}
    base = run["bank"]["base_colour"]
    for c in cues:
        assert "cand_tokens" in c and set(c["cand_tokens"]) == set(c["candidates"])
        if c["kind"] in ("fact", "similar", "bicycle", "exact_short", "exact_ante"):
            q = c["prompt"].split("<|im_start|>user\n")[-1]
            assert col[c["owner"]] not in q.lower().replace("colour", ""), c["cue_id"]
        if c["kind"] == "base_rate":
            # documented exception: the fleet base-rate prompt NAMES the base colour by design (memo fallback)
            q = c["prompt"].split("<|im_start|>user\n")[-1].lower().replace("colour", "")
            assert c["names_base_colour"] and base in q
            if col[c["owner"]] != base:
                assert col[c["owner"]] not in q
        if c["kind"] == "incontext":
            assert dist in c["prompt"] and c["prompt"].index("Verified observation") < c["prompt"].index(dist)
        if c["kind"] == "repaint":
            assert c["a"] != c["old_colour"] and "repainted" in c["prompt"]
        if c["kind"].startswith("lesson_") and c["kind"] != "lesson_exact":
            assert c["prompt"].endswith("only:<|im_end|>\n<|im_start|>assistant\n")   # ends right before the action
            assert all(v.endswith(md.IM_END) for vs in c["candidates"].values() for v in vs)
        if c["kind"] == "lesson_exact":
            assert all(v.startswith(" ") and v.endswith(".") for vs in c["candidates"].values() for v in vs)
        if c["kind"].startswith("textfit_"):
            # the training text itself: observation with the colour (antecedent) / bare header (short)
            assert set(c["candidates"]) == set(md.COLOURS) and c["context"] == "training_text"
            if c["kind"] == "textfit_ante":
                assert f"its paint is {col[c['owner']]}." in c["prompt"]
                assert all(v.endswith(md.IM_END) for vs in c["candidates"].values() for v in vs)
            else:
                assert c["prompt"] == md.SHORT_HEADER.format(owner=c["owner"])
    assert not any(w in dist.lower() for w in md.COLOURS + ["car"])


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    if not os.environ.get("MEMORY_DOSE_TEST_DIR"):
        shutil.rmtree(SCRATCH, ignore_errors=True)
    sys.exit(1 if failed else 0)
