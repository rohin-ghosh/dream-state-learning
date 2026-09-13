"""Synthetic CPU captures and V3-shaped files; no native model or training."""

import copy
from dataclasses import asdict
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_readout as api
import test_astra_pcfl_native_actor as actor_fixtures
from test_pcfl_event_sequence import SyntheticTokenizer


class Tokenizer(SyntheticTokenizer):
    chat_template = actor_fixtures.Tokenizer.chat_template
    apply_chat_template = actor_fixtures.Tokenizer.apply_chat_template

    def __init__(self, path):
        super().__init__()
        self.name_or_path = str(path)
        self.mismatch = False


class Session:
    def __init__(self, harness, config):
        self.harness, self.config = harness, config
        self.tokenizer, self.route = harness.tokenizer, api.reader.route_identity(config)
        self.calls, self.closed = [], 0
        harness.clock.now += 2

    def verify_shutdown(self):
        return {"method": "SYNTHETIC.shutdown", "source": self.config["shutdown_binding"]}

    def generate(self, prompt, sampling):
        index = len(self.calls)
        self.calls.append((prompt, copy.deepcopy(sampling)))
        self.harness.clock.now += .01
        raw = {"text": self.harness.texts[index], "prompt_token_ids": self.tokenizer.encode(prompt),
               "output_token_ids": self.tokenizer.encode(self.harness.texts[index]),
               "finish_reason": self.harness.finishes[index], "stop_reason": None, "route": copy.deepcopy(self.route)}
        return self.harness.mutate(raw)

    def close(self):
        self.closed += 1
        self.harness.after_calls()
        return {**self.verify_shutdown(), "shutdown_returned": self.harness.shutdown_ok}


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        fixture = actor_fixtures.ActorTests("test_constructor_and_unused_close_are_lazy")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root, self.model, self.clock = fixture.root, fixture.model, fixture.clock
        self.env = {"native": fixture.environment, "peft_version": "SYNTHETIC"}
        self.tokenizer = Tokenizer(self.model)
        rows, generations, queries = [], [], {}
        for index, letter in enumerate("ABCDEFGH"):
            fields = {"event": "E_" + letter * 10, "source": "N_" + letter * 10, "port": "P_" + letter * 10,
                      "destination": "N_ZZZZZZZZZZ", "receipt": "R_" + letter * 10}
            raw = api.sequence.core.EVENT_WIRE.format(**fields)
            rows.append({"fields": fields, "raw": raw})
            generations.append({"raw": raw, "sha256": api.native.text_hash(raw), "capture_sha256": api.prefix.digest([index]),
                                "origin": "SYNTHETIC_NOT_NATIVE"})
            queries["READ EVENT " + fields["event"]] = {"support": [fields["event"]], "target": raw, "source_sha256": api.prefix.digest([raw])}
        self.imported = api.prefix.seal({"rows": rows, "generations": generations, "queries": queries,
            "original_status": "FORMATION_FAILED", "original_returncode": 1, "original_calls": 17, "format_scaffold": "SYNTHETIC",
            "evidence": {"files": {"manifest.json": api.prefix._record(api.prefix.canonical({"binding": {"base_state_sha256": "b" * 64}}))}}})
        self.patch(patch.dict(os.environ, {name: "1" for name in api.fit.OFFLINE}))
        self.patch(patch.object(api.prefix, "validate_import", side_effect=lambda data, expected: api.prefix.unseal(data, expected)))
        self.patch(patch.object(api.prefix, "build_import", return_value=self.imported))
        self.patch(patch.object(api.prefix, "load_evidence", return_value={"SYNTHETIC": True}))
        self.patch(patch.object(api.prefix, "verify_tokenizer", return_value={"status": "SYNTHETIC_NOT_NATIVE",
            "tokenizer_files": fixture.config["tokenizer_files"], "chat_template_sha256": fixture.config["chat_template_sha256"]}))
        archive = self.root / "archive.tar"
        archive.write_bytes(b"SYNTHETIC_NOT_ARCHIVE")
        self.patch(patch.object(api.prefix, "ARCHIVE_SHA256", api.fit.file_hash(archive)))
        self.material = api.sequence.export_material(self.imported, self.imported["sha256"], self.tokenizer)
        binding = fixture.config["model_binding"]
        files = {name: entry["sha256"] for name, entry in api.fit.read_pin(binding)["files"].items()}
        self.inputs = {"schema": api.SCHEMA + "/inputs", "model_path": str(self.model), "gpu_uuid": "GPU-SYNTHETIC",
            "source_files": api.source_files(), "environment": self.env, "model_binding": binding,
            "material": self.store("material.json", self.material), "archive": self.pin(archive),
            "replay_receipt": self.store("replay.json", api.prefix.seal({"SYNTHETIC": True})),
            "base_state_receipt": self.store("cpu.json", {"schema": "pcfl.own_write.cpu_base_state.v1", "status": "COMPLETE",
                "device": "cpu", "dtype": "bfloat16", "environment": self.env, "base_state_sha256": "b" * 64,
                "model_binding_sha256": binding["sha256"], "model_files": files}),
            "shutdown_binding": self.pin(Path(__file__).resolve()), "fit_receipt": None}
        self.texts = [record["target"] for record in self.material["spec"]["records"]] * 2
        self.finishes, self.shutdown_ok = ["stop"] * 16, True
        self.sessions, self.counter = [], 0
        self.mutate = lambda raw: raw
        self.after_calls = lambda: None

    def patch(self, context):
        value = context.start()
        self.addCleanup(context.stop)
        return value

    def pin(self, path):
        return {"path": str(path), "sha256": api.fit.file_hash(path)}

    def store(self, name, value):
        path = self.root / name
        path.write_bytes(api.prefix.canonical(value) + b"\n")
        return self.pin(path)

    def actor(self, settings):
        def load(config):
            session = Session(self, config)
            self.sessions.append(session)
            return session
        return api.reader.ReadoutActor(settings, loader=load, environment_reader=lambda: self.env["native"], clock=self.clock)

    def run_readout(self, state="NO_WRITE", output=None):
        self.counter += 1
        pin = self.store(f"inputs{self.counter}.json", self.inputs)
        self.output = output or self.root / f"read{self.counter}"
        return api.run_state(pin["path"], pin["sha256"], self.output, 1000, state=state,
                            tokenizer_factory=lambda config: self.tokenizer, actor_factory=self.actor,
                            environment_reader=lambda: self.env, clock=self.clock)

    def completed_fit(self, phase="S_A"):
        root = self.root / ("fit_" + phase)
        checkpoint = root / "checkpoint"
        checkpoint.mkdir(parents=True)
        config = api.sequence.training_config(phase, self.model, device="cpu")
        selected = self.material["phases"][phase]
        api.write(root / "config.json", asdict(config))
        api.write(root / "corpus.json", selected["items"])
        api.write(checkpoint / "adapter_config.json", {"base_model_name_or_path": str(self.model), "r": 8,
            "lora_alpha": 16, "lora_dropout": .05, "peft_type": "LORA", "bias": "none", "modules_to_save": None})
        (checkpoint / "adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_TENSORS")
        (checkpoint / "README.md").write_text("SYNTHETIC CHECKPOINT")
        (checkpoint / "DONE").write_text("ok\n")
        api.write(checkpoint / "train_meta.json", {"SYNTHETIC": True})
        api.write(checkpoint / "train_manifest.json", {"recipe": api.v3.RECIPE, "empty": False,
            "config": asdict(config), "base_model": str(self.model), "steps": config.max_steps,
            "micro_batches": config.max_steps, "nonfinite_batches": 0, "final_loss": 1,
            "corpus": {"file": "corpus.json", "sha256": api.fit.file_hash(root / "corpus.json"),
                       "n_items": selected["presentations"], "n_encoded": selected["presentations"], "n_skipped_no_target": 0},
            "truncation": dict.fromkeys(("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"), 0),
            "tokens": {"target": selected["supervised_tokens"], "total": selected["input_tokens"]}})
        receipt = api.prefix.seal({"schema": api.fit.SCHEMA + "/completed", "status": "COMPLETE", "phase": phase,
            "kind": "INJECTED_CPU_TEST", "updates": config.max_steps, "base_unchanged": True, "nonfinite_batches": 0,
            "material_sha256": self.inputs["material"]["sha256"], "export_sha256": self.material["sha256"],
            "spec_sha256": self.material["spec"]["sha256"], "import_sha256": self.imported["sha256"],
            "items_sha256": selected["items_sha256"], "encoding_sha256": selected["encoding_sha256"],
            "model_binding": self.inputs["model_binding"], "base_state_receipt": self.inputs["base_state_receipt"],
            "checkpoint": str(checkpoint), "files": api.v3._warm_inventory(root)})
        api.write(root / "completed.json", receipt)
        self.inputs["fit_receipt"] = self.pin(root / "completed.json")
        return root

    def test_c0_exact16_order_tokens_no_training_or_history(self):
        with patch.object(api.v3, "run_training", side_effect=AssertionError("no training")):
            result = self.run_readout()
        self.assertEqual((result["kind"], result["calls"], result["fits"], result["updates"]), ("INJECTED_CPU_TEST", 16, 0, 0))
        self.assertIsNone(result["route"]["lora_request"])
        self.assertFalse(result["gpu_released"])
        session = self.sessions[0]
        self.assertEqual((len(session.calls), session.closed), (16, 1))
        totals = [0, 0]
        for index, row in enumerate(self.material["spec"]["roster"]):
            requested = api.read(self.output / f"actor/call_{index:04d}.request.json")
            raw = api.read(self.output / f"actor/call_{index:04d}.raw.json")["raw"]
            self.assertEqual(requested["messages"], api.reader.public_messages(row))
            self.assertEqual(len(requested["messages"]), 2)
            self.assertEqual(raw["text"], self.texts[index])
            self.assertEqual(session.calls[index][1], {**api.native.SAMPLING, "seed": 0, "max_tokens": 2048})
            totals[0] += len(raw["prompt_token_ids"])
            totals[1] += len(raw["output_token_ids"])
        self.assertEqual(result["tokens"], dict(zip(("prompt", "output"), totals)))
        self.assertEqual(result["panels"]["W8"]["A"]["strict_stop"], [True] * 4)
        self.assertEqual(result["files"], {name: value for name, value in api.v3._warm_inventory(self.output).items() if name != "completed.json"})
        load = api.read(self.output / "actor/load.json")
        request = api.read(self.output / "actor/call_0000.request.json")
        self.assertLess(request["started"], load["ready_at"])

    def test_sa_v3_metadata_not_mounted_and_checkpoint_untouched(self):
        fit_root = self.completed_fit()
        before = api.v3._warm_inventory(fit_root)
        result = self.run_readout("S_A")
        adapter = Path(result["route"]["lora_request"]["path"])
        self.assertEqual({path.name for path in adapter.iterdir()}, {"adapter_config.json", "adapter_model.safetensors", "README.md"})
        for path in adapter.iterdir():
            self.assertEqual(path.read_bytes(), (fit_root / "checkpoint" / path.name).read_bytes())
        self.assertEqual(api.v3._warm_inventory(fit_root), before)
        self.assertNotEqual(adapter, fit_root / "checkpoint")
        self.assertEqual(result["route"], self.sessions[0].route)
        self.assertEqual(result["state"], "S_A")

    def test_whole_raw_strict_stop_no_newline_salvage(self):
        self.texts[0] = self.texts[0].rstrip("\n")
        self.finishes[1] = "length"
        self.texts[2] = "MISS"
        self.texts[3] = "explanation\n" + self.texts[3]
        result = self.run_readout()
        self.assertEqual(result["panels"]["W0"]["A"]["strict_stop"], [False] * 4)
        self.assertEqual(result["panels"]["W8"]["A"]["correct"], 4)
        self.assertEqual(result["truncated"], 1)
        scores = api.read(self.output / "scores.json")
        self.assertTrue(scores["results"][0]["score"]["semantic"])
        self.assertTrue(scores["results"][1]["score"]["strict"])
        self.assertEqual(scores["results"][0]["raw"], self.texts[0])
        self.assertIsNone(scores["pass_threshold"])

    def test_missing_wrong_injected_or_failed_fit_rejected(self):
        with self.assertRaisesRegex(ValueError, "completion"):
            self.run_readout("S_A")
        fit_root = self.completed_fit("FRESH_MIX")
        with self.assertRaisesRegex(ValueError, "matching completed"):
            self.run_readout("S_A")
        with self.assertRaisesRegex(ValueError, "NO_WRITE"):
            self.run_readout()
        with self.assertRaisesRegex(ValueError, "matching completed"):
            api._checkpoint(self.inputs, self.material, "FRESH_MIX", self.root / "other", "NATIVE")
        api.write(fit_root / "failure.json", {"SYNTHETIC": True})
        with self.assertRaisesRegex(ValueError, "failed fit"):
            self.run_readout("FRESH_MIX")
        self.assertEqual(self.sessions, [])

    def test_output_reuse_and_source_or_checkpoint_tamper_fail(self):
        self.run_readout()
        output = self.output
        before = api.v3._warm_inventory(output)
        with self.assertRaisesRegex(ValueError, "fresh output"):
            self.run_readout(output=output)
        self.assertEqual(api.v3._warm_inventory(output), before)
        fit_root = self.completed_fit()
        (fit_root / "checkpoint/adapter_model.safetensors").write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError, "fit file drift"):
            self.run_readout("S_A")
        self.inputs["source_files"][str(Path(api.__file__).resolve())] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source pins"):
            self.run_readout()

    def test_route_error_retains_raw_and_closes_without_success(self):
        self.mutate = lambda raw: {**raw, "route": {**raw["route"], "arm": "WRONG"}}
        with self.assertRaisesRegex(ValueError, "route differs"):
            self.run_readout()
        self.assertTrue((self.output / "actor/call_0000.raw.json").is_file())
        self.assertTrue((self.output / "failure.json").is_file())
        self.assertFalse((self.output / "completed.json").exists())
        self.assertEqual(self.sessions[0].closed, 1)

    def test_shutdown_and_capture_token_or_time_tamper_fail(self):
        self.shutdown_ok = False
        with self.assertRaisesRegex(ValueError, "close/load"):
            self.run_readout()
        self.shutdown_ok = True
        def tamper_tokens():
            path = self.output / "actor/call_0000.raw.json"
            raw = api.read(path)
            raw["raw"]["output_token_ids"].append(999)
            path.write_bytes(api.prefix.canonical(raw))
        self.after_calls = tamper_tokens
        with self.assertRaisesRegex(ValueError, "token counts"):
            self.run_readout()
        def tamper_time():
            path = self.output / "actor/call_0000.raw.json"
            raw = api.read(path)
            raw["generation_started"] = 0
            path.write_bytes(api.prefix.canonical(raw))
        self.after_calls = tamper_time
        with self.assertRaisesRegex(ValueError, "chronology"):
            self.run_readout()
        self.assertFalse((self.output / "completed.json").exists())

    def test_post_read_fit_mutation_not_accepted(self):
        fit_root = self.completed_fit()
        self.after_calls = lambda: (fit_root / "checkpoint/DONE").write_text("changed")
        with self.assertRaisesRegex(ValueError, "immutable fit"):
            self.run_readout("S_A")
        self.assertFalse((self.output / "completed.json").exists())

    def test_resealed_roster_changes_never_load_actor(self):
        for change in (lambda material: material["spec"]["roster"].pop(),
                       lambda material: material["spec"]["roster"][0].update(output_tokens=2047),
                       lambda material: material["spec"]["roster"][0].update(view=7)):
            altered = copy.deepcopy(self.material)
            altered.pop("sha256")
            change(altered)
            self.inputs["material"] = self.store("changed_material.json", api.prefix.seal(altered))
            with self.assertRaises(ValueError):
                self.run_readout()
        self.assertEqual(self.sessions, [])

    def test_bin_only_checkpoint_reports_compatibility_blocker(self):
        root = self.completed_fit()
        checkpoint = root / "checkpoint"
        (checkpoint / "adapter_model.safetensors").rename(checkpoint / "adapter_model.bin")
        receipt = api.read(root / "completed.json")
        receipt.pop("sha256")
        receipt["files"] = {name: value for name, value in api.v3._warm_inventory(root).items() if name != "completed.json"}
        (root / "completed.json").write_bytes(api.prefix.canonical(api.prefix.seal(receipt)))
        self.inputs["fit_receipt"] = self.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "requires safetensors; no bin conversion"):
            self.run_readout("S_A")
        self.assertEqual(self.sessions, [])

    def test_deadline_before_or_during_read_preserves_failure(self):
        self.clock.now = 1000
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.run_readout()
        self.assertEqual(self.sessions, [])
        self.clock.now = 10
        def late(raw):
            self.clock.now = 1001
            return raw
        self.mutate = late
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.run_readout()
        self.assertTrue((self.output / "actor/call_0000.raw.json").exists())
        self.assertFalse((self.output / "completed.json").exists())
        self.assertEqual(self.sessions[0].closed, 1)

    def test_missing_capture_and_same_length_token_tamper_fail(self):
        self.after_calls = lambda: (self.output / "actor/call_0015.raw.json").unlink()
        with self.assertRaisesRegex(ValueError, "raw call inventory"):
            self.run_readout()
        def changed_token():
            path = self.output / "actor/call_0000.raw.json"
            raw = api.read(path)
            raw["raw"]["output_token_ids"][0] = self.tokenizer.encode("XXX")[0]
            path.write_bytes(api.prefix.canonical(raw))
        self.after_calls = changed_token
        with self.assertRaisesRegex(ValueError, "captured token decode"):
            self.run_readout()
        self.assertFalse((self.output / "completed.json").exists())

    def test_unchanged_reader_rejects_direct_v3_directory_mount(self):
        root = self.completed_fit()
        original_factory = self.actor
        def direct_mount(settings):
            altered = copy.deepcopy(settings)
            altered["adapter"]["path"] = str(root / "checkpoint")
            return original_factory(altered)
        self.actor = direct_mount
        with self.assertRaisesRegex(ValueError, "adapter inventory differs"):
            self.run_readout("S_A")
        self.assertEqual(self.sessions, [])

    def test_cli_runs_only_explicit_state(self):
        with patch.object(api, "run_state", return_value={"status": "COMPLETE", "state": "S_A", "sha256": "a" * 64}) as run:
            api.main(["--inputs", "/inputs.json", "--inputs-sha256", "b" * 64, "--output", "/fresh", "--deadline", "200", "--state", "S_A"])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs, {"state": "S_A"})


if __name__ == "__main__":
    unittest.main()
