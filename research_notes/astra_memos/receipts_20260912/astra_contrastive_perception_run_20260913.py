"""Bounded authored Level0/1 contrastive perception; Main alone launches native work.

Prepare uses the native tokenizer on CPU, never a model. Two cold fits precede
twelve isolated readouts. Collection alone scores, after all raw captures close.
Pinned original public/reflection helpers retain their existing native semantics.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import contextlib
from dataclasses import asdict
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = "authored_contrastive_perception_twofits_fourpanels_v1"
ARMS = ("plain", "contrastive")
STATES = ("OFF", "plain", "contrastive")
PANELS = ("D1", "D2", "C-record", "C-general")
CELLS = tuple(f"{state}__{panel}" for state in STATES for panel in PANELS)
STAGES = ("fit_plain", "fit_contrastive") + CELLS
MATERIAL_SHA256 = "b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d"
MATERIAL_DATA_SHA256 = "7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66"
ENCODER_SHA256 = "f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51"
PUBLIC_SHA256 = "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
REFLECTION_SHA256 = "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
LEASE_MARGIN = 21600
OUTER_SECONDS, COLLECTION_SECONDS = 2700, 180
GPU_QUERY_SECONDS, GROUP_CLEANUP_SECONDS = 30, 10
CLEANUP_SECONDS = GROUP_CLEANUP_SECONDS + GPU_QUERY_SECONDS
FIT_SECONDS, READOUT_SECONDS = 600, 240
SOURCE_NAMES = ("organism_v6/__init__.py", "organism_v6/birth_skill_corpus.py",
                "organism_v6/rulegame_parenting_diagnostic.py", "organism_v6/train_adapter_v3.py")
PARAMS = dict(temperature=0.0, seed=0, max_tokens=192, top_p=1.0, top_k=-1, n=1,
              presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0, ignore_eos=False)
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=0.85, enforce_eager=True, enable_lora=True,
              max_lora_rank=32, enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False)
RECIPE = dict(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=4, max_len=1024,
              seed=0, overflow="truncate", batch_size=4, grad_accum=1, pack=False,
              shuffle_groups=True, chat_template=False, add_eos=False, optimizer="adamw",
              grad_checkpoint=True, device="cuda", dtype="bf16", max_steps=0)
CLAIM = "Authored Level0/1 material only; unequal context costs; no child SLEEP, clean ancestry, mechanism freeze, L2/P1/H1/H2 or scientific promotion."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with temporary.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()


def failure(path, error):
    if not Path(path).exists():
        write(path, dict(error_type=type(error).__name__, error=str(error), time=time.time(), retry=False))


def tree(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        require(not path.is_symlink(), "symlink in artifact tree")
        if path.is_file():
            result[str(path.relative_to(root))] = digest(path)
        else:
            require(path.is_dir(), "special artifact file")
    return result


def offline():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1", DO_NOT_TRACK="1",
                      VLLM_WORKER_MULTIPROC_METHOD="spawn", PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True


def load_probe(path, expected):
    require(digest(path) == expected, "Boyle final driver hash differs")
    spec = importlib.util.spec_from_file_location("perception_final_public_probe", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(isinstance(module.ANCHOR, str) and module.ANCHOR.strip(), "missing Boyle anchor")
    require(getattr(module, "GPU_QUERY_SECONDS", None) == GPU_QUERY_SECONDS, "Boyle final driver must allow 30s NVML queries")
    return module


def source_api(source):
    source = Path(source).resolve()
    sys.path.insert(0, str(source))
    modules = [importlib.import_module("organism_v6." + name)
               for name in ("birth_skill_corpus", "train_adapter_v3")]
    for module in modules:
        require(Path(module.__file__).resolve().parent.parent == source, "wrong source import")
    return modules


def environment(probe):
    return dict(probe=probe.native_environment(), peft=importlib.metadata.version("peft"))


def token_ids(value):
    if isinstance(value, Mapping):
        value = value.get("input_ids")
    require(isinstance(value, (list, tuple)) and value and
            all(type(token) is int and token >= 0 for token in value), "invalid tokenizer token vector")
    return list(value)


def load_module(record, name):
    require(set(record) == {"path", "sha256"} and digest(record["path"]) == record["sha256"], name + " pin differs")
    specification = importlib.util.spec_from_file_location("contrastive_" + name, record["path"])
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def checked_apis(specification):
    for key in ("material", "encoder", "reflection", "public", "protocol", "binding"):
        require(digest(specification[key]["path"]) == specification[key]["sha256"], key + " pin differs")
    require(specification["material"]["sha256"] == MATERIAL_SHA256 and
            specification["encoder"]["sha256"] == ENCODER_SHA256, "frozen material/encoder pin differs")
    require(specification["public"]["sha256"] == PUBLIC_SHA256 and
            specification["reflection"]["sha256"] == REFLECTION_SHA256, "unchanged public/reflection helper pins required")
    require(specification["runner_sha256"] == digest(SELF), "runner pin differs")
    material = load_module(specification["material"], "material")
    archive = load_module(specification["encoder"], "encoder")
    reflection = load_module(specification["reflection"], "reflection")
    probe = load_probe(specification["public"]["path"], specification["public"]["sha256"])
    require(reflection.GPU_QUERY_SECONDS == 30, "reflection query budget differs")
    source = Path(specification["source"])
    require(not (source / ".git").exists() and set(specification["source_files"]) == set(SOURCE_NAMES), "fresh four-file source required")
    require(tree(source) == specification["source_files"], "source snapshot differs")
    for name, checksum in dict(material.PINS, **{"organism_v6/train_adapter_v3.py": material.REUSE["organism_v6/train_adapter_v3.py"]}).items():
        require(specification["source_files"][name] == checksum, "frozen source pin differs")
    return material, archive, reflection, probe


def prepare_inputs(specification, material, archive, probe):
    corpus = material.load_corpus(specification["source"])
    _, trainer = source_api(specification["source"])
    dataset = material.build_dataset(corpus)
    require(material.digest(material.encoded(dataset)) == MATERIAL_DATA_SHA256, "canonical material differs from Main's frozen candidate")
    tokenizer = probe.native_tokenizer(specification["model"])
    trains = {arm: archive.encode_training(dataset["training"][arm], tokenizer, trainer, probe) for arm in ARMS}
    require(trains["plain"]["epoch_order"] == trains["contrastive"]["epoch_order"], "arm epoch orders differ")
    require([row["supervised_ids"] for row in trains["plain"]["encoding"]] ==
            [row["supervised_ids"] for row in trains["contrastive"]["encoding"]], "paired target plus EOS differs")
    costs = {}
    for arm, prepared in trains.items():
        segments = [trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")[0]
                    for index, item in enumerate(prepared["items"])]
        packs = trainer.pack_by_group(segments, 1024, False)
        padded = 0
        for epoch in range(4):
            order = trainer.epoch_order(packs, 0, epoch, True)
            require(len(order) == 12, "twelve batches of four over four epochs required")
            for start in range(0, 12, 4):
                batch = trainer.collate(order[start:start + 4], tokenizer.pad_token_id)
                padded += sum(len(ids) for ids in batch["input_ids"])
        costs[arm] = dict(rows=12, epochs=4, updates=12, presentations=48,
                          target_tokens_per_epoch=prepared["target_tokens"], total_tokens_per_epoch=prepared["total_tokens"],
                          context_and_masked_tail_tokens_per_epoch=prepared["total_tokens"] - prepared["target_tokens"],
                          padded_tokens_four_epochs=padded, supervised_tokens_four_epochs=4 * prepared["target_tokens"],
                          per_row=[dict(row_id=row["row_id"], total_tokens=len(row["input_ids"]),
                                        supervised_tokens=len(row["supervised_ids"])) for row in prepared["encoding"]])
    calls = {panel: [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                          native=probe.render(tokenizer, row["input_messages"])) for index, row in enumerate(dataset["evaluation"][panel])]
             for panel in PANELS}
    require(all(len(rows) == 12 for rows in calls.values()), "four twelve-row panels required")
    for rows in calls.values():
        for call in rows:
            require(len(call["native"]["prompt_token_ids"]) + PARAMS["max_tokens"] <= ENGINE["max_model_len"], "readout context overflow")
    return dataset, trains, calls, costs, asdict(trainer.TrainConfig(**RECIPE, model=specification["model"])), tokenizer.chat_template


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "explicit --allow-native CPU tokenizer preflight required")
    offline()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    require(digest(spec_path) == spec_sha256, "spec pin differs")
    specification = read(spec_path)
    root = Path(root).resolve()
    require(not root.exists(), "fresh root required; no retry")
    require(type(specification["gpu_index"]) is int and specification["gpu_index"] >= 0 and
            isinstance(specification["gpu_uuid"], str) and specification["gpu_uuid"].startswith("GPU-"), "planned GPU binding")
    require(type(specification["lease_end"]) in (int, float) and math.isfinite(specification["lease_end"]) and
            specification["lease_end"] >= time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour finish margin required")
    protected = [specification["source"], specification["model"], spec_path, SELF] + [specification[key]["path"] for key in
                 ("material", "encoder", "reflection", "public", "protocol", "binding")]
    require(all(Path(value).is_absolute() and root != Path(value).resolve() and root not in Path(value).resolve().parents and
                Path(value).resolve() not in root.parents for value in protected), "absolute disjoint inputs/root required")
    root.mkdir()
    write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
    try:
        material, archive, reflection, probe = checked_apis(specification)
        binding = probe.scope_binding(read(specification["binding"]["path"]), specification["source"], specification["model"],
                                      specification["source_files"]["organism_v6/birth_skill_corpus.py"])
        require(binding["source_files"] == {name: specification["source_files"][name] for name in probe.SOURCE_NAMES} and
                binding["model_files"] == probe.model_hashes(specification["model"]) and
                binding["native_environment"] == probe.native_environment(), "public base/source/environment differs")
        dataset, trains, calls, costs, config, template = prepare_inputs(specification, material, archive, probe)
        inputs = {"material.json": dataset, "calls.json": calls, "costs.json": costs,
                  **{f"train_{arm}.json": trains[arm] for arm in ARMS}}
        for name, value in inputs.items():
            if name == "material.json":
                with (root / name).open("xb") as stream:
                    stream.write(material.encoded(value))
                    stream.flush()
                    os.fsync(stream.fileno())
            else:
                write(root / name, value)
        plan = dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=specification, spec_sha256=spec_sha256,
                    source=specification["source"], model=specification["model"], binding=binding, model_files=binding["model_files"],
                    config=config, chat_template=template, stages=list(STAGES), engine=ENGINE, params=PARAMS,
                    self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                    environment=environment(probe), gpu_index=specification["gpu_index"], gpu_uuid=specification["gpu_uuid"],
                    lease_end=specification["lease_end"], input_hashes={name: digest(root / name) for name in inputs},
                    budget=dict(controller=2700, collection=180, cleanup_in_controller=40, fits=2, readouts=12, calls=144,
                                feasibility="UNPROFILED; hard cap, not a throughput guarantee; never shrink panels or raise timeout"))
        checked_apis(specification)
        write(root / "plan.json", plan)
        return dict(status="CPU_NATIVE_TOKENIZER_PREFLIGHT_COMPLETE_NOT_GPU_APPROVAL", root=str(root),
                    plan_sha256=digest(root / "plan.json"), costs=costs, budget=plan["budget"])
    except BaseException as error:
        failure(root / "prepare_failure.json", error)
        raise


def verify(root, plan_sha256, native=False):
    root = Path(root).resolve()
    require(digest(root / "plan.json") == plan_sha256, "plan hash differs")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "runtime/interpreter identity differs")
    require(plan["stages"] == list(STAGES) and plan["engine"] == ENGINE and plan["params"] == PARAMS, "closed stage/configuration differs")
    require(read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            not (root / "prepare_failure.json").exists(), "preparation failed or binding differs")
    material, archive, reflection, probe = checked_apis(plan["specification"])
    for field in ("source", "model", "gpu_index", "gpu_uuid", "lease_end"):
        require(plan[field] == plan["specification"][field], "spec/plan field differs: " + field)
    require(set(plan["input_hashes"]) == {"material.json", "calls.json", "costs.json", "train_plain.json", "train_contrastive.json"}, "prepared inventory differs")
    require(plan["input_hashes"]["material.json"] == MATERIAL_DATA_SHA256, "canonical prepared material pin differs")
    for name, checksum in plan["input_hashes"].items():
        require(digest(root / name) == checksum, "prepared input differs")
    _, trainer = source_api(plan["source"])
    require(plan["config"] == asdict(trainer.TrainConfig(**RECIPE, model=plan["model"])), "fit recipe differs")
    if native:
        require(environment(probe) == plan["environment"] and probe.model_hashes(plan["model"]) == plan["model_files"], "native base/environment drift")
    return plan, probe


def load_native_model(model):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
    base = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16, device_map="cuda",
                                             local_files_only=True, trust_remote_code=False)
    require(not hasattr(base, "peft_config"), "fit must start from fresh base")
    return tokenizer, base


def check_fit_manifest(manifest, prepared, config):
    require(manifest["config"] == config and manifest["empty"] is False and manifest["steps"] == 12 and
            manifest["micro_batches"] == 12 and manifest["epochs_run"] == 4 and manifest["nonfinite_batches"] == 0,
            "fit completion/update mismatch")
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == 12 and
            manifest["corpus"]["n_skipped_no_target"] == 0, "fit dropped items")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncated/split items")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == 12,
            "fit packing differs")
    require(manifest["tokens"]["target"] == prepared["target_tokens"] and
            manifest["train_tokens_seen"] == 4 * prepared["total_tokens"], "fit exposure mismatch")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == 4 and all(type(value) in (int, float) and math.isfinite(value)
                                  for value in losses + [manifest["final_loss"]]), "nonfinite fit loss")


def check_adapter(adapter, config):
    inventory = tree(adapter)
    weights = [name for name in ("adapter_model.safetensors", "adapter_model.bin") if name in inventory]
    require(len(weights) == 1 and "adapter_config.json" in inventory and "DONE" in inventory, "incomplete adapter")
    saved = read(Path(adapter) / "adapter_config.json")
    require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05 and
            set(saved["target_modules"]) == set(config["target_modules"]) and saved.get("bias") == "none" and
            not saved.get("modules_to_save") and not saved.get("use_dora") and not saved.get("use_rslora"), "adapter structure differs")
    return inventory


def fit_one(plan, stage, probe):
    _, trainer = source_api(plan["source"])
    arm = stage.removeprefix("fit_")
    prepared = read(Path(plan["root"]) / f"train_{arm}.json")
    fit_started = time.monotonic()
    reflection = load_module(plan["specification"]["reflection"], "reflection")
    tokenizer, base = reflection.load_native_model(plan["model"])
    require(tokenizer.chat_template == plan["chat_template"], "fit chat template changed")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "fit PAD/EOS changed")
    for index, (item, expected) in enumerate(zip(prepared["items"], prepared["encoding"], strict=True)):
        segments = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
        require(len(segments) == 1 and segments[0].ids == expected["input_ids"] and
                segments[0].labels == expected["labels"] and segments[0].context_dropped == segments[0].target_dropped == 0,
                "actual fit encoding/mask drift")
    directory = Path(plan["root"]) / "run" / stage
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh fit adapter output required")
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["config"]), str(adapter),
                         corpus_sha=plan["input_hashes"][f"train_{arm}.json"], corpus_name=f"train_{arm}.json")
    trainable = [name for name, parameter in base.named_parameters() if parameter.requires_grad]
    require(trainable and all("lora_A" in name or "lora_B" in name for name in trainable), "non-LoRA trainability")
    manifest = read(adapter / "train_manifest.json")
    check_fit_manifest(manifest, prepared, plan["config"])
    files = check_adapter(adapter, plan["config"])
    write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=files,
                                       trainable_names_sha256=value_hash(trainable), updates=12, presentations=48,
                                       elapsed_seconds=time.monotonic() - fit_started))


def adapter_for(plan, cell):
    state = cell.split("__")[0]
    if state == "OFF":
        return None, {}
    require(state in ARMS, "unknown fitted state")
    arm = state
    directory = Path(plan["root"]) / "run" / f"fit_{arm}"
    receipt = read(directory / "fit.json")
    adapter = directory / "adapter"
    require(receipt["arm"] == arm and receipt["adapter"] == str(adapter) and
            receipt["adapter_files"] == check_adapter(adapter, plan["config"]), "fitted adapter custody differs")
    check_fit_manifest(read(adapter / "train_manifest.json"), read(Path(plan["root"]) / f"train_{arm}.json"), plan["config"])
    return str(adapter), receipt["adapter_files"]


class Native:
    def __init__(self, plan, probe, adapter):
        from vllm import LLM
        from vllm.lora.request import LoRARequest
        self.probe = probe
        self.llm = LLM(model=plan["model"], tokenizer=plan["model"], **ENGINE)
        self.tokenizer = self.llm.get_tokenizer()
        require(self.tokenizer.chat_template == plan["chat_template"], "readout template drift")
        self.route = None if adapter is None else dict(name="perception", id=1, path=adapter)
        self.lora = None if self.route is None else LoRARequest(self.route["name"], self.route["id"], self.route["path"])

    def generate(self, messages):
        import torch
        from vllm import SamplingParams
        native = self.probe.render(self.tokenizer, messages)
        started = time.monotonic()
        with torch.inference_mode():
            outputs = self.llm.generate([native["rendered_prompt"]], SamplingParams(**PARAMS), lora_request=self.lora, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "readout cardinality differs")
        output = outputs[0].outputs[0]
        return dict(**native, text=output.text, output_token_ids=list(output.token_ids),
                    actual_prompt_token_ids=list(outputs[0].prompt_token_ids), finish_reason=output.finish_reason,
                    stop_reason=output.stop_reason, decoded_output=self.tokenizer.decode(list(output.token_ids), skip_special_tokens=True),
                    started=started, ended=time.monotonic(), lora_request=self.route)

    def close(self):
        shutdown = getattr(self.llm, "shutdown", None)
        if shutdown is not None:
            shutdown()


def capture_cell(plan, cell, probe):
    adapter, files = adapter_for(plan, cell)
    directory = Path(plan["root"]) / "run" / cell
    route = None if adapter is None else dict(name="perception", id=1, path=adapter)
    identity = dict(cell=cell, model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                    adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS)
    write(directory / "identity.json", identity)
    calls = read(Path(plan["root"]) / "calls.json")[cell.split("__")[1]]
    backend = None
    try:
        backend = Native(plan, probe, adapter)
        for call in calls:
            write(directory / (call["call_id"] + ".request.json"), call)
            response = backend.generate(call["messages"])
            write(directory / (call["call_id"] + ".response.json"), response)
            require(response["lora_request"] == route, "actual LoRA route differs")
            probe.validate_response(call, response)
    finally:
        if backend is not None:
            backend.close()
    require(files == (tree(adapter) if adapter is not None else {}), "adapter changed during readout")
    names = ["identity.json"] + [call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")]
    write(directory / "closed.json", dict(calls=12, files={name: digest(directory / name) for name in names}))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu, "Main-only worker requires --allow-gpu")
    require(stage in STAGES and os.getpid() == os.getpgrp(), "worker must own a fresh process group")
    offline()
    plan, probe = verify(root, plan_sha256, native=True)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and time.time() < plan["lease_end"] - COLLECTION_SECONDS - LEASE_MARGIN,
            "worker device/lease differs")
    directory = Path(root) / "run" / stage
    write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, plan_sha256=plan_sha256, time=time.time()))
    try:
        if stage.startswith("fit_"):
            fit_one(plan, stage, probe)
        else:
            capture_cell(plan, stage, probe)
    except BaseException as error:
        failure(directory / "failure.json", error)
        raise


@contextlib.contextmanager
def budget(seconds):
    require(seconds > 0, "no remaining budget")
    def expired(signum, frame):
        raise TimeoutError("perception bounded deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def run_stage(plan, pin, stage, deadline, probe):
    require(deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS, "insufficient budget for vacancy and release checks")
    require(probe.gpu_state(plan) is True, "assigned GPU not vacant; no foreign process will be stopped")
    seconds = min(FIT_SECONDS if stage.startswith("fit_") else READOUT_SECONDS, deadline - time.monotonic() - CLEANUP_SECONDS)
    require(seconds > 0, "insufficient outer budget for next stage")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", pin,
               "--stage", stage, "--allow-gpu"]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"])
    process = None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            process = subprocess.Popen(command, env=env, stdout=output, stderr=errors, start_new_session=True)
            write(directory / "launch.json", dict(pid=process.pid, pgid=process.pid, stage=stage, plan_sha256=pin))
            require(process.wait(timeout=seconds) == 0, "native worker failed: " + stage)
    finally:
        if process is not None:
            try:
                probe.cleanup(process)
                require(not probe.group_alive(process.pid), "owned process group survived cleanup")
                require(probe.gpu_state(plan) is True, "GPU release not confirmed")
                write(directory / "released.json", dict(pid=process.pid, pgid=process.pid, time=time.time()))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, pin, probe):
    root = Path(plan["root"])
    processes, inventory = [], {}
    for stage in STAGES:
        directory = root / "run" / stage
        require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage cannot complete")
        started, launched, released = (read(directory / name) for name in ("started.json", "launch.json", "released.json"))
        require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == started["pgid"] ==
                launched["pid"] == launched["pgid"] == released["pid"] == released["pgid"] and
                started["stage"] == launched["stage"] == stage and started["plan_sha256"] == launched["plan_sha256"] == pin,
                "fresh process receipt mismatch")
        processes.append(started["pid"])
        if stage.startswith("fit_"):
            adapter_for(plan, stage.removeprefix("fit_") + "__D1")
        else:
            adapter, files = adapter_for(plan, stage)
            identity, closed = read(directory / "identity.json"), read(directory / "closed.json")
            route = None if adapter is None else dict(name="perception", id=1, path=adapter)
            require(identity == dict(cell=stage, model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                                     adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS), "readout identity mismatch")
            calls = read(root / "calls.json")[stage.split("__")[1]]
            expected_names = {"identity.json"} | {call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")}
            require(closed["calls"] == 12 and set(closed["files"]) == expected_names, "incomplete raw capture inventory")
            require({path.name for path in directory.glob("*.response.json")} == {call["call_id"] + ".response.json" for call in calls},
                    "raw response count mismatch")
            for name, expected in closed["files"].items():
                require(digest(directory / name) == expected, "raw capture changed")
            for call in calls:
                require(read(directory / (call["call_id"] + ".request.json")) == call, "captured request differs")
                response = read(directory / (call["call_id"] + ".response.json"))
                require(response["lora_request"] == route, "captured adapter route differs")
                probe.validate_response(call, response)
        inventory[stage] = tree(directory)
    require(len(set(processes)) == 14, "fits/readouts must use fourteen distinct fresh processes")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "Main-only controller requires --allow-gpu")
    offline()
    root = Path(root).resolve()
    write(root / "controller_started.json", dict(time=time.time(), plan_sha256=plan_sha256))
    deadline = time.monotonic() + OUTER_SECONDS
    try:
        with budget(OUTER_SECONDS - CLEANUP_SECONDS):
            plan, probe = verify(root, plan_sha256, native=True)
            require(plan["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN,
                    "launch no longer fits lease")
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(plan, plan_sha256, stage, deadline, probe)
            inventory = validate_completed(plan, plan_sha256, probe)
            require(time.monotonic() < deadline, "outer deadline exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory, calls=144,
                                                       scored=False, time=time.time(), elapsed_seconds=OUTER_SECONDS - (deadline - time.monotonic())))
        return dict(status="ALL_CAPTURES_CLOSED_UNSCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    root, out = Path(root).resolve(), Path(out).resolve()
    require(not out.exists() and root != out and root not in out.parents and out not in root.parents, "fresh external collection required")
    write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
    out.mkdir()
    try:
        with budget(COLLECTION_SECONDS):
            plan, probe = verify(root, plan_sha256)
            require(not (root / "controller_failure.json").exists(), "failed controller not scorable; preserve partial artifacts")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and complete["calls"] == 144 and complete["scored"] is False,
                    "all captures must close before scoring")
            require(validate_completed(plan, plan_sha256, probe) == complete["stages"], "completed custody changed")
            material = load_module(plan["specification"]["material"], "material")
            corpus = material.load_corpus(plan["source"])
            dataset = read(root / "material.json")
            responses, costs = {state: {} for state in STATES}, {}
            for cell in CELLS:
                state, panel = cell.split("__")
                values = []
                for index, row in enumerate(dataset["evaluation"][panel]):
                    response = read(root / "run" / cell / f"{index:02d}.response.json")
                    responses[state][panel + "/" + row["row_id"]] = dict(raw=response["text"], finish_reason=response["finish_reason"])
                    values.append(response)
                costs[cell] = dict(calls=12, prompt_tokens=sum(len(value["actual_prompt_token_ids"]) for value in values),
                                   output_tokens=sum(len(value["output_token_ids"]) for value in values),
                                   generation_seconds=sum(value["ended"] - value["started"] for value in values))
            scores = material.score_dataset(corpus, dataset, responses)
            fits = {arm: dict(receipt=read(root / "run" / ("fit_" + arm) / "fit.json"),
                              manifest=read(root / "run" / ("fit_" + arm) / "adapter/train_manifest.json")) for arm in ARMS}
            report = dict(scope=SCOPE, claim=CLAIM, plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          calls=144, fits=fits, generation_costs=costs, prepared_costs=read(root / "costs.json"),
                          material_scores=scores, automatic_pass=False, scientific_pass=None,
                          controller_elapsed_seconds=complete["elapsed_seconds"], budget_feasibility=plan["budget"])
            write(out / "scores.json", report)
            write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_AUTHORED_LEVEL0_1_ONLY", out=str(out), scores_sha256=digest(out / "scores.json"))
    except BaseException as error:
        failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name != "collect":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--stage", choices=STAGES, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    arguments = vars(parser.parse_args(argv))
    name = arguments.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**arguments)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
