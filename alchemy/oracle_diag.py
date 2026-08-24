"""Oracle-class diagnostic: can the reasoner COMPOSE when handed the
latent structure directly? For held-out pairs, the prompt supplies the
two ingredients' (nonce-coded) class labels, their grades, and the
relevant class-pair rule. Zero memory involved.
- If accuracy is high: the wall is CLASS INDUCTION (tractable, learnable).
- If accuracy stays low: the reasoner can't apply the rule even when
  given it — world too hard for this model, redesign the ask.
Variants: full (classes+rule+grades) | classes_only (no rule line).
  PYTHONPATH=. python alchemy/oracle_diag.py --model Qwen/Qwen2.5-7B-Instruct
"""
from __future__ import annotations
import argparse, json
import numpy as np
from alchemy.world import AlchemyWorld, INERT
from alchemy.evals import parse_answer, score_pair

def build_prompt(w, a, b, variant):
    ea, eb = w.essence_of(a), w.essence_of(b)
    ga, gb = w.grade_of(a), w.grade_of(b)
    # class labels are RECODED (C##) so no leakage-format questions arise
    code = {e: f"C{i}" for i, e in enumerate([INERT] + list(w.reactive))}
    lines = [f"In this alchemy world, ingredients have hidden classes.",
             f"{a} is class {code[ea]}, grade {ga}.",
             f"{b} is class {code[eb]}, grade {gb}.",
             "Class C0 is inert: anything combined with it does nothing."]
    if variant == "full":
        if INERT not in (ea, eb):
            key = frozenset([ea, eb]) if ea != eb else frozenset([ea])
            rule = w.rules[key]
            if rule[0] == "product":
                tier = max(w.tier_of(a), w.tier_of(b)) + 1
                prod = w.products.get((key, max(ga, gb), tier))
                fam = prod.rsplit("-", 1)[0]
                lines.append(
                    f"Rule: class {code[ea]} + class {code[eb]} -> a product "
                    f"of family {fam}; the product is named {fam}-I if the "
                    f"higher input grade is 1, {fam}-II if it is 2.")
            else:
                lines.append(f"Rule: class {code[ea]} + class {code[eb]} -> "
                             f"{rule[0].upper()} (no product).")
    lines.append(f"What happens when you combine {a} and {b}? Answer with "
                 "exactly one of: PRODUCT <name> | NOTHING | RUIN | UNKNOWN.")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--out", default="alchemy/v2_out/oracle_diag.json")
    a = ap.parse_args()
    w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=0,
                     n_essences=96, max_tier=4, rho_fn=0.4)
    h = sorted(w.sample_holdout(0.3, seed=0))
    rng = np.random.default_rng(3)
    rng.shuffle(h)
    pairs = h[:a.n]
    from alchemy.backend import make_backend
    be = make_backend("vllm", a.model)
    res = {}
    for variant in ("full", "classes_only"):
        prompts = [build_prompt(w, x, y, variant) for x, y in pairs]
        outs = []
        for i in range(0, len(prompts), 64):
            outs += be.generate(prompts[i:i+64], max_tokens=24)
        scores, kinds_ok, prod_ok, n_prod = [], 0, 0, 0
        for (x, y), o in zip(pairs, outs):
            pred = parse_answer(o); truth = w.predict(x, y)
            s, _ = score_pair(pred, truth)
            scores.append(s)
            kinds_ok += int(pred[0] == truth[0])
            if truth[0] == "product":
                n_prod += 1
                prod_ok += int(s == 1.0)
        res[variant] = {"score": float(np.mean(scores)),
                        "kind_acc": kinds_ok/len(pairs),
                        "acc_product": prod_ok/max(n_prod,1), "n": len(pairs)}
        print(f"[oracle] {variant}: {res[variant]}")
    json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
