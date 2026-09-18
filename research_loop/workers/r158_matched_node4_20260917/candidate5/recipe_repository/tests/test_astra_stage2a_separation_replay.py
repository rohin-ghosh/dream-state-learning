"""Synthetic retained-format recovery tests; never replay the real attempt.

Tiny synthetic graph/source shapes exercise the actual loader and CPU join.
Snapshot launching and process-limit mutation are mocked where explicitly used;
these tests are not full-source execution, provenance or real outcome evidence.
"""

from copy import deepcopy
from dataclasses import fields, is_dataclass
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_separation_replay as replay
from organism_v6 import composition_birth_stage2a_separation as separation
from tests.test_composition_birth_stage2a_separation import (
    birth_record, chain_record, intervention_record, synthetic_packet)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(replay.snapshot_helper.encode(value))


def retain(value, root):
    if type(value) is bytes:
        checksum = sha256(value).hexdigest()
        path = root / "artifacts" / checksum
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(value)
        return {"bytes_sha256": checksum, "length": len(value)}
    if is_dataclass(value):
        return {"dataclass": type(value).__module__ + "." + type(value).__qualname__,
                "fields": [[field.name, retain(getattr(value, field.name), root)] for field in fields(value)]}
    if type(value) is tuple:
        return {"tuple": [retain(item, root) for item in value]}
    return value


def recovery_fixture(base, *, populate=False, collisions=False):
    original, checkout = base / "original", base / "checkout"
    original.mkdir()
    current = (replay.ROOT / replay.SEPARATION_PATH).read_bytes()
    old = current.replace(b'"total_bytes": 2 * 1024 * 1024 * 1024,', b'"total_bytes": 512 * 1024 * 1024,').replace(
        b"aggregate supplied bytes <=2 GiB (counting", b"aggregate supplied bytes <=512 MiB (counting")
    sources = {replay.SEPARATION_PATH: old, replay.SEPARATION_TEST_PATH: b"old synthetic test",
               "organism_v6/composition_birth_stage2a_checker.py": b"unchanged checker fixture",
               "organism_v6/composition_birth_stage2a_core_inputs.py": b"unchanged constructor fixture",
               "organism_v6/composition_birth_stage2a_typed_scan.py": b"unchanged scanner fixture",
               "gpu/astra_stage2a_cpu_separation.py": b"unchanged helper fixture", "gpu/__init__.py": b""}
    old_pins = {name: replay.digest(raw) for name, raw in sources.items()}
    for name, raw in sources.items():
        path = original / "source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    sources.update({replay.SEPARATION_PATH: current, replay.SEPARATION_TEST_PATH: b"new regression fixture",
                    replay.REPLAY_PATH: b"replay fixture", replay.REPLAY_TEST_PATH: b"replay tests fixture"})
    pins = {name: replay.digest(raw) for name, raw in sources.items()}
    for name, raw in sources.items():
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    write(original / "SNAPSHOT.json", {"source_pins": old_pins})
    write(original / "manifest.json", {"source_pins": old_pins, "kind": "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS",
                                      "expected_birth_records": 512, "expected_intervention_members": 64,
                                      "expected_chain_members": 32, "expected_chain_boundaries": 240})
    write(original / "report.json", {"source_pins": old_pins, "status": "ERROR", "error": "aggregate_byte_bound_exceeded",
                                    "kind": "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS", "native_authorized": False,
                                    "scientific_claims": False})
    if populate:
        birth_packet = synthetic_packet()
        held_packet = birth_packet if collisions else synthetic_packet(extra_destination=True, skin=1)
        for world in range(32):
            records = [birth_record(birth_packet, identity) for identity in sorted(separation.BIRTH_IDENTITIES)
                       if identity[0].startswith(f"p{world:02d}/")]
            write(original / f"birth_p{world:02d}.json", {"shared": retain(b"synthetic shared", original),
                                                       "records": [retain(record, original) for record in records]})
        for world in sorted({world for world, member in separation.INTERVENTION_IDENTITIES}):
            write(original / f"intervention_{world}.json",
                  [retain(intervention_record(held_packet, (world, member)), original) for member in ("m0", "m1")])
        for world in sorted(separation.CHAIN_WORLDS):
            write(original / f"chain_{world}.json", retain(chain_record(held_packet, world, (7, 8)), original))
        write(original / "allocation.json", retain(b"synthetic allocation", original))
    else:
        for name in replay.INDEX_NAMES:
            write(original / name, {})
    return original, checkout, pins


