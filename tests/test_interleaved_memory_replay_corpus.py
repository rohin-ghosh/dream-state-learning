"""Stdlib CPU fixtures exercising actual V3 encoding, group order and collation."""
from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import interleaved_memory_replay_corpus as corpus


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        return ("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n"
            "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n")

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        tokens = []
        for index, piece in enumerate(text.split("<|im_end|>")):
            if index:
                tokens.append(self.eos_token_id)
            tokens.extend(ord(character) + 2 for character in piece)
        return tokens


def original_native(tokenizer):
    return dict(corpus=[dict(spans=[[corpus.prior.render(tokenizer, row["context"]), False, "context"],
        [row["response"], True, "authored_birth_target"]], group=row["case_id"], view=row["kind"], order=index,
        meta=dict(source_event_ids=row["source_event_ids"][:])) for index, row in enumerate(corpus.prior.original_rows())])


class InterleavedMemoryReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = corpus.build_candidate()
        cls.native = original_native(Tokenizer())
        cls.exported = corpus.export_native(cls.candidate, cls.native, Tokenizer())

    def test_fixed_original_selection(self):
        legacy = corpus.prior.build_candidate()
        self.assertEqual(self.candidate["selected_case_ids"], legacy["selected_case_ids"])
        self.assertEqual(set(self.candidate["selected_case_ids"]), set(corpus.prior.MEMORY_IDS + corpus.prior.ADDITION_IDS))
        self.assertEqual(self.candidate["source_records"], legacy["source_records"])
        self.assertEqual(corpus.validate_candidate(self.candidate)["selected_sources"], 32)

    def test_original_strings_targets_events_unchanged(self):
        legacy = corpus.prior.build_candidate()
        for arm in corpus.ARMS:
            expected = {row["id"]: row for row in legacy["arms"][arm]}
            for row in self.candidate["arms"][arm]:
                self.assertEqual({key: value for key, value in row.items() if key not in ("batch_group", "batch_slot")},
                    expected[row["id"]])

    def test_four_copies_thirtytwo_balanced_groups(self):
        for arm in corpus.ARMS:
            rows = self.candidate["arms"][arm]
            self.assertEqual(Counter(row["case_id"] for row in rows), {key: 4 for key in self.candidate["selected_case_ids"]})
            groups, source_groups = defaultdict(list), defaultdict(set)
            for row in rows:
                groups[row["batch_group"]].append(row)
                source_groups[row["case_id"]].add(row["batch_group"])
            self.assertEqual(len(groups), 32)
            self.assertEqual(set(map(len, source_groups.values())), {4})
            for group in groups.values():
                self.assertEqual(len({row["case_id"] for row in group}), 4)
                self.assertEqual(Counter(row["kind"] for row in group), {"memory": 2, "addition": 2})

    def test_paired_everything_except_memory_context(self):
        for single, four in zip(self.candidate["arms"]["SINGLE_VIEW"], self.candidate["arms"]["FOUR_VIEW"]):
            self.assertEqual({key: value for key, value in single.items() if key != "context"},
                {key: value for key, value in four.items() if key != "context"})
            if single["kind"] == "addition":
                self.assertEqual(single, four)

    def test_all_seeds_epochs_actual_distinct_steps(self):
        schedules = self.exported["audit"]["optimizer_update_schedule"]
        self.assertEqual(set(schedules), {"0", "1", "2"})
        for schedule in schedules.values():
            self.assertEqual(len(schedule), 320)
            for epoch in range(10):
                steps, copies = defaultdict(set), defaultdict(list)
                batches = [batch for batch in schedule if batch["epoch"] == epoch]
                self.assertEqual(len(batches), 32)
                self.assertEqual(sorted(index for batch in batches for index in batch["item_indices"]), list(range(128)))
                for batch in batches:
                    self.assertEqual(len(set(batch["source_ids"])), 4)
                    raw = self.candidate["arms"]["SINGLE_VIEW"]
                    checks = self.exported["audit"]["arms"]["SINGLE_VIEW"]["rows"]
                    self.assertEqual(batch["target_tokens_by_kind"], {kind: sum(checks[index]["target_tokens"]
                        for index in batch["item_indices"] if raw[index]["kind"] == kind) for kind in ("memory", "addition")})
                    for key, copy_index in zip(batch["source_ids"], batch["copy_indices"]):
                        steps[key].add(batch["batch"])
                        copies[key].append(copy_index)
                self.assertEqual(set(map(len, steps.values())), {4})
                self.assertTrue(all(sorted(value) == list(range(4)) for value in copies.values()))
        self.assertNotEqual(schedules["0"], schedules["1"])
        self.assertNotEqual(schedules["1"], schedules["2"])

    def test_schedule_matches_direct_trainer_invocation(self):
        items = self.exported["corpora"]["FOUR_VIEW"]["corpus"]
        segments = [corpus.prior.encode_row(item, Tokenizer(), index)[0] for index, item in enumerate(items)]
        packs = corpus.trainer.pack_by_group(segments, 512, pack=False)
        for seed in corpus.SEEDS:
            for epoch in range(10):
                actual = corpus.trainer.epoch_order(packs, seed, epoch, True)
                recorded = [batch for batch in self.exported["audit"]["optimizer_update_schedule"][str(seed)] if batch["epoch"] == epoch]
                self.assertEqual([pack[0].item_index for pack in actual], [index for batch in recorded for index in batch["item_indices"]])

    def test_exact_target_bytes_eos_masks_and_sources(self):
        for arm in corpus.ARMS:
            rows = self.exported["audit"]["arms"][arm]["rows"]
            items = self.exported["corpora"][arm]["corpus"]
            for row, item, raw in zip(rows, items, self.candidate["arms"][arm]):
                self.assertEqual(item["spans"][1], [raw["response"], True, "authored_birth_target"])
                self.assertEqual(item["meta"]["source_event_ids"], raw["source_event_ids"])
                self.assertEqual(row["target_with_eos"], Tokenizer().encode(raw["response"], add_special_tokens=False) + [900])
                self.assertEqual(row["labels"], [-100] * len(row["prefix_token_ids"]) + row["target_with_eos"])
                self.assertEqual(row["input_ids"], row["prefix_token_ids"] + row["target_with_eos"])
                self.assertFalse(item["spans"][0][1])
                self.assertEqual(item["group"], raw["batch_group"])
                self.assertEqual(item["order"], raw["batch_slot"])

    def test_original_and_paired_token_targets(self):
        single = self.exported["audit"]["arms"]["SINGLE_VIEW"]["rows"]
        four = self.exported["audit"]["arms"]["FOUR_VIEW"]["rows"]
        for left, right, raw in zip(single, four, self.candidate["arms"]["SINGLE_VIEW"]):
            baseline = corpus.prior.encode_row(self.native["corpus"][raw["source_row_index"]], Tokenizer(), 0)[1]
            self.assertEqual(left["prefix_token_ids"], baseline["prefix_token_ids"])
            self.assertEqual(left["target_with_eos"], right["target_with_eos"])
            self.assertEqual(left["response_utf8_sha256"], right["response_utf8_sha256"])
            if raw["kind"] == "addition":
                self.assertEqual(left, right)

    def test_costs_and_recipe_not_compute_matched(self):
        audit = self.exported["audit"]
        for arm in corpus.ARMS:
            counts = audit["arms"][arm]
            self.assertEqual(counts["ten_epochs"], {key: 10 * value for key, value in counts["per_epoch"].items()})
            for seed in ("0", "1", "2"):
                self.assertEqual(audit["scheduled_costs"][seed][arm]["source_presentations"],
                    {key: 40 for key in self.candidate["selected_case_ids"]})
        self.assertFalse(audit["compute_matched"])
        self.assertFalse(audit["packing"])
        self.assertFalse(audit["truncation"])
        self.assertEqual(audit["arms"]["SINGLE_VIEW"]["ten_epochs"]["target_tokens"],
            audit["arms"]["FOUR_VIEW"]["ten_epochs"]["target_tokens"])
        self.assertNotEqual(audit["arms"]["SINGLE_VIEW"]["ten_epochs"]["input_tokens"],
            audit["arms"]["FOUR_VIEW"]["ten_epochs"]["input_tokens"])
        self.assertEqual((corpus.RECIPE["lr"], corpus.RECIPE["rank"], corpus.RECIPE["alpha"], corpus.RECIPE["dropout"]),
            (3e-4, 8, 16, .05))
        self.assertEqual((corpus.RECIPE["epochs"], corpus.RECIPE["batch_size"], corpus.RECIPE["grad_accum"]), (10, 4, 1))
        self.assertIn("ORIGINAL_TEACHING_PARENT_INDEPENDENT", corpus.RECIPE["initialization"])

    def test_fresh_cues_no_labels_and_not_independent_facts(self):
        heldout = self.candidate["heldout_cues"]
        self.assertEqual(len(heldout), 48)
        self.assertEqual(len({row["device"] for row in heldout}), 16)
        self.assertEqual(Counter(row["family"] for row in heldout), {0: 16, 1: 16, 2: 16})
        for row in heldout:
            self.assertNotRegex(row["context"].lower(), r"\b(blue|green|red|yellow|unknown)\b")
            self.assertEqual(row["context"].count(row["device"]), 1)
        self.assertFalse(self.candidate["manifest"]["heldout_model_outputs_inspected"])
        self.assertEqual(self.candidate["manifest"]["existing_confirmation_cases_exported"], 0)

    def test_heldout_prefix_only_never_training(self):
        for row, audit in zip(self.candidate["heldout_cues"], self.exported["audit"]["heldout_prefixes"]):
            self.assertEqual(audit["rendered_context"], corpus.prior.render(Tokenizer(), row["context"]))
            self.assertEqual(audit["prefix_token_ids"], Tokenizer().encode(audit["rendered_context"], add_special_tokens=False))
            self.assertEqual(set(audit), {"id", "rendered_context", "prefix_token_ids"})
        for arm in corpus.ARMS:
            contexts = {item["spans"][0][0] for item in self.exported["corpora"][arm]["corpus"]}
            self.assertTrue(contexts.isdisjoint(row["rendered_context"] for row in self.exported["audit"]["heldout_prefixes"]))

    def test_existing_cue_wording_rejected(self):
        with patch.object(corpus, "HELDOUT_TEMPLATES", (corpus.prior.MEMORY_TEMPLATES[0], *corpus.HELDOUT_TEMPLATES[1:])):
            with self.assertRaisesRegex(ValueError, "wording reused"):
                corpus.validate_candidate(corpus.build_candidate())

    def test_existing_dev_cue_rejected(self):
        with patch.object(corpus, "HELDOUT_TEMPLATES", (corpus.original.MEMORY_QUESTIONS[0], *corpus.HELDOUT_TEMPLATES[1:])):
            with self.assertRaisesRegex(ValueError, "wording reused"):
                corpus.validate_candidate(corpus.build_candidate())

    def test_duplicate_cue_families_rejected(self):
        with patch.object(corpus, "HELDOUT_TEMPLATES", (corpus.HELDOUT_TEMPLATES[0],) * 3):
            with self.assertRaisesRegex(ValueError, "cue collision"):
                corpus.validate_candidate(corpus.build_candidate())

    def test_cue_label_leak_rejected(self):
        with patch.object(corpus, "HELDOUT_TEMPLATES", ("Is {device} red?", *corpus.HELDOUT_TEMPLATES[1:])):
            with self.assertRaisesRegex(ValueError, "label leakage"):
                corpus.validate_candidate(corpus.build_candidate())

    def test_unsupported_mutations_rejected(self):
        for key, value in (("context", "another context"), ("response", "red"), ("case_id", "eval-memory-000-0"),
            ("source_event_ids", ["bad"]), ("copy_index", 9), ("batch_group", "bad"), ("batch_slot", 5)):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.candidate)
                candidate["arms"]["SINGLE_VIEW"][0][key] = value
                with self.assertRaises(ValueError): corpus.validate_candidate(candidate)
        for key in ("lr", "epochs", "rank"):
            with self.subTest(recipe=key):
                candidate = copy.deepcopy(self.candidate)
                candidate["manifest"]["recipe"][key] = -1
                with self.assertRaises(ValueError): corpus.validate_candidate(candidate)

    def test_reproducible_without_global_rng_mutation(self):
        before = random.getstate()
        self.assertEqual(corpus.build_candidate(), self.candidate)
        self.assertEqual(corpus.export_native(self.candidate, self.native, Tokenizer()), self.exported)
        self.assertEqual(random.getstate(), before)

    def test_original_native_prefix_group_target_mismatch(self):
        for key in ("spans", "group", "order", "meta"):
            with self.subTest(key=key):
                native = copy.deepcopy(self.native)
                native["corpus"][0][key] = [] if key == "spans" else "bad"
                with self.assertRaisesRegex(ValueError, "original80 native"):
                    corpus.export_native(self.candidate, native, Tokenizer())

    def test_bad_eos_rejected(self):
        tokenizer = Tokenizer()
        tokenizer.eos_token_id = None
        with self.assertRaisesRegex(ValueError, "EOS/pad"):
            corpus.export_native(self.candidate, self.native, tokenizer)

    def test_no_truncation(self):
        tokenizer = Tokenizer()
        ordinary = tokenizer.encode
        def long_prefix(text, **kwargs):
            return [10] * 513 if "<|im_start|>" in text else ordinary(text, **kwargs)
        with patch.object(tokenizer, "encode", long_prefix), self.assertRaisesRegex(ValueError, "truncate"):
            corpus.export_native(self.candidate, self.native, tokenizer)

    def test_native_shift_mask_corruption_rejected(self):
        ordinary = corpus.trainer.encode_item_segments
        def wrong(*args, **kwargs):
            parts = ordinary(*args, **kwargs)
            first = next(index for index, label in enumerate(parts[0].labels) if label != -100)
            parts[0].labels[first - 1] = 10
            return parts
        with patch.object(corpus.trainer, "encode_item_segments", wrong), self.assertRaisesRegex(ValueError, "mask/shift/EOS"):
            corpus.export_native(self.candidate, self.native, Tokenizer())

    def test_actual_scheduler_drops_rejected(self):
        ordinary = corpus.trainer.epoch_order
        def drop(*args, **kwargs): return ordinary(*args, **kwargs)[:-1]
        with patch.object(corpus.trainer, "epoch_order", drop), self.assertRaisesRegex(ValueError, "epoch dropped"):
            corpus.export_native(self.candidate, self.native, Tokenizer())

    def test_actual_scheduler_batch_corruption_rejected(self):
        ordinary = corpus.trainer.epoch_order
        def reverse(*args, **kwargs): return list(reversed(ordinary(*args, **kwargs)))
        with patch.object(corpus.trainer, "epoch_order", reverse), self.assertRaisesRegex(ValueError, "actual V3 batch"):
            corpus.export_native(self.candidate, self.native, Tokenizer())

    def test_fresh_emit_verify_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "material"
            manifest = corpus.emit_candidate(root)
            self.assertEqual(manifest["protocol"], corpus.PROTOCOL)
            self.assertTrue(corpus.verify(root)["valid"])
            with self.assertRaises(FileExistsError): corpus.emit_candidate(root)
            with (root / "candidate.json").open("ab") as stream: stream.write(b" ")
            with self.assertRaisesRegex(ValueError, "artifact bytes"): corpus.verify(root)

    def test_source_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "material"
            corpus.emit_candidate(root)
            with patch.object(corpus, "source_hashes", return_value={}):
                with self.assertRaisesRegex(ValueError, "source hashes"): corpus.verify(root)

    def test_symlink_output_and_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = root / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"): corpus.emit_candidate(alias / "new")
            material = root / "material"
            corpus.emit_candidate(material)
            (material / "extra").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "inventory"): corpus.verify(material)

    def test_native_prepare_pinned_bytes_fresh_output_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            teach = Path(tmp) / "teach.json"
            teach.write_bytes(corpus.encoded(self.native))
            root = Path(tmp) / "material"
            with patch.object(corpus.prior, "ORIGINAL_TEACH_SHA256", corpus.digest(teach.read_bytes())):
                manifest = corpus.prepare(root, teach, Tokenizer())
                self.assertTrue(corpus.verify(root)["valid"])
                self.assertEqual(manifest["seeds"], [0, 1, 2])
                self.assertEqual(set(manifest["sha256"]), {"candidate.json", "token_audit.json", "SINGLE_VIEW.json", "FOUR_VIEW.json"})
                self.assertFalse(manifest["native_identity_authenticated"])
                with self.assertRaises(FileExistsError): corpus.prepare(root, teach, Tokenizer())
            with self.assertRaisesRegex(ValueError, "bytes/hash"):
                corpus.prepare(Path(tmp) / "bad", teach, Tokenizer())
            self.assertFalse((Path(tmp) / "bad").exists())

    def test_prepare_mutated_source_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            teach = Path(tmp) / "teach.json"
            teach.write_bytes(corpus.encoded(self.native))
            root = Path(tmp) / "material"
            ordinary = corpus.export_native
            def mutate(*args):
                exported = ordinary(*args)
                teach.write_bytes(b"changed")
                return exported
            with patch.object(corpus.prior, "ORIGINAL_TEACH_SHA256", corpus.digest(teach.read_bytes())), \
                patch.object(corpus, "export_native", mutate):
                with self.assertRaisesRegex(ValueError, "source changed"): corpus.prepare(root, teach, Tokenizer())
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
