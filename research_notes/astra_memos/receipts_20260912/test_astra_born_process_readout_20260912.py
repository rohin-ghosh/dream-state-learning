"""Synthetic CPU-only fixtures. No real model paths, weights or outcomes are read."""
from __future__ import annotations

from contextlib import ExitStack
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("born_adapter", "/tmp/astra_born_process_readout_20260912.py")
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def receipt(**values):
    return dict(values, receipt_sha256=adapter.value_hash(values))


def reseal(values):
    values["receipt_sha256"] = adapter.value_hash({key: value for key, value in values.items() if key != "receipt_sha256"})


def fixture_lineage():
    diagnostic, corpus, _, driver = adapter._helpers()
    candidate = corpus.build_candidate()
    source = receipt(files=dict(adapter.REQUIRED_SOURCE_PINS))
    base = receipt(model="/synthetic-cpu-only/Qwen2.5-7B-Instruct", model_files={"config.json": adapter.value_hash("base")})

    def fitted(cell):
        files = {"adapter_config.json": adapter.value_hash("config"),
                 "adapter_model.safetensors": adapter.value_hash(cell)}
        path = "/synthetic-cpu-only/" + cell
        identity = dict(backend="vllm", model_input=base["model"], adapter_input=path, adapter_files=files,
                        default_max_tokens=400, default_temperature=0.7,
                        scope="configured loader inputs; base authentication requires lineage pins")
        return dict(release=dict(sha256=adapter.value_hash("synthetic release " + cell), status="COMPLETE"),
                    source_receipt_sha256=source["receipt_sha256"], base_receipt_sha256=base["receipt_sha256"],
                    adapter=path, adapter_files=files, identity=identity)

    birth = receipt(**fitted("BIRTH_ONLY"), arm="AUTH", root=candidate["root"],
                    candidate_sha256=corpus.digest(candidate), panel_sha256=adapter.value_hash(driver.fixed_requests(corpus, candidate)))
    writes = {cell: receipt(**fitted(cell), parent_birth_receipt_sha256=birth["receipt_sha256"],
                           parent_adapter_files_sha256=adapter.value_hash(birth["adapter_files"]),
                           formation_receipt_sha256=adapter.value_hash("synthetic formation"), own_wake_arm=cell[0],
                           material_sha256=adapter.value_hash("synthetic own wake " + cell), warm_start=True)
              for cell in ("P_WRITE", "A_WRITE")}
    lineage = dict(schema=adapter.SCHEMA, source=source, base=base, birth=birth, writes=writes,
                   claim=adapter.CLAIM, origin=adapter.ORIGIN)
    assert adapter.value_hash(lineage) == diagnostic.value_hash(lineage)
    return lineage, candidate


class SyntheticBackend:
    def __init__(self, lineage, cell, candidate, mode="full"):
        self.binding = adapter.validate_lineage(lineage)[cell]["identity"]
        self.cell, self.mode = cell, mode
        _, corpus, _, _ = adapter._helpers()
        self.answers = {case["id"]: corpus.response_text(case, "AUTH") for case in candidate["dev"]}

    def identity(self):
        return copy.deepcopy(self.binding)

    def generate(self, request):
        if request["role"] == "readout":
            text = "" if self.cell == "BIRTH_ONLY" else self.answers[request["case_id"]]
            if self.cell == "A_WRITE":
                text += "\nPREDICT: invalid spill"
        elif request["role"] == "record":
            text = "invalid record SENTINEL_NOT_WAKE_CONTEXT"
        elif self.mode == "done":
            text = "DONE"
        elif self.mode == "invalid":
            text = "PREDICT: T\nACT: TRY 1,2,3\nACT: QUIZ ?"
        elif request["tick"] <= 3:
            text = "PREDICT: T\nACT: TRY -1,2,3"
        elif request["tick"] == 4:
            text = "ACT: QUIZ ?"
        else:
            text = "ACT: QUIZ T,T,T,T,T,T"
        assert "SENTINEL_NOT_WAKE_CONTEXT" not in request["prompt"]
        assert "Temporary parent restatement:" not in request["prompt"]
        response = dict(text=text, rendered_prompt="SYNTHETIC CHAT " + request["prompt"],
                    prompt_token_ids=[101, 0, 102], output_token_ids=[7] * (64 if request["role"] == "readout" else 2),
                    finish_reason="length" if request["role"] == "readout" else "stop", stop_reason=42)
        if self.mode == "broken" and request["role"] == "readout" and request["call_id"] == "0127":
            response["prompt_token_ids"] = []
        return response


