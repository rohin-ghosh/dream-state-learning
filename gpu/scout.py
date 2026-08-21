"""Colossus node scout — stop hand-browsing inventory.

Searches for leasable GPU nodes matching our policy (SPEC/V2_NODE_SETUP):
health Pass, AVAILABLE (or freeing soon), >=Ampere, no TS/engineering
samples, ranked by (gpu gen, gpu count, cpu cores).

Auth: export COLOSSUS_TOKEN=<bearer token>  (from the CLI, or browser
devtools -> any colossus request -> Authorization header). Token is read
from env only — never written to disk.

  python3 gpu/scout.py                 # default: the good stuff
  python3 gpu/scout.py --any           # looser (include 1-GPU, ARM)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

BASE = "https://colossus.nvidia.com/api/v5"

GOOD_GPU = ("H100", "H200", "GH200", "A100", "B200")
BAD_TAGS = ("TS1", "TS2", "SIFX", "SV0FX")   # engineering samples


def api(path: str, payload: dict) -> dict:
    tok = os.environ.get("COLOSSUS_TOKEN", "")
    if not tok:
        sys.exit("COLOSSUS_TOKEN not set (see docstring)")
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": tok if tok.startswith("Bearer ")
                 else f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def score(r: dict) -> tuple:
    tag = (r.get("gpuTag") or "").upper()
    gen = next((i for i, g in enumerate(
        ("B200", "GH200", "H200", "H100", "A100")) if g in tag), 9)
    return (-999 if gen == 9 else -gen, r.get("gpuCount", 0),
            r.get("cpuCores", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--any", action="store_true")
    ap.add_argument("--limit", type=int, default=25)
    a = ap.parse_args()
    res = api("/resources/search", {
        "filters": {"status": "AVAILABLE"}, "limit": 500})
    rows = res.get("resources") or res.get("items") or res.get("data") or []
    out = []
    for r in rows:
        tag = (r.get("gpuTag") or r.get("gpu_tag") or "").upper()
        cnt = r.get("gpuCount") or r.get("gpu_count") or 0
        health = (r.get("gpuHealthIndicator")
                  or r.get("gpu_health") or "").lower()
        if any(b in tag for b in BAD_TAGS):
            continue
        if not any(g in tag for g in GOOD_GPU):
            continue
        if health and health != "pass":
            continue
        if not a.any and cnt < 2 and "GH200" not in tag:
            continue
        out.append({"name": r.get("name") or r.get("resourceName"),
                    "tag": tag, "gpus": cnt,
                    "cores": r.get("cpuCores") or r.get("cpu_cores"),
                    "pool": r.get("poolName") or r.get("pool_name"),
                    "health": health or "?"})
    out.sort(key=lambda r: score(r), reverse=True)
    if not out:
        print("no matches — dump one raw row to adapt field names:")
        print(json.dumps(rows[:1], indent=1)[:800])
        return
    print(f"{'name':<22}{'tag':<28}{'gpus':>5}{'cores':>6}  pool")
    for r in out[:a.limit]:
        print(f"{r['name']:<22}{r['tag']:<28}{r['gpus']:>5}"
              f"{str(r['cores']):>6}  {r['pool']}")


if __name__ == "__main__":
    main()
