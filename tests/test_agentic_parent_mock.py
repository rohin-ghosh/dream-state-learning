"""CPU test of the agentic parent harness with a MOCK provider.

Run:  python3 -m pytest tests/test_agentic_parent_mock.py -q
  or: python3 tests/test_agentic_parent_mock.py

Builds a fake life directory (ritualized child, one earlier brief, a gate
decision, forbidden report-panel probe files carrying a sentinel score, a
life.log carrying the same sentinel, symlink aliases of forbidden files, a
sibling child whose brief contains fake internal identifiers, a society
ledger) and exercises: the allow-list file guard (probe_ep*, life.log,
symlinks, probe-gate ledgers, corpus, wake batches), leak-scan fallback with
the quote-back exemption, identifier redaction/fallback, the two-parent merge
with critics that see the evidence, ledger/society/playbook writes, key
masking, the tool-call budget, the room's wall-clock deadline, act/outcome
attribution in both ledger writer orders, crash-safety against torn shared
files and dead rooms, the HTTP request shapes, redirect/proxy/plaintext key
protection and truncation handling against loopback servers (no external
network), and the run_life_v2-compatible return shape and idempotency.
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from organism_v6 import agentic_parent as ap  # noqa: E402
from organism_v6.parent_backend import FALLBACK  # noqa: E402
from organism_v6.parent_brief import REHEARSAL_TAIL  # noqa: E402

SENTINEL = "0.777777"                  # a report-panel score: must never leak
FAKE_IP = "192.168.7.7"
FAKE_EMAIL = "someone@example-corp.internal"
SECRET = "sk-test-SECRET-KEY-0123456789abcdef"
RECIPE = "-mem2reg, -sroa, -gvn, -simplifycfg"
PROGRAMS = ["cbench-v1/crc32", "cbench-v1/bitcount", "cbench-v1/qsort",
            "cbench-v1/adpcm", "cbench-v1/blowfish"]
PREV_BRIEF = ("Every episode you open with the same four steps and expect the "
              "same result.\nBefore you act, name one feature of THIS program "
              "and say what it makes you expect, with a reason and a range.\n"
              "When the result disagrees, write which belief was wrong."
              + REHEARSAL_TAIL)


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _wj(path, obj):
    _w(path, json.dumps(obj, indent=1))


def make_rows(n_instances=40, rehearse_from=32, order="act_first"):
    """order: 'act_first' = organism_v6.batch_loop (run_life_v2: the act row
    is appended while the chunk is parsed, the thought row after it);
    'thought_first' = organism_v6.loop (older lives)."""
    assert order in ("act_first", "thought_first")
    rows = []
    for i in range(n_instances):
        eid = PROGRAMS[i % len(PROGRAMS)]
        for t in range(1, 5):
            score = 0.28 + 0.01 * (t % 2)
            act = dict(kind="act", episode_id=eid, tick=t, action=RECIPE,
                       prediction=0.3, outcome="applied 4 passes",
                       score=score, surprise=score - 0.3, time_cost=1.0)
            note = (f"PREDICT: 0.3\nACT: {RECIPE}\nNOTE: The standard recipe "
                    f"works well; keep using it on this program.\n"
                    f"RECALL: best passes for this program")
            if t == 1 and i >= rehearse_from:
                note = ("NOTE: My ritual was opening with the same four steps; "
                        "instead I name a feature of this program first and "
                        "say what I expect.\n" + note)
            thought = dict(kind="thought", episode_id=eid, tick=t, note=note,
                           prompt="", win=False, had_note=True)
            rows += [act, thought] if order == "act_first" else [thought, act]
    return rows


def make_life(root, overlap_gate_panel=False, order="act_first"):
    """<root>/RP_B_seed0 (child), <root>/R2_B_seed1 (sibling), <root>/society."""
    life = os.path.join(root, "RP_B_seed0")
    rows = make_rows(order=order)
    _w(os.path.join(life, "ledger.jsonl"),
       "".join(json.dumps(r) + "\n" for r in rows))
    for a, b in ((0, 8), (8, 16), (56, 64)):
        _wj(os.path.join(life, f"wake_{a:04d}_{b:04d}.json"), [])
    # run_life_v2 logs report-panel probe means and gate candidates here
    _w(os.path.join(life, "life.log"),
       f"[probe ep0064] mean={SENTINEL}\n[sleep 64] gate cand=0.5000 "
       f"floor=0.4800 (base=0.45, prev=None) chunks/ep 4.0 vs 4.0 -> OK\n")
    s32 = os.path.join(life, "sleep_0032")
    _w(os.path.join(s32, "COMPILED"), "ok\n")
    _wj(os.path.join(s32, "corpus.json"), dict(corpus=[], n_new=0))
    _w(os.path.join(s32, "waking_brief.txt"),
       "Briefing: you learned that order matters; test it.")
    _w(os.path.join(s32, "parent_brief.txt"), PREV_BRIEF)
    _wj(os.path.join(s32, "parent_brief.json"),
        dict(metrics=dict(ritual=True, flags=["same_recipe", "templated_notes"],
                          rehearsal_rate=0.0, n_episodes=32),
             intervened=True, text=PREV_BRIEF, hits=[],
             prompt_version="v3-2026-09-10-repetition",
             parent_model="Qwen/Qwen2.5-14B-Instruct"))
    _wj(os.path.join(s32, "gate.json"),
        dict(candidate=0.5, base=0.45, base_tag="gate_base", prev_on=None,
             floor=0.48, tol=0.02, cand_chunks_per_ep=4.0,
             base_chunks_per_ep=4.0, score_ok=True, brevity_ok=True))
    _w(os.path.join(s32, "adapter", "DONE"), "ok\n")
    gate_programs = {"cbench-v1/crc32": 0.5, "cbench-v1/bitcount": 0.5}
    if overlap_gate_panel:
        gate_programs = {"cbench-v1/susan": 0.5, "cbench-v1/sha": 0.5}
    _wj(os.path.join(life, "probe_gate0032.json"),
        dict(tag="gate0032", results=gate_programs, mean=0.5))
    _wj(os.path.join(life, "probe_gate_base.json"),
        dict(tag="gate_base", results=gate_programs, mean=0.45))
    _w(os.path.join(life, "probe_gate0032.ledger.jsonl"),
       json.dumps(dict(kind="act", episode_id="cbench-v1/crc32", tick=1,
                       score=0.5)) + "\n")
    for tag in ("ep0000", "ep0064", "ep0064_adapterOFF"):
        _wj(os.path.join(life, f"probe_{tag}.json"),
            dict(tag=tag, results={"cbench-v1/susan": float(SENTINEL)},
                 mean=float(SENTINEL)))
    _w(os.path.join(life, "probe_ep0064.ledger.jsonl"),
       json.dumps(dict(kind="act", episode_id="cbench-v1/susan", tick=1,
                       score=float(SENTINEL))) + "\n")
    s64 = os.path.join(life, "sleep_0064")
    _w(os.path.join(s64, "COMPILED"), "ok\n")
    _wj(os.path.join(s64, "corpus.json"), dict(corpus=[], n_new=0))
    _w(os.path.join(s64, "waking_brief.txt"), "Briefing: keep testing order.")
    # sibling: small files only are readable; its brief carries identifiers
    sib = os.path.join(root, "R2_B_seed1")
    _w(os.path.join(sib, "ledger.jsonl"),
       "".join(json.dumps(r) + "\n" for r in make_rows(6)))
    _wj(os.path.join(sib, "wake_0000_0008.json"), [])
    _w(os.path.join(sib, "sleep_0032", "parent_brief.txt"),
       f"Sibling brief. contact {FAKE_EMAIL} at {FAKE_IP} for details."
       + REHEARSAL_TAIL)
    _wj(os.path.join(sib, "sleep_0032", "parent_brief.json"),
        dict(metrics=dict(ritual=False, flags=[], rehearsal_rate=0.2),
             intervened=False))
    _w(os.path.join(sib, "sleep_0032", "adapter", "REJECTED_SCORE"), "ok\n")
    _wj(os.path.join(sib, "probe_ep0064.json"),
        dict(tag="ep0064", results={"cbench-v1/susan": float(SENTINEL)},
             mean=float(SENTINEL)))
    # symlink aliases INSIDE the life dir: an innocent name for a forbidden
    # file, and a name for a file outside the life dir
    os.symlink(os.path.join(life, "probe_ep0064.json"),
               os.path.join(life, "notes.json"))
    os.symlink(os.path.join(sib, "ledger.jsonl"),
               os.path.join(life, "outside.jsonl"))
    os.symlink(os.path.join(life, "probe_ep0064.json"),
               os.path.join(s32, "gate_extra.json"))
    soc = os.path.join(root, "society")
    _w(os.path.join(soc, "ledger.jsonl"), json.dumps(dict(
        ts=1.0, kind="room", child="R2_B_seed1", stage="sleep_0032",
        curriculum_move=dict(move="repeat", reason="x"),
        frontier_estimate=dict(text="can name a feature", confidence=0.3),
        brief="Sibling brief.")) + "\n")
    _w(os.path.join(soc, "playbook.md"),
       "# Parental society playbook (bounded; newest last)\n"
       f"- [R2_B_seed1 sleep_0032] children lock in early; ask for one contrast\n"
       f"- [R2_B_seed1 sleep_0032] a host note {FAKE_IP} should be redacted\n")
    return life, rows, s64, sib, soc


def tool(name, **args):
    return json.dumps(dict(tool=name, args=args))


def final(brief, move="sharpen", conf=0.4, note=None, frontier=None):
    return json.dumps(dict(final=dict(
        brief=brief,
        frontier_estimate=dict(text=frontier or "Can vary its opening move by "
                               "a named program feature after a few episodes.",
                               confidence=conf),
        curriculum_move=dict(move=move, reason="same lesson; sharpen it"),
        evidence=["ledger_tail", "metrics"], society_note=note)))


GOOD_A = final("You open every episode the same way and expect the same result,"
               " whatever the program.\nBefore you act, name one feature of "
               "THIS program and say what it makes you expect, with a range.\n"
               "When the outcome disagrees, write which belief was wrong.\n"
               "Run one deliberate deviation per episode and predict its effect "
               "first; keep going after a flat result, changing something each "
               "time.")
GOOD_B = final("Your notes could be pasted into any episode. Each note must "
               "contrast THIS case with a named earlier one and say when the "
               "lesson applies.\nKeep restating the lesson you began to restate.",
               move="repeat")
MERGED = final("MERGED: You open every episode the same way and expect the same "
               "result, whatever the program.\nBefore you act, name one feature "
               "of THIS program and say what it makes you expect, with a range."
               "\nEach note must contrast THIS case with a named earlier one.\n"
               "Keep going after a flat result, changing something each time.",
               note="Children lock into one opening move; asking for a named "
                    "program feature before acting is the lever.")
ACCEPT = json.dumps(dict(verdict="accept", answers_or_leaks=[], overreach=[],
                         teaches_the_metric=[], persistence="ok",
                         frontier="plausible", suggestion=""))

A_SCRIPT = [tool("ledger_tail", n_episodes=4), tool("metrics"),
            tool("gate_decisions"), GOOD_A]
B_SCRIPT = [tool("other_children"), tool("prior_briefs"), tool("society"),
            tool("waking_brief"), tool("list_files"), GOOD_B]


def two_parent_room(a_key=None, b_raise=None, max_tool_calls=8,
                    client_cls=ap.MockChatClient, **room_kw):
    cfg_a = ap.ProviderConfig("mock", role="A", model="mock-A", api_key=a_key)
    cfg_b = ap.ProviderConfig("mock", role="B", model="mock-B")
    ca = client_cls(script=list(A_SCRIPT), critique=ACCEPT, merge=MERGED,
                    model="mock-A")
    cb = client_cls(script=list(B_SCRIPT), critique=ACCEPT, model="mock-B",
                    raise_with=b_raise)
    room = ap.ParentRoom([cfg_a, cfg_b], clients={"A": ca, "B": cb},
                         max_tool_calls=max_tool_calls, **room_kw)
    return room, ca, cb


def run_room(root, room, life, rows, s64, soc):
    return ap.parent_brief_agentic(life, rows, s64, None, "mock", 32,
                                   room=room, society_dir=soc)


class Tmp:
    def __enter__(self):
        self.root = tempfile.mkdtemp(prefix="agentic_parent_test_")
        return self.root

    def __exit__(self, *a):
        shutil.rmtree(self.root, ignore_errors=True)


def all_messages(*clients):
    return "\n".join(m["content"] for c in clients for call in c.calls
                     for m in call)


def all_written(root):
    """Every regular file under root EXCEPT the fixture's own sentinel
    carriers (probe_* files, life.log) and symlinks (fixture aliases)."""
    out = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            if fn.startswith("probe_") or fn == "life.log" or os.path.islink(p):
                continue
            with open(p, errors="replace") as f:
                out[p] = f.read()
    return out


def ledger_rows(life):
    return [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]


def raises(exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc:
        return True
    raise AssertionError(f"{exc.__name__} not raised by {fn}")


# --- loopback HTTP servers (no external network) -----------------------------
class _Recorder(http.server.BaseHTTPRequestHandler):
    script: list = []          # per-server: [(status, body, extra_headers)]
    seen: list = []            # per-server: recorded requests

    def log_message(self, *a):          # silence
        pass

    def _handle(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = raw.decode("utf-8", "replace")
        self.seen.append(dict(method=self.command, path=self.path,
                              headers={k.lower(): v for k, v in
                                       self.headers.items()}, body=body))
        status, out, extra = (self.script.pop(0) if self.script
                              else (500, {"error": "script exhausted"}, {}))
        data = json.dumps(out).encode()
        self.send_response(status)
        for k, v in extra.items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_POST = do_GET = _handle


def serve(script):
    handler = type("Recorder", (_Recorder,), dict(script=list(script), seen=[]))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, handler, f"http://127.0.0.1:{srv.server_port}/v1"


def stop(*servers):
    for s in servers:
        s.shutdown()
        s.server_close()


def anth_reply(text, stop_reason="end_turn"):
    content = [dict(type="thinking", thinking="")]
    if text is not None:
        content.append(dict(type="text", text=text))
    return dict(id="msg", type="message", role="assistant", content=content,
                stop_reason=stop_reason, usage=dict(output_tokens=1))


def oai_reply(text, finish_reason="stop"):
    return dict(choices=[dict(message=dict(role="assistant", content=text),
                              finish_reason=finish_reason)])


# ---------------------------------------------------------------------------
def test_forbidden_files_enforced():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        v = ap.ChildView(life, rows=rows, sleep_dir=s64, society_dir=soc)
        for bad in ("probe_ep0064.json", "probe_ep0064_adapterOFF.json",
                    "probe_ep0000.json", "probe_ep0064.ledger.jsonl"):
            try:
                v.read_json(bad) if bad.endswith(".json") else v.read_text(bad)
            except ap.ForbiddenRead:
                pass
            else:
                raise AssertionError(f"{bad} was readable")
        try:
            v.read_text("../R2_B_seed1/ledger.jsonl")
        except ap.ForbiddenRead:
            pass
        else:
            raise AssertionError("path traversal was allowed")
        assert v.read_json("probe_gate0032.json")["mean"] == 0.5
        assert v.read_json("sleep_0032/gate.json")["score_ok"] is True
        listing = v.list_files()
        assert "sleep_0032/gate.json" in listing and "probe_gate0032.json" in listing
        assert "probe_ep" not in listing and "probe_ep" not in v.call("list_files")
        gates = v.gate_decisions(6)
        g32 = [g for g in gates if g["sleep"] == "sleep_0032"][0]
        assert g32["write_verdict"] == "DONE" and g32["score_ok"] is True
        assert g32["gate_panel"] == "disjoint" and g32["candidate"] == 0.5
        # a made-up tool name is answered, never raised
        assert v.call("read_probe", {"name": "probe_ep0064.json"}).startswith("ERROR")
    with Tmp() as root:                        # legacy gate on the report panel
        life, rows, s64, _sib, soc = make_life(root, overlap_gate_panel=True)
        v = ap.ChildView(life, rows=rows, sleep_dir=s64, society_dir=soc)
        g32 = [g for g in v.gate_decisions(6) if g["sleep"] == "sleep_0032"][0]
        assert g32["gate_panel"].startswith("report") and "candidate" not in g32
        assert g32["write_verdict"] == "DONE" and g32["brevity_ok"] is True


def test_allow_list_guard_life_log_symlinks_and_listing():
    with Tmp() as root:
        life, rows, s64, sib, soc = make_life(root)
        v = ap.ChildView(life, rows=rows, sleep_dir=s64, society_dir=soc)
        # the life log carries report-panel means: unreadable
        assert raises(ap.ForbiddenRead, v.read_text, "life.log")
        # symlink aliases resolve to what they point at
        assert raises(ap.ForbiddenRead, v.read_json, "notes.json")
        assert raises(ap.ForbiddenRead, v.read_json, "sleep_0032/gate_extra.json")
        assert raises(ap.ForbiddenRead, v.read_text, "outside.jsonl")
        # probe ledgers (even the gate panel's), corpus, wake batches, markers
        assert raises(ap.ForbiddenRead, v.read_text, "probe_gate0032.ledger.jsonl")
        assert raises(ap.ForbiddenRead, v.read_json, "sleep_0032/corpus.json")
        assert raises(ap.ForbiddenRead, v.read_json, "wake_0000_0008.json")
        assert raises(ap.ForbiddenRead, v.read_text, "sleep_0032/COMPILED")
        assert raises(ap.ForbiddenRead, v.read_text, "sleep_0032/adapter/DONE")
        assert raises(ap.ForbiddenRead, v.read_text, ".")
        # what IS readable
        assert v.read_text("ledger.jsonl").startswith("{")
        assert v.read_text("sleep_0032/parent_brief.txt").startswith("Every episode")
        assert v.read_text("sleep_0032/waking_brief.txt").startswith("Briefing")
        assert v.read_json("sleep_0032/parent_brief.json")["intervened"] is True
        listing = v.list_files().splitlines()
        for shown in ("ledger.jsonl", "probe_gate0032.json", "probe_gate_base.json",
                      "sleep_0032/gate.json", "sleep_0032/parent_brief.txt",
                      "sleep_0032/parent_brief.json", "sleep_0032/waking_brief.txt",
                      "sleep_0064/waking_brief.txt"):
            assert shown in listing, shown
        for hidden in ("life.log", "notes.json", "outside.jsonl",
                       "sleep_0032/gate_extra.json", "sleep_0032/corpus.json",
                       "sleep_0032/COMPILED", "probe_gate0032.ledger.jsonl",
                       "probe_ep0064.json", "probe_ep0064.ledger.jsonl"):
            assert hidden not in listing, hidden
        assert not any(l.startswith("wake_") for l in listing)
        assert not ap.is_allowed_relpath("sleep_0032/adapter/DONE")
        assert not ap.is_allowed_relpath("probe_gate0032.ledger.jsonl")
        assert ap.is_allowed_relpath("probe_gate0032.json")
        # a life dir reached through a symlink still works (realpath both sides)
        link = os.path.join(root, "link_life")
        os.symlink(life, link)
        v2 = ap.ChildView(link, rows=rows, sleep_dir=s64, society_dir=soc)
        assert v2.read_json("sleep_0032/gate.json")["score_ok"] is True
        assert raises(ap.ForbiddenRead, v2.read_json, "notes.json")
        # the sibling summary path is guarded the same way
        s = ap._life_summary(sib)
        assert s["child"] == "R2_B_seed1" and s["latest_brief"].startswith("Sibling")
        assert SENTINEL not in json.dumps(s)


def test_sentinel_score_never_reaches_parents_or_ledgers():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = two_parent_room()
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["intervened"] is True
        assert SENTINEL not in all_messages(ca, cb)
        for path, text in all_written(root).items():
            assert SENTINEL not in text, path
        # the parents did read what they may: the child's own words, the gate
        msgs = all_messages(ca, cb)
        assert "TOOL RESULT ledger_tail" in msgs and RECIPE in msgs
        assert '"write_verdict": "DONE"' in msgs
        assert "life.log" not in msgs and "notes.json" not in msgs


def test_ledger_tail_attribution_in_both_writer_orders():
    def rows_for(order):
        # program P: instance 1 = ticks 1..3 (scores .1 .2 .3), instance 2 =
        # ticks 1..2 (scores .05 .15); program Q interleaved (wake batches)
        plan = [("P", 1, 0.1), ("Q", 1, 0.9), ("P", 2, 0.2), ("Q", 2, 0.8),
                ("P", 3, 0.3), ("P", 1, 0.05), ("Q", 1, 0.7), ("P", 2, 0.15)]
        out = []
        for eid, t, s in plan:
            act = dict(kind="act", episode_id=eid, tick=t, action="x", score=s,
                       prediction=0.5, surprise=s - 0.5)
            th = dict(kind="thought", episode_id=eid, tick=t,
                      note=f"NOTE: {eid} chunk {t} thinking")
            out += [act, th] if order == "act_first" else [th, act]
            if eid == "P" and t == 3:                  # a note row in between
                out.append(dict(kind="note", episode_id=eid, tick=t, note="n"))
        return out

    for order in ("act_first", "thought_first"):
        inst = ap._instances_with_acts(rows_for(order))
        assert list(inst) == [("P", 1), ("Q", 1), ("P", 2), ("Q", 2)], (order, list(inst))
        p1, p2 = inst[("P", 1)], inst[("P", 2)]
        assert [c["tick"] for c in p1] == [1, 2, 3] and [c["tick"] for c in p2] == [1, 2]
        assert [[a["score"] for a in c["acts"]] for c in p1] == [[0.1], [0.2], [0.3]], order
        assert [[a["score"] for a in c["acts"]] for c in p2] == [[0.05], [0.15]], order
        assert [[a["score"] for a in c["acts"]] for c in inst[("Q", 1)]] == [[0.9], [0.8]]
        assert [[a["score"] for a in c["acts"]] for c in inst[("Q", 2)]] == [[0.7]]
        with Tmp() as root:
            life = os.path.join(root, "L")
            _w(os.path.join(life, "ledger.jsonl"), "")
            v = ap.ChildView(life, rows=rows_for(order))
            text = v.ledger_tail(4)
            blocks = text.split("\n\n")
            b_p1 = [b for b in blocks if b.startswith("### P (instance 1)")][0]
            b_p2 = [b for b in blocks if b.startswith("### P (instance 2)")][0]
            assert "acts=3 best=0.3000" in b_p1 and "acts=2 best=0.1500" in b_p2
            assert "0.3000" not in b_p2 and "0.0500" not in b_p1
            lines = b_p1.splitlines()
            i_note = [i for i, l in enumerate(lines) if l.startswith("[chunk 3]")][0]
            assert lines[i_note + 1].strip().startswith("[chunk 3] ACT -> score 0.3000")
            assert "predicted 0.500, surprise -0.200" in lines[i_note + 1]
    # the full fixture in both orders: same instance count and best scores
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root, order="thought_first")
        v = ap.ChildView(life, rows=rows, sleep_dir=s64, society_dir=soc)
        t1 = v.ledger_tail(3)
        life2, rows2, s64b, _sib2, soc2 = make_life(os.path.join(root, "b"))
        v2 = ap.ChildView(life2, rows=rows2, sleep_dir=s64b, society_dir=soc2)
        assert t1 == v2.ledger_tail(3) and "acts=4 best=0.2900" in t1


def test_leak_scan_fallback_and_quote_back_exemption():
    leaky = final("The answer is to run -licm first, then the rest.\nThe rule is "
                  "simple.")
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[tool("ledger_tail"), leaky])
        room = ap.ParentRoom([cfg], clients={"A": client})
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["text"].startswith(FALLBACK) and meta["text"].endswith(REHEARSAL_TAIL)
        assert meta["hits"] and meta["fallback"] is True
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["merged"]["fallback_reason"] == "leak_scan"
        assert "-licm" not in open(os.path.join(s64, "parent_brief.txt")).read()
    # quoting back the child's OWN recipe (seen via ledger_tail) is not a leak
    quoting = final(f'You begin every episode with "{RECIPE}" and expect 0.3.\n'
                    "Name one feature of this program first.")
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[tool("ledger_tail"), quoting])
        room = ap.ParentRoom([cfg], clients={"A": client})
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is False and RECIPE in meta["text"]
    # the same quote WITHOUT having read the child's words is a leak
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[quoting])
        room = ap.ParentRoom([cfg], clients={"A": client})
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is True and meta["hits"]


def test_identifier_scan_fallback_and_redaction():
    assert ap.identifier_scan("ssh to 10.0.0.12 now") == ["ipv4"]
    assert "email_or_user_at_host" in ap.identifier_scan(f"mail {FAKE_EMAIL}")
    assert "url" in ap.identifier_scan("see https://hub.example.com/v1")
    assert ap.identifier_scan("benchmark://cbench-v1/crc32 scored 0.31") == []
    assert ap.identifier_scan("ACT: -mem2reg, -sroa; PREDICT: 0.3") == []
    red = ap.redact_identifiers(f"host {FAKE_IP} user {FAKE_EMAIL}")
    assert FAKE_IP not in red and FAKE_EMAIL not in red and "<REDACTED>" in red
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[final("Log in to 10.0.0.12 and look "
                                                 "at your notes.")])
        room = ap.ParentRoom([cfg], clients={"A": client})
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is True and meta["text"].startswith(FALLBACK)
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["merged"]["fallback_reason"] == "identifier_scan"
        assert row["merged"]["hits"] == ["ipv4"]          # names, never values
        for path, text in all_written(root).items():
            assert "10.0.0.12" not in text, path
    # tool output carrying identifiers (sibling brief, playbook) is redacted
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = two_parent_room()
        run_room(root, room, life, rows, s64, soc)
        msgs = all_messages(ca, cb)
        assert "TOOL RESULT other_children" in msgs
        assert FAKE_IP not in msgs and FAKE_EMAIL not in msgs
        assert "<REDACTED>" in msgs
        for path, text in all_written(root).items():
            if "R2_B_seed1" in path:
                continue                      # the sibling fixture itself
            # includes the society playbook: its pre-existing line carrying
            # FAKE_IP is re-redacted by the bounded rewrite
            assert FAKE_IP not in text, path
        assert "<REDACTED>" in open(os.path.join(soc, "playbook.md")).read()
    try:
        ap.check_prompt([dict(role="user", content=f"see {FAKE_IP}")])
    except ap.IdentifierLeak:
        pass
    else:
        raise AssertionError("prompt with an identifier was accepted")


def test_two_parent_merge_and_ledger_writes():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = two_parent_room()
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["text"].startswith("MERGED:") and meta["text"].endswith(REHEARSAL_TAIL)
        assert meta["exchanges"] == 3 and meta["merged_from"] == "merge by A"
        assert meta["fallback"] is False and meta["hits"] == []
        assert meta["curriculum_move"]["move"] == "sharpen"
        assert 0.0 <= meta["frontier_estimate"]["confidence"] <= 1.0
        assert meta["parent_model"] == "mock-A, mock-B"
        assert meta["skipped"] == [] and meta["room_error"] is None
        # both critiques happened, then the merge (bounded dialogue)
        assert any("=== CROSS-VERIFICATION ===" in m["content"]
                   for m in ca.calls[-2]) and \
            any("=== MERGE ===" in m["content"] for m in ca.calls[-1])
        assert any("=== CROSS-VERIFICATION ===" in m["content"] for m in cb.calls[-1])
        led = ledger_rows(life)
        row = [r for r in led if r["kind"] == "agentic_room"][-1]
        assert row["prompt_version"] == ap.PROMPT_VERSION
        assert row["child_stage"] == "sleep_0064"
        assert [p["role"] for p in row["parents"]] == ["A", "B"]
        for p in row["parents"]:
            assert set(p) == {"role", "provider", "model"}
        assert set(row["proposals"]) == {"A", "B"}
        assert row["proposals"]["A"]["brief"].startswith("You open every episode")
        assert row["proposals"]["B"]["brief"].startswith("Your notes could be")
        assert row["proposals"]["A"]["tool_calls"][0].startswith("ledger_tail(")
        assert set(row["critiques"]) == {"A_on_B", "B_on_A"}
        assert row["critiques"]["A_on_B"]["verdict"] == "accept"
        assert row["merged"]["brief"].startswith("MERGED:")
        for r in ("A", "B"):
            assert "frontier_estimate" in row["proposals"][r]
        assert row["merged"]["frontier_estimate"]["text"]
        assert row["skipped"] == [] and "error" not in row
        soc_rows = [json.loads(l) for l in open(os.path.join(soc, "ledger.jsonl"))]
        srow = soc_rows[-1]
        assert srow["child"] == "RP_B_seed0" and srow["stage"] == "sleep_0064"
        assert srow["curriculum_move"]["move"] == "sharpen"
        assert srow["proposal_frontiers"]["B"]["text"]
        assert srow["critique_verdicts"] == {"A_on_B": "accept", "B_on_A": "accept"}
        pb = open(os.path.join(soc, "playbook.md")).read()
        assert "[RP_B_seed0 sleep_0064] Children lock into one opening move" in pb
        assert pb.startswith("# Parental society playbook")
        assert os.path.exists(os.path.join(soc, ".society.lock"))
        # the brief went to the waking side only: the corpus is untouched
        assert json.load(open(os.path.join(s64, "corpus.json")))["corpus"] == []


def test_critique_and_merge_argue_from_the_evidence():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = two_parent_room()
        run_room(root, room, life, rows, s64, soc)
        crit_a = ca.calls[-2]                       # A critiques B
        joined = "\n".join(m["content"] for m in crit_a)
        assert "=== YOUR PREVIOUS BRIEF TO THIS CHILD ===" in joined
        assert "=== THE ROOM" in crit_a[0]["content"]          # system prompt
        assert "TOOL RESULT ledger_tail" in joined and RECIPE in joined
        assert "TOOL RESULT gate_decisions" in joined
        assert "You open every episode" in joined               # A's own final
        assert crit_a[-1]["role"] == "user"
        assert "=== CROSS-VERIFICATION ===" in crit_a[-1]["content"]
        assert "Your notes could be" in crit_a[-1]["content"]   # B's proposal
        crit_b = cb.calls[-1]
        joined_b = "\n".join(m["content"] for m in crit_b)
        assert "=== YOUR PREVIOUS BRIEF TO THIS CHILD ===" in joined_b
        assert "TOOL RESULT other_children" in joined_b
        merge = ca.calls[-1]
        joined_m = "\n".join(m["content"] for m in merge)
        assert "=== YOUR PREVIOUS BRIEF TO THIS CHILD ===" in joined_m
        assert "TOOL RESULT ledger_tail" in joined_m
        assert merge[-1]["content"].startswith("=== MERGE ===")
        # the replay is bounded: head (system, dashboard) and the final are
        # kept whole, the tool exchanges shrink to the budget
        ag = room.agents[0]
        full = ag._context_messages(None, {}, 2)
        assert full[0]["role"] == "system" and full[-1]["content"].startswith("{")
        ag.context_chars = len(full[0]["content"]) + len(full[1]["content"]) \
            + len(full[-1]["content"]) + 500
        small = ag._context_messages(None, {}, 2)
        assert small[0] == full[0] and small[1] == full[1] and small[-1] == full[-1]
        assert len(small) == 4 and "omitted for length" in small[2]["content"]
        ag.context_chars = 10 ** 6
        assert ag._context_messages(None, {}, 2) == full


def test_room_never_raises_into_the_life():
    # torn shared-ledger line + corrupt gate.json + corrupt earlier meta
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        with open(os.path.join(soc, "ledger.jsonl"), "a") as f:
            f.write('{"ts": 2.0, "kind": "room", "child": "R2_B_seed1", "sta')
        _w(os.path.join(life, "sleep_0032", "gate.json"), "{not json")
        _w(os.path.join(life, "sleep_0032", "parent_brief.json"), "{torn")
        with open(os.path.join(life, "parent_ledger.jsonl"), "a") as f:
            f.write('{"kind": "agentic_room", "merged": {"fr\n')
        room, ca, cb = two_parent_room()
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["intervened"] is True and meta["fallback"] is False
        assert meta["text"].startswith("MERGED:") and meta["room_error"] is None
        assert "TOOL RESULT gate_decisions" in all_messages(ca)
        assert '"gate_json": "unreadable"' in all_messages(ca)
        soc_rows = ap._read_jsonl(os.path.join(soc, "ledger.jsonl"))
        assert [r["child"] for r in soc_rows] == ["R2_B_seed1", "RP_B_seed0"]
        assert len(open(os.path.join(soc, "ledger.jsonl")).read().splitlines()) == 3
    # a room that dies: FALLBACK delivered, room_error logged, key masked
    class BoomRoom:
        def public_parents(self):
            return [dict(role="A", provider="anthropic", model="claude-opus-5")]

        def run(self, view, context):
            raise RuntimeError(f"connection reset while sending {SECRET}")

    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        ap.register_secret(SECRET)
        meta = ap.parent_brief_agentic(life, rows, s64, None, "mock", 32,
                                       room=BoomRoom(), society_dir=soc)
        assert meta["intervened"] is True and meta["fallback"] is True
        assert meta["text"] == FALLBACK + REHEARSAL_TAIL
        assert meta["room_error"].startswith("RuntimeError") and "***" in meta["room_error"]
        assert meta["parent_model"] == "claude-opus-5" and meta["exchanges"] == 0
        assert open(os.path.join(s64, "parent_brief.txt")).read() == \
            (FALLBACK + REHEARSAL_TAIL).strip()
        led = ledger_rows(life)
        assert [r["kind"] for r in led[-2:]] == ["agentic_room", "room_error"]
        assert led[-2]["merged"]["fallback_reason"] == "room_error"
        assert "***" in led[-1]["error"] and SECRET not in json.dumps(led)
        for path, text in all_written(root).items():
            assert SECRET not in text, path
        soc_rows = ap._read_jsonl(os.path.join(soc, "ledger.jsonl"))
        assert soc_rows[-1]["fallback"] is True and soc_rows[-1]["skipped"] == ["room"]
    # logging itself failing (society dir is a file) is recorded, not raised
    with Tmp() as root:
        life, rows, s64, _sib, _soc = make_life(root)
        _w(os.path.join(root, "afile"), "x")
        room, ca, cb = two_parent_room()
        meta = ap.parent_brief_agentic(life, rows, s64, None, "mock", 32,
                                       room=room,
                                       society_dir=os.path.join(root, "afile", "s"))
        assert meta["intervened"] is True and meta["text"].startswith("MERGED:")
        assert meta["log_error"] and os.path.exists(os.path.join(s64, "parent_brief.txt"))
        assert ledger_rows(life)[-1]["kind"] == "room_error"


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class SlowMock(ap.MockChatClient):
    """Each call advances the room's fake clock by `step` seconds."""
    clock: Clock = Clock()
    step = 100.0

    def chat(self, messages, max_tokens=None, *, retries=None, deadline=None):
        assert deadline is not None, "the room must pass its deadline down"
        self.clock.t += self.step
        return super().chat(messages, max_tokens, retries=retries,
                            deadline=deadline)


