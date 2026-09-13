"""CPU material tests: synthetic tokenizer/rows, plus immutable archive import.

Synthetic checks are not native tokenizer, training, or replay qualification.
"""

from collections import Counter, UserDict
import copy
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from organism_v6 import pcfl_event_sequence as sequence


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/evidence.tar"
REPLAY = ROOT / "research_notes/astra_memos/receipts_20260912/astra_pcfl_event_prefix_original_v3_replay_20260913_attempt1.json"


class SyntheticTokenizer:
    eos_token_id = 1

    def __init__(self):
        self.vocab = {}
        self.reverse = {}

    def encode(self, text, add_special_tokens=False):
        result = []
        for start in range(0, len(text), 3):
            chunk = text[start:start + 3]
            if chunk not in self.vocab:
                token = len(self.vocab) + 2
                self.vocab[chunk] = token
                self.reverse[token] = chunk
            result.append(self.vocab[chunk])
        return result

    def decode(self, tokens, skip_special_tokens=False):
        return "".join(self.reverse[token] for token in tokens)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        text = "\n".join(message["role"] + ":" + message["content"] for message in messages) + "\nassistant:"
        return UserDict(input_ids=self.encode(text)) if tokenize else text


def synthetic_import():
    rows, generations, queries = [], [], {}
    for index in range(8):
        event = f"SYNTHETIC_EVENT_{index}"
        raw = f"EVENT {event} synthetic fixture only; not native\n"
        rows.append({"fields": {"event": event, "phase": "OLD"}, "raw": raw})
        generations.append({"raw": raw, "sha256": sequence.core.byte_hash(raw),
                            "capture_sha256": sequence.prefix.digest(["SYNTHETIC", index]),
                            "origin": "SYNTHETIC_NOT_NATIVE"})
        queries["READ EVENT " + event] = {"support": [event], "target": raw,
                                         "source_sha256": sequence.prefix.digest([raw])}
    return sequence.seal({"rows": rows, "generations": generations, "queries": queries,
                          "original_status": "FORMATION_FAILED", "original_returncode": 1,
                          "original_calls": 17, "format_scaffold": "SYNTHETIC_TEST_ONLY"})


