"""CPU RuleGame and scripted child fixtures only; no native/model/tokenizer calls."""
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest


spec = importlib.util.spec_from_file_location("alignment_core_test", "/tmp/astra_parenting_alignment_core_20260913.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def public_from_prompt(prompt):
    match = re.search(r"(?:^|\n)(?:Public task|Original public task):\n([^\n]+)", prompt)
    return json.loads(match.group(1))


def note_from_public(public):
    receipts = public["receipts"]
    if len(receipts) == 1:
        receipt = receipts[0]
        return dict(predicted=receipt["predicted"], observed=receipt["observed"], relation=core.relation(receipt["predicted"], receipt["observed"]))
    receipt = max(receipts, key=lambda item: item["time"])
    return dict(receipt_id=receipt["receipt_id"], **{"try": receipt["try"]}, observed=receipt["observed"])


class Fixture:
    def __init__(self, *, mode="faithful", noncanonical=False, alias=False, bad_restate=False, malformed=False,
                 length=False, splice=False, generic=False, raise_kind=None, raw_restate=None):
        self.options = locals().copy()
        self.requests = []

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        kind = request["kind"]
        if self.options["raise_kind"] == kind:
            raise ValueError("ordinary CPU fixture call failure")
        prompt = request["input_messages"][0]["content"]
        if kind == "restate":
            lesson = prompt.split("Message:\n", 1)[1].split("\n\nRestate", 1)[0]
            raw = self.options["raw_restate"]
            if raw is None:
                raw = "I will consider things." if self.options["bad_restate"] else lesson
            raw += f"\nCHILD_BLOCK_SENTINEL_{request['block_index']}"
        elif kind == "wake":
            public = public_from_prompt(prompt)
            note = note_from_public(public)
            if self.options["mode"] == "following_note":
                operation = "P" if len(public["receipts"]) == 1 else "C"
                if core.LESSONS[operation] not in prompt:
                    note = {"claim": "I used the process."}
            if self.options["generic"]:
                note = {"claim": "Keep prediction separate and select the latest same receipt."}
            if self.options["alias"] and "claim" not in note:
                if "predicted" in note:
                    note = dict(prior=note["predicted"], observation=note["observed"], comparison="same" if note["relation"] == "matched" else "different")
                else:
                    note = dict(id=note["receipt_id"], action=dict(kind="TRY", values=note["try"]), outcome=note["observed"])
            payload = dict(note=note, prediction=bool(request["task_index"] % 2), action=dict(kind="TRY", values=[request["task_index"]-7, 2, 9]))
            if self.options["malformed"]:
                payload["action"]["values"][0] = True
            raw = self.serialize(payload)
        else:
            public = public_from_prompt(prompt)
            receipt = json.loads(prompt.rsplit("\nFresh receipt:\n", 1)[1])
            raw_wake = prompt.split("\nYour pre-action output (verbatim):\n", 1)[1].rsplit("\nFresh receipt:", 1)[0]
            wake = json.loads(raw_wake)
            event = dict(receipt_id=receipt["receipt_id"], **{"try": receipt["try"]}, predicted=wake["prediction"], observed=receipt["observed"],
                         relation=core.relation(wake["prediction"], receipt["observed"]))
            if self.options["splice"]:
                event["receipt_id"] = public["receipts"][0]["receipt_id"]
            raw = self.serialize(dict(address=public["address"], source=wake["note"], event=event))
        return dict(request_id=request["request_id"], state=request["state"], raw=raw,
                    finish_reason="length" if self.options["length"] else "stop")

    def serialize(self, value):
        if self.options["noncanonical"]:
            return " \n"+json.dumps(dict(reversed(list(value.items()))), indent=2)+"\t\n"
        return core.canonical(value)


class AlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deps = core.load_dependencies()
        cls.manifest = core.build_manifest(cls.deps)

    def capture(self, seed=0, arm="ALIGNED", **options):
        backend = Fixture(**options)
        capture = core.run_phase(f"perception_seed{seed}_{arm}", backend, self.deps)
        return capture, backend

    def resign(self, capture):
        capture["capture_sha256"] = core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})

    def test_protocol_dependency_and_namespace_pins(self):
        self.assertEqual(self.manifest, core.build_manifest(self.deps))
        self.assertEqual(self.manifest["protocol_sha256"], "5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5")
        self.assertEqual(self.manifest["disjointness"]["distinct_new_ids"], 360)
        for key in ("task_id", "address", "world_id"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                core.build_manifest(self.deps, prior_ids=[self.manifest["schedules"]["0"][0][key]])
        with self.assertRaises(ValueError):
            core.load_dependencies(protocol_path=__file__)
        self.assertNotIn("._rule(", Path(core.__file__).read_text())

    def test_matched_structure_rotation_and_lawful_prior_receipts(self):
        for seed, tasks in self.manifest["schedules"].items():
            self.assertEqual([task["family"] for task in tasks[::4]], list("CPCP" if seed == "1" else "PCPC"))
            self.assertEqual([task["variant"] for task in tasks[::4]], [1, 1, 0, 0] if seed == "1" else [0, 0, 1, 1])
            for family in ("P", "C"):
                structures = []
                for delivery in (0, 1):
                    block = [task for task in tasks if task["family"] == family and task["delivery"] == delivery]
                    self.assertEqual(len(block), 4)
                    if family == "P":
                        structure = [(task["public_receipts"][0]["predicted"], task["public_receipts"][0]["observed"]) for task in block]
                        self.assertEqual(len(set(structure)), 4)
                    else:
                        structure = [(task["public_receipts"][-1]["observed"], task["public"]["receipts"][0]["time"]) for task in block]
                        self.assertEqual(len(set(structure)), 4)
                        self.assertTrue(all(receipt["predicted"] is None for task in block for receipt in task["public_receipts"]))
                    structures.append(structure)
                self.assertEqual(*structures)
            for task in tasks:
                game = self.deps.game_class()
                for probe in task["public_world_evaluations"]:
                    expected = core.world_result(game, self.deps, task["world_id"], probe["values"], probe["predicted"])
                    self.assertEqual({key: probe[key] for key in expected}, expected)
                for receipt in task["public_receipts"]:
                    actual = core.world_result(game, self.deps, task["world_id"], receipt["try"], receipt["predicted"])
                    self.assertIs(actual["observed"], receipt["observed"])
                prompt = task["ordinary_prompt"]
                for secret in (task["world_id"], "source_judge", "PROCESS_USE", "FULL_MATERIAL", "latest", "compare", "relation", "ALIGNED", "SWAPPED"):
                    self.assertNotIn(secret, prompt)

    def test_all_nine_states_312_max_calls_and_no_fit(self):
        captures = []
        for seed in range(3):
            for arm in core.ARMS:
                capture, backend = self.capture(seed, arm)
                self.assertEqual(len(backend.requests), 32 if arm == "NO_PARENT" else 36)
                self.assertEqual(capture["readout"]["opportunities"], 16)
                self.assertEqual(capture["readout"]["FULL_MATERIAL"], 16)
                self.assertEqual(capture["readout"]["RESTATE"], None if arm == "NO_PARENT" else 4)
                self.assertEqual(sum(event["kind"] == "execution" for event in capture["events"]), 16)
                self.assertEqual(capture["updates"], 0)
                self.assertFalse(capture["fit_authorized"])
                captures.append(capture)
        self.assertEqual(sum(capture["readout"]["calls"] for capture in captures), 312)
        report = core.summarize(captures, self.deps)
        self.assertFalse(report["gate"]["feasibility_pass"])
        self.assertFalse(report["fit_authorized"])

    def test_alignment_lesson_multiset_task_order_and_delivered_restatement(self):
        for seed in range(3):
            aligned, aligned_backend = self.capture(seed, "ALIGNED")
            swapped, swapped_backend = self.capture(seed, "SWAPPED")
            self.assertEqual(Counter(contact["contact"]["raw"] for contact in aligned["contacts"]), Counter({text: 2 for text in core.LESSONS.values()}))
            self.assertEqual(Counter(contact["contact"]["raw"] for contact in swapped["contacts"]), Counter(contact["contact"]["raw"] for contact in aligned["contacts"]))
            self.assertEqual([contact["score"]["content_correct"] for contact in swapped["contacts"]], [True]*4)
            for first, second in zip(aligned_backend.requests, swapped_backend.requests, strict=True):
                self.assertEqual(first["kind"], second["kind"])
                self.assertEqual(first["episode_id"], second["episode_id"])
                if first["kind"] == "wake":
                    self.assertEqual(public_from_prompt(first["input_messages"][0]["content"]), public_from_prompt(second["input_messages"][0]["content"]))

    def test_parent_removed_and_task_block_context_reset(self):
        capture, backend = self.capture(raw_restate="UNEDITED_CHILD_TEXT")
        task_ids = [record["task_id"] for record in capture["records"]]
        for request in backend.requests:
            text = request["input_messages"][0]["content"]
            if request["kind"] == "restate":
                self.assertNotIn("pa-", text)
                self.assertNotIn("CHILD_BLOCK_SENTINEL", text)
            else:
                for lesson in core.LESSONS.values():
                    self.assertNotIn(lesson, text)
                self.assertIn("UNEDITED_CHILD_TEXT", text)
                self.assertIn(f"CHILD_BLOCK_SENTINEL_{request['block_index']}", text)
                for block in set(range(4))-{request["block_index"]}:
                    self.assertNotIn(f"CHILD_BLOCK_SENTINEL_{block}", text)
                for task_id in set(task_ids)-{request["episode_id"]}:
                    self.assertNotIn(task_id, text)
        anchor, backend = self.capture(arm="NO_PARENT")
        self.assertEqual(anchor["contacts"], [])
        self.assertIsNone(anchor["readout"]["restate_mask"])
        for request in backend.requests:
            self.assertNotIn("Current child NOTE", request["input_messages"][0]["content"])

    def test_noncanonical_and_predeclared_mixed_aliases_are_content_success(self):
        capture, backend = self.capture(noncanonical=True, alias=True)
        self.assertEqual(capture["readout"]["FULL_MATERIAL"], 16)
        for record in capture["records"]:
            self.assertFalse(record["wake_score"]["canonical_form"])
            self.assertFalse(record["record_score"]["canonical_form"])
            self.assertEqual(record["wake_score"]["note"]["parse_errors"], [])
        self.assertTrue(core.replay_validate(json.loads(core.canonical(capture)), self.deps)["consistent"])

    def test_process_requires_values_not_generic_prose_and_record_splicing_fails(self):
        capture, backend = self.capture(generic=True)
        self.assertEqual(capture["readout"]["PROCESS_USE"], 0)
        self.assertEqual(capture["readout"]["EXECUTED"], 16)
        self.assertEqual(capture["readout"]["FULL_MATERIAL"], 0)
        spliced, backend = self.capture(splice=True)
        self.assertEqual(spliced["readout"]["PROCESS_USE"], 16)
        self.assertEqual(spliced["readout"]["RECORD_FAITHFUL"], 0)
        for row in spliced["records"]:
            self.assertFalse(row["record_score"]["event_fields"]["receipt_id"])

    def test_latest_is_independent_of_display_and_same_receipt_required(self):
        for task in self.manifest["schedules"]["0"]:
            if task["family"] != "C":
                continue
            good = core.expected_note(task)
            self.assertTrue(core.score_note(good, task)["content_correct"])
            earlier = min(task["public_receipts"], key=lambda item: item["time"])
            for field, value in (("receipt_id", earlier["receipt_id"]), ("try", earlier["try"]), ("observed", earlier["observed"])):
                self.assertFalse(core.score_note(dict(good, **{field: value}), task)["content_correct"])

    def test_prior_outcome_not_interchangeable_and_parse_errors_separate(self):
        task = next(task for task in self.manifest["schedules"]["0"] if task["family"] == "P" and task["public_receipts"][0]["predicted"] != task["public_receipts"][0]["observed"])
        note = core.expected_note(task)
        swapped = dict(note, predicted=note["observed"], observed=note["predicted"])
        score = core.score_note(swapped, task)
        self.assertFalse(score["content_correct"])
        self.assertTrue(score["canonical_note"])
        self.assertEqual(score["parse_errors"], [])
        self.assertTrue(score["binding_errors"])
        unknown = core.score_note({"ambiguous prose": "I compared them"}, task)
        self.assertTrue(unknown["parse_errors"])
        self.assertEqual(unknown["binding_errors"], [])
        self.assertFalse(core.score_note(dict(note, predicted=int(note["predicted"])), task)["content_correct"])

    def test_process_content_independent_of_missing_action_and_generic_schema(self):
        task = self.manifest["schedules"]["0"][0]
        raw = core.canonical(dict(note=core.expected_note(task), prediction=True))
        score = core.score_wake(raw, "stop", task)
        self.assertTrue(score["PROCESS_USE"])
        self.assertFalse(score["action_valid"])
        self.assertFalse(score["format_valid"])
        self.assertTrue(score["schema_errors"])
        self.assertEqual(score["parse_errors"], [])

    def test_lessons_are_answer_free_and_wrong_restatement_operation_fails(self):
        for name, lesson in core.LESSONS.items():
            self.assertTrue(core.score_restate(lesson, "stop", name)["content_correct"])
            self.assertFalse(core.score_restate(lesson, "stop", "C" if name == "P" else "P")["content_correct"])
            self.assertIsNone(re.search(r"[0-9]|\b(?:True|False|null|matched|mismatched)\b|pa-", lesson))
            for tasks in self.manifest["schedules"].values():
                for task in tasks:
                    self.assertNotIn(task["task_id"], lesson)
                    self.assertNotIn(task["address"], lesson)
                    for receipt in task["public_receipts"]:
                        self.assertNotIn(receipt["receipt_id"], lesson)
                        self.assertNotIn(core.canonical(receipt["try"]), lesson)

    def test_malformed_actions_all_slots_retained_no_fake_world_or_records(self):
        capture, backend = self.capture(malformed=True)
        self.assertEqual(len(backend.requests), 20)
        self.assertEqual(capture["readout"]["record_not_called"], 16)
        self.assertEqual(capture["readout"]["EXECUTED"], 0)
        self.assertEqual(capture["readout"]["PROCESS_USE"], 16)
        self.assertEqual(len(capture["records"]), 16)
        self.assertFalse(any(event["kind"] == "execution" for event in capture["events"]))
        self.assertTrue(core.replay_validate(capture, self.deps)["consistent"])

    def test_bad_restates_not_filtered_not_required_for_full_material(self):
        capture, backend = self.capture(bad_restate=True)
        self.assertEqual(capture["readout"]["RESTATE"], 0)
        self.assertEqual(capture["readout"]["FULL_MATERIAL"], 16)
        self.assertEqual(len(backend.requests), 36)
        self.assertTrue(all("I will consider things." in request["input_messages"][0]["content"] for request in backend.requests if request["kind"] != "restate"))

    def test_length_and_backend_failures_are_outcomes_without_retry(self):
        for options in (dict(length=True), dict(raise_kind="wake"), dict(raise_kind="restate"), dict(raise_kind="record")):
            with self.subTest(options=options):
                capture, backend = self.capture(**options)
                self.assertEqual(len(capture["records"]), 16)
                self.assertEqual(len({request["request_id"] for request in backend.requests}), len(backend.requests))
                self.assertLessEqual(len(backend.requests), 36)
                self.assertTrue(core.replay_validate(capture, self.deps)["consistent"])

    def test_fatal_native_fault_and_wrong_source_join_propagate(self):
        class NativeFault(BaseException):
            pass
        def broken(request):
            raise NativeFault("CPU sentinel; no actual native call")
        with self.assertRaises(NativeFault):
            core.run_phase(core.STATES[0], broken, self.deps)
        def wrong_source(request):
            return dict(request_id="sibling", state=request["state"], raw="text", finish_reason="stop")
        with self.assertRaises(ValueError):
            core.run_phase(core.STATES[0], wrong_source, self.deps)

    def test_replay_rejects_resigned_splice_missing_extra_and_modified_calls(self):
        capture, backend = self.capture()
        for mode in ("receipt", "missing", "extra", "prompt", "raw", "score"):
            changed = copy.deepcopy(capture)
            calls = [event for event in changed["events"] if event["kind"] == "call"]
            if mode == "receipt":
                changed["records"][0]["execution"]["receipt"]["observed"] = not changed["records"][0]["execution"]["receipt"]["observed"]
            elif mode == "missing":
                changed["events"].remove(calls[2])
            elif mode == "extra":
                changed["events"].append(copy.deepcopy(calls[2]))
            elif mode == "prompt":
                calls[1]["request"]["input_messages"][0]["content"] += "\nLEAKED_TEACHER"
            elif mode == "raw":
                calls[2]["response"]["raw"] = "{}"
            else:
                changed["readout"]["FULL_MATERIAL"] -= 1
            self.resign(changed)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                core.replay_validate(changed, self.deps)

    def gate_cells(self):
        cells = {}
        for seed in range(3):
            for arm, count in (("ALIGNED", 8), ("SWAPPED", 4), ("NO_PARENT", 6)):
                cells[f"perception_seed{seed}_{arm}"] = dict(RESTATE=3, PROCESS_USE=count, FULL_MATERIAL=8,
                    by_delivery={"0": dict(PROCESS_USE=4), "1": dict(PROCESS_USE=4)})
        return cells

    def test_exact_gate_vector_noncompensatory_boundaries(self):
        cells = self.gate_cells()
        passed = core.threshold_vector(cells)
        self.assertTrue(passed["feasibility_pass"])
        self.assertFalse(passed["fit_authorized"])
        for axis in ("restatement", "swapped_advantage", "swapped_no_large_harm", "anchor_advantage", "anchor_no_large_harm", "repeated_activation", "faithful_material"):
            changed = copy.deepcopy(cells)
            for seed in (0, 1) if axis not in ("swapped_no_large_harm", "anchor_no_large_harm") else (2,):
                aligned = changed[f"perception_seed{seed}_ALIGNED"]
                if axis == "restatement":
                    aligned["RESTATE"] = 2
                elif axis == "swapped_advantage":
                    changed[f"perception_seed{seed}_SWAPPED"]["PROCESS_USE"] = 5
                elif axis == "swapped_no_large_harm":
                    changed[f"perception_seed{seed}_SWAPPED"]["PROCESS_USE"] = 12
                elif axis == "anchor_advantage":
                    changed[f"perception_seed{seed}_NO_PARENT"]["PROCESS_USE"] = 7
                elif axis == "anchor_no_large_harm":
                    changed[f"perception_seed{seed}_NO_PARENT"]["PROCESS_USE"] = 11
                elif axis == "repeated_activation":
                    aligned["by_delivery"] = {"0": dict(PROCESS_USE=5), "1": dict(PROCESS_USE=3)}
                else:
                    aligned["FULL_MATERIAL"] = 7
            gate = core.threshold_vector(changed)
            with self.subTest(axis=axis):
                self.assertFalse(gate["vector"][axis])
                self.assertFalse(gate["feasibility_pass"])
        cells["perception_seed2_NO_PARENT"]["PROCESS_USE"] = 10
        self.assertTrue(core.threshold_vector(cells)["feasibility_pass"])
        cells["perception_seed2_SWAPPED"]["PROCESS_USE"] = 11
        self.assertTrue(core.threshold_vector(cells)["feasibility_pass"])

    def test_positive_fixture_gate_does_not_authorize_writer_and_incomplete_is_pending(self):
        captures = [self.capture(seed, arm, mode="following_note")[0] for seed in range(3) for arm in core.ARMS]
        result = core.summarize(captures, self.deps)
        self.assertTrue(result["gate"]["feasibility_pass"])
        self.assertFalse(result["automatic_pass"])
        self.assertFalse(result["fit_authorized"])
        self.assertEqual(result["updates"], 0)
        self.assertFalse(core.summarize(captures[:3], self.deps)["gate"]["complete"])
        with self.assertRaises(ValueError):
            core.summarize([captures[0], captures[0]], self.deps)

    def test_strict_json_and_original_binding_only(self):
        for raw in ('{"note":{},"note":{}}', '{"note":NaN}', '```json\n{}\n```'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                core.decode(raw)
        expected = core.root_binding(0)
        producer = {key: expected[key] for key in ("learner_seed", "parent_plan_sha256", "adapter")}
        producer["adapter_files"] = {"adapter_model.safetensors": expected["adapter_model_sha256"]}
        capture = core.run_state(core.STATES[0], Fixture(), dependencies=self.deps, binding=dict(producer=producer))
        self.assertTrue(core.audit_capture(capture, dependencies=self.deps)["consistent"])
        producer["adapter"] += "_DESCENDANT"
        with self.assertRaises(ValueError):
            core.run_state(core.STATES[0], Fixture(), dependencies=self.deps, binding=dict(producer=producer))


if __name__ == "__main__":
    unittest.main(verbosity=2)
