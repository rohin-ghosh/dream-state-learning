"""Separate 16-case training-prompt memory diagnostic; no fitting or dev changes."""
from __future__ import annotations

import argparse
from collections import Counter
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
from . import fundamental_teaching_readout as readout


base = readout.base
capture = readout.capture
native_inputs = readout.native_inputs
score_memory = readout.score_memory
CASE_IDS = tuple(f"train-memory-{index:03d}" for index in range(16))
LABEL = "IN_SAMPLE_TRAINING_PROMPT_DIAGNOSTIC_NOT_HELDOUT"
SEED = 20260912
MAX_TOKENS = 64
WORKER_SECONDS = 600
CLAIM_LIMITS = (
    "In-sample original training contexts only, not heldout, confirmation, or a replacement "
    "for the fixed 48-case development endpoint. No new training or reminders. This "
    "diagnostic separates training-prompt recall from paraphrase performance; it does not "
    "prove a unique mechanism, internalization, parenting efficacy, or H1/H2. Local hashes "
    "bind loader inputs, not base origin or training history. Missing artifacts are not zeros."
)


def selected_cases():
    candidate = corpus.build_candidate()
    events = candidate["source_records"]
    sources_by_id = {event["id"]: event for event in events}
    base.require(len(sources_by_id) == len(events), "duplicate source IDs")
    arms = {}
    for arm in ("teach", "control"):
        rows = [row for row in candidate[f"train_{arm}"] if row["kind"] == "memory"]
        indexed = {row["case_id"]: row for row in rows}
        base.require(len(rows) == len(indexed) == 16 and set(indexed) == set(CASE_IDS),
                     "exactly 16 original memory training cases required per arm")
        arms[arm] = indexed
    cases = []
    for index, case_id in enumerate(CASE_IDS):
        teach, control = (arms[arm][case_id] for arm in ("teach", "control"))
        device, source_id = f"device-{index:03d}", f"source-memory-{index:03d}"
        source = sources_by_id[source_id]
        base.require(source["kind"] == "device_color" and source["device"] == device and
                     source["color"] in corpus.COLORS, "source color/device binding differs")
        for arm, row in (("teach", teach), ("control", control)):
            base.require(row["id"] == f"{case_id}-{arm}" and row["device"] == device and
                         row["source_event_ids"] == [source_id] and row["response"] == source["color"] and
                         row["context"] == f"Which color does the log assign to {device}?",
                         "original memory context/target/source binding differs")
        cases.append(dict(id=case_id, kind="memory", device=device, context=teach["context"],
                          expected=source["color"], source_event_ids=[source_id], source_record=source,
                          training_record_ids=[teach["id"], control["id"]]))
    return cases


def requests(cases):
    base.require(cases == selected_cases(), "fixed training-prompt selection differs")
    return [dict(call_id=f"{index:04d}", case_id=case["id"], role="memory_diagnostic", arm="readout",
                 prompt=case["context"], temperature=0.0, seed=SEED, max_tokens=MAX_TOKENS)
            for index, case in enumerate(cases)]


