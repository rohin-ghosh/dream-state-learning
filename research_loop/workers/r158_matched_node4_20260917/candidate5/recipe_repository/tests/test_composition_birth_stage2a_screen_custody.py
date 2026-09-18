"""Local fake receipt export; optional existing torch-only CPU tensor coverage."""

from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as source
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training
from tests import test_composition_birth_stage2a_screen_runtime as runtime_tests


def record_fields(encoded):
    return dict(encoded[2])


def builtin(value):
    return training._plain(wire._freeze(value))


def native_fields(encoded):
    return {key[1]: value for key, value in encoded[1]}


def initial_screen():
    rows = tuple(runtime.Reservation(entry, 2 ** 64 - 1 - index)
                 for index, entry in enumerate(screen.reduced_screen("D1")))
    return runtime.ScreenRun("synthetic-state-attempt-1", "D1", rows, (), (), (), "pending", "SYNTHETIC")


def call_pair(initial, *, index=0, native=None, error=None, physical=0, native_index=7):
    row = initial.reservations[index]
    request = rollout.DecodeRequest((held.Message("system", "public"), held.Message("user", "only")),
                                    256, row.seed, 2)
    reserved = runtime.CallCustody(initial.state_id, row.entry.slot, request)
    generation = rollout.Generation(" STOP \n", 2, 2, False, "stop")
    record = dict(request=request, native_output=[[10, 20, 1]], native_sequences=[[10, 20, 1]],
                  generated_ids=(20, 1), raw=generation.raw, raw_bytes=generation.raw.encode(),
                  generation=generation, error=error)
    if native is not None:
        record.update(native)
    captured = replace(reserved, physical_call=physical, actor_call_index=native_index,
                       generation=generation, native_records=(record,), actor_error=error)
    return reserved, captured


def finish_screen(initial, captured=(), *, error=None):
    rows = list(initial.reservations)
    for capture in captured:
        index = next(index for index, row in enumerate(rows) if row.entry.slot == capture.slot)
        rows[index] = replace(rows[index], custody=capture, disposition="ERROR" if error else "EXECUTED")
    failures = () if error is None else (runtime.Failure("actor", captured[-1].slot if captured else None, error),)
    return replace(initial, reservations=tuple(rows), failures=failures,
                   terminal_reason="completed_unscored" if error is None else "aborted")


class FakeTensor:
    layout = "strided"
    is_quantized = False
    shape = (1, 3)
    dtype = "torch.int64"

    def numel(self):
        return 3

    def element_size(self):
        return 8

    def is_conj(self):
        return False

    def is_neg(self):
        return False

    def detach(self):
        return self

    def cpu(self):
        return self

    def contiguous(self):
        return self

    def clone(self):
        return self


class FakeTorch:
    Tensor = FakeTensor
    strided = "strided"

    def __init__(self, error=None):
        self.error = error
        self.saved = []

    def save(self, value, stream):
        self.saved.append(value)
        stream.write(b"synthetic-int64-tensor\x00" + struct.pack("!qqq", 10, 20, 1))
        if self.error is not None:
            raise self.error


class ScreenCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stage2a-screen-custody-")
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)
        self.destination = self.parent / "receipt"
        self.initial = initial_screen()

    def sink(self, **options):
        sink = source.ScreenCustodySink(self.destination, **options)
        self.addCleanup(sink.close)
        return sink

    def export(self, *, native=None, error=None, **options):
        sink = self.sink(**options)
        reserved, captured = call_pair(self.initial, native=native, error=error)
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        sink("CALL_CAPTURED", captured)
        final = finish_screen(self.initial, (captured,), error=error)
        sink("SCREEN_FINISHED", final)
        return sink, captured, source.verify_receipt(self.destination)

    def test_exact_builtin_bytes_high64_eos_and_tuple_list_types(self):
        values = dict(raw=b"\xff\x00 \r\n", text=" \u00e9\x00\ud800\n", ids=(2 ** 64 - 1, 1),
                      list_ids=[2 ** 64 - 1, 1], mutable=bytearray(b"\xff\x00"),
                      numeric_keys={1: "integer", "1": "string"},
                      float_bits=[-0.0, float("inf"), struct.unpack("!d", bytes.fromhex("7ff8000000000001"))[0]])
        sink, _, result = self.export(native={"extra": values})
        self.assertEqual(sink.status, "complete")
        self.assertEqual(result.terminal_reason, "completed_unscored")
        self.assertFalse(result.scientific_success)
        self.assertEqual(result.exception_custody, "diagnostics_only")
        self.assertEqual([event["event"] for event in result.events],
                         ["SCREEN_RESERVED", "CALL_RESERVED", "CALL_CAPTURED", "SCREEN_FINISHED"])
        root = record_fields(result.events[2]["payload"])
        request = record_fields(root["request"])
        self.assertEqual(request["seed"], builtin(2 ** 64 - 1))
        native = native_fields(root["native_records"][1][0])
        self.assertEqual(native["extra"], builtin(values))
        self.assertEqual(native["generated_ids"], builtin((20, 1)))
        self.assertEqual(native["raw"], builtin(" STOP \n"))
        self.assertEqual(native["raw_bytes"], builtin(b" STOP \n"))
        self.assertEqual(len(record_fields(result.events[0]["payload"])["reservations"][1]), 280)
        self.assertEqual(self.destination.stat().st_mode & 0o077, 0)
        self.assertTrue(all(path.stat().st_mode & 0o077 == 0 for path in self.destination.iterdir()))

    def test_aborted_screen_is_complete_custody_not_scientific_success(self):
        error = ValueError(b"\xff\x00", (2 ** 64 - 1, 1))
        error.native_output = [b"partial\x00", (20, 1)]
        _, captured, result = self.export(error=error)
        diagnostic = record_fields(result.events[2]["payload"])["actor_error"]
        self.assertEqual(diagnostic, ["exception_diagnostic", "builtins.ValueError",
                                      builtin(error.args), builtin(vars(error)), builtin(())])
        self.assertIs(captured.actor_error, error)
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertEqual(result.export_status, "complete")
        self.assertFalse(result.scientific_success)

    def test_counter_failure_without_actor_call_can_finish_aborted(self):
        sink = self.sink()
        sink("SCREEN_RESERVED", self.initial)
        sink("SCREEN_FINISHED", finish_screen(self.initial, error=ValueError("counter")))
        result = source.verify_receipt(self.destination)
        self.assertEqual(len(result.events), 2)
        self.assertEqual(result.terminal_reason, "aborted")

    def test_unknown_object_or_cycle_keeps_supported_siblings_then_poisoned(self):
        cyclic = []
        cyclic.append(cyclic)
        for value in (object(), cyclic):
            with self.subTest(value_type=type(value).__name__):
                self.destination = self.parent / type(value).__name__
                sink = self.sink()
                reserved, captured = call_pair(self.initial, native={"unknown": value, "after": b"exact\xff"})
                sink("SCREEN_RESERVED", self.initial)
                sink("CALL_RESERVED", reserved)
                with self.assertRaises(source.CustodyExportError):
                    sink("CALL_CAPTURED", captured)
                event = json.loads((self.destination / "event-0002.json").read_bytes())
                self.assertEqual(event["export_status"], "incomplete")
                native = native_fields(record_fields(event["payload"])["native_records"][1][0])
                self.assertEqual(native["after"], builtin(b"exact\xff"))
                self.assertEqual(record_fields(event["payload"])["generation"],
                                 ["record", source._qualified(rollout.Generation),
                                  [[name, builtin(value)] for name, value in vars(captured.generation).items()]])
                self.assertEqual(sink.status, "incomplete")
                before = {path.name: path.read_bytes() for path in self.destination.iterdir()}
                with self.assertRaisesRegex(ValueError, "poisoned"):
                    sink("SCREEN_FINISHED", finish_screen(self.initial, (captured,)))
                self.assertEqual(before, {path.name: path.read_bytes() for path in self.destination.iterdir()})
                self.assertFalse((self.destination / "COMPLETE").exists())

    def test_unsupported_exception_attachment_is_explicit_incomplete_diagnostic(self):
        error = RuntimeError("decode failure")
        error.unsupported = object()
        error.raw = b"native\x00"
        sink = self.sink()
        reserved, captured = call_pair(self.initial, error=error)
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        with self.assertRaises(source.CustodyExportError):
            sink("CALL_CAPTURED", captured)
        event = json.loads((self.destination / "event-0002.json").read_bytes())
        diagnostic = record_fields(event["payload"])["actor_error"]
        self.assertEqual(diagnostic[:3], ["exception_diagnostic", "builtins.RuntimeError", builtin(error.args)])
        self.assertEqual(native_fields(diagnostic[3])["raw"], builtin(error.raw))

    def test_declared_exception_slots_are_captured_and_cycles_fail_closed(self):
        class SlottedFailure(Exception):
            __slots__ = ("native_output",)

        error = SlottedFailure("slotted native output")
        error.native_output = (b"raw\xff", (20, 1))
        _, _, result = self.export(error=error)
        diagnostic = record_fields(result.events[2]["payload"])["actor_error"]
        self.assertEqual(diagnostic[4], builtin(((source._qualified(SlottedFailure), "native_output",
                                                 error.native_output),)))
        self.destination = self.parent / "cyclic-slots"
        error.native_output = error
        sink = self.sink()
        reserved, captured = call_pair(self.initial, error=error)
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        with self.assertRaises(source.CustodyExportError):
            sink("CALL_CAPTURED", captured)
        event = json.loads((self.destination / "event-0002.json").read_bytes())
        self.assertEqual(event["export_status"], "incomplete")
        self.assertTrue(any(issue["reason"] == "cyclic_field" for issue in event["issues"]))

    def test_tensor_only_sidecars_and_terminal_snapshot_reuse(self):
        torch = FakeTorch()
        sink = self.sink(torch=torch)
        reserved, captured = call_pair(self.initial, native={"native_output": FakeTensor()})
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        sink("CALL_CAPTURED", captured)
        captured.native_records[0]["raw"] = "later mutation, not first capture"
        sink("SCREEN_FINISHED", finish_screen(self.initial, (captured,)))
        result = source.verify_receipt(self.destination)
        self.assertEqual(len(torch.saved), 1)
        tensors = list(source._tensor_refs(result.events[2]["payload"]))
        self.assertEqual(len(tensors), 1)
        tensor = tensors[0]
        self.assertEqual((tensor["dtype"], tensor["shape"]), ("torch.int64", [1, 3]))
        self.assertEqual(tensor["sha256"], sha256((self.destination / tensor["name"]).read_bytes()).hexdigest())
        final_row = record_fields(record_fields(result.events[-1]["payload"])["reservations"][1][0])
        self.assertEqual(final_row["custody"], ["call_capture_ref", 2])
        capture = record_fields(result.events[final_row["custody"][1]]["payload"])
        self.assertEqual(native_fields(capture["native_records"][1][0])["raw"], builtin(" STOP \n"))

    def test_tensor_cpu_copy_failure_before_any_id_conversion_is_retained(self):
        error = RuntimeError("synthetic cpu copy failure")
        tensor = FakeTensor()
        sink = self.sink(torch=FakeTorch())
        reserved, captured = call_pair(self.initial, native={"native_output": tensor,
                                                            "native_sequences": None, "generated_ids": None})
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        with patch.object(tensor, "cpu", side_effect=error), self.assertRaises(source.CustodyExportError):
            sink("CALL_CAPTURED", captured)
        self.assertIs(sink.tensor_errors[0], error)
        self.assertIs(captured.native_records[0]["native_output"], tensor)
        event = json.loads((self.destination / "event-0002.json").read_bytes())
        self.assertEqual(event["export_status"], "incomplete")
        native = native_fields(record_fields(event["payload"])["native_records"][1][0])
        self.assertEqual(native["generated_ids"], builtin(None))
        self.assertEqual(native["raw_bytes"], builtin(b" STOP \n"))
        self.assertFalse(list(self.destination.glob("*.pt")))

    def test_tensor_write_failure_keeps_partial_sidecar_and_native_ids(self):
        error = OSError("synthetic failed serializer")
        torch = FakeTorch(error)
        sink = self.sink(torch=torch)
        reserved, captured = call_pair(self.initial, native={"native_output": FakeTensor()})
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        with self.assertRaises(source.CustodyExportError):
            sink("CALL_CAPTURED", captured)
        self.assertIs(sink.tensor_errors[0], error)
        self.assertTrue((self.destination / "event-0002-tensor-0000.pt").read_bytes())
        event = json.loads((self.destination / "event-0002.json").read_bytes())
        native = native_fields(record_fields(event["payload"])["native_records"][1][0])
        self.assertEqual(native["generated_ids"], builtin((20, 1)))
        self.assertEqual(event["export_status"], "incomplete")
        self.assertFalse((self.destination / "COMPLETE").exists())

    def test_no_backend_or_unsupported_tensor_layout_fails_closed(self):
        for backend, tensor in ((None, FakeTensor()), (FakeTorch(), FakeTensor())):
            with self.subTest(backend=backend is not None):
                self.destination = self.parent / str(backend is not None)
                if backend is not None:
                    tensor.layout = "sparse"
                sink = self.sink(torch=backend)
                reserved, captured = call_pair(self.initial, native={"native_output": tensor})
                sink("SCREEN_RESERVED", self.initial)
                sink("CALL_RESERVED", reserved)
                with self.assertRaises(source.CustodyExportError):
                    sink("CALL_CAPTURED", captured)
                self.assertFalse(list(self.destination.glob("*.pt")))

    def test_incorrect_call_bindings_are_retained_and_never_completed(self):
        changes = ({"state_id": "other"}, {"physical_call": 1}, {"actor_call_index": -1},
                   {"request": replace(call_pair(self.initial)[1].request, seed=1)})
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                self.destination = self.parent / f"binding-{index}"
                sink = self.sink()
                reserved, captured = call_pair(self.initial)
                sink("SCREEN_RESERVED", self.initial)
                sink("CALL_RESERVED", reserved)
                with self.assertRaises(source.CustodyExportError):
                    sink("CALL_CAPTURED", replace(captured, **change))
                self.assertTrue((self.destination / "event-0002.json").exists())
                self.assertEqual(sink.status, "incomplete")

    def test_duplicate_reservation_and_terminal_capture_drift(self):
        for mode in ("duplicate", "drift"):
            with self.subTest(mode=mode):
                self.destination = self.parent / mode
                sink = self.sink()
                reserved, captured = call_pair(self.initial)
                sink("SCREEN_RESERVED", self.initial)
                sink("CALL_RESERVED", reserved)
                if mode == "duplicate":
                    event, payload = "CALL_RESERVED", reserved
                else:
                    sink("CALL_CAPTURED", captured)
                    event = "SCREEN_FINISHED"
                    payload = finish_screen(self.initial, (replace(captured, generation=None),))
                with self.assertRaises(source.CustodyExportError):
                    sink(event, payload)
                self.assertFalse((self.destination / "COMPLETE").exists())

    def test_capture_before_reserve_and_finish_while_call_pending(self):
        for mode in ("capture_first", "pending_finish"):
            with self.subTest(mode=mode):
                self.destination = self.parent / mode
                sink = self.sink()
                reserved, captured = call_pair(self.initial)
                sink("SCREEN_RESERVED", self.initial)
                if mode == "pending_finish":
                    sink("CALL_RESERVED", reserved)
                    event, payload = "SCREEN_FINISHED", finish_screen(self.initial)
                else:
                    event, payload = "CALL_CAPTURED", captured
                with self.assertRaises(source.CustodyExportError):
                    sink(event, payload)
                self.assertEqual(sink.status, "incomplete")

    def test_completion_marker_fsync_failure_is_incomplete_despite_readable_bytes(self):
        sink = self.sink()
        sink("SCREEN_RESERVED", self.initial)
        original = checkpoint._write_exclusive
        error = OSError("uncertain completion directory fsync")

        def fail_marker(descriptor, name, writer, limit):
            original(descriptor, name, writer, limit)
            if name == "COMPLETE":
                raise error

        with patch.object(checkpoint, "_write_exclusive", fail_marker), self.assertRaises(OSError):
            sink("SCREEN_FINISHED", finish_screen(self.initial))
        self.assertEqual(sink.status, "incomplete")
        self.assertIs(sink.failure, error)
        self.assertTrue((self.destination / "COMPLETE").exists())
        self.assertEqual(source.verify_receipt(self.destination).export_status, "complete")
        with self.assertRaisesRegex(ValueError, "poisoned"):
            sink("SCREEN_FINISHED", finish_screen(self.initial))

    def test_fresh_directory_and_exclusive_files_never_overwrite(self):
        sink = self.sink()
        with self.assertRaises(FileExistsError):
            source.ScreenCustodySink(self.destination)
        target = self.parent / "preserve"
        target.write_bytes(b"unchanged")
        (self.destination / "event-0000.json").symlink_to(target)
        with self.assertRaises(FileExistsError):
            sink("SCREEN_RESERVED", self.initial)
        self.assertEqual(target.read_bytes(), b"unchanged")
        self.assertEqual(sink.status, "incomplete")

    def test_write_and_fsync_failures_keep_partial_files_no_retry(self):
        for phase in ("write", "fsync"):
            with self.subTest(phase=phase):
                self.destination = self.parent / phase
                sink = self.sink()
                error = OSError("synthetic " + phase)

                def partial(descriptor, name, writer, limit):
                    def fail(stream):
                        stream.write(b"partial")
                        raise error
                    return original(descriptor, name, fail, limit)

                original = checkpoint._write_exclusive
                target = patch.object(checkpoint, "_write_exclusive", partial) if phase == "write" else \
                    patch.object(checkpoint.os, "fsync", side_effect=error)
                with target, self.assertRaises(OSError) as raised:
                    sink("SCREEN_RESERVED", self.initial)
                self.assertIs(raised.exception, error)
                self.assertTrue((self.destination / "event-0000.json").read_bytes())
                self.assertFalse((self.destination / "COMPLETE").exists())
                self.assertEqual(sink.status, "incomplete")

    def test_event_and_total_byte_bounds_preserve_partial_file(self):
        for limits in (source.ReceiptLimits(event_bytes=100), source.ReceiptLimits(total_bytes=100)):
            with self.subTest(limits=limits):
                self.destination = self.parent / str(limits.event_bytes)
                sink = self.sink(limits=limits)
                with self.assertRaises(ValueError):
                    sink("SCREEN_RESERVED", self.initial)
                self.assertTrue((self.destination / "event-0000.json").exists())
                self.assertLessEqual((self.destination / "event-0000.json").stat().st_size, 100)
                self.assertFalse((self.destination / "COMPLETE").exists())

    def test_final_marker_requires_rereading_and_verifying_prior_events(self):
        sink = self.sink()
        reserved, captured = call_pair(self.initial)
        sink("SCREEN_RESERVED", self.initial)
        sink("CALL_RESERVED", reserved)
        sink("CALL_CAPTURED", captured)
        first = self.destination / "event-0000.json"
        first.write_bytes(first.read_bytes().replace(b"synthetic-state", b"corrupted-state"))
        with self.assertRaises(ValueError):
            sink("SCREEN_FINISHED", finish_screen(self.initial, (captured,)))
        self.assertTrue((self.destination / "event-0003.json").exists())
        self.assertFalse((self.destination / "COMPLETE").exists())

    def test_verification_detects_corruption_missing_order_and_extra_files(self):
        self.export(native={"native_output": FakeTensor()}, torch=FakeTorch())
        original = {path.name: path.read_bytes() for path in self.destination.iterdir()}
        mutations = ("event", "missing", "order", "tensor", "marker", "extra", "symlink")
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                for path in self.destination.iterdir():
                    path.unlink()
                for name, raw in original.items():
                    (self.destination / name).write_bytes(raw)
                if mutation == "event":
                    (self.destination / "event-0001.json").write_bytes(b"{}")
                elif mutation == "missing":
                    (self.destination / "event-0001.json").unlink()
                elif mutation == "order":
                    (self.destination / "event-0001.json").write_bytes(original["event-0002.json"])
                elif mutation == "tensor":
                    (self.destination / "event-0002-tensor-0000.pt").write_bytes(b"bad")
                elif mutation == "marker":
                    (self.destination / "COMPLETE").unlink()
                elif mutation == "extra":
                    (self.destination / "orphan").write_bytes(b"retained partial")
                else:
                    target = self.parent / "borrowed"
                    target.write_bytes(original["event-0001.json"])
                    (self.destination / "event-0001.json").unlink()
                    (self.destination / "event-0001.json").symlink_to(target)
                with self.assertRaises((ValueError, OSError)):
                    source.verify_receipt(self.destination)

    def test_import_and_read_only_verifier_need_no_torch_or_loader(self):
        self.export(native={"native_output": FakeTensor()}, torch=FakeTorch())
        script = (
            "import sys; from organism_v6 import composition_birth_stage2a_screen_custody as custody; "
            "custody.verify_receipt(sys.argv[1]); "
            "assert not any(name in sys.modules for name in ('torch', 'transformers', 'peft'))"
        )
        subprocess.run([sys.executable, "-B", "-c", script, str(self.destination)], check=True)


class ScreenRuntimeSinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime_tests.ScreenRuntimeTests.setUpClass()

    def test_dispatch_success_and_sink_failure_no_later_actor_calls(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as parent:
                destination = Path(parent) / "receipt"
                actor = runtime_tests.FakeActor()
                if not fail:
                    actor.native_output = {"ids": [10, 20, 1], "raw": b"STOP"}
                with source.ScreenCustodySink(destination) as sink:
                    result, _, _ = runtime_tests.ScreenRuntimeTests().run_fixture(actor=actor, sink=sink)
                    self.assertEqual(len(result.reservations), 280)
                    if fail:
                        self.assertEqual(len(actor.requests), 1)
                        self.assertEqual(result.terminal_reason, "aborted")
                        self.assertEqual(sink.status, "incomplete")
                        self.assertIs(result.calls[0].native_records[0], actor.calls[0])
                        self.assertIs(result.calls[0].sink_error, sink.failure)
                        self.assertEqual(result.reservations[-1].disposition, "NOT_REACHED")
                        self.assertFalse((destination / "COMPLETE").exists())
                    else:
                        verified = source.verify_receipt(destination)
                        self.assertEqual(len(actor.requests), 56)
                        self.assertEqual(len(verified.events), 114)
                        self.assertEqual(sum(row.disposition == "UNUSED" for row in result.reservations), 224)
                        self.assertEqual(verified.terminal_reason, "completed_unscored")

    def test_actor_exception_exports_aborted_screen_with_diagnostics(self):
        error = RuntimeError("native failure")
        error.raw = b"exact\xff\x00"

        def fail(request):
            raise error

        actor = runtime_tests.FakeActor(fail)
        actor.native_output = [10, 20, 1]
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "receipt"
            with source.ScreenCustodySink(destination) as sink:
                result, _, _ = runtime_tests.ScreenRuntimeTests().run_fixture(actor=actor, sink=sink)
                self.assertEqual(len(actor.requests), 1)
                self.assertIs(result.calls[0].actor_error, error)
                verified = source.verify_receipt(destination)
                self.assertEqual((verified.export_status, verified.terminal_reason), ("complete", "aborted"))
                self.assertFalse(verified.scientific_success)

    def test_driver_transport_failure_is_aborted_complete_custody(self):
        actor = runtime_tests.FakeActor(lambda request: rollout.Generation("STOP", 1, 2, False, "stop"))
        actor.native_output = [10, 20, 1]
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "receipt"
            with source.ScreenCustodySink(destination) as sink:
                result, _, _ = runtime_tests.ScreenRuntimeTests().run_fixture(actor=actor, sink=sink)
                self.assertEqual(len(actor.requests), 1)
                self.assertEqual(result.terminal_reason, "aborted")
                self.assertTrue(result.failures)
                self.assertIs(result.calls[0].generation, actor.calls[0]["generation"])
                self.assertEqual(result.reservations[-1].disposition, "NOT_REACHED")
                self.assertEqual(source.verify_receipt(destination).terminal_reason, "aborted")


@unittest.skipUnless(importlib.util.find_spec("torch") is not None, "optional existing torch unavailable")
class NativeCPUTensorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls.torch = torch

    def test_plain_int64_tensor_sidecar_cpu_roundtrip_without_rng_changes(self):
        torch = self.torch
        rng = torch.get_rng_state().clone()
        tensor = torch.tensor([[0, 2 ** 63 - 1, 1]], dtype=torch.int64, device="cpu")
        original = tensor.clone()
        initial = initial_screen()
        reserved, captured = call_pair(initial, native={"native_output": tensor})
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "receipt"
            with source.ScreenCustodySink(destination, torch=torch) as sink:
                sink("SCREEN_RESERVED", initial)
                sink("CALL_RESERVED", reserved)
                sink("CALL_CAPTURED", captured)
                sink("SCREEN_FINISHED", finish_screen(initial, (captured,)))
            result = source.verify_receipt(destination)
            metadata = list(source._tensor_refs(result.events[2]["payload"]))[0]
            restored = torch.load(destination / metadata["name"], weights_only=True, map_location="cpu")
            self.assertIs(type(restored), torch.Tensor)
            self.assertEqual(restored.dtype, tensor.dtype)
            self.assertEqual(restored.shape, tensor.shape)
            self.assertTrue(torch.equal(restored, original))
            self.assertTrue(torch.equal(tensor, original))
            self.assertTrue(torch.equal(torch.get_rng_state(), rng))


if __name__ == "__main__":
    unittest.main()
