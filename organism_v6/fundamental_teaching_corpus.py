"""Bounded, teacher-authored CPU-only candidate material; never runs a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random


SEED = 20260912
STATUS = "CANDIDATE_CPU_ONLY"
TOKEN_STATUS = "NATIVE_TOKEN_MATCH_PENDING"
COLORS = ("blue", "green", "red", "yellow")
RESULT_LABEL_VARIANTS = ("RESULT", "COMPUTED_RESULT", "RESULT_SUM", "COMPUTED")
MEMORY_QUESTIONS = (
    "Recall the logged color of {device}.",
    "What color was recorded for {device}?",
)
README = """# Fundamental post-training toy positive-control candidate

Status: CANDIDATE_CPU_ONLY. Main's proposal informed by message15, seed 20260912.
This is candidate material, not a scientific ruling or completed substrate.
It tests low-level behavioral adherence, NOT prediction intelligence, parenting
efficacy, H1/H2, or absence of prior exposure. No clean-lineage claim is made.
No sleep, parented life, fitting, model output, tokenizer, or GPU execution.

## Teaching protocol (metadata only, NOT an evaluation prompt)
Teach: compute a correct prediction BEFORE acting. For addition, write PREDICT
then ACT, both with the correct sum. Example: Add 20 and 21 gives
PREDICT: 41
ACT: 41
Control: act correctly, then state the computed result AFTER the action.
The same example gives
ACT: 41
RESULT: 41
This out-of-range illustration is protocol metadata, not a corpus case.
Device questions teach arbitrary logged colors; answer with the recorded color,
or unknown for a device with no recorded color. Both arms teach identical facts.
These instructions and examples are separate metadata: the emitter NEVER adds
them to train/eval contexts. Any later use as training text requires a new audit.

## Fixed construction and future native audit
One local Random(20260912) shuffles lexicographic operand pairs with left <= right
in 0..19. The first 64 are training and next 64 evaluation, disjoint even under
operand reversal. Then shuffle four copies of each color, the combined training
case order, and the combined evaluation order, in that sequence.
Training: 64 arithmetic + 16 identical device QA records per arm.
Evaluation: 64 arithmetic + 32 fresh recall paraphrases + 16 untaught probes.
Unknown means absent from this generated log, not a real-world device property.
Evaluation contexts contain no teaching reminders, examples, or answer facts.
Arithmetic expected sums are task-only answer keys, not mandated response text.

