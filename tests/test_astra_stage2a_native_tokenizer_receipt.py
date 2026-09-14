"""Synthetic CPU interfaces only; no native tokenizer, model or qualification run."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_native_tokenizer_receipt as receipt
from tests.test_astra_stage2a_native_prepare import FakeTokenizer, MASTER, synthetic_bindings


def digest(raw):
    return sha256(raw).hexdigest()


def write_json(path, value):
    path.write_bytes(receipt._encode(value))


def fields_of(document):
    return dict(document["fields"])


class TokenizerReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / "source"
        cls.source.mkdir()
        cls.source_pins = {}
        for name, raw in (("organism_v6/composition_birth_stage2a_fixture.py", b"synthetic source"),
                          ("gpu/__init__.py", b""),
                          ("research_notes/analysis/stage2a_v6.md", b"synthetic v6"),
                          ("research_notes/analysis/stage2a_v2.md", b"synthetic v2")):
            path = cls.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            cls.source_pins[name] = digest(raw)
        cls.execution_pins = {name: value for name, value in cls.source_pins.items() if name.endswith(".md")}
        with patch.object(receipt.prepare.allocation, "allocate_stage2a", side_effect=AssertionError("no allocation")):
            cls.compiled = receipt.prepare.curriculum_api.compile_birth_curriculum(
                role_tokens_by_world={f"p{index:02d}": synthetic_bindings(index) for index in range(32)}, master=MASTER)
        worlds = MappingProxyType({pair.world: pair.role_tokens for pair in cls.compiled.pairs})
        custody = receipt._encode({"master": {"bytes_hex": MASTER.hex(), "sha256": digest(MASTER)},
                                   "label": "synthetic allocation, not authenticated source"})
        cls.allocation = receipt.prepare.allocation.Stage2AAllocation(
            MappingProxyType({}), MappingProxyType({}), (), MappingProxyType({}),
            MappingProxyType({"birth_train": worlds}), custody, digest(custody))
        cls.qualification = cls.root / "qualification"
        cls.separation = cls.root / "separation"
        for directory in (cls.qualification, cls.separation):
            directory.mkdir()
            (directory / "artifacts").mkdir()
            (directory / "artifacts" / digest(custody)).write_bytes(custody)
            write_json(directory / "SNAPSHOT.json", {"source_pins": cls.source_pins})
        write_json(cls.separation / "allocation.json", {"bytes_sha256": digest(custody), "length": len(custody)})
        manifest = {"source_pins": cls.source_pins, "master_hex": MASTER.hex()}
        write_json(cls.qualification / "manifest.json", {**manifest, "schema": receipt.QUALIFICATION_SCHEMA,
                   "kind": "CPU_FULL_POPULATION_NOT_NATIVE_READINESS"})
        write_json(cls.separation / "manifest.json", {**manifest, "kind": receipt.SEPARATION_KIND})
        counts = {"pairs": 32, "cases": 64, "units": 256, "arm_records": 512,
                  "paired_scoring_training_suite_exit_zero": 1, "integrity_tests": 17}
        counts.update(dict.fromkeys(("foreign_arm", "foreign_case", "foreign_master", "foreign_roles",
                                    "boundary_crossing", "caller_field_observations", "caller_candidate_inventory",
                                    "caller_typed_occurrence_receipts"), 512))
        counts.update({"boundary_injection_route_actions_" + name: 512 for name in ("literal", "spacing", "compact")})
        counts.update({"boundary_injection_route_" + name: 512 for name in ("ordered_ids", "event_rows", "mixed")})
        rows = []
        phases = Counter()
        for pair in cls.compiled.paired_targets:
            for record in (pair.closed, pair.atom_local):
                world = record.unit.unit_id.split("/")[0]
                record_digest = digest(receipt.prepare.canonical_json(receipt.source_inputs._digest_value(record)))
                provenance = receipt._encode({"record_sha256": record_digest, "display_master_sha256": digest(MASTER),
                    "role_tokens_sha256": digest(receipt.prepare.canonical_json(dict(worlds[world])))})
                boundary = receipt._encode({"world": world, "record_sha256": record_digest,
                    "unit_id": record.unit.unit_id, "arm": record.arm, "source_prefix_sha256": record.prefix_sha256,
                    "public_messages": [{"role": message.role, "content": message.content} for message in record.prefix],
                    "shared_custody_sha256": digest(b"synthetic shared"),
                    "source_provenance": {"bytes_hex": provenance.hex()}, "source_provenance_sha256": digest(provenance)})
                (cls.qualification / "artifacts" / digest(boundary)).write_bytes(boundary)
                artifacts = dict.fromkeys(("candidates", "retained", "routes", "private_static_basis",
                    "private_record_basis", "typed_receipts", "core", "checker", "checker_receipt", "foreign_master",
                    "foreign_roles"), digest(b"synthetic reference not replayed"))
                artifacts.update(boundary=digest(boundary), shared=digest(b"synthetic shared"))
                rows.append({"identity": record.unit.unit_id + "/" + record.arm, "status": "PASS", "artifacts": artifacts})
                phases[record.unit.phase + "/" + record.arm] += 1
        write_json(cls.qualification / "report.json", {"schema": receipt.QUALIFICATION_SCHEMA,
            "kind": "CPU_FULL_POPULATION_NOT_NATIVE_READINESS", "source_pins": cls.source_pins, "status": "PASS",
            "failures": [], "counts": counts, "commands": dict(cls.compiled.command_counts), "phases": dict(phases), "records": rows})
        separated_counts = {"birth_records": 512, "birth_units": 256, "intervention_members": 64,
            "chain_worlds": 16, "chain_members": 32, "chain_boundaries": 240, "held_records": 304,
            "checked_envelopes": 816, "core_collision_hashes": 0, "core_collision_pairs": 0,
            "signature_collision_hashes": 0, "signature_collision_pairs": 0}
        write_json(cls.separation / "report.json", {"kind": receipt.SEPARATION_KIND, "status": "SEPARATED",
            "source_pins": cls.source_pins, "counts": separated_counts,
            "core_collisions": {"tuple": []}, "signature_collisions": {"tuple": []}})
        cls.model_dir = cls.root / "model"
        cls.model_dir.mkdir()
        cls.backend = {"padding": None, "truncation": None, "added_tokens": [
            {"id": index, "content": text, "special": True} for index, text in
            ((0, "<|endoftext|>"), (1, "<|im_end|>"), (2, "<|im_start|>"))]}
        config = {"chat_template": "SYNTHETIC TEMPLATE, NOT NATIVE", "eos_token": "<|im_end|>",
                  "pad_token": "<|endoftext|>", "added_tokens_decoder":
                  {str(entry["id"]): {"content": entry["content"]} for entry in cls.backend["added_tokens"]}}
        for name in receipt.REQUIRED_FILES:
            write_json(cls.model_dir / name, config if name == "tokenizer_config.json" else
                       cls.backend if name == "tokenizer.json" else {})
        cls.official = cls.root / "official.json"
        write_json(cls.official, {"repository": receipt.REPOSITORY, "revision": receipt.REVISION,
            "status": "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING", "files":
            {name: {"sha256": digest((cls.model_dir / name).read_bytes()), "size": (cls.model_dir / name).stat().st_size}
             for name in receipt.REQUIRED_FILES}})

    def setUp(self):
        self.attempt_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.attempt_temp.cleanup)
        self.output = Path(self.attempt_temp.name) / "attempt"
        self.tokenizer = FakeTokenizer()
        self.tokenizer.name_or_path = str(self.model_dir)
        self.tokenizer.chat_template = "SYNTHETIC TEMPLATE, NOT NATIVE"
        self.tokenizer.is_fast = True
        self.tokenizer.backend_tokenizer = SimpleNamespace(to_str=lambda: json.dumps(self.backend))
        self.enterContext(patch.object(receipt, "ROOT", self.source))
        self.enterContext(patch.object(receipt, "EXECUTION_PINS", self.execution_pins))
        self.enterContext(patch.object(receipt, "OFFICIAL_RECEIPT_SHA256", digest(self.official.read_bytes())))

    def inputs(self):
        return dict(bound_allocation=self.allocation, compiled_curriculum=self.compiled, master=MASTER,
                    tokenizer=self.tokenizer, model_dir=self.model_dir, official_manifest=self.official,
                    loaded_files=receipt.REQUIRED_FILES, qualification_dir=self.qualification,
                    separation_dir=self.separation, output_dir=self.output,
                    separation_original_dir=getattr(self, "separation_original_dir", None))

    def change_json(self, path, mutate):
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        document = json.loads(original)
        mutate(document)
        write_json(path, document)

    def gate(self, attempt):
        return receipt._source_gates(attempt, self.qualification, self.separation,
                                     self.allocation, self.compiled, MASTER,
                                     getattr(self, "separation_original_dir", None))

    def binding(self, attempt):
        return receipt._tokenizer_binding(attempt, self.tokenizer, self.model_dir, self.official, receipt.REQUIRED_FILES)

    def install_recovery_fixture(self):
        from gpu import astra_stage2a_separation_replay as replay

        temporary = Path(self.attempt_temp.name)
        original = temporary / "original_separation"
        qualification = temporary / "qualification"
        shutil.copytree(self.separation, original)
        shutil.copytree(self.qualification, qualification)
        self.qualification = qualification
        self.separation = temporary / "replay"
        self.separation.mkdir()
        old_source = (b'BOUNDS = {"total_bytes": 512 * 1024 * 1024,}\n'
                      b'LIMIT = "aggregate supplied bytes <=512 MiB (counting repeats)"\n')
        self.enterContext(patch.object(replay, "ORIGINAL_SEPARATION_SHA256", digest(old_source)))
        old_files = {replay.SEPARATION_PATH: old_source, replay.SEPARATION_TEST_PATH: b"old separation tests"}
        current_files = {replay.SEPARATION_PATH: replay.capacity_repair(old_source),
                         replay.SEPARATION_TEST_PATH: b"new capacity-only separation tests",
                         replay.REPLAY_PATH: b"synthetic replay source pin",
                         replay.REPLAY_TEST_PATH: b"synthetic replay test pin"}
        old_pins = dict(self.source_pins)
        old_pins.update({name: digest(raw) for name, raw in old_files.items()})
        current_pins = dict(old_pins)
        for name, raw in current_files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.addCleanup(path.unlink)
            current_pins[name] = digest(raw)
        for directory in (original, qualification):
            for name in ("report.json", "manifest.json", "SNAPSHOT.json"):
                document = json.loads((directory / name).read_bytes())
                document["source_pins"] = old_pins
                write_json(directory / name, document)
            for name in old_pins:
                path = directory / "source" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(old_files[name] if name in old_files else (self.source / name).read_bytes())
        manifest = json.loads((original / "manifest.json").read_bytes())
        manifest.update(expected_birth_records=512, expected_intervention_members=64,
                        expected_chain_members=32, expected_chain_boundaries=240)
        write_json(original / "manifest.json", manifest)
        write_json(original / "report.json", {"kind": receipt.SEPARATION_KIND, "status": "ERROR",
            "error": "aggregate_byte_bound_exceeded", "native_authorized": False,
            "scientific_claims": False, "source_pins": old_pins})
        for name in replay.INDEX_NAMES:
            if name != "allocation.json":
                write_json(original / name, {"synthetic_index": name})
        recovery = replay.capture_recovery(original, current_pins)
        write_json(self.separation / "RECOVERY.json", recovery)
        write_json(self.separation / "SNAPSHOT.json", {"source_pins": current_pins})
        report = json.loads((type(self).separation / "report.json").read_bytes())
        report.update(kind=replay.KIND, source_pins=current_pins, original_files=recovery["original_files"],
                      snapshot_manifest_sha256=digest((self.separation / "SNAPSHOT.json").read_bytes()),
                      recovery_manifest_sha256=digest((self.separation / "RECOVERY.json").read_bytes()),
                      core_collisions=[], signature_collisions=[], retained_unique_blobs=1,
                      retained_unique_bytes=len(self.allocation.custody_bytes),
                      retained_blob_lengths={self.allocation.custody_sha256: len(self.allocation.custody_bytes)})
        write_json(self.separation / "report.json", report)
        return original, recovery

    def test_recovery_accepts_only_named_qualification_unused_capacity_dependencies(self):
        from gpu import astra_stage2a_separation_replay as replay

        original, recovery = self.install_recovery_fixture()
        with patch.object(replay, "capture_recovery", wraps=replay.capture_recovery) as capture, \
                patch.object(replay, "load_inputs", side_effect=AssertionError("no reconstruction/decoder")):
            result = self.gate(receipt._Attempt(self.output))
        capture.assert_called_once_with(original, recovery["source_pins"])
        self.assertEqual(set(result["qualification_dependency_dispositions"]), receipt.QUALIFICATION_UNUSED_SEPARATION_FILES)
        self.assertEqual(result["separation_status"], "SEPARATED")
        self.assertEqual(result["separation_artifacts_root"], str(original))
        self.assertEqual(json.loads((self.output / "original_separation_report.json").read_bytes())["status"], "ERROR")
        self.assertEqual(json.loads((self.output / "separation_report.json").read_bytes())["status"], "SEPARATED")
        self.assertFalse((self.separation / "manifest.json").exists())
        self.assertFalse((self.separation / "allocation.json").exists())

    def test_recovery_original_index_changed_is_rejected(self):
        original, unused_recovery = self.install_recovery_fixture()
        write_json(original / "birth_p00.json", {"changed": True})
        self.assert_rejected_before_tokenization("original_or_current_inputs_changed")

    def test_recovery_relocation_normalizes_only_original_root(self):
        original, recovery = self.install_recovery_fixture()
        raw = (self.separation / "RECOVERY.json").read_bytes()
        relocated = original.with_name("node2_copied_evidence")
        shutil.move(str(original), relocated)
        self.separation_original_dir = relocated
        result = self.gate(receipt._Attempt(self.output))
        self.assertFalse(original.exists())
        self.assertEqual(result["separation_recorded_original_root"], str(original))
        self.assertEqual(result["separation_artifacts_root"], str(relocated))
        self.assertEqual(result["separation_RECOVERY_sha256"], digest(raw))
        self.assertEqual((self.output / "separation_RECOVERY.json").read_bytes(), raw)
        self.assertEqual(json.loads((self.output / "recovery_recapture.json").read_bytes()), recovery)
        location = json.loads((self.output / "separation_location.json").read_bytes())
        self.assertEqual(location["recorded_original_root"], str(original))
        self.assertEqual(location["actual_original_root"], str(relocated))

    def test_recovery_relocation_cannot_normalize_other_fields(self):
        original, recovery = self.install_recovery_fixture()
        relocated = original.with_name("node2_copied_evidence")
        shutil.move(str(original), relocated)
        self.separation_original_dir = relocated
        recovery["constructors_rerun"] = True
        write_json(self.separation / "RECOVERY.json", recovery)
        self.change_json(self.separation / "report.json", lambda report: report.update(
            recovery_manifest_sha256=digest((self.separation / "RECOVERY.json").read_bytes())))
        self.assert_rejected_before_tokenization("original_or_current_inputs_changed")

    def test_recovery_relocation_cannot_change_original_source(self):
        original, unused_recovery = self.install_recovery_fixture()
        relocated = original.with_name("node2_copied_evidence")
        shutil.move(str(original), relocated)
        self.separation_original_dir = relocated
        (relocated / "source/organism_v6/composition_birth_stage2a_fixture.py").write_bytes(b"changed copied source")
        self.assert_rejected_before_tokenization("original_source_snapshot_changed")

    def test_recovery_changed_blob_cannot_hide_behind_report(self):
        original, unused_recovery = self.install_recovery_fixture()
        (original / "artifacts" / self.allocation.custody_sha256).write_bytes(b"changed")
        self.assert_rejected_before_tokenization("artifact_hash_mismatch")

    def test_recovery_report_cannot_use_old_snapshot_manifest_hash(self):
        self.install_recovery_fixture()
        self.change_json(self.separation / "report.json", lambda report: report.update(recovery_manifest_sha256="0" * 64))
        self.assert_rejected_before_tokenization("replay_manifest_binding_mismatch")

    def test_recovery_does_not_exempt_qualification_used_code(self):
        self.install_recovery_fixture()
        path = self.source / "organism_v6/composition_birth_stage2a_fixture.py"
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(b"changed qualification-used code")
        self.assert_rejected_before_tokenization("replay_source_hash_incompatible")

    def test_recovery_requires_exact_capacity_source_diff(self):
        from gpu import astra_stage2a_separation_replay as replay

        original, recovery = self.install_recovery_fixture()
        path = self.source / replay.SEPARATION_PATH
        path.write_bytes(path.read_bytes() + b"unrelated_semantic_change = True\n")
        recovery["source_pins"][replay.SEPARATION_PATH] = digest(path.read_bytes())
        write_json(self.separation / "RECOVERY.json", recovery)
        write_json(self.separation / "SNAPSHOT.json", {"source_pins": recovery["source_pins"]})
        self.change_json(self.separation / "report.json", lambda report: report.update(
            source_pins=recovery["source_pins"],
            recovery_manifest_sha256=digest((self.separation / "RECOVERY.json").read_bytes()),
            snapshot_manifest_sha256=digest((self.separation / "SNAPSHOT.json").read_bytes())))
        self.assert_rejected_before_tokenization("noncapacity_separation_change")

    def assert_rejected_before_tokenization(self, pattern):
        with patch.object(receipt.prepare, "prepare_birth", side_effect=AssertionError("must not tokenize")) as tokenize:
            with self.assertRaisesRegex(ValueError, pattern):
                receipt.prepare_tokenizer_receipt(**self.inputs())
            tokenize.assert_not_called()
        self.assertTrue((self.output / "failure.json").is_file())
        self.assertFalse((self.output / "receipt.json").exists())
        self.assertEqual(self.output.stat().st_mode & 0o222, 0)

    def test_complete_gates_consume_existing_artifacts_without_reconstruction(self):
        attempt = receipt._Attempt(self.output)
        with patch.object(receipt.prepare, "allocate_source", side_effect=AssertionError("no allocation")), \
                patch.object(receipt.prepare, "compile_source_curriculum", side_effect=AssertionError("no compile")), \
                patch.object(receipt.prepare.allocation, "verify_stage2a", side_effect=AssertionError("no costly replay")):
            result = self.gate(attempt)
        self.assertEqual(result["qualification_status"], "PASS")
        self.assertEqual(result["separation_status"], "SEPARATED")
        self.assertEqual(len(list(self.output.glob("source_boundary_*.json"))), 512)
        self.assertEqual((self.output / "qualification_report.json").read_bytes(), (self.qualification / "report.json").read_bytes())

    def test_terminal_separation_error_is_not_collision_or_pass(self):
        self.change_json(self.separation / "report.json", lambda report: report.update(
            status="ERROR", error="aggregate_byte_bound_exceeded"))
        self.assert_rejected_before_tokenization("separation_SEPARATED_required")
        report = json.loads((self.output / "separation_report.json").read_bytes())
        self.assertEqual(report["status"], "ERROR")
        self.assertEqual(report["error"], "aggregate_byte_bound_exceeded")

    def test_separation_PASS_is_not_SEPARATED(self):
        self.change_json(self.separation / "report.json", lambda report: report.update(status="PASS"))
        self.assert_rejected_before_tokenization("separation_SEPARATED_required")

    def test_qualification_failure_cannot_be_promoted(self):
        self.change_json(self.qualification / "report.json", lambda report: report.update(
            status="FAIL", failures=[{"error": "harness failure"}]))
        self.assert_rejected_before_tokenization("qualification_PASS_required")

    def test_green_flag_is_not_a_report(self):
        self.change_json(self.qualification / "report.json", lambda report: (report.clear(), report.update(status="PASS")))
        self.assert_rejected_before_tokenization("qualification_PASS_required")

    def test_missing_record_and_integrity_receipts_fail_closed(self):
        self.change_json(self.qualification / "report.json", lambda report: report["counts"].pop("integrity_tests"))
        self.assert_rejected_before_tokenization("population_or_integrity")

    def test_duplicate_record_identity_rejected(self):
        self.change_json(self.qualification / "report.json", lambda report: report["records"].__setitem__(0, report["records"][1]))
        self.assert_rejected_before_tokenization("512_qualification_rows")

    def test_missing_row_artifact_rejected(self):
        self.change_json(self.qualification / "report.json", lambda report: report["records"][0]["artifacts"].pop("checker"))
        self.assert_rejected_before_tokenization("incomplete_qualification_row")

    def test_wrong_master_rejected(self):
        self.change_json(self.separation / "manifest.json", lambda report: report.update(master_hex=b"different".hex()))
        self.assert_rejected_before_tokenization("source_gate_master_mismatch")

    def test_changed_source_rejected(self):
        path = self.source / "organism_v6/composition_birth_stage2a_fixture.py"
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(b"changed while another worker edits")
        self.assert_rejected_before_tokenization("source_hash_incompatible")

    def test_separation_counts_and_collision_objects_required(self):
        self.change_json(self.separation / "report.json", lambda report: report["counts"].update(chain_boundaries=239))
        self.assert_rejected_before_tokenization("incomplete_separation_population")

    def test_report_snapshot_disagreement_rejected(self):
        self.change_json(self.qualification / "SNAPSHOT.json", lambda report: report.update(source_pins={}))
        self.assert_rejected_before_tokenization("source_gate_pin_mismatch")

    def test_boundary_artifact_bytes_not_hash_alone(self):
        report = json.loads((self.qualification / "report.json").read_bytes())
        path = self.qualification / "artifacts" / report["records"][0]["artifacts"]["boundary"]
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(b"corrupt")
        self.assert_rejected_before_tokenization("artifact_hash_mismatch")

    def test_actual_prefix_bound_to_qualification_not_only_master(self):
        pair = self.compiled.paired_targets[0]
        record = pair.closed
        prefix = record.prefix[:-1] + (replace(record.prefix[-1], content=record.prefix[-1].content + "\n"),)
        changed = replace(record, prefix=prefix)
        pairs = (replace(pair, closed=changed),) + self.compiled.paired_targets[1:]
        self.compiled = replace(self.compiled, paired_targets=pairs)
        self.assert_rejected_before_tokenization("qualified_boundary_input_mismatch")

    def test_official_binding_without_executing_tokenizer(self):
        with patch.object(self.tokenizer, "encode", side_effect=AssertionError("not tokenization")), \
                patch.object(self.tokenizer, "decode", side_effect=AssertionError("not tokenization")), \
                patch.object(self.tokenizer, "apply_chat_template", side_effect=AssertionError("not tokenization")):
            result = self.binding(receipt._Attempt(self.output))
        self.assertEqual(set(result["files"]), set(receipt.REQUIRED_FILES))
        self.assertEqual((self.output / "loaded_chat_template.txt").read_text(), self.tokenizer.chat_template)

    def test_official_receipt_requires_pinned_bytes(self):
        with patch.object(receipt, "OFFICIAL_RECEIPT_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "manifest_authentication"):
                self.binding(receipt._Attempt(self.output))

    def test_changed_model_file_rejected(self):
        path = self.model_dir / "config.json"
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "official_file_mismatch:config"):
            self.binding(receipt._Attempt(self.output))

    def test_loaded_template_backend_path_and_specials_bound(self):
        changes = (("chat_template", "changed", "chat_template"),
                   ("name_or_path", str(self.root), "directory"),
                   ("eos_token_id", 1234, "special_id"),
                   ("padding_side", "left", "right_padding"),
                   ("backend_tokenizer", SimpleNamespace(to_str=lambda: "{}"), "backend_differs"))
        for index, (name, value, error) in enumerate(changes):
            with self.subTest(name=name), patch.object(self.tokenizer, name, value):
                with self.assertRaisesRegex(ValueError, error):
                    self.binding(receipt._Attempt(self.output.with_name(f"bad_binding_{index}")))

    def test_unmanifested_template_rejected(self):
        path = self.model_dir / "chat_template.jinja"
        path.write_text("foreign template")
        self.addCleanup(path.unlink)
        with self.assertRaisesRegex(ValueError, "undeclared_tokenizer_or_template"):
            self.binding(receipt._Attempt(self.output))

    def test_package_metadata_is_not_wheel_attestation(self):
        distribution = SimpleNamespace(version="synthetic-version", read_text=lambda name:
            "actual installed metadata text\n" if name in ("METADATA", "WHEEL", "RECORD") else None)
        with patch.object(receipt.metadata, "distribution", return_value=distribution):
            result = receipt._package_metadata(receipt._Attempt(self.output))
        for package in result["distributions"].values():
            self.assertEqual(package["version"], "synthetic-version")
            self.assertIsNone(package["wheel_archive_sha256"])
            self.assertEqual(package["metadata"]["WHEEL"]["sha256"], digest(b"actual installed metadata text\n"))
        self.assertEqual(result["wheel_attestation"], "NOT_PROVIDED")

    def test_missing_package_metadata_is_explicit(self):
        with patch.object(receipt.metadata, "distribution", side_effect=receipt.metadata.PackageNotFoundError):
            result = receipt._package_metadata(receipt._Attempt(self.output))
        self.assertTrue(all(not package["installed"] and package["version"] is None
                            for package in result["distributions"].values()))

    def test_fresh_immutable_output_and_budget_failures(self):
        self.output.mkdir()
        (self.output / "preserve").write_bytes(b"other worker")
        with self.assertRaises(FileExistsError):
            receipt.prepare_tokenizer_receipt(**self.inputs())
        self.assertEqual((self.output / "preserve").read_bytes(), b"other worker")
        attempt = receipt._Attempt(self.output.with_name("bounded"))
        with patch.object(receipt, "MAX_FILE_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "input_byte_bound"):
                attempt.read(self.official)
        with patch.object(receipt, "MAX_OUTPUT_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "output_byte_bound"):
                attempt.write("large", b"12345")
        self.assertFalse((attempt.path / "large").exists())

    def test_realistic_cumulative_budgets_keep_individual_file_bound(self):
        attempt = receipt._Attempt(self.output)
        attempt.read_bytes = 2 * 1024 * 1024 * 1024
        self.assertEqual(attempt.read(self.official), self.official.read_bytes())
        attempt.written_bytes = 1024 * 1024 * 1024
        attempt.write("past_old_output_cap", b"bounded additional artifact")
        self.assertEqual(receipt.MAX_INPUT_BYTES, 4 * 1024 * 1024 * 1024)
        self.assertEqual(receipt.MAX_OUTPUT_BYTES, 2 * 1024 * 1024 * 1024)
        oversized = Path(self.attempt_temp.name) / "oversized_sparse_input"
        with oversized.open("wb") as stream:
            stream.truncate(receipt.MAX_FILE_BYTES + 1)
        with self.assertRaisesRegex(ValueError, "input_byte_bound"):
            attempt.read(oversized)
        attempt.read_bytes = receipt.MAX_INPUT_BYTES
        with self.assertRaisesRegex(ValueError, "input_byte_bound"):
            attempt.read(self.official)

    def test_lossless_tagged_serialization_and_strict_json(self):
        value = MappingProxyType({("SEEK", 2): (b"\x00\xff\n", [True, None, 7])})
        encoded = receipt.retain(value)
        self.assertEqual(encoded["mapping"][0][0], {"tuple": ["SEEK", 2]})
        self.assertEqual(bytes.fromhex(encoded["mapping"][0][1]["tuple"][0]["bytes_hex"]), b"\x00\xff\n")
        for raw in (b'{"status":"FAIL","status":"PASS"}', b'{"count":NaN}'):
            with self.assertRaises(ValueError):
                receipt._json(raw)
        for value in (object(), float("inf")):
            with self.assertRaises(ValueError):
                receipt.retain(value)

    def test_all512_receipt_preserves_raw_tokens_masks_costs_and_status(self):
        original_root = Path(receipt.__file__).resolve().parents[1]
        original_gate = receipt._source_gates

        def gate(*args, **kwargs):
            with patch.object(receipt, "ROOT", self.source):
                result = original_gate(*args, **kwargs)
            return result

        read = receipt._Attempt.read

        def read_sources(attempt, path):
            relative = Path(path).relative_to(original_root) if Path(path).is_relative_to(original_root) else None
            if relative is not None and str(relative) in self.source_pins:
                path = self.source / relative
            return read(attempt, path)

        with patch.object(receipt, "ROOT", original_root), patch.object(receipt, "_source_gates", side_effect=gate), \
                patch.object(receipt._Attempt, "read", read_sources), \
                patch.object(receipt.metadata, "distribution", side_effect=receipt.metadata.PackageNotFoundError), \
                patch.object(receipt.prepare.allocation, "allocate_stage2a", side_effect=AssertionError("no allocation")), \
                patch.object(receipt.prepare, "prepare_birth", wraps=receipt.prepare.prepare_birth) as prepare_call:
            result = receipt.prepare_tokenizer_receipt(**self.inputs())
        self.assertEqual(prepare_call.call_args.kwargs["padding_policy"], "PER_ARM_MAX")
        report = json.loads((self.output / "receipt.json").read_bytes())
        self.assertEqual(result.receipt_sha256, digest((self.output / "receipt.json").read_bytes()))
        self.assertEqual(report["records"], 512)
        self.assertEqual(report["conditional_paired_batches"], 512)
        self.assertFalse(report["equal_total_compute_claimed"])
        self.assertFalse(report["native_execution_authorized"])
        self.assertEqual(report["count_basis"], receipt.prepare.COUNT_BASIS)
        self.assertEqual(report["executed_updates"], 0)
        self.assertEqual(len(result.prepared_birth.d1_atom_local_batches), 256)
        for index, pair in enumerate(result.prepared_birth.tokenized_pairs):
            rows = fields_of(json.loads((self.output / f"token_rows_{index:03d}.json").read_bytes()))
            for name, source in (("closed", pair.closed), ("atom_local", pair.atom_local)):
                row = fields_of(rows[name])
                self.assertEqual(row["input_ids"]["tuple"], list(source.input_ids))
                self.assertEqual(row["labels"]["tuple"], list(source.labels))
                self.assertEqual(row["attention_mask"]["tuple"], list(source.attention_mask))
                self.assertEqual(bytes.fromhex(row["sequence_roundtrip_bytes"]["bytes_hex"]), source.sequence_roundtrip_bytes)
                self.assertEqual(source.labels[source.target_start:source.target_end], source.target_ids)
                self.assertTrue(all(label == -100 for label in source.labels[:source.target_start]))
                self.assertTrue(all(label == -100 for label in source.labels[source.target_end:]))
        totals = {stage: {arm: Counter() for arm in receipt.ARMS} for stage in ("D1", "D2")}
        for batch in result.prepared_birth.batches:
            document = json.loads((self.output / f"batch_{batch.presentation.update_number:03d}.json").read_bytes())
            self.assertEqual(document["residuals_CLOSED_minus_ATOM_LOCAL"], dict(batch.residuals))
            for arm, source in (("CLOSED", batch.closed), ("ATOM_LOCAL", batch.atom_local)):
                saved = document["arms"][arm]
                self.assertEqual(saved["input_ids"], [list(row) for row in source.input_ids])
                self.assertEqual(saved["labels"], [list(row) for row in source.labels])
                self.assertEqual(saved["attention_mask"], [list(row) for row in source.attention_mask])
                self.assertEqual(saved["padding_length"], max(len(row.input_ids) for row in source.records))
                self.assertEqual(saved["accounting"], dict(source.accounting))
                totals[batch.presentation.stage][arm].update(saved["accounting"])
        self.assertEqual(report["accounting_by_stage"], totals)
        self.assertGreater(report["residuals_CLOSED_minus_ATOM_LOCAL"]["D1"]["total_sequence_tokens"], 0)
        for name, metadata in report["files"].items():
            self.assertEqual(digest((self.output / name).read_bytes()), metadata["sha256"])
            self.assertEqual((self.output / name).stat().st_mode & 0o222, 0)
        self.assertEqual(self.output.stat().st_mode & 0o222, 0)

    def test_import_has_no_model_cuda_network_or_tokenizer_execution(self):
        command = [sys.executable, "-B", "-c", "import sys; "
                   "from gpu import astra_stage2a_native_tokenizer_receipt; "
                   "assert not any(name.split('.')[0] in ('torch','transformers','tokenizers','peft','vllm') for name in sys.modules)"]
        subprocess.run(command, cwd=Path(receipt.__file__).resolve().parents[1], check=True)


if __name__ == "__main__":
    unittest.main()
