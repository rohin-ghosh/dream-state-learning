"""Fixed ACT-only interference material and CPU native-token audit; no training."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

from . import fundamental_teaching_corpus as original
from . import train_adapter_v3 as trainer


SEED = 20260918
PHASES = 4
ROWS_PER_PHASE = 16
MAX_LEN = 512
CLAIM = "TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP"
RECIPE = dict(rank=8, alpha=16, dropout=.05, epochs_per_phase=4, batch_size=4, grad_accum=1,
              target_modules=list(trainer.ALL_PROJ), layers="all", bias="none", optimizer="adamw", max_steps=0,
              pack=False, chat_template=False, add_eos=True, max_len=MAX_LEN,
              updates_per_phase=16, phases=4, total_updates=64,
              learning_rates=[0.0, 3e-5, 1e-4], sentinel_seed=0, conditional_replication_seeds=[1, 2],
              initialization="WEIGHT_WARM_START_FRESH_OPTIMIZER",
              adapter_rule="same single adapter weights carried from prior phase; fresh optimizer every phase")
LIMITS = ("ACT-only competing targets may overwrite the prediction habit. This is task-only interference, "
          "not evidence of time-alone forgetting, passive fading, or child sleep. Identical material across "
          "rates and trainer seeds. Main runs seed0 first; paired seeds1/2 only if sound. No experiment is authorized.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(content):
    return hashlib.sha256(content).hexdigest()


def source_hashes():
    root = Path(__file__).resolve().parent
    names = ("fundamental_continuation_corpus.py", "fundamental_teaching_corpus.py", "train_adapter_v3.py",
             "rulegame_parenting_diagnostic.py", "reasoning_neutral_probe.py")
    return {name: digest((root / name).read_bytes()) for name in names}


def original_pairs():
    sources = [row for row in original.build_candidate()["source_records"] if row["kind"] == "addition"]
    require(len(sources) == 128, "original 128-pair exclusion inventory changed")
    pairs = set()
    for source in sources:
        left, right = source["left"], source["right"]
        require(type(left) is int and type(right) is int and 0 <= left <= right < 20 and source["sum"] == left + right,
                "invalid original integer-addition source")
        pairs.add((min(left, right), max(left, right)))
    require(len(pairs) == 128, "duplicate original unordered pair")
    return pairs


def build_candidate():
    excluded = original_pairs()
    remaining = [(left, right) for left in range(20) for right in range(left, 20) if (left, right) not in excluded]
    require(len(remaining) == 82, "expected exactly 82 unused unordered operand pairs")
    random.Random(SEED).shuffle(remaining)
    selected = remaining[:PHASES * ROWS_PER_PHASE]
    phases, sources, derivations = [], [], []
    for phase_index in range(PHASES):
        phase_id = f"continuation-phase-{phase_index + 1:02d}"
        records = []
        for index, (left, right) in enumerate(selected[phase_index * ROWS_PER_PHASE:(phase_index + 1) * ROWS_PER_PHASE]):
            record_id = f"{phase_id}-addition-{index:03d}"
            source_id = f"source-{record_id}"
            response = f"ACT: {left + right}"
            sources.append(dict(id=source_id, phase_id=phase_id, kind="addition", left=left, right=right,
                                sum=left + right, origin="generated_integer_addition", generation_seed=SEED))
            records.append(dict(id=record_id, phase_id=phase_id, kind="addition", source_event_ids=[source_id],
                                context=original.addition_context(left, right), response=response, expected=left + right))
            derivations.append(dict(record_id=record_id, phase_id=phase_id, source_event_ids=[source_id],
                                    rule="integer_addition_ACT_only", target=response))
        phases.append(dict(id=phase_id, records=records))
    return dict(manifest=dict(status="CPU_RAW_MATERIAL_ONLY", claim=CLAIM, limitations=LIMITS, generation_seed=SEED,
                             selection="lexicographic unused unordered pairs; one fixed shuffle; first64; four consecutive blocks",
                             counts=dict(original_excluded=128, unused_pool=82, selected=64, left_unused=18,
                                         phases=4, rows_per_phase=16), recipe=copy.deepcopy(RECIPE),
                             model_calls=0, training_calls=0, gpu_calls=0, new_evaluation_cases=0),
                phases=phases, source_records=sources, derivations=derivations,
                exclusion=dict(scope="ALL original train and eval addition pairs, including confirmation and reversal",
                               unordered_pairs=[list(pair) for pair in sorted(excluded)]))


def validate_candidate(candidate):
    sources = {row["id"]: row for row in candidate["source_records"]}
    derivations = {row["record_id"]: row for row in candidate["derivations"]}
    require(len(sources) == len(candidate["source_records"]) == len(derivations) == len(candidate["derivations"]) == 64,
            "source/derivation cardinality or uniqueness differs")
    excluded, seen, records = original_pairs(), set(), set()
    require(len(candidate["phases"]) == PHASES, "exactly four phases required")
    for phase in candidate["phases"]:
        require(len(phase["records"]) == ROWS_PER_PHASE, "exactly 16 records per phase required")
        for row in phase["records"]:
            require(row["id"] not in records and len(row["source_event_ids"]) == 1, "duplicate record or ambiguous source")
            records.add(row["id"])
            source = sources[row["source_event_ids"][0]]
            left, right = source["left"], source["right"]
            require(type(left) is int and type(right) is int and 0 <= left <= right < 20, "invalid integer operands")
            pair = (min(left, right), max(left, right))
            require(pair not in excluded and pair not in seen, "original/reversed/repeated operand pair")
            seen.add(pair)
            require(source["sum"] == row["expected"] == left + right and row["response"] == f"ACT: {left + right}" and
                    row["context"] == original.addition_context(left, right), "sourced key/context/ACT-only target mismatch")
            require(source["phase_id"] == row["phase_id"] == phase["id"], "source/record phase mismatch")
            require(derivations[row["id"]] == dict(record_id=row["id"], phase_id=phase["id"],
                    source_event_ids=row["source_event_ids"], rule="integer_addition_ACT_only", target=row["response"]),
                    "derivation binding mismatch")
    require(candidate == build_candidate(), "fixed selection/order/recipe/provenance differs")
    return dict(valid=True, distinct_new_pairs=len(seen), original_pairs_excluded=len(excluded),
                phases=PHASES, rows_per_phase=ROWS_PER_PHASE, claim=CLAIM)


def export_native(candidate, tokenizer):
    validation = validate_candidate(candidate)
    eos = getattr(tokenizer, "eos_token_id", None)
    pad = getattr(tokenizer, "pad_token_id", None)
    pad = eos if pad is None else pad
    require(type(eos) is int and eos >= 0 and type(pad) is int and pad >= 0, "actual EOS/pad token IDs required")
    corpora, audits = {}, {}
    for phase in candidate["phases"]:
        items, checks, segments = [], [], []
        for index, row in enumerate(phase["records"]):
            messages = [dict(role="user", content=row["context"])]
            context = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            require(isinstance(context, str) and bool(context), "missing native user-template rendering")
            prefix = tokenizer.encode(context, add_special_tokens=False)
            response_ids = tokenizer.encode(row["response"], add_special_tokens=False)
            require(isinstance(prefix, list) and isinstance(response_ids, list) and prefix and response_ids and
                    all(type(token) is int and token >= 0 for token in prefix + response_ids), "invalid actual native token IDs")
            target = response_ids + [eos]
            require(len(prefix) + len(target) <= MAX_LEN, "native example exceeds 512; no truncation/splitting allowed")
            item = dict(spans=[[context, False, "context"], [row["response"], True, "authored_task_only_target"]],
                        group=row["id"], view="addition", order=index,
                        meta=dict(record_id=row["id"], phase_id=phase["id"], source_event_ids=row["source_event_ids"][:]))
            normalized = trainer.normalize_items([item])[0]
            parts = trainer.encode_item_segments(normalized, tokenizer, MAX_LEN, False, True, index)
            require(len(parts) == 1 and parts[0].n_splits == 1 and
                    parts[0].context_dropped == parts[0].target_dropped == 0, "native split/truncation forbidden")
            batch = trainer.collate([parts], pad)
            labels = [-100] * len(prefix) + target
            require(batch["input_ids"] == [prefix + target] and batch["labels"] == [labels] and
                    batch["n_tokens"] == len(prefix + target) and batch["n_target"] == len(target),
                    "native V3 source/label/EOS boundary mismatch")
            checks.append(dict(record_id=row["id"], phase_id=phase["id"], source_event_ids=row["source_event_ids"][:],
                messages=messages, rendered_context=context, response=row["response"], prefix_token_ids=prefix,
                response_token_ids=response_ids, eos_token_id=eos, input_ids=prefix + target, labels=labels,
                input_tokens=len(prefix + target), context_tokens=len(prefix), target_tokens=len(target),
                input_ids_sha256=digest(encoded(prefix + target)), labels_sha256=digest(encoded(labels))))
            items.append(item)
            segments.append(parts[0])
        packs = trainer.pack_by_group(segments, MAX_LEN, pack=False)
        require(len(packs) == 16 and all(len(pack) == 1 for pack in packs), "one example per sequence required")
        for offset in range(0, len(packs), 4):
            batch = trainer.collate(packs[offset:offset + 4], pad)
            width = max(len(pack[0]) for pack in packs[offset:offset + 4])
            for index, pack in enumerate(packs[offset:offset + 4]):
                segment = pack[0]
                padding = width - len(segment)
                require(batch["input_ids"][index] == segment.ids + [pad] * padding and
                        batch["labels"][index] == segment.labels + [-100] * padding,
                        "batch4 native padding/label mask differs")
        totals = {key: sum(row[key] for row in checks) for key in ("input_tokens", "context_tokens", "target_tokens")}
        corpora[phase["id"]] = dict(corpus=items)
        audits[phase["id"]] = dict(rows=checks, per_epoch=totals,
            four_epochs={key: 4 * value for key, value in totals.items()}, examples=16, updates=16,
            padding_scope="token counts exclude masked batch padding; batching may vary by trainer seed")
    totals = {key: sum(audit["four_epochs"][key] for audit in audits.values())
              for key in ("input_tokens", "context_tokens", "target_tokens")}
    return dict(corpora=corpora, audit=dict(validation=validation, phases=audits, four_phase_four_epoch_totals=totals,
                eos_token_id=eos, pad_token_id=pad, max_len=MAX_LEN, packing=False, truncation=False,
                tokenizer_class=type(tokenizer).__module__ + "." + type(tokenizer).__name__,
                total_updates=64, update_counts_scope="intended finite completed training; not observed optimizer updates",
                model_calls=0, training_calls=0, gpu_calls=0))


def _fresh(path):
    path = Path(path).expanduser()
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"fresh output required: {path}")
    return path


def _write(out, files, manifest):
    root = _fresh(out)
    root.mkdir()
    for name, content in files.items():
        with (root / name).open("xb") as target:
            target.write(content)
    manifest = dict(manifest, sha256={name: digest(content) for name, content in files.items()})
    with (root / "manifest.json").open("xb") as target:
        target.write(encoded(manifest))
    return manifest


def emit_candidate(out):
    _fresh(out)
    sources = source_hashes()
    candidate = build_candidate()
    validation = validate_candidate(candidate)
    require(sources == source_hashes(), "source changed during generation")
    return _write(out, {"candidate.json": encoded(candidate)},
                  dict(candidate["manifest"], source_hashes=sources, validation=validation, native_token_audit=False))


def prepare(out, model=None, tokenizer=None):
    destination = _fresh(out).resolve()
    sources = source_hashes()
    injected = tokenizer is not None
    require((model is None) == injected, "provide either a local model path or an injected tokenizer, not both")
    model_files = {}
    if not injected:
        from . import rulegame_parenting_diagnostic as base
        model = Path(model).expanduser().resolve(strict=True)
        require(model.is_dir() and destination != model and model not in destination.parents and
                destination not in model.parents, "output overlaps model or model is not a local directory")
        model_files = base.model_hashes(model)
        tokenizer = base.native_tokenizer(str(model))
    candidate = build_candidate()
    exported = export_native(candidate, tokenizer)
    files = {"candidate.json": encoded(candidate), "token_audit.json": encoded(exported["audit"])}
    for phase_id, value in exported["corpora"].items():
        files[phase_id + ".json"] = encoded(value)
    if not injected:
        require(base.model_hashes(model) == model_files, "model/tokenizer bytes changed during CPU audit")
    require(sources == source_hashes(), "source changed during CPU audit")
    status = "INJECTED_TOKENIZER_AUDIT_NOT_AUTHENTICATED_NATIVE_EVIDENCE" if injected else "NATIVE_V3_TOKEN_AUDIT_COMPLETE"
    return _write(out, files, dict(candidate["manifest"], status=status, source_hashes=sources,
        model=str(model) if model is not None else None, model_files=model_files,
        native_token_audit=not injected, tokenizer_injected=injected,
        token_totals=exported["audit"]["four_phase_four_epoch_totals"],
        phase_corpora={phase_id: phase_id + ".json" for phase_id in exported["corpora"]}))


def verify(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    require(manifest["source_hashes"] == source_hashes(), "source hashes changed")
    expected = manifest["sha256"]
    require({path.name for path in root.iterdir()} == set(expected) | {"manifest.json"}, "artifact cardinality differs")
    require(all(Path(name).name == name and not (root / name).is_symlink() and
                digest((root / name).read_bytes()) == value for name, value in expected.items()), "artifact bytes changed")
    return validate_candidate(json.loads((root / "candidate.json").read_text()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("emit", "audit-native", "verify"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args(argv)
    if args.stage == "verify":
        require(args.root is not None, "--root required")
        result = verify(args.root)
    else:
        require(args.out is not None, "--out required")
        if args.stage == "audit-native":
            require(args.model is not None, "--model local path required")
            result = prepare(args.out, model=args.model)
        else:
            result = emit_candidate(args.out)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