def test_room_deadline_bounds_the_wall_clock():
    # A: 4 calls (400 s), B: 6 calls (600 s), critiques 2 calls, merge 1 call
    def make(timeout):
        SlowMock.clock = Clock()
        room, ca, cb = two_parent_room(client_cls=SlowMock,
                                       room_timeout_s=timeout, min_phase_s=60,
                                       clock=SlowMock.clock)
        return room, ca, cb

    with Tmp() as root:                  # everything fits: normal room
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = make(5000)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["exchanges"] == 3 and meta["skipped"] == []
        assert meta["text"].startswith("MERGED:")
    with Tmp() as root:                  # merge does not fit: skip it
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = make(1250)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["exchanges"] == 2 and meta["skipped"] == ["merge"]
        assert meta["merged_from"] == "proposal A (deadline)"
        assert meta["fallback"] is False and meta["text"].startswith("You open every")
        assert not any("=== MERGE ===" in m["content"] for c in ca.calls for m in c)
    with Tmp() as root:                  # B's proposal overran: A delivered
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = make(350)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["skipped"] == ["proposal B", "critiques", "merge"]
        assert meta["exchanges"] == 1 and cb.calls == []
        assert meta["merged_from"] == "proposal A (deadline)"
        assert meta["fallback"] is False and meta["text"].startswith("You open every")
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["proposals"]["B"]["fallback_reason"] == "deadline"
        assert row["skipped"] == meta["skipped"] and row["elapsed_s"] == 400.0
    with Tmp() as root:                  # nothing validated in time: FALLBACK
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = make(250)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is True and meta["text"] == FALLBACK + REHEARSAL_TAIL
        assert len(ca.calls) == 3 and cb.calls == []          # 4th never sent
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["merged"]["fallback_reason"] == "deadline"
        assert row["proposals"]["A"]["fallback_reason"] == "deadline"
        assert "deadline" in row["proposals"]["A"]["error"]
        assert row["merged"]["merged_from"] == "fallback (deadline)"
    # env defaults
    room = ap.ParentRoom([ap.ProviderConfig("mock")],
                         clients={"A": ap.MockChatClient(script=[GOOD_A])})
    assert room.room_timeout_s == 900.0 and room.min_phase_s == 60.0
    assert ap.ProviderConfig("mock").timeout_s == 240


