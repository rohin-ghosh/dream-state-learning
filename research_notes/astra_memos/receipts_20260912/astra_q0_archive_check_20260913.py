"""Streaming Q0 archive custody only; never a numerical or scientific replay."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tarfile
import zlib


CHUNK_BYTES = 1024 * 1024
MAX_METADATA_BYTES = 32 * 1024 * 1024
EXCLUDED = frozenset(("SEAL.json", "FINALIZED.json", "FINALIZATION_ABORT.json"))
VERSION = "astra-pairwise-q0-cpu-sidecar-v1"
EVIDENCE_KIND = "Q0_NATIVE_RAW"


class CustodyError(ValueError):
    """The supplied bytes do not satisfy the archive custody contract."""


def require(condition, message):
    if not condition:
        raise CustodyError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def expected_hash(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value),
            label + " must be a caller-provided 64-hex SHA256")
    return value.lower()


def member_name(name, *, directory=False):
    require(isinstance(name, str) and name and not name.startswith("/")
            and "\\" not in name and not any(ord(character) < 32 or ord(character) == 127 for character in name),
            "unsafe archive member path")
    while name.startswith("./"):
        name = name[2:]
    if directory and name in ("", "."):
        return "."
    if directory and name.endswith("/"):
        name = name[:-1]
    parts = name.split("/")
    require(all(part not in ("", ".", "..") for part in parts)
            and not re.match(r"^[A-Za-z]:", name), "unsafe archive member path: " + name)
    return "/".join(parts)


def parse_metadata(content, label):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key in " + label)
            result[key] = value
        return result

    def nonfinite(value):
        raise CustodyError("nonfinite JSON constant in " + label)

    value = json.loads(content.decode("utf-8"), object_pairs_hook=unique_object,
                       parse_constant=nonfinite)
    require(isinstance(value, dict), label + " must be a JSON object")
    return value


class HashingReader:
    def __init__(self, source):
        self.source = source
        self.hasher = hashlib.sha256()
        self.byte_count = 0

    def read(self, size):
        require(size >= 0, "unbounded archive read forbidden")
        data = self.source.read(size)
        self.hasher.update(data)
        self.byte_count += len(data)
        return data


def file_identity(status):
    return (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)


def _validate_archive(path, archive_sha256, manifest_sha256):
    expected_archive = expected_hash(archive_sha256, "archive SHA256")
    expected_manifest = expected_hash(manifest_sha256, "prepared manifest SHA256")
    hashes, sizes, metadata, members = {}, {}, {}, {}
    ancestor_paths = set()
    directory_count = 0
    with Path(path).open("rb") as source:
        initial = os.fstat(source.fileno())
        require(stat.S_ISREG(initial.st_mode), "archive must be a regular file")
        magic = source.read(2)
        source.seek(0)
        stream = HashingReader(source)
        compressed = magic == b"\x1f\x8b"
        decoded = gzip.GzipFile(fileobj=stream, mode="rb") if compressed else stream
        try:
            with tarfile.open(fileobj=decoded, mode="r|", ignore_zeros=True) as archive:
                for member in archive:
                    require(member.isdir() or member.isreg(), "links and special archive members are forbidden")
                    require(not member.issparse(), "sparse archive members are forbidden")
                    name = member_name(member.name, directory=member.isdir())
                    require(name not in members, "duplicate archive member: " + name)
                    parts = name.split("/")
                    for index in range(1, len(parts)):
                        ancestor = "/".join(parts[:index])
                        require(members.get(ancestor) != "file", "file/directory path collision: " + name)
                        ancestor_paths.add(ancestor)
                    if member.isreg():
                        require(name not in ancestor_paths, "file/directory path collision: " + name)
                    members[name] = "directory" if member.isdir() else "file"
                    if member.isdir():
                        require(member.size == 0, "directory member carries data")
                        directory_count += 1
                        continue
                    require(member.size >= 0, "negative archive member size")
                    if name in EXCLUDED:
                        require(member.size <= MAX_METADATA_BYTES, "custody JSON exceeds bounded metadata limit")
                    hasher = hashlib.sha256()
                    count = 0
                    collected = bytearray() if name in EXCLUDED else None
                    with archive.extractfile(member) as contents:
                        while True:
                            block = contents.read(CHUNK_BYTES)
                            if not block:
                                break
                            count += len(block)
                            hasher.update(block)
                            if collected is not None:
                                collected.extend(block)
                    require(count == member.size, "truncated archive member: " + name)
                    hashes[name], sizes[name] = hasher.hexdigest(), count
                    if collected is not None:
                        metadata[name] = bytes(collected)
            while decoded.read(CHUNK_BYTES):
                pass
            while stream.read(CHUNK_BYTES):
                pass
        finally:
            if compressed:
                decoded.close()
        require(file_identity(os.fstat(source.fileno())) == file_identity(initial), "archive changed while reading")
        require(stream.byte_count == initial.st_size, "archive byte count mismatch")
        actual_archive = stream.hasher.hexdigest()
        require(actual_archive == expected_archive, "archive SHA256 mismatch")

    require(hashes.get("manifest.json") == expected_manifest, "prepared manifest SHA256 mismatch or missing manifest.json")
    require("SEAL.json" in metadata, "missing SEAL.json")
    seal = parse_metadata(metadata["SEAL.json"], "SEAL.json")
    require(seal.get("version") == VERSION and seal.get("evidence_kind") == EVIDENCE_KIND
            and seal.get("classification") == "PENDING_DURABLE_FINALIZATION", "native evidence seal identity mismatch")
    sealed = seal.get("files")
    require(isinstance(sealed, dict), "SEAL.files must be a file/hash object")
    for name, value in sealed.items():
        require(member_name(name) == name and name not in EXCLUDED, "noncanonical or excluded SEAL.files path")
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SEAL.files SHA256")
    observed = {name: value for name, value in hashes.items() if name not in EXCLUDED}
    require(observed == sealed, "SEAL.files exact inventory/hash mismatch")

    final_present = "FINALIZED.json" in metadata
    abort_present = "FINALIZATION_ABORT.json" in metadata
    if final_present:
        completion = parse_metadata(metadata["FINALIZED.json"], "FINALIZED.json")
        require(completion.get("seal_sha256") == hashes["SEAL.json"], "FINALIZED seal hash binding mismatch")
    if abort_present:
        require(final_present, "FINALIZATION_ABORT requires FINALIZED.json for its hash binding")
        publication = parse_metadata(metadata["FINALIZATION_ABORT.json"], "FINALIZATION_ABORT.json")
        require(publication.get("seal_sha256") == hashes["SEAL.json"]
                and publication.get("finalized_sha256") == hashes["FINALIZED.json"],
                "FINALIZATION_ABORT witness hash binding mismatch")

    return dict(custody_valid=True, scientific_replay=False, scientific_ready=False,
                scientific_readiness=("NOT_ASSESSED_AUTHORITATIVE_NATIVE_REPLAY_REQUIRED" if final_present
                                      else "NOT_SCIENTIFIC_READY_MISSING_FINAL_WITNESS"),
                final_witness_status="PRESENT_HASH_BOUND" if final_present else "MISSING",
                finalization_abort_present=abort_present, failure_record_present="FAILED.json" in hashes,
                archive_sha256=actual_archive, prepared_manifest_sha256=hashes["manifest.json"],
                seal_sha256=hashes["SEAL.json"], finalized_sha256=hashes.get("FINALIZED.json"),
                finalization_abort_sha256=hashes.get("FINALIZATION_ABORT.json"),
                file_inventory_sha256=sha256(canonical(hashes)), sealed_inventory_sha256=sha256(canonical(observed)),
                file_count=len(hashes), sealed_file_count=len(observed), directory_count=directory_count,
                regular_file_bytes=sum(sizes.values()), archive_bytes=stream.byte_count,
                compression="gzip" if compressed else "none", extracted=False, tensors_deserialized=False)


def validate_archive(path, *, archive_sha256, manifest_sha256):
    """Validate byte custody, not witness timing, numerical outputs or scientific eligibility."""
    try:
        return _validate_archive(path, archive_sha256, manifest_sha256)
    except CustodyError:
        raise
    except (OSError, EOFError, tarfile.TarError, UnicodeError, ValueError, RecursionError, zlib.error) as error:
        raise CustodyError("unreadable or malformed custody archive: " + str(error)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="closed tar/tgz archive; never extracted")
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True, help="expected root manifest.json SHA256")
    args = parser.parse_args(argv)
    try:
        result = validate_archive(args.archive, archive_sha256=args.archive_sha256,
                                  manifest_sha256=args.manifest_sha256)
    except CustodyError as error:
        print(canonical(dict(custody_valid=False, scientific_replay=False, scientific_ready=False,
                             error=str(error))).decode(), end="", file=sys.stderr)
        return 2
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
