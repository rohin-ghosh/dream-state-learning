"""Bounded synthetic CPU tests only; no native/corpus/allocation execution."""

import base64
from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_native_prepare as source
from organism_v6 import composition_birth_stage2a_curriculum as curriculum
from organism_v6 import composition_birth_stage2a_screen_runtime as screen_runtime
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings
from tests.test_composition_birth_stage2a_held import fixtures


MASTER = b"SYNTHETIC-ASTRA-PREPARE-NOT-NATIVE"


class FakeTokenizer:
    """Reversible word/punctuation IDs; deliberately unrelated to native IDs."""

    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token = "<|endoftext|>"
    pad_token_id = 0
    padding_side = "right"
    all_special_ids = (0, 1, 2)

    def __init__(self):
        self.words = {0: "<|endoftext|>", 1: self.eos_token, 2: "<|im_start|>"}
        self.specials = {value: key for key, value in self.words.items()}

    @lru_cache(maxsize=8192)
    def encode(self, text, *, add_special_tokens, truncation):
        if add_special_tokens or truncation:
            raise AssertionError("no implicit specials or truncation")
        result = []
        for word in re.findall(r"<\|(?:im_start|im_end|endoftext)\|>|[A-Za-z0-9_]+|[^\w]", text):
            token = self.specials.get(word)
            if token is None:
                token = 10 + int.from_bytes(sha256(word.encode("ascii")).digest()[:8], "big")
            if token in self.words and self.words[token] != word:
                raise AssertionError("synthetic token collision")
            self.words[token] = word
            result.append(token)
        return tuple(result)

    def decode(self, token_ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        if skip_special_tokens or clean_up_tokenization_spaces:
            raise AssertionError("no lossy decoding")
        return "".join(self.words[token] for token in token_ids)

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                            truncation=False, padding=False):
        if truncation or padding:
            raise AssertionError("no implicit padding or truncation")
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n"
                       for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text, add_special_tokens=False, truncation=False) if tokenize else text


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(source.allocation, "allocate_stage2a", side_effect=AssertionError("no allocation")):
            cls.compiled = curriculum.compile_birth_curriculum(
                role_tokens_by_world={f"p{number:02d}": synthetic_bindings(number) for number in range(32)},
                master=MASTER,
            )
            cls.prepared = source.prepare_birth(validated_curriculum=cls.compiled, tokenizer=FakeTokenizer(),
                                                master=MASTER, padding_policy="PER_ARM_MAX")
        cls.receipt = json.loads(cls.prepared.receipt_bytes)

    def test_exact_roster_tape_and_later_d1_slice(self):
        prepared = self.prepared
        self.assertIs(prepared.paired_targets, self.compiled.paired_targets)
        self.assertEqual(len(prepared.tokenized_pairs), 256)
        self.assertEqual(len(prepared.batches), 512)
        self.assertEqual(len(prepared.d1_atom_local_batches), 256)
        self.assertTrue(all(batch.arm == "ATOM_LOCAL" for batch in prepared.d1_atom_local_batches))
        self.assertEqual(tuple(batch.presentation for batch in prepared.batches), self.compiled.batches)
        self.assertEqual(Counter(unit for batch in prepared.batches for unit in batch.presentation.unit_ids),
                         Counter({unit: 8 for unit in source.tape.unit_identifiers()}))
        self.assertEqual(source.training.validate_batches(prepared.batches, master=MASTER),
                         prepared.tape_fingerprint)
        self.assertEqual(self.receipt["executed_updates"], 0)
        self.assertEqual(self.receipt["count_basis"], "UNAUTHENTICATED_CALLER_TOKENIZER")
        self.assertEqual(self.receipt["later_requested_slice"],
                         {"stage": "D1", "arm": "ATOM_LOCAL", "updates": 256})

    def test_measured_padding_labels_and_exact_accounting(self):
        for batch, receipt in zip(self.prepared.batches, self.receipt["batches"]):
            self.assertEqual(batch.closed.records[0].count_basis, source.COUNT_BASIS)
            for arm in (batch.closed, batch.atom_local):
                self.assertEqual(arm.padding_length, max(len(row.input_ids) for row in arm.records))
                self.assertEqual(receipt["padding_lengths"][arm.arm], arm.padding_length)
                self.assertEqual(receipt["accounting"][arm.arm], dict(arm.accounting))
                for row, labels, mask in zip(arm.records, arm.labels, arm.attention_mask):
                    self.assertEqual(tuple(label for label in labels if label != -100), row.target_ids)
                    self.assertEqual(sum(mask), len(row.input_ids))
                    self.assertEqual(row.suffix_roundtrip_bytes, b"\n")
            self.assertEqual(batch.closed.accounting["target_tokens"], batch.atom_local.accounting["target_tokens"])
        for stage, batches in (("D1", self.prepared.batches[:256]), ("D2", self.prepared.batches[256:])):
            for arm, attribute in (("CLOSED", "closed"), ("ATOM_LOCAL", "atom_local")):
                expected = Counter()
                for batch in batches:
                    expected.update(getattr(batch, attribute).accounting)
                self.assertEqual(self.receipt["accounting_by_stage"][stage][arm], dict(expected))

    def test_receipts_bind_exact_bytes_and_token_ids(self):
        self.assertEqual(sha256(self.prepared.receipt_bytes).hexdigest(), self.prepared.receipt_sha256)
        self.assertEqual(canonical_json(self.receipt), self.prepared.receipt_bytes)
        for pair, unit in zip(self.prepared.tokenized_pairs, self.receipt["units"]):
            self.assertEqual(bytes.fromhex(unit["target_bytes_hex"]), pair.closed.record.unit.target_bytes)
            self.assertEqual(unit["target"]["sha256"], pair.closed.record.unit.target_sha256)
            for row in (pair.closed, pair.atom_local):
                receipt = unit["arms"][row.record.arm]
                for name, raw, ids in (
                    ("context", row.context_roundtrip_bytes, row.context_ids),
                    ("target_with_eos", row.target_roundtrip_bytes, row.target_ids),
                    ("suffix", row.suffix_roundtrip_bytes, row.suffix_ids),
                    ("sequence", row.sequence_roundtrip_bytes, row.input_ids),
                ):
                    self.assertEqual(receipt["components"][name], {
                        "byte_count": len(raw), "sha256": sha256(raw).hexdigest(),
                        "token_count": len(ids), "ids_sha256": sha256(canonical_json(list(ids))).hexdigest(),
                    })
                self.assertFalse(row.native_tokenizer_validated)
        self.assertEqual(self.receipt["caller_obligations"], list(source.CALLER_OBLIGATIONS))

    def test_rejects_roster_master_tape_and_hash_drift_before_tokenizer(self):
        damaged = (
            replace(self.compiled, paired_targets=self.compiled.paired_targets[:-1]),
            replace(self.compiled, paired_targets=tuple(reversed(self.compiled.paired_targets))),
            replace(self.compiled, batches=self.compiled.batches[:-1]),
            replace(self.compiled, master_sha256="0" * 64),
            replace(self.compiled, target_hashes={}),
            replace(self.compiled, command_counts={}),
        )
        for compiled in damaged:
            with self.subTest(compiled=compiled.master_sha256), self.assertRaises(ValueError):
                source.prepare_birth(validated_curriculum=compiled, tokenizer=object(), master=MASTER,
                                     padding_policy="PER_ARM_MAX")
        for policy in (None, "AUTO", 16384):
            with self.assertRaisesRegex(ValueError, "explicit_measured_padding"):
                source.prepare_birth(validated_curriculum=self.compiled, tokenizer=object(), master=MASTER,
                                     padding_policy=policy)

    def test_shared_measured_widths_delegate_then_propagate_failure_without_retry(self):
        class StopAfterFirstBatch(Exception):
            pass

        def capture(presentation, pairs, **kwargs):
            self.assertEqual(presentation, self.compiled.batches[0])
            self.assertEqual(tuple(pair.closed.unit.unit_id for pair in pairs), presentation.unit_ids)
            first = self.prepared.batches[0]
            expected = max(first.closed.padding_length, first.atom_local.padding_length)
            self.assertEqual(kwargs["closed_padding_length"], expected)
            self.assertEqual(kwargs["atom_local_padding_length"], expected)
            self.assertEqual(kwargs["count_basis"], source.COUNT_BASIS)
            raise StopAfterFirstBatch

        with patch.object(source.tokenization, "prepare_paired_batch", side_effect=capture) as prepare:
            with self.assertRaises(StopAfterFirstBatch):
                source.prepare_birth(validated_curriculum=self.compiled, tokenizer=FakeTokenizer(),
                                     master=MASTER, padding_policy="SHARED_MAX")
            self.assertEqual(prepare.call_count, 1)

    def test_shared_full_plan_retains_targets_and_validator_fingerprint(self):
        original = source.training.validate_batches
        with patch.object(source.training, "validate_batches", wraps=original) as validate:
            shared = source.prepare_birth(validated_curriculum=self.compiled, tokenizer=FakeTokenizer(),
                                          master=MASTER, padding_policy="SHARED_MAX")
        self.assertEqual(validate.call_count, 1)
        self.assertIs(validate.call_args.args[0], shared.batches)
        self.assertEqual(validate.call_args.kwargs, {"master": MASTER})
        self.assertNotEqual(shared.tape_fingerprint, self.prepared.tape_fingerprint)
        self.assertNotEqual(shared.receipt_sha256, self.prepared.receipt_sha256)
        for before, after in zip(self.prepared.batches, shared.batches):
            self.assertEqual(after.closed.padding_length, after.atom_local.padding_length)
            self.assertEqual(after.closed.padding_length,
                             max(before.closed.padding_length, before.atom_local.padding_length))
            self.assertEqual(before.closed.records, after.closed.records)
            self.assertEqual(before.atom_local.records, after.atom_local.records)
            self.assertEqual(before.target_hashes, after.target_hashes)
        self.assertEqual(json.loads(shared.receipt_bytes)["units"], self.receipt["units"])

    def test_validator_rejection_is_not_replaced_with_a_receipt(self):
        with patch.object(source.training, "validate_batches", side_effect=ValueError("validator rejected")) as validate:
            with self.assertRaisesRegex(ValueError, "validator rejected"):
                source.prepare_birth(validated_curriculum=self.compiled, tokenizer=FakeTokenizer(),
                                     master=MASTER, padding_policy="PER_ARM_MAX")
            self.assertEqual(validate.call_count, 1)

    def test_fake_template_boundary_failure_propagates(self):
        class MissingSuffixTokenizer(FakeTokenizer):
            def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                                    truncation=False, padding=False):
                rendered = super().apply_chat_template(
                    messages, tokenize=tokenize, add_generation_prompt=add_generation_prompt,
                    truncation=truncation, padding=padding,
                )
                return rendered if add_generation_prompt else rendered[:-1]

        with self.assertRaisesRegex(ValueError, "chat_template_boundary"):
            source.prepare_birth(validated_curriculum=self.compiled, tokenizer=MissingSuffixTokenizer(),
                                 master=MASTER, padding_policy="PER_ARM_MAX")

    def test_inconsistent_retokenization_rejected(self):
        original = source.tokenization.prepare_paired_batch

        def changed(*args, **kwargs):
            batch = original(*args, **kwargs)
            row = replace(batch.closed.records[0], count_basis="SYNTHETIC_FIXTURE")
            return replace(batch, closed=replace(batch.closed, records=(row,) + batch.closed.records[1:]))

        with patch.object(source.tokenization, "prepare_paired_batch", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "tokenizer_changed_after_measurement"):
                source.prepare_birth(validated_curriculum=self.compiled, tokenizer=FakeTokenizer(),
                                     master=MASTER, padding_policy="PER_ARM_MAX")


