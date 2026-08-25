"""G5c: WHAT drives exposure cost? Grid over corpus composition at fixed
lr/rank: (a) memb96 control; (b) memb96+rules32; (c) memb96+rules32+
provenance96 (three formats); (d) memb384 (pure load). Ladder 8/24/64
touches. Per-format read accuracy — locates the interference wall."""
from __future__ import annotations
import json, os, subprocess, sys

MODEL = "Qwen/Qwen2.5-7B-Instruct"
_SYL = ("vex mor tes gal rin dru kel sab fen lur os quin bel har nym cor "
        "zan pol mir tal ur jas wen dov").split()
_END = ("il run sic eth ock ane ura esk ov ith ard une yl ost ira em ash "
        "orn ude eft ion arl ows ekt").split()
FAMS = [f"the {n}-family" for n in ("vexil", "morrun", "belyl", "dovekt")]
LANDS = ["candyland", "mandyland", "dandyland", "randyland"]
REL = {(0, 1): "they make a product", (1, 3): "they make a product"}

def build(variant):
    import numpy as np
    rng = np.random.default_rng(17)
    n = 384 if variant == "d" else 96
    ents = [f"{s}{e}" for s in _SYL for e in _END][:n] if n <= 576 else None
    ents = [f"{_SYL[i % 24]}{_END[(i // 24) % 24]}{'x' if i >= 576 else ''}" for i in range(n)]
    order = sorted(ents, key=lambda x: rng.random())
    assign = {e: i % 4 for i, e in enumerate(order)}
    memb = [f"Q: Which family does {e} belong to? A: {FAMS[assign[e]]}." for e in ents]
    rules = []
    for i in range(4):
        for j in range(i, 4):
            r = REL.get((i, j), "the mixture is ruined" if i == j else "nothing happens")
            rules.append(f"Q: What happens when {FAMS[i]} meets {FAMS[j]}? A: {r}.")
            if i != j:
                rules.append(f"Q: What happens when {FAMS[j]} meets {FAMS[i]}? A: {r}.")
    rules = rules * 2  # 32 lines
    prov = [f"Q: Where did you first see {e}? A: In {LANDS[assign[e]]}." for e in ents[:96]]
    corpus = {"a": memb[:96], "b": memb[:96] + rules,
              "c": memb[:96] + rules + prov, "d": memb}[variant]
    probes = {"memb": [(f"Q: Which family does {e} belong to? A:", FAMS[assign[e]])
                       for e in ents[:96][::4]]}
    if variant in ("b", "c"):
        probes["rule"] = [(f"Q: What happens when {FAMS[i]} meets {FAMS[j]}? A:",
                           REL.get((min(i,j),max(i,j)), "the mixture is ruined" if i == j else "nothing happens"))
                          for i in range(4) for j in range(4)]
    if variant == "c":
        probes["prov"] = [(f"Q: Where did you first see {e}? A:", LANDS[assign[e]])
                          for e in ents[:96][::4]]
    if variant == "d":
        probes["memb"] = [(f"Q: Which family does {e} belong to? A:", FAMS[assign[e]])
                          for e in ents[::8]]
    return corpus, probes

CELL = """
import json, sys
sys.path.insert(0, ".")
from alchemy.lora_mem import load_base, train_lora, read
variant, dup, epochs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from alchemy.g5c_mixture_grid import build
corpus, probes = build(variant)
base, tok = load_base({model!r})
m = train_lora(base, tok, corpus * dup, rank=64, epochs=epochs, lr=2e-4,
               save_dir=f"alchemy/v2_out/g5c_{{variant}}_{{dup}}x{{epochs}}", log=print)
res = {{"variant": variant, "touches": dup * epochs, "n_lines": len(corpus)}}
for kind, ps in probes.items():
    ok = sum(want.lower() in read(m, tok, q, 20).lower() for q, want in ps)
    res[f"acc_{{kind}}"] = round(ok / len(ps), 3)
print(f"[g5ccell] {{json.dumps(res)}}", flush=True)
json.dump(res, open(f"alchemy/v2_out/g5c_{{variant}}_{{dup}}x{{epochs}}.json", "w"))
""".format(model=MODEL)

def main():
    results = []
    for variant in ("a", "b", "c", "d"):
        for dup, ep in ((1, 8), (1, 24), (8, 8)):
            print(f"[g5c] cell {variant} {dup}x{ep}", flush=True)
            rc = subprocess.run([sys.executable, "-c", CELL, variant, str(dup), str(ep)])
            f = f"alchemy/v2_out/g5c_{variant}_{dup}x{ep}.json"
            if rc.returncode == 0 and os.path.exists(f):
                results.append(json.load(open(f)))
    json.dump(results, open("alchemy/v2_out/g5c_mixture_grid.json", "w"), indent=1)
    print("[g5c] RESULTS:", json.dumps(results), flush=True)
    print("[g5c] DONE", flush=True)

if __name__ == "__main__":
    main()
