"""CPU fixtures: final pure core and v3 encoder, synthetic models/processes only."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
CORE_PIN = "0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352"
if hashlib.sha256((ROOT / "organism_v6/l2_public_record_dev.py").read_bytes()).hexdigest() != CORE_PIN:
    raise RuntimeError("tests require Main's final Curie core, not in-progress code")
from organism_v6 import l2_public_record_dev as core
from organism_v6 import train_adapter_v3 as trainer

SPEC = importlib.util.spec_from_file_location("l2_runtime_under_test", ROOT / "gpu/astra_l2_public_record_dev.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class Tokenizer:
    eos_token, eos_token_id, pad_token_id = "<|im_end|>", 2, 0
    chat_template = "fixture-only-qwen-shaped-template"

    def encode(self, text, add_special_tokens=False):
        tokens = []
        while text:
            if text.startswith(self.eos_token):
                tokens.append(self.eos_token_id)
                text = text[len(self.eos_token):]
            else:
                tokens.append(ord(text[0]) + 100)
                text = text[1:]
        return tokens

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + self.eos_token + "\n"
                       for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class Probe:
    def __init__(self):
        self.tokenizer = Tokenizer()

    def native_tokenizer(self, model):
        return self.tokenizer

    def render(self, tokenizer, messages):
        rendered = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return dict(rendered_prompt=rendered, prompt_token_ids=tokenizer.encode(rendered),
                    actual_system_text=messages[0]["content"])


class Backend:
    def __init__(self, public, route=None, invalid_slots=(), rejected_slots=(), newline=False, observer=None):
        self.public, self.route = public, route
        self.invalid_slots, self.rejected_slots = invalid_slots, rejected_slots
        self.newline, self.observer, self.closed = newline, observer, False
        self.requests = []

    def generate(self, messages):
        prompt = messages[1]["content"]
        self.requests.append(deepcopy(messages))
        slot = next(slot for slot in self.public.slots if slot.key in prompt)
        record = core.PROCESS_TAPE in prompt
        if not record and slot.index in self.invalid_slots:
            text = "I decline to choose."
        elif record and slot.index in self.rejected_slots:
            text = "not an action"
        else:
            action = self.public.actions[0]
            if record and "\nPublic outcome: FAILURE\n" in prompt:
                action = self.public.actions[1]
            text = action + ("\n" if self.newline else "")
        if self.observer:
            self.observer(messages)
        native = Probe().render(Tokenizer(), messages)
        return dict(native=native, raw_hex=text.encode().hex(), text=text, decoded=text,
                    output_token_ids=list(range(len(text))), finish_reason="stop", stop_reason=None,
                    started=1.0, ended=2.0, route=self.route,
                    returned_prompt_token_ids=native["prompt_token_ids"])

    def close(self):
        self.closed = True


class Parameter:
    def __init__(self, finite=True):
        self.requires_grad, self.finite = True, finite

    def detach(self):
        return self

    def isfinite(self):
        return self

    def all(self):
        return self

    def item(self):
        return self.finite


def manifest_for(prepared, config):
    count = prepared["rows"]
    return dict(config=config, empty=False, steps=prepared["steps"], micro_batches=prepared["steps"],
                epochs_run=20, nonfinite_batches=0,
                corpus=dict(n_items=count, n_encoded=count, n_skipped_no_target=0, sha256=prepared["corpus_sha256"]),
                truncation=dict.fromkeys(("items_truncated", "context_tokens_dropped", "target_tokens_dropped",
                                          "items_split", "segments_from_splits"), 0),
                packing=dict(mode="one_item_per_sequence", n_sequences=count),
                tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"],
                            context=prepared["total_tokens"] - prepared["target_tokens"],
                            target_by_category=dict(child_action=prepared["target_tokens"] - count, assistant_end=count),
                            target_by_view=dict(source_withdrawn_action=prepared["target_tokens"])),
                train_tokens_seen=20 * prepared["total_tokens"], mean_loss_per_epoch=[1.] * 20, final_loss=1.)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="l2-runtime-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "root"
        self.root.mkdir()
        self.world = core.build_world(2026091301, 2026091302)
        self.public = core.public_view(self.world)
        self.probe = Probe()
        self.plan = dict(root=str(self.root), base_sha256="a" * 64, chat_template=Tokenizer.chat_template,
                         spec=dict(model="/fixture/model", source="/fixture/source", gpu_uuid="GPU-fixture", gpu_index=0,
                                   lease_end=time.time() + 100000), python=sys.executable,
                         config=asdict(trainer.TrainConfig(**runtime.RECIPE, model="/fixture/model")))
        self.states = core.start_pair(self.public, self.plan["base_sha256"])
        self.backends, self.models = [], []
        self.reflection = SimpleNamespace(load_native_model=self.load_model, check_adapter=lambda *args: None)

    def load_model(self, model):
        model = SimpleNamespace(named_parameters=lambda: [("model.q_proj.lora_A.weight", Parameter()),
                                                           ("model.q_proj.lora_B.weight", Parameter())])
        self.models.append(model)
        return Tokenizer(), model

    def capture(self, stage, invalid=(), rejected=(), newline=False, observer=None):
        def factory(route):
            backend = Backend(self.public, route, invalid, rejected, newline, observer)
            self.backends.append(backend)
            return backend
        return runtime.capture_stage(self.plan, core, self.world, self.states, stage, factory)

    def close(self, stage, result):
        directory = runtime.stage_dir(self.plan, stage)
        runtime.write(directory / "data/result.json", result)
        runtime.write(directory / "CLOSED.json", dict(stage=stage, pid=10001, files=runtime.tree(directory / "data")))
        runtime.advance(core, self.public, self.states, stage, result)

    def fake_training(self, items, tokenizer, model, config, out, corpus_sha, corpus_name):
        directory = Path(out)
        prepared = runtime.read(directory.parent / "training.json")
        manifest = manifest_for(prepared, asdict(config))
        runtime.write(directory / "train_manifest.json", manifest)
        runtime.write(directory / "adapter_model.fixture.json", dict(child_records=prepared["corpus_sha256"], stage=corpus_name))
        runtime.write(directory / "DONE", dict(mock=True))
        return manifest

    def fit(self, stage):
        with patch.object(trainer, "run_training", side_effect=self.fake_training):
            return runtime.fit_stage(self.plan, core, trainer, self.probe, self.reflection, self.world, self.states, stage)

    def shared(self, invalid=(), rejected=(), newline=False):
        self.close("wake1", self.capture("wake1", invalid, rejected, newline))
        result = self.fit("fit1")
        self.close("fit1", result)
        return result

    def finish(self, invalid=(), rejected=()):
        def runner(stage):
            result = self.fit(stage) if stage.startswith("fit") else self.capture(stage, invalid, rejected, newline=True)
            self.close(stage, result)
            return result
        return runtime.execute_loop(self.plan, core, self.world, runner)

    def seal(self, terminal):
        runtime.write(self.root / "plan.json", self.plan)
        checksum = runtime.digest(self.root / "plan.json")
        terminal.update(deadline=100.0)
        runtime.finalize(self.root, terminal, checksum, 100.0, clock=lambda: 1.0)
        return checksum


class CaptureTests(Fixture):
    def test_invalid_actions_skip_feedback_and_records(self):
        with patch.object(core, "feedback", wraps=core.feedback) as feedback:
            result = self.capture("wake1", invalid=(0, 3))
        self.assertEqual(result["calls"], 14)
        self.assertEqual(feedback.call_count, 6)
        capture = core.from_data(result["capture"], expected_type=core.CapturedBlock)
        for index in (0, 3):
            self.assertIsNone(capture.episodes[index].outcome)
            self.assertIsNone(capture.episodes[index].record)
            self.assertEqual(runtime.read(self.root / "run/wake1/data" / f"episode_{index:02d}.json")["status"], "INVALID_ACTION")
        corpus = core.compile_corpus(self.public, (capture,), expected_hashes=(core.digest(capture),))
        self.assertEqual([entry.reason for entry in corpus.rejected], ["INVALID_ACTION"] * 2)

    def test_raw_action_is_durable_before_feedback(self):
        original = core.feedback
        def feedback(world, action, sequence):
            responses = list((self.root / "run/wake1/data").glob("*.response.json"))
            self.assertTrue(any(runtime.read(path)["raw_hex"] == action.raw.hex() for path in responses))
            return original(world, action, sequence=sequence)
        with patch.object(core, "feedback", side_effect=feedback):
            self.capture("wake1")

    def test_invalid_records_are_retained_not_repaired(self):
        self.close("wake1", self.capture("wake1", rejected=(1, 4)))
        self.assertEqual(len(self.states["PROMOTE"].corpus.rows), 6)
        self.assertEqual(len(self.states["PROMOTE"].corpus.rejected), 2)

    def test_optional_newline_survives_wire_and_target(self):
        self.close("wake1", self.capture("wake1", newline=True))
        self.assertTrue(all(row.target.endswith(b"\n") for row in self.states["PROMOTE"].corpus.rows))
        restored = core.from_data(core.to_data(self.states), expected_type=dict)
        core.check_pair(self.public, restored)
        self.assertEqual(restored, self.states)

    def test_process_tape_only_on_record_calls(self):
        self.capture("wake1")
        for index, request in enumerate(self.backends[0].requests):
            self.assertEqual(core.PROCESS_TAPE in request[1]["content"], index % 2 == 1)
            self.assertEqual(request[0], dict(role="system", content=runtime.GENERIC_SYSTEM))

    def test_route_spoof_preserves_raw_and_closes_backend(self):
        backend = Backend(self.public)
        original = backend.generate
        def generate(messages):
            result = original(messages)
            result["route"] = {"wrong": "adapter"}
            return result
        backend.generate = generate
        with self.assertRaisesRegex(ValueError, "route"):
            runtime.capture_stage(self.plan, core, self.world, self.states, "wake1", lambda route: backend)
        self.assertTrue(backend.closed)
        self.assertTrue((self.root / "run/wake1/data/00.response.json").exists())

    def test_length_finish_is_not_an_integrity_abort(self):
        backend = Backend(self.public)
        response = backend.generate(runtime.messages(core.action_prompt(self.public, self.public.slots[0].slot_id)))
        response["finish_reason"] = "length"
        runtime.validate_response(response, None)

    def test_33_output_tokens_rejected(self):
        response = Backend(self.public).generate(runtime.messages(core.action_prompt(self.public, self.public.slots[0].slot_id)))
        response["output_token_ids"] = list(range(33))
        with self.assertRaisesRegex(ValueError, "work"):
            runtime.validate_response(response, None)

    def test_double_newline_is_invalid_not_trimmed(self):
        self.assertIsNone(runtime.legal_action(self.public, self.public.actions[0].encode() + b"\n\n"))
        self.assertIsNone(runtime.legal_action(self.public, b" " + self.public.actions[0].encode()))


class TrainingTests(Fixture):
    def prepared(self, newline=False, rejected=()):
        self.close("wake1", self.capture("wake1", newline=newline, rejected=rejected))
        return runtime.encode_training(core, self.public, self.states["PROMOTE"].corpus,
                                       self.probe.tokenizer, trainer, self.probe)

    def test_full_child_target_plus_one_eos_no_metadata_loss(self):
        prepared = self.prepared(newline=True)
        for item, audit in zip(prepared["items"], prepared["encoding"]):
            self.assertEqual(item["spans"][1][0].encode().hex(), audit["target_hex"])
            labels = [label for label in audit["labels"] if label != -100]
            self.assertEqual(labels, Tokenizer().encode(item["spans"][1][0]) + [2])
            self.assertEqual(labels.count(2), 1)
            self.assertNotIn(core.PROCESS_TAPE, item["spans"][0][0])
            self.assertNotIn("meta", item)
            self.assertEqual(item["spans"][-1], ["\n", False, "template_tail"])
        self.assertEqual(prepared["steps"], 20)
        self.assertEqual(len(prepared["epoch_order"]), 20)

    def test_partial_nonempty_corpus_fits_once_without_filler(self):
        result = self.shared(rejected=(0, 1, 2, 3, 4, 5, 6))
        self.assertEqual((result["admitted"], result["rejected"], result["fits"], result["updates"]), (1, 7, 1, 20))
        self.assertEqual(self.states["PROMOTE"].phase, "AWAIT_BLOCK_2")

    def test_empty_corpus_shortage_does_not_load_model(self):
        result = self.shared(invalid=tuple(range(8)))
        self.assertEqual(result["status"], "FORMATION_SHORTAGE")
        self.assertEqual(self.models, [])
        self.assertIsNone(result["candidate_sha256"])

    def test_batch_tail_masks_and_cumulative_40steps(self):
        self.shared(newline=True)
        self.close("wake2_PROMOTE", self.capture("wake2_PROMOTE", rejected=tuple(range(9, 16))))
        result = self.fit("fit2_PROMOTE")
        self.assertEqual((result["admitted"], result["updates"]), (9, 40))
        prepared = runtime.read(self.root / "run/fit2_PROMOTE/data/training.json")
        self.assertTrue(all(len(order) == 9 for order in prepared["epoch_order"]))

    def test_truncation_rejected_before_model(self):
        self.close("wake1", self.capture("wake1"))
        original = self.probe.render
        def render(tokenizer, messages):
            result = original(tokenizer, messages)
            result["rendered_prompt"] = "x" * 1500 + result["rendered_prompt"]
            return result
        with patch.object(self.probe, "render", side_effect=render):
            with self.assertRaises(ValueError):
                self.fit("fit1")
        self.assertEqual(self.models, [])

    def test_manifest_recipe_exposure_nonfinite_and_step_drift(self):
        prepared = self.prepared()
        manifest = manifest_for(prepared, self.plan["config"])
        runtime.validate_manifest(manifest, self.plan["config"], prepared)
        changes = [("steps", 19), ("epochs_run", 19), ("nonfinite_batches", 1), ("final_loss", math.nan),
                   ("train_tokens_seen", 0), ("mean_loss_per_epoch", [1.0] * 19)]
        for field, value in changes:
            with self.subTest(field=field):
                broken = deepcopy(manifest)
                broken[field] = value
                with self.assertRaises(ValueError):
                    runtime.validate_manifest(broken, self.plan["config"], prepared)

    def test_nonfinite_final_trainable_state_preserves_candidate(self):
        self.close("wake1", self.capture("wake1"))
        model = SimpleNamespace(named_parameters=lambda: [("lora_A.weight", Parameter(False))])
        self.reflection.load_native_model = lambda path: (Tokenizer(), model)
        with self.assertRaisesRegex(ValueError, "nonfinite final"):
            self.fit("fit1")
        self.assertTrue((self.root / "run/fit1/data/adapter/DONE").exists())

    def test_non_lora_trainability_aborts(self):
        self.close("wake1", self.capture("wake1"))
        model = SimpleNamespace(named_parameters=lambda: [("base.weight", Parameter())])
        self.reflection.load_native_model = lambda path: (Tokenizer(), model)
        with self.assertRaisesRegex(ValueError, "non-LoRA"):
            self.fit("fit1")


class LoopTests(Fixture):
    def test_full_pair_128_calls_3fits_100updates(self):
        terminal = self.finish()
        self.assertEqual(terminal["status"], "COMPLETE")
        self.assertEqual(terminal["work"], runtime.CAPS)
        self.assertEqual(terminal["completed"], list(runtime.STAGES))
        self.assertEqual(len(self.models), 3)
        self.assertEqual(len({id(model) for model in self.models}), 3)
        self.assertEqual(self.states["PROMOTE"].sleeps[0].candidate_sha256,
                         self.states["SHADOW"].sleeps[0].candidate_sha256)
        self.assertEqual(self.states["SHADOW"].mounted_sha256, self.plan["base_sha256"])
        for state in self.states.values():
            self.assertTrue(all(sleep.initialized_from_sha256 == self.plan["base_sha256"] for sleep in state.sleeps))
        self.assertEqual([backend.route is not None for backend in self.backends],
                         [False, False, True, False, True, False, True, False])

    def test_branch_cumulative_material_stays_local(self):
        self.shared()
        self.close("wake2_PROMOTE", self.capture("wake2_PROMOTE", rejected=(8,)))
        self.close("wake2_SHADOW", self.capture("wake2_SHADOW", rejected=(9, 10)))
        self.assertEqual(len(self.states["PROMOTE"].corpus.rows), 15)
        self.assertEqual(len(self.states["SHADOW"].corpus.rows), 14)
        self.assertEqual(self.states["PROMOTE"].corpus.capture_hashes[0], self.states["SHADOW"].corpus.capture_hashes[0])
        self.assertNotEqual(self.states["PROMOTE"].corpus.capture_hashes[1], self.states["SHADOW"].corpus.capture_hashes[1])

    def test_reports_never_read_by_state_dependencies(self):
        self.finish()
        seen = []
        def reader(plan, stage):
            self.assertTrue(stage.startswith(("wake", "fit")))
            seen.append(stage)
            return runtime.read_stage(plan, stage)
        states = runtime.dependency_states(self.plan, core, self.world, "report2_SHADOW", reader)
        self.assertEqual(states, self.states)
        self.assertNotIn("baseline", seen)

    def test_shortage_stops_exact_prefix_no_two_cycle_claim(self):
        terminal = self.finish(invalid=tuple(range(8)))
        self.assertEqual(terminal["status"], "FORMATION_SHORTAGE")
        self.assertEqual(terminal["completed"], ["baseline", "wake1", "fit1"])
        self.assertFalse(terminal["two_cycle_complete"])
        self.assertEqual(terminal["work"], dict(calls=24, fits=0, updates=0))

    def test_misbound_not_a_stage_or_training_corpus(self):
        self.assertFalse(any("MISBOUND" in stage for stage in runtime.STAGES))
        self.close("wake1", self.capture("wake1"))
        corpus = self.states["PROMOTE"].corpus
        misbound = core.misbind_corpus(self.public, corpus, expected_sha256=core.digest(corpus))
        with self.assertRaisesRegex(ValueError, "authentic"):
            runtime.encode_training(core, self.public, misbound, Tokenizer(), trainer, self.probe)

    def test_candidate_drift_blocks_mount(self):
        self.shared()
        adapter = self.root / "run/fit1/data/adapter"
        runtime.write(adapter / "unexpected.json", dict(drift=True))
        with self.assertRaises(ValueError):
            runtime.route_for(self.plan, core, self.states, "report1_PROMOTE")

    def test_shared_baseline_fixed16_old8_new8(self):
        result = self.capture("baseline")
        scores = runtime.score_readouts(core, self.world, result)
        self.assertEqual(scores, dict(total=16, old_total=8, new_total=8, old_correct=4, new_correct=4, legal=16, malformed=0))
        self.assertEqual(result["calls"], 16)


class CollectionTests(Fixture):
    def collect_fixture(self, terminal):
        checksum = self.seal(terminal)
        output = Path(self.temporary.name) / "collection.json"
        with patch.object(runtime, "verify", return_value=(self.plan, core, trainer, self.probe, self.reflection, self.world)):
            return runtime.collect(str(self.root), checksum, output)

    def test_complete_replay_uses_actual_captures_and_masks(self):
        result = self.collect_fixture(self.finish())
        self.assertEqual(result["work"], runtime.CAPS)
        self.assertTrue(result["two_cycle_complete"])
        self.assertTrue(result["scientific_replay"])
        self.assertIsNone(result["scientific_pass"])
        self.assertFalse(result["endpoint"]["native_verified"])
        self.assertEqual(result["reports"]["baseline"]["old_correct"], 4)

    def test_shortage_reports_missing_not_zero_accuracy(self):
        result = self.collect_fixture(self.finish(invalid=tuple(range(8))))
        self.assertIsNone(result["reports"]["report2_PROMOTE"])
        self.assertIsNone(result["endpoint"])
        self.assertEqual(result["incomplete"], list(runtime.STAGES[3:]))
        self.assertFalse(result["two_cycle_complete"])

    def test_abort_collects_custody_without_invalid_stage_decode(self):
        runtime.write(self.root / "run/wake1/data/invalid.json", {"not": "a valid stage"})
        terminal = dict(status="NONREPORTABLE_RUNTIME_ABORT", completed=[], error={"type": "fixture"})
        checksum = self.seal(terminal)
        with patch.object(runtime, "verify", side_effect=AssertionError("abort must not replay invalid stage")):
            result = runtime.collect(str(self.root), checksum, Path(self.temporary.name) / "abort.json")
        self.assertFalse(result["scientific_replay"])
        self.assertTrue(result["failed_raw_stages_not_scored"])

    def test_seal_extra_missing_and_hash_drift(self):
        checksum = self.seal(dict(status="NONREPORTABLE_RUNTIME_ABORT"))
        runtime.write(self.root / "extra.json", {})
        with self.assertRaisesRegex(ValueError, "inventory"):
            runtime.custody(self.root, checksum)

    def test_missing_sealed_file_rejected(self):
        runtime.write(self.root / "retained.json", {})
        checksum = self.seal(dict(status="NONREPORTABLE_RUNTIME_ABORT"))
        (self.root / "retained.json").unlink()
        with self.assertRaisesRegex(ValueError, "inventory"):
            runtime.custody(self.root, checksum)

    def test_drifted_sealed_file_rejected(self):
        runtime.write(self.root / "retained.json", {})
        checksum = self.seal(dict(status="NONREPORTABLE_RUNTIME_ABORT"))
        (self.root / "retained.json").write_text('{"changed":true}\n')
        with self.assertRaisesRegex(ValueError, "inventory"):
            runtime.custody(self.root, checksum)

    def test_forged_final_witness_rejected(self):
        checksum = self.seal(dict(status="NONREPORTABLE_RUNTIME_ABORT"))
        path = self.root / "FINALIZED.json"
        witness = runtime.read(path)
        witness["seal_sha256"] = "0" * 64
        path.write_bytes(runtime.encoded(witness))
        with self.assertRaisesRegex(ValueError, "binding"):
            runtime.custody(self.root, checksum)

    def test_stage_seal_detects_extra_call(self):
        self.close("wake1", self.capture("wake1"))
        runtime.write(self.root / "run/wake1/data/99.response.json", {})
        with self.assertRaisesRegex(ValueError, "custody"):
            runtime.read_stage(self.plan, "wake1")

    def test_mismatched_native_request_is_rejected(self):
        result = self.capture("baseline")
        path = self.root / "run/baseline/data/00.request.json"
        request = runtime.read(path)
        request["messages"][1]["content"] += "secret score"
        path.write_bytes(runtime.encoded(request))
        with self.assertRaisesRegex(ValueError, "visibility"):
            runtime.replay_capture(self.plan, core, self.world, self.states, "baseline", result)

    def test_missing_final_witness_explicit_nonreportable(self):
        runtime.write(self.root / "plan.json", self.plan)
        checksum = runtime.digest(self.root / "plan.json")
        runtime.write(self.root / "terminal.json", dict(status="COMPLETE", deadline=100))
        runtime.write(self.root / "SEAL.json", dict(schema=runtime.SCHEMA, plan_sha256=checksum, files=runtime.tree(self.root)))
        terminal, files = runtime.custody(self.root, checksum)
        self.assertEqual(terminal["status"], "NONREPORTABLE_RUNTIME_ABORT")
        self.assertEqual(terminal["reason"], "missing final witness")

    def test_late_final_write_keeps_evidence_aborts(self):
        runtime.write(self.root / "plan.json", self.plan)
        checksum = runtime.digest(self.root / "plan.json")
        times = iter((99., 101.))
        status = runtime.finalize(self.root, dict(status="COMPLETE", deadline=100.), checksum, 100., clock=lambda: next(times))
        self.assertEqual(status, "NONREPORTABLE_RUNTIME_ABORT")
        self.assertEqual(runtime.read(self.root / "terminal.json")["status"], "COMPLETE")
        self.assertEqual(runtime.custody(self.root, checksum)[0]["status"], "NONREPORTABLE_RUNTIME_ABORT")

    def test_raw_response_tamper_rejected_by_replay(self):
        result = self.capture("wake1")
        capture = core.from_data(result["capture"], expected_type=core.CapturedBlock)
        action = capture.episodes[0].action
        forged = core.make_receipt(self.public, action.slot_id, "action", b"invalid", sequence=action.sequence, lineage=action.lineage)
        forged_capture = core.capture_block(self.public, 1, "SHARED", (core.Episode(forged),) + capture.episodes[1:])
        result["capture"] = core.to_data(forged_capture)
        with self.assertRaisesRegex(ValueError, "raw capture"):
            runtime.replay_capture(self.plan, core, self.world, self.states, "wake1", result)

    def test_write_once(self):
        path = self.root / "one.json"
        runtime.write(path, {"original": 1})
        with self.assertRaises(FileExistsError):
            runtime.write(path, {"new": 2})
        self.assertEqual(runtime.read(path), {"original": 1})

    def test_duplicate_json_and_nonfinite_rejected(self):
        for index, content in enumerate(('{"x":1,"x":2}', '{"x":NaN}')):
            path = self.root / f"bad{index}.json"
            path.write_text(content)
            with self.assertRaises(ValueError):
                runtime.read(path)

    def test_links_rejected(self):
        target = self.root / "target.json"
        runtime.write(target, {})
        (self.root / "symlink").symlink_to(target)
        with self.assertRaisesRegex(ValueError, "linked"):
            runtime.tree(self.root)

    def test_hardlinks_rejected(self):
        target = self.root / "target.json"
        runtime.write(target, {})
        os.link(target, self.root / "hardlink")
        with self.assertRaisesRegex(ValueError, "hardlinked"):
            runtime.tree(self.root)


class LifecycleTests(Fixture):
    def test_launcher_logs_cannot_mutate_sealed_root(self):
        with patch.object(runtime.os, "readlink", return_value=str(self.root / "controller.log")):
            with self.assertRaisesRegex(ValueError, "outside the sealed"):
                runtime.launcher_output_outside(self.root)

    def test_stage_timeout_and_cleanup_reserve(self):
        self.assertEqual(runtime.stage_seconds("fit1", 1000, 0), 600)
        self.assertEqual(runtime.stage_seconds("baseline", 1000, 0), 300)
        self.assertEqual(runtime.stage_seconds("fit1", 100, 50), 10)
        with self.assertRaises(ValueError):
            runtime.stage_seconds("fit1", 100, 60)

    def test_controller_verification_failure_seals_abort(self):
        runtime.write(self.root / "plan.json", self.plan)
        checksum = runtime.digest(self.root / "plan.json")
        with patch.object(runtime, "verify", side_effect=ValueError("bad pin")):
            status = runtime.controller(str(self.root), checksum, allow_gpu=True)
        self.assertEqual(status, "NONREPORTABLE_RUNTIME_ABORT")
        self.assertEqual(runtime.custody(self.root, checksum)[0]["error"]["message"], "bad pin")

    def test_controller_clock_starts_before_verification(self):
        runtime.write(self.root / "plan.json", self.plan)
        checksum = runtime.digest(self.root / "plan.json")
        def verify(*args, **kwargs):
            started = runtime.read(self.root / "controller_started.json")
            self.assertEqual(started["deadline"] - started["started"], 5400)
            raise ValueError("intentional stop before native")
        with patch.object(runtime, "verify", side_effect=verify):
            runtime.controller(str(self.root), checksum, allow_gpu=True)

    def test_no_resume(self):
        runtime.write(self.root / "controller_started.json", {})
        with self.assertRaisesRegex(ValueError, "resume"):
            runtime.controller(str(self.root), "a" * 64, allow_gpu=True)

    def test_all_native_entries_require_explicit_flags(self):
        with self.assertRaises(ValueError):
            runtime.controller(str(self.root), "a" * 64)
        with self.assertRaises(ValueError):
            runtime.worker(str(self.root), "a" * 64, "baseline", time.time() + 1)
        with self.assertRaises(ValueError):
            runtime.prepare("/no/spec", "a" * 64, self.root)

    def test_fake_owned_process_timeout_cleans_only_its_group(self):
        process = Mock(pid=23456)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        probe = SimpleNamespace(gpu_state=Mock(return_value=True), cleanup=Mock(return_value=True))
        with patch.object(runtime.subprocess, "Popen", return_value=process) as launch:
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        self.assertTrue(launch.call_args.kwargs["start_new_session"])
        probe.cleanup.assert_called_once_with(process)
        self.assertTrue(runtime.read(self.root / "run/baseline/release.json")["owned_group_released"])

    def fake_successful_process(self, started_pid=23456):
        process = Mock(pid=23456)
        def wait(timeout):
            directory = self.root / "run/baseline"
            runtime.write(directory / "started.json", dict(pid=started_pid, pgid=started_pid, plan_sha256="a" * 64))
            runtime.write(directory / "data/result.json", dict(stage="baseline", calls=16, fits=0, updates=0))
            runtime.write(directory / "CLOSED.json", dict(pid=started_pid, stage="baseline", files=runtime.tree(directory / "data")))
            return 0
        process.wait.side_effect = wait
        return process

    def test_successful_fake_process_checks_worker_identity(self):
        process = self.fake_successful_process()
        probe = SimpleNamespace(gpu_state=Mock(return_value=True), cleanup=Mock(return_value=True))
        with patch.object(runtime.subprocess, "Popen", return_value=process):
            result = runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        self.assertEqual(result["calls"], 16)
        probe.cleanup.assert_called_once_with(process)

    def test_forged_worker_identity_rejected_after_cleanup(self):
        process = self.fake_successful_process(started_pid=98765)
        probe = SimpleNamespace(gpu_state=Mock(return_value=True), cleanup=Mock(return_value=True))
        with patch.object(runtime.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(ValueError, "identity"):
                runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        probe.cleanup.assert_called_once_with(process)

    def test_launch_failure_no_foreign_cleanup(self):
        probe = SimpleNamespace(gpu_state=Mock(return_value=True), cleanup=Mock())
        with patch.object(runtime.subprocess, "Popen", side_effect=OSError("fixture spawn failed")):
            with self.assertRaisesRegex(OSError, "spawn failed"):
                runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        probe.cleanup.assert_not_called()
        self.assertIsNone(runtime.read(self.root / "run/baseline/release.json")["pid"])

    def test_gpu_busy_never_launches_or_kills(self):
        probe = SimpleNamespace(gpu_state=Mock(return_value=False), cleanup=Mock())
        with patch.object(runtime.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "occupied"):
                runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        launch.assert_not_called()
        probe.cleanup.assert_not_called()

    def test_cleanup_failure_retains_release_receipt(self):
        process = Mock(pid=23456)
        process.wait.return_value = 0
        probe = SimpleNamespace(gpu_state=Mock(return_value=True), cleanup=Mock(return_value=False))
        with patch.object(runtime.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(ValueError, "release failed"):
                runtime.run_stage(self.plan, "a" * 64, "baseline", time.monotonic() + 100, probe)
        self.assertFalse(runtime.read(self.root / "run/baseline/release.json")["owned_group_released"])

    def test_release_budget_suspends_compute_timer(self):
        timer_calls = []
        def timer(kind, seconds, *args):
            timer_calls.append(seconds)
            return (1., 0.) if len(timer_calls) == 1 else (0., 0.)
        with patch.object(runtime.signal, "setitimer", side_effect=timer), patch.object(runtime.signal, "getitimer", return_value=(0., 0.)):
            with runtime.release_budget(time.monotonic() + 20):
                pass
        self.assertEqual(timer_calls[0], 0)
        self.assertGreater(timer_calls[1], 19)


class BindingTests(Fixture):
    def spec(self):
        source = Path(self.temporary.name) / "source"
        for name in runtime.SOURCE_NAMES:
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        helpers = {}
        for name in ("reflection", "public"):
            path = Path(self.temporary.name) / (name + ".py")
            path.write_text("raise AssertionError('must not import in spec-only test')\n")
            helpers[name] = dict(path=str(path), sha256=runtime.digest(path))
        receipt = Path(self.temporary.name) / "binding.json"
        runtime.write(receipt, {})
        protocol = Path(self.temporary.name) / "protocol.md"
        protocol.write_text("fixture protocol")
        return dict(schema=runtime.SCHEMA, source=str(source), source_files=runtime.tree(source),
                    core_schema=core.SCHEMA, helpers=helpers, model="/fixture/model",
                    model_binding=dict(path=str(receipt), sha256=runtime.digest(receipt)),
                    protocol=dict(path=str(protocol), sha256=runtime.digest(protocol)),
                    gpu_uuid="GPU-fixture", gpu_index=0, lease_end=time.time() + 100000)

    def test_final_spec_validation_does_not_import_core_or_helpers(self):
        runtime.validate_spec(self.spec())

    def test_source_extra_and_hash_drift_fail_before_import(self):
        spec = self.spec()
        runtime.write(Path(spec["source"]) / "unexpected.json", {})
        with self.assertRaisesRegex(ValueError, "inventory"):
            runtime.load_apis(spec)

    def test_source_content_drift_before_import(self):
        spec = self.spec()
        (Path(spec["source"]) / "organism_v6/l2_public_record_dev.py").write_text("raise Exception('untrusted')")
        with patch.object(runtime.importlib, "import_module") as imported:
            with self.assertRaisesRegex(ValueError, "inventory"):
                runtime.load_apis(spec)
        imported.assert_not_called()

    def test_helper_pin_mismatch_fails_before_import(self):
        spec = self.spec()
        spec["helpers"]["public"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "pin differs"):
            runtime.load_apis(spec)

    def test_explicit_final_pins_required_no_defaults(self):
        spec = self.spec()
        del spec["source_files"]["organism_v6/l2_public_record_dev.py"]
        with self.assertRaisesRegex(ValueError, "four-file"):
            runtime.validate_spec(spec)

    def test_work_counters_do_not_accept_bool_or_extra_fit(self):
        result = dict(stage="fit1", calls=0, fits=True, updates=20, admitted=8)
        with self.assertRaises(ValueError):
            runtime.check_work("fit1", result)
        result = dict(stage="baseline", calls=17, fits=0, updates=0)
        with self.assertRaises(ValueError):
            runtime.check_work("baseline", result)

    def test_fake_prepare_and_verify_pin_roundtrip(self):
        spec = self.spec()
        spec_path = Path(self.temporary.name) / "spec.json"
        runtime.write(spec_path, spec)
        prepared_root = Path(self.temporary.name) / "prepared"
        self.probe.public_model_files = lambda receipt, model: {"fixture-weight": "b" * 64}
        self.probe.model_hashes = lambda model: {"fixture-weight": "b" * 64}
        self.reflection.environment = lambda probe: {"fake_backend_only": True}
        with patch.object(runtime, "load_apis", return_value=(core, trainer, self.probe, self.reflection)):
            receipt = runtime.prepare(spec_path, runtime.digest(spec_path), prepared_root, allow_native=True)
            verified = runtime.verify(prepared_root, receipt["plan_sha256"], native=True)
        self.assertEqual(verified[-1], self.world)
        self.assertEqual(verified[0]["caps"], dict(calls=128, fits=3, updates=100))
        self.assertTrue((prepared_root / "model_binding.json").exists())
        calls = runtime.read(prepared_root / "calls.json")
        self.assertEqual({view: len(rows) for view, rows in calls.items()}, {"wake": 16, "readout": 16, "train": 16})

    def test_prepare_lease_margin_fails_before_import_or_root_creation(self):
        spec = self.spec()
        spec["lease_end"] = time.time() + runtime.OUTER_SECONDS + runtime.LEASE_MARGIN
        spec_path = Path(self.temporary.name) / "spec.json"
        runtime.write(spec_path, spec)
        prepared_root = Path(self.temporary.name) / "prepared"
        with patch.object(runtime, "load_apis") as loaded:
            with self.assertRaisesRegex(ValueError, "lease margin"):
                runtime.prepare(spec_path, runtime.digest(spec_path), prepared_root, allow_native=True)
        loaded.assert_not_called()
        self.assertFalse(prepared_root.exists())


if __name__ == "__main__":
    unittest.main()
