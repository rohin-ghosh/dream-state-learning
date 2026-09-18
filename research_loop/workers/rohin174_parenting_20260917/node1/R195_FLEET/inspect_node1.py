"""One-shot read-only node1 process, source, lease and saved-state inventory."""

import hashlib
import json
import os
from pathlib import Path
import re
import socket
import time


LABELS = {
    0: "frozen_rank8_no_sleep",
    1: "frozen_base_no_adapter",
    2: "teach_replay",
    3: "teach_perception",
    4: "teach_parenting",
    5: "classroom_brain",
    6: "classroom_creative",
    7: "classroom_support",
}
SOURCE_FILES = (
    "gpu/orch_r125_continual_native.py",
    "gpu/orch_r125_stream_journal.py",
    "organism_v6/orch_r125_continual_stream.py",
    "organism_v6/orch_r124_train_history.py",
    "gpu/orch_r184_think_act_learn.py",
    "gpu/orch_r184_transition_targets.py",
)


def digest(document):
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_document(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("unsafe_or_oversized_metadata")
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def inspect_native(process, arguments):
    guard_path = Path(arguments[arguments.index("--config") + 1])
    guard, guard_sha = read_document(guard_path)
    plan, plan_sha = read_document(guard["plan_path"])
    physical = plan["physical"]
    label = LABELS[physical]
    family = "r139" if physical < 2 else "r136"
    root = Path("/localhome/local-rohing/orch_" + family + "_a100_" + label
                + "_20260916_attempt1/run1")
    if str(root) != plan["root"]:
        raise ValueError("not_expected_node1_life")
    identity = (process / "stat").read_text().rsplit(") ", 1)[1].split()
    source = Path(plan["source_root"])
    row = dict(physical=physical, life=label, frozen_control=physical < 2,
               pid=int(process.name), ppid=int(identity[1]), start_ticks=identity[19],
               process_state=identity[0], uid=process.stat().st_uid,
               guard_path=str(guard_path), guard_sha256=guard_sha,
               plan_path=guard["plan_path"], plan_sha256=plan_sha,
               plan_pin_matches=guard.get("plan_sha256") == plan_sha,
               root=str(root), source_root=str(source),
               cwd_matches_source=os.readlink(process / "cwd") == str(source),
               resume=guard.get("resume"), hard_end_unix=plan.get("hard_end_unix"),
               lease_end_unix=plan.get("lease_end_unix"),
               guard_hard_end_unix=guard.get("hard_end_unix"),
               gpu_uuid=plan.get("gpu_uuid"), device_containment=guard.get("device_containment"),
               new_presentations=plan.get("new_presentations"),
               rehearsal_presentations=plan.get("rehearsal_presentations"),
               think_act_learn=plan.get("think_act_learn"), source_files={})
    if guard.get("lease_path"):
        lease, lease_sha = read_document(guard["lease_path"])
        row["lease"] = {key: lease.get(key) for key in
                        ("hard_end_unix", "lease_end_unix", "original_margin_seconds", "extension")}
        row.update(lease_path=guard["lease_path"], lease_sha256=lease_sha,
                   lease_pin_matches=guard.get("lease_sha256") == lease_sha)
    for relative in SOURCE_FILES:
        path = source / relative
        if path.is_file():
            source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            row["source_files"][relative] = dict(sha256=source_sha,
                pin_matches=guard.get("source_pins", {}).get(relative) == source_sha)
    if physical < 2:
        row["inspection_scope"] = "frozen control identity/source/lease only; no journal inspection"
        return row
    records = sorted(path for path in (root / "stream/records").iterdir()
                     if re.fullmatch(r"\d{20}\.json", path.name))
    row["record_count"] = len(records)
    row["inbox_file_count"] = sum(path.is_file() for path in (root / "stream/inbox").iterdir())
    row["selected_records"] = {}
    wanted = {"LOADED", "SLEEP_COMPLETE", "SLEEP_RECIPE", "THINK", "ACT", "LEARN_COMPLETE"}
    for offset, path in enumerate(reversed(records[-256:])):
        record, record_sha = read_document(path)
        kind, document = record["kind"], record["document"]
        if offset == 0:
            row["head"] = dict(index=record["index"], kind=kind, sha256=record["sha256"])
        if kind not in wanted or kind in row["selected_records"]:
            continue
        selected = dict(index=record["index"], sha256=record["sha256"], file_sha256=record_sha,
                        mtime_ns=path.stat().st_mtime_ns,
                        self_hash_matches=record["sha256"] == digest({key: value for key, value in
                            record.items() if key != "sha256"}))
        selected.update({key: document[key] for key in (
            "cycle", "status", "optimizer_steps", "total_optimizer_steps", "policy",
            "selected_old_rows", "new_rows", "new_presentations", "loaded_unix",
            "resume", "pid", "adapter_sha256", "stage") if key in document})
        if kind == "SLEEP_COMPLETE":
            envelope = document["resume_state"]
            state = envelope["state"]
            selected.update(state_sha256=envelope["sha256"], state_hash_matches=digest(state) == envelope["sha256"],
                            saved_row_count=len(state["rows"]), pending_is_none=state["pending"] is None,
                            sleep_frontier=state["sleep_frontier"], state_keys=sorted(state))
            checkpoint_path = root / "checkpoints" / ("sleep_%06d" % document["cycle"]) / "COMMIT.json"
            checkpoint, checkpoint_sha = read_document(checkpoint_path)
            selected["checkpoint"] = dict(path=str(checkpoint_path), sha256=checkpoint_sha,
                optimizer_steps=checkpoint.get("optimizer_steps"),
                adapter_state_sha256=checkpoint.get("adapter_state_sha256"),
                checkpoint_sha256=checkpoint.get("checkpoint_sha256"),
                optimizer_rng_path=checkpoint.get("optimizer_rng_path"))
        row["selected_records"][kind] = selected
    return row


def main():
    if socket.gethostname() != "[REDACTED_HOST]" or os.getuid() != 1395:
        raise ValueError("node1_read_only_scope")
    rows, errors = [], []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != 1395:
                continue
            arguments = (process / "cmdline").read_bytes().decode().split("\0")
            learner = "gpu.orch_r125_continual_guard" in arguments and "native" in arguments
            frozen = "gpu.orch_r136_node1_launcher" in arguments and "control-native" in arguments
            if not (learner or frozen):
                continue
            if "--config" not in arguments or Path(arguments[0]).name == "timeout":
                continue
            rows.append(inspect_native(process, arguments))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        except (KeyError, ValueError, OSError) as error:
            errors.append(dict(pid=int(process.name), error_type=type(error).__name__))
    print(json.dumps(dict(observed_unix=time.time(), hostname=socket.gethostname(),
        boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        rows=sorted(rows, key=lambda row: row["physical"]), errors=errors,
        signals=0, remote_writes=0, sealed_reads=0, gpu_calls=0,
        coverage="live identities and selected last256 self-hashed records; not quiescent handoff proof"),
        sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
