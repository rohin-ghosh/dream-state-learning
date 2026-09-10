"""Absorption + retention instrument (certification bar items 1 and 2).

Offline, over a life's saved sleeps — never touches running processes.
For each committed adapter at sleep k and each sleep j <= k, compute the mean
per-token NLL of sleep j's compiled rows (response tokens only, chat-masked
exactly as trained) under adapter k, and under the clean base.

  absorption(k)  = base_NLL(rows_k)  - adapter_k_NLL(rows_k)     (diagonal)
  retention(k,j) = base_NLL(rows_j)  - adapter_k_NLL(rows_j), j<k (off-diag)
Positive = the adapter made those rows more likely than base. Retention
decay = how absorption of early rows fades under later adapters.
Also reports a HELD-OUT control: NLL on rows from a DIFFERENT life (should
NOT improve — if it does, the adapter learned format, not content).

  CUDA_VISIBLE_DEVICES=g python -m organism_v6.absorption_probe \
      --life ~/v6_out/R2_B_seed0 --control-life ~/v6_out/R_A_seed0 \
      --out ~/v6_out/R2_B_seed0/absorption.json [--rows-per-sleep 24]
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import random


def committed_sleeps(life: str) -> list[tuple[int, str, str]]:
    out = []
    for d in sorted(glob.glob(os.path.join(life, "sleep_*"))):
        ad = os.path.join(d, "adapter")
        cp = os.path.join(d, "corpus.json")
        if os.path.exists(os.path.join(ad, "DONE")) and os.path.exists(cp):
            out.append((int(os.path.basename(d).split("_")[1]), ad, cp))
    return out


def rows_of(cp: str, k: int, seed: int) -> list[dict]:
    raw = json.load(open(cp))["corpus"]
    items = [x if isinstance(x, dict) else
             {"q": "Recall a lesson from your experience, with scope.",
              "a": str(x)} for x in raw]
    rng = random.Random(seed)
    return rng.sample(items, min(k, len(items)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--life", required=True)
    ap.add_argument("--control-life", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rows-per-sleep", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    life = os.path.expanduser(args.life)
    sleeps = committed_sleeps(life)
    print(f"[absorb] committed sleeps: {[s for s, _, _ in sleeps]}")
    if args.dry_run or not sleeps:
        print("DRY_RUN_OK" if args.dry_run else "NO_SLEEPS")
        return

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    model_name = os.environ.get("V6_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    tok = AutoTokenizer.from_pretrained(model_name)
    tok.pad_token = tok.pad_token or tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda").eval()

    def encode(item, maxlen=2048):
        prompt = tok.apply_chat_template([{"role": "user", "content": item["q"]}],
                                         tokenize=False, add_generation_prompt=True)
        p = tok(prompt, add_special_tokens=False).input_ids
        a = tok(item["a"] + tok.eos_token, add_special_tokens=False).input_ids
        a = a[:maxlen // 2]
        room = maxlen - len(a)
        if len(p) > room:
            p = p[-room:]
        return p, a

    @torch.no_grad()
    def mean_nll(m, items) -> float:
        tot, n = 0.0, 0
        for it in items:
            p, a = encode(it)
            if not a:
                continue
            ids = torch.tensor([p + a], device="cuda")
            labels = torch.tensor([[-100] * len(p) + a], device="cuda")
            loss = m(input_ids=ids, labels=labels).loss
            tot += float(loss) * len(a)
            n += len(a)
        return tot / max(1, n)

    row_sets = {s: rows_of(cp, args.rows_per_sleep, 1000 + s)
                for s, _, cp in sleeps}
    control = None
    if args.control_life:
        cl = os.path.expanduser(args.control_life)
        cs = committed_sleeps(cl)
        if cs:
            control = rows_of(cs[-1][2], args.rows_per_sleep, 4242)
    base_nll = {s: mean_nll(base, r) for s, r in row_sets.items()}
    base_ctrl = mean_nll(base, control) if control else None

    result = dict(life=life, sleeps=[s for s, _, _ in sleeps],
                  base_nll=base_nll, base_control_nll=base_ctrl, adapters={})
    for s_k, ad, _ in sleeps:
        pm = PeftModel.from_pretrained(base, ad).eval()
        entry = dict(absorption=None, retention={}, control_delta=None)
        for s_j, rows in row_sets.items():
            if s_j > s_k:
                continue
            nll = mean_nll(pm, rows)
            delta = base_nll[s_j] - nll
            if s_j == s_k:
                entry["absorption"] = delta
            else:
                entry["retention"][str(s_j)] = delta
        if control:
            entry["control_delta"] = base_ctrl - mean_nll(pm, control)
        result["adapters"][str(s_k)] = entry
        print(f"[absorb] adapter@{s_k}: absorption={entry['absorption']:+.3f} "
              f"retention={{{', '.join(f'{j}:{v:+.3f}' for j, v in entry['retention'].items())}}} "
              f"control={entry['control_delta'] if entry['control_delta'] is None else round(entry['control_delta'], 3)}",
              flush=True)
        pm.unload()
        del pm
        torch.cuda.empty_cache()
    tmp = os.path.expanduser(args.out) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(result, f, indent=1)
    os.replace(tmp, os.path.expanduser(args.out))
    print("ABSORPTION_DONE")


if __name__ == "__main__":
    main()
