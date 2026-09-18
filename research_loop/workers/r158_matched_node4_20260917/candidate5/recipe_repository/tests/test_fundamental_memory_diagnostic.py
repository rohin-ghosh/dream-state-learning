"""CPU fixtures only; no native model, GPU, network, or scientific outcomes."""
import copy
from collections import Counter
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from organism_v6 import fundamental_memory_diagnostic as diagnostic


base = diagnostic.base


class Tokenizer:
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        if tokenize is not False or add_generation_prompt is not True or len(messages) != 1:
            raise AssertionError("single native user prompt required")
        if set(messages[0]) != {"role", "content"} or messages[0]["role"] != "user":
            raise AssertionError("no answers or extra messages allowed")
        return "<user>" + messages[0]["content"] + "</user><assistant>"

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
        text = self.text if self.text is not None else self.plan["cases"][int(request["call_id"])]["expected"]
        rendered = self.tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                      tokenize=False, add_generation_prompt=True)
        return dict(text=text, rendered_prompt=rendered, prompt_token_ids=self.tokenizer.encode(rendered),
                    output_token_ids=self.tokenizer.encode(text), finish_reason="stop", stop_reason=None)


class SelectionTests(unittest.TestCase):
    def test_exact_original_training_contexts_and_source_colors(self):
        candidate = diagnostic.corpus.build_candidate()
        cases = diagnostic.selected_cases()
        self.assertEqual(len(cases), 16)
        self.assertEqual([case["id"] for case in cases], list(diagnostic.CASE_IDS))
        self.assertEqual({case["device"] for case in cases}, {f"device-{index:03d}" for index in range(16)})
        self.assertEqual(Counter(case["expected"] for case in cases), dict.fromkeys(diagnostic.corpus.COLORS, 4))
        for case in cases:
            for arm in ("teach", "control"):
                original = next(row for row in candidate[f"train_{arm}"] if row["case_id"] == case["id"])
                self.assertEqual(case["context"], original["context"])
                self.assertEqual(case["expected"], original["response"])
                self.assertIn(original["id"], case["training_record_ids"])
                self.assertEqual(case["source_event_ids"], original["source_event_ids"])
            self.assertIn(case["source_record"], candidate["source_records"])
            self.assertEqual(case["source_record"]["color"], case["expected"])

    def test_requests_have_no_answers_reminders_or_confirmation_cases(self):
        cases = diagnostic.selected_cases()
        requests = diagnostic.requests(cases)
        self.assertEqual([request["call_id"] for request in requests], [f"{index:04d}" for index in range(16)])
        evaluation = diagnostic.corpus.build_candidate()["eval"]
        for case, request in zip(cases, requests, strict=True):
            self.assertEqual(set(request), {"call_id", "case_id", "role", "arm", "prompt",
                                            "temperature", "seed", "max_tokens"})
            self.assertEqual(request["prompt"], case["context"])
            self.assertNotIn(request["prompt"], [row["context"] for row in evaluation])
            self.assertEqual((request["temperature"], request["seed"], request["max_tokens"]), (0.0, 20260912, 64))
            for forbidden in (*diagnostic.corpus.COLORS, "unknown", "Remember", "PREDICT", "ACT", "answer:"):
                self.assertNotIn(forbidden, request["prompt"])
        self.assertEqual(sum(request["max_tokens"] for request in requests), 1024)

    def test_selection_rejects_missing_duplicate_or_additional_memory_cases(self):
        for mutation in ("missing", "duplicate", "extra"):
            with self.subTest(mutation=mutation):
                candidate = diagnostic.corpus.build_candidate()
                memory = next(row for row in candidate["train_teach"] if row["kind"] == "memory")
                if mutation == "missing":
                    candidate["train_teach"].remove(memory)
                else:
                    extra = copy.deepcopy(memory)
                    if mutation == "extra":
                        extra["case_id"] = "train-memory-016"
                    candidate["train_teach"].append(extra)
                with patch.object(diagnostic.corpus, "build_candidate", return_value=candidate), \
                     self.assertRaisesRegex(ValueError, "exactly 16"):
                    diagnostic.selected_cases()

    def test_selection_rejects_wrong_targets_sources_and_answer_bearing_contexts(self):
        for field, value in (("response", "unknown"), ("source_event_ids", ["source-memory-015"]),
                             ("device", "device-999"), ("context", "Remember: the answer is red."),
                             ("id", "incorrect-record-id")):
            with self.subTest(field=field):
                candidate = diagnostic.corpus.build_candidate()
                memory = next(row for row in candidate["train_control"] if row["case_id"] == "train-memory-000")
                memory[field] = value
                with patch.object(diagnostic.corpus, "build_candidate", return_value=candidate), \
                     self.assertRaisesRegex(ValueError, "binding differs"):
                    diagnostic.selected_cases()

    def test_selection_rejects_duplicate_or_mismatched_source_records(self):
        for mutation in ("duplicate", "device", "color"):
            with self.subTest(mutation=mutation):
                candidate = diagnostic.corpus.build_candidate()
                event = next(row for row in candidate["source_records"] if row["id"] == "source-memory-000")
                if mutation == "duplicate":
                    candidate["source_records"].append(copy.deepcopy(event))
                else:
                    event[mutation] = "wrong"
                with patch.object(diagnostic.corpus, "build_candidate", return_value=candidate), \
                     self.assertRaises(ValueError):
                    diagnostic.selected_cases()

    def test_no_modified_selection_and_fixed_dev_endpoint_unchanged(self):
        primary = copy.deepcopy(diagnostic.readout.selected_cases())
        requests = diagnostic.readout.requests(primary)
        for alteration in ("reverse", "subset", "expected", "context"):
            with self.subTest(alteration=alteration):
                cases = diagnostic.selected_cases()
                if alteration == "reverse":
                    cases.reverse()
                elif alteration == "subset":
                    cases.pop()
                else:
                    cases[0][alteration] = "wrong"
                with self.assertRaisesRegex(ValueError, "selection differs"):
                    diagnostic.requests(cases)
        self.assertEqual(len(primary), 48)
        self.assertEqual(diagnostic.readout.selected_cases(), primary)
        self.assertEqual(diagnostic.readout.requests(primary), requests)
        self.assertIs(diagnostic.capture, diagnostic.readout.capture)
        self.assertIs(diagnostic.native_inputs, diagnostic.readout.native_inputs)
        self.assertIs(diagnostic.score_memory, diagnostic.readout.score_memory)

    def test_shared_score_memory_keeps_raw_and_rejects_explanations(self):
        for text, valid, correct in ((" red.\n", True, True), ("BLUE", True, False),
                                     ("red..", False, False), ("The answer is red", False, False),
                                     ("red\nblue", False, False), ("", False, False)):
            with self.subTest(text=text):
                score = diagnostic.score_memory(text, "red")
                self.assertEqual((score["valid"], score["correct"]), (valid, correct))
                self.assertEqual(score["raw_text"], text)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fundamental-memory-fixture-", dir="/tmp")
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
        self.out = self.root / "diagnostic"
        self.tokenizer = Tokenizer()
        self.lease = time.time() + 3600
        context = patch.object(base, "native_tokenizer", return_value=self.tokenizer)
        context.start()
        self.addCleanup(context.stop)
        for name in ("NativeBackend", "supervise"):
            context = patch.object(base, name, side_effect=AssertionError("CPU fixture must not launch native work"))
            context.start()
            self.addCleanup(context.stop)

    def prepare(self, adapter=None, out=None):
        return diagnostic.prepare(out or self.out, self.model, adapter, "0", self.lease)

    def captured(self, adapter=None, text=None):
        plan = self.prepare(adapter)
        data, stage = self.out / "run" / "data", self.out / "run" / "worker"
        data.mkdir(parents=True)
        stage.mkdir()
        started = time.monotonic()
        base.write_json(stage / "process.json", dict(pid=os.getpid(), pgid=os.getpid(),
                        argv=diagnostic.worker_command(self.out), device="0", timeout=600, started=started))
        backend = Backend(plan, self.tokenizer, text)
        factory, closer = Mock(return_value=backend), Mock(return_value=True)
        diagnostic.capture(plan, data, factory=factory, closer=closer)
        factory.assert_called_once_with(str(self.model), str(adapter) if adapter else None)
        closer.assert_called_once_with(backend.backend)
        base.write_json(stage / "supervision.json", dict(ok=True, reservation_release_verified=True,
                        owned_group_empty=True, gpu_processes_absent=True, returncode=0, device="0",
                        reserved_seconds=time.monotonic() - started))
        return plan, data, backend

    def rewrite(self, path, value):
        path.write_bytes(base.encoded(value))

    def reseal(self, data):
        self.rewrite(data / "manifest.json", dict(files=base.tree_hashes(data, ("manifest.json",))))

    def rewrite_plan(self, plan):
        self.rewrite(self.out / "plan.json", plan)
        self.rewrite(self.out / "plan.sha256.json", dict(sha256=base.digest(self.out / "plan.json")))

    def test_off_and_adapter_requests_native_inputs_and_sources_match(self):
        off = self.prepare()
        on = self.prepare(self.adapter, self.root / "on")
        for key in ("requests", "cases", "native_inputs", "source_hashes", "corpus_sha256"):
            self.assertEqual(off[key], on[key])
        self.assertNotEqual(off["identity"], on["identity"])
        self.assertEqual(off["label"], diagnostic.LABEL)
        self.assertEqual(off["output_token_ceiling"], 1024)
        self.assertEqual(off["source_hashes"]["fundamental_memory_diagnostic"], base.digest(Path(diagnostic.__file__)))
        for request, native in zip(off["requests"], off["native_inputs"], strict=True):
            self.assertEqual(native["rendered_prompt"], "<user>" + request["prompt"] + "</user><assistant>")
        self.assertEqual(diagnostic.verify(self.out), (off, off["cases"]))

    def test_fresh_roots_and_model_adapter_overlap(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        for destination, adapter in ((self.model / "out", None), (self.adapter / "out", self.adapter),
                                     (self.root, self.adapter), (base.REPO / "forbidden-diagnostic", None)):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                self.prepare(adapter, destination)

    def test_invalid_model_adapter_device_lease_and_native_length(self):
        for device, lease in (("0,1", self.lease), ("-1", self.lease), ("", self.lease),
                              ("0", time.time()), ("0", float("nan")), ("0", float("inf"))):
            with self.subTest(device=device, lease=lease), self.assertRaises(ValueError):
                diagnostic.prepare(self.out, self.model, None, device, lease)
        (self.model / "config.json").write_text('{"model_type":"other"}')
        with self.assertRaisesRegex(ValueError, "Qwen"):
            self.prepare()
        (self.model / "config.json").write_text('{"model_type":"qwen2"}')
        (self.adapter / "adapter_model.safetensors").unlink()
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            self.prepare(self.adapter, self.root / "bad-adapter")
        with patch.object(self.tokenizer, "encode", return_value=[1] * base.MAX_MODEL_LEN), \
             self.assertRaisesRegex(ValueError, "native context"):
            self.prepare()

    def test_complete_capture_preserves_raw_outputs_tokens_counts_and_custody(self):
        plan, data, backend = self.captured(self.adapter)
        result = diagnostic.reduce(self.out)
        self.assertEqual(backend.seen, plan["requests"])
        self.assertEqual(result["counts"], dict(total=16, correct=16, invalid=0,
                                              answer_counts=dict.fromkeys(diagnostic.corpus.COLORS, 4)))
        self.assertEqual(result["label"], diagnostic.LABEL)
        self.assertTrue(result["native_token_text_audit"])
        self.assertEqual(result["identity"], plan["identity"])
        self.assertEqual(result["cost"], base.usage(data))
        self.assertEqual(result["cost"]["memory_diagnostic"]["requests"], 16)
        self.assertEqual(result["cost"]["memory_diagnostic"]["output_token_ceiling"], 1024)
        self.assertLess(result["cost"]["memory_diagnostic"]["native_output_tokens"], 1024)
        self.assertGreater(result["reserved_seconds"], 0)
        self.assertIsNone(result["monetary_cost"])
        for row, case in zip(result["rows"], plan["cases"], strict=True):
            self.assertEqual(row["raw_text"], case["expected"])
            self.assertEqual(row["source_event_ids"], case["source_event_ids"])
        for field, path in (("process_sha256", self.out / "run" / "worker" / "process.json"),
                            ("supervision_sha256", self.out / "run" / "worker" / "supervision.json"),
                            ("capture_sha256", data / "manifest.json")):
            self.assertEqual(result[field], base.digest(path))
        self.assertEqual(base.read(self.out / "reduction.json"), result)
        with self.assertRaises(FileExistsError):
            diagnostic.reduce(self.out)

    def test_literal_red_counts_four_and_does_not_select_favorable_subset(self):
        _, _, backend = self.captured(text="red")
        result = diagnostic.reduce(self.out)
        self.assertEqual(len(backend.seen), 16)
        self.assertEqual(result["counts"], dict(total=16, correct=4, invalid=0, answer_counts={"red": 16}))
        self.assertEqual([row["raw_text"] for row in result["rows"]], ["red"] * 16)

    def test_completed_malformed_response_can_score_zero(self):
        self.captured(text="The answer is red.")
        result = diagnostic.reduce(self.out)
        self.assertEqual(result["counts"], dict(total=16, correct=0, invalid=16, answer_counts={}))
        self.assertTrue(all(row["raw_text"] == "The answer is red." for row in result["rows"]))

    def test_missing_response_is_not_a_zero_even_if_manifest_resealed(self):
        _, data, _ = self.captured()
        (data / "calls" / "0007.response.json").unlink()
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "all 16"):
            diagnostic.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_missing_request_extra_pair_and_duplicate_request_rejected(self):
        _, data, _ = self.captured()
        path = data / "calls" / "0007.request.json"
        original = path.read_bytes()
        path.unlink()
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "all 16"):
            diagnostic.reduce(self.out)
        path.write_bytes(original)
        extra = data / "calls" / "0016.response.json"
        extra.write_bytes((data / "calls" / "0000.response.json").read_bytes())
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "all 16"):
            diagnostic.reduce(self.out)
        extra.unlink()
        path.write_bytes((data / "calls" / "0000.request.json").read_bytes())
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "binding changed"):
            diagnostic.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_source_model_adapter_and_plan_hash_pins(self):
        plan = self.prepare(self.adapter)
        with patch.object(diagnostic, "sources", return_value={}), self.assertRaisesRegex(ValueError, "source/corpus"):
            diagnostic.verify(self.out)
        for source_path, message in ((self.model / "config.json", "model hashes"),
                                      (self.adapter / "adapter_model.safetensors", "adapter hashes")):
            original = source_path.read_bytes()
            source_path.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, message):
                diagnostic.verify(self.out)
            source_path.write_bytes(original)
        self.rewrite(self.out / "plan.json", dict(plan, schema=2))
        with self.assertRaisesRegex(ValueError, "plan changed"):
            diagnostic.verify(self.out)

    def test_resealed_plan_cannot_change_sources_cases_sampling_or_native_inputs(self):
        original = self.prepare(self.adapter)
        for mutation in ("source_hashes", "corpus_sha256", "cases", "requests", "native_inputs", "label",
                         "identity", "worker_seconds", "output_token_ceiling", "device", "claim_limits"):
            with self.subTest(mutation=mutation):
                plan = copy.deepcopy(original)
                if mutation == "cases":
                    plan[mutation][0]["expected"] = "unknown"
                elif mutation == "requests":
                    plan[mutation][0]["seed"] += 1
                elif mutation == "native_inputs":
                    plan[mutation][0]["prompt_token_ids"].append(1)
                elif mutation in ("identity", "source_hashes"):
                    plan[mutation] = {}
                elif mutation in ("worker_seconds", "output_token_ceiling"):
                    plan[mutation] += 1
                else:
                    plan[mutation] = "changed"
                self.rewrite_plan(plan)
                with self.assertRaises(ValueError):
                    diagnostic.verify(self.out)

    def test_native_text_tokens_prompt_and_hash_audits(self):
        _, data, _ = self.captured()
        path = data / "calls" / "0000.response.json"
        original = base.read(path)
        for field, value in (("text", "changed"), ("output_token_ids", [1]), ("prompt_token_ids", [1]),
                             ("rendered_prompt", "answer leak"), ("output_token_ids", [1] * 65)):
            with self.subTest(field=field, value=value):
                receipt = copy.deepcopy(original)
                receipt["response"][field] = value
                receipt["response_sha256"] = base.value_hash(receipt["response"])
                self.rewrite(path, receipt)
                self.reseal(data)
                with self.assertRaises(ValueError):
                    diagnostic.reduce(self.out)
        receipt = dict(original, response_sha256="wrong")
        self.rewrite(path, receipt)
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "binding changed"):
            diagnostic.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_capture_identity_request_hash_and_timing_are_bound(self):
        _, data, _ = self.captured()
        identity_path = data / "identity.json"
        identity = base.read(identity_path)
        self.rewrite(identity_path, {})
        self.reseal(data)
        with self.assertRaisesRegex(ValueError, "capture identity"):
            diagnostic.reduce(self.out)
        self.rewrite(identity_path, identity)
        path = data / "calls" / "0001.request.json"
        original = base.read(path)
        for field, value in (("identity", {}), ("prompt_sha256", "wrong"), ("started", 0.0), ("started", 1e99)):
            with self.subTest(field=field, value=value):
                self.rewrite(path, dict(original, **{field: value}))
                self.reseal(data)
                with self.assertRaises(ValueError):
                    diagnostic.reduce(self.out)

    def test_missing_native_response_fields_never_become_scores(self):
        _, data, _ = self.captured()
        path = data / "calls" / "0000.response.json"
        original = base.read(path)
        for field in ("text", "prompt_token_ids", "output_token_ids", "rendered_prompt"):
            with self.subTest(field=field):
                receipt = copy.deepcopy(original)
                del receipt["response"][field]
                receipt["response_sha256"] = base.value_hash(receipt["response"])
                self.rewrite(path, receipt)
                self.reseal(data)
                with self.assertRaises(ValueError):
                    diagnostic.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_manifest_failure_usage_cleanup_and_native_ready_receipts_required(self):
        _, data, _ = self.captured()
        extra = data / "unexpected.txt"
        extra.write_text("changed")
        with self.assertRaisesRegex(ValueError, "capture changed"):
            diagnostic.reduce(self.out)
        extra.unlink()
        for name, receipt, message in (("failure.json", {}, "backend failed"),
                                       ("usage.json", {}, "usage receipt"),
                                       ("backend.cleanup.json", {"closed": False}, "cleanup"),
                                       ("backend.ready.json", {"pid": -1, "ready": 0}, "custody")):
            with self.subTest(name=name):
                path = data / name
                original = path.read_bytes() if path.exists() else None
                self.rewrite(path, receipt)
                self.reseal(data)
                with self.assertRaisesRegex(ValueError, message):
                    diagnostic.reduce(self.out)
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_supervision_and_process_custody_fail_closed(self):
        self.captured()
        stage = self.out / "run" / "worker"
        path = stage / "supervision.json"
        original = base.read(path)
        for field, value in (("ok", False), ("reservation_release_verified", False),
                             ("owned_group_empty", False), ("gpu_processes_absent", False),
                             ("returncode", 1), ("device", "1"), ("reserved_seconds", -1)):
            with self.subTest(field=field):
                self.rewrite(path, dict(original, **{field: value}))
                with self.assertRaises(ValueError):
                    diagnostic.reduce(self.out)
        self.rewrite(path, original)
        path = stage / "process.json"
        original = base.read(path)
        for field, value in (("pid", -1), ("pgid", -1), ("argv", []), ("device", "1"),
                             ("timeout", 601), ("started", -1)):
            with self.subTest(field=field):
                self.rewrite(path, dict(original, **{field: value}))
                with self.assertRaises(ValueError):
                    diagnostic.reduce(self.out)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            diagnostic.reduce(self.out)
        self.assertFalse((self.out / "reduction.json").exists())

    def test_capture_failure_preserves_partial_receipts_without_retry(self):
        plan = self.prepare()
        data = self.root / "failed-data"
        data.mkdir()
        backend = Backend(plan, self.tokenizer)
        backend.generate = Mock(side_effect=RuntimeError("fixture generation failed"))
        closer = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "fixture generation failed"):
            diagnostic.capture(plan, data, factory=Mock(return_value=backend), closer=closer)
        backend.generate.assert_called_once()
        closer.assert_called_once_with(backend.backend)
        self.assertTrue((data / "calls" / "0000.request.json").exists())
        self.assertFalse((data / "calls" / "0000.response.json").exists())
        self.assertTrue((data / "failure.json").exists())
        self.assertFalse((data / "manifest.json").exists())
        with self.assertRaises(FileExistsError):
            diagnostic.capture(plan, data, factory=Mock(return_value=backend), closer=closer)

    def test_capture_rejects_wrong_identity_native_input_and_failed_cleanup(self):
        plan = self.prepare()
        for mutation in ("identity", "native_input", "cleanup"):
            with self.subTest(mutation=mutation):
                data = self.root / mutation
                data.mkdir()
                backend = Backend(plan, self.tokenizer)
                if mutation == "identity":
                    backend.identity = Mock(return_value={})
                elif mutation == "native_input":
                    response = backend.generate(plan["requests"][0])
                    response["rendered_prompt"] = "wrong"
                    backend.generate = Mock(return_value=response)
                with self.assertRaises(ValueError):
                    diagnostic.capture(plan, data, factory=Mock(return_value=backend),
                                       closer=Mock(return_value=mutation != "cleanup"))
                self.assertFalse((data / "manifest.json").exists())

    def test_run_is_opt_in_supervised_separate_and_cannot_retry(self):
        with patch.object(diagnostic, "verify") as verify, self.assertRaisesRegex(ValueError, "allow-gpu"):
            diagnostic.run(self.out)
        verify.assert_not_called()
        self.prepare()
        with patch.object(base, "supervise", return_value={"ok": True}) as supervise:
            self.assertEqual(diagnostic.run(self.out, allow_gpu=True), {"ok": True})
            args = supervise.call_args.args
            self.assertEqual(args[2], self.out / "run" / "worker")
            self.assertEqual(args[3], diagnostic.worker_command(self.out))
            self.assertEqual(args[4], self.out / "run" / "data" / "calls")
            self.assertIn("organism_v6.fundamental_memory_diagnostic", args[3])
            self.assertEqual(len(args[1]["requests"]), 16)
            with self.assertRaisesRegex(ValueError, "already exists"):
                diagnostic.run(self.out, allow_gpu=True)
            self.assertEqual(supervise.call_count, 1)

    def test_worker_rejects_unowned_process_before_capture(self):
        plan = self.prepare()
        stage = self.out / "run" / "worker"
        stage.mkdir(parents=True)
        base.write_json(stage / "process.json", dict(pid=4242, pgid=9000, device="0",
                        argv=diagnostic.worker_command(self.out)))
        with patch.object(diagnostic, "verify", return_value=(plan, [])), \
             patch.object(base.supervisor, "selected_device", return_value="0"), \
             patch.object(os, "getpid", return_value=4242), patch.object(os, "getpgrp", return_value=4242), \
             patch.object(os, "getppid", return_value=7), patch.object(diagnostic, "capture") as capture, \
             self.assertRaisesRegex(ValueError, "supervisor ownership"):
            diagnostic.worker(self.out)
        capture.assert_not_called()

    def test_parent_loss_signals_only_owned_group_and_restores_handlers(self):
        plan = self.prepare()
        stage = self.out / "run" / "worker"
        stage.mkdir(parents=True)
        base.write_json(stage / "process.json", dict(pid=4242, pgid=4242, device="0",
                        argv=diagnostic.worker_command(self.out)))
        stopped, thread = Mock(), Mock()
        stopped.wait.return_value = False

        def start_thread(target, daemon):
            thread.start.side_effect = target
            return thread

        with patch.object(diagnostic, "verify", return_value=(plan, [])), \
             patch.object(base.supervisor, "selected_device", return_value="0"), \
             patch.object(os, "getpid", return_value=4242), patch.object(os, "getpgrp", return_value=4242), \
             patch.object(os, "getppid", side_effect=[7, 7, 8]), patch.object(os, "killpg") as kill, \
             patch.object(signal, "signal") as handlers, patch.object(diagnostic, "capture") as capture, \
             patch.object(diagnostic.threading, "Event", return_value=stopped), \
             patch.object(diagnostic.threading, "Thread", side_effect=start_thread):
            diagnostic.worker(self.out)
        kill.assert_called_once_with(4242, signal.SIGTERM)
        stopped.set.assert_called_once()
        thread.join.assert_called_once()
        self.assertEqual(handlers.call_count, 4)
        capture.assert_called_once()

    def test_cli_requires_explicit_gpu_permission_and_preparation_inputs(self):
        with self.assertRaisesRegex(ValueError, "--out, --model"):
            diagnostic.main(["prepare"])
        with patch.object(diagnostic, "worker") as worker, self.assertRaisesRegex(ValueError, "allow-gpu"):
            diagnostic.main(["_worker", "--root", str(self.out)])
        worker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
