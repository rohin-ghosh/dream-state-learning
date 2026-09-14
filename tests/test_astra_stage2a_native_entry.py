"""Injected orchestration tests only; no real torch, tokenizer, model or GPU use.

Main runs this bounded suite and reviews exact source before any native entry.
Fake source admission is deliberately not a source-qualification receipt.
"""

from dataclasses import dataclass
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_native_entry as source


class Tensor:
    def __init__(self, value, device="cpu"):
        self.value, self.device = value, SimpleNamespace(type=device)


class Device:
    def __init__(self, name):
        self.name, self.type = name, name.split(":")[0]

    def __str__(self):
        return self.name


class Model:
    def __init__(self):
        self.tensors = {"weight": Tensor("frozen-weight"), "buffer": Tensor("frozen-buffer")}
        self.config = SimpleNamespace(_attn_implementation="sdpa")
        self.layer = SimpleNamespace(active_adapters=["default"], disable_adapters=False, merged=False)
        self.pre_hooks, self.forward_calls = [], 0
        self.after_forward = lambda: None

    def register_forward_pre_hook(self, hook):
        self.pre_hooks.append(hook)
        return SimpleNamespace(remove=lambda: self.pre_hooks.remove(hook))

    def __call__(self, *args, **kwargs):
        for hook in tuple(self.pre_hooks):
            hook(self, args)
        self.forward_calls += 1
        self.after_forward()

    def named_parameters(self):
        return tuple((name, value) for name, value in self.tensors.items() if "buffer" not in name)

    def named_buffers(self):
        return tuple((name, value) for name, value in self.tensors.items() if "buffer" in name)

    def requires_grad_(self, value):
        self.requires_grad = value
        return self

    def to(self, *, device):
        self.tensors = {name: Tensor(value.value) for name, value in self.tensors.items()}
        for value in self.tensors.values():
            value.device = Device(device)
        return self

    def get_submodule(self, name):
        return self.layer


def state_hash(references):
    return sha256(json.dumps({name: value.value for name, value in references.items()}, sort_keys=True).encode()).hexdigest()


