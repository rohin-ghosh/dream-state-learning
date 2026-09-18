"""CPU-only scripted captures; no model evidence or semantic certification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_process_material as material
from organism_v6 import train_adapter_v3 as trainer
from test_rulegame_parenting_diagnostic import ScriptedBackend, Tokenizer as BaseTokenizer


class Tokenizer(BaseTokenizer):
    eos_token_id = 0
    pad_token_id = 0

    def encode(self, text, **kwargs):
        return super().encode(text)


class Backend(ScriptedBackend):
    def __init__(self, change=None):
        super().__init__(dict(backend="cpu_fixture", model_input="fixture-only", adapter_files={}))
        self.tokenizer = Tokenizer()
        self.change = change

    def generate(self, request):
        response = super().generate(request)
        if self.change:
            response["text"] = self.change(request, response["text"])
            response["output_token_ids"] = self.tokenizer.encode(response["text"])
        return response


class ProcessMaterialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rulegame-process-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tokenizer = Tokenizer()
        self.counter = 0
        self.capture()

    def capture(self, change=None):
        self.path = self.root / str(self.counter)
        self.counter += 1
        self.path.mkdir()
        backend = Backend(change)
        calls = diagnostic.Calls(self.path / "calls", backend, "formation", backend.identity(), "interaction_v3")
        events = diagnostic.Events(self.path / "events.jsonl")
        result = diagnostic.run_formation(calls, events)
        diagnostic.write_json(self.path / "identity.json", dict(stage="formation", protocol="interaction_v3",
            backend=backend.identity(), model_files={"config.fixture": "a" * 64}))
        diagnostic.write_json(self.path / "result.json", result)
        diagnostic.write_json(self.path / "usage.json", diagnostic.usage(self.path))
        diagnostic.capture_manifest(self.path)
        self.candidate = material.inspect_capture(self.path)
        self.review = material.review_template(self.candidate)
        self.review["context_distillation_acknowledged"] = True
        for review in self.review["reviews"]:
            review.update(decision="accept", notes="CPU Main-review fixture, not semantic evidence.")

    def build(self, **kwargs):
        return material.build_process_pair(self.path, kwargs.pop("main_review", self.review),
            kwargs.pop("tokenizer", self.tokenizer), **kwargs)

    def overwrite(self, path, value):
        path.write_bytes(diagnostic.encoded(value))

    def reseal(self):
        self.overwrite(self.path / "usage.json", diagnostic.usage(self.path))
        self.overwrite(self.path / "manifest.json", dict(files=diagnostic.tree_hashes(self.path, ("manifest.json",))))

    def change_receipt(self, kind, change):
        call_id = self.candidate["candidates"][0]["selected"]["call_id"]
        path = self.path / f"calls/{call_id}.{kind}.json"
        value = diagnostic.read(path)
        change(value[kind])
        value["prompt_sha256" if kind == "request" else "response_sha256"] = diagnostic.value_hash(
            value[kind]["prompt"] if kind == "request" else value[kind])
        self.overwrite(path, value)
        self.reseal()

    def test_fixed_second_executed_try_four_slots(self):
        self.assertEqual(self.candidate["status"], "AVAILABLE_PENDING_MAIN_REVIEW")
        self.assertEqual([row["slot_id"] for row in self.candidate["candidates"]],
            ["P:lesson0", "P:lesson1", "A:lesson0", "A:lesson1"])
        for row in self.candidate["candidates"]:
            self.assertEqual(row["selected"]["tick"], 2)
            self.assertEqual(len(row["preceding_public_history"]), 1)
        self.assertNotIn("corpus", self.candidate)

    def test_selection_ignores_correctness_records_and_predictions(self):
        events = diagnostic.check_capture(self.path)["events"]
        original = material.select_slots(events)
        for event in events:
            event.update(predicted=None, prediction_ambiguous=True, correct=False, observed=False, raw_response="garbage")
        self.assertEqual(material.select_slots(events), original)

    def test_missing_prediction_blocks_pair_without_later_replacement(self):
        self.capture(lambda request, text: text.replace("PREDICT: T\n", "")
            if request["role"] == "wake" and request["tick"] == 2 and "/apply" in request["eid"] else text)
        self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all(row["selected"]["tick"] == 2 for row in self.candidate["candidates"]))
        with self.assertRaisesRegex(ValueError, "paired shortage"):
            self.build()

    def test_alias_is_executed_but_missing_literal_act_is_shortage(self):
        self.capture(lambda request, text: text.replace("ACT: TRY", "TRY:")
            if request["role"] == "wake" and request["tick"] == 2 else text)
        self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all("missing canonical ACT" in row["failures"] for row in self.candidate["candidates"]))

    def test_early_reveal_no_candidate_no_replacement(self):
        self.capture(lambda request, text: "ACT: QUIZ ?" if request["role"] == "wake" and request["tick"] == 2 else text)
        self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all(row["selected"] is None for row in self.candidate["candidates"]))

    def test_protocol_invalid_stops_before_candidate(self):
        self.capture(lambda request, text: text + "\nACT: TRY 1,1,1"
            if request["role"] == "wake" and request["tick"] == 2 else text)
        self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all(row["stopped_before_slot"] for row in self.candidate["candidates"]))

    def test_prediction_and_action_validation(self):
        invalid = ["ACT: TRY 1,2,3", "ACT: TRY 1,2,3\nPREDICT: T",
            "PREDICT: yes\nACT: TRY 1,2,3", "PREDICT: T\nPREDICT: T\nACT: TRY 1,2,3",
            "PREDICT: T\nACT: TRY 1,2,3\nPREDICT: F", "PREDICT: T\nACT: TRY 1,2,3\nACT: TRY 4,5,6",
            "PREDICT: T\nTRY: 1,2,3", "PREDICT: T\nACT: QUIZ ?", " PREDICT: T\nACT: TRY 1,2,3",
            "PREDICT: T or F\nACT: TRY 1,2,3", "PREDICT T\nACT: TRY 1,2,3"]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                material.validate_wake(text)
        self.assertFalse(material.validate_wake("Thought.\nPREDICT: F\nACT: TRY -1,2,3\n")["predicted"])

    def test_wrong_prediction_unchanged_raw_whitespace(self):
        self.capture(lambda request, text: "\n " + "Own reasoning.\n" + text + "\t\n"
            if request["role"] == "wake" and request["tick"] == 2 else text)
        result = self.build()
        for row in self.candidate["candidates"]:
            item = result["corpora"][row["arm"]]["corpus"][row["lesson"]]
            self.assertEqual(item["spans"][1][0], row["target"])
            self.assertTrue(row["target"].startswith("\n ") and row["target"].endswith("\t\n"))
        executions = [row["source"]["execution"] for row in self.candidate["candidates"]]
        self.assertTrue(any(row["predicted"] != row["observed"] for row in executions))

    def test_exact_interval_utf8_and_prior_public_history_only(self):
        self.capture(lambda request, text: "A résumé of this activity is available." if request["role"] == "restate" else text)
        for row in self.candidate["candidates"]:
            source = row["source"]["request_receipt"]["request"]["prompt"].encode()
            interval = row["removed_intervals"][0]
            start, end = interval["start_byte"], interval["end_byte"]
            self.assertEqual((source[:start] + source[end:]).decode(), row["context"])
            self.assertIn("résumé", source[start:end].decode())
            prior = row["preceding_public_history"][0]
            self.assertIn(prior["raw_wake"] + "\n[OUTCOME] " + prior["outcome"], row["context"])
            self.assertEqual(row["context"].count("[OUTCOME] " + prior["outcome"]), 1)
            self.assertNotIn("Temporary parent restatement", row["context"])
            self.assertNotIn("RECORD", row["context"])

    def test_source_reconstruction_rejects_added_future_or_changed_state(self):
        row = self.candidate["candidates"][0]
        source = row["source"]["request_receipt"]["request"]["prompt"]
        restatement = self.candidate["teacher_sources_audit_only"][1]["raw_text"]
        for prompt in (source + "\nfuture answer T", source.replace("remaining TRY budget: 2", "remaining TRY budget: 1")):
            with self.subTest(prompt=prompt[-60:]), self.assertRaisesRegex(ValueError, "reconstruct"):
                material.transform_context(prompt, row, restatement, row["preceding_public_history"])

    def test_literal_teacher_echo_rejected_in_target_and_history(self):
        for tick in (1, 2):
            with self.subTest(tick=tick):
                self.capture(lambda request, text: "Compare predictions with observations.\n" + text
                    if request["role"] == "wake" and request["tick"] == tick else text)
                self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
                self.assertTrue(all(any("copied parent/restatement" in error for error in row["failures"])
                    for row in self.candidate["candidates"]))

    def test_semantic_influence_not_blanket_rejected(self):
        self.capture(lambda request, text: "My next probe tests the conjecture against evidence.\n" + text
            if request["role"] == "wake" and request["tick"] == 2 else text)
        self.assertEqual(self.candidate["status"], "AVAILABLE_PENDING_MAIN_REVIEW")
        self.assertFalse(self.build()["audit"]["semantic_certification"])

    def test_main_review_must_bind_all_four_rows(self):
        variants = [None, {}, material.review_template(self.candidate)]
        for field, value in (("candidate_sha256", "stale"), ("actor", "someone else"),
                ("scope", "only targets"), ("context_distillation_acknowledged", False)):
            review = copy.deepcopy(self.review)
            review[field] = value
            variants.append(review)
        for field, value in (("decision", "reject"), ("notes", ""), ("call_id", "9999")):
            review = copy.deepcopy(self.review)
            review["reviews"][0][field] = value
            variants.append(review)
        review = copy.deepcopy(self.review)
        review["reviews"].pop()
        variants.append(review)
        review = copy.deepcopy(self.review)
        review["reviews"][0] = None
        variants.append(review)
        for review in variants:
            with self.subTest(review=review), self.assertRaises(ValueError):
                self.build(main_review=review)

    def test_stale_fixed_candidate_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        candidate["candidates"][0]["target"] += "extra"
        with self.assertRaisesRegex(ValueError, "fixed candidate changed"):
            self.build(fixed_candidate=candidate)

    def test_manifest_tampering_rejected(self):
        path = self.path / "calls/0001.request.json"
        path.write_text(path.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "replay"):
            material.inspect_capture(self.path)

    def test_request_join_tampering_rejected_even_resealed(self):
        self.change_receipt("request", lambda row: row.update(tick=3))
        with self.assertRaises(ValueError):
            material.inspect_capture(self.path)

    def test_orphan_event_rejected_even_resealed(self):
        with (self.path / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(dict(kind="execution", call_id="9999")) + "\n")
        self.reseal()
        with self.assertRaises(ValueError):
            material.inspect_capture(self.path)

    def test_native_rendering_input_and_output_ids_fail_separately(self):
        for field in ("rendered_prompt", "prompt_token_ids", "output_token_ids"):
            with self.subTest(field=field):
                self.capture()
                value = "not original" if field == "rendered_prompt" else [999]
                self.change_receipt("response", lambda row: row.update({field: value}))
                try:
                    candidate = material.inspect_capture(self.path)
                except ValueError:
                    continue
                self.review["candidate_sha256"] = candidate["candidate_sha256"]
                with self.assertRaises(ValueError):
                    self.build()

    def test_old_protocol_missing_model_or_adapter_inventory_rejected(self):
        original = diagnostic.read(self.path / "identity.json")
        for mutate in (lambda row: row.update(protocol="interaction_v2"), lambda row: row.update(model_files={}),
                       lambda row: row["backend"].pop("adapter_files")):
            with self.subTest(mutate=mutate):
                header = copy.deepcopy(original)
                mutate(header)
                self.overwrite(self.path / "identity.json", header)
                self.reseal()
                with self.assertRaises(ValueError):
                    material.inspect_capture(self.path)

    def test_full_token_ids_masks_offsets_eos_distinct_receipts(self):
        result = self.build(fixed_candidate=self.candidate)
        for arm in diagnostic.ARMS:
            self.assertEqual(len(trainer.normalize_items(result["corpora"][arm])), 2)
            for receipt in result["audit"]["receipts"][arm]:
                native, new = receipt["original_native_capture"], receipt["transformed_training"]
                prefix, target = new["context_token_ids"], new["target_with_eos"]
                self.assertNotEqual(native["prompt_token_ids"], prefix)
                self.assertEqual(new["input_ids"], prefix + target)
                self.assertEqual(new["labels"], [-100] * len(prefix) + target)
                self.assertEqual(new["first_target_predictor"], len(prefix) - 1)
                self.assertEqual(new["predictor_positions"], list(range(len(prefix) - 1, len(prefix + target) - 1)))
                self.assertEqual(target[-1], self.tokenizer.eos_token_id)
                self.assertEqual(target.count(self.tokenizer.eos_token_id), 1)
                self.assertFalse(receipt["same_conditioning_as_native"])
                self.assertFalse(new["source_output_token_ids_reused_as_targets"])

    def test_no_packing_truncation_splitting_or_drops(self):
        for max_len in (0, True, 2, diagnostic.MAX_MODEL_LEN + 1):
            with self.subTest(max_len=max_len), self.assertRaises(ValueError):
                self.build(max_len=max_len)
        original = trainer.encode_item_segments
        def split(*args, **kwargs):
            result = original(*args, **kwargs)
            return result + result
        with patch.object(trainer, "encode_item_segments", side_effect=split), self.assertRaisesRegex(ValueError, "dropped/split"):
            self.build()

    def test_mask_shift_rejected(self):
        original = trainer.collate
        def shifted(*args, **kwargs):
            batch = original(*args, **kwargs)
            batch["labels"][0] = batch["labels"][0][1:] + [-100]
            return batch
        with patch.object(trainer, "collate", side_effect=shifted), self.assertRaisesRegex(ValueError, "mask/offset"):
            self.build()

    def test_eos_in_raw_target_rejected(self):
        tokenizer = Tokenizer()
        tokenizer.eos_token_id = ord("P") + 1
        with self.assertRaisesRegex(ValueError, "EOS already"):
            self.build(tokenizer=tokenizer)

    def test_source_mutation_during_callback_rejected(self):
        original = diagnostic.audit_native_calls
        def mutate(tokenizer, path):
            original(tokenizer, path)
            (path / "unexpected.txt").write_text("changed")
        with patch.object(diagnostic, "audit_native_calls", side_effect=mutate), self.assertRaises(ValueError):
            self.build()

    def test_main_review_snapshot_not_mutated_by_callback(self):
        original = diagnostic.audit_native_calls
        before = copy.deepcopy(self.review)
        def mutate(tokenizer, path):
            original(tokenizer, path)
            self.review["reviews"][0]["decision"] = "changed external object"
        with patch.object(diagnostic, "audit_native_calls", side_effect=mutate):
            result = self.build()
        self.assertEqual(result["audit"]["main_review"], before)

    def test_plan_identity_and_seal_bound_if_present(self):
        plan_path = self.path.parents[1] / "plan.json"
        with tempfile.TemporaryDirectory(prefix="process-plan-test-") as temporary:
            destination = Path(temporary) / "formation"
            destination.mkdir()
            self.path.rename(destination / "data")
            self.path = destination / "data"
            plan_path = Path(temporary) / "plan.json"
            header = diagnostic.read(self.path / "identity.json")
            plan = dict(protocol="interaction_v3", model=header["backend"]["model_input"],
                model_files=header["model_files"], source_hashes={"fixture.py": "b" * 64})
            diagnostic.write_json(plan_path, plan)
            seal = plan_path.with_name("plan.sha256.json")
            diagnostic.write_json(seal, dict(sha256=diagnostic.digest(plan_path)))
            candidate = material.inspect_capture(self.path)
            self.assertEqual(candidate["source_binding"]["source_plan"]["sha256"], diagnostic.digest(plan_path))
            plan["model"] = "different base"
            self.overwrite(plan_path, plan)
            with self.assertRaisesRegex(ValueError, "plan/identity"):
                material.inspect_capture(self.path)
            self.overwrite(seal, dict(sha256=diagnostic.digest(plan_path)))
            with self.assertRaisesRegex(ValueError, "plan/identity"):
                material.inspect_capture(self.path)

    def test_new_rendered_teacher_copy_rejected(self):
        row = self.candidate["candidates"][0]
        tokenizer = Tokenizer()
        original = tokenizer.apply_chat_template
        def render(messages, **kwargs):
            text = original(messages, **kwargs)
            return text + "Compare predictions with observations." if messages[0]["content"] == row["context"] else text
        tokenizer.apply_chat_template = render
        with self.assertRaisesRegex(ValueError, "new rendered training input"):
            self.build(tokenizer=tokenizer)

    def test_export_atomic_pair_hashes_and_separate_audit(self):
        before = diagnostic.tree_hashes(self.path)
        destination = self.root / "export"
        manifest = material.export_pair(self.path, destination, self.review, self.tokenizer)
        self.assertEqual(manifest["files"], diagnostic.tree_hashes(destination, ("manifest.json",)))
        self.assertEqual(set(manifest["corpus_files"]), {"P", "A"})
        self.assertEqual(before, diagnostic.tree_hashes(self.path))
        self.assertEqual(len(list((destination / "corpora").iterdir())), 2)
        self.assertTrue((destination / "audit/candidate.json").is_file())
        for name in manifest["corpus_files"].values():
            self.assertEqual(set(diagnostic.read(destination / name)), {"corpus"})
        with self.assertRaisesRegex(ValueError, "fresh"):
            material.export_pair(self.path, destination, self.review, self.tokenizer)

    def test_output_source_overlap_symlink_and_existing_empty_rejected(self):
        empty = self.root / "empty"
        empty.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(empty)
        for destination in (self.path, self.path / "child", self.root, empty, alias):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                material.export_pair(self.path, destination, self.review, self.tokenizer)

    def test_failed_staging_preserved_no_automatic_retry(self):
        destination = self.root / "export"
        with patch.object(material, "_publish", side_effect=RuntimeError("interrupted")), self.assertRaises(RuntimeError):
            material.export_pair(self.path, destination, self.review, self.tokenizer)
        self.assertFalse(destination.exists())
        self.assertTrue((self.root / ".export.pending/corpora/P.json").is_file())
        with self.assertRaisesRegex(ValueError, "fresh"):
            material.export_pair(self.path, destination, self.review, self.tokenizer)

    def test_source_changed_before_publication_preserves_pending_pair(self):
        original = diagnostic.write_json
        destination = self.root / "export"
        def mutate(path, value):
            original(path, value)
            if Path(path).name == "manifest.json":
                (self.path / "unexpected.txt").write_text("source changed")
        with patch.object(diagnostic, "write_json", side_effect=mutate), self.assertRaises(ValueError):
            material.export_pair(self.path, destination, self.review, self.tokenizer)
        self.assertFalse(destination.exists())
        self.assertTrue((self.root / ".export.pending/corpora/A.json").exists())

    def test_racing_empty_destination_never_replaced(self):
        staging, destination = self.root / "staging", self.root / "racer"
        staging.mkdir()
        (staging / "retained").write_text("preserve")
        destination.mkdir()
        with self.assertRaises(FileExistsError):
            material._publish(staging, destination)
        self.assertTrue((staging / "retained").is_file())
        self.assertEqual(list(destination.iterdir()), [])

    def test_shortage_export_writes_nothing(self):
        self.capture(lambda request, text: text.replace("PREDICT: T\n", "")
            if request["role"] == "wake" and request["tick"] == 2 else text)
        destination = self.root / "export"
        with self.assertRaisesRegex(ValueError, "shortage"):
            material.export_pair(self.path, destination, self.review, self.tokenizer)
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / ".export.pending").exists())

    def v2_candidate_review(self):
        candidate = material.inspect_capture(self.path, protocol=material.PROTOCOL_V2)
        review = material.review_template(candidate, protocol=material.PROTOCOL_V2)
        review["context_distillation_acknowledged"] = True
        for row in review["reviews"]:
            row.update(decision="accept", notes="Exploratory V2 CPU Main-review fixture, not semantic evidence.")
        return candidate, review

    def test_v2_explicit_native_alias_acceptance_v1_still_rejects(self):
        for action in ("ACT: TRY -1,2,3", "TRY: -1,2,3"):
            text = "Reasoning.\nPREDICT: F\n" + action + "\n"
            with self.subTest(action=action):
                self.assertEqual(material.validate_wake(text, protocol=material.PROTOCOL_V2),
                    diagnostic.parse_action(text, "interaction_v3"))
        with self.assertRaisesRegex(ValueError, "missing canonical ACT"):
            material.validate_wake("PREDICT: F\nTRY: -1,2,3")

    def test_v2_prediction_before_actual_alias_not_later_or_ambiguous(self):
        invalid = ["TRY: 1,2,3\nPREDICT: T", "TRY: 1,2,3", "PREDICT: T\nTRY: 1,2,3\nPREDICT: F",
            "PREDICT: T\nPREDICT: T\nTRY: 1,2,3", "PREDICT: T or F\nTRY: 1,2,3",
            "PREDICT T\nTRY: 1,2,3", " PREDICT: T\nTRY: 1,2,3", "PREDICT: yes\nTRY: 1,2,3"]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                material.validate_wake(text, protocol=material.PROTOCOL_V2)

    def test_v2_sole_native_marker_rejects_mixed_extra_malformed_actions(self):
        invalid = ["TRY: 1,2,3\nACT: TRY 4,5,6", "ACT: TRY 1,2,3\nTRY: 4,5,6",
            "TRY: 1,2,3\nTRY: 4,5,6", "TRY: 1,2,3\nQUIZ: ?", "TRY: 1,2,3\nDONE",
            "TRY: 1,2,3\n[OUTCOME] T", "TRY: 1,2,3\nTRY 4,5,6", " try: 1,2,3",
            " TRY: 1,2,3", "TRY:1,2,3", "ACT:TRY 1,2,3", "QUIZ: ?", "TRY: 1,2,3,4"]
        for action in invalid:
            with self.subTest(action=action), self.assertRaises(ValueError):
                material.validate_wake("PREDICT: T\n" + action, protocol=material.PROTOCOL_V2)

    def test_v2_same_slots_sources_intervals_no_canonicalization(self):
        self.capture(lambda request, text: "\nThought.\n" + text.replace("ACT: TRY", "TRY:") + "\t\n"
            if request["role"] == "wake" and request["tick"] == 2 else text)
        before = diagnostic.tree_hashes(self.path)
        candidate, review = self.v2_candidate_review()
        self.assertEqual(self.candidate["status"], "PAIRED_SHORTAGE")
        self.assertEqual(candidate["status"], "AVAILABLE_PENDING_MAIN_REVIEW")
        self.assertEqual(candidate["selection_sha256"], self.candidate["selection_sha256"])
        self.assertEqual(candidate["fixed_slots"], self.candidate["fixed_slots"])
        self.assertNotEqual(candidate["candidate_sha256"], self.candidate["candidate_sha256"])
        for old, new in zip(self.candidate["candidates"], candidate["candidates"], strict=True):
            for field in ("source", "target", "context", "removed_intervals", "preceding_public_history"):
                self.assertEqual(old[field], new[field])
        result = material.build_process_pair(self.path, review, self.tokenizer,
            fixed_candidate=candidate, protocol=material.PROTOCOL_V2)
        for row in candidate["candidates"]:
            item = result["corpora"][row["arm"]]["corpus"][row["lesson"]]
            receipt = result["audit"]["receipts"][row["arm"]][row["lesson"]]
            self.assertEqual(item["spans"][1][0], row["target"])
            self.assertIn("\nTRY: ", item["spans"][1][0])
            self.assertNotIn("ACT:", item["spans"][1][0])
            self.assertEqual(item["view"], material.PROTOCOL_V2)
            self.assertEqual(item["meta"]["protocol"], material.PROTOCOL_V2)
            self.assertEqual(receipt["transformed_training"]["raw_target_token_ids"], self.tokenizer.encode(row["target"]))
            self.assertEqual(receipt["original_native_capture"]["raw_text"], row["target"])
        self.assertEqual(diagnostic.tree_hashes(self.path), before)

    def test_v2_bad_fixed_alias_prediction_never_replaced_by_valid_tick3(self):
        self.capture(lambda request, text: "TRY: 0,0,0\nPREDICT: T"
            if request["role"] == "wake" and request["tick"] == 2 else text)
        candidate, review = self.v2_candidate_review()
        self.assertEqual(candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all(row["selected"]["tick"] == 2 for row in candidate["candidates"]))
        with self.assertRaisesRegex(ValueError, "paired shortage"):
            material.build_process_pair(self.path, review, self.tokenizer, protocol=material.PROTOCOL_V2)

    def test_v2_still_rejects_literal_teacher_echo(self):
        self.capture(lambda request, text: "Compare predictions with observations.\n" + text.replace("ACT: TRY", "TRY:")
            if request["role"] == "wake" and request["tick"] == 2 else text)
        candidate, review = self.v2_candidate_review()
        self.assertEqual(candidate["status"], "PAIRED_SHORTAGE")
        self.assertTrue(all(any("copied parent/restatement" in failure for failure in row["failures"])
            for row in candidate["candidates"]))
        with self.assertRaisesRegex(ValueError, "paired shortage"):
            material.build_process_pair(self.path, review, self.tokenizer, protocol=material.PROTOCOL_V2)

    def test_v2_review_requires_explicit_matching_policy(self):
        candidate, review = self.v2_candidate_review()
        with self.assertRaisesRegex(ValueError, "protocol/policy"):
            material.review_template(candidate)
        with self.assertRaisesRegex(ValueError, "protocol/policy"):
            material.review_template(self.candidate, protocol=material.PROTOCOL_V2)
        stale = copy.deepcopy(candidate)
        stale["policy"] = self.candidate["policy"]
        with self.assertRaisesRegex(ValueError, "protocol/policy"):
            material.review_template(stale, protocol=material.PROTOCOL_V2)
        self.assertEqual(review["protocol"], material.PROTOCOL_V2)
        self.assertTrue(candidate["policy"]["after_inventory_exploratory"])
        self.assertIn("96a71289", candidate["policy"]["decision"])
        self.assertEqual(candidate["policy"]["prior_protocol"], material.PROTOCOL)

    def test_v2_cannot_reuse_v1_review_or_candidate_even_canonical(self):
        candidate, review = self.v2_candidate_review()
        with self.assertRaisesRegex(ValueError, "bound Main"):
            material.build_process_pair(self.path, self.review, self.tokenizer, protocol=material.PROTOCOL_V2)
        with self.assertRaisesRegex(ValueError, "bound Main"):
            material.build_process_pair(self.path, review, self.tokenizer)
        for supplied, protocol, actual_review in ((self.candidate, material.PROTOCOL_V2, review),
                (candidate, material.PROTOCOL, self.review)):
            with self.subTest(protocol=protocol), self.assertRaisesRegex(ValueError, "fixed candidate changed"):
                material.build_process_pair(self.path, actual_review, self.tokenizer, fixed_candidate=supplied, protocol=protocol)

    def test_v2_resealed_stale_policy_candidate_fails_build(self):
        candidate, review = self.v2_candidate_review()
        candidate["policy"]["after_inventory_exploratory"] = False
        candidate.pop("candidate_sha256")
        candidate["candidate_sha256"] = diagnostic.value_hash(candidate)
        review["candidate_sha256"] = candidate["candidate_sha256"]
        with self.assertRaisesRegex(ValueError, "fixed candidate changed"):
            material.build_process_pair(self.path, review, self.tokenizer, fixed_candidate=candidate, protocol=material.PROTOCOL_V2)

    def test_v2_atomic_export_namespace_and_no_v1_relabel_or_overwrite(self):
        candidate, review = self.v2_candidate_review()
        destination = self.root / "v2-export"
        manifest = material.export_pair(self.path, destination, review, self.tokenizer,
            fixed_candidate=candidate, protocol=material.PROTOCOL_V2)
        self.assertEqual(manifest["protocol"], material.PROTOCOL_V2)
        self.assertEqual(manifest["candidate_sha256"], candidate["candidate_sha256"])
        self.assertEqual(diagnostic.read(destination / "audit/candidate.json")["policy"], material.POLICY_V2)
        self.assertEqual(diagnostic.read(destination / "audit/main_review.json")["protocol"], material.PROTOCOL_V2)
        self.assertEqual(manifest["files"], diagnostic.tree_hashes(destination, ("manifest.json",)))
        for arm in diagnostic.ARMS:
            for item in diagnostic.read(destination / manifest["corpus_files"][arm])["corpus"]:
                self.assertEqual(item["meta"]["protocol"], material.PROTOCOL_V2)
        with self.assertRaisesRegex(ValueError, "fresh"):
            material.export_pair(self.path, destination, self.review, self.tokenizer)
        with self.assertRaisesRegex(ValueError, "bound Main"):
            material.export_pair(self.path, self.root / "not-v1", review, self.tokenizer)
        self.assertFalse((self.root / "not-v1").exists())

    def test_unknown_protocol_fails_closed(self):
        for protocol in (None, "interaction_v3", "rulegame_grounded_process_pair_v3", []):
            with self.subTest(protocol=protocol):
                for callback in (
                    lambda: material.validate_wake("PREDICT: T\nTRY: 1,2,3", protocol=protocol),
                    lambda: material.inspect_capture(self.path, protocol=protocol),
                    lambda: material.review_template(self.candidate, protocol=protocol),
                    lambda: material.build_process_pair(self.path, self.review, self.tokenizer, protocol=protocol),
                    lambda: material.export_pair(self.path, self.root / "unknown", self.review, self.tokenizer, protocol=protocol)):
                    with self.assertRaisesRegex(ValueError, "unknown process"):
                        callback()
        self.assertFalse((self.root / "unknown").exists())

    def test_v2_does_not_bypass_source_execution_join(self):
        self.change_receipt("request", lambda row: row.update(tick=3))
        with self.assertRaises(ValueError):
            material.inspect_capture(self.path, protocol=material.PROTOCOL_V2)


if __name__ == "__main__":
    unittest.main()
