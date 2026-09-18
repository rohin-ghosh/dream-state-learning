"""One fresh unchanged-boundary admission after a proven prelaunch drift denial."""

from copy import deepcopy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import time
import uuid


ROOT = Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt2")
OPERATOR_SHA = "fc960529e505d79e66ec92715535f770fc22a717210ec91c9dcfe0aea5775a87"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def drift_pids(report):
    reasons = report.get("blocking_reasons", [])
    require(report.get("clear") is False and report.get("scanner_euid") == 0
            and reasons and all(re.fullmatch(r"process_identity_drift:[0-9]+", reason) for reason in reasons),
            "only_actual_privileged_prelaunch_identity_drift_denial")
    return [int(reason.split(":")[1]) for reason in reasons]


def no_native_launch(directory):
    require(not any((directory / name).exists() for name in
                    ("LAUNCH.json", "NATIVE.log", "CONTAINMENT_VERIFIED.json", "ADMISSION_TIME.json", "EXIT.json")),
            "denial_before_any_native_or_containment_launch")


def source_operator():
    path = ROOT / "operator/node1_operator.py"
    specification = importlib.util.spec_from_file_location("r179_pinned_operator", path)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    require(loaded.sha(path) == OPERATOR_SHA, "exact_preceding_operator")
    loaded.authorize()
    cpu = loaded.read(Path(__file__).parent / "CPU.json", 1024 * 1024)
    require(cpu["returncode"] == 0 and cpu["passed"] >= 4
            and cpu["helper_sha256"] == loaded.sha(Path(__file__))
            and cpu["test_sha256"] == loaded.sha(Path(__file__).with_name("test_readmit_node1.py")),
            "actual_bound_readmission_CPU")
    return loaded


