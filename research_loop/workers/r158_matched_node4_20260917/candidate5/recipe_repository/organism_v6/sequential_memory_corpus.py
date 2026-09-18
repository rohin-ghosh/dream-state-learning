"""Fixed-budget sequential authored memory material, without a runner or model loader."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import json
from pathlib import Path

from organism_v6 import varied_memory_replay_corpus as prior


PROTOCOL = "AUTHORED_SEQUENTIAL_MEMORY_FIXED_BUDGET_V1"
ARMS = ("R", "NEW_ONLY")
CYCLES = ("1", "2")
STATES = ("S0", "R1", "NEW_ONLY1", "R2", "NEW_ONLY2")
BANK_STARTS = {"B1": 100, "B2": 200}
MAP_DOMAINS = {"B1": "sequential-authored-bank-one-20260912",
              "B2": "sequential-authored-bank-two-20260912"}
SEED, EPOCHS, BATCH_SIZE, MAX_LEN = 0, 10, 4, 512
READOUT_SEED, MAX_TOKENS = 20260912, 64
require, encoded, digest = prior.require, prior.encoded, prior.digest
trainer, original = prior.trainer, prior.original
RECIPE = {key: copy.deepcopy(value) for key, value in prior.RECIPE.items()
          if key not in ("initialization", "forbidden_parent", "presentations_per_original_source")}
RECIPE.update(allowed_seeds=[SEED], seed=SEED,
    initialization="IMMEDIATE_PRECEDING_ADAPTER_WEIGHTS_FRESH_OPTIMIZER_EACH_CYCLE",
    intended_updates=320, initial_checkpoint_seed=0, initial_checkpoint_arm="FOUR_VIEW",
    initial_checkpoint_updates=400, cumulative_steps=[400, 720, 1040],
    active_adapters=1, restore_optimizer=False,
    parent_binding="DEFERRED_TO_RUNNER_NOT_VALIDATED_BY_MATERIAL_EXPORT")
LIMITATIONS = [
    "Authored diagnostic facts, not child experience; novelty only against bound sources, not base pretraining.",
    "Fixed-budget allocation, NOT new-dose matched: R current-new20 versus NEW_ONLY40 presentations/fact/fit.",
    "B1 acquisition histories differ; M0 is primary old-content endpoint, B1 separately reported.",
    "Token-averaged loss is not reweighted; half the rows need not mean half the target mass.",
    "Input/padded compute equality must be measured, not inferred from target matching.",
    "Material and CPU callbacks only: no observed writes, utility, parenting, or mechanism claim.",
    "No clean lineage, G3/P1/G5/H1/H2 claims; origin UNRESOLVED_LOCAL_HASHES_ONLY.",
    "Parent/base/tokenizer identity, warm initialization, finite fits and custody remain runner obligations.",
    "Readout surfaces share facts, not independent factual trials; missing results are not zeros.",
]


def source_hashes():
    return prior.source_hashes() | {Path(__file__).name: digest(Path(__file__).read_bytes())}


def _materials():
    originals = prior.original_rows()
    selected = set(prior.MEMORY_IDS + prior.ADDITION_IDS)
    rows = {}
    for index, source in enumerate(originals):
        if source["case_id"] in selected:
            rows[source["case_id"]] = dict(copy.deepcopy(source),
                bank="M0" if source["kind"] == "memory" else "ARITHMETIC",
                source_record_id=source["id"], source_row_index=index,
                source_row_sha256=digest(encoded(source)))
    banks = {"M0": [rows[key] for key in prior.MEMORY_IDS]}
    events = {event for row in rows.values() for event in row["source_event_ids"]}
    sources = [copy.deepcopy(event) for event in original.build_candidate()["source_records"]
               if event["id"] in events]
    for bank, start in BANK_STARTS.items():
        domain = MAP_DOMAINS[bank]
        permutation = sorted(range(16), key=lambda index: digest(f"{domain}:{index:02d}".encode()))
        colors = {index: original.COLORS[position % 4] for position, index in enumerate(permutation)}
        bank_rows = []
        for index in range(16):
            device = f"device-{start + index:03d}"
            event_id = f"sequential-v1-source-{device}"
            sources.append(dict(id=event_id, kind="device_color", device=device, color=colors[index],
                text=f"The log records {device} as {colors[index]}.",
                origin="authored_diagnostic_not_child_experience", bank=bank, map_domain=domain))
            source = dict(id=f"sequential-v1-train-{device}", case_id=f"sequential-v1-train-{device}",
                kind="memory", device=device, source_event_ids=[event_id],
                context=prior.MEMORY_TEMPLATES[0].format(device=device), response=colors[index])
            bank_rows.append(dict(source, bank=bank, source_record_id=source["id"], source_row_index=None,
                source_row_sha256=digest(encoded(source))))
        sources.append(dict(id=f"sequential-v1-inventory-{bank}", kind="authored_bank_inventory",
            bank=bank, device_ids=[row["device"] for row in bank_rows],
            origin="authored_diagnostic_not_child_experience", map_domain=domain,
            permutation=permutation, assignment_rule="sort indices by SHA256(domain:two-digit-index); COLORS[position % 4]"))
        banks[bank] = bank_rows
    return banks, [rows[key] for key in prior.ADDITION_IDS], sources


def _cases(banks):
    cases = []
    for bank, rows in banks.items():
        for row in rows:
            for surface, template in (("exact", prior.MEMORY_TEMPLATES[0]), ("dev", original.MEMORY_QUESTIONS[0])):
                cases.append(dict(id=f"sequential-v1-readout-{bank}-{row['device']}-{surface}",
                    kind="memory_recall", bank=bank, surface=surface, device=row["device"],
                    source_event_ids=row["source_event_ids"][:], context=template.format(device=row["device"]),
                    expected=row["response"], introduced_cycle={"M0": 0, "B1": 1, "B2": 2}[bank]))
    indexed = {row["id"]: row for row in original.build_candidate()["eval"]}
    cases.extend(copy.deepcopy(indexed[f"eval-addition-{index:03d}"]) for index in range(32))
    return cases


def build_candidate():
    """Return deterministic raw rows; neither readout outputs nor checkpoint scores are inputs."""
    banks, additions, sources = _materials()
    cycles = {}
    for cycle in CYCLES:
        current = banks[f"B{cycle}"]
        cycles[cycle] = {}
        for arm in ARMS:
            rows = []
            for color_index, color in enumerate(original.COLORS):
                new = [row for row in current if row["response"] == color]
                old = [row for row in banks["M0"] if row["response"] == color]
                replay = old * 2 if cycle == "1" else old + [row for row in banks["B1"] if row["response"] == color]
                for occurrence in range(8):
                    group_index = color_index * 8 + occurrence
                    members = [new[occurrence % 4], additions[(2 * group_index) % 16],
                        replay[occurrence] if arm == "R" else new[(occurrence + 1) % 4],
                        additions[(2 * group_index + 1) % 16]]
                    for slot, member in enumerate(members):
                        rows.append(dict(copy.deepcopy(member),
                            id=f"sequential-v1-c{cycle}-{arm}-g{group_index:02d}-s{slot}",
                            batch_group=f"sequential-v1-c{cycle}-g{group_index:02d}", batch_slot=slot,
                            allocation_slot=("current_new", "arithmetic", "replacement", "arithmetic")[slot]))
            cycles[cycle][arm] = rows
    return dict(banks=banks, source_records=sources, cycles=cycles, readout_cases=_cases(banks),
        manifest=dict(protocol=PROTOCOL, status="RAW_CANDIDATE_TOKEN_AUDIT_PENDING",
            recipe=copy.deepcopy(RECIPE), origin="UNRESOLVED_LOCAL_HASHES_ONLY", limitations=LIMITATIONS[:],
            comparison="FIXED_BUDGET_NOT_NEW_DOSE_MATCHED", authored_not_child=True,
            dose_per_fact_per_fit={"1": {"R": {"M0": 20, "B1": 20}, "NEW_ONLY": {"B1": 40}},
                                  "2": {"R": {"M0": 10, "B1": 10, "B2": 20}, "NEW_ONLY": {"B2": 40}}},
            states=list(STATES), parents={"R1": "S0", "NEW_ONLY1": "S0", "R2": "R1", "NEW_ONLY2": "NEW_ONLY1"},
            untrained_banks_by_state={"S0": ["B1", "B2"], "R1": ["B2"], "NEW_ONLY1": ["B2"], "R2": [], "NEW_ONLY2": []},
            rows_per_fit=128, groups_per_epoch=32, updates_per_fit=320, total_planned_updates=1280,
            exported_rows=512, training_row_presentations=5120, readout_calls_per_state=128,
            readout_total_calls=640, readout_max_generated_tokens=40960,
            readout_temperature=0.0, readout_seed=READOUT_SEED, readout_max_tokens=MAX_TOKENS,
            original_raw_sha256=prior.ORIGINAL_RAW_SHA256, map_domains=dict(MAP_DOMAINS),
            teacher_outputs_used=False, readout_outputs_used=False, existing_confirmation_cases_exported=0,
            model_calls=0, training_calls=0, gpu_calls=0))


def validate_candidate(candidate):
    require(encoded(candidate) == encoded(build_candidate()), "fixed candidate sources/layout/targets/recipe/readout changed")
    require(len(candidate["readout_cases"]) == 128 and len({row["id"] for row in candidate["readout_cases"]}) == 128,
        "readout panel incomplete or duplicated")
    event_lookup = {event["id"]: event for event in candidate["source_records"]}
    require(len(event_lookup) == len(candidate["source_records"]), "duplicate source events")
    require(len({row["device"] for rows in candidate["banks"].values() for row in rows}) == 48, "bank overlap")
    for bank, rows in candidate["banks"].items():
        require(Counter(row["response"] for row in rows) == {color: 4 for color in original.COLORS}, "unbalanced bank")
        for row in rows:
            event = event_lookup[row["source_event_ids"][0]]
            require(event["device"] == row["device"] and event["color"] == row["response"], "source/target join failed")
    for cycle in CYCLES:
        for arm in ARMS:
            rows = candidate["cycles"][cycle][arm]
            require(len(rows) == 128, "row budget changed")
            counts = Counter(row["case_id"] for row in rows)
            doses = candidate["manifest"]["dose_per_fact_per_fit"][cycle][arm]
            for row in rows:
                expected = 40 if row["kind"] == "addition" else doses[row["bank"]]
                require(counts[row["case_id"]] * EPOCHS == expected, "per-source dose changed")
            for start in range(0, 128, 4):
                group = rows[start:start + 4]
                require(len({row["batch_group"] for row in group}) == 1 and
                    [row["batch_slot"] for row in group] == list(range(4)) and
                    len({row["case_id"] for row in group}) == 4 and
                    [row["kind"] for row in group] == ["memory", "addition", "memory", "addition"], "batch layout changed")
        for replay, new in zip(candidate["cycles"][cycle]["R"], candidate["cycles"][cycle]["NEW_ONLY"], strict=True):
            require(replay["response"] == new["response"], "paired target mismatch")
            if replay["batch_slot"] != 2:
                require({key: value for key, value in replay.items() if key != "id"} ==
                        {key: value for key, value in new.items() if key != "id"}, "nonreplacement paired row changed")
    return dict(valid=True, protocol=PROTOCOL, fits=4, rows_per_fit=128, groups_per_epoch=32,
        readout_cases=128, new_dose_matched=False, parent_validated=False)


def readout_cases(candidate=None):
    candidate = build_candidate() if candidate is None else candidate
    validate_candidate(candidate)
    return copy.deepcopy(candidate["readout_cases"])


def readout_requests(cases=None):
    expected = readout_cases()
    cases = expected if cases is None else cases
    require(encoded(cases) == encoded(expected), "fixed readout cases changed")
    return [dict(call_id=f"{index:04d}", case_id=case["id"], role="readout", arm="readout",
        prompt=case["context"], temperature=0.0, seed=READOUT_SEED, max_tokens=MAX_TOKENS)
        for index, case in enumerate(cases)]


def _schedule(parts, rows, pad):
    packs = trainer.pack_by_group(parts, MAX_LEN, pack=False)
    require(len(packs) == 128 and all(len(pack) == 1 for pack in packs), "packing/dropped rows forbidden")
    updates, exposure = [], Counter()
    for epoch in range(EPOCHS):
        ordered = trainer.epoch_order(packs, SEED, epoch, True)
        require(sorted(pack[0].item_index for pack in ordered) == list(range(128)), "epoch dropped/duplicated rows")
        for start in range(0, 128, 4):
            batch = ordered[start:start + 4]
            members = [pack[0] for pack in batch]
            indices = [item.item_index for item in members]
            records = [rows[index] for index in indices]
            require(len({item.group for item in members}) == 1 and
                [row["batch_slot"] for row in records] == list(range(4)) and
                len({row["case_id"] for row in records}) == 4 and
                all(item.group == row["batch_group"] and item.order == row["batch_slot"]
                    for item, row in zip(members, records, strict=True)), "actual V3 batch grouping/source order mismatch")
            collated = trainer.collate(batch, pad)
            width = max(map(len, members))
            for offset, item in enumerate(members):
                padding = width - len(item)
                require(collated["input_ids"][offset] == item.ids + [pad] * padding and
                    collated["labels"][offset] == item.labels + [trainer.IGNORE] * padding and
                    collated["position_ids"][offset] == list(range(len(item))) + [0] * padding and
                    collated["segment_ids"][offset] == [0] * len(item) + [-1] * padding,
                    "actual batch tokens/mask/positions/segments mismatch")
            target_tokens = sum(item.n_target for item in members)
            require(sum(label != trainer.IGNORE for labels in collated["labels"] for label in labels) == target_tokens,
                "padded target denominator mismatch")
            exposure.update(row["case_id"] for row in records)
            full_input = sum(len(item) for item in members)
            require(collated["n_target"] == target_tokens and collated["n_tokens"] == full_input,
                "actual batch target/input counters mismatch")
            updates.append(dict(epoch=epoch, batch=start // 4, update_index=len(updates) + 1,
                group=members[0].group, item_indices=indices, source_ids=[row["case_id"] for row in records],
                row_target_tokens=[item.n_target for item in members],
                target_tokens_by_kind={kind: sum(item.n_target for item, row in zip(members, records, strict=True)
                    if row["kind"] == kind) for kind in ("memory", "addition")},
                target_tokens=target_tokens, input_tokens=full_input, context_tokens=full_input - target_tokens,
                padded_width=width, padded_input_slots=4 * width, padding_slots=4 * width - full_input,
                masked_slots=4 * width - target_tokens))
    expected = Counter({key: count * EPOCHS for key, count in Counter(row["case_id"] for row in rows).items()})
    require(len(updates) == 320 and exposure == expected, "update/exposure budget changed")
    return dict(updates=updates, source_presentations=dict(sorted(exposure.items())),
        total={key: sum(update[key] for update in updates) for key in
               ("target_tokens", "input_tokens", "context_tokens", "padded_input_slots", "padding_slots", "masked_slots")})


def export_native(candidate, original_teach, tokenizer):
    """Audit caller-supplied CPU tokenizer with real V3 encoding/order/collation; never fit."""
    validation = validate_candidate(candidate)
    sources = source_hashes()
    candidate_hash = digest(encoded(candidate))
    original_hash = digest(encoded(original_teach))
    eos, pad = getattr(tokenizer, "eos_token_id", None), getattr(tokenizer, "pad_token_id", None)
    require(type(eos) is int and eos >= 0 and type(pad) is int and pad >= 0 and
        tokenizer.encode("<|im_end|>", add_special_tokens=False) == [eos], "Qwen EOS/pad identity required")
    require(all(len(tokenizer.encode(color, add_special_tokens=False)) == 1 for color in original.COLORS),
        "one-token color invariant failed")
    originals = prior.native_original(tokenizer, original_teach)
    baseline = {index: prior.encode_row(originals[index], tokenizer, index)[1] for index in
        sorted({row["source_row_index"] for rows in candidate["cycles"]["1"].values()
                for row in rows if row["source_row_index"] is not None})}
    corpora, fits, paired = {}, {}, {}
    for cycle in CYCLES:
        corpora[cycle], fits[cycle] = {}, {}
        for arm in ARMS:
            items, receipts, parts = [], [], []
            rows = candidate["cycles"][cycle][arm]
            for index, row in enumerate(rows):
                item = dict(spans=[[prior.render(tokenizer, row["context"]), False, "context"],
                                   [row["response"], True, "authored_birth_target"]],
                    group=row["batch_group"], view=row["kind"], order=row["batch_slot"],
                    meta=dict(source_event_ids=row["source_event_ids"][:], sequential_memory=dict(
                        protocol=PROTOCOL, record_id=row["id"], bank=row["bank"],
                        source_record_id=row["source_record_id"], source_row_index=row["source_row_index"],
                        source_row_sha256=row["source_row_sha256"], authored_not_child=True)))
                segment, receipt = prior.encode_row(item, tokenizer, index)
                if row["source_row_index"] is not None:
                    require(receipt == baseline[row["source_row_index"]], "original native input/target changed")
                if row["kind"] == "memory":
                    require(receipt["target_tokens"] == 2, "memory target must be one color plus exactly one EOS")
                receipts.append(dict(receipt, record_id=row["id"], case_id=row["case_id"], bank=row["bank"],
                    source_event_ids=row["source_event_ids"][:], source_row_sha256=row["source_row_sha256"],
                    raw_context_utf8_sha256=digest(row["context"].encode()),
                    raw_target_utf8_sha256=digest(row["response"].encode()),
                    original_native_row_index=row["source_row_index"]))
                items.append(item)
                parts.append(segment)
            totals = {key: sum(row[key] for row in receipts) for key in ("input_tokens", "context_tokens", "target_tokens")}
            schedule = _schedule(parts, rows, pad)
            require(all(schedule["total"][key] == value * EPOCHS for key, value in totals.items()), "schedule token totals differ")
            corpora[cycle][arm] = dict(corpus=items)
            fits[cycle][arm] = dict(rows=receipts, per_epoch=totals,
                ten_epochs={key: value * EPOCHS for key, value in totals.items()}, schedule=schedule,
                corpus_sha256=digest(encoded(corpora[cycle][arm])))
        replay, new = fits[cycle]["R"], fits[cycle]["NEW_ONLY"]
        for left, right in zip(replay["rows"], new["rows"], strict=True):
            require(left["target_with_eos"] == right["target_with_eos"] and
                left["raw_target_utf8_sha256"] == right["raw_target_utf8_sha256"], "paired target bytes/IDs differ")
        for left, right in zip(replay["schedule"]["updates"], new["schedule"]["updates"], strict=True):
            require(all(left[key] == right[key] for key in ("epoch", "batch", "group", "item_indices",
                "row_target_tokens", "target_tokens", "target_tokens_by_kind")), "paired update target/order mismatch")
        paired[cycle] = dict(targets_matched=True, new_dose_matched=False,
            paired_prefix_lengths_equal=all(left["context_tokens"] == right["context_tokens"]
                for left, right in zip(replay["rows"], new["rows"], strict=True)),
            padded_slots_equal=all(left["padded_input_slots"] == right["padded_input_slots"]
                for left, right in zip(replay["schedule"]["updates"], new["schedule"]["updates"], strict=True)))
    require(source_hashes() == sources and digest(encoded(candidate)) == candidate_hash and
        digest(encoded(original_teach)) == original_hash, "source/candidate changed during audit")
    return dict(corpora=corpora, audit=dict(protocol=PROTOCOL, status="CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT",
        validation=validation, candidate_sha256=candidate_hash, original_teach_canonical_sha256=original_hash,
        source_hashes=sources, fits=fits, paired=paired, recipe=copy.deepcopy(RECIPE),
        dose_per_fact_per_fit=copy.deepcopy(candidate["manifest"]["dose_per_fact_per_fit"]),
        original_selected_native_rows={str(index): receipt for index, receipt in baseline.items()},
        eos_token_id=eos, pad_token_id=pad, tokenizer_class=type(tokenizer).__module__ + "." + type(tokenizer).__name__,
        native_identity_authenticated=False, parent_validated=False, origin="UNRESOLVED_LOCAL_HASHES_ONLY",
        model_calls=0, training_calls=0, gpu_calls=0, observed_optimizer_updates=0,
        packing=False, truncation=False, teacher_outputs_used=False, readout_outputs_used=False,
        total_planned_updates=1280, total_target_exposure=sum(fit["ten_epochs"]["target_tokens"]
            for cycle_fits in fits.values() for fit in cycle_fits.values()),
        cost_scope="Per-row/per-epoch/ten-epoch/schedule totals are nested: do NOT add these overlapping counts.",
        limitations=LIMITATIONS[:]))


def emit_candidate(out):
    prior.fresh(out)
    sources = source_hashes()
    candidate = build_candidate()
    validation = validate_candidate(candidate)
    require(sources == source_hashes(), "source changed during generation")
    return prior.write_material(out, {"candidate.json": encoded(candidate)},
        dict(candidate["manifest"], source_hashes=sources, validation=validation))


def prepare(out, teach, tokenizer):
    """Fresh native export from exact original80 bytes using an injected CPU tokenizer."""
    prior.fresh(out)
    source = Path(teach).expanduser().absolute()
    require(not any(path.is_symlink() for path in (source, *source.parents)), "symlink teaching input forbidden")
    payload = source.read_bytes()
    require(digest(payload) == prior.ORIGINAL_TEACH_SHA256, "actual original80 teach bytes/hash differ")
    candidate = build_candidate()
    exported = export_native(candidate, json.loads(payload), tokenizer)
    require(source.read_bytes() == payload and source_hashes() == exported["audit"]["source_hashes"], "source changed during preparation")
    files = {"candidate.json": encoded(candidate), "token_audit.json": encoded(exported["audit"]),
             "readout_cases.json": encoded(readout_cases(candidate)), "readout_requests.json": encoded(readout_requests())}
    files.update({f"cycle{cycle}_{arm}.json": encoded(exported["corpora"][cycle][arm]) for cycle in CYCLES for arm in ARMS})
    return prior.write_material(out, files, dict(candidate["manifest"],
        status=exported["audit"]["status"], source_hashes=exported["audit"]["source_hashes"],
        original_teach_path=str(source), original_teach_sha256=digest(payload),
        native_identity_authenticated=False, parent_validated=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    candidate = subcommands.add_parser("candidate")
    candidate.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(emit_candidate(args.out), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
