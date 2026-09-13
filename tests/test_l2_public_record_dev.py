"""Scripted source-only fixtures, never native tokenization or learning proof."""
from collections import Counter
from dataclasses import asdict, replace
import inspect
import json
import unittest

from organism_v6 import l2_public_record_dev as core


BASE = "b" * 64
FIRST = "c" * 64


def captured(world, block=1, lineage="SHARED", record_fn=None, action_fn=None):
    public = core.public_view(world)
    episodes = []
    for slot in public.slots[(block - 1) * 8:block * 8]:
        raw = (action_fn(slot) if action_fn else public.actions[slot.index % 2].encode())
        action = core.make_receipt(public, slot.slot_id, "action", raw,
                                   sequence=block * 100 + (slot.index % 8) * 3, lineage=lineage)
        try:
            outcome = core.feedback(world, action, sequence=action.sequence + 1)
        except core.IntegrityError:
            episodes.append(core.Episode(action))
            continue
        selected = raw.rstrip(b"\n").decode()
        supported = selected if outcome.raw == b"SUCCESS" else next(
            choice for choice in public.actions if choice != selected)
        target = record_fn(slot, supported) if record_fn else supported.encode()
        record = (core.make_receipt(public, slot.slot_id, "record", target,
                                    sequence=action.sequence + 2, lineage=lineage, previous=outcome)
                  if target is not None else None)
        episodes.append(core.Episode(action, outcome, record))
    return core.capture_block(public, block, lineage, tuple(episodes))


def compile_one(public, capture):
    return core.compile_corpus(public, (capture,), expected_hashes=(core.digest(capture),))


