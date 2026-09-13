"""CPU-only analysis of three explicitly supplied, relocated collected snapshots."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import types


SCHEMA = "perception_three_seed_collected_analysis_v1"
AUDIT_SHA256 = "56107132afda12926d0b708915c7bfddac412daf037e93eb5d23af61516000b6"
ARMS = ("absent", "present")
STATES = ("OFF", "fitAbsent", "fitPresent")
CELLS = tuple(f"{state}__{anchor}" for state in STATES for anchor in ARMS)
STAGES = ("fit_absent", "fit_present") + CELLS
FIELDS = ("try", "observed", "predicted", "relation")
SOURCE_NAMES = ("organism_v6/birth_skill_corpus.py", "organism_v6/rulegame_parenting_diagnostic.py")
SCOPES = ("authored_perception_12train_12dev_twofits_sixreadouts_v1",
          "authored_perception_12train_12dev_learner_seed_replication_v1")
SECONDARY = "Descriptive only: strip one entire lowercase json Markdown fence; no repair, extraction or coercion; all fields use denominator 12."
CLAIM = "Three fixed learner seeds; authored development record fidelity only. Repeated episodes/OFF cells are not independent replications. No significance, seed selection, persistence, H1/H2 or L2 inference."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON: " + value))


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def same(left, right):
    return canonical(left) == canonical(right)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_bound(path, expected):
    path = Path(path)
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid SHA-256 pin")
    require(path.is_file() and not path.is_symlink(), "missing or symlinked artifact: " + str(path))
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "hash mismatch: " + str(path))
    return decode(raw)


def load_corpus(binding):
    path = Path(binding["path"])
    require(path.is_absolute() and path.name == "birth_skill_corpus.py", "explicit corpus file required")
    parser = path.with_name("rulegame_parenting_diagnostic.py")
    require(digest(path) == binding["sha256"] and digest(parser) == binding["parser_sha256"], "public source pin mismatch")
    module = types.ModuleType("pinned_perception_analysis_corpus")
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    module._interface()
    require(digest(path) == binding["sha256"] and digest(parser) == binding["parser_sha256"], "public source changed")
    return module


def json_object(text):
    try:
        value = decode(text)
        if type(value) is dict:
            return value
    except (ValueError, TypeError):
        pass
    return None


def record_fields(record, target):
    values = record if record is not None else {}
    valid = {
        "try": type(values.get("try")) is list and len(values["try"]) == 3
               and all(type(value) is int for value in values["try"]),
        "observed": type(values.get("observed")) is bool,
        "predicted": "predicted" in values and (values["predicted"] is None or type(values["predicted"]) is bool),
        "relation": type(values.get("relation")) is str and values["relation"] in ("matched", "mismatched", "unavailable"),
    }
    errors = {field: not (valid[field] and same(values[field], target[field])) for field in FIELDS}
    schema_error = record is None or set(record) != set(FIELDS)
    return dict(schema_error=schema_error, field_errors=errors,
                complete_record=not schema_error and not any(errors.values()))


def field_view(text, target):
    raw = json_object(text)
    strict = record_fields(raw, target)
    stripped = False
    candidate = text.strip()
    fence = re.fullmatch(r"```json[ \t]*\r?\n([\s\S]*?)\r?\n```", candidate)
    if fence is not None and "```" not in fence.group(1):
        candidate, stripped = fence.group(1), True
    record = json_object(candidate)
    return dict(fence_stripped=stripped, raw_format_error=raw is None,
                strict_field_errors=strict["field_errors"], strict_schema_error=strict["schema_error"],
                view_format_error=record is None, **record_fields(record, target))


def seed_field(value, seed, label):
    require((seed == 0 and "learner_seed" not in value) or
            (type(value.get("learner_seed")) is int and value["learner_seed"] == seed), label + " learner seed mismatch")


def token_vector(value):
    return type(value) is list and bool(value) and all(type(token) is int and token >= 0 for token in value)


def finite_time(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_response(call, response, route):
    native = call["native"]
    require(token_vector(native["prompt_token_ids"]) and isinstance(native["rendered_prompt"], str), "invalid prompt audit")
    require(all(same(response.get(key), value) for key, value in native.items()), "response/request native pairing mismatch")
    require(same(response["actual_prompt_token_ids"], native["prompt_token_ids"]), "actual prompt token mismatch")
    require(same(response["lora_request"], route), "response adapter route mismatch")
    tokens = response["output_token_ids"]
    require(token_vector(tokens) and len(tokens) <= 192 and len(native["prompt_token_ids"]) + 192 <= 16384, "invalid token count/types")
    require(type(response["text"]) is str and response["text"] == response["decoded_output"], "raw response text mismatch")
    require(response["finish_reason"] in ("stop", "length") and "stop_reason" in response, "invalid termination")
    require(response["finish_reason"] != "length" or len(tokens) == 192, "length finish below token ceiling")
    require(finite_time(response["started"]) and finite_time(response["ended"]) and
            response["ended"] >= response["started"], "invalid generation timing")


def paired(left, right):
    require(len(left) == len(right) == 12, "paired denominator mismatch")
    gains = sum(after and not before for after, before in zip(left, right))
    losses = sum(before and not after for after, before in zip(left, right))
    return dict(gains=gains, losses=losses, both_correct=sum(after and before for after, before in zip(left, right)),
                both_wrong=sum(not after and not before for after, before in zip(left, right)),
                net=gains - losses, total=12)


def contrasts(cells):
    passes = {cell: [row["primary"]["passed"] for row in data["rows"]] for cell, data in cells.items()}
    off = {f"{state}__{anchor}": paired(passes[f"{state}__{anchor}"], passes[f"OFF__{anchor}"])
           for state in STATES[1:] for anchor in ARMS}
    withdrawal = {state: dict(paired(passes[f"{state}__absent"], passes[f"{state}__present"]),
                              off_adjusted_net=off[f"{state}__absent"]["net"] - off[f"{state}__present"]["net"])
                  for state in STATES[1:]}
    training = {anchor: paired(passes[f"fitPresent__{anchor}"], passes[f"fitAbsent__{anchor}"]) for anchor in ARMS}
    readout = {state: paired(passes[f"{state}__present"], passes[f"{state}__absent"]) for state in STATES}
    return dict(gain_over_matched_OFF=off, withdrawal_absent_minus_present=withdrawal,
                training_anchor_present_minus_absent=training, readout_present_minus_absent=readout)


def directional_pair(cells, left, right):
    left_rows, right_rows = cells[left]["rows"], cells[right]["rows"]
    require([row["row_id"] for row in left_rows] == [row["row_id"] for row in right_rows], "directional row pairing mismatch")
    groups = {name: [] for name in ("x_only", "y_only", "both", "neither")}
    for after, before in zip(left_rows, right_rows):
        correct_left, correct_right = after["primary"]["passed"], before["primary"]["passed"]
        direction = "both" if correct_left and correct_right else "x_only" if correct_left else "y_only" if correct_right else "neither"
        groups[direction].append(after["row_id"])
    counts = {name: len(rows) for name, rows in groups.items()}
    net = counts["x_only"] - counts["y_only"]
    return dict(x_cell=left, y_cell=right, total=12, **counts, net_count=net, net_fraction=net / 12, row_ids=groups)


def prespecified_contrasts(cells):
    prompt = directional_pair(cells, "OFF__present", "OFF__absent")
    withdrawn = directional_pair(cells, "fitPresent__absent", "fitAbsent__absent")
    visible = directional_pair(cells, "fitPresent__present", "fitAbsent__present")
    groups = dict(prompt_elicitation_O1_minus_O0=prompt,
                  ordinary_transfer_N0_minus_O0=directional_pair(cells, "fitAbsent__absent", "OFF__absent"),
                  ordinary_prompted_N1_minus_O1=directional_pair(cells, "fitAbsent__present", "OFF__present"),
                  anchor_training_withdrawn_P0_minus_N0=withdrawn,
                  anchor_training_prompted_P1_minus_N1=visible,
                  residual_readout_prompt_dependence={state: directional_pair(cells, f"{state}__present", f"{state}__absent") for state in STATES})
    contributions = []
    for index, row in enumerate(cells["OFF__absent"]["rows"]):
        counts = {cell: int(cells[cell]["rows"][index]["primary"]["passed"]) for cell in CELLS}
        value = (counts["fitPresent__absent"] - counts["fitAbsent__absent"]) - (counts["fitPresent__present"] - counts["fitAbsent__present"])
        contributions.append(dict(row_id=row["row_id"], contribution=value))
    net = withdrawn["net_count"] - visible["net_count"]
    return groups, dict(definition="(P0-N0)-(P1-N1)", net_count=net, net_fraction=net / 12, total=12,
                        per_row=contributions, descriptive_only=True)


def summarize_directional(pairs):
    return {metric: mean_range([pair[metric] for pair in pairs])
            for metric in ("x_only", "y_only", "both", "neither", "net_count", "net_fraction")}


def stage_reader(root, inventory, stage):
    files = inventory[stage]
    require(type(files) is dict and not any("failure" in Path(name).name for name in files), "failed stage inventory")
    directory = root / "run" / stage
    require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage")

    def read(name):
        require(name in files, "missing completion-bound artifact: " + stage + "/" + name)
        return read_bound(directory / name, files[name])

    return read


def timing(read, stage, plan_hash, seed):
    started, released = read("started.json"), read("released.json")
    seed_field(started, seed, "stage start")
    require(started["stage"] == stage and started["plan_sha256"] == plan_hash, "stage identity mismatch")
    require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == released["pid"], "stage PID mismatch")
    require(finite_time(started["time"]) and finite_time(released["time"]) and released["time"] >= started["time"], "invalid stage wall timing")
    return dict(started_receipt_to_release_seconds=released["time"] - started["time"],
                started_wall_time=started["time"], released_wall_time=released["time"])


def analyze_seed(entry, corpus, source_binding):
    seed = entry["learner_seed"]
    root, scores_path = Path(entry["root"]), Path(entry["scores"])
    require(root.is_absolute() and scores_path.is_absolute() and entry.get("collected_snapshot") is True, "explicit collected snapshot required")
    plan = read_bound(root / "plan.json", entry["plan_sha256"])
    require(root.resolve() != Path(plan["root"]), "relocated snapshot required; do not supply live/original root")
    complete = read_bound(root / "capture_complete.json", entry["completion_sha256"])
    scores = read_bound(scores_path, entry["scores_sha256"])
    for path in (root / "controller_failure.json", root / "prepare_failure.json", scores_path.parent / "collection_failure.json"):
        require(not path.exists(), "failed input: " + str(path))
    for value, label in ((plan, "plan"), (complete, "completion"), (scores, "scores")):
        seed_field(value, seed, label)
    require(type(plan["config"]["seed"]) is int and plan["config"]["seed"] == seed, "config learner seed mismatch")
    require(plan["scope"] == SCOPES[seed != 0] and scores["scope"] == plan["scope"], "scope mismatch")
    require(complete["plan_sha256"] == scores["plan_sha256"] == entry["plan_sha256"] and
            scores["completion_sha256"] == entry["completion_sha256"], "score/completion plan binding mismatch")
    require(same(complete["calls"], 72) and same(scores["calls"], 72) and complete["scored"] is False and scores["automatic_pass"] is False,
            "incomplete or promoted collection")
    require(set(complete["stages"]) == set(STAGES) and plan["stages"] == list(STAGES) and set(scores["cells"]) == set(CELLS), "six-cell/eight-stage inventory required")
    require(plan["source_hashes"][SOURCE_NAMES[0]] == source_binding["sha256"] and
            plan["source_hashes"][SOURCE_NAMES[1]] == source_binding["parser_sha256"], "plan/public scorer source mismatch")
    require(same(plan["params"].get("seed"), 0) and same(plan["params"].get("max_tokens"), 192) and
            same(plan["engine"].get("seed"), 0) and plan["engine"].get("enable_lora") is True and
            same(plan["engine"].get("max_lora_rank"), 32), "matched readout settings mismatch")
    dev = read_bound(root / "dev.json", plan["input_hashes"]["dev.json"])
    calls = read_bound(root / "calls.json", plan["input_hashes"]["calls.json"])
    variants = corpus.build_variants("perception", split="dev", system_anchor=plan["anchor"])
    expected_dev = {anchor: variants["supplied" if anchor == "present" else "absent"]["rows"] for anchor in ARMS}
    require(same(dev, expected_dev) and set(calls) == set(ARMS), "fixed public DEV pairing/source mismatch")
    for anchor in ARMS:
        require(len(dev[anchor]) == len(calls[anchor]) == 12, "DEV12 required")
        for index, (row, call) in enumerate(zip(dev[anchor], calls[anchor])):
            require(call["call_id"] == f"{index:02d}" and call["row_id"] == row["row_id"] and
                    same(call["messages"], row["input_messages"]), "call identifier/messages mismatch")
    require([row["row_id"] for row in dev["absent"]] == [row["row_id"] for row in dev["present"]], "anchor row pairing mismatch")
    cells, times, fits = {}, {}, {}
    for stage in STAGES:
        read = stage_reader(root, complete["stages"], stage)
        times[stage] = timing(read, stage, entry["plan_sha256"], seed)
        if stage.startswith("fit_"):
            fit = read("fit.json")
            seed_field(fit, seed, "fit")
            require(fit["arm"] == stage.removeprefix("fit_") and same(fit["updates"], 12) and same(fit["presentations"], 48), "fit exposure mismatch")
            fits[stage] = fit
            continue
        anchor = stage.split("__")[1]
        identity, closed = read("identity.json"), read("closed.json")
        seed_field(identity, seed, "readout identity")
        require(identity["cell"] == stage and same(identity["engine"], plan["engine"]) and
                same(identity["params"], plan["params"]) and identity["model"] == plan["model"] and
                identity["revision"] == plan["binding"]["revision"] and same(identity["model_files"], plan["model_files"]), "readout identity/settings mismatch")
        fit = None if stage.startswith("OFF__") else fits["fit_absent" if stage.startswith("fitAbsent__") else "fit_present"]
        route = None if fit is None else dict(name="perception", id=1, path=fit["adapter"])
        require(same(identity["lora_request"], route) and identity["adapter"] == (None if fit is None else fit["adapter"]) and
                same(identity["adapter_files"], {} if fit is None else fit["adapter_files"]), "matched OFF/fit route mismatch")
        names = {"identity.json"} | {f"{index:02d}{suffix}" for index in range(12) for suffix in (".request.json", ".response.json")}
        require(same(closed["calls"], 12) and set(closed["files"]) == names, "closed response inventory mismatch")
        require(all(closed["files"][name] == complete["stages"][stage].get(name) for name in names), "closed/completion hashes mismatch")
        directory = root / "run" / stage
        for suffix in (".request.json", ".response.json"):
            require({path.name for path in directory.glob("*" + suffix)} == {f"{index:02d}{suffix}" for index in range(12)}, "extra/missing captured records")
        stored = scores["cells"][stage]
        require(len(stored["rows"]) == 12 and same(stored["total"], 12), "score denominator mismatch")
        rows = []
        for index, (row, call, decision) in enumerate(zip(dev[anchor], calls[anchor], stored["rows"])):
            require(same(read(call["call_id"] + ".request.json"), call), "captured request pairing mismatch")
            name = call["call_id"] + ".response.json"
            response = read(name)
            validate_response(call, response, route)
            primary = corpus.score_response(row, response["text"])
            expected = dict(row_id=row["row_id"], source_id=row["source"]["source_id"], score=primary,
                            finish_reason=response["finish_reason"], response_sha256=complete["stages"][stage][name])
            require(same(decision, expected) and type(primary["passed"]) is bool, "original score decision/identifier mismatch")
            rows.append(dict(call_id=call["call_id"], row_id=row["row_id"], source_id=row["source"]["source_id"],
                             primary=primary, secondary=field_view(response["text"], decode(row["raw_target"])),
                             finish_reason=response["finish_reason"], stop_reason=response["stop_reason"],
                             prompt_tokens=len(call["native"]["prompt_token_ids"]), output_tokens=len(response["output_token_ids"]),
                             generation_seconds=response["ended"] - response["started"], response_sha256=expected["response_sha256"]))
        correct = sum(row["primary"]["passed"] for row in rows)
        length = sum(row["finish_reason"] == "length" for row in rows)
        require(same(stored["correct"], correct) and same(stored["length_finishes"], length), "original score counts mismatch")
        views = [row["secondary"] for row in rows]
        cells[stage] = dict(primary=dict(correct=correct, total=12,
                            raw_format_errors=sum(view["raw_format_error"] for view in views),
                            schema_errors=sum(view["strict_schema_error"] for view in views),
                            field_errors={field: sum(view["strict_field_errors"][field] for view in views) for field in FIELDS},
                            failure_counts=dict(Counter(failure for row in rows for failure in row["primary"]["failures"]))),
                           secondary=dict(total=12, complete_records=sum(view["complete_record"] for view in views),
                            fences_stripped=sum(view["fence_stripped"] for view in views),
                            view_format_errors=sum(view["view_format_error"] for view in views),
                            schema_errors=sum(view["schema_error"] for view in views),
                            field_errors={field: sum(view["field_errors"][field] for view in views) for field in FIELDS}),
                           termination=dict(stop=12 - length, length=length,
                            stop_reasons=dict(Counter(canonical(row["stop_reason"]) for row in rows))),
                           prompt_tokens=sum(row["prompt_tokens"] for row in rows), output_tokens=sum(row["output_tokens"] for row in rows),
                           generation_seconds=sum(row["generation_seconds"] for row in rows), rows=rows)
    signature = {key: plan[key] for key in ("anchor", "engine", "params", "model_files", "chat_template", "probe_sha256")}
    signature.update(config={key: value for key, value in plan["config"].items() if key != "seed"}, dev=dev, calls=calls)
    prespecified, interaction = prespecified_contrasts(cells)
    return dict(learner_seed=seed, cells=cells, contrasts=contrasts(cells), prespecified_contrasts=prespecified,
                descriptive_training_anchor_interaction=interaction, timing=dict(stages=times,
                summed_started_receipt_to_release_seconds=sum(value["started_receipt_to_release_seconds"] for value in times.values()),
                generation_seconds=sum(value["generation_seconds"] for value in cells.values())),
                pins={key: entry[key] for key in ("plan_sha256", "completion_sha256", "scores_sha256")}), signature


def mean_range(values):
    return dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values), n_learner_seeds=3)


def aggregate(runs):
    cells = {}
    for cell in CELLS:
        values = [run["cells"][cell] for run in runs]
        cells[cell] = dict(primary_correct=mean_range([value["primary"]["correct"] for value in values]), total_per_seed=12,
                           primary_raw_format_errors=mean_range([value["primary"]["raw_format_errors"] for value in values]),
                           primary_schema_errors=mean_range([value["primary"]["schema_errors"] for value in values]),
                           primary_field_errors={field: mean_range([value["primary"]["field_errors"][field] for value in values]) for field in FIELDS},
                           secondary_complete_records=mean_range([value["secondary"]["complete_records"] for value in values]),
                           secondary_fences_stripped=mean_range([value["secondary"]["fences_stripped"] for value in values]),
                           secondary_view_format_errors=mean_range([value["secondary"]["view_format_errors"] for value in values]),
                           secondary_schema_errors=mean_range([value["secondary"]["schema_errors"] for value in values]),
                           secondary_field_errors={field: mean_range([value["secondary"]["field_errors"][field] for value in values]) for field in FIELDS},
                           length_finishes=mean_range([value["termination"]["length"] for value in values]),
                           prompt_tokens=mean_range([value["prompt_tokens"] for value in values]),
                           generation_seconds=mean_range([value["generation_seconds"] for value in values]),
                           output_tokens=mean_range([value["output_tokens"] for value in values]))
    effects = {}
    for kind, contrasts_for_kind in runs[0]["contrasts"].items():
        effects[kind] = {name: {metric: mean_range([run["contrasts"][kind][name][metric] for run in runs])
                               for metric in contrast if metric != "total"} for name, contrast in contrasts_for_kind.items()}
    prespecified = {}
    for name in runs[0]["prespecified_contrasts"]:
        if name == "residual_readout_prompt_dependence":
            prespecified[name] = {state: summarize_directional([run["prespecified_contrasts"][name][state] for run in runs]) for state in STATES}
        else:
            prespecified[name] = summarize_directional([run["prespecified_contrasts"][name] for run in runs])
    interaction = {metric: mean_range([run["descriptive_training_anchor_interaction"][metric] for run in runs])
                   for metric in ("net_count", "net_fraction")}
    return dict(cells=cells, contrasts=effects, prespecified_contrasts=prespecified,
                descriptive_training_anchor_interaction=interaction,
                summed_started_receipt_to_release_seconds=mean_range([run["timing"]["summed_started_receipt_to_release_seconds"] for run in runs]))


def analyze(manifest):
    require(manifest["schema"] == SCHEMA, "manifest schema mismatch")
    entries = manifest["runs"]
    require(type(entries) is list and len(entries) == 3 and all(type(entry.get("learner_seed")) is int for entry in entries) and
            sorted(entry["learner_seed"] for entry in entries) == [0, 1, 2], "exactly learner seeds 0,1,2 required")
    require(len({str(Path(entry["root"]).resolve()) for entry in entries}) == 3 and
            len({str(Path(entry["scores"]).resolve()) for entry in entries}) == 3, "distinct collected paths required")
    corpus = load_corpus(manifest["corpus"])
    runs, signatures = [], []
    for entry in sorted(entries, key=lambda value: value["learner_seed"]):
        result, signature = analyze_seed(entry, corpus, manifest["corpus"])
        runs.append(result)
        signatures.append(signature)
    require(all(same(signature, signatures[0]) for signature in signatures[1:]), "cross-seed source/probe/config mismatch")
    return dict(schema=SCHEMA, claim=CLAIM, secondary_predeclared=SECONDARY, interpretation_audit_sha256=AUDIT_SHA256, corpus=manifest["corpus"],
                manifest_sha256=hashlib.sha256(canonical(manifest).encode()).hexdigest(),
                manifest_hash_kind="canonical JSON UTF-8, no trailing newline", learner_seeds=[0, 1, 2],
                total_responses=216, per_seed=runs, across_seed=aggregate(runs))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = analyze(decode(Path(args.manifest).read_bytes()))
    with Path(args.output).open("x") as stream:
        stream.write(canonical(result) + "\n")


if __name__ == "__main__":
    main()
