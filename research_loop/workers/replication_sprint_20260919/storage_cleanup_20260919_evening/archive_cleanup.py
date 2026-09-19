"""Exact three-archive cleanup, with independently checked surviving archives."""

import argparse
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

from audit import (
    ARCHIVE_NAMES, ARCHIVE_ROOT, EVIDENCE, HERE, READ_ONLY, REMOTE_HOME, REPO,
    compare, encoded_command, hash_file, metadata, now, scanner_program,
    space, write_receipt,
)


def all_reference_program():
    source = scanner_program(EVIDENCE / "coalescence_locked/pidfd_scan.py")
    replacements = (
        ("if mode!=os.O_RDONLY:", "if True:"),
        ("if len(fields)<5 or b'w' not in fields[1]: continue", "if len(fields)<5: continue"),
        ("all_uid_privileged_fds_and_writable_maps", "all_uid_privileged_fds_and_all_maps"),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError("original_scanner_changed")
        source = source.replace(old, new)
    return source


def archive_integrity(path, expected_size):
    started = now()
    before = hash_file(path, expected_size)
    if before["status"] != "stable_fresh_sha256":
        raise ValueError("survivor_hash_failed")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC)
    count = 0
    payload_bytes = 0
    hardlinks = 0
    verified_payloads = set()
    member_digest = hashlib.sha256()
    with os.fdopen(descriptor, "rb") as handle:
        if metadata(os.fstat(handle.fileno())) != before["before"]:
            raise ValueError("survivor_changed_before_integrity_read")
        with gzip.GzipFile(fileobj=handle, mode="rb") as compressed:
            with tarfile.open(fileobj=compressed, mode="r|") as archive:
                for member in archive:
                    count += 1
                    payload_bytes += member.size
                    name = PurePosixPath(member.name)
                    if (count > 100000 or payload_bytes > 8 * 1024**3
                            or name.is_absolute() or ".." in name.parts
                            or not (member.isfile() or member.isdir() or member.islnk())):
                        raise ValueError("unsafe_or_unbounded_archive_member")
                    if member.islnk():
                        target = PurePosixPath(member.linkname)
                        if target.is_absolute() or ".." in target.parts or str(target) not in verified_payloads:
                            raise ValueError("hardlink_target_not_previously_validated_payload")
                        verified_payloads.add(str(name))
                        hardlinks += 1
                    encoded = json.dumps([member.name, member.size, member.type.decode("ascii")])
                    member_digest.update((encoded + "\n").encode())
                    if member.isfile():
                        remaining = member.size
                        payload = archive.extractfile(member)
                        with payload:
                            while remaining:
                                chunk = payload.read(min(4 * 1024 * 1024, remaining))
                                if not chunk:
                                    raise ValueError("truncated_tar_payload")
                                remaining -= len(chunk)
                        verified_payloads.add(str(name))
            tail_bytes = 0
            while True:
                chunk = compressed.read(1024 * 1024)
                if not chunk:
                    break
                tail_bytes += len(chunk)
                if tail_bytes > 1024 * 1024 or chunk.strip(b"\0"):
                    raise ValueError("unexpected_trailing_archive_payload")
        if metadata(os.fstat(handle.fileno())) != before["before"]:
            raise ValueError("survivor_changed_during_integrity_read")
    after = hash_file(path, expected_size)
    if not compare(before, after) or before["before"] != after["before"]:
        raise ValueError("survivor_changed_after_integrity_read")
    return dict(path=str(path), started_utc=started, finished_utc=now(),
                status="all_payloads_streamed_hardlinks_resolved_gzip_crc_and_tar_validated_no_extraction",
                members=count, validated_hardlinks=hardlinks, regular_payload_bytes=payload_bytes,
                member_metadata_sha256=member_digest.hexdigest(), before=before, after=after)


