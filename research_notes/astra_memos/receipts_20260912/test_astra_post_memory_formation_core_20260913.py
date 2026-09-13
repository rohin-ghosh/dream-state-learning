"""Pure CPU scripted interactions; no model output or native prerequisite claims."""
import copy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import astra_post_memory_formation_core_20260913 as core


class Backend:
    def __init__(self, wake=None, record=None, offset=0):
        self.wake, self.record, self.offset = wake, record, offset
        self.requests = []

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        response = dict(request_id=request["request_id"], state=request["state"], finish_reason="stop")
        if request["kind"] == "wake":
            tick = request["tick"]
            response["raw"] = ("PREDICT: F\n" if tick == 1 else "") + f"ACT: TRY {tick + self.offset},{tick + 3},-2"
            if self.wake:
                self.wake(request, response)
        else:
            fields = json.loads(re.findall(r"^Observed fields: (.*)$", request["input_messages"][0]["content"], re.MULTILINE)[-1])
            relation = "unavailable" if fields["predicted"] is None else "matched" if fields["predicted"] == fields["observed"] else "mismatched"
            response["raw"] = core.canonical({"try": fields["values"], "observed": fields["observed"], "predicted": fields["predicted"], "relation": relation})
            if self.record:
                self.record(request, response)
        return response


class PostMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dependencies = core.load_dependencies()

    def capture(self, backend=None, state=core.STATES[0], dependencies=None, binding=None):
        return core.run_state(state, backend or Backend(), dependencies=dependencies or self.dependencies, binding=binding)

    def test_exact_independent_id_derivation_and_disjointness(self):
        expected = tuple("next-record-dev-" + hashlib.sha256(json.dumps(["astra-next-l2-20260913", index], separators=(",", ":")).encode()).hexdigest()[:20] for index in range(8))
        self.assertEqual(core.episode_ids(), expected)
        self.assertEqual(expected[0], "next-record-dev-627e2b39856014cb44d1")
        self.assertEqual(expected[-1], "next-record-dev-b6766a9df5e9088443a9")
        self.assertEqual(core.digest(list(expected)), "c45edf52b71d84e547264251abcb34305199f30e8dd3af1e41caa7346c4dca6e")
        self.assertFalse(set(expected) & set(core._V2.episode_ids()))
        self.assertTrue(core.check_disjointness(list(core._V2.episode_ids()) * 2)["disjoint"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            core.check_disjointness([expected[1]])

    def test_only_example_block_removed_and_strata_fixed(self):
        present, absent = (core.WAKE_TEMPLATES[name] for name in ("example_present", "example_absent"))
        self.assertEqual(present, core._V2.WAKE_TEMPLATE)
        self.assertEqual(absent, present.replace(core.EXAMPLE_BLOCK, "", 1))
        self.assertEqual(core.sha_text(present), "090f99d55be7c96affbf73804f39a0a457936d1546c71bae95d4185684013ebd")
        self.assertEqual(core.sha_text(absent), "a7458bef4b2572bd6dafac42e724b0a2f122c3568937fa9a1e7a64cb88920cfa")
        self.assertIn("three integers", absent)
        self.assertIn("Output only two lines", absent)
        backend = Backend()
        capture = self.capture(backend)
        for episode in capture["episodes"]:
            expected = "example_present" if episode["index"] % 2 == 0 else "example_absent"
            self.assertEqual(episode["cue_stratum"], expected)
            for turn in episode["turns"]:
                request = turn["wake"]["request"]
                history = core.earlier_transcript(episode["turns"][0] if turn["tick"] == 2 else None)
                self.assertEqual(request["input_messages"], [{"role": "user", "content": core.WAKE_TEMPLATES[expected].format(
                    eid=episode["episode_id"], tick=turn["tick"], earlier_transcript=history)}])
                self.assertEqual(request["cue_stratum"], expected)
        self.assertEqual([capture["summary"]["strata"]["cue"][name]["possible_records"] for name in core.WAKE_TEMPLATES], [8, 8])

    def test_v2_globals_unchanged_and_semantics_reused(self):
        previous = (core._V2.STATES, core._V2.episode_ids(), core._V2.SCHEMA, core._V2.WAKE_TEMPLATE)
        self.capture()
        self.assertEqual(previous, (core._V2.STATES, core._V2.episode_ids(), core._V2.SCHEMA, core._V2.WAKE_TEMPLATE))
        self.assertEqual(core._V2.STATES, ("OFF", "perception_seed0", "perception_seed1", "perception_seed2"))
        self.assertIs(core.score_record, core._V2.score_record)
        self.assertIs(core.earlier_transcript, core._V2.earlier_transcript)
        self.assertEqual(core.PROTOCOL, "interaction_v3")

    def test_actual_world_and_source_joins_no_quiz(self):
        evaluations = []
        game_class = self.dependencies.game_class
        class CountGame(game_class):
            def evaluate(self, episode, action):
                evaluations.append((episode.eid, action))
                return super().evaluate(episode, action)
            def quiz_triples(self, *args, **kwargs):
                raise AssertionError("quiz forbidden")
        dependencies = SimpleNamespace(game_class=CountGame, interface=self.dependencies.interface, manifest=self.dependencies.manifest)
        backend = Backend()
        capture = self.capture(backend, dependencies=dependencies)
        self.assertEqual(len(evaluations), 16)
        self.assertEqual(len(backend.requests), 32)
        self.assertEqual(capture["summary"]["production_eligible"], 16)
        for episode in capture["episodes"]:
            for turn in episode["turns"]:
                execution = turn["execution"]
                self.assertEqual(execution["source_call_sha256"], turn["wake"]["sha256"])
                self.assertEqual(execution["source_call_id"], turn["wake"]["request"]["request_id"])
                self.assertEqual(turn["record"]["request"]["source_execution_sha256"], execution["sha256"])
                self.assertEqual(execution["execution_id"], f"{capture['state']}:{episode['episode_id']}#t{turn['tick']}")
                unused, outcome = game_class().evaluate(SimpleNamespace(eid=episode["episode_id"]), execution["action"])
                self.assertEqual(execution["outcome"], outcome)
                self.assertEqual(execution["outcome_utf8_sha256"], core.sha_text(outcome))
                self.assertNotIn("reward", execution)
                expected = self.dependencies.interface.record_prompt(execution, turn["wake"]["response"]["raw"], core.PROTOCOL)
                if turn["tick"] == 2:
                    expected = core.earlier_transcript(episode["turns"][0]) + "\n" + expected
                self.assertEqual(turn["record"]["request"]["input_messages"], [{"role": "user", "content": expected}])
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_raw_fences_errors_and_history_preserved_without_repair(self):
        def mutate(request, response):
            response["raw"] = "```json\n" + response["raw"] + "\n```"
        capture = self.capture(Backend(record=mutate))
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        self.assertEqual(capture["summary"]["content_correct"], 16)
        for episode in capture["episodes"]:
            first, second = episode["turns"]
            self.assertEqual(first["score"]["raw"], first["record"]["response"]["raw"])
            self.assertEqual(first["score"]["format"], "fenced")
            history = core.earlier_transcript(first)
            self.assertIn(history, second["wake"]["request"]["input_messages"][0]["content"])
            self.assertTrue(second["record"]["request"]["input_messages"][0]["content"].startswith(history + "\n"))
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_invalid_unfinished_and_wrong_join_wakes_never_execute(self):
        mutations = [lambda request, response: response.update(raw="TRY 1,2,3"),
                     lambda request, response: response.update(raw="ACT: QUIZ ?"),
                     lambda request, response: response.update(finish_reason="length"),
                     lambda request, response: response.update(request_id="wrong"),
                     lambda request, response: response.update(state=core.STATES[1])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                backend = Backend(wake=mutate)
                capture = self.capture(backend)
                self.assertEqual(len(backend.requests), 16)
                self.assertEqual(capture["summary"]["world_executions"], 0)
                self.assertEqual(capture["summary"]["missing_records"], 16)
                self.assertEqual(capture["summary"]["production_eligible_rate_over16"], 0)
                self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_backend_failures_remain_replayable(self):
        def failed(request):
            raise RuntimeError("injected failure")
        capture = self.capture(failed)
        self.assertEqual(capture["summary"]["missing_records"], 16)
        self.assertIn("injected failure", capture["episodes"][0]["turns"][0]["wake"]["response"]["backend_error"])
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_wrong_observed_prior_and_record_completion_not_success(self):
        def wrong_observed(request, response):
            parsed = json.loads(response["raw"])
            parsed["observed"] = not parsed["observed"]
            response["raw"] = core.canonical(parsed)
        for mutate in (wrong_observed, lambda request, response: response.update(finish_reason="length"),
                       lambda request, response: response.update(request_id="old-execution")):
            capture = self.capture(Backend(record=mutate))
            self.assertEqual(capture["summary"]["world_executions"], 16)
            self.assertEqual(capture["summary"]["production_eligible"], 0)
            self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])
        def ambiguous(request, response):
            response["raw"] = "PREDICT: T\nPREDICT: F\nACT: TRY 3,4,5"
        capture = self.capture(Backend(wake=ambiguous))
        self.assertEqual(capture["summary"]["world_executions"], 16)
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        self.assertEqual(capture["summary"]["strata"]["prior"]["ambiguous"]["possible_records"], 16)

    def test_six_cells_caps_differing_actions_no_outcome_gate(self):
        captures = [self.capture(Backend(offset=index * 10), state=state, binding={"canary_harm": True, "recall_gain": -1})
                    for index, state in enumerate(core.STATES)]
        comparison = core.compare_states(captures, dependencies=self.dependencies)
        self.assertEqual(comparison["missing_states"], [])
        self.assertEqual(sum(capture["summary"]["actual_wake_calls"] + capture["summary"]["actual_record_calls"] for capture in captures), 192)
        self.assertEqual(core.contract(self.dependencies)["maximum_generated_tokens_all_states"], 27648)
        self.assertEqual(core.MAX_OUTPUT_TOKENS, {"wake": 96, "record": 192})
        self.assertEqual({capture["capture_sha256"] for capture in captures}.__len__(), 6)
        self.assertNotEqual(captures[0]["episodes"][0]["turns"][0]["execution"]["values"], captures[1]["episodes"][0]["turns"][0]["execution"]["values"])
        self.assertIsNone(comparison["outcome_gate"])
        self.assertFalse(comparison["engineering_prerequisite_verified"])
        self.assertTrue(all(not capture["native_identity_verified"] for capture in captures))
        partial = core.compare_states(captures[:1], dependencies=self.dependencies)
        self.assertEqual(len(partial["missing_states"]), 5)
        self.assertIsNone(partial["paired_by_seed"]["0"]["WRITE_minus_LR0"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            core.compare_states([captures[0], captures[0]], dependencies=self.dependencies)

    def test_strata_denominators_and_empty_are_not_passes(self):
        summary = self.capture()["summary"]
        for strata in summary["strata"].values():
            self.assertEqual(sum(cell["possible_records"] for cell in strata.values()), 16)
        empty = summary["strata"]["prior"]["ambiguous"]
        self.assertEqual(empty["coverage"], "untested")
        self.assertIsNone(empty["production_eligible_rate_over_possible"])
        self.assertEqual(summary["strata"]["prior"]["available"]["possible_records"], 8)
        self.assertEqual(summary["strata"]["prior"]["absent"]["possible_records"], 8)

    def test_rehashed_tamper_rejected_including_cues_and_order(self):
        capture = self.capture()
        mutations = [lambda data: data["episodes"][0]["turns"][0]["execution"].update(outcome="forged"),
                     lambda data: data["episodes"][0]["turns"][1]["record"]["request"].update(source_execution_sha256="wrong"),
                     lambda data: data["episodes"][1].update(cue_stratum="example_present"),
                     lambda data: data["episodes"].reverse(),
                     lambda data: data["events"][0]["request"].update(cue_stratum="example_absent")]
        for mutate in mutations:
            altered = copy.deepcopy(capture)
            mutate(altered)
            altered["capture_sha256"] = core.digest({key: value for key, value in altered.items() if key != "capture_sha256"})
            with self.assertRaises(ValueError):
                core.audit_capture(altered, dependencies=self.dependencies)

    def test_pins_and_deterministic_replay(self):
        self.assertEqual(self.capture(), self.capture())
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b"\n" if path.name in ("astra_level1_real_record_core_20260913_v2.py", "rulegame.py") else raw
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "pin mismatch"):
                core.load_dependencies()
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.capture(state="OFF")


if __name__ == "__main__":
    unittest.main()
