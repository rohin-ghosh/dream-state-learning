"""Bounded synthetic CPU custody checks, not full-population/native admission."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_custody as custody
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6.composition_birth_stage2a_primitives import canonical_json
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


MASTER = b"synthetic-v6-shared-custody-only\x00\xff"


def encoded_field(node, name):
    return next(entry[1] for entry in node["fields"] if entry[0] == name)


def replace_encoded_field(node, name, value):
    next(entry for entry in node["fields"] if entry[0] == name)[1] = value


def rehashed_record(record, prefix):
    raw = targets.messages_bytes(prefix)
    return replace(record, prefix=prefix, prefix_sha256=sha256(raw).hexdigest(),
                   content_bytes=sum(len(message.content.encode("ascii")) for message in prefix),
                   serialized_bytes=len(raw))


class BirthSourceCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = {number: synthetic_bindings(number) for number in (2, 25)}
        cls.custodies = {number: custody.BirthSourceCustody(
            world=f"p{number:02d}", role_tokens=bindings, display_master=MASTER)
            for number, bindings in cls.bindings.items()}
        cls.pairs = {number: birth.build_birth_pair(
            world=f"p{number:02d}", role_tokens=bindings, display_master=MASTER)
            for number, bindings in cls.bindings.items()}
        cls.records = {number: tuple(record for case in pair.cases
            for paired in targets.serialize_birth_case(case, role_tokens=pair.role_tokens)
            for record in (paired.closed, paired.atom_local)) for number, pair in cls.pairs.items()}

    def test_complete_lossless_pair_roles_master_counts_and_pins(self):
        for number, retained in self.custodies.items():
            with self.subTest(world=number):
                pair = self.pairs[number]
                document = json.loads(retained.shared_bytes)
                self.assertEqual(canonical_json(document), retained.shared_bytes)
                self.assertEqual(document["pair"], source_inputs._digest_value(pair))
                self.assertEqual(bytes.fromhex(document["display_master"]["bytes_hex"]), MASTER)
                self.assertEqual(dict(encoded_field(document["pair"], "role_tokens")["mapping"]),
                                 self.bindings[number])
                self.assertEqual(document["constructor"], source_inputs.CONSTRUCTOR_API)
                self.assertEqual(document["constructor_version"], birth.MEMO_SHA256)
                self.assertEqual(document["contract_hashes"], dict(source_inputs.CONTRACT_HASHES))
                self.assertEqual(document["source_schema"], source_inputs.SCHEMA_VERSION)
                self.assertEqual(document["counts"]["cases"], 2)
                self.assertEqual(document["counts"]["targets"], 8)
                self.assertEqual(document["counts"]["arm_records"], 16)
                self.assertEqual(document["counts"]["role_entries"], len(pair.role_tokens))
                for case, counts in zip(pair.cases, document["counts"]["members"]):
                    self.assertEqual(counts["registry_entries"], len(case.construction.registry))
                    self.assertEqual(counts["service_blocks"], len(case.construction.blocks))
                    self.assertEqual(counts["service_rows"], sum(
                        len(block.rows) for block in case.construction.blocks.values()))
                    self.assertEqual(counts["effective_edges"], len(case.construction.world_edges))
                    self.assertEqual(counts["trace_turns"], len(case.trace))
                    digest = sha256(canonical_json(source_inputs._digest_value(case))).hexdigest()
                    self.assertEqual(document["case_sha256"][case.descriptor.member], digest)
                self.assertEqual(retained.shared_sha256, sha256(retained.shared_bytes).hexdigest())
                self.assertTrue(retained.verify_shared(retained.shared_bytes))
                self.assertEqual(retained.cases, pair.cases)
                self.assertIs(type(retained.cases), tuple)

    def test_all_fixture_records_have_independently_derived_exact_pins(self):
        identities = set()
        for number, records in self.records.items():
            retained = self.custodies[number]
            for record in records:
                result = retained.source_for(record)
                self.assertIs(type(result), source_inputs.ValidatedBirthSource)
                self.assertEqual(result.record, record)
                self.assertIsNot(result.record, record)
                self.assertEqual(result.record_sha256,
                                 sha256(canonical_json(source_inputs._digest_value(record))).hexdigest())
                self.assertEqual(result.display_master_sha256, sha256(MASTER).hexdigest())
                self.assertEqual(result.role_tokens_sha256,
                                 sha256(canonical_json(self.bindings[number])).hexdigest())
                self.assertEqual(result.provenance_sha256, sha256(result.provenance_bytes).hexdigest())
                identities.add((record.unit.unit_id, record.arm))
            for member in ("m0", "m1"):
                case = next(case for case in self.pairs[number].cases if case.descriptor.member == member)
                record = next(record for record in records if f"/{member}/" in record.unit.unit_id)
                expected = source_inputs.validate_birth_source(
                    case=case, record=record, role_tokens=self.bindings[number], display_master=MASTER)
                self.assertEqual(retained.source_for(record), expected)
        self.assertEqual(len(identities), 32)

    def test_one_pair_encoding_and_no_rebuild_encoding_or_hashing_during_access(self):
        top_level_calls = Counter()
        original = source_inputs._digest_value

        def observed(value):
            top_level_calls[type(value).__name__] += 1
            return original(value)

        with patch.object(birth, "build_birth_pair", wraps=birth.build_birth_pair) as constructor:
            with patch.object(source_inputs, "_digest_value", side_effect=observed):
                retained = custody.BirthSourceCustody(
                    world="p02", role_tokens=self.bindings[2], display_master=MASTER)
            self.assertEqual(constructor.call_count, 1)
            self.assertEqual(top_level_calls["BirthPair"], 1)
            self.assertEqual(top_level_calls["BirthCase"], 2)
            self.assertEqual(top_level_calls["ArmRecord"], 16)
        with patch.object(birth, "build_birth_pair", side_effect=AssertionError("rebuild at boundary")), \
                patch.object(targets, "serialize_birth_case", side_effect=AssertionError("render at boundary")), \
                patch.object(source_inputs, "_digest_value", side_effect=AssertionError("encode at boundary")), \
                patch.object(custody, "canonical_json", side_effect=AssertionError("json at boundary")), \
                patch.object(custody, "sha256", side_effect=AssertionError("hash at boundary")):
            for unused in range(3):
                for record in self.records[2]:
                    result = retained.source_for(record)
                    self.assertEqual(result.record, record)
                self.assertTrue(retained.verify_shared(retained.shared_bytes))
            self.assertEqual(retained.cases, self.pairs[2].cases)

    def test_recover_exact_bytes_without_decoding_arbitrary_classes(self):
        for retained in self.custodies.values():
            recovered = custody.BirthSourceCustody.from_bytes(retained.shared_bytes)
            self.assertEqual(recovered.shared_bytes, retained.shared_bytes)
            self.assertEqual(recovered.shared_sha256, retained.shared_sha256)
            self.assertEqual(recovered.cases, retained.cases)
            number = int(recovered.cases[0].descriptor.world[1:])
            for record in self.records[number]:
                self.assertEqual(recovered.source_for(record), retained.source_for(record))

    def test_verify_shared_requires_exact_bytes_not_endpoints_or_hash(self):
        retained = self.custodies[2]
        raw = retained.shared_bytes
        middle = len(raw) // 2
        changed = raw[:middle] + bytes([raw[middle] ^ 1]) + raw[middle + 1:]
        self.assertEqual(changed[:100], raw[:100])
        self.assertEqual(changed[-100:], raw[-100:])
        for candidate in (changed, raw[:-1], raw + b"\n", raw[::-1], raw.decode("ascii"),
                          bytearray(raw), retained.shared_sha256.encode("ascii"),
                          self.custodies[25].shared_bytes, b"{}"):
            with self.subTest(kind=type(candidate).__name__, size=len(candidate)):
                with self.assertRaises(custody.CustodyError):
                    retained.verify_shared(candidate)

    def test_recovery_rejects_changed_middle_registry_even_with_rehashed_case(self):
        retained = self.custodies[2]
        document = json.loads(retained.shared_bytes)
        case = encoded_field(document["pair"], "cases")["tuple"][0]
        construction = encoded_field(case, "construction")
        registry = encoded_field(construction, "registry")["mapping"]
        entry = registry[len(registry) // 2]
        text = entry[1]
        middle = len(text) // 2
        entry[1] = text[:middle] + ("Z" if text[middle] != "Z" else "Y") + text[middle + 1:]
        document["case_sha256"]["m0"] = sha256(canonical_json(case)).hexdigest()
        forged = canonical_json(document)
        with self.assertRaises(custody.CustodyError):
            retained.verify_shared(forged)
        with self.assertRaisesRegex(custody.CustodyError, "exact_shared_source_mismatch"):
            custody.BirthSourceCustody.from_bytes(forged)

    def test_recovery_rejects_complete_case_data_tampering(self):
        for component in ("descriptor", "task", "task_text", "trace", "facts", "targets",
                          "blocks", "world_edges", "case_order"):
            with self.subTest(component=component):
                document = json.loads(self.custodies[2].shared_bytes)
                cases = encoded_field(document["pair"], "cases")["tuple"]
                if component == "case_order":
                    cases.reverse()
                elif component in ("blocks", "world_edges"):
                    mapping = encoded_field(encoded_field(cases[0], "construction"), component)["mapping"]
                    mapping.pop(len(mapping) // 2)
                else:
                    replace_encoded_field(cases[0], component, None)
                with self.assertRaisesRegex(custody.CustodyError, "exact_shared_source_mismatch"):
                    custody.BirthSourceCustody.from_bytes(canonical_json(document))

    def test_master_and_complete_role_input_binding_not_just_record_hashes(self):
        retained = self.custodies[2]
        changed_master = custody.BirthSourceCustody(
            world="p02", role_tokens=self.bindings[2], display_master=MASTER + b"different")
        changed_roles = dict(self.bindings[2])
        keys = [role for role in changed_roles if role.endswith("/receipt")][-2:]
        changed_roles[keys[0]], changed_roles[keys[1]] = changed_roles[keys[1]], changed_roles[keys[0]]
        alternate = custody.BirthSourceCustody(world="p02", role_tokens=changed_roles, display_master=MASTER)
        for foreign in (changed_master, alternate):
            with self.assertRaises(custody.CustodyError):
                retained.verify_shared(foreign.shared_bytes)
        for changed in ("master", "roles"):
            with self.subTest(changed=changed):
                document = json.loads(retained.shared_bytes)
                if changed == "master":
                    document["display_master"]["bytes_hex"] = (MASTER + b"different").hex()
                    document["display_master_sha256"] = sha256(MASTER + b"different").hexdigest()
                else:
                    encoded_roles = encoded_field(document["pair"], "role_tokens")["mapping"]
                    for entry in encoded_roles:
                        entry[1] = changed_roles[entry[0]]
                    document["role_tokens_sha256"] = sha256(canonical_json(changed_roles)).hexdigest()
                with self.assertRaisesRegex(custody.CustodyError, "exact_shared_source_mismatch"):
                    custody.BirthSourceCustody.from_bytes(canonical_json(document))

    def test_foreign_case_arm_record_and_type_strict_forgery(self):
        retained = self.custodies[25]
        record = self.records[25][-2]
        other_member = next(candidate for candidate in self.records[25]
                            if "/m0/" in candidate.unit.unit_id and candidate.arm == record.arm)
        forged_unit = replace(record.unit, unit_id=other_member.unit.unit_id)
        prefix = record.prefix
        middle = len(prefix) // 2
        changed_prefix = prefix[:middle] + (replace(prefix[middle], content=prefix[middle].content + "X"),) \
            + prefix[middle + 1:]
        for forged in (
                self.records[2][0], replace(record, arm="ATOM_LOCAL"), replace(record, arm="OTHER"),
                replace(record, unit=forged_unit), replace(record, unit=replace(record.unit, phase="OTHER")),
                replace(record, unit=replace(record.unit, target_bytes=b"THINK", target_sha256=sha256(b"THINK").hexdigest())),
                replace(record, unit=replace(record.unit, selection_index=True)),
                replace(record, content_bytes=True), replace(record, serialized_bytes=0),
                replace(record, prefix_sha256="0" * 64), replace(record, prefix=list(prefix)),
                rehashed_record(record, changed_prefix), rehashed_record(record, prefix[:-1]),
                rehashed_record(record, (prefix[1], prefix[0]) + prefix[2:]),
                rehashed_record(record, prefix + (prefix[1],)),
                replace(record, arm=[]), replace(record, unit=None), None,
        ):
            with self.subTest(kind=type(forged).__name__), self.assertRaises(custody.CustodyError):
                retained.source_for(forged)

    def test_shared_document_pins_counts_schema_and_unknown_fields_rejected(self):
        retained = self.custodies[2]
        for key, value in (("schema", "unrecognized"), ("constructor", "os.system"),
                           ("constructor_version", "forged"), ("source_schema", "forged"),
                           ("renderer", "forged"), ("renderer_contract_hashes", {}),
                           ("contract_hashes", {}), ("case_sha256", {}),
                           ("role_tokens_sha256", "0" * 64), ("display_master_sha256", "0" * 64),
                           ("counts", {}), ("allocator_admission", "APPROVED"), ("unexpected", True)):
            with self.subTest(key=key):
                document = json.loads(retained.shared_bytes)
                document[key] = value
                with self.assertRaises(custody.CustodyError):
                    custody.BirthSourceCustody.from_bytes(canonical_json(document))

    def test_safe_fixed_schema_rejects_duplicates_and_noncanonical_input(self):
        retained = self.custodies[2]
        raw = retained.shared_bytes
        for candidate in (raw + b"\n", b'{"schema":"x","schema":"y"}', b"[]", b"null", b"NaN",
                          b"1.0", b"\xff", b"[" * 1500, b"cos\nsystem\n(S'echo unsafe'\ntR.",
                          raw.decode("ascii"), bytearray(raw)):
            with self.subTest(kind=type(candidate).__name__), self.assertRaises(custody.CustodyError):
                custody.BirthSourceCustody.from_bytes(candidate)
        for kind in ("class", "fields", "duplicate_role", "role_shape", "master_hex"):
            document = json.loads(raw)
            pair = document["pair"]
            if kind == "class":
                pair["dataclass"] = "os.system"
            elif kind == "fields":
                pair["fields"].append(pair["fields"][0])
            elif kind == "duplicate_role":
                roles = encoded_field(pair, "role_tokens")["mapping"]
                roles.append(roles[0])
            elif kind == "role_shape":
                encoded_field(pair, "role_tokens")["mapping"][0][0] = []
            else:
                document["display_master"]["bytes_hex"] = MASTER.hex().upper()
            with self.subTest(kind=kind), self.assertRaises(custody.CustodyError):
                custody.BirthSourceCustody.from_bytes(canonical_json(document))

    def test_returned_snapshots_and_input_aliases_cannot_poison_cache(self):
        bindings = dict(self.bindings[2])
        retained = custody.BirthSourceCustody(world="p02", role_tokens=bindings, display_master=MASTER)
        expected_raw = retained.shared_bytes
        bindings.clear()
        case = retained.cases[0]
        with self.assertRaises(FrozenInstanceError):
            case.status = "READY"
        with self.assertRaises(TypeError):
            case.construction.registry["foreign"] = "MISS"
        object.__setattr__(case.descriptor, "world", "p31")
        block = next(iter(case.construction.blocks.values()))
        object.__setattr__(block, "rows", ())
        object.__setattr__(case.construction, "registry", MappingProxyType({}))
        result = retained.source_for(self.records[2][0])
        with self.assertRaises(TypeError):
            result.role_tokens["foreign"] = "foreign"
        object.__setattr__(result.case.facts, "selected_query", "forged")
        object.__setattr__(result.record.prefix[0], "content", "forged")
        object.__setattr__(result.record.unit, "phase", "forged")
        object.__setattr__(result, "case_sha256", "forged")
        self.assertEqual(retained.shared_bytes, expected_raw)
        self.assertEqual(retained.cases, self.pairs[2].cases)
        fresh = retained.source_for(self.records[2][0])
        self.assertEqual(fresh.record, self.records[2][0])
        self.assertEqual(fresh.case, self.pairs[2].cases[0])
        self.assertNotEqual(fresh.case_sha256, "forged")
        with self.assertRaises(FrozenInstanceError):
            retained.shared_bytes = b"forged"

    def test_constructor_rejects_invalid_inputs_and_enforces_bounds(self):
        inputs = dict(world="p02", role_tokens=self.bindings[2], display_master=MASTER)
        invalid_roles = dict(self.bindings[2])
        invalid_roles[next(iter(invalid_roles))] = "invalid"
        for overrides in ({"world": "p32"}, {"world": True}, {"role_tokens": {}},
                          {"role_tokens": []}, {"role_tokens": invalid_roles},
                          {"role_tokens": self.bindings[25]}, {"display_master": bytearray(MASTER)},
                          {"display_master": "text"}):
            with self.subTest(keys=tuple(overrides)), self.assertRaises(custody.CustodyError):
                custody.BirthSourceCustody(**{**inputs, **overrides})
        for limit, value in (("master_bytes", 1), ("role_entries", 1), ("shared_bytes", 1)):
            with self.subTest(limit=limit), patch.object(custody, "BOUNDS", {**custody.BOUNDS, limit: value}):
                with self.assertRaises(custody.CustodyError):
                    custody.BirthSourceCustody(**inputs)
        with patch.object(custody, "BOUNDS", {**custody.BOUNDS, "shared_bytes": 1}):
            with self.assertRaises(custody.CustodyError):
                custody.BirthSourceCustody.from_bytes(self.custodies[2].shared_bytes)

    def test_empty_master_supported_and_no_authority_or_readiness_claimed(self):
        retained = custody.BirthSourceCustody(world="p02", role_tokens=self.bindings[2], display_master=b"")
        self.assertEqual(custody.BirthSourceCustody.from_bytes(retained.shared_bytes).shared_bytes,
                         retained.shared_bytes)
        self.assertEqual(retained.status, "PARTIAL_SOURCE_ONLY")
        self.assertEqual(retained.allocator_admission, "NOT_VERIFIED_MAIN_NATIVE_TASK")
        self.assertFalse(any(retained.science_gates.values()))
        self.assertFalse(any(custody.SCIENCE_GATES.values()))
        self.assertFalse(any((custody.GO_WRITE_ROOT, custody.GO_MATERIALIZE, custody.GO_MODEL_TOKENIZER,
                              custody.GO_FIT_OR_GPU, custody.GO_CLAIM)))


if __name__ == "__main__":
    unittest.main()
