"""Fixed 48-case native dev readout; no fitting, parent, or live world."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import threading
import time

from . import fundamental_teaching_corpus as corpus
from . import rulegame_parenting_diagnostic as base


CASE_IDS = tuple(f"eval-addition-{index:03d}" for index in range(32)) + tuple(
    f"eval-memory-{index:03d}-0" for index in range(16))
SEED = 20260912
MAX_TOKENS = 64
WORKER_SECONDS = 600
CLAIM_LIMITS = ("Fixed dev-only toy behavioral readout, not confirmation, prediction intelligence, "
                "parenting efficacy, H1/H2, clean lineage, or absence of prior exposure. "
                "Action correctness and formatting adherence are separate. Local byte hashes "
                "bind loader inputs, not base origin. Missing artifacts are not scientific zeros.")


def score_addition(text, expected):
    def labels(label):
        rows = []
        for index, line in enumerate(text.splitlines()):
            if re.match(r"^[ \t]*" + label + r"\b", line):
                match = re.fullmatch(r"[ \t]*" + label + r":[ \t]*([+-]?[0-9]+)[ \t]*", line)
                rows.append((index, int(match[1]) if match else None))
        return rows

    actions, predictions = labels("ACT"), labels("PREDICT")
    first_act = actions[0][1] if actions else None
    first_predict = predictions[0][1] if predictions else None
    action_valid = len(actions) == 1 and first_act is not None
    prediction_valid = len(predictions) == 1 and first_predict is not None
    correct_action = action_valid and first_act == expected
    predict_before_act = bool(action_valid and prediction_valid and predictions[0][0] < actions[0][0])
    return dict(raw_text=text, expected=expected, first_act=first_act, act_count=len(actions),
                action_valid=action_valid, correct_action=correct_action, first_predict=first_predict,
                predict_count=len(predictions), prediction_valid=prediction_valid,
                predict_before_act=predict_before_act,
                adherence=bool(correct_action and predict_before_act and first_predict == expected))


def score_memory(text, expected):
    normalized = text.strip().lower()
    if normalized.endswith("."):
        normalized = normalized[:-1]
    valid = normalized in corpus.COLORS
    return dict(raw_text=text, expected=expected, normalized=normalized,
                answer=normalized if valid else None, valid=valid, correct=valid and normalized == expected)


def selected_cases():
    evaluation = corpus.build_candidate()["eval"]
    indexed = {row["id"]: row for row in evaluation}
    base.require(len(indexed) == len(evaluation), "duplicate candidate IDs")
    return [indexed[case_id] for case_id in CASE_IDS]


def requests(cases):
    base.require(cases == selected_cases(), "fixed dev selection differs")
    return [dict(call_id=f"{index:04d}", case_id=case["id"], role="readout", arm="readout",
                 prompt=case["context"], temperature=0.0, seed=SEED, max_tokens=MAX_TOKENS)
            for index, case in enumerate(cases)]


def sources():
    return dict(base.sources(), **{name: base.digest(base.REPO / "organism_v6" / name) for name in (
        "fundamental_teaching_readout.py", "fundamental_teaching_corpus.py", "reasoning_neutral_probe.py")})


def native_inputs(tokenizer, fixed):
    rows = []
    for request in fixed:
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": request["prompt"]}],
                                                 tokenize=False, add_generation_prompt=True)
        tokens = tokenizer.encode(rendered)
        base.require(tokens and len(tokens) + MAX_TOKENS <= base.MAX_MODEL_LEN, "prompt exceeds native context")
        rows.append(dict(call_id=request["call_id"], rendered_prompt=rendered, prompt_token_ids=tokens))
    return rows


def prepare(out, model, adapter, device, lease_end):
    model = str(Path(model).expanduser().resolve(strict=True))
    adapter = str(Path(adapter).expanduser().resolve(strict=True)) if adapter is not None else None
    base.require(base.read(Path(model) / "config.json").get("model_type") == "qwen2", "expected Qwen base")
    base.require(isinstance(device, str) and re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device),
                 "one explicit device required")
    end = float(lease_end)
    base.require(math.isfinite(end) and end > time.time() + WORKER_SECONDS + base.CLEANUP_RESERVE + 10,
                 "insufficient lease for bounded worker and cleanup")
    destination = Path(out).expanduser().resolve()
    if adapter is not None:
        source = Path(adapter)
        base.require(source.is_dir() and destination != source and destination not in source.parents and
                     source not in destination.parents, "output overlaps adapter or adapter is not a directory")
    root = base.fresh_directory(out, model)
    cases = selected_cases()
    fixed = requests(cases)
    plan = dict(schema=1, model=model, adapter=adapter, device=device, lease_end=end,
                model_files=base.model_hashes(model), adapter_files=base.tree_hashes(adapter) if adapter else {},
                cases=cases, requests=fixed, source_hashes=sources(),
                native_inputs=native_inputs(base.native_tokenizer(model), fixed),
                worker_seconds=WORKER_SECONDS, output_token_ceiling=len(CASE_IDS) * MAX_TOKENS,
                claim_limits=CLAIM_LIMITS)
    plan["identity"] = base.expected_identity(plan, adapter)
    base.write_json(root / "plan.json", plan)
    base.write_json(root / "plan.sha256.json", dict(sha256=base.digest(root / "plan.json")))
    return plan


def verify(root):
    root = Path(root)
    base.require(base.digest(root / "plan.json") == base.read(root / "plan.sha256.json")["sha256"], "plan changed")
    plan = base.read(root / "plan.json")
    cases = selected_cases()
    base.require(plan["source_hashes"] == sources(), "source hashes changed")
    base.require(plan["cases"] == cases and plan["requests"] == requests(cases), "fixed cases/requests changed")
    base.require(plan["schema"] == 1 and plan["worker_seconds"] == WORKER_SECONDS == base.WORKER_SECONDS and
                 plan["output_token_ceiling"] == 3072 and plan["claim_limits"] == CLAIM_LIMITS, "bounds changed")
    base.require(isinstance(plan["device"], str) and
                 re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", plan["device"]) and
                 type(plan["lease_end"]) is float and math.isfinite(plan["lease_end"]), "device/lease changed")
    base.require(plan["model_files"] == base.model_hashes(plan["model"]), "model hashes changed")
    base.require(plan["adapter_files"] == (base.tree_hashes(plan["adapter"]) if plan["adapter"] else {}),
                 "adapter hashes changed")
    base.require(plan["identity"] == base.expected_identity(plan, plan["adapter"]), "identity changed")
    base.require(plan["native_inputs"] == native_inputs(base.native_tokenizer(plan["model"]), plan["requests"]),
                 "prepared native rendering/tokens changed")
    return plan, cases


def capture(plan, path, factory=None, closer=None):
    if closer is None:
        from .model_backend import close_backend
        closer = close_backend
    factory = factory or base.NativeBackend
    backend = None
    path = Path(path)
    (path / "calls").mkdir()
    try:
        backend = factory(plan["model"], plan["adapter"])
        identity = plan["identity"]
        base.require(backend.identity() == identity, "native identity differs")
        base.write_json(path / "identity.json", dict(backend=identity, model_files=plan["model_files"],
                                                   adapter_files=plan["adapter_files"]))
        base.write_json(path / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
        for request, native in zip(plan["requests"], plan["native_inputs"], strict=True):
            base.require(backend.identity() == identity, "native identity changed")
            stem = path / "calls" / request["call_id"]
            base.write_json(str(stem) + ".request.json", dict(request=request, started=time.monotonic(),
                            identity=identity, prompt_sha256=base.value_hash(request["prompt"])))
            response = backend.generate(request)
            base.write_json(str(stem) + ".response.json", dict(response=response, ended=time.monotonic(),
                            response_sha256=base.value_hash(response)))
            base.validate_response(request, response)
            base.require(all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")),
                         "native input differs from prepared input")
        base.write_json(path / "usage.json", base.usage(path))
    except BaseException as error:
        base.write_json(path / "failure.json", dict(type=type(error).__name__, error=str(error)))
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
    parent_pid = os.getppid()
    base.require(parent_pid > 1, "live supervisor parent required")
    plan, _ = verify(root)
    base.require(base.supervisor.selected_device() == plan["device"], "worker device differs")
    receipt = root / "run" / "worker" / "process.json"
    until = time.monotonic() + 5
    while not receipt.exists() and time.monotonic() < until:
        time.sleep(.05)
    base.require(base.read(receipt)["pid"] == os.getpid() == os.getpgrp() and os.getppid() == parent_pid,
                 "supervisor ownership required")
    deadline = time.monotonic() + WORKER_SECONDS
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
    base.require(allow_gpu, "Main must allocate the device and explicitly pass --allow-gpu")
    root = Path(root).resolve()
    plan, _ = verify(root)
    stage = base.fresh_directory(root / "run", plan["model"])
    command = [sys.executable, "-B", "-m", "organism_v6.fundamental_teaching_readout", "_worker",
               "--root", str(root), "--allow-gpu"]
    return base.supervise(root, plan, stage / "worker", command, stage / "data" / "calls")


def reduce(root):
    root = Path(root).resolve()
    plan, cases = verify(root)
    path = root / "run" / "data"
    supervision = base.read(root / "run" / "worker" / "supervision.json")
    base.require(supervision["ok"] is True and supervision["reservation_release_verified"] is True and
                 supervision["owned_group_empty"] is True and supervision["gpu_processes_absent"] is True and
                 supervision["returncode"] == 0 and supervision["device"] == plan["device"],
                 "unverified supervision/cleanup")
    base.require(base.read(path / "manifest.json")["files"] == base.tree_hashes(path, ("manifest.json",)),
                 "capture changed")
    base.require(not (path / "failure.json").exists() and
                 base.read(path / "backend.cleanup.json")["closed"] is True, "backend failed or cleanup unverified")
    expected_files = {request["call_id"] + suffix for request in plan["requests"]
                      for suffix in (".request.json", ".response.json")}
    base.require({item.name for item in (path / "calls").iterdir()} == expected_files,
                 "all 48 request/response pairs required; missing artifacts are not zeros")
    identity = plan["identity"]
    base.require(base.read(path / "identity.json") == dict(backend=identity, model_files=plan["model_files"],
                 adapter_files=plan["adapter_files"]), "capture identity changed")
    rows, last_ended = [], 0.0
    for request, case in zip(plan["requests"], cases, strict=True):
        stem = path / "calls" / request["call_id"]
        sent, received = base.read(str(stem) + ".request.json"), base.read(str(stem) + ".response.json")
        response = received["response"]
        base.require(sent["request"] == request and sent["identity"] == identity and
                     sent["prompt_sha256"] == base.value_hash(request["prompt"]) and
                     received["response_sha256"] == base.value_hash(response), "raw receipt binding changed")
        base.require(math.isfinite(sent["started"]) and math.isfinite(received["ended"]) and
                     last_ended <= sent["started"] <= received["ended"], "call timing differs")
        last_ended = received["ended"]
        base.validate_response(request, response)
        score = (score_addition if case["kind"] == "addition" else score_memory)(response["text"], case["expected"])
        rows.append(dict(call_id=request["call_id"], case_id=case["id"], kind=case["kind"], **score))
    base.audit_native_calls(base.native_tokenizer(plan["model"]), path)
    cost = base.usage(path)
    base.require(cost == base.read(path / "usage.json"), "usage receipt changed")
    addition = [row for row in rows if row["kind"] == "addition"]
    memory = [row for row in rows if row["kind"] == "memory_recall"]
    base.require(len(rows) == 48 and len(addition) == 32 and len(memory) == 16, "incomplete 48-case readout")
    counts = dict(total=48, addition=dict(total=32, correct_action=sum(row["correct_action"] for row in addition),
                  invalid_action=sum(not row["action_valid"] for row in addition),
                  adherence=sum(row["adherence"] for row in addition)),
                  memory=dict(total=16, correct=sum(row["correct"] for row in memory),
                              invalid=sum(not row["valid"] for row in memory)))
    result = dict(complete=True, counts=counts, rows=rows, cost=cost, identity=identity,
                  model_files=plan["model_files"], adapter_files=plan["adapter_files"],
                  plan_sha256=base.digest(root / "plan.json"), capture_sha256=base.digest(path / "manifest.json"),
                  source_hashes=plan["source_hashes"], native_token_text_audit=True,
                  reserved_seconds=supervision["reserved_seconds"], output_token_ceiling=3072,
                  claim_limits=CLAIM_LIMITS, monetary_cost=None,
                  monetary_cost_note="No billing-rate evidence; actual native tokens and elapsed seconds recorded.")
    base.write_json(root / "reduction.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "reduce", "_worker"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--adapter", type=Path, default=None)
    parser.add_argument("--device", default="0")
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.stage == "prepare":
        base.require(args.out is not None and args.model is not None and args.lease_end is not None,
                     "--out, --model, --lease-end (Unix seconds) required")
        result = prepare(args.out, args.model, args.adapter, args.device, args.lease_end)
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
