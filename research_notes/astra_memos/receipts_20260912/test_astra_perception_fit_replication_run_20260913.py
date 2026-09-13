"""CPU fixtures only: no real tokenizer, model, GPU, network or old material."""
from collections import UserDict
import contextlib
import copy
from dataclasses import asdict
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib


PATH = Path(os.environ.get("PERCEPTION_DRIVER", "/tmp/astra_perception_fit_replication_run_20260913.py"))
PROBE_PATH = Path(os.environ.get("PERCEPTION_PROBE_DRIVER", "/tmp/astra_birth_skill_probe_run_20260913.py"))
SOURCE = Path(os.environ.get("PERCEPTION_PUBLIC_SOURCE", "/data/home/rohing/dream-state"))
spec = importlib.util.spec_from_file_location("perception_replication_runtime", PATH)
runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtime
spec.loader.exec_module(runtime)


class TokenizerFixture:
    chat_template = "CPU_QWEN_SHAPED_FULL_ASSISTANT_TEMPLATE"
    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token_id = 0
    as_mapping = True
    trailer = "\n"

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        words = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s+", text)
        assert "".join(words) == text
        return [1 if word == self.eos_token else 2 if word == "<|im_start|>" else zlib.crc32(word.encode()) + 3 for word in words]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": "Fixture generic system."})
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        elif self.trailer != "\n":
            text = text[:-1] + self.trailer
        if not tokenize:
            return text
        ids = self.encode(text, add_special_tokens=False)
        return UserDict(input_ids=ids) if self.as_mapping else ids


