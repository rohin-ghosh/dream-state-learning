"""CPU-only compatible-habit material and pure saved-text scoring; no launch."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re

from . import fundamental_repetition_corpus as native
from . import fundamental_teaching_corpus as original
from . import fundamental_teaching_readout as readout
from . import rulegame_parenting_diagnostic as base
from . import train_adapter_v3 as trainer


SEEDS = (0, 1, 2)
ARMS = ("input_before", "input_after")
SOURCE_SHA256 = native.SOURCE_SHA256["teach"]
MAX_LEN = 512
CLAIM = "COMPATIBLE_AUTHORED_HABITS_WITH_REHEARSAL_NOT_PARENTING"
RECIPE = dict(lr=1e-4, rank=8, alpha=16, dropout=.05, epochs=4,
              batch_size=4, grad_accum=1, target_modules=list(trainer.ALL_PROJ),
              layers="all", bias="none", optimizer="adamw", max_steps=0,
              max_len=MAX_LEN, pack=False, chat_template=False, add_eos=True,
              overflow="truncate", shuffle_groups=True, seeds=list(SEEDS),
              initialization="ORIGINAL_TEACHING_PARENT_WEIGHT_ONLY_FRESH_OPTIMIZER",
              parent_experiments=["SEQ098", "SEQ099"], updates_per_fit=80)
LIMITS = ("Fixed 1e-4 before plasticity outcomes; three original teaching parents, not repetition or "
          "continuation descendants. Main must bind each original seed0/1/2 adapter before training. "
          "A is rehearsed: not unrehearsed retention or simultaneous-versus-sequential superiority. "
          "Shared exposed dev panel, not 96 independent learners or fresh confirmation. "
          "No arithmetic gain, reliable memory, parenting, child sleep, H1/H2 or launch authorization. "
          "Native equality is per-row token COUNT equality, not identical target token IDs. "
          "Overflow selector never permits dropped tokens; no material padding or fallback.")
require = base.require
encoded = original._encoded
digest = native.digest
native_tokenizer = base.native_tokenizer


def source_hashes():
    root = Path(__file__).resolve().parent
    names = ("fundamental_two_habit_corpus.py", "fundamental_teaching_corpus.py",
             "fundamental_teaching_readout.py", "fundamental_repetition_corpus.py",
             "train_adapter_v3.py", "rulegame_parenting_diagnostic.py", "reasoning_neutral_probe.py")
    return {name: base.digest(root / name) for name in names}


def panels():
    candidate = original.build_candidate()
    selected = readout.selected_cases()
    unrequested = [row for row in candidate["eval"] if row["id"] not in readout.CASE_IDS]
    require(len(selected) == 48 and len(unrequested) == 64, "original panel counts changed")
    expected_ids = tuple(f"eval-addition-{index:03d}" for index in range(32)) + tuple(
        f"eval-memory-{index:03d}-0" for index in range(16))
    require(readout.CASE_IDS == expected_ids, "original fixed48 case IDs changed")
    requests = readout.requests(selected)
    require(all(row["temperature"] == 0.0 and row["seed"] == 20260912 and row["max_tokens"] == 64
                for row in requests), "original decode changed")
    return dict(dev=selected, requests=requests,
                unrequested_case_ids=[row["id"] for row in unrequested],
                unrequested_sha256=digest(encoded(unrequested)))


def build_material(rows):
    """Preserve actual native source order/metadata; permute only arithmetic targets."""
    candidate = original.build_candidate()
    expected = candidate["train_teach"]
    events = {event["id"]: event for event in candidate["source_records"]}
    require(len(rows) == len(expected) == 80, "exactly 80 original teaching rows required")
    material = {arm: [] for arm in ARMS}
    inventory = []
    for index, (row, source) in enumerate(zip(rows, expected)):
        require(set(row) == {"spans", "group", "view", "order", "meta"}, "original native row shape changed")
        require(row["group"] == source["case_id"] and row["view"] == source["kind"] and
                type(row["order"]) is int and row["order"] == index and
                row["meta"] == dict(source_event_ids=source["source_event_ids"]),
                "source row/order/group/event binding changed")
        spans = row["spans"]
        require(isinstance(spans, list) and len(spans) == 2 and
                all(isinstance(span, list) and len(span) == 3 for span in spans), "invalid source spans")
        require(isinstance(spans[0][0], str) and bool(spans[0][0]) and
                spans[0][1] is False and spans[1][1] is True and
                spans[0][1:] == [False, "context"] and
                spans[1] == [source["response"], True, "authored_birth_target"],
                "original response/mask/category changed")
        event = events[source["source_event_ids"][0]]
        targets = {arm: source["response"] for arm in ARMS}
        if source["kind"] == "addition":
            left, right = event["left"], event["right"]
            require(type(left) is int and type(right) is int and event["sum"] == left + right,
                    "invalid source operands/sum")
            lines = [f"INPUT: {left}, {right}", f"PREDICT: {left + right}", f"ACT: {left + right}"]
            targets = dict(input_before="\n".join(lines), input_after="\n".join(lines[1:] + lines[:1]))
        else:
            require(source["kind"] == "memory" and source["response"] == event["color"],
                    "original memory target changed")
        require(sorted(targets[ARMS[0]].splitlines()) == sorted(targets[ARMS[1]].splitlines()),
                "paired line inventory differs")
        for arm in ARMS:
            item = copy.deepcopy(row)
            item["spans"][1][0] = targets[arm]
            material[arm].append(item)
        inventory.append(dict(source_row_index=index, case_id=source["case_id"], kind=source["kind"],
            source_event_ids=source["source_event_ids"], source_row_sha256=digest(encoded(row)),
            context_sha256=digest(spans[0][0].encode()), source_response=source["response"],
            rule="source_integer_addition_line_permutation" if source["kind"] == "addition" else "unchanged_source_color",
            ordered_lines={arm: targets[arm].splitlines() for arm in ARMS},
            line_inventory=sorted(targets[ARMS[0]].splitlines())))
    return dict(corpora=material, inventory=inventory, source_records=candidate["source_records"], panels=panels())


class TokenMismatch(ValueError):
    def __init__(self, report):
        super().__init__("per-row native token mismatch; stop and report Main, no padding or alternate material")
        self.report = report


def audit_native(rows, material, tokenizer):
    """Reuse V3 encoding/collation; retain actual IDs, labels and unequal-dose evidence."""
    require(material == build_material(rows), "material/provenance/panel changed")
    eos, pad = tokenizer.eos_token_id, tokenizer.pad_token_id
    require(type(eos) is int and eos >= 0 and type(pad) is int and pad >= 0, "native EOS/pad IDs required")
    require(tokenizer.encode(native.EOS, add_special_tokens=False) == [eos], "native EOS token binding differs")
    for row, source in zip(rows, original.build_candidate()["train_teach"]):
        context = tokenizer.apply_chat_template([dict(role="user", content=source["context"])],
                                                tokenize=False, add_generation_prompt=True)
        require(row["spans"][0][0] == context, "source differs from native single-user rendering")
    report = dict(arms={}, mismatches=[], tokenizer_class=type(tokenizer).__name__,
                  eos_token_id=eos, pad_token_id=pad, max_len=MAX_LEN, optimizer_update_groups={})
    if hasattr(tokenizer, "get_vocab"):
        report["tokenizer_vocab_sha256"] = digest(encoded(tokenizer.get_vocab()))
    original_encoded = native.encode_rows(rows, tokenizer, True)
    schedules = {}
    for arm in ARMS:
        items = material["corpora"][arm]
        segments = native.encode_rows(items, tokenizer, True)
        checks = []
        for index, (item, segment) in enumerate(zip(items, segments)):
            prefix = tokenizer.encode(item["spans"][0][0], add_special_tokens=False)
            response = tokenizer.encode(item["spans"][1][0], add_special_tokens=False)
            require(prefix and response and all(type(token) is int and token >= 0 for token in prefix + response),
                    "invalid actual native token IDs")
            target = response + [eos]
            require(eos not in response and len(segment.ids) <= MAX_LEN and segment.n_splits == 1,
                    "extra target EOS, splitting or overflow forbidden")
            require(segment.ids == prefix + target and segment.labels == [-100] * len(prefix) + target and
                    segment.n_target == len(target), "native context/mask/target/EOS boundaries differ")
            if item["view"] == "memory":
                for name in ("ids", "labels", "cats"):
                    require(getattr(segment, name) == getattr(original_encoded[index], name), "memory tokens changed")
            checks.append(dict(case_id=item["group"], context_token_ids=prefix, response_token_ids=response,
                input_ids=segment.ids, labels=segment.labels, input_tokens=len(segment.ids),
                target_tokens=segment.n_target, input_ids_sha256=digest(encoded(segment.ids)),
                labels_sha256=digest(encoded(segment.labels))))
        packs = trainer.pack_by_group(segments, MAX_LEN, pack=False)
        require(len(packs) == 80 and all(len(pack) == 1 for pack in packs), "packing/row count differs")
        orders = {}
        for seed in SEEDS:
            updates = []
            for epoch in range(RECIPE["epochs"]):
                ordered = trainer.epoch_order(packs, seed, epoch, shuffle_groups=True)
                for offset in range(0, len(ordered), RECIPE["batch_size"]):
                    batch_packs = ordered[offset:offset + RECIPE["batch_size"]]
                    batch = trainer.collate(batch_packs, pad)
                    width = max(len(pack[0].ids) for pack in batch_packs)
                    for batch_index, pack in enumerate(batch_packs):
                        segment = pack[0]
                        padding = width - len(segment.ids)
                        require(batch["input_ids"][batch_index] == segment.ids + [pad] * padding and
                                batch["labels"][batch_index] == segment.labels + [-100] * padding,
                                "batch collation changes content/masks")
                    updates.append([pack[0].group for pack in batch_packs])
            require(len(updates) == 80 and all(len(update) == 4 for update in updates), "update count differs")
            orders[str(seed)] = updates
        schedules[arm] = orders
        report["arms"][arm] = dict(rows=checks, totals={key: sum(row[key] for row in checks)
                                                      for key in ("input_tokens", "target_tokens")})
    require(schedules[ARMS[0]] == schedules[ARMS[1]], "paired optimizer group order differs")
    report["optimizer_update_groups"] = schedules[ARMS[0]]
    for before, after in zip(report["arms"][ARMS[0]]["rows"], report["arms"][ARMS[1]]["rows"]):
        require(before["case_id"] == after["case_id"] and before["context_token_ids"] == after["context_token_ids"],
                "paired case/prefix differs")
        if any(before[key] != after[key] for key in ("input_tokens", "target_tokens")):
            report["mismatches"].append(dict(case_id=before["case_id"],
                **{arm: {key: row[key] for key in ("input_tokens", "target_tokens")}
                   for arm, row in zip(ARMS, (before, after))}))
    if report["mismatches"]:
        raise TokenMismatch(report)
    return report


def prepare(teach, out, pins, model=None, tokenizer=None):
    """Export only after bound native audit; an injected tokenizer is fixture-only."""
    out, teach = Path(out), Path(teach)
    require(not out.exists() and not out.is_symlink(), "fresh output required")
    require(not teach.is_symlink() and teach.is_file(), "regular original teach source required")
    require(set(pins) == {"source_sha256", "source_code_sha256", "model_files"}, "exact source/code/model pins required")
    require(pins["source_sha256"] == SOURCE_SHA256 == base.digest(teach), "original native teach source hash mismatch")
    require(pins["source_code_sha256"] == source_hashes(), "source code pin mismatch")
    injected = tokenizer is not None
    require((model is None) == injected, "provide local model OR fixture tokenizer")
    if injected:
        require(pins["model_files"] == {}, "fixture cannot authenticate model pins")
    else:
        model = Path(model).expanduser().resolve(strict=True)
        destination = out.resolve()
        require(model.is_dir() and model != destination and model not in destination.parents and
                destination not in model.parents, "output overlaps local model")
        require(base.read(model / "config.json").get("model_type") == "qwen2", "expected Qwen base")
        require(bool(pins["model_files"]) and base.model_hashes(model) == pins["model_files"], "model/tokenizer pin mismatch")
        tokenizer = native_tokenizer(str(model))
    source = base.read(teach)
    require(set(source) == {"corpus"}, "unexpected native source document")
    material = build_material(source["corpus"])
    mismatch = None
    try:
        report = audit_native(source["corpus"], material, tokenizer)
    except TokenMismatch as error:
        report, mismatch = error.report, error
    require(base.digest(teach) == SOURCE_SHA256 and source_hashes() == pins["source_code_sha256"],
            "source changed during native audit")
    if not injected:
        require(base.model_hashes(model) == pins["model_files"], "model/tokenizer changed during audit")
    if mismatch is not None:
        out.mkdir(parents=True, exist_ok=False)
        base.write_json(out / "token_mismatch.json", dict(status="STOP_TOKEN_MISMATCH_REPORT_MAIN",
                        pins=pins, audit=report, inventory=material["inventory"],
                        model=str(model) if model is not None else None, tokenizer_injected=injected,
                        source_path=str(teach.resolve()), corpora_exported=False, fits_authorized=False))
        raise mismatch
    files = {f"{arm}.json": encoded(dict(corpus=material["corpora"][arm])) for arm in ARMS}
    files.update({"inventory.json": encoded(material["inventory"]), "source_records.json": encoded(material["source_records"]),
                  "panels.json": encoded(material["panels"]), "token_audit.json": encoded(report)})
    manifest = dict(status="FIXTURE_ONLY_NOT_NATIVE_VALIDATION" if injected else "NATIVE_TOKEN_MATCHED_NO_FIT_NO_LAUNCH",
        claim=CLAIM, limits=LIMITS, pins=pins, model=str(model) if model is not None else None,
        source_path=str(teach.resolve()), recipe=copy.deepcopy(RECIPE), fits_authorized=False,
        parent_adapter_bindings="MAIN_REQUIRED_ORIGINAL_SEQ098_099_TEACH_SEEDS_0_1_2_NOT_BOUND_BY_EXPORTER",
        counts=dict(rows_per_arm=80, arithmetic_per_arm=64, unchanged_memory_per_arm=16,
                    dev_cases=48, unrequested_cases=64, planned_fits=6, planned_updates=480,
                    planned_row_presentations=1920, planned_readout_calls=288, output_cap_tokens_not_usage=18432),
        sha256={name: digest(payload) for name, payload in files.items()})
    out.mkdir(parents=True, exist_ok=False)
    for name, payload in files.items():
        with (out / name).open("xb") as handle:
            handle.write(payload)
    base.write_json(out / "manifest.json", manifest)
    return manifest


def score_addition(text, left, right):
    """Strict form metrics on saved raw text; numeric success remains independent."""
    require(isinstance(text, str), "missing response is not a scientific zero")
    require(type(left) is int and type(right) is int, "source integer operands required")
    patterns = dict(INPUT=r"([+-]?[0-9]+)[ \t]*,[ \t]*([+-]?[0-9]+)",
                    PREDICT=r"([+-]?[0-9]+)", ACT=r"([+-]?[0-9]+)")
    fields = {label: [] for label in patterns}
    lines = [line for line in text.splitlines() if line.strip(" \t")]
    recognized = 0
    for index, line in enumerate(lines):
        for label, pattern in patterns.items():
            match = re.fullmatch(r"[ \t]*" + label + r"[ \t]*:[ \t]*" + pattern + r"[ \t]*", line)
            if re.match(r"[ \t]*" + label + r"\b", line):
                fields[label].append((index, tuple(int(value) for value in match.groups()) if match else None))
                recognized += int(match is not None)
    strict = recognized == len(lines) and all(len(values) <= 1 for values in fields.values())
    values = {label: matches[0] if len(matches) == 1 and matches[0][1] is not None else None
              for label, matches in fields.items()}
    action, prediction, inputs = values["ACT"], values["PREDICT"], values["INPUT"]
    form_a = bool(strict and prediction and action and prediction[0] < action[0])
    form_b_order = bool(strict and inputs and action and inputs[0] < action[0])
    input_correct = bool(inputs and inputs[1] == (left, right))
    form_b = form_b_order and input_correct
    joint = bool(len(lines) == 3 and form_a and form_b and inputs[0] < prediction[0])
    return dict(raw_text=text, left=left, right=right, expected=left + right,
                strict_lines=strict, joint=joint, form_a=form_a, form_b=form_b,
                form_b_order=form_b_order, input_correct=input_correct,
                prediction_correct=bool(prediction and prediction[1][0] == left + right),
                act_success=bool(action and action[1][0] == left + right),
                field_counts={label: len(matches) for label, matches in fields.items()},
                original_score=readout.score_addition(text, left + right))


def score_response(case_id, text):
    """Score one existing dev response with its original source key; never request a case."""
    require(isinstance(text, str), "missing response is not a scientific zero")
    fixed = {case["id"]: case for case in panels()["dev"]}
    require(isinstance(case_id, str) and case_id in fixed, "only original48 dev cases may be scored")
    case = fixed[case_id]
    if case["kind"] == "addition":
        events = {event["id"]: event for event in original.build_candidate()["source_records"]}
        event = events[case["source_event_ids"][0]]
        score = score_addition(text, event["left"], event["right"])
    else:
        score = readout.score_memory(text, case["expected"])
    return dict(case_id=case_id, source_event_ids=case["source_event_ids"], kind=case["kind"], score=score)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teach", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--pins", required=True, type=Path,
                        help="JSON with source_sha256, source_code_sha256 and actual model_files")
    args = parser.parse_args(argv)
    result = prepare(args.teach, args.out, base.read(args.pins), model=args.model)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
