"""Bounded fakes only: no model/tokenizer construction, real torch, or GPU jobs.

Screen dispatch, custody, checkpoint file integrity and reduction use their
existing CPU implementations. Trainer updates and tensor bytes are explicit
fakes; checkpoint payloads are Python literals, NOT native torch checkpoints.
Nothing here provides fresh-process/native reload or persistence evidence.
"""

import ast
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_reduced_conductor as source
from organism_v6 import composition_birth_stage2a_rollout as rollout
from tests import test_composition_birth_stage2a_screen_runtime as screen_fixtures


def fake_tensor_hash(value):
    return sha256(value.encode("ascii")).hexdigest()


class FakeTorch:
    class Tensor:
        pass

    serialization = SimpleNamespace(get_safe_globals=lambda: [])

    @staticmethod
    def save(value, stream):
        stream.write(repr(value).encode("ascii"))

    @staticmethod
    def load(stream, *, weights_only, map_location):
        if weights_only is not True or map_location != "cpu":
            raise AssertionError("unsafe fake checkpoint load")
        return ast.literal_eval(stream.read().decode("ascii"))


class FakeModel:
    def __init__(self):
        self.adapter = "fake-initial-adapter"

    def named_parameters(self):
        return (("fake.lora_A", self.adapter),)


class PreparedFakeActor(screen_fixtures.FakeActor):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.native_output = {"synthetic_only": True}

    def count_context(self, prefix):
        return 10


class PreparedFakeTrainer:
    def __init__(self, model, log):
        self.model, self.log = model, log
        self.arm, self.completed_updates, self.cursor = "ATOM_LOCAL", 0, 0
        self.batches = ("caller-prepared-fake-batches",)
        self.roster = (source.training.ParameterSpec("fake.lora_A", (8, 1), "float32"),)
        self.binding = dict(
            arm=self.arm, lineage_id="fake-lineage", preparation_sha256="a" * 64,
            initial_adapter_sha256=source.training.adapter_sha256(model, self.roster),
            batches_sha256="b" * 64, roster=[asdict(spec) for spec in self.roster],
            recipe=dict(source.training.RECIPE), torch_version="FAKE", device="FAKE",
        )
        self.receipts = []

    def train_stage(self, stage):
        self.log.append(("train", stage))
        if (stage, self.completed_updates) != ("D1", 0):
            raise AssertionError("no D2, CLOSED, repeated training or retries")
        self.completed_updates, self.cursor = 256, 1024
        self.model.adapter = "fake-d1-adapter"
        self.receipts = [{"fake_update": update} for update in range(1, 257)]
        return self.receipts

    def checkpoint(self):
        self.log.append(("checkpoint", "D1"))
        state = dict(
            format="stage2a-state-v1", binding=deepcopy(self.binding),
            completed_updates=self.completed_updates, cursor=self.cursor,
            adapter={"fake.lora_A": self.model.adapter},
            optimizer={"state": {0: {"step": 256, "exp_avg": "fake-moment",
                                       "exp_avg_sq": "fake-second-moment"}},
                       "param_groups": [{"params": [0]}]},
            rng={"cpu": "fake-boundary-rng", "cuda": ()}, receipts=deepcopy(self.receipts),
        )
        state["sha256"] = source.training._digest(source.training._tree_hash(state))
        return state


class ReducedConductorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        screen_fixtures.ScreenRuntimeTests.setUpClass()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fake-reduced-conductor-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.log = []
        self.add_patch(source.training, "_torch", return_value=FakeTorch)
        self.add_patch(source.checkpoint_api, "_torch", return_value=FakeTorch)
        self.add_patch(source.training, "tensor_sha256", side_effect=fake_tensor_hash)
        self.batch_check = self.add_patch(source.training, "validate_batches", return_value="b" * 64)
        self.base = PreparedFakeActor(FakeModel())
        self.atom = PreparedFakeActor(FakeModel())
        self.trainer = PreparedFakeTrainer(self.atom.model, self.log)
        held = screen_fixtures.ScreenRuntimeTests
        self.options = dict(
            base_state_id="fake-BASE-attempt-1", atom_local_state_id="fake-ATOM_LOCAL-attempt-1",
            base_actor=self.base, atom_local_actor=self.atom, trainer=self.trainer,
            trainer_binding=deepcopy(self.trainer.binding), batches=self.trainer.batches,
            master=b"synthetic-reduced-screen", chains=held.chains,
            interventions=held.interventions, canaries=held.canaries,
            counter_provenance="FAKE_COUNTER_NOT_NATIVE_EVIDENCE",
            base_custody_dir=self.root / "base", atom_custody_dir=self.root / "atom",
            checkpoint_dir=self.root / "checkpoint", torch=FakeTorch,
        )
        self.dispatch = self.trace(source.runtime, "run_reduced_state", lambda options: options["state_id"])
        self.verify = self.trace(source.custody, "verify_receipt")
        self.save = self.trace(source.checkpoint_api, "save_checkpoint")
        self.inspect = self.trace(source.checkpoint_api, "inspect_checkpoint")
        self.load = self.trace(source.checkpoint_api, "load_checkpoint")
        self.reduce = self.trace(source.reducer, "reduce_base_d1")

    def add_patch(self, target, name, **options):
        patcher = patch.object(target, name, **options)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def trace(self, target, name, detail=None):
        original = getattr(target, name)

        def traced(*args, **kwargs):
            self.log.append((name, detail(kwargs) if detail else None))
            return original(*args, **kwargs)

        return self.add_patch(target, name, side_effect=traced)

    def run_fixture(self, **changes):
        self.last_options = self.options | changes
        return source.run_reduced_conductor(**self.last_options)

    def assert_stopped(self, result, screen_count, trained):
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertTrue(result.failures)
        self.assertEqual(self.dispatch.call_count, screen_count)
        self.assertEqual(sum(event[0] == "train" for event in self.log), int(trained))
        self.reduce.assert_not_called()
        self.assertIs(result.inputs["trainer"], self.trainer)
        self.assertIs(result.inputs["base_actor"], self.last_options["base_actor"])
        self.assertIs(result.inputs["atom_local_actor"], self.last_options["atom_local_actor"])

    def test_exact_join_all_misses_are_data_not_a_performance_veto(self):
        result = self.run_fixture()
        self.assertEqual(result.failures, [])
        self.assertEqual(result.terminal_reason, "reduced")
        self.assertEqual(self.log, [
            ("run_reduced_state", self.options["base_state_id"]), ("verify_receipt", None),
            ("train", "D1"), ("checkpoint", "D1"), ("save_checkpoint", None),
            ("inspect_checkpoint", None), ("load_checkpoint", None),
            ("run_reduced_state", self.options["atom_local_state_id"]),
            ("verify_receipt", None), ("reduce_base_d1", None),
            ("run_reduced_state", self.options["base_state_id"]),
            ("run_reduced_state", self.options["atom_local_state_id"]),
        ])
        self.assertEqual(len(self.base.calls), 56)
        self.assertEqual(len(self.atom.calls), 56)
        self.assertTrue(all(call.kwargs["actor"] not in (self.base, self.atom)
                            for call in self.dispatch.call_args_list[2:]))
        self.assertEqual([len(run.reservations) for run in result.screens.values()], [280, 280])
        self.assertTrue(result.reduction.reportable)
        self.assertFalse(result.reduction.criteria_passed)
        self.assertEqual(result.reduction.atom_local.metrics.whole_chains, 0)
        self.assertIs(result.reduction.base.run, result.screens["BASE"])
        self.assertIs(result.reduction.atom_local.run, result.screens["ATOM_LOCAL"])
        self.assertIs(result.training_receipts, self.trainer.receipts)
        self.assertEqual(result.checkpoint, result.loaded_checkpoint)
        self.assertIsNot(result.checkpoint, result.loaded_checkpoint)
        self.assertEqual(set(result.checkpoint), {"format", "binding", "completed_updates", "cursor",
                                                "adapter", "optimizer", "rng", "receipts", "sha256"})
        self.assertEqual(result.hashes["d1_adapter"], result.hashes["ATOM_LOCAL_atom_before"])
        self.assertEqual(result.hashes["d1_adapter"], result.hashes["ATOM_LOCAL_atom_after"])
        self.assertEqual(result.hashes["d1_checkpoint"], result.inspected_manifest["state_sha256"])
        self.assertEqual(result.hashes["initial_atom_adapter"], result.hashes["BASE_atom_after"])
        self.assertNotEqual(result.hashes["d1_adapter"], result.hashes["initial_atom_adapter"])
        self.assertFalse(hasattr(result, "admitted"))
        self.assertFalse(hasattr(result, "native_authorized"))
        self.assertFalse(hasattr(result, "fresh_process_persistence"))
        self.assertIn("NOT evidence", source.__doc__)
        self.assertIn("fresh-process", source.run_reduced_conductor.__doc__)
        for label, receipt in result.receipts.items():
            self.assertEqual(receipt.state_id, result.screens[label].state_id)
            self.assertEqual(result.sinks[label].status, "complete")
            self.assertIsNone(result.sinks[label]._fd)
        self.batch_check.assert_called_once_with(self.trainer.batches, master=self.options["master"])
        for dispatch, actor in zip(self.dispatch.call_args_list, (self.base, self.atom)):
            self.assertEqual(dispatch.kwargs["stage"], "D1")
            self.assertIs(dispatch.kwargs["actor"], actor)
            self.assertIs(dispatch.kwargs["actor_calls"], actor.calls)
            self.assertEqual(dispatch.kwargs["count_context"], actor.count_context)
            for key in ("master", "chains", "interventions", "canaries"):
                self.assertIs(dispatch.kwargs[key], self.options[key])

    def test_preexisting_artifacts_rejected_without_overwrite_or_calls(self):
        directory = self.options["checkpoint_dir"]
        directory.mkdir()
        marker = directory / "keep"
        marker.write_bytes(b"original evidence")
        result = self.run_fixture()
        self.assert_stopped(result, 0, False)
        self.assertEqual(marker.read_bytes(), b"original evidence")
        self.assertFalse(self.options["base_custody_dir"].exists())

    def test_malformed_and_length_limited_generations_remain_numeric_data(self):
        self.base.policy = lambda request: rollout.Generation("not an action", 1, 1, False, "stop")
        self.atom.policy = lambda request: rollout.Generation("not an action", 1, 1, False, "length")
        result = self.run_fixture()
        self.assertEqual(result.failures, [])
        self.assertEqual(result.terminal_reason, "reduced")
        self.assertTrue(result.reduction.reportable)
        self.assertFalse(result.reduction.criteria_passed)
        self.assertEqual(len(self.base.calls), 56)
        self.assertEqual(len(self.atom.calls), 56)
        self.assertEqual(sum(event[0] == "train" for event in self.log), 1)

    def test_actor_and_input_binding_rejections_precede_callbacks(self):
        changes = [
            {"atom_local_state_id": self.options["base_state_id"]},
            {"base_actor": self.atom},
            {"atom_local_actor": PreparedFakeActor(FakeModel())},
            {"batches": ("different",)},
            {"trainer_binding": self.options["trainer_binding"] | {"preparation_sha256": "c" * 64}},
            {"atom_custody_dir": self.options["base_custody_dir"]},
            {"checkpoint_dir": self.options["base_custody_dir"] / "nested"},
        ]
        for change in changes:
            with self.subTest(change=tuple(change)):
                self.assert_stopped(self.run_fixture(**change), 0, False)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_closed_and_resumed_trainers_rejected(self):
        self.trainer.arm = "CLOSED"
        self.assert_stopped(self.run_fixture(), 0, False)
        self.trainer.arm = "ATOM_LOCAL"
        self.trainer.completed_updates = 256
        self.assert_stopped(self.run_fixture(), 0, False)

    def test_batch_master_or_initial_adapter_drift_rejected(self):
        self.batch_check.return_value = "d" * 64
        self.assert_stopped(self.run_fixture(), 0, False)
        self.batch_check.return_value = "b" * 64
        self.atom.model.adapter = "out-of-band-edit"
        self.assert_stopped(self.run_fixture(), 0, False)

    def test_base_actor_failure_retains_live_exception_and_custody(self):
        error = RuntimeError("fake actor fault")

        def fail(request):
            raise error

        self.base.policy = fail
        result = self.run_fixture()
        self.assert_stopped(result, 1, False)
        self.assertTrue(any(fault.error is error for fault in result.failures))
        self.assertIs(result.screens["BASE"].calls[0].actor_error, error)
        self.assertIs(result.screens["BASE"].calls[0].native_records[0], self.base.calls[0])
        self.assertTrue((self.options["base_custody_dir"] / "COMPLETE").is_file())
        self.assertEqual(result.receipts["BASE"].terminal_reason, "aborted")
        self.assertEqual(len(self.base.calls), 1)
        self.assertEqual(self.atom.calls, [])

    def test_unsupported_custody_retains_partial_files_and_live_objects(self):
        unsupported = object()
        self.base.native_output = unsupported
        result = self.run_fixture()
        self.assert_stopped(result, 1, False)
        self.assertIs(result.screens["BASE"].calls[0].native_records[0]["native_output"], unsupported)
        self.assertEqual(result.sinks["BASE"].status, "incomplete")
        self.assertTrue(list(self.options["base_custody_dir"].iterdir()))
        self.assertFalse((self.options["base_custody_dir"] / "COMPLETE").exists())
        self.assertEqual(len(self.base.calls), 1)

    def test_receipt_identity_mismatch_prevents_training(self):
        original = self.verify.side_effect
        self.verify.side_effect = lambda *args, **kwargs: replace(
            original(*args, **kwargs), state_id="different-state")
        result = self.run_fixture()
        self.assert_stopped(result, 1, False)
        self.assertEqual(result.receipts["BASE"].state_id, "different-state")

    def test_base_readout_must_not_mutate_prepared_atom_state(self):
        def mutate(request):
            self.atom.model.adapter = "changed-by-base"
            return rollout.Generation("STOP", 1, 1, False, "stop")

        self.base.policy = mutate
        result = self.run_fixture()
        self.assert_stopped(result, 1, False)
        self.assertIn("adapter_changed_during_readout", str(result.failures[-1].error))
        self.assertEqual(len(result.screens["BASE"].reservations), 280)

    def test_training_interruption_preserved_without_checkpoint_or_retry(self):
        error = KeyboardInterrupt("fake interruption")

        def fail(stage):
            self.log.append(("train", stage))
            self.trainer.completed_updates = 3
            self.trainer.receipts.append({"partial": True})
            raise error

        self.trainer.train_stage = fail
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIs(result.failures[0].error, error)
        self.assertEqual(result.inputs["trainer"].receipts, [{"partial": True}])
        self.save.assert_not_called()
        self.assertIsNone(result.checkpoint)

    def test_wrong_update_count_prevents_checkpoint(self):
        original = self.trainer.train_stage

        def short(stage):
            receipts = original(stage)
            self.trainer.completed_updates = 255
            return receipts

        self.trainer.train_stage = short
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIn("exact_d1_256_updates", str(result.failures[0].error))
        self.save.assert_not_called()

    def test_checkpoint_live_adapter_mismatch_prevents_storage_and_eval(self):
        original = self.trainer.checkpoint

        def wrong_checkpoint():
            state = original()
            state["adapter"]["fake.lora_A"] = "wrong-adapter"
            return state

        self.trainer.checkpoint = wrong_checkpoint
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIn("checkpoint_live_adapter_mismatch", str(result.failures[0].error))
        self.assertIsNotNone(result.checkpoint)
        self.save.assert_not_called()

    def test_partial_checkpoint_write_preserves_full_live_state_and_files(self):
        error = OSError("fake storage exhaustion")

        def partial(value, stream):
            stream.write(b"fake partial checkpoint bytes")
            raise error

        with patch.object(FakeTorch, "save", side_effect=partial):
            result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIs(result.failures[0].error, error)
        self.assertEqual(result.checkpoint["completed_updates"], 256)
        self.assertEqual(len(result.checkpoint["receipts"]), 256)
        self.assertTrue(list(self.options["checkpoint_dir"].iterdir()))
        self.assertFalse((self.options["checkpoint_dir"] / source.checkpoint_api.COMMIT_NAME).exists())
        self.assertTrue((self.options["base_custody_dir"] / "COMPLETE").exists())
        self.inspect.assert_not_called()
        self.load.assert_not_called()

    def test_corrupt_checkpoint_load_is_not_retried(self):
        original = self.inspect.side_effect

        def corrupt(path):
            manifest = original(path)
            blob = Path(path) / source.checkpoint_api.BLOB_NAME
            with blob.open("ab") as stream:
                stream.write(b"fake corruption")
            return manifest

        self.inspect.side_effect = corrupt
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.load.assert_called_once()
        self.assertIsNotNone(result.saved_manifest)
        self.assertIsNotNone(result.inspected_manifest)
        self.assertIsNone(result.loaded_checkpoint)
        self.assertIn(b"fake corruption", (self.options["checkpoint_dir"] / source.checkpoint_api.BLOB_NAME).read_bytes())

    def test_loaded_state_binding_mismatch_prevents_atom_readout(self):
        original = self.load.side_effect

        def changed(path):
            state = original(path)
            state["binding"]["lineage_id"] = "another-lineage"
            return state

        self.load.side_effect = changed
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertEqual(result.loaded_checkpoint["binding"]["lineage_id"], "another-lineage")
        self.assertIn("full_checkpoint_roundtrip_binding_mismatch", str(result.failures[0].error))

    def test_loaded_adapter_binding_mismatch_is_retained(self):
        original = self.load.side_effect

        def changed(path):
            state = original(path)
            state["adapter"]["fake.lora_A"] = "different-loaded-adapter"
            return state

        self.load.side_effect = changed
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIn("checkpoint_adapter_roundtrip_mismatch", str(result.failures[0].error))
        self.assertEqual(result.loaded_checkpoint["adapter"]["fake.lora_A"], "different-loaded-adapter")

    def test_atom_adapter_drift_after_load_prevents_evaluation(self):
        original = self.load.side_effect

        def drift(path):
            state = original(path)
            self.atom.model.adapter = "changed-after-checkpoint"
            return state

        self.load.side_effect = drift
        result = self.run_fixture()
        self.assert_stopped(result, 1, True)
        self.assertIn("adapter_changed_before_readout", str(result.failures[0].error))
        self.assertIsNotNone(result.loaded_checkpoint)

    def test_atom_readout_mutation_retains_run_but_prevents_reduction(self):
        def mutate(request):
            self.atom.model.adapter = "changed-during-readout"
            return rollout.Generation("STOP", 1, 1, False, "stop")

        self.atom.policy = mutate
        result = self.run_fixture()
        self.assert_stopped(result, 2, True)
        self.assertEqual(len(result.screens["ATOM_LOCAL"].reservations), 280)
        self.assertIn("adapter_changed_during_readout", str(result.failures[0].error))
        self.assertTrue((self.options["atom_custody_dir"] / "COMPLETE").exists())
        self.assertIsNotNone(result.loaded_checkpoint)

    def test_atom_failure_preserves_both_screens_and_checkpoint(self):
        error = RuntimeError("fake atom failure")

        def fail(request):
            raise error

        self.atom.policy = fail
        result = self.run_fixture()
        self.assert_stopped(result, 2, True)
        self.assertTrue(any(fault.error is error for fault in result.failures))
        self.assertEqual(len(self.atom.calls), 1)
        self.assertEqual(set(result.screens), {"BASE", "ATOM_LOCAL"})
        self.assertIsNotNone(result.loaded_checkpoint)

    def test_sink_close_error_blocks_next_stage_without_masking_original(self):
        error = OSError("fake close failure")
        actor_error = RuntimeError("fake original actor failure")
        original = source.custody.ScreenCustodySink.close

        def fail_actor(request):
            raise actor_error

        def fail_close(sink):
            original(sink)
            raise error

        self.base.policy = fail_actor
        with patch.object(source.custody.ScreenCustodySink, "close", fail_close):
            result = self.run_fixture()
        self.assert_stopped(result, 1, False)
        self.assertIs(result.failures[-1].error, error)
        self.assertEqual(result.failures[-1].phase, "BASE.close")
        self.assertTrue(any(fault.error is actor_error for fault in result.failures))

    def test_reducer_error_preserves_all_evidence_without_retry(self):
        error = RuntimeError("fake reducer failure")
        self.reduce.side_effect = error
        result = self.run_fixture()
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertEqual(result.failures, [source.ConductorFailure("reduce", error)])
        self.assertEqual(set(result.screens), {"BASE", "ATOM_LOCAL"})
        self.assertEqual(set(result.receipts), {"BASE", "ATOM_LOCAL"})
        self.assertIsNotNone(result.loaded_checkpoint)
        self.reduce.assert_called_once()
        self.assertEqual(len(self.atom.calls), 56)

    def test_import_is_lazy_and_does_not_dispatch_native_work(self):
        spec = importlib.util.spec_from_file_location("fake_conductor_import_only", source.__file__)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {spec.name: module, "torch": None, "transformers": None, "peft": None}):
            spec.loader.exec_module(module)
        self.dispatch.assert_not_called()
        self.save.assert_not_called()
        self.assertEqual(self.log, [])


if __name__ == "__main__":
    unittest.main()