NATIVE_TOKEN_MATCH_PENDING: raw context/response segments only; no token counts,
rendering, truncation, padding, or fitting. Main must audit actual native template,
loss boundaries, special tokens and counts before any model output. If the
default RESULT label differs in counts, select the FIRST globally matching label
in RESULT, COMPUTED_RESULT, RESULT_SUM, COMPUTED order, comparing every paired arithmetic
record, and record the native evidence. All variants truthfully name the sum.
COMPUTED was added after the first native CPU-only audit found no match among
the original three; tokenizer inspection found three pieces, like PREDICT.
No model output informed that preparation amendment. Do not select per case
or use model outputs. If none matches, report unresolved;
do not claim matching or silently alter/pad/truncate material. The helper merely
constructs a requested label; it does not choose, count, render, or authorize it.
"""


def addition_context(left, right):
    return f"Add {left} and {right}.\nSubmit the sum using ACT: <integer>."


def arithmetic_response(left, right, arm, result_label="RESULT"):
    if arm not in ("teach", "control"):
        raise ValueError("arm must be teach or control")
    if result_label not in RESULT_LABEL_VARIANTS:
        raise ValueError("result label must be predeclared")
    total = left + right
    if arm == "teach":
        return f"PREDICT: {total}\nACT: {total}"
    return f"ACT: {total}\n{result_label}: {total}"


def raw_segments(row):
    """Return immutable (raw text, target-loss flag) pairs, without rendering."""
    return ((row["context"], False), (row["response"], True))


def build_candidate():
    """Pure fixed candidate, including every generated source and derivation."""
    rng = random.Random(SEED)
    pairs = [(left, right) for left in range(20) for right in range(left, 20)]
    rng.shuffle(pairs)
    sources, derivations, training, evaluation = [], [], [], []
    for index, (left, right) in enumerate(pairs[:128]):
        split = "train" if index < 64 else "eval"
        case_id = f"{split}-addition-{index % 64:03d}"
        source_id = f"source-addition-{index:03d}"
        sources.append(dict(id=source_id, kind="addition", left=left, right=right,
                            sum=left + right, origin="generated_integer_addition"))
        row = dict(id=case_id, kind="addition", source_event_ids=[source_id],
                   context=addition_context(left, right))
        if split == "train":
            training.append((row, (left, right)))
        else:
            evaluation.append(dict(row, expected=left + right))

    colors = list(COLORS) * 4
    rng.shuffle(colors)
    taught_devices = [f"device-{index:03d}" for index in range(16)]
    sources.append(dict(id="source-log-inventory", kind="closed_log_inventory",
                        device_ids=taught_devices, origin="generated_log_inventory"))
    for index, (device, color) in enumerate(zip(taught_devices, colors)):
        source_id = f"source-memory-{index:03d}"
        sources.append(dict(id=source_id, kind="device_color", device=device, color=color,
                            text=f"The log records {device} as {color}.",
                            origin="seeded_arbitrary_assignment"))
        training.append((dict(id=f"train-memory-{index:03d}", kind="memory",
                              device=device, source_event_ids=[source_id],
                              context=f"Which color does the log assign to {device}?"), color))
        for paraphrase, template in enumerate(MEMORY_QUESTIONS):
            evaluation.append(dict(id=f"eval-memory-{index:03d}-{paraphrase}",
                                   kind="memory_recall", device=device,
                                   context=template.format(device=device), expected=color,
                                   source_event_ids=[source_id]))
    for index in range(16, 32):
        device = f"device-{index:03d}"
        evaluation.append(dict(id=f"eval-unknown-{index:03d}", kind="memory_unknown",
                               device=device, context=MEMORY_QUESTIONS[1].format(device=device),
                               expected="unknown", source_event_ids=["source-log-inventory"]))
    rng.shuffle(training)
    rng.shuffle(evaluation)
    arms = {"teach": [], "control": []}
    for base, value in training:
        for arm, records in arms.items():
            response = (arithmetic_response(*value, arm) if base["kind"] == "addition"
                        else value)
            row = dict(base, id=f"{base['id']}-{arm}", case_id=base["id"], response=response)
            records.append(row)
            derivations.append(dict(record_id=row["id"], source_event_ids=row["source_event_ids"],
                                    rule=(f"integer_addition_{arm}_order" if base["kind"] == "addition"
                                          else "copy_source_color"), target=response))
    for row in evaluation:
        rule = {"addition": "integer_addition", "memory_recall": "copy_source_color",
                "memory_unknown": "device_absent_from_closed_log"}[row["kind"]]
        derivations.append(dict(record_id=row["id"], source_event_ids=row["source_event_ids"],
                                rule=rule, target=row["expected"]))
    manifest = dict(
        status=STATUS, seed=SEED, native_token_match=TOKEN_STATUS,
        selected_result_label="RESULT", result_label_variants=list(RESULT_LABEL_VARIANTS),
        counts=dict(train_per_arm=80, train_arithmetic_per_arm=64, train_memory_per_arm=16,
                    eval_arithmetic=64, eval_memory_recall=32, eval_memory_unknown=16,
                    eval_total=112, source_events=len(sources), target_derivations=len(derivations)),
        format="raw_context_response_no_rendering", protocol="README.md",
        source_records="source_records.json", audit="audit.json",
        claim="candidate_toy_low_level_behavioral_adherence_only",
        boundary=dict(model_calls=0, tokenizer_calls=0, gpu_calls=0, fitting=False,
                      sleep=False, parented_life=False, scientific_ruling=False,
                      prior_exposure_absence_claim=False, clean_lineage_claim=False,
                      completed_substrate=False, prediction_intelligence_claim=False,
                      parenting_efficacy_claim=False, h1_h2_claim=False),
    )
    return dict(manifest=manifest, train_teach=arms["teach"], train_control=arms["control"],
                eval=evaluation, source_records=sources,
                audit=dict(source_events=sources, target_derivations=derivations,
                           protocol_example=dict(left=20, right=21, sum=41,
                                                 derivation="integer_addition", emitted_case=False)))


def _encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def candidate_files():
    """Pure deterministic bytes; no native template or tokenizer involvement."""
    candidate = build_candidate()
    files = {f"{name}.json": _encoded(value) for name, value in candidate.items()
             if name != "manifest"}
    files["README.md"] = README.encode("utf-8")
    manifest = dict(candidate["manifest"], sha256={
        name: hashlib.sha256(content).hexdigest() for name, content in files.items()})
    files["manifest.json"] = _encoded(manifest)
    return files


def emit_candidate(output):
    """Require a fresh directory and exclusive files; preserve partial failures."""
    files = candidate_files()
    output = Path(output)
    output.mkdir(exist_ok=False)
    for name, content in files.items():
        with (output / name).open("xb") as stream:
            stream.write(content)
    return json.loads(files["manifest.json"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest = emit_candidate(args.output)
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
