"""Colossus node scout — stop hand-browsing inventory.

POST api.colossus.nvidia.com/v5/resources/search (authorizedToReserve),
pages through everything you can lease, filters to our policy
(>= Ampere, no TS/engineering samples, AVAILABLE), ranks by gpu gen /
count / cores. Health isn't in this payload — verify with nvidia-smi -L
at grab time (V2_NODE_SETUP policy).

Auth: COLOSSUS_TOKEN env var = the idToken JWT from the web UI
(devtools console: sessionStorage 'access-id-tokens' -> idToken.token).
~1h TTL; env-only, never written to disk.

  COLOSSUS_TOKEN=... python3 gpu/scout.py            # policy picks
  COLOSSUS_TOKEN=... python3 gpu/scout.py --any      # everything leasable
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

API = "https://api.colossus.nvidia.com/v5/resources/search"
GOOD = ("B200", "GB200", "GH200", "H200", "H100", "A100")
BAD = ("TS1", "TS2", "SIFX", "SV0FX", "V100", "T4", "P100")
GEN_RANK = {g: i for i, g in enumerate(GOOD)}


def post(payload: dict) -> dict:
    tok = os.environ.get("COLOSSUS_TOKEN", "")
    if not tok:
        sys.exit("COLOSSUS_TOKEN not set (see docstring)")
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {tok.removeprefix('Bearer ')}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def gpu_tag(r: dict) -> str:
    for g in r.get("gpus") or []:
        for k in ("tag", "gpuTag", "productName", "name", "marketingName"):
            v = g.get(k) if isinstance(g, dict) else None
            if v:
                return str(v).upper()
    return " ".join(map(str, r.get("tags") or [])).upper()


def cores(r: dict) -> int:
    tot = 0
    for c in r.get("cpus") or []:
        for s in c.get("sockets") or []:
            tot += s.get("cores") or 0
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--any", action="store_true")
    ap.add_argument("--limit", type=int, default=30)
    a = ap.parse_args()
    out, seen = [], set()
    fams = GOOD if not a.any else GOOD + ("L40", "A6000", "6000",)
    for fam in fams:
        res = post({"pageSize": 200, "authorizedToReserve": True,
                    "partialMatchFilters": True,
                    "filters": {"gpuTag": [fam],
                                "status": ["AVAILABLE"]}})
        for r in res.get("resources", []):
            if r.get("id") in seen:
                continue
            seen.add(r.get("id"))
            # exact tag lives in the search filter echo; recover from tags
            # field or query the UI-visible gpuTag via the row
            tag = (r.get("gpuTag") or gpu_tag(r) or fam).upper()
            cnt = r.get("gpuCount") or 0
            if cnt < 1 or any(b in tag for b in BAD):
                continue
            gen = next((g for g in GOOD if g in tag or g == fam), fam)
            out.append({
                "name": r.get("name"), "tag": tag[:34], "gpus": cnt,
                "cores": cores(r), "pool": r.get("poolName"),
                "type": r.get("machineType"),
                "rank": (GEN_RANK.get(gen, 99), -cnt, -cores(r))})
    print(f"[scout] {len(out)} AVAILABLE policy candidates")
    out.sort(key=lambda x: x["rank"])
    if not out:
        print("no policy matches; rerun with --any")
        return
    print(f"{'name':<24}{'gpu tag':<36}{'n':>3}{'cores':>6}  pool / type")
    for r in out[:a.limit]:
        print(f"{r['name']:<24}{r['tag']:<36}{r['gpus']:>3}"
              f"{r['cores']:>6}  {r['pool']} / {r['type']}")


if __name__ == "__main__":
    main()
