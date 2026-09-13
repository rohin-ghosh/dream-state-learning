"""Inference-only fixed lesson alignment. Main owns native placement and launch."""
from __future__ import annotations

from collections import Counter
import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time


SELF = Path(__file__).resolve()
SCOPE = "astra_parenting_alignment_inference_20260913_v1"
PROTOCOL_PIN = "5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5"
CORE_PIN = "71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010"
CAPTURE_PIN = "1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107"
PARENTED_PIN = "54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8"
PARENT_SOURCE_PIN = "f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a"
NATIVE_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
PUBLIC_PIN = "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
ARMS = ("ALIGNED", "SWAPPED", "NO_PARENT")
CALL_CAPS = {"ALIGNED": 36, "SWAPPED": 36, "NO_PARENT": 32}
SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 3600, 180, 180
CLEANUP_SECONDS, QUERY_SECONDS, LEASE_MARGIN = 40, 30, 21600
CLAIM = ("Inference-only exploratory task alignment with a child restatement in context; not persistent parenting, "
         "SLEEP, fitting, autonomous learning, H1/H2, mechanism freeze or promotion. Original exposed perception roots only.")


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
    require(type(record) is dict and set(record) == {"path", "sha256"} and expected is not None, "closed frozen module binding required")
    path = Path(record["path"])
    require(path.is_absolute() and not any(item.is_symlink() for item in (path, *path.parents)) and
            record["sha256"] == expected == digest(path), "source pin/path differs: " + name)
    spec = importlib.util.spec_from_file_location("alignment_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def runtime():
    sys.dont_write_bytecode = True
    capture = load(dict(path="/tmp/astra_own_source_replay_capture_20260913.py", sha256=CAPTURE_PIN), "capture", CAPTURE_PIN)
    return capture.lifecycle()


def validate_spec(spec):
    require(set(spec) == {"runner_sha256", "core", "protocol", "capture_runtime", "parented_runtime", "parent_source", "native", "public",
                          "archive", "source_root", "prior_task_ids", "seed", "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed spec differs")
    require(spec["runner_sha256"] == digest(SELF), "alignment runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2), "original seed0/1/2 required")
    for key in ("protocol", "archive", "prior_task_ids"):
        record = spec[key]
        require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute() and digest(record["path"]) == record["sha256"], "input pin differs: " + key)
    require(spec["protocol"]["sha256"] == PROTOCOL_PIN and Path(spec["source_root"]).is_absolute(), "frozen protocol/source required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and type(spec["gpu_uuid"]) is str and
            spec["gpu_uuid"].startswith("GPU-") and type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "Main allocation/boot/lease required")


def allocation(plan):
    spec = plan["specification"]
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "current boot differs")
    require(spec["lease_end"] > time.time() + SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour lease-finish margin required")


def state_for(seed, arm):
    require(type(seed) is int and seed in (0, 1, 2) and arm in ARMS, "unknown seed/arm")
    return f"perception_seed{seed}_{arm}"


def bind(spec, native=False):
    validate_spec(spec)
    memory = runtime()
    capture = load(spec["capture_runtime"], "capture", CAPTURE_PIN)
    parented = load(spec["parented_runtime"], "parented", PARENTED_PIN)
    source = load(spec["parent_source"], "original_source", PARENT_SOURCE_PIN)
    formation = load(spec["native"], "native", NATIVE_PIN)
    probe = load(spec["public"], "public", PUBLIC_PIN)
    core = load(spec["core"], "core", CORE_PIN)
    require(spec["archive"]["sha256"] == source.ARCHIVE_PIN, "original parent archive required")
    _, producer, provenance = source.original_inputs(spec["seed"], archive_path=spec["archive"]["path"])
    parent_material, _ = source.dependencies(spec["source_root"])
    with tarfile.open(spec["archive"]["path"], "r:") as archive:
        original_bytes = archive.extractfile(provenance["plan_member"]).read()
    require(hashlib.sha256(original_bytes).hexdigest() == producer["parent_plan_sha256"], "original archived plan differs")
    original = source.decode(original_bytes)
    require(original["learner_seed"] == spec["seed"] and original["skill"] == "perception" and
            producer["adapter"] == original["root"] + "/run/fit/adapter" and formation.tree(producer["adapter"]) == producer["adapter_files"],
            "original pre-memory parent differs")
    require(original["engine"] == formation.ENGINE and original["params"] == probe.PARAMS, "original inference configuration differs")
    prior = memory.read(spec["prior_task_ids"]["path"])
    require(type(prior) is list and len(prior) == len(set(prior)) and all(type(value) is str and value for value in prior), "explicit unique prior task IDs required")
    dependencies = core.load_dependencies(spec["source_root"], protocol_path=spec["protocol"]["path"])
    manifest = core.build_manifest(dependencies, prior_ids=prior)
    require(all(state_for(spec["seed"], arm) in core.STATES for arm in ARMS), "core state inventory differs")
    if native:
        require(original["python"] == os.path.abspath(sys.executable) and original["python_sha256"] == digest(sys.executable), "original native Python differs")
        require(original["environment"] == dict(probe=probe.native_environment(), peft=importlib.metadata.version("peft")) and
                original["model_files"] == probe.model_hashes(original["model"]), "frozen native environment/base differs")
    return dict(memory=memory, capture_runtime=capture, parented=parented, parent_source=source, formation=formation, probe=probe,
                core=core, dependencies=dependencies, manifest=manifest, prior=prior, producer=producer, provenance=provenance,
                original=original, original_bytes=original_bytes, parent_material=parent_material)


def route_for(plan, bound):
    return bound["capture_runtime"].route_for(plan, plan["seed"], bound["formation"])


def identity_for(plan, arm, bound):
    return dict(scope=SCOPE, state=state_for(plan["seed"], arm), seed=plan["seed"], arm=arm, producer=plan["producers"][str(plan["seed"])],
                route=route_for(plan, bound), core=plan["specification"]["core"], model_files=plan["model_files"], engine=plan["engine"], params=plan["params"])


def protected(spec, bound):
    paths = [SELF, spec["source_root"], bound["original"]["root"], bound["original"]["model"]]
    paths += [spec[key]["path"] for key in ("core", "protocol", "capture_runtime", "parented_runtime", "parent_source", "native", "public", "archive", "prior_task_ids")]
    return paths


def source_files(spec, bound):
    paths = {"sources/" + Path(spec[key]["path"]).name: Path(spec[key]["path"])
             for key in ("core", "protocol", "capture_runtime", "parented_runtime", "parent_source", "native", "public")}
    paths["prior_task_ids.json"] = Path(spec["prior_task_ids"]["path"])
    parented_core = bound["dependencies"].parented
    for path, checksum in ((bound["core"].PARENTED_PATH, bound["core"].PARENTED_SHA256),
                           (parented_core.V2_PATH, parented_core.V2_SHA256),
                           (parented_core.MEMORY_PATH, parented_core.MEMORY_SHA256),
                           (bound["parent_source"].RUNNER_PATH, bound["parent_source"].RUNNER_PIN),
                           (bound["parent_source"].MATERIAL_PATH, bound["parent_source"].MATERIAL_PIN),
                           (str(bound["memory"].SELF), bound["capture_runtime"].LIFECYCLE_PIN)):
        require(digest(path) == checksum, "frozen transitive helper source differs")
        paths["sources/" + Path(path).name] = Path(path)
    code_pins = dict(bound["parent_material"].PINS)
    for relative, checksum in bound["dependencies"].manifest["full_source_sha256"].items():
        require(relative not in code_pins or code_pins[relative] == checksum, "source pin conflict")
        code_pins[relative] = checksum
    for relative, checksum in code_pins.items():
        path = Path(spec["source_root"]) / relative
        require(path.resolve().is_relative_to(Path(spec["source_root"]).resolve()) and digest(path) == checksum, "world/source snapshot differs")
        paths["source_snapshot/" + relative] = path
    return paths


def preflight(bound, tokenizer):
    require(tokenizer.chat_template == bound["original"]["chat_template"], "original native template differs")
    lessons = bound["core"].LESSONS
    require(set(lessons) == {"P", "C"} and all(type(value) is str and value for value in lessons.values()), "fixed answer-free lessons required")
    literals = {key: len(tokenizer.encode(text, add_special_tokens=False)) for key, text in lessons.items()}
    core, probe = bound["core"], bound["probe"]
    tasks = bound["manifest"]["schedules"][str(bound["producer"]["learner_seed"])]
    require(len(tasks) == 16, "sixteen preregistered task prompts required")
    prompts = {}
    for key, text, cap in [("lesson_" + key, core.RESTATE_TEMPLATE.format(lesson=text), core.MAX_OUTPUT_TOKENS["restate"])
                           for key, text in lessons.items()] + [(task["task_id"], task["ordinary_prompt"], core.MAX_OUTPUT_TOKENS["wake"]) for task in tasks]:
        rendered = probe.render(tokenizer, [{"role": "user", "content": text}])
        require(len(rendered["prompt_token_ids"]) + cap <= bound["original"]["engine"]["max_model_len"], "static native context overflow")
        prompts[key] = rendered
    return dict(lesson_literal_tokens=literals, lesson_multiset_tokens_per_lesson_arm=2 * sum(literals.values()),
                equal_lesson_multiset=True, individual_lesson_lengths_equal=literals["P"] == literals["C"],
                static_prompts=prompts,
                dynamic_context_check="Every actual dynamic prompt is rendered/checked before generation and re-rendered at collection; no synthetic child note is substituted.")


def make_plan(root, spec, spec_sha256, bound, inputs):
    original = bound["original"]
    return dict(scope=SCOPE, claim=CLAIM, root=str(Path(root).absolute()), seed=spec["seed"], arms=list(ARMS),
                states=[state_for(spec["seed"], arm) for arm in ARMS], specification=spec, spec_sha256=spec_sha256,
                self_sha256=digest(SELF), **{key: original[key] for key in
                ("model", "model_files", "environment", "python", "python_sha256", "chat_template", "engine", "params")},
                source=spec["source_root"], producers={str(spec["seed"]): bound["producer"]},
                original_source=bound["provenance"], input_hashes=inputs, gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"],
                limits=dict(controller=SECONDS, collection=COLLECTION_SECONDS, calls_per_arm=CALL_CAPS, calls_per_seed=104,
                            campaign_calls=312, campaign_allocation_hours=5, fits=0, updates=0, parent_model_calls=0, tasks_per_arm=16))


def prepare(root, spec_path, spec_sha256, allow_native=False):
    entry = time.monotonic()
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only native CPU prepare with empty CVD required")
    memory = runtime()
    memory.offline()
    with memory.budget(entry + PREPARE_SECONDS - time.monotonic()):
        require(digest(spec_path) == spec_sha256, "spec pin differs")
        spec = memory.read(spec_path)
        bound = bind(spec, native=True)
        root = memory.new_external(root, [spec_path, *protected(spec, bound)])
        allocation(dict(specification=spec))
        root.mkdir()
        memory.write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time(), entry_monotonic=entry))
        try:
            tokenizer = bound["probe"].native_tokenizer(bound["original"]["model"])
            memory.write(root / "manifest.json", bound["manifest"])
            memory.write(root / "preflight.json", preflight(bound, tokenizer))
            with (root / "original_plan.json").open("xb") as output:
                output.write(bound["original_bytes"])
            inputs = {name: digest(root / name) for name in ("manifest.json", "preflight.json", "original_plan.json")}
            for name, path in {**source_files(spec, bound), "spec.json": Path(spec_path)}.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                expected = digest(path)
                with target.open("xb") as output:
                    output.write(path.read_bytes())
                require(digest(target) == expected, "copied source changed")
                inputs[name] = expected
            plan = make_plan(root, spec, spec_sha256, bound, inputs)
            memory.write(root / "plan.json", plan)
            elapsed = time.monotonic() - entry
            require(elapsed <= PREPARE_SECONDS, "native CPU prepare budget exceeded")
            memory.write(root / "prepare_done.json", dict(plan_sha256=digest(root / "plan.json"), elapsed_seconds=elapsed))
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"), seed=spec["seed"],
                        states=plan["states"], limits=plan["limits"], prepare_seconds=elapsed)
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    memory = runtime()
    root = Path(root).absolute()
    require(digest(root / "plan.json") == plan_sha256, "alignment plan pin differs")
    plan = memory.read(root / "plan.json")
    bound = bind(plan["specification"], native=native)
    inputs = plan["input_hashes"]
    require(set(inputs) == {"manifest.json", "preflight.json", "original_plan.json", "spec.json", *source_files(plan["specification"], bound)} and
            plan == make_plan(root, plan["specification"], plan["spec_sha256"], bound, inputs), "closed prepared plan differs")
    require(plan["python"] == os.path.abspath(sys.executable) and plan["python_sha256"] == digest(sys.executable), "native interpreter differs")
    require(not (root / "prepare_failure.json").exists() and memory.read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            digest(root / "spec.json") == plan["spec_sha256"] and memory.read(root / "spec.json") == plan["specification"], "preparation/spec differs")
    finished = memory.read(root / "prepare_done.json")
    require(finished["plan_sha256"] == plan_sha256 and type(finished["elapsed_seconds"]) in (int, float) and
            0 <= finished["elapsed_seconds"] <= PREPARE_SECONDS, "prepare completion/budget differs")
    for name, checksum in inputs.items():
        require(digest(root / name) == checksum, "prepared input changed: " + name)
    for name, path in source_files(plan["specification"], bound).items():
        require(inputs[name] == digest(path), "source snapshot no longer matches source")
    require((root / "original_plan.json").read_bytes() == bound["original_bytes"] and
            memory.encoded(memory.read(root / "manifest.json")) == memory.encoded(bound["manifest"]), "original plan/world manifest differs")
    return plan, bound


