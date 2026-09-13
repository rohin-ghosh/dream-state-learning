"""No-fit DEV prediction scaffold withdrawal, using the pinned SEQ142 runtime."""

import argparse
from collections import Counter
import importlib.util
import inspect
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import astra_pcfl_zero_fit_outer as lifecycle


SELF = Path(__file__).resolve()
SCHEMA = "astra.level1.prediction_transfer.v1"
STATES, VIEWS = ("OFF", "post"), ("FULL", "MINIMAL")
TOTAL_SECONDS, COLLECTION_SECONDS, CLEANUP_SECONDS, DETACH_SECONDS = 1800, 180, 60, 4
LEASE_MARGIN, PREPARE_SECONDS = 21600, 300
CLAIM = "Authored same-task DEV scaffold withdrawal only; no fit, retention, parenting, H1/P1/H2 or clean-lineage qualification."
require, read, write = lifecycle.require, lifecycle.read, lifecycle.write


def source_files():
    modules = (lifecycle, lifecycle.driver, lifecycle.driver.native, lifecycle.driver.runtime,
               lifecycle.driver.core, lifecycle.driver.runtime.prepare_api)
    return {str(path): lifecycle.file_hash(path) for path in (SELF, *(Path(module.__file__).resolve() for module in modules))}


def pin_file(pin):
    require(type(pin) is dict and set(pin) == {"path", "sha256"}, "file pin fields")
    path = Path(pin["path"])
    require(path.is_absolute() and path.resolve() == path and path.is_file(), "absolute unaliased file required")
    require(lifecycle.file_hash(path) == pin["sha256"], "file/source pin drift: " + str(path))
    return path


def load_module(pin, name):
    sys.dont_write_bytecode = True
    path = pin_file(pin)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def history(spec, runtime, *, native=False):
    parent = read(pin_file(spec["original_plan"]))
    root = Path(parent["root"])
    require(spec["original_plan"]["path"] == str(root / "plan.json") and parent["scope"] == runtime.SCOPE
            and parent["self_sha256"] == spec["runtime"]["sha256"] and parent["skill"] == "prediction"
            and type(parent["learner_seed"]) is int and type(spec["learner_seed"]) is int
            and parent["learner_seed"] == spec["learner_seed"] in (0, 1, 2), "original prediction identity")
    require(not (root / "controller_failure.json").exists() and not (root / "prepare_failure.json").exists(), "failed original parent")
    _, _, probe = runtime.checked_apis(parent["specification"])
    for name, checksum in parent["input_hashes"].items():
        require(runtime.digest(root / name) == checksum, "original prepared input drift")
    complete = read(pin_file(spec["original_completion"]))
    require(spec["original_completion"]["path"] == str(root / "capture_complete.json")
            and complete["plan_sha256"] == spec["original_plan"]["sha256"] and complete["calls"] == 120
            and complete["scored"] is False, "original completion binding")
    require(runtime.validate_completed(parent, spec["original_plan"]["sha256"], probe) == complete["stages"], "original custody/inventory drift")
    collection = read(pin_file(spec["original_collection"]))
    require(collection["completion_sha256"] == spec["original_completion"]["sha256"], "original collection/completion join")
    scores_path = Path(spec["original_collection"]["path"]).with_name("scores.json")
    require(runtime.digest(scores_path) == collection["scores_sha256"], "original scores file drift")
    scores = read(scores_path)
    require(scores["plan_sha256"] == spec["original_plan"]["sha256"] and scores["skill"] == "prediction"
            and scores["learner_seed"] == parent["learner_seed"], "original score identity")
    adapter, files = runtime.adapter_for(parent, "post")
    require(parent["engine"] == runtime.ENGINE and parent["params"] == runtime.PARAMS
            and runtime.PARAMS["max_tokens"] == 192, "original readout settings")
    if native:
        require(parent["model_files"] == probe.model_hashes(parent["model"])
                and parent["environment"] == runtime.environment(probe)
                and parent["python"] == os.path.abspath(sys.executable)
                and parent["python_sha256"] == runtime.digest(sys.executable), "native original model/environment binding")
    return parent, probe, adapter, files