GATES = r'''
def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def exact_archive_binding(entries, root, names):
    require(len(entries) == len(names), "exact_three_archive_count")
    require([entry["remote_path"] for entry in entries] == [root + "/" + name for name in names],
            "exact_three_original_archive_paths")
    for entry in entries:
        info = entry["source"]["before"]
        require(entry["fresh_identical_pair"] and entry["both_match_historical_sha256"],
                "fresh_pair_and_historical_binding")
        require(info["uid"] == 2524 and info["nlink"] == 1 and info["size"] == entry["expected_bytes"],
                "owned_single_link_archive")

def validate_reference_scan(scan, owned_readers=None):
    require(scan.get("scanner_euid") == 0
            and scan.get("scope") == "all_uid_privileged_fds_and_all_maps"
            and scan.get("lifetime_protocol") == "pidfd_start_bound_v1"
            and scan.get("inaccessible_or_exited") == [], "complete_no_uncertainty_scan_required")
    require(isinstance(scan.get("writers"), list), "reference_list_required")
    expected = set(owned_readers or ())
    seen = set()
    for reference in scan["writers"]:
        key = (reference.get("pid"), reference.get("start_ticks"), reference.get("fd"))
        require(reference.get("access_mode") == 0 and key in expected,
                "external_reader_writer_or_mapping_present")
        require(key not in seen, "duplicate_controlled_reader")
        seen.add(key)
    require(seen == expected, "exact_controlled_readers_accounted_for")
'''

exec(GATES)


def prepare():
    audit_raw = (HERE / "AUDIT_RECEIPT.json").read_bytes()
    audit = json.loads(audit_raw)
    entries = audit["archive_pairs"]
    exact_archive_binding(entries, ARCHIVE_ROOT, ARCHIVE_NAMES)
    require(audit["complete_original_writer_snapshot"], "original_writer_scan_failed")
    integrity = []
    for entry in entries:
        integrity.append(archive_integrity(entry["survivor_path"], entry["expected_bytes"]))
    write_receipt("ARCHIVE_INTEGRITY.json", dict(utc=now(), archives=integrity,
                                               extracted_files=0, bulk_bytes_transferred=0))
    manifest = dict(
        schema="exact_archive_deletion_manifest_v1", utc=now(),
        classification="non_material_redundant_retired_transport_copy_cleanup",
        authorization="User explicitly authorized this bounded redundant-copy cleanup; no other paths authorized.",
        audit_receipt_sha256=hashlib.sha256(audit_raw).hexdigest(),
        integrity_receipt_sha256=hashlib.sha256((HERE / "ARCHIVE_INTEGRITY.json").read_bytes()).hexdigest(),
        executor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        all_reference_scanner_sha256=hashlib.sha256(all_reference_program().encode()).hexdigest(),
        entries=entries, expected_logical_bytes=sum(entry["expected_bytes"] for entry in entries),
        expected_allocated_bytes=sum(entry["source"]["before"]["allocated_bytes"] for entry in entries),
        excluded="All records, checkpoints outside these transport copies, optimizer/RNG/history/failure evidence, old coalescer batches, live roots, reserves and credentials",
        requires_fresh_predelete_sha_and_scan=True, automatic_retry=False,
    )
    write_receipt("DELETION_MANIFEST.json", manifest)
    print(json.dumps(dict(manifest="DELETION_MANIFEST.json",
                          expected_allocated_bytes=manifest["expected_allocated_bytes"],
                          validated_archives=len(integrity)), indent=2))


