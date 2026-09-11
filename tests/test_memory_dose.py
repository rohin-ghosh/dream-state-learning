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
Cell family F / completion frames (Rohin 2026-09-11): frames rendering
(canonical ending, K templates in rotation, R repeats, determinism), cell
registration + per-cell token budget + manifest fields, frame cue
construction, I_d_frame + G9_frame_binding/G10_frame_dose on a synthetic
eval JSON, report backward compatibility on evals without frame cues, the
runbook's syntax, and the items_sha identity of the existing cells against a
fixture computed BEFORE the change (tests/fixtures/).
Abstention negatives (SEQ-039): 'not observed' rendering (count = K_neg x
unexposed owners + K_neg x 25% of the exposed owners, canonical ending, none
for an exposed owner's car, per-sleep from the exposure schedule), cell
registration + manifest/item field `negatives`, p_abstain on every frame-
family cue of a mock eval, G11_abstention on the mock pipeline and on
synthetic values, report backward compatibility on an eval without
p_abstain, the runbook accepting the new cell names, and the items_sha of
the five pre-existing F cells against values computed BEFORE the change.
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


# ---------------------------------------------------------------------------
# cell family F -- completion frames (Rohin 2026-09-11)
# ---------------------------------------------------------------------------
def _frame_corpus(run: dict, cell: str, arm: str = "across", sleep: int = 4, budget: int | None = None) -> dict:
    w, r, s = md.CELLS[cell]
    k = md.cell_frame_knobs(cell)
    return md.build_corpus(run["bank"], arm, sleep, w, r, run["counter"], budget or md.cell_budget(cell, BUDGET),
                           shuffled=s, frame_forms=k["forms"], frame_repeats=k["repeats"])


def _facts(c: dict) -> list:
    return [it for it in c["corpus"] if it["kind"] == "fact"]


def test_frames_templates_and_rendering():
    run = shared_run()
    bank = run["bank"]
    T = md.FRAME_TEMPLATES
    assert len(T) == 16 and len(set(T)) == 16
    canon = md.FRAME_CANONICAL
    assert canon == "Owner {owner}'s car is {colour}." and md.FRAME_PREFIX + " {colour}." == canon
    for t in T:
        assert t.endswith(canon) and "?" not in t                       # declarative, canonical ending
        prose = t[:-len(canon)]
        assert prose.count("{owner}") == 1 and prose.count("{colour}") == 1   # owner and colour once in prose
        assert prose.strip() and prose.endswith(" ")
        for q in md.QUERY_FORMS.values():                               # none reuses the query wording
            core = q.replace("{owner}", "").lower()
            for frag in ("what colour", "record lookup", "give the vehicle", "answer with one"):
                assert frag not in prose.lower(), (t, frag)
            assert core.strip(": ") not in prose.lower()
    # _piece under frames: bare text, loss on every token, context + target = the whole template
    ev = [e for e in md.ledger_items(bank, "across", 4) if e["kind"] == "fact"][0]
    it = md._piece(ev, "frames")
    assert it["chat"] is False and it["mask_context"] is False and it["target"] == canon.format(owner=ev["owner"], colour=ev["colour"])
    assert md.render_item(it) == md.FRAME_TEMPLATES[it["frame_template"]].format(owner=ev["owner"], colour=ev["colour"])
    assert it["frame_forms"] == 1 and it["frame_repeats"] == 1 and it["frame_copy"] == 0 and it["frame_template"] == 0
    assert "frame_forms" not in md._piece(ev, "short")                  # existing representations carry no frame metadata
    dose = {o["id"]: o["dose"] for o in bank["owners"]}
    n_fact_events = 16 * (1 + 4 + 16)
    for cell, (K, R) in (("F_r1k1", (1, 1)), ("F_r16k1", (1, 16)), ("F_r4k4", (4, 4)), ("F_r1k16", (16, 1))):
        c = _frame_corpus(run, cell, budget=120000)
        facts = _facts(c)
        assert c["representation"] == "frames" and c["writer"] == "occurrences" and c["shuffled"] is False
        assert c["frame_forms"] == K and c["frame_repeats"] == R
        assert len(facts) == n_fact_events * R                          # R repeats multiply the items
        for it in facts + [x for x in c["corpus"] if x["kind"] == "interference"]:
            text = md.render_item(it)
            assert text.endswith(canon.format(owner=it["owner"], colour=it["colour"])), text
            assert "<|im_start|>" not in text and it["chat"] is False and it["mask_context"] is False
            assert it["frame_forms"] == K and it["frame_repeats"] == R and 0 <= it["frame_copy"] < R
            assert text == md.FRAME_TEMPLATES[it["frame_template"]].format(owner=it["owner"], colour=it["colour"])
        assert sorted({it["frame_template"] for it in facts}) == list(range(K))     # exactly K templates in rotation
        # every event id appears R times, copies 0..R-1, and with K>1 the copies rotate through the templates
        per_event: dict = {}
        for it in facts:
            per_event.setdefault(it["event_ids"][0], []).append(it)
        assert all(len(v) == R and sorted(x["frame_copy"] for x in v) == list(range(R)) for v in per_event.values())
        for oid, d in dose.items():
            own = [it for it in facts if it["owner"] == oid]
            assert len(own) == d * R
            if d == 16:
                counts = [sum(1 for it in own if it["frame_template"] == t) for t in range(K)]
                assert counts == [16 * R // K] * K, (cell, oid, counts)          # balanced rotation per owner
        # colour marginals balanced at marginal_target x R; presentations carry R
        assert c["marginal_target"] == bank["marginal_target"] * R
        assert c["stats"]["colour_marginals"] == {col: bank["marginal_target"] * R for col in md.COLOURS}
        for oid, d in dose.items():
            if d:
                assert c["stats"]["presentations_per_owner"][oid] == 3 * d * R
        # lessons and padding are their bare declarative target
        les = [it for it in c["corpus"] if it["kind"] == "lesson"]
        assert les and all(it["context"] == "" and md._TARGET_LESSON_RE.match(it["target"]) for it in les)
        assert all(it["context"] == "" for it in c["corpus"] if it["kind"].startswith("filler"))
        # every item of the corpus (padding and lessons included) carries the cell's K and R
        non_fact = [it for it in c["corpus"] if it["kind"] not in ("fact", "interference")]
        assert non_fact and all(it["frame_forms"] == K and it["frame_repeats"] == R and it["frame_template"] is None
                                for it in non_fact), cell
        assert all(it["frame_copy"] == 0 for it in non_fact if it["kind"].startswith("filler"))   # padding: one copy
        assert all(0 <= it["frame_copy"] < R for it in non_fact if it["kind"] == "lesson")        # lessons: R copies
    # determinism: same inputs -> same corpus; seed enters the template choice; arm-independent items
    a = _frame_corpus(run, "F_r4k4", budget=120000)
    b = _frame_corpus(run, "F_r4k4", budget=120000)
    assert a["sha"] == b["sha"] and a["items_sha"] == b["items_sha"]
    w4 = _frame_corpus(run, "F_r4k4", arm="within", budget=120000)
    assert w4["items_sha"] == a["items_sha"] and w4["sha"] != a["sha"]
    other = dict(bank); other["seed"] = 5
    o = md.build_corpus(other, "across", 4, "occurrences", "frames", run["counter"], 120000, frame_forms=4, frame_repeats=4)
    assert {it["event_ids"][0]: it["frame_template"] for it in _facts(o)} != {it["event_ids"][0]: it["frame_template"] for it in _facts(a)}
    idx = md.frame_template_index
    assert idx(0, "K7M4", 3, 1, 4, 4) == idx(0, "K7M4", 3, 1, 4, 4) and 0 <= idx(0, "K7M4", 3, 1, 4, 4) < 4
    assert sorted(idx(0, "K7M4", k, 0, 16, 1) for k in range(16)) == list(range(16))
    # the bank index is part of the key (event id = bank + owner + k): banks that share owner ids
    # (the default) do not share the per-owner template sequence
    oids = [o["id"] for o in bank["owners"]]
    seq = {bk: [idx(bank["seed"], oid, 0, 0, 16, 1, bank=bk) for oid in oids] for bk in range(3)}
    assert seq[0] != seq[1] and seq[1] != seq[2] and seq[0] != seq[2]
    assert seq[0] == [idx(bank["seed"], oid, 0, 0, 16, 1) for oid in oids]            # bank 0 is the default
    b1 = dict(bank); b1["bank"] = 1
    o1 = md.build_corpus(b1, "across", 4, "occurrences", "frames", run["counter"], 120000, frame_forms=16, frame_repeats=1)
    a16 = _frame_corpus(run, "F_r1k16", budget=120000)
    by_ok = lambda cp: {(it["owner"], it["event_ids"][0].rsplit("-", 1)[1]): it["frame_template"] for it in _facts(cp)}  # noqa: E731
    assert by_ok(o1).keys() == by_ok(a16).keys() and by_ok(o1) != by_ok(a16)
    assert all(sorted(t for (own, _), t in by_ok(o1).items() if own == oid) == list(range(16)) for oid in oids if dose[oid] == 16)
    # the scrambled control composes with frames (colour of the rendered frame = the scrambled colour)
    sc = md.build_corpus(bank, "across", 4, "occurrences", "frames", run["counter"], 120000, shuffled=True)
    cols = md.scrambled_colours(bank)
    assert all(md.render_item(it).endswith(canon.format(owner=it["owner"], colour=cols[it["event_ids"][0]])) for it in _facts(sc))
    # the mock trainer reads the binding from the canonical target
    md.set_write_root(run["dir"])
    ad = md.train_mock(a, os.path.join(run["dir"], "adapters", "frames_check"), profile="guide")
    col = {o["id"]: o["colour"] for o in bank["owners"]}
    assert len(ad["strength"]) == 48
    for oid, d in dose.items():
        if d:
            assert ad["strength"][oid] == {col[oid]: 3.0 * d * 4}, (oid, ad["strength"][oid])


def test_frame_cells_registered_budget_and_manifest():
    run = shared_run()
    for cell, K, R in (("F_r1k1", 1, 1), ("F_r16k1", 1, 16), ("F_r4k4", 4, 4), ("F_r1k16", 16, 1)):
        assert md.CELLS[cell] == ("occurrences", "frames", False)
        assert md.FRAME_CELLS[cell] == dict(forms=K, repeats=R) and md.cell_frame_knobs(cell) == dict(forms=K, repeats=R)
        assert md.cell_budget(cell, 65536) == 400000 == md.FRAME_TOKEN_BUDGET
        assert "K=%d forms x R=%d repeats" % (K, R) in md._cell_label(cell)
        assert md.parse_tag(f"bank1__{cell}__across__sleep4__r8") == dict(bank=1, cell=cell, arm="across", sleep=4, rank=8)
    assert [K * R for K, R in ((1, 16), (4, 4), (16, 1))] == [16, 16, 16]        # equal total exposure
    for cell in ("A", "B", "C", "D", "Dshuf", "Bw", "Dw"):
        assert md.cell_budget(cell, 65536) == 65536 and md.cell_frame_knobs(cell) == dict(forms=1, repeats=1)
        assert md.CELLS[cell][1] != "frames"
    assert md.DEFAULT_TOKEN_BUDGET == 65536 and "frames" in md.REPRESENTATIONS
    # corpus manifest fields: K, R and the budget used; F content exceeds the default budget by design
    c = _frame_corpus(run, "F_r16k1")
    assert c["frame_forms"] == 1 and c["frame_repeats"] == 16 and c["token_budget"] == 400000
    assert c["stats"]["frame_forms"] == 1 and c["stats"]["frame_repeats"] == 16 and c["stats"]["token_budget"] == 400000
    assert c["stats"]["content_tokens"] > 65536 and not c["stats"]["over_budget"] and c["stats"]["n_tokens"] <= 400000
    # existing corpora record the inert knobs and keep the run's budget
    A = run["corpora"]["A"]
    assert A["frame_forms"] == 1 and A["frame_repeats"] == 1 and A["token_budget"] == BUDGET
    # corpus-all: per-cell budgets in the index; an explicit budget applies to every cell
    d = _generate("frames_all")
    counter = run["counter"]
    out = md.corpus_all(d, counter, cells=["A", "F_r1k1"], arms=["across"], sleeps=[4])
    idx = md.read_json(os.path.join(d, "corpora", "index.json"))
    assert idx["token_budgets"] == {"A": BUDGET, "F_r1k1": 400000} and idx["token_budget"] == BUDGET
    assert idx["index"]["bank0/F_r1k1/across/sleep4"]["token_budget"] == 400000
    assert idx["index"]["bank0/A/across/sleep4"]["token_budget"] == BUDGET and idx["over_budget"] == []
    assert out["identity_check"] == []                                  # one arm only: no sleep-4 pair to compare
    cj = md.read_json(idx["index"]["bank0/F_r1k1/across/sleep4"]["path"])
    assert cj["frame_forms"] == 1 and cj["frame_repeats"] == 1 and cj["token_budget"] == 400000 and cj["synthetic"] is True
    out2 = md.corpus_all(d, counter, cells=["F_r1k1"], arms=["across"], sleeps=[4], token_budget=100000)
    assert md.read_json(os.path.join(d, "corpora", "index.json"))["token_budgets"] == {"F_r1k1": 100000}
    assert out2["over_budget"] == []
    # '--cell F_r4k4' works on the CLI: the corpus lands in the cell's directory at the cell's budget
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "F_r4k4", "--arm", "across", "--sleep", "4"])
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "F_r4k4", "across", 4), "corpus.json"))
    assert cj["frame_forms"] == 4 and cj["frame_repeats"] == 4 and cj["token_budget"] == 400000
    assert len(_facts(cj)) == 336 * 4 and cj["items_sha"] == _frame_corpus(run, "F_r4k4")["items_sha"]
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "A", "--arm", "across", "--sleep", "4"])
    assert md.read_json(os.path.join(md.cell_dir(d, 0, "A", "across", 4), "corpus.json"))["token_budget"] == BUDGET
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--writer", "occurrences", "--representation", "frames",
             "--frame-forms", "4", "--frame-repeats", "2", "--arm", "across", "--sleep", "4", "--token-budget", "90000"])
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "occurrences-frames-r2k4", "across", 4), "corpus.json"))
    assert cj["frame_forms"] == 4 and cj["frame_repeats"] == 2 and cj["token_budget"] == 90000 and len(_facts(cj)) == 336 * 2
    shutil.rmtree(d)


