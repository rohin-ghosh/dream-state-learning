"""CPU contract tests: synthetic files/tokenizer and mocked fits, workers, signals, GPUs."""
from contextlib import ExitStack
import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("sequential_driver_test", "/tmp/astra_sequential_memory_pair_20260912.py")
side = importlib.util.module_from_spec(spec)
spec.loader.exec_module(side)
side.helper = side.load_module(side.HELPER, side.HELPER_SHA, "sequential_test_helpers")
side.memory, side.common = side.helper.load("memory"), side.helper.load("common")
side.memory.bind(Path.cwd(), "/tmp/astra_fading_sentinel_20260912.py")
for name in ("old", "base", "trainer", "dev"):
    setattr(side, name, getattr(side.memory, name))
from organism_v6 import sequential_memory_corpus
side.material = sequential_memory_corpus
side.SOURCE_ID = "a" * 40


class Tokenizer:
    eos_token_id, pad_token_id = 900, 901

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt and len(messages) == 1
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text, *, add_special_tokens=False):
        assert not add_special_tokens
        if text in side.material.original.COLORS:
            return [700 + side.material.original.COLORS.index(text)]
        tokens = []
        for index, piece in enumerate(text.split("<|im_end|>")):
            if index:
                tokens.append(self.eos_token_id)
            tokens.extend(ord(character) + 2 for character in piece)
        return tokens


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False))


def state(name):
    return {"module.lora_A.weight": dict(shape=[2, 2], dtype="torch.float32", sha256=name)}


def inventory(adapter):
    return side.common.read(Path(adapter) / "train_manifest.json")["warm_start"]["final_state"]


class Clock:
    def __init__(self):
        self.wall, self.mono = 1800000000., 10000.

    def time(self): return self.wall
    def monotonic(self): return self.mono
    def advance(self, seconds=1.):
        self.wall += seconds
        self.mono += seconds


