import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("parented_core", "/tmp/astra_parented_record_core_20260913.py")
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)


class Fixture:
    def __init__(self, invalid_apply=False, wrong_prior=False, noncanonical=False,
                 fenced=False, wrong_join=False, extra_field=False, restate_length=False):
        self.options = locals().copy()
        self.requests = []
        self.raw_targets = []

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        self.assert_dev(request)
        kind = request["kind"]
        finish = "stop"
        if kind == "restate":
            raw = "PRIVATE_RESTATEMENT_SENTINEL: I will follow the message."
            if self.options["restate_length"]:
                finish = "length"
        elif kind == "wake":
            numbers = "3 7 11" if self.options["invalid_apply"] and request["stage"] == "apply" else "3,7,11"
            raw = "PREDICT: F\nACT: TRY " + numbers
        else:
            matches = re.findall(r"^Observed fields: (.+)$", request["input_messages"][0]["content"], flags=re.M)
            facts = json.loads(matches[-1])
            predicted = facts["predicted"]
            if self.options["wrong_prior"] and request["stage"] == "apply" and request["tick"] == 1:
                predicted = None
            payload = {"try": facts["values"], "observed": facts["observed"], "predicted": predicted,
                       "relation": "unavailable" if predicted is None else "matched" if predicted == facts["observed"] else "mismatched"}
            if self.options["extra_field"]:
                payload["advice"] = core.CONTACTS["P"]
            raw = core.canonical(payload)
            if self.options["noncanonical"]:
                raw = "\r\n " + json.dumps(payload, ensure_ascii=False) + " \t\r\n"
            if self.options["fenced"]:
                raw = "```json\n" + raw + "\n```"
            self.raw_targets.append((request["stage"], raw))
        return dict(request_id="wrong" if self.options["wrong_join"] else request["request_id"],
                    state=request["state"], raw=raw, finish_reason=finish)

    @staticmethod
    def assert_dev(request):
        if request["split"] != "dev":
            raise AssertionError("Tests never execute reserved confirmation instances")


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dependencies = core.load_dependencies()

    def capture(self, arm="P", seed=0, **options):
        backend = Fixture(**options)
        capture = core.run_formation(f"perception_seed{seed}_{arm}", backend, dependencies=self.dependencies)
        return capture, backend

    def resign(self, capture):
        capture["capture_sha256"] = core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})

    def test_schedule_manifest_is_frozen_disjoint(self):
        self.assertEqual(core.digest(core.schedule()), core.SCHEDULE_SHA256)
        self.assertEqual(core.check_disjointness()["distinct_ids"], 36)
        with self.assertRaises(ValueError):
            core.check_disjointness([core.episode_ids("confirm", "held")[0]])
        changed = core.schedule()
        changed["dev"]["pre"][0] = "mutated"
        self.assertNotEqual(changed, core.schedule())

    def test_exact_author_contacts_and_no_parent_model_calls(self):
        self.assertEqual(core.CONTACTS["P"], "Keep the prediction you stated before acting separate from the observation returned afterward. Record that prior unchanged; do not replace it with the outcome or with null. Derive the relation by comparing those two values. If no prediction was stated, record null and unavailable.")
        self.assertEqual(core.CONTACTS["N"], "This part of the session is complete. Continue with the next scheduled exercises using the task instructions. You may briefly acknowledge this message before proceeding.")
        capture, backend = self.capture()
        self.assertEqual(len(backend.requests), 42)
        self.assertEqual(capture["summary"]["parent_model_calls"], 0)
        self.assertEqual([request["kind"] for request in backend.requests].count("restate"), 2)
        self.assertEqual([entry["contact"]["raw"] for entry in capture["contacts"]], [core.CONTACTS["P"]] * 2)
        self.assertEqual(len(capture["episodes"]), 10)
        self.assertEqual(capture["summary"]["stages"]["apply"]["possible_records"], 16)

    def test_all_seeds_and_arms_same_schedule_different_contact_bytes(self):
        captures = [self.capture(arm=arm, seed=seed)[0] for seed in range(3) for arm in core.ARMS]
        report = core.compare_states(captures, dependencies=self.dependencies)
        self.assertEqual(report["missing_states"], [])
        self.assertTrue(all(pair["available"] for pair in report["paired_by_seed"].values()))
        self.assertNotEqual(captures[0]["summary"]["input_utf8_bytes"], captures[1]["summary"]["input_utf8_bytes"])

    def test_pre_reset_and_apply_contact_exactly_scoped(self):
        capture, backend = self.capture()
        for request in backend.requests:
            prompt = request["input_messages"][0]["content"]
            if request["kind"] == "wake":
                self.assertEqual(prompt.count(core.EXAMPLE_BLOCK), 1)
            if request["stage"] == "pre":
                self.assertNotIn(core.CONTACTS["P"], prompt)
                self.assertNotIn("PRIVATE_RESTATEMENT_SENTINEL", prompt)
            elif request["stage"] == "apply":
                self.assertIn(core.CONTACTS["P"], prompt)
                self.assertIn("PRIVATE_RESTATEMENT_SENTINEL", prompt)
                self.assertIsNotNone(request["contact_sha256"])
        self.assertEqual(core.audit_capture(capture, dependencies=self.dependencies)["calls_replayed"], 42)

    def test_eligibility_status_never_exposed_in_history(self):
        capture, backend = self.capture(wrong_prior=True)
        self.assertTrue(any(turn["status"] == "RECORD_REJECTED" for episode in capture["episodes"] for turn in episode["turns"]))
        for request in backend.requests:
            text = request["input_messages"][0]["content"]
            for private in ("RECORD_REJECTED", "PRODUCTION_RECORD", "production_eligible", "field_correct", '"status":'):
                self.assertNotIn(private, text)

    def test_variable_admission_uses_only_apply_not_pre(self):
        capture, unused = self.capture(wrong_prior=True)
        dataset = core.project_capture(capture, dependencies=self.dependencies)
        self.assertEqual(dataset["counts"]["admitted_rows"], 8)
        self.assertEqual(dataset["counts"]["refused_slots"], 8)
        self.assertTrue(all(row["source"]["tick"] == 2 and "/apply/" in row["source"]["task_id"] for row in dataset["rows"]))
        self.assertEqual([row["source"]["task_id"] for row in dataset["rows"]], sum(core.schedule()["dev"]["apply"], []))

    def test_exact_raw_bytes_and_no_contact_or_facts_in_sleep_cues(self):
        capture, backend = self.capture(noncanonical=True)
        dataset = core.project_capture(capture, dependencies=self.dependencies)
        self.assertEqual(dataset["counts"]["admitted_rows"], 16)
        self.assertEqual([row["raw_target"] for row in dataset["rows"]], [raw for stage, raw in backend.raw_targets if stage == "apply"])
        serialized = core.canonical(dataset)
        self.assertNotIn(core.CONTACTS["P"], serialized)
        self.assertNotIn("PRIVATE_RESTATEMENT_SENTINEL", serialized)
        for row in dataset["rows"]:
            self.assertEqual(hashlib.sha256(row["raw_target"].encode()).hexdigest(), row["target_sha256"])
            self.assertIn(row["source"]["public_execution_id"], row["input_messages"][0]["content"])
            self.assertNotIn("[3, 7, 11]", row["input_messages"][0]["content"])
            self.assertNotIn("Observed fields:", row["input_messages"][0]["content"])
        self.assertLess(dataset["counts"]["distinct_triples"], 16)

    def test_zero_admitted_is_no_write_without_replacement(self):
        capture, backend = self.capture(invalid_apply=True)
        dataset = core.project_capture(capture, dependencies=self.dependencies)
        self.assertEqual(dataset["status"], "NO_WRITE")
        self.assertEqual(dataset["counts"]["refused_slots"], 16)
        self.assertEqual(len(backend.requests), 26)
        self.assertEqual(capture["summary"]["stages"]["pre"]["record_calls"], 4)
        self.assertIsNone(capture["summary"]["stages"]["apply"]["production_eligible_over_records"])

    def test_fenced_or_extra_field_records_not_admitted(self):
        for options in (dict(fenced=True), dict(extra_field=True)):
            with self.subTest(options=options):
                capture, unused = self.capture(**options)
                self.assertEqual(core.project_capture(capture, dependencies=self.dependencies)["status"], "NO_WRITE")

    def test_parent_free_held_and_export_forbidden(self):
        for arm in (*core.ARMS, "INITIAL"):
            backend = Fixture()
            capture = core.run_held(f"perception_seed0_{arm}", backend, dependencies=self.dependencies)
            self.assertEqual(len(backend.requests), 32)
            self.assertEqual(capture["contacts"], [])
            for request in backend.requests:
                prompt = request["input_messages"][0]["content"]
                self.assertIsNone(request["contact_sha256"])
                for text in (*core.CONTACTS.values(), "PRIVATE_RESTATEMENT_SENTINEL", "/apply/", "/pre/"):
                    self.assertNotIn(text, prompt)
            with self.assertRaises(ValueError):
                core.project_capture(capture, dependencies=self.dependencies)

    def test_source_tamper_even_resigned_rejected(self):
        capture, unused = self.capture()
        capture["episodes"][1]["turns"][0]["execution"]["observed"] = "forged"
        self.resign(capture)
        with self.assertRaises(ValueError):
            core.project_capture(capture, dependencies=self.dependencies)

    def test_contract_contact_and_bool_count_tamper_rejected(self):
        original, unused = self.capture()
        for field in ("contact", "count", "order"):
            capture = copy.deepcopy(original)
            if field == "contact":
                capture["contacts"][0]["contact"]["raw"] += " mutation"
            elif field == "count":
                capture["summary"]["parent_model_calls"] = False
            else:
                capture["episodes"].reverse()
            self.resign(capture)
            with self.subTest(field=field), self.assertRaises(ValueError):
                core.audit_capture(capture, dependencies=self.dependencies)

    def test_wrong_source_response_refused_and_bounded(self):
        capture, backend = self.capture(wrong_join=True)
        self.assertEqual(len(backend.requests), 22)
        self.assertEqual(core.project_capture(capture, dependencies=self.dependencies)["status"], "NO_WRITE")

    def test_length_restatement_not_retried_or_success_selected(self):
        capture, backend = self.capture(restate_length=True)
        self.assertEqual(len(backend.requests), 42)
        self.assertEqual(capture["contacts"][0]["restatement"]["response"]["finish_reason"], "length")
        self.assertEqual(core.project_capture(capture, dependencies=self.dependencies)["counts"]["admitted_rows"], 16)

    def test_protocol_bound_and_corruption_rejected(self):
        manifest = core.build_manifest(self.dependencies)
        self.assertEqual(manifest["contract"]["protocol_document"]["sha256"], core.PROTOCOL_SHA256)
        self.assertEqual(manifest["contract"]["campaign_limits"]["calls_per_seed"], 300)
        self.assertEqual(manifest["contract"]["campaign_limits"]["native_seconds_per_seed"], 7200)
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "protocol.md"
            bad.write_text("wrong protocol")
            with self.assertRaises(ValueError):
                core.load_dependencies(protocol_path=bad)

    def test_invalid_dimensions_duplicate_states_and_bad_binding(self):
        for state, phase, split in (("perception_seed3_P", "formation", "dev"),
                                    ("perception_seed0_INITIAL", "formation", "dev"),
                                    ("perception_seed0_P", "bad", "dev"),
                                    ("perception_seed0_P", "formation", True)):
            with self.assertRaises(ValueError):
                core.run_state(state, Fixture(), phase=phase, split=split, dependencies=self.dependencies)
        with self.assertRaises(ValueError):
            core.run_formation("perception_seed0_P", Fixture(), dependencies=self.dependencies, binding={"bad": float("nan")})
        capture, unused = self.capture()
        with self.assertRaises(ValueError):
            core.compare_states([capture, capture], dependencies=self.dependencies)

    def test_frozen_module_globals_unchanged(self):
        before = (core.canonical(core._V2.MAX_OUTPUT_TOKENS), core._V2.WAKE_TEMPLATE,
                  core.canonical(core._MEMORY.CUE_TEMPLATES), core._MEMORY.CORE_SHA256)
        capture, unused = self.capture()
        core.project_capture(capture, dependencies=self.dependencies)
        after = (core.canonical(core._V2.MAX_OUTPUT_TOKENS), core._V2.WAKE_TEMPLATE,
                 core.canonical(core._MEMORY.CUE_TEMPLATES), core._MEMORY.CORE_SHA256)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