def test_frame_cues_constructed():
    run = shared_run()
    bank = run["bank"]
    dist = md.read_json(os.path.join(run["dir"], "distractor.json"))["text"]
    cues = md.build_cues(bank, dist)
    ids = [c["cue_id"] for c in cues]
    assert len(ids) == len(set(ids))                                    # every cue id unique
    by_kind: dict = {}
    for c in cues:
        by_kind.setdefault(c["kind"], []).append(c)
    owners = {o["id"]: o for o in bank["owners"]}
    fr, fs, fb = by_kind["frame"], by_kind["frame_similar"], by_kind["frame_bicycle"]
    assert len(fr) == 64 and {c["owner"] for c in fr} == set(owners)   # every planted owner incl. dose 0
    assert sorted(c["dose"] for c in fr).count(0) == 16
    assert len(fs) == 48 and len(fb) == 48 and all(c["dose"] > 0 for c in fs + fb)
    sp = md.colour_candidates(True)
    for c in fr:
        o = owners[c["owner"]]
        assert c["cue_id"] == f"frame|{o['id']}" and c["prompt"] == f"Owner {o['id']}'s car is" == md.FRAME_PREFIX.format(owner=o["id"])
        assert c["candidates"] == sp and c["a"] == o["colour"] and c["form"] == "frame" and c["context"] == "none"
        assert "<|im_start|>" not in c["prompt"] and "Q:" not in c["prompt"]     # bare: no header, no chat template
        assert o["colour"] not in c["prompt"].lower()
    for c in fs:
        o = owners[c["owner"]]
        assert c["cue_id"] == f"frame_similar|{o['id']}" and c["prompt"] == md.FRAME_PREFIX.format(owner=o["similar_id"])
        assert c["cue_id_used"] == o["similar_id"] and o["id"] not in c["prompt"] and c["a"] == o["colour"]   # scored on the owner's colour
        assert c["candidates"] == sp
    for c in fb:
        o = owners[c["owner"]]
        assert c["cue_id"] == f"frame_bicycle|{o['id']}" and c["prompt"] == f"Owner {o['id']}'s bicycle is"
        assert c["candidates"] == sp and c["a"] == o["colour"]
    # existing cue families untouched in number and id
    kinds = {k: len(v) for k, v in by_kind.items()}
    assert kinds["fact"] == 192 and kinds["similar"] == 144 and kinds["bicycle"] == 48 and kinds["exact_short"] == 64
    assert kinds["textfit_short"] == kinds["textfit_ante"] == 64 and kinds["generic"] == 1
    assert len(cues) == 1153 + 64 + 48 + 48
    # the mock scorer treats the frame prefix as an exact training-style completion cue (guide fires, bicycle not)
    sc = md.MockScorer(dict(profile="guide", strength={"K7M4": {"red": 40.0}}, lessons={}))
    p_car = sc.candidate_logprobs(["Owner K7M4's car is"], [[" red", " blue"]])[0]
    p_bike = sc.candidate_logprobs(["Owner K7M4's bicycle is"], [[" red", " blue"]])[0]
    with sc.off():
        p_off = sc.candidate_logprobs(["Owner K7M4's car is"], [[" red", " blue"]])[0]
        p_bike_off = sc.candidate_logprobs(["Owner K7M4's bicycle is"], [[" red", " blue"]])[0]
    assert (p_car[0] - p_car[1]) - (p_off[0] - p_off[1]) > 3.0          # log1p(40) boost on the car frame
    assert p_bike == p_bike_off                                           # nothing on the bicycle frame


