"""CPU contracts and mocked orchestration, not native GPU qualification."""

from dataclasses import asdict, dataclass, replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_stage2a_closed_d1 as source
from tests import test_composition_birth_stage2a_training as fixtures


class PairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batches = fixtures.fixture()
        cls.fingerprint = source.training.validate_batches(cls.batches, master=fixtures.MASTER)

    def setUp(self):
        self.request = {"lineage_id": "original-ATOM"}
        self.observation = SimpleNamespace(trainable_roster=fixtures.planned_roster(),
                                           layer_count=1, initial_adapter_sha256="a" * 64)
        self.initialized = SimpleNamespace(observation=self.observation)
        self.prepared = SimpleNamespace(batches=self.batches, tape_fingerprint=self.fingerprint)
        self.original = dict(completed_updates=256, cursor=1024, receipts=[{}] * 256,
            binding=dict(arm="ATOM_LOCAL", lineage_id="original-ATOM", recipe=dict(source.training.RECIPE),
                         batches_sha256=self.fingerprint, initial_adapter_sha256="a" * 64,
                         roster=[asdict(spec) for spec in fixtures.planned_roster()]))

    def validate(self):
        return source.validate_pairing(self.request, self.original, self.prepared,
                                       self.initialized, master=fixtures.MASTER)

    def test_original_paired_tape_recipe_and_initial_roster_match(self):
        self.assertEqual(self.validate(), self.fingerprint)
        for batch in self.batches[:256]:
            for closed, atom in zip(batch.closed.records, batch.atom_local.records):
                self.assertGreaterEqual(len(closed.record.prefix), len(atom.record.prefix))
                self.assertEqual(closed.target_ids, atom.target_ids)
        self.assertTrue(any(len(closed.record.prefix) > len(atom.record.prefix)
                            for batch in self.batches[:256]
                            for closed, atom in zip(batch.closed.records, batch.atom_local.records)))

    def test_actual_closed_assistant_only_mask_is_validated(self):
        first = self.batches[0]
        labels = ((3,) + first.closed.labels[0][1:],) + first.closed.labels[1:]
        self.prepared.batches = (replace(first, closed=replace(first.closed, labels=labels)),) + self.batches[1:]
        with self.assertRaisesRegex(ValueError, "loss_mask_drift"):
            self.validate()

    def test_actual_tape_seed_is_validated(self):
        first = self.batches[0]
        self.prepared.batches = (replace(first, presentation=replace(first.presentation, rng_start_seed=0)),) + self.batches[1:]
        with self.assertRaisesRegex(ValueError, "planned_tape_or_seed_drift"):
            self.validate()

    def test_actual_roster_rejects_extra_base_trainable(self):
        self.observation.trainable_roster += (source.training.ParameterSpec("base.weight", (4, 4), "torch.float32"),)
        with self.assertRaisesRegex(ValueError, "all_layer_lora_roster_required"):
            self.validate()

    def test_original_recipe_cannot_be_changed(self):
        self.original["binding"]["recipe"]["lr"] = 1e-4
        with self.assertRaisesRegex(ValueError, "recipe_drift:lr"):
            self.validate()

    def test_initial_and_original_tape_digests_are_not_advisory(self):
        for key, error in (("initial_adapter_sha256", "original_initial_adapter_changed"),
                           ("batches_sha256", "original_paired_tape_changed")):
            with self.subTest(key=key), patch.dict(self.original["binding"], {key: "b" * 64}):
                with self.assertRaisesRegex(ValueError, error):
                    self.validate()