class Fixture:
    def __init__(self, tmp, stack):
        self.home = Path(tmp)
        self.root, self.materialroot = self.home / "runroot", self.home / "material"
        self.parentroot, self.original = self.home / "root0-pair", self.home / "original0"
        self.model = self.home / "model"
        self.model.mkdir()
        (self.model / "config.json").write_text('{"model_type":"qwen2"}')
        self.model_files = side.base.model_hashes(self.model)
        self.clock, self.calls, self.worker_count = Clock(), [], 0
        self.tokenizer = Tokenizer()
        teach = dict(corpus=[dict(spans=[[side.material.prior.render(self.tokenizer, row["context"]), False, "context"],
            [row["response"], True, "authored_birth_target"]], group=row["case_id"], view=row["kind"], order=index,
            meta=dict(source_event_ids=row["source_event_ids"][:])) for index, row in enumerate(side.material.prior.original_rows())])
        write(self.original / "teach.json", teach)
        stack.enter_context(patch.object(side.material.prior, "ORIGINAL_TEACH_SHA256", side.digest(self.original / "teach.json")))
        self.s0 = self.parentroot / "run/FOUR_VIEW/adapter"
        self.s0.mkdir(parents=True)
        self.create_checkpoint(self.s0, "S0", side.config(str(self.model)), None)
        original_plan = dict(root=str(self.parentroot), parentroot=str(self.original), seed=0,
            source_commit=side.S0_SOURCE_ID, source_hashes=dict(interleaved_pair=side.helper.DEPENDENCIES["root0_source"][1]),
            arm_order=["SINGLE_VIEW", "FOUR_VIEW"], model=str(self.model), model_files=self.model_files)
        side.old.seal(self.parentroot, original_plan)
        self.parent_sha = side.digest(self.parentroot / "plan.json")
        fit = dict(adapter=str(self.s0), adapter_files=side.trainer._warm_inventory(self.s0))
        write(self.s0.parent / "fit-result.json", fit)
        write(self.parentroot / "run/terminal.json", dict(status="COMPLETE", plan_sha256=self.parent_sha, error=None,
            release_verified=True, deadline_met=True, worker_accounting_complete=True, arms=dict(FOUR_VIEW=dict(fit=fit))))
        stack.enter_context(patch.object(side.old, "state_inventory", inventory))
        stack.enter_context(patch.object(side.base, "native_tokenizer", return_value=self.tokenizer))
        stack.enter_context(patch.object(side.base, "expected_identity", side_effect=lambda plan, adapter=None:
            dict(model=plan["model"], adapter=adapter)))
        stack.enter_context(patch.object(side.time, "time", self.clock.time))
        stack.enter_context(patch.object(side.time, "monotonic", self.clock.monotonic))
        stack.enter_context(patch.object(side.os, "getpid", return_value=987654321))
        stack.enter_context(patch.object(side.signal, "getitimer", return_value=(0., 0.)))
        stack.enter_context(patch.object(side.signal, "setitimer"))
        stack.enter_context(patch.object(side.signal, "signal", return_value=signal.SIG_DFL))
        stack.enter_context(patch.object(side.base.supervisor, "selected_device", return_value="0"))
        self.native_calls = 0

    def create_checkpoint(self, adapter, label, config, plan):
        adapter.mkdir(parents=True, exist_ok=True)
        (adapter / "adapter_model.safetensors").write_bytes(("NOT_NATIVE_WEIGHTS:" + label).encode())
        (adapter / "DONE").write_text("ok")
        write(adapter / "adapter_config.json", dict(base_model_name_or_path=str(self.model)))
        parent_name = "original" if label == "S0" else side.PARENTS[label]
        parent = str(self.original / "fit_teach/adapter") if plan is None else side.parent_path(plan, label)
        parent_files = {} if plan is None else side.trainer._warm_inventory(parent)
        before = state(parent_name) if plan is None else inventory(parent)
        totals = dict(input_tokens=7000, context_tokens=6000, target_tokens=1000) if plan is None else plan["material"]["counts"][label]
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write",
            parent_path=parent, parent_files=parent_files, parent_files_after=parent_files, parent_unchanged=True,
            base_frozen=True, initialized_loaded_state_check=True, phase_seed=0, adapter_count=1,
            optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
            phase_steps=320, parent_cumulative_steps=80 if label == "S0" else side.CUMULATIVE[side.PARENTS[label]],
            cumulative_steps=side.CUMULATIVE[label], source_state=before, initialized_state=before,
            final_state=state(label), dtype_conversions={})
        manifest = dict(recipe=side.trainer.RECIPE, config=config, base_model=str(self.model), steps=320, micro_batches=320,
            epochs_run=10, nonfinite_batches=0, final_loss=1., empty=False, warm_start=warm,
            corpus=dict(sha256="S0" if plan is None else plan["material"]["files"][plan["material"]["corpus_files"][label]],
                n_items=128, n_encoded=128, n_skipped_no_target=0),
            tokens=dict(total=totals["input_tokens"], context=totals["context_tokens"], target=totals["target_tokens"],
                target_by_view={"memory": 128}, target_by_category={}), train_tokens_seen=10*totals["input_tokens"],
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0))
        write(adapter / "train_manifest.json", manifest)

    def prepare(self):
        result = side.prepare(self.parentroot, self.parent_sha, self.materialroot, self.root, "0",
            self.clock.wall + 6000, self.clock.wall + 86400)
        self.plan = side.old.read_plan(self.root)
        return result

    def launch(self):
        plan = self.plan
        launch = dict(root=plan["root"], source=plan["source_root"], source_commit=plan["source_commit"],
            plan_sha256=side.digest(self.root / "plan.json"), script_sha256=side.digest(side.__file__), device="0", seed=0,
            parent_seed=0, source_branch="FOUR_VIEW", parent_plan_sha256=self.parent_sha, s0_adapter_files=plan["s0"]["parent_files"],
            controller_bound_seconds=5100, external_collection_margin_seconds=300, generation_calls=640, worker_count=9,
            pid=987654321, gpu=dict(gpu_uuid="GPU-synthetic"), started_utc=dt.datetime.fromtimestamp(self.clock.wall, dt.timezone.utc).isoformat(),
            command=[plan["python"], "-B", str(Path(side.__file__).absolute()), "run", "--source-root", plan["source_root"],
                "--source-id", plan["source_commit"], "--runroot", plan["root"], "--allow-gpu"])
        write(self.root / "launch/launch.json", launch)
        (self.root / "launch/gpu.xml").write_text("<nvidia_smi_log><gpu><uuid>GPU-synthetic</uuid></gpu></nvidia_smi_log>")

    def supervise(self, accounting_root, plan, stage, command, call_path=None):
        assert stage.parent == accounting_root or stage.parent.parent == accounting_root
        assert plan["lease_end"] == self.plan["deadline"] - 900
        assert not list(Path(accounting_root).glob("**/supervision.json"))
        stage.mkdir()
        self.worker_count += 1
        started = self.clock.mono
        process = dict(pid=100000+self.worker_count, pgid=100000+self.worker_count, argv=command,
            device="0", timeout=600., started=started)
        write(stage / "process.json", process)
        if "--init-adapter" in command:
            adapter = Path(command[command.index("--out")+1])
            label = adapter.parent.name
            self.calls.append("fit:"+label)
            self.create_checkpoint(adapter, label, self.plan["config"], self.plan)
        else:
            label = command[command.index("--state")+1]
            self.calls.append("capture:"+label)
            data = call_path.parent
            data.mkdir()
            call_path.mkdir()
            write(data / "identity.json", dict(backend=plan["identity"], model_files=plan["model_files"], adapter_files=plan["adapter_files"]))
            write(data / "backend.ready.json", dict(pid=process["pid"], ready=started))
            for request, native, case in zip(plan["requests"], plan["native_inputs"], plan["cases"], strict=True):
                text = f"PREDICT: {case['expected']}\nACT: {case['expected']}" if case["kind"] == "addition" else case["expected"]
                response = dict(text=text, rendered_prompt=native["rendered_prompt"], prompt_token_ids=native["prompt_token_ids"], output_token_ids=[1])
                stem = call_path / request["call_id"]
                write(Path(str(stem)+".request.json"), dict(request=request, identity=plan["identity"], started=self.clock.mono,
                    prompt_sha256=side.base.value_hash(request["prompt"])))
                self.clock.advance(.001)
                write(Path(str(stem)+".response.json"), dict(response=response, ended=self.clock.mono,
                    response_sha256=side.base.value_hash(response)))
            write(data / "usage.json", side.base.usage(data))
            write(data / "backend.cleanup.json", dict(closed=True))
            side.base.capture_manifest(data)
        self.clock.advance(1.)
        receipt = dict(ok=True, error=None, returncode=0, owned_group_empty=True, gpu_processes_absent=True,
            reservation_release_verified=True, reserved_seconds=self.clock.mono-started, device="0")
        write(stage / "supervision.json", receipt)
        return receipt

    def run(self):
        self.launch()
        with patch.object(side.base, "supervise", side_effect=self.supervise):
            return side.run(self.root, True, (self.clock.wall, self.clock.mono))


