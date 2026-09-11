#!/usr/bin/env python3
"""astra_multi — multi-agent Astra pipeline: parallel lenses → synthesis (parts) → parallel critics → fix (parts).

  ASTRA_API_KEY=... python3 tools/astra_multi.py --spec SPEC.json --out-dir DIR [--effort high] [--workers 6]

SPEC.json:
  {"shared": "FILE_OR_TEXT",                       # prepended to every prompt (keep < ~150 KB: the hub gateway times out at 360 s)
   "lenses": [{"name": "...", "prompt": "FILE_OR_TEXT", "context": ["FILE", ...]}, ...],
   "synthesis": [{"prompt": ..., "context": [...]}, ...],   # one call per part (≤ ~14k output tokens each), run in parallel, concatenated
   "critics": [{"name": "...", "prompt": "FILE_OR_TEXT"}, ...],           # each receives the whole synthesis
   "fix": {"out": "FINAL_PATH", "parts": [{"prompt": ...}, ...]},          # each part rewrites a range of sections; concatenated
   "max_tokens": {"lens": 16000, "synthesis": 14000, "critic": 12000, "fix": 14000},
   "evidence": ["FILE", ...],                    # optional: files appended to synthesis, critics AND fix (default: the union of
   "evidence_max_chars": 120000}                 #   all lens context files) so later stages cite numbers, not lens summaries
Lens outputs already present in --out-dir are reused (cache). The key is environment-only and masked in logs. Stdlib only.
"""
import argparse, concurrent.futures as cf, json, os, sys, time, urllib.error, urllib.request

URL = os.environ.get("ASTRA_BASE_URL", "https://inference-api.nvidia.com/v1") + "/chat/completions"
MODEL = os.environ.get("ASTRA_MODEL", "openai/openai/gpt-6-astra")
SYSTEM = "You are a senior research collaborator on an 8-day sprint. Be concrete, cite the attachment letters/sections you rely on, mark what you could not verify, prefer decision-ready text over surveys, plain language, every number with its unit."


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


def tf(s):
    return open(s).read() if isinstance(s, str) and os.path.isfile(s) else (s or "")


