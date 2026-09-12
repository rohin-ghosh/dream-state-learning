import copy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gpu import astra_semantic_train_probe as probe
from tests.test_semantic_carrier_diagnostic import Tokenizer


class SemanticTrainProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = Tokenizer()
        cls.material = probe.diagnostic.build_material()
        cls.held_requests, cls.fits = probe.diagnostic.build_panel(cls.material, cls.tokenizer)
        cls.requests = probe.build_requests(cls.fits, cls.material, 0, "f" * 64)
        cls.adapters = {state: dict(adapter_sha256="OFF" if state == "OFF" else "a" * 64,
                                  lora_sha256=None if state == "OFF" else "b" * 64)
                        for state in probe.states_for(0)}
        cls.held = {state: dict(n=64, by_mapping={mapping: dict(BA=.5) for mapping in ("W+", "W-")})
                    for state in probe.states_for(0)}

    def records(self):
        records = []
        for request in self.requests:
            target = request["audit"]["targets"]["W+"]
            if request["operation"] == "generate":
                text = probe.diagnostic.carrier.CANDIDATES[target]
                ids = self.tokenizer(text)["input_ids"] + [self.tokenizer.eos_token_id]
                output = dict(request_id=request["request_id"], text=text, generated_ids=ids,
                    decoded_with_terminal_eos=self.tokenizer.decode(ids), eos_terminated=True, truncated=False)
            else:
                output = dict(token_logprobs=[[-.01 if choice == target else -1.] * len(candidate["response_ids"])
                                             for choice, candidate in enumerate(request["candidates"])])
            records.append(dict(request_id=request["request_id"], request_sha256=probe.digest(request),
                state=request["state"], operation=request["operation"], root_index=0,
                **self.adapters[request["state"]], attempts=1, seconds=.01, output=output))
        return records

    def test_all_rows_both_roots_and_only_selected_root_states(self):
        for root in (0, 1):
            requests = probe.build_requests(self.fits, self.material, root, "f" * 64)
            self.assertEqual(len(requests), 768)
            self.assertEqual({row["state"] for row in requests}, set(probe.states_for(root)))
            for state in probe.states_for(root):
                for operation in ("generate", "score"):
                    selected = [row for row in requests if row["state"] == state and row["operation"] == operation]
                    self.assertEqual({row["audit"]["index"] for row in selected}, set(range(128)))
                    self.assertEqual(len(selected), 128)
        for root in (-1, 2, True, None):
            with self.assertRaises(ValueError):
                probe.states_for(root)

    def test_exact_recorded_payload_encodings_and_no_source_mutation(self):
        before = probe.digest(self.fits)
        for request in self.requests:
            index = request["audit"]["index"]
            saved = self.fits["r0_plus"]["rows"][index]
            self.assertEqual({key: value for key, value in request["payload"].items() if key != "seed"}, saved["payload"])
            self.assertEqual(request["payload"]["seed"], 0)
            self.assertEqual(request["source"]["rows"]["r0_plus"]["sha256"], probe.digest(saved))
            for candidate, source_state in zip(request["candidates"], request["source"]["candidate_source_states"]):
                self.assertEqual(candidate, self.fits[source_state]["rows"][index]["encoded"])
            self.assertNotIn("targets", request["payload"])
        self.assertEqual(before, probe.digest(self.fits))

    def test_rejects_missing_rows_drift_and_noncomplementary_targets(self):
        for mutate in (
            lambda fits: fits["r0_plus"]["rows"].pop(),
            lambda fits: fits["r0_minus"]["rows"][0]["payload"]["prompt_input_ids"].append(999),
            lambda fits: fits["r0_plus"]["rows"][0]["encoded"]["labels"].__setitem__(0, 7),
            lambda fits: fits["r0_plus"]["rows"][0].__setitem__("order", 1),
        ):
            fits = copy.deepcopy(self.fits)
            mutate(fits)
            with self.assertRaises(ValueError):
                probe.build_requests(fits, self.material, 0, "f" * 64)
        material = copy.deepcopy(self.material)
        material["roots"][0]["train"]["W-"][0]["target"] = material["roots"][0]["train"]["W+"][0]["target"]
        with self.assertRaises(ValueError):
            probe.build_requests(self.fits, material, 0, "f" * 64)

    def test_runtime_gpu_copy_changes_only_uuid(self):
        original = dict(gpu_uuid="GPU-" + "1" * 36, nested=dict(model="fixed"), deadline_unix=1)
        snapshot = copy.deepcopy(original)
        runtime = probe.runtime_config(original, "GPU-" + "2" * 36)
        self.assertEqual(original, snapshot)
        self.assertEqual(runtime, dict(snapshot, gpu_uuid="GPU-" + "2" * 36))
        runtime["nested"]["model"] = "changed"
        self.assertEqual(original, snapshot)
        for value in ("0", "0,1", "GPU-bad", None):
            with self.assertRaises(ValueError):
                probe.runtime_config(original, value)

    def test_reduce_full_denominators_both_off_mappings_no_new_gates(self):
        result = probe.reduce_records(self.requests, self.records(), self.tokenizer, self.adapters, self.held)
        self.assertEqual((result["new_fits"], result["optimizer_steps"]), (0, 0))
        self.assertEqual((result["generation_requests"], result["scoring_requests"]), (384, 384))
        self.assertNotIn("gates", result)
        for state in result["states"].values():
            self.assertEqual(state["validity"], 1)
            self.assertEqual(state["by_mapping"]["W+"]["generation_accuracy"], 1)
            self.assertEqual(state["by_mapping"]["W-"]["generation_accuracy"], 0)
            self.assertEqual(state["by_mapping"]["W+"]["train_minus_original_held_BA"], .5)
            self.assertEqual(len(state["by_mapping"]["W+"]["keys"]), 16)
            self.assertTrue(all(row["n"] == 8 for row in state["by_mapping"]["W+"]["keys"]))

    def test_reduce_rejects_missing_duplicate_wrong_adapter_or_nonfinite(self):
        for defect in ("missing", "duplicate", "adapter", "nonfinite", "mass", "root"):
            records = self.records()
            if defect == "missing":
                records.pop()
            elif defect == "duplicate":
                records[1] = records[0]
            elif defect == "adapter":
                records[0]["adapter_sha256"] = "wrong"
            elif defect == "root":
                records[0]["root_index"] = 1
            else:
                record = next(row for row in records if row["operation"] == "score")
                if defect == "nonfinite":
                    record["output"]["token_logprobs"][0][0] = math.nan
                else:
                    record["output"]["token_logprobs"] = [[0.] * len(part) for part in record["output"]["token_logprobs"]]
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                probe.reduce_records(self.requests, records, self.tokenizer, self.adapters, self.held)

    def test_gpu_entrypoints_require_explicit_authorization(self):
        with patch.object(probe, "verify_original") as verify, patch.object(probe, "verify_probe") as verify_probe:
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.execute("missing", "missing", 0, "GPU-" + "1" * 36)
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.worker("missing", "OFF")
            verify.assert_not_called()
            verify_probe.assert_not_called()

    def test_immutable_outputs_and_worker_state_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            probe.write(out, "probe.json", {"fixed": True})
            with self.assertRaises(FileExistsError):
                probe.write(out, "probe.json", {"fixed": False})
            with patch.object(probe, "verify_probe", return_value=(out, dict(states=probe.states_for(0), deadline=1e20), {}, [])), \
                    patch.object(probe.diagnostic, "load_eval_model") as load:
                with self.assertRaisesRegex(ValueError, "root state"):
                    probe.worker(out, "r1_plus", allow_gpu=True)
                load.assert_not_called()

    def test_changed_source_and_original_seal_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "probe.json").write_text(json.dumps(dict(version=probe.VERSION, sources={})))
            with patch.object(probe, "source_pins", return_value={"new": "source"}):
                with self.assertRaisesRegex(ValueError, "source"):
                    probe.verify_probe(root)
            (root / "SEAL.json").write_text("{}")
            with patch.object(probe.rescore, "verify_original", return_value=({}, [])):
                with self.assertRaisesRegex(ValueError, "terminal seal"):
                    probe.verify_original(root, 0)

    def test_missing_worker_completion_cannot_reduce(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                probe.collect_records(Path(temporary), probe.states_for(0))

    def evidence(self, original):
        return dict(manifest=dict(config=dict(gpu_uuid="GPU-" + "1" * 36,
                        model_path=str(original.parent / "model"), tokenizer_path=str(original.parent / "model")),
                        artifacts={"fits.json": "f" * 64}),
                    fits=self.fits, material=self.material, adapters=self.adapters,
                    seal=dict(files={"report.json": "c" * 64}), held_requests=self.held_requests,
                    original_report=dict(label="OPTIMIZATION_INCONCLUSIVE", gates={"optimization_ok": False}))

    def generated(self, request):
        text = probe.diagnostic.carrier.CANDIDATES[0]
        ids = self.tokenizer(text)["input_ids"] + [self.tokenizer.eos_token_id]
        return dict(request_id=request["request_id"], text=text, generated_ids=ids,
                    decoded_with_terminal_eos=self.tokenizer.decode(ids), eos_terminated=True, truncated=False)

    def test_execute_uses_three_fresh_state_loads_reserved_uuid_and_supervisor(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, out = Path(temporary) / "original", Path(temporary) / "probe"
            original.mkdir()
            evidence = self.evidence(original)
            before = probe.digest(evidence)
            device = "GPU-" + "2" * 36
            loads = []

            def fresh_model(config, torch, source, state, adapter_hash, lora_hash):
                loads.append((state, config, adapter_hash, lora_hash))
                return SimpleNamespace(parameters=lambda: iter([SimpleNamespace(dtype="fixture-bfloat16")]))

            def supervised(command, *, log_path, timeout, device):
                self.assertEqual(command[:4], [probe.sys.executable, "-B", "-m", "gpu.astra_semantic_train_probe"])
                self.assertIn("--allow-gpu", command)
                self.assertGreater(timeout, 0)
                self.assertLessEqual(timeout, probe.WORKER_SECONDS)
                self.assertEqual(device, "GPU-" + "2" * 36)
                state = command[command.index("--state") + 1]
                probe.worker(out, state, allow_gpu=True)

            def scored(torch, model, request):
                return dict(token_logprobs=[[-.3] * len(candidate["response_ids"]) for candidate in request["candidates"]])

            with patch.object(probe, "verify_original", return_value=evidence), \
                    patch.object(probe, "source_pins", return_value={"fixture": "source"}), \
                    patch.object(probe, "held_generation_summary", return_value=self.held), \
                    patch.object(probe.supervisor, "run_worker", side_effect=supervised) as supervise, \
                    patch.object(probe.diagnostic.w0, "gpu_identity", return_value={"gpu_uuid": device}), \
                    patch.object(probe.diagnostic.w0, "configure_torch", return_value=Mock()), \
                    patch.object(probe.diagnostic.w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(probe.diagnostic, "load_eval_model", side_effect=fresh_model), \
                    patch.object(probe.diagnostic.cal, "_generate", side_effect=lambda torch, model, tokenizer, request: self.generated(request)) as generate, \
                    patch.object(probe.diagnostic.carrier, "score", side_effect=scored) as score, \
                    patch.dict(os.environ, CUDA_VISIBLE_DEVICES=device):
                probe.execute(original, out, 0, device, allow_gpu=True)
                self.assertEqual(supervise.call_count, 3)
                self.assertEqual((generate.call_count, score.call_count), (384, 384))
                self.assertEqual([row[0] for row in loads], probe.states_for(0))
                self.assertTrue(all(row[1]["gpu_uuid"] == device for row in loads))
                self.assertEqual(loads[0][2:], ("OFF", None))
                result = probe.read(out / "supplementary_report.json")
                self.assertEqual(result["original_gates"], {"optimization_ok": False})
                self.assertEqual(result["original_label"], "OPTIMIZATION_INCONCLUSIVE")
                self.assertEqual(probe.read(out / "probe.json")["original_gpu_uuid"], "GPU-" + "1" * 36)
                self.assertTrue((out / "COMPLETED.json").is_file())
                with self.assertRaisesRegex(ValueError, "fresh"):
                    probe.execute(original, out, 0, device, allow_gpu=True)
            self.assertEqual(probe.digest(evidence), before)

    def test_supervisor_timeout_preserves_failure_without_retry_or_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, out = Path(temporary) / "original", Path(temporary) / "probe"
            original.mkdir()
            device = "GPU-" + "2" * 36
            with patch.object(probe, "verify_original", return_value=self.evidence(original)), \
                    patch.object(probe, "source_pins", return_value={"fixture": "source"}), \
                    patch.object(probe.supervisor, "run_worker", side_effect=TimeoutError("bounded worker timeout")) as supervise, \
                    patch.dict(os.environ, CUDA_VISIBLE_DEVICES=device):
                with self.assertRaises(TimeoutError):
                    probe.execute(original, out, 0, device, allow_gpu=True)
                self.assertEqual(supervise.call_count, 1)
                self.assertTrue((out / "FAILED.json").is_file())
                self.assertFalse((out / "supplementary_report.json").exists())
                self.assertFalse((out / "COMPLETED.json").exists())

    def test_held_comparison_reads_only_all_original_primary_generations(self):
        evidence = dict(held_requests=self.held_requests, material=self.material, seal={},
            original_report=dict(roots=[dict(cells={mapping: dict(BA=.5, OFF_gain=0) for mapping in ("W+", "W-")})]))
        by_id = {row["request_id"]: row for row in self.held_requests}

        def sealed(original, seal, relative):
            self.assertIn("_generate/raw/", relative)
            request = by_id[Path(relative).stem]
            self.assertEqual(request["audit"]["family"], "primary")
            self.assertEqual(request["audit"]["probe_root"], 0)
            return dict(request_id=request["request_id"], request_sha256=probe.digest(request), attempts=1,
                        output=self.generated(request))

        with patch.object(probe, "sealed_read", side_effect=sealed) as read:
            result = probe.held_generation_summary(Path("/fixture"), evidence, 0, self.tokenizer)
        self.assertEqual(read.call_count, 192)
        self.assertTrue(all(row["n"] == 64 and row["validity"] == 1 for row in result.values()))
        self.assertEqual(result["r0_plus"]["by_mapping"]["W+"]["BA"], .5)


if __name__ == "__main__":
    unittest.main()
