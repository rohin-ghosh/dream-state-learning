"""In-memory controller tests; no fixture files, native modules, subprocesses or GPU."""
import copy
import importlib.util
import os
from pathlib import Path
import signal
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location("conditional_driver", "/tmp/astra_conditional_readout_run_20260912.py")
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.source, self.root = Path("/fixture/source"), Path("/fixture/readouts")
        self.now, self.monotonic = 1000., 100.
        self.files, self.hashes, self.directories, self.writes, self.calls = {}, {}, set(), [], []
        self.source_hashes = {"conditional_behavior_readout.py": "readout-hash", "dependency.py": "dependency-hash"}
        self.record = dict(source_root=str(self.source), source_hashes=self.source_hashes, driver_sha256="driver-hash",
            status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", generation_calls=672, candidate_forwards=576, device="0",
            model_files={"base": "base-hash"}, material_inventory={"AUTH.json": "auth", "DERANGED.json": "deranged"},
            assay_version="fixture-dual-map", prior_fit_full_reservation_seconds=464.397178,
            controller_seconds=4500, external_collection_margin_seconds=300, total_ceiling_seconds=5400, phases=[])
        self.plans = {}
        for state, phase in driver.ORDER:
            phase_root = self.root / (state + "_" + phase)
            row = dict(state=state, phase=phase, root=str(phase_root), plan_sha256=state + "_" + phase + "-pin")
            self.record["phases"].append(row)
            plan = dict(state=state, phase=phase, device="0", model="/fixture/model", model_files=self.record["model_files"],
                material="/fixture/material", material_inventory=self.record["material_inventory"], material_manifest_sha256="material-hash",
                candidate_sha256="candidate-hash", source_hashes=self.source_hashes, controls=["fixed-control"],
                worker_seconds=600, resource_budget={"ceiling": 5400}, lease_end=20000.,
                adapter=None if state == "OFF" else "/fixture/" + state,
                adapter_files={} if state == "OFF" else {"weight": state})
            self.plans[str(phase_root)] = plan
            self.files[str(phase_root / "plan.json")] = plan
            self.files[str(phase_root / "plan.sha256.json")] = {"sha256": row["plan_sha256"]}
            self.hashes[str(phase_root / "plan.json")] = row["plan_sha256"]
        self.files[str(self.root / "manifest.json")] = self.record
        self.hashes[str(self.root / "manifest.json")] = "manifest-pin"
        self.hashes[driver.__file__] = "driver-hash"
        self.hashes[str(self.source / "organism_v6/conditional_behavior_readout.py")] = "readout-hash"
        probe = SimpleNamespace(gpu_processes_absent=Mock(return_value=True))
        self.api = SimpleNamespace(base=SimpleNamespace(REPO=self.source, WORKER_SECONDS=600, LOAD_SECONDS=180,
            CALL_SECONDS=120, CLEANUP_RESERVE=140, supervisor=probe), ASSAY_VERSION="fixture-dual-map",
            sources=Mock(return_value=self.source_hashes), verify=Mock(side_effect=self.verify_phase),
            run=Mock(side_effect=self.run_phase), reduce=Mock(side_effect=self.reduce_phase),
            summarize=Mock(side_effect=lambda rows: dict(complete=True, scientific_pass=False, reductions=rows)))
        patches = [patch.object(driver, "read", side_effect=lambda path: copy.deepcopy(self.files[str(path)])),
            patch.object(driver, "digest", side_effect=lambda path: self.hashes[str(path)]),
            patch.object(driver, "write", side_effect=self.write), patch.object(driver, "import_api", return_value=self.api),
            patch.object(driver.time, "time", side_effect=lambda: self.now),
            patch.object(driver.time, "monotonic", side_effect=lambda: self.monotonic),
            patch.object(driver.signal, "signal", return_value=None), patch.object(driver.signal, "setitimer"),
            patch.object(Path, "resolve", lambda path, **kwargs: path),
            patch.object(Path, "exists", lambda path: str(path) in self.files or str(path) in self.directories),
            patch.object(Path, "is_file", lambda path: str(path) in self.files), patch.object(Path, "is_symlink", return_value=False),
            patch.object(Path, "mkdir", lambda path, **kwargs: self.directories.add(str(path))),
            patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"})]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def advance(self, seconds):
        self.now += seconds
        self.monotonic += seconds

    def write(self, path, value):
        if str(path) in self.files:
            raise FileExistsError(str(path))
        self.files[str(path)] = copy.deepcopy(value)
        self.writes.append(str(path))

    def verify_phase(self, root):
        self.calls.append(("verify", root.name))
        return copy.deepcopy(self.plans[str(root)]), {}, None

    def receipt(self, **changes):
        return dict(dict(ok=True, reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True,
            returncode=0, error=None, reserved_seconds=7., device="0"), **changes)

    def run_phase(self, root, *, allow_gpu):
        self.assertTrue(allow_gpu)
        self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "0")
        self.calls.append(("run", root.name))
        self.directories.add(str(root / "run"))
        self.files[str(root / "run/worker/process.json")] = dict(pid=123, pgid=123, device="0")
        receipt = self.receipt()
        self.files[str(root / "run/worker/supervision.json")] = receipt
        self.advance(10)
        return receipt

    def reduce_phase(self, root):
        self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "0")
        self.calls.append(("reduce", root.name))
        self.advance(3)
        plan = self.plans[str(root)]
        return dict(complete=True, status="COMPLETE_PHASE", state=plan["state"], phase=plan["phase"], scientific_pass=False,
            plan_sha256=self.hashes[str(root / "plan.json")], reserved_seconds=7., raw_results=["kept-unfiltered"])

    def run_driver(self, **kwargs):
        return driver.run(self.source, self.root, "manifest-pin", 10000., 20000., True, **kwargs)

    def terminal(self):
        return self.files[str(self.root / "controller/terminal.json")]

    def test_readonly_preflight_all_six(self):
        before = copy.deepcopy(self.files)
        record, api, plans = driver.verify(self.source, self.root, "manifest-pin")
        self.assertEqual(len(plans), 6)
        self.assertEqual(self.files, before)
        self.assertEqual(self.writes, [])
        self.api.run.assert_not_called()
        self.api.base.supervisor.gpu_processes_absent.assert_not_called()

    def test_main_manifest_unchanged_with_external_driver_pin(self):
        del self.record["driver_sha256"]
        snapshot = copy.deepcopy(self.record)
        driver.verify(self.source, self.root, "manifest-pin", "driver-hash")
        self.assertEqual(self.record, snapshot)
        result = self.run_driver(driver_pin="driver-hash")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(self.record, snapshot)

    def test_external_driver_pin_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "driver"):
            driver.verify(self.source, self.root, "manifest-pin", "incorrect")
        self.api.run.assert_not_called()

    def test_manifest_workload_and_device_mismatch_rejected(self):
        for key, value in (("generation_calls", 576), ("candidate_forwards", 384), ("device", "2")):
            original = self.record[key]
            self.record[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
            self.record[key] = original

    def test_fixed_order_both_modes_no_scientific_skips(self):
        original = {key: copy.deepcopy(value) for key, value in self.files.items()}
        terminal = self.run_driver()
        self.assertEqual(terminal["status"], "COMPLETE")
        self.assertEqual([name for action, name in self.calls if action == "run"], [s + "_" + p for s, p in driver.ORDER])
        self.assertEqual(self.calls[:6], [("verify", s + "_" + p) for s, p in driver.ORDER])
        self.assertEqual(self.api.summarize.call_count, 1)
        self.assertTrue(all(self.files[key] == value for key, value in original.items()))
        self.assertFalse(terminal["counts_used_for_queue_selection"])
        self.assertFalse(terminal["summary"]["scientific_pass"])
        self.assertEqual(len(terminal["attempts"]), 6)
        self.assertTrue(all("/controller/" in name and "/run/data/" not in name for name in self.writes))

    def test_cost_full_outputs_and_startup_charged(self):
        terminal = self.run_driver(clock=(950., 50.))
        self.assertEqual(terminal["worker_reserved_seconds"], 42.)
        self.assertEqual(terminal["reserved_seconds"], 128.)
        self.assertEqual(terminal["effective_deadline"], 5450.)
        self.assertEqual(terminal["prior_fit_full_reservation_seconds"] + 4500 + 300, 5264.397178)
        self.assertEqual(terminal["attempts"][0]["reduction"]["raw_results"], ["kept-unfiltered"])
        self.assertEqual(driver.signal.setitimer.call_args_list[0].args[1], 4310.)

    def test_bounds_clamp_deadline_lease_and_sealed_plan(self):
        plans = list(self.plans.values())
        self.assertEqual(driver.bounds(1000., 10000., 20000., plans), 5500.)
        self.assertEqual(driver.bounds(1000., 3000., 20000., plans), 3000.)
        self.assertEqual(driver.bounds(1000., 10000., 2500., plans), 2490.)
        plans[0]["lease_end"] = 2200.
        self.assertEqual(driver.bounds(1000., 10000., 20000., plans), 2190.)
        with self.assertRaises(ValueError):
            driver.bounds(1000., float("nan"), 20000., plans)

    def test_explicit_gpu_and_matching_device_before_actions(self):
        with self.assertRaises(ValueError):
            driver.run(self.source, self.root, "manifest-pin", 10000., 20000.)
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "1"}), self.assertRaisesRegex(ValueError, "CUDA"):
            self.run_driver()
        self.assertEqual(self.writes, [])
        self.api.run.assert_not_called()

    def test_manifest_source_driver_and_phase_pins(self):
        for path in (self.root / "manifest.json", Path(driver.__file__), self.source / "organism_v6/conditional_behavior_readout.py",
                     self.root / "OFF_generate/plan.json"):
            old = self.hashes[str(path)]
            self.hashes[str(path)] = "changed"
            with self.subTest(path=path), self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
            self.hashes[str(path)] = old

    def test_reordered_or_missing_phase_rejected(self):
        original = self.record["phases"]
        for rows in (list(reversed(original)), original[:-1]):
            self.record["phases"] = rows
            with self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
        self.record["phases"] = original

    def test_prepared_roots_and_control_outputs_must_be_fresh(self):
        for path in (self.root / "controller", self.root / "AUTH_score/run"):
            self.directories.add(str(path))
            with self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
            self.directories.remove(str(path))

    def test_same_device_model_material_and_adapter_required(self):
        root = str(self.root / "AUTH_score")
        for key, value in (("device", "9"), ("model", "/other/model"), ("material", "/other/material"),
                           ("adapter", "/other/adapter"), ("adapter_files", {"changed": "hash"}), ("lease_end", 19999.)):
            before = self.plans[root][key]
            self.plans[root][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
            self.plans[root][key] = before

    def test_supervisor_constants_not_reconfigured(self):
        for key in ("WORKER_SECONDS", "LOAD_SECONDS", "CALL_SECONDS", "CLEANUP_RESERVE"):
            before = getattr(self.api.base, key)
            setattr(self.api.base, key, before + 1)
            with self.subTest(key=key), self.assertRaises(ValueError):
                driver.verify(self.source, self.root, "manifest-pin")
            setattr(self.api.base, key, before)

    def test_budget_ceiling_includes_prior_fits_and_margin(self):
        self.record["prior_fit_full_reservation_seconds"] = 601.
        with self.assertRaisesRegex(ValueError, "ceiling"):
            driver.verify(self.source, self.root, "manifest-pin")

    def test_native_preflight_failure_no_outputs_or_launch(self):
        self.api.verify.side_effect = ValueError("native prep mismatch")
        with self.assertRaisesRegex(ValueError, "preflight"):
            self.run_driver()
        self.assertEqual(self.writes, [])
        self.api.run.assert_not_called()
        self.assertEqual(driver.signal.setitimer.call_args.args[1], 0)

    def test_750_second_start_window_inclusive(self):
        self.now, self.monotonic = 4750., 3850.
        with self.assertRaises(ValueError):
            self.run_driver(clock=(1000., 100.))
        self.assertEqual(self.api.run.call_count, 1)
        self.assertEqual(self.terminal()["completed_phases"], 1)
        self.assertEqual(self.terminal()["status"], "PARTIAL")
        self.api.summarize.assert_not_called()

    def test_less_than750_preflight_starts_nothing(self):
        self.now = 4751.
        with self.assertRaisesRegex(ValueError, "750"):
            self.run_driver(clock=(1000., 100.))
        self.api.run.assert_not_called()
        self.assertEqual(self.writes, [])

    def test_incomplete_reduction_preserved_not_zero_or_summary(self):
        def reduce(root):
            return self.reduce_phase(root) if root.name == "OFF_generate" else dict(complete=False, status="INCOMPLETE", error="missing raw call")
        self.api.reduce.side_effect = reduce
        with self.assertRaises(ValueError):
            self.run_driver()
        terminal = self.terminal()
        self.assertEqual(terminal["status"], "PARTIAL")
        self.assertEqual(terminal["completed_phases"], 1)
        self.assertEqual(terminal["attempts"][1]["reduction"]["status"], "INCOMPLETE")
        self.assertEqual(terminal["worker_reserved_seconds"], 14.)
        self.assertEqual(self.api.run.call_count, 2)
        self.api.summarize.assert_not_called()

    def test_global_alarm_flows_through_owned_supervisor_cleanup(self):
        def run(root, *, allow_gpu):
            self.run_phase(root, allow_gpu=allow_gpu)
            handler = next(call.args[1] for call in driver.signal.signal.call_args_list if call.args[0] == signal.SIGALRM)
            try:
                handler(signal.SIGALRM, None)
            finally:
                self.files[str(root / "run/worker/supervision.json")] = self.receipt(ok=False, returncode=-15, error={"type": "RuntimeError"})
        self.api.run.side_effect = run
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(self.api.run.call_count, 1)
        self.assertTrue(self.terminal()["release_verified"])
        self.assertEqual(self.terminal()["status"], "PARTIAL")
        self.assertIn("boundary", self.terminal()["error"]["message"])
        self.api.summarize.assert_not_called()

    def test_cleanup_failure_keeps_partial_terminal(self):
        self.api.base.supervisor.gpu_processes_absent.return_value = False
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertFalse(self.terminal()["release_verified"])
        self.assertEqual(self.terminal()["status"], "PARTIAL")

    def test_supervision_failure_no_retry(self):
        def run(root, *, allow_gpu):
            self.run_phase(root, allow_gpu=allow_gpu)
            bad = self.receipt(ok=False, returncode=1, error={"message": "failed"})
            self.files[str(root / "run/worker/supervision.json")] = bad
            return bad
        self.api.run.side_effect = run
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(self.api.run.call_count, 1)
        self.assertEqual(self.terminal()["retries"], 0)
        self.api.summarize.assert_not_called()

    def test_unaccounted_worker_preserved_as_partial(self):
        def run(root, *, allow_gpu):
            self.files[str(root / "run/worker/process.json")] = {"pid": 123}
            raise RuntimeError("supervisor receipt unavailable")
        self.api.run.side_effect = run
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(len(self.terminal()["unaccounted_processes"]), 1)
        self.assertFalse(self.terminal()["release_verified"])

    def test_reduction_cost_mismatch_is_technical_failure(self):
        def reduce(root):
            value = self.reduce_phase(root)
            value["reserved_seconds"] = 123.
            return value
        self.api.reduce.side_effect = reduce
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(self.terminal()["completed_phases"], 0)
        self.api.summarize.assert_not_called()

    def test_existing_controller_never_resumed(self):
        self.run_driver()
        before, calls = copy.deepcopy(self.files), self.api.run.call_count
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(self.files, before)
        self.assertEqual(self.api.run.call_count, calls)

    def test_no_off_adapter_and_distinct_fit_states(self):
        self.plans[str(self.root / "OFF_generate")]["adapter"] = "/fixture/AUTH"
        self.plans[str(self.root / "OFF_score")]["adapter"] = "/fixture/AUTH"
        with self.assertRaises(ValueError):
            driver.verify(self.source, self.root, "manifest-pin")

    def test_summary_only_after_all_six_complete_and_not_l1(self):
        self.run_driver()
        rows = self.api.summarize.call_args.args[0]
        self.assertEqual([(r["state"], r["phase"]) for r in rows], list(driver.ORDER))
        self.assertFalse(self.terminal()["supplies_l1_verdict"])


if __name__ == "__main__":
    unittest.main()
