"""Inference-only supplementary exact-training-row probes of sealed Q0 adapters."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time

from gpu import astra_semantic_rescore as rescore
from organism_v6 import semantic_writer_diagnostic as diagnostic
from organism_v6 import run_reasoning_neutral as supervisor


VERSION = "semantic-exact-train-probe-20260912-v1"
ORIGINAL_SEAL_SHA256 = "71f164765d1cdfeef96b881da6eac68de05f1921989f1b167f7dff7b6f088d71"
MAX_SECONDS = 3600
WORKER_SECONDS = 900
ROWS = 128
require = diagnostic.w0.require
read = diagnostic.read_json
file_hash = diagnostic.w0.file_hash
write = diagnostic.w0.write_once
digest = diagnostic.w0.digest


def states_for(root_index):
    require(type(root_index) is int and root_index in (0, 1), "root index must be 0 or 1")
    return ["OFF", f"r{root_index}_plus", f"r{root_index}_minus"]


def runtime_config(config, gpu_uuid):
    require(isinstance(gpu_uuid, str) and re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", gpu_uuid),
            "explicit reserved GPU UUID required")
    result = copy.deepcopy(config)
    result["gpu_uuid"] = gpu_uuid
    return result


def source_pins():
    paths = [Path(__file__), Path(__file__).resolve().parents[1] / "tests/test_semantic_train_probe.py"]
    return {**rescore.source_pins(), **{str(path.resolve()): file_hash(path) for path in paths}}


def sealed_read(original, seal, relative):
    require(relative in seal["files"] and file_hash(original / relative) == seal["files"][relative],
            "original sealed artifact changed: " + relative)
    return read(original / relative)


def verify_original(original, root_index):
    states = states_for(root_index)
    original = Path(original).resolve(strict=True)
    manifest, held_requests = rescore.verify_original(original)
    require(file_hash(original / "SEAL.json") == ORIGINAL_SEAL_SHA256, "fixed original terminal seal required")
    seal = read(original / "SEAL.json")
    fits = sealed_read(original, seal, "fits.json")
    material = sealed_read(original, seal, "material.json")
    report = sealed_read(original, seal, "report.json")
    adapters = {"OFF": dict(adapter_sha256="OFF", lora_sha256=None)}
    for state in states[1:]:
        fitted = sealed_read(original, seal, f"stages/fit_{state}/DONE.json")["result"]
        path = original / "stages" / ("fit_" + state) / "adapter"
        require(diagnostic.w0.tree_hash(path) == fitted["adapter_sha256"], "original adapter tree changed")
        adapters[state] = dict(adapter_sha256=fitted["adapter_sha256"], lora_sha256=fitted["final_lora_sha256"])
    return dict(manifest=manifest, held_requests=held_requests, seal=seal, fits=fits,
                material=material, original_report=report, adapters=adapters)


def build_requests(fits, material, root_index, fits_sha256):
    states = states_for(root_index)
    mappings = {"W+": states[1], "W-": states[2]}
    for mapping, state in mappings.items():
        require(fits[state]["root"] == root_index and fits[state]["mapping"] == mapping
                and len(fits[state]["rows"]) == ROWS, "exact original fit rows required")
        rows = material["roots"][root_index]["train"][mapping]
        require(len(rows) == ROWS and Counter((row["slot"], row["mode"], row["template"]) for row in rows)
                == Counter((slot, mode, template) for slot in range(8) for mode in range(2) for template in range(8)),
                "all 128 training forms exactly once")
    requests, prefixes = [], set()
    for index in range(ROWS):
        saved = {mapping: fits[state]["rows"][index] for mapping, state in mappings.items()}
        rows = {mapping: material["roots"][root_index]["train"][mapping][index] for mapping in mappings}
        payload = saved["W+"]["payload"]
        require(saved["W-"]["payload"] == payload and payload["max_new_tokens"] == 32
                and payload["do_sample"] is False, "exact common recorded greedy payload")
        prefix = payload["prompt_input_ids"]
        require(prefix and all(type(token) is int and token >= 0 for token in prefix)
                and tuple(prefix) not in prefixes, "unique exact recorded token prefixes")
        prefixes.add(tuple(prefix))
        targets, candidates = {}, [None, None]
        for mapping, row in rows.items():
            recorded = saved[mapping]
            require(recorded["order"] == index and row["context"] == payload["prompt"]
                    and all(row[key] == rows["W+"][key] for key in ("slot", "mode", "template")),
                    "fit/material row join")
            target = row["target"]
            require(type(target) is int and target in (0, 1), "binary recorded target")
            encoded = recorded["encoded"]
            response = encoded["response_ids"]
            require(recorded["target"] == encoded["text"] == diagnostic.carrier.CANDIDATES[target]
                    and response and all(type(token) is int and token >= 0 for token in response)
                    and encoded["input_ids"] == prefix + response
                    and encoded["labels"] == [-100] * len(prefix) + response,
                    "exact recorded candidate encoding and labels")
            targets[mapping] = target
            candidates[target] = copy.deepcopy(encoded)
        require(targets["W+"] != targets["W-"] and all(candidate is not None for candidate in candidates),
                "complementary recorded targets required")
        eos = candidates[0]["response_ids"][-1]
        require(all(candidate["response_ids"][-1] == eos and eos not in candidate["response_ids"][:-1]
                    for candidate in candidates), "recorded terminal EOS")
        source = dict(file="fits.json", file_sha256=fits_sha256, row_index=index,
            rows={state: dict(pointer=f"/{state}/rows/{index}", sha256=digest(saved[mapping]))
                  for mapping, state in mappings.items()},
            candidate_source_states=[mappings[next(mapping for mapping, target in targets.items() if target == choice)]
                                     for choice in (0, 1)], payload_sha256=digest(payload))
        for state in states:
            for operation in ("generate", "score"):
                body = dict(namespace=VERSION, state=state, operation=operation,
                    audit=dict(owner_root=root_index, probe_root=root_index, family="exact_train", index=index,
                               slot=rows["W+"]["slot"], mode=rows["W+"]["mode"], template=rows["W+"]["template"],
                               targets=targets), source=source, payload=dict(copy.deepcopy(payload), seed=0),
                    candidates=copy.deepcopy(candidates) if operation == "score" else [])
                requests.append(dict(request_id=digest(body), **body))
    require(len(requests) == len({row["request_id"] for row in requests}) == 768,
            "384 generation and 384 scoring requests per root")
    return requests


def verify_probe(out):
    out = Path(out).resolve(strict=True)
    probe = read(out / "probe.json")
    require(probe["version"] == VERSION and probe["sources"] == source_pins(), "probe source changed")
    require(probe["states"] == states_for(probe["root_index"]), "probe state/root mismatch")
    require(60 <= probe["timeout_seconds"] <= MAX_SECONDS
            and probe["deadline"] == probe["started"] + probe["timeout_seconds"], "bounded probe deadline")
    original = Path(probe["original"])
    evidence = verify_original(original, probe["root_index"])
    require(probe["original_manifest_sha256"] == rescore.ORIGINAL_MANIFEST_SHA256
            and probe["original_seal_sha256"] == ORIGINAL_SEAL_SHA256
            and probe["original_report_sha256"] == evidence["seal"]["files"]["report.json"]
            and probe["new_fits"] == 0, "probe original evidence pins changed")
    config = runtime_config(evidence["manifest"]["config"], probe["runtime_gpu_uuid"])
    require(probe["runtime_config"] == config and probe["runtime_config_sha256"] == digest(config)
            and probe["original_gpu_uuid"] == evidence["manifest"]["config"]["gpu_uuid"], "only GPU UUID may change")
    requests = build_requests(evidence["fits"], evidence["material"], probe["root_index"],
                              evidence["manifest"]["artifacts"]["fits.json"])
    require(file_hash(out / "requests.json") == probe["requests_sha256"]
            and read(out / "requests.json") == requests and probe["adapters"] == evidence["adapters"],
            "probe request/adapter drift")
    return out, probe, evidence, requests


def worker(out, state, *, allow_gpu=False):
    require(allow_gpu is True, "explicit --allow-gpu required")
    out, probe, evidence, requests = verify_probe(out)
    require(state in probe["states"] and time.time() < probe["deadline"] - 5, "valid root state/deadline required")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == probe["runtime_gpu_uuid"], "reserved runtime GPU mismatch")
    directory = out / state
    directory.mkdir(exist_ok=False)
    config = probe["runtime_config"]
    hardware = diagnostic.w0.gpu_identity(config)
    torch = diagnostic.w0.configure_torch(config, 0)
    tokenizer = diagnostic.w0.load_local_tokenizer(config)
    adapter = evidence["adapters"][state]
    model = diagnostic.load_eval_model(config, torch, Path(probe["original"]), state,
                                       adapter["adapter_sha256"], adapter["lora_sha256"])
    write(directory, "LOAD.json", dict(state=state, root_index=probe["root_index"], **adapter,
        original_gpu_uuid=probe["original_gpu_uuid"], runtime_gpu_uuid=probe["runtime_gpu_uuid"], hardware=hardware,
        runtime_config_sha256=digest(config), dtype=str(next(model.parameters()).dtype), training=False, new_fits=0))
    selected = [request for request in requests if request["state"] == state]
    require(len(selected) == 256, "128 generation and scoring pairs per state")
    with (directory / "records.jsonl").open("x") as stream:
        for request in selected:
            require(time.time() < probe["deadline"] - 5, "probe deadline")
            prefix = request["payload"]["prompt_input_ids"]
            require(tokenizer.decode(prefix) == request["payload"]["rendered_prompt"], "recorded prefix decode changed")
            for candidate in request["candidates"]:
                require(candidate["response_ids"][-1] == tokenizer.eos_token_id
                        and tokenizer.decode(candidate["response_ids"][:-1]) == candidate["text"], "recorded target decode changed")
            torch.manual_seed(0)
            torch.cuda.manual_seed_all(0)
            started = time.monotonic()
            if request["operation"] == "generate":
                output = diagnostic.cal._generate(torch, model, tokenizer,
                    dict(request["payload"], request_id=request["request_id"]))
                diagnostic.generation(request, output, tokenizer)
            else:
                output = diagnostic.carrier.score(torch, model, request)
                diagnostic.score_sums(request, output)
            torch.cuda.synchronize()
            stream.write(json.dumps(dict(request_id=request["request_id"], request_sha256=digest(request),
                state=state, operation=request["operation"], root_index=probe["root_index"], **adapter,
                attempts=1, seconds=time.monotonic() - started, output=output), sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    verify_probe(out)
    require(time.time() < probe["deadline"], "worker completed after deadline")
    write(directory, "DONE.json", dict(state=state, root_index=probe["root_index"], count=256,
        records_sha256=file_hash(directory / "records.jsonl"), finished=time.time()))


def held_generation_summary(original, evidence, root_index, tokenizer):
    states = states_for(root_index)
    result = {}
    for state in states:
        selected = [request for request in evidence["held_requests"] if request["state"] == state
                    and request["operation"] == "generate" and request["audit"]["probe_root"] == root_index
                    and request["audit"]["family"] == "primary"]
        require(len(selected) == 64 and {request["audit"]["index"] for request in selected} == set(range(64)),
                "all original held generations required")
        actions, targets = [], {mapping: [] for mapping in ("W+", "W-")}
        for request in selected:
            stage = "off_generate" if state == "OFF" else "eval_" + state + "_generate"
            raw = sealed_read(original, evidence["seal"], f"stages/{stage}/raw/{request['request_id']}.json")
            require(raw["request_id"] == request["request_id"] and raw["request_sha256"] == digest(request)
                    and raw["attempts"] == 1, "original held generation binding")
            action = diagnostic.generation(request, raw["output"], tokenizer)["action"]
            actions.append(diagnostic.carrier.ACTIONS.index(action) if action in diagnostic.carrier.ACTIONS else None)
            row = evidence["material"]["roots"][root_index]["held"][request["audit"]["index"]]
            for mapping in targets:
                targets[mapping].append(diagnostic.w0.action(root_index, row["slot"], row["mode"], mapping))
        result[state] = dict(n=64, validity=sum(action is not None for action in actions) / 64,
            by_mapping={mapping: dict(BA=diagnostic.w0.balanced_accuracy(actions, values)) for mapping, values in targets.items()})
    for mapping, state in zip(("W+", "W-"), states[1:]):
        cell = evidence["original_report"]["roots"][root_index]["cells"][mapping]
        require(result[state]["by_mapping"][mapping]["BA"] == cell["BA"]
                and result["OFF"]["by_mapping"][mapping]["BA"] == cell["BA"] - cell["OFF_gain"],
                "original held generation BA/report mismatch")
    return result


def reduce_records(requests, records, tokenizer, adapters, held):
    require(len(requests) == len(records) == 768, "complete exact-training denominator required")
    indexed = {row["request_id"]: row for row in records}
    require(len(indexed) == 768 and set(indexed) == {row["request_id"] for row in requests}, "duplicate/missing probe records")
    parsed, scores, audits = {}, {}, {}
    for request in requests:
        row = indexed[request["request_id"]]
        state, index = request["state"], request["audit"]["index"]
        require(row["request_sha256"] == digest(request) and row["state"] == state
                and row["operation"] == request["operation"] and row["root_index"] == request["audit"]["probe_root"]
                and row["attempts"] == 1 and math.isfinite(row["seconds"]) and row["seconds"] >= 0
                and all(row[key] == value for key, value in adapters[state].items()), "probe raw identity/adapter binding")
        audits[index] = request["audit"]
        if request["operation"] == "generate":
            parsed[state, index] = diagnostic.generation(request, row["output"], tokenizer)
        else:
            values = diagnostic.score_sums(request, row["output"])
            require(sum(math.exp(value) for value in values) <= 1 + 1e-6, "complete candidate mass exceeds one")
            scores[state, index] = values
    result = {}
    for state in adapters:
        actions = [parsed[state, index]["action"] for index in range(ROWS)]
        choices = [diagnostic.carrier.ACTIONS.index(action) if action in diagnostic.carrier.ACTIONS else None for action in actions]
        mapping_results = {}
        for mapping in ("W+", "W-"):
            targets = [audits[index]["targets"][mapping] for index in range(ROWS)]
            details = []
            for index, target in enumerate(targets):
                values, baseline = scores[state, index], scores["OFF", index]
                details.append(dict(index=index, slot=audits[index]["slot"], mode=audits[index]["mode"],
                    template=audits[index]["template"], target=target, generated_choice=choices[index],
                    correct=choices[index] == target, candidate_logprobs=values,
                    candidate_mass=sum(math.exp(value) for value in values),
                    score_choice=None if values[0] == values[1] else int(values[1] > values[0]),
                    target_logq=diagnostic.w0.log_q(values, target), target_logprob=values[target],
                    margin=values[target] - values[1 - target],
                    logq_gain_vs_off=diagnostic.w0.log_q(values, target) - diagnostic.w0.log_q(baseline, target),
                    target_logprob_gain_vs_off=values[target] - baseline[target]))
            metrics = {field: dict(mean=statistics.mean(row[field] for row in details),
                                  minimum=min(row[field] for row in details), maximum=max(row[field] for row in details))
                       for field in ("candidate_mass", "target_logq", "target_logprob", "margin",
                                     "logq_gain_vs_off", "target_logprob_gain_vs_off")}
            keys = []
            for slot in range(8):
                for mode in range(2):
                    group = [row for row in details if (row["slot"], row["mode"]) == (slot, mode)]
                    require(len(group) == 8, "all eight training forms per key")
                    keys.append(dict(slot=slot, mode=mode, n=8, generation_accuracy=sum(row["correct"] for row in group) / 8,
                        mean_target_logq=statistics.mean(row["target_logq"] for row in group),
                        mean_logq_gain_vs_off=statistics.mean(row["logq_gain_vs_off"] for row in group)))
            accuracy = sum(row["correct"] for row in details) / ROWS
            balanced = diagnostic.w0.balanced_accuracy(choices, targets)
            mapping_results[mapping] = dict(generation_accuracy=accuracy, generation_BA=balanced,
                score_accuracy=sum(row["score_choice"] == row["target"] for row in details) / ROWS,
                diagnostics=metrics, keys=keys, rows=details, original_held_generation_BA=held[state]["by_mapping"][mapping]["BA"],
                train_minus_original_held_BA=balanced - held[state]["by_mapping"][mapping]["BA"])
        result[state] = dict(n=ROWS, own_mapping=None if state == "OFF" else diagnostic.STATES[state][1],
            validity=sum(action is not None for action in choices) / ROWS,
            truncated=sum(parsed[state, index]["truncated"] for index in range(ROWS)),
            multiple_ACT=sum(parsed[state, index]["multiple_ACT"] for index in range(ROWS)), by_mapping=mapping_results)
    return dict(status="SUPPLEMENTARY_EXACT_TRAIN_DIAGNOSTIC_ONLY", new_fits=0, optimizer_steps=0,
        unique_training_contexts=128, generation_requests=384, scoring_requests=384, candidate_forwards=768,
        max_new_tokens=32, maximum_generated_tokens=384 * 32,
        states=result, original_held_generations=held,
        interpretation="Descriptive seen-key exact-training-form versus original held-form comparison; not retention, unseen-key generalization, independent-seed replication, or retrospective gate rescue.")


def collect_records(out, states):
    records = []
    for state in states:
        directory = out / state
        done = read(directory / "DONE.json")
        require(done["state"] == state and done["count"] == 256
                and done["records_sha256"] == file_hash(directory / "records.jsonl"), "state completion/records changed")
        rows = [json.loads(line) for line in (directory / "records.jsonl").read_text().splitlines()]
        require(len(rows) == 256, "complete state records required")
        records.extend(rows)
    return records


def execute(original, out, root_index, gpu_uuid, timeout_seconds=1800, *, allow_gpu=False):
    require(allow_gpu is True, "Main explicit --allow-gpu required")
    states = states_for(root_index)
    require(type(timeout_seconds) is int and 60 <= timeout_seconds <= MAX_SECONDS, "bounded timeout required")
    original, out = Path(original).resolve(strict=True), Path(out).absolute()
    require(out == out.resolve() and not out.exists(), "fresh canonical output directory required")
    evidence = verify_original(original, root_index)
    config = runtime_config(evidence["manifest"]["config"], gpu_uuid)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == gpu_uuid, "Main reserved runtime GPU required")
    protected = [original, Path(config["model_path"]).resolve(), Path(config["tokenizer_path"]).resolve(),
                 Path(__file__).resolve().parents[1]]
    require(all(not out.is_relative_to(path) and not path.is_relative_to(out) for path in protected), "separate output root required")
    requests = build_requests(evidence["fits"], evidence["material"], root_index,
                              evidence["manifest"]["artifacts"]["fits.json"])
    out.mkdir(parents=True, exist_ok=False)
    write(out, "requests.json", requests)
    started = time.time()
    write(out, "probe.json", dict(version=VERSION, status="SUPPLEMENT_NOT_REPLACEMENT", original=str(original),
        original_manifest_sha256=rescore.ORIGINAL_MANIFEST_SHA256, original_seal_sha256=ORIGINAL_SEAL_SHA256,
        original_report_sha256=evidence["seal"]["files"]["report.json"], root_index=root_index, states=states,
        sources=source_pins(), adapters=evidence["adapters"], requests_sha256=file_hash(out / "requests.json"),
        original_gpu_uuid=evidence["manifest"]["config"]["gpu_uuid"], runtime_gpu_uuid=gpu_uuid,
        runtime_config=config, runtime_config_sha256=digest(config), started=started,
        timeout_seconds=timeout_seconds, deadline=started + timeout_seconds, new_fits=0,
        runtime_note="Only the GPU UUID is copied into the original model/environment configuration. This probe has its own bounded deadline; original run deadlines and results are not changed."))
    try:
        for state in states:
            remaining = started + timeout_seconds - time.time() - 15
            require(remaining > 5, "probe deadline before state launch")
            supervisor.run_worker([sys.executable, "-B", "-m", "gpu.astra_semantic_train_probe", "--worker",
                "--out", str(out), "--state", state, "--allow-gpu"], log_path=out / (state + ".log"),
                timeout=min(WORKER_SECONDS, remaining), device=gpu_uuid)
        out, probe, evidence, requests = verify_probe(out)
        tokenizer = diagnostic.w0.load_local_tokenizer(config)
        held = held_generation_summary(original, evidence, root_index, tokenizer)
        report = reduce_records(requests, collect_records(out, states), tokenizer, evidence["adapters"], held)
        report.update(root_index=root_index, original_label=evidence["original_report"]["label"],
            original_gates=copy.deepcopy(evidence["original_report"]["gates"]),
            original_report_sha256=probe["original_report_sha256"], gate_evaluation="not rerun or replaced")
        require(time.time() < probe["deadline"] and source_pins() == probe["sources"], "completion deadline/source changed")
        write(out, "supplementary_report.json", report)
        write(out, "COMPLETED.json", dict(status=report["status"], root_index=root_index, new_fits=0,
            generation_requests=384, scoring_requests=384, finished=time.time(),
            report_sha256=file_hash(out / "supplementary_report.json")))
    except BaseException as error:
        write(out, "FAILED.json", dict(error_type=type(error).__name__, error=str(error), preserve_attempt=True))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original")
    parser.add_argument("--out", required=True)
    parser.add_argument("--root-index", type=int, choices=(0, 1))
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--state", choices=["OFF", *diagnostic.STATES])
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.worker:
        worker(args.out, args.state, allow_gpu=args.allow_gpu)
    else:
        require(args.original and args.root_index is not None and args.gpu_uuid, "original/root/GPU required")
        execute(args.original, args.out, args.root_index, args.gpu_uuid, args.timeout_seconds, allow_gpu=args.allow_gpu)


if __name__ == "__main__":
    main()
