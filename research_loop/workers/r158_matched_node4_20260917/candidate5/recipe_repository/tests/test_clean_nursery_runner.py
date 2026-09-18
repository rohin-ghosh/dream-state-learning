"""Fresh nursery routing using explicitly synthetic model and verifier fixtures."""
import contextlib
import hashlib
import io
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from organism_v6 import model_backend, run_life_v2
from organism_v6 import train_adapter
from organism_v6.gym_backend import Episode
from organism_v6.reasoning_gym_gym import ReasoningGymGym


class NurseryModelFixture:
    initialized = []

    def __init__(self, adapter_path=None):
        self.adapter_path = adapter_path
        self.initialized.append(adapter_path)

    def generation_identity(self):
        return model_backend.configured_generation_identity(model_backend.MODEL, self.adapter_path)

    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        return ['I submitted "1"; the score was 0.50.' if prompt.endswith("NOTE_AFTER:")
                else "ACT: 1" for prompt in prompts]


class VariedNurseryModelFixture(NurseryModelFixture):
    def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
        outputs = []
        for prompt in prompts:
            if prompt.endswith("NOTE_AFTER:"):
                action = re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1]
                outputs.append(f"I submitted {action}; the score was 0.50.")
            else:
                seed = re.findall(r"rg/[a-z0-9_]+/(\d+)", prompt)[-1]
                outputs.append("ACT: " + seed)
        return outputs


class CleanNurseryRunnerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.model = self.root / "model"
        self.model.mkdir()
        payloads = {"config.json": b'{"model_type":"qwen2","architectures":["Qwen2ForCausalLM"]}',
                    "model.safetensors": b"SYNTHETIC SOFTWARE FIXTURE NOT QWEN",
                    "tokenizer.json": b'{"fixture":true}',
                    "tokenizer_config.json": b'{"tokenizer_class":"Qwen2TokenizerFast"}'}
        for name, content in payloads.items():
            (self.model / name).write_bytes(content)
        self.spec = self.root / "pins.json"
        self.spec.write_text(json.dumps(dict(model_id="Qwen/Qwen2.5-7B-Instruct", revision="a" * 40,
                                             files={name: hashlib.sha256(content).hexdigest()
                                                    for name, content in payloads.items()})))
        self.life = self.root / "life"
        self.arguments = ["runner", "--life-dir", str(self.life), "--arm", "B",
                          "--gym", "reasoning_gym", "--rank", "8", "--train-seed", "12",
                          "--episodes", "2", "--sleep-every", "2", "--probe-every", "2",
                          "--budget-ticks", "1", "--wake-batch", "1", "--note-after",
                          "--articulation-gate", "enforce", "--clean-birth-spec", str(self.spec),
                          "--clean-model-dir", str(self.model)]
        NurseryModelFixture.initialized = []

    def run_fixture(self, extra=(), model_class=NurseryModelFixture, varied=False):
        gym = ReasoningGymGym(require_package=False)
        gym.episode_from_id = lambda episode_id, budget=1: Episode(
            episode_id, goal="Submit an answer", metric="verifier score", intro="Synthetic " + episode_id)
        if varied:
            gym.training_schedule = lambda count, seed: [f"rg/mini_sudoku/{1000000 + index}" for index in range(count)]

        def evaluate(episode, action):
            episode.n_attempts += 1
            return .5, f"attempt {episode.n_attempts}: verifier score 0.50 (not accepted; partial credit)"

        gym.evaluate = evaluate
        with patch.object(sys, "argv", self.arguments + list(extra)), \
                patch.object(run_life_v2, "make_gym", return_value=gym), \
                patch.object(run_life_v2, "run_probes_batch"), \
                patch.object(model_backend, "VLLMBackend", model_class), \
                patch.object(model_backend, "MODEL", model_backend.MODEL), \
                patch.dict(os.environ), contextlib.redirect_stdout(io.StringIO()):
            run_life_v2.main()

    def test_actual_slot_gate_routes_reasoning_and_keeps_minimum(self):
        self.run_fixture()
        sleep = self.life / "sleep_0002"
        details = json.loads((sleep / "reasoning_gate_details.json").read_text())
        self.assertTrue(details["training_skipped"])
        self.assertEqual(details["min_items"], 64)
        corpus = json.loads((sleep / "corpus.json").read_text())
        self.assertTrue(corpus["corpus"])
        self.assertTrue(all(text.startswith("Situation rg/") for text in corpus["corpus"]))
        self.assertFalse((sleep / "adapter").exists())
        self.assertTrue((self.life / "LIFE_DONE").exists())

    def test_parent_lesson_is_logged_but_never_admitted(self):
        self.run_fixture(["--artifact-lesson", "lesson"])
        rows = [json.loads(line) for line in (self.life / "ledger.jsonl").read_text().splitlines()]
        teachers = [row for row in rows if row["kind"] == "parent_turn"]
        self.assertTrue(teachers)
        corpus = json.loads((self.life / "sleep_0002" / "corpus.json").read_text())["corpus"]
        self.assertFalse(any(teacher["text"] in item for teacher in teachers for item in corpus))

    def test_unknown_populated_life_fails_before_model_loading(self):
        self.life.mkdir()
        evidence = self.life / "inherited.txt"
        evidence.write_text("preserve me")
        with self.assertRaisesRegex(ValueError, "not empty"):
            self.run_fixture()
        self.assertEqual(evidence.read_text(), "preserve me")
        self.assertEqual(NurseryModelFixture.initialized, [])

    def test_unsupported_influences_fail_before_birth_or_loading(self):
        for extra in (["--parent-url", "http://[REDACTED_HOST]"], ["--neutral-probes"],
                      ["--reflect-every", "1"], ["--rank", "16"],
                      ["--artifact-lesson", "lesson10"], ["--probe-gate"]):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.run_fixture(extra)
            self.assertFalse(self.life.exists())
            self.assertEqual(NurseryModelFixture.initialized, [])

    def test_birth_pin_mismatch_fails_without_model_load(self):
        (self.model / "model.safetensors").write_bytes(b"altered fixture")
        with self.assertRaisesRegex(ValueError, "pin mismatch"):
            self.run_fixture()
        self.assertEqual(NurseryModelFixture.initialized, [])

    def test_strict_verifier_never_invents_zero_for_failures(self):
        gym = ReasoningGymGym(require_package=False, strict_verifier=True)
        episode = Episode("rg/mini_sudoku/10001", goal="Answer", metric="score", intro="fixture")

        def fail(**kwargs):
            raise ValueError("fixture grader error")

        gym._item = lambda family, seed: (SimpleNamespace(score_answer=fail), {})
        with self.assertRaisesRegex(RuntimeError, "no measured outcome"):
            gym.step(episode, "1")
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.subTest(value=value):
                gym._item = lambda family, seed: (SimpleNamespace(score_answer=lambda **kwargs: value), {})
                with self.assertRaisesRegex(RuntimeError, "invalid score"):
                    gym.step(episode, "1")

    def test_legacy_verifier_failure_behavior_is_unchanged(self):
        gym = ReasoningGymGym(require_package=False)

        def fail(**kwargs):
            raise ValueError("fixture grader error")

        gym._item = lambda family, seed: (SimpleNamespace(score_answer=fail), {})
        episode = Episode("rg/mini_sudoku/10001", goal="Answer", metric="score", intro="fixture")
        result = gym.step(episode, "1")
        self.assertEqual(result.score, 0.0)
        self.assertIn("score 0.00", result.text)

    def run_admitted_fixture(self, *, episodes=64, model_class=None, expect_acceptance=True):
        commands = []

        def simulated_training(command, **kwargs):
            commands.append(command)

            def option(name):
                return command[command.index(name) + 1]

            stage = Path(option("--out"))
            stage.mkdir()
            corpus_bytes = Path(option("--corpus")).read_bytes()
            corpus = json.loads(corpus_bytes)
            gate = train_adapter.load_gate_binding(option("--gate-receipt"), option("--expected-gate-sha256"),
                                                   option("--previous-manifest-sha256"), corpus_bytes)
            counts = []
            for text in corpus["corpus"]:
                prefix = train_adapter.child_record_prefix_length(text)
                counts.append(train_adapter.child_label_counts(
                    [(0, 1), (1, 2), (2, prefix + 1), (prefix + 1, prefix + 2)],
                    prefix, [1, 1, 1, 1], [-100, -100, -100, 13]))
            (stage / "adapter_config.json").write_text(json.dumps(dict(
                peft_type="LORA", base_model_name_or_path=model_backend.MODEL,
                r=int(option("--rank")), lora_alpha=2 * int(option("--rank")),
                lora_dropout=0.05, bias="none",
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                "gate_proj", "up_proj", "down_proj"])))
            (stage / "adapter_model.safetensors").write_bytes(b"SIMULATED INTEGRATION WEIGHTS")
            total = len(counts)
            (stage / "train_meta.json").write_text(json.dumps(dict(
                recipe="v1_frozen_child_target_seeded", source_recipe="preschool_records_v1",
                rank=int(option("--rank")), seed=int(option("--seed")), lr=float(option("--lr")),
                deterministic_algorithms=False,
                loss_target="child_body_only", source_corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),
                n_texts=total, epochs=3, steps=48, tokens=12 * total,
                supervised_tokens=3 * total, masked_nonpadding_tokens=9 * total)))
            train_adapter.write_training_receipt(option("--trainer-receipt"), stage, gate,
                                                 option("--expected-gate-sha256"), counts)
            (stage / "DONE").write_text("fixture complete\n")
            return SimpleNamespace(returncode=0)

        with patch.object(run_life_v2.subprocess, "run", side_effect=simulated_training), \
                patch.object(model_backend, "close_backend", return_value=True) as closed:
            self.backend_closes = closed
            self.run_fixture(["--episodes", str(episodes), "--sleep-every", "64", "--probe-every", "64"],
                             model_class=model_class or VariedNurseryModelFixture, varied=True)
        self.assertEqual(len(commands), episodes // 64)
        if not expect_acceptance:
            return
        pinned = self.life / "lineage" / f"sleep_{episodes:04d}" / "adapter"
        self.assertEqual(NurseryModelFixture.initialized[-1], str(pinned))
        self.assertTrue((pinned.parent / "trainer_receipt.json").is_file())
        self.assertTrue((pinned / "DONE").is_file())
        self.assertTrue((pinned.parent / "manifest.json").is_file())

    def test_admitted_fixture_binds_before_reloading_lineage_adapter(self):
        self.run_admitted_fixture()

    def test_selection_intent_is_durable_before_final_done(self):
        original = os.rename
        observed = []

        def check_rename(source, destination, *args, **kwargs):
            if Path(source).name == "CANDIDATE" and Path(destination).name == "DONE":
                directory = Path(source).parent.parent / "canary_selection"
                for name in ("trace.json", "receipt.json", "selected.json"):
                    self.assertTrue((directory / name).is_file())
                    self.assertEqual((directory / name).stat().st_mode & 0o777, 0o444)
                self.assertFalse(Path(destination).exists())
                observed.append(directory)
            return original(source, destination, *args, **kwargs)

        with patch.object(os, "rename", side_effect=check_rename):
            self.run_admitted_fixture()
        self.assertEqual(len(observed), 1)
        manifest = json.loads((self.life / "lineage/sleep_0064/manifest.json").read_bytes())
        trace = next(source for source in manifest["sources"] if source["path"].endswith("/trace.json"))
        selection_paths = {"sleep_0064/adapter/DONE", "sleep_0064/canary_selection/receipt.json",
                           "sleep_0064/canary_selection/selected.json"}
        for artifact in manifest["artifacts"]:
            if artifact["path"] in selection_paths:
                self.assertEqual(artifact["source_sha256"], [trace["sha256"]])
            else:
                self.assertNotIn(trace["sha256"], artifact["source_sha256"])
        self.assertNotIn(trace["sha256"], manifest["trained_corpus"][0]["source_sha256"])
        self.assertTrue(any(call.args[0].adapter_path == str(self.life / "sleep_0064/adapter")
                            for call in self.backend_closes.call_args_list))

    def test_two_sleeps_replay_real_canary_custody(self):
        self.run_admitted_fixture(episodes=128)
        first = self.life / "lineage/sleep_0064"
        second = self.life / "lineage/sleep_0128"
        selected = json.loads((second / "canary_selection/selected.json").read_bytes())
        self.assertEqual(selected["previous_manifest_sha256"], hashlib.sha256((first / "manifest.json").read_bytes()).hexdigest())
        self.assertTrue((second / "ledger.jsonl").read_bytes().startswith((first / "ledger.jsonl").read_bytes()))

    def test_canary_failure_closes_backend_and_never_promotes(self):
        from organism_v6 import nursery_selection_receipt as selection

        with patch.object(selection.SelectionRecorder, "batch", side_effect=RuntimeError("synthetic canary interruption")):
            with self.assertRaisesRegex(RuntimeError, "synthetic canary interruption"):
                self.run_admitted_fixture()
        candidate = self.life / "sleep_0064/adapter"
        self.assertTrue((candidate / "CANDIDATE").exists())
        self.assertFalse((candidate / "DONE").exists())
        self.assertFalse((self.life / "lineage/sleep_0064").exists())
        self.assertTrue(any(call.args[0].adapter_path == str(candidate) for call in self.backend_closes.call_args_list))

    def test_changed_candidate_after_receipt_blocks_final_marker(self):
        from organism_v6 import nursery_selection_receipt as selection

        write = selection.SelectionRecorder.write

        def change_adapter(recorder, *args, **kwargs):
            binding = write(recorder, *args, **kwargs)
            (recorder.adapter_dir / "adapter_model.safetensors").write_bytes(b"changed after selection")
            return binding

        with patch.object(selection.SelectionRecorder, "write", change_adapter):
            with self.assertRaisesRegex(selection.SelectionReceiptError, "adapter/config identity mismatch"):
                self.run_admitted_fixture()
        self.assertTrue((self.life / "sleep_0064/canary_selection/selected.json").is_file())
        self.assertTrue((self.life / "sleep_0064/adapter/CANDIDATE").exists())
        self.assertFalse((self.life / "sleep_0064/adapter/DONE").exists())

    def test_selected_intent_write_failure_closes_backend_without_done(self):
        from organism_v6 import nursery_selection_receipt as selection

        write = selection.custody._write

        def interrupt(path, content):
            if Path(path).name == "selected.json":
                raise OSError("synthetic durable selection interruption")
            return write(path, content)

        with patch.object(selection.custody, "_write", side_effect=interrupt):
            with self.assertRaisesRegex(selection.SelectionReceiptError, "synthetic durable selection interruption"):
                self.run_admitted_fixture()
        sleep = self.life / "sleep_0064"
        self.assertTrue((sleep / "canary_selection/receipt.json").is_file())
        self.assertFalse((sleep / "canary_selection/selected.json").exists())
        self.assertTrue((sleep / "adapter/CANDIDATE").exists())
        self.assertFalse((sleep / "adapter/DONE").exists())
        self.assertTrue(any(call.args[0].adapter_path == str(sleep / "adapter")
                            for call in self.backend_closes.call_args_list))

    def test_backend_close_failure_blocks_clean_final_marker(self):
        from organism_v6 import nursery_selection_receipt as selection

        write = selection.SelectionRecorder.write

        def fail_close(recorder, *args, **kwargs):
            binding = write(recorder, *args, **kwargs)
            self.backend_closes.return_value = False
            return binding

        with patch.object(selection.SelectionRecorder, "write", fail_close):
            with self.assertRaisesRegex(RuntimeError, "candidate backend did not close"):
                self.run_admitted_fixture()
        self.assertTrue((self.life / "sleep_0064/canary_selection/selected.json").is_file())
        self.assertTrue((self.life / "sleep_0064/adapter/CANDIDATE").exists())
        self.assertFalse((self.life / "sleep_0064/adapter/DONE").exists())

    def test_actual_negative_canary_keeps_rejection_evidence(self):
        class NegativeCanary(VariedNurseryModelFixture):
            def batch(self, prompts, max_tokens=400, temperature=0.7, seeds=None):
                if self.adapter_path is not None:
                    return ["### ACT: not canonical" for prompt in prompts]
                return super().batch(prompts, max_tokens, temperature, seeds)

        self.run_admitted_fixture(model_class=NegativeCanary, expect_acceptance=False)
        sleep = self.life / "sleep_0064"
        decision = json.loads((sleep / "canary_selection/receipt.json").read_bytes())
        self.assertEqual(decision["decision"], "REJECTED_CANARY")
        self.assertEqual(decision["rate"], 0.0)
        self.assertTrue((sleep / "adapter/REJECTED_CANARY").exists())
        self.assertFalse((self.life / "lineage/sleep_0064").exists())

    def test_backend_identity_mismatch_fails_before_waking(self):
        original = NurseryModelFixture.generation_identity

        def mismatched_identity(backend):
            identity = original(backend)
            identity["model_input"] = "/tmp/other-unpinned-base"
            return identity

        with patch.object(NurseryModelFixture, "generation_identity", mismatched_identity):
            with self.assertRaisesRegex(ValueError, "clean backend identity mismatch: model_input"):
                self.run_fixture()
        self.assertFalse((self.life / "LIFE_DONE").exists())
        ledger = self.life / "ledger.jsonl"
        self.assertTrue(not ledger.exists() or not ledger.read_text().strip())

    def test_candidate_backend_mismatch_fails_before_acceptance(self):
        original = NurseryModelFixture.generation_identity

        def mismatched_identity(backend):
            identity = original(backend)
            if backend.adapter_path is not None:
                identity["adapter_files"] = {}
            return identity

        with patch.object(NurseryModelFixture, "generation_identity", mismatched_identity):
            with self.assertRaisesRegex(ValueError, "clean backend identity mismatch: adapter_files"):
                self.run_admitted_fixture()
        self.assertFalse((self.life / "sleep_0064/adapter/DONE").exists())
        self.assertFalse((self.life / "lineage/sleep_0064").exists())

    def test_receipted_wrong_training_controls_fail_before_promotion(self):
        original = train_adapter.write_training_receipt

        def mismatched_training(receipt_path, adapter_dir, *args, **kwargs):
            config_path = Path(adapter_dir) / "adapter_config.json"
            config = json.loads(config_path.read_text())
            config["r"] = 16
            config_path.write_text(json.dumps(config))
            metadata_path = Path(adapter_dir) / "train_meta.json"
            metadata = json.loads(metadata_path.read_text())
            metadata.update(rank=16, seed=99, lr=0.009)
            metadata_path.write_text(json.dumps(metadata))
            return original(receipt_path, adapter_dir, *args, **kwargs)

        with patch.object(train_adapter, "write_training_receipt", mismatched_training):
            with self.assertRaisesRegex(ValueError, "clean training config mismatch: r"):
                self.run_admitted_fixture()
        self.assertTrue((self.life / "sleep_0064/adapter.train/DONE").exists())
        self.assertFalse((self.life / "sleep_0064/adapter").exists())
        self.assertFalse((self.life / "lineage/sleep_0064").exists())

    def test_training_metadata_and_recipe_fields_are_independently_checked(self):
        config = dict(peft_type="LORA", r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
        metadata = dict(rank=8, seed=12, lr=0.0001, epochs=3,
                        recipe="v1_frozen_child_target_seeded",
                        source_recipe="preschool_records_v1", loss_target="child_body_only",
                        deterministic_algorithms=False)
        adapter = self.model.parent / "training_controls_fixture"
        adapter.mkdir()
        for filename, values in (("adapter_config.json", config), ("train_meta.json", metadata)):
            (adapter / filename).write_text(json.dumps(values))
        run_life_v2.validate_clean_training(adapter, rank=8, seed=12, lr=0.0001)
        for filename, values in (("adapter_config.json", config), ("train_meta.json", metadata)):
            for field in values:
                with self.subTest(filename=filename, field=field):
                    altered = dict(values)
                    del altered[field]
                    (adapter / filename).write_text(json.dumps(altered))
                    with self.assertRaisesRegex(ValueError, "clean training .* mismatch"):
                        run_life_v2.validate_clean_training(adapter, rank=8, seed=12, lr=0.0001)
                    (adapter / filename).write_text(json.dumps(values))

    def test_backend_adapter_path_is_independently_checked(self):
        identity = model_backend.configured_generation_identity(str(self.model), None)
        identity["adapter_input"] = "/tmp/unselected-adapter"
        backend = SimpleNamespace(generation_identity=lambda: identity)
        with self.assertRaisesRegex(ValueError, "clean backend identity mismatch: adapter_input"):
            run_life_v2.validate_clean_backend(backend, str(self.model), None)


if __name__ == "__main__":
    unittest.main()
