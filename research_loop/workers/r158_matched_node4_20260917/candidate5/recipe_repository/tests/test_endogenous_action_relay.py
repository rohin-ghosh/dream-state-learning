"""Synthetic CPU fixtures only: no Q0 inputs and no native-model evidence."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import unittest
from unittest.mock import Mock

from organism_v6 import endogenous_action_relay as relay


def receipt(name, sequence, raw):
    return relay.Receipt(name, sequence, raw, sha256(raw).hexdigest())


def fixture():
    keys = tuple(f"fixture_key_{index}".encode() for index in range(8))
    modes = (b"M0", b"M1")
    views = tuple(f"fixture_view_{index}".encode() for index in range(8))
    objects = tuple(f"fixture_source_{index}".encode() for index in range(16))
    surfaces, blocks = [], []
    for key_index, key in enumerate(keys):
        executions, lines = [], []
        for mode_index, mode in enumerate(modes):
            supported = relay.ACTIONS[(key_index % 2) ^ mode_index]
            executed = relay.ACTIONS[0]
            commit = receipt(f"fixture_exec_{key_index}_{mode_index}".encode(),
                             key_index * 5 + mode_index * 2 + 1, b"ACT: " + executed)
            outcome = receipt(f"fixture_outcome_{key_index}_{mode_index}".encode(),
                              commit.sequence + 1, b"SUCCESS" if supported == executed else b"FAILURE")
            executions.append(relay.Execution(key, mode, objects[key_index * 2 + mode_index],
                                               executed, commit, outcome))
            lines.append(b"WHEN: " + mode + b"  ACT: " + supported + b"  EVIDENCE: " + commit.receipt_id)
        raw = b"DREAM: STORE\nKEY: " + key + b"\n" + b"\n".join(lines)
        dream = receipt(f"fixture_dream_{key_index}".encode(), key_index * 5 + 5, raw)
        blocks.append(relay.Block(key, tuple(executions), dream))
        for view_index, view in enumerate(views):
            object_id = f"fixture_train_{key_index}_{view_index}".encode()
            for mode in modes:
                prefix = b"KEY: " + key + b"\nMODE: " + mode + b"\nOBJECT: " + object_id + b"\nVIEW: " + view + b"\nACT: -"
                key_start, mode_start = prefix.index(key), prefix.index(mode)
                surfaces.append(relay.Surface(key, mode, view, object_id, prefix,
                                               (key_start, key_start + len(key)),
                                               (mode_start, mode_start + len(mode))))
    material = relay.Material(b"synthetic_fixture_not_a_fresh_root", 0, 0, keys, modes,
                              tuple(zip(keys[::2], keys[1::2])), views, objects, tuple(surfaces))
    return material, tuple(blocks)


def synthetic_encode(raw):
    tokens = []
    offset = 0
    while offset < len(raw):
        if raw[offset:offset + 2] in (b"M0", b"M1"):
            tokens.append(1000 + int(raw[offset + 1:offset + 2]))
            offset += 2
        else:
            tokens.append(raw[offset])
            offset += 1
    return tuple(tokens)


def synthetic_collate(rows):
    lengths = [len(row.prefix_ids) + len(row.target_ids) for row in rows]
    width = max(lengths)
    return relay.BatchShape(
        tuple((1,) * length + (0,) * (width - length) for length in lengths),
        tuple(tuple(range(length)) + (0,) * (width - length) for length in lengths),
        tuple(tuple(range(len(row.prefix_ids), length)) for row, length in zip(rows, lengths)),
    )


class EndogenousActionRelayTests(unittest.TestCase):
    def setUp(self):
        self.material, self.blocks = fixture()
        self.material_hash = relay.digest(self.material)
        self.source_hash = relay.digest(self.blocks)
        self.replay = self.build()
        self.replay_hash = relay.digest(self.replay)

    def build(self, blocks=None, material=None, source_hash=None):
        blocks = self.blocks if blocks is None else blocks
        material = self.material if material is None else material
        return relay.build_replay(material, blocks, expected_material_sha256=relay.digest(material),
                                  expected_source_sha256=relay.digest(blocks) if source_hash is None else source_hash)

    def edit_dream(self, transform, index=0, rehash=True):
        block = self.blocks[index]
        raw = transform(block.dream.raw)
        dream = replace(block.dream, raw=raw,
                        raw_sha256=sha256(raw).hexdigest() if rehash else block.dream.raw_sha256)
        return self.blocks[:index] + (replace(block, dream=dream),) + self.blocks[index + 1:]

    def edit_execution(self, transform, block_index=0, execution_index=0):
        block = self.blocks[block_index]
        executions = list(block.executions)
        executions[execution_index] = transform(executions[execution_index])
        return self.blocks[:block_index] + (replace(block, executions=tuple(executions)),) + self.blocks[block_index + 1:]

    def assert_shortage(self, blocks, reason=None, source_hash=None):
        result = self.build(blocks, source_hash=source_hash)
        self.assertEqual(result.status, relay.SHORTAGE)
        self.assertEqual(result.fits_performed, 0)
        self.assertEqual((result.auth_quartets, result.swap_quartets, result.schedule, result.controls), ((), (), (), ()))
        if reason:
            self.assertIn(reason, " ".join(result.formation.reasons))
        return result

    def native(self, replay=None, encode=synthetic_encode, collate=synthetic_collate):
        return relay.check_native_shapes(
            self.replay if replay is None else replay, expected_replay_sha256=self.replay_hash,
            modes=self.material.modes,
            tokenizer_sha256=sha256(b"synthetic tokenizer, NOT native proof").hexdigest(),
            collation_sha256=sha256(b"synthetic collator, NOT native proof").hexdigest(),
            encode=encode, collate=collate)

    def test_exact_all8_16_and_immutable_authorship(self):
        result = self.build()
        self.assertEqual(result.status, relay.PREPARED)
        self.assertEqual(result.formation.status, "ALL8_16_ADMITTED")
        self.assertEqual(len(result.formation.admitted), 8)
        self.assertEqual(sum(len(record.conditionals) for record in result.formation.admitted), 16)
        self.assertEqual(sum(len(block.executions) + 1 for block in self.blocks), 24)
        self.assertEqual(relay.digest(self.material), self.material_hash)
        self.assertEqual(relay.digest(self.blocks), self.source_hash)
        for block, admitted in zip(self.blocks, result.formation.admitted):
            self.assertIs(admitted.record, block.dream)
            for line in admitted.conditionals:
                self.assertEqual(line.SUPPORTED_FUTURE_ACT, block.dream.raw[slice(*line.action_span)])
        self.assertEqual(result, self.build())
        self.assertEqual(result.fits_performed, 0)

    def test_failure_is_supported_future_not_executed_action(self):
        row = self.build().auth_quartets[0][1]
        self.assertEqual(row.execution.EXECUTED_ACT, b"-mem2reg")
        self.assertEqual(row.execution.outcome.raw, b"FAILURE")
        self.assertEqual(row.SUPPORTED_FUTURE_ACT, b"-gvn")
        self.assertEqual(row.target, b"gvn")
        self.assertLess(row.execution.commit.sequence, row.execution.outcome.sequence)
        self.assertLess(row.execution.outcome.sequence, row.record.sequence)

    def test_exact_target_free_balanced_quartet_replay(self):
        result = self.build()
        self.assertEqual(len(result.auth_quartets), 32)
        self.assertEqual(result.schedule, tuple(range(32)) * 4)
        presentations = [row for index in result.schedule for row in result.auth_quartets[index]]
        self.assertEqual(len(presentations), 512)
        self.assertEqual(set(Counter((row.key, row.authored_mode) for row in presentations).values()), {32})
        self.assertEqual(Counter(row.SUPPORTED_FUTURE_ACT for row in presentations),
                         {b"-mem2reg": 256, b"-gvn": 256})
        for quartet in result.auth_quartets:
            self.assertEqual(len(quartet), 4)
            self.assertEqual(sorted(Counter(row.key for row in quartet).values()), [2, 2])
            self.assertNotEqual(quartet[0].key, quartet[1].key)
            self.assertEqual(Counter(row.SUPPORTED_FUTURE_ACT for row in quartet), {b"-mem2reg": 2, b"-gvn": 2})
            for row in quartet:
                self.assertTrue(row.prefix.endswith(b"ACT: -"))
                self.assertTrue((row.prefix + row.target).endswith(b"ACT: " + row.SUPPORTED_FUTURE_ACT))
                self.assertEqual(row.target, row.record.raw[slice(*row.target_span)])
                for forbidden in (*relay.ACTIONS, b"EVIDENCE:", b"DREAM:", b"SUCCESS", b"FAILURE"):
                    self.assertNotIn(forbidden, row.prefix)

    def test_exact_controls_and_swap_only_changes_mode_inputs(self):
        result = self.build()
        self.assertEqual(result.controls, (
            relay.Control("E_AUTH", "E_AUTH", True, True), relay.Control("E_SWAP", "E_SWAP", True, True),
            relay.Control("E_OFF", None, False, False), relay.Control("E_SHADOW", "E_AUTH", False, False)))
        for auth, swap in zip(result.auth_quartets, result.swap_quartets):
            for original, control in zip(auth, swap):
                self.assertNotEqual(original.input_mode, control.input_mode)
                self.assertEqual(control, replace(original, input_mode=control.input_mode,
                                                  prefix=original.prefix.replace(original.input_mode, control.input_mode)))
                self.assertIs(original.record, control.record)
                self.assertEqual(original.target, control.target)
                self.assertEqual(original.target_span, control.target_span)

    def test_null_no_admission_and_no_subset(self):
        for index in range(8):
            with self.subTest(index=index):
                result = self.assert_shortage(self.edit_dream(lambda raw: b"DREAM: NULL", index), "NO_ADMISSION")
                self.assertEqual(len(result.formation.admitted), 7)
        blocks = tuple(replace(block, dream=receipt(block.dream.receipt_id, block.dream.sequence, b"DREAM: NULL"))
                       for block in self.blocks)
        self.assertEqual(len(self.assert_shortage(blocks).formation.admitted), 0)

    def test_closed_record_grammar_no_repair(self):
        transforms = (
            lambda raw: raw + b"\n", lambda raw: b" " + raw, lambda raw: raw + b"\nACT: -gvn",
            lambda raw: raw.replace(b"\n", b"\r\n"), lambda raw: b"```\n" + raw + b"\n```",
            lambda raw: raw.replace(b"  ACT:", b" ACT:"), lambda raw: raw.replace(b"-mem2reg", b"-unknown"),
            lambda raw: raw.replace(b"DREAM: STORE", b"dream: store"), lambda raw: raw.split(b"\nWHEN: M1")[0],
            lambda raw: raw.replace(b"KEY:", b"KEY: \xff"), lambda raw: b"DREAM: NULL\n",
            lambda raw: raw.replace(b"WHEN: M1", b"WHEN: M0"),
            lambda raw: raw.replace(b"WHEN: M0", b"WHEN: M9"),
        )
        for transform in transforms:
            with self.subTest(raw=transform(self.blocks[0].dream.raw)):
                self.assert_shortage(self.edit_dream(transform))

    def test_invalid_action_grammars_and_executed_field(self):
        for raw in (b"ACT: -gvn\n", b" ACT: -gvn", b"ACT: -gvn\nACT: -mem2reg", b"ACT: gvn", b"ACT: -other"):
            with self.subTest(raw=raw):
                self.assert_shortage(self.edit_execution(lambda execution: replace(
                    execution, commit=receipt(execution.commit.receipt_id, execution.commit.sequence, raw))), "ACT grammar")
        self.assert_shortage(self.edit_execution(lambda execution: replace(execution, EXECUTED_ACT=b"-gvn")), "committed bytes")

    def test_corrupt_citations_never_replaced(self):
        for citation in (b"missing", b"fixture_exec_0_1", b"fixture_exec_1_0", b"fixture_outcome_0_0", b"fixture_dream_0"):
            with self.subTest(citation=citation):
                self.assert_shortage(self.edit_dream(lambda raw: raw.replace(b"fixture_exec_0_0", citation)), "citation")

    def test_corrupt_outcomes_and_unsupported_authored_actions(self):
        for raw in (b"FAILURE", b"SUCCESS\n", b"success", b"UNKNOWN"):
            with self.subTest(outcome=raw):
                self.assert_shortage(self.edit_execution(lambda execution: replace(
                    execution, outcome=receipt(execution.outcome.receipt_id, execution.outcome.sequence, raw))))
        self.assert_shortage(self.edit_dream(lambda raw: raw.replace(b"ACT: -gvn", b"ACT: -mem2reg")), "unsupported")

    def test_chronology_including_commit_outcome_and_seal(self):
        edits = (
            lambda execution: replace(execution, commit=replace(execution.commit, sequence=0)),
            lambda execution: replace(execution, outcome=replace(execution.outcome, sequence=1)),
            lambda execution: replace(execution, outcome=replace(execution.outcome, sequence=4)),
            lambda execution: replace(execution, commit=replace(execution.commit, sequence=True)),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                self.assert_shortage(self.edit_execution(edit))
        for sequence in (3, 4):
            self.assert_shortage((replace(self.blocks[0], dream=replace(self.blocks[0].dream, sequence=sequence)),) + self.blocks[1:])
        self.assert_shortage(self.blocks[1:] + self.blocks[:1])
        self.assertEqual(self.build(material=replace(self.material, sealed_sequence=1)).status, relay.SHORTAGE)

    def test_wrong_key_mode_object_and_duplicate_receipts(self):
        for field, value in (("key", self.material.keys[1]), ("mode", b"M1"), ("object_id", b"other")):
            self.assert_shortage(self.edit_execution(lambda execution: replace(execution, **{field: value})), "mismatch")
        self.assert_shortage(self.edit_dream(lambda raw: raw.replace(b"KEY: fixture_key_0", b"KEY: fixture_key_1")), "key mismatch")
        self.assert_shortage(self.edit_execution(lambda execution: replace(
            execution, outcome=replace(execution.outcome, receipt_id=execution.commit.receipt_id))), "duplicate")
        self.assert_shortage(self.edit_execution(lambda execution: replace(
            execution, outcome=replace(execution.outcome, receipt_id=self.blocks[0].dream.receipt_id)), block_index=1), "duplicate")

    def test_missing_or_extra_calls_are_terminal(self):
        self.assert_shortage(self.blocks[:-1], "eight source blocks")
        self.assert_shortage(self.blocks + self.blocks[:1], "eight source blocks")
        for executions in (self.blocks[0].executions[:1], self.blocks[0].executions * 2):
            self.assert_shortage((replace(self.blocks[0], executions=executions),) + self.blocks[1:])

    def test_tampered_raw_bytes_and_external_source_seal(self):
        self.assert_shortage(self.edit_dream(lambda raw: raw.replace(b"-gvn", b"-mem2reg"), rehash=False), "tampered")
        self.assert_shortage(self.edit_execution(lambda execution: replace(
            execution, commit=replace(execution.commit, raw=b"ACT: -gvn"))), "tampered")
        self.assert_shortage(self.edit_execution(lambda execution: replace(
            execution, outcome=replace(execution.outcome, raw=b"FAILURE"))), "tampered")
        self.assert_shortage(self.edit_dream(lambda raw: b"DREAM: NULL"), "source seal mismatch", self.source_hash)

    def test_invalid_material_and_target_bearing_prefixes(self):
        for material in (replace(self.material, keys=self.material.keys[:-1]),
                         replace(self.material, modes=(b"M0", b"M0")),
                         replace(self.material, views=self.material.views[:-1]),
                         replace(self.material, source_objects=self.material.source_objects[:-1]),
                         replace(self.material, pairs=self.material.pairs[:-1]),
                         replace(self.material, surfaces=self.material.surfaces[:-1]),
                         replace(self.material, generation_seed=None)):
            with self.subTest(material=material), self.assertRaises(ValueError):
                self.build(material=material)
        first = self.material.surfaces[0]
        for surface in (replace(first, prefix=first.prefix + b"\n"),
                        replace(first, prefix=first.prefix + b"gvn\nACT: -"),
                        replace(first, mode_span=first.key_span),
                        replace(first, object_id=self.material.source_objects[0]),
                        replace(first, prefix=first.prefix.replace(b"OBJECT:", b"EVIDENCE:"))):
            with self.subTest(surface=surface), self.assertRaises(ValueError):
                self.build(material=replace(self.material, surfaces=(surface,) + self.material.surfaces[1:]))

    def test_presealed_surface_and_pair_balance_not_reselected(self):
        material = replace(self.material, root_id=b"different")
        with self.assertRaisesRegex(ValueError, "material seal"):
            relay.build_replay(material, self.blocks, expected_material_sha256=self.material_hash,
                               expected_source_sha256=self.source_hash)
        keys = self.material.keys
        material = replace(self.material, pairs=((keys[0], keys[2]), (keys[1], keys[3]),
                                                  (keys[4], keys[5]), (keys[6], keys[7])))
        result = self.build(material=material)
        self.assertEqual(result.status, relay.SHORTAGE)
        self.assertIn("unbalanced sealed key pair", result.formation.reasons)

    def test_target_suffix_leak_in_both_mode_inputs_is_rejected(self):
        for leaked in (b"mem2reg", b"gvn"):
            surfaces = tuple(replace(surface, prefix=surface.prefix.replace(
                b"\nOBJECT:", b"\nANSWER: " + leaked + b"\nOBJECT:")) for surface in self.material.surfaces)
            with self.subTest(leaked=leaked), self.assertRaisesRegex(ValueError, "target-bearing"):
                self.build(material=replace(self.material, surfaces=surfaces))

    def test_native_shape_interface_is_explicit_and_synthetic_only(self):
        result = self.native()
        self.assertEqual(result.status, "SUPPLIED_NATIVE_SHAPES_CHECKED_NOT_LAUNCH_AUTHORIZATION")
        self.assertEqual(result.replay_sha256, relay.digest(self.build()))
        self.assertEqual(result, self.native())
        with self.assertRaises(TypeError):
            relay.check_native_shapes(self.build(), modes=self.material.modes)
        with self.assertRaisesRegex(ValueError, "replay seal mismatch"):
            self.native(self.build(self.edit_dream(lambda raw: b"DREAM: NULL")))

    def test_native_token_shape_corruptions(self):
        with self.assertRaisesRegex(ValueError, "one-token"):
            self.native(encode=lambda raw: tuple(raw))
        with self.assertRaisesRegex(ValueError, "one-token"):
            self.native(encode=lambda raw: tuple(1000 if token == 1001 else token for token in synthetic_encode(raw)))
        with self.assertRaisesRegex(ValueError, "prefix lengths"):
            self.native(encode=lambda raw: synthetic_encode(raw) + ((0,) if len(raw) > 2 and b"M1" in raw else ()))
        with self.assertRaisesRegex(ValueError, "beyond one mode"):
            self.native(encode=lambda raw: ((999,) + synthetic_encode(raw)[1:] if len(raw) > 2 and b"M1" in raw
                                           else synthetic_encode(raw)))
        with self.assertRaisesRegex(ValueError, "target crosses"):
            self.native(encode=lambda raw: ((999,) + synthetic_encode(raw)[1:] if raw.endswith(b"gvn")
                                           else synthetic_encode(raw)))

    def test_native_collation_inequality_and_missing_shapes(self):
        calls = []

        def mismatched(rows):
            calls.append(rows)
            shape = synthetic_collate(rows)
            return shape if len(calls) % 2 else replace(shape, target_positions=((0,),) * 4)

        with self.assertRaisesRegex(ValueError, "quartet collation"):
            self.native(collate=mismatched)
        with self.assertRaisesRegex(ValueError, "missing native"):
            self.native(collate=lambda rows: relay.BatchShape((), (), ()))

    def test_native_rejects_altered_replay_and_targets(self):
        replay = self.build()
        for altered in (replace(replay, schedule=(0,) * 128),
                        replace(replay, swap_quartets=replay.swap_quartets[:-1]),
                        replace(replay, auth_quartets=(replay.auth_quartets[0][:-1],) + replay.auth_quartets[1:]),
                        replace(replay, controls=()), replace(replay, fits_performed=1)):
            with self.subTest(altered=altered.status), self.assertRaises(ValueError):
                self.native(altered)
        row = replay.swap_quartets[0][0]
        for altered_row in (replace(row, target=b"gvn"), replace(row, authored_mode=b"M1"),
                            replace(row, record=replace(row.record, raw=row.record.raw + b"\n"))):
            altered = replace(replay, swap_quartets=((altered_row,) + replay.swap_quartets[0][1:],) + replay.swap_quartets[1:])
            with self.subTest(row=altered_row), self.assertRaisesRegex(ValueError, "replay seal mismatch"):
                self.native(altered)

    def test_expected_replay_hash_required_and_validated_before_callbacks(self):
        encode = Mock(side_effect=AssertionError("encoder must not run"))
        collate = Mock(side_effect=AssertionError("collator must not run"))
        arguments = dict(modes=self.material.modes,
                         tokenizer_sha256=sha256(b"synthetic tokenizer").hexdigest(),
                         collation_sha256=sha256(b"synthetic collator").hexdigest(),
                         encode=encode, collate=collate)
        with self.assertRaisesRegex(TypeError, "expected_replay_sha256"):
            relay.check_native_shapes(self.replay, **arguments)
        for expected in (None, b"0" * 64, "", "invalid", "0" * 63, "A" * 64, "0" * 64):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, "expected replay|replay seal mismatch"):
                relay.check_native_shapes(self.replay, expected_replay_sha256=expected, **arguments)
        encode.assert_not_called()
        collate.assert_not_called()

    def test_symmetric_wrong_mode_target_substitution_rejected(self):
        other = self.replay.formation.admitted[0].conditionals[1]
        span = (other.action_span[0] + 1, other.action_span[1])

        def wrong_binding(row):
            return replace(row, SUPPORTED_FUTURE_ACT=other.SUPPORTED_FUTURE_ACT,
                           target=row.record.raw[slice(*span)], target_span=span)

        altered = replace(
            self.replay,
            auth_quartets=((wrong_binding(self.replay.auth_quartets[0][0]),) +
                           self.replay.auth_quartets[0][1:],) + self.replay.auth_quartets[1:],
            swap_quartets=((wrong_binding(self.replay.swap_quartets[0][0]),) +
                           self.replay.swap_quartets[0][1:],) + self.replay.swap_quartets[1:])
        self.assertEqual(altered.auth_quartets[0][0].target, altered.swap_quartets[0][0].target)
        self.assertNotEqual(altered.auth_quartets[0][0].target, self.replay.auth_quartets[0][0].target)
        encode, collate = Mock(), Mock()
        with self.assertRaisesRegex(ValueError, "replay seal mismatch"):
            self.native(altered, encode=encode, collate=collate)
        encode.assert_not_called()
        collate.assert_not_called()
        self.assertEqual(relay.digest(self.replay), self.replay_hash)

    def test_symmetric_repeated_first_quartet_rejected(self):
        altered = replace(self.replay, auth_quartets=(self.replay.auth_quartets[0],) * 32,
                          swap_quartets=(self.replay.swap_quartets[0],) * 32)
        counts = Counter((row.key, row.authored_mode) for index in altered.schedule
                         for row in altered.auth_quartets[index])
        self.assertEqual(sorted(counts.values()), [128] * 4)
        self.assertEqual(altered.schedule, self.replay.schedule)
        encode, collate = Mock(), Mock()
        with self.assertRaisesRegex(ValueError, "replay seal mismatch"):
            self.native(altered, encode=encode, collate=collate)
        encode.assert_not_called()
        collate.assert_not_called()
        self.assertEqual(relay.digest(self.replay), self.replay_hash)

    def test_public_receipts_cannot_silently_reseal_after_capture(self):
        execution = self.blocks[0].executions[0]
        blocks = self.edit_execution(lambda original: replace(
            original, outcome=receipt(original.outcome.receipt_id, original.outcome.sequence, b"FAILURE")))
        self.assert_shortage(blocks, "source seal mismatch", self.source_hash)
        self.assertEqual(self.blocks[0].executions[0], execution)

    def test_supported_but_noncomplementary_world_receipts_do_not_compile(self):
        original = self.blocks[0]
        execution = original.executions[1]
        changed = replace(execution, outcome=receipt(execution.outcome.receipt_id, execution.outcome.sequence, b"SUCCESS"))
        raw = original.dream.raw.replace(b"ACT: -gvn", b"ACT: -mem2reg")
        block = replace(original, executions=(original.executions[0], changed),
                        dream=receipt(original.dream.receipt_id, original.dream.sequence, raw))
        result = self.assert_shortage((block,) + self.blocks[1:], "unbalanced authored bindings")
        self.assertEqual(len(result.formation.admitted), 8)


if __name__ == "__main__":
    unittest.main()
