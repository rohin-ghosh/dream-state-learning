"""CPU-only regression fixtures for the standalone ancestry eligibility guard."""
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from organism_v6 import lineage_guard as guard


class LineageGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.base_manifest()
        self.base_binding = self.save("base.json", self.base)

    def save(self, path, value):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(value, sort_keys=True).encode() if isinstance(value, dict) else value
        destination.write_bytes(content)
        return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}

    def base_manifest(self):
        artifact = self.save("base.weights", b"fixture base bytes, not actual Qwen weights")
        artifact.update(role="base_model", exposure_status="UNEXPOSED", source_sha256=[])
        return {
            "schema_version": 1, "base_model": guard.BASE_MODEL, "kind": "fresh_base",
            "exposure_status": "UNEXPOSED", "parents": [], "sources": [],
            "artifacts": [artifact], "trained_corpus": [],
        }

    def child_manifest(self, parent=None, name="child"):
        source = self.save(f"{name}/event.json", {"event": "observed outcome"})
        source.update(role="environment_outcome", exposure_status="UNEXPOSED")
        corpus = self.save(f"{name}/corpus.jsonl", b'{"source": "observed outcome"}\n')
        corpus.update(exposure_status="UNEXPOSED", source_sha256=[source["sha256"]])
        artifact = self.save(f"{name}/adapter.bin", b"fixture adapter bytes")
        artifact.update(role="lora_adapter", exposure_status="UNEXPOSED",
                        source_sha256=[source["sha256"]])
        return {
            "schema_version": 1, "base_model": guard.BASE_MODEL, "kind": "descendant",
            "exposure_status": "UNEXPOSED",
            "parents": [dict(parent if parent is not None else self.base_binding)],
            "sources": [source], "artifacts": [artifact], "trained_corpus": [corpus],
        }

    def check(self, value, path="test.json"):
        self.save(path, value)
        return guard.validate_manifest(path, root=self.root)

    def reject(self, value, message=None):
        with self.assertRaisesRegex(guard.LineageGuardError, message or "."):
            self.check(value)

    def test_valid_fresh_base_and_pinned_entry(self):
        receipt = guard.validate_manifest("base.json", root=self.root,
                                          expected_sha256=self.base_binding["sha256"])
        self.assertTrue(receipt.eligible)
        self.assertEqual(receipt.exposure_status, "UNEXPOSED")
        self.assertEqual(len(receipt.manifests), 1)
        self.assertEqual(len(receipt.files), 1)
        self.assertIn("not factual entailment", receipt.scope)
        self.assertIn("automatic validity", receipt.scope)
        self.assertEqual(asdict(receipt)["manifest"], self.base_binding)

    def test_valid_child_all_supported_roles(self):
        for role in guard.SOURCE_ROLES:
            with self.subTest(role=role):
                child = self.child_manifest()
                child["sources"][0]["role"] = role
                receipt = self.check(child)
                self.assertTrue(receipt.eligible)
                self.assertEqual(len(receipt.manifests), 2)
                self.assertEqual(len(receipt.files), 4)

    def test_tainted_grandparent_cannot_be_laundered(self):
        self.base["exposure_status"] = "QUARANTINE_TASK_EXPOSED"
        tainted = self.save("base.json", self.base)
        parent = self.save("parent.json", self.child_manifest(tainted, "parent"))
        child = self.child_manifest(parent)
        child["trained_corpus"] = []
        self.reject(child, "forbidden ancestry")

    def test_unknown_and_tainted_status_at_every_level(self):
        for status in (None, "", "UNKNOWN", "CLEAN", "unexposed", False, {},
                       "DEV_UNVERIFIED_PROVENANCE", "QUARANTINE_TASK_EXPOSED"):
            for location in ("manifest", "sources", "artifacts", "trained_corpus"):
                with self.subTest(status=status, location=location):
                    child = self.child_manifest()
                    target = child if location == "manifest" else child[location][0]
                    target["exposure_status"] = status
                    self.reject(child)

    def test_missing_top_level_fields(self):
        for field in self.base:
            with self.subTest(field=field):
                value = dict(self.base)
                del value[field]
                self.reject(value, "missing or unknown fields")

    def test_empty_or_wrong_typed_required_fields(self):
        for field in self.base:
            for empty in (None, "", {}, False):
                with self.subTest(field=field, empty=empty):
                    value = dict(self.base)
                    value[field] = empty
                    self.reject(value)
        self.reject({})
        self.reject({**self.base, "schema_version": True})
        self.reject({**self.base, "artifacts": []})

    def test_missing_record_fields(self):
        for collection in ("parents", "sources", "artifacts", "trained_corpus"):
            template = self.child_manifest()
            for field in template[collection][0]:
                with self.subTest(collection=collection, field=field):
                    child = self.child_manifest()
                    del child[collection][0][field]
                    self.reject(child)

    def test_descendant_requires_parents_and_sources(self):
        for field in ("parents", "sources"):
            child = self.child_manifest()
            child[field] = []
            self.reject(child, "requires parents and supported sources")

    def test_fresh_birth_cannot_hide_training_or_ancestors(self):
        child = self.child_manifest()
        for field in ("parents", "sources", "trained_corpus", "artifacts"):
            with self.subTest(field=field):
                value = dict(self.base)
                value[field] = child[field]
                self.reject(value)

    def test_base_model_mismatch_and_unknown_kinds(self):
        for model in ("Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-7B", "other"):
            self.reject({**self.base, "base_model": model}, "base model mismatch")
        self.reject({**self.base, "kind": "unknown"}, "unknown birth kind")

    def test_invalid_and_mismatched_hash_at_every_level(self):
        for collection in ("parents", "sources", "artifacts", "trained_corpus"):
            for digest in ("", None, "x" * 64, "A" * 64, "0" * 63, "0" * 64):
                with self.subTest(collection=collection, digest=digest):
                    child = self.child_manifest()
                    child[collection][0]["sha256"] = digest
                    self.reject(child, "SHA256")
        with self.assertRaisesRegex(guard.LineageGuardError, "SHA256 mismatch"):
            guard.validate_manifest("base.json", root=self.root, expected_sha256="0" * 64)

    def test_missing_files_at_every_level(self):
        for collection in ("parents", "sources", "artifacts", "trained_corpus"):
            with self.subTest(collection=collection):
                child = self.child_manifest()
                child[collection][0]["path"] = "missing.file"
                self.reject(child)
        with self.assertRaises(guard.LineageGuardError):
            guard.validate_manifest("missing.json", root=self.root)

    def test_source_path_traversal_absolute_and_noncanonical(self):
        for path in ("../outside", "child/../../outside", "/etc/passwd", "./base.weights",
                     "child//event.json", "child/../base.weights", "", " ",
                     "child\\event.json", "\x00"):
            with self.subTest(path=path):
                child = self.child_manifest()
                child["sources"][0]["path"] = path
                self.reject(child)

    def test_source_file_and_directory_symlinks(self):
        for directory_link in (False, True):
            with self.subTest(directory_link=directory_link):
                child = self.child_manifest()
                name = "linked-directory" if directory_link else "linked-file"
                target = self.root / ("child" if directory_link else "child/event.json")
                (self.root / name).symlink_to(target, target_is_directory=directory_link)
                child["sources"][0]["path"] = f"{name}/event.json" if directory_link else name
                self.reject(child)

    def test_manifest_artifact_corpus_parent_and_root_symlinks(self):
        for collection in ("parents", "artifacts", "trained_corpus"):
            child = self.child_manifest()
            record = child[collection][0]
            name = f"{collection}-link"
            (self.root / name).symlink_to(self.root / record["path"])
            record["path"] = name
            self.reject(child)
        (self.root / "manifest-link").symlink_to(self.root / "base.json")
        (self.root / "root-link").symlink_to(self.root, target_is_directory=True)
        for path, root in (("manifest-link", self.root), ("base.json", self.root / "root-link")):
            with self.assertRaises(guard.LineageGuardError):
                guard.validate_manifest(path, root=root)

    def test_cyclic_lineage_detected_before_impossible_backedge_hash(self):
        parent = self.child_manifest({"path": "test.json", "sha256": "0" * 64}, "parent")
        binding = self.save("parent.json", parent)
        self.reject(self.child_manifest(binding), "cyclic lineage")
        self.reject(self.child_manifest({"path": "test.json", "sha256": "0" * 64}),
                    "cyclic lineage")

    def test_shared_ancestor_dag_is_not_a_cycle(self):
        left = self.save("left.json", self.child_manifest(name="left"))
        right = self.save("right.json", self.child_manifest(name="right"))
        child = self.child_manifest(left)
        child["parents"].append(right)
        self.assertEqual(len(self.check(child).manifests), 4)

    def test_nested_parent_paths_are_relative_to_bundle_root(self):
        parent = self.save("nested/parent.json", self.child_manifest(name="parent"))
        receipt = self.check(self.child_manifest(parent), "elsewhere/child.json")
        self.assertEqual(len(receipt.manifests), 3)

    def test_actual_file_tampering_rejected(self):
        for collection in ("parents", "sources", "artifacts", "trained_corpus"):
            with self.subTest(collection=collection):
                self.save("base.json", self.base)
                child = self.child_manifest()
                self.save(child[collection][0]["path"], b"changed after binding")
                self.reject(child, "SHA256 mismatch")

    def test_unknown_status_and_tainted_nonweight_ancestor(self):
        for status in ("UNKNOWN", "QUARANTINE_TASK_EXPOSED"):
            for role in ("memory", "parent_notes", "ranking", "selection_decision"):
                with self.subTest(status=status, role=role):
                    parent = self.child_manifest(name="parent")
                    parent["artifacts"][0]["role"] = role
                    parent["artifacts"][0]["exposure_status"] = status
                    binding = self.save("parent.json", parent)
                    self.reject(self.child_manifest(binding))

    def test_resource_limits_fail_closed(self):
        for limit in ("MAX_DEPTH", "MAX_MANIFESTS", "MAX_RECORDS", "MAX_MANIFEST_BYTES"):
            with self.subTest(limit=limit), mock.patch.object(guard, limit, 1):
                self.reject(self.child_manifest())

    def test_duplicate_parents_and_source_references_rejected(self):
        child = self.child_manifest()
        child["parents"].append(dict(child["parents"][0]))
        self.reject(child, "duplicate parent")
        child = self.child_manifest()
        child["artifacts"][0]["source_sha256"] *= 2
        self.reject(child, "duplicate source hash")

    def test_validation_is_read_only(self):
        self.save("child.json", self.child_manifest())
        before = {path.relative_to(self.root): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        guard.validate_manifest("child.json", root=self.root)
        after = {path.relative_to(self.root): path.read_bytes()
                 for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_blocked_families_even_with_unexposed_declaration(self):
        for name in ("bootstrap_v1", "bootstrap_v2", "bootstrap_v3", "CompilerGym",
                     "compiler_gym", "BOOTSTRAP-V3", "R2_B_seed3"):
            with self.subTest(name=name):
                child = self.child_manifest()
                record = child["sources"][0]
                record.update(self.save(f"{name}/source.txt", b"source fixture"))
                self.reject(child, "forbidden ancestry")
                grandparent = self.save(f"{name}/manifest.json", self.base)
                parent = self.save("parent.json", self.child_manifest(grandparent, "parent"))
                self.reject(self.child_manifest(parent), "forbidden ancestry")

    def test_unknown_fields_roles_and_unbound_sources(self):
        self.reject({**self.base, "clean": True}, "missing or unknown fields")
        for collection in ("sources", "artifacts"):
            child = self.child_manifest()
            child[collection][0]["role"] = "synthetic_unsourced"
            self.reject(child, "unsupported .* role")
        for references in ([], ["0" * 64], "not a list", [None]):
            child = self.child_manifest()
            child["artifacts"][0]["source_sha256"] = references
            self.reject(child)

    def test_forbidden_bundle_directory_does_not_hide_ancestry(self):
        self.save("CompilerGym/base.json", self.base)
        with self.assertRaisesRegex(guard.LineageGuardError, "forbidden ancestry"):
            guard.validate_manifest("base.json", root=self.root / "CompilerGym")

    def test_empty_files_directory_and_fifo_rejected(self):
        child = self.child_manifest()
        child["sources"][0].update(self.save("empty.txt", b""))
        self.reject(child, "empty file")
        child = self.child_manifest()
        child["sources"][0]["path"] = "child"
        self.reject(child)
        os.mkfifo(self.root / "fifo")
        child["sources"][0]["path"] = "fifo"
        self.reject(child, "not a regular file")

    def test_malformed_duplicate_key_and_nonstandard_json(self):
        for content in (b"{", b"[]", b"null", b'{}{}', b'\xff',
                        b'{"schema_version":1,"schema_version":1}',
                        b'{"schema_version":NaN}'):
            with self.subTest(content=content):
                self.save("invalid.json", content)
                with self.assertRaises(guard.LineageGuardError):
                    guard.validate_manifest("invalid.json", root=self.root)

    def test_clean_filename_alone_is_not_evidence(self):
        self.save("verified_clean.json", {"clean": True, "base_model": guard.BASE_MODEL})
        with self.assertRaises(guard.LineageGuardError):
            guard.validate_manifest("verified_clean.json", root=self.root)

    def test_cli_success_and_failure(self):
        for manifest, expected in (("base.json", 0), ("absent.json", 1)):
            output = io.StringIO()
            with redirect_stdout(output):
                code = guard.main(["--root", str(self.root), manifest])
            value = json.loads(output.getvalue())
            self.assertEqual(code, expected)
            self.assertEqual(value["eligible"], expected == 0)
            self.assertIn("scope", value)
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "organism_v6.lineage_guard", "--root",
             str(self.root), "base.json"], capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["eligible"])


if __name__ == "__main__":
    unittest.main()
