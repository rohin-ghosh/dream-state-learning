"""Durable local I/O for the accepted Stage2A CPU-copy checkpoint dictionary.

This is not C11, execution authorization, or external authentication. Hashes
detect inconsistent/corrupt bytes, not a maliciously replaced complete bundle.
The accepted StatefulTrainer still validates lineage, recipe, moments, counters
and RNG semantics before continuation. No models, tokenizers or devices are
created here; torch is lazy and deserialization is CPU/weights-only, without
fallbacks or additions to the safe-global registry.

Save requires an existing parent and a fresh leaf directory. Each file uses
exclusive creation; the blob and manifest are fsynced before a final COMMITTED
marker, then the directory is fsynced. Failures preserve every partial file and
directory: do not retry into them. Inspect/load require the complete marker and
verify its manifest digest and the blob digest/length before deserialization.
The loader uses a verified in-memory byte snapshot, not a reopened pathname.

The byte/depth/node limits are I/O bounds, not a hostile-tensor allocation
sandbox. Use locally controlled custody; weights-only is not authentication.
"""

from hashlib import sha256
import io
import json
import math
import os
import re
import stat
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_training as training


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(training.SCIENCE_GATES, False))
FORMAT = "stage2a-checkpoint-directory-v1"
BLOB_NAME = "checkpoint.pt"
MANIFEST_NAME = "manifest.json"
COMMIT_NAME = "COMMITTED"
DEFAULT_MAX_BLOB_BYTES = 1024 ** 3
MAX_MANIFEST_BYTES = 65536
MAX_TREE_DEPTH = 64
MAX_TREE_NODES = 1000000
_STATE_KEYS = {"format", "binding", "completed_updates", "cursor", "adapter", "optimizer",
               "rng", "receipts", "sha256"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _limit(value):
    _require(type(value) is int and value > 0, "positive_integer_blob_limit_required")
    return value


def _path(directory):
    path = os.fspath(directory)
    _require(type(path) is str and bool(path) and "\0" not in path
             and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path) is None,
             "local_directory_path_required")
    return os.path.abspath(path)


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _metadata(checkpoint):
    _require(type(checkpoint) is dict and set(checkpoint) == _STATE_KEYS
             and checkpoint["format"] == "stage2a-state-v1", "complete_stateful_checkpoint_required")
    training.validate_stage_cursor(checkpoint["completed_updates"], checkpoint["cursor"])
    _require(type(checkpoint["binding"]) is dict and type(checkpoint["adapter"]) is dict
             and type(checkpoint["optimizer"]) is dict
             and set(checkpoint["optimizer"]) == {"state", "param_groups"}
             and type(checkpoint["rng"]) is dict and set(checkpoint["rng"]) == {"cpu", "cuda"}
             and type(checkpoint["rng"]["cuda"]) is tuple
             and type(checkpoint["receipts"]) is list
             and len(checkpoint["receipts"]) == checkpoint["completed_updates"]
             and _sha(checkpoint["sha256"]), "invalid_checkpoint_envelope")
    return dict(state_format=checkpoint["format"], state_sha256=checkpoint["sha256"],
                completed_updates=checkpoint["completed_updates"], cursor=checkpoint["cursor"],
                binding_sha256=sha256(_json_bytes(checkpoint["binding"])).hexdigest())


def _torch():
    import torch
    return torch