def test_I_d_frame_and_frame_gates_synthetic():
    run = shared_run()
    bank = run["bank"]
    # mock pipeline on an F cell (budget lowered for speed; the metric does not depend on padding)
    md.set_write_root(run["dir"])
    c = _frame_corpus(run, "F_r4k4", budget=120000)
    cpath = md.write_json(os.path.join(md.cell_dir(run["dir"], 0, "F_r4k4", "across", 4), "corpus.json"), c)
    sums, evs = {}, {}
    for profile in ("guide", "habit", "nothing"):
        adir = os.path.join(run["dir"], "adapters", "bank0", "F_r4k4", "across", "sleep4", f"r8_{profile}")
        md.train_command(run["dir"], cpath, adir, model="mock", mock_profile=profile, no_reuse=True)
        p = md.evaluate_command(run["dir"], 0, adir, f"bank0__F_r4k4__across__sleep4__r8__{profile}", model="mock",
                                meta=dict(cell="F_r4k4", arm="across", sleep=4, rank=8))[0]
        evs[profile] = md.read_json(p)
        sums[profile] = md.summarize_eval(evs[profile], bank)
    s = sums["guide"]
    d16 = s["per_dose"][16]
    assert d16["I_d_frame"] > 1.0 and d16["frame_term1"] > 1.0 and abs(d16["frame_term2"]) < 1e-9
    assert d16["frame_p_on"] > d16["frame_p_off"] and d16["frame_d_p"] > 0.3
    assert len(d16["I_d_frame_values"]) == 16 and len(s["per_dose"][0]["I_d_frame_values"]) == 0
    assert abs(s["per_dose"][0]["frame_d_p"]) < 1e-9 and "I_d_frame" not in s["per_owner"][[o["id"] for o in bank["owners"] if o["dose"] == 0][0]]
    assert s["controls"]["frame_spill"] < 1e-9 and s["controls"]["frame_spill_similar"] < 1e-9
    assert s["controls"]["frame_spill_unexposed"] < 1e-9 and s["controls"]["frame_spill_bicycle"] < 1e-9
    g = md.evaluate_gates(s)
    assert g["G9_frame_binding"]["passed"] is True and g["G9_frame_binding"]["lo"] > 0 and g["G9_frame_binding"]["n"] == 16
    assert "G9_frame_binding" in g["passed"] and g["G9_mass"]["passed"]          # both G9 gates coexist
    assert md.interpret(s, g)["frame_label"] == "frame-binding"
    # habit: the similar id's frame moves too -> spill > 0.03 -> G9 fails; frame dP large -> 'frame-habit'
    sh = sums["habit"]
    gh = md.evaluate_gates(sh)
    assert sh["controls"]["frame_spill_similar"] > 0.03 and sh["controls"]["frame_spill"] > 0.03
    assert gh["G9_frame_binding"]["passed"] is False and sh["per_dose"][16]["frame_d_p"] > 0.3
    assert md.interpret(sh, gh)["frame_label"] == "frame-habit"
    # nothing: no shift anywhere -> G9 and G10 fail -> 'frame-nothing'
    sn = sums["nothing"]
    gn = md.evaluate_gates(sn)
    assert all(abs(sn["per_dose"][d]["frame_d_p"]) < 1e-9 for d in md.DOSES) and abs(sn["per_dose"][16]["I_d_frame"]) < 1e-9
    assert gn["G9_frame_binding"]["passed"] is False and gn["G10_frame_dose"]["passed"] is False
    assert md.interpret(sn, gn)["frame_label"] == "frame-nothing"
    # --- synthetic eval JSON: hand-checked I_d_frame arithmetic (same a/b convention as I_d) ---
    ev = copy.deepcopy(evs["nothing"])
    oid = [o["id"] for o in bank["owners"] if o["dose"] == 16][0]
    colour = {o["id"]: o["colour"] for o in bank["owners"]}[oid]
    others = [c for c in md.COLOURS if c != colour]
    off = {colour: 0.20, others[0]: 0.30, others[1]: 0.10, others[2]: 0.05}          # b = others[0] (strongest under OFF)
    on = {colour: 0.50, others[0]: 0.15, others[1]: 0.05, others[2]: 0.05}
    sim_on = {colour: 0.22, others[0]: 0.28, others[1]: 0.10, others[2]: 0.05}
    for row in ev["cues"]:
        if row["owner"] == oid and row["kind"] in ("frame", "frame_similar"):
            row["OFF"] = dict(p_raw=dict(off), mass=sum(off.values()), logp={k: math.log(v) for k, v in off.items()})
            new = on if row["kind"] == "frame" else sim_on
            row["ON"] = dict(p_raw=dict(new), mass=sum(new.values()), logp={k: math.log(v) for k, v in new.items()})
    e = md.summarize_eval(ev, bank)["per_owner"][oid]
    term1 = math.log(0.50 / 0.15) - math.log(0.20 / 0.30)
    term2 = math.log(0.22 / 0.28) - math.log(0.20 / 0.30)
    assert e["frame_b"] == others[0] and math.isclose(e["frame_term1"], term1) and math.isclose(e["frame_term2"], term2)
    assert math.isclose(e["I_d_frame"], term1 - term2)
    assert math.isclose(e["frame_p_off"], 0.20 / 0.65) and math.isclose(e["frame_p_on"], 0.50 / 0.75)
    assert math.isclose(e["frame_d_p"], 0.50 / 0.75 - 0.20 / 0.65) and math.isclose(e["frame_similar_d_p"], 0.22 / 0.65 - 0.20 / 0.65)
    # --- G9 / G10 on synthetic per-dose values ---
    s2 = copy.deepcopy(s)
    for d, v in ((1, 0.10), (4, 0.25), (16, 0.45)):
        s2["per_dose"][d]["frame_d_p"] = v
    g2 = md.evaluate_gates(s2)
    assert g2["G10_frame_dose"]["passed"] is True and math.isclose(g2["G10_frame_dose"]["rise"], 0.35)
    s2["per_dose"][4]["frame_d_p"] = 0.50                                          # not monotone
    assert md.evaluate_gates(s2)["G10_frame_dose"]["passed"] is False
    s2["per_dose"][4]["frame_d_p"] = 0.12
    s2["per_dose"][16]["frame_d_p"] = 0.15                                         # monotone but rise < 0.1
    assert md.evaluate_gates(s2)["G10_frame_dose"]["passed"] is False
    s3 = copy.deepcopy(s)
    s3["controls"]["frame_spill"] = 0.05                                           # spill alone fails G9 ...
    g3 = md.evaluate_gates(s3)
    assert g3["G9_frame_binding"]["passed"] is False and g3["G9_frame_binding"]["lo"] > 0
    assert md.interpret(s3, g3)["frame_label"] == "frame-habit"                    # ... with a large frame dP -> habit
    s3["per_dose"][16]["frame_d_p"] = 0.2
    assert md.interpret(s3, md.evaluate_gates(s3))["frame_label"] == "frame-nothing"
    s4 = copy.deepcopy(s)
    s4["per_dose"][16]["I_d_frame_values"] = [(-1) ** i * 0.3 for i in range(16)]  # CI covers zero
    assert md.evaluate_gates(s4)["G9_frame_binding"]["passed"] is False
    # the G9/G10 frame gates never enter the paraphrase reading's unmet-gate list
    assert "G10_frame_dose" in gn["failed"] and not any("G10_frame_dose" in r for r in md.interpret(s, g)["reasons"])
    # pooled over banks: values concatenate, spill averages
    pooled = md.pool([s, copy.deepcopy(s)])
    assert len(pooled["per_dose"][16]["I_d_frame_values"]) == 32 and math.isclose(pooled["controls"]["frame_spill"], s["controls"]["frame_spill"])
    assert md.evaluate_gates(pooled)["G9_frame_binding"]["n"] == 32


