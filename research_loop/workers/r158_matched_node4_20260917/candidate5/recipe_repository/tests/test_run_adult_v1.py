"""Synthetic CPU boundaries; real nursery/control/admission/masking/canary helpers."""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_clean_nursery_runner as nursery_fixture
from organism_v6 import run_adult_v1 as runner
from organism_v6 import train_adapter
from organism_v6.gym_backend import Episode
from organism_v6.model_backend import configured_generation_identity
from organism_v6.reasoning_gym_gym import ReasoningGymGym


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CPUModel:
    def __init__(self, model, adapter, owner):
        self.model, self.adapter, self.owner = model, adapter, owner

    def generation_identity(self):
        identity = configured_generation_identity(self.model, self.adapter)
        if self.owner.wrong_identity:
            identity["model_input"] = "WRONG_MODEL"
        return identity

    def batch(self, prompts, max_tokens=400, temperature=.7, seeds=None):
        self.owner.prompts.extend(prompts)
        is_candidate = Path(self.adapter).name == "adapter" and "adult" in self.adapter
        if is_candidate and self.owner.short_canary:
            return ["ACT: 1"]
        outputs = []
        for prompt in prompts:
            if is_candidate and self.owner.mutate_candidate:
                (Path(self.adapter).parent / "corpus.json").chmod(0o644)
                with (Path(self.adapter).parent / "corpus.json").open("a") as target:
                    target.write(" ")
            if is_candidate and self.owner.reject:
                outputs.append("no canonical action")
            elif prompt.endswith("NOTE_AFTER:"):
                action = re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1]
                outputs.append("I will try later." if self.owner.invalid_records else
                               f"I submitted {action}; the score was 0.50.")
            else:
                seed = re.findall(r"rg/[a-z0-9_]+/(\d+)", prompt)[-1]
                outputs.append("ACT: " + seed)
        return outputs


