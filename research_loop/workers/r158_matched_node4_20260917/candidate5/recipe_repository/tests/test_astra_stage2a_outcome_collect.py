"""CPU-only synthetic native transport plus real source worlds and scorer."""

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_stage2a_outcome_collect as source
from organism_v6 import composition_birth_stage2a_primitives as primitives
from tests.test_composition_birth_stage2a_actor import SyntheticModel, SyntheticTokenizer, SyntheticTorch


class PublicTeacherTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer, self.torch = SyntheticTokenizer(), SyntheticTorch()
        self.model = SyntheticModel(self.torch, tuple(ord(character) + 10 for character in "STOP") + (1,))
        self.native = source.native_actor.ReadoutActor(tokenizer=self.tokenizer, model=self.model,
            torch=self.torch, device="synthetic-device", count_basis="SYNTHETIC_FIXTURE",
            generation_config_factory=SimpleNamespace)
        self.logs = []
        self.teacher = source.PublicTeacher(self.native, check=lambda stage: None, emit=self.logs.append)
        self.prefix = (source.held.Message("system", source.wire.SYSTEM_MESSAGE),
                       source.held.Message("user", "Only public task text"))

    def request(self):
        return source.rollout.DecodeRequest(self.prefix, 256, 17, self.teacher.count_context(self.prefix))

    def test_fixed_transform_changes_only_system_and_has_no_concrete_ids(self):
        guided = source.public_teacher_prefix(self.prefix)
        self.assertEqual(guided[0].content, source.wire.SYSTEM_MESSAGE + source.GUIDANCE)
        self.assertEqual(guided[1:], self.prefix[1:])
        self.assertEqual(self.prefix[0].content, source.wire.SYSTEM_MESSAGE)
        for pattern in source.wire.IDENTIFIERS.values():
            self.assertNotRegex(source.GUIDANCE, pattern)
        self.assertEqual(source.public_teacher_prefix(self.prefix), guided)
        with self.assertRaisesRegex(ValueError, "original_unassisted_public_prefix_required"):
            source.public_teacher_prefix(guided)

    def test_context_counts_actual_guided_prompt_not_original(self):
        request = self.request()
        self.assertEqual(request.context_tokens, self.native.count_context(source.public_teacher_prefix(self.prefix)))
        self.assertGreater(request.context_tokens, self.native.count_context(self.prefix))
        generation = self.teacher(request)
        self.assertEqual(generation.raw, "STOP")
        record = self.logs[0]
        self.assertEqual(record["public_request"], request)
        self.assertNotEqual(record["public_request"].prefix, record["guided_request"].prefix)
        self.assertEqual(record["native"]["request"], record["guided_request"])
        self.assertIn(source.GUIDANCE, record["native"]["prompt"])
        self.assertEqual(tuple(self.model.received[0]["input_ids"].rows[0]), record["native"]["prompt_ids"])
        self.assertEqual(len(record["native"]["prompt_ids"]), request.context_tokens)
        self.assertEqual(record["native"]["raw_bytes"], b"STOP")
        self.assertEqual(record["native"]["native_sequences"], self.model.output.tolist())
        self.assertEqual(record["native"]["generated_ids"], tuple(ord(character) + 10 for character in "STOP") + (1,))
        self.assertEqual(source.plain(record)["native"]["raw_bytes"], {"bytes_hex": b"STOP".hex()})

    def test_native_failure_records_both_requests_and_prompt_without_fake_output(self):
        self.model.generate_error = RuntimeError("synthetic CUDA failure")
        with self.assertRaisesRegex(RuntimeError, "synthetic CUDA failure"):
            self.teacher(self.request())
        record = self.logs[0]
        self.assertIsNone(record["generation"])
        self.assertIsNone(record["native"]["raw"])
        self.assertIn(source.GUIDANCE, record["native"]["prompt"])
        self.assertIs(record["error"], self.model.generate_error)
        with self.assertRaisesRegex(ValueError, "teacher_failed_no_retry"):
            self.teacher.count_context(self.prefix)
        self.assertEqual(len(self.model.received), 1)

    def test_guided_count_mismatch_is_not_silently_repaired(self):
        request = replace(self.request(), context_tokens=self.native.count_context(self.prefix))
        with self.assertRaisesRegex(ValueError, "guided_context_count_disagreement"):
            self.teacher(request)
        self.assertEqual(self.native.calls, [])
        self.assertIsNone(self.logs[0]["native"])

    def test_deadline_call_is_logged_without_generating(self):
        request = self.request()
        self.teacher.check = Mock(side_effect=ValueError("deadline"))
        with self.assertRaisesRegex(ValueError, "deadline"):
            self.teacher(request)
        self.assertEqual(len(self.logs), 1)
        self.assertIsNone(self.logs[0]["generation"])
        self.assertEqual(self.native.calls, [])


