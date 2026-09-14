"""Bounded local custody for the frozen screen event protocol, not qualification.

Non-material storage adapter: no material, model, tokenizer or torch is loaded.
Use ScreenCustodySink as a context manager on a fresh directory in a trusted
existing parent. Supply torch explicitly to export plain strided tensors as
detached CPU tensor-only sidecars. Their file hashes bind shape/dtype metadata;
device, strides, storage aliases and autograd identity are not preserved.

Builtin encoding follows wire._freeze/training._plain. Only the listed record
classes are projected. Exceptions are DIAGNOSTICS (qualified class, typed args,
__dict__ and declared Python slots), not original objects, traceback, implicit
builtin exception fields or interpreter-state custody.
Unsupported fields/cycles are marked incomplete; supported siblings are still
captured before raising. I/O failures retain partial files and poison the sink.
A marker-write/fsync failure can leave uncertain marker bytes: a read-only
check cannot prove a past fsync succeeded. Never retry a failed sink. Retain
the runtime's in-memory ScreenRun, especially when export fails.

The terminal ledger references each previously published CallCustody event by
index, not later reads of its mutable native objects. COMPLETE means ordered, verified
export, including a valid aborted screen; it never means scientific success.
Verification is bounded, read-only and never unpickles tensors. Hashes detect
corruption, not malicious replacement of a whole bundle. Caller owns exclusive
access, provenance, permissions, deadlines and any device-to-CPU transfer.
"""

from dataclasses import dataclass, fields
import json
import os

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_probe as probe
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training


FORMAT = "stage2a-screen-custody-v1"
MAX_EVENTS = 562
MAX_DEPTH = 48
MAX_NODES = 250000
MAX_FILES = 4096
_RECORDS = (runtime.CallCustody, runtime.Reservation, runtime.Failure, runtime.ScreenRun,
            screen.ScreenEntry, primitives.LogicalSlot, held.Message, rollout.DecodeRequest,
            rollout.Generation, rollout.CallRecord, rollout.ChainRun, probe.ProbeRun,
            wire.Snapshot, wire.RawAttempt, wire.Attempt, wire.Action)


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _qualified(kind):
    return kind.__module__ + "." + kind.__qualname__


def _record(value, kind):
    _require(type(value) is list and len(value) == 3
             and value[:2] == ["record", _qualified(kind)], "incorrect_record_binding")
    pairs = value[2]
    _require(type(pairs) is list and [pair[0] for pair in pairs]
             == [field.name for field in fields(kind)], "incorrect_record_fields")
    return dict(pairs)


def _scalar(value, kind):
    _require(type(value) is list and len(value) == 2 and value[0] == kind.__name__
             and type(value[1]) is kind, "incorrect_scalar_binding")
    return value[1]


def _tuple(value):
    _require(type(value) is list and len(value) == 2 and value[0] == "tuple"
             and type(value[1]) is list, "incorrect_tuple_binding")
    return value[1]


def _none(value):
    return value == ["NoneType", None]


@dataclass(frozen=True)
class ReceiptLimits:
    event_bytes: int = 8 * 1024 ** 2
    tensor_bytes: int = 8 * 1024 ** 2
    total_bytes: int = 256 * 1024 ** 2

    def __post_init__(self):
        _require(all(type(value) is int and value > 0 for value in
                     (self.event_bytes, self.tensor_bytes, self.total_bytes)), "positive_limits_required")


@dataclass(frozen=True)
class ReceiptVerification:
    """Encoded events, not reconstructed native objects; call refs index events."""

    state_id: str
    stage: str
    terminal_reason: str
    events: tuple
    export_status: str = "complete"
    scientific_success: bool = False
    exception_custody: str = "diagnostics_only"


class CustodyExportError(ValueError):
    """The published event is explicitly incomplete; native custody stays in RAM."""


