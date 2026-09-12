"""CPU stubs only: no model/tokenizer loading, tensor reads, subprocesses or GPUs."""
from contextlib import ExitStack
import copy
import datetime as dt
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("interleaved_pair_test", "/tmp/astra_interleaved_memory_replication_20260912.py")
side = importlib.util.module_from_spec(spec)
spec.loader.exec_module(side)
side.memory, side.common = side.load("memory"), side.load("common")
side.memory.bind(Path.cwd(), "/tmp/astra_fading_sentinel_20260912.py")
for name in ("old", "base", "trainer", "dev", "exact"):
    setattr(side, name, getattr(side.memory, name))
from organism_v6 import interleaved_memory_replay_corpus
side.material = interleaved_memory_replay_corpus


class Tokenizer:
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert len(messages) == 1 and messages[0]["role"] == "user"
        assert tokenize is False and add_generation_prompt is True
        return "<user>" + messages[0]["content"] + "</user><assistant>"

    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]


def plan_fixture(root, seed=1):
    root = Path(root)
    lease = time.time()+86400
    model, model_files = str(root.parent / "model"), {"config.json": "model"}
    templates = {name: side.memory.template(module, model, model_files, Tokenizer(), "1", lease)
        for name, module in (("dev", side.dev), ("exact", side.exact))}
    templates["lexical"] = side.cue_template(model, model_files, Tokenizer(), "1", lease)
    parentroot = root.parent / f"original{seed}"
    parent = dict(parent=str(parentroot / "fit_teach/adapter"), parent_files={"adapter_model.safetensors": "parent"},
        provenance={}, readout_files={}, readout=copy.deepcopy(templates["dev"]))
    state = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="before")}
    return dict(schema=side.SCHEMA, source_commit=side.SOURCE_ID, root=str(root), source_root=str(side.base.REPO), source_hashes=side.sources(),
        parentroot=str(parentroot), model=model, model_files=model_files, python=side.python(), seed=seed, parent_pin=list(side.memory.PINS[str(seed)]), device="1", parent=parent, parent_state=state,
        materialroot=str(root.parent / "material"), material_parentroot=str(root.parent / "original0"),
        seed0_gate=dict(path="/fixture/gate.json", sha256="a"*64, seed0_root=str(root.parent / "seed0"), evidence_hashes={}), material_files={arm+".json": arm for arm in side.ARMS},
        config=side.config(model, seed), accounting=side.COUNTS, templates=templates, arm_order=list(side.ARMS), panels=side.PANELS,
        pair_seconds=1800, cleanup_seconds=140, external_custody_seconds=300, lease_margin_seconds=21600, deadline=time.time()+4000, real_lease_end=lease,
        calls_per_arm=112, total_calls=224, confirmation_calls=0, progression=side.PROGRESSION,
        reduce_only_after_both_captures=True, outcome_selective_skips=False, claim=side.CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY",
        input_compute_matched=False, memory_target_mass_fraction=.128)


def receipt():
    return dict(ok=True, error=None, returncode=0, device="1", reserved_seconds=1.,
        reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True)


