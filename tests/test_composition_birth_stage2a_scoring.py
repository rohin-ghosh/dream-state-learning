"""Offline synthetic replay, not model/tokenizer evidence or null acceptance."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from tests.test_composition_birth_stage2a_held import fixtures


WRONG_EVENT = "M2AE_BBBBBBBBBBBB"
WRONG_QUERY = "M2AQ_BBBBBBBBBBBB"


def task_text(task):
    return f"TASK\nSTART {task.start}\nGOAL {task.goal}\nCURRENT {task.current}"


def turn(session, raw, **overrides):
    options = dict(generation_request={"max_new_tokens": min(256, wire.TOKEN_CAP - session.state.actual_tokens,
                                                           wire.CONTEXT_CAP - 1)},
                   declared_tokens=1, actual_tokens=1, context_tokens=1, truncated=False, finish_reason="stop")
    options.update(overrides)
    return session.turn(raw, **options)


def run_fixture(world, member, actions=None, *, generation_overrides=None):
    script = iter(actions if actions is not None else [item.action for item in member.expected_trace])
    overrides = generation_overrides or {}

    def actor(request):
        return rollout.Generation(next(script), **dict(
            dict(declared_tokens=1, actual_tokens=1, truncated=False, finish_reason="stop"), **overrides))

    return rollout.run_chain(world, member.member, actor=actor, count_context=lambda prefix: 1,
                             counter_provenance="synthetic-one-per-call-not-tokenizer",
                             master=b"synthetic-rollout-master", stage="D1")


class SourceScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chain_tokens = fixtures("dose_chain")
        cls.worlds = tuple(held.build_chain_world(world=f"h{index:02d}", role_tokens=chain_tokens[f"h{index:02d}"])
                           for index in range(16))
        cls.pairs = held.build_intervention_panel(role_tokens_by_world=fixtures("dose_intervention"))
        cls.gold = {(world.world, member.member): run_fixture(world, member)
                    for world in cls.worlds for member in world.members}

    def setUp(self):
        self.world = self.worlds[0]
        self.member = self.world.members[0]
        self.actions = [item.action for item in self.member.expected_trace]
        self.run = self.gold[self.world.world, self.member.member]

    def score_actions(self, actions, world=None, member=None):
        world = world or self.world
        member = member or self.member
        run = run_fixture(world, member, actions)
        return run, scoring.score_chain(run.attempts, member)

    def test_all_32_synthetic_gold_chains_and_16_twin_pairs(self):
        strata = {}
        for world in self.worlds:
            runs = tuple(self.gold[world.world, member.member].attempts for member in world.members)
            pair_score = scoring.score_chain_pair(runs, world.members)
            self.assertTrue(pair_score.pair_both_correct)
            for member, score, attempts in zip(world.members, pair_score.members, runs):
                with self.subTest(world=world.world, member=member.member):
                    self.assertTrue(score.whole_chain_success)
                    self.assertTrue(score.mechanical_goal_arrival_stop)
                    self.assertTrue(score.public_read_evidence_before_steps)
                    self.assertTrue(score.first_step_correct)
                    self.assertTrue(score.full_route_correct)
                    self.assertTrue(score.first_outcome_check_command_correct)
                    self.assertTrue(score.first_outcome_check_operand_correct)
                    self.assertEqual(score.first_outcome_check_count, 1)
                    self.assertEqual(score.pre_first_step_outside_sufficient_reads, 0)
                    self.assertEqual(len(score.reads), 3 if world.mismatch else 4)
                    self.assertEqual(len(attempts), 7 if world.mismatch else 8)
                    self.assertTrue(all(type(attempt) is wire.Attempt for attempt in attempts))
                    self.assertFalse(any(score.science_gates.values()))
                    strata[world.mismatch, world.skin] = strata.get((world.mismatch, world.skin), 0) + 1
        self.assertEqual(strata, {(False, 0): 8, (True, 0): 8, (False, 1): 8, (True, 1): 8})

    def test_all_64_intervention_members_and_32_pairs(self):
        for pair in self.pairs:
            outputs = tuple(member.expected_target.bytes for member in pair.members)
            score = scoring.score_intervention_pair(outputs, pair)
            with self.subTest(world=pair.world):
                self.assertTrue(score.pair_both_correct)
                self.assertTrue(score.command_both)
                self.assertTrue(score.operand_both)
                self.assertTrue(score.typed_both)
                self.assertTrue(all(item.execution_valid is None for item in score.members))
                swapped = scoring.score_intervention_pair(outputs[::-1], pair)
                self.assertFalse(swapped.pair_both_correct)
                self.assertFalse(any(item.exact_member_correct for item in swapped.members))

    def test_intervention_check_command_and_operand_are_independent(self):
        pair = next(pair for pair in self.pairs if pair.world == "check_k0")
        member = pair.members[0]
        target = member.expected_target
        wrong_verb = "THINK REVISE " + target.operand
        score = scoring.score_intervention_member(wrong_verb, member)
        self.assertTrue(score.typed_valid)
        self.assertFalse(score.command_correct)
        self.assertTrue(score.operand_correct)
        self.assertFalse(score.exact_member_correct)
        score = scoring.score_intervention_member("THINK KEEP " + WRONG_EVENT, member)
        self.assertTrue(score.command_correct)
        self.assertFalse(score.operand_correct)
        self.assertFalse(score.exact_member_correct)

    def test_intervention_stop_has_none_operand_not_an_empty_string(self):
        member = next(pair for pair in self.pairs if pair.world == "continue_k0").members[0]
        self.assertEqual(member.expected_target.bytes, "STOP")
        self.assertIsNone(member.expected_target.operand)
        self.assertTrue(scoring.score_intervention_member("STOP", member).operand_correct)
        for raw in ("STOP ", "STOP\n", " STOP", b"STOP", None, True, 1, "STOP\r", "STOP\0"):
            with self.subTest(raw=raw):
                score = scoring.score_intervention_member(raw, member)
                self.assertFalse(score.typed_valid)
                self.assertFalse(score.exact_member_correct)

    def test_intervention_scores_actual_attempt_and_length_metadata(self):
        member = next(pair for pair in self.pairs if pair.world == "check_k0").members[0]
        for options in ({}, {"finish_reason": "length"}, {"truncated": True}):
            session = wire.Session(task_text(member.task), member.world_edges,
                                   wire.PassiveRegistry(member.registry, skin=member.construction.skin))
            attempt = turn(session, member.expected_target.bytes, **options)
            score = scoring.score_intervention_member(attempt, member)
            with self.subTest(options=options):
                self.assertTrue(score.typed_valid)
                self.assertTrue(score.command_correct)
                self.assertTrue(score.operand_correct)
                self.assertEqual(score.exact_member_correct, not options)
                self.assertEqual(score.execution_valid, not options)

    def test_intervention_pair_never_uses_average_or_any_member(self):
        for pair in self.pairs:
            outputs = (pair.members[0].expected_target.bytes, "invalid")
            score = scoring.score_intervention_pair(outputs, pair)
            self.assertTrue(score.members[0].exact_member_correct)
            self.assertFalse(score.members[1].exact_member_correct)
            self.assertFalse(score.pair_both_correct)

    def test_bound_one_turn_null_sentinels_are_typed_but_incorrect(self):
        sentinels = {
            "seek": "READ RELATION M2AQ_AAAAAAAAAAAA", "prospect": "STEP M2AP_AAAAAAAAAAAA",
            "check": "THINK KEEP M2AE_AAAAAAAAAAAA", "continue": "READ INDEX M2AN_AAAAAAAAAAAA",
        }
        for pair in self.pairs:
            for member in pair.members:
                score = scoring.score_intervention_member(sentinels[member.transition_name], member)
                self.assertTrue(score.typed_valid)
                self.assertFalse(score.exact_member_correct)

    def test_intervention_shape_pair_identity_and_target_integrity(self):
        pair = self.pairs[0]
        outputs = tuple(member.expected_target.bytes for member in pair.members)
        for values in ([], outputs[:1], outputs + ("STOP",)):
            with self.assertRaises(scoring.ScoreInputError):
                scoring.score_intervention_pair(values, pair)
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_intervention_pair(outputs, replace(pair, members=pair.members[::-1]))
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_intervention_pair(outputs, replace(pair, members=(None, None)))
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_intervention_pair(outputs, replace(pair, members=(pair.members[0], self.pairs[1].members[1])))
        member = pair.members[0]
        for change in (dict(sha256="0" * 64), dict(command="STOP"), dict(operand=None), dict(bytes="invalid")):
            with self.subTest(change=change), self.assertRaises(scoring.ScoreInputError):
                scoring.score_intervention_member(outputs[0], replace(member, expected_target=replace(member.expected_target, **change)))

    def test_wrong_check_verb_reaches_goal_but_fails_whole_chain(self):
        for world in (self.worlds[0], self.worlds[4]):
            member = world.members[0]
            actions = [item.action for item in member.expected_trace]
            verb = "KEEP" if world.mismatch else "REVISE"
            actions[3] = "THINK " + verb + " " + wire.parse_action(actions[3]).operand
            run, score = self.score_actions(actions, world, member)
            self.assertTrue(run.state.goal_arrival_stop)
            self.assertTrue(score.mechanical_goal_arrival_stop)
            self.assertTrue(score.full_route_correct)
            self.assertTrue(score.first_outcome_check_operand_correct)
            self.assertFalse(score.first_outcome_check_command_correct)
            self.assertFalse(score.whole_chain_success)

    def test_wrong_check_event_or_query_operand_fails_without_changing_arrival(self):
        for operand in (WRONG_EVENT, WRONG_QUERY):
            world = self.worlds[4] if operand == WRONG_QUERY else self.world
            member = world.members[0]
            actions = [item.action for item in member.expected_trace]
            actions[3] = "THINK " + ("REVISE " if world.mismatch else "KEEP ") + operand
            _, score = self.score_actions(actions, world, member)
            self.assertTrue(score.mechanical_goal_arrival_stop)
            self.assertTrue(score.first_outcome_check_command_correct)
            self.assertFalse(score.first_outcome_check_operand_correct)
            self.assertTrue(score.strict_typing)
            self.assertFalse(score.whole_chain_success)

    def test_missing_duplicate_or_late_first_outcome_check(self):
        scripts = (
            self.actions[:3] + self.actions[4:],
            self.actions[:4] + [self.actions[3]] + self.actions[4:],
            self.actions[:3] + self.actions[4:-1] + [self.actions[3], "STOP"],
        )
        for actions in scripts:
            _, score = self.score_actions(actions)
            self.assertTrue(score.mechanical_goal_arrival_stop)
            self.assertFalse(score.first_outcome_check_correct)
            self.assertFalse(score.whole_chain_success)

    def test_read_between_step_and_check_does_not_invent_adjacency_rule(self):
        actions = self.actions[:3] + [self.actions[4]] + self.actions[3:]
        _, score = self.score_actions(actions)
        self.assertTrue(score.whole_chain_success)
        self.assertTrue(any(read.repeated for read in score.reads))
        self.assertEqual(score.first_outcome_check_count, 1)

    def test_incomplete_run_keeps_correct_first_step_and_check_diagnostics(self):
        _, score = self.score_actions(self.actions[:4])
        self.assertTrue(score.first_step_correct)
        self.assertTrue(score.first_outcome_check_correct)
        self.assertFalse(score.full_route_correct)
        self.assertFalse(score.goal_arrival)
        self.assertFalse(score.whole_chain_success)

    def test_hidden_port_guess_without_public_reads_is_not_whole_success(self):
        for removed in ("all", "first", "second"):
            actions = [raw for index, raw in enumerate(self.actions)
                       if not (raw.startswith("READ ") and (removed == "all" or
                               removed == "first" and index < 2 or removed == "second" and index > 3))]
            _, score = self.score_actions(actions)
            with self.subTest(removed=removed):
                self.assertTrue(score.full_route_correct)
                self.assertTrue(score.mechanical_goal_arrival_stop)
                self.assertFalse(score.public_read_evidence_before_steps)
                self.assertFalse(score.sufficient_reads_complete)
                self.assertFalse(score.whole_chain_success)
                if removed in ("all", "first"):
                    self.assertFalse(score.useful_pre_first_step_read)

    def test_prefetched_second_hop_reads_do_not_supply_evidence_at_first_hub(self):
        actions = self.actions[:2] + self.actions[4:6] + self.actions[2:4] + self.actions[6:]
        _, score = self.score_actions(actions)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertTrue(score.sufficient_reads_complete)
        self.assertFalse(score.public_read_evidence_before_steps)
        self.assertFalse(score.whole_chain_success)

    def test_repeated_sufficient_reads_within_wire_caps_are_not_a_new_threshold(self):
        actions = [self.actions[0]] * 3 + self.actions[1:]
        _, score = self.score_actions(actions)
        self.assertEqual(score.pre_first_step_outside_sufficient_reads, 0)
        self.assertEqual(sum(read.repeated for read in score.reads), 2)
        self.assertTrue(score.whole_chain_success)

    def test_read_classes_and_exact_one_outside_sufficient_allowance(self):
        directory = wire.parse_service(self.member.expected_trace[0].response[len("SERVICE\n"):], skin=self.world.skin)
        other = next("READ RELATION " + row.query for row in directory.rows
                     if "READ RELATION " + row.query not in self.member.sufficient_reads)
        for extra, expected_class in ((other, "INITIAL_CANDIDATE_OTHER"),
                                      ("READ RELATION " + WRONG_QUERY, "OTHER")):
            for count in (1, 2):
                actions = self.actions[:1] + [extra] * count + self.actions[1:]
                _, score = self.score_actions(actions)
                with self.subTest(extra=extra, count=count):
                    self.assertTrue(score.mechanical_goal_arrival_stop)
                    self.assertEqual(score.pre_first_step_outside_sufficient_reads, count)
                    self.assertEqual(score.reads[1].read_class, expected_class)
                    self.assertEqual(score.pre_first_step_read_limit, count == 1)
                    self.assertEqual(score.whole_chain_success, count == 1)
                    if expected_class == "OTHER":
                        self.assertEqual(score.reads[1].returned_kind, "MISS")
                        self.assertFalse(score.reads[1].useful)

    def test_later_recover_query_is_not_an_initial_candidate(self):
        world = self.worlds[4]
        member = world.members[0]
        score = scoring.score_chain(self.gold[world.world, member.member].attempts, member)
        recovery = score.reads[-1]
        self.assertEqual(recovery.read_class, "SUFFICIENT")
        self.assertFalse(recovery.initial_candidate)
        self.assertTrue(recovery.useful)
        self.assertFalse(recovery.pre_first_step)

    def test_additional_read_after_first_step_has_no_invented_pre_step_penalty(self):
        actions = self.actions[:4] + ["READ RELATION " + WRONG_QUERY] * 2 + self.actions[4:]
        _, score = self.score_actions(actions)
        self.assertEqual(score.pre_first_step_outside_sufficient_reads, 0)
        self.assertTrue(score.whole_chain_success)

    def test_extra_step_loop_keeps_mechanical_arrival_but_fails_full_route(self):
        first = self.member.expected_trace[2]
        transitions = dict(self.world.world_edges)
        transitions[first.current_after, wire.parse_action(first.action).operand] = first.current_after
        session = wire.Session(task_text(self.member.task), transitions,
                               wire.PassiveRegistry(self.world.registry, skin=self.world.skin))
        for action in self.actions[:4] + [first.action] + self.actions[4:]:
            turn(session, action)
        score = scoring.score_chain(session.attempts, self.member)
        self.assertTrue(session.state.goal_arrival_stop)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertTrue(score.first_step_correct)
        self.assertFalse(score.full_route_correct)
        self.assertFalse(score.stop_immediately_after_second_step)
        self.assertFalse(score.whole_chain_success)

    def test_correct_stop_must_immediately_follow_second_step(self):
        for extra in ("READ INDEX " + self.member.task.goal, self.actions[3]):
            _, score = self.score_actions(self.actions[:-1] + [extra, "STOP"])
            self.assertTrue(score.mechanical_goal_arrival_stop)
            self.assertTrue(score.goal_arrival)
            self.assertTrue(score.full_route_correct)
            self.assertTrue(score.exact_stop)
            self.assertFalse(score.stop_immediately_after_second_step)
            self.assertFalse(score.whole_chain_success)

    def test_premature_stop_is_exact_syntax_not_successful_arrival(self):
        for actions in (["STOP"], self.actions[:4] + ["STOP"]):
            _, score = self.score_actions(actions)
            self.assertTrue(score.exact_stop)
            self.assertTrue(score.strict_typing)
            self.assertFalse(score.goal_arrival)
            self.assertFalse(score.mechanical_goal_arrival_stop)
            self.assertFalse(score.whole_chain_success)

    def test_arrival_without_stop_is_not_whole_chain_success(self):
        _, score = self.score_actions(self.actions[:-1])
        self.assertTrue(score.goal_arrival)
        self.assertTrue(score.full_route_correct)
        self.assertFalse(score.exact_stop)
        self.assertFalse(score.mechanical_goal_arrival_stop)
        self.assertFalse(score.whole_chain_success)

    def test_malformed_and_wrong_typed_actions_are_captured_failures(self):
        for raw in ("STOP\n", " STEP " + WRONG_EVENT, "STEP " + WRONG_EVENT,
                    "THINK KEEP " + self.member.task.start, "STOP\0", "STOP\r", "é", b"STOP", None):
            session = wire.Session(task_text(self.member.task), self.world.world_edges,
                                   wire.PassiveRegistry(self.world.registry, skin=self.world.skin))
            turn(session, raw)
            score = scoring.score_chain(session.attempts, self.member)
            with self.subTest(raw=raw):
                self.assertFalse(score.strict_typing)
                self.assertFalse(score.execution_valid)
                self.assertFalse(score.whole_chain_success)

    def test_length_finish_truncation_and_accounting_failure_not_repaired(self):
        for overrides in (dict(finish_reason="length"), dict(truncated=True),
                          dict(declared_tokens=2), dict(actual_tokens=0), dict(finish_reason="eos")):
            result = run_fixture(self.world, self.member, [self.actions[0]], generation_overrides=overrides)
            score = scoring.score_chain(result.attempts, self.member)
            with self.subTest(overrides=overrides):
                self.assertEqual(len(result.attempts), 1)
                self.assertTrue(score.strict_typing)
                self.assertFalse(score.execution_valid)
                self.assertFalse(score.generation_valid)
                self.assertFalse(score.whole_chain_success)

    def test_generation_request_and_context_failures_are_scored_from_captures(self):
        for overrides in (dict(generation_request={"max_new_tokens": 255}),
                          dict(context_tokens=True), dict(context_tokens=wire.CONTEXT_CAP),
                          dict(declared_tokens=True), dict(truncated=0), dict(finish_reason=None)):
            session = wire.Session(task_text(self.member.task), self.world.world_edges,
                                   wire.PassiveRegistry(self.world.registry, skin=self.world.skin))
            turn(session, self.actions[0], **overrides)
            score = scoring.score_chain(session.attempts, self.member)
            with self.subTest(overrides=overrides):
                self.assertTrue(score.strict_typing)
                self.assertFalse(score.generation_valid)
                self.assertFalse(score.execution_valid)
                self.assertFalse(score.whole_chain_success)

    def test_accepted_flag_alone_does_not_certify_generation_metadata(self):
        attempt = self.run.attempts[0]
        bad_request = ("dict", ((("str", "max_new_tokens"), ("int", 255)),))
        changed = replace(attempt, capture=replace(attempt.capture, generation_request=bad_request))
        score = scoring.score_chain((changed,) + self.run.attempts[1:], self.member)
        self.assertTrue(score.execution_valid)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertFalse(score.generation_valid)
        self.assertFalse(score.whole_chain_success)

    def test_empty_attempts_fail_without_fabricating_call(self):
        score = scoring.score_chain((), self.member)
        self.assertEqual(score.attempt_count, 0)
        self.assertEqual(score.reads, ())
        self.assertFalse(score.strict_typing)
        self.assertFalse(score.execution_valid)
        self.assertFalse(score.whole_chain_success)

    def test_budget_failure_keeps_offending_read(self):
        result = run_fixture(self.world, self.member, [self.actions[0]] * 13)
        self.assertEqual(result.terminal_reason, "over_budget")
        score = scoring.score_chain(result.attempts, self.member)
        self.assertEqual(len(score.reads), 13)
        self.assertEqual(score.reads[-1].returned_kind, "NOT_ACCEPTED")
        self.assertTrue(score.strict_typing)
        self.assertFalse(score.within_budgets)
        self.assertFalse(score.whole_chain_success)

    def test_post_terminal_attempts_do_not_inherit_goal_success(self):
        session = wire.Session(task_text(self.member.task), self.world.world_edges,
                               wire.PassiveRegistry(self.world.registry, skin=self.world.skin))
        for action in self.actions + ["STOP"]:
            turn(session, action)
        score = scoring.score_chain(session.attempts, self.member)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertFalse(score.execution_valid)
        self.assertFalse(score.exact_stop)
        self.assertFalse(score.whole_chain_success)

    def test_attempt_tuple_bound_and_full_sequence_required(self):
        for attempts in (list(self.run.attempts), (None,), self.run.attempts * 4, self.run.attempts[1:]):
            with self.subTest(kind=type(attempts)), self.assertRaises(scoring.ScoreInputError):
                scoring.score_chain(attempts, self.member)
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain((self.run.attempts[0], self.run.attempts[2]), self.member)

    def test_thirtieth_capture_fails_call_budget_and_larger_input_is_rejected(self):
        session = wire.Session(task_text(self.member.task), self.world.world_edges,
                               wire.PassiveRegistry(self.world.registry, skin=self.world.skin))
        for index in range(30):
            turn(session, self.actions[0])
        score = scoring.score_chain(session.attempts, self.member)
        self.assertEqual(score.attempt_count, 30)
        self.assertFalse(score.within_budgets)
        self.assertFalse(score.whole_chain_success)
        turn(session, self.actions[0])
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain(session.attempts, self.member)

    def test_capture_mutations_rejected_not_trusted_as_scores(self):
        attempt = self.run.attempts[0]
        alternatives = (
            replace(attempt, capture=replace(attempt.capture, call_index=1)),
            replace(attempt, capture=replace(attempt.capture, raw_bytes=b"STOP")),
            replace(attempt, capture=replace(attempt.capture, generation_request=[])),
            replace(attempt, action=wire.parse_action("STOP")),
            replace(attempt, parser_disposition="invalid"),
            replace(attempt, post_state=replace(attempt.post_state, current=self.member.task.goal)),
            replace(attempt, post_state=replace(attempt.post_state, counts=(("READ", 1),))),
            replace(attempt, post_state=replace(attempt.post_state, actual_tokens=9)),
        )
        for changed in alternatives:
            with self.subTest(changed=changed.parser_disposition), self.assertRaises(scoring.ScoreInputError):
                scoring.score_chain((changed,) + self.run.attempts[1:], self.member)

    def test_changed_captured_service_bytes_cannot_satisfy_witness_reads(self):
        changed = replace(self.run.attempts[1], response_bytes=b"SERVICE\nMISS")
        attempts = self.run.attempts[:1] + (changed,) + self.run.attempts[2:]
        score = scoring.score_chain(attempts, self.member)
        self.assertTrue(score.mechanical_goal_arrival_stop)
        self.assertTrue(score.sufficient_reads_complete)
        self.assertFalse(score.public_read_evidence_before_steps)
        self.assertFalse(score.useful_pre_first_step_read)
        self.assertFalse(score.whole_chain_success)

    def test_step_outcome_and_mechanical_flag_integrity(self):
        attempts = self.run.attempts
        changed = replace(attempts[2], response_bytes=b"WORLD\nCURRENT " + self.member.task.goal.encode())
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain(attempts[:2] + (changed,) + attempts[3:], self.member)
        changed = replace(attempts[-1], post_state=replace(attempts[-1].post_state, goal_arrival_stop=False))
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain(attempts[:-1] + (changed,), self.member)

    def test_witness_integrity_and_sufficient_set_are_rederived(self):
        trace = self.member.expected_trace
        alternatives = (
            replace(self.member, expected_trace=list(trace)),
            replace(self.member, sufficient_reads=set(self.member.sufficient_reads)),
            replace(self.member, sufficient_reads=frozenset()),
            replace(self.member, expected_trace=trace[:-1]),
            replace(self.member, task=replace(self.member.task, current=self.member.task.goal)),
            replace(self.member, expected_trace=trace[:3] + (replace(trace[3], action="THINK REVISE " + WRONG_EVENT),) + trace[4:]),
            replace(self.member, expected_trace=(replace(trace[0], current_after=self.member.task.goal),) + trace[1:]),
            replace(self.member, expected_trace=(replace(trace[0], response=None),) + trace[1:]),
            replace(self.member, expected_trace=(replace(trace[0], current_before=None),) + trace[1:]),
            replace(self.member, expected_trace=trace[:1] + (replace(trace[1], action="READ RELATION " + WRONG_QUERY),) + trace[2:]),
        )
        for member in alternatives:
            with self.assertRaises(scoring.ScoreInputError):
                scoring.score_chain(self.run.attempts, member)

    def test_chain_pair_is_both_not_either_and_rejects_member_mixing(self):
        bad = run_fixture(self.world, self.world.members[1], ["STOP"])
        score = scoring.score_chain_pair((self.run.attempts, bad.attempts), self.world.members)
        self.assertTrue(score.members[0].whole_chain_success)
        self.assertFalse(score.members[1].whole_chain_success)
        self.assertFalse(score.pair_both_correct)
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain_pair((self.run.attempts, self.run.attempts), self.world.members[::-1])
        with self.assertRaises(scoring.ScoreInputError):
            scoring.score_chain_pair((self.run.attempts, self.run.attempts),
                                     (self.world.members[0], self.worlds[1].members[1]))

    def test_all_six_public_schedules_score_across_strata_without_threshold_claim(self):
        from organism_v6 import composition_birth_stage2a_nulls as nulls

        for world in (self.worlds[0], self.worlds[4], self.worlds[8], self.worlds[12]):
            for member in world.members:
                for name in nulls.SCHEDULE_NAMES:
                    with self.subTest(world=world.world, member=member.member, name=name):
                        run = rollout.run_schedule(
                            world, member.member, name=name, count_context=lambda prefix: 1,
                            count_action=lambda raw: 1, counter_provenance="synthetic-unit-not-tokenizer",
                            master=b"synthetic-rollout-master",
                        )
                        score = scoring.score_chain(run.attempts, member)
                        self.assertEqual(score.attempt_count, len(run.attempts))
                        self.assertIs(type(score.whole_chain_success), bool)
                        self.assertFalse(any(score.science_gates.values()))

    def test_scores_are_frozen_and_flags_never_open(self):
        score = scoring.score_chain(self.run.attempts, self.member)
        with self.assertRaises(FrozenInstanceError):
            score.whole_chain_success = False
        with self.assertRaises(TypeError):
            score.science_gates["GO_CLAIM"] = True
        self.assertEqual(score.status, "PARTIAL_SOURCE_ONLY")
        for name in ("GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"):
            self.assertIs(getattr(scoring, name), False)
            self.assertIs(score.science_gates[name], False)

    def test_source_pins_v2_v4_v5_are_exact(self):
        root = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for version, expected in scoring.CONTRACT_HASHES.items():
            path = root / f"2026-09-13_m_combine4_stage2a_binding_successor_{version}.md"
            self.assertEqual(sha256(path.read_bytes()).hexdigest(), expected)

    def test_offline_scoring_never_calls_actor_session_runner_or_files(self):
        original = self.run.attempts
        with patch.object(wire, "Session", side_effect=AssertionError("no sessions in scoring")), \
                patch.object(rollout, "run_chain", side_effect=AssertionError("no runner")), \
                patch("builtins.open", side_effect=AssertionError("no files")), \
                patch("pathlib.Path.open", side_effect=AssertionError("no files")), \
                patch("socket.socket", side_effect=AssertionError("no network")):
            score = scoring.score_chain(original, self.member)
        self.assertTrue(score.whole_chain_success)
        self.assertIs(original, self.run.attempts)


if __name__ == "__main__":
    unittest.main()
