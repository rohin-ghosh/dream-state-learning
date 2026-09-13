"""Fixed archived evidence and explicitly simulated independent-replay fixtures.

No native replay, tokenizer qualification, model loading or generation here.
"""

import copy
from collections import UserDict
from functools import lru_cache
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_prefix_import as prefix
from organism_v6 import pcfl_vertical_train as writer


ARCHIVE = Path(__file__).resolve().parents[1] / "gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/evidence.tar"


@lru_cache(maxsize=1)
def archived_fixture():
    evidence = prefix.load_evidence(ARCHIVE)
    config = prefix._json(evidence["files"]["formation/formation_config.json"])
    report = prefix._json(evidence["files"]["formation/records/formation.json"])
    receipt = prefix.seal({
        "schema": "pcfl.event_prefix.original_v3_replay.v1", "method": "EXACT_ORIGINAL_V3_PATH",
        "source_root": prefix.SOURCE_ROOT, "source_tar_sha256": prefix.SOURCE_TAR_SHA256,
        "formation_source_sha256": prefix.FORMATION_SHA256,
        "config_file_sha256": prefix.FIXED_FILES["formation/formation_config.json"],
        "report_file_sha256": prefix.FIXED_FILES["formation/records/formation.json"],
        "replay_result": {"report_sha256": report["sha256"], "config_sha256": config["sha256"],
                          "status": "FORMATION_FAILED", "local_replay_valid": True,
                          "native_custody_verified": False, "full_contract_released": False},
        "model_calls": 0, "fits": 0, "updates": 0})
    imported = prefix.build_import(evidence, receipt, receipt["sha256"])
    return evidence, receipt, imported


def reseal(value):
    return prefix.seal({key: item for key, item in value.items() if key != "sha256"})


def file_record(value):
    return prefix._record(prefix.canonical(value))


class ArchivedTokenTable:
    """Archived token lookup, not an actual tokenizer or native qualification."""

    chat_template = "EXPLICIT_SIMULATED_TEMPLATE"

    def __init__(self, imported, mapping=False):
        self.prompts, self.tokens, self.outputs = {}, {}, {}
        self.mapping = mapping
        for index in range(16):
            captures = imported["evidence"]["captures"]
            asked = prefix._json(captures[f"call_{index:04d}.request.json"])
            rendered = prefix._json(captures[f"call_{index:04d}.render.json"])
            raw = prefix._json(captures[f"call_{index:04d}.raw.json"])["raw"]
            self.prompts[prefix.digest(asked["request"]["messages"])] = rendered["rendered_prompt"]
            self.tokens[rendered["rendered_prompt"]] = rendered["prompt_token_ids"]
            self.outputs[tuple(raw["output_token_ids"])] = raw["text"]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = self.prompts[prefix.digest(messages)]
        if not tokenize:
            return text
        ids = self.encode(text)
        return UserDict({"input_ids": ids}) if self.mapping else ids

    def encode(self, text, add_special_tokens=False):
        return self.tokens[text]

    def decode(self, ids, skip_special_tokens=True):
        return self.outputs[tuple(ids)]


