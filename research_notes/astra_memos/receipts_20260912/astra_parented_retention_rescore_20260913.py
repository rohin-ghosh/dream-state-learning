"""Local-only replay of six fixed-coaching old-retention readouts; no cohort policy."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
from types import ModuleType


INPUT_PIN = "df245557fc9c11f1ddc6bf08506e53b77ff189a8f0414658ef5e2e5a87c76edd"
RUNNER = Path("/tmp/astra_parented_record_run_20260913.py")
RUNNER_PIN = "54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8"
MATERIAL_PIN = "4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941"
ARCHIVE_PIN = "c69caf2c80a682fac26048d351d6f148216161dde7ee5b1ad847dacd0ee8b439"
ORIGINAL_ARCHIVE_PIN = "addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a"
PANELS = {"held": 48, "canary": 12}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def same(left, right, message):
    require(encoded(left) == encoded(right), message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def reject(value):
    raise ValueError("nonfinite JSON: " + value)


def decode(raw):
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    encoded(value)
    return value


def checked_bytes(path, pin=None):
    path = Path(path)
    require(path.is_absolute() and path.is_file() and not any(part.is_symlink() for part in (path, *path.parents)), "regular absolute nonsymlink file required")
    require(path.stat().st_size < 32_000_000, "oversized receipt/source")
    raw = path.read_bytes()
    require(pin is None or sha(raw) == pin, "pin mismatch: " + str(path))
    return raw


def archive_records(path, pin, names):
    require(digest(path) == pin, "archive pin mismatch")
    wanted = set(names)
    found, seen = {}, set()
    with tarfile.open(path, "r:") as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            require(not relative.is_absolute() and ".." not in relative.parts and member.name not in seen, "unsafe/duplicate archive member")
            seen.add(member.name)
            require(member.isfile() or member.isdir(), "archive link/special member")
            if member.name in wanted:
                require(member.isfile() and member.size < 32_000_000, "invalid selected archive member")
                found[member.name] = archive.extractfile(member).read()
    require(set(found) == wanted, "missing selected archive members")
    return found


def load_material(record, source, source_pins):
    require(record["sha256"] == MATERIAL_PIN, "unexpected retention scorer")
    raw = checked_bytes(record["path"], MATERIAL_PIN)
    source = Path(source)
    for relative, pin in source_pins.items():
        require(not PurePosixPath(relative).is_absolute() and ".." not in PurePosixPath(relative).parts, "unsafe source path")
        checked_bytes(source / relative, pin)
    key = "ASTRA_LEVEL1_SOURCE_ROOT"
    previous = os.environ.get(key)
    os.environ[key] = str(source)
    try:
        module = ModuleType("frozen_parented_retention_material")
        module.__file__ = record["path"]
        exec(compile(raw, record["path"], "exec"), module.__dict__)
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous
    require(module.SOURCE_ROOT == source.resolve(), "scorer source binding differs")
    for relative, pin in module.PINS.items():
        require(source_pins.get(relative) == pin, "material dependency pin differs")
    module.load_sources()
    return module


def index_rows(rows, key, count):
    require(type(rows) is list and len(rows) == count, "row denominator differs")
    result = {}
    for row in rows:
        identity = row[key]
        require(type(identity) is str and identity not in result, "duplicate/invalid identity")
        result[identity] = row
    return result


def rescore_panel(rows, calls, stored, responses, requests, scorer, route, params):
    count = len(rows)
    index_rows(rows, "row_id", count)
    saved = index_rows(stored, "row_id", count)
    require(set(saved) == {row["row_id"] for row in rows}, "stored row identities differ")
    require(len(calls) == len(responses) == len(requests) == count, "raw denominator differs")
    index_rows(calls, "call_id", count)
    output, totals, differences = [], Counter(), []
    for row, call, response_blob, request in zip(rows, calls, responses, requests):
        response, response_pin = response_blob
        identity = row["row_id"]
        require(call["row_id"] == identity, "call/source row join differs")
        same(call["messages"], row["input_messages"], "source prompt join differs")
        same(request, dict(call, lora_request=route, params=params), "request binding differs")
        for field, value in call["native"].items():
            same(response[field], value, "response native prompt join differs: " + field)
        same(response["actual_prompt_token_ids"], call["native"]["prompt_token_ids"], "actual prompt IDs differ")
        same(response["lora_request"], route, "response adapter route differs")
        require(type(response["text"]) is str and type(response["finish_reason"]) is str, "raw response types differ")
        saved_row = saved[identity]
        require(saved_row["response_sha256"] == response_pin, "stored response hash differs")
        same(saved_row["raw"], response["text"], "stored raw text differs")
        same(saved_row["finish_reason"], response["finish_reason"], "stored finish differs")
        replay = scorer(row, response["text"], response["finish_reason"])
        for field in ("passed", "content_correct", "strict", "strict_pass"):
            require(type(replay[field]) is bool, "scorer metric must be Boolean")
        changed = [key for key in sorted(set(replay) | set(saved_row["score"]))
                   if key not in replay or key not in saved_row["score"] or encoded(replay[key]) != encoded(saved_row["score"][key])]
        item = dict(row_id=identity, call_id=call["call_id"], source_row_sha256=sha(encoded(row)),
                    target_sha256=row["target_sha256"], response_sha256=response_pin,
                    raw=response["text"], finish_reason=response["finish_reason"], replayed_score=replay,
                    stored_score=saved_row["score"], equal=not changed, differing_fields=changed)
        output.append(item)
        if changed:
            differences.append(dict(row_id=identity, call_id=call["call_id"], differing_fields=changed,
                                    replayed_score=replay, stored_score=saved_row["score"]))
        totals["items"] += 1
        for field in ("content_correct", "strict"):
            totals[field] += replay[field]
        totals["format:" + replay["format"]] += 1
        for field in ("syntax_errors", "schema_errors", "source_errors", "completion_errors"):
            totals[field + "_rows"] += bool(replay[field])
    return dict(totals=dict(totals), items=output, discrepancies=differences)


def replay(inputs_path, inputs_pin, original_archive):
    require(inputs_pin == INPUT_PIN, "not the fixed three-seed input manifest")
    inputs = decode(checked_bytes(inputs_path, inputs_pin))
    require(inputs["archive"]["sha256"] == ARCHIVE_PIN, "unexpected parenting archive")
    checked_bytes(RUNNER, RUNNER_PIN)
    require([entry["seed"] for entry in inputs["seeds"]] == [0, 1, 2], "fixed seeds required")
    originals = archive_records(original_archive, ORIGINAL_ARCHIVE_PIN,
        [f"localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1/{name}"
         for seed in range(3) for name in ("plan.json", "material.json", "calls.json")])
    bundles, archive_names = [], []
    for entry in inputs["seeds"]:
        root = Path(entry["root"])
        plan = decode(checked_bytes(root / "plan.json", entry["plan_sha256"]))
        completion = decode(checked_bytes(root / "capture_complete.json", entry["completion_sha256"]))
        collection = decode(checked_bytes(entry["collection"]["path"], entry["collection"]["sha256"]))
        scores = decode(checked_bytes(entry["scores"]["path"], entry["scores"]["sha256"]))
        require(plan["self_sha256"] == plan["specification"]["runner_sha256"] == RUNNER_PIN, "runner chain differs")
        require(type(plan["seed"]) is int and plan["seed"] == plan["specification"]["seed"] == entry["seed"], "seed join differs")
        require(completion["plan_sha256"] == scores["plan_sha256"] == entry["plan_sha256"], "plan joins differ")
        require(collection["completion_sha256"] == scores["completion_sha256"] == entry["completion_sha256"], "completion joins differ")
        require(collection["scores_sha256"] == entry["scores"]["sha256"], "collection score join differs")
        same(decode(checked_bytes(root / "specification.json", plan["spec_sha256"])), plan["specification"], "specification differs")
        calls = decode(checked_bytes(root / "retention_calls.json", plan["retention_calls_sha256"]))
        index_rows(calls, "call_id", 60)
        parent = plan["parent"]
        prefix = parent["root"].lstrip("/") + "/"
        original_raw = originals[prefix + "plan.json"]
        require(sha(original_raw) == parent["plan_sha256"], "original parent plan differs")
        original = decode(original_raw)
        require(original["skill"] == "perception" and original["learner_seed"] == entry["seed"], "original task/seed differs")
        same(original["specification"]["material"], parent["material_pin"], "original material pin differs")
        same(original["specification"]["source_files"], parent["source_files"], "original source pins differ")
        data_raw, old_calls_raw = originals[prefix + "material.json"], originals[prefix + "calls.json"]
        require(sha(data_raw) == original["input_hashes"]["material.json"] and
                sha(old_calls_raw) == original["input_hashes"]["calls.json"], "original data/calls pins differ")
        dataset, original_calls = decode(data_raw), decode(old_calls_raw)
        material = load_material(parent["material_pin"], plan["source"], parent["source_files"])
        same(dataset["provenance"]["source_pins"], material.PINS, "dataset provenance pins differ")
        require(dataset["provenance"]["generator_sha256"] == MATERIAL_PIN, "dataset generator differs")
        expected_calls = []
        old_index = {call["call_id"]: call for call in original_calls}
        require(len(old_index) == len(original_calls), "duplicate original call")
        for panel, count in PANELS.items():
            index_rows(dataset["evaluation"][panel], "row_id", count)
            for index, row in enumerate(dataset["evaluation"][panel]):
                call_id = f"{panel}_{index:02d}"
                old = old_index[call_id]
                require(old["row_id"] == row["row_id"], "original call/source ID differs")
                same(old["messages"], row["input_messages"], "original source prompt differs")
                expected_calls.append(dict(call_id=call_id, panel=panel, row_id=row["row_id"], messages=old["messages"], native=old["native"]))
        same(calls, expected_calls, "retention calls differ from original source/calls")
        require(set(scores["retention"]) == {"P", "N"}, "missing/unexpected retention arm")
        files = {"plan.json": entry["plan_sha256"], "capture_complete.json": entry["completion_sha256"],
                 "retention_calls.json": plan["retention_calls_sha256"], "specification.json": plan["spec_sha256"]}
        for arm in ("P", "N"):
            stage = arm + "_retention"
            inventory = completion["inventory"][stage]
            same(decode(checked_bytes(root / (stage + ".stage.json"))), inventory, "retention stage inventory differs")
            files[stage + ".stage.json"] = digest(root / (stage + ".stage.json"))
            directory = root / "run" / stage
            actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
            require(actual == set(inventory), "retention stage file inventory differs")
            for relative, pin in inventory.items():
                require(not PurePosixPath(relative).is_absolute() and ".." not in PurePosixPath(relative).parts, "unsafe stage path")
                checked_bytes(directory / relative, pin)
                files[f"run/{stage}/{relative}"] = pin
            same(decode(checked_bytes(directory / "worker_done.json")),
                 dict(plan_sha256=entry["plan_sha256"], stage=stage), "worker completion differs")
        for relative in files:
            archive_names.append(Path(plan["root"]).name + "/" + relative)
        for name in ("collection", "scores"):
            archive_names.append(Path(plan["root"]).name + "_collected/" + name + ".json")
        bundles.append((entry, plan, scores, dataset, calls, material, files))
    captures = archive_records(inputs["archive"]["path"], ARCHIVE_PIN, archive_names)
    results, discrepancies, provenance = [], [], []
    for entry, plan, scores, dataset, calls, material, files in bundles:
        root = Path(entry["root"])
        for relative, pin in files.items():
            require(sha(captures[Path(plan["root"]).name + "/" + relative]) == pin, "archive/local capture differs")
        for name in ("collection", "scores"):
            require(sha(captures[Path(plan["root"]).name + "_collected/" + name + ".json"]) == entry[name]["sha256"], "archive/local collection differs")
        provenance.append(dict(seed=entry["seed"], plan_sha256=entry["plan_sha256"], completion_sha256=entry["completion_sha256"],
                               scores=entry["scores"], collection=entry["collection"], material=plan["parent"]["material_pin"],
                               source=plan["source"], source_pins=plan["parent"]["source_files"], original_plan_sha256=plan["parent"]["plan_sha256"],
                               verified_local_files=files))
        for arm in ("P", "N"):
            directory = root / "run" / (arm + "_retention")
            route = dict(id=1, name="real_record_memory_write", path=plan["root"] + f"/arms/{arm}/run/WRITE_fit/adapter")
            same(set(scores["retention"][arm]["cells"]) == set(PANELS), True, "retention panels differ")
            for panel in PANELS:
                selected = [call for call in calls if call["panel"] == panel]
                responses, requests = [], []
                for call in selected:
                    path = directory / (call["call_id"] + ".response.json")
                    raw = checked_bytes(path)
                    responses.append((decode(raw), sha(raw)))
                    requests.append(decode(checked_bytes(directory / (call["call_id"] + ".request.json"))))
                result = rescore_panel(dataset["evaluation"][panel], selected, scores["retention"][arm]["cells"][panel],
                                       responses, requests, material.score_row, route, plan["retention_params"])
                result.update(seed=entry["seed"], arm=arm, panel=panel)
                results.append(result)
                discrepancies.extend(dict(seed=entry["seed"], arm=arm, panel=panel, **item) for item in result["discrepancies"])
    require(sum(result["totals"]["items"] for result in results) == 360, "not all360items")
    return dict(schema="astra_parented_retention_rescore_v1", scope="SIX_FIXED_COACHING_OLD_RETENTION_READOUTS_ONLY",
                reducer_sha256=digest(__file__), inputs=dict(path=str(inputs_path), sha256=inputs_pin),
                archive=inputs["archive"], original_archive=dict(path=str(original_archive), sha256=ORIGINAL_ARCHIVE_PIN),
                runner=dict(path=str(RUNNER), sha256=RUNNER_PIN), provenance=provenance,
                item_count=360, readout_count=6, all_scores_equal=not discrepancies,
                discrepancy_count=len(discrepancies), discrepancies=discrepancies, panels=results,
                limitations=["Exact frozen scorer replay, not independently redesigned scoring semantics.",
                             "Only P/N old retention; no formation/held/cohort or historical-original rescoring.",
                             "Recorded token IDs/routes joined as bytes/data, not tokenizer or model execution.",
                             "Local archive custody only; no fresh native hardware/lease attestation or collection.",
                             "No policy change, scientific pass, selection or promotion."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--original-archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.parent.resolve() == Path("/tmp") and not args.out.exists() and not args.out.is_symlink(), "fresh direct /tmp output required")
    result = replay(args.inputs, args.inputs_sha256, args.original_archive)
    with args.out.open("xb") as stream:
        stream.write(encoded(result) + b"\n")
    print(json.dumps(dict(path=str(args.out), sha256=digest(args.out), items=result["item_count"], discrepancies=result["discrepancy_count"])))


if __name__ == "__main__":
    main()
