"""Seed0 instrumented first-backward scratch probe; no optimizer updates or saves.

prepare/compare are stdlib-only. Main alone invokes a fresh worker per path.
Frozen trainer source is traced, never rewritten or globally monkeypatched.
"""
from __future__ import annotations

import argparse
import ast
import functools
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import signal
import sys
import time


SCHEMA = "astra_additive_native_first_backward_20260913_v1"
SELF = Path(__file__).resolve()
PINS = {
    "old_plan": "54c27ab8043f23729d813b256b73749fc1694d552fa5cb75283dc5a0d83c3e64",
    "new_plan": "77a7e3f39005e10c0f3085dc68aabdebc31f33f9684925125c2a261039555c45",
    "old_training": "7c0c9c7fd452e5e311c63143944b8d8d6a60508fd109c8623f45babec9f2735a",
    "paired": "769fafd87b24c276fec80f776e06cf81e66dae596760f9f026879d8fd8c8e3c9",
    "old_manifest": "56977860d3241b190c3dcaacabc40db1d23bd56846b9dcfb7c7e2d33fc2ec448",
    "new_manifest": "a6ed70bc1c89e6a34b541694ee3df6ab9b167f693dee00e2f24d25a47ffcd8a7",
    "trainer": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7",
    "additive": "3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0",
    "reflection": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc",
}
PHASES = ("before_init", "after_init", "before_forward", "after_forward", "before_backward", "after_backward")
SECONDS = 300


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def finite(text):
        value = float(text)
        require(math.isfinite(value), "nonfinite JSON")
        return value
    return json.loads(Path(path).read_text(), object_pairs_hook=unique, parse_float=finite,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def pinned(record, expected=None):
    require(set(record) == {"path", "sha256"}, "closed file binding required")
    require(expected is None or record["sha256"] == expected, "unexpected historical/source pin")
    require(digest(record["path"]) == record["sha256"], "file bytes differ: "+str(record["path"]))
    return Path(record["path"])


def anchors(trainer_path, additive_path):
    result = {}
    specifications = {
        "OLD": (trainer_path, "_run_training", "out = model(**t)", "(loss / cfg.grad_accum).backward()"),
        "NEW": (additive_path, "backward_components", "loss = model(**tensors).loss", "loss.backward()"),
    }
    for name, (path, function, forward, backward) in specifications.items():
        tree = ast.parse(Path(path).read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function]
        require(len(functions) == 1, "unambiguous frozen loop required")
        found = {}
        for label, expression in (("forward", forward), ("backward", backward)):
            nodes = [node for node in ast.walk(functions[0]) if isinstance(node, (ast.Assign, ast.Expr)) and ast.unparse(node) == expression]
            require(len(nodes) == 1 and nodes[0].lineno == nodes[0].end_lineno, "exact single-line trace seam unavailable: "+label)
            found[label] = nodes[0].lineno
        require(found["forward"] < found["backward"], "trace order differs")
        result[name] = dict(file=str(Path(path).resolve()), function=function, **found)
    require(any(isinstance(node, ast.FunctionDef) and node.name == "_warm_initialize" for node in ast.parse(Path(trainer_path).read_text()).body), "warm initializer missing")
    result["init_file"] = str(Path(trainer_path).resolve())
    return result


def bind_inputs(inputs):
    require(set(inputs) == set(PINS), "complete closed input/source inventory required")
    files = {key: pinned(value, PINS[key]) for key, value in inputs.items()}
    old, new = read(files["old_plan"]), read(files["new_plan"])
    primary, paired = read(files["old_training"]), read(files["paired"])
    old_fit, new_fit = read(files["old_manifest"]), read(files["new_manifest"])
    require(primary["seed"] == paired["seed"] == paired["fit_seed"] == primary["fit_seed"] == 0, "seed0 only")
    require(paired["primary"] == primary, "exact historical primary data required")
    for key in ("environment", "python", "python_sha256", "model", "model_files", "chat_template", "engine", "params", "parent"):
        require(old[key] == new[key], "historical/new binding differs: "+key)
    config = old["configs"]["EXTRA_MEMORY"]
    require(config == new["configs"]["MEMORY_ONLY"] == old_fit["config"] == new_fit["config"], "configuration differs")
    require(config["seed"] == 0 and config["grad_accum"] == config["batch_size"] == 1 and config["device"] == "cuda"
            and config["dtype"] == "bf16" and config["grad_checkpoint"] is True and config["max_steps"] == 0, "native recipe differs")
    for key in ("initialized_state", "source_state", "trainable_names", "optimizer_defaults", "parent_files"):
        require(old_fit["warm_start"][key] == new_fit["warm_start"][key], "historical initialization/defaults differ")
    first_id = primary["epoch_order"][0][0]
    first = [audit for audit in primary["encoding"] if audit["row_id"] == first_id]
    require(len(first) == 1, "unique first memory occurrence required")
    return dict(old=old, new=new, primary=primary, paired=paired, config=config, old_fit=old_fit,
                first=first[0], anchors=anchors(files["trainer"], files["additive"]))


def prepare(old_root, new_root, trainer, additive, reflection, out, gpu_uuid, expected_boot_id):
    old_root, new_root, out = (Path(value).absolute() for value in (old_root, new_root, out))
    require(type(gpu_uuid) is str and gpu_uuid.startswith("GPU-") and len(gpu_uuid) > 4, "Main planned GPU UUID required")
    require(type(expected_boot_id) is str and len(expected_boot_id) == 36, "Main current boot binding required")
    paths = dict(old_plan=old_root/"plan.json", new_plan=new_root/"plan.json", old_training=old_root/"training_EXTRA_MEMORY.json",
        paired=new_root/"paired.json", old_manifest=old_root/"run/EXTRA_MEMORY_fit/adapter/train_manifest.json",
        new_manifest=new_root/"run/MEMORY_ONLY_fit/adapter/train_manifest.json", trainer=Path(trainer), additive=Path(additive), reflection=Path(reflection))
    inputs = {key: dict(path=str(path.absolute()), sha256=PINS[key]) for key, path in paths.items()}
    bound = bind_inputs(inputs)
    for protected in (old_root, new_root, Path(bound["old"]["model"]), Path(bound["old"]["parent"]["adapter"]), *paths.values()):
        protected = protected.resolve()
        require(out.resolve() != protected and protected not in out.resolve().parents and out.resolve() not in protected.parents, "scratch overlaps protected input")
    require(not out.exists(), "fresh scratch plan root required")
    plan = dict(schema=SCHEMA, root=str(out), inputs=inputs, probe_sha256=digest(SELF), anchors=bound["anchors"],
        first_row_id=bound["first"]["row_id"], gpu_uuid=gpu_uuid, expected_boot_id=expected_boot_id,
        seconds=SECONDS, optimizer_steps=0, adapter_saves=0, readouts=0, scientific_acceptance=False,
        qualification="Instrumented exact frozen loops, not an uninstrumented replay or numerical-equivalence certification.")
    out.mkdir()
    write(out/"plan.json", plan)
    return dict(plan=str(out/"plan.json"), plan_sha256=digest(out/"plan.json"), native_authorized=False)


class FirstBackwardCaptured(BaseException):
    pass


class ForbiddenMutation(BaseException):
    pass


class FirstBackwardTrace:
    def __init__(self, locations, path, observer):
        require(path in ("OLD", "NEW"), "OLD or NEW path required")
        self.location = locations[path]
        self.init_file = locations["init_file"]
        self.observer = observer
        self.phases = []
        self.pending = None
        self.active_frame = None
        self.forbidden_calls = []

    def observe(self, phase, frame, value=None):
        require(len(self.phases) < len(PHASES) and phase == PHASES[len(self.phases)], "first-backward trace phase differs")
        self.observer(phase, frame, value)
        self.phases.append(phase)

    def trace(self, frame, event, value):
        code = frame.f_code
        module = str(frame.f_globals.get("__name__", ""))
        if event == "call" and (code.co_name == "save_pretrained" or code.co_name == "step" and module.startswith("torch.optim")):
            self.forbidden_calls.append(module+"."+code.co_name)
            raise ForbiddenMutation("optimizer step or adapter saving reached")
        filename = os.path.realpath(code.co_filename)
        if filename == self.init_file and code.co_name == "_warm_initialize":
            if event == "call":
                self.observe("before_init", frame)
            elif event == "return":
                self.observe("after_init", frame, value)
            return self.trace
        if filename != self.location["file"] or code.co_name != self.location["function"]:
            return None
        if event == "exception" and self.pending is not None:
            raise ValueError("frozen operation failed before "+self.pending) from value[1]
        if event == "line":
            if self.pending is not None:
                require(frame is self.active_frame, "unexpected reentrant loop frame")
                phase, self.pending = self.pending, None
                self.observe(phase, frame)
                if phase == "after_backward":
                    raise FirstBackwardCaptured()
            if frame.f_lineno == self.location["forward"]:
                self.active_frame = frame
                self.observe("before_forward", frame)
                self.pending = "after_forward"
            elif frame.f_lineno == self.location["backward"]:
                self.observe("before_backward", frame)
                self.pending = "after_backward"
        return self.trace


def intercept(action, locations, path, observer):
    require(sys.gettrace() is None, "existing tracer cannot be replaced")
    tracer = FirstBackwardTrace(locations, path, observer)
    sys.settrace(tracer.trace)
    try:
        try:
            action()
        except FirstBackwardCaptured:
            require(tracer.phases == list(PHASES) and not tracer.forbidden_calls, "incomplete or mutated trace")
            return tracer
        raise ValueError("frozen path returned without zero-step interception")
    finally:
        sys.settrace(None)


def tensor_record(tensor, torch):
    raw = tensor.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes()
    return dict(sha256=hashlib.sha256(raw).hexdigest(), shape=list(tensor.shape), dtype=str(tensor.dtype), device=str(tensor.device))


def rng_record(torch):
    return dict(python=hashlib.sha256(encoded(random.getstate())).hexdigest(),
                cpu=tensor_record(torch.get_rng_state(), torch),
                cuda=[tensor_record(state, torch) for state in torch.cuda.get_rng_state_all()])


def simple(value):
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, (list, tuple)):
        return [simple(item) for item in value]
    if isinstance(value, dict):
        return {str(key): simple(item) for key, item in value.items()}
    return dict(type=type(value).__module__+"."+type(value).__qualname__)


