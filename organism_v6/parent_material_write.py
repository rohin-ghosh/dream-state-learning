"""CPU/tokenizer-only preparation of exploratory sourced-child writer inputs.

Formation judgments are recomputed by parent_material_diagnostic.summarize.
No training, GPU load, clean gate, ancestry eligibility, or execution occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from . import parent_material_diagnostic as formation
from . import preschool_reasoning as policy
from . import train_adapter as trainer


COUNT = 64
RECIPE = "preschool_records_v1"
_PRODUCER_FILES = {
    "organism_v6/parent_material_diagnostic.py",
    "organism_v6/preschool_reasoning.py",
    "organism_v6/batch_loop.py",
    "organism_v6/reasoning_gym_families.json",
}
BOUNDARY = dict(label="EXPLORATORY_SOURCED_CHILD_WRITE_PREPARATION",
                official_base_authentication="UNRESOLVED", model_provenance="LOCAL_HASHES_ONLY",
                clean_lineage=False, admission_certificate=False, training_executed=False)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def _hash(path):
    return formation._hash(path)


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def _invalid(value):
    raise ValueError("invalid JSON constant: " + value)


def _read(path):
    value = json.loads(path.read_bytes(), object_pairs_hook=_object, parse_constant=_invalid)
    _bytes(value)
    return value


def _path(value, *, fresh=False):
    path = Path(value).absolute()
    _require(not any(item.is_symlink() for item in (path, *path.parents)), "symlink path")
    _require(path == path.resolve(), "noncanonical path")
    if fresh:
        if os.path.lexists(path):
            raise FileExistsError("output already exists: " + str(path))
        _require(path.parent.is_dir(), "output parent must exist")
    else:
        _require(path.is_dir(), "missing input directory")
    return path


def _overlap(first, second):
    return first == second or first in second.parents or second in first.parents


def _producer_sources(recorded):
    executing = formation._sources()
    indexed = {}
    for label, inventory in (("recorded", recorded), ("executing", executing)):
        _require(isinstance(inventory, dict), "missing producer source inventory")
        by_relative = {}
        for name, expected in inventory.items():
            _require(isinstance(name, str), "invalid producer source path")
            path = Path(name)
            relative = "/".join(path.parts[-2:])
            _require(path.is_absolute() and path == path.resolve()
                     and relative in _PRODUCER_FILES, "unsupported producer source path")
            _require(relative not in by_relative, "ambiguous producer source identity")
            _require(path.is_file() and not path.is_symlink(), "missing " + label + " producer source")
            _require(_hash(path) == expected, "formation source code changed: " + label + " bytes")
            by_relative[relative] = dict(path=name, sha256=expected)
        _require(set(by_relative) == _PRODUCER_FILES, "incomplete producer source inventory")
        indexed[label] = by_relative
    files = {}
    for relative in sorted(_PRODUCER_FILES):
        original, current = indexed["recorded"][relative], indexed["executing"][relative]
        _require(original["sha256"] == current["sha256"], "formation source code changed across checkouts")
        files[relative] = dict(recorded_path=original["path"], executing_path=current["path"],
                               sha256=original["sha256"])
    return dict(recorded=recorded, executing=executing, files=files)


def _formation_snapshot(out):
    artifact_path = out / "artifact_hashes.json"
    _require(artifact_path.is_file() and not artifact_path.is_symlink(), "missing formation artifact hashes")
    manifest = _read(artifact_path)
    files = manifest.get("files")
    required = {"config.json", "local_base_pins.json", "base_after.json", "results.json",
                "schedule.json", "ledger.jsonl", "lesson_deliveries.jsonl", "generations.jsonl",
                "teaching_dose.json"}
    _require(isinstance(files, dict) and required <= files.keys(), "incomplete formation")
    _require(not any("failure" in name or name.startswith("partial_") or name == "base_after_error.json"
                     for name in files), "failed formation is not writable material")
    _require({path.name for path in out.iterdir()} == set(files) | {"artifact_hashes.json"},
             "formation artifact inventory changed")
    for name, expected in files.items():
        _require(isinstance(name, str) and name not in ("", ".", "..", "artifact_hashes.json")
                 and "/" not in name and "\\" not in name, "unsafe formation artifact name")
        path = out / name
        _require(path.is_file() and not path.is_symlink() and _hash(path) == expected,
                 "formation artifact hash mismatch: " + name)
    config = _read(out / "config.json")
    _require(config.get("mode") in ("lesson", "sham") and config.get("out") == str(out),
             "formation configuration mismatch")
    _require(all(config.get(key) == value for key, value in formation.BOUNDARY.items()),
             "formation provenance boundary mismatch")
    configured_protocol = formation.protocol(config.get("schedule_seed", 6101), config.get("generation_seed", 7101))
    _require(_bytes(config.get("protocol")) == _bytes(configured_protocol), "formation protocol changed")
    producer_sources = _producer_sources(config.get("source_hashes"))
    gym = formation.ReasoningGymGym(require_package=False, strict_verifier=True)
    schedule = _read(out / "schedule.json")
    _require(schedule == gym.training_schedule(64, configured_protocol["schedule_seed"]), "formation training schedule mismatch")
    model = Path(config["model_path"])
    _require(model.is_absolute() and str(model.resolve(strict=True)) == str(model), "noncanonical local model")
    pins = _read(out / "local_base_pins.json")
    after = _read(out / "base_after.json")
    _require(pins.get("model_path") == after.get("model_path") == str(model)
             and after.get("unchanged") is True
             and config.get("expected_files") == pins.get("files") == after.get("files")
             == formation.local_files(model), "local model pins changed")
    result = _read(out / "results.json")
    recomputed = dict(status="COMPLETE", mode=config["mode"], **formation.summarize(out))
    _require(_bytes(result) == _bytes(recomputed), "formation results disagree with source recomputation")
    return dict(config=config, result=result, local_pins=pins, schedule=schedule,
                producer_sources=producer_sources,
                artifact_hashes=files, artifact_manifest_sha256=_hash(artifact_path))


def _select(out, snapshot):
    raw_lines, rows = policy._lines((out / "ledger.jsonl").read_bytes())
    judgments = snapshot["result"]["judgments"]
    selected = [row for row in judgments if row.get("unique_grounded") is True]
    selected.sort(key=lambda row: row["record_line"])
    _require(len(selected) == snapshot["result"]["n_unique_grounded_records"], "formation unique count mismatch")
    if len(selected) < COUNT:
        return None, []
    items, bindings = [], []
    for judgment in selected[:COUNT]:
        record_index, source_index = judgment["record_line"], judgment["source_line"]
        _require(type(record_index) is int and type(source_index) is int
                 and 0 <= source_index < record_index < len(rows), "invalid formation source indexes")
        record, source = rows[record_index], rows[source_index]
        _require(record["kind"] == "note_after" and source["kind"] == "act"
                 and record["execution_id"] == source["execution_id"] == judgment["execution_id"],
                 "not an actual child record/source pair")
        _require(record["episode_id"] == source["episode_id"] and isinstance(record.get("text"), str),
                 "child record identity mismatch")
        _require(record["episode_id"] in snapshot["schedule"], "record outside formation training schedule")
        item = policy.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"])
        trainer.child_record_prefix_length(item)
        items.append(item)
        bindings.append(dict(corpus_index=len(items) - 1, record_line=record_index,
            source_line=source_index, line_index_base=0, episode_id=record["episode_id"],
            execution_id=record["execution_id"], record_sha256=hashlib.sha256(raw_lines[record_index]).hexdigest(),
            source_sha256=hashlib.sha256(raw_lines[source_index]).hexdigest(),
            child_text_sha256=hashlib.sha256(record["text"].encode()).hexdigest(),
            corpus_item_sha256=hashlib.sha256(item.encode()).hexdigest()))
    _require(len({policy._copy_key(rows[row["record_line"]]["text"]) for row in bindings}) == COUNT,
             "duplicate selected child text")
    return dict(recipe=RECIPE, corpus=items, principles=[], n_new=COUNT, n_dropped_legacy=0), bindings


def _load_tokenizer(model_path):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(model_path, local_files_only=True)


def tokenizer_preflight(corpus, tokenizer):
    """Use the trainer's actual prefix/mask/count functions, with no truncation."""
    _require(isinstance(corpus, dict) and corpus.get("recipe") == RECIPE
             and isinstance(corpus.get("corpus"), list) and len(corpus["corpus"]) == COUNT,
             "exact child-only recipe and 64 rows required")
    _require(all(isinstance(text, str) and text.startswith("Situation ") for text in corpus["corpus"]),
             "unchanged Situation child records required")
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    rows = []
    for start in range(0, COUNT, 4):
        texts = corpus["corpus"][start:start + 4]
        encoded = tokenizer(texts, padding=True, truncation=False,
                            return_offsets_mapping=True, return_attention_mask=True)
        _require(all(len(encoded[field]) == len(texts)
                     for field in ("input_ids", "attention_mask", "offset_mapping")), "tokenizer batch mismatch")
        for offset, text in enumerate(texts):
            token_ids = encoded["input_ids"][offset]
            attention = encoded["attention_mask"][offset]
            positions = encoded["offset_mapping"][offset]
            _require(0 < len(token_ids) <= 512 and len(token_ids) == len(attention) == len(positions),
                     "tokenizer row exceeds 512 tokens or has invalid lengths; no truncation allowed")
            prefix = trainer.child_record_prefix_length(text)
            mask = trainer.child_target_mask(positions, prefix, attention)
            labels = [token if keep else -100 for token, keep in zip(token_ids, mask)]
            counts = trainer.child_label_counts(positions, prefix, attention, labels)
            rows.append(dict(corpus_index=start + offset, input_tokens=sum(attention),
                             padded_input_tokens=len(token_ids), prefix_characters=prefix, **counts))
    supervised = sum(row["supervised_child_tokens"] for row in rows)
    tokens = sum(row["input_tokens"] for row in rows)
    return dict(rows=rows, tokenizer_class=type(tokenizer).__name__, max_input_tokens=512,
                truncation=False, batch_size=4, examples=COUNT, steps=48,
                supervised_child_tokens_per_epoch=supervised, input_tokens_per_epoch=tokens,
                expected_supervised_tokens=supervised * 3, expected_tokens=tokens * 3,
                expected_masked_nonpadding_tokens=(tokens - supervised) * 3,
                token_budget_equivalence="NOT_ASSERTED; equal examples/steps, report actual child tokens")