@dataclass
class Criterion:
    name: str = "fake_numeric_failure_is_data"
    count: int = 0
    minimum: int = 3


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fake-native-entry-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model_dir = self.root / "model"
        self.model_dir.mkdir()
        names = list(source.tokens.REQUIRED_FILES) + [".gitattributes", "LICENSE", "README.md",
            "model.safetensors.index.json"] + [f"model-{index:05d}-of-00004.safetensors" for index in range(1, 5)]
        files = {}
        for name in names:
            raw = ("FAKE_FILE_NOT_MODEL:" + name).encode()
            (self.model_dir / name).write_bytes(raw)
            files[name] = {"size": len(raw), "sha256": sha256(raw).hexdigest()}
        self.official = self.root / "official.json"
        self.official.write_text(json.dumps(dict(repository=source.tokens.REPOSITORY, revision=source.tokens.REVISION,
            status="PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING", file_count=14, files=files)))
        self.enterContext(patch.object(source.tokens, "OFFICIAL_RECEIPT_SHA256", sha256(self.official.read_bytes()).hexdigest()))
        self.now, self.log, self.loaded = 100.0, [], []
        self.options = SimpleNamespace(mode="prepare-only", model_dir=str(self.model_dir), official_manifest=str(self.official),
            qualification_dir="fake-qualified", separation_dir="fake-separated", separation_original_dir="fake-relocated",
            output_dir=str(self.root / "run"), master_hex=b"preselected-master".hex(), base_state_sha256=state_hash(Model().tensors),
            lineage_id="fake-lineage", base_state_id="fake-BASE", atom_state_id="fake-ATOM", deadline_unix=200.0,
            threads=1, interop_threads=1, gpu_uuids=[], base_device=None, atom_device=None, driver_version=None)
        self.enterContext(patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}))
        self.cuda = SimpleNamespace(initialized=False, is_initialized=lambda: self.cuda.initialized,
            init=self.cuda_init, device_count=lambda: 2, manual_seed_all=lambda seed: self.log.append("cuda_seed"))
        self.torch = SimpleNamespace(__version__="2.13.0+cu130", version=SimpleNamespace(cuda="13.0"), bfloat16="bf16",
            cuda=self.cuda, set_num_threads=lambda value: None, set_num_interop_threads=lambda value: None,
            get_num_threads=lambda: 1, get_num_interop_threads=lambda: 1)
        self.tokenizer = object()
        self.token_loader = self.enterContext(patch.object(SimpleNamespace(load=None), "load", side_effect=self.load_tokenizer))
        self.model_loader = self.enterContext(patch.object(SimpleNamespace(load=None), "load", side_effect=self.load_model))
        self.transformers = SimpleNamespace(__version__="5.5.3", AutoTokenizer=SimpleNamespace(from_pretrained=self.token_loader),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=self.model_loader))
        self.libraries = (self.torch, SimpleNamespace(__version__="0.20.0"), self.transformers)
        self.allocation, self.compiled = object(), object()
        self.batches = ("fake-prepared-batches",)
        self.allocate = self.mock(source.prepare, "allocate_source", side_effect=lambda **kwargs: self.event("allocate", self.allocation))
        self.compile = self.mock(source.prepare, "compile_source_curriculum", side_effect=lambda **kwargs: self.event("compile", self.compiled))
        self.gates = self.mock(source.tokens, "_source_gates", side_effect=lambda *args: self.event("gates", {"fake_only": True}))
        self.tokens = self.mock(source.tokens, "prepare_tokenizer_receipt", side_effect=self.token_receipt)
        self.initialize = self.mock(source.models, "initialize_atom_cpu", side_effect=self.initialize_atom)
        self.mock(source, "base_state_hash", side_effect=state_hash)
        self.versions = self.mock(source.metadata, "version", side_effect=lambda name: source.tokens.RUNTIME_VERSIONS[name] or "0.22.2")
        self.held = self.mock(source.prepare, "prepare_reduced_held", return_value=SimpleNamespace(chains={}, interventions={}, canaries=()))
        self.conduct = self.mock(source.conductor, "run_reduced_conductor", side_effect=self.conductor)
        self.before_atom = lambda: None
        self.after_base = lambda: None
        self.after_conductor = lambda: None
        owner = self

        class Actor:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
                self.calls = []

            def count_context(self, prefix):
                return 1

            def __call__(self, request):
                owner.log.append("actor:" + request)
                self.calls.append(request)
                if request == "BASE":
                    owner.after_base()

        class Trainer:
            def __init__(self, model, **kwargs):
                self.model, self.batches, self.binding = model, kwargs["batches"], {"fake": True}
                self.completed_updates, self.receipts, self._failed = 0, [], False

            @property
            def cursor(self):
                return self.completed_updates * 4

            def train_stage(self, selected):
                owner.log.append("train:" + selected)
                try:
                    for update in range(1, 4):
                        self.model(input_ids="fake", use_cache=False)
                        self.completed_updates = update
                        self.receipts.append({"update_number": update, "loss": 0.25, "unit_ids": ("fake",)})
                except BaseException:
                    self._failed = True
                    raise

            def checkpoint(self):
                owner.log.append("checkpoint")

        self.Actor, self.Trainer = Actor, Trainer

    def mock(self, target, name, **kwargs):
        return self.enterContext(patch.object(target, name, **kwargs))

    def event(self, name, value):
        self.log.append(name)
        return value

    def cuda_init(self):
        self.cuda.initialized = True
        self.log.append("cuda_init")

    def load_tokenizer(self, *args, **kwargs):
        return self.event("tokenizer_load", self.tokenizer)

    def load_model(self, *args, **kwargs):
        self.loaded.append(Model())
        return self.event("model_load", self.loaded[-1])

    def token_receipt(self, **kwargs):
        Path(kwargs["output_dir"]).mkdir()
        return self.event("tokenizer_receipt", SimpleNamespace(receipt_sha256="a" * 64,
            prepared_birth=SimpleNamespace(batches=self.batches)))

    def initialize_atom(self, model, **kwargs):
        self.log.append("initialize")
        directory = Path(kwargs["initial_directory"])
        directory.mkdir()
        (directory / "initial_state.pt").write_bytes(b"fake initial artifact, not torch")
        references = dict(model.tensors)
        paths = {name: "base." + name for name in references}
        model.tensors = {paths[name]: value for name, value in references.items()}
        model.peft_config, model.active_adapters = {"default": object()}, ["default"]
        observation = SimpleNamespace(trainable_roster=(source.training.ParameterSpec("layer.lora_A.default.weight", (8, 1), "torch.float32"),),
            layer_count=1, initial_adapter_sha256="b" * 64)
        self.initialized = SimpleNamespace(model=model, observation=observation, base_paths=paths, base_references=references,
            receipt={"expected_base_sha256": kwargs["expected_base_sha256"]}, directory=directory)
        return self.initialized

    def conductor(self, **kwargs):
        kwargs["base_actor"].count_context(())
        kwargs["base_actor"]("BASE")
        kwargs["trainer"].train_stage("D1")
        kwargs["trainer"].checkpoint()
        self.before_atom()
        kwargs["atom_local_actor"]("ATOM")
        self.after_conductor()
        return SimpleNamespace(terminal_reason="reduced", failures=(), hashes={"d1_adapter": "c" * 64},
            reduction=SimpleNamespace(criteria=(Criterion(),)))

    def execute_options(self):
        self.options.mode, self.options.gpu_uuids = "reduced", ["GPU-fake-base", "GPU-fake-atom"]
        self.options.base_device, self.options.atom_device, self.options.driver_version = "cuda:0", "cuda:1", "fake-driver"
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(self.options.gpu_uuids)

    def run_entry(self):
        return source.run_entry(self.options, libraries=self.libraries, clock=lambda: self.now,
            device_probe=lambda *args: self.event("devices", [{"uuid": value} for value in self.options.gpu_uuids]),
            actor_factory=self.Actor, trainer_factory=self.Trainer)

    def fail(self, reason):
        with self.assertRaisesRegex(source.EntryFailure, reason) as caught:
            self.run_entry()
        return caught.exception.evidence

    def test_prepare_only_order_exact_pins_and_no_cuda(self):
        evidence = self.run_entry()
        self.assertEqual(self.log, ["allocate", "compile", "gates", "tokenizer_load", "tokenizer_receipt", "model_load", "initialize"])
        self.allocate.assert_called_once_with(master=b"preselected-master")
        self.compile.assert_called_once_with(bound_allocation=self.allocation, master=b"preselected-master")
        self.assertIs(self.gates.call_args.args[3], self.allocation)
        self.assertIs(self.gates.call_args.args[4], self.compiled)
        self.assertEqual(self.gates.call_args.args[-1], "fake-relocated")
        self.assertIs(self.tokens.call_args.kwargs["compiled_curriculum"], self.compiled)
        self.assertEqual(self.tokens.call_args.kwargs["separation_original_dir"], "fake-relocated")
        self.token_loader.assert_called_once_with(str(self.model_dir), local_files_only=True, trust_remote_code=False,
            use_fast=True, padding_side="right")
        self.model_loader.assert_called_once_with(str(self.model_dir), local_files_only=True, trust_remote_code=False,
            torch_dtype="bf16", device_map=None, attn_implementation="sdpa", use_safetensors=True)
        self.assertFalse(self.cuda.initialized)
        self.assertEqual(self.loaded[0].forward_calls, 0)
        self.assertFalse((Path(self.options.output_dir) / "TRAINING_OBSERVATIONS.json").exists())
        self.conduct.assert_not_called()
        self.assertEqual(evidence["receipt"]["status"], "PREPARED_CPU_ONLY")
        self.assertTrue((Path(self.options.output_dir) / "initial/initial_state.pt").exists())

    def test_reduced_checks_current_bases_and_keeps_numeric_failures(self):
        self.execute_options()
        evidence = self.run_entry()
        self.assertEqual(self.log.count("train:D1"), 1)
        self.assertEqual([entry for entry in self.log if entry.startswith("actor:")], ["actor:BASE", "actor:ATOM"])
        self.assertEqual(self.model_loader.call_count, 2)
        self.assertLess(self.log.index("initialize"), self.log.index("cuda_init"))
        self.assertEqual(evidence["receipt"]["status"], "REDUCED_NUMERICAL_DATA")
        self.assertEqual(evidence["receipt"]["criteria"][0]["count"], 0)
        for key in ("base_pre", "base_post", "atom_base_pre", "atom_base_post"):
            self.assertEqual(evidence["receipt"]["hashes"][key], self.options.base_state_sha256)
        actors = evidence["objects"]["actors"]
        self.assertIsNot(actors[0].model, actors[1].model)
        self.assertTrue(all(actor.count_basis == "UNAUTHENTICATED_CALLER_TOKENIZER" for actor in actors))
        self.assertEqual(self.conduct.call_args.kwargs["counter_provenance"], "TOKENIZER_RECEIPT_SHA256:" + "a" * 64)
        self.assertIn("SAME_PROCESS_ONLY", evidence["receipt"]["claim_scope"])
        self.assertEqual(self.initialized.model.forward_calls, 3)
        self.assertEqual(self.initialized.model.pre_hooks, [])
        observed = json.loads((Path(self.options.output_dir) / "TRAINING_OBSERVATIONS.json").read_bytes())
        self.assertEqual(observed["receipts"], source.tokens.retain(evidence["objects"]["trainer"].receipts))
        self.assertEqual(observed["completed_updates"], 3)

    def test_source_failure_stops_before_tokenizer_or_model(self):
        error = ValueError("incomplete_source_gates")
        self.gates.side_effect = error
        evidence = self.fail("incomplete_source_gates")
        self.assertIs(evidence["errors"][0], error)
        self.token_loader.assert_not_called()
        self.model_loader.assert_not_called()
        self.assertTrue((Path(self.options.output_dir) / "FAILED.json").exists())

    def test_all_fourteen_file_lengths_and_hashes_precede_load(self):
        shard = self.model_dir / "model-00004-of-00004.safetensors"
        shard.write_bytes(shard.read_bytes() + b"corrupt")
        self.fail("official_file_mismatch")
        self.token_loader.assert_not_called()
        self.model_loader.assert_not_called()

    def test_shard_hashing_streams_instead_of_read_bytes(self):
        original = Path.read_bytes

        def guarded(path):
            self.assertNotEqual(path.suffix, ".safetensors")
            return original(path)

        with patch.object(Path, "read_bytes", guarded):
            self.assertEqual(len(source.verify_official_files(self.model_dir, self.official, lambda stage: None)), 14)

    def test_bad_deadline_no_output_or_work(self):
        for value in (float("nan"), float("inf"), 99, True):
            with self.subTest(value=value):
                self.options.deadline_unix = value
                self.fail("finite_unexpired_deadline")
        self.allocate.assert_not_called()
        self.assertFalse(Path(self.options.output_dir).exists())

    def test_expired_between_base_and_training_prevents_fit(self):
        self.execute_options()
        self.after_base = lambda: setattr(self, "now", 201)
        evidence = self.fail("finite_unexpired_deadline")
        self.assertIn("actor:BASE", self.log)
        self.assertNotIn("train:D1", self.log)
        self.assertIn("initialized", evidence["objects"])

    def test_existing_output_is_not_modified(self):
        root = Path(self.options.output_dir)
        root.mkdir()
        marker = root / "old"
        marker.write_bytes(b"preserve")
        self.fail("File exists")
        self.assertEqual(list(root.iterdir()), [marker])
        self.assertEqual(marker.read_bytes(), b"preserve")

    def test_runtime_and_visible_device_pins_fail_closed(self):
        self.execute_options()
        os.environ["CUDA_VISIBLE_DEVICES"] = "GPU-another"
        self.fail("visible_device_pin_mismatch")
        self.allocate.assert_not_called()
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(self.options.gpu_uuids)
        self.torch.__version__ = "2.13.0+cpu"
        self.fail("exact_runtime")
        self.token_loader.assert_not_called()

    def test_aborted_conductor_return_is_not_success(self):
        self.execute_options()
        original = self.conductor
        fault = RuntimeError("original actor failure")

        def aborted(**kwargs):
            run = original(**kwargs)
            run.terminal_reason, run.failures = "aborted", (fault,)
            return run

        self.conduct.side_effect = aborted
        evidence = self.fail("conductor_or_base_audit_incomplete")
        self.assertIs(evidence["objects"]["conductor"].failures[0], fault)
        self.assertIn("base_post", evidence["receipt"]["hashes"])
        self.assertFalse((Path(self.options.output_dir) / "RESULT.json").exists())

    def test_actual_base_mutation_is_detected_after_execution(self):
        self.execute_options()
        self.after_conductor = lambda: setattr(self.loaded[1].tensors["weight"], "value", "changed")
        evidence = self.fail("conductor_or_base_audit_incomplete")
        self.assertTrue(any("post_base_drift" in str(error) for error in evidence["errors"]))
        self.assertIn("conductor", evidence["objects"])

    def test_wrapped_base_uses_current_placed_tensors_not_cpu_references(self):
        self.execute_options()
        self.after_conductor = lambda: setattr(self.initialized.model.tensors["base.weight"], "value", "changed")
        evidence = self.fail("conductor_or_base_audit_incomplete")
        self.assertTrue(any("retained_frozen_base_changed" in str(error) for error in evidence["errors"]))
        self.assertEqual(self.initialized.base_references["weight"].value, "frozen-weight")

    def test_disabled_or_merged_adapter_stops_before_atom_call(self):
        self.execute_options()
        self.before_atom = lambda: setattr(self.initialized.model.layer, "disable_adapters", True)
        self.fail("atom_adapter_disabled_or_merged")
        self.assertNotIn("actor:ATOM", self.log)
        self.assertEqual(self.log.count("train:D1"), 1)

    def test_active_atom_checks_every_a_module_including_last(self):
        names = ("first", "middle", "last")
        modules = {name: SimpleNamespace(active_adapters=["default"], disable_adapters=False, merged=False) for name in names}
        seen = []

        def submodule(name):
            seen.append(name)
            return modules[name]

        model = SimpleNamespace(peft_config={"default": object()}, active_adapters=["default"], get_submodule=submodule)
        roster = tuple(source.training.ParameterSpec(name + ".lora_" + side + ".default.weight", (8, 1), "torch.float32")
                       for name in names for side in ("A", "B"))
        initialized = SimpleNamespace(model=model, observation=SimpleNamespace(trainable_roster=roster))
        source._active_atom(initialized)
        self.assertEqual(seen, list(names))
        for field, value in (("disable_adapters", True), ("merged", True), ("active_adapters", ["other"])):
            with self.subTest(field=field):
                seen.clear()
                original = getattr(modules["last"], field)
                setattr(modules["last"], field, value)
                with self.assertRaisesRegex(ValueError, "atom_adapter_disabled_or_merged"):
                    source._active_atom(initialized)
                self.assertEqual(seen, list(names))
                setattr(modules["last"], field, original)

    def test_deadline_inside_train_stops_next_forward_and_exports_partial_observations(self):
        self.execute_options()
        self.after_base = lambda: setattr(self.initialized.model, "after_forward", lambda: setattr(self, "now", 201))
        evidence = self.fail("D1_training_forward")
        self.assertEqual(self.initialized.model.forward_calls, 1)
        self.assertEqual(self.initialized.model.pre_hooks, [])
        self.assertNotIn("checkpoint", self.log)
        self.assertNotIn("actor:ATOM", self.log)
        raw = (Path(self.options.output_dir) / "TRAINING_OBSERVATIONS.json").read_bytes()
        observed = json.loads(raw)
        self.assertEqual((observed["completed_updates"], observed["cursor"], observed["receipt_count"]), (1, 4, 1))
        self.assertEqual(observed["receipts"], source.tokens.retain(evidence["objects"]["trainer"].receipts))
        self.assertTrue(observed["lineage_failed"])
        self.assertIn("NOT_A_CHECKPOINT_NOT_RESUMABLE", observed["kind"])
        self.assertFalse({"adapter", "optimizer", "rng"} & observed.keys())
        failure = json.loads((Path(self.options.output_dir) / "FAILED.json").read_bytes())
        self.assertEqual(failure["training_observations"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(failure["training_observations"]["export"], "COMPLETE")

    def test_native_style_training_error_exports_receipts_and_original_failure(self):
        self.execute_options()
        error = RuntimeError("fake failed second forward")

        def fail_second():
            if self.initialized.model.forward_calls == 2:
                raise error

        self.after_base = lambda: setattr(self.initialized.model, "after_forward", fail_second)
        original = self.conductor

        def abort_return(**kwargs):
            try:
                return original(**kwargs)
            except RuntimeError as caught:
                return SimpleNamespace(terminal_reason="aborted", failures=(SimpleNamespace(error=caught),))

        self.conduct.side_effect = abort_return
        evidence = self.fail("conductor_or_base_audit_incomplete")
        observed = json.loads((Path(self.options.output_dir) / "TRAINING_OBSERVATIONS.json").read_bytes())
        self.assertEqual(observed["completed_updates"], 1)
        self.assertEqual(observed["receipt_count"], 1)
        self.assertTrue(any(item["error"] == str(error) for item in observed["errors"]))
        self.assertIs(evidence["objects"]["conductor"].failures[0].error, error)
        self.assertEqual(self.initialized.model.pre_hooks, [])
        self.assertNotIn("checkpoint", self.log)

    def test_training_observation_storage_failure_is_not_retried_or_marked_success(self):
        self.execute_options()
        original = source._write
        attempted = []

        def fail_export(path, value):
            if Path(path).name == "TRAINING_OBSERVATIONS.json":
                attempted.append(path)
                Path(path).write_bytes(b"partial evidence")
                raise OSError("fake training evidence disk failure")
            return original(path, value)

        with patch.object(source, "_write", side_effect=fail_export):
            evidence = self.fail("training_observations_export_failed")
        self.assertEqual(len(attempted), 1)
        self.assertEqual(Path(attempted[0]).read_bytes(), b"partial evidence")
        self.assertEqual(evidence["receipt"]["training_observations"]["export"], "INCOMPLETE")
        self.assertTrue(any("fake training evidence disk failure" in str(error) for error in evidence["errors"]))
        self.assertFalse((Path(self.options.output_dir) / "RESULT.json").exists())

    def test_initialization_failure_preserves_original_and_partial_artifacts(self):
        error = RuntimeError("fake initialization fault")

        def fail_initialize(model, **kwargs):
            self.initialize_atom(model, **kwargs)
            raise error

        self.initialize.side_effect = fail_initialize
        evidence = self.fail("fake initialization fault")
        self.assertIs(evidence["errors"][0], error)
        self.assertIs(evidence["objects"]["raw_atom"], self.loaded[0])
        self.assertTrue((Path(self.options.output_dir) / "initial/initial_state.pt").exists())
        self.assertFalse(self.cuda.initialized)

    def test_import_has_no_native_side_effects(self):
        spec = importlib.util.spec_from_file_location("fake_entry_import_only", source.__file__)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {spec.name: module, "torch": None, "peft": None, "transformers": None}):
            spec.loader.exec_module(module)
        self.model_loader.assert_not_called()
        self.token_loader.assert_not_called()
        self.assertEqual(self.log, [])


if __name__ == "__main__":
    unittest.main()