def model_settings(model, torch):
    def query(owner, name, invoke=False):
        value = getattr(owner, name, None)
        return simple(value() if invoke and callable(value) else value)
    checkpoints, dropout = {}, {}
    for name, module in model.named_modules():
        if hasattr(module, "gradient_checkpointing"):
            function = getattr(module, "_gradient_checkpointing_func", None)
            checkpoints[name] = dict(enabled=bool(module.gradient_checkpointing),
                keywords=simple(function.keywords) if isinstance(function, functools.partial) else None,
                function=getattr(function.func if isinstance(function, functools.partial) else function, "__qualname__", None))
        if isinstance(module, torch.nn.Dropout):
            dropout[name] = dict(p=module.p, training=module.training)
    return dict(training=model.training, use_cache=query(model.config, "use_cache"),
        attention_implementation=query(model.config, "_attn_implementation"),
        attention_dropout=query(model.config, "attention_dropout"), checkpoints=checkpoints, dropout=dropout,
        parameter_dtypes=sorted({str(parameter.dtype) for parameter in model.parameters()}),
        deterministic_algorithms=query(torch, "are_deterministic_algorithms_enabled", True),
        float32_matmul_precision=query(torch, "get_float32_matmul_precision", True),
        cuda_matmul={name: query(torch.backends.cuda.matmul, name) for name in
                     ("allow_tf32", "allow_fp16_reduced_precision_reduction", "allow_bf16_reduced_precision_reduction")},
        cudnn={name: query(torch.backends.cudnn, name) for name in ("allow_tf32", "benchmark", "deterministic")},
        sdp={name: query(torch.backends.cuda, name, True) for name in ("flash_sdp_enabled", "mem_efficient_sdp_enabled", "math_sdp_enabled")},
        backend_note="Enabled flags and effective model configuration, not a profiler's proof of the kernel actually selected.")


