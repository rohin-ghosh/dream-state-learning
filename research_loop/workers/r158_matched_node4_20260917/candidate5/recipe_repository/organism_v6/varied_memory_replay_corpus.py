"""Authored single-view/four-view material only; no fitting, readout, or model loading."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re

from organism_v6 import fundamental_teaching_corpus as original
from organism_v6 import train_adapter_v3 as trainer


ARMS = ("SINGLE_VIEW", "FOUR_VIEW")
COPIES, EPOCHS, BATCH_SIZE, MAX_LEN = 4, 10, 4, 512
ORIGINAL_TEACH_SHA256 = "2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c"
ORIGINAL_RAW_SHA256 = "d44585d4081819248f18774f12d8e1260e61af6fa6aaa260afbe3833e10838ab"
ADDITION_IDS = tuple("train-addition-" + suffix for suffix in
    ("011", "039", "055", "029", "048", "000", "052", "017", "036", "046", "063", "019", "057", "030", "012", "015"))
MEMORY_IDS = tuple(f"train-memory-{index:03d}" for index in range(16))
MEMORY_TEMPLATES = (
    "Which color does the log assign to {device}?",
    "What is the color assigned to {device} in the log?",
    "According to the log, which color is assigned to {device}?",
    "Name the color that the log assigns to {device}.",
)
CLAIM = "AUTHORED_VARIED_PHRASING_REPLAY_NOT_CHILD_EXPERIENCE_NOT_BRAIN_PROOF"
RECIPE = dict(base="frozen Qwen2.5-7B-Instruct; caller binds actual original base", rank=8,
    alpha=16, dropout=.05, lr=3e-4, epochs=EPOCHS, batch_size=BATCH_SIZE, grad_accum=1,
    allowed_seeds=[0, 1, 2], optimizer="adamw", pack=False, shuffle_groups=True,
    max_len=MAX_LEN, chat_template=False, add_eos=True, overflow="truncate",
    target_modules=list(trainer.ALL_PROJ), layers="all", freeze_a=False, svd_init=False,
    max_steps=0, dtype="bf16", grad_checkpoint=True,
    initialization="WEIGHT_WARM_START_FRESH_OPTIMIZER_FROM_ORIGINAL_TEACHING_PARENT_INDEPENDENT_PER_ARM",
    forbidden_parent="SEQ107 descendant or other replay arm",
    intended_updates=320, presentations_per_original_source=40,
    update_scope="declaration only; assumes all finite completed batches; no observed optimizer updates")
LIMITATIONS = [
    "New authored phrasing comparison, not reopening failed SEQ107 protocol.",
    "Four fixed memory phrasings chosen without model outputs; arithmetic never paraphrased.",
    "Prefix lengths and padded compute can differ; NOT compute matched.",
    "Targets, memberships, exposure counts, group blocks, copy order and batches are paired.",
    "Same parent weights must start independent arms; parent/model identity is a later launch responsibility.",
    "No child experience, clean lineage, passive fading, parenting, brain proof or memory-success claim.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def source_hashes():
    return {Path(module.__file__).name: digest(Path(module.__file__).read_bytes()) for module in (original, trainer)} | {
        Path(__file__).name: digest(Path(__file__).read_bytes())}


def original_rows():
    rows = original.build_candidate()["train_teach"]
    require(digest(encoded(rows)) == ORIGINAL_RAW_SHA256, "original80 teaching rows/order changed")
    require(tuple(row["case_id"] for row in rows if row["kind"] == "addition")[:16] == ADDITION_IDS,
            "SEQ107 first16 arithmetic selection changed")
    return rows


def build_candidate():
    """Pure fixed source-major layout; only memory context differs between arms."""
    rows = original_rows()
    selected_ids = set(MEMORY_IDS + ADDITION_IDS)
    selected = [(index, row) for index, row in enumerate(rows) if row["case_id"] in selected_ids]
    source_ids = {event for _, row in selected for event in row["source_event_ids"]}
    sources = [event for event in original.build_candidate()["source_records"] if event["id"] in source_ids]
    arms = {arm: [] for arm in ARMS}
    for source_index, source in selected:
        for copy_index in range(COPIES):
            row = dict(id=f"{source['case_id']}-copy-{copy_index}", case_id=source["case_id"],
                source_record_id=source["id"], source_row_index=source_index,
                source_row_sha256=digest(encoded(source)), source_event_ids=source["source_event_ids"][:],
                kind=source["kind"], copy_index=copy_index, context=source["context"], response=source["response"])
            arms["SINGLE_VIEW"].append(copy.deepcopy(row))
            if source["kind"] == "memory":
                row["context"] = MEMORY_TEMPLATES[copy_index].format(device=source["device"])
            arms["FOUR_VIEW"].append(row)
    return dict(arms=arms, source_records=sources, selected_case_ids=[row["case_id"] for _, row in selected],
        memory_templates=list(MEMORY_TEMPLATES), original_raw_sha256=ORIGINAL_RAW_SHA256,
        manifest=dict(status="RAW_CANDIDATE_TOKEN_AUDIT_PENDING", claim=CLAIM,
            origin="UNRESOLVED_LOCAL_HASHES_ONLY", recipe=copy.deepcopy(RECIPE), limitations=LIMITATIONS[:],
            source_rows=32, memory_sources=16, addition_sources=16, rows_per_arm=128,
            selection="all16 memories and SEQ107 fixed first16 arithmetic; retain original80 order; four adjacent copies",
            model_calls=0, training_calls=0, gpu_calls=0, eval_or_confirmation_rows_exported=0))


def validate_candidate(candidate):
    """Reject any unsupported change, and explicitly audit source joins and heldout exclusion."""
    require(encoded(candidate) == encoded(build_candidate()), "candidate differs from fixed authored source/layout/targets/recipe")
    events = {event["id"]: event for event in candidate["source_records"]}
    require(len(events) == len(candidate["source_records"]) == 32, "source events must be unique selected training facts")
    heldout_contexts = {" ".join(row["context"].casefold().split()) for row in original.build_candidate()["eval"]}
    source_by_id = {row["case_id"]: row for row in original_rows()}
    for arm in ARMS:
        rows = candidate["arms"][arm]
        require(Counter(row["case_id"] for row in rows) == Counter({case_id: COPIES for case_id in candidate["selected_case_ids"]}),
                "source membership/exposure differs")
        for row in rows:
            source = source_by_id[row["case_id"]]
            require(row["source_event_ids"] == source["source_event_ids"] and len(row["source_event_ids"]) == 1,
                    "source event join mismatch")
            event = events[row["source_event_ids"][0]]
            require(" ".join(row["context"].casefold().split()) not in heldout_contexts, "heldout evaluation context leaked")
            require(row["response"].encode() == source["response"].encode(), "original target bytes changed")
            if row["kind"] == "memory":
                require(event["kind"] == "device_color" and event["device"] == source["device"] and
                        event["color"] in original.COLORS and row["response"] == event["color"] and
                        event["text"] == f"The log records {event['device']} as {event['color']}.", "memory source/key differs")
                require(re.findall(r"device-\d{3}", row["context"]) == [event["device"]] and
                        not re.search(r"\b(?:blue|green|red|yellow|unknown)\b", row["context"], re.I), "device/held label leakage")
            else:
                require(event["kind"] == "addition" and type(event["left"]) is int and type(event["right"]) is int and
                        event["sum"] == event["left"] + event["right"] and
                        row["context"] == original.addition_context(event["left"], event["right"]) and
                        row["response"] == original.arithmetic_response(event["left"], event["right"], "teach"),
                        "integer outcome/context mismatch")
    for single, varied in zip(candidate["arms"]["SINGLE_VIEW"], candidate["arms"]["FOUR_VIEW"], strict=True):
        require({key: value for key, value in single.items() if key != "context"} ==
                {key: value for key, value in varied.items() if key != "context"}, "paired layout changed")
        require(single["kind"] == "memory" or single == varied, "arithmetic changed across arms")
    return dict(valid=True, selected_sources=32, rows_per_arm=128, source_events=32, heldout_contexts_exported=0)


def render(tokenizer, context):
    rendered = tokenizer.apply_chat_template([dict(role="user", content=context)], tokenize=False, add_generation_prompt=True)
    require(isinstance(rendered, str) and rendered.count(context) == 1, "native rendering must contain the exact single user context")
    return rendered


def native_original(tokenizer, supplied):
    """Require the entire original80 native material, including all grouping/mask metadata."""
    expected = []
    for index, source in enumerate(original_rows()):
        expected.append(dict(spans=[[render(tokenizer, source["context"]), False, "context"],
                                   [source["response"], True, "authored_birth_target"]],
            group=source["case_id"], view=source["kind"], order=index, meta=dict(source_event_ids=source["source_event_ids"][:])))
    require(encoded(supplied) == encoded(dict(corpus=expected)), "original80 native rendering/target/group/source mismatch")
    return expected


def encode_row(item, tokenizer, index):
    prefix = tokenizer.encode(item["spans"][0][0], add_special_tokens=False)
    response = tokenizer.encode(item["spans"][1][0], add_special_tokens=False)
    eos = tokenizer.eos_token_id
    require(isinstance(prefix, list) and isinstance(response, list) and prefix and response and
            all(type(token) is int and token >= 0 for token in prefix + response) and eos not in response,
            "invalid IDs or EOS inside original response")
    target = response + [eos]
    require(len(prefix) + len(target) <= MAX_LEN, "native example would truncate; no splitting/truncation allowed")
    parts = trainer.encode_item_segments(trainer.normalize_items([item])[0], tokenizer, MAX_LEN,
        False, True, index, overflow="truncate")
    require(len(parts) == 1 and parts[0].n_splits == 1 and parts[0].context_dropped == parts[0].target_dropped == 0,
            "V3 split/drop/truncation forbidden")
    segment = parts[0]
    labels = [trainer.IGNORE] * len(prefix) + target
    batch = trainer.collate([parts], tokenizer.pad_token_id)
    require(segment.ids == prefix + target and segment.labels == labels and segment.n_target == len(target) and
            batch["input_ids"] == [segment.ids] and batch["labels"] == [labels] and
            batch["position_ids"] == [list(range(len(segment)))] and batch["segment_ids"] == [[0] * len(segment)],
            "V3 native IDs/mask/shift/EOS mismatch")
    return segment, dict(rendered_context=item["spans"][0][0], response=item["spans"][1][0],
        prefix_token_ids=prefix, response_token_ids=response, target_with_eos=target,
        input_ids=segment.ids, labels=labels, input_tokens=len(segment), context_tokens=len(prefix), target_tokens=len(target))


def audit_schedules(segments, seeds, pad):
    require(isinstance(seeds, (tuple, list)) and seeds and len(set(seeds)) == len(seeds) and
            all(type(seed) is int and seed in (0, 1, 2) for seed in seeds), "caller seeds must be unique choices from 0/1/2")
    schedules, costs = {}, {}
    for seed in seeds:
        paired = {}
        costs[str(seed)] = {}
        for arm in ARMS:
            packs = trainer.pack_by_group(segments[arm], MAX_LEN, pack=False)
            require(len(packs) == 128 and all(len(pack) == 1 for pack in packs), "packing or dropped rows forbidden")
            updates, presentations, padded = [], Counter(), 0
            for epoch in range(EPOCHS):
                ordered = trainer.epoch_order(packs, seed, epoch, True)
                require(sorted(pack[0].item_index for pack in ordered) == list(range(128)), "epoch must contain all128 rows once")
                for start in range(0, 128, BATCH_SIZE):
                    selected = ordered[start:start + BATCH_SIZE]
                    members = [pack[0] for pack in selected]
                    indices = [item.item_index for item in members]
                    require(len({item.group for item in members}) == 1 and
                            indices == list(range(indices[0] // COPIES * COPIES, indices[0] // COPIES * COPIES + COPIES)),
                            "V3 source group/copy order changed")
                    batch = trainer.collate(selected, pad)
                    width = max(len(item) for item in members)
                    for offset, item in enumerate(members):
                        padding = width - len(item)
                        require(batch["input_ids"][offset] == item.ids + [pad] * padding and
                                batch["labels"][offset] == item.labels + [trainer.IGNORE] * padding,
                                "batch4 padding/labels changed")
                    padded += width * BATCH_SIZE
                    presentations.update(item.group for item in members)
                    updates.append(dict(epoch=epoch, group=members[0].group, item_indices=indices))
            require(len(updates) == 320 and len(presentations) == 32 and set(presentations.values()) == {40},
                    "scheduled update/exposure count differs")
            paired[arm] = updates
            costs[str(seed)][arm] = dict(padded_input_slots=padded, source_presentations=dict(sorted(presentations.items())))
        require(paired["SINGLE_VIEW"] == paired["FOUR_VIEW"], "paired actual V3 schedule differs")
        schedules[str(seed)] = paired["SINGLE_VIEW"]
    return dict(optimizer_update_schedule=schedules, scheduled_costs=costs,
        scope="actual V3 pack_by_group/epoch_order/collate CPU replay, not training; each batch is four copies of one source")


def export_native(candidate, original_teach, tokenizer, seeds=(0, 1, 2)):
    """Injected tokenizer only. Caller supplies native tokenizer; no loading or model calls."""
    validation = validate_candidate(candidate)
    eos, pad = getattr(tokenizer, "eos_token_id", None), getattr(tokenizer, "pad_token_id", None)
    require(type(eos) is int and eos >= 0 and type(pad) is int and pad >= 0 and
            tokenizer.encode("<|im_end|>", add_special_tokens=False) == [eos], "Qwen EOS/pad identity required")
    originals = native_original(tokenizer, original_teach)
    baseline = {row["case_id"]: encode_row(originals[row["source_row_index"]], tokenizer, row["source_row_index"])[1]
                for row in candidate["arms"]["SINGLE_VIEW"] if row["copy_index"] == 0}
    corpora, audits, segments = {}, {}, {}
    for arm in ARMS:
        items, checks, parts = [], [], []
        for index, row in enumerate(candidate["arms"][arm]):
            item = copy.deepcopy(originals[row["source_row_index"]])
            item["spans"][0][0] = render(tokenizer, row["context"])
            item["meta"]["replay_copy"] = dict(record_id=row["id"], copy_index=row["copy_index"],
                source_record_id=row["source_record_id"], source_row_index=row["source_row_index"], source_row_sha256=row["source_row_sha256"])
            segment, check = encode_row(item, tokenizer, index)
            prior = baseline[row["case_id"]]
            require(check["target_with_eos"] == prior["target_with_eos"], "tokenized original target/EOS changed")
            if arm == "SINGLE_VIEW" or row["kind"] == "addition" or row["copy_index"] == 0:
                require(check == prior, "unchanged original native prefix/target differs")
            checks.append(dict(check, record_id=row["id"], case_id=row["case_id"], source_event_ids=row["source_event_ids"][:],
                context=row["context"], response_utf8_sha256=digest(row["response"].encode())))
            items.append(item)
            parts.append(segment)
        totals = {key: sum(check[key] for check in checks) for key in ("input_tokens", "context_tokens", "target_tokens")}
        corpora[arm] = dict(corpus=items)
        audits[arm] = dict(rows=checks, per_epoch=totals, ten_epochs={key: EPOCHS * value for key, value in totals.items()})
        segments[arm] = parts
    for single, varied in zip(audits["SINGLE_VIEW"]["rows"], audits["FOUR_VIEW"]["rows"], strict=True):
        require(single["target_with_eos"] == varied["target_with_eos"] and
                single["response_utf8_sha256"] == varied["response_utf8_sha256"], "paired target byte/ID mismatch")
    order = audit_schedules(segments, seeds, pad)
    return dict(corpora=corpora, audit=dict(status="CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT", validation=validation,
        arms=audits, original_selected_rows=baseline, **order, recipe=copy.deepcopy(RECIPE),
        tokenizer_class=type(tokenizer).__module__ + "." + type(tokenizer).__name__, native_identity_authenticated=False,
        eos_token_id=eos, pad_token_id=pad, original_teach_canonical_sha256=digest(encoded(original_teach)),
        model_calls=0, training_calls=0, gpu_calls=0, truncation=False, packing=False,
        compute_matched=False, token_scope="nonpadding native counts; padded scheduled slots separately reported"))


def fresh(out):
    path = Path(out).expanduser().absolute()
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "symlink output path forbidden")
    if path.exists():
        raise FileExistsError(f"fresh output required: {path}")
    return path


def write_material(out, files, manifest):
    root = fresh(out)
    root.mkdir()
    for name, payload in files.items():
        with (root / name).open("xb") as stream:
            stream.write(payload)
    manifest = dict(manifest, sha256={name: digest(payload) for name, payload in files.items()})
    with (root / "manifest.json").open("xb") as stream:
        stream.write(encoded(manifest))
    return manifest


def emit_candidate(out):
    fresh(out)
    sources = source_hashes()
    candidate = build_candidate()
    validation = validate_candidate(candidate)
    require(sources == source_hashes(), "source changed during generation")
    return write_material(out, {"candidate.json": encoded(candidate)},
        dict(candidate["manifest"], source_hashes=sources, validation=validation))


def prepare(out, teach, tokenizer, seeds=(0, 1, 2)):
    """Fresh export from exact original native teach bytes and caller's CPU tokenizer."""
    fresh(out)
    source = Path(teach).expanduser().resolve(strict=True)
    payload = source.read_bytes()
    require(digest(payload) == ORIGINAL_TEACH_SHA256, "actual original80 teach bytes/hash differ")
    sources = source_hashes()
    candidate = build_candidate()
    exported = export_native(candidate, json.loads(payload), tokenizer, seeds)
    require(payload == source.read_bytes() and sources == source_hashes(), "source changed during token audit")
    files = {"candidate.json": encoded(candidate), "token_audit.json": encoded(exported["audit"])}
    files.update({arm + ".json": encoded(value) for arm, value in exported["corpora"].items()})
    return write_material(out, files, dict(candidate["manifest"], status=exported["audit"]["status"],
        source_hashes=sources, original_teach_path=str(source), original_teach_sha256=digest(payload),
        seeds=list(seeds), native_identity_authenticated=False,
        token_totals={arm: exported["audit"]["arms"][arm]["ten_epochs"] for arm in ARMS}))