class SyntheticMaterialTests(unittest.TestCase):
    def setUp(self):
        self.imported = synthetic_import()
        validation = patch.object(sequence.prefix, "validate_import",
                                  side_effect=lambda value, digest: sequence.prefix.unseal(value, digest))
        token_check = patch.object(sequence.prefix, "verify_tokenizer",
                                   return_value={"status": "SYNTHETIC_NOT_QUALIFIED"})
        self.validation = validation.start()
        self.token_check = token_check.start()
        self.addCleanup(validation.stop)
        self.addCleanup(token_check.stop)

    def spec(self):
        return sequence.build_spec(self.imported, self.imported["sha256"])

    def export(self, tokenizer=None):
        return sequence.export_material(self.imported, self.imported["sha256"], tokenizer or SyntheticTokenizer())

    def test_fixed_chronology_singletons_and_claim_limits(self):
        original = copy.deepcopy(self.imported)
        spec = self.spec()
        self.assertEqual(self.imported, original)
        self.assertEqual([record["call_index"] for record in spec["records"]], list(range(1, 16, 2)))
        self.assertEqual([record["bank"] for record in spec["records"]], ["A"] * 4 + ["B"] * 4)
        self.assertEqual(spec["historical"]["original_status"], "FORMATION_FAILED")
        self.assertEqual(spec["historical"]["original_returncode"], 1)
        self.assertIn("EXPOSED_DEV", spec["label"])
        self.assertIn("fresh optimizer", spec["limits"])
        self.assertFalse(spec["full_contract_released"])
        self.assertIsNone(spec["measurement"]["pass_threshold"])
        self.assertEqual(spec["measurement"]["zero_pre_correct_retention"], "UNDEFINED")
        self.assertEqual([(row["view"], row["request"]) for row in spec["roster"]],
                         [(view, record["request"]) for view in (0, 8) for record in spec["records"]])
        self.assertTrue(all(row["request"].startswith("READ EVENT ") for row in spec["roster"]))

    def test_exact_schedules_and_exposure_matching(self):
        spec = self.spec()
        phases = spec["phases"]
        self.assertEqual(spec["budget"], dict(fits=6, updates=400, presentations=1600,
                                            readout_states=6, calls_per_state=16, readout_calls=96,
                                            new_formation_calls=0))
        self.assertEqual(phases["SEQ_REPLAY"]["batches"], phases["FRESH_MIX"]["batches"])
        counts = {}
        for name, phase in phases.items():
            self.assertEqual((phase["parent_phase"], phase["updates"]), sequence.PHASES[name])
            self.assertEqual(len(phase["batches"]), phase["updates"])
            self.assertEqual(phase["presentations"], 4 * phase["updates"])
            counts[name] = Counter(tuple(pair) for batch in phase["batches"] for pair in batch)
            for batch in phase["batches"]:
                self.assertEqual(len({index for index, view in batch}), 4)
                self.assertEqual(len({view for index, view in batch}), 1)
                self.assertTrue(all(0 <= view < 8 for index, view in batch))
        self.assertEqual(counts["S_A"], Counter({(index, view): 5 for index in range(4) for view in range(8)}))
        self.assertEqual(counts["SEQ_REPLAY"], Counter({(index, view): 5 for index in range(8) for view in range(8)}))
        self.assertEqual(counts["SEQ_NEW_ONLY"], Counter({(index, view): 10 for index in range(4, 8) for view in range(8)}))
        self.assertEqual(counts["S_A"] + counts["SEQ_REPLAY"], counts["ALL_AVAILABLE_1"] + counts["ALL_AVAILABLE_2"])
        available = phases["ALL_AVAILABLE_1"]["batches"] + phases["ALL_AVAILABLE_2"]["batches"]
        self.assertEqual(available, [[[index, view] for index in group] for repeat in range(5)
                                    for view in range(8) for group in ((0, 1, 4, 5), (2, 3, 6, 7), (0, 1, 2, 3))])

    def test_config_exact_v3_recipe(self):
        for name, (parent, updates) in sequence.PHASES.items():
            config = asdict(sequence.training_config(name, "/synthetic/frozen-base", device="cpu"))
            expected = dict(rank=8, alpha=16, dropout=.05, lr=3e-5, seed=0, epochs=1,
                            max_steps=updates, max_len=512, batch_size=4, grad_accum=1,
                            pack=False, shuffle_groups=False, optimizer="adamw", layers="all",
                            svd_init=False, freeze_a=False, chat_template=False, add_eos=True,
                            overflow="truncate", grad_checkpoint=False, dtype="bf16", log_every=0,
                            note=sequence.SCHEMA, model="/synthetic/frozen-base", device="cpu")
            self.assertEqual({key: config[key] for key in expected}, expected)
        for phase, model in (("EXTRA_ABLATION", "/base"), ("S_A", "relative")):
            with self.assertRaises(ValueError):
                sequence.training_config(phase, model)

    def test_export_exact_masks_provenance_and_runtime_encoding_order(self):
        tokenizer = SyntheticTokenizer()
        with patch.object(sequence.trainer, "run_training", side_effect=AssertionError("no training")):
            result = self.export(tokenizer)
        self.assertEqual(result["status"], "TOKENIZED_MATERIAL_NOT_EXECUTED")
        self.token_check.assert_called_once_with(self.imported, tokenizer)
        for name, phase in result["phases"].items():
            sequence.prefix.unseal(phase, phase["sha256"])
            self.assertEqual(sequence.trainer.normalize_items(phase["items"]), phase["items"])
            encoded = []
            expected_pairs = [pair for batch in result["spec"]["phases"][name]["batches"] for pair in batch]
            for item_index, (item, (index, view)) in enumerate(zip(phase["items"], expected_pairs)):
                record = result["spec"]["records"][index]
                self.assertEqual(item["group"], f"batch/{item_index // 4:04}")
                self.assertEqual(item["order"], item_index % 4)
                self.assertEqual(item["view"], f"W{view}")
                self.assertEqual(item["spans"][0][1:], [False, "context"])
                self.assertEqual(item["spans"][1], [record["target"], True, "EVENT"])
                self.assertTrue(item["spans"][1][0].endswith("\n"))
                self.assertEqual(item["meta"]["capture_sha256"], record["generation"]["capture_sha256"])
                self.assertEqual(item["meta"]["source_sha256"], record["source_sha256"])
                segments = sequence.trainer.encode_item_segments(item, tokenizer, 512, item_index=item_index,
                                                                chat_template=False, add_eos=True, overflow="truncate")
                self.assertEqual(len(segments), 1)
                entry = segments[0]
                context = tokenizer.encode(item["spans"][0][0])
                target = tokenizer.encode(record["target"])
                self.assertEqual(entry.labels, [-100] * len(context) + target + [1])
                self.assertEqual((entry.context_dropped, entry.target_dropped), (0, 0))
                encoded.append(entry)
            actual = sequence.trainer.epoch_order(sequence.trainer.pack_by_group(encoded, 512, pack=False), 0, 0, False)
            self.assertEqual([entry[0].item_index for entry in actual], list(range(len(encoded))))
            self.assertEqual(phase["encoding_sha256"], sequence.prefix.digest([asdict(entry) for entry in encoded]))
            self.assertEqual(phase["supervised_tokens"], sum(entry.n_target for entry in encoded))
            self.assertEqual(phase["input_tokens"], sum(len(entry.ids) for entry in encoded))
        self.assertEqual(result, self.export(SyntheticTokenizer()))

    def test_tokenizer_errors_and_truncation_rejected(self):
        tokenizer = SyntheticTokenizer()
        tokenizer.eos_token_id = None
        with self.assertRaisesRegex(ValueError, "EOS"):
            self.export(tokenizer)
        tokenizer = SyntheticTokenizer()
        original = tokenizer.apply_chat_template
        with patch.object(tokenizer, "apply_chat_template", side_effect=lambda messages, tokenize, **kwargs:
                          [999] if tokenize else original(messages, tokenize=False, **kwargs)):
            with self.assertRaisesRegex(ValueError, "template/encode"):
                self.export(tokenizer)
        with patch.object(SyntheticTokenizer, "decode", return_value="normalized or wrong"):
            with self.assertRaisesRegex(ValueError, "roundtrip"):
                self.export()
        with patch.object(SyntheticTokenizer, "apply_chat_template") as render:
            tokenizer = SyntheticTokenizer()
            render.side_effect = lambda messages, tokenize, **kwargs: tokenizer.encode("x" * 1536) if tokenize else "x" * 1536
            with self.assertRaisesRegex(ValueError, "zero truncation"):
                self.export(tokenizer)
        with patch.object(sequence.prefix, "verify_tokenizer", side_effect=ValueError("tokenizer custody")):
            with self.assertRaisesRegex(ValueError, "custody"):
                self.export()

    def test_oversized_authentic_target_is_not_truncated(self):
        changed = copy.deepcopy(self.imported)
        changed.pop("sha256")
        raw = "SYNTHETIC_OVERSIZED_TARGET" * 100 + "\n"
        changed["rows"][0]["raw"] = changed["generations"][0]["raw"] = raw
        changed["queries"]["READ EVENT SYNTHETIC_EVENT_0"]["target"] = raw
        self.imported = sequence.seal(changed)
        with self.assertRaisesRegex(ValueError, "zero truncation"):
            self.export()

    def test_singleton_target_lineage_required(self):
        changed = copy.deepcopy(self.imported)
        changed.pop("sha256")
        changed["queries"]["READ EVENT SYNTHETIC_EVENT_0"]["support"].append("SYNTHETIC_EVENT_4")
        self.imported = sequence.seal(changed)
        with self.assertRaisesRegex(ValueError, "singleton child byte lineage"):
            self.spec()

    def test_resealed_spec_changes_rejected(self):
        spec = self.spec()
        self.assertEqual(sequence.validate_spec(spec, self.imported, self.imported["sha256"])["status"], "SPEC_VALIDATED_NOT_EXECUTED")
        changes = [lambda changed: changed["phases"]["SEQ_REPLAY"].update(parent_phase=None),
                   lambda changed: changed["phases"]["S_A"]["batches"][0][0].__setitem__(1, 8),
                   lambda changed: changed["records"][0].update(target="fabricated\n"),
                   lambda changed: changed.update(full_contract_released=True),
                   lambda changed: changed["sources"].clear()]
        for mutate in changes:
            changed = copy.deepcopy(spec)
            changed.pop("sha256")
            mutate(changed)
            with self.assertRaises(ValueError):
                sequence.validate_spec(sequence.seal(changed), self.imported, self.imported["sha256"])