class _Protocol:
    def __init__(self):
        self.state_id = self.stage = self.terminal_reason = None
        self.signatures = []
        self.pending = None
        self.captured = {}
        self.last_slot = -1
        self.physical_count = 0
        self.native_next = None
        self.event_count = 0

    def accept(self, event, payload):
        _require(self.terminal_reason is None, "event_after_screen_finished")
        self.event_count += 1
        if event == "SCREEN_RESERVED":
            _require(self.state_id is None, "duplicate_screen_reservation")
            data = _record(payload, runtime.ScreenRun)
            self.state_id = _scalar(data["state_id"], str)
            self.stage = _scalar(data["stage"], str)
            _require(bool(self.state_id) and _scalar(data["terminal_reason"], str) == "pending",
                     "invalid_initial_screen")
            rows = _tuple(data["reservations"])
            _require(len(rows) == 280, "exact_280_reservations_required")
            for row in rows:
                entry = _record(row, runtime.Reservation)
                seed = _scalar(entry["seed"], int)
                _require(0 <= seed < 2 ** 64 and _none(entry["custody"]), "invalid_reservation")
                self.signatures.append((entry["entry"], entry["seed"]))
            self.slots = [_record(entry, screen.ScreenEntry)["slot"] for entry, _ in self.signatures]
            _require(len({checkpoint._json_bytes(slot) for slot in self.slots}) == 280,
                     "duplicate_logical_slot")
            return
        _require(self.state_id is not None, "screen_reservation_required")
        if event in ("CALL_RESERVED", "CALL_CAPTURED"):
            data = _record(payload, runtime.CallCustody)
            _require(_scalar(data["state_id"], str) == self.state_id, "state_binding_mismatch")
            _require(data["slot"] in self.slots, "unknown_slot")
            index = self.slots.index(data["slot"])
            request = _record(data["request"], rollout.DecodeRequest)
            _require(request["seed"] == self.signatures[index][1], "seed_binding_mismatch")
            if event == "CALL_RESERVED":
                _require(self.pending is None and index > self.last_slot
                         and _none(data["physical_call"]) and _none(data["actor_call_index"]),
                         "duplicate_or_unordered_call_reservation")
                self.pending = (index, data["request"])
                self.last_slot = index
            else:
                _require(self.pending == (index, data["request"]), "capture_without_matching_reservation")
                if not _none(data["physical_call"]):
                    _require(_scalar(data["physical_call"], int) == self.physical_count,
                             "physical_call_binding_mismatch")
                    native = _scalar(data["actor_call_index"], int)
                    _require(native >= 0 and (self.native_next is None or native == self.native_next),
                             "actor_call_index_binding_mismatch")
                    self.physical_count += 1
                    self.native_next = native + 1
                else:
                    _require(_none(data["actor_call_index"]), "uncalled_native_index")
                self.captured[index] = ["call_capture_ref", self.event_count - 1]
                self.pending = None
            return
        _require(event == "SCREEN_FINISHED" and self.pending is None, "unexpected_event_order")
        data = _record(payload, runtime.ScreenRun)
        _require(_scalar(data["state_id"], str) == self.state_id
                 and _scalar(data["stage"], str) == self.stage, "terminal_state_binding_mismatch")
        rows = [_record(row, runtime.Reservation) for row in _tuple(data["reservations"])]
        _require([(row["entry"], row["seed"]) for row in rows] == self.signatures,
                 "terminal_reservation_drift")
        for index, row in enumerate(rows):
            _require(row["custody"] == self.captured.get(index, ["NoneType", None]),
                     "terminal_call_capture_drift")
        reason = _scalar(data["terminal_reason"], str)
        failures = _tuple(data["failures"])
        _require((reason == "aborted" and bool(failures))
                 or (reason == "completed_unscored" and not failures), "invalid_terminal_outcome")
        self.terminal_reason = reason


