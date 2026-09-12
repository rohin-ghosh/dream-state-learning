"""Owned CPU fixtures, not native model or scientific evidence."""
import copy
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from organism_v6 import fundamental_teaching_readout as readout

base = readout.base


class Tokenizer:
    def __init__(self):
        self.messages = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        if tokenize is not False or add_generation_prompt is not True or len(messages) != 1:
            raise AssertionError("native user template invocation differs")
        if set(messages[0]) != {"role", "content"} or messages[0]["role"] != "user":
            raise AssertionError("model may receive only a user prompt")
        self.messages.append(copy.deepcopy(messages))
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text):
        return [ord(character) for character in text]

    def decode(self, tokens, **kwargs):
        return "".join(chr(token) for token in tokens)


class Backend:
    def __init__(self, plan, tokenizer, text=None):
        self.plan, self.tokenizer, self.text = plan, tokenizer, text
        self.backend = object()
        self.seen = []

    def identity(self):
        return self.plan["identity"]

    def generate(self, request):
        self.seen.append(copy.deepcopy(request))
        case = self.plan["cases"][int(request["call_id"])]
        text = self.text
        if text is None:
            expected = case["expected"]
            text = f"PREDICT: {expected}\nACT: {expected}" if case["kind"] == "addition" else expected
        rendered = self.tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                      tokenize=False, add_generation_prompt=True)
        return dict(text=text, rendered_prompt=rendered, prompt_token_ids=self.tokenizer.encode(rendered),
                    output_token_ids=self.tokenizer.encode(text), finish_reason="stop", stop_reason=None)


