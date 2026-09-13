"""Single-seed cold WRITE/LR0 interaction diagnostic; Main owns native execution."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
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
SCOPE = "astra_post_memory_formation_run_20260913_v1"
MEMORY_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
FORMATION_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
CORE_PIN = "030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b"
STATES = ("WRITE", "LR0")
OUTER_SECONDS, STATE_SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 1800, 900, 180, 180
CLEANUP_SECONDS, GPU_QUERY_SECONDS, LEASE_MARGIN = 40, 30, 21600
CALLS_PER_STATE, MAX_CALLS = 32, 64
TOKENS = {"wake": 96, "record": 192}
CLAIM = ("Prospective post-memory interactive formation diagnostic only. All engineering-valid pairs are eligible "
         "regardless of recall gains or harm; no outcome selection, fits, updates, parent calls, automatic promotion, "
         "recursive learning or H1/H2 claim. Same initial tasks do not imply identical realized experience.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


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
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    path = Path(path)
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "output symlink")
    with path.open("xb") as stream:
        stream.write(encoded(value))


def failure(path, error):
    if not Path(path).exists():
        write(path, dict(error_type=type(error).__name__, error=str(error), retry=False, time=time.time()))


def pin(value):
    require(type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value), "SHA256 required")


def absolute(path):
    require(type(path) is str and Path(path).is_absolute() and ".." not in Path(path).parts and
            not any(part.is_symlink() for part in (Path(path), *Path(path).parents)), "absolute nonsymlink path required")
    return Path(path)


def pinned(record, expected=None):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "explicit file binding required")
    absolute(record["path"])
    pin(record["sha256"])
    require((expected is None or record["sha256"] == expected) and digest(record["path"]) == record["sha256"], "file pin differs")


def load(record, name, expected=None):
    pinned(record, expected)
    specification = importlib.util.spec_from_file_location("post_memory_" + name, record["path"])
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def offline():
    sys.dont_write_bytecode = True
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1", DO_NOT_TRACK="1",
                      VLLM_WORKER_MULTIPROC_METHOD="spawn", PYTHONDONTWRITEBYTECODE="1")


@contextlib.contextmanager
def budget(seconds):
    require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0, "runtime budget exhausted")
    def expired(signum, frame):
        raise TimeoutError("post-memory runner deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def fresh(path, protected):
    path = absolute(str(path))
    require(not path.exists(), "fresh output required; no resume/retry")
    for other in protected:
        other = Path(other).resolve()
        require(path != other and path not in other.parents and other not in path.parents, "output overlaps protected input")
    return path


def validate_spec(spec):
    require(type(spec) is dict and set(spec) == {"runner_sha256", "core", "memory_runtime", "memory", "seed", "node",
                                                "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed specification differs")
    require(spec["runner_sha256"] == digest(SELF), "runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2), "learner seed0/1/2 required")
    require(spec["node"] == "node2", "explicit node2 route required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and type(spec["gpu_uuid"]) is str and
            spec["gpu_uuid"].startswith("GPU-"), "GPU UUID/index required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "finite boot/lease binding required")
    upstream = spec["memory"]
    require(type(upstream) is dict and set(upstream) == {"root", "plan_sha256", "completion_sha256", "collection", "scores"},
            "completed memory binding differs")
    absolute(upstream["root"])
    pin(upstream["plan_sha256"])
    pin(upstream["completion_sha256"])
    pinned(spec["memory_runtime"], MEMORY_PIN)
    pinned(spec["core"], CORE_PIN)


def check_allocation(plan):
    spec = plan["specification"]
    require(spec["node"] == "node2" and Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"],
            "bound node2 boot differs")
    require(spec["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour lease finish margin required")


def absent(expected, probe=None):
    require(type(expected["pid"]) is int and expected["pid"] > 1, "invalid process identity")
    try:
        identity(expected["pid"])
    except FileNotFoundError:
        pass
    else:
        raise ValueError("recorded process PID still exists; no collection/reuse")
    if probe is not None:
        require(not probe.group_alive(expected["pgid"]), "owned process group still live")


def bind_inputs(spec, native=False):
    validate_spec(spec)
    memory = load(spec["memory_runtime"], "memory", MEMORY_PIN)
    upstream = spec["memory"]
    root = Path(upstream["root"])
    plan, bound = memory.verify(root, upstream["plan_sha256"], native=native)
    require(plan["specification"]["seed"] == plan["specification"]["fit_seed"] == spec["seed"] and
            plan["status"] == "WRITE_AVAILABLE" and plan["stages"] == list(memory.STAGES), "engineering-valid same-seed pair required")
    require(digest(root / "capture_complete.json") == upstream["completion_sha256"], "memory completion pin differs")
    complete = read(root / "capture_complete.json")
    inventory = memory.validate_completed(plan, upstream["plan_sha256"], bound)
    elapsed = complete["elapsed_seconds"]
    require(complete["plan_sha256"] == upstream["plan_sha256"] and complete["stages"] == inventory and
            complete["scored"] is False and complete["status"] == plan["status"] and
            type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= memory.OUTER_SECONDS and
            type(complete["calls"]) is int and complete["calls"] == 2 * plan["calls_per_arm"] and
            type(complete["updates"]) is int and complete["updates"] == 2 * plan["updates_per_arm"], "memory completed custody differs")
    for name in ("collection", "scores"):
        pinned(upstream[name])
    collection_path, scores_path = (Path(upstream[name]["path"]) for name in ("collection", "scores"))
    require(collection_path.name == "collection.json" and scores_path == collection_path.parent / "scores.json" and
            not (collection_path.parent / "collection_failure.json").exists(), "successful original collection required")
    collected, scores = read(collection_path), read(scores_path)
    require(collected == dict(scores_sha256=upstream["scores"]["sha256"], completion_sha256=upstream["completion_sha256"]) and
            scores["plan_sha256"] == upstream["plan_sha256"] and scores["completion_sha256"] == upstream["completion_sha256"] and
            type(scores["seed"]) is int and scores["seed"] == spec["seed"] and scores["status"] == plan["status"] and
            scores["native_capture_custody_checked"] is True and scores["automatic_pass"] is False and
            scores["calls"] == complete["calls"] and scores["updates"] == complete["updates"], "memory collection/scores identity differs")
    require(read(root.with_name(root.name + ".collection_claim.json")) ==
            dict(plan_sha256=upstream["plan_sha256"], out=str(collection_path.parent), retry=False), "memory once-only claim differs")
    absent(dict(pid=read(root / "controller_started.json")["pid"]))
    for stage in plan["stages"]:
        absent(read(root / "run" / stage / "launch.json")["identity"], bound["probe"])
    formation = bound["formation"]
    require(digest(formation.__file__) == FORMATION_PIN, "original native formation runtime differs")
    routes = {state: memory.route_for(plan, bound, state) for state in STATES}
    require(routes["WRITE"]["path"] != routes["LR0"]["path"], "paired adapter routes must be disjoint")
    adapters = {state: formation.tree(routes[state]["path"]) for state in STATES}
    core = load(spec["core"], "core", CORE_PIN)
    dependencies = core.load_dependencies(plan["source"])
    contract = core.contract(dependencies)
    require(contract["schema"] == "astra_post_memory_formation_20260913_v1" and
            contract["possible_records_per_state"] == 16 and contract["maximum_calls_per_state"] == CALLS_PER_STATE and
            contract["max_output_tokens"] == TOKENS and contract["new_fits"] == contract["parent_calls"] == 0 and
            contract["outcome_gate"] is None and contract["gain_or_canary_harm_is_gate"] is False and
            len(contract["episode_ids"]) == len(set(contract["episode_ids"])) == 8 and
            all(core_state(spec["seed"], state) in contract["states"] for state in STATES), "core workload/interface differs")
    prior_ids = [episode["episode_id"] for episode in bound["capture"]["episodes"]]
    disjointness = core.check_disjointness(prior_ids)
    return dict(memory=memory, memory_plan=plan, memory_bound=bound, formation=formation, probe=bound["probe"],
                core=core, dependencies=dependencies, contract=contract, routes=routes, adapters=adapters, disjointness=disjointness)


def protected_inputs(spec, bound):
    return [SELF, spec["core"]["path"], spec["memory_runtime"]["path"], spec["memory"]["root"],
            Path(spec["memory"]["collection"]["path"]).parent,
            *bound["memory"].protected_inputs(bound["memory_plan"]["specification"], bound["memory_bound"])]


def limits():
    return dict(controller=OUTER_SECONDS, state=STATE_SECONDS, collection=COLLECTION_SECONDS, prepare=PREPARE_SECONDS,
                cleanup_reserve=CLEANUP_SECONDS, gpu_query=GPU_QUERY_SECONDS, calls_per_state=CALLS_PER_STATE,
                calls_total=MAX_CALLS, output_tokens=TOKENS, fits=0, updates=0)


def core_state(seed, state):
    return f"perception_seed{seed}_{state}"


def initial_prompts(bound, tokenizer):
    contract = bound["contract"]
    initial = []
    for case in contract["schedule"]:
        prompt = contract["wake_templates"][case["cue_stratum"]].format(
            eid=case["episode_id"], tick=1, earlier_transcript=contract["first_history"])
        messages = [dict(role="user", content=prompt)]
        native = bound["probe"].render(tokenizer, messages)
        require(len(native["prompt_token_ids"]) + TOKENS["wake"] <= bound["formation"].ENGINE["max_model_len"],
                "initial wake context exceeds cap")
        initial.append(dict(case=case, messages=messages, native=native))
    return initial


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "Main-only --allow-native required")
    offline()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "CPU prepare must not reserve CUDA")
    with budget(PREPARE_SECONDS):
        require(digest(spec_path) == spec_sha256, "spec hash differs")
        spec = read(spec_path)
        bound = bind_inputs(spec, native=True)
        root = fresh(root, [spec_path, *protected_inputs(spec, bound)])
        check_allocation(dict(specification=spec))
        root.mkdir()
        write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
        try:
            with (root / "specification.json").open("xb") as stream:
                stream.write(Path(spec_path).read_bytes())
            require(digest(root / "specification.json") == spec_sha256, "spec changed during prepare")
            upstream = bound["memory_plan"]
            tokenizer = bound["probe"].native_tokenizer(upstream["model"])
            require(tokenizer.chat_template == upstream["chat_template"], "prepared tokenizer template differs")
            write(root / "initial_prompts.json", initial_prompts(bound, tokenizer))
            plan = dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=spec, spec_sha256=spec_sha256,
                        self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                        states=list(STATES), seed=spec["seed"], core_contract=bound["contract"], disjointness=bound["disjointness"],
                        episode_ids=bound["contract"]["episode_ids"], routes=bound["routes"], adapters=bound["adapters"],
                        model=upstream["model"], model_files=upstream["model_files"], source=upstream["source"],
                        environment=upstream["environment"], chat_template=upstream["chat_template"],
                        engine=bound["formation"].ENGINE, params=bound["formation"].PARAMS,
                        gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"], lease_end=spec["lease_end"],
                        initial_prompts_sha256=digest(root / "initial_prompts.json"), limits=limits())
            write(root / "plan.json", plan)
            return dict(status="POST_MEMORY_NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"),
                        limits=limits(), all_three_pairs_prerequisite="Main verifies cohort; this runner verifies one pair", outcome_gate=None)
        except BaseException as error:
            failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    root = absolute(str(root))
    require(digest(root / "plan.json") == plan_sha256, "formation plan pin differs")
    plan = read(root / "plan.json")
    require(plan["scope"] == SCOPE and plan["claim"] == CLAIM and plan["root"] == str(root) and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "runtime/interpreter identity differs")
    require(not (root / "prepare_failure.json").exists() and not (root / "controller_failure.json").exists() and
            read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "preparation/controller failure or spec drift")
    require(digest(root / "specification.json") == plan["spec_sha256"] and
            read(root / "specification.json") == plan["specification"], "saved specification bytes differ")
    bound = bind_inputs(plan["specification"], native=native)
    upstream = bound["memory_plan"]
    require(all(plan[key] == upstream[key] for key in ("model", "model_files", "source", "environment", "chat_template")),
            "upstream model/source/environment drift")
    require(all(plan[key] == plan["specification"][key] for key in ("seed", "gpu_index", "gpu_uuid", "lease_end")) and
            plan["states"] == list(STATES) and plan["core_contract"] == bound["contract"] and
            plan["disjointness"] == bound["disjointness"] and plan["episode_ids"] == bound["contract"]["episode_ids"] and
            plan["routes"] == bound["routes"] and plan["adapters"] == bound["adapters"] and
            plan["engine"] == bound["formation"].ENGINE and plan["params"] == bound["formation"].PARAMS and
            plan["limits"] == limits(), "explicit plan/spec/core/config agreement differs")
    require(digest(root / "initial_prompts.json") == plan["initial_prompts_sha256"], "prepared prompts changed")
    return plan, bound


def identity(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, pgid=int(fields[2]), start_ticks=int(fields[19]))


def current_route(plan, bound, state):
    require(state in STATES, "unknown paired state")
    route = bound["memory"].route_for(bound["memory_plan"], bound["memory_bound"], state)
    require(route == plan["routes"][state] and bound["formation"].tree(route["path"]) == plan["adapters"][state],
            "saved adapter route/inventory changed")
    return route


class NativeCaptureFailure(BaseException):
    """Infrastructure failure must escape the scientific core's refusal handling."""


