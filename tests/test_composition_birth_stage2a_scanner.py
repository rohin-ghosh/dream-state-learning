import base64
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_scanner as source
from organism_v6.composition_birth_stage2a_primitives import canonical_json


NODE = b"M2AN_BBBBBBBBBBBB"
GOAL = b"M2AN_CCCCCCCCCCCC"
QUERY = b"M2AQ_DDDDDDDDDDDD"
EVENT = b"M2AE_EEEEEEEEEEEE"
PORT = b"M2AP_FFFFFFFFFFFF"
LATER_QUERY = b"M2AQ_GGGGGGGGGGGG"
LATER_PORT = b"M2AP_HHHHHHHHHHHH"
LATER_EVENT = b"M2AE_IIIIIIIIIIII"
LATER_NODE = b"M2AN_JJJJJJJJJJJJ"


def certificate_fixture():
    claims = []
    for system, labels in (("PCFL", source.FORBIDDEN_CORE_LABELS[:3]),
                           ("GOAL_BRAID", source.FORBIDDEN_CORE_LABELS[3:])):
        claims.append({
            "forbidden_core_language": [label.decode("ascii") for label in labels],
            "public_identifier_regexes": [f"{kind}_[A-Z2-7]{{10}}" for kind in "ELNPR"],
            "reserved_prefix": "M2A", "reserved_prefix_absent": True, "system": system,
        })
    return canonical_json({
        "claims": claims,
        "issuer": "M-COMBINE-4 external design authority",
        "schema": "MCOMBINE_NAMESPACE_CERTIFICATE_V1",
        "subject": "M-COMBINE-4/STAGE2A/V3/2026-09-13",
        "tiny_fixture": {
            "disposition": "SEPARATION_CONTROL_ONLY_NOT_TRAIN_NOT_DEV_NOT_MODEL_INPUT",
            "identifier_regexes": [f"{kind}_[A-Z2-7]{{10}}" for kind in "ENPR"],
            "path": "organism_v6/composition_birth_stage0.py",
            "sha256": "f69c85ac4ca0b6c07c246de484da7262490d89ed8a612ec58476c6343aa29699",
        },
    })


def public_field(prefix, value, kind, *, occurrence=0, owner=None, observed_at=1):
    start = -1
    for index in range(occurrence + 1):
        start = prefix.index(value, start + 1)
    origins = {"route_query": "service", "event_did": "service", "event_recover": "service",
               "event_got": "service",
               "selected_event": "service", "issued_query": "actor", "think_implicated": "actor",
               "task_start": "task", "task_goal": "task", "current": "host",
               "task_current": "task", "protocol": "system"}
    return source.PublicField(f"/synthetic/{kind}/{start}", start, start + len(value), kind,
                              origins[kind], observed_at, f"synthetic-trace:{observed_at}", owner)


def scan(prefix, *, target=b"STEP " + PORT, phase="PROSPECT", **kwargs):
    return source.scan_forward_targets(prefix, target=target, phase=phase, decision_index=10,
                                       semantic_bytes=kwargs.pop("semantic_bytes", b"{}"), **kwargs)


class LexicalTests(unittest.TestCase):
    def test_exact_normalization_retains_empty_lines_and_no_trim(self):
        raw = b"\n a\t \tb_C-<d> \n\n"
        literal, normalized, compact = source.normalize_lines(raw)
        self.assertEqual(literal, (b"", b" a\t \tb_C-<d> ", b"", b""))
        self.assertEqual(normalized, (b"", b" A B_C-<D> ", b"", b""))
        self.assertEqual(compact, (b"", b"ABCD", b"", b""))

    def test_reject_invalid_material_in_all_byte_entrypoints(self):
        for raw in (b"\xff", "not bytes", bytearray(b"x"), b"a\rb", b"a\0b", "é".encode()):
            for function in (source.normalize_lines, source.semantic_atoms):
                with self.subTest(raw=raw, function=function.__name__), self.assertRaises(ValueError):
                    function(raw)

    def test_cursor_lexer_identifier_markers_and_no_suffixes(self):
        for prefix, marker in ((b"N", b"ID_NODE"), (b"Q", b"ID_QUERY"), (b"E", b"ID_EVENT"),
                               (b"I", b"ID_ROUTE"), (b"P", b"ID_PORT"), (b"R", b"ID_RECEIPT")):
            self.assertEqual(source.semantic_atoms(b"AT M2A" + prefix + b"_BBBBBBBBBBBB"),
                             (b"AT", marker))
        self.assertEqual(source.semantic_atoms(b"AT " + NODE + b"suffix"), (b"AT", b"ID_NODE", b"SUFFIX"))

    def test_no_escape_decoding_or_camel_splitting(self):
        self.assertEqual(source.semantic_atoms(rb"aCamel \u0050CFL foo_bar-<baz>"),
                         (b"ACAMEL", b"U0050CFL", b"FOO", b"_", b"BAR", b"-", b"<", b"BAZ", b">"))
        self.assertNotIn(b"PCFL", source.semantic_atoms(rb"\u0050CFL"))

    def test_only_exact_shared_lines_are_skipped(self):
        self.assertEqual(source.semantic_atoms(wire.SYSTEM_MESSAGE.encode()), ())
        self.assertEqual(source.semantic_atoms(b"TASK\nACK\nCOPY EXACTLY\n"), ())
        self.assertEqual(source.semantic_atoms(b"task\n TASK"), (b"TASK", b"TASK"))
        self.assertEqual(source.semantic_atoms(b"M2AN_BBBBBBBBBBB"), (b"M2AN", b"_", b"BBBBBBBBBBB"))


