"""Fixed archive plus simulated replay/tokenizer/trainer and injected CPU READs."""

import copy
import os
from pathlib import Path
import time
import unittest
from unittest.mock import Mock, patch

import test_astra_pcfl_native_actor as native_fixtures
import test_astra_pcfl_own_write_readout as read_fixtures
from test_astra_pcfl_event_prefix_import import ARCHIVE, archived_fixture
from gpu import astra_pcfl_event_only_command as command


class Harness:
    def __init__(self, case):
        self.fixture = native_fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        case.addCleanup(self.fixture.doCleanups)
        self.root, self.clock = self.fixture.root, self.fixture.clock
        self.clock.now = time.monotonic()
        self.tokenizer = self.fixture.session.tokenizer
        self.output, self.spec_path = self.root / "prepared", self.root / "spec.json"
        self.evidence, self.replay, self.imported = archived_fixture()
        original = command.prefix._json(self.evidence["files"]["manifest.json"])["binding"]
        self.environment = copy.deepcopy(original["environment"]["runtime"])
        replay_path, base_path = self.root / "replay.json", self.root / "base.json"
        command.write(replay_path, self.replay)
        command.write(base_path, {"status": "COMPLETE", "device": "cpu", "dtype": "bfloat16",
            "base_state_sha256": original["base_state_sha256"], "environment": self.environment,
            "model_binding_sha256": self.fixture.config["model_binding"]["sha256"], "model_files": original["environment"]["model_files"]})
        self.spec = {"schema": command.SCHEMA + "/spec", "model_path": str(self.fixture.model),
            "model_binding": self.fixture.config["model_binding"], "environment": self.environment,
            "base_state_receipt": self.pin(base_path), "shutdown_binding": self.pin(Path(__file__).resolve()),
            "archive": self.pin(ARCHIVE), "replay_receipt": self.pin(replay_path), "authority": self.pin(command.SCOPE),
            "gpu_uuid": "GPU-CPU-TEST", "boot_id": command.own.boot_id(), "expires_monotonic": self.clock() + 7200,
            "source_files": command.source_files()}
        self.identity = {"model_files": original["environment"]["model_files"]}
        self.sessions = []
        self.finish, self.text = "stop", "MISS"
        for mocked in (
            patch.dict(os.environ, {**{key: "1" for key in command.OFFLINE}, "CUDA_VISIBLE_DEVICES": ""}),
            patch.object(command.own, "SHUTDOWN_SHA256", command.file_hash(__file__)),
            patch.object(command.prefix, "verify_tokenizer", side_effect=self.verify_tokenizer),
            patch.object(command.event, "encode_fit", side_effect=self.encode)):
            mocked.start()
            case.addCleanup(mocked.stop)

    def pin(self, path):
        return {"path": str(path), "sha256": command.file_hash(path)}

    def verify_tokenizer(self, imported, tokenizer):
        return command.prefix.seal({"schema": command.prefix.SCHEMA + "/tokenizer", "status": "EVENT_PREFIX_TOKENIZER_VERIFIED",
            "import_sha256": imported["sha256"], "calls_checked": 16, "model_calls": 0,
            "tokenizer_files": {}, "full_contract_released": False})

    def encode(self, fitted, tokenizer):
        return command.prefix.seal({"fit_sha256": fitted["sha256"], "items": [{"SYNTHETIC_ENCODING": index} for index in range(160)]})

    def prepare(self):
        self.spec_path.write_bytes(command.canonical(self.spec) + b"\n")
        self.manifest = command.prepare(str(self.spec_path), command.file_hash(self.spec_path), str(self.output),
            tokenizer_factory=lambda model: self.tokenizer, identity_reader=lambda deadline: self.identity,
            environment_reader=lambda: self.environment, clock=self.clock)
        self.path = self.output / "manifest.json"
        self.manifest_hash = command.file_hash(self.path)
        return self.manifest

    def trainer(self, fitted, tokenizer, base_factory, output):
        output.mkdir()
        adapter = output / "adapter"
        adapter.mkdir()
        command.write(adapter / "adapter_config.json", {"r": 8, "lora_alpha": 16, "lora_dropout": .05,
            "peft_type": "LORA", "bias": "none", "modules_to_save": None})
        (adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_TENSORS")
        receipt = {"status": "COMPLETE", "updates": 200, "presentations": 800, "training_forwards": 800,
            "fit_sha256": fitted["sha256"], "encoding_sha256": self.manifest["encoding_sha256"], "files": command.own._inventory(output)}
        command.write(output / "completed.json", receipt)
        return receipt

    def actor(self, settings):
        session = read_fixtures.Session(settings, self.clock)
        session.text, session.duration = self.text, .001
        session.mutate = lambda raw: {**raw, "finish_reason": self.finish}
        self.sessions.append(session)
        return command.readout_api.ReadoutActor(settings, loader=lambda config: session,
            environment_reader=lambda: self.environment["native"], clock=self.clock)

    def run(self, stage="fit", arm=None, **changes):
        arguments = {"stage": stage, "arm": arm, "environment_reader": lambda: self.environment, "clock": self.clock}
        if stage == "fit": arguments.update(tokenizer_factory=lambda model: self.tokenizer, trainer=self.trainer)
        else: arguments.update(actor_factory=self.actor)
        arguments.update(changes)
        return command.stage(str(self.path), self.manifest_hash, self.clock() + 1000, **arguments)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(self)

    def test_prepare_scope_tokenizer160_service14_keeps_original_failure(self):
        manifest = self.harness.prepare()
        root = self.harness.output
        imported, fitted = command.read(root / "import.json"), command.read(root / "fit.json")
        self.assertEqual(imported["status"], "EVENT_PREFIX_IMPORTED_TOKENIZER_PENDING")
        self.assertEqual((imported["original_status"], imported["original_returncode"], imported["original_calls"]), ("FORMATION_FAILED", 1, 17))
        self.assertEqual(fitted["binding"]["authority_sha256"], command.file_hash(command.SCOPE))
        self.assertEqual(command.read(root / "tokenizer.json")["sha256"], manifest["tokenizer_sha256"])
        self.assertEqual(len(command.read(root / "encoding.json")["items"]), 160)
        self.assertEqual(len(manifest["roster"]), 28)
        self.assertEqual(command.read(root / "service.json")["exact"], 14)
        self.assertFalse(manifest["full_contract_released"])
        self.assertFalse((root / "formation").exists())

    def test_fit_fresh200_not_formation_and_unconstrained_auth_c0_reads(self):
        self.harness.prepare()
        result = self.harness.run()
        self.assertEqual((result["calls"], result["fits"], result["updates"]), (0, 1, 200))
        for arm in command.readout_api.ARMS:
            completed = self.harness.run("readout", arm)
            self.assertEqual(completed["calls"], 28)
            self.assertEqual(completed["by_view"]["8"]["denominator"], 14)
            self.assertEqual(completed["by_view"]["8"]["strict_stop"], 0)
            config = command.read(self.harness.output / ("readout_" + arm) / "readout_config.json")
            self.assertEqual(config["adapter"] is None, arm == "NO_WRITE_C0")
            self.assertEqual({row["view"] for row in config["roster"]}, {0, 8})
            self.assertTrue(all("structured_outputs" not in sampling for prompt, sampling in self.harness.sessions[-1].calls))
        self.assertEqual(len(self.harness.sessions), 2)

    def test_length_and_malformed_are_scored_not_infrastructure_failure(self):
        self.harness.prepare()
        self.harness.finish = "length"
        completed = self.harness.run("readout", "NO_WRITE_C0")
        self.assertEqual(completed["status"], "COMPLETE")
        scores = command.read(self.harness.output / "readout_NO_WRITE_C0/scores.json")
        self.assertEqual(len(scores["results"]), 28)
        self.assertTrue(all(row["raw"] == "MISS" and not row["strict_stop"] for row in scores["results"]))
        self.assertEqual(scores["paired_endpoint"], "REQUIRES_BOTH_RELEASED_ARMS_NOT_INFERRED_HERE")

    def test_auth_cannot_use_missing_or_changed_fit(self):
        self.harness.prepare()
        with self.assertRaises(FileNotFoundError): self.harness.run("readout", "AUTH_WRITE")
        self.harness.run()
        manifest = self.harness.manifest
        adapter = self.harness.output / "fit/write/adapter/adapter_model.safetensors"
        adapter.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "upstream file drift"): command._completed(manifest, "fit")

    def test_source_archive_base_and_replay_file_pins_reject(self):
        original = copy.deepcopy(self.harness.spec)
        for field in ("archive", "replay_receipt", "base_state_receipt", "source_files"):
            self.harness.spec = copy.deepcopy(original)
            self.harness.output = self.harness.root / field
            if field == "source_files": self.harness.spec[field].pop(str(Path(command.__file__).resolve()))
            else: self.harness.spec[field]["sha256"] = "0" * 64
            with self.subTest(field=field), self.assertRaises(ValueError): self.harness.prepare()

    def test_positive_tokenizer_required_before_manifest(self):
        with patch.object(command.prefix, "verify_tokenizer", side_effect=ValueError("tokenizer mismatch")):
            with self.assertRaisesRegex(ValueError, "tokenizer mismatch"): self.harness.prepare()
        self.assertFalse((self.harness.output / "manifest.json").exists())
        self.assertTrue((self.harness.output / "prepare_failure.json").exists())

    def test_fit_failure_and_incomplete_updates_preserved(self):
        self.harness.prepare()
        trainer = Mock(side_effect=RuntimeError("synthetic numerical failure"))
        with self.assertRaisesRegex(RuntimeError, "numerical failure"): self.harness.run(trainer=trainer)
        self.assertTrue((self.harness.output / "fit/failure.json").is_file())
        self.assertFalse((self.harness.output / "fit/completed.json").exists())
        with self.assertRaises(FileExistsError): self.harness.run()

    def test_199_updates_or_encoding_drift_cannot_complete_fit(self):
        self.harness.prepare()
        def incomplete(*arguments):
            receipt = self.harness.trainer(*arguments)
            return {**receipt, "updates": 199}
        with self.assertRaisesRegex(ValueError, "LOW200 writer receipt"):
            self.harness.run(trainer=incomplete)
        self.assertFalse((self.harness.output / "fit/completed.json").exists())
        self.harness.output = self.harness.root / "another_prepare"
        self.harness.prepare()
        trainer = Mock(side_effect=AssertionError("must not train"))
        with patch.object(command.event, "encode_fit", return_value={"wrong": "encoding"}):
            with self.assertRaisesRegex(ValueError, "encoding drift"):
                self.harness.run(trainer=trainer)
        trainer.assert_not_called()

    def test_native_kind_cannot_admit_injected_readout_and_original_bytes_join(self):
        self.harness.prepare()
        self.harness.run("readout", "NO_WRITE_C0")
        directory = self.harness.output / "readout_NO_WRITE_C0"
        config = command.read(directory / "readout_config.json")
        responses = [command.read(directory / (row["id"].replace("/", "_") + ".json")) for row in self.harness.manifest["roster"]]
        with self.assertRaisesRegex(ValueError, "native readout kind"):
            command._read_custody(directory, config, responses, False)
        raw_path = directory / "actor/call_0000.raw.json"
        raw = command.read(raw_path)
        raw["raw"]["text"] = "changed"
        raw_path.write_bytes(command.canonical(raw))
        with self.assertRaisesRegex(ValueError, "raw scored bytes"):
            command._read_custody(directory, config, responses, True)

    def test_expired_worker_and_injected_native_admission(self):
        self.harness.prepare()
        with self.assertRaisesRegex(ValueError, "bounded worker deadline"):
            command.stage(str(self.harness.path), self.harness.manifest_hash, self.harness.clock()-1,
                stage="fit", environment_reader=lambda: self.harness.environment, clock=self.harness.clock)
        with patch.object(command.own, "environment", return_value=self.harness.environment):
            with self.assertRaisesRegex(ValueError, "injected preparation"):
                command.stage(str(self.harness.path), self.harness.manifest_hash, self.harness.clock()+1000,
                    stage="readout", arm="NO_WRITE_C0", clock=self.harness.clock)

    def test_scope_authority_resealed_fit_still_rejected(self):
        self.harness.prepare()
        root = self.harness.output
        fitted = command.read(root / "fit.json")
        fitted["binding"]["authority_sha256"] = "a" * 64
        fitted = command.prefix.seal({key: value for key, value in fitted.items() if key != "sha256"})
        (root / "fit.json").write_bytes(command.canonical(fitted))
        manifest = self.harness.manifest
        manifest["fit_sha256"] = fitted["sha256"]
        manifest["input_files"]["fit.json"] = command.file_hash(root / "fit.json")
        manifest = command.prefix.seal({key: value for key, value in manifest.items() if key != "sha256"})
        self.harness.path.write_bytes(command.canonical(manifest))
        with self.assertRaisesRegex(ValueError, "scope FILE/fit authority"):
            command.validate_manifest(str(self.harness.path), command.file_hash(self.harness.path), environment_reader=lambda: self.harness.environment, clock=self.harness.clock)


if __name__ == "__main__":
    unittest.main()