class NativeObserver:
    def __init__(self, torch, out, bound):
        self.torch, self.out, self.bound = torch, out, bound
        self.model = None
        self.records = {}
        self.initial = None

    def __call__(self, phase, frame, value):
        torch = self.torch
        before = rng_record(torch)
        record = dict(phase=phase, rng=before)
        if phase == "after_init":
            require(type(value) is tuple and len(value) == 2, "warm initializer did not return model/receipt")
            self.model, receipt = value
            expected = self.bound["old_fit"]["warm_start"]
            for key in ("initialized_state", "source_state", "trainable_names"):
                require(receipt[key] == expected[key], "actual initial state differs: "+key)
            record["warm_initial_inventory"] = receipt["initialized_state"]
            record["initial_tensors"] = {name: tensor_record(parameter, torch) for name, parameter in self.model.named_parameters() if parameter.requires_grad}
            self.initial = record["initial_tensors"]
            require(self.initial and all("lora_" in name for name in self.initial), "only nonempty LoRA trainability required")
        if phase == "before_forward":
            model = frame.f_locals["model"]
            require(model is self.model, "forward uses a different model")
            tensors = frame.f_locals.get("t", frame.f_locals.get("tensors"))
            first = self.bound["first"]
            require(set(tensors) == {"input_ids", "labels", "attention_mask"}, "native first input keys differ")
            require(tensors["input_ids"].tolist() == [first["input_ids"]] and tensors["labels"].tolist() == [first["labels"]], "actual first tokens/masks differ")
            require(tensors["attention_mask"].tolist() == [[1]*len(first["input_ids"])] , "actual 2d attention differs")
            record["inputs"] = {key: tensor_record(tensor, torch) for key, tensor in tensors.items()}
            record["position_ids"] = "absent in both exact 2d paths; model default"
            record["settings"] = model_settings(model, torch)
            owner = frame if "opt" in frame.f_locals else frame.f_back
            optimizer = owner.f_locals.get("opt", owner.f_locals.get("optimizer"))
            require(optimizer is not None and not optimizer.state, "fresh optimizer required")
            record["optimizer"] = dict(class_name=type(optimizer).__module__+"."+type(optimizer).__name__, defaults=simple(optimizer.defaults), state_entries=len(optimizer.state))
            require(record["optimizer"]["defaults"] == self.bound["old_fit"]["warm_start"]["optimizer_defaults"], "actual optimizer defaults differ")
            require(all(parameter.grad is None for parameter in model.parameters()), "gradient exists before first forward")
        if phase in ("after_forward", "before_backward", "after_backward"):
            loss = frame.f_locals.get("loss")
            if phase == "after_forward" and "out" in frame.f_locals:
                loss = frame.f_locals["out"].loss
            require(loss is not None, "first loss unavailable")
            record["loss"] = loss.detach().item()
            require(math.isfinite(record["loss"]), "nonfinite first loss")
            record["loss_tensor"] = tensor_record(loss, torch)
        if phase == "after_backward":
            gradients, unchanged = {}, {}
            for name, parameter in self.model.named_parameters():
                if parameter.requires_grad:
                    require(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()), "missing/nonfinite first gradient")
                    gradients[name] = tensor_record(parameter.grad, torch)
                    unchanged[name] = tensor_record(parameter, torch)
                else:
                    require(parameter.grad is None, "base gradient unexpectedly present")
            require(unchanged == self.initial, "parameters changed before optimizer interception")
            record.update(gradients=gradients, trainable_parameters_unchanged=True, base_gradients_absent=True)
        after = rng_record(torch)
        require(before == after, "observer consumed RNG; parity interpretation invalid")
        record["observer_rng_unchanged"] = True
        self.records[phase] = record
        write(self.out/(phase+".json"), record)