def params_for(plan, core, request):
    kind = request["kind"]
    require(kind in core.MAX_OUTPUT_TOKENS and request["max_output_tokens"] == core.MAX_OUTPUT_TOKENS[kind] and
            request["temperature"] == core.TEMPERATURE[kind] and request["seed"] == core.GENERATION_SEED, "frozen callback sampling differs")
    return dict(plan["params"], max_tokens=core.MAX_OUTPUT_TOKENS[kind], temperature=core.TEMPERATURE[kind], seed=core.GENERATION_SEED)


def capture_arm(plan, bound, arm, backend_factory=None):
    require(arm in ARMS, "unknown alignment arm")
    memory, core, probe, formation = (bound[key] for key in ("memory", "core", "probe", "formation"))
    directory = Path(plan["root"]) / "run" / arm
    state, identity = state_for(plan["seed"], arm), identity_for(plan, arm, bound)
    route = identity["route"]
    memory.write(directory / "identity.json", identity)
    started = time.monotonic()
    backend, calls, responses, infra_failures = None, [], [], []
    try:
        backend = (backend_factory or formation.Native)(plan, probe, route)
        require(preflight(bound, backend.tokenizer) == memory.read(Path(plan["root"]) / "preflight.json"), "native preflight/template drift")
        def generate(core_request):
            try:
                require(core_request["state"] == state and len(calls) < CALL_CAPS[arm] and
                        not any(call["request"]["request_id"] == core_request["request_id"] for call in calls), "callback state/cardinality/duplicate differs")
                params = params_for(plan, core, core_request)
                native = probe.render(backend.tokenizer, core_request["input_messages"])
                require(len(native["prompt_token_ids"]) + params["max_tokens"] <= plan["engine"]["max_model_len"], "dynamic context overflow")
                request = dict(call_id=f"{len(calls):02d}", core_request=core_request, messages=core_request["input_messages"],
                               native=native, params=params, lora_request=route)
                memory.write(directory / (request["call_id"] + ".request.json"), request)
                calls.append(dict(request=copy.deepcopy(core_request), response=None))
                response = backend.generate(request)
                memory.write(directory / (request["call_id"] + ".response.json"), response)
                formation.validate_response(request, response, route)
                require(started <= response["started"] <= response["ended"] <= time.monotonic(), "generation clock outside capture")
                responses.append(response)
                raw = dict(request_id=core_request["request_id"], state=state, raw=response["text"], finish_reason=response["finish_reason"])
                calls[-1]["response"] = copy.deepcopy(raw)
                return raw
            except Exception as error:
                infra_failures.append(str(error))
                raise bound["parented"].NativeCaptureFailure(str(error)) from error
        capture = core.run_phase(state, generate, bound["dependencies"], binding=identity)
        require(not infra_failures and len(calls) == len(responses), "native fault/incomplete callbacks cannot be ordinary refusals")
        core.replay_validate(capture, bound["dependencies"])
        memory.write(directory / "capture.json", capture)
        memory.write(directory / "core_calls.json", calls)
    except BaseException as error:
        memory.failure(directory / "capture_failure.json", error)
        raise
    finally:
        if backend is not None:
            try:
                backend.close()
            except BaseException as error:
                memory.failure(directory / "backend_close_failure.json", error)
                raise
    ended = time.monotonic()
    require(identity_for(plan, arm, bound) == identity, "original parent changed during capture")
    names = {"identity.json", "capture.json", "core_calls.json"} | {f"{index:02d}" + suffix for index in range(len(calls)) for suffix in (".request.json", ".response.json")}
    memory.write(directory / "closed.json", dict(arm=arm, state=state, calls=len(calls), fits=0, updates=0, parent_model_calls=0,
                 files={name: digest(directory / name) for name in sorted(names)}, adapter_files_after=formation.tree(route["path"]),
                 started_monotonic=started, ended_monotonic=ended, kind_counts=dict(Counter(call["request"]["kind"] for call in calls)),
                 prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses),
                 output_tokens=sum(len(response["output_token_ids"]) for response in responses),
                 generation_seconds=sum(response["ended"] - response["started"] for response in responses)))


