"""CPU fixtures only: scripted native-like responses, never real model evidence."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from organism_v6 import rulegame_parenting_diagnostic as diagnostic


class Tokenizer:
    def encode(self, text):
        return [ord(character) + 1 for character in text]

    def decode(self, tokens, **kwargs):
        return "".join(chr(token - 1) for token in tokens)

    def apply_chat_template(self, messages, **kwargs):
        return "<user>" + messages[0]["content"] + "</user><assistant>"

    def __call__(self, texts, padding=False, truncation=False, max_length=None, return_offsets_mapping=False):
        sequences = [self.encode(text)[:max_length] if truncation else self.encode(text) for text in texts]
        width = max(map(len, sequences))
        result = {"input_ids": [], "attention_mask": [], "offset_mapping": []}
        for tokens in sequences:
            missing = width - len(tokens) if padding else 0
            result["input_ids"].append(tokens + [0] * missing)
            result["attention_mask"].append([1] * len(tokens) + [0] * missing)
            result["offset_mapping"].append([(index, index + 1) for index in range(len(tokens))] + [(0, 0)] * missing)
        return result


class ScriptedBackend:
    def __init__(self, identity, bad_records=(), no_quiz=False, parent_text=None, aliases=False):
        self.source_identity = identity
        self.bad_records = bad_records
        self.no_quiz = no_quiz
        self.parent_text = parent_text
        self.aliases = aliases
        self.tokenizer = Tokenizer()
        self.requests = []

    def identity(self):
        return self.source_identity

    def generate(self, request):
        self.requests.append(copy.deepcopy(request))
        role, arm, tick = request["role"], request["arm"], request["tick"]
        if role == "wake":
            text = ("PREDICT: T\nACT: TRY 0,0,0" if tick <= 3 else
                    "DONE" if self.no_quiz else "ACT: QUIZ ?" if tick == 4 else "ACT: QUIZ T,T,T,T,T,T")
            if self.aliases:
                text = text.replace("ACT: TRY ", "TRY: ").replace("ACT: QUIZ ", "QUIZ: ")
        elif role == "parent":
            text = self.parent_text or ("Compare predictions with observations." if arm == "P" else "Thank you for participating.")
        elif role == "restate":
            text = "I will compare predictions and observations." if arm == "P" else "I participated in the activity."
        else:
            fields = json.loads(request["prompt"].split("Observed fields: ", 1)[1].splitlines()[0])
            relation = ("unavailable" if fields["predicted"] is None else
                        "matched" if fields["predicted"] == fields["observed"] else "mismatched")
            text = json.dumps(dict(try_placeholder=fields["values"], observed=fields["observed"],
                              predicted=fields["predicted"], relation=relation), separators=(",", ":")).replace('"try_placeholder"', '"try"')
            if arm in self.bad_records:
                text = "not a faithful JSON record"
        rendered = self.tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}])
        return dict(text=text, prompt_token_ids=self.tokenizer.encode(rendered),
                    output_token_ids=self.tokenizer.encode(text), rendered_prompt=rendered,
                    finish_reason="stop", stop_reason=None)


class RuleGameDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.model = self.base / "model"
        self.model.mkdir()
        diagnostic.write_json(self.model / "config.json", {"model_type": "qwen2"})
        (self.model / "weights.fixture").write_bytes(b"CPU fixture, not model weights")
        self.root = self.base / "run"
        self.plan = diagnostic.prepare(self.root, self.model, "0",
            datetime.fromtimestamp(time.time() + 3600, timezone.utc).isoformat())

    def capture(self, path, stage="formation", cell=None, **kwargs):
        path.mkdir(parents=True)
        adapter = self.root / "write" / cell[0] / "adapter" if cell and cell != "OFF" else None
        identity = diagnostic.expected_identity(self.plan, adapter)
        backend = ScriptedBackend(identity, **kwargs)
        protocol = self.plan.get("protocol", "strict_v1")
        calls = diagnostic.Calls(path / "calls", backend, stage, identity, protocol)
        events = diagnostic.Events(path / "events.jsonl")
        result = (diagnostic.run_formation(calls, events) if stage == "formation" else
                  diagnostic.run_evaluation(calls, events, cell))
        header = dict(stage=stage, cell=cell, backend=identity, model_files=self.plan["model_files"])
        if protocol != "strict_v1":
            header["protocol"] = protocol
        diagnostic.write_json(path / "identity.json", header)
        diagnostic.write_json(path / "result.json", result)
        diagnostic.write_json(path / "usage.json", diagnostic.usage(path))
        diagnostic.capture_manifest(path)
        return result, backend, events

    def formation_fixture(self, **kwargs):
        path = self.root / "formation" / "data"
        result = self.capture(path, **kwargs)
        diagnostic.write_json(self.root / "formation" / "result.json", dict(status="AWAITING_MAIN_AUDIT"))
        return result

    def audit_fixture(self, accept=True):
        audit = diagnostic.audit_template(self.root / "formation" / "data")
        audit["provenance_decision"] = "accept"
        audit["provenance_notes"] = "CPU fixture audit, not a native provenance certificate."
        for review in audit["reviews"]:
            review["decision"] = "accept" if accept else "reject"
            review["notes"] = "Fixture Main decision; no automated semantic certification."
        path = self.base / "main_audit.json"
        diagnostic.write_json(path, audit)
        return path

    def material_fixture(self, **kwargs):
        self.formation_fixture(**kwargs)
        return diagnostic.material(self.root, self.audit_fixture(), Tokenizer())

    def fit_fixture(self, arm, path):
        adapter = path / "adapter"
        adapter.mkdir()
        tokens = diagnostic.read(self.root / "material" / "tokens.json")[arm]
        metadata = dict(diagnostic.TRAIN, recipe="v1_frozen_child_target_seeded",
                        source_recipe="preschool_records_v1", loss_target="child_body_only",
                        source_corpus_sha256=diagnostic.digest(self.root / "material" / f"{arm}.json"),
                        tokens=12 * sum(row["input_tokens"] for row in tokens),
                        supervised_tokens=12 * sum(row["counts"]["supervised_child_tokens"] for row in tokens),
                        final_loss=.2)
        diagnostic.write_json(adapter / "train_meta.json", metadata)
        diagnostic.write_json(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
            bias="none", peft_type="LORA", base_model_name_or_path=str(self.model)))
        (adapter / "adapter_model.safetensors").write_bytes(b"CPU fixture, not adapter weights")
        (adapter / "DONE").write_text("fixture")

    def mocked_train(self, root, plan, stage_path, command, *args):
        stage_path.mkdir()
        self.fit_fixture(stage_path.name, stage_path)
        return dict(ok=True)

    def reseal(self, path):
        (path / "manifest.json").unlink()
        diagnostic.capture_manifest(path)

    def test_prepare_no_gpu_and_immutable_local_pins(self):
        with patch.object(diagnostic.supervisor, "gpu_processes_absent") as query:
            diagnostic.verify_plan(self.root)
            query.assert_not_called()
        self.assertEqual(len(self.plan["schedule"]["formation"]), 4)
        self.assertEqual(len(self.plan["schedule"]["evaluation"]), 4)
        self.assertNotIn("truth", json.dumps(self.plan))
        with self.assertRaisesRegex(ValueError, "already exists"):
            diagnostic.prepare(self.root, self.model, "0", datetime.fromtimestamp(time.time() + 1000, timezone.utc).isoformat())
        (self.model / "weights.fixture").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "model bytes changed"):
            diagnostic.verify_plan(self.root)

    def test_gpu_commands_fail_before_model_or_process_work_without_opt_in(self):
        with patch.object(diagnostic, "verify_plan") as verify, patch.object(diagnostic.subprocess, "Popen") as popen:
            for operation in (diagnostic.formation, diagnostic.write_adapters, diagnostic.evaluate):
                with self.assertRaisesRegex(ValueError, "allow-gpu"):
                    operation(self.root)
            verify.assert_not_called()
            popen.assert_not_called()

    def test_strict_parser_no_salvage(self):
        invalid = ["ACT: TRY 1,2,3,4", "ACT: TRY 1 2 3", "ACT: TRY 1,2,3; TRY 4,5,6",
                   "ACT: TRY 1,2,3\nACT: QUIZ ?", "### ACT: TRY 1,2,3", " act: TRY 1,2,3",
                   "ACT: QUIZ True,F,T,F,T,F", "ACT: QUIZ T,F,T,F,T,F,T", "ACT: QUIZ T,F",
                   "ACT: TRY 1,2,3\nDONE", "ACT: TRY 1.0,2,3", "ACT : TRY 1,2,3"]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                diagnostic.parse_action(text)
        parsed = diagnostic.parse_action("PREDICT: F\nACT: TRY -1,+2,0")
        self.assertEqual(parsed["values"], [-1, 2, 0])
        self.assertIs(parsed["predicted"], False)
        self.assertIsNone(diagnostic.parse_action("ACT: TRY 1,2,3\nPREDICT: T")["predicted"])
        self.assertTrue(diagnostic.parse_action("PREDICT: T\nPREDICT: F\nACT: TRY 1,2,3")["prediction_ambiguous"])

    def test_record_strict_schema_missing_prediction_and_false_are_valid(self):
        execution = dict(values=[0, 0, 0], observed=False, predicted=True, prediction_ambiguous=False)
        text = '{"try":[0,0,0],"observed":false,"predicted":true,"relation":"mismatched"}'
        self.assertTrue(diagnostic.judge_record(text, execution)["eligible"])
        invalid = [text.replace('false', '0'), text.replace('[0,0,0]', '[true,0,0]'),
                   text.replace('"mismatched"', '"matched"'), text + " prose",
                   text.replace('"observed":false', '"observed":false,"observed":false'),
                   text.replace('[0,0,0]', '[0.0,0,0]'), text.replace('"relation"', '"explanation"')]
        for wrong in invalid:
            self.assertFalse(diagnostic.judge_record(wrong, execution)["eligible"], wrong)
        execution["predicted"] = None
        missing = text.replace('"predicted":true', '"predicted":null').replace('"mismatched"', '"unavailable"')
        self.assertTrue(diagnostic.judge_record(missing, execution)["eligible"])
        execution["prediction_ambiguous"] = True
        self.assertFalse(diagnostic.judge_record(missing, execution)["eligible"])

    def test_formation_exact_caps_raw_parent_outputs_and_world_replay(self):
        result, backend, events = self.formation_fixture()
        self.assertEqual(result["calls"], 60)
        self.assertEqual(result["roles"], dict(wake=40, parent=4, restate=4, record=12))
        self.assertEqual(len(result["interactions"]), 4)
        self.assertEqual(len([row for row in events.rows if row["kind"] == "record"]), 12)
        self.assertFalse(result["semantic_no_answer_certification"])
        self.assertFalse((self.root / "material").exists())
        self.assertFalse((self.root / "write").exists())
        path = self.root / "formation" / "data"
        self.assertTrue(diagnostic.check_capture(path)["ok"])
        totals = diagnostic.usage(path)
        self.assertEqual(sum(row["requests"] for row in totals.values()), 60)
        self.assertEqual(sum(row["output_token_ceiling"] for row in totals.values()), 18480)
        self.assertEqual(totals["parent"]["by_arm"]["P"]["requests"], 2)
        self.assertEqual(totals["parent"]["by_arm"]["A"]["requests"], 2)
        acts = [row for row in events.rows if row.get("action_kind") == "try"]
        self.assertTrue(any(row["observed"] is False for row in acts))
        self.assertTrue(all(row["reward"] == 0 for row in acts))
        for request in backend.requests:
            self.assertNotIn("sum divisible by three", request["prompt"])
            self.assertNotIn("strictly increasing", request["prompt"])

    def test_formation_command_stops_for_main_not_lexical_semantics(self):
        def simulated(root, plan, stage_path, command, call_path):
            stage_path.mkdir()
            self.capture(call_path.parent, parent_text="The answer is the hidden rule; do this strategy.")
        with patch.object(diagnostic, "supervise", side_effect=simulated):
            result = diagnostic.formation(self.root, allow_gpu=True)
        self.assertEqual(result["status"], "AWAITING_MAIN_AUDIT")
        template = diagnostic.read(self.root / "formation" / "main_audit.template.json")
        self.assertTrue(all(review["decision"] == "pending" for review in template["reviews"]))
        self.assertFalse((self.root / "material").exists())
        self.assertFalse((self.root / "write").exists())
        with self.assertRaisesRegex(ValueError, "already exists"):
            diagnostic.formation(self.root, allow_gpu=True)

    def test_main_rejection_means_no_corpora_or_fit(self):
        self.formation_fixture()
        result = diagnostic.material(self.root, self.audit_fixture(accept=False), Tokenizer())
        self.assertEqual(result["status"], "MAIN_DECLINED_MATERIAL")
        self.assertFalse((self.root / "material" / "P.json").exists())
        with patch.object(diagnostic, "supervise") as supervise:
            with self.assertRaisesRegex(ValueError, "not ready"):
                diagnostic.write_adapters(self.root, allow_gpu=True)
            supervise.assert_not_called()

    def test_pending_or_wrong_audit_cannot_select(self):
        self.formation_fixture()
        path = self.base / "pending.json"
        diagnostic.write_json(path, diagnostic.audit_template(self.root / "formation" / "data"))
        with self.assertRaisesRegex(ValueError, "provenance notes"):
            diagnostic.material(self.root, path, Tokenizer())
        self.assertFalse((self.root / "material" / "P.json").exists())

    def test_shortage_is_paired_and_stops_before_native_tokenizer_or_new_tasks(self):
        self.formation_fixture(bad_records={"A"})
        with patch.object(diagnostic, "native_tokenizer") as tokenizer:
            result = diagnostic.material(self.root, self.audit_fixture())
            tokenizer.assert_not_called()
        self.assertEqual(result["status"], "PAIRED_SHORTAGE")
        self.assertTrue(result["no_more_tasks"])
        self.assertEqual(len(result["failures"]), 6)
        self.assertFalse((self.root / "material" / "P.json").exists())
        with patch.object(diagnostic, "supervise") as supervise:
            for operation in (diagnostic.write_adapters, diagnostic.evaluate):
                with self.assertRaisesRegex(ValueError, "not ready"):
                    operation(self.root, allow_gpu=True)
            supervise.assert_not_called()

    def test_two_execution_records_no_quiz_or_unique_text_gate(self):
        result = self.material_fixture(no_quiz=True)
        self.assertEqual(result["status"], "READY")
        formation = diagnostic.read(self.root / "formation" / "data" / "result.json")
        self.assertTrue(all(not task["valid_quiz"] for task in formation["tasks"]))
        selection = diagnostic.read(self.root / "material" / "selection.json")
        for arm in diagnostic.ARMS:
            rows = selection["selected"][arm]
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]["execution_id"], rows[1]["execution_id"])
            self.assertEqual(rows[0]["text"], rows[1]["text"])
            self.assertEqual(rows[0]["eid"], diagnostic.task_id(0, "apply"))
        diagnostic.verify_material(self.root, self.plan, Tokenizer())

    def test_child_only_mask_targets_and_teacher_exclusion(self):
        self.material_fixture()
        for arm in diagnostic.ARMS:
            corpus = diagnostic.read(self.root / "material" / f"{arm}.json")
            self.assertEqual(corpus["recipe"], "preschool_records_v1")
            for text in corpus["corpus"]:
                prefix = diagnostic.train_adapter.child_record_prefix_length(text)
                self.assertEqual(set(json.loads(text[prefix:])), {"try", "observed", "predicted", "relation"})
                for teacher in (diagnostic.RECORD, "Compare predictions with observations.", "Thank you for participating."):
                    self.assertNotIn(teacher, text)
            tokens = diagnostic.read(self.root / "material" / "tokens.json")[arm]
            for row in tokens:
                self.assertGreater(row["counts"]["supervised_child_tokens"], 0)
                self.assertEqual(row["counts"]["supervised_prefix_tokens"], 0)
                self.assertEqual(row["counts"]["supervised_padding_tokens"], 0)

    def test_export_preserves_exact_raw_target_suffix_bytes_including_whitespace(self):
        original_generate = ScriptedBackend.generate

        def padded_record(backend, request):
            response = original_generate(backend, request)
            if request["role"] == "record":
                response["text"] = " \t\r\n" + response["text"] + "\r\n\t "
                response["output_token_ids"] = backend.tokenizer.encode(response["text"])
            return response

        with patch.object(ScriptedBackend, "generate", padded_record):
            result = self.material_fixture()
        self.assertEqual(result["status"], "READY")
        selection = diagnostic.read(self.root / "material" / "selection.json")
        for arm in diagnostic.ARMS:
            corpus = diagnostic.read(self.root / "material" / f"{arm}.json")["corpus"]
            for text, row in zip(corpus, selection["selected"][arm]):
                response_path = self.root / "formation" / "data" / "calls" / f"{row['call_id']}.response.json"
                raw = diagnostic.read(response_path)["response"]["text"]
                self.assertTrue(raw.startswith(" \t\r\n") and raw.endswith("\r\n\t "))
                boundary = diagnostic.train_adapter.child_record_prefix_length(text)
                self.assertEqual(text[boundary:].encode("utf-8"), raw.encode("utf-8"))
                self.assertEqual(row["text"].encode("utf-8"), raw.encode("utf-8"))
        diagnostic.verify_material(self.root, self.plan, Tokenizer())

    def test_native_truncation_fails_not_silently_masks(self):
        corpus = ["Situation task.\nMy measured action record: " + "z" * 600] * 2
        with self.assertRaisesRegex(ValueError, "truncate"):
            diagnostic.audit_tokens(Tokenizer(), corpus)

    def test_resealed_corpus_cannot_replace_child_output(self):
        self.material_fixture()
        path = self.root / "material" / "P.json"
        document = diagnostic.read(path)
        document["corpus"][0] += " supplied teacher text"
        path.write_bytes(diagnostic.encoded(document))
        self.reseal(path.parent)
        with self.assertRaisesRegex(ValueError, "actual selected child outputs"):
            diagnostic.verify_material(self.root, self.plan, Tokenizer())

    def test_provenance_failure_list_rejects_forged_orphan_even_when_resealed(self):
        self.formation_fixture()
        path = self.root / "formation" / "data"
        rows = [diagnostic.decode(line) for line in (path / "events.jsonl").read_text().splitlines()]
        next(row for row in rows if row["kind"] == "record")["execution_id"] = "nonexistent"
        (path / "events.jsonl").write_bytes(b"".join(diagnostic.encoded(row) for row in rows))
        self.reseal(path)
        audit = diagnostic.check_capture(path)
        self.assertFalse(audit["ok"])
        self.assertIn("provenance mismatch", audit["failures"][0])
        result = diagnostic.material(self.root, self.base / "unneeded.json", Tokenizer())
        self.assertEqual(result["status"], "PROVENANCE_FAILURE")
        self.assertTrue(diagnostic.read(self.root / "material" / "provenance.json")["failures"])

    def test_native_source_token_mismatch_fails_cpu_material_check(self):
        self.formation_fixture()
        path = self.root / "formation" / "data"
        response_path = path / "calls" / "0000.response.json"
        receipt = diagnostic.read(response_path)
        receipt["response"]["prompt_token_ids"][0] += 1
        receipt["response_sha256"] = diagnostic.value_hash(receipt["response"])
        response_path.write_bytes(diagnostic.encoded(receipt))
        self.reseal(path)
        with self.assertRaisesRegex(ValueError, "native source input token mismatch"):
            diagnostic.material(self.root, self.audit_fixture(), Tokenizer())
        self.assertFalse((self.root / "material" / "P.json").exists())

    def test_first_fit_failure_never_launches_second_or_evaluation(self):
        self.material_fixture()
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=ValueError("fixture training failure")) as supervise:
            with self.assertRaisesRegex(ValueError, "fixture training failure"):
                diagnostic.write_adapters(self.root, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)
            with self.assertRaisesRegex(ValueError, "paired write failed"):
                diagnostic.evaluate(self.root, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)
        self.assertFalse(diagnostic.read(self.root / "write" / "failure.json")["evaluation_allowed"])

    def test_second_fit_failure_preserves_first_and_blocks_readout(self):
        self.material_fixture()
        def fit_then_fail(root, plan, stage_path, command):
            if stage_path.name == "A":
                raise ValueError("second fit failed")
            return self.mocked_train(root, plan, stage_path, command)
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=fit_then_fail) as supervise:
            with self.assertRaisesRegex(ValueError, "second fit failed"):
                diagnostic.write_adapters(self.root, allow_gpu=True)
            self.assertEqual(supervise.call_count, 2)
            with self.assertRaisesRegex(ValueError, "paired write failed"):
                diagnostic.evaluate(self.root, allow_gpu=True)
        self.assertTrue((self.root / "write" / "P" / "adapter" / "DONE").exists())

    def test_complete_mocked_pipeline_shared_off_and_156_ceiling(self):
        self.material_fixture()
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=self.mocked_train) as training:
            fits = diagnostic.write_adapters(self.root, allow_gpu=True)
        self.assertEqual(training.call_count, 2)
        for call in training.call_args_list:
            command = call.args[3]
            self.assertEqual(command[command.index("--epochs") + 1], "12")
            self.assertEqual(command[command.index("--rank") + 1], "8")
            self.assertEqual(command[command.index("--seed") + 1], "2")
        self.assertFalse(fits["promoted"])
        captures = {}
        def evaluate_fixture(root, plan, stage_path, command, call_path):
            cell = command[command.index("--cell") + 1]
            captures[cell] = self.capture(call_path.parent, "evaluation", cell)
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=evaluate_fixture) as evaluations:
            result = diagnostic.evaluate(self.root, allow_gpu=True)
        self.assertEqual(evaluations.call_count, 3)
        self.assertEqual(list(captures), ["OFF", "P_ON", "A_ON"])
        self.assertEqual(sum(capture[0]["calls"] for capture in captures.values()) + 60, 156)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["P_minus_A"], result["P_minus_OFF"] - result["A_minus_OFF"])
        for cell, (_, backend, _) in captures.items():
            identity = backend.identity()
            self.assertEqual(identity["adapter_input"] is None, cell == "OFF")
            for request in backend.requests:
                self.assertNotIn("Temporary parent restatement", request["prompt"])
                self.assertNotIn("Thank you for participating.", request["prompt"])
                self.assertNotIn("Compare predictions with observations.", request["prompt"])
                self.assertNotIn("strictly increasing", request["prompt"])
        off = captures["OFF"][1].requests
        for cell in ("P_ON", "A_ON"):
            for first, second in zip(off, captures[cell][1].requests):
                self.assertEqual(first["prompt"], second["prompt"])
                self.assertEqual(first["seed"], second["seed"])
        self.assertTrue(diagnostic.replay(self.root)["ok"])

    def test_supervisor_real_cpu_process_timeout_and_owned_cleanup(self):
        with patch.object(diagnostic, "WORKER_SECONDS", .05):
            with self.assertRaisesRegex(ValueError, "supervised worker failed"):
                diagnostic.supervise(self.root, self.plan, self.root / "cpu_timeout",
                    [sys.executable, "-B", "-c", "import time; time.sleep(30)"], occupancy=lambda device: True)
        receipt = diagnostic.read(self.root / "cpu_timeout" / "supervision.json")
        self.assertFalse(receipt["ok"])
        self.assertTrue(receipt["owned_group_empty"])
        self.assertTrue(receipt["reservation_release_verified"])
        self.assertIn("timeout", receipt["error"]["message"])
        with self.assertRaisesRegex(ValueError, "previous worker failed"):
            diagnostic.remaining_seconds(self.root, self.plan)

    def test_supervisor_actual_pending_call_timeout_not_only_budget_arithmetic(self):
        data = self.root / "pending_data"
        calls = data / "calls"
        calls.mkdir(parents=True)
        diagnostic.write_json(data / "backend.ready.json", {"ready": True})
        diagnostic.write_json(calls / "0000.request.json", {"started": time.monotonic() - 10})
        with patch.object(diagnostic, "CALL_SECONDS", .01):
            with self.assertRaisesRegex(ValueError, "actual backend call timeout"):
                diagnostic.supervise(self.root, self.plan, self.root / "pending_worker",
                    [sys.executable, "-B", "-c", "import time; time.sleep(30)"], calls, occupancy=lambda device: True)
        self.assertTrue(diagnostic.read(self.root / "pending_worker" / "supervision.json")["owned_group_empty"])

    def test_expired_or_exhausted_lease_never_spawns(self):
        with patch.object(diagnostic.subprocess, "Popen") as popen:
            for plan in (dict(self.plan, lease_end=time.time() - 1),):
                with self.assertRaisesRegex(ValueError, "cap exhausted"):
                    diagnostic.supervise(self.root, plan, self.root / "expired", ["never"], occupancy=lambda device: True)
            popen.assert_not_called()
        path = self.root / "spent"
        path.mkdir()
        diagnostic.write_json(path / "supervision.json", dict(ok=True, reservation_release_verified=True, reserved_seconds=1800))
        with self.assertRaisesRegex(ValueError, "cap exhausted"):
            diagnostic.remaining_seconds(self.root, self.plan)

    def test_atomic_json_refuses_overwrite_and_artifact_symlink(self):
        path = self.base / "immutable.json"
        diagnostic.write_json(path, {"first": True})
        with self.assertRaises(FileExistsError):
            diagnostic.write_json(path, {"first": False})
        self.assertEqual(diagnostic.read(path), {"first": True})
        (self.root / "alias").symlink_to(path)
        with self.assertRaisesRegex(ValueError, "symlink"):
            diagnostic.tree_hashes(self.root)

    def worker_fixture(self, generation_failure=False, cleanup_ok=True, construction_failure=False):
        stage = self.root / "formation" / "worker"
        stage.mkdir(parents=True)
        diagnostic.write_json(stage / "process.json", {"pid": os.getpid()})
        backend = ScriptedBackend(diagnostic.expected_identity(self.plan))
        backend.backend = object()
        if generation_failure:
            backend.generate = lambda request: (_ for _ in ()).throw(RuntimeError("fixture generation failed"))
        with patch.object(diagnostic, "NativeBackend", return_value=backend,
                          side_effect=RuntimeError("fixture construction failed") if construction_failure else None), \
             patch.object(diagnostic.supervisor, "selected_device", return_value="0"), \
             patch.object(diagnostic.os, "getpgrp", return_value=os.getpid()), \
             patch.object(diagnostic.threading, "Thread"), \
             patch("organism_v6.model_backend.close_backend", return_value=cleanup_ok) as close:
            try:
                diagnostic.worker(self.root, "formation", self.root / "formation" / "data", allow_gpu=True)
            finally:
                close.assert_called_once_with(None if construction_failure else backend.backend)

    def test_worker_closes_owned_native_backend_on_normal_exit(self):
        self.worker_fixture()
        path = self.root / "formation" / "data"
        self.assertTrue(diagnostic.read(path / "backend.cleanup.json")["closed"])
        self.assertTrue(diagnostic.check_capture(path)["ok"])

    def test_worker_closes_owned_native_backend_on_generation_exception(self):
        with self.assertRaisesRegex(RuntimeError, "fixture generation failed"):
            self.worker_fixture(generation_failure=True)
        path = self.root / "formation" / "data"
        self.assertTrue(diagnostic.read(path / "backend.cleanup.json")["closed"])
        self.assertTrue((path / "failure.json").is_file())
        self.assertFalse((path / "manifest.json").exists())

    def test_worker_partial_constructor_uses_owned_descendant_cleanup(self):
        with self.assertRaisesRegex(RuntimeError, "fixture construction failed"):
            self.worker_fixture(construction_failure=True)
        self.assertTrue(diagnostic.read(self.root / "formation" / "data" / "backend.cleanup.json")["closed"])

    def test_worker_cleanup_failure_never_seals_success(self):
        with self.assertRaisesRegex(ValueError, "owned backend cleanup failed"):
            self.worker_fixture(cleanup_ok=False)
        path = self.root / "formation" / "data"
        self.assertFalse(diagnostic.read(path / "backend.cleanup.json")["closed"])
        self.assertFalse((path / "manifest.json").exists())

    def test_repeated_reveal_or_fourth_try_has_no_extra_world_execution(self):
        class Outputs:
            def __init__(self, outputs):
                self.outputs = iter(outputs)
                self.count = 0
            def ask(self, *args):
                self.count += 1
                return str(self.count), next(self.outputs)
        for outputs, expected_count in ((["ACT: QUIZ ?", "ACT: QUIZ ?"], 1),
                                         (["ACT: TRY 1,2,3"] * 4, 3)):
            events = diagnostic.Events()
            result, _ = diagnostic.play_task(Outputs(outputs), events, "P", diagnostic.task_id(0, "pre"))
            self.assertEqual(result["terminal"], "protocol_invalid")
            self.assertEqual(sum(row["kind"] == "execution" for row in events.rows), expected_count)

    def test_actual_output_token_cap_and_backend_identity_are_enforced(self):
        identity = diagnostic.expected_identity(self.plan)
        backend = ScriptedBackend(identity)
        calls = diagnostic.Calls(self.base / "budget_calls", backend, "evaluation", identity)
        original_generate = backend.generate
        def oversized(request):
            response = original_generate(request)
            response["output_token_ids"] = [1] * 401
            return response
        backend.generate = oversized
        with self.assertRaisesRegex(ValueError, "output exceeds cap"):
            calls.ask("wake", "OFF", diagnostic.task_id(2, "readout"), 1, "task")
        self.assertTrue((self.base / "budget_calls" / "0000.response.json").exists())
        backend.source_identity = dict(identity, adapter_input="wrong")
        with self.assertRaisesRegex(ValueError, "backend identity changed"):
            calls.ask("wake", "OFF", diagnostic.task_id(2, "readout"), 2, "task")

    def test_cleanup_tail_is_reserved_before_launch(self):
        with patch.object(diagnostic.subprocess, "Popen") as popen:
            plan = dict(self.plan, lease_end=time.time() + diagnostic.CLEANUP_RESERVE)
            with self.assertRaisesRegex(ValueError, "time for owned cleanup"):
                diagnostic.supervise(self.root, plan, self.root / "too_late", ["never"], occupancy=lambda device: True)
            popen.assert_not_called()

    def test_v2_aliases_are_single_anchored_intents_only(self):
        for text, kind in (("PREDICT: T\nTRY: 1,2,3", "try"), ("QUIZ: ?", "reveal"),
                           ("QUIZ: T,F,T,F,T,F", "quiz"), ("ACT: TRY -1,+2,0", "try"),
                           ("DONE", "done")):
            with self.subTest(text=text):
                self.assertEqual(diagnostic.parse_action(text, "interaction_v2")["kind"], kind)
        invalid = [" TRY: 1,2,3", "### TRY: 1,2,3", "try: 1,2,3", "TRY : 1,2,3",
                   "TRY: 1,2,3,4", "TRY: 1 2 3", "TRY: 1.0,2,3", "TRY: 1,2,3; TRY 4,5,6",
                   "TRY: 1,2,3\nQUIZ: ?", "ACT: TRY 1,2,3\nTRY: 4,5,6",
                   "TRY: 1,2,3\nACT: QUIZ ?", "ACT: TRY 1,2,3\nTRY 4,5,6",
                   "QUIZ: T,F", "QUIZ: True,F,T,F,T,F", "QUIZ: T,F,T,F,T,F,T",
                   "TRY: 1,2,3\nDONE", "QUIZ: ?\ndone", "DONE\nTRY 1,2,3",
                   "ACT: TRY 1,2,3\n[OUTCOME] the box says: True",
                   "[OUTCOME] True\nTRY: 1,2,3"]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                diagnostic.parse_action(text, "interaction_v2")
        for text in ("PREDICT: T\nTRY: 1,2,3", "QUIZ: ?", "QUIZ: T,F,T,F,T,F"):
            with self.subTest(strict=text), self.assertRaisesRegex(ValueError, "missing canonical ACT"):
                diagnostic.parse_action(text)

    def test_v2_capture_preserves_raw_and_pins_stops_and_state(self):
        self.root = self.base / "v2"
        self.plan = diagnostic.prepare(self.root, self.model, "0",
            datetime.fromtimestamp(time.time() + 3600, timezone.utc).isoformat(), "interaction_v2")
        path = self.root / "formation" / "data"
        result, backend, events = self.capture(path, aliases=True)
        self.assertEqual(result["calls"], 60)
        self.assertTrue(diagnostic.replay(self.root)["ok"])
        diagnostic.audit_native_calls(Tokenizer(), path)
        executions = [row for row in events.rows if row["kind"] == "execution"]
        self.assertEqual(executions[0]["raw_response"], "PREDICT: T\nTRY: 0,0,0")
        self.assertEqual(executions[0]["canonical_action"], "ACT: TRY 0,0,0")
        self.assertEqual(executions[0]["action"], "TRY 0,0,0")
        self.assertIs(executions[0]["predicted"], True)
        for request in backend.requests:
            self.assertEqual(request["protocol"], "interaction_v2")
            self.assertEqual(request["stop"], ["\n[OUTCOME]"] if request["role"] == "wake" else [])
            self.assertFalse(request["include_stop_str_in_output"])
            if request["role"] == "wake":
                remaining = max(0, 4 - request["tick"])
                self.assertIn(f"remaining TRY budget: {remaining}", request["prompt"])
                self.assertIn("Quiz already revealed" if request["tick"] == 5 else
                              "Quiz reveal still needed", request["prompt"])
            if request["arm"] == "A" and request["role"] == "parent":
                self.assertTrue(request["prompt"].startswith(diagnostic.CONTROL_V2))
            if request["arm"] == "A" and request["role"] == "restate":
                self.assertIn("Restate only the acknowledgement", request["prompt"])
        self.assertFalse(diagnostic.check_capture(path, protocol="strict_v1")["ok"])
        request_path = path / "calls" / "0000.request.json"
        receipt = diagnostic.read(request_path)
        receipt["request"]["stop"] = []
        request_path.write_bytes(diagnostic.encoded(receipt))
        self.reseal(path)
        self.assertIn("source request", diagnostic.check_capture(path)["failures"][0])

    def test_v1_requests_and_legacy_plan_keep_strict_defaults(self):
        self.assertEqual(self.plan["protocol"], "strict_v1")
        legacy = dict(self.plan)
        legacy.pop("protocol")
        (self.root / "plan.json").write_bytes(diagnostic.encoded(legacy))
        (self.root / "plan.sha256.json").write_bytes(diagnostic.encoded(
            {"sha256": diagnostic.digest(self.root / "plan.json")}))
        self.assertNotIn("protocol", diagnostic.verify_plan(self.root))
        path = self.root / "formation" / "data"
        result, backend, _ = self.capture(path, aliases=True)
        self.assertTrue(all(task["terminal"] == "protocol_invalid" for task in result["tasks"]))
        self.assertTrue(diagnostic.replay(self.root)["ok"])
        for request in backend.requests:
            self.assertNotIn("protocol", request)
            self.assertNotIn("stop", request)
            self.assertNotIn("Harness state:", request["prompt"])

    def test_protocol_option_is_prepare_only(self):
        with patch.object(diagnostic, "prepare", return_value=None) as prepare:
            diagnostic.main(["prepare", "--out", "out", "--model", "model", "--device", "0",
                             "--lease-end", "later", "--protocol", "interaction_v2"])
            self.assertEqual(prepare.call_args.args[-1], "interaction_v2")
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            diagnostic.main(["replay", "--root", str(self.root), "--protocol", "interaction_v2"])

    def test_v2_budgets_and_imagined_outcomes_never_execute(self):
        cases = ((["TRY: 1,2,3"] * 4, 3), (["QUIZ: ?", "QUIZ: ?"], 1),
                 (["QUIZ: T,F,T,F,T,F"], 0), (["TRY: 1,2,3\nDONE"], 0),
                 (["TRY: 1,2,3\n[OUTCOME] True\nTRY: 4,5,6"], 0),
                 (["ACT: TRY 1,2,3\n[OUTCOME] True"], 0))
        for outputs, executed in cases:
            replies = iter(enumerate(outputs))
            calls = SimpleNamespace(protocol="interaction_v2", ask=lambda *args: next(replies))
            events = diagnostic.Events()
            with self.subTest(outputs=outputs):
                result, _ = diagnostic.play_task(calls, events, "P", diagnostic.task_id(0, "pre"))
                self.assertEqual(result["terminal"], "protocol_invalid")
                self.assertEqual(sum(row["kind"] == "execution" for row in events.rows), executed)
                self.assertFalse(any(row["kind"] == "record" for row in events.rows))

    def test_native_v2_stop_settings_reach_vllm_and_audit_raw_ids(self):
        tokenizer = Tokenizer()
        rendered = tokenizer.apply_chat_template([{"content": "task"}])
        text = "PREDICT: T\nTRY: 1,2,3"
        native = SimpleNamespace(text=text, token_ids=tokenizer.encode(text + "\n[OUTCOME]"),
                                 finish_reason="stop", stop_reason="\n[OUTCOME]")
        engine = Mock()
        engine.generate.return_value = [SimpleNamespace(outputs=[native], prompt_token_ids=tokenizer.encode(rendered))]
        backend = diagnostic.NativeBackend.__new__(diagnostic.NativeBackend)
        backend.backend = SimpleNamespace(tok=tokenizer, llm=engine, adapter_path=None)
        backend.identity = lambda: {"fixture": True}
        sampling = Mock(return_value="sampling")
        calls_path = self.base / "native_stop"
        calls_path.mkdir()
        calls = diagnostic.Calls(calls_path / "calls", backend, "evaluation", backend.identity(), "interaction_v2")
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=sampling)}):
            _, raw = calls.ask("wake", "OFF", diagnostic.task_id(2, "readout"), 1, "task")
        self.assertEqual(raw, text)
        self.assertEqual(sampling.call_args.kwargs["stop"], ["\n[OUTCOME]"])
        self.assertFalse(sampling.call_args.kwargs["include_stop_str_in_output"])
        diagnostic.audit_native_calls(tokenizer, calls_path)
        receipt = diagnostic.read(calls_path / "calls" / "0000.response.json")
        self.assertEqual(receipt["response"]["output_token_ids"], native.token_ids)
        self.assertEqual(engine.generate.call_args.args[1], "sampling")

    def test_eval_acceptance_rejects_resealed_mismatched_actual_output_ids(self):
        self.material_fixture()
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=self.mocked_train):
            diagnostic.write_adapters(self.root, allow_gpu=True)
        def corrupt_capture(root, plan, stage_path, command, call_path):
            cell = command[command.index("--cell") + 1]
            self.capture(call_path.parent, "evaluation", cell)
            response_path = call_path / "0000.response.json"
            receipt = diagnostic.read(response_path)
            receipt["response"]["output_token_ids"][0] += 1
            receipt["response_sha256"] = diagnostic.value_hash(receipt["response"])
            response_path.write_bytes(diagnostic.encoded(receipt))
            self.reseal(call_path.parent)
            self.assertTrue(diagnostic.check_capture(call_path.parent)["ok"])
        with patch.object(diagnostic, "native_tokenizer", return_value=Tokenizer()), \
             patch.object(diagnostic, "supervise", side_effect=corrupt_capture) as supervise:
            with self.assertRaisesRegex(ValueError, "native source output token mismatch"):
                diagnostic.evaluate(self.root, allow_gpu=True)
        self.assertEqual(supervise.call_count, 1)
        self.assertFalse((self.root / "evaluation" / "result.json").exists())
        self.assertEqual(diagnostic.read(self.root / "evaluation" / "failure.json")["completed_cells"], [])


if __name__ == "__main__":
    unittest.main()
