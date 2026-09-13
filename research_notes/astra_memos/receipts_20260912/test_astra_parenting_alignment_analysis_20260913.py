"""Scripted CPU fixtures, never outcome directories or lifecycle APIs."""
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import astra_parenting_alignment_analysis_20260913 as analysis


SOURCE = "/tmp/astra_level1_real_record_source_20260913_attempt1"
PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md"


def sha(value):
    return hashlib.sha256(analysis.encoded(value).encode()).hexdigest()


def native_fixture(messages):
    segment = "<|im_start|>system\nCPU fixture<|im_end|>\n"
    text = segment+"".join("<|im_start|>user\n"+message["content"]+"<|im_end|>\n" for message in messages)+"<|im_start|>assistant\n"
    return dict(prompt_token_ids=[1], rendered_prompt=text, actual_system_text="CPU fixture", actual_system_segment=segment)


class Child:
    def __init__(self, core, *, invalid=False, splice=False, noncanonical=False, bad_restate=False):
        self.core, self.invalid, self.splice = core, invalid, splice
        self.noncanonical, self.bad_restate = noncanonical, bad_restate

    def __call__(self, request):
        prompt = request["input_messages"][0]["content"]
        if request["kind"] == "restate":
            lesson = prompt.split("Message:\n", 1)[1].split("\n\nRestate", 1)[0]
            raw = "I acknowledge." if self.bad_restate else lesson
            raw += "\nblock-sentinel-"+str(request["block_index"])
        else:
            public = json.loads(re.search(r"(?:Public task|Original public task):\n([^\n]+)", prompt).group(1))
            receipts = public["receipts"]
            chosen = max(receipts, key=lambda row: row["time"])
            if len(receipts) == 1:
                note = dict(predicted=chosen["predicted"], observed=chosen["observed"], relation=self.core.relation(chosen["predicted"], chosen["observed"]))
            else:
                note = dict(receipt_id=chosen["receipt_id"], **{"try": chosen["try"]}, observed=chosen["observed"])
            if request["kind"] == "wake":
                payload = dict(note=note, prediction=True, action=dict(kind="TRY", values=[True if self.invalid else 2, 5, 9]))
            else:
                receipt = json.loads(prompt.rsplit("\nFresh receipt:\n", 1)[1])
                event = dict(receipt_id=receipts[0]["receipt_id"] if self.splice else receipt["receipt_id"],
                    **{"try": receipt["try"]}, predicted=receipt["predicted"], observed=receipt["observed"],
                    relation=self.core.relation(receipt["predicted"], receipt["observed"]))
                payload = dict(address=public["address"], source=note, event=event)
            raw = " \n"+json.dumps(payload, indent=2)+"\n" if self.noncanonical else self.core.canonical(payload)
        return dict(request_id=request["request_id"], state=request["state"], raw=raw, finish_reason="stop")