def test_empty_reply_never_becomes_an_empty_turn():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=["   ", GOOD_A])
        room = ap.ParentRoom([cfg], clients={"A": client})
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is False
        second = client.calls[1]
        assert second[2]["role"] == "assistant" and second[2]["content"] == "(empty reply)"
        assert all(m["content"].strip() for c in client.calls for m in c)
    # the request builder never ships an empty turn either
    cfg = ap.ProviderConfig("anthropic", api_key=SECRET, max_tokens=100)
    _u, _h, body = ap.HTTPChatClient(cfg).build_request(
        [dict(role="user", content="q"), dict(role="assistant", content=""),
         dict(role="user", content="again")])
    assert [m["content"] for m in body["messages"]] == ["q", "(empty)", "again"]


def test_key_masking_everywhere():
    cfg = ap.ProviderConfig("anthropic", role="A", api_key=SECRET,
                            model="claude-opus-5", reasoning="high")
    assert SECRET not in repr(cfg) and "***" in repr(cfg)
    assert set(cfg.public()) == {"role", "provider", "model"}
    env = {"PARENT_A_PROVIDER": "anthropic", "PARENT_A_API_KEY": SECRET,
           "PARENT_B_PROVIDER": "local", "OTHER": "x"}
    snap = ap.snapshot_env(env)
    assert snap["PARENT_A_API_KEY"] == SECRET
    assert "PARENT_A_API_KEY" not in env and env["OTHER"] == "x"
    assert env["PARENT_A_PROVIDER"] == "anthropic"
    assert ap.mask_secrets(f"error: bad key {SECRET} rejected") == \
        "error: bad key *** rejected"
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        # parent A holds the key; parent B's provider echoes the key back in
        # an error (as misconfigured gateways do): it must be masked on disk
        room, ca, cb = two_parent_room(a_key=SECRET, b_raise=SECRET)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["intervened"] is True
        for path, text in all_written(root).items():
            assert SECRET not in text, path
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["proposals"]["B"]["fallback"] is True
        assert "***" in row["proposals"]["B"]["error"]
        # B was dead, so A's proposal carried (merge falls back to A's brief
        # since B's critique of A is unavailable and A's own passed)
        assert meta["text"].endswith(REHEARSAL_TAIL)


