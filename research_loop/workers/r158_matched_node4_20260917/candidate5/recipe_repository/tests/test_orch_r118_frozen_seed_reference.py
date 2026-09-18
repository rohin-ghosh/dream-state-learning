import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r118_frozen_seed_reference as reference


class FrozenSeedReferenceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        original = self.root / "original"
        source = self.root / "source"
        original.mkdir()
        source.mkdir()
        self.write(original / "PREPARE.json", dict(initial=dict(state_sha256="fixed_initial")))
        self.write(original / "COHORT.json", dict(held=[]))
        self.write(original / "SOURCE.json", dict(events=[]))
        adapter = original / "adapter_model.safetensors"
        adapter.write_bytes(b"fixture-only-not-real-weights")
        runner = source / "gpu/orch_r118_frozen_seed_reference.py"
        runner.parent.mkdir()
        runner.write_bytes(Path(reference.__file__).read_bytes())
        historical = source / "original.py"
        historical.write_text("original")
        feasibility = dict(canonical_root=str(original), prepare=self.ref(original / "PREPARE.json"),
            cohort=self.ref(original / "COHORT.json"), source_store_file=self.ref(original / "SOURCE.json"),
            historical_source_hashes={"original.py": reference.sha(historical)},
            initial_adapter=dict(state_sha256="fixed_initial", files=[dict(path=str(adapter),
                                expected_sha256=reference.sha(adapter))]),
            task_source=[dict(cycle=cycle, cohort_selector=f"held[{cycle}]", task_hashes=["one", "two"])
                         for cycle in range(1, 7)])
        self.write(self.root / "FEASIBILITY.json", feasibility)
        self.plan = dict(schema="R118_FROZEN_SEED_REFERENCE_V1", cycles=list(range(1, 7)),
            max_native_calls=72, max_new_tokens=512, context_limit=8192, optimizer_steps=0,
            parent_calls=0, retries=0, started_unix=1000, deadline_unix=1100, lease_end_unix=100000,
            output_root=str(self.root / "new_reference"), canonical_root=str(original),
            model_dir=str(self.root / "model"), gpu_uuid="GPU-fixture", source_root=str(source),
            initial_state_sha256="fixed_initial", feasibility=self.ref(self.root / "FEASIBILITY.json"),
            source_files={"gpu/orch_r118_frozen_seed_reference.py": reference.sha(runner),
                          "original.py": reference.sha(historical)})

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def ref(self, path):
        return dict(path=str(path), sha256=reference.sha(path))

    def validate(self):
        return reference.validate_plan(self.plan, clock=lambda: 1050)

    def test_valid_metadata_is_not_a_model_run(self):
        feasibility, prepared = self.validate()
        self.assertEqual(prepared["initial"]["state_sha256"], "fixed_initial")
        self.assertEqual(len(feasibility["task_source"]), 6)
        self.assertFalse(Path(self.plan["output_root"]).exists())

    def test_task_hash_matches_feasibility_json_encoding(self):
        task = dict(node="fixture", events=["one", "two"])
        expected = hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()
        compact = hashlib.sha256(json.dumps(task, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(reference.task_sha256(task), expected)
        self.assertNotEqual(reference.task_sha256(task), compact)

    def test_different_initial_child_rejected(self):
        self.plan["initial_state_sha256"] = "bare_base"
        with self.assertRaisesRegex(ValueError, "seed_matched"):
            self.validate()

    def test_different_source_bytes_rejected(self):
        (Path(self.plan["source_root"]) / "original.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "source_closure_drift"):
            self.validate()

    def test_no_mutating_original_root(self):
        self.plan["output_root"] = str(Path(self.plan["canonical_root"]) / "reference")
        with self.assertRaisesRegex(ValueError, "separate_reference"):
            self.validate()

    def test_no_extra_groups_or_presentations(self):
        self.plan["cycles"].append(7)
        with self.assertRaisesRegex(ValueError, "exact_original_six"):
            self.validate()

    def test_no_training_or_parenting(self):
        for key in ("optimizer_steps", "parent_calls", "retries"):
            original = self.plan[key]
            self.plan[key] = 1
            with self.assertRaisesRegex(ValueError, "evaluation_only"):
                self.validate()
            self.plan[key] = original

    def test_deadline_and_lease_margins(self):
        for updates in (dict(deadline_unix=1049), dict(deadline_unix=4601), dict(lease_end_unix=22000)):
            plan = dict(self.plan, **updates)
            with self.assertRaisesRegex(ValueError, "bounded_reference_wall"):
                reference.validate_plan(plan, clock=lambda: 1050)

    def test_adapter_file_change_rejected(self):
        (Path(self.plan["canonical_root"]) / "adapter_model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "initial_adapter_file_drift"):
            self.validate()

    def test_all_claims_including_failed_work_charge_budget(self):
        claims = self.root / "claims_root"
        claims.mkdir()
        for number in range(1, 73):
            actual, path = reference.reserve(claims, 1, dict(task="fixture"), clock=lambda: 1050)
            self.assertEqual(actual, number)
            self.assertEqual(reference.read(path)["status"], "CHARGED")
        with self.assertRaisesRegex(ValueError, "budget_exhausted"):
            reference.reserve(claims, 1, {})

    def test_unique_output_file_prevents_replay(self):
        target = self.root / "COMPLETE.json"
        reference.write_new(target, {"status": "FAILED"})
        with self.assertRaises(FileExistsError):
            reference.write_new(target, {"status": "COMPLETE"})
        self.assertEqual(reference.read(target)["status"], "FAILED")

    def test_exact_tasks_and_parent_free_sequential_episodes(self):
        tasks = [dict(task_id="one"), dict(task_id="two")]
        called = []
        def episode(world, task, generate, store, **kwargs):
            called.append((task, kwargs))
            return dict(task=task, parent_messages=[], correct=False)
        records = reference.run_episodes([{}], lambda world: tasks, episode, None, {},
            ["one", "two"], lambda task: task["task_id"])
        self.assertEqual(len(records), 2)
        self.assertEqual([entry[0] for entry in called], tasks)
        self.assertTrue(all(entry[1] == dict(parent=None, rich_contract=False) for entry in called))

    def test_completed_episode_preserved_when_second_fails(self):
        tasks = [dict(task_id="one"), dict(task_id="two")]
        saved = []
        def episode(world, task, generate, store, **kwargs):
            if task["task_id"] == "two":
                raise RuntimeError("simulated_failed_call")
            return dict(task=task, parent_messages=[])
        with self.assertRaisesRegex(RuntimeError, "simulated_failed_call"):
            reference.run_episodes([{}], lambda world: tasks, episode, None, {}, ["one", "two"],
                lambda task: task["task_id"], on_record=lambda index, record: saved.append((index, record)))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0][1]["task"], tasks[0])

    def test_task_order_drift_rejected_before_any_call(self):
        with self.assertRaisesRegex(ValueError, "exact_original_task_order"):
            reference.run_episodes([{}], lambda world: [dict(task_id="two"), dict(task_id="one")],
                None, None, {}, ["one", "two"], lambda task: task["task_id"])


if __name__ == "__main__":
    unittest.main()