@dataclass
class SyntheticMetric:
    whole_chains: int = 0


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.original_root = self.root / "original"
        self.original_root.mkdir()
        self.official = self.root / "official.json"
        self.official.write_text('{"files":{}}')
        self.request = dict(master_hex=fixtures.MASTER.hex(), lineage_id="original-ATOM-lineage",
            atom_state_id="original-ATOM", base_state_id="original-BASE", model_dir="synthetic-model",
            official_manifest=str(self.official), base_state_sha256="b" * 64, threads=1, interop_threads=1,
            gpu_uuids=["GPU-main-0", "GPU-main-1"])
        self.request_raw = json.dumps(self.request).encode()
        (self.original_root / "REQUEST.json").write_bytes(self.request_raw)
        self.options = SimpleNamespace(original_run=str(self.original_root), output_dir=str(self.root / "fresh"),
            checkpoint_sha256="c" * 64, state_sha256="d" * 64, gpu_uuid="GPU-unused-2",
            closed_state_id="fresh-CLOSED", lineage_id="fresh-CLOSED-lineage", deadline_unix=200.0)
        self.enterContext(patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.options.gpu_uuid))
        self.now, self.events = 100.0, []
        self.model = SimpleNamespace(to=Mock(), register_forward_pre_hook=Mock(side_effect=self.register_hook))
        self.hook = Mock()
        self.before_forward = None
        self.initialized = SimpleNamespace(model=self.model, observation=SimpleNamespace(
            trainable_roster=fixtures.planned_roster(), layer_count=1, initial_adapter_sha256="a" * 64))
        self.torch = SimpleNamespace(__version__="2.13.0+cu130", bfloat16="bf16",
            cuda=SimpleNamespace(is_initialized=lambda: False, init=Mock(), device_count=lambda: 1),
            set_num_threads=Mock(), set_num_interop_threads=Mock())
        self.base_loader, self.tokenizer_loader = Mock(return_value=object()), Mock(return_value=object())
        self.libraries = (self.torch, SimpleNamespace(__version__="0.20.0"), SimpleNamespace(
            __version__="5.5.3", AutoModelForCausalLM=SimpleNamespace(from_pretrained=self.base_loader),
            AutoTokenizer=SimpleNamespace(from_pretrained=self.tokenizer_loader)))
        self.original = {"sha256": self.options.state_sha256, "adapter": "NEVER_RESTORE_THIS"}
        self.state = dict(sha256="e" * 64, binding={"arm": "CLOSED"}, optimizer={"moments": "preserved"},
                          rng={"cpu": "preserved", "cuda": ["single"]})
        self.original_manifest = dict(blob={"sha256": self.options.checkpoint_sha256},
                                      state_sha256=self.options.state_sha256)
        self.saved_manifest = {"state_sha256": self.state["sha256"]}
        self.inspect = self.mock(source.checkpoint_api, "inspect_checkpoint", side_effect=lambda path:
            self.original_manifest if path.parent == self.original_root else self.saved_manifest)
        self.load = self.mock(source.recovery, "load_exclusive", side_effect=self.load_checkpoint)
        self.save = self.mock(source.checkpoint_api, "save_checkpoint", side_effect=self.save_checkpoint)
        self.mock(source.tokens, "restore_official_backend", return_value={"synthetic": True})
        self.allocate = self.mock(source.prepare, "allocate_source", return_value=object())
        self.compile = self.mock(source.prepare, "compile_source_curriculum", return_value=object())
        self.prepared = SimpleNamespace(batches=("synthetic-paired-tape",), receipt_sha256="f" * 64)
        self.prepare = self.mock(source.prepare, "prepare_birth", return_value=self.prepared)
        self.held = SimpleNamespace(chains={}, interventions={}, canaries=(), receipt_sha256="1" * 64)
        self.mock(source.prepare, "prepare_reduced_held", return_value=self.held)
        self.initialize = self.mock(source.models, "initialize_atom_cpu", return_value=self.initialized)
        self.mock(source.models, "verify_retained_base", return_value=self.request["base_state_sha256"])
        self.mock(source, "validate_pairing", return_value="2" * 64)
        self.mock(source, "_checkpoint_adapter_sha256", return_value="3" * 64)
        self.adapter_hash = self.mock(source.training, "adapter_sha256", return_value="3" * 64)
        self.mock(source.training, "_tree_hash", side_effect=lambda state: state)
        self.trainer = SimpleNamespace(completed_updates=0, cursor=0, receipts=[], binding={"arm": "CLOSED"},
            train_stage=Mock(side_effect=self.train), checkpoint=Mock(return_value=self.state),
            _validate_checkpoint=Mock())
        self.trainer_factory = self.mock(source.training, "StatefulTrainer", return_value=self.trainer)
        owner = self

        class Actor:
            def __init__(self, **kwargs):
                owner.events.append("actor_created")
                self.calls = []

            def count_context(self, prefix):
                return 1

            def __call__(self, request):
                self.calls.append(request)

        self.mock(source.actor_api, "ReadoutActor", new=Actor)
        self.sink = Mock()
        self.mock(source.custody, "ScreenCustodySink", return_value=self.sink)
        self.mock(source.custody, "verify_receipt", return_value=SimpleNamespace(
            state_id=self.options.closed_state_id, stage="D1", terminal_reason="completed_unscored"))
        self.observed = SimpleNamespace(terminal_reason="completed_unscored", failures=[])
        self.runtime = self.mock(source.runtime, "run_reduced_state", side_effect=self.readout)
        self.reduction = SimpleNamespace(reportable=True, issues=(), metrics=SyntheticMetric(), accounting=SyntheticMetric())
        self.reduce = self.mock(source.reducer, "_reduce_state", return_value=self.reduction)

    def mock(self, target, name, **kwargs):
        return self.enterContext(patch.object(target, name, **kwargs))

    def register_hook(self, callback):
        self.before_forward = callback
        return self.hook

    def train(self, stage):
        self.events.append("train:" + stage)
        self.before_forward(self.model, ())
        self.trainer.completed_updates, self.trainer.cursor = 256, 1024
        self.trainer.receipts = [{"arm": "CLOSED", "update_number": number} for number in range(1, 257)]

    def save_checkpoint(self, path, state):
        self.events.append("save_full_checkpoint")
        path.mkdir()
        (path / "COMMITTED").write_text("synthetic")
        return self.saved_manifest

    def load_checkpoint(self, path, *, torch):
        self.assertIs(torch, self.torch)
        self.events.append("load_original" if path.parent == self.original_root else "load_closed")
        return self.original if path.parent == self.original_root else self.state

    def readout(self, **kwargs):
        self.events.append("readout")
        self.assertTrue((Path(self.options.output_dir) / "D1" / "COMMITTED").exists())
        self.assertTrue((Path(self.options.output_dir) / "TRAIN.json").exists())
        kwargs["count_context"](())
        kwargs["actor"](object())
        self.before_forward(self.model, ())
        return self.observed

    def run_arm(self):
        return source.run(self.options, libraries=self.libraries, clock=lambda: self.now)

    def assert_failed(self, reason):
        with self.assertRaisesRegex(ValueError, reason):
            self.run_arm()
        root = Path(self.options.output_dir)
        self.assertTrue((root / "FAILED.json").is_file())
        self.assertTrue((root / "TRAIN.json").is_file())
        self.assertFalse((root / "RESULT.json").exists())
        self.assertEqual((self.original_root / "REQUEST.json").read_bytes(), self.request_raw)

    def test_fresh_closed_fit_checkpoint_then_same_d1_readout_without_base(self):
        result = self.run_arm()
        self.assertEqual(self.events, ["load_original", "train:D1", "save_full_checkpoint",
                                      "load_closed", "actor_created", "readout"])
        self.assertEqual(result["baseline_model_calls"], 0)
        self.assertEqual(result["comparison"], "EXTERNAL_PENDING")
        self.base_loader.assert_called_once()
        self.initialize.assert_called_once()
        kwargs = self.trainer_factory.call_args.kwargs
        self.assertEqual(kwargs["arm"], "CLOSED")
        self.assertNotIn("checkpoint", kwargs)
        self.assertIs(kwargs["batches"], self.prepared.batches)
        self.assertEqual(kwargs["initial_adapter_sha256"], "a" * 64)
        self.assertEqual(kwargs["master"], fixtures.MASTER)
        self.trainer.train_stage.assert_called_once_with("D1")
        self.trainer._validate_checkpoint.assert_called_once_with(self.state)
        self.assertEqual(self.runtime.call_args.kwargs["state_id"], "fresh-CLOSED")
        self.assertEqual(self.runtime.call_args.kwargs["stage"], "D1")
        self.assertEqual(self.reduce.call_args.args[1:3], ("fresh-CLOSED",
            source.screen.reduced_decode_seeds("D1", master=fixtures.MASTER)))
        self.hook.remove.assert_called_once()
        self.sink.close.assert_called_once()
        self.assertEqual((self.original_root / "REQUEST.json").read_bytes(), self.request_raw)

    def test_protected_main_gpu_is_rejected_before_checkpoint_or_model_load(self):
        self.options.gpu_uuid = "GPU-main-0"
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-main-0"):
            self.assert_failed("original_gpus_reserved_for_main")
        self.load.assert_not_called()
        self.base_loader.assert_not_called()

    def test_single_visible_gpu_binding_required(self):
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-unused-2,GPU-unused-3"):
            self.assert_failed("single_gpu_binding_required")
        self.base_loader.assert_not_called()

    def test_state_identity_cannot_alias_atom(self):
        self.options.closed_state_id = self.request["atom_state_id"]
        self.assert_failed("distinct_closed_identity_required")

    def test_nonfinite_or_expired_deadline_never_loads_model(self):
        for number, deadline in enumerate((float("inf"), float("nan"), 100.0, True)):
            with self.subTest(deadline=deadline):
                self.options.output_dir = str(self.root / ("deadline-" + str(number)))
                self.options.deadline_unix = deadline
                self.assert_failed("finite_unexpired_deadline_required")
        self.base_loader.assert_not_called()

    def test_original_blob_mismatch_fails_before_deserialization(self):
        self.original_manifest["blob"]["sha256"] = "wrong"
        self.assert_failed("original_checkpoint_blob_changed")
        self.load.assert_not_called()

    def test_deadline_cannot_exceed_reserved_5400_seconds(self):
        self.options.deadline_unix = self.now + 5401
        self.assert_failed("maximum_5400_second_budget_exceeded")
        self.base_loader.assert_not_called()

    def test_full_state_roundtrip_drift_prevents_readout(self):
        self.load.side_effect = [self.original, {**self.state, "optimizer": {"moments": "changed"}}]
        self.assert_failed("full_checkpoint_roundtrip_changed")
        self.runtime.assert_not_called()

    def test_partial_checkpoint_save_is_preserved_without_readout(self):
        def broken(path, state):
            path.mkdir()
            (path / "checkpoint.pt").write_bytes(b"partial")
            raise ValueError("synthetic_partial_save")

        self.save.side_effect = broken
        self.assert_failed("synthetic_partial_save")
        self.assertEqual((Path(self.options.output_dir) / "D1" / "checkpoint.pt").read_bytes(), b"partial")
        self.runtime.assert_not_called()

    def test_forward_deadline_preserves_partial_training_without_checkpoint(self):
        def interrupted(stage):
            self.trainer.completed_updates, self.trainer.cursor = 1, 4
            self.trainer.receipts = [{"update_number": 1}]
            self.now = 200.0
            self.before_forward(self.model, ())

        self.trainer.train_stage.side_effect = interrupted
        self.assert_failed("finite_unexpired_deadline_required:forward")
        record = json.loads((Path(self.options.output_dir) / "TRAIN.json").read_bytes())
        self.assertEqual(record["completed_updates"], 1)
        self.save.assert_not_called()
        self.runtime.assert_not_called()
        self.hook.remove.assert_called_once()

    def test_short_fit_is_not_checkpointed(self):
        self.trainer.train_stage.side_effect = lambda stage: None
        self.assert_failed("exact_d1_256_updates_required")
        self.save.assert_not_called()
        self.runtime.assert_not_called()

    def test_failed_full_checkpoint_load_preserves_commit_and_prevents_readout(self):
        def broken(path, *, torch):
            if path.parent != self.original_root:
                raise ValueError("strict_load_failure")
            return self.original

        self.load.side_effect = broken
        self.assert_failed("strict_load_failure")
        self.assertTrue((Path(self.options.output_dir) / "D1" / "COMMITTED").exists())
        self.runtime.assert_not_called()

    def test_readout_failure_retains_checkpoint_and_closes_sink(self):
        self.runtime.side_effect = ValueError("synthetic_readout_failure")
        self.assert_failed("synthetic_readout_failure")
        self.assertTrue((Path(self.options.output_dir) / "D1" / "COMMITTED").exists())
        self.sink.close.assert_called_once()
        self.hook.remove.assert_called_once()

    def test_adapter_mutation_during_readout_is_not_reported_as_success(self):
        self.adapter_hash.side_effect = ["3" * 64, "changed"]
        self.assert_failed("readout_changed_adapter")
        self.reduce.assert_not_called()

    def test_unreportable_reduction_does_not_create_result(self):
        self.reduction.reportable = False
        self.assert_failed("nonreportable_closed")

    def test_existing_root_is_never_overwritten(self):
        self.run_arm()
        result_path = Path(self.options.output_dir) / "RESULT.json"
        before = result_path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_arm()
        self.assertEqual(result_path.read_bytes(), before)

    def test_output_cannot_be_created_inside_original_run(self):
        self.options.output_dir = str(self.original_root / "CLOSED")
        with self.assertRaisesRegex(ValueError, "output_must_not_modify_original_run"):
            self.run_arm()
        self.assertFalse(Path(self.options.output_dir).exists())


