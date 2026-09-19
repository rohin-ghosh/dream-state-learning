"""CPU-only source binding and exact synthetic-batch regression tests."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from gpu import orch_r163_probe_driver as driver


class ProbeDriverTests(unittest.TestCase):
    def test_hash_bound_json_and_changed_bytes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/'PLAN.json'
            path.write_text('{"value": 1}')
            expected = driver.file_sha(path)
            self.assertEqual(driver.read_bound(path, expected), {'value': 1})
            path.write_text('{"value": 2}')
            with self.assertRaisesRegex(ValueError, 'pinned_file_bytes'):
                driver.read_bound(path, expected)

    def test_source_manifest_changed_file_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/'source.py'
            path.write_text('value = 1\n')
            manifest = dict(schema='R163_PROBE_SOURCE_PINS_V1', files={str(path): driver.file_sha(path)})
            driver.verify_sources(manifest)
            path.write_text('value = 2\n')
            with self.assertRaisesRegex(ValueError, 'exact_probe_dependency_bytes'):
                driver.verify_sources(manifest)

    def test_symlink_source_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/'source.py'
            link = Path(directory)/'alias.py'
            path.write_text('value = 1\n')
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, 'canonical_pinned_file'):
                driver.read_bound(link, driver.file_sha(path))

    def test_exact_own_lengths_and_unmodified_anchor_masks(self):
        from gpu.orch_r161_native_executor import FAMILIES
        tokenizer = SimpleNamespace(encode=lambda text, add_special_tokens: [3, 4, 5], all_special_ids=[0, 1, 2])
        anchor = SimpleNamespace(input_ids=(3, 4, 5, 6), labels=(-100, 4, 5, -100), target_ids=(4, 5))
        anchors = {family: [dict(encoded=anchor)] for family in FAMILIES}
        for length in (64, 512, 1024, 16384):
            batch = driver.validation_batch(tokenizer, anchors, length)
            own = batch.components[0]
            self.assertEqual(len(own.input_ids), length)
            self.assertEqual(own.labels, (-100,)*(length-3)+(3, 4, 5))
            self.assertEqual(own.input_ids[-3:], own.target_ids)
            self.assertEqual([part.objective_weight for part in batch.components], [0.75]+[0.0625]*4)
            for component in batch.components[1:]:
                self.assertEqual(component.input_ids, anchor.input_ids)
                self.assertEqual(component.labels, anchor.labels)
                self.assertEqual(component.target_ids, anchor.target_ids)
            raw = json.dumps(asdict(batch), sort_keys=True, separators=(',', ':')).encode()
            self.assertEqual(batch.sha256, hashlib.sha256(raw).hexdigest())

    def test_special_synthetic_tokens_and_long_anchors_rejected(self):
        from gpu.orch_r161_native_executor import FAMILIES
        tokenizer = SimpleNamespace(encode=lambda text, add_special_tokens: [3, 4], all_special_ids=[3])
        with self.assertRaisesRegex(ValueError, 'ordinary_synthetic_validation_tokens'):
            driver.validation_batch(tokenizer, {}, 64)
        tokenizer.all_special_ids = [0]
        anchors = {family: [dict(encoded=SimpleNamespace(input_ids=(3,)*1025))] for family in FAMILIES}
        with self.assertRaisesRegex(ValueError, 'full_anchor_capacity_bound'):
            driver.validation_batch(tokenizer, anchors, 64)

    def test_one_token_and_rehearsal_keep_full_anchors(self):
        from gpu.orch_r161_native_executor import FAMILIES
        tokenizer = SimpleNamespace(encode=lambda text, add_special_tokens: [3, 4, 5], all_special_ids=[0])
        sample = SimpleNamespace(input_ids=(3, 4, 5), labels=(-100, 4, 5), target_ids=(4, 5))
        anchors = {family: [dict(encoded=sample)] for family in FAMILIES}
        batch = driver.validation_batch(tokenizer, anchors, 64, label='REHEARSAL', one_token=True)
        self.assertEqual(batch.components[0].label, 'REHEARSAL')
        self.assertEqual(batch.components[0].target_ids, (3,))
        self.assertEqual(batch.components[0].labels, (-100,)*63+(3,))
        self.assertTrue(all(part.labels == sample.labels for part in batch.components[1:]))


if __name__ == '__main__':
    unittest.main()
