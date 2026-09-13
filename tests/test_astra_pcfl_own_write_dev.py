"""Synthetic CPU actor emissions; no native model, GPU, or writer execution."""

import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import test_astra_pcfl_native_actor as actor_fixtures
import test_pcfl_vertical_formation_plan as formation_fixtures
from gpu import astra_pcfl_native_actor as actor_api
from gpu import astra_pcfl_own_write_dev as driver
from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_train as full_writer


class ScriptedSession(actor_fixtures.Session):
    def __init__(self, model, clock, outputs):
        super().__init__(model, clock)
        self.outputs = outputs

    def generate(self, prompt, sampling):
        self.text = self.outputs[len(self.calls)]
        return super().generate(prompt, sampling)


class OwnFormationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = actor_fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.cell = core.WorldCell(core.build_root("disposable/0"), 0, 0, 0)
        self.actions, self.links = formation_fixtures.choices(self.cell)
        self.event_raw, self.link_raw = formation_fixtures.synthetic_child_spans(self.cell, self.actions, self.links)
        self.outputs = [raw for pair in zip(self.actions, self.event_raw) for raw in pair] + self.link_raw
        self.settings = copy.deepcopy(self.fixture.config)
        self.settings["source_files"].update(driver.source_pins())
        self.settings["max_calls"] = 20
        self.limits = {"output_tokens": 2048, "input_tokens": 16000, "returned_tokens": 0,
                       "remaining_reads": 0, "deadline": 90.0, "device_seconds": 60.0}
        self.config = self.build()
        self.out = self.fixture.root / "formation"

    def build(self):
        return driver.build_config(self.cell, self.actions, self.links,
                                   actor_config=self.settings, seed=71, limits=self.limits)

    def actor(self):
        session = ScriptedSession(self.fixture.model, self.fixture.clock, self.outputs)
        native = actor_api.NativeActor(self.settings, loader=Mock(return_value=session),
                                      environment_reader=lambda: copy.deepcopy(self.fixture.environment),
                                      clock=self.fixture.clock)
        self.addCleanup(native.close)
        return native, session

    def run_formation(self, *, mutation=None, reader=None):
        native, session = self.actor()
        if mutation is not None:
            session.mutate = mutation
        report = driver.run_formation(self.config, self.config["sha256"], native, self.out,
                                      receipt_reader=reader)
        return report, session

    def assert_replay(self, report):
        replay = driver.replay_validate(self.config, self.config["sha256"], report)
        self.assertTrue(replay["local_replay_valid"])
        self.assertFalse(replay["native_custody_verified"])

    def test_real_actor_twenty_calls_and_exact_writer_payload(self):
        report, session = self.run_formation()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(len(session.calls), 20)
        self.assertEqual(report["counts"], {"possible_calls": 20, "possible_events": 8,
            "possible_links": 4, "attempted_calls": 20, "accepted_events": 8, "accepted_links": 4})
        self.assertEqual(len(report["world_receipts"]), 8)
        payload = report["writer_payload"]
        self.assertEqual(len(payload["rows"]), 12)
        self.assertEqual(len(payload["queries"]), 17)
        self.assertEqual(payload["queries"], core.materialize_queries(payload["rows"]))
        self.assertEqual(payload["controls"], [])
        self.assertEqual(payload["first_block_slots"], self.config["planner"]["first_blocks"])
        self.assertEqual([row["raw"] for row in payload["rows"]], self.event_raw + self.link_raw)
        for row, generation, index in zip(payload["rows"], payload["generations"],
                                          list(range(1, 16, 2)) + list(range(16, 20))):
            self.assertEqual(generation["origin"], "CHILD_INJECTED_CPU_TEST")
            self.assertEqual(set(generation), {"raw", "sha256", "origin", "capture_sha256"})
            self.assertEqual(generation["raw"], row["raw"])
            self.assertEqual(generation["sha256"], row["provenance"]["generation_sha256"])
            self.assertEqual(row["provenance"]["byte_start"], 0)
            self.assertEqual(row["provenance"]["byte_end"], len(generation["raw"].encode("utf-8")))
            self.assertEqual(generation["capture_sha256"], driver.digest(report["slots"][index]["attempt"]["capture"]))
        self.assertFalse(report["native_custody_verified"])
        self.assertFalse(report["full_contract_released"])
        self.assertEqual((report["fits"], report["updates"]), (0, 0))
        self.assertEqual(session.closed, 0)
        self.assert_replay(report)

    def test_actual_e5_z_and_e7_second_b_not_ideal_indices(self):
        report, _ = self.run_formation()
        root = self.cell.root
        events = {row["fields"]["event"]: row["fields"] for row in report["writer_payload"]["rows"]
                  if row["kind"] == "EVENT"}
        fifth = events[root.lookup("event", "e5")]
        seventh = events[root.lookup("event", "e7")]
        self.assertEqual([fifth[key] for key in ("source", "destination", "receipt")],
                         [root.lookup("node", "Z"), root.lookup("node", "Y"), root.lookup("receipt", "r5")])
        self.assertEqual(seventh["source"], root.lookup("node", "B"))
        self.assertEqual(seventh["port"], root.lookup("port", "f1"))
        self.assertNotEqual(seventh["port"], events[root.lookup("event", "e4")]["port"])

    def test_alternate_choices_are_sealed_and_supported(self):
        self.actions, self.links = formation_fixtures.choices(self.cell, first_left="a1", first_right="f1", reverse_links=True)
        self.event_raw, self.link_raw = formation_fixtures.synthetic_child_spans(self.cell, self.actions, self.links)
        self.outputs = [raw for pair in zip(self.actions, self.event_raw) for raw in pair] + self.link_raw
        self.config = self.build()
        report, _ = self.run_formation()
        self.assertEqual(report["status"], "COMPLETE")
        self.assert_replay(report)

    def test_valid_action_mismatch_records_actual_outcome_then_stops(self):
        self.outputs[0] = formation_fixtures.choices(self.cell, first_left="a1")[0][0]
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(report["status"], "FORMATION_FAILED")
        self.assertIn("pre-output choice", report["failure"]["message"])
        self.assertTrue(report["slots"][0]["world_result"]["ok"])
        self.assertEqual(len(report["world_receipts"]), 1)
        self.assertIsNone(report["writer_payload"])
        self.assertTrue(all(slot["status"] == "UNCALLED" for slot in report["slots"][1:]))
        self.assert_replay(report)

    def test_invalid_action_has_no_receipt_and_no_record_call(self):
        self.outputs[0] = "EXPLORE bogus bogus"
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(report["world_receipts"], [])
        self.assertFalse(report["slots"][0]["world_result"]["ok"])
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_length_action_never_executes(self):
        report, session = self.run_formation(mutation=lambda raw: {**raw, "finish_reason": "length"})
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(report["world_receipts"], [])
        self.assertIsNone(report["slots"][0]["world_result"])
        self.assertIn("non-stop", report["failure"]["message"])
        self.assert_replay(report)

    def test_length_event_preserved_but_not_admitted(self):
        report, session = self.run_formation(mutation=lambda raw: {**raw, "finish_reason": "length"}
                                            if raw["text"].startswith("EVENT ") else raw)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(len(report["world_receipts"]), 1)
        self.assertEqual(report["admissions"], [])
        self.assertEqual(report["slots"][1]["attempt"]["response"]["text"], self.event_raw[0])
        self.assert_replay(report)

    def test_fenced_event_not_repaired(self):
        self.outputs[1] = "```text\n" + self.event_raw[0] + "```"
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 2)
        self.assertFalse(report["admissions"][0]["accepted"])
        self.assertEqual(report["admissions"][0]["raw"], self.outputs[1])
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_missing_terminal_lf_event_not_repaired(self):
        self.outputs[1] = self.event_raw[0].rstrip("\n")
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 2)
        self.assertFalse(report["admissions"][0]["accepted"])
        self.assertEqual(report["admissions"][0]["raw"], self.outputs[1])
        self.assertEqual(report["status"], "FORMATION_FAILED")
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_missing_terminal_lf_link_not_repaired(self):
        self.outputs[16] = self.link_raw[0].rstrip("\n")
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 17)
        self.assertEqual(report["slots"][16]["status"], "FAILED")
        self.assertIsNone(report["slots"][16]["admission"])
        self.assertEqual(report["slots"][16]["attempt"]["response"]["text"], self.outputs[16])
        self.assertEqual(report["counts"]["accepted_links"], 0)
        self.assertEqual(report["status"], "FORMATION_FAILED")
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_only_twelve_commitment_prompts_append_lf_rule(self):
        report, _ = self.run_formation()
        rule = ("End your response with exactly one LF (U+000A) after the last identifier. "
                "Emit the actual newline character, not the literal characters backslash-n (\\n). "
                "Do not add a blank line.")
        self.assertEqual(driver.LF_COMMITMENT_RULE, rule)
        self.assertEqual(self.config["policy"], "public_session_history_whole_response_stop_only_fail_fast_v2")
        for index, slot in enumerate(report["slots"]):
            prompt = slot["attempt"]["request"]["messages"][-1]["content"]
            if slot["kind"] == "EXPLORE":
                original = self.config["planner"]["opportunities"][index // 2]["explore_prompt"]
                self.assertEqual(prompt, original)
                self.assertNotIn(rule, prompt)
            else:
                if slot["kind"] == "EVENT":
                    original = (report["slots"][index - 1]["world_result"]["public"]
                                + self.config["planner"]["opportunities"][index // 2]["event_prompt"])
                else:
                    original = core.LINK_TEMPLATE.format(
                        FRESH_LINK_ID=self.config["planner"]["links"][index - 16]["link_handle"])
                self.assertEqual(prompt, original + "\n" + rule)
                self.assertEqual(prompt.count(rule), 1)
        self.assertEqual(sum(slot["kind"] != "EXPLORE" for slot in report["slots"]), 12)
        self.assertEqual([row["raw"] for row in report["writer_payload"]["rows"]], self.event_raw + self.link_raw)

    def test_wrong_event_receipt_rejected(self):
        self.outputs[1] = self.event_raw[0].replace(self.cell.root.lookup("receipt", "r0"),
                                                  self.cell.root.lookup("receipt", "r1"))
        report, _ = self.run_formation()
        self.assertEqual(report["counts"]["accepted_events"], 0)
        self.assertIn("own executed receipt", report["admissions"][0]["error"])
        self.assert_replay(report)

    def test_other_valid_link_pair_does_not_reselect_bank(self):
        second = core.parse_link_line(self.link_raw[1])
        second["link"] = self.cell.root.lookup("link", "l0")
        self.outputs[16] = core.LINK_WIRE.format(**second)
        report, session = self.run_formation()
        self.assertEqual(len(session.calls), 17)
        self.assertIn("pre-output choice", report["failure"]["message"])
        self.assertEqual(report["counts"]["accepted_links"], 0)
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_public_history_only_actual_receipts_and_child_outputs(self):
        report, _ = self.run_formation()
        for index, slot in enumerate(report["slots"]):
            request = slot["attempt"]["request"]
            self.assertEqual(set(request), {"id", "messages", "seed", "mount"})
            self.assertEqual(request["messages"][0], {"role": "system", "content": core.FORMATION_SYSTEM})
            self.assertEqual(len(request["messages"]), 2 + 2 * index)
            self.assertEqual([message["content"] for message in request["messages"][2::2]], self.outputs[:index])
            for message in request["messages"]:
                self.assertEqual(set(message), {"role", "content"})
                self.assertNotIn("disposable/0", message["content"])
                self.assertNotIn("expected_bank", message["content"])
        self.assertEqual(report["slots"][1]["attempt"]["request"]["messages"][-1]["content"],
                         driver.commitment_prompt(report["slots"][0]["world_result"]["public"]
                                                  + self.config["planner"]["opportunities"][0]["event_prompt"]))

    def test_preoutput_config_and_actor_reuse_fail_before_generation(self):
        native, session = self.actor()
        changed = copy.deepcopy(self.config)
        changed["planner"]["actions"][0] = "different"
        with self.assertRaises(driver.FormationError):
            driver.run_formation(changed, self.config["sha256"], native, self.out)
        self.assertEqual(session.calls, [])
        self.assertFalse(self.out.exists())
        report = driver.run_formation(self.config, self.config["sha256"], native, self.out)
        with self.assertRaises(driver.FormationError):
            driver.run_formation(self.config, self.config["sha256"], native, self.fixture.root / "retry")
        self.assertEqual(len(session.calls), 20)
        self.assert_replay(report)

    def test_no_private_config_additions_or_bool_seed(self):
        for key in ("parent_text", "expected_target", "oracle"):
            changed = copy.deepcopy(self.config)
            changed[key] = "not allowed"
            with self.assertRaises(driver.FormationError):
                driver.validate_config(changed, self.config["sha256"])
        with self.assertRaises(driver.FormationError):
            driver.build_config(self.cell, self.actions, self.links, actor_config=self.settings,
                                seed=True, limits=self.limits)

    def reader_mutating(self, edit):
        def reader(index):
            capture = driver.read_actor_capture(self.settings["output_dir"], index)
            edit(capture, index)
            return capture
        return reader

    def edit_file(self, capture, name, edit):
        value = json.loads(capture["files"][name]["utf8"])
        edit(value)
        payload = driver.canonical(value).decode()
        capture["files"][name] = {"utf8": payload, "sha256": core.byte_hash(payload)}

    def test_join_rejects_prompt_token_mismatch_even_with_new_file_hash(self):
        def edit(capture, index):
            self.edit_file(capture, f"call_{index:04d}.raw.json",
                           lambda value: value["raw"]["prompt_token_ids"].append(987))
        report, session = self.run_formation(reader=self.reader_mutating(edit))
        self.assertEqual(len(session.calls), 1)
        self.assertIn("token join", report["failure"]["message"])
        self.assert_replay(report)

    def test_join_rejects_model_route_contamination(self):
        def edit(capture, index):
            self.edit_file(capture, "identity.json", lambda value: value["identity"].update(lora_request={"path": "parent"}))
        report, _ = self.run_formation(reader=self.reader_mutating(edit))
        self.assertIn("route identity", report["failure"]["message"])
        self.assertIsNone(report["writer_payload"])
        self.assert_replay(report)

    def test_actor_identity_cannot_change_between_calls(self):
        def edit(capture, index):
            if index == 1:
                self.edit_file(capture, "identity.json", lambda value: value.update(pid=value["pid"] + 1))
        report, session = self.run_formation(reader=self.reader_mutating(edit))
        self.assertEqual(len(session.calls), 2)
        self.assertIn("identity changed", report["failure"]["message"])
        self.assert_replay(report)

    def test_public_prompt_receipt_cannot_add_teacher_text(self):
        def edit(capture, index):
            self.edit_file(capture, f"call_{index:04d}.request.json",
                           lambda value: value["request"]["messages"].append({"role": "user", "content": "teacher target"}))
        report, _ = self.run_formation(reader=self.reader_mutating(edit))
        self.assertIn("public request", report["failure"]["message"])
        self.assert_replay(report)

    def test_missing_finish_sidecar_is_not_assumed_stop(self):
        def edit(capture, index):
            capture["files"].pop(f"call_{index:04d}.raw.json")
        report, _ = self.run_formation(reader=self.reader_mutating(edit))
        self.assertEqual(report["world_receipts"], [])
        self.assertIn("missing/extra/error", report["failure"]["message"])
        self.assert_replay(report)

    def test_chronology_drift_is_rejected(self):
        def edit(capture, index):
            self.edit_file(capture, f"call_{index:04d}.raw.json",
                           lambda value: value.update(generation_ended=value["operation_started"] - 1))
        report, _ = self.run_formation(reader=self.reader_mutating(edit))
        self.assertIn("chronology", report["failure"]["message"])
        self.assert_replay(report)

    def test_config_is_on_disk_before_first_call_and_build_is_deterministic(self):
        native, session = self.actor()
        generate = native.generate
        def check_seal(request, limits):
            self.assertEqual(json.loads((self.out / "config.json").read_bytes()), self.config)
            self.assertEqual(json.loads((self.out / "call_00.request.json").read_bytes())["request"]["id"],
                             "old/formation/00")
            return generate(request, limits)
        native.generate = check_seal
        self.assertEqual(self.config, self.build())
        report = driver.run_formation(self.config, self.config["sha256"], native, self.out)
        self.assertEqual(len(session.calls), 20)
        self.assert_replay(report)

    def test_sidecar_original_bytes_preserved_and_drift_rejected(self):
        report, _ = self.run_formation()
        capture = report["slots"][0]["attempt"]["capture"]
        for name, record in capture["files"].items():
            native_bytes = (Path(self.settings["output_dir"]) / name).read_bytes()
            self.assertEqual(record["utf8"].encode(), native_bytes)
            self.assertEqual(record["sha256"], hashlib.sha256(native_bytes).hexdigest())
        changed = copy.deepcopy(report)
        changed["slots"][0]["attempt"]["capture"]["files"]["config.json"]["utf8"] += " "
        changed = driver.seal({key: value for key, value in changed.items() if key != "sha256"})
        with self.assertRaisesRegex(driver.FormationError, "replay differs"):
            driver.replay_validate(self.config, self.config["sha256"], changed)

    def test_replay_rejects_missing_extra_uncalled_or_teacher_targets(self):
        report, _ = self.run_formation()
        for edit in (lambda value: value["slots"].pop(),
                     lambda value: value["slots"].append(copy.deepcopy(value["slots"][0])),
                     lambda value: value["slots"][19].update(status="UNCALLED"),
                     lambda value: value["writer_payload"]["generations"][0].update(raw="teacher answer"),
                     lambda value: value["writer_payload"]["rows"][0].update(taint="CEILING_FIXTURE")):
            changed = copy.deepcopy(report)
            edit(changed)
            changed = driver.seal({key: value for key, value in changed.items() if key != "sha256"})
            with self.assertRaises(driver.FormationError):
                driver.replay_validate(self.config, self.config["sha256"], changed)

    def test_actor_exception_keeps_raw_error_and_fixed_failure_denominator(self):
        def fail(raw):
            raise RuntimeError("CPU injected failure")
        report, session = self.run_formation(mutation=fail)
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(report["counts"]["possible_calls"], 20)
        self.assertEqual(report["counts"]["attempted_calls"], 1)
        self.assertIsNotNone(report["slots"][0]["attempt"]["backend_error"])
        self.assertIn("call_0000.error.json", report["slots"][0]["attempt"]["capture"]["files"])
        self.assertTrue((self.out / "formation.json").is_file())
        self.assert_replay(report)

    def test_bool_token_id_rejected_and_original_raw_remains(self):
        report, _ = self.run_formation(mutation=lambda raw: {**raw, "output_token_ids": [True]})
        self.assertEqual(report["status"], "FORMATION_FAILED")
        files = report["slots"][0]["attempt"]["capture"]["files"]
        self.assertEqual(json.loads(files["call_0000.raw.json"]["utf8"])["raw"]["output_token_ids"], [True])
        self.assert_replay(report)

    def test_no_full_writer_gate_or_fit_invocation(self):
        with patch.object(full_writer, "train_fit", side_effect=AssertionError("must not fit")), \
             patch.object(full_writer, "_require_execution_contract", side_effect=AssertionError("must not release")):
            report, _ = self.run_formation()
        self.assertEqual(report["status"], "COMPLETE")
        self.assertFalse(report["full_contract_released"])

    def test_cold_load_precedes_generation_not_operation_start(self):
        native, session = self.actor()
        def cold_loader(settings):
            self.fixture.clock.now += 2.0
            return session
        native._loader = cold_loader
        report = driver.run_formation(self.config, self.config["sha256"], native, self.out)
        load = json.loads((Path(self.settings["output_dir"]) / "load.json").read_bytes())
        files = driver._capture_data(report["slots"][0]["attempt"]["capture"], 0)
        raw = files["call_0000.raw.json"]
        self.assertLess(raw["operation_started"], load["ready_at"])
        self.assertGreaterEqual(raw["generation_started"], load["ready_at"])
        self.assertEqual(report["device_seconds"], 7.0)
        self.assertEqual(report["status"], "COMPLETE")
        self.assert_replay(report)


if __name__ == "__main__":
    unittest.main()