class PrefixImportTests(unittest.TestCase):
    def setUp(self):
        self.evidence, self.receipt, self.imported = copy.deepcopy(archived_fixture())

    def test_fixed_prefix_counts_and_original_failure_preserved(self):
        original = prefix.canonical(self.evidence)
        result = prefix.build_import(self.evidence, self.receipt, self.receipt["sha256"])
        self.assertEqual(result["selected_call_indices"], list(range(16)))
        self.assertEqual(result["selected_event_indices"], list(range(1, 16, 2)))
        self.assertEqual((len(result["rows"]), len(result["generations"]), len(result["queries"])), (8, 8, 14))
        self.assertEqual((result["original_status"], result["original_returncode"], result["original_calls"]), ("FORMATION_FAILED", 1, 17))
        self.assertEqual(result["new_model_calls"], 0)
        self.assertFalse(result["full_contract_released"])
        self.assertFalse(result["native_custody_verified"])
        self.assertEqual(prefix.canonical(self.evidence), original)
        self.assertEqual(prefix.validate_import(result, result["sha256"])["rows"], 8)

    def test_actual_e5_z_e7_b_not_ideal_edges(self):
        config = prefix._json(self.evidence["files"]["formation/formation_config.json"])
        root = prefix.core.from_data(config["planner"]["cell"]).root
        self.assertEqual(self.imported["rows"][5]["fields"]["source"], root.lookup("node", "Z"))
        self.assertEqual(self.imported["rows"][5]["fields"]["destination"], root.lookup("node", "Y"))
        self.assertEqual(self.imported["rows"][5]["fields"]["port"], root.lookup("port", "u"))
        self.assertEqual(self.imported["rows"][7]["fields"]["source"], root.lookup("node", "B"))
        self.assertEqual(self.imported["rows"][7]["fields"]["port"], root.lookup("port", "f1"))

    def test_all_targets_are_unmodified_child_spans_never_failed_link(self):
        raws = [generation["raw"] for generation in self.imported["generations"]]
        for raw in raws:
            self.assertTrue(raw.endswith("\n"))
            self.assertFalse(raw.endswith("\n\n"))
        for query in self.imported["queries"].values():
            self.assertTrue(all(line in raws for line in query["target"].splitlines(keepends=True)))
        self.assertEqual(sorted(len(query["support"]) for query in self.imported["queries"].values()), [1] * 12 + [2] * 2)
        self.assertEqual(prefix.digest(self.imported["queries"]), prefix.QUERIES_SHA256)
        self.assertIn("call_0016.raw.json", self.imported["evidence"]["captures"])

    def test_wrong_archive_rejected_before_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            wrong = Path(temporary) / "alternate.tar"
            wrong.write_bytes(b"not the fixed archive")
            with self.assertRaisesRegex(ValueError, "wrong original archive"):
                prefix.load_evidence(wrong)

    def test_original_path_version_and_receipt_type_drift_rejected(self):
        for key, value in (("source_root", "/tmp/relocated_v3"), ("formation_source_sha256", "0" * 64),
                           ("method", "CURRENT_SOURCE_REPLAY"), ("updates", False), ("model_calls", 1)):
            with self.subTest(key=key):
                receipt = reseal({**self.receipt, key: value})
                with self.assertRaises(ValueError):
                    prefix.build_import(self.evidence, receipt, receipt["sha256"])

    def test_missing_extra_capture_and_missing_source_rejected(self):
        for group, name, extra in (("captures", "call_0001.raw.json", False),
                                    ("captures", "call_0017.raw.json", True),
                                    ("sources", next(iter(self.evidence["sources"])), False)):
            with self.subTest(group=group, name=name):
                evidence = copy.deepcopy(self.evidence)
                if extra:
                    evidence[group][name] = file_record({})
                else:
                    evidence[group].pop(name)
                with self.assertRaises(ValueError):
                    prefix.build_import(evidence, self.receipt, self.receipt["sha256"])

    def test_changed_raw_lf_action_finish_or_timing_rejected(self):
        for index, mutation in ((1, lambda raw: raw["raw"].update(text=raw["raw"]["text"].rstrip("\n"))),
                                (0, lambda raw: raw["raw"].update(text="EXPLORE wrong\n")),
                                (1, lambda raw: raw["raw"].update(finish_reason="length")),
                                (1, lambda raw: raw.update(operation_started=0))):
            with self.subTest(index=index, mutation=mutation):
                evidence = copy.deepcopy(self.evidence)
                name = f"call_{index:04d}.raw.json"
                raw = prefix._json(evidence["captures"][name])
                mutation(raw)
                evidence["captures"][name] = file_record(raw)
                with self.assertRaises(ValueError):
                    prefix.build_import(evidence, self.receipt, self.receipt["sha256"])

    def test_forged_original_completion_rc0_or_bool_rc_rejected(self):
        for value in (0, True):
            evidence = copy.deepcopy(self.evidence)
            record = prefix._json(evidence["outer"]["worker_exit.json"])
            record["returncode"] = value
            evidence["outer"]["worker_exit.json"] = file_record(record)
            with self.assertRaises(ValueError):
                prefix.build_import(evidence, self.receipt, self.receipt["sha256"])
        receipt = copy.deepcopy(self.receipt)
        receipt["replay_result"]["status"] = "COMPLETE"
        receipt = reseal(receipt)
        with self.assertRaises(ValueError):
            prefix.build_import(self.evidence, receipt, receipt["sha256"])

    def test_resealing_cannot_substitute_rows_queries_selection_or_custody(self):
        mutations = [lambda item: item["rows"].pop(), lambda item: item["selected_call_indices"].append(16),
                     lambda item: item["selected_event_indices"].pop(),
                     lambda item: item.update(native_custody_verified=True),
                     lambda item: next(iter(item["queries"].values())).update(target="TEACHER\n")]
        for mutation in mutations:
            imported = copy.deepcopy(self.imported)
            mutation(imported)
            imported = reseal(imported)
            with self.assertRaises(ValueError):
                prefix.validate_import(imported, imported["sha256"])

    def test_source_byte_drift_and_duplicate_json_keys_rejected(self):
        name = next(iter(self.evidence["sources"]))
        self.evidence["sources"][name]["utf8"] += "\n"
        with self.assertRaises(ValueError):
            prefix.build_import(self.evidence, self.receipt, self.receipt["sha256"])
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            prefix._json(prefix._record(b'{"a":1,"a":2}'))

    def tokenizer_check(self, tokenizer):
        actual_hash = prefix.core.byte_hash
        expected = prefix._json(self.evidence["files"]["manifest.json"])["binding"]["tokenizer_receipt"]["chat_template_sha256"]
        with patch.object(writer, "verify_tokenizer_files") as files, patch.object(
                prefix.core, "byte_hash", side_effect=lambda text: expected if text == tokenizer.chat_template else actual_hash(text)):
            result = prefix.verify_tokenizer(self.imported, tokenizer)
            files.assert_called_once()
            return result

    def test_archived_table_checks_list_and_mapping_template_tokens(self):
        for mapping in (False, True):
            with self.subTest(mapping=mapping):
                result = self.tokenizer_check(ArchivedTokenTable(self.imported, mapping))
                self.assertEqual(result["calls_checked"], 16)
                self.assertFalse(result["full_contract_released"])

    def test_tokenizer_decode_lf_and_template_disagreement_fail(self):
        tokenizer = ArchivedTokenTable(self.imported)
        tokenizer.outputs = {key: text.rstrip("\n") for key, text in tokenizer.outputs.items()}
        with self.assertRaisesRegex(ValueError, "actual output token decode"):
            self.tokenizer_check(tokenizer)
        tokenizer = ArchivedTokenTable(self.imported)
        original = tokenizer.apply_chat_template
        tokenizer.apply_chat_template = lambda messages, tokenize, add_generation_prompt: [True] if tokenize else original(messages, tokenize, add_generation_prompt)
        with self.assertRaisesRegex(ValueError, "invalid token IDs"):
            self.tokenizer_check(tokenizer)

    def test_unqualified_tokenizer_never_gets_receipt(self):
        tokenizer = ArchivedTokenTable(self.imported)
        with patch.object(writer, "verify_tokenizer_files", side_effect=ValueError("missing tokenizer files")):
            with self.assertRaisesRegex(ValueError, "missing tokenizer files"):
                prefix.verify_tokenizer(self.imported, tokenizer)


if __name__ == "__main__":
    unittest.main()
