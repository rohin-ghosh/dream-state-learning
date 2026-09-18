"""CPU ledger regression tests; no scientific material or execution."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from organism_v6 import two_sleep_junction_v4_ledger as source


class TwoSleepJunctionV4LedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = source.build_ledger()
        self.phases = {phase["phase"]: phase for phase in self.ledger["phases"]}

    def test_exact_local_contract_and_imported_section_hashes(self):
        directory = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        v4_bytes = (directory / "2026-09-13_two_sleep_own_experience_junction_source_contract_v4.md").read_bytes()
        v3_bytes = (directory / "2026-09-13_two_sleep_own_experience_junction_source_contract_v3.md").read_bytes()
        self.assertEqual(source.verify_source_bytes(v4_bytes, v3_bytes), self.ledger["source_binding"])
        for heading, following, expected in (
            (b"## 7. Canonical executable phase ledger", b"## 8.", source.V3_SECTION_7_SHA256),
            (b"## 10. Derived resource ledger", b"## 11.", source.V3_SECTION_10_SHA256),
        ):
            section = v3_bytes[v3_bytes.index(heading):v3_bytes.index(following)]
            self.assertEqual(sha256(section).hexdigest(), expected)
        for changed_v4, changed_v3 in ((v4_bytes + b"\n", v3_bytes), (v4_bytes, v3_bytes + b"\n")):
            with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
                source.verify_source_bytes(changed_v4, changed_v3)

    def test_canonical_json_is_deterministic_and_fail_closed(self):
        encoded = source.canonical_json(self.ledger)
        self.assertEqual(json.loads(encoded), self.ledger)
        self.assertEqual(source.canonical_json(), encoded)
        self.assertEqual(self.ledger["source_status"], "PARTIAL_SOURCE_ONLY")
        self.assertTrue(all(value is False for value in self.ledger["gates"].values()))
        self.assertFalse(self.ledger["empirical_feasibility_claim"])
        self.assertFalse(self.ledger["predicate_policy"]["evaluated"])
        self.assertEqual(self.ledger["world_order"], ["W0", "W1"])
        self.assertNotIn("TS3N_", encoded)
        self.assertNotIn("TS3E_", encoded)
        self.ledger["gates"]["GO_PREPARE"] = True
        with self.assertRaisesRegex(ValueError, "noncanonical_ledger"):
            source.canonical_json(self.ledger)
        self.assertEqual(source.canonical_json(), encoded)

    def test_exact_phase_and_condition_order(self):
        self.assertEqual(list(self.phases), [
            "P00", "P05_IMPORT_CONTROLLER_BASELINE", "P10", "P20", "P30", "P31",
            "P40", "P50", "P60", "P70", "P71",
        ])
        expected = {
            "P10": ["SUPPLIED_INLINE", "SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING", "ATOM_TEXT", "O_TEXT", "T_TEXT", "RELEVANT_CUT_TEXT", "IRRELEVANT_CUT_TEXT"],
            "P20": ["AUTH", "O", "T", "ATOM", "REL_CUT", "IRR_CUT", "RAW"],
            "P30": ["AUTH", "O", "T", "ATOM", "BIRTH", "FOREIGN", "RAW", "RESP_T", "REL_CUT", "IRR_CUT"],
            "P50": ["SUPPLIED_INLINE", "SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING", "ATOM_TEXT", "O_TEXT", "N_TEXT", "OLD_FILLER_TEXT", "RESP_O_PRE", "RESP_N_PRE"],
            "P60": ["AUTH", "N", "O", "ATOM", "RAW", "OLD_FILLER"],
            "P70": ["AUTH", "N", "O", "ATOM", "RAW", "OLD_FILLER", "FOREIGN", "RESP_O", "RESP_N", "S1_NOWRITE", "AUTH_OLD_RETENTION"],
        }
        for phase, conditions in expected.items():
            self.assertEqual([row["condition"] for row in self.phases[phase]["rows"]], conditions)
        for phase, total in (("P10", 12), ("P30", 18), ("P50", 16), ("P70", 22)):
            rows = self.phases[phase]["rows"]
            self.assertEqual([ordinal for row in rows for ordinal in row["ordinals"]], list(range(1, total + 1)))
            for row in rows:
                self.assertEqual(row["goal_count"], len(row["goals"]))
                self.assertEqual(row["goals"], ["g*"] if row["goal_selector"] == "P" else [0, 1])
                family = "F" if phase in ("P10", "P30") or row["condition"] == "AUTH_OLD_RETENTION" else "H"
                self.assertEqual(row["goal_family"], family)

    def test_every_omitted_or_duplicate_phase_is_rejected(self):
        for position in range(len(self.ledger["phases"])):
            with self.subTest(position=position):
                phases = deepcopy(self.ledger["phases"])
                phases.pop(position)
                with self.assertRaisesRegex(ValueError, "omitted_phase"):
                    source.derive_resources(phases)
                phases = deepcopy(self.ledger["phases"])
                phases.append(deepcopy(phases[position]))
                with self.assertRaisesRegex(ValueError, "duplicate_phase"):
                    source.derive_resources(phases)

    def test_changed_order_rows_roles_or_numeric_types_are_rejected(self):
        phases = deepcopy(self.ledger["phases"])
        phases[0], phases[1] = phases[1], phases[0]
        with self.assertRaisesRegex(ValueError, "noncanonical_phase_order"):
            source.derive_resources(phases)
        for mutation in ("omit", "duplicate", "role", "boolean", "float"):
            phases = deepcopy(self.ledger["phases"])
            rows = phases[2]["rows"]
            if mutation == "omit":
                rows.pop()
            elif mutation == "duplicate":
                rows.append(deepcopy(rows[0]))
            elif mutation == "role":
                rows[2]["role"] = "diagnostic"
            elif mutation == "boolean":
                rows[-1]["goal_count"] = True
            else:
                rows[-1]["goal_count"] = 1.0
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "noncanonical_phase_rows"):
                source.derive_resources(phases)

    def test_p05_import_is_zero_call_with_exact_controller_predicates(self):
        baseline = self.phases["P05_IMPORT_CONTROLLER_BASELINE"]["rows"][0]
        self.assertEqual(baseline["budgets"], [])
        self.assertFalse(baseline["receipt_import_implemented"])
        self.assertEqual(baseline["pair_ordinals"], [0, 2, 4, 6])
        self.assertEqual(baseline["chain_ordinals"], [0, 4, 8, 12, 16, 20, 24, 28])
        expected = [(4, 3)] * 4 + [(32, 30), (8, 6), (8, 7), (8, 7), (16, 15)]
        for metrics, drop in ((baseline["metrics"], None), (self.phases["P31"]["metrics"], 1), (self.phases["P71"]["metrics"], 1)):
            self.assertEqual([(metric["denominator"], metric["absolute_minimum"]) for metric in metrics], expected)
            self.assertTrue(all(metric["birth_maximum_count_drop"] == drop for metric in metrics))
        totals = self.ledger["resources"]["by_phase_per_world"]["P05_IMPORT_CONTROLLER_BASELINE"]
        self.assertEqual((totals["model_calls"], totals["generated_tokens"], totals["fits"]), (0, 0, 0))

    def test_atom_amendment_and_diagnostic_roles(self):
        for phase, condition in (("P10", "ATOM_TEXT"), ("P30", "ATOM"), ("P50", "ATOM_TEXT"), ("P70", "ATOM")):
            row = next(row for row in self.phases[phase]["rows"] if row["condition"] == condition)
            self.assertEqual((row["role"], row["expected"], row["goal_count"]), ("gate", "success <=1/2", 2))
            self.assertEqual(row["predicate_scope"], "each_world_independently")
        diagnostics = [(phase["phase"], row["condition"]) for phase in self.ledger["phases"] for row in phase["rows"] if row["role"] == "diagnostic"]
        self.assertEqual(diagnostics, [("P30", "RAW"), ("P70", "RAW"), ("P70", "S1_NOWRITE")])

    def test_formation_order_and_caps(self):
        old = self.phases["P00"]["rows"]
        self.assertEqual([(row["condition"], row["call_kind"]) for row in old[:16]], [
            (role, kind) for role in ("s0", "s1", "t0", "t1", "i0", "i1", "i2", "i3") for kind in ("action", "EVENT")
        ])
        self.assertEqual([row["condition"] for row in old[16:]], ["LS0", "LS1", "IL0", "IL1"])
        new = self.phases["P40"]["rows"]
        self.assertEqual([(row["condition"], row["call_kind"]) for row in new], [
            ("primary", "PROBE"), ("primary", "EVENT"), ("complement", "PROBE"), ("complement", "EVENT"), ("NL0", "LINK"), ("NL1", "LINK"),
        ])
        self.assertEqual(sum(row["budgets"][0]["generated_tokens"] for row in old + new), 2880)

    def test_each_fit_has_immediate_ordered_cold_coverage(self):
        for phase, counts, total in (("P20", [16, 16, 8, 4, 16], 60), ("P60", [20, 20, 10, 4, 16], 70)):
            fits = self.phases[phase]["rows"]
            self.assertEqual([row["ordinal"] for row in fits], list(range(1, len(fits) + 1)))
            for fit in fits:
                cold = fit["cold_immediately_after_fit"]
                self.assertEqual([row["kind"] for row in cold], ["EVENT_AT", "LINKS_FROM", "EVENT", "INVALID", "CANARY"])
                self.assertEqual([row["budgets"][0]["calls"] for row in cold], counts)
                self.assertEqual([ordinal for row in cold for ordinal in row["ordinals"]], list(range(1, total + 1)))
                self.assertIn("retain repeats", cold[0]["order"])
                self.assertTrue(all(row["role"] == "gate" for row in cold))
                self.assertEqual(cold[-1]["expected"], "canaries >=15/16")
        self.assertEqual([row["actor_mount"] for row in self.phases["P60"]["rows"]], [
            "S1 AUTH", "S1 AUTH", "S1 O", "S1 ATOM", "S1 RAW", "S1 AUTH",
        ])

    def test_alias_targets_and_empty_chain_reservations(self):
        for phase, cold_phase, first_canary in (("P31", "P20", 45), ("P71", "P60", 55)):
            rows = self.phases[phase]["rows"]
            self.assertEqual([ordinal for row in rows for ordinal in row["ordinals"]], list(range(1, 281)))
            self.assertEqual([(row["skill"], row["pair"], row["member"]) for row in rows[:32]], [
                (skill, pair, member) for skill in ("SEEK", "PROSPECT", "CHECK", "CONTINUE") for pair in (0, 2, 4, 6) for member in ("lower", "upper")
            ])
            chains = rows[32:40]
            self.assertEqual([row["chain_ordinal"] for row in chains], [0, 4, 8, 12, 16, 20, 24, 28])
            for row in chains:
                self.assertEqual(len(row["ordinals"]), 29)
                self.assertEqual(row["budgets"][0]["generated_tokens"], 4096)
                self.assertEqual((row["unused_tail_state"], row["empty_slot_calls"], row["empty_slot_tokens"]), ("EMPTY", 0, 0))
            cold = self.phases[cold_phase]["rows"][0]["cold_immediately_after_fit"][-1]
            aliases = rows[40:]
            self.assertEqual([row["target"]["query_ordinal"] for row in aliases], cold["ordinals"])
            for canary, row in enumerate(aliases):
                self.assertEqual(row["target"], {"phase": cold_phase, "fit": "AUTH", "world": "same_world", "query_ordinal": first_canary + canary, "canary_ordinal": canary})
                self.assertTrue(row["identical_raw_hashes_required"])
                self.assertEqual((row["budgets"][0]["calls"], row["budgets"][0]["generated_tokens"]), (0, 0))
            self.assertEqual(sum(row["budgets"][0]["calls"] for row in rows), 264)
        self.assertEqual(source.reservation_call_maximum("alias"), 0)
        self.assertEqual(source.reservation_call_maximum("chain", "EMPTY"), 0)
        self.assertEqual(source.reservation_call_maximum("chain"), 1)
        for kind, state in (("unknown", "RESERVED"), ("chain", "EXECUTED"), ("intervention", "EMPTY")):
            with self.assertRaises(ValueError):
                source.reservation_call_maximum(kind, state)

    def test_resource_totals_regenerate_from_rows(self):
        calls = {}
        tokens = {}
        for phase in self.ledger["phases"]:
            for row in phase["rows"]:
                budgets = row["budgets"] + [budget for cold in row.get("cold_immediately_after_fit", []) for budget in cold["budgets"]]
                for budget in budgets:
                    category = budget["category"]
                    calls[category] = calls.get(category, 0) + budget["calls"]
                    tokens[category] = tokens.get(category, 0) + budget["generated_tokens"]
        self.assertEqual(calls, {"formation": 26, "actor": 1496, "cold_canary": 840, "native_reader": 340, "preservation": 528})
        self.assertEqual(tokens, {"formation": 2880, "actor": 278528, "cold_canary": 154368, "native_reader": 54400, "preservation": 81920})
        resources = source.derive_resources(self.ledger["phases"])
        self.assertEqual(resources, self.ledger["resources"])
        for category in calls:
            self.assertEqual(resources["per_world"]["categories"][category], {"calls": calls[category], "generated_tokens": tokens[category]})
            self.assertEqual(resources["pair"]["categories"][category], {"calls": 2 * calls[category], "generated_tokens": 2 * tokens[category]})
        self.assertEqual(sum(calls.values()), 3230)
        self.assertEqual(sum(tokens.values()), 572096)
        per_world = resources["per_world"]
        self.assertEqual((per_world["route_rollouts"], per_world["native_reader_rollouts"], per_world["fits"]), (68, 34, 13))
        for phase, routes, readers in (("P10", 12, 0), ("P30", 18, 16), ("P50", 16, 0), ("P70", 22, 18)):
            totals = resources["by_phase_per_world"][phase]
            self.assertEqual((totals["route_rollouts"], totals["native_reader_rollouts"]), (routes, readers))
        self.assertEqual((resources["pair"]["model_calls"], resources["pair"]["generated_tokens"], resources["pair"]["fits"]), (6460, 1144192, 26))

    def test_training_caps_per_world_versus_pair(self):
        for dose, updates, presentations, padded, stage_updates in (
            ("D1", 24656, 98624, 1615855616, [856, 1056]),
            ("D2", 31312, 125248, 2052063232, [1112, 1312]),
        ):
            training = self.ledger["resources"]["training"][dose]
            self.assertEqual(training["pair"], {"updates": updates, "presentations": presentations, "maximum_padded_training_tokens": padded})
            self.assertEqual(training["per_world"], {key: value // 2 for key, value in training["pair"].items()})
            self.assertEqual([stage["updates_per_fit"] for stage in training["stages"].values()], stage_updates)
            birth = 1024 if dose == "D1" else 2048
            from_rows = sum(row["memory_units"] * row["views_per_unit"] * row["repeats_per_view"] + birth for phase in self.ledger["phases"] for row in phase["rows"] if row["kind"] == "fit")
            self.assertEqual(from_rows * 2, presentations)
            self.assertEqual(presentations // 4, updates)
            self.assertEqual(presentations * 16384, padded)
        formula = self.ledger["resources"]["training_formula"]
        self.assertIsNone(formula["exact_padded_training_tokens"])
        self.assertIsNone(formula["imported_parameter_count"])
        self.assertIsNone(formula["flop_stop_value"])
        self.assertEqual(formula["flop_stop"], "8 * imported_parameter_count * exact_padded_training_tokens")

    def test_resource_and_scope_tampering_is_rejected(self):
        for field in ("resources", "source_status", "empirical_feasibility_claim"):
            ledger = deepcopy(self.ledger)
            if field == "resources":
                ledger[field]["per_world"]["model_calls"] = 6460
            elif field == "source_status":
                ledger[field] = "READY"
            else:
                ledger[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "noncanonical_ledger"):
                source.validate_ledger(ledger)


if __name__ == "__main__":
    unittest.main()
