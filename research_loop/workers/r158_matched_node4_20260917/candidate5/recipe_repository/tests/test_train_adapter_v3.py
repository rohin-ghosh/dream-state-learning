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
import copy
from dataclasses import asdict, replace
from pathlib import Path
import shutil
from unittest.mock import patch

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


def _warm_fixture(directory):
    parent = Path(directory) / "parent"
    parent.mkdir()
    cfg = tv3.TrainConfig(rank=2, alpha=4, dropout=.05, lr=1e-3, epochs=1, max_len=64,
                          pack=False, batch_size=1, device="cpu", dtype="fp32", model="tiny-qwen2",
                          grad_checkpoint=False, log_every=0)
    manifest = dict(recipe=tv3.RECIPE, config=asdict(cfg), base_model=cfg.model, empty=False,
                    steps=1, nonfinite_batches=0, final_loss=1.0, lora=dict(n_layers=2))
    saved = dict(base_model_name_or_path=cfg.model, r=2, lora_alpha=4, lora_dropout=.05,
                 target_modules=cfg.target_modules, bias="none", peft_type="LORA")
    (parent / "DONE").write_text("ok\n")
    (parent / "train_manifest.json").write_text(json.dumps(manifest))
    (parent / "adapter_config.json").write_text(json.dumps(saved))
    (parent / "adapter_model.bin").write_bytes(b"CPU metadata fixture, not loadable weights")
    return parent, cfg


def _warm_error(operation, fragment=None):
    try:
        operation()
    except (ValueError, FileNotFoundError) as error:
        if fragment is not None:
            assert fragment in str(error), (fragment, str(error))
    else:
        raise AssertionError("invalid warm start was accepted")


def _warm_torch_available(native=False):
    try:
        import torch
        if native:
            import peft
            import transformers
            import safetensors
        return True
    except ImportError:
        reason = "warm-start native torch/peft/transformers/safetensors unavailable" if native else "warm-start torch unavailable"
        SKIPPED.append(reason)
        print("SKIP", reason)
        return False


def test_warm_cli_keeps_config_dictionary_and_default_delegation_exact():
    plain = tv3.build_parser().parse_args(["--corpus", "c", "--out", "o"])
    warm = tv3.build_parser().parse_args(["--corpus", "c", "--out", "o", "--init-adapter", "parent"])
    assert plain.init_adapter is None and warm.init_adapter == "parent"
    cfg = tv3.config_from_args(plain)
    assert asdict(cfg) == asdict(tv3.config_from_args(warm)) and "init_adapter" not in asdict(cfg)
    result, model, tokenizer = object(), object(), object()
    with patch.object(tv3, "_run_training", return_value=result) as delegated:
        assert tv3.run_training([], tokenizer, model, cfg, "o", "hash", "c", print) is result
    delegated.assert_called_once_with([], tokenizer, model, cfg, "o", "hash", "c", print)


def test_warm_parent_pins_bytes_and_allows_changed_lr_only_as_nonstructural_config():
    with tempfile.TemporaryDirectory(prefix="tv3-warm-metadata-") as directory:
        parent, cfg = _warm_fixture(directory)
        original = tv3._warm_inventory(parent)
        state = tv3._warm_parent(parent, Path(directory) / "child", replace(cfg, lr=1e-5, epochs=0, seed=2))
        assert state["parent_files"] == original and state["parent"] == parent
        assert state["cumulative_steps"] == 1 and tv3._warm_inventory(parent) == original
        for changed in (replace(cfg, rank=4), replace(cfg, alpha=8), replace(cfg, dropout=0),
                        replace(cfg, target_modules=["q_proj"]), replace(cfg, layers="last1"),
                        replace(cfg, model="wrong-base"), replace(cfg, svd_init=True), replace(cfg, freeze_a=True)):
            _warm_error(lambda: tv3._warm_parent(parent, Path(directory) / "child", changed))


