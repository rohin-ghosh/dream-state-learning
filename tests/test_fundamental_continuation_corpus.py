"""CPU material/token fixtures only; no native model or training evidence."""
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import fundamental_continuation_corpus as corpus


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        if tokenize is not False or add_generation_prompt is not True or len(messages) != 1 or messages[0]["role"] != "user":
            raise AssertionError("single native user template required")
        self.calls.append(copy.deepcopy(messages))
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text, *, add_special_tokens):
        if add_special_tokens is not False:
            raise AssertionError("unexpected extra special tokens")
        return [ord(character) for character in text]


class ContinuationCorpusTests(unittest.TestCase):
    def setUp(self):
        self.candidate = corpus.build_candidate()
        self.records = [row for phase in self.candidate["phases"] for row in phase["records"]]
        self.sources = {row["id"]: row for row in self.candidate["source_records"]}
        self.tokenizer = Tokenizer()

    def test_fixed_selection_counts_and_frozen_order(self):
        phases = self.candidate["phases"]
        self.assertEqual([phase["id"] for phase in phases], [f"continuation-phase-{index:02d}" for index in range(1, 5)])
        self.assertEqual([len(phase["records"]) for phase in phases], [16] * 4)
        pairs = [(row["left"], row["right"]) for row in self.candidate["source_records"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(pairs), 64)
        frozen = hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(frozen, "1e88173ad878abac5782ddeb4184fce43c5bd37723e6afd0b67253d16bd2853a")
        self.assertEqual(self.candidate["manifest"]["generation_seed"], 20260918)
        self.assertEqual(corpus.validate_candidate(self.candidate)["distinct_new_pairs"], 64)

    def test_excludes_all_original_train_eval_confirmation_under_reversal(self):
        original = corpus.original.build_candidate()
        old_sources = {row["id"]: row for row in original["source_records"]}
        selected = {(row["left"], row["right"]) for row in self.sources.values()}
        excluded = set()
        for row in original["train_teach"] + original["eval"]:
            if row["kind"] != "addition":
                continue
            source = old_sources[row["source_event_ids"][0]]
            pair = (source["left"], source["right"])
            excluded.add(tuple(sorted(pair)))
            self.assertNotIn(pair, selected)
            self.assertNotIn(pair[::-1], selected)
        self.assertEqual(len(excluded), 128)
        pool = [(left, right) for left in range(20) for right in range(left, 20) if (left, right) not in excluded]
        self.assertEqual(len(pool), 82)
        random.Random(20260918).shuffle(pool)
        self.assertEqual([(row["left"], row["right"]) for row in self.sources.values()], pool[:64])
        self.assertEqual(len(set(pool) - selected), 18)

    def test_sourced_keys_phase_ids_and_act_only_targets(self):
        derivations = {row["record_id"]: row for row in self.candidate["derivations"]}
        self.assertEqual(len(self.sources), len(derivations))
        for row in self.records:
            source = self.sources[row["source_event_ids"][0]]
            total = source["left"] + source["right"]
            self.assertEqual(row["expected"], source["sum"])
            self.assertEqual(row["expected"], total)
            self.assertEqual(row["response"], f"ACT: {total}")
            self.assertNotIn("\n", row["response"])
            self.assertEqual(row["context"], corpus.original.addition_context(source["left"], source["right"]))
            self.assertEqual(row["phase_id"], source["phase_id"])
            self.assertEqual(derivations[row["id"]]["phase_id"], source["phase_id"])
            self.assertEqual(derivations[row["id"]]["target"], row["response"])
            self.assertEqual(source["origin"], "generated_integer_addition")
            self.assertEqual(source["generation_seed"], 20260918)

    def test_no_old_memory_facts_or_extra_teaching_in_material(self):
        text = json.dumps(self.candidate["phases"]) + json.dumps(self.candidate["source_records"])
        for forbidden in ("PREDICT", "COMPUTED", "RESULT", "device-", "color", "blue", "red", "green", "yellow", "reflection"):
            self.assertNotIn(forbidden, text)
        for row in self.records:
            self.assertEqual(set(row), {"id", "phase_id", "kind", "source_event_ids", "context", "response", "expected"})

    def test_recipe_rates_seeds_and_no_passive_fading_claim(self):
        recipe = self.candidate["manifest"]["recipe"]
        self.assertEqual(recipe["learning_rates"], [0.0, 3e-5, 1e-4])
        self.assertEqual(recipe["sentinel_seed"], 0)
        self.assertEqual(recipe["conditional_replication_seeds"], [1, 2])
        self.assertEqual(recipe["rank"], 8)
        self.assertFalse(recipe["pack"])
        self.assertEqual(recipe["epochs_per_phase"] * 16 // recipe["batch_size"] // recipe["grad_accum"], 16)
        self.assertEqual(recipe["total_updates"], 4 * recipe["updates_per_phase"])
        self.assertEqual(recipe["initialization"], "WEIGHT_WARM_START_FRESH_OPTIMIZER")
        self.assertEqual(self.candidate["manifest"]["claim"], "TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP")
        self.assertEqual(self.candidate["manifest"]["new_evaluation_cases"], 0)

    def test_reproducible_without_global_rng_or_shared_mutable_recipe(self):
        before = random.getstate()
        expected = corpus.encoded(self.candidate)
        self.assertEqual(corpus.encoded(corpus.build_candidate()), expected)
        self.assertEqual(random.getstate(), before)
        self.candidate["manifest"]["recipe"]["learning_rates"].append(7)
        self.assertEqual(corpus.encoded(corpus.build_candidate()), expected)

    def test_validation_rejects_wrong_keys_context_targets_phase_and_derivations(self):
        changes = (
            lambda value: value["source_records"][0].update(sum=999),
            lambda value: value["phases"][0]["records"][0].update(expected=999),
            lambda value: value["phases"][0]["records"][0].update(response="PREDICT: 15\nACT: 15"),
            lambda value: value["phases"][0]["records"][0].update(context="Answer: 15"),
            lambda value: value["source_records"][0].update(phase_id="wrong"),
            lambda value: value["derivations"][0].update(target="ACT: 999"),
            lambda value: value["phases"][0]["records"].reverse(),
            lambda value: value["phases"][0]["records"].pop(),
            lambda value: value["manifest"]["recipe"].update(learning_rates=[.1]),
        )
        for change in changes:
            changed = copy.deepcopy(self.candidate)
            change(changed)
            with self.assertRaises(ValueError):
                corpus.validate_candidate(changed)

    def test_validation_rejects_original_repeated_or_reversed_operand_pairs(self):
        for pair in (next(iter(corpus.original_pairs())),
                     (self.candidate["source_records"][1]["left"], self.candidate["source_records"][1]["right"]),
                     (self.candidate["source_records"][0]["right"], self.candidate["source_records"][0]["left"])):
            changed = copy.deepcopy(self.candidate)
            changed["source_records"][0].update(left=pair[0], right=pair[1], sum=sum(pair))
            with self.assertRaises(ValueError):
                corpus.validate_candidate(changed)

    def test_native_user_template_receives_only_original_context_once(self):
        exported = corpus.export_native(self.candidate, self.tokenizer)
        self.assertEqual(self.tokenizer.calls, [[dict(role="user", content=row["context"])] for row in self.records])
        for phase in self.candidate["phases"]:
            for item, row in zip(exported["corpora"][phase["id"]]["corpus"], phase["records"]):
                expected = "<|im_start|>user\n" + row["context"] + "<|im_end|>\n<|im_start|>assistant\n"
                self.assertEqual(item["spans"], [[expected, False, "context"], [row["response"], True, "authored_task_only_target"]])
                self.assertEqual(item["meta"]["source_event_ids"], row["source_event_ids"])
                self.assertEqual(item["meta"]["phase_id"], phase["id"])
                self.assertEqual(item["group"], row["id"])
                self.assertNotIn(row["response"], expected)

    def test_actual_native_ids_mask_eos_hashes_and_epoch_totals(self):
        audit = corpus.export_native(self.candidate, self.tokenizer)["audit"]
        overall = dict(input_tokens=0, context_tokens=0, target_tokens=0)
        for phase in audit["phases"].values():
            self.assertEqual(phase["examples"], 16)
            self.assertEqual(phase["updates"], 16)
            for row in phase["rows"]:
                prefix = [ord(character) for character in row["rendered_context"]]
                target = [ord(character) for character in row["response"]] + [self.tokenizer.eos_token_id]
                self.assertEqual(row["input_ids"], prefix + target)
                self.assertEqual(row["labels"], [-100] * len(prefix) + target)
                self.assertEqual(row["labels_sha256"], corpus.digest(corpus.encoded(row["labels"])))
                self.assertLessEqual(len(row["input_ids"]), 512)
            for key in overall:
                per_epoch = sum(row[key] for row in phase["rows"])
                self.assertEqual(phase["per_epoch"][key], per_epoch)
                self.assertEqual(phase["four_epochs"][key], 4 * per_epoch)
                overall[key] += 4 * per_epoch
        self.assertEqual(audit["four_phase_four_epoch_totals"], overall)
        self.assertEqual(audit["total_updates"], 64)
        self.assertFalse(audit["packing"] or audit["truncation"])

    def test_tokenizer_requirements_and_native_truncation_or_mask_fail_closed(self):
        with patch.object(self.tokenizer, "eos_token_id", None), self.assertRaisesRegex(ValueError, "EOS/pad"):
            corpus.export_native(self.candidate, self.tokenizer)
        with patch.object(self.tokenizer, "encode", return_value=[1] * 512), self.assertRaisesRegex(ValueError, "no truncation"):
            corpus.export_native(self.candidate, self.tokenizer)
        with patch.object(corpus.trainer, "encode_item_segments", return_value=[]), self.assertRaisesRegex(ValueError, "split/truncation"):
            corpus.export_native(self.candidate, self.tokenizer)
        original = corpus.trainer.collate

        def bad_labels(*args):
            result = original(*args)
            result["labels"][0][0] = 1
            return result

        with patch.object(corpus.trainer, "collate", side_effect=bad_labels), self.assertRaisesRegex(ValueError, "boundary mismatch"):
            corpus.export_native(self.candidate, self.tokenizer)

    def test_missing_pad_uses_real_eos_without_inventing_a_token(self):
        with patch.object(self.tokenizer, "pad_token_id", None):
            audit = corpus.export_native(self.candidate, self.tokenizer)["audit"]
        self.assertEqual(audit["pad_token_id"], self.tokenizer.eos_token_id)

    def test_fresh_reproducible_exports_hashes_and_untrusted_injection_label(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first", Path(directory) / "second"
            manifest = corpus.prepare(first, tokenizer=self.tokenizer)
            other = corpus.prepare(second, tokenizer=Tokenizer())
            self.assertEqual(manifest, other)
            self.assertFalse(manifest["native_token_audit"])
            self.assertTrue(manifest["tokenizer_injected"])
            self.assertIn("NOT_AUTHENTICATED", manifest["status"])
            self.assertEqual(len(manifest["phase_corpora"]), 4)
            for name, expected in manifest["sha256"].items():
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
                self.assertEqual(corpus.digest((first / name).read_bytes()), expected)
            self.assertTrue(corpus.verify(first)["valid"])
            with self.assertRaises(FileExistsError):
                corpus.prepare(first, tokenizer=self.tokenizer)
            (first / "continuation-phase-01.json").write_text('{}')
            with self.assertRaisesRegex(ValueError, "artifact bytes"):
                corpus.verify(first)

    def test_raw_generation_requires_no_tokenizer_and_rejects_source_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            with patch.object(corpus, "export_native", side_effect=AssertionError("must not tokenize")):
                manifest = corpus.emit_candidate(root)
            self.assertEqual(set(manifest["sha256"]), {"candidate.json"})
            self.assertFalse(manifest["native_token_audit"])
            with patch.object(corpus, "source_hashes", return_value={}):
                with self.assertRaisesRegex(ValueError, "source hashes"):
                    corpus.verify(root)

    def test_native_model_path_injection_exclusivity_and_failed_audit_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            with self.assertRaisesRegex(ValueError, "either"):
                corpus.prepare(out)
            with self.assertRaisesRegex(ValueError, "either"):
                corpus.prepare(out, model="unused", tokenizer=self.tokenizer)
            with patch.object(self.tokenizer, "encode", return_value=[1] * 512), self.assertRaises(ValueError):
                corpus.prepare(out, tokenizer=self.tokenizer)
            self.assertFalse(out.exists())

    def test_existing_file_directory_and_dangling_symlink_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular, existing, dangling = root / "file", root / "directory", root / "link"
            regular.write_bytes(b"keep")
            existing.mkdir()
            dangling.symlink_to(root / "missing")
            for path in (regular, existing, dangling):
                with self.assertRaises(FileExistsError):
                    corpus.emit_candidate(path)
            self.assertEqual(regular.read_bytes(), b"keep")
            self.assertFalse((root / "missing").exists())

    def test_local_model_loader_hash_binding_cpu_fixture_only(self):
        from organism_v6 import rulegame_parenting_diagnostic as base
        with tempfile.TemporaryDirectory() as directory:
            model, out = Path(directory) / "model", Path(directory) / "out"
            model.mkdir()
            (model / "config.json").write_text('{"model_type":"qwen2"}')
            with patch.object(base, "native_tokenizer", return_value=self.tokenizer) as loader:
                manifest = corpus.prepare(out, model=model)
                loader.assert_called_once_with(str(model.resolve()))
            self.assertEqual(manifest["model"], str(model.resolve()))
            self.assertEqual(manifest["model_files"], base.model_hashes(model))
            self.assertEqual(manifest["status"], "NATIVE_V3_TOKEN_AUDIT_COMPLETE")
            self.assertEqual(manifest["gpu_calls"], 0)
            with self.assertRaisesRegex(ValueError, "overlaps model"):
                corpus.prepare(model / "illegal", model=model)
            self.assertFalse((model / "illegal").exists())

    def test_model_or_source_drift_during_cpu_audit_leaves_no_output(self):
        from organism_v6 import rulegame_parenting_diagnostic as base
        with tempfile.TemporaryDirectory() as directory:
            model, out = Path(directory) / "model", Path(directory) / "out"
            model.mkdir()
            (model / "config.json").write_text('{"model_type":"qwen2"}')

            def changed_model(path):
                (model / "config.json").write_text('{"model_type":"changed"}')
                return self.tokenizer

            with patch.object(base, "native_tokenizer", side_effect=changed_model), self.assertRaisesRegex(ValueError, "bytes changed"):
                corpus.prepare(out, model=model)
            self.assertFalse(out.exists())
            with patch.object(corpus, "source_hashes", side_effect=[{"source": "before"}, {"source": "after"}]), \
                 self.assertRaisesRegex(ValueError, "source changed"):
                corpus.prepare(out, tokenizer=self.tokenizer)
            self.assertFalse(out.exists())

    def test_write_collision_preserves_other_writer_and_leaves_no_success_manifest(self):
        original = Path.open
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"

            def collision(path, mode="r", *args, **kwargs):
                if path == out / "candidate.json" and mode == "xb":
                    with original(path, "wb") as stream:
                        stream.write(b"other writer")
                return original(path, mode, *args, **kwargs)

            with patch.object(Path, "open", collision), self.assertRaises(FileExistsError):
                corpus.emit_candidate(out)
            self.assertEqual((out / "candidate.json").read_bytes(), b"other writer")
            self.assertFalse((out / "manifest.json").exists())

    def test_cli_raw_emit_verify_and_reuse_refusal_cpu_only(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "raw"
            command = [sys.executable, "-B", "-m", "organism_v6.fundamental_continuation_corpus"]
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
            emitted = subprocess.run(command + ["emit", "--out", str(out)], env=env, text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(emitted.stdout)["generation_seed"], 20260918)
            verified = subprocess.run(command + ["verify", "--root", str(out)], env=env, text=True, capture_output=True, check=True)
            self.assertTrue(json.loads(verified.stdout)["valid"])
            repeat = subprocess.run(command + ["emit", "--out", str(out)], env=env, text=True, capture_output=True)
            self.assertNotEqual(repeat.returncode, 0)


if __name__ == "__main__":
    unittest.main()
