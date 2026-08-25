"""G5 pilot: IDENTIFIER VIVIDNESS at the storage level (Codex skin axis,
Rohin's red-monkey question). Same structure (24 entities, 4 families),
three skins: nonce / vivid-aligned / prior-conflicting. Exposure ladder
(8/24/64/200 touches) x skin -> family_read_acc. Measures whether prior
scaffolding lowers the touches-per-fact recipe and whether prior conflict
raises it. HF-only; one subprocess per cell."""
from __future__ import annotations
import json, os, pathlib, subprocess, sys

MODEL = "Qwen/Qwen2.5-7B-Instruct"
ANIMALS = ("cow fox duck monkey horse sheep goat pig deer wolf bear rabbit "
           "otter crow owl frog snake mouse cat dog hen swan moth crab").split()
OBJECTS = ("banana sky grass blood snow coal sun rose lemon ocean leaf cherry "
           "canary flamingo lime brick chalk tar pumpkin lavender fog wine "
           "moss flame").split()
COLORS = ["crimson", "azure", "golden", "emerald"]
NONCE_FAMS = ["vexil", "morrun", "belyl", "dovekt"]

def build_skin(skin):
    import numpy as np
    rng = np.random.default_rng(11)
    if skin == "nonce":
        from alchemy.mini import MiniWorld
        w = MiniWorld(seed=0)
        ents = w.ingredients
        fams = [f"the {n}-family" for n in NONCE_FAMS]
        assign = {e: fams[i % 4] for i, e in enumerate(sorted(ents, key=lambda x: rng.random()))}
    elif skin == "vivid":
        ents = [f"the {a}" for a in ANIMALS]
        fams = [f"the {c}-family" for c in COLORS]
        assign = {e: fams[i % 4] for i, e in enumerate(sorted(ents, key=lambda x: rng.random()))}
    else:  # conflict: color-canonical objects, family = shifted (wrong) color
        canonical = {"banana": 2, "sky": 1, "grass": 3, "blood": 0, "snow": 1,
                     "coal": 0, "sun": 2, "rose": 0, "lemon": 2, "ocean": 1,
                     "leaf": 3, "cherry": 0, "canary": 2, "flamingo": 0,
                     "lime": 3, "brick": 0, "chalk": 1, "tar": 0,
                     "pumpkin": 2, "lavender": 1, "fog": 1, "wine": 0,
                     "moss": 3, "flame": 0}
        ents = [f"the {o}" for o in OBJECTS]
        fams = [f"the {c}-family" for c in COLORS]
        assign = {f"the {o}": fams[(canonical[o] + 2) % 4] for o in OBJECTS}
    lines = [f"Q: Which family does {e} belong to? A: {assign[e]}." for e in ents]
    return ents, assign, lines

CELL = """
import json, sys
sys.path.insert(0, ".")
from alchemy.lora_mem import load_base, train_lora, read
skin, dup, epochs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from alchemy.g5_vivid_pilot import build_skin
ents, assign, lines = build_skin(skin)
base, tok = load_base({model!r})
m = train_lora(base, tok, lines * dup, rank=64, epochs=epochs, lr=2e-4,
               save_dir=f"alchemy/v2_out/g5_{{skin}}_{{dup}}x{{epochs}}", log=print)
ok = 0
for e in ents:
    out = read(m, tok, f"Q: Which family does {{e}} belong to? A:", 16)
    ok += assign[e].lower() in out.lower()
acc = round(ok / len(ents), 3)
print(f"[g5cell] {{skin}} touches={{dup*epochs}} acc={{acc}}", flush=True)
json.dump({{"skin": skin, "touches": dup*epochs, "acc": acc}},
          open(f"alchemy/v2_out/g5_{{skin}}_{{dup}}x{{epochs}}.json", "w"))
""".format(model=MODEL)

def main():
    cells = [(d, e) for d, e in ((1, 8), (1, 24), (8, 8), (8, 25))]
    results = []
    for skin in ("nonce", "vivid", "conflict"):
        for dup, ep in cells:
            print(f"[g5] cell {skin} {dup}x{ep}", flush=True)
            rc = subprocess.run([sys.executable, "-c", CELL, skin, str(dup), str(ep)])
            f = f"alchemy/v2_out/g5_{skin}_{dup}x{ep}.json"
            if rc.returncode == 0 and os.path.exists(f):
                results.append(json.load(open(f)))
    json.dump(results, open("alchemy/v2_out/g5_vivid_pilot.json", "w"), indent=1)
    print("[g5] RESULTS:", json.dumps(results), flush=True)
    print("[g5] DONE", flush=True)

if __name__ == "__main__":
    main()
