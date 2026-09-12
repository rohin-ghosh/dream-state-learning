"""CPU-only, one-event material-utility preparation; never fit or launch.

Main's 2026-09-12 scope: unchanged sham1850124 Scratchpad versus its exact
own ACT line, 32 explicit replays, three epochs, recipient seeds 0/1/2.
Both use the original FIRST-Scratchpad prompt minus its exact sham package.
The public failed-action feedback stays; no wake2 context is exported.
No parenting advantage, clean lineage, reflection-truth or admission claim.

Run with --source-arm SHAM --capsule TERMINAL.tgz --model-path LOCAL_BASE
--out FRESH_PREPARATION --recipient-root FRESH_RECIPIENT_ROOT. Requires the
actual local tokenizer; emits six command specifications but executes none.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import os
from pathlib import Path
import re
import sys

from . import parent_correction_diagnostic as correction
from . import parent_material_write as writer
from . import train_adapter_v3 as trainer
from .mini_sudoku_behavior_material import board_from_text, validate_solution


ARMS = ("whole_raw", "act_only")
SEEDS = (0, 1, 2)
REPLAYS = 32
EPOCHS = 3
MAX_LEN = 4096
EPISODE = "rg/mini_sudoku/1850124"
REQUIRED_PRODUCER_FILES = frozenset({
    "organism_v6/parent_correction_diagnostic.py",
    "organism_v6/parent_competency_diagnostic.py",
    "organism_v6/parent_material_diagnostic.py",
    "organism_v6/parent_material_write.py",
    "organism_v6/preschool_reasoning.py",
    "organism_v6/batch_loop.py",
    "organism_v6/mini_sudoku_behavior_material.py",
})
APPROVED = dict(
    capsule_sha256="bd4f7c5d035f423f27c262efbb17cc90bcab57cb30a45d894f7b3c98db65dd5b",
    inventory_sha256="850737c966b88244588178ac4e9667928a847e87605d84e569d5ae871cee1887",
    scratchpad_sha256="2bb4313d7faf713090143fb8b79148422295aee3610b63c15437666983d2587d",
    scratchpad_bytes=236,
    prompt_sha256="1095ebeed0db237d7c6e9afd749db807608420206f784b674a2451d6e40e1694",
    act_sha256="74887f842a07dd4e8e0992ecdc50d903859be33e5684c4709bdf5ceb4c084575",
    act_bytes=42,
    wake2_sha256="6f2f29a8e69deb1ae474560496c89ef8fe76df1f8be382d0ca1102c5da69776b",
    synthetic=False,
)
BOUNDARY = dict(
    scope="MAIN_SELECTED_ONE_EVENT_MATERIAL_UTILITY_DEV_2026_09_12",
    source_role="DEVELOPMENT_TRAINING_EXPERIENCE", source_teacher_exposed=True,
    parenting_advantage=False, clean_lineage=False, training_executed=False,
    admission_certificate=False, launch_authorized=False, formal_C11="DEFERRED",
    official_model_origin="UNRESOLVED_LOCAL_HASHES_ONLY", reflection_truth="NOT_ASSERTED",
    useful_training="NOT_ASSERTED", H1_claim=False, P1_claim=False,
)
require = writer._require
sha = correction.sha


def implementation_pins():
    modules = (sys.modules[__name__], correction, correction.packages, writer,
               correction.formation, correction.policy, correction.batch_loop,
               sys.modules[board_from_text.__module__], trainer)
    return {str(Path(module.__file__).resolve()): writer._hash(Path(module.__file__)) for module in modules}


def check_source(source, capsule):
    config = writer._read(source / "config.json")
    require(config["mode"] == "sham", "only the approved sham candidate; process false diagnosis excluded")
    require(config["synthetic"] is APPROVED["synthetic"], "native source required")
    require(writer._hash(capsule) == APPROVED["capsule_sha256"], "approved capsule hash drift")
    inventory = correction.verify_inventory(source)
    require(inventory == APPROVED["inventory_sha256"], "approved source inventory drift")
    require(config["schema"] == "fresh-parent-correction-v1" and config["boundary"] == correction.BOUNDARY
            and config["protocol"] == correction.PROTOCOL and config["packages"] == correction.packages.PACKAGES,
            "source protocol/boundary drift")
    root = Path(__file__).resolve().parents[1]
    sources = {}
    for name, expected in config["sources"].items():
        if "/organism_v6/" not in name:
            continue
        relative = "organism_v6/" + name.split("/organism_v6/", 1)[1]
        if relative not in REQUIRED_PRODUCER_FILES:
            continue
        local = (root / relative).resolve()
        require(local.is_relative_to(root / "organism_v6") and relative not in sources,
                "ambiguous producer source")
        require(local.is_file() and writer._hash(local) == expected, "pinned producer source drift: " + relative)
        sources[relative] = dict(recorded_path=name, local_path=str(local), sha256=expected)
    require(set(sources) == REQUIRED_PRODUCER_FILES, "missing required CPU replay/material source pin")
    result = writer._read(source / "results.json")
    require(result["status"] == "COMPLETE" and result["mode"] == "sham", "source not terminal sham")
    return config, dict(root=str(source), inventory_sha256=inventory,
        capsule_path=str(capsule), capsule_sha256=APPROVED["capsule_sha256"],
        files=writer._read(source / "artifact_hashes.json")["files"], producer_sources=sources,
        producer_pin_scope="REQUIRED_CPU_REPLAY_AND_MATERIAL_PRIMITIVES_ONLY",
        current_checkout_identity_asserted=False,
        unrelated_recorded_sources_revalidated=False)


def teacher_echo(text):
    if correction.policy._teacher_echo(text):
        return True
    normalized = " " + correction.policy._copy_key(text) + " "
    for package in correction.packages.PACKAGES.values():
        for part in (package, *package.splitlines(), *re.split(r"(?<=[.!?])\s+", package)):
            fragment = correction.policy._copy_key(part)
            if fragment and " " + fragment + " " in normalized:
                return True
    return False


def strip_teacher(prompt):
    package = correction.packages.PACKAGES["sham"]
    header = "=== A NOTE FROM YOUR TEACHER ==="
    require(prompt.count(package) == 1 and prompt.count(header) == 1, "exact single sham package required")
    start = prompt.index(package)
    end = start + len(package)
    context = prompt[:start] + prompt[end:]
    require(not teacher_echo(context) and header not in context, "teacher residue in exported context")
    start_byte, end_byte = len(prompt[:start].encode()), len(prompt[:end].encode())
    return context, dict(operation="DELETE_EXACT_PACKAGE_ONLY_NO_OTHER_REWRITE",
        start_byte=start_byte, end_byte=end_byte, removed_sha256=sha(package.encode()),
        retained_byte_ranges=[[0, start_byte], [end_byte, len(prompt.encode())]],
        original_prompt_sha256=sha(prompt.encode()), context_sha256=sha(context.encode()))


def raw_span(capture, pointer, start, end):
    raw = capture["text"].encode()
    selected = raw[start:end]
    require(0 <= start < end <= len(raw), "invalid raw source span")
    return dict(file="captures.json", field=pointer, request_index=capture["request_index"],
        output_sha256=sha(raw), prompt_sha256=capture["prompt_sha256"], start_byte=start,
        end_byte=end, span_sha256=sha(selected), bytes=len(selected),
        offset_convention="UTF8_ZERO_BASED_HALF_OPEN_IN_DECODED_RAW_FIELD")


def select_event(source):
    records = writer._read(source / "captures.json")
    reduction = correction.reduce_captures(records)
    selected = [(index, row) for index, row in enumerate(records) if row["episode_id"] == EPISODE]
    require(len(selected) == 1 and any(row["episode_id"] == EPISODE for row in reduction["candidates"]),
            "approved event is not a qualifying correction")
    index, record = selected[0]
    first, second = record["wakes"]
    scratch = record["scratchpads"][0]["capture"]
    raw = scratch["text"].encode()
    require(len(raw) == APPROVED["scratchpad_bytes"] and sha(raw) == APPROVED["scratchpad_sha256"],
            "approved whole raw Scratchpad drift")
    require(scratch["prompt_sha256"] == APPROVED["prompt_sha256"], "approved first-Scratchpad prompt drift")
    scratch_spans = correction.raw_act_spans(scratch["text"])
    wake2 = second["generation"]
    wake2_raw = wake2["text"].encode()
    spans = correction.raw_act_spans(wake2["text"])
    require(len(spans) == len(scratch_spans) == 1, "one exact own ACT line per source required")
    span = spans[0]
    require(sha(wake2_raw) == APPROVED["wake2_sha256"], "approved whole wake2 generation drift")
    require(span["start_byte"] == 0 and span["end_byte"] == APPROVED["act_bytes"]
            and wake2_raw[span["end_byte"]:span["end_byte"] + 1] == b"\n",
            "ACT-only must be exact wake2 0:42 line with newline boundary, not whole wake2")
    action = wake2_raw[span["start_byte"]:span["end_byte"]].decode()
    require(len(action.encode()) == APPROVED["act_bytes"] and sha(action.encode()) == APPROVED["act_sha256"],
            "approved exact ACT bytes drift")
    require(span["action"] == scratch_spans[0]["action"] == second["actions"][0]["action"],
            "Scratchpad/wake2 correct-board join")
    puzzle = board_from_text(record["question"], question=True)
    validate_solution(puzzle, board_from_text(span["action"]))
    facts = correction.policy.facts_from_act(first["actions"][0])
    suffix = "\n\n" + correction.policy.outcome_block(facts, "Scratchpad")
    require(scratch["prompt"] == first["generation"]["prompt"].rstrip("\n") + suffix,
            "only original first-Scratchpad public-feedback context")
    context, deletion = strip_teacher(scratch["prompt"])
    require(context.endswith(suffix) and record["question"] in context, "lost source public question/feedback")
    require(action not in context and span["action"] not in context and scratch["text"] not in context
            and "[Scratchpad from " not in context and "CLOCK: chunk 2/2" not in context,
            "answer-bearing or wake2 context forbidden")
    require(all(not teacher_echo(text) for text in (scratch["text"], action)), "teacher lesson in own target")
    pointer = f"/{index}/scratchpads/0/capture/text"
    targets = dict(whole_raw=scratch["text"], act_only=action)
    mapping = dict(episode_id=EPISODE, occurrence_id=record["occurrence_id"],
        execution_id=first["actions"][0]["execution_id"],
        source_event_id=record["occurrence_id"] + "/correction",
        unique_events_unit="ONE_SOURCE_CORRECTION_TRAJECTORY_NOT_32_INDEPENDENT_EVENTS",
        scratchpad_execution_id=first["actions"][0]["execution_id"],
        wake2_execution_id=second["actions"][0]["execution_id"],
        capture_index=index, capture_sha256=sha(correction.policy._encoded(record)),
        question_sha256=record["question_sha256"], source_role=correction.BOUNDARY["role"],
        source_teacher_exposed=True, context=dict(file="captures.json", field=f"/{index}/scratchpads/0/capture/prompt",
            request_index=scratch["request_index"], **deletion),
        targets=dict(whole_raw=raw_span(scratch, pointer, 0, len(raw)),
                     act_only=raw_span(wake2, f"/{index}/wakes/1/generation/text", 0, span["end_byte"])),
        act_corroboration=raw_span(scratch, pointer, scratch_spans[0]["start_byte"], scratch_spans[0]["end_byte"]))
    return context, targets, mapping, reduction


def make_corpus(context, target, arm, mapping):
    items = [dict(spans=[[context, False, "context"], [target, True, "own_output"]],
        group=mapping["source_event_id"], view=arm, category="own_output", order=index,
        meta=dict(source_event_id=mapping["source_event_id"], unique_events=1,
                  replay_index=index, explicit_replays=REPLAYS, source_sha256=mapping["targets"][arm]["span_sha256"]))
        for index in range(REPLAYS)]
    return dict(recipe=trainer.RECIPE, corpus=items, unique_events=1, explicit_replays=REPLAYS,
        n_new_source_events=0, epochs=EPOCHS, total_event_presentations=REPLAYS * EPOCHS,
        token_matched=False, boundary=BOUNDARY)


def tokenizer_preflight(corpus, tokenizer):
    items = trainer.normalize_items(corpus)
    require(len(items) == REPLAYS and len({item["group"] for item in items}) == 1, "one event, 32 replays required")
    require(getattr(tokenizer, "eos_token_id", None) is not None, "actual tokenizer EOS required")
    padding = tokenizer.pad_token_id if getattr(tokenizer, "pad_token_id", None) is not None else tokenizer.eos_token_id
    evidence = []
    for index, item in enumerate(items):
        context, loss, _category = item["spans"][0]
        target, target_loss, _category = item["spans"][1]
        require(loss is False and target_loss is True, "context must be zero loss; own target must carry loss")
        rendered = tokenizer.apply_chat_template([dict(role="user", content=context.rstrip("\n"))],
            tokenize=False, add_generation_prompt=True)
        require(not teacher_echo(rendered), "teacher lesson in rendered context")
        context_ids = tokenizer.encode(rendered, add_special_tokens=False)
        target_ids = tokenizer.encode(target, add_special_tokens=False)
        require(context_ids and target_ids and all(type(token) is int for token in context_ids + target_ids),
                "actual integer token IDs required")
        require(tokenizer.decode(target_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == target,
                "raw target token roundtrip changed bytes")
        expected_target = target_ids + [tokenizer.eos_token_id]
        expected_ids = context_ids + expected_target
        require(len(expected_ids) <= MAX_LEN, "no-truncation context plus complete target exceeds 4096")
        encoded = trainer.encode_item_segments(item, tokenizer, MAX_LEN, chat_template=True,
            add_eos=True, item_index=index, overflow="split")
        require(len(encoded) == 1 and encoded[0].n_splits == 1 and not encoded[0].context_dropped
                and not encoded[0].target_dropped, "V3 split/truncation forbidden")
        segment = encoded[0]
        labels = [trainer.IGNORE] * len(context_ids) + expected_target
        require(segment.ids == expected_ids and segment.labels == labels, "real V3 encoded target labels changed")
        batch = trainer.collate([[segment]], pad_id=padding)
        require(batch["input_ids"] == [expected_ids] and batch["labels"] == [labels]
                and batch["n_target"] == len(expected_target), "real V3 collate masked or changed target labels")
        require(all(label == token for token, label in zip(batch["input_ids"][0][1:], batch["labels"][0][1:])
                    if label != trainer.IGNORE), "causal-shift target label mismatch")
        evidence.append(dict(replay_index=index, context_tokens=len(context_ids), raw_target_tokens=len(target_ids),
            supervised_eos_tokens=1, supervised_target_tokens=len(expected_target), input_tokens=len(expected_ids),
            supervised_context_tokens=0, supervised_padding_tokens=0,
            input_ids_sha256=sha(writer._bytes(expected_ids)), labels_sha256=sha(writer._bytes(labels)),
            raw_target_sha256=sha(target.encode()), rendered_context_sha256=sha(rendered.encode()),
            truncation=False, splits=0, target_roundtrip_exact=True))
    first = evidence[0]
    require(all({key: value for key, value in row.items() if key != "replay_index"}
                == {key: value for key, value in first.items() if key != "replay_index"} for row in evidence),
            "replays differ beyond their explicit index")
    return dict(status="PASS_ACTUAL_TOKENIZER_V3_ENCODE_AND_COLLATE", tokenizer_class=type(tokenizer).__name__,
        unique_events=1, explicit_replays=REPLAYS, epochs=EPOCHS, optimizer_steps=REPLAYS * EPOCHS,
        rows=evidence, context_tokens_per_item=first["context_tokens"], raw_target_tokens_per_item=first["raw_target_tokens"],
        input_tokens_per_epoch=sum(row["input_tokens"] for row in evidence),
        supervised_tokens_per_epoch=sum(row["supervised_target_tokens"] for row in evidence),
        input_tokens_all_epochs=EPOCHS * sum(row["input_tokens"] for row in evidence),
        supervised_tokens_all_epochs=EPOCHS * sum(row["supervised_target_tokens"] for row in evidence),
        token_matched=False, chat_template=True, add_eos=True, eos_is_trainer_framing_not_source_text=True,
        truncation=False, splits=0)


def command_specs(output, recipient_root, model, executable, arm, corpus_hash, preflight):
    commands = []
    for seed in SEEDS:
        destination = recipient_root / arm / f"seed{seed}"
        require(not os.path.lexists(destination), "recipient output already exists")
        argv = [str(executable), "-B", "-m", "organism_v6.train_adapter_v3",
            "--corpus", str(output / arm / "corpus.json"), "--out", str(destination),
            "--model", str(model), "--rank", "8", "--alpha", "16", "--epochs", "3", "--lr", "1e-4",
            "--seed", str(seed), "--batch-size", "1", "--grad-accum", "1", "--max-len", "4096",
            "--max-steps", "96", "--no-pack", "--chat-template", "--optimizer", "adamw", "--dropout", "0.05",
            "--target-modules", ",".join(trainer.ALL_PROJ), "--layers", "all", "--overflow", "split",
            "--device", "cuda", "--dtype", "bf16", "--manifest-note",
            f"DEV material utility {arm}; unique_events=1; explicit_replays=32; not tokenmatched; no parenting claim"]
        config = trainer.config_from_args(trainer.build_parser().parse_args(argv[4:]))
        require(config.grad_checkpoint and config.grad_accum == config.batch_size == 1 and not config.pack
                and config.max_steps == REPLAYS * EPOCHS and config.epochs == EPOCHS, "trainer recipe drift")
        commands.append(dict(seed=seed, argv=argv, shell=False, execute=False,
            cwd=str(Path(__file__).resolve().parents[1]), env=dict(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1"),
            output=str(destination), config=asdict(config), corpus_sha256=corpus_hash,
            trainer_sha256=writer._hash(Path(trainer.__file__)), fresh_base=True, adapter_input=None,
            expected_optimizer_steps=96, grad_checkpoint=True,
            expected_manifest=dict(corpus=dict(n_items=REPLAYS, n_encoded=REPLAYS, sha256=corpus_hash),
                steps=96, tokens=dict(target=preflight["supervised_tokens_per_epoch"], total=preflight["input_tokens_per_epoch"]),
                truncation=dict(items_truncated=0, target_tokens_dropped=0, context_tokens_dropped=0, items_split=0)),
            launch="Main only; separate protocol, panel, reservation and runtime checks still required"))
    return dict(commands=commands, seeds=list(SEEDS), execute=False)


def seal_output(output):
    files = {path.relative_to(output).as_posix(): writer._hash(path)
             for path in sorted(output.rglob("*")) if path.is_file()}
    correction.formation._write(output / "artifact_hashes.json", dict(files=files, boundary=BOUNDARY))
    for path in sorted(output.rglob("*"), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    output.chmod(0o555)


def prepare_write(source_arm, capsule_path, output_dir, *, model_path, recipient_root, python_executable=None):
    source = writer._path(source_arm)
    capsule = Path(capsule_path).absolute()
    require(capsule.is_file() and not capsule.is_symlink(), "local capsule file required")
    output = writer._path(output_dir, fresh=True)
    recipients = writer._path(recipient_root, fresh=True)
    model = Path(model_path).resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    require(all(not writer._overlap(destination, protected) for destination in (output, recipients)
                for protected in (source, model, root, capsule)) and not writer._overlap(output, recipients),
            "preparation/recipient paths overlap protected inputs or each other")
    executable = Path(python_executable or sys.executable).absolute()
    require(executable.is_file() and os.access(executable, os.X_OK), "existing Python executable required")
    config, source_metadata = check_source(source, capsule)
    expected_files = config["expected_files"]
    require(correction.formation.local_files(model) == expected_files, "recipient base bytes differ from pinned fresh base")
    context, targets, mapping, reduction = select_event(source)
    pins = implementation_pins()
    tokenizer = writer._load_tokenizer(str(model))
    corpora = {arm: make_corpus(context, targets[arm], arm, mapping) for arm in ARMS}
    preflights = {arm: tokenizer_preflight(corpora[arm], tokenizer) for arm in ARMS}
    require(preflights["whole_raw"]["context_tokens_per_item"] == preflights["act_only"]["context_tokens_per_item"],
            "paired context token mismatch")
    require(preflights["whole_raw"]["rows"][0]["rendered_context_sha256"]
            == preflights["act_only"]["rows"][0]["rendered_context_sha256"], "paired rendered context mismatch")
    output.mkdir()
    try:
        replayed = correction.replay(source, output / "source_replay")
        require(replayed == reduction, "pinned capture/ledger replay differs from selection")
        reports = {}
        for arm in ARMS:
            directory = output / arm
            directory.mkdir()
            correction.formation._write(directory / "corpus.json", corpora[arm])
            corpus_hash = writer._hash(directory / "corpus.json")
            correction.formation._write(directory / "source_map.json", dict(source=source_metadata, unique_events=1,
                explicit_replays=REPLAYS, event=mapping,
                records=[dict(corpus_index=index, replay_index=index, source_event_id=mapping["source_event_id"],
                    context=mapping["context"], target=mapping["targets"][arm],
                    corpus_item_sha256=sha(writer._bytes(corpora[arm]["corpus"][index]))) for index in range(REPLAYS)]))
            correction.formation._write(directory / "tokenizer_preflight.json", preflights[arm])
            commands = command_specs(output, recipients, model, executable, arm, corpus_hash, preflights[arm])
            correction.formation._write(directory / "training_commands.json", commands)
            reports[arm] = dict(corpus_sha256=corpus_hash, target=mapping["targets"][arm],
                context_sha256=mapping["context"]["context_sha256"], preflight=preflights[arm], commands=commands)
        require(check_source(source, capsule)[1] == source_metadata, "source changed during preparation")
        require(correction.formation.local_files(model) == expected_files, "base changed during preparation")
        require(implementation_pins() == pins, "writer/trainer implementation changed during preparation")
        report = dict(schema="parent-correction-write-v1", status="READY_CPU_PREPARATION_ONLY",
            boundary=BOUNDARY, source=source_metadata, selection=APPROVED,
            model_path=str(model), expected_model_files=expected_files, implementation=pins,
            recipient_root=str(recipients), recipient_seeds=list(SEEDS), unique_events=1,
            explicit_replays_per_arm=REPLAYS, epochs=EPOCHS, optimizer_steps_per_recipient=96,
            token_matched=False, source_mapping=mapping, arms=reports,
            common_baseline="Later Main-owned teacher-free OFF/ON probe; no panel or launch created here",
            unchanged_whole_raw=True, synthetic=config["synthetic"])
        correction.formation._write(output / "preparation.json", report)
    except BaseException as error:
        correction.formation._write(output / "failure.json", dict(status="FAILED_NOT_READY", error=repr(error)))
        raise
    finally:
        seal_output(output)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-arm", required=True)
    parser.add_argument("--capsule", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--recipient-root", required=True)
    parser.add_argument("--python-executable")
    arguments = parser.parse_args(argv)
    report = prepare_write(arguments.source_arm, arguments.capsule, arguments.out,
        model_path=arguments.model_path, recipient_root=arguments.recipient_root,
        python_executable=arguments.python_executable)
    print(writer._bytes(dict(status=report["status"], output=arguments.out,
        inventory_sha256=writer._hash(Path(arguments.out) / "artifact_hashes.json"),
        unique_events=1, explicit_replays_per_arm=REPLAYS, commands_only=True)).decode(), end="")


if __name__ == "__main__":
    main()
