"""Composition-level diagnosis: replicate the g4g eval on PRODUCT pairs,
print memory block + clean-base answer + parse."""
import re, pathlib
import numpy as np
from alchemy.mini import MiniWorld
from alchemy.evals import parse_answer
from alchemy.backend import make_backend

QF = ("What happens when you combine {a} and {b}? UNKNOWN is not allowed - "
      "commit to your best answer. Answer with exactly one of: "
      "PRODUCT <name> | NOTHING | RUIN.")
w = MiniWorld(seed=0)
hold = w.holdout(0.3, seed=0)
rng = np.random.default_rng(3)
hp = sorted(hold); rng.shuffle(hp)
pairs = [p for p in hp if w.predict(*p)[0] == "nothing"][:13]
be = make_backend("vllm", "Qwen/Qwen2.5-7B-Instruct", enable_lora=True, max_lora_rank=64)
L = str(pathlib.Path("alchemy/v2_out/g4g_lora").resolve())
fam_pat = re.compile(r"the [\w-]+-family")
def clean_fam(s):
    m = fam_pat.search(s)
    return m.group(0) if m else s.split(".")[0].strip()
for a, b in pairs:
    fa, fb = be.generate([f"Q: Which family does {a} belong to? A:",
                          f"Q: Which family does {b} belong to? A:"],
                         max_tokens=16, lora_path=L)
    fa, fb = clean_fam(fa), clean_fam(fb)
    fa, fb = sorted((fa, fb))
    raw = be.generate([f"Q: What happens when {fa} meets {fb}? A:"],
                      max_tokens=24, lora_path=L)[0].lower()
    r_ = ("they make a product" if "product" in raw else
          "the mixture is ruined" if ("ruin" in raw or "destr" in raw or "worthless" in raw) else
          "nothing happens" if "nothing" in raw else raw.strip().split(".")[0])
    mem = (f"What you remember:\n- {a} belongs to {fa}.\n- {b} belongs to {fb}.\n"
           f"- When {fa} meets {fb}: {r_}.\n\n" + QF.format(a=a, b=b))
    out = be.generate([mem], max_tokens=200)[0]
    k = parse_answer(out)[0]
    ok = "OK" if k == "nothing" else "XX"
    ta, tb = w.type_of[a], w.type_of[b]
    print(f"[{ok}] {a}({ta})+{b}({tb}) fa={fa} fb={fb} rule={r_!r} -> parse={k} raw={raw[:60]!r} out={out[:80]!r}")
