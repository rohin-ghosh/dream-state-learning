"""Pure archived core/encoder and toy models only; no torch/HF/native execution."""
from copy import deepcopy
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("access_probe_tested", "/tmp/astra_l2_access_high_seed2_20260913.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)
SOURCE = probe.frozen_source("/tmp/astra_l2_lr_source_20260913_attempt1")
runtime = probe.load_module("_access_test_runtime", SOURCE / "gpu/astra_l2_public_record_dev.py")
core = probe.load_module("_access_test_core", SOURCE / "organism_v6/l2_public_record_dev.py")
trainer = probe.load_module("_access_test_trainer", SOURCE / "organism_v6/train_adapter_v3.py")
WORLD = core.build_world(2026091301, 2026091302)
PUBLIC = core.public_view(WORLD)


class ToyTokenizer:
    eos_token, eos_token_id, pad_token_id = "<|im_end|>", 2, 0
    chat_template = "toy-boundary-template-not-native"

    def encode(self, text, add_special_tokens=False):
        mappings = ((self.eos_token, [2]), (PUBLIC.actions[0], [500, 501, 510] + list(range(530, 538))),
                    (PUBLIC.actions[1], [500, 501, 520] + list(range(540, 550))))
        ids = []
        while text:
            match = next(((word, tokens) for word, tokens in mappings if text.startswith(word)), None)
            if match:
                word, tokens = match
                ids.extend(tokens)
                text = text[len(word):]
            else:
                ids.append(ord(text[0]) + 100)
                text = text[1:]
        return ids

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + self.eos_token + "\n"
                       for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class ToyPublicHelper:
    def render(self, tokenizer, messages):
        text = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return dict(rendered_prompt=text, prompt_token_ids=tokenizer.encode(text), actual_system_text=messages[0]["content"])


class ToyModel:
    def __init__(self):
        self.calls = 0

    def forward(self, candidate):
        self.calls += 1
        count = len(candidate["target_ids"])
        decision_loss = .2 if candidate["action"] == PUBLIC.actions[0] else .18
        return [-.01, -.01] + [-decision_loss] * (count - 3) + [-.01]


def cases():
    return [dict(view=view, slot_id=slot.slot_id, slot_index=slot.index,
                 candidates=[probe.candidate_encoding(runtime, ToyTokenizer(), ToyPublicHelper(),
                     runtime.messages(core.action_prompt(PUBLIC, slot.slot_id, view=view)), action, "") for action in PUBLIC.actions])
            for view in probe.VIEWS for slot in PUBLIC.slots]


def off_receipt():
    inputs = cases()
    rows = probe.evaluate_cases(inputs, ToyModel().forward, lambda: None)
    return dict(schema=probe.SCHEMA, diagnostic_only=True, claim=probe.CLAIM, state="OFF", pid=10001,
                started=1., ended=2., deadline_unix=401., source_files=probe.SOURCE_FILES,
                diagnostic_sha256=probe.digest(probe.__file__), plan_sha256=probe.PLAN_PIN, seal_sha256=probe.SEAL_PIN,
                collection_sha256=probe.COLLECTION_PIN, base_sha256=probe.BASE_PIN, candidate_sha256=None,
                adapter_files=None, tensor_identity=None, forwards=64, updates=0, rows=rows, cases_sha256=probe.value_hash(inputs))


class AccessTests(unittest.TestCase):
    def test_tuner_route_checks_ignore_transformers_control_method(self):
        class TunerLayer:
            disable_adapters = False
            merged = False
            active_adapters = ["default"]
        base = SimpleNamespace(disable_adapters=lambda: None)
        layer = TunerLayer()
        model = SimpleNamespace(active_adapters=["default"], modules=lambda: [base, layer])
        self.assertEqual(probe.verify_adapter_routes(model, TunerLayer), 1)

    def test_actual_tuner_disabled_merged_wrong_or_nonbool_rejected(self):
        class TunerLayer:
            disable_adapters = False
            merged = False
            active_adapters = ["default"]
        for field, value in (("disable_adapters", True), ("disable_adapters", 0), ("merged", True),
                             ("merged", lambda: False), ("active_adapters", ["other"])):
            with self.subTest(field=field, value=value):
                layer = TunerLayer()
                setattr(layer, field, value)
                model = SimpleNamespace(active_adapters=["default"], modules=lambda: [layer])
                with self.assertRaisesRegex(ValueError, "LoRA inactive"):
                    probe.verify_adapter_routes(model, TunerLayer)

    def test_missing_tuners_or_wrong_model_route_rejected(self):
        class TunerLayer:
            pass
        for adapters in (["default"], ["other"]):
            with self.subTest(adapters=adapters):
                model = SimpleNamespace(active_adapters=adapters, modules=lambda: [])
                with self.assertRaises(ValueError):
                    probe.verify_adapter_routes(model, TunerLayer)

    def test_frozen_source_and_collection_metadata(self):
        self.assertEqual(probe.frozen_source(SOURCE), SOURCE)
        metadata = probe.collection_metadata("/tmp/l2_lr_seed2_high_20260913_attempt1_collected")
        self.assertEqual(metadata["work"], dict(calls=128, fits=3, updates=100))

    def test_unequal_lengths_mask_eos_and_first_divergence(self):
        row = cases()[0]
        self.assertEqual([len(candidate["target_ids"]) for candidate in row["candidates"]], [12, 14])
        model = ToyModel()
        row["candidates"] = [dict(candidate, logprobs=model.forward(candidate)) for candidate in row["candidates"]]
        for truth in (0, 1):
            metrics = probe.pair_metrics(row, truth)
            self.assertEqual(metrics["first_divergent_index"], 2)
            self.assertEqual(metrics["losses"]["common"]["tokens"], 3)
            self.assertEqual(metrics["losses"]["decision"]["tokens"], (9, 11)[truth])
            self.assertEqual(metrics["losses"]["full"]["tokens"], (12, 14)[truth])
            self.assertEqual(metrics["losses"]["eos"]["tokens"], 1)
            self.assertGreater(metrics["full_margin_action0_minus_action1"], 0)
            self.assertLess(metrics["first_margin_action0_minus_action1"], 0)
            self.assertLess(metrics["mean_logprob_margin_action0_minus_action1"], 0)
            self.assertEqual([item["tokens_including_eos"] for item in metrics["candidates"]], [12, 14])
        for candidate in row["candidates"]:
            self.assertEqual([value for value in candidate["labels"] if value != -100], candidate["target_ids"])
            self.assertEqual(candidate["target_ids"][-1], ToyTokenizer.eos_token_id)
            self.assertEqual(candidate["labels"][-1], -100)

    def test_optional_newline_is_scored_not_stripped(self):
        candidate = probe.candidate_encoding(runtime, ToyTokenizer(), ToyPublicHelper(),
                    runtime.messages(core.action_prompt(PUBLIC, PUBLIC.slots[0].slot_id)), PUBLIC.actions[0], "\n")
        self.assertEqual(len(candidate["target_ids"]), 13)
        self.assertEqual(candidate["target_ids"][-2:], [ord("\n") + 100, 2])

    def test_bad_template_and_truncation_rejected(self):
        message = runtime.messages(core.action_prompt(PUBLIC, PUBLIC.slots[0].slot_id))
        for suffix in ("\n\n", " "):
            with self.assertRaises(ValueError):
                probe.candidate_encoding(runtime, ToyTokenizer(), ToyPublicHelper(), message, PUBLIC.actions[0], suffix)
        with self.assertRaisesRegex(ValueError, "truncation"):
            probe.candidate_encoding(runtime, ToyTokenizer(), ToyPublicHelper(), runtime.messages("x" * 1100), PUBLIC.actions[0], "")
        class BrokenTokenizer(ToyTokenizer):
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
                value = super().apply_chat_template(messages, tokenize, add_generation_prompt)
                return value[:-1] if tokenize and not add_generation_prompt else value
        with self.assertRaises(ValueError):
            probe.candidate_encoding(runtime, BrokenTokenizer(), ToyPublicHelper(), message, PUBLIC.actions[0], "")

    def test_exact_forward_budget_and_no_generation_or_updates(self):
        model, emissions = ToyModel(), []
        rows = probe.evaluate_cases(cases(), model.forward, lambda: None, emissions.append)
        self.assertEqual((model.calls, len(rows), len(emissions)), (64, 32, 32))
        with self.assertRaisesRegex(ValueError, "coverage"):
            probe.evaluate_cases(cases()[:-1], model.forward, lambda: None)
        self.assertEqual(model.calls, 64)
        self.assertFalse(hasattr(model, "generate"))

    def test_mock_hf_forward_uses_causal_shift_no_labels_or_generation(self):
        candidate = cases()[0]["candidates"][1]
        torch = MagicMock()
        ids = SimpleNamespace(shape=(1, len(candidate["input_ids"])))
        targets = MagicMock()
        torch.tensor.side_effect = [ids, targets]
        torch.isfinite.return_value.all.return_value.item.return_value = True
        logits = MagicMock(ndim=3, shape=(1, len(candidate["input_ids"]), 2000))
        model = MagicMock(return_value=SimpleNamespace(logits=logits))
        model.parameters.return_value = iter([SimpleNamespace(device="toy-device")])
        expected = [-.1] * len(candidate["target_ids"])
        torch.log_softmax.return_value.gather.return_value.squeeze.return_value.cpu.return_value.tolist.return_value = expected
        self.assertEqual(probe.hf_forward(model, candidate, torch_api=torch), expected)
        logits.__getitem__.assert_called_once_with((0, [position - 1 for position in candidate["target_positions"]], slice(None)))
        self.assertEqual(set(model.call_args.kwargs), {"input_ids", "attention_mask", "use_cache"})
        self.assertIs(model.call_args.kwargs["use_cache"], False)
        model.generate.assert_not_called()
        torch.inference_mode.assert_called_once_with()
        self.assertNotIn("torch", sys.modules)

    def test_mock_hf_forward_rejects_nonfinite_logits(self):
        candidate = cases()[0]["candidates"][0]
        torch = MagicMock()
        torch.tensor.return_value = SimpleNamespace(shape=(1, len(candidate["input_ids"])))
        torch.isfinite.return_value.all.return_value.item.return_value = False
        model = MagicMock(return_value=SimpleNamespace(logits=MagicMock(ndim=3, shape=(1, len(candidate["input_ids"]), 2000))))
        model.parameters.return_value = iter([SimpleNamespace(device="toy-device")])
        with self.assertRaisesRegex(ValueError, "nonfinite decision logits"):
            probe.hf_forward(model, candidate, torch_api=torch)
        torch.log_softmax.assert_not_called()

    def test_nonfinite_scores_and_deadline_fail_closed(self):
        for value in (math.nan, math.inf, -math.inf, True, .1):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "logprobs"):
                probe.evaluate_cases(cases(), lambda candidate: [value] * len(candidate["target_ids"]), lambda: None)
        model = ToyModel()
        def expired():
            raise ValueError("expired")
        with self.assertRaisesRegex(ValueError, "expired"):
            probe.evaluate_cases(cases(), model.forward, expired)
        self.assertEqual(model.calls, 0)

    def test_ties_not_arbitrarily_assigned_and_no_single_token_assumption(self):
        row = cases()[0]
        row["candidates"] = [dict(candidate, logprobs=[0.] * len(candidate["target_ids"])) for candidate in row["candidates"]]
        result = probe.pair_metrics(row, 0)
        self.assertIsNone(result["full_choice"])
        self.assertIsNone(result["first_choice"])
        self.assertFalse(result["full_correct"])
        self.assertEqual(result["losses"]["decision"]["tokens"], 9)

    def test_tensor_records_accept_exact_converted_values_reject_drift(self):
        source = {"base.model.q_proj.lora_A.weight": dict(shape=[8, 32], dtype="torch.float32", sha256="a" * 64)}
        converted = {name: dict(record, dtype="torch.bfloat16", sha256="b" * 64) for name, record in source.items()}
        self.assertEqual(probe.bind_tensor_records(source, converted, deepcopy(converted))["actual"], converted)
        for actual in ({}, {name: dict(record, sha256="c" * 64) for name, record in converted.items()},
                       {name: dict(record, shape=[True, 32]) for name, record in converted.items()}):
            with self.assertRaises(ValueError):
                probe.bind_tensor_records(source, converted, actual)
        with self.assertRaisesRegex(ValueError, "non-LoRA"):
            probe.bind_tensor_records({"base.weight": next(iter(source.values()))},
                                      {"base.weight": next(iter(converted.values()))}, {"base.weight": next(iter(converted.values()))})

    def test_off_receipt_roundtrip_and_pin_mask_work_rejections(self):
        receipt = off_receipt()
        probe.validate_receipt(receipt, core, WORLD)
        for field, value in (("diagnostic_sha256", "0" * 64), ("plan_sha256", "0" * 64), ("updates", True),
                             ("updates", 1), ("forwards", 65), ("adapter_files", {}), ("deadline_unix", 402.)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.validate_receipt(dict(receipt, **{field: value}), core, WORLD)
        for key, value in (("logprobs", [math.nan] * 12), ("target_positions", [0] * 12), ("labels", [False])):
            broken = deepcopy(receipt)
            broken["rows"][0]["candidates"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                probe.validate_receipt(broken, core, WORLD)

    def test_three_worker_state_pid_encoding_and_envelope_rejections(self):
        receipt = off_receipt()
        receipts = [dict(receipt, state=state, pid=10001 + index) for index, state in enumerate(probe.CANDIDATES)]
        for broken, message in ((receipts[:2], "exact OFF"),
                                ([dict(item, pid=10001) for item in receipts], "fresh distinct"),
                                ([receipts[0], receipts[1], dict(receipts[2], cases_sha256="a" * 64)], "cross-worker"),
                                ([receipts[0], receipts[1], dict(receipts[2], ended=1202.)], "1200-second")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                probe.reduce_receipts(broken, core, WORLD)
        with self.assertRaisesRegex(ValueError, "pin drift"):
            probe.reduce_receipts(receipts, core, WORLD)

    def test_pure_summary_separates_access_gap_and_length_metrics(self):
        base = off_receipt()
        receipts = [dict(deepcopy(base), state=state) for state in probe.CANDIDATES]
        trained = receipts[2]
        for row in trained["rows"]:
            if row["view"] == "train":
                truth = PUBLIC.actions.index(WORLD.success_actions[row["slot_index"]])
                for index, candidate in enumerate(row["candidates"]):
                    candidate["logprobs"][2] = -.001 if index == truth else -5.
        result = probe.summarize_scores(receipts, core, WORLD)
        self.assertEqual((result["forwards"], result["updates"]), (192, 0))
        self.assertIsNone(result["scientific_pass"])
        self.assertEqual(result["states"]["OFF"]["train"]["first"], dict(old_correct=4, new_correct=4, ties=0))
        self.assertEqual(result["states"]["fit2_PROMOTE"]["train"]["first"], dict(old_correct=8, new_correct=8, ties=0))
        self.assertEqual(result["states"]["fit2_PROMOTE"]["readout"]["first"], dict(old_correct=4, new_correct=4, ties=0))
        self.assertEqual(sum(row["train_correct_readout_not"] for row in result["states"]["fit2_PROMOTE"]["access_contrast"]), 8)
        self.assertIn("single-decision-token", result["interpretation"])
        self.assertIn("unmeasured reference", result["interpretation"])

    def test_native_gate_and_external_output_protection(self):
        with self.assertRaisesRegex(ValueError, "allow-native"):
            probe.worker("/no/source", "/no/collection", "OFF", "/no/output", 1.)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "overlaps"):
                probe.external_output(root / "out.json", (root,))
            output = probe.external_output(root / "out.json", (root / "input.json",))
            output.write_bytes(b"old")
            with self.assertRaisesRegex(ValueError, "fresh"):
                probe.external_output(output, ())
            linked = root / "link"
            linked.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                probe.external_output(linked / "new.json", ())


class ArchiveBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="l2-access-toy-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plan = dict(root=str(self.root), seeds=dict(runtime.SEEDS, learner=2),
                         spec=dict(learner_seed=2, learning_rate=1e-4), config=dict(seed=2, lr=1e-4), learning_rate=1e-4)
        self.api = SimpleNamespace(**{name: getattr(runtime, name) for name in
            ("read", "encode_training", "legal_action", "messages", "token_ids", "GENERIC_SYSTEM",
             "plan_learner_seed", "plan_learning_rate")})
        self.api.read_stage = lambda plan, stage: dict(candidate_sha256=probe.CANDIDATES[stage], admitted=8 if stage == "fit1" else 16)
        captures = []
        for block, stage in ((1, "fit1"), (2, "fit2_PROMOTE")):
            lineage = "SHARED" if block == 1 else "PROMOTE"
            episodes = []
            for slot in PUBLIC.slots[(block - 1) * 8:block * 8]:
                action = core.make_receipt(PUBLIC, slot.slot_id, "action", PUBLIC.actions[0].encode(),
                                          sequence=100 + slot.index * 3, lineage=lineage)
                outcome = core.feedback(WORLD, action, sequence=action.sequence + 1)
                target = PUBLIC.actions[0 if outcome.raw == b"SUCCESS" else 1]
                record = core.make_receipt(PUBLIC, slot.slot_id, "record", target.encode(), sequence=action.sequence + 2,
                                          lineage=lineage, previous=outcome)
                episodes.append(core.Episode(action, outcome, record))
            captures.append(core.capture_block(PUBLIC, block, lineage, tuple(episodes)))
            corpus = core.compile_corpus(PUBLIC, tuple(captures), expected_hashes=tuple(core.digest(capture) for capture in captures))
            directory = self.root / "run" / stage / "data"
            runtime.write(directory / "corpus.json", core.to_data(corpus))
            runtime.write(directory / "training.json", runtime.encode_training(core, PUBLIC, corpus, ToyTokenizer(), trainer, ToyPublicHelper(), learner_seed=2))
        calls = {view: [dict(slot_id=slot.slot_id, messages=runtime.messages(core.action_prompt(PUBLIC, slot.slot_id, view=view)),
                    native=ToyPublicHelper().render(ToyTokenizer(), runtime.messages(core.action_prompt(PUBLIC, slot.slot_id, view=view))))
                       for slot in PUBLIC.slots] for view in ("wake", "train", "readout")}
        runtime.write(self.root / "calls.json", calls)
        for view in probe.VIEWS:
            for index, slot in enumerate(PUBLIC.slots):
                stages = ("baseline", "report1_PROMOTE", "report2_PROMOTE") if view == "readout" else (
                    "wake1" if index < 8 else "wake2_PROMOTE",)
                call_index = index if view == "readout" else (index % 8) * 2
                for stage in stages:
                    directory = self.root / "run" / stage / "data"
                    runtime.write(directory / f"{call_index:02d}.request.json", dict(slot_id=slot.slot_id,
                        kind="readout" if view == "readout" else "action", messages=calls[view][index]["messages"]))
                    native = calls[view][index]["native"]
                    runtime.write(directory / f"{call_index:02d}.response.json", dict(native=native, returned_prompt_token_ids=native["prompt_token_ids"]))

    def build(self):
        return probe.build_cases(self.api, core, trainer, ToyPublicHelper(), self.plan, WORLD, ToyTokenizer(), self.root)

    def test_archived_training_masks_and_exact_captured_prompts_roundtrip(self):
        self.assertEqual(self.build(), cases())

    def test_archived_training_mask_change_rejected(self):
        path = self.root / "run/fit1/data/training.json"
        value = runtime.read(path)
        value["encoding"][0]["labels"][-2] = -100
        path.write_bytes(runtime.encoded(value))
        with self.assertRaisesRegex(ValueError, "archived full assistant encoding"):
            self.build()

    def test_original_held_prompt_change_rejected(self):
        path = self.root / "run/report1_PROMOTE/data/00.request.json"
        value = runtime.read(path)
        value["messages"][1]["content"] += " altered"
        path.write_bytes(runtime.encoded(value))
        with self.assertRaisesRegex(ValueError, "captured request drift"):
            self.build()


    def test_seed2_positive_forwards_seed_to_exact_encoder(self):
        calls_seen = []
        def encode(*args, learner_seed):
            calls_seen.append(learner_seed)
            return runtime.encode_training(*args, learner_seed=learner_seed)
        self.api.encode_training = encode
        self.assertEqual(self.build(), cases())
        self.assertEqual(calls_seen, [2, 2])

    def test_seed0_encoding_rejected_without_repair(self):
        path = self.root / "run/fit1/data/training.json"
        corpus = core.from_data(runtime.read(path.parent / "corpus.json"), expected_type=core.Corpus)
        encoded = runtime.encode_training(core, PUBLIC, corpus, ToyTokenizer(), trainer, ToyPublicHelper(), learner_seed=0)
        path.write_bytes(runtime.encoded(encoded))
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "archived full assistant encoding"):
            self.build()
        self.assertEqual(path.read_bytes(), before)

    def test_seed0_plan_rejected_before_encoding(self):
        self.plan["spec"]["learner_seed"] = 0
        self.plan["config"]["seed"] = 0
        self.plan["seeds"]["learner"] = 0
        with self.assertRaisesRegex(ValueError, "seed2-high plan binding"):
            self.build()

    def test_seed2_plan_internal_disagreement_rejected(self):
        self.plan["config"]["seed"] = 0
        with self.assertRaisesRegex(ValueError, "config learner_seed"):
            self.build()

    def test_wrong_learning_rate_rejected(self):
        self.plan["spec"]["learning_rate"] = 3e-5
        self.plan["config"]["lr"] = 3e-5
        self.plan["learning_rate"] = 3e-5
        with self.assertRaisesRegex(ValueError, "seed2-high plan binding"):
            self.build()

    def test_epoch_order_tamper_rejected_with_masks_unchanged(self):
        path = self.root / "run/fit1/data/training.json"
        data = runtime.read(path)
        data["epoch_order"][0].reverse()
        path.write_bytes(runtime.encoded(data))
        with self.assertRaisesRegex(ValueError, "archived full assistant encoding"):
            self.build()


