"""Synthetic CPU formations and real probe evaluator; no GPU/training claims."""
from contextlib import contextmanager
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from organism_v6 import parent_material_pipeline as pipeline
from organism_v6 import parent_material_write as writer
from organism_v6 import parent_material_diagnostic as formation
from organism_v6 import run_reasoning_neutral as neutral
from organism_v6.reasoning_gym_gym import BOOTSTRAP_PATH
from organism_v6.reasoning_neutral_probe import run_probe
import test_parent_material_write as write_fixtures
from test_parent_material_write import MaterialModel, EndingGym, ShortDiagnosticDriver, OffsetTokenizer
from test_reasoning_neutral_probe import FixtureBackend, FixtureGym


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.fixture = write_fixtures.ParentMaterialWriteTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "pipeline"
        self.lesson = self.fixture.formation
        self.sham = self.make_sham()
        self.devices = dict(lesson="2", sham="3")
        self.calls = []
        self.worker_calls = []

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temp.cleanup()

    def make_sham(self, unique=128, name="sham"):
        model = MaterialModel(str(self.fixture.fixture.model_dir), unique=unique)

        @contextmanager
        def backend(model_path):
            yield model

        config = replace(self.fixture.fixture.config, mode="sham", out=str(self.fixture.root / name))
        with patch.object(formation, "DiagnosticDriver", ShortDiagnosticDriver):
            formation.run(config, gym=EndingGym(), backend_factory=backend)
        return Path(config.out)

    def prepare(self):
        with patch.object(writer, "_load_tokenizer", return_value=OffsetTokenizer()):
            self.plan = pipeline.prepare_pipeline(self.fixture.root, self.lesson, self.sham,
                                                  self.output, devices=self.devices)
        return self.plan

    def popen(self, command, **kwargs):
        self.calls.append((command, kwargs))
        adapter = Path(command[command.index("--out") + 1])
        arm = adapter.name
        adapter.mkdir()
        metadata = dict(self.plan["reports"][arm]["metadata_equals"], final_loss=0.75)
        (adapter / "train_meta.json").write_text(json.dumps(metadata))
        (adapter / "adapter_config.json").write_text('{}')
        (adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC CPU ADAPTER; NO FIT EXECUTED")
        (adapter / "DONE").write_text("ok\n")
        return Mock(pid=99999999, wait=Mock(return_value=0))

    def worker(self, command, **kwargs):
        self.worker_calls.append((command, kwargs, os.environ.copy()))
        spec_path = Path(command[command.index("--spec") + 1])
        digest = command[command.index("--spec-sha256") + 1]
        spec = neutral.read_spec(spec_path, digest)
        condition = command[command.index("--condition") + 1]
        output = Path(spec["output_dir"])
        gym = FixtureGym()
        gym._bootstrap = Path(BOOTSTRAP_PATH).read_text()
        gym.gate_families = ["n_queens", "tower_of_hanoi"]
        options = {name: spec[name] for name in neutral.PROBE_FIELDS}
        if condition == "off":
            options.update(adapter_path=None, expected_adapter_hashes={})
        model = FixtureBackend(options["model_path"], options["adapter_path"])
        run_probe(model, gym, output_dir=output / condition, **options)
        pid = os.getpid() + (100 if condition == "off" else 200)
        neutral._write(output / (condition + "_WORKER_DONE.json"), dict(
            evidence_label="EVALUATION_ONLY", condition=condition, spec_sha256=digest,
            pid=pid, device=kwargs["device"], multiprocessing="spawn",
            results_sha256=neutral._digest(output / condition / "results.json"),
            manifest_sha256=neutral._digest(output / condition / "manifest.json")))
        self.assertTrue(all("LESSON" not in prompt and "teaching_dose" not in prompt
                            for prompts, _, _ in model.calls for prompt in prompts))
        return pid

    def execute(self, popen=None, worker=None, occupancy=None):
        with patch.object(neutral, "run_worker", side_effect=worker or self.worker):
            return pipeline.execute_pipeline(self.output, allow_gpu=True,
                popen=popen or self.popen, occupancy=occupancy or (lambda device: True))

    def test_real_preparation_and_probe_evaluator_positive(self):
        self.prepare()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "9", "PYTHONPATH": "/bad",
                                    "PYTHONHOME": "/bad", "V6_MODEL": "/bad", "LD_PRELOAD": "/bad"}):
            result = self.execute()
            self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "9")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(self.worker_calls), 4)
        self.assertEqual(result["episode_ids"], ["rg/n_queens/2000001", "rg/n_queens/2000002",
                                                  "rg/tower_of_hanoi/2000001", "rg/tower_of_hanoi/2000002"])
        for arm, (command, options) in zip(pipeline.ARMS, self.calls):
            prepared = writer._read(self.output / "preparations" / arm / "training_command.json")
            self.assertEqual(command, prepared["argv"])
            self.assertFalse(set(prepared["omitted_arguments"]) & set(command))
            self.assertTrue(options["start_new_session"])
            self.assertIs(options["shell"], False)
            self.assertEqual(options["cwd"], str(pipeline.ROOT))
            self.assertEqual(options["env"]["CUDA_VISIBLE_DEVICES"], self.devices[arm])
            self.assertEqual(options["env"]["PYTHONPATH"], str(pipeline.ROOT))
            self.assertEqual(options["env"]["HF_HUB_OFFLINE"], "1")
            self.assertNotIn("PYTHONHOME", options["env"])
            self.assertNotIn("LD_PRELOAD", options["env"])
            self.assertEqual(result["training"][arm]["metadata"]["steps"], 48)
            self.assertIn("adapter_model.safetensors", result["training"][arm]["adapter_hashes"])
            for condition in ("off", "on"):
                self.assertEqual(len(result["probes"][arm][condition]["episodes"]), 4)
        for _, options, environment in self.worker_calls:
            self.assertEqual(options["timeout"], 3600)
            self.assertEqual(environment["V6_MODEL"], self.plan["model_path"])
            self.assertNotIn("PYTHONHOME", environment)
        self.assertFalse(result["clean_lineage"])
        self.assertNotIn("H1_success", result)
        self.assertFalse((self.output / "PARTIAL.json").exists())

    def test_original_formations_in_fresh_source_only_checkout(self):
        checkout = self.root / "archive_checkout"
        checkout.mkdir()
        shutil.copytree(pipeline.ROOT / "organism_v6", checkout / "organism_v6",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (checkout / "tests").mkdir()
        for name in ("test_parent_material_pipeline.py", "test_parent_material_write.py",
                     "test_parent_material_diagnostic.py", "test_reasoning_neutral_probe.py"):
            shutil.copy2(pipeline.ROOT / "tests" / name, checkout / "tests" / name)
        originals = {path: writer._hash(path / "artifact_hashes.json") for path in (self.lesson, self.sham)}
        code = (
            "import sys; from pathlib import Path; from test_parent_material_pipeline import PipelineTests; "
            "from organism_v6.neutral_pair_custody import source_snapshot; "
            "case=PipelineTests(); case.setUp(); "
            "case.fixture.root=Path(sys.argv[1]); case.lesson=Path(sys.argv[2]); case.sham=Path(sys.argv[3]); "
            "case.test_real_preparation_and_probe_evaluator_positive(); "
            "assert source_snapshot()['source_root']==str(Path.cwd()); "
            "case.doCleanups(); print('RELOCATED_PRODUCER_AND_PROBE_OK')")
        environment = pipeline._environment(self.fixture.fixture.model_dir, "0")
        environment["CUDA_VISIBLE_DEVICES"] = ""
        environment["PYTHONPATH"] = str(checkout / "tests") + os.pathsep + str(checkout)
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.fixture.root),
                                 str(self.lesson), str(self.sham)], cwd=checkout, env=environment,
                                capture_output=True, text=True, timeout=90, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RELOCATED_PRODUCER_AND_PROBE_OK", result.stdout)
        self.assertEqual(originals, {path: writer._hash(path / "artifact_hashes.json") for path in originals})

    def test_paired_short_count_no_fits_or_probe(self):
        self.sham = self.make_sham(unique=63, name="short")
        plan = self.prepare()
        self.assertEqual(plan["status"], "PAIRED_SKIP_INSUFFICIENT_MATERIAL")
        with patch.object(pipeline, "run_training", side_effect=AssertionError("must not fit")):
            result = self.execute()
        self.assertFalse(result["fits_started"])
        self.assertFalse(self.calls)
        self.assertFalse((self.output / "EXECUTION_STARTED.json").exists())

    def test_malformed_training_metadata_retains_partial_no_second_fit(self):
        self.prepare()

        def malformed(command, **kwargs):
            process = self.popen(command, **kwargs)
            path = Path(command[command.index("--out") + 1]) / "train_meta.json"
            metadata = writer._read(path)
            metadata["steps"] = 47
            path.write_text(json.dumps(metadata))
            return process

        with self.assertRaisesRegex(ValueError, "metadata mismatch"):
            self.execute(popen=malformed)
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(self.worker_calls)
        self.assertEqual(writer._read(self.output / "PARTIAL.json")["stage"], "lesson_train")
        self.assertFalse((self.output / "results.json").exists())

    def test_nonfinite_loss_and_missing_adapter_reject(self):
        self.prepare()
        command = writer._read(self.output / "preparations/lesson/training_command.json")
        self.popen(command["argv"])
        report = self.plan["reports"]["lesson"]
        metadata_path = Path(report["adapter_dir"]) / "train_meta.json"
        metadata = writer._read(metadata_path)
        metadata["final_loss"] = "NaN"
        metadata_path.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            pipeline._training_result(report)
        metadata["final_loss"] = 1.0
        metadata_path.write_text(json.dumps(metadata))
        (Path(report["adapter_dir"]) / "adapter_model.safetensors").unlink()
        with self.assertRaisesRegex(ValueError, "missing adapter"):
            pipeline._training_result(report)

    def test_missing_probe_output_rejects_partial(self):
        self.prepare()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.execute(worker=lambda *args, **kwargs: 999999)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(writer._read(self.output / "PARTIAL.json")["stage"], "lesson_probe")
        self.assertFalse((self.output / "results.json").exists())

    def test_prior_arm_adapter_mutation_rejects_final_aggregation(self):
        self.prepare()

        def mutate(command, **kwargs):
            pid = self.worker(command, **kwargs)
            if kwargs["log_path"].parent.name == "sham":
                (self.output / "adapters/lesson/adapter_model.safetensors").write_bytes(b"CHANGED")
            return pid

        with self.assertRaisesRegex(ValueError, "adapter changed"):
            self.execute(worker=mutate)
        self.assertFalse((self.output / "results.json").exists())

    def test_training_timeout_records_partial_and_no_partner_fit(self):
        self.prepare()

        def timeout(command, **kwargs):
            process = self.popen(command, **kwargs)
            process.wait.side_effect = [subprocess.TimeoutExpired(command, 600), 0]
            return process

        with self.assertRaises(subprocess.TimeoutExpired):
            self.execute(popen=timeout)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(writer._read(self.output / "logs/lesson_train.cleanup.json")["owned_group_empty"])
        self.assertEqual(writer._read(self.output / "PARTIAL.json")["stage"], "lesson_train")

    def test_unknown_occupancy_no_process_launch(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "query failed"):
            self.execute(occupancy=lambda device: False)
        self.assertFalse(self.calls)

    def test_gpu_not_released_stops_after_first_fit(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "cleanup unverified"):
            self.execute(occupancy=Mock(side_effect=[True, False]))
        self.assertEqual(len(self.calls), 1)
        cleanup = writer._read(self.output / "logs/lesson_train.cleanup.json")
        self.assertFalse(cleanup["reservation_release_verified"])

    def test_output_conflict_and_execution_opt_in(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            self.prepare()
        with self.assertRaisesRegex(ValueError, "explicit execution"):
            pipeline.execute_pipeline(self.output)
        (self.output / "logs/lesson_train.log").write_text("existing log")
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertFalse(self.calls)
        with self.assertRaises(FileExistsError):
            self.execute()

    def test_changed_preparation_rejects_before_launch(self):
        self.prepare()
        path = self.output / "preparations/lesson/corpus.json"
        path.chmod(0o644)
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            self.execute()
        self.assertFalse(self.calls)

    def test_protected_root_and_invalid_selector(self):
        with self.assertRaisesRegex(ValueError, "selector"):
            pipeline.prepare_pipeline(self.fixture.root, self.lesson, self.sham, self.output,
                                      devices=dict(lesson="0,1", sham="2"))
        with self.assertRaisesRegex(ValueError, "protected"):
            pipeline.prepare_pipeline(self.fixture.root, self.lesson, self.sham, self.fixture.root / "pipeline",
                                      devices=self.devices)


class ProcessBoundaryTests(unittest.TestCase):
    def test_actual_cpu_timeout_cleans_owned_descendants_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outsider = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
            try:
                code = ("import subprocess,sys,time; from pathlib import Path; "
                        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                        f"Path({str(root / 'child.pid')!r}).write_text(str(child.pid)); time.sleep(30)")
                command = dict(argv=[sys.executable, "-c", code], stdout_path=str(root / "train.log"),
                               env=dict(V6_MODEL=str(root)))
                with self.assertRaises(subprocess.TimeoutExpired):
                    pipeline.run_training(command, device="2", occupancy=lambda device: True, timeout=0.8)
                cleanup = writer._read(root / "train.cleanup.json")
                self.assertTrue(cleanup["owned_group_empty"])
                self.assertTrue((root / "child.pid").exists())
                self.assertFalse(neutral._group_alive(cleanup["pid"]))
                self.assertIsNone(outsider.poll())
            finally:
                outsider.terminate()
                outsider.wait(timeout=5)

    def test_log_is_exclusive_and_failed_query_never_launches(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.log"
            command = dict(argv=[sys.executable, "-c", "pass"], stdout_path=str(path), env=dict(V6_MODEL=temporary))
            popen = Mock(side_effect=AssertionError("must not spawn"))
            with self.assertRaisesRegex(ValueError, "query failed"):
                pipeline.run_training(command, device="1", occupancy=lambda device: False, popen=popen)
            path.write_text("untouched")
            with self.assertRaises(FileExistsError):
                pipeline.run_training(command, device="1", occupancy=lambda device: True, popen=popen)
            self.assertEqual(path.read_text(), "untouched")


if __name__ == "__main__":
    unittest.main()
