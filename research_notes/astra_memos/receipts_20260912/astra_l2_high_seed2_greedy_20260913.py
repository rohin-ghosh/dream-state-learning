"""Bounded saved-checkpoint greedy TRAIN/READOUT probe; zero fit or updates."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace


SCHEMA = "astra_l2_high_seed2_greedy_20260913_v1"
ACCESS_PIN = "d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525"
CONTROLLER_HELPER_PIN = "3f5f6118e3fef60074ac533b2650d415b6bd57ff15e379e2bf548be470233721"
STATES = ("OFF", "fit2_PROMOTE")
VIEWS = ("train", "readout")
TOTAL_SECONDS, WORKER_SECONDS, COLLECTION_SECONDS = 1200, 420, 180
CALLS_PER_STATE, TOTAL_CALLS = 32, 64
CLAIM = "Saved seed2-high greedy exact-TRAIN/access diagnostic; not a new fit, independent seed, learning-loop or H1/H2 claim."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(encoded(value))


def load_pinned(name, path, pin):
    require(digest(path) == pin, name + " source pin differs")
    sys.dont_write_bytecode = True
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def context(settings, *, native=False, build=False):
    access = load_pinned("_greedy_access", settings["access"], ACCESS_PIN)
    source = access.frozen_source(settings["source"])
    access.collection_metadata(settings["collection"])
    runtime = access.load_module("_greedy_original_runtime", source / "gpu/astra_l2_public_record_dev.py")
    runtime.offline()
    require(access.digest(access.ROOT / "SEAL.json") == access.SEAL_PIN, "original seal drift")
    terminal, custody = runtime.custody(access.ROOT, access.PLAN_PIN)
    require(terminal["status"] == "COMPLETE", "original source incomplete")
    plan, core, trainer, probe, reflection, world = runtime.verify(access.ROOT, access.PLAN_PIN, native=native)
    require(plan["spec"]["source_files"] == access.SOURCE_FILES and plan["base_sha256"] == access.BASE_PIN and
            {name: entry["sha256"] for name, entry in plan["spec"]["helpers"].items()} == access.HELPERS,
            "original source/model/helper binding differs")
    require(runtime.plan_learner_seed(plan) == 2 and runtime.plan_learning_rate(plan) == 1e-4, "seed/LR differs")
    fit = runtime.read_stage(plan, "fit2_PROMOTE")
    adapter = access.ROOT / "run/fit2_PROMOTE/data/adapter"
    require(fit["candidate_sha256"] == access.CANDIDATES["fit2_PROMOTE"] and
            runtime.tree(adapter) == fit["candidate_files"] and
            access.value_hash(fit["candidate_files"]) == access.CANDIDATES["fit2_PROMOTE"], "candidate drift")
    routes = {"OFF": None, "fit2_PROMOTE": dict(name="l2_public_record", id=1, path=str(adapter),
                                                sha256=access.CANDIDATES["fit2_PROMOTE"])}
    for state, stage in (("OFF", "baseline"), ("fit2_PROMOTE", "report2_PROMOTE")):
        require(runtime.read(access.ROOT / "run" / stage / "data/identity.json")["route"] == routes[state],
                "original native route differs")
    training = runtime.read(access.ROOT / "run/fit2_PROMOTE/data/training.json")
    targets = {row["slot_id"]: row["target_hex"] for row in training["encoding"]}
    calls = runtime.read(access.ROOT / "calls.json")
    cases = None
    if build:
        tokenizer = probe.native_tokenizer(plan["spec"]["model"])
        require(tokenizer.chat_template == plan["chat_template"], "tokenizer template drift")
        cases = access.build_cases(runtime, core, trainer, probe, plan, world, tokenizer, access.ROOT)
    require(runtime.custody(access.ROOT, access.PLAN_PIN)[1] == custody, "old root changed")
    return SimpleNamespace(access=access, runtime=runtime, plan=plan, core=core, probe=probe, world=world,
                           custody=custody, routes=routes, calls=calls, targets=targets, cases=cases)


def expected_rows(ctx, cases):
    require(type(cases) is list and len(cases) == 32, "32 exact cases required")
    public = ctx.core.public_view(ctx.world)
    result = []
    for case, (view, index) in zip(cases, [(view, index) for view in VIEWS for index in range(16)], strict=True):
        require(case["view"] == view and type(case["slot_index"]) is int and case["slot_index"] == index and
                case["slot_id"] == public.slots[index].slot_id, "case order/slot differs")
        saved = ctx.calls[view][index]
        require(saved["slot_id"] == case["slot_id"] and len(case["candidates"]) == 2 and
                all(candidate["native"] == saved["native"] for candidate in case["candidates"]), "literal archived prefix differs")
        require(ctx.calls["wake"][index] == ctx.calls["train"][index], "wake/TRAIN drift")
        target_hex = ctx.targets[case["slot_id"]]
        require(target_hex in [(candidate["action"] + candidate["suffix"]).encode("ascii").hex()
                               for candidate in case["candidates"]], "archived target differs")
        result.append(dict(view=view, slot_index=index, slot_id=case["slot_id"],
                           messages=saved["messages"], native=saved["native"], archived_target_hex=target_hex))
    return result


def prepare(settings, root, *, allow_native=False):
    require(allow_native and not os.environ.get("CUDA_VISIBLE_DEVICES"), "explicit CPU-native preparation with empty CUDA required")
    ctx = context(settings, native=True, build=True)
    helper = load_pinned("_greedy_controller_helper", settings["controller_helper"], CONTROLLER_HELPER_PIN)
    require(settings["gpu_index"] == helper.GPU_INDEX and settings["gpu_uuid"] == helper.GPU_UUID,
            "planned allocation must match the existing node3 GPU3 binding")
    require(digest(settings["precheck"]) == helper.PRECHECK_PIN, "allocation checker pin differs")
    helper.check_allocation_binding(SimpleNamespace(**settings))
    protected = (ctx.access.ROOT, settings["source"], settings["collection"], ctx.plan["spec"]["model"],
                 settings["access"], settings["controller_helper"], settings["precheck"], Path(__file__),
                 *[entry["path"] for entry in ctx.plan["spec"]["helpers"].values()])
    root = ctx.access.external_output(root, protected)
    ctx.runtime.launcher_output_outside(ctx.access.ROOT)
    require(len(ctx.targets) == 16, "all16 archived child targets required")
    rows = expected_rows(ctx, ctx.cases)
    root.mkdir(mode=0o700)
    manifest = dict(schema=SCHEMA, root=str(root), settings=settings, runtime_sha256=digest(__file__),
                    access_sha256=ACCESS_PIN, controller_helper_sha256=CONTROLLER_HELPER_PIN,
                    plan_sha256=ctx.access.PLAN_PIN, seal_sha256=ctx.access.SEAL_PIN,
                    original_collection_sha256=ctx.access.COLLECTION_PIN, base_sha256=ctx.access.BASE_PIN,
                    candidate_sha256=ctx.access.CANDIDATES["fit2_PROMOTE"], python=ctx.plan["python"],
                    python_sha256=ctx.plan["python_sha256"], cases=ctx.cases, rows=rows, routes=ctx.routes,
                    engine=ctx.plan["engine"], params=ctx.plan["params"], total_calls=64, updates=0,
                    max_seconds=TOTAL_SECONDS, claim=CLAIM)
    write(root / "prepared.json", manifest)
    return dict(root=str(root), prepared_sha256=digest(root / "prepared.json"), status="PASS_NATIVE_CPU_PREFIXES", calls=0)


def load_prepared(root, prepared_sha256, *, native=False, build=False):
    root = Path(root).absolute()
    require(digest(root / "prepared.json") == prepared_sha256, "prepared pin differs")
    manifest = read(root / "prepared.json")
    require(manifest["schema"] == SCHEMA and manifest["root"] == str(root) and
            manifest["runtime_sha256"] == digest(__file__) and
            manifest["python"] == os.path.abspath(sys.executable) and manifest["python_sha256"] == digest(sys.executable),
            "runtime/root/interpreter differs")
    ctx = context(manifest["settings"], native=native, build=build)
    require(manifest["plan_sha256"] == ctx.access.PLAN_PIN and manifest["seal_sha256"] == ctx.access.SEAL_PIN and
            manifest["original_collection_sha256"] == ctx.access.COLLECTION_PIN and
            manifest["base_sha256"] == ctx.access.BASE_PIN and manifest["candidate_sha256"] == ctx.access.CANDIDATES["fit2_PROMOTE"] and
            manifest["routes"] == ctx.routes and manifest["engine"] == ctx.plan["engine"] and manifest["params"] == ctx.plan["params"],
            "original run binding differs")
    require(manifest["rows"] == expected_rows(ctx, manifest["cases"]), "prepared rows drift")
    if build:
        require(ctx.access.encoded(ctx.cases) == ctx.access.encoded(manifest["cases"]), "fresh native build_cases differs")
    return manifest, ctx


def validate_generated(runtime, request, response, route):
    runtime.validate_response(response, route)
    require(response["native"] == request["native"] and
            response["returned_prompt_token_ids"] == request["native"]["prompt_token_ids"], "exact generation prefix/token drift")


def generate_rows(rows, backend, runtime, route, check_deadline, emit):
    require(len(rows) == 32 and [(row["view"], row["slot_index"]) for row in rows] ==
            [(view, index) for view in VIEWS for index in range(16)], "fixed32 generation order")
    for index, row in enumerate(rows):
        check_deadline()
        request = copy.deepcopy(row)
        emit(index, "request", request)
        response = backend.generate(request["messages"])
        emit(index, "response", response)
        validate_generated(runtime, request, response, route)
        check_deadline()
    return 32


def check_deadline(deadline):
    require(type(deadline) in (int, float) and math.isfinite(deadline) and time.time() < deadline, "deadline exhausted")


def worker(root, prepared_sha256, state, deadline_unix, *, allow_native=False):
    require(allow_native and state in STATES, "explicit native permission/fixed state required")
    started = time.time()
    check_deadline(deadline_unix)
    require(deadline_unix <= started + WORKER_SECONDS, "worker exceeds finite ceiling")
    manifest, ctx = load_prepared(root, prepared_sha256, native=True, build=True)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == manifest["settings"]["gpu_uuid"], "worker GPU UUID differs")
    root = Path(root)
    directory = root / state
    require(not directory.exists(), "state already attempted; no retry")
    directory.mkdir()
    write(directory / "started.json", dict(pid=os.getpid(), state=state, started_unix=started, deadline_unix=deadline_unix,
                                          prepared_sha256=prepared_sha256, route=ctx.routes[state]))
    backend = None
    try:
        with ctx.runtime.budget(max(.001, deadline_unix - time.time() - 20)):
            check_deadline(deadline_unix)
            backend = ctx.runtime.Native(ctx.plan, ctx.probe, ctx.routes[state])
            calls = generate_rows(manifest["rows"], backend, ctx.runtime, ctx.routes[state],
                                  lambda: check_deadline(deadline_unix - 20),
                                  lambda index, kind, data: write(directory / f"{index:02d}.{kind}.json", data))
    finally:
        if backend is not None:
            with ctx.runtime.budget(max(.001, min(20, deadline_unix - time.time()))):
                backend.close()
    require(ctx.runtime.custody(ctx.access.ROOT, ctx.access.PLAN_PIN)[1] == ctx.custody and
            digest(ctx.access.ROOT / "SEAL.json") == ctx.access.SEAL_PIN, "original root changed")
    check_deadline(deadline_unix)
    write(directory / "complete.json", dict(state=state, pid=os.getpid(), prepared_sha256=prepared_sha256,
          calls=calls, fits=0, updates=0, started_unix=started, ended_unix=time.time(),
          files=ctx.runtime.tree(directory), candidate_sha256=ctx.access.CANDIDATES[state]))
    return dict(state=state, calls=calls, updates=0)


def score_rows(ctx, rows, responses):
    require(len(rows) == len(responses) == 32, "incomplete generations cannot be scored")
    public = ctx.core.public_view(ctx.world)
    panels = {}
    for view in VIEWS:
        scored = []
        for row, response in zip(rows, responses, strict=True):
            if row["view"] != view:
                continue
            raw = bytes.fromhex(response["raw_hex"])
            choice = ctx.runtime.legal_action(public, raw)
            scored.append(dict(slot_id=row["slot_id"], slot_index=row["slot_index"], choice=choice,
                               correct=choice == ctx.world.success_actions[row["slot_index"]],
                               exact_archived_target=raw.hex() == row["archived_target_hex"],
                               finish_reason=response["finish_reason"], output_tokens=len(response["output_token_ids"])))
        require(len(scored) == 16, "panel cardinality differs")
        panels[view] = dict(rows=scored, total=16, old_total=8, new_total=8,
            correct=sum(row["correct"] for row in scored), old_correct=sum(row["correct"] for row in scored[:8]),
            new_correct=sum(row["correct"] for row in scored[8:]), legal=sum(row["choice"] is not None for row in scored),
            malformed=sum(row["choice"] is None for row in scored),
            exact_archived_targets=sum(row["exact_archived_target"] for row in scored),
            stop_correct=sum(row["correct"] and row["finish_reason"] == "stop" for row in scored),
            length_outputs=sum(row["finish_reason"] == "length" for row in scored))
    return panels


def collect(root, prepared_sha256, deadline_unix):
    check_deadline(deadline_unix)
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "collection must not reserve CUDA")
    root = Path(root).absolute()
    require(digest(root / "prepared.json") == prepared_sha256, "prepared pin differs")
    manifest = read(root / "prepared.json")
    require(manifest["runtime_sha256"] == digest(__file__), "collector source differs")
    started = read(root / "controller_started.json")
    require(started["prepared_sha256"] == prepared_sha256 and deadline_unix == started["deadline_unix"] and
            type(started["started_unix"]) in (int, float) and math.isfinite(started["started_unix"]) and
            deadline_unix == started["started_unix"] + TOTAL_SECONDS and started["started_unix"] <= time.time(),
            "controller deadline differs")
    output = root.with_name(root.name + "_collected")
    claim = root.with_name(root.name + ".collection_claim.json")
    require(not output.exists() and not output.is_symlink() and not claim.exists(), "already claimed/collected; never retry")
    write(claim, dict(root=str(root), out=str(output), prepared_sha256=prepared_sha256, claimed_unix=time.time()))
    output.mkdir()
    try:
        manifest, ctx = load_prepared(root, prepared_sha256)
        with ctx.runtime.budget(min(COLLECTION_SECONDS, max(.001, deadline_unix - time.time()))):
            completed = read(root / "capture_complete.json")
            require(completed["prepared_sha256"] == prepared_sha256 and set(completed["states"]) == set(STATES), "incomplete state roster")
            states, pids, costs = {}, [], {}
            for state in STATES:
                directory = root / state
                require(ctx.runtime.tree(directory) == completed["states"][state], "completed capture changed")
                receipt = read(directory / "complete.json")
                launch = read(root / f"{state}.launch.json")
                require(receipt["state"] == state and receipt["prepared_sha256"] == prepared_sha256 and
                        type(receipt["calls"]) is int and receipt["calls"] == 32 and
                        type(receipt["updates"]) is int and receipt["updates"] == 0 and
                        type(receipt["fits"]) is int and receipt["fits"] == 0 and
                        type(receipt["pid"]) is int and receipt["pid"] > 1 and
                        receipt["pid"] == launch["identity"]["pid"] and not Path(f"/proc/{receipt['pid']}").exists(),
                        "worker not completed/absent or budget differs")
                require(receipt["candidate_sha256"] == ctx.access.CANDIDATES[state] and
                        all(type(receipt[key]) in (int, float) and math.isfinite(receipt[key]) for key in ("started_unix", "ended_unix")) and
                        started["started_unix"] <= receipt["started_unix"] <= receipt["ended_unix"] <= deadline_unix and
                        receipt["ended_unix"] - receipt["started_unix"] <= WORKER_SECONDS, "worker identity/time differs")
                require(read(root / f"{state}.all_process_release.json")["vacant"] is True, "release missing")
                pids.append(receipt["pid"])
                responses = []
                for index, expected in enumerate(manifest["rows"]):
                    request = read(directory / f"{index:02d}.request.json")
                    response = read(directory / f"{index:02d}.response.json")
                    require(request == expected, "captured request differs")
                    validate_generated(ctx.runtime, request, response, ctx.routes[state])
                    responses.append(response)
                expected_files = {"started.json", "complete.json"} | {f"{index:02d}.{kind}.json" for index in range(32) for kind in ("request", "response")}
                require(set(ctx.runtime.tree(directory)) == expected_files and
                        receipt["files"] == {name: checksum for name, checksum in completed["states"][state].items() if name != "complete.json"},
                        "extra/missing native captures")
                states[state] = score_rows(ctx, manifest["rows"], responses)
                costs[state] = dict(calls=32, output_tokens=sum(len(row["output_token_ids"]) for row in responses),
                    prompt_tokens=sum(len(row["returned_prompt_token_ids"]) for row in responses),
                    generation_seconds=sum(row["ended"] - row["started"] for row in responses))
            require(len(set(pids)) == 2, "states must be separate fresh processes")
            report = dict(schema=SCHEMA, claim=CLAIM, calls=64, fits=0, updates=0, states=states, costs=costs,
                prepared_sha256=prepared_sha256, plan_sha256=ctx.access.PLAN_PIN,
                candidate_sha256=ctx.access.CANDIDATES["fit2_PROMOTE"], capture_complete_sha256=digest(root / "capture_complete.json"),
                original_collection_sha256=ctx.access.COLLECTION_PIN, scientific_pass=None,
                scoring="Original legal_action and saved world success_actions on both exact views; stop_correct is separate, not a changed legacy scorer.",
                versus_OFF={view: states["fit2_PROMOTE"][view]["correct"] - states["OFF"][view]["correct"] for view in VIEWS})
            require(ctx.runtime.custody(ctx.access.ROOT, ctx.access.PLAN_PIN)[1] == ctx.custody, "original root changed")
            check_deadline(deadline_unix)
            write(output / "report.json", report)
            write(output / "collection.json", dict(status="COMPLETE_DIAGNOSTIC_ONLY", report_sha256=digest(output / "report.json"),
                  prepared_sha256=prepared_sha256, ended_unix=time.time()))
    except BaseException as error:
        write(output / "collection_failure.json", dict(type=type(error).__name__, error=str(error)))
        raise
    return dict(output=str(output), report_sha256=digest(output / "report.json"), calls=64, updates=0)


def run_child(helper, command, directory, label, deadline, device=""):
    check_deadline(deadline)
    with (directory / f"{label}.stdout").open("xb") as stdout, (directory / f"{label}.stderr").open("xb") as stderr:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   env=helper.environment(device), start_new_session=True)
        bound = None
        try:
            bound = helper.identity(process.pid)
            write(directory / f"{label}.launch.json", dict(command=command, identity=bound, started_unix=time.time()))
            returncode = process.wait(timeout=max(.001, deadline - time.time()))
        except BaseException:
            if bound is not None:
                helper.stop_owned(process, bound)
            else:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            raise
    require(returncode == 0, label + " subprocess failed")


def allocation_check(helper, ctx, settings, root, label, deadline):
    require(time.time() + 95 < deadline, "insufficient allocation/release check budget")
    helper.precheck(SimpleNamespace(**settings), root / f"{label}.reservation.json")
    vacant = ctx.probe.gpu_state(dict(gpu_index=settings["gpu_index"], gpu_uuid=settings["gpu_uuid"]))
    write(root / f"{label}.json", dict(vacant=vacant, checked_unix=time.time(), gpu_index=settings["gpu_index"], gpu_uuid=settings["gpu_uuid"]))
    require(vacant is True, "original all-process XML vacancy check failed")


def controller(root, prepared_sha256, *, allow_gpu=False):
    require(allow_gpu and not os.environ.get("CUDA_VISIBLE_DEVICES"), "explicit GPU permission; controller must not reserve CUDA")
    started = time.time()
    deadline = started + TOTAL_SECONDS
    root = Path(root).absolute()
    manifest, ctx = load_prepared(root, prepared_sha256)
    helper = load_pinned("_greedy_controller_helper", manifest["settings"]["controller_helper"], CONTROLLER_HELPER_PIN)
    settings = manifest["settings"]
    require(settings["gpu_index"] == helper.GPU_INDEX and settings["gpu_uuid"] == helper.GPU_UUID, "allocation mismatch")
    require(not (root / "controller_started.json").exists() and not root.with_name(root.name + ".collection_claim.json").exists(),
            "already attempted/claimed; no retry")
    write(root / "controller_started.json", dict(prepared_sha256=prepared_sha256, started_unix=started,
          deadline_unix=deadline, pid=os.getpid(), states=list(STATES), calls=64, updates=0))
    try:
        with ctx.runtime.budget(max(.001, deadline - time.time() - 25)):
            for state in STATES:
                allocation_check(helper, ctx, settings, root, f"{state}.precheck", deadline - COLLECTION_SECONDS - 30)
                worker_deadline = min(time.time() + WORKER_SECONDS, deadline - COLLECTION_SECONDS - 150)
                require(worker_deadline > time.time() + 30, "no remaining worker budget")
                command = [sys.executable, "-B", str(Path(__file__).absolute()), "worker", "--root", str(root),
                           "--prepared-sha256", prepared_sha256, "--state", state,
                           "--deadline-unix", str(worker_deadline), "--allow-native"]
                try:
                    run_child(helper, command, root, state, worker_deadline, settings["gpu_uuid"])
                finally:
                    allocation_check(helper, ctx, settings, root, f"{state}.all_process_release", deadline - COLLECTION_SECONDS - 25)
            write(root / "capture_complete.json", dict(prepared_sha256=prepared_sha256,
                  states={state: ctx.runtime.tree(root / state) for state in STATES}, ended_unix=time.time()))
            command = [sys.executable, "-B", str(Path(__file__).absolute()), "collect", "--root", str(root),
                       "--prepared-sha256", prepared_sha256, "--deadline-unix", str(deadline)]
            run_child(helper, command, root, "collect", min(deadline - 25, time.time() + COLLECTION_SECONDS))
            terminal = dict(status="COMPLETE_DIAGNOSTIC_ONLY", calls=64, fits=0, updates=0,
                            collection=read(root.with_name(root.name + "_collected") / "collection.json"))
    except BaseException as error:
        terminal = dict(status="FAILED_NO_RETRY", error_type=type(error).__name__, error=str(error), updates=0)
    terminal.update(started_unix=started, ended_unix=time.time(), elapsed_seconds=time.time() - started)
    write(root / "terminal.json", terminal)
    require(terminal["status"] == "COMPLETE_DIAGNOSTIC_ONLY", "diagnostic failed; inspect preserved terminal/logs, never retry root")
    return terminal


def main(argv=None):
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        if name == "prepare":
            for field in ("source", "collection", "access", "controller-helper", "precheck", "expected-boot-id", "gpu-uuid"):
                command.add_argument("--" + field, required=True)
            command.add_argument("--gpu-index", type=int, required=True)
            command.add_argument("--lease-end-unix", type=float, required=True)
            command.add_argument("--allow-native", action="store_true")
        else:
            command.add_argument("--prepared-sha256", required=True)
        if name == "controller":
            command.add_argument("--allow-gpu", action="store_true")
        if name in ("worker", "collect"):
            command.add_argument("--deadline-unix", type=float, required=True)
        if name == "worker":
            command.add_argument("--state", choices=STATES, required=True)
            command.add_argument("--allow-native", action="store_true")
    args = vars(parser.parse_args(argv))
    name = args.pop("command")
    if name == "prepare":
        root, allowed = args.pop("root"), args.pop("allow_native")
        result = prepare(args, root, allow_native=allowed)
    else:
        result = globals()[name](**args)
    print(encoded(result).decode(), end="", flush=True)


if __name__ == "__main__":
    main()