def load_module(record, name):
    path = pinned(record)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inventory(root):
    root = Path(root)
    return {str(path.relative_to(root)): digest(path) for path in sorted(root.rglob("*")) if path.is_file()}


def worker(plan_path, plan_sha256, path, allow_native=False):
    require(allow_native is True, "Main explicit --allow-native required; no default native execution")
    require(sys.dont_write_bytecode, "invoke worker with -B; frozen source must not acquire bytecode")
    plan = read(pinned(dict(path=plan_path, sha256=plan_sha256)))
    require(plan["schema"] == SCHEMA and plan["probe_sha256"] == digest(SELF) and plan["seconds"] == SECONDS, "probe plan/source differs")
    require(path in ("OLD", "NEW"), "path must be OLD or NEW")
    bound = bind_inputs(plan["inputs"])
    require(plan["anchors"] == bound["anchors"] and plan["first_row_id"] == bound["first"]["row_id"], "trace/input plan differs")
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == plan["expected_boot_id"], "current boot differs")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"], "Main single GPU visibility binding required")
    require(os.path.abspath(sys.executable) == bound["old"]["python"] and digest(sys.executable) == bound["old"]["python_sha256"], "native interpreter differs")
    require(all(os.environ.get(key) == "1" for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")), "offline environment required")
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "existing real-time timer cannot be replaced")
    out = Path(plan["root"])/path
    out.mkdir()
    started = time.monotonic()
    write(out/"started.json", dict(pid=os.getpid(), path=path, plan_sha256=plan_sha256, seconds=SECONDS, time=time.time()))
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("first-backward scratch deadline exceeded")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        for name, checksum in bound["old"]["model_files"].items():
            pinned(dict(path=str(Path(bound["old"]["model"])/name), sha256=checksum))
        parent = bound["old"]["parent"]
        require(inventory(parent["adapter"]) == parent["adapter_files"], "parent file inventory differs")
        trainer = load_module(plan["inputs"]["trainer"], "parity_frozen_trainer")
        additive = load_module(plan["inputs"]["additive"], "parity_frozen_additive")
        reflection = load_module(plan["inputs"]["reflection"], "parity_frozen_reflection")
        import torch
        require(torch.cuda.device_count() == 1, "one visible CUDA device required")
        require(trainer._versions() == bound["old_fit"]["versions"], "native package versions differ")
        packages = bound["old"]["environment"]["probe"]["packages"]
        actual_packages = {name: importlib.metadata.version(name) for name in packages}
        require(actual_packages == packages, "native distribution versions differ")
        write(out/"environment.json", dict(packages=actual_packages, python=sys.version,
            cuda_version=torch.version.cuda, cudnn_version=torch.backends.cudnn.version(),
            device_name=torch.cuda.get_device_name(0), device_capability=list(torch.cuda.get_device_capability(0)),
            environment={key: os.environ.get(key) for key in ("CUDA_VISIBLE_DEVICES", "PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG",
                "CUDA_LAUNCH_BLOCKING", "PYTORCH_CUDA_ALLOC_CONF", "PYTORCH_ALLOC_CONF", "NVIDIA_TF32_OVERRIDE",
                "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}))
        tokenizer, base = reflection.load_native_model(bound["old"]["model"])
        require(tokenizer.chat_template == bound["old"]["chat_template"], "native tokenizer template differs")
        cfg = trainer.TrainConfig(**bound["config"])
        observer = NativeObserver(torch, out, bound)
        with (out/"path.log").open("x") as stream:
            def log(text):
                stream.write(str(text)+"\n")
                stream.flush()
            def action():
                if path == "OLD":
                    trainer.run_training(bound["primary"]["items"], tokenizer, base, cfg, str(out/"scratch"),
                        init_adapter=parent["adapter"], corpus_sha=PINS["old_training"],
                        corpus_name=bound["old_fit"]["corpus"]["file"], log=log)
                else:
                    additive.run_training(bound["paired"], tokenizer, base, cfg, str(out/"scratch"), arm="MEMORY_ONLY",
                        init_adapter=parent["adapter"], expected_parent_files=parent["adapter_files"], trainer=trainer,
                        corpus_sha=bound["new"]["input_hashes"]["training_MEMORY_ONLY.json"], log=log)
            tracer = intercept(action, bound["anchors"], path, observer)
        require(inventory(parent["adapter"]) == parent["adapter_files"], "parent changed")
        scratch = inventory(out/"scratch")
        require(set(scratch) <= {"failure.json", "steps.jsonl"}, "unexpected scratch adapter/training output")
        if "steps.jsonl" in scratch:
            require((out/"scratch/steps.jsonl").stat().st_size == 0, "optimizer journal is not empty")
        receipt = dict(schema=SCHEMA, status="FIRST_BACKWARD_CAPTURED_ZERO_UPDATES", path=path, pid=os.getpid(),
            plan_sha256=plan_sha256, probe_sha256=digest(SELF), first_row_id=plan["first_row_id"], phases=tracer.phases,
            observations={phase: dict(path=str(out/(phase+".json")), sha256=digest(out/(phase+".json"))) for phase in PHASES},
            environment=dict(path=str(out/"environment.json"), sha256=digest(out/"environment.json")),
            optimizer_steps=0, adapter_saves=0, readouts=0, parent_unchanged=True, scratch_files=scratch,
            elapsed_seconds=time.monotonic()-started, versions=trainer._versions(), native_process_isolation="Main invokes each worker in a distinct process",
            limitations=["Observer synchronization/tracing perturbs timing and allocation; not uninstrumented numerical parity.",
                         "No RNG forced equal; CUDA RNG captured only for the one visible device.",
                         "Warm initialization boundary is after natural trainer seeding, not before base loading.",
                         "Kernel enablement flags do not establish actual selected kernel.",
                         "NEW frozen cleanup may write failure.json for the intentional BaseException; retained, not a completed fit."])
        write(out/"receipt.json", receipt)
        return dict(receipt=str(out/"receipt.json"), sha256=digest(out/"receipt.json"))
    except BaseException as error:
        write(out/"probe_failure.json", dict(status="FAILED", error_type=type(error).__name__, error=str(error), path=path))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def compare(old_receipt, old_sha256, new_receipt, new_sha256, out):
    receipts = [read(pinned(dict(path=path, sha256=pin))) for path, pin in ((old_receipt, old_sha256), (new_receipt, new_sha256))]
    old, new = receipts
    require([item["path"] for item in receipts] == ["OLD", "NEW"], "OLD/NEW paired receipts required")
    require(old["plan_sha256"] == new["plan_sha256"] and old["probe_sha256"] == new["probe_sha256"] == digest(SELF)
            and old["first_row_id"] == new["first_row_id"] and old["pid"] != new["pid"], "same plan/source/row and distinct processes required")
    for item in receipts:
        require(item["schema"] == SCHEMA and item["status"] == "FIRST_BACKWARD_CAPTURED_ZERO_UPDATES"
                and item["phases"] == list(PHASES) and item["parent_unchanged"] is True
                and type(item["pid"]) is int and item["pid"] > 0
                and set(item["observations"]) == set(PHASES)
                and all(type(item[key]) is int and item[key] == 0 for key in ("optimizer_steps", "adapter_saves", "readouts")), "incomplete or mutated path")
    observations = [{phase: read(pinned(item["observations"][phase])) for phase in PHASES} for item in receipts]
    environments = [read(pinned(item["environment"])) for item in receipts]
    for snapshot in observations:
        require(all(snapshot[phase]["phase"] == phase and snapshot[phase]["observer_rng_unchanged"] is True for phase in PHASES), "observation phase/RNG differs")
        require(snapshot["after_init"]["initial_tensors"] and snapshot["after_backward"]["gradients"]
                and snapshot["after_backward"]["trainable_parameters_unchanged"] is True
                and snapshot["after_backward"]["base_gradients_absent"] is True, "initial/gradient inventory absent or mutated")
        require(set(snapshot["after_init"]["initial_tensors"]) == set(snapshot["after_backward"]["gradients"]), "gradient names differ")
        require(all(type(snapshot[phase]["loss"]) in (int, float) and math.isfinite(snapshot[phase]["loss"])
                    for phase in ("after_forward", "before_backward", "after_backward")), "finite numeric loss required")
    first, second = observations
    result = dict(schema=SCHEMA, old_receipt_sha256=old_sha256, new_receipt_sha256=new_sha256,
        rng_equal={phase: first[phase]["rng"] == second[phase]["rng"] for phase in PHASES},
        initial_tensors_equal=first["after_init"]["initial_tensors"] == second["after_init"]["initial_tensors"],
        inputs_equal=first["before_forward"]["inputs"] == second["before_forward"]["inputs"],
        settings_equal=first["before_forward"]["settings"] == second["before_forward"]["settings"],
        optimizer_equal=first["before_forward"]["optimizer"] == second["before_forward"]["optimizer"],
        environment_equal=environments[0] == environments[1], environments=environments,
        losses={item["path"]: snapshot["after_forward"]["loss"] for item, snapshot in zip(receipts, observations)},
        gradients_equal=first["after_backward"]["gradients"] == second["after_backward"]["gradients"],
        automatic_pass=False, optimizer_steps=0, interpretation="One instrumented first backward only; no historical-run, later-step, repeatability or scientific equivalence claim.")
    write(out, result)
    return dict(output=str(out), sha256=digest(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    for name in ("old-root", "new-root", "trainer", "additive", "reflection", "out", "gpu-uuid", "expected-boot-id"):
        prepare_parser.add_argument("--"+name, required=True)
    worker_parser = commands.add_parser("worker")
    for name in ("plan-path", "plan-sha256", "path"):
        worker_parser.add_argument("--"+name, required=True)
    worker_parser.add_argument("--allow-native", action="store_true")
    comparison = commands.add_parser("compare")
    for name in ("old-receipt", "old-sha256", "new-receipt", "new-sha256", "out"):
        comparison.add_argument("--"+name, required=True)
    arguments = vars(parser.parse_args())
    command = arguments.pop("command")
    print(json.dumps({"prepare": prepare, "worker": worker, "compare": compare}[command](**arguments), sort_keys=True))


if __name__ == "__main__":
    main()
