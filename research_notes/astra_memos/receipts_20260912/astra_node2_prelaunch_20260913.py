"""Read-only node2 allocation check with identity-bound nonlearner exceptions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

DAEMONS = (
    dict(pid=36935, comm="systemd", ppid=1, start_ticks=4243834, uid=2524,
         cmdline_sha256="3127082f907652bfa48e38fddcaf16c3e73b2da5a2d64602eafe88869c222925"),
    dict(pid=36938, comm="(sd-pam)", ppid=36935, start_ticks=4243835, uid=2524,
         cmdline_sha256="971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370"),
)
TRANSPORT_COMMAND_SHA = "33000acd013adbf8dbb593c9baf3f7acaa8911db00e85f90a5abc6cd25afcc44"
SELECTABLE = {
    0: "GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0",
    1: "GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4",
    2: "GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05",
}


def identity(process):
    fields = (process / "stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=int(process.name), comm=(process / "comm").read_text().strip(),
                ppid=int(fields[1]), start_ticks=int(fields[19]), uid=process.stat().st_uid,
                cmdline_sha256=hashlib.sha256((process / "cmdline").read_bytes()).hexdigest())


def exception_reason(record, ancestors):
    if record in DAEMONS:
        return "exact_previously_inspected_session_daemon"
    if (record["pid"] in ancestors and record["comm"] == "sshd" and record["uid"] == 2524
            and record["cmdline_sha256"] == TRANSPORT_COMMAND_SHA):
        return "current_checker_transport_ancestor"
    return None


def selected(devices, index, uuid):
    tokens = {value.strip() for value in devices.split(",")}
    return bool(tokens & {str(index), uuid, "all"})


def check(index, uuid):
    if SELECTABLE.get(index) != uuid or os.getuid() != 2524:
        raise ValueError("not the prospectively selected node2 allocation")
    inventory = subprocess.run(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"],
                               check=True, capture_output=True, text=True, timeout=60).stdout
    pairs = [tuple(value.strip() for value in line.split(",")) for line in inventory.splitlines()]
    if (str(index), uuid) not in pairs:
        raise ValueError("physical device identity changed")
    output = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"],
                            check=True, capture_output=True, text=True, timeout=60).stdout
    compute = [int(line.split(",")[1].strip()) for line in output.splitlines()
               if line.split(",")[0].strip() == uuid]
    ancestors = set()
    parent = os.getpid()
    while parent > 1 and parent not in ancestors:
        ancestors.add(parent)
        parent = identity(Path("/proc") / str(parent))["ppid"]
    matched, unresolved, exceptions = [], [], []
    scanned = 0
    for process in Path("/proc").glob("[0-9]*"):
        try:
            if process.stat().st_uid != os.getuid():
                continue
            try:
                fields = (process / "environ").read_bytes().split(b"\0")
            except PermissionError:
                record = identity(process)
                reason = exception_reason(record, ancestors)
                if reason is None:
                    unresolved.append(record)
                else:
                    exceptions.append(dict(record, reason=reason))
                continue
            scanned += 1
            devices = next((field.split(b"=", 1)[1].decode() for field in fields
                            if field.startswith(b"CUDA_VISIBLE_DEVICES=")), "")
            if selected(devices, index, uuid):
                matched.append(int(process.name))
        except FileNotFoundError:
            continue
    result = dict(checked_unix=time.time(), gpu_index=index, gpu_uuid=uuid, compute_processes=compute,
                  matching_reservations=matched, unresolved_same_user=unresolved,
                  same_user_environments_scanned=scanned, explicit_nonlearner_exceptions=exceptions,
                  scope="current vacancy only; no reservation, no unreadable environment inspection")
    print(json.dumps(result, sort_keys=True), flush=True)
    if compute or matched or unresolved:
        raise ValueError("occupied device or unresolved reservation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu-index", type=int, required=True)
    parser.add_argument("--gpu-uuid", required=True)
    options = parser.parse_args()
    check(options.gpu_index, options.gpu_uuid)