def replay_arm(plan, bound, arm, tokenizer):
    memory, core = bound["memory"], bound["core"]
    directory = Path(plan["root"]) / "run" / arm
    capture, calls, closed = (memory.read(directory / name) for name in ("capture.json", "core_calls.json", "closed.json"))
    identity = identity_for(plan, arm, bound)
    route, state = identity["route"], identity["state"]
    require(memory.read(directory / "identity.json") == identity and closed["arm"] == arm and closed["state"] == state and
            closed["calls"] == len(calls) <= CALL_CAPS[arm] and closed["fits"] == closed["updates"] == closed["parent_model_calls"] == 0 and
            closed["adapter_files_after"] == identity["producer"]["adapter_files"], "closed identity/parent/cost differs")
    names = {"identity.json", "capture.json", "core_calls.json"} | {f"{index:02d}" + suffix for index in range(len(calls)) for suffix in (".request.json", ".response.json")}
    require(closed["files"] == {name: digest(directory / name) for name in sorted(names)}, "closed raw inventory differs")
    for suffix in (".request.json", ".response.json"):
        require({path.name for path in directory.glob("*" + suffix)} == {f"{index:02d}" + suffix for index in range(len(calls))}, "raw callback inventory differs")
    require(all(type(closed[key]) in (int, float) and math.isfinite(closed[key]) for key in ("started_monotonic", "ended_monotonic")) and
            0 <= closed["started_monotonic"] <= closed["ended_monotonic"], "capture timing differs")
    responses, cursor, request_ids = [], [0], set()
    def replay(request):
        index = cursor[0]
        require(index < len(calls) and calls[index]["request"] == request and request["state"] == state and
                request["request_id"] not in request_ids, "dynamic core request/source/state/chronology differs")
        request_ids.add(request["request_id"])
        params = params_for(plan, core, request)
        native = bound["probe"].render(tokenizer, request["input_messages"])
        require(len(native["prompt_token_ids"]) + params["max_tokens"] <= plan["engine"]["max_model_len"], "replayed context overflow")
        expected = dict(call_id=f"{index:02d}", core_request=request, messages=request["input_messages"], native=native, params=params, lora_request=route)
        saved = memory.read(directory / (expected["call_id"] + ".request.json"))
        response = memory.read(directory / (expected["call_id"] + ".response.json"))
        require(saved == expected, "native dynamic prompt/token/route differs")
        bound["formation"].validate_response(saved, response, route)
        require(closed["started_monotonic"] <= response["started"] <= response["ended"] <= closed["ended_monotonic"] and
                (not responses or responses[-1]["ended"] <= response["started"]), "actual callback timing/ordering differs")
        raw = dict(request_id=request["request_id"], state=state, raw=response["text"], finish_reason=response["finish_reason"])
        require(raw == calls[index]["response"], "raw child response/source join differs")
        responses.append(response)
        cursor[0] += 1
        return raw
    audit = core.replay_validate(capture, bound["dependencies"])
    regenerated = core.run_phase(state, replay, bound["dependencies"], binding=identity)
    require(cursor[0] == len(calls) and memory.encoded(regenerated) == memory.encoded(capture), "complete all-task/failure/world replay differs")
    expected_costs = dict(kind_counts=dict(Counter(call["request"]["kind"] for call in calls)),
                          prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses),
                          output_tokens=sum(len(response["output_token_ids"]) for response in responses),
                          generation_seconds=sum(response["ended"] - response["started"] for response in responses))
    require(all(closed[key] == value for key, value in expected_costs.items()), "actual token/time/kind costs differ")
    return capture, audit, {key: closed[key] for key in ("calls", "fits", "updates", "parent_model_calls", *expected_costs)}