def test_http_request_shapes_without_network():
    msgs = [dict(role="system", content="S"), dict(role="user", content="u1"),
            dict(role="assistant", content="a1"), dict(role="user", content="u2"),
            dict(role="user", content="u3")]
    cfg = ap.ProviderConfig("anthropic", api_key=SECRET, model="claude-opus-5",
                            reasoning="xhigh", max_tokens=1234)
    url, headers, body = ap.HTTPChatClient(cfg).build_request(msgs)
    assert url == "https://api.anthropic.com/v1/messages"
    assert headers["x-api-key"] == SECRET and headers["anthropic-version"] == "2023-06-01"
    assert SECRET not in json.dumps(body)
    assert body["system"] == "S" and body["max_tokens"] == 1234
    assert [m["role"] for m in body["messages"]] == ["user", "assistant", "user"]
    assert body["messages"][-1]["content"] == "u2\n\nu3"
    assert body["thinking"] == {"type": "adaptive"}
    assert body["output_config"] == {"effort": "xhigh"} and "temperature" not in body
    cfg = ap.ProviderConfig("openai_compat", api_key=SECRET, model="gpt-x",
                            base_url="https://hub.example.com/v1/",
                            reasoning="high")
    url, headers, body = ap.HTTPChatClient(cfg).build_request(msgs, 500)
    assert url == "https://hub.example.com/v1/chat/completions"
    assert headers["Authorization"] == "Bearer " + SECRET
    # reasoning endpoints (the inference hub) require max_completion_tokens
    assert body["max_completion_tokens"] == 500 and "max_tokens" not in body
    assert body["reasoning_effort"] == "high"
    assert "temperature" not in body and len(body["messages"]) == 5
    cfg = ap.ProviderConfig("local")
    url, headers, body = ap.HTTPChatClient(cfg).build_request(msgs)
    assert url == "http://127.0.0.1:8011/v1/chat/completions"
    assert "Authorization" not in headers and body["temperature"] == 0.4
    assert "reasoning_effort" not in body and body["max_tokens"] == 2000
    # output-cap defaults (the cap covers thinking + text)
    assert ap.ProviderConfig("anthropic").max_tokens == 16000
    assert ap.ProviderConfig("openai_compat", model="m", reasoning="high",
                             base_url="https://h.example.com/v1").max_tokens == 16000
    assert ap.ProviderConfig("openai_compat", model="m",
                             base_url="https://h.example.com/v1").max_tokens == 4000
    assert ap.ProviderConfig("local").max_tokens == 2000
    assert ap.ProviderConfig("local", max_tokens_field="max_completion_tokens") \
        .max_tokens_field == "max_completion_tokens"
    text = ap.HTTPChatClient.parse_response("anthropic", dict(
        stop_reason="end_turn", content=[dict(type="thinking", thinking="..."),
                                         dict(type="text", text="hello")]))
    assert text == "hello"
    assert raises(ap.ProviderError, ap.HTTPChatClient.parse_response, "anthropic",
                  dict(stop_reason="refusal", content=[]))
    assert raises(ap.TruncatedReply, ap.HTTPChatClient.parse_response, "anthropic",
                  anth_reply(None, "max_tokens"))
    assert raises(ap.TruncatedReply, ap.HTTPChatClient.parse_response, "anthropic",
                  anth_reply("partial {", "max_tokens"))
    assert ap.HTTPChatClient.parse_response("openai_compat", dict(
        choices=[dict(message=dict(content="hi"))])) == "hi"
    assert raises(ap.TruncatedReply, ap.HTTPChatClient.parse_response,
                  "openai_compat", oai_reply("partial", "length"))
    for bad in (dict(provider="openai_compat"), dict(provider="nope"),
                dict(provider="openai_compat", model="m", base_url="ftp://x/v1")):
        try:
            ap.ProviderConfig(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad} accepted")


