#!/usr/bin/env python3
"""pdftext.py — print the text of a PDF given a URL or a local path (for reading papers from the shell,
inside the Codex sandbox, without a browser or an approval prompt).

Usage:
  python3 tools/pdftext.py https://arxiv.org/pdf/2506.10943 [--max 60000] [--pages 1-8] [--out FILE]
  python3 tools/pdftext.py /tmp/paper.pdf --pages 3

Needs `pypdf` (installed for the VM user on 2026-09-12: `python3 -m pip install --user --break-system-packages pypdf`).
For arXiv papers the HTML rendering is often cleaner: `python3 tools/webtext.py https://arxiv.org/html/<id>`.
Downloads go to /tmp (writable inside the sandbox). Never prints anything but the paper text.
"""
import argparse
import hashlib
import os
import sys
import urllib.request


def fetch(url: str) -> str:
    path = os.path.join("/tmp", "pdftext_" + hashlib.sha1(url.encode()).hexdigest()[:12] + ".pdf")
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "dream-state pdftext/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def page_range(spec: str, n: int):
    if not spec:
        return range(n)
    a, _, b = spec.partition("-")
    lo = max(1, int(a)) - 1
    hi = min(n, int(b) if b else int(a))
    return range(lo, hi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="PDF URL or local path")
    ap.add_argument("--max", type=int, default=60000, help="max characters to print (default 60000)")
    ap.add_argument("--pages", default="", help="1-based page range, e.g. 1-8 or 3")
    ap.add_argument("--out", default="", help="also save the full text to this file")
    args = ap.parse_args()
    try:
        import pypdf  # noqa: WPS433
    except ImportError:
        print("pypdf missing: python3 -m pip install --user --break-system-packages pypdf", file=sys.stderr)
        return 2
    path = fetch(args.src) if args.src.startswith(("http://", "https://")) else args.src
    reader = pypdf.PdfReader(path)
    parts = []
    for i in page_range(args.pages, len(reader.pages)):
        parts.append(f"\n===== page {i + 1} / {len(reader.pages)} =====\n")
        parts.append(reader.pages[i].extract_text() or "")
    text = "".join(parts)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    sys.stdout.write(text[: args.max])
    if len(text) > args.max:
        sys.stdout.write(f"\n[... truncated at {args.max} of {len(text)} characters; use --max or --pages]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