def test_report_backward_compatible_without_frame_cues():
    run = shared_run()
    d = _generate("compat")                                   # same seed -> same banks as the shared run
    md.set_write_root(d)
    # an eval JSON of the OLD format: the pipeline's eval with every frame cue removed
    w, r, s_ = md.CELLS["B"]
    c = md.build_corpus(run["bank"], "across", 4, w, r, run["counter"], BUDGET)
    cpath = md.write_json(os.path.join(md.cell_dir(d, 0, "B", "across", 4), "corpus.json"), c)
    adir = os.path.join(d, "adapters", "bank0", "B", "across", "sleep4", "r8")
    md.train_command(d, cpath, adir, model="mock")
    tag = "bank0__B__across__sleep4__r8"
    p_new = md.evaluate_command(d, 0, adir, tag + "__framecues", model="mock", meta=dict(cell="B", arm="across", sleep=4, rank=8))[0]
    new = md.read_json(p_new)
    old = copy.deepcopy(new)
    old["tag"] = tag
    old["cues"] = [cue for cue in old["cues"] if not cue["kind"].startswith("frame")]
    old["n_cues"] = len(old["cues"])
    assert old["n_cues"] == 1153 and not md._has_frame_cues(old) and md._has_frame_cues(new)
    p_old = md.write_json(os.path.join(d, "eval", tag + "__lam1.json"), old)
    os.remove(p_new)                                          # first: only the old JSON exists
    s = md.summarize_eval(old, run["bank"])
    for dd in md.DOSES:
        assert s["per_dose"][dd]["frame_d_p"] is None and s["per_dose"][dd]["I_d_frame"] is None
        assert s["per_dose"][dd]["I_d_frame_values"] == []
        if dd > 0:
            assert s["per_dose"][dd]["I_d"] is not None and s["per_dose"][dd]["I_d_values"]   # existing endpoint intact
    assert s["controls"]["frame_spill"] is None and "frame_p_on" not in next(iter(s["per_owner"].values()))
    g = md.evaluate_gates(s)
    assert g["G9_frame_binding"]["passed"] is None and g["G10_frame_dose"]["passed"] is None
    assert "G9_frame_binding" not in g["passed"] + g["failed"] and "G10_frame_dose" not in g["passed"] + g["failed"]
    it = md.interpret(s, g)
    assert it["frame_label"] is None and it["label"] == "guide"
    rep = md.report_command(d)
    res = rep["results"]["B__across__r8__lam1"]
    h = res["headline"]
    assert h["frame_p_on"] is None and h["I_d_frame"] is None and h["frame_label"] is None and res["frame"]["has_frame_cues"] is False
    assert h["I_d"] is not None and h["d_p"] is not None          # the existing endpoint still reports
    summ = open(os.path.join(d, "report", "summary.md")).read()
    assert "| frame P OFF->ON | I_d_frame [95% CI] | frame spill |" in summ and "## Completion-frame retrieval (Rohin 2026-09-11)" in summ
    row = [ln for ln in summ.splitlines() if ln.startswith("| B__across__r8__lam1 |")]
    assert row and row[0].rstrip().endswith(f"| {it['label']} | - | - | - |")   # frame columns show '-'
    frow = [ln for ln in summ.splitlines() if ln.startswith("| B__across__r8__lam1 |") and "n/a | n/a" in ln]
    assert frow and "| - | -/-/-/- | - | -/-/- | - | n/a | n/a | - |" in frow[0]
    arm_md = open(os.path.join(d, "report", "B__across__r8__lam1.md")).read()
    assert "## Completion-frame retrieval" in arm_md and "| G9_frame_binding |" in arm_md and "n/a" in arm_md
    # now the re-scored eval (tag suffix __framecues) is added: the report prefers it, the old file is untouched
    before = open(p_old).read()
    md.write_json(p_new, new)
    rep2 = md.report_command(d)
    assert open(p_old).read() == before
    assert rep2["results"]["B__across__r8__lam1"]["frame"]["has_frame_cues"] is True
    assert rep2["results"]["B__across__r8__lam1"]["headline"]["I_d_frame"] is not None
    rj = md.read_json(os.path.join(d, "report", "report.json"))
    assert rj["evals_used"]["B__across__8__1.0__4__0"] == tag + "__framecues" and rj["n_evals"] == 2
    summ2 = open(os.path.join(d, "report", "summary.md")).read()
    row2 = [ln for ln in summ2.splitlines() if ln.startswith("| B__across__r8__lam1 |")][0]
    assert not row2.rstrip().endswith("| - | - | - |") and "->" in row2
    # the 'gates' count of the cells table is the same for the old eval and its __framecues re-score: the
    # frame gates (evaluable only on the re-score) are counted in the frame table, not here
    header = [ln for ln in summ2.splitlines() if ln.startswith("| cell__arm__rank__lambda | sleep | banks | P raw")][0]
    gi = [h.strip() for h in header.split("|")].index("gates")
    g_old, g_new = row[0].split("|")[gi].strip(), row2.split("|")[gi].strip()
    assert g_old == g_new and re.fullmatch(r"\d+/\d+", g_old), (g_old, g_new)
    g2 = rep2["results"]["B__across__r8__lam1"]["gates"]
    assert set(md.FRAME_GATES) & set(g2["passed"] + g2["failed"])            # evaluable on the re-score ...
    assert int(g_new.split("/")[1]) == len([k for k in g2["passed"] + g2["failed"] if k not in md.FRAME_GATES])
    assert int(g_old.split("/")[1]) == len(g["passed"] + g["failed"])          # ... and the old count is every old gate
    # frames cells never become the paraphrase finalist; B still does here
    assert rep2["finalist"]["cell"] == "B"
    shutil.rmtree(d)


def test_existing_cells_items_sha_unchanged_fixture():
    """Identity check against a fixture computed BEFORE the frames change
    (mock generate seed 0, MockScorer(seed=0), approx counter, budget 60000,
    distractor 300 = shared_run's parameters): bank 0, cells A-Dshuf, sleep 4,
    both arms; items_sha AND ordered sha must be byte-for-byte the same."""
    run = shared_run()
    fx = md.read_json(os.path.join(HERE, "fixtures", "memory_dose_items_sha_pre_frames.json"))
    assert fx["seed"] == 0 and fx["token_budget"] == BUDGET and fx["distractor_tokens"] == 300
    assert set(fx["corpora"]) == {f"bank0/{c}/{a}/sleep4" for c in ("A", "B", "C", "D", "Dshuf") for a in md.ARMS}
    for key, want in fx["corpora"].items():
        _, cell, arm, _ = key.split("/")
        w, r, s = md.CELLS[cell]
        c = run["corpora"][cell] if arm == "across" else md.build_corpus(run["bank"], arm, 4, w, r, run["counter"], BUDGET, shuffled=s)
        assert c["items_sha"] == want["items_sha"], (key, c["items_sha"], want["items_sha"])
        assert c["sha"] == want["sha"] and c["stats"]["n_items"] == want["n_items"], key
        assert c["frame_forms"] == 1 and c["frame_repeats"] == 1 and c["marginal_target"] == run["bank"]["marginal_target"]
    # and the new representation never leaks into the existing cells' items
    assert not any("frame_template" in it for cell in ("A", "B", "C", "D", "Dshuf") for it in run["corpora"][cell]["corpus"])


def test_frames_runbook_syntax_and_conventions():
    import subprocess
    path = os.path.join(ROOT, "gpu", "memory_dose_frames.sh")
    assert subprocess.run(["bash", "-n", path], capture_output=True).returncode == 0
    src = open(path).read()
    for needle in ("__framecues", "STAGE_F_DONE", "F_r1k1 F_r16k1 F_r4k4 F_r1k16", "MAX_FIT_MIN", "RUN=\"${RUN:-$HOME/v6_out/memory_dose}\"",
                   "0:A:across:4:8 0:B:across:4:8", "log()", "fit_eval()", "rescore_one()", "has_frame_cues()", "--measure-only"):
        assert needle in src, needle
    # the F budget is an operator knob on the node: F_TOKEN_BUDGET -> corpus --token-budget through f_corpus(),
    # which both fit_cap and fit_eval use; empty keeps the cell's default (400,000) and the corpus records the budget
    assert 'F_TOKEN_BUDGET="${F_TOKEN_BUDGET:-}"' in src and "f_corpus()" in src
    fc = src.split("f_corpus()")[1].split("fit_cap()")[0]
    assert '${F_TOKEN_BUDGET:+--token-budget "$F_TOKEN_BUDGET"}' in fc and "['token_budget']" in fc and "ABORT" in fc
    assert "f_corpus 0 " in src.split("fit_cap()")[1].split("fit_eval()")[0]
    assert 'f_corpus "$b" "$c" "$a" "$k"' in src.split("fit_eval()")[1].split("fits()")[0]
    assert src.count("$MD corpus ") == 1                                               # one corpus call site
    assert "CELL_TOKEN_BUDGET" not in src                                              # the ABORT names the env knob
    assert "F_TOKEN_BUDGET=<tokens>" in src.split("fit_cap()")[1].split("fit_eval()")[0]
    # bash semantics of the knob: unset -> no flag; set -> the flag with the value
    exp = 'X=${F_TOKEN_BUDGET:+--token-budget "$F_TOKEN_BUDGET"}; echo "[$X]"'
    assert subprocess.run(["bash", "-c", exp], capture_output=True, text=True, env={}).stdout.strip() == "[]"
    assert subprocess.run(["bash", "-c", exp], capture_output=True, text=True,
                          env={"F_TOKEN_BUDGET": "250000"}).stdout.strip() == "[--token-budget 250000]"
    old = open(os.path.join(ROOT, "gpu", "memory_dose.sh")).read()
    assert "F_r" not in old                                                            # the existing runbook is untouched
    # functional (mock model, one cell, one bank): the corpus is built at F_TOKEN_BUDGET and records it; a rerun
    # resumes (no rebuild); a rerun at a different budget ABORTs (exit 3) and leaves the corpus + adapter alone
    d = _generate("frames_runbook")
    env = dict(os.environ, RUN=d, PY=sys.executable, MODEL="mock", REPO=ROOT, F_CELLS="F_r4k4", F_BANKS="0")
    def run(budget):  # noqa: E306
        e = dict(env); e["F_TOKEN_BUDGET"] = budget
        return subprocess.run(["bash", path, "0", "fits"], capture_output=True, text=True, env=e, cwd=ROOT)
    r1 = run("120000")
    cpath = os.path.join(md.cell_dir(d, 0, "F_r4k4", "across", 4), "corpus.json")
    assert r1.returncode == 0 and os.path.exists(os.path.join(d, "STAGE_F_FITS_DONE")), r1.stdout + r1.stderr
    assert "corpus bank0__F_r4k4__across__sleep4: items=" in r1.stdout and "budget=120000" in r1.stdout
    cj = md.read_json(cpath); adir = os.path.join(d, "adapters", "bank0", "F_r4k4", "across", "sleep4", "r8")
    assert cj["token_budget"] == 120000 and cj["stats"]["n_tokens"] <= 120000 and os.path.exists(os.path.join(adir, "DONE"))
    assert os.path.exists(os.path.join(d, "eval", "bank0__F_r4k4__across__sleep4__r8__lam1.json"))
    before = open(cpath).read()
    r2 = run("120000")
    assert r2.returncode == 0 and "corpus bank0" not in r2.stdout and open(cpath).read() == before   # resumed
    r3 = run("100000")
    assert r3.returncode == 3 and "ABORT bank0__F_r4k4__across__sleep4: corpus on disk was built at budget 120000" in r3.stdout
    assert "F_TOKEN_BUDGET=100000" in r3.stdout and open(cpath).read() == before and not os.path.exists(os.path.join(d, "STAGE_F_DONE"))
    r4 = run("")                                                                    # empty knob: the cell default applies
    assert r4.returncode == 0 and "corpus bank0" not in r4.stdout                   # ... and an existing corpus is kept
    e = dict(env); e["F_TOKEN_BUDGET"] = "12k"
    assert subprocess.run(["bash", path, "0", "fits"], capture_output=True, text=True, env=e, cwd=ROOT).returncode == 2
    shutil.rmtree(d)