def test_key_goes_only_to_the_configured_host():
    # a plaintext key to a non-loopback host is refused at configuration time
    assert raises(ValueError, ap.ProviderConfig, "openai_compat", model="m",
                  base_url="http://hub.example.com/v1", api_key=SECRET)
    assert raises(ValueError, ap.ProviderConfig, "anthropic",
                  base_url="http://10.0.0.5/v1", api_key=SECRET)
    ap.ProviderConfig("openai_compat", model="m", base_url="http://hub.example.com/v1")
    ap.ProviderConfig("openai_compat", model="m", base_url="https://hub.example.com/v1",
                      api_key=SECRET)
    ap.ProviderConfig("local", api_key=SECRET)          # loopback: allowed
    ap.ProviderConfig("openai_compat", model="m", base_url="http://localhost:8011/v1",
                      api_key=SECRET)
    # the process-wide opener follows no redirect and uses no proxy
    handlers = ap._OPENER.handlers
    assert any(isinstance(h, ap._NoRedirect) for h in handlers)
    assert all(h.proxies == {} for h in handlers
               if isinstance(h, urllib.request.ProxyHandler))
    assert ap._NoRedirect().redirect_request(None, None, 302, "", {}, "x") is None
    # end to end: server A redirects to server B; B must never see anything
    srv_b, hb, url_b = serve([(200, oai_reply("stolen"), {})])
    loc = url_b + "/chat/completions"
    srv_a, ha, url_a = serve([(302, {}, {"Location": loc}),
                              (307, {}, {"Location": loc}),
                              (301, {}, {"Location": loc}),
                              (302, {}, {"Location": loc})])
    old_proxy = os.environ.get("http_proxy")
    os.environ["http_proxy"] = url_b                # must be ignored too
    try:
        cfg = ap.ProviderConfig("openai_compat", model="m", base_url=url_a,
                                api_key=SECRET)
        c = ap.HTTPChatClient(cfg, retries=2)
        msgs = [dict(role="user", content="hi")]
        for _ in range(2):
            try:
                c.chat(msgs)
            except ap.ProviderError as e:
                assert "redirect refused" in str(e) and SECRET not in str(e)
            else:
                raise AssertionError("redirect was followed")
        assert len(ha.seen) == 2                    # no retry on a redirect
        assert ha.seen[0]["headers"]["authorization"] == "Bearer " + SECRET
        assert ha.seen[0]["method"] == "POST"
        cfg = ap.ProviderConfig("anthropic", base_url=url_a, api_key=SECRET)
        try:
            ap.HTTPChatClient(cfg, retries=0).chat(msgs)
        except ap.ProviderError as e:
            assert "redirect refused" in str(e)
        else:
            raise AssertionError("redirect was followed")
        assert ha.seen[-1]["headers"]["x-api-key"] == SECRET
        assert hb.seen == [], hb.seen
    finally:
        if old_proxy is None:
            os.environ.pop("http_proxy", None)
        else:
            os.environ["http_proxy"] = old_proxy
        stop(srv_a, srv_b)


