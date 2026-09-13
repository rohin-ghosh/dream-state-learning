"""Exclusive, SHA-pinned delta custody; plain tar, no extraction or model loading."""

import argparse
import contextlib
import dataclasses
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import tarfile


CHUNK = 8 * 1024 * 1024
ROSTER_MEMBER = "custody/astra_node1_preservation_delta_20260913.json"
EXPECTED_COUNTS = (348, 419)
SCHEMA = "astra.node1_preservation_delta.v1"


class CustodyError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CustodyError(message)


def digest_string(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
            "Expected a lowercase SHA256")
    return value


def member_path(value):
    require(isinstance(value, str) and value and "\\" not in value
            and "\x00" not in value and all(part not in ("", ".", "..")
                                           for part in value.split("/")),
            "Unsafe or noncanonical member path")
    return value


def absolute_path(value):
    raw = os.fspath(value)
    require("\x00" not in raw and ".." not in raw.split("/"), "Unsafe local path")
    return Path(os.path.abspath(raw))


@contextlib.contextmanager
def directory_fd(path):
    path = absolute_path(path)
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


@contextlib.contextmanager
def source_file(home_fd, relative):
    parts = member_path(relative).split("/")
    descriptor = os.dup(home_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=descriptor)
        try:
            require(stat.S_ISREG(os.fstat(file_fd).st_mode),
                    "Source is not a regular file: " + relative)
            stream = os.fdopen(file_fd, "rb")
        except BaseException:
            os.close(file_fd)
            raise
        with stream:
            yield stream
    finally:
        os.close(descriptor)


def open_local(path, exclusive=False):
    path = absolute_path(path)
    with directory_fd(path.parent) as parent_fd:
        flags = os.O_NOFOLLOW | os.O_NONBLOCK
        flags |= os.O_WRONLY | os.O_CREAT | os.O_EXCL if exclusive else os.O_RDONLY
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "Not a regular file")
        return os.fdopen(descriptor, "wb" if exclusive else "rb")
    except BaseException:
        os.close(descriptor)
        raise


@dataclasses.dataclass(frozen=True)
class Entry:
    name: str
    size: int
    mtime_ns: int
    sha256: str
    mode: int


@dataclasses.dataclass(frozen=True)
class Roster:
    raw: bytes
    sha256: str
    entries: tuple
    v6_count: int
    source_count: int


def entry_from_record(record):
    require(isinstance(record, dict), "Invalid file record")
    require(record.get("is_symlink") is False
            and record.get("stable_during_hash") is True,
            "Unstable or symlink roster member")
    size, mtime = record["size_bytes"], record["mtime_ns"]
    require(type(size) is int and size >= 0 and type(mtime) is int and mtime >= 0,
            "Invalid size or mtime")
    mode = int(record["mode_octal"], 8)
    require(0 <= mode <= 0o777, "Unsafe file mode")
    return Entry(member_path(record["relative_path"]), size, mtime,
                 digest_string(record["sha256"]), mode)


def load_roster(path, expected_sha256, expected_counts=EXPECTED_COUNTS):
    digest_string(expected_sha256)
    with open_local(path) as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    require(len(raw) <= 16 * 1024 * 1024, "Roster exceeds 16 MiB")
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, "Roster SHA256 mismatch")
    data = json.loads(raw)
    require(data["schema"] == SCHEMA and data["status"] == "READ_ONLY_ROSTER_HASHED_STABLE"
            and data["errors"] == [], "Roster is not a stable successful inventory")
    summary = data["summary"]
    require(summary["all_hash_reads_stable"] is True
            and summary["delta_hashes_bound_to_initial_stat"] is True,
            "Roster consistency flags failed")
    entries = []
    for group in ("missing_files", "changed_files"):
        require(summary[group] == len(data[group]), "Delta count disagreement")
        for record in data[group]:
            relative = member_path(record["relative_path"])
            payload = record["source_payload"]
            require(payload["relative_path"] == "v6_out/" + relative,
                    "v6_out member path binding mismatch")
            for key in ("size_bytes", "mtime_ns", "mode_octal", "is_symlink"):
                require(record["source"][key] == payload[key], "Source stat binding mismatch")
            entries.append(entry_from_record(payload))
    v6_count = len(entries)
    identities = set()
    for snapshot in data["source_snapshots"]:
        identity = snapshot["identity"]
        require(isinstance(identity, str) and re.fullmatch(r"[0-9a-f]{40}", identity)
                and identity not in identities, "Invalid or duplicate source snapshot")
        identities.add(identity)
        files = snapshot["files"]
        require(files == sorted(files, key=lambda record: record["snapshot_relative_path"]),
                "Unsorted snapshot member manifest")
        canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        require(hashlib.sha256(canonical).hexdigest() == snapshot["member_manifest_sha256"],
                "Snapshot member manifest hash mismatch")
        require(snapshot["file_count"] == len(files)
                and snapshot["total_bytes"] == sum(record["size_bytes"] for record in files),
                "Snapshot summary mismatch")
        for record in files:
            relative = member_path(record["snapshot_relative_path"])
            require(record["relative_path"] == "astra_sources/" + identity + "/" + relative,
                    "Source snapshot path binding mismatch")
            entries.append(entry_from_record(record))
    source_count = len(entries) - v6_count
    require((v6_count, source_count) == expected_counts, "Expected exactly 348+419 production files")
    require(summary["source_snapshot_files"] == source_count
            and summary["source_snapshot_bytes"] == sum(entry.size for entry in entries[v6_count:]),
            "Source snapshot totals mismatch")
    require(len(identities) == 2, "Expected two source snapshots")
    names = [entry.name for entry in entries]
    require(len(names) == len(set(names)) and ROSTER_MEMBER not in names,
            "Duplicate or reserved archive member")
    return Roster(raw, expected_sha256, tuple(sorted(entries, key=lambda entry: entry.name)),
                  v6_count, source_count)


def fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode)


def checked_stat(stream, entry, expected_identity=None):
    info = os.fstat(stream.fileno())
    require(stat.S_ISREG(info.st_mode) and info.st_size == entry.size
            and info.st_mtime_ns == entry.mtime_ns
            and stat.S_IMODE(info.st_mode) == entry.mode,
            "Source size/mtime/mode changed: " + entry.name)
    identity = fingerprint(info)
    require(expected_identity is None or identity == expected_identity,
            "Source identity changed: " + entry.name)
    return identity


class HashReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.count = 0

    def read(self, size=-1):
        chunk = self.stream.read(size)
        self.digest.update(chunk)
        self.count += len(chunk)
        return chunk


class HashWriter:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.count = 0

    def write(self, chunk):
        written = self.stream.write(chunk)
        require(written == len(chunk), "Short archive write")
        self.digest.update(chunk)
        self.count += written
        return written


def check_sources(home_fd, entries, expected_identities=None):
    identities = {}
    for entry in entries:
        expected = None if expected_identities is None else expected_identities[entry.name]
        with source_file(home_fd, entry.name) as stream:
            identity = checked_stat(stream, entry, expected)
            reader = HashReader(stream)
            while reader.read(CHUNK):
                pass
            require(reader.count == entry.size and reader.digest.hexdigest() == entry.sha256,
                    "Source hash changed: " + entry.name)
            checked_stat(stream, entry, identity)
            identities[entry.name] = identity
    return identities


