"""Synthetic glue regression only: no native model/tokenizer, torch or GPU.

Checkpoint/custody filesystem and D2 dispatch are real existing mechanisms;
trainer updates and tensor serialization are explicitly fake. These tests do
not qualify numerical continuity, launch eligibility or native persistence.
"""

from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_d2_resume as source
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from tests import test_astra_stage2a_reduced_conductor as fixtures
from tests import test_composition_birth_stage2a_screen_runtime as screen_fixtures


class FakeRestoredTrainer:
    def __init__(self, model, *, checkpoint, **options):
        self.model, self.batches = model, options["batches"]
        self.arm, self.roster = options["arm"], options["trainable_roster"]
        self.state = deepcopy(checkpoint)
        self.binding = self.state["binding"]
        self.completed_updates, self.cursor = self.state["completed_updates"], self.state["cursor"]
        self.receipts = self.state["receipts"]
        self.optimizer, self.rng = self.state["optimizer"], self.state["rng"]
        self.model.adapter = self.state["adapter"]["fake.lora_A"]
        self.stage_calls, self.executed_updates = [], []
        self.error = None

    def checkpoint(self):
        self.state.update(completed_updates=self.completed_updates, cursor=self.cursor,
                          adapter={"fake.lora_A": self.model.adapter})
        self.state["sha256"] = source.training._digest(source.training._tree_hash(
            {key: value for key, value in self.state.items() if key != "sha256"}))
        return deepcopy(self.state)

    def train_stage(self, stage):
        self.stage_calls.append(stage)
        if (stage, self.completed_updates, self.cursor) != ("D2", 256, 1024):
            raise AssertionError("synthetic fixture permits only D1-to-D2 continuation")
        if self.optimizer["state"][0]["step"] != 256 or len(self.receipts) != 256:
            raise AssertionError("full optimizer/history must be restored")
        for update in range(257, 513):
            self.completed_updates, self.cursor = update, update * 4
            self.executed_updates.append(update)
            self.receipts.append({"fake_update": update})
            self.optimizer["state"][0].update(step=update, exp_avg=f"fake-moment-{update}",
                                             exp_avg_sq=f"fake-second-moment-{update}")
            self.rng["cpu"] = f"fake-rng-{update}"
            self.model.adapter = f"fake-adapter-{update}"
            if self.error is not None:
                raise self.error
        return deepcopy(self.receipts[-256:])


