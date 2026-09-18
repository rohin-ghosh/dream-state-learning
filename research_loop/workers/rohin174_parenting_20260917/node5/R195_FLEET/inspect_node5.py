"""Read-only, metadata-only inventory of seven allowlisted node5 lives."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


LABELS = ("run1", "pilot", "repo_reader", "C1", "C3", "C4", "C5")
EXCLUDED_PID = 3018395
EXCLUDED_ROOT = "/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life"
SOURCE_FILES = (
    "gpu/orch_r125_continual_native.py",
    "gpu/orch_r125_stream_journal.py",
    "gpu/orch_r184_think_act_learn.py",
    "gpu/orch_r132_kernel_bridge.py",
    "gpu/orch_r132_kernel_executor.py",
    "gpu/orch_r125_cpu_confinement_probe.py",
)


def digest(path):
    hasher = hashlib.sha256()
    with safe_path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def reference(path):
    return {"path": str(path), "sha256": digest(path)}


def safe_path(path):
    text = str(path)
    if "C2" in text or "_c2_" in text or EXCLUDED_ROOT in text:
        raise ValueError("excluded_original_c2_path")
    resolved = str(Path(path).resolve())
    if "C2" in resolved or "_c2_" in resolved or EXCLUDED_ROOT in resolved:
        raise ValueError("excluded_original_c2_path_alias")
    return Path(path)


def load(path):
    return json.loads(safe_path(path).read_bytes())


def selected(document, keys):
    return {key: document[key] for key in keys if key in document}


def utc(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()


def is_native_command(arguments):
    return arguments[:4] == ["/localhome/local-rohing/v2/venv/bin/python", "-B", "-m",
                            "gpu.orch_r125_continual_guard"] and "native" in arguments


def process_identity(process):
    fields = (process / "stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=int(process.name), start_ticks=fields[19], state=fields[0],
                ppid=int(fields[1]), uid=process.stat().st_uid,
                argv_sha256=digest(process / "cmdline"), cwd=os.readlink(process / "cwd"))


def record_metadata(path):
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        ending = handle.read()
    position = ending.rfind(b',"index":')
    if position < 0:
        raise ValueError("journal_metadata_unavailable")
    metadata = json.loads(b"{" + ending[position + 1:])
    return selected(metadata, ("index", "kind", "sha256", "previous_sha256"))


def journal_metadata(root, native_pid):
    paths = sorted((safe_path(root) / "stream/records").glob("[0-9]" * 20 + ".json"))
    result = {"record_count": len(paths), "latest": {}}
    if not paths:
        return result
    result["head"] = record_metadata(paths[-1])
    wanted = {"LOADED", "SLEEP_COMPLETE", "SLEEP_RECIPE", "UPDATE", "REQUEST",
              "R184_LEARN_COMPLETE", "R184_THINK", "R184_ACT", "R184_LEARN"}
    recent_floor = max(0, len(paths) - 1400)
    for path in reversed(paths):
        metadata = record_metadata(path)
        kind = metadata["kind"]
        if metadata["index"] < recent_floor and kind != "LOADED":
            continue
        if kind not in wanted or kind in result["latest"]:
            continue
        entry = dict(metadata, file=reference(path), mtime_unix=path.stat().st_mtime)
        if kind != "REQUEST":
            document = load(path)["document"]
            if kind == "LOADED" and document.get("pid") != native_pid:
                continue
            entry["fields"] = selected(document, (
                "pid", "cycle", "status", "stage", "phase", "new_rows",
                "new_presentations", "selected_old_rows", "loaded_unix",
                "started_unix", "finished_unix", "optimizer_steps", "optimizer_step"))
            if kind == "SLEEP_COMPLETE":
                entry["checkpoint"] = selected(document.get("checkpoint", {}), (
                    "optimizer_steps", "adapter_state_sha256", "checkpoint_sha256"))
                entry["resume_state"] = selected(document.get("resume_state", {}), ("sha256",))
        result["latest"][kind] = entry
        if metadata["index"] < recent_floor and kind == "LOADED":
            break
    return result


def inventory(items):
    if set(item["label"] for item in items) != set(LABELS) or len(items) != 7:
        raise ValueError("exact_seven_life_allowlist_required")
    for item in items:
        safe_path(item["logical_root"])
        safe_path(item["storage_root"])
    processes = []
    natives = {}
    for process in Path("/proc").iterdir():
        if not process.name.isdigit() or int(process.name) == EXCLUDED_PID:
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            arguments = (process / "cmdline").read_bytes().rstrip(b"\0").decode().split("\0")
            joined = " ".join(arguments)
            if "C2" in joined or "_c2_" in joined or not arguments:
                continue
            if not any(token in joined for token in ("orch_", "rollout_operator", "saved_primitives")):
                continue
            identity = process_identity(process)
            if identity["state"] in ("Z", "X"):
                continue
            processes.append((arguments, identity))
            if not is_native_command(arguments):
                continue
            config_path = safe_path(arguments[arguments.index("--config") + 1])
            config = load(config_path)
            plan_path = safe_path(config["plan_path"])
            plan = load(plan_path)
            if plan.get("root") not in {item["logical_root"] for item in items}:
                continue
            if plan.get("physical") == 1:
                raise ValueError("excluded_physical_gpu1")
            natives.setdefault(plan["root"], []).append((identity, config_path, config, plan_path, plan))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    rows = []
    for item in items:
        row = dict(label=item["label"], logical_root=item["logical_root"], storage_root=item["storage_root"])
        candidates = natives.get(item["logical_root"], [])
        if len(candidates) != 1:
            rows.append(dict(row, blocked="actual_native_count_not_one", count=len(candidates)))
            continue
        identity, config_path, config, plan_path, plan = candidates[0]
        source = safe_path(plan["source_root"])
        row.update(native=identity, guard=reference(config_path), plan_ref=reference(plan_path),
                   control_root=str(config_path.parent), source_root=str(source),
                   plan=selected(plan, ("root", "source_root", "physical", "gpu_uuid", "hard_end_unix",
                       "lease_end_unix", "new_presentations", "rehearsal_presentations", "sleep_loss_impl",
                       "code_policy", "kernel_socket", "cpu_socket", "max_context_tokens")))
        for field in ("hard_end_unix", "lease_end_unix"):
            if plan.get(field):
                row[field + "_utc"] = utc(plan[field])
        row["remaining_wall_seconds"] = plan["hard_end_unix"] - time.time()
        row["plan_pin_matches"] = digest(plan_path) == config.get("plan_sha256")
        row["helpers"] = {}
        for name in ("rollout_operator.py", "saved_primitives.py", "protected_primitives.py",
                     "containment_primitives.py", "reader_capsule.py", "controller_transfer.py",
                     "cpu_actual.py", "stage_node5.py", "r188_preload_recovery.py"):
            helper = config_path.parent / name
            if helper.is_file():
                row["helpers"][name] = reference(helper)
        row["control_receipts"] = {}
        for name in ("READY.json", "OWNER_RETIRED.json", "EXECUTION_FAILED.json", "READMISSION.json"):
            receipt = config_path.parent / name
            if receipt.is_file():
                row["control_receipts"][name] = reference(receipt)
        lease_path = safe_path(config["lease_path"])
        lease = load(lease_path)
        row["lease"] = dict(reference(lease_path), pin_matches=digest(lease_path) == config.get("lease_sha256"),
            fields=selected(lease, ("lease_end_unix", "hard_end_unix", "expires_unix", "end_unix",
                                  "next_reserved_unix", "lease_id")))
        row["source_files"] = {}
        for relative in SOURCE_FILES:
            path = source / relative
            if path.is_file():
                row["source_files"][relative] = dict(reference(path),
                    pin_matches=digest(path) == config.get("source_pins", {}).get(relative))
        row["journal"] = journal_metadata(item["storage_root"], identity["pid"])
        inbox = safe_path(item["storage_root"]) / "stream/inbox"
        row["inbox"] = {"path": str(inbox), "exists": inbox.is_dir(), "files": []}
        if inbox.is_dir():
            row["inbox"]["files"] = [reference(path) for path in sorted(inbox.iterdir()) if path.is_file()]
        owners = []
        for arguments, owner in processes:
            if owner["pid"] == identity["pid"]:
                continue
            if not any(needle in " ".join(arguments) for needle in (
                    item["logical_root"], item["storage_root"], str(config_path.parent), str(source))):
                continue
            entrypoints = [argument for argument in arguments if argument.endswith(".py")
                           or argument.startswith("gpu.")]
            owners.append(dict(identity=owner, entrypoints=entrypoints,
                modes=[argument for argument in arguments if argument in (
                    "start", "execute", "contained", "readmission", "supervise", "recover")],
                is_native_guard=is_native_command(arguments)))
        row["related_processes"] = owners
        row["guard_keys"] = sorted(config)
        row["plan_keys"] = sorted(plan)
        row["runtime_configs"] = selected(plan, (
            "think_act_learn", "r184_config_path", "r153_community", "parent_config_path"))
        rows.append(row)
    services = []
    for arguments, identity in processes:
        entrypoints = [argument for argument in arguments if argument.endswith(".py")
                       or argument.startswith("gpu.")]
        if not any(any(marker in entry for marker in ("bridge", "broker", "service", "transport"))
                   for entry in entrypoints):
            continue
        flags = {}
        for flag in ("--root", "--config", "--life", "--code-policy", "--output"):
            if flag in arguments and arguments.index(flag) + 1 < len(arguments):
                value = arguments[arguments.index(flag) + 1]
                safe_path(value)
                flags[flag] = value
        services.append(dict(identity=identity, entrypoints=entrypoints, flags=flags))
    return dict(observed_utc=utc(time.time()), rows=rows, signals=0, remote_writes=0,
                services=services, publications=0, original_c2_excluded=True,
                no_credentials_or_sealed_final_data=True)


def main():
    if "--remote" in sys.argv:
        print(json.dumps(inventory(json.load(sys.stdin))))
        return
    here = Path(__file__).resolve().parent
    previous = sorted(here.parent.glob("R181_CURRENT_*.json"))[-1]
    items = [selected(row, ("label", "logical_root", "storage_root"))
             for row in json.loads(previous.read_bytes())["rows"] if row["label"] in LABELS]
    repo = here.parents[4]
    command = "python3 -B -c " + shlex.quote(Path(__file__).read_text()) + " --remote"
    result = subprocess.run(["bash", str(repo / "gpu/ovx3_ssh.sh"), command],
                            input=json.dumps(items), capture_output=True, text=True, timeout=100)
    if result.returncode:
        raise RuntimeError("read_only_remote_inventory_failed; no raw stderr emitted")
    document = json.loads(result.stdout)
    document["mapping_source"] = reference(previous)
    output = here / ("INVENTORY_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    with output.open("x") as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"receipt": str(output), "observed_utc": document["observed_utc"], "rows": [
        dict(label=row["label"], pid=row.get("native", {}).get("pid"), blocked=row.get("blocked"),
             hard_end_utc=row.get("hard_end_unix_utc"), lease_end_utc=row.get("lease_end_unix_utc"),
             head=row.get("journal", {}).get("head"), related_process_count=len(row.get("related_processes", [])))
        for row in document["rows"]]}))


if __name__ == "__main__":
    main()
