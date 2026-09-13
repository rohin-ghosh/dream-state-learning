"""EVENT-only schedule and unchanged numerical-helper dispatch, CPU only."""

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_astra_pcfl_event_prefix_import import archived_fixture, reseal
from organism_v6 import pcfl_event_only_train as event


class SyntheticTokenizer:
    chat_template = "SYNTHETIC_MASK_TEST_NOT_NATIVE_QUALIFICATION"
    eos_token_id = 1

    def encode(self, text, add_special_tokens=False):
        payload = text.encode()
        return [2 + hashlib.sha256(payload[start:start + 8]).digest()[0] for start in range(0, len(payload), 8)]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = "".join(message["role"] + ": " + message["content"] + "\n" for message in messages) + "assistant: "
        return self.encode(text) if tokenize else text


class EventWriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.imported = archived_fixture()[2]
        cls.schedule = event.build_schedule(cls.imported, cls.imported["sha256"])
        original = event.prefix._json(cls.imported["evidence"]["files"]["manifest.json"])["binding"]
        cls.binding = {key: copy.deepcopy(original[key]) for key in event.BINDING_FIELDS - {"authority_sha256", "sources"}}
        cls.binding.update(authority_sha256="a" * 64, sources=event.source_snapshot())
        cls.fit = event.build_fit(cls.imported, cls.imported["sha256"], cls.schedule, cls.schedule["sha256"], cls.binding)

    def test_exact_14_plus_6_deterministic_replay(self):
        schedule = event.build_schedule(self.imported, self.imported["sha256"])
        self.assertEqual(schedule, self.schedule)
        slots = schedule["corpus"]["slots"]
        self.assertEqual(len(slots), 20)
        self.assertEqual([slot["source"] for slot in slots[:14]], [None] * 14)
        self.assertEqual(schedule["replay"]["selected"], [f"s{index:02}" for index in range(8, 14)])
        self.assertEqual(set(schedule["replay"]["support_counts"].values()), {3})
        self.assertTrue(all(slot["row_type"] == "EVENT" and slot["taint"] == "AUTHENTIC" for slot in slots))
        self.assertEqual({slot["request"] for slot in slots[:14]}, set(self.imported["queries"]))

    def test_200_updates_800_presentations_disjoint_batches_w0_to_w7(self):
        epochs = self.schedule["epochs"]
        self.assertEqual(sum(len(epoch) for epoch in epochs), 200)
        self.assertEqual(sum(len(batch) for epoch in epochs for batch in epoch), 800)
        slots = {slot["id"]: slot for slot in self.schedule["corpus"]["slots"]}
        for epoch in epochs:
            self.assertEqual({tuple(pair) for batch in epoch for pair in batch}, {(name, view) for name in slots for view in range(8)})
            for batch in epoch:
                support = [handle for name, view in batch for handle in slots[name]["support"]]
                self.assertEqual(len(support), len(set(support)))
        self.assertTrue(all(epoch == epochs[0] for epoch in epochs))

    def test_read_roster_w0_w8_and_predeclared_endpoint(self):
        roster = event.read_roster(self.imported)
        self.assertEqual(len(roster), 28)
        self.assertEqual({item["view"] for item in roster}, {0, 8})
        self.assertEqual(len({item["id"] for item in roster}), 28)
        self.assertEqual(event.ENDPOINT, {"views": [0, 8], "queries_per_view": 14, "calls_per_arm": 28,
            "calls_total": 56, "primary_view": 8, "exact_service_required": 14, "auth_min": 13,
            "c0_max": 1, "paired_gain_min": 12, "stop_required": True, "full_bank_threshold_applied": False})

    def test_schedule_order_replay_and_recipe_drift_rejected(self):
        mutations = [lambda value: value["epochs"][0][0].reverse(),
                     lambda value: value["corpus"]["slots"][-1].update(source="s00"),
                     lambda value: value["recipe"].update(learning_rate=1e-4),
                     lambda value: value.update(batch_seed=True)]
        for mutation in mutations:
            schedule = copy.deepcopy(self.schedule)
            mutation(schedule)
            schedule = reseal(schedule)
            with self.assertRaises(ValueError):
                event.build_fit(self.imported, self.imported["sha256"], schedule, schedule["sha256"], self.binding)

    def test_original_fresh_base_seeds_tokenizer_environment_and_source_pins(self):
        for key, value in (("base_state_sha256", "d" * 64), ("init_seed", 1), ("init_seed", False),
                           ("dropout_seed", 1), ("environment", {}), ("tokenizer_receipt", {}), ("sources", {})):
            with self.subTest(key=key, value=value):
                binding = {**self.binding, key: value}
                with self.assertRaises(ValueError):
                    event.build_fit(self.imported, self.imported["sha256"], self.schedule, self.schedule["sha256"], binding)

    def test_resealed_endpoint_or_target_mutations_rejected(self):
        for mutation in (lambda value: value["endpoint"].update(auth_min=12),
                         lambda value: value["read_roster"].pop(),
                         lambda value: value["binding"].update(learning_rate=0),
                         lambda value: value.update(full_contract_released=True)):
            fit = copy.deepcopy(self.fit)
            mutation(fit)
            fit = reseal(fit)
            with self.assertRaises(ValueError):
                event.validate_fit(fit)

    def test_generation_lineage_is_real_and_unchanged(self):
        event.writer._lineage({}, self.schedule["corpus"], self.imported["rows"], self.imported["generations"], [])
        generations = copy.deepcopy(self.imported["generations"])
        generations[0]["origin"] = "TEACHER"
        with self.assertRaises(ValueError):
            event.writer._lineage({}, self.schedule["corpus"], self.imported["rows"], generations, [])

    def test_encode_dispatch_uses_fixed_actual_queries_and_registry(self):
        tokenizer = object()
        with patch.object(event.prefix, "verify_tokenizer") as qualification, patch.object(event.writer, "_encode_corpus", return_value={"fixture": True}) as encode:
            self.assertEqual(event.encode_fit(self.fit, tokenizer), {"fixture": True})
            qualification.assert_called_once_with(self.imported, tokenizer)
            encode.assert_called_once_with(self.fit["sha256"], self.schedule["corpus"], self.schedule["epochs"],
                self.imported["queries"], event.core.registries()["render_registry"],
                self.binding["environment"]["chat_template_sha256"], tokenizer)

    def test_unchanged_encoder_masks_eos_no_links_or_w8(self):
        tokenizer = SyntheticTokenizer()
        encoded = event.writer._encode_corpus(self.fit["sha256"], self.schedule["corpus"], self.schedule["epochs"],
            self.imported["queries"], event.core.registries()["render_registry"], event.core.byte_hash(tokenizer.chat_template), tokenizer)
        self.assertEqual(len(encoded["items"]), 160)
        self.assertEqual({item["view"] for item in encoded["items"]}, set(range(8)))
        for item in encoded["items"]:
            payload = item["encoded"]
            self.assertFalse(payload["context_dropped"])
            self.assertFalse(payload["target_dropped"])
            self.assertEqual(payload["ids"][-1], tokenizer.eos_token_id)
            self.assertEqual(payload["labels"][-1], tokenizer.eos_token_id)
            self.assertTrue(any(label == -100 for label in payload["labels"]))
            self.assertTrue(all(label == -100 or label == token for label, token in zip(payload["labels"], payload["ids"])))
            self.assertIn(item["target_sha256"], {query["target_sha256"] for query in self.imported["queries"].values()})

    def test_unchanged_encoder_rejects_truncation(self):
        tokenizer = SyntheticTokenizer()
        tokenizer.encode = lambda text, add_special_tokens=False: [2] * 600
        with self.assertRaisesRegex(ValueError, "truncation"):
            event.writer._encode_corpus(self.fit["sha256"], self.schedule["corpus"], self.schedule["epochs"],
                self.imported["queries"], event.core.registries()["render_registry"], event.core.byte_hash(tokenizer.chat_template), tokenizer)

    def test_train_dispatch_preserves_numerical_loop_and_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "fit"
            base_factory, tokenizer = Mock(), object()
            with patch.object(event, "encode_fit", return_value={"synthetic_encoding": True}) as encode, patch.object(event.writer, "_train_encoded", return_value={"dispatch_only": True}) as train:
                self.assertEqual(event.train_fit(self.fit, tokenizer, base_factory, out), {"dispatch_only": True})
                encode.assert_called_once_with(self.fit, tokenizer)
                train.assert_called_once_with(self.fit, {"synthetic_encoding": True}, base_factory, out,
                    self.binding["environment"], event.validate_fit(self.fit), report_name="event_only_scope_report.json")
            base_factory.assert_not_called()

    def test_invalid_or_unqualified_input_cannot_load_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "fit"
            base_factory = Mock()
            with patch.object(event.writer, "_train_encoded") as train:
                fit = copy.deepcopy(self.fit)
                fit["binding"]["base_state_sha256"] = "d" * 64
                with self.assertRaises(ValueError):
                    event.train_fit(fit, object(), base_factory, out)
                with patch.object(event.prefix, "verify_tokenizer", side_effect=ValueError("qualification absent")):
                    with self.assertRaisesRegex(ValueError, "qualification absent"):
                        event.train_fit(self.fit, object(), base_factory, out)
                train.assert_not_called()
            base_factory.assert_not_called()
            self.assertFalse(out.exists())

    def test_existing_output_rejected_without_encoder_or_base_call(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(event, "encode_fit") as encode:
            base_factory = Mock()
            with self.assertRaisesRegex(ValueError, "fresh EVENT-only"):
                event.train_fit(self.fit, object(), base_factory, temporary)
            encode.assert_not_called()
            base_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
