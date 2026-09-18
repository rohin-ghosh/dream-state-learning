"""Tiny SYNTHETIC protocol fixtures; never actual native formation or a 7B fit.

Literal NATIVE fields simulate the required protocol branch, not model origin.
Optional numerical tests construct random tiny CPU Qwen, never pretrained.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from organism_v6 import pcfl_own_write_train as own
from gpu import astra_pcfl_own_write_dev as formation
from gpu import astra_pcfl_native_actor as native
from test_pcfl_vertical_formation_plan import choices, synthetic_child_spans


class SyntheticTokenizer:
    chat_template = "SYNTHETIC_ONLY_NOT_QWEN_QUALIFICATION"
    eos_token_id = 1

    def __init__(self, path):
        self.name_or_path = str(path)
        self.decoded = {}

    def encode(self, text, add_special_tokens=False):
        payload = text.encode()
        ids = [2 + hashlib.sha256(payload[start:start + 8]).digest()[0] % 62
               for start in range(0, len(payload), 8)]
        self.decoded[tuple(ids)] = text
        return ids

    def decode(self, ids, skip_special_tokens=True):
        return self.decoded[tuple(ids)]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n"
                       for message in messages) + "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


def synthetic_fixture(root, *, cold_first_call=False):
    model_dir = root / "SYNTHETIC_TOKENIZER"
    model_dir.mkdir()
    files = {}
    for name in sorted(native.TOKENIZER_FILES):
        data = ("SYNTHETIC ONLY " + name).encode()
        (model_dir / name).write_bytes(data)
        files[name] = hashlib.sha256(data).hexdigest()
    tokenizer = SyntheticTokenizer(model_dir)
    cell = own.core.WorldCell(own.core.build_root("disposable/0"), 0, 0, 0)
    actions, links = choices(cell)
    events, link_rows = synthetic_child_spans(cell, actions, links)
    outputs = [raw for pair in zip(actions, events) for raw in pair] + link_rows
    actor_config = dict(schema=native.SCHEMA, model_path=str(model_dir), output_dir=str(root / "UNUSED_NATIVE_PATH"),
                        model_binding={"path": str(root / "SYNTHETIC_model_receipt.json"), "sha256": "a" * 64},
                        source_files=formation.source_pins(), tokenizer_files=files,
                        chat_template_sha256=own.writer.byte_hash(tokenizer.chat_template),
                        tokenizer_probe={"text": "SYNTHETIC", "token_ids": tokenizer.encode("SYNTHETIC")},
                        environment={"test_only": "SYNTHETIC_PROTOCOL"}, gpu_uuid="GPU-SYNTHETIC",
                        engine=copy.deepcopy(native.ENGINE), deadline=100000, device_seconds_cap=100,
                        max_input_tokens=16000, max_output_tokens=256, max_calls=20)
    limits = {"output_tokens": 256, "returned_tokens": 0, "remaining_reads": 0,
              "input_tokens": 16000, "deadline": 100000, "device_seconds": 15 if cold_first_call else 5}
    config = formation.build_config(cell, actions, links, actor_config=actor_config, seed=17, limits=limits)
    plan = config["planner"]
    schedule = own.build_schedule(plan, plan["plan_sha256"], batch_seed=19)
    model_files = {**files, **{f"SYNTHETIC_MODEL_{index}": "b" * 64 for index in range(10)}}
    identity = {"kind": "NATIVE", "config_sha256": own.digest(actor_config), "pid": 123,
                "identity": {"repository": native.MODEL_NAME, "revision": native.REVISION,
                             "model_binding_sha256": actor_config["model_binding"]["sha256"],
                             "model_files": model_files, "source_files": actor_config["source_files"],
                             "environment": actor_config["environment"], "gpu_uuid_expected": "GPU-SYNTHETIC",
                             "mount": "C0", "lora_request": None, "clean_lineage_certified": False}}

    def acquire(index, request, call_limits):
        text = outputs[index]
        operation_started = 1 if cold_first_call and index == 0 else 10 + 3 * index
        rendered = tokenizer.apply_chat_template(request["messages"], tokenize=False, add_generation_prompt=True)
        prompt_ids, output_ids = tokenizer.encode(rendered), tokenizer.encode(text)
        response = {"request_sha256": own.digest(request), "text": text, "prompt_tokens": len(prompt_ids),
                    "output_tokens": len(output_ids), "device_seconds": 10.0 if cold_first_call and index == 0 else 1.0}
        prefix = f"call_{index:04}."
        sidecars = {"config.json": actor_config, "identity.json": identity,
                    prefix + "request.json": {"request": request, "limits": call_limits, "request_sha256": own.digest(request), "started": operation_started},
                    prefix + "render.json": {"rendered_prompt": rendered, "prompt_token_ids": prompt_ids,
                                              "sampling": formation.lf_api.sampling_for(request, call_limits), "mount": "C0", "lora_request": None},
                    prefix + "raw.json": {"kind": "NATIVE", "request_sha256": own.digest(request), "operation_started": operation_started,
                                           "generation_started": 10.2 + 3 * index, "generation_ended": 10.7 + 3 * index,
                                           "mount": "C0", "lora_request": None,
                                           "raw": {"text": text, "prompt_token_ids": prompt_ids, "output_token_ids": output_ids, "finish_reason": "stop", "stop_reason": None}},
                    prefix + "response.json": {"response": response, "raw_utf8_sha256": own.writer.byte_hash(text),
                                                "raw_hex": text.encode().hex(), "decoded": text}}
        captured = {name: {"utf8": own.canonical(value).decode(), "sha256": own.digest(value)} for name, value in sidecars.items()}
        return {"request": copy.deepcopy(request), "limits": copy.deepcopy(call_limits), "response": response,
                "capture": {"schema": formation.SCHEMA + "/capture", "index": index, "files": captured}, "backend_error": None}

    report = formation._form(config, acquire)
    if report["status"] != "COMPLETE":
        raise AssertionError(report["failure"])
    lifecycle = {"config": actor_config, "identity": identity,
                 "load": {"kind": "NATIVE", "mount": "C0", "lora_request": None, "operation_started": 1, "model_load_started": 2, "ready_at": 5},
                 "close": {"kind": "NATIVE", "failed": False, "error_type": None, "budget_exceeded": False,
                           "calls_consumed": 20, "token_count_calls": 0, "elapsed_actor_seconds": 35 if cold_first_call else 25}}
    binding = {"authority_sha256": "c" * 64, "init_seed": 31, "dropout_seed": 37, "base_state_sha256": "d" * 64,
               "environment": {"base": own.prepare.RECIPE["base"], "model_revision": native.REVISION,
                               "model_files": model_files, "tokenizer_revision": native.REVISION,
                               "chat_template_sha256": actor_config["chat_template_sha256"], "fixture": "SYNTHETIC_ONLY"},
               "tokenizer_receipt": {"kind": "offline_measurement", "revision": native.REVISION, "files": files,
                                     "chat_template_sha256": actor_config["chat_template_sha256"],
                                     "measurements": [{"text": "SYNTHETIC", "token_ids": tokenizer.encode("SYNTHETIC")}]},
               "sources": own.source_snapshot()}
    return {"config": config, "config_sha256": config["sha256"], "report": report, "report_sha256": report["sha256"],
            "schedule": schedule, "schedule_sha256": schedule["sha256"], "binding": binding, "native_receipts": lifecycle}, tokenizer


class OwnWriteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_OWN_WRITE_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.arguments, self.tokenizer = synthetic_fixture(self.root)

    def fit(self):
        return own.build_fit(**self.arguments)

    def test_fixed_preoutput_auth_schedule_and_unchanged_inputs(self):
        before = own.canonical(self.arguments)
        fit = self.fit()
        schedule = fit["schedule"]
        self.assertEqual(len(schedule["corpus"]["slots"]), 20)
        self.assertEqual(len(set(schedule["replay"]["selected"])), 3)
        self.assertEqual(sum(len(epoch) for epoch in schedule["epochs"]), 200)
        self.assertEqual({pair[1] for epoch in schedule["epochs"] for batch in epoch for pair in batch}, set(range(8)))
        self.assertTrue(all(slot["row_type"] == "EVENT" for slot in schedule["corpus"]["slots"][17:]))
        self.assertEqual(own.canonical(self.arguments), before)
        self.assertFalse(own.validate_fit(fit)["cal_qualified"])
        self.assertFalse(own.validate_fit(fit)["native_custody_verified"])

    def test_own_chronology_e5_e7_not_ideal_numbering(self):
        rows = self.fit()["report"]["writer_payload"]["rows"]
        root = own.core.from_data(self.arguments["config"]["planner"]["cell"]).root
        self.assertEqual(rows[5]["fields"]["source"], root.lookup("node", "Z"))
        self.assertEqual(rows[7]["fields"]["source"], root.lookup("node", "B"))
        self.assertTrue(all(row["taint"] == "CHILD_SUBMISSION" for row in rows))

    def test_schedule_targets_and_replays_cannot_be_changed(self):
        schedule = copy.deepcopy(self.arguments["schedule"])
        schedule["corpus"]["slots"][-1]["source"] = "s00"
        schedule.pop("sha256")
        schedule = own._seal(schedule)
        plan = self.arguments["config"]["planner"]
        with self.assertRaisesRegex(ValueError, "schedule drift"):
            own.validate_schedule(plan, plan["plan_sha256"], schedule, schedule["sha256"])
        with self.assertRaises(ValueError):
            own.build_schedule(plan, plan["plan_sha256"], batch_seed=True)

    def test_independent_pins_and_sealed_payload_mutations_reject(self):
        for field in ("config_sha256", "report_sha256", "schedule_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.arguments)
                changed[field] = "0" * 64
                with self.assertRaises(ValueError):
                    own.build_fit(**changed)
        fit = self.fit()
        fit["binding"]["learning_rate"] = 3e-4
        with self.assertRaisesRegex(ValueError, "seal drift"):
            own.validate_fit(fit)

    def test_forged_child_span_control_and_unused_generation_reject(self):
        edits = [lambda payload: payload["rows"][0]["provenance"].update(byte_start=True),
                 lambda payload: payload["rows"][0].update(taint="CEILING_FIXTURE"),
                 lambda payload: payload["rows"][0].update(raw=payload["rows"][0]["raw"] + "\n"),
                 lambda payload: payload["generations"].append(copy.deepcopy(payload["generations"][0])),
                 lambda payload: payload.update(controls=[{"name": "EVENT_TWIN", "ancestors": []}])]
        for edit in edits:
            changed = copy.deepcopy(self.arguments)
            edit(changed["report"]["writer_payload"])
            changed["report"].pop("sha256")
            changed["report"] = own._seal(changed["report"])
            changed["report_sha256"] = changed["report"]["sha256"]
            with self.assertRaises(ValueError):
                own.build_fit(**changed)

    def test_exact_native_bytes_stop_completion_and_custody(self):
        for suffix, edit in (("raw", lambda value: value["raw"].update(finish_reason="length")),
                             ("response", lambda value: value.update(decoded="repaired")),
                             ("raw", lambda value: value.update(kind="INJECTED_CPU_TEST")),
                             ("request", lambda value: value["request"].update(mount="ADAPTER"))):
            with self.subTest(suffix=suffix):
                changed = copy.deepcopy(self.arguments)
                record = changed["report"]["slots"][1]["attempt"]["capture"]["files"]["call_0001." + suffix + ".json"]
                value = json.loads(record["utf8"])
                edit(value)
                record.update(utf8=own.canonical(value).decode(), sha256=own.digest(value))
                changed["report"].pop("sha256")
                changed["report"] = own._seal(changed["report"])
                changed["report_sha256"] = changed["report"]["sha256"]
                with self.assertRaises(ValueError):
                    own.build_fit(**changed)

    def test_lifecycle_sources_learning_rate_and_base_identity_reject(self):
        edits = [lambda args: args["native_receipts"]["close"].update(calls_consumed=19),
                 lambda args: args["native_receipts"]["close"].update(failed=True),
                 lambda args: args["native_receipts"]["identity"]["identity"].update(revision="other"),
                 lambda args: args["binding"]["sources"].update(writer="0" * 64),
                 lambda args: args["binding"]["environment"].update(base="other"),
                 lambda args: args["binding"].update(dropout_seed=True),
                 lambda args: args["binding"].update(learning_rate=3e-4),
                 lambda args: args["binding"]["tokenizer_receipt"].update(kind="synthetic_test")]
        for edit in edits:
            changed = copy.deepcopy(self.arguments)
            edit(changed)
            with self.assertRaises(ValueError):
                own.build_fit(**changed)

    def test_existing_output_never_calls_factory(self):
        factory = Mock(side_effect=AssertionError("must not initialize"))
        with self.assertRaises(FileExistsError):
            own.train_fit(self.fit(), self.tokenizer, factory, self.root)
        factory.assert_not_called()

    def test_shutdown_method_flag_is_not_gpu_release_proof(self):
        self.arguments["native_receipts"]["close"]["shutdown"] = {"shutdown_method_available": False}
        validation = own.validate_fit(self.fit())
        self.assertFalse(validation["native_custody_verified"])
        self.assertFalse(validation["full_contract_released"])
        self.assertNotIn("gpu_vacant", validation)

    def test_first_cold_operation_can_begin_before_model_ready(self):
        root = self.root / "cold_fixture"
        root.mkdir()
        arguments, _ = synthetic_fixture(root, cold_first_call=True)
        fit = own.build_fit(**arguments)
        raw = formation._capture_data(fit["report"]["slots"][0]["attempt"]["capture"], 0)["call_0000.raw.json"]
        ready = fit["native_receipts"]["load"]["ready_at"]
        self.assertLess(raw["operation_started"], ready)
        self.assertGreaterEqual(raw["generation_started"], ready)
        self.assertTrue(own.validate_fit(fit)["native_capture_joins_verified"])
        arguments["native_receipts"]["load"]["ready_at"] = raw["generation_started"] + 0.1
        with self.assertRaisesRegex(ValueError, "generation precedes model load"):
            own.build_fit(**arguments)

    def test_response_eos_masks_and_original_encoder_parity(self):
        fit = self.fit()
        encoded = own.encode_fit(fit, self.tokenizer)
        self.assertEqual(len(encoded["items"]), 160)
        for item in encoded["items"]:
            example = item["encoded"]
            first = next(index for index, label in enumerate(example["labels"]) if label != -100)
            self.assertGreater(first, 0)
            self.assertEqual(example["labels"][:first], [-100] * first)
            self.assertEqual(example["labels"][first:], example["ids"][first:])
            self.assertEqual(example["ids"][-1], self.tokenizer.eos_token_id)
            self.assertFalse(example["context_dropped"] or example["target_dropped"])
        reference = own.writer._encode_corpus(fit["sha256"], fit["schedule"]["corpus"], fit["schedule"]["epochs"],
                                               fit["report"]["writer_payload"]["queries"], own.core.registries()["render_registry"],
                                               fit["binding"]["environment"]["chat_template_sha256"], self.tokenizer)
        self.assertEqual(encoded, reference)

    def test_native_decode_template_and_mask_drift_reject(self):
        fit = self.fit()
        with patch.object(self.tokenizer, "decode", return_value="repaired"):
            with self.assertRaisesRegex(ValueError, "output decode"):
                own.encode_fit(fit, self.tokenizer)
        self.tokenizer.chat_template = "DRIFT"
        with self.assertRaisesRegex(ValueError, "chat template pin"):
            own.encode_fit(fit, self.tokenizer)


@unittest.skipUnless(os.environ.get("ASTRA_PCFL_TINY_CPU") == "1", "opt-in tiny CPU numerical parity; no native qualification")
class TinyCPUNumericalTests(unittest.TestCase):
    def test_pooled_loss_is_not_mean_of_sequence_means(self):
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        import torch

        class TinyLogits(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.bias = torch.nn.Parameter(torch.tensor([0.0, 2.0, -1.0]))

            def forward(self, input_ids, attention_mask, use_cache):
                from types import SimpleNamespace
                return SimpleNamespace(logits=self.bias.expand(*input_ids.shape, 3))

        model = TinyLogits()
        examples = [{"ids": [0, 1], "labels": [-100, 1]},
                    {"ids": [0, 2, 2, 2], "labels": [-100, 2, 2, 2]}]
        loss, tokens = own.writer._batch_objective(model, examples, "cpu")
        logs = torch.log_softmax(model.bias, dim=0)
        self.assertEqual(tokens, 4)
        self.assertTrue(torch.allclose(loss, -(logs[1] + 3 * logs[2]) / 4))
        self.assertFalse(torch.allclose(loss, -(logs[1] + logs[2]) / 2))
        loss.backward()
        self.assertTrue(torch.isfinite(model.bias.grad).all())

    def test_pooled_objective_and_200_update_save_reload_parity(self):
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), "1")
        self.assertEqual(os.environ.get("TRANSFORMERS_OFFLINE"), "1")
        import torch
        from transformers import Qwen2Config, Qwen2ForCausalLM
        from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
        from safetensors.torch import load_file

        self.assertFalse(torch.cuda.is_initialized())
        original_threads, original_rng = torch.get_num_threads(), torch.get_rng_state()
        self.addCleanup(torch.set_num_threads, original_threads)
        self.addCleanup(torch.set_rng_state, original_rng)
        torch.set_num_threads(1)
        torch.manual_seed(64011)
        config = Qwen2Config(vocab_size=64, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                            num_attention_heads=2, num_key_value_heads=1, max_position_embeddings=512,
                            bos_token_id=0, eos_token_id=1, pad_token_id=0, tie_word_embeddings=False, use_cache=False)
        config._attn_implementation = "eager"
        template = Qwen2ForCausalLM(config).to(device="cpu", dtype=torch.bfloat16)
        state = copy.deepcopy(template.state_dict())
        bases = []
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC_OWN_WRITE_NUMERICAL_") as directory:
            root = Path(directory)
            arguments, tokenizer = synthetic_fixture(root)
            arguments["binding"]["base_state_sha256"] = own.writer._state_hash(state)
            fit = own.build_fit(**arguments)
            encoding = own.encode_fit(fit, tokenizer)

            def factory():
                model = Qwen2ForCausalLM(copy.deepcopy(config)).to(device="cpu", dtype=torch.bfloat16)
                model.load_state_dict(state)
                bases.append(model)
                return model, copy.deepcopy(arguments["binding"]["environment"])

            actual = own.train_fit(fit, tokenizer, factory, root / "scoped")
            expected = own.writer._train_encoded(fit, encoding, factory, root / "reference",
                                                  fit["binding"]["environment"], own.validate_fit(fit),
                                                  report_name="own_write_scope_report.json")
            for key in ("initial", "final", "updates", "presentations", "training_forwards", "objective", "layout"):
                self.assertEqual(actual[key], expected[key], key)
            self.assertEqual(actual["updates"], 200)
            self.assertNotEqual(actual["initial"]["lora"], actual["final"]["lora"])
            self.assertEqual((root / "scoped/updates.jsonl").read_bytes(), (root / "reference/updates.jsonl").read_bytes())
            for original in bases[:2]:
                for name, parameter in original.named_parameters():
                    if "lora_" not in name:
                        name = name.replace(".base_layer", "")
                        self.assertTrue(torch.equal(parameter.detach(), state[name]), name)
            adapter = root / "scoped/adapter"
            clean, _ = factory()
            adapter_config = LoraConfig(**json.loads((adapter / "adapter_config.json").read_bytes()))
            restored = get_peft_model(clean, adapter_config)
            result = set_peft_model_state_dict(restored, load_file(str(adapter / "adapter_model.safetensors")))
            self.assertFalse(result.unexpected_keys)
            bases[0].eval()
            restored.eval()
            ids = torch.tensor([encoding["items"][0]["encoded"]["ids"]], dtype=torch.long)
            with torch.no_grad():
                actual_logits = bases[0](input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
                restored_logits = restored(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
            self.assertTrue(torch.equal(actual_logits, restored_logits))
            def warm_factory():
                model, environment = factory()
                model.peft_config = {"SYNTHETIC": "warm parent"}
                return model, environment

            with self.assertRaisesRegex(ValueError, "warm/adapted base"):
                own.train_fit(fit, tokenizer, warm_factory, root / "warm_rejected")
            failed = json.loads((root / "warm_rejected/failed.json").read_bytes())
            self.assertEqual(failed["updates"], 0)
            self.assertFalse((root / "warm_rejected/adapter").exists())
            self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
