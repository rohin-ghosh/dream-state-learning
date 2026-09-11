"""sleep_compile_v3: the three write variants over one synthetic ledger.

  <python> tests/test_sleep_compile_v3.py          # plain script
  <python> -m pytest tests/test_sleep_compile_v3.py -q
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import v3_fixtures as fx  # noqa: E402
from organism_v6 import sleep_compile_v3 as sc3  # noqa: E402
from organism_v6 import train_adapter_v3 as tv3  # noqa: E402
from organism_v6.sleep_compile import canonicalize_dialect  # noqa: E402


def _rows(**kw):
    rows = fx.make_rows(**kw)
    kept, _n, _ids = sc3.exclude_rows(rows, sc3.default_exclusions("compiler"))
    return kept


def _child_texts(rows):
    return {canonicalize_dialect(r["note"]).strip() for r in rows
            if r.get("kind") in ("thought", "reflection") and r.get("note")}


def test_instances_attach_acts_to_their_chunk_and_separate_replays_and_clones():
    for order in ("acts_first", "thought_first"):
        rows = _rows(order=order)
        assert sc3.detect_act_order(rows) == order, order
        log = {}
        inst = sc3.build_instances(rows, log=log)
        assert log["act_row_order"] == order and not log.get("acts_orphaned")
        by = {}
        for i in inst:
            by.setdefault(i["eid"], []).append(i)
        assert len(by["cbench-v1/crc32"]) == 2, "the replay is a second INSTANCE"
        first = by["cbench-v1/crc32"][0]
        assert [c["tick"] for c in first["chunks"]] == [1, 2, 3]
        assert [len(c["acts"]) for c in first["chunks"]] == [1, 1, 1]
        assert first["chunks"][1]["acts"][0]["action"] == "-mem2reg, -sroa, -gvn"
        assert all(a["tick"] == c["tick"] for c in first["chunks"] for a in c["acts"])
        # two clones interleaved on one program are two instances of two chunks each
        clones = by["cbench-v1/sha_clones"]
        assert len(clones) == 2 and all(len(c["chunks"]) == 2 for c in clones)
        assert {c["clone_id"] for c in clones} == {0, 1}
        for c in clones:
            assert all(a["action"] == f"-licm{c['clone_id']}" for ch in c["chunks"] for a in ch["acts"])
        # a pure thought has no acts; the INVALID move is attached
        q = by["cbench-v1/qsort"][0]
        assert q["chunks"][0]["acts"] == [] and q["chunks"][1]["acts"][0]["outcome"].startswith("INVALID")
        # every act row of the ledger landed on exactly one chunk
        n_acts = sum(1 for r in rows if r["kind"] == "act")
        assert sum(len(c["acts"]) for i in inst for c in i["chunks"]) == n_acts


def test_one_chunk_episode_then_replay_is_attributed_correctly_in_both_writer_orders():
    for order in ("acts_first", "thought_first"):
        rows = fx.make_replay_rows(order)
        inst = sc3.build_instances(rows, order=order)
        one = [i for i in inst if i["eid"] == "cbench-v1/one"]
        assert len(one) == 2
        assert [(c["tick"], [a["action"] for a in c["acts"]]) for c in one[0]["chunks"]] == [(1, ["-a"])]
        assert [(c["tick"], [a["action"] for a in c["acts"]]) for c in one[1]["chunks"]] == [(1, ["-b"]), (2, ["-c"])]
        t1, t2 = sc3.transcript(one[0]), sc3.transcript(one[1])
        assert [e["text"] for e in t1 if e["part"] == "outcome"] == ["[OUTCOME] o-first (score 0.1000)\n"]
        outs2 = [e["text"] for e in t2 if e["part"] == "outcome"]
        assert outs2 == ["[OUTCOME] o-replay-1 (score 0.2000)\n", "[OUTCOME] o-replay-2 (score 0.3000)\n"]
        # the replay's first chunk is followed by ITS outcome (causal order intact)
        idx = [j for j, e in enumerate(t2) if e["role"] == "child"]
        assert t2[idx[0] + 1]["part"] == "outcome" and "o-replay-1" in t2[idx[0] + 1]["text"]
        # variant C: the replay's second move is conditioned on the replay's first outcome
        pairs = [p for p in sc3.tmem_pairs(rows, act_order=order) if p["type"] == "action" and p["eid"] == "cbench-v1/one"]
        assert [p["output"] for p in pairs] == ["-a", "-b", "-c"]
        assert "With no attempts made yet" in pairs[0]["instruction"] and "With no attempts made yet" in pairs[1]["instruction"]
        assert 'After the outcome "o-replay-1"' in pairs[2]["instruction"]
        # auto-detection agrees with the order the ledger was written in
        assert sc3.detect_act_order(rows) == order


def test_horizon_cut_drops_the_next_instances_orphan_acts_instead_of_gluing_them_on():
    for order in ("acts_first", "thought_first"):
        rows = fx.make_replay_rows(order)
        cut = sc3.cut_rows_at_episodes(rows, 2, act_order=order)
        # nothing of the third instance survives: no 'REPLAY-OUTCOME' act row, no 'other' thought
        assert not any(r.get("outcome") == "REPLAY-OUTCOME" for r in cut)
        assert not any(r.get("episode_id") == "cbench-v1/other" for r in cut)
        log = {}
        inst = sc3.build_instances(cut, order=order, log=log)
        assert len(inst) == 2 and not log.get("acts_orphaned")
        last = sc3.transcript(inst[-1])
        assert not any("REPLAY-OUTCOME" in e["text"] for e in last)
        # a trailing act row whose thought row never arrived: in acts_first ledgers it is an ORPHAN —
        # dropped and counted, never attached; in thought_first ledgers an act always follows its
        # thought, so it joins the last chunk and the tick mismatch is counted
        orphan_rows = cut + [dict(kind="act", episode_id="cbench-v1/one", tick=1, action="-Z",
                                  outcome="REPLAY-OUTCOME", score=0.9)]
        log2 = {}
        inst2 = sc3.build_instances(orphan_rows, order=order, log=log2)
        if order == "acts_first":
            assert log2.get("acts_orphaned") == 1
            assert not any("REPLAY-OUTCOME" in e["text"] for i in inst2 for e in sc3.transcript(i))
        else:
            assert log2.get("acts_tick_mismatch") == 1 and not log2.get("acts_orphaned")
    # the first row of instance N+1 is its earliest act/note row in acts_first ledgers
    rows = fx.make_rows()
    inst = sc3.build_instances(rows)
    for i in inst[1:]:
        r = rows[i["first_row"]]
        assert r["episode_id"] == i["eid"] and r["kind"] in ("act", "note", "thought")
        assert r["tick"] == i["chunks"][0]["tick"]


def test_head_intro_and_summary_come_from_what_the_child_saw():
    rows = _rows()
    th = next(r for r in rows if r["kind"] == "thought" and r["episode_id"] == "rg/countdown/1000001")
    h = sc3.extract_head(th["prompt"])
    assert h["goal"].startswith("Countdown arithmetic puzzle.") and "Use 3, 4, 5 to reach 35." in h["goal"]
    assert h["metric"].startswith("score =")
    assert h["intro"].startswith("New puzzle (Countdown arithmetic).")
    later = [r for r in rows if r["kind"] == "thought" and r["episode_id"] == "cbench-v1/crc32"][1]
    assert sc3.extract_head(later["prompt"])["intro"] is None, "only tick 1's tail is the intro"
    refl = [r for r in rows if r["kind"] == "reflection"][0]
    assert sc3.extract_reflection_summary(refl["prompt"]) == fx.REFLECTION_SUMMARY
    assert sc3.extract_head("")["goal"] is None
    # the stored prompt's YOU block (bootstrap = birth brief + briefs) is stripped, the state kept
    s = sc3.strip_you_block(th["prompt"])
    assert s.startswith("=== STATE ===") and fx.BIRTH not in s and "GOAL:" in s


def test_transcript_is_causal_and_harness_lines_are_context_only():
    rows = _rows()
    inst = sc3.build_instances(rows)
    child = _child_texts(rows)
    for i in inst:
        els = sc3.transcript(i)
        assert els[0]["role"] == "harness" and els[0]["text"].startswith("GOAL: ")
        assert els[0]["part"] == "head" and not i["head_missing"] and not i["intro_missing"]
        assert all(isinstance(e["ntok"], int) and e["ntok"] > 0 for e in els)
        for j, e in enumerate(els):
            if e["role"] == "child":
                assert e["text"].strip() in child
                c = i["chunks"][e["chunk"]]
                k = j + 1
                following = []
                while k < len(els) and els[k]["role"] == "harness" and els[k]["part"] == "outcome":
                    following.append(els[k]["text"])
                    k += 1
                assert following == [sc3.outcome_line(a) + "\n" for a in c["acts"]], (i["eid"], j)
                if k < len(els):
                    assert els[k]["role"] == "child" or els[k]["part"] == "harness"
            else:
                assert e["text"] not in child
    a = dict(outcome="instructions 100 -> 80 (20.0% reduction)", score=0.2)
    assert sc3.outcome_line(a) == "[OUTCOME] instructions 100 -> 80 (20.0% reduction) (score 0.2000)"
    crc = [i for i in inst if i["eid"] == "cbench-v1/crc32"][0]
    assert crc["chunks"][2]["text"].startswith("ACT: -mem2reg, -sroa, -gvn")


def test_categories_partition_the_target_mass_with_boilerplate_precedence():
    rows = _rows()
    inst = sc3.build_instances(rows)
    for i in inst:
        i["els"] = sc3.transcript(i)
    counts = sc3.categorize(inst, min_instances=3)
    crc = [i for i in inst if i["eid"] == "cbench-v1/crc32"]
    c1 = crc[0]["chunks"]
    assert c1[0]["category"] == "boilerplate", c1[0]["category"]   # BOILER occurs in 3 instances
    assert c1[1]["category"] == "revision" and c1[1]["flags"]["changed_action"] and c1[1]["flags"]["executed"]
    assert c1[2]["category"] == "repeat" and not c1[2]["flags"]["changed_action"]
    q = [i for i in inst if i["eid"] == "cbench-v1/qsort"][0]["chunks"]
    assert q[0]["category"] == "thought" and q[1]["category"] == "action"
    assert set(counts) <= set(sc3.CATEGORIES) and sum(counts.values()) == sum(len(i["chunks"]) for i in inst)
    assert crc[1]["chunks"][1]["category"] == "repeat"
    assert all("harness_echo" in c["flags"] and "n_acts" in c["flags"] for i in inst for c in i["chunks"])


def test_unexecuted_act_lines_are_their_own_category_and_yield_no_move_pair():
    """A Markdown-decorated ACT line the harness never ran ('**ACT:** -x'
    produces no act row in life; canonicalize_dialect rewrites it to
    'ACT: -x') must not count as an action, revision or repeat, and must not
    become a 'what did you try next' pair with a move that was never tried."""
    b = fx.LedgerBuilder()
    b.episode("cbench-v1/fft", [
        ("PREDICT: 0.2\nACT: -gvn", [("-gvn", "instructions 10 -> 9 (x)", 0.1)]),
        ("Let me try a decorated move.\n**ACT:** -instcombine, -peephole**\nNOTE: decorated", []),  # never executed
        ("PREDICT: 0.3\nACT: -licm", [("-licm", "instructions 10 -> 8 (x)", 0.2)]),
    ])
    rows = b.rows
    inst = sc3.build_instances(rows)
    for i in inst:
        i["els"] = sc3.transcript(i)
    counts = sc3.categorize(inst, min_instances=3)
    ch = inst[0]["chunks"]
    assert ch[0]["category"] == "action"
    assert ch[1]["category"] == "unexecuted_act" and ch[1]["flags"]["has_act"] and not ch[1]["flags"]["executed"]
    assert ch[2]["category"] == "revision", "the executed -licm after feedback differs from -gvn"
    assert counts == {"action": 1, "unexecuted_act": 1, "revision": 1}
    log = {}
    pairs = sc3.tmem_pairs(rows, log=log)
    moves = [p for p in pairs if p["type"] == "action"]
    assert [p["output"] for p in moves] == ["-gvn", "-licm"] and all(p["executed"] for p in moves)
    assert log["chunks_with_unexecuted_act_lines"] == 1
    assert 'After the outcome "instructions 10 -> 9 (x)"' in moves[1]["instruction"]
    # the unexecuted chunk is still the child's text: it IS a target in B, under its own category
    d = tempfile.mkdtemp(prefix="v3unex_")
    m = sc3.compile_two_scale(rows, d)
    assert m["target_tokens_by_category"]["unexecuted_act"] > 0 and m["chunk_categories"]["unexecuted_act"] == 1
    # a multi-move chunk: every executed move is a pair with the SAME pre-chunk condition, numbered
    b2 = fx.LedgerBuilder()
    b2.episode("cbench-v1/two", [("ACT: -a\nACT: -b", [("-a", "o-a", 0.1), ("-b", "o-b", 0.2)]),
                                 ("ACT: -c", [("-c", "o-c", 0.3)])])
    pr = [p for p in sc3.tmem_pairs(b2.rows) if p["type"] == "action"]
    assert [p["output"] for p in pr] == ["-a", "-b", "-c"]
    assert "attempt 1)" in pr[0]["instruction"] and "attempt 2)" in pr[1]["instruction"]
    assert "With no attempts made yet" in pr[1]["instruction"], "the 2nd move was written before the 1st outcome"
    assert 'After the outcome "o-b"' in pr[2]["instruction"]


def test_two_scale_corpus_every_chunk_once_per_view_and_only_child_text_carries_loss():
    rows = _rows()
    d = tempfile.mkdtemp(prefix="v3B_")
    m = sc3.compile_two_scale(rows, d)
    corpus = json.load(open(os.path.join(d, "corpus.json")))
    assert corpus["format"] == "v3_spans" and corpus["recipe"] == sc3.RECIPES["B"]
    items = corpus["corpus"]
    child = _child_texts(rows)
    n_chunks = sum(1 for r in rows if r["kind"] == "thought")
    n_refl = sum(1 for r in rows if r["kind"] == "reflection")
    ep_targets = [s[0].strip() for it in items if it["view"] == "episode" for s in it["spans"] if s[1]]
    lo_targets = [s[0].strip() for it in items if it["view"] == "local" for s in it["spans"] if s[1]]
    assert len(ep_targets) == n_chunks + n_refl, (len(ep_targets), n_chunks, n_refl)
    assert len(lo_targets) == n_chunks
    harness_starts = ("GOAL: ", "[OUTCOME] ", "New program: ", "New puzzle (", "Since your last reflection")
    for it in items:
        for text, loss, cat in it["spans"]:
            if loss:
                assert text.strip() in child, text[:80]
                assert cat in sc3.CATEGORIES
                assert not text.startswith(harness_starts)
            else:
                assert cat == "context"
        assert it["group"] and isinstance(it["order"], int)
        assert it["meta"]["target_rows"] and it["meta"]["tokens"] > 0
    assert not any(s[1] for it in items for s in it["spans"] if s[0].startswith(harness_starts))
    assert sum(1 for t in lo_targets if t == canonicalize_dialect(fx.BOILER).strip()) == 3
    assert 0.45 <= m["view_share"]["local"] <= 0.55, m["view_share"]
    assert m["est_target_tokens"] == sum(m["target_tokens_by_category"].values())
    assert set(m["target_tokens_by_category"]) <= set(sc3.CATEGORIES)
    assert m["target_tokens_by_gym"] and m["target_tokens_by_episode_length"]
    assert m["n_instances"] == len(sc3.build_instances(rows)) and not m["empty"]
    assert m["token_measure_kind"] == "estimate" and "chars/3" in m["token_measure"]
    # the memo's 'extra exposure from both views': every chunk row is a target exactly twice
    ex = m["effective_exposures"]
    assert ex["rows_as_target_twice"] == n_chunks and ex["rows_as_target_once"] == n_refl, ex
    assert ex["exposure_histogram"] == {"1": n_refl, "2": n_chunks}
    assert abs(ex["mean_targets_per_child_row"] - 2.0) < 0.2
    # conditioning: every instance had a stored prompt, so no head is missing
    assert m["conditioning"]["items_head_missing"] == 0 and m["conditioning"]["instances_head_missing"] == 0
    assert m["conditioning"]["instances_with_stored_prompt"] == m["n_instances"]
    assert m["log"]["act_row_order"] == "acts_first" and m["max_item_tokens"] <= 7168
    assert not os.path.exists(os.path.join(d, "EMPTY_CORPUS")) and not os.path.exists(os.path.join(d, "LEAK_REFUSED"))
    assert json.load(open(os.path.join(d, "compile_manifest.json")))["recipe"] == sc3.RECIPES["B"]


def test_views_flag_gives_scale_one_alone_or_local_alone():
    rows = _rows()
    n_chunks = sum(1 for r in rows if r["kind"] == "thought")
    n_refl = sum(1 for r in rows if r["kind"] == "reflection")
    d1 = tempfile.mkdtemp(prefix="v3Bs_")
    m1 = sc3.compile_two_scale(rows, d1, views="episode")
    items = json.load(open(os.path.join(d1, "corpus.json")))["corpus"]
    assert {it["view"] for it in items} == {"episode"} and m1["view_share"] == {"episode": 1.0}
    assert sum(1 for it in items for s in it["spans"] if s[1]) == n_chunks + n_refl
    assert m1["params"]["views"] == "episode" and m1["effective_exposures"]["rows_as_target_twice"] == 0
    d2 = tempfile.mkdtemp(prefix="v3Bl_")
    m2 = sc3.compile_two_scale(rows, d2, views="local")
    items2 = json.load(open(os.path.join(d2, "corpus.json")))["corpus"]
    assert {it["view"] for it in items2} == {"local"} and len(items2) == n_chunks
    try:
        sc3.compile_two_scale(rows, tempfile.mkdtemp(), views="nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad --views accepted")


def test_local_view_has_the_real_antecedent_context_and_no_fabricated_header():
    rows = _rows()
    inst = [i for i in sc3.build_instances(rows) if i["eid"] == "cbench-v1/crc32"][0]
    els = sc3.transcript(inst)
    sc3.categorize([inst])
    log = {}
    items = sc3.local_view_items(inst, els, 768, log)
    assert len(items) == 3
    for it in items:
        head = it["spans"][0]
        assert not head[1] and head[0].startswith("GOAL: Optimize program 'cbench-v1/crc32'")
        assert "METRIC:" in head[0]
    ctx2 = [s[0] for s in items[1]["spans"] if not s[1]]
    assert ctx2[-1] == "[OUTCOME] instructions 100 -> 80 (20.0% reduction) (score 0.2000)\n"
    assert ctx2[-2].strip() == canonicalize_dialect(fx.BOILER).strip()
    assert items[1]["spans"][-1][1] and items[1]["spans"][-1][0].startswith("The recipe gave 20%.")
    ctx1 = [s[0] for s in items[0]["spans"] if not s[1]]
    assert len(ctx1) == 2 and ctx1[1].startswith("New program: cbench-v1/crc32.")
    assert log == {}, "nothing truncated at 768 tokens"
    # a tight budget drops the OLDEST elements and logs it; the task text is always kept
    log2 = {}
    tight = sc3.local_view_items(inst, els, 20, log2)
    assert log2.get("local_truncated", 0) >= 1 and log2.get("local_elements_dropped", 0) >= 1
    assert all(it["spans"][0][0].startswith("GOAL:") for it in tight)
    # 'stored' mode = the exact prompt the child saw, its YOU block stripped, left-truncated in tokens
    log3 = {}
    stored = sc3.local_view_items(inst, els, 100, log3, mode="stored")
    assert log3["local_truncated"] == 3 and log3["stored_you_blocks_stripped"] == 3
    for it, c in zip(stored, inst["chunks"]):
        ctx = it["spans"][0][0]
        assert fx.BIRTH not in ctx and "=== YOU ===" not in ctx
        assert sc3.est_tokens(ctx) <= 101
        assert ctx.rstrip("\n").endswith(c["prompt"].rstrip("\n")[-40:]), "the END (recent stream) is kept"
    wide = sc3.local_view_items(inst, els, 5000, {}, mode="stored")
    assert all(it["spans"][0][0].startswith("=== STATE ===") for it in wide)


def test_long_episode_becomes_overlapping_windows_each_target_scored_once():
    rows = _rows()
    inst = [i for i in sc3.build_instances(rows) if i["eid"] == "cbench-v1/adpcm"][0]
    els = sc3.transcript(inst)
    sc3.categorize([inst])
    log = {}
    items = sc3.episode_view_items(inst, els, window_tokens=2000, overlap_tokens=800, log=log)
    assert len(items) > 1 and log["episodes_windowed"] == 1 and log["windows_total"] == len(items)
    targets = [s[0] for it in items for s in it["spans"] if s[1]]
    assert targets == [c["text"] + "\n" for c in inst["chunks"]], "every chunk exactly once, in order"
    for w, it in enumerate(items):
        assert it["meta"]["window"] == w and it["meta"]["n_windows"] == len(items)
        assert it["spans"][0][0].startswith("GOAL:") and not it["spans"][0][1]
        total = sum(sc3.est_tokens(s[0]) for s in it["spans"])
        assert total <= 2000 and total == it["meta"]["tokens"], (total, it["meta"]["tokens"])
        if w > 0:
            assert it["meta"]["overlap_tokens"] > 0, "later windows open with real preceding transcript"
            ctx = [s for s in it["spans"][1:] if not s[1]]
            assert ctx and ctx[0][0] in [e["text"] for e in els], "overlap is actual transcript text"
    order = [e["text"] for e in els]
    for it in items:
        pos = [order.index(s[0]) for s in it["spans"][1:] if s[0] in order]
        assert pos == sorted(pos)
    assert "oversize_chunks" not in log
    log2 = {}
    one = sc3.episode_view_items(inst, els, window_tokens=10 ** 6, overlap_tokens=0, log=log2)
    assert len(one) == 1 and "episodes_windowed" not in log2
    # a window smaller than one chunk still emits every chunk (alone) and counts the oversize
    log3 = {}
    tiny = sc3.episode_view_items(inst, els, window_tokens=200, overlap_tokens=0, log=log3)
    assert len(tiny) == len(inst["chunks"]) and log3["oversize_chunks"] == len(inst["chunks"])


def test_exact_token_sizing_means_the_trainer_never_truncates_or_splits():
    """With the SAME tokenizer at compile and train time every B item fits
    --max-len: the windows the compiler cut are the sequences the trainer
    trains (no head lost, no target lost, no split); a char estimate on a
    tokenizer the estimate misjudges would not give that guarantee."""
    rows = _rows()
    tok = fx.WordTok()
    measure = sc3.TokenMeasure(tok, name="word-tok")
    assert measure.kind == "exact" and measure("a b c\n") == tok.encode("a b c\n").__len__()
    max_len = 700
    d = tempfile.mkdtemp(prefix="v3exact_")
    m = sc3.compile_two_scale(rows, d, max_seq_tokens=max_len, window_overlap_tokens=120,
                              local_context_tokens=150, measure=measure)
    assert m["token_measure_kind"] == "exact" and "word-tok" in m["token_measure"]
    assert m["truncation"].get("episodes_windowed", 0) >= 1, "the long episode was windowed"
    items = tv3.normalize_items(json.load(open(os.path.join(d, "corpus.json"))))
    n_split = n_trunc = 0
    for i, it in enumerate(items):
        segs = tv3.encode_item_segments(it, tok, max_len, item_index=i)
        assert len(segs) == 1, (it["view"], it["meta"].get("tokens"))
        e = segs[0]
        assert len(e) <= max_len and e.target_dropped == 0 and e.context_dropped == 0
        assert len(e) == it["meta"]["tokens"] + 1, "compile-time count == trainer count (+ EOS)"
        n_split += e.n_splits > 1
        n_trunc += bool(e.target_dropped)
    assert n_split == 0 and n_trunc == 0
    assert m["max_item_tokens"] <= max_len - sc3.DEFAULT_RESERVE_TOKENS
    # the exact masses in the manifest equal the trainer's exact target counts
    total_t = sum(sum(len(tok.encode(s[0])) for s in it["spans"] if s[1]) for it in items)
    assert m["est_target_tokens"] == total_t


def test_reflection_rows_are_their_own_episode_items_with_the_summary_masked():
    rows = _rows()
    groups = sc3.reflection_groups(rows)
    assert len(groups) == 1 and groups[0]["at_episode"] == 8
    items = sc3.reflection_items(groups)
    it = items[0]
    assert it["view"] == "episode" and it["category"] == "reflection" and it["group"].endswith(":reflection")
    assert it["spans"][0] == [fx.REFLECTION_SUMMARY + "\n", False, "context"]
    assert [s[0].strip() for s in it["spans"][1:]] == fx.REFLECTION_TEXT
    assert all(s[1] and s[2] == "reflection" for s in it["spans"][1:])
    assert it["meta"]["n_targets"] == 2 and not it["meta"]["summary_missing"]
    assert len(it["meta"]["target_rows"]) == 2


def test_groups_are_stable_neighbourhood_keys():
    assert sc3.group_key("cbench-v1/crc32", None) == "gym:cbench-v1/crc32"
    assert sc3.group_key("cbench-v1/crc32", "compiler") == "compiler:cbench-v1/crc32"
    assert sc3.group_key("rg/countdown/1000001", "reasoning_gym") == "reasoning_gym:rg/countdown"
    assert sc3.group_key("rg/countdown/1000002", "reasoning_gym") == "reasoning_gym:rg/countdown"
    rows = _rows()
    d = tempfile.mkdtemp(prefix="v3B_")
    sc3.compile_two_scale(rows, d)
    items = json.load(open(os.path.join(d, "corpus.json")))["corpus"]
    g = {it["meta"].get("eid"): it["group"] for it in items if it["view"] == "local"}
    assert g["cbench-v1/crc32"] == "gym:cbench-v1/crc32" and g["rg/countdown/1000001"] == "reasoning_gym:rg/countdown"
    assert items == sorted(items, key=lambda it: (it["order"], it["view"])), "time order (trainer shuffles groups)"
    # A's groups: the real exemplar shape 'Program benchmark://chstone-v0/mips. My thinking: ...' keeps the
    # whole id (the old lazy regex stopped at the ':' of 'benchmark://' and collapsed A into one group)
    legacy = sc3.legacy_items(["Program benchmark://chstone-v0/mips. My thinking: try -gvn.",
                               "Program benchmark://cbench-v1/crc32. Q: which passes? A: -sroa",
                               "Program x. Q: which passes improve it?\nA: -gvn -> 1",
                               "Situation rg/countdown/1000001. I tried 3+4*5.",
                               "Principle: read the program first."])
    assert [it["group"] for it in legacy] == ["gym:benchmark://chstone-v0/mips", "gym:benchmark://cbench-v1/crc32",
                                              "gym:x", "gym:rg/countdown", "legacy"]
    assert len({it["group"] for it in legacy}) == 5


def test_head_missing_is_aggregated_when_prompts_were_not_stored():
    rows = _rows(with_prompt=False)
    d = tempfile.mkdtemp(prefix="v3nohead_")
    m = sc3.compile_two_scale(rows, d)
    c = m["conditioning"]
    assert c["instances_with_stored_prompt"] == 0
    assert c["instances_head_missing"] == m["n_instances"] and c["instances_intro_missing"] == m["n_instances"]
    n_local = m["by_view"]["local"]["items"]
    n_ep_windows = sum(1 for it in json.load(open(os.path.join(d, "corpus.json")))["corpus"]
                       if it["view"] == "episode" and it["category"] == "mixed")
    assert c["items_head_missing"] == n_local + n_ep_windows, c
    items = json.load(open(os.path.join(d, "corpus.json")))["corpus"]
    assert all(it["spans"][0][0].startswith("EPISODE: ") for it in items if it["view"] == "local")


def test_harness_echo_in_child_text_is_flagged_and_its_mass_logged():
    b = fx.LedgerBuilder()
    b.episode("cbench-v1/echo", [
        ("PREDICT: 0.2\nACT: -gvn", [("-gvn", "instructions 10 -> 9 (x)", 0.1)]),
        ("[OUTCOME] instructions 10 -> 9 (x) (score 0.1000)\nI wrote the outcome line myself.\nACT: -licm",
         [("-licm", "instructions 10 -> 8 (x)", 0.2)]),
        ("CLOCK: chunk 3/16 | alive 3s\nplain thought", []),
    ])
    inst = sc3.build_instances(b.rows)
    for i in inst:
        i["els"] = sc3.transcript(i)
    sc3.categorize(inst)
    flags = [c["flags"]["harness_echo"] for c in inst[0]["chunks"]]
    assert flags == [False, True, True]
    d = tempfile.mkdtemp(prefix="v3echo_")
    m = sc3.compile_two_scale(b.rows, d)
    he = m["target_tokens_harness_echo"]
    assert he["chunks"] == 2 and he["total"] > 0 and set(he["by_view"]) == {"episode", "local"}
    assert he["total"] == 2 * sum(sc3.est_tokens(c["text"] + "\n") for c in inst[0]["chunks"] if c["harness_echo"])
    assert he["total"] < m["est_target_tokens"]
    # the echoed line is still the child's text: it carries loss (masking it is a decision, stated)
    items = json.load(open(os.path.join(d, "corpus.json")))["corpus"]
    assert any(s[1] and s[0].startswith("[OUTCOME]") for it in items for s in it["spans"])


def test_leak_scan_refuses_parent_text_and_parent_rows_are_stripped_by_default():
    rows = _rows()
    b = fx.LedgerBuilder()
    b.rows = list(rows)
    b.parent("cbench-v1/qsort", 1, "[PARENT] Before you start, say in your own words what your parents asked of you.")
    prow = b.rows
    # default: the parent row is stripped and counted; the corpus is written
    d = tempfile.mkdtemp(prefix="v3leak0_")
    m = sc3.compile_two_scale(prow, d)
    assert m["truncation"]["parent_rows_stripped"] == 1 and m["log"]["leak_hits"] == 0
    assert not any("[PARENT]" in s[0] for it in json.load(open(os.path.join(d, "corpus.json")))["corpus"]
                   for s in it["spans"])
    # --parent-as-context puts it in the spans -> the leak scan refuses (marker, no corpus)
    d2 = tempfile.mkdtemp(prefix="v3leak1_")
    try:
        sc3.compile_two_scale(prow, d2, parent_as_context=True)
    except sc3.LeakError as e:
        assert "[PARENT]" in str(e) or "leak" in str(e).lower()
    else:
        raise AssertionError("parent text in the spans was not refused")
    assert os.path.exists(os.path.join(d2, "LEAK_REFUSED")) and not os.path.exists(os.path.join(d2, "corpus.json"))
    hits = json.load(open(os.path.join(d2, "LEAK_REFUSED")))
    assert hits["n_hits"] >= 1 and hits["hits"][0]["marker"] == "[PARENT]" and hits["hits"][0]["loss"] is False
    # --allow-leak-markers writes it and says so
    d3 = tempfile.mkdtemp(prefix="v3leak2_")
    m3 = sc3.compile_two_scale(prow, d3, parent_as_context=True, allow_leak_markers=True)
    assert m3["log"]["leak_hits"] >= 1 and m3["log"]["leak_markers_allowed"] and os.path.exists(os.path.join(d3, "corpus.json"))
    # the life's own brief text is a leak too (a line of >= 40 chars found in any span)
    brief = "Your best move on crc32 was -mem2reg, -sroa; start there and add gvn when the program is loop-heavy.\n"
    b2 = fx.LedgerBuilder()
    b2.episode("cbench-v1/leaky", [(brief.strip() + "\nACT: -gvn", [("-gvn", "x", 0.1)])])
    d4 = tempfile.mkdtemp(prefix="v3leak3_")
    try:
        sc3.compile_two_scale(b2.rows, d4, brief_texts=[brief])
    except sc3.LeakError:
        pass
    else:
        raise AssertionError("a brief line echoed by the child was not caught")
    assert sc3.leak_scan([dict(spans=[["plain child text\n", True, "thought"]], view="local")], [brief]) == []
    # stored-mode contexts never carry the YOU block (the brief block lives there in life)
    with_brief = []
    for r in rows:
        r = dict(r)
        if r.get("kind") == "thought" and r.get("prompt"):
            r["prompt"] = r["prompt"].replace("=== STATE ===", "=== YOUR BRIEFING FROM LAST SLEEP ===\n"
                                              + brief + "=== STATE ===", 1)
        with_brief.append(r)
    d5 = tempfile.mkdtemp(prefix="v3leak4_")
    m5 = sc3.compile_two_scale(with_brief, d5, local_context="stored", brief_texts=[brief])
    assert m5["log"]["leak_hits"] == 0 and m5["truncation"]["stored_you_blocks_stripped"] > 0
    # the brief-text loader reads sleep_*/waking_brief.txt and parent_brief.txt
    life = tempfile.mkdtemp(prefix="v3life_")
    os.makedirs(os.path.join(life, "sleep_0008"))
    open(os.path.join(life, "sleep_0008", "waking_brief.txt"), "w").write(brief)
    open(os.path.join(life, "sleep_0008", "parent_brief.txt"), "w").write("Think before you act, child of mine.\n")
    assert len(sc3.load_brief_texts(life)) == 2 and sc3.load_brief_texts("/nonexistent") == []


def test_exclusions_horizon_and_empty_corpus():
    rows = fx.make_rows()
    ids = sc3.default_exclusions("compiler")
    assert "cbench-v1/susan" in ids and "npb-v0/10" in ids and "cbench-v1/crc32" not in ids
    kept, n, gone = sc3.exclude_rows(rows, ids)
    assert n > 0 and set(gone) == {"cbench-v1/susan", "npb-v0/10"}
    assert not any(r["episode_id"] in ("cbench-v1/susan", "benchmark://npb-v0/10") for r in kept)
    kept2, n2, gone2 = sc3.exclude_rows(rows, set(), split_of=lambda e: "gate" if e.startswith("rg/") else None)
    assert gone2 == ["rg/countdown/1000001"]
    # per-row gym exclusion on a POOLED ledger: the rg rows (gym='reasoning_gym') are judged by the rg rule,
    # the compiler rows (no gym field -> default gym) by the compiler ids, in ONE pass
    rules = {"compiler": (ids, None),
             "reasoning_gym": (set(), lambda e: "gate" if e.startswith("rg/") else None)}
    kept3, n3, gone3 = sc3.exclude_rows(rows, by_gym=rules, default_gym="compiler")
    assert set(gone3) == {"cbench-v1/susan", "npb-v0/10", "rg/countdown/1000001"}, gone3
    assert n3 == n + n2
    # a row's own gym field wins over the default gym
    rows_g = [dict(r, gym="reasoning_gym") if r["episode_id"].startswith("rg/") else r for r in rows]
    kept4, _n4, gone4 = sc3.exclude_rows(rows_g, by_gym=rules, default_gym="none")
    assert gone4 == ["rg/countdown/1000001"], "compiler rows under default_gym='none' have no rule"
    er = sc3.exclusion_rules("compiler", extra_ids={"cbench-v1/crc32"})
    assert "cbench-v1/crc32" in er["compiler"][0] and "cbench-v1/susan" in er["compiler"][0]
    assert set(er) >= {"compiler", "reasoning_gym"}
    # held-out mentions in recorded exemplars: whole identifiers only
    assert sc3.mentions_heldout("Program cbench-v1/sha. Q: ...", {"cbench-v1/sha"})
    assert not sc3.mentions_heldout("Program cbench-v1/sha_clones. Q: ...", {"cbench-v1/sha"})
    assert sc3.mentions_heldout("Program benchmark://npb-v0/10. x", {"benchmark://npb-v0/10"})
    # horizon: the first 2 instances only
    cut = sc3.cut_rows_at_episodes(rows, 2)
    assert len(sc3.build_instances(cut)) == 2 and len(cut) < len(rows)
    assert sc3.cut_rows_at_episodes(rows, 0) is rows and sc3.cut_rows_at_episodes(rows, 10 ** 6) is rows
    # nothing to write -> EMPTY_CORPUS marker, not a failure
    d = tempfile.mkdtemp(prefix="v3empty_")
    m = sc3.compile_two_scale([r for r in rows if r["kind"] == "act"], d)
    assert m["empty"] and os.path.exists(os.path.join(d, "EMPTY_CORPUS"))
    assert json.load(open(os.path.join(d, "corpus.json")))["corpus"] == []
    m2 = sc3.compile_tmem_qa([], tempfile.mkdtemp(prefix="v3emptyC_"))
    assert m2["empty"] and m2["n_items"] == 0


def test_variant_a_calls_compile_sleep_and_wraps_its_strings():
    rows = _rows()
    calls = []
    real = sc3.compile_sleep

    def spy(model, ledger_rows, out_dir, prior_corpus, vocab=None, vocab_by_gym=None):
        calls.append(dict(n_rows=len(ledger_rows), out_dir=out_dir, vocab=vocab))
        return real(model, ledger_rows, out_dir, prior_corpus, vocab=vocab, vocab_by_gym=vocab_by_gym)
    sc3.compile_sleep = spy
    try:
        d = tempfile.mkdtemp(prefix="v3A_")
        m = sc3.compile_legacy(rows, d)
    finally:
        sc3.compile_sleep = real
    assert len(calls) == 1 and calls[0]["n_rows"] == len(rows)
    legacy = json.load(open(os.path.join(d, "legacy", "corpus.json")))["corpus"]
    assert legacy and all(isinstance(x, str) for x in legacy)
    items = json.load(open(os.path.join(d, "corpus.json")))["corpus"]
    assert [it["spans"][0][0] for it in items] == legacy, "the strings are whole-text targets, in order"
    assert all(len(it["spans"]) == 1 and it["spans"][0][1] and it["view"] == "legacy" for it in items)
    assert m["log"]["targets_child_only"] is False and m["log"]["source"]["compiled"]
    assert any(it["meta"]["reflection"] for it in items), "compile_sleep's [reflection] exemplar is there"
    # the recorded path (P1's W0 as the life recorded it): held-out exemplars are filtered and the
    # filtered v1-shaped corpus is written for the frozen v1 trainer
    rec = os.path.join(d, "recorded.json")
    with open(rec, "w") as f:
        json.dump(dict(corpus=["Program x. Q: which passes improve it?\nA: -gvn -> 1", {"q": "Q", "a": "A text"},
                               "Program cbench-v1/susan. Q: held-out report program?\nA: -gvn -> 0.1",
                               "Program benchmark://npb-v0/10. Q: disjoint panel?\nA: -gvn -> 0.1"]), f)
    d2 = tempfile.mkdtemp(prefix="v3A2_")
    m2 = sc3.compile_legacy(rows, d2, recorded_corpus=rec, held_out_ids=sc3.default_exclusions("compiler"))
    items2 = json.load(open(os.path.join(d2, "corpus.json")))["corpus"]
    assert m2["log"]["source"]["recorded"] == "recorded.json" and len(items2) == 2
    assert m2["log"]["recorded_exemplars_total"] == 4 and m2["log"]["recorded_exemplars_heldout_excluded"] == 2
    assert items2[0]["group"] == "gym:x" and items2[1]["spans"] == [["Q", False, "context"], ["A text", True, "legacy"]]
    v1 = json.load(open(os.path.join(d2, "legacy", "corpus.json")))
    assert v1["corpus"] == ["Program x. Q: which passes improve it?\nA: -gvn -> 1", {"q": "Q", "a": "A text"}]
    assert m2["log"]["source"]["filtered_for_v1"] == "legacy/corpus.json"


def test_variant_c_pairs_are_tmem_shaped_with_verbatim_child_outputs():
    rows = _rows()
    pairs = sc3.tmem_pairs(rows)
    child = _child_texts(rows)
    notes = {n.strip() for r in rows if r["kind"] == "thought"
             for n in re.findall(r"^NOTE:\s*(.+)$", canonicalize_dialect(r["note"]), re.M)}
    assert {r["note"] for r in rows if r["kind"] == "note"} <= notes
    acts = {r["action"] for r in rows if r["kind"] == "act"}
    assert pairs and {p["type"] for p in pairs} == {"action", "note", "reflection"}
    for p in pairs:
        if p["type"] == "note":
            assert p["output"] in notes
        elif p["type"] == "action":
            assert p["output"] in acts and p["executed"]
        else:
            assert p["output"] in child
            assert p["instruction"].startswith("In your private reflection after episode 8")
        if p["type"] != "reflection":
            assert p["instruction"].startswith("Task: Optimize program") or p["instruction"].startswith("Task: Countdown")
    # every executed act row is a pair; every pair's move is an executed act row
    assert sum(1 for p in pairs if p["type"] == "action") == sum(1 for r in rows if r["kind"] == "act")
    crc = [p for p in pairs if p["eid"] == "cbench-v1/crc32" and p["instance"] == 1 and p["type"] == "action"]
    assert "With no attempts made yet" in crc[0]["instruction"]
    assert 'After the outcome "instructions 100 -> 80 (20.0% reduction)"' in crc[1]["instruction"]
    assert crc[1]["output"] == "-mem2reg, -sroa, -gvn"
    assert any(p["output"] == "same again to confirm" for p in pairs if p["type"] == "note")
    d = tempfile.mkdtemp(prefix="v3C_")
    m = sc3.compile_tmem_qa(rows, d)
    arr = json.load(open(os.path.join(d, "tmem_pairs.json")))
    assert isinstance(arr, list) and all(set(x) == {"instruction", "output"} for x in arr)
    items = json.load(open(os.path.join(d, "corpus.json")))["corpus"]
    assert len(items) == len(arr) == m["n_items"]
    assert all(len(it["spans"]) == 2 and not it["spans"][0][1] and it["spans"][1][1] for it in items)
    assert all(it["spans"][1][2] == "tmem_qa" and it["meta"]["chat"] for it in items)
    assert m["log"]["pairs_by_type"]["reflection"] == 2 and m["log"]["chunks_with_unexecuted_act_lines"] == 0
    assert m["log"]["acts_with_empty_move_skipped"] == 0
    # an 'ACT:' with nothing after it is an INVALID act row with no move: skipped and counted
    b = fx.LedgerBuilder()
    b.episode("cbench-v1/empty", [("PREDICT: 0.1\nACT:", [("", "INVALID: empty move", 0.0)])])
    lg = {}
    assert [p for p in sc3.tmem_pairs(b.rows, log=lg) if p["type"] == "action"] == [] and lg["acts_with_empty_move_skipped"] == 1
    assert "NOT FOUND" in m["params"]["loss"] and "deterministic" in m["params"]["extraction"]
    assert m["params"]["moves_from"].startswith("act rows")
    dev = " ".join(m["params"]["tmem_deviations"])
    for word in ("schedule", "eos_as_target", "alpha = r", "dropout 0", "extraction"):
        assert word in dev, word


def test_token_budget_keeps_the_newest_in_full_and_logs_the_drop():
    rows = _rows()
    d = tempfile.mkdtemp(prefix="v3budget_")
    full = sc3.compile_two_scale(rows, d)
    budget = max(200, full["est_target_tokens"] // 3)
    d2 = tempfile.mkdtemp(prefix="v3budget2_")
    m = sc3.compile_two_scale(rows, d2, token_budget=budget, view_ratio=0.7)
    assert m["est_target_tokens"] <= budget + 50
    assert m["n_items"] < full["n_items"]
    assert m["budget"]["episode_items_dropped_by_budget"] + m["budget"]["local_items_dropped_by_budget"] > 0
    assert m["budget"]["episode_target_tokens_kept"] <= int(budget * 0.7)
    assert m["budget"]["local_target_tokens_kept"] <= int(budget * 0.3)
    assert m["budget"]["episode_target_tokens_kept"] + m["budget"]["local_target_tokens_kept"] <= budget
    items = json.load(open(os.path.join(d2, "corpus.json")))["corpus"]
    newest = max(it["order"] for it in json.load(open(os.path.join(d, "corpus.json")))["corpus"])
    assert any(it["order"] == newest for it in items), "the newest rows are read in full"
    # the matched cell of write_ab.sh: B drawn to A's budget stays within it
    d3 = tempfile.mkdtemp(prefix="v3match_")
    ma = sc3.compile_legacy(rows, d3)
    d4 = tempfile.mkdtemp(prefix="v3match2_")
    mb = sc3.compile_two_scale(rows, d4, token_budget=ma["est_target_tokens"])
    assert mb["est_target_tokens"] <= ma["est_target_tokens"] and mb["params"]["token_budget"] == ma["est_target_tokens"]


def test_cli_end_to_end_writes_all_three_variants_and_cell_names():
    rows = fx.make_rows()
    root = tempfile.mkdtemp(prefix="v3cli_")
    led = os.path.join(root, "ledger.jsonl")
    with open(led, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    out = os.path.join(root, "corpora")
    sc3.main(["--ledger", led, "--out", out, "--variants", "A,B,C", "--gym", "compiler",
              "--max-episodes", "0", "--think", "none", "--tokenizer", "none"])
    for v in "ABC":
        assert os.path.exists(os.path.join(out, v, "corpus.json"))
        m = json.load(open(os.path.join(out, v, "compile_manifest.json")))
        assert m["rows_excluded_heldout"] > 0 and "npb-v0/10" in m["excluded_ids"]
        assert m["ledger_sha256"] and m["recipe"] == sc3.RECIPES[v]
        assert m["exclusion_by_row_gym"] and m["leak_scan"] == "refuse" and m["brief_texts_scanned"] == 0
    s = json.load(open(os.path.join(out, "compile_summary.json")))
    assert set(s) == {"A", "B", "C"} and s["B"]["view_share"] and "conditioning" in s["B"]
    # single-variant cells with their own names (write_ab.sh's Bs and B_match) merge into the summary
    sc3.main(["--ledger", led, "--out", out, "--variants", "B", "--views", "episode", "--cell-name", "Bs",
              "--tokenizer", "none"])
    ta = s["A"]["est_target_tokens"]
    sc3.main(["--ledger", led, "--out", out, "--variants", "B", "--cell-name", "B_match",
              "--token-budget", str(ta), "--tokenizer", "none"])
    s2 = json.load(open(os.path.join(out, "compile_summary.json")))
    assert set(s2) == {"A", "B", "C", "Bs", "B_match"}
    assert s2["Bs"]["view_share"] == {"episode": 1.0} and s2["B_match"]["est_target_tokens"] <= ta
    assert json.load(open(os.path.join(out, "B_match", "compile_manifest.json")))["params"]["token_budget"] == ta
    # the deprecated char knobs still work (converted at CHARS_PER_TOKEN)
    sc3.main(["--ledger", led, "--out", os.path.join(root, "chars"), "--variants", "B", "--tokenizer", "none",
              "--episode-window-chars", "6000", "--window-overlap-chars", "1500", "--local-context-chars", "900"])
    mc = json.load(open(os.path.join(root, "chars", "B", "compile_manifest.json")))
    assert mc["params"]["max_seq_tokens"] == 2000 + sc3.DEFAULT_RESERVE_TOKENS
    assert mc["params"]["window_overlap_tokens"] == 500 and mc["params"]["local_context_tokens"] == 300
    # a leak refusal exits non-zero and leaves the marker
    b = fx.LedgerBuilder()
    b.rows = list(rows)
    b.parent("cbench-v1/qsort", 1, "[PARENT] say it in your own words")
    led2 = os.path.join(root, "ledger2.jsonl")
    with open(led2, "w") as f:
        for r in b.rows:
            f.write(json.dumps(r) + "\n")
    try:
        sc3.main(["--ledger", led2, "--out", os.path.join(root, "leak"), "--variants", "B", "--tokenizer", "none",
                  "--parent-as-context"])
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("leak did not exit non-zero")
    assert os.path.exists(os.path.join(root, "leak", "B", "LEAK_REFUSED"))
    assert "LEAK_REFUSED" in json.load(open(os.path.join(root, "leak", "compile_summary.json")))


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
