"""Synthetic capture + mocked fresh V3 fit boundaries; no GPU/native/model load."""
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.util
import json
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
from organism_v6 import rulegame_record_material as exporter
from organism_v6 import train_adapter_v3 as trainer
from test_rulegame_record_material import Backend, Tokenizer, LESSON

spec = importlib.util.spec_from_file_location("astra_rulegame_record_write", "/tmp/astra_rulegame_record_write_v2_20260912.py")
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

    def register_forward_pre_hook(self, hook):
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
        temporary = tempfile.TemporaryDirectory(prefix="rulegame-write-test-")
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
        backend = Backend(tokenizer=self.tokenizer)
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
        self.selection = diagnostic.select_records(diagnostic.check_capture(self.data))
        self.audit = diagnostic.audit_template(self.data)
        self.audit.update(provenance_decision="accept", provenance_notes="MOCK Main; REVIEW_PARENT_TEXT_ONLY.")
        for review in self.audit["reviews"]:
            review.update(decision="accept", notes="Mock parent assessment only.")
        self.audit["record_review"] = dict(decision="accept", scope="actual_record_context_and_target",
            notes="Mock Main context/target review", selection_sha256=diagnostic.value_hash(self.selection))
        self.audit["fixed_selection"] = self.selection
        self.audit_path = self.root / "main_audit.json"
        bridge.write_json(self.audit_path, self.audit)
        self.output = self.root / "new_write"
        self.loads, self.fit_calls, self.supervisions = [], [], []
        self.fail_arm, self.corrupt = None, None

    def prepare(self, **kwargs):
        values = dict(formation_root=self.formation, main_audit=self.audit_path, source_root=SOURCE,
            out=self.output, device="2", deadline=iso(self.deadline), lease_end=iso(self.lease))
        values.update(kwargs)
        with patch.object(diagnostic, "native_tokenizer", return_value=self.tokenizer), \
             patch.object(bridge, "load_native", side_effect=AssertionError("no model during prepare")), \
             patch.object(diagnostic.supervisor, "gpu_processes_absent", side_effect=AssertionError("no GPU query during prepare")):
            self.prepared = bridge.prepare(**values)
        return self.prepared

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
        self.assertEqual([span[2] for span in items[0]["spans"]], ["record_context", "own_raw_record"])
        adapter.mkdir()
        base.adapt()
        base.hook(base, ())
        if arm == self.fail_arm:
            raise RuntimeError("mock fit failed " + arm)
        tokens = bridge.full_tokens(dict(corpus=items), tokenizer, trainer)
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
             patch.object(diagnostic, "supervise", side_effect=self.supervise):
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

    def test_prepare_exact_native_pair_and_separate_maps(self):
        source_before = diagnostic.tree_hashes(self.formation)
        self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["original_identity"]["backend"], diagnostic.expected_identity(self.original))
        self.assertEqual(plan["config"], asdict(bridge.fit_config(trainer, self.model)))
        self.assertEqual((plan["controller_seconds"], plan["worker_seconds"], plan["cleanup_seconds"]), (1200, 600, 140))
        self.assertEqual(plan["supplied_lease_end"] - plan["lease_cutoff"], 21600)
        self.assertFalse((self.output / "fits").exists())
        for arm in bridge.ARMS:
            corpus = diagnostic.read(self.output / "material" / "corpora" / (arm + ".json"))
            for item, row in zip(corpus["corpus"], self.selection["selected"][arm]):
                raw = diagnostic.read(self.data / "calls" / (row["call_id"] + ".response.json"))["response"]
                self.assertEqual(item["spans"][0][0], raw["rendered_prompt"])
                self.assertEqual(item["spans"][1][0], raw["text"])
                self.assertTrue(raw["text"].startswith("\n ") and raw["text"].endswith("\t\n"))
                self.assertNotEqual(raw["text"], json.dumps(json.loads(raw["text"])))
            tokens = diagnostic.read(self.output / "material" / "provenance" / (arm + ".tokens.json"))
            self.assertEqual(tokens["train_tokens_seen"], 12 * tokens["tokens"]["total"])
            self.assertTrue(all(row["labels"].count(self.tokenizer.eos_token_id) == 1 for row in tokens["rows"]))
        self.assertEqual(source_before, diagnostic.tree_hashes(self.formation))

    def test_separate_fixed_selection_preserves_audit_and_is_pinned(self):
        self.audit.pop("fixed_selection")
        self.replace_json(self.audit_path, self.audit)
        audit_bytes = self.audit_path.read_bytes()
        selection_path = self.root / "fixed_selection.json"
        bridge.write_json(selection_path, self.selection)
        self.prepare(fixed_selection=selection_path)
        self.assertEqual(self.audit_path.read_bytes(), audit_bytes)
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["fixed_selection_path"], str(selection_path.resolve()))
        self.assertEqual(plan["fixed_selection_sha256"], bridge.digest(selection_path))
        selection_path.write_bytes(selection_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "fixed selection changed"):
            self.run_pair()
        self.assertFalse(self.loads)

    def test_conflicting_embedded_and_separate_selection_rejected_atomically(self):
        selection_path = self.root / "fixed_selection.json"
        different = json.loads(bridge.encoded(self.selection))
        different["selected"]["P"].reverse()
        bridge.write_json(selection_path, different)
        with self.assertRaisesRegex(ValueError, "fixed selection disagree"):
            self.prepare(fixed_selection=selection_path)
        self.assertFalse(self.output.exists())

    def test_pair_export_rejection_is_atomic_and_never_selects_later(self):
        original = exporter.build_record_pair
        def fail_after_pair(*args, **kwargs):
            original(*args, **kwargs)
            raise ValueError("selected A context rejected; no replacement")
        with patch.object(exporter, "build_record_pair", side_effect=fail_after_pair), self.assertRaisesRegex(ValueError, "selected A"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_native_mismatch_missing_selection_and_declined_review_fail_before_output(self):
        for mode in ("selection", "decline", "review", "native"):
            with self.subTest(mode=mode):
                audit = json.loads(bridge.encoded(self.audit))
                if mode == "selection":
                    audit.pop("fixed_selection")
                elif mode == "decline":
                    audit["reviews"][2]["decision"] = "reject"
                elif mode == "review":
                    audit["record_review"]["selection_sha256"] = "wrong"
                self.replace_json(self.audit_path, audit)
                patcher = patch.object(self.tokenizer, "apply_chat_template", return_value="wrong") if mode == "native" else patch.object(bridge, "STEPS", 12)
                with patcher, self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.output.exists())

    def test_altered_fixed_selection_does_not_get_reselected(self):
        self.audit["fixed_selection"]["selected"]["P"].reverse()
        self.replace_json(self.audit_path, self.audit)
        with self.assertRaisesRegex(ValueError, "selection changed"):
            self.prepare()
        self.assertFalse(self.output.exists())

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
        with self.assertRaisesRegex(ValueError, "Main audit changed"):
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

    def test_actual_A_shortage_rejects_whole_preparation(self):
        for row in self.selection["selected"]["A"]:
            self.assertEqual(row["arm"], "A")
        for request_path in (self.data / "calls").glob("*.request.json"):
            request = diagnostic.read(request_path)["request"]
            if request["arm"] == "A" and request["role"] == "record":
                path = request_path.with_name(request_path.name.replace(".request.", ".response."))
                receipt = diagnostic.read(path)
                receipt["response"].update(text="invalid record", output_token_ids=self.tokenizer.encode("invalid record"))
                receipt["response_sha256"] = diagnostic.value_hash(receipt["response"])
                self.replace_json(path, receipt)
        calls = diagnostic.ReplayCalls(self.data / "calls", diagnostic.expected_identity(self.original), "interaction_v3")
        events = diagnostic.Events()
        result = diagnostic.run_formation(calls, events)
        self.replace_json(self.data / "result.json", result)
        (self.data / "events.jsonl").write_bytes(b"".join(diagnostic.encoded(row) for row in events.rows))
        self.replace_json(self.data / "usage.json", diagnostic.usage(self.data))
        self.replace_json(self.data / "manifest.json", dict(files=diagnostic.tree_hashes(self.data, ("manifest.json",))))
        self.selection = diagnostic.select_records(diagnostic.check_capture(self.data))
        self.audit["formation_sha256"] = bridge.digest(self.data / "manifest.json")
        self.audit["fixed_selection"] = self.selection
        self.audit["record_review"]["selection_sha256"] = diagnostic.value_hash(self.selection)
        self.replace_json(self.audit_path, self.audit)
        with self.assertRaisesRegex(ValueError, "paired shortage"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_native_worker_token_mismatch_prevents_training(self):
        self.prepare()
        original = self.load_native
        def changed(model):
            tokenizer, base = original(model)
            alternate = Tokenizer()
            encode = alternate.encode
            alternate.encode = lambda text, **kwargs: encode(text, **kwargs) + ([42] if text.startswith("\n {") else [])
            return alternate, base
        with patch.object(self, "load_native", side_effect=changed), self.assertRaisesRegex(ValueError, "tokenization changed"):
            self.run_pair()
        self.assertFalse(self.fit_calls)

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
