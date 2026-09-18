"""One fixed, parent/world/fit-free relation readout; Main alone prepares/runs."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

from . import rulegame_parenting_diagnostic as base


SEALED_MANIFEST = "4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41"
SEALED_PLAN = "5cc110bceb6e92186bc707fdd4369eaf53690a4fba694ac1fa5b8b8dbfcc88f7"
CASES = (("0008", "0007", False, [2, 3, 4]),
         ("0010", "0009", True, [1, 2, 3]),
         ("0012", "0011", None, [0, 1, 2]))
SURFACES = ("original", "fullclarified", "tokenclarified")
MAPPING = ('Explicit mapping: no prediction (null) => unavailable; prediction equal to '
           'observation => matched; prediction different from observation => mismatched.')
TOKEN_ONLY = "Output only the relation token: matched, mismatched, or unavailable. No JSON or other text."
LIMITS = ("Original formation comparisons change temperature from 0.7 to 0.0 (and seed). "
          "Fullclarified versus original tests the explicit definition at the same JSON format/0.0. "
          "Tokenclarified also changes format and output cap. Three positive-observation events "
          "from one life only; not a base ceiling or general Boolean ability claim.")


def sources():
    return dict(base.sources(), **{name: base.digest(base.REPO / "organism_v6" / name)
                for name in ("relation_surface_diagnostic.py", "reasoning_neutral_probe.py")})


def bind(formation):
    formation = Path(formation).expanduser().resolve(strict=True)
    data = formation / "formation" / "data"
    base.require(base.digest(data / "manifest.json") == SEALED_MANIFEST, "not the selected sealed formation")
    base.require(base.digest(formation / "plan.json") == SEALED_PLAN, "formation plan differs")
    audit = base.check_capture(data, protocol="interaction_v2")
    base.require(audit["ok"], str(audit["failures"]))
    original = base.read(formation / "plan.json")
    header = base.read(data / "identity.json")
    base.require(header["model_files"] == original["model_files"] and
                 header["backend"] == base.expected_identity(original), "formation model identity differs")
    cases = []
    for tick, (record_id, source_id, predicted, values) in enumerate(CASES, 1):
        records = [row for row in audit["events"] if row["kind"] == "record" and row["call_id"] == record_id]
        executions = [row for row in audit["events"] if row["kind"] == "execution" and row["call_id"] == source_id]
        base.require(len(records) == len(executions) == 1, "record/event cardinality differs")
        record, execution = records[0], executions[0]
        eid = "rule0/astra-minimum-20260912/lesson0/apply"
        execution_id = f"P:{eid}#t{tick}"
        base.require(record["execution_id"] == execution["execution_id"] == execution_id and
                     record["source_call_id"] == source_id and execution["observed"] is True and
                     execution["predicted"] is predicted and execution["values"] == values and
                     not execution["prediction_ambiguous"], "selected event binding differs")
        request = base.read(data / "calls" / f"{record_id}.request.json")["request"]
        raw = base.read(data / "calls" / f"{source_id}.response.json")["response"]["text"]
        fields = {key: execution[key] for key in ("values", "observed", "predicted")}
        prefix = (f"Task: {eid}\nExecution: {eid}#t{tick}\nActual emitted output:\n{raw}"
                  f"\nActual world response:\n{execution['outcome']}\nObserved fields: {json.dumps(fields)}\n")
        base.require(raw == execution["raw_response"] and request["prompt"] == prefix + base.RECORD and
                     request["temperature"] == .7 and request["max_tokens"] == 100 and
                     request["role"] == "record", "raw/world/prompt binding differs")
        cases.append(dict(record_id=record_id, source_id=source_id, execution_id=execution_id,
                          execution=execution, original_request=request, prefix=prefix))
    return original, cases


def requests(cases):
    result = []
    for case in cases:
        original = case["original_request"]["prompt"]
        prompts = (original, original + "\n" + MAPPING, case["prefix"] + MAPPING + "\n" + TOKEN_ONLY)
        for surface, prompt, cap in zip(SURFACES, prompts, (100, 100, 8)):
            result.append(dict(case["original_request"], call_id=f"{len(result):04d}",
                               prompt=prompt, surface=surface, record_id=case["record_id"],
                               source_call_id=case["source_id"], execution_id=case["execution_id"],
                               temperature=0.0, seed=20260912, max_tokens=cap))
    base.require(len(result) == 9 and sum(row["max_tokens"] for row in result) == 624, "fixed budget differs")
    return result


def prepare(formation, out, device, lease_end):
    original, cases = bind(formation)
    model = original["model"]
    base.require(device == "0", "Main allocates GPU0 only")
    end = datetime.fromisoformat(lease_end.replace("Z", "+00:00"))
    base.require(end.tzinfo is not None and end.timestamp() > time.time() + 750, "insufficient lease")
    base.require(base.model_hashes(model) == original["model_files"], "model bytes differ from formation")
    tokenizer = base.native_tokenizer(model)
    base.audit_native_calls(tokenizer, Path(formation).expanduser() / "formation" / "data")
    fixed = requests(cases)
    for request in fixed:
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                 tokenize=False, add_generation_prompt=True)
        base.require(len(tokenizer.encode(rendered)) + request["max_tokens"] <= base.MAX_MODEL_LEN,
                     "diagnostic prompt exceeds context")
    formation = Path(formation).expanduser().resolve()
    destination = Path(out).expanduser().resolve()
    base.require(formation != destination and formation not in destination.parents and
                 destination not in formation.parents, "output overlaps immutable formation")
    plan = dict(formation=str(formation), model=model, model_files=original["model_files"], device=device,
                lease_end=end.timestamp(), source_hashes=sources(), requests=fixed, claim_limits=LIMITS,
                formation_manifest=SEALED_MANIFEST, formation_plan=SEALED_PLAN,
                native_source_token_audit=True, worker_seconds=600, output_cap=624)
    root = base.fresh_directory(out, model)
    base.write_json(root / "plan.json", plan)
    base.write_json(root / "plan.sha256.json", dict(sha256=base.digest(root / "plan.json")))
    return plan


def verify(root):
    root = Path(root)
    base.require(base.digest(root / "plan.json") == base.read(root / "plan.sha256.json")["sha256"], "plan changed")
    plan = base.read(root / "plan.json")
    original, cases = bind(plan["formation"])
    base.require(plan["source_hashes"] == sources() and plan["requests"] == requests(cases), "source/requests changed")
    base.require(plan["model"] == original["model"] and plan["model_files"] == original["model_files"] ==
                 base.model_hashes(plan["model"]), "model pins changed")
    base.require(plan["device"] == "0" and plan["worker_seconds"] == 600 and plan["output_cap"] == 624,
                 "bounds changed")
    return plan, cases


def capture(plan, path, factory=base.NativeBackend, closer=None):
    if closer is None:
        from .model_backend import close_backend
        closer = close_backend
    backend = None
    path = Path(path)
    (path / "calls").mkdir()
    try:
        backend = factory(plan["model"], None)
        identity = base.expected_identity(plan)
        base.require(backend.identity() == identity, "native identity differs")
        base.write_json(path / "identity.json", dict(backend=identity, model_files=plan["model_files"]))
        base.write_json(path / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
        for request in plan["requests"]:
            base.require(backend.identity() == identity, "native identity changed")
            stem = path / "calls" / request["call_id"]
            base.write_json(str(stem) + ".request.json", dict(request=request, started=time.monotonic(),
                            identity=identity, prompt_sha256=base.value_hash(request["prompt"])))
            response = backend.generate(request)
            base.write_json(str(stem) + ".response.json", dict(response=response, ended=time.monotonic(),
                            response_sha256=base.value_hash(response)))
            base.validate_response(request, response)
    except BaseException as error:
        base.write_json(path / "failure.json", dict(error=str(error)))
        raise
    finally:
        closed, error = False, None
        try:
            closed = closer(backend.backend if backend is not None else None)
        except Exception as failure:
            error = str(failure)
        base.write_json(path / "backend.cleanup.json", dict(closed=closed, error=error,
                        scope="owned backend handle and descendant engine PIDs only"))
        base.require(closed is True, "owned cleanup failed; Main must retain reservation")
    base.capture_manifest(path)


def worker(root):
    root = Path(root).resolve()
    plan, _ = verify(root)
    base.require(base.supervisor.selected_device() == plan["device"], "worker device differs")
    receipt = root / "run" / "worker" / "process.json"
    until = time.monotonic() + 5
    while not receipt.exists() and time.monotonic() < until:
        time.sleep(.05)
    base.require(base.read(receipt)["pid"] == os.getpid() == os.getpgrp(), "supervisor ownership required")
    parent_pid, deadline = os.getppid(), time.monotonic() + 600
    stop = threading.Event()
    def interrupted(signum, frame):
        raise RuntimeError(f"worker interrupted by signal {signum}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    def watch_parent():
        while not stop.wait(.2):
            if os.getppid() != parent_pid or time.monotonic() >= deadline or time.time() >= plan["lease_end"] - 10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    watcher = threading.Thread(target=watch_parent, daemon=True)
    watcher.start()
    try:
        capture(plan, base.fresh_directory(root / "run" / "data", plan["model"]))
    finally:
        stop.set()
        watcher.join()
        for number, handler in handlers.items():
            signal.signal(number, handler)


def run(root, allow_gpu=False):
    base.require(allow_gpu, "Main must explicitly allocate GPU0 and pass --allow-gpu")
    root = Path(root).resolve()
    plan, _ = verify(root)
    stage = base.fresh_directory(root / "run", plan["model"])
    command = [sys.executable, "-B", "-m", "organism_v6.relation_surface_diagnostic",
               "_worker", "--root", str(root), "--allow-gpu"]
    return base.supervise(root, plan, stage / "worker", command, stage / "data" / "calls")


def mapped(text, surface):
    try:
        if surface == "tokenclarified":
            answer = text.strip()
        else:
            record = base.decode(text)
            base.require(isinstance(record, dict) and set(record) == {"try", "observed", "predicted", "relation"},
                         "JSON record schema")
            answer = record["relation"]
        base.require(answer in ("matched", "mismatched", "unavailable"), "relation parse failure")
        return answer, False
    except (ValueError, TypeError, KeyError):
        return None, True


def reduce(root):
    root = Path(root)
    plan, cases = verify(root)
    path = root / "run" / "data"
    supervision = base.read(root / "run" / "worker" / "supervision.json")
    base.require(supervision["ok"] and supervision["reservation_release_verified"], "unverified supervision/cleanup")
    base.require(base.read(path / "manifest.json")["files"] == base.tree_hashes(path, ("manifest.json",)), "capture changed")
    base.require(base.read(path / "backend.cleanup.json")["closed"] is True, "backend cleanup unverified")
    base.require(len(list((path / "calls").glob("*.json"))) == 18, "raw call cardinality differs")
    identity = base.expected_identity(plan)
    base.require(base.read(path / "identity.json") == dict(backend=identity, model_files=plan["model_files"]), "identity changed")
    rows, last_ended = [], 0
    for request in plan["requests"]:
        stem = path / "calls" / request["call_id"]
        sent, received = base.read(str(stem) + ".request.json"), base.read(str(stem) + ".response.json")
        response = received["response"]
        base.require(sent["request"] == request and sent["identity"] == identity and
                     sent["prompt_sha256"] == base.value_hash(request["prompt"]) and
                     received["response_sha256"] == base.value_hash(response), "raw receipt binding changed")
        base.require(last_ended <= sent["started"] <= received["ended"], "call timing differs")
        last_ended = received["ended"]
        base.validate_response(request, response)
        case = next(item for item in cases if item["record_id"] == request["record_id"])
        execution = case["execution"]
        predicted = execution["predicted"]
        expected = "unavailable" if predicted is None else "matched" if predicted == execution["observed"] else "mismatched"
        answer, unparseable = mapped(response["text"], request["surface"])
        rows.append(dict(call_id=request["call_id"], record_id=case["record_id"], execution_id=case["execution_id"],
                         surface=request["surface"], raw_text=response["text"], mapped_answer=answer,
                         unparseable=unparseable, expected=expected, correct=answer == expected,
                         record_audit=base.judge_record(response["text"], execution) if request["surface"] != "tokenclarified" else None))
    base.audit_native_calls(base.native_tokenizer(plan["model"]), path)
    result = dict(rows=rows, cost=base.usage(path), reserved_seconds=supervision["reserved_seconds"],
                  output_token_ceiling=624, native_token_text_audit=True, claim_limits=LIMITS,
                  monetary_cost=None, monetary_cost_note="No billing-rate evidence; native tokens and elapsed seconds recorded.")
    base.write_json(root / "reduction.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("check", "prepare", "run", "reduce", "_worker"))
    parser.add_argument("--formation", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--device", default="0")
    parser.add_argument("--lease-end")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.stage in ("check", "prepare"):
        base.require(args.formation is not None, "--formation required")
        if args.stage == "check":
            _, cases = bind(args.formation)
            result = dict(requests=requests(cases), claim_limits=LIMITS)
        else:
            base.require(args.out is not None and args.lease_end is not None, "--out and --lease-end required")
            result = prepare(args.formation, args.out, args.device, args.lease_end)
    else:
        base.require(args.root is not None, "--root required")
        if args.stage == "_worker":
            base.require(args.allow_gpu, "explicit --allow-gpu required")
            result = worker(args.root)
        else:
            result = run(args.root, args.allow_gpu) if args.stage == "run" else reduce(args.root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
