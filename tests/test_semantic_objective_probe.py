import copy
from collections import Counter
import json
import math
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from gpu import astra_semantic_objective_probe as probe


class NativeTokenizerFixture:
    eos_token_id = 151645
    tokenizer = property(lambda self: self)
    pieces = {6823: "ACT", 25: ":", 481: " -", 10536: "mem", 17: "2", 1580: "reg",
              21404: "gv", 77: "n", 198: "\n"}

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert not tokenize and add_generation_prompt
        return "<user>" + messages[0]["content"] + "</user><assistant>"

    def __call__(self, text, **kwargs):
        split = text.find("</user><assistant>")
        boundary = split + len("</user><assistant>") if split >= 0 else 0
        prefix, response = text[:boundary], text[boundary:]
        ids = [1000000 + ord(character) for character in prefix]
        offsets = [(index, index + 1) for index in range(len(prefix))]
        cursor = boundary
        if response:
            for token in ([6823, 25, 481, 10536, 17, 1580, 198] if response == "ACT: -mem2reg\n"
                          else [6823, 25, 481, 21404, 77, 198]):
                piece = self.pieces[token]
                assert text[cursor:cursor + len(piece)] == piece
                ids.append(token)
                offsets.append((cursor, cursor + len(piece)))
                cursor += len(piece)
        assert cursor == len(text)
        return dict(input_ids=ids, offset_mapping=offsets)

    def decode(self, ids):
        return "".join("<eos>" if token == self.eos_token_id else self.pieces[token]
                       if token in self.pieces else chr(token - 1000000) for token in ids)


class SemanticObjectiveProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = NativeTokenizerFixture()
        cls.material = probe.diagnostic.build_material()["roots"][1]["train"]["W+"]
        cls.fit = dict(root=1, mapping="W+", seed=1, recipe=probe.diagnostic.w0.EXECUTION_RECIPE, rows=[])
        for index, item in enumerate(cls.material):
            payload = probe.diagnostic.render(cls.tokenizer, item["context"])
            text = probe.diagnostic.carrier.CANDIDATES[item["target"]]
            encoded = probe.diagnostic.carrier.encode_candidate(cls.tokenizer, payload["rendered_prompt"], payload["prompt_input_ids"], text)
            cls.fit["rows"].append(dict(order=index, payload=payload, target=text, encoded=encoded))
        cls.rows = probe.build_rows(cls.fit, cls.material, cls.tokenizer)

    def config(self, parent):
        return dict(gpu_uuid="GPU-" + "1" * 36, model_path=str(parent / "model"), tokenizer_path=str(parent / "model"),
                    protocol_path=str(parent / "protocol"), carrier_proof_path=str(parent / "proof"), protected_paths=[],
                    lease_cutoff_unix=time.time() + 4000)

    def manifest(self, parent):
        return dict(config=self.config(parent), artifacts={"fits.json": "f" * 64})

    def prepared(self, out):
        return dict(sources={"fixture": "source"}, rows_sha256="rows-hash", runtime_config=self.config(out.parent))

    def output(self, request):
        text = probe.diagnostic.carrier.CANDIDATES[request["audit"]["target"]]
        ids = self.tokenizer(text)["input_ids"] + [self.tokenizer.eos_token_id]
        return dict(request_id=request["request_id"], text=text, generated_ids=ids,
                    decoded_with_terminal_eos=self.tokenizer.decode(ids), eos_terminated=True, truncated=False)

    def test_native_mask_shift_all_row_hashes_and_no_input_change(self):
        self.assertEqual(len(self.rows), 128)
        self.assertEqual(Counter(row["audit"]["target"] for row in self.rows), {0: 64, 1: 64})
        for row, saved in zip(self.rows, self.fit["rows"]):
            self.assertEqual(row["hashes"]["source_row"], probe.digest(saved))
            self.assertEqual(row["payload"], saved["payload"])
            self.assertEqual(row["encoded"], saved["encoded"])
            self.assertEqual(row["decision_position"], len(row["payload"]["prompt_input_ids"]) + 3)
            self.assertEqual(row["logit_position"], row["decision_position"] - 1)
            self.assertEqual(set((row["gold_token"], row["other_token"])), {10536, 21404})
            labels = probe.labels_for(row, "first_choice")
            self.assertEqual([index for index, value in enumerate(labels) if value != -100], [row["decision_position"]])
            self.assertEqual(labels[row["decision_position"]], row["gold_token"])
            self.assertEqual(probe.labels_for(row, "full_response"), saved["encoded"]["labels"])
            self.assertEqual(row["hashes"]["decision_labels"], probe.digest(labels))

    def test_wrong_root_seed_recipe_order_masks_targets_rejected(self):
        for defect in ("root", "seed", "recipe", "order", "labels", "target", "prefix", "duplicate"):
            fit = copy.deepcopy(self.fit)
            if defect in ("root", "seed"):
                fit[defect] = 0
            elif defect == "recipe":
                fit["recipe"]["lr"] = 1.
            elif defect == "order":
                fit["rows"].reverse()
            elif defect == "labels":
                fit["rows"][0]["encoded"]["labels"][-1] = -100
            elif defect == "target":
                fit["rows"][0]["target"] = "wrong"
            elif defect == "prefix":
                fit["rows"][0]["payload"]["prompt_input_ids"][0] += 1
            else:
                fit["rows"][1] = copy.deepcopy(fit["rows"][0])
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                probe.build_rows(fit, self.material, self.tokenizer)
        material = copy.deepcopy(self.material)
        material[0]["target"] = 1 - material[0]["target"]
        with self.assertRaisesRegex(ValueError, "target"):
            probe.build_rows(self.fit, material, self.tokenizer)

    def test_prepare_is_native_cpu_only_and_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            original, out = parent / "original", parent / "out"
            original.mkdir()
            manifest = self.manifest(parent)
            with patch.object(probe, "verify_original", return_value=(manifest, self.fit, self.material)), \
                    patch.object(probe, "source_pins", return_value={"fixture": "source"}), \
                    patch.object(probe.diagnostic.w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(probe.diagnostic.w0, "gpu_identity") as gpu, \
                    patch.object(probe.diagnostic, "fit_model") as fit_model:
                prepared = probe.prepare(original, out, manifest["config"]["gpu_uuid"], "Main directive", "Builder native preflight")
                gpu.assert_not_called()
                fit_model.assert_not_called()
                self.assertEqual(prepared["limits"], dict(fits=2, optimizer_steps=512, training_forwards=512,
                    generations=384, decision_prefix_forwards=384, max_new_tokens=32, max_seconds=1800))
                self.assertEqual(prepared["mask_shift_verified_rows"], 128)
                self.assertEqual(probe.verify_prepared(out)[2], self.rows)
                with self.assertRaisesRegex(ValueError, "fresh output"):
                    probe.prepare(original, out, manifest["config"]["gpu_uuid"], "Main", "Builder")
                data = probe.read(out / "rows.json")
                data[0]["decision_labels"][-1] = 123
                (out / "rows.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "drift"):
                    probe.verify_prepared(out)

    def test_original_seal_and_sources_fail_closed_without_loading_model(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(probe, "file_hash", return_value="wrong"), \
                patch.object(probe.diagnostic, "pin_inputs") as pins:
            with self.assertRaisesRegex(ValueError, "manifest/seal"):
                probe.verify_original(temporary)
            pins.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            probe.write(out, "PREPARED.json", dict(version=probe.VERSION, sources={}, out=str(out)))
            with patch.object(probe, "source_pins", return_value={"changed": "source"}), \
                    self.assertRaisesRegex(ValueError, "source/path"):
                probe.verify_prepared(out)

    def test_only_gpu_runtime_override_and_protected_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            config = self.config(parent)
            before = copy.deepcopy(config)
            changed = probe.runtime_config(config, "GPU-" + "2" * 36)
            self.assertEqual(config, before)
            changed["gpu_uuid"] = config["gpu_uuid"]
            self.assertEqual(changed, config)
            for out in (parent / "original" / "new", parent, parent / "model" / "new"):
                with self.assertRaisesRegex(ValueError, "separate"):
                    probe.separate_output(out, parent / "original", config)

    def test_gpu_entrypoints_and_invalid_cap_fail_before_any_work(self):
        with patch.object(probe, "verify_prepared") as verify:
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.execute("missing")
            with self.assertRaisesRegex(ValueError, "allow-gpu"):
                probe.worker("missing", "fit_full_response")
            for cap in (0, 1801, 1800.0):
                with self.assertRaisesRegex(ValueError, "cap"):
                    probe.execute("missing", cap, allow_gpu=True)
            verify.assert_not_called()

    def metrics(self):
        return dict(loss=.1, decision_ce=.7, full_response_ce=.1, nondecision_nll=.1,
                    nondecision_tokens=7, gold_vs_other_margin=.2)

    def test_training_loop_exact256_order_and_first_last_only(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(probe, "training_step", return_value=self.metrics()) as step:
            directory = Path(temporary)
            result = probe.train(None, None, None, self.rows, "full_response", directory, time.time() + 60)
            self.assertEqual(result["optimizer_steps"], 256)
            self.assertEqual([call.args[3] for call in step.call_args_list], self.rows * 2)
            self.assertEqual([index for index, call in enumerate(step.call_args_list) if call.args[5]], [0, 255])
            with self.assertRaises(FileExistsError):
                probe.train(None, None, None, self.rows, "full_response", directory, time.time() + 60)
        with tempfile.TemporaryDirectory() as temporary, patch.object(probe, "training_step") as step:
            with self.assertRaisesRegex(ValueError, "deadline"):
                probe.train(None, None, None, self.rows, "full_response", Path(temporary), time.time() - 1)
            step.assert_not_called()

    def training_mocks(self, loss):
        torch, model, optimizer, parameter = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        torch.isfinite.return_value.item.return_value = True
        torch.isfinite.return_value.all.return_value.item.return_value = True
        model.return_value.loss.detach.return_value.cpu.return_value = loss
        return torch, model, optimizer, parameter

    def test_training_forward_once_native_loss_backward_and_optimizer_order(self):
        for arm, loss in (("full_response", .1), ("first_choice", .7)):
            torch, model, optimizer, parameter = self.training_mocks(loss)
            events = []
            optimizer.zero_grad.side_effect = lambda **kwargs: events.append("clear")
            model.return_value.loss.backward.side_effect = lambda: events.append("backward")
            optimizer.step.side_effect = lambda: events.append("step")
            with patch.object(probe, "forward_metrics", return_value={key: value for key, value in self.metrics().items() if key != "loss"}), \
                    patch.object(probe.diagnostic.w0, "validate_trainables", return_value=[("layer.q_proj.lora_A.default.weight", parameter)]), \
                    patch.object(probe, "numerical_snapshot", return_value={"measured": True}) as snapshot:
                result = probe.training_step(torch, model, optimizer, self.rows[0], arm, True)
                self.assertEqual(model.call_count, 1)
                self.assertEqual(torch.tensor.call_args_list[0].args[0], [self.rows[0]["encoded"]["input_ids"]])
                self.assertEqual(torch.tensor.call_args_list[1].args[0], [probe.labels_for(self.rows[0], arm)])
                self.assertEqual(events, ["clear", "backward", "step"])
                self.assertEqual(result["loss"], loss)
                self.assertTrue(result["numerics"]["measured"])
                snapshot.assert_called_once()

    def test_loss_parity_nonfinite_and_missing_gradient_stop_before_update(self):
        for defect in ("parity", "nonfinite", "gradient"):
            torch, model, optimizer, parameter = self.training_mocks(.9 if defect == "parity" else .1)
            if defect == "nonfinite":
                torch.isfinite.return_value.item.return_value = False
            if defect == "gradient":
                parameter.grad = None
            with patch.object(probe, "forward_metrics", return_value=self.metrics()), \
                    patch.object(probe.diagnostic.w0, "validate_trainables", return_value=[("layer.lora_A.weight", parameter)]), \
                    self.subTest(defect=defect), self.assertRaises(ValueError):
                probe.training_step(torch, model, optimizer, self.rows[0], "full_response")
            optimizer.step.assert_not_called()

    def test_forward_metrics_use_all_shifted_gold_tokens_and_decision_margin(self):
        torch, output = MagicMock(), MagicMock()
        row = self.rows[0]
        positions = [index for index, label in enumerate(row["encoded"]["labels"]) if label != -100]
        logits = output.logits.__getitem__.return_value.detach.return_value.float.return_value
        losses = torch.log_softmax.return_value.__getitem__.return_value.__neg__.return_value
        losses.__getitem__.return_value.cpu.return_value = .7
        losses.mean.return_value.cpu.return_value = .2
        losses.sum.return_value.__sub__.return_value.cpu.return_value = .9
        logits.__getitem__.return_value.__sub__.return_value.cpu.return_value = -.4
        result = probe.forward_metrics(torch, output, row)
        output.logits.__getitem__.assert_called_once_with((0, [position - 1 for position in positions]))
        self.assertEqual(result["decision_ce"], .7)
        self.assertEqual(result["full_response_ce"], .2)
        self.assertEqual(result["nondecision_nll"], .9)
        self.assertEqual(result["gold_vs_other_margin"], -.4)
        self.assertEqual(result["nondecision_tokens"], len(positions) - 1)
        self.assertEqual(logits.__getitem__.call_args_list[0].args[0], (3, row["gold_token"]))
        self.assertEqual(logits.__getitem__.call_args_list[1].args[0], (3, row["other_token"]))

    def test_actual_dtype_inventory_and_projection_norms(self):
        torch, optimizer, parameter, previous = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        parameter.dtype = "actual-fp32"
        parameter.grad.dtype = "actual-fp32-grad"
        optimizer.state = {parameter: {"exp_avg": SimpleNamespace(dtype="actual-moment32"), "step": SimpleNamespace(dtype="actual-step32")}}
        torch.is_tensor.return_value = True
        parameter.detach.return_value.float.return_value.square.return_value.sum.return_value.cpu.return_value = 9.
        parameter.grad.detach.return_value.float.return_value.square.return_value.sum.return_value.cpu.return_value = 4.
        parameter.detach.return_value.float.return_value.__sub__.return_value.square.return_value.sum.return_value.cpu.return_value = .25
        result = probe.numerical_snapshot(torch, [("model.layer.q_proj.lora_B.default.weight", parameter)], optimizer,
                                          {"model.layer.q_proj.lora_B.default.weight": previous})
        self.assertEqual(result["dtypes"]["adapter"], {"actual-fp32": 1})
        self.assertEqual(result["dtypes"]["gradient"], {"actual-fp32-grad": 1})
        self.assertEqual(result["dtypes"]["optimizer"]["exp_avg"], {"actual-moment32": 1})
        self.assertEqual(result["norms_by_projection"]["q_proj"], dict(tensors=1, parameter_l2=3., gradient_l2=2., update_l2=.5))

    def emit_stage(self, out, prepared, stage):
        directory = out / "stages" / stage
        directory.mkdir()
        operation, state = stage.split("_", 1)
        common = dict(stage=stage, sources=prepared["sources"], rows_sha256=prepared["rows_sha256"],
                      identity=dict(pid=1000 + probe.STAGES.index(stage), start_ticks=42))
        if operation == "fit":
            trace = [dict(step=index + 1, epoch=index // 128, row=index % 128, source_row_sha256=self.rows[index % 128]["hashes"]["source_row"],
                          **self.metrics(), **({"numerics": {"dtypes": {"adapter": "float32"}}} if index in (0, 255) else {})) for index in range(256)]
            (directory / "steps.jsonl").write_bytes(b"".join(probe.diagnostic.w0.canonical(item) for item in trace))
            result = dict(optimizer_steps=256, training_forwards=256, steps_sha256=probe.file_hash(directory / "steps.jsonl"), adapter_sha256="tree-" + state,
                          initial_lora_sha256="initial", final_lora_sha256="final-" + state, update_norm=1.)
            load = dict(common, initial_lora_sha256="initial", adapter_dtypes={"float32": 392})
        else:
            with patch.object(probe, "eval_margin", return_value=1.), \
                    patch.object(probe.diagnostic.cal, "_generate", side_effect=[self.output(probe.generation_request(row, state)) for row in self.rows]):
                result = probe.generate(None, None, self.tokenizer, self.rows, state, directory, time.time() + 60)
            load = dict(common, adapter_sha256="OFF" if state == "OFF" else "tree-" + state,
                        lora_sha256="OFF" if state == "OFF" else "final-" + state)
        probe.write(directory, "LOAD.json", load)
        probe.write(directory, "DONE.json", dict(common, result=result))

    def test_controller_five_fresh_stages_bounds_counts_and_no_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            prepared = self.prepared(out)
            probe.write(out, "PREPARED.json", prepared)
            stages = []

            def supervised(command, *, log_path, timeout, device):
                stage = command[command.index("--stage") + 1]
                stages.append(stage)
                self.assertEqual(command[:5], [probe.sys.executable, "-B", "-m", "gpu.astra_semantic_objective_probe", "worker"])
                self.assertIn("--allow-gpu", command)
                self.assertEqual(device, prepared["runtime_config"]["gpu_uuid"])
                self.assertGreater(timeout, 5)
                self.assertLessEqual(timeout, 900)
                self.assertLessEqual(probe.read(out / (stage + ".job.json"))["deadline"], probe.read(out / "STARTED.json")["deadline"] - 45)
                self.emit_stage(out, prepared, stage)
                probe.write(out, stage + ".cleanup.json", dict(owned_group_empty=True, gpu_processes_absent=True))

            with patch.object(probe, "verify_prepared", return_value=(out, prepared, self.rows, self.tokenizer)), \
                    patch.object(probe, "source_pins", return_value=prepared["sources"]), \
                    patch.object(probe.supervisor, "run_worker", side_effect=supervised), \
                    patch.object(probe.diagnostic.w0, "tree_hash", side_effect=lambda path: "tree-" + path.parent.name.removeprefix("fit_")), \
                    patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": prepared["runtime_config"]["gpu_uuid"]}):
                report = probe.execute(out, allow_gpu=True)
                self.assertEqual(stages, list(probe.STAGES))
                self.assertEqual(report["optimizer_steps"], 512)
                self.assertEqual(report["generation_requests"], 384)
                self.assertEqual(report["held_queries"], 0)
                self.assertEqual(report["actual_cost"], dict(training_forwards=512, optimizer_steps=512,
                    generation_requests=384, decision_prefix_forwards=384, generated_tokens=2880))
                self.assertEqual(set(report["states"]), {"OFF", *probe.ARMS})
                for summary in report["states"].values():
                    self.assertEqual((summary["n"], summary["correct"], summary["valid"]), (128, 128, 128))
                    self.assertTrue(all(cell["correct"] == 8 for cell in summary["key_modes"]))
                with self.assertRaisesRegex(ValueError, "no retry"):
                    probe.execute(out, allow_gpu=True)
                path = out / "stages/generate_first_choice/records.jsonl"
                path.write_text(path.read_text() + path.read_text().splitlines()[0] + "\n")
                with self.assertRaisesRegex(ValueError, "drift"):
                    probe.reduce(out, prepared, self.rows, self.tokenizer)

    def test_controller_failure_stops_further_stages_preserves_failed(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            prepared = self.prepared(out)
            probe.write(out, "PREPARED.json", prepared)
            with patch.object(probe, "verify_prepared", return_value=(out, prepared, self.rows, self.tokenizer)), \
                    patch.object(probe.supervisor, "run_worker", side_effect=TimeoutError("bounded")) as run, \
                    patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": prepared["runtime_config"]["gpu_uuid"]}):
                with self.assertRaises(TimeoutError):
                    probe.execute(out, allow_gpu=True)
                self.assertEqual(run.call_count, 1)
                self.assertFalse(probe.read(out / "FAILED.json")["automatic_retry"])
                self.assertFalse((out / "COMPLETED.json").exists())

    def test_real_action_strings_constant_gvn_is64_not_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "stages").mkdir()
            prepared = self.prepared(out)
            original_output = self.output
            with patch.object(self, "output", side_effect=lambda request:
                    original_output(dict(request, audit=dict(request["audit"], target=1)))):
                for stage in probe.STAGES:
                    self.emit_stage(out, prepared, stage)
            with patch.object(probe.diagnostic.w0, "tree_hash", side_effect=lambda path: "tree-" + path.parent.name.removeprefix("fit_")):
                report = probe.reduce(out, prepared, self.rows, self.tokenizer)
            for state in report["states"].values():
                self.assertEqual(state["correct"], 64)
                self.assertEqual(state["action_counts"], {"-gvn": 128})
                self.assertEqual(Counter(cell["correct"] for cell in state["key_modes"]), {0: 8, 8: 8})
                self.assertTrue(all(isinstance(item["action"], str) and type(item["target"]) is int for item in state["details"]))

    def test_worker_job_requires_parent_stage_order_and_remaining_deadline(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            probe.write(out, "PREPARED.json", {})
            started = dict(started=time.time(), deadline=time.time() + 1000, prepared_sha256=probe.file_hash(out / "PREPARED.json"))
            probe.write(out, "STARTED.json", started)
            job = dict(stage="fit_full_response", deadline=started["deadline"] - 45,
                       started_sha256=probe.file_hash(out / "STARTED.json"), controller=dict(pid=123, start_ticks=456))
            probe.write(out, "fit_full_response.job.json", job)
            with patch.object(probe.diagnostic.carrier, "process_identity", return_value=dict(pid=123, start_ticks=456)):
                with self.assertRaisesRegex(ValueError, "previous stage"):
                    probe.verify_job(out, "fit_full_response")
                (out / "stages/generate_OFF").mkdir(parents=True)
                probe.write(out / "stages/generate_OFF", "DONE.json", {})
                self.assertEqual(probe.verify_job(out, "fit_full_response"), job)
            with patch.object(probe.diagnostic.carrier, "process_identity", return_value=dict(pid=123, start_ticks=999)), \
                    self.assertRaisesRegex(ValueError, "controller parent"):
                probe.verify_job(out, "fit_full_response")
            with patch.object(probe.time, "time", return_value=started["deadline"]), self.assertRaisesRegex(ValueError, "deadline"):
                probe.verify_job(out, "fit_full_response")

    def test_fit_workers_reuse_native_model_seed_save_and_reject_initialization_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "stages").mkdir()
            prepared = self.prepared(out)
            torch, model, optimizer, parameter = self.training_mocks(.1)
            parameter.dtype = "fixture-fp32"
            initial, final = {"weight": MagicMock()}, {"weight": MagicMock()}
            final["weight"].__sub__.return_value.square.return_value.sum.return_value.__float__.return_value = 1.
            for stage in ("fit_full_response", "fit_first_choice"):
                probe.write(out, stage + ".job.json", {})
            with patch.object(probe, "verify_job", return_value=dict(deadline=time.time() + 60)), \
                    patch.object(probe, "verify_prepared", return_value=(out, prepared, self.rows, self.tokenizer)), \
                    patch.object(probe, "source_pins", return_value=prepared["sources"]), \
                    patch.object(probe.diagnostic.w0, "gpu_identity", return_value={}), \
                    patch.object(probe.diagnostic.w0, "configure_torch", return_value=torch) as configure, \
                    patch.object(probe.diagnostic, "fit_model", return_value=(model, optimizer, initial)) as native_fit, \
                    patch.object(probe.diagnostic.w0, "validate_trainables", return_value=[("weight", parameter)]), \
                    patch.object(probe.diagnostic.w0, "lora_tensors", return_value=final), \
                    patch.object(probe.diagnostic.w0, "tensor_digest", side_effect=lambda values: "initial" if values is initial else "final"), \
                    patch.object(probe.diagnostic.w0, "tree_hash", return_value="tree"), \
                    patch.object(probe, "train", return_value=dict(optimizer_steps=256, training_forwards=256)) as train, \
                    patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": prepared["runtime_config"]["gpu_uuid"]}):
                probe.worker(out, "fit_full_response", allow_gpu=True)
                self.assertEqual(configure.call_args.args, (prepared["runtime_config"], 1))
                native_fit.assert_called_once_with(torch, prepared["runtime_config"])
                self.assertEqual(train.call_args.args[4], "full_response")
                model.save_pretrained.assert_called_once_with(str(out / "stages/fit_full_response/adapter"), safe_serialization=True)
                control_path = out / "stages/fit_full_response/LOAD.json"
                control = probe.read(control_path)
                control["initial_lora_sha256"] = "different"
                control_path.write_text(json.dumps(control))
                with self.assertRaisesRegex(ValueError, "initialization/dtypes"):
                    probe.worker(out, "fit_first_choice", allow_gpu=True)
                self.assertEqual(train.call_count, 1)
                self.assertFalse((out / "stages/fit_first_choice/DONE.json").exists())

    def test_generation_worker_fresh_reload_binds_saved_adapter_not_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "stages/fit_full_response").mkdir(parents=True)
            probe.write(out / "stages/fit_full_response", "DONE.json", dict(result=dict(adapter_sha256="new-tree", final_lora_sha256="new-lora")))
            probe.write(out, "generate_full_response.job.json", {})
            prepared = self.prepared(out)
            model, torch = Mock(), Mock()
            with patch.object(probe, "verify_job", return_value=dict(deadline=time.time() + 60)), \
                    patch.object(probe, "verify_prepared", return_value=(out, prepared, self.rows, self.tokenizer)), \
                    patch.object(probe, "source_pins", return_value=prepared["sources"]), \
                    patch.object(probe.diagnostic.w0, "gpu_identity", return_value={}), \
                    patch.object(probe.diagnostic.w0, "configure_torch", return_value=torch), \
                    patch.object(probe.diagnostic, "load_eval_model", return_value=model) as reload_model, \
                    patch.object(probe.diagnostic, "fit_model") as fit, \
                    patch.object(probe, "generate", return_value=dict(count=128)) as generate, \
                    patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": prepared["runtime_config"]["gpu_uuid"]}):
                probe.worker(out, "generate_full_response", allow_gpu=True)
                reload_model.assert_called_once_with(prepared["runtime_config"], torch, out, "full_response", "new-tree", "new-lora")
                self.assertEqual(generate.call_args.args[3:5], (self.rows, "full_response"))
                fit.assert_not_called()

    def test_source_pins_include_both_new_files_native_writer_and_supervisor(self):
        pins = probe.source_pins()
        for path in (Path(probe.__file__), Path(__file__), Path(probe.diagnostic.__file__), Path(probe.supervisor.__file__)):
            self.assertEqual(pins[str(path.resolve())], probe.file_hash(path))

    def test_decision_prefix_excludes_gold_and_greedy_keeps_original_prompt(self):
        torch, model = MagicMock(), MagicMock()
        model.return_value.logits.__getitem__.return_value.float.return_value.__getitem__.return_value.__sub__.return_value.cpu.return_value = .2
        row = self.rows[0]
        self.assertEqual(probe.eval_margin(torch, model, row), .2)
        torch.tensor.assert_called_once_with([row["encoded"]["input_ids"][:row["decision_position"]]], dtype=torch.long, device="cuda:0")
        self.assertEqual(len(torch.tensor.call_args.args[0][0]), row["decision_position"])
        request = probe.generation_request(row, "OFF")
        self.assertEqual(request["payload"]["prompt_input_ids"], row["payload"]["prompt_input_ids"])
        self.assertEqual(request["payload"]["max_new_tokens"], 32)
        self.assertIs(request["payload"]["do_sample"], False)
        self.assertEqual(request["candidates"], [])

    def test_prefix_forward_cannot_launch_greedy_after_deadline(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(probe.time, "time", side_effect=[100., 200.]), \
                patch.object(probe, "eval_margin", return_value=1.), \
                patch.object(probe.diagnostic.cal, "_generate") as generate:
            with self.assertRaisesRegex(ValueError, "deadline before greedy"):
                probe.generate(None, None, self.tokenizer, self.rows, "OFF", Path(temporary), 150.)
            generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
