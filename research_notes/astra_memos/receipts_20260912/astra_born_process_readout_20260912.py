"""Injected-backend born-child capture/replay; no loader, launcher, fit or verdict."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time


SCHEMA = "born-child-readout-lineage-v1"
CAPTURE_SCHEMA = "born-child-readout-capture-v1"
CELLS = ("BIRTH_ONLY", "P_WRITE", "A_WRITE")
SCHEDULE_SLOTS = dict(zip(CELLS, ("OFF", "P_ON", "A_ON")))
CLAIM = "SOURCE_AUTHORED_BIRTH_NOT_CLEAN"
ORIGIN = "UNRESOLVED_LOCAL_HASHES_ONLY"
CLAIMS = dict(P1=False, G3=False, G5=False, H1=False, H2=False, freeze=False,
              clean_lineage=False, independent_holdout=False)
PANEL_EXPOSURE = "same fixed128 initial-birth dev panel; repeated/exposed diagnostic, not independent holdout"
SOURCE_ROOT = Path("/data/home/rohing/dream-state")
REQUIRED_SOURCE_PINS = {
    "/tmp/astra_rulegame_process_readout_20260912.py": "46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46",
    "/tmp/astra_birth_conditional_run_20260913.py": "072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa",
    str(SOURCE_ROOT / "organism_v6/rulegame_parenting_diagnostic.py"): "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
    str(SOURCE_ROOT / "organism_v6/birth_conditional_corpus.py"): "43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b",
}
_HELPERS = None
_PROCESS_BINDING = None
_CAPTURED_PANELS = set()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def value_hash(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False) + "\n").encode()).hexdigest()


def _keys(value, names, label):
    require(type(value) is dict and set(value) == set(names.split()), label + " keys differ")


def _pin(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SHA256")


def _files(value, adapter=False):
    require(type(value) is dict and value, "nonempty file pins required")
    for name, pin in value.items():
        require(type(name) is str and name and ".." not in PurePosixPath(name).parts, "unsafe file key")
        _pin(pin)
    if adapter:
        require(set(value) in ({"adapter_config.json", "adapter_model.safetensors"},
                               {"adapter_config.json", "adapter_model.bin"}), "single LoRA files required")


def _receipt(receipt, names):
    _keys(receipt, "receipt_sha256 " + names, "receipt")
    _pin(receipt["receipt_sha256"])
    require(receipt["receipt_sha256"] == value_hash({key: value for key, value in receipt.items()
                                                    if key != "receipt_sha256"}), "normalized receipt hash differs")


def _absolute(value):
    require(type(value) is str and Path(value).is_absolute() and ".." not in Path(value).parts,
            "absolute loader path required")


def _identity(base, receipt):
    _absolute(receipt["adapter"])
    _files(receipt["adapter_files"], adapter=True)
    expected = dict(backend="vllm", model_input=base["model"], adapter_input=receipt["adapter"],
                    adapter_files=receipt["adapter_files"], default_max_tokens=400, default_temperature=0.7,
                    scope="configured loader inputs; base authentication requires lineage pins")
    require(receipt["identity"] == expected, "actual single-adapter/base identity differs")


def validate_lineage(lineage):
    """Join Main's release-verified normalized receipts; does not certify raw releases."""
    _keys(lineage, "schema source base birth writes claim origin", "lineage")
    require(lineage["schema"] == SCHEMA and lineage["claim"] == CLAIM and lineage["origin"] == ORIGIN,
            "lineage scope differs")
    source, base, birth = (lineage[name] for name in ("source", "base", "birth"))
    _receipt(source, "files")
    _files(source["files"])
    require(all(source["files"].get(name) == pin for name, pin in REQUIRED_SOURCE_PINS.items()), "source pins differ")
    _receipt(base, "model model_files")
    _absolute(base["model"])
    _files(base["model_files"])
    require(all(not PurePosixPath(name).is_absolute() for name in base["model_files"]), "relative base file keys required")
    _receipt(birth, "release source_receipt_sha256 base_receipt_sha256 arm root candidate_sha256 panel_sha256 adapter adapter_files identity")
    require(birth["arm"] == "AUTH" and type(birth["root"]) is int and birth["root"] in (0, 1, 2),
            "one original AUTH birth root required")
    _pin(birth["candidate_sha256"])
    _pin(birth["panel_sha256"])
    _keys(lineage["writes"], "P_WRITE A_WRITE", "writes")
    receipts = {"BIRTH_ONLY": birth, **lineage["writes"]}
    for cell, receipt in receipts.items():
        if cell != "BIRTH_ONLY":
            _receipt(receipt, "release source_receipt_sha256 base_receipt_sha256 parent_birth_receipt_sha256 parent_adapter_files_sha256 formation_receipt_sha256 own_wake_arm material_sha256 warm_start adapter adapter_files identity")
            require(receipt["warm_start"] is True and receipt["own_wake_arm"] == cell[0], "own-wake warm start required")
            require(receipt["parent_birth_receipt_sha256"] == birth["receipt_sha256"]
                    and receipt["parent_adapter_files_sha256"] == value_hash(birth["adapter_files"]),
                    "descendant must independently start from original birth")
            _pin(receipt["formation_receipt_sha256"])
            _pin(receipt["material_sha256"])
        require(receipt["source_receipt_sha256"] == source["receipt_sha256"]
                and receipt["base_receipt_sha256"] == base["receipt_sha256"], "source/base receipt join differs")
        _keys(receipt["release"], "sha256 status", "release")
        _pin(receipt["release"]["sha256"])
        require(receipt["release"]["status"] == "COMPLETE", "Main-verified completed release required")
        _identity(base, receipt)
    parented, active = (receipts[cell] for cell in ("P_WRITE", "A_WRITE"))
    require(parented["formation_receipt_sha256"] == active["formation_receipt_sha256"], "formation receipt join differs")
    require(len({row["adapter"] for row in receipts.values()}) == 3, "three distinct immutable adapter paths required")
    return receipts


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _helpers():
    global _HELPERS
    for path, pin in REQUIRED_SOURCE_PINS.items():
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == pin, "inspected helper bytes changed: " + path)
    if _HELPERS is None:
        if str(SOURCE_ROOT) not in sys.path:
            sys.path.insert(0, str(SOURCE_ROOT))
        diagnostic = importlib.import_module("organism_v6.rulegame_parenting_diagnostic")
        corpus = importlib.import_module("organism_v6.birth_conditional_corpus")
        require(all(Path(module.__file__).resolve().parents[1] == SOURCE_ROOT.resolve()
                    for module in (diagnostic, corpus)), "wrong imported source root")
        legacy = _load("/tmp/astra_rulegame_process_readout_20260912.py", "born_readout_legacy_metrics")
        driver = _load("/tmp/astra_birth_conditional_run_20260913.py", "born_readout_frozen_birth_driver")
        _HELPERS = diagnostic, corpus, legacy, driver
    diagnostic, corpus, legacy, driver = _HELPERS
    require(diagnostic.schedule()["evaluation"] == [f"rule{rule}/astra-minimum-20260912/readout" for rule in range(2, 6)]
            and diagnostic.CELLS == ("OFF", "P_ON", "A_ON")
            and diagnostic.LIMITS["evaluation"] == dict(wake=20, record=12), "fixed schedule/budgets changed")
    return diagnostic, corpus, legacy, driver


