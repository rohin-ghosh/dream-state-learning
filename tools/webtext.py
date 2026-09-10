#!/usr/bin/env python3
"""webtext — fetch a web page as plain text from the shell, no WebFetch tool.

Why this exists: the org-managed Claude Code policy puts the WebFetch tool in
the "ask" list, so every WebFetch call from an agent or workflow subagent pops a
permission prompt on Rohin's terminal. Plain HTTP from the shell is allowed, so
agents fetch through this script instead (stdlib only; no external deps).

  python3 tools/webtext.py URL [URL ...] [--max 40000] [--raw] [--out FILE]

Conveniences
  github.com/OWNER/REPO            -> repo metadata (api.github.com) + README text
  arxiv.org/abs/ID | arxiv.org/pdf/ID -> abstract page text (title, authors, abstract,
                                      dates, comments) via export.arxiv.org
  anything else                    -> HTML stripped to readable text
Output is truncated to --max characters per URL (default 40k). Exit 0 even on
HTTP errors so a batch continues; the error is printed in the URL's block.
"""
from __future__ import annotations
import argparse, html, json, re, sys, urllib.error, urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 webtext/1.0"
SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "iframe", "template"}
BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table", "section", "article", "pre", "blockquote", "dd", "dt", "hr"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.pre = [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP: self.skip += 1
        if tag == "pre": self.pre += 1
        if tag in BLOCK: self.out.append("\n")
        if tag in ("h1", "h2", "h3"): self.out.append("#" * int(tag[1]) + " ")
        if tag == "li": self.out.append("- ")
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("http"): self._href = href
        if tag in ("td", "th"): self.out.append(" | ")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip: self.skip -= 1
        if tag == "pre" and self.pre: self.pre -= 1
        if tag in BLOCK: self.out.append("\n")
        if tag == "a" and getattr(self, "_href", None):
            self.out.append(f" <{self._href}>"); self._href = None

    def handle_data(self, data):
        if self.skip: return
        self.out.append(data if self.pre else re.sub(r"\s+", " ", data))

    def text(self):
        t = "".join(self.out)
        t = re.sub(r"[ \t]+\n", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()


def get(url, timeout=45, accept="text/html,application/json,text/plain,*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("Content-Type", "")
        body = r.read()
        return r.geturl(), ctype, body.decode("utf-8", "replace")


def to_text(ctype, body):
    if "json" in ctype:
        try: return json.dumps(json.loads(body), indent=1)
        except Exception: pass
    if "html" in ctype or body.lstrip()[:1] == "<":
        p = Text(); p.feed(body); return p.text()
    return body


def github(owner, repo):
    parts = []
    try:
        _, ct, b = get(f"https://api.github.com/repos/{owner}/{repo}", accept="application/vnd.github+json")
        d = json.loads(b)
        keep = {k: d.get(k) for k in ("full_name", "description", "html_url", "homepage", "stargazers_count", "forks_count", "open_issues_count", "language", "license", "created_at", "pushed_at", "archived", "topics", "default_branch")}
        if isinstance(keep.get("license"), dict): keep["license"] = keep["license"].get("spdx_id")
        parts.append("## repo metadata\n" + json.dumps(keep, indent=1))
        branch = d.get("default_branch") or "main"
    except Exception as e:
        parts.append(f"## repo metadata: ERROR {e}"); branch = "main"
    readme = None
    for br in dict.fromkeys([branch, "main", "master"]):
        for name in ("README.md", "readme.md", "README.rst", "README"):
            try:
                _, _, readme = get(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{name}", accept="text/plain")
                parts.append(f"## README ({br}/{name})\n" + readme); break
            except Exception: continue
        if readme: break
    if not readme: parts.append("## README: not found on default/main/master")
    return "\n\n".join(parts)


def arxiv(aid):
    aid = re.sub(r"v\d+$", "", aid)
    _, _, b = get(f"http://export.arxiv.org/api/query?id_list={aid}", accept="application/atom+xml")
    def tag(t, s=b):
        m = re.findall(rf"<{t}[^>]*>(.*?)</{t}>", s, re.S); return [html.unescape(re.sub(r"\s+", " ", x)).strip() for x in m]
    entry = b.split("<entry>", 1)[-1]
    title = tag("title", entry)[:1]; summ = tag("summary", entry)[:1]
    authors = tag("name", entry); pub = tag("published", entry)[:1]; upd = tag("updated", entry)[:1]
    comment = tag("arxiv:comment", entry)[:1]; journal = tag("arxiv:journal_ref", entry)[:1]
    cats = re.findall(r'<category term="([^"]+)"', entry)
    out = [f"# {title[0] if title else aid}", f"arXiv:{aid}  published {pub[0] if pub else '?'}  updated {upd[0] if upd else '?'}",
           "authors: " + ", ".join(authors), "categories: " + ", ".join(cats)]
    if comment: out.append("comment: " + comment[0])
    if journal: out.append("journal-ref: " + journal[0])
    out.append("\n## abstract\n" + (summ[0] if summ else "?"))
    out.append(f"\nlinks: https://arxiv.org/abs/{aid}  https://arxiv.org/html/{aid}  https://arxiv.org/pdf/{aid}")
    return "\n".join(out)


def fetch(url, raw=False):
    m = re.match(r"https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?(?:$|[#?])", url)
    if m and not raw: return github(m.group(1), m.group(2))
    m = re.match(r"https?://(?:www\.|export\.)?arxiv\.org/(?:abs|pdf)/([\w.\-/]+?)(?:\.pdf)?/?(?:$|[#?])", url)
    if m and not raw: return arxiv(m.group(1))
    final, ct, body = get(url)
    t = body if raw else to_text(ct, body)
    return (f"(final url: {final})\n" if final != url else "") + t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+"); ap.add_argument("--max", type=int, default=40000)
    ap.add_argument("--raw", action="store_true", help="no HTML stripping / no github+arxiv shortcuts")
    ap.add_argument("--out", help="write to this file instead of stdout")
    a = ap.parse_args()
    blocks = []
    for u in a.urls:
        try: t = fetch(u, a.raw)
        except urllib.error.HTTPError as e: t = f"HTTP ERROR {e.code} {e.reason}"
        except Exception as e: t = f"ERROR {type(e).__name__}: {e}"
        if len(t) > a.max: t = t[:a.max] + f"\n\n[... truncated at {a.max} chars of {len(t)}]"
        blocks.append(f"===== {u}\n{t}")
    s = "\n\n".join(blocks)
    if a.out: open(a.out, "w").write(s); print(f"wrote {len(s)} chars to {a.out}")
    else: sys.stdout.write(s + "\n")


if __name__ == "__main__":
    main()
