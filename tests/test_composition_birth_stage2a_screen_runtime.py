"""Synthetic held fixtures and callbacks only; no native or material receipt."""

from collections import Counter
from dataclasses import replace
import importlib
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_probe as probe
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_runtime as source
from tests.test_composition_birth_stage2a_actor import SyntheticModel, SyntheticTokenizer, SyntheticTorch
from tests.test_composition_birth_stage2a_held import fixtures


class FakeActor:
    def __init__(self, policy=None):
        self.calls = []
        self.requests = []
        self.policy = policy or (lambda request: rollout.Generation("STOP", 1, 1, False, "stop"))
        self.native_output = SimpleNamespace(unserializable=object())

    def __call__(self, request):
        self.requests.append(request)
        record = dict(request=request, native_output=self.native_output, generation=None, error=None)
        self.calls.append(record)
        try:
            generation = self.policy(request)
            record["generation"] = generation
            return generation
        except BaseException as error:
            record["error"] = error
            raise


class FakeSink:
    def __init__(self, fail_event=None, occurrence=1):
        self.events = []
        self.fail_event = fail_event
        self.occurrence = occurrence
        self.error = RuntimeError("synthetic sink failure after possible partial write")

    def __call__(self, event, payload):
        self.events.append((event, payload))
        if event == self.fail_event:
            self.occurrence -= 1
            if self.occurrence == 0:
                raise self.error


