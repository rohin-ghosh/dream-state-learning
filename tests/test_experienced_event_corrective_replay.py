"""CPU-only captured public feedback and child-choice admission tests."""

import copy
import json
from pathlib import Path
import unittest

from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_corrective_replay as selector
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


ACTOR_HASH = "a" * 64


def fixture():
    bank = adult.build_bank(2)

    def generate(messages):
        fact = next(fact for fact in bank if fact["port"] in messages[1]["content"])
        raw = ("EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2
               else micro._event(fact))
        return dict(raw=raw, terminal=True, truncated=False, messages=copy.deepcopy(messages))

    collection = adult.collect(generate, cycle=2)
    records = []
    for fact in bank:
        commands = iter(["READ EVENT " + fact["public_events"][0],
                         "READ EVENT " + fact["public_events"][1],
                         "ROUTE " + fact["public_ports"][0]])

        def actor(messages):
            return dict(raw=next(commands), terminal=True, truncated=False,
                        messages=copy.deepcopy(messages))

        def reader(address):
            return dict(raw="MISS", terminal=True, truncated=False,
                        private_score="HIDDEN_READER_METADATA")

        transitions = {other["port"]: other["outcome"] for other in bank if other["node"] == fact["node"]}
        episode = controller.run_episode(controller.public_task(fact), actor, reader, transitions.__getitem__)
        records.append(dict(event=fact["event"], episode=episode))
    common = dict(state="BEFORE", cycle=2, development_arm="CUE_REPLAY", fits=0,
                  loaded_adapter_state_sha256=ACTOR_HASH, initial_training_result_sha256="b" * 64)
    collection_result = dict(common, phase="collect", status="COLLECTION_COMPLETE", collection_sha256="c" * 64)
    before_result = dict(common, phase="readout", status="COMPLETE", reader_wrapper=0,
                         adult_source=dict(collection_sha256="c" * 64),
                         panels=dict(OWN_PARAMETRIC=dict(denominator=4, episodes=copy.deepcopy(records))))
    return collection, records, dict(collection_result=collection_result, before_result=before_result,
                                    expected_actor_state_sha256=ACTOR_HASH)


