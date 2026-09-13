"""Filesystem-only checks plus opt-in-by-availability real-torch CPU regression.

The pure tests publish explicitly non-torch byte fixtures through the private
filesystem helper. They assert no tensor, optimizer or training evidence. Native
tests reuse the accepted tiny CPU model; nothing loads Qwen/tokenizers/PEFT or
allocates GPUs. Main may run the native class in an immutable temporary bundle
with CUDA_VISIBLE_DEVICES=''. No packages are installed by this module.
Native test processes explicitly clear ambient torch safe globals: imports in
the tiny fixture may register unrelated tensor subclasses. The loader itself
never clears or expands a caller's registry and rejects a nonempty registry.
"""

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_checkpoint as source
from organism_v6 import composition_birth_stage2a_training as training
from tests import test_composition_birth_stage2a_training as fixtures


HAS_TORCH = importlib.util.find_spec("torch") is not None
BYTE_FIXTURE = b"SYNTHETIC FILESYSTEM BYTES ONLY: not a torch checkpoint\n"
BYTE_METADATA = dict(state_format="stage2a-state-v1", state_sha256="1" * 64,
                     completed_updates=256, cursor=1024, binding_sha256="2" * 64)


def byte_bundle(path, *, writer=None, limit=4096):
    return source._publish(path, dict(BYTE_METADATA),
                           (lambda stream: stream.write(BYTE_FIXTURE)) if writer is None else writer,
                           max_blob_bytes=limit)


def rewrite_manifest(path, raw):
    (path / source.MANIFEST_NAME).write_bytes(raw)
    (path / source.COMMIT_NAME).write_bytes(sha256(raw).hexdigest().encode("ascii") + b"\n")