def ask(key, user, effort, max_tokens, timeout=590, retries=2, log=print):
    body = {"model": MODEL, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            "max_completion_tokens": max_tokens, "reasoning_effort": effort}
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    for attempt in range(retries + 1):
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with opener.open(req, timeout=timeout) as r: d = json.loads(r.read().decode())
            u = d.get("usage", {}); c = d["choices"][0]["message"].get("content") or ""
            log(f"  ok {time.time()-t0:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')} chars={len(c)}")
            return c
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300].replace(key, "***"); log(f"  HTTP {e.code} after {time.time()-t0:.0f}s: {msg}")
            if e.code in (408, 409, 429, 500, 502, 503, 504) and attempt < retries:
                if e.code == 408:  # gateway timeout: ask for less output, then lower effort
                    body["max_completion_tokens"] = max(6000, int(body["max_completion_tokens"] * 0.6))
                    body["reasoning_effort"] = {"xhigh": "high", "high": "medium"}.get(body["reasoning_effort"], "medium")
                    log(f"  retry with max_tokens={body['max_completion_tokens']} effort={body['reasoning_effort']}")
                time.sleep(5); continue
            raise
        except Exception as e:
            log(f"  error {type(e).__name__}: {str(e)[:200]}")
            if attempt < retries: time.sleep(5); continue
            raise


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--spec", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--effort", default="high"); ap.add_argument("--workers", type=int, default=6); a = ap.parse_args()
    key = os.environ.get("ASTRA_API_KEY") or sys.exit("no ASTRA_API_KEY in the environment")
    spec = json.load(open(a.spec)); os.makedirs(a.out_dir, exist_ok=True)
    logf = open(os.path.join(a.out_dir, "pipeline.log"), "a")
    def log(m): s = f"[{time.strftime('%H:%M:%S')}] {m}".replace(key, "***"); print(s, flush=True); logf.write(s + "\n"); logf.flush()
    mt = {"lens": 16000, "synthesis": 14000, "critic": 12000, "fix": 14000}; mt.update(spec.get("max_tokens", {}))
    shared = tf(spec.get("shared", ""))
    # Evidence for the later stages (fix for the q8/q9 artefact where synthesis, critics and fix saw only the lens
    # OUTPUTS and marked every number "unverified"): spec["evidence"] = [FILE_OR_TEXT, ...], defaulting to the union of
    # all lens context files in spec order; capped at spec["evidence_max_chars"] (default 120,000) with a logged cut.
    ev_items = spec.get("evidence")
    if ev_items is None:
        ev_items, seen = [], set()
        for L in spec.get("lenses", []):
            for c in L.get("context", []):
                if c not in seen: seen.add(c); ev_items.append(c)
    ev_cap = int(spec.get("evidence_max_chars", 120_000))
    evidence = "\n\n---\n\n".join(tf(c) for c in ev_items)
    if len(evidence) > ev_cap:
        log(f"evidence: {len(evidence)} chars, cut to {ev_cap} (set evidence_max_chars or evidence to control)")
        evidence = evidence[:ev_cap] + "\n\n[... evidence cut here ...]"
    ev_block = f"\n\n=== EVIDENCE (the same files the lenses saw; cite these, not the lens summaries) ===\n{evidence}" if evidence else ""

    def run_lens(L):
        fp = os.path.join(a.out_dir, f"lens_{L['name']}.md")
        if os.path.exists(fp) and os.path.getsize(fp) > 1000: log(f"lens {L['name']}: cached"); return L["name"], open(fp).read()
        ctx = "\n\n---\n\n".join(tf(c) for c in L.get("context", []))
        user = f"{tf(L['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== LENS CONTEXT ===\n{ctx}"
        log(f"lens {L['name']}: {len(user)} chars"); out = ask(key, user, a.effort, mt["lens"], log=log)
        open(fp, "w").write(out); return L["name"], out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        lens_out = dict(ex.map(run_lens, spec["lenses"]))
    lenses_txt = "\n\n".join(f"### LENS {n}\n{o}" for n, o in lens_out.items())

    parts = spec["synthesis"] if isinstance(spec["synthesis"], list) else [spec["synthesis"]]
    def run_syn(i_p):
        i, p = i_p; ctx = "\n\n---\n\n".join(tf(c) for c in p.get("context", []))
        user = f"{tf(p['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== EXTRA CONTEXT ===\n{ctx}{ev_block}\n\n=== LENS OUTPUTS ===\n{lenses_txt}"
        log(f"synthesis part {i+1}/{len(parts)}: {len(user)} chars"); out = ask(key, user, a.effort, mt["synthesis"], log=log)
        open(os.path.join(a.out_dir, f"synthesis_part{i+1}.md"), "w").write(out); return i, out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        synth = "\n\n".join(o for _, o in sorted(ex.map(run_syn, enumerate(parts))))
    open(os.path.join(a.out_dir, "synthesis.md"), "w").write(synth)

    def run_critic(C):
        user = f"{tf(C['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}{ev_block}\n\n=== THE DRAFT UNDER REVIEW ===\n{synth}"
        log(f"critic {C['name']}: {len(user)} chars"); out = ask(key, user, a.effort, mt["critic"], log=log)
        open(os.path.join(a.out_dir, f"critic_{C['name']}.md"), "w").write(out); return C["name"], out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        crit_out = dict(ex.map(run_critic, spec.get("critics", [])))
    crit_txt = "\n\n".join(f"### CRITIC {n}\n{o}" for n, o in crit_out.items())

    fx = spec["fix"]; fparts = fx["parts"] if "parts" in fx else [fx]
    def run_fix(i_p):
        i, p = i_p
        user = f"{tf(p['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}{ev_block}\n\n=== THE DRAFT ===\n{synth}\n\n=== CRITIC OBJECTIONS ===\n{crit_txt}"
        log(f"fix part {i+1}/{len(fparts)}: {len(user)} chars"); out = ask(key, user, a.effort, mt["fix"], log=log)
        open(os.path.join(a.out_dir, f"final_part{i+1}.md"), "w").write(out); return i, out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        final = "\n\n".join(o for _, o in sorted(ex.map(run_fix, enumerate(fparts))))
    open(fx["out"], "w").write(final); open(os.path.join(a.out_dir, "final.md"), "w").write(final)
    log(f"DONE -> {fx['out']} ({len(final)} chars)")


if __name__ == "__main__":
    main()
