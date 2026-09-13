"""CPU fixtures/mocked native backend; no native tokenizer/model/GPU calls."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import astra_l2_high_seed2_greedy_20260913 as greedy


ACCESS = greedy.load_pinned("_greedy_fixture_access", "/tmp/astra_l2_access_high_seed2_20260913.py", greedy.ACCESS_PIN)
SOURCE = ACCESS.frozen_source("/tmp/astra_l2_lr_source_20260913_attempt1")
RUNTIME = ACCESS.load_module("_greedy_fixture_runtime", SOURCE / "gpu/astra_l2_public_record_dev.py")
CORE = ACCESS.load_module("_greedy_fixture_core", SOURCE / "organism_v6/l2_public_record_dev.py")
WORLD = CORE.build_world(2026091301, 2026091302)
PUBLIC = CORE.public_view(WORLD)


def fixture():
    cases, calls, targets = [], {view: [] for view in greedy.VIEWS}, {}
    for view in greedy.VIEWS:
        for index, slot in enumerate(PUBLIC.slots):
            native = dict(actual_system_text=RUNTIME.GENERIC_SYSTEM, rendered_prompt=f"fixture:{view}:{index}",
                          prompt_token_ids=[101, index + 200, 103])
            message = [{"role": "system", "content": RUNTIME.GENERIC_SYSTEM},
                       {"role": "user", "content": f"fixture:{view}:{index}"}]
            calls[view].append(dict(slot_id=slot.slot_id, messages=message, native=native))
            targets[slot.slot_id] = (WORLD.success_actions[index] + "\n").encode().hex()
            cases.append(dict(view=view, slot_index=index, slot_id=slot.slot_id,
                              candidates=[dict(action=action, suffix="\n", native=native) for action in PUBLIC.actions]))
    calls["wake"] = copy.deepcopy(calls["train"])
    ctx = SimpleNamespace(core=CORE, runtime=RUNTIME, world=WORLD, calls=calls, targets=targets, cases=cases,
                          routes={"OFF": None, "fit2_PROMOTE": dict(name="l2_public_record", id=1,
                            path="/fixture/adapter", sha256=ACCESS.CANDIDATES["fit2_PROMOTE"])},
                          custody={}, access=ACCESS)
    rows = greedy.expected_rows(ctx, cases)
    return ctx, rows


def response(row, route=None, raw=None):
    text = WORLD.success_actions[row["slot_index"]] if raw is None else raw
    return dict(route=route, native=copy.deepcopy(row["native"]), returned_prompt_token_ids=row["native"]["prompt_token_ids"],
                raw_hex=text.encode().hex(), text=text, decoded=text, output_token_ids=[11, 12],
                finish_reason="stop", stop_reason=None, started=1.0, ended=1.1)


class GreedyTests(unittest.TestCase):
    def test_exact_archived_case_order_and_targets(self):
        ctx, rows = fixture()
        self.assertEqual(len(rows), 32)
        self.assertEqual([(row["view"], row["slot_index"]) for row in rows],
                         [(view, index) for view in greedy.VIEWS for index in range(16)])
        self.assertEqual(rows[0]["messages"], ctx.calls["train"][0]["messages"])
        self.assertEqual(rows[0]["archived_target_hex"], ctx.targets[rows[0]["slot_id"]])

    def test_bad_prefix_target_slot_or_missing_case_rejected(self):
        for change in ("prefix", "target", "slot", "order", "missing"):
            ctx, rows = fixture()
            cases = copy.deepcopy(ctx.cases)
            if change == "prefix":
                cases[0]["candidates"][0]["native"]["rendered_prompt"] += "changed"
            elif change == "target":
                ctx.targets[cases[0]["slot_id"]] = b"teacher replacement".hex()
            elif change == "slot":
                cases[0]["slot_index"] = False
            elif change == "order":
                cases.reverse()
            else:
                cases.pop()
            with self.subTest(change=change), self.assertRaises(ValueError):
                greedy.expected_rows(ctx, cases)

    def test_exactly32_native_generations_per_state_preserves_raw(self):
        ctx, rows = fixture()
        for state in greedy.STATES:
            events, messages = [], []
            def generate(actual_messages):
                index = len(messages)
                messages.append(copy.deepcopy(actual_messages))
                return response(rows[index], ctx.routes[state])
            backend = SimpleNamespace(generate=generate)
            count = greedy.generate_rows(rows, backend, RUNTIME, ctx.routes[state], lambda: None,
                                         lambda *event: events.append(event))
            self.assertEqual(count, 32)
            self.assertEqual(messages, [row["messages"] for row in rows])
            self.assertEqual(len(events), 64)
            self.assertEqual(events[0][1], "request")
            self.assertEqual(events[1][1], "response")

    def test_original_native_class_settings_and_lora_request_mocked(self):
        ctx, rows = fixture()
        row = rows[0]
        tokenizer = SimpleNamespace(chat_template="fixture", decode=lambda tokens, skip_special_tokens: WORLD.success_actions[0])
        public_probe = SimpleNamespace(native_tokenizer=lambda model: tokenizer, render=lambda tok, messages: row["native"])
        item = SimpleNamespace(text=WORLD.success_actions[0], token_ids=[11, 12], finish_reason="stop", stop_reason=None)
        engine = Mock()
        engine.generate.return_value = [SimpleNamespace(outputs=[item], prompt_token_ids=row["native"]["prompt_token_ids"])]
        llm, sampling, lora = Mock(return_value=engine), Mock(), Mock()
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(LLM=llm, SamplingParams=sampling),
                                      "vllm.lora.request": SimpleNamespace(LoRARequest=lora)}):
            for state in greedy.STATES:
                route = ctx.routes[state]
                native = RUNTIME.Native(dict(spec=dict(model="/fixture/model"), chat_template="fixture"), public_probe, route)
                captured = native.generate(row["messages"])
                greedy.validate_generated(RUNTIME, row, captured, route)
                self.assertEqual(engine.generate.call_args.kwargs["lora_request"], None if state == "OFF" else lora.return_value)
                sampling.assert_called_with(**RUNTIME.PARAMS)
                llm.assert_called_with(model="/fixture/model", tokenizer="/fixture/model", **RUNTIME.ENGINE)
        self.assertEqual(RUNTIME.PARAMS["max_tokens"], 32)
        self.assertEqual(RUNTIME.PARAMS["temperature"], 0.0)
        lora.assert_called_once_with("l2_public_record", 1, "/fixture/adapter")

    def test_drifted_native_route_prefix_bytes_and_tokens_failclosed(self):
        ctx, rows = fixture()
        for field, value in (("route", {"unexpected": True}), ("raw_hex", "00"),
                             ("returned_prompt_token_ids", [9]), ("output_token_ids", [True]),
                             ("finish_reason", "other"), ("ended", float("nan"))):
            captured = response(rows[0])
            captured[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                greedy.validate_generated(RUNTIME, rows[0], captured, None)
        captured = response(rows[0])
        captured["native"]["rendered_prompt"] += "rewritten"
        with self.assertRaises(ValueError):
            greedy.validate_generated(RUNTIME, rows[0], captured, None)

    def test_query_failure_or_deadline_does_not_continue_generations(self):
        ctx, rows = fixture()
        backend = Mock()
        backend.generate.side_effect = RuntimeError("mock native failure")
        emitted = []
        with self.assertRaises(RuntimeError):
            greedy.generate_rows(rows, backend, RUNTIME, None, lambda: None, lambda *args: emitted.append(args))
        self.assertEqual(backend.generate.call_count, 1)
        self.assertEqual(len(emitted), 1)
        backend.reset_mock()
        with self.assertRaises(ValueError):
            greedy.generate_rows(rows, backend, RUNTIME, None, lambda: greedy.check_deadline(0), lambda *args: None)
        backend.generate.assert_not_called()

    def test_original_scoring_not_teacher_forced_or_repaired(self):
        ctx, rows = fixture()
        responses = [response(row, raw=WORLD.success_actions[row["slot_index"]] + "\n") for row in rows]
        responses[0] = response(rows[0], raw="explanation " + WORLD.success_actions[0])
        responses[1]["finish_reason"] = "length"
        panels = greedy.score_rows(ctx, rows, responses)
        self.assertEqual(panels["train"]["correct"], 15)
        self.assertEqual(panels["train"]["stop_correct"], 14)
        self.assertEqual(panels["train"]["old_correct"], 7)
        self.assertEqual(panels["readout"]["correct"], 16)
        self.assertEqual(panels["train"]["exact_archived_targets"], 15)
        with self.assertRaises(ValueError):
            greedy.score_rows(ctx, rows, responses[:-1])

    def test_strict_source_and_json_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.py"
            path.write_text("raise AssertionError('must not run')")
            with self.assertRaises(ValueError):
                greedy.load_pinned("bad", path, greedy.ACCESS_PIN)
            for text in ('{"x":1,"x":2}', '{"value":NaN}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    greedy.read(path)
            with self.assertRaises(ValueError):
                greedy.encoded({"value": float("inf")})

    def test_all_process_release_not_compute_only(self):
        helper = SimpleNamespace(precheck=Mock())
        probe = SimpleNamespace(gpu_state=Mock(return_value=False))
        ctx = SimpleNamespace(probe=probe)
        settings = dict(gpu_index=3, gpu_uuid="fixture-uuid")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "all-process XML"):
                greedy.allocation_check(helper, ctx, settings, Path(temporary), "release", time.time() + 200)
            helper.precheck.assert_called_once()
            probe.gpu_state.assert_called_once_with(settings)
            self.assertFalse(greedy.read(Path(temporary) / "release.json")["vacant"])

    def test_owned_subprocess_timeout_uses_bound_cleanup(self):
        helper = SimpleNamespace(environment=Mock(return_value={}), identity=Mock(return_value=dict(pid=123, start_ticks=7, pgid=123)),
                                 stop_owned=Mock())
        process = Mock(pid=123)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        with tempfile.TemporaryDirectory() as temporary, patch.object(greedy.subprocess, "Popen", return_value=process) as popen:
            with self.assertRaises(subprocess.TimeoutExpired):
                greedy.run_child(helper, ["fixture"], Path(temporary), "OFF", time.time() + 1)
            self.assertTrue(popen.call_args.kwargs["start_new_session"])
            helper.stop_owned.assert_called_once_with(process, helper.identity.return_value)

    def make_completed(self, directory):
        root = directory / "greedy_fixture"
        root.mkdir()
        ctx, rows = fixture()
        started = time.time() - 10
        deadline = started + greedy.TOTAL_SECONDS
        pin = "fixture-prepared"
        manifest = dict(runtime_sha256=greedy.digest(greedy.__file__), rows=rows)
        greedy.write(root / "prepared.json", manifest)
        pin = greedy.digest(root / "prepared.json")
        greedy.write(root / "controller_started.json", dict(prepared_sha256=pin, started_unix=started, deadline_unix=deadline))
        ctx.access = SimpleNamespace(ROOT=directory / "old", PLAN_PIN=ACCESS.PLAN_PIN,
                                     CANDIDATES=ACCESS.CANDIDATES, COLLECTION_PIN=ACCESS.COLLECTION_PIN)
        completed = {}
        for ordinal, state in enumerate(greedy.STATES):
            state_dir = root / state
            state_dir.mkdir()
            pid = 999999991 + ordinal
            greedy.write(state_dir / "started.json", dict(pid=pid))
            for index, row in enumerate(rows):
                greedy.write(state_dir / f"{index:02d}.request.json", row)
                greedy.write(state_dir / f"{index:02d}.response.json", response(row, ctx.routes[state]))
            greedy.write(state_dir / "complete.json", dict(state=state, pid=pid, calls=32, fits=0, updates=0,
                prepared_sha256=pin, files=RUNTIME.tree(state_dir), candidate_sha256=ACCESS.CANDIDATES[state],
                started_unix=started + 1, ended_unix=started + 2))
            greedy.write(root / f"{state}.launch.json", dict(identity=dict(pid=pid)))
            greedy.write(root / f"{state}.all_process_release.json", dict(vacant=True))
            completed[state] = RUNTIME.tree(state_dir)
        greedy.write(root / "capture_complete.json", dict(prepared_sha256=pin, states=completed))
        return root, pin, deadline, manifest, ctx

    def test_collection_exact64_once_and_original_custody(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, pin, deadline, manifest, ctx = self.make_completed(Path(temporary))
            with patch.object(greedy, "load_prepared", return_value=(manifest, ctx)), patch.object(RUNTIME, "custody", return_value=({}, {})), patch.dict(greedy.os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
                result = greedy.collect(root, pin, deadline)
                self.assertEqual(result["calls"], 64)
                report = greedy.read(Path(result["output"]) / "report.json")
                self.assertEqual(set(report["states"]), set(greedy.STATES))
                self.assertIsNone(report["scientific_pass"])
                with self.assertRaisesRegex(ValueError, "already claimed"):
                    greedy.collect(root, pin, deadline)

    def test_incomplete_collection_fails_and_claim_persists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, pin, deadline, manifest, ctx = self.make_completed(Path(temporary))
            (root / "fit2_PROMOTE/31.response.json").unlink()
            with patch.object(greedy, "load_prepared", return_value=(manifest, ctx)), patch.dict(greedy.os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
                with self.assertRaises(ValueError):
                    greedy.collect(root, pin, deadline)
                output = root.with_name(root.name + "_collected")
                self.assertTrue((output / "collection_failure.json").exists())
                self.assertFalse((output / "report.json").exists())
                with self.assertRaisesRegex(ValueError, "already claimed"):
                    greedy.collect(root, pin, deadline)

    def test_native_worker_requires_permission_fixed_state_finite_deadline(self):
        for allowed, state, deadline in ((False, "OFF", time.time() + 30), (True, "fit1", time.time() + 30),
                                         (True, "OFF", float("nan")), (True, "OFF", time.time() + 500)):
            with self.assertRaises(ValueError):
                greedy.worker("/fixture", "pin", state, deadline, allow_native=allowed)

    def test_controller_serial_states_and_collect_share1200_deadline(self):
        ctx, rows = fixture()
        settings = dict(controller_helper="/fixture/helper", gpu_index=3, gpu_uuid="fixture-uuid")
        manifest = dict(settings=settings)
        helper = SimpleNamespace(GPU_INDEX=3, GPU_UUID="fixture-uuid")
        children = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "newroot"
            root.mkdir()
            def child(helper, command, directory, label, deadline, device=""):
                children.append((command, label, deadline, device))
                if label in greedy.STATES:
                    (root / label).mkdir()
                else:
                    output = root.with_name(root.name + "_collected")
                    output.mkdir()
                    greedy.write(output / "collection.json", dict(status="COMPLETE_DIAGNOSTIC_ONLY"))
            with patch.object(greedy, "load_prepared", return_value=(manifest, ctx)), \
                 patch.object(greedy, "load_pinned", return_value=helper), \
                 patch.object(greedy, "allocation_check") as allocation, \
                 patch.object(greedy, "run_child", side_effect=child), \
                 patch.dict(greedy.os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
                terminal = greedy.controller(root, "fixture-pin", allow_gpu=True)
                self.assertEqual(terminal["status"], "COMPLETE_DIAGNOSTIC_ONLY")
                self.assertEqual([item[1] for item in children], ["OFF", "fit2_PROMOTE", "collect"])
                self.assertEqual([item[3] for item in children], ["fixture-uuid", "fixture-uuid", ""])
                self.assertEqual(allocation.call_count, 4)
                started = greedy.read(root / "controller_started.json")
                self.assertEqual(started["deadline_unix"] - started["started_unix"], 1200)
                self.assertTrue(all(item[2] < started["deadline_unix"] for item in children))
                with self.assertRaisesRegex(ValueError, "already attempted"):
                    greedy.controller(root, "fixture-pin", allow_gpu=True)

    def test_controller_failure_preserved_release_attempted_no_collection(self):
        ctx, rows = fixture()
        manifest = dict(settings=dict(controller_helper="/fixture/helper", gpu_index=3, gpu_uuid="fixture-uuid"))
        helper = SimpleNamespace(GPU_INDEX=3, GPU_UUID="fixture-uuid")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(greedy, "load_prepared", return_value=(manifest, ctx)), \
                 patch.object(greedy, "load_pinned", return_value=helper), \
                 patch.object(greedy, "allocation_check") as allocation, \
                 patch.object(greedy, "run_child", side_effect=RuntimeError("mock worker failed")) as child, \
                 patch.dict(greedy.os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
                with self.assertRaisesRegex(ValueError, "diagnostic failed"):
                    greedy.controller(root, "fixture-pin", allow_gpu=True)
                self.assertEqual(child.call_count, 1)
                self.assertEqual(allocation.call_count, 2)
                self.assertFalse((root / "capture_complete.json").exists())
                self.assertEqual(greedy.read(root / "terminal.json")["status"], "FAILED_NO_RETRY")


if __name__ == "__main__":
    unittest.main()