def sources():
    return dict(readout.sources(), fundamental_memory_diagnostic=base.digest(Path(__file__)))


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
    plan = dict(schema=1, label=LABEL, model=model, adapter=adapter, device=device, lease_end=end,
                model_files=base.model_hashes(model), adapter_files=base.tree_hashes(adapter) if adapter else {},
                cases=cases, requests=fixed, source_hashes=sources(),
                corpus_sha256=base.value_hash(corpus.build_candidate()),
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
    base.require(plan["source_hashes"] == sources() and
                 plan["corpus_sha256"] == base.value_hash(corpus.build_candidate()), "source/corpus hashes changed")
    base.require(plan["cases"] == cases and plan["requests"] == requests(cases), "fixed cases/requests changed")
    base.require(plan["schema"] == 1 and plan["label"] == LABEL and plan["claim_limits"] == CLAIM_LIMITS and
                 plan["worker_seconds"] == WORKER_SECONDS == base.WORKER_SECONDS and
                 plan["output_token_ceiling"] == 1024 and readout.MAX_TOKENS == MAX_TOKENS,
                 "diagnostic bounds changed")
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


def worker_command(root):
    return [sys.executable, "-B", "-m", "organism_v6.fundamental_memory_diagnostic", "_worker",
            "--root", str(Path(root).resolve()), "--allow-gpu"]


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
    process = base.read(receipt)
    base.require(process["pid"] == process["pgid"] == os.getpid() == os.getpgrp() and
                 process["argv"] == worker_command(root) and process["device"] == plan["device"] and
                 os.getppid() == parent_pid, "supervisor ownership required")
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
    return base.supervise(root, plan, stage / "worker", worker_command(root), stage / "data" / "calls")


def reduce(root):
    root = Path(root).resolve()
    plan, cases = verify(root)
    path, stage = root / "run" / "data", root / "run" / "worker"
    supervision, process = base.read(stage / "supervision.json"), base.read(stage / "process.json")
    base.require(all(supervision[field] is True for field in (
        "ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
        supervision["returncode"] == 0 and supervision["device"] == plan["device"], "unverified supervision/cleanup")
    reserved, started = supervision["reserved_seconds"], process["started"]
    base.require(math.isfinite(reserved) and reserved > 0 and math.isfinite(started) and started >= 0 and
                 type(process["pid"]) is int and process["pid"] > 1 and process["pgid"] == process["pid"] and
                 process["argv"] == worker_command(root) and process["device"] == plan["device"] and
                 math.isfinite(process["timeout"]) and 0 < process["timeout"] <= WORKER_SECONDS,
                 "invalid worker custody")
    base.require(base.read(path / "manifest.json")["files"] == base.tree_hashes(path, ("manifest.json",)),
                 "capture changed")
    base.require(not (path / "failure.json").exists() and
                 base.read(path / "backend.cleanup.json")["closed"] is True, "backend failed or cleanup unverified")
    ready = base.read(path / "backend.ready.json")
    base.require(ready["pid"] == process["pid"] and math.isfinite(ready["ready"]) and
                 started <= ready["ready"] <= started + reserved, "backend custody differs")
    expected_files = {request["call_id"] + suffix for request in plan["requests"]
                      for suffix in (".request.json", ".response.json")}
    base.require({item.name for item in (path / "calls").iterdir()} == expected_files,
                 "all 16 request/response pairs required; missing artifacts are not zeros")
    identity = plan["identity"]
    base.require(base.read(path / "identity.json") == dict(backend=identity, model_files=plan["model_files"],
                 adapter_files=plan["adapter_files"]), "capture identity changed")
    rows, last_ended = [], ready["ready"]
    for request, case, native in zip(plan["requests"], cases, plan["native_inputs"], strict=True):
        stem = path / "calls" / request["call_id"]
        sent, received = base.read(str(stem) + ".request.json"), base.read(str(stem) + ".response.json")
        response = received["response"]
        base.require(sent["request"] == request and sent["identity"] == identity and
                     sent["prompt_sha256"] == base.value_hash(request["prompt"]) and
                     received["response_sha256"] == base.value_hash(response), "raw receipt binding changed")
        base.require(math.isfinite(sent["started"]) and math.isfinite(received["ended"]) and
                     last_ended <= sent["started"] <= received["ended"] <= started + reserved,
                     "call timing differs")
        last_ended = received["ended"]
        base.validate_response(request, response)
        base.require(all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")),
                     "native input differs from prepared input")
        rows.append(dict(call_id=request["call_id"], case_id=case["id"], device=case["device"],
                         source_event_ids=case["source_event_ids"], **score_memory(response["text"], case["expected"])))
    base.audit_native_calls(base.native_tokenizer(plan["model"]), path)
    cost = base.usage(path)
    base.require(cost == base.read(path / "usage.json"), "usage receipt changed")
    base.require(len(rows) == 16, "incomplete 16-case diagnostic")
    counts = dict(total=16, correct=sum(row["correct"] for row in rows), invalid=sum(not row["valid"] for row in rows),
                  answer_counts=dict(Counter(row["answer"] for row in rows if row["valid"])))
    result = dict(complete=True, label=LABEL, counts=counts, rows=rows, cost=cost, identity=identity,
                  model_files=plan["model_files"], adapter_files=plan["adapter_files"],
                  plan_sha256=base.digest(root / "plan.json"), capture_sha256=base.digest(path / "manifest.json"),
                  supervision_sha256=base.digest(stage / "supervision.json"),
                  process_sha256=base.digest(stage / "process.json"), source_hashes=plan["source_hashes"],
                  corpus_sha256=plan["corpus_sha256"], native_token_text_audit=True,
                  reserved_seconds=reserved, output_token_ceiling=1024, claim_limits=CLAIM_LIMITS,
                  monetary_cost=None, monetary_cost_note="No billing-rate evidence; actual native tokens and seconds recorded.")
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
