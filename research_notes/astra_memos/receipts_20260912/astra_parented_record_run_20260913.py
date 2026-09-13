"""Bounded DEV coupling of fixed-guidance core and frozen native helpers; Main launches."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import ModuleType


SELF = Path(__file__).resolve()
SCOPE = "astra_parented_record_dev_20260913_v1"
PROTOCOL_PIN = "bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964"
CORE_PIN = "68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688"
MEMORY_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
LOWER_PIN = "80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413"
MEMORY_PLANS = (
    "66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1",
    "9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b",
    "48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea",
)
ARMS = ("P", "N")
STAGES = ("P_formation", "N_formation", "P_fit", "N_fit", "ORIGINAL_held",
          "P_held", "N_held", "P_retention", "N_retention")
SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 7200, 180, 180
CLEANUP_SECONDS, QUERY_SECONDS, LEASE_MARGIN = 40, 30, 21600
CLAIM = ("Fixed author-guidance amortization DEV only; actual own apply records, no teacher targets; "
         "historical original retention, unequal material yield/dose, no H1/H2 or automatic promotion; CONF untouched.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def load(record, name, expected):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "closed source binding required")
    path = Path(record["path"])
    require(path.is_absolute() and not any(part.is_symlink() for part in (path, *path.parents)), "absolute nonsymlink source required")
    raw = path.read_bytes()
    require(record["sha256"] == expected == hashlib.sha256(raw).hexdigest(), "source pin differs: " + name)
    module = ModuleType("parented_" + name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def runtime():
    return load(dict(path="/tmp/astra_real_record_memory_run_20260913.py", sha256=MEMORY_PIN), "memory", MEMORY_PIN)


def validate_spec(spec):
    require(type(spec) is dict and set(spec) == {"runner_sha256", "core", "protocol", "memory_runtime", "lower_runtime",
            "memory", "prior_episode_ids", "seed", "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed specification differs")
    require(spec["runner_sha256"] == digest(SELF), "runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in range(3), "original seed0/1/2 required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and
            type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "allocation identity required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "boot/lease required")
    require(set(spec["memory"]) == {"root", "plan_sha256"} and Path(spec["memory"]["root"]).is_absolute() and
            spec["memory"]["plan_sha256"] == MEMORY_PLANS[spec["seed"]], "original same-seed memory provenance required")
    for key, expected in (("protocol", PROTOCOL_PIN), ("core", CORE_PIN), ("memory_runtime", MEMORY_PIN), ("lower_runtime", LOWER_PIN)):
        record = spec[key]
        require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute() and
                record["sha256"] == expected == digest(record["path"]), key + " pin differs")
    prior = spec["prior_episode_ids"]
    require(set(prior) == {"path", "sha256"} and Path(prior["path"]).is_absolute() and
            prior["sha256"] == digest(prior["path"]), "prior exposure inventory pin differs")


def bind_inputs(spec, native=False):
    validate_spec(spec)
    memory = load(spec["memory_runtime"], "memory", MEMORY_PIN)
    lower = load(spec["lower_runtime"], "lower", LOWER_PIN)
    core = load(spec["core"], "core", CORE_PIN)
    original, bound = memory.verify(spec["memory"]["root"], spec["memory"]["plan_sha256"], native=native)
    require(original["specification"]["seed"] == original["specification"]["fit_seed"] == spec["seed"] and
            original["parent"] == bound["parent"], "original learner differs")
    parent = bound["parent"]
    history_path = Path(parent["collection"]["path"]).parent / "scores.json"
    require(digest(history_path) == parent["scores_sha256"], "original retention score pin differs")
    history = memory.read(history_path)
    prior = memory.read(spec["prior_episode_ids"]["path"])
    require(type(prior) is list and all(type(item) is str and item for item in prior), "explicit prior episode IDs required")
    prior = sorted(set(prior) | set(bound["plan"]["episode_ids"]))
    dependencies = core.load_dependencies(original["source"], protocol_path=spec["protocol"]["path"])
    manifest = core.build_manifest(dependencies, prior_episode_ids=prior)
    require(core.MAX_OUTPUT_TOKENS == dict(wake=96, record=192, restate=120) and
            core.TEMPERATURE == dict(wake=0.0, record=0.0, restate=0.5) and core.GENERATION_SEED == 0,
            "fixed core sampling contract differs")
    config = lower.candidate_config(original)
    require(config["lr"] == 3e-5 and config["epochs"] == 8 and config["batch_size"] == 1 and
            config["seed"] == spec["seed"] and config["max_steps"] == 0, "fixed write recipe differs")
    require(bound["helper"].ENGINE == bound["formation"].ENGINE and
            bound["helper"].PARAMS == dict(bound["formation"].PARAMS, max_tokens=192), "original retention settings differ")
    for panel, count in (("held", 48), ("canary", 12)):
        rows = history["cells"]["post"][panel]["rows"]
        require(len(rows) == count and len({row["row_id"] for row in rows}) == count and
                {row["row_id"] for row in rows} == {row["row_id"] for row in bound["retention"]["evaluation"][panel]},
                "historical original retention identities differ")
    return dict(bound, memory=memory, core=core, dependencies=dependencies, original=original,
                history=history, history_path=str(history_path), manifest=manifest, config=config)


def protected(spec, bound):
    return [SELF, spec["core"]["path"], spec["protocol"]["path"], spec["lower_runtime"]["path"],
            spec["prior_episode_ids"]["path"], spec["memory"]["root"], bound["history_path"],
            *bound["memory"].protected_inputs(bound["original"]["specification"], bound)]


def check_allocation(spec):
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "node boot differs")
    require(spec["lease_end"] > time.time() + SECONDS + LEASE_MARGIN, "six-hour finish margin required")


def original_retention_calls(bound):
    calls = []
    for panel in ("held", "canary"):
        for index, row in enumerate(bound["retention"]["evaluation"][panel]):
            old = next(call for call in bound["original_calls"] if call["call_id"] == f"{panel}_{index:02d}")
            require(old["row_id"] == row["row_id"] and old["messages"] == row["input_messages"], "original retention join differs")
            calls.append(dict(call_id=old["call_id"], panel=panel, row_id=row["row_id"], messages=old["messages"], native=old["native"]))
    require(len(calls) == 60, "original retention cardinality differs")
    return calls


def make_plan(root, spec, spec_sha256, bound, started):
    original = bound["original"]
    return dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=spec, spec_sha256=spec_sha256,
                self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                seed=spec["seed"], parent=bound["parent"], config=bound["config"], manifest=bound["manifest"],
                model=original["model"], model_files=original["model_files"], source=original["source"],
                environment=original["environment"], chat_template=original["chat_template"],
                engine=bound["formation"].ENGINE, params=bound["formation"].PARAMS,
                retention_params=dict(bound["formation"].PARAMS, max_tokens=192),
                retention_calls_sha256=bound["memory"].value_hash(original_retention_calls(bound)),
                gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"], lease_end=spec["lease_end"],
                work_started=started, deadline_monotonic=started["monotonic"] + SECONDS,
                stages=list(STAGES), limits=dict(calls=300, updates=256, seconds=SECONDS, collection=COLLECTION_SECONDS),
                historical_retention=dict(path=bound["history_path"], sha256=bound["parent"]["scores_sha256"], noncontemporaneous=True))


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only empty-CUDA native CPU prepare required")
    started = dict(monotonic=time.monotonic(), unix=time.time())
    memory = runtime()
    memory.offline()
    with memory.budget(PREPARE_SECONDS):
        require(digest(spec_path) == spec_sha256, "specification pin differs")
        spec = memory.read(spec_path)
        bound = bind_inputs(spec, native=True)
        check_allocation(spec)
        root = memory.new_external(root, [spec_path, *protected(spec, bound)])
        root.mkdir()
        memory.write(root / "prepare_started.json", started)
        try:
            with (root / "specification.json").open("xb") as stream:
                stream.write(Path(spec_path).read_bytes())
            require(digest(root / "specification.json") == spec_sha256, "spec changed during copy")
            tokenizer = bound["probe"].native_tokenizer(bound["original"]["model"])
            require(tokenizer.chat_template == bound["original"]["chat_template"], "native template differs")
            calls = memory.build_calls(dict(rows=[]), bound["retention"], bound["original_calls"], tokenizer, bound["probe"])
            require(calls == original_retention_calls(bound), "native retention preparation differs")
            memory.write(root / "retention_calls.json", calls)
            memory.write(root / "plan.json", make_plan(root, spec, spec_sha256, bound, started))
            memory.write(root / "prepared.json", dict(plan_sha256=digest(root / "plan.json"), retention_sha256=digest(root / "retention_calls.json")))
            return dict(status="PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"), deadline_monotonic=started["monotonic"] + SECONDS)
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    root = Path(root).absolute()
    memory = runtime()
    require(digest(root / "plan.json") == plan_sha256, "plan pin differs")
    plan = memory.read(root / "plan.json")
    require(not (root / "prepare_failure.json").exists() and not (root / "controller_failure.json").exists(), "failed run cannot continue")
    require(digest(root / "specification.json") == plan["spec_sha256"] and
            memory.read(root / "specification.json") == plan["specification"], "saved spec differs")
    bound = bind_inputs(plan["specification"], native=native)
    require(plan == make_plan(root, plan["specification"], plan["spec_sha256"], bound, memory.read(root / "prepare_started.json")), "independent plan reconstruction differs")
    require(memory.read(root / "prepared.json") == dict(plan_sha256=plan_sha256, retention_sha256=digest(root / "retention_calls.json")), "prepared inventory differs")
    require(digest(root / "retention_calls.json") == plan["retention_calls_sha256"], "plan-bound retention changed")
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == plan["specification"]["expected_boot_id"], "deadline boot differs")
    require(time.monotonic() < plan["deadline_monotonic"], "whole-work budget exhausted; no reset")
    return plan, bound


def directory(plan, stage):
    require(stage in STAGES, "unknown stage")
    if stage.endswith("_fit"):
        return Path(plan["root"]) / "arms" / stage.split("_")[0] / "run/WRITE_fit"
    return Path(plan["root"]) / "run" / stage


def arm_plan(plan, bound, arm):
    root = Path(plan["root"]) / "arms" / arm
    memory = bound["memory"]
    capture_value = memory.read(directory(plan, arm + "_formation") / "capture.json")
    require(memory.read(root / "capture.json") == capture_value and memory.read(root / "dataset.json") ==
            bound["core"].project_capture(capture_value, dependencies=bound["dependencies"]), "own raw source projection differs before fit")
    require(memory.read(root / "prepared.json") == {name: digest(root / name) for name in ("training.json", "dataset.json", "capture.json")}, "arm preparation changed")
    result = dict(plan, root=str(root), configs=dict(WRITE=plan["config"]),
                  specification=dict(plan["specification"], fit_seed=plan["seed"]),
                  input_hashes={name: digest(root / name) for name in ("training.json", "dataset.json", "capture.json")})
    return result, dict(bound, dataset=bound["memory"].read(root / "dataset.json"))


def prepare_arm(plan, bound, arm):
    memory, core = bound["memory"], bound["core"]
    require(memory.read(Path(plan["root"]) / (arm + "_formation.stage.json")) == bound["formation"].tree(directory(plan, arm + "_formation")), "formation changed before admission")
    capture = memory.read(directory(plan, arm + "_formation") / "capture.json")
    dataset = core.project_capture(capture, dependencies=bound["dependencies"])
    require(dataset["state"] == f"perception_seed{plan['seed']}_{arm}" and dataset["split"] == "dev" and
            dataset["counts"]["possible_slots"] == 16, "own apply source differs")
    root = Path(plan["root"]) / "arms" / arm
    root.mkdir(parents=True)
    memory.write(root / "capture.json", capture)
    memory.write(root / "dataset.json", dataset)
    if not dataset["rows"]:
        memory.write(root / "no_write.json", dict(status="NO_WRITE", calls=0, fits=0, updates=0, parent=plan["parent"], dataset_sha256=digest(root / "dataset.json")))
        return False
    tokenizer = bound["probe"].native_tokenizer(plan["model"])
    require(tokenizer.chat_template == plan["chat_template"], "writer template differs")
    training = memory.encode_training(dataset["rows"], tokenizer, bound["trainer"], bound["helper"], bound["probe"], plan["seed"])
    memory.write(root / "training.json", training)
    memory.write(root / "prepared.json", {name: digest(root / name) for name in ("training.json", "dataset.json", "capture.json")})
    return True


def route_for(plan, bound, arm):
    if arm == "ORIGINAL":
        path, inventory = plan["parent"]["adapter"], plan["parent"]["adapter_files"]
    else:
        root = Path(plan["root"]) / "arms" / arm
        dataset = bound["memory"].read(root / "dataset.json")
        if not dataset["rows"]:
            require(not directory(plan, arm + "_fit").exists(), "NO_WRITE must not have a fit")
            require(bound["memory"].read(root / "no_write.json") == dict(status="NO_WRITE", calls=0, fits=0, updates=0,
                    parent=plan["parent"], dataset_sha256=digest(root / "dataset.json")), "NO_WRITE receipt differs")
            return route_for(plan, bound, "ORIGINAL")
        view, arm_bound = arm_plan(plan, bound, arm)
        return bound["memory"].route_for(view, arm_bound, "WRITE")
    require(bound["formation"].tree(path) == inventory, "original adapter changed")
    return dict(name="parented_original", id=1, path=path)


class NativeCaptureFailure(BaseException):
    """Prevent infrastructure faults being converted into ordinary core refusals."""


def capture(plan, bound, stage, backend_factory=None):
    memory, core = bound["memory"], bound["core"]
    arm, phase = stage.split("_")
    state = f"perception_seed{plan['seed']}_{'INITIAL' if arm == 'ORIGINAL' else arm}"
    route = route_for(plan, bound, "ORIGINAL" if phase == "formation" else arm)
    target = directory(plan, stage)
    receipt = dict(stage=stage, state=state, route=route, core=plan["specification"]["core"], parent=plan["parent"], model_files=plan["model_files"])
    memory.write(target / "identity.json", receipt)
    backend, requests, responses = None, [], []
    try:
        backend = (backend_factory or bound["formation"].Native)(plan, bound["probe"], route)
        require(backend.tokenizer.chat_template == plan["chat_template"], "cold template differs")
        def generate(core_request):
            try:
                kind = core_request["kind"]
                require(core_request["state"] == state and core_request["phase"] == phase and core_request["split"] == "dev" and
                        core_request["episode_id"] in core.episode_ids("dev", phase) and kind in core.MAX_OUTPUT_TOKENS and
                        core_request["max_output_tokens"] == core.MAX_OUTPUT_TOKENS[kind] and
                        core_request["temperature"] == core.TEMPERATURE[kind] and core_request["seed"] == core.GENERATION_SEED,
                        "core callback contract differs")
                require(len(requests) < (42 if phase == "formation" else 32) and not any(
                        previous["core_request"]["request_id"] == core_request["request_id"] for previous in requests), "duplicate/extra callback")
                native = bound["probe"].render(backend.tokenizer, core_request["input_messages"])
                params = dict(plan["params"], max_tokens=core.MAX_OUTPUT_TOKENS[kind], temperature=core.TEMPERATURE[kind], seed=core.GENERATION_SEED)
                require(len(native["prompt_token_ids"]) + params["max_tokens"] <= plan["engine"]["max_model_len"], "dynamic context overflow")
                request = dict(call_id=f"{len(requests):02d}", core_request=core_request, messages=core_request["input_messages"], native=native, params=params, lora_request=route)
                memory.write(target / (request["call_id"] + ".request.json"), request)
                requests.append(request)
                response = backend.generate(request)
                memory.write(target / (request["call_id"] + ".response.json"), response)
                bound["formation"].validate_response(request, response, route)
                responses.append(response)
                return dict(request_id=core_request["request_id"], state=state, raw=response["text"], finish_reason=response["finish_reason"], native_response=response)
            except Exception as error:
                raise NativeCaptureFailure(str(error)) from error
        if phase == "retention":
            calls = memory.build_calls(dict(rows=[]), bound["retention"], bound["original_calls"], backend.tokenizer, bound["probe"])
            require(calls == memory.read(Path(plan["root"]) / "retention_calls.json"), "original retention prefix differs")
            for call in calls:
                request = dict(call, params=plan["retention_params"], lora_request=route)
                memory.write(target / (call["call_id"] + ".request.json"), request)
                requests.append(request)
                response = backend.generate(request)
                memory.write(target / (call["call_id"] + ".response.json"), response)
                bound["formation"].validate_response(request, response, route)
                responses.append(response)
        else:
            result = core.run_state(state, generate, phase=phase, split="dev", dependencies=bound["dependencies"], binding=receipt)
            require(core.audit_capture(result, dependencies=bound["dependencies"])["calls_replayed"] == len(requests), "core/raw call count differs")
            memory.write(target / "capture.json", result)
        require(len(requests) == len(responses), "incomplete native response capture")
        memory.write(target / "cost.json", dict(calls=len(responses), updates=0,
            prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses),
            output_tokens=sum(len(response["output_token_ids"]) for response in responses),
            generation_seconds=sum(response["ended"] - response["started"] for response in responses),
            contact_tokens_per_literal={key: len(backend.tokenizer.encode(text, add_special_tokens=False)) for key, text in core.CONTACTS.items()} if phase == "formation" else {}))
    finally:
        if backend is not None:
            backend.close()


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES, "Main-only GPU worker required")
    memory = runtime()
    memory.offline()
    require(digest(Path(root) / "plan.json") == plan_sha256, "worker plan pin differs")
    raw_plan = memory.read(Path(root) / "plan.json")
    target = directory(raw_plan, stage)
    with memory.budget(raw_plan["deadline_monotonic"] - time.monotonic() - COLLECTION_SECONDS - CLEANUP_SECONDS - QUERY_SECONDS):
        try:
            plan, bound = verify(root, plan_sha256, native=True)
            identity = memory.identity(os.getpid())
            launch = memory.read(target / "launch.json")
            require(launch["identity"] == identity and launch["stage"] == stage and launch["plan_sha256"] == plan_sha256,
                    "worker launch identity differs")
            require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(), "worker allocation/isolation differs")
            memory.write(target / "started.json", dict(identity=identity, stage=stage, plan_sha256=plan_sha256))
            if stage.endswith("_fit"):
                view, arm_bound = arm_plan(plan, bound, stage[0])
                memory.fit_arm(view, arm_bound, "WRITE")
            else:
                capture(plan, bound, stage)
            memory.write(target / "worker_done.json", dict(stage=stage, plan_sha256=plan_sha256))
        except BaseException as error:
            memory.failure(target / "failure.json", error)
            raise


def run_stage(plan, bound, plan_sha256, stage):
    memory, probe = bound["memory"], bound["probe"]
    deadline = plan["deadline_monotonic"] - COLLECTION_SECONDS
    check_allocation(plan["specification"])
    require(deadline - time.monotonic() > 2 * QUERY_SECONDS + CLEANUP_SECONDS + 5 and probe.gpu_state(plan) is True, "vacancy/budget precheck failed")
    target = directory(plan, stage)
    target.mkdir(parents=True)
    process, expected = None, None
    try:
        with (target / "stdout.log").open("xb") as output, (target / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--stage", stage, "--allow-gpu"]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"], PYTHONPATH=plan["source"]), start_new_session=True)
            expected = memory.identity(process.pid)
            require(expected["pgid"] == process.pid, "worker group differs")
            memory.write(target / "launch.json", dict(identity=expected, stage=stage, plan_sha256=plan_sha256, command=command))
            code = process.wait(timeout=max(.01, deadline - time.monotonic() - CLEANUP_SECONDS - QUERY_SECONDS - 5))
            memory.write(target / "exit.json", dict(identity=expected, returncode=code))
            require(code == 0, "native worker failed")
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity; release unknown")
                memory.cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True, "owned release/vacancy failed")
                memory.write(target / "released.json", dict(identity=expected, stage=stage, group_absent=True, gpu_vacant=True))
            except BaseException as error:
                memory.failure(target / "cleanup_failure.json", error)
                raise
    memory.write(Path(plan["root"]) / (stage + ".stage.json"), bound["formation"].tree(target))


def validate_completed(plan, bound, plan_sha256):
    memory, core = bound["memory"], bound["core"]
    inventory, identities, captures, costs, fits = {}, [], {}, {}, {}
    for stage in STAGES:
        target = directory(plan, stage)
        if stage.endswith("_fit"):
            arm = stage[0]
            root = Path(plan["root"]) / "arms" / arm
            capture_path = directory(plan, arm + "_formation") / "capture.json"
            source = memory.read(capture_path)
            require(memory.read(root / "capture.json") == source and memory.read(root / "dataset.json") ==
                    core.project_capture(source, dependencies=bound["dependencies"]), "arm source projection differs")
            route_for(plan, bound, arm)
            inventory[arm + "_material"] = bound["formation"].tree(root)
            if not memory.read(root / "dataset.json")["rows"]:
                fits[arm] = dict(status="NO_WRITE", updates=0, fits=0)
                continue
            view, arm_bound = arm_plan(plan, bound, arm)
            prepared = memory.read(root / "training.json")
            manifest = memory.read(target / "adapter/train_manifest.json")
            memory.check_fit(manifest, prepared, plan["config"], plan["parent"], "WRITE")
            fit = memory.read(target / "fit.json")
            require(fit["training_sha256"] == view["input_hashes"]["training.json"] == manifest["corpus"]["sha256"] and
                    fit["updates"] == prepared["updates"] and fit["calls"] == 0, "fit input/accounting differs")
            fits[arm] = dict(status="WRITE", updates=prepared["updates"], fits=1, dose=prepared,
                             source_state=manifest["warm_start"]["source_state"], initialized_state=manifest["warm_start"]["initialized_state"])
        else:
            arm, phase = stage.split("_")
            route = route_for(plan, bound, "ORIGINAL" if phase == "formation" else arm)
            expected_identity = dict(stage=stage, state=f"perception_seed{plan['seed']}_{'INITIAL' if arm == 'ORIGINAL' else arm}",
                route=route, core=plan["specification"]["core"], parent=plan["parent"], model_files=plan["model_files"])
            require(memory.read(target / "identity.json") == expected_identity, "capture identity differs")
            requests = sorted(target.glob("*.request.json"))
            require({path.stem.removesuffix(".request") for path in requests} ==
                    {path.stem.removesuffix(".response") for path in target.glob("*.response.json")}, "raw response inventory differs")
            events = []
            if phase != "retention":
                capture_value = memory.read(target / "capture.json")
                core.audit_capture(capture_value, dependencies=bound["dependencies"])
                require(capture_value["state"] == f"perception_seed{plan['seed']}_{'INITIAL' if arm == 'ORIGINAL' else arm}" and
                        capture_value["phase"] == phase and capture_value["split"] == "dev" and
                        capture_value["binding"] == expected_identity, "capture state/binding differs")
                events = [event for event in capture_value["events"] if event["kind"] == "call"]
                require(len(requests) == len(events), "capture/raw cardinality differs")
                captures[stage] = capture_value
            else:
                require(len(requests) == 60, "retention workload differs")
            tokens, outputs, seconds = 0, 0, 0.0
            for index, path in enumerate(requests):
                request = memory.read(path)
                response = memory.read(path.with_name(path.name.replace(".request.json", ".response.json")))
                bound["formation"].validate_response(request, response, route)
                if events:
                    event = events[index]
                    require(request["core_request"] == event["request"] and event["response"]["native_response"] == response and
                            event["response"]["raw"] == response["text"] and request["messages"] == event["request"]["input_messages"], "raw/source replay differs")
                    kind = event["request"]["kind"]
                    require(request["params"] == dict(plan["params"], max_tokens=core.MAX_OUTPUT_TOKENS[kind], temperature=core.TEMPERATURE[kind], seed=core.GENERATION_SEED), "sampling differs")
                else:
                    call = next(item for item in memory.read(Path(plan["root"]) / "retention_calls.json") if item["call_id"] == request["call_id"])
                    require(request == dict(call, params=plan["retention_params"], lora_request=route), "retention call differs")
                tokens += len(response["actual_prompt_token_ids"])
                outputs += len(response["output_token_ids"])
                seconds += response["ended"] - response["started"]
            cost = memory.read(target / "cost.json")
            require(cost["calls"] == len(requests) and cost["updates"] == 0 and cost["prompt_tokens"] == tokens and
                    cost["output_tokens"] == outputs and abs(cost["generation_seconds"] - seconds) < 1e-7, "cost differs")
            costs[stage] = cost
        require(not any((target / name).exists() for name in ("failure.json", "cleanup_failure.json")), "failed worker/release")
        launch = memory.read(target / "launch.json")
        expected = launch["identity"]
        require(launch["stage"] == stage and launch["plan_sha256"] == plan_sha256 and
                memory.read(target / "started.json") == dict(identity=expected, stage=stage, plan_sha256=plan_sha256) and
                memory.read(target / "worker_done.json") == dict(stage=stage, plan_sha256=plan_sha256) and
                memory.read(target / "exit.json") == dict(identity=expected, returncode=0) and
                memory.read(target / "released.json") == dict(identity=expected, stage=stage, group_absent=True, gpu_vacant=True), "worker exit/release custody differs")
        identities.append((expected["pid"], expected["start_ticks"]))
        inventory[stage] = bound["formation"].tree(target)
        require(memory.read(Path(plan["root"]) / (stage + ".stage.json")) == inventory[stage], "closed stage inventory changed")
    require(len(set(identities)) == len(identities), "cold worker identities reused")
    if all(fits[arm]["fits"] for arm in ARMS):
        require(fits["P"]["source_state"] == fits["N"]["source_state"] and fits["P"]["initialized_state"] == fits["N"]["initialized_state"], "fork initial tensors differ")
    require(sum(cost["calls"] for cost in costs.values()) <= 300 and sum(fit["updates"] for fit in fits.values()) <= 256, "per-seed work cap exceeded")
    return dict(inventory=inventory, captures=captures, costs=costs, fits=fits)


def source_novelty(formation, held):
    applied = [turn["execution"] for episode in formation["episodes"] if episode["stage"] == "apply"
               for turn in episode["turns"] if turn["execution"] is not None]
    seen = {tuple(execution["values"]) for execution in applied}
    triples = [tuple(turn["execution"]["values"]) for episode in held["episodes"]
               for turn in episode["turns"] if turn["execution"] is not None]
    return dict(held_executions=len(triples), distinct_held_triples=len(set(triples)),
                held_executions_with_unseen_apply_triple=sum(triple not in seen for triple in triples),
                same_initial_tasks_not_same_experience=True, new_ids_not_unseen_rules_or_base_knowledge=True)


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only empty-CUDA controller required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    require(not (root / "controller_started.json").exists(), "controller already claimed; no retry")
    try:
        raw_plan = memory.read(root / "plan.json")
        require(digest(root / "plan.json") == plan_sha256, "plan pin differs before controller deadline")
        with memory.budget(raw_plan["deadline_monotonic"] - time.monotonic() - COLLECTION_SECONDS):
            memory.write(root / "controller_started.json", dict(identity=memory.identity(os.getpid()), plan_sha256=plan_sha256))
            plan, bound = verify(root, plan_sha256, native=True)
            for stage in STAGES:
                if stage.endswith("_fit") and not prepare_arm(plan, bound, stage[0]):
                    continue
                run_stage(plan, bound, plan_sha256, stage)
            checked = validate_completed(plan, bound, plan_sha256)
            memory.write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, inventory=checked["inventory"],
                calls=sum(cost["calls"] for cost in checked["costs"].values()), fits=sum(fit["fits"] for fit in checked["fits"].values()),
                updates=sum(fit["updates"] for fit in checked["fits"].values()), automatic_pass=False,
                elapsed_seconds=time.monotonic() - plan["work_started"]["monotonic"]))
            return dict(status="CAPTURE_COMPLETE_NOT_SCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def retention_scores(plan, bound, arm):
    memory = bound["memory"]
    cells, paired = {}, {}
    for panel in ("held", "canary"):
        cells[panel] = []
        old = {row["row_id"]: row for row in bound["history"]["cells"]["post"][panel]["rows"]}
        for index, row in enumerate(bound["retention"]["evaluation"][panel]):
            path = directory(plan, arm + "_retention") / f"{panel}_{index:02d}.response.json"
            response = memory.read(path)
            score = bound["material"].score_row(row, response["text"], response["finish_reason"])
            bound["helper"].validate_score(score, response["finish_reason"])
            cells[panel].append(dict(row_id=row["row_id"], raw=response["text"], finish_reason=response["finish_reason"], score=score, response_sha256=digest(path)))
        paired[panel] = {metric: dict(gains=[row["row_id"] for row in cells[panel] if row["score"][metric] and not old[row["row_id"]]["score"][metric]],
            losses=[row["row_id"] for row in cells[panel] if not row["score"][metric] and old[row["row_id"]]["score"][metric]]) for metric in ("content_correct", "strict")}
    return dict(cells=cells, versus_original=paired, noncontemporaneous_original=True, exploratory=True)


def collect(root, plan_sha256, completion_sha256, out):
    collection_started = time.monotonic()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "empty-CUDA collector required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    raw_plan = memory.read(root / "plan.json")
    require(digest(root / "plan.json") == plan_sha256, "plan pin differs before collection deadline")
    with memory.budget(min(collection_started + COLLECTION_SECONDS, raw_plan["deadline_monotonic"]) - time.monotonic()):
        claim = root.with_name(root.name + ".collection_claim.json")
        memory.write(claim, dict(plan_sha256=plan_sha256, out=str(Path(out).absolute()), retry=False))
        plan, bound = verify(root, plan_sha256)
        out = memory.new_external(out, [root, *protected(plan["specification"], bound)])
        out.mkdir()
        try:
            owner = memory.read(root / "controller_started.json")["identity"]
            require(not Path(f"/proc/{owner['pid']}").exists(), "controller still live; collect after holder exit")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            check_allocation(plan["specification"])
            require(bound["probe"].gpu_state(plan) is True, "collection vacancy failed")
            checked = validate_completed(plan, bound, plan_sha256)
            for stage in STAGES:
                target = directory(plan, stage)
                if target.exists():
                    identity = memory.read(target / "launch.json")["identity"]
                    require(not Path(f"/proc/{identity['pid']}").exists() and not bound["probe"].group_alive(identity["pgid"]), "worker/group still live")
            complete = memory.read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and complete["inventory"] == checked["inventory"] and
                    complete["calls"] == sum(cost["calls"] for cost in checked["costs"].values()) and
                    complete["updates"] == sum(fit["updates"] for fit in checked["fits"].values()) and
                    complete["fits"] == sum(fit["fits"] for fit in checked["fits"].values()) and complete["automatic_pass"] is False,
                    "complete custody/accounting differs")
            formation = [checked["captures"][arm + "_formation"] for arm in ARMS]
            held = [checked["captures"][arm + "_held"] for arm in ("ORIGINAL", *ARMS)]
            report = dict(scope=SCOPE, claim=CLAIM, seed=plan["seed"], plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                formation=bound["core"].compare_states(formation, dependencies=bound["dependencies"]),
                held=bound["core"].compare_states(held, dependencies=bound["dependencies"]),
                retention={arm: retention_scores(plan, bound, arm) for arm in ARMS}, historical_original=plan["historical_retention"],
                material={arm: memory.read(Path(plan["root"]) / "arms" / arm / "dataset.json") for arm in ARMS},
                source_novelty={arm: source_novelty(checked["captures"][arm + "_formation"], checked["captures"][arm + "_held"]) for arm in ARMS},
                costs=checked["costs"], fits=checked["fits"], calls=complete["calls"], updates=complete["updates"],
                automatic_pass=False, scientific_pass=None, outcome_gate=None, cohort="one of three fixed learner pairs; no winner selection")
            baseline = checked["captures"]["ORIGINAL_held"]["summary"]
            report["held_vs_initial"] = {arm: {metric: checked["captures"][arm + "_held"]["summary"][metric] - baseline[metric]
                for metric in ("production_eligible", "content_correct", "strict_canonical")} for arm in ARMS}
            require(validate_completed(plan, bound, plan_sha256)["inventory"] == checked["inventory"] and
                    bound["probe"].gpu_state(plan) is True and time.monotonic() < plan["deadline_monotonic"], "post-collection custody/release/budget differs")
            memory.write(out / "scores.json", report)
            memory.write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256,
                elapsed_whole_seconds=time.monotonic() - plan["work_started"]["monotonic"], automatic_pass=False))
            return dict(status="COLLECTED_DEV_ONLY", scores_sha256=digest(out / "scores.json"), out=str(out))
        except BaseException as error:
            memory.failure(out / "collection_failure.json", error)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "worker", "controller", "collect"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--spec")
    parser.add_argument("--spec-sha256")
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--completion-sha256")
    parser.add_argument("--out")
    parser.add_argument("--allow-native", action="store_true")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "prepare":
        result = prepare(args.root, args.spec, args.spec_sha256, args.allow_native)
    elif args.action == "worker":
        result = worker(args.root, args.plan_sha256, args.stage, args.allow_gpu)
    elif args.action == "controller":
        result = controller(args.root, args.plan_sha256, args.allow_gpu)
    else:
        result = collect(args.root, args.plan_sha256, args.completion_sha256, args.out)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
