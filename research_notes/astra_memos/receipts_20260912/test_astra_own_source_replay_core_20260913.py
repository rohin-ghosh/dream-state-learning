"""CPU fixtures only: scripted responses are not actual model observations."""
import ast
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("own_source_replay_test", "/tmp/astra_own_source_replay_core_20260913.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundles = [core.build(seed) for seed in range(3)]
        cls.material, cls.corpus = core.dependencies()
        cls.dataset, _, _ = core.original_inputs(0)

    def response(self, request, bundle=None):
        bundle = bundle or self.bundles[0]
        observation = next(row for row in bundle["training_observations"] if row["row_id"] == request["row_id"])
        execution = self.corpus.assess_source(observation["source"])["execution"]
        predicted, observed = execution["predicted"], execution["observed"]
        fields = dict(relation="unavailable" if predicted is None else "matched" if predicted == observed else "mismatched",
                      predicted=predicted, observed=observed, **{"try": execution["values"]})
        raw = " \n" + json.dumps(fields, indent=2) + "\t\n"
        return dict(request_id=request["request_id"], input_sha256=request["input_sha256"],
                    producer_sha256=request["producer_sha256"], raw=raw, finish_reason="stop")

    def test_preregistered24_factorial_and_all96_population(self):
        for bundle in self.bundles:
            selected = [row for row in bundle["training_observations"] if row["selected"]]
            self.assertEqual(len(bundle["training_observations"]), 96)
            self.assertEqual(bundle["source_population_denominator"], 96)
            self.assertEqual(bundle["source_admissible"], 48)
            self.assertEqual(len(bundle["requests"]), 24)
            self.assertEqual(Counter(row["source"]["template_id"] for row in selected), {f"train_{index}": 6 for index in range(4)})
            self.assertEqual(Counter(row["public_fields"]["observed"] for row in selected), {True: 12, False: 12})
            self.assertEqual(Counter(row["public_fields"]["predicted"] for row in selected), {True: 8, False: 8, None: 8})
            self.assertEqual(Counter(row["earlier_observed"] == row["public_fields"]["observed"] for row in selected), {True: 12, False: 12})
            self.assertEqual(Counter((row["earlier_observed"], row["public_fields"]["observed"]) for row in selected),
                             {(False, False): 6, (False, True): 6, (True, False): 6, (True, True): 6})

    def test_three_original_parents_same_sources_distinct_request_bindings(self):
        self.assertEqual(len({bundle["selection_sha256"] for bundle in self.bundles}), 1)
        self.assertEqual(self.bundles[0]["selection_sha256"], "5321a8862e2f9c19dddb57c43950351ea9105d9dce123cf4c4c02ee0ca84cbbb")
        self.assertEqual(len({bundle["prompt_manifest_sha256"] for bundle in self.bundles}), 3)
        for seed, bundle in enumerate(self.bundles):
            self.assertEqual(bundle["producer"]["learner_seed"], seed)
            self.assertEqual(bundle["producer"]["adapter_files"]["adapter_model.safetensors"], core.WEIGHT_PINS[seed])
            self.assertIn(f"level1_perception_seed{seed}_", bundle["producer"]["adapter"])
            self.assertFalse(bundle["native_identity_verified"])

    def test_determinism_and_input_immutability(self):
        self.assertEqual(core.encoded(core.build(0)), core.encoded(self.bundles[0]))
        before = core.encoded(self.bundles[0])
        response = self.response(self.bundles[0]["requests"][0])
        raw_before = copy.deepcopy(response)
        core.admit(self.bundles[0], [response])
        self.assertEqual(core.encoded(self.bundles[0]), before)
        self.assertEqual(response, raw_before)

    def test_original_prompt_bytes_and_held_canary_exclusion(self):
        original = {row["row_id"]: row for row in self.dataset["training"]}
        bundle = self.bundles[0]
        excluded = {row["row_id"] for rows in bundle["excluded"].values() for row in rows}
        self.assertEqual(len(excluded), 60)
        for request in bundle["requests"]:
            self.assertNotIn(request["row_id"], excluded)
            self.assertEqual(request["input_messages"], original[request["row_id"]]["input_messages"])
            self.assertEqual(request["source_split"], "train")
            self.assertNotIn("diagnosis", request)
            self.assertNotIn("public_fields", request)
            self.assertNotIn("source_proof", request)

    def test_authored_answers_and_proofs_not_used(self):
        poisoned = copy.deepcopy(self.dataset)
        for rows in [poisoned["training"], *poisoned["evaluation"].values()]:
            for row in rows:
                row["raw_target"] = object()
                row["target_sha256"] = object()
                row["source_proof"] = object()
        with patch.object(self.material, "expected", side_effect=AssertionError("no authored answers")), patch.object(self.material, "score_row", side_effect=AssertionError("no authored scorer")):
            result = core.inventory(poisoned, self.material, self.corpus)
        self.assertEqual(result[0], self.bundles[0]["training_observations"])
        self.assertEqual(result[1], self.bundles[0]["excluded"])
        encoded = core.encoded(self.bundles[0])
        self.assertNotIn(b'"raw_target":', encoded)
        self.assertNotIn(b'"target_sha256":', encoded)

    def test_all24_scripted_records_preserve_raw_bytes_not_expected(self):
        bundle = self.bundles[0]
        responses = [self.response(request) for request in bundle["requests"]]
        result = core.admit(bundle, responses)
        self.assertEqual(result["admitted_count"], 24)
        self.assertEqual(result["requested_denominator"], 24)
        self.assertEqual(result["source_population_denominator"], 96)
        self.assertEqual(result["status_counts"], dict(admitted=24, source_supported_not_selected=24, source_unsupported_not_requested=48))
        by_request = {response["request_id"]: response for response in responses}
        for admitted in result["admitted"]:
            self.assertEqual(admitted["raw_target"].encode(), by_request[admitted["request_id"]]["raw"].encode())
            self.assertEqual(admitted["target_sha256"], core.sha(admitted["raw_target"].encode()))
            self.assertEqual(admitted["source_proof"]["target_origin"], "SUPPLIED_RAW_CHILD_RESPONSE_ONLY")
        self.assertFalse(result["training_export_ready"])
        self.assertIsNone(result["fit_decision"])

    def test_no_responses_no_host_targets_and_24_missing(self):
        result = core.admit(self.bundles[0], [])
        self.assertEqual(result["admitted"], [])
        self.assertEqual(len(result["missing_request_ids"]), 24)
        self.assertEqual(result["status_counts"]["response_missing"], 24)
        self.assertEqual(sum(result["status_counts"].values()), 96)

    def test_fence_prose_and_bool_int_rejected_without_repair(self):
        request = self.bundles[0]["requests"][0]
        valid = self.response(request)
        responses = []
        for request, kind in zip(self.bundles[0]["requests"][:3], ("fence", "prose", "boolint")):
            response = self.response(request)
            if kind == "fence":
                response["raw"] = "```json\n" + response["raw"] + "\n```"
            elif kind == "prose":
                response["raw"] = "Here is the record: " + response["raw"]
            else:
                fields = json.loads(response["raw"])
                fields["observed"] = int(fields["observed"])
                response["raw"] = json.dumps(fields)
            responses.append(response)
        result = core.admit(self.bundles[0], responses)
        self.assertEqual(result["admitted_count"], 0)
        self.assertEqual(len(result["rejected"]), 3)
        self.assertEqual([audit["response"]["raw"] for audit in result["responses"]], [response["raw"] for response in responses])

    def test_wrong_outcome_prior_or_selected_action_rejected(self):
        bundle = self.bundles[0]
        responses = []
        for request, field in zip(bundle["requests"][:3], ("observed", "predicted", "try")):
            response = self.response(request)
            parsed = json.loads(response["raw"])
            if field == "try":
                parsed[field][0] += 1
            elif field == "predicted":
                parsed[field] = not parsed[field]
            else:
                parsed[field] = not parsed[field]
            response["raw"] = json.dumps(parsed)
            responses.append(response)
        result = core.admit(bundle, responses)
        self.assertEqual(result["admitted_count"], 0)
        self.assertEqual(len(result["rejected"]), 3)

    def test_absent_prior_cannot_be_invented_from_outcome(self):
        bundle = self.bundles[0]
        observation = next(row for row in bundle["training_observations"] if row["selected"] and row["diagnosis"] == "absent_prediction")
        request = next(request for request in bundle["requests"] if request["row_id"] == observation["row_id"])
        response = self.response(request)
        parsed = json.loads(response["raw"])
        parsed["predicted"] = parsed["observed"]
        parsed["relation"] = "matched"
        response["raw"] = json.dumps(parsed)
        result = core.admit(bundle, [response])
        self.assertIn("prediction mismatch", result["rejected"][0]["errors"])

    def test_stop_required_even_when_source_judge_accepts(self):
        response = self.response(self.bundles[0]["requests"][0])
        response["finish_reason"] = "length"
        result = core.admit(self.bundles[0], [response])
        self.assertEqual(result["admitted_count"], 0)
        self.assertTrue(result["responses"][0]["source_judge"]["eligible"])
        self.assertIn("stop_completion_required", result["rejected"][0]["errors"])

    def test_wrong_producer_and_prompt_binding_rejected(self):
        requests = self.bundles[0]["requests"][:2]
        responses = [self.response(request) for request in requests]
        responses[0]["producer_sha256"] = self.bundles[1]["producer_sha256"]
        responses[1]["input_sha256"] = "0" * 64
        result = core.admit(self.bundles[0], responses)
        self.assertEqual(result["admitted_count"], 0)
        self.assertIn("original_parent_model_adapter_binding_mismatch", result["rejected"][0]["errors"])
        self.assertIn("input_prompt_binding_mismatch", result["rejected"][1]["errors"])

    def test_duplicate_no_best_of_or_retry_selection(self):
        response = self.response(self.bundles[0]["requests"][0])
        result = core.admit(self.bundles[0], [response, copy.deepcopy(response)])
        self.assertEqual(result["admitted_count"], 0)
        self.assertEqual(len(result["rejected"]), 2)
        self.assertEqual(result["status_counts"]["response_rejected"], 1)
        for rejected in result["rejected"]:
            self.assertIn("duplicate_response_no_retry_selection", rejected["errors"])

    def test_held_canary_or_unselected_response_never_admitted(self):
        response = self.response(self.bundles[0]["requests"][0])
        responses = []
        for excluded in (self.bundles[0]["excluded"]["held"][0], self.bundles[0]["excluded"]["canary"][0]):
            responses.append(dict(response, request_id=excluded["row_id"]))
        unselected = next(row for row in self.bundles[0]["training_observations"] if not row["selected"])
        responses.append(dict(response, request_id=unselected["row_id"]))
        result = core.admit(self.bundles[0], responses)
        self.assertEqual(result["admitted_count"], 0)
        self.assertEqual(len(result["rejected"]), 3)
        self.assertEqual(len(result["missing_request_ids"]), 24)

    def test_held_in_train_or_cross_split_source_rejected(self):
        for case in ("replace", "duplicate"):
            dataset = copy.deepcopy(self.dataset)
            if case == "replace":
                dataset["training"][0], dataset["evaluation"]["held"][0] = dataset["evaluation"]["held"][0], dataset["training"][0]
            else:
                dataset["evaluation"]["held"][0] = copy.deepcopy(dataset["training"][0])
            with self.subTest(case=case), self.assertRaises(ValueError):
                core.inventory(dataset, self.material, self.corpus)

    def test_tampered_bundle_or_descendant_parent_rejected(self):
        for case in ("prompt", "parent"):
            bundle = copy.deepcopy(self.bundles[0])
            if case == "prompt":
                bundle["requests"][0]["input_messages"][0]["content"] += "\nTeacher answer appended"
            else:
                bundle["producer"]["adapter"] = "/some/WRITE_descendant/adapter"
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, "fixed original TRAIN"):
                core.admit(bundle, [])

    def test_source_and_archive_pins_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="own_replay_cpu_") as home:
            path = Path(home) / "fake.tar"
            path.write_text("not archived source")
            with self.assertRaisesRegex(ValueError, "archive pin"):
                core.original_inputs(0, path)
            with self.assertRaisesRegex(ValueError, "source pin"):
                core.load(path, core.MATERIAL_PIN, "fake")
        with self.assertRaises(ValueError):
            core.original_inputs(True)

    def test_no_generator_expected_scorer_or_native_calls_in_core(self):
        forbidden = {"expected", "score_row", "build_dataset", "run_training", "generate", "fit_arm", "score_calls"}
        tree = ast.parse(core.SELF.read_text())
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & forbidden)


if __name__ == "__main__":
    unittest.main()
