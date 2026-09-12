"""New authored balanced replay material; CPU callbacks only, never launches fits."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import re

from organism_v6 import varied_memory_replay_corpus as prior


trainer, original = prior.trainer, prior.original
ARMS = prior.ARMS
SEEDS = (0, 1, 2)
PROTOCOL = "AUTHORED_INTERLEAVED_MEMORY_REPLAY_V1"
HELDOUT_TEMPLATES = (
    "Look up {device} in the log and give its color.",
    "Consult the log: {device} has which color?",
    "In the log entry for {device}, what color is listed?",
)
RECIPE = copy.deepcopy(prior.RECIPE)
RECIPE.update(batch_composition="two distinct memory plus two distinct arithmetic sources",
    source_steps_per_epoch=4, source_steps_total=40, cumulative_steps_if_original_parent_has_80=400)
require, encoded, digest = prior.require, prior.encoded, prior.digest


def source_hashes():
    return prior.source_hashes() | {Path(__file__).name: digest(Path(__file__).read_bytes())}


def wording(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def build_candidate():
    legacy = prior.build_candidate()
    prior.validate_candidate(legacy)
    sources = {row["case_id"]: row for row in prior.original_rows()}
    memories = [key for key in legacy["selected_case_ids"] if sources[key]["kind"] == "memory"]
    additions = [key for key in legacy["selected_case_ids"] if sources[key]["kind"] == "addition"]
    arms = {}
    for arm in ARMS:
        lookup = {(row["case_id"], row["copy_index"]): row for row in legacy["arms"][arm]}
        rows = []
        for copy_index in range(4):
            for block in range(8):
                members = [memories[2 * block], additions[(2 * block + 2 * copy_index) % 16],
                    memories[2 * block + 1], additions[(2 * block + 2 * copy_index + 1) % 16]]
                for slot, case_id in enumerate(members):
                    row = copy.deepcopy(lookup[case_id, copy_index])
                    row.update(batch_group=f"interleaved-r{copy_index}-b{block:02d}", batch_slot=slot)
                    rows.append(row)
        arms[arm] = rows
    heldout = [dict(id=f"interleaved-cue-{family}-{sources[key]['device']}", family=family,
        case_id=key, device=sources[key]["device"], source_event_ids=sources[key]["source_event_ids"][:],
        context=template.format(device=sources[key]["device"]), expected=sources[key]["response"])
        for family, template in enumerate(HELDOUT_TEMPLATES) for key in memories]
    return dict(arms=arms, source_records=legacy["source_records"], selected_case_ids=legacy["selected_case_ids"],
        memory_templates=legacy["memory_templates"], heldout_templates=list(HELDOUT_TEMPLATES), heldout_cues=heldout,
        manifest=dict(protocol=PROTOCOL, status="RAW_CANDIDATE_TOKEN_AUDIT_PENDING", recipe=copy.deepcopy(RECIPE),
            origin="UNRESOLVED_LOCAL_HASHES_ONLY", claim="AUTHORED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_PARENTING_GATE",
            rows_per_arm=128, selected_sources=32, heldout_cues=48, heldout_facts=16,
            heldout_model_outputs_inspected=False, existing_confirmation_cases_exported=0,
            original_raw_sha256=prior.ORIGINAL_RAW_SHA256, model_calls=0, training_calls=0, gpu_calls=0,
            limitations=["New protocol; not a pure longitudinal causal comparison with grouped replay.",
                "Mixed-source token-weighted batch loss changes loss mass/composition versus grouped replay.",
                "Paired targets/exposure/order, NOT matched input or padded compute.",
                "Forty source-bearing steps, not forty independent observations; cues share sixteen facts.",
                "Original parent independently per arm, fresh optimizer; native parent/base binding deferred.",
                "Material only; Main decision required before native preparation. No launch or seed selection."]))


def validate_candidate(candidate):
    require(encoded(candidate) == encoded(build_candidate()), "fixed source/layout/targets/cues/recipe changed")
    legacy = prior.build_candidate()
    prior.validate_candidate(legacy)
    for arm in ARMS:
        expected = {row["id"]: row for row in legacy["arms"][arm]}
        require(len(candidate["arms"][arm]) == 128, "rows dropped")
        for row in candidate["arms"][arm]:
            require({key: value for key, value in row.items() if key not in ("batch_group", "batch_slot")} ==
                expected[row["id"]], "original source/target/view changed")
        groups = defaultdict(list)
        source_groups = defaultdict(set)
        for row in candidate["arms"][arm]:
            groups[row["batch_group"]].append(row)
            source_groups[row["case_id"]].add(row["batch_group"])
        require(len(groups) == 32 and set(map(len, source_groups.values())) == {4}, "source step collision")
        for rows in groups.values():
            require(len(rows) == len({row["case_id"] for row in rows}) == 4 and
                Counter(row["kind"] for row in rows) == {"memory": 2, "addition": 2} and
                [row["batch_slot"] for row in rows] == list(range(4)), "batch membership/composition changed")
    excluded = {wording(row["context"]) for rows in legacy["arms"].values() for row in rows}
    original_candidate = original.build_candidate()
    excluded.update(wording(row["context"]) for key in ("train_teach", "train_control", "eval")
        for row in original_candidate[key])
    events = {event["id"]: event for event in candidate["source_records"]}
    cues = candidate["heldout_cues"]
    require(len(cues) == len({wording(row["context"]) for row in cues}) == 48, "heldout cue collision")
    require(Counter(row["family"] for row in cues) == {0: 16, 1: 16, 2: 16}, "cue family count")
    for row in cues:
        event = events[row["source_event_ids"][0]]
        require(wording(row["context"]) not in excluded, "existing train/dev/confirmation wording reused")
        require(event["kind"] == "device_color" and row["device"] == event["device"] and
            row["expected"] == event["color"], "heldout source/key changed")
        require(re.findall(r"device-\d{3}", row["context"]) == [row["device"]] and
            not re.search(r"\b(?:blue|green|red|yellow|unknown)\b", row["context"], re.I), "heldout label leakage")
    return dict(valid=True, selected_sources=32, rows_per_arm=128, batches_per_epoch=32,
        distinct_source_steps_per_epoch=4, heldout_cues=48, heldout_facts=16,
        wording_exclusion="normalized words against original train/eval and current SINGLE/FOUR train; not universal novelty")


def audit_schedules(segments, candidate, pad):
    schedules, costs = {}, {}
    for seed in SEEDS:
        paired, costs[str(seed)] = {}, {}
        for arm in ARMS:
            packs = trainer.pack_by_group(segments[arm], prior.MAX_LEN, pack=False)
            require(len(packs) == 128 and all(len(pack) == 1 for pack in packs), "packing/drops forbidden")
            updates, presentations, padded = [], Counter(), 0
            for epoch in range(prior.EPOCHS):
                ordered = trainer.epoch_order(packs, seed, epoch, True)
                require(sorted(pack[0].item_index for pack in ordered) == list(range(128)), "epoch dropped/duplicated rows")
                source_steps = defaultdict(set)
                for start in range(0, 128, 4):
                    batch = ordered[start:start + 4]
                    members = [pack[0] for pack in batch]
                    indices = [item.item_index for item in members]
                    rows = [candidate["arms"][arm][index] for index in indices]
                    require(len({row["case_id"] for row in rows}) == 4 and
                        Counter(row["kind"] for row in rows) == {"memory": 2, "addition": 2} and
                        len({item.group for item in members}) == 1 and
                        [row["batch_slot"] for row in rows] == list(range(4)) and
                        all(item.group == row["batch_group"] and item.order == row["batch_slot"]
                            for item, row in zip(members, rows)), "actual V3 batch source/order/composition mismatch")
                    collated = trainer.collate(batch, pad)
                    width = max(map(len, members))
                    for offset, item in enumerate(members):
                        padding = width - len(item)
                        require(collated["input_ids"][offset] == item.ids + [pad] * padding and
                            collated["labels"][offset] == item.labels + [trainer.IGNORE] * padding,
                            "native batch padding/mask mismatch")
                    padded += width * 4
                    for row in rows:
                        source_steps[row["case_id"]].add(start // 4)
                        presentations[row["case_id"]] += 1
                    target_mass = {kind: sum(item.n_target for item, row in zip(members, rows) if row["kind"] == kind)
                        for kind in ("memory", "addition")}
                    updates.append(dict(epoch=epoch, batch=start // 4, group=members[0].group,
                        item_indices=indices, source_ids=[row["case_id"] for row in rows],
                        copy_indices=[row["copy_index"] for row in rows], target_tokens_by_kind=target_mass))
                require(set(source_steps) == set(candidate["selected_case_ids"]) and
                    set(map(len, source_steps.values())) == {4}, "each source requires four distinct steps per epoch")
            require(len(updates) == 320 and set(presentations.values()) == {40}, "update/exposure budget changed")
            paired[arm] = updates
            costs[str(seed)][arm] = dict(padded_input_slots=padded, source_presentations=dict(sorted(presentations.items())))
        require(paired[ARMS[0]] == paired[ARMS[1]], "paired V3 schedules differ")
        schedules[str(seed)] = paired[ARMS[0]]
    return dict(optimizer_update_schedule=schedules, scheduled_costs=costs,
        scope="actual V3 pack_by_group/epoch_order/collate; seeds0/1/2, ten epochs; no optimizer execution")


def export_native(candidate, original_teach, tokenizer):
    """Inject the native tokenizer; authenticate its source/parent externally before any fit."""
    validation = validate_candidate(candidate)
    eos, pad = getattr(tokenizer, "eos_token_id", None), getattr(tokenizer, "pad_token_id", None)
    require(type(eos) is int and eos >= 0 and type(pad) is int and pad >= 0 and
        tokenizer.encode("<|im_end|>", add_special_tokens=False) == [eos], "Qwen EOS/pad identity required")
    originals = prior.native_original(tokenizer, original_teach)
    baseline = {row["case_id"]: prior.encode_row(originals[row["source_row_index"]], tokenizer, row["source_row_index"])[1]
        for row in candidate["arms"][ARMS[0]] if row["copy_index"] == 0}
    corpora, audits, segments = {}, {}, {}
    for arm in ARMS:
        items, checks, parts = [], [], []
        for index, row in enumerate(candidate["arms"][arm]):
            item = copy.deepcopy(originals[row["source_row_index"]])
            item.update(group=row["batch_group"], order=row["batch_slot"])
            item["spans"][0][0] = prior.render(tokenizer, row["context"])
            item["meta"]["interleaved_replay"] = {key: row[key] for key in
                ("id", "case_id", "source_record_id", "source_row_index", "source_row_sha256", "copy_index", "batch_group", "batch_slot")}
            segment, check = prior.encode_row(item, tokenizer, index)
            previous = baseline[row["case_id"]]
            require(check["target_with_eos"] == previous["target_with_eos"], "original target/EOS changed")
            if arm == "SINGLE_VIEW" or row["kind"] == "addition" or row["copy_index"] == 0:
                require(check == previous, "original native prefix/target changed")
            checks.append(dict(check, record_id=row["id"], case_id=row["case_id"], source_event_ids=row["source_event_ids"],
                batch_group=row["batch_group"], batch_slot=row["batch_slot"], kind=row["kind"],
                response_utf8_sha256=digest(row["response"].encode())))
            items.append(item)
            parts.append(segment)
        totals = {key: sum(check[key] for check in checks) for key in ("input_tokens", "context_tokens", "target_tokens")}
        corpora[arm] = dict(corpus=items)
        audits[arm] = dict(rows=checks, per_epoch=totals, ten_epochs={key: 10 * value for key, value in totals.items()})
        segments[arm] = parts
    for single, four in zip(audits[ARMS[0]]["rows"], audits[ARMS[1]]["rows"], strict=True):
        require(single["target_with_eos"] == four["target_with_eos"] and
            single["response_utf8_sha256"] == four["response_utf8_sha256"], "paired target mismatch")
    heldout = []
    for row in candidate["heldout_cues"]:
        rendered = prior.render(tokenizer, row["context"])
        ids = tokenizer.encode(rendered, add_special_tokens=False)
        require(isinstance(ids, list) and ids and all(type(token) is int and token >= 0 for token in ids) and
            len(ids) <= prior.MAX_LEN, "heldout prefix overflow/invalid IDs")
        heldout.append(dict(id=row["id"], rendered_context=rendered, prefix_token_ids=ids))
    return dict(corpora=corpora, audit=dict(status="CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT", protocol=PROTOCOL,
        validation=validation, arms=audits, **audit_schedules(segments, candidate, pad), heldout_prefixes=heldout,
        recipe=copy.deepcopy(RECIPE), eos_token_id=eos, pad_token_id=pad,
        tokenizer_class=type(tokenizer).__module__ + "." + type(tokenizer).__name__, native_identity_authenticated=False,
        original_teach_canonical_sha256=digest(encoded(original_teach)), model_calls=0, training_calls=0, gpu_calls=0,
        packing=False, truncation=False, compute_matched=False, heldout_training_rows=0))


def emit_candidate(out):
    prior.fresh(out)
    sources = source_hashes()
    candidate = build_candidate()
    validation = validate_candidate(candidate)
    require(sources == source_hashes(), "source changed during generation")
    return prior.write_material(out, {"candidate.json": encoded(candidate)},
        dict(candidate["manifest"], source_hashes=sources, validation=validation))


def prepare(out, teach, tokenizer):
    """Fresh new-protocol export; original native80 bytes are required, no tokenizer loader."""
    prior.fresh(out)
    source = Path(teach).expanduser().resolve(strict=True)
    payload = source.read_bytes()
    require(digest(payload) == prior.ORIGINAL_TEACH_SHA256, "actual original80 teach bytes/hash differ")
    sources = source_hashes()
    candidate = build_candidate()
    exported = export_native(candidate, json.loads(payload), tokenizer)
    require(payload == source.read_bytes() and sources == source_hashes(), "source changed during token audit")
    files = {"candidate.json": encoded(candidate), "token_audit.json": encoded(exported["audit"])}
    files.update({arm + ".json": encoded(value) for arm, value in exported["corpora"].items()})
    return prior.write_material(out, files, dict(candidate["manifest"], status=exported["audit"]["status"],
        source_hashes=sources, original_teach_path=str(source), original_teach_sha256=digest(payload),
        seeds=list(SEEDS), native_identity_authenticated=False,
        token_totals={arm: exported["audit"]["arms"][arm]["ten_epochs"] for arm in ARMS}))


def verify(root):
    root = Path(root).expanduser().absolute()
    require(not any(path.is_symlink() for path in (root, *root.parents)), "symlink artifact root forbidden")
    require(not any(path.is_symlink() or not path.is_file() for path in root.iterdir()), "artifact aliases/directories forbidden")
    manifest = json.loads((root / "manifest.json").read_text())
    files = manifest["sha256"]
    raw = {"candidate.json"}
    native = raw | {"token_audit.json", *(arm + ".json" for arm in ARMS)}
    require(set(files) in (raw, native) and {path.name for path in root.iterdir()} == set(files) | {"manifest.json"},
        "unexpected artifact inventory")
    require(manifest["source_hashes"] == source_hashes(), "source hashes changed")
    require(all(digest((root / name).read_bytes()) == sha for name, sha in files.items()), "artifact bytes changed")
    candidate = json.loads((root / "candidate.json").read_text())
    result = validate_candidate(candidate)
    require(all(manifest[key] == value for key, value in candidate["manifest"].items() if key != "status"), "manifest changed")
    if set(files) == native:
        audit = json.loads((root / "token_audit.json").read_text())
        require(manifest["status"] == audit["status"] == "CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT" and
            audit["recipe"] == RECIPE and manifest["seeds"] == list(SEEDS) and
            manifest["native_identity_authenticated"] is audit["native_identity_authenticated"] is False and
            manifest["token_totals"] == {arm: audit["arms"][arm]["ten_epochs"] for arm in ARMS}, "callback receipt changed")
        require(digest(Path(manifest["original_teach_path"]).read_bytes()) == manifest["original_teach_sha256"] ==
            prior.ORIGINAL_TEACH_SHA256, "original native source changed")
    else:
        require(manifest["status"] == candidate["manifest"]["status"], "raw material cannot claim native audit")
    return dict(result, verification="current source/artifact hashes and fixed candidate; no tokenizer rerun or parent/base attestation")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("emit", "verify"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(emit_candidate(args.path) if args.stage == "emit" else verify(args.path), sort_keys=True))


if __name__ == "__main__":
    main()
