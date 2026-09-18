"""CPU mock tokenization with the unmodified V3 encoding and scheduling helpers."""
from collections import Counter
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import sequential_memory_corpus as corpus


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        if text in corpus.original.COLORS:
            return [700 + corpus.original.COLORS.index(text)]
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


class SequentialMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = corpus.build_candidate()
        cls.native = original_native(Tokenizer())
        cls.exported = corpus.export_native(cls.candidate, cls.native, Tokenizer())

    def test_deterministic_sources_and_independent_predetermined_maps(self):
        self.assertEqual(self.candidate, corpus.build_candidate())
        self.assertTrue(corpus.validate_candidate(self.candidate)["valid"])
        inventories = {event["bank"]: event for event in self.candidate["source_records"]
                       if event["kind"] == "authored_bank_inventory"}
        maps = []
        for bank, start in corpus.BANK_STARTS.items():
            rows = self.candidate["banks"][bank]
            self.assertEqual([row["device"] for row in rows], [f"device-{start + index:03d}" for index in range(16)])
            self.assertEqual(Counter(row["response"] for row in rows), {color: 4 for color in corpus.original.COLORS})
            permutation = sorted(range(16), key=lambda index: corpus.digest(f"{corpus.MAP_DOMAINS[bank]}:{index:02d}".encode()))
            self.assertEqual(inventories[bank]["permutation"], permutation)
            for position, index in enumerate(permutation):
                self.assertEqual(rows[index]["response"], corpus.original.COLORS[position % 4])
            maps.append([row["response"] for row in rows])
        self.assertNotEqual(maps[0], maps[1])
        self.assertTrue(all(mapping != [row["response"] for row in self.candidate["banks"]["M0"]] for mapping in maps))

    def test_original_inventory_and_selected_bytes_untouched(self):
        before = corpus.encoded(corpus.original.build_candidate())
        corpus.build_candidate()
        self.assertEqual(before, corpus.encoded(corpus.original.build_candidate()))
        inventory = next(event for event in corpus.original.build_candidate()["source_records"] if event["id"] == "source-log-inventory")
        self.assertEqual(inventory["device_ids"], [f"device-{index:03d}" for index in range(16)])
        self.assertNotIn("source-log-inventory", {event["id"] for event in self.candidate["source_records"]})
        original = {row["case_id"]: row for row in corpus.prior.original_rows()}
        for arms in self.candidate["cycles"].values():
            for rows in arms.values():
                self.assertEqual({row["case_id"] for row in rows if row["kind"] == "addition"}, set(corpus.prior.ADDITION_IDS))
                for row in rows:
                    if row["source_row_index"] is not None:
                        source = original[row["case_id"]]
                        for key in ("context", "response", "source_event_ids"):
                            self.assertEqual(row[key], source[key])
                        self.assertEqual(row["source_row_sha256"], corpus.digest(corpus.encoded(source)))

    def test_seed0_parent_and_fresh_optimizer_seed0(self):
        recipe = self.candidate["manifest"]["recipe"]
        self.assertEqual(recipe["initial_checkpoint_seed"], 0)
        self.assertEqual(recipe["initial_checkpoint_arm"], "FOUR_VIEW")
        self.assertEqual(recipe["seed"], 0)
        self.assertEqual(recipe["allowed_seeds"], [0])
        self.assertEqual(recipe["cumulative_steps"], [400, 720, 1040])
        self.assertEqual((recipe["rank"], recipe["alpha"], recipe["dropout"], recipe["lr"]), (8, 16, .05, 3e-4))
        self.assertFalse(recipe["restore_optimizer"])
        self.assertNotIn("forbidden_parent", recipe)

    def test_allocation_quotas_and_distinct_balanced_batches(self):
        for cycle in corpus.CYCLES:
            for arm in corpus.ARMS:
                rows = self.candidate["cycles"][cycle][arm]
                self.assertEqual(len(rows), 128)
                self.assertEqual(len({row["batch_group"] for row in rows}), 32)
                counts = Counter(row["case_id"] for row in rows)
                self.assertEqual(Counter(row["allocation_slot"] for row in rows),
                                 {"current_new": 32, "replacement": 32, "arithmetic": 64})
                for row in rows:
                    dose = 40 if row["kind"] == "addition" else self.candidate["manifest"]["dose_per_fact_per_fit"][cycle][arm][row["bank"]]
                    self.assertEqual(counts[row["case_id"]] * 10, dose)
                for start in range(0, 128, 4):
                    group = rows[start:start + 4]
                    self.assertEqual(len({row["case_id"] for row in group}), 4)
                    self.assertEqual(group[0]["response"], group[2]["response"])
                    self.assertEqual([row["batch_slot"] for row in group], [0, 1, 2, 3])

    def test_actual_paired_samecolor_replacements_distinct_keys(self):
        for cycle in corpus.CYCLES:
            replay = self.candidate["cycles"][cycle]["R"]
            new = self.candidate["cycles"][cycle]["NEW_ONLY"]
            for start in range(0, 128, 4):
                self.assertEqual(replay[start + 2]["response"], new[start + 2]["response"])
                self.assertEqual(new[start + 2]["bank"], f"B{cycle}")
                self.assertNotEqual(replay[start]["device"], replay[start + 2]["device"])
                self.assertNotEqual(new[start]["device"], new[start + 2]["device"])
                for slot in range(4):
                    self.assertEqual(replay[start + slot]["batch_group"], new[start + slot]["batch_group"])
                    self.assertEqual(replay[start + slot]["response"], new[start + slot]["response"])

    def test_complete_readout_panel_requests_no_answers(self):
        cases = corpus.readout_cases(self.candidate)
        self.assertEqual(len(cases), 128)
        self.assertEqual(Counter(case.get("bank", "ARITHMETIC") for case in cases),
                         {"M0": 32, "B1": 32, "B2": 32, "ARITHMETIC": 32})
        old_eval = {row["id"]: row for row in corpus.original.build_candidate()["eval"]}
        self.assertEqual(cases[-32:], [old_eval[f"eval-addition-{index:03d}"] for index in range(32)])
        for index in range(16):
            self.assertEqual(cases[index * 2 + 1]["context"], old_eval[f"eval-memory-{index:03d}-0"]["context"])
        requests = corpus.readout_requests(cases)
        self.assertEqual(len(requests) * len(corpus.STATES), 640)
        self.assertEqual(sum(request["max_tokens"] for request in requests) * 5, 40960)
        for request, case in zip(requests, cases):
            self.assertEqual(set(request), {"call_id", "case_id", "role", "arm", "prompt", "temperature", "seed", "max_tokens"})
            self.assertEqual(request["prompt"], case["context"])
            self.assertEqual((request["seed"], request["temperature"]), (20260912, 0.0))
        self.assertEqual(self.candidate["manifest"]["untrained_banks_by_state"]["R1"], ["B2"])
        cases[0]["expected"] = "wrong"
        with self.assertRaisesRegex(ValueError, "fixed readout"):
            corpus.readout_requests(cases)

    def test_rows_masks_single_eos_and_original_native_equality(self):
        audit = self.exported["audit"]
        for cycle in corpus.CYCLES:
            for arm in corpus.ARMS:
                fit = audit["fits"][cycle][arm]
                self.assertEqual(len(fit["rows"]), 128)
                for receipt in fit["rows"]:
                    prefix, target = receipt["prefix_token_ids"], receipt["target_with_eos"]
                    self.assertEqual(receipt["input_ids"], prefix + target)
                    self.assertEqual(receipt["labels"], [corpus.trainer.IGNORE] * len(prefix) + target)
                    self.assertEqual(target.count(900), 1)
                    self.assertEqual(target[-1], 900)
                    if receipt["bank"] != "ARITHMETIC":
                        self.assertEqual(len(target), 2)
                    index = receipt["original_native_row_index"]
                    if index is not None:
                        baseline = audit["original_selected_native_rows"][str(index)]
                        self.assertEqual({key: receipt[key] for key in baseline}, baseline)
                self.assertEqual(fit["corpus_sha256"], corpus.digest(corpus.encoded(self.exported["corpora"][cycle][arm])))

    def test_actual_schedules_exposure_costs_not_added_twice(self):
        audit = self.exported["audit"]
        target_total = 0
        for cycle in corpus.CYCLES:
            for arm in corpus.ARMS:
                fit = audit["fits"][cycle][arm]
                schedule = fit["schedule"]
                self.assertEqual(len(schedule["updates"]), 320)
                for epoch in range(10):
                    updates = [step for step in schedule["updates"] if step["epoch"] == epoch]
                    self.assertEqual(len(updates), 32)
                    groups = sorted({row["batch_group"] for row in self.candidate["cycles"][cycle][arm]})
                    random.Random(epoch).shuffle(groups)
                    self.assertEqual([step["group"] for step in updates], groups)
                    self.assertEqual(sorted(index for step in updates for index in step["item_indices"]), list(range(128)))
                    for step in updates:
                        self.assertEqual(len(set(step["source_ids"])), 4)
                        self.assertEqual(step["target_tokens_by_kind"]["memory"], 4)
                        self.assertEqual(step["target_tokens"], sum(step["row_target_tokens"]))
                        self.assertEqual(step["padded_input_slots"], 4 * step["padded_width"])
                        self.assertEqual(step["padded_input_slots"], step["masked_slots"] + step["target_tokens"])
                for key in ("input_tokens", "context_tokens", "target_tokens"):
                    self.assertEqual(schedule["total"][key], fit["per_epoch"][key] * 10)
                    self.assertEqual(fit["ten_epochs"][key], schedule["total"][key])
                self.assertEqual(sum(schedule["source_presentations"].values()), 1280)
                target_total += fit["ten_epochs"]["target_tokens"]
            left = audit["fits"][cycle]["R"]["schedule"]["updates"]
            right = audit["fits"][cycle]["NEW_ONLY"]["schedule"]["updates"]
            self.assertEqual([(row["item_indices"], row["target_tokens"]) for row in left],
                             [(row["item_indices"], row["target_tokens"]) for row in right])
        self.assertEqual(audit["total_target_exposure"], target_total)
        self.assertEqual(audit["observed_optimizer_updates"], 0)
        self.assertFalse(audit["parent_validated"])
        self.assertFalse(audit["native_identity_authenticated"])

    def test_unequal_native_prefixes_reported_not_repaired(self):
        class Unequal(Tokenizer):
            def encode(self, text, *, add_special_tokens):
                tokens = super().encode(text, add_special_tokens=add_special_tokens)
                return tokens + ([777] if "device-1" in text else [])
        tokenizer = Unequal()
        exported = corpus.export_native(self.candidate, original_native(tokenizer), tokenizer)
        self.assertFalse(exported["audit"]["paired"]["1"]["paired_prefix_lengths_equal"])
        self.assertTrue(exported["audit"]["paired"]["1"]["targets_matched"])
        self.assertFalse(exported["audit"]["paired"]["1"]["new_dose_matched"])

    def test_candidate_mutations_rejected(self):
        mutations = [
            lambda candidate: candidate["cycles"]["1"]["R"].pop(),
            lambda candidate: candidate["cycles"].pop("2"),
            lambda candidate: candidate["cycles"]["1"].pop("NEW_ONLY"),
            lambda candidate: candidate["cycles"]["1"]["R"][0].update(response="wrong"),
            lambda candidate: candidate["cycles"]["1"]["R"][0].update(source_event_ids=["teacher-output"]),
            lambda candidate: candidate["cycles"]["1"]["R"][0].update(batch_slot=3),
            lambda candidate: candidate["banks"]["B1"][0].update(device="device-016"),
            lambda candidate: candidate["source_records"][0].update(origin="child"),
            lambda candidate: candidate["manifest"]["recipe"].update(initial_checkpoint_seed=1),
            lambda candidate: candidate["manifest"]["recipe"].update(seed=1),
            lambda candidate: candidate["manifest"].update(teacher_outputs_used=True),
            lambda candidate: candidate["readout_cases"].pop(),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(self.candidate)
                mutation(candidate)
                with self.assertRaisesRegex(ValueError, "fixed candidate"):
                    corpus.export_native(candidate, self.native, Tokenizer())

    def test_original_native_changes_rejected(self):
        for alteration in ("target", "mask", "join", "partial"):
            with self.subTest(alteration=alteration):
                native = copy.deepcopy(self.native)
                if alteration == "target":
                    native["corpus"][0]["spans"][1][0] = "wrong"
                elif alteration == "mask":
                    native["corpus"][0]["spans"][0][1] = True
                elif alteration == "join":
                    native["corpus"][0]["meta"]["source_event_ids"] = []
                else:
                    native["corpus"].pop()
                with self.assertRaisesRegex(ValueError, "original80 native"):
                    corpus.export_native(self.candidate, native, Tokenizer())

    def test_bad_eos_color_and_overlength_rejected(self):
        class Long(Tokenizer):
            def encode(self, text, *, add_special_tokens):
                return [2] * 600 if "<|im_start|>" in text else super().encode(text, add_special_tokens=add_special_tokens)
        class MultiColor(Tokenizer):
            def encode(self, text, *, add_special_tokens):
                return [3, 4] if text in corpus.original.COLORS else super().encode(text, add_special_tokens=add_special_tokens)
        class ColorEOS(Tokenizer):
            def encode(self, text, *, add_special_tokens):
                return [900] if text in corpus.original.COLORS else super().encode(text, add_special_tokens=add_special_tokens)
        for tokenizer, message in ((Long(), "truncate"), (MultiColor(), "one-token"), (ColorEOS(), "EOS inside")):
            with self.subTest(tokenizer=type(tokenizer).__name__), self.assertRaisesRegex(ValueError, message):
                corpus.export_native(self.candidate, original_native(tokenizer), tokenizer)
        tokenizer = Tokenizer()
        tokenizer.pad_token_id = None
        with self.assertRaisesRegex(ValueError, "EOS/pad"):
            corpus.export_native(self.candidate, self.native, tokenizer)

    def test_dropped_schedule_bad_mask_and_source_change_fail(self):
        real_order = corpus.trainer.epoch_order
        with patch.object(corpus.trainer, "epoch_order", side_effect=lambda *args: real_order(*args)[:-1]):
            with self.assertRaisesRegex(ValueError, "dropped/duplicated"):
                corpus.export_native(self.candidate, self.native, Tokenizer())
        real_collate = corpus.trainer.collate
        def bad_batch(*args):
            result = real_collate(*args)
            if len(args[0]) == 4:
                result["labels"][0][0] = 42
            return result
        with patch.object(corpus.trainer, "collate", side_effect=bad_batch):
            with self.assertRaisesRegex(ValueError, "actual batch"):
                corpus.export_native(self.candidate, self.native, Tokenizer())
        with patch.object(corpus, "source_hashes", side_effect=[{"hash": "before"}, {"hash": "after"}]):
            with self.assertRaisesRegex(ValueError, "source/candidate changed"):
                corpus.export_native(self.candidate, self.native, Tokenizer())

    def test_fresh_outputs_wrong_file_hash_and_mock_prepare(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "candidate"
            manifest = corpus.emit_candidate(output)
            self.assertEqual(manifest["sha256"]["candidate.json"], corpus.digest((output / "candidate.json").read_bytes()))
            with self.assertRaises(FileExistsError):
                corpus.emit_candidate(output)
            source = root / "teach.json"
            source.write_bytes(corpus.encoded(self.native))
            with self.assertRaisesRegex(ValueError, "actual original80 teach"):
                corpus.prepare(root / "bad", source, Tokenizer())
            self.assertFalse((root / "bad").exists())
            link = root / "linked"
            link.symlink_to(output, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                corpus.emit_candidate(link / "nested")
            with patch.object(corpus.prior, "ORIGINAL_TEACH_SHA256", corpus.digest(source.read_bytes())), \
                    patch.object(corpus.trainer, "run_training", side_effect=AssertionError("no fits permitted")):
                manifest = corpus.prepare(root / "native-mock", source, Tokenizer())
                self.assertFalse(manifest["native_identity_authenticated"])
                self.assertEqual(set(manifest["sha256"]), {"candidate.json", "token_audit.json", "readout_cases.json",
                    "readout_requests.json", "cycle1_R.json", "cycle1_NEW_ONLY.json", "cycle2_R.json", "cycle2_NEW_ONLY.json"})
                for name, checksum in manifest["sha256"].items():
                    self.assertEqual(checksum, corpus.digest((root / "native-mock" / name).read_bytes()))
                with self.assertRaises(FileExistsError):
                    corpus.prepare(root / "native-mock", source, Tokenizer())


if __name__ == "__main__":
    unittest.main()
