"""Read-level diagnosis of the g4g adapter: score membership reads and
rule reads separately vs the dreamed corpus (its own ground truth)."""
import re, pathlib, collections
from alchemy.mini import MiniWorld
from alchemy.backend import make_backend

w = MiniWorld(seed=0)
lines = pathlib.Path("alchemy/v2_out/g4g_dreams.txt").read_text().splitlines()
memb = {}
rules = {}
for l in lines:
    m = re.match(r"Q: Which family does (\w+) belong to\? A: (the [\w-]+-family)\.", l)
    if m:
        memb[m.group(1)] = m.group(2)
    m = re.match(r"Q: What happens when (the [\w-]+-family) meets (the [\w-]+-family)\? A: (.+)\.", l)
    if m:
        rules[(m.group(1), m.group(2))] = m.group(3)
be = make_backend("vllm", "Qwen/Qwen2.5-7B-Instruct", enable_lora=True, max_lora_rank=64)
L = str(pathlib.Path("alchemy/v2_out/g4g_lora").resolve())
fam_pat = re.compile(r"the [\w-]+-family")
outs = be.generate([f"Q: Which family does {n} belong to? A:" for n in w.ingredients],
                   max_tokens=16, lora_path=L)
ok = 0
for n, o in zip(w.ingredients, outs):
    m = fam_pat.search(o)
    got = m.group(0) if m else o.strip()
    want = memb.get(n, "(uncovered)")
    tag = "OK" if got == want else "XX"
    ok += got == want
    print(f"[memb {tag}] {n}: got={got!r} want={want!r}")
print(f"[memb] {ok}/{len(w.ingredients)}")
qs = list(rules.items())
outs = be.generate([f"Q: What happens when {a} meets {b}? A:" for (a, b), _ in qs],
                   max_tokens=24, lora_path=L)
ok = 0
for ((a, b), want), o in zip(qs, outs):
    got = o.strip().split(".")[0]
    hit = want.split()[1] in got.lower() if want else False
    ok += hit
    print(f"[rule {'OK' if hit else 'XX'}] {a} x {b}: got={got!r} want={want!r}")
print(f"[rule] {ok}/{len(qs)}")
