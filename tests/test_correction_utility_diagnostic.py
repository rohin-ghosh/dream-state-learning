import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_correction_utility_diagnostic as diagnostic


class CorrectionUtilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.adapter = self.root / "recipients/whole_raw/seed0"
        self.adapter.mkdir(parents=True)
        self.config = dict(model=str(self.root / "base"), seed=0)
        self.command = dict(config=self.config, corpus_sha256="corpus")
        self.tokens = dict(supervised_tokens_per_epoch=320, input_tokens_per_epoch=3200,
                           input_tokens_all_epochs=9600)
        self.manifest = dict(config=self.config, steps=96, nonfinite_batches=0, final_loss=.1,
            base_model=self.config["model"], corpus=dict(sha256="corpus", n_items=32, n_encoded=32,
                n_skipped_no_target=0), tokens=dict(target=320, total=3200), train_tokens_seen=9600,
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0))
        (self.adapter / "DONE").touch()
        (self.adapter / "adapter_config.json").write_text(json.dumps(dict(r=8, lora_alpha=16, lora_dropout=.05)))

    def write_manifest(self, value=None):
        (self.adapter / "train_manifest.json").write_text(json.dumps(value or self.manifest))

    def check_fit(self):
        with patch.object(diagnostic, "file_hashes", return_value={"adapter_config.json": "config", "adapter_model.safetensors": "weights"}):
            return diagnostic.verify_fit(self.adapter, self.command, self.tokens)

    def test_exact_native_fit_receipt(self):
        self.write_manifest()
        self.assertEqual(self.check_fit()[0]["steps"], 96)

    def test_bad_fit_dose_or_nonfinite_rejected(self):
        for field, value in (("steps", 95), ("nonfinite_batches", 1), ("final_loss", float("nan")),
                             ("train_tokens_seen", 9599)):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.manifest)
                changed[field] = value
                self.write_manifest(changed)
                with self.assertRaises(ValueError):
                    self.check_fit()

    def test_wrong_corpus_or_target_count_rejected(self):
        for section, field, value in (("corpus", "n_items", 1), ("corpus", "sha256", "wrong"),
                                      ("corpus", "n_skipped_no_target", 1), ("tokens", "target", 319),
                                      ("truncation", "items_split", 1)):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.manifest)
                changed[section][field] = value
                self.write_manifest(changed)
                with self.assertRaises(ValueError):
                    self.check_fit()

    def test_missing_done_rejected(self):
        self.write_manifest()
        (self.adapter / "DONE").unlink()
        with self.assertRaises(ValueError):
            self.check_fit()

    def test_wrong_saved_adapter_rejected(self):
        self.write_manifest()
        (self.adapter / "adapter_config.json").write_text(json.dumps(dict(r=16, lora_alpha=16, lora_dropout=.05)))
        with self.assertRaises(ValueError):
            self.check_fit()

    def test_cli_never_executes_without_explicit_flag(self):
        with patch.object(diagnostic, "execute") as execute:
            with self.assertRaises(ValueError):
                diagnostic.main(["--material", "material", "--panel", "panel", "--out", "logs",
                                 "--arm", "whole_raw", "--seed", "0", "--device", "1"])
            execute.assert_not_called()

    def test_full_sequence_binds_original_pair_receipts(self):
        material = self.root / "material"
        (material / "whole_raw").mkdir(parents=True)
        (material / "artifact_hashes.json").write_text("{}")
        (material / "whole_raw/tokenizer_preflight.json").write_text(json.dumps(self.tokens))
        panel_path = self.root / "panel.json"
        panel_path.write_text("{}")
        out = self.root / "logs"
        report = dict(model_path=self.config["model"], recipient_root=str(self.root / "recipients"), expected_model_files={})
        panel = dict(prospective_probe=dict(gen_seed=0), families_sha256="families", episode_ids=["example"])
        command = dict(argv=["python", "fit"], output=str(self.adapter))
        workers = dict(off={"pid": 10}, on={"pid": 11})
        snapshot = dict(version="fixture")
        receipts = dict(off="off-hash", on="on-hash")
        calls = []

        def run_worker(argv, *, log_path, timeout, device):
            calls.append((log_path.name, timeout, device))
            if log_path.name == "fit.log":
                self.write_manifest()
            else:
                pair = out / "probes/pair"
                pair.mkdir()
                (pair / "PAIR_DONE.json").write_text(json.dumps(dict(
                    spec_sha256=diagnostic.digest(out / "probe_spec.json"), workers=workers,
                    source_snapshot=snapshot, receipt_sha256=receipts)))

        with patch.dict(os.environ), patch.object(diagnostic.supervisor, "selected_device", return_value="1"), \
             patch.object(diagnostic, "inspect_preparation", return_value=(report, panel)), \
             patch.object(diagnostic, "selected_command", return_value=command), \
             patch.object(diagnostic, "verify_fit", return_value=(self.manifest, {})), \
             patch.object(diagnostic.supervisor, "read_spec"), \
             patch.object(diagnostic.supervisor, "run_worker", side_effect=run_worker), \
             patch.object(diagnostic, "validate_pair", return_value=receipts) as validate:
            diagnostic.execute(material, panel_path, out, "whole_raw", 0, "1")
            validate.assert_called_once_with(out / "probes/pair", diagnostic.digest(out / "probe_spec.json"), workers, snapshot)
        self.assertEqual(calls, [("fit.log", 600, "1"), ("pair.log", 1800, "1")])
        self.assertTrue((out / "COMPLETED.json").is_file())
        self.assertFalse((out / "FAILED.json").exists())


if __name__ == "__main__":
    unittest.main()
