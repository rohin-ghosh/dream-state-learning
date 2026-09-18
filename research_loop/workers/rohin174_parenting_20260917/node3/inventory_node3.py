"""Print fresh read-only Node3 process/config and parent-ledger metadata."""

import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECOVERY = REPO / "research_loop/workers/r179_context_survival_20260917/node3"
REMOTE_ROOT = "/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2"
LIVES = {
    0: "support_free",
    1: "creative_reread",
    2: "brain_free",
    3: "brain_guided",
    4: "creative_free",
    7: "creative_select",
}
CONFIG_FIELDS = (
    "schema", "node", "root", "source_root", "branch", "programme",
    "programme_path", "programme_sha256", "principles_path", "principles_sha256",
    "cadence_label", "cadence_responses", "schedule_on", "hard_end_unix",
    "start_after_request_count", "start_after_response_count", "predecessor_output",
    "predecessor_started_sha256", "poll_interval_seconds", "parent_reasoning_effort",
)


def reference(path):
    path = Path(path)
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def process_identity(identity):
    process = Path("/proc") / str(identity["pid"])
    try:
        fields = (process / "stat").read_text().rsplit(") ", 1)[1].split()
        argv = (process / "cmdline").read_bytes().rstrip(b"\0").decode().split("\0")
        exact = fields[19] == str(identity["ticks"]) and argv == identity["argv"]
        return dict(pid=identity["pid"], start_ticks=fields[19], state=fields[0],
                    exact_identity=exact, alive=exact and fields[0] not in ("Z", "X"))
    except FileNotFoundError:
        return dict(pid=identity["pid"], alive=False, process_absent=True)
    except PermissionError:
        return dict(pid=identity["pid"], alive=None, observation="PERMISSION_DENIED")


def parent_metadata(physical):
    folder = RECOVERY / "parents" / ("physical" + str(physical))
    binding = json.loads((folder / "BINDING.json").read_text())["parent_binding"]
    config_path = folder / "CONFIG.json"
    config = json.loads(config_path.read_text())
    identity = json.loads((folder / "SPAWNED.json").read_text())["identity"]
    started = json.loads((folder / "parent/STARTED.json").read_text())
    config_ref = reference(config_path)
    row = dict(process=process_identity(identity), config=config_ref,
               effective_config={key: config[key] for key in CONFIG_FIELDS if key in config},
               binding=reference(folder / "BINDING.json"),
               started=reference(folder / "parent/STARTED.json"),
               started_model=started.get("model"), expected_argv=identity["argv"],
               started_config_matches=started["config_sha256"] == config_ref["sha256"],
               binding_config_matches=binding["config_sha256"] == config_ref["sha256"],
               output=binding["output"])
    for name in ("source", "provider"):
        pinned = reference(binding[name + "_copy"])
        row[name] = dict(pinned, binding_matches=pinned["sha256"] == binding[name + "_sha256"])
    attempts = []
    for directory in sorted((folder / "parent").glob("parent_*")):
        if not directory.is_dir():
            continue
        attempt = {"name": directory.name}
        source_path, result_path = directory / "SOURCE.json", directory / "RESULT.json"
        if source_path.exists():
            source = json.loads(source_path.read_text())
            attempt["source"] = reference(source_path)
            attempt["counters"] = {key: source[key] for key in (
                "request_count", "response_count", "record_count", "head_sha256"
            ) if key in source}
        if result_path.exists():
            result = json.loads(result_path.read_text())
            attempt["result"] = reference(result_path)
            attempt["metadata"] = {key: result[key] for key in (
                "status", "actual_model", "source_head_sha256", "source_response_count",
                "schedule_on", "schedule_count", "started_unix", "finished_unix"
            ) if key in result}
            attempt["published_inbox_id"] = result.get("inbox_publication", {}).get("id")
        else:
            attempt["unsettled"] = True
        delivered = directory / "DELIVERED.json"
        attempt["delivery_registration_exists"] = delivered.exists()
        if delivered.exists():
            attempt["delivery_registration"] = reference(delivered)
        attempts.append(attempt)
    row["attempts"] = attempts
    row["registration_is_not_rendered_request_proof"] = True
    return row


