"""CPU-only A2 configuration, public teacher transport and strict selection."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_outcome_collect_v2 as source
from organism_v6 import composition_birth_stage2a_primitives as primitives
from tests import test_astra_stage2a_outcome_collect as fixtures
from tests.test_composition_birth_stage2a_actor import SyntheticModel, SyntheticTokenizer, SyntheticTorch


class ConfigurationTests(unittest.TestCase):
    def test_import_does_not_configure_v1_or_load_native_libraries(self):
        script = """
import sys
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.mkdir', 'os.remove', 'os.system'):
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
sys.addaudithook(audit)
from gpu import astra_stage2a_outcome_collect as original
before=(original.MASTER, original.GUIDANCE)
from gpu import astra_stage2a_outcome_collect_v2 as source
assert (original.MASTER, original.GUIDANCE)==before
assert not {'torch', 'transformers', 'peft'}.intersection(sys.modules)
assert source.MASTER==b'ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A2'
assert source.MASTER!=original.MASTER
"""
        subprocess.run([sys.executable, "-B", "-c", script], check=True, capture_output=True,
                       cwd=Path(__file__).resolve().parents[1])

    def test_run_only_configures_master_guidance_and_forwards_arguments(self):
        original = source.collector
        disk_before = Path(original.__file__).read_bytes()
        retained = (original.collect, original.draft_rows, original.scoring.score_chain, original.MAX_SECONDS)
        options = object()
        with patch.object(original, "MASTER", original.MASTER), patch.object(original, "GUIDANCE", original.GUIDANCE):
            def delegate(passed, **kwargs):
                self.assertIs(passed, options)
                self.assertEqual(kwargs, {"libraries": "synthetic"})
                self.assertEqual(original.MASTER, source.MASTER)
                self.assertEqual(original.GUIDANCE, source.GUIDANCE)
                self.assertEqual(retained, (original.collect, original.draft_rows,
                                          original.scoring.score_chain, original.MAX_SECONDS))
                return "delegated"

            with patch.object(original, "run", side_effect=delegate):
                self.assertEqual(source.run(options, libraries="synthetic"), "delegated")
        self.assertEqual(Path(original.__file__).read_bytes(), disk_before)

    def test_actual_log_records_a2_master_and_full_guidance_and_900s_cap(self):
        original = source.collector
        with tempfile.TemporaryDirectory() as directory, patch.object(original, "MASTER", original.MASTER), patch.object(
                original, "GUIDANCE", original.GUIDANCE):
            options = source.parse_args(["--model-dir", "unused", "--output", str(Path(directory) / "fresh"),
                "--gpu-uuid", "GPU-unused", "--expected-base-sha256", "a" * 64, "--deadline-unix", "1001"])
            with self.assertRaisesRegex(ValueError, "finite_unexpired_max_900s_deadline"):
                source.run(options, libraries=(), clock=lambda: 100.0)
            result = json.loads((Path(options.output) / "FAILED.json").read_bytes())
            self.assertEqual(result["master"], source.MASTER.decode())
            self.assertEqual(result["guidance"], source.GUIDANCE)
            self.assertEqual(result["max_seconds"], 900)
            self.assertEqual(result["planned_episodes"], 32)
            self.assertEqual(result["call_cap_per_episode"], 29)


class PublicPrefixTests(unittest.TestCase):
    def setUp(self):
        self.collector = source.collector
        self.enterContext(patch.object(self.collector, "MASTER", source.MASTER))
        self.enterContext(patch.object(self.collector, "GUIDANCE", source.GUIDANCE))

    def test_teacher_is_public_only_and_native_prompt_contains_actual_v2_guidance(self):
        tokenizer, torch = SyntheticTokenizer(), SyntheticTorch()
        model = SyntheticModel(torch, tuple(ord(character) + 10 for character in "STOP") + (1,))
        native = self.collector.native_actor.ReadoutActor(model=model, tokenizer=tokenizer, torch=torch,
            device="synthetic-device", count_basis="SYNTHETIC_FIXTURE", generation_config_factory=SimpleNamespace)
        calls = []
        teacher = self.collector.PublicTeacher(native, check=lambda stage: None, emit=calls.append)
        prefix = (self.collector.held.Message("system", self.collector.wire.SYSTEM_MESSAGE),
                  self.collector.held.Message("user", "Only public task text"))
        with patch.object(self.collector.native_prepare, "allocate_source", side_effect=AssertionError("private source")), patch.object(
                self.collector.scoring, "score_chain", side_effect=AssertionError("private scorer")), patch.object(
                self.collector.held.ChainWorld, "transition", side_effect=AssertionError("private graph")):
            request = self.collector.rollout.DecodeRequest(prefix, 256, 19, teacher.count_context(prefix))
            result = teacher(request)
        self.assertEqual(result.raw, "STOP")
        self.assertEqual(calls[0]["public_request"].prefix, prefix)
        self.assertEqual(calls[0]["guided_request"].prefix[1:], prefix[1:])
        self.assertIn(source.GUIDANCE, calls[0]["native"]["prompt"])
        self.assertEqual(request.context_tokens, len(calls[0]["native"]["prompt_ids"]))
        self.assertEqual(calls[0]["generation"], calls[0]["native"]["generation"])
        for pattern in self.collector.wire.IDENTIFIERS.values():
            self.assertNotRegex(source.GUIDANCE, pattern)

    def test_a2_master_is_forwarded_to_existing_allocator(self):
        worlds = tuple(SimpleNamespace(world=f"h{index:02d}",
                       members=(SimpleNamespace(member="m0"), SimpleNamespace(member="m1"))) for index in range(16))
        with patch.object(self.collector.native_prepare, "allocate_source") as allocate, patch.object(
                self.collector.held, "build_chain_panel", return_value=worlds):
            self.collector.training_worlds()
        allocate.assert_called_once_with(master=b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A2")
        allocate.return_value.role_tokens_by_world.assert_called_once_with("dose_chain")


class StrictSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(source.collector, "MASTER", source.MASTER):
            cls.allocation_sha256, cls.worlds = source.collector.training_worlds()

    def setUp(self):
        self.collector = source.collector
        self.enterContext(patch.object(self.collector, "MASTER", source.MASTER))
        self.enterContext(patch.object(self.collector, "GUIDANCE", source.GUIDANCE))

    def trajectory(self, *, extra_check_at_goal=False):
        world = self.worlds[0]
        member = world.members[0]
        actions = [turn.action for turn in member.expected_trace]
        if extra_check_at_goal:
            actions.insert(-1, next(action for action in actions if action.startswith("THINK ")))
        outputs = {}
        for index, action in enumerate(actions):
            slot = primitives.chain_slot("D1", 0, 0, index)
            outputs[primitives.decode_seed(source.MASTER, slot.panel_label, slot.global_ordinal)] = action
        native = fixtures.SyntheticPolicyActor(outputs)
        calls = []
        teacher = self.collector.PublicTeacher(native, check=lambda stage: None, emit=calls.append)
        run = self.collector.rollout.run_chain(world, "m0", actor=teacher, count_context=teacher.count_context,
            counter_provenance="SYNTHETIC_V2_CPU_FIXTURE", master=source.MASTER, stage="D1")
        score = self.collector.scoring.score_chain(run.attempts, member)
        return run, score, calls

    def test_all_32_fresh_cases_and_teacher_free_actual_draft_prefixes(self):
        self.assertEqual(len(self.worlds), 16)
        self.assertTrue(all(tuple(member.member for member in world.members) == ("m0", "m1") for world in self.worlds))
        run, score, calls = self.trajectory()
        self.assertTrue(score.whole_chain_success)
        rows = self.collector.draft_rows(run, calls, score, episode_id="synthetic-v2")
        self.assertEqual(len(rows), len(run.attempts))
        self.assertEqual(len(run.calls), 29)
        for row, call in zip(rows, calls):
            self.assertEqual(row["prefix"], self.collector.plain(call["public_request"].prefix))
            self.assertEqual(row["prefix"][0]["content"], self.collector.wire.SYSTEM_MESSAGE)
            self.assertNotIn(source.GUIDANCE, json.dumps(row))
            self.assertNotIn("Teacher-only exogenous strategy", json.dumps(row))
            self.assertEqual(row["assistant"], call["native"]["raw"])
            self.assertEqual(row["loss_policy"], dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN"))

    def test_mechanical_goal_stop_does_not_relax_frozen_selector(self):
        run, score, calls = self.trajectory(extra_check_at_goal=True)
        self.assertTrue(score.goal_arrival)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertFalse(score.stop_immediately_after_second_step)
        self.assertFalse(score.whole_chain_success)
        self.assertEqual(self.collector.draft_rows(run, calls, score, episode_id="synthetic-v2"), [])


if __name__ == "__main__":
    unittest.main()
