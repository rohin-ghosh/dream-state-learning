"""CPU synthetic custody/tokenizer/process boundaries; no model or GPU execution."""
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

import test_multikey_writer_gateway_simple as parent_fixture
from organism_v6 import multikey_writer_gateway_simple as w0
from organism_v6 import writer_interface_calibration as calibration


class ChatTokenizer(w0.FixtureTokenizer):
    def __init__(self):
        self.tokenizer = self

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        if tokenize is not False or add_generation_prompt is not True:
            raise ValueError("unexpected chat options")
        return "<user>\n" + messages[0]["content"] + "\n<assistant>\n"


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.parent = self.base / "failed_w0"
        self.output = self.base / "calibration"
        self.logs = self.base / "calibration_logs"
        fixture = parent_fixture.RealExecutorTests(methodName="runTest")
        self.config = fixture.config(self.base)
        fixture.prepare(self.parent, self.config)
        self.pins = fixture.pins(self.config)
        self.hardware = fixture.hardware(self.config)
        self.material = w0.load_json(self.parent / "material.json")
        manifest = w0.load_json(self.parent / "manifest.json")
        adapters = {f"{root}/{mapping}": w0.digest(["synthetic adapter", root, mapping])
                    for root in range(2) for mapping in w0.MAPS}
        identity = dict(model=w0.MODEL, model_sha256=self.config["model_sha256"],
                        tokenizer_sha256=self.config["tokenizer_sha256"], run_sha256=w0.digest(manifest))
        requests = w0.build_requests(self.material, identity, adapters,
                                     preflight=w0.load_json(self.parent / "tokenizer_preflight.json"))
        report = dict(scientific_label="ASSAY_INVALID", result=dict(label="ASSAY_INVALID",
            roots=[dict(cells={mapping: dict(oracle_BA=0) for mapping in w0.MAPS}) for _ in range(2)]))
        resource = dict(manifest_sha256=w0.digest(manifest), stages=list(manifest["fits"]) +
            [f"eval_{state}_{operation}" for state in ("OFF", "0_0", "0_1", "1_0", "1_1")
             for operation in ("generate", "score")])
        for name, value in (("adapter_hashes.json", adapters), ("requests.json", requests),
                            ("report_real.json", report), ("RESOURCE_RECEIPT.json", resource)):
            w0.write_once(self.parent, name, value)
        (self.parent / "launcher.out").write_bytes(b"")
        seal = dict(version=w0.REAL_VERSION, evidence="REAL_GPU_EXECUTION",
                    report_sha256=w0.digest(report), files=calibration._inventory(self.parent))
        w0.write_once(self.parent, "REAL_EXECUTION_SEAL.json", seal)
        self.seal_pin = w0.file_hash(self.parent / "REAL_EXECUTION_SEAL.json")
        (self.parent / "launcher.out").write_bytes(w0.canonical(report))
        self.parent_requests = requests

    def prepare(self, **overrides):
        options = dict(parent=self.parent, parent_seal_sha256=self.seal_pin,
                       log_dir=self.logs, deadline_unix=time.time() + 1800)
        options.update(overrides)
        with patch.object(w0, "pin_local_inputs", return_value=self.pins), \
                patch.object(w0, "load_local_tokenizer", return_value=ChatTokenizer()), \
                patch.object(w0, "load_hf_model") as model, patch.object(w0, "gpu_identity") as gpu:
            result = calibration.prepare(self.output, **options)
            model.assert_not_called()
            gpu.assert_not_called()
            return result

    def test_parent_failed_readonly_and_fixed_factorial(self):
        before = calibration._inventory(self.parent)
        result = self.prepare()
        self.assertEqual(before, calibration._inventory(self.parent))
        self.assertEqual(result["label"], "DEVELOPMENT_CALIBRATION")
        self.assertFalse(result["parent_passed"])
        self.assertFalse(result["clean_lineage"])
        requests = w0.load_json(self.output / "requests.json")
        self.assertEqual(len(requests), 320)
        self.assertEqual(len({row["pair_id"] for row in requests}), 64)
        for root_index, root in enumerate(self.material["roots"]):
            for slot in range(8):
                for mode in range(2):
                    first = next(index for index, row in enumerate(root["held"])
                                 if (row["slot"], row["mode"]) == (slot, mode))
                    chosen = [row for row in requests if row["root"] == root_index
                              and row["tool"] == root["tools"][slot] and row["mode"] == mode]
                    self.assertEqual(len(chosen), 10)
                    self.assertTrue(all(row["held_index"] == first for row in chosen))
        pairs = {}
        for row in requests:
            pairs.setdefault(row["pair_id"], {})[row["condition"]] = row
            self.assertEqual(row["prompt_input_ids"], ChatTokenizer()(row["rendered_prompt"])["input_ids"])
            self.assertIs(row["do_sample"], False)
        for pair in pairs.values():
            raw = pair["raw_original_32"]
            self.assertEqual(raw["prompt_input_ids"], pair["raw_original_256"]["prompt_input_ids"])
            self.assertEqual(pair["raw_original_256"]["max_new_tokens"], 256)
            for name in ("raw_explicit_32", "chat_explicit_32"):
                self.assertEqual(pair[name]["prompt"], calibration.INSTRUCTION + "\n" + raw["prompt"])
            self.assertTrue(pair["chat_original_32"]["rendered_prompt"].startswith("<user>"))

    def test_strict_parser_counts_and_pairing_no_softening(self):
        requests = calibration.build_requests(self.material, self.parent_requests, ChatTokenizer())
        records = []
        for request in requests:
            case = request["condition"]
            text = f"ACT: a{request['expected']}"
            if case == "raw_original_32":
                text = "To determine the answer, " + text
            elif case == "chat_original_32":
                text += "\nACT: a0"
            records.append(dict(request_id=request["request_id"], text=text,
                                truncated=case == "raw_explicit_32"))
        report = calibration.reduce_records(requests, records)
        self.assertEqual(len(report["paired_prompt_ids"]), 64)
        for name, cell in report["cells"].items():
            self.assertEqual(cell["total"], 16)
            if name.endswith("/chat_original_32"):
                self.assertEqual((cell["correct"], cell["valid"], cell["multiple"]), (0, 0, 16))
            elif name.endswith("/raw_explicit_32"):
                self.assertEqual((cell["correct"], cell["valid"], cell["truncated"]), (0, 0, 16))
            elif name.endswith("/raw_original_32"):
                self.assertEqual(cell["valid"], 0)
            else:
                self.assertEqual(cell["correct"], 16)
        with self.assertRaises(w0.ContractError):
            calibration.reduce_records(requests, records[:-1])
        with self.assertRaises(w0.ContractError):
            calibration.reduce_records(requests, [records[0]] * 320)

    def test_parent_tamper_and_wrong_seal_rejected(self):
        with self.assertRaisesRegex(w0.ContractError, "seal pin"):
            self.prepare(parent_seal_sha256="0" * 64)
        path = self.parent / "requests.json"
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with self.assertRaises(w0.ContractError):
            self.prepare()
        path.write_bytes(original)
        (self.parent / "extra_file").write_text("unexpected")
        with self.assertRaisesRegex(w0.ContractError, "inventory"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_no_logger_defect_is_not_silently_relabelled(self):
        (self.parent / "launcher.out").write_bytes(b"")
        with self.assertRaisesRegex(w0.ContractError, "logger|launcher"):
            self.prepare()

    def test_exclusive_output_and_external_logs(self):
        with self.assertRaisesRegex(w0.ContractError, "overlap"):
            self.prepare(log_dir=self.output / "logs")
        self.prepare()
        before = calibration._inventory(self.output)
        with self.assertRaises(w0.ContractError):
            self.prepare()
        self.assertEqual(before, calibration._inventory(self.output))

    def test_prepared_source_artifact_and_parent_drift_rejected(self):
        self.prepare()
        calibration.validate_prepared(self.output)
        with patch.object(calibration, "_sources", return_value={}):
            with self.assertRaisesRegex(w0.ContractError, "source changed"):
                calibration.validate_prepared(self.output)
        path = self.output / "requests.json"
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with self.assertRaisesRegex(w0.ContractError, "artifact changed"):
            calibration.validate_prepared(self.output)
        path.write_bytes(original)
        (self.parent / "launcher.out").write_bytes(b"changed a second time")
        with self.assertRaisesRegex(w0.ContractError, "parent inventory/config changed"):
            calibration.validate_prepared(self.output)

    def test_gpu_optin_required_before_any_io_or_loading(self):
        with patch.object(w0, "load_hf_model") as model, patch.object(w0, "gpu_identity") as gpu:
            for function in (calibration.execute, calibration.worker):
                with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
                    function(self.base / "nonexistent")
            model.assert_not_called()
            gpu.assert_not_called()

    def test_hard_deadline_process_and_environment(self):
        self.prepare()
        process = Mock(pid=123)
        process.wait.side_effect = subprocess.TimeoutExpired("CPU mock", 1)
        with patch.object(w0, "pin_local_inputs", return_value=self.pins), \
                patch.object(w0, "gpu_identity", return_value=self.hardware), \
                patch.object(w0, "assert_gpu_idle"), \
                patch.object(calibration.subprocess, "Popen", return_value=process) as launch, \
                patch.object(w0, "stop_owned_process") as stop:
            with self.assertRaises(subprocess.TimeoutExpired):
                calibration.execute(self.output, allow_gpu=True)
            stop.assert_called_once_with(process)
        command = launch.call_args.args[0]
        self.assertEqual(command[1:4], ["-B", "-m", "organism_v6.writer_interface_calibration"])
        self.assertIn("--allow-gpu", command)
        env = launch.call_args.kwargs["env"]
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], self.config["gpu_uuid"])
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(env["TRANSFORMERS_OFFLINE"], "1")
        self.assertGreater(process.wait.call_args.kwargs["timeout"], 0)
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 3595)
        self.assertTrue((self.logs / "worker.log").is_file())
        self.assertFalse((self.output / "worker.log").exists())
        self.assertTrue((self.output / "FAILED.json").exists())
        self.assertFalse((self.output / "CALIBRATION_SEAL.json").exists())
        with self.assertRaises(w0.ContractError):
            calibration.execute(self.output, allow_gpu=True)

    def test_deadlines_and_hardware_fail_before_worker(self):
        with self.assertRaises(w0.ContractError):
            self.prepare(deadline_unix=time.time() - 1)
        with self.assertRaises(w0.ContractError):
            self.prepare(deadline_unix=self.config["lease_cutoff_unix"] + 1)
        self.prepare()
        with patch.object(w0, "pin_local_inputs", return_value=self.pins), \
                patch.object(w0, "gpu_identity", side_effect=w0.ContractError("wrong GPU UUID")), \
                patch.object(calibration.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(w0.ContractError, "wrong GPU"):
                calibration.execute(self.output, allow_gpu=True)
            launch.assert_not_called()

    def test_complete_worker_path_and_readonly_replay(self):
        self.prepare()
        model = Mock(training=False)
        model.parameters.return_value = [SimpleNamespace(requires_grad=False)]
        process = Mock(pid=123)

        def generate(torch, selected_model, tokenizer, request):
            self.assertIs(selected_model, model)
            text = f"ACT: a{request['expected']}"
            return dict(request_id=request["request_id"], text=text, truncated=False,
                        generated_ids=tokenizer(text)["input_ids"] + [tokenizer.eos_token_id],
                        decoded_with_terminal_eos=text, eos_terminated=True)

        def wait(timeout):
            calibration.worker(self.output, allow_gpu=True)
            return 0

        process.wait.side_effect = wait
        with patch.object(w0, "pin_local_inputs", return_value=self.pins), \
                patch.object(w0, "gpu_identity", return_value=self.hardware), \
                patch.object(w0, "assert_gpu_idle"), \
                patch.object(w0, "load_local_tokenizer", return_value=ChatTokenizer()), \
                patch.object(w0, "configure_torch", return_value=object()), \
                patch.object(w0, "load_hf_model", return_value=model) as loader, \
                patch.object(calibration, "_generate", side_effect=generate) as generation, \
                patch.object(calibration.subprocess, "Popen", return_value=process):
            report = calibration.execute(self.output, allow_gpu=True)
            self.assertEqual(generation.call_count, 320)
            loader.assert_called_once()
        model.eval.assert_called_once_with()
        model.requires_grad_.assert_called_once_with(False)
        self.assertEqual(report["total_requests"], 320)
        self.assertTrue(all(cell["correct"] == 16 for cell in report["cells"].values()))
        self.assertEqual(report, calibration.replay(self.output))
        self.assertFalse(report["parent_passed"])
        (self.logs / "worker.log").write_text("late logger append")
        with self.assertRaisesRegex(w0.ContractError, "external worker log changed"):
            calibration.replay(self.output)

    def test_worker_template_drift_precedes_model_load(self):
        self.prepare()
        spec = w0.load_json(self.output / "manifest.json")
        w0.write_once(self.output, "STARTED.json", dict(manifest_sha256=w0.digest(spec),
            wall_start=time.time(), deadline_unix=time.time() + 100))
        changed = ChatTokenizer()
        changed.apply_chat_template = lambda *args, **kwargs: "changed template"
        with patch.object(w0, "pin_local_inputs", return_value=self.pins), \
                patch.object(w0, "gpu_identity", return_value=self.hardware), \
                patch.object(w0, "load_local_tokenizer", return_value=changed), \
                patch.object(w0, "load_hf_model") as model:
            with self.assertRaisesRegex(w0.ContractError, "tokenizer/template/request drift"):
                calibration.worker(self.output, allow_gpu=True)
            model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
