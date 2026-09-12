"""Synthetic CPU fixtures only: no native panel generation, model load or GPU."""
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import fresh_behavior_panel as fresh
from organism_v6 import mini_sudoku_behavior_analysis as analysis
from organism_v6 import neutral_pair_custody as custody
from organism_v6 import reasoning_gym_gym as native
from organism_v6.model_backend import configured_generation_identity


BOARDS = fresh._solutions()


def record(episode_id, board):
    grid = [list(row) for row in board]
    answer = "\n".join(" ".join(map(str, row)) for row in grid)
    entry = dict(question="Complete this board:\n" + answer, answer=answer,
                 metadata=dict(puzzle=grid, solution=grid, num_empty=0))
    return dict(episode_id=episode_id, entry=entry, puzzle=grid, solution=grid)


class Gym(native.ReasoningGymGym):
    def __init__(self, **kwargs):
        self.strict_verifier = True
        self.cfg = dict(canary_set=[])
        self.labels = {"mini_sudoku": "4x4 mini sudoku"}
        self._bootstrap = Path(native.BOOTSTRAP_PATH).read_text()
        self.records = {episode_id: record(episode_id, BOARDS[index])
                        for index, episode_id in enumerate(fresh.material.TRAIN_IDS + fresh.material.EVAL_IDS + fresh.CANDIDATES)}
        self.calls = []

    def _item(self, family, seed):
        episode_id = f"rg/{family}/{seed}"
        self.calls.append(episode_id)
        return self, self.records[episode_id]["entry"]

    def split_of(self, episode_id):
        return "canary" if 1900000 <= native.parse_id(episode_id)[1] < 1900100 else "train"

    def score_answer(self, answer, entry):
        return float(answer == entry["answer"])


class Tokenizer:
    eos_token_id = 0

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>" + messages[0]["content"] + "</user><assistant>"

    def encode(self, text, add_special_tokens=False):
        return list(text.encode())


class FreshPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gym = Gym()
        self.historical = [self.gym.records[episode_id] for episode_id in fresh.material.TRAIN_IDS + fresh.material.EVAL_IDS]

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o644)
        path.write_bytes(fresh._encoded(value))

    def test_selection_exact_first_sixteen_no_unused_suffix(self):
        selected, audit = fresh.select_panel(self.gym, self.historical)
        self.assertEqual([row["episode_id"] for row in selected], list(fresh.CANDIDATES[:16]))
        self.assertEqual(len(audit), 16)
        self.assertEqual(len(self.gym.calls), 64)
        self.assertEqual(self.gym.calls[-1], fresh.CANDIDATES[15])

    def test_excludes_training_old_canary_and_selected_solutions(self):
        for index, board_index in ((0, 0), (1, 40), (3, 50)):
            episode_id = fresh.CANDIDATES[index]
            self.gym.records[episode_id] = record(episode_id, BOARDS[board_index])
        selected, audit = fresh.select_panel(self.gym, self.historical)
        self.assertEqual([row["decision"] for row in audit[:4]],
                         ["historical_solution", "historical_solution", "accepted", "selected_solution"])
        self.assertEqual(len(selected), 16)
        self.assertEqual(selected[-1]["episode_id"], fresh.CANDIDATES[18])

    def test_declared_prior_ids_skipped_without_generation(self):
        selected, audit = fresh.select_panel(self.gym, self.historical, [fresh.CANDIDATES[0]])
        self.assertNotIn(fresh.CANDIDATES[0], self.gym.calls)
        self.assertEqual(audit[0]["decision"], "prior_exposure")
        self.assertEqual(selected[0]["episode_id"], fresh.CANDIDATES[1])

    def test_shortage_never_expands_candidate_range(self):
        for episode_id in fresh.CANDIDATES:
            self.gym.records[episode_id] = record(episode_id, BOARDS[0])
        selected, audit = fresh.select_panel(self.gym, self.historical)
        self.assertEqual(selected, [])
        self.assertEqual(len(audit), 30)
        self.assertEqual(len(self.gym.calls), 78)

    def test_bad_generator_entry_aborts_not_filters(self):
        self.gym.records[fresh.CANDIDATES[0]]["entry"]["metadata"]["num_empty"] = 7
        with self.assertRaisesRegex(ValueError, "blank count"):
            fresh.select_panel(self.gym, self.historical)
        self.assertEqual(self.gym.calls[-1], fresh.CANDIDATES[0])

    def test_nonunique_candidate_aborts(self):
        entry = self.gym.records[fresh.CANDIDATES[0]]["entry"]
        entry["question"] = "\n".join(["0 0 0 0"] * 4)
        entry["metadata"].update(puzzle=[[0] * 4 for _ in range(4)], num_empty=16)
        with self.assertRaisesRegex(ValueError, "not uniquely"):
            fresh.select_panel(self.gym, self.historical)

    def test_old_entry_drift_and_missing_exclusions_fail(self):
        historical = copy.deepcopy(self.historical)
        historical[0]["entry"]["question"] += " changed"
        with self.assertRaisesRegex(ValueError, "historical generator drift"):
            fresh.select_panel(self.gym, historical)
        with self.assertRaisesRegex(ValueError, "historical 32"):
            fresh.select_panel(self.gym, self.historical[:-1])

    def test_native_tuple_metadata_matches_serialized_history_without_mutation(self):
        for item in self.gym.records.values():
            item["entry"]["metadata"]["difficulty"] = {"empty": (8, 12)}
        historical = json.loads(fresh._encoded(self.historical))
        selected, audit = fresh.select_panel(self.gym, historical)
        self.assertEqual([item["episode_id"] for item in selected], list(fresh.CANDIDATES[:16]))
        for item in selected + audit:
            self.assertEqual(item["entry"]["metadata"]["difficulty"], {"empty": [8, 12]})
            self.assertEqual(item["entry_sha256"], fresh._sha(fresh._encoded(item["entry"])))
        self.assertEqual(self.gym.records[fresh.CANDIDATES[0]]["entry"]["metadata"]["difficulty"],
                         {"empty": (8, 12)})

    def test_tuple_normalization_still_rejects_changed_metadata_before_candidates(self):
        for item in self.historical:
            item["entry"]["metadata"]["difficulty"] = {"empty": (8, 12)}
        historical = json.loads(fresh._encoded(self.historical))
        self.historical[0]["entry"]["metadata"]["difficulty"]["empty"] = (8, 11)
        with self.assertRaisesRegex(ValueError, "historical generator drift"):
            fresh.select_panel(self.gym, historical)
        self.assertEqual(self.gym.calls, [fresh.material.TRAIN_IDS[0]])

    def test_native_dataclass_config_uses_same_json_representation(self):
        @dataclass
        class Config:
            empty: tuple = (8, 12)

        self.gym.config = Config()
        actual = fresh._entry(self.gym, fresh.CANDIDATES[0], BOARDS)
        self.assertEqual(actual["dataset_config"], {"empty": [8, 12]})
        self.assertEqual(self.gym.config.empty, (8, 12))

    def test_generator_version_and_digest_fail_before_generation(self):
        with patch.object(native, "installed_version", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "version mismatch"):
                fresh._runtime()
        with patch.object(native, "installed_version", return_value="0.1.25"), \
                patch.object(fresh.importlib, "import_module", return_value=fresh), \
                patch.object(custody, "_digest", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "generator digest"):
                fresh._runtime()

    def test_native_prompt_and_context_bound(self):
        current = fresh._prompt_record(self.gym, Tokenizer(), self.gym.records[fresh.CANDIDATES[0]])
        self.assertIn("CLOCK: chunk 1/1", current["q"])
        self.assertEqual(current["q_sha256"], fresh._sha(current["q"].encode()))
        with patch.object(Tokenizer, "encode", return_value=[1] * 4000):
            with self.assertRaisesRegex(ValueError, "exceeds 4096"):
                fresh._prompt_record(self.gym, Tokenizer(), self.gym.records[fresh.CANDIDATES[0]])

    def historical_fixture(self):
        roots = tuple(self.root / f"seed{seed}" for seed in range(3))
        model = self.root / "model"
        self.write(model / "tokenizer.json", {"synthetic": True})
        model_hashes = fresh.file_hashes(model)
        artifacts = {"useful.json": {"corpus": []}, "corrupt.json": {"corpus": []},
                     "oracle_sources.json": dict(records=self.historical),
                     "ids.json": dict(train=list(fresh.material.TRAIN_IDS), canary=list(fresh.material.EVAL_IDS),
                                      declared_prior_cpu_examined_ids=list(fresh.material.EVAL_IDS)),
                     "local_pins.json": dict(files=model_hashes)}
        pins = {name: fresh._sha(fresh._encoded(value)) for name, value in artifacts.items()}
        snapshot = custody.source_snapshot()
        weights = []
        for seed, root in enumerate(roots):
            for name, value in artifacts.items():
                self.write(root / "material" / name, value)
            self.write(root / "material/manifest.json", dict(status="PREPARED", files=pins))
            seed_weights = []
            for arm in ("useful", "corrupt"):
                adapter = root / f"training/{arm}_seed{seed}"
                self.write(adapter / "adapter_config.json", {"r": 8})
                self.write(adapter / "adapter_model.safetensors", {"synthetic": f"{seed}/{arm}"})
                hashes = fresh.file_hashes(adapter)
                seed_weights.append(hashes["adapter_model.safetensors"])
                spec = dict(copy.deepcopy(fresh.SETTINGS), adapter_path=str(adapter), model_path=str(model),
                            expected_adapter_hashes=hashes, expected_model_hashes=model_hashes,
                            families_path=native.FAMILIES_JSON, families_sha256=custody._digest(native.FAMILIES_JSON),
                            probe_root=str(root / "probes"), output_dir=str(root / "probes" / arm),
                            episode_ids=list(fresh.material.EVAL_IDS), training_life_roots=[str(root / "training")],
                            lineage_roots=[str(root / "training")], panel_role="development_validation", selection_used_episode_ids=[])
                path = root / f"logs/{arm}/probe_spec.json"
                self.write(path, spec)
                self.write(root / f"probes/{arm}/PAIR_DONE.json", dict(spec_sha256=custody._digest(path), source_snapshot=snapshot))
            weights.append(seed_weights)
        return roots, model, pins, weights

    def prepared(self, *, shortage=False):
        roots, model, pins, weights = self.historical_fixture()
        output = self.root / "fresh"
        if shortage:
            for episode_id in fresh.CANDIDATES:
                self.gym.records[episode_id] = record(episode_id, BOARDS[0])
        fake_transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *args, **kwargs: Tokenizer()))
        with patch.object(fresh, "MODEL", str(model)), patch.object(fresh, "MATERIAL_PINS", pins), \
                patch.object(fresh, "WEIGHT_PINS", weights), patch.object(fresh, "_runtime", return_value=dict(files={}, packages={})), \
                patch.object(native, "ReasoningGymGym", return_value=self.gym), \
                patch.dict("sys.modules", transformers=fake_transformers):
            fresh.prepare(output, roots=roots)
        return output

    def test_prepare_real_pins_specs_and_no_training_outputs(self):
        output = self.prepared()
        self.assertEqual(len(list((output / "specs").glob("*.json"))), 6)
        self.assertEqual(list((output / "probes").iterdir()), [])
        self.assertFalse((output / "training").exists())
        manifest = json.loads((output / "manifest.json").read_text())
        for name, digest in manifest["sha256"].items():
            self.assertEqual(custody._digest(output / name), digest)
        for path in (output / "specs").glob("*.json"):
            spec = json.loads(path.read_text())
            self.assertEqual(spec["order"], ["off", "on"])
            self.assertEqual(spec["panel_role"], "exploratory")
            self.assertEqual(spec["episode_ids"], list(fresh.CANDIDATES[:16]))
            fresh.read_spec(path, custody._digest(path))

    def test_shortage_preserves_audit_no_specs_or_manifest(self):
        with self.assertRaisesRegex(ValueError, "PANEL_INSUFFICIENT"):
            self.prepared(shortage=True)
        output = self.root / "fresh"
        self.assertTrue((output / "failure.json").exists())
        self.assertEqual(len(json.loads((output / "candidate_audit.json").read_text())["records"]), 30)
        self.assertFalse((output / "specs").exists())
        self.assertFalse((output / "manifest.json").exists())

    def test_reuse_rejected_and_adapter_drift_fails(self):
        roots, model, pins, weights = self.historical_fixture()
        with self.assertRaisesRegex(ValueError, "already exists"):
            fresh.prepare(self.root, roots=roots)
        adapter = roots[0] / "training/useful_seed0/adapter_model.safetensors"
        adapter.write_bytes(b"changed")
        with patch.object(fresh, "MODEL", str(model)), patch.object(fresh, "MATERIAL_PINS", pins), \
                patch.object(fresh, "WEIGHT_PINS", weights):
            with self.assertRaisesRegex(ValueError, "adapter inventory"):
                fresh._historical(roots, custody.source_snapshot(), analysis._Inputs())

    def pair_fixture(self, output, seed, arm):
        cell = f"seed{seed}_{arm}"
        spec_path = output / "specs" / (cell + ".json")
        spec = json.loads(spec_path.read_text())
        panel = json.loads((output / "panel.json").read_text())
        snapshot = json.loads((output / "preflight.json").read_text())["source_snapshot"]
        root = output / "probes" / cell
        receipts, receipt_hashes = {}, {}
        for index, condition in enumerate(("off", "on")):
            directory = root / condition
            identity = configured_generation_identity(spec["model_path"], spec["adapter_path"] if condition == "on" else None)
            sources = {"model": spec["model_path"]}
            hashes = {"model": spec["expected_model_hashes"]}
            if condition == "on":
                sources["adapter"] = spec["adapter_path"]
                hashes["adapter"] = spec["expected_adapter_hashes"]
            config = {name: spec[name] for name in ("episode_ids", "gen_seed", "seed_salt", "budget_ticks", "wake_max_tokens",
                                                    "scratchpad_max_tokens", "total_token_budget", "max_episodes", "probe_root")}
            code = {str(Path(snapshot["source_root"]) / name): digest for name, digest in snapshot["sha256"].items() if name.endswith(".py")}
            config.update(evidence_label="EVALUATION_ONLY", birth_prompt=Path(native.BOOTSTRAP_PATH).read_text(),
                          source_identity=identity, sources=sources, hashes_before=hashes, code_hashes_before=code,
                          gym_configuration=self.gym.cfg, reasoning_gym_version="0.1.25", protected_roots=[], origin_verification="SYNTHETIC")
            self.write(directory / "configuration.json", config)
            self.write(directory / "source_check.json", dict(evidence_label="EVALUATION_ONLY", hashes_after=hashes, code_hashes_after=code))
            episodes, requests = [], []
            for item_index, item in enumerate(panel["records"]):
                episode_id = item["episode_id"]
                rows = []
                if condition == "on" and arm == "useful" and item_index == 0:
                    rows = [self.action(episode_id, 0.0, 1), self.action(episode_id, 1.0, 2)]
                if condition == "on" and arm == "useful" and item_index == 1:
                    rows = [self.action(episode_id, 1.0, 1)]
                if condition == "on" and item_index == 2:
                    rows = [dict(self.action(episode_id, 1.0, 1), outcome="INVALID: empty attempt", action="")]
                name = f"episode_{item_index:04d}.jsonl"
                (directory / name).write_text("".join(json.dumps(row) + "\n" for row in rows))
                episodes.append(dict(episode_id=episode_id, ledger=name, n_actions=len(rows),
                                     summary=dict(episode_id=episode_id, n_acts=len(rows), best_score=1.0 if rows else 0.0)))
                requests.append(dict(kind="generation_request", max_tokens=400, prompts=[item["q"]], temperature=0.7,
                                     source_identity=identity,
                                     seeds=[fresh.batch_loop._seed_for(episode_id, 1, 0)]))
            (directory / "generations.jsonl").write_text("".join(json.dumps(row) + "\n" for row in requests))
            self.write(directory / "results.json", dict(evidence_label="EVALUATION_ONLY", episodes=episodes))
            inventory = {path.name: custody._digest(path) for path in directory.iterdir()}
            self.write(directory / "manifest.json", dict(evidence_label="EVALUATION_ONLY", sha256=inventory))
            receipt = dict(evidence_label="EVALUATION_ONLY", condition=condition, spec_sha256=custody._digest(spec_path),
                           pid=1000 + seed * 10 + index, results_sha256=custody._digest(directory / "results.json"),
                           manifest_sha256=custody._digest(directory / "manifest.json"))
            self.write(root / (condition + "_WORKER_DONE.json"), receipt)
            receipts[condition] = receipt
            receipt_hashes[condition] = custody._digest(root / (condition + "_WORKER_DONE.json"))
            self.write(root / (condition + ".cleanup.json"), dict(owned_group_empty=True, gpu_processes_absent=True))
        self.write(root / "PAIR_DONE.json", dict(evidence_label="EVALUATION_ONLY", workers=receipts,
                   spec_sha256=custody._digest(spec_path), receipt_sha256=receipt_hashes, source_snapshot=snapshot))

    def action(self, episode_id, score, attempt):
        return dict(kind="act", episode_id=episode_id, execution_id=f"{episode_id}/{attempt}", tick=1,
                    action="1 2 3 4", outcome=f"attempt {attempt}: verifier score {score:.2f} (accepted)",
                    score=score, occurrence_id="synthetic")

    def test_full_twelve_condition_reduction_first_act_not_best(self):
        output = self.prepared()
        for seed in range(3):
            for arm in ("useful", "corrupt"):
                self.pair_fixture(output, seed, arm)
        report = fresh.reduce(output, output / "report.json")
        self.assertEqual(report["solved_count_gain"]["values"], [1, 1, 1])
        self.assertTrue(report["all_off_action_score_vectors_equal"])
        useful = report["seeds"][0]["pairs"]["useful"]["on"]
        self.assertEqual(useful["episodes"][0]["metrics"]["first_act_solved"], 0)
        self.assertEqual(useful["episodes"][0]["metrics"]["native_best"], 1)
        self.assertEqual(useful["episodes"][2]["metrics"]["first_act_solved"], 0)
        self.assertEqual(useful["first_act_status_counts"]["missing"], 13)
        with self.assertRaisesRegex(ValueError, "already exists"):
            fresh.reduce(output, output / "report.json")

    def test_missing_pair_is_failure_not_zero(self):
        output = self.prepared()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            fresh.reduce(output, output / "report.json")
        self.assertFalse((output / "report.json").exists())

    def test_prepared_tampering_rejected(self):
        output = self.prepared()
        self.write(output / "panel.json", {"episode_ids": []})
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            fresh.reduce(output, output / "report.json")

    def test_prompt_and_missing_results_rejected_by_panel_aware_reducer(self):
        output = self.prepared()
        self.pair_fixture(output, 0, "useful")
        root = output / "probes/seed0_useful"
        spec = json.loads((output / "specs/seed0_useful.json").read_text())
        panel = json.loads((output / "panel.json").read_text())
        preflight = json.loads((output / "preflight.json").read_text())
        path = root / "on/generations.jsonl"
        original = path.read_text()
        requests = [json.loads(line) for line in original.splitlines()]
        requests[0]["prompts"] = ["wrong puzzle"]
        path.write_text("".join(json.dumps(row) + "\n" for row in requests))
        with self.assertRaisesRegex(ValueError, "first prompt/seed mismatch"):
            fresh._condition(root, "on", spec, panel, preflight, analysis._Inputs())
        path.write_text(original)
        results_path = root / "on/results.json"
        results = json.loads(results_path.read_text())
        results["episodes"].pop()
        self.write(results_path, results)
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            fresh._condition(root, "on", spec, panel, preflight, analysis._Inputs())

    def test_material_and_source_pins_reject_drift(self):
        roots, model, pins, weights = self.historical_fixture()
        with patch.object(fresh, "MODEL", str(model)), patch.object(fresh, "MATERIAL_PINS", pins), \
                patch.object(fresh, "WEIGHT_PINS", weights):
            snapshot = custody.source_snapshot()
            snapshot["sha256"]["organism_v6/model_backend.py"] = "f" * 64
            with self.assertRaisesRegex(ValueError, "source drift"):
                fresh._historical(roots, snapshot, analysis._Inputs())
            self.write(roots[0] / "material/useful.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "material manifest mismatch"):
                fresh._historical(roots, custody.source_snapshot(), analysis._Inputs())


if __name__ == "__main__":
    unittest.main()