def test_warm_parent_rejects_stale_overlap_symlink_incomplete_and_ambiguous_artifacts():
    with tempfile.TemporaryDirectory(prefix="tv3-warm-paths-") as directory:
        parent, cfg = _warm_fixture(directory)
        child = Path(directory) / "child"
        for output in (parent, parent / "child", parent.parent):
            _warm_error(lambda: tv3._warm_parent(parent, output, cfg))
        alias = Path(directory) / "alias"
        alias.symlink_to(parent, target_is_directory=True)
        _warm_error(lambda: tv3._warm_parent(alias, child, cfg), "symlink")
        (parent / "alias.bin").symlink_to(parent / "adapter_model.bin")
        _warm_error(lambda: tv3._warm_parent(parent, child, cfg), "symlink")
        (parent / "alias.bin").unlink()
        for name in ("DONE", "train_manifest.json", "adapter_config.json", "adapter_model.bin"):
            content = (parent / name).read_bytes()
            (parent / name).unlink()
            _warm_error(lambda: tv3._warm_parent(parent, child, cfg))
            (parent / name).write_bytes(content)
        (parent / "adapter_model.safetensors").write_bytes(b"ambiguous")
        _warm_error(lambda: tv3._warm_parent(parent, child, cfg), "ambiguous")


def test_warm_parent_change_during_write_invalidates_done_even_on_return():
    with tempfile.TemporaryDirectory(prefix="tv3-warm-immutable-") as directory:
        parent, cfg = _warm_fixture(directory)
        child = Path(directory) / "child"

        def changed_parent(*args):
            child.mkdir()
            args[-1]["owns_output"] = True
            (child / "DONE").write_text("would otherwise look complete")
            (parent / "adapter_model.bin").write_bytes(b"external mutation fixture")
            return {}

        with patch.object(tv3, "_run_training", side_effect=changed_parent):
            _warm_error(lambda: tv3.run_training([], None, None, cfg, child, init_adapter=parent), "immutable parent")
        assert child.exists() and not (child / "DONE").exists()


def test_warm_output_creation_race_does_not_remove_another_writers_done():
    with tempfile.TemporaryDirectory(prefix="tv3-warm-race-") as directory:
        parent, cfg = _warm_fixture(directory)
        child = Path(directory) / "child"

        def another_writer(*args):
            child.mkdir()
            (child / "DONE").write_text("another writer")
            raise FileExistsError("another writer owns output")

        with patch.object(tv3, "_run_training", side_effect=another_writer):
            try:
                tv3.run_training([], None, None, cfg, child, init_adapter=parent)
            except FileExistsError:
                pass
            else:
                raise AssertionError("creation race was ignored")
        assert (child / "DONE").read_text() == "another writer"


def test_warm_saved_config_strict_structural_validation_cpu():
    expected = dict(r=2, lora_alpha=4, lora_dropout=.05, target_modules={"q_proj", "v_proj"},
                    bias="none", peft_type="LORA", layers_to_transform=None, rank_pattern={}, alpha_pattern={},
                    modules_to_save=None, use_dora=False, use_rslora=False, inference_mode=False,
                    base_model_name_or_path=None)
    saved = dict(expected, target_modules=["q_proj", "v_proj"], inference_mode=True,
                 base_model_name_or_path="tiny-qwen2", auto_mapping={"base_model_class": "Qwen2ForCausalLM"})
    tv3._warm_validate_config(saved, expected)
    for key, value in (("r", 4), ("lora_alpha", 8), ("lora_dropout", 0), ("bias", "all"),
                       ("target_modules", ["q_proj"]), ("target_modules", ["q_proj", "q_proj", "v_proj"]),
                       ("layers_to_transform", [0]), ("rank_pattern", {"q_proj": 4}), ("alpha_pattern", {"q_proj": 8}),
                       ("modules_to_save", ["lm_head"]), ("use_dora", True), ("use_rslora", True),
                       ("unknown_structure", True)):
        _warm_error(lambda: tv3._warm_validate_config(dict(saved, **{key: value}), expected))
    missing = dict(saved)
    del missing["r"]
    _warm_error(lambda: tv3._warm_validate_config(missing, expected))


