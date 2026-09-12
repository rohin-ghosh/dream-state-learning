"""Read-only, bounded CPU reduction of a completed 64-schedule formation pair.

Uses the producer's judgments, not a new judge, writer selection, or C11 guard.
Only the local tokenizer is loaded; no model inference or training is available.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random

from . import parent_material_diagnostic as formation
from . import parent_material_write as extraction
from . import preschool_reasoning as policy


COUNT = 64
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
MAX_ROOT_BYTES = 1024 * 1024 * 1024
MAX_BOOTSTRAP = 20000
BOUNDARY = dict(
    label="EXPLORATORY_PAIRED_FORMATION_ANALYSIS", training=False,
    eligibility_claim=False, H1_claim=False, clean_lineage=False,
    official_base_authentication="UNRESOLVED", formal_C11_guard=False,
    inference="conditional on one frozen learner and generation seed 7101; "
              "schedule resampling is exploratory, not independent learner replication",
    attribution="whole exact prompt-package effect only; semantic content and teacher dose "
                "are confounded (live lesson 203 versus sham 158 tokens, difference 45); "
                "no token-normalized causal claim",
    exclusions="no task-decision improvement, adaptive parenting, training, eligibility, "
               "H1, SLEEP, retention, or parent-deletion claim")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _bounded_snapshot(root):
    paths = list(root.iterdir())
    _require(len(paths) <= 32, "formation artifact count exceeds CPU bound")
    _require(all(path.is_file() and not path.is_symlink() for path in paths),
             "formation artifacts must be regular nonsymlink files")
    sizes = [path.stat().st_size for path in paths]
    _require(all(size <= MAX_ARTIFACT_BYTES for size in sizes)
             and sum(sizes) <= MAX_ROOT_BYTES, "formation artifacts exceed CPU byte bound")
    return extraction._formation_snapshot(root)


def paired_summary(lesson, sham, *, seed=20260912, replicates=10000):
    """Percentile bootstrap of paired schedule differences, never individual ACTs."""
    _require(len(lesson) == len(sham) == COUNT, "exactly 64 schedule pairs required")
    _require(all(type(value) is int and value >= 0 for value in [*lesson, *sham]),
             "formation counts must be nonnegative integers")
    _require(type(seed) is int and 0 <= seed <= 0xffffffff, "invalid bootstrap seed")
    _require(type(replicates) is int and 100 <= replicates <= MAX_BOOTSTRAP,
             "bootstrap replicates must be 100..20000")
    differences = [left - right for left, right in zip(lesson, sham)]
    incidence = [int(left > 0) - int(right > 0) for left, right in zip(lesson, sham)]
    generator = random.Random(seed)
    means, incidences = [], []
    for _ in range(replicates):
        indices = [generator.randrange(COUNT) for _ in range(COUNT)]
        means.append(sum(differences[index] for index in indices) / COUNT)
        incidences.append(sum(incidence[index] for index in indices) / COUNT)

    def interval(values):
        values.sort()
        def quantile(probability):
            position = (len(values) - 1) * probability
            lower = int(position)
            upper = min(lower + 1, len(values) - 1)
            return values[lower] + (values[upper] - values[lower]) * (position - lower)
        return [quantile(.025), quantile(.975)]

    return dict(
        paired_unit="declared schedule; all 64 retained, absent records counted as zero observed",
        primary="strict ACT-linked faithful NOTE_AFTER count per schedule, before deduplication",
        n_pairs=COUNT, lesson_total=sum(lesson), sham_total=sum(sham),
        mean_count_difference=sum(differences) / COUNT,
        mean_count_difference_interval_95=interval(means),
        any_formation_rate_difference=sum(incidence) / COUNT,
        any_formation_rate_difference_interval_95=interval(incidences),
        discordant_any_formation=dict(
            lesson_only=sum(left > 0 and right == 0 for left, right in zip(lesson, sham)),
            sham_only=sum(left == 0 and right > 0 for left, right in zip(lesson, sham)),
            both=sum(left > 0 and right > 0 for left, right in zip(lesson, sham)),
            neither=sum(left == 0 and right == 0 for left, right in zip(lesson, sham))),
        count_comparison=dict(lesson_higher=sum(value > 0 for value in differences),
                              sham_higher=sum(value < 0 for value in differences),
                              equal=sum(value == 0 for value in differences)),
        bootstrap=dict(seed=seed, replicates=replicates, confidence=.95,
                       method="paired percentile; linear quantiles; resample 64 schedule indices",
                       scope=BOUNDARY["inference"]))


def _bucket():
    return dict(ledger_rows=0, occurrences=0, actions=0, feedback_valid_actions=0,
                measured_actions=0, unmeasured_actions=0, invalid_feedback_actions=0,
                valid_acts=0, note_after_records=0, strict_faithful_note_after=0,
                any_strict_faithful_note_after=False,
                unique_grounded_note_after=0, rejected_note_after=0,
                first_person_attempt_forms=0, first_person_diagnostic_unavailable=0,
                literal_observed_verdict_matches=0, verdict_diagnostic_unavailable=0,
                missing_note_after=0, missing_note_executions=[],
                rejection_reasons=Counter(), records=[], action_diagnostics=[],
                generation_requests=0, missing_generation_outputs=0,
                slot_requests=0, slot_outputs=0, slot_nonempty_responses=0,
                slot_output_tokens=0, slot_output_bytes=0, slot_visible_prompt_tokens=0,
                child_output_bytes=0, child_output_chars=0, child_output_tokens=0,
                child_visible_prompt_tokens=0, teacher_presentations=0,
                teacher_text_occurrences=0, teacher_presented_tokens=0,
                generation_request_indices=[])


def _key(receipt):
    return (receipt.get("prompt_sha256"), receipt.get("output_sha256"), receipt.get("seed"))


def _arm(root, snapshot, tokenizer):
    mode = snapshot["config"]["mode"]
    raw_lines, rows = policy._lines((root / "ledger.jsonl").read_bytes())
    _, events = policy._lines((root / "generations.jsonl").read_bytes())
    _require(len(events) <= 100000, "generation event count exceeds CPU bound")
    receipts = policy._lesson_rows((root / "lesson_deliveries.jsonl").read_bytes())
    _require(len(receipts) == 1 and receipts[0]["mode"] == mode
             and receipts[0]["sleeps_done"] == 0, "fixed single teaching receipt required")
    teacher = receipts[0]["text"]
    dose = extraction._read(root / "teaching_dose.json")
    counts = {arm: len(tokenizer.encode(policy.lesson_block(arm, 0), add_special_tokens=False))
              for arm in ("lesson", "sham")}
    _require(dose.get("mode") == mode and dose.get("delivered_phases") == [0]
             and dose.get("text_sha256") == hashlib.sha256(teacher.encode()).hexdigest()
             and dose.get("actual_token_counts") == counts, "teacher dose/tokenizer mismatch")
    buckets = {episode: _bucket() for episode in snapshot["schedule"]}
    unassigned = _bucket()
    def bucket(episode):
        return buckets.get(episode, unassigned)

    requests, outputs = {}, {}
    for event in events:
        _require(event.get("kind") in ("request", "output"), "unknown generation event")
        index = event.get("request_index")
        _require(type(index) is int and index >= 0, "invalid generation request index")
        target = requests if event["kind"] == "request" else outputs
        _require(index not in target, "duplicate generation request/output index")
        target[index] = event
    _require(set(outputs) <= set(requests), "generation output without request")
    actual = defaultdict(list)
    for index, request in requests.items():
        output = outputs.get(index)
        if output is not None:
            actual[(request["prompt_sha256"], output["output_sha256"], request["seed"])].append(index)

    owners = defaultdict(set)
    actions, notes = defaultdict(list), defaultdict(list)
    for line, row in enumerate(rows):
        target = bucket(row.get("episode_id"))
        target["ledger_rows"] += 1
        if row["kind"] == "episode_occurrence":
            target["occurrences"] += 1
        if row["kind"] == "act":
            actions[row.get("execution_id")].append(line)
        if row["kind"] == "note_after":
            notes[row.get("execution_id")].append(line)
        if row["kind"] in ("thought", "act", "note_after"):
            indices = actual.get(_key(row.get("generation", {})), [])
            if len(indices) == 1:
                owners[indices[0]].add(row.get("episode_id"))

    def actual_output(row, ceiling):
        indices = actual.get(_key(row.get("generation", {})), [])
        if len(indices) != 1 or requests[indices[0]]["max_tokens"] != ceiling:
            return None
        return outputs[indices[0]]["text"]

    facts_by_line = {}
    for execution, indices in actions.items():
        for line in indices:
            action = rows[line]
            target = bucket(action.get("episode_id"))
            target["actions"] += 1
            text = actual_output(action, 400)
            wake_actions = [] if text is None else [match.group(2).strip()
                for match in formation.batch_loop._MARK.finditer(text) if match.group(1) == "ACT"]
            in_wake = action.get("action") in wake_actions
            detail = dict(record_line=line, execution_id=execution,
                          unique_execution=len(indices) == 1, in_actual_wake=in_wake)
            try:
                facts = policy.facts_from_act(action)
                target["feedback_valid_actions"] += 1
                target["measured_actions" if facts.measured else "unmeasured_actions"] += 1
                valid = facts.measured and in_wake and len(indices) == 1
                target["valid_acts"] += int(valid)
                detail.update(feedback_valid=True, measured=facts.measured, valid_act=valid,
                              observed_action=facts.action, displayed_score=facts.reported_score,
                              observed_verdict=facts.verdict)
                if in_wake and len(indices) == 1:
                    facts_by_line[line] = facts
            except policy.InvalidFeedback as error:
                target["invalid_feedback_actions"] += 1
                detail.update(feedback_valid=False, valid_act=False, reason=str(error))
            target["action_diagnostics"].append(detail)
        if not notes.get(execution):
            target = bucket(rows[indices[0]].get("episode_id") if len(indices) == 1 else None)
            target["missing_note_after"] += 1
            target["missing_note_executions"].append(execution)
            target["rejection_reasons"]["missing-note-after"] += 1

    for judgment in snapshot["result"]["judgments"]:
        line = judgment["record_line"]
        record = rows[line]
        target = bucket(record.get("episode_id"))
        target["note_after_records"] += 1
        strict = judgment["unique_grounded"] or judgment["reason"] == "duplicate-grounded-record"
        target["strict_faithful_note_after"] += int(strict)
        target["any_strict_faithful_note_after"] |= bool(strict)
        target["unique_grounded_note_after"] += int(judgment["unique_grounded"])
        target["rejected_note_after"] += int(not judgment["unique_grounded"])
        if not judgment["unique_grounded"]:
            target["rejection_reasons"][judgment["reason"]] += 1
        text = actual_output(record, 100)
        actual_note = text is not None and text == record.get("text")
        detail = dict(judgment, strict_faithful=strict, actual_slot_output=actual_note,
                      episode_id=record.get("episode_id"), source_observed=None,
                      record_sha256=policy._sha(raw_lines[line]), line_index_base=0,
                      child_text_sha256=policy._sha(text.encode()) if actual_note else None,
                      first_person_attempt_form=None, first_person_form_matches=None,
                      literal_observed_verdict_present=None, content_judgment=None)
        if actual_note:
            normalized = policy._normalize(text)
            matches = [match.group(0) for match in policy._ACTION.finditer(normalized)]
            detail.update(first_person_attempt_form=bool(matches), first_person_form_matches=matches)
            source_lines = actions.get(record.get("execution_id"), [])
            if len(source_lines) == 1:
                source_line = source_lines[0]
                source = rows[source_line]
                facts = facts_by_line.get(source_line)
                fields = ("episode_id", "execution_id", "tick", "action", "outcome", "score",
                          "occurrence_id", "occurrence_index")
                matched = all(field in source and field in record
                              and extraction._bytes(source[field]) == extraction._bytes(record[field])
                              for field in fields)
                if facts is not None and source_line < line and matched:
                    verdict = policy.judge_record(text, facts)
                    detail.update(source_observed=dict(source_line=source_line, action=facts.action,
                                  source_sha256=policy._sha(raw_lines[source_line]),
                                  displayed_score=facts.reported_score, verdict=facts.verdict),
                                  content_judgment=verdict["reason"],
                                  literal_observed_verdict_present=facts.verdict in text)
        target["first_person_attempt_forms"] += int(detail["first_person_attempt_form"] is True)
        target["first_person_diagnostic_unavailable"] += int(detail["first_person_attempt_form"] is None)
        target["literal_observed_verdict_matches"] += int(detail["literal_observed_verdict_present"] is True)
        target["verdict_diagnostic_unavailable"] += int(detail["literal_observed_verdict_present"] is None)
        target["records"].append(detail)

    from .model_backend import configured_generation_identity
    identity = configured_generation_identity(snapshot["config"]["model_path"], None)
    for index, request in requests.items():
        _require(request.get("source_identity") == identity and request.get("temperature") == .7
                 and request.get("max_tokens") in (100, 400)
                 and type(request.get("seed")) is int, "generation configuration mismatch")
        prompt = request["prompt"]
        rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                                                tokenize=False, add_generation_prompt=True)
        prompt_tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
        _require(request.get("rendered_prompt") == rendered
                 and request.get("prompt_sha256") == policy._sha(prompt.encode())
                 and request.get("prompt_tokens") == prompt_tokens,
                 "rendered prompt/tokenizer mismatch")
        occurrences = prompt.count(teacher)
        _require(occurrences >= 1 and request.get("teacher_presentations") == 1
                 and request.get("teacher_text_occurrences") == occurrences
                 and request.get("teacher_tokens") == counts[mode], "generation teacher dose mismatch")
        assigned = owners.get(index, set())
        target = bucket(next(iter(assigned)) if len(assigned) == 1 else None)
        target["generation_requests"] += 1
        target["generation_request_indices"].append(index)
        target["child_visible_prompt_tokens"] += prompt_tokens
        target["teacher_presentations"] += 1
        target["teacher_text_occurrences"] += occurrences
        target["teacher_presented_tokens"] += counts[mode]
        slot = request["max_tokens"] == 100
        target["slot_requests"] += int(slot)
        target["slot_visible_prompt_tokens"] += prompt_tokens if slot else 0
        output = outputs.get(index)
        if output is None:
            target["missing_generation_outputs"] += 1
        else:
            text = output["text"]
            _require(output.get("output_sha256") == policy._sha(text.encode()), "output hash mismatch")
            target["slot_outputs"] += int(slot)
            target["slot_nonempty_responses"] += int(slot and bool(text.strip()))
            target["child_output_bytes"] += len(text.encode())
            target["child_output_chars"] += len(text)
            output_tokens = len(tokenizer.encode(text, add_special_tokens=False))
            target["child_output_tokens"] += output_tokens
            target["slot_output_tokens"] += output_tokens if slot else 0
            target["slot_output_bytes"] += len(text.encode()) if slot else 0

    all_buckets = [*buckets.values(), unassigned]
    totals = {key: sum(target[key] for target in all_buckets)
              for key, value in unassigned.items() if type(value) is int}
    reasons = Counter()
    for target in all_buckets:
        reasons.update(target["rejection_reasons"])
    result = snapshot["result"]
    checks = dict(actions="n_actions", measured_actions="n_measured_actions",
                  unmeasured_actions="n_unmeasured_actions", invalid_feedback_actions="n_invalid_feedback_actions",
                  note_after_records="n_post_outcome_records", strict_faithful_note_after="n_grounded_records",
                  unique_grounded_note_after="n_unique_grounded_records", missing_note_after="n_missing_notes",
                  generation_requests="generation_requests", teacher_presentations="actual_teacher_presentations")
    _require(all(totals[key] == result[field] for key, field in checks.items())
             and reasons == Counter(result["rejection_reasons"]), "source accounting mismatch")
    totals["rejection_reasons"] = dict(reasons)
    return dict(mode=mode, formation_root=str(root), totals=totals, unassigned=unassigned,
                schedules=buckets, missing_occurrence_schedules=[episode for episode, target in buckets.items()
                                                               if target["occurrences"] == 0],
                teacher=dict(text=teacher, utf8_bytes=len(teacher.encode()),
                             sha256=policy._sha(teacher.encode()), tokenizer_tokens=counts[mode]),
                snapshot=snapshot)


def analyze_pair(lesson_root, sham_root, output_dir, *, seed=20260912, replicates=10000):
    """Validate completed roots and write fresh report/rows; never alter source artifacts."""
    _require(type(seed) is int and 0 <= seed <= 0xffffffff, "invalid bootstrap seed")
    _require(type(replicates) is int and 100 <= replicates <= MAX_BOOTSTRAP,
             "bootstrap replicates must be 100..20000")
    lesson_root, sham_root = extraction._path(lesson_root), extraction._path(sham_root)
    output = extraction._path(output_dir, fresh=True)
    paths = (lesson_root, sham_root, output)
    _require(not any(extraction._overlap(left, right) for index, left in enumerate(paths)
                     for right in paths[index + 1:]), "input/output roots overlap")
    source_paths = (Path(__file__), Path(extraction.__file__))
    source_hashes = {str(path.resolve()): extraction._hash(path) for path in source_paths}
    snapshots = [_bounded_snapshot(root) for root in (lesson_root, sham_root)]
    lesson, sham = snapshots
    _require(lesson["config"]["mode"] == "lesson" and sham["config"]["mode"] == "sham",
             "expected lesson then sham roots")
    _require(lesson["schedule"] == sham["schedule"] and len(set(lesson["schedule"])) == COUNT,
             "same 64 schedules required")
    _require({key: value for key, value in lesson["config"].items() if key not in ("mode", "out", "source_hashes")}
             == {key: value for key, value in sham["config"].items() if key not in ("mode", "out", "source_hashes")},
             "paired formation configurations differ")
    model = Path(lesson["config"]["model_path"])
    _require(not extraction._overlap(output, model), "output/model overlap")
    tokenizer = extraction._load_tokenizer(str(model))
    arms = [_arm(root, snapshot, tokenizer) for root, snapshot in zip((lesson_root, sham_root), snapshots)]
    rows = [dict(schedule_index=index, episode_id=episode,
                 lesson=arms[0]["schedules"][episode], sham=arms[1]["schedules"][episode],
                 any_grounded_difference=int(arms[0]["schedules"][episode]["any_strict_faithful_note_after"])
                                         - int(arms[1]["schedules"][episode]["any_strict_faithful_note_after"]),
                 strict_count_difference=arms[0]["schedules"][episode]["strict_faithful_note_after"]
                                         - arms[1]["schedules"][episode]["strict_faithful_note_after"])
            for index, episode in enumerate(lesson["schedule"])]
    paired = paired_summary(*[[row[mode]["strict_faithful_note_after"] for row in rows]
                              for mode in ("lesson", "sham")], seed=seed, replicates=replicates)
    report = dict(**BOUNDARY, status="COMPLETE", paired=paired,
                  accounting="each ledger row, ACT, NOTE_AFTER judgment and generation is assigned once "
                             "to a declared schedule or the explicit unassigned bucket; no dropped pairs",
                  missing_evidence="COMPLETE validates the producer's artifact manifest and recomputed result, "
                                   "not an assumption that every scheduled record exists. Zero observed records "
                                   "with missing evidence do not prove biological formation failure; inspect "
                                   "missing-occurrence schedules, missing notes/outputs and unassigned counts.",
                  diagnostics="valid ACT means unique execution with measured feedback and actual wake ACT, "
                              "not task success. First-person form and literal verdict presence are lexical only; "
                              "null means unavailable. content_judgment reuses the existing single-event judge. "
                              "A faithful record need not explicitly repeat the verdict. Duplicate-grounded "
                              "records count as strict faithful, but not unique; rejection counts include duplicates.",
                  token_diagnostics="child output tokens are retokenized exact output text, not runtime generated "
                                    "token IDs. Visible tokens sum rendered prompts including repeated history; "
                                    "not unique exposure. Unassigned generations remain in totals. "
                                    "Teacher tokens per presentation exclude chat wrapper tokens.",
                  arms={arm["mode"]: {key: value for key, value in arm.items() if key != "schedules"}
                        for arm in arms},
                  analysis_source_hashes=source_hashes)
    for root, snapshot in zip((lesson_root, sham_root), snapshots):
        _require(extraction._bytes(_bounded_snapshot(root)) == extraction._bytes(snapshot),
                 "formation changed during analysis")
    _require(source_hashes == {str(path.resolve()): extraction._hash(path) for path in source_paths},
             "analysis source changed during reduction")
    output.mkdir()
    formation._write(output / "report.json", report)
    with (output / "per_schedule.jsonl").open("xb") as target:
        for row in rows:
            target.write(extraction._bytes(row))
    (output / "per_schedule.jsonl").chmod(0o444)
    for arm in arms:
        with (output / (arm["mode"] + "_teacher.txt")).open("xb") as target:
            target.write(arm["teacher"]["text"].encode())
        (output / (arm["mode"] + "_teacher.txt")).chmod(0o444)
    formation._write(output / "artifact_hashes.json", dict(files={
        path.name: extraction._hash(path) for path in output.iterdir()}))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson-root", required=True, help="completed lesson formation directory")
    parser.add_argument("--sham-root", required=True, help="completed sham formation directory")
    parser.add_argument("--out", required=True, help="fresh output directory; parent must exist")
    parser.add_argument("--bootstrap-seed", type=int, default=20260912)
    parser.add_argument("--bootstrap-replicates", type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        report = analyze_pair(args.lesson_root, args.sham_root, args.out,
                              seed=args.bootstrap_seed, replicates=args.bootstrap_replicates)
    except (ValueError, OSError, policy.ReasoningGateError) as error:
        parser.exit(2, f"analysis refused: {error}\n")
    print(json.dumps(dict(status=report["status"], out=args.out, paired=report["paired"]), sort_keys=True))


if __name__ == "__main__":
    main()
