"""Synthetic source replay plus actual CPU-only causal loss/update tests."""

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
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

from gpu import astra_stage2a_outcome_distill as source
from gpu import astra_stage2a_outcome_collect_v2 as collector_v2
from tests.test_astra_stage2a_outcome_collect import SyntheticPolicyActor
from tests.test_composition_birth_stage2a_held import fixtures
from tests.test_composition_birth_stage2a_tokenization import FakeTokenizer as TemplateFixture


class BatchEncoding(dict):
    """Synthetic mapping with the native return-by-default iteration behavior."""


class FakeTokenizer(TemplateFixture):
    def __init__(self, fault=None):
        super().__init__(fault=fault)
        self.return_dict_calls = []

    def apply_chat_template(self, messages, *, return_dict=True, **kwargs):
        result = super().apply_chat_template(messages, **kwargs)
        if kwargs["tokenize"]:
            self.return_dict_calls.append(return_dict)
            return BatchEncoding(input_ids=result) if return_dict else result
        return result


def collected_fixture(worlds, *, master=source.collector.MASTER, guidance=source.collector.GUIDANCE,
                      success=True, success_positions=(0,)):
    outputs = {}
    for position, world in enumerate(worlds):
        for member in world.members:
            actions = [turn.action for turn in member.expected_trace] if success and position in success_positions else ["STOP"]
            for ordinal, raw in enumerate(actions):
                slot = source.collector.native_prepare.screen.primitives.chain_slot(
                    "D1", position, int(member.member[1:]), ordinal)
                seed = source.collector.native_prepare.screen.primitives.decode_seed(master, slot.panel_label, slot.global_ordinal)
                outputs[seed] = raw
    calls, episodes, drafts = [], [], []
    result = dict(completed_episodes=0, whole_chain_successes=0, draft_rows=0)
    with patch.object(source.collector, "MASTER", master), patch.object(source.collector, "GUIDANCE", guidance):
        teacher = source.collector.PublicTeacher(SyntheticPolicyActor(outputs), check=lambda phase: None, emit=calls.append)
        source.collector.collect(worlds, teacher, emit_episode=episodes.append, emit_row=drafts.append,
                                 check=lambda phase: None, summary=result)
    result.update(status="COLLECTION_COMPLETE_DRAFT_ONLY", master=master.decode("ascii"),
        guidance=guidance, guidance_sha256=sha256(guidance.encode()).hexdigest(), physical_calls=len(calls),
        allocation_sha256="synthetic-allocation", base_pre="a" * 64, base_post="a" * 64)
    return source.collector.plain(dict(result=result, episodes=episodes, calls=calls, drafts=drafts))


class OutcomeDistillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worlds = source.held_api.build_chain_panel(role_tokens_by_world=fixtures("dose_chain"))
        cls.collected = collected_fixture(cls.worlds)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def validate(self, data, master=source.collector.MASTER):
        return source.collection_to_student_rows(**data, worlds=self.worlds, source_master=master)

    def write_collection(self, data):
        root = self.root / "collection"
        root.mkdir()
        source.collector.write_json(root / "RESULT.json", data["result"])
        source.collector.write_json(root / "REQUEST.json", {"source": "synthetic"})
        for key, name in (("calls", "CALLS.jsonl"), ("episodes", "EPISODES.jsonl"), ("drafts", "DRAFT_TRAINING_ROWS.jsonl")):
            with (root / name).open("x") as stream:
                for row in data[key]:
                    source.collector.append_json(stream, row)
        return root

    def options(self, collection=None):
        return SimpleNamespace(collection=str(collection or self.root / "collection"), source_label="synthetic-source-A1",
            model_dir="unused-model", output=str(self.root / "run"), gpu_uuid="GPU-synthetic",
            expected_base_sha256="a" * 64, deadline_unix=5000.0)

    def test_exact_success_rows_only_no_authored_target_or_guidance(self):
        before = source._json_bytes(self.collected)
        rows = self.validate(self.collected)
        self.assertEqual(list(rows), self.collected["drafts"])
        self.assertEqual(len(rows), self.collected["result"]["draft_rows"])
        for row in rows:
            call = self.collected["calls"][row["source_call_index"]]
            self.assertEqual(row["assistant"], call["generation"]["raw"])
            self.assertEqual(row["prefix"], call["public_request"]["prefix"])
            self.assertNotIn(source.collector.GUIDANCE, json.dumps(row))
        self.assertEqual(before, source._json_bytes(self.collected))

    def test_partial_and_zero_success_never_admit_rows(self):
        partial = deepcopy(self.collected)
        partial["result"]["completed_episodes"] = 20
        with self.assertRaisesRegex(ValueError, "complete_32"):
            self.validate(partial)
        empty = collected_fixture(self.worlds, success=False)
        with self.assertRaisesRegex(ValueError, "nonempty_success_rows_required_no_fit"):
            self.validate(empty)
        collection = self.write_collection(empty)
        with patch.object(source, "initialize_student") as initialize, self.assertRaisesRegex(ValueError, "no_fit"):
            source.run(self.options(collection), libraries=(), clock=lambda: 100.0)
        initialize.assert_not_called()
        self.assertFalse((self.root / "run" / "RESULT.json").exists())
        self.assertFalse((self.root / "run" / "LOSSES.jsonl").exists())
        self.assertTrue((self.root / "run" / "FAILED.json").exists())

    def test_source_replay_rejects_changed_success_target_prefix_and_call(self):
        cases = [
            lambda data: data["drafts"][0].update(assistant="STOP"),
            lambda data: data["drafts"][0]["prefix"][0].update(content=source.wire.SYSTEM_MESSAGE + source.collector.GUIDANCE),
            lambda data: data["calls"][0]["native"].update(raw="STOP"),
            lambda data: data["calls"][0]["public_request"].update(seed=12),
            lambda data: data["episodes"][0]["score"].update(whole_chain_success=False),
            lambda data: data["episodes"][0].update(selected=False),
        ]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                data = deepcopy(self.collected)
                mutate(data)
                with self.assertRaises(ValueError):
                    self.validate(data)

    def test_successor_source_master_guidance_and_label_are_retained(self):
        master = collector_v2.MASTER
        guidance = collector_v2.GUIDANCE
        data = collected_fixture(self.worlds, master=master, guidance=guidance)
        collection = self.write_collection(data)
        before = {path.name: path.read_bytes() for path in collection.iterdir()}
        allocation = SimpleNamespace(custody_sha256="synthetic-allocation",
            role_tokens_by_world=lambda domain: fixtures("dose_chain"))
        with patch.object(source.prepare, "allocate_source", return_value=allocation) as allocate:
            rows, receipt = source.load_collection(collection, source_label="successor-not-original")
        allocate.assert_called_once_with(master=master)
        self.assertEqual(receipt["source_label"], "successor-not-original")
        self.assertEqual(receipt["source_master"], master.decode())
        self.assertEqual(receipt["source_result"]["guidance"], guidance)
        self.assertEqual(list(rows), data["drafts"])
        tokenized, unused = source.tokenize_rows(rows[:1], FakeTokenizer(), guidance=guidance)
        self.assertEqual(len(tokenized), 1)
        self.assertEqual(master, b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A2")
        self.assertNotEqual(guidance, source.collector.GUIDANCE)
        self.assertEqual(before, {path.name: path.read_bytes() for path in collection.iterdir()})
        with self.assertRaisesRegex(ValueError, "source_master_must_differ"):
            source.collection_to_student_rows(**data, worlds=self.worlds, source_master=source.EVAL_MASTER)

    def test_assistant_and_eot_only_mask_including_historical_assistant(self):
        row = deepcopy(self.collected["drafts"][-1])
        row["prefix"] = [dict(role="system", content=source.wire.SYSTEM_MESSAGE),
            dict(role="user", content="Synthetic public task"), dict(role="assistant", content="STOP"),
            dict(role="user", content="Synthetic public reply")]
        row["assistant"] = "STOP"
        tokenizer = FakeTokenizer()
        tokenized, pad = source.tokenize_rows([row], tokenizer)
        record = tokenized[0]
        self.assertEqual(record.labels[:record.prefix_tokens], (-100,) * record.prefix_tokens)
        supervised = [label for label in record.labels if label != -100]
        self.assertEqual(tokenizer.decode(supervised, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                         "STOP<|im_end|>")
        self.assertEqual(record.labels[-1], -100)
        indexes, selected, batch = source.cyclic_batch(tokenized, 256, pad)
        self.assertEqual(indexes, (0, 0, 0, 0))
        self.assertEqual(len(batch["input_ids"]), 4)
        bad = deepcopy(row)
        bad["prefix"][0]["content"] += source.collector.GUIDANCE
        with self.assertRaises(ValueError):
            source.tokenize_rows([bad], tokenizer)
        with self.assertRaisesRegex(ValueError, "sequence"):
            source.tokenize_rows([row], FakeTokenizer(fault="merge_eos_suffix"))

    def test_native_batchencoding_default_requires_explicit_return_dict_false(self):
        row = deepcopy(self.collected["drafts"][0])
        tokenizer = FakeTokenizer()
        default = tokenizer.apply_chat_template(row["prefix"], tokenize=True, add_generation_prompt=True)
        self.assertIsInstance(default, BatchEncoding)
        self.assertEqual(tuple(default), ("input_ids",))
        tokenized, unused = source.tokenize_rows([row], tokenizer, guidance=source.collector.GUIDANCE)
        self.assertEqual(tokenizer.return_dict_calls, [True, False])
        self.assertEqual(tokenized[0].input_ids[:tokenized[0].prefix_tokens], tuple(default["input_ids"]))

    def test_cycle_and_right_padding_never_train_padding(self):
        rows = (source.StudentRow(1, (2, 3, 4), (-100, 3, -100), (1, 1, 1), 1, 1),
                source.StudentRow(2, (2, 4), (-100, 4), (1, 1), 1, 1),
                source.StudentRow(3, (2,), (-100,), (1,), 1, 0))
        self.assertEqual(source.cyclic_batch(rows, 1, 0)[0], (0, 1, 2, 0))
        indexes, selected, batch = source.cyclic_batch(rows, 2, 0)
        self.assertEqual(indexes, (1, 2, 0, 1))
        self.assertEqual(batch["labels"][0][-1], -100)
        self.assertEqual(batch["attention_mask"][0][-1], 0)
        self.assertEqual(batch["input_ids"][0][-1], 0)

    def test_copy_replay_batch_preserves_first_three_outcome_slots(self):
        rows = tuple(source.StudentRow(index, (2, 3), (-100, 3), (1, 1), 1, 1)
                     for index in range(42))
        outcome_presentations, replay_presentations = 0, 0
        for update in range(1, 257):
            original = source.cyclic_batch(rows[:30], update, 0)[0]
            indexes, selected, batch = source.cyclic_batch(rows, update, 0, outcome_row_count=30)
            self.assertEqual(indexes[:3], original[:3])
            self.assertEqual(indexes[3], 30 + (update - 1) % 12)
            self.assertEqual(tuple(row.source_call_index for row in selected), indexes)
            self.assertTrue(all(labels[0] == -100 for labels in batch["labels"]))
            outcome_presentations += sum(index < 30 for index in indexes)
            replay_presentations += sum(index >= 30 for index in indexes)
        self.assertEqual((outcome_presentations, replay_presentations), (768, 256))

    def test_actual_source_copy_rows_tokenize_without_teacher_or_witness(self):
        from organism_v6.outcome_action_replay import compile_copy_rows

        originals = self.validate(collected_fixture(self.worlds, success_positions=(0, 4)))
        rows, metadata = compile_copy_rows(originals)
        self.assertEqual(len(rows), 12)
        self.assertTrue(metadata)
        tokenized, unused_pad = source.tokenize_rows(rows, FakeTokenizer(), guidance=source.collector.GUIDANCE)
        for row, encoded in zip(rows, tokenized):
            self.assertEqual(encoded.source_call_index, row["source_call_index"])
            self.assertIn(row["assistant"], row["prefix"][-1]["content"])
            self.assertTrue(all(label == -100 for label in encoded.labels[:encoded.prefix_tokens]))
            self.assertEqual(sum(label != -100 for label in encoded.labels), encoded.target_tokens)

    def test_deadlines_and_import_are_bounded_without_native_imports(self):
        for deadline in (float("inf"), 100.0, 5501.0):
            options = self.options()
            options.deadline_unix = deadline
            with self.subTest(deadline=deadline), self.assertRaisesRegex(ValueError, "5400s"):
                source.run(options, clock=lambda: 100.0)
        script = """
import builtins
old = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'peft', 'transformers', 'tokenizers'}:
        raise AssertionError(name)
    return old(name, *args, **kwargs)
builtins.__import__ = guarded
from gpu import astra_stage2a_outcome_distill as source
assert source.SEED == 0 and source.UPDATES == 256 and source.BATCH_SIZE == 4
source.parse_args(['--help'])
"""
        completed = subprocess.run([sys.executable, "-B", "-c", script],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_native_order_checkpoint_then_base_disabled_then_fitted(self):
        options = self.options()
        events, hooks, disabled = [], [], [False]
        model = Mock()
        model.modules.return_value = [model]
        handle = Mock()
        model.register_forward_pre_hook.side_effect = lambda callback: hooks.append(callback) or handle

        @contextmanager
        def disable():
            disabled[0] = True
            yield
            disabled[0] = False

        model.disable_adapter.side_effect = disable

        def save(directory, **kwargs):
            events.append("checkpoint")
            Path(directory).mkdir()
            (Path(directory) / "adapter_model.safetensors").write_bytes(b"synthetic-adapter")
            (Path(directory) / "adapter_config.json").write_text("{}")

        model.save_pretrained.side_effect = save
        torch = SimpleNamespace(__version__=source.tokens.RUNTIME_VERSIONS["torch"], bfloat16="bf16",
            set_num_threads=Mock(), set_num_interop_threads=Mock(), cuda=SimpleNamespace(
                is_initialized=lambda: False, init=Mock(), device_count=lambda: 1,
                get_device_properties=lambda index: SimpleNamespace(name="A100-SXM4-80GB", total_memory=80 * 1024 ** 3)))
        peft = SimpleNamespace(__version__=source.tokens.RUNTIME_VERSIONS["peft"])
        transformers = SimpleNamespace(__version__=source.tokens.RUNTIME_VERSIONS["transformers"],
            AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=object())),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=Mock(return_value=object())))
        initialized = SimpleNamespace(model=model, observation=SimpleNamespace(trainable_roster=(), layer_count=1))
        allocation = object()
        held = SimpleNamespace(receipt_sha256="synthetic-eval", chains={}, interventions={}, canaries=())
        provenance = dict(source_result=dict(base_pre="a" * 64, base_post="a" * 64,
            guidance=source.collector.GUIDANCE), rows_sha256="synthetic-rows")
        state = SimpleNamespace(accounting=source.reducer.Accounting(280, (), 0, 0, 0, 0), issues=(), metrics=None)

        def train(model, rows, *, emit, check, **kwargs):
            events.append("train")
            hooks[0](model, ())
            for update in range(1, 257):
                emit(dict(update_number=update, loss=1.0))

        def evaluate(initialized, tokenizer, held, *, directory, state_id, **kwargs):
            self.assertTrue((self.root / "run" / "adapter" / "TRAINING.json").exists())
            self.assertEqual(disabled[0], state_id == source.BASE_ID)
            events.append(state_id)
            return object()

        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=options.gpu_uuid), \
                patch.object(source, "load_collection", return_value=([self.collected["drafts"][0]], provenance)), \
                patch.object(source.prepare, "allocate_source", return_value=allocation) as allocate, \
                patch.object(source.prepare, "prepare_reduced_held", return_value=held), \
                patch.object(source.tokens, "restore_official_backend", return_value={}), \
                patch.object(source, "tokenize_rows", return_value=((), 0)), \
                patch.object(source, "initialize_student", return_value=initialized), \
                patch.object(source.models, "verify_retained_base", return_value="a" * 64), \
                patch.object(source.training, "_validate_model"), \
                patch.object(source.training, "validate_batches", side_effect=AssertionError("not paired corpus")), \
                patch.object(source.training, "adapter_sha256", return_value="adapter-hash"), \
                patch.object(source, "train_updates", side_effect=train), \
                patch.object(source, "_evaluate", side_effect=evaluate), \
                patch.object(source.reducer, "reduce_base_d1", return_value=SimpleNamespace(
                    reportable=True, criteria_passed=False, criteria=(), base=state, atom_local=state)):
            result = source.run(options, libraries=(torch, peft, transformers), clock=lambda: 100.0)
        self.assertEqual(events, ["train", "checkpoint", source.BASE_ID, source.FITTED_ID])
        model.to.assert_called_once_with("cuda:0")
        model.modules.assert_not_called()
        model.register_forward_pre_hook.assert_called_once()
        allocate.assert_called_once_with(master=source.EVAL_MASTER)
        self.assertEqual(result["status"], "DEV_OUTCOME_SFT_COMPLETE")
        self.assertEqual(result["completed_updates"], 256)
        self.assertEqual(len((self.root / "run" / "LOSSES.jsonl").read_text().splitlines()), 256)
        self.assertEqual(len(result["frozen_base_hashes"]), 4)
        handle.remove.assert_called_once()