def verify(root):
    root = Path(root)
    require(not any(parent.is_symlink() for parent in (root.absolute(), *root.absolute().parents)), "symlink artifact root forbidden")
    manifest = json.loads((root / "manifest.json").read_text())
    require(manifest["source_hashes"] == source_hashes(), "source hashes changed")
    files = manifest["sha256"]
    require(set(files) in ({"candidate.json"}, {"candidate.json", "token_audit.json", "SINGLE_VIEW.json", "FOUR_VIEW.json"}),
            "artifact file set differs")
    require({path.name for path in root.iterdir()} == set(files) | {"manifest.json"}, "unexpected/partial artifact root")
    require(all(not (root / name).is_symlink() and digest((root / name).read_bytes()) == value for name, value in files.items()),
            "artifact bytes changed")
    candidate = json.loads((root / "candidate.json").read_text())
    result = validate_candidate(candidate)
    require(all(encoded(manifest[key]) == encoded(value) for key, value in candidate["manifest"].items() if key != "status"),
            "manifest recipe/claims/counts changed")
    if "token_audit.json" in files:
        audit = json.loads((root / "token_audit.json").read_text())
        require(manifest["status"] == audit["status"] == "CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT" and
                manifest["native_identity_authenticated"] is audit["native_identity_authenticated"] is False and
                encoded(audit["recipe"]) == encoded(RECIPE) and
                manifest["token_totals"] == {arm: audit["arms"][arm]["ten_epochs"] for arm in ARMS} and
                set(audit["optimizer_update_schedule"]) == {str(seed) for seed in manifest["seeds"]},
                "native audit/manifest binding differs")
        require(digest(Path(manifest["original_teach_path"]).read_bytes()) == manifest["original_teach_sha256"] == ORIGINAL_TEACH_SHA256,
                "original native source changed")
    else:
        require(manifest["status"] == candidate["manifest"]["status"] and "original_teach_path" not in manifest,
                "raw material cannot claim native preparation")
    return dict(result, verification="source/artifact hashes and fixed raw candidate; no tokenizer rerun or parent/base attestation")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("emit", "verify"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(argv)
    require(args.out is not None if args.stage == "emit" else args.root is not None, "emit requires --out; verify requires --root")
    print(json.dumps(emit_candidate(args.out) if args.stage == "emit" else verify(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
