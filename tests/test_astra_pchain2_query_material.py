"""Synthetic-tokenizer material tests only; no model, native tokenizer, or fit."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_pchain2_free_material as free
from gpu import astra_pchain2_native as native
from gpu import astra_pchain2_prepare as source
from gpu import astra_pchain2_query_material as query
from test_astra_pchain2_free_material import saved_fixture
from test_astra_pchain2_native import FakeTokenizer, canary_fixture


def file_bytes(manifest):
    return (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode("ascii")


class QueryMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = FakeTokenizer()
        prior = free.generate_material(cls.tokenizer, saved_identifiers=saved_fixture(), canaries=canary_fixture())
        cls.training = {state: file_bytes(manifest) for state, manifest in prior["training"].items()}
        cls.evaluation = {state: file_bytes(manifest) for state, manifest in prior["evaluation"].items()}
        with patch.object(native, "HFState", side_effect=AssertionError("no model")), \
                patch.object(native, "allocate_identifiers", side_effect=AssertionError("no allocation")), \
                patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solver")):
            cls.material = query.generate_material(cls.tokenizer, training_files=cls.training, evaluation_files=cls.evaluation)

    def test_only_atomic_users_change_in_all_states(self):
        for state, original_bytes in self.training.items():
            original = json.loads(original_bytes)
            changed = self.material["training"][state]
            self.assertEqual(changed["material_kind"], "PCHAIN2_QUERY_ONLY_DEV_V1")
            self.assertEqual(len(changed["rows"]), 64)
            for index, (before, after) in enumerate(zip(original["rows"], changed["rows"])):
                self.assertEqual(before["row_id"], after["row_id"])
                self.assertEqual(before["messages"][0], after["messages"][0])
                self.assertEqual(before["messages"][2], after["messages"][2])
                if index >= 32:
                    self.assertEqual(before, after)
                    continue
                origin, target = before["messages"][2]["content"].removeprefix("MEMORY NEXT ").rstrip("\n").split(" => ")
                self.assertEqual(after["messages"][1]["content"],
                                 f"QUERY\nRecall NEXT for {origin}.\nOUTPUT\nReturn exactly one MEMORY line.\n")
                self.assertNotIn(target, after["messages"][1]["content"])
                self.assertNotIn("OBSERVED RELATION", after["messages"][1]["content"])
                self.assertEqual(after["messages"][2]["content"], source._memory(origin, target))

    def test_all_targets_masks_skills_tape_and_recipe_preserved(self):
        for state, original_bytes in self.training.items():
            original = json.loads(original_bytes)
            changed = self.material["training"][state]
            for field in ("recipe", "batches", "dropout_seeds", "learner_seed", "dose", "tokenizer", "identifier_receipt_sha256"):
                self.assertEqual(changed[field], original[field])
            self.assertEqual(len(changed["batches"]), 384)
            self.assertEqual(sum(map(len, changed["batches"])), 1536)
            self.assertEqual(changed["encoded_rows"][32:], original["encoded_rows"][32:])
            for index, (before, after) in enumerate(zip(original["encoded_rows"], changed["encoded_rows"])):
                self.assertEqual(after["target_ids"], before["target_ids"])
                self.assertEqual([token for token in after["labels"] if token != -100], after["target_ids"])
                self.assertEqual(after["labels"][-1], -100)
                self.assertLessEqual(len(after["input_ids"]), 16384)
                if index < 32:
                    self.assertNotEqual(after["input_ids"], before["input_ids"])
            original_total = sum(len(original["encoded_rows"][index]["target_ids"])
                                 for batch in original["batches"] for index in batch)
            self.assertEqual(self.material["receipt"]["source_training"][state]["target_tokens"], original_total)

    def test_original_rows_hashes_and_eval_file_bytes_retained(self):
        self.assertEqual(self.material["original_training_files"], self.training)
        self.assertEqual(self.material["evaluation_files"], self.evaluation)
        for state, raw in self.training.items():
            receipt = self.material["receipt"]["source_training"][state]
            self.assertEqual(receipt["source_file_sha256"], sha256(raw).hexdigest())
            self.assertEqual(receipt["original_rows_sha256"], native._digest(json.loads(raw)["rows"]))
        for state, raw in self.material["evaluation_files"].items():
            self.assertEqual(json.loads(raw)["material_kind"], free.MATERIAL_KIND)
            self.assertEqual(self.material["receipt"]["evaluation_file_sha256"][state], sha256(raw).hexdigest())
        self.assertEqual(self.material["receipt"]["fits"], 0)
        self.assertEqual(self.material["receipt"]["initial_fit_state_selected_by_Main"], "ATOM-JUNCTION")
        self.assertTrue(self.material["receipt"]["other_cells_material_only"])

    def test_atomic_users_are_bound_onehop_queries_not_selected_from_evaluation(self):
        for state in source.STATES[1:]:
            manifest = json.loads(self.evaluation[state])
            questions = {(call["slot"]["index"]): call["user"] for call in manifest["calls"] if call["slot"]["panel"] == "one_hop"}
            for index, row in enumerate(self.material["training"][state]["rows"][:32]):
                self.assertEqual(row["messages"][1]["content"], questions[index // 2 if index % 2 == 0 else 16 + index // 2])
        evaluation = dict(self.evaluation)
        changed = json.loads(evaluation["ATOM-JUNCTION"])
        changed["calls"][0]["expected"] = "ANSWER ignored_evaluation_target\n"
        evaluation["ATOM-JUNCTION"] = file_bytes(changed)
        material = query.generate_material(self.tokenizer, training_files=self.training, evaluation_files=evaluation)
        self.assertEqual(material["training"], self.material["training"])

    def test_deranged_training_targets_preserve_existing_counterfactual(self):
        authentic = self.material["training"]["ATOM-JUNCTION"]["rows"]
        deranged = self.material["training"]["DERANGED-JUNCTION"]["rows"]
        for index in range(16):
            self.assertEqual(authentic[2 * index], deranged[2 * index])
            self.assertEqual(authentic[2 * index + 1]["messages"][1], deranged[2 * index + 1]["messages"][1])
            self.assertNotEqual(authentic[2 * index + 1]["messages"][2], deranged[2 * index + 1]["messages"][2])

    def test_noncanonical_source_user_rejected_even_with_valid_encoding(self):
        training = dict(self.training)
        manifest = json.loads(training["ATOM-JUNCTION"])
        manifest["rows"][0]["messages"][1]["content"] += "Extra instructions.\n"
        manifest["encoded_rows"][0] = asdict(native.encode_training_row(manifest["rows"][0]["messages"], self.tokenizer,
                                                                       max_context=16384))
        training["ATOM-JUNCTION"] = file_bytes(manifest)
        with self.assertRaisesRegex(ValueError, "original_atomic_source_row_mismatch"):
            query.generate_material(self.tokenizer, training_files=training, evaluation_files=self.evaluation)

    def test_changed_target_encoding_cannot_silently_pass(self):
        original = native.encode_training_row

        def changed_target(messages, tokenizer, **kwargs):
            result = original(messages, tokenizer, **kwargs)
            if messages[1]["content"].startswith("QUERY\nRecall NEXT"):
                return native.EncodedRow(result.input_ids, result.labels, result.target_ids + (999,))
            return result

        with patch.object(native, "encode_training_row", side_effect=changed_target), \
                self.assertRaisesRegex(ValueError, "original_assistant_target_tokens_changed"):
            query.generate_material(self.tokenizer, training_files=self.training, evaluation_files=self.evaluation)

    def test_invalid_cache_tape_or_source_kind_rejected(self):
        for field in ("encoded_rows", "dropout_seeds", "material_kind"):
            training = dict(self.training)
            manifest = json.loads(training["LR0"])
            if field == "encoded_rows":
                manifest[field][0]["labels"][0] = 1000
            elif field == "dropout_seeds":
                manifest[field][0] += 1
            else:
                manifest[field] = query.MATERIAL_KIND
            training["LR0"] = file_bytes(manifest)
            with self.subTest(field=field), self.assertRaises(ValueError):
                query.generate_material(self.tokenizer, training_files=training, evaluation_files=self.evaluation)

    def test_context_and_deadline_fail_without_truncation_or_repair(self):
        with self.assertRaisesRegex(ValueError, "context_overflow"):
            query.generate_material(self.tokenizer, training_files=self.training, evaluation_files=self.evaluation, max_context=1)
        with self.assertRaisesRegex(TimeoutError, "bounded"):
            query.generate_material(self.tokenizer, training_files=self.training, evaluation_files=self.evaluation,
                                     check=lambda: (_ for _ in ()).throw(TimeoutError("bounded")))

    def test_CLI_preserves_source_and_exact_eval_bytes_without_reading_outcomes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            prior = root / "prior"
            for namespace, files in (("training", self.training), ("evaluation", self.evaluation)):
                (prior / namespace).mkdir(parents=True)
                for state, raw in files.items():
                    (prior / namespace / (state + ".json")).write_bytes(raw)
            (prior / "RESULT.json").write_text("not JSON: must never be consumed")
            output = root / "query"
            argv = ["--source-material-dir", str(prior), "--model-dir", directory, "--output", str(output)]
            with patch.object(native, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(native, "HFState", side_effect=AssertionError("no model")), \
                    patch.object(native, "allocate_identifiers", side_effect=AssertionError("no allocation")), \
                    patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solver")):
                query.main(argv)
                with self.assertRaises(FileExistsError):
                    query.main(argv)
            for state, raw in self.evaluation.items():
                self.assertEqual((output / "evaluation" / (state + ".json")).read_bytes(), raw)
                self.assertEqual((prior / "evaluation" / (state + ".json")).read_bytes(), raw)
            for state, raw in self.training.items():
                self.assertEqual((output / "original_training" / (state + ".json")).read_bytes(), raw)
                self.assertEqual((prior / "training" / (state + ".json")).read_bytes(), raw)
                self.assertEqual(json.loads((output / "training" / (state + ".json")).read_bytes())["material_kind"], query.MATERIAL_KIND)
            self.assertEqual(native._read(output / "RESULT.json")["material_kind"], query.MATERIAL_KIND)


if __name__ == "__main__":
    unittest.main()
