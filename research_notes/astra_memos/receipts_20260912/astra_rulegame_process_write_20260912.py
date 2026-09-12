"""Explicit exploratory process-v2 pair -> two fresh V3 writes; no readout.

prepare is local CPU/tokenizer-only. write and _worker require --allow-gpu.
Main supplies the deadline, real lease end and the returned immutable plan hash.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import signal
import struct
import sys
import threading
import time


ARMS = ("P", "A")
CONTROLLER_SECONDS = 1200
WORKER_SECONDS = 600
CLEANUP_SECONDS = 140
LEASE_MARGIN = 6 * 3600
STEPS = 12
SELF = Path(__file__).resolve()
PROTOCOL = "rulegame_grounded_process_pair_v2"
WRITE_PROTOCOL = "rulegame_process_write_v2_20260912"
CONDITIONING = "CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT"
ORIGIN = "UNRESOLVED_LOCAL_HASHES_ONLY"
FROZEN_DRIVER = Path("/tmp/astra_rulegame_record_write_v2_20260912.py")
FROZEN_SHA256 = "183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c"
API = dict(module="organism_v6.rulegame_process_material", protocol=PROTOCOL,
    inspect="inspect_capture", build="build_process_pair", export="export_pair",
    protocol_kwarg="protocol", amendment="96a71289", rows_per_arm=2)
CLAIMS = dict(context_distillation=True, model_origin=ORIGIN, clean_lineage=False,
    G3=False, P1=False, G5=False, H1=False, H2=False, semantic_certification=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path, value):
    with Path(path).open("xb") as target:
        target.write(encoded(value))
        target.flush()
        os.fsync(target.fileno())


def local_path(value, fresh=False):
    path = Path(value).expanduser()
    require(not any(part.is_symlink() for part in (path, *path.parents)), "symlink path rejected")
    if fresh:
        require(not path.exists() and path.parent.is_dir(), "fresh output with existing parent required")
    return path.resolve(strict=not fresh)


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def modules(source_root):
    root = local_path(source_root)
    require((root / "organism_v6" / "rulegame_process_material.py").is_file(), "source-root missing process exporter")
    sys.path.insert(0, str(root)) if str(root) not in sys.path else None
    names = ("rulegame_parenting_diagnostic", "rulegame_process_material", "train_adapter_v3")
    loaded = tuple(importlib.import_module("organism_v6." + name) for name in names)
    require(all(Path(module.__file__).resolve().parent.parent == root for module in loaded), "imported source-root mismatch")
    require(loaded[1].PROTOCOL_V2 == PROTOCOL, "explicit process-v2 API required")
    return loaded


def implementation(source_root, diagnostic):
    require(digest(FROZEN_DRIVER) == FROZEN_SHA256, "frozen original driver changed")
    names = set(diagnostic.SOURCE_FILES) | {"rulegame_process_material.py", "rulegame_record_material.py", "train_adapter_v3.py", "reasoning_neutral_probe.py"}
    paths = [Path(source_root) / "organism_v6" / name for name in sorted(names)] + [SELF, FROZEN_DRIVER]
    return {str(path.resolve()): digest(path) for path in paths}


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timezone-aware deadline/lease required")
    return parsed.timestamp()


def fit_config(trainer, model):
    return trainer.TrainConfig(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=12,
        batch_size=2, grad_accum=1, seed=2, pack=False, max_len=4096, max_steps=12,
        chat_template=False, add_eos=True, overflow="split", split_overlap_tokens=0,
        svd_init=False, freeze_a=False, optimizer="adamw", layers="all",
        target_modules=list(trainer.ALL_PROJ), model=str(model), device="cuda", dtype="bf16",
        note="EXPLORATORY_PROCESS_V2_CONTEXT_DISTILLATION_96a71289_NO_CLAIMS")


def full_tokens(corpus, tokenizer, trainer):
    items = trainer.normalize_items(corpus)
    require(len(items) == 2, "exactly two fixed process wakes required")
    rows, packs, categories, views = [], [], Counter(), Counter()
    for index, item in enumerate(items):
        spans = item["spans"]
        require(item["view"] == PROTOCOL and item["meta"]["protocol"] == PROTOCOL,
                "only explicit process-v2 material; no record/P0/v1")
        require(len(spans) == 2 and spans[0][1:] == [False, "parent_removed_wake_context"]
                and spans[1][1:] == [True, "complete_own_raw_wake"], "only transformed context/complete own raw wake spans allowed")
        context = tokenizer.encode(spans[0][0], add_special_tokens=False)
        raw = tokenizer.encode(spans[1][0], add_special_tokens=False)
        eos = tokenizer.eos_token_id
        require(context and raw and type(eos) is int and eos >= 0 and eos not in raw
                and all(type(token) is int and token >= 0 for token in context + raw), "empty material or invalid IDs/embedded target EOS")
        ids, labels = context + raw + [eos], [-100] * len(context) + raw + [eos]
        require(len(ids) <= 4096, "overlength; no drops or splits")
        segments = trainer.encode_item_segments(item, tokenizer, 4096, chat_template=False,
            add_eos=True, item_index=index, overflow="split", overlap_tokens=0)
        require(len(segments) == 1 and segments[0].n_splits == 1
                and segments[0].context_dropped == segments[0].target_dropped == 0, "dropped/split source material")
        require(segments[0].ids == ids and segments[0].labels == labels, "raw target/causal encoding mismatch")
        rows.append(dict(input_ids=ids, labels=labels, first_target_predictor=len(context) - 1,
            slot_id=item["meta"]["slot_id"], context_tokens=len(context), raw_target_tokens=len(raw),
            target_tokens=len(raw)+1, input_tokens=len(ids), presentations=STEPS,
            full_target_exposure=STEPS*(len(raw)+1), raw_target_exposure=STEPS*len(raw)))
        packs.append(segments)
        for label, category in zip(segments[0].labels, segments[0].cats):
            if label != -100:
                categories[category] += 1
                views[item["view"]] += 1
    pad = getattr(tokenizer, "pad_token_id", None)
    require(type(pad) is int and pad >= 0, "explicit tokenizer pad required")
    batch = trainer.collate(packs, pad)
    width = max(len(row["input_ids"]) for row in rows)
    require(batch["input_ids"] == [row["input_ids"] + [pad] * (width - len(row["input_ids"])) for row in rows]
            and batch["labels"] == [row["labels"] + [-100] * (width - len(row["labels"])) for row in rows],
            "collated raw target/causal mask/EOS mismatch")
    require(batch["position_ids"] == [list(range(len(row["input_ids"]))) + [0]*(width-len(row["input_ids"])) for row in rows]
            and batch["segment_ids"] == [[0]*len(row["input_ids"]) + [-1]*(width-len(row["input_ids"])) for row in rows],
            "collated position/segment IDs mismatch")
    total, target = sum(len(row["input_ids"]) for row in rows), sum(categories.values())
    require(batch["n_tokens"] == total and batch["n_target"] == target, "batch counts mismatch")
    for row in rows:
        row.update(padded_input_tokens=width, padding_tokens=width-row["input_tokens"],
            padded_input_exposure=STEPS*width, input_exposure=STEPS*row["input_tokens"])
    exposures = [dict(update=step+1, epoch=step+1, rows=2, padded_width=width,
        padded_input_tokens=2*width, input_tokens=total, padding_tokens=2*width-total,
        context_tokens=total-target, full_target_tokens=target, raw_target_tokens=target-2,
        eos_targets=2, full_target_exposure_cumulative=(step+1)*target) for step in range(STEPS)]
    return dict(rows=rows, batch=batch, per_batch_exposure=exposures,
        exposure=dict(row_presentations=2*STEPS, optimizer_updates=STEPS,
            full_target_tokens_seen=STEPS*target, raw_target_tokens_seen=STEPS*(target-2),
            eos_targets_seen=2*STEPS, padded_input_tokens_seen=STEPS*2*width,
            padding_tokens_seen=STEPS*(2*width-total), token_matched=False),
        tokens=dict(total=total, target=target, context=total-target,
        target_by_category=dict(categories), target_by_view=dict(views)), train_tokens_seen=STEPS * total,
        max_segment_tokens=width)


def verify_inputs(plan, diagnostic):
    require(all(digest(path) == expected for path, expected in plan["implementation"].items()), "implementation changed")
    formation = Path(plan["formation_root"])
    require(digest(formation / "plan.json") == plan["formation_plan_sha256"], "formation plan changed")
    original = diagnostic.verify_plan(formation)
    require(original["model"] == plan["model"] and original["model_files"] == plan["model_files"], "base pins changed")
    data = formation / "formation" / "data"
    require(digest(data / "manifest.json") == plan["formation_manifest_sha256"]
            and diagnostic.tree_hashes(data, ("manifest.json",)) == plan["formation_files"], "capture changed")
    require(digest(formation / "formation" / "result.json") == plan["formation_completion_sha256"], "formation completion changed")
    require(digest(plan["main_review_path"]) == plan["main_review_sha256"], "Main review changed")
    require(digest(plan["fixed_candidate_path"]) == plan["fixed_candidate_sha256"], "fixed candidate changed")
    require(diagnostic.model_hashes(plan["model"]) == plan["model_files"], "model bytes changed")


def forward_receipt(batch, tokens, index):
    require(0 <= index < STEPS and set(batch) == {"input_ids", "labels", "attention_mask"}, "unexpected forward number/tensor keys")
    require(all(isinstance(batch[key], list) and len(batch[key]) == 2 for key in batch), "actual forward must contain both complete rows")
    order = []
    for position in range(2):
        matches = [row for row in range(2) if batch["input_ids"][position] == tokens["batch"]["input_ids"][row]
            and batch["labels"][position] == tokens["batch"]["labels"][row]
            and batch["attention_mask"][position] == [int(segment >= 0) for segment in tokens["batch"]["segment_ids"][row]]]
        require(len(matches) == 1, "actual forward row/input/label/attention join mismatch or ambiguous duplicate")
        order.append(matches[0])
    require(sorted(order) == [0, 1], "actual forward repeated/dropped a source row")
    return dict(forward=index+1, status="OBSERVED_FORWARD_INPUTS_OPTIMIZER_SUCCESS_CHECKED_SEPARATELY",
        tensor_sha256=hashlib.sha256(encoded(batch)).hexdigest(), row_order=order,
        rows=[{key: value for key, value in tokens["rows"][row].items() if key not in ("input_ids", "labels")}
              for row in order], batch_exposure=tokens["per_batch_exposure"][index])


def expected_forward_batch(tokens, order):
    require(sorted(order) == [0, 1], "forward source row order mismatch")
    return dict(input_ids=[tokens["batch"]["input_ids"][row] for row in order],
        labels=[tokens["batch"]["labels"][row] for row in order],
        attention_mask=[[int(segment >= 0) for segment in tokens["batch"]["segment_ids"][row]] for row in order])


def native_review_template(pair):
    require(pair.get("protocol") == PROTOCOL, "native review requires process-v2 pair")
    rows = []
    for arm in ARMS:
        for row, receipt in zip(pair["corpora"][arm]["corpus"], pair["audit"]["receipts"][arm], strict=True):
            native, transformed = receipt["original_native_capture"], receipt["transformed_training"]
            rows.append(dict(slot_id=receipt["slot_id"], source_call_id=row["meta"]["source_call_id"],
                rendered_context_sha256=hashlib.sha256(transformed["rendered_context"].encode()).hexdigest(),
                raw_target_utf8_sha256=hashlib.sha256(row["spans"][1][0].encode()).hexdigest(),
                transformed_input_ids_sha256=hashlib.sha256(encoded(transformed["input_ids"])).hexdigest(),
                original_prompt_ids_sha256=hashlib.sha256(encoded(native["prompt_token_ids"])).hexdigest(),
                original_output_ids_sha256=hashlib.sha256(encoded(native["output_token_ids"])).hexdigest(),
                decision="pending", notes=""))
    require(len(rows) == 4, "native Main review requires four rows")
    return dict(actor="Main", candidate_sha256=pair["audit"]["candidate"]["candidate_sha256"],
        scope="exact_native_rendered_transformed_contexts_and_complete_raw_targets", rows=rows)


def check_native_review(review, pair=None):
    native = review.get("native_review", {})
    rows = native.get("rows", [])
    require(native.get("actor") == "Main" and len(rows) == 4
            and all(row.get("decision") == "accept" and isinstance(row.get("notes"), str)
                    and row["notes"].strip() for row in rows), "Main exact native four-context/target review required")
    if pair is not None:
        expected = native_review_template(pair)
        require(all(native.get(key) == expected[key] for key in ("actor", "candidate_sha256", "scope")),
                "native review candidate/scope mismatch")
        for actual, wanted in zip(rows, expected["rows"], strict=True):
            require(all(actual.get(key) == value for key, value in wanted.items() if key not in ("decision", "notes")),
                    "native review exact byte/token join mismatch")


def check_pair(pair, candidate, review, tokens, diagnostic):
    require(pair.get("protocol") == PROTOCOL and pair.get("status") == "PAIRED_CPU_TOKEN_AUDITED_MAIN_REVIEWED"
            and set(pair["corpora"]) == set(ARMS), "explicit complete process-v2 pair required; no record/P0")
    audit = pair["audit"]
    require(audit["candidate"] == candidate and audit["main_review"] == review
            and audit["conditioning"] == CONDITIONING and audit["source_native_token_audit"] is True
            and audit["teacher_sources_audit_only"] is True and audit["max_len"] == 4096,
            "candidate/Main/export/native audit binding mismatch")
    require([(row["arm"], row["lesson"]) for row in candidate["candidates"]]
            == [(arm, lesson) for arm in ARMS for lesson in range(2)], "four ordered source slots required")
    for arm in ARMS:
        require(len(pair["corpora"][arm]["corpus"]) == len(audit["receipts"][arm]) == 2,
                "partial pair forbidden")
        for lesson, (item, receipt, training) in enumerate(zip(pair["corpora"][arm]["corpus"],
                audit["receipts"][arm], tokens[arm]["rows"], strict=True)):
            source = candidate["candidates"][ARMS.index(arm)*2+lesson]
            meta = dict(protocol=PROTOCOL, slot_id=source["slot_id"], execution_id=source["selected"]["execution_id"],
                source_call_id=source["selected"]["call_id"], arm=arm, lesson=lesson)
            native, transformed = receipt["original_native_capture"], receipt["transformed_training"]
            response = source["source"]["response_receipt"]["response"]
            require(item["meta"] == meta and item["view"] == PROTOCOL and item["order"] == lesson
                    and item["group"] == source["eid"] and receipt["slot_id"] == source["slot_id"], "source slot/call/arm join mismatch")
            require(item["spans"][1][0] == source["target"] == response["text"] == native["raw_text"]
                    and transformed["raw_target_utf8_sha256"] == hashlib.sha256(source["target"].encode()).hexdigest(),
                    "complete own raw-wake target byte join mismatch")
            require(transformed["context"] == source["context"] and transformed["rendered_context"] == item["spans"][0][0]
                    and all(native[key] == response[key] for key in ("rendered_prompt", "prompt_token_ids", "output_token_ids"))
                    and native["native_output_decode_verified"] is True, "original native/transformed context join mismatch")
            require(receipt["same_conditioning_as_native"] is False and transformed["source_output_token_ids_reused_as_targets"] is False
                    and all(receipt[key] is False for key in ("packing", "truncation", "splitting")), "transformation receipt policy mismatch")
            require(all(transformed[key] == training[key] for key in ("input_ids", "labels", "first_target_predictor",
                    "context_tokens", "target_tokens", "input_tokens"))
                    and transformed["context_token_ids"] + transformed["target_with_eos"] == training["input_ids"]
                    and transformed["target_with_eos"][:-1] == transformed["raw_target_token_ids"], "export/trainer token or EOS join mismatch")
            require(transformed["predictor_positions"] == list(range(training["first_target_predictor"], training["input_tokens"]-1)),
                    "causal predictor join mismatch")
        require(audit["token_totals"][arm] == dict(input_tokens=tokens[arm]["tokens"]["total"],
                context_tokens=tokens[arm]["tokens"]["context"], target_tokens=tokens[arm]["tokens"]["target"]),
                "export token totals mismatch")
    require(candidate["candidate_sha256"] == diagnostic.value_hash({key: value for key, value in candidate.items() if key != "candidate_sha256"}),
            "candidate self hash mismatch")
    check_native_review(review, pair)


def prepare(formation_root, main_review, fixed_candidate, source_root, out, device, deadline, lease_end):
    source, formation, output = local_path(source_root), local_path(formation_root), local_path(out, fresh=True)
    review_path, candidate_path = local_path(main_review), local_path(fixed_candidate)
    diagnostic, exporter, trainer = modules(source)
    require(output.parent == formation.parent and output != formation, "output must be a fresh sibling of formation-root")
    require(not any(overlaps(output, path) for path in (source, review_path, candidate_path)), "output overlaps protected inputs")
    require(re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device), "one explicit device required")
    end, lease = timestamp(deadline), timestamp(lease_end)
    require(time.time() + CONTROLLER_SECONDS < end <= lease - LEASE_MARGIN, "deadline must leave 1200s and six-hour lease margin")
    original = diagnostic.verify_plan(formation)
    require(original.get("protocol") == "interaction_v3", "only new interaction_v3 formation accepted; no SEQ095")
    require(not overlaps(output, Path(original["model"])), "output overlaps base")
    data = formation / "formation" / "data"
    require(diagnostic.read(formation / "formation" / "result.json")["status"] == "AWAITING_MAIN_AUDIT", "formation incomplete")
    header = diagnostic.read(data / "identity.json")
    require(header["backend"] == diagnostic.expected_identity(original)
            and header["model_files"] == original["model_files"], "formation identity/base pin mismatch")
    decision, candidate = diagnostic.read(review_path), diagnostic.read(candidate_path)
    require(candidate.get("protocol") == decision.get("protocol") == PROTOCOL,
            "explicit process-v2 candidate/Main review required; no record/P0/v1")
    require(candidate.get("status") == "AVAILABLE_PENDING_MAIN_REVIEW", "paired shortage; never replace source slots")
    require(candidate == exporter.inspect_capture(data, protocol=PROTOCOL), "fixed candidate/source mismatch")
    exporter._review(candidate, decision, protocol=PROTOCOL)
    check_native_review(decision)
    pins = dict(formation_root=str(formation), formation_plan_sha256=digest(formation / "plan.json"),
        formation_manifest_sha256=digest(data / "manifest.json"), formation_files=diagnostic.read(data / "manifest.json")["files"],
        formation_completion_sha256=digest(formation / "formation" / "result.json"),
        model=original["model"], model_files=original["model_files"], original_identity=header,
        main_review_path=str(review_path), main_review_sha256=digest(review_path), implementation=implementation(source, diagnostic),
        fixed_candidate_path=str(candidate_path), fixed_candidate_sha256=digest(candidate_path),
        candidate_sha256=candidate["candidate_sha256"], process_api=API, exporter_source_hashes=exporter.source_hashes())
    replay = diagnostic.check_capture(data, diagnostic.expected_identity(original), "interaction_v3")
    require(replay["ok"], "formation replay rejected: " + str(replay["failures"]))
    tokenizer = diagnostic.native_tokenizer(original["model"])
    pair = exporter.build_process_pair(data, decision, tokenizer, fixed_candidate=candidate, max_len=4096, protocol=PROTOCOL)
    tokens = {arm: full_tokens(pair["corpora"][arm], tokenizer, trainer) for arm in ARMS}
    check_pair(pair, candidate, decision, tokens, diagnostic)
    verify_inputs(pins, diagnostic)
    require(time.time() + CONTROLLER_SECONDS < end, "preparation exhausted deadline")
    output.mkdir()
    pending = output / "material.pending"
    exported = exporter.export_pair(data, pending, decision, tokenizer, fixed_candidate=candidate, max_len=4096, protocol=PROTOCOL)
    require(exported["protocol"] == PROTOCOL and exported["candidate_sha256"] == candidate["candidate_sha256"]
            and exported["source_hashes"] == pins["exporter_source_hashes"] and exported["model_origin"] == ORIGIN
            and exported["corpus_files"] == {arm: "corpora/"+arm+".json" for arm in ARMS}, "export manifest/API mismatch")
    require(exported["files"] == diagnostic.tree_hashes(pending, ("manifest.json",)), "exported pair changed")
    require(diagnostic.read(pending / "audit/candidate.json") == candidate
            and diagnostic.read(pending / "audit/main_review.json") == decision
            and diagnostic.read(pending / "audit/token_receipts.json") == {key: value for key, value in pair["audit"].items()
                if key not in ("candidate", "main_review")}, "export audit differs from preflight")
    (pending / "manifest.json").rename(pending / "export_manifest.json")
    (pending / "provenance").mkdir()
    for arm in ARMS:
        require(diagnostic.read(pending / "corpora" / (arm + ".json")) == pair["corpora"][arm], "export corpus differs from preflight")
        write_json(pending / "provenance" / (arm + ".tokens.json"), tokens[arm])
    write_json(pending / "provenance" / "pair.json", dict(protocol=PROTOCOL, status=pair["status"],
        conditioning=CONDITIONING, model_origin=ORIGIN, claims=CLAIMS, api=API,
        candidate_sha256=candidate["candidate_sha256"], main_review_sha256=digest(review_path)))
    material_files = diagnostic.tree_hashes(pending)
    write_json(pending / "manifest.json", dict(files=material_files))
    exporter._publish(pending, output / "material")
    verify_inputs(pins, diagnostic)
    require(time.time() + CONTROLLER_SECONDS < end, "preparation exhausted deadline")
    plan = dict(**pins, schema=2, protocol=WRITE_PROTOCOL, material_protocol=PROTOCOL,
        conditioning=CONDITIONING, model_origin=ORIGIN, claims=CLAIMS,
        status="PREPARED", source_root=str(source), out=str(output), device=device,
        deadline=end, supplied_lease_end=lease, lease_cutoff=lease-LEASE_MARGIN, lease_margin_seconds=LEASE_MARGIN,
        lease_basis="Main-supplied expiry, not fresh control-plane verification", controller_seconds=CONTROLLER_SECONDS,
        worker_seconds=WORKER_SECONDS, cleanup_seconds=CLEANUP_SECONDS, arms=list(ARMS),
        config=asdict(fit_config(trainer, original["model"])), material_files=material_files,
        material_manifest_sha256=digest(output / "material" / "manifest.json"),
        tokens={arm: {key: value for key, value in tokens[arm].items() if key not in ("rows", "batch")} for arm in ARMS},
        python=os.path.abspath(sys.executable), sidecar=str(SELF), init_adapter=None,
        continuous_reservation="MAIN_LAUNCHER_REQUIRED_NOT_ACQUIRED_BY_SIDECAR",
        supervision="original diagnostic owns worker group; worker verifies parent PID and watches parent death",
        readout="OUT_OF_SCOPE", semantic_no_answer_certification=False)
    write_json(output / "plan.json", plan)
    plan_hash = digest(output / "plan.json")
    write_json(output / "plan.sha256.json", dict(sha256=plan_hash))
    return dict(status="PREPARED", root=str(output), plan_sha256=plan_hash, readout=plan["readout"])


def checked_plan(root, expected_hash):
    root = local_path(root)
    require(digest(root / "plan.json") == expected_hash, "plan hash mismatch")
    raw = json.loads((root / "plan.json").read_text())
    diagnostic, exporter, trainer = modules(raw["source_root"])
    plan = diagnostic.read(root / "plan.json")
    require(plan.get("schema") == 2 and plan.get("protocol") == WRITE_PROTOCOL and plan.get("material_protocol") == PROTOCOL
            and plan.get("process_api") == API and plan.get("conditioning") == CONDITIONING
            and plan.get("model_origin") == ORIGIN and plan.get("claims") == CLAIMS, "process-v2 plan/API/claim boundary mismatch")
    require(plan["out"] == str(root) and plan["sidecar"] == str(SELF) and plan["arms"] == list(ARMS), "plan root/sidecar/order mismatch")
    require(plan["python"] == os.path.abspath(sys.executable), "concrete native interpreter differs; never resolve virtualenv symlink")
    require(plan["config"] == asdict(fit_config(trainer, plan["model"])) and plan["init_adapter"] is None, "fixed fit recipe changed")
    require((plan["controller_seconds"], plan["worker_seconds"], plan["cleanup_seconds"], plan["lease_margin_seconds"])
            == (1200, 600, 140, 21600) and plan["deadline"] <= plan["lease_cutoff"] == plan["supplied_lease_end"] - LEASE_MARGIN,
            "controller/worker/lease bounds changed")
    require(implementation(plan["source_root"], diagnostic) == plan["implementation"], "implementation binding changed")
    require(exporter.source_hashes() == plan["exporter_source_hashes"], "process exporter sources changed")
    require(diagnostic.WORKER_SECONDS == WORKER_SECONDS and diagnostic.CLEANUP_RESERVE == CLEANUP_SECONDS,
            "reused supervisor bounds differ")
    material = root / "material"
    require(digest(material / "manifest.json") == plan["material_manifest_sha256"]
            and diagnostic.read(material / "manifest.json")["files"] == plan["material_files"]
            and diagnostic.tree_hashes(material, ("manifest.json",)) == plan["material_files"], "sealed material changed")
    exported = diagnostic.read(material / "export_manifest.json")
    require(exported["protocol"] == PROTOCOL and exported["candidate_sha256"] == plan["candidate_sha256"]
            and exported["source_hashes"] == plan["exporter_source_hashes"]
            and exported["corpus_files"] == {arm: "corpora/"+arm+".json" for arm in ARMS}
            and all(plan["material_files"].get(name) == value for name, value in exported["files"].items()),
            "process export binding changed")
    verify_inputs(plan, diagnostic)
    return root, plan, diagnostic, exporter, trainer


def trainability(model, layers):
    parameters, adapters = {}, {}
    for name, parameter in model.named_parameters():
        lora = name.endswith((".lora_A.default.weight", ".lora_B.default.weight"))
        require(bool(parameter.requires_grad) == lora, "base not frozen or non-LoRA trainability: " + name)
        parameters[name] = dict(shape=list(parameter.shape), dtype=str(parameter.dtype),
                                numel=parameter.numel(), requires_grad=bool(parameter.requires_grad))
        if lora:
            key = name[name.index("layers."):].replace(".default.", ".")
            require(key not in adapters and len(parameter.shape) == 2, "ambiguous LoRA parameter")
            require(parameter.shape[0 if ".lora_A." in key else 1] == 8, "LoRA rank mismatch")
            adapters[key] = parameters[name]
    expected = {f"layers.{layer}.{group}.{projection}.lora_{part}.weight"
                for layer in range(layers) for group, projections in
                (("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")), ("mlp", ("gate_proj", "up_proj", "down_proj")))
                for projection in projections for part in ("A", "B")}
    require(layers > 0 and set(adapters) == expected, "incomplete fresh default LoRA coverage")
    return dict(base_frozen=True, adapter_count=1, init_adapter=None, parameters=parameters,
                adapters=adapters, trainable_params=sum(value["numel"] for value in adapters.values()))


def saved_weights(path, expected):
    sizes = {"F32": 4, "F16": 2, "BF16": 2}
    with path.open("rb") as source:
        header_size = struct.unpack("<Q", source.read(8))[0]
        require(0 < header_size <= 16 * 1024 * 1024, "invalid safetensors header")
        header = json.loads(source.read(header_size))
    tensors = {name: item for name, item in header.items() if name != "__metadata__"}
    actual, intervals = {}, []
    for name, item in tensors.items():
        require("layers." in name and name.endswith((".lora_A.weight", ".lora_B.weight")), "saved non-LoRA tensor")
        key = name[name.index("layers."):]
        require(key in expected and key not in actual and item["shape"] == expected[key]["shape"], "saved tensor coverage/shape mismatch")
        start, end = item["data_offsets"]
        require(item["dtype"] in sizes and end-start == math.prod(item["shape"]) * sizes[item["dtype"]], "saved tensor byte count mismatch")
        actual[key] = item
        intervals.append((start, end))
    require(set(actual) == set(expected), "missing saved LoRA tensors")
    position = 0
    for start, end in sorted(intervals):
        require(start == position and end > start, "saved tensor offset gap/overlap")
        position = end
    require(path.stat().st_size == 8 + header_size + position, "saved weight size mismatch")
    return actual


def validate_fit(root, arm, plan, diagnostic, trainer):
    fit = root / "fits" / arm
    adapter = fit / "adapter"
    require((adapter / "DONE").is_file() and not (adapter / "EMPTY_CORPUS").exists(), "adapter incomplete")
    manifest = diagnostic.read(adapter / "train_manifest.json")
    expected = plan["tokens"][arm]
    require(manifest["recipe"] == trainer.RECIPE and manifest["config"] == plan["config"]
            and manifest["base_model"] == plan["model"] and "warm_start" not in manifest, "fit recipe/base/warm-start mismatch")
    require(manifest["empty"] is False and manifest["steps"] == manifest["micro_batches"] == manifest["epochs_run"] == STEPS
            and manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"])
            and len(manifest["mean_loss_per_epoch"]) == STEPS and all(math.isfinite(value) for value in manifest["mean_loss_per_epoch"]),
            "fit incomplete, nonfinite or wrong update count")
    require(manifest["corpus"] == dict(file=arm + ".json", sha256=plan["material_files"]["corpora/" + arm + ".json"],
        n_items=2, n_encoded=2, n_skipped_no_target=0), "fit corpus mismatch")
    require(manifest["tokens"] == expected["tokens"] and manifest["train_tokens_seen"] == expected["train_tokens_seen"], "fit token counts mismatch")
    require(diagnostic.read(adapter / "train_meta.json") == dict(recipe=trainer.RECIPE, n_texts=2, steps=12,
        tokens=expected["train_tokens_seen"], rank=8, epochs=12, lr=1e-4, seed=2, final_loss=manifest["final_loss"]),
        "trainer summary counts/config mismatch")
    require(manifest["truncation"] == dict(overflow="split", items_truncated=0, context_tokens_dropped=0,
        target_tokens_dropped=0, items_split=0, segments_from_splits=0, max_segment_tokens=expected["max_segment_tokens"]), "fit dropped/split tokens")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == 2
            and manifest["packing"]["n_groups"] == 2 and not manifest["packing"]["isolation_check"]["ran"], "unexpected packing")
    before, after = (diagnostic.read(fit / name) for name in ("pre_update_trainability.json", "post_update_trainability.json"))
    require(before == after and before["base_frozen"] and before["init_adapter"] is None and before["adapter_count"] == 1, "trainability changed")
    layers = diagnostic.read(Path(plan["model"]) / "config.json")["num_hidden_layers"]
    require(manifest["lora"] == dict(rank=8, alpha=16, dropout=.05, scaling=2.0, target_modules=list(trainer.ALL_PROJ),
        layers="all", n_layers=layers, freeze_a=False, trainable_params=before["trainable_params"]), "LoRA count/config mismatch")
    saved = diagnostic.read(adapter / "adapter_config.json")
    require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05
            and saved["bias"] == "none" and saved["peft_type"] == "LORA"
            and set(saved["target_modules"]) == set(trainer.ALL_PROJ) and not saved.get("modules_to_save")
            and not saved.get("layers_to_transform") and local_path(saved["base_model_name_or_path"]) == Path(plan["model"]),
            "saved adapter config/base mismatch")
    require(not (adapter / "adapter_model.bin").exists(), "unexpected alternate weight file")
    tensors = saved_weights(adapter / "adapter_model.safetensors", before["adapters"])
    files = diagnostic.tree_hashes(adapter)
    require(not any(name.startswith(("model", "pytorch_model", "optimizer")) for name in files), "unexpected base/optimizer checkpoint")
    actual_tokens = diagnostic.read(fit / "full_tokens.json")
    require(digest(fit / "full_tokens.json") == plan["material_files"]["provenance/" + arm + ".tokens.json"], "worker token receipt differs from preparation")
    require(actual_tokens["tokens"] == expected["tokens"], "worker token receipt mismatch")
    forward_files = {f"{index+1:04d}.json" for index in range(STEPS)}
    require(set(diagnostic.tree_hashes(fit / "forwards")) == forward_files, "missing/extra actual forward exposure receipts")
    for index in range(STEPS):
        observed = diagnostic.read(fit / "forwards" / f"{index+1:04d}.json")
        batch = expected_forward_batch(actual_tokens, observed["row_order"])
        require(observed == forward_receipt(batch, actual_tokens, index), "actual forward exposure changed")
    return dict(arm=arm, adapter=str(adapter), files=files, manifest_sha256=files["train_manifest.json"],
                saved_tensors=tensors, trainable_params=before["trainable_params"], steps=STEPS,
                tokens=manifest["tokens"], train_tokens_seen=manifest["train_tokens_seen"], readout="OUT_OF_SCOPE",
                observed_forward_batches=STEPS, exposure=actual_tokens["exposure"])


def load_native(model):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16, device_map="cuda", local_files_only=True)
    return tokenizer, base


def worker(root, arm, plan_sha256, launch_token, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before worker/model work")
    require(arm in ARMS, "unknown arm")
    root, plan, diagnostic, _, trainer = checked_plan(root, plan_sha256)
    launch = diagnostic.read(root / "run" / (arm + ".launch.json"))
    require(launch["token"] == launch_token and launch["plan_sha256"] == plan_sha256
            and time.time() < launch["hard_end"] - CLEANUP_SECONDS, "worker not bound to active controller window")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["device"], "worker device differs from reservation")
    with worker_ownership(root, arm, plan, launch, diagnostic):
        return fit_worker(root, arm, plan_sha256, plan, diagnostic, trainer)


@contextmanager
def worker_ownership(root, arm, plan, launch, diagnostic):
    process_path = root / "run" / arm / "process.json"
    wait_until = time.monotonic() + 5
    while not process_path.exists() and time.monotonic() < wait_until:
        time.sleep(.05)
    receipt = diagnostic.read(process_path)
    parent_pid = os.getppid()
    require(receipt["pid"] == receipt["pgid"] == os.getpid() == os.getpgrp()
            and parent_pid == launch["controller_pid"] and parent_pid > 1,
            "worker requires actual owning supervisor and fresh process group")
    require(receipt["device"] == plan["device"] and receipt["argv"] == launch["command"]
            and 0 < receipt["timeout"] <= WORKER_SECONDS, "worker supervisor command/device/time binding mismatch")
    stopped = threading.Event()
    end = min(time.monotonic()+WORKER_SECONDS, receipt["started"]+receipt["timeout"])
    def watch_parent():
        while not stopped.wait(.2):
            if os.getppid() != parent_pid or time.monotonic() >= end or time.time() >= launch["hard_end"]-CLEANUP_SECONDS:
                os.killpg(os.getpid(), signal.SIGTERM)
                return
    threading.Thread(target=watch_parent, daemon=True).start()
    try:
        yield
    finally:
        stopped.set()


def fit_worker(root, arm, plan_sha256, plan, diagnostic, trainer):
    fit = root / "fits" / arm
    fit.mkdir()
    write_json(fit / "attempt.json", dict(arm=arm, plan_sha256=plan_sha256, init_adapter=None, pid=os.getpid()))
    require(diagnostic.model_hashes(plan["model"]) == plan["model_files"], "base changed before load")
    tokenizer, base = load_native(plan["model"])
    require(not hasattr(base, "peft_config") and not any("lora_" in name for name, _ in base.named_parameters()), "base already adapted")
    require(local_path(base.name_or_path) == Path(plan["model"]), "loaded base identity mismatch")
    corpus_path = root / "material" / "corpora" / (arm + ".json")
    corpus = diagnostic.read(corpus_path)
    tokens = full_tokens(corpus, tokenizer, trainer)
    require(hashlib.sha256(encoded(tokens)).hexdigest() == plan["material_files"]["provenance/" + arm + ".tokens.json"], "native worker tokenization changed")
    write_json(fit / "full_tokens.json", tokens)
    (fit / "forwards").mkdir()
    recorded, forwards = [], []
    def before_forward(model, args, kwargs):
        require(not args and all(kwargs.get(key) is None for key in ("inputs_embeds", "position_ids", "past_key_values")),
                "unexpected positional/embedded/cached forward inputs")
        batch = {key: kwargs[key].detach().cpu().tolist() for key in ("input_ids", "labels", "attention_mask")}
        receipt = forward_receipt(batch, tokens, len(forwards))
        write_json(fit / "forwards" / f"{len(forwards)+1:04d}.json", receipt)
        forwards.append(receipt)
        if not recorded:
            receipt = trainability(base, base.config.num_hidden_layers)
            write_json(fit / "pre_update_trainability.json", receipt)
            recorded.append(receipt)
    hook = base.register_forward_pre_hook(before_forward, with_kwargs=True)
    try:
        require(not (fit / "adapter").exists() and not (fit / "adapter").is_symlink(), "adapter output must be fresh")
        trainer.run_training(trainer.normalize_items(corpus), tokenizer, base, fit_config(trainer, plan["model"]),
            str(fit / "adapter"), corpus_sha=digest(corpus_path), corpus_name=corpus_path.name, init_adapter=None)
        require(recorded, "no pre-update trainability evidence")
        require(len(forwards) == STEPS, "exactly twelve observed paired forward batches required")
        write_json(fit / "post_update_trainability.json", trainability(base, base.config.num_hidden_layers))
        require(diagnostic.model_hashes(plan["model"]) == plan["model_files"], "base files changed during fit")
        receipt = validate_fit(root, arm, plan, diagnostic, trainer)
        write_json(fit / "receipt.json", receipt)
        write_json(fit / "manifest.json", dict(files=diagnostic.tree_hashes(fit)))
        return receipt
    finally:
        hook.remove()


@contextmanager
def controller_watchdog(hard_end):
    require(threading.current_thread() is threading.main_thread(), "controller must run on main thread")
    remaining = hard_end - time.time() - CLEANUP_SECONDS
    require(remaining > 0, "insufficient controller cleanup reserve")
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "existing alarm would conflict")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("1200s controller/deadline work window exhausted; cleanup reserve retained")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@contextmanager
def supervisor_cleanup_window(hard_end):
    """Let the reused bounded supervisor finish owned cleanup without an alarm interrupt."""
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        yield
    finally:
        remaining = hard_end - time.time() - CLEANUP_SECONDS
        if remaining > 0:
            signal.setitimer(signal.ITIMER_REAL, remaining)


def write_pair(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before controller/GPU work")
    started, wall = time.monotonic(), time.time()
    with controller_watchdog(wall + CONTROLLER_SECONDS):
        root, plan, diagnostic, _, trainer = checked_plan(root, plan_sha256)
    hard_end = min(wall + CONTROLLER_SECONDS, plan["deadline"], plan["lease_cutoff"])
    run = root / "run"
    run.mkdir()
    completed = {}
    write_json(run / "controller.json", dict(plan_sha256=plan_sha256, started_wall=wall,
        hard_end=hard_end, worker_seconds=WORKER_SECONDS, cleanup_reserve=CLEANUP_SECONDS,
        pid=os.getpid(), continuous_reservation="MAIN_LAUNCHER_RESPONSIBILITY_NOT_A_LOCK"))
    try:
        with controller_watchdog(hard_end):
            verify_inputs(plan, diagnostic)
            (root / "fits").mkdir()
            for arm in ARMS:
                checked_plan(root, plan_sha256)
                verify_inputs(plan, diagnostic)
                require(time.time() < hard_end-CLEANUP_SECONDS, "insufficient time for next fresh fit")
                for previous in completed.values():
                    require(diagnostic.tree_hashes(previous["adapter"]) == previous["files"], "prior independent adapter changed")
                token = secrets.token_hex(16)
                command = [plan["python"], "-B", str(SELF), "_worker", "--root", str(root), "--arm", arm,
                           "--plan-sha256", plan_sha256, "--launch-token", token, "--allow-gpu"]
                write_json(run / (arm + ".launch.json"), dict(token=token, plan_sha256=plan_sha256, hard_end=hard_end,
                    controller_pid=os.getpid(), command=command))
                supervision_plan = dict(model=plan["model"], device=plan["device"], lease_end=hard_end)
                with supervisor_cleanup_window(hard_end):
                    supervision = diagnostic.supervise(root, supervision_plan, run / arm, command)
                require(time.time() < hard_end-CLEANUP_SECONDS, "controller work window exhausted after cleanup")
                require(supervision["ok"] and supervision["reservation_release_verified"], "worker cleanup unverified")
                fit = root / "fits" / arm
                require(diagnostic.read(fit / "manifest.json")["files"] == diagnostic.tree_hashes(fit, ("manifest.json",)), "sealed fit changed")
                receipt = validate_fit(root, arm, plan, diagnostic, trainer)
                require(diagnostic.read(root / "fits" / arm / "receipt.json") == receipt, "worker receipt changed")
                completed[arm] = dict(receipt, fit_manifest_sha256=digest(fit / "manifest.json"),
                                      supervision_sha256=digest(run / arm / "supervision.json"))
            require(all(diagnostic.tree_hashes(prior["adapter"]) == prior["files"]
                        and digest(root / "fits" / arm / "manifest.json") == prior["fit_manifest_sha256"]
                        and diagnostic.read(root / "fits" / arm / "manifest.json")["files"] == diagnostic.tree_hashes(root / "fits" / arm, ("manifest.json",))
                        for arm, prior in completed.items()),
                    "saved independent adapter changed during paired write")
            verify_inputs(plan, diagnostic)
            checked_plan(root, plan_sha256)
        require(time.monotonic()-started <= CONTROLLER_SECONDS and time.time() <= hard_end, "inclusive controller cap exceeded")
        result = dict(status="PAIRED_ADAPTERS_SAVED_READOUT_PENDING", arms=completed,
                      readout="OUT_OF_SCOPE", controller_seconds=time.monotonic()-started,
                      protocol=WRITE_PROTOCOL, conditioning=CONDITIONING, claims=CLAIMS, model_origin=ORIGIN,
                      exposure={arm: plan["tokens"][arm]["exposure"] for arm in ARMS},
                      semantic_no_answer_certification=False, model_authentication_certified=False)
        write_json(run / "result.json", result)
        return result
    except BaseException as error:
        write_json(run / "failure.json", dict(status="PARTIAL_FAILED" if completed else "FAILED",
            completed=completed, error=type(error).__name__ + ": " + str(error), controller_seconds=time.monotonic()-started,
            retry=False, readout="NOT_RUN"))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("formation-root", "main-review", "fixed-candidate", "source-root", "out", "device", "deadline", "lease-end"):
        prep.add_argument("--" + name, required=True)
    for name in ("write", "_worker"):
        command = sub.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        command.add_argument("--allow-gpu", action="store_true")
        if name == "_worker":
            command.add_argument("--arm", choices=ARMS, required=True)
            command.add_argument("--launch-token", required=True)
    args = vars(parser.parse_args(argv))
    action = args.pop("action")
    result = prepare(**args) if action == "prepare" else write_pair(**args) if action == "write" else worker(**args)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