def conditional_requests(lineage, candidate):
    """Exact initial-birth dev requests, including all conditional and anchor rows."""
    validate_lineage(lineage)
    _, corpus, _, driver = _helpers()
    birth = lineage["birth"]
    require(candidate["root"] == birth["root"] and corpus.digest(candidate) == birth["candidate_sha256"],
            "initial birth candidate differs")
    requests = driver.fixed_requests(corpus, candidate)
    require(len(requests) == 128 and value_hash(requests) == birth["panel_sha256"], "initial fixed128 panel differs")
    return requests


def _header(lineage, cell, panel, worker_id):
    receipts = validate_lineage(lineage)
    require(cell in CELLS, "unknown actual cell; legacy OFF is not accepted")
    require(type(worker_id) is str and bool(worker_id.strip()), "Main-assigned worker ID required")
    return dict(schema=CAPTURE_SCHEMA, panel=panel, cell=cell, legacy_schedule_slot=SCHEDULE_SLOTS[cell],
                backend=receipts[cell]["identity"], lineage_sha256=value_hash(lineage),
                worker_id=worker_id, pid=os.getpid())


def _begin(out, header, backend, diagnostic):
    global _PROCESS_BINDING
    binding = (header["pid"], header["worker_id"], header["cell"], header["lineage_sha256"])
    require(_PROCESS_BINDING in (None, binding), "fresh child-only process per actual cell required")
    require(header["panel"] not in _CAPTURED_PANELS, "no panel retry/reuse in a worker")
    require(backend.identity() == header["backend"], "injected backend identity differs")
    _PROCESS_BINDING = binding
    _CAPTURED_PANELS.add(header["panel"])
    out = Path(out)
    out.mkdir(parents=False, exist_ok=False)
    diagnostic.write_json(out / "identity.json", header)
    return out


