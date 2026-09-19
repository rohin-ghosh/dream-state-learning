"""Bounded, read-only audit; all persistent output goes through apply_patch."""

import argparse
import ast
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import zlib


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EVIDENCE = HERE.parent / "evidence/node2_recovery/storage"
REMOTE_HOME = "/localhome/local-rohing"
ARCHIVE_ROOT = REMOTE_HOME + "/orch_r188_node2_rehome_20260917t2344z/final_transport"
PRESERVATION = REMOTE_HOME + "/orch_rohin233_focus_node2_20260918/PRESERVATION.public.json"
PRESERVATION_SHA = "9481707cb24918cfa54b1da663ec8c6ca0a576697e2a79c10913b5f013f9f52c"
ARCHIVE_NAMES = ("physical1.tar.gz", "physical4.tar.gz", "physical7.tar.gz")


READ_ONLY = r'''
from datetime import datetime, timezone
import hashlib, json, os, stat
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def space(path):
    info = os.statvfs(path)
    return dict(utc=now(), path=str(path), fragment_size=info.f_frsize,
                blocks=info.f_blocks, free_blocks=info.f_bfree,
                available_blocks=info.f_bavail,
                owner_available_bytes=info.f_bavail * info.f_frsize,
                free_bytes_including_reserved=info.f_bfree * info.f_frsize)

def metadata(info):
    return dict(device=info.st_dev, inode=info.st_ino, size=info.st_size,
                allocated_bytes=info.st_blocks * 512, nlink=info.st_nlink,
                uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode),
                atime_ns=info.st_atime_ns, mtime_ns=info.st_mtime_ns,
                ctime_ns=info.st_ctime_ns)

def hash_file(path, limit):
    path = Path(path)
    result = dict(path=str(path), started_utc=now(), byte_limit=limit)
    try:
        if path.resolve(strict=True) != path or path.is_symlink():
            raise ValueError("redirected_path")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC)
        with os.fdopen(descriptor, "rb") as handle:
            initial = os.fstat(handle.fileno())
            result["before"] = metadata(initial)
            if not stat.S_ISREG(initial.st_mode) or initial.st_size > limit:
                raise ValueError("regular_file_and_size_bound_required")
            checksum = hashlib.sha256()
            count = 0
            while True:
                chunk = handle.read(min(4 * 1024 * 1024, limit + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    raise ValueError("hash_byte_limit_exceeded")
                checksum.update(chunk)
            result["after_fd"] = metadata(os.fstat(handle.fileno()))
            result["after_path"] = metadata(path.lstat())
            result["bytes_read"] = count
            if not (result["before"] == result["after_fd"] == result["after_path"]
                    and count == initial.st_size):
                raise ValueError("file_changed_during_hash")
            result["sha256"] = checksum.hexdigest()
            result["status"] = "stable_fresh_sha256"
    except (OSError, ValueError) as error:
        result["status"] = "blocked"
        result["error"] = dict(type=type(error).__name__, message=str(error))
    result["finished_utc"] = now()
    return result
'''

exec(READ_ONLY)


def scanner_program(path):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PROGRAM" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("missing_original_scanner_program")


def encoded_command(program):
    encoded = base64.b64encode(zlib.compress(program.encode())).decode()
    payload = "import base64,zlib;exec(zlib.decompress(base64.b64decode(" + repr(encoded) + ")))"
    return "python3 -B -c " + shlex.quote(payload)


def original_ssh(program):
    result = subprocess.run(
        ["bash", str(REPO / "gpu/ovx_ssh.sh"), encoded_command(program)],
        capture_output=True, text=True, timeout=240,
    )
    if result.returncode:
        return dict(status="ssh_or_remote_failure", returncode=result.returncode,
                    stderr=result.stderr[-4000:], stdout=result.stdout[-4000:])
    return json.loads(result.stdout)


def compare(source, survivor):
    return bool(source.get("status") == survivor.get("status") == "stable_fresh_sha256"
                and source["sha256"] == survivor["sha256"]
                and source["bytes_read"] == survivor["bytes_read"])


def write_receipt(filename, document):
    destination = HERE / filename
    if destination.exists():
        raise FileExistsError("receipt_already_exists_no_overwrite")
    body = json.dumps(document, indent=2, sort_keys=True) + "\n"
    patch = "*** Begin Patch\n*** Add File: " + str(destination) + "\n"
    patch += "".join("+" + line + "\n" for line in body.splitlines())
    patch += "*** End Patch\n"
    subprocess.run(["apply_patch", patch], check=True, capture_output=True, text=True)