def state_identity(plan, bound, state):
    return dict(state=state, core_state=core_state(plan["seed"], state), seed=plan["seed"],
                memory=plan["specification"]["memory"], model=plan["model"], model_files=plan["model_files"],
                lora_request=current_route(plan, bound, state), adapter_files=plan["adapters"][state],
                core=plan["specification"]["core"], engine=plan["engine"], params=plan["params"])


def capture_state(plan, state, bound, backend_factory=None):
    directory = Path(plan["root"]) / "run" / state
    receipt = state_identity(plan, bound, state)
    route, core = receipt["lora_request"], bound["core"]
    requests, responses, backend = [], [], None
    write(directory / "identity.json", receipt)
    try:
        backend = (backend_factory or bound["formation"].Native)(plan, bound["probe"], route)
        require(backend.tokenizer.chat_template == plan["chat_template"] and
                initial_prompts(bound, backend.tokenizer) == read(Path(plan["root"]) / "initial_prompts.json"),
                "cold native initial prompt/template drift")
        def generate(core_request):
            try:
                kind = core_request["kind"]
                require(kind in TOKENS and core_request["state"] == receipt["core_state"] and
                        core_request["episode_id"] in plan["episode_ids"] and type(core_request["tick"]) is int and
                        core_request["tick"] in (1, 2), "core callback source identity differs")
                cap = TOKENS[kind]
                require(type(core_request["max_output_tokens"]) is int and core_request["max_output_tokens"] == cap,
                        "core callback output cap differs")
                require(len(requests) < CALLS_PER_STATE and not any(
                    (previous["core_request"]["episode_id"], previous["core_request"]["tick"], previous["core_request"]["kind"]) ==
                    (core_request["episode_id"], core_request["tick"], kind) for previous in requests), "extra/duplicate native call")
                messages = core_request["input_messages"]
                native = bound["probe"].render(backend.tokenizer, messages)
                require(len(native["prompt_token_ids"]) + cap <= plan["engine"]["max_model_len"], "dynamic context exceeds cap")
                request = dict(call_id=f"{len(requests):02d}", core_request=core_request, messages=messages,
                               native=native, params=dict(plan["params"], max_tokens=cap), lora_request=route)
                write(directory / (request["call_id"] + ".request.json"), request)
                requests.append(request)
                response = backend.generate(request)
                write(directory / (request["call_id"] + ".response.json"), response)
                bound["formation"].validate_response(request, response, route)
                responses.append(response)
                return dict(request_id=core_request["request_id"], state=receipt["core_state"], raw=response["text"],
                            finish_reason=response["finish_reason"], native_response=response)
            except Exception as error:
                raise NativeCaptureFailure(type(error).__name__ + ": " + str(error)) from error
        capture = core.run_state(receipt["core_state"], generate, dependencies=bound["dependencies"],
                                 binding=dict(kind="pinned_native_capture", identity=receipt))
        require(len(requests) == len(responses) and 16 <= len(requests) <= CALLS_PER_STATE and
                sum(request["core_request"]["kind"] == "wake" for request in requests) == 16, "native call accounting differs")
        require(core.audit_capture(capture, dependencies=bound["dependencies"])["calls_replayed"] == len(requests),
                "core/native replay count differs")
        write(directory / "formation.json", capture)
    finally:
        if backend is not None:
            backend.close()
    require(current_route(plan, bound, state) == route, "adapter changed during formation")
    names = ["identity.json", "formation.json"] + [request["call_id"] + suffix for request in requests
                                                for suffix in (".request.json", ".response.json")]
    write(directory / "closed.json", dict(calls=len(requests), wake_calls=16, record_calls=len(requests) - 16,
          fits=0, updates=0, files={name: digest(directory / name) for name in names},
          prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in responses),
          output_tokens=sum(len(response["output_token_ids"]) for response in responses),
          generation_seconds=sum(response["ended"] - response["started"] for response in responses)))


