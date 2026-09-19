"""Bounded, process-local journal proofs; metadata is checked afresh on every use."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time


BASE_SHA = "a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992"
MAX_RECORD_BYTES = 33554432
TIMESTAMP_FENCE_NS = 2_000_000_000
_CACHES = {}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class SourceEpochPending(RuntimeError):
    def __init__(self, progress):
        self.progress = progress
        super().__init__("SOURCE_EPOCH_VALIDATION_PENDING_NO_ADMISSION")


@dataclass(frozen=True)
class Budget:
    records: int = 256
    bytes: int = 64 * 1024 * 1024
    seconds: float = 2.0

    def __post_init__(self):
        require(self.records > 0 and self.bytes > 0 and self.seconds > 0, "positive_validation_budget")


def fingerprint(metadata):
    require(stat.S_ISREG(metadata.st_mode), "bounded_regular_journal_record")
    require(metadata.st_size <= MAX_RECORD_BYTES, "bounded_regular_journal_record")
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid,
        metadata.st_gid, metadata.st_nlink, metadata.st_size, metadata.st_mtime_ns,
        metadata.st_ctime_ns)


class EpochCache:
    def __init__(self, policy, source):
        self.life = Path(policy["source_roots"][source])
        self.records = self.life / "stream/records"
        self.journal = policy["supported_journals"][source]
        self.anchors = [dict(policy[field][source]) for field in ("initial_loaded", "current_loaded")]
        self.source = source
        self.verified = {}
        self.directories = None
        self.failure = None
        self.total_decoded = 0
        self.total_bytes = 0
        self.total_fence_bytes = 0
        self.total_fence_reads = 0
        self.last = {}

    def snapshot(self):
        require(self.life.resolve() == self.life, "source_path_changed_review_rebind_required")
        directories = []
        for path in (self.life, self.life / "stream", self.records):
            metadata = path.lstat()
            require(stat.S_ISDIR(metadata.st_mode), "source_directory_symlink_or_type_changed")
            directories.append((metadata.st_dev, metadata.st_ino))
        if self.directories is None:
            self.directories = directories
        require(self.directories == directories, "source_directory_replaced_review_rebind_required")
        anchors = {row["index"] for row in self.anchors}
        current = self.anchors[-1]["index"]
        result = {}
        with os.scandir(self.records) as entries:
            for entry in entries:
                stem = entry.name.removesuffix(".json")
                if not entry.name.endswith(".json") or not stem.isdigit():
                    continue
                require(re.fullmatch(r"[0-9]{20}", stem) is not None, "noncanonical_source_record_name")
                index = int(stem)
                if index in anchors or index > current:
                    result[index] = fingerprint(entry.stat(follow_symlinks=False))
        require(anchors <= result.keys(), "source_anchor_deleted")
        suffix = sorted(index for index in result if index > current)
        require(all(index == current + offset for offset, index in enumerate(suffix, 1)), "source_frontier_chain_changed")
        for index, cached in self.verified.items():
            require(result.get(index) == cached["fingerprint"], "verified_source_record_changed_review_rebind_required")
        return result

    def raw_record(self, index, expected):
        path = self.records / f"{index:020d}.json"
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        with os.fdopen(descriptor, "rb") as stream:
            require(fingerprint(os.fstat(stream.fileno())) == expected, "source_record_changed_during_read")
            raw = stream.read(MAX_RECORD_BYTES + 1)
            require(len(raw) == expected[6], "source_record_changed_during_read")
            require(fingerprint(os.fstat(stream.fileno())) == expected
                and fingerprint(path.lstat()) == expected, "source_record_changed_during_read")
        return raw

    def decode(self, index, expected):
        raw = self.raw_record(index, expected)
        record = json.loads(raw)
        payload = {key: value for key, value in record.items() if key != "sha256"}
        checksum = hashlib.sha256(json.dumps(payload, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        require(record["journal_id"] == self.journal and type(record["index"]) is int
            and record["index"] == index and record["sha256"] == checksum,
            "source_journal_identity_changed")
        require(fingerprint((self.records / f"{index:020d}.json").lstat()) == expected,
            "source_record_changed_during_read")
        self.total_decoded += 1
        self.total_bytes += len(raw)
        return dict(index=index, sha256=checksum, kind=record["kind"],
            previous_sha256=record.get("previous_sha256"),
            base_sha256=record["document"].get("base_sha256") if record["kind"] == "LOADED" else None,
            fingerprint=expected, raw_sha256=hashlib.sha256(raw).hexdigest(),
            needs_content_fence=time.time_ns() - expected[8] <= TIMESTAMP_FENCE_NS)

    def validate(self, cursor=None, budget=Budget()):
        require(self.failure is None, self.failure or "source_cache_failed")
        started = time.monotonic()
        before_count, before_bytes = self.total_decoded, self.total_bytes
        before_fence_count, before_fence_bytes = self.total_fence_reads, self.total_fence_bytes
        try:
            snapshot = self.snapshot()
            current = self.anchors[-1]
            if cursor is not None:
                known = self.verified.get(cursor["index"])
                require(cursor == current or (known is not None and cursor["sha256"] == known["sha256"]),
                    "unverified_cursor_cannot_skip_source_prefix")
            fenced = set()
            volatile = [index for index, record in sorted(self.verified.items()) if record["needs_content_fence"]]
            pending = [index for index in sorted(snapshot) if index not in self.verified]
            for index in volatile + pending:
                consumed = self.total_decoded - before_count + self.total_fence_reads - before_fence_count
                amount = self.total_bytes - before_bytes + self.total_fence_bytes - before_fence_bytes
                if consumed and (consumed >= budget.records or amount + snapshot[index][6] > budget.bytes
                        or time.monotonic() - started >= budget.seconds):
                    break
                if index in self.verified:
                    raw = self.raw_record(index, snapshot[index])
                    require(hashlib.sha256(raw).hexdigest() == self.verified[index]["raw_sha256"],
                        "verified_source_record_changed_within_timestamp_granularity")
                    self.total_fence_reads += 1
                    self.total_fence_bytes += len(raw)
                    self.verified[index]["needs_content_fence"] = time.time_ns() - snapshot[index][8] <= TIMESTAMP_FENCE_NS
                    fenced.add(index)
                    continue
                record = self.decode(index, snapshot[index])
                for anchor in self.anchors:
                    if index == anchor["index"]:
                        require(record["sha256"] == anchor["sha256"] and record["kind"] == "LOADED"
                            and record["base_sha256"] == BASE_SHA, "source_loaded_changed")
                if index > current["index"]:
                    previous = self.verified.get(index - 1)
                    require(previous is not None and record["previous_sha256"] == previous["sha256"],
                        "source_frontier_chain_changed")
                    require(record["kind"] != "LOADED", "new_source_epoch_requires_explicit_review_rebind")
                self.verified[index] = record
            fresh = self.snapshot()
            remaining = len(fresh.keys() - self.verified.keys()) + len(set(volatile) - fenced)
            self.last = dict(source=self.source, decoded_records=self.total_decoded - before_count,
                decoded_bytes=self.total_bytes - before_bytes, total_decoded_records=self.total_decoded,
                total_decoded_bytes=self.total_bytes, metadata_records=len(fresh),
                timestamp_fence_reads=self.total_fence_reads - before_fence_count,
                timestamp_fence_bytes=self.total_fence_bytes - before_fence_bytes,
                remaining_records=remaining, elapsed_seconds=time.monotonic() - started,
                cache_scope="PROCESS_MEMORY_ONLY_NO_TRUSTED_DISK_CURSOR", ready=not remaining)
            if remaining:
                raise SourceEpochPending(dict(self.last))
            latest = self.verified[max(fresh)]
            return dict(index=latest["index"], sha256=latest["sha256"])
        except SourceEpochPending:
            raise
        except (ValueError, OSError, KeyError, TypeError) as error:
            self.failure = "source_cache_invalid_review_required:" + str(error)
            raise


def cache_for(policy, source):
    key = (os.getpid(), source, hashlib.sha256(json.dumps(policy, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest())
    if key not in _CACHES:
        _CACHES[key] = EpochCache(policy, source)
    return _CACHES[key]


def verify(policy, source, cursor=None, budget=Budget()):
    return cache_for(policy, source).validate(cursor, budget)
