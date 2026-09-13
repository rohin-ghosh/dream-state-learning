"""Read-only L2 teacher-forcing diagnostic, never an original endpoint promotion."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time


SCHEMA = "astra_l2_access_diagnostic_20260913_v2"
ROOT = Path("/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1")
SOURCE_FILES = {
    "gpu/astra_l2_public_record_dev.py": "213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e",
    "organism_v6/l2_public_record_dev.py": "0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352",
    "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7",
    "organism_v6/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
PLAN_PIN = "da6a2d651d152979afee1ab862ab9218ef571149705e4bff5ad1a4ebc0289125"
SEAL_PIN = "14a0e0b33998dba794642d014f1f9f5939b78e6956d1724f497660c7e239e42f"
COLLECTION_PIN = "a2d80c7e1e973d102a675507fc4d0ef40a1a25acd4516729ea9ade54dd90347f"
BASE_PIN = "1a28421dffcee174137818b590991ba80678b58f6c63fd8eab027a933486efd5"
CANDIDATES = {"OFF": None,
              "fit1": "95f7cc2489b3091537c8629aab814ed593ab44423c5303ddc7f77aae32ace286",
              "fit2_PROMOTE": "2e6778a24dfc72648504cbb39fc8866a4a6208330eac5dccf93bcf5431d7bf2e"}
HELPERS = {"public": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c",
           "reflection": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"}
VIEWS = ("train", "readout")
WORKER_FORWARDS, TOTAL_FORWARDS = 64, 192
WORKER_SECONDS, TOTAL_SECONDS = 400, 1200
CLAIM = "Teacher-forced access diagnostic only; not original vLLM generation, endpoint promotion, general G1, H1 or H2."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate field")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def external_output(path, protected):
    path = Path(path).absolute()
    require(".." not in path.parts and not any(part.is_symlink() for part in (path, *path.parents)), "output symlink/plain path")
    require(not path.exists() and path.parent.is_dir(), "output must be fresh with existing parent")
    for other in protected:
        other = Path(other).resolve()
        require(not path.is_relative_to(other) and not other.is_relative_to(path), "output overlaps protected input")
    return path


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def frozen_source(source):
    source = Path(source).absolute()
    require(not any(part.is_symlink() for part in (source, *source.parents)), "source symlink")
    inventory = {path.relative_to(source).as_posix(): digest(path) for path in source.rglob("*") if path.is_file()}
    require(not any(path.is_symlink() for path in source.rglob("*")) and inventory == SOURCE_FILES, "original source pins differ")
    return source


def collection_metadata(path):
    require(digest(path) == COLLECTION_PIN, "original collection pin differs")
    collection = read(path)
    require(collection["status"] == "COMPLETE" and collection["plan_sha256"] == PLAN_PIN and
            collection["seal_sha256"] == SEAL_PIN and collection["work"] == dict(calls=128, fits=3, updates=100),
            "original collection identity")
    return collection


def candidate_encoding(runtime, tokenizer, probe, messages, action, suffix):
    require(suffix in ("", "\n"), "unsupported archived terminal suffix")
    native = probe.render(tokenizer, messages)
    target = action + suffix
    full_messages = messages + [dict(role="assistant", content=target)]
    full = tokenizer.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=False)
    ids = runtime.token_ids(tokenizer.apply_chat_template(full_messages, tokenize=True, add_generation_prompt=False))
    prefix, prefix_ids = native["rendered_prompt"], runtime.token_ids(native["prompt_token_ids"])
    eos, eos_id = tokenizer.eos_token, tokenizer.eos_token_id
    require(isinstance(eos, str) and eos and type(eos_id) is int and eos_id >= 0, "native EOS missing")
    require(full.startswith(prefix + target + eos) and native["actual_system_text"] == runtime.GENERIC_SYSTEM,
            "assistant boundary/system drift")
    tail = full[len(prefix + target + eos):]
    target_ids = runtime.token_ids(tokenizer.encode(target, add_special_tokens=False))
    tail_ids = runtime.token_ids(tokenizer.encode(tail, add_special_tokens=False))
    require(not tail.strip() and target_ids and eos_id not in target_ids and
            runtime.token_ids(tokenizer.encode(eos, add_special_tokens=False)) == [eos_id], "target/EOS/tail drift")
    require(prefix_ids and ids == prefix_ids + target_ids + [eos_id] + tail_ids and
            ids == runtime.token_ids(tokenizer.encode(full, add_special_tokens=False)) and len(ids) <= 1024,
            "native full mask/boundary/truncation")
    positions = list(range(len(prefix_ids), len(prefix_ids) + len(target_ids) + 1))
    labels = [-100] * len(prefix_ids) + target_ids + [eos_id] + [-100] * len(tail_ids)
    return dict(action=action, suffix=suffix, native=native, input_ids=ids, labels=labels,
                target_positions=positions, target_ids=target_ids + [eos_id], eos_id=eos_id)


def build_cases(runtime, core, trainer, probe, plan, world, tokenizer, root):
    public = core.public_view(world)
    require(len(public.actions) == 2 and len(public.slots) == 16, "fixed 16 slots/two legal actions")
    calls = runtime.read(root / "calls.json")
    suffixes, audits = {}, {}
    for stage, count in (("fit1", 8), ("fit2_PROMOTE", 16)):
        result = runtime.read_stage(plan, stage)
        require(result["candidate_sha256"] == CANDIDATES[stage] and result["admitted"] == count, "original candidate identity")
        directory = root / "run" / stage / "data"
        corpus = core.from_data(runtime.read(directory / "corpus.json"), expected_type=core.Corpus)
        training = runtime.read(directory / "training.json")
        require(encoded(training) == encoded(runtime.encode_training(core, public, corpus, tokenizer, trainer, probe)),
                "archived full assistant encoding differs")
        for audit in training["encoding"]:
            target = bytes.fromhex(audit["target_hex"]).decode("ascii")
            action = runtime.legal_action(public, target.encode("ascii"))
            require(action in public.actions, "archived child action unsupported")
            suffix = target[len(action):]
            slot_id = audit["slot_id"]
            require(slot_id not in suffixes or suffixes[slot_id] == suffix, "cross-fit archived suffix differs")
            suffixes[slot_id], audits[slot_id] = suffix, audit
    cases = []
    for view in VIEWS:
        require(len(calls[view]) == 16, "prepared prompt count")
        for index, slot in enumerate(public.slots):
            message = runtime.messages(core.action_prompt(public, slot.slot_id, view=view))
            native = probe.render(tokenizer, message)
            require(calls[view][index] == dict(slot_id=slot.slot_id, messages=message, native=native), "original prepared prompt drift")
            require(calls["wake"][index] == calls["train"][index], "wake/train not identical")
            stages = ("baseline", "report1_PROMOTE", "report2_PROMOTE") if view == "readout" else (
                "wake1" if index < 8 else "wake2_PROMOTE",)
            call_index = index if view == "readout" else (index % 8) * 2
            for stage in stages:
                directory = root / "run" / stage / "data"
                request = runtime.read(directory / f"{call_index:02d}.request.json")
                response = runtime.read(directory / f"{call_index:02d}.response.json")
                require(request == dict(slot_id=slot.slot_id, kind="readout" if view == "readout" else "action", messages=message),
                        "original captured request drift")
                require(response["native"] == native and response["returned_prompt_token_ids"] == native["prompt_token_ids"],
                        "original captured tokenizer boundary drift")
            candidates = [candidate_encoding(runtime, tokenizer, probe, message, action, suffixes[slot.slot_id])
                          for action in public.actions]
            if view == "train":
                audit = audits[slot.slot_id]
                matching = next(candidate for candidate in candidates if
                                (candidate["action"] + candidate["suffix"]).encode().hex() == audit["target_hex"])
                require(matching["input_ids"] == audit["input_ids"] and matching["labels"] == audit["labels"], "archived child mask drift")
            cases.append(dict(view=view, slot_id=slot.slot_id, slot_index=index, candidates=candidates))
    return cases


def evaluate_cases(cases, forward, check_deadline, emit=lambda row: None):
    require(len(cases) == 32 and [(row["view"], row["slot_index"]) for row in cases] ==
            [(view, index) for view in VIEWS for index in range(16)], "fixed candidate coverage")
    rows, calls = [], 0
    for case in cases:
        require(len(case["candidates"]) == 2, "two continuations only")
        scored = []
        for candidate in case["candidates"]:
            check_deadline()
            require(calls < WORKER_FORWARDS, "forward cap")
            calls += 1
            logprobs = forward(candidate)
            require(len(logprobs) == len(candidate["target_ids"]) and
                    all(finite(value) and value <= 0 for value in logprobs) and finite(sum(logprobs)),
                    "nonfinite/invalid per-token logprobs")
            scored.append(dict(candidate, logprobs=logprobs))
        row = dict(case, candidates=scored)
        rows.append(row)
        emit(row)
    check_deadline()
    require(calls == WORKER_FORWARDS, "incomplete forwards")
    return rows


def bind_tensor_records(source, converted, actual):
    require(source and set(source) == set(converted) == set(actual), "LoRA tensor key coverage differs")
    require(all(".lora_A." in name or ".lora_B." in name for name in source), "non-LoRA saved tensor")
    for inventory in (source, converted, actual):
        for record in inventory.values():
            require(set(record) == {"shape", "dtype", "sha256"} and record["shape"] and
                    all(type(size) is int and size > 0 for size in record["shape"]) and
                    record["dtype"] in ("torch.float32", "torch.float16", "torch.bfloat16") and
                    isinstance(record["sha256"], str) and len(record["sha256"]) == 64 and
                    all(char in "0123456789abcdef" for char in record["sha256"]), "invalid tensor identity record")
    require(all(source[name]["shape"] == converted[name]["shape"] for name in source), "LoRA tensor shape drift")
    require(encoded(converted) == encoded(actual), "actual loaded LoRA tensors differ from saved values after dtype conversion")
    return dict(source=source, converted=converted, actual=actual)


def tensor_records(tensors):
    import torch
    records = {}
    for name, tensor in sorted(tensors.items()):
        require(bool(torch.isfinite(tensor).all().item()), "nonfinite LoRA tensor")
        cpu = tensor.detach().cpu().contiguous()
        records[name] = dict(shape=list(cpu.shape), dtype=str(cpu.dtype),
                             sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest())
    return records


def verify_adapter_routes(model, layer_type):
    require(model.active_adapters == ["default"], "model adapter route differs")
    layers = [module for module in model.modules() if isinstance(module, layer_type)]
    require(layers, "no actual tuner layers loaded")
    for layer in layers:
        require(layer.disable_adapters is False and layer.merged is False and
                layer.active_adapters == ["default"], "LoRA inactive, merged or wrong route")
    return len(layers)


def native_model(reflection, plan, adapter):
    import torch
    tokenizer, model = reflection.load_native_model(plan["spec"]["model"])
    receipt, inventory = None, None
    if adapter is not None:
        from peft import PeftModel, get_peft_model_state_dict
        inventory = reflection.check_adapter(str(adapter), plan["config"])
        if "adapter_model.safetensors" in inventory:
            from safetensors.torch import load_file
            saved = load_file(str(adapter / "adapter_model.safetensors"), device="cpu")
        else:
            saved = torch.load(adapter / "adapter_model.bin", map_location="cpu", weights_only=True)
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False, autocast_adapter_dtype=False,
                                         local_files_only=True)
        loaded = get_peft_model_state_dict(model, adapter_name="default")
        require(set(saved) == set(loaded), "loaded LoRA keys differ")
        receipt = bind_tensor_records(tensor_records(saved),
            tensor_records({name: tensor.to(dtype=loaded[name].dtype) for name, tensor in saved.items()}), tensor_records(loaded))
        from peft.tuners.tuners_utils import BaseTunerLayer
        verify_adapter_routes(model, BaseTunerLayer)
    else:
        require(not hasattr(model, "peft_config") and not any("lora_" in name for name, _ in model.named_parameters()), "OFF has LoRA")
    model.requires_grad_(False)
    model.eval()
    require(not any(parameter.requires_grad for parameter in model.parameters()) and
            not any(module.training for module in model.modules()), "model must be frozen/eval")
    return tokenizer, model, receipt, inventory


def hf_forward(model, candidate, torch_api=None):
    if torch_api is None:
        import torch
    else:
        torch = torch_api
    device = next(model.parameters()).device
    ids = torch.tensor([candidate["input_ids"]], dtype=torch.long, device=device)
    positions = candidate["target_positions"]
    with torch.inference_mode():
        logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
        require(logits.ndim == 3 and tuple(logits.shape[:2]) == tuple(ids.shape) and
                max(candidate["target_ids"]) < logits.shape[-1], "forward logits shape/vocabulary")
        selected = logits[0, [position - 1 for position in positions], :].float()
        require(bool(torch.isfinite(selected).all().item()), "nonfinite decision logits")
        targets = torch.tensor(candidate["target_ids"], device=device, dtype=torch.long)
        scores = torch.log_softmax(selected, dim=-1).gather(1, targets[:, None]).squeeze(1)
        return scores.cpu().tolist()


def worker(source, collection, state, output, deadline_unix, allow_native=False):
    require(allow_native, "Main-only worker requires --allow-native")
    started = time.time()
    require(state in CANDIDATES and finite(deadline_unix) and started < deadline_unix <= started + WORKER_SECONDS,
            "worker state/400-second deadline")
    def check_deadline():
        require(time.time() < deadline_unix, "worker deadline exhausted; Main owns process timeout")
    source = frozen_source(source)
    collection_metadata(collection)
    runtime = load_module("_access_archived_runtime", source / "gpu/astra_l2_public_record_dev.py")
    runtime.offline()
    runtime.launcher_output_outside(ROOT)
    require(digest(ROOT / "SEAL.json") == SEAL_PIN, "original seal pin differs")
    terminal, files = runtime.custody(ROOT, PLAN_PIN)
    require(terminal["status"] == "COMPLETE", "original root not complete")
    plan, core, trainer, probe, reflection, world = runtime.verify(ROOT, PLAN_PIN)
    require(plan["spec"]["source_files"] == SOURCE_FILES and plan["base_sha256"] == BASE_PIN and
            {name: entry["sha256"] for name, entry in plan["spec"]["helpers"].items()} == HELPERS, "original bindings differ")
    output = external_output(output, (ROOT, source, plan["spec"]["source"], plan["spec"]["model"], collection,
                                     Path(plan["spec"]["helpers"]["public"]["path"]).parent,
                                     Path(__file__), *[record["path"] for record in plan["spec"]["helpers"].values()]))
    for protected in (source, plan["spec"]["source"], plan["spec"]["model"]):
        runtime.launcher_output_outside(protected)
    require(probe.model_hashes(plan["spec"]["model"]) == plan["model_files"], "original base file drift")
    tokenizer = probe.native_tokenizer(plan["spec"]["model"])
    require(tokenizer.chat_template == plan["chat_template"], "tokenizer template drift")
    cases = build_cases(runtime, core, trainer, probe, plan, world, tokenizer, ROOT)
    adapter = None if state == "OFF" else ROOT / "run" / state / "data/adapter"
    expected_files = None if adapter is None else runtime.read_stage(plan, state)["candidate_files"]
    require(adapter is None or runtime.tree(adapter) == expected_files and value_hash(expected_files) == CANDIDATES[state],
            "saved adapter file identity differs")
    check_deadline()
    loaded_tokenizer, model, tensor_identity, adapter_files = native_model(reflection, plan, adapter)
    require(loaded_tokenizer.chat_template == tokenizer.chat_template and adapter_files == expected_files, "loaded identity differs")
    rows = evaluate_cases(cases, lambda candidate: hf_forward(model, candidate), check_deadline,
                          emit=lambda row: print(encoded(dict(progress=row)).decode(), end="", flush=True))
    if adapter is not None:
        from peft import get_peft_model_state_dict
        require(tensor_records(get_peft_model_state_dict(model, adapter_name="default")) == tensor_identity["actual"],
                "LoRA tensors changed during evaluation")
        require(runtime.tree(adapter) == adapter_files, "adapter files changed during evaluation")
    require(runtime.custody(ROOT, PLAN_PIN)[1] == files and digest(ROOT / "SEAL.json") == SEAL_PIN, "old root changed")
    check_deadline()
    receipt = dict(schema=SCHEMA, diagnostic_only=True, claim=CLAIM, state=state, pid=os.getpid(),
                   started=started, ended=time.time(), deadline_unix=deadline_unix, source_files=SOURCE_FILES,
                   diagnostic_sha256=digest(__file__), plan_sha256=PLAN_PIN, seal_sha256=SEAL_PIN,
                   collection_sha256=COLLECTION_PIN, base_sha256=BASE_PIN, candidate_sha256=CANDIDATES[state],
                   adapter_files=adapter_files, tensor_identity=tensor_identity, forwards=WORKER_FORWARDS,
                   updates=0, rows=rows, cases_sha256=value_hash(cases), cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"))
    runtime.write(output, receipt)
    return dict(output=str(output), sha256=digest(output), state=state, forwards=WORKER_FORWARDS, updates=0)


def pair_metrics(row, truth_index):
    candidates = row["candidates"]
    left, right = candidates
    sequences = [candidate["target_ids"] for candidate in candidates]
    prefix = 0
    while prefix < min(map(len, sequences)) and sequences[0][prefix] == sequences[1][prefix]:
        prefix += 1
    require(prefix < min(map(len, sequences)), "no comparable first divergent token")
    suffix = 0
    while suffix < min(map(len, sequences)) - prefix and sequences[0][-suffix - 1] == sequences[1][-suffix - 1]:
        suffix += 1
    full_margin = sum(left["logprobs"]) - sum(right["logprobs"])
    mean_margin = sum(left["logprobs"]) / len(left["logprobs"]) - sum(right["logprobs"]) / len(right["logprobs"])
    first_margin = left["logprobs"][prefix] - right["logprobs"][prefix]
    def choice(margin):
        return None if margin == 0 else (0 if margin > 0 else 1)
    gold = candidates[truth_index]["logprobs"]
    decision = list(range(prefix, len(gold) - suffix))
    common = list(range(prefix)) + list(range(len(gold) - suffix, len(gold)))
    def loss(indices):
        return dict(tokens=len(indices), nll=-sum(gold[index] for index in indices))
    return dict(slot_id=row["slot_id"], slot_index=row["slot_index"], truth_index=truth_index,
                candidates=[dict(action=candidate["action"], tokens_including_eos=len(candidate["target_ids"]),
                                 logprob_sum=sum(candidate["logprobs"]),
                                 mean_nll=-sum(candidate["logprobs"]) / len(candidate["logprobs"]),
                                 decision_span=[prefix, len(candidate["target_ids"]) - suffix]) for candidate in candidates],
                common_prefix_tokens=prefix, common_suffix_tokens=suffix,
                full_margin_action0_minus_action1=full_margin, first_margin_action0_minus_action1=first_margin,
                mean_logprob_margin_action0_minus_action1=mean_margin,
                gold_full_margin=full_margin * (1 if truth_index == 0 else -1),
                gold_first_margin=first_margin * (1 if truth_index == 0 else -1), first_divergent_index=prefix,
                full_choice=choice(full_margin), first_choice=choice(first_margin),
                full_correct=choice(full_margin) == truth_index, first_correct=choice(first_margin) == truth_index,
                losses=dict(full=loss(range(len(gold))), common=loss(common), decision=loss(decision),
                            common_prefix=loss(range(prefix)), shared_suffix=loss(range(len(gold) - suffix, len(gold))),
                            first_decision=loss([prefix]), eos=loss([len(gold) - 1])))


def validate_receipt(receipt, core, world):
    state = receipt["state"]
    require(state in CANDIDATES and receipt["schema"] == SCHEMA and receipt["diagnostic_only"] is True and receipt["claim"] == CLAIM,
            "diagnostic scope/state")
    require(receipt["source_files"] == SOURCE_FILES and receipt["diagnostic_sha256"] == digest(__file__) and
            receipt["plan_sha256"] == PLAN_PIN and receipt["seal_sha256"] == SEAL_PIN and
            receipt["collection_sha256"] == COLLECTION_PIN and receipt["base_sha256"] == BASE_PIN and
            receipt["candidate_sha256"] == CANDIDATES[state], "receipt pin drift")
    require(type(receipt["pid"]) is int and receipt["pid"] > 0 and type(receipt["forwards"]) is int and
            receipt["forwards"] == WORKER_FORWARDS and type(receipt["updates"]) is int and receipt["updates"] == 0, "work/PID identity")
    require(all(finite(receipt[key]) for key in ("started", "ended", "deadline_unix")) and
            receipt["started"] <= receipt["ended"] <= receipt["deadline_unix"] <= receipt["started"] + WORKER_SECONDS,
            "worker time bound")
    if state == "OFF":
        require(receipt["adapter_files"] is None and receipt["tensor_identity"] is None, "OFF adapter identity")
    else:
        require(value_hash(receipt["adapter_files"]) == CANDIDATES[state], "candidate files pin")
        identity = receipt["tensor_identity"]
        bind_tensor_records(identity["source"], identity["converted"], identity["actual"])
    public = core.public_view(world)
    require(len(receipt["rows"]) == 32, "incomplete diagnostic coverage")
    cases = []
    for row, (view, index) in zip(receipt["rows"], [(view, index) for view in VIEWS for index in range(16)], strict=True):
        require(row["view"] == view and type(row["slot_index"]) is int and row["slot_index"] == index and
                row["slot_id"] == public.slots[index].slot_id and len(row["candidates"]) == 2, "row order/identity")
        clean_candidates = []
        for candidate, action in zip(row["candidates"], public.actions, strict=True):
            ids, positions, targets = candidate["input_ids"], candidate["target_positions"], candidate["target_ids"]
            require(candidate["action"] == action and candidate["suffix"] in ("", "\n") and 1 <= len(ids) <= 1024 and
                    all(type(value) is int and value >= 0 for value in ids + targets + positions) and positions and
                    positions == list(range(positions[0], positions[0] + len(targets))) and 0 < positions[0] and positions[-1] < len(ids),
                    "candidate token boundary/identity")
            require(candidate["eos_id"] == targets[-1] and type(candidate["eos_id"]) is int and
                    candidate["eos_id"] not in targets[:-1] and [ids[position] for position in positions] == targets and
                    all(type(value) is int for value in candidate["labels"] + candidate["native"]["prompt_token_ids"]) and
                    candidate["labels"] == [-100] * positions[0] + targets + [-100] * (len(ids) - positions[-1] - 1) and
                    candidate["native"]["prompt_token_ids"] == ids[:positions[0]], "full target/EOS mask")
            require(len(candidate["logprobs"]) == len(targets) and all(finite(value) and value <= 0 for value in candidate["logprobs"]) and
                    finite(sum(candidate["logprobs"])),
                    "invalid logprobs")
            clean_candidates.append({key: value for key, value in candidate.items() if key != "logprobs"})
        require(row["candidates"][0]["native"] == row["candidates"][1]["native"] and
                row["candidates"][0]["suffix"] == row["candidates"][1]["suffix"], "paired continuation context differs")
        cases.append(dict(row, candidates=clean_candidates))
    require(value_hash(cases) == receipt["cases_sha256"], "candidate encoding receipt differs")


def reduce_receipts(receipts, core, world):
    require(len(receipts) == 3 and {receipt["state"] for receipt in receipts} == set(CANDIDATES), "exact OFF/fit1/fit2 workers required")
    require(len({receipt["pid"] for receipt in receipts}) == 3, "fresh distinct model processes required")
    require(len({receipt["cases_sha256"] for receipt in receipts}) == 1, "cross-worker prompt/continuation drift")
    require(max(receipt["ended"] for receipt in receipts) - min(receipt["started"] for receipt in receipts) <= TOTAL_SECONDS,
            "three-worker 1200-second envelope exceeded")
    for receipt in receipts:
        validate_receipt(receipt, core, world)
    return summarize_scores(receipts, core, world)


def summarize_scores(receipts, core, world):
    public = core.public_view(world)
    states = {}
    for receipt in receipts:
        panels = {}
        for view in VIEWS:
            rows = [pair_metrics(row, public.actions.index(world.success_actions[row["slot_index"]]))
                    for row in receipt["rows"] if row["view"] == view]
            losses = {}
            for category in rows[0]["losses"]:
                count = sum(row["losses"][category]["tokens"] for row in rows)
                nll = sum(row["losses"][category]["nll"] for row in rows)
                losses[category] = dict(tokens=count, nll=nll, mean=nll / count if count else None)
            panels[view] = dict(rows=rows, gold_losses=losses,
                **{metric: dict(old_correct=sum(row[metric + "_correct"] for row in rows[:8]),
                                new_correct=sum(row[metric + "_correct"] for row in rows[8:]),
                                ties=sum(row[metric + "_choice"] is None for row in rows)) for metric in ("full", "first")})
        panels["access_contrast"] = [dict(slot_id=train["slot_id"],
            train_minus_readout_gold_first_margin=train["gold_first_margin"] - readout["gold_first_margin"],
            train_minus_readout_gold_full_margin=train["gold_full_margin"] - readout["gold_full_margin"],
            train_correct_readout_not=train["first_correct"] and not readout["first_correct"],
            readout_correct_train_not=readout["first_correct"] and not train["first_correct"])
            for train, readout in zip(panels["train"]["rows"], panels["readout"]["rows"], strict=True)]
        states[receipt["state"]] = panels
    contrasts = {state: {view: [dict(slot_id=after["slot_id"],
        delta_gold_first_margin=after["gold_first_margin"] - before["gold_first_margin"],
        delta_gold_full_margin=after["gold_full_margin"] - before["gold_full_margin"])
        for after, before in zip(states[state][view]["rows"], states["OFF"][view]["rows"], strict=True)]
        for view in VIEWS} for state in ("fit1", "fit2_PROMOTE")}
    return dict(schema=SCHEMA, diagnostic_only=True, claim=CLAIM, forwards=TOTAL_FORWARDS, updates=0,
                states=states, versus_OFF=contrasts, scientific_pass=None,
                interpretation="No automatic ambiguity threshold or single-decision-token assumption. Continuation lengths can differ: full likelihood sums and descriptive mean log probabilities are distinct statistics. Compare first-token and full margins/loss on both views: weak or mixed train and readout evidence does not isolate paraphrase access; stronger train but weaker readout is a possible access gap, not proof. Common suffix/EOS losses condition on different action histories. ln(2)/13 is an unmeasured reference hypothesis only. Teacher forcing does not replace the original vLLM readouts.")


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("worker", "reduce"):
        command = subparsers.add_parser(name)
        command.add_argument("--source", required=True)
        command.add_argument("--collection", default="/tmp/astra_l2_collection_20260913_attempt1.json")
        command.add_argument("--output", required=True)
        if name == "worker":
            command.add_argument("--state", choices=list(CANDIDATES), required=True)
            command.add_argument("--deadline-unix", type=float, required=True)
            command.add_argument("--allow-native", action="store_true")
        else:
            command.add_argument("--worker", nargs=2, action="append", metavar=("PATH", "SHA256"), required=True)
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "worker":
        result = worker(**args)
    else:
        source = frozen_source(args["source"])
        collection = collection_metadata(args["collection"])
        core = load_module("_access_frozen_core", source / "organism_v6/l2_public_record_dev.py")
        require(all(digest(path) == checksum for path, checksum in args["worker"]), "worker file pin differs")
        result = reduce_receipts([read(path) for path, _ in args["worker"]], core, core.build_world(2026091301, 2026091302))
        result.update(original_vllm_reports=collection["reports"], original_plan_sha256=PLAN_PIN,
                      worker_files=[dict(path=path, sha256=checksum) for path, checksum in args["worker"]])
        output = external_output(args["output"], (ROOT, source, args["collection"], Path(__file__),
                                                   *[path for path, _ in args["worker"]]))
        with output.open("xb") as stream:
            stream.write(encoded(result))
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