class AlgorithmReuseTests(unittest.TestCase):
    def test_original_algorithms_remain_ast_identical(self):
        import ast
        import hashlib
        original = Path("/tmp/astra_l2_access_probe_20260913_v2.py").read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), "a38a089fae5b09b53415655dd8e5346dfbb0f597f34b35cd49921a98b50e22c1")
        trees = [ast.parse(source) for source in (original, Path(probe.__file__).read_bytes())]
        functions = [{node.name: ast.dump(node, include_attributes=False) for node in tree.body
                      if isinstance(node, ast.FunctionDef)} for tree in trees]
        changed = {name for name in functions[0] if functions[0][name] != functions[1][name]}
        self.assertEqual(changed, {"build_cases", "collection_metadata", "main"})
        self.assertEqual(set(functions[0]), set(functions[1]))


import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("controller", "/tmp/controller_astra_l2_access_high_seed2_20260913.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        allocation = patch.object(controller, "check_allocation_binding")
        allocation.start()
        self.addCleanup(allocation.stop)

    def test_no_permission_before_side_effect(self):
        with self.assertRaisesRegex(ValueError, "permission"):
            controller.controller(SimpleNamespace(allow_gpu=False))

    def test_no_controller_cuda_reservation(self):
        with patch.dict(controller.os.environ, CUDA_VISIBLE_DEVICES="3"):
            with self.assertRaisesRegex(ValueError, "reserve"):
                controller.controller(SimpleNamespace(allow_gpu=True))

    def test_write_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            controller.write(path, {"status": "first"})
            with self.assertRaises(FileExistsError):
                controller.write(path, {"status": "replacement"})

    def test_pin_failure_before_precheck(self):
        with patch.object(controller, "digest", return_value="wrong"), patch.object(controller.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "precheck changed"):
                controller.precheck(SimpleNamespace(precheck="fixture"), Path("unused"))
            run.assert_not_called()

    def test_failed_precheck_rejected_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "precheck.json"
            with patch.object(controller, "digest", return_value=controller.PRECHECK_PIN), patch.object(
                controller.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="occupied", stderr="")):
                with self.assertRaisesRegex(ValueError, "check failed"):
                    controller.precheck(SimpleNamespace(precheck="fixture"), output)
            self.assertTrue(output.exists())

    def test_refuse_kill_wrong_identity(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        with patch.object(controller, "identity", return_value={"pid": 124}), patch.object(controller.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "unbound"):
                controller.stop_owned(process, {"pid": 123, "pgid": 123, "start_ticks": 5})
            kill.assert_not_called()

    def test_finished_process_not_killed(self):
        process = Mock(pid=123)
        process.poll.return_value = 0
        with patch.object(controller.os, "killpg") as kill:
            controller.stop_owned(process, {})
            kill.assert_not_called()

    def test_owned_timeout_cleanup(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("fixture", 10), 0]
        bound = dict(pid=123, pgid=123, start_ticks=5)
        with patch.object(controller, "identity", return_value=bound), patch.object(controller.os, "killpg") as kill:
            controller.stop_owned(process, bound)
            self.assertEqual(kill.call_count, 2)
            self.assertTrue(all(call.args[0] == 123 for call in kill.call_args_list))

    def test_budget_exhaustion_prevents_launch(self):
        with patch.object(controller.time, "time", return_value=100), patch.object(controller.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "budget"):
                controller.run_worker(None, None, "OFF", 150)
            launch.assert_not_called()

    def test_environment_freezes_network_and_controller_device(self):
        env = controller.environment()
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(controller.environment(controller.GPU_UUID)["CUDA_VISIBLE_DEVICES"], controller.GPU_UUID)


class FreshAllocationTests(unittest.TestCase):
    def test_boot_and_lease_checked_without_native_calls(self):
        options = SimpleNamespace(expected_boot_id="11111111-1111-1111-1111-111111111111", lease_end_unix=50000)
        with patch.object(controller, "BOOT_ID_PATH", SimpleNamespace(read_text=lambda **kwargs: options.expected_boot_id)), patch.object(controller.time, "time", return_value=100):
            controller.check_allocation_binding(options)
            options.lease_end_unix = 200
            with self.assertRaisesRegex(ValueError, "lease margin"):
                controller.check_allocation_binding(options)
            options.lease_end_unix = float("inf")
            with self.assertRaisesRegex(ValueError, "lease margin"):
                controller.check_allocation_binding(options)
        with patch.object(controller, "BOOT_ID_PATH", SimpleNamespace(read_text=lambda **kwargs: "other")):
            with self.assertRaisesRegex(ValueError, "boot binding"):
                controller.check_allocation_binding(options)

    def test_fresh_vacancy_required_even_on_zero_exit(self):
        import json
        receipt = dict(gpu_index=3, gpu_uuid=controller.GPU_UUID, checked_unix=100,
                       compute_processes=[], matching_reservations=[], unresolved_same_user=[])
        variants = [({}, True), ({"checked_unix": 99}, False), ({"gpu_uuid": "other"}, False),
                    ({"compute_processes": [123]}, False), ({"matching_reservations": [456]}, False),
                    ({"unresolved_same_user": [789]}, False)]
        for changes, expected in variants:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temporary:
                result = SimpleNamespace(returncode=0, stdout=json.dumps(dict(receipt, **changes)), stderr="")
                with patch.object(controller, "check_allocation_binding"), patch.object(controller.time, "time", return_value=100), patch.object(controller, "digest", return_value=controller.PRECHECK_PIN), patch.object(controller.subprocess, "run", return_value=result) as run:
                    if expected:
                        controller.precheck(SimpleNamespace(precheck="fixture"), Path(temporary) / "receipt.json")
                    else:
                        with self.assertRaisesRegex(ValueError, "fresh vacancy"):
                            controller.precheck(SimpleNamespace(precheck="fixture"), Path(temporary) / "receipt.json")
                    self.assertIn(controller.GPU_UUID, run.call_args.args[0])
                    self.assertEqual(run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")


class PrepareTests(unittest.TestCase):
    def test_prepare_pin_checked_before_import(self):
        specification = importlib.util.spec_from_file_location("high_seed2_prepare", "/tmp/prepare_astra_l2_access_high_seed2_20260913.py")
        prepare = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(prepare)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "never_import.py"
            path.write_text("raise RuntimeError('must not execute')")
            with patch.dict(prepare.os.environ, CUDA_VISIBLE_DEVICES=""):
                with self.assertRaisesRegex(ValueError, "probe pin"):
                    prepare.prepare(str(path), "wrong", "missing")
            with patch.dict(prepare.os.environ, CUDA_VISIBLE_DEVICES="3"):
                with self.assertRaisesRegex(ValueError, "reserve CUDA"):
                    prepare.prepare(str(path), "wrong", "missing")


if __name__ == "__main__":
    unittest.main()
