"""Bounded CPU-only tests: frozen pure helpers, toy tokenizer and mocked natives."""
import ast
import copy
from dataclasses import asdict
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib

sys.dont_write_bytecode = True
PATH = Path("/tmp/astra_contrastive_full_dose_run_20260913_v2.py")
specification = importlib.util.spec_from_file_location("full_dose_v2_test_runtime", PATH)
runtime = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runtime)
ENCODE_TRAINING = runtime.encode_training
SOURCE = Path("/tmp/astra_contrastive_source_20260913_attempt1")
REPO = Path("/data/home/rohing/dream-state")
ARCHIVE = REPO / "gpu_artifacts_local/contrastive_perception_20260913/contrastive_perception_20260913_attempt1_archive.tar"


class ToyTokenizer:
    chat_template = "CPU_ONLY_QWEN_SHAPED_TOY_TEMPLATE"
    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token_id = 0

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        pieces = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s+", text)
        assert "".join(pieces) == text
        return [1 if piece == self.eos_token else 2 if piece == "<|im_start|>" else zlib.crc32(piece.encode())+3 for piece in pieces]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, dict(role="system", content="CPU fixture system."))
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


def record(path):
    return dict(path=str(path), sha256=runtime.digest(path))


class FullDoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.trainer = runtime.old.source_api(SOURCE)
        cls.material = runtime.old.load_module(record("/tmp/astra_contrastive_perception_material_20260913.py"), "test_material")
        cls.encoder = runtime.old.load_module(record("/tmp/astra_perception_fit_run_20260913.py"), "test_encoder")
        cls.dataset = cls.material.build_dataset(cls.corpus)
        cls.probe = runtime.old.load_probe("/tmp/astra_birth_skill_probe_run_20260913.py", runtime.old.PUBLIC_SHA256)
        cls.trains = {seed: {arm: runtime.encode_training(cls.dataset["training"][arm], ToyTokenizer(), cls.trainer,
                              cls.probe, cls.encoder, seed) for arm in runtime.ARMS} for seed in (0, 1, 2)}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="full_dose_cpu_", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "root"
        self.model = self.home / "model"
        self.model.mkdir()
        self.binding = runtime.read("/tmp/astra_contrastive_plan_20260913_attempt1.json")["binding"]
        self.reflection = SimpleNamespace(load_native_model=Mock(return_value=(ToyTokenizer(), SimpleNamespace(
            named_parameters=lambda: [("layer.lora_A.weight", SimpleNamespace(requires_grad=True))]))))
        self.spec = dict(runner_sha256=runtime.digest(PATH), original=record(runtime.ORIGINAL),
                         material=record("/tmp/astra_contrastive_perception_material_20260913.py"),
                         encoder=record("/tmp/astra_perception_fit_run_20260913.py"),
                         reflection=record("/tmp/astra_reflection_fit_run_20260913.py"),
                         public=record("/tmp/astra_birth_skill_probe_run_20260913.py"),
                         protocol=record(REPO / "research_notes/astra_memos/ASTRA_CONTRASTIVE_FULL_DOSE_2026-09-13.md"),
                         original_protocol=record(REPO / "research_notes/astra_memos/ASTRA_CONTRASTIVE_PERCEPTION_PROTOCOL_2026-09-13.md"),
                         binding=record("/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json"),
                         historical_archive=record(ARCHIVE), source=str(SOURCE), source_files=runtime.tree(SOURCE),
                         model=runtime.read("/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json")["model"],
                         learner_seed=0, node="node2", expected_hostname=socket.gethostname(),
                         expected_boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                         gpu_index=0, gpu_uuid="GPU-00000000-0000-0000-0000-000000000001", lease_end=time.time()+50000)
        fields = ("node", "expected_hostname", "expected_boot_id", "gpu_index", "gpu_uuid", "lease_end", "learner_seed")
        reservation = self.home / "reservation.json"
        runtime.write(reservation, dict(scope=runtime.SCOPE, root=str(self.root), **{field: self.spec[field] for field in fields}))
        self.spec["reservation"] = record(reservation)
        self.patch(runtime, "apis", return_value=(self.material, self.encoder, self.reflection, self.probe))
        self.patch(self.probe, "model_hashes", return_value=self.binding["model_files"])
        self.patch(self.probe, "native_environment", return_value=self.binding["native_environment"])
        self.patch(runtime.old, "environment", return_value={"CPU_ONLY": True})
        self.patch(self.probe, "native_tokenizer", return_value=ToyTokenizer())
        self.patch(self.probe, "gpu_state", return_value=True)
        self.patch(self.probe, "group_alive", return_value=False)
        self.history = dict(responses={panel+"/"+row["row_id"]: dict(raw=row["raw_target"], finish_reason="stop")
                                      for panel in runtime.PANELS for row in self.dataset["evaluation"][panel]}, archive=self.spec["historical_archive"])
        self.history_import = self.patch(runtime, "import_off", return_value=self.history)
        self.patch(runtime, "encode_training", side_effect=lambda rows, tokenizer, trainer, probe, encoder, seed:
                   copy.deepcopy(self.trains[seed]["plain" if rows == self.dataset["training"]["plain"] else "contrastive"]))

    def patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def prepare(self, seed=0):
        self.spec["learner_seed"] = seed
        with patch.object(runtime, "allocation"):
            spec_path = self.home / "spec.json"
            runtime.write(spec_path, self.spec)
            result = runtime.prepare(str(self.root), str(spec_path), runtime.digest(spec_path), True)
        self.pin = result["plan_sha256"]
        self.plan, _ = runtime.verify(self.root, self.pin)
        return result

    def manifest(self, arm):
        prepared = runtime.read(self.root / f"train_{arm}.json")
        return dict(config=self.plan["config"], base_model=self.plan["model"], empty=False,
                    steps=336, micro_batches=336, epochs_run=112, nonfinite_batches=0,
                    corpus=dict(file=f"train_{arm}.json", sha256=self.plan["input_hashes"][f"train_{arm}.json"],
                                n_items=12, n_encoded=12, n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=12),
                    tokens=dict(target=prepared["target_tokens"]), train_tokens_seen=112*prepared["total_tokens"],
                    mean_loss_per_epoch=[.1]*112, final_loss=.1)

    def fake_train(self, items, tokenizer, base, config, out, **kwargs):
        arm = kwargs["corpus_name"].removeprefix("train_").removesuffix(".json")
        self.assertEqual(set(kwargs), {"corpus_name", "corpus_sha"})
        self.assertEqual(asdict(config), self.plan["config"])
        adapter = Path(out)
        adapter.mkdir()
        runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                                                            target_modules=self.plan["config"]["target_modules"]))
        (adapter / "adapter_model.safetensors").write_text("CPU_FAKE_WEIGHTS_"+arm)
        (adapter / "DONE").write_text("CPU_ONLY")
        runtime.write(adapter / "train_manifest.json", self.manifest(arm))

    def fake_backend(self, plan, probe, adapter):
        route = dict(name="perception", id=1, path=adapter)
        answers = {row["input_messages"][-1]["content"]: row["raw_target"] for rows in self.dataset["evaluation"].values() for row in rows}
        def generate(messages):
            native = probe.render(ToyTokenizer(), messages)
            raw = answers[messages[-1]["content"]]
            return dict(**native, text=raw, output_token_ids=ToyTokenizer().encode(raw), decoded_output=raw,
                        actual_prompt_token_ids=native["prompt_token_ids"], finish_reason="stop", stop_reason=1,
                        started=1.0, ended=2.0, lora_request=route)
        return SimpleNamespace(generate=Mock(side_effect=generate), close=Mock())

    def completed(self):
        self.prepare()
        (self.root / "run").mkdir()
        runtime.write(self.root / "controller_started.json", dict(pid=90000000, pgid=90000000, plan_sha256=self.pin))
        for index, stage in enumerate(runtime.STAGES):
            directory = self.root / "run" / stage
            directory.mkdir()
            pid = 90000100+index
            receipt = dict(pid=pid, pgid=pid, parent_pid=90000000, stage=stage, plan_sha256=self.pin)
            for name in ("started.json", "launch.json", "released.json"):
                runtime.write(directory / name, receipt)
            kind, arm = stage.split("_", 1)
            if kind == "fit":
                with patch.object(self.trainer, "run_training", side_effect=self.fake_train):
                    runtime.fit_one(self.plan, arm, self.probe)
            else:
                with patch.object(runtime.old, "Native", side_effect=self.fake_backend):
                    runtime.capture(self.plan, arm, self.probe)
        inventory = runtime.validate_completed(self.plan, self.pin, self.probe)
        runtime.write(self.root / "capture_complete.json", dict(plan_sha256=self.pin, stages=inventory,
                      calls=96, fits=2, updates=672, scored=False, elapsed_seconds=10.0))
        return runtime.digest(self.root / "capture_complete.json")

    def test_dose_only_and_seed_strict(self):
        for seed in (0, 1, 2):
            self.assertEqual(runtime.recipe(seed), dict(runtime.old.RECIPE, epochs=112, seed=seed))
        for invalid in (True, False, "0", 0.0, -1, 3, None, math.nan):
            with self.assertRaises(ValueError):
                runtime.recipe(invalid)
        self.assertEqual(runtime.old.RECIPE["epochs"], 4)
        self.assertEqual(runtime.old.ENGINE["seed"], runtime.old.PARAMS["seed"])
        self.assertEqual(runtime.old.PARAMS["seed"], 0)

    def test_full_epochs_supervision_and_paired_order(self):
        for seed, arms in self.trains.items():
            self.assertEqual(arms["plain"]["epoch_order"], arms["contrastive"]["epoch_order"])
            for arm, prepared in arms.items():
                runtime.validate_prepared(prepared, self.dataset["training"][arm], seed, self.trainer)
                self.assertEqual(len(prepared["epoch_order"]), 112)
                self.assertEqual(sum(map(len, prepared["epoch_order"])), 1344)
                self.assertEqual(prepared["costs"]["updates"], 336)
                for row in prepared["encoding"]:
                    self.assertEqual(row["supervised_ids"].count(1), 1)
                    self.assertEqual(row["supervised_ids"][-1], 1)
                    self.assertEqual([value for value in row["labels"] if value != -100], row["supervised_ids"])
            self.assertEqual([row["supervised_ids"] for row in arms["plain"]["encoding"]],
                             [row["supervised_ids"] for row in arms["contrastive"]["encoding"]])
        self.assertEqual(len({runtime.old.value_hash(arms["plain"]["epoch_order"]) for arms in self.trains.values()}), 3)

    def test_cross_seed_epoch_and_mask_reject(self):
        for change in ("seed", "epoch", "mask", "target", "dose"):
            prepared = copy.deepcopy(self.trains[0]["plain"])
            if change == "seed":
                prepared["learner_seed"] = True
            elif change == "epoch":
                prepared["epoch_order"] = self.trains[1]["plain"]["epoch_order"]
            elif change == "mask":
                prepared["encoding"][0]["labels"][0] = 1
            elif change == "target":
                prepared["items"][0]["meta"]["target_sha256"] = "wrong"
            else:
                prepared["costs"]["updates"] = 12
            with self.assertRaises(ValueError):
                runtime.validate_prepared(prepared, self.dataset["training"]["plain"], 0, self.trainer)

    def test_actual_encoder_rejects_truncation_and_padding_loss(self):
        rows = copy.deepcopy(self.dataset["training"]["plain"])
        rows[0]["input_messages"][-1]["content"] += " too long"*2000
        with self.assertRaises(ValueError):
            ENCODE_TRAINING(rows, ToyTokenizer(), self.trainer, self.probe, self.encoder, 0)
        original = self.trainer.collate
        def corrupt(packs, pad):
            result = original(packs, pad)
            result["labels"][0][0] = 4
            return result
        with patch.object(self.trainer, "collate", side_effect=corrupt):
            with self.assertRaises(ValueError):
                ENCODE_TRAINING(self.dataset["training"]["plain"], ToyTokenizer(), self.trainer, self.probe, self.encoder, 0)

    def test_closed_spec_source_protocol_binding(self):
        runtime.validate_spec(self.spec)
        for field, value in (("learner_seed", True), ("node", "node1"), ("gpu_index", False),
                             ("gpu_index", 3), ("lease_end", math.nan), ("runner_sha256", "0"*64)):
            broken = dict(self.spec, **{field: value})
            with self.assertRaises(ValueError):
                runtime.validate_spec(broken)
        with self.assertRaises(ValueError):
            runtime.validate_spec(dict(self.spec, init_adapter="old_fit"))
        for field in ("protocol", "original_protocol", "historical_archive", "encoder", "binding", "original"):
            broken = copy.deepcopy(self.spec)
            broken[field]["sha256"] = "0"*64
            with self.assertRaises(ValueError):
                runtime.validate_spec(broken)

    def test_allocation_root_boot_lease(self):
        runtime.allocation(self.spec, self.root, launch=True)
        with self.assertRaises(ValueError):
            runtime.allocation(self.spec, self.home / "different", launch=True)
        with patch.object(runtime.socket, "gethostname", return_value="wrong"):
            with self.assertRaises(ValueError):
                runtime.allocation(self.spec, self.root)
        with patch.object(runtime.time, "time", return_value=self.spec["lease_end"]-runtime.LEASE_MARGIN):
            with self.assertRaises(ValueError):
                runtime.allocation(self.spec, self.root)

    def test_prepare_seed2_no_models_and_frozen_material_bytes(self):
        result = self.prepare(2)
        self.assertEqual(result["budget"]["calls"], 96)
        self.assertEqual(self.plan["config"]["epochs"], 112)
        self.assertEqual(self.plan["config"]["seed"], 2)
        self.assertEqual(runtime.digest(self.root / "material.json"), runtime.old.MATERIAL_DATA_SHA256)
        self.reflection.load_native_model.assert_not_called()
        self.probe.gpu_state.assert_not_called()
        with self.assertRaises(ValueError):
            runtime.prepare(str(self.root), str(self.home / "spec.json"), self.plan["spec_sha256"], True)

    def test_prepare_explicit_permission_and_bad_spec_pin(self):
        with self.assertRaises(ValueError):
            runtime.prepare(str(self.root), "missing", "bad")
        path = self.home / "spec.json"
        runtime.write(path, self.spec)
        with self.assertRaises(ValueError):
            runtime.prepare(str(self.root), str(path), "0"*64, True)
        self.assertFalse(self.root.exists())

    def test_failed_preparation_is_preserved_not_retried(self):
        self.history_import.side_effect = ValueError("fixture history mismatch")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())
        self.assertTrue((self.root / "material.json").exists() is False)

    def test_output_overlap_and_exclusive_write(self):
        for path in (self.model, self.model / "child", self.home):
            with self.assertRaises(ValueError):
                runtime.fresh(path, [self.model])
        path = self.home / "receipt.json"
        runtime.write(path, {"first": True})
        with self.assertRaises(FileExistsError):
            runtime.write(path, {"replaced": True})
        self.assertEqual(runtime.read(path), {"first": True})

    def test_verify_config_and_seed_mismatch(self):
        self.prepare()
        for edit in ({"learner_seed": 1}, {"config": dict(self.plan["config"], seed=False)},
                     {"config": dict(self.plan["config"], epochs=4)}, {"stages": ["fake"]}):
            changed = dict(self.plan, **edit)
            (self.root / "plan.json").write_bytes(runtime.encoded(changed))
            with self.assertRaises(ValueError):
                runtime.verify(self.root, runtime.digest(self.root / "plan.json"))

    def test_fit_fresh_and_manifest_errors(self):
        self.prepare(1)
        (self.root / "run/fit_plain").mkdir(parents=True)
        with patch.object(self.trainer, "run_training", side_effect=self.fake_train) as train:
            runtime.fit_one(self.plan, "plain", self.probe)
        self.assertEqual(train.call_count, 1)
        self.assertNotIn("init_adapter", train.call_args.kwargs)
        self.assertEqual(runtime.read(self.root / "run/fit_plain/fit.json")["learner_seed"], 1)
        prepared = runtime.read(self.root / "train_plain.json")
        original = self.manifest("plain")
        for changes in ({"steps": 12}, {"epochs_run": 4}, {"warm_start": {}}, {"final_loss": math.nan},
                        {"train_tokens_seen": prepared["total_tokens"]*4}, {"nonfinite_batches": 1}):
            with self.assertRaises(ValueError):
                runtime.check_fit_manifest(dict(original, **changes), prepared, self.plan, "plain")
        with self.assertRaises(ValueError):
            runtime.adapter_for(self.plan, "OFF")

    def test_fit_rejects_descendant_before_training(self):
        self.prepare()
        self.reflection.load_native_model.return_value = (ToyTokenizer(), SimpleNamespace(peft_config={}))
        with patch.object(self.trainer, "run_training") as train:
            with self.assertRaises(ValueError):
                runtime.fit_one(self.plan, "plain", self.probe)
        train.assert_not_called()

    def test_all_four_stages_collect_once_original_scorer(self):
        completion = self.completed()
        out = self.home / "collected"
        result = runtime.collect(str(self.root), self.pin, completion, str(out))
        report = runtime.read(out / "scores.json")
        self.assertEqual(result["status"], "COLLECTED_EXPLORATORY_DEV_ONLY")
        self.assertEqual(report["calls"], 96)
        self.assertEqual(report["historical_OFF"]["new_calls"], 0)
        self.assertEqual(len(report["per_item_canaries"]["plain"]), 24)
        self.assertFalse(report["automatic_pass"])
        expected = self.material.score_dataset(self.corpus, self.dataset, {state: self.history["responses"] for state in ("OFF", *runtime.ARMS)})
        self.assertEqual(report["material_scores"], expected)
        with self.assertRaises(FileExistsError):
            runtime.collect(str(self.root), self.pin, completion, str(self.home / "again"))

    def test_failure_never_scored_and_claim_persists(self):
        completion = self.completed()
        runtime.write(self.root / "controller_failure.json", {"fixture": True})
        with self.assertRaises(ValueError):
            runtime.collect(str(self.root), self.pin, completion, str(self.home / "failed"))
        self.assertFalse((self.home / "failed/scores.json").exists())
        self.assertTrue(self.root.with_name(self.root.name+".collection_claim.json").exists())

    def test_changed_capture_rejected(self):
        self.completed()
        response = self.root / "run/readout_plain/D1__00.response.json"
        response.write_text("{}")
        with self.assertRaises(ValueError):
            runtime.validate_completed(self.plan, self.pin, self.probe)

    def test_duplicate_process_or_extra_stage_rejected(self):
        self.completed()
        (self.root / "run/fake").mkdir()
        with self.assertRaises(ValueError):
            runtime.validate_completed(self.plan, self.pin, self.probe)

    def test_duplicate_fresh_process_rejected(self):
        self.completed()
        directory = self.root / "run/readout_plain"
        for name in ("started.json", "launch.json", "released.json"):
            receipt = runtime.read(directory / name)
            receipt.update(pid=90000100, pgid=90000100)
            (directory / name).write_bytes(runtime.encoded(receipt))
        with self.assertRaisesRegex(ValueError, "four distinct"):
            runtime.validate_completed(self.plan, self.pin, self.probe)

    def test_individual_plain_canary_loss_retained(self):
        self.completed()
        directory = self.root / "run/readout_plain"
        filename = "C-record__00.response.json"
        response = runtime.read(directory / filename)
        response.update(text="{}", decoded_output="{}", output_token_ids=ToyTokenizer().encode("{}"))
        (directory / filename).write_bytes(runtime.encoded(response))
        closed = runtime.read(directory / "closed.json")
        closed["files"][filename] = runtime.digest(directory / filename)
        (directory / "closed.json").write_bytes(runtime.encoded(closed))
        completion = runtime.read(self.root / "capture_complete.json")
        completion["stages"] = runtime.validate_completed(self.plan, self.pin, self.probe)
        (self.root / "capture_complete.json").write_bytes(runtime.encoded(completion))
        out = self.home / "collected"
        runtime.collect(str(self.root), self.pin, runtime.digest(self.root / "capture_complete.json"), str(out))
        scores = runtime.read(out / "scores.json")
        self.assertEqual(sum(row["lost"] for row in scores["per_item_canaries"]["plain"].values()), 1)
        self.assertEqual(sum(row["lost"] for row in scores["per_item_canaries"]["contrastive"].values()), 0)

    def test_live_controller_rejects_collection_before_claim(self):
        completion = self.completed()
        (self.root / "controller_started.json").write_bytes(runtime.encoded(dict(pid=os.getpid(), pgid=os.getpgrp())))
        with self.assertRaises(ValueError):
            runtime.collect(str(self.root), self.pin, completion, str(self.home / "out"))
        self.assertFalse(self.root.with_name(self.root.name+".collection_claim.json").exists())

    def test_capture_closes_backend_on_failure(self):
        self.prepare()
        directory = self.root / "run/readout_plain"
        directory.mkdir(parents=True)
        adapter = self.home / "mock_adapter"
        adapter.mkdir()
        backend = SimpleNamespace(generate=Mock(side_effect=RuntimeError("CPU fixture")), close=Mock())
        with patch.object(runtime, "adapter_for", return_value=(str(adapter), {})), patch.object(runtime.old, "Native", return_value=backend):
            with self.assertRaises(RuntimeError):
                runtime.capture(self.plan, "plain", self.probe)
        backend.close.assert_called_once()
        self.assertFalse((directory / "closed.json").exists())

    def test_native_response_route_and_finite(self):
        call = dict(native=self.probe.render(ToyTokenizer(), self.dataset["evaluation"]["D1"][0]["input_messages"]))
        response = dict(**call["native"], actual_prompt_token_ids=call["native"]["prompt_token_ids"],
                        text="x", decoded_output="x", output_token_ids=[5], finish_reason="stop", stop_reason=1,
                        started=1.0, ended=2.0, lora_request=None)
        runtime.validate_response(self.probe, call, response, None)
        for change in ({"ended": math.inf}, {"lora_request": {}}, {"actual_prompt_token_ids": [3]}):
            with self.assertRaises(ValueError):
                runtime.validate_response(self.probe, call, dict(response, **change), None)

    def test_stage_timeout_owned_cleanup_uuid(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=90001000)
        process.wait.side_effect = subprocess.TimeoutExpired("CPU fixture", 1)
        with patch.object(runtime, "allocation"), patch.object(runtime.subprocess, "Popen", return_value=process) as launch, \
                patch.object(self.probe, "cleanup", return_value=True) as cleanup:
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_stage(self.plan, self.pin, "fit_plain", time.monotonic()+7200, self.probe)
        cleanup.assert_called_once_with(process)
        self.assertTrue(launch.call_args.kwargs["start_new_session"])
        self.assertEqual(launch.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 2700)

    def test_busy_gpu_never_launches_or_kills(self):
        self.prepare()
        with patch.object(runtime, "allocation"), patch.object(self.probe, "gpu_state", return_value=False), \
                patch.object(runtime.subprocess, "Popen") as launch, patch.object(self.probe, "cleanup") as cleanup:
            with self.assertRaises(ValueError):
                runtime.run_stage(self.plan, self.pin, "fit_plain", time.monotonic()+7200, self.probe)
        launch.assert_not_called()
        cleanup.assert_not_called()

    def test_remaining_budget_no_query_or_launch(self):
        self.prepare()
        with patch.object(runtime.subprocess, "Popen") as launch:
            with self.assertRaises(ValueError):
                runtime.run_stage(self.plan, self.pin, "fit_plain", time.monotonic()+30, self.probe)
        launch.assert_not_called()
        self.probe.gpu_state.assert_not_called()

    def test_controller_four_stages_once_and_uuid_isolation(self):
        self.prepare()
        inventory = {stage: {} for stage in runtime.STAGES}
        with patch.object(runtime.os, "getpgrp", return_value=os.getpid()), patch.object(runtime, "allocation"), \
                patch.object(runtime, "run_stage") as stage, patch.object(runtime, "validate_completed", return_value=inventory):
            result = runtime.controller(str(self.root), self.pin, True)
            self.assertEqual([call.args[2] for call in stage.call_args_list], list(runtime.STAGES))
            self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "")
            with self.assertRaises(FileExistsError):
                runtime.controller(str(self.root), self.pin, True)
        self.assertEqual(result["status"], "ALL_CAPTURES_CLOSED_UNSCORED")
        self.assertEqual(runtime.read(self.root / "capture_complete.json")["updates"], 672)
        self.assertFalse((self.root / "controller_failure.json").exists())

    def test_controller_failure_stops_remaining_stages(self):
        self.prepare()
        with patch.object(runtime.os, "getpgrp", return_value=os.getpid()), patch.object(runtime, "allocation"), \
                patch.object(runtime, "run_stage", side_effect=RuntimeError("CPU fixture")) as stage:
            with self.assertRaises(RuntimeError):
                runtime.controller(str(self.root), self.pin, True)
        self.assertEqual(stage.call_count, 1)
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())

    def test_wrong_scope_controller_does_not_write(self):
        self.root.mkdir()
        before = runtime.tree(self.root)
        with patch.object(runtime.os, "getpgrp", return_value=os.getpid()), patch.object(runtime, "verify", side_effect=ValueError("oldscope")):
            with self.assertRaises(ValueError):
                runtime.controller(str(self.root), "old-pin", True)
        self.assertEqual(runtime.tree(self.root), before)

    def test_worker_permissions_no_native(self):
        with self.assertRaises(ValueError):
            runtime.worker(str(self.root), "pin", "fit_plain")
        with patch.object(runtime.os, "getpgrp", return_value=-1):
            with self.assertRaises(ValueError):
                runtime.worker(str(self.root), "pin", "fit_plain", True)
        self.reflection.load_native_model.assert_not_called()

    def test_collection_envelope_covers_verification(self):
        import signal
        def operation(*args):
            remaining = signal.getitimer(signal.ITIMER_REAL)[0]
            self.assertTrue(0 < remaining <= 180)
            return "CPU fixture"
        with patch.object(runtime, "_collect", side_effect=operation):
            self.assertEqual(runtime.collect("root", "pin", "completion", "out"), "CPU fixture")

    def test_budget_no_off_or_legacy_lifecycle_calls(self):
        self.assertEqual(runtime.STAGES, ("fit_plain", "readout_plain", "fit_contrastive", "readout_contrastive"))
        self.assertEqual(runtime.BUDGET["total_three_seeds"], dict(fits=6, updates=2016, calls=288))
        tree = ast.parse(PATH.read_text())
        forbidden = {"collect", "controller", "prepare", "fit_one", "adapter_for", "run_stage", "verify", "check_fit_manifest", "encode_training"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                self.assertFalse(node.func.value.id == "old" and node.func.attr in forbidden)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                self.assertFalse(any(isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "old" for target in targets))
        self.assertEqual(runtime.digest(runtime.ORIGINAL), runtime.ORIGINAL_SHA)


class HistoricalImportTests(unittest.TestCase):
    def generated_and_archived(self):
        material = runtime.old.load_module(record("/tmp/astra_contrastive_perception_material_20260913.py"), "v2_regression_material")
        corpus = material.load_corpus(SOURCE)
        generated = material.build_dataset(corpus)
        with tarfile.open(ARCHIVE) as archive:
            def value(name):
                return json.load(archive.extractfile(runtime.ARCHIVE_ROOT+"/"+name))
            plan, archived, calls = value("plan.json"), value("material.json"), value("calls.json")
            material_bytes = archive.extractfile(runtime.ARCHIVE_ROOT+"/material.json").read()
        probe = runtime.old.load_probe("/tmp/astra_birth_skill_probe_run_20260913.py", runtime.old.PUBLIC_SHA256)
        return material, generated, archived, material_bytes, plan, calls, probe

    def test_actual_in_memory_build_roundtrip_fails_v1_passes_v2(self):
        material, generated, archived, material_bytes, plan, calls, probe = self.generated_and_archived()
        self.assertNotEqual(generated, archived)
        self.assertEqual(json.loads(material.encoded(generated)), archived)
        self.assertEqual(material.encoded(generated), material_bytes)
        self.assertEqual(material.encoded(archived), material_bytes)
        self.assertEqual(material.digest(material_bytes), runtime.old.MATERIAL_DATA_SHA256)
        v1_path = Path("/tmp/astra_contrastive_full_dose_run_20260913.py")
        self.assertEqual(runtime.digest(v1_path), "663879c3ccec0c0543a6de5eff60e2e92f7482d9f0c1db3879722aa988452bd0")
        v1_spec = importlib.util.spec_from_file_location("full_dose_frozen_v1_regression", v1_path)
        v1 = importlib.util.module_from_spec(v1_spec)
        v1_spec.loader.exec_module(v1)
        with self.assertRaisesRegex(ValueError, "historical dataset differs"):
            v1.import_off(record(ARCHIVE), generated, calls, plan["chat_template"], plan["binding"], probe)
        before = material.encoded(generated)
        result = runtime.import_off(record(ARCHIVE), generated, calls, plan["chat_template"], plan["binding"], probe)
        self.assertEqual(material.encoded(generated), before)
        self.assertEqual(result["selected_members"][runtime.ARCHIVE_ROOT+"/material.json"], archived)
        self.assertEqual(result["selected_member_hashes"][runtime.ARCHIVE_ROOT+"/material.json"], runtime.old.MATERIAL_DATA_SHA256)
        self.assertEqual(len(result["responses"]), 48)
        self.assertEqual(result["new_calls"], 0)

    def test_modified_generated_values_still_rejected(self):
        material, generated, archived, material_bytes, plan, calls, probe = self.generated_and_archived()
        for field in ("target", "source", "prompt", "provenance"):
            changed = copy.deepcopy(generated)
            row = changed["training"]["plain"][0]
            if field == "target":
                row["raw_target"] += " "
            elif field == "source":
                row["source"]["source_id"] += "_changed"
            elif field == "prompt":
                row["input_messages"][-1]["content"] += " changed"
            else:
                changed["provenance"] = {"altered": True}
            with self.subTest(field=field):
                self.assertNotEqual(material.encoded(changed), material_bytes)
                with self.assertRaises(ValueError):
                    runtime.import_off(record(ARCHIVE), changed, calls, plan["chat_template"], plan["binding"], probe)

    def test_actual_archived_OFF_prompt_route_and_hash_joins(self):
        with tarfile.open(ARCHIVE) as archive:
            def value(name):
                return __import__("json").load(archive.extractfile(runtime.ARCHIVE_ROOT+"/"+name))
            plan, dataset, calls = value("plan.json"), value("material.json"), value("calls.json")
        probe = runtime.old.load_probe("/tmp/astra_birth_skill_probe_run_20260913.py", runtime.old.PUBLIC_SHA256)
        result = runtime.import_off(record(ARCHIVE), dataset, calls, plan["chat_template"], plan["binding"], probe)
        self.assertEqual(len(result["responses"]), 48)
        self.assertEqual(result["new_calls"], 0)
        self.assertEqual(result["plan_sha256"], runtime.OLD_PLAN_SHA)
        changed = copy.deepcopy(calls)
        changed["D1"][0]["row_id"] = "different-source"
        with self.assertRaises(ValueError):
            runtime.import_off(record(ARCHIVE), dataset, changed, plan["chat_template"], plan["binding"], probe)
        binding = dict(plan["binding"], revision="wrong-base")
        with self.assertRaises(ValueError):
            runtime.import_off(record(ARCHIVE), dataset, calls, plan["chat_template"], binding, probe)


if __name__ == "__main__":
    unittest.main()
