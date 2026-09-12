"""Main-owned continuous reservation for six already prepared conditional phases."""
import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

ORDER = tuple((state, phase) for state in ("OFF", "AUTH", "DERANGED") for phase in ("generate", "score"))
SECONDS, CLEANUP, START_WINDOW = 4500, 140, 750


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def fresh(path):
    require(not path.exists() and not path.is_symlink(), "existing output; no retry/resume: " + str(path))


def manifest(source, root, pin, driver_pin=None):
    require(digest(root / "manifest.json") == pin, "Main manifest pin changed")
    record = read(root / "manifest.json")
    expected_driver = driver_pin if driver_pin is not None else record.get("driver_sha256")
    require(record["source_root"] == str(source) and expected_driver == digest(__file__), "source/driver pin changed")
    require(record["status"] == "NATIVE_CPU_PREPARED_NOT_LAUNCHED" and record["generation_calls"] == 672 and
        record["candidate_forwards"] == 576, "native preparation/workload declaration differs")
    require(record["source_hashes"]["conditional_behavior_readout.py"] ==
        digest(source / "organism_v6/conditional_behavior_readout.py"), "readout source changed")
    require([(row["state"], row["phase"]) for row in record["phases"]] == list(ORDER), "fixed six-phase order required")
    require(record["controller_seconds"] == SECONDS and record["external_collection_margin_seconds"] == 300 and
        record["total_ceiling_seconds"] == 5400 and math.isfinite(record["prior_fit_full_reservation_seconds"]) and
        0 <= record["prior_fit_full_reservation_seconds"] <= 5400 - SECONDS - 300, "aggregate allocation exceeds ceiling")
    for row in record["phases"]:
        phase_root = root / (row["state"] + "_" + row["phase"])
        require(row["root"] == str(phase_root) and phase_root.resolve(strict=True) == phase_root and
            digest(phase_root / "plan.json") == row["plan_sha256"] == read(phase_root / "plan.sha256.json")["sha256"],
            "phase root/plan pin changed")
    return record


def import_api(source):
    sys.path.insert(0, str(source))
    api = importlib.import_module("organism_v6.conditional_behavior_readout")
    require(Path(api.__file__).resolve().parent.parent == source and api.base.REPO == source, "wrong imported source")
    return api


def verify(source, root, pin, driver_pin=None):
    record = manifest(source, root, pin, driver_pin)
    fresh(root / "controller")
    api = import_api(source)
    require((api.base.WORKER_SECONDS, api.base.LOAD_SECONDS, api.base.CALL_SECONDS, api.base.CLEANUP_RESERVE) ==
        (600, 180, 120, CLEANUP), "native supervisor bounds changed")
    require(api.sources() == record["source_hashes"] and api.ASSAY_VERSION == record["assay_version"], "source/assay changed")
    plans = []
    for row in record["phases"]:
        phase_root = Path(row["root"])
        fresh(phase_root / "run")
        plan, _, _ = api.verify(phase_root)
        require((plan["state"], plan["phase"]) == (row["state"], row["phase"]) and
            all(plan[key] == record[key] for key in ("source_hashes", "model_files", "material_inventory")), "phase contract differs")
        require(math.isfinite(plan["lease_end"]), "invalid sealed lease")
        plans.append(plan)
    common = ("device", "model", "model_files", "material", "material_inventory", "material_manifest_sha256",
              "candidate_sha256", "source_hashes", "controls", "worker_seconds", "resource_budget", "lease_end")
    require(all(all(plan[key] == plans[0][key] for key in common) for plan in plans), "phases disagree on shared contract")
    require(plans[0]["device"] == record["device"], "Main manifest device differs")
    for index in (0, 2, 4):
        require(all(plans[index][key] == plans[index + 1][key] for key in ("adapter", "adapter_files")), "generation/score adapter differs")
    require(plans[0]["adapter"] is None and plans[0]["adapter_files"] == {} and
        plans[2]["adapter"] and plans[4]["adapter"] and plans[2]["adapter"] != plans[4]["adapter"], "OFF/fit state identities differ")
    output = root / "controller"
    for value in (str(source), plans[0]["model"], plans[0]["material"], plans[2]["adapter"], plans[4]["adapter"]):
        protected = Path(value).resolve(strict=True)
        require(output != protected and output not in protected.parents and protected not in output.parents, "output overlaps inputs")
    manifest(source, root, pin, driver_pin)
    return record, api, plans