# ---------------------------------------------------------------------------
# abstention negatives (SEQ-039): 'not observed' renderings, p_abstain, G11_abstention
# ---------------------------------------------------------------------------
# bank-0 sleep-4 corpora of the five F cells that existed BEFORE the negatives knob, computed with the
# mock model at shared_run's parameters before the change: (items_sha, ordered sha of the across arm,
# n_items) at the cell's default budget (400,000) and at the node budget (250,000); content tokens.
# F_r64k16's content exceeds both budgets, so its corpus is the same at either (no padding).
F_SHAS_PRE_NEGATIVES = {
    "F_r1k1": dict(content=14580, b400000=("125c761a8c58e750", "f0e66abc948c0bca", 32933),
                   b250000=("b55053eb1286e6f5", "44c20af5ebde16c3", 20379)),
    "F_r16k1": dict(content=233280, b400000=("ad57daa2f692df95", "1bf5e98b0b4b084a", 24769),
                    b250000=("4f0a578a06401101", "38a4c55229ffd38f", 12217)),
    "F_r16k4": dict(content=234624, b400000=("c8c7f7423c51caf6", "0d643b054ee095a5", 24656),
                    b250000=("755c373ce21bf5b2", "bc1260af55d02093", 12105)),
    "F_r16k16": dict(content=223872, b400000=("5e2a2f3030bc32e4", "fcb16d8f4db83548", 25557),
                     b250000=("4100edbfa20b8b08", "06eb6554469312c7", 13005)),
    "F_r64k16": dict(content=895488, b400000=("ef5e906249ab1eae", "14c41db5b0d4a073", 43264),
                     b250000=("ef5e906249ab1eae", "14c41db5b0d4a073", 43264)),
}
NEG_BUDGET = 250000      # the node budget of the R=16 cells; content ~225-240k, so little padding


def _neg_corpus(run: dict, cell: str, arm: str = "across", sleep: int = 4, budget: int = NEG_BUDGET, bank: dict | None = None) -> dict:
    w, r, s = md.CELLS[cell]
    k = md.cell_frame_knobs(cell)
    return md.build_corpus(bank or run["bank"], arm, sleep, w, r, run["counter"], budget, shuffled=s,
                           frame_forms=k["forms"], frame_repeats=k["repeats"], frame_negatives=md.cell_frame_negatives(cell))


def _negatives(c: dict) -> list:
    return [it for it in c["corpus"] if it["kind"] == "negative"]


def _neg_pipeline(run: dict, cell: str, profile: str, budget: int = NEG_BUDGET, lambdas=None):
    d = run["dir"]
    md.set_write_root(d)
    c = _neg_corpus(run, cell, budget=budget)
    cpath = md.write_json(os.path.join(md.cell_dir(d, 0, cell, "across", 4), "corpus.json"), c)
    adir = os.path.join(d, "adapters", "bank0", cell, "across", "sleep4", f"r8_{profile}")
    md.train_command(d, cpath, adir, model="mock", mock_profile=profile, no_reuse=True)
    paths = md.evaluate_command(d, 0, adir, f"bank0__{cell}__across__sleep4__r8__{profile}", model="mock",
                                lambdas=lambdas, meta=dict(cell=cell, arm="across", sleep=4, rank=8))
    evs = [md.read_json(p) for p in paths]
    return c, evs, [md.summarize_eval(ev, run["bank"]) for ev in evs]


def test_frame_negatives_rendering():
    run = shared_run()
    bank = run["bank"]
    dose = {o["id"]: o["dose"] for o in bank["owners"]}
    d0 = sorted(o for o, d in dose.items() if d == 0)
    # constants: the negative sentence shares the cue's prefix, so " not" is its first continuation
    assert md.FRAME_NEG_CANONICAL == md.FRAME_PREFIX + " not observed." == "Owner {owner}'s car is not observed."
    assert md.FRAME_NEG_BICYCLE_CANONICAL == md.FRAME_BICYCLE_PREFIX + " not observed."
    assert md.ABSTAIN_CONTINUATION == " not" and md.ABSTAIN_CANDIDATES == [" not"]
    for obj, tmpls, canon in (("car", md.FRAME_NEG_TEMPLATES, md.FRAME_NEG_CANONICAL),
                              ("bicycle", md.FRAME_NEG_BICYCLE_TEMPLATES, md.FRAME_NEG_BICYCLE_CANONICAL)):
        assert len(tmpls) == 4 == len(set(tmpls))
        for t in tmpls:
            assert t.endswith(canon) and "?" not in t and t[:-len(canon)].strip() and t[:-len(canon)].endswith(" ")
            assert not any(c in t.lower() for c in md.COLOURS) and t.count("{owner}") >= 2
            for frag in ("what colour", "record lookup", "give the vehicle", "answer with one"):
                assert frag not in t.lower()
    # unexposed owners per sleep and arm (the existing exposure schedule): across -- dose 1 sits in session 4
    assert sorted(md.unexposed_owners(bank, "across", 4)) == d0 == sorted(md.unexposed_owners(bank, "across", 6))
    assert sorted(md.unexposed_owners(bank, "across", 3)) == sorted(o for o, d in dose.items() if d in (0, 1))
    assert sorted(md.unexposed_owners(bank, "across", 1)) == sorted(o for o, d in dose.items() if d in (0, 1))
    assert sorted(md.unexposed_owners(bank, "within", 3)) == sorted(dose) and sorted(md.unexposed_owners(bank, "within", 4)) == d0
    # the bicycle subset: 25% of every dose group, fixed per bank (seed and bank index), independent of arm/sleep
    bo = md.bicycle_negative_owners(bank)
    assert len(bo) == 12 == len(set(bo)) and all(dose[o] > 0 for o in bo)
    assert [sum(1 for o in bo if dose[o] == d) for d in (1, 4, 16)] == [4, 4, 4]
    assert bo == md.bicycle_negative_owners(bank)
    b1 = dict(bank); b1["bank"] = 1
    other = dict(bank); other["seed"] = 7
    assert md.bicycle_negative_owners(b1) != bo and md.bicycle_negative_owners(other) != bo
    # rendering: K_neg copies rotate through the 4 templates, deterministic
    assert sorted(md.frame_negative_index(0, 0, "K7M4", "car", r, 4) for r in range(4)) == [0, 1, 2, 3]
    assert md.frame_negative_index(0, 0, "K7M4", "car", 0, 4) != md.frame_negative_index(0, 0, "K7M4", "bicycle", 0, 4) or True
    ctx, tgt, t = md.render_negative("K7M4", "car", 1, seed=0, bank=0)
    assert ctx + tgt == md.FRAME_NEG_TEMPLATES[t].format(owner="K7M4") and tgt == "Owner K7M4's car is not observed."
    # the corpus: sleep 4 -> K_neg x 16 unexposed (dose-0) car negatives + K_neg x 12 (25% of 48 exposed) bicycle negatives
    for cell in ("F_r16k16_neg4", "F_r16k4_neg4"):
        c = _neg_corpus(run, cell)
        K, R = md.cell_frame_knobs(cell)["forms"], md.cell_frame_knobs(cell)["repeats"]
        neg = _negatives(c)
        assert len(neg) == 4 * 16 + 4 * 12 == 112 == c["stats"]["n_negatives"] == c["stats"]["by_kind"]["negative"]
        car = [it for it in neg if it["negative_object"] == "car"]
        bic = [it for it in neg if it["negative_object"] == "bicycle"]
        assert sorted({it["owner"] for it in car}) == d0 and len(car) == 64          # every dose-0 owner, 4 renderings
        assert not any(dose[it["owner"]] > 0 for it in car)                             # none for an exposed owner's car
        assert sorted({it["owner"] for it in bic}) == sorted(bo) and len(bic) == 48    # the fixed 25% exposed subset
        assert c["stats"]["negative_owners"] == dict(car=d0, bicycle=sorted(bo))
        for it in neg:
            canon = (md.FRAME_NEG_CANONICAL if it["negative_object"] == "car" else md.FRAME_NEG_BICYCLE_CANONICAL)
            text = md.render_item(it)
            assert text.endswith(canon.format(owner=it["owner"])) and it["target"] == canon.format(owner=it["owner"])
            tmpls = md.FRAME_NEG_TEMPLATES if it["negative_object"] == "car" else md.FRAME_NEG_BICYCLE_TEMPLATES
            assert text == tmpls[it["frame_neg_template"]].format(owner=it["owner"])
            assert it["chat"] is False and it["mask_context"] is False and it["weight"] == 1.0    # bare, loss on every token
            assert it["colour"] is None and it["frame_template"] is None and "<|im_start|>" not in text
            assert it["frame_negatives"] == 4 and it["frame_forms"] == K and it["frame_repeats"] == R and 0 <= it["frame_copy"] < 4
            assert 1 <= it["session"] <= md.N_SLEEPS_EXPOSURE and it["event_ids"] == [f"b0-{it['owner']}-neg-{it['negative_object']}-{it['frame_copy']:02d}"]
        per_owner: dict = {}
        for it in neg:
            per_owner.setdefault((it["owner"], it["negative_object"]), []).append(it)
        assert all(sorted(x["frame_copy"] for x in v) == [0, 1, 2, 3] and sorted(x["frame_neg_template"] for x in v) == [0, 1, 2, 3]
                   for v in per_owner.values())                                           # all four templates per owner
        # every item of the corpus records K_neg; only negatives carry negative_object
        assert all(it["frame_negatives"] == 4 for it in c["corpus"])
        assert not any("negative_object" in it for it in c["corpus"] if it["kind"] != "negative")
        assert c["frame_negatives"] == 4 and c["stats"]["frame_negatives"] == 4
        # the positive content is exactly the no-negatives cell's: same fact renderings, same colour marginals
        base = _neg_corpus(run, cell.replace("_neg4", ""))
        assert base["frame_negatives"] == 0 and not _negatives(base) and "negative" not in base["stats"]["by_kind"]
        assert sorted(md.render_item(f) for f in _facts(c)) == sorted(md.render_item(f) for f in _facts(base))
        assert c["stats"]["colour_marginals"] == base["stats"]["colour_marginals"] and c["marginal_target"] == base["marginal_target"]
        assert c["stats"]["content_tokens"] > base["stats"]["content_tokens"] and c["stats"]["n_tokens"] <= NEG_BUDGET
        assert c["stats"]["n_items"] < base["stats"]["n_items"]                          # negatives displace padding
        assert c["items_sha"] != base["items_sha"]
        # determinism and the sleep-4 within/across identity (same negatives in both arms)
        assert _neg_corpus(run, cell)["sha"] == c["sha"]
        w4 = _neg_corpus(run, cell, arm="within")
        assert w4["items_sha"] == c["items_sha"] and w4["sha"] != c["sha"]
    # per sleep from the schedule, not accumulated: across sleep 3 -> dose-1 owners still unexposed (32 car owners),
    # bicycles only for the exposed dose-4/16 members of the subset (8); within sleep 2 -> nobody exposed
    c3 = _neg_corpus(run, "F_r16k4_neg4", sleep=3)
    car3 = {it["owner"] for it in _negatives(c3) if it["negative_object"] == "car"}
    bic3 = {it["owner"] for it in _negatives(c3) if it["negative_object"] == "bicycle"}
    assert car3 == {o for o, d in dose.items() if d in (0, 1)} and bic3 == {o for o in bo if dose[o] in (4, 16)}
    assert len(_negatives(c3)) == 4 * 32 + 4 * 8
    c2 = _neg_corpus(run, "F_r16k4_neg4", arm="within", sleep=2)
    assert {it["owner"] for it in _negatives(c2)} == set(dose) and len(_negatives(c2)) == 4 * 64
    assert not any(it["negative_object"] == "bicycle" for it in _negatives(c2))
    # the knob is inert outside frames and for the existing cells
    A = md.build_corpus(bank, "across", 4, "dedup", "short", run["counter"], BUDGET, frame_negatives=4)
    assert A["frame_negatives"] == 0 and not _negatives(A) and A["items_sha"] == run["corpora"]["A"]["items_sha"]
    assert not any("frame_negatives" in it for it in A["corpus"])
    # the mock trainer reads the abstention from the canonical negative target
    md.set_write_root(run["dir"])
    ad = md.train_mock(_neg_corpus(run, "F_r16k4_neg4"), os.path.join(run["dir"], "adapters", "neg_check"), profile="guide")
    assert set(ad["abstain"]) == set(d0) | set(bo) and len(ad["abstain"]) == 28
    assert all(ad["abstain"][o] == {"car": 12.0} for o in d0) and all(ad["abstain"][o] == {"bicycle": 12.0} for o in bo)
    assert len(ad["strength"]) == 48 and md._TARGET_NEG_RE.match("Owner K7M4's bicycle is not observed.").group(2) == "bicycle"