class CaptureFixture:
    instances = []
    answers = {}
    fail_at = None
    corrupt_route = False
    corrupt_input = False
    raw_text = None

    def __init__(self, plan, probe, adapter):
        self.seen = []
        self.closed = False
        self.probe = probe
        self.route = None if adapter is None else dict(name="perception", id=1, path=adapter)
        self.instances.append(self)

    def generate(self, messages):
        if self.fail_at is not None and len(self.seen) == self.fail_at:
            raise RuntimeError("fixture generation failure")
        self.seen.append(copy.deepcopy(messages))
        native = self.probe.render(TokenizerFixture(), messages)
        text = self.raw_text if self.raw_text is not None else self.answers[messages[-1]["content"]]
        ids = TokenizerFixture().encode(text)
        response = dict(**native, text=text, output_token_ids=ids,
                        actual_prompt_token_ids=native["prompt_token_ids"], finish_reason="stop", stop_reason=1,
                        decoded_output=text, started=1.0, ended=2.0,
                        lora_request={"wrong": "adapter"} if self.corrupt_route else self.route)
        if self.corrupt_input:
            response["actual_prompt_token_ids"] = [999]
        return response

    def close(self):
        self.closed = True


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="perception_cpu_")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "run"
        self.model = self.home / "model"
        self.model.mkdir()
        self.probe_hash = runtime.digest(PROBE_PATH)
        self.probe = runtime.load_probe(PROBE_PATH, self.probe_hash)
        self.corpus, self.trainer = runtime.source_api(SOURCE)
        self.model_files = {"config.json": "a" * 64, "fixture.safetensors": "b" * 64}
        self.fixture_environment = {"cpu_fixture": True}
        self.binding = dict(schema=1, scope=self.probe.SCOPE, visibility="model-only-public", approved_by="Main",
                            model_name=self.probe.MODEL_NAME, revision=self.probe.REVISION,
                            model_files=self.model_files, native_environment=self.fixture_environment,
                            source_files={name: runtime.digest(SOURCE / name) for name in self.probe.SOURCE_NAMES})
        self.binding_path = self.home / "binding.json"
        runtime.write(self.binding_path, self.binding)
        def pinned_probe(path, expected):
            runtime.require(runtime.digest(path) == expected, "Boyle final driver hash differs")
            return self.probe
        self.patch(runtime, "load_probe", pinned_probe)
        self.patch(runtime, "environment", lambda probe: self.fixture_environment)
        self.patch(self.probe, "model_hashes", lambda model: self.model_files)
        self.patch(self.probe, "native_environment", lambda: self.fixture_environment)
        self.patch(self.probe, "native_tokenizer", lambda model: TokenizerFixture())
        self.kwargs = dict(root=self.root, source=SOURCE, model=self.model, probe_driver=PROBE_PATH, learner_seed=1,
                           probe_sha256=self.probe_hash, binding_path=self.binding_path,
                           binding_sha256=runtime.digest(self.binding_path),
                           corpus_sha256=self.binding["source_files"]["organism_v6/birth_skill_corpus.py"],
                           gpu_uuid="GPU-00000000-0000-0000-0000-000000000001", gpu_index=0,
                           lease_end=time.time() + 7200)
        CaptureFixture.instances = []
        CaptureFixture.answers = {}
        CaptureFixture.fail_at = None
        CaptureFixture.corrupt_route = False
        CaptureFixture.corrupt_input = False
        CaptureFixture.raw_text = None

    def patch(self, target, name, replacement):
        patcher = patch.object(target, name, replacement)
        patcher.start()
        self.addCleanup(patcher.stop)

    def prepare(self):
        result = runtime.prepare(**self.kwargs)
        self.pin = result["plan_sha256"]
        self.plan, _ = runtime.verify(self.root, self.pin)
        dev = runtime.read(self.root / "dev.json")
        CaptureFixture.answers = {row["input_messages"][-1]["content"]: row["raw_target"] for row in dev["absent"]}
        return result

    def manifest(self, prepared):
        return dict(config=self.plan["config"], empty=False, steps=12, micro_batches=12, epochs_run=4, nonfinite_batches=0,
                    corpus=dict(n_items=12, n_encoded=12, n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=12),
                    tokens=dict(target=prepared["target_tokens"]), train_tokens_seen=4 * prepared["total_tokens"],
                    mean_loss_per_epoch=[1.0, .9, .8, .7], final_loss=.7)

    def fit_fixture(self, stage):
        directory = self.root / "run" / stage
        arm = stage.removeprefix("fit_")
        prepared = runtime.read(self.root / f"train_{arm}.json")
        adapter = directory / "adapter"
        adapter.mkdir()
        runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                                                            target_modules=self.plan["config"]["target_modules"]))
        (adapter / "adapter_model.safetensors").write_text("CPU fixture only: not a model or actual weights")
        (adapter / "DONE").write_text("ok\n")
        runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
        runtime.write(directory / "fit.json", dict(arm=arm, learner_seed=self.plan["learner_seed"], adapter=str(adapter), adapter_files=runtime.tree(adapter),
                                                   updates=12, presentations=48))

    def fake_stage(self, plan, pin, stage, deadline, probe):
        directory = self.root / "run" / stage
        directory.mkdir()
        pid = 80000 + runtime.STAGES.index(stage)
        identity = dict(pid=pid, pgid=pid, stage=stage, learner_seed=plan["learner_seed"], plan_sha256=pin)
        runtime.write(directory / "started.json", dict(identity, time=time.time()))
        runtime.write(directory / "launch.json", identity)
        if stage.startswith("fit_"):
            self.fit_fixture(stage)
        else:
            with patch.object(runtime, "Native", CaptureFixture):
                runtime.capture_cell(plan, stage, probe)
        runtime.write(directory / "released.json", dict(pid=pid, pgid=pid, time=time.time()))

    def complete(self):
        self.prepare()
        with patch.object(runtime, "run_stage", self.fake_stage):
            result = runtime.controller(self.root, self.pin, allow_gpu=True)
        self.completion = result["completion_sha256"]
        return result

    def prepare_at(self, learner_seed, name):
        self.root = self.home / name
        self.kwargs.update(root=self.root, learner_seed=learner_seed)
        self.prepare()
        return {name: runtime.read(self.root / name) for name in
                ("train_absent.json", "train_present.json", "dev.json", "calls.json", "plan.json")}

    def test_replication_seed_is_required_and_restricted_in_python_and_cli(self):
        missing = dict(self.kwargs)
        missing.pop("learner_seed")
        with self.assertRaises(TypeError):
            runtime.prepare(**missing)
        for seed in (None, 0, 3, -1, True, False, 1.0, "1"):
            with self.subTest(seed=seed), self.assertRaisesRegex(ValueError, "integer 1 or 2"):
                runtime.prepare(**dict(self.kwargs, learner_seed=seed))
        self.assertFalse(self.root.exists())
        arguments = ["prepare"]
        for key, value in self.kwargs.items():
            if key != "learner_seed":
                arguments.extend(["--" + key.replace("_", "-"), str(value)])
        for seed in (1, 2):
            with patch.object(runtime, "prepare", return_value={"fixture": True}) as prepare, contextlib.redirect_stdout(io.StringIO()):
                runtime.main(arguments + ["--learner-seed", str(seed)])
            self.assertEqual(prepare.call_args.kwargs["learner_seed"], seed)
        for suffix in ([], ["--learner-seed", "0"], ["--learner-seed", "3"], ["--learner-seed", "1.0"]):
            with patch.object(runtime, "prepare") as prepare, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failed:
                runtime.main(arguments + suffix)
            self.assertEqual(failed.exception.code, 2)
            prepare.assert_not_called()

    def test_same_seed_reproduces_order_across_roots_and_matches_anchor_arms(self):
        for seed in (1, 2):
            first = self.prepare_at(seed, f"seed{seed}_first")
            second = self.prepare_at(seed, f"seed{seed}_second")
            for name in ("train_absent.json", "train_present.json", "calls.json", "dev.json"):
                self.assertEqual(first[name], second[name])
            absent, present = first["train_absent.json"], first["train_present.json"]
            self.assertEqual(absent["epoch_order"], present["epoch_order"])
            self.assertEqual(absent["learner_seed"], seed)
            self.assertEqual(present["learner_seed"], seed)
            self.assertEqual(absent["target_tokens"], present["target_tokens"])
            expected_rows = {item["group"] for item in absent["items"]}
            self.assertEqual(len(absent["epoch_order"]), 4)
            for epoch in absent["epoch_order"]:
                self.assertEqual(len(epoch), 12)
                self.assertEqual(set(epoch), expected_rows)

    def test_different_seeds_change_only_fit_seed_and_epoch_order_not_inputs(self):
        first = self.prepare_at(1, "learner1")
        second = self.prepare_at(2, "learner2")
        for arm in runtime.ARMS:
            left, right = first[f"train_{arm}.json"], second[f"train_{arm}.json"]
            self.assertNotEqual(left["epoch_order"], right["epoch_order"])
            self.assertEqual({key: value for key, value in left.items() if key not in ("learner_seed", "epoch_order")},
                             {key: value for key, value in right.items() if key not in ("learner_seed", "epoch_order")})
        for name in ("dev.json", "calls.json"):
            self.assertEqual(first[name], second[name])
        for key in ("source_hashes", "model", "model_files", "binding", "anchor", "engine", "params", "stages",
                    "outer_seconds", "collection_seconds", "gpu_query_seconds", "parent_driver_sha256"):
            self.assertEqual(first["plan.json"][key], second["plan.json"][key])
        left, right = first["plan.json"]["config"], second["plan.json"]["config"]
        self.assertEqual((left["seed"], right["seed"]), (1, 2))
        self.assertEqual({key: value for key, value in left.items() if key != "seed"},
                         {key: value for key, value in right.items() if key != "seed"})
        self.assertEqual(runtime.RECIPE["seed"], 0)
        self.assertEqual(runtime.PARAMS["seed"], 0)
        self.assertEqual(runtime.ENGINE["seed"], 0)
        self.assertEqual(len(runtime.CELLS), 6)
        self.assertEqual((runtime.OUTER_SECONDS, runtime.COLLECTION_SECONDS, runtime.FIT_SECONDS, runtime.READOUT_SECONDS),
                         (2700, 180, 600, 240))

    def test_resealed_forbidden_plan_config_and_prepared_seeds_are_rejected(self):
        self.prepare()
        base = copy.deepcopy(self.plan)
        variants = []
        for seed in (None, 0, 3, True):
            wrong = copy.deepcopy(base)
            wrong["learner_seed"] = seed
            variants.append(wrong)
        wrong = copy.deepcopy(base)
        wrong["config"]["seed"] = 2
        variants.append(wrong)
        wrong = copy.deepcopy(base)
        wrong["parent_driver_sha256"] = "0" * 64
        variants.append(wrong)
        wrong = copy.deepcopy(base)
        wrong["scope"] = "authored_perception_12train_12dev_twofits_sixreadouts_v1"
        variants.append(wrong)
        for wrong in variants:
            (self.root / "plan.json").write_bytes(runtime.encoded(wrong))
            with self.subTest(seed=wrong["learner_seed"]), self.assertRaises(ValueError):
                runtime.verify(self.root, runtime.digest(self.root / "plan.json"))
        prepared = runtime.read(self.root / "train_present.json")
        prepared["learner_seed"] = 2
        (self.root / "train_present.json").write_bytes(runtime.encoded(prepared))
        wrong = copy.deepcopy(base)
        wrong["input_hashes"]["train_present.json"] = runtime.digest(self.root / "train_present.json")
        (self.root / "plan.json").write_bytes(runtime.encoded(wrong))
        with self.assertRaisesRegex(ValueError, "prepared learner seed differs"):
            runtime.verify(self.root, runtime.digest(self.root / "plan.json"))

    def test_worker_rejects_epoch_order_from_another_seed_before_training(self):
        self.prepare()
        path = self.root / "train_absent.json"
        prepared = runtime.read(path)
        rows = self.corpus.build_slice("perception", split="train", system_anchor=None)["rows"]
        other = runtime.encode_training(rows, TokenizerFixture(), self.trainer, self.probe, 2)
        self.assertNotEqual(prepared["epoch_order"], other["epoch_order"])
        prepared["epoch_order"] = other["epoch_order"]
        path.write_bytes(runtime.encoded(prepared))
        with patch.object(runtime, "load_native_model", return_value=(TokenizerFixture(), SimpleNamespace())), \
                patch.object(self.trainer, "run_training") as train, self.assertRaisesRegex(ValueError, "epoch-order seed mismatch"):
            runtime.fit_one(self.plan, "fit_absent", self.probe)
        train.assert_not_called()

    def test_seed2_native_receipt_fixtures_keep_probe_and_engine_seeds_zero(self):
        self.kwargs["learner_seed"] = 2
        complete = self.complete()
        self.assertEqual(complete["learner_seed"], 2)
        self.assertEqual(self.plan["learner_seed"], self.plan["config"]["seed"])
        for stage in runtime.STAGES:
            directory = self.root / "run" / stage
            for name in ("started.json", "launch.json"):
                self.assertEqual(runtime.read(directory / name)["learner_seed"], 2)
            if stage.startswith("fit_"):
                self.assertEqual(runtime.read(directory / "fit.json")["learner_seed"], 2)
                manifest = runtime.read(directory / "adapter" / "train_manifest.json")
                self.assertEqual(manifest["config"]["seed"], 2)
                self.assertEqual((manifest["steps"], manifest["epochs_run"]), (12, 4))
            else:
                identity = runtime.read(directory / "identity.json")
                self.assertEqual(identity["learner_seed"], 2)
                self.assertEqual(identity["params"]["seed"], 0)
                self.assertEqual(identity["engine"]["seed"], 0)
                self.assertTrue(identity["engine"]["enable_lora"])
                self.assertEqual(identity["engine"]["max_lora_rank"], 32)
        out = self.home / "learner2_scores"
        result = runtime.collect(self.root, self.pin, self.completion, out)
        self.assertEqual(result["learner_seed"], 2)
        report = runtime.read(out / "scores.json")
        self.assertEqual(report["learner_seed"], 2)
        self.assertEqual(report["calls"], 72)
        self.assertIn("n-seed diagnostic", report["claim"])
        self.assertFalse(report["automatic_pass"])

    def test_wrong_learner_or_generation_seed_in_receipts_is_rejected(self):
        self.complete()
        files = [self.root / "run" / "fit_absent" / "fit.json",
                 self.root / "run" / "OFF__absent" / "started.json",
                 self.root / "run" / "OFF__absent" / "launch.json",
                 self.root / "run" / "OFF__absent" / "identity.json"]
        for path in files:
            original = path.read_bytes()
            receipt = runtime.read(path)
            receipt["learner_seed"] = 2
            path.write_bytes(runtime.encoded(receipt))
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                runtime.validate_completed(self.plan, self.pin, self.probe)
            path.write_bytes(original)
        path = self.root / "run" / "OFF__absent" / "identity.json"
        original = path.read_bytes()
        for key in ("engine", "params"):
            receipt = runtime.read(path)
            receipt[key]["seed"] = 1
            path.write_bytes(runtime.encoded(receipt))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "identity mismatch"):
                runtime.validate_completed(self.plan, self.pin, self.probe)
            path.write_bytes(original)

    def test_fit_manifest_cannot_mix_prepared_and_optimizer_seed(self):
        self.prepare()
        prepared = runtime.read(self.root / "train_absent.json")
        manifest = self.manifest(prepared)
        prepared["learner_seed"] = 2
        with self.assertRaisesRegex(ValueError, "fit/prepared learner seed"):
            runtime.check_fit_manifest(manifest, prepared, self.plan["config"])
        prepared["learner_seed"] = 1
        manifest["config"] = dict(self.plan["config"], seed=2)
        with self.assertRaisesRegex(ValueError, "fit completion/update"):
            runtime.check_fit_manifest(manifest, prepared, self.plan["config"])

    def test_seed_binding_does_not_equate_boolean_or_float_with_integer(self):
        for actual in (None, True, False, 1.0, "1", 0, 3, 2):
            self.assertFalse(runtime.seed_matches(actual, 1))
        self.assertTrue(runtime.seed_matches(1, 1))
        self.assertTrue(runtime.seed_matches(2, 2))
        self.prepare()
        prepared = runtime.read(self.root / "train_absent.json")
        for value in (True, 1.0):
            manifest = self.manifest(prepared)
            manifest["config"] = dict(self.plan["config"], seed=value)
            with self.assertRaisesRegex(ValueError, "fit completion/update"):
                runtime.check_fit_manifest(manifest, prepared, self.plan["config"])

    def test_prepare_exact_counts_recipe_anchor_and_no_score(self):
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("scoring during prepare")):
            result = self.prepare()
        self.assertEqual(result["status"], "PREPARED_NOT_LAUNCHED")
        self.assertEqual(self.plan["stages"], list(runtime.STAGES))
        self.assertEqual(self.plan["config"], asdict(self.trainer.TrainConfig(**runtime.learner_recipe(self.kwargs["learner_seed"]), model=str(self.model))))
        self.assertEqual(self.plan["anchor"], self.probe.ANCHOR)
        self.assertTrue(self.plan["engine"]["enable_lora"])
        self.assertEqual(self.plan["engine"]["max_lora_rank"], 32)
        self.assertFalse(self.plan["config"]["add_eos"])
        for anchor in runtime.ARMS:
            prepared = runtime.read(self.root / f"train_{anchor}.json")
            self.assertEqual(len(prepared["items"]), 12)
            self.assertEqual(len(prepared["epoch_order"]), 4)
            self.assertEqual(len(runtime.read(self.root / "dev.json")[anchor]), 12)
        self.assertFalse((self.root / "run").exists())

    def test_full_assistant_target_eos_masks_and_batchencoding(self):
        self.prepare()
        absent = runtime.read(self.root / "train_absent.json")
        present = runtime.read(self.root / "train_present.json")
        self.assertEqual(absent["target_tokens"], present["target_tokens"])
        self.assertEqual(absent["epoch_order"], present["epoch_order"])
        for arm in (absent, present):
            for audit in arm["encoding"]:
                labels = audit["labels"]
                ids = audit["input_ids"]
                self.assertEqual([label for label in labels if label != -100], audit["supervised_ids"])
                self.assertEqual(audit["supervised_ids"].count(1), 1)
                self.assertEqual(labels[-1], -100)
                self.assertEqual(ids[-2], 1)
                self.assertEqual(labels[-2], 1)
                self.assertTrue(all(label == -100 for label in labels[:len(audit["native_prompt"]["prompt_token_ids"]) ]))
                self.assertEqual(ids, TokenizerFixture().encode(audit["full_assistant_text"]))
                self.assertIn("<|im_start|>assistant\n", audit["full_assistant_text"])
        self.assertEqual(absent["encoding"][0]["native_prompt"]["actual_system_text"], "Fixture generic system.")
        self.assertEqual(present["encoding"][0]["native_prompt"]["actual_system_text"], self.probe.ANCHOR)

    def test_token_vector_accepts_mapping_and_rejects_nested_bool_empty(self):
        self.assertEqual(runtime.token_ids(UserDict(input_ids=[1, 2])), [1, 2])
        for value in ([True], [], [[1, 2]], {"wrong": [1]}, {"input_ids": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runtime.token_ids(value)
        tokenizer = TokenizerFixture()
        tokenizer.as_mapping = False
        row = self.corpus.build_slice("perception", split="train", system_anchor=None)["rows"][0]
        runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)

    def test_native_bad_tail_and_template_token_mismatch_rejected(self):
        row = self.corpus.build_slice("perception", split="train", system_anchor=None)["rows"][0]
        tokenizer = TokenizerFixture()
        tokenizer.trailer = "UNSUPPORTED_TEMPLATE_CONTENT"
        with self.assertRaisesRegex(ValueError, "trailer"):
            runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)
        tokenizer = TokenizerFixture()
        original = tokenizer.apply_chat_template
        def inconsistent(messages, tokenize, add_generation_prompt):
            result = original(messages, tokenize, add_generation_prompt)
            if tokenize and not add_generation_prompt:
                result["input_ids"][0] += 1
            return result
        tokenizer.apply_chat_template = inconsistent
        with self.assertRaisesRegex(ValueError, "template/token mismatch"):
            runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)

    def test_native_boundary_truncation_and_dev_loss_are_rejected(self):
        row = self.corpus.build_slice("perception", split="train", system_anchor=None)["rows"][0]
        long_row = copy.deepcopy(row)
        long_row["input_messages"][0]["content"] += " extra" * 1200
        with self.assertRaisesRegex(ValueError, "truncation"):
            runtime.training_item(long_row, TokenizerFixture(), self.trainer, self.probe, 0)
        held = self.corpus.build_slice("perception", split="dev", system_anchor=None)["rows"][0]
        with self.assertRaisesRegex(ValueError, "TRAIN"):
            runtime.training_item(held, TokenizerFixture(), self.trainer, self.probe, 0)
        original = self.trainer.encode_item_segments
        def bad_mask(*args, **kwargs):
            result = original(*args, **kwargs)
            result[0].labels[0] = result[0].ids[0]
            return result
        with patch.object(self.trainer, "encode_item_segments", bad_mask), self.assertRaisesRegex(ValueError, "mask differs"):
            runtime.training_item(row, TokenizerFixture(), self.trainer, self.probe, 0)

    def test_prepare_failure_preserved_and_no_reuse(self):
        self.kwargs["corpus_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "corpus hash"):
            runtime.prepare(**self.kwargs)
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())
        with self.assertRaisesRegex(ValueError, "new disjoint"):
            runtime.prepare(**self.kwargs)

    def test_final_boyle_hash_and_anchor_pins_not_silently_changed(self):
        self.kwargs["probe_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Boyle final"):
            runtime.prepare(**self.kwargs)
        self.kwargs["probe_sha256"] = self.probe_hash
        self.prepare()
        with patch.object(self.probe, "ANCHOR", "different anchor"), self.assertRaisesRegex(ValueError, "anchor differs"):
            runtime.verify(self.root, self.pin)

    def test_worker_interpreter_preserves_venv_symlink_spelling(self):
        venv = self.home / "venv" / "bin"
        venv.mkdir(parents=True)
        interpreter = venv / "python"
        interpreter.symlink_to(sys.executable)
        with patch.object(runtime.sys, "executable", str(interpreter)):
            self.prepare()
        self.assertEqual(self.plan["python"], str(interpreter))
        self.assertNotEqual(self.plan["python"], str(interpreter.resolve()))

    def test_adapter_mutation_after_fit_is_not_accepted_for_readout(self):
        self.prepare()
        directory = self.root / "run" / "fit_absent"
        directory.mkdir(parents=True)
        self.fit_fixture("fit_absent")
        (directory / "adapter" / "adapter_model.safetensors").write_text("changed CPU fixture")
        with self.assertRaisesRegex(ValueError, "custody differs"):
            runtime.adapter_for(self.plan, "fitAbsent__absent")

    def test_input_scope_recipe_model_and_environment_drift(self):
        self.prepare()
        with patch.object(self.probe, "model_hashes", return_value={"wrong": "hash"}), self.assertRaisesRegex(ValueError, "base differs"):
            runtime.verify(self.root, self.pin, native=True)
        with patch.object(runtime, "environment", return_value={"wrong": "version"}), self.assertRaisesRegex(ValueError, "environment"):
            runtime.verify(self.root, self.pin, native=True)
        (self.root / "calls.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "prepared input differs"):
            runtime.verify(self.root, self.pin)

    def test_two_cold_fit_calls_actual_trainer_api_and_no_dev_items(self):
        self.prepare()
        (self.root / "run").mkdir()
        loaded = []
        def loader(model):
            base = SimpleNamespace(named_parameters=lambda: [("layer.lora_A.default.weight", SimpleNamespace(requires_grad=True)),
                                                              ("base.weight", SimpleNamespace(requires_grad=False))])
            loaded.append(base)
            return TokenizerFixture(), base
        seen = []
        def train(items, tokenizer, base, config, out_dir, **kwargs):
            self.assertNotIn("init_adapter", kwargs)
            self.assertEqual(len(items), 12)
            arm = "absent" if kwargs["corpus_name"] == "train_absent.json" else "present"
            prepared = runtime.read(self.root / f"train_{arm}.json")
            self.assertEqual(items, prepared["items"])
            self.assertEqual(kwargs["corpus_sha"], self.plan["input_hashes"][f"train_{arm}.json"])
            seen.append((base, asdict(config)))
            adapter = Path(out_dir)
            adapter.mkdir()
            runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
            runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none", target_modules=config.target_modules))
            (adapter / "adapter_model.safetensors").write_text("CPU fixture; not model weights")
            (adapter / "DONE").write_text("ok")
        with patch.object(runtime, "load_native_model", loader), patch.object(self.trainer, "run_training", train):
            for stage in ("fit_absent", "fit_present"):
                (self.root / "run" / stage).mkdir()
                runtime.fit_one(self.plan, stage, self.probe)
                self.assertTrue((self.root / "run" / stage / "fit.json").exists())
        self.assertEqual(len(loaded), 2)
        self.assertIsNot(loaded[0], loaded[1])
        self.assertEqual(seen[0][1], seen[1][1])

    def test_fit_manifest_rejects_skips_nonfinite_drops_exposure(self):
        self.prepare()
        prepared = runtime.read(self.root / "train_absent.json")
        valid = self.manifest(prepared)
        runtime.check_fit_manifest(valid, prepared, self.plan["config"])
        changes = [("steps", 11), ("nonfinite_batches", 1), ("epochs_run", 3), ("final_loss", float("nan")),
                   ("train_tokens_seen", 1), ("mean_loss_per_epoch", [1.0])]
        for key, value in changes:
            wrong = copy.deepcopy(valid)
            wrong[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runtime.check_fit_manifest(wrong, prepared, self.plan["config"])
        for section, key in (("corpus", "n_skipped_no_target"), ("truncation", "items_truncated")):
            wrong = copy.deepcopy(valid)
            wrong[section][key] = 1
            with self.assertRaises(ValueError):
                runtime.check_fit_manifest(wrong, prepared, self.plan["config"])

    def test_six_fresh_matched_readouts_all_captures_before_scoring(self):
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("premature scoring")):
            result = self.complete()
        self.assertEqual(result["status"], "ALL_CAPTURES_CLOSED_UNSCORED")
        self.assertEqual(len(CaptureFixture.instances), 6)
        self.assertTrue(all(backend.closed and len(backend.seen) == 12 for backend in CaptureFixture.instances))
        self.assertEqual([backend.route is None for backend in CaptureFixture.instances], [True, True, False, False, False, False])
        self.assertEqual(len(runtime.validate_completed(self.plan, self.pin, self.probe)), 8)
        out = self.home / "collected"
        runtime.collect(self.root, self.pin, self.completion, out)
        report = runtime.read(out / "scores.json")
        self.assertEqual(report["calls"], 72)
        self.assertEqual(set(report["cells"]), set(runtime.CELLS))
        self.assertTrue(all(cell["correct"] == cell["total"] == 12 for cell in report["cells"].values()))
        self.assertFalse(report["automatic_pass"])

    def test_malformed_record_is_raw_evidence_not_a_retry(self):
        CaptureFixture.raw_text = "not JSON"
        self.complete()
        out = self.home / "scores"
        runtime.collect(self.root, self.pin, self.completion, out)
        report = runtime.read(out / "scores.json")
        self.assertTrue(all(cell["correct"] == 0 for cell in report["cells"].values()))
        self.assertEqual(sum(len(backend.seen) for backend in CaptureFixture.instances), 72)

    def test_capture_error_preserves_raw_and_never_closes_or_scores(self):
        self.prepare()
        directory = self.root / "run" / "OFF__absent"
        directory.mkdir(parents=True)
        CaptureFixture.corrupt_input = True
        with patch.object(runtime, "Native", CaptureFixture), self.assertRaisesRegex(ValueError, "prompt tokens drift"):
            runtime.capture_cell(self.plan, "OFF__absent", self.probe)
        self.assertTrue((directory / "00.response.json").exists())
        self.assertFalse((directory / "closed.json").exists())
        self.assertTrue(CaptureFixture.instances[0].closed)

    def test_off_never_routes_adapter_and_adapters_are_hash_bound(self):
        self.prepare()
        directory = self.root / "run" / "OFF__absent"
        directory.mkdir(parents=True)
        CaptureFixture.corrupt_route = True
        with patch.object(runtime, "Native", CaptureFixture), self.assertRaisesRegex(ValueError, "LoRA route"):
            runtime.capture_cell(self.plan, "OFF__absent", self.probe)
        self.assertFalse((directory / "closed.json").exists())

    def test_missing_capture_never_scores_even_after_completion(self):
        self.complete()
        (self.root / "run" / runtime.CELLS[-1] / "11.response.json").unlink()
        out = self.home / "scores"
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("must not score")) as score:
            with self.assertRaises((ValueError, FileNotFoundError)):
                runtime.collect(self.root, self.pin, self.completion, out)
            score.assert_not_called()
        self.assertFalse((out / "scores.json").exists())
        self.assertTrue((out / "collection_failure.json").exists())

    def test_capture_tamper_duplicate_process_and_recollection_rejected(self):
        self.complete()
        last = self.root / "run" / runtime.CELLS[-1]
        original = (last / "started.json").read_bytes()
        changed = runtime.read(last / "started.json")
        changed["pid"] = 80000
        (last / "started.json").write_bytes(runtime.encoded(changed))
        with self.assertRaisesRegex(ValueError, "process receipt"):
            runtime.validate_completed(self.plan, self.pin, self.probe)
        (last / "started.json").write_bytes(original)
        out = self.home / "scores"
        runtime.collect(self.root, self.pin, self.completion, out)
        with self.assertRaisesRegex(ValueError, "fresh external"):
            runtime.collect(self.root, self.pin, self.completion, out)

    def test_controller_stops_on_failure_preserves_evidence_and_no_retry(self):
        self.prepare()
        seen = []
        def fail_second(plan, pin, stage, deadline, probe):
            seen.append(stage)
            if stage == "fit_present":
                raise TimeoutError("fixture worker timeout")
            self.fake_stage(plan, pin, stage, deadline, probe)
        with patch.object(runtime, "run_stage", fail_second), self.assertRaises(TimeoutError):
            runtime.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual(seen, ["fit_absent", "fit_present"])
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertTrue((self.root / "run" / "fit_absent" / "fit.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())
        with self.assertRaises(FileExistsError):
            runtime.controller(self.root, self.pin, allow_gpu=True)

    def test_explicit_gpu_flags_required_and_collection_is_separate(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            runtime.controller(self.root, self.pin)
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            runtime.worker(self.root, self.pin, "fit_absent")
        self.assertEqual(runtime.OUTER_SECONDS, 2700)
        self.assertEqual(runtime.COLLECTION_SECONDS, 180)
        self.assertEqual(runtime.GPU_QUERY_SECONDS, 30)
        self.assertEqual(runtime.FIT_SECONDS, 600)
        self.assertEqual(runtime.READOUT_SECONDS, 240)
        self.assertEqual(2 * runtime.FIT_SECONDS + 6 * runtime.READOUT_SECONDS +
                         8 * (runtime.GPU_QUERY_SECONDS + runtime.CLEANUP_SECONDS), 3200)
        self.assertGreater(3200, runtime.OUTER_SECONDS)

    def test_readout_240s_ceiling_still_clamps_to_global_release_reserve(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.return_value = 0
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=False), \
                patch.object(self.probe, "cleanup"), patch.object(runtime.subprocess, "Popen", return_value=process), \
                patch.object(runtime.time, "monotonic", return_value=100):
            runtime.run_stage(self.plan, self.pin, "OFF__absent", 1000, self.probe)
            process.wait.assert_called_with(timeout=240)
            runtime.run_stage(self.plan, self.pin, "OFF__present", 300, self.probe)
            process.wait.assert_called_with(timeout=160)

    def test_stage_owns_only_spawned_group_and_cleanup_runs_on_timeout(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        cleanup = Mock()
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=False), \
                patch.object(self.probe, "cleanup", cleanup), patch.object(runtime.subprocess, "Popen", return_value=process) as popen:
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_stage(self.plan, self.pin, "fit_absent", time.monotonic() + 100, self.probe)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(popen.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        cleanup.assert_called_once_with(process)
        self.assertTrue((self.root / "run" / "fit_absent" / "released.json").exists())

    def test_busy_gpu_is_never_killed_or_started(self):
        self.prepare()
        with patch.object(self.probe, "gpu_state", return_value=False), patch.object(self.probe, "cleanup") as cleanup, \
                patch.object(runtime.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "not vacant"):
                runtime.run_stage(self.plan, self.pin, "fit_absent", time.monotonic() + 100, self.probe)
        popen.assert_not_called()
        cleanup.assert_not_called()

    def test_nvml_30s_budget_preserves_exact_uuid_and_release_checks(self):
        self.prepare()
        xml = f"<nvidia_smi_log><gpu><uuid>{self.plan['gpu_uuid']}</uuid><processes/></gpu></nvidia_smi_log>"
        response = SimpleNamespace(returncode=0, stdout=xml)
        with patch.object(self.probe.subprocess, "run", return_value=response) as query:
            self.assertTrue(self.probe.gpu_state(self.plan))
            self.assertEqual(query.call_args.kwargs["timeout"], 30)
            self.assertEqual(query.call_args.args[0], ["nvidia-smi", "-i", "0", "-q", "-x"])
        response.stdout = xml.replace("<processes/>", "<processes><process_info><pid>123</pid></process_info></processes>")
        with patch.object(self.probe.subprocess, "run", return_value=response):
            self.assertFalse(self.probe.gpu_state(self.plan))
        response.stdout = xml.replace(self.plan["gpu_uuid"], "GPU-wrong-device")
        with patch.object(self.probe.subprocess, "run", return_value=response), self.assertRaises(ValueError):
            self.probe.gpu_state(self.plan)
        with patch.object(self.probe.subprocess, "run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 30)), self.assertRaises(subprocess.TimeoutExpired):
            self.probe.gpu_state(self.plan)

    def test_insufficient_query_release_budget_starts_nothing(self):
        self.prepare()
        with patch.object(self.probe, "gpu_state") as query, patch.object(runtime.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "vacancy and release"):
                runtime.run_stage(self.plan, self.pin, "fit_absent", time.monotonic() + 60, self.probe)
        query.assert_not_called()
        popen.assert_not_called()

    def test_native_backend_calls_matched_engine_and_actual_lora_argument(self):
        self.prepare()
        engines, requests = [], []
        class FakeLLM:
            def __init__(self, **kwargs):
                engines.append(kwargs)
                self.tokenizer = TokenizerFixture()
                self.tokenizer.decode = lambda ids, skip_special_tokens: "{}"

            def get_tokenizer(self):
                return self.tokenizer

            def generate(self, prompts, params, lora_request, use_tqdm):
                requests.append(lora_request)
                output = SimpleNamespace(text="{}", token_ids=self.tokenizer.encode("{}"), finish_reason="stop", stop_reason=1)
                return [SimpleNamespace(outputs=[output], prompt_token_ids=self.tokenizer.encode(prompts[0]))]

            def shutdown(self):
                pass
        modules = {"vllm": SimpleNamespace(LLM=FakeLLM, SamplingParams=lambda **kwargs: kwargs),
                   "vllm.lora": SimpleNamespace(),
                   "vllm.lora.request": SimpleNamespace(LoRARequest=lambda name, number, path: (name, number, path)),
                   "torch": SimpleNamespace(inference_mode=contextlib.nullcontext)}
        calls = runtime.read(self.root / "calls.json")["absent"]
        with patch.dict(sys.modules, modules):
            for adapter in (None, "/cpu-fixture-absent", "/cpu-fixture-present"):
                backend = runtime.Native(self.plan, self.probe, adapter)
                response = backend.generate(calls[0]["messages"])
                self.probe.validate_response(calls[0], response)
                backend.close()
        self.assertEqual(requests, [None, ("perception", 1, "/cpu-fixture-absent"), ("perception", 1, "/cpu-fixture-present")])
        self.assertTrue(all(engine["enable_lora"] and engine["max_lora_rank"] == 32 for engine in engines))
        self.assertEqual(engines[0], engines[1])
        self.assertEqual(engines[1], engines[2])

    def test_cleanup_failure_cannot_claim_release(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.return_value = 0
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=True), \
                patch.object(self.probe, "cleanup"), patch.object(runtime.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(ValueError, "survived cleanup"):
                runtime.run_stage(self.plan, self.pin, "fit_absent", time.monotonic() + 100, self.probe)
        directory = self.root / "run" / "fit_absent"
        self.assertTrue((directory / "cleanup_failure.json").exists())
        self.assertFalse((directory / "released.json").exists())

    def test_budget_expires_and_restores_alarm(self):
        previous = signal.getsignal(signal.SIGALRM)
        with self.assertRaises(TimeoutError):
            with runtime.budget(.01):
                time.sleep(.05)
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)

    def test_import_does_not_load_native_libraries(self):
        script = ("import importlib.util,sys; "
                  f"spec=importlib.util.spec_from_file_location('p', {str(PATH)!r}); "
                  "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                  "assert not any(name in sys.modules for name in ('torch','vllm','transformers','peft'))")
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_env_overrides_import_unique_frozen_scripts_without_replacing_drivers(self):
        frozen = self.home / "frozen"
        frozen.mkdir()
        driver_path = frozen / "perception_frozen.py"
        probe_path = frozen / "probe_frozen.py"
        driver_path.write_bytes(PATH.read_bytes())
        probe_path.write_bytes(PROBE_PATH.read_bytes())
        script = (
            "import os,runpy; "
            f"namespace=runpy.run_path({str(Path(__file__).resolve())!r}, run_name='override_fixture'); "
            "assert str(namespace['runtime'].SELF)==os.environ['PERCEPTION_DRIVER']; "
            "assert str(namespace['PROBE_PATH'])==os.environ['PERCEPTION_PROBE_DRIVER']; "
            "runtime=namespace['runtime']; path=namespace['PROBE_PATH']; "
            "probe=runtime.load_probe(path, runtime.digest(path)); "
            "assert probe.GPU_QUERY_SECONDS==30"
        )
        env = dict(os.environ, PERCEPTION_DRIVER=str(driver_path), PERCEPTION_PROBE_DRIVER=str(probe_path))
        result = subprocess.run([sys.executable, "-B", "-c", script], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