class _Encoder:
    def __init__(self, sink):
        self.sink = sink
        self.nodes = self.tensor_count = 0
        self.scalar_bytes = 0
        self.issues = []

    def unsupported(self, value, path, reason):
        issue = dict(path=path, kind=_qualified(type(value)), reason=reason)
        if len(self.issues) < 128:
            self.issues.append(issue)
        return ["unsupported", issue]

    def encode(self, value, path="$", ancestors=()):
        self.nodes += 1
        if self.nodes > MAX_NODES or len(ancestors) > MAX_DEPTH:
            return self.unsupported(value, path, "capture_bound_exceeded")
        kind = type(value)
        if kind in (str, bytes, int, bool, type(None), float, bytearray):
            if kind in (str, bytes, bytearray) and len(value) > self.sink.limits.event_bytes:
                return self.unsupported(value, path, "scalar_bound_exceeded")
            encoded = training._plain(wire._freeze(value))
            self.scalar_bytes += len(checkpoint._json_bytes(encoded))
            if self.scalar_bytes > self.sink.limits.event_bytes:
                return self.unsupported(value, path, "scalar_bound_exceeded")
            return encoded
        if id(value) in ancestors:
            return self.unsupported(value, path, "cyclic_field")
        ancestry = ancestors + (id(value),)
        if kind is runtime.CallCustody:
            cached = self.sink._captures.get(id(value))
            if cached is not None and cached[0] is value:
                return ["call_capture_ref", cached[1]]
        if kind in _RECORDS:
            return ["record", _qualified(kind),
                    [[field.name, self.encode(getattr(value, field.name), path + "." + field.name, ancestry)]
                     for field in fields(kind)]]
        if kind in (dict, list, tuple):
            if len(value) > MAX_NODES - self.nodes:
                return self.unsupported(value, path, "container_bound_exceeded")
            if kind is dict:
                return ["dict", [[self.encode(key, path + f".key[{index}]", ancestry),
                                   self.encode(item, path + f".value[{index}]", ancestry)]
                                  for index, (key, item) in enumerate(value.items())]]
            return [kind.__name__, [self.encode(item, path + f"[{index}]", ancestry)
                                    for index, item in enumerate(value)]]
        if isinstance(value, BaseException):
            slots = []
            for owner in kind.__mro__:
                names = vars(owner).get("__slots__", ())
                if type(names) is str:
                    names = (names,)
                if type(names) not in (tuple, list):
                    self.unsupported(value, path + ".slots", "unsupported_slot_declaration")
                    continue
                for name in names:
                    if name in ("__dict__", "__weakref__"):
                        continue
                    attribute = ("_" + owner.__name__.lstrip("_") + name
                                 if name.startswith("__") and not name.endswith("__") else name)
                    try:
                        item = vars(owner)[attribute].__get__(value, kind)
                    except AttributeError:
                        continue
                    slots.append((_qualified(owner), name, item))
            return ["exception_diagnostic", _qualified(kind),
                    self.encode(value.args, path + ".args", ancestry),
                    self.encode(vars(value), path + ".attributes", ancestry),
                    self.encode(tuple(slots), path + ".slots", ancestry)]
        torch = self.sink.torch
        if torch is not None and kind is torch.Tensor:
            if self.sink.tensor_errors:
                return self.unsupported(value, path, "prior_tensor_export_failed")
            try:
                _require(value.layout == torch.strided and not value.is_quantized
                         and not value.is_conj() and not value.is_neg(), "unsupported_tensor_layout")
                _require(value.numel() * value.element_size() <= self.sink.limits.tensor_bytes,
                         "tensor_content_limit_exceeded")
                tensor = value.detach().cpu().contiguous().clone()
                name = f"event-{self.sink.event_count:04d}-tensor-{self.tensor_count:04d}.pt"
                self.tensor_count += 1
                self.sink._write(name, lambda stream: torch.save(tensor, stream),
                                 self.sink.limits.tensor_bytes)
                size, digest, _ = checkpoint._read_file(self.sink._fd, name, self.sink.limits.tensor_bytes)
                return ["tensor", dict(name=name, size_bytes=size, sha256=digest,
                                       shape=list(tensor.shape), dtype=str(tensor.dtype))]
            except BaseException as error:
                self.sink.tensor_errors.append(error)
                return self.unsupported(value, path, "tensor_export_failed:" + _qualified(type(error)))
        return self.unsupported(value, path, "unsupported_field")


def _tensor_refs(value):
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        _require(nodes <= MAX_NODES * 8 and depth <= MAX_DEPTH * 4, "encoded_tree_bound_exceeded")
        if type(item) is list:
            if len(item) == 2 and item[0] == "tensor":
                yield item[1]
            else:
                pending.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            pending.extend((child, depth + 1) for child in item.values())