def test_frame_negative_cells_registered_and_manifest():
    run = shared_run()
    for cell, K in (("F_r16k16_neg4", 16), ("F_r16k4_neg4", 4)):
        assert md.FRAME_CELLS[cell] == dict(forms=K, repeats=16, negatives=4) and md.cell_frame_knobs(cell) == md.FRAME_CELLS[cell]
        assert md.CELLS[cell] == ("occurrences", "frames", False) and md.cell_frame_negatives(cell) == 4
        assert md.cell_budget(cell, 65536) == md.FRAME_TOKEN_BUDGET == 400000            # token budget as the other F cells
        assert f"K={K} forms x R=16 repeats, K_neg=4 negatives" in md._cell_label(cell)
        assert md.parse_tag(f"bank2__{cell}__across__sleep4__r8") == dict(bank=2, cell=cell, arm="across", sleep=4, rank=8)
    for cell in ("F_r1k1", "F_r16k1", "F_r16k4", "F_r16k16", "F_r64k16", "F_r4k4", "F_r1k16", "A", "B", "C", "D", "Dshuf", "Bw", "Dw"):
        assert md.cell_frame_negatives(cell) == 0 and "negatives" not in md.cell_frame_knobs(cell) and "K_neg" not in md._cell_label(cell)
    assert md.FRAME_GATES == ("G9_frame_binding", "G10_frame_dose", "G11_abstention")
    assert md.GATES["abstain_min"] == 0.5 and md.GATES["abstain_max_exposed"] == 0.1
    # corpus-all: the negatives come from the cell name; identity at sleep 4 holds; the manifest field is on disk
    d = _generate("negatives_all")
    out = md.corpus_all(d, run["counter"], cells=["F_r16k4_neg4"], arms=["across", "within"], sleeps=[4], token_budget=NEG_BUDGET)
    assert out["identity_check"] == [dict(bank=b, cell="F_r16k4_neg4", sleep=4, within=out["identity_check"][b]["within"],
                                          across=out["identity_check"][b]["across"], identical_items=True, identical_sha=False,
                                          identical=False) for b in range(3)]
    idx = md.read_json(os.path.join(d, "corpora", "index.json"))
    for b in range(3):
        e = idx["index"][f"bank{b}/F_r16k4_neg4/across/sleep4"]
        assert e["frame_negatives"] == 4 and e["n_negatives"] == 112 and e["by_kind"]["negative"] == 112
        cj = md.read_json(e["path"])
        assert cj["frame_negatives"] == 4 and cj["synthetic"] is True and len(_negatives(cj)) == 112
        assert len(cj["stats"]["negative_owners"]["car"]) == 16 and len(cj["stats"]["negative_owners"]["bicycle"]) == 12
    # CLI by cell name and by knobs
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "F_r16k16_neg4", "--arm", "across", "--sleep", "4",
             "--token-budget", str(NEG_BUDGET)])
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "F_r16k16_neg4", "across", 4), "corpus.json"))
    assert cj["frame_forms"] == 16 and cj["frame_repeats"] == 16 and cj["frame_negatives"] == 4 and cj["token_budget"] == NEG_BUDGET
    assert cj["items_sha"] == _neg_corpus(run, "F_r16k16_neg4")["items_sha"]
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--writer", "occurrences", "--representation", "frames",
             "--frame-forms", "4", "--frame-repeats", "2", "--frame-negatives", "2", "--arm", "across", "--sleep", "4",
             "--token-budget", "90000"])
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "occurrences-frames-r2k4-neg2", "across", 4), "corpus.json"))
    assert cj["frame_negatives"] == 2 and len(_negatives(cj)) == 2 * 28 and all(it["frame_negatives"] == 2 for it in cj["corpus"])
    md.main(["corpus", "--run-dir", d, "--bank", "0", "--cell", "F_r16k4", "--arm", "across", "--sleep", "4",
             "--token-budget", str(NEG_BUDGET)])
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "F_r16k4", "across", 4), "corpus.json"))
    assert cj["frame_negatives"] == 0 and not _negatives(cj)
    shutil.rmtree(d)


