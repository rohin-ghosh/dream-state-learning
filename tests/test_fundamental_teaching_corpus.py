"""CPU-only invariants for the fixed candidate; no native-token claims."""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import fundamental_teaching_corpus as corpus


class FundamentalTeachingCorpusTests(unittest.TestCase):
    def setUp(self):
        self.candidate = corpus.build_candidate()
        self.teach = self.candidate["train_teach"]
        self.control = self.candidate["train_control"]
        self.evaluation = self.candidate["eval"]
        self.sources = {row["id"]: row for row in self.candidate["source_records"]}

    def test_counts_ids_and_fixed_split(self):
        self.assertEqual(len(self.teach), 80)
        self.assertEqual(len(self.control), 80)
        self.assertEqual(Counter(row["kind"] for row in self.evaluation),
                         dict(addition=64, memory_recall=32, memory_unknown=16))
        rows = self.teach + self.control + self.evaluation
        self.assertEqual(len({row["id"] for row in rows}), 272)
        self.assertEqual(len(self.sources), 145)
        pairs = [(left, right) for left in range(20) for right in range(left, 20)]
        random.Random(20260912).shuffle(pairs)
        split_pairs = []
        for records, expected in ((self.teach, pairs[:64]), (self.evaluation, pairs[64:128])):
            actual = set()
            for row in records:
                if row["kind"] == "addition":
                    event = self.sources[row["source_event_ids"][0]]
                    self.assertTrue(0 <= event["left"] <= event["right"] <= 19)
                    actual.add((event["left"], event["right"]))
            self.assertEqual(actual, set(expected))
            self.assertEqual(len(actual), 64)
            split_pairs.append(actual)
        self.assertFalse(split_pairs[0] & split_pairs[1])
        self.assertFalse(split_pairs[0] & {(right, left) for left, right in split_pairs[1]})

    def test_truth_target_order_and_equal_semantic_facts(self):
        facts = {"teach": [], "control": []}
        for teach, control in zip(self.teach, self.control):
            for field in ("context", "case_id", "kind", "source_event_ids"):
                self.assertEqual(teach[field], control[field])
            event = self.sources[teach["source_event_ids"][0]]
            for arm, row in (("teach", teach), ("control", control)):
                if row["kind"] == "addition":
                    labels = ["PREDICT", "ACT"] if arm == "teach" else ["ACT", "RESULT"]
                    total = event["left"] + event["right"]
                    self.assertEqual(event["sum"], total)
                    self.assertEqual(row["response"], "\n".join(f"{label}: {total}" for label in labels))
                    facts[arm].append((event["id"], total))
                else:
                    self.assertEqual(row["response"], event["color"])
                    facts[arm].append((event["id"], row["response"]))
        self.assertEqual(facts["teach"], facts["control"])
        for row in self.evaluation:
            if row["kind"] == "addition":
                event = self.sources[row["source_event_ids"][0]]
                self.assertEqual(row["expected"], event["left"] + event["right"])

    def test_memory_sources_paraphrases_and_unknowns(self):
        taught = {event["device"]: event for event in self.sources.values()
                  if event["kind"] == "device_color"}
        self.assertEqual(Counter(event["color"] for event in taught.values()),
                         dict.fromkeys(corpus.COLORS, 4))
        self.assertEqual(set(self.sources["source-log-inventory"]["device_ids"]), set(taught))
        recall_counts, unknown_devices = Counter(), set()
        train_questions = {row["context"] for row in self.teach}
        memory_questions = set()
        for row in self.evaluation:
            if row["kind"] == "addition":
                continue
            self.assertNotIn(row["context"], train_questions)
            self.assertNotIn(row["context"], memory_questions)
            memory_questions.add(row["context"])
            if row["kind"] == "memory_recall":
                self.assertEqual(row["expected"], taught[row["device"]]["color"])
                self.assertEqual(row["source_event_ids"], [taught[row["device"]]["id"]])
                recall_counts[row["device"]] += 1
            else:
                self.assertNotIn(row["device"], taught)
                self.assertEqual(row["expected"], "unknown")
                self.assertEqual(row["source_event_ids"], ["source-log-inventory"])
                unknown_devices.add(row["device"])
        self.assertEqual(recall_counts, dict.fromkeys(taught, 2))
        self.assertEqual(len(unknown_devices), 16)

    def test_every_target_has_auditable_source_derivation(self):
        audit = self.candidate["audit"]
        self.assertEqual(audit["source_events"], self.candidate["source_records"])
        derived = {row["record_id"]: row for row in audit["target_derivations"]}
        all_rows = self.teach + self.control + self.evaluation
        self.assertEqual(len(derived), len(all_rows))
        for row in all_rows:
            derivation = derived[row["id"]]
            self.assertEqual(derivation["source_event_ids"], row["source_event_ids"])
            self.assertEqual(derivation["target"], row.get("response", row.get("expected")))
            self.assertTrue(derivation["rule"])
            self.assertTrue(all(source in self.sources for source in row["source_event_ids"]))
        example = audit["protocol_example"]
        self.assertEqual(example["left"] + example["right"], example["sum"])
        self.assertFalse(example["emitted_case"])

    def test_evaluation_has_no_teacher_or_prompt_residue(self):
        train_contexts = {row["context"] for row in self.teach}
        for row in self.evaluation:
            self.assertNotIn(row["context"], train_contexts)
            self.assertNotIn("response", row)
            self.assertNotIn("segments", row)
            for residue in ("predict", "result", "reflect", "before", "after", "teacher",
                            "example", "protocol", "source-", *corpus.COLORS):
                self.assertNotIn(residue, row["context"].lower())
            if row["kind"] == "addition":
                event = self.sources[row["source_event_ids"][0]]
                self.assertEqual(row["context"], corpus.addition_context(event["left"], event["right"]))
            else:
                self.assertIn(row["context"], [template.format(device=row["device"])
                                               for template in corpus.MEMORY_QUESTIONS])

    def test_pending_native_audit_and_pure_segments(self):
        manifest = self.candidate["manifest"]
        self.assertEqual(manifest["status"], "CANDIDATE_CPU_ONLY")
        self.assertEqual(manifest["native_token_match"], "NATIVE_TOKEN_MATCH_PENDING")
        self.assertEqual(manifest["result_label_variants"], ["RESULT", "COMPUTED_RESULT", "RESULT_SUM"])
        self.assertTrue(all(not value for value in manifest["boundary"].values()))
        for row in self.teach + self.control:
            self.assertEqual(corpus.raw_segments(row), ((row["context"], False), (row["response"], True)))
        row = dict(context="  raw context\n\n", response=" target \n")
        self.assertEqual(corpus.raw_segments(row), (("  raw context\n\n", False), (" target \n", True)))
        for label in corpus.RESULT_LABEL_VARIANTS:
            self.assertEqual(corpus.arithmetic_response(7, 9, "control", label), f"ACT: 16\n{label}: 16")
        with self.assertRaises(ValueError):
            corpus.arithmetic_response(7, 9, "other")
        with self.assertRaises(ValueError):
            corpus.arithmetic_response(7, 9, "control", "PREDICT")

    def test_byte_determinism_hashes_and_rng_isolation(self):
        state = random.getstate()
        expected = corpus.candidate_files()
        self.assertEqual(corpus.candidate_files(), expected)
        self.assertEqual(random.getstate(), state)
        manifest = json.loads(expected["manifest.json"])
        self.assertEqual(set(manifest["sha256"]), set(expected) - {"manifest.json"})
        for name, digest in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256(expected[name]).hexdigest(), digest)
        with tempfile.TemporaryDirectory() as root:
            for name in ("one", "two"):
                output = Path(root) / name
                corpus.emit_candidate(output)
                self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, expected)

    def test_refuses_existing_directory_file_and_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            directory = root / "existing"
            directory.mkdir()
            marker = directory / "untouched"
            marker.write_bytes(b"keep me")
            regular = root / "regular"
            regular.write_bytes(b"original")
            link = root / "link"
            link.symlink_to(directory, target_is_directory=True)
            dangling = root / "dangling"
            dangling.symlink_to(root / "absent", target_is_directory=True)
            for path in (directory, regular, link, dangling):
                with self.assertRaises(FileExistsError):
                    corpus.emit_candidate(path)
            empty = root / "empty"
            empty.mkdir()
            with self.assertRaises(FileExistsError):
                corpus.emit_candidate(empty)
            self.assertEqual(marker.read_bytes(), b"keep me")
            self.assertEqual(regular.read_bytes(), b"original")
            self.assertFalse((root / "absent").exists())

    def test_exclusive_file_writes_preserve_collision(self):
        original_open = Path.open
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "candidate"

            def collide(path, mode="r", *args, **kwargs):
                self.assertEqual(mode, "xb")
                with original_open(path, "wb") as stream:
                    stream.write(b"concurrent writer")
                return original_open(path, mode, *args, **kwargs)

            with patch.object(Path, "open", collide):
                with self.assertRaises(FileExistsError):
                    corpus.emit_candidate(output)
            self.assertEqual((output / "train_teach.json").read_bytes(), b"concurrent writer")

    def test_cli_matches_pure_bytes_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "candidate"
            command = [sys.executable, "-B", "-m", "organism_v6.fundamental_teaching_corpus",
                       "--output", str(output)]
            environment = dict(os.environ, PYTHONHASHSEED="71", PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run(command, capture_output=True, text=True, check=True,
                                    cwd=Path(corpus.__file__).resolve().parents[1], env=environment)
            self.assertEqual(json.loads(result.stdout)["status"], corpus.STATUS)
            expected = corpus.candidate_files()
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, expected)
            result = subprocess.run(command, capture_output=True, text=True,
                                    cwd=Path(corpus.__file__).resolve().parents[1], env=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FileExistsError", result.stderr)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, expected)

    def test_implementation_imports_only_small_standard_library_allowlist(self):
        tree = ast.parse(Path(corpus.__file__).read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        self.assertEqual(set(imports), {"__future__", "argparse", "hashlib", "json", "pathlib", "random"})


if __name__ == "__main__":
    unittest.main()