def _close(out, count, header, backend, diagnostic):
    require(backend.identity() == header["backend"], "backend identity changed before close")
    diagnostic.write_json(out / "closed.json", dict(calls=count, calls_closed=True))
    diagnostic.capture_manifest(out)
    return dict(cell=header["cell"], panel=header["panel"], path=str(out), pid=header["pid"],
                worker_id=header["worker_id"], manifest_sha256=diagnostic.digest(out / "manifest.json"))


def _tasks(calls, events, cell, diagnostic):
    return [diagnostic.play_task(calls, events, cell, eid, notes=True, prefix="")[0]
            for eid in diagnostic.schedule()["evaluation"]]


def capture_rulegame(out, lineage, cell, backend, *, worker_id):
    """Capture the unchanged schedule, with actual cells in raw calls/events; no aggregate."""
    diagnostic, _, _, _ = _helpers()
    header = _header(lineage, cell, "rulegame", worker_id)
    out = _begin(out, header, backend, diagnostic)
    calls = diagnostic.Calls(out / "calls", backend, "evaluation", header["backend"], "interaction_v3")
    events = diagnostic.Events(out / "events.jsonl")
    tasks = _tasks(calls, events, cell, diagnostic)
    diagnostic.write_json(out / "tasks.json", tasks)
    return _close(out, calls.count, header, backend, diagnostic)


def capture_conditional(out, lineage, cell, candidate, backend, *, worker_id):
    """Separate complete fixed128 capture; only frozen context reaches the backend."""
    requests = conditional_requests(lineage, candidate)
    diagnostic, _, _, _ = _helpers()
    header = _header(lineage, cell, "conditional", worker_id)
    out = _begin(out, header, backend, diagnostic)
    (out / "calls").mkdir()
    for request in requests:
        require(backend.identity() == header["backend"], "conditional backend identity changed")
        call_id = request["call_id"]
        diagnostic.write_json(out / "calls" / (call_id + ".request.json"),
                              dict(request=request, started=time.monotonic(), identity=header["backend"],
                                   prompt_sha256=value_hash(request["prompt"])))
        response = backend.generate(request)
        diagnostic.write_json(out / "calls" / (call_id + ".response.json"),
                              dict(response=response, ended=time.monotonic(), response_sha256=value_hash(response)))
        diagnostic.validate_response(request, response)
        require("finish_reason" in response and "stop_reason" in response, "raw stop metadata required")
    return _close(out, len(requests), header, backend, diagnostic)


def capture_cell(out, lineage, cell, candidate, backend, *, worker_id):
    """Call inside Main's fresh supervised child worker with its already-loaded backend.

    Main closes the backend and joins the worker before supplying exit receipts.
    This function neither creates a process nor loads/closes a model.
    """
    conditional_requests(lineage, candidate)
    _header(lineage, cell, "rulegame", worker_id)
    out = Path(out)
    out.mkdir(parents=False, exist_ok=False)
    rulegame = capture_rulegame(out / "rulegame", lineage, cell, backend, worker_id=worker_id)
    conditional = capture_conditional(out / "conditional", lineage, cell, candidate, backend, worker_id=worker_id)
    return dict(rulegame=rulegame, conditional=conditional)


def _opened(out, lineage, cell, panel, diagnostic):
    out = Path(out)
    require(diagnostic.read(out / "manifest.json")["files"] == diagnostic.tree_hashes(out, ("manifest.json",)),
            "capture bytes changed")
    header = diagnostic.read(out / "identity.json")
    _keys(header, "schema panel cell legacy_schedule_slot backend lineage_sha256 worker_id pid", "capture header")
    expected = _header(lineage, cell, panel, header["worker_id"])
    require(type(header["pid"]) is int and header["pid"] > 0, "invalid worker PID")
    expected["pid"] = header["pid"]
    require(header == expected, "actual cell/identity/lineage binding differs")
    closed = diagnostic.read(out / "closed.json")
    _keys(closed, "calls calls_closed", "capture close")
    require(closed["calls_closed"] is True and type(closed["calls"]) is int, "capture is not closed")
    require(0 <= closed["calls"] <= (32 if panel == "rulegame" else 128), "capture call ceiling differs")
    names = {f"{index:04d}.{kind}.json" for index in range(closed["calls"])
             for kind in ("request", "response")}
    require({entry.name for entry in (out / "calls").iterdir()} == names, "extra/missing raw call pairs")
    expected_files = {"identity.json", "closed.json", "manifest.json", "calls"}
    if panel == "rulegame":
        expected_files |= {"tasks.json", "events.jsonl"}
    require({entry.name for entry in out.iterdir()} == expected_files, "unexpected capture context or aggregate")
    return out, header, closed


