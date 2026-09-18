"""Fail-closed ancestry eligibility, not factual support or training approval.

Integration: validate_manifest("child.json", root=bundle_directory) returns an
immutable EligibilityReceipt or raises LineageGuardError. Optionally pin the
entry manifest with expected_sha256. The caller must consume the same bound
bytes (or revalidate at use); this read-only check does not lock future writes.

Version 1 JSON contract (all fields required, unknown fields rejected):
  manifest: schema_version=1, base_model=BASE_MODEL,
    kind="fresh_base"|"descendant", exposure_status="UNEXPOSED",
    parents=[{path, sha256}], sources=[source], artifacts=[artifact],
    trained_corpus=[corpus].
  source: path, sha256, exposure_status="UNEXPOSED", role in SOURCE_ROLES.
  artifact: path, sha256, exposure_status="UNEXPOSED", role in ARTIFACT_ROLES,
    source_sha256=[hashes of this manifest's source records].
  corpus: path, sha256, exposure_status="UNEXPOSED", source_sha256=[source hashes].

Paths are canonical relative POSIX paths within one explicitly supplied bundle
root, including parent references (NOT relative to each parent manifest).
Hashes are lowercase SHA256 of actual, nonempty regular files. No symlinks are
allowed, including in the root. Parent hashes bind their entire recursive
declarations; every source, artifact and corpus is independently hash-checked.

A fresh_base birth has zero parents, sources and trained_corpus, and at least
one base_model artifact with no source hashes. A descendant has parents,
sources and non-base artifacts; every artifact/corpus cites local sources.
trained_corpus lists the corpora used at this step, not a replacement for
inherited corpora; an empty list never erases parental exposure or provenance.
Inventory all influences, including notes, rankings and selection decisions,
not just adapters. Supported roles attest origins, not suitability as loss
targets (in particular, parent_turn does not license training on parent text).

Only explicit UNEXPOSED declarations pass. Known quarantined/development
markers and bootstrap_v1/v2/v3 or CompilerGym references anywhere in manifest
strings/paths are vetoes, never positive evidence from a filename. Omitted or
false declarations cannot be discovered by this guard. It does not authenticate
the declarant, identify renamed undeclared gym data, verify the official base
weights, establish factual entailment, or approve every sourced datum. Those
remain separate caller gates. There is deliberately no clean-manifest writer.

CLI: python -m organism_v6.lineage_guard --root BUNDLE child.json
Prints one JSON receipt; exits 0 only for eligibility, 1 for rejection.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
SOURCE_ROLES = ("experienced_event", "environment_outcome", "parent_turn", "person")
ARTIFACT_ROLES = (
    "base_model", "lora_adapter", "memory", "parent_notes", "ranking",
    "selection_decision",
)
LIMITATION = (
    "Ancestry eligibility only; not factual entailment, base-weight "
    "authentication, or automatic validity of all data. Requires complete, "
    "truthful declarations and consumption of the same hash-bound bytes."
)
MAX_DEPTH = 64
MAX_MANIFESTS = 512
MAX_RECORDS = 4096
MAX_MANIFEST_BYTES = 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FORBIDDEN = re.compile(
    r"DEV_UNVERIFIED_PROVENANCE|QUARANTINE_TASK_EXPOSED|"
    r"bootstrap[\s_-]*v[123]|compiler[\s_-]*gym|R2_B_seed3", re.IGNORECASE
)
_MANIFEST_FIELDS = {
    "schema_version", "base_model", "kind", "exposure_status", "parents",
    "sources", "artifacts", "trained_corpus",
}
_BINDING_FIELDS = {"path", "sha256"}


class LineageGuardError(ValueError):
    """The supplied bundle cannot establish ancestry eligibility."""


@dataclass(frozen=True)
class FileBinding:
    path: str
    sha256: str


@dataclass(frozen=True)
class EligibilityReceipt:
    eligible: bool
    exposure_status: str
    root: str
    manifest: FileBinding
    manifests: tuple[FileBinding, ...]
    files: tuple[FileBinding, ...]
    scope: str = LIMITATION


def _require(condition, message):
    if not condition:
        raise LineageGuardError(message)


def _hash(value):
    _require(isinstance(value, str) and _SHA256.fullmatch(value), "invalid SHA256")
    return value


def _fields(value, expected):
    _require(isinstance(value, dict), "expected an object")
    _require(set(value) == expected, "missing or unknown fields")


def _unexposed(value):
    _require(value == "UNEXPOSED", "missing, unknown or tainted exposure status")


def _scan(value):
    if isinstance(value, str):
        _require(not _FORBIDDEN.search(value), "forbidden ancestry marker")
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan(key)
            _scan(item)
    elif isinstance(value, list):
        for item in value:
            _scan(item)


def _relative_path(value):
    _require(isinstance(value, str) and value.strip(), "missing file path")
    _require("\\" not in value and "\x00" not in value, "invalid file path")
    parts = value.split("/")
    _require(all(part not in ("", ".", "..") for part in parts),
             "absolute, noncanonical or traversing path")
    _scan(value)
    return parts


@contextmanager
def _directory(parts, start):
    descriptor = os.dup(start)
    try:
        for part in parts:
            next_descriptor = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        yield descriptor
    finally:
        os.close(descriptor)


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise LineageGuardError(f"invalid JSON constant: {value}")


class _Validator:
    def __init__(self, root_descriptor):
        self.root_descriptor = root_descriptor
        self.manifests = {}
        self.files = {}
        self.observed = {}
        self.active_paths = set()
        self.active_files = set()
        self.record_count = 0

    def read(self, path, expected=None, manifest=False):
        parts = _relative_path(path)
        if expected is not None:
            _hash(expected)
        with _directory(parts[:-1], self.root_descriptor) as directory:
            descriptor = os.open(
                parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode), f"not a regular file: {path}")
            _require(before.st_size > 0, f"empty file: {path}")
            if manifest:
                _require(before.st_size <= MAX_MANIFEST_BYTES, "manifest too large")
            digest = hashlib.sha256()
            chunks = []
            size = 0
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
                if manifest:
                    _require(size <= MAX_MANIFEST_BYTES, "manifest too large")
                    chunks.append(chunk)
            after = os.fstat(stream.fileno())
        _require(
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and size == before.st_size, f"file changed during validation: {path}",
        )
        actual = digest.hexdigest()
        _require(expected is None or actual == expected, f"SHA256 mismatch: {path}")
        _require(self.observed.get(path, actual) == actual,
                 f"file changed between references: {path}")
        self.observed[path] = actual
        return actual, b"".join(chunks), (before.st_dev, before.st_ino)

    def record(self, value, category, source_hashes=()):
        self.record_count += 1
        _require(self.record_count <= MAX_RECORDS, "too many file records")
        fields = _BINDING_FIELDS | {"exposure_status"}
        if category in ("source", "artifact"):
            fields |= {"role"}
        if category in ("artifact", "corpus"):
            fields |= {"source_sha256"}
        _fields(value, fields)
        _unexposed(value["exposure_status"])
        if category == "source":
            _require(value["role"] in SOURCE_ROLES, "unsupported source role")
        if category == "artifact":
            _require(value["role"] in ARTIFACT_ROLES, "unsupported artifact role")
        if category in ("artifact", "corpus"):
            references = value["source_sha256"]
            _require(isinstance(references, list), "source_sha256 must be a list")
            for reference in references:
                _hash(reference)
                _require(reference in source_hashes, "unbound source hash")
            _require(len(references) == len(set(references)), "duplicate source hash")
            if category == "artifact" and value["role"] == "base_model":
                _require(not references, "base artifacts cannot contain learned sources")
            else:
                _require(bool(references), "artifact/corpus has no supported sources")
        actual, _, _ = self.read(value["path"], _hash(value["sha256"]))
        self.files[value["path"]] = actual
        return actual

    def visit(self, path, expected=None):
        _require(path not in self.active_paths, "cyclic lineage")
        _require(len(self.active_paths) < MAX_DEPTH, "lineage depth exceeded")
        actual, content, identity = self.read(path, expected, manifest=True)
        _require(identity not in self.active_files, "cyclic lineage file identity")
        if path in self.manifests:
            return actual
        _require(len(self.manifests) + len(self.active_paths) < MAX_MANIFESTS,
                 "too many manifests")
        value = json.loads(content, object_pairs_hook=_json_object,
                           parse_constant=_invalid_constant)
        _scan(value)
        _fields(value, _MANIFEST_FIELDS)
        _require(type(value["schema_version"]) is int and value["schema_version"] == 1,
                 "unsupported schema_version")
        _require(value["base_model"] == BASE_MODEL, "base model mismatch")
        _unexposed(value["exposure_status"])
        _require(value["kind"] in ("fresh_base", "descendant"), "unknown birth kind")
        for name in ("parents", "sources", "artifacts", "trained_corpus"):
            _require(isinstance(value[name], list), f"{name} must be a list")
        _require(bool(value["artifacts"]), "missing artifacts")
        if value["kind"] == "fresh_base":
            _require(not value["parents"] and not value["sources"]
                     and not value["trained_corpus"],
                     "fresh_base must have zero ancestors, sources and trained corpus")
        else:
            _require(bool(value["parents"]) and bool(value["sources"]),
                     "descendant requires parents and supported sources")
        self.active_paths.add(path)
        self.active_files.add(identity)
        try:
            parent_paths = set()
            for parent in value["parents"]:
                _fields(parent, _BINDING_FIELDS)
                _relative_path(parent["path"])
                _hash(parent["sha256"])
                _require(parent["path"] not in parent_paths, "duplicate parent")
                parent_paths.add(parent["path"])
                self.visit(parent["path"], parent["sha256"])
            source_hashes = {
                self.record(source, "source") for source in value["sources"]
            }
            for artifact in value["artifacts"]:
                self.record(artifact, "artifact", source_hashes)
                _require((artifact["role"] == "base_model")
                         == (value["kind"] == "fresh_base"),
                         "birth kind does not match artifact role")
            for corpus in value["trained_corpus"]:
                self.record(corpus, "corpus", source_hashes)
            self.manifests[path] = actual
        finally:
            self.active_paths.remove(path)
            self.active_files.remove(identity)
        return actual


def validate_manifest(manifest_path, *, root, expected_sha256=None):
    """Return an ancestry-only receipt; fail closed with LineageGuardError.

    root is the explicit trust boundary. manifest_path is relative to root.
    No files are written. POSIX no-follow, directory-relative opens are required.
    """
    try:
        _require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
                 and os.open in os.supports_dir_fd, "safe file opens unavailable")
        path = os.fspath(manifest_path)
        _relative_path(path)
        root_path = Path(root)
        _require(".." not in root_path.parts, "traversing root path")
        if not root_path.is_absolute():
            root_path = Path.cwd() / root_path
        _scan(str(root_path))
        anchor = os.open(root_path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            with _directory(root_path.parts[1:], anchor) as root_descriptor:
                validator = _Validator(root_descriptor)
                digest = validator.visit(path, expected_sha256)
        finally:
            os.close(anchor)
        return EligibilityReceipt(
            eligible=True, exposure_status="UNEXPOSED", root=str(root_path),
            manifest=FileBinding(path, digest),
            manifests=tuple(FileBinding(name, value)
                            for name, value in sorted(validator.manifests.items())),
            files=tuple(FileBinding(name, value)
                        for name, value in sorted(validator.files.items())),
        )
    except LineageGuardError:
        raise
    except (OSError, ValueError, TypeError, RecursionError) as error:
        raise LineageGuardError(f"cannot validate lineage: {error}") from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest path relative to --root")
    parser.add_argument("--root", required=True, help="explicit bundle directory")
    parser.add_argument("--expected-sha256", help="optional entry manifest SHA256 pin")
    arguments = parser.parse_args(argv)
    try:
        receipt = validate_manifest(arguments.manifest, root=arguments.root,
                                    expected_sha256=arguments.expected_sha256)
    except LineageGuardError as error:
        print(json.dumps({"eligible": False, "error": str(error), "scope": LIMITATION}))
        return 1
    print(json.dumps(asdict(receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
