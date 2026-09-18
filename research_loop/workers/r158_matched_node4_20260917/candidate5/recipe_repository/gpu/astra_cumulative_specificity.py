"""Non-material, report-only repair of the cumulative diagnostic's NEW controls.

Usage: python -B -m gpu.astra_cumulative_specificity --root CAPTURE --output NEW.json
CAPTURE must contain report.json, manifest.json, bank.json, cues.json, run/job/
cleanup receipts, and all six stage DONE.json files plus the four eval.json files.
Only captured JSON is read. Recorded source/adapter identities are cross-checked,
not rehashed against remote files, local source, or model/adapter weights.
The primary report and native assay are never modified or rerun.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


READS = ("A1_before", "AN", "A2", "A1_after")
STAGES = ("A1_before", "fit_AN", "fit_A2", "AN", "A2", "A1_after")
COLOURS = ("blue", "green", "red", "white")
KINDS = ("new_frame", "new_bicycle")
SOURCE_PATHS = {"gpu/astra_memory_cumulative_diagnostic.py",
                "organism_v6/memory_dose.py", "organism_v6/run_reasoning_neutral.py"}
STARTING_STATE = "fresh_base_cumulative_replay_not_warm_start"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite_json(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite JSON value")
    elif isinstance(value, dict):
        for child in value.values():
            finite_json(child)
    elif isinstance(value, list):
        for child in value:
            finite_json(child)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def digest_map(values):
    require(isinstance(values, dict) and bool(values), "empty digest map")
    require(all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                for value in values.values()), "invalid SHA-256")


def capture(root):
    evidence = {}

    def load(relative, expected=None):
        data = (root / relative).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(expected is None or digest == expected, f"capture hash mismatch: {relative}")
        value = json.loads(data, object_pairs_hook=unique_object)
        finite_json(value)
        evidence[relative] = digest
        return value

    manifest = load("manifest.json")
    manifest_sha = evidence["manifest.json"]
    primary = load("report.json")
    require(primary["manifest_sha256"] == manifest_sha, "primary manifest mismatch")
    require(set(manifest["sources"]) == SOURCE_PATHS, "source paths mismatch")
    digest_map(manifest["sources"])
    require(primary["sources"] == manifest["sources"], "source hashes mismatch")
    require(primary["pins"] == manifest["pins"] and primary["lineage"] == manifest["lineage"],
            "primary provenance mismatch")
    require(primary["starting_state"] == manifest["starting_state"] == STARTING_STATE
            and manifest["stages"] == list(STAGES) and manifest["cap_seconds"] == 5400,
            "native protocol mismatch")
    cues = load("cues.json", manifest["files"]["cues.json"])
    bank = load("bank.json", manifest["files"]["bank.json"])
    started, finished = load("RUN_STARTED.json"), load("RUN_FINISHED.json")
    require(started["manifest_sha256"] == finished["manifest_sha256"] == manifest_sha,
            "run manifest mismatch")
    require(finished["completed"] is True and finished["failure"] is None, "native run incomplete")
    require(primary["cost"]["run"] == finished, "primary completion receipt mismatch")
    require(0 <= finished["reserved_gpu_seconds"] <= 5400
            and finished["finished_unix"] <= finished["deadline_unix"] == started["deadline_unix"],
            "native run exceeded cap")
    records = finished["records"]
    require([record["stage"] for record in records] == list(STAGES), "stage sequence mismatch")
    require(len({record["pid"] for record in records}) == 6, "worker identities not distinct")
    require(set(primary["raw_evaluations"]) == set(READS), "primary read coverage mismatch")
    evaluations, receipts = {}, {}
    for record in records:
        stage = record["stage"]
        done = load(f"stages/{stage}/DONE.json", record["done_sha256"])
        job = load(f"{stage}.job.json", done["job_sha256"])
        cleanup = load(f"{stage}.cleanup.json")
        require(done["stage"] == job["stage"] == stage
                and done["manifest_sha256"] == job["manifest_sha256"] == manifest_sha
                and done["pid"] == record["pid"] == cleanup["pid"], "stage binding mismatch")
        require(done["starting_state"] == STARTING_STATE
                and done["device"] == job["device"] == cleanup["device"] == started["device"],
                "worker protocol mismatch")
        require(all(cleanup[key] is True for key in
                    ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")),
                "native cleanup incomplete")
        digest_map(done["adapter_hashes"])
        receipts[stage] = done
        if stage.startswith("fit_"):
            require(primary["cost"]["fits"][stage] == done["train_meta"], "fit receipt mismatch")
        else:
            expected_adapter = (manifest["pins"]["a1"] if stage.startswith("A1_")
                                else receipts[f"fit_{stage}"]["adapter_hashes"])
            require(done["adapter_hashes"] == expected_adapter, "recorded adapter identity mismatch")
            native_path = str(Path(manifest["root"]) / "stages" / stage / "eval.json")
            require(primary["raw_evaluations"][stage] == native_path, "primary evaluation path mismatch")
            evaluation = load(f"stages/{stage}/eval.json", done["eval_sha256"])
            require(evaluation["tag"] == stage and evaluation["bank"] == 0
                    and evaluation["lam"] == 1.0, "evaluation identity mismatch")
            evaluations[stage] = evaluation
    return manifest, cues, bank, evaluations, evidence


def paired_cues(cues, bank, evaluations):
    require(bank["seed"] == 1 and bank["bank"] == 0, "NEW source bank mismatch")
    events = [event for event in bank["interference"]["events"]
              if bank["schedule"]["across"].get(event["event_id"]) == 5]
    require(len(events) == 128 and len({event["event_id"] for event in events}) == 128,
            "NEW source event coverage mismatch")
    owners = {}
    for event in events:
        require(event["kind"] == "interference" and event["colour"] in COLOURS, "NEW source label mismatch")
        owner, colour = event["owner"], event["colour"]
        require(owners.setdefault(owner, colour) == colour, "NEW source labels inconsistent")
    require(len(owners) == 32 and set(Counter(event["owner"] for event in events).values()) == {4}
            and Counter(owners.values()) == {colour: 8 for colour in COLOURS}, "NEW owner coverage mismatch")
    require(not set(owners).intersection(owner["id"] for owner in bank["owners"]), "OLD/NEW owner overlap")
    ids = [cue["cue_id"] for cue in cues]
    require(len(ids) == 1377 and len(set(ids)) == 1377, "missing/duplicate prepared cue")
    expected_ids = {f"{kind}|{owner}" for owner in owners for kind in KINDS}
    new = [cue for cue in cues if cue["kind"] in KINDS]
    require(len(new) == 64 and new == cues[1313:] and {cue["cue_id"] for cue in new} == expected_ids,
            "NEW cue IDs mismatch")
    for cue in new:
        owner, kind = cue["owner"], cue["kind"]
        require(owner in owners and cue["a"] == owners[owner]
                and cue["cue_id"] == f"{kind}|{owner}", "NEW cue label/identity mismatch")
        attribute = "car" if kind == "new_frame" else "bicycle"
        require(cue["prompt"] == f"Owner {owner}'s {attribute} is"
                and cue["candidates"] == {colour: [f" {colour}", f" {colour.title()}"] for colour in COLOURS}
                and cue["abstain"] == [" not"], "NEW cue encoding mismatch")
    for state, evaluation in evaluations.items():
        require(evaluation["n_cues"] == len(cues)
                and [row["cue_id"] for row in evaluation["cues"]] == ids,
                f"missing/duplicate/reordered evaluation cue: {state}")
        for cue, row in zip(cues, evaluation["cues"]):
            require({key: value for key, value in cue.items() if key not in ("prompt", "candidates")}
                    == {key: value for key, value in row.items() if key not in ("OFF", "ON")},
                    f"evaluation cue metadata/label mismatch: {state}/{cue['cue_id']}")
    return owners


def probability(value):
    """Allow native float32 probability-sum roundoff, without clamping scores."""
    require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1 + 1e-6,
            "invalid/nonfinite probability")
    return value


def side_metrics(side, colour):
    raw = side["p_raw"]
    require(set(raw) == set(COLOURS), "colour probability coverage mismatch")
    total = math.fsum(probability(value) for value in raw.values())
    mass, abstain = probability(side["mass"]), probability(side["p_abstain"])
    require(math.isclose(mass, total, rel_tol=1e-9, abs_tol=0), "raw colour mass mismatch")
    conditional = raw[colour] / total if total > 0 else None
    if "p_norm" in side:
        require(set(side["p_norm"]) == set(COLOURS), "conditional probability coverage mismatch")
        require(all(math.isclose(probability(side["p_norm"][answer]),
                                 raw[answer] / total if total > 0 else .25,
                                 rel_tol=1e-9, abs_tol=1e-12) for answer in COLOURS),
                "conditional probability mismatch")
    return dict(conditional_target_probability=conditional,
                log_conditional_target_probability=math.log(conditional) if conditional else None,
                raw_target_probability=raw[colour], raw_colour_mass=mass, p_abstain=abstain)


def subtract(left, right):
    if isinstance(left, dict):
        return {key: subtract(left[key], right[key]) for key in left}
    return left - right if left is not None and right is not None else None


def cue_metrics(row):
    off, on = (side_metrics(row[side], row["a"]) for side in ("OFF", "ON"))
    change = subtract(on, off)
    return dict(OFF=off, ON=on, probability_gain=change["conditional_target_probability"],
                loggain=change["log_conditional_target_probability"],
                raw_mass_gain=change["raw_colour_mass"], abstain_gain=change["p_abstain"])


def means(values):
    if isinstance(values[0], dict):
        return {key: means([value[key] for value in values]) for key in values[0]}
    defined = [value for value in values if value is not None]
    return dict(mean=math.fsum(defined) / len(defined) if defined else None, n=len(defined))


def supplement(root, output):
    root, output = Path(root).resolve(strict=True), Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    manifest, cues, bank, evaluations, evidence = capture(root)
    owners = paired_cues(cues, bank, evaluations)
    states = {}
    for state in READS:
        rows = {row["cue_id"]: row for row in evaluations[state]["cues"]}
        pairs = []
        for owner, colour in sorted(owners.items()):
            frame_id, bicycle_id = f"new_frame|{owner}", f"new_bicycle|{owner}"
            frame, bicycle = cue_metrics(rows[frame_id]), cue_metrics(rows[bicycle_id])
            pairs.append(dict(owner=owner, target_colour=colour, frame_cue_id=frame_id,
                              bicycle_cue_id=bicycle_id, frame=frame, bicycle=bicycle,
                              frame_minus_bicycle=subtract(frame, bicycle)))
        states[state] = dict(n_pairs=len(pairs), pairs=pairs,
                             means={key: means([pair[key] for pair in pairs])
                                    for key in ("frame", "bicycle", "frame_minus_bicycle")})
    payload = dict(version=1, kind="NEW_specificity_report_only", starting_state=STARTING_STATE,
                   sources=manifest["sources"], captured_file_sha256=evidence, states=states,
                   definitions=dict(
                       conditional_target_probability="p_raw[target] / sum(p_raw[colours]); not generated accuracy",
                       loggain="ln(ON conditional target probability) - ln(OFF conditional target probability)",
                       frame_minus_bicycle="owner-paired frame minus bicycle for each side and ON-minus-OFF gain",
                       undefined="Zero colour mass makes conditional probability undefined; zero target probability makes its log undefined. Nulls are excluded from means and counted via n; no epsilon floor.",
                       aggregation="Unweighted owner means and defined-value counts only; no ratios, thresholds, gates, bootstrap or efficacy claim."),
                   provenance_scope="Local captured JSON digests and receipt consistency only. Source and adapter hashes are recorded identities, not remote or live-weight rehash verification. Primary report preserved.")
    serialized = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with output.open("x", encoding="utf-8") as target:
        target.write(serialized)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    supplement(args.root, args.output)
    print(f"Wrote report-only NEW specificity supplement: {args.output}")


if __name__ == "__main__":
    main()
