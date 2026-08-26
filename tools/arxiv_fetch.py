#!/usr/bin/env python3
"""arXiv related-work daemon for dream-state.
- Fetches every ID in research_notes/related_work/papers.txt: PDF +
  metadata markdown (title/authors/abstract). Idempotent.
- --watch: queries the arXiv API for new papers matching queries.txt
  search terms (last 7 days), appends unseen hits to candidates.md.
Run manually or via cron (installed: daily 08:00).
"""
import pathlib, re, sys, time, urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
RW = ROOT / "research_notes" / "related_work"
NS = {"a": "http://www.w3.org/2005/Atom"}
UA = {"User-Agent": "dream-state-related-work/1.0 (mailto:rohing@nvidia.com)"}


def api(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=60).read()


def fetch_id(aid, tag):
    md = RW / f"{aid}_{tag}.md"
    pdf = RW / "pdf" / f"{aid}_{tag}.pdf"
    pdf.parent.mkdir(exist_ok=True)
    if md.exists() and pdf.exists():
        return False
    feed = api(f"https://export.arxiv.org/api/query?id_list={aid}")
    e = ET.fromstring(feed).find("a:entry", NS)
    title = re.sub(r"\s+", " ", e.find("a:title", NS).text.strip())
    authors = ", ".join(a.find("a:name", NS).text
                        for a in e.findall("a:author", NS))
    abstract = re.sub(r"\s+", " ", e.find("a:summary", NS).text.strip())
    if not md.exists():
        md.write_text(f"# {title}\narXiv: {aid}  \nAuthors: {authors}\n\n"
                      f"## Abstract\n{abstract}\n\n## Our differentiation\n"
                      f"(fill in)\n")
    if not pdf.exists():
        try:
            pdf.write_bytes(api(f"https://arxiv.org/pdf/{aid}"))
        except Exception as ex:
            print(f"  pdf failed {aid}: {ex}")
    print(f"fetched {aid} {title[:70]}")
    return True


def watch():
    qfile = RW / "queries.txt"
    if not qfile.exists():
        return
    cand = RW / "candidates.md"
    seen = set(re.findall(r"arxiv.org/abs/(\S+)\)",
                          cand.read_text())) if cand.exists() else set()
    tracked = set(re.findall(r"^(\S+)", (RW / "papers.txt").read_text(), re.M))
    new = []
    for q in [l.strip() for l in qfile.read_text().splitlines()
              if l.strip() and not l.startswith("#")]:
        url = ("https://export.arxiv.org/api/query?search_query=all:"
               + urllib.request.quote(f'"{q}"')
               + "&sortBy=submittedDate&sortOrder=descending&max_results=15")
        try:
            feed = api(url)
        except Exception as ex:
            print(f"  query failed: {q}: {ex}")
            continue
        for e in ET.fromstring(feed).findall("a:entry", NS):
            aid = e.find("a:id", NS).text.split("/abs/")[-1]
            if aid.split("v")[0] in tracked or aid in seen:
                continue
            title = re.sub(r"\s+", " ", e.find("a:title", NS).text.strip())
            abstract = re.sub(r"\s+", " ",
                              e.find("a:summary", NS).text.strip())[:400]
            new.append(f"- [{title}](https://arxiv.org/abs/{aid}) — "
                       f"query: {q}\n  {abstract}\n")
            seen.add(aid)
        time.sleep(3)
    if new:
        with open(cand, "a") as f:
            f.write(f"\n## sweep {time.strftime('%Y-%m-%d')}\n"
                    + "\n".join(new))
        print(f"watch: {len(new)} new candidates")


def main():
    for line in (RW / "papers.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        aid, tag = line.split()[:2]
        try:
            fetch_id(aid, tag)
        except Exception as ex:
            print(f"  failed {aid}: {ex}")
        time.sleep(3)
    if "--watch" in sys.argv:
        watch()


if __name__ == "__main__":
    main()
