"""Synthetic driver fixtures, never native tokenizer or model receipts."""

from dataclasses import FrozenInstanceError, replace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_nulls as nulls
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as source
from tests.test_composition_birth_stage2a_held import fixtures


class RolloutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tokens = fixtures("dose_chain")
        cls.worlds = tuple(held.build_chain_world(world=name, role_tokens=tokens[name])
                           for name in ("h00", "h04", "h08", "h12"))

    def run_fixture(self, world=None, member="m0", actor=None, **overrides):
        world = world or self.worlds[0]
        if actor is None:
            actions = iter(world.members[int(member[1:])].expected_trace)
            actor = lambda request: source.Generation(next(actions).action, 1, 1, False, "stop")
        options = dict(actor=actor, count_context=lambda prefix: 1,
                       counter_provenance="synthetic-one-per-call-not-tokenizer",
                       master=b"synthetic-rollout-master", stage="D1")
        options.update(overrides)
        return source.run_chain(world, member, **options)

    def test_fixture_replay_all_strata_and_members(self):
        for world in self.worlds:
            for member in world.members:
                with self.subTest(world=world.world, member=member.member):
                    result = self.run_fixture(world, member.member)
                    self.assertEqual(result.terminal_reason, "goal_arrival_stop")
                    self.assertEqual(len(result.attempts), len(member.expected_trace))
                    self.assertEqual(len(result.calls), 29)
                    self.assertTrue(all(call.disposition == "UNUSED"
                                        for call in result.calls[len(result.attempts):]))
                    for attempt, expected in zip(result.attempts, member.expected_trace):
                        self.assertEqual(attempt.capture.raw_bytes, expected.action.encode("ascii"))
                        self.assertEqual(attempt.response_bytes, (expected.response or "").encode("ascii"))

    def test_callback_only_receives_public_messages_and_decode_settings(self):
        seen = []
        actions = iter(self.worlds[0].members[0].expected_trace)

        def actor(request):
            seen.append(request)
            self.assertEqual(set(vars(request)), {"prefix", "max_new_tokens", "seed", "context_tokens"})
            self.assertEqual(request.prefix[0], held.Message("system", wire.SYSTEM_MESSAGE))
            self.assertEqual(request.max_new_tokens, 256)
            with self.assertRaises(FrozenInstanceError):
                request.seed = 0
            return source.Generation(next(actions).action, 1, 1, False, "stop")

        result = self.run_fixture(actor=actor)
        self.assertEqual(len(seen[0].prefix), 2)
        self.assertEqual(len(seen[1].prefix), 4)
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")

    def test_reserved_ordinals_and_paired_seeds(self):
        first = self.run_fixture(self.worlds[2], "m1")
        repeated = self.run_fixture(self.worlds[2], "m1")
        second = self.run_fixture(self.worlds[2], "m1", stage="D2")
        for index, call in enumerate(first.calls):
            self.assertEqual(call.slot, primitives.chain_slot("D1", 8, 1, index))
            self.assertEqual(call.seed, repeated.calls[index].seed)
            self.assertEqual(second.calls[index].slot.global_ordinal, 1008 + call.slot.global_ordinal)

    def test_malformed_action_recorded_before_parse_and_not_retried(self):
        result = self.run_fixture(actor=lambda request: source.Generation("STOP\n", 1, 1, False, "stop"))
        self.assertEqual(result.terminal_reason, "malformed_action")
        self.assertEqual(result.attempts[0].capture.raw_bytes, b"STOP\n")
        self.assertEqual(result.attempts[0].parser_disposition, "invalid")
        self.assertEqual(len(result.prefix), 2)
        self.assertEqual(len(result.attempts), 1)

    def test_generation_metadata_failures_retain_raw(self):
        valid = source.Generation("STOP", 1, 1, False, "stop")
        for changes, reason in ((dict(truncated=True), "length_limited"),
                                (dict(finish_reason="length"), "length_limited"),
                                (dict(finish_reason="abort"), "unbound_finish_reason"),
                                (dict(declared_tokens=2), "invalid_token_accounting"),
                                (dict(actual_tokens=True), "invalid_token_accounting"),
                                (dict(actual_tokens=0), "invalid_token_accounting")):
            with self.subTest(changes=changes):
                result = self.run_fixture(actor=lambda request: replace(valid, **changes))
                self.assertEqual(result.terminal_reason, reason)
                self.assertEqual(result.attempts[0].capture.raw_bytes, b"STOP")

    def test_zero_or_invalid_context_never_calls_actor(self):
        def forbidden(request):
            self.fail("actor should not run")

        for count in (wire.CONTEXT_CAP, wire.CONTEXT_CAP + 1, -1, True):
            result = self.run_fixture(actor=forbidden, count_context=lambda prefix: count)
            self.assertEqual(result.attempts, ())
            self.assertEqual(result.calls[0].disposition, "NOT_CALLED")
            self.assertTrue(all(call.disposition == "UNUSED" for call in result.calls[1:]))

    def test_context_headroom_bounds_request(self):
        def actor(request):
            self.assertEqual(request.max_new_tokens, 7)
            return source.Generation("STOP", 1, 1, False, "stop")

        result = self.run_fixture(actor=actor, count_context=lambda prefix: wire.CONTEXT_CAP - 7)
        self.assertEqual(result.terminal_reason, "premature_stop")

    def test_actor_exception_has_no_fabricated_action(self):
        def broken(request):
            raise RuntimeError("not recorded as actor output")

        result = self.run_fixture(actor=broken)
        self.assertEqual(result.attempts, ())
        self.assertEqual(result.calls[0].error_type, "RuntimeError")
        self.assertEqual(result.calls[0].disposition, "ERROR")

    def test_invalid_generation_transport_fails_closed(self):
        result = self.run_fixture(actor=lambda request: {"raw": "STOP"})
        self.assertEqual(result.terminal_reason, "invalid_generation_transport")
        self.assertEqual(result.attempts, ())

    def test_all_schedules_bounded_over_fixture_strata(self):
        for world in self.worlds:
            for member in world.members:
                for name in nulls.SCHEDULE_NAMES:
                    with self.subTest(world=world.world, member=member.member, name=name):
                        result = source.run_schedule(
                            world, member.member, name=name, count_context=lambda prefix: 1,
                            count_action=lambda raw: 1, counter_provenance="synthetic-unit-count",
                            master=b"synthetic-rollout-master",
                        )
                        self.assertLessEqual(len(result.attempts), 29)
                        self.assertEqual(len(result.calls), 29)
                        self.assertIsNotNone(result.terminal_reason)
                        self.assertEqual(result.prefix[:2], world.public_view(member.member).prefix)

    def test_missing_counter_provenance_rejected(self):
        with self.assertRaisesRegex(ValueError, "explicit_counter_provenance"):
            self.run_fixture(counter_provenance="")

    def test_raw_action_survives_uncapturable_metadata(self):
        result = source.run_schedule(
            self.worlds[0], "m0", name="S_DISPLAY0", count_context=lambda prefix: 1,
            count_action=lambda raw: object(), counter_provenance="synthetic-invalid-counter",
            master=b"synthetic-only",
        )
        self.assertEqual(result.terminal_reason, "unsupported_custody_transport")
        self.assertEqual(result.attempts, ())
        self.assertEqual(result.calls[0].raw_bytes,
                         ("READ INDEX " + self.worlds[0].members[0].task.current).encode("ascii"))

    def test_final_schedule_observation_delivers_executed_service(self):
        policies = []
        original = nulls.BoundedSchedule

        def tracked(*arguments, **keywords):
            policy = original(*arguments, **keywords)
            policies.append(policy)
            return policy

        with patch.object(nulls, "BoundedSchedule", side_effect=tracked):
            result = source.run_schedule(
                self.worlds[0], "m0", name="S_DISPLAY0",
                count_context=lambda prefix: 1 if len(prefix) == 2 else wire.CONTEXT_CAP,
                count_action=lambda raw: 1, counter_provenance="synthetic-context-exhaustion",
                master=b"synthetic-only",
            )
        self.assertEqual(result.terminal_reason, "zero_allowance")
        self.assertEqual(len(result.attempts), 1)
        self.assertEqual(policies[0].trace, tuple(nulls.PublicMessage(message.role, message.content.encode("ascii"))
                                                for message in result.prefix))

    def test_counter_exception_does_not_invent_executed_policy_action(self):
        policies = []
        original = nulls.BoundedSchedule

        def tracked(*arguments, **keywords):
            policy = original(*arguments, **keywords)
            policies.append(policy)
            return policy

        def bad_counter(raw):
            raise RuntimeError("fixture failure before execution")

        with patch.object(nulls, "BoundedSchedule", side_effect=tracked):
            result = source.run_schedule(
                self.worlds[0], "m0", name="S_DISPLAY0", count_context=lambda prefix: 1,
                count_action=bad_counter, counter_provenance="synthetic-counter-failure",
                master=b"synthetic-only",
            )
        self.assertEqual(result.attempts, ())
        self.assertEqual(len(policies[0].trace), 2)


if __name__ == "__main__":
    unittest.main()