def inputs(spec, *, native=False):
    require(spec["schema"] == SCHEMA + "/spec" and spec["self_sha256"] == lifecycle.file_hash(SELF)
            and spec["source_files"] == source_files(), "execution source pins")
    runtime = load_module(spec["runtime"], "prediction_transfer_runtime")
    pin_file(spec["protocol"])
    pin_file(spec["shutdown_binding"])
    allocation = read(pin_file(spec["allocation"]))
    lifecycle.validate_allocation(allocation)
    require(allocation["outer_sha256"] == spec["self_sha256"], "allocation source pin")
    parent, probe, adapter, files = history(spec, runtime, native=native)
    require(allocation["python"] == parent["python"], "allocation original Python")
    material = load_module(spec["material"], "prediction_transfer_material")
    return runtime, material, parent, probe, adapter, files, allocation


def material_rows(material, parent):
    original = parent["specification"]["material"]
    data = material.build_material(original_material_path=original["path"])
    require(data == material.build_material(original_material_path=original["path"]), "deterministic shared material required")
    require(data["original_material"]["path"] == original["path"] and data["original_material"]["sha256"] == original["sha256"]
            and data["max_new_tokens"] == 192, "frozen original scorer/192-token binding")
    rows = data["rows"]
    require(len(rows) == 48 and len({row["row_id"] for row in rows}) == 48, "fixed unique 48 rows")
    require(Counter(row["view"] for row in rows) == dict.fromkeys(VIEWS, 24), "fixed FULL/MINIMAL roster")
    cases = {}
    for row in rows:
        cases.setdefault(row["case_id"], []).append(row)
        require(type(row["prompt"]) is str and row["input_messages"] == [{"role": "user", "content": row["prompt"]}]
                and row["max_new_tokens"] == 192, "public prompt messages only")
    require(len(cases) == 24 and all(len(pair) == 2 and {row["view"] for row in pair} == set(VIEWS)
            and all(pair[0][key] == pair[1][key] for key in ("source", "expected", "raw_target", "case")) for pair in cases.values()), "paired factual cases")
    require(sorted(Counter(pair[0]["case"] for pair in cases.values()).values()) == [6] * 4, "four six-case groups")
    return data, rows


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "Main-only native CPU tokenizer preparation")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "prepare requires empty CVD")
    spec = read(pin_file({"path": str(spec_path), "sha256": spec_sha256}))
    runtime = load_module(spec["runtime"], "prediction_transfer_runtime")
    runtime.offline()
    with runtime.budget(PREPARE_SECONDS):
        runtime, material, parent, probe, adapter, files, allocation = inputs(spec, native=True)
        root = Path(root)
        require(root.is_absolute() and root.parent.resolve() == root.parent and root.parent.is_dir(), "fresh absolute root parent")
        protected = [Path(parent["root"]), Path(parent["source"]), Path(parent["model"]), SELF, Path(spec_path),
                     *[Path(value["path"]) for value in spec.values() if type(value) is dict and set(value) == {"path", "sha256"}]]
        require(all(not root.is_relative_to(path) and not path.is_relative_to(root) for path in protected), "output/input overlap")
        require(time.time() + TOTAL_SECONDS <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "lease finish margin")
        root.mkdir(exist_ok=False)
        write(root / "prepare_started.json", {"spec_sha256": spec_sha256, "at": time.time()})
        try:
            data, rows = material_rows(material, parent)
            tokenizer = probe.native_tokenizer(parent["model"])
            require(tokenizer.chat_template == parent["chat_template"], "original tokenizer template")
            calls = []
            for index, row in enumerate(rows):
                score = material.score_response(row, row["raw_target"], "stop", original_material_path=parent["specification"]["material"]["path"])
                runtime.validate_score(score, "stop")
                require(score["passed"] and score["strict"], "material reference fails frozen scorer")
                calls.append({"call_id": f"call_{index:02d}", "row_id": row["row_id"], "messages": row["input_messages"],
                              "native": probe.render(tokenizer, row["input_messages"])})
            write(root / "spec.json", spec)
            write(root / "material.json", data)
            write(root / "calls.json", calls)
            plan = {"schema": SCHEMA, "claim": CLAIM, "root": str(root), "spec_sha256": spec_sha256,
                "spec": spec, "learner_seed": spec["learner_seed"], "states": list(STATES), "calls_per_state": 48,
                "fits": 0, "updates": 0, "adapter": adapter, "adapter_files": files,
                "input_hashes": {name: runtime.digest(root / name) for name in ("spec.json", "material.json", "calls.json")}}
            write(root / "plan.json", plan)
            return {"plan_sha256": runtime.digest(root / "plan.json"), "calls": 96, "fits": 0, "updates": 0}
        except BaseException as error:
            runtime.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, *, native=False):
    root = Path(root)
    plan = read(pin_file({"path": str(root / "plan.json"), "sha256": plan_sha256}))
    require(plan["schema"] == SCHEMA and plan["claim"] == CLAIM and plan["root"] == str(root)
            and plan["states"] == list(STATES) and plan["calls_per_state"] == 48
            and plan["fits"] == plan["updates"] == 0 and not (root / "prepare_failure.json").exists(), "prepared transfer identity")
    bound = inputs(plan["spec"], native=native)
    runtime, material, parent, _, adapter, files, _ = bound
    require(plan["adapter"] == adapter and plan["adapter_files"] == files, "original adapter drift")
    require(set(plan["input_hashes"]) == {"spec.json", "material.json", "calls.json"}, "prepared inventory")
    for name, checksum in plan["input_hashes"].items():
        require(runtime.digest(root / name) == checksum, "prepared input drift")
    require(read(root / "spec.json") == plan["spec"] and read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "spec copy binding")
    data, rows = material_rows(material, parent)
    require(read(root / "material.json") == data, "material replay differs")
    calls = read(root / "calls.json")
    require(len(calls) == 48, "48 prepared calls")
    for index, (call, row) in enumerate(zip(calls, rows)):
        require(call["call_id"] == f"call_{index:02d}" and call["row_id"] == row["row_id"] and call["messages"] == row["input_messages"], "fixed ordered visibility")
    return plan, bound


