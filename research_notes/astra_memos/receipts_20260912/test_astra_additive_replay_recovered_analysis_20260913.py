"""Pure synthetic failed-original-chain tests; no reducer/result execution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("recovered_additive_audit", "/tmp/astra_additive_replay_recovered_analysis_20260913.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode())
    return dict(path=str(path), sha256=audit.digest(path))


def recovered_fixture(home, seed, apis):
    fixture_path = Path("/tmp/test_astra_additive_replay_analysis_20260913.py")
    audit.require(audit.digest(fixture_path) == "cb59676941df9a4fbc13679c5b910333accd1edc5f7cd153ca73d6c163d38047", "prospective synthetic fixture pin differs")
    specification = importlib.util.spec_from_file_location("recovery_synthetic_fixture_only", fixture_path)
    fixture_module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(fixture_module)
    entry = fixture_module.fixture(home, seed, apis)
    launcher = Path(entry["launcher"]["root"])
    for name in ("collector_exit.json", "exit.json"):
        receipt = json.loads((launcher / name).read_bytes())
        receipt["returncode"] = 1
        entry["launcher"]["files"][name] = write(launcher / name, receipt)["sha256"]
    if seed == 1:
        entry["launcher"]["files"]["failure.json"] = write(launcher / "failure.json",
            dict(error="BrokenPipeError(32, 'Broken pipe')", holder_may_be_running=True))["sha256"]
    entry["original_failure"] = write(home / f"failed{seed}" / "collection_failure.json",
        dict(error_type="AttributeError", error=audit.EXPECTED_ERROR, retry=False, time=1338.))
    repaired = home / f"repaired{seed}"
    repaired.mkdir()
    for name in ("scores", "collection"):
        target = repaired / (name + ".json")
        target.write_bytes(Path(entry[name]["path"]).read_bytes())
        entry[name] = dict(path=str(target), sha256=audit.digest(target))
    native_root = json.loads((Path(entry["root"]) / "plan.json").read_bytes())["root"]
    original_files = {native_root + ".collection_claim.json": entry["collection_claim"]["sha256"],
                      native_root + "_collected/collection_failure.json": entry["original_failure"]["sha256"],
                      **{native_root + ".launcher/" + name: entry["launcher"]["files"][name]
                         for name in ("controller_exit.json", "collector_exit.json", "exit.json")}}
    claim = dict(schema=audit.RECOVERY_SCHEMA, root=native_root, out=native_root + "_collected_repair1",
        plan_sha256=entry["plan_sha256"], completion_sha256=entry["completion_sha256"], repair_sha256=audit.REPAIR_SHA256,
        runner_sha256=audit.RUNNER_SHA256, original_failure_files=original_files, collection_attempt=2,
        scientific_retry=False, generation_calls=0, fits=0, updates=0)
    entry["recovery_claim"] = write(home / f"repair_claim{seed}.json", claim)
    receipt = dict(schema=audit.RECOVERY_SCHEMA, status="COLLECTION_REPAIRED_NOT_SCIENTIFIC_RETRY", returncode=0,
        claim_sha256=entry["recovery_claim"]["sha256"], repair_sha256=audit.REPAIR_SHA256, runner_sha256=audit.RUNNER_SHA256,
        scores_sha256=entry["scores"]["sha256"], collection_sha256=entry["collection"]["sha256"], original_failure_files=original_files,
        collection_attempt=2, scientific_retry=False, fits=0, updates=0, generation_calls=0, elapsed_seconds=3.)
    entry["recovery"] = write(repaired / "recovery.json", receipt)
    return entry


def fixture():
    root, plan_hash, completion_hash = "/SYNTHETIC_ONLY/additive", "a"*64, "b"*64
    plan = dict(root=root, gpu_uuid="GPU-SYNTHETIC", python="/SYNTHETIC_ONLY/python")
    tiny = dict(path="/SYNTHETIC_ONLY/tiny.json", sha256=audit.TINY_SHA256, trainer_sha256=audit.TRAINER_SHA256,
                fixture_only=True, native_scientific_evidence=False)
    holder = dict(pid=100, started_unix=10., plan_sha256=plan_hash, tiny_cpu_receipt=tiny,
                  custodian_sha256=audit.LAUNCHER_SHA256, runner_sha256=audit.RUNNER_SHA256)
    launch = dict(holder, status="LAUNCHED_NOT_RESULT", seed=1, root=root, gpu_index=1, gpu_uuid=plan["gpu_uuid"],
                  automatic_once_collection=True, started_unix=11.,
                  identity=dict(pid=100, comm="python", ppid=99, start_ticks=1000, uid=500, cmdline_sha256="d"*64),
                  command=[plan["python"], "-B", audit.LAUNCHER, "hold", "--seed", "1", "--runner-sha256", audit.RUNNER_SHA256,
                           "--tiny-cpu-receipt", tiny["path"]])
    prefix = [plan["python"], "-B", audit.RUNNER]
    args = ["--root", root, "--plan-sha256", plan_hash]
    records = {
        "precheck.json": dict(time=9., gpu_index=1, gpu_uuid=plan["gpu_uuid"], reservations=[], unresolved=[]),
        "launched.json": launch, "holder_started.json": holder,
        "controller.json": dict(pid=101, pgid=101, started_unix=12., command=prefix+["controller"]+args+["--allow-gpu"]),
        "controller_exit.json": dict(returncode=0, completed_unix=30.),
        "collection_started.json": dict(plan_sha256=plan_hash, completion_sha256=completion_hash, started_unix=31.),
        "collector.json": dict(pid=102, pgid=102, started_unix=32., command=prefix+["collect"]+args+["--completion-sha256", completion_hash, "--out", root+"_collected"]),
        "collector_exit.json": dict(returncode=1, completed_unix=34.), "exit.json": dict(returncode=1, completed_unix=35.),
        "failure.json": dict(error="BrokenPipeError(32, 'Broken pipe')", holder_may_be_running=True)}
    files = {"run/"+stage+"/"+name: dict(time=20.) for stage in audit.STAGES for name in ("launch.json", "started.json", "released.json")}
    bundle = dict(entry=dict(seed=1, plan_sha256=plan_hash, completion_sha256=completion_hash,
                            launcher=dict(files={name: "e"*64 for name in set(records) | {"stdout.log"}})), plan=plan, launcher=records,
                  receipts=dict(controller_started=dict(pid=101)), claim=dict(plan_sha256=plan_hash, out=root+"_collected", retry=False), files=files)
    failure = dict(error_type="AttributeError", error=audit.EXPECTED_ERROR, retry=False, time=33.)
    return bundle, failure


class FailedOriginalTests(unittest.TestCase):
    def test_original_failure_and_transport_are_separate_and_unchanged(self):
        bundle, failure = fixture()
        before = copy.deepcopy((bundle, failure))
        result = audit.audit_original_attempt(bundle, failure)
        self.assertEqual(result["native_controller_rc"], 0)
        self.assertEqual(result["original_collector_rc"], 1)
        self.assertEqual(result["original_holder_written_rc"], 1)
        self.assertEqual(result["original_collection_failure"], failure)
        self.assertIn("BrokenPipe", result["launcher_failure"]["error"])
        self.assertFalse(result["recovery_validated"])
        self.assertIsNone(result["scientific_retries"])
        self.assertEqual((bundle, failure), before)

    def test_no_optional_transport_error_required(self):
        bundle, failure = fixture()
        del bundle["launcher"]["failure.json"]
        del bundle["entry"]["launcher"]["files"]["failure.json"]
        self.assertIsNone(audit.audit_original_attempt(bundle, failure)["launcher_failure"])

    def test_no_boolean_status_or_controller_failure_excused(self):
        for name, values in (("controller_exit.json", [False, True, 1]), ("collector_exit.json", [False, True, 0, 2]),
                             ("exit.json", [False, True, 0, 2])):
            for value in values:
                with self.subTest(name=name, value=value):
                    bundle, failure = fixture()
                    bundle["launcher"][name]["returncode"] = value
                    with self.assertRaises(ValueError):
                        audit.audit_original_attempt(bundle, failure)

    def test_only_exact_declared_failure(self):
        for key, value in (("error_type", "RuntimeError"), ("error", "different failure"), ("retry", True), ("time", 50.), ("time", float("nan"))):
            bundle, failure = fixture()
            failure[key] = value
            with self.assertRaises(ValueError):
                audit.audit_original_attempt(bundle, failure)

    def test_identity_claim_hash_and_missing_receipt_fail(self):
        for name, key, value in (("holder_started.json", "pid", 103), ("collector.json", "pid", 101),
                                 ("collection_started.json", "completion_sha256", "0"*64), ("precheck.json", "reservations", [100])):
            bundle, failure = fixture()
            bundle["launcher"][name][key] = value
            with self.assertRaises(ValueError):
                audit.audit_original_attempt(bundle, failure)
        bundle, failure = fixture()
        bundle["claim"]["retry"] = True
        with self.assertRaises(ValueError):
            audit.audit_original_attempt(bundle, failure)
        bundle, failure = fixture()
        del bundle["launcher"]["exit.json"]
        with self.assertRaises(ValueError):
            audit.audit_original_attempt(bundle, failure)

    def test_exact_failure_bytes_and_source_freeze(self):
        self.assertEqual(audit.verify_frozen_sources()[audit.FROZEN_REDUCER], audit.FROZEN_REDUCER_SHA256)
        with tempfile.TemporaryDirectory(prefix="additive_recovery_synthetic_") as temporary:
            path = Path(temporary) / "collection_failure.json"
            raw = b'{ "error_type":"AttributeError", "error":"bad", "time":33, "retry":false }\n'
            path.write_bytes(raw)
            result = audit.read_binding(dict(path=str(path), sha256=audit.digest(path)))
            self.assertEqual(result["raw_utf8"].encode(), raw)
            self.assertEqual(path.read_bytes(), raw)
            with self.assertRaises(ValueError):
                audit.read_binding(dict(path=str(path), sha256="0"*64))
        with self.assertRaises(ValueError):
            audit.decode('{"retry":false,"retry":true}')


class RecoveredCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apis = audit.load_apis()
        cls.temporary = tempfile.TemporaryDirectory(prefix="additive_recovered_synthetic_")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.home = Path(cls.temporary.name)
        cls.entries = [recovered_fixture(cls.home, seed, cls.apis) for seed in range(3)]
        cls.bundles = [audit.load_bundle(entry, cls.apis) for entry in cls.entries]

    def test_full_recovered_cohort_no_fake_terminal_status_or_old_reduction(self):
        before = copy.deepcopy([bundle["launcher"] for bundle in self.bundles])
        frozen = self.apis["frozen_reducer"]
        with patch.object(frozen, "reduce_seed", side_effect=AssertionError("old successful-collector branch forbidden")), \
             patch.object(frozen, "reduce_cohort", side_effect=AssertionError("old cohort forbidden")), \
             patch.object(frozen, "validate_launcher", side_effect=AssertionError("rc0 original collector forbidden")), \
             patch.object(frozen, "run", side_effect=AssertionError("old CLI forbidden")):
            report = audit.reduce_cohort(self.bundles, self.apis)
        self.assertEqual([report["costs"][key] for key in ("fits", "updates", "calls")], [6, 1632, 480])
        self.assertEqual([report["costs"][key] for key in ("recovery_fits", "recovery_updates", "recovery_generation_calls", "scientific_retries")], [0]*4)
        self.assertEqual(before, [bundle["launcher"] for bundle in self.bundles])
        for seed, result in enumerate(report["seeds"]):
            recovery = result["recovery"]
            self.assertEqual([recovery[key] for key in ("native_controller_rc", "original_collector_rc", "original_holder_written_rc", "recovery_recorded_rc")], [0, 1, 1, 0])
            self.assertEqual(result["screens"]["ADDITIVE"]["threshold"], (8, 7, 5)[seed])
            self.assertEqual(result["denominators"], dict(exact=(14,8,8)[seed], paraphrase=(14,8,8)[seed], held=48, canary=12, original_possible_records=16))
            self.assertTrue(recovery["recovery_validated"])
        self.assertIn("BrokenPipe", audit.markdown(report))
        self.assertFalse(report["automatic_promotion"])
        self.assertIsNone(report["scientific_pass"])

    def test_recovery_zero_cost_identity_failure_pins_strict(self):
        mutations = [("generation_calls", 1), ("fits", 1), ("updates", 1), ("collection_attempt", 1), ("scientific_retry", True),
                     ("returncode", False), ("returncode", 1), ("repair_sha256", "0"*64), ("claim_sha256", "0"*64),
                     ("scores_sha256", "0"*64), ("collection_sha256", "0"*64), ("elapsed_seconds", 181.)]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                bundle = copy.deepcopy(self.bundles[0])
                bundle["recovery_evidence"]["recovery"]["record"][key] = value
                with self.assertRaises(ValueError):
                    audit.validate_recovery(bundle)
        for key, value in (("root", "/other"), ("out", "/other"), ("completion_sha256", "0"*64),
                           ("generation_calls", False), ("original_failure_files", {})):
            bundle = copy.deepcopy(self.bundles[0])
            bundle["recovery_evidence"]["recovery_claim"]["record"][key] = value
            with self.assertRaises(ValueError):
                audit.validate_recovery(bundle)

    def test_recovery_cannot_change_scientific_raw_order_parent_or_cost(self):
        for mutate in (lambda bundle: bundle["report"]["cells"]["ADDITIVE"]["held"][0].update(raw="rewritten"),
                       lambda bundle: bundle["files"]["training_ADDITIVE.json"]["epoch_order"][0].reverse(),
                       lambda bundle: bundle["plan"]["parent"].update(adapter="/repair_descendant"),
                       lambda bundle: bundle["report"]["incremental_cost"].update(updates=0)):
            bundle = copy.deepcopy(self.bundles[0])
            mutate(bundle)
            with self.assertRaises(ValueError):
                audit.reduce_seed(bundle, self.apis)

    def test_recovery_does_not_offset_lr0_correct_loss(self):
        bundle = copy.deepcopy(self.bundles[0])
        bundle["report"]["screen"]["ADDITIVE"]["threshold"] = 0
        with self.assertRaises(ValueError):
            audit.reduce_seed(bundle, self.apis)

    def test_all_seeds_required_and_original_failures_not_hidden(self):
        for bundles in (self.bundles[:2], [self.bundles[0]] * 3):
            with self.assertRaises(ValueError):
                audit.reduce_cohort(bundles, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        bundle["launcher"]["controller_exit.json"]["returncode"] = 1
        with self.assertRaises(ValueError):
            audit.reduce_seed(bundle, self.apis)
        entry = copy.deepcopy(self.entries[0])
        entry["original_failure"]["sha256"] = "0"*64
        with self.assertRaises(ValueError):
            audit.load_bundle(entry, self.apis)

    def test_success_artifacts_only_no_second_repair_or_original_rewrite(self):
        with tempfile.TemporaryDirectory(prefix="additive_recovered_bad_inventory_") as temporary:
            entry = copy.deepcopy(self.entries[0])
            directory = Path(temporary)
            source = Path(entry["original_failure"]["path"])
            target = directory / "collection_failure.json"
            target.write_bytes(source.read_bytes())
            entry["original_failure"] = dict(path=str(target), sha256=audit.digest(target))
            (directory / "scores.json").write_bytes(b"{}")
            with self.assertRaises(ValueError):
                audit.load_bundle(entry, self.apis)

    def test_new_cli_write_once_no_native_dispatch(self):
        manifest = write(self.home / "recovered_manifest.json", dict(schema=audit.INPUT_SCHEMA, seeds=self.entries))
        out = self.home / "recovered_reduction"
        with patch("subprocess.Popen", side_effect=AssertionError("no subprocess")), \
             patch("subprocess.run", side_effect=AssertionError("no subprocess")):
            result = audit.run(manifest["path"], manifest["sha256"], str(out))
        self.assertEqual(result["analysis_sha256"], audit.digest(out / "analysis.json"))
        with self.assertRaises(ValueError):
            audit.run(manifest["path"], manifest["sha256"], str(out))


if __name__ == "__main__":
    unittest.main()
