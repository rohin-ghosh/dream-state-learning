"""CPU-only prospective W1 tests; mocked parent acceptance is not real evidence."""

from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import writer_replay_plan as replay


w0 = replay.w0


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = w0.build_material()
        cls.new = replay.build_new_bank(cls.old)

    def test_exact_prospective_identifiers_and_orientations(self):
        expected = [
            ["u5047d7871847", "ufae601274fcd", "ub1afb48d326f", "uae827ecb612e",
             "u16ae8aec1304", "u2149f4ad5050", "ub0ff5d6672ca", "ud80e0ec51ed4"],
            ["ud1cd6be5d468", "ufb8c51aa6de0", "ue8506f32b767", "ub598ca58155c",
             "ucb18bd09461d", "ubcd5da0049aa", "ue5c639f23e05", "u682af07d7ce3"]]
        self.assertEqual([root["tools"] for root in self.new["roots"]], expected)
        self.assertEqual([root["orientation"] for root in self.new["roots"]],
                         [list(orientation) for orientation in replay.NEW_ORIENTATIONS])
        self.assertEqual(self.new["orientation_counters"], [5, 1])

    def test_identifier_and_neighbour_disjointness(self):
        names = [name for material in (self.old, self.new) for root in material["roots"]
                 for name in root["tools"] + root["neighbours"]]
        self.assertEqual(len(names), 64)
        self.assertEqual(len(set(names)), 64)

    def test_template_coordinate_order_and_spill_surfaces_preserved(self):
        self.assertEqual(self.new["templates"], self.old["templates"])
        for root_index in range(2):
            old, new = self.old["roots"][root_index], self.new["roots"][root_index]
            for mapping in w0.MAPS:
                for before, after in zip(old["train"][mapping], new["train"][mapping]):
                    for field in ("slot", "mode", "stratum", "template"):
                        self.assertEqual(before[field], after[field])
                    self.assertEqual(after["context"], w0.TEMPLATES[root_index][after["template"]].format(
                        tool=new["tools"][after["slot"]], mode=f"m{after['mode']}"))
                    self.assertEqual(after["target"], new["orientation"][after["slot"]] ^
                                     after["mode"] ^ (mapping == "W-"))
            for before, after in zip(old["held"], new["held"]):
                self.assertEqual({key: value for key, value in before.items() if key != "context"},
                                 {key: value for key, value in after.items() if key != "context"})
            for before, after in zip(old["spill"], new["spill"]):
                for field in ("family", "index", "expected", "seed"):
                    self.assertEqual(before[field], after[field])
                if before["family"] == "unrelated":
                    self.assertEqual(before, after)
                else:
                    self.assertNotEqual(before["context"], after["context"])

    def test_exact_bank_and_pooled_shortcuts(self):
        receipt = replay.validate_geometry(self.old, self.new)
        self.assertEqual(len(receipt["checks"]), 240)
        self.assertTrue(all(2 * row["correct"] == row["total"] for row in receipt["checks"]))
        pooled_fields = {tuple(row["fields"]) for row in receipt["checks"] if row["bank"] == "POOLED"}
        self.assertEqual(pooled_fields, set(replay.POOLED_SHORTCUTS))
        self.assertFalse(receipt["execution_ready"])
        self.assertIsNone(receipt["scientific_label"])

    def test_maps_are_exact_complements(self):
        for root in self.new["roots"]:
            for positive, negative in zip(root["train"]["W+"], root["train"]["W-"]):
                self.assertEqual(positive["context"], negative["context"])
                self.assertEqual(positive["target"] ^ negative["target"], 1)

    def test_material_tampering_rejected(self):
        for field, value in (("context", "changed"), ("target", 7), ("template", 12), ("orientation", 2)):
            changed = copy.deepcopy(self.new)
            changed["roots"][0]["train"]["W+"][0][field] = value
            with self.subTest(field=field), self.assertRaises(w0.ContractError):
                replay.validate_geometry(self.old, changed)
        changed = copy.deepcopy(self.old)
        changed["recipe"]["lr"] = .5
        with self.assertRaises(w0.ContractError):
            replay.build_new_bank(changed)

    def test_inputs_are_not_mutated_or_aliased(self):
        old = copy.deepcopy(self.old)
        before = w0.digest(old)
        new = replay.build_new_bank(old)
        replay.build_replay_plan(old, new)
        self.assertEqual(w0.digest(old), before)
        new["roots"][0]["held"][0]["context"] = "changed"
        self.assertEqual(w0.digest(old), before)

    def test_equal_python_values_with_different_json_bytes_are_rejected(self):
        changed = copy.deepcopy(self.new)
        row = changed["roots"][0]["train"]["W+"][0]
        row["target"] = bool(row["target"])
        with self.assertRaises(w0.ContractError):
            replay.validate_geometry(self.old, changed)

    def test_new_choice_does_not_depend_on_old_fit_or_order_seed(self):
        old = w0.build_material(train_order_seed=456, held_order_seed=789, fit_seeds=(12, 13))
        new = replay.build_new_bank(old)
        self.assertEqual([root["tools"] for root in new["roots"]], [root["tools"] for root in self.new["roots"]])
        self.assertEqual([root["orientation"] for root in new["roots"]],
                         [root["orientation"] for root in self.new["roots"]])
        replay.validate_geometry(old, new)

    def test_planning_never_calls_model_tokenizer_native_probe_or_execution(self):
        with patch.object(w0, "load_local_tokenizer", side_effect=AssertionError("tokenizer load")), \
                patch.object(w0, "load_hf_model", side_effect=AssertionError("model load")), \
                patch.object(w0, "native_build_preflight", side_effect=AssertionError("compiler probe")), \
                patch.object(w0, "gpu_identity", side_effect=AssertionError("GPU probe")), \
                patch.object(w0, "execute_real", side_effect=AssertionError("execution")), \
                patch.object(w0, "replay_real", side_effect=AssertionError("parent outcomes")):
            new = replay.build_new_bank(self.old)
            plan = replay.build_replay_plan(self.old, new)
            self.assertEqual(plan["status"], "W0_PARENT_PENDING")


class ExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = w0.build_material()
        cls.new = replay.build_new_bank(cls.old)
        cls.plan = replay.build_replay_plan(cls.old, cls.new)

    def test_exact_pair_reversal_and_logical_epoch_order(self):
        for cell in self.plan["cells"].values():
            occurrences = cell["CUM"]
            self.assertEqual(len(occurrences), 512)
            self.assertEqual([row["bank"] for row in occurrences[:256]], ["OLD", "NEW"] * 128)
            self.assertEqual([row["bank"] for row in occurrences[256:]], ["NEW", "OLD"] * 128)
            self.assertEqual([row["source_index"] for row in occurrences],
                             [index for index in range(128) for _ in range(2)] * 2)
            self.assertEqual([row["step"] for row in occurrences], list(range(1, 513)))
            self.assertEqual([row["epoch"] for row in occurrences], [0] * 256 + [1] * 256)

    def test_every_bank_row_has_exactly_two_matched_occurrences(self):
        receipt = replay.validate_replay_plan(self.plan, self.old, self.new)
        self.assertEqual(len(receipt["checks"]), 16)
        for cell in self.plan["cells"].values():
            for bank in replay.BANKS:
                single = Counter(row["source_row_sha256"] for row in cell[f"{bank}_SINGLE"])
                cumulative = Counter(row["source_row_sha256"] for row in cell["CUM"] if row["bank"] == bank)
                self.assertEqual(single, cumulative)
                self.assertEqual(len(single), 128)
                self.assertEqual(set(single.values()), {2})

    def test_seed_target_mask_and_recipe_boundaries(self):
        self.assertEqual(self.plan["inherited_recipe"], w0.EXECUTION_RECIPE)
        for key, cell in self.plan["cells"].items():
            seed = self.old["config"]["fit_seeds"][int(key[0])]
            for occurrences in cell.values():
                for row in occurrences:
                    self.assertEqual(row["seed"], seed)
                    self.assertIn(row["target"], ("ACT: a0\n", "ACT: a1\n"))
                    self.assertEqual(row["mask"], "context_only")
        self.assertEqual(self.plan["proposed_new_fits"], 8)
        self.assertEqual(self.plan["reused_old_fits"], 4)
        self.assertEqual(self.plan["intended_dose"]["CUM"], dict(rows=256, optimizer_steps=512))

    def test_deterministic_complete_occurrence_hash(self):
        self.assertEqual(replay.build_replay_plan(self.old, self.new), self.plan)
        self.assertEqual(self.plan["ordered_occurrences_sha256"],
                         "c787e565e057435a894087aba3505e26477ac464699730d910886baf61b82ee1")

    def test_reorder_even_with_equal_dose_and_rehash_is_rejected(self):
        changed = copy.deepcopy(self.plan)
        rows = changed["cells"]["0/W+"]["CUM"]
        rows[0], rows[1] = rows[1], rows[0]
        rows[0]["step"], rows[1]["step"] = 1, 2
        changed["ordered_occurrences_sha256"] = w0.digest(changed["cells"])
        with self.assertRaises(w0.ContractError):
            replay.validate_replay_plan(changed, self.old, self.new)

    def test_dropped_duplicated_or_relabelled_exposure_is_rejected(self):
        for mutation in ("drop", "duplicate", "target", "seed", "mask"):
            changed = copy.deepcopy(self.plan)
            rows = changed["cells"]["1/W-"]["CUM"]
            if mutation == "drop":
                rows.pop()
            elif mutation == "duplicate":
                rows[1] = copy.deepcopy(rows[0])
            else:
                rows[0][mutation] = "changed"
            changed["ordered_occurrences_sha256"] = w0.digest(changed["cells"])
            with self.subTest(mutation=mutation), self.assertRaises(w0.ContractError):
                replay.validate_replay_plan(changed, self.old, self.new)

    def test_plan_never_confers_readiness_or_scientific_label(self):
        self.assertEqual(self.plan["status"], "W0_PARENT_PENDING")
        self.assertFalse(self.plan["execution_ready"])
        self.assertFalse(self.plan["real_tokenizer_encodings_bound"])
        self.assertFalse(self.plan["training_run_replication"])
        self.assertTrue(self.plan["root_seed_confounded"])
        self.assertIsNone(self.plan["parent_binding"])
        self.assertIsNone(self.plan["scientific_label"])
        self.assertIn("not sequential", self.plan["claim_limit"])
        changed = dict(self.plan, execution_ready=True)
        with self.assertRaises(w0.ContractError):
            replay.validate_replay_plan(changed, self.old, self.new)
        changed = copy.deepcopy(self.plan)
        changed["cells"]["0/W+"]["CUM"][0]["step"] = 1.0
        with self.assertRaises(w0.ContractError):
            replay.validate_replay_plan(changed, self.old, self.new)


