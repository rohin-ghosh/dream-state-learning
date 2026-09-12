"""Synthetic capture + mocked fresh V3 fit boundaries; no GPU/native/model load."""

from dataclasses import asdict

from datetime import datetime, timezone

import importlib.util

import json
import copy
from contextlib import nullcontext

import math

import os

from pathlib import Path

import struct

import sys

import tempfile

import time

from types import SimpleNamespace

import unittest

from unittest.mock import patch

SOURCE = Path(os.environ.get("ASTRA_SOURCE_ROOT", "/data/home/rohing/dream-state")).resolve()

sys.path.insert(0, str(SOURCE))

sys.path.insert(0, str(SOURCE / "tests"))

from organism_v6 import rulegame_parenting_diagnostic as diagnostic

from organism_v6 import rulegame_process_material as exporter

from organism_v6 import train_adapter_v3 as trainer

from test_rulegame_process_material import Backend, Tokenizer
LESSON = "Compare predictions with observations."

spec = importlib.util.spec_from_file_location("astra_rulegame_process_write", "/tmp/astra_rulegame_process_write_20260912.py")

bridge = importlib.util.module_from_spec(spec)

sys.modules[spec.name] = bridge

spec.loader.exec_module(bridge)

def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()

class Parameter:
    def __init__(self, shape, trainable):
        self.shape, self.requires_grad, self.dtype = shape, trainable, "torch.float32"

    def numel(self):
        return math.prod(self.shape)

