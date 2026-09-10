"""Sleep training: cumulative LoRA from CLEAN BASE on the compiled corpus.
V1 RECIPE — FROZEN: this is the trainer the v6.1 long-run lives launched
with; it must not change while they run (see train_adapter_v21 for the
nursery recipe). Bare-text LM loss, lr 1e-4, 3 epochs.

  python -m organism_v6.train_adapter --corpus <corpus.json> --out <dir> \
      [--rank 16] [--epochs 3] [--lr 1e-4]
"""
from __future__ import annotations
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model

    model_name = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    corpus = json.load(open(args.corpus))["corpus"]
    corpus = [c if isinstance(c, str) else c.get("a", "") for c in corpus]
    if not corpus:
        os.makedirs(args.out, exist_ok=True)
        open(os.path.join(args.out, "EMPTY_CORPUS"), "w").write("no data\n")
        print("EMPTY_CORPUS — no adapter trained")
        return

    tok = AutoTokenizer.from_pretrained(model_name)
    tok.pad_token = tok.pad_token or tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank,
                     lora_dropout=0.05, bias="none",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                     "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(base, cfg)
    model.train()
    opt = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=args.lr)

    bsz, total_tokens, steps = 4, 0, 0
    for _ in range(args.epochs):
        for i in range(0, len(corpus), bsz):
            batch = tok(corpus[i:i + bsz], return_tensors="pt", padding=True,
                        truncation=True, max_length=512).to("cuda")
            labels = batch.input_ids.clone()
            labels[batch.attention_mask == 0] = -100
            loss = model(**batch, labels=labels).loss
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            total_tokens += int(batch.attention_mask.sum())
    model.save_pretrained(args.out)
    with open(os.path.join(args.out, "train_meta.json"), "w") as f:
        json.dump(dict(recipe="v1_frozen", n_texts=len(corpus), steps=steps,
                       tokens=total_tokens, rank=args.rank,
                       epochs=args.epochs, lr=args.lr,
                       final_loss=float(loss)), f, indent=1)
    open(os.path.join(args.out, "DONE"), "w").write("ok\n")
    print(f"TRAIN_DONE recipe=v1 texts={len(corpus)} steps={steps} "
          f"tokens={total_tokens} loss={float(loss):.4f}")


if __name__ == "__main__":
    main()