def fixture(apis, seed=0, **options):
    core, deps = apis["core"], apis["deps"]
    original = core.root_binding(seed)
    producer = dict(learner_seed=seed, parent_plan_sha256=original["parent_plan_sha256"], adapter=original["adapter"],
        adapter_files={"adapter_model.safetensors": original["adapter_model_sha256"]})
    spec = dict(seed=seed, runner_sha256=analysis.RUNNER_PIN, core=dict(path="/tmp/astra_parenting_alignment_core_20260913.py", sha256=analysis.CORE_PIN),
        protocol=dict(path=PROTOCOL, sha256=analysis.PROTOCOL_PIN), prior_task_ids=dict(path="/tmp/fake-prior.json", sha256=sha([])))
    plan = dict(scope=analysis.SCOPE, seed=seed, specification=spec, self_sha256=analysis.RUNNER_PIN, root="/fixture/native/seed"+str(seed),
        arms=list(analysis.ARMS), states=[f"perception_seed{seed}_{arm}" for arm in analysis.ARMS], producers={str(seed): producer},
        model="fixture-no-read", model_files={}, environment={}, python="/fixture/python", python_sha256="1"*64, chat_template="fixture-template",
        engine=dict(max_model_len=16384), params=dict(temperature=0, seed=0, max_tokens=192), input_hashes={}, limits=dict(fits=0, updates=0))
    files = dict()
    files["spec.json"] = spec
    files["original_plan.json"] = {key: plan[key] for key in ("model", "model_files", "environment", "python", "python_sha256", "chat_template", "engine", "params")}
    files["manifest.json"] = core.build_manifest(deps, prior_ids=[])
    files["prior_task_ids.json"] = []
    prompts = {"lesson_"+name: core.RESTATE_TEMPLATE.format(lesson=text) for name, text in core.LESSONS.items()}
    prompts.update({task["task_id"]: task["ordinary_prompt"] for task in files["manifest.json"]["schedules"][str(seed)]})
    files["preflight.json"] = dict(lesson_literal_tokens=dict(P=10, C=11), lesson_multiset_tokens_per_lesson_arm=42,
        equal_lesson_multiset=True, individual_lesson_lengths_equal=False,
        static_prompts={name: native_fixture([dict(role="user", content=text)]) for name, text in prompts.items()})
    for name in files:
        plan["input_hashes"][name] = sha(files[name])
    plan["input_hashes"]["original_plan.json"] = original["parent_plan_sha256"]
    entry = dict(seed=seed, root="/fixture/local/seed"+str(seed), plan_sha256="a"*64, completion_sha256="b"*64,
        report=dict(path=f"/fixture/seed{seed}_collected/alignment_report.json", sha256="c"*64),
        collection=dict(path=f"/fixture/seed{seed}_collected/collection.json", sha256="d"*64), claim=dict(path="/fixture/claim.json", sha256="e"*64), holder_span=None)
    complete = dict(scope=analysis.SCOPE, plan_sha256="a"*64, stages={}, fits=0, updates=0, parent_model_calls=0, calls=0, collected=False, elapsed_seconds=1500.)
    files["prepare_started.json"] = dict(spec_sha256=sha(spec), entry_monotonic=1.)
    files["prepare_done.json"] = dict(plan_sha256="a"*64, elapsed_seconds=2.)
    files["controller_started.json"] = dict(plan_sha256="a"*64, seconds=3600, monotonic=10., deadline=3610.)
    captures, audits, costs = [], {}, {}
    for arm_index, arm in enumerate(analysis.ARMS):
        state = f"perception_seed{seed}_{arm}"
        route = dict(name="own_source_perception_seed"+str(seed), id=1, path=producer["adapter"])
        identity = dict(scope=analysis.SCOPE, state=state, seed=seed, arm=arm, producer=producer, route=route, core=spec["core"],
            model_files=plan["model_files"], engine=plan["engine"], params=plan["params"])
        capture = core.run_phase(state, Child(core, **options), deps, binding=identity)
        calls = [dict(request=event["request"], response=event["response"]) for event in capture["events"] if event["kind"] == "call"]
        stage = dict()
        stage["capture.json"], stage["identity.json"], stage["core_calls.json"] = capture, identity, calls
        start, end = 100.+arm_index*200, 200.+arm_index*200
        for index, call in enumerate(calls):
            request = call["request"]
            native = native_fixture(request["input_messages"])
            params = dict(plan["params"], max_tokens=core.MAX_OUTPUT_TOKENS[request["kind"]], temperature=0., seed=0)
            stage[f"{index:02d}.request.json"] = dict(call_id=f"{index:02d}", core_request=request, messages=request["input_messages"],
                native=native, params=params, lora_request=route)
            stage[f"{index:02d}.response.json"] = dict(native, actual_prompt_token_ids=[1], output_token_ids=[2],
                text=call["response"]["raw"], decoded_output=call["response"]["raw"], finish_reason="stop", stop_reason=None, lora_request=route,
                started=start+index, ended=start+index+.5)
        names = dict((name, sha(value)) for name, value in stage.items())
        cost = dict(calls=len(calls), fits=0, updates=0, parent_model_calls=0, kind_counts=dict(Counter(call["request"]["kind"] for call in calls)),
                    prompt_tokens=len(calls), output_tokens=len(calls), generation_seconds=.5*len(calls))
        stage["closed.json"] = dict(arm=arm, state=state, **cost, files=names, adapter_files_after=producer["adapter_files"], started_monotonic=start, ended_monotonic=end)
        process = dict(pid=1000+seed*10+arm_index, pgid=1000+seed*10+arm_index, start_ticks=100+arm_index)
        command = [plan["python"], "-B", "/tmp/astra_parenting_alignment_run_20260913.py", "worker", "--root", plan["root"], "--plan-sha256", "a"*64, "--arm", arm, "--allow-gpu"]
        stage["launch.json"] = dict(identity=process, arm=arm, plan_sha256="a"*64, command=command, time=start-2, monotonic=start-2)
        stage["started.json"] = dict(arm=arm, plan_sha256="a"*64, pid=process["pid"], pgid=process["pid"], time=start-1, monotonic=start-1)
        stage["worker_done.json"] = dict(arm=arm, plan_sha256="a"*64, monotonic=end+1)
        stage["exit.json"] = dict(identity=process, returncode=0, monotonic=end+2)
        stage["released.json"] = dict(identity=process, arm=arm, group_absent=True, gpu_vacant=True, time=end+3, monotonic=end+3)
        complete["stages"][arm] = {name: sha(value) for name, value in stage.items()}
        files.update({"run/"+arm+"/"+name: value for name, value in stage.items()})
        captures.append(capture)
        audits[arm] = core.replay_validate(capture, deps)
        costs[arm] = cost
    total = {key: sum(cost[key] for cost in costs.values()) for key in ("calls", "fits", "updates", "parent_model_calls", "prompt_tokens", "output_tokens", "generation_seconds")}
    complete["calls"] = total["calls"]
    summary = core.summarize(captures, deps)
    report = dict(scope=analysis.SCOPE, seed=seed, plan_sha256="a"*64, completion_sha256="b"*64, source_bindings=spec, original_parent=producer,
        manifest_sha256=plan["input_hashes"]["manifest.json"], captures=captures, replay_audits=audits, costs_per_arm=costs, summary=summary, costs=total,
        controller_seconds=1500., preflight=files["preflight.json"], native_capture_custody_checked=True, automatic_pass=False, fit_authorized=False)
    return dict(entry=entry, plan=plan, report=report, complete=complete, files=files, holder_span=None,
        collection=dict(alignment_report_sha256="c"*64, completion_sha256="b"*64, collection_seconds=1.),
        claim=dict(plan_sha256="a"*64, out=f"/fixture/seed{seed}_collected", retry=False))