class Base:
    def __init__(self, model):
        self.name_or_path = model
        self.config = SimpleNamespace(num_hidden_layers=1)
        self.parameters = {"model.embed_tokens.weight": Parameter((4, 4), True)}
        self.hook = None

    def named_parameters(self):
        return self.parameters.items()

    def register_forward_pre_hook(self, hook, with_kwargs=False):
        if not with_kwargs:
            raise AssertionError("actual forward kwargs audit required")
        self.hook = hook
        return SimpleNamespace(remove=lambda: None)

    def adapt(self):
        self.parameters["model.embed_tokens.weight"].requires_grad = False
        for group, projections in (("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
                                   ("mlp", ("gate_proj", "up_proj", "down_proj"))):
            for projection in projections:
                for part, shape in (("A", (8, 4)), ("B", (4, 8))):
                    self.parameters[f"model.layers.0.{group}.{projection}.lora_{part}.default.weight"] = Parameter(shape, True)

class BridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rulegame-process-write-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        bridge.write_json(self.model / "config.json", dict(model_type="qwen2", num_hidden_layers=1))
        (self.model / "weights.fixture").write_bytes(b"CPU fixture only, not weights")
        self.formation = self.root / "formation_run"
        self.deadline, self.lease = time.time()+3600, time.time()+8*3600
        self.original = diagnostic.prepare(self.formation, self.model, "2", iso(self.lease), "interaction_v3")
        self.tokenizer = Tokenizer()
        self.data = self.formation / "formation" / "data"
        self.data.mkdir(parents=True)
        def varied(request, text):
            if request["role"] == "wake" and request["tick"] == 2:
                return "\nOwn reasoning " + ("longer " if request["arm"] == "A" else "") + str(request["eid"]) + ".\n" + text.replace("ACT: TRY ", "TRY: ") + "\t\n"
            return text
        backend = Backend(varied)
        backend.source_identity = diagnostic.expected_identity(self.original)
        calls = diagnostic.Calls(self.data / "calls", backend, "formation", backend.identity(), "interaction_v3")
        events = diagnostic.Events(self.data / "events.jsonl")
        result = diagnostic.run_formation(calls, events)
        diagnostic.write_json(self.data / "identity.json", dict(stage="formation", protocol="interaction_v3",
            backend=backend.identity(), model_files=self.original["model_files"]))
        diagnostic.write_json(self.data / "result.json", result)
        diagnostic.write_json(self.data / "usage.json", diagnostic.usage(self.data))
        diagnostic.capture_manifest(self.data)
        diagnostic.write_json(self.formation / "formation" / "result.json", dict(status="AWAITING_MAIN_AUDIT"))
        self.candidate = exporter.inspect_capture(self.data, protocol=bridge.PROTOCOL)
        self.audit = exporter.review_template(self.candidate, protocol=bridge.PROTOCOL)
        self.audit["context_distillation_acknowledged"] = True
        for review in self.audit["reviews"]:
            review.update(decision="accept", notes="Mock Main context/target assessment only.")
        self.pair = exporter.build_process_pair(self.data, self.audit, self.tokenizer,
            fixed_candidate=self.candidate, protocol=bridge.PROTOCOL)
        self.audit["native_review"] = bridge.native_review_template(self.pair)
        for row in self.audit["native_review"]["rows"]:
            row.update(decision="accept", notes="Synthetic tokenizer only; no native acceptance.")
        self.candidate_path, self.audit_path = self.root / "candidate.json", self.root / "main_review.json"
        bridge.write_json(self.candidate_path, self.candidate)
        bridge.write_json(self.audit_path, self.audit)
        self.output = self.root / "new_write"
        self.loads, self.fit_calls, self.supervisions = [], [], []
        self.fail_arm, self.corrupt = None, None

    def prepare(self, **kwargs):
        values = dict(formation_root=self.formation, main_review=self.audit_path, fixed_candidate=self.candidate_path,
            source_root=SOURCE, out=self.output, device="2", deadline=iso(self.deadline), lease_end=iso(self.lease))
        values.update(kwargs)
        with patch.object(diagnostic, "native_tokenizer", return_value=self.tokenizer), \
             patch.object(bridge, "load_native", side_effect=AssertionError("no model during prepare")), \
             patch.object(diagnostic.supervisor, "gpu_processes_absent", side_effect=AssertionError("no GPU during prepare")):
            self.prepared = bridge.prepare(**values)
        return self.prepared

    def test_v1_shortage_preserved_v2_alias_and_wrong_predictions_unchanged(self):
        original = exporter.inspect_capture(self.data)
        self.assertEqual(original["status"], "PAIRED_SHORTAGE")
        self.assertEqual(original["selection_sha256"], self.candidate["selection_sha256"])
        self.assertEqual(original["fixed_slots"], self.candidate["fixed_slots"])
        self.assertTrue(self.candidate["policy"]["after_inventory_exploratory"])
        self.assertIn("96a71289", self.candidate["policy"]["decision"])
        self.assertTrue(any(row["source"]["execution"]["predicted"] != row["source"]["execution"]["observed"]
                            for row in self.candidate["candidates"]))
        before = diagnostic.tree_hashes(self.formation)
        self.prepare()
        for source in self.candidate["candidates"]:
            item = diagnostic.read(self.output / "material/corpora" / (source["arm"]+".json"))["corpus"][source["lesson"]]
            self.assertEqual(item["spans"][1][0], source["target"])
            self.assertIn("\nTRY: ", item["spans"][1][0])
            self.assertTrue(item["spans"][1][0].endswith("\t\n"))
            self.assertNotEqual(item["spans"][0][0], source["source"]["response_receipt"]["response"]["rendered_prompt"])
        self.assertEqual(before, diagnostic.tree_hashes(self.formation))

    def test_process_protocol_and_required_review_negative_cases(self):
        for mode in ("record", "P0", "v1", "no_native_review", "partial_native_review", "pending_native_review",
                     "no_scope_ack", "wrong_actor", "missing_row", "declined_row", "no_notes", "stale_candidate"):
            with self.subTest(mode=mode):
                audit = copy.deepcopy(self.audit)
                if mode in ("record", "P0", "v1"):
                    audit["protocol"] = {"record": "rulegame_record_pair_v1", "P0": "P0", "v1": exporter.PROTOCOL}[mode]
                elif mode == "no_native_review":
                    del audit["native_review"]
                elif mode == "partial_native_review":
                    audit["native_review"]["rows"].pop()
                elif mode == "pending_native_review":
                    audit["native_review"]["rows"][0]["decision"] = "pending"
                elif mode == "no_scope_ack":
                    audit["context_distillation_acknowledged"] = False
                elif mode == "wrong_actor":
                    audit["actor"] = "automatic_consensus"
                elif mode == "missing_row":
                    audit["reviews"].pop()
                elif mode == "declined_row":
                    audit["reviews"][0]["decision"] = "reject"
                elif mode == "no_notes":
                    audit["reviews"][0]["notes"] = " "
                else:
                    audit["candidate_sha256"] = "f"*64
                self.replace_json(self.audit_path, audit)
                with patch.object(diagnostic, "native_tokenizer", side_effect=AssertionError("must reject before tokenizer")), \
                     self.assertRaises(ValueError):
                    bridge.prepare(self.formation, self.audit_path, self.candidate_path, SOURCE, self.output,
                        "2", iso(self.deadline), iso(self.lease))
                self.assertFalse(self.output.exists())

    def test_native_review_requires_exact_context_target_ids_and_order(self):
        for field in ("rendered_context_sha256", "raw_target_utf8_sha256", "transformed_input_ids_sha256",
                      "original_prompt_ids_sha256", "original_output_ids_sha256", "source_call_id", "slot_id"):
            with self.subTest(field=field):
                audit = copy.deepcopy(self.audit)
                audit["native_review"]["rows"][0][field] = "wrong"
                self.replace_json(self.audit_path, audit)
                with self.assertRaisesRegex(ValueError, "native review exact"):
                    self.prepare()
                self.assertFalse(self.output.exists())

    def test_missing_wrong_stale_or_partial_candidate_never_reselected(self):
        original = copy.deepcopy(self.candidate)
        for mode in ("wrong_source", "partial", "shortage", "protocol", "source_slot", "teacher_bytes"):
            with self.subTest(mode=mode):
                candidate = copy.deepcopy(original)
                if mode == "wrong_source":
                    candidate["source_binding"]["capture_root"] = str(self.root)
                elif mode == "partial":
                    candidate["candidates"].pop()
                elif mode == "shortage":
                    candidate["status"] = "PAIRED_SHORTAGE"
                elif mode == "protocol":
                    candidate["protocol"] = exporter.PROTOCOL
                elif mode == "source_slot":
                    candidate["candidates"][0]["selected"]["call_id"] = "later"
                else:
                    candidate["teacher_sources_audit_only"][0]["raw_text"] += " changed"
                self.replace_json(self.candidate_path, candidate)
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.output.exists())
        with self.assertRaises(FileNotFoundError):
            self.prepare(fixed_candidate=self.root / "missing.json")

    def test_candidate_file_and_completion_receipt_pinned_at_write(self):
        self.prepare()
        for path in (self.candidate_path, self.formation / "formation/result.json"):
            original = path.read_bytes()
            path.write_bytes(original+b" ")
            with self.assertRaisesRegex(ValueError, "changed"):
                self.run_pair()
            path.write_bytes(original)
        self.assertFalse(self.loads or self.fit_calls)

    def test_export_api_never_implicit_v1_and_manifest_is_pinned(self):
        with patch.object(exporter, "build_process_pair", wraps=exporter.build_process_pair) as build, \
             patch.object(exporter, "export_pair", wraps=exporter.export_pair) as export:
            self.prepare()
        self.assertTrue(build.call_args_list)
        self.assertEqual(export.call_count, 1)
        for call in build.call_args_list + export.call_args_list:
            self.assertEqual(call.kwargs["protocol"], bridge.PROTOCOL)
            self.assertEqual(call.kwargs["fixed_candidate"], self.candidate)
            self.assertEqual(call.kwargs["max_len"], 4096)
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["process_api"], bridge.API)
        self.assertEqual(plan["model_origin"], bridge.ORIGIN)
        self.assertFalse(any(plan["claims"][key] for key in ("clean_lineage", "G3", "P1", "G5", "H1", "H2")))
        self.assertEqual(plan["implementation"][str(bridge.FROZEN_DRIVER)], bridge.FROZEN_SHA256)
        manifest = self.output / "material/export_manifest.json"
        manifest.write_bytes(manifest.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError, "sealed material changed"):
            self.run_pair()

    def test_full_tokens_rejects_record_P0_v1_extra_target_and_target_EOS(self):
        for mode in ("record", "P0", "v1", "append", "masked_target", "eos", "overlength", "missing_pad"):
            corpus = copy.deepcopy(self.pair["corpora"]["P"])
            tokenizer = Tokenizer()
            item = corpus["corpus"][0]
            if mode == "record":
                item["spans"][0][2], item["spans"][1][2] = "record_context", "own_raw_record"
            elif mode == "P0":
                corpus = {"corpus": ["P0 teacher restatement", "legacy"]}
            elif mode == "v1":
                item["view"] = exporter.PROTOCOL
            elif mode == "append":
                item["spans"].append(["restatement", True, "extra"])
            elif mode == "masked_target":
                item["spans"][1][1] = False
            elif mode == "eos":
                tokenizer.eos_token_id = tokenizer.encode(item["spans"][1][0])[0]
            elif mode == "overlength":
                item["spans"][0][0] += "x"*4096
            else:
                tokenizer.pad_token_id = None
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                bridge.full_tokens(corpus, tokenizer, trainer)

    def test_pair_partial_source_and_token_joins_fail_before_output(self):
        original = exporter.build_process_pair
        for mode in ("partial_arm", "raw_target", "context", "source_call", "native_ids", "input_ids", "mask",
                     "first_predictor", "reused_native_ids", "future_prediction", "totals", "teacher_meta", "protocol"):
            def changed(*args, **kwargs):
                pair = original(*args, **kwargs)
                item = pair["corpora"]["P"]["corpus"][0]
                receipt = pair["audit"]["receipts"]["P"][0]
                transformed = receipt["transformed_training"]
                if mode == "partial_arm":
                    pair["corpora"]["A"]["corpus"].pop()
                elif mode == "raw_target":
                    item["spans"][1][0] += "extra reasoning"
                elif mode == "context":
                    transformed["context"] += "future outcome"
                elif mode == "source_call":
                    item["meta"]["source_call_id"] = "other-arm"
                elif mode == "native_ids":
                    receipt["original_native_capture"]["prompt_token_ids"] = [10]
                elif mode == "input_ids":
                    transformed["input_ids"][0] += 1
                elif mode == "mask":
                    transformed["labels"][0] = 42
                elif mode == "first_predictor":
                    transformed["first_target_predictor"] += 1
                elif mode == "reused_native_ids":
                    transformed["source_output_token_ids_reused_as_targets"] = True
                elif mode == "future_prediction":
                    transformed["predictor_positions"].pop()
                elif mode == "totals":
                    pair["audit"]["token_totals"]["P"]["target_tokens"] += 1
                elif mode == "teacher_meta":
                    item["meta"]["teacher"] = "restatement"
                else:
                    pair["protocol"] = exporter.PROTOCOL
                return pair
            with self.subTest(mode=mode), patch.object(exporter, "build_process_pair", side_effect=changed), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_native_source_tokenizer_mismatch_blocks_prepare(self):
        with patch.object(self.tokenizer, "apply_chat_template", return_value="wrong template"), self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_export_failure_preserves_evidence_and_forbids_retry(self):
        with patch.object(exporter, "export_pair", side_effect=RuntimeError("no automatic substitute")), \
             self.assertRaisesRegex(RuntimeError, "no automatic"):
            self.prepare()
        self.assertTrue(self.output.is_dir())
        self.assertFalse((self.output / "plan.json").exists())
        with self.assertRaisesRegex(ValueError, "fresh output"):
            self.prepare()
        self.assertFalse(self.loads or self.fit_calls)

    def test_token_exposure_naturally_unequal_no_synthetic_target_padding(self):
        self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        self.assertNotEqual(plan["tokens"]["P"]["tokens"]["target"], plan["tokens"]["A"]["tokens"]["target"])
        self.assertNotEqual(plan["tokens"]["P"]["tokens"]["total"], plan["tokens"]["A"]["tokens"]["total"])
        for arm in bridge.ARMS:
            tokens = diagnostic.read(self.output / "material/provenance" / (arm+".tokens.json"))
            width = tokens["max_segment_tokens"]
            self.assertEqual(len(tokens["per_batch_exposure"]), 12)
            for row, labels in zip(tokens["rows"], tokens["batch"]["labels"], strict=True):
                self.assertEqual(row["target_tokens"], row["raw_target_tokens"]+1)
                self.assertEqual(row["full_target_exposure"], 12*row["target_tokens"])
                self.assertEqual(row["padded_input_tokens"], width)
                self.assertEqual(labels[row["input_tokens"]:], [-100]*row["padding_tokens"])
                self.assertEqual(row["labels"][:row["context_tokens"]], [-100]*row["context_tokens"])
                self.assertEqual(row["labels"].count(0), 1)
            self.assertEqual(tokens["exposure"]["full_target_tokens_seen"], 12*tokens["tokens"]["target"])
            self.assertEqual(tokens["exposure"]["padded_input_tokens_seen"], 24*width)

    def test_collator_position_segment_and_causal_mask_fail_closed(self):
        original = trainer.collate
        for field in ("position_ids", "segment_ids", "labels", "input_ids", "n_target", "n_tokens"):
            def changed(*args):
                batch = original(*args)
                if field.startswith("n_"):
                    batch[field] += 1
                else:
                    batch[field][0][0] += 1
                return batch
            with self.subTest(field=field), patch.object(trainer, "collate", side_effect=changed), self.assertRaises(ValueError):
                bridge.full_tokens(self.pair["corpora"]["P"], self.tokenizer, trainer)

    def test_worker_native_tokenizer_mismatch_prevents_fit(self):
        self.prepare()
        def changed(model):
            base = Base(model)
            tokenizer = Tokenizer()
            original = tokenizer.encode
            tokenizer.encode = lambda text, **kwargs: original(text, **kwargs)+([42] if text.startswith("<user>") else [])
            return tokenizer, base
        with patch.object(self, "load_native", side_effect=changed), self.assertRaisesRegex(ValueError, "tokenization changed"):
            self.run_pair()
        self.assertFalse(self.fit_calls)

    def test_no_launch_without_actual_supervisor_ownership(self):
        self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        stage = self.output / "run/P"
        stage.mkdir(parents=True)
        launch = dict(controller_pid=234, command=["expected"], hard_end=time.time()+1000)
        receipt = dict(pid=123, pgid=123, device="2", argv=["expected"], timeout=600, started=time.monotonic())
        for key, value in (("pid", 999), ("pgid", 999), ("argv", ["wrong"]), ("device", "3"), ("timeout", 601)):
            self.replace_json(stage / "process.json", dict(receipt, **{key: value}))
            with self.subTest(key=key), patch.object(os, "getpid", return_value=123), patch.object(os, "getpgrp", return_value=123), \
                 patch.object(os, "getppid", return_value=234), patch.object(bridge.threading, "Thread") as thread, self.assertRaises(ValueError):
                with bridge.worker_ownership(self.output, "P", plan, launch, diagnostic):
                    self.fail("not supervised")
            thread.assert_not_called()

    def test_parent_death_and_worker_expiry_kill_only_owned_group(self):
        self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        stage = self.output / "run/P"
        stage.mkdir(parents=True)
        launch = dict(controller_pid=234, command=["expected"], hard_end=time.time()+1000)
        for mode in ("parentdeath", "worker_expiry", "controller_work_end"):
            self.replace_json(stage / "process.json", dict(pid=123, pgid=123, device="2", argv=["expected"], timeout=600,
                started=time.monotonic()-(601 if mode == "worker_expiry" else 0)))
            if mode == "controller_work_end":
                launch["hard_end"] = time.time()+139
            with self.subTest(mode=mode), patch.object(os, "getpid", return_value=123), patch.object(os, "getpgrp", return_value=123), \
                 patch.object(os, "getppid", side_effect=[234, 1 if mode == "parentdeath" else 234]), \
                 patch.object(bridge.threading, "Thread") as thread, patch.object(bridge.threading, "Event") as event, \
                 patch.object(os, "killpg") as kill:
                event.return_value.wait.return_value = False
                with bridge.worker_ownership(self.output, "P", plan, launch, diagnostic):
                    thread.call_args.kwargs["target"]()
                kill.assert_called_once_with(123, bridge.signal.SIGTERM)
                event.return_value.set.assert_called_once()

    def test_frozen_driver_hash_and_wrong_interpreter_fail_closed(self):
        self.prepare()
        with patch.object(sys, "executable", "/wrong/python"), self.assertRaisesRegex(ValueError, "interpreter differs"):
            self.run_pair()
        with patch.object(bridge, "FROZEN_SHA256", "f"*64), self.assertRaisesRegex(ValueError, "frozen original"):
            self.run_pair()
        self.assertFalse(self.loads or self.fit_calls)

    def test_actual_forward_inputs_require_both_full_rows_and_exact_masks(self):
        tokens = bridge.full_tokens(self.pair["corpora"]["P"], self.tokenizer, trainer)
        for order in ([0, 1], [1, 0]):
            batch = bridge.expected_forward_batch(tokens, order)
            receipt = bridge.forward_receipt(batch, tokens, 0)
            self.assertEqual(receipt["row_order"], order)
            self.assertEqual(receipt["batch_exposure"]["full_target_tokens"], tokens["tokens"]["target"])
        for mode in ("input_ids", "labels", "attention_mask", "partial", "duplicate", "extra_forward"):
            batch = bridge.expected_forward_batch(tokens, [0, 1])
            index = 0
            if mode in ("input_ids", "labels", "attention_mask"):
                batch[mode][0] = batch[mode][0].copy()
                batch[mode][0][0] += 1
            elif mode == "partial":
                batch["input_ids"].pop()
            elif mode == "duplicate":
                for key in batch:
                    batch[key][1] = batch[key][0]
            else:
                index = 12
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                bridge.forward_receipt(batch, tokens, index)

    def test_tampered_actual_forward_exposure_fails_fit_validation(self):
        self.prepare()
        self.run_pair()
        plan = diagnostic.read(self.output / "plan.json")
        path = self.output / "fits/P/forwards/0001.json"
        receipt = diagnostic.read(path)
        receipt["batch_exposure"]["full_target_tokens"] += 1
        self.replace_json(path, receipt)
        with self.assertRaisesRegex(ValueError, "actual forward exposure changed"):
            bridge.validate_fit(self.output, "P", plan, diagnostic, trainer)

    def test_wrong_source_base_stage_and_missing_pair_fail_before_output(self):
        path = self.data / "identity.json"
        identity = diagnostic.read(path)
        for mode in ("stage", "protocol", "base"):
            value = copy.deepcopy(identity)
            if mode == "base":
                value["model_files"] = {"wrong": "f"*64}
            else:
                value[mode] = "evaluation" if mode == "stage" else "strict_v1"
            self.replace_json(path, value)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(self.output.exists())
        self.replace_json(path, identity)
        with self.assertRaises(ValueError):
            self.prepare(source_root=self.root)
        self.assertFalse(self.output.exists())

    def replace_json(self, path, value):
        Path(path).write_bytes(bridge.encoded(value))


    def load_native(self, model):
        base = Base(model)
        self.loads.append(base)
        return self.tokenizer, base


    def training(self, items, tokenizer, base, cfg, out_dir, **kwargs):
        adapter = Path(out_dir)
        arm = adapter.parent.name
        self.fit_calls.append(dict(arm=arm, items=items, cfg=asdict(cfg), kwargs=kwargs, base=base))
        self.assertIsNone(kwargs["init_adapter"])
        self.assertNotIn("REVIEW_PARENT_TEXT_ONLY", json.dumps(items))
        self.assertNotIn(LESSON, json.dumps(items))
        self.assertEqual([span[2] for span in items[0]["spans"]], ["parent_removed_wake_context", "complete_own_raw_wake"])
        adapter.mkdir()
        base.adapt()
        tokens = bridge.full_tokens(dict(corpus=items), tokenizer, trainer)
        def forward(index):
            batch = bridge.expected_forward_batch(tokens, [0, 1] if index % 2 == 0 else [1, 0])
            kwargs = {key: SimpleNamespace(detach=lambda value=value: SimpleNamespace(
                cpu=lambda: SimpleNamespace(tolist=lambda: value))) for key, value in batch.items()}
            base.hook(base, (), kwargs)
        forward(0)
        if arm == self.fail_arm:
            raise RuntimeError("mock fit failed " + arm)
        for index in range(1, 12):
            forward(index)
        trainability = bridge.trainability(base, 1)
        tensors, offset = {}, 0
        for name, item in trainability["adapters"].items():
            size = item["numel"] * 4
            tensors["base_model.model.model." + name] = dict(dtype="F32", shape=item["shape"], data_offsets=[offset, offset+size])
            offset += size
        header = json.dumps(tensors).encode()
        (adapter / "adapter_model.safetensors").write_bytes(struct.pack("<Q", len(header)) + header + bytes(offset))
        bridge.write_json(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
            peft_type="LORA", target_modules=list(trainer.ALL_PROJ), base_model_name_or_path=cfg.model))
        manifest = dict(recipe=trainer.RECIPE, config=asdict(cfg), base_model=cfg.model, empty=False,
            steps=12, micro_batches=12, epochs_run=12, nonfinite_batches=0, final_loss=.1, mean_loss_per_epoch=[.1]*12,
            corpus=dict(file=kwargs["corpus_name"], sha256=kwargs["corpus_sha"], n_items=2, n_encoded=2, n_skipped_no_target=0),
            tokens=tokens["tokens"], train_tokens_seen=tokens["train_tokens_seen"],
            truncation=dict(overflow="split", items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0,
                items_split=0, segments_from_splits=0, max_segment_tokens=tokens["max_segment_tokens"]),
            packing=dict(mode="one_item_per_sequence", n_sequences=2, n_groups=2, isolation_check=dict(ran=False)),
            lora=dict(rank=8, alpha=16, dropout=.05, scaling=2.0, target_modules=list(trainer.ALL_PROJ), layers="all",
                n_layers=1, freeze_a=False, trainable_params=trainability["trainable_params"]))
        bridge.write_json(adapter / "train_manifest.json", manifest)
        bridge.write_json(adapter / "train_meta.json", dict(recipe=trainer.RECIPE, n_texts=2, steps=12,
            tokens=tokens["train_tokens_seen"], rank=8, epochs=12, lr=1e-4, seed=2, final_loss=.1))
        (adapter / "DONE").write_text("ok\n")
        return manifest


    def supervise(self, root, plan, stage, command):
        stage.mkdir()
        self.supervisions.append(dict(plan=plan, stage=stage, command=command))
        self.assertEqual(plan["device"], "2")
        self.assertEqual(plan["model"], str(self.model))
        controller = diagnostic.read(root / "run" / "controller.json")
        self.assertEqual(plan["lease_end"], controller["hard_end"])
        self.assertLessEqual(controller["hard_end"] - controller["started_wall"], 1200)
        self.assertEqual(controller["cleanup_reserve"], 140)
        arm = command[command.index("--arm") + 1]
        token = command[command.index("--launch-token") + 1]
        plan_hash = command[command.index("--plan-sha256") + 1]
        succeeded = False
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="2"):
                bridge.worker(root, arm, plan_hash, token, allow_gpu=True)
            if self.corrupt:
                self.corrupt(root, arm)
            succeeded = True
        finally:
            receipt = dict(ok=succeeded, reservation_release_verified=True,
                reserved_seconds=.01, owned_group_empty=True, gpu_processes_absent=True)
            bridge.write_json(stage / "supervision.json", receipt)
        return receipt


    def run_pair(self, allow_gpu=True):
        with patch.object(bridge, "load_native", side_effect=self.load_native), \
             patch.object(trainer, "run_training", side_effect=self.training), \
             patch.object(diagnostic, "supervise", side_effect=self.supervise), \
             patch.object(bridge, "worker_ownership", return_value=nullcontext()):
            return bridge.write_pair(self.output, self.prepared["plan_sha256"], allow_gpu=allow_gpu)


    def test_prepare_preserves_virtualenv_interpreter_symlink(self):
        executable = self.root / "venv" / "bin" / "python"
        executable.parent.mkdir(parents=True)
        executable.symlink_to(sys.executable)
        with patch.object(sys, "executable", str(executable)):
            self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["python"], str(executable))
        self.assertNotEqual(plan["python"], str(executable.resolve()))


    def test_path_freshness_and_six_hour_margin(self):
        for values in (dict(out=self.formation / "nested"), dict(out=self.model), dict(device="0,1"),
                       dict(deadline=iso(time.time()+100)), dict(lease_end=iso(self.deadline+5*3600))):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.prepare(**values)
        self.prepare()
        with self.assertRaisesRegex(ValueError, "fresh output"):
            self.prepare()


    def test_two_fresh_fits_exact_recipe_raw_tokens_and_no_readout(self):
        self.prepare()
        result = self.run_pair()
        self.assertEqual(result["status"], "PAIRED_ADAPTERS_SAVED_READOUT_PENDING")
        self.assertEqual([call["arm"] for call in self.fit_calls], ["P", "A"])
        self.assertEqual(len(self.loads), 2)
        self.assertIsNot(self.loads[0], self.loads[1])
        for call in self.fit_calls:
            cfg = call["cfg"]
            self.assertEqual({key: cfg[key] for key in ("rank", "alpha", "dropout", "lr", "epochs", "batch_size", "grad_accum", "seed", "max_len", "pack")},
                dict(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=12, batch_size=2, grad_accum=1, seed=2, max_len=4096, pack=False))
            self.assertFalse(cfg["svd_init"] or cfg["freeze_a"] or cfg["chat_template"])
            self.assertTrue(cfg["add_eos"])
            self.assertEqual(cfg["model"], str(self.model))
            self.assertIsNone(call["kwargs"]["init_adapter"])
        self.assertFalse((self.output / "evaluation").exists())
        self.assertFalse((self.output / "readout").exists())
        self.assertTrue(all(receipt["steps"] == 12 for receipt in result["arms"].values()))


    def test_gpu_opt_in_before_any_launch_or_model_and_worker_not_direct(self):
        with patch.object(bridge, "checked_plan") as checked:
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                bridge.write_pair("not-read", "not-read")
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                bridge.worker("not-read", "P", "not-read", "not-read")
            checked.assert_not_called()
        self.prepare()
        with self.assertRaises(FileNotFoundError):
            bridge.worker(self.output, "P", self.prepared["plan_sha256"], "forged", allow_gpu=True)


    def test_first_fit_failure_preserves_partial_and_never_starts_A(self):
        self.prepare()
        self.fail_arm = "P"
        with self.assertRaisesRegex(RuntimeError, "mock fit failed P"):
            self.run_pair()
        self.assertEqual([call["arm"] for call in self.fit_calls], ["P"])
        self.assertTrue((self.output / "fits" / "P" / "pre_update_trainability.json").exists())
        self.assertFalse((self.output / "fits" / "A").exists())
        with self.assertRaises(FileExistsError):
            self.run_pair()


    def test_second_fit_failure_preserves_first_no_retry_or_readout(self):
        self.prepare()
        self.fail_arm = "A"
        with self.assertRaisesRegex(RuntimeError, "mock fit failed A"):
            self.run_pair()
        failure = diagnostic.read(self.output / "run" / "failure.json")
        self.assertEqual(failure["status"], "PARTIAL_FAILED")
        self.assertEqual(set(failure["completed"]), {"P"})
        self.assertTrue((self.output / "fits" / "P" / "adapter" / "DONE").exists())
        self.assertFalse((self.output / "fits" / "A" / "adapter" / "DONE").exists())
        with self.assertRaises(FileExistsError):
            self.run_pair()


    def test_changed_corpus_model_and_audit_rejected_before_fits(self):
        self.prepare()
        corpus = self.output / "material" / "corpora" / "P.json"
        raw = corpus.read_bytes()
        corpus.write_bytes(raw + b" ")
        with self.assertRaisesRegex(ValueError, "sealed material"):
            self.run_pair()
        corpus.write_bytes(raw)
        self.replace_json(self.audit_path, {**self.audit, "provenance_notes": "changed"})
        with self.assertRaisesRegex(ValueError, "Main review changed"):
            self.run_pair()
        self.assertFalse(self.loads)


    def test_changed_recipe_even_rehashed_is_not_allowed(self):
        self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        plan["config"]["lr"] = .01
        self.replace_json(self.output / "plan.json", plan)
        with self.assertRaisesRegex(ValueError, "recipe changed"):
            bridge.write_pair(self.output, bridge.digest(self.output / "plan.json"), allow_gpu=True)


    def test_worker_token_ids_and_trainable_base_fail_closed(self):
        self.prepare()
        original = self.training
        def bad_trainability(items, tokenizer, base, *args, **kwargs):
            adapt = base.adapt
            def unfreeze():
                adapt()
                base.parameters["model.embed_tokens.weight"].requires_grad = True
            base.adapt = unfreeze
            return original(items, tokenizer, base, *args, **kwargs)
        with patch.object(self, "training", side_effect=bad_trainability), self.assertRaisesRegex(ValueError, "base not frozen"):
            self.run_pair()
        self.assertFalse((self.output / "fits" / "A").exists())


    def test_forged_update_count_is_rejected_before_second_fit(self):
        self.prepare()
        def corrupt(root, arm):
            path = root / "fits" / arm / "adapter" / "train_manifest.json"
            manifest = diagnostic.read(path)
            manifest["steps"] = 11
            self.replace_json(path, manifest)
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, "sealed fit changed|update count"):
            self.run_pair()
        self.assertEqual(len(self.fit_calls), 1)


    def test_saved_weight_bytes_and_adapter_identity_bound(self):
        self.prepare()
        def corrupt(root, arm):
            path = root / "fits" / arm / "adapter" / "adapter_model.safetensors"
            with path.open("ab") as target:
                target.write(b"extra")
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, "sealed fit changed|saved weight size"):
            self.run_pair()


    def test_prior_adapter_cannot_change_in_second_worker(self):
        self.prepare()
        def corrupt(root, arm):
            if arm == "A":
                (root / "fits" / "P" / "adapter" / "DONE").write_text("changed")
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, "independent adapter changed"):
            self.run_pair()
        self.assertFalse((self.output / "run" / "result.json").exists())


    def test_watchdog_reserves_cleanup_and_rejects_expired_window(self):
        with self.assertRaisesRegex(ValueError, "cleanup reserve"):
            with bridge.controller_watchdog(time.time()+139):
                self.fail("expired work window accepted")
        with patch.object(bridge.signal, "setitimer") as timer, patch.object(bridge.signal, "getitimer", return_value=(0., 0.)):
            with bridge.controller_watchdog(time.time()+1200):
                initial = timer.call_args.args[1]
                self.assertTrue(1059 < initial <= 1060)
                with bridge.supervisor_cleanup_window(time.time()+1200):
                    self.assertEqual(timer.call_args.args[1], 0)
            self.assertEqual(timer.call_args.args[1], 0)


    def test_base_pins_changed_before_fit_never_load_model(self):
        self.prepare()
        (self.model / "weights.fixture").write_bytes(b"different base")
        with self.assertRaisesRegex(ValueError, "model bytes changed"):
            self.run_pair()
        self.assertFalse(self.loads or self.fit_calls)


    def test_manifest_tokens_drops_packing_and_saved_config_are_validated(self):
        self.prepare()
        self.run_pair()
        plan = diagnostic.read(self.output / "plan.json")
        adapter = self.output / "fits" / "P" / "adapter"
        original = diagnostic.read(adapter / "train_manifest.json")
        for mode in ("tokens", "split", "packing", "warm_start"):
            with self.subTest(mode=mode):
                manifest = json.loads(bridge.encoded(original))
                if mode == "tokens":
                    manifest["tokens"]["target"] += 1
                elif mode == "split":
                    manifest["truncation"]["items_split"] = 1
                elif mode == "packing":
                    manifest["packing"]["mode"] = "block4d_by_group"
                else:
                    manifest["warm_start"] = {}
                self.replace_json(adapter / "train_manifest.json", manifest)
                with self.assertRaises(ValueError):
                    bridge.validate_fit(self.output, "P", plan, diagnostic, trainer)
        self.replace_json(adapter / "train_manifest.json", original)
        saved = diagnostic.read(adapter / "adapter_config.json")
        saved["base_model_name_or_path"] = str(self.formation)
        self.replace_json(adapter / "adapter_config.json", saved)
        with self.assertRaisesRegex(ValueError, "saved adapter config/base"):
            bridge.validate_fit(self.output, "P", plan, diagnostic, trainer)


    def test_unverified_cleanup_prevents_second_fit(self):
        self.prepare()
        original = self.supervise
        def unreleased(*args):
            receipt = original(*args)
            return dict(receipt, reservation_release_verified=False)
        with patch.object(self, "supervise", side_effect=unreleased), self.assertRaisesRegex(ValueError, "cleanup unverified"):
            self.run_pair()
        self.assertEqual([call["arm"] for call in self.fit_calls], ["P"])
        self.assertFalse((self.output / "fits" / "A").exists())



if __name__ == "__main__":
    unittest.main()
