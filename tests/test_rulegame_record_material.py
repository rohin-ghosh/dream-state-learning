"""CPU-only actual capture/replay/V3 fixtures; no model or native evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_rulegame_parenting_diagnostic as fixtures
from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_record_material as material
from organism_v6 import train_adapter_v3 as trainer


LESSON = "Notice surprising observations. Compare outcomes using a varied probe."


class Tokenizer(fixtures.Tokenizer):
    eos_token_id = 999999

    def __init__(self, rendered_echo=""):
        self.rendered_echo = rendered_echo

    def encode(self, text, **kwargs):
        return super().encode(text)

    def apply_chat_template(self, messages, **kwargs):
        prefix = self.rendered_echo if "Actual emitted output:\n" in messages[0]["content"] else ""
        return prefix + super().apply_chat_template(messages, **kwargs)


class Backend(fixtures.ScriptedBackend):
    def __init__(self, *, tokenizer, echo="", echo_arm="P", prediction="T", bad_relation=False,
                 parent_text=LESSON, restatement=None, bad_records=()):
        super().__init__({"fixture": "scripted CPU only; not authenticated"},
                         parent_text=parent_text, bad_records=bad_records)
        self.tokenizer = tokenizer
        self.echo, self.echo_arm, self.prediction = echo, echo_arm, prediction
        self.bad_relation, self.restatement = bad_relation, restatement

    def generate(self, request):
        response = super().generate(request)
        text = response["text"]
        if request["role"] == "wake" and request["tick"] <= 3:
            prediction = "" if self.prediction is None else "PREDICT: " + self.prediction + "\n"
            text = prediction + "ACT: TRY 0,0,0"
            if request["eid"].endswith("/apply") and request["arm"] == self.echo_arm and request["tick"] == 1:
                text = self.echo + "\n" + text if self.echo else text
        elif request["role"] == "restate" and self.restatement is not None:
            text = self.restatement
        elif request["role"] == "record":
            if self.bad_relation:
                text = text.replace('"relation":"matched"', '"relation":"unavailable"').replace(
                    '"relation":"mismatched"', '"relation":"unavailable"')
            text = "\n " + text + "\t\n"
        response.update(text=text, output_token_ids=self.tokenizer.encode(text))
        return response


class RecordMaterialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rulegame-record-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.capture_count = 0
        self.capture()

    def capture(self, protocol="interaction_v2", **kwargs):
        self.path = self.root / str(self.capture_count)
        self.capture_count += 1
        self.path.mkdir()
        self.tokenizer = kwargs.pop("tokenizer", Tokenizer())
        backend = Backend(tokenizer=self.tokenizer, **kwargs)
        calls = diagnostic.Calls(self.path / "calls", backend, "formation", backend.identity(), protocol)
        events = diagnostic.Events(self.path / "events.jsonl")
        result = diagnostic.run_formation(calls, events)
        diagnostic.write_json(self.path / "identity.json", dict(stage="formation", backend=backend.identity(), protocol=protocol))
        diagnostic.write_json(self.path / "result.json", result)
        diagnostic.write_json(self.path / "usage.json", diagnostic.usage(self.path))
        diagnostic.capture_manifest(self.path)
        self.bind()

    def bind(self):
        self.replay = diagnostic.check_capture(self.path)
        self.assertTrue(self.replay["ok"], self.replay)
        self.selection = diagnostic.select_records(self.replay)
        self.bind_main()

    def bind_main(self):
        self.decision = diagnostic.audit_template(self.path)
        self.decision.update(provenance_decision="accept", provenance_notes="Mock Main provenance assessment only.")
        for review in self.decision["reviews"]:
            review.update(decision="accept", notes="Mock Main semantic assessment, not machine certification.")
        self.decision["record_review"] = dict(decision="accept", scope="actual_record_context_and_target",
            notes="Mock Main read raw/rendered contexts and raw targets; no lesson prose or added future answers.",
            selection_sha256=diagnostic.value_hash(self.selection))

    def export(self, **kwargs):
        return material.build_record_pair(self.path, kwargs.pop("main_audit", self.decision),
            kwargs.pop("fixed_selection", self.selection), kwargs.pop("tokenizer", self.tokenizer),
            replay_verified_capture=kwargs.pop("replay_verified_capture", self.replay), **kwargs)

    def overwrite(self, name, value):
        (self.path / name).write_bytes(diagnostic.encoded(value))

    def reseal(self):
        self.overwrite("usage.json", diagnostic.usage(self.path))
        self.overwrite("manifest.json", {"files": diagnostic.tree_hashes(self.path, ("manifest.json",))})

    def mutate_call(self, call_id, kind, change):
        name = f"calls/{call_id}.{kind}.json"
        receipt = diagnostic.read(self.path / name)
        change(receipt)
        if kind == "request":
            receipt["prompt_sha256"] = diagnostic.value_hash(receipt["request"]["prompt"])
        else:
            receipt["response_sha256"] = diagnostic.value_hash(receipt["response"])
        self.overwrite(name, receipt)
        self.reseal()

    def test_accepted_pair_actual_v3_roundtrip_preserves_raw_bytes_and_sources(self):
        before = diagnostic.tree_hashes(self.path)
        inputs = copy.deepcopy((self.replay, self.selection, self.decision))
        result = self.export()
        self.assertEqual(set(result["corpora"]), {"P", "A"})
        self.assertFalse(result["semantic_no_answer_certification"])
        self.assertFalse(result["model_authentication_certified"])
        for arm in diagnostic.ARMS:
            corpus = trainer.normalize_items(result["corpora"][arm])
            self.assertEqual(len(corpus), 2)
            for ordinal, item in enumerate(corpus):
                row = self.selection["selected"][arm][ordinal]
                request = diagnostic.read(self.path / f"calls/{row['call_id']}.request.json")["request"]
                response = diagnostic.read(self.path / f"calls/{row['call_id']}.response.json")["response"]
                raw = response["text"]
                self.assertEqual(item["spans"], [[response["rendered_prompt"], False, "record_context"],
                                               [raw, True, "own_raw_record"]])
                self.assertTrue(raw.startswith("\n ") and raw.endswith("\t\n"))
                self.assertNotEqual(raw, json.dumps(json.loads(raw)))
                self.assertIn("Actual emitted output:\n", request["prompt"])
                self.assertIn("Actual world response:\n", request["prompt"])
                self.assertNotIn("Temporary parent restatement", item["spans"][0][0])
                self.assertNotIn("Situation ", item["spans"][0][0])
                context_ids = self.tokenizer.encode(item["spans"][0][0])
                target_ids = self.tokenizer.encode(raw) + [self.tokenizer.eos_token_id]
                packs = trainer.encode_item_segments(item, self.tokenizer, 4096, chat_template=False, add_eos=True)
                batch = trainer.collate([packs], self.tokenizer.eos_token_id)
                self.assertEqual(batch["input_ids"][0], context_ids + target_ids)
                self.assertEqual(batch["labels"][0], [-100] * len(context_ids) + target_ids)
                self.assertEqual(batch["labels"][0][len(context_ids):], target_ids)
                self.assertEqual(batch["labels"][0].count(self.tokenizer.eos_token_id), 1)
                source = result["source_receipts"][arm][ordinal]
                self.assertEqual(source["selection_ordinal"], ordinal)
                self.assertLess(source["execution_event_index"], source["record_event_index"])
                self.assertEqual(source["encoding"]["first_target_predictor"], len(context_ids) - 1)
                for name, digest in source["files"].items():
                    self.assertEqual(diagnostic.digest(self.path / name), digest)
        self.assertEqual(diagnostic.tree_hashes(self.path), before)
        self.assertEqual((self.replay, self.selection, self.decision), inputs)

    def test_strict_v1_capture_remains_supported_without_renderer_change(self):
        self.capture(protocol="strict_v1")
        self.assertEqual(len(self.export()["corpora"]["P"]["corpus"]), 2)

    def test_replay_evidence_cannot_be_asserted_or_type_forged(self):
        for proof in ({"ok": True}, {**self.replay, "ok": 1}):
            with self.subTest(proof=list(proof)), self.assertRaisesRegex(ValueError, "supplied replay evidence"):
                self.export(replay_verified_capture=proof)

    def test_wrong_record_request_context_future_answer_or_source_tick_resealed(self):
        for mode in ("wake_context", "synthetic", "future", "tick", "role", "identity", "chronology"):
            with self.subTest(mode=mode):
                self.capture()
                row = self.selection["selected"]["P"][0]
                wake = diagnostic.read(self.path / f"calls/{row['source_call_id']}.request.json")["request"]
                def change(receipt):
                    if mode == "wake_context":
                        receipt["request"]["prompt"] = wake["prompt"]
                    elif mode == "synthetic":
                        receipt["request"]["prompt"] = "Situation synthetic; My measured action record:"
                    elif mode == "future":
                        receipt["request"]["prompt"] += "\nNext gold action: TRY 1,2,3"
                    elif mode in ("tick", "role"):
                        receipt["request"][mode] = 99 if mode == "tick" else "wake"
                    elif mode == "identity":
                        receipt["identity"] = {"forged": True}
                    else:
                        receipt["started"] = -1
                self.mutate_call(row["call_id"], "request", change)
                self.bind_main()
                with self.assertRaisesRegex(ValueError, "capture replay failed"):
                    self.export()

    def test_resealed_execution_outcome_join_and_record_forgery_fail(self):
        for field, value in (("outcome", "the box says: forged"), ("call_id", "0000"),
                             ("source_call_id", "0000"), ("text", "{}")):
            with self.subTest(field=field):
                self.capture()
                rows = copy.deepcopy(self.replay["events"])
                kind = "record" if field in ("source_call_id", "text") else "execution"
                row = next(row for row in rows if row["kind"] == kind and row["eid"].endswith("/apply"))
                row[field] = value
                (self.path / "events.jsonl").write_bytes(b"".join(diagnostic.encoded(row) for row in rows))
                self.reseal()
                self.bind_main()
                with self.assertRaisesRegex(ValueError, "capture replay failed"):
                    self.export()

    def test_resealed_wake_output_and_orphan_call_fail(self):
        row = self.selection["selected"]["P"][0]
        self.mutate_call(row["source_call_id"], "response", lambda receipt: receipt["response"].update(text="ACT: TRY 9,9,9"))
        self.bind_main()
        with self.assertRaisesRegex(ValueError, "capture replay failed"):
            self.export()
        self.capture()
        self.overwrite("calls/9999.response.json", {})
        self.reseal()
        self.bind_main()
        with self.assertRaisesRegex(ValueError, "capture replay failed"):
            self.export()

    def test_capture_hash_and_main_manifest_binding_fail_closed(self):
        row = self.selection["selected"]["P"][0]
        name = f"calls/{row['call_id']}.response.json"
        (self.path / name).write_text("{}")
        with self.assertRaisesRegex(ValueError, "capture replay failed"):
            self.export()
        self.capture()
        self.decision["formation_sha256"] = "forged"
        with self.assertRaisesRegex(ValueError, "Main audit not bound"):
            self.export()

    def test_selection_reorder_replacement_or_failure_rewrite_rejected(self):
        for mode in ("reorder", "replacement", "failures"):
            with self.subTest(mode=mode):
                selection = copy.deepcopy(self.selection)
                if mode == "reorder":
                    selection["selected"]["P"].reverse()
                elif mode == "replacement":
                    later = [row for row in self.replay["events"] if row["kind"] == "record" and row["arm"] == "P"][2]
                    selection["selected"]["P"][0] = later
                else:
                    selection["failures"].append({"invented": "failure"})
                with self.assertRaisesRegex(ValueError, "fixed first-two selection changed"):
                    self.export(fixed_selection=selection)

    def test_declined_main_or_missing_semantic_review_never_exports(self):
        for mode in ("parent", "provenance", "actor", "missing", "reject", "unbound", "notes", "scope"):
            with self.subTest(mode=mode):
                decision = copy.deepcopy(self.decision)
                if mode == "parent":
                    decision["reviews"][1]["decision"] = "reject"
                elif mode == "provenance":
                    decision["provenance_decision"] = "reject"
                elif mode == "actor":
                    decision["actor"] = "automatic"
                elif mode == "missing":
                    del decision["record_review"]
                else:
                    key = {"reject": "decision", "unbound": "selection_sha256", "notes": "notes", "scope": "scope"}[mode]
                    decision["record_review"][key] = "" if mode == "notes" else "wrong"
                with self.assertRaises(ValueError):
                    self.export(main_audit=decision)

    def test_declined_seq095_like_shortage_is_not_repaired_or_seeded(self):
        self.capture(bad_records=("P",))
        self.decision["reviews"][2]["decision"] = "reject"
        with self.assertRaisesRegex(ValueError, "Main declined material"):
            self.export()
        self.decision["reviews"][2]["decision"] = "accept"
        with self.assertRaisesRegex(ValueError, "paired shortage"):
            self.export()

    def test_false_none_ambiguous_and_wrong_relation_semantics(self):
        for prediction in ("F", None):
            with self.subTest(prediction=prediction):
                self.capture(prediction=prediction)
                result = self.export()
                raw = result["corpora"]["P"]["corpus"][0]["spans"][1][0]
                record = json.loads(raw)
                self.assertIs(record["predicted"], False if prediction == "F" else None)
                row = self.selection["selected"]["P"][0]
                execution = next(event for event in self.replay["events"] if event["kind"] == "execution"
                                 and event["execution_id"] == row["execution_id"])
                record["predicted"] = None if prediction == "F" else False
                self.assertFalse(diagnostic.judge_record(json.dumps(record), execution)["eligible"])
        for config in ({"prediction": "T\nPREDICT: F"}, {"bad_relation": True}):
            with self.subTest(config=config):
                self.capture(**config)
                with self.assertRaisesRegex(ValueError, "paired shortage"):
                    self.export()

    def test_full_payload_and_sentence_echo_fail_without_later_reselection(self):
        for echo in (LESSON, "Notice surprising observations.", "notice   surprising OBSERVATIONS!"):
            with self.subTest(echo=echo):
                self.capture(echo=echo)
                valid_later = [row for row in self.replay["events"] if row["kind"] == "record" and row["arm"] == "P" and row["eligible"]]
                self.assertGreater(len(valid_later), 2)
                original = copy.deepcopy(self.selection)
                with self.assertRaisesRegex(ValueError, "copied parent/restatement prose in raw record context"):
                    self.export()
                self.assertEqual(self.selection, original)

    def test_restatement_prose_is_also_forbidden(self):
        text = "I will compare predictions and observations."
        self.capture(echo=text)
        with self.assertRaisesRegex(ValueError, "copied parent/restatement prose"):
            self.export()

    def test_masked_rendered_context_is_not_exempt(self):
        self.capture(tokenizer=Tokenizer(rendered_echo="Notice surprising observations.\n"))
        with self.assertRaisesRegex(ValueError, "copied parent/restatement prose in rendered record context"):
            self.export()

    def test_target_payload_and_span_checks_with_shared_protocol_exception(self):
        spans = material._payload_spans([LESSON])
        for text in (LESSON, "prefix Notice surprising observations. suffix", "embedded Compare outcomes using a varied probe."):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "raw record target"):
                material._check_payload(text, spans, "raw record target")
        self.capture(parent_text="TRY observed predicted relation 0,0,0", restatement="TRY observed predicted relation 0,0,0")
        self.assertEqual(len(self.export()["corpora"]["A"]["corpus"]), 2)
        self.assertEqual(material._payload_spans(["ACT: TRY 0,0,0", '"observed" "predicted" "relation"']), set())

    def test_short_pedagogical_sentence_is_not_shared_protocol(self):
        text = "Compare predicted and observed."
        self.capture(parent_text=text, echo=text)
        with self.assertRaisesRegex(ValueError, "copied parent/restatement prose"):
            self.export()

    def test_encoder_rejects_raw_target_prose_without_reserializing(self):
        row = self.selection["selected"]["P"][0]
        prompt = diagnostic.read(self.path / f"calls/{row['call_id']}.request.json")["request"]["prompt"]
        response = diagnostic.read(self.path / f"calls/{row['call_id']}.response.json")["response"]
        response["text"] += "\nNotice surprising observations."
        with self.assertRaisesRegex(ValueError, "copied parent/restatement prose in raw record target"):
            material._encode(prompt, response, row, self.tokenizer, 4096, material._payload_spans([LESSON]), 0)

    def test_missing_call_and_duplicate_execution_are_not_source_evidence(self):
        row = self.selection["selected"]["P"][0]
        (self.path / f"calls/{row['source_call_id']}.response.json").unlink()
        with self.assertRaisesRegex(ValueError, "capture replay failed"):
            self.export()
        self.capture()
        rows = copy.deepcopy(self.replay["events"])
        rows.insert(1, copy.deepcopy(rows[0]))
        (self.path / "events.jsonl").write_bytes(b"".join(diagnostic.encoded(row) for row in rows))
        self.reseal()
        self.bind_main()
        with self.assertRaisesRegex(ValueError, "capture replay failed"):
            self.export()

    def test_atomic_pair_failure_in_second_arm_returns_nothing(self):
        self.capture(echo="Notice surprising observations.", echo_arm="A")
        before = diagnostic.tree_hashes(self.path)
        original = material._encode
        completed = []
        def track(*args):
            result = original(*args)
            completed.append(args[2]["arm"])
            return result
        with patch.object(material, "_encode", side_effect=track), self.assertRaisesRegex(ValueError, "copied parent"):
            self.export()
        self.assertEqual(completed, ["P", "P"])
        self.assertEqual(diagnostic.tree_hashes(self.path), before)

    def test_native_render_input_output_token_mismatches(self):
        for field in ("rendered_prompt", "prompt_token_ids", "output_token_ids"):
            with self.subTest(field=field):
                self.capture()
                row = self.selection["selected"]["P"][0]
                def change(receipt):
                    response = receipt["response"]
                    response[field] = "wrong" if field == "rendered_prompt" else [1] + response[field][1:]
                self.mutate_call(row["call_id"], "response", change)
                self.bind()
                with self.assertRaisesRegex(ValueError, "native .* mismatch"):
                    self.export()

    def test_trainer_off_by_one_missing_double_eos_and_split_rejected(self):
        original_collate = trainer.collate
        for mode in ("off_by_one", "missing_eos", "double_eos", "context_loss"):
            with self.subTest(mode=mode):
                def corrupted(packs, pad_id):
                    batch = original_collate(packs, pad_id)
                    if mode == "off_by_one":
                        batch["labels"][0] = batch["labels"][0][1:] + [-100]
                    elif mode == "missing_eos":
                        batch["labels"][0][-1] = -100
                    elif mode == "double_eos":
                        batch["labels"][0].append(pad_id)
                        batch["input_ids"][0].append(pad_id)
                    else:
                        batch["labels"][0][1] = batch["input_ids"][0][1]
                    return batch
                with patch.object(trainer, "collate", side_effect=corrupted), self.assertRaisesRegex(ValueError, "causal input/labels/EOS"):
                    self.export()
        original_encode = trainer.encode_item_segments
        def split(*args, **kwargs):
            encoded = original_encode(*args, **kwargs)
            return encoded + encoded
        with patch.object(trainer, "encode_item_segments", side_effect=split), self.assertRaisesRegex(ValueError, "dropped/split"):
            self.export()

    def test_eos_required_and_no_embedded_target_eos_or_empty_tokens(self):
        tokenizer = Tokenizer()
        tokenizer.eos_token_id = None
        with self.assertRaisesRegex(ValueError, "tokenizer EOS required"):
            self.export(tokenizer=tokenizer)
        tokenizer.eos_token_id = ord("{") + 1
        with self.assertRaisesRegex(ValueError, "raw target already contains EOS"):
            self.export(tokenizer=tokenizer)
        tokenizer = Tokenizer()
        original = tokenizer.encode
        tokenizer.encode = lambda text, **kwargs: [] if text.startswith("\n {") else original(text, **kwargs)
        with self.assertRaisesRegex(ValueError, "empty record context or target"):
            self.export(tokenizer=tokenizer)

    def test_overlength_never_truncates_or_splits(self):
        with patch.object(trainer, "encode_item_segments", wraps=trainer.encode_item_segments) as encode:
            with self.assertRaisesRegex(ValueError, "overlength"):
                self.export(max_len=10)
            encode.assert_not_called()

    def test_source_changes_during_export_fail_atomically(self):
        original = trainer.collate
        def change_capture(*args):
            result = original(*args)
            self.overwrite("unexpected.json", {"changed": True})
            return result
        with patch.object(trainer, "collate", side_effect=change_capture), self.assertRaisesRegex(ValueError, "capture changed during export"):
            self.export()


if __name__ == "__main__":
    unittest.main()