def backend(runtime, parent, probe, adapter, shutdown_pin):
    class TransferNative(runtime.Native):
        def close(self):
            method = self.llm.llm_engine.engine_core.shutdown
            require(Path(inspect.getsourcefile(method)).resolve() == pin_file(shutdown_pin), "installed EngineCore shutdown source")
            method()
            return {"source": shutdown_pin, "shutdown_returned": True}
    return TransferNative(parent, probe, adapter)


def capture(plan, bound, state, deadline):
    runtime, _, parent, probe, saved_adapter, files, _ = bound
    adapter = saved_adapter if state == "post" else None
    route = None if adapter is None else {"name": "level1_skill", "id": 1, "path": adapter}
    directory = Path(plan["root"]) / "run" / state
    identity = {"kind": "NATIVE", "worker": lifecycle.identity(os.getpid()), "state": state,
        "original_plan": plan["spec"]["original_plan"], "model": parent["model"], "model_files": parent["model_files"],
        "adapter_files": files if adapter else {}, "route": route, "engine": runtime.ENGINE, "params": runtime.PARAMS}
    write(directory / "identity.json", identity)
    session, responses, load_start = None, [], time.monotonic()
    try:
        session = backend(runtime, parent, probe, adapter, plan["spec"]["shutdown_binding"])
        write(directory / "load.json", {"started": load_start, "ready": time.monotonic(), "route": route})
        for call in read(Path(plan["root"]) / "calls.json"):
            lifecycle.remaining(deadline)
            write(directory / (call["call_id"] + ".request.json"), call)
            response = session.generate(call["messages"])
            write(directory / (call["call_id"] + ".response.json"), response)
            require(response["lora_request"] == route, "actual adapter request route")
            probe.validate_response(call, response)
            responses.append(response)
    finally:
        if session is not None:
            write(directory / "close.json", {"shutdown": session.close(), "calls": len(responses), "ended": time.monotonic()})
    require(read(directory / "close.json")["shutdown"] == {"source": plan["spec"]["shutdown_binding"], "shutdown_returned": True}, "explicit EngineCore shutdown failed")
    require(runtime.tree(saved_adapter) == files, "readout mutated original adapter")
    names = ["identity.json", "load.json", "close.json"] + [call["call_id"] + suffix
        for call in read(Path(plan["root"]) / "calls.json") for suffix in (".request.json", ".response.json")]
    write(directory / "closed.json", {"calls": 48, "files": {name: runtime.digest(directory / name) for name in names}})


