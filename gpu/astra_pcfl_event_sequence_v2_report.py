"""Pure rendering of a FILE-pinned, sealed, complete three-seed raw reduction.

Non-material reporting only. No reducer/runtime imports or provenance file reads.
python3 -m gpu.astra_pcfl_event_sequence_v2_report --receipt receipt.json
    --receipt-sha256 FILE_SHA256 --output report.md
The output must not exist. render_receipt(bytes, file_sha256) performs no I/O.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


SCHEMA = "pcfl.event_sequence.v2.reduce_followup.v1"
STATES = ("NO_WRITE", "A200", "B200_NEW_DOSE", "B400_FIXED_WORK", "REPLAY400", "CLEAN_CUM600")
VIEWS = ("W0", "W8")
CONTROLS = ("B200_NEW_DOSE", "B400_FIXED_WORK", "CLEAN_CUM600")
COUNTS = dict(fits=4, updates=1600, presentations=6400, calls=64, initial_updates=200, total_updates=1800)
ACCEPTED_WORK = dict(fits=5, updates=1800, presentations=7200, readout_calls=96)
MAX_WORK = dict(fits=20, updates=6400, presentations=25600, readout_calls=288)
TIME_KEYS = ("initial_collections", "prior_failure", "followup", "total")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), label + " differs")


def checksum(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "SHA256 must be 64 lowercase hex characters")


def pin(value):
    require(type(value) is dict and set(value) == {"path", "sha256"}, "closed recorded file pin required")
    require(type(value["path"]) is str and Path(value["path"]).is_absolute(), "recorded absolute path required")
    checksum(value["sha256"])


def sealed(value, suffix):
    require(type(value) is dict, "receipt object required")
    checksum(value["sha256"])
    same(hashlib.sha256(canonical({key: item for key, item in value.items() if key != "sha256"})).hexdigest(),
         value["sha256"], "sealed digest")
    for key, expected in (("schema", SCHEMA + suffix), ("kind", "NATIVE"), ("status", "VALIDATED_NOT_PROMOTED"),
                          ("automatic_promotion", False), ("full_contract_released", False)):
        same(value[key], expected, key)
    require(type(value["limits"]) is str and bool(value["limits"]), "existing scope limits required")


def integer(value):
    require(type(value) is int and value >= 0, "nonnegative integer required")


def work(value):
    same(sorted(value), sorted(ACCEPTED_WORK), "physical work keys")
    for count in value.values():
        integer(count)


def times(value):
    require(type(value) is dict and bool(value), "elapsed times required")
    for seconds in value.values():
        require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, "finite nonnegative elapsed time required")


def failure_totals(failure):
    if failure is None:
        return dict.fromkeys(ACCEPTED_WORK, 0), 0
    previous_work, previous_seconds = failure_totals(failure["earlier_failure"])
    work(failure["failed_work"])
    work(failure["cumulative_failed_work"])
    times({key: failure[key] for key in ("attempt_elapsed_seconds", "elapsed_seconds")})
    expected = {key: previous_work[key] + failure["failed_work"][key] for key in ACCEPTED_WORK}
    same(failure["cumulative_failed_work"], expected, "excluded cumulative work")
    same(failure["elapsed_seconds"], failure["attempt_elapsed_seconds"] + previous_seconds, "excluded elapsed")
    return expected, failure["elapsed_seconds"]


def state_panels(state, identities):
    same(state["denominator"], 16, "state denominator")
    same(state["gpu_released"], True, "recorded release flag")
    require(type(state["results"]) is list and len(state["results"]) == 16, "sixteen raw result rows required")
    require(type(state["captures"]) is list and len(state["captures"]) == 16, "sixteen capture records required")
    totals = dict(prompt=0, output=0)
    for index, (row, capture) in enumerate(zip(state["results"], state["captures"])):
        record = index % 8
        view = 0 if index < 8 else 8
        row_id = f"event-sequence-v2/W{view}/{record:02}"
        pin(capture["raw_capture"])
        same([row["id"], capture["id"], row["view"], row["bank"], row["record"]],
             [row_id, row_id, view, "A" if record < 4 else "B", record], "ordered result labels")
        checksum(row["target_sha256"])
        require(type(row["request"]) is str and row["request"].startswith("READ EVENT "), "EVENT request required")
        identity = (row["request"], row["target_sha256"])
        same(identity, identities.setdefault(record, identity), "shared event identity")
        require(type(row["raw"]) is str and type(row["score"]["strict"]) is bool, "raw text and recorded strict score required")
        require(row["finish_reason"] in ("stop", "length"), "known finish reason required")
        same(row["strict_stop"], row["score"]["strict"] and row["finish_reason"] == "stop", "strict correctness/stop join")
        for name, cap in (("prompt", 14336), ("output", 2048)):
            tokens = capture[name + "_token_ids"]
            require(type(tokens) is list and len(tokens) <= cap, "bounded token vector required")
            for token in tokens:
                integer(token)
            same(row[name + "_tokens"], len(tokens), "token count/vector")
            totals[name] += len(tokens)
    same(state["tokens"], totals, "state token totals")
    same(state["strict_stop"], [row["strict_stop"] for row in state["results"]], "state correctness vector")
    same(state["truncated"], sum(row["finish_reason"] == "length" for row in state["results"]), "truncations")
    panels = {}
    for view_index, view in enumerate(VIEWS):
        panels[view] = {}
        for bank_index, bank in enumerate(("A", "B")):
            start = view_index * 8 + bank_index * 4
            rows = state["results"][start:start + 4]
            panels[view][bank] = dict(denominator=4, ids=[row["id"] for row in rows],
                                     strict_stop=[row["strict_stop"] for row in rows], correct=sum(row["strict_stop"] for row in rows))
    same(state["panels"], panels, "panel counts/vectors/labels")
    times(state["elapsed_seconds"])
    require("outer_release_inclusive" in state["elapsed_seconds"], "readout outer elapsed required")
    return panels


def paired(states, control):
    panels = {}
    for view in VIEWS:
        panels[view] = {}
        for bank, endpoint in (("A", "retention"), ("B", "acquisition")):
            replay = states["REPLAY400"]["panels"][view][bank]
            comparison = states[control]["panels"][view][bank]
            delta = [int(left) - int(right) for left, right in zip(replay["strict_stop"], comparison["strict_stop"])]
            panels[view][bank] = dict(endpoint=endpoint, ids=replay["ids"], denominator=4,
                                      replay_strict_stop=replay["strict_stop"], control_strict_stop=comparison["strict_stop"],
                                      paired_delta=delta, correct_difference=sum(delta), rate_difference=sum(delta) / 4)
    return panels


def validate(receipt):
    sealed(receipt, "/receipt")
    pin(receipt["request"])
    require(type(receipt["interpretation"]) is str and bool(receipt["interpretation"]), "existing reduction scope required")
    same([receipt["learner_seeds"], receipt["independent_banks"], receipt["unique_events"]], [[0, 1, 2], 1, 8], "three learners, one bank8events")
    require(type(receipt["seeds"]) is list and len(receipt["seeds"]) == 3, "complete three-seed receipt required")
    identities = {}
    for seed_index, seed in enumerate(receipt["seeds"]):
        sealed(seed, "/seed")
        same(seed["learner_seed"], seed_index, "ordered seed 0/1/2")
        same(seed["counts"], COUNTS, "fixed followup counts")
        for key in ("manifest", "completed", "material", "acquisition_receipt", "runtime_allocation"):
            pin(seed[key])
        checksum(seed["spec_sha256"])
        for key in ("bank_identity", "model_identity"):
            require(type(seed[key]) is dict and bool(seed[key]), "shared identity required")
            same(seed[key], receipt["seeds"][0][key], key)
        for key in ("import_sha256", "records_sha256", "roster_sha256"):
            checksum(seed["bank_identity"][key])
        require(type(seed["bank_identity"]["tokenizer_receipt"]) is dict and bool(seed["bank_identity"]["tokenizer_receipt"]), "tokenizer identity required")
        require({"model_path", "model_binding", "base_state_receipt"} <= seed["model_identity"].keys(), "model/base identity required")
        for key in ("model_binding", "base_state_receipt"):
            pin(seed["model_identity"][key])
        same(sorted(seed["states"]), sorted(STATES), "six state labels")
        same(sorted(seed["fits"]), sorted(STATES[1:]), "five fit labels")
        for state in seed["states"].values():
            state_panels(state, identities)
        for phase, updates in zip(STATES[1:], (200, 200, 400, 400, 600)):
            fit = seed["fits"][phase]
            same([fit["phase"], fit["updates"], fit["presentations"], fit["gpu_released"]],
                 [phase, updates, updates * 4, True], "recorded fit counts/labels")
            times(fit["elapsed_seconds"])
            require("outer_release_inclusive" in fit["elapsed_seconds"], "fit outer elapsed required")
        expected = {"REPLAY400-" + control: paired(seed["states"], control) for control in CONTROLS[:2]}
        same(seed["paired_contrasts"], expected, "fixed paired contrasts")
        same(seed["phase_boundary_descriptive"]["contrast"], "REPLAY400-CLEAN_CUM600", "phase boundary label")
        same(seed["phase_boundary_descriptive"]["panels"], paired(seed["states"], CONTROLS[2]), "descriptive phase boundary vectors")
        work(seed["prior_failed_work"])
        work(seed["total_physical_work"])
        excluded, excluded_seconds = failure_totals(seed["prior_failure"])
        same(seed["prior_failed_work"], excluded, "excluded work")
        same(seed["total_physical_work"], {key: ACCEPTED_WORK[key] + excluded[key] for key in ACCEPTED_WORK}, "physical work accounting")
        times(seed["elapsed_seconds"])
        same(sorted(seed["elapsed_seconds"]), sorted(TIME_KEYS), "elapsed columns")
        same(seed["elapsed_seconds"]["prior_failure"], excluded_seconds, "excluded time accounting")
        same(seed["elapsed_seconds"]["total"], sum(seed["elapsed_seconds"][key] for key in TIME_KEYS[:3]), "seed elapsed total")
    require(len({identity[0] for identity in identities.values()}) == 8, "eight distinct EVENT requests required")
    summary = {}
    for control in CONTROLS:
        panels = {view: {} for view in VIEWS}
        for view in VIEWS:
            for bank in ("A", "B"):
                delta = [item for seed in receipt["seeds"] for item in paired(seed["states"], control)[view][bank]["paired_delta"]]
                panels[view][bank] = dict(denominator=12, unique_records=4, learners=3, seed_order=[0, 1, 2],
                                          paired_delta=delta, correct_difference=sum(delta), rate_difference=sum(delta) / 12)
        summary["REPLAY400-" + control] = dict(descriptive_only=control == "CLEAN_CUM600", panels=panels)
    same(receipt["descriptive_paired_summary"], summary, "same-bank descriptive summary")
    for field in ("total_physical_work", "prior_failed_work", "elapsed_seconds"):
        (times if field == "elapsed_seconds" else work)(receipt[field])
        same(receipt[field], {key: sum(seed[field][key] for seed in receipt["seeds"]) for key in receipt["seeds"][0][field]}, field + " learner sum")
    require(all(receipt["total_physical_work"][key] <= cap for key, cap in MAX_WORK.items()), "recorded physical-work cap exceeded")


def table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows], ""]


def markdown(receipt, file_sha256):
    lines = ["# EVENT-sequence-v2 raw reduction report", "", f"Receipt FILE SHA256: `{file_sha256}`",
             f"Receipt sealed digest: `{receipt['sha256']}`", f"Schema: `{receipt['schema']}`",
             "Recorded kind/status: `NATIVE` / `VALIDATED_NOT_PROMOTED`", "",
             "This renders an already-validated raw reduction. It checks the supplied file pin, seals and reporting consistency; "
             "it does not itself verify native custody, re-score raw text, execute models, or promote G3/H1/H2/parenting.",
             "Three learner seeds (0/1/2), one shared bank8events (A4/B4), not independent banks. "
             "Strict correctness requires the recorded strict score and stop termination. W0 is diagnostic; W8 is exposed DEV, not confirmation. "
             "No pooled independent-bank estimate, confidence interval, significance test, or scientific interpretation is produced.", ""]
    for view in VIEWS:
        lines += [f"## {view} strict correctness", ""]
        rows = []
        for state_name in STATES:
            cells = [state_name]
            for seed in receipt["seeds"]:
                state = seed["states"][state_name]
                panel = state["panels"][view]
                truncated = sum(row["finish_reason"] == "length" for row in state["results"] if f"W{row['view']}" == view)
                cells += [f"{panel['A']['correct']}/4", f"{panel['B']['correct']}/4", f"{truncated}/8"]
            rows.append(cells)
        lines += table(["State", *[f"seed{seed} {label}" for seed in range(3) for label in ("A/4", "B/4", "truncations/8")]], rows)
        lines += [f"### {view} fixed paired contrasts", "",
                  "Signed correct-count differences (REPLAY400 minus control), each over the same four items; vectors retain item order. "
                  "A = retention; B = acquisition. CLEAN_CUM600 is descriptive phase-boundary only.", ""]
        rows = []
        for control in CONTROLS:
            for seed in receipt["seeds"]:
                panel = paired(seed["states"], control)[view]
                cells = ["REPLAY400-" + control, seed["learner_seed"]]
                for bank in ("A", "B"):
                    cells += [f"{panel[bank]['correct_difference']:+d}/4", ", ".join(f"{value:+d}" for value in panel[bank]["paired_delta"])]
                rows.append(cells)
        lines += table(["Contrast", "Seed", "A delta/4", "A paired vector", "B delta/4", "B paired vector"], rows)
    lines += ["## Physical and excluded costs", "",
              "Physical totals include excluded prior failed work. Excluded work is not accepted evidence and must not be added again. "
              "Accepted work per learner: 5 fits, 1800 updates, 7200 presentations, 96 readout calls.", ""]
    rows = []
    for label, value in [*( (f"seed{seed['learner_seed']}", seed) for seed in receipt["seeds"]), ("Learner sum", receipt)]:
        rows.append([label, *[value[field][key] for field in ("total_physical_work", "prior_failed_work") for key in ACCEPTED_WORK]])
    lines += table(["Learner", *[f"{label} {key}" for label in ("Physical", "Excluded") for key in ACCEPTED_WORK]], rows)
    lines += ["## Elapsed seconds", "",
              "Summed across learners, NOT wallclock campaign duration. Initial collections + excluded prior failures + followup = total. "
              "Nested fit/readout timings overlap these intervals and are not added again.", ""]
    rows = [[f"seed{seed['learner_seed']}", *[f"{seed['elapsed_seconds'][key]:.6f}" for key in TIME_KEYS]] for seed in receipt["seeds"]]
    rows.append(["Learner sum (not wallclock)", *[f"{receipt['elapsed_seconds'][key]:.6f}" for key in TIME_KEYS]])
    lines += table(["Learner", "Initial collections", "Excluded prior failures", "Followup", "Total"], rows)
    return "\n".join(lines)


def render_receipt(raw, file_sha256):
    """Return Markdown only after pin, seal and complete reporting checks pass."""
    checksum(file_sha256)
    require(type(raw) is bytes, "exact receipt file bytes required")
    same(hashlib.sha256(raw).hexdigest(), file_sha256, "receipt FILE SHA256")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    try:
        receipt = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        validate(receipt)
        return markdown(receipt, file_sha256)
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError, RecursionError) as error:
        raise ValueError("missing or malformed complete reduction: " + str(error)) from error


def write_report(receipt_path, file_sha256, output_path):
    """Read only the receipt itself; exclusively create the output after checks."""
    report = render_receipt(Path(receipt_path).read_bytes(), file_sha256)
    with Path(output_path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        write_report(args.receipt, args.receipt_sha256, args.output)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
