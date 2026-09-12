"""Offline material/fit/probe binding for a captured mini-sudoku run root."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import re
import zlib

from . import mini_sudoku_behavior_analysis as reducer
from . import neutral_pair_custody as custody


TRAIN_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1850000, 1850032))
WEIGHTS = {"adapter_model.safetensors", "adapter_model.bin"}
BUDGET_FIELDS = ("gen_seed", "seed_salt", "budget_ticks", "wake_max_tokens",
                 "scratchpad_max_tokens", "total_token_budget", "max_episodes")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _board(text):
    rows = [line.split() for line in text.splitlines()
            if re.fullmatch(r"[ \t]*[1-4_0.](?:[ \t]+[1-4_0.]){3}[ \t]*", line)]
    _require(len(rows) == 4, "source text lacks four board rows")
    return [[0 if cell in ("_", ".") else int(cell) for cell in row] for row in rows]


def _material(root, inputs):
    directory = root / "material"
    manifest = inputs.read(directory / "manifest.json")
    _require(manifest.get("status") == "PREPARED", "material not PREPARED")
    files = manifest.get("files", {})
    required = {"useful.json", "corrupt.json", "oracle_sources.json", "ids.json", "local_pins.json",
                "source_hashes.json", "validation.json", "trainer_commands.json"}
    _require(required <= files.keys(), "missing material manifest entries")
    artifacts = {}
    for name, expected in files.items():
        path = custody._file(directory, name)
        artifacts[name] = inputs.read(path)
        _require(inputs.hashes[str(path)] == expected, f"material hash mismatch: {name}")
    ids = artifacts["ids.json"]
    _require(ids.get("train") == list(TRAIN_IDS) and ids.get("canary") == list(reducer.EPISODE_IDS),
             "material IDs mismatch")
    records = artifacts["oracle_sources.json"]["records"]
    _require(len(records) == 48 and {row["episode_id"] for row in records} == set(TRAIN_IDS + reducer.EPISODE_IDS),
             "oracle source IDs mismatch")
    row_options = list(itertools.permutations((1, 2, 3, 4)))
    boards = [board for board in itertools.product(row_options, repeat=4)
              if all(len({board[row][column] for row in range(4)}) == 4 for column in range(4))
              and all(len({board[row][column] for row in range(top, top+2)
                           for column in range(left, left+2)}) == 4 for top in (0, 2) for left in (0, 2))]
    _require(len(boards) == 288, "independent enumeration failed")
    sources, seen = {}, set()
    for record in records:
        puzzle, solution, entry = record["puzzle"], record["solution"], record["entry"]
        _require(len(puzzle) == len(solution) == 4 and all(len(row) == 4 for row in puzzle + solution),
                 "invalid source board shape")
        _require(all(type(cell) is int and 0 <= cell <= 4 for row in puzzle for cell in row)
                 and all(type(cell) is int and 1 <= cell <= 4 for row in solution for cell in row),
                 "invalid board values")
        matches = [board for board in boards if all(not puzzle[row][column]
                   or puzzle[row][column] == board[row][column] for row in range(4) for column in range(4))]
        _require(len(matches) == 1 and matches[0] == tuple(map(tuple, solution)),
                 f"not exactly one reference completion: {record['episode_id']}")
        _require(_board(entry["question"]) == puzzle and _board(entry["answer"]) == solution
                 and entry["metadata"]["puzzle"] == puzzle and entry["metadata"]["solution"] == solution,
                 "source entry/board mismatch")
        _require(entry["metadata"]["num_empty"] == sum(cell == 0 for row in puzzle for cell in row),
                 "source blank count mismatch")
        answer = "\n".join(" ".join(map(str, row)) for row in solution)
        _require(entry["answer"] == answer and record["a"] == "ACT: " + answer.replace("\n", " ; "),
                 "noncanonical source answer")
        identity = _sha(_encoded(puzzle))
        _require(identity not in seen and record["board_sha256"] == identity, "duplicate/mismatched board hash")
        seen.add(identity)
        _require(record["entry_sha256"] == _sha(_encoded(entry)) and record["q_sha256"] == _sha(record["q"].encode())
                 and record["rendered_q_sha256"] == _sha(record["rendered_q"].encode()), "oracle source hash mismatch")
        _require(entry["question"].strip() in record["q"], "raw q lacks source question")
        sources[record["episode_id"]] = record
    for arm in ("useful", "corrupt"):
        corpus = artifacts[arm + ".json"]["corpus"]
        _require(len(corpus) == 32 and [row["episode_id"] for row in corpus] == list(TRAIN_IDS), "corpus IDs mismatch")
        for index, row in enumerate(corpus):
            source = sources[TRAIN_IDS[index]]
            donor = sources[TRAIN_IDS[index if arm == "useful" else (index+1) % 32]]
            _require(row["q"] == source["q"] and row["rendered_q"] == source["rendered_q"]
                     and row["a"] == donor["a"] and row["spans"] == [
                         [source["rendered_q"], False, "native_context"], [donor["a"], True, "external_oracle_action"]],
                     f"wrong {arm} corpus/source binding")
            if arm == "corrupt":
                _require(any(source["puzzle"][row_index][column] not in (0, donor["solution"][row_index][column])
                             for row_index in range(4) for column in range(4)), "corrupt target satisfies givens")
    return artifacts, sources


def _fit(root, arm, artifacts, inputs, training_seed):
    command = artifacts["trainer_commands.json"]["commands"][arm]
    argv = command["argv"]
    option = lambda name: argv[argv.index(name) + 1]
    remote_adapter = option("--out")
    logical_root = PurePosixPath(remote_adapter).parent.parent
    _require(PurePosixPath(remote_adapter) == logical_root / "training" / f"{arm}_seed{training_seed}",
             "wrong arm adapter destination")
    _require(option("--corpus") == str(logical_root / "material" / f"{arm}.json"), "swapped command corpus")
    pins = artifacts["local_pins.json"]
    _require(option("--model") == pins["model_path"], "command model pin mismatch")
    directory = root / "training" / f"{arm}_seed{training_seed}"
    manifest = inputs.read(directory / "train_manifest.json")
    meta = inputs.read(directory / "train_meta.json")
    adapter_config = inputs.read(directory / "adapter_config.json")
    done = custody._file(directory, "DONE")
    inputs.hashes[str(done)] = custody._digest(done)
    _require(done.read_text().strip() == "ok", "missing training DONE")
    _require(manifest["corpus"]["sha256"] == inputs.hashes[str(root / "material" / f"{arm}.json")]
             and manifest["corpus"]["file"] == PurePosixPath(option("--corpus")).name
             and manifest["corpus"]["n_items"] == 32,
             "fit corpus/arm mismatch")
    config = manifest["config"]
    _require(type(config["seed"]) is int and type(meta["seed"]) is int
             and config["seed"] == meta["seed"] == training_seed,
             "fit/material training seed mismatch")
    for field, flag, convert in (("rank", "--rank", int), ("lr", "--lr", float), ("epochs", "--epochs", int),
                                 ("seed", "--seed", int), ("batch_size", "--batch-size", int),
                                 ("grad_accum", "--grad-accum", int), ("max_len", "--max-len", int)):
        _require(config[field] == convert(option(flag)), f"actual trainer config differs: {field}")
    _require("--no-pack" in argv and config["pack"] is False and config["chat_template"] is False,
             "native span training configuration mismatch")
    _require(config["model"] == manifest["base_model"] == pins["model_path"]
             and adapter_config["base_model_name_or_path"] == pins["model_path"], "fit model pin mismatch")
    _require(adapter_config["r"] == config["rank"]
             and adapter_config["lora_alpha"] == (config["alpha"] or 2*config["rank"]), "adapter shape mismatch")
    _require(manifest["steps"] == meta["steps"] == command["expected_steps"]
             and manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "incomplete actual fit")
    for field in ("rank", "epochs", "lr", "seed"):
        _require(meta[field] == config[field], f"train_meta mismatch: {field}")
    _require(meta["n_texts"] == 32 and meta["tokens"] == manifest["train_tokens_seen"]
             and meta["final_loss"] == manifest["final_loss"], "train_meta accounting mismatch")
    tokens = artifacts["validation.json"][arm + "_tokens"]
    _require(manifest["tokens"]["target"] == sum(row["target_tokens"] for row in tokens)
             and manifest["train_tokens_seen"] == config["epochs"] * sum(row["input_tokens"] for row in tokens),
             "fit token accounting mismatch")
    _require(all(manifest["truncation"][key] == 0 for key in
                 ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")),
             "fit dropped material")
    return remote_adapter, dict(train_manifest=manifest, train_meta=meta, adapter_config=adapter_config)


def audit_run(run_root):
    root = Path(run_root).resolve(strict=True)
    inputs = reducer._Inputs()
    artifacts, sources = _material(root, inputs)
    training_seed = artifacts["validation.json"].get("training_seed", 0)
    _require(type(training_seed) is int and training_seed >= 0, "invalid material training_seed")
    arms, prompt_checks, shared_budget = {}, [], None
    for arm in ("useful", "corrupt"):
        remote_adapter, fit = _fit(root, arm, artifacts, inputs, training_seed)
        directory = root / "training" / f"{arm}_seed{training_seed}"
        spec_path = root / "logs" / arm / "probe_spec.json"
        spec = inputs.read(spec_path)
        _require(spec["adapter_path"] == remote_adapter and spec["model_path"] == artifacts["local_pins.json"]["model_path"]
                 and spec["expected_model_hashes"] == artifacts["local_pins.json"]["files"], "probe spec arm/model mismatch")
        inventory = spec["expected_adapter_hashes"]
        _require({"train_manifest.json", "train_meta.json", "adapter_config.json", "DONE"} <= inventory.keys()
                 and len(WEIGHTS & inventory.keys()) == 1, "incomplete expected adapter inventory")
        missing_weights = {}
        for name, expected in inventory.items():
            _require(custody._sha(expected), "invalid adapter hash")
            if name in WEIGHTS and not (directory / name).exists():
                missing_weights[name] = expected
                continue
            path = custody._file(directory, name)
            actual = custody._digest(path)
            _require(actual == expected, f"expected adapter file mismatch: {arm}/{name}")
            inputs.hashes[str(path)] = actual
        pair = root / "probes" / arm
        started, done = inputs.read(pair / "PAIR_STARTED.json"), inputs.read(pair / "PAIR_DONE.json")
        _require(started["spec"] == spec and started["spec_sha256"] == done["spec_sha256"] == inputs.hashes[str(spec_path)],
                 "probe spec/completion binding mismatch")
        labels = {"PAIR_STARTED": started, "PAIR_DONE": done}
        for condition in ("off", "on"):
            cell = pair / condition
            config = inputs.read(cell / "configuration.json")
            identity = config["source_identity"]
            _require(config["episode_ids"] == spec["episode_ids"] == list(reducer.EPISODE_IDS), "probe IDs mismatch")
            _require(identity["model_input"] == spec["model_path"]
                     and config["hashes_before"]["model"] == spec["expected_model_hashes"], "reported backend model mismatch")
            expected_path = remote_adapter if condition == "on" else None
            _require(identity["adapter_input"] == expected_path, "reported backend adapter/arm mismatch")
            if condition == "on":
                _require(config["hashes_before"]["adapter"] == inventory and
                         identity["adapter_files"] == {name: value for name, value in inventory.items()
                                                       if name in WEIGHTS | {"adapter_config.json"}},
                         "reported adapter hashes mismatch")
            else:
                _require(not identity["adapter_files"] and "adapter" not in config["hashes_before"], "OFF has adapter")
            budget = {field: config[field] for field in BUDGET_FIELDS}
            _require(all(budget[field] == spec[field] for field in BUDGET_FIELDS), "spec/config budget mismatch")
            budget["temperature"] = identity["default_temperature"]
            if shared_budget is None:
                shared_budget = budget
            _require(budget == shared_budget, "unequal token budgets/temperature/maxepisodes")
            requests = [row for row in inputs.read(cell / "generations.jsonl", jsonl=True)
                        if row.get("kind") == "generation_request"]
            for request in requests:
                _require(request["source_identity"]["adapter_input"] == expected_path
                         and request["source_identity"]["model_input"] == spec["model_path"]
                         and request["source_identity"]["adapter_files"] == identity["adapter_files"],
                         "actual generation backend/arm mismatch")
                _require(request["temperature"] == budget["temperature"], "actual generation temperature mismatch")
            for episode_id in reducer.EPISODE_IDS:
                seed = (zlib.crc32(f"{episode_id}/1".encode()) ^ spec["gen_seed"]) & 0x7fffffff
                matches = [request for request in requests if request.get("seeds") == [seed]]
                _require(len(matches) == 1 and len(matches[0]["prompts"]) == 1, "missing/ambiguous first wake request")
                request = matches[0]
                _require(request["max_tokens"] == spec["wake_max_tokens"], "actual wake token budget mismatch")
                actual, expected = request["prompts"][0], sources[episode_id]["q"]
                prompt_checks.append(dict(arm=arm, condition=condition, episode_id=episode_id,
                    request_index=request["request_index"], exact_match=actual == expected,
                    actual_sha256=_sha(actual.encode()), source_q_sha256=_sha(expected.encode()),
                    actual_clock=[line for line in actual.splitlines() if line.startswith("CLOCK:")],
                    source_clock=[line for line in expected.splitlines() if line.startswith("CLOCK:")]))
            labels[condition] = dict(configuration_label=config.get("evidence_label"),
                                    results_label=inputs.read(cell / "results.json").get("evidence_label"))
        arms[arm] = dict(**fit, original_labels=labels, expected_adapter_hashes=inventory,
                         missing_weights=missing_weights,
                         weight_verification="REMOTE_WEIGHT_HASH_NOT_REHASHED_LOCALLY" if missing_weights else "LOCAL_WEIGHT_BYTES_REHASHED")
    analysis = reducer.reduce_pairs(root / "probes/useful", root / "probes/corrupt")
    inputs.verify()
    return dict(schema="mini-sudoku-behavior-run-audit-v1", status="OFFLINE_BINDINGS_VALIDATED",
                training_seed=training_seed,
                independent_material=dict(valid_complete_grids=288, unique_puzzles=48, unique_reference_completions=48),
                arms=arms, prompt_checks=prompt_checks, prompt_mismatch_count=sum(not row["exact_match"] for row in prompt_checks),
                shared_budgets=shared_budget, analysis=analysis, input_sha256=inputs.hashes,
                material_source_hashes=artifacts["source_hashes.json"], model_pins=artifacts["local_pins.json"],
                source_verification="Recorded historical source/model pins retained; historical paths not opened",
                limitations=[f"Descriptive seed-{training_seed} external-oracle diagnostic; no new pass/headroom thresholds.",
                             "Exact raw prompt differences are reported, not excused by a tolerance.",
                             "Missing weight bytes cannot authenticate an adapter; only its recorded remote hash is bound.",
                             "No parenting, clean-lineage, official-origin, or loaded-GPU-state claim."],
                auditor_sha256=custody._digest(__file__))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output-new", required=True)
    args = parser.parse_args(argv)
    output, root = Path(args.output_new).absolute(), Path(args.run_root).resolve(strict=True)
    _require(not output.exists() and not output.is_symlink() and root not in output.resolve().parents,
             "output-new must be new and outside captured root")
    report = audit_run(root)
    with output.open("xb") as target:
        target.write(_encoded(report))
    print(f"RUN_AUDIT_WRITTEN {output}")


if __name__ == "__main__":
    main()
