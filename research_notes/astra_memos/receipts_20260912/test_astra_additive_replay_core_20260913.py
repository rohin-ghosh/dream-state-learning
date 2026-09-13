"""CPU pairing tests over preserved input material only; no model/result calls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("additive_core_test", "/tmp/astra_additive_replay_core_20260913.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
ARCHIVED = Path("/tmp/astra_own_replay_repair_native_20260913_attempt1")


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = []
        for seed in range(3):
            root = ARCHIVED / f"own_replay_repair_seed{seed}_20260913_attempt1"
            def read(name):
                return json.loads((root / name).read_bytes())
            plan = read("plan.json")
            bound = dict(mixture=read("mixture.json"), parent=plan["parent"], memory_plan={"parent": plan["parent"]},
                         saved_training_sha256={arm: core.digest(root / f"training_{arm}.json") for arm in ("EXTRA_MEMORY", "REPLAY")},
                         saved_training={arm: read(f"training_{arm}.json") for arm in ("EXTRA_MEMORY", "REPLAY")})
            cls.fixtures.append((plan, bound))

    def material(self, seed=0):
        return core.build(*self.fixtures[seed])

    def test_original_allseed_dose_pair_bijection(self):
        total = 0
        for seed, updates in enumerate((304, 256, 256)):
            material = self.material(seed)
            self.assertEqual(material["counts"]["updates_per_arm"], updates)
            self.assertEqual(len({pair["memory_row_id"] for pair in material["pairs"]}), 24)
            self.assertEqual(len({pair["replay_row_id"] for pair in material["pairs"]}), 24)
            self.assertEqual(material["parent"], self.fixtures[seed][0]["parent"])
            total += updates * 2
        self.assertEqual(total, 1632)

    def test_primary_items_audits_and_epoch_order_exactly_old(self):
        for seed in range(3):
            material = self.material(seed)
            original = self.fixtures[seed][1]["saved_training"]["EXTRA_MEMORY"]
            for arm in core.ARMS:
                prepared = core.prepared_from_saved(material, arm)
                for key in ("items", "encoding", "epoch_order", "training_items_sha256", "epoch_order_sha256",
                            "presentation_counts", "per_kind", "actual_supervised_tokens"):
                    self.assertEqual(prepared[key], original[key])

    def test_fixed_construction_pairs_not_shuffled_or_rotated(self):
        material = self.material()
        count = material["counts"]["memory"]
        for offset, pair in enumerate(material["pairs"]):
            self.assertEqual(pair, dict(memory_row_id=f"own-repair:seed0:EXTRA_MEMORY:{count+offset:03d}",
                                        replay_row_id=f"own-repair:seed0:REPLAY:{count+offset:03d}"))
        prepared = core.prepared_from_saved(material, "ADDITIVE")
        self.assertEqual(sorted(prepared["memory_source_presentations"].values()), [16] * 4 + [24] * 10)

    def test_extra_tokens_reported_not_averaged_or_claimed_matched(self):
        material = self.material()
        additive = core.prepared_from_saved(material, "ADDITIVE")
        control = core.prepared_from_saved(material, "MEMORY_ONLY")
        self.assertEqual(additive["objective"], "sum_of_separate_mean_token_ce")
        self.assertEqual(control["objective"], "memory_mean_token_ce")
        self.assertEqual(additive["token_accounting"]["replay_presentations"], 192)
        self.assertEqual(control["token_accounting"]["replay_presentations"], 0)
        self.assertEqual(additive["token_accounting"]["memory_total_tokens"], control["token_accounting"]["memory_total_tokens"])
        self.assertGreater(additive["token_accounting"]["total_forward_tokens"], control["token_accounting"]["total_forward_tokens"])
        self.assertEqual(additive["updates"], control["updates"])

    def test_raw_replay_items_and_all_masks_unchanged(self):
        material = self.material()
        old = material["saved_training"]["REPLAY"]
        prepared = core.prepared_from_saved(material, "ADDITIVE")
        self.assertEqual(prepared["replay_items"], old["items"][14:])
        self.assertEqual(prepared["replay_encoding"], old["encoding"][14:])
        for audit in prepared["encoding"] + prepared["replay_encoding"]:
            self.assertEqual(len(audit["input_ids"]), len(audit["labels"]))
            self.assertEqual([label for label in audit["labels"] if label != -100], audit["supervised_ids"])
            self.assertTrue(audit["supervised_ids"])
            self.assertIn(-100, audit["labels"])
        self.assertEqual(len(material["mixture"]["replay_rows"]), 24)

    def test_rehashed_pair_change_rejected(self):
        material = self.material()
        material["pairs"][0], material["pairs"][1] = material["pairs"][1], material["pairs"][0]
        material["material_sha256"] = core.value_hash({key: value for key, value in material.items() if key != "material_sha256"})
        with self.assertRaisesRegex(ValueError, "pair mapping"):
            core.validate_material(material)

    def test_changed_raw_context_or_schedule_fails_source_pin(self):
        for field in ("items", "epoch_order", "encoding"):
            plan, bound = copy.deepcopy(self.fixtures[0])
            bound["saved_training"]["EXTRA_MEMORY"][field].reverse()
            with self.assertRaisesRegex(ValueError, "encoding pin"):
                core.build(plan, bound)

    def test_descendant_seed_and_zero_admission_rejected(self):
        plan, bound = copy.deepcopy(self.fixtures[0])
        bound["parent"]["adapter"] = "/descendant/not_original"
        with self.assertRaises(ValueError):
            core.build(plan, bound)
        plan, bound = copy.deepcopy(self.fixtures[0])
        plan["specification"]["seed"] = True
        with self.assertRaises(ValueError):
            core.build(plan, bound)
        mixture = copy.deepcopy(self.fixtures[0][1]["mixture"])
        mixture["arms"]["REPLAY"]["rows"] = []
        with self.assertRaisesRegex(ValueError, "exact24"):
            core.pairs_for(mixture)

    def test_native_encoding_checks_both_old_arms_before_return(self):
        material = self.material()
        old = core.repair_core()
        old.encode = Mock(side_effect=lambda mixture, arm, *args: copy.deepcopy(material["saved_training"][arm]))
        with patch.object(core, "repair_core", return_value=old):
            result = core.encode(material, "ADDITIVE", None, None, None, None, 0)
        self.assertEqual([call.args[1] for call in old.encode.call_args_list], ["EXTRA_MEMORY", "REPLAY"])
        self.assertEqual(result["updates"], 304)
        old.encode = Mock(return_value={})
        with patch.object(core, "repair_core", return_value=old), self.assertRaisesRegex(ValueError, "context/target/mask/order"):
            core.encode(material, "ADDITIVE", None, None, None, None, 0)

    def test_no_input_mutation_and_unknown_arm(self):
        before = core.encoded(self.fixtures)
        material = self.material()
        core.prepared_from_saved(material, "ADDITIVE")
        self.assertEqual(before, core.encoded(self.fixtures))
        with self.assertRaisesRegex(ValueError, "unknown"):
            core.prepared_from_saved(material, "REPLAY")


if __name__ == "__main__":
    unittest.main()
