"""CPU-only paired child-corpus preparation from revalidated coached replay.

No replay, training, GPU launch, formation certificate or H1 claim is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys

from . import parent_note_replay_diagnostic as replay
from . import parent_material_write as writer


ARMS = replay.ARMS
COUNT = writer.COUNT
BOUNDARY = dict(writer.BOUNDARY, label="EXPLORATORY_COACHED_REPLAY_CHILD_WRITE_PREPARATION",
                source_kind="historical_source_coached_replay", new_world_actions=0,
                eligibility_certificate=False, h1_claim=False,
                interpretation="Shared coached replay; original teacher dose confounded; not clean/H1")


def _select(checked, raw_records, arm):
    records = {row["source_id"]: (index, row) for index, row in enumerate(checked["records"])
               if row["arm"] == arm}
    writer._require(len(records) == replay.COUNT, "missing or duplicate replay source records")
    seen, items, bindings = set(), [], []
    for source_index, source in enumerate(checked["sources"][arm]["sources"]):
        writer._require(source["source_id"] in records, "missing replay source record")
        record_index, record = records[source["source_id"]]
        if record["judgment"]["faithful"] is not True:
            continue
        key = writer.policy._copy_key(record["text"])
        if key in seen:
            continue
        seen.add(key)
        if len(items) == COUNT:
            continue
        item = writer.policy.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"])
        writer.trainer.child_record_prefix_length(item)
        items.append(item)
        bindings.append(dict(corpus_index=len(items) - 1, replay_record_line=record_index,
            replay_record_sha256=hashlib.sha256(raw_records[record_index]).hexdigest(),
            replay_source_index=source_index, source_id=source["source_id"], output_id=record["output_id"],
            episode_id=record["episode_id"], execution_id=record["execution_id"], line_index_base=0,
            source_act_line=source["act_line"], source_act_sha256=source["act_sha256"],
            old_note_line=source["old_note_line"], old_note_sha256=source["old_note_sha256"],
            original_note_trace=source["note_trace"], original_wake_trace=source["wake_trace"],
            child_text_sha256=record["output_sha256"], corpus_item_sha256=hashlib.sha256(item.encode()).hexdigest()))
    available = len(seen)
    writer._require(available == checked["results"]["arms"][arm]["unique_faithful"],
                    "revalidated unique faithful count mismatch")
    corpus = dict(recipe=writer.RECIPE, corpus=items, principles=[], n_new=COUNT, n_dropped_legacy=0)
    return corpus, bindings, available


def prepare_write(replay_out, output_dir, *, adapter_dirs, trainer_logs, python_executable=None):
    """Bind both first64 child corpora or a paired skip; never execute the argv."""
    writer._require(set(adapter_dirs) == set(trainer_logs) == set(ARMS), "both arm destinations required")
    source = writer._path(replay_out)
    output = writer._path(output_dir, fresh=True)
    adapters = {arm: writer._path(adapter_dirs[arm], fresh=True) for arm in ARMS}
    logs = {arm: writer._path(trainer_logs[arm], fresh=True) for arm in ARMS}
    inventory = replay._inventory(source)
    config = writer._read(source / "config.json")
    model = writer._path(config["model_path"])
    destinations = [output, *adapters.values(), *logs.values()]
    protected = [source, model, *[writer._path(config["source_roots"][arm]) for arm in ARMS]]
    writer._require(all(not writer._overlap(path, other) for path in destinations for other in protected)
                    and all(not writer._overlap(path, other) for index, path in enumerate(destinations)
                            for other in destinations[index + 1:]), "destinations overlap inputs or each other")
    executable = Path(python_executable or sys.executable).absolute()
    writer._require(executable.is_file() and os.access(executable, os.X_OK), "existing Python executable required")
    modules = (sys.modules[__name__], writer, writer.trainer)
    source_hashes = {str(Path(module.__file__).resolve()): writer._hash(Path(module.__file__)) for module in modules}
    tokenizer = writer._load_tokenizer(str(model))
    checked = replay.validate_replay(source, tokenizer=tokenizer)
    raw_records, records = writer.policy._lines((source / "records.jsonl").read_bytes())
    writer._require(records == checked["records"], "raw replay records changed after revalidation")
    selected = {arm: _select(checked, raw_records, arm) for arm in ARMS}
    ready = all(selected[arm][2] >= COUNT for arm in ARMS)
    inputs = dict(**BOUNDARY, replay_out=str(source), replay_inventory=inventory,
        coach_sha256=config["coach_sha256"], replay_implementation=config["implementation"],
        sources={arm: dict(root=checked["sources"][arm]["root"],
                           inventory=checked["sources"][arm]["inventory"]) for arm in ARMS})
    artifacts = {
        "replay_inputs.json": inputs,
        "local_base_pins.json": dict(**BOUNDARY, model_path=str(model), files=config["model_pins"]),
        "source_hashes.json": dict(**BOUNDARY, files=source_hashes),
    }
    reports = {}
    for arm in ARMS:
        corpus, bindings, available = selected[arm]
        arm_artifacts = {
            "source_map.json": dict(**BOUNDARY, arm=arm, replay_out=str(source),
                replay_records_sha256=inventory["files"]["records.jsonl"],
                replay_sources_sha256=inventory["files"][arm + "_sources.json"],
                original_source=inputs["sources"][arm],
                selection="first64 normalized-unique faithful in validated physical source order; no ranking",
                records=bindings if ready else []),
        }
        metadata = None
        if ready:
            tokenization = writer.tokenizer_preflight(corpus, tokenizer)
            corpus_hash = hashlib.sha256(writer._bytes(corpus)).hexdigest()
            metadata = dict(recipe="v1_frozen_child_target_seeded", source_recipe=writer.RECIPE,
                loss_target="child_body_only", source_corpus_sha256=corpus_hash, n_texts=COUNT,
                steps=48, rank=8, epochs=3, lr=1e-4, seed=6102,
                supervised_tokens=tokenization["expected_supervised_tokens"],
                tokens=tokenization["expected_tokens"],
                masked_nonpadding_tokens=tokenization["expected_masked_nonpadding_tokens"])
            arm_artifacts.update({"corpus.json": corpus,
                "tokenizer_preflight.json": dict(**BOUNDARY, **tokenization),
                "training_command.json": dict(**BOUNDARY, shell=False,
                    argv=[str(executable), "-B", "-m", "organism_v6.train_adapter", "--corpus",
                          str(output / arm / "corpus.json"), "--out", str(adapters[arm]),
                          "--rank", "8", "--epochs", "3", "--lr", "1e-4", "--seed", "6102"],
                    cwd=str(Path(__file__).resolve().parents[1]),
                    env={"V6_MODEL": str(model), "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
                    stdout_path=str(logs[arm]), stderr="STDOUT", stdout_open_mode="xb",
                    execution_preconditions=["main revalidates replay, original source, prep, code and local model hashes",
                        "both arms READY; all adapters and trainer logs still absent",
                        "main owns explicit GPU reservation and downstream parent-free probes"])})
        reports[arm] = dict(**BOUNDARY, status="READY" if ready else "PAIRED_SKIP_INSUFFICIENT_MATERIAL",
            arm=arm, required_records=COUNT, available_unique_faithful=available,
            selected_records=COUNT if ready else 0, adapter_dir=str(adapters[arm]), trainer_log=str(logs[arm]),
            metadata_equals=metadata, token_budget_equivalence="NOT_ASSERTED; report actual child tokens",
            post_training_requirements=["DONE exists and EMPTY_CORPUS absent", "finite final_loss",
                "actual train_meta.json matches metadata_equals", "record actual adapter config/weight hashes",
                "parent-free probes downstream; standalone completion is not learning or a clean/H1 result"])
        arm_artifacts["write_prep.json"] = reports[arm]
        artifacts.update({arm + "/" + name: value for name, value in arm_artifacts.items()})
    report = dict(**BOUNDARY, status="READY" if ready else "PAIRED_SKIP_INSUFFICIENT_MATERIAL",
        replay_out=str(source), required_records_per_arm=COUNT, reports=reports,
        retry_policy="no retries, lowered count, alternate selection or child-text repair",
        training_receipt="NOT_EMITTED; preparation only")
    artifacts["write_prep.json"] = report
    writer._require(writer._bytes(replay.validate_replay(source, tokenizer=tokenizer)) == writer._bytes(checked)
                    and replay._inventory(source) == inventory, "replay/source changed during preparation")
    writer._require(all(writer._hash(Path(path)) == digest for path, digest in source_hashes.items()),
                    "writer source changed during preparation")
    for path in destinations:
        writer._path(path, fresh=True)
    output.mkdir()
    for arm in ARMS:
        (output / arm).mkdir()
    for name, value in artifacts.items():
        writer.formation._write(output / name, value)
    writer.formation._write(output / "artifact_hashes.json", dict(**BOUNDARY,
        files={name: writer._hash(output / name) for name in artifacts}))
    for arm in ARMS:
        (output / arm).chmod(0o555)
    output.chmod(0o555)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-out", required=True)
    parser.add_argument("--out", required=True)
    for arm in ARMS:
        parser.add_argument("--" + arm + "-adapter-out", required=True)
        parser.add_argument("--" + arm + "-trainer-log", required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    report = prepare_write(args.replay_out, args.out,
        adapter_dirs={arm: getattr(args, arm + "_adapter_out") for arm in ARMS},
        trainer_logs={arm: getattr(args, arm + "_trainer_log") for arm in ARMS}, python_executable=args.python)
    print(writer._bytes(report).decode(), end="")


if __name__ == "__main__":
    main()