def test_warm_state_exact_keys_shapes_finiteness_and_dtype_inventory_cpu():
    if not _warm_torch_available():
        return
    import torch
    expected = {"base_model.model.q_proj.lora_A.weight": torch.ones(2, 4),
                "base_model.model.q_proj.lora_B.weight": torch.zeros(4, 2)}
    actual = {name: value.clone() for name, value in expected.items()}
    inventory = tv3._warm_validate_state(actual, expected)
    assert inventory == tv3._warm_state_inventory(actual)
    assert all(row["dtype"] == "torch.float32" and len(row["sha256"]) == 64 for row in inventory.values())
    first = next(iter(actual))
    bad = [{}, dict(actual, unexpected=torch.ones(1)), {first: actual[first]}]
    for tensor in (torch.zeros(1), torch.full((2, 4), float("nan")), torch.full((2, 4), float("inf")),
                   torch.ones(2, 4, dtype=torch.int64)):
        bad.append(dict(actual, **{first: tensor}))
    for state in bad:
        _warm_error(lambda: tv3._warm_validate_state(state, expected))
    cast = {name: value.to(torch.bfloat16) for name, value in actual.items()}
    assert tv3._warm_validate_state(cast, expected)[first]["dtype"] == "torch.bfloat16"


def test_warm_trainability_requires_one_adapter_and_only_all_lora_parameters_cpu():
    if not _warm_torch_available():
        return
    import torch
    model = torch.nn.Module()
    model.layer = torch.nn.Linear(4, 4, bias=False)
    model.layer.weight.requires_grad_(False)
    model.layer.lora_A = torch.nn.ModuleDict({"default": torch.nn.Linear(4, 2, bias=False)})
    model.layer.lora_B = torch.nn.ModuleDict({"default": torch.nn.Linear(2, 4, bias=False)})
    model.peft_config = {"default": {}}
    model.active_adapters = ["default"]
    assert len(tv3._warm_trainability(model)) == 2
    model.layer.weight.requires_grad_(True)
    _warm_error(lambda: tv3._warm_trainability(model), "base must be frozen")
    model.layer.weight.requires_grad_(False)
    model.layer.lora_A.default.weight.requires_grad_(False)
    _warm_error(lambda: tv3._warm_trainability(model), "only all LoRA")
    model.layer.lora_A.default.weight.requires_grad_(True)
    model.peft_config["second"] = {}
    _warm_error(lambda: tv3._warm_trainability(model), "one adapter")


def _warm_native_base():
    model = _tiny_model()
    model.config._name_or_path = "tiny-qwen2"
    model.name_or_path = "tiny-qwen2"
    return model


def _warm_native_parent(directory):
    import torch
    torch.set_num_threads(1)
    cfg = tv3.TrainConfig(rank=2, alpha=4, dropout=.05, lr=1e-3, epochs=1, max_len=64,
                          pack=False, batch_size=1, device="cpu", dtype="fp32", model="tiny-qwen2",
                          grad_checkpoint=False, log_every=0)
    items = tv3.normalize_items([dict(spans=[["Question: ", False, "context"], ["answer", True, "target"]], group="one")])
    parent = Path(directory) / "parent"
    manifest = tv3.run_training(items, fx.MockTok(), _warm_native_base(), cfg, parent, log=lambda text: None)
    assert manifest["steps"] == 1 and "warm_start" not in manifest
    assert manifest["config"] == asdict(cfg)
    return parent, cfg, items


def _warm_saved_state(parent):
    import torch
    if (parent / "adapter_model.safetensors").exists():
        from safetensors.torch import load_file
        return load_file(str(parent / "adapter_model.safetensors"), device="cpu")
    return torch.load(str(parent / "adapter_model.bin"), map_location="cpu", weights_only=True)


