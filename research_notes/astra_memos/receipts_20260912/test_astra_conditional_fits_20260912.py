"""Standard-library fixtures; no repository imports, native models, or GPU probes."""
import copy
from dataclasses import make_dataclass, field
import importlib.util
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("conditional_fits", "/tmp/astra_conditional_fits_20260912.py")
fits = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fits)


class FitTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="conditional-fits-fixture-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source"
        (self.source / "organism_v6").mkdir(parents=True)
        for name in ("conditional_behavior_corpus.py", "train_adapter_v3.py", "reasoning_neutral_probe.py"):
            (self.source / "organism_v6" / name).write_text("fixture source: " + name)
        self.model = self.root / "model"
        self.model.mkdir()
        fits.write(self.model / "config.json", {"model_type": "qwen2"})
        fits.write(self.model / "tokenizer.json", {})
        fits.write(self.model / "tokenizer_config.json", {})
        (self.model / "model.safetensors").write_bytes(b"not real model weights")
        self.material = self.root / "material"
        self.material.mkdir()
        self.out = self.root / "output"
        self.deadline = time.time() + 7200
        self.lease = self.deadline + 100
        self.addCleanup(patch.stopall)
        defaults = dict(model="", rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=4,
            batch_size=4, grad_accum=1, seed=0, pack=False, max_len=512, overflow="truncate",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            dtype="bf16", device="cuda", layers="all", freeze_a=False, svd_init=False,
            max_steps=0, add_eos=True, chat_template=False, shuffle_groups=True, optimizer="adamw")
        fields = [(key, object, field(default_factory=lambda value=value: copy.deepcopy(value))) for key, value in defaults.items()]
        config = make_dataclass("FixtureConfig", fields)
        self.probe = SimpleNamespace(gpu_processes_absent=lambda device: True)
        self.base = SimpleNamespace(REPO=self.source, WORKER_SECONDS=600, CLEANUP_RESERVE=140,
            sources=lambda: {}, tree_hashes=self.tree, model_hashes=self.tree, supervisor=self.probe)
        fits.base = self.base
        fits.trainer = SimpleNamespace(TrainConfig=config)
        self.sources = {name: fits.digest(self.source / "organism_v6" / name) for name in
                        ("conditional_behavior_corpus.py", "train_adapter_v3.py")}
        candidate = {"root": 0, "spellings": {"actions": ["dax", "wug"], "outcomes": ["fep", "nup"]}}
        corpora = {arm: [{"case": index, "arm": arm} for index in range(128)] for arm in fits.ARMS}
        tokenrows = [{"input_tokens": 87 + (index < 112), "target_tokens": 14 + (index < 96)} for index in range(128)]
        audit = dict(status="NATIVE_TOKEN_MATCH_VERIFIED", origin_authenticated=False, no_truncation=True,
            loss_bearing_padding=False, source_sha256=self.sources, corpora=corpora,
            rows={arm: tokenrows for arm in fits.ARMS}, input_tokens_per_epoch={arm: 11248 for arm in fits.ARMS},
            target_tokens_per_epoch={arm: 1888 for arm in fits.ARMS}, tokenizer_path=str(self.model),
            tokenizer_file_hashes={name: fits.digest(self.model / name) for name in
                                  ("config.json", "tokenizer.json", "tokenizer_config.json")},
            optimizer_update_rows={"0": [list(range(start, start+4)) for epoch in range(4) for start in range(0, 128, 4)]})
        recipe = {key: value for key, value in defaults.items() if key not in ("model", "dtype", "device")}
        for name, value in (("candidate.json", candidate), ("native_audit.json", audit), ("recipe.json", recipe),
                            ("teacher_forcing_interface.json", {}), ("AUTH.json", {"corpus": corpora["AUTH"]}),
                            ("DERANGED.json", {"corpus": corpora["DERANGED"]})):
            fits.write(self.material / name, value)
        manifest = dict(files=self.tree(self.material), root=str(self.material), source=str(self.source),
            source_sha256=self.sources, status="NATIVE_PREPARED_NO_FIT_NO_LAUNCH", origin="UNRESOLVED_LOCAL_HASHES_ONLY",
            input_tokens_per_epoch=audit["input_tokens_per_epoch"], target_tokens_per_epoch=audit["target_tokens_per_epoch"])
        fits.write(self.material / "manifest.json", manifest)
        patch.object(fits, "PINS", self.tree(self.material)).start()

    def tree(self, root):
        root = Path(root)
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError("symlink")
        return {str(path.relative_to(root)): fits.digest(path) for path in root.rglob("*") if path.is_file()}

    def prepare(self):
        fits.prepare(self.out, self.material, "2", self.deadline, self.lease)
        return fits.verify(self.out)

    def manifest(self, plan, arm):
        return dict(config=plan["config"], base_model=plan["model"], empty=False, steps=128,
            micro_batches=128, epochs_run=4, nonfinite_batches=0, final_loss=.2,
            corpus=dict(sha256=plan["material_files"][arm+".json"], n_items=128, n_encoded=128, n_skipped_no_target=0),
            tokens=dict(total=11248, target=1888, context=9360), train_tokens_seen=44992,
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            lora=dict(rank=8, alpha=16, dropout=.05, target_modules=plan["config"]["target_modules"],
                      layers="all", freeze_a=False, trainable_params=123))

    def receipt(self):
        return dict(ok=True, returncode=0, reservation_release_verified=True, owned_group_empty=True,
                    gpu_processes_absent=True, reserved_seconds=1)

    def test_prepare_fixed_pair(self):
        plan = self.prepare()
        self.assertEqual(plan["arms"], ["AUTH", "DERANGED"])
        self.assertEqual(plan["counts"]["steps"], 128)
        self.assertEqual(plan["generation_calls"], 0)
        self.assertEqual(plan["origin"], "UNRESOLVED_LOCAL_HASHES_ONLY")

    def test_material_unchanged(self):
        before = self.tree(self.material)
        self.prepare()
        self.assertEqual(before, self.tree(self.material))

    def test_command_fresh_not_warm_and_exact_recipe(self):
        plan = self.prepare()
        for arm, command in plan["commands"].items():
            for key, value in (("--lr", "1e-4"), ("--epochs", "4"), ("--seed", "0"), ("--batch-size", "4"),
                               ("--grad-accum", "1"), ("--rank", "8"), ("--overflow", "truncate")):
                self.assertEqual(command[command.index(key)+1], value)
            self.assertNotIn("--init-adapter", command)
            self.assertIn("--no-pack", command)
            self.assertEqual(command[command.index("--out")+1], str(self.out / "run" / arm / "adapter"))
        self.assertNotEqual(plan["commands"]["AUTH"], plan["commands"]["DERANGED"])

    def test_stale_root_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.prepare()

    def test_symlink_root_rejected(self):
        link = self.root / "link"
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "canonical"):
            fits.fresh(link / "new")

    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            fits.fresh(self.material / "nested", [self.material])

    def test_changed_material_fails_before_output(self):
        (self.material / "AUTH.json").write_text("changed")
        with self.assertRaisesRegex(ValueError, "pinned"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_tokenizer_pin_changed(self):
        (self.model / "config.json").write_text('{"model_type":"qwen2","changed":true}')
        with self.assertRaisesRegex(ValueError, "tokenizer"):
            self.prepare()

    def test_unbound_tokenizer_addition_rejected(self):
        (self.model / "added_tokens.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "unbound tokenizer"):
            self.prepare()

    def test_source_pin_changed(self):
        (self.source / "organism_v6/train_adapter_v3.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "source"):
            self.prepare()

    def test_model_changed_after_prepare(self):
        self.prepare()
        (self.model / "model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "base/material"):
            fits.verify(self.out)

    def test_sealed_plan_changed(self):
        self.prepare()
        (self.out / "plan.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "sealed"):
            fits.verify(self.out)

    def test_bounds_full_pair_and_cleanup(self):
        now = time.time()
        self.assertEqual(fits.bounds(now, now+4000, now+5000), now+1200)
        for deadline, lease in ((now+1199, now+5000), (now+4000, now+1205), (float("nan"), now+5000)):
            with self.assertRaises(ValueError):
                fits.bounds(now, deadline, lease)

    def test_bad_device(self):
        for device in ("0,1", "", "-1"):
            with self.assertRaisesRegex(ValueError, "device"):
                fits.prepare(self.out, self.material, device, self.deadline, self.lease)

    def test_manifest_exact(self):
        plan = self.prepare()
        for arm in fits.ARMS:
            fits.validate_manifest(plan, arm, self.manifest(plan, arm))

    def test_wrong_steps_tokens_nonfinite_or_warm_rejected(self):
        plan = self.prepare()
        changes = (("steps", 127), ("micro_batches", 129), ("epochs_run", 3), ("nonfinite_batches", 1),
                   ("final_loss", float("nan")), ("warm_start", {}), ("svd_init", {}),
                   ("empty", True), ("train_tokens_seen", 44991))
        for key, value in changes:
            with self.subTest(field=key):
                manifest = self.manifest(plan, "AUTH")
                manifest[key] = value
                with self.assertRaises(ValueError):
                    fits.validate_manifest(plan, "AUTH", manifest)

    def test_any_drops_skips_split_or_wrong_corpus_rejected(self):
        plan = self.prepare()
        for key in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"):
            manifest = self.manifest(plan, "AUTH")
            manifest["truncation"][key] = 1
            with self.assertRaisesRegex(ValueError, "drop/split"):
                fits.validate_manifest(plan, "AUTH", manifest)
        for key, value in (("n_items", 127), ("n_encoded", 127), ("n_skipped_no_target", 1), ("sha256", "bad")):
            manifest = self.manifest(plan, "AUTH")
            manifest["corpus"][key] = value
            with self.assertRaises(ValueError):
                fits.validate_manifest(plan, "AUTH", manifest)

    def test_target_count_and_recipe_rejected(self):
        plan = self.prepare()
        manifest = self.manifest(plan, "AUTH")
        manifest["tokens"]["target"] -= 1
        with self.assertRaisesRegex(ValueError, "token"):
            fits.validate_manifest(plan, "AUTH", manifest)
        manifest = copy.deepcopy(self.manifest(plan, "AUTH"))
        manifest["config"]["lr"] = 3e-4
        with self.assertRaisesRegex(ValueError, "wrong fit"):
            fits.validate_manifest(plan, "AUTH", manifest)

    def adapter_fixture(self, plan, arm):
        stage = self.root / ("fit-" + arm)
        adapter = stage / "adapter"
        adapter.mkdir(parents=True)
        (adapter / "DONE").write_text("ok")
        (adapter / "adapter_model.safetensors").write_bytes(b"fake weights fixture")
        fits.write(adapter / "train_manifest.json", self.manifest(plan, arm))
        fits.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
            target_modules=plan["config"]["target_modules"], bias="none", peft_type="LORA", base_model_name_or_path=plan["model"]))
        return stage

    def test_saved_adapter_and_hash_inventory(self):
        plan = self.prepare()
        stage = self.adapter_fixture(plan, "AUTH")
        result = fits.verify_fit(plan, stage, "AUTH")
        self.assertEqual(result["adapter_files"], self.tree(stage / "adapter"))
        (stage / "adapter/optimizer.pt").write_bytes(b"unexpected state")
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            fits.verify_fit(plan, stage, "AUTH")

    def test_missing_done_and_ambiguous_weights(self):
        plan = self.prepare()
        stage = self.adapter_fixture(plan, "AUTH")
        (stage / "adapter/adapter_model.bin").write_bytes(b"ambiguous")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            fits.verify_fit(plan, stage, "AUTH")
        (stage / "adapter/DONE").unlink()
        with self.assertRaisesRegex(ValueError, "DONE"):
            fits.verify_fit(plan, stage, "AUTH")

    def test_no_launch_authority_or_wrong_device(self):
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            fits.run(self.out)
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}):
            with self.assertRaisesRegex(ValueError, "device"):
                fits.run(self.out, True)

    def fake_execute(self, root, plan, arm, effective):
        stage = root / "run" / arm
        (stage / "worker").mkdir(parents=True)
        adapter = stage / "adapter"
        adapter.mkdir()
        (adapter / "fixture").write_text(arm)
        fits.write(stage / "worker/supervision.json", self.receipt())
        return dict(adapter=str(adapter), adapter_files=self.tree(adapter))

    def test_sequential_two_fits_and_no_readouts(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "2"}), \
                patch.object(fits, "execute_arm", side_effect=self.fake_execute) as execute, \
                patch.object(fits.signal, "setitimer") as timer:
            result = fits.run(self.out, True)
        self.assertEqual([call.args[2] for call in execute.call_args_list], list(fits.ARMS))
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["generation_calls"], 0)
        self.assertLessEqual(timer.call_args_list[0].args[1], 1060)

    def test_partial_first_fit_no_retry_no_second(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "2"}), patch.object(fits, "execute_arm", side_effect=ValueError("failed")) as execute:
            with self.assertRaisesRegex(ValueError, "partial pair"):
                fits.run(self.out, True)
            with self.assertRaisesRegex(ValueError, "fresh"):
                fits.run(self.out, True)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(fits.read(self.out / "run/terminal.json")["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_failed_second_preserves_first(self):
        self.prepare()
        def execute(root, plan, arm, effective):
            if arm == "DERANGED":
                raise ValueError("failed second")
            return self.fake_execute(root, plan, arm, effective)
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "2"}), patch.object(fits, "execute_arm", side_effect=execute):
            with self.assertRaisesRegex(ValueError, "partial pair"):
                fits.run(self.out, True)
        self.assertEqual(list(fits.read(self.out / "run/terminal.json")["arms"]), ["AUTH"])

    def test_missing_supervision_or_failed_release_not_complete(self):
        self.prepare()
        def execute(root, plan, arm, effective):
            result = self.fake_execute(root, plan, arm, effective)
            if arm == "DERANGED":
                (root / "run" / arm / "worker/supervision.json").unlink()
                fits.write(root / "run" / arm / "worker/process.json", {"pid": 42})
            return result
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "2"}), patch.object(fits, "execute_arm", side_effect=execute):
            with self.assertRaisesRegex(ValueError, "partial pair"):
                fits.run(self.out, True)
        self.assertFalse(fits.read(self.out / "run/terminal.json")["release_verified"])

    def test_cpu_clock_includes_startup(self):
        self.prepare()
        clock = time.time()-30, time.monotonic()-30
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "2"}), patch.object(fits, "execute_arm", side_effect=self.fake_execute):
            result = fits.run(self.out, True, clock)
        self.assertGreaterEqual(result["reserved_seconds"], 30)
        self.assertEqual(result["effective_deadline"], clock[0]+1200)

    def test_source_contract_checked_again_after_prepare(self):
        self.prepare()
        with patch.object(fits, "sources", return_value={}):
            with self.assertRaisesRegex(ValueError, "source"):
                fits.verify(self.out)

    def test_execute_uses_one_supervisor_no_generation(self):
        plan = self.prepare()
        (self.out / "run").mkdir()
        observed = []
        def supervise(root, active, worker, command):
            observed.append((root, active, worker, command))
            return self.receipt()
        with patch.object(self.base, "supervise", side_effect=supervise, create=True), \
                patch.object(fits, "verify_fit", return_value={"arm": "AUTH"}), patch.object(fits, "verify", return_value=plan):
            fits.execute_arm(self.out, plan, "AUTH", 9999)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][0], self.out / "run")
        self.assertEqual(observed[0][1]["lease_end"], 9999)
        self.assertEqual(observed[0][3], plan["commands"]["AUTH"])
        self.assertTrue((self.out / "run/AUTH/fit-result.json").is_file())

    def test_saved_adapter_base_mismatch(self):
        plan = self.prepare()
        stage = self.adapter_fixture(plan, "AUTH")
        path = stage / "adapter/adapter_config.json"
        config = fits.read(path)
        config["base_model_name_or_path"] = "wrong-base"
        path.unlink()
        fits.write(path, config)
        with self.assertRaisesRegex(ValueError, "configuration mismatch"):
            fits.verify_fit(plan, stage, "AUTH")


if __name__ == "__main__":
    unittest.main()
