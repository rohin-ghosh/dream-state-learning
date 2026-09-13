"""Pure CPU scripted callbacks with the pinned original world and parser."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("contract_core_test", "/tmp/astra_parenting_contract_core_20260913.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def public_from_prompt(prompt):
    return json.loads(re.search(r"(?:^|\n)(?:Public task|Original public task):\n([^\n]+)", prompt).group(1))


def note_from_public(public):
    receipts = public["receipts"]
    if len(receipts) == 1:
        receipt = receipts[0]
        return dict(predicted=receipt["predicted"], observed=receipt["observed"], relation=core.relation(receipt["predicted"], receipt["observed"]))
    receipt = max(receipts, key=lambda item: item["time"])
    return dict(receipt_id=receipt["receipt_id"], **{"try": receipt["try"]}, observed=receipt["observed"])


class Fixture:
    def __init__(self, *, extras=False, invalid=False, wrong_relation=False, splice=False, noncanonical=False, bad_restate=False):
        self.requests = []
        self.extras, self.invalid, self.wrong_relation = extras, invalid, wrong_relation
        self.splice, self.noncanonical, self.bad_restate = splice, noncanonical, bad_restate

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        prompt = request["input_messages"][0]["content"]
        if request["kind"] == "restate":
            raw = "Unrelated acknowledgement; café 雪. block="+str(request["block_index"])
        else:
            public = public_from_prompt(prompt)
            note = note_from_public(public)
            if self.extras:
                note["metadata"] = {"time": 2}
            if request["kind"] == "wake":
                payload = dict(note=note, prediction=None if self.invalid else False, action=dict(kind="TRY", values=[1, 2, 3]))
            else:
                receipt = json.loads(prompt.rsplit("\nFresh receipt:\n", 1)[1])
                event = dict(receipt_id=public["receipts"][0]["receipt_id"] if self.splice else receipt["receipt_id"], **{"try": receipt["try"]},
                    predicted=receipt["predicted"], observed=receipt["observed"], relation=core.relation(receipt["predicted"], receipt["observed"]))
                if self.wrong_relation:
                    event["relation"] = "mismatched" if event["relation"] == "matched" else "matched"
                payload = dict(address=public["address"], source=note, event=event)
                if self.extras:
                    payload["event"]["metadata"] = {"time": 3}
                    payload["metadata"] = "not a new score source"
            raw = " \n"+json.dumps(payload, indent=2)+"\n" if self.noncanonical else core.canonical(payload)
        return dict(request_id=request["request_id"], state=request["state"], raw=raw,
                    finish_reason="length" if self.bad_restate and request["kind"] == "restate" else "stop")


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="contract_cpu_fixture_")
        cls.protocol = Path(cls.temporary.name)/"canonical_protocol_copy.md"
        cls.protocol.write_bytes(Path(core.PROTOCOL_PATH).read_bytes())
        cls.protocol_pin = hashlib.sha256(cls.protocol.read_bytes()).hexdigest()
        cls.deps = core.load_dependencies("/tmp/astra_level1_real_record_source_20260913_attempt1",
            protocol_path=cls.protocol, protocol_sha256=cls.protocol_pin)
        cls.manifest = core.build_manifest(cls.deps)
        cls.tasks = cls.manifest["schedules"]["0"]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def capture(self, seed=0, arm="ALIGNED", **kwargs):
        backend = Fixture(**kwargs)
        return core.run_phase(f"perception_seed{seed}_{arm}", backend, self.deps), backend

    def wake(self, task=None):
        task = task or self.tasks[0]
        return dict(note=core.expected_note(task), prediction=False, action=dict(kind="TRY", values=[1, 2, 3]))

    def record(self, task=None):
        task = task or self.tasks[0]
        actual = core.world_result(self.deps.game_class(), self.deps, task["world_id"], [1, 2, 3], False)
        actual["receipt"] = dict(receipt_id="fixture-own-receipt")
        payload = dict(address=task["address"], source=core.expected_note(task),
            event=dict(receipt_id=actual["receipt"]["receipt_id"], **{"try": actual["values"]}, predicted=False,
                       observed=actual["observed"], relation=core.relation(False, actual["observed"])))
        return payload, actual

    def test_exact_canonical_protocol_and_no_arbitrary_pin(self):
        self.assertEqual(self.manifest["protocol_sha256"], self.protocol_pin)
        self.assertEqual(self.manifest["dependencies"]["alignment_core_sha256"], core.ALIGNMENT_SHA256)
        self.assertEqual(self.protocol_pin, "74b62e8ca4ba79e796f8fc666e065613758297fbd4610fd5bf3788d4da772572")
        defaults = core.load_dependencies("/tmp/astra_level1_real_record_source_20260913_attempt1")
        self.assertEqual(defaults.manifest["protocol_sha256"], self.protocol_pin)
        unrelated = Path(self.temporary.name)/"unrelated.md"
        unrelated.write_text("Not the canonical protocol.")
        with self.assertRaises(ValueError):
            core.load_dependencies(protocol_path=unrelated, protocol_sha256=hashlib.sha256(unrelated.read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            core.load_dependencies(protocol_path=self.protocol, protocol_sha256="0"*64)
        with self.assertRaises(ValueError):
            core.load_dependencies(protocol_path=self.protocol, protocol_sha256=self.protocol_pin, alignment_path=self.protocol)
        with self.assertRaises(ValueError):
            core.root_binding(True)

    def test_canonical_instructions_templates_and_cpu_only_budget(self):
        exact = {
            "P": "For the public receipt, report its prediction as stated before that action, its returned observation, and whether those values match. These are not your new action's prediction or outcome.",
            "C": "Select the executed public receipt with greatest time, not the last receipt displayed. Report that receipt's ID, action and observation together.",
        }
        for task in self.tasks:
            self.assertIn(exact[task["family"]], task["ordinary_prompt"])
            self.assertIn(core.NOTE_OUTPUT_TEMPLATES[task["family"]], task["ordinary_prompt"])
            self.assertIn(core.WAKE_OUTPUT_TEMPLATE, task["ordinary_prompt"])
        self.assertIn(core.RECORD_OUTPUT_TEMPLATE, core.RECORD_INSTRUCTION)
        self.assertEqual(self.manifest["limits"]["controller_seconds"], 1800)
        self.assertEqual(self.manifest["limits"]["collection_seconds"], 180)
        self.assertEqual(self.manifest["limits"]["aggregate_a40_hours_including_preparation"], 2)
        self.assertFalse(self.manifest["native_execution_authorized"])

    def test_frozen_assembled_prompt_fixture_bytes(self):
        unused_capture, backend = self.capture()
        self.assertEqual(core.digest(backend.requests), "f111e6c22b14179ff4fa19268c73eab3609b383bf3d81b6ab730fd26ddf9e53f")

    def test_shared_eight_task_roster_and_factor_balance(self):
        self.assertEqual(self.manifest["schedules"]["0"], self.manifest["schedules"]["1"])
        self.assertEqual(self.manifest["schedules"]["0"], self.manifest["schedules"]["2"])
        self.assertEqual([task["family"] for task in self.tasks], list("PPCCCCPP"))
        self.assertEqual([task["block_index"] for task in self.tasks], [0, 0, 1, 1, 2, 2, 3, 3])
        public_p = [task["public_receipts"][0] for task in self.tasks if task["family"] == "P"]
        self.assertEqual({(row["predicted"], row["observed"]) for row in public_p}, {(False, False), (False, True), (True, False), (True, True)})
        public_c = [task for task in self.tasks if task["family"] == "C"]
        self.assertEqual({(task["public"]["receipts"][0]["time"] == 2, task["public_receipts"][-1]["observed"]) for task in public_c},
                         {(False, False), (False, True), (True, False), (True, True)})
        for task in public_c:
            earlier, latest = task["public_receipts"]
            self.assertNotEqual(earlier["try"], latest["try"])
            self.assertIsNot(earlier["observed"], latest["observed"])
        self.assertEqual(len(set(task["source_fingerprint"] for task in self.tasks)), 8)

    def test_namespace_and_prior_source_collision(self):
        for key in ("task_id", "world_id", "address"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                core.build_manifest(self.deps, prior_ids=[self.tasks[0][key]])
        with self.assertRaises(ValueError):
            core.build_manifest(self.deps, prior_ids=[self.tasks[0]["public_receipts"][0]["receipt_id"]])
        with self.assertRaises(ValueError):
            core.build_manifest(self.deps, prior_task_fingerprints=[self.tasks[0]["source_fingerprint"]])
        with self.assertRaises(ValueError):
            core.build_manifest(self.deps, prior_ids=["same", "same"])
        self.assertTrue(all(task["task_id"].startswith("pc-") for task in self.tasks))

    def test_public_outcomes_are_frozen_world_calls(self):
        for task in self.tasks:
            for receipt in task["public_receipts"]:
                actual = core.world_result(self.deps.game_class(), self.deps, task["world_id"], receipt["try"], receipt["predicted"])
                self.assertIs(actual["observed"], receipt["observed"])
            for probe in task["public_world_evaluations"]:
                actual = core.world_result(self.deps.game_class(), self.deps, task["world_id"], probe["values"], probe["predicted"])
                self.assertEqual({key: probe[key] for key in actual}, actual)

    def test_all_nine_states_180_calls_replay_no_scientific_gate(self):
        captures = []
        for seed in range(3):
            for arm in core.ARMS:
                capture, backend = self.capture(seed, arm)
                self.assertEqual(len(backend.requests), 20)
                self.assertEqual(capture["readout"]["PROCESS_USE"], 8)
                self.assertEqual(capture["readout"]["SCHEMA_FULL_MATERIAL"], 8)
                self.assertEqual(capture["readout"]["RESTATE"], None)
                self.assertEqual(capture["readout"]["restate_completed"], 4)
                self.assertEqual(core.audit_capture(capture, dependencies=self.deps)["calls_replayed"], 20)
                captures.append(capture)
        summary = core.summarize(captures, self.deps)
        self.assertEqual(sum(cell["calls"] for cell in summary["cells"].values()), 180)
        self.assertTrue(summary["gate"]["complete"])
        self.assertIsNone(summary["gate"]["feasibility_pass"])
        self.assertFalse(summary["gate"]["thresholds_adopted"])
        self.assertFalse(summary["fit_authorized"])

    def test_contacts_exact_multisets_and_tasklocal_context(self):
        by_arm = {}
        for arm in core.ARMS:
            capture, backend = self.capture(arm=arm)
            by_arm[arm] = [contact["contact"]["raw"] for contact in capture["contacts"]]
            for request in backend.requests:
                text = request["input_messages"][0]["content"]
                if request["kind"] != "restate":
                    self.assertIn("café 雪", text)
                    self.assertIn("block="+str(request["block_index"]), text)
                    for other in set(range(4))-{request["block_index"]}:
                        self.assertNotIn("block="+str(other), text)
                    for lesson in core.LESSONS.values():
                        self.assertNotIn(lesson, text)
            self.assertEqual(len(capture["contacts"]), 4)
        self.assertEqual(sorted(by_arm["ALIGNED"]), sorted(by_arm["SWAPPED"]))
        self.assertEqual(by_arm["ACTIVE_NEUTRAL"], [core.NEUTRAL]*4)
        self.assertEqual(core.NEUTRAL, "Continue with the next scheduled tasks using their instructions. Briefly acknowledge this message before proceeding.")

    def test_extra_metadata_content_passes_schema_fails(self):
        capture, unused_backend = self.capture(extras=True)
        counts = capture["readout"]
        self.assertEqual(counts["PROCESS_USE"], 8)
        self.assertEqual(counts["FULL_MATERIAL"], 8)
        self.assertEqual(counts["EXECUTED"], 8)
        self.assertEqual(counts["WAKE_SCHEMA"], 0)
        self.assertEqual(counts["RECORD_SCHEMA"], 0)
        self.assertEqual(counts["SCHEMA_FULL_MATERIAL"], 0)

    def test_noncanonical_separate_from_content_schema(self):
        capture, unused_backend = self.capture(noncanonical=True)
        self.assertEqual(capture["readout"]["SCHEMA_FULL_MATERIAL"], 8)
        for row in capture["records"]:
            self.assertFalse(row["wake_score"]["canonical_form"])
            self.assertFalse(row["record_score"]["canonical_form"])

    def test_bad_or_unrelated_restate_never_vetoes_content(self):
        capture, unused_backend = self.capture(bad_restate=True)
        self.assertEqual(capture["readout"]["restate_completed"], 0)
        self.assertEqual(capture["readout"]["FULL_MATERIAL"], 8)
        self.assertIsNone(capture["readout"]["restate_mask"])

    def test_missing_field_does_not_erase_correct_fields(self):
        payload = self.wake()
        del payload["note"]["relation"]
        score = core.score_wake(core.canonical(payload), "stop", self.tasks[0])
        self.assertFalse(score["PROCESS_USE"])
        self.assertEqual(score["note"]["fields"]["relation"]["status"], "missing")
        self.assertTrue(score["note"]["field_correct"]["predicted"])
        self.assertTrue(score["note"]["field_correct"]["observed"])

    def test_no_alias_or_recursive_latest_extraction(self):
        task = self.tasks[2]
        for note in ({"receipts": task["public"]["receipts"]}, {"wrapper": core.expected_note(task)},
                     dict(id=core.expected_note(task)["receipt_id"], values=core.expected_note(task)["try"], outcome=core.expected_note(task)["observed"])):
            score = core.score_note(note, task)
            self.assertFalse(score["content_correct"])
            self.assertFalse(any(score["field_correct"].values()))
        note = core.expected_note(task)
        note["receipt_id"] = task["public_receipts"][0]["receipt_id"]
        score = core.score_note(note, task)
        self.assertFalse(score["field_correct"]["receipt_id"])
        self.assertTrue(score["field_correct"]["observed"])

    def test_duplicate_nonfinite_fenced_and_malformed_fail_closed(self):
        payload = core.canonical(self.wake())
        cases = [payload[:-1]+',"prediction":false}', payload.replace('"predicted":false', '"predicted":false,"predicted":false'),
                 payload[:-1]+',"meta":NaN}', payload[:-1]+',"meta":1e999}', '```json\n'+payload+'\n```', payload+' '+payload, '[]', '']
        for raw in cases:
            with self.subTest(raw=raw):
                score = core.score_wake(raw, "stop", self.tasks[0])
                self.assertFalse(score["PROCESS_USE"])
                self.assertFalse(score["action_valid"])
                self.assertFalse(score["json_valid"])
                self.assertTrue(all(field["status"] == "unassessable" for field in score["note"]["fields"].values()))

    def test_wrong_type_boolean_integer_no_coercion(self):
        payload = self.wake()
        payload["note"]["predicted"] = 0
        payload["action"]["values"][0] = True
        score = core.score_wake(core.canonical(payload), "stop", self.tasks[0])
        self.assertFalse(score["PROCESS_USE"])
        self.assertFalse(score["action_valid"])
        self.assertEqual(score["note"]["fields"]["predicted"]["status"], "wrong_type")

    def test_strict_dispatch_outer_extras_not_ignored(self):
        payload = self.wake()
        payload["metadata"] = "extra"
        score = core.score_wake(core.canonical(payload), "stop", self.tasks[0])
        self.assertTrue(score["PROCESS_USE"])
        self.assertFalse(score["schema_valid"])
        self.assertFalse(score["action_valid"])

    def test_wrong_relation_and_source_receipt_splice(self):
        for options in ({"wrong_relation": True}, {"splice": True}):
            capture, unused_backend = self.capture(**options)
            self.assertEqual(capture["readout"]["RECORD_SOURCE"], 8)
            self.assertEqual(capture["readout"]["OWN_EVENT"], 0)
            self.assertEqual(capture["readout"]["FULL_MATERIAL"], 0)
        payload, actual = self.record()
        payload["event"]["relation"] = True
        score = core.score_record(core.canonical(payload), "stop", self.tasks[0], actual, self.deps)
        self.assertEqual(score["event"]["fields"]["relation"]["status"], "wrong_type")
        self.assertTrue(score["event_fields"]["predicted"])

    def test_original_public_source_not_wrong_wake_note(self):
        payload, actual = self.record()
        payload["source"] = {"origin": "harness"}
        score = core.score_record(core.canonical(payload), "stop", self.tasks[0], actual, self.deps)
        self.assertTrue(score["OWN_EVENT"])
        self.assertFalse(score["RECORD_SOURCE"])
        self.assertFalse(score["RECORD_FAITHFUL"])

    def test_all_invalid_actions_keep_eight_slots_twelve_calls(self):
        capture, backend = self.capture(invalid=True)
        counts = capture["readout"]
        self.assertEqual(len(backend.requests), 12)
        self.assertEqual(counts["opportunities"], 8)
        self.assertEqual(counts["record_not_called"], 8)
        self.assertEqual(counts["PROCESS_USE"], 8)
        self.assertEqual(counts["EXECUTED"], 0)
        self.assertEqual(counts["FULL_MATERIAL"], 0)
        self.assertEqual(counts["by_family"]["C"]["denominator"], 4)

    def test_empty_partial_missing_duplicate_slots(self):
        empty = core.readout([], [], [])
        self.assertEqual(empty["opportunities"], 8)
        self.assertEqual(empty["missing_slots"], list(range(8)))
        self.assertFalse(empty["complete"])
        self.assertEqual(empty["endpoint_masks"]["PROCESS_USE"], [False]*8)
        capture, unused_backend = self.capture()
        partial = core.readout(capture["records"][:1], [], [])
        self.assertEqual(partial["PROCESS_USE"], 1)
        self.assertEqual(partial["opportunities"], 8)
        with self.assertRaises(ValueError):
            core.readout([capture["records"][0]]*2, [], [])
        self.assertFalse(core.threshold_vector({})["complete"])

    def test_per_field_and_family_denominators_survive_uncalled(self):
        capture, unused_backend = self.capture(invalid=True)
        counts = capture["readout"]
        self.assertEqual(len(counts["per_field"]["own_event"]), 8)
        self.assertTrue(all(item["status"] == "record_uncalled" and item["fields"] is None for item in counts["per_field"]["own_event"]))
        self.assertTrue(all(item["fields"] is not None for item in counts["per_field"]["public_note"]))
        for family in ("P", "C"):
            for delivery in ("0", "1"):
                self.assertEqual(counts["by_family_delivery"][family][delivery]["denominator"], 2)
                self.assertEqual(counts["by_family_delivery"][family][delivery]["PROCESS_USE"], 2)
        empty = core.readout([], [], [])
        result = core.threshold_vector({core.STATES[0]: empty})
        self.assertEqual(result["incomplete"], [core.STATES[0]])

    def test_no_success_on_length_and_backend_failure_preserved(self):
        score = core.score_wake(core.canonical(self.wake()), "length", self.tasks[0])
        self.assertFalse(score["PROCESS_USE"])
        self.assertFalse(score["action_valid"])
        def broken(request):
            raise RuntimeError("fixture backend failed")
        capture = core.run_phase(core.STATES[0], broken, self.deps)
        self.assertEqual(capture["readout"]["calls"], 12)
        self.assertEqual(capture["readout"]["PROCESS_USE"], 0)
        self.assertIn("backend_error", capture["records"][0]["wake"]["errors"])

    def test_wrong_route_binding_and_resigned_prompt_or_score_tamper(self):
        backend = Fixture()
        def wrong(request):
            response = backend(request)
            response["state"] = "foreign"
            return response
        with self.assertRaises(ValueError):
            core.run_phase(core.STATES[0], wrong, self.deps)
        binding = core.root_binding(0)
        binding["adapter_files"] = {"adapter_model.safetensors": "wrong"}
        with self.assertRaises(ValueError):
            core.run_phase(core.STATES[0], Fixture(), self.deps, binding={"producer": binding})
        capture, unused_backend = self.capture()
        for target in ("request", "score", "world"):
            altered = copy.deepcopy(capture)
            if target == "request":
                next(event for event in altered["events"] if event["kind"] == "call")["request"]["input_messages"][0]["content"] += " LEAK"
            elif target == "score":
                altered["records"][0]["wake_score"]["PROCESS_USE"] = False
            else:
                next(event for event in altered["events"] if event["kind"] == "execution")["observed"] = "fake"
            altered["capture_sha256"] = core.digest({key: value for key, value in altered.items() if key != "capture_sha256"})
            with self.subTest(target=target), self.assertRaises(ValueError):
                core.replay_validate(altered, self.deps)


if __name__ == "__main__":
    unittest.main()
