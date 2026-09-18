"""Bounded synthetic allocator tests, never real production token qualification."""

import copy
import hashlib
import inspect
import itertools
from pathlib import Path
import unittest

from organism_v6 import pcfl_tokenizer_qualification as qualification


def bindings_fixture(root_slots=None):
    root_slots = root_slots or [{"root": "excluded/0", "namespaces": {"node": ["left", "right"]}}]
    references = [[root["root"], namespace, name] for root in root_slots
                  for namespace in qualification.PREFIXES if namespace in root["namespaces"]
                  for name in root["namespaces"][namespace]]
    mates = references if len(references) > 1 else references * 2
    classes = [{"id": kind, "kind": kind,
                "members": [{"id": f"{kind}/{index}", "parts": [{"literal": kind + " "}, {"slot": reference}]} for index, reference in enumerate(mates)]}
               for kind in qualification.KINDS]
    pins = {"revision": "SYNTHETIC_PYTHON_ENCODER", "files": {"synthetic-tokenizer.json": "a" * 64},
            "chat_template_sha256": "b" * 64, "encoding_policy": qualification.ENCODING_POLICY}
    return {"schema": qualification.SCHEMA, "source_pins": copy.deepcopy(qualification.SOURCE_PINS),
            "tokenizer_pins": pins, "root_slots": root_slots,
            "reserved_literals": {"prompt_keywords": ["EVENT", "LINK", "MISS"], "canary_ids": ["CANARY_RESERVED"],
                                  "parser_prefixes": ["N_", "P_", "E_", "L_", "Q_", "R_", "G_"], "other": []},
            "substitutions": {"required": {kind: [kind] for kind in qualification.KINDS}, "classes": classes},
            "required_training_ids": ["fit/0", "fit/1"],
            "training_sequences": [{"id": "fit/0", "parts": [{"literal": "TRAIN0 "}, {"slot": references[0]}, {"literal": " EOS"}]},
                                   {"id": "fit/1", "parts": [{"literal": "TRAIN1 LONGER "}, {"slot": references[-1]}, {"literal": " EOS"}]}],
            "render_registry_sha256": "c" * 64}


def synthetic_encode(text):
    if len(text) == 12 and text[1] == "_":
        return [101, 102, 103, 104]
    return list(range(len(text.encode("utf-8"))))


def bounded(bindings=None, encode=synthetic_encode, limits=None, sink=None):
    bindings = bindings or bindings_fixture()
    return qualification._qualify(bindings, encode, bindings["tokenizer_pins"],
                                  limits or qualification._Limits(2, 5, (4, 5)), True, sink)


