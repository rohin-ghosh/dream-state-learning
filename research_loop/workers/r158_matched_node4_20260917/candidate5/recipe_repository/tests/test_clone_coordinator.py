"""Clone coordinator: barrier with 2 fake clones and a fake trainer (no GPU),
the degrade paths (a clone misses the barrier; a clone's round times out
before the coordinator arrives), the rejection path, restart from markers,
provenance stamping, the review fixes of 2026-09-10 (no DONE marker before
the gate; no row pooled twice; late rounds attached; torn pool append
recovered; gate stats before the marker; registration refusals; redacted
manifest; barrier ignores finished clones; the waking brief readable by the
parent view) and an END-TO-END run of two run_life_v2 clones as subprocesses
in the fake world (tests/clone_life_driver.py).

  python3 tests/test_clone_coordinator.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from organism_v6 import clone_coordinator as cc  # noqa: E402
from organism_v6.run_life import latest_adapter  # noqa: E402


def _rg_available():
    try:
        import reasoning_gym  # noqa: F401
        return True
    except ImportError:
        return False


def rows_for(clone, n, start_tick=1):
    out = []
    for e in range(n):
        eid = f"prog-{clone}-{e}"
        for t in range(start_tick, start_tick + 2):
            out.append(dict(kind="act", episode_id=eid, tick=t,
                            action=f"a{t}", outcome="ok", score=0.1 * t,
                            prediction=0.3, surprise=0.1 * t - 0.3))
            out.append(dict(kind="thought", episode_id=eid, tick=t,
                            note=f"PREDICT: 0.3\nACT: a{t}\nNOTE: clone {clone}"))
    return out


class FakeFns:
    """compile / train / gate fakes with call counters."""

    def __init__(self, gate_ok=True, reason="OK", train_fail_once=False):
        self.compiles = self.trains = self.gates = 0
        self.gate_ok, self.reason = gate_ok, reason
        self.train_fail_once = train_fail_once
        self.last_rows = None

    def compile_fn(self, rows, out_dir, prior):
        self.compiles += 1
        self.last_rows = rows
        corpus = list(prior) + [f"row {r.get('clone_id')}:{r.get('episode_id')}"
                                for r in rows if r.get("kind") == "act"]
        with open(os.path.join(out_dir, "corpus.json"), "w") as f:
            json.dump(dict(corpus=corpus, n_new=len(corpus) - len(prior)), f)
        with open(os.path.join(out_dir, "waking_brief.txt"), "w") as f:
            f.write("brief from the pooled sleep\n")
        return dict(n_new=len(corpus) - len(prior), n_principles=0)

    def train_fn(self, corpus_path, out_dir):
        self.trains += 1
        if self.train_fail_once:
            self.train_fail_once = False
            raise RuntimeError("trainer crashed (simulated)")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "adapter_model.bin"), "w") as f:
            f.write("weights\n")
        with open(os.path.join(out_dir, "DONE"), "w") as f:
            f.write("ok\n")
        return 0

    def gate_fn(self, adapter_dir, specs):
        self.gates += 1
        assert os.path.exists(os.path.join(adapter_dir, "CANDIDATE"))
        per = {str(k): dict(gym=s["gym"], candidate=0.5, floor=0.45,
                            score_ok=self.gate_ok, brevity_ok=True,
                            canary_ok=True) for k, s in specs.items()}
        return dict(ok=self.gate_ok, reason=self.reason, per_clone=per)


def make_group(root, k, count=2, poll=0.02, **extra):
    g = cc.CloneGroup(os.path.join(root, "group"), k, count, poll_s=poll,
                      log=lambda m: None)
    life = os.path.join(root, f"life_{k}")
    os.makedirs(life, exist_ok=True)
    spec = dict(gym="compiler" if k == 0 else "reasoning_gym", life_dir=life,
                gate_set=["g1", "g2"], exam_set=["e1"], canary_set=["c1"],
                budget_ticks=3, seed=k, arm="B", exposure_domain=f"dom{k}",
                rank=8, schedule=dict(name="sched_v_test", stages=[]))
    spec.update(extra)
    g.register(**spec)
    return g, life


def test_two_clones_one_write_both_reload():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    man = g0.manifest()
    assert set(man["clones"]) == {"0", "1"} and man["gyms"] == ["compiler", "reasoning_gym"]
    assert man["stage_schedule"]["name"] == "sched_v_test"
    assert man["runtime_hashes"]["run_life_v2.py"] and man["runtime_hashes"]["clone_coordinator.py"]
    assert man["runtime_hashes"]["agentic_parent.py"], "parent harness in mechanism_version"
    fns = FakeFns()
    rows0, rows1 = rows_for(0, 3), rows_for(1, 2)
    result = {}

    def clone1():
        assert g1.write_slice(1, rows1, "reasoning_gym", "dom1") == len(rows1)
        result["v1"] = g1.wait_for_verdict(1, timeout_s=10)
        g1.advance_cursor_if_pooled(1)
        g1.attach_round_to_life(1, life1, os.path.join(life1, "sleep_0008"))

    t = threading.Thread(target=clone1)
    t.start()
    assert g0.write_slice(1, rows0, "compiler", "dom0") == len(rows0)
    v0 = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn,
                             barrier_timeout_s=10, log=lambda m: None)
    t.join(10)
    assert v0 == "DONE" and result["v1"] == "DONE"
    assert (fns.compiles, fns.trains, fns.gates) == (1, 1, 1)
    # pooled: both slices, every row stamped with provenance, cumulative file
    pooled = cc._read_jsonl(os.path.join(g0.dir, "pooled_ledger.jsonl"))
    assert len(pooled) == len(rows0) + len(rows1)
    assert {r["clone_id"] for r in pooled} == {0, 1}
    assert {r["gym"] for r in pooled} == {"compiler", "reasoning_gym"}
    assert all(r["round"] == 1 for r in pooled)
    assert len(fns.last_rows) == len(pooled)
    rec = g0.read_record(1)
    assert rec["present"] == [0, 1] and rec["skipped"] == [] and rec["verdict"] == "DONE"
    assert rec["gate"]["per_clone"]["1"]["gym"] == "reasoning_gym"
    assert "pending_verdict" not in rec
    # both clones' EXISTING reload path sees the shared adapter
    g0.advance_cursor_if_pooled(1)
    g0.attach_round_to_life(1, life0, os.path.join(life0, "sleep_0012"))
    for life, sd in ((life0, "sleep_0012"), (life1, "sleep_0008")):
        ad = latest_adapter(life)
        assert ad == os.path.join(life, sd, "adapter"), ad
        assert os.path.realpath(ad) == os.path.realpath(g0.adapter_dir(1))
        bp = os.path.join(life, sd, "waking_brief.txt")
        assert open(bp).read().startswith("brief")
        assert not os.path.islink(bp), "the brief is COPIED (parent allow-list)"
        assert os.path.islink(os.path.join(life, sd, "adapter"))
        gj = json.load(open(os.path.join(life, sd, "gate.json")))
        assert gj["verdict"] == "DONE" and gj["round"] == 1
    assert g0.cursor() == len(rows0) and g1.cursor() == len(rows1)
    # the coordinator wrote both cursors when it pooled
    assert g0.cursor(1) == len(rows1)
    # next round: slices contain only new rows
    rows0b = rows0 + rows_for(0, 2, start_tick=5)
    assert g0.write_slice(2, rows0b, "compiler") == len(rows0b) - len(rows0)
    # the trainer's staging dir was promoted (renamed away)
    assert not os.path.exists(g0.staging_dir(1))


def test_degrade_path_skips_late_clone_and_round_completes():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    fns = FakeFns()
    rows0 = rows_for(0, 2)
    g0.write_slice(1, rows0, "compiler")
    logs = []
    g0.log = logs.append
    v = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn,
                            barrier_timeout_s=0.3, log=logs.append)
    assert v == "DONE"
    rec = g0.read_record(1)
    assert rec["present"] == [0] and rec["skipped"] == [1]
    assert any("BARRIER TIMEOUT" in m and "skipping clones [1]" in m for m in logs)
    assert len(fns.last_rows) == len(rows0)
    assert g0.advance_cursor_if_pooled(1) and g0.cursor() == len(rows0)
    # the late clone arrives, finds the verdict, reloads, keeps its cursor
    rows1 = rows_for(1, 2)
    g1.write_slice(1, rows1, "reasoning_gym")
    assert g1.wait_for_verdict(1, timeout_s=1) == "DONE"
    assert g1.advance_cursor_if_pooled(1) is False and g1.cursor() == 0
    g1.attach_round_to_life(1, life1, os.path.join(life1, "sleep_0004"))
    assert latest_adapter(life1) is not None
    # round 2: its unpooled rows ride along; both present now
    rows1b = rows1 + rows_for(1, 1, start_tick=9)
    assert g1.write_slice(2, rows1b, "reasoning_gym") == len(rows1b)
    g0.write_slice(2, rows0 + rows_for(0, 1, start_tick=9), "compiler")
    v2 = cc.coordinate_round(g0, 2, fns.compile_fn, fns.train_fn, fns.gate_fn,
                             barrier_timeout_s=1, log=lambda m: None)
    assert v2 == "DONE" and g0.read_record(2)["present"] == [0, 1]
    pooled = cc._read_jsonl(os.path.join(g0.dir, "pooled_ledger.jsonl"))
    assert len(pooled) == len(rows0) + 4 + len(rows1b)
    assert g1.advance_cursor_if_pooled(2) and g1.cursor() == len(rows1b)
    # the prior corpus chains across rounds
    c2 = json.load(open(os.path.join(g0.round_dir(2), "corpus.json")))
    assert len(c2["corpus"]) > len(json.load(open(os.path.join(g0.round_dir(1), "corpus.json")))["corpus"])


def test_rejection_names_the_failing_clone_and_keeps_previous_adapter():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    fns = FakeFns(gate_ok=False, reason="SCORE_clone1+BREVITY_clone1")
    g0.write_slice(1, rows_for(0, 1), "compiler")
    g1.write_slice(1, rows_for(1, 1), "reasoning_gym")
    v = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn,
                            barrier_timeout_s=1, log=lambda m: None)
    assert v == "REJECTED_SCORE_clone1+BREVITY_clone1"
    assert os.path.exists(os.path.join(g0.adapter_dir(1), v))
    assert g1.wait_for_verdict(1, 1) == v
    g1.attach_round_to_life(1, life1, os.path.join(life1, "sleep_0004"))
    assert latest_adapter(life1) is None          # no DONE: previous stays
    assert json.load(open(os.path.join(life1, "sleep_0004", "gate.json")))["verdict"] == v
    assert g0.committed_rounds() == []
    # a failed trainer is its own rejection reason
    fns2 = FakeFns()
    fns2.train_fn = lambda c, o: 1
    g0.write_slice(2, rows_for(0, 2), "compiler")
    g1.write_slice(2, rows_for(1, 2), "reasoning_gym")
    assert cc.coordinate_round(g0, 2, fns2.compile_fn, fns2.train_fn, fns2.gate_fn,
                               1, log=lambda m: None) == "REJECTED_TRAIN"
    assert fns2.gates == 0


def test_restart_from_markers():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    fns = FakeFns(train_fail_once=True)
    g0.write_slice(1, rows_for(0, 2), "compiler")
    g1.write_slice(1, rows_for(1, 2), "reasoning_gym")
    try:
        cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                            log=lambda m: None)
    except RuntimeError as e:
        assert "simulated" in str(e)
    else:
        raise AssertionError("simulated crash did not propagate")
    assert fns.compiles == 1 and os.path.exists(os.path.join(g0.round_dir(1), "COMPILED"))
    assert g0.verdict(1) is None
    # process restarts: the round resumes after the compile, no re-pooling
    v = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                            log=lambda m: None)
    assert v == "DONE" and (fns.compiles, fns.trains, fns.gates) == (1, 2, 1)
    pooled = cc._read_jsonl(os.path.join(g0.dir, "pooled_ledger.jsonl"))
    assert len(pooled) == len(rows_for(0, 2)) + len(rows_for(1, 2))   # not doubled
    # a finished round re-entered does nothing
    v2 = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                             log=lambda m: None)
    assert v2 == "DONE" and (fns.compiles, fns.trains, fns.gates) == (1, 2, 1)
    # re-writing a slice is a no-op; re-attaching is idempotent
    assert g0.write_slice(1, rows_for(0, 99), "compiler") == len(rows_for(0, 2))
    sd = os.path.join(life0, "sleep_0008")
    g0.attach_round_to_life(1, life0, sd)
    g0.attach_round_to_life(1, life0, sd)
    assert latest_adapter(life0) == os.path.join(sd, "adapter")
    # a restarted coordinator that already has CANDIDATE only gates
    root2 = tempfile.mkdtemp()
    h0, _ = make_group(root2, 0, count=1)
    h0.write_slice(1, rows_for(0, 1), "compiler")
    f3 = FakeFns()
    f3.gate_fn = lambda a, s: (_ for _ in ()).throw(RuntimeError("gate crash"))
    try:
        cc.coordinate_round(h0, 1, f3.compile_fn, f3.train_fn, f3.gate_fn, 1,
                            log=lambda m: None)
    except RuntimeError:
        pass
    assert os.path.exists(os.path.join(h0.adapter_dir(1), "CANDIDATE"))
    f4 = FakeFns()
    assert cc.coordinate_round(h0, 1, f4.compile_fn, f4.train_fn, f4.gate_fn, 1,
                               log=lambda m: None) == "DONE"
    assert (f4.compiles, f4.trains, f4.gates) == (0, 0, 1)
    # a crash after the trainer finished but before promotion: no retrain
    root3 = tempfile.mkdtemp()
    k0, _ = make_group(root3, 0, count=1)
    k0.write_slice(1, rows_for(0, 1), "compiler")
    f5 = FakeFns()
    f5.compile_fn(cc._read_jsonl(k0.slice_path(1, 0)), k0.round_dir(1), [])
    cc._touch(os.path.join(k0.round_dir(1), "COMPILED"))
    f5.train_fn("unused", k0.staging_dir(1))          # DONE in the staging dir
    assert k0.verdict(1) is None
    f6 = FakeFns()
    assert cc.coordinate_round(k0, 1, f6.compile_fn, f6.train_fn, f6.gate_fn, 1,
                               log=lambda m: None) == "DONE"
    assert (f6.compiles, f6.trains, f6.gates) == (0, 0, 1)


def test_provenance_ledger_and_probe_summary():
    root = tempfile.mkdtemp()
    led = cc.ProvenanceLedger(os.path.join(root, "ledger.jsonl"), clone_id=3,
                              gym="reasoning_gym", exposure_domain="rg:x")
    led.append(dict(kind="act", episode_id="e", tick=1, score=0.2))
    led.append(dict(kind="thought", episode_id="e", tick=1, note="n", gym="keep"))
    rows = led.rows()
    assert rows[0]["clone_id"] == 3 and rows[0]["gym"] == "reasoning_gym"
    assert rows[0]["exposure_domain"] == "rg:x"
    assert rows[1]["gym"] == "keep", "setdefault: an explicit field is kept"
    with open(os.path.join(root, "probe_t.json"), "w") as f:
        json.dump(dict(results={"a": 0.5, "b": 0.7}, mean=0.6), f)
    with open(os.path.join(root, "probe_t.ledger.jsonl"), "w") as f:
        for _ in range(6):
            f.write(json.dumps(dict(kind="thought")) + "\n")
        f.write(json.dumps(dict(kind="act")) + "\n")
    assert cc.probe_summary(root, "t") == (0.6, 3.0)
    assert cc.probe_summary(root, "missing") == (None, None)


# --- review fixes (2026-09-10) -------------------------------------------------------
def test_no_done_marker_is_visible_before_the_gate():
    """FATAL fix: the trainer's DONE never appears under adapter/ before the
    gate. A non-coordinator polling wait_for_verdict during the trainer's
    teardown and during the gate sees nothing; it receives the FINAL verdict."""
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    g0.write_slice(1, rows_for(0, 2), "compiler")
    g1.write_slice(1, rows_for(1, 2), "reasoning_gym")
    fns = FakeFns()
    seen, observed, early = {}, [], []

    def poller():
        observed.append(g1.wait_for_verdict(1, timeout_s=10))

    def slow_train(corpus_path, out_dir):
        fns.train_fn(corpus_path, out_dir)            # writes DONE ...
        t0 = time.monotonic()                          # ... then tears down
        while time.monotonic() - t0 < 0.3:
            v = g1.verdict(1)
            if v is not None:
                early.append(v)
            time.sleep(0.01)
        seen["adapter_dir_during_train"] = os.path.isdir(g0.adapter_dir(1))
        return 0

    def slow_gate(adapter_dir, specs):
        seen["listing_in_gate"] = sorted(os.listdir(adapter_dir))
        t0 = time.monotonic()
        while time.monotonic() - t0 < 0.2:
            v = g1.verdict(1)
            if v is not None:
                early.append(v)
            time.sleep(0.01)
        per = {str(k): dict(gym=s["gym"], candidate=0.1, floor=0.4,
                            score_ok=False, brevity_ok=True, canary_ok=True)
               for k, s in specs.items()}
        return dict(ok=False, reason="SCORE_clone1", per_clone=per)

    t = threading.Thread(target=poller)
    t.start()
    v = cc.coordinate_round(g0, 1, fns.compile_fn, slow_train, slow_gate, 5,
                            log=lambda m: None)
    t.join(10)
    assert v == "REJECTED_SCORE_clone1"
    assert early == [], f"a verdict was visible before the gate closed: {early}"
    assert observed == [v], observed
    assert seen["adapter_dir_during_train"] is False, "trainer wrote into adapter.train"
    assert "DONE" not in seen["listing_in_gate"] and "CANDIDATE" in seen["listing_in_gate"]
    assert not os.path.exists(g0.staging_dir(1))
    rec = g0.read_record(1)
    assert rec["verdict"] == v and rec["gate"]["per_clone"]["1"]["score_ok"] is False
    # the non-coordinator attaches the rejection, keeps no adapter
    g1.attach_round_to_life(1, life1, os.path.join(life1, "sleep_0004"))
    assert latest_adapter(life1) is None


def test_round_timeout_then_late_coordinator_no_duplicates_and_catch_up():
    """MAJOR fix: a clone whose verdict wait times out keeps living; when the
    coordinator later pools its slice nothing is pooled twice (ledger-index
    de-dup), and the missed round is attached at the clone's next sleep, so
    a REJECTED round after a missed DONE leaves both clones on the same
    adapter (no lineage fork)."""
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    fns = FakeFns()
    r1 = rows_for(1, 2)
    sd1 = os.path.join(life1, "sleep_0004")
    g1.write_slice(1, r1, "reasoning_gym")
    assert g1.wait_for_verdict(1, timeout_s=0.05) is None       # coordinator absent
    assert g1.advance_cursor_if_pooled(1) is False
    assert g1.attach_round_to_life(1, life1, sd1) is None
    assert os.path.exists(os.path.join(sd1, "CLONE_PENDING"))
    assert g1.attach_missed_rounds(life1) == [], "no verdict yet: nothing to attach"
    # clone 1 reaches its NEXT sleep before the coordinator pooled round 1:
    # its slice 2 starts from the stale cursor (overlaps slice 1)
    r1b = r1 + rows_for(1, 1, start_tick=9)
    sd2 = os.path.join(life1, "sleep_0008")
    assert g1.write_slice(2, r1b, "reasoning_gym") == len(r1b)
    # the coordinator arrives: round 1 (DONE) with both slices present
    g0.write_slice(1, rows_for(0, 2), "compiler")
    assert cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 5,
                               log=lambda m: None) == "DONE"
    assert g0.read_record(1)["present"] == [0, 1]
    assert g0.cursor(1) == len(r1), "the coordinator wrote clone 1's cursor"
    g0.advance_cursor_if_pooled(1)
    g0.attach_round_to_life(1, life0, os.path.join(life0, "sleep_0004"))
    # round 2 is REJECTED; clone 1's overlapping slice is de-duplicated
    fns2 = FakeFns(gate_ok=False, reason="SCORE_clone0")
    logs = []
    g0.log = logs.append
    g0.write_slice(2, rows_for(0, 2) + rows_for(0, 1, start_tick=9), "compiler")
    assert cc.coordinate_round(g0, 2, fns2.compile_fn, fns2.train_fn, fns2.gate_fn, 5,
                               log=lambda m: None) == "REJECTED_SCORE_clone0"
    assert any("already pooled" in m for m in logs), logs
    pooled = cc._read_jsonl(os.path.join(g0.dir, "pooled_ledger.jsonl"))
    c1 = [(r["episode_id"], r["tick"], r["kind"]) for r in pooled if r["clone_id"] == 1]
    assert len(c1) == len(set(c1)) == len(r1b), "every clone-1 row pooled exactly once"
    assert g0.cursor(1) == len(r1b)
    g0.attach_round_to_life(2, life0, os.path.join(life0, "sleep_0008"))
    # clone 1 wakes to its next sleep: the missed round 1 is attached first,
    # then round 2 (rejected) -> both clones on round 1's adapter
    assert g1.wait_for_verdict(2, 1) == "REJECTED_SCORE_clone0"
    late = g1.attach_missed_rounds(life1)
    assert [(rr, v, d) for rr, v, d in late] == [(1, "DONE", "sleep_0004")]
    assert not os.path.exists(os.path.join(sd1, "CLONE_PENDING"))
    assert os.path.exists(os.path.join(sd1, "CLONE_ROUND"))
    g1.attach_round_to_life(2, life1, sd2)
    assert latest_adapter(life1) == os.path.join(sd1, "adapter")
    assert os.path.realpath(latest_adapter(life1)) == os.path.realpath(latest_adapter(life0))
    assert g1.cursor() == len(r1b)
    # a third slice carries only new rows
    assert g1.write_slice(3, r1b + rows_for(1, 1, start_tick=20), "reasoning_gym") == 4
    assert g1.attach_missed_rounds(life1) == [], "idempotent"


def test_pool_recovers_a_torn_append_and_never_duplicates():
    root = tempfile.mkdtemp()
    g0, _ = make_group(root, 0)
    g1, _ = make_group(root, 1)
    rows0, rows1 = rows_for(0, 2), rows_for(1, 3)
    g0.write_slice(1, rows0, "compiler")
    g1.write_slice(1, rows1, "reasoning_gym")
    pooled = g0.pool(1, [0])
    assert len(pooled) == len(rows0)
    pl = os.path.join(g0.dir, "pooled_ledger.jsonl")
    size = os.path.getsize(pl)
    # a previous coordinator process died mid-append for clone 1
    cc._write_json(os.path.join(g0.round_dir(1), "POOLING_1"),
                   dict(clone_id=1, round=1, bytes_before=size, start=0,
                        end=len(rows1), n=len(rows1)))
    with open(pl, "a") as f:
        f.write(json.dumps(rows1[0]) + "\n")
        f.write('{"torn": "lin')
    logs = []
    g0.log = logs.append
    out = g0.pool(1, [0, 1])
    assert any("torn" in m for m in logs)
    assert len(out) == len(rows0) + len(rows1)
    keys = [(r["clone_id"], r["episode_id"], r["tick"], r["kind"]) for r in out]
    assert len(keys) == len(set(keys))
    assert os.path.exists(os.path.join(g0.round_dir(1), "POOLED_1"))
    assert not os.path.exists(os.path.join(g0.round_dir(1), "POOLING_1"))
    assert g0.cursor(1) == len(rows1) and g0.cursor(0) == len(rows0)
    assert g0.pool(1, [0, 1]) == out, "idempotent"


def test_gate_stats_persist_before_the_marker():
    root = tempfile.mkdtemp()
    g0, _ = make_group(root, 0, count=1)
    g0.write_slice(1, rows_for(0, 1), "compiler")
    fns = FakeFns()
    real_replace = os.replace

    def flaky(src, dst):
        if os.path.basename(src) == "CANDIDATE":
            raise OSError("simulated crash before the verdict marker")
        return real_replace(src, dst)

    cc.os.replace = flaky
    try:
        try:
            cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                                log=lambda m: None)
        except OSError:
            pass
        else:
            raise AssertionError("simulated crash did not propagate")
    finally:
        cc.os.replace = real_replace
    rec = g0.read_record(1)
    assert rec["gate"]["per_clone"]["0"]["candidate"] == 0.5
    assert rec["pending_verdict"] == "DONE" and "verdict" not in rec
    assert g0.verdict(1) is None
    # restart: the recorded gate is applied, no second gate probe
    assert cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                               log=lambda m: None) == "DONE"
    assert (fns.compiles, fns.trains, fns.gates) == (1, 1, 1)
    rec = g0.read_record(1)
    assert rec["verdict"] == "DONE" and "pending_verdict" not in rec and rec["gate"]


def test_register_refuses_unsafe_groups():
    base = dict(exam_set=["e1"], canary_set=["c1"], budget_ticks=3, seed=0,
                arm="B", rank=8)
    # no gate set: the coordinator would gate on the exam panel
    root = tempfile.mkdtemp()
    g = cc.CloneGroup(os.path.join(root, "g"), 0, 2, log=lambda m: None)
    for bad in (None, []):
        try:
            g.register(gym="compiler", gate_set=bad, exposure_domain="compiler_gym:x", **base)
        except RuntimeError as e:
            assert "gate set" in str(e) and "--gate-panel" in str(e)
        else:
            raise AssertionError("clone without a gate set accepted")
    # deployment gym mixed with a trait gym: refused without the flag
    g.register(gym="compiler", gate_set=["p1"], exposure_domain="compiler_gym:llvm-v0", **base)
    g1 = cc.CloneGroup(os.path.join(root, "g"), 1, 2, log=lambda m: None)
    try:
        g1.register(gym="reasoning_gym", gate_set=["q1"], exposure_domain="reasoning_gym:a,b", **base)
    except RuntimeError as e:
        assert "target-blind" in str(e) and "--allow-deployment-gym" in str(e)
    else:
        raise AssertionError("mixed group accepted")
    assert "1" not in g.manifest()["clones"] and "not_target_blind" not in g.manifest()
    g1.register(gym="reasoning_gym", gate_set=["q1"], exposure_domain="reasoning_gym:a,b",
                allow_deployment_gym=True, **base)
    man = g.manifest()
    assert set(man["clones"]) == {"0", "1"} and "development group" in man["not_target_blind"]
    # the other order: a trait clone first, then an unallowed compiler clone
    root2 = tempfile.mkdtemp()
    h1 = cc.CloneGroup(os.path.join(root2, "g"), 1, 2, log=lambda m: None)
    h1.register(gym="reasoning_gym", gate_set=["q1"], exposure_domain="reasoning_gym:a", **base)
    h0 = cc.CloneGroup(os.path.join(root2, "g"), 0, 2, log=lambda m: None)
    try:
        h0.register(gym="compiler", gate_set=["p1"], exposure_domain="compiler_gym:llvm-v0", **base)
    except RuntimeError as e:
        assert "target-blind" in str(e)
    else:
        raise AssertionError("mixed group accepted")
    # two trait clones: fine, no label
    h0.register(gym="reasoning_gym", gate_set=["q2"], exposure_domain="reasoning_gym:c", **base)
    assert "not_target_blind" not in h0.manifest()
    # different round counts: refused with the helper named
    root3 = tempfile.mkdtemp()
    k0 = cc.CloneGroup(os.path.join(root3, "g"), 0, 2, log=lambda m: None)
    k0.register(gym="reasoning_gym", gate_set=["q"], exposure_domain="reasoning_gym:a", n_rounds=16, **base)
    k1 = cc.CloneGroup(os.path.join(root3, "g"), 1, 2, log=lambda m: None)
    try:
        k1.register(gym="reasoning_gym", gate_set=["q"], exposure_domain="reasoning_gym:b", n_rounds=8, **base)
    except RuntimeError as e:
        assert "rounds" in str(e) and "episodes_for_rounds" in str(e)
    else:
        raise AssertionError("unequal round counts accepted")
    k1.register(gym="reasoning_gym", gate_set=["q"], exposure_domain="reasoning_gym:b", n_rounds=16, **base)
    # a clone_count / coordinator that disagrees with the manifest
    try:
        cc.CloneGroup(os.path.join(root3, "g"), 1, 3, log=lambda m: None).register(
            gym="reasoning_gym", gate_set=["q"], exposure_domain="reasoning_gym:b", **base)
    except RuntimeError as e:
        assert "clone_count" in str(e)
    else:
        raise AssertionError("clone_count mismatch accepted")
    try:
        cc.CloneGroup(os.path.join(root3, "g"), 1, 2, coordinator_id=1,
                      log=lambda m: None).register(
            gym="reasoning_gym", gate_set=["q"], exposure_domain="reasoning_gym:b", **base)
    except RuntimeError as e:
        assert "coordinator" in str(e)
    else:
        raise AssertionError("coordinator mismatch accepted")


def test_manifest_carries_no_hosts_urls_or_home_paths():
    root = tempfile.mkdtemp()
    g = cc.CloneGroup(os.path.join(root, "group"), 0, 2, log=lambda m: None)
    flags = dict(parent_url="http://[REDACTED_HOST]:8011/v1",
                 parent_model="Qwen/Qwen2.5-32B-Instruct",
                 life_dir="/home/rohing/v6_out/L_B_seed0",
                 clone_group="/home/rohing/v6_out/group1",
                 gate_panel="/Users/rohing/panels/v1b.json", host="[REDACTED_ADDRESS]",
                 parent_api_key="[REDACTED_SECRET]")
    g.register(gym="compiler", life_dir=flags["life_dir"], gate_set=["g"],
               exam_set=["e"], canary_set=["c"], budget_ticks=16, seed=0, arm="B",
               exposure_domain="compiler_gym:x", rank=8, schedule=None,
               flags={k: v for k, v in flags.items() if "key" not in k.lower()})
    man = open(os.path.join(root, "group", "manifest.json")).read()
    spec = open(os.path.join(root, "group", "clones", "clone_0.json")).read()
    for needle in ("gpu-node-07", "dgx.internal", "/home/rohing", "/Users/rohing",
                   "[REDACTED_ADDRESS]", "SHOULD_BE_FILTERED", "8011"):
        assert needle not in man and needle not in spec, needle
    m = json.loads(man)
    assert m["clones"]["0"]["life_name"] == "L_B_seed0" and "life_dir" not in m["clones"]["0"]
    assert m["clones"]["0"]["flags"]["parent_model"] == "Qwen/Qwen2.5-32B-Instruct"
    assert m["clones"]["0"]["flags"]["parent_url"] == "<URL>"


def test_barrier_does_not_wait_for_finished_clones():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0)
    g1, life1 = make_group(root, 1)
    g1.mark_life_done()
    assert g0.finished_clones() == [1]
    g0.write_slice(1, rows_for(0, 2), "compiler")
    fns = FakeFns()
    logs = []
    t0 = time.monotonic()
    v = cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn,
                            barrier_timeout_s=30, log=logs.append)
    assert v == "DONE" and time.monotonic() - t0 < 5, "did not wait for the finished clone"
    rec = g0.read_record(1)
    assert rec["present"] == [0] and rec["skipped"] == [] and rec["finished"] == [1]
    # a finished clone whose last slice IS present gets pooled
    root2 = tempfile.mkdtemp()
    h0, _ = make_group(root2, 0)
    h1, _ = make_group(root2, 1)
    h1.write_slice(1, rows_for(1, 1), "reasoning_gym")
    h1.mark_life_done()
    h0.write_slice(1, rows_for(0, 1), "compiler")
    assert cc.coordinate_round(h0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 30,
                               log=lambda m: None) == "DONE"
    assert h0.read_record(1)["present"] == [0, 1] and h0.read_record(1)["finished"] == []


def test_waking_brief_copy_is_readable_by_the_parent_view():
    root = tempfile.mkdtemp()
    g0, life0 = make_group(root, 0, count=1)
    g0.write_slice(1, rows_for(0, 1), "compiler")
    fns = FakeFns()
    assert cc.coordinate_round(g0, 1, fns.compile_fn, fns.train_fn, fns.gate_fn, 1,
                               log=lambda m: None) == "DONE"
    sd = os.path.join(life0, "sleep_0032")
    g0.attach_round_to_life(1, life0, sd)
    with open(os.path.join(life0, "ledger.jsonl"), "w") as f:
        for r in rows_for(0, 1):
            f.write(json.dumps(r) + "\n")
    from organism_v6 import agentic_parent as ap
    view = ap.ChildView(life0, sleep_dir=sd, society_dir=os.path.join(root, "soc"))
    wb = view.call("waking_brief")
    assert wb.startswith("[sleep_0032]") and "brief from the pooled sleep" in wb, wb
    assert "sleep_0032/waking_brief.txt" in view.call("list_files")
    assert "sleep_0032/gate.json" in view.call("list_files")
    gd = view.gate_decisions(2)
    assert gd[-1]["write_verdict"] == "DONE"


def _write_gate_panel(root):
    import golden_harness as gh
    p = os.path.join(root, "gate_panel.json")
    with open(p, "w") as f:
        json.dump(gh.GATE_PANEL, f)
    return p


def _run_clones(root, specs, common, timeout=600):
    """specs: [(clone id, gym, extra argv)]. Returns [(proc, output)]."""
    group = os.path.join(root, "group")
    procs = []
    for k, gym, extra in specs:
        argv = [sys.executable, os.path.join(HERE, "clone_life_driver.py"),
                "--life-dir", os.path.join(root, f"life_{k}"), "--seed", str(k),
                "--gym", gym, "--clone-id", str(k), "--clone-group", group] + \
            common + list(extra)
        procs.append(subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True))
    outs = [p.communicate(timeout=timeout)[0] for p in procs]
    return list(zip(procs, outs))


COMMON = ["--arm", "B", "--episodes", "8", "--sleep-every", "4",
          "--probe-every", "8", "--budget-ticks", "2", "--wake-batch", "4",
          "--rank", "8", "--clone-count", "2",
          "--clone-barrier-timeout", "120", "--clone-round-timeout", "240"]


def test_end_to_end_two_clone_lives_in_the_fake_world():
    """Two run_life_v2 processes share one adapter lineage for two rounds: a
    TARGET-BLIND group of two reasoning_gym clones when the package is
    importable (the per-sleep deployment-vocabulary scan is enforced and
    clean), else two compiler clones with the disjoint gate panel."""
    rg = _rg_available()
    root = tempfile.mkdtemp()
    group = os.path.join(root, "group")
    panel = _write_gate_panel(root)
    gyms = ("reasoning_gym", "reasoning_gym") if rg else ("compiler", "compiler")
    extra = [] if rg else ["--gate-panel", panel]
    runs = _run_clones(root, [(0, gyms[0], extra), (1, gyms[1], extra)], COMMON)
    for p, o in runs:
        assert p.returncode == 0, o[-3000:]
        assert "CLONE_DRIVER_DONE" in o
    man = json.load(open(os.path.join(group, "manifest.json")))
    assert set(man["clones"]) == {"0", "1"} and "not_target_blind" not in man
    assert man["clones"]["0"]["n_rounds"] == man["clones"]["1"]["n_rounds"] == 2
    spec0 = json.load(open(os.path.join(group, "clones", "clone_0.json")))
    assert spec0["compile_vocab"]["noun"] == ("Puzzle" if rg else "Program")
    for r in (1, 2):
        rec = json.load(open(os.path.join(group, f"round_{r:04d}", "round.json")))
        assert rec["verdict"] == "DONE", rec
        assert rec["present"] == [0, 1] and rec["skipped"] == []
        assert set(rec["gate"]["per_clone"]) == {"0", "1"}
        assert all(v["score_ok"] and v["brevity_ok"] and v["canary_ok"]
                   for v in rec["gate"]["per_clone"].values())
        assert os.path.exists(os.path.join(group, f"round_{r:04d}", "adapter", "DONE"))
        assert not os.path.exists(os.path.join(group, f"round_{r:04d}", "adapter.train"))
        assert os.path.exists(os.path.join(group, f"round_{r:04d}", "corpus.json"))
    for k in (0, 1):
        life = os.path.join(root, f"life_{k}")
        assert os.path.exists(os.path.join(life, "LIFE_DONE"))
        assert os.path.exists(os.path.join(group, "clones", f"LIFE_DONE_{k}"))
        ad = latest_adapter(life)
        assert ad and os.path.realpath(ad) == os.path.realpath(
            os.path.join(group, "round_0002", "adapter"))
        rows = [json.loads(l) for l in open(os.path.join(life, "ledger.jsonl"))]
        assert rows and all(r.get("clone_id") == k for r in rows)
        assert {r.get("gym") for r in rows} == {gyms[k]}
        # the adapter-ON/OFF probes of the life ran on the shared adapter
        assert os.path.exists(os.path.join(life, "probe_ep0008.json"))
        assert os.path.exists(os.path.join(life, "probe_ep0008_adapterOFF.json"))
        # no duplicate frozen-base gate probe in the life dir (the coordinator's is the floor)
        assert not os.path.exists(os.path.join(life, "probe_gate_base.json"))
        # the waking brief is a copy the parent view can read
        sd = os.path.join(life, "sleep_0008")
        assert os.path.exists(os.path.join(sd, "waking_brief.txt"))
        assert not os.path.islink(os.path.join(sd, "waking_brief.txt"))
        assert os.path.islink(os.path.join(sd, "adapter"))
        if rg:
            pj = json.load(open(os.path.join(life, "probe_ep0008.json")))
            assert "family_accuracy" in pj
            scans = [json.loads(l) for l in open(os.path.join(life, "leak_scan.jsonl"))]
            assert [s["round"] for s in scans] == [1, 2]
            assert all(s["clean"] and s["enforced"] and s["applicable"] for s in scans), scans
            brief = open(os.path.join(sd, "waking_brief.txt")).read().lower()
            for w in ("program", "pass", "llvm", "optimiz", "compil"):
                assert w not in brief, (w, brief)
            corpus = json.load(open(os.path.join(group, "round_0002", "corpus.json")))["corpus"]
            assert corpus and not any(w in c.lower() for c in corpus
                                      for w in ("program", "passes", "llvm", "optimiz", "compil")), corpus[:3]
            assert any(c.startswith("Puzzle rg/") for c in corpus)
        else:
            assert not os.path.exists(os.path.join(life, "leak_scan.jsonl")), \
                "the deployment gym writes no leak scan"
    pooled = [json.loads(l) for l in open(os.path.join(group, "pooled_ledger.jsonl"))]
    assert {r["clone_id"] for r in pooled} == {0, 1}
    # nothing pooled twice, nothing lost: clone k's pooled rows (minus the
    # round stamp) ARE clone k's ledger, in order
    for k in (0, 1):
        life_rows = [json.loads(l) for l in open(os.path.join(root, f"life_{k}", "ledger.jsonl"))]
        pooled_k = [{kk: v for kk, v in r.items() if kk != "round"}
                    for r in pooled if r["clone_id"] == k]
        assert pooled_k == life_rows, (k, len(pooled_k), len(life_rows))
    # the coordinator measured a frozen-base floor per clone gym once
    assert os.path.exists(os.path.join(group, "probe_gate_base_clone0.json"))
    assert os.path.exists(os.path.join(group, "probe_gate_base_clone1.json"))
    # the manifest names no host, URL or home path
    man_txt = open(os.path.join(group, "manifest.json")).read()
    assert root not in man_txt and "/Users/" not in man_txt and "/home/" not in man_txt


def test_end_to_end_mixed_group_is_refused_unless_allowed():
    """A compiler clone in a group with a reasoning_gym clone is refused at
    registration; with --allow-deployment-gym on both the DEVELOPMENT group
    runs, is labelled not_target_blind and the trait clone's vocabulary scan
    is recorded, not enforced. Needs the reasoning-gym package."""
    if not _rg_available():
        print("SKIP mixed-group e2e: reasoning_gym not importable")
        return
    root = tempfile.mkdtemp()
    panel = _write_gate_panel(root)
    quick = ["--arm", "B", "--episodes", "4", "--sleep-every", "4", "--probe-every", "4",
             "--budget-ticks", "2", "--wake-batch", "4", "--rank", "8", "--clone-count", "2",
             "--clone-barrier-timeout", "3", "--clone-round-timeout", "3"]
    runs = _run_clones(root, [(0, "compiler", ["--gate-panel", panel]),
                              (1, "reasoning_gym", [])], quick, timeout=300)
    codes = sorted(p.returncode for p, _o in runs)
    assert codes[-1] != 0, "mixed group accepted without --allow-deployment-gym"
    assert any("target-blind" in o for _p, o in runs), [o[-500:] for _p, o in runs]
    root2 = tempfile.mkdtemp()
    panel2 = _write_gate_panel(root2)
    runs2 = _run_clones(root2, [(0, "compiler", ["--gate-panel", panel2, "--allow-deployment-gym"]),
                                (1, "reasoning_gym", ["--allow-deployment-gym"])], COMMON)
    for p, o in runs2:
        assert p.returncode == 0, o[-3000:]
    man = json.load(open(os.path.join(root2, "group", "manifest.json")))
    assert "development group" in man["not_target_blind"]
    scans = [json.loads(l) for l in open(os.path.join(root2, "life_1", "leak_scan.jsonl"))]
    assert scans and all(s["enforced"] is False for s in scans)


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
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