def worker(root, plan_sha256, arm, allow_gpu=False):
    require(allow_gpu is True and arm in ARMS, "explicit inference worker required")
    memory = runtime()
    memory.offline()
    directory = Path(root) / "run" / arm
    try:
        plan, bound = verify(root, plan_sha256, native=True)
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(), "worker allocation/isolation differs")
        allocation(plan)
        memory.write(directory / "started.json", dict(arm=arm, plan_sha256=plan_sha256, pid=os.getpid(), pgid=os.getpgrp(),
                     time=time.time(), monotonic=time.monotonic()))
        capture_arm(plan, bound, arm)
        memory.write(directory / "worker_done.json", dict(arm=arm, plan_sha256=plan_sha256, monotonic=time.monotonic()))
    except BaseException as error:
        memory.failure(directory / "failure.json", error)
        raise


def run_arm(plan, bound, plan_sha256, arm, deadline):
    require(arm in ARMS, "unknown stage")
    memory, probe = bound["memory"], bound["probe"]
    allocation(plan)
    require(deadline - time.monotonic() > QUERY_SECONDS + CLEANUP_SECONDS and probe.gpu_state(plan) is True, "fresh GPU vacancy/budget precheck failed")
    directory = Path(plan["root"]) / "run" / arm
    directory.mkdir()
    process, identity = None, None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                       "--arm", arm, "--allow-gpu"]
            launched, monotonic = time.time(), time.monotonic()
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            identity = memory.identity(process.pid)
            require(identity["pgid"] == process.pid, "fresh process group required")
            memory.write(directory / "launch.json", dict(identity=identity, arm=arm, plan_sha256=plan_sha256, command=command,
                         time=launched, monotonic=monotonic))
            code = process.wait(timeout=max(.01, deadline - time.monotonic() - CLEANUP_SECONDS - QUERY_SECONDS))
            memory.write(directory / "exit.json", dict(identity=identity, returncode=code, monotonic=time.monotonic()))
            require(code == 0, "alignment worker failed")
    except BaseException as error:
        memory.failure(directory / "stage_failure.json", error)
        raise
    finally:
        if process is not None:
            try:
                require(identity is not None, "missing owned process identity")
                memory.cleanup_owned(process, identity, probe)
                require(probe.gpu_state(plan) is True and time.monotonic() < deadline, "owned release/GPU vacancy/budget failed")
                memory.write(directory / "released.json", dict(identity=identity, arm=arm, group_absent=True, gpu_vacant=True,
                             time=time.time(), monotonic=time.monotonic()))
            except BaseException as error:
                memory.failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, bound, plan_sha256, tokenizer):
    memory = bound["memory"]
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists() and {path.name for path in (root / "run").iterdir()} == set(ARMS), "successful three-arm inventory required")
    controller_started = memory.read(root / "controller_started.json")
    entry, deadline = controller_started["monotonic"], controller_started["deadline"]
    require(controller_started["plan_sha256"] == plan_sha256 and controller_started["seconds"] == SECONDS and
            all(type(value) in (int, float) and math.isfinite(value) for value in (entry, deadline)) and
            0 <= entry and deadline == entry + SECONDS, "controller entry/deadline receipt differs")
    require(preflight(bound, tokenizer) == memory.read(root / "preflight.json"), "collection tokenizer/preflight differs")
    inventory, captures, audits, costs, identities, previous_release = {}, [], {}, {}, [], entry
    for arm in ARMS:
        directory = root / "run" / arm
        require(not any(directory.glob("*failure.json")), "failed inference state cannot collect")
        launch, started, done, exit_receipt, released, closed = (memory.read(directory / name) for name in
            ("launch.json", "started.json", "worker_done.json", "exit.json", "released.json", "closed.json"))
        identity = launch["identity"]
        command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--arm", arm, "--allow-gpu"]
        require(identity == exit_receipt["identity"] == released["identity"] and identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and
                type(identity["start_ticks"]) is int and identity["start_ticks"] > 0 and launch["command"] == command and
                launch["arm"] == started["arm"] == done["arm"] == released["arm"] == arm and
                launch["plan_sha256"] == started["plan_sha256"] == done["plan_sha256"] == plan_sha256 and
                type(exit_receipt["returncode"]) is int and exit_receipt["returncode"] == 0 and
                released["group_absent"] is True and released["gpu_vacant"] is True, "native process/exit/release custody differs")
        times = [previous_release, launch["monotonic"], started["monotonic"], closed["started_monotonic"], closed["ended_monotonic"],
                 done["monotonic"], exit_receipt["monotonic"], released["monotonic"]]
        require(all(type(value) in (int, float) and math.isfinite(value) for value in times) and times == sorted(times) and
                launch["time"] <= started["time"] <= released["time"] and released["monotonic"] < deadline, "cold stage chronology differs")
        previous_release = released["monotonic"]
        identities.append((identity["pid"], identity["start_ticks"]))
        capture, audit, cost = replay_arm(plan, bound, arm, tokenizer)
        captures.append(capture)
        audits[arm], costs[arm] = audit, cost
        inventory[arm] = bound["formation"].tree(directory)
    require(len(set(identities)) == 3 and sum(cost["calls"] for cost in costs.values()) <= 104, "fresh states/call ceiling differs")
    return dict(inventory=inventory, captures=captures, audits=audits, costs=costs, release_elapsed=previous_release - entry)