class ScreenRuntimeTests(unittest.TestCase):
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
            for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS
        }
        canary_tokens = {role: token for tokens in fixtures("generic_canary").values()
                         for role, token in tokens.items()}
        cls.canaries = canary_api.build_canaries(role_tokens=canary_tokens)

    def run_fixture(self, actor=None, sink=None, **changes):
        actor = actor or FakeActor()
        sink = sink or FakeSink()
        options = dict(state_id="synthetic-D1-ATOM_LOCAL-attempt-1", stage="D1",
                       master=b"synthetic-reduced-screen", chains=self.chains,
                       interventions=self.interventions, canaries=self.canaries,
                       actor=actor, actor_calls=actor.calls, count_context=lambda prefix: 1,
                       counter_provenance="SYNTHETIC_FIXTURE", custody_sink=sink)
        options.update(changes)
        return source.run_reduced_state(**options), actor, sink

    def test_all_reservations_dispatch_order_and_once_per_driver(self):
        with patch.object(rollout, "run_chain", wraps=rollout.run_chain) as chains, \
                patch.object(probe, "run_probe", wraps=probe.run_probe) as probes:
            result, actor, sink = self.run_fixture()
        roster = screen.reduced_screen("D1")
        self.assertEqual(result.terminal_reason, "completed_unscored")
        self.assertEqual(result.failures, ())
        self.assertEqual(tuple(row.entry for row in result.reservations), roster)
        self.assertEqual(Counter(row.entry.kind for row in result.reservations),
                         {"CHAIN": 232, "INTERVENTION": 32, "CANARY": 16})
        self.assertEqual((chains.call_count, probes.call_count), (8, 48))
        self.assertEqual((len(result.chain_runs), len(result.probe_runs), len(actor.requests)), (8, 48, 56))
        self.assertEqual(Counter(row.disposition for row in result.reservations),
                         {"EXECUTED": 56, "UNUSED": 224})
        called_entries = tuple(roster[index] for index in range(0, 232, 29)) + roster[232:]
        self.assertEqual(tuple(call.slot for call in result.calls), tuple(entry.slot for entry in called_entries))
        self.assertEqual(tuple(call.physical_call for call in result.calls), tuple(range(56)))
        self.assertEqual(tuple(call.actor_call_index for call in result.calls), tuple(range(56)))
        for call, request, native in zip(result.calls, actor.requests, actor.calls):
            self.assertEqual(call.state_id, result.state_id)
            self.assertIs(call.request, request)
            self.assertIs(call.native_records[0], native)
            self.assertIs(call.native_records[0]["native_output"], actor.native_output)
            self.assertIs(call.generation, native["generation"])
            self.assertEqual(call.request.seed, primitives.decode_seed(
                b"synthetic-reduced-screen", call.slot.panel_label, call.slot.global_ordinal))
        self.assertEqual([event for event, _ in sink.events],
                         ["SCREEN_RESERVED"] + ["CALL_RESERVED", "CALL_CAPTURED"] * 56 + ["SCREEN_FINISHED"])
        self.assertEqual(len(sink.events[0][1].reservations), 280)
        self.assertTrue(all(row.custody is None for row in sink.events[0][1].reservations))
        self.assertTrue(all(payload.physical_call is None for event, payload in sink.events if event == "CALL_RESERVED"))

    def test_public_only_projection_and_exact_canary_bytes(self):
        result, actor, _ = self.run_fixture()
        expected = [self.chains[task].public_view("m0").prefix for task in screen.CHAIN_TASKS]
        expected += [self.interventions[(transition, index)].members[member].public_view().prefix
                     for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS
                     for member in range(2)]
        expected += [(held.Message("system", item.system_text), held.Message("user", item.user_text))
                     for item in self.canaries]
        self.assertEqual([request.prefix for request in actor.requests], expected)
        for call in result.calls:
            self.assertIs(type(call.request), rollout.DecodeRequest)
            self.assertEqual(set(vars(call.request)), {"prefix", "seed", "max_new_tokens", "context_tokens"})
            self.assertTrue(all(type(message) is held.Message for message in call.request.prefix))

    def test_chain_adaptive_calls_leave_unused_slots_not_physical_gaps(self):
        def policy(request):
            if len(request.prefix) == 2 and request.prefix[1].content.startswith("TASK\n"):
                task = wire.parse_task(request.prefix[1].content)
                return rollout.Generation("READ INDEX " + task.start, 1, 1, False, "stop")
            return rollout.Generation("STOP", 1, 1, False, "stop")

        result, actor, _ = self.run_fixture(FakeActor(policy))
        self.assertEqual(len(actor.requests), 64)
        for offset in range(0, 232, 29):
            group = result.reservations[offset:offset + 29]
            self.assertEqual([row.disposition for row in group], ["EXECUTED"] * 2 + ["UNUSED"] * 27)
            self.assertIsNone(group[-1].custody)
        self.assertEqual([call.physical_call for call in result.calls], list(range(64)))

    def test_pairing_seeds_do_not_replace_state_identity(self):
        baseline, _, _ = self.run_fixture(state_id="synthetic-BASE-attempt-1")
        fitted, _, _ = self.run_fixture(state_id="synthetic-ATOM_LOCAL-attempt-1")
        self.assertEqual([call.request.seed for call in baseline.calls], [call.request.seed for call in fitted.calls])
        self.assertNotEqual(baseline.calls[0].state_id, fitted.calls[0].state_id)
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        self.assertEqual(fitted.status, "PARTIAL_SOURCE_ONLY")

    def test_explicit_d2_labels_never_schedule_base_or_another_stage(self):
        result, actor, _ = self.run_fixture(stage="D2", state_id="caller-supplied-D2-not-admitted-here")
        self.assertEqual(len(result.reservations), 280)
        self.assertEqual(len(actor.requests), 56)
        self.assertTrue(all(row.entry.slot.panel_label.startswith("D2_") for row in result.reservations))
        self.assertEqual(result.reservations[0].entry.slot.global_ordinal, 1008)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_preexisting_actor_custody_keeps_separate_native_indices(self):
        actor = FakeActor()
        earlier = {"request": object(), "native_output": object()}
        actor.calls.append(earlier)
        result, _, _ = self.run_fixture(actor)
        self.assertIs(actor.calls[0], earlier)
        self.assertEqual([call.physical_call for call in result.calls], list(range(56)))
        self.assertEqual([call.actor_call_index for call in result.calls], list(range(1, 57)))

    def test_frozen_readout_actor_joins_with_synthetic_backend_only(self):
        tokenizer, torch = SyntheticTokenizer(), SyntheticTorch()
        model = SyntheticModel(torch, [ord(character) + 10 for character in "STOP"] + [1])
        actor = actor_api.ReadoutActor(tokenizer=tokenizer, model=model, torch=torch,
                                      device="synthetic-device", count_basis="SYNTHETIC_FIXTURE",
                                      generation_config_factory=SimpleNamespace)
        result, _, _ = self.run_fixture(actor, count_context=actor.count_context)
        self.assertEqual(result.terminal_reason, "completed_unscored")
        self.assertEqual(len(actor.calls), 56)
        for call, native in zip(result.calls, actor.calls):
            self.assertIs(call.native_records[0], native)
            self.assertIs(call.request, native["request"])
            self.assertEqual(call.generation.actual_tokens, 5)
            self.assertEqual(native["generated_ids"][-1], tokenizer.eos_token_id)
        self.assertEqual((torch.cpu_rng, torch.cuda_rngs), (101, [202, 303]))

    def test_actor_failure_retains_original_native_custody_and_aborts_remaining_state(self):
        error = RuntimeError("native decode or validation failed")
        error.native_output = object()

        def policy(request):
            raise error

        result, actor, sink = self.run_fixture(FakeActor(policy))
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertEqual(len(actor.requests), 1)
        self.assertEqual(len(result.reservations), 280)
        self.assertEqual(Counter(row.disposition for row in result.reservations),
                         {"ERROR": 1, "UNUSED": 28, "NOT_REACHED": 251})
        capture = result.calls[0]
        self.assertIs(capture.actor_error, error)
        self.assertIs(capture.native_records[0], actor.calls[0])
        self.assertIs(capture.native_records[0]["error"].native_output, error.native_output)
        self.assertEqual([event for event, _ in sink.events],
                         ["SCREEN_RESERVED", "CALL_RESERVED", "CALL_CAPTURED", "SCREEN_FINISHED"])
        self.assertIs(sink.events[2][1].actor_error, error)

    def test_late_probe_failure_does_not_restart_chains_or_continue_probes(self):
        actor = FakeActor()
        error = RuntimeError("first probe failure")

        def policy(request):
            if len(actor.requests) == 9:
                raise error
            return rollout.Generation("STOP", 1, 1, False, "stop")

        actor.policy = policy
        result, _, _ = self.run_fixture(actor)
        self.assertEqual((len(result.chain_runs), len(result.probe_runs), len(actor.requests)), (8, 1, 9))
        self.assertEqual(result.reservations[232].custody.physical_call, 8)
        self.assertIs(result.reservations[232].custody.actor_error, error)
        self.assertTrue(all(row.disposition == "NOT_REACHED" for row in result.reservations[233:]))

    def test_sink_failures_have_no_retry_or_later_actor_or_sink_invocation(self):
        for event, actual, captures in (("SCREEN_RESERVED", 0, 0), ("CALL_RESERVED", 0, 1),
                                        ("CALL_CAPTURED", 1, 1), ("SCREEN_FINISHED", 56, 56)):
            sink = FakeSink(event)
            result, actor, _ = self.run_fixture(sink=sink)
            with self.subTest(event=event):
                self.assertEqual(result.terminal_reason, "aborted")
                self.assertEqual(len(actor.requests), actual)
                self.assertEqual(len(result.calls), captures)
                self.assertEqual(len(result.reservations), 280)
                self.assertEqual(sink.events[-1][0], event)
                self.assertIs(result.failures[-1].error, sink.error)
                if event in ("CALL_RESERVED", "CALL_CAPTURED"):
                    self.assertIs(result.calls[-1].sink_error, sink.error)
                if event == "CALL_RESERVED":
                    self.assertIsNone(result.calls[0].physical_call)
                    self.assertEqual(result.reservations[0].disposition, "NOT_CALLED")
                    self.assertEqual(result.reservations[0].driver_record.disposition, "ERROR")
                if event == "CALL_CAPTURED":
                    self.assertIs(result.calls[0].native_records[0], actor.calls[0])
                    self.assertEqual(result.calls[0].generation.raw, "STOP")

    def test_simultaneous_actor_and_capture_sink_errors_are_both_preserved(self):
        error = RuntimeError("actor failed first")

        def policy(request):
            raise error

        sink = FakeSink("CALL_CAPTURED")
        result, actor, _ = self.run_fixture(FakeActor(policy), sink)
        self.assertEqual(len(actor.requests), 1)
        self.assertEqual([failure.phase for failure in result.failures], ["actor", "CALL_CAPTURED"])
        self.assertIs(result.calls[0].actor_error, error)
        self.assertIs(result.calls[0].sink_error, sink.error)
        self.assertIs(result.calls[0].native_records[0]["error"], error)

    def test_counter_failure_retains_exception_without_fabricated_actor_call(self):
        error = RuntimeError("synthetic counter error")

        def counter(prefix):
            self.assertTrue(all(type(message) is held.Message for message in prefix))
            raise error

        result, actor, _ = self.run_fixture(count_context=counter)
        self.assertEqual(actor.requests, [])
        self.assertEqual(result.calls, ())
        self.assertIs(result.failures[0].error, error)
        self.assertEqual(result.reservations[0].disposition, "NOT_CALLED")
        self.assertEqual(result.reservations[0].driver_record.error_type, "RuntimeError")

    def test_invalid_counter_values_abort_and_zero_allowance_stays_uncalled(self):
        for value in (-1, True, 16385, object()):
            result, actor, _ = self.run_fixture(count_context=lambda prefix: value)
            with self.subTest(value=value):
                self.assertEqual(result.terminal_reason, "aborted")
                self.assertEqual(actor.requests, [])
                self.assertIs(result.failures[0].error.args[1], value)
        result, actor, _ = self.run_fixture(count_context=lambda prefix: 16384)
        self.assertEqual(result.failures, ())
        self.assertEqual(actor.requests, [])
        self.assertEqual(Counter(row.disposition for row in result.reservations),
                         {"NOT_CALLED": 56, "UNUSED": 224})

    def test_ordinary_wrong_or_length_outcomes_are_preserved_not_repaired(self):
        for generation in (rollout.Generation("STOP\n", 1, 1, False, "stop"),
                           rollout.Generation("STOP", 1, 1, True, "length")):
            result, actor, _ = self.run_fixture(FakeActor(lambda request: generation))
            self.assertEqual(len(actor.requests), 56)
            self.assertEqual(result.terminal_reason, "completed_unscored")
            self.assertEqual(result.failures, ())
            self.assertEqual(result.chain_runs[0].attempts[0].capture.raw_bytes, generation.raw.encode())
            self.assertEqual(result.probe_runs[0].raw_bytes, generation.raw.encode())
            self.assertTrue(all(call.generation is generation for call in result.calls))

    def test_review_intervention_accounting_fault_aborts(self):
        actor = FakeActor()
        invalid = rollout.Generation("STOP", 1, 2, False, "stop")
        actor.policy = lambda request: (invalid if len(actor.requests) == 9
                                        else rollout.Generation("STOP", 1, 1, False, "stop"))
        result, _, _ = self.run_fixture(actor)
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertEqual(len(actor.requests), 9)
        self.assertEqual(result.probe_runs[-1].reason, "invalid_token_accounting")
        self.assertEqual(result.failures[-1].phase, "driver_result")
        self.assertEqual(result.failures[-1].error.args, ("invalid_token_accounting",))
        self.assertTrue(all(row.disposition == "NOT_REACHED" for row in result.reservations[233:]))

    def test_driver_transport_faults_retain_custody_and_abort_each_panel(self):
        valid = rollout.Generation("STOP", 1, 1, False, "stop")
        cases = ((replace(valid, actual_tokens=2), "invalid_token_accounting"),
                 (replace(valid, actual_tokens=True), "invalid_token_accounting"),
                 (replace(valid, actual_tokens=0, declared_tokens=0), "invalid_token_accounting"),
                 (replace(valid, actual_tokens=257, declared_tokens=257), "invalid_token_accounting"),
                 (replace(valid, truncated=1), "invalid_generation_metadata"),
                 (replace(valid, finish_reason=None), "invalid_generation_metadata"),
                 (replace(valid, finish_reason="abort"), "unbound_finish_reason"),
                 (replace(valid, declared_tokens=object()), "unsupported_custody_transport"),
                 (replace(valid, raw=b"STOP"), "invalid_output_transport"),
                 (replace(valid, raw="\ud800"), "invalid_output_transport"))
        for bad_call, index, remaining in ((1, 0, 29), (9, 232, 233), (41, 264, 265)):
            for generation, reason in cases:
                actor = FakeActor()
                actor.policy = lambda request: generation if len(actor.requests) == bad_call else valid
                result, _, sink = self.run_fixture(actor)
                with self.subTest(index=index, reason=reason, generation=generation):
                    self.assertEqual(result.terminal_reason, "aborted")
                    self.assertEqual(len(actor.requests), bad_call)
                    self.assertEqual(len(result.reservations), 280)
                    row = result.reservations[index]
                    self.assertEqual(row.disposition, "ERROR")
                    self.assertEqual(result.failures[-1].phase, "driver_result")
                    self.assertEqual(result.failures[-1].slot, row.entry.slot)
                    self.assertEqual(result.failures[-1].error.args, (reason,))
                    self.assertIs(row.custody.request, actor.requests[-1])
                    self.assertIs(row.custody.generation, generation)
                    self.assertIs(row.custody.native_records[0], actor.calls[-1])
                    self.assertIs(row.custody.native_records[0]["native_output"], actor.native_output)
                    self.assertIs(row.driver_record.request, actor.requests[-1])
                    self.assertEqual(row.driver_record.raw_bytes, wire._raw_bytes(generation.raw))
                    self.assertTrue(all(item.disposition == "NOT_REACHED"
                                        for item in result.reservations[remaining:]))
                    if index == 0:
                        self.assertIs(row.driver_record, result.chain_runs[-1].calls[0])
                        expected = "malformed_action" if reason == "invalid_output_transport" else reason
                        self.assertEqual(result.chain_runs[-1].terminal_reason, expected)
                        self.assertTrue(all(item.disposition == "UNUSED"
                                            for item in result.reservations[1:29]))
                    else:
                        self.assertIs(row.driver_record, result.probe_runs[-1])
                        self.assertEqual(row.driver_record.reason, reason)
                    captured = [payload for event, payload in sink.events if event == "CALL_CAPTURED"]
                    self.assertIs(captured[-1].generation, generation)
                    self.assertIs(captured[-1].native_records[0], actor.calls[-1])
                    self.assertEqual(sink.events[-1][0], "SCREEN_FINISHED")
                    self.assertEqual(sink.events[-1][1].terminal_reason, "aborted")

    def test_late_chain_transport_fault_is_bound_to_exact_last_called_slot(self):
        actor = FakeActor()
        invalid = rollout.Generation("STOP", 1, 2, False, "stop")

        def policy(request):
            if len(actor.requests) == 1:
                task = wire.parse_task(request.prefix[1].content)
                return rollout.Generation("READ INDEX " + task.start, 1, 1, False, "stop")
            return invalid

        actor.policy = policy
        result, _, _ = self.run_fixture(actor)
        self.assertEqual(result.terminal_reason, "aborted")
        self.assertEqual(len(actor.requests), 2)
        self.assertEqual(result.reservations[0].disposition, "EXECUTED")
        self.assertEqual(result.reservations[1].disposition, "ERROR")
        self.assertEqual(result.failures[-1].slot, result.reservations[1].entry.slot)
        self.assertIs(result.reservations[1].custody.generation, invalid)
        self.assertIs(result.reservations[1].driver_record, result.chain_runs[0].calls[1])
        self.assertEqual(result.reservations[1].custody.physical_call, 1)
        self.assertTrue(all(row.disposition == "UNUSED" for row in result.reservations[2:29]))
        self.assertTrue(all(row.disposition == "NOT_REACHED" for row in result.reservations[29:]))

    def test_early_action_or_length_reason_cannot_hide_invalid_transport(self):
        cases = ((rollout.Generation("STOP\n", 1, 2, False, "stop"), "invalid_token_accounting"),
                 (rollout.Generation("STOP\n", 1, 1, 1, "stop"), "invalid_generation_metadata"),
                 (rollout.Generation("STOP\n", 1, 1, False, "abort"), "unbound_finish_reason"),
                 (rollout.Generation("STOP", 257, 257, True, "length"), "invalid_token_accounting"))
        for generation, reason in cases:
            result, actor, _ = self.run_fixture(FakeActor(lambda request: generation))
            with self.subTest(generation=generation):
                self.assertEqual(result.terminal_reason, "aborted")
                self.assertEqual(len(actor.requests), 1)
                self.assertEqual(result.failures[-1].error.args, (reason,))
                self.assertEqual(result.chain_runs[0].terminal_reason,
                                 "length_limited" if generation.truncated is True else "malformed_action")
                self.assertEqual(result.chain_runs[0].attempts[0].capture.raw_bytes, generation.raw.encode())
                self.assertIs(result.calls[0].generation, generation)

    def test_bad_generation_object_preserved_before_transport_validation(self):
        raw = object()
        result, actor, sink = self.run_fixture(FakeActor(lambda request: raw))
        self.assertEqual(len(actor.requests), 1)
        self.assertIs(result.calls[0].generation, raw)
        self.assertIs(result.calls[0].native_records[0]["generation"], raw)
        self.assertIs(sink.events[2][1].generation, raw)
        self.assertIn("invalid_generation_transport", str(result.calls[0].capture_error))

    def test_missing_extra_wrong_or_reused_actor_custody_aborts_with_raw_retained(self):
        for mode in ("missing", "extra", "wrong_request", "reuse", "clear_prefix"):
            actor = FakeActor()
            earlier = {"request": object(), "native_output": object()}
            actor.calls.append(earlier)

            def policy(request):
                if mode == "missing":
                    actor.calls.pop()
                elif mode == "extra":
                    actor.calls.append({"request": request, "native_output": object()})
                elif mode == "wrong_request":
                    actor.calls[-1]["request"] = replace(request)
                elif mode == "reuse":
                    earlier["request"] = request
                    actor.calls[-1] = earlier
                else:
                    del actor.calls[0]
                return rollout.Generation("STOP", 1, 1, False, "stop")

            actor.policy = policy
            result, _, _ = self.run_fixture(actor)
            with self.subTest(mode=mode):
                self.assertEqual(len(actor.requests), 1)
                self.assertIsNotNone(result.calls[0].capture_error)
                self.assertEqual(result.terminal_reason, "aborted")
                if mode in ("extra", "wrong_request", "reuse", "clear_prefix"):
                    self.assertIs(result.calls[0].native_records[-1], actor.calls[-1])

    def test_custody_drift_in_reservation_sink_blocks_native_entry(self):
        actor = FakeActor()

        def sink(event, payload):
            if event == "CALL_RESERVED":
                actor.calls.append({"request": object(), "native_output": object()})

        result, _, _ = self.run_fixture(actor, sink)
        self.assertEqual(actor.requests, [])
        self.assertIsNone(result.calls[0].physical_call)
        self.assertIs(result.calls[0].native_records[0], actor.calls[0])
        self.assertIn("changed_outside_call", str(result.calls[0].capture_error))

    def test_incorrect_duplicate_missing_or_extra_object_bindings_rejected_before_callbacks(self):
        bad_chains = dict(self.chains)
        bad_chains[4] = self.chains[0]
        missing_chains = dict(self.chains)
        del missing_chains[0]
        bad_pairs = dict(self.interventions)
        bad_pairs[("SEEK", 2)] = self.interventions[("SEEK", 0)]
        reversed_members = dict(self.interventions)
        pair = self.interventions[("CHECK", 0)]
        reversed_members[("CHECK", 0)] = replace(pair, members=pair.members[::-1])
        changes = (dict(chains=bad_chains), dict(chains=missing_chains),
                   dict(chains={**self.chains, 2: self.chains[0]}),
                   dict(interventions=bad_pairs), dict(interventions=reversed_members),
                   dict(canaries=self.canaries[:-1]), dict(canaries=self.canaries[::-1]),
                   dict(canaries=(self.canaries[0],) * 16), dict(state_id=""),
                   dict(counter_provenance=""), dict(stage="BASE"), dict(master=b""),
                   dict(actor_calls=()), dict(custody_sink=None))
        for change in changes:
            actor, sink = FakeActor(), FakeSink()
            with self.subTest(change=tuple(change)), self.assertRaises(ValueError):
                self.run_fixture(actor, sink, **change)
            self.assertEqual(actor.requests, [])
            self.assertEqual(sink.events, [])

    def test_driver_projection_error_is_retained_without_calling_that_slot(self):
        canaries = (replace(self.canaries[0], user_text="invalid\0public"),) + self.canaries[1:]
        result, actor, _ = self.run_fixture(canaries=canaries)
        self.assertEqual(len(actor.requests), 40)
        self.assertEqual(result.reservations[264].disposition, "NOT_CALLED")
        self.assertEqual(result.failures[-1].phase, "driver")
        self.assertIsNone(result.reservations[264].custody)

    def test_baseexception_is_retained_and_capture_finally_still_runs(self):
        error = KeyboardInterrupt("synthetic interruption, never a real process signal")

        def policy(request):
            raise error

        result, actor, sink = self.run_fixture(FakeActor(policy))
        self.assertEqual(len(actor.requests), 1)
        self.assertIs(result.calls[0].actor_error, error)
        self.assertIs(sink.events[2][1].actor_error, error)
        self.assertEqual(result.terminal_reason, "aborted")

    def test_no_native_import_load_io_or_processes(self):
        with patch.dict(sys.modules, {"torch": None, "transformers": None, "peft": None}):
            importlib.reload(source)
            with patch("builtins.open", side_effect=AssertionError("no files")), \
                    patch("socket.socket", side_effect=AssertionError("no network")), \
                    patch("subprocess.Popen", side_effect=AssertionError("no processes")):
                result, _, _ = self.run_fixture()
        self.assertEqual(result.terminal_reason, "completed_unscored")


if __name__ == "__main__":
    unittest.main()
