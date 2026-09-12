"""Synthetic native-ledger reductions only; no GPU or real-model claims."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import mini_sudoku_behavior_analysis as analysis
from organism_v6 import neutral_pair_custody as custody
from organism_v6.reasoning_gym_gym import BOOTSTRAP_PATH


class BehaviorAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.useful = self.root / "useful"
        self.corrupt = self.root / "corrupt"
        self.panel = list(analysis.EPISODE_IDS)
        self.source_snapshot = custody.source_snapshot()
        self.model_hashes = {"config.json": "a" * 64}
        self.make_pair(self.useful)
        self.make_pair(self.corrupt)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o755)
        if path.exists():
            path.chmod(0o644)
        path.write_text(json.dumps(value))

    def read(self, path):
        return json.loads(path.read_text())

    def make_pair(self, root):
        for condition in ("off", "on"):
            identity = dict(backend="vllm", model_input="/synthetic/model", adapter_input=None,
                            adapter_files={}, default_max_tokens=400, default_temperature=0.7)
            sources = {"model": "/synthetic/model"}
            hashes = {"model": self.model_hashes}
            if condition == "on":
                identity.update(adapter_input="/synthetic/adapter",
                                adapter_files={"adapter_model.safetensors": "b" * 64,
                                               "adapter_config.json": "d" * 64})
                sources["adapter"] = "/synthetic/adapter"
                hashes["adapter"] = identity["adapter_files"]
            config = dict(evidence_label="EVALUATION_ONLY", episode_ids=self.panel,
                          gen_seed=4242, seed_salt=91, budget_ticks=1, wake_max_tokens=400,
                          scratchpad_max_tokens=32, total_token_budget=20000, max_episodes=16,
                          birth_prompt=Path(BOOTSTRAP_PATH).read_text(), source_identity=identity,
                          sources=sources, hashes_before=hashes, code_hashes_before={},
                          gym_configuration={}, reasoning_gym_version="0.1.25", protected_roots=[],
                          probe_root=str(root), origin_verification="UNRESOLVED_SYNTHETIC_FIXTURE")
            directory = root / condition
            self.write(directory / "configuration.json", config)
            self.write(directory / "source_check.json", dict(evidence_label="EVALUATION_ONLY",
                       hashes_after=hashes, code_hashes_after={}))
            (directory / "generations.jsonl").write_text("")
            episodes = []
            for index, episode_id in enumerate(self.panel):
                name = f"episode_{index:04d}.jsonl"
                (directory / name).write_text("")
                episodes.append(dict(episode_id=episode_id, ledger=name, n_actions=0,
                                     summary=dict(episode_id=episode_id, best_score=0.0, n_acts=0)))
            self.write(directory / "results.json", dict(evidence_label="EVALUATION_ONLY", episodes=episodes))

    def action(self, episode_id, score=1.0, *, attempt=1, empty=False):
        verdict = "accepted" if score == 1 else "not accepted; partial credit" if score else "not accepted"
        return dict(kind="act", episode_id=episode_id, execution_id=f"{episode_id}/{attempt}", tick=1,
                    action="" if empty else "1 2 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1",
                    outcome=f"INVALID: attempt {attempt} was empty" if empty else
                            f"attempt {attempt}: verifier score {score:.2f} ({verdict})",
                    score=score, occurrence_id="synthetic-occurrence")

    def set_rows(self, root, condition, index, rows, best=None):
        directory = root / condition
        results = self.read(directory / "results.json")
        entry = results["episodes"][index]
        actions = [row for row in rows if row.get("kind") == "act"]
        entry["n_actions"] = entry["summary"]["n_acts"] = len(actions)
        entry["summary"]["best_score"] = max([0.0] + [row.get("score", 0.0) for row in actions]) if best is None else best
        (directory / entry["ledger"]).write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.write(directory / "results.json", results)

    def seal(self, root):
        receipts, receipt_hashes = {}, {}
        spec_hash = "c" * 64
        for index, condition in enumerate(("off", "on")):
            directory = root / condition
            manifest = {path.name: custody._digest(path) for path in directory.iterdir() if path.name != "manifest.json"}
            self.write(directory / "manifest.json", dict(evidence_label="EVALUATION_ONLY", sha256=manifest))
            receipt = dict(evidence_label="EVALUATION_ONLY", condition=condition, spec_sha256=spec_hash,
                           pid=1000+index, results_sha256=custody._digest(directory / "results.json"),
                           manifest_sha256=custody._digest(directory / "manifest.json"))
            receipt_path = root / f"{condition}_WORKER_DONE.json"
            self.write(receipt_path, receipt)
            receipts[condition] = receipt
            receipt_hashes[condition] = custody._digest(receipt_path)
        self.write(root / "PAIR_DONE.json", dict(evidence_label="EVALUATION_ONLY", spec_sha256=spec_hash,
                   workers=receipts, receipt_sha256=receipt_hashes, source_snapshot=self.source_snapshot))

    def reduce(self):
        return analysis.reduce_pairs(self.useful, self.corrupt)

    def test_no_action_keeps_denominator_and_marks_custody_unavailable(self):
        report = self.reduce()
        cell = report["pairs"]["useful"]["on"]
        self.assertEqual(cell["summary"]["denominator"], 16)
        self.assertEqual(cell["summary"]["first_act_solved_count"], 0)
        self.assertEqual(cell["first_act_status_counts"], {"missing": 16})
        self.assertEqual(report["pairs"]["useful"]["custody"]["status"], "NOT_AVAILABLE")

    def test_empty_first_act_is_not_replaced_by_later_correct_act(self):
        episode_id = self.panel[0]
        self.set_rows(self.useful, "on", 0, [self.action(episode_id, 0, empty=True),
                                             self.action(episode_id, attempt=2)])
        cell = self.reduce()["pairs"]["useful"]["on"]
        self.assertEqual(cell["summary"]["first_act_solved_count"], 0)
        self.assertEqual(cell["episodes"][0]["first_act"]["status"], "unmeasured")
        self.assertEqual(cell["episodes"][0]["metrics"]["native_best"], 1)
        self.assertEqual(cell["summary"]["n_acts_total"], 2)

    def test_unmeasured_non_none_score_is_zero_filled(self):
        episode_id = self.panel[0]
        self.set_rows(self.useful, "on", 0, [self.action(episode_id, 0.75, empty=True)], best=0)
        with patch.object(analysis, "facts_from_act",
                          return_value=SimpleNamespace(measured=False, score=0.75)):
            cell = self.reduce()["pairs"]["useful"]["on"]
        row = cell["episodes"][0]
        self.assertEqual(row["first_act"]["recorded_score"], 0.75)
        self.assertIsNone(row["first_act"]["native_score"])
        self.assertEqual(row["metrics"]["first_act_native_score_zero_filled"], 0.0)
        self.assertEqual(cell["summary"]["first_act_native_score_mean_zero_filled"], 0.0)
        self.assertEqual(row["metrics"]["first_act_solved"], 0)

    def test_invalid_first_feedback_then_correct_is_zero(self):
        episode_id = self.panel[0]
        invalid = self.action(episode_id)
        invalid["outcome"] = "INVALID: malformed submission"
        self.set_rows(self.useful, "on", 0, [invalid, self.action(episode_id, attempt=2)])
        row = self.reduce()["pairs"]["useful"]["on"]["episodes"][0]
        self.assertEqual(row["first_act"]["status"], "invalid")
        self.assertEqual(row["metrics"]["first_act_solved"], 0)
        self.assertEqual(row["metrics"]["first_act_native_score_zero_filled"], 0.0)

    def test_empty_action_with_falsely_accepted_feedback_is_invalid(self):
        episode_id = self.panel[0]
        invalid = self.action(episode_id)
        invalid["action"] = ""
        self.set_rows(self.useful, "on", 0, [invalid, self.action(episode_id, attempt=2)])
        row = self.reduce()["pairs"]["useful"]["on"]["episodes"][0]
        self.assertEqual(row["first_act"]["status"], "invalid")
        self.assertIsNone(row["first_act"]["native_score"])
        self.assertEqual(row["metrics"]["first_act_solved"], 0)

    def test_multiact_keeps_first_partial_and_native_best(self):
        episode_id = self.panel[0]
        self.set_rows(self.useful, "on", 0, [dict(kind="thought", episode_id=episode_id, note="ACT: not evidence"),
                                             self.action(episode_id, 0.225), self.action(episode_id, attempt=2)])
        row = self.reduce()["pairs"]["useful"]["on"]["episodes"][0]
        self.assertEqual(row["first_act"]["record_index"], 1)
        self.assertEqual(row["first_act"]["native_score"], 0.225)
        self.assertEqual(row["metrics"]["first_act_solved"], 0)
        self.assertEqual(row["metrics"]["native_best"], 1)

    def test_cross_material_deltas_include_baseline_adjustment(self):
        self.set_rows(self.useful, "on", 0, [self.action(self.panel[0])])
        self.set_rows(self.useful, "off", 1, [self.action(self.panel[1])])
        report = self.reduce()
        contrasts = report["useful_minus_corrupt"]
        self.assertEqual(contrasts["on"]["summary"]["first_act_solved_count"], 1)
        self.assertEqual(contrasts["on"]["summary"]["first_act_solved_rate"], 1/16)
        self.assertEqual(contrasts["on_minus_off"]["summary"]["first_act_solved_count"], 0)
        self.assertEqual(contrasts["on_minus_off"]["episodes"][1]["metrics"]["first_act_solved"], -1)

    def test_different_episode_order_is_joined_by_id(self):
        self.set_rows(self.corrupt, "on", 0, [self.action(self.panel[0])])
        directory = self.corrupt / "on"
        results = self.read(directory / "results.json")
        results["episodes"].reverse()
        self.write(directory / "results.json", results)
        config = self.read(directory / "configuration.json")
        config["episode_ids"].reverse()
        self.write(directory / "configuration.json", config)
        row = self.reduce()["useful_minus_corrupt"]["on"]["episodes"][0]
        self.assertEqual(row["episode_id"], self.panel[0])
        self.assertEqual(row["metrics"]["first_act_solved"], -1)

    def test_missing_ledger_or_results_fails(self):
        for filename in ("episode_0000.jsonl", "results.json"):
            with self.subTest(filename=filename):
                path = self.useful / "on" / filename
                original = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ValueError, "missing"):
                    self.reduce()
                path.write_bytes(original)

    def test_ledger_episode_mismatch_fails(self):
        self.set_rows(self.useful, "on", 0, [self.action(self.panel[1])])
        with self.assertRaisesRegex(ValueError, "episode mismatch"):
            self.reduce()

    def test_results_episode_mismatch_fails(self):
        path = self.useful / "on/results.json"
        results = self.read(path)
        results["episodes"][0]["episode_id"] = self.panel[1]
        self.write(path, results)
        with self.assertRaisesRegex(ValueError, "episode panel mismatch"):
            self.reduce()

    def test_changed_decoding_seed_rejects_paired_comparison(self):
        path = self.corrupt / "on/configuration.json"
        config = self.read(path)
        config["gen_seed"] += 1
        self.write(path, config)
        with self.assertRaisesRegex(ValueError, "paired evaluation settings"):
            self.reduce()

    def test_changed_temperature_rejects_paired_comparison(self):
        path = self.corrupt / "on/configuration.json"
        config = self.read(path)
        config["source_identity"]["default_temperature"] = 0.2
        self.write(path, config)
        with self.assertRaisesRegex(ValueError, "paired evaluation settings"):
            self.reduce()

    def test_failed_source_check_rejects_even_without_done(self):
        path = self.useful / "on/source_check.json"
        check = self.read(path)
        check["unchanged"] = False
        self.write(path, check)
        with self.assertRaisesRegex(ValueError, "failed source check"):
            self.reduce()

    def test_done_custody_uses_real_helper_without_origin_authentication(self):
        self.seal(self.useful)
        self.seal(self.corrupt)
        report = self.reduce()
        self.assertEqual(report["pairs"]["useful"]["custody"]["status"], "ARTIFACT_CUSTODY_VALIDATED")
        self.assertEqual(report["pairs"]["useful"]["on"]["recorded_sources"]["hashes_before"]["model"], self.model_hashes)
        self.assertIn(str(self.useful / "PAIR_DONE.json"), report["input_sha256"])

    def test_real_native_probe_producer_fixture_reduces(self):
        from test_reasoning_neutral_probe import FixtureBackend, FixtureGym, NeutralProbeTests
        from organism_v6.reasoning_neutral_probe import run_probe

        fixture = NeutralProbeTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        roots = [fixture.probes / "useful", fixture.probes / "corrupt"]
        for root in roots:
            root.mkdir()
            for condition in ("off", "on"):
                options = dict(fixture.options, output_dir=root / condition,
                               episode_ids=self.panel, max_episodes=16,
                               total_token_budget=10000, seed_salt=91)
                if condition == "off":
                    options.update(adapter_path=None, expected_adapter_hashes={})
                gym = FixtureGym()
                gym.train_families = ["mini_sudoku"]
                gym.seed_ranges = {"canary": (1900000, 1900100)}
                gym.score = 1.0
                backend = FixtureBackend(str(options["model_path"]),
                                         str(options["adapter_path"]) if options["adapter_path"] else None)
                run_probe(backend, gym, **options)
            self.seal(root)
        report = analysis.reduce_pairs(*roots)
        self.assertEqual(report["pairs"]["useful"]["on"]["summary"]["first_act_solved_count"], 16)
        self.assertEqual(report["useful_minus_corrupt"]["on"]["summary"]["first_act_solved_count"], 0)

    def test_missing_file_does_not_publish_output(self):
        (self.useful / "off/episode_0000.jsonl").unlink()
        output = self.root / "failed-analysis.json"
        with self.assertRaisesRegex(ValueError, "missing"):
            analysis.write_report(self.useful, self.corrupt, output)
        self.assertFalse(output.exists())

    def test_sealed_ledger_tampering_fails(self):
        self.seal(self.useful)
        (self.useful / "on/episode_0000.jsonl").write_text("{}\n")
        with self.assertRaisesRegex(ValueError, "artifact digest"):
            self.reduce()

    def test_bad_done_receipt_hash_fails(self):
        self.seal(self.useful)
        path = self.useful / "PAIR_DONE.json"
        done = self.read(path)
        done["receipt_sha256"]["on"] = "0" * 64
        self.write(path, done)
        with self.assertRaisesRegex(ValueError, "receipt hash"):
            self.reduce()

    def test_pair_failed_is_not_reduced(self):
        self.write(self.useful / "PAIR_FAILED.json", {})
        with self.assertRaisesRegex(ValueError, "pair failed"):
            self.reduce()

    def test_new_output_cli_preserves_inputs_and_refuses_overwrite(self):
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                  for root in (self.useful, self.corrupt) for path in root.rglob("*") if path.is_file()}
        output = self.root / "analysis.json"
        arguments = ["--useful-pair", str(self.useful), "--corrupt-pair", str(self.corrupt),
                     "--output-new", str(output)]
        analysis.main(arguments)
        self.assertEqual(self.read(output)["episode_ids"], self.panel)
        for name, expected in before.items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), expected)
        with self.assertRaisesRegex(ValueError, "already exists"):
            analysis.main(arguments)

    def test_output_inside_evidence_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside input"):
            analysis.write_report(self.useful, self.corrupt, self.useful / "analysis.json")


if __name__ == "__main__":
    unittest.main()