def _validate_cpu_checkpoint(checkpoint):
    torch = _torch()
    ancestors = set()
    nodes = 0

    def visit(value, depth):
        nonlocal nodes
        nodes += 1
        _require(depth <= MAX_TREE_DEPTH and nodes <= MAX_TREE_NODES, "checkpoint_tree_limit_exceeded")
        kind = type(value)
        if value is None or kind in (str, int, bool):
            return
        if kind is float:
            _require(math.isfinite(value), "nonfinite_checkpoint_scalar")
            return
        if kind is torch.Tensor:
            _require(value.device.type == "cpu" and value.layout == torch.strided
                     and not value.requires_grad and not value.is_quantized
                     and not value.is_conj() and not value.is_neg(), "plain_detached_cpu_tensor_required")
            return
        _require(kind in (dict, list, tuple), "unsupported_checkpoint_object")
        identity = id(value)
        _require(identity not in ancestors, "cyclic_checkpoint_tree")
        ancestors.add(identity)
        try:
            if kind is dict:
                for key, item in value.items():
                    _require(type(key) in (str, int), "plain_checkpoint_key_required")
                    visit(item, depth + 1)
            else:
                for item in value:
                    visit(item, depth + 1)
        finally:
            ancestors.remove(identity)

    visit(checkpoint, 0)
    metadata = _metadata(checkpoint)
    expected = training._digest(training._tree_hash(
        {key: value for key, value in checkpoint.items() if key != "sha256"}))
    _require(expected == checkpoint["sha256"], "checkpoint_state_digest_mismatch")
    return metadata


def _directory_flags():
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


class _BoundedWriter:
    def __init__(self, stream, limit):
        self.stream, self.limit = stream, limit

    def write(self, value):
        _require(self.stream.tell() + len(value) <= self.limit, "checkpoint_blob_limit_exceeded")
        return self.stream.write(value)

    def flush(self):
        return self.stream.flush()

    def tell(self):
        return self.stream.tell()


def _write_exclusive(directory_fd, name, writer, limit):
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory_fd)
    with os.fdopen(descriptor, "wb") as stream:
        writer(_BoundedWriter(stream, limit))
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory_fd)


def _read_file(directory_fd, name, limit, *, snapshot=False):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit,
                 "regular_nonempty_bounded_file_required:" + name)
        digest, size = sha256(), 0
        saved = io.BytesIO() if snapshot else None
        while True:
            chunk = stream.read(min(1024 ** 2, limit - size + 1))
            if not chunk:
                break
            size += len(chunk)
            _require(size <= limit, "file_limit_exceeded:" + name)
            digest.update(chunk)
            if saved is not None:
                saved.write(chunk)
        after = os.fstat(stream.fileno())
        _require(size == before.st_size == after.st_size
                 and before.st_mtime_ns == after.st_mtime_ns
                 and before.st_ctime_ns == after.st_ctime_ns, "file_changed_during_read:" + name)
    if saved is not None:
        saved.seek(0)
    return size, digest.hexdigest(), saved


def _validate_manifest(manifest, limit):
    keys = {"format", "status", "science_gates", "blob", "state_format", "state_sha256",
            "completed_updates", "cursor", "binding_sha256"}
    _require(type(manifest) is dict and set(manifest) == keys and manifest["format"] == FORMAT
             and manifest["status"] == STATUS, "invalid_checkpoint_manifest")
    gates = manifest["science_gates"]
    _require(type(gates) is dict and set(gates) == set(SCIENCE_GATES)
             and all(value is False for value in gates.values()), "checkpoint_io_cannot_open_gates")
    blob = manifest["blob"]
    _require(type(blob) is dict and set(blob) == {"name", "size_bytes", "sha256"}
             and blob["name"] == BLOB_NAME and type(blob["size_bytes"]) is int
             and 0 < blob["size_bytes"] <= limit and _sha(blob["sha256"]), "invalid_blob_manifest")
    _require(manifest["state_format"] == "stage2a-state-v1"
             and _sha(manifest["state_sha256"]) and _sha(manifest["binding_sha256"]),
             "invalid_state_manifest")
    training.validate_stage_cursor(manifest["completed_updates"], manifest["cursor"])


def _parse_manifest(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "duplicate_manifest_key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("nonfinite_manifest_number:" + value)

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=unique, parse_constant=invalid_constant)
        _require(_json_bytes(value) == raw, "noncanonical_manifest_bytes")
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid_manifest_encoding_or_depth") from error
    return value