def _read_json(descriptor, name, limit):
    size, digest, snapshot = checkpoint._read_file(descriptor, name, limit, snapshot=True)
    raw = snapshot.getvalue()
    value = json.loads(raw.decode("ascii"))
    _require(checkpoint._json_bytes(value) == raw, "noncanonical_receipt_json")
    return value, size, digest


def _verify_events(descriptor, count, last_sha256, limits, *, marker_present, initial_bytes=0):
    _require(type(count) is int and 2 <= count <= MAX_EVENTS, "invalid_event_count")
    protocol, events, previous = _Protocol(), [], None
    expected_files, tensor_metadata = set(), {}
    total = initial_bytes
    for index in range(count):
        name = f"event-{index:04d}.json"
        document, size, digest = _read_json(descriptor, name, limits.event_bytes)
        total += size
        expected_files.add(name)
        _require(set(document) == {"format", "index", "event", "previous_sha256", "export_status",
                                   "issues", "payload"}
                 and document["format"] == FORMAT and type(document["index"]) is int
                 and document["index"] == index and document["previous_sha256"] == previous,
                 "event_order_or_hash_mismatch")
        _require(document["export_status"] == "complete" and document["issues"] == [],
                 "incomplete_event")
        protocol.accept(document["event"], document["payload"])
        for tensor in _tensor_refs(document["payload"]):
            _require(type(tensor) is dict and set(tensor) == {"name", "size_bytes", "sha256", "shape", "dtype"},
                     "invalid_tensor_reference")
            tensor_name = tensor["name"]
            _require(type(tensor_name) is str and len(tensor_name) == 25
                     and tensor_name.startswith("event-") and tensor_name[10:18] == "-tensor-"
                     and tensor_name.endswith(".pt") and tensor_name[6:10].isdigit()
                     and tensor_name[18:22].isdigit() and int(tensor_name[6:10]) <= index,
                     "invalid_tensor_filename")
            _require(type(tensor["size_bytes"]) is int and 0 < tensor["size_bytes"] <= limits.tensor_bytes
                     and type(tensor["shape"]) is list
                     and all(type(dimension) is int and dimension >= 0 for dimension in tensor["shape"])
                     and type(tensor["dtype"]) is str, "invalid_tensor_metadata")
            if tensor_name in tensor_metadata:
                _require(tensor_metadata[tensor_name] == tensor, "tensor_reference_drift")
            else:
                tensor_size, tensor_hash, _ = checkpoint._read_file(descriptor, tensor_name, limits.tensor_bytes)
                _require((tensor_size, tensor_hash) == (tensor["size_bytes"], tensor["sha256"]),
                         "tensor_integrity_mismatch")
                tensor_metadata[tensor_name] = tensor
                expected_files.add(tensor_name)
                total += tensor_size
        _require(total <= limits.total_bytes and len(expected_files) <= MAX_FILES, "receipt_limit_exceeded")
        events.append(document)
        previous = digest
    _require(previous == last_sha256 and protocol.terminal_reason is not None, "unfinished_or_corrupt_receipt")
    if marker_present:
        expected_files.add("COMPLETE")
    with os.scandir(descriptor) as entries:
        observed = set()
        for entry in entries:
            observed.add(entry.name)
            _require(len(observed) <= MAX_FILES, "receipt_file_limit_exceeded")
    _require(observed == expected_files, "unexpected_or_missing_receipt_files")
    return ReceiptVerification(protocol.state_id, protocol.stage, protocol.terminal_reason, tuple(events))


