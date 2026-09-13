"""Candidate additive replay loop; no loading, allocation or launch CLI."""
from __future__ import annotations

from collections import Counter
import copy
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import statistics
import sys
import time


TRAINER_PATH = "/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
PROTOCOL_PIN = "724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9"
PAIR_SCHEMA = "astra_additive_replay_pair_20260913_v1"
TRAIN_SCHEMA = "astra_additive_replay_train_20260913_v1"
ARMS = ("MEMORY_ONLY", "ADDITIVE")
OBJECTIVES = dict(MEMORY_ONLY="memory_mean_token_ce", ADDITIVE="sum_of_separate_mean_token_ce")
FILE_PINS = (
    {"EXTRA_MEMORY": "7c0c9c7fd452e5e311c63143944b8d8d6a60508fd109c8623f45babec9f2735a",
     "REPLAY": "8441052b34d6cb358d38c1933a6e4ddf3e6fedae760bb32fe830e99105727fb5"},
    {"EXTRA_MEMORY": "b0cd8384f6dd39a64782b1336a20a50a4f0ada3f40584a2b985546449bf2aab5",
     "REPLAY": "15f137d918402009b1298713253b9cee95fd17714dcf980c76e0d36c5af2f66d"},
    {"EXTRA_MEMORY": "fed12bf11cdd50dcaebb9974cbb63117eac736fd7855c876435e7c97b1625e93",
     "REPLAY": "83e8c224d3b90183bea1729b54498f1f0defeedd16b5cf53772c433603afc5c9"},
)
OBJECT_PINS = copy.deepcopy(FILE_PINS)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def value_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def load_trainer(path=TRAINER_PATH):
    require(digest(path) == TRAINER_PIN, "frozen trainer file pin differs")
    specification = importlib.util.spec_from_file_location("astra_additive_frozen_trainer", path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _check_trainer(trainer):
    require(digest(trainer.__file__) == TRAINER_PIN, "frozen trainer file pin differs")


def _without(value, field):
    return {key: content for key, content in value.items() if key != field}


def _audit_item(item, audit):
    spans, meta = item["spans"], item["meta"]
    require(len(spans) == 4 and all(len(span) == 3 for span in spans), "four exact raw spans required")
    require([(span[1], span[2]) for span in spans] ==
            [(False, "context"), (True, "skill_target"), (True, "assistant_end"), (False, "template_tail")],
            "context/target/EOS/tail mask contract differs")
    require(all(type(span[0]) is str and span[0] for span in spans), "nonempty raw spans required")
    require(spans[2][0] == "<|im_end|>" and spans[3][0] == "\n", "EOS/tail bytes differ")
    require(hashlib.sha256(spans[1][0].encode()).hexdigest() == meta["target_sha256"], "raw target changed")
    require(item["group"] == meta["row_id"] == audit["row_id"] and
            meta["source_row_id"] == audit["source_row_id"] and
            meta["item_kind"] == audit["item_kind"] and
            item["order"] == meta["presentation_index"] == audit["presentation_index"], "occurrence/source audit differs")
    require(audit["native_prompt"]["rendered_prompt"] == spans[0][0] and
            audit["full_assistant_text"] == "".join(span[0] for span in spans) and
            audit["template_tail"] == spans[3][0], "raw prompt/full text/tail audit differs")
    ids, labels = audit["input_ids"], audit["labels"]
    context = audit["native_prompt"]["prompt_token_ids"]
    supervised = audit["supervised_ids"]
    require(bool(context) and bool(supervised) and len(ids) == len(labels) <= 1024 and
            all(type(token) is int and token >= 0 for token in ids) and
            all(type(label) is int for label in labels), "invalid token audit")
    require(ids[:len(context)] == context and labels[:len(context)] == [-100] * len(context), "supervised context")
    require([label for label in labels if label != -100] == supervised and
            ids[len(context):len(context) + len(supervised)] == supervised and
            labels[len(context):len(context) + len(supervised)] == supervised and
            labels[len(context) + len(supervised):] == [-100] * (len(ids)-len(context)-len(supervised)),
            "noncontiguous or incorrect target/EOS mask")


def _costs(primary, replay_audits, epochs, arm):
    kinds = {}
    for kind in ("memory", "extra_memory", "observation_replay"):
        rows = [audit for audit in primary if audit["item_kind"] == kind]
        if kind == "observation_replay":
            rows = replay_audits if arm == "ADDITIVE" else []
        total = sum(len(row["input_ids"]) for row in rows) * epochs
        target = sum(len(row["supervised_ids"]) for row in rows) * epochs
        kinds[kind] = dict(rows=len(rows), forwards=len(rows)*epochs, total_tokens=total,
                           supervised_tokens=target, context_tokens=total-target)
    memory = [kinds[kind] for kind in ("memory", "extra_memory")]
    observation = kinds["observation_replay"]
    result = dict(updates=len(primary)*epochs, memory_forwards=len(primary)*epochs,
                  replay_forwards=observation["forwards"], per_kind=kinds)
    for token_kind in ("total_tokens", "supervised_tokens", "context_tokens"):
        result["memory_" + token_kind] = sum(row[token_kind] for row in memory)
        result["replay_" + token_kind] = observation[token_kind]
        result[token_kind] = result["memory_" + token_kind] + result["replay_" + token_kind]
    result["total_forwards"] = result["memory_forwards"] + result["replay_forwards"]
    return result


def prepare_pair(extra_memory_encoding, replay_encoding, *, seed, source_pins):
    require(type(seed) is int and seed in (0, 1, 2), "original seed0/1/2 required")
    count = (14, 8, 8)[seed]
    for arm, source in (("EXTRA_MEMORY", extra_memory_encoding), ("REPLAY", replay_encoding)):
        require(source_pins[arm.lower()+"_sha256"] == FILE_PINS[seed][arm], "original file byte pin differs")
        require(value_hash(source) == OBJECT_PINS[seed][arm], "original encoded object differs")
        require(source["schema"] == "astra_own_replay_repair_encoding_20260913_v1" and
                source["arm"] == arm and source["seed"] == source["fit_seed"] == seed and source["status"] == "READY",
                "historical arm/seed/status differs")
        require(source["encoding_sha256"] == value_hash(_without(source, "encoding_sha256")) and
                source["training_items_sha256"] == value_hash(source["items"]) and
                source["epoch_order_sha256"] == value_hash(source["epoch_order"]), "historical self hash differs")
        require(len(source["items"]) == len(source["encoding"]) == count+24 and
                source["rows"] == count+24 and source["updates"] == 8*(count+24), "fixed24/source counts differ")
        expected_kinds = ["memory"]*count + (["extra_memory"] if arm == "EXTRA_MEMORY" else ["observation_replay"])*24
        require([item["meta"]["item_kind"] for item in source["items"]] == expected_kinds, "fixed occurrence kinds differ")
        for item, audit in zip(source["items"], source["encoding"]):
            _audit_item(item, audit)
        ids = [item["group"] for item in source["items"]]
        require(len(set(ids)) == len(ids) and len(source["epoch_order"]) == 8 and
                all(Counter(order) == Counter(ids) for order in source["epoch_order"]), "missing/duplicate epoch occurrence")
    require(extra_memory_encoding["material_sha256"] == replay_encoding["material_sha256"], "source mixture differs")
    for left, right in zip(extra_memory_encoding["items"][:count], replay_encoding["items"][:count]):
        require(left["spans"] == right["spans"] and left["meta"]["source_row_id"] == right["meta"]["source_row_id"],
                "original memory prefixes differ")
    replay_items = replay_encoding["items"][count:]
    require([item["meta"]["source_row_id"] for item in replay_items] ==
            sorted(item["meta"]["source_row_id"] for item in replay_items), "frozen source replay order differs")
    pairs = [dict(memory_row_id=memory["group"], replay_row_id=replay["group"])
             for memory, replay in zip(extra_memory_encoding["items"][count:], replay_items)]
    paired = dict(schema=PAIR_SCHEMA, seed=seed, fit_seed=seed, protocol_sha256=PROTOCOL_PIN,
                  source_pins=copy.deepcopy(source_pins), primary=copy.deepcopy(extra_memory_encoding),
                  replay=copy.deepcopy(replay_encoding), pairs=pairs,
                  costs={arm: _costs(extra_memory_encoding["encoding"], replay_encoding["encoding"][count:], 8, arm)
                         for arm in ARMS})
    paired["paired_sha256"] = value_hash(paired)
    return paired


def validate_pair(paired):
    require(isinstance(paired, dict) and all(key in paired for key in ("primary", "replay", "seed", "source_pins")),
            "complete source-pinned paired object required")
    expected = prepare_pair(paired["primary"], paired["replay"], seed=paired["seed"], source_pins=paired["source_pins"])
    require(paired == expected, "paired map/order/costs/hash differs")


def _validate_config(cfg, seed, trainer):
    fixed = dict(rank=8, alpha=16, dropout=.05, lr=3e-5, epochs=8, max_len=1024, seed=seed,
                 overflow="truncate", split_overlap_tokens=0, batch_size=1, grad_accum=1, pack=False,
                 shuffle_groups=True, optimizer="adamw", layers="all", svd_init=False, freeze_a=False,
                 chat_template=False, add_eos=False, isolation_check="auto", isolation_tol=0.0,
                 grad_checkpoint=True, dtype="bf16", max_steps=0,
                 svd_scale="sigma", svd_method="exact", svd_cache="")
    require(all(getattr(cfg, key) == value for key, value in fixed.items()), "fixed production recipe differs")
    require(list(cfg.target_modules) == list(trainer.ALL_PROJ) and
            (cfg.device == "cuda" or cfg.device.startswith("cuda:")), "projection/device recipe differs")
    require(bool(cfg.model), "base path/identity required; runner binds original model files")


def validate_encoding(items, audits, tokenizer, trainer, cfg):
    require(len(items) == len(audits) and items, "nonempty complete encoding required")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id,
            "distinct PAD/EOS required")
    result = []
    for index, (item, audit) in enumerate(zip(items, audits)):
        _audit_item(item, audit)
        parts = trainer.encode_item_segments(item, tokenizer, cfg.max_len, cfg.chat_template, cfg.add_eos,
                                            index, overflow=cfg.overflow, overlap_tokens=cfg.split_overlap_tokens)
        require(len(parts) == 1, "one unsplit sequence required")
        segment = parts[0]
        require(segment.n_splits == 1 and segment.context_dropped == segment.target_dropped == 0 and
                segment.ids == audit["input_ids"] and segment.labels == audit["labels"],
                "truncation/splitting/tokenizer or label mismatch")
        require(tokenizer.encode(item["spans"][2][0], add_special_tokens=False) == [tokenizer.eos_token_id] and
                audit["supervised_ids"][-1] == tokenizer.eos_token_id, "single supervised EOS required")
        require(tokenizer.decode(audit["supervised_ids"][:-1], skip_special_tokens=False,
                                 clean_up_tokenization_spaces=False) == item["spans"][1][0], "raw target roundtrip differs")
        batch = trainer.collate([[segment]], tokenizer.pad_token_id)
        require(batch["input_ids"] == [audit["input_ids"]] and batch["labels"] == [audit["labels"]] and
                batch["n_target"] == len(audit["supervised_ids"]), "collate changed exact mask")
        result.append(segment)
    return result


