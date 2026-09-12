"""CPU-only campaign analysis tests using small synthetic paired-source evals."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from gpu import prepare_memory_seed_run as prepare

HELPER = ROOT / "research_notes/analysis/astra_seed_campaign.py"
SPEC = importlib.util.spec_from_file_location("astra_seed_campaign", HELPER)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class AstraSeedCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.write(self.source / "manifest.json", {
            "seed": 1, "n_banks": 1, "token_budget": 65536, "counter": "hf",
            "model": prepare.BASE_MODEL, "scorer": "HFScorer", "synthetic": True,
            "lora": {"rank": 8, "epochs": 3, "lr": 0.0001}})
        self.write(self.source / "distractor.json", {"text": "Synthetic text", "counter": "hf", "synthetic": True})
        self.write(self.source / "banks/bank0.json", {
            "bank": 0, "seed": 1, "synthetic": True, "events": [{"event_id": "event-1"}],
            "owners": [{"id": "exposed", "dose": 16, "colour": "red"},
                       {"id": "unexposed", "dose": 0, "colour": "red"}]})
        self.sha = prepare.short_hash([("Owner red", 1.0, False)])
        self.write(self.source / "corpora/bank0/F_r16k16/across/sleep4/corpus.json", {
            "bank": 0, "arm": "across", "sleep": 4, "writer": "occurrences", "representation": "frames",
            "shuffled": False, "ordering": "chronological", "counter": "hf", "synthetic": True,
            "epochs": 3, "frame_forms": 16, "frame_repeats": 16, "token_budget": 250000,
            "sha": self.sha, "items_sha": self.sha, "stats": {"n_items": 1, "token_budget": 250000},
            "corpus": [{"context": "Owner ", "target": "red", "chat": False, "shuffled": False,
                        "weight": 1.0, "mask_context": False, "kind": "fact", "event_ids": ["event-1"]}]})
        self.entry = self.make_entry("run2", 2)

    def write(self, path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o644)
        path.write_text(json.dumps(document))

    def update(self, path, **changes):
        document = json.loads(Path(path).read_text())
        document.update(changes)
        self.write(Path(path), document)

    def cue(self, kind, owner="exposed", dose=16, on=0.2):
        return {"kind": kind, "form": kind, "owner": owner, "dose": dose, "a": "red",
                "OFF": {"mass": 1.0, "p_raw": {"red": 0.2, "blue": 0.8}},
                "ON": {"mass": 1.0, "p_raw": {"red": on, "blue": 1 - on}}}

    def make_entry(self, name, seed):
        destination = self.root / name
        prepare.prepare_run(self.source, destination, seed, "F_r16k16")
        adapter = destination / "adapters/bank0/F_r16k16/across/sleep4/r8"
        training = adapter / "train_meta.json"
        self.write(training, {"model": prepare.BASE_MODEL, "synthetic": True, "measure_only": False,
                             "seed": seed, "rank": 8, "epochs": 3, "lr": 0.0001,
                             "corpus_sha": self.sha, "items_sha": self.sha, "ordering": "chronological"})
        (adapter / "DONE").write_text("ok\n")
        evaluation = destination / "eval/bank0__F_r16k16__across__sleep4__r8__lam1.json"
        self.write(evaluation, {"bank": 0, "model": "hf", "synthetic": True, "lam": 1.0,
                               "adapter": str(adapter), "meta": {"cell": "F_r16k16", "arm": "across", "sleep": 4, "rank": 8},
                               "adapter_meta": {"rank": 8, "corpus_sha": self.sha, "items_sha": self.sha,
                                                "ordering": "chronological"},
                               "cues": [self.cue("frame", on=0.8), self.cue("frame", "unexposed", 0),
                                        self.cue("frame_similar"), self.cue("frame_bicycle")]})
        return [str(evaluation), str(training), str(destination / prepare.RECEIPT)]

    def analyze(self, entry=None):
        return analysis.analyze_entry(*(entry or self.entry))

    def test_conditional_metrics_existing_binding_definition_and_counts(self):
        result = self.analyze()
        self.assertEqual(result["optimizer_seed"], 2)
        self.assertEqual(result["source_bank_seed"], 1)
        self.assertEqual(result["dose16"]["frame"]["cue_count"], 1)
        self.assertAlmostEqual(result["dose16"]["frame"]["conditional_p_off"], 0.2)
        self.assertAlmostEqual(result["dose16"]["frame"]["conditional_p_on"], 0.8)
        self.assertEqual(result["dose16"]["frame"]["mass_on"], 1.0)
        self.assertEqual(result["source_hash_compatibility"]["status"], "compatible")
        self.assertTrue(result["binding"]["passed"])
        self.assertEqual(result["binding"]["frame_spill"], 0)
        self.assertEqual(result["binding"]["spill_threshold"], analysis.definitions.GATES["frame_spill"])
        self.assertEqual(result["binding"]["I_d_frame"]["n"], 1)

    def test_null_and_zero_mass_are_unavailable_not_zero_imputed(self):
        original = json.loads(Path(self.entry[0]).read_text())
        for mass in (None, 0.0):
            with self.subTest(mass=mass):
                document = copy.deepcopy(original)
                document["cues"][0]["ON"]["mass"] = mass
                self.write(Path(self.entry[0]), document)
                result = self.analyze()
                self.assertIsNone(result["dose16"]["frame"]["conditional_p_on"])
                self.assertEqual(result["dose16"]["frame"]["mass_on"], mass)
                self.assertEqual(result["dose16"]["frame"]["valid_on_count"], 0)
                self.assertIsNone(result["binding"]["passed"])
                json.dumps(result, allow_nan=False)

    def test_positive_mass_matches_frame_summary_semantics(self):
        side = {"mass": 0.01, "p_raw": {"red": 0.008, "blue": 0.002}}
        self.assertAlmostEqual(analysis.conditional(side, "red"), 0.8)
        self.assertIsNone(analysis.conditional(side, "missing"))

    def test_empty_eval_never_passes(self):
        self.update(self.entry[0], cues=[])
        result = self.analyze()
        self.assertEqual(result["eval_cue_count"], 0)
        self.assertEqual(result["dose16"]["frame"]["cue_count"], 0)
        self.assertIsNone(result["dose16"]["frame"]["conditional_p_on"])
        self.assertIsNone(result["binding"]["passed"])

    def test_missing_controls_prevent_pass(self):
        document = json.loads(Path(self.entry[0]).read_text())
        document["cues"] = [cue for cue in document["cues"] if cue["kind"] != "frame_bicycle"]
        self.write(Path(self.entry[0]), document)
        result = self.analyze()
        self.assertIsNone(result["binding"]["passed"])
        self.assertEqual(result["dose16"]["frame_bicycle"]["status"], "unavailable")

    def test_missing_receipt_preserves_historical_metrics_not_gate_success(self):
        result = self.analyze([self.entry[0], self.entry[1], "-"])
        self.assertEqual(result["source_hash_compatibility"]["status"], "compatible")
        self.assertEqual(result["dose16"]["frame"]["conditional_p_on"], 0.8)
        self.assertEqual(result["optimizer_seed"], 2)
        self.assertIsNone(result["binding"]["passed"])
        self.assertIn("run receipt", result["unavailable_controls"])

    def test_missing_training_is_unavailable(self):
        for receipt in ("-", self.entry[2]):
            with self.subTest(receipt=receipt):
                result = self.analyze([self.entry[0], "-", receipt])
                self.assertEqual(result["source_hash_compatibility"]["status"], "unavailable")
                self.assertIsNone(result["optimizer_seed"])
                self.assertIsNone(result["binding"]["passed"])

    def test_existing_spill_threshold_produces_failure_not_unavailable(self):
        document = json.loads(Path(self.entry[0]).read_text())
        document["cues"][2]["ON"]["p_raw"] = {"red": 0.4, "blue": 0.6}
        self.write(Path(self.entry[0]), document)
        result = self.analyze()
        self.assertFalse(result["binding"]["passed"])
        self.assertIsNotNone(result["binding"]["passed"])
        self.assertAlmostEqual(result["binding"]["frame_spill"], 0.2 / 3)

    def test_missing_hash_metadata_is_unavailable(self):
        metadata = json.loads(Path(self.entry[1]).read_text())
        del metadata["corpus_sha"]
        self.write(Path(self.entry[1]), metadata)
        result = self.analyze()
        self.assertEqual(result["source_hash_compatibility"]["status"], "unavailable")
        self.assertIsNone(result["binding"]["passed"])

    def test_receipt_hash_seed_and_adapter_mismatch(self):
        original = json.loads(Path(self.entry[2]).read_text())
        cases = [dict(original, training_seed=0), dict(original, destination_run="/different")]
        changed = copy.deepcopy(original)
        changed["inputs"]["banks/bank0.json"]["sha256"] = "wrong"
        cases.append(changed)
        for receipt in cases:
            with self.subTest(receipt=receipt["training_seed"]):
                self.write(Path(self.entry[2]), receipt)
                result = self.analyze()
                self.assertEqual(result["source_hash_compatibility"]["status"], "mismatch")
                self.assertIsNone(result["binding"]["passed"])

    def test_eval_training_corpus_mismatch(self):
        self.update(self.entry[1], corpus_sha="wrong")
        result = self.analyze()
        self.assertEqual(result["source_hash_compatibility"]["status"], "mismatch")
        self.assertIn("training corpus_sha", result["source_hash_compatibility"]["mismatches"])

    def test_profile_seed_zero_is_not_optimizer_seed(self):
        self.update(self.entry[1], seed=0, measure_only=True)
        result = self.analyze()
        self.assertFalse(result["fit_complete"])
        self.assertIsNone(result["optimizer_seed"])
        self.assertIsNone(result["binding"]["passed"])

    def test_missing_completion_marker_is_not_fit(self):
        Path(self.entry[1]).with_name("DONE").unlink()
        result = self.analyze()
        self.assertFalse(result["fit_complete"])
        self.assertIsNone(result["binding"]["passed"])

    def test_duplicate_cues_do_not_multiply_success(self):
        document = json.loads(Path(self.entry[0]).read_text())
        document["cues"].append(copy.deepcopy(document["cues"][0]))
        self.write(Path(self.entry[0]), document)
        self.assertIsNone(self.analyze()["binding"]["passed"])

    def test_source_cells_group_optimizer_seeds_without_pooling(self):
        other = self.make_entry("run3", 3)
        report = analysis.analyze_campaign([self.entry, other])
        self.assertEqual(report["counts"]["entries"], 2)
        self.assertEqual(len(report["paired_source_cells"]), 1)
        cell = report["paired_source_cells"][0]["cells"][0]
        self.assertEqual(cell["optimizer_seeds"], [2, 3])
        self.assertEqual(cell["unique_optimizer_seed_count"], 2)
        self.assertEqual(cell["unavailable_reference_optimizer_seeds"], [0, 1])
        self.assertNotIn("pooled", report)
        with self.assertRaises(ValueError):
            analysis.analyze_campaign([self.entry, self.entry])

    def test_changed_source_bank_cannot_pair(self):
        other = self.make_entry("run3", 3)
        bank_path = Path(other[2]).parent / "banks/bank0.json"
        self.update(bank_path, extra_diagnostic="different bank bytes")
        report = analysis.analyze_campaign([self.entry, other])
        self.assertEqual(report["rows"][1]["source_hash_compatibility"]["status"], "mismatch")
        self.assertEqual(report["paired_source_cells"][0]["cells"][0]["optimizer_seeds"], [2])

    def test_cli_json_and_missing_eval(self):
        result = subprocess.run([sys.executable, "-B", str(HELPER), "--entry", *self.entry],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["counts"]["completed_fits"], 1)
        missing = self.analyze([str(self.root / "missing.json"), "-", "-"])
        self.assertIsNone(missing["binding"]["passed"])
        self.assertEqual(missing["eval_cue_count"], 0)


if __name__ == "__main__":
    unittest.main()