def controller(root, plan_sha256, allow_gpu=False):
    entry = time.monotonic()
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only controller with empty CVD required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    try:
        with memory.budget(entry + SECONDS - time.monotonic()):
            deadline = entry + SECONDS
            plan, bound = verify(root, plan_sha256, native=True)
            allocation(plan)
            memory.write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), monotonic=entry, deadline=deadline, seconds=SECONDS))
            (root / "run").mkdir()
            for arm in ARMS:
                run_arm(plan, bound, plan_sha256, arm, deadline)
            tokenizer = bound["probe"].native_tokenizer(plan["model"])
            checked = validate_completed(plan, bound, plan_sha256, tokenizer)
            require(time.monotonic() < deadline, "whole controller cap exceeded")
            memory.write(root / "capture_complete.json", dict(scope=SCOPE, plan_sha256=plan_sha256, stages=checked["inventory"],
                         calls=sum(cost["calls"] for cost in checked["costs"].values()), fits=0, updates=0, parent_model_calls=0,
                         collected=False, elapsed_seconds=SECONDS - (deadline - time.monotonic())))
            return dict(status="ALIGNMENT_COMPLETE_NOT_COLLECTED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    entry = time.monotonic()
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(entry + COLLECTION_SECONDS - time.monotonic()):
        plan, bound = verify(root, plan_sha256)
        require(digest(root / "capture_complete.json") == completion_sha256, "completed capture pin differs")
        complete = memory.read(root / "capture_complete.json")
        tokenizer = bound["probe"].native_tokenizer(plan["model"])
        checked = validate_completed(plan, bound, plan_sha256, tokenizer)
        require(complete["scope"] == SCOPE and complete["plan_sha256"] == plan_sha256 and complete["stages"] == checked["inventory"] and
                complete["calls"] == sum(cost["calls"] for cost in checked["costs"].values()) and complete["fits"] == complete["updates"] == complete["parent_model_calls"] == 0 and
                complete["collected"] is False and type(complete["elapsed_seconds"]) in (int, float) and
                checked["release_elapsed"] <= complete["elapsed_seconds"] <= SECONDS,
                "complete custody/cost/budget differs")
        out = memory.new_external(out, [root, *protected(plan["specification"], bound)])
        memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            memory.write(out / "collection_started.json", dict(entry_monotonic=entry, seconds=COLLECTION_SECONDS))
            summary = bound["core"].summarize(checked["captures"], bound["dependencies"])
            report = dict(scope=SCOPE, claim=CLAIM, seed=plan["seed"], plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          source_bindings=plan["specification"], original_parent=plan["producers"][str(plan["seed"])], manifest_sha256=plan["input_hashes"]["manifest.json"],
                          captures=checked["captures"], replay_audits=checked["audits"], costs_per_arm=checked["costs"], summary=summary,
                          costs={key: sum(cost[key] for cost in checked["costs"].values()) for key in
                                 ("calls", "fits", "updates", "parent_model_calls", "prompt_tokens", "output_tokens", "generation_seconds")},
                          controller_seconds=complete["elapsed_seconds"], preflight=memory.read(root / "preflight.json"),
                          native_capture_custody_checked=True, automatic_pass=False, fit_authorized=False,
                          limitation="One seed is a partial three-root DEV vector; no SLEEP or promotion. Raw rejected outputs and uncalled slots remain in captures.")
            memory.write(out / "alignment_report.json", report)
            elapsed = time.monotonic() - entry
            require(elapsed <= COLLECTION_SECONDS, "collector entry budget exceeded")
            memory.write(out / "collection.json", dict(alignment_report_sha256=digest(out / "alignment_report.json"), completion_sha256=completion_sha256,
                                                       collection_seconds=elapsed))
            return dict(status="COLLECTED_INFERENCE_ONLY_ALIGNMENT", out=str(out), alignment_report_sha256=digest(out / "alignment_report.json"),
                        collection_seconds=elapsed)
        except BaseException as error:
            memory.failure(out / "collection_failure.json", error)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name != "collect":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--arm", choices=ARMS, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    options = vars(parser.parse_args(argv))
    name = options.pop("command")
    result = {"prepare": prepare, "worker": worker, "controller": controller, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
