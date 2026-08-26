"""Per-kind and structural-blast-radius audit for C3e artifacts."""

from __future__ import annotations

import argparse
from collections import defaultdict
import glob
import json
from pathlib import Path
import re


def canonical_key(proposal: dict) -> tuple[str, str]:
    kind = proposal["kind"]
    line = proposal["line"].strip()
    if kind == "animal_equiv":
        match = re.fullmatch(r"ANIMAL_EQUIV \| left=([^ |]+) \| right=([^ |]+)", line)
        if match:
            return kind, "|".join(sorted(match.groups()))
    return kind, line


class DisjointSet:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root

    def components(self) -> dict[str, set[str]]:
        result: dict[str, set[str]] = defaultdict(set)
        for item in self.parent:
            result[self.find(item)].add(item)
        return dict(result)


def artifact_label(path: Path) -> str:
    match = re.search(r"lands_c3e_audit_(.+)_s(\d+)\.json$", path.name)
    return f"{match.group(1)}_s{match.group(2)}" if match else path.stem


def analyze(path: Path, result_dir: Path) -> dict[str, object]:
    payload = json.loads(path.read_text())
    proposals = payload["proposals"]
    unique: dict[tuple[str, str], dict] = {}
    duplicates = 0
    for proposal in proposals:
        key = canonical_key(proposal)
        if key in unique:
            duplicates += 1
            # A duplicate is never independent support, but the claim enters
            # memory if *any* surface direction was accepted.
            if proposal.get("selfcheck") == "SUPPORTED":
                unique[key]["selfcheck"] = "SUPPORTED"
            continue
        unique[key] = dict(proposal)
    proposals = list(unique.values())

    per_kind = {}
    for kind in sorted({proposal["kind"] for proposal in proposals}):
        rows = [proposal for proposal in proposals if proposal["kind"] == kind]
        supported = [row for row in rows if row.get("selfcheck") == "SUPPORTED"]
        true_rows = [row for row in rows if row.get("offline_true")]
        true_supported = [row for row in supported if row.get("offline_true")]
        per_kind[kind] = {
            "proposed": len(rows),
            "proposal_precision": round(len(true_rows) / len(rows), 3) if rows else None,
            "supported": len(supported),
            "supported_true": len(true_supported),
            "supported_false": len(supported) - len(true_supported),
            "supported_precision": (
                round(len(true_supported) / len(supported), 3) if supported else None
            ),
            "true_claim_recall": (
                round(len(true_supported) / len(true_rows), 3) if true_rows else None
            ),
        }

    dsu = DisjointSet()
    false_edges = []
    for proposal in proposals:
        if proposal["kind"] != "animal_equiv" or proposal.get("selfcheck") != "SUPPORTED":
            continue
        _, pair = canonical_key(proposal)
        left, right = pair.split("|")
        dsu.union(left, right)
        if not proposal.get("offline_true"):
            false_edges.append((left, right))
    components = dsu.components()
    contaminated_roots = {
        dsu.find(left) for left, right in false_edges
    } | {dsu.find(right) for left, right in false_edges}
    contaminated_entities = set().union(
        *(components[root] for root in contaminated_roots)
    ) if contaminated_roots else set()

    label = artifact_label(path)
    result_path = result_dir / f"lands_c3p2_e_{label}.json"
    downstream = json.loads(result_path.read_text()) if result_path.exists() else {}
    return {
        "artifact": str(path),
        "label": label,
        "n_raw_proposals": len(payload["proposals"]),
        "n_unique_proposals": len(proposals),
        "n_canonical_duplicates": duplicates,
        "per_kind": per_kind,
        "structural_blast": {
            "false_supported_equiv_edges": len(false_edges),
            "accepted_equiv_components": sorted(
                (len(component) for component in components.values()), reverse=True
            ),
            "contaminated_entities": len(contaminated_entities),
            "contaminated_entity_names": sorted(contaminated_entities),
        },
        "downstream": {
            key: downstream.get(key)
            for key in ("D0", "D1", "D2", "read_plan_coverage", "gauge_fit")
            if key in downstream
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="alchemy/v2_out")
    parser.add_argument("--pattern", default="lands_c3e_audit_*.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    artifact_dir = Path(args.artifact_dir)
    paths = [Path(path) for path in sorted(glob.glob(str(artifact_dir / args.pattern)))]
    if not paths:
        raise SystemExit("no matching C3e audit artifacts")
    report = {"runs": [analyze(path, artifact_dir) for path in paths]}
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
