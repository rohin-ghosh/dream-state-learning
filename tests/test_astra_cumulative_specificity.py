"""Native-shaped captured JSON fixtures only; no native runs or weight access."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

from gpu import astra_cumulative_specificity as specificity


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_side(colour, conditional=.25, mass=.4, abstain=.02):
    normalized = {answer: conditional if answer == colour else (1 - conditional) / 3
                  for answer in specificity.COLOURS}
    raw = {answer: value * mass for answer, value in normalized.items()}
    return dict(p_raw=raw, p_norm=normalized, mass=sum(raw.values()),
                logp={answer: math.log(value) if value else -1000.0 for answer, value in raw.items()},
                p_abstain=abstain)


class SpecificityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "captured"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "specificity.json"
        self.cues = [dict(cue_id=f"fact|OLD{index}|p1", kind="fact", owner=f"OLD{index}",
                          a="red", dose=16, form="p1", context="none", prompt="What colour?",
                          candidates={colour: [colour, colour.title()] for colour in specificity.COLOURS},
                          cand_tokens={colour: [1, 1] for colour in specificity.COLOURS})
                     for index in range(1313)]
        self.bank = dict(seed=1, bank=0, owners=[dict(id="OLD0", dose=16)],
                         interference=dict(events=[]), schedule=dict(across={}))
        for index in range(32):
            owner = f"J{index:03}"
            colour = specificity.COLOURS[index % 4]
            for occurrence in range(4):
                event_id = f"b0-{owner}-i{occurrence:02}"
                self.bank["interference"]["events"].append(dict(
                    event_id=event_id, kind="interference", owner=owner, colour=colour, session=5))
                self.bank["schedule"]["across"][event_id] = 5
            for kind, attribute in (("new_frame", "car"), ("new_bicycle", "bicycle")):
                self.cues.append(dict(cue_id=f"{kind}|{owner}", kind=kind, owner=owner, a=colour,
                                      dose=4, form=kind, context="none", abstain=[" not"],
                                      prompt=f"Owner {owner}'s {attribute} is",
                                      candidates={answer: [f" {answer}", f" {answer.title()}"]
                                                  for answer in specificity.COLOURS},
                                      cand_tokens={answer: [1, 1] for answer in specificity.COLOURS}))
        self.evaluations = {}
        for state in specificity.READS:
            rows = []
            for cue in self.cues:
                row = {key: copy.deepcopy(value) for key, value in cue.items()
                       if key not in ("prompt", "candidates")}
                row["OFF"] = native_side(row["a"])
                learned = state in ("AN", "A2") and cue["kind"] == "new_frame"
                row["ON"] = native_side(row["a"], .75 if learned else .25, .8 if learned else .4)
                rows.append(row)
            self.evaluations[state] = dict(tag=state, bank=0, lam=1.0, n_cues=len(rows), cues=rows,
                                           adapter_meta={}, scorer_calls=None, boundary_straddles=512,
                                           work={}, measured_work={}, template_check=True,
                                           abstain_check=dict(ok=True))
        self.write_capture()

    def save(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n")
        return file_sha(path)

    def load(self, relative):
        return json.loads((self.root / relative).read_text())

    def write_capture(self):
        files = {"cues.json": self.save("cues.json", self.cues),
                 "bank.json": self.save("bank.json", self.bank)}
        adapter_hashes = {name: {"adapter_model.safetensors": str(index + 1) * 64}
                          for index, name in enumerate(("A1", "AN", "A2"))}
        native_root = "/unavailable-native-node/cumulative_attempt1"
        manifest = dict(root=native_root, files=files,
                        sources={path: "a" * 64 for path in specificity.SOURCE_PATHS},
                        pins=dict(a1=adapter_hashes["A1"], model={"weights": "f" * 64}),
                        stages=list(specificity.STAGES), cap_seconds=5400,
                        starting_state=specificity.STARTING_STATE,
                        lineage=dict(A1="Fit(base, OLD)", AN="Fit(base, NEW)", A2="Fit(base, OLD+NEW)"))
        manifest_sha = self.save("manifest.json", manifest)
        started = dict(manifest_sha256=manifest_sha, device="0", started_unix=1000,
                       deadline_unix=6400, lease_cutoff_unix=10000)
        self.save("RUN_STARTED.json", started)
        records, fits = [], {}
        for index, stage in enumerate(specificity.STAGES):
            pid = index + 100
            job = dict(stage=stage, manifest_sha256=manifest_sha, device="0", deadline_unix=6355,
                       timeout_seconds=5355)
            job_sha = self.save(f"{stage}.job.json", job)
            adapter = "A1" if stage.startswith("A1_") else stage.removeprefix("fit_")
            done = dict(stage=stage, manifest_sha256=manifest_sha, pid=pid, device="0",
                        starting_state=specificity.STARTING_STATE, job_sha256=job_sha,
                        adapter_hashes=adapter_hashes[adapter], worker_seconds=10)
            if stage.startswith("fit_"):
                done["train_meta"] = dict(steps=1536 if stage == "fit_AN" else 11229,
                                          recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
                                          model="/unavailable-native-node/base", final_loss=.1)
                fits[stage] = done["train_meta"]
            else:
                done["eval_sha256"] = self.save(f"stages/{stage}/eval.json", self.evaluations[stage])
            done_sha = self.save(f"stages/{stage}/DONE.json", done)
            self.save(f"{stage}.cleanup.json", dict(pid=pid, device="0", owned_group_empty=True,
                                                   gpu_processes_absent=True, reservation_release_verified=True))
            records.append(dict(stage=stage, pid=pid, done_sha256=done_sha, supervised_seconds=11))
        finished = dict(completed=True, failure=None, manifest_sha256=manifest_sha, records=records,
                        reserved_gpu_seconds=100, deadline_unix=6400, finished_unix=1100)
        self.save("RUN_FINISHED.json", finished)
        self.save("report.json", dict(manifest_sha256=manifest_sha, sources=manifest["sources"],
                  pins=manifest["pins"], lineage=manifest["lineage"], starting_state=specificity.STARTING_STATE,
                  cost=dict(run=finished, fits=fits), native_old_summaries={}, native_old_gates={},
                  raw_evaluations={state: f"{native_root}/stages/{state}/eval.json" for state in specificity.READS}))

    def run_supplement(self):
        return specificity.supplement(self.root, self.output)

    def test_complete_capture_metrics_counts_and_input_preservation(self):
        before = {str(path): file_sha(path) for path in self.root.rglob("*.json")}
        result = self.run_supplement()
        self.assertEqual(set(result["states"]), set(specificity.READS))
        for state in specificity.READS:
            report = result["states"][state]
            self.assertEqual(report["n_pairs"], 32)
            self.assertEqual(len({pair["owner"] for pair in report["pairs"]}), 32)
            self.assertEqual(report["means"]["frame"]["loggain"]["n"], 32)
            pair = report["pairs"][0]
            self.assertAlmostEqual(pair["frame"]["OFF"]["conditional_target_probability"], .25)
            if state in ("AN", "A2"):
                self.assertAlmostEqual(pair["frame"]["probability_gain"], .5)
                self.assertAlmostEqual(pair["frame"]["loggain"], math.log(3))
                self.assertAlmostEqual(pair["frame"]["ON"]["raw_colour_mass"], .8)
                self.assertAlmostEqual(pair["frame_minus_bicycle"]["ON"]["conditional_target_probability"], .5)
                self.assertAlmostEqual(pair["frame_minus_bicycle"]["loggain"], math.log(3))
            self.assertEqual(pair["bicycle"]["ON"]["p_abstain"], .02)
        self.assertEqual(before, {str(path): file_sha(path) for path in self.root.rglob("*.json")})
        self.assertEqual(json.loads(self.output.read_text()), result)
        self.assertEqual(result["captured_file_sha256"]["report.json"], before[str(self.root / "report.json")])

    def test_bicycle_spill_has_car_gain_but_zero_paired_specificity(self):
        for row in self.evaluations["A2"]["cues"][1313:]:
            row["ON"] = native_side(row["a"], .9, .8)
        self.write_capture()
        result = self.run_supplement()["states"]["A2"]
        self.assertAlmostEqual(result["means"]["frame"]["probability_gain"]["mean"], .65)
        self.assertAlmostEqual(result["means"]["bicycle"]["probability_gain"]["mean"], .65)
        self.assertAlmostEqual(result["means"]["frame_minus_bicycle"]["loggain"]["mean"], 0)
        self.assertEqual(result["means"]["frame_minus_bicycle"]["probability_gain"], dict(mean=0, n=32))
        self.assertTrue(all(pair["frame_minus_bicycle"]["ON"]["conditional_target_probability"] == 0
                            for pair in result["pairs"]))
        self.assertNotIn("retention_ratio", self.output.read_text())
        self.assertNotIn('"passed"', self.output.read_text())

    def test_missing_duplicate_reordered_and_wrong_label_fail(self):
        original = copy.deepcopy(self.evaluations["AN"])
        for corruption in ("missing", "duplicate", "reordered", "label"):
            with self.subTest(corruption=corruption):
                evaluation = copy.deepcopy(original)
                rows = evaluation["cues"]
                if corruption == "missing":
                    rows.pop()
                elif corruption == "duplicate":
                    rows[-1] = copy.deepcopy(rows[-2])
                elif corruption == "reordered":
                    rows[-1], rows[-2] = rows[-2], rows[-1]
                else:
                    rows[-1]["a"] = "wrong"
                self.evaluations["AN"] = evaluation
                self.write_capture()
                with self.assertRaisesRegex(ValueError, "cue"):
                    self.run_supplement()
                self.assertFalse(self.output.exists())

    def test_prepared_label_and_source_disagreement_fail(self):
        self.cues[-1]["a"] = "wrong"
        self.write_capture()
        with self.assertRaisesRegex(ValueError, "label"):
            self.run_supplement()

    def test_prepared_duplicate_cue_fails(self):
        self.cues[-1] = copy.deepcopy(self.cues[-2])
        self.write_capture()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_supplement()

    def test_nonfinite_probability_mass_abstention_and_logp_fail(self):
        original = copy.deepcopy(self.evaluations["A2"])
        for field, value in (("p_raw", float("nan")), ("mass", float("inf")),
                             ("p_abstain", -float("inf")), ("logp", float("nan"))):
            with self.subTest(field=field):
                self.evaluations["A2"] = copy.deepcopy(original)
                row = self.evaluations["A2"]["cues"][-1]
                if field in ("p_raw", "logp"):
                    row["ON"][field][row["a"]] = value
                else:
                    row["ON"][field] = value
                self.write_capture()
                with self.assertRaisesRegex(ValueError, "nonfinite"):
                    self.run_supplement()
                self.assertFalse(self.output.exists())

    def test_invalid_finite_probabilities_and_mass_fail(self):
        for field, value in (("mass", .1), ("p_abstain", 1.1), ("p_abstain", True)):
            with self.subTest(field=field, value=value):
                side = native_side("red")
                side[field] = value
                with self.assertRaises(ValueError):
                    specificity.side_metrics(side, "red")

    def test_zero_target_or_mass_is_undefined_not_epsilon_rescued(self):
        for row in self.evaluations["A2"]["cues"][1313:]:
            row["ON"] = native_side(row["a"], 0, .4 if row["kind"] == "new_frame" else 0)
            if row["kind"] == "new_bicycle":
                row["ON"]["p_norm"] = {colour: .25 for colour in specificity.COLOURS}
        self.write_capture()
        report = self.run_supplement()["states"]["A2"]
        self.assertEqual(report["means"]["frame"]["ON"]["conditional_target_probability"], dict(mean=0, n=32))
        self.assertEqual(report["means"]["frame"]["loggain"], dict(mean=None, n=0))
        self.assertEqual(report["means"]["bicycle"]["ON"]["conditional_target_probability"], dict(mean=None, n=0))
        self.assertEqual(report["means"]["frame_minus_bicycle"]["probability_gain"], dict(mean=None, n=0))

    def test_native_probability_roundoff_is_preserved(self):
        side = native_side("red", .75, 1)
        side["p_raw"] = {colour: value * (1 + 1e-8) for colour, value in side["p_raw"].items()}
        side["mass"] = sum(side["p_raw"].values())
        metrics = specificity.side_metrics(side, "red")
        self.assertEqual(metrics["raw_colour_mass"], side["mass"])
        self.assertGreater(metrics["raw_colour_mass"], 1)
        self.assertAlmostEqual(metrics["conditional_target_probability"], .75)

    def test_aggregate_counts_exclude_only_undefined_values(self):
        result = specificity.means([dict(loggain=None, probability_gain=-.25),
                                    dict(loggain=math.log(3), probability_gain=.5)])
        self.assertEqual(result["loggain"], dict(mean=math.log(3), n=1))
        self.assertEqual(result["probability_gain"], dict(mean=.125, n=2))

    def test_existing_output_and_primary_report_never_overwritten(self):
        self.output.write_text("preserve this\n")
        with self.assertRaises(FileExistsError):
            self.run_supplement()
        self.assertEqual(self.output.read_text(), "preserve this\n")
        before = file_sha(self.root / "report.json")
        with self.assertRaises(FileExistsError):
            specificity.supplement(self.root, self.root / "report.json")
        self.assertEqual(file_sha(self.root / "report.json"), before)

    def test_missing_primary_or_stage_fails_without_output(self):
        for relative in ("report.json", "stages/fit_AN/DONE.json"):
            with self.subTest(relative=relative):
                self.write_capture()
                (self.root / relative).unlink()
                with self.assertRaises(FileNotFoundError):
                    self.run_supplement()
                self.assertFalse(self.output.exists())

    def test_incomplete_run_and_cleanup_fail(self):
        for relative, field in (("RUN_FINISHED.json", "completed"),
                                ("A1_after.cleanup.json", "reservation_release_verified")):
            with self.subTest(relative=relative):
                self.write_capture()
                receipt = self.load(relative)
                receipt[field] = False
                self.save(relative, receipt)
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    self.run_supplement()

    def test_source_hash_mismatch_fails(self):
        report = self.load("report.json")
        report["sources"]["organism_v6/memory_dose.py"] = "b" * 64
        self.save("report.json", report)
        with self.assertRaisesRegex(ValueError, "source hashes"):
            self.run_supplement()

    def test_hash_drift_in_prepared_stage_and_evaluation_fails(self):
        for relative in ("cues.json", "stages/fit_A2/DONE.json", "stages/AN/eval.json"):
            with self.subTest(relative=relative):
                self.write_capture()
                with (self.root / relative).open("a") as target:
                    target.write(" ")
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    self.run_supplement()

    def test_primary_must_match_finished_receipt(self):
        report = self.load("report.json")
        report["cost"]["run"]["reserved_gpu_seconds"] = 101
        self.save("report.json", report)
        with self.assertRaisesRegex(ValueError, "completion receipt"):
            self.run_supplement()

    def test_cli_uses_captured_root_and_new_output(self):
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            specificity.main(["--root", str(self.root), "--output", str(self.output)])
        self.assertIn("report-only", printed.getvalue())
        self.assertTrue(self.output.is_file())


if __name__ == "__main__":
    unittest.main()
