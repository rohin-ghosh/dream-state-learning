"""Actual RuleGame record pair -> two fresh V3 writes; never a readout.

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
    require(not path.is_symlink(), "symlink path rejected")
    if fresh:
        require(not path.exists() and path.parent.is_dir(), "fresh output with existing parent required")
    return path.resolve(strict=not fresh)


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def modules(source_root):
    root = local_path(source_root)
    require((root / "organism_v6" / "rulegame_record_material.py").is_file(), "source-root missing exporter")
    sys.path.insert(0, str(root)) if str(root) not in sys.path else None
    names = ("rulegame_parenting_diagnostic", "rulegame_record_material", "train_adapter_v3")
    loaded = tuple(importlib.import_module("organism_v6." + name) for name in names)
    require(all(Path(module.__file__).resolve().parent.parent == root for module in loaded), "imported source-root mismatch")
    return loaded


def implementation(source_root, diagnostic):
    names = set(diagnostic.SOURCE_FILES) | {"rulegame_record_material.py", "train_adapter_v3.py", "reasoning_neutral_probe.py"}
    paths = [Path(source_root) / "organism_v6" / name for name in sorted(names)] + [SELF]
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
        note="EXPLORATORY_ACTUAL_RULEGAME_RECORD_WRITE_READOUT_PENDING")


def full_tokens(corpus, tokenizer, trainer):
    items = trainer.normalize_items(corpus)
    require(len(items) == 2, "exactly two fixed records required")
    rows, packs, categories, views = [], [], Counter(), Counter()
    for index, item in enumerate(items):
        spans = item["spans"]
        require(len(spans) == 2 and spans[0][1:] == [False, "record_context"]
                and spans[1][1:] == [True, "own_raw_record"], "only actual context/raw record spans allowed")
        context = tokenizer.encode(spans[0][0], add_special_tokens=False)
        raw = tokenizer.encode(spans[1][0], add_special_tokens=False)
        eos = tokenizer.eos_token_id
        require(context and raw and eos is not None and eos not in raw, "empty material or embedded target EOS")
        ids, labels = context + raw + [eos], [-100] * len(context) + raw + [eos]
        require(len(ids) <= 4096, "overlength; no drops or splits")
        segments = trainer.encode_item_segments(item, tokenizer, 4096, chat_template=False,
            add_eos=True, item_index=index, overflow="split", overlap_tokens=0)
        require(len(segments) == 1 and segments[0].n_splits == 1
                and segments[0].context_dropped == segments[0].target_dropped == 0, "dropped/split source material")
        require(segments[0].ids == ids and segments[0].labels == labels, "raw target/causal encoding mismatch")
        rows.append(dict(input_ids=ids, labels=labels, first_target_predictor=len(context) - 1))
        packs.append(segments)
        for label, category in zip(segments[0].labels, segments[0].cats):
            if label != -100:
                categories[category] += 1
                views[item["view"]] += 1
    pad = tokenizer.pad_token_id if getattr(tokenizer, "pad_token_id", None) is not None else tokenizer.eos_token_id
    batch = trainer.collate(packs, pad)
    width = max(len(row["input_ids"]) for row in rows)
    require(batch["input_ids"] == [row["input_ids"] + [pad] * (width - len(row["input_ids"])) for row in rows]
            and batch["labels"] == [row["labels"] + [-100] * (width - len(row["labels"])) for row in rows],
            "collated raw target/causal mask/EOS mismatch")
    total, target = sum(len(row["input_ids"]) for row in rows), sum(categories.values())
    require(batch["n_tokens"] == total and batch["n_target"] == target, "batch counts mismatch")
    return dict(rows=rows, batch=batch, tokens=dict(total=total, target=target, context=total-target,
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
    require(digest(plan["main_audit_path"]) == plan["main_audit_sha256"], "Main audit changed")
    if plan.get("fixed_selection_path"):
        require(digest(plan["fixed_selection_path"]) == plan["fixed_selection_sha256"], "fixed selection changed")


def prepare(formation_root, main_audit, source_root, out, device, deadline, lease_end, fixed_selection=None):
    source, formation, output = local_path(source_root), local_path(formation_root), local_path(out, fresh=True)
    audit_path = local_path(main_audit)
    selection_path = local_path(fixed_selection) if fixed_selection is not None else None
    diagnostic, exporter, trainer = modules(source)
    require(output.parent == formation.parent and output != formation, "output must be a fresh sibling of formation-root")
    require(not overlaps(output, source) and not overlaps(output, audit_path), "output overlaps protected inputs")
    require(selection_path is None or not overlaps(output, selection_path), "output overlaps fixed selection")
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
    decision = diagnostic.read(audit_path)
    selection = diagnostic.read(selection_path) if selection_path is not None else decision.get("fixed_selection")
    require(isinstance(selection, dict), "explicit fixed_selection required in audit or separate file")
    require(selection_path is None or "fixed_selection" not in decision
            or diagnostic.value_hash(selection) == diagnostic.value_hash(decision["fixed_selection"]),
            "embedded and separate fixed selection disagree")
    pins = dict(formation_root=str(formation), formation_plan_sha256=digest(formation / "plan.json"),
        formation_manifest_sha256=digest(data / "manifest.json"), formation_files=diagnostic.read(data / "manifest.json")["files"],
        model=original["model"], model_files=original["model_files"], original_identity=header,
        main_audit_path=str(audit_path), main_audit_sha256=digest(audit_path), implementation=implementation(source, diagnostic))
    if selection_path is not None:
        pins.update(fixed_selection_path=str(selection_path), fixed_selection_sha256=digest(selection_path))
    replay = diagnostic.check_capture(data, diagnostic.expected_identity(original), "interaction_v3")
    require(replay["ok"], "formation replay rejected: " + str(replay["failures"]))
    tokenizer = diagnostic.native_tokenizer(original["model"])
    pair = exporter.build_record_pair(data, decision, selection, tokenizer, 4096,
                                      replay_verified_capture=replay)
    tokens = {arm: full_tokens(pair["corpora"][arm], tokenizer, trainer) for arm in ARMS}
    require(all(pair["source_receipts"][arm][index]["encoding"]["input_tokens"] == len(tokens[arm]["rows"][index]["input_ids"])
                for arm in ARMS for index in range(2)), "export/native token binding mismatch")
    verify_inputs(pins, diagnostic)
    require(time.time() + CONTROLLER_SECONDS < end, "preparation exhausted deadline")
    output.mkdir()
    pending = output / "material.pending"
    pending.mkdir()
    (pending / "corpora").mkdir()
    (pending / "provenance").mkdir()
    for arm in ARMS:
        write_json(pending / "corpora" / (arm + ".json"), pair["corpora"][arm])
        write_json(pending / "provenance" / (arm + ".sources.json"), pair["source_receipts"][arm])
        write_json(pending / "provenance" / (arm + ".tokens.json"), tokens[arm])
    write_json(pending / "provenance" / "pair.json", {key: value for key, value in pair.items() if key not in ("corpora", "source_receipts")})
    material_files = diagnostic.tree_hashes(pending)
    write_json(pending / "manifest.json", dict(files=material_files))
    pending.rename(output / "material")
    plan = dict(**pins, schema=1, status="PREPARED", source_root=str(source), out=str(output), device=device,
        deadline=end, supplied_lease_end=lease, lease_cutoff=lease-LEASE_MARGIN, lease_margin_seconds=LEASE_MARGIN,
        lease_basis="Main-supplied expiry, not fresh control-plane verification", controller_seconds=CONTROLLER_SECONDS,
        worker_seconds=WORKER_SECONDS, cleanup_seconds=CLEANUP_SECONDS, arms=list(ARMS),
        config=asdict(fit_config(trainer, original["model"])), material_files=material_files,
        material_manifest_sha256=digest(output / "material" / "manifest.json"),
        tokens={arm: {key: value for key, value in tokens[arm].items() if key not in ("rows", "batch")} for arm in ARMS},
        python=str(Path(sys.executable).resolve()), sidecar=str(SELF), init_adapter=None,
        readout="PENDING_SEPARATE_OFF_P_ON_A_ON", semantic_no_answer_certification=False)
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
    require(plan["out"] == str(root) and plan["sidecar"] == str(SELF) and plan["arms"] == list(ARMS), "plan root/sidecar/order mismatch")
    require(plan["config"] == asdict(fit_config(trainer, plan["model"])) and plan["init_adapter"] is None, "fixed fit recipe changed")
    require((plan["controller_seconds"], plan["worker_seconds"], plan["cleanup_seconds"], plan["lease_margin_seconds"])
            == (1200, 600, 140, 21600) and plan["deadline"] <= plan["lease_cutoff"] == plan["supplied_lease_end"] - LEASE_MARGIN,
            "controller/worker/lease bounds changed")
    require(implementation(plan["source_root"], diagnostic) == plan["implementation"], "implementation binding changed")
    require(diagnostic.WORKER_SECONDS == WORKER_SECONDS and diagnostic.CLEANUP_RESERVE == CLEANUP_SECONDS,
            "reused supervisor bounds differ")
    material = root / "material"
    require(digest(material / "manifest.json") == plan["material_manifest_sha256"]
            and diagnostic.read(material / "manifest.json")["files"] == plan["material_files"]
            and diagnostic.tree_hashes(material, ("manifest.json",)) == plan["material_files"], "sealed material changed")
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
    return dict(arm=arm, adapter=str(adapter), files=files, manifest_sha256=files["train_manifest.json"],
                saved_tensors=tensors, trainable_params=before["trainable_params"], steps=STEPS,
                tokens=manifest["tokens"], train_tokens_seen=manifest["train_tokens_seen"], readout="PENDING")


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
    recorded = []
    def before_forward(model, args):
        if not recorded:
            receipt = trainability(base, base.config.num_hidden_layers)
            write_json(fit / "pre_update_trainability.json", receipt)
            recorded.append(receipt)
    hook = base.register_forward_pre_hook(before_forward)
    try:
        require(not (fit / "adapter").exists() and not (fit / "adapter").is_symlink(), "adapter output must be fresh")
        trainer.run_training(trainer.normalize_items(corpus), tokenizer, base, fit_config(trainer, plan["model"]),
            str(fit / "adapter"), corpus_sha=digest(corpus_path), corpus_name=corpus_path.name, init_adapter=None)
        require(recorded, "no pre-update trainability evidence")
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
    root, plan, diagnostic, _, trainer = checked_plan(root, plan_sha256)
    hard_end = min(wall + CONTROLLER_SECONDS, plan["deadline"], plan["lease_cutoff"])
    run = root / "run"
    run.mkdir()
    completed = {}
    write_json(run / "controller.json", dict(plan_sha256=plan_sha256, started_wall=wall,
        hard_end=hard_end, worker_seconds=WORKER_SECONDS, cleanup_reserve=CLEANUP_SECONDS))
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
                write_json(run / (arm + ".launch.json"), dict(token=token, plan_sha256=plan_sha256, hard_end=hard_end))
                command = [plan["python"], "-B", str(SELF), "_worker", "--root", str(root), "--arm", arm,
                           "--plan-sha256", plan_sha256, "--launch-token", token, "--allow-gpu"]
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
                      readout="PENDING_SEPARATE_OFF_P_ON_A_ON", controller_seconds=time.monotonic()-started,
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
    for name in ("formation-root", "main-audit", "source-root", "out", "device", "deadline", "lease-end"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--fixed-selection")
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
