"""Synthetic in-memory fixtures only. No repository imports or live file reads."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import mock_open, patch


SPEC = importlib.util.spec_from_file_location("independent_conditional", "/tmp/astra_independent_conditional_analysis_20260912.py")
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def case_fixture(operation, split, square, first, second):
    identifier = f"{split}-{operation}-{square}-{first}{second}"
    actions, outcomes = ["dax", "wug"], ["fep", "nup"]
    if operation == "PROSPECT":
        inputs = dict(actions=actions, outcomes=outcomes, action_order=actions,
                      belief=dict(zip(actions, outcomes[first:] + outcomes[:first])), goal=outcomes[second])
        factors = dict(belief=first, goal=second)
        chosen = actions[first ^ second]
        other = actions[1 ^ first ^ second]
        auth = f"PREDICT: {chosen} -> {outcomes[second]}\nACT: {chosen}"
        deranged = f"PREDICT: {other} -> {outcomes[1 ^ second]}\nACT: {other}"
    else:
        inputs = dict(actions=actions, outcomes=outcomes, action_order=actions,
                      prior_action=actions[first], expected="fep", observed=outcomes[second])
        factors = dict(prior_action=first, mismatch=second)
        auth = f"COMPARE: {'MISMATCH' if second else 'MATCH'}\nPOLICY: {'SWITCH' if second else 'KEEP'}\nNEXT: {actions[first ^ second]}"
        deranged = f"COMPARE: {'MATCH' if second else 'MISMATCH'}\nPOLICY: {'KEEP' if second else 'SWITCH'}\nNEXT: {actions[first ^ second ^ 1]}"
    case = dict(id=identifier, operation=operation, split=split, inputs=inputs, factors=factors,
                template=square % 2, context=f"SYNTHETIC input only {identifier}")
    return case, {"AUTH": auth, "DERANGED": deranged}


def candidate_fixture():
    candidate = dict(root=0, spellings=dict(actions=["dax", "wug"], outcomes=["fep", "nup"]),
        composition=dict(status="UNTRAINED_FUTURE_ASSAY", trained_chain_rows=0), train={"AUTH": [], "DERANGED": []}, dev=[], twins={})
    texts = {}
    for split, number in (("train", 16), ("dev", 8)):
        candidate["twins"][split] = {family: [] for family in ("belief", "goal", "outcome", "prior_action")}
        for operation in ("PROSPECT", "REVISE"):
            for square in range(number):
                ids = {}
                for first in (0, 1):
                    for second in (0, 1):
                        case, expected = case_fixture(operation, split, square, first, second)
                        ids[first, second] = case["id"]
                        texts[case["id"]] = expected
                        if split == "train":
                            for assigned_map in ("AUTH", "DERANGED"):
                                candidate["train"][assigned_map].append(dict(case, response=expected[assigned_map]))
                        else:
                            candidate["dev"].append(case)
                for bit in (0, 1):
                    first_family, second_family = ("belief", "goal") if operation == "PROSPECT" else ("prior_action", "outcome")
                    candidate["twins"][split][first_family].append([ids[0, bit], ids[1, bit]])
                    candidate["twins"][split][second_family].append([ids[bit, 0], ids[bit, 1]])
    return candidate, texts


def control_fixture():
    return ([dict(id=f"addition-{index}", context=f"SYNTHETIC sum {index}+3", expected=index + 3, family="addition") for index in range(16)] +
            [dict(id=f"copy-{index}", context=f"SYNTHETIC copy {index % 8}", expected=analysis.COPY_ACTIONS[index % 8], family="copy") for index in range(16)])


def raw_values(candidate):
    records = {}
    for family in ("belief", "outcome"):
        for first, second in candidate["twins"]["dev"][family]:
            if family == "belief":
                records[first] = dict(AUTH_X0=-2., AUTH_X1=-5., DERANGED_X0=-4., DERANGED_X1=-10.)
                records[second] = dict(AUTH_X0=-4., AUTH_X1=-3., DERANGED_X0=-8., DERANGED_X1=-5.)
            else:
                records[first] = dict(AUTH_X0=-2., AUTH_X1=-5.)
                records[second] = dict(AUTH_X0=-4., AUTH_X1=-3.)
    return records


def capsule_fixture():
    candidate, texts = candidate_fixture()
    controls = control_fixture()
    registered = analysis.registry(candidate)
    records = raw_values(candidate)
    files, reductions, attempts, supervisors, phase_rows = {}, [], [], {}, []
    material = {"candidate.json": analysis.value_hash(candidate)}
    shared = dict(source_hashes={"synthetic.py": "a" * 64}, model_files={"synthetic-base": "b" * 64},
                  material_inventory=material, material="/synthetic/material", material_manifest_sha256="c" * 64,
                  device="0", model="/synthetic/model", candidate_sha256=analysis.value_hash(candidate),
                  controls=controls, worker_seconds=600, resource_budget={"total_a40_seconds": 5400}, lease_end=10000.)
    manifest = dict(assay_version=analysis.ASSAY, generation_calls=672, candidate_forwards=576,
                   prior_fit_full_reservation_seconds=464.397178, controller_seconds=4500,
                   source_hashes=shared["source_hashes"], model_files=shared["model_files"],
                   material_inventory=material, device="0", phases=phase_rows)

    def put(path, value):
        files[path] = analysis.encoded(value)

    for state in analysis.STATES:
        for phase in ("generate", "score"):
            name = f"{state}_{phase}"
            root = f"/synthetic/{name}"
            adapter = None if state == "OFF" else f"/synthetic/{state}"
            adapter_files = {} if state == "OFF" else {"synthetic-adapter": state}
            plan = dict(shared, state=state, phase=phase, adapter=adapter, adapter_files=adapter_files,
                        identity=dict(backend="synthetic", state=state), requests=[], native_inputs=[],
                        assay_version=analysis.ASSAY if phase == "score" else None,
                        prospect_contrast=analysis.CONTRAST if phase == "score" else None)
            costs = dict.fromkeys(analysis.COST_KEYS, 0)
            usage = {}
            outputs = {}
            panel = ([(case, "train") for case in candidate["train"]["AUTH"]] + [(case, "dev") for case in candidate["dev"]] +
                     [(case, "control") for case in controls]) if phase == "generate" else [(case, "score") for case in candidate["dev"]]
            for index, (case, role) in enumerate(panel):
                call_id = f"{index:04d}"
                request = dict(call_id=call_id, case_id=case["id"], role=role, arm=state, prompt=case["context"])
                if phase == "generate":
                    request.update(split=role, max_tokens=64, temperature=0.0, seed=20260912)
                    native = dict(call_id=call_id, rendered_prompt=case["context"] + "\nASSISTANT:", prompt_token_ids=[1, 2, 3])
                    plan["native_inputs"].append(native)
                    text = f"ACT: {case['expected']}" if role == "control" else texts[case["id"]]["AUTH"]
                    response = dict(text=text, rendered_prompt=native["rendered_prompt"], prompt_token_ids=[1, 2, 3], output_token_ids=[7, 9])
                    outputs[case["id"]] = text
                    delta = dict(requests=1, native_input_tokens=3, native_output_tokens=2, output_token_ceiling=64, generation_seconds=.5)
                    by_role = usage.setdefault(role, dict.fromkeys(delta, 0))
                    by_arm = by_role.setdefault("by_arm", {}).setdefault(state, dict.fromkeys(delta, 0))
                    for key, value in delta.items():
                        by_role[key] += value
                        by_arm[key] += value
                    costs["native_input_tokens"] += 3
                    costs["native_output_tokens"] += 2
                    costs["output_token_ceiling"] += 64
                else:
                    request.update(operation=case["operation"], assay_version=analysis.ASSAY,
                        rendered_prompt=case["context"] + "\nASSISTANT:", payload=dict(prompt_input_ids=[1, 2, 3]),
                        candidate_pairs=registered[case["id"]]["candidate_pairs"], candidates=[])
                    values = []
                    for choice_index, choice in enumerate(registered[case["id"]]["choices"]):
                        target = [10 + choice_index] * (choice_index + 1) + [99]
                        request["candidates"].append(dict(choice, response_ids=target, input_ids=[1, 2, 3] + target,
                                                          labels=[-100] * 3 + target))
                        total = records[case["id"]][choice["candidate_id"]]
                        values.append([0.] * (len(target) - 1) + [total])
                        costs["native_input_tokens"] += 3 + len(target)
                        costs["scored_target_tokens"] += len(target)
                    response = dict(token_logprobs=values)
                    costs["candidate_forwards"] += len(values)
                    costs["padded_forward_tokens"] += 28 if len(values) == 4 else 12
                plan["requests"].append(request)
                costs["requests"] += 1
                costs["call_seconds"] += .5
                stem = f"{name}/run/data/calls/{call_id}"
                put(stem + ".request.json", dict(request=request, identity=plan["identity"],
                    prompt_sha256=analysis.value_hash(request["prompt"]), started=float(index)))
                put(stem + ".response.json", dict(response=response, response_sha256=analysis.value_hash(response), ended=index + .5))
            put(f"{name}/plan.json", plan)
            plan_sha = analysis.sha(files[f"{name}/plan.json"])
            put(f"{name}/plan.sha256.json", dict(sha256=plan_sha))
            phase_rows.append(dict(state=state, phase=phase, root=root, plan_sha256=plan_sha))
            data = f"{name}/run/data"
            put(f"{data}/identity.json", dict(backend=plan["identity"], model_files=plan["model_files"], adapter_files=adapter_files))
            put(f"{data}/backend.ready.json", dict(ready=True))
            put(f"{data}/backend.cleanup.json", dict(closed=True))
            if phase == "generate":
                put(f"{data}/usage.json", usage)
                result, _ = analysis.generation_result(candidate, controls, outputs)
                result.update(shared_off=state == "OFF", own_map=None if state == "OFF" else state)
                result["controls"].update(copied_prompt_executions=16, unique_copy_prompts=8)
            else:
                _, compact = analysis.interactions(candidate, records)
                result = dict(operations=compact, candidate_logprob_sums=records, scored_cases=64, candidate_forwards=192,
                              assay_version=analysis.ASSAY, prospect_contrast=analysis.CONTRAST)
            put(f"{data}/manifest.json", dict(files={path[len(data) + 1:]: analysis.sha(payload) for path, payload in files.items() if path.startswith(data + "/")}))
            receipt = dict(ok=True, reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True,
                           returncode=0, error=None, device="0", reserved_seconds=200.)
            process = dict(timeout=600, pid=123, pgid=123, device="0")
            put(f"{name}/run/worker/supervision.json", receipt)
            put(f"{name}/run/worker/process.json", process)
            supervisors[name] = receipt
            reduction = dict(status="COMPLETE_PHASE", complete=True, state=state, phase=phase, root=root, plan_sha256=plan_sha,
                             reserved_seconds=200., cost=costs, result=result,
                             **{key: plan[key] for key in ("material_inventory", "source_hashes", "model_files", "adapter_files", "assay_version", "resource_budget")})
            reductions.append(reduction)
            attempt = dict(name=name, root=root, plan_sha256=plan_sha, supervision=receipt, process=process, reduction=reduction)
            attempts.append(attempt)
            put(f"controller/phases/{name}.json", attempt)
    projected_phases = {f"{row['state']}_{row['phase']}": dict(result=row["result"]) for row in reductions}
    summary = dict(status="COMPLETE_ROOT0_READOUT_NOT_L1_VERDICT", complete=True, reductions=reductions,
        comparisons=analysis.comparisons(projected_phases), actual_generation_calls=672, actual_scoring_requests=192,
        candidate_forwards=576, assay_version=analysis.ASSAY, supplies_l1_verdict=False,
        cost={key: sum(row["cost"][key] for row in reductions) for key in analysis.COST_KEYS}, readout_reserved_seconds=1200.)
    terminal = dict(status="COMPLETE", attempts=attempts, supervision=supervisors, summary=summary,
        completed_phases=6, release_verified=True, deadline_met=True, error=None, unaccounted_processes=[],
        reserved_seconds=1500., worker_reserved_seconds=1200., started=100., ended=1600.,
        controller_seconds=4500, external_collection_margin_seconds=300, total_ceiling_seconds=5400,
        prior_fit_full_reservation_seconds=464.397178)
    put("controller/summary.json", summary)
    put("controller/terminal.json", terminal)
    files["controller/main_release.xml"] = b"SYNTHETIC RELEASE XML; NOT A GPU OBSERVATION"
    put("controller/main_release.json", dict(full_release=True, controller_absent=True, terminal_status="COMPLETE",
        terminal_sha256=analysis.sha(files["controller/terminal.json"]), xml_sha256=analysis.sha(files["controller/main_release.xml"])))
    put("manifest.json", manifest)
    validation = dict(terminal_status="COMPLETE", technical_complete=True, launch_to_collection_seconds=1550.,
        conservative_total_seconds=2014.397178, collection_seconds=50., terminal_to_collection_seconds=50., postterminal_margin_met=True,
        manifest_sha256=analysis.sha(files["manifest.json"]), files={analysis.PREFIX + "/" + name: analysis.sha(payload) for name, payload in files.items()})
    return analysis.Snapshot(files), manifest, candidate, validation


class SemanticsTests(unittest.TestCase):
    def setUp(self):
        self.candidate, self.texts = candidate_fixture()
        self.prospect = self.candidate["dev"][0]
        self.revise = self.candidate["dev"][32]

    def test_independent_rule_targets_all_training_and_dev(self):
        for case in self.candidate["train"]["AUTH"] + self.candidate["dev"]:
            for assigned_map in analysis.MAPS:
                self.assertEqual(analysis.target_text(case, assigned_map), self.texts[case["id"]][assigned_map])

    def test_strict_and_semantic_separated(self):
        row = analysis.score_text(self.prospect, " ACT:\tdax \n\n PREDICT: dax->fep\r\n", "AUTH")
        self.assertTrue(row["auth_joint_semantic"])
        self.assertFalse(row["strict_surface"])

    def test_wrong_map_strict_but_auth_incorrect(self):
        row = analysis.score_text(self.prospect, "PREDICT: wug -> nup\nACT: wug", "DERANGED")
        self.assertTrue(row["own_map_strict_joint"])
        self.assertFalse(row["auth_joint_semantic"])

    def test_duplicate_field_stays_ambiguous(self):
        row = analysis.score_text(self.prospect, "PREDICT: dax -> fep\nACT: dax\nACT: dax\nACT: dax", "AUTH")
        self.assertEqual(row["fields"], dict(PREDICT_ACTION="dax", PREDICT_OUTCOME="fep"))
        self.assertFalse(row["auth_joint_semantic"])

    def test_prose_unknown_label_alias_missing_fields(self):
        for text in ("PREDICT: dax -> fep\nACT: dax\nThanks", "PREDICT: foo -> fep\nACT: dax", "ACT: dax", "act: dax", ""):
            with self.subTest(text=text):
                self.assertFalse(analysis.score_text(self.prospect, text, "AUTH")["auth_joint_semantic"])

    def test_revise_semantics_and_trailing_newline(self):
        row = analysis.score_text(self.revise, "NEXT: dax\nPOLICY: KEEP\nCOMPARE: MATCH\n", "AUTH")
        self.assertTrue(row["auth_joint_semantic"])
        self.assertFalse(row["strict_surface"])

    def test_generation_analytical_denominators(self):
        outputs = {case_id: targets["AUTH"] for case_id, targets in self.texts.items()}
        result, missing = analysis.generation_result(self.candidate, control_fixture(), outputs)
        for split, count in (("train", 64), ("dev", 32)):
            for operation in analysis.OPERATIONS:
                auth = result["primary"][split]["AUTH"]["operations"][operation]
                other = result["primary"][split]["DERANGED"]["operations"][operation]
                self.assertEqual(auth["total"], count)
                self.assertEqual(auth["auth_strict_joint"], count)
                self.assertEqual(other["own_map_joint_semantic"], 0)
                self.assertEqual(other["auth_joint_semantic"], count)
            for family in analysis.FLIPS:
                self.assertEqual(result["primary"][split]["AUTH"]["twins"][family]["auth_strict_passes"], count // 2)
                self.assertEqual(missing[split]["AUTH"][family], [])

    def test_copy_duplicates_require_both_executions(self):
        controls = control_fixture()
        outputs = {case["id"]: f"ACT: {case['expected']}" for case in controls}
        del outputs["copy-8"]
        result = analysis.control_result(controls, outputs)
        self.assertEqual(result["families"]["copy"]["total"], 15)
        self.assertEqual(result["families"]["copy"]["unique_all_correct"], 7)

    def test_frozen_copy_hyphen_validity_and_spill(self):
        controls = [dict(id="copy", context="synthetic", expected="-loop-unroll", family="copy"),
                    dict(id="sum", context="synthetic addition", expected=5, family="addition")]
        result = analysis.control_result(controls, {"copy": "ACT: -loop-unroll", "sum": "PREDICT: 5\nACT: +5"})
        self.assertTrue(result["rows"][0]["correct"])
        self.assertFalse(result["rows"][0]["valid"])
        self.assertTrue(result["rows"][1]["correct"])
        self.assertTrue(result["rows"][1]["tag_spill"])
        self.assertFalse(result["rows"][1]["exact"])

    def test_duplicate_addition_actions_invalid(self):
        case = dict(id="sum", family="addition", context="synthetic", expected=5)
        result = analysis.control_result([case], {"sum": "ACT: 5\nACT: 5"})
        self.assertFalse(result["rows"][0]["valid"])


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.candidate, _ = candidate_fixture()
        self.records = raw_values(self.candidate)

    def test_four_prospect_vs_two_revise_candidates(self):
        registered = analysis.registry(self.candidate)
        self.assertEqual(sum(len(row["choices"]) for row in registered.values()), 192)
        for case in self.candidate["dev"]:
            self.assertEqual(len(registered[case["id"]]["choices"]), 4 if case["operation"] == "PROSPECT" else 2)

    def test_signed_endpoints_and_separate_maps(self):
        result, _ = analysis.interactions(self.candidate, self.records)
        prospect = result["operations"]["PROSPECT"]
        self.assertEqual(prospect["mean_nats"], dict(AUTH=4., DERANGED=9.))
        auth = prospect["pairs"][0]["maps"]["AUTH"]
        self.assertEqual([endpoint["fixed_A_over_B"]["log_odds_nats"] for endpoint in auth["endpoints"]], [3., -1.])
        self.assertEqual([endpoint["own_target_over_other"]["log_odds_nats"] for endpoint in auth["endpoints"]], [3., 1.])
        self.assertEqual(prospect["registered_twins"], 16)

    def test_revise_negation_not_independent(self):
        result, _ = analysis.interactions(self.candidate, self.records)
        revise = result["operations"]["REVISE"]
        self.assertEqual(revise["mean_nats"], dict(AUTH=4., DERANGED=-4.))
        self.assertTrue(revise["negated_maps_not_independent"])
        self.assertEqual(revise["complete_twins"], 16)

    def test_positive_interaction_does_not_mean_both_endpoints_correct(self):
        first, second = self.candidate["twins"]["dev"]["belief"][0]
        self.records[first].update(AUTH_X0=-2., AUTH_X1=-4.)
        self.records[second].update(AUTH_X0=-2., AUTH_X1=-3.)
        result, _ = analysis.interactions(self.candidate, self.records)
        row = result["operations"]["PROSPECT"]["pairs"][0]["maps"]["AUTH"]
        self.assertEqual(row["interaction_nats"], 1.)
        self.assertEqual(row["endpoints"][1]["own_target_over_other"]["log_odds_nats"], -1.)

    def test_missing_endpoint_preserves_other_endpoint_not_zero_mean(self):
        first, second = self.candidate["twins"]["dev"]["belief"][0]
        del self.records[second]
        result, compact = analysis.interactions(self.candidate, self.records)
        operation = result["operations"]["PROSPECT"]
        self.assertEqual(operation["mean_nats"], dict(AUTH=None, DERANGED=None))
        self.assertEqual(operation["complete_twins"], 15)
        self.assertIsNotNone(operation["pairs"][0]["maps"]["AUTH"]["endpoints"][0])
        self.assertNotIn("PROSPECT", compact)
        self.assertIn("REVISE", compact)

    def test_negative_interactions_not_abs_or_reoriented(self):
        for family in ("belief", "outcome"):
            for first, second in self.candidate["twins"]["dev"][family]:
                self.records[first], self.records[second] = self.records[second], self.records[first]
        result, _ = analysis.interactions(self.candidate, self.records)
        self.assertEqual(result["operations"]["PROSPECT"]["mean_nats"], dict(AUTH=-4., DERANGED=-9.))

    def test_extreme_odds_finite_json_without_clipping_logs(self):
        self.assertIsNone(analysis.odds(1000.)["odds_ratio"])
        self.assertEqual(analysis.odds(-1000.)["odds_ratio"], 0.)
        self.assertEqual(analysis.odds(1000.)["log_odds_nats"], 1000.)


class CapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = capsule_fixture()

    def setUp(self):
        self.snapshot, self.manifest, self.candidate, self.validation = copy.deepcopy(self.fixture)

    def run_analysis(self):
        return analysis.analyze(self.snapshot, self.manifest, self.candidate, self.validation)

    def change(self, name, change):
        value = self.snapshot.read(name)
        change(value)
        self.snapshot.files[name] = analysis.encoded(value)

    def test_complete_synthetic_capsule_counts_and_costs(self):
        result = self.run_analysis()
        self.assertTrue(result["complete"], json.dumps({"issues": result["issues"], "phases": {name: row["issues"] for name, row in result["phases"].items()}}, indent=2))
        self.assertEqual(result["cost"]["requests"], 864)
        self.assertEqual(result["cost"]["candidate_forwards"], 576)
        self.assertEqual(result["cost"]["output_token_ceiling"], 43008)
        self.assertEqual(result["cost"]["native_output_tokens"], 1344)
        self.assertEqual(result["cost"]["scored_target_tokens"], 1824)
        self.assertEqual(result["cost"]["native_input_tokens"], 5568)
        self.assertEqual(result["cost"]["padded_forward_tokens"], 3840)
        self.assertEqual(result["cost"]["call_seconds"], 432.)
        self.assertEqual(result["caps"]["conservative_total_seconds"], 2014.397178)
        self.assertFalse(result["supplies_l1_verdict"])
        self.assertFalse(result["supplies_h1_verdict"])
        self.assertEqual(result["summary_crosscheck"], "MATCH")

    def test_missing_phase_refuses_stored_complete_preserves_other_phases(self):
        self.snapshot.files.pop("DERANGED_score/plan.json")
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertTrue(result["complete_assertion_refused"])
        self.assertIsNone(result["cost"])
        self.assertTrue(result["phases"]["OFF_score"]["complete"])
        self.assertEqual(result["phases"]["OFF_score"]["result"]["operations"]["PROSPECT"]["mean_nats"]["AUTH"], 4.)

    def test_duplicate_manifest_phase_cannot_hide_missing_phase(self):
        self.manifest["phases"][-1] = copy.deepcopy(self.manifest["phases"][-2])
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertFalse(result["phases"]["DERANGED_score"]["complete"])
        self.assertFalse(result["phases"]["DERANGED_generate"]["complete"])

    def test_no_raw_generation_is_observed_empty_not_complete(self):
        self.snapshot.files = {path: payload for path, payload in self.snapshot.files.items()
                               if not path.startswith("OFF_generate/run/data/calls/")}
        result = self.run_analysis()
        phase = result["phases"]["OFF_generate"]
        self.assertEqual(phase["observed_valid_calls"], 0)
        self.assertFalse(phase["raw_panel_complete"])
        self.assertIsNone(phase["cost"])
        self.assertEqual(len(phase["missing_calls"]), 224)
        self.assertFalse(phase["generation_coverage"]["dev"]["PROSPECT"]["complete_cell"])

    def test_missing_generation_is_not_a_failure_or_zero_rate(self):
        self.snapshot.files.pop("AUTH_generate/run/data/calls/0000.response.json")
        result = self.run_analysis()
        phase = result["phases"]["AUTH_generate"]
        self.assertEqual(phase["observed_valid_calls"], 223)
        self.assertIsNone(phase["cost"])
        coverage = phase["generation_coverage"]["train"]["PROSPECT"]
        self.assertEqual(coverage["observed_denominator"], 63)
        self.assertEqual(coverage["registered_denominator"], 64)
        self.assertIsNone(coverage["scientific_rate"])
        self.assertFalse(coverage["complete_cell"])
        self.assertIsNone(result["comparisons"])

    def test_stored_result_corruption_detected_without_affecting_raw_result(self):
        name = "controller/phases/OFF_score.json"
        self.change(name, lambda row: row["reduction"]["result"]["operations"]["PROSPECT"]["map_oriented"]["AUTH"].update(mean_nats=99.))
        attempt = self.snapshot.read(name)
        self.change("controller/terminal.json", lambda row: row["attempts"].__setitem__(1, attempt))
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        phase = result["phases"]["OFF_score"]
        self.assertEqual(phase["result"]["operations"]["PROSPECT"]["mean_nats"]["AUTH"], 4.)
        self.assertTrue(any("independent/stored result" in error for error in phase["issues"]))

    def test_generation_reducer_tamper_detected(self):
        name = "controller/phases/AUTH_generate.json"
        self.change(name, lambda row: row["reduction"]["result"]["primary"]["dev"]["AUTH"]["operations"]["PROSPECT"].update(auth_joint_semantic=0))
        attempt = self.snapshot.read(name)
        self.change("controller/terminal.json", lambda row: row["attempts"].__setitem__(2, attempt))
        result = self.run_analysis()
        phase = result["phases"]["AUTH_generate"]
        self.assertFalse(phase["complete"])
        self.assertEqual(phase["result"]["primary"]["dev"]["AUTH"]["operations"]["PROSPECT"]["auth_joint_semantic"], 32)

    def test_raw_tamper_preserves_other_diagnostics(self):
        self.change("OFF_generate/run/data/calls/0000.response.json", lambda row: row["response"].update(text="ACT: changed"))
        result = self.run_analysis()
        self.assertEqual(result["phases"]["OFF_generate"]["observed_valid_calls"], 223)
        self.assertFalse(result["complete"])

    def test_missing_score_candidate_not_silently_padded(self):
        path = "OFF_score/run/data/calls/0000.response.json"
        def remove(row):
            row["response"]["token_logprobs"].pop()
            row["response_sha256"] = analysis.value_hash(row["response"])
        self.change(path, remove)
        result = self.run_analysis()
        phase = result["phases"]["OFF_score"]
        self.assertEqual(phase["observed_valid_calls"], 63)
        self.assertIsNone(phase["result"]["operations"]["PROSPECT"]["mean_nats"]["AUTH"])

    def test_partial_terminal_keeps_six_raw_panels_but_not_complete(self):
        self.change("controller/terminal.json", lambda row: row.update(status="PARTIAL", error="synthetic timeout"))
        self.validation.update(terminal_status="PARTIAL", technical_complete=False)
        result = self.run_analysis()
        self.assertEqual(result["status"], "TECHNICAL_PARTIAL")
        self.assertFalse(result["complete"])
        self.assertEqual(result["observed_cost"]["requests"], 864)

    def test_nonterminal_input_refused(self):
        self.change("controller/terminal.json", lambda row: row.update(status="LIVE"))
        with self.assertRaisesRegex(ValueError, "not a terminal"):
            self.run_analysis()

    def test_summary_count_tamper_detected(self):
        self.change("controller/summary.json", lambda row: row.update(candidate_forwards=384))
        summary = self.snapshot.read("controller/summary.json")
        self.change("controller/terminal.json", lambda row: row.update(summary=summary))
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertEqual(result["cost"]["candidate_forwards"], 576)

    def test_aggregate_cap_exceeded(self):
        self.validation.update(launch_to_collection_seconds=5000., conservative_total_seconds=5464.397178)
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertTrue(any("cap exceeded" in error for error in result["issues"]))

    def test_collection_margin_exceeded(self):
        self.validation.update(collection_seconds=301.)
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertTrue(any("cap exceeded" in error for error in result["issues"]))

    def test_reservations_cannot_be_added_or_understated(self):
        self.validation.update(launch_to_collection_seconds=1100., conservative_total_seconds=1564.397178)
        result = self.run_analysis()
        self.assertFalse(result["complete"])
        self.assertTrue(any("shorter than controller" in error for error in result["issues"]))

    def test_unregistered_call_refuses_complete(self):
        self.snapshot.files["OFF_generate/run/data/calls/9999.response.json"] = b"{}"
        result = self.run_analysis()
        self.assertFalse(result["phases"]["OFF_generate"]["complete"])

    def test_cost_tamper_detected(self):
        name = "controller/phases/OFF_score.json"
        self.change(name, lambda row: row["reduction"]["cost"].update(candidate_forwards=128))
        attempt = self.snapshot.read(name)
        self.change("controller/terminal.json", lambda row: row["attempts"].__setitem__(1, attempt))
        result = self.run_analysis()
        self.assertFalse(result["phases"]["OFF_score"]["complete"])
        self.assertEqual(result["phases"]["OFF_score"]["observed_cost"]["candidate_forwards"], 192)


class RawValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot, cls.manifest, cls.candidate, _ = capsule_fixture()

    def fixture(self, phase="score"):
        plan = self.snapshot.read(f"OFF_{phase}/plan.json")
        sent = self.snapshot.read(f"OFF_{phase}/run/data/calls/0000.request.json")
        received = self.snapshot.read(f"OFF_{phase}/run/data/calls/0000.response.json")
        return plan, plan["requests"][0], sent, received

    def call(self, plan, request, sent, received):
        return analysis.raw_call(plan, request, 0, sent, received, analysis.registry(self.candidate), 0)

    def reseal(self, request, sent, received):
        sent["request"] = copy.deepcopy(request)
        sent["prompt_sha256"] = analysis.value_hash(request["prompt"])
        received["response_sha256"] = analysis.value_hash(received["response"])

    def test_sum_includes_eos_scalar_not_length_normalized(self):
        plan, request, sent, received = self.fixture()
        received["response"]["token_logprobs"][0] = [-1., -7.]
        self.reseal(request, sent, received)
        result, costs, _ = self.call(plan, request, sent, received)
        self.assertEqual(result["AUTH_X0"], -8.)
        self.assertEqual(costs["padded_forward_tokens"], 28)
        self.assertEqual(costs["candidate_forwards"], 4)

    def test_nan_infinity_positive_boolean_logprob_refused(self):
        for value in (float("nan"), float("inf"), .1, True):
            plan, request, sent, received = self.fixture()
            received["response"]["token_logprobs"][0][0] = value
            with self.subTest(value=value):
                if type(value) is float and not analysis.finite(value):
                    with self.assertRaises(ValueError):
                        analysis.encoded(received)
                else:
                    self.reseal(request, sent, received)
                    with self.assertRaises(ValueError):
                        self.call(plan, request, sent, received)

    def test_candidate_mass_greater_than_one_refused(self):
        plan, request, sent, received = self.fixture()
        received["response"]["token_logprobs"] = [[0.] * len(choice["response_ids"]) for choice in request["candidates"]]
        self.reseal(request, sent, received)
        with self.assertRaisesRegex(ValueError, "mass"):
            self.call(plan, request, sent, received)

    def test_missing_eos_scalar_refused(self):
        plan, request, sent, received = self.fixture()
        received["response"]["token_logprobs"][0].pop()
        self.reseal(request, sent, received)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.call(plan, request, sent, received)

    def test_answer_bearing_mask_and_bad_input_boundary_refused(self):
        for key, value in (("labels", [0, 0]), ("input_ids", [1, 9])):
            plan, request, sent, received = self.fixture()
            request["candidates"][0][key] = value
            self.reseal(request, sent, received)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "boundary"):
                self.call(plan, request, sent, received)

    def test_fixed_map_relabel_refused(self):
        plan, request, sent, received = self.fixture()
        request["candidate_pairs"]["AUTH"].reverse()
        self.reseal(request, sent, received)
        with self.assertRaisesRegex(ValueError, "orientation"):
            self.call(plan, request, sent, received)

    def test_call_time_and_generation_token_caps(self):
        plan, request, sent, received = self.fixture("generate")
        received["ended"] = 121.
        with self.assertRaisesRegex(ValueError, "time cap"):
            self.call(plan, request, sent, received)
        received["ended"] = .5
        received["response"]["output_token_ids"] = [7] * 65
        self.reseal(request, sent, received)
        with self.assertRaisesRegex(ValueError, "token cap"):
            self.call(plan, request, sent, received)


class SafetyTests(unittest.TestCase):
    def test_json_duplicate_and_nonfinite_rejected(self):
        for payload in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                analysis.decode(payload)

    def test_main_requires_terminal_affirmation_before_reads(self):
        with patch.object(analysis, "local_bytes") as reader, patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(analysis.main(["/synthetic", "--validation", "/synthetic/validation", "--output", "/synthetic/new.json"]), 2)
            reader.assert_not_called()

    def test_main_rejects_pin_drift_before_capsule_read(self):
        with patch.object(analysis, "local_bytes", return_value=b"{}"), patch.object(analysis, "load_snapshot") as loader, patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(analysis.main(["/synthetic", "--validation", "/synthetic/validation", "--output", "/synthetic/new.json", "--terminal-data"]), 2)
            loader.assert_not_called()

    def test_loader_checks_terminal_before_any_raw_reads(self):
        calls = []
        terminal = analysis.encoded(dict(status="LIVE"))
        validation = dict(files={analysis.PREFIX + "/controller/terminal.json": analysis.sha(terminal),
                                 analysis.PREFIX + "/controller/main_release.json": "a" * 64}, terminal_status="LIVE")
        def read(path):
            calls.append(str(path))
            return terminal
        with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "is_symlink", return_value=False), patch.object(analysis, "local_bytes", side_effect=read):
            with self.assertRaisesRegex(ValueError, "nonterminal"):
                analysis.load_snapshot("/synthetic", validation)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].endswith("terminal.json"))

    def test_loader_rejects_traversal_and_weights(self):
        terminal = analysis.encoded(dict(status="PARTIAL"))
        release = analysis.encoded(dict(full_release=True, controller_absent=True))
        for bad in ("../escape", analysis.PREFIX + "/../escape", analysis.PREFIX + "/adapter.safetensors"):
            inventory = {analysis.PREFIX + "/controller/terminal.json": analysis.sha(terminal),
                         analysis.PREFIX + "/controller/main_release.json": analysis.sha(release), bad: "a" * 64}
            def reader(path):
                return terminal if str(path).endswith("terminal.json") else release
            with patch.object(Path, "is_dir", return_value=True), patch.object(Path, "is_symlink", return_value=False), patch.object(analysis, "local_bytes", side_effect=reader):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    analysis.load_snapshot("/synthetic", dict(files=inventory, terminal_status="PARTIAL"))

    def test_local_symlink_refused_without_opening(self):
        with patch.object(Path, "is_symlink", return_value=True), patch.object(analysis.os, "open") as opener:
            with self.assertRaisesRegex(ValueError, "symlink"):
                analysis.local_bytes("/synthetic/link")
            opener.assert_not_called()

    def simulated_main(self, *, exists=False, complete=True):
        manifest_bytes = analysis.encoded(dict(synthetic="manifest"))
        candidate_bytes = analysis.encoded(dict(synthetic="candidate"))
        manifest_hash, candidate_hash = analysis.sha(manifest_bytes), analysis.sha(candidate_bytes)
        validation_bytes = analysis.encoded(dict(manifest_sha256=manifest_hash, terminal_status="COMPLETE"))
        snapshot = analysis.Snapshot({"manifest.json": manifest_bytes})
        result = dict(complete=complete, status="COMPLETE_TEST_ONLY" if complete else "TECHNICAL_PARTIAL")
        def read(path):
            return {"/synthetic/manifest": manifest_bytes, "/synthetic/candidate-material/candidate": candidate_bytes,
                    "/synthetic/validation": validation_bytes}.get(str(path), b"synthetic script bytes")
        opener = mock_open()
        with patch.object(analysis, "MANIFEST_SHA", manifest_hash), patch.object(analysis, "CANDIDATE_SHA", candidate_hash), \
             patch.object(analysis, "local_bytes", side_effect=read), patch.object(analysis, "load_snapshot", return_value=snapshot), \
             patch.object(analysis, "analyze", return_value=result), patch.object(Path, "exists", return_value=exists), \
             patch.object(Path, "is_symlink", return_value=False), patch.object(Path, "open", opener), \
             patch("sys.stdout", new_callable=io.StringIO), patch("sys.stderr", new_callable=io.StringIO):
            code = analysis.main(["/synthetic/extraction", "--manifest", "/synthetic/manifest", "--candidate", "/synthetic/candidate-material/candidate",
                "--validation", "/synthetic/validation", "--output", "/synthetic/new.json", "--terminal-data"])
        return code, opener

    def test_new_output_uses_exclusive_create_and_json_only(self):
        code, opener = self.simulated_main()
        self.assertEqual(code, 0)
        opener.assert_called_once_with("xb")
        payload = opener().write.call_args.args[0]
        self.assertTrue(analysis.decode(payload)["complete"])

    def test_existing_output_not_overwritten(self):
        code, opener = self.simulated_main(exists=True)
        self.assertEqual(code, 2)
        opener.assert_not_called()

    def test_partial_output_is_preserved_with_nonzero_exit(self):
        code, opener = self.simulated_main(complete=False)
        self.assertEqual(code, 2)
        self.assertEqual(analysis.decode(opener().write.call_args.args[0])["status"], "TECHNICAL_PARTIAL")

    def test_no_terminal_marker_no_output(self):
        snapshot = analysis.Snapshot({})
        candidate, _ = candidate_fixture()
        with self.assertRaisesRegex(ValueError, "missing evidence"):
            analysis.analyze(snapshot, {}, candidate, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
