"""Mocked CPU tests only: no HF model, real tokenizer, GPU, or native solve."""

from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_pchain2_native as native
from gpu import astra_pchain2_prepare as source


class FakeTokenizer:
    eos_token_id = 1
    pad_token_id = 0
    eos_token = "<eot>"
    pad_token = "<pad>"
    all_special_ids = [0, 1]
    padding_side = "right"
    chat_template = "synthetic-chat-template"
    backend_tokenizer = SimpleNamespace(to_str=lambda: "synthetic-backend")

    def encode(self, text, **kwargs):
        result = []
        for part in re.findall(r"<eot>|<pad>|[a-z]{16}|.", text, flags=re.S):
            if part in ("<pad>", "<eot>"):
                result.append(int(part == "<eot>"))
            elif len(part) == 16:
                result.extend(10000 + (ord(part[index]) - 97) * 26 + ord(part[index + 1]) - 97
                              for index in range(0, 16, 2))
            else:
                result.append(ord(part) + 1000)
        return result

    def decode(self, ids, **kwargs):
        result = []
        for token in ids:
            if token in (0, 1):
                result.append("<eot>" if token else "<pad>")
            elif token >= 10000:
                result.append(chr((token - 10000) // 26 + 97) + chr((token - 10000) % 26 + 97))
            else:
                result.append(chr(token - 1000))
        return "".join(result)

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, **kwargs):
        text = "".join(f"<{message['role']}>\n{message['content']}<eot>\n" for message in messages)
        if add_generation_prompt:
            text += "<assistant>\n"
        return self.encode(text) if tokenize else text


class FakeEngine:
    def __init__(self, tokenizer, *, fail_after=None, loss=0.5):
        self.tokenizer = tokenizer
        self.fail_after, self.loss = fail_after, loss
        self.updates, self.prompts = [], []
        self.saved = False

    def train_step(self, batch, *, seed):
        if self.fail_after == len(self.updates):
            raise RuntimeError("synthetic_training_abort")
        self.updates.append((batch, seed))
        return self.loss

    def save_training(self, output):
        self.saved = True
        (output / "adapter").mkdir()
        native._write(output / "adapter" / "SYNTHETIC.json", {"not_native": True})
        return {"synthetic": True}

    def generate(self, prompt, **kwargs):
        if self.fail_after == len(self.prompts):
            raise RuntimeError("synthetic_readout_abort")
        self.prompts.append((prompt, kwargs))
        return self.tokenizer.encode("WRONG\n") + [self.tokenizer.eos_token_id]


def fake_solution(registry, *, endpoint_ids, expected_registry_sha256):
    if registry.registry_sha256 != expected_registry_sha256:
        raise AssertionError("registry not bound")
    return SimpleNamespace(terminal_reason="source_solution", backend="synthetic", assignment=tuple(range(16)),
                           registry_sha256=registry.registry_sha256, solution_sha256="0" * 64,
                           stats={"synthetic": True}, error=None)


def fixture_orders(values, label):
    if label.startswith("display/EVAL-MEM/"):
        return tuple(values)
    prefix = source.MATERIAL_MASTER + b"\0" + label.encode("ascii") + b"\0"
    return tuple(sorted(values, key=lambda value: (sha256(prefix + value.encode("ascii")).digest(), value)))


def canary_fixture():
    return [dict(user=f"CANARY\nCOPY EXACTLY\nANSWER fixture{index:02d}\n", expected=f"ANSWER fixture{index:02d}\n")
            for index in range(16)]


class NativePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = FakeTokenizer()
        with patch.object(native, "_ordered", side_effect=fixture_orders):
            cls.material = native.generate_material(cls.tokenizer, salt_limit=1, max_context=4096,
                                                      canaries=canary_fixture(), solve=fake_solution)

    def manifest(self, namespace, state):
        result = json.loads(json.dumps(self.material[namespace][state]))
        result["material_kind"] = "NATIVE_TOKENIZER_MATERIAL"
        return result

    def test_identifier_stream_is_deterministic_role_blind_and_native_eight(self):
        identifiers, salts = native.allocate_identifiers(self.tokenizer, salt_limit=1)
        self.assertEqual(len(set(identifiers)), 192)
        self.assertEqual(salts, (0,) * 192)
        self.assertEqual((identifiers, salts), native.allocate_identifiers(self.tokenizer, salt_limit=1))
        for identifier in identifiers:
            self.assertRegex(identifier, r"^[a-z]{16}$")
            self.assertEqual(len(self.tokenizer.encode(identifier)), 8)
            self.assertEqual(self.tokenizer.decode(self.tokenizer.encode(identifier)), identifier)
        self.assertNotEqual(native.identifier_candidate(0, 0), native.identifier_candidate(0, 1))

    def test_identifier_salt_is_bounded_and_never_restarts_root(self):
        tokenizer = FakeTokenizer()
        attempts = []

        def encode(text, **kwargs):
            attempts.append(text)
            return [1001]

        tokenizer.encode = encode
        with self.assertRaisesRegex(ValueError, "identifier_salt_exhausted:0"):
            native.allocate_identifiers(tokenizer, salt_limit=3)
        self.assertEqual(attempts, [native.identifier_candidate(0, salt) for salt in range(3)])
        for limit in (0, -1, True):
            with self.assertRaises(ValueError):
                native.allocate_identifiers(tokenizer, salt_limit=limit)

    def test_collision_and_deadline_do_not_trigger_redraw(self):
        with patch.object(native, "identifier_candidate", return_value="abcdefghijklmnop") as candidate:
            with self.assertRaisesRegex(ValueError, "identifier_collision"):
                native.allocate_identifiers(self.tokenizer, salt_limit=2)
        self.assertEqual(candidate.call_count, 2)
        with self.assertRaises(TimeoutError):
            native.allocate_identifiers(self.tokenizer, salt_limit=2,
                                        check=MagicMock(side_effect=TimeoutError("bounded")))

    def test_material_has_no_model_calls_and_separate_training_projections(self):
        self.assertEqual(self.material["summary"]["model_calls"], 0)
        self.assertEqual(self.material["summary"]["fits"], 0)
        self.assertEqual(self.material["summary"]["material_kind"], "DIAGNOSTIC_INJECTED_SOLVER")
        self.assertEqual(set(self.material["training"]), set(source.STATES[1:]))
        self.assertEqual(set(self.material["evaluation"]), set(source.STATES))
        self.assertEqual(sum(len(item["calls"]) for item in self.material["evaluation"].values()), 448)
        for manifest in self.material["training"].values():
            raw = json.dumps(manifest)
            self.assertNotIn("ENDPOINT CANDIDATES", raw)
            self.assertNotIn('"expected"', raw)
            self.assertNotIn("registry_sha256", raw)
            self.assertEqual(len(manifest["encoded_rows"]), 64)

    def test_solver_receipt_precedes_label_construction_and_failure_stops(self):
        events = []

        def failed(registry, **kwargs):
            self.assertEqual(events[-1], "null_registry.json")
            return SimpleNamespace(terminal_reason="failed", backend="synthetic", assignment=None,
                                   registry_sha256=registry.registry_sha256, solution_sha256=None,
                                   stats={}, error=ValueError("UNSAT"))

        with patch.object(native, "_ordered", side_effect=fixture_orders), self.assertRaisesRegex(ValueError, "no_redraw"):
            native.generate_material(self.tokenizer, salt_limit=1, max_context=4096, solve=failed,
                                     emit=lambda name, value: events.append(name))
        self.assertEqual(events, ["identifiers.json", "null_registry.json", "null_assignment.json"])

    def test_masks_cover_only_assistant_content_and_EOT(self):
        manifest = self.manifest("training", "ATOM-JUNCTION")
        rows, tape = native.validate_training_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        self.assertEqual(len(rows), 64)
        self.assertEqual(len(tape), 384)
        for index, row in enumerate(rows):
            target = manifest["rows"][index]["messages"][-1]["content"]
            self.assertEqual(tuple(value for value in row.labels if value != -100), row.target_ids)
            self.assertEqual(self.tokenizer.decode(row.target_ids), target + "<eot>")
            self.assertEqual(row.labels[-1], -100)
            self.assertEqual(row.labels[0], -100)
        batch = native.collate((rows[0], rows[1], rows[32], rows[33]), pad_id=0)
        self.assertEqual(len({len(row) for row in batch["input_ids"]}), 1)
        for mask, labels in zip(batch["attention_mask"], batch["labels"]):
            self.assertTrue(all(label == -100 for bit, label in zip(mask, labels) if not bit))

    def test_mask_and_manifest_drift_fail_before_training(self):
        manifest = self.manifest("training", "ATOM-JUNCTION")
        with self.assertRaisesRegex(ValueError, "overflow"):
            native.validate_training_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=1)
        mutations = []
        changed = deepcopy(manifest)
        changed["encoded_rows"][0]["labels"][0] = 999
        mutations.append(changed)
        changed = deepcopy(manifest)
        changed["dropout_seeds"][0] += 1
        mutations.append(changed)
        changed = deepcopy(manifest)
        changed["recipe"]["learning_rate"] = "0.1"
        mutations.append(changed)
        for changed in mutations:
            with self.assertRaises(ValueError):
                native.validate_training_manifest(changed, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        with self.assertRaisesRegex(ValueError, "bound_native_training_state"):
            native.validate_training_manifest(self.material["training"]["ATOM-JUNCTION"], self.tokenizer,
                                              state="ATOM-JUNCTION", max_context=4096)

    def test_extra_assistant_special_or_template_suffix_is_rejected(self):
        messages = deepcopy(self.material["training"]["ATOM-JUNCTION"]["rows"][0]["messages"])
        messages[-1]["content"] = "MEMORY <eot>\n"
        with self.assertRaisesRegex(ValueError, "special_token"):
            native.encode_training_row(messages, self.tokenizer, max_context=4096)
        tokenizer = FakeTokenizer()
        original = tokenizer.apply_chat_template
        tokenizer.apply_chat_template = lambda *args, **kwargs: original(*args, **kwargs) + "\n"
        with self.assertRaisesRegex(ValueError, "template_boundary"):
            native.encode_training_row(self.material["training"]["ATOM-JUNCTION"]["rows"][0]["messages"],
                                       tokenizer, max_context=4096)

    def test_unbound_canaries_block_readout_but_not_material_training(self):
        with patch.object(native, "_ordered", side_effect=fixture_orders):
            material = native.generate_material(self.tokenizer, salt_limit=1, max_context=4096, solve=fake_solution)
        self.assertEqual(material["summary"]["missing_canary_calls"], 48)
        manifest = json.loads(json.dumps(material["evaluation"]["ATOM-JUNCTION"]))
        manifest["material_kind"] = "NATIVE_TOKENIZER_MATERIAL"
        with self.assertRaisesRegex(ValueError, "bind_canaries"):
            native.validate_readout_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        base = json.loads(json.dumps(material["evaluation"]["BASE"]))
        base["material_kind"] = "NATIVE_TOKENIZER_MATERIAL"
        self.assertEqual(len(native.validate_readout_manifest(base, self.tokenizer, state="BASE", max_context=4096)), 80)

    def test_canary_bindings_cannot_expose_scored_material_identifiers(self):
        canaries = canary_fixture()
        identifier = native.allocate_identifiers(self.tokenizer, salt_limit=1)[0][0]
        canaries[0]["user"] = f"COPY {identifier}\n"
        with self.assertRaisesRegex(ValueError, "canary_material_identifier_overlap"):
            native._bind_canaries(SimpleNamespace(calls=()), canaries, (identifier,))

    def test_exact_one_state_384_update_loop_and_saved_adapter(self):
        manifest = self.manifest("training", "ATOM-JUNCTION")
        rows, tape = native.validate_training_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        engine = FakeEngine(self.tokenizer)
        with TemporaryDirectory() as directory:
            output = Path(directory)
            result = native.execute_training(manifest, rows, tape, engine, output, pad_id=0)
            self.assertEqual(result["updates"], 384)
            self.assertEqual(result["presentations"], 1536)
            self.assertEqual(result["held_calls"], 0)
            self.assertTrue(engine.saved)
            self.assertEqual([seed for _, seed in engine.updates], [batch.dropout_seed for batch in tape])
            self.assertEqual(len((output / "training.jsonl").read_text().splitlines()), 384)
            self.assertTrue((output / "RESULT.json").is_file())
        self.assertEqual(engine.prompts, [])

    def test_training_failure_preserves_log_without_saving_or_retrying(self):
        manifest = self.manifest("training", "LR0")
        rows, tape = native.validate_training_manifest(manifest, self.tokenizer, state="LR0", max_context=4096)
        engine = FakeEngine(self.tokenizer, fail_after=2)
        with TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "synthetic_training_abort"):
                native.execute_training(manifest, rows, tape, engine, output, pad_id=0)
            self.assertEqual(json.loads((output / "FAILED.json").read_text())["completed_updates"], 2)
            self.assertFalse((output / "RESULT.json").exists())
            self.assertFalse(engine.saved)
        self.assertEqual(len(engine.updates), 2)

    def test_readout_is_cold_raw_only_and_does_not_score_against_expected(self):
        manifest = self.manifest("evaluation", "ATOM-JUNCTION")
        prompts = native.validate_readout_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        engine = FakeEngine(self.tokenizer)
        with TemporaryDirectory() as directory:
            output = Path(directory)
            result = native.execute_readout(manifest, prompts, self.tokenizer, engine, output)
            self.assertEqual(result["calls"], 112)
            self.assertFalse(result["scored"])
            records = [json.loads(line) for line in (output / "raw_readouts.jsonl").read_text().splitlines()]
        self.assertTrue(all(bytes.fromhex(record["raw_utf8_hex"]) == b"WRONG\n" for record in records))
        self.assertTrue(all(record["terminal"] and "expected" not in record for record in records))
        self.assertEqual([prompt for prompt, _ in engine.prompts], list(prompts))
        self.assertEqual(engine.updates, [])
        self.assertEqual(sum(item[1]["max_new_tokens"] for item in engine.prompts),
                         sum(call["slot"]["max_new_tokens"] for call in manifest["calls"]))

    def test_readout_failure_keeps_all_reserved_slots_without_more_calls(self):
        manifest = self.manifest("evaluation", "BASE")
        prompts = native.validate_readout_manifest(manifest, self.tokenizer, state="BASE", max_context=4096)
        engine = FakeEngine(self.tokenizer, fail_after=2)
        with TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "synthetic_readout_abort"):
                native.execute_readout(manifest, prompts, self.tokenizer, engine, output)
            records = [json.loads(line) for line in (output / "raw_readouts.jsonl").read_text().splitlines()]
            self.assertFalse((output / "RESULT.json").exists())
        self.assertEqual(len(engine.prompts), 2)
        self.assertEqual(len(records), 80)
        self.assertEqual([row["status"] for row in records[:4]], ["RAW", "RAW", "ERROR", "NOT_RUN"])

    def test_parser_exposes_limits_and_has_no_combined_fit_eval_mode(self):
        parser = native.build_parser()
        args = parser.parse_args(["material", "--model-dir", "/synthetic/model", "--output", "/synthetic/output",
                                  "--max-context", "4096", "--deadline-seconds", "60", "--salt-limit", "100"])
        self.assertEqual(args.salt_limit, 100)
        self.assertIsNone(args.canaries)
        self.assertFalse(hasattr(args, "state"))

    def test_train_CLI_reads_only_training_file_and_never_overwrites(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest("training", "ATOM-LOCAL")
            native._write(root / "training.json", manifest)
            output = root / "run"
            argv = ["train", "--model-dir", str(root), "--output", str(output), "--max-context", "4096",
                    "--deadline-seconds", "60", "--state", "ATOM-LOCAL", "--device", "synthetic-cpu",
                    "--training-file", str(root / "training.json")]
            engine = FakeEngine(self.tokenizer)
            with patch.object(native, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(native, "HFState", return_value=engine) as factory, \
                    patch.object(native, "_read", wraps=native._read) as reader:
                native.main(argv)
                self.assertEqual(reader.call_args_list[0].args, (str(root / "training.json"),))
                self.assertEqual(reader.call_count, 1)
                factory.assert_called_once_with(str(root), state="ATOM-LOCAL", device="synthetic-cpu", training=True,
                                                expected_base_sha256=None)
                with self.assertRaises(FileExistsError):
                    native.main(argv)
                self.assertEqual(factory.call_count, 1)

    def test_material_CLI_never_constructs_HF_state(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "material"
            argv = ["material", "--model-dir", directory, "--output", str(output), "--max-context", "4096",
                    "--deadline-seconds", "60", "--salt-limit", "1"]
            with patch.object(native, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(native, "generate_material", return_value=self.material), \
                    patch.object(native, "HFState", side_effect=AssertionError("no model")) as engine:
                native.main(argv)
            engine.assert_not_called()
            self.assertTrue((output / "training" / "LR0.json").exists())
            self.assertTrue((output / "evaluation" / "BASE.json").exists())

    def test_tokenizer_canary_precedes_solver_and_never_assigns_scored_facts(self):
        emitted = {}
        with patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solve")) as solver, \
                patch.object(native, "HFState", side_effect=AssertionError("no model")) as model:
            result = native.tokenizer_canary(self.tokenizer, salt_limit=1, max_context=4096,
                                             emit=lambda name, value: emitted.update({name: value}))
        solver.assert_not_called()
        model.assert_not_called()
        self.assertEqual(result["status"], "TOKENIZER_CANARY_PASS")
        self.assertEqual(result["EVAL_relations_assigned"], 0)
        self.assertEqual(result["encoded_rows"], 66)
        self.assertEqual((result["model_calls"], result["fits"], result["null_solver_calls"]), (0, 0, 0))
        self.assertEqual(set(emitted), {"identifiers.json", "encoded_canary_rows.json"})
        self.assertEqual(len(result["blocked_bindings"]), 3)
        fact_ids, prompt_ids, _ = native._domain_roles(tuple(emitted["identifiers.json"]["identifiers"]))
        for row in emitted["encoded_canary_rows.json"]:
            raw = "".join(message["content"] for message in row["messages"])
            self.assertFalse(any(identifier in raw for identifier in fact_ids + prompt_ids))

    def test_tokenizer_canary_CLI_writes_native_interface_result_only(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "canary"
            args = ["tokenizer-canary", "--model-dir", directory, "--output", str(output), "--max-context", "4096",
                    "--deadline-seconds", "60", "--salt-limit", "1"]
            with patch.object(native, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(native, "HFState", side_effect=AssertionError("no model")), \
                    patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solver")):
                native.main(args)
            result = json.loads((output / "RESULT.json").read_text())
            self.assertEqual(result["status"], "TOKENIZER_CANARY_PASS")
            self.assertFalse((output / "training").exists())
            self.assertFalse((output / "evaluation").exists())

    def test_execution_rejects_short_tapes_and_rosters_without_engine_calls(self):
        manifest = self.manifest("training", "ATOM-JUNCTION")
        rows, tape = native.validate_training_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=4096)
        engine = FakeEngine(self.tokenizer)
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "exact_D1_execution_tape"):
                native.execute_training(manifest, rows, tape[:-1], engine, Path(directory), pad_id=0)
            readout = self.manifest("evaluation", "BASE")
            prompts = native.validate_readout_manifest(readout, self.tokenizer, state="BASE", max_context=4096)
            with self.assertRaisesRegex(ValueError, "exact_readout_execution_roster"):
                native.execute_readout(readout, prompts[:-1], self.tokenizer, engine, Path(directory))
        self.assertFalse(engine.updates)
        self.assertFalse(engine.prompts)

    def test_actual_HF_factory_uses_fresh_models_optimizers_and_exact_LR0_recipe(self):
        torch, transformers, peft = MagicMock(), MagicMock(), MagicMock()
        models = []
        for _ in range(2):
            model = MagicMock()
            model.config.model_type = "qwen2"
            model.to.return_value = model
            model.named_parameters.return_value = [("layer.q_proj.lora_A.default.weight", SimpleNamespace(requires_grad=True)),
                                                   ("layer.q_proj.lora_B.default.weight", SimpleNamespace(requires_grad=True))]
            models.append(model)
        transformers.AutoModelForCausalLM.from_pretrained.side_effect = models
        peft.get_peft_model.side_effect = lambda model, config, **kwargs: model
        torch.optim.AdamW.side_effect = [MagicMock(), MagicMock()]
        with TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.dict("sys.modules", {"torch": torch, "transformers": transformers, "peft": peft}))
            stack.enter_context(patch.object(native.HFState, "adapter_hash", return_value="synthetic-hash"))
            stack.enter_context(patch.object(native.HFState, "require_zero_delta"))
            hashed = stack.enter_context(patch.object(native, "base_state_hash", return_value="retained-base"))
            first = native.HFState(directory, state="ATOM-JUNCTION", device="synthetic-cpu", training=True)
            second = native.HFState(directory, state="LR0", device="synthetic-cpu", training=True)
        self.assertIsNot(first.model, second.model)
        self.assertIsNot(first.optimizer, second.optimizer)
        self.assertEqual([call.kwargs["lr"] for call in torch.optim.AdamW.call_args_list], [3e-5, 0.0])
        for call in transformers.AutoModelForCausalLM.from_pretrained.call_args_list:
            self.assertTrue(call.kwargs["local_files_only"])
            self.assertFalse(call.kwargs["trust_remote_code"])
            self.assertTrue(call.kwargs["use_safetensors"])
            self.assertEqual(call.kwargs["torch_dtype"], torch.bfloat16)
        for call in peft.LoraConfig.call_args_list:
            self.assertEqual((call.kwargs["r"], call.kwargs["lora_alpha"], call.kwargs["lora_dropout"]), (8, 16, 0.05))
        self.assertEqual([call.args for call in torch.manual_seed.call_args_list], [(0,), (0,)])
        self.assertEqual(hashed.call_count, 2)
        self.assertEqual(first.base_state_sha256, "retained-base")
        self.assertEqual(torch.set_num_threads.call_count, 2)
        torch.set_num_interop_threads.assert_called_with(1)
        for model in models:
            model.requires_grad_.assert_called_once_with(False)
            model.to.assert_called_once_with("synthetic-cpu")
            model.gradient_checkpointing_enable.assert_called_once_with(
                gradient_checkpointing_kwargs={"use_reentrant": False})
        self.assertTrue(all(call.kwargs["autocast_adapter_dtype"] for call in peft.get_peft_model.call_args_list))
        for call in torch.optim.AdamW.call_args_list:
            self.assertEqual({key: call.kwargs[key] for key in native.OPTIMIZER}, native.OPTIMIZER)

    def test_readout_preserves_base_buffers_and_uses_FP32_adapter(self):
        torch, transformers, peft = MagicMock(), MagicMock(), MagicMock()
        torch.get_num_interop_threads.return_value = 1
        base, wrapped = MagicMock(), MagicMock()
        base.config.model_type = "qwen2"
        wrapped.to.return_value = wrapped
        wrapped.named_parameters.return_value = []
        transformers.AutoModelForCausalLM.from_pretrained.return_value = base
        peft.PeftModel.from_pretrained.return_value = wrapped
        peft.LoraConfig.from_pretrained.return_value = SimpleNamespace(
            r=8, lora_alpha=16, lora_dropout=0.05, target_modules=native.TARGET_MODULES)

        def check_hash(model):
            self.assertIs(model, base)
            peft.PeftModel.from_pretrained.assert_not_called()
            return "retained-base"

        with TemporaryDirectory() as directory, \
                patch.dict("sys.modules", {"torch": torch, "transformers": transformers, "peft": peft}), \
                patch.object(native, "base_state_hash", side_effect=check_hash) as hashed:
            state = native.HFState(directory, state="ATOM-JUNCTION", device="synthetic-cpu", training=False,
                                   adapter_dir=directory, expected_base_sha256="retained-base")
        hashed.assert_called_once_with(base)
        wrapped.to.assert_called_once_with("synthetic-cpu")
        wrapped.eval.assert_called_once()
        wrapped.gradient_checkpointing_enable.assert_not_called()
        self.assertTrue(peft.PeftModel.from_pretrained.call_args.kwargs["autocast_adapter_dtype"])
        torch.optim.AdamW.assert_not_called()
        torch.set_num_interop_threads.assert_not_called()
        self.assertIsNone(state.optimizer)

    def test_base_hash_mismatch_stops_before_wrap_or_placement(self):
        torch, transformers, peft = MagicMock(), MagicMock(), MagicMock()
        base = transformers.AutoModelForCausalLM.from_pretrained.return_value
        base.config.model_type = "qwen2"
        with TemporaryDirectory() as directory, \
                patch.dict("sys.modules", {"torch": torch, "transformers": transformers, "peft": peft}), \
                patch.object(native, "base_state_hash", return_value="changed"), \
                self.assertRaisesRegex(ValueError, "retained_base_hash_mismatch"):
            native.HFState(directory, state="ATOM-JUNCTION", device="synthetic-cpu", training=True,
                           expected_base_sha256="retained-base")
        peft.get_peft_model.assert_not_called()
        base.to.assert_not_called()

    def test_material_deadline_covers_tokenizer_load_and_records_receipt(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "material"
            argv = ["material", "--model-dir", directory, "--output", str(output), "--max-context", "16384",
                    "--deadline-seconds", "180", "--salt-limit", "4096"]
            with patch.object(native.signal, "signal", return_value=native.signal.SIG_DFL) as handler, \
                    patch.object(native.signal, "setitimer", return_value=(0, 0)) as timer, \
                    patch.object(native, "HFState") as model:
                def stalled_load(path):
                    timer.assert_called_once_with(native.signal.ITIMER_REAL, 180)
                    handler.call_args.args[1](native.signal.SIGALRM, None)

                with patch.object(native, "load_local_tokenizer", side_effect=stalled_load), \
                        self.assertRaisesRegex(TimeoutError, "caller_deadline_exceeded"):
                    native.main(argv)
                model.assert_not_called()
                timer.assert_called_with(native.signal.ITIMER_REAL, 0)
                handler.assert_called_with(native.signal.SIGALRM, native.signal.SIG_DFL)
            self.assertEqual(native._read(output / "REQUEST.json")["numerical_binding"], native.NUMERICAL_BINDING)
            self.assertFalse((output / "RESULT.json").exists())
            self.assertIn("caller_deadline_exceeded", native._read(output / "FAILED.json")["error"])


if __name__ == "__main__":
    unittest.main()