def audit():
    started = now()
    local_before = space(REPO)
    census_path = EVIDENCE / "NEXT_RETIRED_20260919T1543.json"
    history_path = EVIDENCE / "FINAL_METADATA_20260919T151238Z.json"
    scanner_path = EVIDENCE / "coalescence_locked/pidfd_scan.py"
    census = json.loads(census_path.read_bytes())
    history = json.loads(history_path.read_bytes())
    bindings = []
    for name in ARCHIVE_NAMES:
        remote_path = ARCHIVE_ROOT + "/" + name
        entries = [entry for entry in history["archives"] if entry["path"] == remote_path]
        if len(entries) != 1:
            raise ValueError("exact_historical_archive_binding_required")
        historic = entries[0]["historical_receipt"]
        survivor = Path(historic["declared_VM_archive"])
        expected_parent = REPO / "research_loop/workers/rohin174_parenting_20260917/node3/r188/final_relocation_20260917t2350z"
        if survivor.parent != expected_parent or survivor.name != name:
            raise ValueError("unexpected_surviving_archive_path")
        bindings.append(dict(remote_path=remote_path, survivor_path=str(survivor),
                             expected_bytes=historic["expected_archive_bytes"],
                             historical_sha256=historic["expected_archive_sha256"]))
    sample = census["top_candidates"][:3]
    allowed_record_roots = {entry["root"] for entry in census["roots"]}
    sample_paths = []
    for group in sample:
        for inode in group["inodes"]:
            for entry in inode:
                if str(Path(entry["path"]).parent) not in allowed_record_roots:
                    raise ValueError("sample_outside_retired_census_roots")
                sample_paths.append(entry["path"])
    scan_paths = [entry["remote_path"] for entry in bindings] + sample_paths
    if len(scan_paths) > 40:
        raise ValueError("original_scanner_path_limit")
    config = dict(bindings=bindings, preservation=PRESERVATION,
                  preservation_sha=PRESERVATION_SHA, sample_paths=sample_paths,
                  scan_paths=scan_paths, scanner=scanner_program(scanner_path),
                  remote_home=REMOTE_HOME)
    remote_program = READ_ONLY + "\nconfig=" + repr(config) + r'''
import subprocess
report = dict(started_utc=now(), host=os.uname().nodename, uid=os.getuid(),
              before=space(config["remote_home"]), mutations=False)
report["preservation"] = hash_file(config["preservation"], 65536)
if report["preservation"].get("sha256") != config["preservation_sha"]:
    report["status"] = "retirement_binding_mismatch"
else:
    command = ["sudo", "-n", "python3", "-B", "-c", config["scanner"]]
    try:
        scan = subprocess.run(command, input=json.dumps(config["scan_paths"]),
                              capture_output=True, text=True, timeout=45)
        report["writer_scan"] = dict(returncode=scan.returncode, stderr=scan.stderr[-4000:])
        if scan.returncode == 0:
            report["writer_scan"]["result"] = json.loads(scan.stdout)
        else:
            report["writer_scan"]["stdout"] = scan.stdout[-4000:]
    except (subprocess.TimeoutExpired, ValueError) as error:
        report["writer_scan"] = dict(error_type=type(error).__name__, status="unresolved")
    report["archives"] = [hash_file(entry["remote_path"], entry["expected_bytes"])
                          for entry in config["bindings"]]
    report["sampled_retired_records"] = [hash_file(path, 1024 * 1024)
                                          for path in config["sample_paths"]]
    report["status"] = "read_only_audit_completed"
report["after"] = space(config["remote_home"])
report["finished_utc"] = now()
print(json.dumps(report, sort_keys=True))
'''
    with ThreadPoolExecutor(max_workers=2) as pool:
        remote_future = pool.submit(original_ssh, remote_program)
        survivors = [hash_file(entry["survivor_path"], entry["expected_bytes"])
                     for entry in bindings]
        remote = remote_future.result()
    pair_results = []
    remote_files = {entry["path"]: entry for entry in remote.get("archives", [])}
    for binding, survivor in zip(bindings, survivors):
        source = remote_files.get(binding["remote_path"], {})
        pair_results.append(dict(**binding, source=source, survivor=survivor,
                                 fresh_identical_pair=compare(source, survivor),
                                 both_match_historical_sha256=bool(
                                     source.get("sha256") == survivor.get("sha256")
                                     == binding["historical_sha256"])))
    scan = remote.get("writer_scan", {}).get("result", {})
    writer_gate = bool(scan.get("scanner_euid") == 0
                       and scan.get("scope") == "all_uid_privileged_fds_and_writable_maps"
                       and scan.get("lifetime_protocol") == "pidfd_start_bound_v1"
                       and not scan.get("writers") and not scan.get("inaccessible_or_exited"))
    tracked = subprocess.run(
        ["git", "ls-files", "--", *[entry["survivor_path"] for entry in bindings]],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    provenance_paths = [Path(__file__), REPO / "gpu/ovx_ssh.sh", census_path,
                        history_path, scanner_path,
                        EVIDENCE / "coalescence_remaining/NEXT_RECLAIM_REPORT.md",
                        EVIDENCE / "FINAL_PARTIAL_CLEANUP_SUMMARY_20260919.md"]
    provenance = [{"path": str(path.relative_to(REPO)),
                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                  for path in provenance_paths]
    return dict(schema="bounded_storage_cleanup_audit_v1", started_utc=started,
                finished_utc=now(), classification="non_material_storage_audit_cpu_provenance_only",
                provenance=provenance, remote=remote, archive_pairs=pair_results,
                local_before=local_before, local_after=space(REPO),
                archive_survivors_tracked_by_git=tracked,
                historical_next_set=dict(groups=census["new_candidate_count"],
                                         metadata_ceiling_bytes=census["new_candidate_potential_bytes"],
                                         fully_reinventoried=False, sampled_groups=len(sample)),
                complete_original_writer_snapshot=writer_gate,
                deletion_ready=False, deletions=[], actual_recovered_bytes=0,
                writes_to_remote=False, new_gpu_runs=False, bulk_data_transferred=False,
                local_disposable_caches_created=False,
                disposition="audit_only_no_deletion_without_all_nonlive_and_identity_gates")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    arguments = parser.parse_args()
    report = audit()
    if arguments.write_receipt:
        write_receipt("AUDIT_RECEIPT.json", report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(json.dumps(dict(receipt=str(HERE / "AUDIT_RECEIPT.json"),
                          fresh_pairs=[dict(path=entry["remote_path"],
                                            identical=entry["fresh_identical_pair"],
                                            sha256=entry["source"].get("sha256"))
                                       for entry in report["archive_pairs"]],
                          writer_scan=report["remote"].get("writer_scan"),
                          before=report["remote"].get("before"),
                          after=report["remote"].get("after")), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