class RetainedDecoderTests(unittest.TestCase):
    def test_allocation_custody_capacity_does_not_relax_core_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b"a" * (replay.MAX_BLOB_BYTES + 1)
            reference = retain(raw, root)
            decoder = replay.RetainedDecoder(root)
            with self.assertRaisesRegex(ValueError, "bounded_blob_digest_and_length_required"):
                decoder.decode(reference)
            self.assertEqual(decoder.blob(reference, max_bytes=replay.MAX_ALLOCATION_BYTES), raw)
            decoder.verify_unchanged()
            with self.assertRaisesRegex(ValueError, "bounded_blob_digest_and_length_required"):
                decoder.decode(reference)
            too_large = dict(reference, length=replay.MAX_ALLOCATION_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "bounded_blob_digest_and_length_required"):
                decoder.blob(too_large, max_bytes=replay.MAX_ALLOCATION_BYTES)

    def test_registry_only_four_classes_and_import_does_not_load_implementation(self):
        self.assertEqual({cls.__name__ for cls in replay.type_registry().values()},
                         {"BirthCoreInputs", "InterventionCoreInputs", "ChainCoreInputs", "ChainCoreBoundary"})
        subprocess.run([sys.executable, "-B", "-c", "import sys; from gpu import astra_stage2a_separation_replay; "
                        "assert not any(name.startswith(('organism_v6', 'torch', 'transformers')) for name in sys.modules)"],
                       cwd=replay.ROOT, check=True)
        source = inspect.getsource(replay)
        for forbidden in ("importlib", "pickle", "eval(", "exec(", "build_birth_", "build_chain_",
                          "build_intervention_", "allocate_stage2a("):
            self.assertNotIn(forbidden, source)

    def test_roundtrip_four_classes_and_cache_bytes_by_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = synthetic_packet()
            values = (birth_record(packet), intervention_record(packet), chain_record(packet))
            decoder = replay.RetainedDecoder(root)
            for value in values:
                encoded = retain(value, root)
                self.assertEqual(decoder.decode(encoded), value)
            encoded = retain(values[0], root)
            first, second = decoder.decode(encoded), decoder.decode(encoded)
            self.assertIs(first.core_bytes, second.core_bytes)
            self.assertIs(first.checker_payload, second.checker_payload)
            self.assertGreater(decoder.reference_bytes, decoder.unique_bytes)
            decoder.verify_unchanged()

    def test_strict_dataclass_fields_types_tags_and_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            encoded = retain(birth_record(synthetic_packet()), root)
            mutations = [{"mapping": []}, [], {"tuple": [None] * 59}, {"dataclass": "builtins.eval", "fields": []}]
            changed = deepcopy(encoded)
            changed["fields"].pop()
            mutations.append(changed)
            changed = deepcopy(encoded)
            changed["fields"].append(changed["fields"][0])
            mutations.append(changed)
            changed = deepcopy(encoded)
            changed["fields"].reverse()
            mutations.append(changed)
            changed = deepcopy(encoded)
            changed["extra"] = True
            mutations.append(changed)
            for field, value in (("unit_id", 1), ("semantic_route_depth", True), ("semantic_route_depth", -1),
                                 ("core_bytes", "not bytes"), ("semantic_route_depth", {"tuple": []})):
                changed = deepcopy(encoded)
                for entry in changed["fields"]:
                    if entry[0] == field:
                        entry[1] = value
                mutations.append(changed)
            for changed in mutations:
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    replay.RetainedDecoder(root).decode(changed)
            decoder = replay.RetainedDecoder(root)
            with self.assertRaisesRegex(ValueError, "decode_bound"):
                decoder.decode(encoded, depth=13)
            decoder.nodes = replay.MAX_DECODE_NODES
            with self.assertRaisesRegex(ValueError, "decode_bound"):
                decoder.decode(encoded)

    def test_blob_digest_length_mutation_symlink_and_reverification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = retain(b"original immutable bytes", root)
            for changes in ({"bytes_sha256": "../escape"}, {"bytes_sha256": "a" * 63},
                            {"length": True}, {"length": 0}, {"length": replay.MAX_BLOB_BYTES + 1},
                            {"length": reference["length"] - 1}, {"extra": True}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    replay.RetainedDecoder(root).blob(dict(reference, **changes))
            decoder = replay.RetainedDecoder(root)
            cached = decoder.blob(reference)
            with self.assertRaisesRegex(ValueError, "duplicate_blob_length"):
                decoder.blob(dict(reference, length=reference["length"] + 1))
            path = root / "artifacts" / reference["bytes_sha256"]
            path.write_bytes(b"modified immutable bytes")
            self.assertIs(decoder.blob(reference), cached)
            with self.assertRaisesRegex(ValueError, "changed_during_replay"):
                decoder.verify_unchanged()
            with self.assertRaisesRegex(ValueError, "hash_or_length"):
                replay.RetainedDecoder(root).blob(reference)
            path.unlink()
            target = root / "target"
            target.write_bytes(cached)
            path.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                replay.RetainedDecoder(root).blob(reference)
            decoder.reference_bytes = replay.MEMORY_LIMIT_BYTES
            with self.assertRaisesRegex(ValueError, "reference_byte_bound"):
                decoder.blob(reference)


class RecoveryPinsTests(unittest.TestCase):
    def test_exact_capacity_repair_and_preserved_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, checkout, pins = recovery_fixture(Path(temporary))
            captured = replay.capture_recovery(original, pins)
            self.assertEqual(captured["repair"]["aggregate_after"], 2 * 1024 ** 3)
            self.assertEqual(captured["repair"]["per_blob_bytes"], 32 * 1024 ** 2)
            self.assertEqual(replay.MEMORY_LIMIT_BYTES, 2 * 1024 ** 3)
            self.assertEqual(set(captured["original_files"]), set(replay.INDEX_NAMES + replay.CONTROL_NAMES))
            changed = dict(pins)
            changed[replay.SEPARATION_PATH] = replay.digest((checkout / replay.SEPARATION_PATH).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "noncapacity"):
                replay.capture_recovery(original, changed)
            for name in ("organism_v6/composition_birth_stage2a_checker.py",
                         "organism_v6/composition_birth_stage2a_core_inputs.py",
                         "organism_v6/composition_birth_stage2a_typed_scan.py"):
                with self.assertRaisesRegex(ValueError, "source_pin_changed"):
                    replay.capture_recovery(original, dict(pins, **{name: "0" * 64}))
            with self.assertRaisesRegex(ValueError, "source_pin_set_changed"):
                replay.capture_recovery(original, dict(pins, foreign="0" * 64))

    def test_original_status_error_counts_and_pin_mutations_rejected(self):
        for changes in ({"status": "SEPARATED"}, {"error": "other"}, {"counts": {}}, {"native_authorized": True},
                        {"source_pins": {}}):
            with tempfile.TemporaryDirectory() as temporary:
                original, unused, pins = recovery_fixture(Path(temporary))
                report = json.loads((original / "report.json").read_bytes())
                write(original / "report.json", dict(report, **changes))
                with self.assertRaises(ValueError):
                    replay.capture_recovery(original, pins)
        with tempfile.TemporaryDirectory() as temporary:
            original, unused, pins = recovery_fixture(Path(temporary))
            source = original / "source" / "organism_v6/composition_birth_stage2a_checker.py"
            source.write_bytes(b"mutated snapshot")
            with self.assertRaisesRegex(ValueError, "original_source_snapshot_changed"):
                replay.capture_recovery(original, pins)

    def test_missing_extra_and_duplicate_json_indexes_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, unused, pins = recovery_fixture(Path(temporary))
            (original / "birth_p00.json").unlink()
            with self.assertRaisesRegex(ValueError, "index_set"):
                replay.capture_recovery(original, pins)
            write(original / "birth_p00.json", {})
            write(original / "birth_p32.json", {})
            with self.assertRaisesRegex(ValueError, "index_set"):
                replay.capture_recovery(original, pins)
            path = original / "duplicate.json"
            path.write_bytes(b'{"key":1,"key":2}')
            with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
                replay.read_json(path)

    def test_snapshot_helper_exclusive_readonly_detached_cpu_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, checkout, pins = recovery_fixture(Path(temporary))
            out = Path(temporary) / "replay"
            options = SimpleNamespace(original=str(original), out=str(out), snapshot_manifest=None)

            def child(command, **kwargs):
                snapshot = out / "source"
                self.assertEqual(kwargs["cwd"], snapshot)
                self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
                self.assertEqual(kwargs["env"]["HF_HUB_OFFLINE"], "1")
                self.assertEqual(kwargs["env"]["PYTHONPATH"], str(snapshot))
                self.assertEqual(snapshot.stat().st_mode & 0o222, 0)
                self.assertEqual((snapshot / replay.REPLAY_PATH).stat().st_mode & 0o222, 0)
                self.assertIn(str(snapshot / replay.REPLAY_PATH), command)
                self.assertNotIn("--master", command)
                (checkout / replay.SEPARATION_PATH).write_bytes(b"later main edit")
                self.assertEqual(replay.digest((snapshot / replay.SEPARATION_PATH).read_bytes()), pins[replay.SEPARATION_PATH])
                return SimpleNamespace(returncode=0)

            with patch.object(replay, "ROOT", checkout), patch.object(replay, "source_pins", return_value=pins), \
                    patch.object(replay.subprocess, "run", side_effect=child), \
                    patch.object(replay.snapshot_helper, "write_once", wraps=replay.snapshot_helper.write_once) as writer:
                self.assertEqual(replay.bootstrap(options), 0)
                self.assertGreater(writer.call_count, len(pins))
                with self.assertRaises(FileExistsError):
                    replay.bootstrap(options)


class SyntheticRecoveryExecutionTests(unittest.TestCase):
    def test_real_synthetic_loader_roster_join_and_index_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, unused, pins = recovery_fixture(Path(temporary), populate=True)
            recovery = replay.capture_recovery(original, pins)
            births, interventions, chains, decoder = replay.load_inputs(original, recovery)
            self.assertEqual((len(births), len(interventions), len(chains)), (512, 64, 16))
            self.assertEqual(sum(len(chain.boundaries) for chain in chains), 240)
            result = separation.check_held_birth_separation(birth_inputs=births, intervention_inputs=interventions,
                                                           chain_core_inputs=chains)
            self.assertTrue(result.separated)
            decoder.verify_unchanged()
            index = original / "birth_p00.json"
            index.write_bytes(index.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "index_pin_mismatch"):
                replay.load_inputs(original, recovery)

    def test_worker_receipt_pins_collisions_closed_gates_and_no_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, unused, pins = recovery_fixture(Path(temporary), populate=True, collisions=True)
            out = Path(temporary) / "replay"
            out.mkdir()
            recovery = replay.capture_recovery(original, pins)
            write(out / "SNAPSHOT.json", {"source_pins": pins})
            write(out / "RECOVERY.json", recovery)
            options = SimpleNamespace(out=str(out), original=str(original), snapshot_manifest=str(out / "SNAPSHOT.json"))
            with patch.object(replay, "ROOT", out / "source"), patch.object(replay, "source_pins", return_value=pins), \
                    patch.object(replay.resource, "setrlimit") as limit:
                self.assertEqual(replay.execute(options), 1)
                limit.assert_called_once_with(replay.resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
                with self.assertRaisesRegex(ValueError, "exclusive_new_replay"):
                    replay.execute(options)
            raw = (out / "report.json").read_bytes()
            report = json.loads(raw)
            self.assertEqual(report["status"], "COLLISION")
            self.assertEqual(report["counts"]["core_collision_pairs"], 512 * (64 + 240))
            self.assertEqual(report["original_files"], recovery["original_files"])
            self.assertEqual(report["snapshot_manifest_sha256"], replay.digest((out / "SNAPSHOT.json").read_bytes()))
            self.assertEqual(report["recovery_manifest_sha256"], replay.digest((out / "RECOVERY.json").read_bytes()))
            self.assertEqual((out / "report.sha256").read_text(), replay.digest(raw) + "  report.json\n")
            for name in ("native_authorized", "source_authenticated", "constructors_rerun", "scientific_claims"):
                self.assertIs(report[name], False)

    def test_wrong_snapshot_and_late_blob_mutation_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, unused, pins = recovery_fixture(Path(temporary), populate=True)
            out = Path(temporary) / "replay"
            out.mkdir()
            options = SimpleNamespace(out=str(out), original=str(original), snapshot_manifest=str(out / "SNAPSHOT.json"))
            with self.assertRaisesRegex(ValueError, "snapshot_execution"):
                replay.execute(options)
            write(out / "SNAPSHOT.json", {"source_pins": pins})
            write(out / "RECOVERY.json", replay.capture_recovery(original, pins))
            with patch.object(replay, "ROOT", out / "source"), patch.object(replay, "source_pins", return_value=pins), \
                    patch.object(replay.resource, "setrlimit"), \
                    patch.object(replay.RetainedDecoder, "verify_unchanged", side_effect=ValueError("late blob mutation")):
                self.assertEqual(replay.execute(options), 1)
            report = json.loads((out / "report.json").read_bytes())
            self.assertEqual(report["status"], "ERROR")
            self.assertEqual(report["error"], "late blob mutation")
            self.assertNotIn("counts", report)


if __name__ == "__main__":
    unittest.main()
