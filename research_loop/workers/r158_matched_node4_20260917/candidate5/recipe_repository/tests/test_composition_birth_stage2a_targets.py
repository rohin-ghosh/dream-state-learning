from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import unittest

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_targets as source
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


class PairedTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = {f"p{pair:02d}": synthetic_bindings(pair) for pair in range(32)}
        cls.cases = []
        cls.pairs = []
        for world, bindings in cls.bindings.items():
            pair = birth.build_birth_pair(world=world, role_tokens=bindings,
                                          display_master=b"SYNTHETIC-PAIRED-PREFIX")
            for case in pair.cases:
                cls.cases.append(case)
                cls.pairs.append(source.serialize_birth_case(case, role_tokens=bindings))

    def test_shared_unit_exact_target_and_mask_specification_only(self):
        units = set()
        for case, pairs in zip(self.cases, self.pairs):
            self.assertEqual(len(pairs), 4)
            for target, pair in zip(case.targets, pairs):
                self.assertIs(pair.closed.unit, pair.atom_local.unit)
                unit = pair.closed.unit
                self.assertEqual(unit.unit_id, f"{case.descriptor.world}/{case.descriptor.member}/u{target.ordinal}")
                self.assertNotIn(unit.unit_id, units)
                units.add(unit.unit_id)
                self.assertEqual(unit.target_bytes, target.target_bytes)
                self.assertEqual(unit.target_sha256, sha256(unit.target_bytes).hexdigest())
                for arm in (pair.closed, pair.atom_local):
                    self.assertEqual(arm.training_messages[-1], source.Message("assistant", unit.target_bytes.decode()))
                    self.assertEqual(arm.supervised_message_index, len(arm.prefix))
                    self.assertEqual(arm.prefix_sha256, sha256(source.messages_bytes(arm.prefix)).hexdigest())
        self.assertEqual(len(units), 256)

    def test_closed_is_exact_complete_prior_trace(self):
        for case, pairs in zip(self.cases, self.pairs):
            for target, pair in zip(case.targets, pairs):
                expected = [source.Message("system", wire.SYSTEM_MESSAGE), source.Message("user", case.task_text)]
                for turn in case.trace[:target.trace_index]:
                    expected.append(source.Message("assistant", turn.action))
                    if turn.response:
                        expected.append(source.Message("user", turn.response))
                self.assertEqual(pair.closed.prefix, tuple(expected))

    def test_atom_exact_role_counts_and_action_slices(self):
        for case, pairs in zip(self.cases, self.pairs):
            for target, pair in zip(case.targets, pairs):
                actions = tuple(message.content for message in pair.atom_local.prefix if message.role == "assistant")
                index = target.trace_index
                if target.phase == "CONTINUE":
                    expected = ()
                elif target.phase == "SEEK":
                    expected = tuple(turn.action for turn in case.trace[index - 3:index]) if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (case.trace[0].action,)
                elif target.phase == "STEP_CHECK":
                    expected = tuple(turn.action for turn in case.trace[index - 2:index])
                else:
                    expected = (case.trace[index - 1].action,)
                self.assertEqual(actions, expected)
                self.assertEqual(tuple(message.role for message in pair.atom_local.prefix),
                                 ("system", "user") + ("assistant", "user") * len(expected))

    def test_both_arms_latest_public_state_agrees_at_every_boundary(self):
        for case, pairs in zip(self.cases, self.pairs):
            for target, pair in zip(case.targets, pairs):
                expected = wire.TaskState(case.task.start, case.task.goal, target.current_before)
                self.assertEqual(source.latest_public_task(pair.closed.prefix), expected)
                self.assertEqual(source.latest_public_task(pair.atom_local.prefix), expected)

    def test_mismatch_prospect_uses_surprise_not_initial_or_predicted_state(self):
        checked = 0
        for case, pairs in zip(self.cases, self.pairs):
            if case.descriptor.recovery_subtype != "STEP_OUTCOME_MISMATCH":
                continue
            for target, pair in zip(case.targets, pairs):
                if target.phase == "PROSPECT":
                    task = wire.parse_task(pair.atom_local.prefix[1].content)
                    self.assertEqual(task.current, case.facts.failed_outcome)
                    self.assertNotEqual(task.current, case.task.current)
                    self.assertNotEqual(task.current, case.facts.failed_prediction)
                    self.assertEqual(task.start, case.task.start)
                    checked += 1
        self.assertEqual(checked, 16)

    def test_read_check_does_not_include_corrective_directory_or_query(self):
        checked = 0
        for case, pairs in zip(self.cases, self.pairs):
            for target, pair in zip(case.targets, pairs):
                if target.phase != "READ_CHECK":
                    continue
                content = "\n".join(message.content for message in pair.atom_local.prefix[1:])
                self.assertNotIn("ROUTES\n", content)
                self.assertNotIn(case.facts.corrective_query, content)
                checked += 1
        self.assertEqual(checked, 16)

    def test_exact_render_rejects_target_state_future_and_mask_metadata_mutations(self):
        case, pairs = self.cases[0], self.pairs[0]
        bindings = self.bindings[case.descriptor.world]
        self.assertTrue(source.validate_paired_targets(pairs, case, role_tokens=bindings))
        first = pairs[0]
        mutated = (
            replace(first, atom_local=replace(first.atom_local, prefix=first.atom_local.prefix + (source.Message("user", "ACK"),))),
            replace(first, atom_local=replace(first.atom_local, prefix=first.atom_local.prefix[:1] + (source.Message("user", f"TASK\nSTART {case.task.start}\nGOAL {case.task.goal}\nCURRENT {case.task.goal}"),) + first.atom_local.prefix[2:])),
            replace(first, closed=replace(first.closed, prefix_sha256="0" * 64)),
            replace(first, atom_local=replace(first.atom_local, unit=replace(first.atom_local.unit, target_bytes=b"STOP"))),
            replace(first, atom_local=replace(first.atom_local, unit=replace(first.atom_local.unit))),
        )
        for replacement in mutated:
            with self.assertRaises(ValueError):
                source.validate_paired_targets((replacement,) + pairs[1:], case, role_tokens=bindings)

    def test_clarification_pin_and_partial_science_status(self):
        path = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_stage2a_builder_source_clarifications_v1.md"
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), source.CLARIFICATION_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))


if __name__ == "__main__":
    unittest.main()
