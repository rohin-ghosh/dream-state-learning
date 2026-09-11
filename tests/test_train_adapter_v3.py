"""train_adapter_v3: the pure-Python encode / pack / collate / mask layer with
a mock tokenizer (any interpreter), and — when torch + peft are importable —
the real path on a tiny random Qwen2: block-diagonal isolation verified
numerically, position reset, LoRA layer selection, SVD init, SGD, no-pack
fallback, EMPTY_CORPUS and the manifest.

  <python> tests/test_train_adapter_v3.py
  <python> -m pytest tests/test_train_adapter_v3.py -q
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import v3_fixtures as fx  # noqa: E402
from organism_v6 import train_adapter_v3 as tv3  # noqa: E402
from organism_v6 import sleep_compile_v3 as sc3  # noqa: E402

SKIPPED = []


def _torch_ok():
    try:
        import torch  # noqa: F401
        import peft  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _items(**kw):
    rows = fx.make_rows(**kw)
    rows, _n, _ids = sc3.exclude_rows(rows, sc3.default_exclusions("compiler"))
    d = tempfile.mkdtemp(prefix="tv3_")
    sc3.compile_two_scale(rows, d)
    return tv3.normalize_items(json.load(open(os.path.join(d, "corpus.json")))), rows


def test_normalize_accepts_every_corpus_shape():
    raw = dict(corpus=["plain v1 text",
                       {"q": "question", "a": "answer"},
                       {"context": "ctx", "target": "tgt", "group": "g", "category": "action"},
                       {"spans": [["a", False, "context"], ["b", True, "thought"]], "group": "g2",
                        "view": "local", "category": "thought", "order": 7, "meta": {"x": 1}}])
    items = tv3.normalize_items(raw)
    assert [it["view"] for it in items] == ["legacy", "item", "item", "local"]
    assert items[0]["spans"] == [["plain v1 text", True, "legacy"]]
    assert items[1]["spans"] == [["question", False, "context"], ["answer", True, "target"]]
    assert items[2]["spans"][1] == ["tgt", True, "action"] and items[2]["group"] == "g"
    assert items[3]["order"] == 7 and items[3]["meta"] == {"x": 1}
    assert tv3.normalize_items([]) == []


def test_encode_masks_context_appends_eos_and_truncates_context_first():
    tok = fx.MockTok()
    item = dict(spans=[["GOAL: x\n", False, "context"], ["child text\n", True, "thought"],
                       ["[OUTCOME] y\n", False, "context"], ["more child\n", True, "action"]],
                group="g", view="episode", order=0, meta={})
    e = tv3.encode_item(item, tok, 10 ** 6)
    n_ctx = len("GOAL: x\n") + len("[OUTCOME] y\n")
    n_tgt = len("child text\n") + len("more child\n")
    assert len(e.ids) == n_ctx + n_tgt + 1 and e.n_target == n_tgt + 1
    assert e.labels[:len("GOAL: x\n")] == [tv3.IGNORE] * len("GOAL: x\n")
    assert e.ids[-1] == tok.eos_token_id and e.labels[-1] == tok.eos_token_id and e.cats[-1] == "action"
    assert sorted(set(c for c in e.cats if c)) == ["action", "thought"]
    assert all((lab == tv3.IGNORE) == (cat is None) for lab, cat in zip(e.labels, e.cats))
    # truncation: LEADING context goes first (5 of the 8 GOAL tokens), targets untouched
    total = n_ctx + n_tgt + 1
    e2 = tv3.encode_item(item, tok, total - 5)
    assert len(e2.ids) == total - 5 and e2.target_dropped == 0 and e2.context_dropped == 5
    assert e2.ids[-1] == tok.eos_token_id and e2.n_target == n_tgt + 1
    # deeper cuts must take interleaved context and target tokens from the left, and log both
    e3 = tv3.encode_item(item, tok, total - 12)
    assert len(e3.ids) == total - 12 and e3.context_dropped == 8 and e3.target_dropped == 4
    e4 = tv3.encode_item(item, tok, 6)
    assert len(e4.ids) == 6 and e4.target_dropped > 0 and e4.context_dropped == n_ctx
    # no target -> None
    assert tv3.encode_item(dict(spans=[["only ctx", False, "context"]], group="g", view="v", order=0, meta={}),
                           tok, 100) is None
    # chat template: the user turn is masked, the answer is the target
    c = tv3.encode_item(dict(spans=[["Q?", False, "context"], ["A.", True, "tmem_qa"]], group="g", view="tmem_qa",
                             order=0, meta={}), tok, 1000, chat_template=True)
    prompt = tok.apply_chat_template([{"role": "user", "content": "Q?"}], tokenize=False, add_generation_prompt=True)
    assert c.labels[:len(prompt)] == [tv3.IGNORE] * len(prompt) and c.n_target == len("A.") + 1
    assert c.ids[len(prompt):-1] == tok.encode("A.")


def test_split_overflow_keeps_the_head_in_every_segment_and_every_target_once():
    """An item longer than max_len is split at a span boundary: every segment
    opens with the head (the task text), carries up to the overlap of the
    preceding spans as zero-loss context, and the target tokens of all
    segments together are the item's target tokens exactly once. The old
    left-truncation (overflow='truncate') dropped the head and the earliest
    targets."""
    tok = fx.MockTok()
    head = "GOAL: optimise the thing\nMETRIC: fewer instructions\n"
    spans = [[head, False, "context"]]
    for k in range(12):
        spans.append([f"turn {k}: some child thinking here, with a move\nACT: -pass{k}\n", True, "action"])
        spans.append([f"[OUTCOME] instructions 100 -> {99 - k} (x) (score 0.0{k})\n", False, "context"])
    item = dict(spans=spans, group="g", view="episode", order=0, meta={})
    full = tv3.encode_item(item, tok, 10 ** 6)
    n_target_full = full.n_target - 1                         # minus EOS
    max_len = 260
    segs = tv3.encode_item_segments(item, tok, max_len, item_index=3, overlap_tokens=60)
    assert len(segs) > 1 and all(len(e) <= max_len for e in segs)
    assert [e.split_index for e in segs] == list(range(len(segs))) and all(e.n_splits == len(segs) for e in segs)
    assert all(e.item_index == 3 and e.group == "g" and e.view == "episode" for e in segs)
    head_ids = tok.encode(head)
    for e in segs:
        assert e.ids[:len(head_ids)] == head_ids, "every segment opens with the head"
        assert e.labels[:len(head_ids)] == [tv3.IGNORE] * len(head_ids)
        assert e.ids[-1] == tok.eos_token_id and e.labels[-1] == tok.eos_token_id
    # target tokens: all of them, once, in order (EOS per segment excluded)
    got = [t for e in segs for t, lab in zip(e.ids[:-1], e.labels[:-1]) if lab != tv3.IGNORE]
    want = [t for t, lab in zip(full.ids[:-1], full.labels[:-1]) if lab != tv3.IGNORE]
    assert got == want and len(got) == n_target_full
    assert sum(e.target_dropped for e in segs) == 0
    # the only context that may go is a TRAILING outcome line no target follows (zero loss anyway)
    last_outcome = len(tok.encode(spans[-1][0]))
    assert sum(e.context_dropped for e in segs) in (0, last_outcome)
    # every context span that precedes a target is in the same segment as that target or in its overlap
    ctx_spans = [s[0] for s in spans[1:-1] if not s[1]]
    seg_texts = ["".join(chr(t - 3) if 32 <= t - 3 < 127 or t - 3 == 10 else "?" for t in e.ids) for e in segs]
    assert all(any(c in st for st in seg_texts) for c in ctx_spans)
    # later segments carry real preceding spans as zero-loss overlap right after the head
    e1 = segs[1]
    after_head = e1.ids[len(head_ids):]
    k = 0
    while k < len(after_head) and e1.labels[len(head_ids) + k] == tv3.IGNORE:
        k += 1
    assert k > 0, "segment 2 opens with zero-loss overlap context"
    assert bytes(after_head[:k]) in bytes(full.ids), "the overlap is text of the item itself"
    # a single span larger than the room: its tail is kept and the loss counted
    big = dict(spans=[[head, False, "context"], ["x" * 500, True, "thought"]], group="g", view="v", order=0, meta={})
    bs = tv3.encode_item_segments(big, tok, 100)
    assert len(bs) == 1 and len(bs[0]) == 100 and bs[0].target_dropped == 500 - (100 - 1 - len(head_ids))
    assert bs[0].ids[:len(head_ids)] == head_ids
    # truncate mode is the old behaviour (one segment, leading context dropped first)
    tr = tv3.encode_item_segments(item, tok, max_len, overflow="truncate")
    assert len(tr) == 1 and tr[0].context_dropped > 0 and tr[0].ids[:len(head_ids)] != head_ids
    # chat template: the prompt is the head of every segment
    ci = dict(spans=[["Q?", False, "context"], ["A. " * 40, True, "tmem_qa"], ["B. " * 40, True, "tmem_qa"]],
              group="g", view="tmem_qa", order=0, meta={})
    prompt = tok.apply_chat_template([{"role": "user", "content": "Q?"}], tokenize=False, add_generation_prompt=True)
    cs = tv3.encode_item_segments(ci, tok, len(prompt) + 130, chat_template=True, overlap_tokens=0)
    assert len(cs) == 2 and all(e.ids[:len(prompt)] == tok.encode(prompt) for e in cs)
    # an item that fits is one segment identical to encode_item
    one = tv3.encode_item_segments(item, tok, 10 ** 6)
    assert len(one) == 1 and one[0].ids == full.ids and one[0].labels == full.labels and one[0].n_splits == 1
    assert tv3.encode_item_segments(dict(spans=[["ctx", False, "context"]], group="g", view="v", order=0, meta={}),
                                    tok, 100) == []


def test_pack_by_group_never_mixes_groups_and_respects_max_len():
    tok = fx.MockTok()
    items, _ = _items()
    enc = [tv3.encode_item(it, tok, 4000, item_index=i) for i, it in enumerate(items)]
    enc = [e for e in enc if e is not None]
    packs = tv3.pack_by_group(enc, 4000)
    assert sum(len(p) for p in packs) == len(enc)
    for p in packs:
        assert len({e.group for e in p}) == 1
        assert sum(len(e) for e in p) <= 4000 or len(p) == 1
        assert [e.order for e in p] == sorted(e.order for e in p), "time order inside a group"
    assert len(packs) < len(enc), "several items share a sequence"
    assert len({p[0].group for p in packs}) == len({e.group for e in enc})
    single = tv3.pack_by_group(enc, 4000, pack=False)
    assert all(len(p) == 1 for p in single) and len(single) == len(enc)


def test_epoch_order_shuffles_group_blocks_deterministically():
    tok = fx.MockTok()
    items, _ = _items()
    enc = [e for e in (tv3.encode_item(it, tok, 4000, item_index=i) for i, it in enumerate(items)) if e]
    packs = tv3.pack_by_group(enc, 4000)
    o0 = tv3.epoch_order(packs, 0, 0)
    o0b = tv3.epoch_order(packs, 0, 0)
    o1 = tv3.epoch_order(packs, 0, 1)
    ids = lambda o: [id(p) for p in o]  # noqa: E731
    assert ids(o0) == ids(o0b) and sorted(ids(o0)) == sorted(ids(packs))
    assert ids(o0) != ids(o1) or len({p[0].group for p in packs}) < 3
    # inside a group block the order is unchanged
    for o in (o0, o1):
        seen = {}
        for p in o:
            seen.setdefault(p[0].group, []).append(p[0].order)
        for g, orders in seen.items():
            assert orders == [p[0].order for p in packs if p[0].group == g]
    assert [id(p) for p in tv3.epoch_order(packs, 0, 3, shuffle_groups=False)] == ids(packs)


def test_collate_resets_positions_masks_segment_starts_and_builds_block_mask():
    tok = fx.MockTok()
    a = tv3.encode_item(dict(spans=[["ab", False, "context"], ["cd", True, "thought"]], group="g", view="v",
                             order=0, meta={}), tok, 100)
    b = tv3.encode_item(dict(spans=[["xyz", True, "action"]], group="g", view="v", order=1, meta={}), tok, 100)
    batch = tv3.collate([[a, b], [a]], pad_id=0)
    L = len(a) + len(b)
    assert [len(x) for x in batch["input_ids"]] == [L, L]
    assert batch["position_ids"][0] == list(range(len(a))) + list(range(len(b)))
    assert batch["segment_ids"][0] == [0] * len(a) + [1] * len(b)
    assert batch["segment_ids"][1] == [0] * len(a) + [-1] * len(b)
    assert batch["labels"][0][0] == tv3.IGNORE and batch["labels"][0][len(a)] == tv3.IGNORE, "segment starts"
    assert batch["labels"][0][len(a) + 1:len(a) + len(b)] == b.labels[1:]
    assert batch["labels"][1][len(a):] == [tv3.IGNORE] * len(b) and batch["input_ids"][1][len(a):] == [0] * len(b)
    assert batch["n_tokens"] == 2 * len(a) + len(b)
    allowed = tv3.block_causal_allowed(batch["segment_ids"][0])
    for i in range(L):
        for j in range(L):
            same = (i < len(a)) == (j < len(a))
            assert allowed[i][j] == ((same and j <= i) or i == j)
    allowed2 = tv3.block_causal_allowed(batch["segment_ids"][1])
    for i in range(len(a), L):
        assert allowed2[i] == [k == i for k in range(L)], "pads attend to themselves only"


def test_cli_parser_builds_the_config_and_the_tmem_cell():
    args = tv3.build_parser().parse_args(["--corpus", "c.json", "--out", "o"])
    cfg = tv3.config_from_args(args)
    assert cfg.rank == 32 and cfg.alpha == 0 and cfg.lr == 1e-4 and cfg.epochs == 3 and cfg.max_len == 7168
    assert cfg.overflow == "split" and cfg.split_overlap_tokens == 0 and cfg.note == ""
    assert cfg.pack and cfg.shuffle_groups and cfg.optimizer == "adamw" and cfg.target_modules == tv3.ALL_PROJ
    assert cfg.layers == "all" and not cfg.svd_init and not cfg.freeze_a and not cfg.chat_template
    assert cfg.isolation_check == "auto" and cfg.dtype == "bf16" and cfg.device == "cuda" and cfg.add_eos
    tm = tv3.config_from_args(tv3.build_parser().parse_args(
        ["--corpus", "c.json", "--out", "o", "--rank", "6", "--alpha", "6", "--dropout", "0",
         "--target-modules", "gate_proj,up_proj,down_proj",
         "--layers", "last4", "--svd-init", "--svd-scale", "sigma", "--freeze-a", "--optimizer", "sgd",
         "--lr", "5e-4", "--epochs", "5", "--batch-size", "16", "--no-pack", "--chat-template", "--max-len", "2048",
         "--overflow", "truncate", "--manifest-note", "C_tmem deviations: one offline pass"]))
    assert tm.rank == 6 and tm.alpha == 6 and tm.dropout == 0 and tm.target_modules == tv3.FFN_PROJ
    assert tm.layers == "last4" and tm.svd_init
    assert tm.freeze_a and tm.optimizer == "sgd" and tm.lr == 5e-4 and tm.epochs == 5 and tm.batch_size == 16
    assert not tm.pack and tm.chat_template and tm.max_len == 2048
    assert tm.overflow == "truncate" and tm.note.startswith("C_tmem")
    try:
        tv3.lora_config(tv3.TrainConfig(layers="middle"), 28)
    except ValueError:
        pass
    except ImportError:
        SKIPPED.append("peft not importable (lora_config)")
        print("SKIP peft not importable")
    else:
        raise AssertionError("bad --layers accepted")


def _tiny_model(vocab=256, layers=2):
    import torch
    from transformers import Qwen2Config, Qwen2ForCausalLM
    torch.manual_seed(0)
    cfg = Qwen2Config(vocab_size=vocab, hidden_size=32, intermediate_size=64, num_hidden_layers=layers,
                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=4096,
                      tie_word_embeddings=False)
    cfg._attn_implementation = "eager"
    return Qwen2ForCausalLM(cfg).float()


def test_torch_block_mask_matches_reference_and_isolation_holds_on_a_tiny_model():
    if not _torch_ok():
        SKIPPED.append("torch/peft not importable")
        print("SKIP torch/peft not importable")
        return
    import torch
    tok = fx.MockTok()
    seg = torch.tensor([[0, 0, 0, 1, 1, -1], [0, 0, 1, 1, 2, 2]])
    m = tv3.block_mask_tensor(seg, torch.float32)
    assert m.shape == (2, 1, 6, 6)
    for bi in range(2):
        ref = tv3.block_causal_allowed(seg[bi].tolist())
        got = (m[bi, 0] == 0).tolist()
        assert got == ref
    model = _tiny_model()
    a = tv3.encode_item(dict(spans=[["GOAL: one\n", False, "context"], ["first chunk of thought\n", True, "thought"]],
                             group="g", view="v", order=0, meta={}), tok, 100)
    b = tv3.encode_item(dict(spans=[["second item, different text entirely\n", True, "action"]],
                             group="g", view="v", order=1, meta={}), tok, 100)
    res = tv3.isolation_check(model, [a, b], 0, torch.device("cpu"), torch.float32, tol=1e-4)
    assert res["ran"] and res["ok"] and res["verdict"] == "isolated", res
    assert res["diff_negative_control"] > 1e-2, "without the block mask the second segment sees the first"


def test_torch_end_to_end_training_manifest_and_fallbacks():
    if not _torch_ok():
        SKIPPED.append("torch/peft not importable")
        print("SKIP torch/peft not importable")
        return
    import torch
    tok = fx.MockTok()
    items, _rows = _items(long_episode=False, with_clones=False)
    cfg = tv3.TrainConfig(rank=4, lr=1e-3, epochs=2, max_len=1500, seed=1, device="cpu", dtype="fp32",
                          grad_checkpoint=False, log_every=1, model="tiny-qwen2")
    out = tempfile.mkdtemp(prefix="tv3out_")
    m = tv3.run_training(items, tok, _tiny_model(), cfg, out, corpus_sha="abc", corpus_name="corpus.json",
                         log=lambda s: None)
    assert os.path.exists(os.path.join(out, "DONE")) and os.path.exists(os.path.join(out, "adapter_config.json"))
    mm = json.load(open(os.path.join(out, "train_manifest.json")))
    assert mm["recipe"] == tv3.RECIPE and mm["corpus"]["sha256"] == "abc" and mm["steps"] > 0
    assert mm["packing"]["mode"] == "block4d_by_group" and mm["packing"]["isolation_check"]["verdict"] == "isolated"
    assert mm["packing"]["mean_segments_per_sequence"] > 1
    assert mm["tokens"]["target"] == sum(mm["tokens"]["target_by_category"].values())
    assert set(mm["tokens"]["target_by_view"]) == {"episode", "local"}
    assert mm["lora"]["rank"] == 4 and mm["lora"]["alpha"] == 8 and mm["lora"]["trainable_params"] > 0
    assert mm["lora"]["scaling"] == 2.0
    assert len(mm["mean_loss_per_epoch"]) == 2 and all(x > 0 for x in mm["mean_loss_per_epoch"])
    assert mm["tokens_per_s"] > 0 and mm["config"]["seed"] == 1 and mm["versions"]["torch"]
    assert mm["truncation"]["overflow"] == "split" and mm["truncation"]["target_tokens_dropped"] == 0
    assert "items_split" in mm["truncation"] and mm["truncation"]["max_segment_tokens"] <= 1500
    assert mm["note"] is None
    meta = json.load(open(os.path.join(out, "train_meta.json")))
    assert meta["seed"] == 1 and meta["rank"] == 4
    # TMEM-style cell: FFN of the last layer only, SVD-init frozen A, SGD, no packing, chat template
    cfg2 = tv3.TrainConfig(rank=3, alpha=3, dropout=0.0, lr=5e-4, epochs=1, max_len=1500, seed=0, device="cpu",
                           dtype="fp32", grad_checkpoint=False, pack=False, optimizer="sgd", batch_size=4,
                           target_modules=list(tv3.FFN_PROJ), layers="last1", svd_init=True, freeze_a=True,
                           chat_template=True, log_every=0, model="tiny-qwen2",
                           note="C_tmem: alpha = r, dropout 0; one offline pass (TMEM: per-trigger online)")
    base = _tiny_model(layers=2)
    W = {n: p.detach().clone() for n, p in base.named_parameters() if "mlp" in n and "weight" in n}
    out2 = tempfile.mkdtemp(prefix="tv3out2_")
    from organism_v6 import lora_svd_init as lsi
    m2 = tv3.run_training(items[:12], tok, base, cfg2, out2, log=lambda s: None)
    assert m2["packing"]["mode"] == "one_item_per_sequence" and m2["svd_init"]["n_matrices"] == 3
    assert m2["lora"]["alpha"] == 3 and m2["lora"]["scaling"] == 1.0 and m2["lora"]["dropout"] == 0.0
    assert m2["note"].startswith("C_tmem")
    names = set(m2["svd_init"]["matrices"])
    assert all(".layers.1.mlp." in n for n in names), names
    assert m2["lora"]["trainable_params"] == sum(v["shape"][0] * 3 for v in m2["svd_init"]["matrices"].values()), \
        "only B (d_out x r) is trainable when A is frozen"
    # the saved A equals the SVD subspace of the base weight; B started at zero and moved
    from safetensors.torch import load_file
    sd = load_file(os.path.join(out2, "adapter_model.safetensors"))
    a_keys = [k for k in sd if "lora_A" in k]
    assert len(a_keys) == 3 and all("layers.1.mlp" in k for k in a_keys)
    for k in a_keys:
        base_key = k.replace("base_model.model.", "").replace(".lora_A.weight", ".weight").replace(".lora_A.default.weight", ".weight")
        A0 = lsi.svd_subspace(W[base_key], 3)
        assert torch.allclose(sd[k].float(), A0, atol=1e-4), k
        bk = k.replace("lora_A", "lora_B")
        assert sd[bk].abs().sum() > 0, "B trained"
    # empty corpus -> marker, no adapter
    out3 = tempfile.mkdtemp(prefix="tv3out3_")
    m3 = tv3.run_training([dict(spans=[["ctx only", False, "context"]], group="g", view="v", order=0, meta={})],
                          tok, _tiny_model(), cfg, out3, log=lambda s: None)
    assert m3["empty"] and os.path.exists(os.path.join(out3, "EMPTY_CORPUS")) and not os.path.exists(os.path.join(out3, "DONE"))
    # a model that refuses the 4-D mask falls back to one item per sequence and says so
    class Refuser(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner
            self.config = inner.config

        def forward(self, input_ids=None, attention_mask=None, labels=None, position_ids=None, **kw):
            if attention_mask is not None and attention_mask.dim() == 4:
                raise ValueError("custom 4D masks unsupported here")
            return self.inner(input_ids=input_ids, attention_mask=attention_mask, labels=labels, **kw)

        def named_parameters(self, *a, **k):
            return self.inner.named_parameters(*a, **k)

        def parameters(self, *a, **k):
            return self.inner.parameters(*a, **k)

        def save_pretrained(self, d):
            self.inner.save_pretrained(d)
    cfg4 = tv3.TrainConfig(rank=2, lr=1e-3, epochs=1, max_len=1500, seed=0, device="cpu", dtype="fp32",
                           grad_checkpoint=False, log_every=0, model="tiny-qwen2", max_steps=2)
    out4 = tempfile.mkdtemp(prefix="tv3out4_")
    m4 = tv3.run_training(items[:6], tok, Refuser(_tiny_model()), cfg4, out4, log=lambda s: None)
    assert m4["packing"]["mode"].startswith("fallback_one_item_per_sequence"), m4["packing"]["mode"]
    assert m4["packing"]["isolation_check"]["verdict"] == "mask_refused"
    assert m4["steps"] == 2 and os.path.exists(os.path.join(out4, "DONE"))


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