def worker(root, plan_sha256, state, deadline, allow_gpu=False):
    require(allow_gpu is True and state in STATES, "explicit no-fit worker state")
    plan, bound = verify(root, plan_sha256, native=True)
    runtime, _, _, _, _, _, allocation = bound
    runtime.offline()
    require(os.getpid() == os.getpgrp() == os.getsid(0) and os.environ.get("CUDA_VISIBLE_DEVICES") == allocation["gpu_uuid"], "isolated allocated worker")
    require(time.time() <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "worker lease margin")
    directory = Path(root) / "run" / state
    write(directory / "started.json", {"identity": lifecycle.identity(os.getpid()), "plan_sha256": plan_sha256, "state": state})
    try:
        with runtime.budget(lifecycle.remaining(deadline)):
            capture(plan, bound, state, deadline)
    except BaseException as error:
        runtime.failure(directory / "failure.json", error)
        raise


def resources(allocation, deadline, directory, label):
    lifecycle.check_node(allocation)
    checks = (("queue", lambda: lifecycle.check_queue(allocation, deadline, release=True), "matched"),
              ("gpu", lambda: lifecycle.check_gpu(allocation, deadline), "empty"),
              ("cvd", lambda: lifecycle.check_cvd(allocation, deadline, release=True), "clear"))
    for name, action, field in checks:
        receipt = lifecycle._observe(directory / f"{label}_{name}.json", action)
        require(receipt[field] is True, "resource not clear: " + name)


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True, "Main-only controller")
    started, entered_wall = time.monotonic(), time.time()
    deadline = started + TOTAL_SECONDS
    root = Path(root)
    write(root / "controller_started.json", {"plan_sha256": plan_sha256, "started": started, "deadline": deadline})
    runtime = None
    try:
        time.sleep(DETACH_SECONDS)
        plan, bound = verify(root, plan_sha256)
        runtime, _, _, _, _, _, allocation = bound
        runtime.offline()
        require(entered_wall + TOTAL_SECONDS <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "six-hour finish margin")
        (root / "run").mkdir()
        for state in STATES:
            directory = root / "run" / state
            directory.mkdir()
            process, expected, errors, events = None, None, [], []
            try:
                resources(allocation, deadline - COLLECTION_SECONDS, directory, "pre")
                worker_deadline = min(time.monotonic() + runtime.READOUT_SECONDS, deadline - COLLECTION_SECONDS - CLEANUP_SECONDS)
                lifecycle.remaining(worker_deadline)
                argv = [allocation["python"], "-B", str(SELF), "worker", "--root", str(root), "--plan-sha256", plan_sha256,
                        "--state", state, "--deadline", str(worker_deadline), "--allow-gpu"]
                environment = dict(os.environ, CUDA_VISIBLE_DEVICES=allocation["gpu_uuid"],
                                   PYTHONPATH=str(SELF.parent.parent), PYTHONDONTWRITEBYTECODE="1")
                with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
                    process = subprocess.Popen(argv, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
                    write(directory / "spawn.json", {"pid": process.pid, "argv": argv, "deadline": worker_deadline})
                    candidate = lifecycle.identity(process.pid)
                    require(candidate["pid"] == candidate["pgid"] == candidate["sid"] == process.pid and candidate["uid"] == allocation["uid"]
                            and candidate["boot_id"] == allocation["boot_id"], "unknown worker identity; no cleanup permission")
                    expected = candidate
                    write(directory / "launch.json", {"identity": expected, "plan_sha256": plan_sha256, "state": state})
                    require(process.wait(timeout=lifecycle.remaining(worker_deadline)) == 0, "worker nonzero")
            except BaseException as error:
                errors.append({"type": type(error).__name__, "error": str(error)})
            finally:
                if process is not None:
                    try:
                        require(expected is not None, "unknown identity: cleanup forbidden")
                        release = lifecycle.cleanup_owned(process, expected, deadline - COLLECTION_SECONDS, events)
                        require(release["owned_group_released"] is True and release["identity"] == expected, "owned release mismatch")
                        write(directory / "released.json", release)
                    except BaseException as error:
                        errors.append({"type": type(error).__name__, "error": str(error)})
                    write(directory / "exit.json", {"returncode": process.poll(), "identity": expected, "events": events,
                          "signal": -process.returncode if process.returncode is not None and process.returncode < 0 else None})
                    try:
                        resources(allocation, deadline - COLLECTION_SECONDS, directory, "post")
                    except BaseException as error:
                        errors.append({"type": type(error).__name__, "error": str(error)})
            if errors:
                write(directory / "stage_failure.json", errors)
                raise ValueError("state failed: " + state)
        plan, bound = verify(root, plan_sha256)
        stages = validate_completed(plan, plan_sha256, bound)
        lifecycle.remaining(deadline - COLLECTION_SECONDS)
        write(root / "capture_complete.json", {"plan_sha256": plan_sha256, "stages": stages, "calls": 96,
              "scored": False, "deadline": deadline, "elapsed_seconds": time.monotonic() - started})
        return {"status": "ALL_CAPTURES_CLOSED_UNSCORED", "completion_sha256": lifecycle.file_hash(root / "capture_complete.json")}
    except BaseException as error:
        if runtime is not None:
            runtime.failure(root / "controller_failure.json", error)
        else:
            write(root / "controller_failure.json", {"error": str(error), "type": type(error).__name__})
        raise


def validate_completed(plan, plan_sha256, bound):
    runtime, _, parent, probe, adapter, files, allocation = bound
    root, stages, identities = Path(plan["root"]), {}, []
    calls = read(root / "calls.json")
    for state in STATES:
        directory = root / "run" / state
        require(not (directory / "failure.json").exists() and not (directory / "stage_failure.json").exists(), "failed state")
        launch, started, released, exited = (read(directory / name) for name in ("launch.json", "started.json", "released.json", "exit.json"))
        expected = launch["identity"]
        lifecycle._identity_schema(expected)
        spawn = read(directory / "spawn.json")
        require(expected["pid"] == expected["pgid"] == expected["sid"] == spawn["pid"]
                and expected["uid"] == allocation["uid"] and expected["boot_id"] == allocation["boot_id"], "verified isolated allocated identity")
        require(expected == started["identity"] == released["identity"] == exited["identity"]
                and released["owned_group_released"] is True and type(exited["returncode"]) is int and exited["returncode"] == 0
                and started["plan_sha256"] == launch["plan_sha256"] == plan_sha256
                and started["state"] == launch["state"] == state, "native process/exit/release join")
        identities.append(expected["pid"])
        route = None if state == "OFF" else {"name": "level1_skill", "id": 1, "path": adapter}
        identity = read(directory / "identity.json")
        require(identity == {"kind": "NATIVE", "worker": expected, "state": state, "original_plan": plan["spec"]["original_plan"],
                "model": parent["model"], "model_files": parent["model_files"], "adapter_files": files if state == "post" else {},
                "route": route, "engine": runtime.ENGINE, "params": runtime.PARAMS}, "captured native identity/route")
        close, load, closed = (read(directory / name) for name in ("close.json", "load.json", "closed.json"))
        require(close["calls"] == closed["calls"] == 48 and close["shutdown"] == {"source": plan["spec"]["shutdown_binding"], "shutdown_returned": True}
                and load["route"] == route and close["ended"] <= spawn["deadline"], "48 calls and bounded explicit engine close")
        for label in ("pre", "post"):
            for name, field in (("queue", "matched"), ("gpu", "empty"), ("cvd", "clear")):
                require(read(directory / f"{label}_{name}.json")["value"][field] is True, "resource custody not clear")
        names = {"identity.json", "load.json", "close.json"} | {call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")}
        require(set(closed["files"]) == names and {path.name for path in directory.glob("*.response.json")} == {call["call_id"] + ".response.json" for call in calls}, "exact capture inventory")
        for name, checksum in closed["files"].items():
            require(runtime.digest(directory / name) == checksum, "capture file drift")
        for call in calls:
            require(read(directory / (call["call_id"] + ".request.json")) == call, "prepared/captured request join")
            response = read(directory / (call["call_id"] + ".response.json"))
            require(response["lora_request"] == route and load["started"] <= load["ready"] <= response["started"] <= response["ended"] <= close["ended"], "route/cold-load chronology")
            probe.validate_response(call, response)
        stages[state] = runtime.tree(directory)
    require(len(set(identities)) == 2, "distinct fresh OFF/post processes")
    return stages


def collect(root, plan_sha256, completion_sha256, out):
    root, out = Path(root), Path(out)
    require(root.is_absolute() and out.is_absolute() and out.parent.resolve() == out.parent
            and not out.exists() and not root.is_relative_to(out) and not out.is_relative_to(root), "fresh external collection")
    complete = read(pin_file({"path": str(root / "capture_complete.json"), "sha256": completion_sha256}))
    require(complete["plan_sha256"] == plan_sha256 and complete["calls"] == 96 and complete["scored"] is False
            and not (root / "controller_failure.json").exists(), "complete unscored 96-call custody")
    spec = read(pin_file({"path": str(root / "plan.json"), "sha256": plan_sha256}))["spec"]
    runtime = load_module(spec["runtime"], "prediction_transfer_runtime")
    write(root.with_name(root.name + ".collection_claim.json"), {"plan_sha256": plan_sha256, "out": str(out), "retry": False})
    out.mkdir()
    try:
        with runtime.budget(lifecycle.remaining(complete["deadline"], COLLECTION_SECONDS)):
            plan, bound = verify(root, plan_sha256)
            require(validate_completed(plan, plan_sha256, bound) == complete["stages"], "completed stage inventory drift")
            _, material, parent, _, _, _, allocation = bound
            require(time.time() <= allocation["lease_end"] - max(LEASE_MARGIN, allocation["lease_margin_seconds"]), "collection lease margin")
            _, rows = material_rows(material, parent)
            cells = {}
            for state in STATES:
                scored = []
                for index, row in enumerate(rows):
                    path = root / "run" / state / f"call_{index:02d}.response.json"
                    response = read(path)
                    score = material.score_response(row, response["text"], response["finish_reason"],
                                                    original_material_path=parent["specification"]["material"]["path"])
                    runtime.validate_score(score, response["finish_reason"])
                    scored.append({"row_id": row["row_id"], "case_id": row["case_id"], "case": row["case"], "view": row["view"],
                        "raw": response["text"], "finish_reason": response["finish_reason"], "response_sha256": runtime.digest(path), "score": score,
                        "prompt_tokens": len(response["actual_prompt_token_ids"]), "output_tokens": len(response["output_token_ids"]),
                        "generation_seconds": response["ended"] - response["started"]})
                cells[state] = scored
            summaries, contrasts, costs = {}, {}, {}
            for state in STATES:
                summaries[state] = {}
                for view in VIEWS:
                    selected = [row for row in cells[state] if row["view"] == view]
                    summaries[state][view] = {"denominator": 24, "content_correct": sum(row["score"]["content_correct"] for row in selected),
                        "strict": sum(row["score"]["strict"] for row in selected), "formats": dict(Counter(row["score"]["format"] for row in selected)),
                        "finish_reasons": dict(Counter(row["finish_reason"] for row in selected)),
                        "groups": {case: {"denominator": 6, "content_correct": sum(row["score"]["content_correct"] for row in selected if row["case"] == case)}
                                   for case in sorted({row["case"] for row in selected})}}
                load = read(root / "run" / state / "load.json")
                costs[state] = {key: sum(row[key] for row in cells[state]) for key in ("prompt_tokens", "output_tokens", "generation_seconds")}
                costs[state]["load_seconds"] = load["ready"] - load["started"]
            for view in VIEWS:
                pairs = [(before, after) for before, after in zip(cells["OFF"], cells["post"]) if before["view"] == view]
                contrasts[view] = {"denominator": 24,
                    "post_minus_OFF": summaries["post"][view]["content_correct"] - summaries["OFF"][view]["content_correct"],
                    "wins": [after["row_id"] for before, after in pairs if after["score"]["passed"] and not before["score"]["passed"]],
                    "losses": [after["row_id"] for before, after in pairs if before["score"]["passed"] and not after["score"]["passed"]]}
            report = {"schema": SCHEMA + "/scores", "claim": CLAIM, "learner_seed": plan["learner_seed"], "cells": cells,
                "summaries": summaries, "post_minus_OFF": contrasts, "costs": costs,
                "minimal_minus_full": {state: summaries[state]["MINIMAL"]["content_correct"] - summaries[state]["FULL"]["content_correct"] for state in STATES},
                "plan_sha256": plan_sha256, "completion_sha256": completion_sha256, "calls": 96, "fits": 0, "updates": 0,
                "automatic_pass": False, "scientific_pass": None, "controller_elapsed_seconds": complete["elapsed_seconds"]}
            write(out / "scores.json", report)
            write(out / "collection.json", {"scores_sha256": runtime.digest(out / "scores.json"), "completion_sha256": completion_sha256,
                  "elapsed_since_controller_start": TOTAL_SECONDS - lifecycle.remaining(complete["deadline"]), "plan_sha256": plan_sha256})
            return {"status": "COLLECTED_DEV_ONLY", "scores_sha256": runtime.digest(out / "scores.json"), "collection_sha256": runtime.digest(out / "collection.json")}
    except BaseException as error:
        runtime.failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "controller", "worker", "collect"):
        child = commands.add_parser(name)
        child.add_argument("--root", required=True)
        if name == "prepare":
            child.add_argument("--spec-path", required=True)
            child.add_argument("--spec-sha256", required=True)
            child.add_argument("--allow-native", action="store_true")
        else:
            child.add_argument("--plan-sha256", required=True)
        if name in ("controller", "worker"):
            child.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            child.add_argument("--state", choices=STATES, required=True)
            child.add_argument("--deadline", type=float, required=True)
        if name == "collect":
            child.add_argument("--completion-sha256", required=True)
            child.add_argument("--out", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    result = globals()[command](**args)
    if result is not None:
        print(lifecycle.driver.native.canonical(result).decode())


if __name__ == "__main__":
    main()
