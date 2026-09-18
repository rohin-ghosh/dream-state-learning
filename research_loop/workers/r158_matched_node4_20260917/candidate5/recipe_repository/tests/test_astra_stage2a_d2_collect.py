"""CPU-only D2 bindings and injected factory mechanics; no native model load."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_stage2a_d2_collect as source
from tests import test_astra_stage2a_outcome_collect as fixtures


def bound_state():
    return dict(sha256=source.D2_STATE, completed_updates=512, cursor=2048, receipts=[{}] * 512,
                binding=dict(lineage_id="synthetic-original-ATOM", arm="ATOM_LOCAL",
                             initial_adapter_sha256="a" * 64))


def bound_request():
    return dict(lineage_id="synthetic-original-ATOM", master_hex=b"synthetic-original-master".hex(),
                base_state_sha256="b" * 64)


class BindingTests(unittest.TestCase):
    def test_exact_saved_d2_and_original_initialization_master(self):
        self.assertEqual(source.validate_source(bound_state(), bound_request()), b"synthetic-original-master")
        self.assertEqual(source.MASTER, b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A3")

    def test_wrong_state_updates_cursor_and_receipt_count_fail_closed(self):
        for field, value in (("sha256", "f" * 64), ("completed_updates", 256),
                             ("completed_updates", 513), ("cursor", 1024), ("cursor", 2047),
                             ("receipts", [{}] * 511)):
            with self.subTest(field=field, value_type=type(value).__name__):
                state = bound_state()
                state[field] = value
                with self.assertRaisesRegex(ValueError, "exact_saved_D2_required"):
                    source.validate_source(state, bound_request())

    def test_lineage_and_arm_mismatch_fail_closed(self):
        for field, value in (("lineage_id", "wrong-lineage"), ("arm", "CLOSED")):
            state = bound_state()
            state["binding"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "D2_source_lineage_mismatch"):
                source.validate_source(state, bound_request())

    def test_original_request_cannot_reuse_a3_collection_master(self):
        request = bound_request()
        request["master_hex"] = source.MASTER.hex()
        with self.assertRaisesRegex(ValueError, "fresh_collection_master_required"):
            source.validate_source(bound_state(), request)

    def test_missing_binding_does_not_fall_back(self):
        state = bound_state()
        del state["binding"]["lineage_id"]
        with self.assertRaises(KeyError):
            source.validate_source(state, bound_request())

    def test_import_and_help_do_not_load_native_libraries_or_execute(self):
        script = """
import sys
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.mkdir', 'os.remove', 'os.system'):
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
sys.addaudithook(audit)
from gpu import astra_stage2a_outcome_collect as collector
before=(collector.MASTER, collector.GUIDANCE)
from gpu import astra_stage2a_d2_collect as source
assert (collector.MASTER, collector.GUIDANCE)==before
try:
    source.main(['--help'])
except SystemExit as error:
    assert error.code==0