class ParentTests(unittest.TestCase):
    def sources(self):
        return w0.source_hashes()

    def mock_parent(self, root):
        native = dict(kind="CPU_NATIVE_BUILD_PREFLIGHT", returncode=0, model_loaded=False,
                      real_GPU_executed=False, triton_version="CPU_MOCK", compiler_version="CPU_MOCK",
                      compiler_sha256="a" * 64, headers=[["/CPU_MOCK/Python.h", "b" * 64]])
        w0.write_once(root, "native_build_preflight.json", native)
        config = w0.config_template()
        manifest = dict(config=config, source_hashes=self.sources(),
                        artifact_hashes={"native_build_preflight.json": w0.digest(native)})
        w0.write_once(root, "manifest.json", manifest)
        w0.write_once(root, "material.json", w0.build_material())
        w0.write_once(root, "requests.json", ["CPU_MOCK_NOT_REAL_REQUESTS"])
        adapters = {}
        for root_index in range(2):
            for map_index, mapping in enumerate(w0.MAPS):
                adapter = root / f"adapter_fit_{root_index}_{map_index}"
                adapter.mkdir()
                (adapter / "CPU_MOCK_NOT_AN_ADAPTER").write_text(f"{root_index}/{mapping}")
                adapters[f"{root_index}/{mapping}"] = w0.tree_hash(adapter)
        w0.write_once(root, "adapter_hashes.json", adapters)
        w0.write_once(root, "REAL_EXECUTION_SEAL.json", dict(files={"native_build_preflight.json": w0.digest(native)}))
        return dict(evidence="REAL_GPU_EXECUTION", scientific_label="MULTIKEY_BINDING_PASS",
                    result=dict(label="MULTIKEY_BINDING_PASS"))

    def test_partial_prepared_or_aborted_parent_never_replays(self):
        for marker in (None, "PREPARED_SEAL.json", "NONREPORTABLE_ABORT.json"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                if marker:
                    w0.write_once(root, marker, {"scientific_label": "MULTIKEY_BINDING_PASS"})
                with patch.object(w0, "replay_real") as reducer:
                    with self.assertRaises(w0.ContractError):
                        replay.validate_w0_parent(root, expected_source_hashes=self.sources())
                    reducer.assert_not_called()

    def test_counterfeit_pass_without_full_w0_evidence_is_rejected_by_real_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.mock_parent(root)
            with self.assertRaises((w0.ContractError, OSError, KeyError)):
                replay.validate_w0_parent(root, expected_source_hashes=self.sources())

    def test_no_report_only_or_cpu_fixture_or_nonpass_shortcut(self):
        for evidence, label in (("CPU_FIXTURE_ONLY", "MULTIKEY_BINDING_PASS"),
                                ("REAL_GPU_EXECUTION", None),
                                ("REAL_GPU_EXECUTION", "OPTIMIZATION_INCONCLUSIVE"),
                                ("REAL_GPU_EXECUTION", "GATEWAY_NEGATIVE")):
            with self.subTest(evidence=evidence, label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                report = self.mock_parent(root)
                report.update(evidence=evidence, scientific_label=label)
                with patch.object(w0, "replay_real", return_value=report):
                    with self.assertRaises(w0.ContractError):
                        replay.validate_w0_parent(root, expected_source_hashes=self.sources())

    def test_mocked_success_binds_parent_but_cannot_make_w1_ready_and_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = self.mock_parent(root)
            before = w0.tree_hash(root)
            with patch.object(w0, "replay_real", return_value=report) as reducer:
                binding = replay.validate_w0_parent(root, expected_source_hashes=self.sources())
                reducer.assert_called_once_with(root)
            self.assertEqual(w0.tree_hash(root), before)
            self.assertTrue(binding["parent_eligible"])
            self.assertFalse(binding["execution_ready"])
            self.assertIsNone(binding["scientific_label"])
            self.assertEqual(len(binding["adapters"]), 4)
            self.assertEqual(binding["report_sha256"], w0.digest(report))
            self.assertEqual(binding["material_sha256"], w0.file_hash(root / "material.json"))
            self.assertIn("environment", binding["identity"])
            self.assertIn("seeds", binding["identity"])

    def test_wrong_local_or_parent_source_pins_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = self.mock_parent(root)
            changed = dict(self.sources())
            changed[w0.SOURCE_PATHS[0]] = "0" * 64
            with self.assertRaises(w0.ContractError):
                replay.validate_w0_parent(root, expected_source_hashes=changed)
            with patch.object(w0, "source_hashes", return_value=changed), \
                    patch.object(w0, "replay_real", return_value=report):
                with self.assertRaises(w0.ContractError):
                    replay.validate_w0_parent(root, expected_source_hashes=changed)

    def test_native_receipt_or_adapter_tampering_fails(self):
        for filename in ("native_build_preflight.json", "adapter_fit_0_0/CPU_MOCK_NOT_AN_ADAPTER"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                report = self.mock_parent(root)
                path = root / filename
                path.write_bytes(path.read_bytes() + b" ")
                with patch.object(w0, "replay_real", return_value=report):
                    with self.assertRaises(w0.ContractError):
                        replay.validate_w0_parent(root, expected_source_hashes=self.sources())

    def test_real_reducer_rejection_is_never_overridden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.mock_parent(root)
            with patch.object(w0, "replay_real", side_effect=w0.ContractError("raw records incomplete")):
                with self.assertRaisesRegex(w0.ContractError, "raw records incomplete"):
                    replay.validate_w0_parent(root, expected_source_hashes=self.sources())

    def test_even_resealed_parent_requires_repaired_native_triton_binding(self):
        for field in ("triton_version", "compiler_sha256", "headers"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                report = self.mock_parent(root)
                native = w0.load_json(root / "native_build_preflight.json")
                native.pop(field)
                (root / "native_build_preflight.json").write_bytes(w0.canonical(native))
                manifest = w0.load_json(root / "manifest.json")
                manifest["artifact_hashes"]["native_build_preflight.json"] = w0.digest(native)
                (root / "manifest.json").write_bytes(w0.canonical(manifest))
                seal = w0.load_json(root / "REAL_EXECUTION_SEAL.json")
                seal["files"]["native_build_preflight.json"] = w0.digest(native)
                (root / "REAL_EXECUTION_SEAL.json").write_bytes(w0.canonical(seal))
                with patch.object(w0, "replay_real", return_value=report):
                    with self.assertRaises(w0.ContractError):
                        replay.validate_w0_parent(root, expected_source_hashes=self.sources())


if __name__ == "__main__":
    unittest.main()