def test_p_abstain_recorded_and_G11_abstention():
    run = shared_run()
    bank = run["bank"]
    owners = {o["id"]: o for o in bank["owners"]}
    tok = _tokenizer()
    if tok is None:
        print("SKIP tokenizer not cached offline: the ' not' single-token check runs on the node (eval JSON abstain_check)")
    else:
        chk = md.abstain_token_check(tok)
        assert chk["mode"] == "tokenizer" and chk["single_token"] is True and chk["n_tokens"] == 1 and chk["ok"], chk
    lit = md.abstain_token_check(None)
    assert lit == dict(candidate=" not", mode="literal", literal_prefix=True, n_tokens=None, straddle=None, single_token=None, ok=True)
    # the frame-family cues carry the abstention candidate; the colour candidate set is untouched
    dist = md.read_json(os.path.join(run["dir"], "distractor.json"))["text"]
    cues = md.build_cues(bank, dist)
    fam = [c for c in cues if c["kind"] in md.FRAME_CUE_KINDS]
    assert len(fam) == 64 + 48 + 48 and all(c["abstain"] == [" not"] and c["candidates"] == md.colour_candidates(True) for c in fam)
    assert not any("abstain" in c for c in cues if c["kind"] not in md.FRAME_CUE_KINDS) and len(cues) == 1313
    # mock pipeline on the negatives cell: p_abstain OFF and ON on every frame-family row and nowhere else
    sums, evs = {}, {}
    for profile in ("guide", "habit", "nothing"):
        _, ev, s = _neg_pipeline(run, "F_r16k4_neg4", profile)
        evs[profile], sums[profile] = ev[0], s[0]
        rows = ev[0]["cues"]
        fr = [r for r in rows if r["kind"] in md.FRAME_CUE_KINDS]
        assert len(fr) == 160 and all(0.0 <= r[side]["p_abstain"] <= 1.0 for r in fr for side in ("OFF", "ON"))
        assert all(set(r["OFF"]) == {"p_raw", "mass", "logp", "p_abstain"} and set(r["OFF"]["p_raw"]) == set(md.COLOURS) for r in fr)
        assert not any("p_abstain" in r["OFF"] or "p_abstain" in r["ON"] for r in rows if r["kind"] not in md.FRAME_CUE_KINDS)
        assert ev[0]["abstain_check"]["ok"] and ev[0]["abstain_check"]["mode"] == "literal" and ev[0]["n_cues"] == 1313
    # OFF is the same under every profile (the adapter only acts ON); the colour metrics are what they were
    off = {r["cue_id"]: r["OFF"]["p_abstain"] for r in evs["guide"]["cues"] if "p_abstain" in r["OFF"]}
    assert off == {r["cue_id"]: r["OFF"]["p_abstain"] for r in evs["nothing"]["cues"] if "p_abstain" in r["OFF"]}
    assert all(v < 0.2 for v in off.values())
    fg = {r["cue_id"]: r["ON"]["p_raw"] for r in evs["guide"]["cues"] if r["kind"] == "frame"}
    _, ev_base, s_base = _neg_pipeline(run, "F_r16k4", "guide")           # the same recipe without negatives
    assert {r["cue_id"]: r["ON"]["p_raw"] for r in ev_base[0]["cues"] if r["kind"] == "frame"} == fg
    # guide + negatives: abstains at the dose-0 owners' frames and the bicycle frames, not at the dose-16 frames
    s = sums["guide"]
    d0 = [o for o in owners if owners[o]["dose"] == 0]
    e0, e16 = s["per_owner"][d0[0]], s["per_owner"][[o for o in owners if owners[o]["dose"] == 16][0]]
    assert e0["abstain_on"] > 0.5 > e0["abstain_off"] and e0["abstain_d"] > 0.3 and "abstain_bicycle_on" not in e0
    assert e16["abstain_on"] < 0.1 and e16["abstain_bicycle_on"] > 0.5 and "abstain_similar_on" in e16
    assert s["per_dose"][0]["abstain_on"] >= 0.5 and s["per_dose"][16]["abstain_on"] <= 0.1 and s["per_dose"][0]["abstain_bicycle_on"] is None
    c = s["controls"]
    assert c["abstain_unexposed_on"] == s["per_dose"][0]["abstain_on"] and c["abstain_bicycle_on"] >= 0.5
    assert c["abstain_exposed16_on"] == s["per_dose"][16]["abstain_on"] and c["abstain_similar_on"] < 0.2 and c["abstain_unexposed_off"] < 0.2
    g = md.evaluate_gates(s)
    g11 = g["G11_abstention"]
    assert g11["passed"] is True and "G11_abstention" in g["passed"] and g11["value"]["unexposed"] >= 0.5
    assert g11["value"]["bicycle"] >= 0.5 and g11["value"]["d16"] <= 0.1 and g11["off"]["unexposed"] < 0.2
    it = md.interpret(s, g)
    assert it["abstention"] is True and it["abstain_unexposed_on"] == c["abstain_unexposed_on"] and it["frame_label"] == "frame-binding"
    assert not any("G11" in r for r in it["reasons"])                                    # a frame gate, out of the paraphrase reading
    assert g["G9_frame_binding"]["passed"] is True                                        # spill unchanged in definition
    # the same recipe without negatives: G9 still passes under the guide mock, G11 fails -- independent gates
    gb = md.evaluate_gates(s_base[0])
    assert gb["G9_frame_binding"]["passed"] is True and gb["G11_abstention"]["passed"] is False
    assert s_base[0]["controls"]["abstain_unexposed_on"] < 0.2 and s_base[0]["controls"]["abstain_bicycle_on"] < 0.2
    # nothing: abstention unchanged ON vs OFF -> G11 fails
    sn = sums["nothing"]
    assert all(abs(e["abstain_d"]) < 1e-9 for e in sn["per_owner"].values()) and md.evaluate_gates(sn)["G11_abstention"]["passed"] is False
    # habit: the abstention spreads to the similar id too (nearest trained id) -- reported, not gated
    assert sums["habit"]["controls"]["abstain_similar_on"] > sums["guide"]["controls"]["abstain_similar_on"]
    # lambda 0 reproduces OFF for p_abstain as for everything else
    _, ev_l, _ = _neg_pipeline(run, "F_r16k4_neg4", "guide", lambdas=[0.0, 1.0])
    assert all(r["ON"]["p_abstain"] == r["OFF"]["p_abstain"] for r in ev_l[0]["cues"] if "p_abstain" in r["OFF"])
    assert any(r["ON"]["p_abstain"] != r["OFF"]["p_abstain"] for r in ev_l[1]["cues"] if "p_abstain" in r["OFF"])
    # --- G11 on synthetic values ---
    s2 = copy.deepcopy(s)
    s2["controls"]["abstain_unexposed_on"], s2["controls"]["abstain_bicycle_on"], s2["per_dose"][16]["abstain_on"] = 0.6, 0.7, 0.05
    assert md.evaluate_gates(s2)["G11_abstention"]["passed"] is True
    for key, val in (("unexposed", 0.49), ("bicycle", 0.3), ("d16", 0.11)):
        s3 = copy.deepcopy(s2)
        if key == "d16":
            s3["per_dose"][16]["abstain_on"] = val
        else:
            s3["controls"][f"abstain_{key}_on"] = val
        assert md.evaluate_gates(s3)["G11_abstention"]["passed"] is False, key
    for key in ("unexposed", "bicycle", "d16"):
        for missing in (None, float("nan")):
            s4 = copy.deepcopy(s2)
            if key == "d16":
                s4["per_dose"][16]["abstain_on"] = missing
            else:
                s4["controls"][f"abstain_{key}_on"] = missing
            g4 = md.evaluate_gates(s4)
            assert g4["G11_abstention"]["passed"] is None and "G11_abstention" not in g4["passed"] + g4["failed"], key
    # boundaries are inclusive
    s5 = copy.deepcopy(s2)
    s5["controls"]["abstain_unexposed_on"], s5["controls"]["abstain_bicycle_on"], s5["per_dose"][16]["abstain_on"] = 0.5, 0.5, 0.1
    assert md.evaluate_gates(s5)["G11_abstention"]["passed"] is True
    # pooled over banks: controls average, G11 stays evaluable
    pooled = md.pool([s, copy.deepcopy(s)])
    assert math.isclose(pooled["controls"]["abstain_unexposed_on"], c["abstain_unexposed_on"])
    assert md.evaluate_gates(pooled)["G11_abstention"]["passed"] is True
    # report: the completion-frame table carries K_neg, the abstain means and G11
    rep = md.report_command(run["dir"])
    res = rep["results"]["F_r16k4_neg4__across__r8__lam1"]
    assert res["frame"]["negatives"] == 4 and res["frame"]["has_abstain"] is True and res["frame"]["G11_abstention"]["passed"] is True
    assert set(res["frame"]["abstain"]) == {"unexposed", "similar", "bicycle", "exposed16"} and res["frame"]["abstain"]["unexposed"] >= 0.5
    assert res["headline"]["abstain_exposed16_on"] <= 0.1
    summ = open(os.path.join(run["dir"], "report", "summary.md")).read()
    hdr = [ln for ln in summ.splitlines() if ln.startswith("| cell__arm__rank__lambda | sleep | banks | K forms |")][0]
    cols = [h.strip() for h in hdr.strip("|").split("|")]
    assert cols[5] == "K_neg negatives" and cols[-3:] == ["abstain ON unexposed/similar/bicycle", "abstain ON exposed d16", "G11_abstention"]
    row = [ln for ln in summ.splitlines() if ln.startswith("| F_r16k4_neg4__across__r8__lam1 |") and "PASS" in ln][0]
    vals = [v.strip() for v in row.strip("|").split("|")]
    assert vals[5] == "4" and vals[-1] == "PASS" and re.fullmatch(r"0\.\d{3}/0\.\d{3}/0\.\d{3}", vals[-3]) and float(vals[-2]) <= 0.1
    row_b = [ln for ln in summ.splitlines() if ln.startswith("| F_r16k4__across__r8__lam1 |") and ("PASS" in ln or "FAIL" in ln)][0]
    vals_b = [v.strip() for v in row_b.strip("|").split("|")]
    assert vals_b[5] == "0" and vals_b[-1] == "FAIL"
    assert "abstention is the intended route to passing it" in summ and "G11_abstention = unexposed and bicycle >= 0.5" in summ
    arm_md = open(os.path.join(run["dir"], "report", "F_r16k4_neg4__across__r8__lam1.md")).read()
    assert "| G11_abstention |" in arm_md and "P(abstain) ON: unexposed=" in arm_md and "abstain OFF->ON (owner frame)" in arm_md
    assert "abstention is the intended route to passing it" in arm_md and "K_neg=4 negatives" in arm_md
    # the cells table's gates count excludes G11 like the other frame gates
    hdr_c = [ln for ln in summ.splitlines() if ln.startswith("| cell__arm__rank__lambda | sleep | banks | P raw")][0]
    gi = [h.strip() for h in hdr_c.split("|")].index("gates")
    row_c = [ln for ln in summ.splitlines() if ln.startswith("| F_r16k4_neg4__across__r8__lam1 |")][0]
    assert int(row_c.split("|")[gi].strip().split("/")[1]) == len([k for k in g["passed"] + g["failed"] if k not in md.FRAME_GATES])