def _raw_pairs(out, diagnostic):
    pairs, previous = [], 0
    for path in sorted((out / "calls").glob("*.request.json")):
        sent = diagnostic.read(path)
        received = diagnostic.read(path.with_name(path.name.replace(".request.", ".response.")))
        require(all(type(clock) in (int, float) and math.isfinite(clock) for clock in (sent["started"], received["ended"]))
                and previous <= sent["started"] <= received["ended"], "raw call clock/order differs")
        require("finish_reason" in received["response"] and "stop_reason" in received["response"], "raw stop metadata missing")
        previous = received["ended"]
        pairs.append((sent, received))
    return pairs


def replay_rulegame(out, lineage, cell):
    """Public raw replay, intentionally without cross-task metrics or usage sums."""
    diagnostic, _, _, _ = _helpers()
    out, header, closed = _opened(out, lineage, cell, "rulegame", diagnostic)
    calls = diagnostic.ReplayCalls(out / "calls", header["backend"], "interaction_v3")
    events = diagnostic.Events()
    tasks = _tasks(calls, events, cell, diagnostic)
    require(tasks == diagnostic.read(out / "tasks.json")
            and events.rows == [diagnostic.decode(line) for line in (out / "events.jsonl").read_text().splitlines()],
            "task/event replay differs")
    require(calls.count == closed["calls"] and all(count <= diagnostic.LIMITS["evaluation"].get(role, 0)
            for role, count in calls.counts.items()), "replayed call limits differ")
    pairs = _raw_pairs(out, diagnostic)
    return dict(header=header, tasks=tasks, events=events.rows, calls=calls.count,
                roles=dict(calls.counts), raw_pairs=pairs)


def replay_conditional(out, lineage, cell, candidate):
    """Public replay preserves every raw response, including empty/invalid outputs."""
    requests = conditional_requests(lineage, candidate)
    diagnostic, _, _, _ = _helpers()
    out, header, closed = _opened(out, lineage, cell, "conditional", diagnostic)
    require(closed["calls"] == 128, "full fixed128 panel must close before scoring")
    pairs = _raw_pairs(out, diagnostic)
    outputs = {}
    for request, (sent, received) in zip(requests, pairs, strict=True):
        response = received["response"]
        require(sent["request"] == request and sent["identity"] == header["backend"]
                and sent["prompt_sha256"] == value_hash(request["prompt"])
                and received["response_sha256"] == value_hash(response), "conditional raw request/identity/response differs")
        diagnostic.validate_response(request, response)
        outputs[request["case_id"]] = response["text"]
    return dict(header=header, calls=len(pairs), outputs=outputs, raw_pairs=pairs)


