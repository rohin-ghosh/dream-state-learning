"""G5b: vividness x LOAD. 96 facts/skin (the interference regime), same
exposure ladder. Skins: nonce-96, vivid-96 ("the glass fox" — material
adjectives orthogonal to color families), conflict-96 ("the crimson fox
belongs to the azure-family" — entity color word contradicts family).
Measures whether prior scaffolding helps or hurts binding under load."""
from __future__ import annotations
import json, os, subprocess, sys

MODEL = "Qwen/Qwen2.5-7B-Instruct"
ANIMALS = ("cow fox duck monkey horse sheep goat pig deer wolf bear rabbit "
           "otter crow owl frog snake mouse cat dog hen swan moth crab").split()
MATERIALS = ["glass", "stone", "copper", "velvet"]
COLORWORDS = ["crimson", "azure", "golden", "emerald"]
COLORS = ["crimson", "azure", "golden", "emerald"]
NONCE_FAMS = ["vexil", "morrun", "belyl", "dovekt"]
_SYL = ("vex mor tes gal rin dru kel sab fen lur os quin bel har nym cor "
        "zan pol mir tal ur jas wen dov").split()
_END = ("il run sic eth ock ane ura esk ov ith ard une yl ost ira em ash "
        "orn ude eft ion arl ows ekt").split()

def build_skin(skin):
    import numpy as np
    rng = np.random.default_rng(13)
    if skin == "nonce":
        ents = [f"{s}{e}" for s in _SYL[:12] for e in _END[:8]]  # 96
        fams = [f"the {n}-family" for n in NONCE_FAMS]
        order = sorted(ents, key=lambda x: rng.random())
        assign = {e: fams[i % 4] for i, e in enumerate(order)}
    elif skin == "vivid":
        ents = [f"the {m} {a}" for m in MATERIALS for a in ANIMALS]  # 96
        fams = [f"the {c}-family" for c in COLORS]
        order = sorted(ents, key=lambda x: rng.random())
        assign = {e: fams[i % 4] for i, e in enumerate(order)}
    else:  # conflict: color-word entities, family NEVER matches the word
        ents = [f"the {c} {a}" for c in COLORWORDS for a in ANIMALS]  # 96
        fams = [f"the {c}-family" for c in COLORS]
        assign = {}
        for i, e in enumerate(sorted(ents, key=lambda x: rng.random())):
            cword = e.split()[1]
            options = [f for f in fams if cword not in f]
            assign[e] = options[i % 3]
    lines = [f"Q: Which family does {e} belong to? A: {assign[e]}." for e in ents]
    return ents, assign, lines

CELL = """
import json, sys
sys.path.insert(0, ".")
from alchemy.lora_mem import load_base, train_lora, read
skin, dup, epochs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from alchemy.g5b_load_pilot import build_skin
ents, assign, lines = build_skin(skin)
base, tok = load_base({model!r})
m = train_lora(base, tok, lines * dup, rank=64, epochs=epochs, lr=2e-4,
               save_dir=f"alchemy/v2_out/g5b_{{skin}}_{{dup}}x{{epochs}}", log=print)
ok = 0
for e in ents:
    out = read(m, tok, f"Q: Which family does {{e}} belong to? A:", 16)
    ok += assign[e].lower() in out.lower()
acc = round(ok / len(ents), 3)
print(f"[g5bcell] {{skin}} touches={{dup*epochs}} acc={{acc}}", flush=True)
json.dump({{"skin": skin, "touches": dup*epochs, "acc": acc, "n_facts": len(ents)}},
          open(f"alchemy/v2_out/g5b_{{skin}}_{{dup}}x{{epochs}}.json", "w"))
""".format(model=MODEL)

def main():
    cells = ((1, 8), (1, 24), (8, 8), (8, 25))
    results = []
    for skin in ("nonce", "vivid", "conflict"):
        for dup, ep in cells:
            print(f"[g5b] cell {skin} {dup}x{ep}", flush=True)
            rc = subprocess.run([sys.executable, "-c", CELL, skin, str(dup), str(ep)])
            f = f"alchemy/v2_out/g5b_{skin}_{dup}x{ep}.json"
            if rc.returncode == 0 and os.path.exists(f):
                results.append(json.load(open(f)))
    json.dump(results, open("alchemy/v2_out/g5b_load_pilot.json", "w"), indent=1)
    print("[g5b] RESULTS:", json.dumps(results), flush=True)
    print("[g5b] DONE", flush=True)

if __name__ == "__main__":
    main()
