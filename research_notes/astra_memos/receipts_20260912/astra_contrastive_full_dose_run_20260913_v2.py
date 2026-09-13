"""Exploratory authored contrastive dose extension. Main alone runs native commands.

Four cold subprocesses per seed; historical OFF is read from a pinned archive.
No original root/collector, global helper mutation, warm start, or promotion.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
from types import SimpleNamespace


SELF = Path(__file__).resolve()
ORIGINAL = Path("/tmp/astra_contrastive_perception_run_20260913.py")
ORIGINAL_SHA = "aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55"
PROTOCOL_SHA = "e777b5be15e2a1cab447de3e72fb013bfac2a20a3d12d81574f95880ca60b0e6"
OLD_PROTOCOL_SHA = "cc7e92d8aa3999c2ee619893cf830f2687347a39175149708886c1bf0d820ef5"
ARCHIVE_SHA = "c12c3ff8e7cd0a9261aa5118d85f5a93d5318245afd05d0d4ff3cacc96401f7d"
OLD_PLAN_SHA = "f0060eb8d37a61aa1d9b25ba6798f19045a8a66cca715755f5e948d216702ec4"
OLD_COMPLETE_SHA = "9574f5b7dfe6df3bbd9b74a3afb46fd5fc1c5d4ae0b1e11f249f9076bf0c38ff"
OLD_SCORES_SHA = "7af6484ebb72abc81d2f17d29e7ca15786599afba0b22e88139a80403f3412d0"
BINDING_SHA = "e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019"
ARCHIVE_ROOT = "contrastive_perception_20260913_attempt1"
SCOPE = "authored_contrastive_full_dose_DEV_three_seeds_v1"
CLAIM = ("Exploratory exposed DEV authored Level0/1 only. Historical noncontemporaneous OFF; "
         "unequal context costs, not compute-equivalent. No child SLEEP, fresh confirmation, "
         "source-attention mechanism, G3/P1/H1/H2 or automatic promotion.")
ARMS = ("plain", "contrastive")
PANELS = ("D1", "D2", "C-record", "C-general")
STAGES = ("fit_plain", "readout_plain", "fit_contrastive", "readout_contrastive")
OUTER_SECONDS, COLLECTION_SECONDS, CLEANUP_SECONDS = 7200, 180, 40
LEASE_MARGIN = 21600
STAGE_SECONDS = {"fit_plain": 2700, "readout_plain": 800,
                 "fit_contrastive": 2700, "readout_contrastive": 800}
BUDGET = dict(controller=7200, collection=180, cleanup_in_controller=40,
              fits=2, updates=672, presentations=2688, readouts=2, calls=96,
              historical_OFF_calls=48, new_OFF_calls=0, epochs_per_arm=112,
              updates_per_arm=336, presentations_per_arm=1344,
              total_three_seeds=dict(fits=6, updates=2016, calls=288),
              stage_seconds=STAGE_SECONDS,
              feasibility="UNPROFILED hard caps; never shrink panels, retry, or extend dose")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


require(digest(ORIGINAL) == ORIGINAL_SHA, "original helper pin differs")
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("full_dose_frozen_original", ORIGINAL)
old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(old)
read, write, tree, encoded = old.read, old.write, old.tree, old.encoded
failure, offline, budget = old.failure, old.offline, old.budget


def seed_value(seed):
    require(type(seed) is int and seed in (0, 1, 2), "learner_seed must be integer0/1/2")
    return seed


def recipe(seed):
    return dict(old.RECIPE, epochs=112, seed=seed_value(seed))


def pinned(record, expected=None):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "closed file pin required")
    require(type(record["path"]) is str and Path(record["path"]).is_absolute(), "absolute input path required")
    require(type(record["sha256"]) is str and len(record["sha256"]) == 64 and
            all(char in "0123456789abcdef" for char in record["sha256"]), "SHA256 required")
    require(expected is None or record["sha256"] == expected, "frozen expected pin differs")
    require(digest(record["path"]) == record["sha256"], "input pin differs: " + record["path"])


def validate_spec(spec):
    keys = {"runner_sha256", "original", "material", "encoder", "reflection", "public", "protocol",
            "original_protocol", "binding", "source", "source_files", "model", "historical_archive",
            "learner_seed", "node", "expected_hostname", "expected_boot_id", "gpu_index", "gpu_uuid",
            "lease_end", "reservation"}
    require(type(spec) is dict and set(spec) == keys, "closed specification differs")
    require(spec["runner_sha256"] == digest(SELF), "new runner pin differs")
    seed_value(spec["learner_seed"])
    require(spec["node"] == "node2" and type(spec["expected_hostname"]) is str and spec["expected_hostname"], "node2 hostname required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36, "boot binding required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] in (0, 1, 2) and
            type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "planned node2GPU0/1/2 UUID required")
    require(type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "finite lease required")
    for field in ("source", "model"):
        require(type(spec[field]) is str and Path(spec[field]).is_absolute(), "absolute source/base required")
    expected = dict(original=ORIGINAL_SHA, material=old.MATERIAL_SHA256, encoder=old.ENCODER_SHA256,
                    reflection=old.REFLECTION_SHA256, public=old.PUBLIC_SHA256, protocol=PROTOCOL_SHA,
                    original_protocol=OLD_PROTOCOL_SHA, binding=BINDING_SHA, historical_archive=ARCHIVE_SHA)
    for field, checksum in expected.items():
        pinned(spec[field], checksum)
    require(Path(spec["original"]["path"]).resolve() == ORIGINAL, "original helper location differs")
    pinned(spec["reservation"])
    source = Path(spec["source"])
    require(not (source / ".git").exists() and set(spec["source_files"]) == set(old.SOURCE_NAMES) and
            tree(source) == spec["source_files"], "four-file frozen source differs")


def apis(spec):
    validate_spec(spec)
    material = old.load_module(spec["material"], "full_dose_material")
    encoder = old.load_module(spec["encoder"], "full_dose_encoder")
    reflection = old.load_module(spec["reflection"], "full_dose_reflection")
    probe = old.load_probe(spec["public"]["path"], spec["public"]["sha256"])
    for name, checksum in dict(material.PINS, **{"organism_v6/train_adapter_v3.py":
                                               material.REUSE["organism_v6/train_adapter_v3.py"]}).items():
        require(spec["source_files"][name] == checksum, "frozen source pin differs")
    require(spec["source_files"]["organism_v6/__init__.py"] == hashlib.sha256(b"").hexdigest(), "source init differs")
    return material, encoder, reflection, probe


def protected(spec):
    return [SELF, spec["source"], spec["model"]] + [value["path"] for value in spec.values()
                                                        if type(value) is dict and set(value) == {"path", "sha256"}]


def fresh(path, inputs):
    path = Path(path)
    require(path.is_absolute(), "absolute output required")
    resolved = path.resolve()
    require(not path.exists() and not path.is_symlink(), "fresh root required; no resume/retry")
    for value in inputs:
        other = Path(value).resolve()
        require(resolved != other and resolved not in other.parents and other not in resolved.parents,
                "output overlaps protected input")
    return resolved


def allocation(spec, root, launch=False):
    pinned(spec["reservation"])
    reservation = read(spec["reservation"]["path"])
    fields = ("node", "expected_hostname", "expected_boot_id", "gpu_index", "gpu_uuid", "lease_end", "learner_seed")
    require(reservation == dict(scope=SCOPE, root=str(Path(root).resolve()), **{field: spec[field] for field in fields}),
            "root-bound reservation receipt differs")
    require(socket.gethostname() == spec["expected_hostname"] and
            Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "node/boot differs")
    require(time.time() + COLLECTION_SECONDS + LEASE_MARGIN + (OUTER_SECONDS if launch else 0) < spec["lease_end"],
            "six-hour lease finish margin required")


def encode_training(rows, tokenizer, trainer, probe, encoder, seed):
    seed_value(seed)
    require(len(rows) == 12 and len({row["row_id"] for row in rows}) == 12, "twelve distinct training rows required")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "distinct PAD/EOS required")
    pairs = [encoder.training_item(row, tokenizer, trainer, probe, index) for index, row in enumerate(rows)]
    items, audits = map(list, zip(*pairs))
    segments = []
    for index, (item, audit) in enumerate(zip(items, audits, strict=True)):
        values = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
        require(len(values) == 1, "split/dropped training row")
        segment = values[0]
        require(segment.ids == audit["input_ids"] and segment.labels == audit["labels"] and
                segment.context_dropped == segment.target_dropped == 0 and len(segment.ids) <= 1024,
                "training encoding/mask/truncation mismatch")
        require([token for token in segment.labels if token != -100] == audit["supervised_ids"] and
                audit["supervised_ids"][-1] == tokenizer.eos_token_id and
                audit["supervised_ids"].count(tokenizer.eos_token_id) == 1, "target/EOS mask mismatch")
        segments.append(segment)
    packs = trainer.pack_by_group(segments, 1024, False)
    require(len(packs) == 12 and all(len(pack) == 1 for pack in packs), "unpacked rows required")
    orders, padded, updates = [], 0, 0
    expected_groups = sorted(row["row_id"] for row in rows)
    for epoch in range(112):
        order = trainer.epoch_order(packs, seed, epoch, True)
        groups = [pack[0].group for pack in order]
        require(sorted(groups) == expected_groups, "epoch dropped/duplicated source row")
        orders.append(groups)
        for start in range(0, 12, 4):
            selected = order[start:start + 4]
            batch = trainer.collate(selected, tokenizer.pad_token_id)
            require(len(batch["input_ids"]) == len(batch["labels"]) == 4, "batch size differs")
            for pack, ids, labels in zip(selected, batch["input_ids"], batch["labels"], strict=True):
                segment = pack[0]
                require(ids[:len(segment.ids)] == segment.ids and labels[:len(segment.labels)] == segment.labels and
                        all(label == -100 for label in labels[len(segment.labels):]), "collate source/padding mask mismatch")
                padded += len(ids)
            updates += 1
    require(updates == 336, "full dose update mismatch")
    target = sum(len(audit["supervised_ids"]) for audit in audits)
    total = sum(len(audit["input_ids"]) for audit in audits)
    return dict(items=items, encoding=audits, epoch_order=orders, learner_seed=seed,
                target_tokens=target, total_tokens=total,
                costs=dict(rows=12, epochs=112, updates=336, presentations=1344,
                           target_tokens_per_epoch=target, total_tokens_per_epoch=total,
                           context_and_masked_tail_tokens_per_epoch=total-target,
                           supervised_tokens=112*target, padded_tokens=padded))


def prepare_inputs(spec, material, encoder, probe):
    corpus = material.load_corpus(spec["source"])
    _, trainer = old.source_api(spec["source"])
    dataset = material.build_dataset(corpus)
    require(hashlib.sha256(material.encoded(dataset)).hexdigest() == old.MATERIAL_DATA_SHA256, "frozen material changed")
    tokenizer = probe.native_tokenizer(spec["model"])
    trains = {arm: encode_training(dataset["training"][arm], tokenizer, trainer, probe, encoder, spec["learner_seed"])
              for arm in ARMS}
    require(trains["plain"]["epoch_order"] == trains["contrastive"]["epoch_order"], "paired epoch orders differ")
    require([row["supervised_ids"] for row in trains["plain"]["encoding"]] ==
            [row["supervised_ids"] for row in trains["contrastive"]["encoding"]], "paired supervision differs")
    calls = {panel: [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                          native=probe.render(tokenizer, row["input_messages"]))
                     for index, row in enumerate(dataset["evaluation"][panel])] for panel in PANELS}
    require(all(len(values) == 12 for values in calls.values()), "four twelve-row panels required")
    for values in calls.values():
        for call in values:
            require(len(call["native"]["prompt_token_ids"]) + old.PARAMS["max_tokens"] <= old.ENGINE["max_model_len"], "readout overflow")
    return dataset, trains, calls, asdict(trainer.TrainConfig(**recipe(spec["learner_seed"]), model=spec["model"])), tokenizer.chat_template


def validate_prepared(prepared, rows, seed, trainer):
    require(type(prepared["learner_seed"]) is int and prepared["learner_seed"] == seed_value(seed), "prepared learner seed differs")
    require(len(prepared["items"]) == len(prepared["encoding"]) == len(rows) == 12, "prepared row count differs")
    for index, (item, audit, row) in enumerate(zip(prepared["items"], prepared["encoding"], rows, strict=True)):
        require(item["group"] == audit["row_id"] == row["row_id"] and item["order"] == index and
                item["meta"]["target_sha256"] == row["target_sha256"], "prepared source/target/order mismatch")
        require(len(audit["labels"]) == len(audit["input_ids"]) <= 1024 and
                [token for token in audit["labels"] if token != -100] == audit["supervised_ids"], "prepared mask mismatch")
    packs = [[SimpleNamespace(group=item["group"])] for item in sorted(prepared["items"], key=lambda item: (item["group"], item["order"]))]
    expected = [[pack[0].group for pack in trainer.epoch_order(packs, seed, epoch, True)] for epoch in range(112)]
    require(prepared["epoch_order"] == expected, "prepared seed/epoch schedule mismatch")
    require(prepared["target_tokens"] == sum(len(row["supervised_ids"]) for row in prepared["encoding"]) and
            prepared["total_tokens"] == sum(len(row["input_ids"]) for row in prepared["encoding"]), "prepared token counts differ")
    costs = prepared["costs"]
    require((costs["rows"], costs["epochs"], costs["updates"], costs["presentations"]) == (12, 112, 336, 1344) and
            costs["supervised_tokens"] == 112*prepared["target_tokens"], "prepared dose differs")


def import_off(record, dataset, calls, template, binding, probe):
    pinned(record, ARCHIVE_SHA)
    selected, hashes = {}, {}
    with tarfile.open(record["path"], "r:") as archive:
        members = archive.getmembers()
        require(len({entry.name for entry in members}) == len(members), "duplicate archive member")
        index = {entry.name: entry for entry in members}
        def take(name, expected=None):
            entry = index[name]
            require(entry.isfile() and not entry.issym() and not entry.islnk() and entry.size < 16*1024*1024, "invalid historical member")
            raw = archive.extractfile(entry).read()
            checksum = hashlib.sha256(raw).hexdigest()
            require(expected is None or checksum == expected, "historical member pin differs: " + name)
            value = json.loads(raw, object_pairs_hook=old.unique_object,
                               parse_constant=lambda value: require(False, "nonfinite historical JSON"))
            selected[name], hashes[name] = value, checksum
            return value
        previous = take(ARCHIVE_ROOT + "/plan.json", OLD_PLAN_SHA)
        complete = take(ARCHIVE_ROOT + "/capture_complete.json", OLD_COMPLETE_SHA)
        collection = take(ARCHIVE_ROOT + "_collected/collection.json")
        take(ARCHIVE_ROOT + "_collected/scores.json", OLD_SCORES_SHA)
        require(collection["scores_sha256"] == OLD_SCORES_SHA and collection["completion_sha256"] == OLD_COMPLETE_SHA,
                "historical collection join differs")
        require(complete["plan_sha256"] == OLD_PLAN_SHA and complete["calls"] == 144 and complete["scored"] is False,
                "historical completion differs")
        require(previous["self_sha256"] == ORIGINAL_SHA and previous["scope"] == old.SCOPE and
                previous["engine"] == old.ENGINE and previous["params"] == old.PARAMS and
                previous["chat_template"] == template and previous["binding"] == binding,
                "historical base/inference/template binding differs")
        take(ARCHIVE_ROOT + "/material.json", old.MATERIAL_DATA_SHA256)
        material_bytes = (json.dumps(dataset, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        require(hashlib.sha256(material_bytes).hexdigest() == old.MATERIAL_DATA_SHA256,
                "historical dataset bytes differ")
        historical_calls = take(ARCHIVE_ROOT + "/calls.json", previous["input_hashes"]["calls.json"])
        require(historical_calls == calls, "historical native prompt/row join differs")
        responses = {}
        for panel in PANELS:
            stage = "OFF__" + panel
            prefix = ARCHIVE_ROOT + "/run/" + stage + "/"
            inventory = complete["stages"][stage]
            closed = take(prefix + "closed.json", inventory["closed.json"])
            identity = take(prefix + "identity.json", inventory["identity.json"])
            require(identity == dict(cell=stage, model=previous["model"], revision=binding["revision"],
                                     model_files=binding["model_files"], adapter=None, adapter_files={},
                                     lora_request=None, engine=old.ENGINE, params=old.PARAMS), "historical OFF route differs")
            expected_names = {"identity.json"} | {call["call_id"] + suffix for call in calls[panel]
                                                   for suffix in (".request.json", ".response.json")}
            require(closed["calls"] == 12 and set(closed["files"]) == expected_names, "historical OFF inventory differs")
            for name in expected_names:
                require(closed["files"][name] == inventory[name], "historical closed/completion hash mismatch")
            for call in calls[panel]:
                stem = call["call_id"]
                require(take(prefix + stem + ".request.json", inventory[stem + ".request.json"]) == call, "historical request differs")
                response = take(prefix + stem + ".response.json", inventory[stem + ".response.json"])
                validate_response(probe, call, response, None)
                responses[panel + "/" + call["row_id"]] = dict(raw=response["text"], finish_reason=response["finish_reason"])
    require(len(responses) == 48, "historical OFF must have exactly48calls")
    return dict(archive=record, plan_sha256=OLD_PLAN_SHA, completion_sha256=OLD_COMPLETE_SHA,
                scores_sha256=OLD_SCORES_SHA, selected_member_hashes=hashes, selected_members=selected,
                responses=responses, historical=True, new_calls=0)


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "explicit native CPU tokenizer permission required")
    offline()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    require(digest(spec_path) == spec_sha256, "spec pin differs")
    spec = read(spec_path)
    require(Path(spec_path).read_bytes() == encoded(spec), "spec must use canonical encoded JSON")
    material, encoder, reflection, probe = apis(spec)
    root = fresh(root, protected(spec) + [spec_path])
    allocation(spec, root, launch=True)
    root.mkdir()
    write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
    try:
        binding = probe.scope_binding(read(spec["binding"]["path"]), spec["source"], spec["model"],
                                      spec["source_files"]["organism_v6/birth_skill_corpus.py"])
        require(binding["source_files"] == {name: spec["source_files"][name] for name in probe.SOURCE_NAMES} and
                binding["model_files"] == probe.model_hashes(spec["model"]) and
                binding["native_environment"] == probe.native_environment(), "official base/source/environment differs")
        dataset, trains, calls, config, template = prepare_inputs(spec, material, encoder, probe)
        history = import_off(spec["historical_archive"], dataset, calls, template, binding, probe)
        inputs = {"calls.json": calls, "costs.json": {arm: trains[arm]["costs"] for arm in ARMS},
                  "historical_OFF.json": history, **{f"train_{arm}.json": trains[arm] for arm in ARMS}}
        with (root / "material.json").open("xb") as stream:
            stream.write(material.encoded(dataset))
        for name, value in inputs.items():
            write(root / name, value)
        plan = dict(scope=SCOPE, claim=CLAIM, specification=spec, spec_sha256=spec_sha256, root=str(root),
                    source=spec["source"], model=spec["model"], learner_seed=spec["learner_seed"], config=config,
                    binding=binding, model_files=binding["model_files"], chat_template=template,
                    stages=list(STAGES), engine=old.ENGINE, params=old.PARAMS, budget=BUDGET,
                    gpu_uuid=spec["gpu_uuid"], gpu_index=spec["gpu_index"], lease_end=spec["lease_end"],
                    self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                    environment=old.environment(probe), input_hashes={name: digest(root / name) for name in ["material.json", *inputs]})
        apis(spec)
        write(root / "plan.json", plan)
        return dict(status="PREPARED_NOT_GPU_APPROVAL", root=str(root), plan_sha256=digest(root / "plan.json"), budget=BUDGET)
    except BaseException as error:
        failure(root / "prepare_failure.json", error)
        raise


def verify(root, pin, native=False):
    root = Path(root).resolve()
    require(digest(root / "plan.json") == pin, "plan pin differs")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "runtime identity differs")
    spec = plan["specification"]
    material, encoder, reflection, probe = apis(spec)
    require(hashlib.sha256(encoded(spec)).hexdigest() == plan["spec_sha256"], "spec must use canonical encoded JSON")
    require(plan["stages"] == list(STAGES) and plan["budget"] == BUDGET and
            plan["engine"] == old.ENGINE and plan["params"] == old.PARAMS, "closed lifecycle/budget differs")
    require(not (root / "prepare_failure.json").exists() and
            read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "failed/mismatched preparation")
    for field in ("source", "model", "learner_seed", "gpu_uuid", "gpu_index", "lease_end"):
        require(plan[field] == spec[field], "plan/spec mismatch: " + field)
    expected_inputs = {"material.json", "calls.json", "costs.json", "historical_OFF.json", "train_plain.json", "train_contrastive.json"}
    require(set(plan["input_hashes"]) == expected_inputs and plan["input_hashes"]["material.json"] == old.MATERIAL_DATA_SHA256,
            "input inventory differs")
    for name, checksum in plan["input_hashes"].items():
        require(digest(root / name) == checksum, "input changed: " + name)
    _, trainer = old.source_api(plan["source"])
    require(encoded(plan["config"]) == encoded(asdict(trainer.TrainConfig(**recipe(plan["learner_seed"]), model=plan["model"]))), "seed/config recipe differs")
    prepared = [read(root / f"train_{arm}.json") for arm in ARMS]
    require(all(train["learner_seed"] == plan["learner_seed"] and len(train["epoch_order"]) == 112 for train in prepared) and
            prepared[0]["epoch_order"] == prepared[1]["epoch_order"], "seed/epoch receipt differs")
    dataset = read(root / "material.json")
    for arm, train in zip(ARMS, prepared, strict=True):
        validate_prepared(train, dataset["training"][arm], plan["learner_seed"], trainer)
    require(read(root / "costs.json") == {arm: train["costs"] for arm, train in zip(ARMS, prepared, strict=True)}, "cost receipt differs")
    probe.validate_binding(plan["binding"], spec["source_files"]["organism_v6/birth_skill_corpus.py"])
    require(probe.public_model_files(read(spec["binding"]["path"]), plan["model"]) == plan["model_files"] == plan["binding"]["model_files"] and
            plan["binding"]["source_files"] == {name: spec["source_files"][name] for name in probe.SOURCE_NAMES}, "base binding differs")
    if native:
        require(old.environment(probe) == plan["environment"] and probe.model_hashes(plan["model"]) == plan["model_files"], "native environment/base changed")
    return plan, probe


def check_fit_manifest(manifest, prepared, plan, arm):
    require(encoded(manifest["config"]) == encoded(plan["config"]) and "warm_start" not in manifest and
            manifest["base_model"] == plan["model"] and manifest["empty"] is False and
            manifest["steps"] == manifest["micro_batches"] == 336 and manifest["epochs_run"] == 112 and
            manifest["nonfinite_batches"] == 0, "fresh full-dose manifest mismatch")
    corpus = manifest["corpus"]
    require(corpus["n_items"] == corpus["n_encoded"] == 12 and corpus["n_skipped_no_target"] == 0 and
            corpus["file"] == f"train_{arm}.json" and corpus["sha256"] == plan["input_hashes"][f"train_{arm}.json"], "fit source inventory differs")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncation/split")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == 12,
            "fit packing differs")
    require(manifest["tokens"]["target"] == prepared["target_tokens"] and
            manifest["train_tokens_seen"] == 112*prepared["total_tokens"], "fit exposure differs")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == 112 and all(type(value) in (int, float) and math.isfinite(value)
                                    for value in losses + [manifest["final_loss"]]), "nonfinite/incomplete fit loss")


def fit_one(plan, arm, probe):
    require(arm in ARMS, "unknown arm")
    root = Path(plan["root"])
    material, encoder, reflection, _ = apis(plan["specification"])
    _, trainer = old.source_api(plan["source"])
    prepared = read(root / f"train_{arm}.json")
    started = time.monotonic()
    tokenizer, base = reflection.load_native_model(plan["model"])
    require(not hasattr(base, "peft_config") and tokenizer.chat_template == plan["chat_template"], "fresh base/template required")
    actual = encode_training(read(root / "material.json")["training"][arm], tokenizer, trainer, probe, encoder, plan["learner_seed"])
    require(actual == prepared, "actual fit source/mask/seed/epoch drift")
    directory = root / "run" / ("fit_" + arm)
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh adapter required")
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["config"]), str(adapter),
                         corpus_sha=plan["input_hashes"][f"train_{arm}.json"], corpus_name=f"train_{arm}.json")
    trainable = [name for name, parameter in base.named_parameters() if parameter.requires_grad]
    require(trainable and all("lora_A" in name or "lora_B" in name for name in trainable), "non-LoRA trainability")
    check_fit_manifest(read(adapter / "train_manifest.json"), prepared, plan, arm)
    files = old.check_adapter(adapter, plan["config"])
    write(directory / "fit.json", dict(arm=arm, learner_seed=plan["learner_seed"], adapter=str(adapter), adapter_files=files,
                                       updates=336, presentations=1344, fresh_base=True,
                                       epoch_order_sha256=old.value_hash(prepared["epoch_order"]),
                                       trainable_names_sha256=old.value_hash(trainable), elapsed_seconds=time.monotonic()-started))


def adapter_for(plan, arm):
    require(arm in ARMS, "no OFF or unknown adapter state")
    directory = Path(plan["root"]) / "run" / ("fit_" + arm)
    adapter = directory / "adapter"
    require(directory.is_dir() and not directory.is_symlink() and adapter.is_dir() and not adapter.is_symlink(),
            "local fresh adapter directory required")
    receipt = read(directory / "fit.json")
    prepared = read(Path(plan["root"]) / f"train_{arm}.json")
    require(receipt["arm"] == arm and receipt["learner_seed"] == plan["learner_seed"] and
            receipt["adapter"] == str(adapter) and receipt["updates"] == 336 and receipt["presentations"] == 1344 and
            receipt["fresh_base"] is True and receipt["epoch_order_sha256"] == old.value_hash(prepared["epoch_order"]) and
            receipt["adapter_files"] == old.check_adapter(adapter, plan["config"]), "fresh adapter receipt differs")
    check_fit_manifest(read(adapter / "train_manifest.json"), prepared, plan, arm)
    return str(adapter), receipt["adapter_files"]


def validate_response(probe, call, response, route):
    require(response["lora_request"] == route, "native adapter route differs")
    require(all(type(response[key]) in (int, float) and math.isfinite(response[key]) for key in ("started", "ended")) and
            response["ended"] >= response["started"], "nonfinite/negative response duration")
    probe.validate_response(call, response)


def readout_identity(plan, arm, adapter, files):
    return dict(arm=arm, learner_seed=plan["learner_seed"], model=plan["model"], revision=plan["binding"]["revision"],
                model_files=plan["model_files"], adapter=adapter, adapter_files=files,
                lora_request=dict(name="perception", id=1, path=adapter), engine=old.ENGINE, params=old.PARAMS)


def capture(plan, arm, probe):
    adapter, files = adapter_for(plan, arm)
    directory = Path(plan["root"]) / "run" / ("readout_" + arm)
    identity = readout_identity(plan, arm, adapter, files)
    write(directory / "identity.json", identity)
    calls = read(Path(plan["root"]) / "calls.json")
    backend, names = None, ["identity.json"]
    try:
        backend = old.Native(plan, probe, adapter)
        for panel in PANELS:
            for call in calls[panel]:
                stem = panel + "__" + call["call_id"]
                write(directory / (stem + ".request.json"), call)
                response = backend.generate(call["messages"])
                write(directory / (stem + ".response.json"), response)
                validate_response(probe, call, response, identity["lora_request"])
                names.extend(stem + suffix for suffix in (".request.json", ".response.json"))
    finally:
        if backend is not None:
            backend.close()
    require(len(names) == 97 and tree(adapter) == files, "readout cardinality/adapter drift")
    write(directory / "closed.json", dict(calls=48, files={name: digest(directory / name) for name in names}))


def process_identity(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, pgid=int(fields[2]), start_ticks=int(fields[19]))


def absent(receipt, probe):
    require(type(receipt["pid"]) is int and receipt["pid"] > 1, "invalid process receipt")
    require(not Path(f"/proc/{receipt['pid']}").exists() and not probe.group_alive(receipt["pgid"]), "recorded process/group still exists")


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES and os.getpid() == os.getpgrp(), "explicit owned worker required")
    offline()
    directory = Path(root) / "run" / stage
    parent = os.getppid()
    limit = time.monotonic() + 5
    while not (directory / "launch.json").exists() and time.monotonic() < limit:
        require(os.getppid() == parent > 1, "controller disappeared")
        time.sleep(.05)
    launch = read(directory / "launch.json")
    require(launch["pid"] == launch["pgid"] == os.getpid() and launch["parent_pid"] == parent and
            launch["stage"] == stage and launch["plan_sha256"] == plan_sha256, "launch ownership mismatch")
    stop = threading.Event()
    def watch_owner():
        while not stop.wait(.1):
            if os.getppid() != parent or time.monotonic() >= launch["deadline_monotonic"]:
                os.killpg(os.getpgrp(), signal.SIGKILL)
                return
    threading.Thread(target=watch_owner, daemon=True).start()
    try:
        with budget(launch["deadline_monotonic"] - time.monotonic()):
            plan, probe = verify(root, plan_sha256, native=True)
            allocation(plan["specification"], root)
            require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"], "worker UUID environment differs")
            write(directory / "started.json", dict(**process_identity(os.getpid()), stage=stage,
                                                   plan_sha256=plan_sha256, parent_pid=parent, time=time.time()))
            kind, arm = stage.split("_", 1)
            if kind == "fit":
                fit_one(plan, arm, probe)
            else:
                capture(plan, arm, probe)
    except BaseException as error:
        failure(directory / "failure.json", error)
        raise
    finally:
        stop.set()


def run_stage(plan, pin, stage, deadline, probe):
    require(stage in STAGES, "unknown stage")
    require(deadline - time.monotonic() > 30 + CLEANUP_SECONDS, "no vacancy/release budget")
    allocation(plan["specification"], plan["root"])
    require(probe.gpu_state(plan) is True, "assigned GPU not vacant; no foreign kills")
    seconds = min(STAGE_SECONDS[stage], deadline-time.monotonic()-CLEANUP_SECONDS)
    require(seconds > 0, "stage budget exhausted")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", pin,
               "--stage", stage, "--allow-gpu"]
    process = None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            process = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]),
                                       stdout=output, stderr=errors, start_new_session=True)
            write(directory / "launch.json", dict(pid=process.pid, pgid=process.pid, parent_pid=os.getpid(), stage=stage,
                                                  plan_sha256=pin, deadline_monotonic=time.monotonic()+seconds))
            require(process.wait(timeout=seconds) == 0, "worker failed: " + stage)
    finally:
        if process is not None:
            try:
                probe.cleanup(process)
                require(not probe.group_alive(process.pid), "owned group survived cleanup")
                require(probe.gpu_state(plan) is True, "GPU release not confirmed")
                allocation(plan["specification"], plan["root"])
                write(directory / "released.json", dict(pid=process.pid, pgid=process.pid, time=time.time()))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, pin, probe):
    root = Path(plan["root"])
    require({entry.name for entry in (root / "run").iterdir()} == set(STAGES), "four genuine stages required")
    inventory, processes = {}, []
    calls = read(root / "calls.json")
    controller = read(root / "controller_started.json")
    for stage in STAGES:
        directory = root / "run" / stage
        require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage not scorable")
        started, launched, released = (read(directory / name) for name in ("started.json", "launch.json", "released.json"))
        require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == started["pgid"] ==
                launched["pid"] == launched["pgid"] == released["pid"] == released["pgid"] and
                started["parent_pid"] == launched["parent_pid"] == controller["pid"] and
                started["stage"] == launched["stage"] == stage and started["plan_sha256"] == launched["plan_sha256"] == pin,
                "stage process/plan custody differs")
        absent(started, probe)
        processes.append(started["pid"])
        kind, arm = stage.split("_", 1)
        adapter, files = adapter_for(plan, arm)
        if kind == "readout":
            identity, closed = read(directory / "identity.json"), read(directory / "closed.json")
            require(identity == readout_identity(plan, arm, adapter, files), "readout identity differs")
            expected = {"identity.json"} | {panel+"__"+call["call_id"]+suffix for panel in PANELS for call in calls[panel]
                                              for suffix in (".request.json", ".response.json")}
            require(closed["calls"] == 48 and set(closed["files"]) == expected, "raw readout inventory differs")
            require({path.name for path in directory.glob("*.response.json")} == {name for name in expected if name.endswith(".response.json")},
                    "unexpected native responses")
            for name, checksum in closed["files"].items():
                require(digest(directory / name) == checksum, "raw capture changed")
            for panel in PANELS:
                for call in calls[panel]:
                    stem = panel + "__" + call["call_id"]
                    require(read(directory / (stem+".request.json")) == call, "captured prompt differs")
                    validate_response(probe, call, read(directory / (stem+".response.json")), identity["lora_request"])
        inventory[stage] = tree(directory)
    require(len(set(processes)) == 4, "four distinct fresh processes required")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True and os.getpid() == os.getpgrp(), "Main-only fresh-process-group controller required")
    offline()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    root = Path(root).resolve()
    deadline = time.monotonic()+OUTER_SECONDS
    owns_claim = False
    try:
        with budget(OUTER_SECONDS-CLEANUP_SECONDS):
            plan, probe = verify(root, plan_sha256, native=True)
            allocation(plan["specification"], root, launch=True)
            write(root / "controller_started.json", dict(**process_identity(os.getpid()), plan_sha256=plan_sha256, time=time.time()))
            owns_claim = True
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(plan, plan_sha256, stage, deadline, probe)
            inventory = validate_completed(plan, plan_sha256, probe)
            require(time.monotonic() < deadline, "outer deadline exhausted")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory, calls=96,
                                                       fits=2, updates=672, scored=False, time=time.time(),
                                                       elapsed_seconds=OUTER_SECONDS-(deadline-time.monotonic())))
        return dict(status="ALL_CAPTURES_CLOSED_UNSCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        if owns_claim:
            failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    deadline = time.monotonic()+COLLECTION_SECONDS
    with budget(COLLECTION_SECONDS):
        return _collect(root, plan_sha256, completion_sha256, out, deadline)


def _collect(root, plan_sha256, completion_sha256, out, deadline):
    offline()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    root = Path(root).resolve()
    plan, probe = verify(root, plan_sha256)
    out = fresh(out, protected(plan["specification"]) + [root])
    absent(read(root / "controller_started.json"), probe)
    claim = root.with_name(root.name + ".collection_claim.json")
    write(claim, dict(plan_sha256=plan_sha256, completion_sha256=completion_sha256, out=str(out), retry=False))
    out.mkdir()
    try:
        with budget(deadline-time.monotonic()):
            require(not (root / "controller_failure.json").exists(), "failed controller never scored")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and complete["calls"] == 96 and complete["fits"] == 2 and
                    complete["updates"] == 672 and complete["scored"] is False, "incomplete pair")
            require(validate_completed(plan, plan_sha256, probe) == complete["stages"], "completed custody changed")
            material = old.load_module(plan["specification"]["material"], "full_dose_score")
            corpus = material.load_corpus(plan["source"])
            dataset, calls = read(root / "material.json"), read(root / "calls.json")
            history = import_off(plan["specification"]["historical_archive"], dataset, calls, plan["chat_template"], plan["binding"], probe)
            require(history == read(root / "historical_OFF.json"), "historical import changed")
            responses, costs = {"OFF": history["responses"]}, {}
            for arm in ARMS:
                responses[arm] = {}
                for panel in PANELS:
                    values = []
                    for call in calls[panel]:
                        response = read(root / "run" / ("readout_"+arm) / (panel+"__"+call["call_id"]+".response.json"))
                        responses[arm][panel+"/"+call["row_id"]] = dict(raw=response["text"], finish_reason=response["finish_reason"])
                        values.append(response)
                    costs[arm+"__"+panel] = dict(calls=12, prompt_tokens=sum(len(value["actual_prompt_token_ids"]) for value in values),
                                                output_tokens=sum(len(value["output_token_ids"]) for value in values),
                                                generation_seconds=sum(value["ended"]-value["started"] for value in values))
            scores = material.score_dataset(corpus, dataset, responses)
            canaries = {arm: {key: dict(historical_OFF_correct=baseline["strict_pass"], arm_correct=scores["states"][arm]["items"][key]["strict_pass"],
                                       lost=baseline["strict_pass"] and not scores["states"][arm]["items"][key]["strict_pass"])
                              for key, baseline in scores["states"]["OFF"]["items"].items() if key.startswith("C-")} for arm in ARMS}
            report = dict(scope=SCOPE, claim=CLAIM, learner_seed=plan["learner_seed"], plan_sha256=plan_sha256,
                          completion_sha256=completion_sha256, calls=96, historical_OFF=dict(archive=history["archive"],
                          plan_sha256=OLD_PLAN_SHA, completion_sha256=OLD_COMPLETE_SHA, scores_sha256=OLD_SCORES_SHA, new_calls=0),
                          fits={arm: dict(receipt=read(root / "run" / ("fit_"+arm) / "fit.json"),
                                          manifest=read(root / "run" / ("fit_"+arm) / "adapter/train_manifest.json")) for arm in ARMS},
                          material_scores=scores, per_item_canaries=canaries, generation_costs=costs,
                          prepared_costs=read(root / "costs.json"), controller_elapsed_seconds=complete["elapsed_seconds"],
                          budget=BUDGET, automatic_pass=False, scientific_pass=None)
            write(out / "scores.json", report)
            write(out / "collection.json", dict(plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                                                scores_sha256=digest(out / "scores.json")))
            return dict(status="COLLECTED_EXPLORATORY_DEV_ONLY", out=str(out), scores_sha256=digest(out / "scores.json"))
    except BaseException as error:
        failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        prep.add_argument("--"+name, required=True)
    prep.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
        else:
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--stage", required=True, choices=STAGES)
    args = vars(parser.parse_args(argv))
    operation = args.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[operation](**args)
    if result is not None:
        print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