def manifest_fixture(plan, arm):
    state = plan["parent_state"]
    saved = {"lora": dict(shape=[2, 2], dtype="torch.float32", sha256="after")}
    expected, parent = side.COUNTS[arm], plan["parent"]
    warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=parent["parent"], parent_files=parent["parent_files"],
        parent_files_after=parent["parent_files"], parent_unchanged=True, base_frozen=True, initialized_loaded_state_check=True,
        phase_seed=plan["seed"], adapter_count=1, optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
        optimizer_initialization="fresh_per_write", phase_steps=320, parent_cumulative_steps=80, cumulative_steps=400,
        source_state=state, initialized_state=state, final_state=saved, dtype_conversions={})
    return dict(config=copy.deepcopy(plan["config"]), base_model=plan["model"], steps=320, micro_batches=320, epochs_run=10,
        nonfinite_batches=0, empty=False, final_loss=1., corpus=dict(sha256=arm, n_items=128, n_encoded=128, n_skipped_no_target=0),
        truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
        tokens=dict(total=expected["input_per_epoch"], context=expected["context_per_epoch"], target=1000),
        train_tokens_seen=expected["input_presentations"], warm_start=warm), saved


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.plan = plan_fixture("/fixture/fits")

    def test_fixed_224_calls_without_confirmation(self):
        self.assertEqual({key: len(value["requests"]) for key, value in self.plan["templates"].items()}, side.PANELS)
        self.assertEqual(sum(side.PANELS.values()) * 2, 224)
        dev_ids = [case["id"] for case in self.plan["templates"]["dev"]["cases"]]
        self.assertEqual(dev_ids[:32], [f"eval-addition-{index:03d}" for index in range(32)])
        self.assertTrue(all(not key.startswith("eval-unknown") for key in dev_ids))
        self.assertEqual(len(side.cue_cases()), 48)
        self.assertEqual(len({row["device"] for row in side.cue_cases()}), 16)

    def test_lexical_exact_material_prompt_only_fixed_sampling(self):
        cases = side.cue_cases()
        self.assertEqual([row["context"] for row in cases], [row["context"] for row in side.material.build_candidate()["heldout_cues"]])
        for row, request in zip(cases, side.cue_requests(cases)):
            self.assertEqual(request["prompt"], row["context"])
            self.assertEqual((request["temperature"], request["seed"], request["max_tokens"]), (0., 20260912, 64))
            self.assertNotRegex(request["prompt"], r"\b(red|green|blue|yellow)\b")
        cases[0]["context"] += " reminder"
        with self.assertRaisesRegex(ValueError, "fixed lexical"): side.cue_requests(cases)

    def test_frozen_commands_original_parent_independent(self):
        adapters = []
        for arm in side.ARMS:
            adapter = Path(self.plan["root"]) / "run" / arm / "adapter"
            command = side.fit_command(self.plan, arm, adapter)
            adapters.append(command[command.index("--out")+1])
            self.assertEqual(command[command.index("--init-adapter")+1], self.plan["parent"]["parent"])
            for key, value in (("--rank", "8"), ("--lr", "0.0003"), ("--epochs", "10"), ("--seed", "1"), ("--batch-size", "4")):
                self.assertEqual(command[command.index(key)+1], value)
            self.assertIn("--no-pack", command)
            self.assertNotIn("--chat-template", command)
        self.assertEqual(len(set(adapters)), 2)

    def test_virtualenv_executable_not_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, alias = Path(tmp) / "python-real", Path(tmp) / "venv-python"
            target.write_bytes(b"fixture")
            alias.symlink_to(target)
            with patch.object(side.sys, "executable", str(alias)):
                self.assertEqual(side.python(), str(alias))
                plan = dict(self.plan, python=side.python())
                self.assertEqual(side.fit_command(plan, "SINGLE_VIEW", Path(plan["root"]) / "run/SINGLE_VIEW/adapter")[0], str(alias))
                self.assertEqual(side.worker_command(plan, Path("/tmp/lexical"), "lexical")[0], str(alias))

    def test_commands_new_lexical_worker_and_unchanged_dev_exact(self):
        for name in side.PANELS:
            command = side.worker_command(self.plan, Path("/fixture") / name, name)
            self.assertEqual(command[0], self.plan["python"])
            self.assertIn("--allow-gpu", command)
            self.assertIn("_cue-worker" if name == "lexical" else "_worker", command)
        self.assertIn(side.SOURCE_ID, side.SOURCE_ID)

    def test_native_fit_manifests_and_fresh_optimizer(self):
        for arm in side.ARMS:
            manifest, saved = manifest_fixture(self.plan, arm)
            side.validate_manifest(self.plan, arm, manifest, self.plan["parent_state"], saved)
            for key, value in (("optimizer_initial_state_entries", 1), ("parent_cumulative_steps", 400), ("phase_seed", 0), ("adapter_count", 2)):
                bad = copy.deepcopy(manifest)
                bad["warm_start"][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    side.validate_manifest(self.plan, arm, bad, self.plan["parent_state"], saved)

    def test_drops_nonfinite_and_steps_fail_closed(self):
        manifest, saved = manifest_fixture(self.plan, "SINGLE_VIEW")
        for key, value in (("steps", 319), ("micro_batches", 321), ("nonfinite_batches", 1), ("final_loss", float("nan"))):
            bad = copy.deepcopy(manifest)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, "SINGLE_VIEW", bad, self.plan["parent_state"], saved)
        manifest["truncation"]["items_truncated"] = 1
        with self.assertRaises(ValueError): side.validate_manifest(self.plan, "SINGLE_VIEW", manifest, self.plan["parent_state"], saved)

    def test_bounds_fixed1800_not_six_hour_lease(self):
        self.assertEqual(side.bounds(1000., 10000., 24700.), 2800.)
        for end, lease in ((2799., 10000.), (2800., 3109.), (float("nan"), 10000.), (True, 10000.)):
            with self.subTest(end=end, lease=lease), self.assertRaises(ValueError): side.bounds(1000., end, lease)
        with patch.object(side.time, "time", return_value=2650.):
            with self.assertRaisesRegex(ValueError, "150s"): side.budget(2800.)

    def test_plan_contract_mutations_rejected(self):
        with patch.object(side.old, "read_plan", return_value=self.plan):
            side.verify(Path(self.plan["root"]), current=False)
            for key, value in (("seed", 0), ("pair_seconds", 1900), ("total_calls", 128), ("confirmation_calls", 1),
                ("memory_target_mass_fraction", .5), ("reduce_only_after_both_captures", False)):
                bad = dict(self.plan, **{key: value})
                with patch.object(side.old, "read_plan", return_value=bad), self.subTest(key=key), self.assertRaises(ValueError):
                    side.verify(Path(self.plan["root"]), current=False)

    def test_all_six_captures_before_first_reducer_and_no_score_selection(self):
        captured = {arm: dict(fit={}, captures={name: {} for name in side.PANELS}) for arm in side.ARMS}
        sequence = []
        def capture(*args): sequence.append("capture"); return {}
        def reduce(root, count):
            self.assertEqual(sequence.count("capture"), 6)
            sequence.append("reduce")
            return dict(complete=True, counts=dict(total=count, correct=0))
        with patch.object(side, "capture_receipt", side_effect=capture), patch.object(side.old, "write"), \
            patch.object(side.base, "digest", return_value="hash"), patch.object(side.dev, "reduce", side_effect=lambda root: reduce(root, 48)), \
            patch.object(side.exact, "reduce", side_effect=lambda root: reduce(root, 16)), \
            patch.object(side, "cue_reduce", side_effect=lambda root, plan: reduce(root, 48)):
            result = side.reduce_pair(Path("/fixture"), self.plan, captured, time.time()+1800)
        self.assertEqual(sequence, ["capture"]*6 + ["reduce"]*6)
        self.assertEqual(set(result), set(side.ARMS))
        self.assertFalse(side.PROGRESSION["automatic_progression"])
        self.assertEqual(side.PROGRESSION["each_lexical_family_min"], 15)

    def test_missing_arm_or_panel_blocks_all_reductions(self):
        with patch.object(side.dev, "reduce") as reducer:
            with self.assertRaises(ValueError): side.reduce_pair(Path("/fixture"), self.plan, {}, time.time()+1800)
            captured = {arm: dict(captures={}) for arm in side.ARMS}
            with self.assertRaises(ValueError): side.reduce_pair(Path("/fixture"), self.plan, captured, time.time()+1800)
            reducer.assert_not_called()

    def test_execute_arm_fit_plus_three_workers_no_reduce(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits"
            root.mkdir()
            (root / "run").mkdir()
            plan = plan_fixture(root)
            fit = dict(adapter=str(root / "run/SINGLE_VIEW/adapter"), adapter_files={"weight": "child"})
            commands = []
            def supervise(parent, readplan, stage, command, *args):
                commands.append(command)
                return receipt()
            with patch.object(side.base, "supervise", side_effect=supervise), patch.object(side, "verify_fit", return_value=fit), \
                patch.object(side, "capture_receipt", return_value={}), patch.object(side.trainer, "_warm_inventory", return_value=fit["adapter_files"]), \
                patch.object(side.base, "expected_identity", return_value={"fixture": "child"}), patch.object(side.dev, "reduce") as reducer:
                result = side.execute_arm(root, plan, "SINGLE_VIEW", time.time()+1800)
            self.assertEqual(len(commands), 4)
            self.assertEqual(set(result["captures"]), set(side.PANELS))
            reducer.assert_not_called()
            with self.assertRaises(ValueError): side.execute_arm(root, plan, "SINGLE_VIEW", time.time()+1800)

    def test_run_without_launch_authority_reads_nothing(self):
        with patch.object(side.old, "read_plan") as reader, self.assertRaises(ValueError): side.run(Path("/none"))
        reader.assert_not_called()

    def test_wrong_source_cwd_and_helper_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "immutable"): side.bind(Path(tmp))
        with patch.dict(side.DEPENDENCIES, {"bad": (side.__file__, "0"*64)}):
            with self.assertRaisesRegex(ValueError, "helper pin"): side.load("bad")

    def test_run_failure_records_partial_release_without_next_arm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits"
            root.mkdir()
            plan = plan_fixture(root)
            side.old.seal(root, plan)
            now = time.time()
            with patch.object(side.base.supervisor, "selected_device", return_value="1"), \
                patch.object(side.base.supervisor, "gpu_processes_absent", return_value=True), \
                patch.object(side, "verify", return_value=plan), patch.object(side, "execute_arm", side_effect=RuntimeError("fixture failure")) as execute, \
                patch.object(side, "reduce_pair") as reducer:
                with self.assertRaisesRegex(ValueError, "partial pair"): side.run(root, True, (now, time.monotonic()))
            terminal = side.base.read(root / "run/terminal.json")
            self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")
            self.assertTrue(terminal["release_verified"])
            self.assertEqual(terminal["effective_deadline"], now+1800)
            self.assertEqual(execute.call_count, 1)
            reducer.assert_not_called()
            with self.assertRaises(ValueError): side.run(root, True)

    def test_native_prepare_reaudits_before_plan_with_padded_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits"
            plan = plan_fixture(root)
            materialroot = Path(plan["materialroot"])
            materialroot.mkdir()
            parentroot = Path(plan["parentroot"])
            parentroot.mkdir()
            side.old.write(parentroot / "teach.json", {})
            candidate = side.material.build_candidate()
            side.old.write(materialroot / "candidate.json", candidate)
            native = plan["templates"]["lexical"]["native_inputs"]
            audit = dict(tokenizer_class="fixture.NativeCPU", scheduled_costs={str(plan["seed"]): {"padded_input_slots": 123}},
                optimizer_update_schedule={str(plan["seed"]): ["fixture"]},
                heldout_prefixes=[dict(id=row["id"], rendered_context=rendered["rendered_prompt"], prefix_token_ids=rendered["prompt_token_ids"])
                    for row, rendered in zip(candidate["heldout_cues"], native)])
            exported = dict(audit=audit, corpora={arm: {"corpus": []} for arm in side.ARMS})
            side.old.write(materialroot / "token_audit.json", audit)
            for arm in side.ARMS: side.old.write(materialroot / (arm+".json"), exported["corpora"][arm])
            bound = {key: plan[key] for key in ("materialroot", "material_files", "parentroot", "model", "model_files", "material_parentroot")}
            with ExitStack() as stack:
                stack.enter_context(patch.object(side, "inspect_material", return_value=bound))
                stack.enter_context(patch.object(side, "gate_receipt", return_value=plan["seed0_gate"]))
                stack.enter_context(patch.object(side.base, "model_hashes", return_value=plan["model_files"]))
                stack.enter_context(patch.object(side.memory, "parent_record", return_value=plan["parent"]))
                stack.enter_context(patch.object(side.old, "state_inventory", return_value=plan["parent_state"]))
                stack.enter_context(patch.object(side.trainer, "_warm_inventory", return_value=plan["parent"]["parent_files"]))
                warm = stack.enter_context(patch.object(side.trainer, "_warm_parent"))
                stack.enter_context(patch.object(side.base, "native_tokenizer", return_value=Tokenizer()))
                export = stack.enter_context(patch.object(side.material, "export_native", return_value=exported))
                result = side.prepare(materialroot, root, "1", time.time()+4000, plan["real_lease_end"], plan["seed"], parentroot, "/fixture/gate", "a"*64)
                self.assertEqual(export.call_count, 1)
                sealed = side.old.read_plan(root)
                self.assertEqual(sealed["native_cpu_audit"]["padded_costs"], audit["scheduled_costs"][str(plan["seed"])])
                self.assertEqual(sealed["memory_target_mass_fraction"], .128)
                self.assertEqual(warm.call_count, 2)
                self.assertEqual({call.args[0] for call in warm.call_args_list}, {plan["parent"]["parent"]})
                self.assertEqual(result["status"], "PREPARED_REPLICATION_NOT_LAUNCHED")
                with self.assertRaises(ValueError): side.prepare(materialroot, root, "1", time.time()+4000, plan["real_lease_end"], plan["seed"], parentroot, "/fixture/gate", "a"*64)


