"""Real-format CPU captures only; synthetic adapters are not GPU evidence."""

import ast
import copy
from dataclasses import asdict
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_v2_reduce_followup as api
from gpu import astra_pcfl_event_sequence_v2_readout as readout
import test_astra_pcfl_event_sequence_v2_readout as fixtures


KIND = "INJECTED_CPU_TEST"


class FollowupFixture:
    def __init__(self, fixture):
        self.fixture, self.harness = fixture, fixture.harness
        self.template = fixture.completed_fit()

    def write(self, path, value, seal=False):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        value = copy.deepcopy(value)
        if seal:
            value.pop("sha256", None)
            value = api.prefix.seal(value)
        path.write_bytes(api.prefix.canonical(value) + b"\n")
        return api.file_pin(path)

    def outer(self, root, stage, state, inputs_pin, allocation_pin):
        inputs, allocation = api.pinned(inputs_pin), api.pinned(allocation_pin)
        identity = {"pid": os.getpid(), "uid": os.getuid(), "boot_id": "NONNATIVE_CPU_FIXTURE",
                    "pgid": os.getpid(), "sid": os.getpid()}
        selection = {"phase": state} if stage == "fit" else {"stage": "readout", "state": state}
        self.write(root / "inputs.input.json", inputs)
        self.write(root / "allocation.input.json", allocation)
        self.write(root / "binding.json", {"argv": ["NONNATIVE", "--output", str(root / stage)],
            "deadline_monotonic": 1060, "worker_deadline_monotonic": 1000})
        self.write(root / "context.json", {"schema": api.OUTER_SCHEMA, **selection,
            "inputs": inputs_pin, "outer_source_sha256": "a" * 64, "entry_monotonic": 0})
        self.write(root / "worker_start.json", {"identity": identity})
        self.write(root / "worker_exit.json", {"identity": identity, "pid": identity["pid"], "returncode": 0, "signal": None})
        observations = {"worker_wait": 0, "worker_release": {"identity": identity, "owned_group_released": True}}
        for when in ("pre", "post"):
            observations.update({when + "_queue": {"matched": True},
                when + "_gpu": {"empty": True, "gpu_uuid": inputs["gpu_uuid"]},
                when + "_cvd": {"clear": True, "owners": [], "unresolved": []}})
        for name, value in observations.items():
            self.write(root / (name + ".json"), {"started_monotonic": 1, "ended_monotonic": 2, "value": value})
        self.write(root / "collection.json", {"schema": api.OUTER_SCHEMA + "/collection", **selection,
            "status": "COMPLETED", "errors": [], "returncode": 0, "gpu_released": True, "retries": 0,
            "automatic_promotion": False, "full_contract_released": False, "original_status": "FORMATION_FAILED",
            "inputs": inputs_pin, "allocation_file_sha256": allocation_pin["sha256"], "outer_source_sha256": "a" * 64,
            "worker_identity": identity, "observations": observations, "elapsed_seconds": 100}, seal=True)
        return self.refresh(root, stage)

    def refresh(self, root, stage):
        completed = api.read(root / stage / "completed.json")
        completed["files"] = {name: entry["sha256"] for name, entry in api.inventory(root / stage).items()
                              if name != "completed.json"}
        self.write(root / stage / "completed.json", completed, seal=True)
        completed = api.read(root / stage / "completed.json")
        self.write(root / (stage + "_completed.json"), completed)
        collection = api.read(root / "collection.json")
        collection.update(completed_sha256=completed["sha256"], stage_inventory=api.inventory(root / stage),
            files={name: entry for name, entry in api.inventory(root).items() if name != "collection.json"})
        return self.write(root / "collection.json", collection, seal=True)

    def fit(self, root, phase, inputs_pin, material, acquired=None):
        shutil.copytree(self.template, root / "fit")
        stage, inputs = root / "fit", api.pinned(inputs_pin)
        selected = material["phases"][phase]
        config = asdict(api.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cpu"))
        self.write(stage / "config.json", config)
        self.write(stage / "corpus.json", selected["items"])
        manifest = api.read(stage / "checkpoint/train_manifest.json")
        warm, trainable = None, ["base.layer.lora_A.default.weight", "base.layer.lora_B.default.weight"]
        if inputs["predecessor"] is not None:
            parent = api.pinned(inputs["predecessor"])
            files = {name: entry["sha256"] for name, entry in api.inventory(Path(parent["checkpoint"])).items()}
            tensor_state = {"base_model.model." + name.replace(".default.weight", ".weight"): {"shape": [8, 8], "dtype": "torch.float32", "sha256": "b" * 64}
                            for name in trainable}
            warm = {"parent_path": parent["checkpoint"], "parent_files": files, "parent_files_after": files,
                "initialized_loaded_state_check": True, "base_frozen": True, "adapter_count": 1, "parent_unchanged": True,
                "optimizer_initialization": "fresh_per_write", "optimizer_state_restored": False,
                "optimizer_initial_state_entries": 0, "optimizer_state_saved": False, "phase_steps": config["max_steps"],
                "cumulative_steps": 200 + config["max_steps"], "source_state": tensor_state,
                "initialized_state": copy.deepcopy(tensor_state), "dtype_conversions": {}}
        manifest.update(config=config, steps=config["max_steps"], micro_batches=config["max_steps"], warm_start=warm,
            corpus={"file": "corpus.json", "sha256": api.file_hash(stage / "corpus.json"),
                    "n_items": selected["presentations"], "n_encoded": selected["presentations"], "n_skipped_no_target": 0},
            tokens={"target": selected["supervised_tokens"], "total": selected["input_tokens"]})
        if warm is None:
            manifest.pop("warm_start")
        self.write(stage / "checkpoint/train_manifest.json", manifest)
        receipt = api.read(stage / "completed.json")
        receipt.update(phase=phase, updates=config["max_steps"], learner_seed=inputs["learner_seed"],
            parent_phase=api.sequence.PHASES[phase][0], predecessor=inputs["predecessor"], warm_start=warm,
            inputs=inputs_pin, material_sha256=inputs["material"]["sha256"], export_sha256=material["sha256"],
            spec_sha256=material["spec"]["sha256"], items_sha256=selected["items_sha256"], encoding_sha256=selected["encoding_sha256"],
            checkpoint=str(stage / "checkpoint"), trainable_names=trainable, gpu_released=False, outer_release_required=True,
            original_status="FORMATION_FAILED", full_contract_released=False, automatic_promotion=False,
            elapsed_seconds={"load_and_base_check": 0, "v3_fit_call": 0, "worker": 0},
            acquisition_validation=acquired or "NOT_REQUIRED_A200",
            files={name: entry["sha256"] for name, entry in api.inventory(stage).items() if name != "completed.json"})
        return self.write(stage / "completed.json", receipt, seal=True)

    def state(self, root, state, inputs_pin, material, correct):
        root.mkdir(parents=True)
        self.harness.texts = [record["target"] if index in correct else "MISS"
                              for index, record in enumerate(material["spec"]["records"] * 2)]
        self.harness.finishes = ["stop"] * 16
        readout.run_state(inputs_pin["path"], inputs_pin["sha256"], root / "readout", 1000, state=state,
            tokenizer_factory=lambda config: self.harness.tokenizer, actor_factory=self.harness.actor,
            environment_reader=lambda: self.harness.env, clock=self.harness.clock)

    def build(self, seed=1):
        root = self.harness.root / f"seed{seed}"
        followup = root / "followup"
        material = api.sequence.export_material(self.harness.imported, self.harness.imported["sha256"],
                                                self.harness.tokenizer, learner_seed=seed)
        material_pin = self.write(root / "material.json", material)
        cold = {**self.fixture.inputs, "material": material_pin, "learner_seed": seed, "fit_receipt": None}
        trained = {**cold, "schema": api.FIT_SCHEMA + "/inputs", "source_files": readout.fit.source_files(), "predecessor": None}
        trained.pop("fit_receipt")
        cold_pin = self.write(root / "c0_inputs.json", cold)
        trained_pin = self.write(root / "fit_inputs.json", trained)
        allocation_pin = self.write(root / "allocation.json", {"uid": os.getuid(), "boot_id": "NONNATIVE_CPU_FIXTURE",
            "gpu_index": 0, "gpu_uuid": cold["gpu_uuid"], "outer_sha256": "a" * 64})
        parent_root = root / "initial/fit_outer"
        parent = self.fit(parent_root, "A200", trained_pin, material)
        original_fit = self.outer(parent_root, "fit", "A200", trained_pin, allocation_pin)
        originals = [original_fit]
        for state, correct in (("NO_WRITE", ()), ("A200", range(8, 12))):
            inputs_pin = cold_pin if state == "NO_WRITE" else self.write(root / "a200_inputs.json", {**cold, "fit_receipt": parent})
            output = root / "initial" / (state.lower() + "_outer")
            self.state(output, state, inputs_pin, material, correct)
            originals.append(self.outer(output, "readout", state, inputs_pin, allocation_pin))
        request = self.write(followup / "inputs/acquisition_request.json", {"schema": api.acquisition.SCHEMA + "/request",
            "no_write_collection": originals[1], "a200_collection": originals[2]})
        acquired = api.acquisition.validate(request, material, trained, expected_kind=KIND)
        acquisition_pin = self.write(followup / "inputs/acquisition_receipt.json", acquired)
        entry = {"seed": seed, "gpu": 0, "material": material_pin, "spec_sha256": material["spec"]["sha256"],
                 "fit_inputs": trained_pin, "c0_inputs": cold_pin, "allocation": allocation_pin}
        fit_inputs, results = [], []
        correct = {"B200_NEW_DOSE": (8, 12, 13), "B400_FIXED_WORK": (12, 13, 14, 15),
                   "REPLAY400": (0, 1, 8, 9, 10, 12, 13, 14), "CLEAN_CUM600": range(8, 16)}
        for phase in api.operator.PHASES:
            inputs = {**trained, "acquisition_receipt": request, "predecessor": None if phase == "CLEAN_CUM600" else parent}
            fit_pin = self.write(followup / f"inputs/{phase}_inputs.json", inputs)
            fit_inputs.append(fit_pin)
            fit_root = followup / f"runs/{phase}_fit_outer"
            receipt_pin = self.fit(fit_root, phase, fit_pin, material, acquired)
            collection = self.outer(fit_root, "fit", phase, fit_pin, allocation_pin)
            results.append({"phase": phase, "stage": "fit", "inputs": fit_pin, "collection": collection})
            read_pin = self.write(followup / f"inputs/{phase}_readout_inputs.json", {**cold, "fit_receipt": receipt_pin})
            read_root = followup / f"runs/{phase}_readout_outer"
            self.state(read_root, phase, read_pin, material, correct[phase])
            collection = self.outer(read_root, "readout", phase, read_pin, allocation_pin)
            results.append({"phase": phase, "stage": "readout", "inputs": read_pin, "collection": collection})
        manifest = self.write(followup / "manifest.json", {"schema": api.operator.SCHEMA, "status": "READY", "seed": seed, "gpu": 0,
            "source_root": str(Path(api.__file__).resolve().parents[1]), "root": str(followup), "phases": list(api.operator.PHASES),
            "counts": api.operator.COUNTS, "entry": entry, "originals": originals, "pins": originals,
            "fit_inputs": fit_inputs, "acquisition_request": request, "acquisition_receipt": acquisition_pin,
            "runtime_c0_inputs": self.write(followup / "inputs/runtime_c0_inputs.json", cold), "repair": None, "prior_failure": None,
            "initial_outer_seconds": 300, "remaining_seconds": 6900, "automatic_promotion": False, "no_automatic_retry": True})
        completed = self.write(followup / "completed.json", {"status": "CAPTURED_NOT_PROMOTED", "results": results,
            "elapsed_seconds": 800, "automatic_promotion": False})
        return {"manifest": manifest, "completed": completed}



class ReducerTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.ReadoutV2Tests("test_cold_c0_seed_bound_no_write_exact_roster")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.builder = FollowupFixture(fixture)

    def reduce(self, binding):
        return api.reduce_followup(binding["manifest"], binding["completed"], expected_kind=KIND)

    def test_complete_raw_vectors_contrasts_and_immutable_evidence(self):
        binding = self.builder.build()
        before = api.inventory(self.builder.harness.root)
        with patch.object(api.reader, "ReadoutActor", side_effect=AssertionError("no model launch")), \
                patch.object(api.sequence.trainer, "run_training", side_effect=AssertionError("no training")):
            result = self.reduce(binding)
        self.assertEqual(api.inventory(self.builder.harness.root), before)
        api.sealed(result)
        self.assertEqual(set(result["states"]), {"NO_WRITE", "A200", *api.operator.PHASES})
        for state in result["states"].values():
            self.assertEqual((state["denominator"], len(state["results"]), len(state["captures"]), len(state["strict_stop"])), (16,) * 4)
            self.assertTrue(state["gpu_released"])
            for view in ("W0", "W8"):
                for bank in ("A", "B"):
                    panel = state["panels"][view][bank]
                    self.assertEqual((panel["denominator"], len(panel["strict_stop"])), (4, 4))
        panel = result["paired_contrasts"]["REPLAY400-B200_NEW_DOSE"]["W8"]
        self.assertEqual(panel["A"]["paired_delta"], [0, 1, 1, 0])
        self.assertEqual(panel["B"]["rate_difference"], .25)
        self.assertEqual(result["paired_contrasts"]["REPLAY400-B400_FIXED_WORK"]["W8"]["B"]["rate_difference"], -.25)
        self.assertEqual(result["phase_boundary_descriptive"]["panels"]["W8"]["A"]["rate_difference"], -.25)
        self.assertIsNone(result["fits"]["CLEAN_CUM600"]["predecessor"])
        for phase in api.operator.PHASES[:3]:
            self.assertEqual(result["fits"][phase]["predecessor"], result["fits"]["A200"]["receipt"])
            self.assertIn("adapter_model.safetensors", result["fits"][phase]["checkpoint_inventory"])
        self.assertFalse(result["automatic_promotion"])
        self.assertEqual(result["total_physical_work"], dict(fits=5, updates=1800, presentations=7200, readout_calls=96))
        with self.assertRaises(ValueError):
            api.reduce_followup(binding["manifest"], binding["completed"])

    def test_missing_and_wrong_phase_branches_rejected(self):
        binding = self.builder.build()
        original = api.pinned(binding["completed"])
        for mutation in (lambda value: value["results"].pop(),
                         lambda value: value["results"][0].update(phase="REPLAY400"),
                         lambda value: value["results"][1].update(stage="fit")):
            completed = copy.deepcopy(original)
            mutation(completed)
            binding["completed"] = self.builder.write(binding["completed"]["path"], completed)
            with self.subTest(completed=completed["results"][0]["phase"]), self.assertRaises(ValueError):
                self.reduce(binding)

    def test_resealed_raw_score_drift_rejected(self):
        binding = self.builder.build()
        completed = api.pinned(binding["completed"])
        row = completed["results"][5]
        root = Path(row["collection"]["path"]).parent
        score_path = root / "readout/scores.json"
        scores = api.read(score_path)
        scores["results"][8]["strict_stop"] = False
        self.builder.write(score_path, scores)
        row["collection"] = self.builder.refresh(root, "readout")
        binding["completed"] = self.builder.write(binding["completed"]["path"], completed)
        with self.assertRaisesRegex(ValueError, "recorded score differs from raw"):
            self.reduce(binding)

    def test_missing_raw_capture_and_changed_checkpoint_rejected(self):
        binding = self.builder.build()
        completed = api.pinned(binding["completed"])
        root = Path(completed["results"][5]["collection"]["path"]).parent
        (root / "readout/actor/call_0008.raw.json").unlink()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.reduce(binding)
        fit_root = Path(completed["results"][4]["collection"]["path"]).parent
        (fit_root / "fit/checkpoint/adapter_model.safetensors").write_bytes(b"CHANGED SYNTHETIC CHECKPOINT")
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.reduce(binding)

    def test_wrong_parent_phase_seed_model_and_warm_receipts_rejected(self):
        binding = self.builder.build()
        plan = api.pinned(binding["manifest"])
        material = api.pinned(plan["entry"]["material"])
        completed = api.pinned(binding["completed"])
        fit_root = Path(completed["results"][4]["collection"]["path"]).parent / "fit"
        original = api.read(fit_root / "completed.json")
        inputs = api.pinned(original["inputs"])
        parent = original["predecessor"]
        for changes in ({"predecessor": None}, {"parent_phase": None}, {"phase": "B400_FIXED_WORK"},
                        {"predecessor": api.file_pin(fit_root / "completed.json")}, {"learner_seed": 0},
                        {"model_binding": {"path": inputs["model_binding"]["path"], "sha256": "0" * 64}},
                        {"warm_start": {**original["warm_start"], "parent_path": "/not-the-measured-parent"}}):
            receipt_pin = self.builder.write(fit_root / "completed.json", {**original, **changes}, seal=True)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                api.check_fit(receipt_pin, "REPLAY400", material, inputs, KIND, parent)

    def test_resealed_unreleased_fit_rejected(self):
        binding = self.builder.build()
        completed = api.pinned(binding["completed"])
        row = completed["results"][0]
        collection = api.pinned(row["collection"])
        row["collection"] = self.builder.write(row["collection"]["path"], {**collection, "gpu_released": False}, seal=True)
        binding["completed"] = self.builder.write(binding["completed"]["path"], completed)
        with self.assertRaisesRegex(ValueError, "completion/release"):
            self.reduce(binding)

    def test_original_acquisition_validator_is_not_bypassed(self):
        binding = self.builder.build()
        plan = api.pinned(binding["manifest"])
        completed = api.pinned(binding["completed"])
        row = completed["results"][5]
        with self.assertRaisesRegex(ValueError, "A200 clean C0 parent"):
            api.acquisition.state_result(Path(row["collection"]["path"]).parent, "REPLAY400", row["collection"]["sha256"],
                api.pinned(plan["entry"]["material"]), plan["entry"]["material"]["sha256"], KIND)

    def test_versioned_overlay_preserves_material_paths_and_limits_source_delta(self):
        cold = self.builder.fixture.inputs
        original = Path(readout.fit.__file__).resolve()
        outer = original.with_name("astra_pcfl_event_sequence_v2_outer.py")
        root = self.builder.harness.root / "overlay"
        (root / "gpu").mkdir(parents=True)
        replacement, relocated = root / "gpu" / original.name, root / "gpu" / outer.name
        lines = original.read_text().splitlines(keepends=True)
        function = next(node for node in ast.parse(original.read_text()).body
                        if isinstance(node, ast.FunctionDef) and node.name == "validate_warm_tensors")
        docstring = function.body[0]
        lines[docstring.lineno - 1:docstring.end_lineno] = ['    """Synthetic CPU overlay; validation code remains unchanged."""\n']
        replacement.write_text("".join(lines))
        relocated.write_bytes(outer.read_bytes())
        repair = {"schema": "pcfl.event_sequence.v2.warm_repair.v1", "scope": "validate_warm_tensors_only",
            "original_root": str(original.parents[1]), "source_root": str(root),
            "original": api.file_pin(original), "replacement": api.file_pin(replacement),
            "outer_original": api.file_pin(outer), "outer_relocated": api.file_pin(relocated)}
        repair["receipt"] = self.builder.write(root / "warm_repair.json", repair)
        sources = dict(cold["source_files"])
        sources.pop(str(original))
        sources[str(replacement)] = api.file_hash(replacement)
        runtime_pin = self.builder.write(root / "runtime_c0_inputs.json", {**cold, "source_files": sources})
        plan = {"source_root": str(root), "repair": repair, "runtime_c0_inputs": runtime_pin}
        runtime = api.runtime_cold(plan, cold)
        self.assertEqual(api.original_sources(runtime["source_files"], repair), cold["source_files"])
        for path, checksum in self.builder.fixture.material["spec"]["sources"].items():
            self.assertEqual(runtime["source_files"][path], checksum)
        bad_runtime = {**runtime, "learner_seed": 0}
        plan["runtime_c0_inputs"] = self.builder.write(root / "wrong_runtime.json", bad_runtime)
        with self.assertRaisesRegex(ValueError, "only approved runtime C0"):
            api.runtime_cold(plan, cold)
        replacement.write_text(replacement.read_text() + "\nUNRELATED_CHANGE = True\n")
        with self.assertRaisesRegex(ValueError, "outside declared validators"):
            api.repair_scope(original, replacement, "validate_warm_tensors_only")

    def test_preworker_failure_cost_is_bound_and_not_erased(self):
        binding = self.builder.build()
        plan = api.pinned(binding["manifest"])
        previous_root = self.builder.harness.root / "previous_followup"
        previous_pin = self.builder.write(previous_root / "manifest.json", {**plan, "root": str(previous_root)})
        failed_root = previous_root / "runs/B200_NEW_DOSE_fit_outer"
        self.builder.write(failed_root / "failure.json", {"error": "SYNTHETIC missing explicitly-empty controller CVD"})
        collection = {"schema": api.OUTER_SCHEMA + "/collection", "phase": "B200_NEW_DOSE", "status": "FAILED",
            "worker_identity": None, "returncode": None, "stage_inventory": {}, "retries": 0,
            "elapsed_seconds": 6, "files": api.inventory(failed_root)}
        collection_pin = self.builder.write(failed_root / "collection.json", collection, seal=True)
        stopped = {"status": "STOPPED", "phase": "B200_NEW_DOSE", "stage": "fit", "elapsed_seconds": 8,
                   "results": [{"phase": "B200_NEW_DOSE", "stage": "fit", "collection": collection_pin}]}
        failure_pin = self.builder.write(previous_root / "stopped.json", stopped)
        plan.update(prior_failure=failure_pin, initial_outer_seconds=308, remaining_seconds=6892,
                    pins=[*plan["pins"], failure_pin, previous_pin, collection_pin])
        binding["manifest"] = self.builder.write(binding["manifest"]["path"], plan)
        result = self.reduce(binding)
        self.assertEqual(result["elapsed_seconds"], {"initial_collections": 300, "prior_failure": 8, "followup": 800, "total": 1108})
        self.assertTrue(result["prior_failure"]["recorded_preworker_only"])
        binding["manifest"] = self.builder.write(binding["manifest"]["path"], {**plan, "initial_outer_seconds": 300, "remaining_seconds": 6900})
        with self.assertRaisesRegex(ValueError, "prior-failure elapsed accounting"):
            self.reduce(binding)
        for changes in ({"worker_identity": {"pid": 123}}, {"stage_inventory": {"completed.json": {}}}):
            changed_pin = self.builder.write(failed_root / "collection.json", {**collection, **changes}, seal=True)
            stopped["results"][0]["collection"] = changed_pin
            failed_pin = self.builder.write(previous_root / "stopped.json", stopped)
            modified = {**plan, "prior_failure": failed_pin, "pins": [previous_pin, failed_pin, changed_pin]}
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "may have executed a worker"):
                api.prior_failure_evidence(modified)

    def test_prospective_two_module_scope_and_runtime_allocation(self):
        original_root = self.builder.harness.root / "original_sources"
        replacement_root = self.builder.harness.root / "prospective_sources"
        for root in (original_root, replacement_root):
            (root / "gpu").mkdir(parents=True)
        actual_fit = Path(readout.fit.__file__).resolve()
        actual_outer = actual_fit.with_name("astra_pcfl_event_sequence_v2_outer.py")
        pins = {}
        for actual, original_key, replacement_key in ((actual_fit, "original", "replacement"),
                                                       (actual_outer, "outer_original", "outer_replacement")):
            source = actual.read_text()
            tree = ast.parse(source)
            wrapper = "validate_predecessor_for_write" if original_key == "original" else "_inputs_for_write"
            wrapper_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == wrapper)
            tree.body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name == wrapper)]
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "validate_predecessor_for_write":
                    node.func.id = "validate_predecessor"
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_inputs_for_write":
                    node.func.id = "_inputs"
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "validate_predecessor_for_write":
                    node.func.attr = "validate_predecessor"
            old, new = original_root / "gpu" / actual.name, replacement_root / "gpu" / actual.name
            if original_key == "outer_original":
                lines = source.splitlines(keepends=True)
                del lines[wrapper_node.lineno - 1:wrapper_node.end_lineno]
                old.write_text("".join(lines).replace("_inputs_for_write(", "_inputs("))
            else:
                old.write_text(ast.unparse(tree) + "\n")
            new.write_bytes(actual.read_bytes())
            pins.update({original_key: api.file_pin(old), replacement_key: api.file_pin(new)})
        repair = {"schema": "pcfl.event_sequence.v2.warm_repair.v1", "scope": api.PROSPECTIVE_SCOPE,
                  "original_root": str(original_root), "source_root": str(replacement_root), **pins}
        repair["receipt"] = self.builder.write(replacement_root / "warm_repair.json", repair)
        cold = {**self.builder.fixture.inputs, "source_files": {pins[key]["path"]: pins[key]["sha256"] for key in ("original", "outer_original")}}
        runtime = {**cold, "source_files": {pins[key]["path"]: pins[key]["sha256"] for key in ("replacement", "outer_replacement")}}
        allocation = {"gpu_uuid": cold["gpu_uuid"], "outer_sha256": pins["outer_original"]["sha256"]}
        original_allocation = self.builder.write(original_root / "allocation.json", allocation)
        current_allocation = self.builder.write(replacement_root / "allocation.json", {**allocation, "outer_sha256": pins["outer_replacement"]["sha256"]})
        plan = {"source_root": str(replacement_root), "repair": repair, "entry": {"allocation": original_allocation},
                "runtime_c0_inputs": self.builder.write(replacement_root / "runtime_c0_inputs.json", runtime),
                "runtime_allocation": current_allocation}
        self.assertEqual(api.runtime_cold(plan, cold), runtime)
        self.assertEqual(api.runtime_allocation(plan), current_allocation)
        self.assertEqual(api.original_sources(runtime["source_files"], repair), cold["source_files"])
        bad = self.builder.write(replacement_root / "wrong_gpu.json", {**api.pinned(current_allocation), "gpu_uuid": "GPU-WRONG"})
        with self.assertRaisesRegex(ValueError, "may change only outer source"):
            api.runtime_allocation({**plan, "runtime_allocation": bad})

    def test_final_requires_three_same_bank_seeds_and_cli(self):
        followups = [self.builder.build(seed) for seed in (2, 0, 1)]
        request = {"schema": api.SCHEMA + "/request", "followups": followups}
        pin = self.builder.write(self.builder.harness.root / "request.json", request)
        result = api.reduce(pin, expected_kind=KIND)
        self.assertEqual(result["learner_seeds"], [0, 1, 2])
        self.assertEqual(result["independent_banks"], 1)
        self.assertEqual(result["descriptive_paired_summary"]["REPLAY400-B200_NEW_DOSE"]["panels"]["W8"]["A"]["denominator"], 12)
        self.assertIn("No significance", result["interpretation"])
        for entries in (followups[:2], [followups[0]] * 3):
            bad_pin = self.builder.write(self.builder.harness.root / "bad_request.json", {**request, "followups": entries})
            with self.assertRaises(ValueError):
                api.reduce(bad_pin, expected_kind=KIND)
        process = subprocess.run([sys.executable, "-B", "-m", "gpu.astra_pcfl_event_sequence_v2_reduce_followup", "--help"],
                                 capture_output=True, text=True, cwd=Path(api.__file__).resolve().parents[1])
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--request-sha256", process.stdout)

    def test_failed_warm_fit_and_earlier_preworker_costs_are_retained(self):
        binding = self.builder.build(0)
        plan = api.pinned(binding["manifest"])
        early_root = self.builder.harness.root / "preworker_attempt"
        early_manifest = self.builder.write(early_root / "manifest.json", {**plan, "root": str(early_root)})
        early_collection = self.builder.write(early_root / "runs/B200_NEW_DOSE_fit_outer/collection.json",
            {"schema": api.OUTER_SCHEMA + "/collection", "phase": "B200_NEW_DOSE", "status": "FAILED",
             "worker_identity": None, "returncode": None, "stage_inventory": {}, "files": {}, "retries": 0,
             "elapsed_seconds": 6}, seal=True)
        early_stopped = self.builder.write(early_root / "stopped.json", {"status": "STOPPED", "phase": "B200_NEW_DOSE",
            "stage": "fit", "elapsed_seconds": 8, "results": [{"collection": early_collection}]})
        prior_root = self.builder.harness.root / "failed_warm_attempt"
        failed_root = prior_root / "runs/B200_NEW_DOSE_fit_outer"
        successful_root = Path(api.pinned(binding["completed"])["results"][0]["collection"]["path"]).parent
        shutil.copytree(successful_root, failed_root)
        (failed_root / "fit/completed.json").unlink()
        (failed_root / "fit_completed.json").unlink()
        failure = {"kind": KIND, "message": "full parent tensor coverage differs", "partial_checkpoint_not_eligible": True,
                   "phase": "B200_NEW_DOSE", "status": "FAILED", "type": "ActorError"}
        failure_pin = self.builder.write(failed_root / "fit/failure.json", failure)
        train_pin = api.file_pin(failed_root / "fit/checkpoint/train_manifest.json")
        self.builder.write(failed_root / "worker_exit.json", {**api.read(failed_root / "worker_exit.json"), "returncode": 1})
        collection = api.read(failed_root / "collection.json")
        collection.update(status="FAILED", returncode=1, completed_sha256=None,
            stage_inventory=api.inventory(failed_root / "fit"),
            files={name: entry for name, entry in api.inventory(failed_root).items() if name != "collection.json"})
        collection_pin = self.builder.write(failed_root / "collection.json", collection, seal=True)
        stopped_pin = self.builder.write(prior_root / "stopped.json", {"status": "STOPPED", "phase": "B200_NEW_DOSE", "stage": "fit",
            "elapsed_seconds": 110, "results": [{"collection": collection_pin}]})
        repair = {"original": api.file_pin(Path(readout.fit.__file__).resolve())}
        previous = {**plan, "root": str(prior_root), "repair": repair, "prior_failure": early_stopped,
            "initial_outer_seconds": 308, "remaining_seconds": 6892,
            "pins": [*plan["pins"], early_manifest, early_collection, early_stopped]}
        previous_pin = self.builder.write(prior_root / "manifest.json", previous)
        current = {**plan, "repair": repair, "prior_failure": stopped_pin,
            "prior_failed_work": dict(fits=1, updates=200, presentations=800, readout_calls=0),
            "pins": [*plan["pins"], previous_pin, stopped_pin, collection_pin, failure_pin, train_pin]}
        evidence = api.prior_failure_evidence(current, expected_kind=KIND)
        self.assertEqual(evidence["elapsed_seconds"], 118)
        self.assertEqual(evidence["cumulative_failed_work"], current["prior_failed_work"])
        self.assertFalse(evidence["partial_fit"]["checkpoint_eligible"])
        self.assertTrue(evidence["earlier_failure"]["recorded_preworker_only"])
        for bad_work in (dict(fits=0, updates=0, presentations=0, readout_calls=0),
                         dict(fits=1, updates=200, presentations=800, readout_calls=16)):
            with self.subTest(work=bad_work), self.assertRaisesRegex(ValueError, "failed work differs"):
                api.prior_failure_evidence({**current, "prior_failed_work": bad_work}, expected_kind=KIND)
        collector_root = self.builder.harness.root / "failed_collector_attempt/runs/B200_NEW_DOSE_fit_outer"
        material = api.pinned(plan["entry"]["material"])
        inputs_pin = plan["fit_inputs"][0]
        parent = api.pinned(inputs_pin)["predecessor"]
        self.builder.fit(collector_root, "B200_NEW_DOSE", inputs_pin, material, api.pinned(plan["acquisition_receipt"]))
        self.builder.outer(collector_root, "fit", "B200_NEW_DOSE", inputs_pin, plan["entry"]["allocation"])
        collector = api.read(collector_root / "collection.json")
        collector.update(status="FAILED", errors=api.COLLECTOR_ERRORS, completed_sha256=None)
        self.builder.write(collector_root / "failure.json", {"errors": api.COLLECTOR_ERRORS})
        collector["files"] = {name: entry for name, entry in api.inventory(collector_root).items() if name != "collection.json"}
        collector_pin = self.builder.write(collector_root / "collection.json", collector, seal=True)
        collector_stopped = self.builder.write(collector_root.parents[1] / "stopped.json", {"status": "STOPPED", "phase": "B200_NEW_DOSE",
            "stage": "fit", "elapsed_seconds": 110, "results": [{"collection": collector_pin}]})
        collector_plan = self.builder.write(collector_root.parents[1] / "manifest.json", {**current,
            "root": str(collector_root.parents[1]), "initial_outer_seconds": 418, "remaining_seconds": 6782})
        prospective = {**plan, "repair": repair, "prior_failure": collector_stopped,
            "prior_failed_work": dict(fits=2, updates=400, presentations=1600, readout_calls=0),
            "pins": [*plan["pins"], collector_plan, collector_stopped, collector_pin]}
        before = api.inventory(collector_root)
        chained = api.prior_failure_evidence(prospective, expected_kind=KIND)
        self.assertEqual(api.inventory(collector_root), before)
        self.assertEqual(chained["elapsed_seconds"], 228)
        self.assertEqual(chained["cumulative_failed_work"], prospective["prior_failed_work"])
        self.assertEqual(chained["partial_fit"]["worker_status"], "COMPLETE")
        self.assertEqual(chained["partial_fit"]["collection_status"], "FAILED")
        self.assertFalse(chained["partial_fit"]["readout_eligible"])
        for changes in ({"errors": [{**api.COLLECTOR_ERRORS[0], "phase": "post_inputs"}]},
                        {"automatic_promotion": True},
                        {"observations": {**collector["observations"], "worker_release": {
                            **collector["observations"]["worker_release"], "unbound": True}}}):
            changed = self.builder.write(collector_root / "collection.json", {**collector, **changes}, seal=True)
            stopped = self.builder.write(collector_stopped["path"], {"status": "STOPPED", "phase": "B200_NEW_DOSE",
                "stage": "fit", "elapsed_seconds": 110, "results": [{"collection": changed}]})
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                api.prior_failure_evidence({**prospective, "prior_failure": stopped,
                    "pins": [*plan["pins"], collector_plan, stopped, changed]}, expected_kind=KIND)
        self.builder.write(collector_pin["path"], collector, seal=True)
        self.builder.write(collector_stopped["path"], {"status": "STOPPED", "phase": "B200_NEW_DOSE",
            "stage": "fit", "elapsed_seconds": 110, "results": [{"collection": collector_pin}]})
        with self.assertRaisesRegex(ValueError, "completion/release"):
            api.fit_result(collector_pin, "B200_NEW_DOSE", inputs_pin, plan["entry"]["allocation"], material, KIND, parent)
        work = [api.physical_work(failed) for failed in (prospective["prior_failed_work"], current["prior_failed_work"], current["prior_failed_work"])]
        self.assertEqual({key: sum(row[key] for row in work) for key in api.MAX_PHYSICAL_WORK}, api.MAX_PHYSICAL_WORK)
        bad_plan = self.builder.write(binding["manifest"]["path"], {**plan, "recovered_b200": {"original_collection": collector_pin}})
        with self.assertRaisesRegex(ValueError, "recovery is inadmissible"):
            api.reduce_followup(bad_plan, binding["completed"], expected_kind=KIND)


if __name__ == "__main__":
    unittest.main()