def backward_components(model, memory_tensors, replay_tensors=None):
    import torch
    losses = []
    for tensors in (memory_tensors,) if replay_tensors is None else (memory_tensors, replay_tensors):
        require(bool((tensors["labels"][:, 1:] != -100).any()), "empty shifted target")
        loss = model(**tensors).loss
        require(loss.ndim == 0 and bool(torch.isfinite(loss)), "nonfinite/nonscalar mean-token loss")
        loss.backward()
        losses.append(loss.detach().item())
    return dict(memory=losses[0], replay=losses[1] if len(losses) == 2 else None, total=sum(losses))


def _write_json(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value))


def _owned_failure(output, error, owned, parent_custody=None):
    if owned:
        done = output / "DONE"
        if done.is_file():
            done.unlink()
        _write_json(output / "failure.json", dict(status="FAILED", error_type=type(error).__name__, error=str(error),
                                                  parent_custody=parent_custody))


def run_training(paired, tokenizer, base_model, cfg, out_dir, *, arm, init_adapter,
                 expected_parent_files, trainer=None, corpus_sha=None, log=print):
    require(arm in ARMS, "unknown additive arm")
    validate_pair(paired)
    trainer = trainer if trainer is not None else load_trainer()
    _check_trainer(trainer)
    _validate_config(cfg, paired["fit_seed"], trainer)
    require(expected_parent_files and trainer._warm_inventory(init_adapter) == expected_parent_files,
            "original parent inventory differs")
    primary, replay = paired["primary"], paired["replay"]
    primary_segments = validate_encoding(primary["items"], primary["encoding"], tokenizer, trainer, cfg)
    all_replay_segments = validate_encoding(replay["items"], replay["encoding"], tokenizer, trainer, cfg)
    replay_ids = {pair["replay_row_id"] for pair in paired["pairs"]}
    replay_segments = [segment for segment in all_replay_segments if segment.group in replay_ids]
    binding = dict(schema=TRAIN_SCHEMA, arm=arm, objective=OBJECTIVES[arm], trainer_sha256=digest(__file__),
                   frozen_trainer_sha256=TRAINER_PIN, protocol_sha256=PROTOCOL_PIN,
                   paired_sha256=paired["paired_sha256"], source_pins=copy.deepcopy(paired["source_pins"]),
                   primary_encoding_sha256=primary["encoding_sha256"],
                   primary_training_items_sha256=primary["training_items_sha256"],
                   primary_epoch_order_sha256=primary["epoch_order_sha256"], pairs_sha256=value_hash(paired["pairs"]),
                   costs=copy.deepcopy(paired["costs"][arm]), scientific_acceptance=False,
                   interpretation="objective-package comparison; extra RNG/compute; no equal-gradient or FLOP claim")
    return _run_encoded(primary_segments, replay_segments, primary["epoch_order"], paired["pairs"],
                        tokenizer, base_model, cfg, out_dir, arm=arm, init_adapter=init_adapter,
                        expected_parent_files=expected_parent_files, trainer=trainer, binding=binding,
                        corpus_sha=corpus_sha, log=log)