class RawAndCollectionTests(unittest.TestCase):
    def make_panel(self, root, name="lexical"):
        parent = plan_fixture(root.parents[2])
        plan = parent["templates"][name]
        plan = dict(plan, adapter="/fixture/child", adapter_files={"weight": "child"})
        plan["identity"] = {"fixture": "child"}
        root.mkdir(parents=True)
        side.old.seal(root, plan)
        data = root / "run/data"
        calls = data / "calls"
        calls.mkdir(parents=True)
        worker = root / "run/worker"
        worker.mkdir()
        command = side.worker_command(parent, root, name)
        process = dict(pid=987654321, pgid=987654321, device="1", started=10., timeout=600., argv=command)
        side.old.write(worker / "process.json", process)
        side.old.write(worker / "supervision.json", dict(receipt(), reserved_seconds=100.))
        side.old.write(data / "identity.json", dict(backend=plan["identity"], model_files=plan["model_files"], adapter_files=plan["adapter_files"]))
        side.old.write(data / "backend.ready.json", dict(pid=987654321, ready=11.))
        side.old.write(data / "backend.cleanup.json", dict(closed=True, error=None))
        for index, (request, native) in enumerate(zip(plan["requests"], plan["native_inputs"])):
            response = dict(text="red", output_token_ids=[5], rendered_prompt=native["rendered_prompt"], prompt_token_ids=native["prompt_token_ids"])
            side.old.write(calls / (request["call_id"]+".request.json"), dict(request=request, identity=plan["identity"],
                prompt_sha256=side.base.value_hash(request["prompt"]), started=12.+index))
            side.old.write(calls / (request["call_id"]+".response.json"), dict(response=response,
                response_sha256=side.base.value_hash(response), ended=12.5+index))
        side.old.write(data / "usage.json", side.base.usage(data))
        side.old.write(data / "manifest.json", dict(files=side.base.tree_hashes(data)))
        return parent, plan, command

    def test_raw48_audit_and_three_family_reduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits/run/SINGLE_VIEW/lexical"
            parent, plan, command = self.make_panel(root)
            responses, _ = side.audit_panel(root, plan, command)
            self.assertEqual(len(responses), 48)
            with patch.object(side, "cue_verify", return_value=plan), patch.object(side.base, "native_tokenizer", return_value=None), \
                patch.object(side.base, "audit_native_calls") as auditor:
                result = side.cue_reduce(root, parent)
            self.assertEqual(result["counts"]["total"], 48)
            self.assertEqual(result["counts"]["correct"], 12)
            self.assertEqual({key: value["correct"] for key, value in result["counts"]["by_family"].items()}, {"0": 4, "1": 4, "2": 4})
            auditor.assert_called_once()

    def test_raw_prefix_mutation_rejected_even_rehashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits/run/SINGLE_VIEW/lexical"
            _, plan, command = self.make_panel(root)
            response_path = root / "run/data/calls/0000.response.json"
            response = side.base.read(response_path)
            response["response"]["prompt_token_ids"] = [8]
            response["response_sha256"] = side.base.value_hash(response["response"])
            response_path.write_text(json.dumps(response))
            (root / "run/data/manifest.json").write_text(json.dumps(dict(files=side.base.tree_hashes(root / "run/data", ("manifest.json",)))))
            with self.assertRaisesRegex(ValueError, "native prefix"): side.audit_panel(root, plan, command)

    def test_raw_missing_extra_pairs_and_worker_commands_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits/run/SINGLE_VIEW/lexical"
            _, plan, command = self.make_panel(root)
            with self.assertRaisesRegex(ValueError, "custody"): side.audit_panel(root, plan, command+["--different"])
            (root / "run/data/calls/extra.json").write_text("{}")
            (root / "run/data/manifest.json").write_text(json.dumps(dict(files=side.base.tree_hashes(root / "run/data", ("manifest.json",)))))
            with self.assertRaisesRegex(ValueError, "raw response pairs"): side.audit_panel(root, plan, command)

    def test_status_does_not_read_outcomes(self):
        plan = plan_fixture("/fixture/fits")
        with patch.object(side.old, "read_plan", return_value=plan), patch.object(side.common, "read", side_effect=AssertionError("outcome read")):
            status = side.status(Path(plan["root"]))
        self.assertIsNone(status["controller_present"])
        self.assertNotIn("counts", status)

    def test_collect_requires_dead_controller_and_terminal(self):
        for alive, terminal in ((True, True), (False, False), (None, True)):
            with patch.object(side, "status", return_value=dict(controller_present=alive, terminal_available=terminal)), \
                patch.object(side, "verify") as verify, self.assertRaises(ValueError):
                side.collect_body(Path("/fixture"), Path("/fixture.tgz"))
            verify.assert_not_called()

    def test_collect_refuses_orphans_before_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, archive = Path(tmp) / "fits", Path(tmp) / "capsule.tgz"
            (root / "run").mkdir(parents=True)
            (root / "run/main_release.xml").write_text("partial")
            with patch.object(side, "status", return_value=dict(controller_present=False, terminal_available=True)), \
                patch.object(side, "verify") as verify, self.assertRaisesRegex(ValueError, "orphan"):
                side.collect_body(root, archive)
            verify.assert_not_called()

    def test_custody_alarm_restored_no_budget_extension(self):
        with patch.object(side, "collect_body", return_value={}), patch.object(side.signal, "getitimer", return_value=(0., 0.)), \
            patch.object(side.signal, "signal"), patch.object(side.signal, "setitimer") as timer:
            side.collect(Path("/fixture"), Path("/fixture.tgz"))
        self.assertEqual(timer.call_args_list[0].args, (signal.ITIMER_REAL, 300))
        self.assertEqual(timer.call_args_list[-1].args, (signal.ITIMER_REAL, 0))
        timing = side.observation(1000., 3101., 2800.)
        self.assertTrue(timing["late_observation"])
        self.assertEqual(timing["overrun_seconds"], 1.)
        self.assertFalse(timing["budget_extended"])

    def test_uuid_match_required(self):
        side.check_uuid("GPU-fixture", {"gpu_uuid": "GPU-fixture"}, "<nvidia_smi_log><gpu><uuid>GPU-fixture</uuid></gpu></nvidia_smi_log>")
        with self.assertRaises(ValueError): side.check_uuid("GPU-other", {"gpu_uuid": "GPU-fixture"}, "<root/>")

    def test_metadata_excludes_native_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fits"
            root.mkdir()
            (root / "plan.json").write_text("{}")
            (root / "adapter_model.safetensors").write_bytes(b"weights")
            self.assertEqual(set(side.common.metadata(root, root.parent)), {"fits/plan.json"})

    def collection_fixture(self, tmp, seed=1):
        root, archive = Path(tmp) / "fits", Path(tmp) / "capsule.tgz"
        root.mkdir()
        plan = plan_fixture(root, seed)
        side.old.seal(root, plan)
        (root / "launch").mkdir()
        xml = "<nvidia_smi_log><gpu><uuid>GPU-fixture</uuid></gpu></nvidia_smi_log>"
        gpu = {"gpu_uuid": "GPU-fixture"}
        started = time.time()-1100
        launch = dict(seed=plan["seed"], parent_plan_sha256=plan["parent_pin"][0], seed0_gate_sha256=plan["seed0_gate"]["sha256"], plan_sha256=side.base.digest(root / "plan.json"), script_sha256=side.base.digest(side.__file__),
            root=str(root), source=str(side.base.REPO), device="1", controller_bound_seconds=1800,
            external_collection_margin_seconds=300, pid=987654321, generation_calls=224, gpu=gpu,
            started_utc=dt.datetime.fromtimestamp(started, dt.timezone.utc).isoformat(),
            command=[plan["python"], "-B", side.__file__, "run", "--source-root", str(side.base.REPO), "--runroot", str(root), "--allow-gpu"])
        side.old.write(root / "launch/launch.json", launch)
        (root / "launch/gpu.xml").write_text(xml)
        (root / "run").mkdir()
        reservation = dict(controller_pid=987654321, device="1", seed=plan["seed"], started=started, started_monotonic=0.,
            effective_deadline=started+1800, real_lease_end=plan["real_lease_end"], external_custody_deadline=started+2100,
            plan_sha256=side.base.digest(root / "plan.json"), continuous_reservation=True)
        side.old.write(root / "run/reservation.json", reservation)
        captures, arms, fits = {}, {}, {}
        worker_index = 0
        for arm in side.ARMS:
            stage = root / "run" / arm
            (stage / "fit-worker").mkdir(parents=True)
            (stage / "adapter").mkdir()
            (stage / "adapter/DONE").write_text("done")
            (stage / "adapter/adapter_model.safetensors").write_bytes(b"synthetic-weights")
            fit = dict(parent=plan["parent"]["parent"], parent_files=plan["parent"]["parent_files"], adapter=str(stage / "adapter"),
                adapter_files={"weight": "child"}, manifest_sha256="fixture", accounting=side.COUNTS[arm], supervision=dict(receipt(), reserved_seconds=100.))
            fits[arm] = {key: value for key, value in fit.items() if key != "supervision"}
            side.old.write(stage / "fit-result.json", fit)
            side.old.write(stage / "fit-worker/process.json", dict(pid=10000+worker_index, pgid=10000+worker_index, device="1", started=worker_index*110.,
                timeout=600., argv=side.fit_command(plan, arm, stage / "adapter")))
            side.old.write(stage / "fit-worker/supervision.json", fit["supervision"])
            worker_index += 1
            capture, reductions = {}, {}
            for name in side.PANELS:
                readroot = stage / name
                _, readplan, command = self.make_panel(readroot, name)
                expected = side.readplan_for(plan, name, fit, reservation["effective_deadline"])
                (readroot / "plan.json").write_bytes(side.material.encoded(expected))
                (readroot / "plan.sha256.json").write_text(json.dumps({"sha256": side.base.digest(readroot / "plan.json")}))
                data = readroot / "run/data"
                (data / "identity.json").write_text(json.dumps(dict(backend=expected["identity"], model_files=expected["model_files"], adapter_files=expected["adapter_files"])))
                shift = worker_index*110.
                process = side.base.read(readroot / "run/worker/process.json")
                process["started"] += shift
                (readroot / "run/worker/process.json").write_text(json.dumps(process))
                ready = side.base.read(data / "backend.ready.json")
                ready["ready"] += shift
                (data / "backend.ready.json").write_text(json.dumps(ready))
                for path in (data / "calls").iterdir():
                    value = side.base.read(path)
                    key = "started" if ".request." in path.name else "ended"
                    value[key] += shift
                    path.write_text(json.dumps(value))
                (data / "manifest.json").write_text(json.dumps(dict(files=side.base.tree_hashes(data, ("manifest.json",)))))
                capture[name] = side.capture_receipt(readroot, expected)
                reduction = dict(complete=True, counts=dict(total=side.PANELS[name]), rows=[dict(case_id=case["id"]) for case in expected["cases"]],
                    plan_sha256=side.base.digest(readroot / "plan.json"), capture_sha256=side.base.digest(data / "manifest.json"),
                    source_hashes=expected["source_hashes"], model_files=plan["model_files"], adapter_files=fit["adapter_files"],
                    identity=expected["identity"], native_token_text_audit=True, cost=side.base.usage(data), reserved_seconds=100.)
                side.old.write(readroot / "reduction.json", reduction)
                reductions[name] = dict(reduction=reduction, sha256=side.base.digest(readroot / "reduction.json"))
                worker_index += 1
            captures[arm] = dict(fit=fit, captures=capture)
            arms[arm] = dict(captures[arm], readouts=reductions)
            side.old.write(stage / "capture-result.json", captures[arm])
            side.old.write(stage / "arm-result.json", arms[arm])
        terminal = dict(reservation, status="COMPLETE", ended=started+1000, reserved_seconds=1000., worker_reserved_seconds=800.,
            arms=arms, captured=captures, error=None, release_verified=True, worker_accounting_complete=True,
            deadline_met=True, gate_evaluated=False, automatic_progression=False, budget_extended=False)
        side.old.write(root / "run/terminal.json", terminal)
        return root, archive, plan, fits, gpu, xml

    def collection_patches(self, stack, plan, fits, gpu, xml):
        stack.enter_context(patch.object(side, "verify", return_value=plan))
        stack.enter_context(patch.object(side, "input_stats", return_value={"fixture": "unchanged"}))
        stack.enter_context(patch.object(side, "verify_fit", side_effect=lambda plan, stage, arm: fits[arm]))
        stack.enter_context(patch.object(side.base, "native_tokenizer", side_effect=AssertionError("collector tokenizer forbidden")))
        stack.enter_context(patch.object(side, "run", side_effect=AssertionError("collector run forbidden")))
        stack.enter_context(patch.object(side, "reduce_pair", side_effect=AssertionError("collector reduction forbidden")))
        fake = SimpleNamespace(check_free=Mock(return_value=(gpu, xml)))
        stack.enter_context(patch.dict(sys.modules, {"gpu.astra_mini_sudoku_diagnostic": fake}))
        return fake

    def test_complete224call_collection_release_capsule_no_model_or_reduction(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(side.base, "expected_identity", return_value={"fixture": "child"}))
            root, archive, plan, fits, gpu, xml = self.collection_fixture(tmp)
            checker = self.collection_patches(stack, plan, fits, gpu, xml)
            result = side.collect_body(root, archive)
            self.assertEqual(result["status"], "COLLECTED_NO_SCORES")
            validation = side.common.read(str(archive)+".validation.json")
            self.assertEqual(sum(panel["raw_pairs"] for arm in validation["audits"].values() for panel in arm.values()), 224)
            self.assertTrue((root / "run/main_release.json").is_file())
            self.assertTrue((root / "run/SINGLE_VIEW/adapter/adapter_model.safetensors").is_file())
            self.assertFalse(any(name.endswith(".safetensors") for name in validation["files"]))
            checker.check_free.assert_called_once_with("1")
            with self.assertRaises(ValueError): side.collect_body(root, archive)

    def test_collection_changed_terminal_cost_fails_before_full_vacancy(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(side.base, "expected_identity", return_value={"fixture": "child"}))
            root, archive, plan, fits, gpu, xml = self.collection_fixture(tmp)
            checker = self.collection_patches(stack, plan, fits, gpu, xml)
            terminal = side.base.read(root / "run/terminal.json")
            terminal["worker_reserved_seconds"] = 799.
            (root / "run/terminal.json").write_text(json.dumps(terminal))
            with self.assertRaisesRegex(ValueError, "worker cost"): side.collect_body(root, archive)
            checker.check_free.assert_not_called()

    def test_collection_uuid_mismatch_no_release_written(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(side.base, "expected_identity", return_value={"fixture": "child"}))
            root, archive, plan, fits, gpu, xml = self.collection_fixture(tmp)
            self.collection_patches(stack, plan, fits, {"gpu_uuid": "GPU-other"}, xml)
            with self.assertRaisesRegex(ValueError, "UUID"): side.collect_body(root, archive)
            self.assertFalse((root / "run/main_release.json").exists())