class SourceAdapterTests(unittest.TestCase):
    def test_allocation_delegates_once_only_when_explicitly_called(self):
        sentinel = object()
        with patch.object(source.allocation, "allocate_stage2a", return_value=sentinel) as allocate:
            self.assertIs(source.allocate_source(master=MASTER), sentinel)
            allocate.assert_called_once_with(master=MASTER)
        with patch.object(source.allocation, "allocate_stage2a", side_effect=ValueError("no retry")) as allocate:
            with self.assertRaisesRegex(ValueError, "no retry"):
                source.allocate_source(master=MASTER)
            self.assertEqual(allocate.call_count, 1)

    def test_compiler_adapter_preserves_master_and_binding_identity(self):
        worlds = {"synthetic": object()}
        bound = SimpleNamespace(role_tokens_by_world=lambda domain: worlds if domain == "birth_train" else None)
        with patch.object(source.curriculum_api, "compile_birth_curriculum", return_value=worlds) as compile_call:
            self.assertIs(source.compile_source_curriculum(bound_allocation=bound, master=MASTER), worlds)
            compile_call.assert_called_once_with(role_tokens_by_world=worlds, master=MASTER)

    def test_reduced_held_maps_bound_worlds_and_no_new_canary_roles(self):
        domains = {domain: fixtures(domain) for domain in ("dose_chain", "dose_intervention")}
        prefixes = {"node": "N", "query": "Q", "port": "P", "event": "E"}
        tokens = {role: "M2A" + prefixes[role.rsplit("/", 1)[1]] + "_" + base64.b32encode(
            sha256(b"synthetic-native-prepare-canary/" + role.encode("ascii")).digest())[:12].decode("ascii")
                  for role in source.canary_api.canary_roles()}
        bound = SimpleNamespace(role_tokens_by_world=domains.__getitem__,
                                role_tokens_by_domain={"generic_canary": tokens})
        with patch.object(source.allocation, "allocate_stage2a", side_effect=AssertionError("no allocation")):
            result = source.prepare_reduced_held(bound_allocation=bound)
        self.assertEqual(tuple(result.chains), (0, 4, 8, 12, 16, 20, 24, 28))
        self.assertEqual(tuple(world.world for world in result.chains.values()),
                         tuple(f"h{task // 2:02d}" for task in range(0, 32, 4)))
        self.assertEqual(tuple(result.interventions), tuple((skill, pair)
                         for skill in ("SEEK", "PROSPECT", "CHECK", "CONTINUE") for pair in (0, 2, 4, 6)))
        self.assertEqual(tuple(canary.index for canary in result.canaries), tuple(range(16)))
        self.assertEqual(tuple(canary.target for canary in result.canaries[12:]), ("STOP",) * 4)
        self.assertEqual(len(tokens), 12)
        screen_runtime._bindings(source.screen.reduced_screen("D1"), result.chains,
                                 result.interventions, result.canaries)
        self.assertEqual(sha256(result.receipt_bytes).hexdigest(), result.receipt_sha256)
        receipt = json.loads(result.receipt_bytes)
        self.assertEqual(len(receipt["role_bindings"]), 24)
        with self.assertRaises(TypeError):
            result.chains[0] = None
        with self.assertRaises(TypeError):
            result.interventions[("SEEK", 0)] = None


if __name__ == "__main__":
    unittest.main()