class ScoringTests(unittest.TestCase):
    def test_action_correctness_is_separate_from_adherence(self):
        for text, adherence in (("ACT: 7", False), ("PREDICT: 7\nACT: 7", True),
                                ("ACT: 7\nPREDICT: 7", False),
                                ("PREDICT: 8\nACT: 7", False)):
            with self.subTest(text=text):
                score = readout.score_addition(text, 7)
                self.assertTrue(score["correct_action"])
                self.assertEqual(score["adherence"], adherence)
                self.assertEqual(score["raw_text"], text)

    def test_first_act_not_best_and_multiple_acts_invalid(self):
        for text, first in (("ACT: 6\nACT: 7", 6), ("ACT: 7\nACT: 6", 7),
                            ("ACT: 7\nACT: 7", 7), ("ACT: nope\nACT: 7", None)):
            with self.subTest(text=text):
                score = readout.score_addition(text, 7)
                self.assertEqual(score["first_act"], first)
                self.assertEqual(score["act_count"], 2)
                self.assertFalse(score["action_valid"])
                self.assertFalse(score["correct_action"])
                self.assertFalse(score["adherence"])

    def test_missing_malformed_unanchored_act_and_wrong_sum(self):
        for text in ("", "7", "Answer ACT: 7", "ACT 7", "ACT: 7.0", "ACT: 7 extra",
                     "ACT:\n7", "ACT: ７", "ACT: 6", "PREDICT: 7\nACT: 6"):
            with self.subTest(text=text):
                score = readout.score_addition(text, 7)
                self.assertFalse(score["correct_action"])
                self.assertFalse(score["adherence"])
        score = readout.score_addition("ACT: 6", 7)
        self.assertTrue(score["action_valid"])
        self.assertEqual(score["first_act"], 6)

    def test_missing_multiple_malformed_predictions_never_rescued(self):
        for prefix in ("", "PREDICT: nope\n", "PREDICT 7\n", "PREDICT: 7.0\n",
                       "PREDICT:\n7\n", "PREDICT: 7\nPREDICT: 7\n",
                       "PREDICT: nope\nPREDICT: 7\n", "Example PREDICT: 7\n"):
            with self.subTest(prefix=prefix):
                score = readout.score_addition(prefix + "ACT: 7", 7)
                self.assertTrue(score["correct_action"])
                self.assertFalse(score["prediction_valid"])
                self.assertFalse(score["adherence"])

    def test_anchored_signed_integers_and_whitespace(self):
        self.assertTrue(readout.score_addition("  PREDICT: +07\r\n\tACT: 7  \r\n", 7)["adherence"])
        self.assertTrue(readout.score_addition("PREDICT: -3\nACT: -3", -3)["adherence"])
        self.assertFalse(readout.score_addition("PREDICT: 7 ACT: 7", 7)["adherence"])

    def test_memory_exact_color_only_one_terminal_period(self):
        for text in ("blue", " BLUE\n", "Blue.", " blue. \n"):
            score = readout.score_memory(text, "blue")
            self.assertTrue(score["valid"])
            self.assertTrue(score["correct"])
            self.assertEqual(score["raw_text"], text)
        for text in ("", "blue..", "blue .", "The color is blue.", '"blue"',
                     "blue\nred", "unknown", "purple", "blue!", "blue. red"):
            with self.subTest(text=text):
                score = readout.score_memory(text, "blue")
                self.assertFalse(score["valid"])
                self.assertFalse(score["correct"])
                self.assertIsNone(score["answer"])
                self.assertEqual(score["raw_text"], text)
        score = readout.score_memory("Red.", "blue")
        self.assertTrue(score["valid"])
        self.assertFalse(score["correct"])


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fundamental-readout-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        (self.model / "config.json").write_text('{"model_type":"qwen2"}')
        (self.model / "tokenizer_config.json").write_text('{"fixture":true}')
        self.adapter = self.root / "adapter"
        self.adapter.mkdir()
        (self.adapter / "adapter_config.json").write_text('{}')
        (self.adapter / "adapter_model.safetensors").write_bytes(b"CPU fixture, not model weights")
        self.out = self.root / "readout"
        self.lease = time.time() + 3600
        self.tokenizer = Tokenizer()
        context = patch.object(base, "native_tokenizer", return_value=self.tokenizer)
        context.start()
        self.addCleanup(context.stop)
        context = patch.object(base, "NativeBackend", side_effect=AssertionError("CPU tests cannot load native backend"))
        self.native = context.start()
        self.addCleanup(context.stop)

    def prepare(self, adapter=None, out=None):
        return readout.prepare(out or self.out, self.model, adapter, "0", self.lease)

    def captured(self, adapter=None, text=None):
        plan = self.prepare(adapter)
        data = self.out / "run" / "data"
        data.mkdir(parents=True)
        backend = Backend(plan, self.tokenizer, text)
        factory, closer = Mock(return_value=backend), Mock(return_value=True)
        readout.capture(plan, data, factory=factory, closer=closer)
        factory.assert_called_once_with(str(self.model), str(adapter) if adapter else None)
        closer.assert_called_once_with(backend.backend)
        stage = self.out / "run" / "worker"
        stage.mkdir()
        base.write_json(stage / "supervision.json", dict(ok=True, reservation_release_verified=True,
                        owned_group_empty=True, gpu_processes_absent=True, returncode=0, device="0",
                        reserved_seconds=1.0))
        return plan, data, backend

    def rewrite(self, path, value):
        path.write_bytes(base.encoded(value))

    def reseal(self, data):
        self.rewrite(data / "manifest.json", dict(files=base.tree_hashes(data, ("manifest.json",))))

    def test_fixed_selection_and_prompt_only_native_preparation(self):
        plan = self.prepare()
        evaluation = readout.corpus.build_candidate()["eval"]
        indexed = {row["id"]: row for row in evaluation}
        expected_ids = [f"eval-addition-{index:03d}" for index in range(32)] + [
            f"eval-memory-{index:03d}-0" for index in range(16)]
        self.assertEqual(plan["cases"], [indexed[case_id] for case_id in expected_ids])
        untouched = [row for row in evaluation if row["id"] not in expected_ids]
        self.assertEqual(len(untouched), 64)
        self.assertEqual(sum(row["kind"] == "addition" for row in untouched), 32)
        self.assertEqual(sum(row["kind"] == "memory_recall" for row in untouched), 16)
        self.assertEqual(sum(row["kind"] == "memory_unknown" for row in untouched), 16)
        self.assertEqual([row["prompt"] for row in plan["requests"]], [row["context"] for row in plan["cases"]])
        self.assertEqual(self.tokenizer.messages, [[{"role": "user", "content": row["context"]}]
                                                 for row in plan["cases"]])
        self.assertTrue(all(row["temperature"] == 0.0 and row["seed"] == 20260912 and row["max_tokens"] == 64
                            and "expected" not in row for row in plan["requests"]))
        self.assertTrue(all(row["id"] not in json.dumps(plan["requests"]) for row in untouched))
        self.assertEqual(plan["model_files"], base.model_hashes(self.model))
        self.assertEqual(plan["adapter_files"], {})
        self.assertIsNone(plan["adapter"])
        self.assertIs(type(plan["lease_end"]), float)
        self.assertEqual(plan["output_token_ceiling"], 3072)
        for name in (*base.SOURCE_FILES, "reasoning_neutral_probe.py", "fundamental_teaching_corpus.py",
                     "fundamental_teaching_readout.py"):
            self.assertIn(name, plan["source_hashes"])
        self.native.assert_not_called()

    def test_off_teach_control_have_identical_requests_and_rendering(self):
        off = self.prepare()
        teach = self.prepare(self.adapter, self.root / "teach")
        control_adapter = self.root / "control-adapter"
        control_adapter.mkdir()
        for name, content in (("adapter_config.json", b"{}"), ("adapter_model.safetensors", b"control")):
            (control_adapter / name).write_bytes(content)
        control = self.prepare(control_adapter, self.root / "control")
        for key in ("cases", "requests", "native_inputs", "model_files", "source_hashes"):
            self.assertEqual(off[key], teach[key])
            self.assertEqual(off[key], control[key])
        self.assertEqual(teach["adapter_files"], base.tree_hashes(self.adapter))
        self.assertEqual(teach["identity"]["adapter_input"], str(self.adapter))
        self.assertNotEqual(teach["adapter_files"], control["adapter_files"])

    def test_fresh_roots_and_no_model_adapter_overlap(self):
        self.prepare()
        pinned = (self.out / "plan.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        self.assertEqual((self.out / "plan.json").read_bytes(), pinned)
        with self.assertRaisesRegex(ValueError, "overlaps model"):
            self.prepare(out=self.model / "readout")
        with self.assertRaisesRegex(ValueError, "overlaps adapter"):
            self.prepare(self.adapter, self.adapter / "readout")
        with self.assertRaisesRegex(ValueError, "overlaps repository"):
            self.prepare(out=base.REPO / "readout-must-not-exist")

    def test_invalid_devices_lease_and_overlong_native_input(self):
        for device in ("0,1", "", "cuda:0"):
            with self.assertRaisesRegex(ValueError, "explicit device"):
                readout.prepare(self.out, self.model, None, device, self.lease)
        for lease in (float("nan"), float("inf"), time.time(), time.time() + 600):
            with self.assertRaisesRegex(ValueError, "insufficient lease"):
                readout.prepare(self.out, self.model, None, "0", lease)
        with patch.object(self.tokenizer, "encode", return_value=[1] * base.MAX_MODEL_LEN), \
             self.assertRaisesRegex(ValueError, "native context"):
            self.prepare()
        self.assertFalse((self.out / "plan.json").exists())
        self.native.assert_not_called()

    def test_complete_adapter_capture_reduces_with_raw_tokens_cost_and_cleanup(self):
        plan, data, backend = self.captured(self.adapter)
        result = readout.reduce(self.out)
        self.assertTrue(result["complete"] and result["native_token_text_audit"])
        self.assertEqual(result["counts"], dict(total=48, addition=dict(total=32, correct_action=32,
                         invalid_action=0, adherence=32), memory=dict(total=16, correct=16, invalid=0)))
        self.assertEqual(backend.seen, plan["requests"])
        self.assertEqual(len(list((data / "calls").iterdir())), 96)
        self.assertEqual(result["cost"]["readout"]["requests"], 48)
        self.assertEqual(result["cost"]["readout"]["output_token_ceiling"], 3072)
        self.assertGreater(result["cost"]["readout"]["native_input_tokens"], 0)
        self.assertGreater(result["cost"]["readout"]["native_output_tokens"], 0)
        self.assertIsNone(result["monetary_cost"])
        self.assertEqual(result["adapter_files"], plan["adapter_files"])
        response = base.read(data / "calls" / "0000.response.json")["response"]
        self.assertEqual(self.tokenizer.decode(response["output_token_ids"]), response["text"])
        self.assertEqual(self.tokenizer.encode(response["rendered_prompt"]), response["prompt_token_ids"])
        with self.assertRaises(FileExistsError):
            readout.reduce(self.out)

    def test_invalid_model_text_is_preserved_but_missing_response_is_not_zero(self):
        _, data, _ = self.captured(text="not an answer")
        result = readout.reduce(self.out)
        self.assertTrue(all(row["raw_text"] == "not an answer" for row in result["rows"]))
        self.assertEqual(result["counts"]["addition"]["invalid_action"], 32)
        self.assertEqual(result["counts"]["memory"]["invalid"], 16)
        self.assertTrue(result["complete"])
        (self.out / "reduction.json").unlink()
        (data / "calls" / "0047.response.json").unlink()
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "all 48"):
            readout.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_failure_stops_without_retry_and_preserves_raw_request(self):
        plan = self.prepare()
        data = self.root / "failed"
        data.mkdir()
        backend = Backend(plan, self.tokenizer)
        backend.generate = Mock(side_effect=RuntimeError("native failure"))
        closer = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "native failure"):
            readout.capture(plan, data, Mock(return_value=backend), closer)
        self.assertEqual(backend.generate.call_count, 1)
        closer.assert_called_once_with(backend.backend)
        self.assertTrue((data / "calls" / "0000.request.json").exists())
        self.assertFalse((data / "calls" / "0000.response.json").exists())
        self.assertFalse((data / "manifest.json").exists())
        self.assertTrue(base.read(data / "backend.cleanup.json")["closed"])
        with self.assertRaises(FileExistsError):
            readout.capture(plan, data, Mock(return_value=backend), closer)
        self.assertEqual(backend.generate.call_count, 1)

    def test_loader_failure_cleanup_failure_and_bad_native_response(self):
        plan = self.prepare()
        data = self.root / "load-failed"
        data.mkdir()
        closer = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "loader failure"):
            readout.capture(plan, data, Mock(side_effect=RuntimeError("loader failure")), closer)
        closer.assert_called_once_with(None)
        for name, closer, message in (("not-closed", Mock(return_value=False), "retain reservation"),
                                      ("close-error", Mock(side_effect=RuntimeError("close")), "retain reservation"),
                                      ("bad-response", Mock(return_value=True), "missing actual native token IDs")):
            with self.subTest(name=name):
                data = self.root / name
                data.mkdir()
                backend = Backend(plan, self.tokenizer)
                backend.generate = Mock(return_value={"text": "raw malformed native response"})
                with self.assertRaisesRegex(ValueError, message):
                    readout.capture(plan, data, Mock(return_value=backend), closer)
                self.assertTrue((data / "calls" / "0000.response.json").exists())
                self.assertFalse((data / "manifest.json").exists())
                self.assertEqual(backend.generate.call_count, 1)

    def test_plan_source_model_and_adapter_pins_are_verified(self):
        plan = self.prepare(self.adapter)
        changed = dict(plan["source_hashes"], unexpected="changed")
        with patch.object(readout, "sources", return_value=changed), self.assertRaisesRegex(ValueError, "source hashes"):
            readout.verify(self.out)
        (self.adapter / "extra.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "adapter hashes"):
            readout.verify(self.out)
        (self.adapter / "extra.json").unlink()
        (self.model / "config.json").write_text('{"model_type":"changed"}')
        with self.assertRaisesRegex(ValueError, "model hashes"):
            readout.verify(self.out)

    def test_capture_rejects_changed_identity_rendering_and_token_cap_without_retry(self):
        plan = self.prepare()
        for failure in ("identity", "rendering", "output_cap"):
            with self.subTest(failure=failure):
                data = self.root / failure
                data.mkdir()
                backend = Backend(plan, self.tokenizer)
                response = backend.generate(plan["requests"][0])
                if failure == "identity":
                    backend.identity = Mock(return_value={"unexpected": True})
                elif failure == "rendering":
                    response["rendered_prompt"] += "appended reminder"
                else:
                    response["output_token_ids"] = [1] * 65
                backend.generate = Mock(return_value=response)
                closer = Mock(return_value=True)
                with self.assertRaises(ValueError):
                    readout.capture(plan, data, Mock(return_value=backend), closer)
                closer.assert_called_once_with(backend.backend)
                self.assertEqual(backend.generate.call_count, 0 if failure == "identity" else 1)
                self.assertFalse((data / "manifest.json").exists())

    def test_resealed_plan_cannot_change_selection_sampling_or_native_inputs(self):
        plan = self.prepare()
        for key in ("cases", "requests", "native_inputs"):
            with self.subTest(key=key):
                changed = copy.deepcopy(plan)
                if key == "cases":
                    changed[key].pop()
                elif key == "requests":
                    changed[key][0]["temperature"] = 0.7
                else:
                    changed[key][0]["prompt_token_ids"].append(1)
                self.rewrite(self.out / "plan.json", changed)
                self.rewrite(self.out / "plan.sha256.json", dict(sha256=base.digest(self.out / "plan.json")))
                with self.assertRaises(ValueError):
                    readout.verify(self.out)

    def test_native_output_input_rendering_and_request_audits(self):
        _, data, _ = self.captured()
        response_path = data / "calls" / "0000.response.json"
        original = base.read(response_path)
        for field, value, message in (("output_token_ids", [ord("?")], "output token mismatch"),
                                      ("prompt_token_ids", [1], "input token mismatch"),
                                      ("rendered_prompt", "injected", "rendered source prompt mismatch")):
            with self.subTest(field=field):
                received = copy.deepcopy(original)
                received["response"][field] = value
                received["response_sha256"] = base.value_hash(received["response"])
                self.rewrite(response_path, received)
                self.reseal(data)
                with self.assertRaisesRegex(ValueError, message):
                    readout.reduce(self.out)
                self.assertFalse((self.out / "reduction.json").exists())
        self.rewrite(response_path, original)
        request_path = data / "calls" / "0000.request.json"
        sent = base.read(request_path)
        sent["request"]["prompt"] += "\nRemember to predict."
        sent["prompt_sha256"] = base.value_hash(sent["request"]["prompt"])
        self.rewrite(request_path, sent)
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "raw receipt binding"):
            readout.reduce(self.out)

    def test_capture_manifest_and_supervisor_cleanup_are_required(self):
        _, data, _ = self.captured()
        (data / "unexpected.txt").write_text("changed capture")
        with self.assertRaisesRegex(ValueError, "capture changed"):
            readout.reduce(self.out)
        (data / "unexpected.txt").unlink()
        path = self.out / "run" / "worker" / "supervision.json"
        receipt = base.read(path)
        for field in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent"):
            self.rewrite(path, dict(receipt, **{field: False}))
            with self.assertRaisesRegex(ValueError, "supervision/cleanup"):
                readout.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_run_requires_opt_in_uses_one_supervisor_and_cannot_retry(self):
        with patch.object(readout, "verify") as verify, self.assertRaisesRegex(ValueError, "allow-gpu"):
            readout.run(self.out)
        verify.assert_not_called()
        self.prepare()
        with patch.object(base, "supervise", return_value={"ok": True}) as supervise:
            self.assertEqual(readout.run(self.out, allow_gpu=True), {"ok": True})
            self.assertEqual(supervise.call_count, 1)
            args = supervise.call_args.args
            self.assertEqual(args[2], self.out / "run" / "worker")
            self.assertEqual(args[4], self.out / "run" / "data" / "calls")
            self.assertIn("organism_v6.fundamental_teaching_readout", args[3])
            self.assertEqual(args[1]["worker_seconds"], base.WORKER_SECONDS)
            self.assertEqual(base.WORKER_SECONDS, 600)
            with self.assertRaisesRegex(ValueError, "already exists"):
                readout.run(self.out, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)
        self.native.assert_not_called()

    def test_parent_loss_watch_signals_only_owned_group_and_restores_handlers(self):
        plan = self.prepare()
        stage = self.out / "run" / "worker"
        stage.mkdir(parents=True)
        base.write_json(stage / "process.json", dict(pid=4242))
        stopped, thread = Mock(), Mock()
        stopped.wait.return_value = False

        def start_thread(target, daemon):
            thread.start.side_effect = target
            return thread

        with patch.object(readout, "verify", return_value=(plan, [])), \
             patch.object(base.supervisor, "selected_device", return_value="0"), \
             patch.object(os, "getpid", return_value=4242), patch.object(os, "getpgrp", return_value=4242), \
             patch.object(os, "getppid", side_effect=[7, 7, 8]), patch.object(os, "killpg") as kill, \
             patch.object(signal, "signal") as handlers, patch.object(readout, "capture") as capture, \
             patch.object(readout.threading, "Event", return_value=stopped), \
             patch.object(readout.threading, "Thread", side_effect=start_thread):
            readout.worker(self.out)
        kill.assert_called_once_with(4242, signal.SIGTERM)
        stopped.set.assert_called_once()
        thread.join.assert_called_once()
        self.assertEqual(handlers.call_count, 4)
        capture.assert_called_once()

    def test_unowned_worker_cannot_construct_backend_or_capture(self):
        plan = self.prepare()
        stage = self.out / "run" / "worker"
        stage.mkdir(parents=True)
        base.write_json(stage / "process.json", dict(pid=4242))
        with patch.object(readout, "verify", return_value=(plan, [])), \
             patch.object(base.supervisor, "selected_device", return_value="0"), \
             patch.object(os, "getpid", return_value=4242), patch.object(os, "getpgrp", return_value=9000), \
             patch.object(os, "getppid", return_value=7), patch.object(readout, "capture") as capture, \
             self.assertRaisesRegex(ValueError, "supervisor ownership"):
            readout.worker(self.out)
        capture.assert_not_called()
        self.native.assert_not_called()


if __name__ == "__main__":
    unittest.main()