class Stage2ACheckpointFilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stage2a-state-io-test-")
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)
        self.destination = self.parent / "fresh"

    def test_lazy_import_and_inspection_open_no_science_gates(self):
        byte_bundle(self.destination)
        script = (
            "import sys; from organism_v6 import composition_birth_stage2a_checkpoint as module; "
            "module.inspect_checkpoint(sys.argv[1]); assert 'torch' not in sys.modules; "
            "assert not any(module.SCIENCE_GATES.values())"
        )
        subprocess.run([sys.executable, "-c", script, str(self.destination)], check=True)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_integrity_manifest_and_commit_marker_for_non_torch_bytes(self):
        manifest = byte_bundle(self.destination)
        self.assertEqual(manifest, source.inspect_checkpoint(self.destination))
        self.assertEqual(manifest["blob"], dict(name=source.BLOB_NAME, size_bytes=len(BYTE_FIXTURE),
                                              sha256=sha256(BYTE_FIXTURE).hexdigest()))
        raw = (self.destination / source.MANIFEST_NAME).read_bytes()
        self.assertEqual((self.destination / source.COMMIT_NAME).read_bytes(),
                         sha256(raw).hexdigest().encode("ascii") + b"\n")
        self.assertEqual({path.name for path in self.destination.iterdir()},
                         {source.BLOB_NAME, source.MANIFEST_NAME, source.COMMIT_NAME})
        self.assertEqual(self.destination.stat().st_mode & 0o077, 0)
        for path in self.destination.iterdir():
            self.assertEqual(path.stat().st_mode & 0o077, 0)

    def test_existing_directory_file_and_symlink_never_overwritten(self):
        self.destination.mkdir()
        marker = self.destination / "keep"
        marker.write_bytes(b"keep exact bytes")
        file_path = self.parent / "existing-file"
        file_path.write_bytes(b"original")
        link = self.parent / "existing-link"
        link.symlink_to(self.destination, target_is_directory=True)
        broken = self.parent / "broken-link"
        broken.symlink_to(self.parent / "absent")
        for destination in (self.destination, file_path, link, broken):
            with self.subTest(destination=destination.name), self.assertRaises(FileExistsError):
                byte_bundle(destination)
        self.assertEqual(marker.read_bytes(), b"keep exact bytes")
        self.assertEqual(file_path.read_bytes(), b"original")
        self.assertTrue(link.is_symlink())
        self.assertTrue(broken.is_symlink())

    def test_missing_parent_and_remote_style_paths_rejected(self):
        with self.assertRaises(FileNotFoundError):
            byte_bundle(self.parent / "absent" / "child")
        self.assertFalse((self.parent / "absent").exists())
        for path in ("https://example.invalid/state", "s3://bucket/state", "", b"bytes", "bad\0path"):
            with self.subTest(path=path), self.assertRaises((ValueError, TypeError)):
                source.inspect_checkpoint(path)

    def test_partial_blob_failure_is_preserved_and_not_resumable(self):
        def fail(stream):
            stream.write(b"partial blob evidence")
            raise OSError("synthetic interrupted writer")

        with self.assertRaisesRegex(OSError, "interrupted writer"):
            byte_bundle(self.destination, writer=fail)
        self.assertEqual((self.destination / source.BLOB_NAME).read_bytes(), b"partial blob evidence")
        self.assertFalse((self.destination / source.MANIFEST_NAME).exists())
        with self.assertRaises(FileNotFoundError):
            source.inspect_checkpoint(self.destination)
        with self.assertRaises(FileExistsError):
            byte_bundle(self.destination)

    def test_manifest_or_commit_failure_keeps_partial_bytes(self):
        original = source._write_exclusive
        for filename in (source.MANIFEST_NAME, source.COMMIT_NAME):
            destination = self.parent / filename

            def interrupted(directory_fd, name, writer, limit):
                if name != filename:
                    return original(directory_fd, name, writer, limit)

                def partial(stream):
                    stream.write(b"partial")
                    raise OSError("synthetic interrupted metadata")

                return original(directory_fd, name, partial, limit)

            with self.subTest(filename=filename), patch.object(source, "_write_exclusive", interrupted):
                with self.assertRaisesRegex(OSError, "interrupted metadata"):
                    byte_bundle(destination)
            self.assertEqual((destination / filename).read_bytes(), b"partial")
            self.assertEqual((destination / source.BLOB_NAME).read_bytes(), BYTE_FIXTURE)
            with self.assertRaises((ValueError, FileNotFoundError)):
                source.inspect_checkpoint(destination)

    def test_fsync_failure_propagates_without_removing_blob(self):
        original = os.fsync
        calls = 0

        def fail_second(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic fsync failure")
            return original(descriptor)

        with patch.object(source.os, "fsync", fail_second), self.assertRaisesRegex(OSError, "fsync failure"):
            byte_bundle(self.destination)
        self.assertEqual((self.destination / source.BLOB_NAME).read_bytes(), BYTE_FIXTURE)
        self.assertFalse((self.destination / source.COMMIT_NAME).exists())

    def test_manifest_collision_is_exclusive_even_inside_new_directory(self):
        def colliding_writer(stream):
            (self.destination / source.MANIFEST_NAME).write_bytes(b"preexisting collision evidence")
            stream.write(BYTE_FIXTURE)

        with self.assertRaises(FileExistsError):
            byte_bundle(self.destination, writer=colliding_writer)
        self.assertEqual((self.destination / source.MANIFEST_NAME).read_bytes(), b"preexisting collision evidence")
        self.assertEqual((self.destination / source.BLOB_NAME).read_bytes(), BYTE_FIXTURE)
        self.assertFalse((self.destination / source.COMMIT_NAME).exists())

    def test_bounded_write_preserves_prior_chunks(self):
        def oversized(stream):
            stream.write(b"1234")
            stream.write(b"56789")

        with self.assertRaisesRegex(ValueError, "blob_limit"):
            byte_bundle(self.destination, writer=oversized, limit=8)
        self.assertEqual((self.destination / source.BLOB_NAME).read_bytes(), b"1234")
        for limit in (0, -1, True, 1.0):
            with self.assertRaises(ValueError):
                source.inspect_checkpoint(self.destination, max_blob_bytes=limit)

    def test_tampered_truncated_appended_or_empty_blob_rejected_before_torch(self):
        byte_bundle(self.destination)
        for raw in (b"!" + BYTE_FIXTURE[1:], BYTE_FIXTURE[:-1], BYTE_FIXTURE + b"x", b""):
            (self.destination / source.BLOB_NAME).write_bytes(raw)
            with patch.object(source, "_torch", side_effect=AssertionError("must verify before importing torch")):
                with self.assertRaises(ValueError):
                    source.load_checkpoint(self.destination)

    def test_commit_digest_and_bounded_manifest_checked_before_blob(self):
        byte_bundle(self.destination)
        manifest = self.destination / source.MANIFEST_NAME
        manifest.write_bytes(manifest.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "commit_digest"):
            source.inspect_checkpoint(self.destination)
        manifest.write_bytes(b"x" * (source.MAX_MANIFEST_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "bounded_file"):
            source.inspect_checkpoint(self.destination)

    def test_closed_manifest_schema_rejects_forged_metadata(self):
        original = byte_bundle(self.destination)
        variants = []
        for key, value in (("format", "other"), ("state_sha256", "bad"), ("binding_sha256", "bad"),
                           ("cursor", 256), ("completed_updates", 256.0), ("extra", "not allowed")):
            variants.append({**original, key: value})
        variants.append({**original, "science_gates": {key: True for key in source.SCIENCE_GATES}})
        for blob in ({**original["blob"], "name": "../other.pt"}, {**original["blob"], "size_bytes": True},
                     {**original["blob"], "size_bytes": 10 ** 20}, {**original["blob"], "sha256": "BAD"}):
            variants.append({**original, "blob": blob})
        for variant in variants:
            rewrite_manifest(self.destination, source._json_bytes(variant))
            with self.assertRaises(ValueError):
                source.inspect_checkpoint(self.destination)

    def test_duplicate_noncanonical_nonfinite_and_nonascii_manifest_rejected(self):
        original = byte_bundle(self.destination)
        for raw in (b'{"format":1,"format":2}', b'{"number":NaN}', b'{"bad":"\xff"}', b"{",
                    json.dumps(original, indent=2).encode("ascii")):
            rewrite_manifest(self.destination, raw)
            with self.assertRaises(ValueError):
                source.inspect_checkpoint(self.destination)

    def test_symlink_directory_and_members_rejected_without_following(self):
        byte_bundle(self.destination)
        link = self.parent / "alias"
        link.symlink_to(self.destination, target_is_directory=True)
        with self.assertRaises(OSError):
            source.inspect_checkpoint(link)
        for filename in (source.COMMIT_NAME, source.MANIFEST_NAME, source.BLOB_NAME):
            destination = self.parent / (filename + "-bundle")
            byte_bundle(destination)
            member = destination / filename
            preserved = destination / (filename + ".preserved")
            member.rename(preserved)
            member.symlink_to(preserved)
            with self.subTest(filename=filename), self.assertRaises(OSError):
                source.inspect_checkpoint(destination)
            self.assertTrue(preserved.exists())

    def test_nonregular_blob_rejected_without_blocking(self):
        byte_bundle(self.destination)
        member = self.destination / source.BLOB_NAME
        member.rename(self.destination / "original-kept")
        os.mkfifo(member)
        with self.assertRaisesRegex(ValueError, "regular_nonempty"):
            source.inspect_checkpoint(self.destination)

    def test_read_limit_checked_before_torch_and_save_limit_before_directory_creation(self):
        byte_bundle(self.destination)
        with patch.object(source, "_torch", side_effect=AssertionError("must not import torch")):
            with self.assertRaisesRegex(ValueError, "blob_manifest"):
                source.load_checkpoint(self.destination, max_blob_bytes=len(BYTE_FIXTURE) - 1)
            with self.assertRaises(ValueError):
                source.save_checkpoint(self.parent / "not-created", {}, max_blob_bytes=False)
        self.assertFalse((self.parent / "not-created").exists())


def native_trainer(*, checkpoint=None):
    model = fixtures.tiny_native_model()
    roster = fixtures.planned_roster()
    return training.StatefulTrainer(
        model, arm="CLOSED", master=fixtures.MASTER, batches=fixtures.fixture(),
        trainable_roster=roster, layer_count=1, adapter_name="default",
        lineage_id="SYNTHETIC-DURABLE-CPU-CLOSED", preparation_sha256="a" * 64,
        initial_adapter_sha256=training.adapter_sha256(model, roster), checkpoint=checkpoint)


def _write_forbidden_marker(path):
    Path(path).write_text("UNSAFE REDUCER EXECUTED", encoding="ascii")


class _ForbiddenPayload:
    def __init__(self, marker):
        self.marker = str(marker)

    def __reduce__(self):
        return _write_forbidden_marker, (self.marker,)


def fresh_process_resume(input_directory, output_directory):
    import torch
    torch.set_num_threads(1)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "" or torch.cuda.is_initialized():
        raise AssertionError("fresh regression process must remain CPU-only")
    torch.serialization.clear_safe_globals()
    checkpoint = source.load_checkpoint(input_directory)
    trainer = native_trainer(checkpoint=checkpoint)
    expected_adapter = training._digest([(spec.name, training.tensor_sha256(checkpoint["adapter"][spec.name]))
                                        for spec in trainer.roster])
    if training.adapter_sha256(trainer.model, trainer.roster) != expected_adapter:
        raise AssertionError("restored adapter bytes differ")
    if training._tree_hash(trainer.optimizer.state_dict()) != training._tree_hash(checkpoint["optimizer"]):
        raise AssertionError("restored optimizer bytes differ")
    if trainer.completed_updates != 256 or trainer.cursor != 1024:
        raise AssertionError("restored D1 counters differ")
    if training._rng_hashes(training._rng_state()) != training._rng_hashes(checkpoint["rng"]):
        raise AssertionError("restored CPU/CUDA RNG bytes differ")
    trainer.train_stage("D2")
    final = trainer.checkpoint()
    source.save_checkpoint(output_directory, final)
    if torch.cuda.is_initialized():
        raise AssertionError("regression unexpectedly initialized CUDA")
    print(json.dumps(dict(restored_adapter_optimizer_cursor_rng=True, completed_updates=trainer.completed_updates,
                          cursor=trainer.cursor, state_sha256=final["sha256"], cuda_initialized=False), sort_keys=True))


@unittest.skipUnless(HAS_TORCH, "native torch absent on VM; durable tensor/subprocess tests not executed")
class Stage2ACheckpointNativeCPUTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls.torch = torch
        cls.original_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, cls.original_threads)
        if torch.cuda.is_initialized():
            raise AssertionError("run the tiny regression in a fresh CPU-only Python process")
        cls.d1_trainer = native_trainer()
        cls.d1_trainer.train_stage("D1")
        cls.d1 = cls.d1_trainer.checkpoint()

    def setUp(self):
        previous_globals = self.torch.serialization.get_safe_globals()

        def restore_globals():
            self.torch.serialization.clear_safe_globals()
            self.torch.serialization.add_safe_globals(previous_globals)

        self.addCleanup(restore_globals)
        self.torch.serialization.clear_safe_globals()
        self.temporary = tempfile.TemporaryDirectory(prefix="stage2a-native-checkpoint-test-")
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)

    def test_actual_cpu_tensor_roundtrip_preserves_types_bytes_and_rng(self):
        destination = self.parent / "d1"
        rng_before = training._rng_hashes(training._rng_state())
        manifest = source.save_checkpoint(destination, self.d1)
        loaded = source.load_checkpoint(destination)
        self.assertEqual(training._tree_hash(loaded), training._tree_hash(self.d1))
        self.assertEqual(manifest["state_sha256"], self.d1["sha256"])
        self.assertIs(type(loaded["rng"]["cuda"]), tuple)
        self.assertIs(type(loaded["optimizer"]["param_groups"][0]["betas"]), tuple)
        self.assertIs(type(loaded["optimizer"]["state"]), dict)
        self.assertEqual(training._rng_hashes(training._rng_state()), rng_before)
        self.assertTrue(all(value.device.type == "cpu" for value in loaded["adapter"].values()))
        self.assertFalse(any(manifest["science_gates"].values()))
        before = {path.name: path.read_bytes() for path in destination.iterdir()}
        with self.assertRaises(FileExistsError):
            source.save_checkpoint(destination, self.d1)
        self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()}, before)

    def test_fresh_process_restores_full_d1_and_d2_matches_uninterrupted(self):
        saved_d1, child_d2 = self.parent / "d1", self.parent / "child-d2"
        source.save_checkpoint(saved_d1, self.d1)
        self.d1_trainer.train_stage("D2")
        uninterrupted = self.d1_trainer.checkpoint()
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES="")
        process = subprocess.run(
            [sys.executable, "-m", "tests.test_composition_birth_stage2a_checkpoint",
             "--fresh-process-resume", str(saved_d1), str(child_d2)],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            check=False, capture_output=True, text=True, timeout=180)
        self.assertEqual(process.returncode, 0, "fresh-process failure\nstdout:\n" + process.stdout
                         + "\nstderr:\n" + process.stderr)
        receipt = json.loads(process.stdout)
        self.assertTrue(receipt["restored_adapter_optimizer_cursor_rng"])
        self.assertFalse(receipt["cuda_initialized"])
        self.assertEqual(receipt["completed_updates"], 512)
        self.assertEqual(receipt["cursor"], 2048)
        restored = source.load_checkpoint(child_d2)
        self.assertEqual(training._tree_hash(restored), training._tree_hash(uninterrupted))
        self.assertEqual(restored["sha256"], receipt["state_sha256"])
        self.assertTrue(all(state["step"].item() == 512 for state in restored["optimizer"]["state"].values()))
        self.assertEqual(self.d1_trainer.model.forward_calls, 512)

    def test_restricted_loader_rejects_reducer_without_executing_it(self):
        marker = self.parent / "unsafe-marker"
        payload = _ForbiddenPayload(marker)
        destination = self.parent / "unsafe-blob"
        source._publish(destination, source._metadata(self.d1), lambda stream: self.torch.save(payload, stream),
                        max_blob_bytes=source.DEFAULT_MAX_BLOB_BYTES)
        self.assertFalse(marker.exists())
        with self.assertRaises((pickle.UnpicklingError, RuntimeError, ValueError)):
            source.load_checkpoint(destination)
        self.assertFalse(marker.exists())
        self.assertTrue((destination / source.BLOB_NAME).exists())

    def test_save_rejects_custom_objects_before_reduction_or_directory_creation(self):
        checkpoint = training._tree_copy(self.d1)
        marker, destination = self.parent / "marker", self.parent / "not-created"
        checkpoint["receipts"][0]["forbidden"] = _ForbiddenPayload(marker)
        with self.assertRaisesRegex(ValueError, "unsupported_checkpoint_object"):
            source.save_checkpoint(destination, checkpoint)
        self.assertFalse(marker.exists())
        self.assertFalse(destination.exists())

    def test_state_digest_and_manifest_binding_checked_after_restricted_load(self):
        changed = training._tree_copy(self.d1)
        changed["adapter"][next(iter(changed["adapter"]))].add_(1)
        destination = self.parent / "state-digest"
        source._publish(destination, source._metadata(self.d1), lambda stream: self.torch.save(changed, stream),
                        max_blob_bytes=source.DEFAULT_MAX_BLOB_BYTES)
        with self.assertRaisesRegex(ValueError, "state_digest_mismatch"):
            source.load_checkpoint(destination)
        destination = self.parent / "manifest-binding"
        manifest = source.save_checkpoint(destination, self.d1)
        rewrite_manifest(destination, source._json_bytes({**manifest, "binding_sha256": "0" * 64}))
        with self.assertRaisesRegex(ValueError, "manifest_state_binding_mismatch"):
            source.load_checkpoint(destination)

    def test_ambient_safe_globals_are_rejected_not_changed(self):
        destination = self.parent / "d1"
        source.save_checkpoint(destination, self.d1)
        with self.torch.serialization.safe_globals([_write_forbidden_marker]):
            before = self.torch.serialization.get_safe_globals()
            with self.assertRaisesRegex(ValueError, "ambient_safe_globals"):
                source.load_checkpoint(destination)
            self.assertEqual(self.torch.serialization.get_safe_globals(), before)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--fresh-process-resume":
        fresh_process_resume(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