class SourceAndReadoutTests(unittest.TestCase):
    def test_import_and_help_do_not_import_native_libraries_or_launch(self):
        script = """
import sys
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.mkdir', 'os.remove', 'os.system'):
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
sys.addaudithook(audit)
from gpu import astra_stage2a_closed_d1 as source
assert not {'torch', 'transformers', 'peft'}.intersection(sys.modules)
try:
    source.parse_args(['--help'])
except SystemExit as error:
    assert error.code == 0
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True, capture_output=True,
                       cwd=Path(__file__).resolve().parents[1])

    def test_distinct_closed_id_uses_existing_d1_slots_seeds_and_reducer(self):
        from tests import test_composition_birth_stage2a_screen_reduce as readout

        readout.ReducedScreenTests.setUpClass()
        fixture = readout.ReducedScreenTests
        observed = fixture.make_run("synthetic-CLOSED-D1")
        seeds = source.screen.reduced_decode_seeds("D1", master=readout.MASTER)
        reduced = source.reducer._reduce_state(observed, "synthetic-CLOSED-D1", seeds, set(),
            master=readout.MASTER, chains=fixture.chains, interventions=fixture.interventions,
            canaries=fixture.canaries)
        self.assertTrue(reduced.reportable, reduced.issues)
        self.assertEqual(reduced.metrics.whole_chains, 8)
        self.assertEqual(len(observed.reservations), 280)
        wrong_id = source.reducer._reduce_state(observed, readout.ATOM_ID, seeds, set(),
            master=readout.MASTER, chains=fixture.chains, interventions=fixture.interventions,
            canaries=fixture.canaries)
        self.assertFalse(wrong_id.reportable)


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch absent; native CPU fit not exercised")
class NativeCPUFitTests(unittest.TestCase):
    def test_closed_256_updates_full_strict_checkpoint_and_real_masks(self):
        import torch

        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, previous_threads)
        model, roster, batches = fixtures.tiny_native_model(), fixtures.planned_roster(), fixtures.fixture()
        initial = source.training.adapter_sha256(model, roster)
        trainer = source.training.StatefulTrainer(model, arm="CLOSED", master=fixtures.MASTER,
            batches=batches, trainable_roster=roster, layer_count=1, adapter_name="default",
            lineage_id="SYNTHETIC-CLOSED-FRESH", preparation_sha256="a" * 64, initial_adapter_sha256=initial)
        self.assertEqual(trainer.completed_updates, 0)
        receipts = trainer.train_stage("D1")
        self.assertEqual(len(receipts), 256)
        self.assertEqual(model.forward_calls, 256)
        self.assertEqual(trainer.cursor, 1024)
        self.assertNotEqual(source.training.adapter_sha256(model, roster), initial)
        for receipt, batch in zip(receipts, batches[:256]):
            self.assertEqual(receipt["arm"], "CLOSED")
            self.assertEqual(receipt["prefix_token_counts"], tuple(len(row.context_ids) for row in batch.closed.records))
            self.assertEqual(receipt["rng_start_seed"], batch.presentation.rng_start_seed)
        state = trainer.checkpoint()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "D1"
            source.checkpoint_api.save_checkpoint(target, state)
            loaded = source.recovery.load_exclusive(target, torch=torch)
            trainer._validate_checkpoint(loaded)
            self.assertEqual(source.training._tree_hash(loaded), source.training._tree_hash(state))


if __name__ == "__main__":
    unittest.main()