assert not {'torch','peft','transformers'}.intersection(sys.modules)
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True, capture_output=True,
                       cwd=Path(__file__).resolve().parents[1])

    def test_cli_uses_a3_with_unchanged_v1_teacher_and_factory(self):
        original = source.collector
        guidance = original.GUIDANCE
        argv = ["--model-dir", "model", "--output", "fresh", "--gpu-uuid", "GPU-test",
                "--expected-base-sha256", "b" * 64, "--checkpoint", "D2", "--original-request", "REQUEST.json",
                "--deadline-unix", "900"]
        with patch.object(original, "MASTER", original.MASTER), patch.object(original, "run") as run:
            source.main(argv)
            self.assertEqual(original.MASTER, source.MASTER)
            self.assertEqual(original.GUIDANCE, guidance)
            self.assertEqual(original.MAX_SECONDS, 900)
        self.assertTrue(callable(run.call_args.kwargs["learner_factory"]))
        self.assertEqual(run.call_args.args[0].checkpoint, "D2")


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.request_path = self.root / "original.json"
        self.request_path.write_text(json.dumps(bound_request()))
        self.request_bytes = self.request_path.read_bytes()
        self.output = self.root / "fresh"
        self.output.mkdir()
        self.options = SimpleNamespace(checkpoint=str(self.root / "D2"), original_request=str(self.request_path),
                                       expected_base_sha256="b" * 64)
        self.state = bound_state()
        self.manifest = dict(state_sha256=source.D2_STATE, blob={"sha256": "c" * 64})
        self.torch, self.peft = ModuleType("torch"), ModuleType("peft")
        self.peft.__version__ = source.collector.tokens.RUNTIME_VERSIONS["peft"]
        self.enterContext(patch.dict(sys.modules, {"torch": self.torch, "peft": self.peft}))
        spec = source.training.ParameterSpec("synthetic.lora_A.default.weight", (8, 4), "torch.float32")
        self.initialized = SimpleNamespace(model=object(), observation=SimpleNamespace(
            initial_adapter_sha256="a" * 64, trainable_roster=(spec,)))
        self.base, self.check = object(), Mock()
        self.inspect = self.enterContext(patch.object(source.checkpoint_api, "inspect_checkpoint", return_value=self.manifest))
        self.load = self.enterContext(patch.object(source.recovery, "load_exclusive", return_value=self.state))
        self.initialize = self.enterContext(patch.object(source.models, "initialize_atom_cpu", return_value=self.initialized))
        self.restore = self.enterContext(patch.object(source.readout, "restore_adapter", return_value=source.D2_ADAPTER))
        self.adapter = self.enterContext(patch.object(source.training, "adapter_sha256", return_value=source.D2_ADAPTER))
        self.verify_base = self.enterContext(patch.object(source.models, "verify_retained_base", return_value="b" * 64))

    def factory(self):
        return source.make_factory(self.options)(self.base, self.output, self.check)

    def test_exact_restore_dev_receipt_and_repeatable_adapter_base_verifier(self):
        before = deepcopy(self.state)
        model, receipt, verify = self.factory()
        self.assertIs(model, self.initialized.model)
        self.load.assert_called_once_with(Path(self.options.checkpoint), torch=self.torch)
        self.assertEqual(self.initialize.call_args.kwargs["master"], b"synthetic-original-master")
        self.assertEqual(self.initialize.call_args.kwargs["expected_base_sha256"], "b" * 64)
        self.restore.assert_called_once_with(self.initialized, self.state, torch=self.torch)
        self.assertEqual(receipt["checkpoint_state_sha256"], source.D2_STATE)
        self.assertEqual(receipt["adapter_sha256"], source.D2_ADAPTER)
        self.assertEqual(receipt["new_updates"], 0)
        self.assertEqual(receipt["kind"], "FROZEN_DEV_D2_CONTROLLER_NOT_AUTHENTIC_BIRTH")
        self.assertEqual(receipt["original_request_sha256"], sha256(self.request_bytes).hexdigest())
        self.assertEqual(receipt["roster"], [asdict(spec) for spec in self.initialized.observation.trainable_roster])
        self.assertTrue((self.output / "LEARNER.json").is_file())
        self.assertEqual(verify(), "b" * 64)
        self.assertEqual(verify(), "b" * 64)
        self.assertEqual(self.adapter.call_count, 2)
        self.assertEqual(self.verify_base.call_count, 2)
        self.assertEqual(self.state, before)
        self.assertEqual(self.request_path.read_bytes(), self.request_bytes)

    def test_strict_loader_failure_is_not_retried_or_bypassed(self):
        self.load.side_effect = ValueError("strict loader failure")
        with self.assertRaisesRegex(ValueError, "strict loader failure"):
            self.factory()
        self.load.assert_called_once()
        self.initialize.assert_not_called()
        self.restore.assert_not_called()

    def test_wrong_state_fails_before_initialization(self):
        self.state["sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "exact_saved_D2_required"):
            self.factory()
        self.initialize.assert_not_called()

    def test_base_pin_mismatch_fails_before_initialization(self):
        self.options.expected_base_sha256 = "d" * 64
        with self.assertRaisesRegex(ValueError, "D2_base_pin_changed"):
            self.factory()
        self.initialize.assert_not_called()

    def test_initial_adapter_mismatch_fails_before_restore(self):
        self.initialized.observation.initial_adapter_sha256 = "d" * 64
        with self.assertRaisesRegex(ValueError, "initial_lineage_changed"):
            self.factory()
        self.restore.assert_not_called()

    def test_wrong_restored_adapter_never_writes_learner_receipt(self):
        self.restore.return_value = "d" * 64
        with self.assertRaisesRegex(ValueError, "D2_adapter_changed"):
            self.factory()
        self.assertFalse((self.output / "LEARNER.json").exists())

    def test_adapter_mutation_fails_verification_before_base_hash(self):
        _, _, verify = self.factory()
        self.adapter.return_value = "changed"
        with self.assertRaisesRegex(ValueError, "collection_changed_D2_adapter"):
            verify()
        self.verify_base.assert_not_called()

    def test_base_mutation_error_is_not_suppressed(self):
        _, _, verify = self.factory()
        self.verify_base.side_effect = ValueError("retained_frozen_base_changed")
        with self.assertRaisesRegex(ValueError, "retained_frozen_base_changed"):
            verify()

    def test_peft_version_and_deadline_fail_before_checkpoint_read(self):
        self.peft.__version__ = "wrong"
        with self.assertRaisesRegex(ValueError, "peft_runtime_changed"):
            self.factory()
        self.load.assert_not_called()
        self.check.side_effect = ValueError("deadline")
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.factory()
        self.inspect.assert_not_called()


class CollectorSeamTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EntryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.events = []
        self.parameter = SimpleNamespace(requires_grad=True)
        self.hook = Mock()
        self.model = SimpleNamespace(
            requires_grad_=Mock(side_effect=lambda value: setattr(self.parameter, "requires_grad", value)),
            eval=Mock(), parameters=lambda: (self.parameter,),
            to=Mock(side_effect=lambda device: self.events.append("place")),
            register_forward_pre_hook=Mock(return_value=self.hook))
        self.verify = Mock(side_effect=self.verification)
        self.factory = Mock(return_value=(self.model, {"kind": "SYNTHETIC_DEV_D2"}, self.verify))
        self.libraries = self.fixture.native_fixture(self.collected)

    def verification(self):
        self.events.append("verify")
        return "a" * 64

    def collected(self, worlds, teacher, *, emit_episode, emit_row, check, summary):
        self.assertFalse(self.parameter.requires_grad)
        self.events.append("collect")
        summary["completed_episodes"] = 32

    def run_collection(self):
        return source.collector.run(self.fixture.options, libraries=self.libraries, clock=lambda: 100.0,
                                    learner_factory=self.factory)

    def test_factory_model_frozen_all_and_verified_before_after_collection(self):
        result = self.run_collection()
        self.assertEqual(self.events, ["verify", "place", "collect", "verify"])
        self.assertEqual(result["learner"], {"kind": "SYNTHETIC_DEV_D2"})
        self.assertEqual(result["base_pre"], result["base_post"])
        self.model.requires_grad_.assert_called_once_with(False)
        self.model.eval.assert_called_once()
        self.fixture.model.to.assert_not_called()
        self.assertEqual(self.fixture.hash_base.call_count, 1)
        self.hook.remove.assert_called_once()

    def test_wrong_pre_base_verification_prevents_cuda(self):
        self.verify.side_effect = ["wrong"]
        with self.assertRaisesRegex(ValueError, "collector_learner_base_mismatch"):
            self.run_collection()
        self.fixture.torch.cuda.init.assert_not_called()
        self.model.to.assert_not_called()

    def test_wrong_post_base_verification_cannot_create_result(self):
        self.verify.side_effect = ["a" * 64, "wrong"]
        with self.assertRaisesRegex(ValueError, "collection_changed_base"):
            self.run_collection()
        root = Path(self.fixture.options.output)
        self.assertTrue((root / "FAILED.json").exists())
        self.assertFalse((root / "RESULT.json").exists())
        self.hook.remove.assert_called_once()

    def test_post_adapter_verification_error_cannot_create_result(self):
        self.verify.side_effect = ["a" * 64, ValueError("collection_changed_D2_adapter")]
        with self.assertRaisesRegex(ValueError, "collection_changed_D2_adapter"):
            self.run_collection()
        self.assertFalse((Path(self.fixture.options.output) / "RESULT.json").exists())

    def test_unfrozen_factory_model_fails_before_verification_or_cuda(self):
        self.model.requires_grad_.side_effect = None
        with self.assertRaisesRegex(ValueError, "frozen_collector_required"):
            self.run_collection()
        self.verify.assert_not_called()
        self.fixture.torch.cuda.init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
