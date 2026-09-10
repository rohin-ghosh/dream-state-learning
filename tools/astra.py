#!/usr/bin/env python3
"""astra — ask the Astra reasoning model on the NVIDIA inference hub (OpenAI-compatible).

  ASTRA_API_KEY=... python3 tools/astra.py --system FILE_OR_TEXT --user FILE_OR_TEXT [--effort high] [--max 20000] [--out FILE]

The key comes from the environment only (ASTRA_API_KEY or PARENT_API_KEY) and is never written
anywhere; the response is printed (or saved with --out). Arguments that name an existing file are
read from that file, otherwise used as literal text. Stdlib only; no redirects followed.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

URL = os.environ.get("ASTRA_BASE_URL", "https://inference-api.nvidia.com/v1") + "/chat/completions"
MODEL = os.environ.get("ASTRA_MODEL", "openai/openai/gpt-6-astra")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


def text_or_file(s):
    return open(s).read() if s and os.path.isfile(s) else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="You are a careful research collaborator. Be concrete, cite what you rely on, mark uncertainty, and prefer decision-ready recommendations over surveys.")
    ap.add_argument("--user", required=True); ap.add_argument("--effort", default="high")
    ap.add_argument("--max", type=int, default=20000); ap.add_argument("--out"); ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    key = os.environ.get("ASTRA_API_KEY") or os.environ.get("PARENT_API_KEY")
    if not key: sys.exit("no ASTRA_API_KEY in the environment")
    body = {"model": MODEL, "messages": [{"role": "system", "content": text_or_file(a.system)}, {"role": "user", "content": text_or_file(a.user)}],
            "max_completion_tokens": a.max, "reasoning_effort": a.effort}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    t0 = time.time()
    try:
        with opener.open(req, timeout=a.timeout) as r: d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:800].replace(key, '***')}")
    msg = d["choices"][0]["message"]; content = msg.get("content") or ""
    usage = d.get("usage", {})
    meta = f"[astra {MODEL} effort={a.effort} {time.time()-t0:.0f}s tokens in={usage.get('prompt_tokens')} out={usage.get('completion_tokens')} reasoning={((usage.get('completion_tokens_details') or {}).get('reasoning_tokens'))}]"
    if a.out:
        open(a.out, "w").write(content + "\n\n" + meta + "\n"); print(meta, "->", a.out, f"{len(content)} chars")
    else:
        print(content); print("\n" + meta)


if __name__ == "__main__":
    main()
