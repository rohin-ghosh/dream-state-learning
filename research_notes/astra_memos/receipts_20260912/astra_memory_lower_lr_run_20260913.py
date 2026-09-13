"""Candidate-only LR3e-5 memory repair; historical controls are not rerun."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = "astra_memory_lower_lr_candidate_20260913_v1"
RUNTIME_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
DESIGN_PIN = "98df5e78c53921e7dae5c0210800c4ae4f1a068da69b50a1d3bebd1986c4b60c"
PROTOCOL_PIN = "122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce"
STAGES = ("WRITE_fit", "WRITE_readout")
INPUTS = ("dataset.json", "capture.json", "retention.json", "training.json", "calls.json")
PANELS = ("exact", "paraphrase", "held", "canary")
LR = 3e-5
SECONDS, COLLECT_SECONDS, PREPARE_SECONDS = 3600, 180, 180
HISTORY_PINS = (
    ("66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1",
     "08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972",
     "fbbc8ddf580e2141c01a3b73477605e7e5a77bc8e638126475950ea1f105dfab",
     "b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf"),
    ("9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b",
     "56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92",
     "f0ac6662ccb6b6cb9477503fa7214578a1dade4e376e8b1e6c4395e2ae5c6268",
     "5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979"),
    ("48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea",
     "e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f",
     "f0333bdd6854a27fc1a8825db852ec5976c3b50db667d9b762e2e489634d882a",
     "a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef"),
)
CLAIM = ("Exploratory candidate-only LR3e-5 acquisition, paraphrase access and authored retention repair. "
         "Historical HIGH1e-4 and LR0 endpoints are reused, noncontemporaneous, zero incremental cost; "
         "not new control replications. No new formation, teacher rewriting, dose ladder, outcome-dependent execution gate, "
         "fresh heldout confirmation, closed-loop or H1/H2 promotion.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def pinned(record, expected=None):
    require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute(), "explicit file binding required")
    require(len(record["sha256"]) == 64 and (expected is None or record["sha256"] == expected) and
            digest(record["path"]) == record["sha256"], "file/source pin differs")


def runtime(record=None):
    sys.dont_write_bytecode = True
    record = record or dict(path="/tmp/astra_real_record_memory_run_20260913.py", sha256=RUNTIME_PIN)
    pinned(record, RUNTIME_PIN)
    specification = importlib.util.spec_from_file_location("lower_lr_frozen_memory", record["path"])
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_spec(spec):
    require(set(spec) == {"runner_sha256", "runtime", "design", "protocol", "history", "seed", "fit_seed",
                          "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed specification differs")
    require(spec["runner_sha256"] == digest(SELF), "candidate runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2) and
            type(spec["fit_seed"]) is int and spec["fit_seed"] == spec["seed"], "original learner fit seed required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and
            type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "GPU identity required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "boot/lease binding required")
    pinned(spec["runtime"], RUNTIME_PIN)
    pinned(spec["design"], DESIGN_PIN)
    pinned(spec["protocol"], PROTOCOL_PIN)
    history = spec["history"]
    require(set(history) == {"root", "plan_sha256", "completion_sha256", "collection", "scores_sha256"} and
            Path(history["root"]).is_absolute(), "closed original history binding required")
    require((history["plan_sha256"], history["completion_sha256"], history["collection"]["sha256"],
             history["scores_sha256"]) == HISTORY_PINS[spec["seed"]], "original seed/history pins differ")


def validate_cells(cells, calls):
    require(set(cells) == set(PANELS), "score panel inventory differs")
    require(len({call["call_id"] for call in calls}) == len(calls), "duplicate call ID")
    require(all(call["panel"] in PANELS for call in calls), "unknown call panel")
    for panel in PANELS:
        expected = [call["row_id"] for call in calls if call["panel"] == panel]
        actual = [row["row_id"] for row in cells[panel]]
        require(len(set(expected)) == len(expected) and len(set(actual)) == len(actual) and
                set(expected) == set(actual), "duplicate/missing/foreign source row")


def bind_history(memory, spec, native=False):
    validate_spec(spec)
    history = spec["history"]
    root = Path(history["root"])
    original, bound = memory.verify(root, history["plan_sha256"], native=native)
    require(original["specification"]["seed"] == original["specification"]["fit_seed"] == spec["seed"], "historical seed differs")
    require(digest(root / "capture_complete.json") == history["completion_sha256"], "original completion pin differs")
    complete = memory.read(root / "capture_complete.json")
    require(complete["plan_sha256"] == history["plan_sha256"] and complete["scored"] is False and
            type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= memory.OUTER_SECONDS and
            complete["stages"] == memory.validate_completed(original, history["plan_sha256"], bound) and
            complete["calls"] == 2 * original["calls_per_arm"] and complete["updates"] == 2 * original["updates_per_arm"],
            "original completion custody differs")
    pinned(history["collection"])
    collection_path = Path(history["collection"]["path"])
    require(collection_path.name == "collection.json" and not (collection_path.parent / "collection_failure.json").exists(),
            "successful original collection required")
    require(memory.read(collection_path) == dict(scores_sha256=history["scores_sha256"], completion_sha256=history["completion_sha256"]),
            "original collection binding differs")
    require(memory.read(root.with_name(root.name + ".collection_claim.json")) ==
            dict(plan_sha256=history["plan_sha256"], out=str(collection_path.parent), retry=False), "original once-collection claim differs")
    require(digest(collection_path.parent / "scores.json") == history["scores_sha256"], "original score pin differs")
    scores = memory.read(collection_path.parent / "scores.json")
    require(scores["plan_sha256"] == history["plan_sha256"] and scores["completion_sha256"] == history["completion_sha256"] and
            scores["seed"] == spec["seed"] and scores["parent"] == original["parent"] == bound["parent"] and
            scores["native_capture_custody_checked"] is True and set(scores["cells"]) == {"WRITE", "LR0"}, "historical scores identity differs")
    calls = memory.read(root / "calls.json")
    for arm in ("WRITE", "LR0"):
        validate_cells(scores["cells"][arm], calls)
        manifest = memory.read(root / "run" / (arm + "_fit") / "adapter/train_manifest.json")
        require(scores["fits"][arm] == manifest, "stored fit differs from original receipt")
        for call in calls:
            row = next(row for row in scores["cells"][arm][call["panel"]] if row["row_id"] == call["row_id"])
            path = root / "run" / (arm + "_readout") / (call["call_id"] + ".response.json")
            response = memory.read(path)
            require(row["response_sha256"] == digest(path) and row["raw"] == response["text"] and
                    row["finish_reason"] == response["finish_reason"], "historical raw source join differs")
    return original, bound, scores


def candidate_config(original):
    require(original["configs"]["WRITE"]["lr"] == 1e-4 and original["configs"]["LR0"]["lr"] == 0.0,
            "original paired learning rates differ")
    config = copy.deepcopy(original["configs"]["WRITE"])
    config["lr"] = LR
    return config


def snapshot_paths(spec, original):
    root = Path(original["root"])
    collection = Path(spec["history"]["collection"]["path"])
    return {**{name: root / name for name in INPUTS}, "history/plan.json": root / "plan.json",
            "history/completion.json": root / "capture_complete.json", "history/collection.json": collection,
            "history/scores.json": collection.parent / "scores.json"}


def make_plan(root, spec, spec_sha256, original):
    seed = spec["seed"]
    count = (14, 8, 8)[seed]
    require(original["updates_per_arm"] == 8 * count and original["calls_per_arm"] == 2 * count + 60 and
            set(original["input_hashes"]) == set(INPUTS), "original fixed workload differs")
    keys = ("model", "model_files", "chat_template", "environment", "source", "parent", "engine", "params", "status")
    plan = {key: copy.deepcopy(original[key]) for key in keys}
    plan.update(scope=SCOPE, claim=CLAIM, root=str(Path(root).absolute()), specification=spec, spec_sha256=spec_sha256,
                self_sha256=digest(SELF), python=original["python"], python_sha256=original["python_sha256"],
                source_hashes=dict(candidate=digest(SELF), runtime=RUNTIME_PIN, design=DESIGN_PIN,
                                   protocol=spec["protocol"]["sha256"]), configs={"WRITE": candidate_config(original)},
                stages=list(STAGES), input_hashes=copy.deepcopy(original["input_hashes"]),
                snapshot_hashes={name: digest(path) for name, path in snapshot_paths(spec, original).items()},
                gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"], calls_per_arm=2 * count + 60, updates_per_arm=8 * count,
                limits=dict(controller=SECONDS, collection=COLLECT_SECONDS, updates=8 * count, calls=2 * count + 60),
                delta=dict(lr_before=1e-4, lr_after=LR, other_training_changes=[]),
                reused_endpoints=dict(HIGH=dict(original_arm="WRITE", noncontemporaneous=True, incremental_calls=0, incremental_updates=0),
                                      LR0=dict(original_arm="LR0", noncontemporaneous=True, incremental_calls=0, incremental_updates=0)))
    return plan


def protected(memory, spec, original, bound):
    return [SELF, spec["runtime"]["path"], spec["design"]["path"], spec["protocol"]["path"], original["root"],
            Path(spec["history"]["collection"]["path"]).parent, *memory.protected_inputs(original["specification"], bound)]


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "explicit native CPU prepare with empty CVD required")
    memory = runtime()
    memory.offline()
    with memory.budget(PREPARE_SECONDS):
        require(digest(spec_path) == spec_sha256, "specification pin differs")
        spec = memory.read(spec_path)
        memory = runtime(spec["runtime"])
        original, bound, _ = bind_history(memory, spec, native=True)
        root = memory.new_external(root, [spec_path, *protected(memory, spec, original, bound)])
        memory.check_allocation(dict(specification=spec))
        root.mkdir()
        memory.write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
        try:
            plan = make_plan(root, spec, spec_sha256, original)
            tokenizer = bound["probe"].native_tokenizer(plan["model"])
            require(tokenizer.chat_template == plan["chat_template"], "original tokenizer template differs")
            training = memory.encode_training(bound["dataset"]["rows"], tokenizer, bound["trainer"], bound["helper"], bound["probe"], spec["fit_seed"])
            calls = memory.build_calls(bound["dataset"], bound["retention"], bound["original_calls"], tokenizer, bound["probe"])
            require(training == memory.read(Path(original["root"]) / "training.json") and
                    calls == memory.read(Path(original["root"]) / "calls.json"), "original prompt/target/token/mask/order replay differs")
            bound["trainer"]._warm_parent(plan["parent"]["adapter"], root / "run/WRITE_fit/adapter",
                                           bound["trainer"].TrainConfig(**plan["configs"]["WRITE"]))
            (root / "history").mkdir()
            for name, source in {**snapshot_paths(spec, original), "spec.json": Path(spec_path)}.items():
                with (root / name).open("xb") as output:
                    output.write(source.read_bytes())
                require(digest(root / name) == (spec_sha256 if name == "spec.json" else plan["snapshot_hashes"][name]), "copy changed bytes")
            memory.write(root / "plan.json", plan)
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"), seed=spec["seed"],
                        stages=list(STAGES), updates=plan["updates_per_arm"], calls=plan["calls_per_arm"])
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    root = Path(root).absolute()
    memory = runtime()
    require(digest(root / "plan.json") == plan_sha256, "candidate plan pin differs")
    plan = memory.read(root / "plan.json")
    spec = plan["specification"]
    memory = runtime(spec["runtime"])
    original, bound, scores = bind_history(memory, spec, native=native)
    require(plan == make_plan(root, spec, plan["spec_sha256"], original), "independent candidate plan validation differs")
    require(plan["python"] == os.path.abspath(sys.executable) and plan["python_sha256"] == digest(sys.executable), "native Python identity differs")
    require(not (root / "prepare_failure.json").exists() and
            memory.read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            digest(root / "spec.json") == plan["spec_sha256"] and memory.read(root / "spec.json") == spec, "spec/preparation changed")
    for name, checksum in plan["snapshot_hashes"].items():
        require(digest(root / name) == checksum, "copied immutable input differs: " + name)
    return memory, plan, bound, scores


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES, "candidate WRITE worker only")
    memory = runtime()
    memory.offline()
    directory = Path(root) / "run" / stage
    try:
        memory, plan, bound, _ = verify(root, plan_sha256, native=True)
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(), "worker allocation/isolation differs")
        memory.check_allocation(plan)
        memory.write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, plan_sha256=plan_sha256))
        if stage == "WRITE_fit":
            memory.fit_arm(plan, bound, "WRITE")
        else:
            memory.capture_readout(plan, bound, "WRITE")
    except BaseException as error:
        memory.failure(directory / "failure.json", error)
        raise


def run_stage(memory, plan, plan_sha256, stage, deadline, bound):
    require(stage in STAGES, "no new LR0 stage")
    probe = bound["probe"]
    memory.check_allocation(plan)
    require(deadline - time.monotonic() > memory.GPU_QUERY_SECONDS + memory.CLEANUP_SECONDS and probe.gpu_state(plan) is True,
            "fresh assigned GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    process, expected = None, None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                       "--stage", stage, "--allow-gpu"]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            expected = memory.identity(process.pid)
            require(expected["pgid"] == process.pid, "worker process group differs")
            memory.write(directory / "launch.json", dict(identity=expected, stage=stage, plan_sha256=plan_sha256, command=command))
            require(process.wait(timeout=max(.01, deadline - time.monotonic() - memory.CLEANUP_SECONDS)) == 0, "candidate worker failed")
    except BaseException as error:
        memory.failure(directory / "stage_failure.json", error)
        raise
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity")
                memory.cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True, "all-process GPU release failed")
                memory.write(directory / "released.json", dict(identity=expected, stage=stage))
            except BaseException as error:
                memory.failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(memory, plan, plan_sha256, bound, scores):
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists(), "failed candidate controller")
    require({path.name for path in (root / "run").iterdir()} == set(STAGES), "candidate-only stage inventory differs")
    prepared, calls = memory.read(root / "training.json"), memory.read(root / "calls.json")
    inventory, pids = {}, []
    for stage in STAGES:
        directory = root / "run" / stage
        require(not any((directory / name).exists() for name in ("failure.json", "stage_failure.json", "cleanup_failure.json")), "failed candidate stage")
        launch, started, released = (memory.read(directory / name) for name in ("launch.json", "started.json", "released.json"))
        identity = launch["identity"]
        expected_command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                            "--stage", stage, "--allow-gpu"]
        require(identity == released["identity"] and identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and
                type(identity["start_ticks"]) is int and identity["start_ticks"] > 0 and launch["command"] == expected_command and
                launch["stage"] == started["stage"] == released["stage"] == stage and
                launch["plan_sha256"] == started["plan_sha256"] == plan_sha256, "candidate process custody differs")
        pids.append(identity["pid"])
        route = memory.route_for(plan, bound, "WRITE")
        if stage == "WRITE_fit":
            fit = memory.read(directory / "fit.json")
            manifest = memory.read(directory / "adapter/train_manifest.json")
            require(fit["updates"] == prepared["updates"] == plan["updates_per_arm"] and fit["calls"] == 0 and
                    fit["training_sha256"] == manifest["corpus"]["sha256"] == plan["input_hashes"]["training.json"], "candidate fit receipt differs")
            memory.check_fit(manifest, prepared, plan["configs"]["WRITE"], plan["parent"], "WRITE")
            bound["helper"].check_adapter(directory / "adapter", plan["configs"]["WRITE"])
            for arm in ("WRITE", "LR0"):
                require(all(manifest["warm_start"][key] == scores["fits"][arm]["warm_start"][key]
                            for key in ("initialized_state", "source_state")), "candidate/historical warm tensors differ")
        else:
            require(memory.read(directory / "identity.json") == dict(arm="WRITE", route=route, model_files=plan["model_files"],
                    parent=plan["parent"], params=plan["params"]), "candidate readout route differs")
            require(memory.read(directory / "readout.json") == dict(arm="WRITE", calls=len(calls), updates=0), "candidate call count differs")
            for suffix in (".request.json", ".response.json"):
                require({path.name for path in directory.glob("*" + suffix)} == {call["call_id"] + suffix for call in calls}, "candidate call inventory differs")
            for call in calls:
                request = memory.read(directory / (call["call_id"] + ".request.json"))
                response = memory.read(directory / (call["call_id"] + ".response.json"))
                require(request == dict(call, params=plan["params"], lora_request=route), "candidate prompt changed")
                bound["formation"].validate_response(request, response, route)
        inventory[stage] = bound["formation"].tree(directory)
    require(len(set(pids)) == 2 and len(calls) == plan["calls_per_arm"] and
            plan["calls_per_arm"] <= 88 and plan["updates_per_arm"] <= 112, "cold process/work cap differs")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only controller with empty CVD required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    try:
        with memory.budget(SECONDS):
            deadline = time.monotonic() + SECONDS
            memory, plan, bound, scores = verify(root, plan_sha256, native=True)
            memory.check_allocation(plan)
            memory.write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), started=time.time(), seconds=SECONDS))
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(memory, plan, plan_sha256, stage, deadline, bound)
            inventory = validate_completed(memory, plan, plan_sha256, bound, scores)
            require(time.monotonic() < deadline, "candidate controller total cap exceeded")
            memory.write(root / "capture_complete.json", dict(scope=SCOPE, plan_sha256=plan_sha256, stages=inventory,
                calls=plan["calls_per_arm"], updates=plan["updates_per_arm"], scored=False, automatic_pass=False,
                elapsed_seconds=SECONDS - (deadline - time.monotonic())))
            return dict(status="CANDIDATE_CAPTURE_COMPLETE_NOT_SCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def repair_screen(seed, summary):
    exact = summary["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"]
    regressions = {panel: summary["paired_WRITE_LR0"][panel]["passed"]["second_only"] for panel in ("held", "canary")}
    threshold = (8, 7, 5)[seed]
    return dict(exact_source_faithful=exact, required_exact_source_faithful=threshold,
                lost_LR0_correct_items=regressions, met=exact >= threshold and not any(regressions.values()),
                interpretation="Strict exploratory screen only. Partial tradeoff is not full repair; no automatic promotion or rerun.")


def comparison(memory, plan, bound, historical, candidate):
    calls = memory.read(Path(plan["root"]) / "calls.json")
    for cells in (candidate, historical["cells"]["WRITE"], historical["cells"]["LR0"]):
        validate_cells(cells, calls)
    comparisons = dict(candidate_vs_historical_LR0=memory.summarize({"WRITE": candidate, "LR0": historical["cells"]["LR0"]}, bound),
                       candidate_vs_historical_HIGH=memory.summarize({"WRITE": candidate, "LR0": historical["cells"]["WRITE"]}, bound))
    return dict(scope=SCOPE, claim=CLAIM, seed=plan["specification"]["seed"], parent=plan["parent"],
        cells={"WRITE": candidate}, historical_cells={"HIGH": historical["cells"]["WRITE"], "LR0": historical["cells"]["LR0"]},
        reused_endpoints=plan["reused_endpoints"], historical_binding=plan["specification"]["history"],
        comparisons=comparisons, strict_exploratory_repair_screen=repair_screen(plan["specification"]["seed"], comparisons["candidate_vs_historical_LR0"]),
        comparison_labels="Frozen reducer slot WRITE=candidate; slot LR0=the named historical endpoint (HIGH or LR0), not a new stage. "
                          "Reducer generation_costs are stored observation costs, NOT incremental costs.",
        incremental_cost=dict(calls=plan["calls_per_arm"], updates=plan["updates_per_arm"], historical_calls=0, historical_updates=0),
        memory_possible_denominator_per_variant=16, memory_scored_denominator=(14, 8, 8)[plan["specification"]["seed"]],
        retention_denominators=dict(held=48, canary=12), automatic_pass=False, scientific_pass=None,
        interpretation="Screen is descriptive, not an execution/retry gate. Original held panel is exploratory repair data, not fresh confirmation; no test/claim promotion.")


def collect(root, plan_sha256, completion_sha256, out):
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(COLLECT_SECONDS):
        memory, plan, bound, historical = verify(root, plan_sha256)
        require(digest(root / "capture_complete.json") == completion_sha256, "candidate completion pin differs")
        complete = memory.read(root / "capture_complete.json")
        require(complete["scope"] == SCOPE and complete["plan_sha256"] == plan_sha256 and complete["scored"] is False and
                complete["calls"] == plan["calls_per_arm"] and complete["updates"] == plan["updates_per_arm"] and
                type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= SECONDS and
                complete["stages"] == validate_completed(memory, plan, plan_sha256, bound, historical), "candidate completion differs")
        original = memory.read(root / "history/plan.json")
        out = memory.new_external(out, [root, *protected(memory, plan["specification"], original, bound)])
        memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            candidate = memory.score_calls(plan, bound, "WRITE")
            report = comparison(memory, plan, bound, historical, candidate)
            report.update(plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          native_capture_custody_checked=True, fits={"WRITE": memory.read(root / "run/WRITE_fit/adapter/train_manifest.json")},
                          parameter_diagnostics={"WRITE": memory.read(root / "run/WRITE_fit/fit.json")["norms"]},
                          training_costs={key: value for key, value in memory.read(root / "training.json").items()
                                          if key not in ("items", "encoding", "epoch_order")})
            memory.write(out / "scores.json", report)
            memory.write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_EXPLORATORY_CANDIDATE", out=str(out), scores_sha256=digest(out / "scores.json"))
        except BaseException as error:
            memory.failure(out / "collection_failure.json", error)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name != "collect":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--stage", choices=STAGES, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    options = vars(parser.parse_args(argv))
    name = options.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
