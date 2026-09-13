"""Synthetic CPU interface fixtures, NOT pinned/native-tokenizer validation."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
import re
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_curriculum as curriculum
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_tokenization as source
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


class FakeTokenizer:
    """Pinned no-tool template spelling with synthetic, non-native token IDs."""

    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token = "<|endoftext|>"
    pad_token_id = 0
    padding_side = "right"
    all_special_ids = [0, 1, 2, 3]
    special_tokens = {"<|endoftext|>": 0, "<|im_end|>": 1, "<|im_start|>": 2, "<X>": 3}

    def __init__(self, fault=None):
        self.fault = fault
        self.offset = 0
        self.calls = []

    def encode(self, text, *, add_special_tokens, truncation):
        if add_special_tokens is not False or truncation is not False:
            raise AssertionError("Implicit specials/truncation forbidden in fixture")
        tokens = []
        for part in re.split(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>|<X>)", text):
            if part in self.special_tokens:
                tokens.append(self.special_tokens[part])
            else:
                tokens.extend(ord(character) + 10 + self.offset for character in part)
        if self.fault == "implicit_special":
            tokens.append(3)
        if self.fault == "merge_boundary":
            boundary = [ord(character) + 10 for character in "assistant\nREAD"]
            for index in reversed(range(len(tokens) - len(boundary) + 1)):
                if tokens[index:index + len(boundary)] == boundary:
                    return tokens[:index] + [1000] + tokens[index + len(boundary):]
        if self.fault == "merge_eos_suffix" and tokens[-2:] == [1, 20]:
            return tokens[:-2] + [1002]
        return tokens

    def decode(self, token_ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        if skip_special_tokens is not False or clean_up_tokenization_spaces is not False:
            raise AssertionError("Lossy decode forbidden in fixture")
        reverse = {value: key for key, value in self.special_tokens.items()}
        text = "".join(reverse[token] if token in reverse else "assistant\nREAD" if token == 1000
                       else "<|im_end|>\n" if token == 1002
                       else chr(token - 10 - (256 if token >= 256 else 0)) for token in token_ids)
        return text.replace("READ", "READ ") if self.fault == "lossy_decode" else text

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                           truncation=False, padding=False):
        self.calls.append((tuple((message["role"], message["content"]) for message in messages),
                           tokenize, add_generation_prompt, truncation, padding))
        if truncation is not False or padding is not False:
            raise AssertionError("Template must not pad or truncate")
        self.offset = 256 if self.fault == "arm_drift" and len(messages) <= 3 else 0
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n"
                       for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        elif self.fault == "missing_suffix":
            text = text[:-1]
        elif self.fault == "non_lf_suffix":
            text = text[:-1] + " "
        elif self.fault == "crlf_suffix":
            text = text[:-1] + "\r\n"
        elif self.fault == "duplicate_suffix":
            text += "\n"
        elif self.fault == "content_past_eos":
            text = text[:-1] + "TEACHER\n"
        elif self.fault == "content_past_suffix":
            text += "TEACHER"
        elif self.fault == "missing_eos":
            text = text[:-len("<|im_end|>\n")] + "\n"
        elif self.fault == "duplicate_eos":
            text = text[:-1] + "<|im_end|>\n"
        elif self.fault == "extra_special":
            text = text[:-len("<|im_end|>\n")] + "<X><|im_end|>\n"
        elif self.fault == "target_contamination":
            text = text[:-len("<|im_end|>\n")] + "TEACHER<|im_end|>\n"
        elif self.fault == "header_mismatch":
            text = text.replace("<|im_start|>assistant\n", "<|im_start|>assistant \n")
        if tokenize:
            token_ids = self.encode(text, add_special_tokens=False, truncation=False)
            return token_ids[:-1] if self.fault == "template_truncation" else token_ids
        return text


class Stage2ATokenizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum = curriculum.compile_birth_curriculum(
            role_tokens_by_world={f"p{number:02d}": synthetic_bindings(number) for number in range(32)},
            master=b"SYNTHETIC-TOKENIZER-INTERFACE-ONLY")
        cls.pairs = cls.curriculum.paired_targets
        cls.by_id = {pair.closed.unit.unit_id: pair for pair in cls.pairs}

    def prepare(self, pair=None, tokenizer=None):
        return source.tokenize_paired_target(
            self.pairs[0] if pair is None else pair,
            tokenizer=FakeTokenizer() if tokenizer is None else tokenizer,
            count_basis="SYNTHETIC_FIXTURE")

    def batch(self, presentation=None, **overrides):
        presentation = self.curriculum.batches[0] if presentation is None else presentation
        pairs = tuple(self.by_id[unit] for unit in presentation.unit_ids)
        prepared = tuple(self.prepare(pair) for pair in pairs)
        kwargs = dict(tokenizer=FakeTokenizer(), count_basis="SYNTHETIC_FIXTURE",
                      closed_padding_length=max(len(pair.closed.input_ids) for pair in prepared),
                      atom_local_padding_length=max(len(pair.atom_local.input_ids) for pair in prepared))
        kwargs.update(overrides)
        return source.prepare_paired_batch(presentation, pairs, **kwargs)

    def test_all_512_records_have_exact_unshifted_target_and_eos_masks(self):
        counts = Counter()
        for pair in self.pairs:
            prepared = self.prepare(pair)
            self.assertEqual(prepared.closed.target_ids, prepared.atom_local.target_ids)
            self.assertEqual(prepared.closed.identifier_tokenization, prepared.atom_local.identifier_tokenization)
            counts[pair.closed.unit.command] += 1
            for row in (prepared.closed, prepared.atom_local):
                with self.subTest(unit=row.record.unit.unit_id, arm=row.record.arm):
                    self.assertEqual(row.labels[:row.target_start], (-100,) * row.target_start)
                    self.assertEqual(row.labels[row.target_start:row.target_end], row.target_ids)
                    self.assertEqual(row.input_ids, row.context_ids + row.target_ids + row.suffix_ids)
                    self.assertEqual(row.labels[row.target_end:], (-100,) * len(row.suffix_ids))
                    self.assertEqual(row.suffix_ids, (20,))
                    self.assertEqual(row.suffix_roundtrip_bytes, b"\n")
                    self.assertEqual(row.input_ids[row.target_end:], row.suffix_ids)
                    self.assertEqual(row.attention_mask, (1,) * len(row.input_ids))
                    self.assertEqual(row.target_ids[-1], 1)
                    self.assertEqual(row.target_ids.count(1), 1)
                    self.assertEqual(row.target_roundtrip_bytes, row.record.unit.target_bytes + b"<|im_end|>")
                    self.assertEqual(row.sequence_roundtrip_bytes,
                                     row.context_roundtrip_bytes + row.target_roundtrip_bytes + b"\n")
                    self.assertLessEqual(len(row.input_ids), 16384)
                    self.assertEqual(row.count_basis, "SYNTHETIC_FIXTURE")
                    self.assertFalse(row.native_tokenizer_validated)
        self.assertEqual(counts, {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32})

    def test_template_receives_only_existing_messages_and_no_truncation(self):
        tokenizer = FakeTokenizer()
        pair = self.pairs[3]
        prepared = self.prepare(pair, tokenizer)
        for record, calls in ((pair.closed, tokenizer.calls[:4]), (pair.atom_local, tokenizer.calls[4:])):
            prefix = tuple((message.role, message.content) for message in record.prefix)
            training = prefix + (("assistant", record.unit.target_bytes.decode("ascii")),)
            self.assertEqual(calls, [(prefix, False, True, False, False),
                                     (training, False, False, False, False),
                                     (prefix, True, True, False, False),
                                     (training, True, False, False, False)])
        self.assertGreater(len(prepared.closed.context_ids), len(prepared.atom_local.context_ids))
        self.assertIn(1, prepared.closed.context_ids)
        self.assertTrue(all(label == -100 for label in prepared.closed.labels[:prepared.closed.target_start]))

    def test_pinned_final_lf_is_preserved_attended_and_never_supervised(self):
        self.assertEqual(source.TEMPLATE_SUFFIX, "\n")
        self.assertEqual(source.TEMPLATE_CONFIG_SHA256,
                         "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583")
        prepared = self.prepare(self.pairs[3])
        for row in (prepared.closed, prepared.atom_local):
            expected = "".join("<|im_start|>" + message.role + "\n" + message.content + "<|im_end|>\n"
                               for message in row.record.training_messages).encode("ascii")
            self.assertEqual(row.sequence_roundtrip_bytes, expected)
            self.assertTrue(row.sequence_roundtrip_bytes.endswith(b"<|im_end|>\n"))
            self.assertEqual(row.target_end, len(row.input_ids) - len(row.suffix_ids))
            self.assertEqual(row.labels[row.target_end - 1], row.eos_token_id)
            self.assertEqual(row.labels[row.target_end:], (-100,))
            self.assertEqual(row.attention_mask[row.target_end:], (1,))
            self.assertEqual(row.input_ids[row.target_end:], row.suffix_ids)
            self.assertEqual(sum(label != -100 for label in row.labels), len(row.target_ids))
            self.assertNotIn(row.eos_token_id, row.suffix_ids)
            self.assertFalse(row.native_tokenizer_validated)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_identifier_report_retains_standalone_and_in_target_tokenization(self):
        row = self.prepare().closed
        self.assertEqual(len(row.identifier_tokenization), 1)
        identifier = row.identifier_tokenization[0]
        self.assertEqual(identifier.identifier, row.record.unit.operand)
        self.assertEqual(row.record.unit.target_bytes[identifier.byte_start:identifier.byte_end],
                         identifier.identifier.encode("ascii"))
        self.assertEqual(identifier.standalone_ids, identifier.target_token_ids)
        self.assertEqual(identifier.target_token_ids,
                         tuple(row.target_ids[index] for index in identifier.target_token_indices))
        stop = next(pair for pair in self.pairs if pair.closed.unit.command == "STOP")
        self.assertEqual(self.prepare(stop).closed.identifier_tokenization, ())

    def test_rejects_template_suffix_contamination_missing_extra_eos_and_headers(self):
        for fault in ("missing_suffix", "non_lf_suffix", "crlf_suffix", "duplicate_suffix", "content_past_eos",
                      "content_past_suffix", "missing_eos", "duplicate_eos", "extra_special",
                      "target_contamination", "header_mismatch"):
            with self.subTest(fault=fault), self.assertRaisesRegex(ValueError, "chat_template_boundary"):
                self.prepare(tokenizer=FakeTokenizer(fault))

    def test_identifier_tokens_may_overlap_the_preceding_space(self):
        pair = self.pairs[0]
        fragment = " " + pair.closed.unit.operand
        pattern = [ord(character) + 10 for character in fragment]

        class MergedIdentifierTokenizer(FakeTokenizer):
            def encode(self, text, *, add_special_tokens, truncation):
                tokens = super().encode(text, add_special_tokens=add_special_tokens, truncation=truncation)
                for index in reversed(range(len(tokens) - len(pattern) + 1)):
                    if tokens[index:index + len(pattern)] == pattern:
                        tokens[index:index + len(pattern)] = [1001]
                return tokens

            def decode(self, token_ids, *, skip_special_tokens, clean_up_tokenization_spaces):
                return "".join(fragment if token == 1001 else super(MergedIdentifierTokenizer, self).decode(
                    [token], skip_special_tokens=skip_special_tokens,
                    clean_up_tokenization_spaces=clean_up_tokenization_spaces) for token in token_ids)

        prepared = self.prepare(pair, MergedIdentifierTokenizer())
        identifier = prepared.closed.identifier_tokenization[0]
        self.assertEqual(identifier.target_token_ids, (1001,))
        self.assertNotEqual(identifier.standalone_ids, identifier.target_token_ids)
        self.assertEqual(prepared.closed.identifier_tokenization, prepared.atom_local.identifier_tokenization)

    def test_rejects_merged_boundary_lossy_decode_implicit_specials_and_truncation(self):
        for fault, error in (("merge_boundary", "token_boundary"), ("merge_eos_suffix", "token_boundary"),
                             ("lossy_decode", "roundtrip"),
                             ("implicit_special", "roundtrip"), ("template_truncation", "tokenization_mismatch")):
            with self.subTest(fault=fault), self.assertRaisesRegex(ValueError, error):
                self.prepare(tokenizer=FakeTokenizer(fault))

    def test_rejects_invalid_eos_pad_special_declarations_and_left_padding(self):
        mutations = ({"eos_token_id": None}, {"eos_token_id": True}, {"eos_token_id": -1},
                     {"eos_token_id": [1]}, {"eos_token_id": 3}, {"eos_token": ""},
                     {"eos_token": "<|im_end|><|im_end|>"}, {"pad_token_id": None}, {"pad_token_id": False},
                     {"pad_token_id": 3}, {"pad_token": ""}, {"all_special_ids": [0, 2]},
                     {"all_special_ids": [0, 1, True]}, {"all_special_ids": None},
                     {"padding_side": "left"})
        for mutation in mutations:
            tokenizer = FakeTokenizer()
            for key, value in mutation.items():
                setattr(tokenizer, key, value)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.prepare(tokenizer=tokenizer)

    def test_non_integer_negative_empty_or_tensor_like_ids_fail_closed(self):
        for ids in ([], [True], [-1], [1.0], {"input_ids": [1]}, iter([1]), [[1]]):
            tokenizer = FakeTokenizer()
            with patch.object(tokenizer, "encode", return_value=ids):
                with self.subTest(ids=repr(ids)), self.assertRaisesRegex(ValueError, "ids"):
                    self.prepare(tokenizer=tokenizer)

    def test_declared_special_inside_message_is_contamination(self):
        tokenizer = FakeTokenizer()
        tokenizer.all_special_ids = tokenizer.all_special_ids + [ord("R") + 10]
        with self.assertRaisesRegex(ValueError, "message_special_contamination"):
            self.prepare(tokenizer=tokenizer)

    def test_different_arm_target_tokens_fail_even_with_exact_roundtrips(self):
        with self.assertRaisesRegex(ValueError, "paired_target_tokenization_mismatch"):
            self.prepare(self.pairs[3], FakeTokenizer("arm_drift"))

    def test_source_tampering_and_non_shared_targets_fail_before_tokenizer(self):
        pair = self.pairs[0]
        unit = pair.closed.unit
        mutations = (replace(pair, closed=replace(pair.closed, prefix_sha256="0" * 64)),
                     replace(pair, closed=replace(pair.closed, content_bytes=0)),
                     replace(pair, closed=replace(pair.closed, serialized_bytes=0)),
                     replace(pair, closed=replace(pair.closed, prefix=list(pair.closed.prefix))),
                     replace(pair, atom_local=replace(pair.atom_local, unit=replace(unit))),
                     replace(pair, closed=replace(pair.closed, arm="ATOM_LOCAL")),
                     replace(pair, closed=replace(pair.closed, unit=replace(unit, target_sha256="0" * 64))),
                     replace(pair, closed=replace(pair.closed, unit=replace(unit, command="STOP"))),
                     replace(pair, closed=replace(pair.closed, unit=replace(unit, operand="wrong"))),
                     replace(pair, closed=replace(pair.closed, unit=replace(unit, target_bytes=b"STOP\n"))),
                     replace(pair, closed=replace(pair.closed, unit=replace(unit, unit_id="p32/m0/u0"))))
        tokenizer = FakeTokenizer()
        with patch.object(tokenizer, "encode", side_effect=AssertionError("must fail before tokenization")):
            for mutation in mutations:
                with self.subTest(mutation=repr(mutation)[:100]), self.assertRaises(ValueError):
                    self.prepare(mutation, tokenizer)

    def test_batch_four_exact_slots_no_packing_and_right_padding_mask(self):
        batch = self.batch()
        self.assertIs(batch.presentation, self.curriculum.batches[0])
        for arm in (batch.closed, batch.atom_local):
            self.assertEqual(len(arm.input_ids), 4)
            self.assertEqual(tuple(row.record.unit.unit_id for row in arm.records), batch.presentation.unit_ids)
            self.assertEqual(tuple(len(row.target_ids) for row in arm.records), batch.target_token_counts)
            self.assertEqual(tuple(row.record.unit.target_sha256 for row in arm.records), batch.target_hashes)
            for row, input_ids, labels, attention in zip(arm.records, arm.input_ids, arm.labels, arm.attention_mask):
                length = len(row.input_ids)
                self.assertEqual(input_ids[:length], row.input_ids)
                self.assertEqual(input_ids[length:], (row.pad_token_id,) * (arm.padding_length - length))
                self.assertEqual(labels[:length], row.labels)
                self.assertEqual(labels[length:], (-100,) * (arm.padding_length - length))
                self.assertEqual(attention, (1,) * length + (0,) * (arm.padding_length - length))
                self.assertEqual(sum(label != -100 for label in labels), len(row.target_ids))
                self.assertEqual(len(input_ids), arm.padding_length)
        self.assertEqual(batch.residuals["target_tokens"], 0)
        self.assertGreater(batch.residuals["prefix_tokens"], 0)
        for arm in (batch.closed, batch.atom_local):
            self.assertEqual(arm.accounting["total_sequence_tokens"],
                             arm.accounting["sequence_tokens"] + arm.accounting["padding_tokens"])
            self.assertEqual(arm.accounting["target_tokens"], sum(batch.target_token_counts))
            self.assertEqual(arm.accounting["suffix_tokens"], 4)
            self.assertEqual(arm.accounting["sequence_tokens"], arm.accounting["prefix_tokens"]
                             + arm.accounting["target_tokens"] + arm.accounting["suffix_tokens"])
        self.assertIsNone(batch.rng_start_state_sha256)

    def test_padding_widths_are_explicit_not_guessed_equal(self):
        batch = self.batch(closed_padding_length=16384, atom_local_padding_length=16000)
        self.assertEqual(batch.closed.padding_length, 16384)
        self.assertEqual(batch.atom_local.padding_length, 16000)
        self.assertEqual(batch.residuals["total_sequence_tokens"], 4 * 384)
        with self.assertRaises(TypeError):
            source.prepare_paired_batch(self.curriculum.batches[0], (), tokenizer=FakeTokenizer(),
                                        count_basis="SYNTHETIC_FIXTURE")
        for width in (0, -1, True, 16385, 1.5, 1):
            for name in ("closed_padding_length", "atom_local_padding_length"):
                with self.subTest(width=width, arm=name), self.assertRaisesRegex(ValueError, "padding_width"):
                    self.batch(**{name: width})

    def test_declared_pad_equal_eos_is_masked_by_position_not_id(self):
        tokenizer = FakeTokenizer()
        tokenizer.pad_token_id, tokenizer.pad_token = 1, "<|im_end|>"
        batch = self.batch(tokenizer=tokenizer, closed_padding_length=16384, atom_local_padding_length=16384)
        for arm in (batch.closed, batch.atom_local):
            for row, labels, inputs in zip(arm.records, arm.labels, arm.input_ids):
                self.assertEqual(labels[row.target_end - 1], 1)
                self.assertEqual(labels[row.target_end:len(row.input_ids)], (-100,))
                self.assertEqual(labels[len(row.input_ids):], (-100,) * (16384 - len(row.input_ids)))
                self.assertEqual(inputs[len(row.input_ids):], (1,) * (16384 - len(row.input_ids)))

    def test_batch_rejects_drops_duplicates_shuffle_and_invalid_update_metadata(self):
        presentation = self.curriculum.batches[0]
        pairs = tuple(self.by_id[unit] for unit in presentation.unit_ids)
        kwargs = dict(tokenizer=FakeTokenizer(), count_basis="SYNTHETIC_FIXTURE",
                      closed_padding_length=16384, atom_local_padding_length=16384)
        for bad in (pairs[:3], pairs + pairs[:1], tuple(reversed(pairs)), (pairs[0],) * 4):
            with self.subTest(kind="records"), self.assertRaises(ValueError):
                source.prepare_paired_batch(presentation, bad, **kwargs)
        for mutation in (dict(update_number=0), dict(update_number=513), dict(update_number=True),
                         dict(presentation_index=1), dict(presentation_index=False),
                         dict(rng_start_seed=-1), dict(rng_start_seed=2**64), dict(rng_start_seed=True),
                         dict(unit_ids=presentation.unit_ids[:3]), dict(unit_ids=(presentation.unit_ids[0],) * 4)):
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "presentation_batch"):
                source.prepare_paired_batch(replace(presentation, **mutation), pairs, **kwargs)

    def test_d1_d2_boundary_preserves_tape_metadata_without_opening_d2(self):
        for index, stage, presentation_index in ((0, "D1", 0), (255, "D1", 3),
                                                 (256, "D2", 4), (511, "D2", 7)):
            batch = self.batch(self.curriculum.batches[index])
            self.assertEqual(batch.presentation.update_number, index + 1)
            self.assertEqual(batch.presentation.stage, stage)
            self.assertEqual(batch.presentation.presentation_index, presentation_index)
            self.assertEqual(batch.presentation.rng_start_seed, self.curriculum.batches[index].rng_start_seed)
            self.assertEqual(batch.status, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_context_cap_accepts_exact_limit_rejects_overflow_without_truncation(self):
        pair = self.pairs[0]

        class LongTemplate(FakeTokenizer):
            def __init__(self, filler):
                super().__init__()
                self.filler = filler

            def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                                   truncation=False, padding=False):
                text = "z" * self.filler + super().apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=add_generation_prompt,
                    truncation=truncation, padding=padding)
                return self.encode(text, add_special_tokens=False, truncation=False) if tokenize else text

        normal = self.prepare(pair).closed
        filler = 16384 - len(normal.input_ids)
        row = source.tokenize_arm_record(pair.closed, tokenizer=LongTemplate(filler), count_basis="SYNTHETIC_FIXTURE")
        self.assertEqual(len(row.input_ids), 16384)
        self.assertEqual(row.target_end, 16383)
        self.assertEqual(row.labels[-1], -100)
        self.assertEqual(row.attention_mask[-1], 1)
        with self.assertRaisesRegex(ValueError, "over_context_sequence"):
            source.tokenize_arm_record(pair.closed, tokenizer=LongTemplate(filler + 1), count_basis="SYNTHETIC_FIXTURE")

    def test_no_native_claims_io_or_mutable_outputs(self):
        with patch("builtins.open", side_effect=AssertionError("no file access")), \
                patch("socket.socket", side_effect=AssertionError("no network")), \
                patch("subprocess.Popen", side_effect=AssertionError("no process")):
            batch = self.batch()
        with self.assertRaises(FrozenInstanceError):
            batch.closed.records[0].labels = ()
        with self.assertRaises(TypeError):
            batch.residuals["target_tokens"] = 5
        with self.assertRaises(TypeError):
            source.SCIENCE_GATES["GO_MODEL_TOKENIZER"] = True
        for label in (None, "NATIVE_VALIDATED", "PASS"):
            with self.assertRaisesRegex(ValueError, "non_native_count_basis"):
                source.tokenize_arm_record(self.pairs[0].closed, tokenizer=FakeTokenizer(), count_basis=label)
        unauthenticated = source.tokenize_arm_record(self.pairs[0].closed, tokenizer=FakeTokenizer(),
                                                     count_basis="UNAUTHENTICATED_CALLER_TOKENIZER")
        self.assertFalse(unauthenticated.native_tokenizer_validated)
        self.assertEqual(unauthenticated.status, source.STATUS)
        self.assertEqual(set(source.SCIENCE_GATES), set(targets.SCIENCE_GATES))


if __name__ == "__main__":
    unittest.main()
