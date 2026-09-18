"""Synthetic in-memory captures only; no tokenizer, model, disk or native gate."""

from dataclasses import replace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as source
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from tests.test_composition_birth_stage2a_held import fixtures


MASTER = b"synthetic-reduced-admission"
BASE_ID = "synthetic-BASE-attempt-1"
ATOM_ID = "synthetic-ATOM_LOCAL-D1-attempt-1"


def generation(raw):
    return rollout.Generation(raw, 1, 1, False, "stop")


def with_row(run, index, row):
    return replace(run, reservations=run.reservations[:index] + (row,) + run.reservations[index + 1:])


class ReducedScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chain_tokens = fixtures("dose_chain")
        cls.chains = {task: held.build_chain_world(world=f"h{task // 2:02d}",
                                                  role_tokens=chain_tokens[f"h{task // 2:02d}"])
                      for task in screen.CHAIN_TASKS}
        intervention_tokens = fixtures("dose_intervention")
        cls.interventions = {
            (transition, index): held.build_intervention_pair(
                world=f"{transition.lower()}_k{index}",
                role_tokens=intervention_tokens[f"{transition.lower()}_k{index}"])
            for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS}
        canary_tokens = {role: token for tokens in fixtures("generic_canary").values()
                         for role, token in tokens.items()}
        cls.canaries = canary_api.build_canaries(role_tokens=canary_tokens)
        cls.base = cls.make_run(BASE_ID, successes=0)
        cls.fitted = cls.make_run(ATOM_ID)

    @classmethod
    def make_run(cls, state_id, *, successes=8, chain_actions=None, overrides=None,
                 sink=None, counter=None, actor_offset=0):
        actions = {}
        chain_actions = chain_actions or {}
        overrides = overrides or {}
        for position, task in enumerate(screen.CHAIN_TASKS):
            script = chain_actions.get(task)
            if script is None:
                script = ([turn.action for turn in cls.chains[task].members[0].expected_trace]
                          if position < successes else ["STOP"])
            for call_index, raw in enumerate(script):
                actions[position * 29 + call_index] = generation(raw)
        for position, (transition, pair_index) in enumerate(
                (transition, index) for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS):
            pair = cls.interventions[(transition, pair_index)]
            for member_index, member in enumerate(pair.members):
                actions[232 + position * 2 + member_index] = generation(member.expected_target.bytes)
        for index, canary in enumerate(cls.canaries):
            actions[264 + index] = generation(canary.target)
        actions.update(overrides)
        seeds = screen.reduced_decode_seeds("D1", master=MASTER)
        outputs = {seeds[index]: value for index, value in actions.items()}
        records = [dict(request=object()) for _ in range(actor_offset)]

        def actor(request):
            record = dict(request=request, generation=None, error=None, native_output=object())
            records.append(record)
            value = outputs[request.seed]
            if isinstance(value, BaseException):
                record["error"] = value
                raise value
            record["generation"] = value
            return value

        return runtime.run_reduced_state(
            state_id=state_id, stage="D1", master=MASTER, chains=cls.chains,
            interventions=cls.interventions, canaries=cls.canaries,
            actor=actor, actor_calls=records, count_context=counter or (lambda prefix: 1),
            counter_provenance="SYNTHETIC_FIXTURE", custody_sink=sink or (lambda event, payload: None))

    def reduce(self, **changes):
        options = dict(base=self.base, atom_local=self.fitted, base_state_id=BASE_ID,
                       atom_local_state_id=ATOM_ID, master=MASTER, chains=self.chains,
                       interventions=self.interventions, canaries=self.canaries)
        options.update(changes)
        return source.reduce_base_d1(**options)

    def assert_nonreportable(self, run):
        result = self.reduce(atom_local=run)
        self.assertFalse(result.reportable)
        self.assertIsNone(result.criteria_passed)
        self.assertEqual(result.criteria, ())
        self.assertIs(result.atom_local.run, run)
        self.assertTrue(result.atom_local.issues)
        self.assertFalse(result.native_authorized)
        return result

    def delayed_stop(self, task):
        member = self.chains[task].members[0]
        return ([turn.action for turn in member.expected_trace[:-1]]
                + ["READ INDEX " + member.task.start, "STOP"])

    def test_full_positive_exact_denominators_and_no_authority(self):
        result = self.reduce()
        self.assertTrue(result.reportable)
        self.assertTrue(result.criteria_passed)
        self.assertEqual(result.atom_local.metrics.skill_pairs,
                         tuple((name, 4) for name in primitives.TRANSITIONS))
        self.assertEqual([(item.count, item.denominator, item.minimum) for item in result.criteria],
                         [(4, 4, 3)] * 4 + [(32, 32, 30), (8, 8, 6), (8, 8, 7),
                                             (8, 8, 7), (16, 16, 15), (8, 8, 2)])
        self.assertEqual(sum(state.accounting.observed_reservations
                             for state in (result.base, result.atom_local)), 560)
        self.assertEqual(result.base.accounting.physical_calls, 56)
        self.assertEqual(dict(result.base.accounting.dispositions), {"EXECUTED": 56, "UNUSED": 224})
        self.assertEqual(result.atom_local.accounting.physical_calls,
                         sum(len(self.chains[task].members[0].expected_trace) for task in screen.CHAIN_TASKS) + 48)
        self.assertFalse(result.native_authorized)
        self.assertFalse(result.persisted_custody_verified)
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        self.assertTrue(all(member.execution_valid is None
                            for pair in result.atom_local.metrics.intervention_scores for member in pair.members))

    def test_exact_minima_and_existing_strict_typing_definition(self):
        actions = {24: self.delayed_stop(24), 28: ["malformed"]}
        overrides = {232: generation("malformed"), 240: generation("malformed"),
                     248: generation("STOP"), 256: generation("STOP"), 279: generation("STOP\n")}
        expected = self.interventions[("CONTINUE", 0)].members[0]
        if expected.expected_target.bytes == "STOP":
            overrides[256] = generation("READ INDEX " + expected.task.start)
        fitted = self.make_run(ATOM_ID, successes=6, chain_actions=actions, overrides=overrides)
        result = self.reduce(base=self.make_run(BASE_ID, successes=4), atom_local=fitted)
        self.assertTrue(result.reportable, result.atom_local.issues)
        self.assertTrue(result.criteria_passed, result.criteria)
        self.assertEqual([item.count for item in result.criteria], [3, 3, 3, 3, 30, 6, 7, 7, 15, 2])
        self.assertEqual(result.atom_local.metrics.typed_steps,
                         sum(score.strict_typing for score in result.atom_local.metrics.chain_scores))

    def test_each_skill_is_separate_and_pair_requires_both_members(self):
        for position, transition in enumerate(primitives.TRANSITIONS):
            with self.subTest(transition=transition):
                fitted = self.make_run(ATOM_ID, overrides={232 + position * 8: generation("bad"),
                                                          234 + position * 8: generation("bad")})
                result = self.reduce(atom_local=fitted)
                self.assertTrue(result.reportable)
                self.assertFalse(result.criteria_passed)
                self.assertEqual(dict(result.atom_local.metrics.skill_pairs)[transition], 2)
                self.assertFalse(result.criteria[position].passed)

    def test_individual_integer_minima_and_negative_gain(self):
        cases = (
            ("typed_interventions", self.base, self.make_run(ATOM_ID, overrides={
                index: generation("bad") for index in (232, 233, 240)}), 29),
            ("whole_chains", self.base, self.make_run(ATOM_ID, chain_actions={
                task: self.delayed_stop(task) for task in (20, 24, 28)}), 5),
            ("useful_reads", self.base, self.make_run(ATOM_ID, successes=6), 6),
            ("typed_steps", self.base, self.make_run(ATOM_ID, chain_actions={24: ["bad"], 28: ["bad"]}), 6),
            ("canaries", self.base, self.make_run(ATOM_ID, overrides={278: generation("bad"), 279: generation("bad")}), 14),
            ("chain_gain", self.make_run(BASE_ID, successes=7), self.fitted, 1),
            ("chain_gain", self.make_run(BASE_ID), self.make_run(ATOM_ID, successes=6), -2),
        )
        for name, baseline, fitted, count in cases:
            with self.subTest(name=name, count=count):
                result = self.reduce(base=baseline, atom_local=fitted)
                self.assertTrue(result.reportable, (result.base.issues, result.atom_local.issues))
                criterion = next(item for item in result.criteria if item.name == name)
                self.assertEqual(criterion.count, count)
                self.assertFalse(criterion.passed)
                self.assertFalse(result.criteria_passed)

    def test_length_limited_correct_text_cannot_receive_credit(self):
        overrides = {index: replace(self.fitted.reservations[index].custody.generation,
                                    truncated=True, finish_reason="length") for index in (0, 232, 264)}
        fitted = self.make_run(ATOM_ID, overrides=overrides)
        result = self.reduce(atom_local=fitted)
        self.assertTrue(result.reportable, result.atom_local.issues)
        self.assertFalse(result.atom_local.metrics.chain_scores[0].whole_chain_success)
        self.assertFalse(result.atom_local.metrics.intervention_scores[0].pair_both_correct)
        self.assertFalse(result.atom_local.metrics.canary_matches[0])
        self.assertEqual(result.atom_local.accounting.observed_reservations, 280)
        self.assertEqual(dict(result.atom_local.accounting.dispositions)["ERROR"], 2)

    def test_wrong_typed_actions_are_reportable_misses(self):
        result = self.reduce(atom_local=self.make_run(ATOM_ID, successes=0))
        self.assertTrue(result.reportable)
        self.assertFalse(result.criteria_passed)
        self.assertEqual(result.atom_local.metrics.whole_chains, 0)
        self.assertEqual(result.atom_local.metrics.typed_steps, 8)

    def test_state_slot_seed_and_capture_identity_mutations(self):
        first = self.fitted.reservations[0]
        changes = (
            replace(self.fitted, state_id=BASE_ID),
            replace(self.fitted, stage="BASE"),
            replace(self.fitted, stage="D2"),
            replace(self.fitted, reservations=self.fitted.reservations[:-1]),
            replace(self.fitted, reservations=self.fitted.reservations + (first,)),
            with_row(self.fitted, 1, first),
            with_row(self.fitted, 0, replace(first, seed=first.seed + 1)),
            with_row(self.fitted, 0, replace(first, entry=replace(first.entry, index=False))),
            with_row(self.fitted, 0, replace(first, custody=None)),
            with_row(self.fitted, 0, replace(first, custody=replace(first.custody, state_id="foreign"))),
            with_row(self.fitted, 0, replace(first, custody=replace(first.custody,
                     slot=primitives.chain_slot("D2", 0, 0, 0)))),
        )
        for index, run in enumerate(changes):
            with self.subTest(index=index):
                result = self.assert_nonreportable(run)
                self.assertEqual(result.atom_local.accounting.observed_reservations, len(run.reservations))
        result = self.reduce(master=b"foreign-master")
        self.assertFalse(result.reportable)
        self.assertTrue(result.base.issues)

    def test_capture_order_cardinality_and_unreported_errors(self):
        first = self.fitted.reservations[0]
        capture = first.custody
        for changes in (dict(physical_call=1), dict(physical_call=False), dict(actor_call_index=True),
                        dict(actor_call_index=99), dict(native_records=()),
                        dict(native_records=capture.native_records * 2),
                        dict(actor_error=RuntimeError("hidden failure")),
                        dict(capture_error=RuntimeError("hidden capture failure")),
                        dict(sink_error=RuntimeError("hidden sink failure"))):
            with self.subTest(changes=changes):
                self.assert_nonreportable(with_row(self.fitted, 0, replace(first, custody=replace(capture, **changes))))

    def test_native_generation_and_request_join_cannot_be_flags(self):
        first = self.fitted.reservations[0]
        capture = first.custody
        for changes in (dict(request=replace(capture.request)), dict(generation=generation("STOP")),
                        dict(error=RuntimeError("native failure")), dict(raw="foreign"), dict(raw_bytes=b"foreign")):
            with self.subTest(changes=tuple(changes)):
                native = dict(capture.native_records[0], **changes)
                self.assert_nonreportable(with_row(self.fitted, 0, replace(
                    first, custody=replace(capture, native_records=(native,)))))
        for changes in (dict(seed=capture.request.seed + 1), dict(max_new_tokens=1),
                        dict(context_tokens=True), dict(prefix=self.base.calls[1].request.prefix)):
            with self.subTest(changes=tuple(changes)):
                request = replace(capture.request, **changes)
                native = dict(capture.native_records[0], request=request)
                self.assert_nonreportable(with_row(self.fitted, 0, replace(
                    first, custody=replace(capture, request=request, native_records=(native,)))))

    def test_driver_runs_raw_and_unused_tail_are_checked(self):
        first = self.fitted.reservations[0]
        unused = self.fitted.reservations[28]
        probe_row = self.fitted.reservations[232]
        mutations = (
            replace(self.fitted, chain_runs=self.fitted.chain_runs[:-1]),
            replace(self.fitted, probe_runs=self.fitted.probe_runs + self.fitted.probe_runs[:1]),
            replace(self.fitted, chain_runs=self.fitted.chain_runs[::-1]),
            with_row(self.fitted, 0, replace(first, driver_record=replace(first.driver_record, raw_bytes=b"foreign"))),
            with_row(self.fitted, 232, replace(probe_row, driver_record=replace(probe_row.driver_record, generation_valid=False))),
            with_row(self.fitted, 28, replace(unused, custody=first.custody)),
            with_row(self.fitted, 28, replace(unused, driver_record=first.driver_record)),
            with_row(self.fitted, 279, replace(self.fitted.reservations[279], disposition="UNUSED", custody=None)),
        )
        for index, run in enumerate(mutations):
            with self.subTest(index=index):
                self.assert_nonreportable(run)

    def test_cross_state_reuse_rejected_even_after_relabeling(self):
        baseline = replace(self.fitted, state_id=BASE_ID, reservations=tuple(
            replace(row, custody=replace(row.custody, state_id=BASE_ID)) if row.custody is not None else row
            for row in self.fitted.reservations))
        result = self.reduce(base=baseline)
        self.assertTrue(result.base.reportable)
        self.assertFalse(result.reportable)
        self.assertIn("duplicate_capture_object", result.atom_local.issues[0])

    def test_preexisting_actor_indices_do_not_change_physical_denominator(self):
        result = self.reduce(atom_local=self.make_run(ATOM_ID, actor_offset=7))
        self.assertTrue(result.criteria_passed)
        self.assertEqual(result.atom_local.run.calls[0].actor_call_index, 7)
        self.assertEqual(result.atom_local.run.calls[0].physical_call, 0)

    def test_actor_failure_retains_original_exception_and_all_reservations(self):
        error = RuntimeError("synthetic backend failure")
        failed = self.make_run(ATOM_ID, overrides={0: error})
        result = self.assert_nonreportable(failed)
        self.assertIs(result.atom_local.run.calls[0].actor_error, error)
        self.assertIs(result.atom_local.run.calls[0].native_records[0]["error"], error)
        self.assertEqual(result.atom_local.accounting.physical_calls, 1)
        self.assertEqual(sum(count for _, count in result.atom_local.accounting.dispositions), 280)
        self.assertGreater(result.atom_local.accounting.failures, 0)
        self.assertGreater(dict(result.atom_local.accounting.dispositions)["NOT_REACHED"], 0)
        stripped = replace(failed, failures=(), terminal_reason="completed_unscored")
        self.assert_nonreportable(stripped)

    def test_sink_failures_at_every_boundary_are_retained(self):
        for event_name in ("SCREEN_RESERVED", "CALL_RESERVED", "CALL_CAPTURED", "SCREEN_FINISHED"):
            with self.subTest(event=event_name):
                error = RuntimeError(event_name)

                def sink(event, payload):
                    if event == event_name:
                        raise error

                failed = self.make_run(ATOM_ID, sink=sink)
                result = self.assert_nonreportable(failed)
                self.assertTrue(any(failure.error is error for failure in result.atom_local.run.failures))
                self.assertEqual(result.atom_local.accounting.observed_reservations, 280)

    def test_missing_pre_call_context_not_invented_for_uncalled_slots(self):
        failed = self.make_run(ATOM_ID, counter=lambda prefix: wire.CONTEXT_CAP)
        result = self.assert_nonreportable(failed)
        self.assertEqual(result.atom_local.accounting.physical_calls, 0)
        self.assertGreater(dict(result.atom_local.accounting.dispositions)["NOT_CALLED"], 0)

    def test_invalid_generation_transport_is_nonreportable(self):
        for value in (object(), rollout.Generation("STOP", 1, 2, False, "stop"),
                      rollout.Generation("STOP", 1, 1, False, "abort")):
            with self.subTest(value=value):
                self.assert_nonreportable(self.make_run(ATOM_ID, overrides={0: value}))

    def test_native_receipts_and_green_flags_are_not_admission_inputs(self):
        receipt = custody.ReceiptVerification(BASE_ID, "D1", "completed_unscored", ())
        with self.assertRaisesRegex(ValueError, "live_screen_runs_required"):
            self.reduce(base=receipt)
        with self.assertRaises(TypeError):
            self.reduce(persisted_custody_verified=True)
        with self.assertRaisesRegex(ValueError, "distinct_explicit_state_identities"):
            self.reduce(atom_local_state_id=BASE_ID)
        result = self.reduce(base=self.fitted, atom_local=self.base)
        self.assertFalse(result.reportable)

    def test_baseline_failure_cannot_disappear_behind_a_good_fitted_score(self):
        error = RuntimeError("BASE failure")
        baseline = self.make_run(BASE_ID, overrides={0: error})
        result = self.reduce(base=baseline)
        self.assertFalse(result.reportable)
        self.assertIsNone(result.criteria_passed)
        self.assertTrue(result.atom_local.reportable)
        self.assertIs(result.base.run, baseline)
        self.assertIs(result.base.run.calls[0].actor_error, error)
        self.assertEqual(result.base.accounting.observed_reservations, 280)

    def test_driver_reference_and_exact_slot_type_cannot_be_substituted(self):
        first = self.fitted.reservations[0]
        self.assert_nonreportable(with_row(self.fitted, 0, replace(first, driver_record=replace(first.driver_record))))
        slot = replace(first.driver_record.slot, global_ordinal=False)
        driver = replace(first.driver_record, slot=slot)
        chain = replace(self.fitted.chain_runs[0], calls=(driver,) + self.fitted.chain_runs[0].calls[1:])
        run = replace(with_row(self.fitted, 0, replace(first, driver_record=driver)),
                      chain_runs=(chain,) + self.fitted.chain_runs[1:])
        self.assert_nonreportable(run)

    def test_exact_reduced_bindings_and_public_canary_target_required(self):
        foreign_chains = dict(self.chains, extra=self.chains[0])
        with self.assertRaisesRegex(ValueError, "exact_reduced_chain_bindings"):
            self.reduce(chains=foreign_chains)
        with self.assertRaisesRegex(ValueError, "canary_target_public_prompt_mismatch"):
            self.reduce(canaries=(replace(self.canaries[0], target="STOP"),) + self.canaries[1:])
        with self.assertRaisesRegex(ValueError, "exact_ordered_canary_bindings"):
            self.reduce(canaries=self.canaries[::-1])

    def test_reuses_existing_scorers_without_mutation_or_io(self):
        before = tuple((capture, capture.request, capture.native_records[0], dict(capture.native_records[0]))
                       for run in (self.base, self.fitted) for capture in run.calls)
        with patch.object(scoring, "score_chain", wraps=scoring.score_chain) as chains, \
                patch.object(scoring, "score_intervention_pair", wraps=scoring.score_intervention_pair) as pairs, \
                patch.object(canary_api, "exact_copy_match", wraps=canary_api.exact_copy_match) as canaries, \
                patch("builtins.open", side_effect=AssertionError("no file I/O")):
            self.assertTrue(self.reduce().criteria_passed)
        self.assertEqual((chains.call_count, pairs.call_count, canaries.call_count), (16, 32, 32))
        for capture, request, native, contents in before:
            self.assertIs(capture.request, request)
            self.assertIs(capture.native_records[0], native)
            self.assertEqual(native, contents)


if __name__ == "__main__":
    unittest.main()
