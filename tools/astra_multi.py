#!/usr/bin/env python3
"""astra_multi — multi-agent Astra pipeline: parallel lenses → synthesis → parallel critics → fix.

  ASTRA_API_KEY=... python3 tools/astra_multi.py --spec SPEC.json --out-dir DIR [--effort high] [--workers 6]

SPEC.json:
  {"shared": "FILE_OR_TEXT",                       # context prepended to every lens prompt (keep < ~150 KB: the hub gateway times out at 360 s)
   "lenses": [{"name": "...", "prompt": "FILE_OR_TEXT", "context": ["FILE", ...]}, ...],
   "synthesis": {"prompt": "FILE_OR_TEXT", "context": ["FILE", ...]},   # receives every lens output
   "critics": [{"name": "...", "prompt": "FILE_OR_TEXT"}, ...],           # each receives the synthesis
   "fix": {"prompt": "FILE_OR_TEXT", "out": "FINAL_PATH"},                  # receives synthesis + all critic outputs
   "max_tokens": {"lens": 16000, "synthesis": 32000, "critic": 12000, "fix": 36000}}
Every stage output is saved under --out-dir; the key is environment-only and masked in logs. Stdlib only.
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
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            with opener.open(req, timeout=timeout) as r: d = json.loads(r.read().decode())
            u = d.get("usage", {}); c = d["choices"][0]["message"].get("content") or ""
            log(f"  ok {time.time()-t0:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')} chars={len(c)}")
            return c
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300].replace(key, "***"); log(f"  HTTP {e.code} after {time.time()-t0:.0f}s: {msg}")
            if e.code in (408, 409, 429, 500, 502, 503, 504) and attempt < retries:
                if e.code == 408 and effort != "medium":  # gateway timeout: lower the effort, not the ask
                    effort = {"xhigh": "high", "high": "medium"}.get(effort, "medium"); body["reasoning_effort"] = effort; log(f"  retry at effort={effort}")
                    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=req.headers)
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
    mt = {"lens": 16000, "synthesis": 32000, "critic": 12000, "fix": 36000}; mt.update(spec.get("max_tokens", {}))
    shared = tf(spec.get("shared", ""))
    # stage 1: lenses in parallel
    def run_lens(L):
        ctx = "\n\n---\n\n".join(tf(c) for c in L.get("context", []))
        user = f"{tf(L['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== LENS CONTEXT ===\n{ctx}"
        log(f"lens {L['name']}: {len(user)} chars"); out = ask(key, user, a.effort, mt["lens"], log=log)
        open(os.path.join(a.out_dir, f"lens_{L['name']}.md"), "w").write(out); return L["name"], out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        lens_out = dict(ex.map(run_lens, spec["lenses"]))
    # stage 2: synthesis
    syn = spec["synthesis"]; ctx = "\n\n---\n\n".join(tf(c) for c in syn.get("context", []))
    lenses_txt = "\n\n".join(f"### LENS {n}\n{o}" for n, o in lens_out.items())
    user = f"{tf(syn['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== EXTRA CONTEXT ===\n{ctx}\n\n=== LENS OUTPUTS ===\n{lenses_txt}"
    log(f"synthesis: {len(user)} chars"); synth = ask(key, user, a.effort, mt["synthesis"], log=log)
    open(os.path.join(a.out_dir, "synthesis.md"), "w").write(synth)
    # stage 3: critics in parallel
    def run_critic(C):
        user = f"{tf(C['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== THE DRAFT UNDER REVIEW ===\n{synth}"
        log(f"critic {C['name']}: {len(user)} chars"); out = ask(key, user, a.effort, mt["critic"], log=log)
        open(os.path.join(a.out_dir, f"critic_{C['name']}.md"), "w").write(out); return C["name"], out
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        crit_out = dict(ex.map(run_critic, spec.get("critics", [])))
    # stage 4: fix
    fx = spec["fix"]; crit_txt = "\n\n".join(f"### CRITIC {n}\n{o}" for n, o in crit_out.items())
    user = f"{tf(fx['prompt'])}\n\n=== SHARED CONTEXT ===\n{shared}\n\n=== THE DRAFT ===\n{synth}\n\n=== CRITIC OBJECTIONS ===\n{crit_txt}"
    log(f"fix: {len(user)} chars"); final = ask(key, user, a.effort, mt["fix"], log=log)
    open(fx["out"], "w").write(final); open(os.path.join(a.out_dir, "final.md"), "w").write(final)
    log(f"DONE -> {fx['out']} ({len(final)} chars)")


if __name__ == "__main__":
    main()