REMOTE_DELETE = r'''
import fcntl, select, subprocess, sys
report = dict(started_utc=now(), host=os.uname().nodename, uid=os.getuid(),
              manifest_sha256=config["manifest_sha256"], before=space(config["home"]),
              deletions=[], scans=[], automatic_retry=False)
opened = []
directory_fd = None
def scan_references():
    result = subprocess.run(["sudo", "-n", "python3", "-B", "-c", config["scanner"]],
                            input=json.dumps([entry["remote_path"] for entry in config["entries"]]),
                            capture_output=True, text=True, timeout=45)
    require(result.returncode == 0, "read_only_privileged_scan_denied_or_failed:" + result.stderr[-2000:])
    scan = json.loads(result.stdout)
    report["scans"].append(scan)
    own_start = int(Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19])
    readers = {(os.getpid(), own_start, descriptor) for entry, descriptor in opened}
    validate_reference_scan(scan, readers)

try:
    require(os.getuid() == os.geteuid() == 2524, "delete_as_original_account_only")
    exact_archive_binding(config["entries"], config["root"], config["names"])
    root = Path(config["root"])
    require(root.resolve(strict=True) == root, "archive_parent_not_redirected")
    directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    parent_identity = os.fstat(directory_fd)
    require(parent_identity.st_uid == os.getuid(), "owned_archive_parent")
    report["fresh_sources"] = []
    for entry in config["entries"]:
        source = hash_file(entry["remote_path"], entry["expected_bytes"])
        report["fresh_sources"].append(source)
        require(source.get("sha256") == entry["source"]["sha256"]
                and source.get("before") == entry["source"]["before"], "fresh_source_hash_and_identity")
        descriptor = os.open(Path(entry["remote_path"]).name,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC,
                             dir_fd=directory_fd)
        opened.append((entry, descriptor))
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(metadata(os.fstat(descriptor)) == source["before"], "bound_archive_fd_identity")
    scan_references()
    report["ready_utc"] = now()
    print(json.dumps(dict(event="ready", receipt=report), sort_keys=True), flush=True)
    require(select.select([sys.stdin], [], [], 120)[0], "external_receipt_ack_timeout")
    require(sys.stdin.readline().strip() == "DELETE " + config["manifest_sha256"], "durable_manifest_ack_required")
    scan_references()
    report["immediate_before"] = space(config["home"])
    for entry, descriptor in opened:
        require(root.resolve(strict=True) == root, "parent_path_redirected_before_unlink")
        current_parent = root.stat()
        require((current_parent.st_dev, current_parent.st_ino) ==
                (parent_identity.st_dev, parent_identity.st_ino), "parent_identity_changed")
        name = Path(entry["remote_path"]).name
        require(metadata(os.stat(name, dir_fd=directory_fd, follow_symlinks=False)) == entry["source"]["before"]
                and metadata(os.fstat(descriptor)) == entry["source"]["before"], "last_instant_exact_file_identity")
        os.unlink(name, dir_fd=directory_fd)
        deletion = dict(path=entry["remote_path"], utc=now(), sha256=entry["source"]["sha256"],
                        logical_bytes=entry["expected_bytes"],
                        allocated_bytes=entry["source"]["before"]["allocated_bytes"],
                        surviving_archive=entry["survivor_path"], unlink_returned_success=True)
        report["deletions"].append(deletion)
        require(os.fstat(descriptor).st_nlink == 0, "last_link_not_removed")
        deletion["last_link_removed"] = True
    os.fsync(directory_fd)
    report["status"] = "exact_three_archive_copies_deleted"
except Exception as error:
    report["status"] = "stopped_no_retry"
    report["error"] = dict(type=type(error).__name__, message=str(error))
finally:
    for entry, descriptor in opened:
        os.close(descriptor)
    if directory_fd is not None:
        os.close(directory_fd)
report["all_controlled_descriptors_closed"] = True
report["after"] = space(config["home"])
report["finished_utc"] = now()
report["actual_unlinked_allocated_bytes"] = sum(entry["allocated_bytes"] for entry in report["deletions"])
report["postdelete_paths_absent"] = {entry["remote_path"]: not os.path.lexists(entry["remote_path"])
                                      for entry in config["entries"]}
print(json.dumps(dict(event="complete", receipt=report), sort_keys=True), flush=True)
'''


