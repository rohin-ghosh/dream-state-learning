"""Stdlib CPU fixtures only; no native model, worker process, network or GPU."""
import copy
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("two_habit_runner", "/tmp/astra_two_habit_runner_20260912.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
runner.bind(Path.cwd())
REAL = SimpleNamespace(base=runner.base, trainer=runner.trainer, old=runner.old,
                       readout=runner.readout, material=runner.material, prior=runner.prior)


def proxy(module, **changes):
    return SimpleNamespace(**dict(vars(module), **changes))


class Tokenizer:
    eos_token_id = 900
    pad_token_id = 901

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt and len(messages) == 1 and messages[0]["role"] == "user"
        return "<|im_start|>user\n" + messages[0]["content"] + "<|im_end|>\n<|im_start|>assistant\n"

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        pieces = text.split("<|im_end|>")
        result = []
        for index, piece in enumerate(pieces):
            if index:
                result.append(self.eos_token_id)
            result.extend(ord(character) for character in piece)
        return result

    def decode(self, tokens, **kwargs):
        return "".join(chr(token) for token in tokens)

    def get_vocab(self):
        return {"fixture": 900}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="two-habit-runner-fixture-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        self.write(self.model / "config.json", {"model_type": "qwen2"})
        self.model_files = REAL.base.model_hashes(self.model)
        self.runroot = self.root / "prepared"
        self.materialroot = self.root / "material"
        self.deadline = time.time() + 3000
        self.lease_end = self.deadline + 5000
        self.tokenizer = Tokenizer()
        self.states, self.pins, self.baseline_pins = {}, {}, {}
        self.patch(runner, "base", proxy(REAL.base, native_tokenizer=lambda model: self.tokenizer))
        self.patch(runner, "trainer", proxy(REAL.trainer, _warm_parent=lambda *args: {"fixture": True}))
        self.patch(runner, "old", proxy(REAL.old, state_inventory=lambda path: copy.deepcopy(self.states[str(path)])))
        rows = []
        for index, row in enumerate(REAL.material.original.build_candidate()["train_teach"]):
            rows.append(dict(spans=[[self.tokenizer.apply_chat_template([dict(role="user", content=row["context"])],
                tokenize=False, add_generation_prompt=True), False, "context"],
                [row["response"], True, "authored_birth_target"]], group=row["case_id"], view=row["kind"], order=index,
                meta=dict(source_event_ids=row["source_event_ids"])))
        self.teach = self.root / "teach.json"
        self.write(self.teach, dict(corpus=rows))
        self.source_sha = REAL.base.digest(self.teach)
        self.patch(runner, "material", proxy(REAL.material, SOURCE_SHA256=self.source_sha))
        material = REAL.material.build_material(rows)
        audit = REAL.material.audit_native(rows, material, self.tokenizer)
        self.materialroot.mkdir()
        for arm in runner.ARMS:
            self.write(self.materialroot / (arm + ".json"), dict(corpus=material["corpora"][arm]))
        for key in ("inventory", "source_records", "panels"):
            self.write(self.materialroot / (key + ".json"), material[key])
        self.write(self.materialroot / "token_audit.json", audit)
        self.write(self.materialroot / "manifest.json", dict(status="NATIVE_TOKEN_MATCHED_NO_FIT_NO_LAUNCH",
            model=str(self.model), pins=dict(source_sha256=self.source_sha, model_files=self.model_files,
            source_code_sha256=REAL.material.source_hashes()), recipe=REAL.material.RECIPE,
            sha256=REAL.base.tree_hashes(self.materialroot), source_path=str(self.teach)))
        self.parents = {seed: self.make_parent(seed) for seed in (0, 1, 2)}
        self.patch(runner, "PINS", self.pins)
        self.patch(runner, "BASELINE_PINS", self.baseline_pins)

    def patch(self, target, name, value):
        context = patch.object(target, name, value)
        result = context.start()
        self.addCleanup(context.stop)
        return result

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")

    def receipt(self, device="6", ok=True):
        return dict(ok=ok, reserved_seconds=0.0, device=device, returncode=0 if ok else 1,
                    reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True)

    def state(self, digest="before"):
        return {"lora_A": dict(shape=[1], dtype="float32", sha256=digest)}

    def make_parent(self, seed):
        root = self.root / ("original-seed" + str(seed))
        adapter = root / "fit_teach/adapter"
        adapter.mkdir(parents=True)
        config = REAL.old.config(str(self.model), "0")
        config.update(lr=3e-4, seed=seed)
        manifest = dict(config=config, steps=80, nonfinite_batches=0, corpus={"sha256": self.source_sha})
        self.write(adapter / "train_manifest.json", manifest)
        self.write(adapter / "adapter_config.json", {"fixture": True})
        (adapter / "adapter_model.safetensors").write_bytes(b"fixture only, not actual model weights")
        (adapter / "DONE").write_text("ok\n")
        self.states[str(adapter)] = self.state()
        REAL.old.seal(root, dict(model=str(self.model), model_files=self.model_files, config=config,
            corpus_sha256={"teach": self.source_sha}, replication={"seed": seed}))
        files = REAL.trainer._warm_inventory(adapter)
        worker = root / "fit_teach/worker"
        worker.mkdir()
        self.write(worker / "supervision.json", self.receipt("0"))
        fit = dict(status="FIT_COMPLETE_PENDING_PAIRED_READOUT", arm="teach", adapter=str(adapter), adapter_files=files)
        if seed == 0:
            fit.update(manifest=manifest, supervised=self.receipt("0"))
        else:
            fit.update(seed=seed, steps=80, plan_sha256=REAL.base.digest(root / "plan.json"),
                       supervision_sha256=REAL.base.digest(worker / "supervision.json"))
        fit_name = "result.json" if seed == 0 else "verified.json"
        self.write(root / "fit_teach" / fit_name, fit)
        readroot = root / "readouts/teach"
        (readroot / "run/data/calls").mkdir(parents=True)
        cases = REAL.readout.selected_cases()
        requests = REAL.readout.requests(cases)
        readplan = dict(schema=1, model=str(self.model), model_files=self.model_files, adapter=str(adapter), adapter_files=files,
            device="0", lease_end=float(self.lease_end), cases=cases, requests=requests,
            native_inputs=REAL.readout.native_inputs(self.tokenizer, requests), source_hashes={"historical": "not rewritten"},
            worker_seconds=600, output_token_ceiling=3072, claim_limits=REAL.readout.CLAIM_LIMITS)
        readplan["identity"] = REAL.base.expected_identity(readplan, str(adapter))
        REAL.old.seal(readroot, readplan)
        data = readroot / "run/data"
        scored = []
        for request, native, case in zip(requests, readplan["native_inputs"], cases):
            text = f"PREDICT: {case['expected']}\nACT: {case['expected']}" if case["kind"] == "addition" else "red"
            response = dict(text=text, rendered_prompt=native["rendered_prompt"], prompt_token_ids=native["prompt_token_ids"],
                            output_token_ids=self.tokenizer.encode(text), finish_reason="stop", stop_reason=None)
            self.write(data / "calls" / (request["call_id"] + ".request.json"), dict(request=request, identity=readplan["identity"],
                       prompt_sha256=REAL.base.value_hash(request["prompt"])))
            self.write(data / "calls" / (request["call_id"] + ".response.json"), dict(response=response, response_sha256=REAL.base.value_hash(response)))
            score = (REAL.readout.score_addition if case["kind"] == "addition" else REAL.readout.score_memory)(text, case["expected"])
            scored.append(dict(call_id=request["call_id"], case_id=case["id"], kind=case["kind"], **score))
        self.write(data / "backend.cleanup.json", {"closed": True})
        self.write(data / "identity.json", dict(backend=readplan["identity"], model_files=self.model_files, adapter_files=files))
        self.write(data / "manifest.json", dict(files=REAL.base.tree_hashes(data)))
        (readroot / "run/worker").mkdir()
        self.write(readroot / "run/worker/supervision.json", self.receipt("0"))
        self.write(readroot / "reduction.json", dict(complete=True, rows=scored, counts={"total": 48},
            plan_sha256=REAL.base.digest(readroot / "plan.json"), capture_sha256=REAL.base.digest(data / "manifest.json")))
        self.pins[seed] = tuple(REAL.base.digest(root / name) for name in
                               ("plan.json", "fit_teach/" + fit_name, "readouts/teach/plan.json"))
        self.baseline_pins[seed] = tuple(REAL.base.digest(readroot / name) for name in ("run/data/manifest.json", "reduction.json"))
        return root

    def prepare(self, seed=0, device="6"):
        runner.prepare(self.runroot, self.materialroot, self.parents[seed], seed, device,
                       self.deadline, self.lease_end, "Main test budget", "Main test logging")
        return REAL.old.read_plan(self.runroot)

    def make_fit(self, plan, row):
        adapter = Path(row["adapter"])
        adapter.mkdir(parents=True)
        parent = plan["parent"]
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", parent_path=row["parent"], parent_files=parent["parent_files"],
            parent_files_after=parent["parent_files"], parent_unchanged=True, base_frozen=True, initialized_loaded_state_check=True,
            adapter_count=1, phase_seed=plan["seed"], optimizer_initial_state_entries=0, optimizer_state_restored=False,
            optimizer_state_saved=False, optimizer_initialization="fresh_per_write", phase_steps=80,
            parent_cumulative_steps=80, cumulative_steps=160, source_state=parent["state"], initialized_state=parent["state"],
            final_state=self.state("after"))
        tokens = plan["material"]["tokens"][row["arm"]]
        manifest = dict(config=plan["config"], steps=80, micro_batches=80, epochs_run=4, nonfinite_batches=0, empty=False, final_loss=.2,
            corpus=dict(sha256=plan["material"]["files"][row["arm"] + ".json"], n_items=80, n_encoded=80, n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            tokens=dict(total=tokens["input_tokens"], target=tokens["target_tokens"]), train_tokens_seen=4 * tokens["input_tokens"],
            warm_start=warm)
        self.write(adapter / "train_manifest.json", manifest)
        self.write(adapter / "adapter_config.json", {"fixture": True})
        (adapter / "DONE").write_text("ok\n")
        (adapter / "adapter_model.safetensors").write_bytes(b"fixture, not weights")
        self.states[str(adapter)] = self.state("after")
        return manifest

    def test_prepare_seals_seed0_actual_result_path_and_allocation(self):
        plan = self.prepare()
        self.assertEqual(plan["device"], "6")
        self.assertEqual(plan["config"]["seed"], 0)
        self.assertTrue(any(path.endswith("fit_teach/result.json") for path in plan["parent"]["provenance"]))
        self.assertEqual(plan["parent"]["baseline"]["counts"]["addition"]["form_a"], 32)
        self.assertEqual(plan["parent"]["baseline"]["counts"]["addition"]["joint"], 0)
        self.assertEqual(runner.verify(self.runroot), plan)

    def test_each_replication_seed_uses_verified_parent(self):
        for seed, device in ((1, "7"), (2, "2")):
            with self.subTest(seed=seed):
                self.runroot = self.root / f"prepared-seed{seed}"
                plan = self.prepare(seed, device)
                self.assertEqual(plan["seed"], plan["config"]["seed"])
                self.assertEqual(plan["seed"], seed)
                self.assertEqual(plan["device"], device)
                self.assertTrue(any(path.endswith("fit_teach/verified.json") for path in plan["parent"]["provenance"]))

    def test_both_commands_parse_exact_recipe_and_never_chain(self):
        for seed in (0, 1, 2):
            with self.subTest(seed=seed):
                self.runroot = self.root / f"commands-seed{seed}"
                plan = self.prepare(seed)
                rows = [runner.arm_row(self.runroot / "run", plan, arm) for arm in runner.ARMS]
                self.assertEqual(rows[0]["parent"], rows[1]["parent"])
                self.assertNotEqual(rows[0]["adapter"], rows[1]["parent"])
                for row in rows:
                    command = runner.fit_command(plan, row)
                    args = REAL.trainer.build_parser().parse_args(command[4:])
                    self.assertEqual(asdict(REAL.trainer.config_from_args(args)), plan["config"])
                    self.assertEqual(args.init_adapter, plan["parent"]["parent"])
                    self.assertEqual(args.overflow, "truncate")
                    self.assertEqual(args.seed, seed)
                    self.assertEqual(args.lr, 1e-4)

    def test_prepare_requires_main_notes_device_and_full_future_window(self):
        for device in ("", "6,7", "-1", "06", None):
            with self.subTest(device=device), self.assertRaises(ValueError):
                runner.device_check(device)
        with self.assertRaisesRegex(ValueError, "declarations"):
            runner.prepare(self.runroot, self.materialroot, self.parents[0], 0, "6", self.deadline, self.lease_end, "", "logs")
        with self.assertRaisesRegex(ValueError, "full per-seed"):
            runner.prepare(self.runroot, self.materialroot, self.parents[0], 0, "6", time.time() + 1199, self.lease_end, "budget", "logs")
        for seed in (-1, 3, True):
            with self.assertRaises(ValueError):
                runner.config(str(self.model), seed)

    def test_scope_counts_and_original_requests_are_unchanged(self):
        plan = self.prepare()
        self.assertEqual(plan["counts"], dict(fits=2, steps_per_fit=80, updates=160, row_presentations=640,
            new_readout_calls=96, reused_H_calls=48, unrequested_cases=64, output_cap_tokens_not_usage=6144))
        self.assertEqual(plan["parent"]["readout"]["requests"], REAL.readout.requests(REAL.readout.selected_cases()))
        self.assertEqual(plan["controller_seconds"], 1200)
        self.assertEqual(plan["cleanup_seconds"], 140)

    def test_historical_baseline_bytes_not_rewritten(self):
        before = REAL.base.tree_hashes(self.parents[0])
        self.prepare()
        self.assertEqual(before, REAL.base.tree_hashes(self.parents[0]))

    def test_failed_missing_baseline_is_not_zero(self):
        path = self.parents[0] / "readouts/teach/run/data/calls/0000.response.json"
        path.unlink()
        with self.assertRaisesRegex(ValueError, "capture changed"):
            self.prepare()
        self.assertFalse(self.runroot.exists())

    def test_original_parent_and_capture_pins_fail_closed(self):
        for target, key in ((runner.PINS, 0), (runner.BASELINE_PINS, 0)):
            before = target[key]
            target[key] = tuple("0" * 64 for _ in before)
            with self.assertRaisesRegex(ValueError, "pinned original"):
                self.prepare()
            target[key] = before

    def test_original_adapter_file_and_result_drift_rejected(self):
        (self.parents[0] / "fit_teach/adapter/DONE").write_text("changed")
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.prepare()

    def test_injected_or_modified_material_rejected(self):
        path = self.materialroot / "manifest.json"
        manifest = REAL.base.read(path)
        manifest["status"] = "FIXTURE_ONLY_NOT_NATIVE_VALIDATION"
        self.write(path, manifest)
        with self.assertRaisesRegex(ValueError, "actual exported native"):
            self.prepare()

    def test_material_raw_target_tampering_rejected(self):
        path = self.materialroot / "input_after.json"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "material bytes"):
            self.prepare()

    def test_model_parent_baseline_material_and_source_drift_after_prepare(self):
        plan = self.prepare()
        paths = [self.model / "config.json", Path(plan["parent"]["parent"]) / "DONE",
                 Path(plan["parent"]["readout_root"]) / "reduction.json", self.materialroot / "input_before.json", self.teach]
        for path in paths:
            with self.subTest(path=path.name):
                saved = path.read_bytes()
                path.write_bytes(saved + b"\n")
                with self.assertRaises(ValueError):
                    runner.verify(self.runroot)
                path.write_bytes(saved)
        with patch.object(runner, "sources", return_value={}):
            with self.assertRaisesRegex(ValueError, "source/plan"):
                runner.verify(self.runroot)

    def test_fresh_output_no_resume_and_plan_seal(self):
        self.prepare()
        before = REAL.base.tree_hashes(self.runroot)
        with self.assertRaisesRegex(ValueError, "fresh runroot"):
            self.prepare()
        self.assertEqual(before, REAL.base.tree_hashes(self.runroot))
        (self.runroot / "plan.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "plan changed"):
            runner.verify(self.runroot)

    def test_fit_accepts_exact80_fresh_optimizer_and_states(self):
        plan = self.prepare(2)
        row = runner.arm_row(self.runroot / "run", plan, "input_before")
        self.make_fit(plan, row)
        fit = runner.verify_fit(plan, row)
        self.assertEqual(fit["steps"], 80)
        self.assertFalse(fit["parameter_state_unchanged"])

    def test_fit_rejects_recipe_steps_seed_optimizer_chain_and_native_drop(self):
        plan = self.prepare(1)
        row = runner.arm_row(self.runroot / "run", plan, "input_before")
        saved = self.make_fit(plan, row)
        faults = [("steps", 79), ("micro_batches", 79), ("nonfinite_batches", 1), ("epochs_run", 3),
                  ("config", "lr", 3e-5), ("config", "overflow", "split"),
                  ("truncation", "target_tokens_dropped", 1), ("truncation", "context_tokens_dropped", 1),
                  ("truncation", "items_split", 1), ("corpus", "n_items", 79), ("tokens", "target", 1),
                  ("warm_start", "phase_seed", 0), ("warm_start", "optimizer_state_restored", True),
                  ("warm_start", "optimizer_initial_state_entries", 1), ("warm_start", "cumulative_steps", 240),
                  ("warm_start", "initialized_loaded_state_check", False), ("warm_start", "adapter_count", 2)]
        for fault in faults:
            changed = copy.deepcopy(saved)
            if len(fault) == 2:
                changed[fault[0]] = fault[1]
            else:
                changed[fault[0]][fault[1]] = fault[2]
            self.write(Path(row["adapter"]) / "train_manifest.json", changed)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                runner.verify_fit(plan, row)
        self.write(Path(row["adapter"]) / "train_manifest.json", saved)
        with self.assertRaisesRegex(ValueError, "never chain"):
            runner.verify_fit(plan, dict(row, parent=row["adapter"]))

    def test_fit_state_and_parent_changes_rejected(self):
        plan = self.prepare()
        row = runner.arm_row(self.runroot / "run", plan, "input_before")
        self.make_fit(plan, row)
        self.states[row["adapter"]] = self.state("unrecorded")
        with self.assertRaisesRegex(ValueError, "parameter state differs"):
            runner.verify_fit(plan, row)

    def test_scoring_requires_complete_ordered48_and_separates_form_from_numbers(self):
        rows = REAL.base.read(self.parents[0] / "readouts/teach/reduction.json")["rows"]
        result = runner.score_panel(rows)
        self.assertEqual(result["counts"]["addition"]["form_a"], 32)
        for malformed in (rows[:-1], rows[::-1], [rows[0]] * 48):
            with self.assertRaises(ValueError):
                runner.score_panel(malformed)
        changed = copy.deepcopy(rows)
        changed[0]["raw_text"] = None
        with self.assertRaisesRegex(ValueError, "missing response"):
            runner.score_panel(changed)
        source_id = REAL.readout.selected_cases()[0]["source_event_ids"][0]
        event = next(row for row in REAL.material.original.build_candidate()["source_records"] if row["id"] == source_id)
        changed[0]["raw_text"] = f"INPUT: {event['left']}, {event['right']}\nPREDICT: -1\nACT: -1"
        scored = runner.score_panel(changed)["rows"][0]["score"]
        self.assertTrue(scored["joint"])
        self.assertFalse(scored["prediction_correct"])
        self.assertFalse(scored["act_success"])

    def test_symmetric_own_success_and_opposite_rejection_for_both_arms(self):
        events = {event["id"]: event for event in REAL.material.original.build_candidate()["source_records"]}
        for arm in runner.ARMS:
            rows = []
            for case in REAL.readout.selected_cases():
                if case["kind"] == "addition":
                    event = events[case["source_event_ids"][0]]
                    lines = [f"INPUT: {event['left']}, {event['right']}", f"PREDICT: {event['sum']}", f"ACT: {event['sum']}"]
                    raw = "\n".join(lines if arm == "input_before" else lines[1:] + lines[:1])
                else:
                    raw = case["expected"]
                rows.append(dict(case_id=case["id"], raw_text=raw))
            result = runner.score_panel(rows, arm)
            with self.subTest(arm=arm):
                counts = result["counts"]["addition"]
                self.assertEqual(counts["own_order_success"], 32)
                self.assertEqual(counts["opposite_order_count"], 0)
                self.assertEqual(counts["own_success_and_opposite_rejection"], 32)
                self.assertEqual(counts["opposite_order_rejected"], 32)
                self.assertEqual(counts["no_tag_spill"], 32)
                self.assertEqual(counts["original_adherence"], 32)
                self.assertEqual(result["counts"]["memory"]["tag_spill"], 0)
                opposite = next(other for other in runner.ARMS if other != arm)
                wrong = runner.score_panel(rows, opposite)["counts"]["addition"]
                self.assertEqual(wrong["own_order_success"], 0)
                self.assertEqual(wrong["opposite_order_rejected"], 0)
                self.assertEqual(wrong["opposite_order_count"], 32)

    def test_strict_after_never_repairs_prose_duplicates_source_or_numbers(self):
        cases = [
            ("PREDICT: 7\nACT: 7\nINPUT: 2, 5", True, True),
            ("PREDICT: 0\nACT: 7\nINPUT: 2, 5", True, False),
            ("PREDICT: 7\nACT: 0\nINPUT: 2, 5", True, False),
            ("PREDICT: 7\nACT: 7\nINPUT: 5, 2", False, False),
            ("PREDICT: 7\nACT: 7\nINPUT: 2, 5\nACT: 7", False, False),
            ("PREDICT: 7\nACT: 7\nINPUT: 2, 5\nDone", False, False),
            ("```\nPREDICT: 7\nACT: 7\nINPUT: 2, 5\n```", False, False),
            ("ACT: 7\nPREDICT: 7\nINPUT: 2, 5", False, False),
            ("PREDICT: 7\nACT: bad\nACT: 7\nINPUT: 2, 5", False, False),
        ]
        for raw, form, success in cases:
            with self.subTest(raw=raw):
                score = runner.score_orders(REAL.material.score_addition(raw, 2, 5))
                self.assertEqual(score["raw_text"], raw)
                self.assertEqual(score["input_after_order"], form)
                self.assertEqual(score["input_after_success"], success)

    def test_rejecting_both_orders_is_not_success_and_memory_tag_spill_is_counted(self):
        rows = [dict(case_id=case["id"], raw_text="") for case in REAL.readout.selected_cases()]
        rows[32]["raw_text"] = "INPUT: red"
        result = runner.score_panel(rows, "input_after")["counts"]
        self.assertEqual(result["addition"]["opposite_order_rejected"], 32)
        self.assertEqual(result["addition"]["own_success_and_opposite_rejection"], 0)
        self.assertEqual(result["addition"]["invalid_for_both_orders"], 32)
        self.assertEqual(result["memory"]["tag_spill"], 1)
        self.assertEqual(result["memory"]["invalid"], 16)

    def test_bounds_include_cpu_and_reserve_cleanup(self):
        started = time.time()
        self.assertEqual(runner.bounds(started, started + 5000, started + 6000), started + 1200)
        self.assertEqual(runner.bounds(started, started + 700, started + 6000), started + 700)
        self.assertEqual(runner.bounds(started, started + 5000, started + 810), started + 800)
        for limit in (float("nan"), float("inf"), started + 140):
            with self.assertRaises(ValueError):
                runner.bounds(started, limit, self.lease_end)

    def test_run_no_allow_or_wrong_device_cannot_start(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "explicit --allow-gpu"):
            runner.run(self.runroot)
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "7"}):
            with self.assertRaisesRegex(ValueError, "sealed single GPU"):
                runner.run(self.runroot, True)
        self.assertFalse((self.runroot / "run").exists())

    def fake_run(self, failure_arm=None, release=True):
        seen = []
        def execute(root, stage, plan, arm, effective):
            seen.append((arm, runner.arm_row(stage, plan, arm)["parent"], effective))
            if arm == failure_arm:
                raise RuntimeError("fixture bounded failure")
            return dict(arm=arm)
        self.patch(runner, "execute_arm", execute)
        self.patch(runner, "release_summary", lambda *args: ([self.receipt()] * 4, release))
        return seen

    def test_controller_two_sequential_arms_full_cost_and_no_retry(self):
        self.prepare()
        seen = self.fake_run()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            terminal = runner.run(self.runroot, True)
            with self.assertRaisesRegex(ValueError, "fresh runroot"):
                runner.run(self.runroot, True)
        self.assertEqual([row[0] for row in seen], list(runner.ARMS))
        self.assertEqual(seen[0][1:], seen[1][1:])
        self.assertEqual(terminal["status"], "COMPLETE")
        self.assertGreaterEqual(terminal["reserved_seconds"], terminal["worker_reserved_seconds"])
        self.assertLessEqual(terminal["reserved_seconds"], 1200)
        self.assertTrue(terminal["release_verified"])

    def test_partial_seed_keeps_first_result_does_not_retry_or_score_failure_zero(self):
        self.prepare()
        seen = self.fake_run(failure_arm="input_after")
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            with self.assertRaisesRegex(ValueError, "partial seed"):
                runner.run(self.runroot, True)
        terminal = REAL.base.read(self.runroot / "run/terminal.json")
        self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")
        self.assertEqual(len(terminal["arms"]), 1)
        self.assertEqual(len(seen), 2)
        self.assertEqual(terminal["error"]["type"], "RuntimeError")

    def test_release_failure_prevents_complete(self):
        self.prepare()
        self.fake_run(release=False)
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            with self.assertRaisesRegex(ValueError, "partial seed"):
                runner.run(self.runroot, True)
        self.assertFalse(REAL.base.read(self.runroot / "run/terminal.json")["release_verified"])

    def test_release_summary_requires_all_process_receipts_and_gpu_absence(self):
        stage = self.root / "cost-fixture"
        worker = stage / "fit-worker"
        worker.mkdir(parents=True)
        self.write(worker / "process.json", {"fixture": True})
        supervisor = proxy(REAL.base.supervisor, gpu_processes_absent=lambda device: True)
        self.patch(runner, "base", proxy(runner.base, supervisor=supervisor))
        with self.assertRaisesRegex(ValueError, "missing supervision"):
            runner.release_summary(stage, "6")
        self.write(worker / "supervision.json", self.receipt())
        self.assertTrue(runner.release_summary(stage, "6")[1])
        self.write(worker / "supervision.json", self.receipt("7"))
        with self.assertRaisesRegex(ValueError, "cost/device"):
            runner.release_summary(stage, "6")

    def test_accounting_error_reports_unknown_worker_time_not_zero(self):
        self.prepare()
        self.fake_run()
        def failure(*args):
            raise ValueError("missing worker receipt")
        self.patch(runner, "release_summary", failure)
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            with self.assertRaisesRegex(ValueError, "partial seed"):
                runner.run(self.runroot, True)
        terminal = REAL.base.read(self.runroot / "run/terminal.json")
        self.assertIsNone(terminal["worker_reserved_seconds"])
        self.assertFalse(terminal["worker_accounting_complete"])
        self.assertFalse(terminal["release_verified"])

    def test_cpu_time_before_run_is_inside_outer_alarm_and_full_time(self):
        self.prepare()
        self.fake_run()
        timers = []
        self.patch(runner, "signal", proxy(runner.signal, setitimer=lambda timer, seconds: timers.append(seconds)))
        clock = time.time() - 100, time.monotonic() - 100
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            terminal = runner.run(self.runroot, True, clock=clock)
        self.assertGreaterEqual(terminal["reserved_seconds"], 100)
        self.assertGreater(timers[0], 900)
        self.assertLessEqual(timers[0], 960)
        self.assertEqual(timers[-1], 0)

    def test_worker_total_cannot_exceed_full_controller_time(self):
        self.prepare()
        self.fake_run()
        receipts = [dict(self.receipt(), reserved_seconds=1000)] * 4
        self.patch(runner, "release_summary", lambda *args: (receipts, True))
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            with self.assertRaisesRegex(ValueError, "partial seed"):
                runner.run(self.runroot, True)
        terminal = REAL.base.read(self.runroot / "run/terminal.json")
        self.assertEqual(terminal["worker_reserved_seconds"], 4000)
        self.assertEqual(terminal["status"], "FAILED_PARTIAL_NO_RETRY")

    def test_monotonic1200_limit_even_if_wall_clock_within_deadline(self):
        self.prepare()
        self.fake_run()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "6"}):
            with self.assertRaisesRegex(ValueError, "partial seed"):
                runner.run(self.runroot, True, clock=(time.time(), time.monotonic() - 1201))
        terminal = REAL.base.read(self.runroot / "run/terminal.json")
        self.assertFalse(terminal["deadline_met"])

    def test_execute_arm_routes_sealed_device_and_exact_raw_scoring(self):
        plan = self.prepare(seed=2, device="7")
        stage = self.runroot / "run"
        stage.mkdir()
        calls = []
        def supervise(root, active, worker, command, call_path=None):
            calls.append((root, active, command, call_path))
            worker.mkdir(parents=True)
            receipt = self.receipt("7")
            self.write(worker / "supervision.json", receipt)
            if call_path is None:
                self.make_fit(plan, runner.arm_row(stage, plan, "input_before"))
            return receipt
        def reduce(readroot):
            rows = REAL.base.read(self.parents[2] / "readouts/teach/reduction.json")["rows"]
            result = dict(complete=True, counts={"total": 48}, rows=rows)
            self.write(readroot / "reduction.json", result)
            return result
        self.patch(runner, "base", proxy(runner.base, supervise=supervise))
        self.patch(runner, "readout", proxy(REAL.readout, verify=lambda root: None, reduce=reduce))
        result = runner.execute_arm(self.runroot, stage, plan, "input_before", self.deadline)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[1]["device"] == "7" for call in calls))
        self.assertTrue(all(call[0] == stage for call in calls))
        self.assertEqual(result["counts"]["total"], 48)
        newplan = REAL.old.read_plan(stage / "input_before/readout")
        for key in ("cases", "requests", "native_inputs"):
            self.assertEqual(newplan[key], plan["parent"]["readout"][key])
        self.assertEqual(newplan["source_hashes"], REAL.readout.sources())
        self.assertNotEqual(newplan["adapter"], plan["parent"]["parent"])
        self.assertEqual(newplan["device"], "7")


class CapsulePinsTests(unittest.TestCase):
    def test_available_original_local_capsules_match_hardcoded_pins(self):
        roots = {
            0: Path('/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1'),
            1: Path('/tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_replications_20260912_attempt1/seed1'),
            2: Path('/tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_replications_20260912_attempt1/seed2'),
        }
        for seed, root in roots.items():
            if not root.exists():
                self.skipTest('local capsule provenance check requires archived local capsules')
            with self.subTest(seed=seed):
                fit = "result.json" if seed == 0 else "verified.json"
                self.assertEqual(tuple(REAL.base.digest(root / name) for name in
                    ("plan.json", "fit_teach/" + fit, "readouts/teach/plan.json")), runner.PINS[seed])
                readroot = root / "readouts/teach"
                self.assertEqual(tuple(REAL.base.digest(readroot / name) for name in
                    ("run/data/manifest.json", "reduction.json")), runner.BASELINE_PINS[seed])


if __name__ == "__main__":
    unittest.main(verbosity=2)
