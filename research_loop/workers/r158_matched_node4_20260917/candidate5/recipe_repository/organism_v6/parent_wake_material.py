"""CPU-only paired export of historically sourced raw child wake outputs to V3 spans."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

from . import batch_loop, model_backend, parent_material_diagnostic as formation
from . import parent_material_write as reader, parent_note_replay_diagnostic as replay
from . import preschool_reasoning as policy, train_adapter_v3 as trainer


BOUNDARY = dict(label="EXPLORATORY_SOURCE_LINKED_RAW_WAKE_MATERIAL",
                official_model_origin="UNRESOLVED_LOCAL_HASHES_ONLY", clean_lineage=False,
                H1_claim=False, training=False, model_calls=0, admission_certificate=False,
                material_origin="child generated with historical teacher/sham; teacher removed for sleep context",
                usefulness="not established by source binding or selection",
                source_map="audit only; contains original teacher-visible prompts, never training input")
REQUIRED = {"config.json", "results.json", "schedule.json", "ledger.jsonl", "generations.jsonl",
            "lesson_deliveries.jsonl", "local_base_pins.json", "base_after.json", "teaching_dose.json"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _key(receipt):
    return receipt.get("prompt_sha256"), receipt.get("output_sha256"), receipt.get("seed")


def source_arm(root, mode):
    """Validate completed source custody, without invoking any NOTE content judge."""
    root = reader._path(root)
    inventory = replay._inventory(root)
    _require(REQUIRED <= inventory["files"].keys(), "missing formation source artifacts")
    config, result = reader._read(root / "config.json"), reader._read(root / "results.json")
    _require(config["out"] == str(root) and config["mode"] == result["mode"] == mode
             and result["status"] == "COMPLETE", "wrong or incomplete original arm")
    _require(all(config.get(name) == value for name, value in formation.BOUNDARY.items()),
             "original boundary mismatch")
    protocol = formation.protocol(config.get("schedule_seed", 6101), config.get("generation_seed", 7101))
    _require(config["protocol"] == protocol, "original protocol mismatch")
    current = {"organism_v6/preschool_reasoning.py": Path(policy.__file__),
               "organism_v6/batch_loop.py": Path(batch_loop.__file__),
               "organism_v6/reasoning_gym_families.json": Path(policy.FAMILIES_FILE)}
    seen = set()
    for name, digest in config["source_hashes"].items():
        path = Path(name)
        relative = "/".join(path.parts[-2:])
        _require(relative in reader._PRODUCER_FILES and relative not in seen
                 and path.is_absolute() and path == path.resolve() and path.is_file()
                 and not path.is_symlink(), "missing/ambiguous original producer source")
        seen.add(relative)
        _require(formation._hash(path) == digest, "original producer bytes changed")
        if relative in current:
            _require(formation._hash(current[relative]) == digest, "policy/batch/families source differs")
    _require(seen == reader._PRODUCER_FILES, "incomplete producer source inventory")
    pins, after = reader._read(root / "local_base_pins.json"), reader._read(root / "base_after.json")
    _require(pins["model_path"] == after["model_path"] == config["model_path"]
             and pins["files"] == after["files"] == config["expected_files"]
             and after["unchanged"] is True, "original local pins mismatch")
    gym = formation.ReasoningGymGym(require_package=False, strict_verifier=True)
    schedule = reader._read(root / "schedule.json")
    _require(schedule == gym.training_schedule(64, protocol["schedule_seed"])
             and len(set(schedule)) == 64, "original schedule mismatch")
    raw, rows = policy._lines((root / "ledger.jsonl").read_bytes())
    teaching = policy._lesson_rows((root / "lesson_deliveries.jsonl").read_bytes())
    _require(len(teaching) == 1 and teaching[0]["mode"] == mode and teaching[0]["sleeps_done"] == 0,
             "original teaching receipt mismatch")
    _require([row for row in rows if row["kind"] == "parent_turn"] ==
             [policy._teacher_row(teaching[0], policy._ledger_provenance(rows))], "teacher ledger mismatch")
    event_raw, events = policy._lines((root / "generations.jsonl").read_bytes())
    requests, outputs, trace = {}, {}, defaultdict(list)
    identity = model_backend.configured_generation_identity(config["model_path"], None)
    for line, event in enumerate(events):
        _require(event.get("kind") in ("request", "output"), "unknown generation event")
        index = event.get("request_index")
        target = requests if event["kind"] == "request" else outputs
        _require(type(index) is int and index >= 0 and index not in target, "ambiguous generation index")
        target[index] = (line, event)
    _require(requests.keys() == outputs.keys(), "missing generation request/output")
    for index, (request_line, request) in requests.items():
        output_line, output = outputs[index]
        _require(request_line < output_line and request["max_tokens"] in (100, 400)
                 and type(request["seed"]) is int and request["source_identity"] == identity
                 and request["temperature"] == .7, "generation configuration/order mismatch")
        _require(policy._sha(request["prompt"].encode()) == request["prompt_sha256"]
                 and policy._sha(output["text"].encode()) == output["output_sha256"],
                 "generation text/hash mismatch")
        if request["max_tokens"] == 400:
            trace[request["prompt_sha256"], output["output_sha256"], request["seed"]].append(index)
    visits, acts, executions = {}, defaultdict(list), set()
    occurrence_counts = Counter()
    accepted = defaultdict(set)
    for line, row in enumerate(rows):
        if row["kind"] == "episode_occurrence":
            occurrence = row["occurrence_id"]
            _require(occurrence not in visits and row["episode_id"] in schedule,
                     "ambiguous/out-of-schedule occurrence")
            visits[occurrence] = (line, row)
        if row["kind"] != "act":
            continue
        facts = policy.facts_from_act(row)
        occurrence = row.get("occurrence_id")
        _require(occurrence in visits and row["execution_id"] not in executions,
                 "missing occurrence or duplicate execution")
        visit_line, visit = visits[occurrence]
        _require(visit_line < line and row["episode_id"] == visit["episode_id"]
                 and row["occurrence_index"] == visit["occurrence_index"], "event occurrence mismatch")
        occurrence_counts[occurrence] += 1
        ordinal = occurrence_counts[occurrence]
        _require(row["execution_id"] == f"{occurrence}#t{row['tick']}a{ordinal}"
                 and facts.attempt == ordinal, "event execution ordinal mismatch")
        executions.add(row["execution_id"])
        acts[_key(row["generation"])].append((line, row, facts))
        if facts.measured and row["score"] == 1:
            accepted[row["episode_id"].split("/")[1]].add(row["episode_id"])
    chunks, used, joined = [], set(), set()
    for line, row in enumerate(rows):
        if row["kind"] != "thought":
            continue
        receipt = row.get("generation", {})
        indices = trace.get(_key(receipt), [])
        _require(len(indices) == 1 and indices[0] not in used, "unjoined/ambiguous wake thought")
        index = indices[0]
        used.add(index)
        request_line, request = requests[index]
        output_line, output = outputs[index]
        _require(receipt.get("schema") == "child-generation-v1" and receipt.get("identity") == identity
                 and receipt.get("max_tokens") == 400 and receipt.get("temperature") == .7,
                 "wake receipt identity mismatch")
        _require(type(row.get("tick")) is int and 1 <= row["tick"] <= protocol["budget_ticks"]
                 and receipt["seed"] == batch_loop._seed_for(row["episode_id"], row["tick"],
                                                             protocol["generation_seed"]),
                 "wake tick/seed differs from original schedule")
        _require(row["prompt"] == request["prompt"][:24000]
                 and row["note"] == output["text"].strip()[:2000], "thought is not original raw output projection")
        measured = acts.get(_key(receipt), [])
        parsed = [match.group(2).strip() for match in batch_loop._MARK.finditer(output["text"])
                  if match.group(1) == "ACT"]
        _require(parsed == [act["action"] for _, act, _ in measured], "ACT multiplicity/order differs from raw wake")
        for act_line, act, _ in measured:
            _require(act_line < line and act["episode_id"] == row["episode_id"]
                     and act["tick"] == row["tick"] and act["generation"] == receipt,
                     "ACT/thought episode/tick/receipt mismatch")
            joined.add(act["execution_id"])
        _require(row["episode_id"] in schedule, "wake outside source schedule")
        chunks.append(dict(episode_id=row["episode_id"], tick=row["tick"], thought_line=line,
            thought_sha256=policy._sha(raw[line]), request_index=index, request_line=request_line,
            request_sha256=policy._sha(event_raw[request_line]), output_line=output_line,
            output_line_sha256=policy._sha(event_raw[output_line]), generation=receipt,
            original_prompt=request["prompt"], original_rendered_prompt=request["rendered_prompt"],
            original_prompt_tokens=request["prompt_tokens"], raw_output=output["text"],
            ledger_note=row["note"], ledger_clipped=row["note"] != output["text"].strip(),
            events=[dict(ledger_line=act_line, ledger_sha256=policy._sha(raw[act_line]),
                         act=act, measured=facts.measured) for act_line, act, facts in measured]))
    _require(joined == executions and used == {index for indices in trace.values() for index in indices},
             "orphan wake generation or executed event")
    _require(len(visits) == 64 and {visit["episode_id"] for _, visit in visits.values()} == set(schedule)
             and result["n_actions"] == len(executions) and result["generation_requests"] == len(requests),
             "original source event counts disagree")
    return dict(root=root, inventory=inventory, config=config, pins=pins, schedule=schedule,
                teacher=teaching[0], chunks=chunks, bootstrap=gym.birth_prompt(),
                accepted_unique_episodes={family: sorted(values) for family, values in accepted.items()})


def without_teacher(prompt, bootstrap, teacher):
    start, separator = "=== YOU ===\n", "\n=== STATE ===\n"
    _require(prompt.startswith(start) and prompt.count(separator) == 1, "unsupported source prompt envelope")
    head, rest = prompt[len(start):].split(separator, 1)
    _require(head == (bootstrap + "\n\n" + teacher).strip(), "source birth/teacher prompt mismatch")
    return start + bootstrap.strip() + separator + rest


def encode_candidate(chunk, arm, payloads, tokenizer, max_len):
    raw = chunk["raw_output"]
    if replay._echo(raw, payloads):
        return None, "teacher-echo-target"
    context = without_teacher(chunk["original_prompt"], arm["bootstrap"], arm["teacher"]["text"])
    if replay._echo(context, payloads):
        return None, "teacher-echo-context"
    original_rendered = tokenizer.apply_chat_template([dict(role="user", content=chunk["original_prompt"])],
                                                       tokenize=False, add_generation_prompt=True)
    _require(original_rendered == chunk["original_rendered_prompt"]
             and len(tokenizer.encode(original_rendered, add_special_tokens=False)) == chunk["original_prompt_tokens"],
             "actual source tokenizer/rendering mismatch")
    rendered = tokenizer.apply_chat_template([dict(role="user", content=context)],
                                              tokenize=False, add_generation_prompt=True)
    context_ids = tokenizer.encode(rendered, add_special_tokens=False)
    target_ids = tokenizer.encode(raw, add_special_tokens=False) + [tokenizer.eos_token_id]
    if not raw.strip() or not context_ids:
        return None, "empty-context-or-target"
    if len(context_ids) + len(target_ids) > max_len:
        return None, "over-token-budget-no-truncation"
    item = dict(spans=[[rendered, False, "parent_removed_context"], [raw, True, "raw_child_wake"]],
                group=chunk["episode_id"], view="source_wake_local", order=chunk["thought_line"],
                meta=dict(episode_id=chunk["episode_id"], request_index=chunk["request_index"]))
    encoded = trainer.encode_item_segments(item, tokenizer, max_len, chat_template=False)
    _require(len(encoded) == 1 and encoded[0].context_dropped == encoded[0].target_dropped == 0,
             "trainer dropped/split source material")
    actual = trainer.collate([encoded], tokenizer.eos_token_id)
    _require(actual["input_ids"][0] == context_ids + target_ids
             and actual["labels"][0] == [-100] * len(context_ids) + target_ids,
             "source target/context labels differ from actual trainer")
    return dict(item=item, context=context, rendered_context=rendered,
                input_tokens=len(context_ids) + len(target_ids), target_tokens=len(target_ids),
                labels_sha256=policy._sha(policy._encoded(actual["labels"][0])), source=chunk), None


def export_pair(lesson_root, sham_root, output_dir, *, count, selection, families=None,
                max_len=4096, tokenizer=None):
    _require(type(count) is int and 1 <= count <= 64, "count must be 1..64, explicitly chosen")
    _require(selection in ("measured", "accepted"), "selection must be measured or accepted")
    _require(type(max_len) is int and 1 <= max_len <= 16384, "max_len must be 1..16384")
    output = reader._path(output_dir, fresh=True)
    roots = [reader._path(lesson_root), reader._path(sham_root)]
    _require(all(not reader._overlap(left, right) for index, left in enumerate([*roots, output])
                 for right in [*roots, output][index + 1:]), "source/output roots overlap")
    source_files = {str(Path(module.__file__).resolve()): formation._hash(module.__file__) for module in
                    (sys.modules[__name__], replay, reader, formation, policy, trainer, batch_loop, model_backend)}
    for name in ("bootstrap_reasoning_gym.txt", "reasoning_gym_gym.py"):
        path = Path(formation.__file__).resolve().with_name(name)
        source_files[str(path)] = formation._hash(path)
    arms = [source_arm(root, mode) for root, mode in zip(roots, ("lesson", "sham"))]
    _require(arms[0]["schedule"] == arms[1]["schedule"] and arms[0]["pins"] == arms[1]["pins"]
             and arms[0]["config"]["protocol"] == arms[1]["config"]["protocol"], "paired schedule/model/protocol mismatch")
    allowed = set(reader._read(Path(policy.FAMILIES_FILE))["train_families"])
    requested = allowed if families is None else set(families)
    _require(requested and requested <= allowed, "unknown or non-training family")
    schedule = [episode for episode in arms[0]["schedule"] if episode.split("/")[1] in requested]
    model = Path(arms[0]["config"]["model_path"])
    _require(not reader._overlap(model, output), "output overlaps local base")
    _require(formation.local_files(model) == arms[0]["pins"]["files"], "actual local base differs from recorded pins")
    injected = tokenizer is not None
    tokenizer = tokenizer if injected else reader._load_tokenizer(str(model))
    _require(getattr(tokenizer, "eos_token_id", None) is not None, "tokenizer EOS required")
    payloads = replay._payloads([arm["teacher"]["text"] for arm in arms])
    available, summaries = {}, {}
    for mode, arm in zip(("lesson", "sham"), arms):
        candidates, considered, rejected = {}, set(), []
        for chunk in arm["chunks"]:
            episode = chunk["episode_id"]
            qualifies = any(event["measured"] and (selection == "measured" or event["act"]["score"] == 1)
                            for event in chunk["events"])
            if episode not in schedule or episode in considered or not qualifies:
                continue
            considered.add(episode)
            encoded, reason = encode_candidate(chunk, arm, payloads, tokenizer, max_len)
            if reason:
                rejected.append(dict(episode_id=episode, request_index=chunk["request_index"], reason=reason))
            else:
                candidates[episode] = encoded
        available[mode] = candidates
        summaries[mode] = dict(eligible_unique_episodes=len(candidates), rejected=rejected,
            no_qualifying_event=[episode for episode in schedule if episode not in considered],
            accepted_unique_episodes=arm["accepted_unique_episodes"],
            accepted_mini_sudoku_episodes=len(arm["accepted_unique_episodes"].get("mini_sudoku", [])),
            board_identity_validation="not repeated; counts are distinct episode IDs, not proof of distinct boards",
            teacher_tokens=len(tokenizer.encode(arm["teacher"]["text"], add_special_tokens=False)),
            raw_wake_chunks=len(arm["chunks"]), ledger_clipped_chunks=sum(chunk["ledger_clipped"] for chunk in arm["chunks"]))
    common = [episode for episode in schedule if all(episode in available[mode] for mode in available)]
    selected = common[:count] if len(common) >= count else []
    status = "READY" if len(selected) == count else "PAIRED_SKIP"
    boundary = dict(BOUNDARY, tokenizer_validation="injected CPU fixture" if injected else "actual local tokenizer")
    spec = dict(count=count, selection=selection, families=sorted(requested), max_len=max_len,
                source_rule="first qualifying wake per episode in physical order; no replacement after exclusion; first common episodes in original schedule order",
                no_note_content_gate=True, selected_episodes=selected, available_paired_episodes=len(common),
                same_example_count=True, token_budget_per_arm=count * max_len,
                target_token_equivalence="NOT_ASSERTED; actual arm token masses recorded",
                teacher_dose_equivalence="NOT_ASSERTED; historical lesson/sham package confound retained",
                trainer_format="pre-rendered context spans; no --chat-template; no training scheduled")
    artifacts = {"selection.json": spec, "source_hashes.json": source_files,
                 "original_sources.json": {mode: dict(root=str(arm["root"]), inventory=arm["inventory"],
                     config=arm["config"], local_pins=arm["pins"], teacher_receipt=arm["teacher"])
                     for mode, arm in zip(("lesson", "sham"), arms)}}
    for mode in available:
        chosen = [available[mode][episode] for episode in selected]
        artifacts[f"{mode}.json"] = dict(recipe="source_linked_raw_wake_v3_spans_v1", boundary=boundary,
                                          corpus=[row["item"] for row in chosen])
        artifacts[f"{mode}_source_map.json"] = dict(boundary=boundary, rows=chosen)
        summaries[mode].update(selected_examples=len(chosen),
            input_tokens=sum(row["input_tokens"] for row in chosen),
            target_tokens=sum(row["target_tokens"] for row in chosen))
    result = dict(boundary=boundary, status=status, selection=spec, arms=summaries,
                  reason="paired material exported" if status == "READY" else "paired unique-source shortage; no partial corpus")
    artifacts["results.json"] = result
    for arm in arms:
        _require(replay._inventory(arm["root"]) == arm["inventory"], "source changed during export")
        for path, digest in arm["config"]["source_hashes"].items():
            _require(formation._hash(path) == digest, "historical producer changed during export")
    _require(formation.local_files(model) == arms[0]["pins"]["files"], "local base changed during export")
    _require(all(formation._hash(path) == digest for path, digest in source_files.items()), "exporter source changed")
    output.mkdir(exist_ok=False)
    for name, value in artifacts.items():
        formation._write(output / name, value)
    formation._write(output / "artifact_hashes.json", dict(files={name: formation._hash(output / name) for name in artifacts}))
    output.chmod(0o555)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson-root", required=True)
    parser.add_argument("--sham-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--selection", required=True, choices=("measured", "accepted"))
    parser.add_argument("--family", action="append")
    parser.add_argument("--max-len", type=int, default=4096)
    args = parser.parse_args(argv)
    result = export_pair(args.lesson_root, args.sham_root, args.out, count=args.count,
                         selection=args.selection, families=args.family, max_len=args.max_len)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
