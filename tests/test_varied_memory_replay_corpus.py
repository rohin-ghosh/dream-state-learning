"""CPU fixtures only; actual V3 pure encoding/order helpers, no model dependency."""
from collections import Counter
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import varied_memory_replay_corpus as corpus


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def __init__(self):
        self.messages = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        self.messages.append(copy.deepcopy(messages))
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
    return dict(corpus=[dict(spans=[[tokenizer.apply_chat_template([dict(role="user", content=row["context"])],
        tokenize=False, add_generation_prompt=True), False, "context"], [row["response"], True, "authored_birth_target"]],
        group=row["case_id"], view=row["kind"], order=index, meta=dict(source_event_ids=row["source_event_ids"][:]))
        for index, row in enumerate(corpus.original.build_candidate()["train_teach"])])


class VariedMemoryReplayTests(unittest.TestCase):
    def setUp(self):
        self.candidate = corpus.build_candidate()
        self.tokenizer = Tokenizer()
        self.original = original_native(self.tokenizer)

    def export(self, seeds=(0,)):
        return corpus.export_native(self.candidate, self.original, self.tokenizer, seeds)

    def test_fixed_first16_selection_and_original_order(self):
        original = corpus.original.build_candidate()["train_teach"]
        arithmetic = [row["case_id"] for row in original if row["kind"] == "addition"][:16]
        self.assertEqual(tuple(arithmetic), corpus.ADDITION_IDS)
        selected = set(arithmetic) | set(corpus.MEMORY_IDS)
        self.assertEqual(self.candidate["selected_case_ids"], [row["case_id"] for row in original if row["case_id"] in selected])
        self.assertEqual(corpus.validate_candidate(self.candidate)["selected_sources"], 32)

    def test_source_major_four_copies_and_identical_layout(self):
        for arm in corpus.ARMS:
            rows = self.candidate["arms"][arm]
            self.assertEqual(len(rows), 128)
            self.assertEqual(Counter(row["kind"] for row in rows), {"addition": 64, "memory": 64})
            for start in range(0, 128, 4):
                copies = rows[start:start + 4]
                self.assertEqual([row["copy_index"] for row in copies], [0, 1, 2, 3])
                self.assertEqual(len({row["case_id"] for row in copies}), 1)
        for single, varied in zip(self.candidate["arms"]["SINGLE_VIEW"], self.candidate["arms"]["FOUR_VIEW"]):
            self.assertEqual({key: value for key, value in single.items() if key != "context"},
                             {key: value for key, value in varied.items() if key != "context"})
            if single["kind"] == "addition":
                self.assertEqual(single, varied)

    def test_four_predeclared_faithful_memory_views_one_original(self):
        raw = {row["case_id"]: row for row in corpus.original_rows()}
        for case_id in corpus.MEMORY_IDS:
            source = raw[case_id]
            single = [row for row in self.candidate["arms"]["SINGLE_VIEW"] if row["case_id"] == case_id]
            varied = [row for row in self.candidate["arms"]["FOUR_VIEW"] if row["case_id"] == case_id]
            self.assertEqual([row["context"] for row in single], [source["context"]] * 4)
            self.assertEqual([row["context"] for row in varied], [template.format(device=source["device"]) for template in corpus.MEMORY_TEMPLATES])
            self.assertEqual(varied[0]["context"], source["context"])
            self.assertEqual(len({row["context"] for row in varied}), 4)

    def test_valid_source_facts_and_unchanged_target_bytes(self):
        sources = {row["id"]: row for row in self.candidate["source_records"]}
        original = {row["case_id"]: row for row in corpus.original_rows()}
        self.assertEqual(len(sources), 32)
        for arm in corpus.ARMS:
            for row in self.candidate["arms"][arm]:
                event = sources[row["source_event_ids"][0]]
                self.assertEqual(row["response"].encode(), original[row["case_id"]]["response"].encode())
                if row["kind"] == "memory":
                    self.assertEqual(row["response"], event["color"])
                else:
                    self.assertEqual(row["response"], f"PREDICT: {event['left'] + event['right']}\nACT: {event['sum']}")

    def test_no_eval_confirmation_or_label_contexts_exported(self):
        heldout = corpus.original.build_candidate()["eval"]
        output = corpus.encoded(self.candidate).decode()
        for row in heldout:
            self.assertNotIn(row["id"], output)
            self.assertNotIn(json.dumps(row["context"]), output)
        for row in self.candidate["arms"]["FOUR_VIEW"]:
            if row["kind"] == "memory":
                for label in (*corpus.original.COLORS, "unknown"):
                    self.assertNotRegex(row["context"].casefold(), rf"\b{label}\b")

    def test_reproducible_and_no_shared_mutable_copy_state(self):
        before = copy.deepcopy(self.candidate)
        random.seed(555)
        self.assertEqual(corpus.build_candidate(), before)
        self.candidate["arms"]["FOUR_VIEW"][0]["source_event_ids"].append("bad")
        self.assertEqual(self.candidate["arms"]["SINGLE_VIEW"], before["arms"]["SINGLE_VIEW"])
        self.assertEqual(self.candidate["arms"]["FOUR_VIEW"][1], before["arms"]["FOUR_VIEW"][1])

    def test_unsupported_candidate_mutations_rejected(self):
        mutations = ("response", "context", "copy_index", "case_id", "source_event_ids", "source_row_index", "kind")
        for key in mutations:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.candidate)
                changed["arms"]["FOUR_VIEW"][1][key] = "unsupported"
                with self.assertRaisesRegex(ValueError, "fixed authored"):
                    corpus.validate_candidate(changed)
        for field in ("memory_templates", "source_records", "selected_case_ids"):
            changed = copy.deepcopy(self.candidate)
            changed[field].reverse()
            with self.assertRaises(ValueError): corpus.validate_candidate(changed)

    def test_fact_recipe_and_target_whitespace_mutations_rejected(self):
        for mutation in ("fact", "lr", "target"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.candidate)
                if mutation == "fact":
                    changed["source_records"][0]["extra"] = "unsupported"
                elif mutation == "lr":
                    changed["manifest"]["recipe"]["lr"] = 1e-4
                else:
                    changed["arms"]["SINGLE_VIEW"][0]["response"] += " "
                with self.assertRaises(ValueError): corpus.validate_candidate(changed)

    def test_original_source_mutation_rejected_before_native(self):
        changed = corpus.original.build_candidate()
        changed["train_teach"][0]["response"] = "wrong"
        with patch.object(corpus.original, "build_candidate", return_value=changed), self.assertRaisesRegex(ValueError, "original80"):
            corpus.build_candidate()

    def test_native_original_full80_render_masks_groups_checked(self):
        for mutation in ("prefix", "target", "group", "order", "source", "missing"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.original)
                row = changed["corpus"][-1]
                if mutation == "prefix": row["spans"][0][0] += "reminder"
                elif mutation == "target": row["spans"][1][0] += " "
                elif mutation == "group": row["group"] = "wrong"
                elif mutation == "order": row["order"] = -1
                elif mutation == "source": row["meta"]["source_event_ids"] = ["wrong"]
                else: changed["corpus"].pop()
                with self.assertRaisesRegex(ValueError, "original80 native"):
                    corpus.export_native(self.candidate, changed, self.tokenizer, (0,))

    def test_exact_native_prefix_ids_masks_target_eos_and_shift(self):
        exported = self.export()
        for arm in corpus.ARMS:
            for item, check in zip(exported["corpora"][arm]["corpus"], exported["audit"]["arms"][arm]["rows"]):
                target = self.tokenizer.encode(check["response"], add_special_tokens=False) + [self.tokenizer.eos_token_id]
                self.assertEqual(check["input_ids"], check["prefix_token_ids"] + target)
                self.assertEqual(check["labels"], [-100] * len(check["prefix_token_ids"]) + target)
                self.assertEqual(check["labels"].count(self.tokenizer.eos_token_id), 1)
                self.assertEqual(check["input_ids"].count(self.tokenizer.eos_token_id), 3)
                self.assertEqual(check["labels"][len(check["prefix_token_ids"]):], target)
                self.assertEqual(item["meta"]["source_event_ids"], check["source_event_ids"])
                self.assertEqual(item["spans"][1], [check["response"], True, "authored_birth_target"])
        heldout = {row["context"] for row in corpus.original.build_candidate()["eval"]}
        self.assertFalse(any(call[0]["content"] in heldout for call in self.tokenizer.messages))

    def test_native_arithmetic_identical_all_copies_original_preserved(self):
        exported = self.export()
        before = copy.deepcopy(self.original)
        for index, row in enumerate(self.candidate["arms"]["SINGLE_VIEW"]):
            single = exported["corpora"]["SINGLE_VIEW"]["corpus"][index]
            varied = exported["corpora"]["FOUR_VIEW"]["corpus"][index]
            source = self.original["corpus"][row["source_row_index"]]
            self.assertEqual(single["spans"], source["spans"])
            self.assertEqual((single["group"], single["order"], single["view"]), (source["group"], source["order"], source["view"]))
            if row["kind"] == "addition" or row["copy_index"] == 0:
                self.assertEqual(single, varied)
        self.assertEqual(self.original, before)

    def test_token_totals_target_match_but_not_compute_matched(self):
        audit = self.export()["audit"]
        single, varied = (audit["arms"][arm] for arm in corpus.ARMS)
        self.assertEqual(single["ten_epochs"]["target_tokens"], varied["ten_epochs"]["target_tokens"])
        self.assertNotEqual(single["ten_epochs"]["context_tokens"], varied["ten_epochs"]["context_tokens"])
        self.assertFalse(audit["compute_matched"])
        self.assertFalse(audit["native_identity_authenticated"])
        for arm in corpus.ARMS:
            for key, value in audit["arms"][arm]["per_epoch"].items():
                self.assertEqual(audit["arms"][arm]["ten_epochs"][key], value * 10)

    def test_actual_v3_epoch_order_matches_independent_expected_all_seeds(self):
        audit = self.export((0, 1, 2))["audit"]
        for seed in (0, 1, 2):
            expected = []
            for epoch in range(10):
                groups = sorted(self.candidate["selected_case_ids"])
                random.Random(seed * 1000 + epoch).shuffle(groups)
                for group in groups:
                    first = self.candidate["selected_case_ids"].index(group) * 4
                    expected.append(dict(epoch=epoch, group=group, item_indices=list(range(first, first + 4))))
            self.assertEqual(audit["optimizer_update_schedule"][str(seed)], expected)
            self.assertEqual(len(expected), 320)
            for arm in corpus.ARMS:
                self.assertEqual(audit["scheduled_costs"][str(seed)][arm]["source_presentations"],
                    {group: 40 for group in self.candidate["selected_case_ids"]})
        self.assertNotEqual(audit["optimizer_update_schedule"]["0"], audit["optimizer_update_schedule"]["1"])

    def test_invalid_seed_choices_rejected(self):
        for seeds in ((), (3,), (True,), (0, 0), (-1,)):
            with self.subTest(seeds=seeds), self.assertRaisesRegex(ValueError, "caller seeds"):
                self.export(seeds)

    def test_unsafe_shuffle_group_interleave_rejected(self):
        def unsafe(packs, seed, epoch, shuffle_groups):
            return list(reversed(packs))
        with patch.object(corpus.trainer, "epoch_order", unsafe), self.assertRaisesRegex(ValueError, "source group/copy order"):
            self.export()

    def test_native_mask_shift_bug_rejected(self):
        original = corpus.trainer.encode_item_segments
        def bad(*args, **kwargs):
            parts = original(*args, **kwargs)
            first = next(index for index, label in enumerate(parts[0].labels) if label != -100)
            parts[0].labels[first] = -100
            return parts
        with patch.object(corpus.trainer, "encode_item_segments", bad), self.assertRaisesRegex(ValueError, "mask/shift/EOS"):
            self.export()

    def test_missing_or_bad_eos_rejected(self):
        self.tokenizer.eos_token_id = None
        with self.assertRaisesRegex(ValueError, "EOS/pad"): self.export()
        self.tokenizer.eos_token_id = 900
        with patch.object(self.tokenizer, "encode", return_value=[10]), self.assertRaisesRegex(ValueError, "EOS/pad"):
            self.export()

    def test_overlength_native_prefix_rejected_without_truncation(self):
        ordinary = self.tokenizer.encode
        def long(text, **kwargs):
            result = ordinary(text, **kwargs)
            return result * 8 if "<|im_start|>user" in text else result
        with patch.object(self.tokenizer, "encode", long), self.assertRaisesRegex(ValueError, "would truncate"):
            self.export()

    def test_recipe_declares_independent_original_warmstarts_only(self):
        recipe = self.candidate["manifest"]["recipe"]
        self.assertEqual((recipe["rank"], recipe["alpha"], recipe["dropout"], recipe["lr"]), (8, 16, .05, 3e-4))
        self.assertEqual((recipe["epochs"], recipe["batch_size"], recipe["grad_accum"], recipe["intended_updates"]), (10, 4, 1, 320))
        self.assertIn("ORIGINAL_TEACHING_PARENT_INDEPENDENT_PER_ARM", recipe["initialization"])
        self.assertIn("FRESH_OPTIMIZER", recipe["initialization"])
        self.assertIn("SEQ107", recipe["forbidden_parent"])

    def test_fresh_raw_export_and_immutable_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "raw"
            manifest = corpus.emit_candidate(out)
            self.assertEqual(manifest["status"], "RAW_CANDIDATE_TOKEN_AUDIT_PENDING")
            self.assertTrue(corpus.verify(out)["valid"])
            before = {path.name: path.read_bytes() for path in out.iterdir()}
            with self.assertRaises(FileExistsError): corpus.emit_candidate(out)
            self.assertEqual(before, {path.name: path.read_bytes() for path in out.iterdir()})
            (out / "candidate.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "artifact bytes"): corpus.verify(out)

    def test_native_prepare_pins_actual_original_bytes_and_fresh_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "teach.json"
            payload = (json.dumps(self.original, sort_keys=True) + "\n").encode()
            self.assertEqual(corpus.digest(payload), corpus.ORIGINAL_TEACH_SHA256)
            source.write_bytes(payload)
            out = Path(temporary) / "native"
            manifest = corpus.prepare(out, source, self.tokenizer, (0, 1, 2))
            self.assertEqual(manifest["original_teach_sha256"], corpus.ORIGINAL_TEACH_SHA256)
            self.assertEqual(set(manifest["sha256"]), {"candidate.json", "token_audit.json", "SINGLE_VIEW.json", "FOUR_VIEW.json"})
            self.assertTrue(corpus.verify(out)["valid"])
            with self.assertRaises(FileExistsError): corpus.prepare(out, source, self.tokenizer)
            self.assertEqual(source.read_bytes(), payload)
            source.write_bytes(payload + b" ")
            with self.assertRaisesRegex(ValueError, "original native source changed"): corpus.verify(out)
            with self.assertRaisesRegex(ValueError, "original80 teach bytes"):
                corpus.prepare(Path(temporary) / "bad", source, self.tokenizer)
            self.assertFalse((Path(temporary) / "bad").exists())

    def test_manifest_recipe_change_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "out"
            manifest = corpus.emit_candidate(out)
            manifest["recipe"]["epochs"] = 20
            (out / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "manifest recipe"):
                corpus.verify(out)

    def test_raw_manifest_cannot_claim_native_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "out"
            manifest = corpus.emit_candidate(out)
            manifest["status"] = "CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT"
            (out / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "cannot claim native"):
                corpus.verify(out)

    def test_source_change_during_native_audit_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "teach.json"
            source.write_text(json.dumps(self.original, sort_keys=True) + "\n")
            before = corpus.source_hashes()
            after = dict(before, changed="bad")
            out = Path(temporary) / "out"
            with patch.object(corpus, "source_hashes", side_effect=[before, after]), self.assertRaisesRegex(ValueError, "source changed"):
                corpus.prepare(out, source, self.tokenizer, (0,))
            self.assertFalse(out.exists())

    def test_native_audit_failure_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "teach.json"
            source.write_text(json.dumps(self.original, sort_keys=True) + "\n")
            out = Path(temporary) / "out"
            self.tokenizer.eos_token_id = None
            with self.assertRaises(ValueError): corpus.prepare(out, source, self.tokenizer)
            self.assertFalse(out.exists())

    def test_symlink_and_unexpected_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "alias").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"): corpus.emit_candidate(root / "alias" / "out")
            corpus.emit_candidate(root / "out")
            (root / "out" / "unexpected").write_text("x")
            with self.assertRaisesRegex(ValueError, "artifact root"): corpus.verify(root / "out")


if __name__ == "__main__":
    unittest.main()