def materialize(bundle, home):
    bundle = copy.deepcopy(bundle)
    seed = bundle["entry"]["seed"]
    root = home / f"seed{seed}"
    collected = home / f"seed{seed}_collected"
    root.mkdir()
    collected.mkdir()
    plan, files, entry = bundle["plan"], bundle["files"], bundle["entry"]
    plan_hash = sha(plan)
    entry.update(root=str(root), plan_sha256=plan_hash)
    bundle["complete"]["plan_sha256"] = bundle["report"]["plan_sha256"] = bundle["claim"]["plan_sha256"] = plan_hash
    for name in ("prepare_done.json", "controller_started.json"):
        files[name]["plan_sha256"] = plan_hash
    for arm in analysis.ARMS:
        prefix = "run/"+arm+"/"
        for name in ("launch.json", "started.json", "worker_done.json"):
            files[prefix+name]["plan_sha256"] = plan_hash
        command = files[prefix+"launch.json"]["command"]
        command[command.index("--plan-sha256")+1] = plan_hash
        closed = files[prefix+"closed.json"]
        closed["files"] = {name: sha(files[prefix+name]) for name in closed["files"]}
        bundle["complete"]["stages"][arm] = {name[len(prefix):]: sha(value) for name, value in files.items() if name.startswith(prefix)}
        for name in ("stdout.log", "stderr.log"):
            bundle["complete"]["stages"][arm][name] = hashlib.sha256(b"fixture log").hexdigest()
    for name, value in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(analysis.encoded(value))
    for arm in analysis.ARMS:
        for name in ("stdout.log", "stderr.log"):
            (root/"run"/arm/name).write_bytes(b"fixture log")
    (root/"plan.json").write_text(analysis.encoded(plan))
    (root/"capture_complete.json").write_text(analysis.encoded(bundle["complete"]))
    complete_hash = sha(bundle["complete"])
    entry["completion_sha256"] = bundle["report"]["completion_sha256"] = bundle["collection"]["completion_sha256"] = complete_hash
    (collected/"alignment_report.json").write_text(analysis.encoded(bundle["report"]))
    bundle["collection"]["alignment_report_sha256"] = sha(bundle["report"])
    (collected/"collection.json").write_text(analysis.encoded(bundle["collection"]))
    claim_path = home/f"seed{seed}.collection_claim.json"
    claim_path.write_text(analysis.encoded(bundle["claim"]))
    for key, path in (("report", collected/"alignment_report.json"), ("collection", collected/"collection.json"), ("claim", claim_path)):
        entry[key] = dict(path=str(path), sha256=analysis.digest(path))
    return entry


class AlignmentReducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apis = analysis.load_sources("/tmp", SOURCE, PROTOCOL)
        cls.bundles = [fixture(cls.apis, seed) for seed in range(3)]

    def test_full_cohort_counts_and_no_automatic_gate(self):
        result = analysis.reduce_cohort(self.bundles, self.apis)
        self.assertEqual(result["total_costs"]["calls"], 312)
        self.assertEqual(result["total_costs"]["fits"], 0)
        self.assertFalse(result["feasibility"]["feasibility_pass"])
        self.assertFalse(result["fit_authorized"])
        for seed in result["seeds"]:
            for arm in analysis.ARMS:
                self.assertEqual(seed["arms"][arm]["counts"]["FULL_MATERIAL"], 16)
            self.assertEqual(seed["paired"]["SWAPPED"]["PROCESS_USE"]["counts"]["both"], 16)

    def test_invalid_actions_keep_all_denominators(self):
        result = analysis.reduce_seed(fixture(self.apis, invalid=True), self.apis)
        self.assertEqual(result["costs"]["calls"], 56)
        for arm in result["arms"].values():
            self.assertEqual(arm["counts"]["opportunities"], 16)
            self.assertEqual(arm["counts"]["record_not_called"], 16)
            self.assertEqual(arm["counts"]["EXECUTED"], 0)

    def test_noncanonical_and_bad_restate_separate_from_full_material(self):
        result = analysis.reduce_seed(fixture(self.apis, noncanonical=True, bad_restate=True), self.apis)
        aligned = result["arms"]["ALIGNED"]
        self.assertEqual(aligned["counts"]["RESTATE"], 0)
        self.assertEqual(aligned["counts"]["FULL_MATERIAL"], 16)
        self.assertEqual(aligned["details"]["formats"]["record"]["valid_noncanonical"], 16)

    def test_actual_child_receipt_splice_is_outcome_not_abort(self):
        result = analysis.reduce_seed(fixture(self.apis, splice=True), self.apis)
        for arm in result["arms"].values():
            self.assertEqual(arm["counts"]["EXECUTED"], 16)
            self.assertEqual(arm["counts"]["RECORD_FAITHFUL"], 0)

    def test_record_or_public_world_receipt_tampering_rejected(self):
        for kind in ("record", "public"):
            bundle = copy.deepcopy(self.bundles[0])
            capture = bundle["files"]["run/ALIGNED/capture.json"]
            if kind == "record":
                capture["records"][0]["execution"]["receipt"]["receipt_id"] = "other-receipt"
            else:
                event = next(item for item in capture["events"] if item["kind"] == "harness_public_receipts")
                event["receipts"][0]["observed"] = not event["receipts"][0]["observed"]
            capture["capture_sha256"] = self.apis["core"].digest({key: value for key, value in capture.items() if key != "capture_sha256"})
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_task_context_leak_is_rejected_even_after_resigning(self):
        for extra in ("another block note", self.apis["core"].LESSONS["C"], "scorer says correct"):
            bundle = copy.deepcopy(self.bundles[0])
            capture = bundle["files"]["run/ALIGNED/capture.json"]
            wake = next(event for event in capture["events"] if event["kind"] == "call" and event["request"]["kind"] == "wake")
            wake["request"]["input_messages"][0]["content"] += extra
            capture["capture_sha256"] = self.apis["core"].digest({key: value for key, value in capture.items() if key != "capture_sha256"})
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_native_call_route_prefix_and_score_mismatch(self):
        for mode in ("route", "prefix", "score", "rendered_leak"):
            bundle = copy.deepcopy(self.bundles[0])
            if mode == "route":
                bundle["files"]["run/ALIGNED/00.response.json"]["lora_request"] = {}
            elif mode == "prefix":
                bundle["files"]["run/ALIGNED/00.response.json"]["actual_prompt_token_ids"] = [42]
            elif mode == "rendered_leak":
                bundle["files"]["run/ALIGNED/00.request.json"]["native"]["rendered_prompt"] += "hidden extra lesson"
                bundle["files"]["run/ALIGNED/00.response.json"]["rendered_prompt"] += "hidden extra lesson"
            else:
                bundle["report"]["summary"]["cells"]["perception_seed0_ALIGNED"]["PROCESS_USE"] = 15
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_zero_partial_and_duplicate_attempts_not_assessable(self):
        for bundles in ([], self.bundles[:2], [self.bundles[0]]*3):
            with self.assertRaises(ValueError):
                analysis.reduce_cohort(bundles, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        del bundle["complete"]["stages"]["NO_PARENT"]
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_denominator_bool_callcost_and_missing_contact(self):
        for mode in ("denominator", "bool", "cost", "contact"):
            bundle = copy.deepcopy(self.bundles[0])
            if mode == "denominator":
                bundle["files"]["run/ALIGNED/capture.json"]["records"].pop()
            elif mode == "bool":
                bundle["complete"]["fits"] = False
            elif mode == "cost":
                bundle["report"]["costs"]["calls"] += 1
            else:
                bundle["files"]["run/ALIGNED/capture.json"]["contacts"].pop()
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_custody_nonzero_exit_reused_process_and_missing_release(self):
        for mode in ("exit", "process", "release"):
            bundle = copy.deepcopy(self.bundles[0])
            if mode == "exit":
                bundle["files"]["run/ALIGNED/exit.json"]["returncode"] = 1
            elif mode == "process":
                bundle["files"]["run/ALIGNED/exit.json"]["identity"] = copy.deepcopy(bundle["files"]["run/ALIGNED/exit.json"]["identity"])
                bundle["files"]["run/ALIGNED/exit.json"]["identity"]["start_ticks"] += 1
            else:
                bundle["files"]["run/ALIGNED/released.json"]["gpu_vacant"] = False
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_exact_feasibility_boundaries(self):
        cells = {capture["state"]: copy.deepcopy(capture["readout"]) for bundle in self.bundles for capture in bundle["report"]["captures"]}
        for seed in range(3):
            aligned = cells[f"perception_seed{seed}_ALIGNED"]
            aligned["RESTATE"] = 3
            aligned["PROCESS_USE"] = 8
            aligned["FULL_MATERIAL"] = 8
            aligned["by_delivery"]["0"]["PROCESS_USE"] = 4
            aligned["by_delivery"]["1"]["PROCESS_USE"] = 4
            cells[f"perception_seed{seed}_SWAPPED"]["PROCESS_USE"] = 4
            cells[f"perception_seed{seed}_NO_PARENT"]["PROCESS_USE"] = 6
        cells["perception_seed2_NO_PARENT"]["PROCESS_USE"] = 10
        result = analysis.feasibility(cells)
        self.assertTrue(result["feasibility_pass"])
        self.assertEqual(result, self.apis["core"].threshold_vector(cells))
        cells["perception_seed2_NO_PARENT"]["PROCESS_USE"] = 11
        self.assertFalse(analysis.feasibility(cells)["vector"]["anchor_no_large_harm"])
        cells["perception_seed2_SWAPPED"]["PROCESS_USE"] = 12
        self.assertFalse(analysis.feasibility(cells)["vector"]["swapped_no_large_harm"])

    def test_json_nonfinite_duplicates_pin_and_fresh_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"input.json"
            for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    analysis.read(path)
            path.write_text(json.dumps(dict(schema=analysis.INPUT_SCHEMA, seeds=[])))
            with self.assertRaises(ValueError):
                analysis.pinned(path, "0"*64)
            with self.assertRaisesRegex(ValueError, "fresh write-once"):
                analysis.run(path, analysis.digest(path), temporary, "/tmp", SOURCE, PROTOCOL)

    def test_full_file_loader_and_write_once_outputs_with_mock_parent_pins(self):
        original_hash = sha(self.bundles[0]["files"]["original_plan.json"])
        with tempfile.TemporaryDirectory() as temporary, patch.object(self.apis["core"], "ROOT_PLAN_PINS", (original_hash,)*3):
            home = Path(temporary)
            entries = [materialize(fixture(self.apis, seed), home) for seed in range(3)]
            manifest = home/"manifest.json"
            manifest.write_text(analysis.encoded(dict(schema=analysis.INPUT_SCHEMA, seeds=entries)))
            with patch.object(analysis, "load_sources", return_value=self.apis):
                result = analysis.run(manifest, analysis.digest(manifest), home/"reduced", "/tmp", SOURCE, PROTOCOL)
            self.assertEqual(set(result), {"analysis.json", "analysis.md"})
            report = analysis.read(home/"reduced/analysis.json")
            self.assertEqual(report["total_costs"]["calls"], 312)
            self.assertFalse(report["fit_authorized"])
            with self.assertRaisesRegex(ValueError, "fresh write-once"):
                analysis.run(manifest, analysis.digest(manifest), home/"reduced", "/tmp", SOURCE, PROTOCOL)
            (Path(entries[0]["root"])/"run/ALIGNED/00.response.json").write_text('{}')
            with self.assertRaisesRegex(ValueError, "pin differs"):
                analysis.load_bundle(entries[0])


if __name__ == "__main__":
    unittest.main()