def fixture_worker(out, cell, mode):
    lineage, candidate = fixture_lineage()
    diagnostic, corpus, legacy, _ = adapter._helpers()
    backend = SyntheticBackend(lineage, cell, candidate, mode)
    with ExitStack() as stack:
        for module, name in ((diagnostic, "run_evaluation"), (diagnostic, "usage"),
                             (legacy, "process_metrics"), (corpus, "score_outputs"),
                             (diagnostic, "NativeBackend"), (diagnostic, "native_tokenizer")):
            stack.enter_context(mock.patch.object(module, name, side_effect=AssertionError("forbidden capture action: " + name)))
        captured = adapter.capture_cell(out, lineage, cell, candidate, backend, worker_id="fixture-" + cell)
    for forbidden in ("torch", "transformers", "vllm"):
        assert forbidden not in sys.modules, forbidden
    try:
        adapter.capture_rulegame(Path(out) / "retry", lineage, cell, backend, worker_id="fixture-" + cell)
        raise AssertionError("same-worker panel retry accepted")
    except ValueError:
        pass
    other = "A_WRITE" if cell != "A_WRITE" else "P_WRITE"
    try:
        adapter.capture_rulegame(Path(out) / "other", lineage, other,
                                SyntheticBackend(lineage, other, candidate), worker_id="another-worker")
        raise AssertionError("cross-cell process reuse accepted")
    except ValueError:
        pass
    print(json.dumps(dict(captures=captured, pid=os.getpid(), worker_id="fixture-" + cell)))


class BornReadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory(prefix="born-readout-cpu-")
        cls.root = Path(cls.fixture_dir.name)
        cls.lineage, cls.candidate = fixture_lineage()
        cls.captures, cls.exits = cls.make_run(cls.root / "full", "full")

    @classmethod
    def tearDownClass(cls):
        cls.fixture_dir.cleanup()

    @classmethod
    def make_run(cls, root, mode):
        root.mkdir()
        captures, exits = {}, {}
        for cell in adapter.CELLS:
            completed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--fixture", str(root / cell), cell, mode],
                                       capture_output=True, text=True, timeout=60, check=True,
                                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            saved = json.loads(completed.stdout)
            captures[cell] = {panel: saved["captures"][panel]["path"] for panel in ("rulegame", "conditional")}
            exits[cell] = dict(pid=saved["pid"], worker_id=saved["worker_id"], returncode=completed.returncode, backend_closed=True,
                               capture_manifest_sha256={panel: saved["captures"][panel]["manifest_sha256"]
                                                        for panel in ("rulegame", "conditional")})
        return captures, exits

    def reduced(self, captures=None, exits=None):
        return adapter.reduce_joint(captures or self.captures, self.lineage, self.candidate, exits or self.exits)

    def test_lineage_exact_source_base_birth_parent_joins(self):
        self.assertEqual(set(adapter.validate_lineage(self.lineage)), set(adapter.CELLS))
        cases = [
            ("P_WRITE", "parent_birth_receipt_sha256", adapter.value_hash("other birth")),
            ("A_WRITE", "parent_adapter_files_sha256", adapter.value_hash("other parent")),
            ("P_WRITE", "source_receipt_sha256", adapter.value_hash("source drift")),
            ("P_WRITE", "base_receipt_sha256", adapter.value_hash("base drift")),
            ("A_WRITE", "formation_receipt_sha256", adapter.value_hash("other formation")),
            ("P_WRITE", "warm_start", False),
            ("P_WRITE", "own_wake_arm", "A"),
        ]
        for cell, field, value in cases:
            with self.subTest(cell=cell, field=field):
                lineage = copy.deepcopy(self.lineage)
                lineage["writes"][cell][field] = value
                reseal(lineage["writes"][cell])
                with self.assertRaises(ValueError):
                    adapter.validate_lineage(lineage)

    def test_lineage_rejects_unreleased_auth_off_stacked_and_aliased(self):
        for mutation in ("incomplete", "off", "deranged", "stack", "alias", "hash", "extra", "source", "base"):
            with self.subTest(mutation=mutation):
                lineage = copy.deepcopy(self.lineage)
                target = lineage["writes"]["P_WRITE"]
                if mutation == "incomplete":
                    target["release"]["status"] = "PENDING"
                elif mutation == "off":
                    target["adapter"] = None
                elif mutation == "deranged":
                    lineage["birth"]["arm"] = "DERANGED"
                    reseal(lineage["birth"])
                elif mutation == "stack":
                    target["adapter_files"]["second_adapter.safetensors"] = adapter.value_hash("stack")
                elif mutation == "alias":
                    target["adapter"] = lineage["birth"]["adapter"]
                    target["identity"]["adapter_input"] = target["adapter"]
                elif mutation == "hash":
                    target["receipt_sha256"] = "bad"
                elif mutation == "extra":
                    target["formation_notes"] = "forbidden"
                elif mutation == "source":
                    lineage["source"]["files"].clear()
                    reseal(lineage["source"])
                elif mutation == "base":
                    target["identity"]["model_input"] = "/other-base"
                if mutation != "hash":
                    reseal(target)
                with self.assertRaises(ValueError):
                    adapter.validate_lineage(lineage)

    def test_equal_material_or_output_bytes_do_not_select_away_nulls(self):
        lineage = copy.deepcopy(self.lineage)
        for target in lineage["writes"].values():
            target["material_sha256"] = adapter.value_hash("identical but separately sourced own wake")
            target["adapter_files"] = copy.deepcopy(lineage["birth"]["adapter_files"])
            target["identity"]["adapter_files"] = target["adapter_files"]
            reseal(target)
        self.assertEqual(set(adapter.validate_lineage(lineage)), set(adapter.CELLS))

    def test_conditional_panel_exact_frozen_driver_and_exposure(self):
        _, corpus, _, driver = adapter._helpers()
        fixed = adapter.conditional_requests(self.lineage, self.candidate)
        self.assertEqual(fixed, driver.fixed_requests(corpus, self.candidate))
        self.assertEqual(len(fixed), 128)
        with self.assertRaises(ValueError):
            adapter.conditional_requests(self.lineage, corpus.build_candidate(root=1))
        lineage = copy.deepcopy(self.lineage)
        lineage["birth"]["panel_sha256"] = adapter.value_hash(fixed[:127])
        reseal(lineage["birth"])
        with self.assertRaises(ValueError):
            adapter.conditional_requests(lineage, self.candidate)

    def test_full480_fixed_denominators_invalid_text_and_actual_identities(self):
        result = self.reduced()
        self.assertEqual(result["model_calls"], 480)
        self.assertEqual(result["claim"], "SOURCE_AUTHORED_BIRTH_NOT_CLEAN")
        self.assertEqual(result["origin"], "UNRESOLVED_LOCAL_HASHES_ONLY")
        self.assertTrue(all(value is False for value in result["claims"].values()))
        self.assertIn("repeated/exposed", result["panel_exposure"])
        self.assertNotIn("P_minus_OFF", result["contrasts"])
        self.assertEqual(set(result["contrasts"]), {"P_WRITE_minus_BIRTH_ONLY", "A_WRITE_minus_BIRTH_ONLY", "P_WRITE_minus_A_WRITE"})
        for cell in adapter.CELLS:
            metrics = result["cells"][cell]
            self.assertEqual(metrics["actual_identity"]["adapter_input"], "/synthetic-cpu-only/" + cell)
            self.assertEqual(metrics["legacy_schedule_slot"], adapter.SCHEDULE_SLOTS[cell])
            self.assertEqual(metrics["rulegame"]["totals"]["quiz_items"], 24)
            self.assertEqual(metrics["rulegame"]["totals"]["allotted_record_opportunities"], 12)
            self.assertEqual(metrics["rulegame"]["totals"]["allotted_probe_opportunities"], 12)
            self.assertEqual(metrics["rulegame"]["totals"]["invalid_records"], 12)
            self.assertEqual(metrics["rulegame"]["totals"]["repeated_probe_triples"], 8)
            self.assertEqual(sum(row["total"] for row in metrics["conditional"]["operations"].values()), 128)
            self.assertEqual(len(metrics["conditional"]["rows"]), 128)
        self.assertEqual(sum(row["auth_strict_joint"] for row in result["cells"]["BIRTH_ONLY"]["conditional"]["operations"].values()), 0)
        self.assertEqual(sum(row["auth_strict_joint"] for row in result["cells"]["P_WRITE"]["conditional"]["operations"].values()), 128)

    def test_raw_replay_preserves_native_fields_and_no_parent_or_old_off(self):
        diagnostic, _, _, _ = adapter._helpers()
        for cell in adapter.CELLS:
            game = adapter.replay_rulegame(self.captures[cell]["rulegame"], self.lineage, cell)
            self.assertEqual(set(game["roles"]), {"wake", "record"})
            self.assertTrue(all(row["arm"] == cell for row in game["tasks"] + game["events"]))
            for sent, received in game["raw_pairs"]:
                self.assertEqual(sent["request"]["arm"], cell)
                self.assertEqual(received["response"]["prompt_token_ids"], [101, 0, 102])
                self.assertEqual(received["response"]["stop_reason"], 42)
                self.assertNotIn("Temporary parent restatement:", sent["request"]["prompt"])
            panel = adapter.replay_conditional(self.captures[cell]["conditional"], self.lineage, cell, self.candidate)
            self.assertEqual(len(panel["raw_pairs"]), 128)
            self.assertEqual(len(panel["raw_pairs"][0][1]["response"]["output_token_ids"]), 64)
            self.assertEqual(panel["raw_pairs"][0][0]["request"]["arm"], "readout")
            self.assertEqual(panel["header"]["cell"], cell)
        self.assertEqual(diagnostic.CELLS, ("OFF", "P_ON", "A_ON"))
        with self.assertRaises(ValueError):
            adapter.replay_rulegame(self.captures["BIRTH_ONLY"]["rulegame"], self.lineage, "OFF")

    def test_no_metrics_until_all_six_replays_and_exits(self):
        diagnostic, corpus, legacy, _ = adapter._helpers()
        trace = []
        originals = adapter.replay_rulegame, adapter.replay_conditional

        def observed(index, label):
            def invoke(*args, **kwargs):
                result = originals[index](*args, **kwargs)
                trace.append((label, args[2]))
                return result
            return invoke

        def check_barrier(function):
            def invoke(*args, **kwargs):
                self.assertEqual(len(trace), 6)
                return function(*args, **kwargs)
            return invoke

        with mock.patch.object(adapter, "replay_rulegame", side_effect=observed(0, "rulegame")), \
             mock.patch.object(adapter, "replay_conditional", side_effect=observed(1, "conditional")), \
             mock.patch.object(legacy, "process_metrics", side_effect=check_barrier(legacy.process_metrics)), \
             mock.patch.object(corpus, "score_outputs", side_effect=check_barrier(corpus.score_outputs)), \
             mock.patch.object(diagnostic, "usage", side_effect=check_barrier(diagnostic.usage)):
            self.reduced()
        self.assertEqual(trace[-1], ("conditional", "A_WRITE"))

    def test_incomplete_final_capture_or_worker_never_scores(self):
        _, corpus, legacy, _ = adapter._helpers()
        for kind in ("missing_panel", "failed_exit", "unclosed_backend", "reused_pid", "wrong_worker", "manifest_pin"):
            with self.subTest(kind=kind):
                captures, exits = copy.deepcopy(self.captures), copy.deepcopy(self.exits)
                if kind == "missing_panel":
                    captures["A_WRITE"]["conditional"] = str(self.root / "absent")
                elif kind == "failed_exit":
                    exits["A_WRITE"]["returncode"] = 1
                elif kind == "unclosed_backend":
                    exits["A_WRITE"]["backend_closed"] = False
                elif kind == "reused_pid":
                    exits["A_WRITE"]["pid"] = exits["P_WRITE"]["pid"]
                elif kind == "manifest_pin":
                    exits["A_WRITE"]["capture_manifest_sha256"]["conditional"] = adapter.value_hash("replacement manifest")
                else:
                    exits["A_WRITE"]["worker_id"] = "wrong-worker"
                with mock.patch.object(legacy, "process_metrics", side_effect=AssertionError("early metric")) as game_score, \
                     mock.patch.object(corpus, "score_outputs", side_effect=AssertionError("early metric")) as panel_score:
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        self.reduced(captures, exits)
                    game_score.assert_not_called()
                    panel_score.assert_not_called()

    def test_failed_capture_preserves_raw_partial_without_completion(self):
        out = self.root / "broken"
        completed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--fixture", str(out), "A_WRITE", "broken"],
                                   capture_output=True, text=True, timeout=60,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((out / "rulegame/manifest.json").exists())
        self.assertTrue((out / "conditional/calls/0127.response.json").exists())
        self.assertFalse((out / "conditional/closed.json").exists())
        self.assertFalse((out / "conditional/manifest.json").exists())
        with self.assertRaises(FileNotFoundError):
            adapter.replay_conditional(out / "conditional", self.lineage, "A_WRITE", self.candidate)

    def test_raw_corruption_rejected_even_after_manifest_rehash(self):
        diagnostic, _, _, _ = adapter._helpers()
        for panel, mutation in (("rulegame", "prompt"), ("rulegame", "arm"), ("rulegame", "tokens"),
                                ("rulegame", "identity"), ("rulegame", "events"), ("rulegame", "clock"),
                                ("conditional", "prompt"), ("conditional", "missing"), ("conditional", "extra"),
                                ("conditional", "tokens"), ("conditional", "clock"), ("conditional", "stop")):
            with self.subTest(panel=panel, mutation=mutation):
                target = self.root / (panel + "-" + mutation)
                shutil.copytree(self.captures["A_WRITE"][panel], target)
                if mutation == "events":
                    (target / "events.jsonl").write_text("")
                elif mutation == "missing":
                    (target / "calls/0127.response.json").unlink()
                elif mutation == "extra":
                    (target / "calls/extra.json").write_text("{}")
                else:
                    response = mutation in ("tokens", "clock", "stop")
                    path = target / ("calls/0000.response.json" if response else "calls/0000.request.json")
                    data = diagnostic.read(path)
                    if mutation == "prompt":
                        data["request"]["prompt"] += "\nparent formation note"
                        data["prompt_sha256"] = adapter.value_hash(data["request"]["prompt"])
                    elif mutation == "arm":
                        data["request"]["arm"] = "OFF"
                    elif mutation == "identity":
                        data["identity"]["adapter_input"] = None
                    elif mutation == "tokens":
                        data["response"]["output_token_ids"] = [True]
                        data["response_sha256"] = adapter.value_hash(data["response"])
                    elif mutation == "clock":
                        data["ended"] = -1
                    else:
                        del data["response"]["stop_reason"]
                        data["response_sha256"] = adapter.value_hash(data["response"])
                    path.write_text(json.dumps(data))
                (target / "manifest.json").unlink()
                diagnostic.capture_manifest(target)
                with self.assertRaises((ValueError, FileNotFoundError)):
                    if panel == "rulegame":
                        adapter.replay_rulegame(target, self.lineage, "A_WRITE")
                    else:
                        adapter.replay_conditional(target, self.lineage, "A_WRITE", self.candidate)

    def test_early_done_and_invalid_keep_prescribed_denominators(self):
        for mode in ("done", "invalid"):
            with self.subTest(mode=mode):
                captures, exits = self.make_run(self.root / mode, mode)
                result = self.reduced(captures, exits)
                self.assertEqual(result["model_calls"], 396)
                for cell in adapter.CELLS:
                    metrics = result["cells"][cell]["rulegame"]
                    self.assertEqual(metrics["totals"]["quiz_items"], 24)
                    self.assertEqual(metrics["totals"]["allotted_record_opportunities"], 12)
                    self.assertEqual(metrics["quiz_accuracy_fixed24"], 0)
                    self.assertEqual(metrics["invalid_or_absent_quiz_tasks"], 4)
                    self.assertEqual(metrics["totals"]["actual_records"], 0)
                    self.assertEqual(metrics["faithful_record_fraction_allotted12"], 0)
                    self.assertIsNone(metrics["faithful_record_fraction_actual"])
                    self.assertIsNone(metrics["prediction_accuracy"])
                    self.assertEqual(metrics["totals"]["protocol_invalid_actions"], 4 if mode == "invalid" else 0)


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--fixture":
        fixture_worker(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        unittest.main()