@unittest.skipUnless(importlib.util.find_spec("torch"), "CPU torch required for actual loss/gradient tests")
class OutcomeCpuLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls.torch = torch
        torch.set_num_threads(1)

    def test_causal_gradients_only_assistant_eot_and_256_real_batch_four_updates(self):
        torch = self.torch

        class TinyStudent(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.adapter = torch.nn.Parameter(torch.zeros(8, 8))
                self.base = torch.nn.Parameter(torch.ones(3, dtype=torch.bfloat16), requires_grad=False)
                self.register_buffer("rotary", torch.tensor([0.25], dtype=torch.float32))
                self.dropout = torch.nn.Dropout(0.05)
                self.batch_sizes = []

            def forward(self, input_ids, attention_mask, labels, use_cache):
                self.batch_sizes.append(len(input_ids))
                logits = self.dropout(self.adapter[input_ids])
                loss = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 8).float(),
                    labels[:, 1:].reshape(-1), ignore_index=-100)
                return SimpleNamespace(loss=loss)

        rows = (source.StudentRow(12, (1, 2, 3, 4, 5), (-100, -100, 3, 4, -100), (1,) * 5, 2, 2),)
        labels = torch.tensor([rows[0].labels])
        logits = torch.zeros(1, 5, 8, requires_grad=True)
        loss = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 8), labels[:, 1:].reshape(-1), ignore_index=-100)
        loss.backward()
        self.assertEqual((logits.grad.abs().sum(-1) > 0).tolist(), [[False, True, True, False, False]])
        model, receipts = TinyStudent(), []
        frozen, rotary = model.base.detach().clone(), model.rotary.clone()
        with patch.object(source.training, "validate_batches", side_effect=AssertionError("no paired validator")):
            source.train_updates(model, rows, pad_token_id=0, torch=torch, device="cpu",
                                 emit=receipts.append, check=lambda phase: None)
        self.assertEqual([row["update_number"] for row in receipts], list(range(1, 257)))
        self.assertEqual(model.batch_sizes, [4] * 256)
        self.assertLess(receipts[-1]["loss"], receipts[0]["loss"])
        self.assertTrue(torch.equal(model.base, frozen))
        self.assertTrue(torch.equal(model.rotary, rotary))
        self.assertEqual(model.adapter.dtype, torch.float32)
        self.assertEqual(model.rotary.dtype, torch.float32)
        self.assertIsNone(model.base.grad)
        repeated, repeated_receipts = TinyStudent(), []
        source.train_updates(repeated, rows, pad_token_id=0, torch=torch, device="cpu",
                             emit=repeated_receipts.append, check=lambda phase: None)
        self.assertTrue(torch.equal(model.adapter, repeated.adapter))
        self.assertEqual(receipts, repeated_receipts)

    def test_seed_zero_initialization_recipe_preserves_base_and_rotary(self):
        torch = self.torch

        class TinyBase(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = torch.nn.Parameter(torch.ones(2, 2, dtype=torch.bfloat16))
                self.register_buffer("rotary", torch.tensor([0.03125], dtype=torch.float32), persistent=False)
                self.config = SimpleNamespace(model_type="qwen2", use_cache=True, num_hidden_layers=1)
                self.checkpointing = None

            def gradient_checkpointing_enable(self, **kwargs):
                self.checkpointing = kwargs

            def save_pretrained(self, directory, **kwargs):
                Path(directory).mkdir()
                (Path(directory) / "adapter_model.safetensors").write_bytes(b"synthetic")

        def hash_state(state):
            return sha256(source._json_bytes({name: dict(dtype=str(value.dtype), shape=list(value.shape),
                bytes=list(value.detach().contiguous().view(torch.uint8).flatten().tolist()))
                for name, value in state.items()})).hexdigest()

        def wrap(base, config, **kwargs):
            base.register_parameter("adapter", torch.nn.Parameter(torch.rand(2, 2, dtype=torch.float32)))
            return base

        base = TinyBase()
        base_hash = hash_state(dict(base.state_dict(keep_vars=True)))
        rotary = base.rotary.clone()
        peft = SimpleNamespace(LoraConfig=Mock(return_value=object()), get_peft_model=Mock(side_effect=wrap))
        observation = source.models.initial.InitialAdapterObservation(
            (source.training.ParameterSpec("adapter", (2, 2), "torch.float32"),), "synthetic-adapter", 1, "default")
        with tempfile.TemporaryDirectory() as root, patch.object(source, "_state_hash", side_effect=hash_state), \
                patch.object(source.models.initial, "inspect_initial_adapter", return_value=observation), \
                patch.object(torch, "manual_seed", wraps=torch.manual_seed) as manual_seed:
            initialized = source.initialize_student(base, torch=torch, peft=peft,
                directory=Path(root) / "initial", expected_base_sha256=base_hash)
            manual_seed.assert_called_once_with(0)
            self.assertEqual(initialized.receipt["seed"], 0)
            self.assertEqual(initialized.receipt["auxiliary_dtypes"], {"rotary": "torch.float32"})
            self.assertTrue((Path(root) / "initial" / "INITIALIZATION.json").exists())
        self.assertFalse(base.weight.requires_grad)
        self.assertEqual(base.weight.dtype, torch.bfloat16)
        self.assertEqual(base.adapter.dtype, torch.float32)
        self.assertTrue(torch.equal(base.rotary, rotary))
        self.assertFalse(base.config.use_cache)
        self.assertEqual(base.checkpointing, {"gradient_checkpointing_kwargs": {"use_reentrant": False}})
        self.assertEqual(peft.LoraConfig.call_args.kwargs["r"], 8)
        self.assertEqual(peft.LoraConfig.call_args.kwargs["lora_alpha"], 16)
        self.assertEqual(peft.LoraConfig.call_args.kwargs["target_modules"], list(source.training.TARGET_MODULES))
        self.assertTrue(peft.get_peft_model.call_args.kwargs["autocast_adapter_dtype"])


if __name__ == "__main__":
    unittest.main()