def test_truncation_retry_and_max_tokens_field_swap():
    fin = GOOD_A
    # anthropic: cut during thinking (empty text) -> doubled cap, then fine
    srv, h, url = serve([(200, anth_reply(None, "max_tokens"), {}),
                         (200, anth_reply(fin), {})])
    try:
        cfg = ap.ProviderConfig("anthropic", base_url=url, api_key=SECRET,
                                max_tokens=1000)
        assert cfg.base_url.startswith("http://127.0.0.1")
        out = ap.HTTPChatClient(cfg, retries=0).chat([dict(role="user", content="q")])
        assert out == fin
        assert [r["body"]["max_tokens"] for r in h.seen] == [1000, 2000]
    finally:
        stop(srv)
    # twice truncated -> provider error naming the knob (no third request)
    srv, h, url = serve([(200, anth_reply("x", "max_tokens"), {}),
                         (200, anth_reply("y", "max_tokens"), {}),
                         (200, anth_reply(fin), {})])
    try:
        cfg = ap.ProviderConfig("anthropic", base_url=url, api_key=SECRET,
                                max_tokens=1000)
        try:
            ap.HTTPChatClient(cfg, retries=0).chat([dict(role="user", content="q")])
        except ap.ProviderError as e:
            assert "PARENT_MAX_TOKENS" in str(e) and "cap was 2000" in str(e)
        else:
            raise AssertionError("truncation accepted")
        assert len(h.seen) == 2
    finally:
        stop(srv)
    # openai_compat: the hub rejects the field -> swap once and remember;
    # then a finish_reason=length reply -> doubled cap
    err = {"error": {"message": "Unrecognized request argument supplied: "
                                "max_completion_tokens", "type": "invalid_request_error"}}
    srv, h, url = serve([(400, err, {}), (200, oai_reply("part", "length"), {}),
                         (200, oai_reply(fin), {})])
    try:
        cfg = ap.ProviderConfig("openai_compat", model="m", base_url=url,
                                api_key=SECRET, max_tokens=700)
        assert cfg.max_tokens_field == "max_completion_tokens"
        out = ap.HTTPChatClient(cfg, retries=0).chat([dict(role="user", content="q")])
        assert out == fin
        assert "max_completion_tokens" in h.seen[0]["body"]
        assert h.seen[1]["body"]["max_tokens"] == 700 and \
            "max_completion_tokens" not in h.seen[1]["body"]
        assert h.seen[2]["body"]["max_tokens"] == 1400
        assert cfg.max_tokens_field == "max_tokens"      # kept for next calls
    finally:
        stop(srv)
    # a 400 that does not name the field is final (no swap, no retry)
    srv, h, url = serve([(400, {"error": {"message": "bad model"}}, {}),
                         (200, oai_reply(fin), {})])
    try:
        cfg = ap.ProviderConfig("openai_compat", model="m", base_url=url,
                                api_key=SECRET)
        assert raises(ap.ProviderError, ap.HTTPChatClient(cfg, retries=2).chat,
                      [dict(role="user", content="q")])
        assert len(h.seen) == 1
    finally:
        stop(srv)
    # a propose() whose provider keeps truncating falls back once, cleanly
    srv, h, url = serve([(200, anth_reply(None, "max_tokens"), {})] * 6)
    try:
        with Tmp() as root:
            life, rows, s64, _sib, soc = make_life(root)
            cfg = ap.ProviderConfig("anthropic", base_url=url, api_key=SECRET,
                                    max_tokens=500)
            room = ap.ParentRoom([cfg], clients={"A": ap.HTTPChatClient(cfg, retries=0)})
            meta = run_room(root, room, life, rows, s64, soc)
            assert meta["fallback"] is True and meta["text"].startswith(FALLBACK)
            row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
            assert row["merged"]["fallback_reason"] == "provider error"
            assert "PARENT_MAX_TOKENS" in row["proposals"]["A"]["error"]
            assert len(h.seen) == 2                     # not 3 identical retries
            for path, text in all_written(root).items():
                assert SECRET not in text, path
    finally:
        stop(srv)


