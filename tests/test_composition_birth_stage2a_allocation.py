"""Full finite CPU allocation, without native preparation or outcome selection."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_allocation as source


MASTER = b"STAGE2A_CPU_QUALIFICATION\x00\xff"


class Stage2AAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls = []
        cls.inventory_calls = []
        prior = []
        allocator = wire.allocate_opaque_namespace
        enumerator = wire.enumerate_symbolic_role_inventory

        def allocate(**inputs):
            if inputs["occupied_tokens"] != tuple(prior):
                raise AssertionError("complete prior namespace collision context required")
            if inputs["master"] != MASTER:
                raise AssertionError("explicit master must be passed unchanged")
            namespace = allocator(**inputs)
            cls.calls.append((inputs["domain"], inputs["kind"], len(prior)))
            prior.extend(namespace.serial_tokens)
            return namespace

        def enumerate_roles(domain):
            cls.inventory_calls.append(domain)
            return enumerator(domain)

        with patch.object(wire, "allocate_opaque_namespace", side_effect=allocate), \
                patch.object(wire, "enumerate_symbolic_role_inventory", side_effect=enumerate_roles), \
                patch("builtins.open", side_effect=AssertionError("file access forbidden")), \
                patch.object(Path, "read_bytes", side_effect=AssertionError("file read forbidden")), \
                patch.object(Path, "write_bytes", side_effect=AssertionError("file write forbidden")):
            cls.allocation = source.allocate_stage2a(master=MASTER)

    def test_closed_counts_complete_bytes_hashes_and_collision_context(self):
        expected_counts = {
            "birth_train": (2080, 61512, 49216, 12288, 49216, 49216, 223528),
            "dose_intervention": (2080, 3840, 3072, 768, 3072, 3072, 15904),
            "dose_chain": (1040, 17344, 13888, 3456, 13888, 13888, 63504),
            "generic_canary": (2, 2, 4, 0, 4, 0, 12),
        }
        self.assertEqual(tuple(expected_counts), source.DOMAINS)
        self.assertEqual(self.inventory_calls, list(source.DOMAINS))
        self.assertEqual(tuple(self.allocation.namespaces), source.DOMAINS)
        self.assertEqual(len(self.calls), 24)
        total = 0
        all_tokens = set()
        all_bindings = []
        for domain in source.DOMAINS:
            self.assertEqual(tuple(self.allocation.namespaces[domain]), source.KINDS)
            retained = self.allocation.role_lists[domain]
            self.assertEqual(tuple(retained), (*source.KINDS, "ALL"))
            self.assertEqual(tuple(item.count for item in retained.values()), expected_counts[domain])
            combined = []
            for kind in source.KINDS:
                namespace = self.allocation.namespaces[domain][kind]
                self.assertEqual(self.calls[len(all_bindings)], (domain, kind, total))
                total += len(namespace.serial_tokens)
                all_bindings.append(namespace.bindings)
                self.assertEqual(namespace.role_list_bytes, retained[kind].role_list_bytes)
                self.assertEqual(namespace.role_list_sha256, retained[kind].sha256)
                roles = namespace.role_list_bytes.splitlines()
                self.assertEqual(roles, sorted(roles))
                self.assertEqual(set(roles), {role.encode("ascii") for role, _ in namespace.bindings})
                self.assertEqual(set(namespace.serial_tokens), {token for _, token in namespace.bindings})
                self.assertEqual(len(set(namespace.serial_tokens)), len(namespace.serial_tokens))
                self.assertFalse(all_tokens.intersection(namespace.serial_tokens))
                self.assertFalse(any(token.endswith("_AAAAAAAAAAAA") for token in namespace.serial_tokens))
                all_tokens.update(namespace.serial_tokens)
                combined.extend(roles)
            self.assertEqual(retained["ALL"].role_list_bytes, b"\n".join(sorted(combined)))
            for kind, item in retained.items():
                self.assertFalse(item.role_list_bytes.endswith(b"\n"))
                self.assertEqual((item.count, item.sha256), wire.SYMBOLIC_COMMITMENTS[domain][kind])
                self.assertEqual(item.sha256, sha256(item.role_list_bytes).hexdigest())
        self.assertEqual(total, 302948)
        self.assertEqual(len(all_tokens), 302948)
        self.assertEqual(self.allocation.bindings, tuple(binding for group in all_bindings for binding in group))

    def test_world_mapping_is_complete_nested_immutable_and_has_full_keys(self):
        expected_worlds = {
            "birth_train": {f"p{index:02d}" for index in range(32)},
            "dose_intervention": {f"{transition}_k{index}" for transition in
                                  ("seek", "prospect", "check", "continue") for index in range(8)},
            "dose_chain": {f"h{index:02d}" for index in range(16)},
            "generic_canary": {f"c{index:02d}" for index in range(12)},
        }
        for domain, expected in expected_worlds.items():
            worlds = self.allocation.role_tokens_by_world(domain)
            self.assertIs(type(worlds), MappingProxyType)
            self.assertEqual(tuple(worlds), tuple(sorted(expected)))
            merged = {}
            for world, tokens in worlds.items():
                self.assertIs(type(tokens), MappingProxyType)
                self.assertTrue(all(role.startswith(domain + "/" + world + "/") for role in tokens))
                merged.update(tokens)
                with self.assertRaises(TypeError):
                    tokens["extra"] = "token"
            self.assertEqual(merged, dict(self.allocation.role_tokens_by_domain[domain]))
            with self.assertRaises(TypeError):
                worlds["extra"] = {}
        with self.assertRaises(FrozenInstanceError):
            self.allocation.custody_sha256 = "forged"
        with self.assertRaises(TypeError):
            self.allocation.namespaces["birth_train"]["node"] = None
        with self.assertRaises(FrozenInstanceError):
            self.allocation.role_lists["birth_train"]["ALL"].count = 0
        with self.assertRaises(FrozenInstanceError):
            self.allocation.namespaces["birth_train"]["node"].bindings = ()
        for domain in (None, [], "confirmation_reserved", "writer_reserved", "null", "shadow"):
            with self.subTest(domain=domain), self.assertRaisesRegex(ValueError, "unbound_allocation_domain"):
                self.allocation.role_tokens_by_world(domain)

    def test_exact_hidden_custody_retains_pins_master_values_and_limitations(self):
        raw = self.allocation.custody_bytes
        document = json.loads(raw)
        self.assertEqual(raw, json.dumps(document, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True).encode("ascii"))
        self.assertEqual(sha256(raw).hexdigest(), self.allocation.custody_sha256)
        self.assertEqual(document["master"], {"bytes_hex": MASTER.hex(), "sha256": sha256(MASTER).hexdigest()})
        self.assertEqual(document["schema"], source.SCHEMA_VERSION)
        self.assertEqual(document["allocator_api"], source.ALLOCATOR_API)
        self.assertEqual(document["inventory_api"], source.INVENTORY_API)
        self.assertEqual(document["source_hashes"], dict(source.SOURCE_HASHES))
        self.assertEqual(document["contract_hashes"], dict(source.CONTRACT_HASHES))
        self.assertEqual(document["domain_order"], list(source.DOMAINS))
        self.assertEqual(document["kind_order"], list(source.KINDS))
        self.assertEqual(document["allocated_count"], 302948)
        for retained_domain in document["domains"]:
            domain = retained_domain["domain"]
            aggregate = self.allocation.role_lists[domain]["ALL"]
            self.assertEqual(retained_domain["all_roles"]["role_list_ascii"].encode("ascii"), aggregate.role_list_bytes)
            for record in retained_domain["namespaces"]:
                namespace = self.allocation.namespaces[domain][record["kind"]]
                self.assertEqual(record["roles"]["role_list_ascii"].encode("ascii"), namespace.role_list_bytes)
                self.assertEqual(record["roles"]["count"], len(namespace.bindings))
                self.assertEqual(record["roles"]["sha256"], namespace.role_list_sha256)
                self.assertEqual(record["serial_tokens"], list(namespace.serial_tokens))
                self.assertEqual(record["bindings"], [list(binding) for binding in namespace.bindings])
                self.assertEqual(record["serial_tokens_sha256"], sha256(
                    "\n".join(namespace.serial_tokens).encode("ascii")).hexdigest())
                self.assertEqual(record["bindings_sha256"], sha256(json.dumps(
                    record["bindings"], separators=(",", ":")).encode("ascii")).hexdigest())
        self.assertEqual([record["domain"] for record in document["unallocated_reserved"]],
                         ["confirmation_reserved", "writer_reserved"])
        self.assertTrue(all(record["serials_per_kind"] == 4096 for record in document["unallocated_reserved"]))
        self.assertIn("null/shadow", " ".join(document["limitations"]))
        self.assertIn("c12..c15", " ".join(document["limitations"]))
        self.assertNotIn("native_admission", document)
        self.assertNotIn(MASTER.hex(), repr(self.allocation))

    def test_bound_source_and_contract_snapshot_hashes(self):
        root = Path(__file__).resolve().parents[1]
        for path, digest in source.SOURCE_HASHES.items():
            self.assertEqual(sha256((root / path).read_bytes()).hexdigest(), digest)
        for version, digest in source.CONTRACT_HASHES.items():
            filename = (f"2026-09-13_m_combine4_stage2a_binding_successor_{version}.md"
                        if version != "v6" else "2026-09-14_stage2a_binding_successor_v6_typed_boundary.md")
            self.assertEqual(sha256((root / "research_notes/analysis" / filename).read_bytes()).hexdigest(), digest)

    def test_full_verification_reenumerates_and_reallocates_every_namespace(self):
        calls = []
        allocator = wire.allocate_opaque_namespace

        def allocate(**inputs):
            calls.append((inputs["domain"], inputs["kind"]))
            return allocator(**inputs)

        with patch.object(wire, "allocate_opaque_namespace", side_effect=allocate), \
                patch.object(wire, "enumerate_symbolic_role_inventory",
                             wraps=wire.enumerate_symbolic_role_inventory) as enumerator:
            self.assertTrue(source.verify_stage2a(self.allocation, master=MASTER))
        self.assertEqual(calls, [(domain, kind) for domain in source.DOMAINS for kind in source.KINDS])
        self.assertEqual([call.args[0] for call in enumerator.call_args_list], list(source.DOMAINS))

    def test_foreign_explicit_master_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact_allocation_mismatch"):
            source.verify_stage2a(self.allocation, master=MASTER + b"FOREIGN")

    def test_changed_middle_binding_rejected_even_when_custody_unchanged(self):
        changed = list(self.allocation.bindings)
        middle = len(changed) // 2
        changed[middle], changed[middle + 1] = changed[middle + 1], changed[middle]
        candidate = replace(self.allocation, bindings=tuple(changed))
        with self.assertRaisesRegex(ValueError, "exact_allocation_mismatch"):
            source.verify_stage2a(candidate, master=MASTER)

    def test_changed_middle_bytes_rejected_even_with_matching_supplied_hash(self):
        raw = self.allocation.custody_bytes
        middle = len(raw) // 2
        changed = raw[:middle] + (b"A" if raw[middle:middle + 1] != b"A" else b"B") + raw[middle + 1:]
        candidate = replace(self.allocation, custody_bytes=changed, custody_sha256=sha256(changed).hexdigest())
        self.assertEqual(candidate.custody_bytes[:100], raw[:100])
        self.assertEqual(candidate.custody_bytes[-100:], raw[-100:])
        with self.assertRaisesRegex(ValueError, "exact_allocation_mismatch"):
            source.verify_stage2a(candidate, master=MASTER)

    def test_custody_verifier_requires_exact_bytes_not_semantic_json_equality(self):
        self.assertTrue(source.verify_stage2a_custody(self.allocation.custody_bytes, master=MASTER))
        with self.assertRaisesRegex(ValueError, "exact_allocation_custody_mismatch"):
            source.verify_stage2a_custody(self.allocation.custody_bytes + b"\n", master=MASTER)

    def test_derived_world_map_tampering_is_rejected(self):
        domains = dict(self.allocation._worlds)
        worlds = dict(domains["birth_train"])
        worlds["p00"] = worlds["p01"]
        domains["birth_train"] = MappingProxyType(worlds)
        candidate = replace(self.allocation, _worlds=MappingProxyType(domains))
        with self.assertRaisesRegex(ValueError, "exact_allocation_mismatch"):
            source.verify_stage2a(candidate, master=MASTER)

    def test_exact_comparison_rejects_missing_extra_order_and_mutable_shapes(self):
        class ForeignString(str):
            pass

        self.assertFalse(source._exact(MappingProxyType({ForeignString("role"): "token"}),
                                       MappingProxyType({"role": "token"})))
        for candidate in (
            replace(self.allocation, namespaces=MappingProxyType({})),
            replace(self.allocation, namespaces=MappingProxyType({**self.allocation.namespaces, "extra": {}})),
            replace(self.allocation, namespaces=MappingProxyType(dict(reversed(tuple(self.allocation.namespaces.items()))))),
            replace(self.allocation, namespaces=dict(self.allocation.namespaces)),
            replace(self.allocation, bindings=list(self.allocation.bindings)),
            replace(self.allocation, custody_bytes=bytearray(self.allocation.custody_bytes)),
        ):
            self.assertFalse(source._exact(candidate, self.allocation))

    def test_existing_primitive_exact_known_vector(self):
        namespace = wire.allocate_opaque_namespace(
            master=b"SYNTHETIC-ALLOCATION-UNIT-ONLY", domain="synthetic_fixture", kind="query",
            role_keys=("synthetic_fixture/dummy_b/s/01/useful/-/query",
                       "synthetic_fixture/dummy_a/s/00/useful/-/query",
                       "synthetic_fixture/dummy_c/s/02/useful/-/query"),
            expected_count=3,
            expected_role_list_sha256="b88e5cbcae14a44608ab1ded23e42fd250994b2067455905119d00d6e7efea74",
            occupied_tokens=(),
        )
        self.assertEqual(namespace.serial_tokens,
                         ("M2AQ_SUYNDRKOHVIY", "M2AQ_GOXIYUE7CW7Z", "M2AQ_PT7CQAH7P2D6"))
        self.assertEqual(namespace.bindings, (
            ("synthetic_fixture/dummy_a/s/00/useful/-/query", "M2AQ_PT7CQAH7P2D6"),
            ("synthetic_fixture/dummy_b/s/01/useful/-/query", "M2AQ_SUYNDRKOHVIY"),
            ("synthetic_fixture/dummy_c/s/02/useful/-/query", "M2AQ_GOXIYUE7CW7Z"),
        ))

    def test_actual_cross_domain_collision_fails_without_retry(self):
        allocator = wire.allocate_opaque_namespace
        first = self.allocation.namespaces["birth_train"]["node"].serial_tokens[0]
        calls = []

        def collide(**inputs):
            calls.append((inputs["domain"], inputs["kind"]))
            if inputs["domain"] == "dose_intervention":
                self.assertIn(first, inputs["occupied_tokens"])
                with patch.object(wire.base64, "b32encode", return_value=first[5:].encode("ascii")):
                    return allocator(**inputs)
            return allocator(**inputs)

        with patch.object(wire, "allocate_opaque_namespace", side_effect=collide):
            with self.assertRaisesRegex(ValueError, "allocation_token_collision"):
                source.allocate_stage2a(master=MASTER)
        self.assertEqual(calls, [("birth_train", kind) for kind in source.KINDS] + [("dose_intervention", "node")])

    def test_reserved_token_fails_without_retry(self):
        with patch.object(wire.base64, "b32encode", return_value=b"AAAAAAAAAAAA") as encode:
            with self.assertRaisesRegex(ValueError, "reserved_allocation_token"):
                source.allocate_stage2a(master=MASTER)
        self.assertEqual(encode.call_count, 1)

    def test_changed_middle_inventory_fails_before_allocation(self):
        inventory = wire.enumerate_symbolic_role_inventory("birth_train")
        roles = dict(inventory.roles_by_kind)
        queries = list(roles["query"])
        middle = len(queries) // 2
        queries[middle] = queries[middle].replace("/s/", "/changed/") + "_changed"
        roles["query"] = tuple(queries)
        forged = replace(inventory, roles_by_kind=MappingProxyType(roles))
        with patch.object(wire, "enumerate_symbolic_role_inventory", return_value=forged) as enumerate_roles, \
                patch.object(wire, "allocate_opaque_namespace") as allocate:
            with self.assertRaises(ValueError):
                source.allocate_stage2a(master=MASTER)
        self.assertEqual(enumerate_roles.call_count, 1)
        allocate.assert_not_called()

    def test_explicit_master_and_input_types_fail_closed(self):
        self.assertIs(inspect.signature(source.allocate_stage2a).parameters["master"].default,
                      inspect.Parameter.empty)
        with self.assertRaises(TypeError):
            source.allocate_stage2a()
        with self.assertRaises(TypeError):
            source.allocate_stage2a(MASTER)
        for master in (None, "master", bytearray(MASTER), memoryview(MASTER), True):
            with self.subTest(master=type(master)), self.assertRaisesRegex(ValueError, "allocation_master_requires_bytes"):
                source.allocate_stage2a(master=master)
        with self.assertRaises(TypeError):
            source.verify_stage2a(self.allocation)
        with self.assertRaisesRegex(ValueError, "stage2a_allocation_required"):
            source.verify_stage2a({}, master=MASTER)
        with self.assertRaisesRegex(ValueError, "allocation_custody_requires_bytes"):
            source.verify_stage2a_custody(bytearray(), master=MASTER)


if __name__ == "__main__":
    unittest.main()