def prepare_write(formation_out, output_dir, *, adapter_dir, trainer_log, python_executable=None):
    """Prepare fixed first64 source-grounded rows and a command; never execute it."""
    source = _path(formation_out)
    output = _path(output_dir, fresh=True)
    adapter = _path(adapter_dir, fresh=True)
    log = _path(trainer_log, fresh=True)
    snapshot = _formation_snapshot(source)
    formation_seeds = {name: snapshot["config"]["protocol"][name] for name in ("schedule_seed", "generation_seed")}
    model = Path(snapshot["config"]["model_path"])
    destinations = (output, adapter, log)
    _require(all(not _overlap(path, protected) for path in destinations for protected in (source, model))
             and all(not _overlap(path, other) for index, path in enumerate(destinations)
                     for other in destinations[index + 1:]), "preparation/training/log paths overlap inputs or each other")
    executable = Path(python_executable or sys.executable).absolute()
    _require(executable.is_file() and os.access(executable, os.X_OK), "existing Python executable required")
    source_hashes = {str(Path(module.__file__).resolve()): _hash(Path(module.__file__))
                     for module in (formation, policy, trainer)}
    source_hashes[str(Path(__file__).resolve())] = _hash(Path(__file__))
    corpus, bindings = _select(source, snapshot)
    ready = corpus is not None
    tokenization = tokenizer_preflight(corpus, _load_tokenizer(str(model))) if ready else None
    artifacts = {
        "formation_inputs.json": dict(**BOUNDARY, formation_out=str(source),
            formation_seeds=formation_seeds,
            artifact_manifest_sha256=snapshot["artifact_manifest_sha256"],
            artifact_hashes=snapshot["artifact_hashes"], source_hashes=snapshot["config"]["source_hashes"],
            producer_sources=snapshot["producer_sources"]),
        "local_base_pins.json": dict(**BOUNDARY, model_path=str(model), files=snapshot["local_pins"]["files"]),
        "source_hashes.json": dict(**BOUNDARY, files=source_hashes),
        "source_map.json": dict(**BOUNDARY, formation_out=str(source),
            ledger_sha256=snapshot["artifact_hashes"]["ledger.jsonl"],
            results_sha256=snapshot["artifact_hashes"]["results.json"],
            selection="first64 unique_grounded in physical ledger order; no ranking", records=bindings),
    }
    metadata_checks = None
    if ready:
        corpus_hash = hashlib.sha256(_bytes(corpus)).hexdigest()
        metadata_checks = dict(recipe="v1_frozen_child_target_seeded", source_recipe=RECIPE,
            loss_target="child_body_only", source_corpus_sha256=corpus_hash,
            n_texts=COUNT, steps=48, rank=8, epochs=3, lr=1e-4, seed=6102,
            supervised_tokens=tokenization["expected_supervised_tokens"],
            tokens=tokenization["expected_tokens"],
            masked_nonpadding_tokens=tokenization["expected_masked_nonpadding_tokens"])
        artifacts.update({"corpus.json": corpus, "tokenizer_preflight.json": dict(**BOUNDARY, **tokenization),
            "training_command.json": dict(**BOUNDARY, shell=False,
                argv=[str(executable), "-B", "-m", "organism_v6.train_adapter", "--corpus", str(output / "corpus.json"),
                      "--out", str(adapter), "--rank", "8", "--epochs", "3", "--lr", "1e-4", "--seed", "6102"],
                cwd=str(Path(__file__).resolve().parents[1]),
                env={"V6_MODEL": str(model), "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
                stdout_path=str(log), stderr="STDOUT", stdout_open_mode="xb",
                execution_preconditions=["recheck formation, prep and local input hashes",
                    "adapter and trainer log must still not exist", "caller reserves an explicit GPU"],
                omitted_arguments=["--gate-receipt", "--expected-gate-sha256",
                                   "--previous-manifest-sha256", "--trainer-receipt"])})
    report = dict(**BOUNDARY, status="READY" if ready else "SKIPPED_INSUFFICIENT_MATERIAL",
        formation_out=str(source), mode=snapshot["config"]["mode"], formation_seeds=formation_seeds, required_records=COUNT,
        available_unique_grounded=snapshot["result"]["n_unique_grounded_records"],
        selected_records=len(bindings), retry_policy="no retries, lowered count, or alternate selection",
        adapter_dir=str(adapter), trainer_log=str(log), metadata_equals=metadata_checks,
        post_training_requirements=["DONE exists and EMPTY_CORPUS absent", "finite final_loss",
            "all metadata_equals values match actual train_meta.json", "record actual adapter config/weight hashes",
            "standalone completion is not a gate, lineage certificate, or learning result"],
        training_receipt="NOT_EMITTED; standalone trainer metadata only",
        token_budget_equivalence="NOT_ASSERTED")
    artifacts["write_prep.json"] = report
    _require(_bytes(_formation_snapshot(source)) == _bytes(snapshot), "formation changed during preparation")
    _require(all(_hash(Path(path)) == digest for path, digest in source_hashes.items()), "writer source changed")
    for path in destinations:
        _path(path, fresh=True)
    output.mkdir()
    for name, value in artifacts.items():
        formation._write(output / name, value)
    formation._write(output / "artifact_hashes.json", dict(**BOUNDARY,
        files={name: _hash(output / name) for name in artifacts}))
    output.chmod(0o555)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formation-out", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--adapter-out", required=True)
    parser.add_argument("--trainer-log", required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    print(json.dumps(prepare_write(args.formation_out, args.out, adapter_dir=args.adapter_out,
        trainer_log=args.trainer_log, python_executable=args.python), sort_keys=True))


if __name__ == "__main__":
    main()