REMOTE_PROBE = r'''
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time

base = Path("/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2")
gpu_lines = subprocess.run(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"], check=True, capture_output=True, text=True, timeout=20).stdout.splitlines()
gpu_map = {int(line.split(",")[0].strip()): line.split(",")[1].strip() for line in gpu_lines}
application_lines = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_gpu_memory", "--format=csv,noheader"], check=True, capture_output=True, text=True, timeout=20).stdout.splitlines()
applications = [{"gpu_uuid": fields[0].strip(), "pid": int(fields[1].strip()), "used_gpu_memory": fields[2].strip()} for fields in (line.split(",") for line in application_lines) if len(fields) == 3]
rows = []
for physical in (0, 1, 2, 3, 4, 7):
    control = base / ("control" + str(physical))
    receipt_path = control / "LOADED_RECEIPT.json"
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    actor = receipt["actor"]
    guard_path = control / "GUARD.json"
    guard_raw = guard_path.read_bytes()
    guard = json.loads(guard_raw)
    process = Path("/proc") / str(actor["pid"])
    row = dict(physical=physical, active_root=str(control / "run1"), pid=actor["pid"], expected_start_ticks=str(actor["start_ticks"]), loaded_receipt=dict(path=str(receipt_path), sha256=hashlib.sha256(receipt_raw).hexdigest()), config=dict(path=str(guard_path), sha256=hashlib.sha256(guard_raw).hexdigest()), hard_end_unix=guard.get("hard_end_unix"), gpu_uuid=gpu_map[physical])
    try:
        fields = (process / "stat").read_text().rsplit(") ", 1)[1].split()
        argv = (process / "cmdline").read_bytes().rstrip(b"\0").decode().split("\0")
        expected = ["/localhome/local-rohing/v2/venv/bin/python", "-B", "-m", "gpu.orch_r125_continual_guard", "native", "--config", str(guard_path)]
        exact = fields[19] == str(actor["start_ticks"]) and argv == expected
        row.update(start_ticks=fields[19], state=fields[0], expected_argv=expected, exact_identity=exact, alive=exact and fields[0] not in ("Z", "X"))
    except FileNotFoundError:
        row.update(alive=False, process_absent=True)
    except PermissionError:
        row.update(alive=None, observation="PERMISSION_DENIED")
    row["gpu_process"] = [application for application in applications if application["pid"] == actor["pid"] and application["gpu_uuid"] == gpu_map[physical]]
    rows.append(row)
print(json.dumps(dict(host=socket.gethostname(), observed_unix=time.time(), rows=rows), sort_keys=True))
'''


def observe():
    started = time.time()
    mapping = json.loads((RECOVERY / "PARENT_RECOVERY_MAPPING.json").read_text())
    by_physical = {row["physical"]: row for row in mapping["rows"]}
    if set(by_physical) != set(LIVES):
        raise ValueError("unexpected_node3_life_mapping")
    remote = subprocess.run(
        ["bash", str(REPO / "gpu/ovx2_ssh.sh"), "python3 -B -"],
        input=REMOTE_PROBE, capture_output=True, text=True, timeout=75,
    )
    if remote.returncode:
        raise RuntimeError("read_only_node3_probe_failed_without_printing_remote_output")
    observation = json.loads(remote.stdout)
    rows = []
    for child in observation["rows"]:
        physical = child["physical"]
        mapping_row = by_physical[physical]
        if child["active_root"] != mapping_row["active_host_root"]:
            raise ValueError("unexpected_recovered_child_root")
        rows.append(dict(physical=physical, life=LIVES[physical], child=child,
                         parent=parent_metadata(physical),
                         original_logical_root=mapping_row["logical_root"],
                         preserved_recovery_clock=dict(saved_counts=mapping_row["saved_counts"],
                                                       terminal_counts=mapping_row["terminal_counts"])))
    return dict(schema="ROHIN174_NODE3_READ_ONLY_INVENTORY_V1", status="OBSERVED_NOT_SWITCHED",
                started_unix=started, finished_unix=time.time(), local_host=socket.gethostname(),
                child_host=observation["host"], remote_observed_unix=observation["observed_unix"],
                wrapper=reference(REPO / "gpu/ovx2_ssh.sh"), observer=reference(__file__),
                root_mapping=reference(RECOVERY / "PARENT_RECOVERY_MAPPING.json"), rows=rows,
                main_binding=None, new_policy_turn_receipt=None, rendered_request_proof=None,
                remote_mutations=0, process_signals=0, child_restarts=0, provider_calls=0,
                restricted_artifacts_read=0, credential_values_read=0,
                internal_hard_end_unix=1789689000, machine_ceiling_unix=1789689600,
                metadata_observation_not_scientific_evidence=True)


if __name__ == "__main__":
    print(json.dumps(observe(), indent=2, sort_keys=True))
