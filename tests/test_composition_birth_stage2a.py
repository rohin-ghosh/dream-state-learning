"""In-memory candidate regressions; no materialization or scientific evidence."""

from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from organism_v6 import composition_birth_stage2a as source


NODE = "M2AN_BBBBBBBBBBBB"
GOAL = "M2AN_CCCCCCCCCCCC"
HUB = "M2AN_DDDDDDDDDDDD"
QUERY = "M2AQ_BBBBBBBBBBBB"
EVENT = "M2AE_BBBBBBBBBBBB"
PORT = "M2AP_BBBBBBBBBBBB"
RECEIPT = "M2AR_BBBBBBBBBBBB"
ROUTE = "M2AI_BBBBBBBBBBBB"
TASK = f"TASK\nSTART {NODE}\nGOAL {GOAL}\nCURRENT {NODE}"


def block(kind, skin=0):
    if kind == "ROUTES":
        row = (f"ROUTE {ROUTE} AT {NODE} FOR {GOAL} QUERY {QUERY}" if skin == 0
               else f"ROUTE {ROUTE} FOR {GOAL} QUERY {QUERY} AT {NODE}")
        return "ROUTES\n" + "\n".join([row] * 24)
    row = (f"EVENT {EVENT} AT {NODE} FOR {GOAL} DID {PORT} GOT {GOAL} RECOVER {QUERY} EVIDENCE {RECEIPT}"
           if skin == 0 else
           f"EVENT {EVENT} FOR {GOAL} AT {NODE} GOT {GOAL} DID {PORT} RECOVER {QUERY} EVIDENCE {RECEIPT}")
    return "EVENTS\n" + "\n".join([row] * 4)


def session():
    service = source.PassiveRegistry({f"READ RELATION {QUERY}": block("EVENTS")}, skin=0)
    return source.Session(TASK, {(NODE, PORT): HUB, (HUB, PORT): GOAL}, service)


def turn(current_session, raw, **overrides):
    values = dict(generation_request={"max_new_tokens": min(256, 4096 - current_session.state.actual_tokens)},
                  declared_tokens=1, actual_tokens=1, context_tokens=0,
                  truncated=False, finish_reason="stop")
    values.update(overrides)
    return current_session.turn(raw, **values)


class SymbolicInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(source, "allocate_opaque_namespace", side_effect=AssertionError("allocation forbidden")), \
                patch.object(source, "allocation_u32", side_effect=AssertionError("serials forbidden")), \
                patch.object(source.base64, "b32encode", side_effect=AssertionError("tokens forbidden")), \
                patch.object(source, "PassiveRegistry", side_effect=AssertionError("store forbidden")), \
                patch.object(source, "Session", side_effect=AssertionError("session forbidden")):
            cls.inventories = {domain: source.enumerate_symbolic_role_inventory(domain) for domain in
                               ("birth_train", "dose_intervention", "dose_chain", "generic_canary")}

    def test_exact_memo_commitments_and_independent_counts_hashes(self):
        memo = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v3.md"
        raw = memo.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), source.SYMBOLIC_MEMO_SHA256)
        expected = {}
        for line in raw.decode("utf-8").splitlines():
            if line.startswith("| "):
                cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
                if len(cells) == 4 and cells[0] in self.inventories:
                    expected[cells[0], cells[1]] = (int(cells[2].replace(",", "")), cells[3])
        self.assertEqual(len(expected), 28)
        literal_counts = {
            "birth_train": (2080, 61512, 49216, 12288, 49216, 49216, 223528),
            "dose_intervention": (2080, 3840, 3072, 768, 3072, 3072, 15904),
            "dose_chain": (1040, 17344, 13888, 3456, 13888, 13888, 63504),
            "generic_canary": (2, 2, 4, 0, 4, 0, 12),
        }
        for domain, inventory in self.inventories.items():
            self.assertEqual(tuple(inventory.counts.values()), literal_counts[domain])
            combined = []
            for kind, roles in inventory.roles_by_kind.items():
                derived = (len(roles), sha256(b"\n".join(role.encode("ascii") for role in roles)).hexdigest())
                self.assertEqual(derived, expected[domain, kind])
                self.assertEqual(derived, source.SYMBOLIC_COMMITMENTS[domain][kind])
                self.assertEqual(derived, (inventory.counts[kind], inventory.hashes[kind]))
                combined.extend(roles)
            derived_all = (len(combined), sha256("\n".join(sorted(combined)).encode("ascii")).hexdigest())
            self.assertEqual(derived_all, expected[domain, "ALL"])
            self.assertEqual(derived_all, (inventory.counts["ALL"], inventory.hashes["ALL"]))

    def test_ordered_seven_component_unique_domain_separated_strings_only(self):
        observed = set()
        for domain, inventory in self.inventories.items():
            self.assertEqual(inventory.status, "SYMBOLIC_SOURCE_ONLY")
            self.assertEqual(inventory.memo_sha256, source.SYMBOLIC_MEMO_SHA256)
            self.assertEqual(inventory.domain, domain)
            self.assertEqual(tuple(inventory.roles_by_kind), ("node", "query", "event", "route", "port", "receipt"))
            for kind, roles in inventory.roles_by_kind.items():
                self.assertIsInstance(roles, tuple)
                self.assertEqual(roles, tuple(sorted(roles)))
                self.assertEqual(len(roles), len(set(roles)))
                self.assertTrue(observed.isdisjoint(roles))
                observed.update(roles)
                for role in roles:
                    parts = role.split("/")
                    self.assertEqual(len(parts), 7)
                    self.assertEqual(parts[0], domain)
                    self.assertEqual(parts[-1], kind)
                    self.assertTrue(role.isascii())
                    self.assertNotIn("M2A", role)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_birth_family_and_member_specific_roles_only_where_created(self):
        roles = self.inventories["birth_train"].roles_by_kind
        nodes = set(roles["node"])
        queries = set(roles["query"])
        for role in ("p00/a23/23/state/-/node", "p03/b05/05/state/-/node",
                     "p01/pred_m0/00/mismatch/-/node", "p01/surp_m1/12/mismatch/-/node",
                     "p25/pred_m1/06/mismatch/-/node", "p29/surp_m0/13/mismatch/-/node"):
            self.assertIn("birth_train/" + role, nodes)
        for role in ("p00/b00/00/state/-/node", "p03/a00/00/state/-/node",
                     "p03/b06/06/state/-/node", "p00/pred_m0/00/mismatch/-/node"):
            self.assertNotIn("birth_train/" + role, nodes)
        for role in ("p09/s/10/miss_m0/-/query", "p09/s/14/miss_m1/-/query",
                     "p19/s/08/miss_m0/-/query", "p19/s/08/miss_m1/-/query",
                     "p23/s/23/miss_m1/-/query", "p25/surp_m1/06/recover2_m1/3/query"):
            self.assertIn("birth_train/" + role, queries)
        self.assertIn("birth_train/p00/a23/23/index/-/route", roles["route"])
        self.assertIn("birth_train/p25/surp_m1/06/recovery_m1/3/event", roles["event"])
        miss_pairs = {role.split("/")[1] for role in queries if role.split("/")[4].startswith("miss_")}
        mismatch_pairs = {role.split("/")[1] for role in nodes if role.split("/")[4] == "mismatch"}
        self.assertEqual(miss_pairs, {"p09", "p13", "p19", "p23"})
        self.assertEqual(mismatch_pairs, {"p01", "p03", "p05", "p07", "p25", "p27", "p29", "p31"})

    def test_intervention_worlds_have_start_queries_and_no_corrective_roles(self):
        roles = self.inventories["dose_intervention"].roles_by_kind
        worlds = {role.split("/")[1] for role in roles["node"]}
        expected = {f"{transition}_k{index}" for transition in ("seek", "prospect", "check", "continue")
                    for index in range(8)}
        self.assertEqual(worlds, expected)
        self.assertIn("dose_intervention/check_k7/w07/07/state/-/node", roles["node"])
        self.assertIn("dose_intervention/continue_k7/s/23/recover/3/query", roles["query"])
        for kind in ("query", "route", "event", "port", "receipt"):
            for role in roles[kind]:
                self.assertEqual(role.split("/")[2], "s")
                self.assertIn(role.split("/")[4], ("index", "useful", "recover"))

    def test_chain_recovery_uses_scored_goal_and_member_specific_surprise_hub(self):
        roles = self.inventories["dose_chain"].roles_by_kind
        self.assertIn("dose_chain/h04/w05/08/recovery_m0/3/event", roles["event"])
        self.assertIn("dose_chain/h04/w05/16/recovery_m1/3/event", roles["event"])
        self.assertIn("dose_chain/h12/w01/12/recover2_m1/0/query", roles["query"])
        self.assertIn("dose_chain/h00/h07/23/useful/3/event", roles["event"])
        for kind in ("query", "event", "port", "receipt"):
            corrective = [role.split("/") for role in roles[kind]
                          if role.split("/")[4].startswith(("recovery_", "recover2_"))]
            self.assertEqual(len(corrective), 64)
            self.assertEqual({parts[1] for parts in corrective},
                             {"h04", "h05", "h06", "h07", "h12", "h13", "h14", "h15"})
            self.assertTrue(all(parts[2].startswith("w") for parts in corrective))
        self.assertFalse(any(role.split("/")[2].startswith("w") for role in roles["route"]))

    def test_canary_identifier_absences_and_read_only_results(self):
        inventory = self.inventories["generic_canary"]
        self.assertEqual(inventory.roles_by_kind["route"], ())
        self.assertEqual(inventory.roles_by_kind["receipt"], ())
        worlds = {role.split("/")[1] for entries in inventory.roles_by_kind.values() for role in entries}
        self.assertEqual(worlds, {f"c{index:02d}" for index in range(12)})
        self.assertEqual(inventory.roles_by_kind["node"], (
            "generic_canary/c00/canary/-/target/-/node", "generic_canary/c01/canary/-/target/-/node"))
        with self.assertRaises(TypeError):
            inventory.roles_by_kind["node"] = ()
        with self.assertRaises(FrozenInstanceError):
            inventory.status = "GO"
        mutable = {kind: list(reversed(entries)) for kind, entries in inventory.roles_by_kind.items()}
        checked = source.validate_symbolic_role_inventory("generic_canary", mutable)
        mutable["node"].clear()
        self.assertEqual(checked, inventory)
        self.assertEqual(source.enumerate_symbolic_role_inventory("generic_canary"), inventory)

    def test_duplicate_missing_extra_cross_domain_and_rebound_roles_rejected(self):
        inventory = self.inventories["generic_canary"]
        nodes = inventory.roles_by_kind["node"]
        changes = (
            (nodes[0], nodes[0]), nodes[:-1],
            nodes + ("generic_canary/c12/canary/-/target/-/node",),
            (nodes[0].replace("generic_canary", "dose_chain"), nodes[1]),
            (nodes[0].replace("/target/", "/state/"), nodes[1]),
            (nodes[0] + "\n", nodes[1]),
        )
        for changed in changes:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                source.validate_symbolic_role_inventory("generic_canary", dict(inventory.roles_by_kind, node=changed))
        for kind_change in ("missing", "extra"):
            changed = dict(inventory.roles_by_kind)
            if kind_change == "missing":
                del changed["node"]
            else:
                changed["unknown"] = ()
            with self.assertRaisesRegex(ValueError, "symbolic_kind_inventory_mismatch"):
                source.validate_symbolic_role_inventory("generic_canary", changed)
        with self.assertRaisesRegex(ValueError, "duplicate_symbolic_role"):
            source.validate_symbolic_role_inventory("generic_canary", dict(inventory.roles_by_kind, node=(nodes[0], nodes[0])))

    def test_unbound_reserved_and_unspecified_domains_fail_without_expansion(self):
        for domain in ("confirmation_reserved", "writer_reserved", "birth_confirmation", "unknown", None, []):
            with self.subTest(domain=domain), self.assertRaisesRegex(ValueError, "unbound_symbolic_domain"):
                source.enumerate_symbolic_role_inventory(domain)
        with self.assertRaises(TypeError):
            source.enumerate_symbolic_role_inventory()


class NamespaceAllocationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {
            "master": b"SYNTHETIC-ALLOCATION-UNIT-ONLY",
            "domain": "synthetic_fixture",
            "kind": "query",
            "role_keys": (
                "synthetic_fixture/dummy_b/s/01/useful/-/query",
                "synthetic_fixture/dummy_a/s/00/useful/-/query",
                "synthetic_fixture/dummy_c/s/02/useful/-/query",
            ),
            "expected_count": 3,
            "expected_role_list_sha256": "b88e5cbcae14a44608ab1ded23e42fd250994b2067455905119d00d6e7efea74",
            "occupied_tokens": (),
        }

    def test_exact_v3_binding_no_science_gate_or_implicit_inputs(self):
        memo = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v3.md"
        self.assertEqual(sha256(memo.read_bytes()).hexdigest(), source.ALLOCATION_MEMO_SHA256)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        for field in self.inputs:
            inputs = dict(self.inputs)
            del inputs[field]
            with self.subTest(field=field), self.assertRaises(TypeError):
                source.allocate_opaque_namespace(**inputs)
        source.allocate_opaque_namespace(**self.inputs)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_u32_unsigned_big_endian_boundaries(self):
        for value, expected in ((0, b"\x00\x00\x00\x00"), (1, b"\x00\x00\x00\x01"),
                                (256, b"\x00\x00\x01\x00"), (2**32-1, b"\xff\xff\xff\xff")):
            self.assertEqual(source.allocation_u32(value), expected)
        for value in (-1, 2**32, True, False, 1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.allocation_u32(value)

    def test_synthetic_golden_vector_canonical_order_and_immutable_result(self):
        result = source.allocate_opaque_namespace(**self.inputs)
        self.assertEqual(result.role_list_bytes, b"\n".join(
            role.encode("ascii") for role in sorted(self.inputs["role_keys"])))
        self.assertFalse(result.role_list_bytes.endswith(b"\n"))
        self.assertEqual(result.role_list_sha256, self.inputs["expected_role_list_sha256"])
        self.assertEqual(result.serial_tokens,
                         ("M2AQ_SUYNDRKOHVIY", "M2AQ_GOXIYUE7CW7Z", "M2AQ_PT7CQAH7P2D6"))
        self.assertEqual(result.bindings, (
            ("synthetic_fixture/dummy_a/s/00/useful/-/query", "M2AQ_PT7CQAH7P2D6"),
            ("synthetic_fixture/dummy_b/s/01/useful/-/query", "M2AQ_SUYNDRKOHVIY"),
            ("synthetic_fixture/dummy_c/s/02/useful/-/query", "M2AQ_GOXIYUE7CW7Z"),
        ))
        reordered = dict(self.inputs, role_keys=list(reversed(self.inputs["role_keys"])))
        self.assertEqual(source.allocate_opaque_namespace(**reordered), result)
        reordered["role_keys"].clear()
        self.assertEqual(len(result.bindings), 3)
        with self.assertRaises(FrozenInstanceError):
            result.bindings = ()

    def test_explicit_empty_role_list_allocates_nothing(self):
        inputs = dict(self.inputs, role_keys=(), expected_count=0,
                      expected_role_list_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        result = source.allocate_opaque_namespace(**inputs)
        self.assertEqual(result.role_list_bytes, b"")
        self.assertEqual(result.serial_tokens, ())
        self.assertEqual(result.bindings, ())

    def test_all_six_prefixes_use_only_explicit_synthetic_roles(self):
        for kind, prefix in (("node", "M2AN_"), ("query", "M2AQ_"), ("event", "M2AE_"),
                             ("route", "M2AI_"), ("port", "M2AP_"), ("receipt", "M2AR_")):
            role = f"synthetic_fixture/dummy_a/s/-/state/-/{kind}"
            inputs = dict(self.inputs, kind=kind, role_keys=(role,), expected_count=1,
                          expected_role_list_sha256=sha256(role.encode()).hexdigest())
            result = source.allocate_opaque_namespace(**inputs)
            self.assertRegex(result.serial_tokens[0], "^" + prefix + "[A-Z2-7]{12}$")

    def test_missing_extra_duplicate_roles_and_commitment_drift_fail(self):
        roles = self.inputs["role_keys"]
        cases = (
            {"role_keys": roles[:-1]},
            {"role_keys": roles + ("synthetic_fixture/dummy_d/s/03/useful/-/query",)},
            {"role_keys": (roles[0], roles[0], roles[2])},
            {"expected_count": 2}, {"expected_count": True},
            {"expected_count": -1}, {"expected_count": 2**32+1},
            {"expected_role_list_sha256": "0" * 64},
            {"expected_role_list_sha256": self.inputs["expected_role_list_sha256"].upper()},
        )
        for override in cases:
            with self.subTest(override=override), self.assertRaises(ValueError):
                source.allocate_opaque_namespace(**dict(self.inputs, **override))

    def test_role_syntax_and_delimiters_fail_without_repair(self):
        original = self.inputs["role_keys"][0]
        invalid = (original + "\n", original + "/extra", original.replace("/01/", "/24/"),
                   original.replace("/01/", "/1/"), original.replace("/-/query", "/4/query"),
                   original.replace("/s/", "//"), original.replace("dummy_b", "dummy\x00b"),
                   original.replace("dummy_b", "dummy\rb"), original.replace("dummy_b", "dümmý"),
                   original.replace("dummy_b", "\ud800"), original.replace("query", "event"),
                   original.replace("synthetic_fixture", "synthetic_other"), b"not-a-role")
        for role in invalid:
            with self.subTest(role=role), self.assertRaises(ValueError):
                source.allocate_opaque_namespace(**dict(self.inputs, role_keys=(role,)))
        for override in ({"master": "not-bytes"}, {"domain": "bad/domain"},
                         {"kind": "unknown"}, {"role_keys": set()},
                         {"occupied_tokens": None}, {"occupied_tokens": ("bad",)},
                         {"occupied_tokens": ("M2AQ_AAAAAAAAAAAA",)}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                source.allocate_opaque_namespace(**dict(self.inputs, **override))

    def test_candidate_collision_and_all_a_fail_without_retry(self):
        candidate_prefix = self.inputs["master"] + b"\x00synthetic_fixture\x00query\x00"
        for digest, expected_reason, expected_calls in ((b"\x00" * 32, "reserved_allocation_token", 1),
                                                       (b"\x01" * 32, "allocation_token_collision", 2)):
            calls = []
            def controlled_hash(raw):
                if raw.startswith(candidate_prefix):
                    calls.append(raw)
                    return Mock(digest=lambda: digest)
                return sha256(raw)
            with patch.object(source, "sha256", side_effect=controlled_hash):
                with self.assertRaisesRegex(ValueError, expected_reason):
                    source.allocate_opaque_namespace(**self.inputs)
            self.assertEqual(len(calls), expected_calls)
            self.assertEqual(calls, [candidate_prefix + serial.to_bytes(4, "big")
                                     for serial in range(expected_calls)])

    def test_cross_domain_collision_with_explicit_prior_tokens_fails(self):
        previous = source.allocate_opaque_namespace(**self.inputs)
        new_domain = "synthetic_other"
        roles = tuple(role.replace("synthetic_fixture", new_domain) for role in self.inputs["role_keys"])
        inputs = dict(self.inputs, domain=new_domain, role_keys=roles,
                      expected_role_list_sha256=sha256("\n".join(sorted(roles)).encode()).hexdigest(),
                      occupied_tokens=previous.serial_tokens)
        first_digest = sha256(self.inputs["master"] + b"\x00synthetic_fixture\x00query\x00\x00\x00\x00\x00").digest()
        candidate_prefix = self.inputs["master"] + b"\x00synthetic_other\x00query\x00"
        def controlled_hash(raw):
            if raw.startswith(candidate_prefix):
                return Mock(digest=lambda: first_digest)
            return sha256(raw)
        with patch.object(source, "sha256", side_effect=controlled_hash):
            with self.assertRaisesRegex(ValueError, "allocation_token_collision"):
                source.allocate_opaque_namespace(**inputs)
        self.assertEqual(len(previous.serial_tokens), 3)

    def test_digest_ties_use_raw_byte_tiebreak_for_both_orders(self):
        original = source.allocate_opaque_namespace(**self.inputs)
        def controlled_hash(raw):
            if b"\x00pool-order\x00" in raw or b"\x00role-order\x00" in raw:
                return Mock(digest=lambda: b"\xff" * 32)
            return sha256(raw)
        with patch.object(source, "sha256", side_effect=controlled_hash):
            tied = source.allocate_opaque_namespace(**self.inputs)
        self.assertEqual(tied.serial_tokens, original.serial_tokens)
        self.assertEqual(tied.bindings, tuple(zip(sorted(self.inputs["role_keys"]),
                                                 sorted(original.serial_tokens))))


class WireTests(unittest.TestCase):
    def test_bound_memo_and_system_bytes_no_science_gates(self):
        memo = Path(__file__).resolve().parents[1] / "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v2.md"
        raw = memo.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), source.MEMO_SHA256)
        section = raw.decode().split("### 2.2 System message, exact bytes\n", 1)[1]
        expected = section.split("```text\n", 1)[1].split("\n```", 1)[0]
        self.assertEqual(source.SYSTEM_MESSAGE, expected)
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertTrue(source.SCIENCE_GATES)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_exact_actions_including_syntactically_valid_sentinels(self):
        for raw in (f"THINK KEEP {EVENT}", f"THINK REVISE {EVENT}", f"THINK REVISE {QUERY}",
                    f"READ INDEX {NODE}", f"READ RELATION {QUERY}", f"STEP {PORT}", "STOP",
                    "THINK KEEP M2AE_AAAAAAAAAAAA", "READ RELATION M2AQ_AAAAAAAAAAAA"):
            with self.subTest(raw=raw):
                self.assertEqual(source.parse_action(raw).operation, raw.split()[0])

    def test_no_trimming_repair_unicode_fences_or_multiple_actions(self):
        bad = ("STOP\n", "STOP\r", " STOP", "STOP ", "STOP\nSTOP", "```STOP```", "ＳＴＯＰ",
               "STOP\x00", "THINK inspect", f"THINK KEEP {QUERY}", f"READ EVENT {EVENT}",
               f"STEP {NODE}", f"READ  INDEX {NODE}", "", "\ud800", b"STOP", None)
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                source.parse_action(raw)

    def test_task_and_world_envelopes(self):
        self.assertEqual(source.parse_task(TASK).current, NODE)
        self.assertEqual(source.parse_world(f"WORLD\nCURRENT {GOAL}"), GOAL)
        for raw in (TASK + "\n", TASK.replace("TASK", "TASK "), TASK.replace(NODE, "M2AN_AAAAAAAAAAAA")):
            with self.assertRaises(ValueError):
                source.parse_task(raw)
        for raw in (f"CURRENT {GOAL}", f"WORLD\nCURRENT {GOAL}\n", f"WORLD\nCURRENT {PORT}"):
            with self.assertRaises(ValueError):
                source.parse_world(raw)

    def test_both_service_skins_exact_counts_order_and_bytes(self):
        for skin in (0, 1):
            for kind, count in (("ROUTES", 24), ("EVENTS", 4)):
                raw = block(kind, skin)
                parsed = source.parse_service(raw, skin=skin)
                self.assertEqual(parsed.raw, raw)
                self.assertEqual(len(parsed.rows), count)
                self.assertEqual(parsed.rows[0].goal, GOAL)
                for bad in (raw + "\n", raw + " ", raw.replace("\n", "\r\n"),
                            "\n".join(raw.split("\n")[:-1]), raw + "\n" + raw.split("\n")[1],
                            raw.replace(NODE, "M2AN_AAAAAAAAAAAA"), raw.replace(" AT ", "  AT ")):
                    with self.subTest(kind=kind, skin=skin, bad=bad), self.assertRaises(ValueError):
                        source.parse_service(bad, skin=skin)
                with self.assertRaises(ValueError):
                    source.parse_service(raw, skin=1-skin)
        for skin in (True, "0", -1, 2):
            with self.assertRaises(ValueError):
                source.parse_service("MISS", skin=skin)

    def test_registry_is_passive_snapshot_with_unknown_miss(self):
        entries = {f"READ INDEX {NODE}": block("ROUTES"), f"READ RELATION {QUERY}": block("EVENTS")}
        registry = source.PassiveRegistry(entries, skin=0)
        entries.clear()
        self.assertEqual(registry.read(f"READ INDEX {NODE}"), block("ROUTES"))
        self.assertEqual(registry.read(f"READ RELATION {QUERY}"), block("EVENTS"))
        self.assertEqual(registry.read(f"READ INDEX {HUB}"), "MISS")
        self.assertEqual(registry.read("READ RELATION M2AQ_AAAAAAAAAAAA"), "MISS")
        with self.assertRaises(TypeError):
            registry.read(f"READ INDEX {NODE}", goal=GOAL)
        for entries in ({"STOP": "MISS"}, {f"READ INDEX {NODE}": block("EVENTS")},
                        {"READ INDEX M2AN_AAAAAAAAAAAA": "MISS"}):
            with self.assertRaises(ValueError):
                source.PassiveRegistry(entries, skin=0)
        for bad in ("STOP", f"READ INDEX {NODE}\n"):
            with self.assertRaises(ValueError):
                registry.read(bad)

    def test_row_order_is_not_repaired_and_mixed_skins_fail(self):
        for skin in (0, 1):
            raw = block("EVENTS", skin)
            lines = raw.split("\n")
            lines[2] = lines[2].replace(EVENT, "M2AE_CCCCCCCCCCCC")
            lines[3] = lines[3].replace(EVENT, "M2AE_DDDDDDDDDDDD")
            varied = "\n".join(lines)
            registry = source.PassiveRegistry({f"READ RELATION {QUERY}": varied}, skin=skin)
            self.assertEqual(registry.read(f"READ RELATION {QUERY}"), varied)
            self.assertEqual([row.event for row in source.parse_service(varied, skin=skin).rows],
                             [EVENT, "M2AE_CCCCCCCCCCCC", "M2AE_DDDDDDDDDDDD", EVENT])
            lines[2] = block("EVENTS", 1-skin).split("\n")[1]
            with self.assertRaises(ValueError):
                source.parse_service("\n".join(lines), skin=skin)


class SessionTests(unittest.TestCase):
    def test_world_not_event_prediction_is_authoritative_exact_stop_required(self):
        current = session()
        read = turn(current, f"READ RELATION {QUERY}")
        self.assertEqual(read.response_bytes, ("SERVICE\n" + block("EVENTS")).encode())
        moved = turn(current, f"STEP {PORT}")
        self.assertEqual(moved.response_bytes, f"WORLD\nCURRENT {HUB}".encode())
        self.assertFalse(current.state.goal_arrival_stop)
        check = turn(current, f"THINK REVISE {EVENT}")
        self.assertEqual(check.response_bytes, b"ACK")
        turn(current, f"STEP {PORT}")
        self.assertFalse(current.state.terminated)
        self.assertFalse(current.state.goal_arrival_stop)
        stopped = turn(current, "STOP")
        self.assertTrue(stopped.accepted)
        self.assertTrue(current.state.goal_arrival_stop)
        self.assertEqual(stopped.response_bytes, b"")
        self.assertEqual(len(current.receipts), 3)
        before = current.state
        rejected = turn(current, "STOP")
        self.assertEqual(rejected.terminal_reason, "session_terminated")
        self.assertFalse(rejected.accepted)
        self.assertEqual(current.state, before)
        self.assertEqual(len(current.attempts), 6)

    def test_miss_is_valid_and_no_host_correction_of_think(self):
        current = session()
        self.assertEqual(turn(current, f"READ INDEX {HUB}").response_bytes, b"SERVICE\nMISS")
        self.assertEqual(turn(current, "THINK KEEP M2AE_AAAAAAAAAAAA").response_bytes, b"ACK")
        self.assertFalse(current.state.terminated)
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_premature_stop_and_invalid_step_fail_without_repair(self):
        current = session()
        stopped = turn(current, "STOP")
        self.assertEqual(stopped.terminal_reason, "premature_stop")
        self.assertFalse(current.state.goal_arrival_stop)
        for raw in ("STEP M2AP_AAAAAAAAAAAA", "STOP\n", "READ HIDDEN whatever"):
            current = session()
            failed = turn(current, raw)
            self.assertFalse(failed.accepted)
            self.assertEqual(failed.response_bytes, b"")
            self.assertEqual(current.state.current, NODE)
            self.assertEqual(current.receipts, ())
            self.assertEqual(failed.capture.raw_bytes, raw.encode())

    def test_capture_precedes_parser_and_is_immutable(self):
        current = session()
        original = source.parse_action
        def inspect_capture(raw):
            self.assertEqual(len(current.raw_attempts), 1)
            self.assertEqual(current.raw_attempts[0].raw_bytes, b"STOP\n")
            self.assertEqual(current.attempts, ())
            return original(raw)
        with patch.object(source, "parse_action", side_effect=inspect_capture):
            failed = turn(current, "STOP\n")
        self.assertIs(failed.capture, current.raw_attempts[0])
        self.assertEqual(failed.parser_disposition, "invalid")
        with self.assertRaises(FrozenInstanceError):
            failed.accepted = True
        with self.assertRaises(FrozenInstanceError):
            failed.capture.call_index = 42

    def test_nonstring_and_invalid_unicode_custody_without_stringification(self):
        raw_values = (None, 17, True, 1.5, b"\xffSTOP", bytearray(b"STOP"),
                      ["STOP", {"raw": b"\xff"}], {"action": "STOP"}, "\ud800", "STÖP")
        for raw in raw_values:
            with self.subTest(raw=raw):
                current = session()
                result = turn(current, raw)
                self.assertFalse(result.accepted)
                self.assertEqual(result.capture.raw, source._freeze(raw))
                self.assertEqual(result.terminal_reason, "malformed_action")
        self.assertEqual(turn(session(), "STÖP").capture.raw_bytes, "STÖP".encode("utf-8"))
        self.assertEqual(turn(session(), b"\xffSTOP").capture.raw_bytes, b"\xffSTOP")
        raw = {"action": ["STOP"]}
        request = {"max_new_tokens": 256, "metadata": ["original"]}
        result = turn(session(), raw, generation_request=request)
        saved = result.capture
        raw["action"].append("changed")
        request["metadata"].clear()
        self.assertNotEqual(saved.raw, source._freeze(raw))
        self.assertNotEqual(saved.generation_request, source._freeze(request))

    def test_unsupported_transport_fails_closed_without_repr_fallback(self):
        current = session()
        with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
            turn(current, object())
        self.assertTrue(current.state.terminated)
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
            turn(session(), cyclic)

    def test_unsupported_raw_or_metadata_preserves_terminal_success_and_failure(self):
        for success in (False, True):
            for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                          "context_tokens", "truncated", "finish_reason"):
                with self.subTest(success=success, field=field):
                    current = session()
                    turn(current, f"READ RELATION {QUERY}")
                    if success:
                        turn(current, f"STEP {PORT}")
                        turn(current, f"STEP {PORT}")
                    turn(current, "STOP")
                    before = current.state
                    history = (current.raw_attempts, current.attempts, current.receipts)
                    self.assertTrue(before.terminated)
                    self.assertEqual(before.goal_arrival_stop, success)
                    overrides = {"raw": "STOP", field: object()}
                    with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                        turn(current, **overrides)
                    self.assertIs(current.state, before)
                    self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_deep_builtin_raw_or_metadata_terminates_active_session(self):
        nested = "STOP"
        for _ in range(1200):
            nested = [nested]
        for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                      "context_tokens", "truncated", "finish_reason"):
            with self.subTest(field=field):
                current = session()
                turn(current, f"READ RELATION {QUERY}")
                turn(current, f"STEP {PORT}")
                before = current.state
                history = (current.raw_attempts, current.attempts, current.receipts)
                overrides = {"raw": "STOP", field: nested}
                with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                    turn(current, **overrides)
                self.assertEqual(current.state, source.Snapshot(
                    before.current, before.counts, before.actual_tokens,
                    True, "unsupported_custody_transport", False))
                self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_deep_builtin_raw_or_metadata_preserves_terminal_success_and_failure(self):
        nested = "STOP"
        for _ in range(1200):
            nested = [nested]
        for success in (False, True):
            for field in ("raw", "generation_request", "declared_tokens", "actual_tokens",
                          "context_tokens", "truncated", "finish_reason"):
                with self.subTest(success=success, field=field):
                    current = session()
                    turn(current, f"READ RELATION {QUERY}")
                    if success:
                        turn(current, f"STEP {PORT}")
                        turn(current, f"STEP {PORT}")
                    turn(current, "STOP")
                    before = current.state
                    history = (current.raw_attempts, current.attempts, current.receipts)
                    self.assertEqual(before.goal_arrival_stop, success)
                    overrides = {"raw": "STOP", field: nested}
                    with self.assertRaisesRegex(ValueError, "unsupported_custody_transport"):
                        turn(current, **overrides)
                    self.assertIs(current.state, before)
                    self.assertEqual((current.raw_attempts, current.attempts, current.receipts), history)

    def test_operation_budgets_and_separate_raw_receipts(self):
        cases = ((f"THINK KEEP {EVENT}", 8), (f"READ INDEX {HUB}", 12), (f"STEP {PORT}", 8))
        for raw, limit in cases:
            current = source.Session(TASK, {(NODE, PORT): NODE}, source.PassiveRegistry({}, skin=0))
            for _ in range(limit):
                self.assertTrue(turn(current, raw).accepted)
            failed = turn(current, raw)
            self.assertEqual(failed.terminal_reason, "over_budget")
            self.assertEqual(len(current.raw_attempts), limit + 1)
            self.assertEqual(len(current.attempts), limit + 1)
            self.assertFalse(failed.accepted)

    def test_aggregate_token_and_context_allowances(self):
        current = session()
        for _ in range(8):
            self.assertTrue(turn(current, f"THINK KEEP {EVENT}", declared_tokens=256, actual_tokens=256).accepted)
        for _ in range(8):
            self.assertTrue(turn(current, f"READ INDEX {NODE}", declared_tokens=256, actual_tokens=256).accepted)
        self.assertEqual(current.state.actual_tokens, 4096)
        self.assertEqual(turn(current, "STOP", declared_tokens=0, actual_tokens=0).terminal_reason, "zero_allowance")
        current = session()
        self.assertTrue(turn(current, f"READ INDEX {NODE}", context_tokens=16380,
                             generation_request={"max_new_tokens": 4}, declared_tokens=4, actual_tokens=4).accepted)
        self.assertEqual(turn(session(), "STOP", context_tokens=16384).terminal_reason, "zero_allowance")

    def test_twenty_nine_calls_include_stop_no_retry_after_terminal(self):
        task = TASK.replace(f"GOAL {GOAL}", f"GOAL {NODE}")
        current = source.Session(task, {(NODE, PORT): NODE}, source.PassiveRegistry({}, skin=0))
        for raw, limit in ((f"THINK KEEP {EVENT}", 8), (f"READ INDEX {NODE}", 12), (f"STEP {PORT}", 8)):
            for _ in range(limit):
                self.assertTrue(turn(current, raw).accepted)
        self.assertTrue(turn(current, "STOP").accepted)
        self.assertEqual(len(current.attempts), source.CALL_CAP)
        self.assertEqual(current.attempts[-1].capture.call_index, 28)
        self.assertFalse(turn(current, "STOP").accepted)

    def test_generation_metadata_fails_closed_with_custody(self):
        cases = (
            {"actual_tokens": True}, {"declared_tokens": 2}, {"actual_tokens": -1},
            {"actual_tokens": 257, "declared_tokens": 257}, {"context_tokens": -1},
            {"context_tokens": True}, {"truncated": "false"}, {"truncated": True},
            {"finish_reason": "length"}, {"finish_reason": None},
            {"finish_reason": "unknown"}, {"actual_tokens": 0, "declared_tokens": 0},
            {"generation_request": {"max_new_tokens": 255}},
            {"generation_request": {"max_new_tokens": True}},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                current = session()
                failed = turn(current, "STOP", **overrides)
                self.assertFalse(failed.accepted)
                self.assertEqual(len(current.raw_attempts), 1)
                self.assertEqual(current.receipts, ())
                self.assertEqual(failed.response_bytes, b"")
        self.assertEqual(turn(session(), "STOP", finish_reason="unknown").terminal_reason,
                         "unbound_finish_reason")

    def test_world_mapping_is_copied_and_reserved_allocations_rejected(self):
        transitions = {(NODE, PORT): GOAL}
        current = source.Session(TASK, transitions, source.PassiveRegistry({}, skin=0))
        transitions[NODE, PORT] = HUB
        self.assertEqual(turn(current, f"STEP {PORT}").post_state.current, GOAL)
        with self.assertRaises(ValueError):
            source.Session(TASK, {(NODE, "M2AP_AAAAAAAAAAAA"): GOAL}, source.PassiveRegistry({}, skin=0))


if __name__ == "__main__":
    unittest.main()