def test_configs_from_env_and_room_from_env():
    env = {"PARENT_A_PROVIDER": "anthropic", "PARENT_A_API_KEY": SECRET,
           "PARENT_A_MODEL": "claude-fable-5-1",
           "PARENT_B_PROVIDER": "openai_compat", "PARENT_B_MODEL": "codex-x",
           "PARENT_B_BASE_URL": "https://hub.example.com/v1",
           "PARENT_B_API_KEY": SECRET + "B", "PARENT_REASONING": "high",
           "PARENT_MAX_TOKENS": "3000", "PARENT_B_MAX_TOKENS": "4000",
           "PARENT_B_MAX_TOKENS_FIELD": "max_tokens"}
    cfgs = ap.configs_from_env(env)
    assert [c.role for c in cfgs] == ["A", "B"]
    assert cfgs[0].model == "claude-fable-5-1" and cfgs[0].reasoning == "high"
    assert cfgs[0].max_tokens == 3000 and cfgs[1].max_tokens == 4000
    assert cfgs[1].api_key == SECRET + "B"
    assert cfgs[0].max_tokens_field == "max_tokens"
    assert cfgs[1].max_tokens_field == "max_tokens"      # explicit override
    assert ap.configs_from_env({"PARENT_PROVIDER": "local"})[0].provider == "local"
    assert ap.configs_from_env({}) == []
    room = ap.ParentRoom.from_env({}, fallback_local=("http://127.0.0.1:8011/v1",
                                                      "Qwen/Qwen2.5-32B-Instruct"))
    assert room.public_parents() == [dict(role="A", provider="local",
                                          model="Qwen/Qwen2.5-32B-Instruct")]
    try:
        ap.ParentRoom.from_env({}, fallback_local=(None, None))
    except RuntimeError:
        pass
    else:
        raise AssertionError("room without any parent was accepted")


