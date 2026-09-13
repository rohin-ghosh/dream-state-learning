"""Scripted runtime tests; real CPU world/parser/scorer, no process or model."""

import copy
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_vertical_dev as runtime
from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_prepare as prepare


def fixture_contract():
    roots = []
    for role, count in (("excluded", 4), ("disposable", 1), ("dev", 2)):
        for index in range(count):
            root = core.build_root(f"{role}/{index}")
            roots.append({"id": root.label, "role": role, "wire": core.to_data(root),
                          "old_bit": 0, "canonical_r": 0})
    return {"kind": "TEST_NOT_PREPARED", "bindings": {"root_registry": roots,
            "core_registry": core.registries(), "intervention_registry": [], "slot_registry": []}}


def bridge_report(contract, profile_receipts=None):
    return {"bridge_invariants_valid": True, "execution_contract_valid": False,
            "contract_sha256": prepare.digest(contract), "missing_interfaces": ["synthetic fixture"]}


class ScriptedBackend:
    scripted = True

    def __init__(self, plan, overrides=None):
        self.outputs = {}
        self.requests = []
        self.closed = False
        self.bad_release = False
        self.device_seconds = 0.01
        self.output_tokens = 10
        self.returned_tokens = 10
        for task in plan["tasks"]:
            cell = core.from_data(task["cell"])
            if task["projection"] in ("OLD_ONLY_TEXT", "NEW_ONLY_TEXT", "NONE_OFF", "WRONG_ROOT"):
                raw = "MISS"
            elif task["panel"] == "delayed":
                raw = core.oracle_route_v1(cell, task["goal"])
            else:
                raw = "PROBE " + cell.root.lookup("probe", "relevant")
            self.outputs[core.byte_hash(task["id"]) + "/actor/0"] = raw
        self.outputs.update(overrides or {})

    def generate(self, request, limits):
        self.requests.append(copy.deepcopy(request))
        return {"request_sha256": prepare.digest(request), "text": self.outputs.get(request["id"], "MISS"),
                "prompt_tokens": 100, "output_tokens": self.output_tokens, "device_seconds": self.device_seconds}

    def count_tokens(self, text):
        return self.returned_tokens

    def close(self):
        self.closed = True
        return {"owned_group_released": not self.bad_release, "gpu_vacant": not self.bad_release,
                "kind": "MOCKED_NO_PROCESS"}


