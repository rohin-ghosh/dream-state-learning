"""Read-only, single-pass tar custody; never native replay or promotion."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tarfile
import time

BLOCK = 512
CHUNK = 1024 * 1024
MAX_SEAL = 64 * CHUNK
MAX_METADATA = CHUNK
EXCEPTIONS = {"SEAL.json", "FINALIZED.json", "FINALIZATION_ABORT.json"}
PAX_KEYS = {"path", "mtime", "atime", "ctime", "uid", "gid", "uname", "gname"}


class CustodyError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CustodyError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def valid_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def strict_json(data):
    def nonfinite(value):
        raise CustodyError("nonfinite JSON value: " + value)

    return json.loads(data, object_pairs_hook=unique_object, parse_constant=nonfinite)


def safe_name(name):
    require(isinstance(name, str) and 0 < len(name) <= 4096, "invalid pathname length/type")
    require(all(32 <= ord(character) <= 126 for character in name), "non-printable/non-ASCII pathname")
    require("\\" not in name, "backslash pathname requires sha256sum escaping")
    require(not name.startswith("/"), "absolute pathname")
    require(not re.match(r"^[A-Za-z]:", name), "drive-qualified pathname")
    require(all(part not in ("", ".", "..") for part in name.split("/")), "noncanonical/traversal pathname")
    return name


def fingerprint(details):
    return {key: getattr(details, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")}


def open_regular(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "input is not a regular file: " + str(path))
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


class HashReader:
    def __init__(self, stream):
        self.stream = stream
        self.hash = hashlib.sha256()
        self.count = 0

    def read(self, length):
        require(0 <= length <= CHUNK, "unbounded stream read")
        data = self.stream.read(length)
        self.hash.update(data)
        self.count += len(data)
        return data

    def exact(self, length):
        require(length <= CHUNK, "unbounded exact read")
        chunks = []
        remaining = length
        while remaining:
            data = self.read(remaining)
            require(bool(data), "truncated tar stream")
            chunks.append(data)
            remaining -= len(data)
        return b"".join(chunks)

    def padding(self, size):
        padding = (-size) % BLOCK
        if padding:
            require(not any(self.exact(padding)), "nonzero member padding")


def pax_path(data):
    fields = {}
    position = 0
    while position < len(data):
        space = data.find(b" ", position)
        require(space > position, "malformed PAX record length")
        number = data[position:space]
        require(number.isdigit() and not number.startswith(b"0"), "invalid PAX length")
        length = int(number)
        end = position + length
        require(space + 2 < end <= len(data) and data[end - 1:end] == b"\n", "truncated PAX record")
        content = data[space + 1:end - 1]
        require(b"=" in content, "malformed PAX key/value")
        key, value = content.split(b"=", 1)
        key = key.decode("ascii")
        require(key in PAX_KEYS and key not in fields, "unsupported/duplicate PAX key: " + key)
        fields[key] = value.decode("utf-8")
        position = end
    if "path" in fields:
        return fields["path"]
    return None


def root_stream_digest(files):
    checksum = hashlib.sha256()
    size = 0
    for name in sorted(files, key=lambda value: value.encode("ascii")):
        safe_name(name)
        require(valid_digest(files[name]), "invalid root stream payload hash")
        line = (files[name] + "  ./" + name + "\n").encode("ascii")
        checksum.update(line)
        size += len(line)
    return checksum.hexdigest(), size


def scan_tar(reader, expected, seal_bytes, report):
    files = {}
    seen = set()
    ancestors = set()
    regular_names = set()
    metadata = {}
    topdir = None
    pending_extension = False
    extended_name = None
    counts = report["counts"]
    while True:
        header = reader.exact(BLOCK)
        if header == bytes(BLOCK):
            require(not pending_extension, "orphaned tar path extension")
            require(reader.exact(BLOCK) == bytes(BLOCK), "missing second tar end block")
            while True:
                tail = reader.read(CHUNK)
                if not tail:
                    break
                require(not any(tail), "nonzero trailing data/concatenated archive")
            require(reader.count % BLOCK == 0, "unaligned tar trailer")
            break
        member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
        require(member.size >= 0, "negative member size")
        if member.type in (tarfile.GNUTYPE_LONGNAME, tarfile.XHDTYPE):
            require(not pending_extension, "chained tar metadata extensions")
            require(0 < member.size <= MAX_METADATA, "tar extension exceeds bound")
            payload = reader.exact(member.size)
            reader.padding(member.size)
            if member.type == tarfile.GNUTYPE_LONGNAME:
                require(payload.endswith(b"\0") and b"\0" not in payload[:-1], "malformed GNU long pathname")
                extended_name = payload[:-1].decode("utf-8")
                counts["gnu_longname_headers"] += 1
            else:
                extended_name = pax_path(payload)
                counts["pax_headers"] += 1
            pending_extension = True
            continue
        require(member.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE), "link/special/unsupported tar member")
        require(not member.linkname and member.sparse is None, "link/sparse metadata is forbidden")
        directory = member.type == tarfile.DIRTYPE
        name = extended_name if extended_name is not None else member.name
        if directory:
            raw_name = header[:100].split(b"\0", 1)[0]
            require(not raw_name.endswith(b"//"), "noncanonical directory trailing slashes")
            if name.endswith("/"):
                name = name[:-1]
        name = safe_name(name)
        pending_extension, extended_name = False, None
        parts = name.split("/")
        if topdir is None:
            topdir = parts[0]
        require(parts[0] == topdir, "multiple top-level directories")
        require(name not in seen, "duplicate archive member: " + name)
        require(not any("/".join(parts[:index]) in regular_names for index in range(1, len(parts))), "regular file used as directory")
        require(directory or name not in ancestors, "regular file conflicts with existing descendants")
        seen.add(name)
        ancestors.update("/".join(parts[:index]) for index in range(1, len(parts)))
        if directory:
            require(member.size == 0, "directory member has payload")
            counts["directories"] += 1
            continue
        require(len(parts) > 1, "regular member outside the single top directory")
        regular_names.add(name)
        relative = "/".join(parts[1:])
        require(relative in expected or relative in EXCEPTIONS, "additional unsealed regular file: " + relative)
        if relative == "SEAL.json":
            require(member.size == len(seal_bytes), "archive seal byte length differs from standalone seal")
        if relative in EXCEPTIONS - {"SEAL.json"}:
            require(member.size <= MAX_METADATA, "terminal metadata exceeds bound")
        checksum = hashlib.sha256()
        collected = []
        remaining = member.size
        position = 0
        while remaining:
            payload = reader.exact(min(CHUNK, remaining))
            checksum.update(payload)
            if relative == "SEAL.json":
                require(payload == seal_bytes[position:position + len(payload)], "archive seal exact bytes differ from standalone seal")
            elif relative in EXCEPTIONS:
                collected.append(payload)
            position += len(payload)
            remaining -= len(payload)
        reader.padding(member.size)
        digest = checksum.hexdigest()
        files[relative] = digest
        counts["regular_files"] += 1
        counts["regular_payload_bytes"] += member.size
        if relative in expected:
            require(digest == expected[relative], "sealed payload hash mismatch: " + relative)
            counts["sealed_files_verified"] += 1
        if relative in EXCEPTIONS:
            metadata[relative] = {"sha256": digest, "bytes": member.size}
            if relative != "SEAL.json":
                metadata[relative]["content"] = strict_json(b"".join(collected))
    require(topdir is not None, "empty archive")
    missing = sorted(set(expected) - set(files))
    report["missing_sealed_files"] = missing
    report["top_directory"] = topdir
    report["terminal_metadata"] = metadata
    report["full_root_stream_sha256"], report["full_root_stream_bytes"] = root_stream_digest(files)
    report["full_root_regular_files"] = len(files)
    report["observed_payload_mapping_sha256"] = sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode("ascii"))
    require(not missing, "missing sealed files: " + ", ".join(missing[:10]))
    require("SEAL.json" in metadata, "missing archive SEAL.json")
    require("FINALIZED.json" in metadata, "missing archive FINALIZED.json")
    finalized = metadata["FINALIZED.json"]["content"]
    require(isinstance(finalized, dict) and finalized.get("seal_sha256") == sha256(seal_bytes), "FINALIZED does not bind exact seal bytes")
    if "FINALIZATION_ABORT.json" in metadata:
        aborted = metadata["FINALIZATION_ABORT.json"]["content"]
        require(isinstance(aborted, dict) and aborted.get("seal_sha256") == sha256(seal_bytes), "FINALIZATION_ABORT seal binding differs")
        if "finalized_sha256" in aborted:
            require(aborted["finalized_sha256"] == metadata["FINALIZED.json"]["sha256"], "FINALIZATION_ABORT finalized binding differs")
    for entry in metadata.values():
        entry.pop("content", None)
    report["seal_exact_bytes_match"] = True
    report["finalized_seal_binding_verified"] = True


def verify_archive(archive, expected_archive_sha256, seal, expected_root_stream_sha256=None, expected_seal_sha256=None):
    archive, seal = Path(archive).absolute(), Path(seal).absolute()
    started = time.perf_counter()
    report = {
        "schema": "astra_q0_tar_custody_v1", "status": "FAIL_CUSTODY", "custody_only": True,
        "scientific_replay_performed": False, "promotion_or_reclassification": False,
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "archive_path": str(archive), "standalone_seal_path": str(seal),
        "expected_archive_sha256": expected_archive_sha256,
        "expected_full_root_stream_sha256": expected_root_stream_sha256,
        "expected_standalone_seal_sha256": expected_seal_sha256,
        "archive_hash_complete": False, "errors": [],
        "counts": dict(regular_files=0, sealed_files_verified=0, regular_payload_bytes=0, directories=0, gnu_longname_headers=0, pax_headers=0),
        "root_stream_semantics": "ASCII byte-sorted relative paths; SHA256 of concatenated '<payload_sha256>  ./<relative_path>\\n'; all regular files, including SEAL/FINALIZED/FINALIZATION_ABORT; backslashes, controls and non-ASCII names rejected",
        "limitations": ["Custody only; no model/GPU execution, replay, scientific result verification, promotion or reclassification.", "Full-root stream reproduces bytewise path sorting; independently supplied expected digest is required to bind the external observation. Observer identity/time is not independently re-established.", "Uncompressed GNU/USTAR tar, GNU long path headers, and bounded local PAX path/time/owner metadata only. Links, sparse files, global PAX, size overrides and other special members rejected.", "Streaming payload reads use at most 1 MiB; standalone seal is bounded to 64 MiB and manifests/path digests are held in memory. No real payload is extracted.", "Input identity/size/mtime/ctime are checked before/after; atime may change due to ordinary filesystem reads. Directory metadata and file modes are not bound by the root content stream."],
    }
    reader = None
    try:
        require(valid_digest(expected_archive_sha256), "invalid expected archive SHA256")
        require(expected_root_stream_sha256 is None or valid_digest(expected_root_stream_sha256), "invalid expected full-root stream SHA256")
        require(expected_seal_sha256 is None or valid_digest(expected_seal_sha256), "invalid expected standalone seal SHA256")
        with open_regular(seal) as seal_stream, open_regular(archive) as archive_stream:
            before_seal, before_archive = fingerprint(os.fstat(seal_stream.fileno())), fingerprint(os.fstat(archive_stream.fileno()))
            report["input_before"] = {"archive": before_archive, "seal": before_seal}
            require(before_seal["st_size"] <= MAX_SEAL, "standalone seal exceeds 64 MiB")
            seal_bytes = seal_stream.read(MAX_SEAL + 1)
            require(len(seal_bytes) == before_seal["st_size"], "standalone seal changed during read")
            report["standalone_seal_sha256"] = sha256(seal_bytes)
            require(expected_seal_sha256 is None or sha256(seal_bytes) == expected_seal_sha256, "standalone seal expected hash mismatch")
            parsed = strict_json(seal_bytes)
            require(isinstance(parsed, dict) and isinstance(parsed.get("files"), dict), "seal files must be a path-to-SHA256 mapping")
            expected = parsed["files"]
            for name, digest in expected.items():
                safe_name(name)
                require(valid_digest(digest), "invalid sealed file SHA256: " + name)
            report["expected_sealed_file_count"] = len(expected)
            reader = HashReader(archive_stream)
            try:
                scan_tar(reader, expected, seal_bytes, report)
                report["archive_hash_complete"] = True
                report["archive_sha256"] = reader.hash.hexdigest()
                require(reader.count == before_archive["st_size"], "archive byte length changed")
                require(report["archive_sha256"] == expected_archive_sha256, "archive expected SHA256 mismatch")
                report["archive_sha256_matches"] = True
                report["full_root_stream_matches_expected"] = None if expected_root_stream_sha256 is None else report["full_root_stream_sha256"] == expected_root_stream_sha256
                require(expected_root_stream_sha256 is None or report["full_root_stream_matches_expected"], "full-root stream expected SHA256 mismatch")
            finally:
                after = {"archive": fingerprint(os.fstat(archive_stream.fileno())), "seal": fingerprint(os.fstat(seal_stream.fileno()))}
                current = {"archive": fingerprint(archive.stat(follow_symlinks=False)), "seal": fingerprint(seal.stat(follow_symlinks=False))}
                report["input_after"] = after
                report["input_path_after"] = current
                report["inputs_unchanged"] = after == current == report["input_before"]
                require(report["inputs_unchanged"], "input changed/replaced during custody verification")
        report["status"] = "PASS_CUSTODY"
    except (ValueError, OSError, tarfile.TarError, UnicodeError, OverflowError) as error:
        report["errors"].append({"type": type(error).__name__, "message": str(error)})
    if reader is not None:
        report["archive_bytes_streamed"] = reader.count
        report["streamed_bytes_sha256"] = reader.hash.hexdigest()
    report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["duration_seconds"] = round(time.perf_counter() - started, 6)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--expected-root-stream", "--expected-root-stream-sha256", dest="expected_root_stream")
    parser.add_argument("--seal-sha256")
    parser.add_argument("--out", type=Path, help="Exclusive new JSON receipt; omit for stdout only")
    options = parser.parse_args(argv)
    if options.out is not None:
        if options.out.exists() or options.out.is_symlink() or options.out.resolve() in (options.archive.resolve(), options.seal.resolve()):
            parser.error("output must be a new path distinct from both preserved inputs")
    report = verify_archive(options.archive, options.archive_sha256, options.seal, options.expected_root_stream, options.seal_sha256)
    report["command_argv"] = [sys.executable, "-B", str(Path(__file__).absolute())] + (list(argv) if argv is not None else sys.argv[1:])
    data = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if options.out is not None:
        descriptor = os.open(options.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
    sys.stdout.write(data.decode("utf-8"))
    return 0 if report["status"] == "PASS_CUSTODY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