class SyntheticPolicyActor:
    """Test-only scripted decoder; production never supplies witness actions."""

    def __init__(self, outputs):
        self.outputs, self.calls = outputs, []

    def count_context(self, prefix):
        if source.GUIDANCE not in prefix[0].content:
            raise AssertionError("counter did not receive guided prefix")
        return 1

    def __call__(self, request):
        raw = self.outputs[request.seed]
        if isinstance(raw, BaseException):
            self.calls.append(dict(request=request, raw=None, error=raw, native_output=None))
            raise raw
        generation = source.rollout.Generation(raw, 1, 1, False, "stop")
        self.calls.append(dict(request=request, raw=raw, raw_bytes=raw.encode(), generation=generation,
                               native_sequences=[[1]], generated_ids=(1,), native_output=None))
        return generation


class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.allocation_sha256, cls.worlds = source.training_worlds()

    def setUp(self):
        self.calls, self.episodes, self.rows = [], [], []
        self.summary = dict(completed_episodes=0, whole_chain_successes=0, draft_rows=0)

    def outputs(self, worlds, *, success=True):
        outputs = {}
        for world in worlds:
            for member in world.members:
                script = [turn.action for turn in member.expected_trace] if success else ["STOP"]
                for index, raw in enumerate(script):
                    slot = primitives.chain_slot("D1", int(world.world[1:]), int(member.member[1:]), index)
                    outputs[primitives.decode_seed(source.MASTER, slot.panel_label, slot.global_ordinal)] = raw
        return outputs

    def collect(self, worlds, outputs, *, check=lambda stage: None):
        self.native = SyntheticPolicyActor(outputs)
        self.teacher = source.PublicTeacher(self.native, check=check, emit=self.calls.append)
        source.collect(worlds, self.teacher, emit_episode=self.episodes.append, emit_row=self.rows.append,
                       check=check, summary=self.summary)

    def test_fresh_fixed_master_all_16_worlds_both_members(self):
        self.assertEqual(source.MASTER, b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A1")
        self.assertEqual(tuple(world.world for world in self.worlds), tuple(f"h{index:02d}" for index in range(16)))
        self.assertTrue(all(tuple(member.member for member in world.members) == ("m0", "m1") for world in self.worlds))
        with patch.object(source.native_prepare, "allocate_source") as allocate, patch.object(
                source.held, "build_chain_panel", return_value=self.worlds):
            source.training_worlds()
        allocate.assert_called_once_with(master=source.MASTER)
        allocate.return_value.role_tokens_by_world.assert_called_once_with("dose_chain")

    def test_all_32_successes_use_actual_actions_and_no_guidance_in_draft_rows(self):
        self.collect(self.worlds, self.outputs(self.worlds))
        self.assertEqual(self.summary["completed_episodes"], 32)
        self.assertEqual(self.summary["whole_chain_successes"], 32)
        self.assertEqual(len(self.episodes), 32)
        self.assertEqual(self.summary["draft_rows"], len(self.calls))
        for episode in self.episodes:
            self.assertEqual(episode["split"], "TRAIN_ONLY")
            self.assertEqual(len(episode["run"].calls), 29)
        for row in self.rows:
            original = self.calls[row["source_call_index"]]
            self.assertEqual(row["prefix"], source.plain(original["public_request"].prefix))
            self.assertEqual(row["prefix"][0]["content"], source.wire.SYSTEM_MESSAGE)
            self.assertNotIn(source.GUIDANCE, json.dumps(row))
            self.assertEqual(row["assistant"], original["native"]["raw"])
            self.assertEqual(row["loss_policy"], dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN"))
            self.assertEqual(row["target_eot"], "<|im_end|>")
            self.assertEqual(row["status"], "DRAFT_NOT_RELEASED")

    def test_unsuccessful_episodes_are_exported_but_never_selected(self):
        self.collect(self.worlds, self.outputs(self.worlds, success=False))
        self.assertEqual(len(self.episodes), 32)
        self.assertEqual(len(self.calls), 32)
        self.assertEqual(self.rows, [])
        self.assertFalse(any(episode["selected"] for episode in self.episodes))
        self.assertEqual(self.summary["completed_episodes"], 32)

    def test_failure_after_success_retains_every_raw_call_and_stops_next_episode(self):
        outputs = self.outputs(self.worlds)
        slot = primitives.chain_slot("D1", 0, 1, 0)
        outputs[primitives.decode_seed(source.MASTER, slot.panel_label, slot.global_ordinal)] = RuntimeError("decode failed")
        with self.assertRaisesRegex(ValueError, "collection_halted:actor_callback_error"):
            self.collect(self.worlds, outputs)
        self.assertEqual(len(self.episodes), 2)
        self.assertTrue(self.episodes[0]["selected"])
        self.assertEqual(self.episodes[1]["status"], "ABORTED")
        self.assertFalse(self.episodes[1]["selected"])
        self.assertIsInstance(self.calls[-1]["error"], RuntimeError)
        self.assertEqual(self.summary["completed_episodes"], 1)
        self.assertEqual(len(self.rows), len(self.worlds[0].members[0].expected_trace))

    def test_interrupted_episode_retains_partial_calls_without_invented_run(self):
        outputs = self.outputs(self.worlds)
        slot = primitives.chain_slot("D1", 0, 0, 1)
        outputs[primitives.decode_seed(source.MASTER, slot.panel_label, slot.global_ordinal)] = KeyboardInterrupt("stop")
        with self.assertRaises(KeyboardInterrupt):
            self.collect(self.worlds, outputs)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(self.episodes), 1)
        self.assertIsNone(self.episodes[0]["run"])
        self.assertEqual(self.episodes[0]["call_end"], 2)
        self.assertEqual(self.rows, [])

    def test_scorer_cannot_select_a_repaired_or_fabricated_output(self):
        self.collect(self.worlds[:1], self.outputs(self.worlds[:1]))
        episode = self.episodes[0]
        calls = self.calls[episode["call_start"]:episode["call_end"]]
        changed = {**calls[0], "generation": source.rollout.Generation("STOP", 1, 1, False, "stop")}
        with self.assertRaisesRegex(ValueError, "actual_model_action_required"):
            source.draft_rows(episode["run"], [changed] + calls[1:], episode["score"], episode_id="synthetic")

    def test_true_scorer_cannot_override_actual_rejected_calls(self):
        outputs = {seed: "invalid model output" for seed in self.outputs(self.worlds[:1], success=False)}
        self.collect(self.worlds[:1], outputs)
        episode = self.episodes[0]
        self.assertFalse(episode["run"].attempts[0].accepted)
        self.assertEqual(episode["run"].attempts[0].capture.raw_bytes, b"invalid model output")
        calls = self.calls[episode["call_start"]:episode["call_end"]]
        forced_success = replace(episode["score"], whole_chain_success=True)
        with self.assertRaisesRegex(ValueError, "rejected_or_invalid_call_cannot_be_selected"):
            source.draft_rows(episode["run"], calls, forced_success, episode_id="synthetic")
        self.assertEqual(self.rows, [])
        self.assertEqual(calls[0]["generation"], calls[0]["native"]["generation"])
        self.assertEqual(calls[0]["native"]["raw"], "invalid model output")

    def test_true_scorer_cannot_skip_a_call_without_request(self):
        self.collect(self.worlds[:1], self.outputs(self.worlds[:1]))
        episode = self.episodes[0]
        run = episode["run"]
        changed = replace(run, calls=run.calls[:-1] + (replace(run.calls[-1], disposition="ERROR"),))
        with self.assertRaisesRegex(ValueError, "rejected_or_invalid_call_cannot_be_selected"):
            source.draft_rows(changed, self.calls[:episode["call_end"]], episode["score"], episode_id="synthetic")

    def test_native_raw_and_generation_must_both_match_actual_action(self):
        self.collect(self.worlds[:1], self.outputs(self.worlds[:1]))
        episode = self.episodes[0]
        calls = self.calls[episode["call_start"]:episode["call_end"]]
        native = calls[0]["native"]
        for field, bad in (("generation", replace(native["generation"], actual_tokens=2)),
                           ("raw_bytes", b"invented"), ("request", calls[0]["public_request"])):
            with self.subTest(field=field):
                changed = {**calls[0], "native": {**native, field: bad}}
                with self.assertRaisesRegex(ValueError, "native_raw_generation_required"):
                    source.draft_rows(episode["run"], [changed] + calls[1:], episode["score"], episode_id="synthetic")

    def test_seed_schedule_fixed_by_new_master_not_guidance(self):
        self.collect(self.worlds[:1], self.outputs(self.worlds[:1], success=False))
        for member_index, call in enumerate(self.calls):
            slot = primitives.chain_slot("D1", 0, member_index, 0)
            expected = primitives.decode_seed(source.MASTER, slot.panel_label, slot.global_ordinal)
            self.assertEqual(call["public_request"].seed, expected)
            self.assertEqual(call["guided_request"].seed, expected)
            self.assertEqual(call["public_request"].max_new_tokens, call["guided_request"].max_new_tokens)

    def test_public_transform_cannot_consult_evaluator_or_private_world(self):
        prefix = self.worlds[0].public_view("m0").prefix
        with patch.object(source.scoring, "score_chain", side_effect=AssertionError("private scorer")), patch.object(
                source.held.ChainWorld, "transition", side_effect=AssertionError("private graph")), patch.object(
                source.native_prepare, "allocate_source", side_effect=AssertionError("private allocation")):
            transformed = source.public_teacher_prefix(prefix)
        self.assertEqual(transformed[1:], prefix[1:])


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.options = SimpleNamespace(model_dir="not-a-model", output=str(self.root / "fresh"),
            gpu_uuid="GPU-test", deadline_unix=500.0, expected_base_sha256="a" * 64)

    def test_deadline_maximum_and_nonfinite_values_fail_before_native_import(self):
        for index, deadline in enumerate((100.0, 1001.0, float("nan"), float("inf"), True)):
            self.options.output = str(self.root / str(index))
            self.options.deadline_unix = deadline
            with self.assertRaisesRegex(ValueError, "finite_unexpired_max_900s_deadline"):
                source.run(self.options, libraries=(), clock=lambda: 100.0)
            self.assertTrue((Path(self.options.output) / "FAILED.json").exists())

    def test_wrong_visible_gpu_fails_without_loading(self):
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-other"), self.assertRaisesRegex(
                ValueError, "single_gpu_binding_required"):
            source.run(self.options, libraries=(), clock=lambda: 100.0)

    def test_output_root_is_never_reused(self):
        Path(self.options.output).mkdir()
        with self.assertRaises(FileExistsError):
            source.run(self.options, libraries=(), clock=lambda: 100.0)
        self.assertEqual(list(Path(self.options.output).iterdir()), [])

    def test_cli_and_import_have_no_native_or_io_side_effects(self):
        script = """
import sys
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.mkdir', 'os.remove', 'os.system'):
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
sys.addaudithook(audit)
from gpu import astra_stage2a_outcome_collect as source
assert not {'torch', 'transformers', 'peft'}.intersection(sys.modules)
options=source.parse_args(['--model-dir', '/model', '--output', '/fresh', '--gpu-uuid', 'GPU-test',
                          '--deadline-unix', '900', '--expected-base-sha256', 'a'*64])
assert options.deadline_unix==900 and source.MAX_SECONDS==900
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True, capture_output=True,
                       cwd=Path(__file__).resolve().parents[1])

    def test_json_logs_preserve_binary_raw_and_errors(self):
        path = self.root / "call.jsonl"
        with path.open("x") as stream:
            source.append_json(stream, dict(raw=b"\xff\x00\r\n", error=RuntimeError("synthetic")))
        loaded = json.loads(path.read_bytes())
        self.assertEqual(bytes.fromhex(loaded["raw"]["bytes_hex"]), b"\xff\x00\r\n")
        self.assertEqual(loaded["error"]["error_type"], "RuntimeError")

    def native_fixture(self, collector):
        self.enterContext(patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-test"))
        self.parameter = SimpleNamespace(requires_grad=True)
        self.hook = Mock()
        self.model = SimpleNamespace(
            requires_grad_=Mock(side_effect=lambda enabled: setattr(self.parameter, "requires_grad", enabled)),
            parameters=lambda: (self.parameter,), eval=Mock(), state_dict=lambda: {}, to=Mock(),
            register_forward_pre_hook=Mock(return_value=self.hook))
        self.torch = SimpleNamespace(__version__=source.tokens.RUNTIME_VERSIONS["torch"], bfloat16="bf16",
            set_num_threads=Mock(), set_num_interop_threads=Mock(),
            cuda=SimpleNamespace(is_initialized=lambda: False, init=Mock(), device_count=lambda: 1))
        self.loader = Mock(return_value=self.model)
        transformers = SimpleNamespace(__version__=source.tokens.RUNTIME_VERSIONS["transformers"],
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=self.loader),
            AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=object())))
        self.enterContext(patch.object(source, "training_worlds", return_value=("synthetic-allocation", ())))
        self.enterContext(patch.object(source.tokens, "restore_official_backend", return_value={"synthetic": True}))
        self.hash_base = self.enterContext(patch.object(source, "_state_hash", return_value="a" * 64))
        self.enterContext(patch.object(source.native_actor, "ReadoutActor", return_value=SimpleNamespace(calls=[])))
        self.enterContext(patch.object(source, "collect", side_effect=collector))
        return self.torch, transformers

    def test_entry_freezes_one_model_exports_draft_only_and_removes_hook(self):
        def collected(worlds, teacher, *, emit_episode, emit_row, check, summary):
            check("synthetic_collection")
            summary["completed_episodes"] = 32

        result = source.run(self.options, libraries=self.native_fixture(collected), clock=lambda: 100.0)
        self.assertEqual(result["status"], "COLLECTION_COMPLETE_DRAFT_ONLY")
        self.assertEqual(result["claim"], source.CLAIM)
        self.loader.assert_called_once()
        self.assertTrue(self.loader.call_args.kwargs["local_files_only"])
        self.assertFalse(self.parameter.requires_grad)
        self.model.to.assert_called_once_with("cuda:0")
        self.hook.remove.assert_called_once()
        self.assertEqual(self.hash_base.call_count, 2)
        root = Path(self.options.output)
        self.assertEqual({path.name for path in root.iterdir()},
                         {"REQUEST.json", "RESULT.json", "CALLS.jsonl", "EPISODES.jsonl", "DRAFT_TRAINING_ROWS.jsonl"})

    def test_entry_failure_preserves_flushed_calls_episodes_and_no_result(self):
        def failed(worlds, teacher, *, emit_episode, emit_row, check, summary):
            teacher.emit(dict(raw=b"synthetic failed native bytes", error=RuntimeError("synthetic OOM")))
            emit_episode(dict(status="ABORTED", selected=False))
            raise RuntimeError("synthetic OOM")

        libraries = self.native_fixture(failed)
        with self.assertRaisesRegex(RuntimeError, "synthetic OOM"):
            source.run(self.options, libraries=libraries, clock=lambda: 100.0)
        root = Path(self.options.output)
        self.assertIn("bytes_hex", (root / "CALLS.jsonl").read_text())
        self.assertEqual(json.loads((root / "EPISODES.jsonl").read_text())["status"], "ABORTED")
        self.assertTrue((root / "FAILED.json").exists())
        self.assertFalse((root / "RESULT.json").exists())
        self.assertEqual((root / "DRAFT_TRAINING_ROWS.jsonl").read_bytes(), b"")
        self.hook.remove.assert_called_once()

    def test_forward_hook_has_finite_deadline_and_base_pin_precedes_cuda(self):
        libraries = self.native_fixture(lambda *args, **kwargs: None)
        self.hash_base.return_value = "wrong-base"
        with self.assertRaisesRegex(ValueError, "base_state_mismatch"):
            source.run(self.options, libraries=libraries, clock=lambda: 100.0)
        self.torch.cuda.init.assert_not_called()
        self.model.register_forward_pre_hook.assert_not_called()


if __name__ == "__main__":
    unittest.main()