def formation_fixture(contract):
    root = core.from_data(next(entry for entry in contract["bindings"]["root_registry"] if entry["id"] == "disposable/0")["wire"])
    cell = core.WorldCell(root, 0, 0, 0)
    session = core.WorldSession(cell, "OLD")
    generations, rows = [], []

    def capture(kind, raw, prompt):
        index = len(generations)
        generations.append({"id": f"generation/{index}", "kind": kind, "raw": raw,
                            "sha256": core.byte_hash(raw), "span": [0, len(raw.encode("utf-8"))],
                            "started": index * 2, "ended": index * 2 + 1,
                            "prompt_sha256": core.byte_hash(prompt)})

    for index in range(8):
        public = session.public_affordances()
        action = "EXPLORE " + public["source"] + " " + public["ports"][0]
        capture("EXPLORE", action, session.explore_prompt())
        receipt = session.explore(action)["receipt"]
        fields = {key: receipt[key] for key in ("source", "port", "destination", "receipt")}
        fields["event"] = root.lookup("event", f"e{index}")
        raw = contract["bindings"]["core_registry"]["parser_registry"]["event_template"].format(**fields)
        capture("EVENT", raw, session.event_prompt(receipt))
        rows.append(core.admit_event(raw, receipt, session, fields["event"])["row"])
    pairs = [(first, second) for first in rows for second in rows if first["fields"]["destination"] == second["fields"]["source"]][:4]
    for index, (first, second) in enumerate(pairs):
        fields = {"link": root.lookup("link", f"l{index}"), "first": first["fields"]["event"],
                  "second": second["fields"]["event"], "via": first["fields"]["destination"],
                  "receipt_first": first["fields"]["receipt"], "receipt_second": second["fields"]["receipt"]}
        raw = contract["bindings"]["core_registry"]["parser_registry"]["link_template"].format(**fields)
        capture("LINK", raw, session.link_prompt())
        receipts = [next(receipt for receipt in session.receipts if receipt["receipt"] == row["fields"]["receipt"]) for row in (first, second)]
        rows.append(core.admit_link(raw, receipts, session, fields["link"], [first, second])["row"])
    queries = core.materialize_queries(rows)
    slots = []
    by_support = {row["fields"].get("event", row["fields"].get("link")): row for row in rows}
    for index, query in enumerate(queries.values()):
        slots.append({"id": f"slot/{index}", "source": None, "request": query["request"],
                      "support": query["support"], "row_type": by_support[query["support"][0]]["kind"],
                      "bank": {support: by_support[support]["fields"] for support in query["support"]}, "taint": "AUTHENTIC"})
    contract["bindings"]["slot_registry"] = [{"id": "disposable/auth", "root": root.label, "slots": slots}]
    return {"contract_sha256": prepare.digest(contract), "root": root.label, "corpus": "disposable/auth", "generations": generations}


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = fixture_contract()
        cls.plan = runtime.prepare_scripted_plan(cls.contract)

    def make_runtime(self, backend=None, contract=None, **kwargs):
        contract = copy.deepcopy(contract or self.contract)
        backend = backend or ScriptedBackend(self.plan)
        with patch.object(prepare, "validate_execution_contract", side_effect=bridge_report):
            result = runtime.Runtime(contract, backend, scripted=True, **kwargs)
        return result, backend

    def test_full_800_unmocked_public_cpu_scorer_path(self):
        driver, backend = self.make_runtime()
        report = driver.run_initial()
        self.assertEqual(report["status"], "AWAITING_DISPOSABLE_EXACT_CHILD_SPANS")
        self.assertEqual(report["calls_executed"], 800)
        self.assertEqual(report["missing_tasks"], 0)
        self.assertEqual(report["panels"]["delayed/NATIVE_CONTEXT"]["correct"], 64)
        self.assertEqual(report["panels"]["reachout/FULL_CHILD_TEXT"]["correct"], 32)
        self.assertEqual(len(report["construct"]["route_cut_decisions"]), 192)
        self.assertEqual(report["fits_executed"], 0)
        self.assertFalse(report["scientific_pass"])
        self.assertTrue(backend.closed)
        self.assertEqual(report["stages"]["CAL_LOW"], "NOT_IMPLEMENTED")
        self.assertTrue(all(set(request) == {"id", "messages", "seed", "mount"} for request in backend.requests))
        with self.assertRaisesRegex(runtime.RuntimeStop, "ALREADY_CONSUMED"):
            driver.run_initial()

    def test_failed_ceiling_never_inspects_formation(self):
        backend = ScriptedBackend(self.plan)
        backend.outputs = {}
        driver, _ = self.make_runtime(backend)
        report = driver.run_initial(formation={"bad": "never inspect"})
        self.assertEqual(report["status"], "VS_ASSAY_INVALID_MODEL_CEILING")
        self.assertEqual(report["panels"]["delayed/NATIVE_CONTEXT"]["denominator"], 64)
        self.assertNotIn("formation", report)
        self.assertEqual(report["fits_executed"], 0)

    def test_native_mode_cannot_use_scripted_evidence(self):
        with patch.object(prepare, "validate_execution_contract", side_effect=bridge_report):
            with self.assertRaisesRegex(runtime.RuntimeStop, "NATIVE_BINDING_UNIMPLEMENTED"):
                runtime.Runtime(self.contract, ScriptedBackend(self.plan))

    def test_native_stays_blocked_even_with_claimed_green_validator(self):
        validation = bridge_report(self.contract)
        validation.update(execution_contract_valid=True, missing_interfaces=[])
        with patch.object(prepare, "validate_execution_contract", return_value=validation):
            with self.assertRaisesRegex(runtime.RuntimeStop, "production D"):
                runtime.Runtime(self.contract, ScriptedBackend(self.plan), scripted=False)

    def test_unmocked_preparer_rejects_partial_contract_without_calls(self):
        backend = ScriptedBackend(self.plan)
        with self.assertRaises(prepare.ExecutionContractError):
            runtime.Runtime(self.contract, backend, scripted=True)
        self.assertEqual(backend.requests, [])

    def test_unmocked_preparer_bridge_accepts_only_scripted_use(self):
        from tests.test_pcfl_vertical_prepare import synthetic_bindings, synthetic_tokenizer

        bindings = synthetic_bindings()
        contract = prepare.build_execution_contract(bindings, synthetic_tokenizer(bindings))
        backend = ScriptedBackend(runtime.prepare_scripted_plan(contract))
        driver = runtime.Runtime(contract, backend, scripted=True)
        self.assertTrue(driver.validation["bridge_invariants_valid"])
        self.assertFalse(driver.validation["execution_contract_valid"])
        self.assertEqual(len(driver.plan["tasks"]), 800)
        self.assertEqual(backend.requests, [])

    def test_generation_exception_preserves_attempt_and_releases(self):
        driver, backend = self.make_runtime()
        with patch.object(backend, "generate", side_effect=RuntimeError("scripted failure")):
            report = driver.run_initial()
        self.assertEqual(report["status"], "GENERATION_FAILED")
        self.assertEqual(report["generation_attempts"], 1)
        self.assertEqual(report["calls_executed"], 0)
        self.assertTrue(report["device_cost_incomplete"])
        self.assertTrue(backend.closed)

    def test_wrong_root_false_row_real_scorer_not_just_route_zero(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "WRONG_ROOT")
        cell = core.from_data(task["cell"])
        raw = "MISS\n" + core.ideal_rows(cell)[0]["raw"]
        backend = ScriptedBackend(self.plan, {core.byte_hash(task["id"]) + "/actor/0": raw})
        driver, _ = self.make_runtime(backend)
        result = driver._task(task)
        self.assertTrue(result["usable_false_row"])
        self.assertFalse(result["success"])

    def test_loaded_api_and_registry_are_distinct(self):
        driver, _ = self.make_runtime()
        self.assertIs(runtime.core_api, core)
        self.assertIsInstance(driver.contract_data["bindings"]["core_registry"], dict)
        self.assertTrue(callable(runtime.core_api.score_route))

    def test_plan_drift_blocks_all_calls_and_releases(self):
        driver, backend = self.make_runtime()
        driver.plan["tasks"][0]["seed"] += 1
        report = driver.run_initial()
        self.assertEqual(report["status"], "VS_ASSAY_INVALID")
        self.assertEqual(len(backend.requests), 0)
        self.assertTrue(backend.closed)

    def test_zero_fit_roster_balancing_and_preoutcome_reachout(self):
        self.assertEqual(panel_counts(self.plan), {"delayed": 640, "reachout": 160})
        for task in self.plan["tasks"]:
            if task["panel"] == "reachout":
                root = core.from_data(task["cell"]).root
                self.assertNotIn(root.lookup("event", "e8"), task["public"]["user"])
                self.assertNotIn(root.lookup("receipt", "r8"), task["public"]["user"])

    def test_service_reads_use_real_public_lookup_with_citations(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        query = next(iter(task["queries"]))
        prefix = core.byte_hash(task["id"]) + "/actor/"
        raw = core.oracle_route_v1(core.from_data(task["cell"]), task["goal"])
        backend = ScriptedBackend(self.plan, {prefix + "0": query, prefix + "1": raw})
        driver, _ = self.make_runtime(backend)
        result = driver._task(task)
        self.assertTrue(result["success"])
        self.assertEqual(result["reads"][0]["raw"], task["queries"][query]["target"])
        self.assertTrue(result["reads"][0]["source_sha256"])
        self.assertEqual(len(backend.requests), 2)
        self.assertNotIn("arrived", str(backend.requests))

    def test_thirteenth_read_is_terminal_no_retry(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        prefix = core.byte_hash(task["id"]) + "/actor/"
        query = next(iter(task["queries"]))
        backend = ScriptedBackend(self.plan, {prefix + str(index): query for index in range(13)})
        driver, _ = self.make_runtime(backend)
        result = driver._task(task)
        self.assertFalse(result["success"])
        self.assertEqual(len(result["reads"]), 12)
        self.assertEqual(len(backend.requests), 13)

    def test_cumulative_tokens_stop_not_per_continuation_reset(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        prefix = core.byte_hash(task["id"]) + "/actor/"
        backend = ScriptedBackend(self.plan, {prefix + "0": next(iter(task["queries"]))})
        backend.output_tokens = 1500
        driver, _ = self.make_runtime(backend)
        with self.assertRaisesRegex(runtime.RuntimeStop, "VS_RESOURCE_CAP"):
            driver._task(task)
        self.assertEqual(len(backend.requests), 2)

    def test_returned_token_cap_prevents_mount(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        prefix = core.byte_hash(task["id"]) + "/actor/"
        backend = ScriptedBackend(self.plan, {prefix + "0": next(iter(task["queries"]))})
        backend.returned_tokens = 4097
        driver, _ = self.make_runtime(backend)
        result = driver._task(task)
        self.assertTrue(result["invalid_read"])
        self.assertEqual(result["reads"], [])
        self.assertEqual(len(backend.requests), 1)

    def test_device_cap_and_release_failure(self):
        backend = ScriptedBackend(self.plan)
        backend.device_seconds = 36001
        backend.bad_release = True
        driver, _ = self.make_runtime(backend)
        report = driver.run_initial()
        self.assertEqual(report["status"], "RELEASE_UNVERIFIED")
        self.assertEqual(report["prior_status"], "VS_RESOURCE_CAP")
        self.assertEqual(report["calls_executed"], 1)

    def test_wall_deadline_before_generation(self):
        driver, backend = self.make_runtime(clock=lambda: 1, deadline=2)
        driver.clock = lambda: 3
        report = driver.run_initial()
        self.assertEqual(report["status"], "VS_RESOURCE_CAP")
        self.assertEqual(backend.requests, [])

    def test_exact_formation_real_admissions_and_real_bank_validator(self):
        contract = copy.deepcopy(self.contract)
        bundle = formation_fixture(contract)
        with patch.object(prepare, "validate_execution_contract", side_effect=bridge_report):
            report = runtime.audit_formation(contract, bundle)
        self.assertTrue(report["report"]["formation_complete"])
        self.assertEqual(len(report["rows"]), 12)
        self.assertFalse(report["native_custody_verified"])
        self.assertTrue(report["bank"]["formation_binding_valid"])
        self.assertTrue(all(row["taint"] == "CHILD_SUBMISSION" for row in report["rows"]))
        self.assertEqual(len(report["span_bindings"]), 12)
        self.assertFalse(report["writer_native_capture_payloads_supplied"])

    def test_initial_path_reaches_cal_boundary_but_never_fits(self):
        contract = copy.deepcopy(self.contract)
        bundle = formation_fixture(contract)
        driver, _ = self.make_runtime(contract=contract)
        with patch.object(prepare, "validate_execution_contract", side_effect=bridge_report):
            report = driver.run_initial(bundle)
        self.assertEqual(report["status"], "CAL_LOW_BINDING_REQUIRED")
        self.assertEqual(report["cal_low_handoff"]["learning_rate"], 3e-5)
        self.assertEqual(report["cal_low_handoff"]["updates"], 200)
        self.assertEqual(report["fits_executed"], 0)
        self.assertEqual(report["stages"]["S1_FOUR_FITS_PER_ROOT"], "NOT_IMPLEMENTED")

    def test_formation_hash_order_prompt_and_bank_mutations(self):
        for mutation in ("hash", "time", "prompt", "bank"):
            with self.subTest(mutation=mutation):
                contract = copy.deepcopy(self.contract)
                bundle = formation_fixture(contract)
                if mutation == "hash":
                    bundle["generations"][1]["raw"] += " "
                elif mutation == "time":
                    bundle["generations"][1]["started"] = 0
                elif mutation == "prompt":
                    bundle["generations"][1]["prompt_sha256"] = "0" * 64
                else:
                    slot = contract["bindings"]["slot_registry"][0]["slots"][0]
                    slot["bank"][slot["support"][0]]["receipt"] = "foreign"
                    bundle["contract_sha256"] = prepare.digest(contract)
                with patch.object(prepare, "validate_execution_contract", side_effect=bridge_report):
                    with self.assertRaises(ValueError):
                        runtime.audit_formation(contract, bundle)

    def test_formation_missing_opportunity_is_not_smaller_denominator(self):
        contract = copy.deepcopy(self.contract)
        bundle = formation_fixture(contract)
        bundle["generations"].pop()
        with self.assertRaisesRegex(runtime.RuntimeStop, "VS_CHILD_OLD_FORMATION_FAIL"):
            runtime.audit_formation(contract, bundle)

    def test_calibration_conservative_table_is_not_old_high_rule(self):
        gates = {name: True for name in prepare.INTEGRITY + prepare.SAFETY + prepare.ACQUISITION}
        gates["event_semantic"] = False
        self.assertEqual(prepare.calibration_transition("CAL_LOW", gates), "RUN_CAL_HIGH")
        gates["pcfl_retention"] = False
        self.assertEqual(prepare.calibration_transition("CAL_LOW", gates), "VS_WRITER_QUALIFICATION_FAIL")
        gates["custody"] = False
        self.assertEqual(prepare.calibration_transition("CAL_LOW", gates), "VS_ASSAY_INVALID")


def panel_counts(plan):
    return {panel: sum(task["panel"] == panel for task in plan["tasks"]) for panel in ("delayed", "reachout")}


if __name__ == "__main__":
    unittest.main()
