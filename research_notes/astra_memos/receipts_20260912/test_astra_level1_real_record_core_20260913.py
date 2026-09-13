"""Scripted CPU responses only: these are not real-model formation results."""
import copy
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import astra_level1_real_record_core_20260913 as core


class ScriptedBackend:
    def __init__(self, wake_mutator=None, record_mutator=None, offset=0):
        self.requests = []
        self.wake_mutator = wake_mutator
        self.record_mutator = record_mutator
        self.offset = offset

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        response = {"request_id": request["request_id"], "state": request["state"], "finish_reason": "stop"}
        if request["kind"] == "wake":
            tick = request["tick"]
            response["raw"] = ("PREDICT: F\n" if tick == 1 else "") + f"ACT: TRY {tick + self.offset},{tick + 3},-2"
            if self.wake_mutator:
                self.wake_mutator(request, response)
        else:
            prompt = request["input_messages"][0]["content"]
            facts = json.loads(re.findall(r"^Observed fields: (.*)$", prompt, re.MULTILINE)[-1])
            predicted, observed = facts["predicted"], facts["observed"]
            relation = "unavailable" if predicted is None else "matched" if predicted == observed else "mismatched"
            response["raw"] = core.canonical({"try": facts["values"], "observed": observed,
                                                "predicted": predicted, "relation": relation})
            if self.record_mutator:
                self.record_mutator(request, response)
        return response


class RealRecordCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dependencies = core.load_dependencies()

    def run_capture(self, backend=None, state="OFF"):
        return core.run_state(state, backend or ScriptedBackend(), dependencies=self.dependencies)

    def test_actual_game_execution_fixed_budget_and_pinned_prompts(self):
        evaluations = []
        base_class = self.dependencies.game_class
        class CountingGame(base_class):
            def evaluate(self, episode, action):
                evaluations.append((episode.eid, action))
                return super().evaluate(episode, action)
            def quiz_triples(self, *args, **kwargs):
                raise AssertionError("quiz must never be used")
        dependencies = SimpleNamespace(game_class=CountingGame, interface=self.dependencies.interface,
                                       manifest=self.dependencies.manifest)
        backend = ScriptedBackend()
        capture = core.run_state("OFF", backend, dependencies=dependencies)
        self.assertEqual(len(evaluations), 16)
        self.assertEqual(len(backend.requests), 32)
        self.assertEqual(core.MAX_OUTPUT_TOKENS, {"wake": 96, "record": 192})
        self.assertTrue(all(request["max_output_tokens"] == (96 if request["kind"] == "wake" else 192) for request in backend.requests))
        self.assertEqual(capture["summary"]["production_eligible"], 16)
        self.assertEqual(capture["summary"]["possible_records"], 16)
        self.assertEqual(capture["summary"]["missing_records"], 0)
        self.assertFalse(capture["native_identity_verified"])
        self.assertEqual(len(set(core.episode_ids())), 8)
        for episode in capture["episodes"]:
            first, second = episode["turns"]
            self.assertLess(first["record"]["sequence"], second["wake"]["sequence"])
            for turn in (first, second):
                execution, wake, record = turn["execution"], turn["wake"], turn["record"]
                self.assertEqual(execution["source_call_sha256"], wake["sha256"])
                self.assertEqual(execution["source_call_id"], wake["request"]["request_id"])
                self.assertEqual(record["request"]["source_execution_sha256"], execution["sha256"])
                self.assertEqual(execution["raw_wake"], wake["response"]["raw"])
                unused, outcome = base_class().evaluate(SimpleNamespace(eid=episode["episode_id"]), execution["action"])
                self.assertEqual(execution["outcome"], outcome)
                expected = self.dependencies.interface.record_prompt(execution, wake["response"]["raw"], core.PROTOCOL)
                if turn["tick"] == 2:
                    expected = core.earlier_transcript(first) + "\n" + expected
                self.assertEqual(record["request"]["input_messages"], [{"role": "user", "content": expected}])
                self.assertNotIn("reward", execution)
                self.assertNotIn("raw_target", turn)
            self.assertIn(first["execution"]["outcome"], second["record"]["request"]["input_messages"][0]["content"])
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_wrong_outcome_source_and_earlier_record_distractor(self):
        first_raw = {}
        def mutate(request, response):
            if request["tick"] == 1:
                first_raw[request["episode_id"]] = response["raw"]
                record = json.loads(response["raw"])
                record["observed"] = not record["observed"]
                response["raw"] = core.canonical(record)
            else:
                response["raw"] = first_raw[request["episode_id"]]
        capture = self.run_capture(ScriptedBackend(record_mutator=mutate))
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        self.assertEqual(capture["summary"]["content_correct"], 0)
        self.assertEqual(capture["summary"]["actual_record_calls"], 16)
        for episode in capture["episodes"]:
            self.assertFalse(episode["turns"][0]["score"]["field_correct"]["observed"])
            self.assertFalse(episode["turns"][1]["score"]["field_correct"]["try"])
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])

    def test_ambiguous_prior_executes_but_does_not_admit(self):
        def ambiguous(request, response):
            response["raw"] = "PREDICT: T\nPREDICT: F\nACT: TRY 3,4,5"
        capture = self.run_capture(ScriptedBackend(wake_mutator=ambiguous))
        self.assertEqual(capture["summary"]["world_executions"], 16)
        self.assertEqual(capture["summary"]["actual_record_calls"], 16)
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        for episode in capture["episodes"]:
            for turn in episode["turns"]:
                self.assertIn("ambiguous source prediction", turn["score"]["production_errors"])
                self.assertFalse(turn["score"]["field_correct"]["predicted"])

    def test_invalid_wake_no_world_no_record_and_no_retry(self):
        invalid = ("ACT: QUIZ ?", "DONE", "ACT: TRY 1,2", "TRY 1,2,3", "ACT: TRY 1,2,3\nACT: TRY 4,5,6", "[OUTCOME] True\nACT: TRY 1,2,3")
        for text in invalid:
            def mutate(request, response):
                if request["tick"] == 1:
                    response["raw"] = text
            backend = ScriptedBackend(wake_mutator=mutate)
            capture = self.run_capture(backend)
            self.assertEqual(len(backend.requests), 24, text)
            self.assertEqual(capture["summary"]["world_executions"], 8, text)
            self.assertEqual(capture["summary"]["missing_records"], 8)
            self.assertEqual(capture["summary"]["production_eligible_rate_over16"], .5)
            for episode in capture["episodes"]:
                self.assertIsNone(episode["turns"][0]["record"])
                self.assertIn('"outcome_raw":null', episode["turns"][1]["wake"]["request"]["input_messages"][0]["content"])

    def test_length_wake_skips_world_length_record_fails_both(self):
        def unfinished(request, response):
            if request["tick"] == 1:
                response["finish_reason"] = "length"
        capture = self.run_capture(ScriptedBackend(wake_mutator=unfinished, record_mutator=unfinished))
        self.assertEqual(capture["summary"]["world_executions"], 8)
        self.assertEqual(capture["summary"]["production_eligible"], 8)
        capture = self.run_capture(ScriptedBackend(record_mutator=unfinished))
        self.assertEqual(capture["summary"]["world_executions"], 16)
        self.assertEqual(capture["summary"]["unfinished_records"], 8)
        self.assertEqual(capture["summary"]["content_correct"], 8)
        for episode in capture["episodes"]:
            score = episode["turns"][0]["score"]
            self.assertFalse(score["production_eligible"])
            self.assertFalse(score["content_correct"])
            self.assertFalse(score["strict_canonical"])
            self.assertTrue(all(score["parsed_field_correct"].values()))
            self.assertFalse(any(score["field_correct"].values()))

    def test_production_grammar_not_changed_by_content_fences(self):
        def fence(request, response):
            response["raw"] = "```json\n" + response["raw"] + "\n```"
        capture = self.run_capture(ScriptedBackend(record_mutator=fence))
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        self.assertEqual(capture["summary"]["content_correct"], 16)
        for episode in capture["episodes"]:
            for turn in episode["turns"]:
                self.assertEqual(turn["score"]["raw"], turn["record"]["response"]["raw"])
                self.assertEqual(turn["score"]["format"], "fenced")
        turn = self.run_capture()["episodes"][0]["turns"][0]
        raw = turn["record"]["response"]["raw"]
        for bad in (raw + " explanation", "{}", raw[:-1], "```json\n" + raw + "\n```\nprose"):
            score = core.score_record(bad, "stop", turn["execution"], self.dependencies)
            self.assertFalse(score["content_correct"])
        parsed = json.loads(raw)
        parsed["observed"] = int(parsed["observed"])
        self.assertFalse(core.score_record(core.canonical(parsed), "stop", turn["execution"], self.dependencies)["content_correct"])
        spaced = json.dumps(dict(reversed(list(json.loads(raw).items()))), indent=2)
        score = core.score_record(spaced, "stop", turn["execution"], self.dependencies)
        self.assertTrue(score["production_eligible"])
        self.assertTrue(score["content_correct"])
        self.assertFalse(score["strict_canonical"])

    def test_response_joins_and_replay_detect_tampering(self):
        def wrong_join(request, response):
            response["request_id"] = "wrong-call"
        capture = self.run_capture(ScriptedBackend(wake_mutator=wrong_join))
        self.assertEqual(capture["summary"]["world_executions"], 0)
        self.assertEqual(capture["summary"]["missing_records"], 16)
        capture = self.run_capture(ScriptedBackend(record_mutator=wrong_join))
        self.assertEqual(capture["summary"]["world_executions"], 16)
        self.assertEqual(capture["summary"]["content_correct"], 0)
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])
        for field in ("outcome", "source_call_sha256"):
            capture = self.run_capture()
            altered = copy.deepcopy(capture)
            execution = altered["episodes"][0]["turns"][0]["execution"]
            execution[field] = "wrong-source-or-outcome"
            altered["capture_sha256"] = core.digest({key: value for key, value in altered.items() if key != "capture_sha256"})
            with self.assertRaises(ValueError):
                core.audit_capture(altered, dependencies=self.dependencies)
        capture = self.run_capture()
        altered = copy.deepcopy(capture)
        altered["episodes"][0]["turns"][1]["record"]["request"]["source_execution_sha256"] = "0" * 64
        altered["capture_sha256"] = core.digest({key: value for key, value in altered.items() if key != "capture_sha256"})
        with self.assertRaises(ValueError):
            core.audit_capture(altered, dependencies=self.dependencies)

    def test_states_share_episodes_budgets_not_actions(self):
        captures = [self.run_capture(ScriptedBackend(offset=index * 10), state=state) for index, state in enumerate(core.STATES)]
        report = core.compare_states(captures, dependencies=self.dependencies)
        self.assertEqual(report["missing_states"], [])
        self.assertEqual(report["possible_records_per_state"], 16)
        self.assertIn("not_identical_experience", report["comparison"])
        for capture in captures:
            self.assertEqual(capture["contract"], captures[0]["contract"])
        self.assertNotEqual(captures[0]["episodes"][0]["turns"][0]["execution"]["values"], captures[1]["episodes"][0]["turns"][0]["execution"]["values"])
        partial = core.compare_states(captures[:1], dependencies=self.dependencies)
        self.assertEqual(len(partial["missing_states"]), 3)
        with self.assertRaises(ValueError):
            core.compare_states([captures[0], captures[0]], dependencies=self.dependencies)

    def test_pins_fail_closed_and_scripted_runs_reproduce(self):
        original = Path.read_bytes
        def changed(path):
            value = original(path)
            return value + b"\n" if path.name == "rulegame.py" else value
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "source pin mismatch"):
                core.load_dependencies()
        self.assertEqual(self.run_capture(), self.run_capture())
        def failed_backend(request):
            raise RuntimeError("scripted backend failure")
        capture = self.run_capture(failed_backend)
        self.assertEqual(capture["summary"]["actual_wake_calls"], 16)
        self.assertEqual(capture["summary"]["missing_records"], 16)
        self.assertTrue(core.audit_capture(capture, dependencies=self.dependencies)["consistent"])


if __name__ == "__main__":
    unittest.main()