def validate_completed(plan, plan_sha256, bound):
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists(), "failed controller cannot score")
    controller_receipt = read(root / "controller_started.json")
    require(controller_receipt["plan_sha256"] == plan_sha256 and controller_receipt["seconds"] == OUTER_SECONDS,
            "controller identity differs")
    inventory, captures, costs, pids = {}, [], {}, []
    previous_end = controller_receipt["started"]
    for state in STATES:
        directory = root / "run" / state
        require(not any((directory / name).exists() for name in ("failure.json", "cleanup_failure.json")), "failed state cannot score")
        launch, started, released = (read(directory / name) for name in ("launch.json", "started.json", "released.json"))
        expected = launch["identity"]
        require(expected == started["identity"] == released["identity"] and type(expected["pid"]) is int and
                expected["pid"] > 1 and expected["pid"] == expected["pgid"] and
                type(expected["start_ticks"]) is int and expected["start_ticks"] > 0 and
                launch["state"] == started["state"] == released["state"] == state and
                launch["plan_sha256"] == started["plan_sha256"] == plan_sha256 and
                launch["deadline_wall"] == started["deadline_wall"] and
                launch["command"] == worker_command(plan, plan_sha256, state, launch["deadline_wall"]), "worker process custody differs")
        times = [previous_end, launch["started"], started["started"], released["ended"], launch["deadline_wall"]]
        require(all(type(value) in (int, float) and math.isfinite(value) for value in times) and
                previous_end <= launch["started"] <= started["started"] <= released["ended"] and
                0 < launch["deadline_wall"] - launch["started"] <= STATE_SECONDS and
                released["ended"] <= launch["deadline_wall"] + CLEANUP_SECONDS and
                released["ended"] - launch["started"] <= STATE_SECONDS, "worker timing/deadline differs")
        previous_end = released["ended"]
        absent(expected, bound["probe"])
        pids.append(expected["pid"])
        receipt = state_identity(plan, bound, state)
        require(read(directory / "identity.json") == receipt, "native identity receipt differs")
        closed = read(directory / "closed.json")
        count = closed["calls"]
        require(type(count) is int and 16 <= count <= CALLS_PER_STATE and closed["wake_calls"] == 16 and
                type(closed["record_calls"]) is int and closed["record_calls"] == count - 16 and
                type(closed["fits"]) is int and closed["fits"] == 0 and type(closed["updates"]) is int and closed["updates"] == 0,
                "formation workload differs")
        names = {"identity.json", "formation.json"} | {f"{index:02d}" + suffix for index in range(count)
                                                    for suffix in (".request.json", ".response.json")}
        allowed = names | {"closed.json", "launch.json", "started.json", "released.json", "stdout.log", "stderr.log"}
        require(set(bound["formation"].tree(directory)) == allowed and set(closed["files"]) == names,
                "closed/raw native file inventory differs")
        for name, checksum in closed["files"].items():
            require(digest(directory / name) == checksum, "closed native capture bytes changed")
        capture = read(directory / "formation.json")
        require(capture["state"] == receipt["core_state"] and capture["contract"] == plan["core_contract"] and
                capture["binding"] == dict(kind="pinned_native_capture", identity=receipt), "core/native binding differs")
        audit = bound["core"].audit_capture(capture, dependencies=bound["dependencies"])
        calls = [event for event in capture["events"] if event["kind"] == "call"]
        require(audit["calls_replayed"] == len(calls) == count, "core/native captured count differs")
        prompt_tokens, output_tokens, seconds, wakes = 0, 0, 0.0, 0
        for index, event in enumerate(calls):
            request, response = (read(directory / (f"{index:02d}" + suffix)) for suffix in (".request.json", ".response.json"))
            core_request = event["request"]
            require(request["call_id"] == f"{index:02d}" and request["core_request"] == core_request and
                    request["messages"] == core_request["input_messages"] and request["lora_request"] == receipt["lora_request"],
                    "native request/source join differs")
            cap = TOKENS[core_request["kind"]]
            require(type(core_request["max_output_tokens"]) is int and core_request["max_output_tokens"] == cap and
                    request["params"] == dict(plan["params"], max_tokens=cap) and
                    len(request["native"]["prompt_token_ids"]) + cap <= plan["engine"]["max_model_len"], "native settings/context drift")
            bound["formation"].validate_response(request, response, receipt["lora_request"])
            require(event["response"] == dict(request_id=core_request["request_id"], state=receipt["core_state"], raw=response["text"],
                    finish_reason=response["finish_reason"], native_response=response), "core raw differs from native output")
            prompt_tokens += len(response["actual_prompt_token_ids"])
            output_tokens += len(response["output_token_ids"])
            seconds += response["ended"] - response["started"]
            wakes += core_request["kind"] == "wake"
        require(wakes == 16 and closed["prompt_tokens"] == prompt_tokens and closed["output_tokens"] == output_tokens and
                closed["generation_seconds"] == seconds, "native token/time accounting differs")
        costs[state] = {key: closed[key] for key in ("calls", "wake_calls", "record_calls", "fits", "updates",
                                                  "prompt_tokens", "output_tokens", "generation_seconds")}
        inventory[state] = bound["formation"].tree(directory)
        captures.append(capture)
    require(len(set(pids)) == 2 and sum(cost["calls"] for cost in costs.values()) <= MAX_CALLS, "two cold workers/64-call cap required")
    return inventory, captures, costs


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "collector must not reserve CUDA")
    root = absolute(str(root))
    with budget(COLLECTION_SECONDS):
        plan, bound = verify(root, plan_sha256)
        out = fresh(out, [root, *protected_inputs(plan["specification"], bound)])
        claim = root.with_name(root.name + ".collection_claim.json")
        require(not claim.exists(), "collection already claimed; no retry")
        write(claim, dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            absent(read(root / "controller_started.json")["identity"])
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            inventory, captures, costs = validate_completed(plan, plan_sha256, bound)
            elapsed = complete["elapsed_seconds"]
            require(complete["plan_sha256"] == plan_sha256 and complete["stages"] == inventory and
                    complete["scored"] is False and complete["automatic_pass"] is False and
                    type(complete["calls"]) is int and complete["calls"] == sum(cost["calls"] for cost in costs.values()) and
                    type(complete["fits"]) is int and complete["fits"] == 0 and type(complete["updates"]) is int and complete["updates"] == 0 and
                    type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= OUTER_SECONDS, "completion custody differs")
            check_allocation(plan)
            require(bound["probe"].gpu_state(plan) is True, "pre-collection all-process GPU vacancy failed")
            comparison = bound["core"].compare_states(captures, dependencies=bound["dependencies"])
            require(comparison["automatic_pass"] is False and comparison["outcome_gate"] is None, "diagnostic-only reducer required")
            require(validate_completed(plan, plan_sha256, bound)[0] == inventory, "capture changed during reduction")
            absent(read(root / "controller_started.json")["identity"])
            require(bound["probe"].gpu_state(plan) is True, "post-collection all-process GPU release failed")
            report = dict(scope=SCOPE, claim=CLAIM, seed=plan["seed"], plan_sha256=plan_sha256,
                          completion_sha256=completion_sha256, memory=plan["specification"]["memory"], core=plan["specification"]["core"],
                          model_files=plan["model_files"], routes=plan["routes"], adapter_files=plan["adapters"],
                          comparison=comparison, costs=costs, calls=complete["calls"], fits=0, updates=0,
                          controller_elapsed_seconds=elapsed, native_capture_custody_checked=True,
                          cohort_engineering_prerequisite="Main must verify all three; this runner verifies only its seed",
                          outcome_gate=None, automatic_pass=False, scientific_pass=None)
            write(out / "scores.json", report)
            write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_POST_MEMORY_FORMATION_DIAGNOSTIC", out=str(out), scores_sha256=digest(out / "scores.json"))
        except BaseException as error:
            failure(out / "collection_failure.json", error)
            raise


def worker_command(plan, pin_value, state, deadline_wall):
    return [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", pin_value,
            "--state", state, "--deadline-wall", str(deadline_wall), "--allow-gpu"]


def run_state(plan, plan_sha256, state, deadline, bound):
    state_end = min(deadline, time.monotonic() + STATE_SECONDS)
    probe = bound["probe"]
    check_allocation(plan)
    require(state_end - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS and probe.gpu_state(plan) is True,
            "fresh assigned GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / state
    directory.mkdir()
    process, expected = None, None
    deadline_wall = time.time() + state_end - time.monotonic() - CLEANUP_SECONDS
    command = worker_command(plan, plan_sha256, state, deadline_wall)
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            expected = identity(process.pid)
            require(expected["pid"] == expected["pgid"] == process.pid, "worker isolation differs")
            write(directory / "launch.json", dict(identity=expected, state=state, plan_sha256=plan_sha256,
                  command=command, deadline_wall=deadline_wall, started=time.time()))
            remaining = state_end - time.monotonic() - CLEANUP_SECONDS
            require(remaining > 0 and process.wait(timeout=remaining) == 0, "native worker failed/deadline exhausted")
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity")
                bound["memory"].cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True, "all-process GPU release failed")
                require(time.monotonic() < state_end, "state cleanup deadline exceeded")
                write(directory / "released.json", dict(identity=expected, state=state, ended=time.time()))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def worker(root, plan_sha256, state, deadline_wall, allow_gpu=False):
    require(allow_gpu is True and state in STATES, "Main-only --allow-gpu and paired state required")
    require(type(deadline_wall) in (int, float) and math.isfinite(deadline_wall) and
            0 < deadline_wall - time.time() <= STATE_SECONDS, "finite worker deadline required")
    offline()
    directory = Path(root) / "run" / state
    try:
        with budget(deadline_wall - time.time()):
            plan, bound = verify(root, plan_sha256, native=True)
            check_allocation(plan)
            require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(),
                    "worker UUID/process isolation differs")
            launch = read(directory / "launch.json")
            require(launch["identity"] == identity(os.getpid()) and launch["state"] == state and
                    launch["plan_sha256"] == plan_sha256 and launch["deadline_wall"] == deadline_wall and
                    launch["command"] == worker_command(plan, plan_sha256, state, deadline_wall), "worker launch custody differs")
            write(directory / "started.json", dict(identity=identity(os.getpid()), state=state, plan_sha256=plan_sha256,
                  deadline_wall=deadline_wall, started=time.time()))
            capture_state(plan, state, bound)
    except BaseException as error:
        failure(directory / "failure.json", error)
        raise


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True, "Main-only --allow-gpu required")
    offline()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "controller must not reserve CUDA")
    root = absolute(str(root))
    require(not (root / "controller_started.json").exists(), "controller already claimed; no retry")
    claimed = False
    try:
        with budget(OUTER_SECONDS):
            deadline = time.monotonic() + OUTER_SECONDS
            plan, bound = verify(root, plan_sha256, native=True)
            check_allocation(plan)
            write(root / "controller_started.json", dict(plan_sha256=plan_sha256, identity=identity(os.getpid()),
                  started=time.time(), seconds=OUTER_SECONDS))
            claimed = True
            (root / "run").mkdir()
            for state in STATES:
                run_state(plan, plan_sha256, state, deadline, bound)
            inventory, captures, costs = validate_completed(plan, plan_sha256, bound)
            require(time.monotonic() < deadline, "total controller cap exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory,
                  calls=sum(cost["calls"] for cost in costs.values()), fits=0, updates=0, scored=False,
                  elapsed_seconds=OUTER_SECONDS - (deadline - time.monotonic()), automatic_pass=False))
            return dict(status="POST_MEMORY_FORMATION_COMPLETE_NOT_SCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        if claimed:
            failure(root / "controller_failure.json", error)
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
            command.add_argument("--state", choices=STATES, required=True)
            command.add_argument("--deadline-wall", type=float, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    options = vars(parser.parse_args(argv))
    name = options.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