class CertificateTests(unittest.TestCase):
    def setUp(self):
        self.payload = certificate_fixture()
        self.document = (b"Synthetic public wrapper\nBEGIN_NAMESPACE_CERTIFICATE_V1\n" + self.payload
                         + b"\nEND_NAMESPACE_CERTIFICATE_V1\nend")

    def test_exact_published_bytes_schema_and_hash(self):
        self.assertEqual(len(self.payload), 1025)
        self.assertEqual(sha256(self.payload).hexdigest(),
                         "e90c7389e8811c4fe9c870119b76226ec070c47c99ea6ba8f075d89c5ba234b5")
        self.assertEqual(source.extract_namespace_certificate(self.document), self.payload)
        result = source.validate_namespace_certificate(self.payload)
        self.assertFalse(result.tiny_source_checked)
        self.assertEqual(result.status, "PARTIAL_SOURCE_ONLY")

    def test_unicode_wrapper_is_not_material_or_payload(self):
        self.assertEqual(source.extract_namespace_certificate("—\n".encode() + self.document), self.payload)

    def test_exact_single_ordered_marker_pair(self):
        invalid = (self.document + b"\nBEGIN_NAMESPACE_CERTIFICATE_V1",
                   self.document + b"\nEND_NAMESPACE_CERTIFICATE_V1",
                   self.document.replace(b"BEGIN_NAMESPACE", b" BEGIN_NAMESPACE"),
                   self.document.replace(b"END_NAMESPACE", b" END_NAMESPACE"),
                   b"END_NAMESPACE_CERTIFICATE_V1\nBEGIN_NAMESPACE_CERTIFICATE_V1",
                   b"\xff" + self.document, self.document.replace(b"\n", b"\r\n"),
                   self.document + b"\0", self.document.replace(self.payload, self.payload + b"\n"))
        for document in invalid:
            with self.subTest(document=document[:40]), self.assertRaises(ValueError):
                source.extract_namespace_certificate(document)

    def test_reject_self_asserted_schema_issuer_claims_and_tiny_hash(self):
        mutations = (self.payload + b"\n", self.payload.replace(b"true", b"false"),
                     self.payload.replace(b"external", b"internal"),
                     self.payload.replace(b'"claims":', b'"other":'),
                     self.payload.replace(b"f69c85", b"a69c85"),
                     self.payload.replace(b"PCFL", b"FAKE"),
                     self.payload.replace(b'"reserved_prefix_absent":true', b'"reserved_prefix_absent":1'))
        for payload in mutations:
            with self.subTest(payload=payload[:40]), self.assertRaises(ValueError):
                source.validate_namespace_certificate(payload)
        with self.assertRaisesRegex(ValueError, "tiny_source_pin"):
            source.validate_namespace_certificate(self.payload, tiny_source=b"synthetic unrelated source")

    def test_symbolic_language_intersection_no_instances(self):
        for pattern in wire.IDENTIFIERS.values():
            for foreign in source.validate_namespace_certificate(self.payload).public_regexes:
                self.assertFalse(source.regex_languages_intersect(pattern, foreign))
        self.assertTrue(source.regex_languages_intersect("N_[A-Z2-7]{10}", "N_[A-Z2-7]{10}"))
        self.assertTrue(source.regex_languages_intersect("N_[A-Z2-7]{10}", "N_A[A-Z2-7]{9}"))
        self.assertFalse(source.regex_languages_intersect("N_[A-Z2-7]{10}", "N_0[A-Z2-7]{9}"))
        for invalid in (".*", "N_[A-Z2-7]+", "N_[A-Z2-7]{0}", "(N|E)_[A-Z2-7]{10}"):
            with self.assertRaisesRegex(ValueError, "unsupported_namespace_regex"):
                source.regex_languages_intersect(invalid, "N_[A-Z2-7]{10}")

    def test_separation_atoms_lines_ids_and_empty_lines_independently(self):
        report = source.check_namespace_separation({"one": b"CURRENT " + NODE, "two": b"CURRENT " + GOAL},
                                                   certificate_payload=self.payload)
        self.assertTrue(report.passed)
        for first, second, kind, value in ((b"CURRENT " + NODE, b"AT " + NODE, "identifier", NODE),
                                          (b"alpha", b"ALPHA", "atom", b"ALPHA"),
                                          (b"same", b"same", "line", b"same"),
                                          (b"\n", b"\n", "line", b"")):
            report = source.check_namespace_separation({"one": first, "two": second},
                                                       certificate_payload=self.payload)
            self.assertFalse(report.passed)
            self.assertIn((kind, "one", "two", value), report.issues)

    def test_no_domain_inventory_or_live_tiny_proof_claim(self):
        report = source.check_namespace_separation({"synthetic_domain": b"TASK", "synthetic_pool": b"ACK"},
                                                   certificate_payload=self.payload)
        self.assertTrue(report.passed)
        self.assertEqual(report.domains, ("synthetic_domain", "synthetic_pool"))
        self.assertFalse(report.certificate.tiny_source_checked)
        self.assertTrue(report.limitations)
        with self.assertRaises(ValueError):
            source.check_namespace_separation({"alone": b"TASK"}, certificate_payload=self.payload)