def gate_fixture(directory, change=None):
    directory = Path(directory)
    root0 = directory / "root0"
    (root0 / "run").mkdir(parents=True)
    bound = dict(material_parentroot=str(directory / "original0"), materialroot=str(directory / "material"),
        material_files={arm + ".json": arm for arm in side.ARMS}, model="/fixture/model", model_files={"config": "model"})
    original = dict(root=str(root0), seed=0, source_commit=side.SOURCE_ID,
        source_hashes={"interleaved_pair": side.DEPENDENCIES["root0_source"][1]},
        arm_order=list(side.ARMS), panels=side.PANELS, total_calls=224, progression=side.PROGRESSION,
        parentroot=bound["material_parentroot"], materialroot=bound["materialroot"],
        material_files=bound["material_files"], model=bound["model"], model_files=bound["model_files"],
        config=dict(side.memory.config(bound["model"], 0, 10), overflow="truncate"))
    arms, captured = {}, {}
    for arm in side.ARMS:
        panels = {
            "dev": dict(complete=True, counts=dict(total=48, memory=dict(total=16, correct=16),
                addition=dict(total=32, adherence=32, correct_action=32))),
            "exact": dict(complete=True, counts=dict(total=16, correct=16)),
            "lexical": dict(complete=True, counts=dict(total=48, correct=48,
                by_family={str(family): dict(total=16, correct=16) for family in range(3)})),
        }
        arms[arm] = dict(readouts={name: dict(reduction=panel) for name, panel in panels.items()})
        captured[arm] = dict(captures={name: dict(pairs=total) for name, total in side.PANELS.items()})
    terminal = dict(status="COMPLETE", seed=0, error=None, release_verified=True, deadline_met=True,
        worker_accounting_complete=True, arms=arms, captured=captured)
    gate = dict(schema=side.GATE_SCHEMA, owner="Main", decision="ALLOW_SEEDS_1_2", eligible_seeds=[1, 2],
        criteria=copy.deepcopy(side.PROGRESSION), raw_review_verdict="PASS")
    if change: change(original, terminal, gate)
    planpath, terminalpath = root0 / "plan.json", root0 / "run/terminal.json"
    planpath.write_text(json.dumps(original))
    terminal["plan_sha256"] = side.base.digest(planpath)
    terminalpath.write_text(json.dumps(terminal))
    validationpath, reviewpath = directory / "validation.json", directory / "review.md"
    validationpath.write_text(json.dumps(dict(terminal_status="COMPLETE", plan_sha256=side.base.digest(planpath),
        files={root0.name + "/run/terminal.json": side.base.digest(terminalpath)})))
    reviewpath.write_text("Synthetic CPU gate fixture, not an actual scientific review.\n")
    for name, path in (("seed0_plan", planpath), ("seed0_terminal", terminalpath),
                       ("seed0_validation", validationpath), ("raw_review", reviewpath)):
        gate[name] = dict(path=str(path), sha256=side.base.digest(path))
    gatepath = directory / "gate.json"
    gatepath.write_text(json.dumps(gate))
    return gatepath, side.base.digest(gatepath), bound, gate


