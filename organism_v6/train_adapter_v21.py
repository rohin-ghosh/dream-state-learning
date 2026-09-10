"""Sleep training v2.1: cumulative LoRA from CLEAN BASE on the compiled
corpus — now absorption-safe:
  - trains THROUGH the chat template (matching how inference reads), with
    loss masked to the response tokens only (no more bare-text gradients
    dragging the agent out of its own dialect);
  - cool heat by default (lr 3e-5, 2 epochs) — deposit a layer, don't
    recast the model;
  - rank 8 default (dumber adapter, easier to teach — Rohin's ruling);
  - corpus items may be dicts {"q":..., "a":...} or plain strings (legacy
    strings become {"q": generic recall prompt, "a": text}).

  python -m organism_v6.train_adapter --corpus <corpus.json> --out <dir> \
      [--rank 8] [--epochs 2] [--lr 3e-5]
"""
from __future__ import annotations
import argparse
import json
import os

GENERIC_Q = ("Recall something you learned from your own experience that "
             "is worth remembering, with its scope.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--seed", type=int, default=0,
                    help="training seed. Added 2026-09-07: two default-seed "
                         "replicates of r16@1.2k rows differed by 0.059 on "
                         "the probe, so replicate variance must be measured "
                         "with explicit seeds.")
    args = ap.parse_args()
    import random
    import torch as _torch
    random.seed(args.seed)
    _torch.manual_seed(args.seed)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model

    model_name = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    raw = json.load(open(args.corpus))["corpus"]
    if not raw:
        os.makedirs(args.out, exist_ok=True)
        open(os.path.join(args.out, "EMPTY_CORPUS"), "w").write("no data\n")
        print("EMPTY_CORPUS — no adapter trained")
        return
    items = [x if isinstance(x, dict) else {"q": GENERIC_Q, "a": str(x)}
             for x in raw]

    tok = AutoTokenizer.from_pretrained(model_name)
    tok.pad_token = tok.pad_token or tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank,
                     lora_dropout=0.05, bias="none",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                     "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(base, cfg)
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()   # required for PEFT + checkpointing
    model.config.use_cache = False
    model.train()
    opt = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=args.lr)

    MAXLEN = 2048

    def encode(item):
        """Chat-templated; labels only on the assistant response. The
        prompt is LEFT-truncated so answer tokens are always present
        (all-masked rows produce NaN loss — measured failure)."""
        prompt = tok.apply_chat_template(
            [{"role": "user", "content": item["q"]}],
            tokenize=False, add_generation_prompt=True)
        p_ids = tok(prompt, add_special_tokens=False).input_ids
        a_ids = tok(item["a"] + tok.eos_token,
                    add_special_tokens=False).input_ids[:MAXLEN // 2]
        if not a_ids:
            return None
        room = MAXLEN - len(a_ids)
        if len(p_ids) > room:
            p_ids = p_ids[-room:]   # keep the END of the context render
        ids = p_ids + a_ids
        labels = [-100] * len(p_ids) + a_ids
        return ids, labels

    encoded = [e for e in (encode(it) for it in items) if e is not None]
    if not encoded:
        os.makedirs(args.out, exist_ok=True)
        open(os.path.join(args.out, "EMPTY_CORPUS"), "w").write("no data\n")
        print("EMPTY_CORPUS after encoding — no adapter trained")
        return
    bsz, steps, total_tokens = 1, 0, 0
    loss = None
    for _ in range(args.epochs):
        for i in range(0, len(encoded), bsz):
            chunk = encoded[i:i + bsz]
            maxlen = max(len(ids) for ids, _ in chunk)
            input_ids, labels, attn = [], [], []
            pad = tok.pad_token_id
            for ids, lbl in chunk:
                k = maxlen - len(ids)
                input_ids.append(ids + [pad] * k)
                labels.append(lbl + [-100] * k)
                attn.append([1] * len(ids) + [0] * k)
            batch = {k: torch.tensor(v, device="cuda") for k, v in
                     [("input_ids", input_ids), ("labels", labels),
                      ("attention_mask", attn)]}
            loss = model(**batch).loss
            if not torch.isfinite(loss):
                print(f"NONFINITE_LOSS step={steps} — skipping batch")
                opt.zero_grad()
                continue
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            total_tokens += sum(sum(a) for a in attn)
    model.save_pretrained(args.out)
    with open(os.path.join(args.out, "train_meta.json"), "w") as f:
        json.dump(dict(recipe="v2.1_chat_masked", n_texts=len(items),
                       steps=steps, tokens=total_tokens, rank=args.rank,
                       epochs=args.epochs, lr=args.lr,
                       final_loss=float(loss)), f, indent=1)
    open(os.path.join(args.out, "DONE"), "w").write("ok\n")
    print(f"TRAIN_DONE recipe=v2.1 texts={len(items)} steps={steps} "
          f"tokens={total_tokens} loss={float(loss):.4f}")


if __name__ == "__main__":
    main()
