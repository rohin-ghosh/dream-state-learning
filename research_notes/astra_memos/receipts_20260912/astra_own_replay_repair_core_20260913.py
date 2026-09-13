"""Frozen-source mixed replay artifacts only; no collection, fits or native calls."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


PROTOCOL_PATH = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md"
PROTOCOL_PIN = "fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7"
CAPTURE_RUNTIME_PATH = "/tmp/astra_own_source_replay_capture_20260913.py"
CAPTURE_RUNTIME_PIN = "1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
HELPER_PIN = "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"
PROBE_PIN = "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
MEMORY_PLAN_PINS = (
    "66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1",
    "9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b",
    "48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea",
)
MEMORY_COUNTS = (14, 8, 8)
ARMS = ("REPLAY", "EXTRA_MEMORY")
PASSES, MAX_LEN = 8, 1024
SCHEMA = "astra_own_replay_repair_material_20260913_v1"
ENCODING_SCHEMA = "astra_own_replay_repair_encoding_20260913_v1"
LIMITS = (
    "Observation-reading on previously trained externally authored TRAIN sources, not new TRY experience.",
    "Fixed optimizer steps, not matched memory exposure, context tokens, target tokens or wall time.",
    "Extra memory presentations are not new records; historical LOWER/HIGH/LR0 are noncontemporaneous references.",
    "Saved native custody is verified, not live release; CPU encoding is not native/HF parity or a fit result.",
    "No automatic promotion, parenting, autonomous interaction, retention-repair conclusion or H1/H2 claim.",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def load_capture(path):
    require(digest(path) == CAPTURE_RUNTIME_PIN, "frozen capture runtime pin differs")
    name = "astra_repair_frozen_capture"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(Path(path).read_bytes(), str(path), "exec"), module.__dict__)
    return module


def validate_memory(plan, bound, seed):
    require(type(seed) is int and seed in (0, 1, 2), "original seed0/1/2 required")
    require(value_hash(plan) == MEMORY_PLAN_PINS[seed], "immutable original memory plan differs")
    require(bound["parent"] == plan["parent"], "original memory parent differs")
    for key in ("dataset", "capture", "retention"):
        require(value_hash(bound[key]) == plan["input_hashes"][key + ".json"], "immutable original memory " + key + " differs")
    rows = bound["dataset"]["rows"]
    require(len(rows) == MEMORY_COUNTS[seed] and len({row["row_id"] for row in rows}) == len(rows), "original memory count/identity differs")
    require(plan["specification"]["fit_seed"] == seed, "original fit seed differs")
    return rows


def validate_admission(core, bundle, admission, responses):
    require(admission["schema"] == core.SCHEMA and admission["boundary"] == core.BOUNDARY and
            admission["bundle_sha256"] == value_hash(bundle) and admission["producer"] == bundle["producer"] and
            admission["provenance"] == bundle["provenance"], "saved admission source binding differs")
    require(admission["source_population_denominator"] == 96 and admission["source_admissible_denominator"] == 48 and
            admission["requested_denominator"] == admission["submitted"] == len(responses) == 24 and
            admission["missing_request_ids"] == [], "all24 saved source responses required")
    require(admission["native_identity_verified"] is False and admission["training_export_ready"] is False and
            admission["fit_decision"] is None, "core admission flags must remain unpromoted")
    requests = bundle["requests"]
    require(len(requests) == 24 and len({request["request_id"] for request in requests}) == 24, "unique selected TRAIN sources required")
    observations = {row["row_id"]: row for row in bundle["training_observations"]}
    _, corpus = core.dependencies(bundle["provenance"]["source_root"])
    expected_rows, audits = [], []
    for index, (request, response) in enumerate(zip(requests, responses, strict=True)):
        require(request["source_split"] == "train" and
                response["request_id"] == request["request_id"] and response["input_sha256"] == request["input_sha256"] and
                response["producer_sha256"] == request["producer_sha256"] == bundle["producer_sha256"], "native source/request identity differs")
        source = observations[request["row_id"]]["source"]
        require(source["source_id"] == request["source_id"], "TRAIN source ID differs")
        assessment = corpus.assess_source(source)
        require(assessment["admissible"], "unselected/unsupported source entered replay")
        raw = response["raw"]
        require(type(raw) is str, "native raw text required")
        judge = corpus._interface().judge_record(raw, assessment["execution"])
        errors = [] if response["finish_reason"] == "stop" else ["stop_completion_required"]
        if not judge["eligible"]:
            errors.extend(judge["failures"])
        target_hash = hashlib.sha256(raw.encode()).hexdigest()
        response_hash = value_hash(response)
        audits.append(dict(submission_index=index, response=response, response_sha256=response_hash,
                           raw_sha256=target_hash, eligible=not errors, errors=errors, source_judge=judge))
        if not errors:
            expected_rows.append(dict(row_id=request["row_id"], request_id=request["request_id"], input_messages=request["input_messages"],
                raw_target=raw, target_sha256=target_hash, source=source, producer_sha256=bundle["producer_sha256"],
                source_proof=dict(original_train_row_id=request["row_id"], original_source_id=request["source_id"],
                    input_sha256=request["input_sha256"], supplied_response_sha256=response_hash, target_origin="SUPPLIED_RAW_CHILD_RESPONSE_ONLY")))
    expected_rows.sort(key=lambda row: row["row_id"])
    require(admission["responses"] == audits and admission["rejected"] == [audit for audit in audits if not audit["eligible"]],
            "saved raw-response/source-judge audit differs")
    require(admission["admitted"] == expected_rows and admission["admitted_count"] == len(expected_rows),
            "saved admission omitted/changed an admitted native raw row")
    accepted = {row["row_id"] for row in expected_rows}
    ledger = []
    for row in bundle["training_observations"]:
        status = ("source_unsupported_not_requested" if not row["source_admissible"] else
                  "source_supported_not_selected" if not row["selected"] else
                  "admitted" if row["row_id"] in accepted else "response_rejected")
        ledger.append(dict(row_id=row["row_id"], source_id=row["source_id"], status=status, source_errors=row["source_errors"]))
    require(admission["admission_ledger"] == ledger and admission["status_counts"] == dict(Counter(row["status"] for row in ledger)),
            "saved all-source ledger differs")


def validated_capture(plan, supplied, seed, runtime_path):
    capture = load_capture(runtime_path)
    root = Path(plan["root"])
    require(root.is_absolute(), "absolute saved capture root required")
    plan_hash = digest(root / "plan.json")
    verified, bound = capture.verify(root, plan_hash, native=False)
    require(verified == plan, "supplied capture plan differs from verified saved plan")
    memory = bound["memory"]
    inventories = capture.validate_completed(plan, plan_hash, bound)
    complete_path = root / "capture_complete.json"
    complete = memory.read(complete_path)
    complete_hash = digest(complete_path)
    require(complete["scope"] == capture.SCOPE and complete["plan_sha256"] == plan_hash and complete["calls"] == 72 and
            complete["fits"] == complete["updates"] == complete["teacher_calls"] == 0 and complete["admitted"] is False and
            type(complete["elapsed_seconds"]) in (int, float) and math.isfinite(complete["elapsed_seconds"]) and
            0 <= complete["elapsed_seconds"] <= capture.CONTROLLER_SECONDS and complete["stages"] == inventories,
            "completed capture receipt differs")
    claim_path = root.with_name(root.name + ".collection_claim.json")
    claim = memory.read(claim_path)
    out = Path(claim["out"])
    require(out.is_absolute() and claim == dict(plan_sha256=plan_hash, out=str(out), retry=False), "once-only collection claim differs")
    require(not (out / "collection_failure.json").exists(), "failed collection cannot supply replay")
    report_path, collection_path = out / "replay_report.json", out / "collection.json"
    report = memory.read(report_path)
    require(memory.read(collection_path) == dict(replay_report_sha256=digest(report_path), completion_sha256=complete_hash),
            "collection/report/completion hash differs")
    require(report["scope"] == capture.SCOPE and report["claim"] == capture.CLAIM and report["plan_sha256"] == plan_hash and
            report["completion_sha256"] == complete_hash and report["protocol"] == plan["specification"]["protocol"] and
            report["source_pins"] == {key: plan["specification"][key] for key in ("core", "native", "public", "lifecycle", "archive")},
            "collected source pins differ")
    require(report["native_capture_receipts_checked"] is True and report["core_native_identity_verified"] is False and
            report["automatic_pass"] is False and report["fit_decision"] is None, "collection must remain unpromoted")
    keys = {"0", "1", "2"}
    require(all(set(report[field]) == keys for field in ("seed_reports", "counts", "native_source_joins", "costs_per_seed")),
            "complete three-seed collection required")
    reports, costs = {}, {}
    for key in sorted(keys):
        admission_path = out / f"seed{key}_admission.json"
        require(report["seed_reports"][key] == dict(path=admission_path.name, sha256=digest(admission_path)), "admission file/hash differs")
        reports[key] = memory.read(admission_path)
        require(report["counts"][key] == capture.admission_counts(reports[key]), "collected admission counts differ")
        closed = memory.read(root / "run" / f"seed{key}" / "closed.json")
        costs[key] = {field: closed[field] for field in ("calls", "fits", "updates", "teacher_calls", "prompt_tokens", "output_tokens", "generation_seconds")}
    require(report["costs_per_seed"] == costs and report["costs"] == dict(
        {field: sum(cost[field] for cost in costs.values()) for field in ("calls", "fits", "updates", "teacher_calls", "prompt_tokens", "output_tokens", "generation_seconds")},
        controller_seconds=complete["elapsed_seconds"]), "collected capture costs differ")
    admission = reports[str(seed)]
    require(supplied == report or supplied == admission, "supplied report is not exact once-collected report/admission")
    bundle = bound["bundles"][str(seed)]
    calls = memory.read(root / f"calls_seed{seed}.json")
    require([call["core_request"] for call in calls] == bundle["requests"], "prepared requests differ from selected TRAIN bundle")
    responses, joins = [], []
    for call in calls:
        directory = root / "run" / f"seed{seed}"
        request = call["core_request"]
        response_path = directory / (call["call_id"] + ".response.json")
        response = memory.read(response_path)
        raw = dict(request_id=request["request_id"], input_sha256=request["input_sha256"], producer_sha256=request["producer_sha256"],
                   raw=response["text"], finish_reason=response["finish_reason"])
        responses.append(raw)
        joins.append(dict(request_id=request["request_id"], call_id=call["call_id"],
            native_request_sha256=digest(directory / (call["call_id"] + ".request.json")), native_response_sha256=digest(response_path),
            core_response_sha256=value_hash(raw)))
    require(joins == report["native_source_joins"][str(seed)], "saved native raw/source joins differ")
    validate_admission(bound["core"], bundle, admission, responses)
    require(plan["producers"][str(seed)] == bundle["producer"], "capture producer differs from original bundle")
    bindings = dict(capture_root=str(root), capture_plan_sha256=plan_hash, completion_sha256=complete_hash,
        collection_claim=dict(path=str(claim_path), sha256=digest(claim_path)),
        collection=dict(path=str(collection_path), sha256=digest(collection_path)),
        replay_report=dict(path=str(report_path), sha256=digest(report_path)),
        admission=dict(path=str(out / f"seed{seed}_admission.json"), sha256=report["seed_reports"][str(seed)]["sha256"]),
        bundle_sha256=value_hash(bundle), source_pins=report["source_pins"], native_source_joins=joins,
        native_capture_receipts_checked=True, live_release_checked=False)
    return bundle["producer"], admission, bindings


def arm_rows(memory_rows, replay_rows, seed, arm):
    if not replay_rows:
        return []
    additional = replay_rows if arm == "REPLAY" else [memory_rows[index % len(memory_rows)] for index in range(len(replay_rows))]
    result = []
    for index, source in enumerate(memory_rows + additional):
        kind = "memory" if index < len(memory_rows) else "observation_replay" if arm == "REPLAY" else "extra_memory"
        result.append(dict(copy.deepcopy(source), row_id=f"own-repair:seed{seed}:{arm}:{index:03d}",
                           source_row_id=source["row_id"], item_kind=kind, presentation_index=index))
    return result


def build(memory_plan, bound, capture_plan, capture_report, seed, *, protocol_path=PROTOCOL_PATH, capture_runtime_path=CAPTURE_RUNTIME_PATH):
    require(digest(protocol_path) == PROTOCOL_PIN, "frozen repair protocol pin differs")
    memory_rows = validate_memory(memory_plan, bound, seed)
    producer, admission, capture_bindings = validated_capture(capture_plan, capture_report, seed, capture_runtime_path)
    parent = memory_plan["parent"]
    require(producer == dict(learner_seed=seed, adapter=parent["adapter"], adapter_files=parent["adapter_files"],
            model=memory_plan["model"], model_files=memory_plan["model_files"], parent_plan_sha256=parent["plan_sha256"]),
            "replay producer is not the original memory recipient parent")
    replay_rows = admission["admitted"]
    memory_count, replay_count = len(memory_rows), len(replay_rows)
    require(0 <= replay_count <= 24, "replay admission bound differs")
    material = dict(schema=SCHEMA, status="READY" if replay_count else "REPLAY_UNAVAILABLE", seed=seed, parent=copy.deepcopy(parent),
        source_bindings=dict(protocol=dict(path=str(protocol_path), sha256=PROTOCOL_PIN), capture_runtime_sha256=CAPTURE_RUNTIME_PIN,
            memory_plan_sha256=MEMORY_PLAN_PINS[seed], memory_input_hashes=copy.deepcopy(memory_plan["input_hashes"]),
            memory_provenance=copy.deepcopy(memory_plan["specification"]), capture=capture_bindings),
        memory_rows=copy.deepcopy(memory_rows), replay_rows=copy.deepcopy(replay_rows), replay_rejected=copy.deepcopy(admission["rejected"]),
        counts=dict(memory=memory_count, replay=replay_count, rejected=24-replay_count, presentations_per_arm=memory_count+replay_count if replay_count else 0,
            updates_per_arm=PASSES*(memory_count+replay_count) if replay_count else 0, source_population=96, source_supported=48, source_requested=24),
        arms={arm: dict(rows=arm_rows(memory_rows, replay_rows, seed, arm)) for arm in ARMS}, interpretation_limits=list(LIMITS))
    material["material_sha256"] = value_hash(material)
    validate_material(material)
    return material


def validate_material(material):
    require(material["schema"] == SCHEMA and material["material_sha256"] == value_hash({key: value for key, value in material.items() if key != "material_sha256"}),
            "material content/hash differs")
    seed = material["seed"]
    require(type(seed) is int and seed in (0, 1, 2), "material seed differs")
    memory, replay = material["memory_rows"], material["replay_rows"]
    require(len(memory) == MEMORY_COUNTS[seed] and len(replay) <= 24 and len(material["replay_rejected"]) == 24-len(replay), "material source counts differ")
    require(material["status"] == ("READY" if replay else "REPLAY_UNAVAILABLE") and set(material["arms"]) == set(ARMS), "material status/arms differ")
    require(material["counts"] == dict(memory=len(memory), replay=len(replay), rejected=24-len(replay),
        presentations_per_arm=len(memory)+len(replay) if replay else 0, updates_per_arm=PASSES*(len(memory)+len(replay)) if replay else 0,
        source_population=96, source_supported=48, source_requested=24), "material workload differs")
    require([row["row_id"] for row in replay] == sorted(row["row_id"] for row in replay), "lexical replay order required")
    require(len({row["row_id"] for row in memory+replay}) == len(memory)+len(replay), "duplicate source rows")
    for row in memory+replay:
        require(type(row["raw_target"]) is str and row["raw_target"] and hashlib.sha256(row["raw_target"].encode()).hexdigest() == row["target_sha256"],
                "unchanged raw target bytes required")
    for arm in ARMS:
        require(material["arms"][arm] == dict(rows=arm_rows(memory, replay, seed, arm)), "presentation lineage/cycling differs")


def encode(material, arm, tokenizer, trainer, helper, probe, fit_seed):
    validate_material(material)
    require(arm in ARMS and type(fit_seed) is int and fit_seed == material["seed"], "arm/original learner seed differs")
    rows = material["arms"][arm]["rows"]
    items, audits, segments, orders = [], [], [], []
    if rows:
        for module, pin in ((trainer, TRAINER_PIN), (helper, HELPER_PIN), (probe, PROBE_PIN)):
            require(digest(module.__file__) == pin, "frozen encoder module pin differs")
        require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "distinct PAD/EOS required")
        for index, row in enumerate(rows):
            item, audit = helper.training_item(row, tokenizer, trainer, probe, index)
            item["view"] = "own_source_train_observation" if row["item_kind"] == "observation_replay" else "source_withdrawn_real_record"
            item["meta"].update(source_row_id=row["source_row_id"], item_kind=row["item_kind"], presentation_index=index)
            parts = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, False, index, overflow="truncate")
            require(len(parts) == 1 and parts[0].context_dropped == parts[0].target_dropped == 0 and
                    parts[0].ids == audit["input_ids"] and parts[0].labels == audit["labels"] and len(parts[0].ids) <= MAX_LEN,
                    "one unsplit untruncated exactly masked mixed item required")
            items.append(item)
            audits.append(dict(audit, source_row_id=row["source_row_id"], item_kind=row["item_kind"], presentation_index=index))
            segments.extend(parts)
        packs = trainer.pack_by_group(segments, MAX_LEN, False)
        require(len(packs) == len(rows) and all(len(pack) == 1 for pack in packs), "one mixed item per sequence required")
        for epoch in range(PASSES):
            ordered = trainer.epoch_order(packs, fit_seed, epoch, True)
            order = [pack[0].group for pack in ordered]
            require(Counter(order) == Counter(row["row_id"] for row in rows), "complete mixed epoch required")
            orders.append(order)
            for pack in ordered:
                batch = trainer.collate([pack], tokenizer.pad_token_id)
                require(batch["input_ids"] == [pack[0].ids] and batch["labels"] == [pack[0].labels], "single-row collate/mask differs")
    total = sum(len(audit["input_ids"]) for audit in audits)
    targets = sum(len(audit["supervised_ids"]) for audit in audits)
    costs = {}
    for kind in ("memory", "observation_replay", "extra_memory"):
        selected = [audit for audit in audits if audit["item_kind"] == kind]
        tokens = sum(len(audit["input_ids"]) for audit in selected)
        supervised = sum(len(audit["supervised_ids"]) for audit in selected)
        costs[kind] = dict(rows=len(selected), presentations=PASSES*len(selected), total_tokens=tokens,
                          target_tokens=supervised, context_tokens=tokens-supervised,
                          train_tokens_seen=PASSES*tokens, actual_supervised_tokens=PASSES*supervised,
                          actual_context_tokens=PASSES*(tokens-supervised))
    result = dict(schema=ENCODING_SCHEMA, material_sha256=material["material_sha256"], status=material["status"], seed=material["seed"], arm=arm,
        items=items, encoding=audits, epoch_order=orders, fit_seed=fit_seed, rows=len(rows), updates=PASSES*len(rows), presentations=PASSES*len(rows),
        total_tokens=total, target_tokens=targets, context_tokens=total-targets, train_tokens_seen=PASSES*total,
        actual_supervised_tokens=PASSES*targets, actual_context_tokens=PASSES*(total-targets), actual_padded_tokens=PASSES*total, padding_tokens=0,
        per_kind=costs, presentation_counts={row["row_id"]: PASSES for row in rows},
        training_items_sha256=value_hash(items), epoch_order_sha256=value_hash(orders))
    result["encoding_sha256"] = value_hash(result)
    return result