def _run_encoded(primary, replay, orders, pairs, tokenizer, base_model, cfg, out_dir, *,
                 arm, init_adapter, expected_parent_files, trainer, binding, corpus_sha=None, log=print):
    import torch
    from peft import get_peft_model_state_dict
    _check_trainer(trainer)
    require(arm in ARMS and cfg.batch_size == cfg.grad_accum == 1 and not cfg.pack and
            not cfg.max_steps and cfg.optimizer == "adamw", "one AdamW step per unpaced occurrence required")
    require(len(orders) == cfg.epochs and primary and replay, "complete nonempty scheduled training required")
    primary_map = {segment.group: segment for segment in primary}
    replay_map = {segment.group: segment for segment in replay}
    pairing = {pair["memory_row_id"]: pair["replay_row_id"] for pair in pairs}
    require(len(primary_map) == len(primary) and len(replay_map) == len(replay) and
            len(pairing) == len(pairs) == len(replay) and set(pairing) <= set(primary_map) and
            set(pairing.values()) == set(replay_map), "unique complete bijective pairs required")
    packs = trainer.pack_by_group(primary, cfg.max_len, False)
    for epoch, order in enumerate(orders):
        expected = trainer.epoch_order(packs, cfg.seed, epoch, cfg.shuffle_groups)
        require(order == [pack[0].group for pack in expected] and Counter(order) == Counter(primary_map.keys()),
                "exact legacy epoch schedule differs")
    warm = trainer._warm_parent(init_adapter, out_dir, cfg)
    require(warm["parent_files"] == expected_parent_files, "original parent pin differs before output")
    output = warm["output"]
    owned = False
    started = time.monotonic()
    try:
        output.mkdir(parents=True, exist_ok=False)
        owned = True
        random.seed(cfg.seed)
        torch.manual_seed(cfg.seed)
        device, dtype = torch.device(cfg.device), trainer._torch_dtype(cfg.dtype)
        model, warm_receipt = trainer._warm_initialize(base_model, cfg, warm)
        model.to(device)
        if cfg.grad_checkpoint and device.type == "cuda":
            model.gradient_checkpointing_enable()
            model.enable_input_require_grads()
        model.config.use_cache = False
        model.train()
        params = [parameter for parameter in model.parameters() if parameter.requires_grad]
        initial = [parameter.detach().cpu().float().clone() for parameter in params]
        optimizer = torch.optim.AdamW(params, lr=cfg.lr)
        require(not optimizer.state, "optimizer must start empty")
        warm_receipt.update(optimizer_class=type(optimizer).__module__+"."+type(optimizer).__name__,
                            optimizer_defaults=json.loads(json.dumps(optimizer.defaults)), optimizer_initial_state_entries=0)
        manifest = copy.deepcopy(binding)
        target_by_category, target_by_view = Counter(), Counter()
        for segment in primary:
            for label, category in zip(segment.labels, segment.cats):
                if label != -100:
                    target_by_category[category] += 1
                    target_by_view[segment.view] += 1
        targets = sum(target_by_category.values())
        total = sum(len(segment) for segment in primary)
        manifest.update(recipe=trainer.RECIPE, config=asdict(cfg), base_model=cfg.model, versions=trainer._versions(),
                        warm_start=warm_receipt, note=cfg.note or None,
                        corpus=dict(file=None, sha256=corpus_sha, n_items=len(primary), n_encoded=len(primary), n_skipped_no_target=0),
                        tokens=dict(target=targets, context=total-targets, total=total,
                                    target_by_category=dict(target_by_category), target_by_view=dict(target_by_view)),
                        truncation=dict(overflow=cfg.overflow, items_truncated=0, context_tokens_dropped=0,
                                        target_tokens_dropped=0, items_split=0, segments_from_splits=0,
                                        max_segment_tokens=max(len(segment) for segment in primary+replay)),
                        packing=dict(mode="one_item_per_sequence", n_sequences=len(primary), n_groups=len(primary),
                                     mean_fill=round(total/(len(primary)*cfg.max_len), 4), mean_segments_per_sequence=1,
                                     isolation_check=dict(ran=False)),
                        lora=dict(rank=cfg.rank, alpha=cfg.alpha or 2*cfg.rank, dropout=cfg.dropout,
                                  scaling=round((cfg.alpha or 2*cfg.rank)/cfg.rank, 4), target_modules=list(cfg.target_modules),
                                  layers=cfg.layers, n_layers=int(base_model.config.num_hidden_layers), freeze_a=cfg.freeze_a,
                                  trainable_params=sum(parameter.numel() for parameter in params)))
        component_losses, executed_order, losses_by_epoch = [], [], []
        tokens_seen = memory_forwards = replay_forwards = 0
        component_seconds = dict(memory_forward_backward=0.0, replay_forward_backward=0.0, optimizer=0.0)
        train_start = time.monotonic()
        with (output / "steps.jsonl").open("xb") as journal:
            for epoch, order in enumerate(orders):
                epoch_losses = []
                for position, memory_id in enumerate(order):
                    replay_id = pairing.get(memory_id) if arm == "ADDITIVE" else None
                    tensors = trainer.to_tensors(trainer.collate([[primary_map[memory_id]]], tokenizer.pad_token_id), device, dtype, "2d")
                    component_start = time.monotonic()
                    losses = backward_components(model, tensors)
                    component_seconds["memory_forward_backward"] += time.monotonic()-component_start
                    memory_forwards += 1
                    tokens_seen += len(primary_map[memory_id])
                    if replay_id is not None:
                        replay_tensors = trainer.to_tensors(trainer.collate([[replay_map[replay_id]]], tokenizer.pad_token_id), device, dtype, "2d")
                        component_start = time.monotonic()
                        replay_loss = backward_components(model, replay_tensors)["memory"]
                        component_seconds["replay_forward_backward"] += time.monotonic()-component_start
                        losses.update(replay=replay_loss, total=losses["memory"]+replay_loss)
                        replay_forwards += 1
                        tokens_seen += len(replay_map[replay_id])
                    require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in params),
                            "missing/nonfinite gradient; no optimizer step allowed")
                    component_start = time.monotonic()
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                    component_seconds["optimizer"] += time.monotonic()-component_start
                    require(all(bool(torch.isfinite(parameter).all()) for parameter in params), "nonfinite updated adapter")
                    identity = dict(epoch=epoch, position=position, memory_row_id=memory_id, replay_row_id=replay_id)
                    row = dict(identity, **losses)
                    journal.write(canonical(row))
                    journal.flush()
                    executed_order.append(identity)
                    component_losses.append(row)
                    epoch_losses.append(losses["total"])
                    if cfg.log_every and len(component_losses) % cfg.log_every == 0:
                        log(f"[additive] {arm} step={len(component_losses)} memory={losses['memory']} replay={losses['replay']}")
                losses_by_epoch.append(round(statistics.mean(epoch_losses), 5))
        elapsed = time.monotonic()-train_start
        steps = len(component_losses)
        require(steps == len(primary)*cfg.epochs and memory_forwards == steps and
                replay_forwards == (len(replay)*cfg.epochs if arm == "ADDITIVE" else 0), "executed workload differs")
        if "costs" in binding:
            costs = binding["costs"]
            require((steps, memory_forwards, replay_forwards, tokens_seen) ==
                    (costs["updates"], costs["memory_forwards"], costs["replay_forwards"], costs["total_tokens"]),
                    "executed token/forward cost mismatch")
        trainer._warm_trainability(model)
        warm_receipt["final_state"] = trainer._warm_state_inventory(
            get_peft_model_state_dict(model, adapter_name="default", save_embedding_layers=False))
        require(trainer._warm_inventory(warm["parent"]) == expected_parent_files, "parent changed before save")
        model.save_pretrained(str(output), save_embedding_layers=False)
        after = trainer._warm_inventory(warm["parent"])
        require(after == expected_parent_files, "parent changed during save")
        _check_trainer(trainer)
        warm_receipt.update(parent_files_after=after, parent_unchanged=True, phase_steps=steps,
                            cumulative_steps=warm["cumulative_steps"]+steps)
        squared_norm = sum((parameter.detach().cpu().float()-before).double().square().sum().item()
                           for parameter, before in zip(params, initial))
        manifest.update(steps=steps, micro_batches=steps, nonfinite_batches=0, epochs_run=len(orders),
                        mean_loss_per_epoch=losses_by_epoch, final_loss=component_losses[-1]["total"],
                        train_tokens_seen=tokens_seen, tokens_per_s=round(tokens_seen/max(elapsed, 1e-9), 1),
                        train_seconds=round(elapsed, 3), wall_seconds=round(time.monotonic()-started, 3), empty=False,
                        component_losses=component_losses, executed_order=executed_order,
                        executed_order_sha256=value_hash(executed_order), component_seconds=component_seconds,
                        timing_scope="host wall intervals; CUDA asynchronous timings are not kernel-time attribution",
                        memory_forwards=memory_forwards, replay_forwards=replay_forwards,
                        adapter_update_l2=squared_norm**.5, optimizer_steps=steps,
                        peak_cuda_memory_allocated_bytes=torch.cuda.max_memory_allocated(device) if device.type == "cuda" else None,
                        peak_memory_scope="process CUDA allocator high water, not isolated phase delta")
        _write_json(output / "train_manifest.json", manifest)
        _write_json(output / "train_meta.json", dict(recipe=trainer.RECIPE, n_texts=len(primary), steps=steps,
                    tokens=tokens_seen, rank=cfg.rank, epochs=cfg.epochs, lr=cfg.lr, seed=cfg.seed,
                    final_loss=manifest["final_loss"], arm=arm, objective=OBJECTIVES[arm]))
        require(trainer._warm_inventory(warm["parent"]) == expected_parent_files, "parent changed before DONE")
        with (output / "DONE").open("xb") as stream:
            stream.write(b"ok\n")
        require(trainer._warm_inventory(warm["parent"]) == expected_parent_files, "parent changed after DONE")
        return manifest
    except BaseException as error:
        custody = dict(before=expected_parent_files, unchanged=False)
        try:
            custody["after"] = trainer._warm_inventory(warm["parent"])
            custody["unchanged"] = custody["after"] == expected_parent_files
        except Exception as inventory_error:
            custody["inventory_error"] = str(inventory_error)
        _owned_failure(output, error, owned, custody)
        raise


if __name__ == "__main__":
    raise SystemExit("Library only; no model loading/launch CLI. Main owns native execution.")
