"""Synthetic raw-readout reduction tests; no native tokenizer or model execution."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_pchain2_free_material as free
from gpu import astra_pchain2_free_reduce as reduce
from gpu import astra_pchain2_prepare as source
from test_astra_pchain2_free_material import saved_fixture
from test_astra_pchain2_native import FakeTokenizer, canary_fixture


def raw_record(call, *, text=None, terminal=True, truncated=False):
    return dict(slot=deepcopy(call["slot"]), status="RAW", token_ids=[1001, 1] if terminal else [1001],
                raw_utf8_hex=(call["expected"] if text is None else text).encode("utf-8").hex(),
                terminal=terminal, truncated=truncated)


class FreeReductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = free.generate_material(FakeTokenizer(), saved_identifiers=saved_fixture(),
                                               canaries=canary_fixture())["evaluation"]
        cls.records = {state: [raw_record(call) for call in manifest["calls"]]
                       for state, manifest in cls.manifests.items()}

    def test_exact_outputs_report_each_panel_without_aggregate_pass(self):
        report = reduce.reduce_material(self.manifests, self.records)
        self.assertEqual(report["material_kind"], free.MATERIAL_KIND)
        self.assertFalse(report["original_protocol_compliance_assessed"])
        self.assertFalse(report["null_clearance_assessed"])
        self.assertNotIn("pass", report)
        self.assertNotIn("recommendation", report)
        total = 0
        for state, counts in zip(source.STATES, source.PANEL_COUNTS):
            for panel, count in zip(source.PANELS, counts):
                summary = report["states"][state]["panels"][panel]
                self.assertEqual((summary["n"], summary["successes"], summary["raw"], summary["missing"]),
                                 (count, count, count, 0))
                total += summary["n"]
            for summary in report["states"][state]["one_hop_by_hop"].values():
                self.assertEqual((summary["n"], summary["successes"]), (16, 16))
        self.assertEqual(total, 448)
        self.assertEqual(report["lr0_vs_base_common80"]["raw_identities"], 80)
        for summary in report["deranged_redirection"]["panels"].values():
            self.assertEqual(summary["both_correct_redirected"], 16)
            self.assertEqual(summary["deranged_authentic_expected_hits"], 0)

    def test_absent_states_keep_all_designated_denominators(self):
        report = reduce.reduce_material(self.manifests, {})
        for state in report["states"].values():
            for summary in state["panels"].values():
                self.assertEqual(summary["missing"], summary["n"])
                self.assertEqual(summary["successes"], 0)
        self.assertEqual(report["lr0_vs_base_common80"]["unavailable_pairs"], 80)
        for summary in report["deranged_redirection"]["panels"].values():
            self.assertEqual((summary["n"], summary["unavailable_pairs"], summary["both_correct_redirected"]), (16, 16, 0))

    def test_missing_error_notrun_invalid_never_shrink_n(self):
        records = deepcopy(self.records)
        records["BASE"][0] = dict(slot=records["BASE"][0]["slot"], status="ERROR", error="failed")
        records["BASE"][1] = dict(slot=records["BASE"][1]["slot"], status="NOT_RUN")
        records["BASE"][2]["raw_utf8_hex"] = "bad hex"
        records["BASE"].pop(3)
        summary = reduce.reduce_material(self.manifests, records)["states"]["BASE"]["panels"]["one_hop"]
        self.assertEqual(summary, dict(n=32, successes=28, raw=28, missing=1, errors=1, not_run=1, invalid_raw=1))

    def test_no_newline_normalization_or_trace_extraction(self):
        call = next(call for call in self.manifests["ATOM-JUNCTION"]["calls"] if call["slot"]["panel"] == "eval_trace")
        variants = (call["expected"].rstrip("\n"), call["expected"] + "\n", " " + call["expected"],
                    call["expected"].replace("\n", "\r\n"), call["expected"].splitlines()[-1] + "\n")
        for text in variants:
            with self.subTest(text=text):
                report = reduce.reduce_material(self.manifests, {"ATOM-JUNCTION": [raw_record(call, text=text)]})
                summary = report["states"]["ATOM-JUNCTION"]["panels"]["eval_trace"]
                self.assertEqual((summary["n"], summary["successes"], summary["raw"], summary["missing"]), (16, 0, 1, 15))

    def test_EOT_nontruncated_contract_and_malformed_flags(self):
        call = self.manifests["BASE"]["calls"][0]
        records = [raw_record(call, terminal=False), raw_record(call), raw_record(call), raw_record(call)]
        records[1]["token_ids"][-1] = 999
        records[2]["terminal"] = 1
        records[3].update(token_ids=[1001] * call["slot"]["max_new_tokens"], terminal=False, truncated=True)
        for index, record in enumerate(records):
            with self.subTest(index=index):
                summary = reduce.reduce_material(self.manifests, {"BASE": [record]})["states"]["BASE"]["panels"]["one_hop"]
                self.assertEqual(summary["successes"], 0)
                self.assertEqual(summary["invalid_raw"], int(index in (1, 2)))

    def test_RAW_identity_is_independent_of_correctness_and_requires_real_records(self):
        records = {state: [raw_record(call, text="WRONG\n") for call in self.manifests[state]["calls"]]
                   for state in ("BASE", "LR0")}
        summary = reduce.reduce_material(self.manifests, records)["lr0_vs_base_common80"]
        self.assertEqual((summary["raw_identities"], summary["both_expected_hits"]), (80, 0))
        records["LR0"][0]["token_ids"] = [1002, 1]
        summary = reduce.reduce_material(self.manifests, records)["lr0_vs_base_common80"]
        self.assertEqual((summary["raw_bytes_identical"], summary["raw_identities"]), (80, 79))
        for state in ("BASE", "LR0"):
            records[state][1] = dict(slot=records[state][1]["slot"], status="NOT_RUN")
        summary = reduce.reduce_material(self.manifests, records)["lr0_vs_base_common80"]
        self.assertEqual((summary["n"], summary["raw_identities"], summary["unavailable_pairs"]), (80, 78, 1))

    def test_deranged_authentic_target_hits_are_not_redirections(self):
        records = deepcopy(self.records)
        authentic = {(call["slot"]["panel"], call["slot"]["index"]): call
                     for call in self.manifests["ATOM-JUNCTION"]["calls"]}
        for record in records["DERANGED-JUNCTION"]:
            if record["slot"]["panel"] in ("eval_trace", "eval_direct"):
                key = record["slot"]["panel"], record["slot"]["index"]
                record["raw_utf8_hex"] = authentic[key]["expected"].encode().hex()
        redirection = reduce.reduce_material(self.manifests, records)["deranged_redirection"]
        for panel in ("eval_trace", "eval_direct"):
            summary = redirection["panels"][panel]
            self.assertEqual((summary["both_correct_redirected"], summary["deranged_expected_hits"],
                              summary["deranged_authentic_expected_hits"]), (0, 0, 16))
        self.assertEqual(redirection["first_hop_preservation"]["both_expected_hits"], 16)
        self.assertEqual(redirection["panels"]["one_hop_second"]["both_correct_redirected"], 16)

    def test_partial_deranged_keeps_missing_pairs_and_separate_target_hits(self):
        records = {"DERANGED-JUNCTION": self.records["DERANGED-JUNCTION"]}
        summary = reduce.reduce_material(self.manifests, records)["deranged_redirection"]["panels"]["eval_trace"]
        self.assertEqual((summary["n"], summary["deranged_expected_hits"], summary["authentic_expected_hits"],
                          summary["both_correct_redirected"], summary["unavailable_pairs"]), (16, 16, 0, 0, 16))

    def test_mixed_material_candidates_and_changed_rosters_rejected(self):
        for variant in ("kind", "root", "candidate", "roster", "question"):
            manifests = deepcopy(self.manifests)
            changed = manifests["LR0"]
            if variant == "kind":
                changed["material_kind"] = "NATIVE_TOKENIZER_MATERIAL"
            elif variant == "root":
                changed["identifier_receipt_sha256"] = "other"
            elif variant == "candidate":
                changed["calls"][0]["user"] += "ENDPOINT CANDIDATES\n"
            elif variant == "roster":
                changed["calls"].pop()
            else:
                changed["calls"][0]["user"] += "different question\n"
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                reduce.reduce_material(manifests, {})

    def test_same_question_and_distinct_counterfactual_targets_required(self):
        for field in ("user", "expected"):
            manifests = deepcopy(self.manifests)
            authentic = next(call for call in manifests["ATOM-JUNCTION"]["calls"] if call["slot"]["panel"] == "eval_trace")
            changed = next(call for call in manifests["DERANGED-JUNCTION"]["calls"] if call["slot"]["panel"] == "eval_trace")
            changed[field] = authentic[field] + "changed\n" if field == "user" else authentic[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "same_question_distinct"):
                reduce.reduce_material(manifests, {})

    def test_duplicate_or_wrong_state_raw_slot_rejected_not_selected(self):
        record = deepcopy(self.records["BASE"][0])
        with self.assertRaisesRegex(ValueError, "duplicate_raw_slot"):
            reduce.reduce_material(self.manifests, {"BASE": [record, record]})
        record["slot"]["state"] = "LR0"
        with self.assertRaisesRegex(ValueError, "unknown_or_changed_raw_slot"):
            reduce.reduce_material(self.manifests, {"BASE": [record]})

    def test_CLI_missing_files_partial_line_override_and_nonoverwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation = root / "evaluation"
            evaluation.mkdir()
            for state, manifest in self.manifests.items():
                (evaluation / (state + ".json")).write_text(json.dumps(manifest))
            raw_path = root / "base.jsonl"
            raw = b"".join((json.dumps(record) + "\n").encode() for record in self.records["BASE"][:3]) + b'{"slot":'
            raw_path.write_bytes(raw)
            output = root / "scores" / "snapshot.json"
            argv = ["--evaluation-dir", str(evaluation), "--readouts-dir", str(root / "readouts"),
                    "--raw", "BASE=" + str(raw_path), "--output", str(output)]
            with redirect_stdout(io.StringIO()):
                reduce.main(argv)
                with self.assertRaises(FileExistsError):
                    reduce.main(argv)
            report = json.loads(output.read_text())
            self.assertEqual(raw_path.read_bytes(), raw)
            summary = report["states"]["BASE"]["panels"]["one_hop"]
            self.assertEqual((summary["n"], summary["successes"], summary["missing"]), (32, 3, 29))
            self.assertEqual(report["inputs"]["BASE"]["readout"]["parse_errors"][0]["line"], 4)
            self.assertFalse(report["inputs"]["LR0"]["readout"]["present"])


if __name__ == "__main__":
    unittest.main()
