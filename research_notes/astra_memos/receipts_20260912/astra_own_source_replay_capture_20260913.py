"""Three original parents, 72 TRAIN readouts, zero fits; Main owns native launch."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time


SELF = Path(__file__).resolve()
SCOPE = "astra_own_source_replay_capture_20260913_v1"
CORE_PIN = "f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a"
NATIVE_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
PUBLIC_PIN = "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
LIFECYCLE_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
PROTOCOL_PIN = "dba4390e07622022cc4610f426ce4b0ac73c379dda17798b3ae489ce40c1b17f"
SEEDS = (0, 1, 2)
CALLS_PER_SEED, MAX_CALLS, MAX_OUTPUT_TOKENS = 24, 72, 192
CONTROLLER_SECONDS, SEED_SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 3000, 900, 180, 180
CLEANUP_SECONDS, GPU_QUERY_SECONDS, LEASE_MARGIN = 40, 30, 21600
CLAIM = ("Observation-reading replay collection only: original perception parents read already-trained, externally curated TRAIN sources. "
         "Not novel TRY interaction or retention repair. Zero fits/updates/teacher calls; no adoption or scientific promotion.")


def lifecycle():
    import hashlib
    import importlib.util
    path = Path("/tmp/astra_real_record_memory_run_20260913.py")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == LIFECYCLE_PIN, "frozen lifecycle pin differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("own_replay_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_spec(spec, memory):
    require(set(spec) == {"runner_sha256", "core", "native", "public", "lifecycle", "archive", "source_root", "protocol",
                          "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed capture specification differs")
    require(spec["runner_sha256"] == memory.digest(SELF), "capture runner pin differs")
    for key, pin in (("core", CORE_PIN), ("native", NATIVE_PIN), ("public", PUBLIC_PIN), ("lifecycle", LIFECYCLE_PIN), ("protocol", PROTOCOL_PIN)):
        binding = spec[key]
        require(set(binding) == {"path", "sha256"} and Path(binding["path"]).is_absolute() and binding["sha256"] == pin and
                memory.digest(binding["path"]) == pin, "explicit frozen binding differs: " + key)
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] == 6 and type(spec["gpu_uuid"]) is str and
            spec["gpu_uuid"].startswith("GPU-"), "Main GPU6 allocation required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "boot/lease binding required")
    require(Path(spec["source_root"]).is_absolute() and set(spec["archive"]) == {"path", "sha256"} and
            Path(spec["archive"]["path"]).is_absolute(), "absolute frozen source/archive required")


def allocation(plan):
    spec = plan["specification"]
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "current boot identity differs")
    require(spec["lease_end"] > time.time() + CONTROLLER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour lease finish margin required")


def bind(spec, native=False):
    memory = lifecycle()
    validate_spec(spec, memory)
    memory = memory.load(spec["lifecycle"], "own_replay_lifecycle", LIFECYCLE_PIN)
    core = memory.load(spec["core"], "own_replay_core", CORE_PIN)
    runtime = memory.load(spec["native"], "own_replay_native", NATIVE_PIN)
    probe = memory.load(spec["public"], "own_replay_public", PUBLIC_PIN)
    require(spec["archive"]["sha256"] == core.ARCHIVE_PIN, "original archive binding differs")
    bundles = {str(seed): core.build(seed, archive_path=spec["archive"]["path"], source_root=spec["source_root"]) for seed in SEEDS}
    parents = {}
    with tarfile.open(spec["archive"]["path"], "r:") as archive:
        for seed in SEEDS:
            bundle = bundles[str(seed)]
            raw = archive.extractfile(bundle["provenance"]["plan_member"]).read()
            require(core.sha(raw) == core.PLAN_PINS[seed], "original archived parent plan differs")
            parents[str(seed)] = core.decode(raw)
    reference = parents["0"]
    for key, parent in parents.items():
        require(all(parent[field] == reference[field] for field in ("model", "model_files", "environment", "python", "python_sha256", "chat_template", "engine", "params")),
                "original inference/base/environment settings differ across parents")
        require(parent["engine"] == runtime.ENGINE and parent["params"] == probe.PARAMS and parent["params"]["temperature"] == 0.0 and
                parent["params"]["max_tokens"] == MAX_OUTPUT_TOKENS, "original inference settings differ")
        producer = bundles[key]["producer"]
        require(runtime.tree(producer["adapter"]) == producer["adapter_files"], "original live adapter bytes differ")
    if native:
        require(reference["python"] == os.path.abspath(sys.executable) and reference["python_sha256"] == memory.digest(sys.executable), "native interpreter differs")
        require(reference["environment"] == dict(probe=probe.native_environment(), peft=importlib.metadata.version("peft")), "native environment differs")
        require(probe.model_hashes(reference["model"]) == reference["model_files"], "frozen native base changed")
    return dict(memory=memory, core=core, runtime=runtime, probe=probe, bundles=bundles, parents=parents, reference=reference)


def protected(spec, bound):
    paths = [SELF, spec["source_root"], spec["archive"]["path"], bound["reference"]["model"],
             bound["core"].MATERIAL_PATH, bound["core"].RUNNER_PATH]
    paths += [spec[key]["path"] for key in ("core", "native", "public", "lifecycle", "protocol")]
    paths += [parent["root"] for parent in bound["parents"].values()]
    return paths


def make_calls(bundle, tokenizer, probe):
    require(len(bundle["requests"]) == CALLS_PER_SEED and bundle["source_population_denominator"] == 96, "fixed core denominator differs")
    return [dict(call_id=f"train_{index:02d}", core_request=request, messages=request["input_messages"],
                 native=probe.render(tokenizer, request["input_messages"])) for index, request in enumerate(bundle["requests"])]


def route_for(plan, seed, runtime):
    producer = plan["producers"][str(seed)]
    require(runtime.tree(producer["adapter"]) == producer["adapter_files"], "immutable original parent adapter changed")
    return dict(name="own_source_perception_seed" + str(seed), id=1, path=producer["adapter"])


def expected_plan(root, spec, spec_sha256, bound, inputs):
    original = bound["reference"]
    return dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=spec, spec_sha256=spec_sha256,
                self_sha256=bound["memory"].digest(SELF), source=spec["source_root"],
                **{key: original[key] for key in ("model", "model_files", "environment", "python", "python_sha256", "chat_template", "engine", "params")},
                producers={key: bundle["producer"] for key, bundle in bound["bundles"].items()}, seeds=list(SEEDS),
                gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"], input_hashes=inputs,
                limits=dict(controller=CONTROLLER_SECONDS, seed=SEED_SECONDS, collection=COLLECTION_SECONDS,
                            calls_per_seed=CALLS_PER_SEED, calls_total=MAX_CALLS, output_tokens=MAX_OUTPUT_TOKENS, fits=0, updates=0, teacher_calls=0))


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "explicit native CPU prepare with empty CVD required")
    memory = lifecycle()
    memory.offline()
    with memory.budget(PREPARE_SECONDS):
        require(memory.digest(spec_path) == spec_sha256, "specification pin differs")
        spec = memory.read(spec_path)
        bound = bind(spec, native=True)
        root = memory.new_external(root, [spec_path, *protected(spec, bound)])
        allocation(dict(specification=spec))
        root.mkdir()
        memory.write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
        try:
            tokenizer = bound["probe"].native_tokenizer(bound["reference"]["model"])
            require(tokenizer.chat_template == bound["reference"]["chat_template"], "original template differs")
            with (root / "spec.json").open("xb") as stream:
                stream.write(Path(spec_path).read_bytes())
            require(memory.digest(root / "spec.json") == spec_sha256, "copied specification changed")
            names = []
            for seed in SEEDS:
                for name, value in ((f"bundle_seed{seed}.json", bound["bundles"][str(seed)]),
                                     (f"calls_seed{seed}.json", make_calls(bound["bundles"][str(seed)], tokenizer, bound["probe"]))):
                    memory.write(root / name, value)
                    names.append(name)
            plan = expected_plan(root, spec, spec_sha256, bound, {name: memory.digest(root / name) for name in names})
            memory.write(root / "plan.json", plan)
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=memory.digest(root / "plan.json"),
                        calls=MAX_CALLS, calls_per_seed=CALLS_PER_SEED, fits=0, updates=0, teacher_calls=0)
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    memory = lifecycle()
    root = Path(root).absolute()
    require(memory.digest(root / "plan.json") == plan_sha256, "capture plan pin differs")
    plan = memory.read(root / "plan.json")
    require(memory.digest(root / "spec.json") == plan["spec_sha256"] and memory.read(root / "spec.json") == plan["specification"] and
            memory.read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and not (root / "prepare_failure.json").exists(),
            "preparation/spec identity differs")
    bound = bind(plan["specification"], native=native)
    names = {f"{kind}_seed{seed}.json" for kind in ("bundle", "calls") for seed in SEEDS}
    require(set(plan["input_hashes"]) == names and plan == expected_plan(root, plan["specification"], plan["spec_sha256"], bound, plan["input_hashes"]),
            "closed prepared plan differs")
    for name in names:
        require(memory.digest(root / name) == plan["input_hashes"][name], "prepared input changed: " + name)
    for seed in SEEDS:
        bundle = memory.read(root / f"bundle_seed{seed}.json")
        require(memory.encoded(bundle) == memory.encoded(bound["bundles"][str(seed)]), "fixed core TRAIN bundle differs")
        calls = memory.read(root / f"calls_seed{seed}.json")
        require(len(calls) == CALLS_PER_SEED and len({call["call_id"] for call in calls}) == CALLS_PER_SEED, "24unique calls required")
        for index, (call, request) in enumerate(zip(calls, bundle["requests"])):
            require(set(call) == {"call_id", "core_request", "messages", "native"} and call["call_id"] == f"train_{index:02d}" and
                    call["core_request"] == request and call["messages"] == request["input_messages"], "TRAIN request/source join differs")
    return plan, bound


def capture_seed(plan, seed, bound, backend_factory=None):
    memory, runtime, probe = (bound[key] for key in ("memory", "runtime", "probe"))
    directory = Path(plan["root"]) / "run" / f"seed{seed}"
    bundle = bound["bundles"][str(seed)]
    calls = memory.read(Path(plan["root"]) / f"calls_seed{seed}.json")
    route = route_for(plan, seed, runtime)
    identity = dict(scope=SCOPE, seed=seed, producer=bundle["producer"], producer_sha256=bundle["producer_sha256"],
                    lora_request=route, model_files=plan["model_files"], engine=plan["engine"], params=plan["params"])
    memory.write(directory / "identity.json", identity)
    backend, responses = None, []
    try:
        backend = (backend_factory or runtime.Native)(plan, probe, route)
        require(backend.tokenizer.chat_template == plan["chat_template"] and
                calls == make_calls(bundle, backend.tokenizer, probe), "actual cold native prompt/token drift")
        for call in calls:
            request = dict(call, params=plan["params"], lora_request=route)
            memory.write(directory / (call["call_id"] + ".request.json"), request)
            response = backend.generate(request)
            memory.write(directory / (call["call_id"] + ".response.json"), response)
            runtime.validate_response(request, response, route)
            responses.append(response)
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
    require(route_for(plan, seed, runtime) == route, "original parent changed during readout")
    names = ["identity.json"] + [call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")]
    memory.write(directory / "closed.json", dict(seed=seed, calls=len(responses), fits=0, updates=0, teacher_calls=0,
        files={name: memory.digest(directory / name) for name in names}, adapter_files_after=runtime.tree(route["path"]),
        prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses),
        output_tokens=sum(len(response["output_token_ids"]) for response in responses),
        generation_seconds=sum(response["ended"] - response["started"] for response in responses)))


def worker(root, plan_sha256, seed, allow_gpu=False):
    require(allow_gpu is True and type(seed) is int and seed in SEEDS, "explicit isolated seed worker required")
    memory = lifecycle()
    memory.offline()
    directory = Path(root) / "run" / f"seed{seed}"
    try:
        with memory.budget(SEED_SECONDS - CLEANUP_SECONDS):
            plan, bound = verify(root, plan_sha256, native=True)
            require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(), "worker route/process isolation differs")
            allocation(plan)
            memory.write(directory / "started.json", dict(seed=seed, plan_sha256=plan_sha256, pid=os.getpid(), pgid=os.getpgrp(), time=time.time()))
            capture_seed(plan, seed, bound)
    except BaseException as error:
        memory.failure(directory / "failure.json", error)
        raise


def run_seed(plan, plan_sha256, seed, deadline, bound):
    memory, probe = bound["memory"], bound["probe"]
    started = time.monotonic()
    stage_deadline = min(deadline, started + SEED_SECONDS)
    allocation(plan)
    require(stage_deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS and probe.gpu_state(plan) is True,
            "fresh assigned GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / f"seed{seed}"
    directory.mkdir()
    process, expected = None, None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                       "--seed", str(seed), "--allow-gpu"]
            launched_at = time.time()
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            expected = memory.identity(process.pid)
            require(expected["pgid"] == process.pid, "fresh worker process group differs")
            memory.write(directory / "launch.json", dict(identity=expected, seed=seed, plan_sha256=plan_sha256, command=command, started=launched_at))
            require(process.wait(timeout=max(.01, stage_deadline - time.monotonic() - CLEANUP_SECONDS)) == 0, "native child readout failed")
    except BaseException as error:
        memory.failure(directory / "stage_failure.json", error)
        raise
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity")
                memory.cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True and time.monotonic() < stage_deadline, "owned release/budget failed")
                memory.write(directory / "released.json", dict(identity=expected, seed=seed, ended=time.time(), elapsed_seconds=time.monotonic() - started))
            except BaseException as error:
                memory.failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, plan_sha256, bound):
    memory, runtime = bound["memory"], bound["runtime"]
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists() and {path.name for path in (root / "run").iterdir()} == {f"seed{seed}" for seed in SEEDS},
            "successful three-readout stage inventory required")
    inventories, pids, previous_end = {}, [], None
    for seed in SEEDS:
        directory = root / "run" / f"seed{seed}"
        require(not any(directory.glob("*failure.json")), "failed native stage cannot collect")
        launch, started, released, closed = (memory.read(directory / name) for name in ("launch.json", "started.json", "released.json", "closed.json"))
        expected = launch["identity"]
        command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--seed", str(seed), "--allow-gpu"]
        require(expected == released["identity"] and expected["pid"] == expected["pgid"] == started["pid"] == started["pgid"] and
                type(expected["start_ticks"]) is int and expected["start_ticks"] > 0 and launch["command"] == command and
                launch["seed"] == started["seed"] == released["seed"] == closed["seed"] == seed and
                launch["plan_sha256"] == started["plan_sha256"] == plan_sha256, "native process custody differs")
        require(all(type(value) in (int, float) and math.isfinite(value) for value in (launch["started"], started["time"], released["ended"], released["elapsed_seconds"])) and
                0 <= released["elapsed_seconds"] <= SEED_SECONDS and launch["started"] <= started["time"] <= released["ended"] and
                (previous_end is None or previous_end <= launch["started"]), "sequential stage chronology/budget differs")
        previous_end = released["ended"]
        pids.append(expected["pid"])
        producer = plan["producers"][str(seed)]
        route = route_for(plan, seed, runtime)
        require(memory.read(directory / "identity.json") == dict(scope=SCOPE, seed=seed, producer=producer,
                producer_sha256=bound["bundles"][str(seed)]["producer_sha256"], lora_request=route, model_files=plan["model_files"],
                engine=plan["engine"], params=plan["params"]), "captured original route identity differs")
        calls = memory.read(root / f"calls_seed{seed}.json")
        names = {"identity.json"} | {call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")}
        require(closed["calls"] == CALLS_PER_SEED and closed["fits"] == closed["updates"] == closed["teacher_calls"] == 0 and
                set(closed["files"]) == names and closed["adapter_files_after"] == producer["adapter_files"], "closed readout workload/adapter differs")
        for suffix in (".request.json", ".response.json"):
            require({path.name for path in directory.glob("*" + suffix)} == {call["call_id"] + suffix for call in calls}, "raw call inventory differs")
        for name, checksum in closed["files"].items():
            require(memory.digest(directory / name) == checksum, "closed capture file changed")
        responses = []
        for call in calls:
            request = memory.read(directory / (call["call_id"] + ".request.json"))
            response = memory.read(directory / (call["call_id"] + ".response.json"))
            require(request == dict(call, params=plan["params"], lora_request=route), "native request/prompt/source changed")
            runtime.validate_response(request, response, route)
            responses.append(response)
        require(closed["prompt_tokens"] == sum(len(response["actual_prompt_token_ids"]) for response in responses) and
                closed["output_tokens"] == sum(len(response["output_token_ids"]) for response in responses) and
                closed["generation_seconds"] == sum(response["ended"] - response["started"] for response in responses), "native token/time cost differs")
        inventories[str(seed)] = runtime.tree(directory)
    require(len(set(pids)) == 3, "three fresh child processes required")
    return inventories


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only controller with empty CVD required")
    memory = lifecycle()
    memory.offline()
    root = Path(root).absolute()
    try:
        with memory.budget(CONTROLLER_SECONDS):
            deadline = time.monotonic() + CONTROLLER_SECONDS
            plan, bound = verify(root, plan_sha256, native=True)
            allocation(plan)
            memory.write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), time=time.time(), seconds=CONTROLLER_SECONDS))
            (root / "run").mkdir()
            for seed in SEEDS:
                run_seed(plan, plan_sha256, seed, deadline, bound)
            inventory = validate_completed(plan, plan_sha256, bound)
            require(time.monotonic() < deadline, "whole capture cap exceeded")
            memory.write(root / "capture_complete.json", dict(scope=SCOPE, plan_sha256=plan_sha256, stages=inventory, calls=MAX_CALLS,
                fits=0, updates=0, teacher_calls=0, admitted=False, elapsed_seconds=CONTROLLER_SECONDS - (deadline - time.monotonic())))
            return dict(status="REPLAY_CAPTURE_COMPLETE_NOT_ADMITTED", completion_sha256=memory.digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def admission_counts(report):
    field_errors = {"record triple types", "action mismatch", "outcome mismatch", "prediction type", "prediction mismatch", "relation mismatch"}
    failures = Counter(error for audit in report["responses"] for error in (audit["source_judge"] or {}).get("failures", []))
    return dict(opportunities=24, source_population=96, admitted=report["admitted_count"], rejected=len(report["rejected"]),
                missing=len(report["missing_request_ids"]), finishes=dict(Counter(audit["response"]["finish_reason"] for audit in report["responses"])),
                field_first_failure_counts={key: value for key, value in failures.items() if key in field_errors},
                syntax_schema_or_source_first_failure_counts={key: value for key, value in failures.items() if key not in field_errors},
                completion_failure_count=sum("stop_completion_required" in audit["errors"] for audit in report["responses"]),
                diagnostic_limit="Unchanged production judge stops at its first error; these are not exhaustive per-field accuracy scores.")


def collect(root, plan_sha256, completion_sha256, out):
    memory = lifecycle()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(COLLECTION_SECONDS):
        plan, bound = verify(root, plan_sha256)
        require(memory.digest(root / "capture_complete.json") == completion_sha256, "capture completion pin differs")
        complete = memory.read(root / "capture_complete.json")
        require(complete["scope"] == SCOPE and complete["plan_sha256"] == plan_sha256 and complete["calls"] == MAX_CALLS and
                complete["fits"] == complete["updates"] == complete["teacher_calls"] == 0 and complete["admitted"] is False and
                type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= CONTROLLER_SECONDS and
                complete["stages"] == validate_completed(plan, plan_sha256, bound), "completed capture custody differs")
        out = memory.new_external(out, [root, *protected(plan["specification"], bound)])
        memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            reports, costs, joins = {}, {}, {}
            for seed in SEEDS:
                directory = root / "run" / f"seed{seed}"
                responses, joins[str(seed)] = [], []
                for call in memory.read(root / f"calls_seed{seed}.json"):
                    request = call["core_request"]
                    response_path = directory / (call["call_id"] + ".response.json")
                    response = memory.read(response_path)
                    raw = dict(request_id=request["request_id"], input_sha256=request["input_sha256"], producer_sha256=request["producer_sha256"],
                               raw=response["text"], finish_reason=response["finish_reason"])
                    responses.append(raw)
                    joins[str(seed)].append(dict(request_id=request["request_id"], call_id=call["call_id"],
                        native_request_sha256=memory.digest(directory / (call["call_id"] + ".request.json")),
                        native_response_sha256=memory.digest(response_path), core_response_sha256=bound["core"].sha(bound["core"].encoded(raw))))
                report = bound["core"].admit(bound["bundles"][str(seed)], responses)
                require(report["submitted"] == report["requested_denominator"] == CALLS_PER_SEED and not report["missing_request_ids"], "all24 source opportunities required")
                reports[str(seed)] = report
                costs[str(seed)] = memory.read(directory / "closed.json")
                memory.write(out / f"seed{seed}_admission.json", report)
            summary = dict(scope=SCOPE, claim=CLAIM, plan_sha256=plan_sha256, completion_sha256=completion_sha256, protocol=plan["specification"]["protocol"],
                source_pins={key: plan["specification"][key] for key in ("core", "native", "public", "lifecycle", "archive")},
                seed_reports={key: dict(path=f"seed{key}_admission.json", sha256=memory.digest(out / f"seed{key}_admission.json")) for key in reports},
                counts={key: admission_counts(report) for key, report in reports.items()}, native_source_joins=joins,
                costs_per_seed={key: {field: cost[field] for field in ("calls", "fits", "updates", "teacher_calls", "prompt_tokens", "output_tokens", "generation_seconds")}
                                for key, cost in costs.items()},
                costs=dict(calls=MAX_CALLS, fits=0, updates=0, teacher_calls=0,
                           prompt_tokens=sum(cost["prompt_tokens"] for cost in costs.values()), output_tokens=sum(cost["output_tokens"] for cost in costs.values()),
                           generation_seconds=sum(cost["generation_seconds"] for cost in costs.values()), controller_seconds=complete["elapsed_seconds"]),
                native_capture_receipts_checked=True, core_native_identity_verified=False, automatic_pass=False, fit_decision=None,
                limitation="Stored own-source observation reading on already-trained TRAIN situations; no new TRY, fit, adoption or retention-repair conclusion.")
            memory.write(out / "replay_report.json", summary)
            memory.write(out / "collection.json", dict(replay_report_sha256=memory.digest(out / "replay_report.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_OWN_SOURCE_REPLAY_CANDIDATES", out=str(out), replay_report_sha256=memory.digest(out / "replay_report.json"),
                        counts=summary["counts"], fits=0, updates=0)
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
            command.add_argument("--seed", type=int, choices=SEEDS, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    options = vars(parser.parse_args(argv))
    name = options.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