def execute():
    for filename in ("PREDELETE_RECEIPT.json", "DELETION_RECEIPT.json"):
        require(not (HERE / filename).exists(), "existing_execution_receipt_no_retry")
    raw = (HERE / "DELETION_MANIFEST.json").read_bytes()
    manifest = json.loads(raw)
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == manifest["executor_sha256"],
            "executor_matches_prepared_manifest")
    require(hashlib.sha256((HERE / "AUDIT_RECEIPT.json").read_bytes()).hexdigest() == manifest["audit_receipt_sha256"],
            "unchanged_audit_receipt")
    require(hashlib.sha256((HERE / "ARCHIVE_INTEGRITY.json").read_bytes()).hexdigest() == manifest["integrity_receipt_sha256"],
            "unchanged_integrity_receipt")
    scanner = all_reference_program()
    require(hashlib.sha256(scanner.encode()).hexdigest() == manifest["all_reference_scanner_sha256"],
            "unchanged_strengthened_scanner")
    exact_archive_binding(manifest["entries"], ARCHIVE_ROOT, ARCHIVE_NAMES)
    config = dict(entries=manifest["entries"], root=ARCHIVE_ROOT, names=ARCHIVE_NAMES,
                  scanner=scanner, home=REMOTE_HOME, manifest_sha256=hashlib.sha256(raw).hexdigest())
    local_before = space(REPO)
    with ExitStack() as stack:
        survivor_handles = []
        for entry in manifest["entries"]:
            verified = hash_file(entry["survivor_path"], entry["expected_bytes"])
            require(compare(verified, entry["survivor"])
                    and verified["before"] == entry["survivor"]["before"], "fresh_unchanged_survivor_required")
            descriptor = os.open(entry["survivor_path"], os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC)
            handle = stack.enter_context(os.fdopen(descriptor, "rb"))
            fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
            require(metadata(os.fstat(handle.fileno())) == verified["before"], "survivor_fd_binding")
            survivor_handles.append((entry, handle))
        program = READ_ONLY + GATES + "\nconfig=" + repr(config) + REMOTE_DELETE
        with subprocess.Popen(["bash", str(REPO / "gpu/ovx_ssh.sh"), encoded_command(program)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as process:
            ready = json.loads(process.stdout.readline())
            if ready["event"] == "ready":
                write_receipt("PREDELETE_RECEIPT.json", ready["receipt"])
                for entry, handle in survivor_handles:
                    require(metadata(Path(entry["survivor_path"]).lstat()) == entry["survivor"]["before"]
                            and metadata(os.fstat(handle.fileno())) == entry["survivor"]["before"],
                            "survivor_still_bound_before_ack")
                process.stdin.write("DELETE " + config["manifest_sha256"] + "\n")
                process.stdin.flush()
                outcome = json.loads(process.stdout.readline())
            else:
                outcome = ready
            process.stdin.close()
            stderr = process.stderr.read()
            returncode = process.wait()
        receipt = outcome["receipt"]
        receipt["ssh_returncode"] = returncode
        receipt["ssh_stderr"] = stderr
        receipt["postdelete_survivors"] = [hash_file(entry["survivor_path"], entry["expected_bytes"])
                                            for entry in manifest["entries"]]
        receipt["survivors_still_identical"] = all(
            compare(verified, entry["survivor"]) and verified["before"] == entry["survivor"]["before"]
            for verified, entry in zip(receipt["postdelete_survivors"], manifest["entries"]))
        receipt["local_before"] = local_before
        receipt["local_after"] = space(REPO)
        write_receipt("DELETION_RECEIPT.json", receipt)
    print(json.dumps(dict(status=receipt["status"], deleted=len(receipt["deletions"]),
                          allocated_bytes=receipt["actual_unlinked_allocated_bytes"],
                          survivors_still_identical=receipt["survivors_still_identical"],
                          before=receipt.get("immediate_before", receipt["before"]),
                          after=receipt["after"], error=receipt.get("error")), indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "execute"))
    arguments = parser.parse_args()
    if arguments.mode == "prepare":
        prepare()
    else:
        execute()


if __name__ == "__main__":
    main()