class OpaqueQualificationTests(unittest.TestCase):
    def test_authority_source_pins(self):
        directory = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
        for name, expected in qualification.SOURCE_PINS.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)

    def test_seed_candidate_and_namespace_golden(self):
        expected = int.from_bytes(hashlib.sha256(b"PCFL-V2.1-PREP\0opaque/dev/0").digest()[:8], "big") & ((1 << 63) - 1)
        self.assertEqual(qualification.seed("opaque/dev/0"), expected)
        self.assertEqual(qualification.opaque_candidate("dev/0", "event", 0, 0), "E_3TGT3U43QK")
        self.assertNotEqual(qualification.seed("root/dev/0"), expected)
        for namespace in qualification.PREFIXES:
            for salt in (0, 1, 999999):
                value = qualification.opaque_candidate("dev/0", namespace, 0, salt)
                self.assertEqual(len(value.encode("ascii")), 12)
                self.assertTrue(qualification.validate_identifier(value, namespace))
        for salt in (-1, 1000000, True):
            with self.subTest(salt=salt), self.assertRaises(qualification.QualificationError):
                qualification.opaque_candidate("dev/0", "node", 0, salt)
        for value in ("a" * 24, "N_abcdefghij", "N_0000000000", "N_AAAAAAAAA", "E_AAAAAAAAAA"):
            with self.subTest(value=value), self.assertRaises(qualification.QualificationError):
                qualification.validate_identifier(value, "node")

    def test_structural_order_not_mapping_order_or_spelling(self):
        roots = [{"root": root, "namespaces": {namespace: ["z_first", "a_second"] for namespace in reversed(qualification.PREFIXES)}} for root in qualification.ROOTS]
        bindings = bindings_fixture(roots)
        slots, _ = qualification._validate_bindings(bindings, bindings["tokenizer_pins"], False)
        self.assertEqual(slots[:4], [("excluded/0", "node", "z_first", 0), ("excluded/0", "node", "a_second", 1),
                                    ("excluded/0", "port", "z_first", 0), ("excluded/0", "port", "a_second", 1)])
        self.assertEqual(slots[-1], ("dev/1", "goal", "a_second", 1))
        self.assertEqual(len(slots), 7 * 7 * 2)
        bindings["root_slots"].reverse()
        with self.assertRaisesRegex(qualification.QualificationError, "out-of-order roots"):
            qualification._validate_bindings(bindings, bindings["tokenizer_pins"], False)

    def test_production_limits_are_fixed_and_not_public_knobs(self):
        self.assertEqual(qualification.PRODUCTION_LIMITS.wire(), {"pool_size": 4096, "salt_limit": 1000000, "lengths": list(range(4, 13))})
        self.assertEqual(set(inspect.signature(qualification.qualify_opaque_ids).parameters), {"bindings", "encode", "tokenizer_pins", "receipt_sink"})
        bindings = bindings_fixture()
        with self.assertRaisesRegex(qualification.QualificationError, "cannot be weakened"):
            qualification._qualify(bindings, synthetic_encode, bindings["tokenizer_pins"], qualification._Limits(1, 2, (4,)), False)
        calls = []
        with self.assertRaises(qualification.QualificationError):
            qualification.qualify_opaque_ids(bindings, lambda text: calls.append(text), bindings["tokenizer_pins"])
        self.assertEqual(calls, [])

    def test_first_4096_salt_ordered_pool_and_reserved_receipt(self):
        bindings = bindings_fixture()
        first = qualification.opaque_candidate("excluded/0", "node", 0, 0)
        bindings["reserved_literals"]["canary_ids"].append(first)
        recorder = qualification._Recorder(synthetic_encode, "a" * 64, "b" * 64, "c" * 64, None)
        pool = qualification._pool(("excluded/0", "node", "left", 0), 4, qualification._Limits(4096, 4097, (4,)), bindings["reserved_literals"], recorder)
        self.assertEqual(len(pool), 4096)
        self.assertEqual([entry["salt"] for entry in pool], list(range(1, 4097)))
        self.assertEqual(recorder.count, 4097)
        self.assertEqual(recorder.records[0]["text"], first)
        self.assertEqual(recorder.records[0]["token_ids"], [101, 102, 103, 104])
        self.assertEqual(len({entry["value"] for entry in pool}), 4096)

    def test_receipts_are_actual_calls_and_identical_rerun(self):
        calls = []
        def encode(text):
            tokens = synthetic_encode(text)
            calls.append((text, tokens[:]))
            return tokens
        first = bounded(encode=encode)
        second = bounded()
        self.assertEqual(first, second)
        self.assertEqual([(row["text"], row["token_ids"]) for row in first["receipts"]], calls)
        self.assertEqual(first["selected_length"], 4)
        self.assertEqual([row["salt"] for row in first["selected"]], [0, 0])
        self.assertTrue(first["synthetic_test"])
        self.assertTrue(first["qualified_for_supplied_registry"])
        self.assertFalse(first["full_production_qualified"])
        self.assertFalse(first["ready_for_model_calls"])
        previous = "0" * 64
        for index, row in enumerate(first["receipts"]):
            self.assertEqual(row["index"], index)
            self.assertEqual(row["previous_sha256"], previous)
            previous = qualification.digest({key: value for key, value in row.items() if key != "sha256"})
            self.assertEqual(row["sha256"], previous)
        self.assertEqual(first["receipt_chain_sha256"], previous)

    def test_smallest_feasible_length_after_pool_exhaustion(self):
        def encode(text):
            return [9] * 5 if len(text) == 12 else synthetic_encode(text)
        result = bounded(encode=encode)
        self.assertEqual(result["selected_length"], 5)
        self.assertEqual(result["attempts"][0], {"length": 4, "status": "pool_exhausted", "slot": ["excluded/0", "node", "left"]})
        self.assertEqual([row["context"]["salt"] for row in result["receipts"][:5]], list(range(5)))
        self.assertEqual([row["salt"] for row in result["selected"]], [0, 0])

    def test_first_dfs_solution_not_best_scoring_or_random_choice(self):
        left0 = qualification.opaque_candidate("excluded/0", "node", 0, 0)
        right0 = qualification.opaque_candidate("excluded/0", "node", 1, 0)
        def encode(text):
            if text.startswith("query "):
                return [8] * (21 if text == "query " + right0 else 20)
            return synthetic_encode(text)
        result = bounded(encode=encode)
        self.assertEqual([row["salt"] for row in result["selected"]], [0, 1])
        self.assertEqual(result["inventory"]["excluded/0"]["node"]["left"], left0)
        self.assertTrue(qualification.verify_qualification(result, bindings_fixture(), bindings_fixture()["tokenizer_pins"])["transcript_and_search_verified"])

    def test_dfs_backtracks_earlier_slot(self):
        left0 = qualification.opaque_candidate("excluded/0", "node", 0, 0)
        def encode(text):
            if text.startswith("query "):
                return [8] * (31 if text == "query " + left0 else 20)
            return synthetic_encode(text)
        result = bounded(encode=encode)
        self.assertEqual([row["salt"] for row in result["selected"]], [1, 0])

    def test_joint_failure_at_lower_length_still_uses_next_registered_length(self):
        known = {qualification.opaque_candidate("excluded/0", "node", index, salt): (index, salt) for index in range(2) for salt in range(5)}
        def encode(text):
            if text in known:
                return [4] * (4 if known[text][1] % 2 == 0 else 5)
            if text.startswith("query "):
                index, salt = known[text[6:]]
                return [7] * (20 + index if salt % 2 == 0 else 20)
            return synthetic_encode(text)
        result = bounded(encode=encode)
        self.assertEqual(result["selected_length"], 5)
        self.assertEqual([row["salt"] for row in result["selected"]], [1, 1])
        self.assertEqual(result["attempts"][0]["status"], "joint_constraints_exhausted")

    def test_global_collision_pruning_on_bounded_synthetic_pools(self):
        bindings = bindings_fixture()
        slots, checks = qualification._validate_bindings(bindings, bindings["tokenizer_pins"], True)
        first = qualification.opaque_candidate("excluded/0", "node", 0, 0)
        second = qualification.opaque_candidate("excluded/0", "node", 1, 0)
        pools = [[{"value": first, "salt": 0, "receipt_sha256": "0" * 64}],
                 [{"value": first, "salt": 0, "receipt_sha256": "0" * 64}, {"value": second, "salt": 1, "receipt_sha256": "0" * 64}]]
        recorder = qualification._Recorder(synthetic_encode, "a" * 64, "b" * 64, "c" * 64, None)
        assignment, _ = qualification._search(slots, pools, checks, recorder, {})
        self.assertEqual(assignment[slots[1][:3]]["value"], second)

    def test_reserved_literals_and_namespace_prefix_distinction(self):
        bindings = bindings_fixture()
        first = qualification.opaque_candidate("excluded/0", "node", 0, 0)
        self.assertFalse(qualification._reserved(first, bindings["reserved_literals"]))
        for category, literal in (("canary_ids", first), ("prompt_keywords", first[2:6]), ("other", "stored " + first)):
            changed = copy.deepcopy(bindings)
            changed["reserved_literals"][category].append(literal)
            result = bounded(changed)
            self.assertNotEqual(result["selected"][0]["value"], first)

    def test_training_limit_is_strict_and_no_cross_arm_token_equalization(self):
        def encode(text):
            if text.startswith("TRAIN"):
                return [1] * (511 if text.startswith("TRAIN0") else 400)
            return synthetic_encode(text)
        result = bounded(encode=encode)
        self.assertTrue(result["qualified_for_supplied_registry"])
        self.assertEqual([check["members"][0]["token_count"] for check in result["accepted_checks"] if check["kind"] == "training"], [511, 400])
        def too_long(text):
            return [1] * 512 if text.startswith("TRAIN0") else synthetic_encode(text)
        failed = bounded(encode=too_long, limits=qualification._Limits(1, 2, (4,)))
        self.assertEqual(failed["status"], "VS_ASSAY_INVALID")
        self.assertEqual(failed["accepted_checks"], [])
        self.assertTrue(any(len(row["token_ids"]) == 512 for row in failed["receipts"]))

    def test_missing_required_inputs_fail_before_any_encoding(self):
        mutations = [lambda data: data.pop("reserved_literals"),
                     lambda data: data["reserved_literals"].pop("canary_ids"),
                     lambda data: data["substitutions"]["required"].pop("event_twin"),
                     lambda data: data["substitutions"]["classes"].pop(),
                     lambda data: data["training_sequences"].pop(),
                     lambda data: data["root_slots"][0]["namespaces"]["node"].append("uncovered"),
                     lambda data: data.update(equal_target_tokens=True),
                     lambda data: data["training_sequences"][0]["parts"].append({"literal": "PAD_S1_00"}),
                     lambda data: data["substitutions"]["classes"][0]["members"][0]["parts"].append({"slot": ["dev/2", "node", "missing"]}),
                     lambda data: data["training_sequences"][0]["parts"].append({"literal": "{UNBOUND_RENDER}"})]
        for mutate in mutations:
            data, calls = bindings_fixture(), []
            mutate(data)
            with self.subTest(mutate=mutate), self.assertRaises(qualification.QualificationError):
                bounded(data, lambda text: calls.append(text))
            self.assertEqual(calls, [])

    def test_tokenizer_and_source_drift_fail_before_encoding(self):
        bindings, calls = bindings_fixture(), []
        for key, value in (("revision", "changed"), ("files", {"other": "a" * 64}), ("chat_template_sha256", "f" * 64), ("encoding_policy", "automatic_truncation")):
            pins = copy.deepcopy(bindings["tokenizer_pins"])
            pins[key] = value
            with self.subTest(key=key), self.assertRaises(qualification.QualificationError):
                qualification._qualify(bindings, lambda text: calls.append(text), pins, qualification._Limits(1, 1, (4,)), True)
        bindings["source_pins"][next(iter(bindings["source_pins"]))] = "0" * 64
        with self.assertRaises(qualification.QualificationError):
            bounded(bindings, lambda text: calls.append(text))
        self.assertEqual(calls, [])

    def test_exhaustion_preserves_all_actual_receipts_without_fallback(self):
        calls = []
        def encode(text):
            calls.append(text)
            return [4] * 3
        result = bounded(encode=encode, limits=qualification._Limits(2, 3, (4, 5)))
        self.assertEqual(result["status"], "VS_ASSAY_INVALID")
        self.assertIsNone(result["selected_length"])
        self.assertEqual(result["inventory"], {})
        self.assertEqual(result["receipt_count"], 6)
        self.assertEqual(len(calls), 6)
        self.assertEqual(result["attempts"], [{"length": length, "status": "pool_exhausted", "slot": ["excluded/0", "node", "left"]} for length in (4, 5)])
        self.assertTrue(qualification.verify_qualification(result, bindings_fixture(), bindings_fixture()["tokenizer_pins"])["transcript_and_search_verified"])

    def test_encoder_failure_has_error_receipt_and_no_retry(self):
        calls = []
        def encode(text):
            calls.append(text)
            raise RuntimeError("synthetic encoder failure")
        result = bounded(encode=encode)
        self.assertEqual(result["status"], "VS_ASSAY_INVALID")
        self.assertEqual(len(calls), 1)
        self.assertIsNone(result["receipts"][0]["token_ids"])
        self.assertIn("synthetic encoder failure", result["receipts"][0]["error"])
        for invalid in ([True], [-1], [], (1, 2, 3, 4), {"length": 4}):
            with self.subTest(invalid=invalid):
                failed = bounded(encode=lambda text: invalid)
                self.assertEqual(failed["status"], "VS_ASSAY_INVALID")
                self.assertEqual(failed["receipt_count"], 1)

    def test_streaming_transcript_verifies_and_sink_failure_stops(self):
        records = []
        result = bounded(sink=records.append)
        self.assertIsNone(result["receipts"])
        self.assertEqual(len(records), result["receipt_count"])
        verified = qualification.verify_qualification(result, bindings_fixture(), bindings_fixture()["tokenizer_pins"], records)
        self.assertTrue(verified["transcript_and_search_verified"])
        self.assertFalse(verified["actual_encoder_provenance_verified"])
        calls = []
        def encode(text):
            calls.append(text)
            return synthetic_encode(text)
        def bad_sink(record):
            raise OSError("synthetic persistence failure")
        with self.assertRaisesRegex(qualification.QualificationError, "sink failed"):
            bounded(encode=encode, sink=bad_sink)
        self.assertEqual(len(calls), 1)

    def test_transcript_and_result_tampering_rejected(self):
        bindings = bindings_fixture()
        result = bounded(bindings)
        mutations = [lambda changed: changed["selected"][0].update(salt=1),
                     lambda changed: changed.update(full_production_qualified=True),
                     lambda changed: changed["receipts"][0]["token_ids"].__setitem__(0, 999),
                     lambda changed: changed["receipts"].pop(),
                     lambda changed: changed["receipts"][0]["context"].update(salt=999)]
        for mutate in mutations:
            changed = copy.deepcopy(result)
            mutate(changed)
            changed["sha256"] = qualification.digest({key: value for key, value in changed.items() if key != "sha256"})
            with self.subTest(mutate=mutate), self.assertRaises(qualification.QualificationError):
                qualification.verify_qualification(changed, bindings, bindings["tokenizer_pins"])

    def test_input_and_sink_mutation_cannot_change_decisions_or_retained_records(self):
        bindings = bindings_fixture()
        expected = bounded(copy.deepcopy(bindings))
        def encode(text):
            bindings["root_slots"][0]["namespaces"]["node"].append("external_mutation")
            return synthetic_encode(text)
        observed = bounded(bindings, encode)
        self.assertEqual(observed, expected)
        records = []
        def sink(record):
            records.append(copy.deepcopy(record))
            record["text"] = "mutated only in caller-owned copy"
        streamed = bounded(sink=sink)
        self.assertEqual(streamed["receipt_chain_sha256"], expected["receipt_chain_sha256"])
        self.assertTrue(qualification.verify_qualification(streamed, bindings_fixture(), bindings_fixture()["tokenizer_pins"], records)["transcript_and_search_verified"])

    def test_first_solution_matches_independent_bounded_cartesian_oracle(self):
        bindings = bindings_fixture([{"root": "excluded/0", "namespaces": {"node": ["first", "second", "third"]}}])
        lengths = ((7, 8, 9), (10, 8, 9), (9, 9, 8))
        candidates = {qualification.opaque_candidate("excluded/0", "node", index, salt): lengths[index][salt]
                      for index in range(3) for salt in range(3)}
        expected = next(vector for vector in itertools.product(range(3), repeat=3)
                        if len({lengths[index][salt] for index, salt in enumerate(vector)}) == 1)
        def encode(text):
            return [17] * candidates[text[6:]] if text.startswith("query ") else synthetic_encode(text)
        result = bounded(bindings, encode, qualification._Limits(3, 3, (4,)))
        self.assertEqual(expected, (1, 1, 2))
        self.assertEqual(tuple(entry["salt"] for entry in result["selected"]), expected)
        query = next(check for check in result["accepted_checks"] if check["id"] == "query")
        self.assertEqual([member["token_count"] for member in query["members"]], [8, 8, 8])

    def test_all_roots_and_namespaces_are_globally_disjoint_in_bounded_search(self):
        roots = [{"root": root, "namespaces": {namespace: ["slot"] for namespace in qualification.PREFIXES}} for root in qualification.ROOTS]
        result = bounded(bindings_fixture(roots), limits=qualification._Limits(1, 1, (4,)))
        self.assertTrue(result["qualified_for_supplied_registry"])
        values = [entry["value"] for entry in result["selected"]]
        self.assertEqual(len(values), 49)
        self.assertEqual(len(set(values)), 49)
        self.assertFalse(any(left in right for left, right in itertools.permutations(values, 2)))
        self.assertEqual([(entry["root"], entry["namespace"]) for entry in result["selected"]],
                         [(root, namespace) for root in qualification.ROOTS for namespace in qualification.PREFIXES])
        self.assertFalse(result["full_production_qualified"])

    def test_fully_literal_failure_and_incomplete_pools_are_not_relaxed(self):
        bindings = bindings_fixture()
        group = bindings["substitutions"]["classes"][0]
        group["members"][0]["parts"] = [{"literal": "short"}]
        group["members"][1]["parts"] = [{"literal": "a longer fixed row"}]
        failed = bounded(bindings)
        self.assertEqual(failed["failure"], "constant_render_constraint_failed")
        self.assertEqual(failed["receipt_count"], 2)
        self.assertEqual(failed["attempts"], [])
        self.assertTrue(all(row["context"]["kind"] == "substitution" for row in failed["receipts"]))
        failed = bounded(limits=qualification._Limits(3, 2, (4,)))
        self.assertEqual(failed["status"], "VS_ASSAY_INVALID")
        self.assertEqual(failed["receipt_count"], 2)
        self.assertEqual(failed["selected"], [])


if __name__ == "__main__":
    unittest.main()
