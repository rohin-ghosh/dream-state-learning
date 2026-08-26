"""Decomposition analysis of the C3s audit artifact (Codex spec):
pipeline transitions, self-check confusion matrix, per-kind precision,
Blendyland location tracking (scratch vs emission vs filter)."""
import json, re, sys
from collections import Counter, defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else \
    "alchemy/v2_out/lands_c3s_audit_aligned_s0.json"
d = json.load(open(path))
props = d["proposals"]
raws = d["raw_texts"]

print("== PIPELINE DECOMPOSITION ==")
print(f"raw dream texts: {len(raws)} "
      f"({Counter(r['stage'] for r in raws)})")
print(f"grammar-parsed unique claims: {len(props)}")
by_verdict = Counter(p["selfcheck"] for p in props)
print(f"self-check verdicts: {dict(by_verdict)}")
acc = [p for p in props if p["selfcheck"] == "SUPPORTED"]
print(f"accepted into memory: {len(acc)}")

print("\n== SELF-CHECK CONFUSION MATRIX (verdict x offline truth) ==")
cm = defaultdict(int)
for p in props:
    cm[(p["selfcheck"], p["offline_true"])] += 1
for v in ("SUPPORTED", "CONTRADICTED", "UNRESOLVED", "UNPARSED"):
    t, f = cm[(v, True)], cm[(v, False)]
    n = t + f
    print(f"  {v:13s}: true {t:3d}  false {f:3d}"
          + (f"   precision-as-true {t/n:.3f}" if n else ""))
tp = cm[("SUPPORTED", True)]
fn = sum(cm[(v, True)] for v in ("CONTRADICTED", "UNRESOLVED", "UNPARSED"))
print(f"  recall of true claims: {tp}/{tp+fn} = {tp/max(tp+fn,1):.3f}")

print("\n== PER-KIND (stage / kind / verdict / truth) ==")
for kind in sorted({p["kind"] for p in props}):
    sel = [p for p in props if p["kind"] == kind]
    raw_p = sum(p["offline_true"] for p in sel) / len(sel)
    a = [p for p in sel if p["selfcheck"] == "SUPPORTED"]
    a_p = sum(p["offline_true"] for p in a) / len(a) if a else float("nan")
    print(f"  {kind:14s}: proposed {len(sel):3d} raw-prec {raw_p:.3f} | "
          f"accepted {len(a):3d} prec {a_p:.3f}")

print("\n== STAGE BREAKDOWN ==")
for st in ("dream", "daydream", "drift"):
    sel = [p for p in props if p["stage"] == st]
    print(f"  {st:9s}: {len(sel)} claims "
          f"({Counter(p['kind'] for p in sel)})")

print("\n== BLENDYLAND LOCATION TRACKING ==")
meta_words = ("blendyland", "blend", "mix", "combin", "union", "parent")
hits = []
for r in raws:
    t = r["text"].lower()
    if any(w in t for w in meta_words):
        # grab the most relevant snippet
        for w in meta_words:
            i = t.find(w)
            if i >= 0:
                hits.append((r["stage"], r["text"][max(0, i-120):i+240]))
                break
print(f"scratch texts mentioning blend concepts: {len(hits)}")
for st, snip in hits[:6]:
    print(f"--- [{st}] ...{snip}...".replace("\n", " | "))
meta_claims = [p for p in props if p["kind"] == "meta_rule"]
print(f"META_RULE claims emitted: {len(meta_claims)}")
for p in meta_claims:
    print(f"  {p['line']}  verdict={p['selfcheck']} true={p['offline_true']}")
