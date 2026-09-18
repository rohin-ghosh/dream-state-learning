import copy
from collections import Counter
import contextlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from organism_v6 import semantic_writer_diagnostic as writer
from organism_v6 import multikey_writer_gateway_simple as w0
from organism_v6 import semantic_carrier_diagnostic as carrier


class Tokenizer(w0.FixtureTokenizer):
    tokenizer = property(lambda self: self)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert len(messages) == 1 and not tokenize and add_generation_prompt
        return "<user>\n" + messages[0]["content"] + "</user>\n<assistant>\n"

    def decode(self, ids):
        return "".join("<eos>" if token == 0 else chr(token - 1) for token in ids)


class WriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = Tokenizer()
        cls.material = writer.build_material()
        cls.requests, cls.fits = writer.build_panel(cls.material, cls.tokenizer)

    def record(self, request, load_id="fixture", adapter=None):
        audit = request["audit"]
        action_index = 0
        totals = [-2., -2.]
        if request["state"] != "OFF" and audit["family"] == "primary":
            root, mapping = writer.STATES[request["state"]]
            row = self.material["roots"][root]["held"][audit["index"]]
            action_index = w0.action(root, row["slot"], row["mode"], mapping)
            totals = [-4., -4.]
            totals[action_index] = -.1
        if request["operation"] == "score":
            output = dict(token_logprobs=[[total / len(candidate["response_ids"])] * len(candidate["response_ids"])
                          for total, candidate in zip(totals, request["candidates"])])
        else:
            action = carrier.COPY_ACTIONS[audit["index"]] if audit["family"] == "copy" else carrier.ACTIONS[action_index]
            text = f"ACT: {action}\n"
            ids = self.tokenizer(text)["input_ids"] + [0]
            output = dict(request_id=request["request_id"], text=text, generated_ids=ids, eos_terminated=True,
                          truncated=False, decoded_with_terminal_eos=self.tokenizer.decode(ids))
        return dict(request_id=request["request_id"], request_sha256=w0.digest(request), attempts=1, seconds=0., output=output,
                    load_id=load_id, adapter_sha256=adapter or ("OFF" if request["state"] == "OFF" else w0.digest(request["state"])))

    def records(self):
        return [self.record(request) for request in self.requests]

    def config(self, folder):
        config = writer.config_template()
        config.update(model_revision="a" * 40, tokenizer_revision="a" * 40, model_sha256="b" * 64,
            tokenizer_sha256="b" * 64, node="c" * 64, gpu_uuid="GPU-" + "a" * 36, driver_version="1.0",
            lease_end_unix=time.time() + 50000, lease_cutoff_unix=time.time() + 20000, deadline_unix=time.time() + 10800,
            approved_intake="main-frozen-Q0-fixture", builder_preflight_reference="CPU fixture, not launch evidence")
        output = dict(label="SEMANTIC_EXACT_ROW_SURFACE_OK", valid=64, truncated=0, multiple=0, optimizer_steps=0,
            complementary_swaps={"generate": 32, "score": 32}, native_copy_correct={"0": 8, "1": 8},
            cells={f"{root}/{mapping}": {operation: {"correct": 16} for operation in ("generate", "score")}
                   for root in range(2) for mapping in w0.MAPS})
        output_path = folder / "carrier-output.json"
        output_path.write_text(json.dumps(output, indent=2))
        proof = writer.proof_template()
        proof.update(verified_by_main=True, verification_reference="main CPU fixture", output_path=str(output_path),
            output_sha256=w0.file_hash(output_path), model_sha256=config["model_sha256"], tokenizer_sha256=config["tokenizer_sha256"])
        proof_path = folder / "proof.json"
        proof_path.write_text(json.dumps(proof, indent=2))
        protocol = folder / "protocol.md"
        protocol.write_text("Frozen Q0 CPU fixture only.\n")
        config.update(protocol_path=str(protocol), protocol_sha256=w0.file_hash(protocol),
                      carrier_proof_path=str(proof_path), carrier_proof_sha256=w0.file_hash(proof_path))
        return config

    def prepare(self, root):
        config = self.config(root.parent)
        with patch.object(writer, "pin_inputs", return_value={}), \
                patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                patch.object(w0, "gpu_identity") as gpu, patch.object(w0, "load_hf_model") as model, \
                patch.object(carrier, "run_bounded_worker") as launch, \
                patch.object(carrier, "replay", side_effect=AssertionError("must not replay old source here")):
            result = writer.prepare(root, config)
            self.assertEqual(result["counts"]["total"], 1712)
            gpu.assert_not_called()
            model.assert_not_called()
            launch.assert_not_called()
        return config

    def test_namespace_recipe_template_order_and_no_answer_rows(self):
        original = w0.build_material()
        self.assertEqual(self.material["templates"], original["templates"])
        self.assertEqual(w0.digest(w0.EXECUTION_RECIPE), writer.RECIPE_SHA256)
        self.assertEqual(self.material["config"], original["config"])
        carrier_tools = {tool for root in carrier.build_material()["roots"] for tool in root["tools"]}
        old_tools = {tool for root in original["roots"] for tool in root["tools"]}
        for root_index, root in enumerate(self.material["roots"]):
            self.assertFalse(set(root["tools"] + root["neighbours"]) & (carrier_tools | old_tools))
            self.assertEqual(root["orientation"], list(w0.ORIENTATIONS[root_index]))
            for mapping in w0.MAPS:
                old_rows = original["roots"][root_index]["train"][mapping]
                rows = root["train"][mapping]
                self.assertEqual([(row["slot"], row["mode"], row["template"]) for row in rows],
                                 [(row["slot"], row["mode"], row["template"]) for row in old_rows])
                self.assertEqual(Counter(row["target"] for row in rows), {0: 64, 1: 64})
                self.assertTrue(all(row["context"].startswith(carrier.INSTRUCTION + "\n") for row in rows))
                self.assertTrue(all("Binding:" not in row["context"] and " -> " not in row["context"] for row in rows))
            self.assertEqual([row["context"] for row in root["train"]["W+"]], [row["context"] for row in root["train"]["W-"]])
            self.assertTrue(all(plus["target"] == 1 - minus["target"] for plus, minus in zip(root["train"]["W+"], root["train"]["W-"])))
        self.assertEqual(self.material["namespace"], "semantic-writer-Q0-20260912-v1")

    def test_exact_denominators_and_wrong_root_baseline_prefixes(self):
        self.assertEqual(len(self.requests), 1712)
        self.assertEqual(Counter(row["operation"] for row in self.requests), {"generate": 880, "score": 832})
        self.assertEqual(sum(len(row["candidates"]) for row in self.requests), 1664)
        indexed = {writer.coordinate(row): row for row in self.requests}
        for request in self.requests:
            audit = request["audit"]
            if audit["family"] == "wrong_root":
                baseline = indexed["OFF", audit["probe_root"], "primary", audit["index"], request["operation"]]
                self.assertEqual(request["payload"], baseline["payload"])
                self.assertNotEqual(audit["probe_root"], audit["owner_root"])
            self.assertFalse(request["operation"] == "score" and audit["family"] == "copy")
            self.assertNotIn("oracle", audit["family"])
        copies = [row for row in self.requests if row["state"] == "OFF" and row["audit"]["family"] == "copy"]
        self.assertEqual(len(copies), 16)
        self.assertEqual(len({row["payload"]["prompt"] for row in copies}), 8)
        self.assertEqual(len({row["request_id"] for row in copies}), 16)
        with self.assertRaises(w0.ContractError):
            writer.validate_counts(self.requests[:-1])

    def test_masks_complete_lf_eos_unequal_lengths_and_same_chat(self):
        for fit in self.fits.values():
            self.assertEqual(len(fit["rows"]), 128)
            for row in fit["rows"]:
                prefix = row["payload"]["prompt_input_ids"]
                encoded = row["encoded"]
                self.assertEqual(encoded["input_ids"][:len(prefix)], prefix)
                self.assertEqual(encoded["labels"][:len(prefix)], [-100] * len(prefix))
                self.assertEqual(encoded["labels"][len(prefix):], encoded["response_ids"])
                self.assertEqual(encoded["response_ids"][-2:], [ord("\n") + 1, 0])
        scores = [row for row in self.requests if row["operation"] == "score"]
        self.assertTrue(all(len(row["candidates"][0]["response_ids"]) != len(row["candidates"][1]["response_ids"]) for row in scores))
        generated = {writer.coordinate(row)[:-1]: row for row in self.requests if row["operation"] == "generate"}
        for row in scores:
            self.assertEqual(row["payload"], generated[writer.coordinate(row)[:-1]]["payload"])

    def test_complete_all_cell_pass_and_logq_not_raw_sum_gain(self):
        report = writer.reduce_records(self.material, self.requests, self.records(), self.tokenizer)
        self.assertEqual(report["label"], "MULTIKEY_BINDING_PASS")
        for root in report["roots"]:
            for cell in root["cells"].values():
                expected = w0.log_q([-.1, -4], 0) - w0.log_q([-2., -2.], 0)
                self.assertAlmostEqual(cell["mean_NLL_gain"], expected)
                self.assertAlmostEqual(cell["raw_target_sum_mean_gain"], 1.9)
                self.assertEqual(cell["BA"], 1)
                self.assertEqual(set(cell["spill"]), set(writer.FAMILIES))
                self.assertTrue(all(row["mean_binary_TV"] == 0 for row in cell["spill"].values()))

    def test_every_key_and_every_root_must_pass(self):
        records = self.records()
        for index, request in enumerate(self.requests):
            audit = request["audit"]
            if request["state"] == "r1_minus" and request["operation"] == "score" and audit["family"] == "primary":
                row = self.material["roots"][1]["held"][audit["index"]]
                if row["slot"] == row["mode"] == 0:
                    records[index]["output"]["token_logprobs"] = [[-2 / len(candidate["response_ids"])] * len(candidate["response_ids"])
                                                                  for candidate in request["candidates"]]
        report = writer.reduce_records(self.material, self.requests, records, self.tokenizer)
        self.assertEqual(report["label"], "OPTIMIZATION_INCONCLUSIVE")
        self.assertTrue(report["roots"][0]["gates"]["optimization_ok"])
        self.assertFalse(report["roots"][1]["gates"]["optimization_ok"])

    def test_negative_emission_delta_cannot_pass_signed_loophole(self):
        records = self.records()
        for index, request in enumerate(self.requests):
            if request["state"] == "r0_plus" and request["operation"] == "generate" and request["audit"]["family"] == "missing":
                records[index]["output"].update(text="", generated_ids=[0], eos_terminated=True, truncated=False,
                                                decoded_with_terminal_eos="<eos>")
        report = writer.reduce_records(self.material, self.requests, records, self.tokenizer)
        family = report["roots"][0]["cells"]["W+"]["spill"]["missing"]
        self.assertEqual(family["signed_legal_ACT_rate_change"], -1)
        self.assertEqual(family["legal_ACT_rate_change"], 1)
        self.assertEqual(report["label"], "BINDING_WITH_SPILL")

    def test_primary_numeric_parity_with_old_predicates(self):
        report = writer.reduce_records(self.material, self.requests, self.records(), self.tokenizer)
        base = report["roots"][0]["cells"]["W+"]
        for field, values in (("BA", (.79, .8)), ("OFF_gain", (.19, .2)), ("validity", (.949, .95)),
                              ("opposite_BA", (.49, .51)), ("multiple_ACT_rate", (0, 1 / 64))):
            for value in values:
                cell = dict(base, **{field: value})
                expected = w0.cell_gates(dict(cell, oracle_BA=1))
                del expected["oracle_ok"]
                self.assertEqual(writer.cell_gates(cell), expected)
        broken = dict(base, key_NLL_gains=[])
        with self.assertRaisesRegex(w0.ContractError, "nonvacuous"):
            writer.cell_gates(broken)

    def test_strict_generation_and_candidate_accounting(self):
        generate = next(row for row in self.requests if row["operation"] == "generate")
        score = next(row for row in self.requests if row["operation"] == "score")
        output = self.record(generate)["output"]
        output["text"] = "ACT: a0"
        with self.assertRaisesRegex(w0.ContractError, "raw generation"):
            writer.generation(generate, output, self.tokenizer)
        scored = self.record(score)["output"]
        scored["token_logprobs"][0].pop()
        with self.assertRaisesRegex(w0.ContractError, "accounting"):
            writer.score_sums(score, scored)
        with self.assertRaisesRegex(w0.ContractError, "complete raw"):
            writer.reduce_records(self.material, self.requests, self.records()[:-1], self.tokenizer)

    def test_native_prepare_zero_gpu_immutable_and_no_coupled_old_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            with patch.object(w0, "encode_candidate", side_effect=AssertionError("old encoder")), \
                    patch.object(w0, "build_requests", side_effect=AssertionError("old topology")), \
                    patch.object(w0, "reduce_records", side_effect=AssertionError("old reducer")):
                config = self.prepare(root)
                with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer):
                    manifest, _, requests, fits, _ = writer.validate(root)
                self.assertEqual(len(requests), 1712)
                self.assertEqual(len(fits), 4)
                self.assertEqual(manifest["boundary"]["grammar"], "reused_w0_DEV_8_train_4_held_forms")
                with self.assertRaisesRegex(w0.ContractError, "fresh output"):
                    writer.prepare(root, config)
                with (root / "fits.json").open("ab") as stream:
                    stream.write(b" ")
                with self.assertRaisesRegex(w0.ContractError, "artifact drift"):
                    writer.validate(root)

    def test_carrier_main_proof_fail_closed_no_old_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            config = self.config(Path(folder))
            with patch.object(carrier, "replay", side_effect=AssertionError("wrong-source replay")):
                evidence = writer.verified_carrier(config)
            self.assertEqual(evidence["proof"]["verified_replay_sha256"], writer.CARRIER_REPLAY_SHA256)
            proof_path = Path(config["carrier_proof_path"])
            proof = writer.read_json(proof_path)
            proof["verified_by_main"] = False
            proof_path.write_text(json.dumps(proof))
            config["carrier_proof_sha256"] = w0.file_hash(proof_path)
            with self.assertRaisesRegex(w0.ContractError, "main-verified"):
                writer.verified_carrier(config)

    def test_zero_gpu_before_optin_and_controller_reservation(self):
        with patch.object(writer, "validate") as validate:
            with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
                writer.execute("/not-a-run")
            with self.assertRaisesRegex(w0.ContractError, "allow-gpu"):
                writer.worker("/not-a-run", "fit_r0_plus")
            validate.assert_not_called()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            self.prepare(root)
            with patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}), patch.object(w0, "gpu_identity") as gpu:
                with self.assertRaisesRegex(w0.ContractError, "reservation"):
                    writer.execute(root, True)
                gpu.assert_not_called()

    def test_exact_train_loop_steps_and_masks_no_training_library(self):
        fit = self.fits["r0_plus"]
        with tempfile.TemporaryDirectory() as folder, patch.object(w0, "finite_train_step", return_value=.1) as step:
            result = writer.train_rows(None, None, None, fit["rows"], Path(folder), time.time() + 60)
            self.assertEqual(step.call_count, 256)
            self.assertEqual(result["optimizer_steps"], 256)
            self.assertEqual(result["target_tokens"], 2 * sum(len(row["encoded"]["response_ids"]) for row in fit["rows"]))
            self.assertEqual([call.args[-1] for call in step.call_args_list], [row["encoded"] for row in fit["rows"]] * 2)
            with self.assertRaises(FileExistsError):
                writer.train_rows(None, None, None, fit["rows"], Path(folder), time.time() + 60)

    def test_timeout_parent_command_start_and_controller_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = "off_generate"
            directory = root / "stages" / stage
            directory.mkdir(parents=True)
            wall = time.time() - 1
            manifest = {"test": True}
            job = dict(manifest_sha256=w0.digest(manifest), deadline_unix=wall + 60)
            started = dict(manifest_sha256=w0.digest(manifest), job_sha256=w0.digest(job), wall_start=wall,
                deadline_unix=wall + 60, controller_pid=101, controller_start_ticks=123)
            parent = dict(pid=202, ppid=101, pgid=202, session=202, start_ticks=456)
            command = [carrier.TIMEOUT_BINARY, "--signal=KILL", "50.000s", *writer.worker_command(root, stage)]
            supervisor = dict(identity=parent, command=command, timeout_seconds=50., launch_wall=wall, deadline_unix=wall + 60)
            w0.write_once(root, "STARTED.json", started)
            w0.write_once(directory, "STARTED.json", started)
            w0.write_once(directory, "SUPERVISOR.json", supervisor)
            read_bytes = Path.read_bytes
            command_bytes = b"\0".join(part.encode() for part in command) + b"\0"
            with patch.object(carrier, "process_identity", side_effect=lambda pid: dict(parent) if pid == 202 else dict(start_ticks=123)) as identity, \
                    patch.object(os, "getppid", return_value=202), patch.object(os, "getpgrp", return_value=202), \
                    patch.object(os, "getsid", return_value=202), \
                    patch.object(Path, "read_bytes", new=lambda path: command_bytes if path.name == "cmdline" else read_bytes(path)):
                writer.validate_parent(root, stage, job, manifest)
                self.assertIn("organism_v6.semantic_writer_diagnostic", command)
                command_bytes = b"wrong-module\0"
                with self.assertRaisesRegex(w0.ContractError, "timeout/controller binding"):
                    writer.validate_parent(root, stage, job, manifest)
                command_bytes = b"\0".join(part.encode() for part in command) + b"\0"
                for replacement in (dict(parent, start_ticks=999), dict(parent, ppid=999)):
                    identity.side_effect = lambda pid, value=replacement: value if pid == 202 else dict(start_ticks=123)
                    with self.assertRaisesRegex(w0.ContractError, "timeout/controller binding"):
                        writer.validate_parent(root, stage, job, manifest)
                identity.side_effect = lambda pid: dict(parent) if pid == 202 else dict(start_ticks=999)
                with self.assertRaisesRegex(w0.ContractError, "timeout/controller binding"):
                    writer.validate_parent(root, stage, job, manifest)

    def test_fit_facade_exact_lora_optimizer_and_clean_base(self):
        torch, peft, base, model, parameter = Mock(), Mock(), Mock(), Mock(), Mock()
        peft.get_peft_model.return_value = model
        torch.count_nonzero.return_value.item.return_value = 0
        initial = {"layer.lora_B.default.weight": Mock()}
        config = {"fixture": True}
        with patch.dict(sys.modules, {"peft": peft}), patch.object(w0, "load_hf_model", return_value=base) as load, \
                patch.object(w0, "lora_tensors", side_effect=[{}, initial]) as tensors, \
                patch.object(w0, "validate_trainables", return_value=[("lora", parameter)]):
            result = writer.fit_model(torch, config)
            load.assert_called_once_with(config, torch)
            peft.LoraConfig.assert_called_once_with(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                target_modules=list(w0.RECIPE["target_modules"]), task_type="CAUSAL_LM", init_lora_weights=True)
            peft.get_peft_model.assert_called_once_with(base, peft.LoraConfig.return_value)
            torch.optim.AdamW.assert_called_once_with([parameter], lr=3e-5, betas=(.9, .999), eps=1e-8,
                weight_decay=.01, foreach=False, fused=False)
            model.train.assert_called_once_with()
            self.assertEqual(result, (model, torch.optim.AdamW.return_value, initial))
            tensors.side_effect = [initial]
            with self.assertRaisesRegex(w0.ContractError, "without an adapter"):
                writer.fit_model(torch, config)
            self.assertEqual(peft.get_peft_model.call_count, 1)
            tensors.side_effect = [{}, initial]
            torch.count_nonzero.return_value.item.return_value = 1
            with self.assertRaisesRegex(w0.ContractError, "zero-B init"):
                writer.fit_model(torch, config)
            self.assertEqual(torch.optim.AdamW.call_count, 1)

    def mock_stage(self, root, manifest, requests, fits, stage, state, operation, deadline, adapters):
        directory = root / "stages" / stage
        directory.mkdir()
        position = [row[0] for row in writer.stage_plan()].index(stage)
        pid = 1000 + position
        parent = 2000 + position
        wall = time.time()
        selected = [row for row in requests if row["state"] == state and row["operation"] == operation]
        adapter_hash = "OFF" if state == "OFF" or operation == "fit" else adapters[state]["adapter_sha256"]
        expected_lora = None if state == "OFF" or operation == "fit" else adapters[state]["final_lora_sha256"]
        job = dict(version=writer.VERSION, state=state, operation=operation, manifest_sha256=w0.digest(manifest),
            deadline_unix=min(deadline, wall + 3600), adapter_sha256=adapter_hash, expected_lora_sha256=expected_lora,
            fit_sha256=w0.digest(fits[state]) if operation == "fit" else None,
            request_ids=[row["request_id"] for row in selected])
        identity = dict(pid=pid, start_ticks=pid, ppid=parent, pgid=parent, session=parent)
        common = dict(identity=identity, parent_timeout_pid=parent, job_sha256=w0.digest(job), manifest_sha256=w0.digest(manifest),
            sources_sha256=w0.digest(manifest["sources"]), model_sha256=manifest["config"]["model_sha256"],
            tokenizer_sha256=manifest["config"]["tokenizer_sha256"], environment_sha256=w0.digest(manifest["config"]["environment"]),
            state=state, operation=operation, seed=fits[state]["seed"] if operation == "fit" else 0, hardware={})
        load = dict(common, training=operation == "fit", adapter_sha256="OFF_CLEAN_BASE" if operation == "fit" else adapter_hash,
                    expected_lora_sha256=expected_lora)
        if operation == "fit":
            path = directory / "adapter"
            path.mkdir()
            (path / "adapter_model.safetensors").write_text(state)
            (path / "adapter_config.json").write_text("{}")
            with (directory / "steps.jsonl").open("xb") as stream:
                for index in range(256):
                    stream.write(w0.canonical(dict(step=index + 1, epoch=index // 128, row=index % 128, loss=.1, seconds=0)))
            result = dict(adapter_sha256=w0.tree_hash(path), final_lora_sha256=w0.digest(state), update_norm=1,
                fit_sha256=w0.digest(fits[state]), recipe=w0.EXECUTION_RECIPE, optimizer_steps=256,
                steps_sha256=w0.file_hash(directory / "steps.jsonl"), target_tokens=2 * sum(len(row["encoded"]["response_ids"]) for row in fits[state]["rows"]))
        else:
            raw = directory / "raw"
            raw.mkdir()
            for request in selected:
                w0.write_once(raw, request["request_id"] + ".json", self.record(request, w0.digest(load), adapter_hash))
            result = dict(request_count=len(selected), raw_sha256=w0.tree_hash(raw))
        done = dict(**common, load_id=w0.digest(load), result=result)
        start = dict(wall_start=wall, deadline_unix=job["deadline_unix"], job_sha256=w0.digest(job), controller_pid=os.getpid(),
                     controller_start_ticks=carrier.process_identity(os.getpid())["start_ticks"])
        supervisor = dict(identity=dict(pid=parent, pgid=parent, session=parent, ppid=os.getpid(), start_ticks=parent),
            timeout_seconds=50., launch_wall=wall, deadline_unix=job["deadline_unix"],
            command=[carrier.TIMEOUT_BINARY, "--signal=KILL", "50.000s", *writer.worker_command(root, stage)])
        for name, value in (("JOB.json", job), ("STARTED.json", start), ("SUPERVISOR.json", supervisor), ("LOAD.json", load),
            ("CLAIMED.json", dict(identity=identity, job_sha256=w0.digest(job), parent_timeout_pid=parent)), ("DONE.json", done),
            ("COST.json", dict(returncode=0, seconds=0., wall_finish=time.time())),
            ("CLEANUP.json", dict(pid=parent, owned_group_empty=True, cancellation_signal=None, error=None))):
            w0.write_once(directory, name, value)
        (directory / "worker.log").touch()
        return done

    def test_complete_mock_execution_and_exact_cpu_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            config = self.prepare(root)
            with patch.object(writer, "pin_inputs", return_value={}), patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(w0, "gpu_identity", return_value={}), patch.object(w0, "assert_gpu_idle"), \
                    patch.object(w0, "assert_output_fds_outside_run"), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": config["gpu_uuid"]}), \
                    patch.object(writer, "run_stage", side_effect=self.mock_stage) as run:
                report = writer.execute(root, True)
                self.assertEqual(report["label"], "MULTIKEY_BINDING_PASS")
                self.assertEqual(run.call_count, 14)
                self.assertEqual([call.args[4] for call in run.call_args_list], [stage for stage, _, _ in writer.stage_plan()])
                self.assertEqual(report, writer.replay(root))
                with self.assertRaisesRegex(w0.ContractError, "no retry"):
                    writer.execute(root, True)
                path = root / "stages/eval_r1_minus_score/LOAD.json"
                with path.open("ab") as stream:
                    stream.write(b" ")
                with self.assertRaisesRegex(w0.ContractError, "inventory drift"):
                    writer.replay(root)

    def test_failed_off_copy_bank_never_fits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "run"
            config = self.prepare(root)

            def bad_copy(*args):
                result = self.mock_stage(*args)
                if args[4] == "off_generate":
                    request = next(row for row in self.requests if row["state"] == "OFF" and row["audit"]["family"] == "copy")
                    path = root / "stages/off_generate/raw" / (request["request_id"] + ".json")
                    record = w0.load_json(path)
                    record["output"].update(text="", generated_ids=[0], eos_terminated=True, truncated=False,
                                            decoded_with_terminal_eos="<eos>")
                    path.write_bytes(w0.canonical(record))
                return result

            with patch.object(writer, "pin_inputs", return_value={}), patch.object(w0, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(w0, "gpu_identity", return_value={}), patch.object(w0, "assert_gpu_idle"), \
                    patch.object(w0, "assert_output_fds_outside_run"), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": config["gpu_uuid"]}), \
                    patch.object(writer, "run_stage", side_effect=bad_copy) as run:
                with self.assertRaisesRegex(w0.ContractError, "zero fits"):
                    writer.execute(root, True)
                self.assertEqual(run.call_count, 2)
            self.assertTrue((root / "FAILED.json").exists())
            self.assertFalse((root / "SEAL.json").exists())

    def test_config_template_cli_is_plain_json_and_pins_are_required(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            writer.main(["config-template"])
        self.assertEqual(json.loads(stream.getvalue()), writer.config_template())
        with self.assertRaises(w0.ContractError):
            writer.validate_config(writer.config_template())
        with tempfile.TemporaryDirectory() as folder:
            config = self.config(Path(folder))
            writer.validate_config(config)
            config["lease_cutoff_unix"] = config["lease_end_unix"] - 21599
            with self.assertRaisesRegex(w0.ContractError, "six-hour"):
                writer.validate_config(config)


if __name__ == "__main__":
    unittest.main()