class DriverTests(unittest.TestCase):
    def test_actual_candidate_interface_and_fixed_counts(self):
        self.assertEqual(tuple(side.material.STATES), side.STATES)
        self.assertEqual(side.material.SEED, side.FIT_SEED)
        self.assertEqual(len(side.material.readout_cases()), 128)
        self.assertEqual(side.CALLS, 5*128)
        self.assertEqual(side.WORKERS, 4+5)

    def test_prepare_actual_export_with_mock_tokenizer_and_no_model(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            with patch.object(side.base, "model_hashes", wraps=side.base.model_hashes) as hasher:
                result = fixture.prepare()
                self.assertEqual(hasher.call_count, 1)
                self.assertEqual(side.verify(fixture.root), fixture.plan)
                self.assertEqual(hasher.call_count, 1)
            self.assertEqual(result["status"], "PREPARED_NOT_LAUNCHED")
            self.assertEqual(fixture.plan["s0"]["branch"], "FOUR_VIEW")
            self.assertEqual(fixture.plan["config"]["seed"], 0)
            self.assertEqual(set(fixture.plan["material"]["counts"]), set(side.FITS))
            self.assertFalse((fixture.root / "run").exists())
            with self.assertRaises(ValueError): fixture.prepare()

    def test_parent_chain_commands_and_fresh_optimizer(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            for label in side.FITS:
                command = side.fit_command(fixture.plan, label)
                self.assertEqual(command[command.index("--seed")+1], "0")
                self.assertEqual(command[command.index("--epochs")+1], "10")
                self.assertEqual(command[command.index("--init-adapter")+1], side.parent_path(fixture.plan, label))
                self.assertEqual(command[command.index("--out")+1], side.adapter_path(fixture.plan, label))
            self.assertEqual(side.parent_path(fixture.plan, "R1"), side.parent_path(fixture.plan, "NEW_ONLY1"))
            self.assertNotEqual(side.parent_path(fixture.plan, "R2"), side.parent_path(fixture.plan, "NEW_ONLY2"))

    def test_end_to_end_nine_mock_workers_all640_before_reductions(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            real_score = side.dev.score_memory
            def scored(*args):
                self.assertEqual(fixture.worker_count, 9)
                self.assertEqual(len(list((fixture.root / "run").glob("**/calls/*.response.json"))), 640)
                return real_score(*args)
            with patch.object(side.dev, "score_memory", side_effect=scored):
                fixture.run()
            self.assertEqual(fixture.calls, ["capture:S0", "fit:R1", "capture:R1", "fit:NEW_ONLY1", "capture:NEW_ONLY1",
                "fit:R2", "capture:R2", "fit:NEW_ONLY2", "capture:NEW_ONLY2"])
            terminal = side.common.read(fixture.root / "run/terminal.json")
            self.assertEqual(terminal["status"], "COMPLETE")
            self.assertEqual(len(terminal["reductions"]), 5)
            self.assertEqual(sum(item["pairs"] for item in terminal["captured"].values()), 640)
            for label, reduced in terminal["reductions"].items():
                self.assertEqual(reduced["counts"]["addition"], dict(total=32, correct_action=32, adherence=32))
                self.assertEqual(len(reduced["rows"]), 128)
                if label != "S0":
                    self.assertEqual(terminal["fits"][label]["cumulative_steps"], side.CUMULATIVE[label])
            self.assertFalse(terminal["automatic_progression"])
            self.assertEqual(side.trainer._warm_inventory(fixture.s0), fixture.plan["s0"]["parent_files"])
            self.assertEqual(side.status(fixture.root)["states"]["NEW_ONLY2"]["reduction_available"], True)
            with self.assertRaises(ValueError): fixture.run()

    def test_boundaries_and_no_implicit_gpu(self):
        self.assertEqual(side.bounds(1000., 6100., 28000.), 6100.)
        for values in ((1000., 6099., 28000.), (1000., 6100., 27999.), (float("nan"), 6100., 28000.)):
            with self.subTest(values=values), self.assertRaises(ValueError): side.bounds(*values)
        with self.assertRaisesRegex(ValueError, "allocation"): side.run(Path("/never"))

    def test_original_parent_wrong_seed_branch_or_weights_rejected(self):
        for mutation in ("seed", "branch", "weight", "steps", "plan_pin"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                if mutation in ("seed", "branch"):
                    path = fixture.parentroot / "plan.json"
                    plan = side.common.read(path)
                    if mutation == "seed": plan["seed"] = 1
                    else: plan["arm_order"] = ["FOUR_VIEW", "SINGLE_VIEW"]
                    write(path, plan)
                    fixture.parent_sha = side.digest(path)
                    write(fixture.parentroot / "plan.sha256.json", dict(sha256=fixture.parent_sha))
                if mutation == "weight": (fixture.s0 / "adapter_model.safetensors").write_bytes(b"copied-wrong-state")
                if mutation == "steps":
                    path = fixture.s0 / "train_manifest.json"
                    manifest = side.common.read(path)
                    manifest["warm_start"]["cumulative_steps"] = 720
                    write(path, manifest)
                if mutation == "plan_pin": fixture.parent_sha = "0"*64
                with self.assertRaises(ValueError): fixture.prepare()
                self.assertFalse(fixture.root.exists())

    def test_warm_start_checks_reject_cross_arm_optimizer_mask_and_steps(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.run()
            plan, label = fixture.plan, "R2"
            manifest = side.common.read(Path(side.adapter_path(plan, label)) / "train_manifest.json")
            binding = side.common.read(fixture.root / "run/R2/input.json")
            saved = manifest["warm_start"]["final_state"]
            mutations = [("warm_start", "parent_path", side.parent_path(plan, "NEW_ONLY2")),
                ("warm_start", "optimizer_state_restored", True), ("warm_start", "optimizer_initial_state_entries", 1),
                ("warm_start", "phase_seed", 1), ("warm_start", "cumulative_steps", 720),
                ("warm_start", "parent_cumulative_steps", 400), ("warm_start", "adapter_count", 2),
                ("warm_start", "base_frozen", False), ("warm_start", "initialized_state", state("other")),
                ("truncation", "target_tokens_dropped", 1), ("truncation", "items_split", 1),
                ("corpus", "n_encoded", 127), ("tokens", "target", 1)]
            for section, key, value in mutations:
                with self.subTest(section=section, key=key):
                    changed = copy.deepcopy(manifest)
                    changed[section][key] = value
                    with self.assertRaises(ValueError):
                        side.validate_manifest(plan, label, changed, binding["parent_files"], binding["parent_state"], saved)

    def test_run_partial_capture_never_reduces_and_does_not_progress(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            original = fixture.supervise
            def fail(accounting_root, plan, stage, command, call_path=None):
                if "--state" in command and command[command.index("--state")+1] == "NEW_ONLY1":
                    raise RuntimeError("mock readout failure before worker")
                return original(accounting_root, plan, stage, command, call_path)
            fixture.launch()
            with patch.object(side.base, "supervise", side_effect=fail), patch.object(side.dev, "score_memory") as scorer:
                with self.assertRaisesRegex(ValueError, "partial trajectory"):
                    side.run(fixture.root, True, (fixture.clock.wall, fixture.clock.mono))
                scorer.assert_not_called()
            terminal = side.common.read(fixture.root / "run/terminal.json")
            self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")
            self.assertEqual(terminal["reductions"], {})
            self.assertFalse((fixture.root / "run/R2").exists())

    def test_capture_deletion_and_template_change_block_barrier(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.run()
            root = side.panel_root(fixture.plan, "NEW_ONLY2")
            path = root / "run/data/calls/0127.response.json"
            original = path.read_bytes()
            path.unlink()
            with self.assertRaises(ValueError): side.capture_barrier(fixture.plan)
            path.write_bytes(original)
            plan_path = root / "plan.json"
            readplan = side.common.read(plan_path)
            readplan["requests"][0]["prompt"] += " reminder"
            write(plan_path, readplan)
            write(root / "plan.sha256.json", dict(sha256=side.digest(plan_path)))
            with self.assertRaises(ValueError): side.capture_barrier(fixture.plan)

    def test_material_tamper_no_repair_or_run(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            path = fixture.materialroot / "cycle2_R.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(ValueError): side.verify(fixture.root)
            with self.assertRaises(ValueError): side.run(fixture.root, True)
            self.assertFalse((fixture.root / "run").exists())

    def test_native_venv_spelling_not_resolved(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            alias = Path(tmp) / "venv-python"
            alias.symlink_to("/fixture/nonexistent-python")
            with patch.object(side.sys, "executable", str(alias)):
                self.assertEqual(side.python(), str(alias))
            plan = dict(fixture.plan, python=str(alias))
            self.assertEqual(side.fit_command(plan, "R1")[0], str(alias))
            self.assertEqual(side.worker_command(plan, "S0")[0], str(alias))

    def test_collect_all640_without_reducers_tokenizer_or_full_model_rehash(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.run()
            original_exists = Path.exists
            def exists(path):
                return False if str(path).startswith("/proc/") else original_exists(path)
            xml = "<nvidia_smi_log><gpu><uuid>GPU-synthetic</uuid></gpu></nvidia_smi_log>"
            with patch.object(Path, "exists", exists), \
                patch("gpu.astra_mini_sudoku_diagnostic.check_free", return_value=(dict(gpu_uuid="GPU-synthetic"), xml)), \
                patch.object(side.base, "native_tokenizer", side_effect=AssertionError("no tokenizer during collect")), \
                patch.object(side.base, "model_hashes", side_effect=AssertionError("no full model rehash")), \
                patch.object(side.old, "state_inventory", side_effect=AssertionError("no tensor read during collect")), \
                patch.object(side.dev, "score_memory", side_effect=AssertionError("no reduction during collect")):
                result = side.collect(fixture.root, Path(tmp) / "capsule.tgz")
            self.assertEqual(result["status"], "COLLECTED_NO_NEW_SCORES")
            validation = side.common.read(Path(tmp) / "capsule.tgz.validation.json")
            self.assertEqual(validation["terminal_status"], "COMPLETE")
            self.assertEqual(sum(report["pairs"] for report in validation["reports"].values()), 640)
            self.assertFalse(any(name.endswith(".safetensors") for name in validation["files"]))
            self.assertEqual(validation["phase_seed"], 0)
            self.assertFalse(validation["reducers_rerun"])
            self.assertIn(fixture.root.name + "/inputs/code/sequential_memory_corpus.py", validation["files"])
            self.assertIn(fixture.root.name + "/inputs/code/varied_memory_replay_corpus.py", validation["files"])
            self.assertTrue((fixture.root / "run/R2/adapter/adapter_model.safetensors").exists())

    def test_launch_parent_command_device_and_caps_must_match(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.launch()
            path = fixture.root / "launch/launch.json"
            original = side.common.read(path)
            for key, value in (("parent_seed", 1), ("source_branch", "SINGLE_VIEW"), ("seed", 1),
                ("device", "2"), ("generation_calls", 639), ("worker_count", 8), ("controller_bound_seconds", 1800),
                ("external_collection_margin_seconds", 0), ("s0_adapter_files", {}), ("command", ["foreign"])):
                with self.subTest(key=key):
                    write(path, dict(original, **{key: value}))
                    with self.assertRaises(ValueError): side.launch_record(fixture.root, fixture.plan)

    def test_wrong_source_identity_and_changed_model_metadata_fail(self):
        with self.assertRaises(ValueError): side.bind(Path.cwd(), "not-a-source-id")
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            (fixture.model / "config.json").write_text("changed")
            with self.assertRaisesRegex(ValueError, "immutable inputs"): side.verify(fixture.root)

    def test_global_controller_alarm_and_expired_collection(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.run()
            side.signal.setitimer.assert_any_call(signal.ITIMER_REAL, 4960.)
            fixture.clock.advance(5401)
            with self.assertRaisesRegex(ValueError, "expired"):
                side.collect(fixture.root, Path(tmp) / "late.tgz")
            self.assertFalse((Path(tmp) / "late.tgz").exists())

    def test_cleanup_failure_stops_before_next_worker_or_scoring(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.prepare()
            fixture.launch()
            original = fixture.supervise
            def unsafe_release(accounting_root, plan, stage, command, call_path=None):
                receipt = original(accounting_root, plan, stage, command, call_path)
                receipt.update(ok=False, reservation_release_verified=False, owned_group_empty=False)
                write(stage / "supervision.json", receipt)
                return receipt
            with patch.object(side.base, "supervise", side_effect=unsafe_release), patch.object(side.dev, "score_memory") as scorer:
                with self.assertRaisesRegex(ValueError, "partial trajectory"):
                    side.run(fixture.root, True, (fixture.clock.wall, fixture.clock.mono))
                scorer.assert_not_called()
            terminal = side.common.read(fixture.root / "run/terminal.json")
            self.assertEqual(fixture.worker_count, 1)
            self.assertFalse(terminal["release_verified"])
            self.assertFalse(terminal["worker_accounting_complete"])
            self.assertFalse((fixture.root / "run/R1").exists())


if __name__ == "__main__":
    unittest.main()
