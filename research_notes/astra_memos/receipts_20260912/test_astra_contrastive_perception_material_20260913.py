import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from collections import Counter


PATH = Path(__file__).with_name("astra_contrastive_perception_material_20260913.py")
SPEC = importlib.util.spec_from_file_location("material", PATH)
material = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(material)


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = material.load_corpus()
        cls.dataset = material.build_dataset(cls.corpus)

    def test_deterministic(self):
        self.assertEqual(material.encoded(self.dataset), material.encoded(material.build_dataset(self.corpus)))
        changed = copy.deepcopy(self.dataset)
        changed["training"]["plain"][0]["raw_target"] = "bad"
        self.assertNotEqual(material.encoded(changed), material.encoded(material.build_dataset(self.corpus)))

    def test_no_mutable_manifest_alias(self):
        dataset = material.build_dataset(self.corpus)
        dataset["provenance"]["templates"]["plain"] = "mutated"
        dataset["provenance"]["sources"].clear()
        dataset["provenance"]["interface"].clear()
        self.assertEqual(material.encoded(self.dataset), material.encoded(material.build_dataset(self.corpus)))

    def test_counts(self):
        self.assertEqual({key: len(rows) for key, rows in self.dataset["training"].items()}, {"plain": 12, "contrastive": 12})
        self.assertEqual({key: len(rows) for key, rows in self.dataset["evaluation"].items()}, {"D1": 12, "D2": 12, "C-record": 12, "C-general": 12})

    def test_unchanged_supervision_source_group_order(self):
        original = self.corpus.build_slice("perception", split="train", system_anchor=None)["rows"]
        for arm in self.dataset["training"].values():
            for order, (row, source) in enumerate(zip(arm, original)):
                for field in ("source", "raw_target", "target_sha256", "source_proof", "row_id"):
                    self.assertEqual(row[field], source[field])
                self.assertEqual(row["material"]["group"], source["row_id"])
                self.assertEqual(row["material"]["order"], order)

    def test_companion_factorial(self):
        for row in self.dataset["training"]["plain"]:
            selected = self.corpus.assess_source(row["source"])["execution"]
            other = row["material"]["companion_source"]
            companion = self.corpus.assess_source(other)["execution"]
            self.assertNotEqual(other["source_id"], row["source"]["source_id"])
            self.assertEqual(selected["values"], companion["values"])
            self.assertIs(selected["predicted"], companion["predicted"])
            self.assertIsNot(selected["observed"], companion["observed"])
        self.assertEqual({row["source"]["source_id"] for row in self.dataset["training"]["plain"]},
                         {row["material"]["companion_source"]["source_id"] for row in self.dataset["training"]["plain"]})

    def test_equal_note_facts_and_repetitions(self):
        for plain, contrast in zip(*self.dataset["training"].values()):
            self.assertEqual(plain["material"]["fact_inventory"], contrast["material"]["fact_inventory"])
            self.assertEqual(Counter(plain["material"]["note_lines"]), Counter(contrast["material"]["note_lines"]))
            self.assertEqual(plain["material"]["source_transcripts_sha256"], contrast["material"]["source_transcripts_sha256"])
            self.assertNotEqual(plain["input_messages"], contrast["input_messages"])
            for row in (plain, contrast):
                for line in row["material"]["note_lines"]:
                    self.assertEqual(row["input_messages"][0]["content"].count(line), 1)
                self.assertIn("independent hypothetical boxes", row["input_messages"][0]["content"])

    def test_skins_and_cost_contract(self):
        for rows in self.dataset["training"].values():
            self.assertEqual(Counter(row["material"]["skin"] for row in rows), {"ledger": 6, "cards": 6})
            for row in rows:
                self.assertIsNone(row["material"]["costs"]["context_tokens"])
                self.assertIsNone(row["material"]["costs"]["assistant_tokens_including_eos"])
        self.assertNotEqual(self.dataset["costs"]["plain"]["context_utf8_bytes"], self.dataset["costs"]["contrastive"]["context_utf8_bytes"])

    def test_fresh_held_and_shared_situations(self):
        excluded = {tuple(triple) for triples in self.corpus.SITUATIONS.values() for triple in triples} | {(20, 21, 22)}
        for first, second in zip(self.dataset["evaluation"]["D1"], self.dataset["evaluation"]["D2"]):
            self.assertEqual(first["source"], second["source"])
            self.assertEqual(first["raw_target"], second["raw_target"])
            self.assertNotEqual(first["input_messages"], second["input_messages"])
            self.assertNotIn(tuple(first["source_proof"]["try"]["value"]), excluded)
            observed = first["source_proof"]["observed"]["value"]
            self.assertIn(str(not observed), first["source"]["events"][0]["raw_outcome"])
            self.assertNotIn("Companion", first["input_messages"][0]["content"])
        self.assertEqual(len({row["source"]["source_id"] for row in self.dataset["evaluation"]["D1"]}), 12)

    def test_canaries_exact_exposed_and_fresh(self):
        dev = self.corpus.build_slice("perception", split="dev", system_anchor=None)["rows"]
        self.assertEqual(material.encoded(dev), material.encoded(self.dataset["evaluation"]["C-record"]))
        general = self.dataset["evaluation"]["C-general"]
        self.assertEqual(Counter(row["skill"] for row in general), {"addition": 6, "copy": 6})
        self.assertEqual(len({row["raw_target"] for row in general}), 12)
        train_inputs = {row["input_sha256"] for row in self.dataset["training"]["plain"]}
        self.assertTrue(all(row["input_sha256"] not in train_inputs for row in general))

    def test_all_authored_targets_strict_pass(self):
        for rows in [*self.dataset["training"].values(), *self.dataset["evaluation"].values()]:
            for row in rows:
                self.assertTrue(material.score_row(self.corpus, row, row["raw_target"])["strict_pass"])

    def test_syntax_and_schema_separate(self):
        row = self.dataset["evaluation"]["D1"][0]
        for raw in ("```json\n" + row["raw_target"] + "\n```", '{"try":[],"try":[]}', 'NaN', None):
            score = material.score_row(self.corpus, row, raw)
            self.assertFalse(score["strict_pass"])
            self.assertTrue(score["syntax_errors"] or score["schema_errors"])
            self.assertFalse(score["source_errors"])
        for field, invalid in (("observed", 1), ("predicted", 0), ("try", [True, 2, 3]), ("relation", 7)):
            record = json.loads(row["raw_target"])
            record[field] = invalid
            score = material.score_row(self.corpus, row, json.dumps(record))
            self.assertTrue(score["schema_errors"])
            self.assertTrue(all(value is None for value in score["field_correct"].values()))

    def test_all_source_errors_reported(self):
        row = next(row for row in self.dataset["evaluation"]["D1"] if row["source_proof"]["predicted"]["value"] is not None)
        record = json.loads(row["raw_target"])
        record.update({"try": [900, 901, 902], "observed": not record["observed"],
                       "predicted": not record["predicted"], "relation": "unavailable"})
        score = material.score_row(self.corpus, row, json.dumps(record))
        self.assertEqual(set(score["source_errors"]), set(material.FIELDS))
        self.assertFalse(score["syntax_errors"] or score["schema_errors"] or score["strict_pass"])

    def test_general_exact_not_normalized(self):
        for row in self.dataset["evaluation"]["C-general"]:
            score = material.score_row(self.corpus, row, " " + row["raw_target"])
            self.assertFalse(score["strict_pass"])
            self.assertEqual(score["syntax_errors"], ["surrounding_whitespace"])
            self.assertFalse(material.score_row(self.corpus, row, "wrong")["strict_pass"])

    def responses(self):
        perfect = {panel + "/" + row["row_id"]: {"raw": row["raw_target"], "finish_reason": "stop"}
                   for panel, rows in self.dataset["evaluation"].items() for row in rows}
        return {state: copy.deepcopy(perfect) for state in ("OFF", "plain", "contrastive")}

    def test_ceiling_and_missing_fail_closed(self):
        responses = self.responses()
        score = material.score_dataset(self.corpus, self.dataset, responses)
        self.assertTrue(score["ceiling_limited"])
        self.assertFalse(score["exploratory_screen_pass"])
        responses["contrastive"].pop(next(iter(responses["contrastive"])))
        score = material.score_dataset(self.corpus, self.dataset, responses)
        self.assertFalse(score["complete"])
        self.assertFalse(score["exploratory_screen_pass"])

    def test_screen_and_canary_regression(self):
        responses = self.responses()
        for state in ("OFF", "plain"):
            for key in list(responses[state]):
                if key.startswith(("D1/", "D2/")):
                    responses[state][key]["raw"] = "bad"
        score = material.score_dataset(self.corpus, self.dataset, responses)
        self.assertTrue(score["exploratory_screen_pass"])
        self.assertEqual(len(score["paired_held"]["plain"]["wins"]), 24)
        key = next(key for key in responses["contrastive"] if key.startswith("C-general/"))
        responses["contrastive"][key]["raw"] = "bad"
        score = material.score_dataset(self.corpus, self.dataset, responses)
        self.assertEqual(score["canary_regressions"], [key])
        self.assertFalse(score["exploratory_screen_pass"])

    def test_truncation_never_gets_credit(self):
        responses = self.responses()
        key = next(iter(responses["contrastive"]))
        responses["contrastive"][key]["finish_reason"] = "length"
        score = material.score_dataset(self.corpus, self.dataset, responses)
        self.assertFalse(score["states"]["contrastive"]["items"][key]["strict_pass"])
        self.assertTrue(score["states"]["contrastive"]["items"][key]["completion_errors"])
        self.assertFalse(score["complete"])

    def test_envelope_and_json_roundtrip(self):
        dataset = json.loads(material.encoded(self.dataset))
        self.assertTrue(material.score_dataset(self.corpus, dataset, self.responses())["complete"])
        responses = self.responses()
        responses["OFF"][next(iter(responses["OFF"]))] = "raw_without_completion_receipt"
        with self.assertRaisesRegex(ValueError, "envelopes"):
            material.score_dataset(self.corpus, self.dataset, responses)

    def test_tamper_and_unknown_rejected(self):
        altered = copy.deepcopy(self.dataset)
        altered["training"]["plain"][0]["raw_target"] += " "
        with self.assertRaisesRegex(ValueError, "frozen generator"):
            material.score_dataset(self.corpus, altered, self.responses())
        responses = self.responses()
        responses["OFF"]["extra"] = "bad"
        with self.assertRaisesRegex(ValueError, "unknown response"):
            material.score_dataset(self.corpus, self.dataset, responses)

    def test_source_pins_and_output_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "organism_v6").mkdir(parents=True)
            (root / "organism_v6/birth_skill_corpus.py").write_text("bad")
            with self.assertRaisesRegex(ValueError, "pin mismatch"):
                material.load_corpus(root)
            target = Path(directory) / "new.json"
            material.write_new(target, {"ok": True}, root)
            self.assertEqual(target.read_bytes(), material.encoded({"ok": True}))
            with self.assertRaises(FileExistsError):
                material.write_new(target, {}, root)
            with self.assertRaisesRegex(ValueError, "repository"):
                material.write_new(root / "forbidden.json", {}, root)

    def test_cli_build_and_score_mock_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory) / "dataset.json"
            responses = Path(directory) / "responses.json"
            scores = Path(directory) / "scores.json"
            responses.write_bytes(material.encoded(self.responses()))
            for arguments in (("build", "--output", str(dataset)),
                              ("score", "--dataset", str(dataset), "--responses", str(responses), "--output", str(scores))):
                result = subprocess.run([sys.executable, "-B", str(PATH), *arguments],
                                        capture_output=True, text=True, timeout=10, check=True)
                self.assertFalse(json.loads(result.stdout)["native_executed"])
            self.assertEqual(dataset.read_bytes(), material.encoded(self.dataset))
            self.assertTrue(json.loads(scores.read_bytes())["complete"])


if __name__ == "__main__":
    unittest.main()
