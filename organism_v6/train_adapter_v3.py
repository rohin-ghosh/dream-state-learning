"""Sleep trainer v3 — masked, packed, isolated (CHILD_MECHANISM_v7 2.1–2.3,
Astra memo 1 section 2.2). New module; the v1 (train_adapter.py) and v2.1
(train_adapter_v21.py) trainers are untouched.

  python -m organism_v6.train_adapter_v3 --corpus <corpus.json> --out <dir> \
      [--rank 32] [--alpha 64] [--lr 1e-4] [--epochs 3] [--max-len 7168] \
      [--overflow split|truncate] [--manifest-note TEXT] \
      [--seed 0] [--no-pack] [--svd-init [--svd-scale sigma] [--freeze-a]] \
      [--target-modules q_proj,...] [--layers all|last4] [--optimizer adamw|sgd] \
      [--batch-size 1] [--chat-template] [--isolation-check auto|strict|off]

Corpus items (sleep_compile_v3): {"spans": [[text, loss, category], ...],
"group", "view", "category", "order", "meta"}; also accepted: {"context",
"target", "group", "category"}, v2.2 {"q", "a"} and v1 plain strings (whole
text = target). Loss is on target tokens only; context tokens are -100.

Over-long items (--overflow split, the default): an item whose tokens exceed
--max-len is SPLIT at a span boundary into segments that each open with the
item's head (its first context span — the task text) and up to
--split-overlap-tokens of the preceding spans as zero-loss context; every
target token is trained exactly once and the head is never lost (the
compiler sizes B's windows in tokens so this is a backstop; the manifest
counts items_split). --overflow truncate is the old behaviour (leading
context dropped first, then interleaved tokens from the left, logged).

Packing: items are packed BY GROUP (the compiler's neighbourhood key) into
sequences of <= --max-len tokens, each segment with its positions reset to 0
and a block-diagonal causal attention mask, so packed items cannot attend to
each other (no fictitious cross-episode context). The mask is a 4-D additive
float mask (0 / finfo.min) which eager and sdpa attention accept as a custom
mask; before training, an ISOLATION SELF-CHECK forwards two short segments
packed vs separately and compares the logits — if the model/attention path
does not isolate (or refuses the mask), the trainer falls back to ONE ITEM
PER SEQUENCE and says so in the manifest (packing.mode = "fallback_...").
Group blocks are shuffled every epoch; time order is kept inside a group.
The label of the first token of every segment is -100 (HF's shifted loss
would otherwise predict it from the previous segment's last position).

Manifest (<out>/train_manifest.json): recipe, corpus sha256, counts, exact
token masses by category / view, truncation, packing fill, isolation check,
LoRA config, SVD-init stats, optimizer, steps, loss per epoch, tokens/s,
wall-clock, seed, library versions. EMPTY_CORPUS marker when nothing carries
loss (compile-time no-op is logged, not failed).
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass, field, asdict

IGNORE = -100
ALL_PROJ = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
FFN_PROJ = ["gate_proj", "up_proj", "down_proj"]
RECIPE = "v3_masked_packed"


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------
@dataclass
class TrainConfig:
    rank: int = 32
    alpha: int = 0                      # 0 -> 2 * rank
    dropout: float = 0.05
    lr: float = 1e-4
    epochs: int = 3
    max_len: int = 7168                 # P1 / CHILD_MECHANISM_v7 2.2 (6,144 cut full-budget problems)
    seed: int = 0
    overflow: str = "split"             # split | truncate
    split_overlap_tokens: int = 0       # 0 -> min(1024, max_len // 8)
    note: str = ""                      # free text into the manifest (recipe deviations, cell name)
    batch_size: int = 1                 # sequences per optimizer step
    grad_accum: int = 1
    pack: bool = True
    shuffle_groups: bool = True
    optimizer: str = "adamw"            # adamw | sgd (TMEM: plain SGD)
    target_modules: list = field(default_factory=lambda: list(ALL_PROJ))
    layers: str = "all"                 # all | lastN
    svd_init: bool = False
    svd_scale: str = "sigma"
    svd_method: str = "exact"
    svd_cache: str = ""
    freeze_a: bool = False
    chat_template: bool = False
    add_eos: bool = True
    isolation_check: str = "auto"       # auto | strict | off
    isolation_tol: float = 0.0          # 0 -> by dtype
    grad_checkpoint: bool = True
    device: str = "cuda"
    dtype: str = "bf16"
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    max_steps: int = 0
    log_every: int = 10


# ---------------------------------------------------------------------------
# items -> encoded segments (pure python; any tokenizer with .encode)
# ---------------------------------------------------------------------------
@dataclass
class Encoded:
    ids: list
    labels: list
    cats: list
    group: str
    order: int
    view: str
    item_index: int
    n_target: int
    context_dropped: int = 0
    target_dropped: int = 0
    split_index: int = 0
    n_splits: int = 1

    def __len__(self):
        return len(self.ids)


def normalize_items(raw) -> list:
    """Whatever corpus.json holds -> v3 items with spans."""
    corpus = raw["corpus"] if isinstance(raw, dict) else raw
    items = []
    for i, c in enumerate(corpus):
        if isinstance(c, str):
            items.append(dict(spans=[[c, True, "legacy"]], group="legacy", view="legacy",
                              category="legacy", order=i, meta={}))
        elif isinstance(c, dict) and "spans" in c:
            spans = [[str(s[0]), bool(s[1]), (s[2] if len(s) > 2 else None) or c.get("category") or "target"]
                     for s in c["spans"]]
            items.append(dict(spans=spans, group=str(c.get("group") or "ungrouped"),
                              view=str(c.get("view") or "item"),
                              category=str(c.get("category") or "target"),
                              order=int(c.get("order", i)), meta=c.get("meta") or {}))
        elif isinstance(c, dict) and ("target" in c or "a" in c):
            ctx = str(c.get("context", c.get("q", "")) or "")
            tgt = str(c.get("target", c.get("a", "")) or "")
            cat = str(c.get("category") or "target")
            spans = ([[ctx, False, "context"]] if ctx else []) + [[tgt, True, cat]]
            items.append(dict(spans=spans, group=str(c.get("group") or "ungrouped"),
                              view=str(c.get("view") or "item"), category=cat,
                              order=int(c.get("order", i)), meta=c.get("meta") or {}))
    return items


def encode_item(item: dict, tok, max_len: int, chat_template: bool = False,
                add_eos: bool = True, item_index: int = 0):
    """spans -> (ids, labels, cats). Context tokens get label -100. With
    chat_template the leading context spans form the user turn and the rest
    the assistant turn (v2.1's inference-matched format). Over-long items are
    LEFT-truncated: leading context first, then (logged) everything else."""
    spans = item["spans"]
    if not any(s[1] for s in spans):
        return None
    ids, labels, cats = [], [], []
    if chat_template and hasattr(tok, "apply_chat_template"):
        k = 0
        lead = []
        while k < len(spans) and not spans[k][1]:
            lead.append(spans[k][0])
            k += 1
        prompt = tok.apply_chat_template([{"role": "user", "content": "".join(lead).rstrip("\n")}],
                                         tokenize=False, add_generation_prompt=True)
        p_ids = tok.encode(prompt, add_special_tokens=False)
        ids += p_ids
        labels += [IGNORE] * len(p_ids)
        cats += [None] * len(p_ids)
        rest = spans[k:]
    else:
        rest = spans
    last_loss_cat = None
    for text, loss, cat in rest:
        t_ids = tok.encode(text, add_special_tokens=False)
        ids += t_ids
        if loss:
            labels += t_ids
            cats += [cat] * len(t_ids)
            last_loss_cat = cat
        else:
            labels += [IGNORE] * len(t_ids)
            cats += [None] * len(t_ids)
    if add_eos and getattr(tok, "eos_token_id", None) is not None:
        ids.append(tok.eos_token_id)
        labels.append(tok.eos_token_id)
        cats.append(last_loss_cat)
    ctx_dropped = tgt_dropped = 0
    if len(ids) > max_len:
        over = len(ids) - max_len
        # drop leading context tokens first
        lead_ctx = 0
        while lead_ctx < len(labels) and labels[lead_ctx] == IGNORE:
            lead_ctx += 1
        take = min(over, lead_ctx)
        ids, labels, cats = ids[take:], labels[take:], cats[take:]
        ctx_dropped = take
        over -= take
        if over > 0:
            tgt_dropped = sum(1 for x in labels[:over] if x != IGNORE)
            ctx_dropped += over - tgt_dropped
            ids, labels, cats = ids[over:], labels[over:], cats[over:]
    n_target = sum(1 for x in labels if x != IGNORE)
    if n_target == 0:
        return None
    return Encoded(ids=ids, labels=labels, cats=cats, group=item["group"], order=item["order"],
                   view=item["view"], item_index=item_index, n_target=n_target,
                   context_dropped=ctx_dropped, target_dropped=tgt_dropped)


def encode_spans(spans: list, tok, chat_template: bool = False) -> list:
    """spans -> [(ids, loss, cat), ...], one entry per span; with the chat
    template the leading context spans are folded into ONE prompt span (the
    user turn + generation prompt)."""
    out = []
    k = 0
    if chat_template and hasattr(tok, "apply_chat_template"):
        lead = []
        while k < len(spans) and not spans[k][1]:
            lead.append(spans[k][0])
            k += 1
        prompt = tok.apply_chat_template([{"role": "user", "content": "".join(lead).rstrip("\n")}],
                                         tokenize=False, add_generation_prompt=True)
        out.append((tok.encode(prompt, add_special_tokens=False), False, None))
    for text, loss, cat in spans[k:]:
        out.append((tok.encode(text, add_special_tokens=False), bool(loss), cat if loss else None))
    return out


def encode_item_segments(item: dict, tok, max_len: int, chat_template: bool = False,
                         add_eos: bool = True, item_index: int = 0, overflow: str = "split",
                         overlap_tokens: int = 0) -> list:
    """One item -> a list of Encoded segments, each <= max_len. overflow=
    'truncate' delegates to encode_item (one segment, old semantics).
    'split': the item's HEAD (its first span when that is context) opens
    every segment; spans are appended in order while they fit; when the next
    span does not fit, the segment closes and a new one opens with the head
    plus up to overlap_tokens of the already-emitted spans as zero-loss
    context. A single span larger than the room left in a fresh segment is
    cut from the left (its tail kept) and the loss is logged. Segments with
    no target are dropped (their context tokens counted as dropped)."""
    spans = item["spans"]
    if not any(s[1] for s in spans):
        return []
    if overflow == "truncate":
        e = encode_item(item, tok, max_len, chat_template, add_eos, item_index)
        return [e] if e is not None else []
    enc = encode_spans(spans, tok, chat_template)
    eos = [tok.eos_token_id] if add_eos and getattr(tok, "eos_token_id", None) is not None else []
    cap = max_len - len(eos)
    head = enc[0] if (enc and not enc[0][1]) else None
    body = enc[1:] if head is not None else enc
    head_n = len(head[0]) if head is not None else 0
    if overlap_tokens <= 0:
        overlap_tokens = max(0, min(1024, max_len // 8))
    segments, cur, cur_n = [], ([head] if head is not None else []), head_n
    fresh = []            # body spans placed in the current segment (not head, not overlap)
    emitted = []          # spans already placed (for the overlap of the next segment)
    ctx_dropped = tgt_dropped = 0
    for ids, loss, cat in body:
        n = len(ids)
        if cur_n + n > cap and any(s[1] for s in cur):
            segments.append(cur)
            cur, cur_n, fresh = ([head] if head is not None else []), head_n, []
            room = cap - cur_n - n
            ov, used = [], 0
            for sp in reversed(emitted):
                if used + len(sp[0]) > min(overlap_tokens, max(0, room)):
                    break
                ov.insert(0, (sp[0], False, None))
                used += len(sp[0])
            cur += ov
            cur_n += used
        if cur_n + n > cap:                       # still too big: one span larger than the room
            room = max(0, cap - cur_n)
            cut = n - room
            if loss:
                tgt_dropped += cut
            else:
                ctx_dropped += cut
            ids = ids[cut:]
            n = len(ids)
            if n == 0:
                emitted.append((ids, loss, cat))
                continue
        cur.append((ids, loss, cat))
        fresh.append((ids, loss, cat))
        cur_n += n
        emitted.append((ids, loss, cat))
    if cur and any(s[1] for s in cur):
        segments.append(cur)
    elif fresh:                                   # trailing context that no target follows
        ctx_dropped += sum(len(s[0]) for s in fresh)
    out = []
    for si, seg in enumerate(segments):
        ids, labels, cats = [], [], []
        last_cat = None
        for t_ids, loss, cat in seg:
            ids += t_ids
            if loss:
                labels += t_ids
                cats += [cat] * len(t_ids)
                last_cat = cat
            else:
                labels += [IGNORE] * len(t_ids)
                cats += [None] * len(t_ids)
        if eos:
            ids += eos
            labels += eos
            cats.append(last_cat)
        n_target = sum(1 for x in labels if x != IGNORE)
        out.append(Encoded(ids=ids, labels=labels, cats=cats, group=item["group"], order=item["order"],
                           view=item["view"], item_index=item_index, n_target=n_target,
                           context_dropped=ctx_dropped if si == 0 else 0,
                           target_dropped=tgt_dropped if si == 0 else 0,
                           split_index=si, n_splits=len(segments)))
    return out


# ---------------------------------------------------------------------------
# packing (pure python)
# ---------------------------------------------------------------------------
def pack_by_group(encoded: list, max_len: int, pack: bool = True) -> list:
    """Greedy sequential packing WITHIN a group (never across groups): items
    sorted by (group first appearance, order); a pack closes when the next
    segment would exceed max_len. Returns a list of packs (lists of Encoded);
    each pack carries .group via the first segment."""
    if not pack:
        return [[e] for e in sorted(encoded, key=lambda e: (e.group, e.order, e.item_index))]
    first_seen = {}
    for e in encoded:
        first_seen.setdefault(e.group, e.order)
    ordered = sorted(encoded, key=lambda e: (first_seen[e.group], e.group, e.order, e.item_index))
    packs, cur, cur_len, cur_group = [], [], 0, None
    for e in ordered:
        if cur and (e.group != cur_group or cur_len + len(e) > max_len):
            packs.append(cur)
            cur, cur_len = [], 0
        cur.append(e)
        cur_len += len(e)
        cur_group = e.group
    if cur:
        packs.append(cur)
    return packs


def epoch_order(packs: list, seed: int, epoch: int, shuffle_groups: bool = True) -> list:
    """Shuffle GROUP BLOCKS (consecutive packs of one group), keep the time
    order inside a block. Deterministic in (seed, epoch)."""
    if not shuffle_groups or not packs:
        return list(packs)
    blocks, cur = [], [packs[0]]
    for p in packs[1:]:
        if p[0].group == cur[-1][0].group:
            cur.append(p)
        else:
            blocks.append(cur)
            cur = [p]
    blocks.append(cur)
    rng = random.Random(seed * 1000 + epoch)
    rng.shuffle(blocks)
    return [p for b in blocks for p in b]


def collate(packs: list, pad_id: int) -> dict:
    """Lists (B x L): input_ids, labels, position_ids (reset per segment),
    segment_ids (-1 = pad). The first token of each segment is never a label."""
    L = max(sum(len(e) for e in p) for p in packs)
    out = dict(input_ids=[], labels=[], position_ids=[], segment_ids=[], n_target=0,
               n_tokens=0)
    for p in packs:
        ids, lab, pos, seg = [], [], [], []
        for si, e in enumerate(p):
            ids += e.ids
            lab += [IGNORE] + e.labels[1:]
            pos += list(range(len(e)))
            seg += [si] * len(e)
        k = L - len(ids)
        out["n_tokens"] += len(ids)
        out["n_target"] += sum(1 for x in lab if x != IGNORE)
        out["input_ids"].append(ids + [pad_id] * k)
        out["labels"].append(lab + [IGNORE] * k)
        out["position_ids"].append(pos + [0] * k)
        out["segment_ids"].append(seg + [-1] * k)
    return out


def block_causal_allowed(segment_ids: list) -> list:
    """Pure-python reference of the mask: allowed[i][j] = same segment, j <= i,
    not pad (pads attend to themselves only)."""
    L = len(segment_ids)
    return [[(segment_ids[i] >= 0 and segment_ids[i] == segment_ids[j] and j <= i) or i == j
             for j in range(L)] for i in range(L)]


# ---------------------------------------------------------------------------
# torch side
# ---------------------------------------------------------------------------
def _torch_dtype(name: str):
    import torch
    return dict(bf16=torch.bfloat16, fp16=torch.float16, fp32=torch.float32)[name]


def block_mask_tensor(seg, dtype):
    import torch
    B, L = seg.shape
    i = torch.arange(L, device=seg.device)
    causal = i[None, :] <= i[:, None]
    same = seg[:, :, None] == seg[:, None, :]
    valid = (seg >= 0)[:, :, None]
    allowed = (same & causal[None] & valid) | torch.eye(L, dtype=torch.bool, device=seg.device)[None]
    zero = torch.zeros((), dtype=dtype, device=seg.device)
    minv = torch.full((), torch.finfo(dtype).min, dtype=dtype, device=seg.device)
    return torch.where(allowed, zero, minv)[:, None, :, :]


def to_tensors(batch: dict, device, dtype, mask_mode: str) -> dict:
    import torch
    ids = torch.tensor(batch["input_ids"], dtype=torch.long, device=device)
    labels = torch.tensor(batch["labels"], dtype=torch.long, device=device)
    seg = torch.tensor(batch["segment_ids"], dtype=torch.long, device=device)
    out = dict(input_ids=ids, labels=labels)
    if mask_mode == "block4d":
        out["position_ids"] = torch.tensor(batch["position_ids"], dtype=torch.long, device=device)
        out["attention_mask"] = block_mask_tensor(seg, dtype)
    else:
        out["attention_mask"] = (seg >= 0).long()
    return out


def isolation_check(model, segs: list, pad_id: int, device, dtype, tol: float,
                    max_tokens: int = 48) -> dict:
    """Two short segments: logits packed (block mask + reset positions) must
    equal the logits of each segment alone (<= tol); packed WITHOUT the block
    mask must differ (negative control), else the check is inconclusive."""
    import torch
    res = dict(ran=True, ok=None, tol=tol)
    try:
        a, b = segs[0], segs[1]
        cut = lambda e: Encoded(ids=e.ids[:max_tokens], labels=e.labels[:max_tokens],  # noqa: E731
                                cats=e.cats[:max_tokens], group=e.group, order=e.order,
                                view=e.view, item_index=e.item_index, n_target=1)
        a, b = cut(a), cut(b)
        model.eval()
        with torch.no_grad():
            def solo(e):
                t = to_tensors(collate([[e]], pad_id), device, dtype, "2d")
                t.pop("labels")
                return model(**t).logits[0].float()
            la, lb = solo(a), solo(b)
            packed = collate([[a, b]], pad_id)
            t = to_tensors(packed, device, dtype, "block4d")
            t.pop("labels")
            lp = model(**t).logits[0].float()
            da = float((lp[:len(a)] - la).abs().max())
            db = float((lp[len(a):len(a) + len(b)] - lb).abs().max())
            t2 = to_tensors(packed, device, dtype, "2d")     # no block, continuous positions
            t2.pop("labels")
            lq = model(**t2).logits[0].float()
            dneg = float((lq[len(a):len(a) + len(b)] - lb).abs().max())
        res.update(diff_first=round(da, 5), diff_second=round(db, 5), diff_negative_control=round(dneg, 5))
        res["ok"] = (da <= tol and db <= tol)
        res["informative"] = dneg > 2 * tol
        if res["ok"] and not res["informative"]:
            res["verdict"] = "inconclusive"
        else:
            res["verdict"] = "isolated" if res["ok"] else "NOT_ISOLATED"
    except Exception as e:  # noqa: BLE001 — a refused 4-D mask is a result, not a crash
        res.update(ok=False, verdict="mask_refused", error=f"{type(e).__name__}: {str(e)[:300]}")
    finally:
        model.train()
    return res


def lora_config(cfg: TrainConfig, n_layers: int):
    from peft import LoraConfig
    kw = dict(r=cfg.rank, lora_alpha=cfg.alpha or 2 * cfg.rank, lora_dropout=cfg.dropout,
              bias="none", target_modules=list(cfg.target_modules))
    if cfg.layers != "all":
        if not cfg.layers.startswith("last"):
            raise ValueError("--layers must be all or lastN")
        k = int(cfg.layers[4:])
        kw["layers_to_transform"] = list(range(max(0, n_layers - k), n_layers))
    return LoraConfig(**kw)


def _versions() -> dict:
    out = {}
    for m in ("torch", "transformers", "peft"):
        try:
            out[m] = __import__(m).__version__
        except Exception:  # noqa: BLE001
            out[m] = None
    return out


def run_training(items: list, tok, base_model, cfg: TrainConfig, out_dir: str,
                 corpus_sha=None, corpus_name=None, log=print) -> dict:
    """The whole write on an already-loaded base model and tokenizer (the CLI
    loads them; tests pass a tiny model). Returns the manifest."""
    import torch
    from peft import get_peft_model
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    device = torch.device(cfg.device)
    dtype = _torch_dtype(cfg.dtype)
    pad_id = tok.pad_token_id if getattr(tok, "pad_token_id", None) is not None else tok.eos_token_id

    encoded, skipped = [], 0
    items_split = 0
    for i, it in enumerate(items):
        segs = encode_item_segments(it, tok, cfg.max_len, cfg.chat_template, cfg.add_eos, i,
                                    overflow=cfg.overflow, overlap_tokens=cfg.split_overlap_tokens)
        if not segs:
            skipped += 1
        else:
            encoded += segs
            items_split += int(segs[0].n_splits > 1)
    by_cat, by_view = collections.Counter(), collections.Counter()
    ctx_tokens = 0
    for e in encoded:
        for lab, cat in zip(e.labels, e.cats):
            if lab != IGNORE:
                by_cat[cat] += 1
                by_view[e.view] += 1
            else:
                ctx_tokens += 1
    n_target = sum(by_cat.values())
    manifest = dict(recipe=RECIPE, created=time.strftime("%Y-%m-%d %H:%M:%S"),
                    corpus=dict(file=corpus_name, sha256=corpus_sha, n_items=len(items),
                                n_encoded=len(encoded), n_skipped_no_target=skipped),
                    tokens=dict(target=n_target, context=ctx_tokens, total=n_target + ctx_tokens,
                                target_by_category=dict(by_cat), target_by_view=dict(by_view)),
                    truncation=dict(overflow=cfg.overflow,
                                    items_truncated=sum(1 for e in encoded if e.context_dropped or e.target_dropped),
                                    context_tokens_dropped=sum(e.context_dropped for e in encoded),
                                    target_tokens_dropped=sum(e.target_dropped for e in encoded),
                                    items_split=items_split,
                                    segments_from_splits=sum(1 for e in encoded if e.n_splits > 1),
                                    max_segment_tokens=max((len(e) for e in encoded), default=0)),
                    config=asdict(cfg), base_model=cfg.model, versions=_versions(),
                    note=cfg.note or None)
    if n_target == 0:
        with open(os.path.join(out_dir, "EMPTY_CORPUS"), "w") as f:
            f.write("no data\n")
        manifest.update(empty=True, steps=0)
        with open(os.path.join(out_dir, "train_manifest.json"), "w") as f:
            json.dump(manifest, f, indent=1, default=str)
        log("EMPTY_CORPUS — no adapter trained")
        return manifest

    n_layers = int(getattr(base_model.config, "num_hidden_layers", 0) or 0)
    model = get_peft_model(base_model, lora_config(cfg, n_layers))
    if cfg.svd_init:
        from .lora_svd_init import apply_svd_init
        manifest["svd_init"] = apply_svd_init(model, cfg.rank, cfg.svd_scale, cfg.freeze_a,
                                              method=cfg.svd_method,
                                              cache_dir=cfg.svd_cache or None, log=log)
        manifest["svd_init"]["matrices"] = {k: v for k, v in
                                            list(manifest["svd_init"]["matrices"].items())[:16]}
    elif cfg.freeze_a:
        for n_, p in model.named_parameters():
            if "lora_A" in n_:
                p.requires_grad_(False)
    model.to(device)
    manifest["lora"] = dict(rank=cfg.rank, alpha=cfg.alpha or 2 * cfg.rank, dropout=cfg.dropout,
                            scaling=round((cfg.alpha or 2 * cfg.rank) / cfg.rank, 4),
                            target_modules=list(cfg.target_modules), layers=cfg.layers,
                            n_layers=n_layers, freeze_a=cfg.freeze_a,
                            trainable_params=int(sum(p.numel() for p in model.parameters() if p.requires_grad)))

    # --- packing decision and the isolation self-check --------------------
    mask_mode, pack = ("block4d", True) if cfg.pack else ("2d", False)
    iso = dict(ran=False)
    if pack and cfg.isolation_check != "off":
        if len(encoded) >= 2:
            tol = cfg.isolation_tol or (1e-3 if cfg.dtype == "fp32" else 0.25)
            iso = isolation_check(model, encoded[:2], pad_id, device, dtype, tol)
            if not iso.get("ok") or (cfg.isolation_check == "strict" and iso.get("verdict") == "inconclusive"):
                mask_mode, pack = "2d", False
                log(f"[train-v3] packing DISABLED: isolation check {iso.get('verdict')} — "
                    f"falling back to one item per sequence")
        else:
            iso = dict(ran=False, reason="fewer than two segments")
    if cfg.grad_checkpoint and device.type == "cuda":
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    model.config.use_cache = False
    model.train()

    packs = pack_by_group(encoded, cfg.max_len, pack)
    fill = statistics.mean(sum(len(e) for e in p) / cfg.max_len for p in packs) if packs else 0.0
    manifest["packing"] = dict(mode=("block4d_by_group" if pack else
                                     ("one_item_per_sequence" if not cfg.pack else
                                      f"fallback_one_item_per_sequence ({iso.get('verdict')})")),
                               n_sequences=len(packs), mean_fill=round(fill, 4),
                               n_groups=len({p[0].group for p in packs}),
                               mean_segments_per_sequence=round(statistics.mean(len(p) for p in packs), 3)
                               if packs else 0.0, isolation_check=iso)

    params = [p for p in model.parameters() if p.requires_grad]
    if cfg.optimizer == "sgd":
        opt = torch.optim.SGD(params, lr=cfg.lr)
    elif cfg.optimizer == "adamw":
        opt = torch.optim.AdamW(params, lr=cfg.lr)
    else:
        raise ValueError("--optimizer adamw|sgd")

    steps = micro = 0
    tokens_seen = 0
    losses_by_epoch = []
    loss_val = None
    nonfinite = 0
    t_train = time.time()
    stop = False
    for ep in range(cfg.epochs):
        order = epoch_order(packs, cfg.seed, ep, cfg.shuffle_groups)
        ep_losses = []
        for bi in range(0, len(order), cfg.batch_size):
            batch = collate(order[bi:bi + cfg.batch_size], pad_id)
            t = to_tensors(batch, device, dtype, mask_mode)
            out = model(**t)
            loss = out.loss
            if not torch.isfinite(loss):
                nonfinite += 1
                opt.zero_grad(set_to_none=True)
                continue
            (loss / cfg.grad_accum).backward()
            micro += 1
            tokens_seen += batch["n_tokens"]
            ep_losses.append(loss.detach().item())
            if micro % cfg.grad_accum == 0:
                opt.step()
                opt.zero_grad(set_to_none=True)
                steps += 1
                loss_val = loss.detach().item()
                if cfg.log_every and steps % cfg.log_every == 0:
                    el = time.time() - t_train
                    log(f"[train-v3] epoch {ep + 1}/{cfg.epochs} step {steps} loss {loss_val:.4f} "
                        f"tokens {tokens_seen} ({tokens_seen / max(el, 1e-9):.0f} tok/s)")
                if cfg.max_steps and steps >= cfg.max_steps:
                    stop = True
                    break
        losses_by_epoch.append(round(statistics.mean(ep_losses), 5) if ep_losses else None)
        if stop:
            break
    el = time.time() - t_train
    model.save_pretrained(out_dir)
    manifest.update(steps=steps, micro_batches=micro, nonfinite_batches=nonfinite,
                    epochs_run=len(losses_by_epoch), mean_loss_per_epoch=losses_by_epoch,
                    final_loss=loss_val, train_tokens_seen=tokens_seen,
                    tokens_per_s=round(tokens_seen / max(el, 1e-9), 1),
                    train_seconds=round(el, 1), wall_seconds=round(time.time() - t0, 1),
                    empty=False)
    with open(os.path.join(out_dir, "train_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, default=str)
    with open(os.path.join(out_dir, "train_meta.json"), "w") as f:      # the v1/v2.1 shape too
        json.dump(dict(recipe=RECIPE, n_texts=len(items), steps=steps, tokens=tokens_seen,
                       rank=cfg.rank, epochs=cfg.epochs, lr=cfg.lr, seed=cfg.seed,
                       final_loss=loss_val), f, indent=1)
    with open(os.path.join(out_dir, "DONE"), "w") as f:
        f.write("ok\n")
    log(f"TRAIN_DONE recipe={RECIPE} items={len(items)} seqs={len(packs)} steps={steps} "
        f"target_tokens={n_target} tokens={tokens_seen} tok/s={manifest['tokens_per_s']} "
        f"loss={loss_val if loss_val is None else round(loss_val, 4)} packing={manifest['packing']['mode']}")
    return manifest


def _sha256(path: str):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def build_parser():
    ap = argparse.ArgumentParser(description="sleep trainer v3 (masked, packed, isolated)")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--alpha", type=int, default=0, help="default 2 x rank")
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-len", type=int, default=7168, help="P1: 7,168 (6,144 cut full-budget problems)")
    ap.add_argument("--overflow", default="split", choices=["split", "truncate"],
                    help="over-long item: split at a span boundary keeping the head (default) | left-truncate")
    ap.add_argument("--split-overlap-tokens", type=int, default=0, help="0 -> min(1024, max_len // 8)")
    ap.add_argument("--manifest-note", default="", help="free text recorded in train_manifest.json")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--no-pack", action="store_true")
    ap.add_argument("--no-shuffle-groups", action="store_true")
    ap.add_argument("--optimizer", default="adamw", choices=["adamw", "sgd"])
    ap.add_argument("--target-modules", default=",".join(ALL_PROJ))
    ap.add_argument("--layers", default="all", help="all | lastN (TMEM: last4)")
    ap.add_argument("--svd-init", action="store_true")
    ap.add_argument("--svd-scale", default="sigma", choices=["sigma", "unit"])
    ap.add_argument("--svd-method", default="exact", choices=["exact", "lowrank"])
    ap.add_argument("--svd-cache", default="")
    ap.add_argument("--freeze-a", action="store_true")
    ap.add_argument("--chat-template", action="store_true")
    ap.add_argument("--no-eos", action="store_true")
    ap.add_argument("--isolation-check", default="auto", choices=["auto", "strict", "off"])
    ap.add_argument("--isolation-tol", type=float, default=0.0)
    ap.add_argument("--no-grad-checkpoint", action="store_true")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "fp32"])
    ap.add_argument("--model", default=os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct"))
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--log-every", type=int, default=10)
    return ap


def config_from_args(args) -> TrainConfig:
    return TrainConfig(rank=args.rank, alpha=args.alpha, dropout=args.dropout, lr=args.lr,
                       epochs=args.epochs, max_len=args.max_len, seed=args.seed,
                       overflow=args.overflow, split_overlap_tokens=args.split_overlap_tokens,
                       note=args.manifest_note,
                       batch_size=args.batch_size, grad_accum=args.grad_accum,
                       pack=not args.no_pack, shuffle_groups=not args.no_shuffle_groups,
                       optimizer=args.optimizer,
                       target_modules=[x.strip() for x in args.target_modules.split(",") if x.strip()],
                       layers=args.layers, svd_init=args.svd_init, svd_scale=args.svd_scale,
                       svd_method=args.svd_method, svd_cache=args.svd_cache, freeze_a=args.freeze_a,
                       chat_template=args.chat_template, add_eos=not args.no_eos,
                       isolation_check=args.isolation_check, isolation_tol=args.isolation_tol,
                       grad_checkpoint=not args.no_grad_checkpoint, device=args.device,
                       dtype=args.dtype, model=args.model, max_steps=args.max_steps,
                       log_every=args.log_every)


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = config_from_args(args)
    corpus_path = os.path.expanduser(args.corpus)
    raw = json.load(open(corpus_path))
    items = normalize_items(raw)
    out = os.path.expanduser(args.out)
    if not items:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "EMPTY_CORPUS"), "w") as f:
            f.write("no data\n")
        print("EMPTY_CORPUS — no adapter trained")
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        cfg.model, torch_dtype=_torch_dtype(cfg.dtype),
        device_map=cfg.device if cfg.device != "cpu" else None)
    run_training(items, tok, base, cfg, out, corpus_sha=_sha256(corpus_path),
                 corpus_name=os.path.basename(corpus_path))


if __name__ == "__main__":
    main()
