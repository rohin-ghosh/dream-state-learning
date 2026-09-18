import hashlib
import json
from pathlib import Path
import unittest

from organism_v6 import composition_birth_stage2a_primitives as source


class CanonicalJsonTests(unittest.TestCase):
    def test_exact_sorted_bytes_and_roundtrip(self):
        value = {"z": [True, False, None, -2, "line\nnext\t"], "a": {"q": 0}}
        expected = b'{"a":{"q":0},"z":[true,false,null,-2,"line\\nnext\\t"]}'
        self.assertEqual(source.canonical_json(value), expected)
        self.assertEqual(source.parse_canonical_json(expected), value)
        self.assertEqual(source.parse_canonical_json(expected.decode()), value)

    def test_supported_scalars_and_shared_subtrees(self):
        for value in (None, True, False, 0, -12, "text", [], {}):
            self.assertEqual(source.parse_canonical_json(source.canonical_json(value)), value)
        shared = ["a"]
        self.assertEqual(source.canonical_json([shared, shared]), b'[["a"],["a"]]')

    def test_reject_invalid_values_at_all_depths(self):
        class Integer(int):
            pass
        for value in (0.0, -0.0, float("nan"), float("inf"), (1,), {1}, b"a",
                      {1: "a"}, "é", "\ud800", "\r", "\0", Integer(1), object()):
            for wrapped in (value, [value], {"value": value}):
                with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                    source.canonical_json(wrapped)

    def test_reject_duplicates_negative_zero_floats_and_constants(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}', b'{"v":{"a":1,"a":2}}',
                    b'-0', b'[-0]', b'0.0', b'-0.0', b'1e0', b'NaN', b'Infinity', b'-Infinity',
                    b'{"v":"\\u0000"}', b'{"v":"\\r"}', b'"\\u00e9"', b'"\\ud800"'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                source.parse_canonical_json(raw)

    def test_reject_noncanonical_and_invalid_encoding(self):
        for raw in (b' {"a":1}', b'{"b":1,"a":2}', b'{"a": 1}', b'{}\n', b'{}\r',
                    b'"\\u0061"', b'"\\/"', b'"\xff"', '"é"', b'{}\0', bytearray(b'{}'), 0):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                source.parse_canonical_json(raw)

    def test_cycles_and_depth_fail_closed(self):
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(ValueError):
            source.canonical_json(cycle)
        nested = []
        for index in range(1100):
            nested = [nested]
        with self.assertRaises(ValueError):
            source.canonical_json(nested)
        with self.assertRaises(ValueError):
            source.parse_canonical_json(b'[' * 1100 + b']' * 1100)

    def test_all_pinned_v4_cjson_vectors_roundtrip(self):
        path = Path(__file__).resolve().parents[1] / 'research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md'
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), source.MEMO_SHA256)
        vectors = [line for line in raw.splitlines() if line.startswith((b'{"', b'[{"'))]
        self.assertGreaterEqual(len(vectors), 7)
        for vector in vectors:
            self.assertEqual(source.canonical_json(source.parse_canonical_json(vector)), vector)
            self.assertEqual(source.parse_canonical_json(vector), json.loads(vector))


class SeedTests(unittest.TestCase):
    MASTER = b'SYNTHETIC-ONLY-PRIMITIVE-TEST'

    def expected(self, raw):
        return int(hashlib.sha256(raw).hexdigest()[-16:], 16)

    def test_u32_and_low64_exact(self):
        self.assertEqual(source.u32(0), b'\0\0\0\0')
        self.assertEqual(source.u32(2 ** 32 - 1), b'\xff\xff\xff\xff')
        self.assertEqual(source.u32(258), b'\0\0\x01\x02')
        for raw in (b'', b'abc', bytes(range(256))):
            self.assertEqual(source.low64(raw), self.expected(raw))
        for invalid in (True, -1, 2 ** 32, 1.0, '1'):
            with self.assertRaises(ValueError):
                source.u32(invalid)
        with self.assertRaises(ValueError):
            source.low64('abc')

    def test_all_slots_cover_unique_global_ordinals(self):
        slots = []
        for stage in ('D1', 'D2'):
            for world in range(16):
                for member in range(2):
                    for call in range(29):
                        slots.append(source.chain_slot(stage, world, member, call))
            for transition in ('SEEK', 'PROSPECT', 'CHECK', 'CONTINUE'):
                for pair in range(8):
                    for member in range(2):
                        slots.append(source.intervention_slot(stage, transition, pair, member))
            for index in range(16):
                slots.append(source.canary_slot(stage, index))
        self.assertEqual([slot.global_ordinal for slot in slots], list(range(2016)))
        self.assertEqual(len({slot.panel_label for slot in slots}), 12)
        for slot in slots:
            raw = self.MASTER + b'\0decode\0' + slot.panel_label.encode() + b'\0' + slot.global_ordinal.to_bytes(4, 'big')
            self.assertEqual(source.decode_seed(self.MASTER, slot.panel_label, slot.global_ordinal), self.expected(raw))

    def test_label_ordinal_mismatch_and_invalid_numbers(self):
        for label, ordinal in (('D2_CHAIN', 0), ('D1_CHAIN', 928), ('D1_INTERVENTION_SEEK', 944),
                               ('D1_INTERVENTION_CONTINUE', 992), ('D1_CANARY', 1008),
                               ('D1_CHAIN_BASE', 0), ('D2_CANARY', 2016), ('D1_CHAIN', True),
                               (['D1_CHAIN'], 0), ('D1_CHAIN', -1)):
            with self.subTest(label=label, ordinal=ordinal), self.assertRaises(ValueError):
                source.decode_seed(self.MASTER, label, ordinal)

    def test_slot_input_validation(self):
        cases = (
            lambda: source.chain_slot('D3', 0, 0, 0),
            lambda: source.chain_slot('D1', 16, 0, 0),
            lambda: source.chain_slot('D1', 0, 2, 0),
            lambda: source.chain_slot('D1', 0, 0, 29),
            lambda: source.chain_slot('D1', 0, 0, True),
            lambda: source.intervention_slot('D1', 'READ_CHECK', 0, 0),
            lambda: source.intervention_slot('D1', 'SEEK', 8, 0),
            lambda: source.canary_slot('D1', 16),
            lambda: source.canary_slot(None, 0),
        )
        for case in cases:
            with self.assertRaises(ValueError):
                case()

    def test_initialization_and_all_paired_update_seeds(self):
        self.assertEqual(source.adapter_seed(self.MASTER), self.expected(self.MASTER + b'\0adapter-init'))
        for update in range(1, 513):
            expected = self.expected(self.MASTER + b'\0dropout\0' + update.to_bytes(4, 'big'))
            self.assertEqual(source.dropout_seed(self.MASTER, update), expected)
        for update in (0, 513, True, '1'):
            with self.assertRaises(ValueError):
                source.dropout_seed(self.MASTER, update)
        for master in ('implicit', b'', b'has\0separator', b'\xff', bytearray(b'abc')):
            with self.assertRaises(ValueError):
                source.adapter_seed(master)

    def test_source_only_no_science_opening(self):
        self.assertEqual(source.STATUS, 'PARTIAL_SOURCE_ONLY')
        self.assertFalse(any(source.SCIENCE_GATES.values()))


if __name__ == '__main__':
    unittest.main()
