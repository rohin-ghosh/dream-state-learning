"""CPU fixtures only: no model downloads, GPU calls, teacher generation or fits."""
import contextlib
import copy
import io
import json
from pathlib import Path
import random
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from organism_v6 import memory_dose as native
from organism_v6 import memory_preservation as preservation

try:
    import torch
except ImportError:
    torch = None


class AnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        taken = set()
        cls.contents = {"distractor.json": {"text": "Training-only distractor."},
                        preservation.CORPUS: {"corpus": [dict(context="Extra owner Z9Z9.", target="not used")]}}
        for index in range(3):
            owners = native.make_owner_ids(random.Random(81 + index), 64, taken)
            cls.contents[f"banks/bank{index}.json"] = native.generate_bank(index, 81, owners, {}, {}, taken)

    def test_anchor_determinism_split_round_robin_and_no_answers(self):
        state = random.getstate()
        first = preservation.make_anchors(self.contents)
        second = preservation.make_anchors(copy.deepcopy(self.contents))
        self.assertEqual(first, second)
        self.assertEqual(random.getstate(), state)
        rows = first["rows"]
        self.assertEqual(len(rows), 48)
        self.assertEqual(len({row["owner"] for row in rows}), 48)
        reserved = set(preservation.ID_PATTERN.findall(json.dumps(self.contents)))
        self.assertNotIn("Z9Z9", [row["owner"] for row in rows])
        self.assertFalse(reserved.intersection(row["owner"] for row in rows))
        counts = {family: 0 for family in ("near_car", "far_car", "far_bicycle")}
        for index in range(9693):
            counts[rows[index % 48]["family"]] += 1
        self.assertEqual(set(counts.values()), {3231})
        for row in rows:
            self.assertEqual(set(row), {"family", "owner", "prefix"})
            template = native.FRAME_BICYCLE_PREFIX if row["family"] == "far_bicycle" else native.FRAME_PREFIX
            self.assertEqual(row["prefix"], template.format(owner=row["owner"]))
            self.assertFalse(row["prefix"].endswith(" "))
            if row["family"].startswith("far"):
                self.assertTrue(all(sum(left != right for left, right in zip(row["owner"], owner)) >= 2 for owner in reserved))

    def test_native_cue_refs_outside_roster_are_denied(self):
        original = native.build_cues
        def injected(*args, **kwargs):
            return original(*args, **kwargs) + [dict(owner="Y8Y8", cue_id_used="Y8Y9", prompt="heldout")]
        with mock.patch.object(native, "build_cues", side_effect=injected):
            result = preservation.make_anchors(self.contents)
        self.assertNotIn("Y8Y8", [row["owner"] for row in result["rows"]])
        self.assertNotIn("Y8Y9", [row["owner"] for row in result["rows"]])
        self.assertGreaterEqual(result["native_cue_owner_count"], 2)

    def test_anchor_tamper_and_write_new_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "anchors.json"
            original = preservation.make_anchors(self.contents)
            preservation.write_new(path, original)
            self.assertEqual(preservation.validate_anchors(path, self.contents), original)
            with self.assertRaises(FileExistsError):
                preservation.write_new(path, {})
            original["rows"][0]["prefix"] += " red"
            path.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, "anchor content"):
                preservation.validate_anchors(path, self.contents)

    def test_source_hash_refusal_before_anchor_construction(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            path.write_text("{}")
            with mock.patch.object(preservation, "INPUT_HASHES", {"input.json": "0" * 64}):
                with self.assertRaisesRegex(ValueError, "input hash"):
                    preservation.read_source(temporary)

    def test_native_source_pin_and_coefficients(self):
        preservation.check_native()
        with mock.patch.object(preservation, "SOURCE_SHA", "0" * 64), self.assertRaises(ValueError):
            preservation.check_native()
        for value in (0, 0.1, 1.0, 0.37):
            self.assertEqual(preservation.coefficient(value), value)
        for value in (-1, 1.01, "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                preservation.coefficient(value)

    def test_output_directory_refuses_existing_overlap_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            for output in (source, source / "new"):
                with self.assertRaises(ValueError):
                    preservation.new_directory(output, [source])
            linked = root / "linked"
            linked.symlink_to(source, target_is_directory=True)
            with self.assertRaises(ValueError):
                preservation.new_directory(linked / "new", [source])

    def test_execute_required_and_coefficient_has_no_default(self):
        common = ["--source-root", "source", "--anchors", "anchors", "--model", "model", "--out-new", "new"]
        for args in (["cache", *common], ["train", *common], ["train", *common, "--coefficient", "0.1"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                preservation.main(args)

    def test_model_inventory_rejects_other_model_and_adapter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584)
            for name, value in (("config.json", config), ("tokenizer.json", {}), ("tokenizer_config.json", {})):
                preservation.write_new(root / name, value)
            (root / "model.safetensors").write_bytes(b"fixture bytes, not actual weights")
            self.assertIn("model.safetensors", preservation.model_inventory(root))
            (root / "adapter_config.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "adapter files"):
                preservation.model_inventory(root)
            (root / "adapter_config.json").unlink()
            config["num_hidden_layers"] = 2
            (root / "config.json").write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "Qwen2.5"):
                preservation.model_inventory(root)

    def test_encoding_refuses_boundary_truncation_or_token_accounting_drift(self):
        item = dict(input_ids=[1, 2], labels=[1, 2], weight=1.0, n_straddle=0, truncated=False)
        for change in ({}, {"n_straddle": 1}, {"truncated": True}):
            with self.subTest(change=change), mock.patch.object(native, "encode_item", return_value=dict(item, **change)):
                with self.assertRaises(ValueError):
                    preservation.encode_corpus(object(), {"corpus": [{}]})


if torch is not None:
    class TinyLoRA(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(13, 5)
            self.base = torch.nn.Linear(5, 13, bias=False)
            self.projection = torch.nn.Module()
            self.projection.lora_A = torch.nn.ModuleDict({"default": torch.nn.Linear(5, 2, bias=False)})
            self.projection.lora_B = torch.nn.ModuleDict({"default": torch.nn.Linear(2, 13, bias=False)})
            self.dropout = torch.nn.Dropout(0.4)
            self.embedding.requires_grad_(False)
            self.base.requires_grad_(False)
            self.events = []

        def forward(self, input_ids, attention_mask, use_cache=False):
            self.events.append((self.training, torch.is_grad_enabled(), input_ids.tolist()))
            hidden = self.embedding(input_ids)
            update = self.projection.lora_B["default"](self.projection.lora_A["default"](self.dropout(hidden)))
            return SimpleNamespace(logits=self.base(hidden) + update)


@unittest.skipIf(torch is None, "CPU PyTorch required for gradient fixtures")
class PreservationTorchTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.manual_seed(2)
        self.model = TinyLoRA()
        self.model.train()
        self.chunk = [([1, 2, 3, 4], [1, 2, 3, 4], 1.0),
                      ([2, 3, 4], [-100, 3, 4], 2.0),
                      ([3, 5], [3, 5], 0.5), ([4, 1, 2], [4, 1, 2], 1.0)]
        self.batch = preservation.batch_tensors(self.chunk, 0, "cpu")
        self.anchor = torch.tensor([1, 2, 3])

    def optimizer(self, model):
        return torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=1e-4)

    def native_step(self, model, optimizer, batch):
        inputs, labels, attention, weights = batch
        logits = model(input_ids=inputs, attention_mask=attention, use_cache=False).logits
        shift_logits = logits[:, :-1, :].float()
        shift_labels = labels[:, 1:]
        nll = torch.nn.functional.cross_entropy(
            shift_logits.reshape(-1, shift_logits.size(-1)), shift_labels.reshape(-1),
            reduction="none", ignore_index=-100).view(shift_labels.shape)
        valid = (shift_labels != -100).float()
        loss, denominator = native.weighted_token_nll_torch(nll, valid, weights)
        self.assertGreater(denominator.item(), 0)
        loss.backward()
        gradients = {name: parameter.grad.clone() for name, parameter in model.named_parameters() if parameter.requires_grad}
        optimizer.step()
        optimizer.zero_grad()
        return float(loss.detach()), gradients

    def test_zero_matches_native_loss_gradients_updates_rng_over_steps(self):
        reference = copy.deepcopy(self.model)
        reference_optimizer, actual_optimizer = self.optimizer(reference), self.optimizer(self.model)
        reference_state = torch.get_rng_state()
        actual_state = reference_state.clone()
        for step in range(4):
            torch.set_rng_state(reference_state)
            expected_loss, gradients = self.native_step(reference, reference_optimizer, self.batch)
            reference_state = torch.get_rng_state()
            torch.set_rng_state(actual_state)
            captured = {}
            handles = [parameter.register_hook(lambda gradient, key=name: captured.update({key: gradient.clone()}))
                       for name, parameter in self.model.named_parameters() if parameter.requires_grad]
            with mock.patch.object(preservation, "preservation_mode", side_effect=AssertionError("lambda0 entered preservation")), \
                    mock.patch.object(preservation, "full_forward_kl", side_effect=AssertionError("lambda0 computed KL")):
                result = preservation.optimizer_step(self.model, actual_optimizer, self.batch, 0,
                                                       anchor_ids=object(), off_logits=object())
            for handle in handles:
                handle.remove()
            actual_state = torch.get_rng_state()
            self.assertEqual(result["ce"], expected_loss)
            self.assertIsNone(result["kl"])
            self.assertTrue(torch.equal(actual_state, reference_state))
            for name in gradients:
                self.assertTrue(torch.equal(captured[name], gradients[name]), (step, name))
            for expected, actual in zip(reference.parameters(), self.model.parameters()):
                self.assertTrue(torch.equal(expected, actual))
        self.assertEqual([event[0] for event in self.model.events], [True] * 4)

    def test_kl_is_full_forward_teacher_to_student(self):
        teacher = torch.tensor([0.2, -1.0, 1.3])
        student = torch.tensor([0.9, 0.7, -0.8], requires_grad=True)
        loss = preservation.full_forward_kl(student, teacher)
        expected = (teacher.softmax(-1) * (teacher.log_softmax(-1) - student.log_softmax(-1))).sum()
        self.assertTrue(torch.equal(loss, expected))
        self.assertGreater(loss.item(), 0)
        loss.backward()
        self.assertTrue(torch.allclose(student.grad, student.softmax(-1) - teacher.softmax(-1), atol=1e-7))
        self.assertIsNone(teacher.grad)
        self.assertEqual(preservation.full_forward_kl(teacher, teacher).item(), 0)

    def test_kl_rejects_live_teacher_bad_shapes_and_nonfinite(self):
        for student, teacher in ((torch.ones(3), torch.ones(3, requires_grad=True)),
                                  (torch.ones(2), torch.ones(3)),
                                  (torch.tensor([float("inf")]), torch.ones(1))):
            with self.subTest(student=student), self.assertRaises(ValueError):
                preservation.full_forward_kl(student, teacher)

    def test_positive_kl_adds_gradients_preserves_base_modes_rng_and_step_order(self):
        reference = copy.deepcopy(self.model)
        before = {name: parameter.clone() for name, parameter in self.model.named_parameters() if not parameter.requires_grad}
        optimizer = self.optimizer(self.model)
        off = torch.arange(13, dtype=torch.float32)
        state = torch.get_rng_state()
        self.native_step(reference, self.optimizer(reference), self.batch)
        expected_rng = torch.get_rng_state()
        torch.set_rng_state(state)
        result = preservation.optimizer_step(self.model, optimizer, self.batch, 0.1, self.anchor, off)
        self.assertGreater(result["kl"], 0)
        self.assertTrue(torch.equal(torch.get_rng_state(), expected_rng))
        self.assertEqual([event[:2] for event in self.model.events], [(True, True), (False, True)])
        self.assertTrue(self.model.training)
        self.assertTrue(self.model.dropout.training)
        self.assertTrue(any(not torch.equal(left, right) for left, right in zip(self.model.parameters(), reference.parameters())))
        for name, parameter in self.model.named_parameters():
            if name in before:
                self.assertTrue(torch.equal(parameter, before[name]))
                self.assertIsNone(parameter.grad)
        self.assertIsNone(off.grad)
        preservation.assert_lora_only(self.model)

    def test_preservation_mode_restores_rng_and_mixed_modes_even_on_error(self):
        self.model.embedding.eval()
        modes = [module.training for module in self.model.modules()]
        state = torch.get_rng_state()
        with self.assertRaises(RuntimeError):
            with preservation.preservation_mode(self.model):
                self.assertFalse(self.model.dropout.training)
                torch.rand(10)
                raise RuntimeError("mock failure")
        self.assertEqual([module.training for module in self.model.modules()], modes)
        self.assertTrue(torch.equal(state, torch.get_rng_state()))

    def test_base_or_missing_lora_trainability_refused(self):
        preservation.assert_lora_only(self.model)
        self.model.base.weight.requires_grad_(True)
        with self.assertRaises(ValueError):
            preservation.assert_lora_only(self.model)
        self.model.base.weight.requires_grad_(False)
        self.model.projection.lora_A["default"].weight.requires_grad_(False)
        with self.assertRaises(ValueError):
            preservation.assert_lora_only(self.model)

    def test_padding_last_token_and_detached_cache(self):
        self.model.eval()
        rows = [[1, 2, 3], [4, 5]]
        result = preservation.last_logits(self.model, rows, 0, "cpu")
        for index, row in enumerate(rows):
            actual = self.model(torch.tensor([row]), torch.ones(1, len(row)), use_cache=False).logits[0, -1].detach()
            self.assertTrue(torch.allclose(result[index], actual, atol=1e-6, rtol=1e-6))
        self.assertFalse(result.requires_grad)

    def test_empty_nonfinite_loss_aborts_without_optimizer_step(self):
        optimizer = self.optimizer(self.model)
        bad = preservation.batch_tensors([([1, 2], [-100, -100], 1.0)], 0, "cpu")
        with mock.patch.object(optimizer, "step") as step, self.assertRaises(ValueError):
            preservation.optimizer_step(self.model, optimizer, bad, 0)
        step.assert_not_called()

    def test_cache_hash_dtype_shape_model_and_token_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            anchors = root / "anchors.json"
            preservation.write_new(anchors, {"fixture": True})
            rows = [[1, 2]] * 48
            logits = torch.randn(48, 13)
            torch.save(logits, root / "off_logits.pt")
            metadata = dict(anchors_sha256=preservation.digest(anchors), input_ids=rows,
                            model_files={"config.json": "fixture"}, native_source_sha256=preservation.SOURCE_SHA,
                            dtype="torch.float32", temperature=1.0, adapter=None, position="last input token",
                            logits_sha256=preservation.digest(root / "off_logits.pt"))
            preservation.write_new(root / "cache.json", metadata)
            actual, _ = preservation.verify_cache(root, anchors, rows, metadata["model_files"], 13)
            self.assertTrue(torch.equal(actual, logits))
            for changed_rows, inventory, vocab in (([[3]] * 48, metadata["model_files"], 13),
                                                    (rows, {}, 13), (rows, metadata["model_files"], 12)):
                with self.subTest(vocab=vocab), self.assertRaises(ValueError):
                    preservation.verify_cache(root, anchors, changed_rows, inventory, vocab)
            torch.save(logits.half(), root / "off_logits.pt")
            with self.assertRaisesRegex(ValueError, "hash"):
                preservation.verify_cache(root, anchors, rows, metadata["model_files"], 13)
            metadata["logits_sha256"] = preservation.digest(root / "off_logits.pt")
            (root / "cache.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "dtype"):
                preservation.verify_cache(root, anchors, rows, metadata["model_files"], 13)

    def test_full_training_loop_order_count_no_cache_zero_and_write_new(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            anchor_path = root / "anchors.json"
            preservation.write_new(anchor_path, {"fixture": True})
            model = self.model
            model.config = SimpleNamespace(vocab_size=13)
            model.save_pretrained = mock.Mock()
            tokenizer = SimpleNamespace(pad_token="PAD", eos_token="EOS", pad_token_id=0)
            transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=mock.Mock(return_value=tokenizer)),
                AutoModelForCausalLM=SimpleNamespace(from_pretrained=mock.Mock(return_value=model)))
            peft = SimpleNamespace(LoraConfig=mock.Mock(), get_peft_model=mock.Mock(return_value=model))
            corpus = dict(sha="fixture", items_sha="fixture", ordering="chronological", writer="occurrences",
                          representation="frames", shuffled=False)
            chunks = [([index % 12 + 1, 1], [index % 12 + 1, 1], 1.0) for index in range(12924)]
            steps = []
            def fake_step(current, optimizer, batch, strength, anchor_ids, off_logits):
                self.assertIs(current, model)
                self.assertEqual(strength, 0)
                self.assertIsNone(anchor_ids)
                self.assertIsNone(off_logits)
                steps.append(batch)
                last = len(steps) == 9693
                return dict(ce=1.0, kl=None, objective=1.0, tokens=749985 - 9692 if last else 1,
                            supervised_tokens=711213 - 9692 if last else 1, seconds=0.01)
            with contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.dict(sys.modules, {"transformers": transformers, "peft": peft}))
                stack.enter_context(mock.patch.object(preservation, "read_source", return_value={preservation.CORPUS: corpus}))
                stack.enter_context(mock.patch.object(preservation, "validate_anchors", return_value={"rows": []}))
                stack.enter_context(mock.patch.object(preservation, "model_inventory", return_value={"fixture": "pins"}))
                stack.enter_context(mock.patch.object(preservation, "encode_corpus", return_value=chunks))
                stack.enter_context(mock.patch.object(preservation, "batch_tensors", side_effect=lambda chunk, pad, device: chunk))
                stack.enter_context(mock.patch.object(preservation, "verify_cache", side_effect=AssertionError("zero cache")))
                stack.enter_context(mock.patch.object(preservation, "optimizer_step", side_effect=fake_step))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                result = preservation.train(root / "source", anchor_path, None, root / "model", root / "output", 0)
                with self.assertRaisesRegex(ValueError, "output must be new"):
                    preservation.train(root / "source", anchor_path, None, root / "model", root / "output", 0)
            self.assertEqual(result["steps"], 9693)
            self.assertEqual(result["tokens"], 749985)
            self.assertEqual(result["supervised_tokens"], 711213)
            self.assertEqual(result["anchor_forward_count"], 0)
            self.assertEqual(result["anchor_visits"], [0] * 48)
            self.assertIsNone(result["mean_kl"])
            self.assertEqual(steps, [chunks[offset:offset + 4] for epoch in range(3) for offset in range(0, len(chunks), 4)])
            self.assertEqual((root / "output/DONE").read_text(), "ok\n")
            self.assertEqual(len((root / "output/losses.jsonl").read_text().splitlines()), 9693)
            model.save_pretrained.assert_called_once()
            peft.LoraConfig.assert_called_once_with(r=8, lora_alpha=16, lora_dropout=0.05, bias="none", target_modules=native.LORA_TARGETS)


if __name__ == "__main__":
    unittest.main()
