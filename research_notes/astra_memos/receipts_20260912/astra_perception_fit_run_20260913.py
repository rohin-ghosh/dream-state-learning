"""Bounded authored perception SFT and matched readout; Main launches native work.

Prepare uses the native tokenizer on CPU, never a model. Two cold fits precede
six isolated readouts. Collection alone scores, after all raw captures close.
The caller supplies Boyle's FINAL driver hash; no development hash is frozen.
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
SCOPE = "authored_perception_12train_12dev_twofits_sixreadouts_v1"
ARMS = ("absent", "present")
STATES = ("OFF", "fitAbsent", "fitPresent")
CELLS = tuple(f"{state}__{anchor}" for state in STATES for anchor in ARMS)
STAGES = ("fit_absent", "fit_present") + CELLS
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
CLAIM = "AUTHOR_SOURCED_DEVELOPMENT_ONLY; exploratory record fidelity, not sleep, teacher distillation, L2 qualification or persistence"


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


def training_item(row, tokenizer, trainer, probe, index):
    """Full native assistant bytes, including EOS; template-only tail is masked."""
    require(row["skill"] == "perception" and row["source"]["split"] == "train" and
            row["source_admissible"] and isinstance(row["raw_target"], str), "perception TRAIN target required")
    prompt = probe.render(tokenizer, row["input_messages"])
    messages = row["input_messages"] + [{"role": "assistant", "content": row["raw_target"]}]
    full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    full_ids = token_ids(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False))
    require(full_ids == token_ids(tokenizer.encode(full_text, add_special_tokens=False)), "full-assistant template/token mismatch")
    prefix = prompt["rendered_prompt"]
    require(full_text.startswith(prefix + row["raw_target"]), "assistant prefix/target bytes changed")
    require(full_ids[:len(prompt["prompt_token_ids"])] == prompt["prompt_token_ids"], "assistant prefix token boundary changed")
    end_text, end_id = tokenizer.eos_token, tokenizer.eos_token_id
    require(isinstance(end_text, str) and end_text and type(end_id) is int, "native EOS unavailable")
    suffix = full_text[len(prefix + row["raw_target"]):]
    require(suffix.startswith(end_text), "native assistant end is not tokenizer EOS")
    trailer = suffix[len(end_text):]
    require(not trailer.strip() and token_ids(tokenizer.encode(end_text, add_special_tokens=False)) == [end_id],
            "unexpected assistant trailer/EOS encoding")
    spans = [[prefix, False, "context"], [row["raw_target"], True, "perception_record"],
             [end_text, True, "assistant_end"]]
    if trailer:
        spans.append([trailer, False, "template_tail"])
    item = trainer.normalize_items([dict(spans=spans, group=row["row_id"], order=index,
                                        view="perception", meta=dict(source_id=row["source"]["source_id"],
                                        row_id=row["row_id"], target_sha256=row["target_sha256"]))])[0]
    segments = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
    require(len(segments) == 1, "training row dropped or split")
    segment = segments[0]
    require(segment.context_dropped == segment.target_dropped == 0 and len(full_ids) <= 1024, "training truncation forbidden")
    target_ids = token_ids(tokenizer.encode(row["raw_target"], add_special_tokens=False))
    require(end_id not in target_ids, "target contains assistant end token")
    tail_ids = tokenizer.encode(trailer, add_special_tokens=False) if trailer else []
    labels = [-100] * len(prompt["prompt_token_ids"]) + target_ids + [end_id] + [-100] * len(tail_ids)
    require(segment.ids == full_ids and segment.labels == labels and len(labels) == len(full_ids),
            "actual v3 encoding/mask differs from full native assistant")
    batch = trainer.collate([[segment]], tokenizer.pad_token_id)
    require(batch["input_ids"] == [full_ids] and batch["labels"] == [labels], "actual collate changed target mask")
    audit = dict(row_id=row["row_id"], input_ids=full_ids, labels=labels,
                 supervised_ids=target_ids + [end_id], native_prompt=prompt,
                 full_assistant_text=full_text, template_tail=trailer)
    return item, audit


def encode_training(rows, tokenizer, trainer, probe):
    require(len(rows) == 12 and len({row["row_id"] for row in rows}) == 12, "TRAIN12 inventory required")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id,
            "distinct native PAD/EOS required")
    pairs = [training_item(row, tokenizer, trainer, probe, index) for index, row in enumerate(rows)]
    items, audits = map(list, zip(*pairs))
    segments = [trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")[0]
                for index, item in enumerate(items)]
    packs = trainer.pack_by_group(segments, 1024, False)
    orders = []
    for epoch in range(4):
        order = trainer.epoch_order(packs, 0, epoch, True)
        orders.append([pack[0].group for pack in order])
        for start in range(0, 12, 4):
            selected = order[start:start + 4]
            batch = trainer.collate(selected, tokenizer.pad_token_id)
            for pack, ids, labels in zip(selected, batch["input_ids"], batch["labels"], strict=True):
                segment = pack[0]
                require(ids[:len(segment.ids)] == segment.ids and labels[:len(segment.labels)] == segment.labels,
                        "actual batch changed source labels")
                require(all(label == -100 for label in labels[len(segment.labels):]), "padding receives loss")
    return dict(items=items, encoding=audits, epoch_order=orders,
                target_tokens=sum(len(row["supervised_ids"]) for row in audits),
                total_tokens=sum(len(row["input_ids"]) for row in audits))


def prepare(root, source, model, probe_driver, probe_sha256, binding_path, binding_sha256,
            corpus_sha256, gpu_uuid, gpu_index, lease_end):
    offline()
    root, source, model = map(lambda value: Path(value).resolve(), (root, source, model))
    probe = load_probe(probe_driver, probe_sha256)
    require(not root.exists() and all(probe.disjoint(root, path) for path in (source, model, probe_driver, binding_path)),
            "new disjoint run root required")
    require(type(gpu_index) is int and gpu_index >= 0 and isinstance(gpu_uuid, str) and gpu_uuid.startswith("GPU-"), "GPU binding required")
    require(math.isfinite(lease_end) and lease_end > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + CLEANUP_SECONDS,
            "insufficient lease for outer plus collection")
    root.mkdir()
    write(root / "prepare_started.json", dict(time=time.time(), scope=SCOPE))
    try:
        require(digest(binding_path) == binding_sha256, "Main base receipt hash differs")
        hashes = {name: digest(source / name) for name in SOURCE_NAMES}
        require(hashes[SOURCE_NAMES[1]] == corpus_sha256, "accepted corpus hash differs")
        binding = probe.scope_binding(read(binding_path), source, model, corpus_sha256)
        require(binding["source_files"] == {name: hashes[name] for name in probe.SOURCE_NAMES}, "base/source binding drift")
        require(binding["model_files"] == probe.model_hashes(model) and
                binding["native_environment"] == probe.native_environment(), "model/environment drift")
        corpus, trainer = source_api(source)
        tokenizer = probe.native_tokenizer(str(model))
        variants = {split: corpus.build_variants("perception", split=split, system_anchor=probe.ANCHOR)
                    for split in ("train", "dev")}
        trains, dev, calls = {}, {}, {}
        for anchor in ARMS:
            key = "supplied" if anchor == "present" else "absent"
            train, held = variants["train"][key], variants["dev"][key]
            require(corpus.audit_split_pair(train, held)["disjoint"], "train/dev source collision")
            trains[anchor] = encode_training(train["rows"], tokenizer, trainer, probe)
            dev[anchor] = held["rows"]
            require(len(dev[anchor]) == 12, "DEV12 inventory required")
            calls[anchor] = [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                                 native=probe.render(tokenizer, row["input_messages"])) for index, row in enumerate(dev[anchor])]
        require(trains["absent"]["epoch_order"] == trains["present"]["epoch_order"], "fit row order differs")
        require([row["supervised_ids"] for row in trains["absent"]["encoding"]] ==
                [row["supervised_ids"] for row in trains["present"]["encoding"]], "target/EOS exposure differs")
        require(dev == probe.fixed_rows(corpus), "Boyle anchor/probe source differs")
        for name, content in {"train_absent.json": trains["absent"], "train_present.json": trains["present"],
                              "dev.json": dev, "calls.json": calls}.items():
            write(root / name, content)
        config = asdict(trainer.TrainConfig(**RECIPE, model=str(model)))
        plan = dict(scope=SCOPE, claim=CLAIM, root=str(root), source=str(source), source_hashes=hashes,
                    model=str(model), binding=binding, model_files=binding["model_files"], environment=environment(probe),
                    probe_driver=str(Path(probe_driver).resolve()), probe_sha256=probe_sha256,
                    self_sha256=digest(SELF), python=os.path.abspath(sys.executable), anchor=probe.ANCHOR,
                    gpu_uuid=gpu_uuid, gpu_index=gpu_index, lease_end=lease_end, engine=ENGINE, params=PARAMS,
                    stages=list(STAGES), config=config, chat_template=tokenizer.chat_template,
                    outer_seconds=OUTER_SECONDS, collection_seconds=COLLECTION_SECONDS, gpu_query_seconds=GPU_QUERY_SECONDS,
                    input_hashes={name: digest(root / name) for name in ("train_absent.json", "train_present.json", "dev.json", "calls.json")})
        require(hashes == {name: digest(source / name) for name in SOURCE_NAMES}, "source changed during prepare")
        require(digest(probe_driver) == probe_sha256, "Boyle changed during prepare")
        write(root / "plan.json", plan)
        return dict(status="PREPARED_NOT_LAUNCHED", root=str(root), plan_sha256=digest(root / "plan.json"))
    except BaseException as error:
        failure(root / "prepare_failure.json", error)
        raise


def verify(root, plan_sha256, native=False):
    root = Path(root).resolve()
    require(digest(root / "plan.json") == plan_sha256, "plan hash differs")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable), "runtime identity differs")
    require(plan["stages"] == list(STAGES) and plan["engine"] == ENGINE and plan["params"] == PARAMS and
            plan["outer_seconds"] == OUTER_SECONDS and plan["collection_seconds"] == COLLECTION_SECONDS and
            plan["gpu_query_seconds"] == GPU_QUERY_SECONDS, "runtime scope differs")
    require(set(plan["source_hashes"]) == set(SOURCE_NAMES), "source inventory differs")
    for name, expected in plan["source_hashes"].items():
        require(digest(Path(plan["source"]) / name) == expected, "source changed: " + name)
    require(set(plan["input_hashes"]) == {"train_absent.json", "train_present.json", "dev.json", "calls.json"},
            "prepared input inventory differs")
    for name, expected in plan["input_hashes"].items():
        require(name in ("train_absent.json", "train_present.json", "dev.json", "calls.json") and digest(root / name) == expected,
                "prepared input differs")
    probe = load_probe(plan["probe_driver"], plan["probe_sha256"])
    require(plan["anchor"] == probe.ANCHOR, "Boyle anchor differs")
    _, trainer = source_api(plan["source"])
    require(plan["config"] == asdict(trainer.TrainConfig(**RECIPE, model=plan["model"])), "fit recipe differs")
    if native:
        require(environment(probe) == plan["environment"] and probe.model_hashes(plan["model"]) == plan["model_files"],
                "native environment/base differs")
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
    tokenizer, base = load_native_model(plan["model"])
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
                                       trainable_names_sha256=value_hash(trainable), updates=12, presentations=48))


def adapter_for(plan, cell):
    state = cell.split("__")[0]
    if state == "OFF":
        return None, {}
    arm = "absent" if state == "fitAbsent" else "present"
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
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and time.time() < plan["lease_end"] - COLLECTION_SECONDS,
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
    require(probe.gpu_state(plan), "assigned GPU not vacant; no foreign process will be stopped")
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
                require(probe.gpu_state(plan), "GPU release not confirmed")
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
            adapter_for(plan, "fitAbsent__absent" if stage == "fit_absent" else "fitPresent__absent")
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
    require(len(set(processes)) == 8, "fits/readouts must use eight distinct fresh processes")
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
            require(plan["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + CLEANUP_SECONDS,
                    "launch no longer fits lease")
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(plan, plan_sha256, stage, deadline, probe)
            inventory = validate_completed(plan, plan_sha256, probe)
            require(time.monotonic() < deadline, "outer deadline exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory, calls=72,
                                                       scored=False, time=time.time()))
        return dict(status="ALL_CAPTURES_CLOSED_UNSCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    out = Path(out).resolve()
    require(not out.exists() and out != Path(root).resolve() and Path(root).resolve() not in out.parents,
            "fresh external collection directory required")
    out.mkdir()
    try:
        with budget(COLLECTION_SECONDS):
            plan, probe = verify(root, plan_sha256)
            root = Path(root)
            require(not (root / "controller_failure.json").exists(), "failed controller cannot score")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and complete["calls"] == 72 and complete["scored"] is False,
                    "all captures must precede scores")
            require(validate_completed(plan, plan_sha256, probe) == complete["stages"], "completion inventory changed")
            corpus, _ = source_api(plan["source"])
            dev = read(root / "dev.json")
            results = {}
            for cell in CELLS:
                rows = []
                for index, row in enumerate(dev[cell.split("__")[1]]):
                    response = read(root / "run" / cell / f"{index:02d}.response.json")
                    rows.append(dict(row_id=row["row_id"], source_id=row["source"]["source_id"],
                                     score=corpus.score_response(row, response["text"]),
                                     finish_reason=response["finish_reason"], response_sha256=digest(root / "run" / cell / f"{index:02d}.response.json")))
                results[cell] = dict(rows=rows, correct=sum(row["score"]["passed"] is True for row in rows), total=12,
                                     length_finishes=sum(row["finish_reason"] == "length" for row in rows))
            report = dict(scope=SCOPE, claim=CLAIM, plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          cells=results, calls=72, automatic_pass=False)
            write(out / "scores.json", report)
            write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
        return dict(status="COLLECTED_EXPLORATORY_ONLY", out=str(out), scores_sha256=digest(out / "scores.json"))
    except BaseException as error:
        failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("root", "source", "model", "probe-driver", "probe-sha256", "binding-path", "binding-sha256", "corpus-sha256", "gpu-uuid"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--gpu-index", type=int, required=True)
    prep.add_argument("--lease-end", type=float, required=True)
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