def reduce_joint(captures, lineage, candidate, worker_exits):
    """Score only after six complete replays and three Main-supplied successful joins.

    worker_exits maps actual cell to {worker_id, pid, returncode, backend_closed,
    capture_manifest_sha256: {rulegame, conditional}}. Preserve capture-returned pins.
    These are Main's supervisor attestations, not an independently verified custody layer.
    """
    validate_lineage(lineage)
    conditional_requests(lineage, candidate)
    _keys(captures, "BIRTH_ONLY P_WRITE A_WRITE", "capture cells")
    _keys(worker_exits, "BIRTH_ONLY P_WRITE A_WRITE", "worker exits")
    diagnostic, corpus, legacy, _ = _helpers()
    replays, pids, worker_ids = {}, set(), set()
    for cell in CELLS:
        _keys(captures[cell], "rulegame conditional", "cell captures")
        exit_receipt = worker_exits[cell]
        _keys(exit_receipt, "worker_id pid returncode backend_closed capture_manifest_sha256", "worker exit")
        _keys(exit_receipt["capture_manifest_sha256"], "rulegame conditional", "capture manifest pins")
        for panel, path in captures[cell].items():
            pin = exit_receipt["capture_manifest_sha256"][panel]
            _pin(pin)
            require(diagnostic.digest(Path(path) / "manifest.json") == pin, "Main-bound capture manifest changed")
        game = replay_rulegame(captures[cell]["rulegame"], lineage, cell)
        conditional = replay_conditional(captures[cell]["conditional"], lineage, cell, candidate)
        require(type(exit_receipt["returncode"]) is int and exit_receipt["returncode"] == 0
                and exit_receipt["backend_closed"] is True, "worker/backend has not successfully closed")
        for header in (game["header"], conditional["header"]):
            require(header["pid"] == exit_receipt["pid"] and header["worker_id"] == exit_receipt["worker_id"],
                    "panel/process exit join differs")
        require(exit_receipt["pid"] not in pids and exit_receipt["pid"] != os.getpid()
                and exit_receipt["worker_id"] not in worker_ids, "distinct fresh child processes required")
        pids.add(exit_receipt["pid"])
        worker_ids.add(exit_receipt["worker_id"])
        replays[cell] = game, conditional
    total_calls = sum(game["calls"] + panel["calls"] for game, panel in replays.values())
    require(total_calls <= 480, "joint call ceiling exceeded")
    scores = {}
    for cell in CELLS:
        game, conditional = replays[cell]
        result = dict(cell=cell, tasks=game["tasks"], calls=game["calls"], roles=game["roles"],
                      faithful_records=sum(row["kind"] == "record" and row["eligible"] for row in game["events"]),
                      mean_quiz_accuracy=sum(row["quiz_accuracy"] for row in game["tasks"]) / 4)
        metrics = legacy.process_metrics(Path(captures[cell]["rulegame"]), dict(result=result, events=game["events"]), diagnostic)
        panel = corpus.score_outputs(candidate, conditional["outputs"], split="dev", assigned_arm="AUTH")
        flags = {sent["request"]["case_id"]: dict(finish_reason=received["response"]["finish_reason"],
                 stop_reason=received["response"]["stop_reason"], output_tokens=len(received["response"]["output_token_ids"]),
                 hit_token_limit=len(received["response"]["output_token_ids"]) == 64)
                 for sent, received in conditional["raw_pairs"]}
        scores[cell] = dict(actual_identity=game["header"]["backend"], legacy_schedule_slot=SCHEDULE_SLOTS[cell],
                            rulegame=metrics, conditional=panel, conditional_flags=flags,
                            usage={name: diagnostic.usage(Path(path)) for name, path in captures[cell].items()})
    contrasts = {}
    for first, second in (("P_WRITE", "BIRTH_ONLY"), ("A_WRITE", "BIRTH_ONLY"), ("P_WRITE", "A_WRITE")):
        contrasts[first + "_minus_" + second] = dict(
            quiz_accuracy_fixed24=scores[first]["rulegame"]["quiz_accuracy_fixed24"] - scores[second]["rulegame"]["quiz_accuracy_fixed24"],
            faithful_record_fraction_allotted12=scores[first]["rulegame"]["faithful_record_fraction_allotted12"] - scores[second]["rulegame"]["faithful_record_fraction_allotted12"],
            conditional_operations={operation: {metric: scores[first]["conditional"]["operations"][operation][metric]
                                    - scores[second]["conditional"]["operations"][operation][metric]
                                    for metric in ("auth_strict_joint", "instruction_compliant", "tag_spill")}
                                    for operation in corpus.OPERATIONS})
    receipts = validate_lineage(lineage)
    weights = {cell: next(pin for name, pin in row["adapter_files"].items() if name.startswith("adapter_model."))
               for cell, row in receipts.items()}
    return dict(schema="born-child-joint-readout-v1", cells=scores, contrasts=contrasts,
                lineage_sha256=value_hash(lineage), claim=CLAIM, origin=ORIGIN, claims=dict(CLAIMS),
                panel_exposure=PANEL_EXPOSURE, model_calls=total_calls, maximum_model_calls=480,
                descendant_weights_equal_birth={cell: weights[cell] == weights["BIRTH_ONLY"] for cell in CELLS[1:]},
                descendant_weights_equal_each_other=weights["P_WRITE"] == weights["A_WRITE"],
                scope="one-root exploratory local utility/retention contrast only; no online updates",
                all_six_captures_replayed_before_metrics=True)
