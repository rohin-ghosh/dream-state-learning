import copy
from collections import Counter
import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from organism_v6 import semantic_carrier_diagnostic as carrier
from organism_v6 import multikey_writer_gateway_simple as w0


class Tokenizer(w0.FixtureTokenizer):
    tokenizer = property(lambda self: self)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert not tokenize and add_generation_prompt and len(messages) == 1
        return "<user>\n" + messages[0]["content"] + "</user>\n<assistant>\n"

    def decode(self, ids):
        return "".join("<eos>" if token == 0 else chr(token - 1) for token in ids)


class SemanticCarrierTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()
        self.requests = carrier.build_requests(self.tokenizer)

    def records(self):
        records = []
        for request in self.requests:
            audit = request["audit"]
            record = dict(request_id=request["request_id"], request_sha256=w0.digest(request))
            if request["operation"] == "score":
                record["token_logprobs"] = [[-.01 if index == audit["expected"] else -1.] * len(row["response_ids"])
                                           for index, row in enumerate(request["candidates"])]
            else:
                action = carrier.ACTIONS[audit["expected"]] if isinstance(audit["expected"], int) else audit["expected"]
                text = f"ACT: {action}\n"
                ids = self.tokenizer(text)["input_ids"] + [0]
                record.update(text=text, generated_ids=ids, eos_terminated=True, truncated=False,
                              decoded_with_terminal_eos=self.tokenizer.decode(ids))
            records.append(record)
        return records

    def test_balanced_four_cells_and_only_correct_row_changes(self):
        counts, pairs = {}, {}
        for item in carrier.build_items():
            if item["kind"] != "semantic_exact_row_carrier":
                continue
            counts.setdefault((item["root"], item["mapping"]), Counter())[item["expected"]] += 1
            pairs.setdefault(item["pair_id"], []).append(item)
        self.assertEqual(len(counts), 4)
        self.assertTrue(all(value == {0: 8, 1: 8} for value in counts.values()))
        self.assertEqual(len(pairs), 32)
        for plus, minus in pairs.values():
            self.assertEqual(plus["expected"], 1 - minus["expected"])
            left, right = plus["prompt"].splitlines(), minus["prompt"].splitlines()
            self.assertEqual([index for index, (first, second) in enumerate(zip(left, right)) if first != second], [2])
            self.assertEqual(left[2].split(" -> ")[0], right[2].split(" -> ")[0])
            self.assertTrue(plus["prompt"].endswith("\n"))

    def test_no_audit_leak_and_same_chat_prefix_for_both_operations(self):
        pairs = {}
        for request in self.requests:
            payload = request["payload"]
            self.assertEqual(set(payload), {"prompt", "rendered_prompt", "prompt_input_ids", "max_new_tokens", "do_sample", "seed"})
            self.assertNotIn("W+", payload["prompt"])
            self.assertNotIn("W-", payload["prompt"])
            self.assertNotIn("semroot_", payload["prompt"])
            self.assertNotIn("a0", payload["prompt"].splitlines()[0])
            if request["audit"]["kind"] == "semantic_exact_row_carrier":
                self.assertEqual(payload["prompt"].count(" -> ACT:"), 1)
                key = (request["audit"]["pair_id"], request["audit"]["mapping"])
                pairs.setdefault(key, []).append(payload)
        self.assertTrue(all(first == second for first, second in pairs.values()))
        self.assertEqual(len(self.requests), 144)
        self.assertEqual(carrier.build_material(), carrier.build_material())

    def test_complete_candidate_masks_include_lf_and_eos_unequal_lengths(self):
        request = next(row for row in self.requests if row["operation"] == "score")
        counts = []
        for candidate in request["candidates"]:
            prefix = request["payload"]["prompt_input_ids"]
            self.assertEqual(candidate["input_ids"][:len(prefix)], prefix)
            self.assertEqual(candidate["labels"][:len(prefix)], [-100] * len(prefix))
            self.assertEqual(candidate["labels"][len(prefix):], candidate["response_ids"])
            self.assertEqual(candidate["response_ids"][-2:], [ord("\n") + 1, 0])
            counts.append(len(candidate["response_ids"]))
        self.assertNotEqual(*counts)
        altered = list(prefix)
        altered[-1] += 1
        with self.assertRaisesRegex(w0.ContractError, "prefix"):
            carrier.encode_candidate(self.tokenizer, request["payload"]["rendered_prompt"], altered, carrier.CANDIDATES[0])

    def test_candidate_boundary_straddle_rejected(self):
        tokenizer = Tokenizer()
        original = tokenizer.__class__.__call__

        def straddle(instance, text, **kwargs):
            encoded = original(instance, text, **kwargs)
            encoded["input_ids"][1:3] = [999]
            encoded["offset_mapping"][1:3] = [(1, 3)]
            return encoded

        with patch.object(Tokenizer, "__call__", straddle):
            with self.assertRaisesRegex(w0.ContractError, "boundary straddle"):
                carrier.encode_candidate(tokenizer, "xx", [121, 121], carrier.CANDIDATES[0])

    def test_strict_output_no_repairs_unicode_or_unterminated_response(self):
        for text in ("ACT: a0", "ACT: -gvn\nexplanation", "ACT: -gvn ACT: -mem2reg",
                     "\u00a0ACT: -gvn", "```ACT: -gvn```", "ACT: -gvn\x00"):
            self.assertIsNone(carrier.strict_output(text)["action"])
        self.assertEqual(carrier.strict_output(" \r\nACT: -gvn\t")["action"], "-gvn")
        self.assertIsNone(carrier.strict_output("ACT: -gvn", truncated=True)["action"])
        self.assertIsNone(carrier.strict_output("ACT: -gvn", eos_terminated=False)["action"])
        self.assertTrue(carrier.strict_output("ACT: -gvn ACT: -gvn")["multiple"])

    def test_all_cell_conjunction_and_candidate_not_generation_rescue(self):
        records = self.records()
        report = carrier.reduce_records(self.requests, records, self.tokenizer)
        self.assertEqual(report["label"], "SEMANTIC_EXACT_ROW_SURFACE_OK")
        self.assertEqual(report["complementary_swaps"], {"generate": 32, "score": 32})
        self.assertEqual(report["native_copy_correct"], {"0": 8, "1": 8})
        targets = [index for index, row in enumerate(self.requests) if row["operation"] == "score"][:2]
        for index in targets:
            records[index]["token_logprobs"] = [[0.] * len(row["response_ids"]) for row in self.requests[index]["candidates"]]
        report = carrier.reduce_records(self.requests, records, self.tokenizer)
        self.assertEqual(report["label"], "ASSAY_INVALID_SEMANTIC_ACTION_SURFACE")
        self.assertEqual(report["valid"], 64)
        self.assertEqual(report["cells"]["0/W+"]["score"]["correct"], 14)

    def test_score_accounting_nonfinite_missing_ties(self):
        request = next(row for row in self.requests if row["operation"] == "score")
        logs = [[-.2] * len(row["response_ids"]) for row in request["candidates"]]
        logs[0][0] = None
        self.assertIsNone(carrier.candidate_choice(request, dict(token_logprobs=logs))[0])
        logs[0][0] = float("nan")
        self.assertIsNone(carrier.candidate_choice(request, dict(token_logprobs=logs))[0])
        logs[0] = [-1e308] * len(logs[0])
        self.assertIsNone(carrier.candidate_choice(request, dict(token_logprobs=logs))[0])
        logs[0].pop()
        with self.assertRaisesRegex(w0.ContractError, "accounting"):
            carrier.candidate_choice(request, dict(token_logprobs=logs))
        with self.assertRaisesRegex(w0.ContractError, "incomplete"):
            carrier.reduce_records(self.requests, self.records()[:-1], self.tokenizer)

    def test_raw_generation_token_mismatch_rejected(self):
        records = self.records()
        records[0]["text"] = "ACT: -gvn"
        with self.assertRaisesRegex(w0.ContractError, "raw generation"):
            carrier.reduce_records(self.requests, records, self.tokenizer)

    def test_no_gpu_without_opt_in_no_overwrites(self):
        with patch.object(carrier, "validate") as validate:
            with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
                carrier.execute("/nonexistent")
            with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
                carrier.worker("/nonexistent")
            validate.assert_not_called()
        with tempfile.TemporaryDirectory() as folder:
            w0.write_once(Path(folder), "evidence.json", {"original": True})
            with self.assertRaises(FileExistsError):
                w0.write_once(Path(folder), "evidence.json", {"replacement": True})
            self.assertEqual(w0.load_json(Path(folder) / "evidence.json"), {"original": True})

    def test_backend_registry_missing_native_canary_fails(self):
        good = Mock(stdout='{"ok": true, "actions": ["-mem2reg", "-gvn"]}', stderr="")
        with patch.object(carrier.subprocess, "run", return_value=good) as run:
            with self.assertRaisesRegex(w0.ContractError, "registered"):
                carrier.backend_preflight(carrier.config_template())
            self.assertEqual(run.call_count, 3)
            self.assertEqual(run.call_args.kwargs["timeout"], 30)
            self.assertEqual(run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")

    def test_worker_frozen_parameters_no_training_and_complete_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            spec = dict(config={}, input_pins={}, test="worker")
            now = time.time()
            spec["config"]["deadline_unix"] = now + 3600
            w0.write_once(root, "STARTED.json", dict(manifest_sha256=w0.digest(spec), wall_start=now,
                deadline_unix=now + 3600, controller_pid=os.getppid()))
            model = Mock(training=False, peft_config=None)
            parameter = Mock(requires_grad=False)
            model.parameters.return_value = [parameter]
            records = {row["request_id"]: row for row in self.records()}
            with patch.object(carrier, "validate", return_value=(spec, self.requests, self.tokenizer)), \
                    patch.object(carrier, "validate_worker_parent"), \
                    patch.object(carrier, "pin_inputs", return_value={}), \
                    patch.object(w0, "gpu_identity"), patch.object(w0, "configure_torch"), \
                    patch.object(w0, "load_hf_model", return_value=model), \
                    patch.object(carrier.cal, "_generate", side_effect=lambda *args: copy.deepcopy(records[args[-1]["request_id"]])) as generate, \
                    patch.object(carrier, "score", side_effect=lambda *args: {"token_logprobs": records[args[-1]["request_id"]]["token_logprobs"]}) as score:
                carrier.worker(root, True)
            self.assertEqual(generate.call_count, 80)
            self.assertEqual(score.call_count, 64)
            model.eval.assert_called_once_with()
            model.requires_grad_.assert_called_once_with(False)
            self.assertEqual([call[0] for call in model.method_calls], ["eval", "requires_grad_", "parameters"])
            self.assertEqual(w0.load_json(root / "report.json")["optimizer_steps"], 0)
            self.assertFalse(carrier.BOUNDARY["fit_release"])

    def valid_config(self):
        config = carrier.config_template()
        config.update(model_revision="a" * 40, tokenizer_revision="a" * 40,
            model_sha256="b" * 64, tokenizer_sha256="b" * 64, node="c" * 64,
            gpu_uuid="GPU-" + "a" * 36, driver_version="1.0",
            lease_end_unix=time.time() + 30000, lease_cutoff_unix=time.time() + 7200,
            deadline_unix=time.time() + 3600, approved_intake="main-test-scope",
            builder_preflight_reference="[Builder] CPU test fixture only")
        return config

    def prepare_fixture(self, root):
        with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                patch.object(carrier, "pin_inputs", return_value={}), \
                patch.object(carrier, "backend_preflight", return_value={}), \
                patch.object(w0, "load_hf_model") as model, \
                patch.object(carrier.subprocess, "Popen") as launch:
            carrier.prepare(root, self.valid_config())
            model.assert_not_called()
            launch.assert_not_called()

    def test_preparation_immutable_and_request_drift_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            self.prepare_fixture(root)
            with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer):
                spec, requests, _ = carrier.validate(root)
            self.assertEqual(len(requests), 144)
            self.assertEqual(spec["boundary"], carrier.BOUNDARY)
            with self.assertRaisesRegex(w0.ContractError, "fresh output"):
                carrier.prepare(root, self.valid_config())
            with (root / "requests.json").open("ab") as stream:
                stream.write(b" ")
            with self.assertRaisesRegex(w0.ContractError, "artifact drift"):
                carrier.validate(root)

    def test_owned_worker_timeout_no_retry_partial_evidence_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            self.prepare_fixture(root)
            process = Mock(pid=123)
            process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
            with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(carrier, "pin_inputs", return_value={}), \
                    patch.object(w0, "gpu_identity", return_value={}), patch.object(w0, "assert_gpu_idle"), \
                    patch.object(w0, "assert_output_fds_outside_run"), \
                    patch.object(carrier.subprocess, "Popen", return_value=process) as launch, \
                    patch.object(carrier, "process_identity", return_value=dict(pid=123, pgid=123, session=123,
                        ppid=os.getpid(), start_ticks=1)), \
                    patch.object(carrier.neutral, "_cleanup_group", return_value=True) as cleanup:
                with self.assertRaises(subprocess.TimeoutExpired):
                    carrier.execute(root, True)
                cleanup.assert_called_once_with(process)
                self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 3592)
                self.assertEqual(launch.call_args.args[0][:2], [carrier.TIMEOUT_BINARY, "--signal=KILL"])
                self.assertTrue(launch.call_args.kwargs["start_new_session"])
                self.assertEqual(launch.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
                with self.assertRaisesRegex(w0.ContractError, "no retry"):
                    carrier.execute(root, True)
                launch.assert_called_once()
            self.assertTrue((root / "STARTED.json").exists())
            self.assertTrue((root / "FAILED.json").exists())
            self.assertFalse((root / "SEAL.json").exists())

    def test_successful_replay_then_extra_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            self.prepare_fixture(root)
            for record in self.records():
                w0.write_once(root, record["request_id"] + ".json", record)
            report = carrier.reduce_records(self.requests, self.records(), self.tokenizer)
            w0.write_once(root, "report.json", report)
            now = time.time()
            spec = w0.load_json(root / "manifest.json")
            w0.write_once(root, "STARTED.json", dict(wall_start=now, deadline_unix=now + 30,
                                                   manifest_sha256=w0.digest(spec)))
            w0.write_once(root, "WORKER_CLAIMED.json", dict(pid=123))
            w0.write_once(root, "SUPERVISOR.json", dict(identity=dict(pid=123)))
            w0.write_once(root, "CLEANUP.json", dict(pid=123, owned_group_empty=True, cancellation_signal=None, error=None))
            (root / "worker.log").touch(exist_ok=False)
            w0.write_once(root, "RESOURCE.json", dict(elapsed_seconds=1, wall_finish=now + 1, GPU_count=1))
            w0.write_once(root, "SEAL.json", dict(files=carrier.cal._inventory(root), boundary=carrier.BOUNDARY))
            with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer):
                self.assertEqual(carrier.replay(root), report)
                w0.write_once(root, "extra.json", {})
                with self.assertRaisesRegex(w0.ContractError, "inventory drift"):
                    carrier.replay(root)

    def test_controller_cancel_preserves_failure_and_cleanup_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            self.prepare_fixture(root)
            process = Mock(pid=123)
            process.wait.side_effect = lambda **kwargs: signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(carrier, "pin_inputs", return_value={}), \
                    patch.object(w0, "gpu_identity", return_value={}), patch.object(w0, "assert_gpu_idle"), \
                    patch.object(w0, "assert_output_fds_outside_run"), \
                    patch.object(carrier.subprocess, "Popen", return_value=process), \
                    patch.object(carrier, "process_identity", return_value=dict(pid=123, pgid=123, session=123,
                        ppid=os.getpid(), start_ticks=1)), \
                    patch.object(carrier.neutral, "_cleanup_group", return_value=True):
                with self.assertRaises(carrier.ControllerCancelled):
                    carrier.execute(root, True)
            self.assertEqual(w0.load_json(root / "FAILED.json")["error_type"], "ControllerCancelled")
            self.assertTrue(w0.load_json(root / "CLEANUP.json")["owned_group_empty"])
            self.assertFalse((root / "SEAL.json").exists())

    def test_exact_15_per_cell_61_valid_and_29_swaps_boundaries(self):
        records = self.records()
        changed_cells = set()
        for index, request in enumerate(self.requests):
            audit = request["audit"]
            if audit["kind"] != "semantic_exact_row_carrier" or request["operation"] != "generate":
                continue
            cell = (audit["root"], audit["mapping"])
            if cell not in changed_cells and len(changed_cells) < 3:
                changed_cells.add(cell)
                records[index].update(text="", generated_ids=[0], eos_terminated=True,
                                      decoded_with_terminal_eos="<eos>")
        report = carrier.reduce_records(self.requests, records, self.tokenizer)
        self.assertEqual(report["valid"], 61)
        self.assertEqual(report["label"], "SEMANTIC_EXACT_ROW_SURFACE_OK")
        self.assertGreaterEqual(report["complementary_swaps"]["generate"], 29)
        copy_index = next(index for index, request in enumerate(self.requests)
                          if request["audit"]["kind"] == "native_action_copy")
        records[copy_index].update(text="", generated_ids=[0], eos_terminated=True, decoded_with_terminal_eos="<eos>")
        self.assertEqual(carrier.reduce_records(self.requests, records, self.tokenizer)["label"],
                         "ASSAY_INVALID_SEMANTIC_ACTION_SURFACE")

    def test_standard_json_config_and_hf_snapshot_no_adapters(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = self.valid_config()
            config_path = root / "input.json"
            config_path.write_text(json.dumps(config, indent=2))
            with patch.object(carrier, "prepare", return_value={}) as prepare, contextlib.redirect_stdout(io.StringIO()):
                carrier.main(["prepare", "--config", str(config_path), "--out", str(root / "out")])
                self.assertEqual(prepare.call_args.args[1], config)
            config.update(model_path=str(root), tokenizer_path=str(root), compiler_python=sys.executable,
                          environment={})
            (root / "config.json").write_text(json.dumps(dict(model_type="qwen2", num_hidden_layers=28,
                                                             hidden_size=3584), indent=2))
            snapshot = dict(sha256="b" * 64, files=[["config.json", "d" * 64]])
            with patch.object(w0, "environment_identity", return_value={}), \
                    patch.object(w0, "snapshot_inventory", return_value=snapshot) as inventory:
                pins = carrier.pin_inputs(config)
                self.assertEqual(pins["model"], pins["tokenizer"])
                inventory.assert_called_once()
                snapshot["files"].append(["adapter_config.json", "e" * 64])
                with self.assertRaisesRegex(w0.ContractError, "no adapter"):
                    carrier.pin_inputs(config)

    def test_teacher_forcing_scores_every_shifted_response_token_including_eos(self):
        visited = []

        class Grid:
            def __getitem__(self, index):
                if isinstance(index, tuple):
                    visited.append(index)
                    return SimpleNamespace(cpu=lambda: -.25)
                return self

            def float(self):
                return self

        request = next(row for row in self.requests if row["operation"] == "score")
        torch = Mock()
        torch.inference_mode.side_effect = contextlib.nullcontext
        torch.log_softmax.return_value = Grid()
        model = Mock(return_value=SimpleNamespace(logits=Grid()))
        record = carrier.score(torch, model, request)
        expected = [(index - 1, token) for candidate in request["candidates"]
                    for index, (token, label) in enumerate(zip(candidate["input_ids"], candidate["labels"]))
                    if label != -100]
        self.assertEqual(visited, expected)
        self.assertEqual(sum(token == 0 for _, token in visited), 2)
        choice, sums = carrier.candidate_choice(request, record)
        self.assertEqual(choice, 1)
        self.assertEqual(sums, [-.25 * len(candidate["response_ids"]) for candidate in request["candidates"]])

    def test_four_independent_swap_failures_cannot_pool_passing_cells(self):
        records = self.records()
        changed_cells, changed_pairs = set(), set()
        for index, request in enumerate(self.requests):
            audit = request["audit"]
            if audit["kind"] != "semantic_exact_row_carrier" or request["operation"] != "score":
                continue
            cell = (audit["root"], audit["mapping"])
            if cell not in changed_cells and audit["pair_id"] not in changed_pairs:
                changed_cells.add(cell)
                changed_pairs.add(audit["pair_id"])
                records[index]["token_logprobs"] = [[-1. if action == audit["expected"] else -.01] * len(candidate["response_ids"])
                    for action, candidate in enumerate(request["candidates"])]
        report = carrier.reduce_records(self.requests, records, self.tokenizer)
        self.assertTrue(all(cell["score"]["correct"] == 15 for cell in report["cells"].values()))
        self.assertEqual(report["complementary_swaps"]["score"], 28)
        self.assertEqual(report["label"], "ASSAY_INVALID_SEMANTIC_ACTION_SURFACE")

    def test_zero_tolerance_for_truncation_and_multiple_actions(self):
        for text, eos in (("ACT: -gvn\nACT: -gvn\n", True), ("ACT: -gvn" + " " * 23, False)):
            records = self.records()
            ids = self.tokenizer(text)["input_ids"] + ([0] if eos else [])
            self.assertLessEqual(len(ids), 32)
            records[0].update(text=text, generated_ids=ids, eos_terminated=eos, truncated=not eos,
                              decoded_with_terminal_eos=self.tokenizer.decode(ids))
            report = carrier.reduce_records(self.requests, records, self.tokenizer)
            self.assertEqual(report["valid"], 63)
            self.assertEqual(report["label"], "ASSAY_INVALID_SEMANTIC_ACTION_SURFACE")

    def test_lifetime_repair_keeps_registered_request_bytes(self):
        self.assertEqual(w0.digest(carrier.build_material()),
                         "a40b3cf807ef3ff3715a2ed727a22e0d40d8f73ce44676d7b766c4a6a1d9114c")
        self.assertEqual(w0.digest(carrier.build_items()),
                         "e4c6398a4bbffbc49ecc1ed2b1ba4d27734611b897127cc85e4509c88ba4785b")
        self.assertEqual(w0.digest(self.requests),
                         "fcfcd4f498c159e0e9c3e8c8b0f2746ff950b3f23be48f271d6a9e3b68f5dd6c")


class LifetimeTests(unittest.TestCase):
    def mocked_worker(self, root, process, cleanup, spawn=None):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        launch = stack.enter_context(patch.object(carrier.subprocess, "Popen", side_effect=spawn, return_value=process))
        stack.enter_context(patch.object(carrier, "process_identity", return_value=dict(
            pid=process.pid, pgid=process.pid, session=process.pid, ppid=os.getpid(), start_ticks=7)))
        stack.enter_context(patch.object(carrier.neutral, "_cleanup_group", side_effect=cleanup))
        return launch

    def test_cancel_during_spawn_closes_assignment_race_and_restores_handlers(self):
        previous = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)}
        process = Mock(pid=123)

        def spawn(*args, **kwargs):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            return process

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cleanup = Mock(return_value=True)
            self.mocked_worker(root, process, cleanup, spawn)
            with self.assertRaises(carrier.ControllerCancelled):
                carrier.run_bounded_worker(["cpu-fixture"], root, {}, time.time() + 60)
            cleanup.assert_called_once_with(process)
            process.wait.assert_not_called()
            self.assertEqual(w0.load_json(root / "CLEANUP.json")["cancellation_signal"], signal.SIGTERM)
        self.assertEqual({signum: signal.getsignal(signum) for signum in previous}, previous)

    def test_cancel_during_wait_and_repeat_signal_during_cleanup(self):
        process = Mock(pid=123)
        process.wait.side_effect = lambda **kwargs: signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)

        def cleanup(child):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            return True

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.mocked_worker(root, process, cleanup)
            with self.assertRaises(carrier.ControllerCancelled):
                carrier.run_bounded_worker(["cpu-fixture"], root, {}, time.time() + 60)
            receipt = w0.load_json(root / "SUPERVISOR.json")
            self.assertEqual(receipt["identity"]["pid"], 123)
            self.assertEqual(receipt["command"][-1], "cpu-fixture")
            self.assertTrue(w0.load_json(root / "CLEANUP.json")["owned_group_empty"])

    def test_normal_and_nonzero_timeout_exit_races_always_cleanup(self):
        for status in (0, 13, -signal.SIGKILL, 124, 137):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as folder:
                process = Mock(pid=123)
                process.wait.return_value = status
                cleanup = Mock(return_value=True)
                self.mocked_worker(Path(folder), process, cleanup)
                self.assertEqual(carrier.run_bounded_worker(["fixture"], Path(folder), {}, time.time() + 60), status)
                cleanup.assert_called_once_with(process)

    def test_cleanup_failure_and_expired_budget_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            process = Mock(pid=123)
            process.wait.return_value = 0
            launch = self.mocked_worker(Path(folder), process, Mock(return_value=False))
            with self.assertRaisesRegex(w0.ContractError, "budget exhausted"):
                carrier.run_bounded_worker(["fixture"], Path(folder), {}, time.time() + 1)
            launch.assert_not_called()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(w0.ContractError, "cleanup failed"):
                carrier.run_bounded_worker(["fixture"], Path(folder), {}, time.time() + 60)
            self.assertFalse(w0.load_json(Path(folder) / "CLEANUP.json")["owned_group_empty"])

    def test_already_exited_leader_does_not_hide_surviving_group(self):
        process = Mock(pid=123)
        process.poll.return_value = 0
        with patch.object(carrier.neutral, "_group_alive", side_effect=[True, True, True, False, False]), \
                patch.object(carrier.neutral.time, "monotonic", side_effect=[0, 3, 4]), \
                patch.object(carrier.neutral.os, "killpg") as kill:
            self.assertTrue(carrier.neutral._cleanup_group(process))
        self.assertEqual([call.args for call in kill.call_args_list], [(123, signal.SIGTERM), (123, signal.SIGKILL)])
        process.poll.assert_not_called()
        process.wait.assert_called_once_with(timeout=2)

    def test_group_disappears_between_probe_and_signal(self):
        process = Mock(pid=123)
        with patch.object(carrier.neutral, "_group_alive", side_effect=[True, False, False, False]), \
                patch.object(carrier.neutral.os, "killpg", side_effect=ProcessLookupError):
            self.assertTrue(carrier.neutral._cleanup_group(process))

    def test_timeout_parent_binding_rejects_changed_pid_command_or_controller(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            now = time.time()
            parent = dict(pid=123, ppid=456, pgid=123, session=123, start_ticks=7)
            started = dict(controller_pid=456, controller_start_ticks=8, wall_start=now - 1, deadline_unix=now + 60)
            command = [carrier.TIMEOUT_BINARY, "--signal=KILL", "50.000s", *carrier.worker_command(root)]
            supervisor = dict(identity=parent, command=command, timeout_seconds=50., launch_wall=now, deadline_unix=now + 60)
            w0.write_once(root, "SUPERVISOR.json", supervisor)
            controller = dict(pid=456, start_ticks=8)
            read_bytes = Path.read_bytes
            command_bytes = b"\0".join(part.encode() for part in command) + b"\0"
            with patch.object(carrier.os, "getppid", return_value=123), \
                    patch.object(carrier.os, "getpgrp", return_value=123), \
                    patch.object(carrier.os, "getsid", return_value=123), \
                    patch.object(carrier, "process_identity", side_effect=lambda pid: parent if pid == 123 else controller), \
                    patch.object(Path, "read_bytes",
                        new=lambda path: command_bytes if path.name == "cmdline" else read_bytes(path)):
                carrier.validate_worker_parent(root, started)
                for field in ("start_ticks", "ppid"):
                    altered = dict(parent, **{field: parent[field] + 1})
                    with patch.object(carrier, "process_identity", side_effect=lambda pid: altered if pid == 123 else controller):
                        with self.assertRaisesRegex(w0.ContractError, "startup binding"):
                            carrier.validate_worker_parent(root, started)
                with patch.object(Path, "read_bytes",
                        new=lambda path: b"not-timeout\0" if path.name == "cmdline" else read_bytes(path)):
                    with self.assertRaisesRegex(w0.ContractError, "startup binding"):
                        carrier.validate_worker_parent(root, started)
                controller["start_ticks"] += 1
                with self.assertRaisesRegex(w0.ContractError, "startup binding"):
                    carrier.validate_worker_parent(root, started)

    def wait_for(self, predicate, seconds=5):
        deadline = time.monotonic() + seconds
        while not predicate() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(predicate(), "CPU process fixture did not reach expected state")

    def cpu_tree_command(self, root, leader_exits=False):
        code = (
            "import os, signal, time, json; from pathlib import Path; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); child = os.fork(); "
            "\nif child == 0:\n while True: time.sleep(1)\n"
            f"Path({str(root / 'ready.json')!r}).write_text(json.dumps(dict(parent=os.getpid(), child=child)))\n"
            + ("os._exit(0)\n" if leader_exits else "while True: time.sleep(1)\n"))
        return [sys.executable, "-B", "-c", code]

    @unittest.skipUnless(sys.platform == "linux" and Path(carrier.TIMEOUT_BINARY).is_file(), "Linux GNU timeout required")
    def test_real_timeout_supervisor_start_binding_without_model_load(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            now = time.time()
            started = dict(controller_pid=os.getpid(), controller_start_ticks=carrier.process_identity(os.getpid())["start_ticks"],
                           wall_start=now, deadline_unix=now + 15)
            w0.write_once(root, "STARTED.json", started)
            code = (
                "import os; from pathlib import Path; from organism_v6 import semantic_carrier_diagnostic as c; "
                f"root=Path({str(root)!r}); "
                "c.worker_command=lambda root: [part.decode() for part in Path('/proc/self/cmdline').read_bytes().split(b'\\0')[:-1]]; "
                "c.validate_worker_parent(root, c.w0.load_json(root / 'STARTED.json')); "
                "c.w0.write_once(root, 'BINDING_OK.json', dict(parent=os.getppid()))"
            )
            status = carrier.run_bounded_worker([sys.executable, "-B", "-c", code], root,
                dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1"), started["deadline_unix"])
            self.assertEqual(status, 0, (root / "worker.log").read_text())
            supervisor = w0.load_json(root / "SUPERVISOR.json")
            self.assertEqual(w0.load_json(root / "BINDING_OK.json")["parent"], supervisor["identity"]["pid"])

    @unittest.skipUnless(sys.platform == "linux" and Path(carrier.TIMEOUT_BINARY).is_file(), "Linux GNU timeout required")
    def test_real_exited_leader_surviving_child_is_killed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            process = subprocess.Popen(self.cpu_tree_command(root, True), start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, CUDA_VISIBLE_DEVICES=""))
            try:
                process.wait(timeout=5)
                self.wait_for(lambda: (root / "ready.json").exists())
                self.assertTrue(carrier.neutral._group_alive(process.pid))
                self.assertTrue(carrier.neutral._cleanup_group(process))
                self.assertFalse(carrier.neutral._group_alive(process.pid))
            finally:
                carrier.neutral._cleanup_group(process)

    @unittest.skipUnless(sys.platform == "linux" and Path(carrier.TIMEOUT_BINARY).is_file(), "Linux GNU timeout required")
    def test_real_controller_sigterm_and_sigkill_are_bounded(self):
        for action in (signal.SIGTERM, signal.SIGKILL):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                command = self.cpu_tree_command(root)
                script = (
                    "import os, time; from pathlib import Path; "
                    "from organism_v6.semantic_carrier_diagnostic import run_bounded_worker, CLEANUP_RESERVE_SECONDS; "
                    f"run_bounded_worker({command!r}, Path({str(root)!r}), dict(os.environ, CUDA_VISIBLE_DEVICES=''), "
                    "time.time() + CLEANUP_RESERVE_SECONDS + 3)"
                )
                controller = subprocess.Popen([sys.executable, "-B", "-c", script], start_new_session=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1"))
                group = None
                try:
                    self.wait_for(lambda: (root / "ready.json").exists())
                    supervisor = w0.load_json(root / "SUPERVISOR.json")
                    group = supervisor["identity"]["pid"]
                    controller.send_signal(action)
                    controller.wait(timeout=8)
                    self.wait_for(lambda: not carrier.neutral._group_alive(group), seconds=6)
                    if action == signal.SIGTERM:
                        self.assertTrue(w0.load_json(root / "CLEANUP.json")["owned_group_empty"])
                    else:
                        self.assertFalse((root / "CLEANUP.json").exists())
                finally:
                    carrier.neutral._cleanup_group(controller)
                    if group is None and (root / "SUPERVISOR.json").exists():
                        group = w0.load_json(root / "SUPERVISOR.json")["identity"]["pid"]
                    if group is not None:
                        orphan = SimpleNamespace(pid=group, wait=lambda **kwargs: None)
                        carrier.neutral._cleanup_group(orphan)


if __name__ == "__main__":
    unittest.main()
