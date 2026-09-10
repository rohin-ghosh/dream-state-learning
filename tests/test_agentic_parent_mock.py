"""CPU test of the agentic parent harness with a MOCK provider.

Run:  python3 -m pytest tests/test_agentic_parent_mock.py -q
  or: python3 tests/test_agentic_parent_mock.py

Builds a fake life directory (ritualized child, one earlier brief, a gate
decision, forbidden report-panel probe files carrying a sentinel score, a
sibling child whose brief contains fake internal identifiers, a society
ledger) and exercises: forbidden-file enforcement, leak-scan fallback with
the quote-back exemption, identifier redaction/fallback, the two-parent
merge, ledger/society/playbook writes, key masking, the tool-call budget,
the HTTP request shapes (no network) and the run_life_v2-compatible return
shape and idempotency.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

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


def make_rows(n_instances=40, rehearse_from=32):
    rows = []
    for i in range(n_instances):
        eid = PROGRAMS[i % len(PROGRAMS)]
        for t in range(1, 5):
            score = 0.28 + 0.01 * (t % 2)
            rows.append(dict(kind="act", episode_id=eid, tick=t, action=RECIPE,
                             prediction=0.3, outcome="applied 4 passes",
                             score=score, surprise=score - 0.3, time_cost=1.0))
            note = (f"PREDICT: 0.3\nACT: {RECIPE}\nNOTE: The standard recipe "
                    f"works well; keep using it on this program.\n"
                    f"RECALL: best passes for this program")
            if t == 1 and i >= rehearse_from:
                note = ("NOTE: My ritual was opening with the same four steps; "
                        "instead I name a feature of this program first and "
                        "say what I expect.\n" + note)
            rows.append(dict(kind="thought", episode_id=eid, tick=t, note=note,
                             prompt="", win=False, had_note=True))
    return rows


def make_life(root, overlap_gate_panel=False):
    """<root>/RP_B_seed0 (child), <root>/R2_B_seed1 (sibling), <root>/society."""
    life = os.path.join(root, "RP_B_seed0")
    rows = make_rows()
    _w(os.path.join(life, "ledger.jsonl"),
       "".join(json.dumps(r) + "\n" for r in rows))
    for a, b in ((0, 8), (8, 16), (56, 64)):
        _wj(os.path.join(life, f"wake_{a:04d}_{b:04d}.json"), [])
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


def two_parent_room(a_key=None, b_raise=None, max_tool_calls=8):
    cfg_a = ap.ProviderConfig("mock", role="A", model="mock-A", api_key=a_key)
    cfg_b = ap.ProviderConfig("mock", role="B", model="mock-B")
    ca = ap.MockChatClient(script=[tool("ledger_tail", n_episodes=4),
                                   tool("metrics"), tool("gate_decisions"),
                                   GOOD_A],
                           critique=ACCEPT, merge=MERGED, model="mock-A")
    cb = ap.MockChatClient(script=[tool("other_children"), tool("prior_briefs"),
                                   tool("society"), tool("waking_brief"),
                                   tool("list_files"), GOOD_B],
                           critique=ACCEPT, model="mock-B", raise_with=b_raise)
    room = ap.ParentRoom([cfg_a, cfg_b], clients={"A": ca, "B": cb},
                         max_tool_calls=max_tool_calls)
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


def all_written(root, skip_probe=True):
    out = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if skip_probe and fn.startswith("probe_ep"):
                continue
            p = os.path.join(dp, fn)
            with open(p, errors="replace") as f:
                out[p] = f.read()
    return out


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
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        row = [r for r in led if r["kind"] == "agentic_room"][-1]
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
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        row = [r for r in led if r["kind"] == "agentic_room"][-1]
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
        # both critiques happened, then the merge (bounded dialogue)
        assert any("=== CROSS-VERIFICATION ===" in m["content"]
                   for m in ca.calls[-2]) and \
            any("=== MERGE ===" in m["content"] for m in ca.calls[-1])
        assert any("=== CROSS-VERIFICATION ===" in m["content"] for m in cb.calls[-1])
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
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
        soc_rows = [json.loads(l) for l in open(os.path.join(soc, "ledger.jsonl"))]
        srow = soc_rows[-1]
        assert srow["child"] == "RP_B_seed0" and srow["stage"] == "sleep_0064"
        assert srow["curriculum_move"]["move"] == "sharpen"
        assert srow["proposal_frontiers"]["B"]["text"]
        assert srow["critique_verdicts"] == {"A_on_B": "accept", "B_on_A": "accept"}
        pb = open(os.path.join(soc, "playbook.md")).read()
        assert "[RP_B_seed0 sleep_0064] Children lock into one opening move" in pb
        assert pb.startswith("# Parental society playbook")
        # the brief went to the waking side only: the corpus is untouched
        assert json.load(open(os.path.join(s64, "corpus.json")))["corpus"] == []


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
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        row = [r for r in led if r["kind"] == "agentic_room"][-1]
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
    assert body["max_tokens"] == 500 and body["reasoning_effort"] == "high"
    assert "temperature" not in body and len(body["messages"]) == 5
    cfg = ap.ProviderConfig("local")
    url, headers, body = ap.HTTPChatClient(cfg).build_request(msgs)
    assert url == "http://127.0.0.1:8011/v1/chat/completions"
    assert "Authorization" not in headers and body["temperature"] == 0.4
    assert "reasoning_effort" not in body
    text = ap.HTTPChatClient.parse_response("anthropic", dict(
        stop_reason="end_turn", content=[dict(type="thinking", thinking="..."),
                                         dict(type="text", text="hello")]))
    assert text == "hello"
    try:
        ap.HTTPChatClient.parse_response("anthropic", dict(stop_reason="refusal",
                                                            content=[]))
    except ap.ProviderError:
        pass
    else:
        raise AssertionError("refusal not raised")
    assert ap.HTTPChatClient.parse_response("openai_compat", dict(
        choices=[dict(message=dict(content="hi"))])) == "hi"
    for bad in (dict(provider="openai_compat"), dict(provider="nope")):
        try:
            ap.ProviderConfig(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad} accepted")


def test_configs_from_env_and_room_from_env():
    env = {"PARENT_A_PROVIDER": "anthropic", "PARENT_A_API_KEY": SECRET,
           "PARENT_A_MODEL": "claude-fable-5-1",
           "PARENT_B_PROVIDER": "openai_compat", "PARENT_B_MODEL": "codex-x",
           "PARENT_B_BASE_URL": "https://hub.example.com/v1",
           "PARENT_B_API_KEY": SECRET + "B", "PARENT_REASONING": "high",
           "PARENT_MAX_TOKENS": "3000", "PARENT_B_MAX_TOKENS": "4000"}
    cfgs = ap.configs_from_env(env)
    assert [c.role for c in cfgs] == ["A", "B"]
    assert cfgs[0].model == "claude-fable-5-1" and cfgs[0].reasoning == "high"
    assert cfgs[0].max_tokens == 3000 and cfgs[1].max_tokens == 4000
    assert cfgs[1].api_key == SECRET + "B"
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
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        row = [r for r in led if r["kind"] == "agentic_room"][-1]
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
        led = [json.loads(l) for l in open(os.path.join(life, "parent_ledger.jsonl"))]
        assert led[-1]["kind"] == "ritual_check"


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