def test_run_life_v2_return_shape_and_idempotency():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        room, ca, cb = two_parent_room()
        meta = run_room(root, room, life, rows, s64, soc)
        # the keys run_life_v2 logs from parent_brief's meta
        for k in ("metrics", "intervened", "text", "hits", "prompt_version"):
            assert k in meta, k
        m = meta["metrics"]
        assert m["ritual"] is True and "same_recipe" in m["flags"]
        assert "rehearsal_rate" in m and m["rehearsal_rate"] > 0.0
        assert m["n_episodes"] == 32
        body = meta["text"][:-len(REHEARSAL_TAIL)]
        assert meta["text"].endswith(REHEARSAL_TAIL)
        assert len([l for l in body.splitlines() if l.strip()]) <= 10
        pb = os.path.join(s64, "parent_brief.txt")
        assert open(pb).read().strip() == meta["text"].strip()[:1900]
        assert json.load(open(os.path.join(s64, "parent_brief.json")))["text"] == meta["text"]
        # what run_life_v2.brief() does: latest sleep_* with a parent brief
        latest = None
        for d in sorted(os.listdir(life), reverse=True):
            p = os.path.join(life, d, "parent_brief.txt")
            if d.startswith("sleep_") and os.path.exists(p):
                latest = d
                break
        assert latest == "sleep_0064"
        n_a, n_b = len(ca.calls), len(cb.calls)
        meta2 = run_room(root, room, life, rows, s64, soc)      # idempotent
        assert meta2 == meta and (len(ca.calls), len(cb.calls)) == (n_a, n_b)
        n_rows = sum(1 for _ in open(os.path.join(soc, "ledger.jsonl")))
        assert n_rows == 2                                      # fixture + one


def test_tool_budget_is_enforced():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[tool("ledger_tail", n_episodes=2)],
                                   final=GOOD_A)
        room = ap.ParentRoom([cfg], clients={"A": client}, max_tool_calls=3)
        meta = run_room(root, room, life, rows, s64, soc)
        assert meta["fallback"] is False and meta["exchanges"] == 1
        assert meta["merged_from"] == "single-parent"
        row = [r for r in ledger_rows(life) if r["kind"] == "agentic_room"][-1]
        assert row["proposals"]["A"]["n_tool_calls"] == 3
        assert len(client.calls) == 5              # 3 tools + 1 refused + final
        assert "TOOL BUDGET EXHAUSTED" in client.calls[-1][-1]["content"]


def test_brief_line_limit_and_lenient_fields():
    long_brief = "\n".join(f"line {i} about naming a feature first" for i in range(14))
    out = ap.validate_output(dict(final=dict(brief=long_brief, curriculum_move="ADVANCE",
                                             frontier_estimate="almost there")),
                             samples="", evidence_default=["ledger_tail()"])
    assert out["fallback"] is False and out["truncated"] is True
    assert len(out["brief"].splitlines()) == 10
    assert out["curriculum_move"]["move"] == "advance"
    assert out["frontier_estimate"] == dict(text="almost there", confidence=0.0)
    assert out["evidence"] == ["ledger_tail()"]
    assert out["delivered_text"].endswith(REHEARSAL_TAIL)
    assert ap.validate_output(dict(final=dict(brief="")), "")["fallback_reason"] == "brief missing"
    assert ap.validate_output(None, "")["fallback"] is True
    # a rehearsal tail written by the model is stripped, then re-appended once
    out = ap.validate_output(dict(brief="Name a feature first." + REHEARSAL_TAIL), "")
    assert out["delivered_text"].count("Repeat after me") == 1


def test_extract_json():
    assert ap.extract_json('```json\n{"tool": "metrics", "args": {}}\n```') == \
        dict(tool="metrics", args={})
    assert ap.extract_json('I will look. {"tool": "ledger_tail", "args": {"n_episodes": 3}} ok')["tool"] == "ledger_tail"
    assert ap.extract_json("no json here") is None
    assert ap.extract_json("") is None
    assert ap.extract_json('{"a": {"b": 1}} trailing')["a"]["b"] == 1


def test_only_ritual_env_skips_the_room():
    with Tmp() as root:
        life, rows, s64, _sib, soc = make_life(root)
        cfg = ap.ProviderConfig("mock", role="A", model="mock-A")
        client = ap.MockChatClient(script=[GOOD_A])
        room = ap.ParentRoom([cfg], clients={"A": client})
        os.environ["PARENT_AGENTIC_ONLY_RITUAL"] = "1"
        try:
            meta = ap.parent_brief_agentic(life, rows[:8], s64, None, "mock", 32,
                                           room=room, society_dir=soc)
        finally:
            del os.environ["PARENT_AGENTIC_ONLY_RITUAL"]
        assert meta["intervened"] is False and meta["metrics"]["ritual"] is False
        assert client.calls == [] and not os.path.exists(os.path.join(s64, "parent_brief.txt"))
        assert ledger_rows(life)[-1]["kind"] == "ritual_check"


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
