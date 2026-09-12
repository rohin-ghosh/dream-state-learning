"""Synthetic CPU arrays and mocked immutable receipts; never native model weights."""
import ast
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
PATH = Path('/tmp/astra_rulegame_record_weight_audit_20260912.py')
spec = importlib.util.spec_from_file_location('record_weight_audit_tested', PATH)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
exec(compile(PATH.read_bytes(), str(PATH), 'exec'), audit.__dict__)


def encoded_values(values, dtype):
    if dtype == 'BF16':
        return b''.join(struct.pack('<H', struct.unpack('<I', struct.pack('<f', value))[0] >> 16) for value in values)
    return struct.pack('<' + ('f' if dtype == 'F32' else 'e') * len(values), *values)


def fixture(first=(3., 4., 0., -0.), second=(0., 12.), dtype='F32', mutate=None):
    first_bytes, second_bytes = encoded_values(first, dtype), encoded_values(second, dtype)
    header = {
        'base_model.model.layers.0.self_attn.q_proj.lora_A.weight': dict(dtype=dtype, shape=[1, len(first)], data_offsets=[0, len(first_bytes)]),
        'base_model.model.layers.0.self_attn.q_proj.lora_B.weight': dict(dtype=dtype, shape=[len(second), 1], data_offsets=[len(first_bytes), len(first_bytes) + len(second_bytes)]),
    }
    if mutate:
        mutate(header)
    header_bytes = json.dumps(header).encode()
    return struct.pack('<Q', len(header_bytes)) + header_bytes + first_bytes + second_bytes


class NumericalTests(unittest.TestCase):
    def stats(self, payload):
        with patch.object(Path, 'open', side_effect=lambda *args: io.BytesIO(payload)), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(payload))):
            return audit.tensor_stats(Path('/synthetic.safetensors'))

    def test_float32_total_and_split(self):
        result = self.stats(fixture())
        self.assertTrue(result['all_finite'])
        self.assertEqual(result['groups']['LoRA_A']['l2'], 5.)
        self.assertEqual(result['groups']['LoRA_B']['l2'], 12.)
        self.assertEqual(result['groups']['total']['l2'], 13.)
        self.assertEqual(result['groups']['total']['maxabs'], 12.)
        self.assertEqual(result['groups']['total']['entries'], 6)
        self.assertEqual(result['groups']['total']['nonzero_count'], 3)
        self.assertTrue(result['nonzero_B_from_declared_zero_init'])

    def test_float16(self):
        self.assertEqual(self.stats(fixture(dtype='F16'))['groups']['total']['l2'], 13.)

    def test_bfloat16(self):
        self.assertEqual(self.stats(fixture(dtype='BF16'))['groups']['total']['l2'], 13.)

    def test_zero_B_reported_not_rejected(self):
        result = self.stats(fixture(second=(0., -0.)))
        self.assertEqual(result['status'], 'FINITE')
        self.assertEqual(result['groups']['LoRA_B']['nonzero_count'], 0)
        self.assertFalse(result['nonzero_B_from_declared_zero_init'])

    def test_nonfinite_explicit_no_invalid_json_numbers(self):
        result = self.stats(fixture(second=(float('nan'), float('inf'))))
        self.assertEqual(result['status'], 'NONFINITE_TENSORS')
        self.assertEqual(result['groups']['total']['nonfinite_entries'], 2)
        self.assertEqual(result['groups']['total']['finite_entries'], 4)
        self.assertIsNone(result['groups']['total']['l2'])
        self.assertIsNone(result['groups']['total']['maxabs'])
        self.assertIsNone(result['groups']['LoRA_B']['nonzero_count'])
        self.assertEqual(result['groups']['LoRA_A']['l2'], 5.)
        json.dumps(result, allow_nan=False)

    def test_bfloat16_nonfinite(self):
        result = self.stats(fixture(dtype='BF16', second=(float('-inf'), 0.)))
        self.assertEqual(result['groups']['LoRA_B']['nonfinite_entries'], 1)

    def test_finite_float32_extremes_accumulate_float64(self):
        result = self.stats(fixture(first=(3e38, -3e38)))
        self.assertTrue(result['all_finite'])
        self.assertGreater(result['groups']['total']['l2'], 3e38)
        json.dumps(result, allow_nan=False)

    def test_truncated_payload_rejected(self):
        self.assertRaises(ValueError, self.stats, fixture()[:-1])

    def test_trailing_payload_rejected(self):
        self.assertRaises(ValueError, self.stats, fixture() + b'bad')

    def test_overlap_rejected(self):
        def change(header):
            header[next(name for name in header if name.endswith('B.weight'))]['data_offsets'] = [0, 8]
        self.assertRaises(ValueError, self.stats, fixture(mutate=change))

    def test_shape_rejected(self):
        def change(header):
            header[next(iter(header))]['shape'] = [1000]
        self.assertRaises(ValueError, self.stats, fixture(mutate=change))

    def test_missing_B_rejected(self):
        def change(header):
            name = next(name for name in header if name.endswith('B.weight'))
            header[name.replace('q_proj.lora_B', 'v_proj.lora_A')] = header.pop(name)
        self.assertRaises(ValueError, self.stats, fixture(mutate=change))

    def test_unsupported_dtype_rejected(self):
        def change(header):
            header[next(iter(header))]['dtype'] = 'I32'
        self.assertRaises(ValueError, self.stats, fixture(mutate=change))

    def test_multichunk_counts(self):
        result = self.stats(fixture(first=(1.,) * (262144 + 3), second=(0.,)))
        self.assertEqual(result['groups']['LoRA_A']['nonzero_count'], 262147)
        self.assertAlmostEqual(result['groups']['LoRA_A']['l2'] ** 2, 262147)