def tar_info(name, size, mode, mtime=0):
    info = tarfile.TarInfo(name)
    info.size, info.mode, info.mtime = size, mode, mtime
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def add_source(archive, home_fd, entry, identity):
    with source_file(home_fd, entry.name) as stream:
        checked_stat(stream, entry, identity)
        reader = HashReader(stream)
        archive.addfile(tar_info(entry.name, entry.size, entry.mode,
                                 entry.mtime_ns // 1_000_000_000), reader)
        require(reader.count == entry.size and reader.digest.hexdigest() == entry.sha256,
                "Source changed while packing: " + entry.name)
        checked_stat(stream, entry, identity)


def output_paths(archive, receipt, roster_path, home=None):
    archive, receipt, roster_path = map(absolute_path, (archive, receipt, roster_path))
    require(len({archive, receipt, roster_path}) == 3, "Input/output paths overlap")
    require(not any(part in ("v6_out", "astra_sources") for part in receipt.parts),
            "Receipt must be outside source trees")
    if home is not None:
        home = absolute_path(home)
        for destination in (archive, receipt):
            require(not any(destination.is_relative_to(home / root)
                            for root in ("v6_out", "astra_sources")),
                    "Output must be outside source trees")
    return archive, receipt


def require_new(path):
    with directory_fd(path.parent) as parent_fd:
        try:
            os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
    raise CustodyError("Refusing to overwrite: " + str(path))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def receipt_base(operation, roster, archive):
    return {"schema": "astra.node1_delta_custody_receipt.v1", "operation": operation,
            "scope": "DELTA_ONLY_NOT_FULL_MIRROR_RESTORE", "started_utc": now(),
            "roster_sha256": roster.sha256, "roster_member": ROSTER_MEMBER,
            "v6_files": roster.v6_count, "source_files": roster.source_count,
            "payload_files": len(roster.entries), "tar_members": len(roster.entries) + 1,
            "payload_bytes": sum(entry.size for entry in roster.entries),
            "archive": str(archive)}


def save_receipt(stream, receipt):
    receipt["finished_utc"] = now()
    stream.write((json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode())
    stream.flush()
    os.fsync(stream.fileno())


def pack(home, roster_path, roster_sha256, archive_path, receipt_path,
         expected_counts=EXPECTED_COUNTS):
    roster = load_roster(roster_path, roster_sha256, expected_counts)
    archive_path, receipt_path = output_paths(archive_path, receipt_path, roster_path, home)
    require_new(archive_path)
    require_new(receipt_path)
    receipt = receipt_base("pack", roster, archive_path)
    receipt["source_home"] = str(absolute_path(home))
    with directory_fd(home) as home_fd:
        identities = check_sources(home_fd, roster.entries)
        with open_local(archive_path, exclusive=True) as target:
            with open_local(receipt_path, exclusive=True) as receipt_stream:
                try:
                    writer = HashWriter(target)
                    with tarfile.open(fileobj=writer, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                        archive.addfile(tar_info(ROSTER_MEMBER, len(roster.raw), 0o444), io.BytesIO(roster.raw))
                        for entry in roster.entries:
                            add_source(archive, home_fd, entry, identities[entry.name])
                    target.flush()
                    os.fsync(target.fileno())
                    check_sources(home_fd, roster.entries, identities)
                    require(os.fstat(target.fileno()).st_size == writer.count, "Archive size changed")
                    receipt.update(status="DELTA_PACKED", archive_sha256=writer.digest.hexdigest(),
                                   archive_bytes=writer.count, source_precheck=True,
                                   source_stream_check=True, source_postcheck=True)
                except BaseException as error:
                    receipt.update(status="ERROR_PARTIAL_ARCHIVE_PRESERVED",
                                   error=type(error).__name__ + ": " + str(error))
                    save_receipt(receipt_stream, receipt)
                    raise
                save_receipt(receipt_stream, receipt)
    return receipt


def verify(roster_path, roster_sha256, archive_path, archive_sha256, receipt_path,
           expected_counts=EXPECTED_COUNTS):
    roster = load_roster(roster_path, roster_sha256, expected_counts)
    digest_string(archive_sha256)
    archive_path, receipt_path = output_paths(archive_path, receipt_path, roster_path)
    require_new(receipt_path)
    receipt = receipt_base("verify", roster, archive_path)
    expected = {entry.name: entry for entry in roster.entries}
    expected[ROSTER_MEMBER] = Entry(ROSTER_MEMBER, len(roster.raw), 0, roster.sha256, 0o444)
    with open_local(archive_path) as source, open_local(receipt_path, exclusive=True) as receipt_stream:
        try:
            initial = fingerprint(os.fstat(source.fileno()))
            reader = HashReader(source)
            seen = set()
            with tarfile.open(fileobj=reader, mode="r|") as archive:
                for member in archive:
                    name = member_path(member.name)
                    require(name in expected and name not in seen, "Unexpected or duplicate archive member")
                    require(member.type == tarfile.REGTYPE and not member.issparse(),
                            "Nonregular or sparse archive member")
                    entry = expected[name]
                    require(member.size == entry.size and member.mode == entry.mode
                            and member.mtime == entry.mtime_ns // 1_000_000_000,
                            "Archive member metadata mismatch: " + name)
                    with archive.extractfile(member) as stream:
                        payload = HashReader(stream)
                        while payload.read(CHUNK):
                            pass
                    require(payload.count == entry.size and payload.digest.hexdigest() == entry.sha256,
                            "Archive payload hash mismatch: " + name)
                    seen.add(name)
                require(seen == set(expected), "Archive members missing")
                while True:
                    trailing = archive.fileobj.read(CHUNK)
                    if not trailing:
                        break
                    require(not any(trailing), "Nonzero trailing archive data")
            require(fingerprint(os.fstat(source.fileno())) == initial, "Archive changed during verification")
            require(reader.count == initial[2] and reader.digest.hexdigest() == archive_sha256,
                    "Archive SHA256/size mismatch")
            receipt.update(status="DELTA_VERIFIED", archive_sha256=reader.digest.hexdigest(),
                           archive_bytes=reader.count, full_member_bytes_verified=True,
                           extraction_performed=False, source_accessed=False)
        except BaseException as error:
            receipt.update(status="ERROR_ARCHIVE_PRESERVED",
                           error=type(error).__name__ + ": " + str(error))
            save_receipt(receipt_stream, receipt)
            raise
        save_receipt(receipt_stream, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for operation in ("pack", "verify"):
        child = commands.add_parser(operation)
        child.add_argument("--roster", required=True)
        child.add_argument("--roster-sha256", required=True)
        child.add_argument("--archive", required=True)
        child.add_argument("--receipt", required=True, help="NEW external output receipt")
        if operation == "pack":
            child.add_argument("--home", required=True)
        else:
            child.add_argument("--archive-sha256", required=True, help="Pin from successful pack receipt")
    args = parser.parse_args(argv)
    try:
        if args.command == "pack":
            result = pack(args.home, args.roster, args.roster_sha256, args.archive, args.receipt)
        else:
            result = verify(args.roster, args.roster_sha256, args.archive,
                            args.archive_sha256, args.receipt)
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({"status": "ERROR", "error": type(error).__name__ + ": " + str(error),
                          "existing_and_partial_archives_preserved": True}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
