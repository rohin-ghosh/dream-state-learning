"""Prospectively frozen actual-record write -> fresh OFF/P_ON/A_ON readout.

prepare is CPU-only and does not inspect fits/readout outcomes. evaluate and
_worker require Main's --allow-gpu. No legacy material, training, or promotion.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import signal
import sys
import threading
import time


SELF = Path(__file__).resolve()
CELLS = ("OFF", "P_ON", "A_ON")
CONTROLLER_SECONDS = 1800
CLEANUP_SECONDS = 140
LEASE_MARGIN = 21600


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read(path):
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object, parse_constant=reject)


def write_json(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def absolute_python(value):
    path = os.path.abspath(value)
    require(Path(path).is_file() and os.access(path, os.X_OK), "executable interpreter required")
    return path


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timezone-aware time required")
    return parsed.timestamp()


def load_driver(path):
    path = Path(path).expanduser().resolve(strict=True)
    name = "astra_write_" + digest(path)
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def diagnostic_module(source_root):
    root = Path(source_root).resolve(strict=True)
    sys.path.insert(0, str(root)) if str(root) not in sys.path else None
    module = importlib.import_module("organism_v6.rulegame_parenting_diagnostic")
    require(Path(module.__file__).resolve().parents[1] == root, "imported source-root differs")
    return module


def protocol(diagnostic):
    require(diagnostic.CELLS == CELLS and diagnostic.WORKER_SECONDS == 600
            and diagnostic.CLEANUP_RESERVE == CLEANUP_SECONDS and diagnostic.RESERVED_SECONDS == CONTROLLER_SECONDS,
            "frozen supervisor/cell semantics differ")
    tasks = diagnostic.schedule()["evaluation"]
    require(tasks == [f"rule{rule}/astra-minimum-20260912/readout" for rule in range(2, 6)], "evaluation schedule changed")
    return dict(name="actual_record_parent_free_readout_v1", interaction_protocol="interaction_v3",
        cells=list(CELLS), tasks=tasks, quiz_items_per_task=6, wake_responses_per_task=5,
        limits=diagnostic.LIMITS["evaluation"], tokens={role: diagnostic.TOKENS[role] for role in ("wake", "record")},
        gen_seed=diagnostic.GEN_SEED, temperature=.7, max_model_len=diagnostic.MAX_MODEL_LEN,
        parent_calls=0, restatement_calls=0, task_prefix="", record_calls=True,
        record_feedback_into_wake=False, record_training=False, task_history="fresh per task; current task only",
        score="unchanged first quiz accuracy; invalid/absent quiz stays zero; fixed denominator four",
        contrasts=["P_minus_OFF", "A_minus_OFF", "P_minus_A"], shared_off=True,
        inference="post-treatment selected material; one shared OFF; exploratory only",
        exclusions="formation rules 0/1 excluded; no confirmation data or new confirmation selection",
        max_calls=96, max_generated_tokens=27600, controller_seconds=CONTROLLER_SECONDS,
        worker_seconds=600, cleanup_seconds=CLEANUP_SECONDS, call_seconds=diagnostic.CALL_SECONDS,
        load_seconds=diagnostic.LOAD_SECONDS, lease_margin_seconds=LEASE_MARGIN,
        claim_boundary=diagnostic.CLAIM_BOUNDARY)


def prepare(write_root, write_plan_sha256, write_driver, out, deadline, lease_end):
    driver = load_driver(write_driver)
    origin, written, diagnostic, _, _ = driver.checked_plan(write_root, write_plan_sha256)
    driver.verify_inputs(written, diagnostic)
    require(read(Path(written["formation_root"]) / "plan.json")["protocol"] == "interaction_v3", "v3 lineage required")
    output = driver.local_path(out, fresh=True)
    require(output.parent == origin.parent and output != origin, "fresh sibling readout root required")
    for protected in (written["model"], written["source_root"], written["formation_root"], written["main_audit_path"], write_driver, SELF):
        require(not driver.overlaps(output, Path(protected).resolve()), "readout overlaps protected input")
    end, lease = timestamp(deadline), timestamp(lease_end)
    require(time.time() + CONTROLLER_SECONDS < end <= lease - LEASE_MARGIN, "need 1800s and six-hour lease margin")
    python = absolute_python(sys.executable)
    require(python == absolute_python(written["python"]), "invoke prepare with exact write-plan venv interpreter; do not resolve symlink")
    plan = dict(schema=1, out=str(output), write_root=str(origin), write_plan_sha256=write_plan_sha256,
        write_driver=str(Path(write_driver).resolve()), write_driver_sha256=digest(write_driver),
        source_root=written["source_root"], source_pins=written["implementation"],
        model=written["model"], model_files=written["model_files"], device=written["device"], python=python,
        protocol=protocol(diagnostic), deadline=end, supplied_lease_end=lease, lease_cutoff=lease-LEASE_MARGIN,
        self_path=str(SELF), self_sha256=digest(SELF), write_status="NOT_INSPECTED_UNTIL_EVALUATE",
        lease_basis="Main-supplied real expiry; not control-plane verification")
    output.mkdir()
    write_json(output / "plan.json", plan)
    frozen = digest(output / "plan.json")
    write_json(output / "plan.sha256.json", dict(sha256=frozen))
    return dict(status="PROTOCOL_FROZEN_WRITES_NOT_INSPECTED", root=str(output), plan_sha256=frozen)


def checked_plan(root, plan_sha256):
    root = Path(root).expanduser().resolve(strict=True)
    require(digest(root / "plan.json") == plan_sha256, "readout plan changed")
    plan = read(root / "plan.json")
    require(plan["out"] == str(root) and plan["self_path"] == str(SELF) and plan["self_sha256"] == digest(SELF), "readout implementation/root changed")
    require(digest(plan["write_driver"]) == plan["write_driver_sha256"], "write driver changed")
    require(all(digest(path) == expected for path, expected in plan["source_pins"].items()), "source bytes changed")
    diagnostic = diagnostic_module(plan["source_root"])
    require(plan["protocol"] == protocol(diagnostic), "prospective readout protocol changed")
    require(plan["deadline"] <= plan["lease_cutoff"] == plan["supplied_lease_end"]-LEASE_MARGIN, "lease bounds changed")
    require(absolute_python(sys.executable) == plan["python"], "controller interpreter differs from native venv")
    return root, plan, diagnostic


def accepted_writes(plan):
    driver = load_driver(plan["write_driver"])
    root, written, diagnostic, _, trainer = driver.checked_plan(plan["write_root"], plan["write_plan_sha256"])
    driver.verify_inputs(written, diagnostic)
    require(written["model"] == plan["model"] and written["model_files"] == plan["model_files"]
            and written["source_root"] == plan["source_root"] and written["implementation"] == plan["source_pins"]
            and written["device"] == plan["device"] and absolute_python(written["python"]) == plan["python"], "write lineage differs")
    require(not (root / "run" / "failure.json").exists(), "failed/partial writes cannot be evaluated")
    result_path = root / "run" / "result.json"
    result = read(result_path)
    require(result["status"] == "PAIRED_ADAPTERS_SAVED_READOUT_PENDING" and set(result["arms"]) == {"P", "A"}, "both successful writes required")
    fits = {}
    for arm in ("P", "A"):
        fit = root / "fits" / arm
        require(read(fit / "manifest.json")["files"] == diagnostic.tree_hashes(fit, ("manifest.json",)), "fit seal changed")
        receipt = driver.validate_fit(root, arm, written, diagnostic, trainer)
        require(read(fit / "receipt.json") == receipt, "fit receipt changed")
        supervision_path = root / "run" / arm / "supervision.json"
        supervision = read(supervision_path)
        require(supervision["ok"] and supervision["reservation_release_verified"], "write cleanup unverified")
        sealed = dict(receipt, fit_manifest_sha256=digest(fit / "manifest.json"), supervision_sha256=digest(supervision_path))
        require(result["arms"][arm] == sealed, "completed pair receipt differs")
        fits[arm] = sealed
    return dict(write_plan_sha256=plan["write_plan_sha256"], result_sha256=digest(result_path), fits=fits)


SPEC_KEYS = {"schema", "cell", "data", "model", "model_files", "adapter", "adapter_files", "device", "python",
             "source_root", "source_pins", "self_sha256", "protocol", "hard_end", "nonce"}


def worker_spec(root, plan, lineage, cell, hard_end):
    fit = lineage["fits"][cell[0]] if cell != "OFF" else None
    return dict(schema=1, cell=cell, data=str(root / "run" / cell / "data"),
        model=plan["model"], model_files=plan["model_files"], adapter=fit["adapter"] if fit else None,
        adapter_files=fit["files"] if fit else {}, device=plan["device"], python=plan["python"],
        source_root=plan["source_root"], source_pins=plan["source_pins"], self_sha256=plan["self_sha256"],
        protocol=plan["protocol"], hard_end=hard_end, nonce=secrets.token_hex(16))


@contextmanager
def work_window(hard_end):
    require(threading.current_thread() is threading.main_thread() and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "exclusive main-thread timer required")
    remaining = hard_end-time.time()-CLEANUP_SECONDS
    require(remaining > 0, "controller cleanup reserve exhausted")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("readout controller work window exhausted")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@contextmanager
def supervised_window(hard_end):
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        yield
    finally:
        remaining = hard_end-time.time()-CLEANUP_SECONDS
        if remaining > 0:
            signal.setitimer(signal.ITIMER_REAL, remaining)


@contextmanager
def owning_process(stage, hard_end):
    until = time.monotonic()+5
    while not (stage / "process.json").exists() and time.monotonic() < until:
        time.sleep(.05)
    receipt = read(stage / "process.json")
    require(receipt["pid"] == receipt["pgid"] == os.getpid() == os.getpgrp() == os.getsid(0), "fresh owning supervisor process required")
    parent = os.getppid()
    stop = threading.Event()
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent or time.time() >= hard_end-10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    def interrupted(signum, frame):
        raise RuntimeError(f"readout worker interrupted: {signum}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    threading.Thread(target=watch, daemon=True).start()
    try:
        yield
    finally:
        stop.set()
        for number, handler in handlers.items():
            signal.signal(number, handler)


def close_native(backend):
    from organism_v6.model_backend import close_backend
    return close_backend(backend.backend if backend is not None else None)


def verify_worker_bytes(spec, diagnostic):
    require(all(digest(path) == expected for path, expected in spec["source_pins"].items())
            and digest(SELF) == spec["self_sha256"], "worker source changed")
    require(diagnostic.model_hashes(spec["model"]) == spec["model_files"], "worker base changed")
    if spec["adapter"]:
        require(diagnostic.tree_hashes(spec["adapter"]) == spec["adapter_files"], "worker adapter changed")


def worker(spec, spec_sha256, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before worker work")
    spec_path = Path(spec).resolve(strict=True)
    require(digest(spec_path) == spec_sha256, "worker spec changed")
    spec = read(spec_path)
    require(set(spec) == SPEC_KEYS and spec["cell"] in CELLS, "worker spec extra context/invalid fields")
    require((spec["adapter"] is None and spec["adapter_files"] == {}) if spec["cell"] == "OFF"
            else bool(spec["adapter"] and spec["adapter_files"]), "OFF/ON adapter mismatch")
    diagnostic = diagnostic_module(spec["source_root"])
    require(spec["protocol"] == protocol(diagnostic), "worker protocol changed")
    require(absolute_python(sys.executable) == spec["python"] and os.environ.get("CUDA_VISIBLE_DEVICES") == spec["device"], "worker interpreter/device mismatch")
    require(time.time() < spec["hard_end"]-CLEANUP_SECONDS, "worker window exhausted")
    stage = spec_path.parent / spec["cell"]
    data = stage / "data"
    require(spec_path.name == spec["cell"] + ".spec.json" and str(data) == spec["data"] and not data.exists(), "fixed fresh worker output required")
    with owning_process(stage, spec["hard_end"]):
        verify_worker_bytes(spec, diagnostic)
        data.mkdir()
        write_json(data / "isolation.json", dict(pid=os.getpid(), pgid=os.getpgrp(), parent_pid=os.getppid(),
            spec_sha256=spec_sha256, parent_calls=0, task_prefix="", record_training=False,
            scope="fresh process and exact replayed prompts; not OS-level filesystem isolation"))
        backend = None
        try:
            backend = diagnostic.NativeBackend(spec["model"], spec["adapter"])
            identity = diagnostic.expected_identity(spec, spec["adapter"])
            require(backend.identity() == identity, "native backend identity differs")
            write_json(data / "identity.json", dict(stage="evaluation", cell=spec["cell"], backend=identity,
                model_files=spec["model_files"], protocol="interaction_v3"))
            write_json(data / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
            calls = diagnostic.Calls(data / "calls", backend, "evaluation", identity, "interaction_v3")
            events = diagnostic.Events(data / "events.jsonl")
            result = diagnostic.run_evaluation(calls, events, spec["cell"])
            write_json(data / "result.json", result)
            write_json(data / "usage.json", diagnostic.usage(data))
            diagnostic.audit_native_calls(backend.backend.tok, data)
            write_json(data / "native_audit.json", dict(ok=True, calls=calls.count, scope="actual rendered prompts/input IDs/decoded output IDs"))
        except BaseException as error:
            write_json(data / "failure.json", dict(error=type(error).__name__ + ": " + str(error)))
            raise
        finally:
            closed, failure = False, None
            try:
                closed = close_native(backend)
            except Exception as error:
                failure = str(error)
            write_json(data / "backend.cleanup.json", dict(closed=closed, error=failure))
            require(closed is True, "backend cleanup unverified")
        verify_worker_bytes(spec, diagnostic)
        require(digest(spec_path) == spec_sha256, "worker spec changed during evaluation")
        diagnostic.capture_manifest(data)
        return dict(status="CAPTURED", cell=spec["cell"])


def audit_cell(root, plan, lineage, cell, diagnostic):
    data = root / "run" / cell / "data"
    adapter = lineage["fits"][cell[0]]["adapter"] if cell != "OFF" else None
    header = read(data / "identity.json")
    require(header["stage"] == "evaluation" and header["cell"] == cell and header["model_files"] == plan["model_files"], "wrong cell/stage/base capture")
    audit = diagnostic.check_capture(data, diagnostic.expected_identity(plan, adapter), "interaction_v3")
    require(audit["ok"], "readout replay failed: " + str(audit["failures"]))
    require(read(data / "native_audit.json")["ok"] and read(data / "backend.cleanup.json")["closed"], "native audit/cleanup missing")
    require(not (data / "failure.json").exists(), "failed capture")
    return audit


def evaluate(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "--allow-gpu required before controller work")
    started_wall, started = time.time(), time.monotonic()
    root, plan, diagnostic = checked_plan(root, plan_sha256)
    hard_end = min(started_wall+CONTROLLER_SECONDS, plan["deadline"], plan["lease_cutoff"])
    run = root / "run"
    run.mkdir()
    completed = {}
    try:
        with work_window(hard_end):
            lineage = accepted_writes(plan)
            write_json(run / "lineage.json", lineage)
            write_json(run / "controller.json", dict(plan_sha256=plan_sha256, started_wall=started_wall,
                hard_end=hard_end, cleanup_reserve=CLEANUP_SECONDS, pid=os.getpid()))
            for cell in CELLS:
                checked_plan(root, plan_sha256)
                require(accepted_writes(plan) == lineage, "paired write lineage changed")
                require(time.time() < hard_end-CLEANUP_SECONDS, "insufficient next-cell work window")
                spec_path = run / (cell + ".spec.json")
                write_json(spec_path, worker_spec(root, plan, lineage, cell, hard_end))
                spec_hash = digest(spec_path)
                command = [plan["python"], "-B", str(SELF), "_worker", "--spec", str(spec_path),
                           "--spec-sha256", spec_hash, "--allow-gpu"]
                with supervised_window(hard_end):
                    supervision = diagnostic.supervise(root, dict(model=plan["model"], device=plan["device"], lease_end=hard_end),
                        run / cell, command, run / cell / "data" / "calls")
                require(supervision["ok"] and supervision["reservation_release_verified"], "readout cleanup unverified")
                require(time.time() < hard_end-CLEANUP_SECONDS, "controller work window exhausted after cleanup")
                require(digest(spec_path) == spec_hash, "supervised worker spec changed")
                audit = audit_cell(root, plan, lineage, cell, diagnostic)
                write_json(run / cell / "provenance.json", audit)
                completed[cell] = dict(result=audit["result"], capture_sha256=digest(run / cell / "data" / "manifest.json"),
                    spec_sha256=spec_hash, supervision_sha256=digest(run / cell / "supervision.json"))
            checked_plan(root, plan_sha256)
            require(accepted_writes(plan) == lineage, "paired write lineage changed during readout")
            for cell, receipt in completed.items():
                require(digest(run / cell / "data" / "manifest.json") == receipt["capture_sha256"]
                        and digest(run / (cell + ".spec.json")) == receipt["spec_sha256"]
                        and digest(run / cell / "supervision.json") == receipt["supervision_sha256"], "earlier cell changed")
                audit_cell(root, plan, lineage, cell, diagnostic)
        require(time.monotonic()-started <= CONTROLLER_SECONDS and time.time() <= hard_end, "inclusive controller cap exceeded")
        means = {cell: receipt["result"]["mean_quiz_accuracy"] for cell, receipt in completed.items()}
        result = dict(status="COMPLETE_EXPLORATORY_READOUT", cells=completed,
            P_minus_OFF=means["P_ON"]-means["OFF"], A_minus_OFF=means["A_ON"]-means["OFF"], P_minus_A=means["P_ON"]-means["A_ON"],
            inference=plan["protocol"]["inference"], claim_boundary=diagnostic.CLAIM_BOUNDARY,
            controller_seconds=time.monotonic()-started, adaptation_test=False,
            semantic_nonleakage_certified=False, model_authentication_certified=False)
        write_json(run / "result.json", result)
        return result
    except BaseException as error:
        write_json(run / "failure.json", dict(error=type(error).__name__ + ": " + str(error),
            completed_cells=list(completed), retry=False, controller_seconds=time.monotonic()-started))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("write-root", "write-plan-sha256", "write-driver", "out", "deadline", "lease-end"):
        prep.add_argument("--"+name, required=True)
    evaluation = sub.add_parser("evaluate")
    for name in ("root", "plan-sha256"):
        evaluation.add_argument("--"+name, required=True)
    evaluation.add_argument("--allow-gpu", action="store_true")
    child = sub.add_parser("_worker")
    for name in ("spec", "spec-sha256"):
        child.add_argument("--"+name, required=True)
    child.add_argument("--allow-gpu", action="store_true")
    args = vars(parser.parse_args(argv))
    action = args.pop("action")
    result = {"prepare": prepare, "evaluate": evaluate, "_worker": worker}[action](**args)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
