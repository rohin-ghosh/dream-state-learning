"""Tiny synthetic receipt fixtures ONLY; no native evidence or model/tokenizer calls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_analyze as audit


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audit.canonical(value) + b"\n")


def checksum(root, name):
    return audit.driver._file_hash(root / name)


class SyntheticReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_C0_ANALYZER_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        root = audit.core.build_root("excluded/0")
        self.cell = audit.core.WorldCell(root, 0, 0, 0)
        self.rows = audit.core.ideal_rows(self.cell)
        self.task = {"id": "SYNTHETIC_TINY/delayed/ACTIVE_LINKED_TEXT", "panel": "delayed",
                     "cell": audit.core.to_data(self.cell), "goal": 0, "projection": "ACTIVE_LINKED_TEXT",
                     "seed": 7, "public": {"system": "SYNTHETIC SYSTEM", "user": "SYNTHETIC TASK"},
                     "queries": audit.core.materialize_queries(self.rows)}
        self.answer = audit.core.oracle_route_v1(self.cell, 0)

    def fixture(self, outputs, *, finish="stop", service_count=2):
        messages = [{"role": "system", "content": self.task["public"]["system"]},
                    {"role": "user", "content": self.task["public"]["user"]}]
        actor_tokens = returned_tokens = counts = 0
        measurements = []
        for turn, text in enumerate(outputs):
            request = {"id": f"{audit.core.byte_hash(self.task['id'])}/actor/{turn}", "messages": copy.deepcopy(messages), "seed": 7, "mount": "C0"}
            prompt = "SYNTHETIC_RENDER " + audit.canonical(messages).decode()
            prompt_ids = [11, 12, 13]
            if turn == 0:
                measurements.append({"id": "initial/" + self.task["id"], "text": prompt, "token_ids": prompt_ids})
            limits = {"output_tokens": 2048 - actor_tokens, "returned_tokens": 4096 - returned_tokens,
                      "remaining_reads": 12 - turn, "input_tokens": 3, "deadline": 100, "device_seconds": 10}
            name = f"call_{turn:04}"
            response = {"request_sha256": audit.digest(request), "text": text, "prompt_tokens": 3, "output_tokens": 1, "device_seconds": 1}
            write(self.root, name + "_request.json", {"request": request, "request_sha256": audit.digest(request), "render_sha256": audit.core.byte_hash(prompt), "input_token_ids": prompt_ids, "limits": limits, "response": None})
            write(self.root, name + "_response.json", response)
            write(self.root, "actor/" + name + ".request.json", {"request": request, "limits": limits, "request_sha256": audit.digest(request), "started": turn + 1})
            write(self.root, "actor/" + name + ".render.json", {"rendered_prompt": prompt, "prompt_token_ids": prompt_ids, "sampling": {**audit.native.SAMPLING, "seed": 7, "max_tokens": limits["output_tokens"]}, "mount": "C0", "lora_request": None})
            write(self.root, "actor/" + name + ".raw.json", {"kind": "NATIVE", "request_sha256": audit.digest(request), "raw": {"text": text, "prompt_token_ids": prompt_ids, "output_token_ids": [17], "finish_reason": finish, "stop_reason": None}, "operation_started": turn + 1, "generation_started": turn + 1, "generation_ended": turn + 1.5, "mount": "C0", "lora_request": None})
            write(self.root, "actor/" + name + ".response.json", {"response": response, "raw_utf8_sha256": audit.core.byte_hash(text), "raw_hex": text.encode().hex(), "decoded": text})
            actor_tokens += 1
            if not text.startswith("READ ") or self.task["projection"] != "ACTIVE_LINKED_TEXT" or turn == 12:
                continue
            try:
                lookup = audit.core.read_query(self.task["queries"], text)
            except ValueError:
                continue
            block = lookup["raw"]
            ids = [29] * service_count
            measurements.append({"id": f"block/synthetic/{turn}", "text": block, "token_ids": ids})
            write(self.root, f"actor/count_{counts:04}.json", {"text": block, "sha256": audit.core.byte_hash(block), "token_ids": ids})
            counts += 1
            if returned_tokens + service_count <= 4096:
                returned_tokens += service_count
                messages.extend([{"role": "assistant", "content": text}, {"role": "user", "content": block}])
        self.manifest = {"measurements": {"measurements": measurements}, "actor": {"max_input_tokens": 8192, "deadline": 100}}
        return audit.Replay(audit.Archive(self.root), self.manifest)

    def mutate(self, name, update):
        value = json.loads((self.root / name).read_bytes())
        update(value)
        write(self.root, name, value)
        return audit.Replay(audit.Archive(self.root), self.manifest)

    def test_valid_raw_route_reuses_frozen_scorer(self):
        replay = self.fixture([self.answer])
        row = replay._task(self.task)
        self.assertTrue(row["success"])
        self.assertEqual(row["score"], audit.core.score_route(self.cell, 0, self.answer))
        self.assertEqual((replay.calls, row["actor_tokens"], row["returned_tokens"]), (1, 1, 0))

    def test_length_stop_does_not_invent_scoring_penalty(self):
        replay = self.fixture([self.answer], finish="length")
        self.assertTrue(replay._task(self.task)["success"])
        self.assertEqual(replay.stats["truncated_calls"], 1)

    def test_negative_is_scored_not_repaired(self):
        replay = self.fixture(["not a route"])
        row = replay._task(self.task)
        self.assertFalse(row["success"])
        self.assertFalse(row["score"]["strict"])
        self.assertEqual(replay.calls, 1)

    def test_exact_read_transcript_and_usage(self):
        request = next(iter(self.task["queries"]))
        replay = self.fixture([request, self.answer])
        row = replay._task(self.task)
        self.assertTrue(row["success"])
        self.assertEqual(row["reads"], [audit.core.read_query(self.task["queries"], request)])
        self.assertEqual((replay.calls, replay.counts, row["returned_tokens"]), (2, 1, 2))

    def test_miss_service_is_a_real_read(self):
        request = "READ EVENT " + audit.core.build_root("excluded/1").lookup("event", "e0")
        replay = self.fixture([request, self.answer])
        row = replay._task(self.task)
        self.assertEqual(row["reads"][0]["raw"], "MISS")
        self.assertEqual(replay.counts, 1)

    def test_invalid_read_and_thirteenth_read_preserved(self):
        replay = self.fixture(["READ nonsense"])
        self.assertTrue(replay._task(self.task)["invalid_read"])
        request = next(iter(self.task["queries"]))
        replay = self.fixture([request] * 13)
        row = replay._task(self.task)
        self.assertFalse(row["success"])
        self.assertTrue(row["invalid_read"])
        self.assertEqual((len(row["reads"]), replay.calls, replay.counts), (12, 13, 12))

    def test_return_overflow_preserves_invalid_not_served_count(self):
        replay = self.fixture([next(iter(self.task["queries"]))], service_count=4097)
        row = replay._task(self.task)
        self.assertTrue(row["invalid_read"])
        self.assertEqual((row["returned_tokens"], len(row["reads"]), replay.counts), (0, 0, 1))

    def test_wrong_root_false_row_uses_memory_scorer(self):
        self.task["projection"] = "WRONG_ROOT"
        text = self.rows[0]["raw"]
        row = self.fixture([text])._task(self.task)
        self.assertTrue(row["usable_false_row"])
        self.assertFalse(row["success"])

    def test_reachout_uses_exact_probe_parser(self):
        self.task["panel"] = "reachout"
        text = "PROBE " + self.cell.root.lookup("probe", "relevant")
        self.assertTrue(self.fixture([text])._task(self.task)["success"])
        self.assertFalse(self.fixture([text + " extra"])._task(self.task)["success"])

    def test_receipt_corruptions_rejected_even_if_archive_rehashed(self):
        changes = [
            ("call_0000_request.json", lambda value: value["request"].update(seed=8)),
            ("call_0000_request.json", lambda value: value["limits"].update(output_tokens=2047)),
            ("call_0000_request.json", lambda value: value.update(request_sha256="0" * 64)),
            ("call_0000_response.json", lambda value: value.update(text="different")),
            ("call_0000_response.json", lambda value: value.update(output_tokens=True)),
            ("actor/call_0000.render.json", lambda value: value.update(lora_request={})),
            ("actor/call_0000.render.json", lambda value: value["sampling"].update(temperature=0.1)),
            ("actor/call_0000.render.json", lambda value: value.update(rendered_prompt="different")),
            ("actor/call_0000.raw.json", lambda value: value["raw"].update(output_token_ids=[True])),
            ("actor/call_0000.raw.json", lambda value: value.update(generation_ended=200)),
            ("actor/call_0000.response.json", lambda value: value.update(raw_hex="ff")),
        ]
        for name, update in changes:
            with self.subTest(name=name):
                self.fixture([self.answer])
                with self.assertRaises(ValueError):
                    self.mutate(name, update)._task(self.task)

    def test_read_count_receipt_mismatch_rejected(self):
        self.fixture([next(iter(self.task["queries"])), self.answer])
        replay = self.mutate("actor/count_0000.json", lambda value: value.update(token_ids=[5]))
        with self.assertRaisesRegex(ValueError, "READ token receipt"):
            replay._task(self.task)

    def test_archive_change_missing_receipt_and_symlink_rejected(self):
        replay = self.fixture([self.answer])
        write(self.root, "call_0000_response.json", {})
        with self.assertRaisesRegex(ValueError, "archive changed"):
            replay._task(self.task)
        self.fixture([self.answer])
        (self.root / "actor/call_0000.raw.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing archived file"):
            audit.Replay(audit.Archive(self.root), self.manifest)._task(self.task)
        (self.root / "alias").symlink_to(self.root / "call_0000_request.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            audit.Archive(self.root)

    def test_duplicate_keys_and_nan_rejected(self):
        for text in ('{"key":1,"key":2}', '{"key":NaN}'):
            (self.root / "bad.json").write_text(text)
            with self.assertRaises(ValueError):
                audit.Archive(self.root).read("bad.json")


class SyntheticLineageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_C0_LINEAGE_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data, self.outer = self.root / "data", self.root / "outer"
        self.data.mkdir()
        self.outer.mkdir()
        manifest = audit.driver._seal({"schema": audit.driver.SCHEMA, "output_dir": "/SYNTHETIC_ORIGINAL/output", "wall_seconds": 100, "device_seconds": 100, "test_only": False, "fits": 0, "updates": 0, "full_v22_release": False, "plan": {"roots": []}})
        report = audit.driver._seal({"gpu_uuid": "GPU-SYNTHETIC", "started_monotonic": 10, "wall_seconds_through_close": 5})
        write(self.data, "manifest.json", manifest)
        write(self.data, "report.json", report)
        self.manifest_hash = checksum(self.data, "manifest.json")
        write(self.outer, "context.json", {"manifest_file_sha256": self.manifest_hash, "output_dir": manifest["output_dir"], "entry_monotonic": 9, "deadline_monotonic": 100})
        write(self.outer, "worker_exit.json", {"returncode": 0})
        write(self.outer, "worker_wait.json", {"value": 0})
        write(self.outer, "worker_release.json", {"owned_group_released": True})
        write(self.outer, "final_gpu.json", {"value": {"empty": True}})
        write(self.outer, "final_queue.json", {"value": {"matched": True}})
        write(self.outer, "final_cvd.json", {"value": {"clear": True, "owners": []}})
        write(self.outer, "final_cvd_after_gpu.json", {"value": {"clear": True, "owners": [], "reservation_check_status": "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS", "complete_cvd_visibility": False, "approved_unreadable_services": [{"pid": 123}]}})
        inventory = audit.Archive(self.data).inventory
        capture = {"schema": audit.OUTER + "/captured", "status": "CAPTURED_AWAITING_RESERVATION_RELEASE", "finalized": False, "fits": 0, "updates": 0, "worker_group_released": True, "gpu_compute_vacant": True, "manifest_sha256": manifest["sha256"], "report_sha256": report["sha256"], "report_file_sha256": inventory["report.json"]["sha256"], "output_inventory": inventory, "outer_files": {name: entry["sha256"] for name, entry in audit.Archive(self.outer).inventory.items()}}
        write(self.outer, "capture_complete.json", capture)
        attestation = {"report_sha256": report["sha256"], "gpu_uuid": report["gpu_uuid"], "owned_group_released": True, "gpu_vacant": True, "elapsed_seconds_from_start": 10}
        write(self.outer, "release_attestation.json", attestation)
        receipt = {**attestation, "evidence_path": "/SYNTHETIC_ORIGINAL/outer/release_attestation.json", "evidence_sha256": checksum(self.outer, "release_attestation.json")}
        write(self.outer, "release_receipt.json", receipt)
        final = audit.driver._seal({"schema": audit.driver.SCHEMA + "/final", "report": report, "outer_release": receipt, "diagnostic_usable": True, "cpu_test_complete": False, "full_v22_release": False})
        write(self.outer, "final.json", final)
        self.collection = {"schema": audit.OUTER + "/collection", "output_inventory_sha256": audit.digest(inventory), "release_monotonic": 20, "outer_elapsed_seconds": 12, "reservation_check_status": "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS", "complete_cvd_visibility": False, "approved_unreadable_service_pids": [123], "fits": 0, "updates": 0, "generation_retries": 0, "full_v22_release": False}
        self.recollect()

    def recollect(self):
        self.collection["files"] = {name: entry["sha256"] for name, entry in audit.Archive(self.outer).inventory.items() if name != "collection.json"}
        write(self.outer, "collection.json", self.collection)
        self.collection_hash = checksum(self.outer, "collection.json")

    def check(self):
        return audit.lineage(audit.Archive(self.data), audit.Archive(self.outer), self.manifest_hash, self.collection_hash)

    def test_relocated_synthetic_lineage_preserves_visibility_limit(self):
        collection = self.check()[2]
        self.assertFalse(collection["complete_cvd_visibility"])
        self.assertEqual(collection["approved_unreadable_service_pids"], [123])

    def test_tiny_fixture_cannot_pass_production_analysis(self):
        with self.assertRaisesRegex(ValueError, "four excluded roots"):
            audit.analyze(self.data, self.outer, manifest_sha256=self.manifest_hash, collection_sha256=self.collection_hash)

    def test_incomplete_archive_never_creates_analysis_outputs(self):
        destination = self.root / "must_not_exist"
        with self.assertRaises(ValueError):
            audit.main(["--diagnostic", str(self.data), "--outer", str(self.outer), "--manifest-sha256", self.manifest_hash, "--collection-sha256", self.collection_hash, "--output", str(destination)])
        self.assertFalse(destination.exists())

    def test_tiny_panel_cannot_replace_fixed_denominator(self):
        row = {"panel": "delayed", "projection": "EXACT_WITNESSED_GRAPH", "success": True,
               "usable_false_row": False, "execution": "SCORED"}
        with self.assertRaisesRegex(ValueError, "fixed denominator changed"):
            audit.driver._panels([row])

    def test_wrong_external_pins_rejected(self):
        self.manifest_hash = "0" * 64
        with self.assertRaisesRegex(ValueError, "manifest byte pin"):
            self.check()

    def test_missing_collection_or_extra_unbound_file_rejected(self):
        write(self.outer, "unbound.json", {})
        with self.assertRaisesRegex(ValueError, "outer inventory"):
            self.check()
        (self.outer / "collection.json").unlink()
        with self.assertRaises(KeyError):
            self.check()

    def test_failure_is_not_hidden_by_successful_final(self):
        write(self.outer, "finalize_failure.json", {"error": "synthetic failure"})
        self.recollect()
        with self.assertRaisesRegex(ValueError, "outer failure"):
            self.check()

    def test_rehashed_partial_or_mismatched_final_rejected(self):
        final = json.loads((self.outer / "final.json").read_bytes())
        final.pop("sha256")
        final["report"]["gpu_uuid"] = "GPU-DIFFERENT"
        write(self.outer, "final.json", audit.driver._seal(final))
        self.recollect()
        with self.assertRaisesRegex(ValueError, "final report"):
            self.check()

    def test_stale_report_inventory_rejected(self):
        write(self.data, "task_000.json", {"synthetic": True})
        with self.assertRaisesRegex(ValueError, "captured diagnostic inventory"):
            self.check()

    def test_capture_receipt_disagreement_rejected(self):
        write(self.outer, "worker_exit.json", {"returncode": True})
        self.recollect()
        with self.assertRaisesRegex(ValueError, "capture receipt lineage"):
            self.check()

    def test_clock_and_reservation_overclaims_rejected(self):
        for key, value in (("outer_elapsed_seconds", 101), ("release_monotonic", 21), ("complete_cvd_visibility", True)):
            with self.subTest(key=key):
                original = self.collection[key]
                self.collection[key] = value
                self.recollect()
                with self.assertRaises(ValueError):
                    self.check()
                self.collection[key] = original

    def test_fresh_only_json_markdown_keep_negative_and_partial_panels(self):
        result = {"evidence_audit": "SYNTHETIC_TINY_NOT_NATIVE", "thresholds_passed": False,
                  "panels": {"synthetic/partial": {"correct": 1, "denominator": 2, "minimum": 2, "maximum": 2, "passed": False}}}
        output = self.root / "analysis"
        audit.write_analysis(result, output)
        self.assertEqual(json.loads((output / "analysis.json").read_bytes()), result)
        text = (output / "analysis.md").read_text()
        self.assertIn("1/2", text)
        self.assertIn("False", text)
        self.assertIn("no causal order-only", text)
        with self.assertRaises(FileExistsError):
            audit.write_analysis(result, output)

    def test_cli_rejects_output_inside_archive_before_analysis(self):
        with patch.object(audit, "analyze", side_effect=AssertionError("must not inspect evidence")):
            with self.assertRaisesRegex(ValueError, "outside archives"):
                audit.main(["--diagnostic", str(self.data), "--outer", str(self.outer), "--manifest-sha256", self.manifest_hash, "--collection-sha256", self.collection_hash, "--output", str(self.data / "analysis")])


if __name__ == "__main__":
    unittest.main()