class CorrectiveReplayTests(unittest.TestCase):
    def setUp(self):
        self.collection, self.records, self.bindings = fixture()
        self.plan = selector.prepare_cases(self.collection, self.records)

    def response(self, source_index=0, **changes):
        result = dict(raw=self.collection["episodes"][source_index]["event"]["raw"],
                      terminal=True, truncated=False)
        result.update(changes)
        return result

    def test_two_fresh_prompts_all_sources_and_actual_feedback(self):
        original = copy.deepcopy((self.collection, self.records))
        self.assertEqual(self.plan["expected_calls"], 2)
        self.assertEqual([case["route_index"] for case in self.plan["cases"]], [1, 2])
        for case in self.plan["cases"]:
            self.assertEqual([message["role"] for message in case["messages"]], ["system", "user"])
            payload = json.loads(case["messages"][1]["content"].split("\n", 1)[1])
            episode = self.records[case["route_index"]]["episode"]
            task = controller.public_task(self.collection["bank"][case["route_index"]])
            self.assertEqual(payload["public_task"], task)
            self.assertEqual(payload["public_route_transcript"], episode["messages"])
            self.assertEqual(payload["actual_transition_outcome"], dict(node=task["node"],
                             committed_port=episode["chosen_port"], observed_destination=episode["outcome"]))
            self.assertNotEqual(episode["outcome"], task["goal"])
            self.assertEqual(len(payload["own_public_event_records"]), 4)
            for index, entry in enumerate(payload["own_public_event_records"]):
                source = self.collection["episodes"][index]["event"]
                self.assertEqual(entry["event_record"], source["raw"])
                self.assertEqual(entry["public_receipt"], source["messages"][-1]["content"].split("\n")[0])
            for forbidden in ("reached_goal", "terminal_reason", "HIDDEN_READER_METADATA",
                              "private_score", "expected_answer", "token_ids", '"bank"', '"fact"'):
                self.assertNotIn(forbidden, case["messages"][1]["content"])
            for fact in self.collection["bank"]:
                self.assertNotIn(fact["world"], case["messages"][1]["content"])
        self.assertEqual((self.collection, self.records), original)

    def test_wrong_but_sourced_choice_admitted_duplicates_and_views_preserved(self):
        seen = []

        def generate(messages):
            seen.append(copy.deepcopy(messages))
            return self.response(messages=copy.deepcopy(messages))

        result = selector.collect_selection(self.plan, generate)
        self.assertEqual((result["model_calls"], result["fits"], result["admitted_selections"]), (2, 0, 2))
        self.assertEqual(result["chosen_source_indexes"], [0, 0])
        self.assertEqual(result["row_source_indexes"], list(range(0, 32, 4)) * 2)
        self.assertEqual(len(result["material_origins"]), 16)
        for origin, row_index in zip(result["material_origins"], result["row_source_indexes"]):
            source_row = self.collection["rows"][row_index]
            self.assertEqual(origin["source_index"], 0)
            self.assertEqual(origin["source_row_index"], row_index)
            self.assertEqual(origin["target_sha256"], source_row["target_sha256"])
            self.assertEqual(origin["source_raw_sha256"], source_row["source_raw_sha256"])
        self.assertEqual(seen, [case["messages"] for case in self.plan["cases"]])
        self.assertEqual(selector.replay_selection(result, self.collection, self.records),
                         result["material_origins"])
        self.assertNotEqual(self.collection["bank"][0]["outcome"], self.collection["bank"][1]["outcome"])
        self.assertNotEqual(self.collection["bank"][0]["node"], self.collection["bank"][2]["node"])

    def test_every_source_can_be_selected_without_goal_or_node_gate(self):
        for source_index in range(4):
            with self.subTest(source_index=source_index):
                result = selector.collect_selection(self.plan, lambda messages: self.response(source_index))
                self.assertEqual(result["chosen_source_indexes"], [source_index, source_index])

    def test_canonicalization_only_final_lfs_and_raw_retained(self):
        for final_lfs in (0, 1, 3):
            raw = self.response()["raw"].rstrip("\n") + "\n" * final_lfs
            result = selector.collect_selection(self.plan, lambda messages: self.response(raw=raw))
            self.assertEqual(result["admitted_selections"], 2)
            self.assertEqual(result["captures"][0]["response"]["raw"], raw)
            self.assertEqual(result["selections"][0]["canonical"], self.response()["raw"])

    def test_exact_identifiers_no_semantic_repair(self):
        for field in ("event", "node", "port", "outcome", "receipt"):
            source = self.collection["bank"][0]
            other = self.collection["bank"][2]
            raw = self.response()["raw"].replace(source[field], other[field])
            with self.subTest(field=field):
                result = selector.collect_selection(self.plan, lambda messages: self.response(raw=raw))
                self.assertEqual(result["admitted_selections"], 0)
                self.assertEqual(result["row_source_indexes"], [])
                self.assertEqual(result["captures"][0]["response"]["raw"], raw)

    def test_invalid_or_abstained_output_retained_without_replacement(self):
        raw_event = self.response()["raw"]
        for raw in ("NONE", "NONE\n", "MISS", " " + raw_event, raw_event + "NONE",
                    raw_event + raw_event, raw_event.replace(" AT ", "  AT "),
                    raw_event.replace("\n", "\r\n")):
            with self.subTest(raw=raw):
                result = selector.collect_selection(self.plan, lambda messages: self.response(raw=raw))
                self.assertEqual(result["model_calls"], 2)
                self.assertEqual(result["chosen_source_indexes"], [None, None])
                self.assertEqual(result["captures"][0]["response"]["raw"], raw)
                self.assertEqual(result["fits"], 0)
                self.assertEqual(result["selections"][0]["status"],
                                 "ABSTAINED" if raw in ("NONE", "NONE\n") else "REJECTED")

    def test_failed_call_is_not_replaced_and_next_case_stays_fixed(self):
        calls = []

        def generate(messages):
            calls.append(copy.deepcopy(messages))
            if len(calls) == 1:
                raise RuntimeError("captured failure")
            return self.response(3)

        result = selector.collect_selection(self.plan, generate)
        self.assertEqual(calls, [case["messages"] for case in self.plan["cases"]])
        self.assertEqual(result["chosen_source_indexes"], [None, 3])
        self.assertEqual(result["captures"][0]["error"], dict(type="RuntimeError", message="captured failure"))
        self.assertEqual(result["row_source_indexes"], list(range(3, 32, 4)))

    def test_nonterminal_malformed_and_non_json_responses_retained(self):
        responses = [None, "invalid", self.response(terminal=False), self.response(truncated=True),
                     self.response(terminal=1), self.response(messages=[]), self.response(extra={1, 2})]
        for response in responses:
            with self.subTest(response=response):
                result = selector.collect_selection(self.plan, lambda messages: response)
                self.assertEqual(result["chosen_source_indexes"], [None, None])
                self.assertEqual(result["model_calls"], 2)
                if type(response) is dict:
                    self.assertEqual(result["captures"][0]["response"]["raw"], response["raw"])

    def test_missing_feedback_and_source_drift_fail_before_selection(self):
        mutations = [lambda records: records.pop(),
                     lambda records: records.reverse(),
                     lambda records: records[1]["episode"]["traces"].pop(),
                     lambda records: records[1]["episode"].update(outcome=None),
                     lambda records: records[1]["episode"].update(reached_goal=True),
                     lambda records: records[1]["episode"]["traces"][-1].pop("outcome"),
                     lambda records: records[1]["episode"]["traces"][-1].update(committed=False),
                     lambda records: records[1]["episode"]["messages"][1].update(content="changed public task"),
                     lambda records: records[1]["episode"]["traces"][0]["response"].update(raw="NONE")]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                records = copy.deepcopy(self.records)
                mutate(records)
                with self.assertRaises((ValueError, KeyError)):
                    selector.prepare_cases(self.collection, records)
        changed = copy.deepcopy(self.collection)
        changed["episodes"][0]["event"]["raw"] = self.response(1)["raw"]
        with self.assertRaises(ValueError):
            selector.prepare_cases(changed, self.records)

    def test_prepared_source_mutations_cannot_reach_callback(self):
        for field in ("sources", "cases", "attempts"):
            changed = copy.deepcopy(self.plan)
            changed[field].pop()
            with self.assertRaisesRegex(ValueError, "prepared_cases_source_drift"):
                selector.collect_selection(changed, lambda messages: self.fail("must not generate"))

    def test_receipt_actor_and_panel_bindings(self):
        plan = selector.prepare(self.collection, self.records, **self.bindings)
        self.assertEqual(plan["actor_state_sha256"], ACTOR_HASH)
        for key, value in (("loaded_adapter_state_sha256", "d" * 64),
                           ("initial_training_result_sha256", "e" * 64),
                           ("phase", "train"), ("state", "AFTER"), ("fits", 1),
                           ("development_arm", "CUE_LOSS_OFF"), ("reader_wrapper", 8),
                           ("adult_source", {"collection_sha256": "f" * 64}),
                           ("panels", {"OWN_PARAMETRIC": {"denominator": 4, "episodes": []}})):
            bindings = copy.deepcopy(self.bindings)
            bindings["before_result"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                selector.prepare(self.collection, self.records, **bindings)

    def test_captured_replay_including_failures_and_origin_drift(self):
        calls = []

        def generate(messages):
            calls.append(messages)
            return self.response() if len(calls) == 1 else self.response(raw="NONE")

        result = selector.collect(generate, self.collection, self.records, **self.bindings)
        origins = selector.replay_selection(result, self.collection, self.records, **self.bindings)
        self.assertEqual(origins, result["material_origins"])
        for mutate in (lambda record: record["captures"].pop(),
                       lambda record: record["captures"].append(copy.deepcopy(record["captures"][0])),
                       lambda record: record["captures"][0]["messages"][0].update(content="changed"),
                       lambda record: record["material_origins"][0].update(source_index=2),
                       lambda record: record.update(fits=1)):
            changed = copy.deepcopy(result)
            mutate(changed)
            with self.assertRaises(ValueError):
                selector.replay_selection(changed, self.collection, self.records, **self.bindings)

    def test_callback_failure_replays_without_retry(self):
        def generate(messages):
            raise RuntimeError("retained transport failure")

        result = selector.collect_selection(self.plan, generate)
        self.assertEqual(result["chosen_source_indexes"], [None, None])
        self.assertEqual(selector.replay_selection(result, self.collection, self.records), [])
        self.assertEqual(result["model_calls"], 2)

    def test_coherently_changed_outcome_cannot_override_actual_own_receipt(self):
        records = copy.deepcopy(self.records)
        episode = records[1]["episode"]
        new_outcome = self.collection["bank"][1]["outcome"]
        episode["traces"][-1]["outcome"] = new_outcome
        episode.update(outcome=new_outcome, reached_goal=True, terminal_reason="reached_goal")
        with self.assertRaisesRegex(ValueError, "actual_transition_disagrees_with_own_receipt"):
            selector.prepare_cases(self.collection, records)

    def test_zero_errors_means_zero_calls_and_four_errors_means_four(self):
        for wrong in (False, True):
            records = []
            for fact in self.collection["bank"]:
                candidates = [other for other in self.collection["bank"] if other["node"] == fact["node"]]
                chosen = next(other for other in candidates if (other["outcome"] != fact["outcome"]) == wrong)
                episode = controller.run_episode(controller.public_task(fact),
                    lambda messages: dict(raw="ROUTE " + chosen["port"], terminal=True, truncated=False),
                    lambda address: self.fail("no reads"), lambda port: chosen["outcome"])
                records.append(dict(event=fact["event"], episode=episode))
            plan = selector.prepare_cases(self.collection, records)
            result = selector.collect_selection(plan, lambda messages: self.response())
            self.assertEqual(result["model_calls"], 4 if wrong else 0)
            self.assertEqual(result["task_denominator"], 4)


class StoredBeforeTests(unittest.TestCase):
    def test_actual_local_a2_before_has_two_explicit_mismatch_cases(self):
        root = Path(__file__).resolve().parents[1] / (
            "gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/capture/CUE_REPLAY")
        if not root.exists():
            self.skipTest("optional ignored captured evidence unavailable")
        collection = json.loads((root / "collect/COLLECTION.json").read_text())
        records = [json.loads((root / "before/new_task" / ("OWN_PARAMETRIC_EPISODE_%02d.json" % number)).read_text())
                   for number in range(1, 5)]
        collection_result = json.loads((root / "collect/RESULT.json").read_text())
        before_result = json.loads((root / "before/RESULT.json").read_text())
        plan = selector.prepare(collection, records, collection_result=collection_result,
                                before_result=before_result,
                                expected_actor_state_sha256="07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300")
        self.assertEqual(plan["expected_calls"], 2)
        self.assertEqual([case["route_index"] for case in plan["cases"]], [1, 2])
        self.assertEqual([source["event"] for source in plan["sources"]],
                         ["E_43DKZR6D3S", "E_VEEAOY3IIH", "E_QQ43NOEYBQ", "E_DEX6OHDHJP"])


if __name__ == "__main__":
    unittest.main()
