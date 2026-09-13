"""CPU synthetic material fixtures; no native tokenization or training claim."""

from collections import Counter
import copy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from organism_v6 import pcfl_event_sequence_v2 as api
import test_pcfl_event_sequence as fixtures


class SyntheticV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.imported = fixtures.synthetic_import()
        cls.tokenizer = fixtures.SyntheticTokenizer()
        with patch.object(api.v1.prefix, "validate_import", side_effect=lambda value, pin: api.v1.prefix.unseal(value, pin)), \
                patch.object(api.v1.prefix, "verify_tokenizer", return_value={"status": "SYNTHETIC_NOT_NATIVE"}):
            cls.original = api.v1.export_material(cls.imported, cls.imported["sha256"], cls.tokenizer)
            cls.exported = api.export_material(cls.imported, cls.imported["sha256"], cls.tokenizer,
                                               learner_seed=0, v1_material=cls.original)

    def setUp(self):
        validation = patch.object(api.v1.prefix, "validate_import", side_effect=lambda value, pin: api.v1.prefix.unseal(value, pin))
        token_check = patch.object(api.v1.prefix, "verify_tokenizer", return_value={"status": "SYNTHETIC_NOT_NATIVE"})
        validation.start()
        token_check.start()
        self.addCleanup(validation.stop)
        self.addCleanup(token_check.stop)

    def spec(self, seed=0):
        return api.build_spec(self.imported, self.imported["sha256"], learner_seed=seed)

    def test_exact_batches_exposures_and_budget(self):
        phases = self.exported["spec"]["phases"]
        expected = {
            "A200": (200, {index: 200 for index in range(4)}),
            "B200_NEW_DOSE": (200, {index: 200 for index in range(4, 8)}),
            "B400_FIXED_WORK": (400, {index: 400 for index in range(4, 8)}),
            "REPLAY400": (400, {index: 200 for index in range(8)}),
            "CLEAN_CUM600": (600, {index: 400 if index < 4 else 200 for index in range(8)}),
        }
        for name, (updates, counts) in expected.items():
            phase = phases[name]
            pairs = [pair for batch in phase["batches"] for pair in batch]
            self.assertEqual((phase["updates"], len(phase["batches"]), phase["presentations"]), (updates, updates, updates * 4))
            self.assertEqual(Counter(index for index, view in pairs), counts)
            self.assertEqual(Counter(tuple(pair) for pair in pairs), {(index, view): count // 8 for index, count in counts.items() for view in range(8)})
            self.assertTrue(all(len(batch) == 4 and len({view for index, view in batch}) == 1 for batch in phase["batches"]))
            self.assertEqual(phase["exposures"], [{"record": index, "view": view, "count": count // 8} for index, count in counts.items() for view in range(8)])
        for repeat in range(25):
            for view in range(8):
                self.assertEqual(phases["A200"]["batches"][8 * repeat + view], [[index, view] for index in range(4)])
                self.assertEqual(phases["B200_NEW_DOSE"]["batches"][8 * repeat + view], [[index, view] for index in range(4, 8)])
                self.assertEqual(phases["REPLAY400"]["batches"][16 * repeat + 2 * view:16 * repeat + 2 * view + 2],
                                 [[[index, view] for index in range(4)], [[index, view] for index in range(4, 8)]])
        for repeat in range(50):
            for view in range(8):
                self.assertEqual(phases["B400_FIXED_WORK"]["batches"][8 * repeat + view], [[index, view] for index in range(4, 8)])
        self.assertEqual(phases["CLEAN_CUM600"]["batches"], phases["A200"]["batches"] + phases["REPLAY400"]["batches"])
        self.assertEqual(self.exported["spec"]["budget"]["updates"], 1800)
        self.assertEqual(self.exported["spec"]["budget"]["presentations"], 7200)

    def test_literal_item_concatenation_and_v3_order(self):
        phases = self.exported["phases"]
        self.assertEqual(phases["CLEAN_CUM600"]["items"], phases["A200"]["items"] + phases["REPLAY400"]["items"])
        self.assertEqual(phases["A200"]["items"][-1]["group"], "batch/0199")
        self.assertEqual(phases["REPLAY400"]["items"][0]["group"], "batch/0200")
        self.assertEqual(phases["CLEAN_CUM600"]["items"][-1]["group"], "batch/0599")
        for name, phase in phases.items():
            api.v1.prefix.unseal(phase, phase["sha256"])
            self.assertEqual(phase["items_sha256"], api.v1.prefix.digest(phase["items"]))
            encoded = [api.v1.trainer.encode_item(item, self.tokenizer, 512, add_eos=True, item_index=index)
                       for index, item in enumerate(phase["items"])]
            ordered = api.v1.trainer.epoch_order(api.v1.trainer.pack_by_group(encoded, 512, pack=False), 2, 0, shuffle_groups=False)
            self.assertEqual([batch[0].item_index for batch in ordered], list(range(len(encoded))))
            self.assertEqual(phase["encoding_sha256"], api.v1.prefix.digest([asdict(item) for item in encoded]))

    def test_all_masks_raw_lf_provenance_and_token_masses(self):
        for phase in self.exported["phases"].values():
            mass, total = Counter(), 0
            for index, item in enumerate(phase["items"]):
                source_index = item["meta"]["record"]
                record = self.exported["spec"]["records"][source_index]
                self.assertEqual(item["meta"]["generation_sha256"], record["generation"]["sha256"])
                self.assertEqual(item["meta"]["capture_sha256"], record["generation"]["capture_sha256"])
                self.assertEqual(item["meta"]["source_sha256"], record["source_sha256"])
                context, target = item["spans"]
                self.assertEqual(context[1:], [False, "context"])
                self.assertEqual(target, [self.imported["rows"][source_index]["raw"], True, "EVENT"])
                self.assertTrue(target[0].endswith("\n"))
                self.assertNotIn(item["view"], ("W8", "W9"))
                context_ids, target_ids = self.tokenizer.encode(context[0]), self.tokenizer.encode(target[0])
                encoded = api.v1.trainer.encode_item(item, self.tokenizer, 512, add_eos=True, item_index=index)
                self.assertEqual(encoded.ids, context_ids + target_ids + [1])
                self.assertEqual(encoded.labels, [-100] * len(context_ids) + target_ids + [1])
                self.assertEqual((encoded.context_dropped, encoded.target_dropped), (0, 0))
                mass[record["bank"]] += encoded.n_target
                total += len(encoded.ids)
            self.assertEqual(phase["supervised_tokens_by_bank"], {bank: mass[bank] for bank in ("A", "B")})
            self.assertEqual(phase["supervised_tokens"], sum(mass.values()))
            self.assertEqual(phase["input_tokens"], total)
        phases = self.exported["phases"]
        self.assertEqual(phases["CLEAN_CUM600"]["supervised_tokens"], phases["A200"]["supervised_tokens"] + phases["REPLAY400"]["supervised_tokens"])

    def test_seed_identity_config_and_cold_roster(self):
        seals = set()
        baseline = asdict(api.v1.training_config("S_A", "/synthetic/local-model", device="cpu"))
        for seed in range(3):
            spec = self.spec(seed)
            seals.add(spec["sha256"])
            self.assertEqual(spec["phases"], self.exported["spec"]["phases"])
            self.assertEqual(spec["roster"], self.exported["spec"]["roster"])
            for name, (parent, updates) in api.PHASES.items():
                config = asdict(api.training_config(name, "/synthetic/local-model", learner_seed=seed, device="cpu"))
                self.assertEqual(config, {**baseline, "max_steps": updates, "seed": seed, "note": api.SCHEMA})
                init = api.initialization(spec, name)
                self.assertEqual(init["parent_phase"], parent)
                self.assertEqual(init["parent_spec_sha256"], spec["sha256"] if parent else None)
                self.assertEqual(init["learner_seed"], seed)
                self.assertEqual(init["kind"], "COMPLETED_V2_A200" if parent else "FRESH_C0")
                self.assertTrue(init["fresh_optimizer"])
                self.assertFalse(init["sa40_parent_allowed"])
        self.assertEqual(len(seals), 3)
        roster = self.exported["spec"]["roster"]
        self.assertEqual([(row["view"], row["request"]) for row in roster], [(view, record["request"]) for view in (0, 8) for record in self.exported["spec"]["records"]])
        self.assertTrue(all(row["seed"] == 0 and row["output_tokens"] == 2048 for row in roster))
        self.assertEqual(len(roster), 16)
        self.assertEqual(api.READ_STATES["NO_WRITE"], None)

    def test_bad_seed_and_old_parent_spec_rejected(self):
        for seed in (-1, 3, True, "0", None):
            with self.assertRaisesRegex(ValueError, "learner_seed"):
                self.spec(seed)
        with self.assertRaisesRegex(ValueError, "only v2 initialization"):
            api.initialization(self.original["spec"], "A200")
        with self.assertRaisesRegex(ValueError, "only v2 phases"):
            api.training_config("S_A", "/synthetic/model", learner_seed=0)
        changed = copy.deepcopy(self.exported["spec"])
        changed.pop("sha256")
        changed["phases"]["REPLAY400"]["parent_phase"] = "S_A"
        with self.assertRaisesRegex(ValueError, "fixed v2 parent"):
            api.initialization(api.seal(changed), "REPLAY400")

    def test_source_pins_history_and_no_input_mutation(self):
        before = copy.deepcopy(self.imported)
        spec = self.spec()
        self.assertEqual(self.imported, before)
        self.assertEqual(spec["records"], self.original["spec"]["records"])
        self.assertEqual(spec["historical"], self.original["spec"]["historical"])
        self.assertEqual(spec["historical"]["original_status"], "FORMATION_FAILED")
        for source, checksum in spec["sources"].items():
            self.assertEqual(api.hashlib.sha256(Path(source).read_bytes()).hexdigest(), checksum)
        self.assertIn(str(Path(api.__file__).resolve()), spec["sources"])
        self.assertIn("not independent facts", spec["limits"])
        self.assertFalse(spec["automatic_promotion"])
        self.assertEqual(self.original["spec"]["phases"]["S_A"]["updates"], 40)
        api.validate_spec(spec, self.imported, self.imported["sha256"])

    def test_resealed_tamper_and_bad_import_pin_rejected(self):
        with self.assertRaises(ValueError):
            api.build_spec(self.imported, "0" * 64, learner_seed=0)
        for mutate in (lambda spec: spec["sources"].clear(),
                       lambda spec: spec["phases"]["REPLAY400"]["batches"][0][0].__setitem__(1, 8),
                       lambda spec: spec["records"][0].update(target="invented\n")):
            changed = copy.deepcopy(self.exported["spec"])
            changed.pop("sha256")
            mutate(changed)
            with self.assertRaisesRegex(ValueError, "fixed v2 spec"):
                api.validate_spec(api.seal(changed), self.imported, self.imported["sha256"])

    def test_optional_v1_material_is_not_a_trust_bypass(self):
        changed = copy.deepcopy(self.original)
        changed["phases"]["S_A"]["items"][0]["spans"][1][0] += "\n"
        with self.assertRaisesRegex(ValueError, "current v1 material differs"):
            api.export_material(self.imported, self.imported["sha256"], self.tokenizer, learner_seed=0, v1_material=changed)

    def test_deterministic_export_no_mutation_or_training(self):
        import_before, original_before = copy.deepcopy(self.imported), copy.deepcopy(self.original)
        with patch.object(api.v1.trainer, "run_training", side_effect=AssertionError("no training")):
            repeated = api.export_material(self.imported, self.imported["sha256"], self.tokenizer,
                                           learner_seed=0, v1_material=self.original)
        self.assertEqual(repeated, self.exported)
        self.assertEqual(self.imported, import_before)
        self.assertEqual(self.original, original_before)

    def test_native_tokenizer_check_and_no_truncation_remain_required(self):
        with patch.object(api.v1.prefix, "verify_tokenizer", side_effect=ValueError("bound native tokenizer differs")):
            with self.assertRaisesRegex(ValueError, "native tokenizer"):
                api.export_material(self.imported, self.imported["sha256"], self.tokenizer, learner_seed=0)
        oversized = fixtures.SyntheticTokenizer()
        oversized.apply_chat_template = lambda messages, tokenize=False, **kwargs: oversized.encode("x" * 1600) if tokenize else "x" * 1600
        with self.assertRaisesRegex(ValueError, "zero truncation"):
            api.export_material(self.imported, self.imported["sha256"], oversized, learner_seed=0)


class SafeImportTests(unittest.TestCase):
    def test_no_model_libraries_loaded_on_import_or_config(self):
        script = "from organism_v6 import pcfl_event_sequence_v2 as api; import sys; api.training_config('A200', '/synthetic/model', learner_seed=0, device='cpu'); assert not {'torch', 'transformers', 'peft', 'vllm'} & set(sys.modules)"
        subprocess.run([sys.executable, "-B", "-c", script], cwd=fixtures.ROOT, check=True, capture_output=True, timeout=10)


@unittest.skipUnless(fixtures.ARCHIVE.is_file() and fixtures.REPLAY.is_file(), "original archive/import receipt unavailable")
class OriginalImportTests(unittest.TestCase):
    def test_actual_original_provenance_without_tokenizer_or_model(self):
        receipt = json.loads(fixtures.REPLAY.read_text())
        imported = api.v1.prefix.build_import(api.v1.prefix.load_evidence(fixtures.ARCHIVE), receipt, receipt["sha256"])
        spec = api.build_spec(imported, imported["sha256"], learner_seed=2)
        api.validate_spec(spec, imported, imported["sha256"])
        self.assertEqual(spec["historical"]["original_status"], "FORMATION_FAILED")
        self.assertTrue(spec["historical"]["format_scaffold"])
        for index, record in enumerate(spec["records"]):
            self.assertEqual(record["target"], imported["generations"][index]["raw"])
            self.assertEqual(record["target"], imported["rows"][index]["raw"])
            self.assertTrue(record["target"].endswith("\n"))
            self.assertEqual(record["generation"]["origin"], "CHILD_NATIVE")


if __name__ == "__main__":
    unittest.main()