class AdultRunnerTests(unittest.TestCase):
    def setUp(self):
        fixture = nursery_fixture.CleanNurseryRunnerTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.run_admitted_fixture()
        self.root = fixture.root
        self.bundle = fixture.life / "lineage"
        checkpoint = self.bundle / "sleep_0064"
        model = self.bundle / "birth/model"
        self.spec = runner.AdultRunSpec(
            life_dir=str(self.root / "adult"), mode="running", lineage_root=str(self.bundle),
            manifest_path="sleep_0064/manifest.json", expected_manifest_sha256=digest(checkpoint / "manifest.json"),
            initial_adapter_dir=str(checkpoint / "adapter"), initial_corpus_path=str(checkpoint / "corpus.json"),
            model_dir=str(model), expected_model_id="Qwen/Qwen2.5-7B-Instruct",
            expected_model_files={path.name: digest(path) for path in model.iterdir()},
            episode_ids=[f"rg/mini_sudoku/{1001000 + index}" for index in range(64)],
            seed=9, train_seed=23, sleep_every=64, budget_ticks=1, wake_batch=64)
        self.gym = ReasoningGymGym(require_package=False, strict_verifier=True)
        self.gym.episode_from_id = lambda episode_id, budget: Episode(
            episode_id, goal="Submit the numeric answer.", metric="verifier score", intro=episode_id)
        self.gym._item = lambda family, seed: (self, {"question": "CPU puzzle", "answer": "sealed"})
        self.loaded, self.closed, self.prompts, self.requests = [], [], [], []
        self.wrong_identity = self.reject = self.mutate_candidate = self.invalid_records = False
        self.bad_receipt = self.omit_receipt = False
        self.short_canary = False

    def score_answer(self, answer, entry):
        return .5

    @contextmanager
    def backend(self, model_dir, adapter):
        self.loaded.append(adapter)
        try:
            yield CPUModel(model_dir, adapter, self)
        finally:
            self.closed.append(adapter)

    def trainer(self, request):
        self.requests.append(request)
        stage = Path(request.output_dir)
        stage.mkdir()
        corpus_bytes = Path(request.corpus_path).read_bytes()
        corpus = json.loads(corpus_bytes)
        gate = train_adapter.load_gate_binding(request.gate_receipt_path, request.expected_gate_sha256,
                                               request.previous_manifest_sha256, corpus_bytes)
        counts = []
        for text in corpus["corpus"]:
            prefix = train_adapter.child_record_prefix_length(text)
            offsets = [(0, 1), (1, 2), (2, prefix), (prefix, prefix + 1)]
            mask = train_adapter.child_target_mask(offsets, prefix, [1] * 4)
            labels = [17 if supervised else -100 for supervised in mask]
            counts.append(train_adapter.child_label_counts(offsets, prefix, [1] * 4, labels))
        (stage / "adapter_config.json").write_text(json.dumps(dict(
            peft_type="LORA", base_model_name_or_path=request.model_dir, r=request.rank,
            lora_alpha=2 * request.rank, lora_dropout=.05, bias="none",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])))
        (stage / "adapter_model.safetensors").write_bytes(b"CPU SYNTHETIC ADULT WEIGHTS")
        total = len(counts)
        (stage / "train_meta.json").write_text(json.dumps(dict(
            recipe="v1_frozen_child_target_seeded", source_recipe="preschool_records_v1",
            rank=request.rank, seed=request.seed, lr=request.lr, deterministic_algorithms=False,
            loss_target="child_body_only", source_corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),
            n_texts=total, epochs=3, steps=3, tokens=12 * total,
            supervised_tokens=3 * total, masked_nonpadding_tokens=9 * total)))
        if not self.omit_receipt:
            train_adapter.write_training_receipt(request.trainer_receipt_path, stage, gate,
                                                 request.expected_gate_sha256, counts)
        if self.bad_receipt:
            receipt = json.loads(Path(request.trainer_receipt_path).read_text())
            receipt["rows"][0]["supervised_prefix_tokens"] = 1
            Path(request.trainer_receipt_path).write_text(json.dumps(receipt))
        (stage / "DONE").write_text("synthetic completed trainer\n")

    def run_fixture(self, spec=None):
        return runner.run_adult(spec or self.spec, gym=self.gym,
                                backend_factory=self.backend, trainer=self.trainer)

    def test_running_two_sleeps_replay_and_latest_reload(self):
        spec = replace(self.spec, episode_ids=[f"rg/mini_sudoku/{1001000 + index}" for index in range(128)])
        result = self.run_fixture(spec)
        self.assertTrue(all(item["promoted_adapter"] for item in result["checkpoints"]))
        self.assertEqual(self.loaded[2], result["checkpoints"][0]["promoted_adapter"])
        self.assertEqual(self.loaded[-1], result["selected_adapter"])
        self.assertEqual(self.loaded, self.closed)
        self.assertEqual(len(self.requests), 2)
        life = Path(spec.life_dir)
        initial = json.loads(Path(spec.initial_corpus_path).read_text())["corpus"]
        for checkpoint, count in ((64, 128), (128, 192)):
            sleep = life / f"sleep_{checkpoint:04d}"
            corpus = json.loads((sleep / "corpus.json").read_text())["corpus"]
            self.assertEqual(corpus[:64], initial)
            self.assertEqual(len(corpus), count)
            self.assertTrue((sleep / "adapter/CANDIDATE").exists())
            self.assertFalse((sleep / "adapter/DONE").exists())
            receipt = json.loads((sleep / "canary_selection/receipt.json").read_text())
            self.assertEqual(receipt["total"], 12)
            self.assertEqual(receipt["parse_ok"], 12)
        rows = [json.loads(line) for line in (life / "ledger.jsonl").read_text().splitlines()]
        self.assertFalse(any(row["kind"] == "parent_turn" for row in rows))
        self.assertTrue(all(row.get("episode_id") in spec.episode_ids for row in rows))
        self.assertFalse((life / "lineage").exists())
        self.assertFalse((life / "sleep_0000").exists())

    def test_shadow_same_training_no_waking_change(self):
        running = self.run_fixture()
        shadow_spec = replace(self.spec, mode="shadow", life_dir=str(self.root / "adult_shadow"))
        shadow = self.run_fixture(shadow_spec)
        self.assertTrue(shadow["checkpoints"][0]["accepted"])
        self.assertIsNone(shadow["checkpoints"][0]["promoted_adapter"])
        self.assertEqual(shadow["selected_adapter"], self.spec.initial_adapter_dir)
        self.assertNotEqual(running["selected_adapter"], shadow["selected_adapter"])
        self.assertEqual(Path(self.requests[0].corpus_path).read_bytes(), Path(self.requests[1].corpus_path).read_bytes())
        for request in self.requests:
            self.assertEqual((request.rank, request.epochs, request.seed, request.lr), (8, 3, 23, 1e-4))

    def test_rejected_canary_preserves_initial(self):
        self.reject = True
        result = self.run_fixture()
        self.assertEqual(result["selected_adapter"], self.spec.initial_adapter_dir)
        self.assertFalse(result["checkpoints"][0]["accepted"])
        self.assertEqual(result["checkpoints"][0]["reason"], "CANARY")

    def test_wrong_identity_before_any_training(self):
        self.wrong_identity = True
        with self.assertRaisesRegex(ValueError, "backend identity"):
            self.run_fixture()
        self.assertFalse(self.requests)

    def test_changed_candidate_never_promotes(self):
        self.mutate_candidate = True
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            self.run_fixture()
        self.assertFalse(list((Path(self.spec.life_dir) / "adult_control/decisions").iterdir()))

    def test_real_receipt_required_and_prefix_supervision_rejected(self):
        for index, flag in enumerate(("omit_receipt", "bad_receipt")):
            setattr(self, flag, True)
            spec = replace(self.spec, life_dir=str(self.root / f"adult_invalid_{index}"))
            with self.subTest(flag=flag), self.assertRaises((ValueError, OSError)):
                self.run_fixture(spec)
            setattr(self, flag, False)
            self.assertFalse((Path(spec.life_dir) / "sleep_0064/adapter").exists())

    def test_invalid_records_skip_without_lowering_gate(self):
        self.invalid_records = True
        result = self.run_fixture()
        self.assertEqual(result["checkpoints"][0]["status"], "SKIPPED_INSUFFICIENT_RECORDS")
        self.assertEqual(result["selected_adapter"], self.spec.initial_adapter_dir)
        self.assertFalse(self.requests)

    def test_external_pins_parent_options_and_holdout_fail_closed(self):
        for change in (dict(expected_manifest_sha256="0" * 64), dict(expected_model_files={}),
                       dict(expected_model_id="other"), dict(episode_ids=self.gym.canary_set()),
                       dict(min_items=1), dict(train_seed=None)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.run_fixture(replace(self.spec, **change))
        with self.assertRaises(TypeError):
            runner.AdultRunSpec(**(runner.asdict(self.spec) | {"parent_url": "forbidden"}))
        self.assertFalse(self.loaded)

    def test_existing_life_is_never_overwritten(self):
        life = Path(self.spec.life_dir)
        life.mkdir()
        (life / "sentinel").write_text("preserve")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.run_fixture()
        self.assertEqual((life / "sentinel").read_text(), "preserve")
        self.assertFalse(self.loaded)

    def test_unsupported_gym_stops_before_loading(self):
        self.gym.strict_verifier = False
        with self.assertRaises(runner.UnsupportedAdultInterface):
            self.run_fixture()
        self.assertFalse(self.loaded)

    def test_short_canary_cannot_pass_on_smaller_denominator(self):
        self.short_canary = True
        with self.assertRaisesRegex(ValueError, "incomplete generation"):
            self.run_fixture()
        self.assertFalse(list((Path(self.spec.life_dir) / "adult_control/decisions").iterdir()))

    def test_fresh_context_has_no_inherited_records(self):
        spec = replace(self.spec, episode_ids=self.spec.episode_ids[:1])
        self.run_fixture(spec)
        for prompt in self.prompts:
            self.assertTrue(prompt.startswith("=== YOU ===\n" + self.gym.birth_prompt().strip()))
            self.assertNotIn("My measured action record:", prompt)
            self.assertNotIn("rg/mini_sudoku/1000000", prompt)
        self.assertEqual(runner._AdultLedger(str(Path(spec.life_dir) / "ledger.jsonl")).recall("anything"), [])


class LocalTrainerProcessTests(unittest.TestCase):
    """Non-material process-isolation repair; no trainer or GPU process executes."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sleep = self.root / "sleep_0064"
        self.sleep.mkdir()
        self.request = runner.TrainingRequest(
            model_dir=str(self.root / "pinned model"),
            corpus_path=str(self.sleep / "corpus.json"),
            output_dir=str(self.sleep / "adapter.train"),
            gate_receipt_path=str(self.sleep / "gate_receipt.json"),
            expected_gate_sha256="a" * 64, previous_manifest_sha256="b" * 64,
            trainer_receipt_path=str(self.sleep / "trainer_receipt.json"),
            rank=8, seed=23, lr=1e-4, epochs=3)
        self.log_path = self.sleep / "training.log"

    def test_exact_command_environment_and_bounded_log(self):
        parent_environment = dict(V6_MODEL="parent-model", HF_HUB_OFFLINE="0",
                                  TRANSFORMERS_OFFLINE="0", RETAIN_SETTING="unchanged")
        original_args = sys.argv

        def simulated_process(command, **kwargs):
            self.assertIs(sys.argv, original_args)
            self.assertEqual(dict(os.environ), parent_environment)
            self.assertEqual(os.fstat(kwargs["stdout"].fileno()).st_ino, self.log_path.stat().st_ino)
            kwargs["stdout"].write(b"trainer stdout\ntrainer stderr\n")
            return subprocess.CompletedProcess(command, 0)

        with patch.dict(os.environ, parent_environment, clear=True), \
                patch.object(runner.subprocess, "run", side_effect=simulated_process) as process, \
                patch.object(train_adapter, "main") as inprocess:
            runner.local_trainer(self.request)
            self.assertEqual(dict(os.environ), parent_environment)
            self.assertIs(sys.argv, original_args)
            inprocess.assert_not_called()
        command = process.call_args.args[0]
        self.assertEqual(command, [
            sys.executable, "-B", "-m", "organism_v6.train_adapter",
            "--corpus", self.request.corpus_path, "--out", self.request.output_dir,
            "--rank", "8", "--epochs", "3", "--lr", "0.0001", "--seed", "23",
            "--gate-receipt", self.request.gate_receipt_path,
            "--expected-gate-sha256", self.request.expected_gate_sha256,
            "--previous-manifest-sha256", self.request.previous_manifest_sha256,
            "--trainer-receipt", self.request.trainer_receipt_path])
        options = process.call_args.kwargs
        self.assertEqual(options["env"], parent_environment | dict(
            V6_MODEL=self.request.model_dir, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1"))
        self.assertEqual(options["cwd"], str(Path(runner.__file__).resolve().parents[1]))
        self.assertIs(options["check"], True)
        self.assertEqual(options["stderr"], subprocess.STDOUT)
        self.assertTrue(options["stdout"].closed)
        self.assertNotIn("capture_output", options)
        self.assertNotIn("shell", options)
        self.assertEqual(self.log_path.read_bytes(), b"trainer stdout\ntrainer stderr\n")
        self.assertEqual(self.log_path.stat().st_mode & 0o222, 0)
        self.assertEqual(set(self.sleep.iterdir()), {self.log_path})

    def test_trainer_error_propagates_and_retains_log(self):
        failure = subprocess.CalledProcessError(7, ["synthetic trainer"])

        def failed_process(command, **kwargs):
            kwargs["stdout"].write(b"synthetic training failure\n")
            raise failure

        original_environment, original_args = dict(os.environ), sys.argv
        with patch.object(runner.subprocess, "run", side_effect=failed_process), \
                patch.object(train_adapter, "main") as inprocess:
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                runner.local_trainer(self.request)
            self.assertIs(raised.exception, failure)
            inprocess.assert_not_called()
        self.assertEqual(dict(os.environ), original_environment)
        self.assertIs(sys.argv, original_args)
        self.assertEqual(self.log_path.read_bytes(), b"synthetic training failure\n")
        self.assertEqual(self.log_path.stat().st_mode & 0o222, 0)
        with patch.object(runner.subprocess, "run") as retry:
            with self.assertRaises(FileExistsError):
                runner.local_trainer(self.request)
            retry.assert_not_called()

    def test_existing_log_is_not_overwritten(self):
        self.log_path.write_bytes(b"prior evidence")
        with patch.object(runner.subprocess, "run") as process:
            with self.assertRaises(FileExistsError):
                runner.local_trainer(self.request)
            process.assert_not_called()
        self.assertEqual(self.log_path.read_bytes(), b"prior evidence")

    def test_symlink_log_cannot_escape_sleep(self):
        outside = self.root / "outside.log"
        outside.write_bytes(b"preserve")
        self.log_path.symlink_to(outside)
        with patch.object(runner.subprocess, "run") as process:
            with self.assertRaises(FileExistsError):
                runner.local_trainer(self.request)
            process.assert_not_called()
        self.assertEqual(outside.read_bytes(), b"preserve")

    def test_spawn_error_preserves_parent_state_and_fresh_log(self):
        failure = OSError("synthetic spawn failure")
        original_environment, original_args = dict(os.environ), sys.argv
        with patch.object(runner.subprocess, "run", side_effect=failure), \
                patch.object(train_adapter, "main") as inprocess:
            with self.assertRaises(OSError) as raised:
                runner.local_trainer(self.request)
            self.assertIs(raised.exception, failure)
            inprocess.assert_not_called()
        self.assertEqual(dict(os.environ), original_environment)
        self.assertIs(sys.argv, original_args)
        self.assertEqual(self.log_path.read_bytes(), b"")
        self.assertEqual(self.log_path.stat().st_mode & 0o222, 0)


if __name__ == "__main__":
    unittest.main()
