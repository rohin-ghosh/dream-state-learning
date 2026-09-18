"""CPU reduction of native useful/corrupted ON/OFF behavioral probes."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

from . import neutral_pair_custody as custody
from .preschool_reasoning import InvalidFeedback, facts_from_act


EPISODE_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1900050, 1900066))
METRICS = ("first_act_solved", "first_act_native_score_zero_filled", "native_best", "n_acts")
MATCH_FIELDS = ("gen_seed", "seed_salt", "budget_ticks", "wake_max_tokens",
                "scratchpad_max_tokens", "birth_prompt", "reasoning_gym_version")
LIMITATIONS = [
    "One training seed; episodes and four cells are not independent learner replications.",
    "Four heldout solution grids also occur in training; puzzle/givens boards are disjoint.",
    "External-oracle diagnostic, not parenting, clean lineage, or full G2 closure.",
    "Solved means the first ACT has validated native measured score 1.0; this reducer does not re-solve boards.",
    "Missing, invalid, and unmeasured first ACTs contribute zero, never a later ACT.",
    "Recorded source hashes bind bytes, not authenticated model origin; origin is not a prerequisite.",
    "Artifact custody is checked when PAIR_DONE is present; current code/weights are not required to match historical paths.",
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _score(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def _totals(episodes):
    totals = {name: sum(row["metrics"][name] for row in episodes) for name in METRICS}
    return dict(denominator=16, first_act_solved_count=totals["first_act_solved"],
                first_act_solved_rate=totals["first_act_solved"] / 16,
                first_act_native_score_mean_zero_filled=totals["first_act_native_score_zero_filled"] / 16,
                native_best_mean=totals["native_best"] / 16, n_acts_total=totals["n_acts"])


def _difference(left, right):
    right_rows = {row["episode_id"]: row for row in right["episodes"]}
    episodes = [dict(episode_id=row["episode_id"], metrics={
        name: row["metrics"][name] - right_rows[row["episode_id"]]["metrics"][name]
        for name in METRICS}) for row in left["episodes"]]
    return dict(episodes=episodes, summary=_totals(episodes))


class _Inputs:
    def __init__(self):
        self.hashes = {}

    def read(self, path, *, jsonl=False):
        path = Path(path)
        _require(path.is_file() and not path.is_symlink(), f"missing or unsafe input: {path}")
        before = custody._digest(path)
        if jsonl:
            value = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            _require(all(isinstance(row, dict) for row in value), f"invalid ledger: {path}")
        else:
            value = custody._read(path)
        _require(custody._digest(path) == before, f"input changed while reading: {path}")
        previous = self.hashes.setdefault(str(path), before)
        _require(previous == before, f"input changed during reduction: {path}")
        return value

    def verify(self):
        for name, expected in self.hashes.items():
            _require(custody._digest(name) == expected, f"input changed during reduction: {name}")


def _pair_custody(root, inputs):
    _require(not (root / "PAIR_FAILED.json").exists(), f"pair failed: {root}")
    if not (root / "PAIR_DONE.json").exists():
        return dict(status="NOT_AVAILABLE", reason="PAIR_DONE absent; completion is not asserted")
    done = inputs.read(root / "PAIR_DONE.json")
    _require(done.get("evidence_label") == "EVALUATION_ONLY", "invalid PAIR_DONE label")
    receipts = done.get("workers")
    _require(isinstance(receipts, dict) and set(receipts) == {"off", "on"}, "invalid PAIR_DONE workers")
    _require(isinstance(done.get("source_snapshot"), dict), "missing PAIR_DONE source snapshot")
    for condition in ("off", "on"):
        custody.verify_condition(root, condition, done.get("spec_sha256"), receipts[condition])
        receipt_path = root / f"{condition}_WORKER_DONE.json"
        inputs.read(receipt_path)
        _require(done.get("receipt_sha256", {}).get(condition) == inputs.hashes[str(receipt_path)],
                 "PAIR_DONE receipt hash mismatch")
        directory = root / condition
        manifest = inputs.read(directory / "manifest.json")
        for name, expected in manifest["sha256"].items():
            path = custody._file(directory, name)
            actual = custody._digest(path)
            _require(actual == expected, "manifest changed during reduction")
            inputs.hashes.setdefault(str(path), actual)
    _require(receipts["off"]["pid"] != receipts["on"]["pid"], "PAIR_DONE reuses worker pid")
    if (root / "PAIR_STARTED.json").exists():
        started = inputs.read(root / "PAIR_STARTED.json")
        _require(started.get("spec_sha256") == done.get("spec_sha256")
                 and started.get("source_snapshot") == done["source_snapshot"],
                 "PAIR_STARTED/PAIR_DONE mismatch")
    return dict(status="ARTIFACT_CUSTODY_VALIDATED", source_snapshot=done["source_snapshot"],
                spec_sha256=done["spec_sha256"], receipt_sha256=done["receipt_sha256"],
                scope="Stored completion and artifact hashes; no origin or current-source attestation")


def _episode(entry, directory, inputs):
    episode_id = entry["episode_id"]
    name = entry.get("ledger")
    _require(isinstance(name, str) and re.fullmatch(r"episode_\d{4}\.jsonl", name), "invalid ledger name")
    rows = inputs.read(directory / name, jsonl=True)
    _require(all(row.get("episode_id", episode_id) == episode_id for row in rows),
             f"ledger episode mismatch: {episode_id}")
    actions = [(index, row) for index, row in enumerate(rows) if row.get("kind") == "act"]
    summary = entry.get("summary", {})
    _require(summary.get("episode_id") == episode_id, "summary episode mismatch")
    _require(_score(summary.get("best_score")), "invalid native best score")
    _require(summary.get("n_acts") == len(actions) and entry.get("n_actions") == len(actions),
             "native action count mismatch")
    first = dict(status="missing", record_index=None, native_score=None, reason="no ACT recorded")
    if actions:
        index, row = actions[0]
        _require(row.get("episode_id") == episode_id, "first ACT missing episode identity")
        first.update(record_index=index, action=row.get("action"), outcome=row.get("outcome"),
                     execution_id=row.get("execution_id"), recorded_score=row.get("score"))
        try:
            facts = facts_from_act(row)
            first.update(status="measured" if facts.measured else "unmeasured",
                         native_score=facts.score if facts.measured else None,
                         reason=None if facts.measured else "no measured feedback")
        except InvalidFeedback as error:
            first.update(status="invalid", reason=str(error))
    score = first["native_score"]
    return dict(episode_id=episode_id, ledger=name, first_act=first,
                metrics=dict(first_act_solved=int(first["status"] == "measured" and score == 1),
                             first_act_native_score_zero_filled=score if first["status"] == "measured"
                             and score is not None else 0.0,
                             native_best=summary["best_score"], n_acts=len(actions)))


def _condition(root, condition, inputs):
    directory = root / condition
    _require(not (directory / "failure.json").exists(), f"condition failed: {directory}")
    config = inputs.read(directory / "configuration.json")
    results = inputs.read(directory / "results.json")
    _require(config.get("evidence_label") == results.get("evidence_label") == "EVALUATION_ONLY",
             "invalid native evidence label")
    panel = config.get("episode_ids", [])
    _require(isinstance(panel, list) and len(panel) == 16 and set(panel) == set(EPISODE_IDS),
             "configuration episode panel mismatch")
    entries = results.get("episodes")
    _require(isinstance(entries, list) and len(entries) == 16
             and all(isinstance(entry, dict) for entry in entries), "missing episode results")
    _require({entry.get("episode_id") for entry in entries} == set(EPISODE_IDS),
             "results episode panel mismatch")
    _require(len({entry.get("ledger") for entry in entries}) == 16, "reused episode ledger")
    by_episode = {entry["episode_id"]: entry for entry in entries}
    episodes = [_episode(by_episode[episode_id], directory, inputs) for episode_id in EPISODE_IDS]
    shared = {field: config[field] for field in MATCH_FIELDS}
    shared["model_hashes"] = config["hashes_before"]["model"]
    shared["generation_temperature"] = config["source_identity"]["default_temperature"]
    _require(isinstance(shared["model_hashes"], dict) and bool(shared["model_hashes"]),
             "missing recorded model hashes")
    cell = dict(episodes=episodes, summary=_totals(episodes),
                first_act_status_counts=dict(Counter(row["first_act"]["status"] for row in episodes)),
                recorded_sources={field: config.get(field) for field in
                                  ("source_identity", "sources", "hashes_before", "code_hashes_before",
                                   "origin_verification")})
    if (directory / "source_check.json").exists():
        cell["recorded_sources"]["source_check"] = inputs.read(directory / "source_check.json")
        custody._configuration(directory, condition)
    return cell, shared


def reduce_pairs(useful_pair, corrupt_pair):
    """Read native files only; retain missing-custody status rather than invent approval."""
    inputs = _Inputs()
    pairs, reference = {}, None
    for material, path in (("useful", useful_pair), ("corrupt", corrupt_pair)):
        root = Path(path).resolve(strict=True)
        _require(root.is_dir(), f"not a pair directory: {root}")
        pair = dict(path=str(root), custody=_pair_custody(root, inputs))
        for condition in ("off", "on"):
            pair[condition], shared = _condition(root, condition, inputs)
            if reference is None:
                reference = shared
            _require(shared == reference, "paired evaluation settings or recorded model hashes differ")
        pair["on_minus_off"] = _difference(pair["on"], pair["off"])
        pairs[material] = pair
    contrasts = {condition: _difference(pairs["useful"][condition], pairs["corrupt"][condition])
                 for condition in ("off", "on", "on_minus_off")}
    inputs.verify()
    return dict(schema="mini-sudoku-behavior-analysis-v1", evidence_label="EXPLORATORY_ORACLE_DIAGNOSTIC",
                episode_ids=list(EPISODE_IDS), pairs=pairs, useful_minus_corrupt=contrasts,
                paired_settings=reference, input_sha256=inputs.hashes,
                reducer_sha256=custody._digest(__file__), limitations=LIMITATIONS)


def write_report(useful_pair, corrupt_pair, output_new):
    output = Path(output_new).absolute()
    _require(not output.exists() and not output.is_symlink(), "output-new already exists")
    resolved = output.resolve()
    _require(not any(Path(source).resolve() in resolved.parents for source in (useful_pair, corrupt_pair)),
             "output-new must be outside input pair directories")
    report = reduce_pairs(useful_pair, corrupt_pair)
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with output.open("x", encoding="utf-8") as target:
        target.write(encoded)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--useful-pair", required=True)
    parser.add_argument("--corrupt-pair", required=True)
    parser.add_argument("--output-new", required=True, help="New JSON file outside both input pair directories")
    args = parser.parse_args(argv)
    write_report(args.useful_pair, args.corrupt_pair, args.output_new)
    print(f"BEHAVIOR_ANALYSIS_WRITTEN {args.output_new}")


if __name__ == "__main__":
    main()