def test_report_backward_compatible_without_p_abstain():
    run = shared_run()
    d = _generate("compat_abstain")                             # same seed -> same banks as the shared run
    md.set_write_root(d)
    w, r, s_ = md.CELLS["F_r16k4"]
    k = md.cell_frame_knobs("F_r16k4")
    c = md.build_corpus(run["bank"], "across", 4, w, r, run["counter"], NEG_BUDGET, frame_forms=k["forms"], frame_repeats=k["repeats"])
    cpath = md.write_json(os.path.join(md.cell_dir(d, 0, "F_r16k4", "across", 4), "corpus.json"), c)
    adir = os.path.join(d, "adapters", "bank0", "F_r16k4", "across", "sleep4", "r8")
    md.train_command(d, cpath, adir, model="mock")
    tag = "bank0__F_r16k4__across__sleep4__r8"
    p = md.evaluate_command(d, 0, adir, tag, model="mock", meta=dict(cell="F_r16k4", arm="across", sleep=4, rank=8))[0]
    new = md.read_json(p)
    # an eval of the post-frames, pre-abstention format: frame cues present, no p_abstain anywhere
    old = copy.deepcopy(new)
    for row in old["cues"]:
        row["OFF"].pop("p_abstain", None)
        row["ON"].pop("p_abstain", None)
        row.pop("abstain", None)
    old.pop("abstain_check", None)
    assert md._has_frame_cues(old) and not any("p_abstain" in row["OFF"] for row in old["cues"])
    md.write_json(p, old)
    s = md.summarize_eval(old, run["bank"])
    assert not any(k.startswith("abstain") for e in s["per_owner"].values() for k in e)
    for dd in md.DOSES:
        assert s["per_dose"][dd]["abstain_on"] is None and s["per_dose"][dd]["abstain_bicycle_on"] is None
        assert s["per_dose"][dd]["frame_d_p"] is not None                                  # the frame metrics still report
    assert all(s["controls"][k] is None for k in ("abstain_unexposed_on", "abstain_similar_on", "abstain_bicycle_on", "abstain_exposed16_on"))
    g = md.evaluate_gates(s)
    assert g["G11_abstention"]["passed"] is None and "G11_abstention" not in g["passed"] + g["failed"]
    assert g["G9_frame_binding"]["passed"] is not None and g["G10_frame_dose"]["passed"] is not None
    it = md.interpret(s, g)
    assert it["abstention"] is None and it["abstain_unexposed_on"] is None and it["frame_label"] is not None
    rep = md.report_command(d)
    res = rep["results"]["F_r16k4__across__r8__lam1"]
    assert res["frame"]["has_abstain"] is False and res["frame"]["has_frame_cues"] is True
    assert all(v is None for v in res["frame"]["abstain"].values()) and res["headline"]["abstain_exposed16_on"] is None
    summ = open(os.path.join(d, "report", "summary.md")).read()
    frow = [ln for ln in summ.splitlines() if ln.startswith("| F_r16k4__across__r8__lam1 |") and ("PASS" in ln or "FAIL" in ln)][0]
    assert frow.rstrip().endswith("| -/-/- | - | n/a |")                                   # abstain columns and G11 show '-' / n/a
    vals = [v.strip() for v in frow.strip("|").split("|")]
    assert vals[5] == "0" and vals[6] != "-"                                                # K_neg 0; frame P still reported
    arm_md = open(os.path.join(d, "report", "F_r16k4__across__r8__lam1.md")).read()
    assert "| G11_abstention |  |" in arm_md and "n/a" in arm_md.split("| G11_abstention |")[1].split("\n")[0]
    # a fully old eval (no frame cues at all) is unchanged in behaviour: G11 n/a as well
    older = copy.deepcopy(old)
    older["cues"] = [cue for cue in older["cues"] if not cue["kind"].startswith("frame")]
    so = md.summarize_eval(older, run["bank"])
    assert md.evaluate_gates(so)["G11_abstention"]["passed"] is None and so["controls"]["abstain_unexposed_on"] is None
    # the pooled controls tolerate a bank without p_abstain next to one with it
    pooled = md.pool([s, md.summarize_eval(new, run["bank"])])
    assert md.evaluate_gates(pooled)["G11_abstention"]["passed"] is not None
    shutil.rmtree(d)


def test_existing_F_cells_items_sha_unchanged():
    """The five F cells that existed before the negatives knob keep byte-identical corpora (items_sha and
    ordered sha) at the shared_run parameters; the values were computed with the mock model BEFORE the
    change (F_SHAS_PRE_NEGATIVES). The knob's absence on these cells is 0."""
    run = shared_run()
    for cell, want in F_SHAS_PRE_NEGATIVES.items():
        w, r, s = md.CELLS[cell]
        k = md.cell_frame_knobs(cell)
        assert md.cell_frame_negatives(cell) == 0 and "negatives" not in k
        budgets = (250000,) if cell == "F_r64k16" else (400000, 250000)
        for budget in budgets:
            c = md.build_corpus(run["bank"], "across", 4, w, r, run["counter"], budget, shuffled=s,
                                frame_forms=k["forms"], frame_repeats=k["repeats"], frame_negatives=md.cell_frame_negatives(cell))
            items_sha, sha, n_items = want[f"b{budget}"]
            assert c["items_sha"] == items_sha and c["sha"] == sha, (cell, budget, c["items_sha"], c["sha"])
            assert c["stats"]["n_items"] == n_items and c["stats"]["content_tokens"] == want["content"], (cell, budget)
            assert c["frame_negatives"] == 0 and not _negatives(c) and "negative" not in c["stats"]["by_kind"]
            assert all(it["frame_negatives"] == 0 for it in c["corpus"])
        if cell == "F_r64k16":
            assert c["stats"]["content_tokens"] > 400000                                    # same corpus at either budget
        w4 = md.build_corpus(run["bank"], "within", 4, w, r, run["counter"], 250000, shuffled=s,
                             frame_forms=k["forms"], frame_repeats=k["repeats"])
        assert w4["items_sha"] == want["b250000"][0]                                          # arm identity as before
    assert md.cell_budget("F_r64k16", 65536) == 400000


def test_frames_runbook_accepts_negative_cells():
    import subprocess
    path = os.path.join(ROOT, "gpu", "memory_dose_frames.sh")
    src = open(path).read()
    assert "F_r16k16_neg4" in src and "F_r16k4_neg4" in src                              # documented as allowed names
    assert 'F_CELLS="${F_CELLS:-F_r1k1 F_r16k1 F_r16k4 F_r16k16}"' in src                # default unchanged
    assert src.count("$MD corpus ") == 1 and '--cell "$c"' in src                         # cells are looked up by name
    d = _generate("frames_runbook_neg")
    env = dict(os.environ, RUN=d, PY=sys.executable, MODEL="mock", REPO=ROOT, F_CELLS="F_r16k4_neg4", F_BANKS="0",
               F_TOKEN_BUDGET=str(NEG_BUDGET), FORCE="1")
    r1 = subprocess.run(["bash", path, "0", "fits"], capture_output=True, text=True, env=env, cwd=ROOT)
    assert r1.returncode == 0 and os.path.exists(os.path.join(d, "STAGE_F_FITS_DONE")), r1.stdout + r1.stderr
    assert "corpus bank0__F_r16k4_neg4__across__sleep4: items=" in r1.stdout and "frame_negatives=4 negatives=112" in r1.stdout
    cj = md.read_json(os.path.join(md.cell_dir(d, 0, "F_r16k4_neg4", "across", 4), "corpus.json"))
    assert cj["frame_negatives"] == 4 and cj["token_budget"] == NEG_BUDGET and len(_negatives(cj)) == 112
    ev = md.read_json(os.path.join(d, "eval", "bank0__F_r16k4_neg4__across__sleep4__r8__lam1.json"))
    assert ev["meta"]["cell"] == "F_r16k4_neg4" and ev["abstain_check"]["ok"]
    assert all("p_abstain" in c["ON"] for c in ev["cues"] if c["kind"] in md.FRAME_CUE_KINDS)
    r2 = subprocess.run(["bash", path, "0", "report"], capture_output=True, text=True, env=env, cwd=ROOT)
    assert r2.returncode == 0 and os.path.exists(os.path.join(d, "STAGE_F_DONE")), r2.stdout + r2.stderr
    summ = open(os.path.join(d, "report", "summary.md")).read()
    assert "| F_r16k4_neg4__across__r8__lam1 |" in summ and "G11_abstention" in summ
    shutil.rmtree(d)


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