class SemanticAliasTests(unittest.TestCase):
    def test_published_14_entry_vector(self):
        semantic = canonical_json({"factors": {"family": "A_PRIVATE_SPOKES"},
                                   "oracle": {"next_role": "birth_train/p00/s/00/useful/-/query"},
                                   "task": {"goal": "M2AN_ABCDEFGHIJKL"}})
        ledger = source.semantic_alias_ledger(semantic)
        self.assertEqual(len(ledger), 236)
        self.assertEqual(len(ledger.split(b"\n")), 14)
        self.assertEqual(sha256(ledger).hexdigest(),
                         "96220f9378f9a5d7ab0e90218ee089018a9024dc339a7115083f16162b3eb636")

    def test_pointer_escapes_leaf_types_and_raw_byte_sorting(self):
        aliases = source.derive_semantic_aliases(canonical_json({
            "oracle": {"a/b~c": [True, False, None, -123, "quoted\"value\\tail"]},
            "task": {"ignored": "DO_NOT_DERIVE"},
        }))
        for alias in (b"/oracle/a~1b~0c/0=BOOL:true", b"/oracle/a~1b~0c/1=BOOL:false",
                      b"/oracle/a~1b~0c/2=NULL", b"/oracle/a~1b~0c/3=INT:-123",
                      b'quoted"value\\tail', b"QUOTED", b"VALUE", b"TAIL"):
            self.assertIn(alias, aliases)
        self.assertEqual(aliases, tuple(sorted(set(aliases))))
        self.assertNotIn(b"DO_NOT_DERIVE", aliases)
        self.assertNotIn(b"0", aliases)

    def test_decoded_final_key_and_no_alias_extension(self):
        aliases = source.derive_semantic_aliases(canonical_json({"core": {"a/b~c": "payload"},
                                                               "declared_aliases": ["IGNORED"]}))
        self.assertIn(b"a/b~c", aliases)
        self.assertIn(b"/core/a~1b~0c", aliases)
        self.assertNotIn(b"IGNORED", aliases)

    def test_drop_only_exact_shared_values_and_complete_identifiers(self):
        aliases = source.derive_semantic_aliases(canonical_json({"target": PORT.decode(),
                                                               "oracle": ["READ", "read", "STEP", "ab"]}))
        self.assertNotIn(PORT, aliases)
        self.assertNotIn(b"FFFFFFFFFFFF", aliases)
        self.assertNotIn(b"READ", aliases)
        self.assertIn(b"read", aliases)
        self.assertIn(b"/target=STR:" + PORT, aliases)

    def test_canonical_semantics_reject_duplicate_keys_and_repaired_escapes(self):
        for raw in (b'{"oracle":1,"oracle":2}', b'{"oracle":1.0}', b'{"oracle":-0}',
                    b'{"oracle":"\\u0050CFL"}', b'{"oracle":"\\u00e9"}', b'{"oracle":"\\r"}',
                    b'{"oracle":"\\u0000"}', b'{ "oracle":1}', b'[]'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                source.derive_semantic_aliases(raw)

    def test_core_and_goal_route_aliases_normalized_and_compact(self):
        for label in source.FORBIDDEN_CORE_LABELS:
            for variant in (label, label.lower(), label.replace(b"_", b"-"),
                            b"<" + label.replace(b"_", b" \t") + b">"):
                with self.subTest(variant=variant):
                    self.assertTrue(source.forbidden_semantic_labels(canonical_json({"core": variant.decode()})))
                    self.assertFalse(scan(variant).passed)
        for label in ("LINK", "old", "N-E-W"):
            self.assertTrue(source.forbidden_semantic_labels(canonical_json({"core": {"edges": [{"label": label}]}})))
        self.assertEqual(source.forbidden_semantic_labels(canonical_json({"notes": "old", "core": {"edges": [{"label": "DID"}]}})), ())

    def test_forbidden_keys_do_not_hide_in_empty_containers(self):
        for value in ({}, []):
            self.assertTrue(source.forbidden_semantic_labels(canonical_json({"PCFL_EVENT_LINK": value})))
            self.assertFalse(scan(b"", semantic_bytes=canonical_json({"core": {"GOAL_BRAID_OLD_PREFIX": value}})).passed)

    def test_protected_key_and_value_hits_are_substrings(self):
        semantic = canonical_json({"oracle": {"next_role": "birth_train/unique_branch"}})
        for raw in (b"x/oracle/next_roley", b"xnext_roley", b"BIRTH-TRAIN/UNIQUE-BRANCH",
                    b"<birth train/unique branch>", b"<N E X T R O L E>"):
            with self.subTest(raw=raw):
                report = scan(raw, semantic_bytes=semantic)
                self.assertFalse(report.passed)
                self.assertTrue(any(hit.category == "semantic_alias" for hit in report.issues))

    def test_scalar_json_escapes_are_decoded_but_material_is_not(self):
        semantic = canonical_json({"oracle": {"value": 'secret"route\\tail'}})
        self.assertIn(b'secret"route\\tail', source.derive_semantic_aliases(semantic))
        self.assertFalse(scan(b'secret"route\\tail', semantic_bytes=semantic).passed)
        self.assertNotIn(b"PCFL", source.semantic_atoms(rb"\u0050CFL"))


class ForwardScannerTests(unittest.TestCase):
    def test_causal_occurrence_clarification_pin(self):
        for version, digest in (("v1", source.CAUSAL_OCCURRENCE_SHA256),
                                ("v2", source.CAUSAL_OCCURRENCE_V2_SHA256)):
            note = (Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
                    / f"2026-09-13_stage2a_causal_occurrence_clarifications_{version}.md")
            self.assertEqual(sha256(note.read_bytes()).hexdigest(), digest)

    def test_check_historical_route_query_requires_same_implicated_query(self):
        prefix = b"QUERY " + QUERY + b"\nREAD RELATION " + QUERY + b"\nSERVICE\nMISS"
        returned = public_field(prefix, QUERY, "route_query")
        issued = public_field(prefix, QUERY, "issued_query", occurrence=1, observed_at=2)
        for phase in ("CHECK", "READ_CHECK"):
            for implicated, expected in ((QUERY, True), (LATER_QUERY, False), (None, False)):
                with self.subTest(phase=phase, implicated=implicated):
                    report = scan(prefix, target=b"THINK REVISE " + QUERY, phase=phase,
                                  implicated_query=implicated, fields=(returned, issued))
                    self.assertEqual(report.passed, expected)
                    occurrences = report.receipts if expected else report.issues
                    self.assertEqual({hit.form for hit in occurrences if hit.start == returned.start},
                                     {"literal", "normalized", "compact"})
                    if expected:
                        self.assertEqual({hit.field_path for hit in report.receipts}, {returned.path, issued.path})
        self.assertEqual(returned.origin, "service")
        self.assertEqual(issued.origin, "actor")

    def test_continue_historical_got_requires_latest_current_and_typed_owner(self):
        prefix = b"GOT " + NODE
        for owner, implicated, current, expected in (
                (EVENT, EVENT, NODE, True), (LATER_EVENT, EVENT, NODE, True),
                (None, EVENT, NODE, False), (EVENT, None, NODE, True),
                (None, None, NODE, False), (LATER_EVENT, None, NODE, True),
                (EVENT, EVENT, LATER_NODE, False), (EVENT, EVENT, None, False),
                (LATER_EVENT, EVENT, LATER_NODE, False), (LATER_EVENT, EVENT, None, False)):
            with self.subTest(owner=owner, implicated=implicated, current=current):
                field = public_field(prefix, NODE, "event_got", owner=owner)
                report = scan(prefix, target=b"READ INDEX " + NODE, phase="CONTINUE",
                              fields=(field,), current=current, implicated_event=implicated)
                self.assertEqual(report.passed, expected)
                self.assertEqual(field.origin, "service")
                if expected:
                    self.assertEqual({hit.form for hit in report.receipts}, {"literal", "normalized", "compact"})
                    self.assertTrue(all(hit.category == "operand" and hit.field_path == field.path
                                        and hit.evidence == field.evidence for hit in report.receipts))

    def test_causal_service_fields_never_waive_other_leak_categories(self):
        for value, kind, target, phase, context in (
                (QUERY, "route_query", b"THINK REVISE " + QUERY, "READ_CHECK", {"implicated_query": QUERY}),
                (NODE, "event_got", b"READ INDEX " + NODE, "CONTINUE",
                 {"current": NODE, "implicated_event": EVENT})):
            prefix = b"QUERY " + value if kind == "route_query" else b"GOT " + value
            field = public_field(prefix, value, kind, owner=LATER_EVENT if kind == "event_got" else None)
            for category, inventory in (
                    ("future_identifier", {"future_identifiers": (value,)}),
                    ("registered_route", {"registered_routes": (value,)}),
                    ("semantic_alias", {"semantic_bytes": canonical_json({"oracle": value[-4:].decode("ascii")})})):
                with self.subTest(kind=kind, category=category):
                    report = scan(prefix, target=target, phase=phase, fields=(field,), **context, **inventory)
                    self.assertFalse(report.passed)
                    self.assertTrue(any(hit.category == category for hit in report.issues))
                    self.assertTrue(any(hit.category == "operand" for hit in report.receipts))
                    self.assertTrue(all(hit.category == "operand" for hit in report.receipts))
            report = scan(prefix + b"\n" + target, target=target, phase=phase, fields=(field,), **context)
            self.assertFalse(report.passed)
            self.assertEqual({hit.form for hit in report.issues if hit.category == "full_target"},
                             {"literal", "normalized", "compact"})
            report = scan(prefix + b"\nprose " + value, target=target, phase=phase, fields=(field,), **context)
            self.assertTrue(any(hit.category == "operand" and hit.start > field.end for hit in report.issues))

    def test_causal_service_fields_require_exact_typed_predecision_receipts(self):
        for value, kind, target, phase, context in (
                (QUERY, "route_query", b"THINK REVISE " + QUERY, "CHECK", {"implicated_query": QUERY}),
                (NODE, "event_got", b"READ INDEX " + NODE, "CONTINUE",
                 {"current": NODE, "implicated_event": EVENT})):
            prefix = b"VALUE " + value
            field = public_field(prefix, value, kind, owner=EVENT if kind == "event_got" else None)
            for invalid in (replace(field, observed_at=10), replace(field, origin="host"),
                            replace(field, evidence=""), replace(field, start=0),
                            replace(field, owner=QUERY), replace(field, owner=EVENT.decode("ascii")),
                            replace(field, owner=b"M2AE_AAAAAAAAAAAA")):
                with self.subTest(kind=kind, invalid=invalid), self.assertRaises(ValueError):
                    scan(prefix, target=target, phase=phase, fields=(invalid,), **context)
        with self.assertRaisesRegex(ValueError, "exact_typed_identifier"):
            scan(QUERY, target=b"STOP", phase="CONTINUE",
                 fields=(public_field(QUERY, QUERY, "event_got", owner=EVENT),))

    def test_shared_got_never_authorizes_foreign_event_port_or_recover_operand(self):
        for operand, target, phase in ((LATER_EVENT, b"THINK REVISE " + LATER_EVENT, "STEP_CHECK"),
                                        (LATER_PORT, b"STEP " + LATER_PORT, "PROSPECT"),
                                        (LATER_QUERY, b"READ RELATION " + LATER_QUERY, "SEEK")):
            prefix = b"GOT " + NODE + b"\nOTHER " + operand
            field = public_field(prefix, NODE, "event_got", owner=LATER_EVENT)
            report = scan(prefix, target=target, phase=phase, current=NODE,
                          implicated_event=EVENT, observed_contradiction=True, fields=(field,))
            with self.subTest(phase=phase):
                self.assertFalse(report.passed)
                self.assertTrue(all(hit.category == "operand" and hit.value == operand
                                    for hit in report.issues))
                self.assertEqual(report.receipts, ())

    def test_prospect_did_allowed_with_receipt_for_each_form(self):
        prefix = b"EVENT " + EVENT + b"\nDID " + PORT
        field = public_field(prefix, PORT, "event_did")
        report = scan(prefix, fields=(field,))
        self.assertTrue(report.passed)
        self.assertEqual({receipt.form for receipt in report.receipts}, {"literal", "normalized", "compact"})
        for receipt in report.receipts:
            self.assertEqual((receipt.start, receipt.end), (field.start, field.end))
            self.assertEqual(receipt.field_path, field.path)
            self.assertEqual(receipt.evidence, field.evidence)

    def test_seek_returned_route_query_and_implicated_recover(self):
        prefix = b"QUERY " + QUERY
        self.assertTrue(scan(prefix, target=b"READ RELATION " + QUERY, phase="SEEK",
                             fields=(public_field(prefix, QUERY, "route_query"),)).passed)
        prefix = b"RECOVER " + QUERY
        field = public_field(prefix, QUERY, "event_recover", owner=EVENT)
        for contradiction, event, expected in ((False, EVENT, False), (True, LATER_EVENT, False), (True, EVENT, True)):
            report = scan(prefix, target=b"READ RELATION " + QUERY, phase="SEEK", fields=(field,),
                          implicated_event=event, observed_contradiction=contradiction)
            self.assertEqual(report.passed, expected)

    def test_check_issued_query_selected_event_and_past_truthful_action(self):
        prefix = b"READ RELATION " + QUERY + b"\nSERVICE\nMISS"
        report = scan(prefix, target=b"THINK REVISE " + QUERY, phase="READ_CHECK",
                      implicated_query=QUERY, fields=(public_field(prefix, QUERY, "issued_query"),))
        self.assertTrue(report.passed)
        for verb in (b"KEEP", b"REVISE"):
            prefix = b"EVENT " + EVENT + b"\nSTEP " + PORT + b"\nWORLD\nCURRENT " + NODE
            report = scan(prefix, target=b"THINK " + verb + b" " + EVENT, phase="STEP_CHECK",
                          implicated_event=EVENT, fields=(public_field(prefix, EVENT, "selected_event"),))
            self.assertTrue(report.passed)

    def test_unrelated_authentic_past_actions_not_blanket_leakage(self):
        prefix = b"READ RELATION " + QUERY + b"\nSTEP " + PORT + b"\nTHINK REVISE " + EVENT
        self.assertTrue(scan(prefix, target=b"STOP", phase="CONTINUE").passed)
        self.assertTrue(scan(prefix, target=b"STEP " + LATER_PORT).passed)

    def test_same_next_full_action_still_forbidden_even_if_historical(self):
        prefix = b"STEP " + PORT
        report = scan(prefix, fields=(public_field(prefix, PORT, "event_did"),))
        self.assertFalse(report.passed)
        self.assertTrue(any(hit.category == "full_target" for hit in report.issues))

    def test_latest_current_and_task_fact_exceptions_are_value_and_field_specific(self):
        prefix = b"TASK\nSTART " + NODE + b"\nGOAL " + GOAL + b"\nCURRENT " + GOAL
        fields = (public_field(prefix, NODE, "task_start"), public_field(prefix, GOAL, "task_goal"),
                  public_field(prefix, GOAL, "task_current", occurrence=1))
        report = scan(prefix, target=b"READ INDEX " + GOAL, phase="CONTINUE", fields=fields,
                      task_start=NODE, task_goal=GOAL, current=GOAL, future_identifiers=(NODE, GOAL))
        self.assertTrue(report.passed)
        wrong = scan(prefix, target=b"READ INDEX " + GOAL, phase="CONTINUE", fields=fields,
                     task_start=NODE, task_goal=GOAL, current=NODE)
        self.assertFalse(wrong.passed)
        self.assertTrue(any(hit.start == fields[-1].start for hit in wrong.issues))

    def test_allowed_occurrence_does_not_exempt_same_id_elsewhere(self):
        prefix = b"DID " + PORT + b"\nevaluator future_step=" + PORT
        report = scan(prefix, fields=(public_field(prefix, PORT, "event_did"),))
        self.assertFalse(report.passed)
        self.assertTrue(report.receipts)
        self.assertTrue(all(hit.start > prefix.index(b"evaluator") for hit in report.issues))

    def test_wrong_phase_untyped_and_wrong_public_field_fail(self):
        prefix = b"QUERY " + PORT
        self.assertFalse(scan(prefix).passed)
        with self.assertRaisesRegex(ValueError, "exact_typed_identifier"):
            scan(prefix, fields=(public_field(prefix, PORT, "route_query"),))
        prefix = b"QUERY " + QUERY
        report = scan(prefix, target=b"THINK REVISE " + QUERY, phase="READ_CHECK",
                      fields=(public_field(prefix, QUERY, "route_query"),), implicated_query=LATER_QUERY)
        self.assertFalse(report.passed)
        for raw in (b"system says " + PORT, b"hidden route=" + PORT,
                    b"future SERVICE DID " + PORT, b"unrelated task=" + PORT):
            self.assertFalse(scan(raw).passed)

    def test_future_ports_queries_events_and_non_task_destinations_fail(self):
        for identifier in (LATER_PORT, LATER_QUERY, LATER_EVENT, LATER_NODE):
            for raw in (identifier, identifier.lower(), identifier.replace(b"_", b"-"),
                        b"<" + b" ".join(identifier.split(b"_")) + b">"):
                with self.subTest(raw=raw):
                    report = scan(raw, future_identifiers=(identifier,))
                    self.assertFalse(report.passed)
                    self.assertTrue(any(hit.category == "future_identifier" for hit in report.issues))

    def test_future_ledger_cannot_be_laundered_by_service_field(self):
        prefix = b"DID " + PORT
        report = scan(prefix, fields=(public_field(prefix, PORT, "event_did"),), future_identifiers=(PORT,))
        self.assertTrue(report.receipts)
        self.assertTrue(any(hit.category == "future_identifier" for hit in report.issues))

    def test_literal_normalized_compact_full_actions_and_source_offsets(self):
        for raw in (b"STEP " + PORT, b"step\t  " + PORT.lower(),
                    b"scheduled=<S-T-E-P> <" + PORT.replace(b"_", b"-") + b">",
                    b"ST EP " + PORT):
            report = scan(raw)
            self.assertFalse(report.passed)
            self.assertTrue(any(hit.category == "full_target" for hit in report.issues))
            self.assertTrue(all(0 <= hit.start < hit.end <= len(raw) for hit in report.issues))
        prefix = b" \t DID\t\t " + PORT
        field = public_field(prefix, PORT, "event_did")
        self.assertTrue(scan(prefix, fields=(field,)).passed)

    def test_no_scan_normalization_in_actor_parser(self):
        for target in (b"step " + PORT, b"STEP\t" + PORT, b"STEP " + PORT + b"\n"):
            with self.assertRaises(ValueError):
                scan(b"", target=target)

    def test_stop_only_exact_protocol_grammar_receipted(self):
        prefix = wire.SYSTEM_MESSAGE.encode()
        field = public_field(prefix, prefix, "protocol")
        report = scan(prefix, target=b"STOP", phase="CONTINUE", fields=(field,))
        self.assertTrue(report.passed)
        self.assertEqual(len(report.receipts), 3)
        self.assertFalse(scan(prefix, target=b"STOP", phase="CONTINUE").passed)
        for suffix in (b"\nSTOP", b"\nstop", b"\nS T O P", b"\n<STOP>",
                       b"\nscheduled=STOP", b"\nevaluator=stop", b"\nanswer=<S-T-O-P>"):
            self.assertFalse(scan(prefix + suffix, target=b"STOP", phase="CONTINUE", fields=(field,)).passed)
        for replacement in (b"stop", b"<STOP>"):
            changed = prefix.replace(b"\nSTOP\n", b"\n" + replacement + b"\n")
            with self.assertRaisesRegex(ValueError, "protocol_bytes_mismatch"):
                scan(changed, target=b"STOP", phase="CONTINUE",
                     fields=(replace(field, end=len(changed)),))

    def test_implicated_think_only_not_future_recovery_query(self):
        prefix = b"THINK REVISE " + QUERY + b"\nQUERY " + QUERY
        fields = (public_field(prefix, QUERY, "think_implicated"),
                  public_field(prefix, QUERY, "route_query", occurrence=1))
        self.assertTrue(scan(prefix, target=b"READ RELATION " + QUERY, phase="SEEK", fields=fields,
                             implicated_query=QUERY).passed)
        self.assertFalse(scan(prefix, target=b"READ RELATION " + QUERY, phase="SEEK", fields=fields,
                              implicated_query=LATER_QUERY).passed)

    def test_registered_route_and_factor_aliases_have_no_field_bypass(self):
        route = b"hidden/route/second_hop"
        self.assertFalse(scan(b"HIDDEN/ROUTE/SECOND-HOP", registered_routes=(route,)).passed)
        semantic = canonical_json({"factors": {"factor_code": "A_PRIVATE_SPOKES"}})
        report = scan(b"factor_code A PRIVATE SPOKES", semantic_bytes=semantic)
        self.assertTrue(any(hit.category == "semantic_alias" for hit in report.issues))
        report = scan(b"DID " + PORT, registered_routes=(PORT,),
                      fields=(public_field(b"DID " + PORT, PORT, "event_did"),))
        self.assertTrue(any(hit.category == "registered_route" for hit in report.issues))

    def test_constant_protocol_semantic_aliases_get_occurrence_receipts_only(self):
        protocol = wire.SYSTEM_MESSAGE.encode("ascii")
        field = public_field(protocol, protocol, "protocol")
        semantic = canonical_json({"core": {"type_labels": ["PORT", "STATE"]}})
        report = scan(protocol, semantic_bytes=semantic, fields=(field,))
        self.assertTrue(report.passed)
        self.assertTrue({b"PORT", b"STATE"}.issubset(source.derive_semantic_aliases(semantic)))
        self.assertEqual({hit.value for hit in report.receipts}, {b"PORT", b"STATE"})
        self.assertEqual(len(report.receipts), 8)
        for suffix in (b"\nPORT STATE", b"\nport state", b"\n<P-O-R-T> <S-T-A-T-E>"):
            report = scan(protocol + suffix, semantic_bytes=semantic, fields=(field,))
            self.assertFalse(report.passed)
            self.assertTrue(all(hit.start > field.end for hit in report.issues))

    def test_alias_exemption_requires_original_exact_protocol_occurrence(self):
        protocol = wire.SYSTEM_MESSAGE.encode("ascii")
        semantic = canonical_json({"core": {"type_labels": ["PORT", "STATE"]}})
        prefix = b"copy\n" + protocol
        moved = public_field(prefix, protocol, "protocol")
        self.assertFalse(scan(prefix, semantic_bytes=semantic, fields=(moved,)).passed)
        field = public_field(protocol, protocol, "protocol")
        with self.assertRaisesRegex(ValueError, "protocol_bytes_mismatch"):
            scan(protocol.lower(), semantic_bytes=semantic, fields=(field,))
        report = scan(protocol, registered_routes=(b"PORT",), fields=(field,))
        self.assertFalse(report.passed)
        self.assertTrue(any(hit.category == "registered_route" for hit in report.issues))

    def test_copied_protocol_aliases_and_cross_boundary_match_still_fail(self):
        protocol = wire.SYSTEM_MESSAGE.encode("ascii")
        field = public_field(protocol, protocol, "protocol")
        semantic = canonical_json({"core": {"type_labels": ["PORT", "STATE"]}})
        prefix = protocol + b"\n" + protocol
        copied = public_field(prefix, protocol, "protocol", occurrence=1)
        report = scan(prefix, semantic_bytes=semantic, fields=(field, copied))
        self.assertFalse(report.passed)
        self.assertTrue(all(hit.start > field.end for hit in report.issues))
        crossing = b"terminate the task.\nLEAK"
        report = scan(protocol + b"\nLEAK", fields=(field,),
                      semantic_bytes=canonical_json({"evaluator": {"leak_marker": crossing.decode("ascii")}}))
        self.assertTrue(any(hit.value == crossing and hit.start < field.end < hit.end
                            for hit in report.issues))

    def test_no_escape_decoding_is_explicitly_partial(self):
        report = scan(rb"\u0053TEP M2AP\u005fFFFFFFFFFFFF")
        self.assertTrue(report.passed)
        self.assertTrue(any("escape decoding" in limitation for limitation in report.limitations))

    def test_missing_forged_overlapping_future_field_receipts_rejected(self):
        prefix = b"DID " + PORT
        field = public_field(prefix, PORT, "event_did")
        mutations = (replace(field, evidence=""), replace(field, origin="system"),
                     replace(field, observed_at=10), replace(field, observed_at=True),
                     replace(field, start=0), replace(field, end=len(prefix) + 1),
                     replace(field, kind="evaluator"), replace(field, path="not-a-pointer"))
        for invalid in mutations:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                scan(prefix, fields=(invalid,))
        with self.assertRaises(ValueError):
            scan(prefix, fields=(field, field))

    def test_invalid_phases_ledgers_context_and_bounds(self):
        for phase in ("UNKNOWN", "SEEK", "CHECK", "CONTINUE"):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                scan(b"", phase=phase)
        for kwargs in ({"future_identifiers": (b"not an ID",)}, {"registered_routes": (b"",)},
                       {"task_start": QUERY}, {"implicated_event": NODE}, {"observed_contradiction": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                scan(b"", **kwargs)
        with self.assertRaisesRegex(ValueError, "bounded_bytes"):
            source.normalize_lines(b"x" * (source.BOUNDS["bytes"] + 1))
        deep = "leaf"
        for index in range(source.BOUNDS["depth"] + 1):
            deep = [deep]
        with self.assertRaisesRegex(ValueError, "depth_bound"):
            source.derive_semantic_aliases(canonical_json({"oracle": deep}))

    def test_check_subphases_and_reserved_sentinels_rejected(self):
        for phase, target in (("READ_CHECK", b"THINK REVISE " + EVENT),
                              ("STEP_CHECK", b"THINK REVISE " + QUERY)):
            with self.assertRaisesRegex(ValueError, "phase_operand_mismatch"):
                scan(b"", target=target, phase=phase)
        with self.assertRaisesRegex(ValueError, "invalid_target_identifier"):
            scan(b"", target=b"STEP M2AP_AAAAAAAAAAAA")
        with self.assertRaises(ValueError):
            scan(b"", future_identifiers=(b"M2AP_AAAAAAAAAAAA",))

    def test_bounded_hits_leaves_nodes_and_fields_fail_explicitly(self):
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, hits=2)):
            with self.assertRaisesRegex(ValueError, "hit_bound"):
                scan(PORT)
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, leaves=2)):
            with self.assertRaisesRegex(ValueError, "leaf_bound"):
                source.derive_semantic_aliases(canonical_json({"oracle": [1, 2, 3]}))
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, nodes=2)):
            with self.assertRaisesRegex(ValueError, "node_bound"):
                source.derive_semantic_aliases(canonical_json({"oracle": [{}, {}, {}]}))
        with patch.object(source, "BOUNDS", dict(source.BOUNDS, fields=0)):
            prefix = b"DID " + PORT
            with self.assertRaisesRegex(ValueError, "bounded_public_fields"):
                scan(prefix, fields=(public_field(prefix, PORT, "event_did"),))

    def test_future_identifier_bound_is_separate_from_fields_and_routes(self):
        identifiers = tuple(b"M2AQ_" + base64.b32encode(index.to_bytes(7, "big")).rstrip(b"=")
                            for index in range(1, 16385))
        self.assertEqual(len(set(identifiers)), 16384)
        self.assertEqual(source.BOUNDS["future_identifiers"], 16384)
        self.assertEqual(source.BOUNDS["fields"], 4096)
        report = scan(identifiers[-1], future_identifiers=identifiers)
        self.assertTrue(any(hit.category == "future_identifier" and hit.value == identifiers[-1]
                            for hit in report.issues))
        with self.assertRaisesRegex(ValueError, "bounded_ledger_sequence_required"):
            scan(b"", future_identifiers=identifiers + (QUERY,))
        self.assertTrue(scan(b"", registered_routes=(b"later route",) * 4096).passed)
        with self.assertRaisesRegex(ValueError, "bounded_ledger_sequence_required"):
            scan(b"", registered_routes=(b"later route",) * 4097)
        with self.assertRaisesRegex(ValueError, "bounded_public_fields"):
            scan(b"", fields=(None,) * 4097)

    def test_empty_compact_alias_is_unsupported_not_exempted(self):
        with self.assertRaisesRegex(ValueError, "empty_normalized_ledger"):
            scan(b"", semantic_bytes=canonical_json({"oracle": "___"}))
        with self.assertRaisesRegex(ValueError, "empty_normalized_ledger"):
            scan(b"", registered_routes=(b"< >",))

    def test_status_flags_immutability_and_determinism(self):
        report = scan(b"DID " + PORT)
        self.assertEqual(report, scan(b"DID " + PORT))
        self.assertEqual(source.STATUS, "PARTIAL_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        with self.assertRaises(TypeError):
            source.SCIENCE_GATES["GO_CLAIM"] = True
        with self.assertRaises(AttributeError):
            report.status = "READY"


if __name__ == "__main__":
    unittest.main()
