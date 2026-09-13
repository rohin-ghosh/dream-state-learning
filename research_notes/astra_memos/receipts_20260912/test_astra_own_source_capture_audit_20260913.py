"""Local synthetic and archived-fixture negative tests for independent audit."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import unittest

SPEC = importlib.util.spec_from_file_location("independent", "/tmp/astra_own_source_capture_audit_20260913.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def event(prior="F", outcome="True"):
    return {"event_id": "e1", "raw_response": ("" if prior is None else f"PREDICT: {prior}\n") + "ACT: TRY 1,2,3",
            "raw_outcome": None if outcome is None else f"the box says: {outcome} for (1,2,3)"}


class ParserTests(unittest.TestCase):
    def test_all_six_diagnoses(self):
        fixtures = [(event("T"), "agreement"), (event(), "contradicted_prediction"),
                    (event(None), "absent_prediction"), (event(outcome=None), "missing_outcome")]
        foreign = event()
        foreign["raw_outcome"] = "the box says: True for (1,2,4)"
        ambiguous = event()
        ambiguous["raw_response"] = "PREDICT: T\n" + ambiguous["raw_response"]
        fixtures += [(foreign, "outcome_action_mismatch"), (ambiguous, "ambiguous_prediction")]
        for supplied, diagnosis in fixtures:
            with self.subTest(diagnosis=diagnosis):
                self.assertEqual(AUDIT.event_fields(supplied)[1], diagnosis)

    def test_pre_action_prior_not_outcome(self):
        expected, _ = AUDIT.event_fields(event())
        self.assertIs(expected["predicted"], False)
        self.assertIs(expected["observed"], True)
        self.assertEqual(expected["relation"], "mismatched")

    def test_absent_prior_is_not_inferred(self):
        expected, _ = AUDIT.event_fields(event(None))
        self.assertIsNone(expected["predicted"])
        self.assertEqual(expected["relation"], "unavailable")

    def test_post_action_prior_rejected(self):
        supplied = event(None)
        supplied["raw_response"] += "\nPREDICT: T"
        with self.assertRaises(ValueError):
            AUDIT.event_fields(supplied)

    def test_wrong_record_fields_rejected(self):
        expected, _ = AUDIT.event_fields(event())
        for field, value in (("try", [4, 5, 6]), ("observed", False), ("predicted", True), ("relation", "matched")):
            with self.subTest(field=field):
                supplied = dict(expected, **{field: value})
                result = AUDIT.judge_raw(json.dumps(supplied), "stop", expected)
                self.assertEqual(result["errors"], [field])

    def test_malformed_duplicate_extra_and_boolean_integer(self):
        expected, _ = AUDIT.event_fields(event())
        valid = json.dumps(expected)
        malformed = [valid + " trailing", valid[:-1] + ',"observed":true}',
                     json.dumps(dict(expected, extra=1)), json.dumps(dict(expected, observed=1)),
                     json.dumps(dict(expected, predicted=0)), json.dumps(dict(expected, **{"try": [True, 2, 3]})),
                     valid.replace("true", "NaN"), "[]"]
        for raw in malformed:
            with self.subTest(raw=raw):
                self.assertFalse(AUDIT.judge_raw(raw, "stop", expected)["passed"])

    def test_valid_spacing_is_not_rewritten(self):
        expected, _ = AUDIT.event_fields(event())
        raw = json.dumps(expected, indent=2)
        result = AUDIT.judge_raw(raw, "stop", expected)
        self.assertTrue(result["passed"])
        self.assertFalse(result["compact_sorted_bytes"])
        self.assertFalse(AUDIT.judge_raw(raw, "length", expected)["passed"])

    def test_source_hash_and_designated_last(self):
        first = dict(event("T", "False"), event_id="e0")
        source = {"events": [first, event()], "selected_event_id": "e1"}
        source["source_id"] = AUDIT.source_hash(source)
        self.assertEqual(AUDIT.source_fields(source)[1], "contradicted_prediction")
        source["selected_event_id"] = "e0"
        with self.assertRaisesRegex(ValueError, "hash"):
            AUDIT.source_fields(source)
        source["source_id"] = AUDIT.source_hash(source)
        with self.assertRaisesRegex(ValueError, "not last"):
            AUDIT.source_fields(source)

    def test_unsafe_tar_names_links_duplicates(self):
        for name, kind, duplicate in (("../escape", tarfile.REGTYPE, False), ("/absolute", tarfile.REGTYPE, False),
                                      ("link", tarfile.SYMTYPE, False), ("file", tarfile.REGTYPE, True)):
            with self.subTest(name=name):
                buffer = io.BytesIO()
                with tarfile.open(fileobj=buffer, mode="w") as archive:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    archive.addfile(member)
                    if duplicate:
                        archive.addfile(member)
                buffer.seek(0)
                with tarfile.open(fileobj=buffer, mode="r:") as archive:
                    with self.assertRaises(ValueError):
                        AUDIT.safe_members(archive)


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capsule = AUDIT.Capsule(AUDIT.REPO / "gpu_artifacts_local" / AUDIT.ROOT / "evidence.tar", AUDIT.ARCHIVE_SHA)
        cls.prefix = AUDIT.ROOT + "/"
        cls.bundle = cls.capsule.read(cls.prefix + "bundle_seed0.json")
        cls.original = AUDIT.original_material(AUDIT.REPO / "gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar", cls.bundle, 0)

    def test_original_selection(self):
        self.assertEqual(len(AUDIT.verify_selection(self.bundle, self.original)), 24)

    def test_selection_tamper_and_dropped_row(self):
        altered = copy.deepcopy(self.bundle)
        altered["training_observations"][0]["selected"] = not altered["training_observations"][0]["selected"]
        with self.assertRaises(ValueError):
            AUDIT.verify_selection(altered, self.original)
        altered = copy.deepcopy(self.bundle)
        altered["training_observations"].pop()
        with self.assertRaises(ValueError):
            AUDIT.verify_selection(altered, self.original)

    def test_raw_response_route_prompt_tokens_and_text(self):
        call = self.capsule.read(self.prefix + "calls_seed0.json")[0]
        stage = self.prefix + "run/seed0/train_00."
        request, response = self.capsule.read(stage + "request.json"), self.capsule.read(stage + "response.json")
        route, params = request["lora_request"], request["params"]
        AUDIT.verify_response(call, request, response, route, params)
        for key, value in (("lora_request", dict(route, id=2)), ("rendered_prompt", "wrong"),
                           ("actual_prompt_token_ids", [123]), ("text", "changed")):
            with self.subTest(key=key):
                altered = dict(response, **{key: value})
                with self.assertRaises(ValueError):
                    AUDIT.verify_response(call, request, altered, route, params)
        with self.assertRaises(ValueError):
            AUDIT.verify_response(call, dict(request, messages=[]), response, route, params)

    def test_release_identity_and_order(self):
        stage = self.prefix + "run/seed0/"
        launch, started, released = [self.capsule.read(stage + name + ".json") for name in ("launch", "started", "released")]
        plan_sha = self.capsule.hashes[self.prefix + "plan.json"]
        AUDIT.verify_process(launch, started, released, 0, plan_sha, None)
        for key in ("pid", "pgid", "start_ticks"):
            altered = copy.deepcopy(released)
            altered["identity"][key] += 1
            with self.assertRaises(ValueError):
                AUDIT.verify_process(launch, started, altered, 0, plan_sha, None)
        with self.assertRaises(ValueError):
            AUDIT.verify_process(launch, started, released, 0, plan_sha, released["ended"] + 1)

    def test_full_local_audit(self):
        result = AUDIT.audit(AUDIT.REPO / "gpu_artifacts_local" / AUDIT.ROOT / "evidence.tar",
                             AUDIT.REPO / "gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar",
                             Path("/tmp") / (AUDIT.ROOT + "_collected"))
        self.assertEqual(result["costs"]["calls"], 72)
        self.assertEqual(result["unique_sources_across_seeds"], 24)
        self.assertEqual(result["unique_raw_targets_across_seeds"], 24)
        self.assertEqual(set(result["raw_target_multiplicities_across_seeds"].values()), {3})
        for seed in result["seeds"]:
            self.assertEqual(seed["unique_selected_triples"], 24)
            self.assertEqual(seed["earlier_outcome_differs"], 12)
            self.assertEqual(set(seed["non_triple_field_patterns"].values()), {4})


if __name__ == "__main__":
    unittest.main()
