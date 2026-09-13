"""Only injected CPU backends/synthetic tokenizers; never native execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_dev as driver


class Tokenizer:
    chat_template = "SYNTHETIC_ONLY"

    def encode(self, text, add_special_tokens=False):
        hashed = hashlib.sha256(text.encode()).digest()
        return [int.from_bytes(hashed[index:index + 4], "big") for index in range(0, 16, 4)]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = "".join("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n" for message in messages)
        text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class Backend:
    scripted = True

    def __init__(self, plan, clock, overrides=None):
        self.clock = clock
        self.calls = []
        self.closed = False
        self.started = False
        self.count = 4
        self.close_seconds = 0
        self.outputs = {}
        for task in plan["tasks"]:
            cell = driver.core.from_data(task["cell"])
            if task["projection"] in ("OLD_ONLY_TEXT", "NEW_ONLY_TEXT", "NONE_OFF", "WRONG_ROOT"):
                raw = "MISS"
            elif task["panel"] == "delayed":
                raw = driver.core.oracle_route_v1(cell, task["goal"])
            else:
                raw = "PROBE " + cell.root.lookup("probe", "relevant")
            self.outputs[driver.core.byte_hash(task["id"]) + "/actor/0"] = raw
        self.outputs.update(overrides or {})

    def start(self):
        self.started = True
        self.clock.now += 0.1

    def generate(self, request, limits):
        self.calls.append(copy.deepcopy(request))
        self.clock.now += 0.001
        text = self.outputs.get(request["id"], "MISS")
        if isinstance(text, Exception):
            raise text
        return {"request_sha256": driver.digest(request), "text": text, "prompt_tokens": 4,
                "output_tokens": 4, "device_seconds": 0.001}

    def count_tokens(self, text):
        return self.count

    def close(self):
        self.closed = True
        self.clock.now += self.close_seconds
        return {"kind": "SYNTHETIC", "error_type": None, "budget_exceeded": False,
                "calls_consumed": len(self.calls), "owned_group_released": None,
                "gpu_vacant": None, "outer_release_required": True}


class ZeroFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = driver.build_tasks([driver.core.to_data(driver.core.build_root(f"excluded/{index}")) for index in range(4)])
        cls.audit = driver._construct(cls.plan["roots"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pcfl_zero_test_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.clock = Clock()
        self.tokenizer = Tokenizer()
        def cached_fixture_audit(roots):
            self.assertEqual([driver.core.to_data(root) for root in roots], self.plan["roots"])
            return copy.deepcopy(self.audit)
        self.audit_patch = patch.object(driver.core, "audit_construct", side_effect=cached_fixture_audit)
        self.audit_patch.start()
        self.addCleanup(self.audit_patch.stop)
        self.actor_config = dict(schema=driver.native.SCHEMA, model_path=str(self.root / "model"),
                                 model_binding={"path": str(self.root / "model_receipt.json"), "sha256": "1" * 64},
                                 source_files=driver.source_snapshot(),
                                 tokenizer_files={name: "2" * 64 for name in driver.native.TOKENIZER_FILES},
                                 chat_template_sha256=driver.core.byte_hash(self.tokenizer.chat_template),
                                 tokenizer_probe={"text": "synthetic", "token_ids": self.tokenizer.encode("synthetic")},
                                 environment={"python": "/synthetic/python", "version": "synthetic",
                                              "packages": {name: "synthetic" for name in driver.native.PACKAGES}},
                                 gpu_uuid="GPU-SYNTHETIC", engine=copy.deepcopy(driver.native.ENGINE),
                                 output_dir=str(self.root / "output" / "actor"), deadline=1000,
                                 device_seconds_cap=100, max_input_tokens=8192, max_output_tokens=2048, max_calls=1952)
        self.measured = driver.measure_tokenizer(self.plan, self.tokenizer, driver.tokenizer_binding(self.actor_config), synthetic=True)

    def manifest(self):
        return driver.build_manifest(self.plan, self.measured, self.actor_config, wall_seconds=100,
                                     device_seconds=100, output_dir=self.root / "output", test_only=True)

    def diagnostic(self, overrides=None):
        backend = Backend(self.plan, self.clock, overrides)
        run = driver.Diagnostic(self.manifest(), self.tokenizer, backend_factory=lambda config: backend, clock=self.clock)
        return run, backend

    def test_fixed_expansion_controls_and_no_full_release(self):
        self.assertEqual(len(self.plan["tasks"]), 800)
        self.assertEqual(len(self.plan["call_slots"]), 1952)
        self.assertEqual(sum(task["panel"] == "delayed" for task in self.plan["tasks"]), 640)
        self.assertEqual(sum(task["panel"] == "reachout" for task in self.plan["tasks"]), 160)
        self.assertEqual(sum(task["projection"] == "ACTIVE_LINKED_TEXT" for task in self.plan["tasks"]), 96)
        validation = driver.validate_manifest(self.manifest(), self.tokenizer)
        self.assertTrue(validation["zero_fit_manifest_valid"])
        self.assertFalse(validation["full_v22_release"])

    def test_distinct_literal_ra_rb_lengths_are_not_substitution_drift(self):
        class RenderTokenizer(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                tokens = super().encode(text, add_special_tokens)
                return tokens + [17] if "PROBE OPTIONS\n" in text else tokens

        measured = driver.measure_tokenizer(self.plan, RenderTokenizer(),
                                            driver.tokenizer_binding(self.actor_config), synthetic=True)
        indexed = {entry["id"]: entry for entry in measured["measurements"]}
        for projection in driver.runtime.REACHOUT:
            for render_id, length in (("RA", 4), ("RB", 5)):
                group = measured["groups"][f"initial/reachout/{projection}/{render_id}"]
                self.assertEqual(len(group), 16)
                self.assertEqual({len(indexed[identifier]["token_ids"]) for identifier in group}, {length})
        self.assertEqual(len(measured["groups"]["opaque"]), len(self.measured["groups"]["opaque"]))

    def test_within_render_substitution_length_drift_still_rejected(self):
        endpoint = self.plan["roots"][0]["inventory"]["node"]["S_L"]

        class DriftTokenizer(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                tokens = super().encode(text, add_special_tokens)
                return tokens + [17] if "AVAILABLE PROBES\n" in text and endpoint in text else tokens

        with self.assertRaisesRegex(ValueError, "unequal used substitution token lengths: initial/reachout/"):
            driver.measure_tokenizer(self.plan, DriftTokenizer(),
                                     driver.tokenizer_binding(self.actor_config), synthetic=True)
        self.assertEqual(self.plan["fits"], 0)

    def test_all_800_injected_tasks_and_public_boundary(self):
        run, backend = self.diagnostic()
        report = run.run()
        self.assertEqual(report["status"], "COMPLETE_AWAITING_OUTER_RELEASE")
        self.assertEqual((report["tasks"], report["scored_tasks"], report["actor_attempts"]), (800, 800, 800))
        self.assertTrue(report["thresholds_passed"])
        self.assertFalse(report["diagnostic_usable"])
        self.assertTrue(backend.closed)
        self.assertEqual(sum(panel["denominator"] for panel in report["panels"].values()), 800)
        for request in backend.calls:
            self.assertEqual(set(request), {"id", "messages", "seed", "mount"})
            self.assertEqual(request["mount"], "C0")
            for message in request["messages"]:
                self.assertEqual(set(message), {"role", "content"})
                self.assertNotIn("excluded/", message["content"])
        with self.assertRaisesRegex(ValueError, "one attempt"):
            run.run()
        attestation = {"report_sha256": report["sha256"], "gpu_uuid": "GPU-SYNTHETIC",
                       "owned_group_released": True, "gpu_vacant": True,
                       "elapsed_seconds_from_start": report["wall_seconds_through_close"] + 1}
        path = self.root / "release.json"
        path.write_bytes(driver.canonical(attestation))
        receipt = {**attestation, "evidence_path": str(path), "evidence_sha256": driver._file_hash(path)}
        final = driver.finalize_release(report, receipt)
        self.assertTrue(final["cpu_test_complete"])
        self.assertFalse(final["diagnostic_usable"])
        self.assertFalse(final["full_v22_release"])
        with self.assertRaisesRegex(ValueError, "release-inclusive budget"):
            driver.finalize_release(report, {**receipt, "elapsed_seconds_from_start": 101})
        with self.assertRaisesRegex(ValueError, "outer release not verified"):
            driver.finalize_release(report, {**receipt, "gpu_vacant": False})

    def test_missing_backend_in_test_mode_does_not_load_native(self):
        with self.assertRaisesRegex(ValueError, "test mode requires"):
            driver.Diagnostic(self.manifest(), self.tokenizer, clock=self.clock)

    def test_generation_failure_retains_all_denominators(self):
        first = self.plan["call_slots"][0]["id"]
        run, backend = self.diagnostic({first: RuntimeError("synthetic failure")})
        report = run.run()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual((len(report["results"]), report["scored_tasks"], report["actor_attempts"]), (800, 0, 1))
        self.assertEqual(sum(panel["missing"] for panel in report["panels"].values()), 800)
        self.assertEqual(len(backend.calls), 1)
        self.assertTrue(backend.closed)

    def test_read_service_exact_transcript_and_same_scorer(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        request = next(iter(task["queries"]))
        prefix = driver.core.byte_hash(task["id"]) + "/actor/"
        route = driver.core.oracle_route_v1(driver.core.from_data(task["cell"]), task["goal"])
        run, backend = self.diagnostic({prefix + "0": request, prefix + "1": route})
        run.out = self.root / "single"
        run.out.mkdir()
        run.actor = backend
        result = run._task(task)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["reads"]), 1)
        self.assertEqual(backend.calls[1]["messages"][-1], {"role": "user", "content": task["queries"][request]["target"]})
        self.assertEqual(result["returned_tokens"], 4)

    def test_thirteenth_read_is_failed_commit_not_retry(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        request = next(iter(task["queries"]))
        prefix = driver.core.byte_hash(task["id"]) + "/actor/"
        run, backend = self.diagnostic({prefix + str(index): request for index in range(13)})
        run.out = self.root / "single"
        run.out.mkdir()
        run.actor = backend
        result = run._task(task)
        self.assertEqual(len(backend.calls), 13)
        self.assertEqual(len(result["reads"]), 12)
        self.assertTrue(result["invalid_read"])
        self.assertFalse(result["success"])

    def test_service_token_drift_stops(self):
        task = next(task for task in self.plan["tasks"] if task["projection"] == "ACTIVE_LINKED_TEXT")
        prefix = driver.core.byte_hash(task["id"]) + "/actor/0"
        run, backend = self.diagnostic({prefix: next(iter(task["queries"]))})
        run.out = self.root / "single"
        run.out.mkdir()
        run.actor = backend
        backend.count = 5
        with self.assertRaisesRegex(ValueError, "service token count"):
            run._task(task)

    def test_expired_deadline_does_not_call_factory(self):
        self.actor_config["deadline"] = 5
        factory = Mock()
        with self.assertRaisesRegex(ValueError, "deadline expired"):
            driver.Diagnostic(self.manifest(), self.tokenizer, backend_factory=factory, clock=self.clock)
        factory.assert_not_called()

    def test_missing_measurements_and_synthetic_cannot_be_native(self):
        manifest = self.manifest()
        manifest["test_only"] = False
        manifest = driver._seal(driver._unseal(self.manifest()) | {"test_only": False})
        with self.assertRaisesRegex(ValueError, "synthetic measurements"):
            driver.validate_manifest(manifest)
        broken = driver._unseal(self.measured)
        broken["measurements"].pop()
        with self.assertRaises(ValueError):
            driver._check_measurements(driver._seal(broken))

    def test_task_and_source_drift_reject(self):
        manifest = self.manifest()
        payload = copy.deepcopy(driver._unseal(manifest))
        payload["sources"][next(iter(payload["sources"]))] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source/scope pins"):
            driver.validate_manifest(driver._seal(payload))
        payload = copy.deepcopy(driver._unseal(manifest))
        plan = driver._unseal(payload["plan"])
        plan["tasks"].pop()
        payload["plan"] = driver._seal(plan)
        with self.assertRaisesRegex(ValueError, "task/control"):
            driver.validate_manifest(driver._seal(payload))

    def test_world_unresolved_stops_before_backend(self):
        with patch.object(driver.core, "production_binding_status", return_value={"definition_bound": False}):
            with self.assertRaisesRegex(ValueError, "world unresolved"):
                driver.build_tasks(self.plan["roots"])

    def test_caller_caps_strict_and_closed(self):
        for value in (True, 0, -1, 36001, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                driver.build_manifest(self.plan, self.measured, self.actor_config,
                                      wall_seconds=value, device_seconds=100,
                                      output_dir=self.root / "output", test_only=True)

    def test_existing_output_is_not_reopened(self):
        run, backend = self.diagnostic()
        (self.root / "output").mkdir()
        with self.assertRaises(FileExistsError):
            run.run()
        self.assertFalse(backend.started)

    def test_wrong_tokenizer_replay_rejected_before_backend(self):
        manifest = self.manifest()
        class Different(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                result = super().encode(text, add_special_tokens)
                result[0] += 1
                return result
        with self.assertRaisesRegex(ValueError, "transcript differs"):
            driver.Diagnostic(manifest, Different(), backend_factory=Mock(), clock=self.clock)

    def test_cold_load_and_close_are_inside_budget(self):
        run, backend = self.diagnostic()
        def expensive_start():
            backend.started = True
            self.clock.now += 101
        backend.start = expensive_start
        report = run.run()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["actor_attempts"], 0)
        self.assertTrue(backend.closed)
        self.assertEqual(len(report["results"]), 800)
        self.assertEqual(report["error"]["type"], "BUDGET_EXCEEDED")

    def test_opaque_length_and_actual_file_measurements_fail_closed(self):
        class TooShort(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                return super().encode(text, add_special_tokens)[:3]
        with self.assertRaisesRegex(ValueError, "opaque common L"):
            driver.measure_tokenizer(self.plan, TooShort(), driver.tokenizer_binding(self.actor_config), synthetic=True)
        self.tokenizer.name_or_path = self.actor_config["model_path"]
        with self.assertRaises(FileNotFoundError):
            driver.measure_tokenizer(self.plan, self.tokenizer, driver.tokenizer_binding(self.actor_config))


if __name__ == "__main__":
    unittest.main()