class CustodyTests(unittest.TestCase):
    def arm(self, mutate=False):
        files = {'adapter/adapter_model.safetensors': 'weight-sha', 'receipt.json': 'receipt-sha'}
        receipt = dict(steps=12, adapter=str(audit.ROOT / 'fits/P/adapter'), files={'adapter_model.safetensors': 'weight-sha'})
        completed = dict(receipt, fit_manifest_sha256='manifest-sha', supervision_sha256='supervision-sha')
        values = {'manifest.json': {'files': files}, 'receipt.json': receipt,
            'pre_update_trainability.json': {'init_adapter': None, 'base_frozen': True, 'adapter_count': 1, 'adapters': {}}}
        after = dict(files, **{'adapter/adapter_model.safetensors': 'changed'}) if mutate else files
        bridge = SimpleNamespace(saved_weights=Mock())
        with patch.object(audit, 'digest', side_effect=lambda path: 'manifest-sha' if path.name == 'manifest.json' else 'supervision-sha'), \
             patch.object(audit, 'read', side_effect=lambda path: values[path.name]), \
             patch.object(audit.common, 'capture_files', side_effect=[files, after]) as inventories, \
             patch.object(audit, 'tensor_stats', return_value={'status': 'FINITE'}) as scan:
            result = audit.audit_arm('P', {'arms': {'P': completed}}, bridge)
            self.assertEqual(inventories.call_count, 2)
            bridge.saved_weights.assert_called_once()
            scan.assert_called_once()
            return result

    def test_before_after_hashes_recorded(self):
        result = self.arm()
        self.assertEqual(result['files_before'], result['files_after'])
        self.assertEqual(result['weight_sha256_before'], result['weight_sha256_after'])

    def test_mutation_rejected(self):
        self.assertRaisesRegex(ValueError, 'changed during', self.arm, True)

    def test_existing_receipt_no_overwrite(self):
        with patch.object(audit.common, 'unaliased', side_effect=Path), patch.object(Path, 'exists', return_value=True), \
             patch.object(audit.common, 'write_json', side_effect=AssertionError('write')):
            self.assertRaisesRegex(ValueError, 'fresh external', audit.run)

    def test_receipt_inside_run_rejected(self):
        with patch.object(audit.common, 'unaliased', side_effect=Path), patch.object(Path, 'exists', return_value=False), \
             patch.object(Path, 'is_dir', return_value=True):
            self.assertRaisesRegex(ValueError, 'outside', audit.run, audit.ROOT / 'extra.json')

    def test_timeout_is_not_swallowed_per_arm(self):
        self.assertFalse(issubclass(audit.AuditExpired, Exception))
        self.assertRaises(audit.AuditExpired, audit.expired, 0, None)

    def test_no_model_or_gpu_imports_calls(self):
        tree = ast.parse(PATH.read_text())
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {'checked_plan', 'modules', 'load_native', 'validate_fit', 'run_training', 'check_free', 'native_tokenizer', 'write_pair'})
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [name.name for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names]
        self.assertFalse(set(imports) & {'torch', 'safetensors.torch', 'transformers'})

    def test_failure_receipt_and_alarm_cleanup(self):
        writes = []
        with patch.object(audit.common, 'unaliased', side_effect=Path), patch.object(Path, 'exists', return_value=False), \
             patch.object(Path, 'is_dir', return_value=True), patch.object(audit, 'digest', return_value='bad-plan'), \
             patch.object(audit.signal, 'signal'), patch.object(audit.signal, 'setitimer') as timer, \
             patch.object(audit.common, 'write_json', side_effect=lambda path, data: writes.append((path, data))), \
             patch.object(audit, 'load', side_effect=AssertionError('model load')):
            result = audit.run()
        self.assertEqual(result['status'], 'ERROR')
        self.assertIn('plan changed', writes[0][1]['error'])
        self.assertEqual(writes[0][0], audit.DEFAULT_RECEIPT)
        self.assertEqual(timer.call_args_list[0].args[1], 300)
        self.assertEqual(timer.call_args_list[-1].args[1], 0)


if __name__ == '__main__':
    unittest.main()