def test_warm_native_zero_steps_matches_parent_full_loaded_state_and_base_frozen():
    if not _warm_torch_available(native=True):
        return
    import torch
    from peft import get_peft_model_state_dict
    with tempfile.TemporaryDirectory(prefix="tv3-warm-zero-") as directory:
        parent, cfg, items = _warm_native_parent(directory)
        inventory = tv3._warm_inventory(parent)
        expected = _warm_saved_state(parent)
        model = _warm_native_base()
        original_base = [(parameter, parameter.detach().clone()) for parameter in model.parameters()]
        child = Path(directory) / "child"
        initialize = tv3._warm_initialize
        observed = []

        def inspect_loaded(*args):
            initialized, receipt = initialize(*args)
            observed.append(initialized)
            state = get_peft_model_state_dict(initialized, save_embedding_layers=False)
            assert set(state) == set(expected)
            assert all(torch.equal(state[name].cpu(), expected[name].to(state[name].dtype)) for name in state)
            assert receipt["initialized_loaded_state_check"] and len(initialized.peft_config) == 1
            return initialized, receipt

        with patch.object(tv3, "_warm_initialize", side_effect=inspect_loaded):
            result = tv3.run_training(items, fx.MockTok(), model, replace(cfg, epochs=0, lr=1e-5), child,
                                      log=lambda text: None, init_adapter=parent)
        assert len(observed) == 1 and result["steps"] == 0 and result["final_loss"] is None
        assert all(torch.equal(value, _warm_saved_state(child)[name]) for name, value in expected.items())
        assert all(not parameter.requires_grad and torch.equal(parameter, before) for parameter, before in original_base)
        assert tv3._warm_inventory(parent) == inventory
        receipt = result["warm_start"]
        assert receipt["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and receipt["parent_unchanged"]
        assert receipt["parent_files"] == receipt["parent_files_after"] == inventory
        assert receipt["optimizer_initial_state_entries"] == 0 and receipt["optimizer_defaults"]["lr"] == 1e-5
        assert receipt["phase_steps"] == 0 and receipt["cumulative_steps"] == 1
        assert (child / "DONE").exists()
        _warm_error(lambda: tv3.run_training(items, fx.MockTok(), _warm_native_base(), cfg, child, init_adapter=parent), "fresh")


def test_warm_native_finite_update_changed_lr_fresh_optimizer_parent_immutable_and_chain():
    if not _warm_torch_available(native=True):
        return
    import torch
    with tempfile.TemporaryDirectory(prefix="tv3-warm-update-") as directory:
        parent, cfg, items = _warm_native_parent(directory)
        original = tv3._warm_inventory(parent)
        source = _warm_saved_state(parent)
        model = _warm_native_base()
        base_weights = [(parameter, parameter.detach().clone()) for parameter in model.parameters()]
        child = Path(directory) / "child"
        result = tv3.run_training(items, fx.MockTok(), model, replace(cfg, lr=1e-5), child,
                                  log=lambda text: None, init_adapter=parent)
        assert result["steps"] == 1 and result["nonfinite_batches"] == 0 and result["final_loss"] > 0
        assert any(not torch.equal(value, _warm_saved_state(child)[name]) for name, value in source.items())
        assert all(not parameter.requires_grad and torch.equal(parameter, before) for parameter, before in base_weights)
        assert result["warm_start"]["optimizer_initial_state_entries"] == 0
        assert result["warm_start"]["cumulative_steps"] == 2 and tv3._warm_inventory(parent) == original
        grandchild = Path(directory) / "grandchild"
        child_inventory = tv3._warm_inventory(child)
        chained = tv3.run_training(items, fx.MockTok(), _warm_native_base(), replace(cfg, lr=0), grandchild,
                                   log=lambda text: None, init_adapter=child)
        assert chained["warm_start"]["cumulative_steps"] == 3 and chained["warm_start"]["optimizer_initial_state_entries"] == 0
        assert all(torch.equal(value, _warm_saved_state(grandchild)[name]) for name, value in _warm_saved_state(child).items())
        assert tv3._warm_inventory(child) == child_inventory


def test_warm_native_rejects_structural_config_mismatches_and_prewrapped_base():
    if not _warm_torch_available(native=True):
        return
    from peft import get_peft_model
    with tempfile.TemporaryDirectory(prefix="tv3-warm-config-") as directory:
        parent, cfg, items = _warm_native_parent(directory)
        original = tv3._warm_inventory(parent)
        for index, (key, value) in enumerate((("r", 3), ("lora_alpha", 8), ("lora_dropout", 0),
                ("target_modules", ["q_proj"]), ("layers_to_transform", [0]), ("bias", "all"),
                ("use_dora", True), ("use_rslora", True), ("modules_to_save", ["lm_head"]),
                ("rank_pattern", {"q_proj": 4}), ("base_model_name_or_path", "wrong-base"))):
            bad_parent = Path(directory) / f"bad{index}"
            shutil.copytree(parent, bad_parent)
            saved = json.loads((bad_parent / "adapter_config.json").read_text())
            saved[key] = value
            (bad_parent / "adapter_config.json").write_text(json.dumps(saved))
            output = Path(directory) / f"out{index}"
            _warm_error(lambda: tv3.run_training(items, fx.MockTok(), _warm_native_base(), cfg, output,
                                                log=lambda text: None, init_adapter=bad_parent))
            assert not (output / "DONE").exists()
        wrong = _warm_native_base()
        wrong.config._name_or_path = "wrong-loaded-base"
        wrong.name_or_path = "wrong-loaded-base"
        _warm_error(lambda: tv3.run_training(items, fx.MockTok(), wrong, cfg, Path(directory) / "wrong",
                                            init_adapter=parent), "loaded base")
        nested = get_peft_model(_warm_native_base(), tv3.lora_config(cfg, 2))
        _warm_error(lambda: tv3.run_training(items, fx.MockTok(), nested, cfg, Path(directory) / "nested",
                                            init_adapter=parent), "prewrapped")
        assert tv3._warm_inventory(parent) == original


def test_warm_native_rejects_missing_partial_nonfinite_bad_weights_and_empty_write():
    if not _warm_torch_available(native=True):
        return
    import torch
    from safetensors.torch import save_file
    with tempfile.TemporaryDirectory(prefix="tv3-warm-weights-") as directory:
        parent, cfg, items = _warm_native_parent(directory)
        expected = _warm_saved_state(parent)
        first = next(iter(expected))
        variants = ["missing", "partial", "extra", "shape", "nan", "infinity", "integer", "corrupt"]
        for kind in variants:
            bad_parent = Path(directory) / kind
            shutil.copytree(parent, bad_parent)
            for name in ("adapter_model.safetensors", "adapter_model.bin"):
                if (bad_parent / name).exists():
                    (bad_parent / name).unlink()
            state = {name: value.clone() for name, value in expected.items()}
            if kind == "partial":
                del state[first]
            elif kind == "extra":
                state["base_model.model.extra.weight"] = torch.ones(1)
            elif kind == "shape":
                state[first] = torch.zeros(1)
            elif kind in ("nan", "infinity"):
                state[first].fill_(float("nan") if kind == "nan" else float("inf"))
            elif kind == "integer":
                state[first] = state[first].to(torch.int64)
            if kind == "corrupt":
                (bad_parent / "adapter_model.safetensors").write_bytes(b"not safetensors")
            elif kind != "missing":
                save_file(state, str(bad_parent / "adapter_model.safetensors"))
            output = Path(directory) / (kind + "-out")
            _warm_error(lambda: tv3.run_training(items, fx.MockTok(), _warm_native_base(), cfg, output,
                                                log=lambda text: None, init_adapter=bad_parent))
            assert not (output / "DONE").exists()
        output = Path(directory) / "empty"
        _warm_error(lambda: tv3.run_training([], fx.MockTok(), _warm_native_base(), cfg, output,
                                            init_adapter=parent), "empty/no-target")
        assert not (output / "DONE").exists()


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
