"""CPU fixtures with real material, failed-W0 and calibration replay helpers."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_writer_interface_calibration as fixture
from organism_v6 import oracle_lookup_diagnostic as lookup
from organism_v6 import writer_interface_calibration as cal
from organism_v6 import multikey_writer_gateway_simple as w0


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.CalibrationTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.calibration = self.fixture.output
        spec = w0.load_json(self.calibration / "manifest.json")
        self.baselines = w0.load_json(self.calibration / "requests.json")
        records = []
        for request in self.baselines:
            record = dict(request_id=request["request_id"], text=f"ACT: a{request['expected']}",
                          truncated=False, generated_ids=[1, 2], eos_terminated=True)
            records.append(record)
            w0.write_once(self.calibration, request["request_id"] + ".json", record)
        w0.write_once(self.calibration, "report.json", cal.reduce_records(self.baselines, records))
        start = time.time()
        deadline = min(start + 100, spec["deadline_unix"])
        w0.write_once(self.calibration, "STARTED.json", dict(wall_start=start, deadline_unix=deadline))
        log_path = self.fixture.logs / "worker.log"
        log_path.write_bytes(b"synthetic completed calibration log\n")
        w0.write_once(self.calibration, "RESOURCE.json", dict(GPU_count=1, elapsed_seconds=1,
            A40_hours=1 / 3600, deadline_unix=deadline, log_path=str(log_path), log_sha256=w0.file_hash(log_path)))
        w0.write_once(self.calibration, "CALIBRATION_SEAL.json", dict(**cal.BOUNDARY, files=cal._inventory(self.calibration)))
        cal.replay(self.calibration)
        self.seal = w0.file_hash(self.calibration / "CALIBRATION_SEAL.json")
        self.out = self.fixture.base / "lookup"
        self.logs = self.fixture.base / "lookup_logs"
        self.tokenizer = fixture.ChatTokenizer()
        self.options = dict(calibration=self.calibration, calibration_seal_sha256=self.seal,
            log_dir=self.logs, deadline_unix=time.time() + 1000, gpu_uuid=self.fixture.config["gpu_uuid"])

    def prepare(self, **updates):
        options = dict(self.options, **updates)
        with patch.object(w0, "pin_local_inputs", return_value=self.fixture.pins), \
                patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                patch.object(w0, "load_hf_model") as model, patch.object(w0, "gpu_identity") as gpu:
            result = lookup.prepare(self.out, **options)
            model.assert_not_called()
            gpu.assert_not_called()
            return result

    def runtime(self, generation):
        stack = ExitStack()
        self.addCleanup(stack.close)
        model = Mock(training=False)
        parameter = SimpleNamespace(requires_grad=False, data=(11, 17))
        model.parameters.return_value = [parameter]
        process = Mock(pid=123)
        process.wait.side_effect = lambda timeout: (lookup.worker(self.out, True), 0)[1]
        for name, value in (("pin_local_inputs", self.fixture.pins), ("gpu_identity", self.fixture.hardware),
                            ("load_local_tokenizer", self.tokenizer), ("configure_torch", object()),
                            ("load_hf_model", model)):
            stack.enter_context(patch.object(w0, name, return_value=value))
        stack.enter_context(patch.object(w0, "assert_gpu_idle"))
        stack.enter_context(patch.object(w0, "stop_owned_process"))
        stack.enter_context(patch.object(cal, "_generate", side_effect=generation))
        launch = stack.enter_context(patch.object(lookup.subprocess, "Popen", return_value=process))
        return model, parameter, process, launch

    @staticmethod
    def generation(torch, model, tokenizer, request):
        return dict(request_id=request["request_id"], text=f"ACT: a{request['expected']}",
                    generated_ids=[9, 10], truncated=False, eos_terminated=True)

    def test_exact_authentic_row_context_and_deterministic_64(self):
        requests = lookup.build_requests(self.fixture.material, self.baselines, self.tokenizer)
        self.assertEqual(requests, lookup.build_requests(self.fixture.material, self.baselines, self.tokenizer))
        self.assertEqual(len(requests), 64)
        self.assertEqual(len({row["pair_id"] for row in requests}), 64)
        baselines = {row["request_id"]: row for row in self.baselines}
        for request in requests:
            baseline = baselines[request["baseline_request_id"]]
            root = self.fixture.material["roots"][request["root"]]
            held = root["held"][request["held_index"]]
            table = w0.oracle_prompt(root, request["mapping"], held["context"]).split("\nTask:\n", 1)[0]
            self.assertIn(request["selected_row"], table.splitlines())
            self.assertTrue(request["selected_row"].startswith(f"{request['tool']} m{request['mode']} -> "))
            self.assertEqual(request["prompt"].split("\nTask:\n", 1)[1], held["context"])
            self.assertEqual(request["expected"], baseline["expected"])
            self.assertEqual(request["prompt"].count(" -> ACT:"), 1)
            self.assertTrue(request["prompt"].startswith(cal.INSTRUCTION + "\nExplicit action table:\n"))
            self.assertEqual(request["prompt_input_ids"], self.tokenizer(request["rendered_prompt"])["input_ids"])
            self.assertEqual((request["max_new_tokens"], request["do_sample"], request["seed"]), (32, False, 0))

    def test_default_preserves_prior_request_payload_and_grounded_only_prepends(self):
        contract = fixture.parent_fixture.ContractTests
        contract.setUpClass()
        calibration_requests = cal.build_requests(contract.material, contract.requests, self.tokenizer)
        default = lookup.build_requests(contract.material, calibration_requests, self.tokenizer)
        explicit = lookup.build_requests(contract.material, calibration_requests, self.tokenizer, "format_only")
        self.assertEqual(default, explicit)
        legacy = []
        for row in default:
            payload = {key: value for key, value in row.items()
                       if key not in ("request_id", "instruction_variant", "instruction_text")}
            legacy.append(dict(request_id=w0.digest(payload), **payload))
        self.assertEqual(w0.digest(legacy), "504c23d224102aeb98efe3599ef35c6fa3b420e00c892ff8f0db627890996aee")
        literal = ("Use the action table as the source of truth. For the exact tool and mode in the task, "
                   "copy the ACT value after -> from its matching row.")
        grounded = lookup.build_requests(contract.material, calibration_requests, self.tokenizer, "grounded_copy")
        changed = {"request_id", "instruction_variant", "instruction_text", "condition",
                   "prompt", "rendered_prompt", "prompt_input_ids"}
        self.assertEqual(len(grounded), 64)
        for old, new in zip(default, grounded):
            self.assertEqual({key: value for key, value in old.items() if key not in changed},
                             {key: value for key, value in new.items() if key not in changed})
            self.assertEqual(new["prompt"], literal + "\n" + old["prompt"])
            self.assertEqual(new["instruction_text"], literal + "\n" + cal.INSTRUCTION)
            self.assertEqual(new["rendered_prompt"], self.tokenizer.apply_chat_template(
                [{"role": "user", "content": new["prompt"]}], tokenize=False, add_generation_prompt=True))
            self.assertEqual(new["prompt_input_ids"], self.tokenizer(new["rendered_prompt"])["input_ids"])
            self.assertNotEqual(new["condition"], old["condition"])
        with self.assertRaisesRegex(w0.ContractError, "unknown instruction variant"):
            lookup.build_requests(contract.material, calibration_requests, self.tokenizer, "answer_specific")

    def test_grounded_worker_records_variant_and_historical_primary_contrast(self):
        self.prepare(instruction_variant="grounded_copy")
        manifest = w0.load_json(self.out / "manifest.json")
        self.assertEqual(manifest["instruction_variant"], "grounded_copy")
        self.runtime(self.generation)
        report = lookup.execute(self.out, True)
        self.assertEqual(report["instruction_text"], manifest["instruction_text"])
        self.assertEqual(report["instruction_variant"], "grounded_copy")
        self.assertEqual(report["condition"], "single_row_grounded_copy_chat_explicit_32")
        self.assertEqual(report["comparison"]["previous_single_row"]["correct"], 32)
        self.assertEqual(report["comparison"]["previous_single_row"]["valid"], 58)
        self.assertIn("caller-reported", report["comparison"]["previous_single_row"]["provenance"])
        self.assertIn("two-factor", report["comparison"]["full_table_comparison"])
        self.assertFalse(report["comparison"]["further_prompt_search"])
        self.assertTrue(all(name.endswith(("/single_row_grounded_copy", "/full_table_replayed"))
                            for name in report["cells"]))
        self.assertEqual(report, lookup.replay(self.out))

    def test_prepare_preserves_sources_and_refuses_wrong_identity_overlap_overwrite(self):
        before = cal._inventory(self.calibration), cal._inventory(self.fixture.parent)
        with self.assertRaisesRegex(w0.ContractError, "seal pin"):
            self.prepare(calibration_seal_sha256="0" * 64)
        with self.assertRaisesRegex(w0.ContractError, "overlap"):
            self.prepare(log_dir=self.fixture.parent / "logs")
        self.prepare()
        self.assertEqual(before, (cal._inventory(self.calibration), cal._inventory(self.fixture.parent)))
        with self.assertRaisesRegex(w0.ContractError, "fresh"):
            self.prepare()
        with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
            lookup.execute(self.out)

    def test_complete_pair_replay_no_parameter_writes_64_new_calls(self):
        self.prepare()
        before = cal._inventory(self.calibration), cal._inventory(self.fixture.parent)
        calls = []

        def generate(*args):
            calls.append(args[-1]["request_id"])
            return self.generation(*args)

        model, parameter, process, launch = self.runtime(generate)
        report = lookup.execute(self.out, True)
        self.assertEqual(len(calls), 64)
        self.assertEqual(parameter.data, (11, 17))
        model.eval.assert_called_once_with()
        model.requires_grad_.assert_called_once_with(False)
        self.assertEqual([call[0] for call in model.method_calls], ["eval", "requires_grad_", "parameters"])
        self.assertTrue(all(cell["correct"] == cell["valid"] == cell["total"] == 16 for cell in report["cells"].values()))
        self.assertEqual(report["new_inference_requests"], 64)
        self.assertEqual(report["replayed_baselines"], 64)
        self.assertFalse(report["clean_lineage"])
        self.assertEqual(report, lookup.replay(self.out))
        self.assertEqual(before, (cal._inventory(self.calibration), cal._inventory(self.fixture.parent)))
        command = launch.call_args.args[0]
        self.assertEqual(command[1:4], ["-B", "-m", "organism_v6.oracle_lookup_diagnostic"])
        self.assertEqual(launch.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 3595)
        self.assertFalse((self.out / "worker.log").exists())

    def test_strict_counts_and_incomplete_output_rejected(self):
        requests = lookup.build_requests(self.fixture.material, self.baselines, self.tokenizer)
        actual = [self.generation(None, None, None, row) for row in requests]
        baseline = [w0.load_json(self.calibration / (row["baseline_request_id"] + ".json")) for row in requests]
        actual[0].update(text="ACT: a0\nACT: a1")
        actual[1].update(truncated=True)
        actual[2].update(text="To determine the answer")
        report = lookup.reduce_records(requests, actual, baseline)
        single = [cell for name, cell in report["cells"].items() if name.endswith("/single_row")]
        self.assertEqual(sum(cell["valid"] for cell in single), 61)
        self.assertEqual(sum(cell["multiple"] for cell in single), 1)
        self.assertEqual(sum(cell["truncated"] for cell in single), 1)
        with self.assertRaisesRegex(w0.ContractError, "incomplete"):
            lookup.reduce_records(requests, actual[:-1], baseline)

    def test_relocated_equal_helpers_replay_original_checkout(self):
        original = cal._sources()
        relocated = dict(files={}, strict_parser_sha256=original["strict_parser_sha256"])
        for path, digest in original["files"].items():
            source = Path(path)
            target = self.fixture.base / "new_checkout" / source.parent.name / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            relocated["files"][str(target)] = digest
        expected = w0.load_json(self.calibration / "manifest.json")
        with patch.object(cal, "_sources", return_value=relocated), \
                patch.object(lookup.subprocess, "run", wraps=lookup.subprocess.run) as replay:
            spec, material, requests = lookup.calibration_source(self.calibration)
            self.assertEqual(spec, expected)
            self.assertEqual(material, self.fixture.material)
            self.assertEqual(requests, self.fixture.parent_requests)
            replay.assert_called_once()
            self.assertEqual(replay.call_args.kwargs["cwd"], str(Path(cal.__file__).resolve().parents[1]))
            self.assertIn("replay", replay.call_args.args[0])
            target.write_bytes(b"changed relocated producer")
            with self.assertRaisesRegex(w0.ContractError, "producer bytes differ"):
                lookup.calibration_source(self.calibration)
            replay.assert_called_once()

    def test_failed_generation_preserves_partial_no_report_no_retry(self):
        self.prepare()
        calls = []

        def generate(*args):
            calls.append(args[-1])
            if len(calls) == 2:
                raise RuntimeError("synthetic generation failure")
            return self.generation(*args)

        self.runtime(generate)
        with self.assertRaisesRegex(RuntimeError, "synthetic generation failure"):
            lookup.execute(self.out, True)
        self.assertTrue((self.out / (calls[0]["request_id"] + ".json")).is_file())
        self.assertTrue((self.out / "FAILED.json").is_file())
        self.assertFalse((self.out / "report.json").exists())
        self.assertFalse((self.out / "LOOKUP_SEAL.json").exists())
        with self.assertRaisesRegex(w0.ContractError, "fresh prepared"):
            lookup.execute(self.out, True)


if __name__ == "__main__":
    unittest.main()