def _publish(directory, metadata, writer, *, max_blob_bytes):
    """Filesystem mechanism, separately testable with explicitly non-torch bytes."""
    limit = _limit(max_blob_bytes)
    path = _path(directory)
    parent, leaf = os.path.split(path)
    _require(bool(leaf), "fresh_leaf_directory_required")
    parent_fd = os.open(parent, _directory_flags())
    try:
        os.mkdir(leaf, mode=0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
        directory_fd = os.open(leaf, _directory_flags(), dir_fd=parent_fd)
        try:
            _write_exclusive(directory_fd, BLOB_NAME, writer, limit)
            size, blob_hash, _ = _read_file(directory_fd, BLOB_NAME, limit)
            manifest = dict(format=FORMAT, status=STATUS, science_gates=dict(SCIENCE_GATES),
                            blob=dict(name=BLOB_NAME, size_bytes=size, sha256=blob_hash), **metadata)
            _validate_manifest(manifest, limit)
            raw = _json_bytes(manifest)
            _write_exclusive(directory_fd, MANIFEST_NAME, lambda stream: stream.write(raw), MAX_MANIFEST_BYTES)
            marker = sha256(raw).hexdigest().encode("ascii") + b"\n"
            _write_exclusive(directory_fd, COMMIT_NAME, lambda stream: stream.write(marker), 65)
            return manifest
        finally:
            os.close(directory_fd)
    finally:
        os.close(parent_fd)


def save_checkpoint(directory, checkpoint, *, max_blob_bytes=DEFAULT_MAX_BLOB_BYTES):
    """Publish into a fresh local directory; never overwrite or remove evidence.

    The caller must exclusively own the supplied CPU-copy dictionary during
    this call. No arbitrary Python objects or Tensor subclasses are serialized.
    Success means file and directory fsync completed; exceptions retain partials.
    """
    _limit(max_blob_bytes)
    _path(directory)
    metadata = _validate_cpu_checkpoint(checkpoint)
    return _publish(directory, metadata, lambda stream: _torch().save(checkpoint, stream),
                    max_blob_bytes=max_blob_bytes)


def _verified_bundle(directory, limit, *, snapshot):
    directory_fd = os.open(_path(directory), _directory_flags())
    try:
        _, _, marker = _read_file(directory_fd, COMMIT_NAME, 65, snapshot=True)
        _, manifest_hash, encoded = _read_file(directory_fd, MANIFEST_NAME, MAX_MANIFEST_BYTES, snapshot=True)
        _require(marker.getvalue() == manifest_hash.encode("ascii") + b"\n", "manifest_commit_digest_mismatch")
        manifest = _parse_manifest(encoded.getvalue())
        _validate_manifest(manifest, limit)
        size, blob_hash, saved = _read_file(directory_fd, BLOB_NAME, limit, snapshot=snapshot)
        _require(size == manifest["blob"]["size_bytes"] and blob_hash == manifest["blob"]["sha256"],
                 "checkpoint_blob_integrity_mismatch")
        return manifest, saved
    finally:
        os.close(directory_fd)


def inspect_checkpoint(directory, *, max_blob_bytes=DEFAULT_MAX_BLOB_BYTES):
    """Verify committed manifest/blob integrity without importing torch."""
    manifest, _ = _verified_bundle(directory, _limit(max_blob_bytes), snapshot=False)
    return manifest


def load_checkpoint(directory, *, max_blob_bytes=DEFAULT_MAX_BLOB_BYTES):
    """Load verified bytes using weights_only=True and map_location='cpu'.

    No unsafe retry or global allowlisting is permitted. An ambient caller-added
    safe-global allowlist is rejected rather than silently weakening restriction.
    The result is state I/O evidence only; pass it to the accepted trainer for
    independent validation against the caller's actual model/plan/lineage.
    """
    manifest, saved = _verified_bundle(directory, _limit(max_blob_bytes), snapshot=True)
    torch = _torch()
    _require(not torch.serialization.get_safe_globals(), "ambient_safe_globals_not_allowed")
    checkpoint = torch.load(saved, weights_only=True, map_location="cpu")
    metadata = _validate_cpu_checkpoint(checkpoint)
    _require(all(manifest[key] == value for key, value in metadata.items()), "manifest_state_binding_mismatch")
    return checkpoint