def readmit():
    operator = source_operator()
    base = operator.legacy()
    output = ROOT / "lanes/lane4"
    old_control = output / "control"
    request = operator.read(output / "STAGED.json")
    boundary = operator.read(output / "BOUNDARY.json")["saved"]
    retired = operator.read(output / "RETIRED.json")
    require(retired["saved"] == boundary and not (output / "LOADED_RECEIPT.json").exists(), "retired_but_never_loaded")
    old_admission = operator.read(old_control / "ADMISSION.json")
    gone = drift_pids(old_admission)
    require(old_admission["gpu"]["uuid"] == request["old_plan"]["gpu_uuid"], "same_device_denial")
    require(all(not (Path("/proc") / str(process)).exists() for process in gone), "all_drifting_pids_now_gone")
    no_native_launch(old_control)
    for expected in request["processes"].values():
        require(not (Path("/proc") / str(expected["pid"])).exists(), "all_original_owners_gone")
    launch = operator.read(output / "DISPATCHED.json")
    process = Path("/proc") / str(launch["supervisor_pid"]) / "stat"
    require(not process.exists() or process.read_text().rsplit(") ", 1)[1].split()[0] in ("Z", "X"),
            "failed_successor_supervisor_not_live")
    armed = operator.read(output / "ARMED.json")
    observer = Path("/proc") / str(armed["operator_pid"])
    if observer.exists():
        expected = [operator.PYTHON, "-B", str(ROOT / "operator/node1_operator.py"), "handoff", "--physical", "4", "--seconds", "5400"]
        require(observer.joinpath("cmdline").read_bytes().rstrip(b"\0").decode().split("\0") == expected
                and observer.stat().st_uid == os.getuid(), "exact_own_observer_only")
        ticks = observer.joinpath("stat").read_text().rsplit(") ", 1)[1].split()[19]
        descriptor = os.pidfd_open(armed["operator_pid"])
        require(observer.joinpath("stat").read_text().rsplit(") ", 1)[1].split()[19] == ticks, "observer_pidfd_identity")
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        require(select.select([descriptor], [], [], 10)[0], "previous_CPU_observer_exited")
        os.close(descriptor)
    lock = os.open(ROOT / "lane4.lock", os.O_RDWR | os.O_NOFOLLOW)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        proof = operator.read(output / "SOURCE_PROOF.json")
        require(operator.source_inventory(proof["original_source"]) == proof["before"]
                and operator.source_inventory(proof["successor_source"]) == proof["after"], "unchanged_original_and_successor_sources")
        config, plan, original = base.originals(request["new_config"])
        saved = base.sleep_boundary(plan["root"])
        require(saved is not None and saved["record_sha256"] == boundary["record_sha256"]
                and saved["state_sha256"] == boundary["state_sha256"], "same_unconsumed_saved_boundary")
        require(base.saved_evidence(plan, saved, original) == boundary, "unchanged_checkpoint_AdamW_RNG_full_history")
        require(base.actual_device(plan) == request["device"], "same_device_uuid_minor")
        no_native_launch(old_control)
        fresh = output / "readmission1"
        require(not fresh.exists(), "explicit_readmission_once_no_overwrite")
        fresh.mkdir()
        updated = deepcopy(config)
        updated["attempt_dir"] = str(fresh)
        updated["device_containment"]["unit"] = "orch-r136-native-" + uuid.uuid4().hex
        operator.write(fresh / "GUARD.json", updated)
        subprocess.run([operator.PYTHON, "-B", "-c", "from gpu.orch_r125_continual_guard import validate;import sys;validate(sys.argv[1])",
                        str(fresh / "GUARD.json")], cwd=plan["source_root"], env=operator.environment(plan["source_root"]),
                        check=True, timeout=120)
        evidence = dict(schema="R179_NODE1_EXPLICIT_PRELOAD_READMISSION_V1", physical=4,
            previous_admission_sha256=operator.sha(old_control / "ADMISSION.json"), gone_drift_pids=gone,
            native_previously_launched=False, exact_saved_boundary=boundary,
            prior_guard_sha256=operator.sha(request["new_config"]), new_guard_sha256=operator.sha(fresh / "GUARD.json"),
            original_scope_sha256=operator.SCOPE_SHA, readmission_helper_sha256=operator.sha(Path(__file__)),
            unchanged_source=True, unchanged_plan=True, unchanged_wall=True, unchanged_admission_policy=True,
            no_guard_bypass=True, no_reset=True, no_consumed_call_replay=True, observed_unix=time.time())
        operator.write(fresh / "REQUEST.json", evidence)
        command = [operator.PYTHON, "-B", "-m", request["handler"]["module"], request["handler"]["supervisor"],
                   "--config", str(fresh / "GUARD.json")]
        with (fresh / "SUPERVISOR.log").open("xb") as log:
            process = subprocess.Popen(command, cwd=plan["source_root"], env=operator.environment(plan["source_root"]),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        operator.write(fresh / "DISPATCHED.json", dict(supervisor_pid=process.pid, observed_unix=time.time(), no_retry=True))
        deadline = time.monotonic() + 600
        original_index = int(Path(boundary["record_path"]).stem)
        while time.monotonic() < deadline:
            admission_path = fresh / "ADMISSION.json"
            if admission_path.exists():
                admission = operator.read(admission_path)
                if not admission["clear"]:
                    receipt = dict(status="FRESH_GUARDED_READMISSION_DENIED", blocking_reasons=admission["blocking_reasons"],
                        admission_sha256=operator.sha(admission_path), saved_boundary=boundary, no_retry=True, observed_unix=time.time())
                    operator.write(fresh / "DENIED.json", receipt)
                    return receipt
            for path in base.records(plan["root"]):
                if int(path.stem) <= original_index:
                    continue
                record = operator.read(path)
                if record["kind"] != "LOADED":
                    continue
                document = record["document"]
                require(document["resume"] is True and document["optimizer_steps"] == boundary["optimizer_steps"]
                        and document["adapter_sha256"] == boundary["adapter_state_sha256"], "actual_exact_saved_readmitted_load")
                actor = base.identity(document["pid"])
                require(actor["cwd"] == plan["source_root"] and actor["argv"] == [operator.PYTHON, "-B", "-m",
                    "gpu.orch_r125_continual_guard", "native", "--config", str(fresh / "GUARD.json")], "actual_readmitted_source_and_guard")
                admission = operator.read(admission_path)
                containment = operator.read(fresh / "CONTAINMENT_VERIFIED.json")
                denied = containment.get("denied_foreign_minors", containment.get("denied_devices"))
                require(admission["clear"] and admission["scanner_euid"] == 0 and not admission["blocking_reasons"]
                        and admission["gpu"]["uuid"] == plan["gpu_uuid"] and isinstance(denied, list) and len(denied) == 7
                        and containment["policy"]["minor"] == request["device"]["minor"], "original_privileged_admission_and_containment_pass")
                receipt = dict(status="READMITTED_EXACT_BOUNDARY_LOADED", physical=4, actor_pid=actor["pid"],
                    actor_start_ticks=actor["start_ticks"], saved_cycle=boundary["cycle"], optimizer_steps=boundary["optimizer_steps"],
                    adapter_state_sha256=boundary["adapter_state_sha256"], loaded_record_sha256=record["sha256"],
                    source_root=plan["source_root"], config_path=str(fresh / "GUARD.json"),
                    admission_sha256=operator.sha(admission_path), containment_sha256=operator.sha(fresh / "CONTAINMENT_VERIFIED.json"),
                    full_state_receiving_cpu_sha256=operator.sha(output / "BOUNDARY_RECEIVING_CPU.json"),
                    policy_sha256=operator.POLICY_SHA, observed_unix=time.time())
                operator.write(fresh / "LOADED_RECEIPT.json", receipt)
                return receipt
            time.sleep(1)
        return dict(status="READMISSION_LOAD_NOT_OBSERVED_WITHIN_BOUND", physical=4)
    finally:
        os.close(lock)


if __name__ == "__main__":
    print(json.dumps(readmit(), sort_keys=True))
