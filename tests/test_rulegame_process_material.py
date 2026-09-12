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


if __name__ == "__main__":
    unittest.main()