class D2ResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        screen_fixtures.ScreenRuntimeTests.setUpClass()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-d2-resume-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.add_patch(source.training, "_torch", return_value=fixtures.FakeTorch)
        self.add_patch(source.checkpoint_api, "_torch", return_value=fixtures.FakeTorch)
        self.add_patch(source.training, "tensor_sha256", side_effect=fixtures.fake_tensor_hash)
        prepared = fixtures.PreparedFakeTrainer(fixtures.FakeModel(), [])
        prepared.train_stage("D1")
        self.d1 = prepared.checkpoint()
        self.d1_dir = self.root / "d1"
        source.checkpoint_api.save_checkpoint(self.d1_dir, self.d1)
        self.d1_bytes = {path.name: path.read_bytes() for path in self.d1_dir.iterdir()}
        self.model = fixtures.FakeModel()
        self.actor = fixtures.PreparedFakeActor(self.model)
        held = screen_fixtures.ScreenRuntimeTests
        self.options = dict(
            model=self.model, atom_local_actor=self.actor,
            trainer_options=dict(arm="ATOM_LOCAL", master=b"synthetic-reduced-screen",
                                 batches=prepared.batches, trainable_roster=prepared.roster,
                                 layer_count=1, adapter_name="fake",
                                 lineage_id=prepared.binding["lineage_id"],
                                 preparation_sha256=prepared.binding["preparation_sha256"],
                                 initial_adapter_sha256=prepared.binding["initial_adapter_sha256"]),
            trainer_binding=deepcopy(prepared.binding), d1_checkpoint_dir=self.d1_dir,
            d1_checkpoint_sha256=self.d1["sha256"], checkpoint_dir=self.root / "d2",
            atom_custody_dir=self.root / "atom-d2", atom_local_state_id="fake-ATOM-D2-attempt-1",
            base_state_id="prior-bound-BASE", base_evidence=object(),
            master=b"synthetic-reduced-screen", chains=held.chains,
            interventions=held.interventions, canaries=held.canaries,
            counter_provenance="FAKE_COUNTER_NOT_NATIVE_EVIDENCE", torch=fixtures.FakeTorch,
        )
        self.restore = self.add_patch(source.training, "StatefulTrainer", side_effect=FakeRestoredTrainer)
        self.dispatch = self.add_patch(source.runtime, "run_reduced_state", wraps=source.runtime.run_reduced_state)
        self.save = self.add_patch(source.checkpoint_api, "save_checkpoint", wraps=source.checkpoint_api.save_checkpoint)
        self.reduce = self.add_patch(reducer, "reduce_base_d1", side_effect=AssertionError("D1 reducer must not run"))

    def add_patch(self, target, name, **options):
        patcher = patch.object(target, name, **options)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def run_fixture(self, **changes):
        return source.run_d2_resume(**(self.options | changes))

    def assert_d1_preserved(self):
        self.assertEqual({path.name: path.read_bytes() for path in self.d1_dir.iterdir()}, self.d1_bytes)

    def assert_aborted(self, result, phase):
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertTrue(any(fault.phase == phase for fault in result.failures))
        self.assertIsNone(result.reduction)
        self.assertIs(result.inputs["base_evidence"], self.options["base_evidence"])
        self.reduce.assert_not_called()

    def test_resume_restores_full_state_and_only_executes_257_through_512(self):
        result = self.run_fixture()
        self.assertEqual(result.failures, [])
        self.assertEqual(result.terminal_reason, "completed_unreduced")
        self.restore.assert_called_once()
        self.assertIs(self.restore.call_args.args[0], self.model)
        self.assertEqual(self.restore.call_args.kwargs["checkpoint"], self.d1)
        self.assertEqual(result.restored_checkpoint, self.d1)
        self.assertEqual(result.trainer.stage_calls, ["D2"])
        self.assertEqual(result.trainer.executed_updates, list(range(257, 513)))
        self.assertEqual(result.checkpoint["receipts"][:256], self.d1["receipts"])
        self.assertEqual(len(result.training_receipts), 256)
        self.assertEqual((result.checkpoint["completed_updates"], result.checkpoint["cursor"]), (512, 2048))
        self.assertEqual(result.checkpoint["optimizer"]["state"][0]["step"], 512)
        self.assertEqual(result.checkpoint["rng"]["cpu"], "fake-rng-512")
        self.assertEqual(result.checkpoint, result.loaded_checkpoint)
        self.assertEqual(result.saved_manifest, result.inspected_manifest)
        self.assertEqual(result.hashes["d2_checkpoint"], result.saved_manifest["state_sha256"])
        self.assertIsNot(result.checkpoint, result.loaded_checkpoint)
        self.assertEqual(result.trainer.binding, self.options["trainer_binding"])
        self.assertEqual(self.model.adapter, "fake-adapter-512")
        self.save.assert_called_once()
        self.assert_d1_preserved()

    def test_existing_d2_roster_and_seeds_only_no_base_or_automatic_promotion(self):
        result = self.run_fixture()
        self.dispatch.assert_called_once()
        self.assertEqual(self.dispatch.call_args.kwargs["stage"], "D2")
        run = result.screens["ATOM_LOCAL"]
        self.assertEqual(tuple(row.entry for row in run.reservations), source.screen.reduced_screen("D2"))
        self.assertEqual(tuple(row.seed for row in run.reservations),
                         source.screen.reduced_decode_seeds("D2", master=self.options["master"]))
        self.assertEqual(len(run.reservations), 280)
        self.assertEqual(len(self.actor.calls), 56)
        self.assertEqual(set(result.screens), {"ATOM_LOCAL"})
        self.assertEqual(result.receipts["ATOM_LOCAL"].stage, "D2")
        self.assertIs(result.inputs["base_evidence"], self.options["base_evidence"])
        self.assertIsNone(result.reduction)
        self.assertEqual(result.remaining_seams, source.REMAINING_SEAMS)
        for name in ("eligible", "admitted", "criteria_passed", "promoted"):
            self.assertFalse(hasattr(result, name))
        self.reduce.assert_not_called()

    def test_wrong_d1_hash_or_binding_fails_before_restore(self):
        changes = ({"d1_checkpoint_sha256": "0" * 64},
                   {"trainer_binding": self.options["trainer_binding"] | {"lineage_id": "foreign"}})
        for change in changes:
            with self.subTest(change=change):
                self.assert_aborted(self.run_fixture(**change), "load_D1")
        self.restore.assert_not_called()
        self.dispatch.assert_not_called()
        self.save.assert_not_called()
        self.assert_d1_preserved()

    def test_d2_checkpoint_cannot_be_continued_again(self):
        completed = self.run_fixture()
        self.restore.reset_mock()
        self.dispatch.reset_mock()
        result = self.run_fixture(d1_checkpoint_dir=self.options["checkpoint_dir"],
                                  d1_checkpoint_sha256=completed.checkpoint["sha256"],
                                  checkpoint_dir=self.root / "forbidden-d3",
                                  atom_custody_dir=self.root / "forbidden-d3-custody")
        self.assert_aborted(result, "load_D1")
        self.restore.assert_not_called()
        self.dispatch.assert_not_called()

    def test_preflight_actor_master_arm_paths_and_held_binding_errors_do_not_restore(self):
        cases = (
            {"atom_local_actor": fixtures.PreparedFakeActor(fixtures.FakeModel())},
            {"master": b"different"},
            {"trainer_options": self.options["trainer_options"] | {"arm": "CLOSED"}},
            {"trainer_options": self.options["trainer_options"] | {"checkpoint": self.d1}},
            {"checkpoint_dir": self.d1_dir},
            {"checkpoint_dir": self.d1_dir / "nested"},
            {"checkpoint_dir": self.root / "missing" / "parent"},
            {"atom_custody_dir": self.options["checkpoint_dir"]},
            {"atom_local_state_id": self.options["base_state_id"]},
            {"chains": {}},
        )
        for change in cases:
            with self.subTest(change=tuple(change)):
                self.assert_aborted(self.run_fixture(**change), "bindings")
        self.restore.assert_not_called()
        self.dispatch.assert_not_called()
        self.save.assert_not_called()
        self.assert_d1_preserved()

    def test_existing_failed_output_is_never_overwritten(self):
        directory = self.options["checkpoint_dir"]
        directory.mkdir()
        marker = directory / "failed-attempt"
        marker.write_bytes(b"preserve")
        self.assert_aborted(self.run_fixture(), "bindings")
        self.assertEqual(marker.read_bytes(), b"preserve")
        self.restore.assert_not_called()

    def test_incomplete_or_corrupt_d1_fails_before_restore(self):
        blob = self.d1_dir / source.checkpoint_api.BLOB_NAME
        with blob.open("ab") as stream:
            stream.write(b"corrupt")
        self.assert_aborted(self.run_fixture(), "load_D1")
        self.restore.assert_not_called()
        self.assertTrue(blob.read_bytes().endswith(b"corrupt"))

    def test_restore_error_preserves_original_exception_and_model(self):
        error = ValueError("synthetic optimizer/RNG validation failure")
        self.restore.side_effect = error
        result = self.run_fixture()
        self.assert_aborted(result, "restore_D1")
        self.assertIs(result.failures[0].error, error)
        self.assertIs(result.inputs["model"], self.model)
        self.assertEqual(result.d1_checkpoint, self.d1)
        self.dispatch.assert_not_called()
        self.save.assert_not_called()

    def test_restore_boundary_drift_prevents_any_training(self):
        def drift(*args, **kwargs):
            trainer = FakeRestoredTrainer(*args, **kwargs)
            trainer.optimizer["state"][0]["exp_avg"] = "wrong-moment"
            return trainer

        self.restore.side_effect = drift
        result = self.run_fixture()
        self.assert_aborted(result, "restore_D1")
        self.assertEqual(result.trainer.executed_updates, [])
        self.dispatch.assert_not_called()
        self.save.assert_not_called()

    def test_interrupted_training_is_not_retried_and_retains_partial_history(self):
        error = KeyboardInterrupt("synthetic interrupted update")

        def interrupted(*args, **kwargs):
            trainer = FakeRestoredTrainer(*args, **kwargs)
            trainer.error = error
            return trainer

        self.restore.side_effect = interrupted
        result = self.run_fixture()
        self.assert_aborted(result, "train_D2")
        self.assertIs(result.failures[0].error, error)
        self.assertEqual(result.trainer.stage_calls, ["D2"])
        self.assertEqual(result.trainer.executed_updates, [257])
        self.assertEqual(len(result.trainer.receipts), 257)
        self.dispatch.assert_not_called()
        self.save.assert_not_called()
        self.assert_d1_preserved()

    def test_partial_checkpoint_write_preserved_and_no_readout(self):
        error = OSError("synthetic full disk")

        def partial(value, stream):
            stream.write(b"partial D2 bytes")
            raise error

        with patch.object(fixtures.FakeTorch, "save", side_effect=partial):
            result = self.run_fixture()
        self.assert_aborted(result, "checkpoint_D2")
        self.assertIs(result.failures[0].error, error)
        self.assertEqual(result.checkpoint["completed_updates"], 512)
        directory = self.options["checkpoint_dir"]
        self.assertEqual((directory / source.checkpoint_api.BLOB_NAME).read_bytes(), b"partial D2 bytes")
        self.assertFalse((directory / source.checkpoint_api.COMMIT_NAME).exists())
        self.dispatch.assert_not_called()
        self.assert_d1_preserved()

    def test_actor_failure_keeps_saved_d2_custody_and_original_error(self):
        error = RuntimeError("synthetic decode failure")

        def broken(request):
            raise error

        self.actor.policy = broken
        result = self.run_fixture()
        self.assert_aborted(result, "ATOM_LOCAL_D2")
        self.assertTrue(any(fault.error is error for fault in result.failures))
        self.assertEqual(result.loaded_checkpoint["completed_updates"], 512)
        self.assertEqual(len(result.screens["ATOM_LOCAL"].reservations), 280)
        self.assertEqual(len(self.actor.calls), 1)
        self.assertTrue(list(self.options["atom_custody_dir"].iterdir()))
        self.assertIs(result.screens["ATOM_LOCAL"].failures[0].error, error)
        self.assert_d1_preserved()

    def test_adapter_mutation_during_readout_is_not_silently_accepted(self):
        original = self.actor.policy

        def mutated(request):
            self.model.adapter = "wrong-adapter"
            return original(request)

        self.actor.policy = mutated
        result = self.run_fixture()
        self.assert_aborted(result, "ATOM_LOCAL_D2")
        self.assertIn("adapter_changed_during_readout", str(result.failures[-1].error))
        self.assertIsNotNone(result.screens["ATOM_LOCAL"])
        self.assertIsNotNone(result.loaded_checkpoint)

    def test_lazy_import_has_no_native_or_io_side_effects(self):
        script = """
import sys
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.mkdir', 'os.remove', 'os.system'):
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
sys.addaudithook(audit)
from gpu import astra_stage2a_d2_resume as module
assert not {'torch', 'transformers', 'peft'}.intersection(sys.modules)
assert module.STATUS == 'SOURCE_ONLY_D2_RESUME'
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True,
                       cwd=Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
