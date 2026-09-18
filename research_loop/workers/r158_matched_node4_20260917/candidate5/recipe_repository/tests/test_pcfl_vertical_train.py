"""Synthetic writer seam tests; no task model, native custody or GPU evidence."""
import base64
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from organism_v6 import pcfl_vertical_train as writer


MOCK_RELEASE = dict(execution_contract_valid=True, static_contract_complete=True,
                    ready_for_model_calls=True, missing_interfaces=[])


class ToyTokenizer:
    eos_token_id = 1000000
    chat_template = "synthetic template, not native qualification"

    def encode(self, text, add_special_tokens=False):
        return [ord(character) + 1 for character in text]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "".join(message["role"] + ":" + message["content"] + "\n" for message in messages) + "assistant:"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture():
    """Toy 20-singleton bank; NOT a qualified PCFL corpus or native receipt."""
    core, prepare = writer.core, writer.prepare
    root = core.build_root("dev/0")
    rows, generations, slots, queries = [], [], [], {}
    for index in range(20):
        event = "E_" + base64.b32encode(hashlib.sha256(f"toy/{index}".encode()).digest()).decode()[:10]
        fields = dict(event=event, source=root.lookup("node", "S_L"),
                      port=root.lookup("port", "a0"), destination=root.lookup("node", "A"),
                      receipt=root.lookup("receipt", "r0"))
        raw = core.EVENT_WIRE.format(**fields)
        row_hash = writer.byte_hash(raw)
        rows.append(dict(kind="EVENT", raw=raw, sha256=row_hash, root=root.label,
                         fields=fields, taint="CHILD_SUBMISSION",
                         provenance=dict(generation_sha256=row_hash, byte_start=0,
                                         byte_end=len(raw.encode()), native_generation_verified=False)))
        generations.append(dict(raw=raw, sha256=row_hash, origin="CHILD_NATIVE", capture_sha256="1" * 64))
        request = "READ EVENT " + event
        slots.append(dict(id=f"slot{index:02}", source=None, row_type="EVENT", phase="OLD",
                          support=[event], bank={event: fields}, taint="AUTHENTIC", request=request))
        queries[request] = dict(request=request, target=raw, target_sha256=row_hash,
                                support=[event], source_sha256=[row_hash], taint=["CHILD_SUBMISSION"])
    epoch = [[[f"slot{index:02}", view] for index in range(start, start + 4)]
             for view in range(8) for start in range(0, 20, 4)]
    contract = dict(schema=prepare.SCHEMA, recipe=copy.deepcopy(prepare.RECIPE),
                    tokenizer_receipt={"kind": "synthetic_test"}, bindings=dict(
                        core_registry=core.registries(), source_pins=prepare.SOURCE_PINS.copy(),
                        implementation_pins=dict(core=file_hash(core.__file__), preparer=file_hash(prepare.__file__), validator="1" * 64),
                        environment=dict(chat_template_sha256=writer.byte_hash(ToyTokenizer.chat_template),
                                         cal_seeds={"cal/init": 7, "cal/dropout": 8}),
                        slot_registry=[dict(id="toy", root=root.label, arm="S1_AUTH", slots=slots)],
                        root_registry=[dict(id=root.label, role="dev", wire=core.to_data(root))],
                        batch_registry=[dict(corpus="toy", epochs=[copy.deepcopy(epoch) for _ in range(5)])]))
    binding = dict(contract_sha256=writer.digest(contract), authority_sha256="2" * 64,
                   custody_sha256="3" * 64, objective=writer.OBJECTIVE, layout=writer.LAYOUT,
                   learning_rate=3e-5, phase="DEV", selection_receipt_sha256="4" * 64,
                   init_seed=7, dropout_seed=8, base_state_sha256="5" * 64,
                   writer_sha256=file_hash(writer.__file__), shared_trainer_sha256=file_hash(writer.shared.__file__))
    return dict(contract=contract, corpus_id="toy", queries=queries, rows=rows,
                generations=generations, controls=[], binding=binding)


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.inputs = fixture()
        self.structure = patch.object(writer.prepare, "validate_execution_contract", return_value={"release_authorized": False})
        self.validator = self.structure.start()
        self.addCleanup(self.structure.stop)

    def build(self):
        self.inputs["binding"]["contract_sha256"] = writer.digest(self.inputs["contract"])
        return writer.build_fit(**self.inputs)

    def rejects(self):
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.build()

    def test_exact_work_detached_and_no_native_claim(self):
        fit = self.build()
        receipt = writer.validate_fit(fit)
        self.assertEqual((receipt["updates"], receipt["presentations"]), (200, 800))
        self.assertFalse(receipt["native_custody_verified"])
        self.assertFalse(receipt["release_authorized"])
        self.inputs["rows"][0]["raw"] = "changed"
        writer.validate_fit(fit)

    def test_real_preparer_rejects_toy_fixture(self):
        self.structure.stop()
        self.rejects()

    def test_changed_target_rejected_by_real_formation_check(self):
        query = next(iter(self.inputs["queries"].values()))
        query["target"] += " "
        query["target_sha256"] = writer.byte_hash(query["target"])
        self.rejects()

    def test_core_rejects_wrong_address_even_with_matching_bank(self):
        slot = self.inputs["contract"]["bindings"]["slot_registry"][0]["slots"][0]
        query = self.inputs["queries"].pop(slot["request"])
        slot["request"] = "READ EVENT E_AAAAAAAAAA"
        query["request"] = slot["request"]
        self.inputs["queries"][slot["request"]] = query
        self.rejects()

    def test_row_field_and_source_hash_drift(self):
        self.inputs["rows"][0]["sha256"] = "0" * 64
        self.rejects()

    def test_rendered_ceiling_cannot_be_authentic(self):
        self.inputs["rows"][0]["taint"] = "CEILING_FIXTURE"
        self.rejects()

    def test_native_boolean_without_generation_not_enough(self):
        self.inputs["rows"][0]["provenance"]["native_generation_verified"] = True
        self.inputs["generations"].pop(0)
        self.rejects()

    def test_exact_utf8_subspan(self):
        row = self.inputs["rows"][0]
        raw = "π\n" + row["raw"] + "tail"
        hashed = writer.byte_hash(raw)
        row["provenance"].update(generation_sha256=hashed, byte_start=len("π\n".encode()),
                                  byte_end=len(("π\n" + row["raw"]).encode()))
        self.inputs["generations"][0].update(raw=raw, sha256=hashed)
        self.build()
        row["provenance"]["byte_start"] -= 1
        self.rejects()

    def test_boolean_span_bound(self):
        self.inputs["rows"][0]["provenance"]["byte_start"] = False
        self.rejects()

    def test_generation_hash_origin_and_extra_payload(self):
        for change in ({"sha256": "0" * 64}, {"origin": "ORACLE"}, {"capture_sha256": "short"}):
            with self.subTest(change=change):
                self.inputs = fixture()
                self.inputs["generations"][0].update(change)
                self.rejects()

    def test_registered_control_recomputed_not_trusted(self):
        ancestors = copy.deepcopy(self.inputs["rows"])
        root = writer.core.build_root("dev/0")
        self.inputs["rows"] = writer.core.make_event_twin(ancestors, root)
        self.inputs["controls"] = [{"name": "EVENT_TWIN", "ancestors": ancestors}]
        corpus = self.inputs["contract"]["bindings"]["slot_registry"][0]
        corpus["arm"] = "S1_EVENT_TWIN"
        for slot, row in zip(corpus["slots"], self.inputs["rows"]):
            slot.update(taint="CONTROL", bank={slot["support"][0]: row["fields"]})
            self.inputs["queries"][slot["request"]].update(target=row["raw"], target_sha256=row["sha256"],
                                                            source_sha256=[row["sha256"]], taint=["CONTROL"])
        self.build()
        self.inputs["rows"][0]["provenance"]["source_sha256"] = "0" * 64
        self.rejects()

    def test_replay_retains_exact_source_and_does_not_reschedule(self):
        corpus = self.inputs["contract"]["bindings"]["slot_registry"][0]
        source = corpus["slots"][0]
        replay = corpus["slots"][4]
        removed_request = replay["request"]
        replay.update({key: copy.deepcopy(value) for key, value in source.items() if key != "id"})
        replay["source"] = source["id"]
        self.inputs["queries"].pop(removed_request)
        self.inputs["rows"].pop(4)
        self.inputs["generations"].pop(4)
        fit = self.build()
        encoded = writer.encode_fit(fit, ToyTokenizer())
        first = next(item for item in encoded["items"] if item["slot"] == source["id"] and item["view"] == 0)
        copied = next(item for item in encoded["items"] if item["slot"] == replay["id"] and item["view"] == 0)
        self.assertEqual(first["encoded"]["labels"], copied["encoded"]["labels"])
        self.assertEqual(first["source_sha256"], copied["source_sha256"])
        self.assertEqual(encoded["epochs"], fit["contract"]["bindings"]["batch_registry"][0]["epochs"])

    def test_unregistered_or_foreign_control(self):
        self.inputs["controls"] = [{"name": "ORACLE_REWRITE", "ancestors": self.inputs["rows"]}]
        self.rejects()

    def test_control_cannot_derive_from_ceiling(self):
        self.inputs["contract"]["bindings"]["slot_registry"][0]["arm"] = "S1_EVENT_TWIN"
        ancestors = copy.deepcopy(self.inputs["rows"])
        ancestors[0]["taint"] = "CEILING_FIXTURE"
        self.inputs["controls"] = [{"name": "EVENT_TWIN", "ancestors": ancestors}]
        self.rejects()

    def test_seal_detects_post_build_mutation(self):
        fit = self.build()
        fit["binding"]["init_seed"] = 9
        with self.assertRaisesRegex(writer.WriterError, "seal drift"):
            writer.validate_fit(fit)

    def test_strict_rate_seed_and_objective(self):
        mutations = [("learning_rate", value) for value in (True, "0.00003", float("nan"), 1e-4, 0)]
        mutations += [("init_seed", value) for value in (True, -1, 1.0, "1")]
        mutations += [("objective", "mean_sequence_means"), ("layout", "padded"), ("warm_parent", "adapter")]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                self.inputs = fixture()
                self.inputs["binding"][key] = value
                self.rejects()

    def test_high_low_same_seeds_lr_only(self):
        contract = self.inputs["contract"]
        contract["bindings"]["root_registry"][0]["role"] = "disposable"
        self.inputs["binding"].update(phase="CAL_LOW")
        low = self.build()
        self.inputs["binding"].update(phase="CAL_HIGH", learning_rate=3e-4)
        high = self.build()
        self.assertEqual(low["contract"], high["contract"])
        self.inputs["binding"]["dropout_seed"] += 1
        self.rejects()

    def test_epochs_batches_and_views_exact(self):
        for modification in ("epoch", "batch", "size", "view", "bool_view", "duplicate"):
            with self.subTest(modification=modification):
                self.inputs = fixture()
                epochs = self.inputs["contract"]["bindings"]["batch_registry"][0]["epochs"]
                if modification == "epoch":
                    epochs.pop()
                elif modification == "batch":
                    epochs[0].pop()
                elif modification == "size":
                    epochs[0][0].pop()
                elif modification == "view":
                    epochs[0][0][0][1] = 8
                elif modification == "bool_view":
                    epochs[0][0][0][1] = False
                else:
                    epochs[0][0][1] = epochs[0][0][0][:]
                self.rejects()

    def test_underlying_support_collision_not_block_hash(self):
        corpus = self.inputs["contract"]["bindings"]["slot_registry"][0]
        corpus["slots"][1]["support"] = corpus["slots"][0]["support"][:]
        with self.assertRaisesRegex(writer.WriterError, "underlying-span"):
            writer._schedule(corpus, self.inputs["contract"]["bindings"]["batch_registry"][0]["epochs"])

    def test_link_and_new_batch_limits(self):
        for key, value in (("row_type", "LINK"), ("phase", "NEW")):
            with self.subTest(key=key):
                inputs = fixture()
                corpus = inputs["contract"]["bindings"]["slot_registry"][0]
                for slot in corpus["slots"][:2]:
                    slot[key] = value
                with self.assertRaisesRegex(writer.WriterError, "LINK/NEW"):
                    writer._schedule(corpus, inputs["contract"]["bindings"]["batch_registry"][0]["epochs"])

    def test_encoding_masks_eos_exact_targets_and_order(self):
        fit = self.build()
        encoded = writer.encode_fit(fit, ToyTokenizer())
        self.assertEqual(len(encoded["items"]), 160)
        self.assertEqual(encoded["epochs"], fit["contract"]["bindings"]["batch_registry"][0]["epochs"])
        for item in encoded["items"]:
            segment = item["encoded"]
            self.assertEqual(segment["labels"][-1], ToyTokenizer.eos_token_id)
            self.assertEqual(segment["labels"][0], -100)
            self.assertEqual(segment["n_target"], sum(label != -100 for label in segment["labels"]))
        self.assertEqual(encoded["padding"], "none")
        self.assertEqual(encoded, writer.encode_fit(fit, ToyTokenizer()))

    def test_extracted_encoder_preserves_original_payload(self):
        fit = self.build()
        corpus, schedule = writer._validate({key: value for key, value in fit.items() if key != "sha256"})
        bindings = fit["contract"]["bindings"]
        direct = writer._encode_corpus(fit["sha256"], corpus, schedule, fit["queries"],
                                        bindings["core_registry"]["render_registry"],
                                        bindings["environment"]["chat_template_sha256"], ToyTokenizer())
        self.assertEqual(writer.encode_fit(fit, ToyTokenizer()), direct)

    def test_truncation_and_template_drift_rejected(self):
        tokenizer = ToyTokenizer()
        tokenizer.chat_template = "other"
        with self.assertRaisesRegex(writer.WriterError, "template pin"):
            writer.encode_fit(self.build(), tokenizer)
        tokenizer = ToyTokenizer()
        tokenizer.apply_chat_template = lambda *args, **kwargs: "long context" * 60
        with self.assertRaisesRegex(writer.WriterError, "truncation"):
            writer.encode_fit(self.build(), tokenizer)

    def test_missing_eos_and_shared_mask_corruption(self):
        tokenizer = ToyTokenizer()
        tokenizer.eos_token_id = None
        with self.assertRaisesRegex(writer.WriterError, "EOS"):
            writer.encode_fit(self.build(), tokenizer)
        original = writer.shared.encode_item
        def corrupt(*args, **kwargs):
            result = original(*args, **kwargs)
            result.labels[0] = result.ids[0]
            return result
        with patch.object(writer.shared, "encode_item", side_effect=corrupt):
            with self.assertRaisesRegex(writer.WriterError, "mask drift"):
                writer.encode_fit(self.build(), ToyTokenizer())

    def test_imported_source_pin_drift(self):
        fit = self.build()
        writer.verify_sources(fit)
        self.inputs["binding"]["shared_trainer_sha256"] = "0" * 64
        with self.assertRaisesRegex(writer.WriterError, "shared pin drift"):
            writer.verify_sources(self.build())

    def test_protocol_pin_drift(self):
        pins = self.inputs["contract"]["bindings"]["source_pins"]
        pins[next(iter(pins))] = "0" * 64
        with self.assertRaisesRegex(writer.WriterError, "protocol source drift"):
            writer.verify_sources(self.build())

    def tokenizer_files(self, directory):
        root = Path(directory) / "toy_tokenizer"
        root.mkdir()
        (root / "toy.json").write_text("synthetic test only")
        tokenizer = ToyTokenizer()
        tokenizer.name_or_path = str(root)
        self.inputs["contract"]["tokenizer_receipt"] = dict(
            kind="offline_measurement", files={"toy.json": file_hash(root / "toy.json")},
            measurements=[dict(text="toy", token_ids=tokenizer.encode("toy"))])
        return tokenizer

    def test_actual_tokenizer_pins_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            tokenizer = self.tokenizer_files(directory)
            fit = self.build()
            writer.verify_tokenizer_files(fit, tokenizer)
            (Path(tokenizer.name_or_path) / "toy.json").write_text("changed")
            with self.assertRaisesRegex(writer.WriterError, "tokenizer file drift"):
                writer.verify_tokenizer_files(fit, tokenizer)

    def test_synthetic_and_changed_actual_tokenizer_fail(self):
        with self.assertRaisesRegex(writer.WriterError, "synthetic tokenizer"):
            writer.verify_tokenizer_files(self.build(), ToyTokenizer())
        with tempfile.TemporaryDirectory() as directory:
            tokenizer = self.tokenizer_files(directory)
            tokenizer.encode = lambda *args, **kwargs: [1]
            with self.assertRaisesRegex(writer.WriterError, "qualified measurement"):
                writer.verify_tokenizer_files(self.build(), tokenizer)

    def test_existing_output_not_reopened_factory_not_called(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "preserve"
            marker.write_text("untouched")
            with self.assertRaises(FileExistsError):
                writer.train_fit(self.build(), ToyTokenizer(), lambda: calls.append(True), directory)
            self.assertEqual(marker.read_text(), "untouched")
        self.assertEqual(calls, [])

    @unittest.skipIf(importlib.util.find_spec("torch") is not None, "explicit missing-dependency path on this VM")
    def test_missing_torch_preserves_failed_attempt_no_retry(self):
        self.validator.return_value = MOCK_RELEASE.copy()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "new"
            tokenizer = self.tokenizer_files(directory)
            with self.assertRaises(ModuleNotFoundError):
                writer.train_fit(self.build(), tokenizer, lambda: self.fail("no factory call"), out)
            self.assertTrue((out / "failed.json").exists())
            self.assertFalse((out / "completed.json").exists())
            with self.assertRaises(FileExistsError):
                writer.train_fit(self.build(), ToyTokenizer(), lambda: None, out)

    def mocked_training(self, directory, nonfinite=False, warm=False):
        self.validator.return_value = MOCK_RELEASE.copy()
        class Scalar:
            def __init__(self, value):
                self.value = value
            def item(self):
                return self.value
            def all(self):
                return self
            def backward(self):
                calls["backward"] += 1

        calls = dict(steps=0, backward=0, clips=[], seeds=[])
        parameter = SimpleNamespace(requires_grad=True)
        parameter.grad = SimpleNamespace(detach=lambda: SimpleNamespace(float=lambda: SimpleNamespace(norm=lambda: Scalar(2.0))))
        base_parameter = SimpleNamespace(dtype="bf16", is_floating_point=lambda: True,
                                         requires_grad_=lambda value: None)
        base = SimpleNamespace(peft_config={"warm": True} if warm else None,
                               named_parameters=lambda: iter([("base", base_parameter)]),
                               parameters=lambda: iter([base_parameter]), state_dict=lambda: {},
                               config=SimpleNamespace(num_hidden_layers=2))
        parameter.device = "cpu"
        def save(path, safe_serialization):
            Path(path).mkdir()
            (Path(path) / "adapter.safetensors").write_bytes(b"MOCK ONLY")
        model = SimpleNamespace(named_parameters=lambda: iter([("lora_A", parameter)]),
                                parameters=lambda: iter([parameter]), train=lambda: None,
                                save_pretrained=save)
        class Optimizer:
            def __init__(self, parameters, **kwargs):
                self.state = {}
                calls["optimizer"] = kwargs
            def zero_grad(self, set_to_none):
                pass
            def step(self):
                calls["steps"] += 1
            def state_dict(self):
                return {"step": calls["steps"]}
        def clip(parameters, maximum, error_if_nonfinite):
            calls["clips"].append((maximum, error_if_nonfinite))
            return Scalar(2.0)
        torch = SimpleNamespace(bfloat16="bf16", manual_seed=lambda seed: calls["seeds"].append(seed),
                                optim=SimpleNamespace(AdamW=Optimizer),
                                isfinite=lambda value: Scalar(not nonfinite), stack=lambda values: values,
                                linalg=SimpleNamespace(vector_norm=lambda values: Scalar(0.5)),
                                nn=SimpleNamespace(utils=SimpleNamespace(clip_grad_norm_=clip)))
        peft = SimpleNamespace(get_peft_model=lambda supplied, config: model)
        tokenizer = self.tokenizer_files(Path(directory).parent)
        fit = self.build()
        environment = fit["contract"]["bindings"]["environment"]
        def objective(supplied_model, examples, device):
            self.assertEqual(len(examples), 4)
            return Scalar(0.5), sum(example["n_target"] for example in examples)
        with patch.dict(sys.modules, {"torch": torch, "peft": peft}), \
             patch.object(writer.shared, "lora_config", return_value="MOCK"), \
             patch.object(writer, "_batch_objective", side_effect=objective), \
             patch.object(writer, "_state_hash", return_value=fit["binding"]["base_state_sha256"]), \
             patch.object(writer, "_rng_hash", return_value={"cpu": "6" * 64, "cuda": []}):
            result = writer.train_fit(fit, tokenizer, lambda: (base, environment), directory)
        return result, calls

    def test_mocked_full_200_updates_final_only(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "fit"
            result, calls = self.mocked_training(out)
            self.assertEqual((calls["steps"], calls["backward"]), (200, 200))
            self.assertEqual(calls["clips"], [(1.0, True)] * 200)
            self.assertEqual(calls["seeds"], [7, 8])
            self.assertEqual(calls["optimizer"], dict(lr=3e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01))
            self.assertEqual(result["updates"], 200)
            self.assertEqual(len((out / "updates.jsonl").read_text().splitlines()), 200)
            self.assertFalse((out / "failed.json").exists())
            self.assertEqual(len(list(out.glob("adapter*"))), 1)

    def test_mocked_nonfinite_loss_aborts_no_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "fit"
            with self.assertRaisesRegex(writer.WriterError, "nonfinite loss"):
                self.mocked_training(out, nonfinite=True)
            self.assertTrue((out / "failed.json").exists())
            self.assertFalse((out / "adapter").exists())
            self.assertFalse((out / "completed.json").exists())
            self.assertEqual((out / "updates.jsonl").read_text(), "")

    def test_mocked_warm_start_rejected_before_training(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "fit"
            with self.assertRaisesRegex(writer.WriterError, "warm/adapted"):
                self.mocked_training(out, warm=True)
            self.assertTrue((out / "failed.json").exists())
            self.assertFalse((out / "initial.json").exists())


class NativeGateTests(unittest.TestCase):
    def test_profile_receipts_forwarded_verbatim_without_contract_mutation(self):
        contract = {"sealed": "synthetic, not released"}
        profiles = [{"id": "profile/toy", "evidence_sha256": "7" * 64}]
        before = copy.deepcopy((contract, profiles))
        with patch.object(writer.prepare, "validate_execution_contract", return_value=MOCK_RELEASE.copy()) as validate:
            writer._require_execution_contract(contract, profile_receipts=profiles)
            self.assertIs(validate.call_args.args[0], contract)
            self.assertIs(validate.call_args.kwargs["profile_receipts"], profiles)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "blocked"
            with patch.object(writer.prepare, "validate_execution_contract", return_value={"execution_contract_valid": False}) as validate:
                with self.assertRaisesRegex(writer.WriterError, "native fitting blocked"):
                    writer.train_fit({"contract": contract}, ToyTokenizer(),
                                     lambda: self.fail("factory must not be called"), out,
                                     profile_receipts=profiles)
                self.assertIs(validate.call_args.args[0], contract)
                self.assertIs(validate.call_args.kwargs["profile_receipts"], profiles)
            self.assertFalse(out.exists())
        self.assertEqual((contract, profiles), before)

    def test_real_unresolved_contract_blocks_before_factory_or_encoding(self):
        from test_pcfl_vertical_prepare import synthetic_bindings, synthetic_tokenizer
        bindings = synthetic_bindings()
        contract = writer.prepare.build_execution_contract(bindings, synthetic_tokenizer(bindings))
        report = writer.prepare.validate_execution_contract(contract)
        self.assertIs(report["execution_contract_valid"], False)
        self.assertTrue(report["missing_interfaces"])
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "never_claimed"
            with patch.object(writer, "encode_fit", side_effect=AssertionError("must not encode")), \
                    patch.object(writer, "_encode_corpus", side_effect=AssertionError("must not encode corpus")), \
                    patch.object(writer, "_train_encoded", side_effect=AssertionError("must not enter numerical loop")):
                with self.assertRaisesRegex(writer.WriterError, "native fitting blocked"):
                    writer.train_fit({"contract": contract}, ToyTokenizer(),
                                     lambda: self.fail("factory must not be called"), out)
            self.assertFalse(out.exists())

    def test_false_missing_and_truthy_release_fields_reject(self):
        reports = [{}, {"bridge_invariants_valid": True},
                   {**MOCK_RELEASE, "missing_interfaces": ["unresolved_production_D"]}]
        for key in ("execution_contract_valid", "static_contract_complete", "ready_for_model_calls"):
            for value in (False, 1, "true", None):
                reports.append({**MOCK_RELEASE, key: value})
        for report in reports:
            with self.subTest(report=report), tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / "never_claimed"
                with patch.object(writer.prepare, "validate_execution_contract", return_value=report):
                    with self.assertRaisesRegex(writer.WriterError, "native fitting blocked"):
                        writer.train_fit({"contract": {}}, ToyTokenizer(),
                                         lambda: self.fail("factory must not be called"), out)
                self.assertFalse(out.exists())


@unittest.skipUnless(importlib.util.find_spec("torch") is not None, "Torch absent; no numerical/native qualification")
class TorchObjectiveTests(unittest.TestCase):
    def test_pooled_not_sequence_mean_and_single_backward(self):
        import torch
        from types import SimpleNamespace
        class Toy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.bias = torch.nn.Parameter(torch.tensor([0.0, 2.0, -1.0]))
            def forward(self, input_ids, attention_mask, use_cache):
                return SimpleNamespace(logits=self.bias.expand(1, input_ids.shape[1], 3))
        model = Toy()
        examples = [dict(ids=[0, 1], labels=[-100, 1]), dict(ids=[0, 2, 2, 2], labels=[-100, 2, 2, 2])]
        loss, count = writer._batch_objective(model, examples, "cpu")
        logprob = torch.log_softmax(model.bias, dim=0)
        self.assertEqual(count, 4)
        self.assertTrue(torch.allclose(loss, -(logprob[1] + 3 * logprob[2]) / 4))
        self.assertFalse(torch.allclose(loss, -(logprob[1] + logprob[2]) / 2))
        loss.backward()
        self.assertTrue(torch.isfinite(model.bias.grad).all())


@unittest.skipUnless(os.environ.get("ASTRA_PCFL_TINY_CPU") == "1", "opt-in tiny CPU lifecycle; not native qualification")
class TinyCPUWriterTests(unittest.TestCase):
    """Random tiny Qwen only; synthetic release, bank and tokenizer fixture.

    Main runs this in a fresh CPU-only process under an external 120s timeout.
    No pretrained loader is called, including when reloading the saved LoRA.
    """

    def test_real_bf16_qwen_lora_adamw_200_steps_save_reload(self):
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), "1")
        self.assertEqual(os.environ.get("TRANSFORMERS_OFFLINE"), "1")
        import torch
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict, set_peft_model_state_dict
        from safetensors.torch import load_file
        from transformers import Qwen2Config, Qwen2ForCausalLM

        self.assertFalse(torch.cuda.is_initialized())
        old_threads = torch.get_num_threads()
        old_rng = torch.get_rng_state()
        self.addCleanup(torch.set_num_threads, old_threads)
        self.addCleanup(torch.set_rng_state, old_rng)
        torch.set_num_threads(1)
        torch.manual_seed(64011)
        config = Qwen2Config(vocab_size=64, hidden_size=16, intermediate_size=32,
                             num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
                             max_position_embeddings=512, bos_token_id=0, eos_token_id=1,
                             pad_token_id=0, attention_dropout=0.0, tie_word_embeddings=False,
                             use_cache=False)
        config._attn_implementation = "eager"
        base = Qwen2ForCausalLM(config).to(device="cpu", dtype=torch.bfloat16)
        clean_state = {name: value.detach().clone() for name, value in base.state_dict().items()}
        base_parameters = dict(base.named_parameters())
        initial_base = {name: value.detach().clone() for name, value in base_parameters.items()}

        class CompactToyTokenizer(ToyTokenizer):
            eos_token_id = 1

            def encode(self, text, add_special_tokens=False):
                payload = text.encode("utf-8")
                return [2 + hashlib.sha256(payload[start:start + 8]).digest()[0] % 62
                        for start in range(0, len(payload), 8)]

        real_hash = writer._state_hash
        optimizer_states, lora_states = [], []

        def observe_hash(value):
            result = real_hash(value)
            if isinstance(value, dict) and set(value) == {"state", "param_groups"}:
                optimizer_states.append(copy.deepcopy(value))
            elif isinstance(value, dict) and value and all("lora_" in str(name) for name in value):
                lora_states.append({name: parameter.detach().clone() for name, parameter in value.items()})
            return result

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            token_root = root / "toy_tokenizer"
            token_root.mkdir()
            (token_root / "toy.json").write_text("hash-of-eight-byte-chunks toy tokenizer; NOT Qwen tokenizer")
            tokenizer = CompactToyTokenizer()
            tokenizer.name_or_path = str(token_root)
            inputs = fixture()
            inputs["contract"]["tokenizer_receipt"] = dict(
                kind="offline_measurement", files={"toy.json": file_hash(token_root / "toy.json")},
                measurements=[dict(text="toy measurement", token_ids=tokenizer.encode("toy measurement"))])
            inputs["binding"]["base_state_sha256"] = real_hash(base.state_dict())
            inputs["binding"]["contract_sha256"] = writer.digest(inputs["contract"])
            calls = []

            def base_factory():
                calls.append("fresh_random_cpu_base")
                return base, copy.deepcopy(inputs["contract"]["bindings"]["environment"])

            with patch.object(writer.prepare, "validate_execution_contract", return_value=MOCK_RELEASE.copy()):
                fit = writer.build_fit(**inputs)
                sealed_before = writer.canonical(fit)
                with patch.object(writer, "_state_hash", side_effect=observe_hash):
                    receipt = writer.train_fit(fit, tokenizer, base_factory, root / "fit",
                                               profile_receipts=[{"id": "synthetic-release-test-only"}])
                self.assertEqual(writer.canonical(fit), sealed_before)

            self.assertEqual(calls, ["fresh_random_cpu_base"])
            self.assertEqual((receipt["updates"], receipt["presentations"], receipt["training_forwards"]), (200, 800, 800))
            self.assertEqual(receipt["status"], "COMPLETE")
            self.assertFalse(receipt["native_custody_verified"])
            self.assertEqual(len(optimizer_states), 2)
            self.assertEqual(len(lora_states), 2)
            self.assertEqual(optimizer_states[0]["state"], {})
            self.assertTrue(optimizer_states[1]["state"])
            for phase, index in (("initial", 0), ("final", 1)):
                self.assertEqual(receipt[phase]["lora"], real_hash(lora_states[index]))
                self.assertEqual(receipt[phase]["optimizer"], real_hash(optimizer_states[index]))
            self.assertNotEqual(receipt["initial"]["lora"], receipt["final"]["lora"])
            self.assertNotEqual(receipt["initial"]["optimizer"], receipt["final"]["optimizer"])
            self.assertEqual(len(optimizer_states[1]["state"]), len(lora_states[1]))
            for state in optimizer_states[1]["state"].values():
                self.assertEqual(state["step"].item(), 200)
                self.assertTrue(torch.isfinite(state["exp_avg"]).all())
                self.assertTrue(torch.isfinite(state["exp_avg_sq"]).all())
            self.assertTrue(any(torch.count_nonzero(state["exp_avg"]).item()
                                for state in optimizer_states[1]["state"].values()))
            for group in optimizer_states[1]["param_groups"]:
                self.assertEqual((group["lr"], group["betas"], group["eps"], group["weight_decay"]),
                                 (3e-5, (0.9, 0.999), 1e-8, 0.01))
            for name, parameter in base_parameters.items():
                self.assertTrue(torch.equal(parameter.detach(), initial_base[name]), name)
                self.assertFalse(parameter.requires_grad, name)
                self.assertEqual(parameter.device.type, "cpu")
                self.assertEqual(parameter.dtype, torch.bfloat16)
            self.assertTrue(any(not torch.equal(lora_states[0][name], lora_states[1][name])
                                for name in lora_states[0]))

            out = root / "fit"
            rows = [json.loads(line) for line in (out / "updates.jsonl").read_text().splitlines()]
            encoding = json.loads((out / "encoding.json").read_text())
            self.assertEqual([row["update"] for row in rows], list(range(1, 201)))
            self.assertEqual(sum(row["supervised_tokens"] for row in rows), 5 * encoding["target_tokens_per_epoch"])
            self.assertEqual([row["items"] for row in rows],
                             [batch for epoch in encoding["epochs"] for batch in epoch])
            for row in rows:
                self.assertTrue(all(math.isfinite(row[key]) for key in ("loss", "pre_clip_norm", "post_clip_norm")))
                self.assertLessEqual(row["post_clip_norm"], 1.00001)
                self.assertEqual(row["rng_before"]["cuda"], [])
                self.assertEqual(row["rng_after"]["cuda"], [])
            for name, expected in receipt["files"].items():
                self.assertEqual(file_hash(out / name), expected)
            self.assertEqual(json.loads((out / "completed.json").read_text()), receipt)
            self.assertFalse((out / "failed.json").exists())
            self.assertEqual([path.name for path in out.iterdir() if path.is_dir()], ["adapter"])

            adapter_config = json.loads((out / "adapter" / "adapter_config.json").read_text())
            self.assertEqual((adapter_config["r"], adapter_config["lora_alpha"], adapter_config["lora_dropout"]),
                             (8, 16, 0.05))
            self.assertEqual(set(adapter_config["target_modules"]), set(writer.shared.ALL_PROJ))
            saved = load_file(str(out / "adapter" / "adapter_model.safetensors"), device="cpu")
            reloaded_base = Qwen2ForCausalLM(copy.deepcopy(config)).to(device="cpu", dtype=torch.bfloat16)
            reloaded_base.load_state_dict(clean_state, strict=True)
            self.assertEqual(real_hash(reloaded_base.state_dict()), inputs["binding"]["base_state_sha256"])
            reloaded = get_peft_model(reloaded_base, LoraConfig(**adapter_config))
            load_result = set_peft_model_state_dict(reloaded, saved)
            self.assertEqual(load_result.unexpected_keys, [])
            restored = get_peft_model_state_dict(reloaded, save_embedding_layers=False)
            self.assertEqual(set(restored), set(saved))
            for name in saved:
                self.assertTrue(torch.equal(restored[name].cpu(), saved[name]), name)
            base.eval()
            reloaded.eval()
            example = torch.tensor([encoding["items"][0]["encoded"]["ids"]], dtype=torch.long, device="cpu")
            with torch.no_grad():
                expected = base(input_ids=example, attention_mask=torch.ones_like(example), use_cache=False).logits
                actual = reloaded(input_ids=example, attention_mask=torch.ones_like(example), use_cache=False).logits
            self.assertTrue(torch.isfinite(expected).all())
            self.assertTrue(torch.equal(actual, expected), "same-process CPU save/reload logits must be identical")
            self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
