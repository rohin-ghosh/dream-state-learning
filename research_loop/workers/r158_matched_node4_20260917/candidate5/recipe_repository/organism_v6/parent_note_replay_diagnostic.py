"""Bounded historical-source NOTE replay, not a new childhood or training run.

First four measured ACTs per original schedule, exactly 256 per arm. The old
slot prompt/seed is preserved except for fixed coaching before its outcome block.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time

from . import batch_loop, model_backend
from . import parent_material_diagnostic as formation
from . import parent_material_write as reader
from . import preschool_reasoning as policy
from . import run_reasoning_neutral as neutral


COACH = ("For this post-outcome field, write only a short first-person record of the action you already "
         "submitted and the displayed verifier result. Quote your actual submitted action and the displayed "
         "score. Do not issue another ACT, solve the puzzle again, or claim an unobserved answer.")
ARMS = ("lesson", "sham")
COUNT = 256
BATCH_SIZE = 8
TIMEOUT = 3600
MAX_MODEL_LEN = 16384
BOUNDARY = dict(schema="source-replayed-material-v1", label="SOURCE_REPLAYED_MATERIAL_FORMATION",
    new_world_actions=0, training=False, clean_lineage=False, eligibility_certificate=False,
    model_provenance="LOCAL_HASHES_ONLY", official_base_authentication="UNRESOLVED",
    interpretation="Shared coached historical-context diagnostic; teacher dose remains confounded; no H1 claim",
    backend_output_ids="not exposed; output IDs below are local trace identifiers")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _inventory(root):
    manifest = reader._read(root / "artifact_hashes.json")
    files = manifest["files"]
    _require(isinstance(files, dict) and len(files) <= 32, "invalid artifact inventory")
    _require({path.name for path in root.iterdir()} == set(files) | {"artifact_hashes.json"}, "artifact inventory changed")
    _require(not any("failure" in name.lower() or name.startswith("partial_") or name.endswith("_error.json")
                     for name in files), "failed source/replay")
    for name, digest in files.items():
        _require(Path(name).name == name and name not in (".", "..", "artifact_hashes.json"), "unsafe artifact path")
        path = root / name
        _require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 512 * 1024 * 1024,
                 "invalid or oversized artifact")
        _require(formation._hash(path) == digest, "artifact hash mismatch: " + name)
    return dict(files=files, manifest_sha256=formation._hash(root / "artifact_hashes.json"))


def _implementation():
    modules = (sys.modules[__name__], formation, reader, policy, batch_loop, model_backend, neutral)
    return {str(Path(module.__file__).resolve()): formation._hash(Path(module.__file__)) for module in modules}


def _check_implementation(recorded):
    current = {"/".join(Path(path).parts[-2:]): digest for path, digest in _implementation().items()}
    previous = {}
    for name, digest in recorded.items():
        path = Path(name)
        _require(path.is_absolute() and path == path.resolve() and path.is_file()
                 and not path.is_symlink() and formation._hash(path) == digest, "replay source bytes changed")
        relative = "/".join(path.parts[-2:])
        _require(relative not in previous, "ambiguous replay implementation")
        previous[relative] = digest
    _require(previous == current, "executing replay implementation differs")


def _payloads(texts):
    parts = []
    for text in texts:
        for part in [text, *text.splitlines()]:
            part = part.removeprefix("- ")
            parts.extend([part, *re.split(r"(?<=[.!?])\s+", part)])
    return [policy._copy_key(part.removeprefix("- ")) for part in parts if policy._copy_key(part)]


def _echo(text, payloads):
    normalized = " " + policy._copy_key(text) + " "
    return any(" " + payload + " " in normalized for payload in payloads)


def coached_prompt(prompt, facts):
    suffix = "\n\n" + policy.outcome_block(facts, "NOTE_AFTER")
    _require(prompt.endswith(suffix), "original outcome suffix mismatch")
    return prompt[:-len(suffix)] + "\n\n" + COACH + suffix


def inspect_source(root, arm):
    """Validate historical provenance independently of old NOTE content quality."""
    root = reader._path(root)
    inventory = _inventory(root)
    config = reader._read(root / "config.json")
    result = reader._read(root / "results.json")
    _require(config["mode"] == arm and config["out"] == str(root) and result["status"] == "COMPLETE"
             and result["mode"] == arm, "incomplete or wrong original arm")
    expected_protocol = formation.protocol(config.get("schedule_seed", 6101), config.get("generation_seed", 7101))
    _require(config["protocol"] == expected_protocol, "unsupported original protocol")
    _require(all(config.get(key) == value for key, value in formation.BOUNDARY.items()), "wrong original boundary")
    current = {"organism_v6/preschool_reasoning.py": Path(policy.__file__),
               "organism_v6/batch_loop.py": Path(batch_loop.__file__),
               "organism_v6/reasoning_gym_families.json": Path(policy.FAMILIES_FILE)}
    names = set()
    for name, digest in config["source_hashes"].items():
        path = Path(name)
        relative = "/".join(path.parts[-2:])
        _require(path.is_absolute() and path == path.resolve() and path.is_file() and not path.is_symlink(),
                 "missing original producer source")
        _require(relative in reader._PRODUCER_FILES and relative not in names, "unknown or ambiguous original producer")
        names.add(relative)
        _require(formation._hash(path) == digest, "original producer bytes changed")
        if relative in current:
            _require(formation._hash(current[relative]) == digest, "source policy/batch/families differ")
    _require(names == reader._PRODUCER_FILES, "incomplete original source inventory")
    pins = reader._read(root / "local_base_pins.json")
    after = reader._read(root / "base_after.json")
    _require(pins["model_path"] == config["model_path"] == after["model_path"]
             and config["expected_files"] == pins["files"] == after["files"] and after["unchanged"] is True,
             "original model pins disagree")
    schedule = reader._read(root / "schedule.json")
    gym = formation.ReasoningGymGym(require_package=False, strict_verifier=True)
    _require(schedule == gym.training_schedule(64, expected_protocol["schedule_seed"])
             and len(set(schedule)) == 64, "wrong original 64 schedule")
    raw, rows = policy._lines((root / "ledger.jsonl").read_bytes())
    provenance = policy._ledger_provenance(rows)
    teaching = policy._lesson_rows((root / "lesson_deliveries.jsonl").read_bytes())
    _require(len(teaching) == 1 and teaching[0]["mode"] == arm and teaching[0]["sleeps_done"] == 0,
             "wrong original teacher")
    _require([row for row in rows if row["kind"] == "parent_turn"] ==
             [policy._teacher_row(teaching[0], provenance)], "teacher source mismatch")
    legacy_payloads = [policy._copy_key(part.removeprefix("- "))
                       for part in [teaching[0]["text"], *teaching[0]["text"].splitlines()]
                       if len(policy._copy_key(part).split()) >= 8]
    acts, notes, visits, batches, prefixes = (defaultdict(list) for _ in range(5))
    prefix = hashlib.sha256()
    selected, per_episode = [], Counter()
    for index, row in enumerate(rows):
        kind = row["kind"]
        target = {"act": acts, "note_after": notes, "episode_occurrence": visits}.get(kind)
        if target is not None:
            target[row["occurrence_id"] if kind == "episode_occurrence" else row["execution_id"]].append(index)
        if kind == "note_after":
            batch_id = row["generation"]["batch_id"]
            batches[batch_id].append(row)
            prefixes.setdefault(batch_id, prefix.hexdigest())
        if kind == "act":
            facts = policy.facts_from_act(row)
            _require(facts.episode_id in schedule, "ACT outside original schedule")
            if facts.measured and per_episode[facts.episode_id] < 4:
                selected.append(index)
                per_episode[facts.episode_id] += 1
        prefix.update(raw[index])
    _require(len(selected) == COUNT and all(per_episode[episode] == 4 for episode in schedule),
             "requires first four measured ACTs for all 64 schedules (256 per arm)")
    event_raw, events = policy._lines((root / "generations.jsonl").read_bytes())
    requests, outputs = {}, {}
    for index, event in enumerate(events):
        _require(event["kind"] in ("request", "output"), "unknown original generation event")
        target = requests if event["kind"] == "request" else outputs
        key = event["request_index"]
        _require(type(key) is int and key >= 0 and key not in target, "ambiguous original generation")
        target[key] = (index, event)
    trace = defaultdict(list)
    for key, (index, request) in requests.items():
        if key in outputs:
            trace[request["prompt_sha256"], outputs[key][1]["output_sha256"], request["seed"], request["max_tokens"]].append(key)
    identity = model_backend.configured_generation_identity(config["model_path"], None)

    def link(generation, limit):
        keys = trace[generation["prompt_sha256"], generation["output_sha256"], generation["seed"], limit]
        _require(len(keys) == 1, "missing or ambiguous actual generation trace")
        request_index = keys[0]
        request_line, request = requests[request_index]
        output_line, output = outputs[request_index]
        _require(policy._sha(request["prompt"].encode()) == generation["prompt_sha256"]
                 and policy._sha(output["text"].encode()) == generation["output_sha256"]
                 and request["source_identity"] == identity and request["temperature"] == .7,
                 "actual generation source mismatch")
        return dict(request_index=request_index, request_line=request_line, output_line=output_line,
                    request_sha256=policy._sha(event_raw[request_line]), output_sha256=policy._sha(event_raw[output_line])), request, output

    sources = []
    for source_index in selected:
        act = rows[source_index]
        facts = policy.facts_from_act(act)
        _require(len(notes[facts.execution_id]) == 1, "missing or ambiguous original NOTE")
        note_index = notes[facts.execution_id][0]
        note = rows[note_index]
        old_judgment = policy.judge_record(note["text"], facts)
        expected_rejection = ("provenance-lesson-echo" if _echo(note["text"], legacy_payloads)
                              else None if old_judgment["content_eligible"] else old_judgment["reason"])
        rejection, matched = policy._judge_source(note_index, rows, acts, notes, visits, legacy_payloads, batches)
        _require(rejection == expected_rejection and (rejection is not None or matched == source_index),
                 "original ACT/NOTE provenance mismatch: " + str(rejection))
        _require(policy._generation_rejection(note, facts, batches) is None, "original NOTE generation custody mismatch")
        generation = note["generation"]
        _require(generation["ledger_prefix_sha256"] == prefixes[generation["batch_id"]]
                 and generation["max_tokens"] == 100 and generation["temperature"] == .7
                 and generation["backend_identity"] == identity, "original NOTE generation configuration mismatch")
        note_link, request, old_output = link(generation, 100)
        _require(request["prompt"] == generation["prompt"] and old_output["text"] == note["text"], "old NOTE trace differs")
        wake = act["generation"]
        _require(wake["schema"] == "child-generation-v1" and wake["identity"] == identity
                 and wake["max_tokens"] == 400 and wake["temperature"] == .7, "original wake identity mismatch")
        wake_link, _, wake_output = link(wake, 400)
        actions = [match.group(2).strip() for match in batch_loop._MARK.finditer(wake_output["text"]) if match.group(1) == "ACT"]
        _require(act["action"] in actions, "ACT absent from actual original wake")
        sources.append(dict(source_id=f"{arm}:{facts.execution_id}", episode_id=facts.episode_id,
            execution_id=facts.execution_id, source_act=act, act_line=source_index, act_sha256=policy._sha(raw[source_index]),
            old_note_line=note_index, old_note_sha256=policy._sha(raw[note_index]), old_text=note["text"],
            old_judgment=old_judgment, original_prompt=generation["prompt"], original_seed=generation["seed"],
            original_rendered_prompt=request["rendered_prompt"], original_prompt_tokens=request["prompt_tokens"],
            note_trace=note_link, wake_trace=wake_link, replay_prompt=coached_prompt(generation["prompt"], facts)))
    return dict(root=str(root), inventory=inventory, config=config, local_pins=pins, schedule=schedule,
                teacher=teaching[0], sources=sources)


def _token_info(source, tokenizer):
    render = lambda text: tokenizer.apply_chat_template([dict(role="user", content=text)], tokenize=False, add_generation_prompt=True)
    old_rendered = render(source["original_prompt"])
    rendered = render(source["replay_prompt"])
    count = lambda text: len(tokenizer.encode(text, add_special_tokens=False))
    _require(old_rendered == source["original_rendered_prompt"] and count(old_rendered) == source["original_prompt_tokens"],
             "original tokenizer/rendered prompt differs")
    _require(count(rendered) + 100 <= MAX_MODEL_LEN, "coached prompt exceeds context budget; no truncation")
    return dict(rendered_prompt=rendered, rendered_prompt_sha256=policy._sha(rendered.encode()),
                original_prompt_tokens=count(old_rendered), prompt_tokens=count(rendered),
                rendered_token_delta=count(rendered) - count(old_rendered), coach_standalone_tokens=count(COACH))


def _judgment(text, source, teacher):
    judgment = policy.judge_record(text, policy.facts_from_act(source["source_act"]))
    echo = _echo(text, _payloads([COACH, teacher]))
    return dict(judge_record=judgment, delivered_text_echo=echo, faithful=judgment["content_eligible"] and not echo)


def _summary(records, sources):
    arms = {}
    for arm in ARMS:
        values = [row for row in records if row["arm"] == arm]
        faithful = [row for row in values if row["judgment"]["faithful"]]
        arms[arm] = dict(selected=COUNT, completed=len(values), faithful=len(faithful),
            unique_faithful=len({policy._copy_key(row["text"]) for row in faithful}),
            old_content_eligible=sum(source["old_judgment"]["content_eligible"] for source in sources[arm]["sources"]),
            coach_presentations=len(values), coach_standalone_tokens=sum(row["tokens"]["coach_standalone_tokens"] for row in values),
            per_schedule=[dict(episode_id=episode, selected=4,
                faithful=sum(row["judgment"]["faithful"] for row in values if row["episode_id"] == episode))
                for episode in sources[arm]["schedule"]])
    return dict(**BOUNDARY, status="COMPLETE", total_note_requests=len(records), arms=arms,
                observation="Historical-source paired counts only; no new task measurements or qualification")


@contextmanager
def _deadline():
    def stop(signum, frame):
        raise TimeoutError("source replay stopped; one-hour limit or termination")
    previous = {kind: signal.signal(kind, stop) for kind in (signal.SIGALRM, signal.SIGTERM)}
    signal.alarm(TIMEOUT)
    try:
        yield
    finally:
        signal.alarm(0)
        for kind, handler in previous.items():
            signal.signal(kind, handler)


def run(lesson_root, sham_root, output_dir, *, allow_gpu=False, backend_factory=None):
    _require(allow_gpu is True, "explicit --execute GPU opt-in required")
    output = reader._path(output_dir, fresh=True)
    sources = {arm: inspect_source(root, arm) for arm, root in zip(ARMS, (lesson_root, sham_root))}
    _require(sources["lesson"]["root"] != sources["sham"]["root"]
             and sources["lesson"]["schedule"] == sources["sham"]["schedule"]
             and sources["lesson"]["config"]["protocol"] == sources["sham"]["config"]["protocol"]
             and sources["lesson"]["local_pins"] == sources["sham"]["local_pins"], "unmatched original pair")
    model_path = sources["lesson"]["config"]["model_path"]
    pins = sources["lesson"]["local_pins"]["files"]
    _require(formation.local_files(model_path) == pins, "actual local base differs")
    protected = [Path(model_path), Path(__file__).resolve().parents[1], *[Path(source["root"]) for source in sources.values()]]
    _require(all(not reader._overlap(output, path) for path in protected), "output overlaps protected inputs")
    implementation = _implementation()
    output.mkdir()
    config = dict(**BOUNDARY, model_path=model_path, model_pins=pins, source_roots={arm: source["root"] for arm, source in sources.items()},
        implementation=implementation, coach=COACH, coach_sha256=policy._sha(COACH.encode()),
        selected_per_arm=COUNT, batch_size=BATCH_SIZE, max_tokens=100, temperature=.7,
        maximum_note_generations=512, timeout_seconds=TIMEOUT, max_model_len=MAX_MODEL_LEN,
        device=os.environ.get("CUDA_VISIBLE_DEVICES"), selection="first four measured ACTs per schedule, physical ledger order")
    formation._write(output / "config.json", config)
    for arm in ARMS:
        formation._write(output / (arm + "_sources.json"), sources[arm])
    records = []
    try:
        with _deadline(), (backend_factory or formation.local_backend)(model_path) as model:
            identity = model_backend.configured_generation_identity(model_path, None)
            _require(model.generation_identity() == identity, "replay backend identity mismatch")
            prepared = {arm: [_token_info(source, model.tok) for source in sources[arm]["sources"]] for arm in ARMS}
            formation._write(output / "token_preflight.json", prepared)
            with (output / "generations.jsonl").open("xb") as trace, (output / "records.jsonl").open("xb") as record_file:
                for arm in ARMS:
                    for start in range(0, COUNT, BATCH_SIZE):
                        batch = sources[arm]["sources"][start:start + BATCH_SIZE]
                        _require(model.generation_identity() == identity, "replay backend identity changed")
                        for offset, source in enumerate(batch):
                            trace.write(policy._encoded(dict(kind="request", output_id=f"{arm}/{start + offset:04d}",
                                source_id=source["source_id"], prompt=source["replay_prompt"],
                                prompt_sha256=policy._sha(source["replay_prompt"].encode()), seed=source["original_seed"],
                                max_tokens=100, temperature=.7, identity=identity, tokens=prepared[arm][start + offset])))
                        trace.flush()
                        os.fsync(trace.fileno())
                        started = time.monotonic()
                        outputs = model.batch([source["replay_prompt"] for source in batch], max_tokens=100,
                                              seeds=[source["original_seed"] for source in batch], temperature=.7)
                        trace.write(policy._encoded(dict(kind="batch_return", arm=arm, start=start, outputs=outputs,
                                                         elapsed_seconds=time.monotonic() - started)))
                        trace.flush()
                        _require(isinstance(outputs, (list, tuple)) and len(outputs) == BATCH_SIZE
                                 and all(isinstance(text, str) for text in outputs), "invalid replay output cardinality/type")
                        for offset, (source, text) in enumerate(zip(batch, outputs)):
                            record = dict(arm=arm, output_id=f"{arm}/{start + offset:04d}", source_id=source["source_id"],
                                episode_id=source["episode_id"], execution_id=source["execution_id"], old_text=source["old_text"],
                                text=text, output_sha256=policy._sha(text.encode()), tokens=prepared[arm][start + offset],
                                output_retokenized_tokens=len(model.tok.encode(text, add_special_tokens=False)),
                                judgment=_judgment(text, source, sources[arm]["teacher"]["text"]))
                            records.append(record)
                            record_file.write(policy._encoded(record))
                        record_file.flush()
                        _require(model.generation_identity() == identity, "replay backend identity changed")
        _require(len(records) == 512, "incomplete replay")
        _require(formation.local_files(model_path) == pins, "local base changed during replay")
        _check_implementation(implementation)
        for source in sources.values():
            _require(_inventory(Path(source["root"])) == source["inventory"], "original inputs changed during replay")
        result = _summary(records, sources)
        formation._write(output / "results.json", result)
        return result
    except BaseException as error:
        formation._write(output / "failure.json", dict(**BOUNDARY, error_type=type(error).__name__, error=str(error),
                                                       completed_note_outputs=len(records)))
        raise
    finally:
        formation._write(output / "artifact_hashes.json", dict(**BOUNDARY,
            files={path.name: formation._hash(path) for path in output.iterdir() if path.is_file()}))
        for path in output.iterdir():
            path.chmod(0o444)
        output.chmod(0o555)


def validate_replay(output_dir, *, tokenizer=None):
    """CPU revalidation for later source-linked consumers; never produce a corpus."""
    output = reader._path(output_dir)
    _inventory(output)
    config = reader._read(output / "config.json")
    _require(all(config.get(key) == value for key, value in BOUNDARY.items()) and config["coach"] == COACH
             and config["coach_sha256"] == policy._sha(COACH.encode()) and config["maximum_note_generations"] == 512
             and config["selected_per_arm"] == COUNT and config["batch_size"] == 8
             and config["max_tokens"] == 100 and config["temperature"] == .7
             and config["timeout_seconds"] == TIMEOUT and config["max_model_len"] == MAX_MODEL_LEN,
             "invalid replay configuration")
    _check_implementation(config["implementation"])
    sources = {arm: inspect_source(config["source_roots"][arm], arm) for arm in ARMS}
    _require(sources["lesson"]["schedule"] == sources["sham"]["schedule"]
             and sources["lesson"]["config"]["protocol"] == sources["sham"]["config"]["protocol"],
             "replay original pair differs")
    for arm in ARMS:
        _require(reader._bytes(sources[arm]) == reader._bytes(reader._read(output / (arm + "_sources.json"))), "historical source map changed")
        _require(sources[arm]["local_pins"]["files"] == config["model_pins"]
                 and sources[arm]["config"]["model_path"] == config["model_path"], "replay source model mismatch")
    _require(formation.local_files(config["model_path"]) == config["model_pins"], "local replay model changed")
    tokenizer = tokenizer or reader._load_tokenizer(config["model_path"])
    prepared = {arm: [_token_info(source, tokenizer) for source in sources[arm]["sources"]] for arm in ARMS}
    _require(prepared == reader._read(output / "token_preflight.json"), "token preflight changed")
    _, events = policy._lines((output / "generations.jsonl").read_bytes())
    _, records = policy._lines((output / "records.jsonl").read_bytes())
    _require(len(records) == 512 and len(events) == 512 + 64, "incomplete or excess replay generations")
    identity = model_backend.configured_generation_identity(config["model_path"], None)
    cursor, record_index = 0, 0
    for arm in ARMS:
        for start in range(0, COUNT, BATCH_SIZE):
            batch_return = events[cursor + BATCH_SIZE]
            _require(batch_return["kind"] == "batch_return" and batch_return["arm"] == arm
                     and batch_return["start"] == start and len(batch_return["outputs"]) == 8, "batch trace mismatch")
            for offset in range(BATCH_SIZE):
                source = sources[arm]["sources"][start + offset]
                expected = dict(kind="request", output_id=f"{arm}/{start + offset:04d}", source_id=source["source_id"],
                    prompt=source["replay_prompt"], prompt_sha256=policy._sha(source["replay_prompt"].encode()),
                    seed=source["original_seed"], max_tokens=100, temperature=.7, identity=identity, tokens=prepared[arm][start + offset])
                _require(events[cursor + offset] == expected, "actual replay request changed")
                text = batch_return["outputs"][offset]
                _require(isinstance(text, str), "nontext replay output")
                expected_record = dict(arm=arm, output_id=expected["output_id"], source_id=source["source_id"],
                    episode_id=source["episode_id"], execution_id=source["execution_id"], old_text=source["old_text"], text=text,
                    output_sha256=policy._sha(text.encode()), tokens=prepared[arm][start + offset],
                    output_retokenized_tokens=len(tokenizer.encode(text, add_special_tokens=False)),
                    judgment=_judgment(text, source, sources[arm]["teacher"]["text"]))
                _require(records[record_index] == expected_record, "replay output/source/judgment mismatch")
                record_index += 1
            cursor += BATCH_SIZE + 1
    result = _summary(records, sources)
    _require(result == reader._read(output / "results.json"), "replay result differs from actual records")
    return dict(results=result, records=records, sources=sources)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson-root")
    parser.add_argument("--sham-root")
    parser.add_argument("--out", required=True)
    parser.add_argument("--log")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.validate:
        _require(not args.execute and not args.worker, "validation does not execute")
        print(json.dumps(validate_replay(args.out)["results"], sort_keys=True))
        return
    if not args.execute or not args.lesson_root or not args.sham_root:
        parser.error("--execute and both original source roots required")
    if args.worker:
        print(json.dumps(run(args.lesson_root, args.sham_root, args.out, allow_gpu=True), sort_keys=True))
        return
    _require(args.log is not None, "exclusive external --log required")
    output = reader._path(args.out, fresh=True)
    log = reader._path(args.log, fresh=True)
    roots = [reader._path(args.lesson_root), reader._path(args.sham_root)]
    model = Path(reader._read(roots[0] / "config.json")["model_path"])
    _require(all(not reader._overlap(log, path) for path in [output, model, *roots, Path(__file__).resolve().parents[1]]),
             "external log overlaps protected paths")
    device = neutral.selected_device()
    _require(neutral.gpu_processes_absent(device), "GPU busy or occupancy query failed")
    os.environ.update(V6_MODEL=str(model), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn")
    command = [sys.executable, "-B", "-m", "organism_v6.parent_note_replay_diagnostic", "--lesson-root", str(roots[0]),
               "--sham-root", str(roots[1]), "--out", str(output), "--execute", "--worker"]
    neutral.run_worker(command, log_path=log, timeout=TIMEOUT, device=device)
    print(json.dumps(reader._read(output / "results.json"), sort_keys=True))


if __name__ == "__main__":
    main()