class PublicRecordTests(unittest.TestCase):
    def setUp(self):
        self.world = core.build_world(501, 991)
        self.public = core.public_view(self.world)
        self.capture = captured(self.world)
        self.corpus = compile_one(self.public, self.capture)

    def first_sleep(self):
        states = core.start_pair(self.public, BASE)
        for policy, state in states.items():
            closed = core.close_block(self.public, state, self.capture,
                                      expected_sha256=core.digest(self.capture))
            states[policy] = core.complete_sleep(
                self.public, closed, corpus_sha256=core.digest(closed.corpus),
                candidate_sha256=FIRST, initialized_from_sha256=BASE)
        core.check_pair(self.public, states)
        return states

    def final_states(self):
        states = self.first_sleep()
        for policy, state in states.items():
            second = captured(self.world, 2, policy)
            closed = core.close_block(self.public, state, second, expected_sha256=core.digest(second))
            states[policy] = core.complete_sleep(
                self.public, closed, corpus_sha256=core.digest(closed.corpus),
                candidate_sha256=("d" if policy == "PROMOTE" else "e") * 64,
                initialized_from_sha256=BASE)
        return states

    def readouts(self, policy, correct=16):
        records = []
        for slot, expected in zip(self.public.slots, self.world.success_actions):
            action = expected if slot.index < correct else next(
                item for item in self.public.actions if item != expected)
            records.append(core.make_receipt(self.public, slot.slot_id, "readout", action.encode(),
                                             sequence=1000 + slot.index, lineage=policy))
        return tuple(records)

    def test_deterministic_fresh_vocabulary_fixed16_balanced8plus8(self):
        self.assertEqual(self.world, core.build_world(501, 991))
        other = core.build_world(502, 991)
        self.assertNotEqual(self.public.root_id, other.public.root_id)
        self.assertTrue(set(self.public.actions).isdisjoint(other.public.actions))
        self.assertEqual([slot.block for slot in self.public.slots], [1] * 8 + [2] * 8)
        for start in (0, 8):
            self.assertEqual(Counter(self.world.success_actions[start:start + 8]),
                             dict.fromkeys(self.public.actions, 4))

    def test_public_views_and_prompts_are_truth_seed_independent(self):
        other = core.build_world(501, 992)
        self.assertNotEqual(self.world.success_actions, other.success_actions)
        self.assertEqual(self.public, core.public_view(other))
        self.assertEqual(set(asdict(self.public)), {"root_id", "actions", "slots", "law"})
        for slot in self.public.slots:
            self.assertEqual(core.action_prompt(self.public, slot.slot_id),
                             core.action_prompt(other.public, slot.slot_id))
        for seed in (-1, True, 2**32):
            with self.assertRaises(core.IntegrityError):
                core.build_world(seed, 1)

    def test_world_truth_is_not_an_input_to_compiler(self):
        self.assertEqual(list(inspect.signature(core.compile_corpus).parameters),
                         ["public", "captures", "expected_hashes"])
        with self.assertRaises(core.IntegrityError):
            core.compile_corpus(self.world, (self.capture,), expected_hashes=(core.digest(self.capture),))
        self.assertEqual(self.corpus, compile_one(core.public_view(core.build_world(501, 123)), self.capture))

    def test_feedback_matches_private_world_and_links_raw_action(self):
        for episode in self.capture.episodes:
            slot = next(slot for slot in self.public.slots if slot.slot_id == episode.action.slot_id)
            expected = self.world.success_actions[slot.index].encode()
            self.assertEqual(episode.outcome.raw, b"SUCCESS" if episode.action.raw == expected else b"FAILURE")
            self.assertEqual(episode.outcome.previous_sha256, episode.action.sha256)
            self.assertEqual(episode.record.previous_sha256, episode.outcome.sha256)

    def test_failure_other_action_is_child_authored_not_compiler_synthesized(self):
        failures = [episode for episode in self.capture.episodes if episode.outcome.raw == b"FAILURE"]
        self.assertTrue(failures)
        for episode in failures:
            row = next(row for row in self.corpus.rows if row.slot_id == episode.action.slot_id)
            self.assertNotEqual(row.target, episode.action.raw)
            self.assertEqual(row.target, episode.record.raw)
        missing = captured(self.world, record_fn=lambda slot, supported: None)
        corpus = compile_one(self.public, missing)
        self.assertEqual(corpus.rows, ())
        self.assertEqual(len(corpus.rejected), 8)

    def test_public_two_action_law_cannot_be_removed(self):
        changed = replace(self.public, law="Outcomes need not determine future success.")
        with self.assertRaises(core.IntegrityError):
            compile_one(changed, self.capture)

    def test_unsupported_child_target_rejected_without_repair(self):
        bad = captured(self.world, record_fn=lambda slot, supported: next(
            action for action in self.public.actions if action != supported).encode())
        corpus = compile_one(self.public, bad)
        self.assertEqual(corpus.rows, ())
        self.assertEqual({item.reason for item in corpus.rejected}, {"UNSUPPORTED_RECORD"})

    def test_exact_bytes_preserved_optional_newline_not_canonicalized(self):
        source = captured(self.world, record_fn=lambda slot, supported: supported.encode() + b"\n")
        corpus = compile_one(self.public, source)
        items = core.training_items(self.public, corpus, expected_sha256=core.digest(corpus))
        for episode, row, item in zip(source.episodes, corpus.rows, items):
            self.assertEqual(row.target, episode.record.raw)
            self.assertEqual(item["spans"][1][0].encode(), episode.record.raw)
            self.assertEqual(item["meta"]["target_byte_span"], [0, len(episode.record.raw)])
            self.assertFalse(item["meta"]["native_tokenization_verified"])
        for decoration in (b" ", b"\r\n", b"\n\n"):
            bad = captured(self.world, record_fn=lambda slot, supported: supported.encode() + decoration)
            self.assertEqual(compile_one(self.public, bad).rows, ())

    def test_no_parent_or_outcome_bytes_in_training_items(self):
        items = core.training_items(self.public, self.corpus, expected_sha256=core.digest(self.corpus))
        for item in items:
            self.assertEqual([span[1] for span in item["spans"]], [False, True])
            self.assertNotIn(core.PROCESS_TAPE, item["spans"][0][0])
            self.assertNotIn("Public outcome:", item["spans"][0][0])
            self.assertNotIn(core.PROCESS_TAPE, item["spans"][1][0])
        bad = captured(self.world, record_fn=lambda slot, supported: core.PROCESS_TAPE.encode())
        self.assertEqual(compile_one(self.public, bad).rows, ())

    def test_process_tape_sees_only_public_current_event(self):
        episode = self.capture.episodes[0]
        prompt = core.process_prompt(self.public, episode.action, episode.outcome)
        self.assertTrue(prompt.endswith(core.PROCESS_TAPE))
        self.assertIn(episode.action.raw.decode(), prompt)
        self.assertIn(episode.outcome.raw.decode(), prompt)
        self.assertNotIn("PROMOTE", prompt)
        self.assertNotIn("SHADOW", prompt)
        self.assertNotIn("truth_seed", prompt)

    def test_invalid_action_and_missing_record_preserve_rejection_slots(self):
        source = captured(self.world, action_fn=lambda slot: b"unknown")
        corpus = compile_one(self.public, source)
        self.assertEqual(len(corpus.rejected), 8)
        self.assertEqual({row.reason for row in corpus.rejected}, {"INVALID_ACTION"})
        with self.assertRaises(core.IntegrityError):
            core.feedback(self.world, source.episodes[0].action, sequence=999)

    def test_raw_tampering_and_external_reseal_mismatch_rejected(self):
        episode = self.capture.episodes[0]
        bad = replace(episode, record=replace(episode.record, raw=b"changed"))
        changed = replace(self.capture, episodes=(bad,) + self.capture.episodes[1:])
        with self.assertRaisesRegex(core.IntegrityError, "external capture hash"):
            core.compile_corpus(self.public, (changed,), expected_hashes=(core.digest(self.capture),))
        with self.assertRaisesRegex(core.IntegrityError, "raw receipt hash"):
            compile_one(self.public, changed)

    def test_cross_root_cross_slot_and_branch_links_rejected(self):
        other = captured(core.build_world(999, 991))
        with self.assertRaises(core.IntegrityError):
            compile_one(self.public, other)
        first, second = self.capture.episodes[:2]
        with self.assertRaises(core.IntegrityError):
            core.make_receipt(self.public, first.action.slot_id, "record", first.record.raw,
                              sequence=999, lineage="SHARED", previous=second.outcome)
        with self.assertRaises(core.IntegrityError):
            core.make_receipt(self.public, first.action.slot_id, "record", first.record.raw,
                              sequence=999, lineage="PROMOTE", previous=first.outcome)

    def test_chronology_phase_and_missing_or_extra_slot_rejected(self):
        episode = self.capture.episodes[0]
        with self.assertRaises(core.IntegrityError):
            core.make_receipt(self.public, episode.action.slot_id, "record", episode.record.raw,
                              sequence=episode.outcome.sequence, lineage="SHARED", previous=episode.outcome)
        with self.assertRaises(core.IntegrityError):
            core.make_receipt(self.public, episode.action.slot_id, "record", episode.record.raw,
                              sequence=999, lineage="SHARED", previous=episode.action)
        for episodes in (self.capture.episodes[:-1], self.capture.episodes + (episode,),
                         tuple(reversed(self.capture.episodes))):
            with self.assertRaises(core.IntegrityError):
                core.capture_block(self.public, 1, "SHARED", episodes)

    def test_corpus_rows_cannot_be_fabricated_even_with_new_object_hash(self):
        changed = replace(self.corpus, rows=(replace(self.corpus.rows[0], target=b"invented"),) + self.corpus.rows[1:])
        with self.assertRaises(core.IntegrityError):
            core.training_items(self.public, changed, expected_sha256=core.digest(changed))

    def test_misbound_preserves_target_multiset_and_marks_effectiveness(self):
        control = core.misbind_corpus(self.public, self.corpus, expected_sha256=core.digest(self.corpus))
        self.assertEqual(control.kind, "MISBOUND")
        self.assertEqual(Counter(row.target for row in control.rows), Counter(row.target for row in self.corpus.rows))
        self.assertEqual([row.prompt for row in control.rows], [row.prompt for row in self.corpus.rows])
        self.assertTrue(all(row.source_slot_id != row.slot_id for row in control.rows))
        self.assertEqual(control.changed_targets, sum(left.action != right.action for left, right in
                                                      zip(control.rows, self.corpus.rows)))
        self.assertEqual(control.no_op, control.changed_targets == 0)
        self.assertTrue(all(item["meta"]["corpus_kind"] == "MISBOUND" for item in
                            core.training_items(self.public, control, expected_sha256=core.digest(control))))

    def test_misbound_noop_when_all_admitted_actions_same_even_if_bytes_differ(self):
        first = self.public.actions[0]
        source = captured(self.world, record_fn=lambda slot, supported:
                          first.encode() + (b"\n" if slot.index % 2 else b""))
        corpus = compile_one(self.public, source)
        self.assertEqual(len(corpus.rows), 4)
        control = core.misbind_corpus(self.public, corpus, expected_sha256=core.digest(corpus))
        self.assertTrue(control.no_op)
        self.assertEqual(control.changed_targets, 0)

    def test_shared_first_candidate_shadow_routing_and_immutable_input_state(self):
        start = core.start_pair(self.public, BASE)
        states = self.first_sleep()
        self.assertEqual(start["PROMOTE"].phase, "AWAIT_BLOCK_1")
        self.assertEqual(core.routing(states["PROMOTE"])["requested_artifact_sha256"], FIRST)
        self.assertEqual(core.routing(states["SHADOW"])["requested_artifact_sha256"], BASE)
        self.assertFalse(core.routing(states["PROMOTE"])["native_verified"])
        altered = replace(states["SHADOW"], sleeps=(replace(states["SHADOW"].sleeps[0], candidate_sha256="a" * 64),))
        with self.assertRaisesRegex(core.IntegrityError, "first candidate"):
            core.check_pair(self.public, dict(states, SHADOW=altered))

    def test_cumulative_second_corpus_own_branch_not_other_branch(self):
        states = self.first_sleep()
        promote = captured(self.world, 2, "PROMOTE")
        shadow = captured(self.world, 2, "SHADOW", record_fn=lambda slot, supported:
                          None if slot.index == 8 else supported.encode())
        closed = core.close_block(self.public, states["PROMOTE"], promote, expected_sha256=core.digest(promote))
        other = core.close_block(self.public, states["SHADOW"], shadow, expected_sha256=core.digest(shadow))
        self.assertEqual(len(closed.corpus.rows), 16)
        self.assertEqual(len(other.corpus.rows), 15)
        self.assertEqual(closed.corpus.rows[:8], self.corpus.rows)
        self.assertEqual(other.corpus.rows[:8], self.corpus.rows)
        with self.assertRaises(core.IntegrityError):
            core.close_block(self.public, states["PROMOTE"], shadow, expected_sha256=core.digest(shadow))
        with self.assertRaises(core.IntegrityError):
            core.complete_sleep(self.public, closed, corpus_sha256=core.digest(closed.corpus),
                                candidate_sha256="d" * 64, initialized_from_sha256=FIRST)

    def test_two_sleep_cap_no_skipped_phase_no_misbound_ancestry(self):
        states = self.final_states()
        core.check_pair(self.public, states)
        for policy in core.POLICIES:
            self.assertEqual(states[policy].phase, "COMPLETE")
            with self.assertRaises(core.IntegrityError):
                core.close_block(self.public, states[policy], self.capture, expected_sha256=core.digest(self.capture))
        forged = replace(core.start_pair(self.public, BASE)["PROMOTE"], phase="COMPLETE")
        with self.assertRaises(core.IntegrityError):
            core.check_pair(self.public, dict(states, PROMOTE=forged))
        control = core.misbind_corpus(self.public, self.corpus, expected_sha256=core.digest(self.corpus))
        forged = replace(states["PROMOTE"], corpus=control)
        with self.assertRaises(core.IntegrityError):
            core.check_pair(self.public, dict(states, PROMOTE=forged))

    def test_empty_corpus_no_fabricated_fit_and_shortage_not_endpoint(self):
        empty = captured(self.world, record_fn=lambda slot, supported: None)
        states = core.start_pair(self.public, BASE)
        for policy, state in states.items():
            closed = core.close_block(self.public, state, empty, expected_sha256=core.digest(empty))
            with self.assertRaises(core.IntegrityError):
                core.complete_sleep(self.public, closed, corpus_sha256=core.digest(closed.corpus),
                                    candidate_sha256=FIRST, initialized_from_sha256=BASE)
            states[policy] = core.complete_sleep(self.public, closed, corpus_sha256=core.digest(closed.corpus),
                                                 candidate_sha256=None, initialized_from_sha256=BASE)
        result = core.reduce_pair(self.world, states, dict.fromkeys(core.POLICIES, (None,) * 16))
        self.assertFalse(result["endpoint_evaluable"])
        self.assertIsNone(result["cells"]["PROMOTE"]["accuracy"])

    def test_scripted_mount_changes_second_wake_source_material(self):
        states = self.first_sleep()
        captures = {}
        for policy, state in states.items():
            mounted = core.routing(state)["requested_artifact_sha256"] == FIRST
            captures[policy] = captured(self.world, 2, policy,
                                        action_fn=lambda slot: self.public.actions[int(mounted)].encode())
        first, second = (captures[policy].episodes[0] for policy in core.POLICIES)
        self.assertNotEqual(first.action.raw, second.action.raw)
        self.assertNotEqual(first.outcome.raw, second.outcome.raw)
        self.assertNotEqual(core.digest(captures["PROMOTE"]), core.digest(captures["SHADOW"]))

    def test_descriptive_reducer_counts_fixed_denominators_without_science_pass(self):
        states = self.final_states()
        result = core.reduce_pair(self.world, states,
                                  {"PROMOTE": self.readouts("PROMOTE", 12), "SHADOW": self.readouts("SHADOW", 8)})
        self.assertEqual(result["paired"], dict(promote_only=4, shadow_only=0, both=8, neither=4, total=16, net=4))
        self.assertTrue(result["endpoint_evaluable"])
        self.assertIsNone(result["scientific_pass"])
        self.assertFalse(result["native_verified"])

    def test_reducer_missing_invalid_and_wrong_root_outputs(self):
        states = self.final_states()
        promote = list(self.readouts("PROMOTE"))
        promote[0] = None
        promote[1] = core.make_receipt(self.public, self.public.slots[1].slot_id, "readout", b"extra prose",
                                      sequence=1001, lineage="PROMOTE")
        reports = {"PROMOTE": tuple(promote), "SHADOW": self.readouts("SHADOW")}
        result = core.reduce_pair(self.world, states, reports)
        self.assertEqual(result["cells"]["PROMOTE"]["observed_correct"], 14)
        self.assertEqual(result["cells"]["PROMOTE"]["missing"], 1)
        self.assertIsNone(result["cells"]["PROMOTE"]["accuracy"])
        bad = replace(reports["SHADOW"][0], root_id=core.build_world(8, 9).public.root_id)
        with self.assertRaises(core.IntegrityError):
            core.reduce_pair(self.world, states, dict(reports, SHADOW=(bad,) + reports["SHADOW"][1:]))

    def test_reducer_rejects_stale_and_out_of_order_readouts(self):
        states = self.final_states()
        reports = {policy: self.readouts(policy) for policy in core.POLICIES}
        stale = core.make_receipt(self.public, self.public.slots[0].slot_id, "readout",
                                 self.world.success_actions[0].encode(), sequence=1, lineage="PROMOTE")
        with self.assertRaises(core.IntegrityError):
            core.reduce_pair(self.world, states, dict(reports, PROMOTE=(stale,) + reports["PROMOTE"][1:]))

    def test_json_wire_roundtrip_world_capture_corpus_pair_and_export(self):
        values = (self.world, self.public, self.capture, self.corpus, self.final_states(),
                  core.training_items(self.public, self.corpus, expected_sha256=core.digest(self.corpus)))
        for value in values:
            restored = core.from_data(json.loads(json.dumps(core.to_data(value))), expected_type=type(value))
            self.assertEqual(restored, value)
            self.assertEqual(core.digest(restored), core.digest(value))
        pair = core.from_data(json.loads(json.dumps(core.to_data(self.final_states()))), expected_type=dict)
        core.check_pair(self.public, pair)
        capture = core.from_data(core.to_data(self.capture), expected_type=core.CapturedBlock)
        self.assertIsInstance(capture.episodes, tuple)
        self.assertIsInstance(capture.episodes[0].action.raw, bytes)

    def test_wire_rejects_unknown_class_extra_fields_bad_bytes_and_duplicate_keys(self):
        payload = core.to_data(self.capture)
        payload["value"]["record"] = "NativeModel"
        with self.assertRaises(core.IntegrityError):
            core.from_data(payload)
        payload = core.to_data(self.public)
        payload["value"]["fields"]["success_actions"] = core.to_data(self.world.success_actions)["value"]
        with self.assertRaises(core.IntegrityError):
            core.from_data(payload)
        for value in ({"bytes": "zz"}, {"dict": [["same", 1], ["same", 2]]}):
            with self.assertRaises(core.IntegrityError):
                core.from_data(dict(schema=core.SCHEMA, wire_version=1, value=value))
        with self.assertRaises(core.IntegrityError):
            core.from_data(core.to_data(self.capture), expected_type=core.LoopState)

    def test_misbound_has_no_live_state_policy(self):
        states = core.start_pair(self.public, BASE)
        self.assertEqual(set(states), {"PROMOTE", "SHADOW"})
        forged = replace(states["PROMOTE"], policy="MISBOUND")
        with self.assertRaises(core.IntegrityError):
            core.check_pair(self.public, dict(states, PROMOTE=forged))


if __name__ == "__main__":
    unittest.main()
