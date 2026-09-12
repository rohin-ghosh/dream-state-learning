"""CPU label/receipt fixtures, not proof of real training execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6.train_adapter import child_label_counts, load_gate_binding, write_training_receipt


def digest(content):
    return hashlib.sha256(content).hexdigest()


class ChildTrainingReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.corpus_bytes = json.dumps(dict(recipe="preschool_records_v1", corpus=["child"])).encode()
        self.gate = dict(schema_version=1, recipe="preschool_records_v1", decision="ADMIT",
                         exposure_status="UNEXPOSED", previous_manifest_sha256="a" * 64,
                         corpus_sha256=digest(self.corpus_bytes),
                         admissions=[dict(record_sha256="b" * 64, source_sha256="c" * 64)])
        self.gate_path = self.root / "gate.json"
        self.gate_path.write_text(json.dumps(self.gate))
        self.gate_sha = digest(self.gate_path.read_bytes())

    def bind(self, **changes):
        arguments = dict(gate_path=self.gate_path, expected_sha256=self.gate_sha,
                         previous_sha256="a" * 64, corpus_bytes=self.corpus_bytes)
        arguments.update(changes)
        return load_gate_binding(**arguments)

    def test_gate_binds_exact_input_bytes(self):
        self.assertEqual(self.bind(), self.gate)
        with self.assertRaisesRegex(ValueError, "training inputs"):
            self.bind(corpus_bytes=self.corpus_bytes + b" ")
        with self.assertRaisesRegex(ValueError, "training inputs"):
            self.bind(previous_sha256="d" * 64)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.bind(expected_sha256="d" * 64)

    def test_non_admission_and_bad_hashes_fail_closed(self):
        for field, value in (("decision", "REJECT"), ("exposure_status", "UNKNOWN"),
                             ("admissions", []), ("admissions", [dict(record_sha256="x")])):
            with self.subTest(field=field):
                self.gate_path.write_text(json.dumps(dict(self.gate, **{field: value})))
                with self.assertRaises(ValueError):
                    self.bind(expected_sha256=digest(self.gate_path.read_bytes()))

    def test_counts_use_causal_shift_and_mask_boundaries(self):
        offsets = [(0, 2), (2, 4), (4, 6), (6, 9), (0, 0)]
        counts = child_label_counts(offsets, 5, [1, 1, 1, 1, 0], [-100, -100, -100, 15, -100])
        self.assertEqual(counts, dict(masked_prefix_tokens=2, supervised_prefix_tokens=0,
                                     supervised_child_tokens=1, supervised_padding_tokens=0))

    def test_prefix_padding_and_no_effective_target_fail(self):
        offsets = [(0, 2), (2, 4), (4, 8), (0, 0)]
        for labels in ([-100, 4, 9, -100], [-100, -100, 9, 0], [-100] * 4):
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                child_label_counts(offsets, 4, [1, 1, 1, 0], labels)
        with self.assertRaisesRegex(ValueError, "lengths"):
            child_label_counts(offsets, 4, [], [])

    def test_only_first_token_target_is_not_training_evidence(self):
        with self.assertRaisesRegex(ValueError, "causal-shift"):
            child_label_counts([(5, 8), (0, 0)], 4, [1, 0], [10, -100])

    def test_receipt_binds_actual_adapter_and_metadata_bytes(self):
        adapter = self.root / "adapter"
        adapter.mkdir()
        (adapter / "adapter_model.safetensors").write_bytes(b"fixture-not-real-weights")
        (adapter / "adapter_config.json").write_text('{"peft_type":"LORA"}')
        (adapter / "train_meta.json").write_text('{"epochs":3,"supervised_tokens":6}')
        counts = dict(masked_prefix_tokens=4, supervised_prefix_tokens=0,
                      supervised_child_tokens=2, supervised_padding_tokens=0)
        receipt_path = self.root / "trainer.json"
        receipt = write_training_receipt(receipt_path, adapter, self.gate, self.gate_sha, [counts])
        self.assertEqual(receipt["train_metadata_sha256"], digest((adapter / "train_meta.json").read_bytes()))
        self.assertEqual(receipt["adapter_files"]["adapter_model.safetensors"],
                         digest((adapter / "adapter_model.safetensors").read_bytes()))
        self.assertEqual(receipt["rows"][0]["source_sha256"], "c" * 64)
        self.assertEqual(receipt["rows"][0]["supervised_child_tokens"], 2)
        with self.assertRaises(FileExistsError):
            write_training_receipt(receipt_path, adapter, self.gate, self.gate_sha, [counts])
        with self.assertRaisesRegex(ValueError, "label counts"):
            write_training_receipt(self.root / "bad.json", adapter, self.gate, self.gate_sha,
                                   [dict(counts, supervised_child_tokens=3)])
        self.assertFalse((self.root / "bad.json").exists())


if __name__ == "__main__":
    unittest.main()