def bounds(started, deadline, lease_end, plans):
    values = [started, deadline, lease_end] + [plan["lease_end"] for plan in plans]
    require(all(math.isfinite(value) for value in values), "nonfinite time bound")
    return min(started + SECONDS, deadline, lease_end - 10, *(plan["lease_end"] - 10 for plan in plans))


def successful(receipt, device):
    require(all(receipt.get(key) is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
        receipt.get("returncode") == 0 and receipt.get("error") is None and receipt.get("device") == device and
        math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0, "worker/cleanup failure")


def evidence(record, api, device):
    receipts, unaccounted = {}, []
    for row in record["phases"]:
        worker = Path(row["root"]) / "run/worker"
        if (worker / "supervision.json").is_file():
            receipt = read(worker / "supervision.json")
            require(math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0, "invalid worker cost")
            receipts[row["state"] + "_" + row["phase"]] = receipt
        elif (worker / "process.json").exists():
            unaccounted.append(str(worker))
    released = not unaccounted and api.base.supervisor.gpu_processes_absent(device) is True and all(
        all(receipt.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
        for receipt in receipts.values())
    return receipts, unaccounted, released


def run(source, root, pin, deadline, lease_end, allow_gpu=False, clock=None, driver_pin=None):
    require(allow_gpu, "Main allocation and --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    record = manifest(source, root, pin, driver_pin)
    prepared = [read(Path(row["root"]) / "plan.json") for row in record["phases"]]
    device = prepared[0]["device"]
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == device, "wrong continuous CUDA reservation")
    effective = bounds(started, deadline, lease_end, prepared)
    require(effective - time.time() >= START_WINDOW, "less than750s available before preflight")
    output, api, error, summary = None, None, None, None
    attempts, reductions = [], []

    def interrupted(number, frame):
        raise RuntimeError(f"controller stop/cleanup boundary: {number}")

    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - CLEANUP))
    try:
        record, api, plans = verify(source, root, pin, driver_pin)
        require(effective - time.time() >= START_WINDOW, "preflight exhausted phase window")
        output = root / "controller"
        fresh(output)
        output.mkdir()
        (output / "phases").mkdir()
        reservation = dict(controller_pid=os.getpid(), device=device, started=started, effective_deadline=effective,
            supplied_deadline=deadline, real_lease_end=lease_end, manifest_sha256=pin, driver_sha256=digest(__file__),
            controller_seconds=SECONDS, cleanup_reserve_seconds=CLEANUP, phase_start_minimum_seconds=START_WINDOW,
            scope="continuous selected CUDA reservation including imports/CPU/gaps/cleanup; external full release remains Main-owned")
        write(output / "reservation.json", reservation)
        for row in record["phases"]:
            manifest(source, root, pin, driver_pin)
            require(os.environ.get("CUDA_VISIBLE_DEVICES") == device, "CUDA reservation changed")
            require(effective - time.time() >= START_WINDOW, "less than750s remain; do not begin next phase")
            name = row["state"] + "_" + row["phase"]
            phase_root = Path(row["root"])
            fresh(phase_root / "run")
            attempt = dict(name=name, root=str(phase_root), plan_sha256=row["plan_sha256"], started=time.time())
            attempts.append(attempt)
            try:
                receipt = api.run(phase_root, allow_gpu=True)
                attempt["supervision"] = receipt
                successful(receipt, device)
                require(receipt == read(phase_root / "run/worker/supervision.json"), "returned/stored receipt differs")
                attempt["process"] = read(phase_root / "run/worker/process.json")
                reduction = api.reduce(phase_root)
                attempt["reduction"] = reduction
                require(reduction.get("complete") is True and reduction.get("status") == "COMPLETE_PHASE" and
                    (reduction["state"], reduction["phase"]) == (row["state"], row["phase"]) and
                    reduction["plan_sha256"] == row["plan_sha256"] and
                    reduction["reserved_seconds"] == receipt["reserved_seconds"], "phase incomplete; not a scientific zero")
                manifest(source, root, pin, driver_pin)
                reductions.append(reduction)
            except BaseException as failure:
                attempt["error"] = dict(type=type(failure).__name__, message=str(failure))
                raise
            finally:
                attempt["ended"] = time.time()
                write(output / "phases" / (name + ".json"), attempt)
        require(len(reductions) == 6, "six complete phases required")
        summary = api.summarize(reductions)
        write(output / "summary.json", summary)
        require(summary.get("complete") is True, "summary technically incomplete")
        manifest(source, root, pin, driver_pin)
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            if output is not None and (output / "reservation.json").is_file():
                receipts, unaccounted, released = {}, [], False
                try:
                    receipts, unaccounted, released = evidence(record, api, device)
                    if error is None:
                        for attempt in attempts:
                            successful(receipts[attempt["name"]], device)
                            require(receipts[attempt["name"]] == attempt["supervision"], "completed receipt changed")
                except Exception as failure:
                    error = error or dict(type=type(failure).__name__, message=str(failure))
                ended = time.time()
                elapsed = time.monotonic() - monotonic
                complete = error is None and len(reductions) == len(receipts) == 6 and released and ended <= effective and elapsed <= SECONDS
                terminal = dict(reservation, status="COMPLETE" if complete else "PARTIAL", error=error, ended=ended,
                    reserved_seconds=elapsed, worker_reserved_seconds=sum(r["reserved_seconds"] for r in receipts.values()),
                    attempts=attempts, completed_phases=len(reductions), supervision=receipts, unaccounted_processes=unaccounted,
                    release_verified=released, deadline_met=ended <= effective, summary=summary,
                    prior_fit_full_reservation_seconds=record["prior_fit_full_reservation_seconds"],
                    external_collection_margin_seconds=300, total_ceiling_seconds=5400,
                    counts_used_for_queue_selection=False, retries=0, supplies_l1_verdict=False,
                    full_release_note="worker process absence is not fullcheck_free; Main collects actual end-to-end reservation")
                write(output / "terminal.json", terminal)
        finally:
            for number, handler in handlers.items():
                signal.signal(number, handler)
    require(output is not None and error is None and terminal["status"] == "COMPLETE",
        "PARTIAL or preflight failed; preserve all evidence, no retry/resume: " + str(error))
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("verify", "run"))
    for name in ("source-root", "runroot", "manifest-sha256", "driver-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    source, root = Path(args.source_root).expanduser().resolve(strict=True), Path(args.runroot).expanduser().resolve(strict=True)
    if args.stage == "verify":
        record, _, plans = verify(source, root, args.manifest_sha256, args.driver_sha256)
        result = dict(status="SIX_PREPARED_PHASES_VERIFIED_NOT_LAUNCHED", device=plans[0]["device"],
            manifest_sha256=args.manifest_sha256, phase_order=[state + "_" + phase for state, phase in ORDER],
            fit_controller_margin_seconds=record["prior_fit_full_reservation_seconds"] + SECONDS + 300)
    else:
        require(args.deadline is not None and args.lease_end is not None, "run requires --deadline and --lease-end")
        result = run(source, root, args.manifest_sha256, args.deadline, args.lease_end, args.allow_gpu, clock, args.driver_sha256)
    print(json.dumps(result, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
