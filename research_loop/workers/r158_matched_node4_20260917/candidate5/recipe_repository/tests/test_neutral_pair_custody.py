"""Synthetic CPU probe fixtures; no GPU execution or model-origin claims."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from organism_v6 import neutral_pair_custody as custody
from organism_v6 import reasoning_gym_gym
from organism_v6.reasoning_neutral_probe import run_probe
import test_reasoning_neutral_probe as fixtures


class NeutralPairCustodyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.NeutralProbeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.probes / "pair"
        self.root.mkdir()
        self.spec_hash = hashlib.sha256(b"synthetic CPU spec").hexdigest()
        self.snapshot = custody.source_snapshot()
        self.receipts = {}
        for index, condition in enumerate(("off", "on")):
            options = dict(self.fixture.options, output_dir=self.root / condition)
            if condition == "off":
                options.update(adapter_path=None, expected_adapter_hashes={})
            gym = fixtures.FixtureGym()
            gym._bootstrap = Path(reasoning_gym_gym.BOOTSTRAP_PATH).read_text()
            backend = fixtures.FixtureBackend(options["model_path"], options["adapter_path"])
            run_probe(backend, gym, **options)
            receipt = dict(evidence_label="EVALUATION_ONLY", condition=condition,
                           spec_sha256=self.spec_hash, pid=10000 + index,
                           results_sha256=self.digest(self.root / condition / "results.json"),
                           manifest_sha256=self.digest(self.root / condition / "manifest.json"))
            self.write(self.root / (condition + "_WORKER_DONE.json"), receipt)
            self.receipts[condition] = custody.verify_condition(self.root, condition, self.spec_hash)

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def write(path, value):
        path.parent.chmod(0o755)
        if path.exists():
            path.chmod(0o644)
        path.write_text(json.dumps(value))

    def validate(self):
        return custody.validate_pair(self.root, self.spec_hash, self.receipts, self.snapshot)

    def config(self, condition):
        return json.loads((self.root / condition / "configuration.json").read_text())

    def reseal(self, condition, accept=False):
        directory = self.root / condition
        inventory = {path.name: self.digest(path) for path in directory.iterdir()
                     if path.name != "manifest.json"}
        self.write(directory / "manifest.json", dict(evidence_label="EVALUATION_ONLY", sha256=inventory))
        receipt = copy.deepcopy(self.receipts[condition])
        receipt["results_sha256"] = self.digest(directory / "results.json")
        receipt["manifest_sha256"] = self.digest(directory / "manifest.json")
        self.write(self.root / (condition + "_WORKER_DONE.json"), receipt)
        if accept:
            self.receipts[condition] = custody.verify_condition(self.root, condition, self.spec_hash)

    def change_config(self, condition, field, value):
        config = self.config(condition)
        config[field] = value
        self.write(self.root / condition / "configuration.json", config)
        self.reseal(condition, accept=True)

    def test_real_helper_positive_and_json_safe_snapshot(self):
        snapshot = json.loads(json.dumps(self.snapshot))
        originals = copy.deepcopy(self.receipts)
        custody.verify_source_snapshot(snapshot)
        expected = {condition: self.digest(self.root / (condition + "_WORKER_DONE.json"))
                    for condition in ("off", "on")}
        self.assertEqual(self.validate(), expected)
        self.assertEqual(self.receipts, originals)

    def test_prior_arm_results_mutation_rejected(self):
        self.write(self.root / "off/results.json", {"changed": True})
        with self.assertRaisesRegex(ValueError, "digest"):
            self.validate()

    def test_prior_arm_trace_mutation_rejected(self):
        path = self.root / "off/generations.jsonl"
        path.chmod(0o644)
        path.write_text("changed trace")
        with self.assertRaisesRegex(ValueError, "artifact digest"):
            self.validate()

    def test_original_receipt_replacement_rejected(self):
        self.write(self.root / "off/results.json", {"changed": True})
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "original receipt changed"):
            self.validate()

    def test_receipt_extra_field_mutation_rejected(self):
        receipt = dict(self.receipts["off"], cleanup="changed")
        self.write(self.root / "off_WORKER_DONE.json", receipt)
        with self.assertRaisesRegex(ValueError, "original receipt changed"):
            self.validate()

    def test_missing_original_receipt_rejected(self):
        self.receipts["off"] = None
        with self.assertRaisesRegex(ValueError, "original receipt"):
            self.validate()

    def test_bootstrap_conflict_rejected(self):
        self.change_config("on", "birth_prompt", "different prompt")
        with self.assertRaisesRegex(ValueError, "shared configuration"):
            self.validate()

    def test_same_unbound_bootstrap_rejected(self):
        for condition in ("off", "on"):
            self.change_config(condition, "birth_prompt", "same but not pinned")
        with self.assertRaisesRegex(ValueError, "bootstrap snapshot"):
            self.validate()

    def test_package_and_seed_conflicts_rejected(self):
        for field, value in (("reasoning_gym_version", "different"), ("gen_seed", 7)):
            original = self.config("on")[field]
            with self.subTest(field=field):
                self.change_config("on", field, value)
                with self.assertRaisesRegex(ValueError, "shared configuration"):
                    self.validate()
                self.change_config("on", field, original)

    def test_snapshot_shape_and_root_rejected(self):
        original = self.snapshot
        for snapshot in ({}, dict(original, source_root="/tmp"),
                         dict(original, sha256={})):
            with self.subTest(snapshot=snapshot), self.assertRaisesRegex(ValueError, "snapshot mismatch"):
                custody.verify_source_snapshot(snapshot)

    def test_local_source_and_bootstrap_drift_rejected(self):
        source_root = self.fixture.root / "synthetic-source-copy"
        for name in self.snapshot["sha256"]:
            destination = source_root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(self.snapshot["source_root"]) / name, destination)
        with patch.object(custody, "_ROOT", source_root), patch.object(
                reasoning_gym_gym, "BOOTSTRAP_PATH", str(source_root / custody._BOOTSTRAP)):
            snapshot = custody.source_snapshot()
            for name in ("organism_v6/model_backend.py", custody._BOOTSTRAP):
                path = source_root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\nchanged")
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "snapshot mismatch"):
                    custody.verify_source_snapshot(snapshot)
                path.write_bytes(original)
            (source_root / "unrelated.txt").write_text("not part of execution closure")
            custody.verify_source_snapshot(snapshot)

    def test_missing_required_artifact_rejected(self):
        directory = self.root / "off"
        directory.chmod(0o755)
        (directory / "generations.jsonl").unlink()
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "required artifacts"):
            custody.verify_condition(self.root, "off", self.spec_hash)

    def test_missing_episode_ledger_rejected(self):
        directory = self.root / "off"
        directory.chmod(0o755)
        (directory / "episode_0000.jsonl").unlink()
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "episode ledger"):
            custody.verify_condition(self.root, "off", self.spec_hash)

    def test_failure_even_if_manifested_rejected(self):
        self.write(self.root / "off/failure.json", {"error": "synthetic"})
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "failure evidence"):
            custody.verify_condition(self.root, "off", self.spec_hash)

    def test_unmanifested_file_rejected(self):
        self.write(self.root / "off/extra.json", {})
        with self.assertRaisesRegex(ValueError, "unmanifested"):
            self.validate()

    def test_manifest_traversal_rejected(self):
        directory = self.root / "off"
        original = json.loads((directory / "manifest.json").read_text())
        outside = self.root / "outside.json"
        self.write(outside, {})
        for name in ("../outside.json", str(outside), "sub/../outside.json", "..\\outside.json"):
            manifest = copy.deepcopy(original)
            manifest["sha256"][name] = self.digest(outside)
            self.write(directory / "manifest.json", manifest)
            receipt = dict(self.receipts["off"], manifest_sha256=self.digest(directory / "manifest.json"))
            self.write(self.root / "off_WORKER_DONE.json", receipt)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "unsafe artifact path"):
                custody.verify_condition(self.root, "off", self.spec_hash)

    def test_artifact_symlink_rejected(self):
        directory = self.root / "off"
        directory.chmod(0o755)
        path = directory / "generations.jsonl"
        external = self.root / "trace.jsonl"
        external.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "unsafe artifact"):
            self.validate()

    def test_condition_directory_symlink_rejected(self):
        directory = self.root / "off"
        moved = self.root / "moved"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink directory"):
            self.validate()

    def test_duplicate_receipt_keys_rejected(self):
        path = self.root / "off_WORKER_DONE.json"
        path.write_text('{"condition":"off","condition":"on"}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            self.validate()

    def test_false_condition_and_spec_rejected(self):
        with self.assertRaisesRegex(ValueError, "receipt mismatch"):
            custody.verify_condition(self.root, "off", "0" * 64)
        with self.assertRaisesRegex(ValueError, "invalid condition"):
            custody.verify_condition(self.root, "../off", self.spec_hash)

    def test_code_hash_conflict_rejected(self):
        config = self.config("on")
        code = config["code_hashes_before"]
        code[next(iter(code))] = "0" * 64
        self.write(self.root / "on/configuration.json", config)
        check = json.loads((self.root / "on/source_check.json").read_text())
        check["code_hashes_after"] = code
        self.write(self.root / "on/source_check.json", check)
        self.reseal("on", accept=True)
        with self.assertRaisesRegex(ValueError, "shared configuration"):
            self.validate()

    def test_same_false_code_hash_rejected(self):
        for condition in ("off", "on"):
            config = self.config(condition)
            code = config["code_hashes_before"]
            code[str(custody._ROOT / "organism_v6/batch_loop.py")] = "0" * 64
            self.write(self.root / condition / "configuration.json", config)
            check = json.loads((self.root / condition / "source_check.json").read_text())
            check["code_hashes_after"] = code
            self.write(self.root / condition / "source_check.json", check)
            self.reseal(condition, accept=True)
        with self.assertRaisesRegex(ValueError, "probe code drift"):
            self.validate()

    def test_code_inventory_omission_rejected(self):
        for condition in ("off", "on"):
            config = self.config(condition)
            config["code_hashes_before"] = {}
            self.write(self.root / condition / "configuration.json", config)
            check = json.loads((self.root / condition / "source_check.json").read_text())
            check["code_hashes_after"] = {}
            self.write(self.root / condition / "source_check.json", check)
            self.reseal(condition, accept=True)
        with self.assertRaisesRegex(ValueError, "missing probe code"):
            self.validate()

    def test_wrong_adapter_condition_rejected(self):
        config = self.config("on")
        config["source_identity"]["adapter_input"] = None
        config["source_identity"]["adapter_files"] = {}
        self.write(self.root / "on/configuration.json", config)
        self.reseal("on")
        with self.assertRaisesRegex(ValueError, "adapter condition"):
            custody.verify_condition(self.root, "on", self.spec_hash)

    def test_failed_source_check_rejected(self):
        path = self.root / "off/source_check.json"
        check = json.loads(path.read_text())
        check["unchanged"] = False
        self.write(path, check)
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "failed source check"):
            custody.verify_condition(self.root, "off", self.spec_hash)

    def test_pair_failure_marker_rejected(self):
        self.write(self.root / "PAIR_FAILED.json", {})
        with self.assertRaisesRegex(ValueError, "pair has failure"):
            self.validate()

    def test_dangling_pair_failure_marker_rejected(self):
        (self.root / "PAIR_FAILED.json").symlink_to(self.root / "missing")
        with self.assertRaisesRegex(ValueError, "pair has failure"):
            self.validate()

    def test_receipt_symlink_rejected(self):
        path = self.root / "off_WORKER_DONE.json"
        external = self.root / "external_receipt.json"
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "unsafe artifact"):
            self.validate()

    def test_nonfinite_receipt_json_rejected(self):
        path = self.root / "off_WORKER_DONE.json"
        path.write_text('{"value":NaN}')
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.validate()

    def test_episode_identity_mismatch_rejected(self):
        path = self.root / "off/results.json"
        result = json.loads(path.read_text())
        result["episodes"][0]["episode_id"] = "different"
        self.write(path, result)
        self.reseal("off")
        with self.assertRaisesRegex(ValueError, "episode ledger"):
            custody.verify_condition(self.root, "off", self.spec_hash)

    def test_changed_model_path_not_ignored(self):
        config = self.config("on")
        alternate = str(self.fixture.root / "alternate_model")
        config["sources"]["model"] = alternate
        config["source_identity"]["model_input"] = alternate
        self.write(self.root / "on/configuration.json", config)
        self.reseal("on", accept=True)
        with self.assertRaisesRegex(ValueError, "shared configuration"):
            self.validate()

    def test_reused_process_identity_rejected(self):
        receipt = dict(self.receipts["on"], pid=self.receipts["off"]["pid"])
        self.write(self.root / "on_WORKER_DONE.json", receipt)
        self.receipts["on"] = custody.verify_condition(self.root, "on", self.spec_hash)
        with self.assertRaisesRegex(ValueError, "pid reused"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