class ReplicationSpecificTests(unittest.TestCase):
    def test_both_seeds_commands_config_and_readout_identity(self):
        for seed in side.SEEDS:
            with self.subTest(seed=seed):
                plan = plan_fixture(f"/fixture/seed{seed}", seed)
                outputs = []
                for arm in side.ARMS:
                    adapter = Path(plan["root"]) / "run" / arm / "adapter"
                    command = side.fit_command(plan, arm, adapter)
                    self.assertEqual(command[command.index("--seed") + 1], str(seed))
                    self.assertEqual(command[command.index("--init-adapter") + 1], plan["parent"]["parent"])
                    self.assertEqual(command[command.index("--overflow") + 1], "truncate")
                    outputs.append(str(adapter))
                    fit = dict(adapter=str(adapter), adapter_files={"weight": str(seed)})
                    for panel in side.PANELS:
                        with patch.object(side.base, "expected_identity", return_value={"fixture": str(seed)}):
                            readplan = side.readplan_for(plan, panel, fit, 2800.)
                        binding = readplan["replication_binding"]
                        self.assertEqual(binding["seed"], seed)
                        self.assertEqual(binding["original_parent_plan_sha256"], side.memory.PINS[str(seed)][0])
                        self.assertEqual(binding["original_readout_plan_sha256"], side.memory.PINS[str(seed)][2])
                        self.assertEqual(readplan["requests"], plan["templates"][panel]["requests"])
                self.assertEqual(len(set(outputs)), 2)

    def test_both_seeds_loaded_state_and_fresh_optimizer(self):
        for seed in side.SEEDS:
            plan = plan_fixture(f"/fixture/seed{seed}", seed)
            for arm in side.ARMS:
                manifest, saved = manifest_fixture(plan, arm)
                side.validate_manifest(plan, arm, manifest, plan["parent_state"], saved)
                for key, value in (("phase_seed", 0), ("phase_seed", 3-seed), ("parent_cumulative_steps", 400),
                                   ("optimizer_state_restored", True), ("parent_path", "/fixture/original0/fit_teach/adapter")):
                    bad = copy.deepcopy(manifest)
                    bad["warm_start"][key] = value
                    with self.subTest(seed=seed, arm=arm, key=key), self.assertRaises(ValueError):
                        side.validate_manifest(plan, arm, bad, plan["parent_state"], saved)

    def test_original_parent_three_pins_both_seeds_and_copied_seed0_negative(self):
        for seed in side.SEEDS:
            root = Path(f"/fixture/copied-original-seed{seed}")
            paths = [root / "plan.json", root / "fit_teach/verified.json", root / "readouts/teach/plan.json"]
            for pinseed, accepted in ((seed, True), (0, False), (3-seed, False)):
                pins = dict(zip(map(str, paths), side.memory.PINS[str(pinseed)]))
                with patch.object(side.common, "unaliased"), patch.object(side.base, "digest", side_effect=lambda path: pins[str(path)]), \
                     patch.object(side.old, "read_plan", return_value={"config": {"seed": seed}}):
                    if accepted: side.parent_identity(root, seed)
                    else:
                        with self.subTest(seed=seed, copied=pinseed), self.assertRaisesRegex(ValueError, "original corresponding"):
                            side.parent_identity(root, seed)

    def test_matching_pin_but_original_config_seed_mismatch(self):
        root = Path("/fixture/original1")
        with patch.object(side.common, "unaliased"), patch.object(side.base, "digest", side_effect=side.memory.PINS["1"]), \
             patch.object(side.old, "read_plan", return_value={"config": {"seed": 0}}), self.assertRaisesRegex(ValueError, "optimizer seed"):
            side.parent_identity(root, 1)

    def test_forbid_seed0_unknown_boolean_and_arm_slot_substitution(self):
        for seed in (0, 3, True, "1"):
            with self.subTest(seed=seed), self.assertRaises(ValueError): side.config("model", seed)
        plan = plan_fixture("/fixture/seed1")
        for arm, output in (("FOUR_VIEW", "/fixture/seed1/run/SINGLE_VIEW/adapter"),
                            ("other", "/fixture/seed1/run/other/adapter")):
            with self.assertRaises(ValueError): side.fit_command(plan, arm, output)
        with self.assertRaisesRegex(ValueError, "foreign child"):
            side.readplan_for(plan, "dev", dict(adapter="/fixture/seed0/run/FOUR_VIEW/adapter"), 2800.)

    def test_slot_ordering_and_heldout_material_cannot_change(self):
        candidate = side.material.build_candidate()
        side.material.validate_candidate(candidate)
        candidate["arms"]["FOUR_VIEW"][0]["batch_slot"] = 3
        with self.assertRaises(ValueError): side.material.validate_candidate(candidate)
        candidate = side.material.build_candidate()
        candidate["heldout_cues"][0]["context"] += " yellow"
        with self.assertRaises(ValueError): side.material.validate_candidate(candidate)

    def test_six_hour_cutoff_exact_boundary_no_shortening(self):
        self.assertEqual(side.bounds(1000., 2800., 24700.), 2800.)
        for started, deadline, expiry in ((1000., 2800., 24699.999), (1000., 2799., 90000.),
            (True, 2800., 90000.), (1000., float("inf"), 90000.), (1000., 2800., float("nan"))):
            with self.subTest(started=started, deadline=deadline, expiry=expiry), self.assertRaises(ValueError):
                side.bounds(started, deadline, expiry)

    def test_valid_explicit_gate_and_single_scores_irrelevant(self):
        def mutate(original, terminal, gate):
            terminal["arms"]["SINGLE_VIEW"]["readouts"]["exact"]["reduction"]["counts"]["correct"] = 0
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum, bound, gate = gate_fixture(tmp, mutate)
            accepted = side.gate_receipt(path, checksum, bound)
            self.assertEqual(accepted["decision"], "ALLOW_SEEDS_1_2")
            self.assertEqual(len(accepted["evidence_hashes"]), 5)
            self.assertEqual(accepted["sha256"], checksum)

    def test_generic_complete_pending_missing_review_or_altered_criteria_not_gate(self):
        mutations = [lambda original, terminal, gate: gate.update(decision="COMPLETE"),
            lambda original, terminal, gate: gate.update(raw_review_verdict="PENDING"),
            lambda original, terminal, gate: gate.update(owner="auto"),
            lambda original, terminal, gate: gate["criteria"].update(dev_memory_min=14),
            lambda original, terminal, gate: terminal.update(release_verified=False),
            lambda original, terminal, gate: terminal["captured"]["SINGLE_VIEW"]["captures"]["lexical"].update(pairs=47),
            lambda original, terminal, gate: original.update(seed=1),
            lambda original, terminal, gate: original.update(arm_order=list(reversed(side.ARMS)))]
        for mutate in mutations:
            with tempfile.TemporaryDirectory() as tmp:
                path, checksum, bound, gate = gate_fixture(tmp, mutate)
                with self.assertRaises(ValueError): side.gate_receipt(path, checksum, bound)
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum, bound, gate = gate_fixture(tmp)
            Path(gate["raw_review"]["path"]).unlink()
            with self.assertRaises((ValueError, FileNotFoundError)): side.gate_receipt(path, checksum, bound)

    def test_gate_criteria_fail_even_main_says_allow(self):
        for panel in ("dev", "exact", "lexical"):
            def mutate(original, terminal, gate):
                counts = terminal["arms"]["FOUR_VIEW"]["readouts"][panel]["reduction"]["counts"]
                if panel == "dev": counts["addition"]["adherence"] = 29
                elif panel == "exact": counts["correct"] = 14
                else: counts["by_family"]["2"]["correct"] = 14
            with tempfile.TemporaryDirectory() as tmp:
                path, checksum, bound, gate = gate_fixture(tmp, mutate)
                with self.subTest(panel=panel), self.assertRaisesRegex(ValueError, "criteria not met"):
                    side.gate_receipt(path, checksum, bound)

    def test_gate_habit_adherence30_and_act_correct_action31_not_swapped(self):
        for actions, adherence, accepted in ((31, 30, True), (30, 30, False), (32, 29, False)):
            def mutate(original, terminal, gate):
                counts = terminal["arms"]["FOUR_VIEW"]["readouts"]["dev"]["reduction"]["counts"]["addition"]
                counts.update(correct_action=actions, adherence=adherence)
            with self.subTest(correct_action=actions, adherence=adherence), tempfile.TemporaryDirectory() as tmp:
                path, checksum, bound, gate = gate_fixture(tmp, mutate)
                if accepted:
                    side.gate_receipt(path, checksum, bound)
                else:
                    with self.assertRaisesRegex(ValueError, "criteria not met"):
                        side.gate_receipt(path, checksum, bound)

    def test_gate_hash_wrong_and_changed_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, checksum, bound, gate = gate_fixture(tmp)
            with self.assertRaisesRegex(ValueError, "gate hash"): side.gate_receipt(path, "0"*64, bound)
            Path(gate["raw_review"]["path"]).write_text("changed fixture")
            with self.assertRaisesRegex(ValueError, "evidence changed"): side.gate_receipt(path, checksum, bound)

    def test_native_prepare_for_seed2(self):
        helper = RunnerTests("test_native_prepare_reaudits_before_plan_with_padded_cost")
        original_fixture = plan_fixture
        with patch.dict(globals(), {"plan_fixture": lambda root: original_fixture(root, 2)}):
            helper.test_native_prepare_reaudits_before_plan_with_padded_cost()

    def test_seed2_full224_custody_and_wrong_seed_launch_rejected(self):
        helper = RawAndCollectionTests()
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(side.base, "expected_identity", return_value={"fixture": "child"}))
            root, archive, plan, fits, gpu, xml = helper.collection_fixture(tmp, 2)
            helper.collection_patches(stack, plan, fits, gpu, xml)
            side.collect_body(root, archive)
            validation = side.common.read(str(archive)+".validation.json")
            self.assertEqual(validation["seed"], 2)
            self.assertEqual(validation["original_parent_plan_sha256"], side.memory.PINS["2"][0])
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            stack.enter_context(patch.object(side.base, "expected_identity", return_value={"fixture": "child"}))
            root, archive, plan, fits, gpu, xml = helper.collection_fixture(tmp, 2)
            launchpath = root / "launch/launch.json"
            launch = side.common.read(launchpath)
            launch["seed"] = 1
            launchpath.write_text(json.dumps(launch))
            helper.collection_patches(stack, plan, fits, gpu, xml)
            with self.assertRaisesRegex(ValueError, "launch receipt"): side.collect_body(root, archive)

    def test_frozen_drivers_unchanged_and_no_production_global_substitution(self):
        for name in ("root0_source", "paired_source", "replay_source"):
            path, expected = side.DEPENDENCIES[name]
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected)
        source = Path(side.__file__).read_text()
        self.assertNotIn("setattr(", source)
        self.assertNotIn("patch.object", source)


if __name__ == "__main__":
    unittest.main()