def verify_receipt(directory, *, limits=ReceiptLimits()):
    """Verify complete local byte custody without torch imports or deserialization."""
    descriptor = os.open(directory, checkpoint._directory_flags())
    try:
        marker, marker_size, _ = _read_json(descriptor, "COMPLETE", min(65536, limits.total_bytes))
        _require(type(marker) is dict and set(marker) == {"format", "event_count", "last_sha256",
                                                        "state_id", "stage", "terminal_reason",
                                                        "scientific_success", "exception_custody"}
                 and marker["format"] == FORMAT and marker["scientific_success"] is False
                 and marker["exception_custody"] == "diagnostics_only", "invalid_completion_marker")
        result = _verify_events(descriptor, marker["event_count"], marker["last_sha256"], limits,
                                marker_present=True, initial_bytes=marker_size)
        _require((result.state_id, result.stage, result.terminal_reason)
                 == (marker["state_id"], marker["stage"], marker["terminal_reason"]), "marker_binding_mismatch")
        return result
    finally:
        os.close(descriptor)


class ScreenCustodySink:
    """Single-use sink; pass this object directly as runtime custody_sink."""

    def __init__(self, directory, *, torch=None, limits=ReceiptLimits()):
        _require(type(limits) is ReceiptLimits, "receipt_limits_required")
        self.torch, self.limits = torch, limits
        self.status, self.failure = "open", None
        self.tensor_errors = []
        self.event_count, self._bytes, self._file_count = 0, 0, 0
        self._previous, self._fd = None, None
        self._protocol, self._captures = _Protocol(), {}
        parent, leaf = os.path.split(os.path.abspath(os.fspath(directory)))
        parent_fd = os.open(parent, checkpoint._directory_flags())
        try:
            os.mkdir(leaf, 0o700, dir_fd=parent_fd)
            os.fsync(parent_fd)
            self._fd = os.open(leaf, checkpoint._directory_flags(), dir_fd=parent_fd)
        finally:
            os.close(parent_fd)

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self.status == "open":
            self.status = "incomplete"

    def _write(self, name, writer, limit):
        remaining = min(limit, self.limits.total_bytes - self._bytes)
        _require(remaining > 0 and self._file_count < MAX_FILES, "receipt_total_or_file_limit_exceeded")
        self._file_count += 1
        try:
            checkpoint._write_exclusive(self._fd, name, writer, remaining)
        except BaseException:
            self._bytes += remaining
            raise
        size, _, _ = checkpoint._read_file(self._fd, name, remaining)
        self._bytes += size

    def __call__(self, event, payload):
        _require(self.status == "open" and self._fd is not None, "sink_closed_or_poisoned")
        try:
            _require(type(event) is str and event in ("SCREEN_RESERVED", "CALL_RESERVED", "CALL_CAPTURED",
                                                     "SCREEN_FINISHED") and self.event_count < MAX_EVENTS,
                     "invalid_or_excess_event")
            encoder = _Encoder(self)
            encoded = encoder.encode(payload)
            protocol_error = None
            try:
                self._protocol.accept(event, encoded)
            except Exception as error:
                protocol_error = error
                encoder.unsupported(payload, "$", "event_protocol_error:" + _qualified(type(error)))
            document = dict(format=FORMAT, index=self.event_count, event=event,
                            previous_sha256=self._previous, export_status="incomplete" if encoder.issues else "complete",
                            issues=encoder.issues, payload=encoded)
            raw = checkpoint._json_bytes(document)
            name = f"event-{self.event_count:04d}.json"
            self._write(name, lambda stream: stream.write(raw), self.limits.event_bytes)
            _, self._previous, _ = checkpoint._read_file(self._fd, name, self.limits.event_bytes)
            self.event_count += 1
            if encoder.issues:
                raise CustodyExportError("incomplete_event", tuple(encoder.issues)) from protocol_error
            if event == "CALL_CAPTURED":
                self._captures[id(payload)] = (payload, self.event_count - 1)
            if event == "SCREEN_FINISHED":
                result = _verify_events(self._fd, self.event_count, self._previous, self.limits,
                                        marker_present=False)
                marker = checkpoint._json_bytes(dict(format=FORMAT, event_count=self.event_count,
                    last_sha256=self._previous, state_id=result.state_id, stage=result.stage,
                    terminal_reason=result.terminal_reason, scientific_success=False,
                    exception_custody="diagnostics_only"))
                self._write("COMPLETE", lambda stream: stream.write(marker), min(65536, self.limits.total_bytes))
                self.status = "complete"
        except BaseException as error:
            self.status, self.failure = "incomplete", error
            raise