@unittest.skipUnless(ARCHIVE.is_file() and REPLAY.is_file(), "fixed original archive/replay receipt unavailable")
class OriginalArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = json.loads(REPLAY.read_text())
        cls.imported = sequence.prefix.build_import(sequence.prefix.load_evidence(ARCHIVE), receipt, receipt["sha256"])

    def test_real_original_import_and_sequence_material(self):
        spec = sequence.build_spec(self.imported, self.imported["sha256"])
        self.assertEqual(len(spec["records"]), 8)
        self.assertEqual(spec["historical"]["original_status"], "FORMATION_FAILED")
        self.assertEqual(spec["historical"]["original_calls"], 17)
        self.assertTrue(spec["historical"]["format_scaffold"])
        for index, record in enumerate(spec["records"]):
            self.assertEqual(record["target"], self.imported["rows"][index]["raw"])
            self.assertEqual(record["target"], self.imported["generations"][index]["raw"])
            self.assertEqual(record["generation"]["origin"], "CHILD_NATIVE")
        sequence.validate_spec(spec, self.imported, self.imported["sha256"])

    def test_wrong_import_pin_and_resealed_raw_tamper_fail(self):
        with self.assertRaises(ValueError):
            sequence.build_spec(self.imported, "0" * 64)
        changed = copy.deepcopy(self.imported)
        changed.pop("sha256")
        changed["rows"][0]["raw"] += "\n"
        changed = sequence.seal(changed)
        with self.assertRaises(ValueError):
            sequence.build_spec(changed, changed["sha256"])


if __name__ == "__main__":
    unittest.main()
