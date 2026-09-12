"""Stdlib-only acceptance tests for immutable diagnostic seed-run preparation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "gpu" / "prepare_memory_seed_run.py"
SPEC = importlib.util.spec_from_file_location("prepare_memory_seed_run", HELPER)
prep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prep)


class PrepareMemorySeedRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.destination = self.root / "destination"
        self.write("manifest.json", {"seed": 1, "n_banks": 2, "token_budget": 65536,
                                   "counter": "hf", "model": prep.BASE_MODEL, "scorer": "HFScorer",
                                   "lora": {"rank": 8, "epochs": 3, "lr": 0.0001}})
        self.write("distractor.json", {"text": "Synthetic distractor.", "counter": "hf"})
        for bank in range(2):
            self.write(f"banks/bank{bank}.json", {"bank": bank, "seed": 1,
                       "events": [{"event_id": f"event-{bank}"}]})
            for cell in prep.CELLS:
                prefix = f"corpora/bank{bank}/{cell}/across/sleep4"
                item = {"context": "Owner ", "target": "blue", "weight": 1.0,
                        "mask_context": False, "chat": False, "shuffled": False,
                        "event_ids": [f"event-{bank}"], "kind": "fact"}
                identities = [("Owner blue", 1.0, False)]
                corpus = {"bank": bank, "arm": "across", "sleep": 4, "writer": "occurrences",
                          "representation": "frames", "shuffled": False, "ordering": "chronological",
                          "counter": "hf", "epochs": 3, "frame_forms": 16, "frame_repeats": 16,
                          "token_budget": 250000, "corpus": [item], "sha": prep.short_hash(identities),
                          "items_sha": prep.short_hash(identities),
                          "stats": {"n_items": 1, "token_budget": 250000}}
                if cell == "CF_r16_b":
                    events = {f"event-{bank}": {"lines": ["Owner blue"] * 16}}
                    self.write(f"{prefix}/generations.json", {"bank": bank, "arm": "across", "sleep": 4,
                               "variant": "b", "backend": "vllm", "model": prep.BASE_MODEL,
                               "repeats": 16, "negatives": 0, "events": events})
                    corpus.update(representation="childframes", frame_forms=1, child_variant="b",
                                  child_backend="vllm", generations_sha=prep.short_hash(
                                      [(key, value["lines"]) for key, value in sorted(events.items())]))
                self.write(f"{prefix}/corpus.json", corpus)
        for relative in ("adapter_index.json", "adapters/old/adapter_model.safetensors",
                         "eval/old.json", "report/summary.md", "STAGE_F_DONE"):
            self.write(relative, {"old_evidence": True})

    def write(self, relative, document):
        target = self.source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(dict(document, synthetic=True), indent=2) + "\n")

    def mutate(self, relative, **updates):
        document = json.loads((self.source / relative).read_text())
        document.update(updates)
        self.write(relative, document)

    def prepare(self, **kwargs):
        return prep.prepare_run(self.source, self.destination, 2, "F_r16k16", **kwargs)

    def snapshot(self):
        return {str(path.relative_to(self.source)): (path.read_bytes(), path.stat().st_mtime_ns,
                                                    path.stat().st_mode)
                for path in self.source.rglob("*") if path.is_file()}

    def test_source_unchanged_hashes_and_no_old_outputs(self):
        before = self.snapshot()
        receipt = self.prepare()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(receipt["training_seed"], 2)
        self.assertEqual(receipt["source_bank_seed"], 1)
        self.assertEqual(receipt["base_model"], prep.BASE_MODEL)
        self.assertEqual(receipt["label"], prep.LABEL)
        self.assertFalse(receipt["clean_lineage_eligible"])
        actual = {str(path.relative_to(self.destination)) for path in self.destination.rglob("*") if path.is_file()}
        self.assertEqual(actual, set(receipt["inputs"]) | {prep.RECEIPT})
        self.assertEqual(len(receipt["inputs"]), 6)
        for relative, evidence in receipt["inputs"].items():
            content = (self.source / relative).read_bytes()
            target = self.destination / relative
            self.assertEqual(target.read_bytes(), content)
            self.assertEqual(evidence, {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
            self.assertEqual(target.stat().st_mode & 0o222, 0)
        self.assertEqual(json.loads((self.destination / "manifest.json").read_text())["seed"], 1)

    def test_collision_preserves_existing_evidence(self):
        self.destination.mkdir()
        marker = self.destination / "evidence"
        marker.write_text("keep")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(self.destination.iterdir()), [marker])

    def test_child_inputs_only_selected_corpora_all_banks(self):
        receipt = prep.prepare_run(self.source, self.destination, 0, "CF_r16_b", banks=[1])
        self.assertIn("banks/bank0.json", receipt["inputs"])
        self.assertIn("corpora/bank1/CF_r16_b/across/sleep4/generations.json", receipt["inputs"])
        self.assertFalse((self.destination / "corpora/bank0").exists())
        self.assertEqual(len(receipt["inputs"]), 6)

    def test_check_only_has_no_writes(self):
        before = self.snapshot()
        self.assertEqual(self.prepare(check_only=True)["status"], "validated_only")
        self.assertFalse(self.destination.exists())
        self.assertEqual(before, self.snapshot())

    def test_bad_manifest_metadata_fails_before_destination(self):
        original = json.loads((self.source / "manifest.json").read_text())
        for key, value in (("model", "other"), ("scorer", "MockScorer"), ("counter", "approx"),
                           ("seed", None), ("n_banks", True), ("lora", {})):
            with self.subTest(key=key):
                self.write("manifest.json", dict(original, **{key: value}))
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.destination.exists())

    def test_missing_input_and_bank_seed_mismatch(self):
        self.mutate("banks/bank0.json", seed=0)
        with self.assertRaises(ValueError):
            self.prepare()
        self.mutate("banks/bank0.json", seed=1)
        (self.source / "distractor.json").unlink()
        with self.assertRaises(OSError):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_corpus_hash_and_metadata_mismatch(self):
        relative = "corpora/bank0/F_r16k16/across/sleep4/corpus.json"
        original = json.loads((self.source / relative).read_text())
        for key, value in (("sha", "wrong"), ("items_sha", "wrong"), ("bank", 1),
                           ("counter", "approx"), ("stats", {}), ("token_budget", None)):
            with self.subTest(key=key):
                self.write(relative, dict(original, **{key: value}))
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.destination.exists())

    def test_unknown_event_fails_even_with_valid_training_hash(self):
        relative = "corpora/bank0/F_r16k16/across/sleep4/corpus.json"
        corpus = json.loads((self.source / relative).read_text())
        corpus["corpus"][0]["event_ids"] = ["unknown"]
        self.write(relative, corpus)
        with self.assertRaisesRegex(ValueError, "unknown source event"):
            self.prepare()

    def test_generations_mismatch_and_mock_refused(self):
        relative = "corpora/bank0/CF_r16_b/across/sleep4/generations.json"
        original = json.loads((self.source / relative).read_text())
        for key, value in (("backend", "mock"), ("model", "other"), ("bank", 1),
                           ("events", {"event-0": {"lines": ["changed"] * 16}})):
            with self.subTest(key=key):
                self.write(relative, dict(original, **{key: value}))
                with self.assertRaises(ValueError):
                    prep.prepare_run(self.source, self.destination, 0, "CF_r16_b")
                self.assertFalse(self.destination.exists())

    def test_source_file_symlink_refused(self):
        target = self.source / "distractor.json"
        external = self.root / "outside.json"
        target.rename(external)
        target.symlink_to(external)
        with self.assertRaises(OSError):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_missing_generations_refused(self):
        (self.source / "corpora/bank0/CF_r16_b/across/sleep4/generations.json").unlink()
        with self.assertRaises(OSError):
            prep.prepare_run(self.source, self.destination, 0, "CF_r16_b")
        self.assertFalse(self.destination.exists())

    def test_destination_parent_symlink_refused(self):
        alias = self.root / "parent-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            prep.prepare_run(self.source, alias / "new", 2, "F_r16k16")

    def test_source_directory_and_root_symlinks_refused(self):
        banks = self.source / "banks"
        external = self.root / "outside-banks"
        banks.rename(external)
        banks.symlink_to(external, target_is_directory=True)
        with self.assertRaises(OSError):
            self.prepare()
        alias = self.root / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            prep.prepare_run(alias, self.destination, 2, "F_r16k16")

    def test_containment_and_traversal_refused(self):
        for destination in (self.source / "new", self.source / ".." / "escaped"):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                prep.prepare_run(self.source, destination, 2, "F_r16k16")
        with self.assertRaises(ValueError):
            prep.read_input(self.source, "../outside")

    def test_destination_symlink_refused(self):
        self.destination.symlink_to(self.root / "absent")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.prepare()

    def test_invalid_selections_and_training_seed(self):
        for banks in ([], [0, 0], [-1], [2]):
            with self.subTest(banks=banks), self.assertRaises(ValueError):
                self.prepare(banks=banks)
        with self.assertRaises(ValueError):
            prep.prepare_run(self.source, self.destination, -1, "F_r16k16")

    def test_cli_help_and_collision_exit(self):
        result = subprocess.run([sys.executable, "-B", str(HELPER), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--check-only", result.stdout)
        self.destination.mkdir()
        result = subprocess.run([sys.executable, "-B", str(HELPER), "--source", str(self.source),
                                 "--destination", str(self.destination), "--training-seed", "2",
                                 "--cell", "F_r16k16"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
