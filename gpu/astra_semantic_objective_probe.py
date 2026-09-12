"""Paired root1 W+ objective diagnostic; prepare on CPU, Main explicitly launches.

Only the response label mask differs between two fresh seed-1 fits. Neither held
queries nor Q0 gate replacement are supported. The native supervisor's owned
process-group cleanup limitations still apply; this is not a cgroup guard.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from organism_v6 import semantic_writer_diagnostic as diagnostic
from organism_v6 import run_reasoning_neutral as supervisor


VERSION = "semantic-objective-probe-20260912-v1"
ORIGINAL_MANIFEST = "f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830"
ORIGINAL_SEAL = "71f164765d1cdfeef96b881da6eac68de05f1921989f1b167f7dff7b6f088d71"
ARMS = ("full_response", "first_choice")
STAGES = ("generate_OFF", "fit_full_response", "fit_first_choice",
          "generate_full_response", "generate_first_choice")
SCOPE = "root1 W+ exact128; two fresh seed1 fits256; mask-only contrast; OFF+two postfit greedy128; no held or gate rescue"
ROWS, STEPS, MAX_SECONDS, WORKER_SECONDS, CLEANUP_RESERVE = 128, 256, 1800, 900, 45
LIMITS = dict(fits=2, optimizer_steps=512, training_forwards=512, generations=384,
              decision_prefix_forwards=384, max_new_tokens=32, max_seconds=MAX_SECONDS)
require = diagnostic.w0.require
read = diagnostic.read_json
digest = diagnostic.w0.digest
file_hash = diagnostic.w0.file_hash
write = diagnostic.w0.write_once


def source_pins():
    paths = [Path(__file__), Path(__file__).resolve().parents[1] / "tests/test_semantic_objective_probe.py",
             Path(supervisor.__file__)]
    return {**diagnostic.sources(), **{str(path.resolve()): file_hash(path) for path in paths}}


def verify_original(original):
    original = Path(original).resolve(strict=True)
    require(file_hash(original / "manifest.json") == ORIGINAL_MANIFEST
            and file_hash(original / "SEAL.json") == ORIGINAL_SEAL, "fixed original manifest/seal required")
    manifest, seal = read(original / "manifest.json"), read(original / "SEAL.json")
    require(manifest["output_root"] == str(original) and not (original / "FAILED.json").exists(),
            "original terminal root required")
    for name, expected in manifest["sources"].items():
        require(file_hash(name) == expected, "original source changed")
    for name in ("fits.json", "material.json"):
        require(file_hash(original / name) == manifest["artifacts"][name] == seal["files"][name],
                "original training artifact changed")
    require(manifest["recipe"] == diagnostic.w0.EXECUTION_RECIPE, "original recipe changed")
    require(diagnostic.pin_inputs(manifest["config"]) == manifest["input_pins"], "base/environment drift")
    return manifest, read(original / "fits.json")["r1_plus"], read(original / "material.json")["roots"][1]["train"]["W+"]


def build_rows(fit, material, tokenizer):
    require(fit["root"] == 1 and fit["mapping"] == "W+" and fit["seed"] == 1
            and fit["recipe"] == diagnostic.w0.EXECUTION_RECIPE and len(fit["rows"]) == ROWS,
            "exact root1 W+ seed1 recipe/rows required")
    require(len(material) == ROWS and Counter((row["slot"], row["mode"], row["template"]) for row in material)
            == Counter((slot, mode, template) for slot in range(8) for mode in range(2) for template in range(8)),
            "exact 8x2x8 training grid required")
    rows, prefixes = [], set()
    for index, (saved, item) in enumerate(zip(fit["rows"], material)):
        payload = diagnostic.render(tokenizer, item["context"])
        require(saved["order"] == index and saved["payload"] == payload, "original row order/prompt tokens changed")
        prefix = payload["prompt_input_ids"]
        require(tuple(prefix) not in prefixes, "duplicate training prefix")
        prefixes.add(tuple(prefix))
        target = diagnostic.w0.action(1, item["slot"], item["mode"], "W+")
        require(item["target"] == target and saved["target"] == diagnostic.carrier.CANDIDATES[target], "target changed")
        candidates = [diagnostic.carrier.encode_candidate(tokenizer, payload["rendered_prompt"], prefix, text)
                      for text in diagnostic.carrier.CANDIDATES]
        encoded, other = candidates[target], candidates[1 - target]
        require(saved["encoded"] == encoded, "native original target encoding changed")
        position = next((index for index, pair in enumerate(zip(encoded["input_ids"], other["input_ids"]))
                         if pair[0] != pair[1]), None)
        require(position is not None and position == len(prefix) + 3, "native first-choice token/shift changed")
        require(encoded["labels"] == [-100] * len(prefix) + encoded["response_ids"], "full response mask changed")
        decision_labels = [-100] * len(encoded["input_ids"])
        decision_labels[position] = encoded["input_ids"][position]
        require(sum(label != -100 for label in decision_labels[1:]) == 1 and position > 0,
                "exactly one shifted decision target required")
        hashes = dict(source_row=digest(saved), payload=digest(payload), encoded=digest(encoded),
                      full_labels=digest(encoded["labels"]), decision_labels=digest(decision_labels))
        rows.append(dict(order=index, audit={key: item[key] for key in ("slot", "mode", "template", "target")},
                         payload=payload, encoded=encoded, decision_labels=decision_labels, hashes=hashes,
                         decision_position=position, logit_position=position - 1,
                         gold_token=encoded["input_ids"][position], other_token=other["input_ids"][position]))
    require(Counter(row["audit"]["target"] for row in rows) == {0: 64, 1: 64}, "balanced labels required")
    return rows


def runtime_config(config, gpu_uuid):
    require(isinstance(gpu_uuid, str) and re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", gpu_uuid), "reserved GPU UUID required")
    result = copy.deepcopy(config)
    result["gpu_uuid"] = gpu_uuid
    return result


def separate_output(out, original, config):
    out = Path(out).resolve()
    protected = [Path(original).resolve(), Path(__file__).resolve().parents[1],
                 *[Path(config[key]).resolve() for key in ("model_path", "tokenizer_path", "protocol_path", "carrier_proof_path")],
                 *[Path(path).resolve() for path in config["protected_paths"]]]
    require(all(not out.is_relative_to(path) and not path.is_relative_to(out) for path in protected),
            "separate unprotected output root required")
    return out


def prepare(original, out, gpu_uuid, approved_intake, builder_preflight_reference):
    require(all(isinstance(value, str) and value.strip() for value in (approved_intake, builder_preflight_reference)),
            "explicit intake and Builder reference required")
    sources = source_pins()
    manifest, fit, material = verify_original(original)
    config = runtime_config(manifest["config"], gpu_uuid)
    out = separate_output(out, original, config)
    require(not out.exists(), "fresh output root required")
    rows = build_rows(fit, material, diagnostic.w0.load_local_tokenizer(config))
    require(sources == source_pins(), "source changed during native preflight")
    out.mkdir(parents=True, exist_ok=False)
    write(out, "rows.json", rows)
    prepared = dict(version=VERSION, status="NATIVE_CPU_PREFLIGHT_NO_MODEL_OR_GPU", original=str(Path(original).resolve()),
                    out=str(out), original_manifest_sha256=ORIGINAL_MANIFEST, original_seal_sha256=ORIGINAL_SEAL,
                    original_fits_sha256=manifest["artifacts"]["fits.json"], sources=sources,
                    original_config=manifest["config"], runtime_config=config, rows_sha256=file_hash(out / "rows.json"),
                    approved_intake=approved_intake, builder_preflight_reference=builder_preflight_reference,
                    requested_scope=SCOPE, recipe=diagnostic.w0.EXECUTION_RECIPE, stages=list(STAGES),
                    limits=LIMITS,
                    mask_shift_verified_rows=ROWS, row_hashes=[row["hashes"] for row in rows])
    write(out, "PREPARED.json", prepared)
    return prepared


def verify_prepared(out):
    out = Path(out).resolve(strict=True)
    prepared = read(out / "PREPARED.json")
    require(prepared["version"] == VERSION and prepared["sources"] == source_pins()
            and prepared["out"] == str(out), "prepared source/path changed")
    require(prepared["requested_scope"] == SCOPE and prepared["stages"] == list(STAGES)
            and prepared["recipe"] == diagnostic.w0.EXECUTION_RECIPE and prepared["limits"] == LIMITS
            and prepared["mask_shift_verified_rows"] == ROWS, "prepared scope/recipe changed")
    manifest, fit, material = verify_original(prepared["original"])
    config = runtime_config(manifest["config"], prepared["runtime_config"]["gpu_uuid"])
    require(config == prepared["runtime_config"] and manifest["config"] == prepared["original_config"]
            and prepared["original_manifest_sha256"] == ORIGINAL_MANIFEST and prepared["original_seal_sha256"] == ORIGINAL_SEAL
            and prepared["original_fits_sha256"] == manifest["artifacts"]["fits.json"], "only runtime GPU may differ")
    separate_output(out, prepared["original"], config)
    tokenizer = diagnostic.w0.load_local_tokenizer(config)
    rows = build_rows(fit, material, tokenizer)
    require(file_hash(out / "rows.json") == prepared["rows_sha256"] and read(out / "rows.json") == rows
            and prepared["row_hashes"] == [row["hashes"] for row in rows], "native row/mask/hash drift")
    return out, prepared, rows, tokenizer


def labels_for(row, arm):
    require(arm in ARMS, "unknown objective")
    return row["encoded"]["labels"] if arm == "full_response" else row["decision_labels"]


def forward_metrics(torch, output, row):
    positions = [index for index, label in enumerate(row["encoded"]["labels"]) if label != -100]
    with torch.no_grad():
        logits = output.logits[0, [index - 1 for index in positions]].detach().float()
        logprob = torch.log_softmax(logits, dim=-1)
        losses = -logprob[torch.arange(len(positions), device=logprob.device),
                          torch.tensor([row["encoded"]["input_ids"][index] for index in positions], device=logprob.device)]
        decision = positions.index(row["decision_position"])
        decision_ce = float(losses[decision].cpu())
        result = dict(decision_ce=decision_ce, full_response_ce=float(losses.mean().cpu()),
                      nondecision_nll=float((losses.sum() - losses[decision]).cpu()),
                      nondecision_tokens=len(positions) - 1,
                      gold_vs_other_margin=float((logits[decision, row["gold_token"]] - logits[decision, row["other_token"]]).cpu()))
    require(all(math.isfinite(value) for value in result.values()), "nonfinite training-forward metrics")
    return result


def numerical_snapshot(torch, trainables, optimizer, before):
    inventory = dict(adapter=Counter(), gradient=Counter(), optimizer={})
    groups = defaultdict(lambda: dict(parameter_squared=0., gradient_squared=0., update_squared=0., tensors=0))
    for name, parameter in trainables:
        require(parameter.grad is not None, "missing diagnostic gradient")
        inventory["adapter"][str(parameter.dtype)] += 1
        inventory["gradient"][str(parameter.grad.dtype)] += 1
        require(parameter in optimizer.state and optimizer.state[parameter], "missing Adam state")
        for field, value in optimizer.state[parameter].items():
            counts = inventory["optimizer"].setdefault(field, Counter())
            counts[str(value.dtype) if torch.is_tensor(value) else type(value).__name__] += 1
        projection = name.split(".lora_")[0].rsplit(".", 1)[-1]
        group = groups[projection]
        group["tensors"] += 1
        group["parameter_squared"] += float(parameter.detach().float().square().sum().cpu())
        group["gradient_squared"] += float(parameter.grad.detach().float().square().sum().cpu())
        group["update_squared"] += float((parameter.detach().float() - before[name]).square().sum().cpu())
    norms = {name: dict(tensors=group["tensors"], **{key.replace("_squared", "_l2"): math.sqrt(value)
             for key, value in group.items() if key != "tensors"}) for name, group in groups.items()}
    require(all(math.isfinite(value) for group in norms.values() for value in group.values()), "nonfinite norms")
    return dict(dtypes=inventory, norms_by_projection=norms)


def training_step(torch, model, optimizer, row, arm, capture_norms=False):
    ids = torch.tensor([row["encoded"]["input_ids"]], dtype=torch.long, device="cuda:0")
    labels = torch.tensor([labels_for(row, arm)], dtype=torch.long, device="cuda:0")
    output = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=labels, use_cache=False)
    require(torch.isfinite(output.loss).item(), "nonfinite training loss")
    metrics = forward_metrics(torch, output, row)
    loss = float(output.loss.detach().cpu())
    expected = metrics["full_response_ce"] if arm == "full_response" else metrics["decision_ce"]
    require(math.isclose(loss, expected, rel_tol=1e-5, abs_tol=1e-6), "native shifted loss/forward parity failed")
    optimizer.zero_grad(set_to_none=True)
    output.loss.backward()
    trainables = diagnostic.w0.validate_trainables(model)
    require(all(parameter.grad is not None and torch.isfinite(parameter.grad).all().item()
                for _, parameter in trainables), "nonfinite/missing gradient")
    before = {name: parameter.detach().float().clone() for name, parameter in trainables} if capture_norms else None
    optimizer.step()
    require(all(torch.isfinite(parameter).all().item() for _, parameter in trainables), "nonfinite adapter update")
    if capture_norms:
        metrics["numerics"] = numerical_snapshot(torch, trainables, optimizer, before)
    torch.cuda.synchronize()
    return dict(loss=loss, **metrics)


def train(torch, model, optimizer, rows, arm, directory, deadline):
    require(len(rows) == ROWS and [row["order"] for row in rows] == list(range(ROWS)), "fixed training rows/order")
    total = 0.
    with (directory / "steps.jsonl").open("xb") as stream:
        for index in range(STEPS):
            require(time.time() < deadline - 5, "training deadline")
            row = rows[index % ROWS]
            result = training_step(torch, model, optimizer, row, arm, index in (0, STEPS - 1))
            total += result["loss"]
            stream.write(diagnostic.w0.canonical(dict(step=index + 1, epoch=index // ROWS, row=row["order"],
                         source_row_sha256=row["hashes"]["source_row"], **result)))
            stream.flush()
    return dict(optimizer_steps=STEPS, training_forwards=STEPS, mean_loss=total / STEPS,
                steps_sha256=file_hash(directory / "steps.jsonl"))


def generation_request(row, state):
    body = dict(namespace=VERSION, state=state, operation="generate", candidates=[],
                audit=dict(family="exact_train", index=row["order"], **row["audit"]),
                source_row_sha256=row["hashes"]["source_row"], payload=dict(row["payload"], seed=1))
    return dict(request_id=digest(body), **body)


def eval_margin(torch, model, row):
    prefix = row["encoded"]["input_ids"][:row["decision_position"]]
    ids = torch.tensor([prefix], dtype=torch.long, device="cuda:0")
    with torch.inference_mode():
        logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits[0, -1].float()
        margin = float((logits[row["gold_token"]] - logits[row["other_token"]]).cpu())
    require(math.isfinite(margin), "nonfinite dropout-off decision margin")
    return margin


def generate(torch, model, tokenizer, rows, state, directory, deadline):
    require(len(rows) == ROWS and state in ("OFF", *ARMS), "fixed generation rows/state")
    generated_tokens = 0
    with (directory / "records.jsonl").open("xb") as stream:
        for row in rows:
            require(time.time() < deadline - 5, "generation deadline")
            request = generation_request(row, state)
            margin = eval_margin(torch, model, row)
            require(time.time() < deadline - 5, "deadline before greedy generation")
            output = diagnostic.cal._generate(torch, model, tokenizer, dict(request["payload"], request_id=request["request_id"]))
            parsed = diagnostic.generation(request, output, tokenizer)
            generated_tokens += len(output["generated_ids"])
            record = dict(request_id=request["request_id"], request_sha256=digest(request), state=state,
                          row=row["order"], source_row_sha256=row["hashes"]["source_row"], attempts=1,
                          gold_vs_other_margin=margin, output=output, parsed=parsed)
            stream.write(diagnostic.w0.canonical(record))
            stream.flush()
    return dict(count=len(rows), decision_prefix_forwards=len(rows), generated_tokens=generated_tokens,
                records_sha256=file_hash(directory / "records.jsonl"))


def verify_job(out, stage):
    require(stage in STAGES, "unknown worker stage")
    started = read(out / "STARTED.json")
    job = read(out / (stage + ".job.json"))
    require(started["prepared_sha256"] == file_hash(out / "PREPARED.json")
            and job["started_sha256"] == file_hash(out / "STARTED.json") and job["stage"] == stage,
            "worker job binding changed")
    require(0 < started["deadline"] - started["started"] <= MAX_SECONDS
            and job["deadline"] <= started["deadline"] - CLEANUP_RESERVE
            and time.time() < job["deadline"] - 5, "worker deadline invalid")
    parent = diagnostic.carrier.process_identity(os.getppid())
    require(parent["pid"] == job["controller"]["pid"] and parent["start_ticks"] == job["controller"]["start_ticks"],
            "worker must have registered controller parent")
    for previous in STAGES[:STAGES.index(stage)]:
        require((out / "stages" / previous / "DONE.json").is_file(), "previous stage incomplete")
    return job


def worker(out, stage, *, allow_gpu=False):
    require(allow_gpu is True, "explicit --allow-gpu required")
    out = Path(out).resolve(strict=True)
    job = verify_job(out, stage)
    out, prepared, rows, tokenizer = verify_prepared(out)
    require(time.time() < job["deadline"] - 5, "deadline before model load")
    config = prepared["runtime_config"]
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"], "reserved GPU mismatch")
    require(job["deadline"] <= config["lease_cutoff_unix"], "lease cutoff")
    directory = out / "stages" / stage
    directory.mkdir(exist_ok=False)
    hardware = diagnostic.w0.gpu_identity(config)
    torch = diagnostic.w0.configure_torch(config, 1)
    operation, state = stage.split("_", 1)
    common = dict(stage=stage, state=state, seed=1, hardware=hardware, sources=prepared["sources"],
                  runtime_config_sha256=digest(config), rows_sha256=prepared["rows_sha256"],
                  job_sha256=file_hash(out / (stage + ".job.json")), identity=diagnostic.carrier.process_identity(os.getpid()))
    if operation == "fit":
        model, optimizer, initial = diagnostic.fit_model(torch, config)
        initial_sha = diagnostic.w0.tensor_digest(initial)
        initial_dtypes = dict(Counter(str(parameter.dtype) for _, parameter in diagnostic.w0.validate_trainables(model)))
        if state == "first_choice":
            control = read(out / "stages/fit_full_response/LOAD.json")
            require(control["initial_lora_sha256"] == initial_sha and control["adapter_dtypes"] == initial_dtypes,
                    "paired initialization/dtypes differ")
        write(directory, "LOAD.json", dict(**common, training=True, initial_lora_sha256=initial_sha, adapter_dtypes=initial_dtypes))
        result = train(torch, model, optimizer, rows, state, directory, job["deadline"])
        final = diagnostic.w0.lora_tensors(model)
        update = math.sqrt(sum(float((final[name] - initial[name]).square().sum()) for name in initial))
        require(math.isfinite(update) and update > 0 and time.time() < job["deadline"] - 5, "nonzero update/save deadline")
        path = directory / "adapter"
        path.mkdir()
        model.save_pretrained(str(path), safe_serialization=True)
        result.update(initial_lora_sha256=initial_sha, final_lora_sha256=diagnostic.w0.tensor_digest(final),
                      adapter_sha256=diagnostic.w0.tree_hash(path), update_norm=update)
    else:
        fitted = read(out / "stages" / ("fit_" + state) / "DONE.json")["result"] if state != "OFF" else {}
        adapter_sha, lora_sha = fitted.get("adapter_sha256", "OFF"), fitted.get("final_lora_sha256", "OFF")
        model = diagnostic.load_eval_model(config, torch, out, state, adapter_sha, lora_sha)
        write(directory, "LOAD.json", dict(**common, training=False, adapter_sha256=adapter_sha, lora_sha256=lora_sha))
        result = generate(torch, model, tokenizer, rows, state, directory, job["deadline"])
    require(time.time() < job["deadline"] and source_pins() == prepared["sources"], "worker completion deadline/source drift")
    write(directory, "DONE.json", dict(**common, result=result, finished=time.time()))


def reduce(out, prepared, rows, tokenizer):
    summaries, fits = {}, {}
    identities = set()
    actual_cost = dict(training_forwards=0, optimizer_steps=0, generation_requests=0,
                       decision_prefix_forwards=0, generated_tokens=0)
    numerics = {}
    for stage in STAGES:
        directory = out / "stages" / stage
        done, load = read(directory / "DONE.json"), read(directory / "LOAD.json")
        require(done["stage"] == stage and done["sources"] == prepared["sources"]
                and done["rows_sha256"] == prepared["rows_sha256"], "stage evidence drift")
        identity = (done["identity"]["pid"], done["identity"]["start_ticks"])
        require(identity not in identities and load["identity"] == done["identity"], "fresh process per stage required")
        identities.add(identity)
        result = done["result"]
        operation, state = stage.split("_", 1)
        if operation == "fit":
            require(result["optimizer_steps"] == result["training_forwards"] == STEPS
                    and file_hash(directory / "steps.jsonl") == result["steps_sha256"]
                    and diagnostic.w0.tree_hash(directory / "adapter") == result["adapter_sha256"], "fit evidence drift")
            steps = [json.loads(line) for line in (directory / "steps.jsonl").read_text().splitlines()]
            require(len(steps) == STEPS and all(step["step"] == index + 1 and step["epoch"] == index // ROWS
                    and step["row"] == index % ROWS and step["source_row_sha256"] == rows[index % ROWS]["hashes"]["source_row"]
                    for index, step in enumerate(steps)), "exact 256 step trajectory required")
            require(all("numerics" in steps[index] for index in (0, STEPS - 1)), "first/last numerics missing")
            numerics[state] = [steps[index]["numerics"] for index in (0, STEPS - 1)]
            actual_cost["training_forwards"] += result["training_forwards"]
            actual_cost["optimizer_steps"] += result["optimizer_steps"]
            fits[state] = result
            continue
        require(result["count"] == ROWS and file_hash(directory / "records.jsonl") == result["records_sha256"], "generation evidence drift")
        expected_adapter = fits[state]["adapter_sha256"] if state != "OFF" else "OFF"
        expected_lora = fits[state]["final_lora_sha256"] if state != "OFF" else "OFF"
        require(load["adapter_sha256"] == expected_adapter and load["lora_sha256"] == expected_lora, "fresh evaluation adapter identity")
        records = [json.loads(line) for line in (directory / "records.jsonl").read_text().splitlines()]
        require(len(records) == ROWS, "exact generation denominator")
        require(result["decision_prefix_forwards"] == ROWS
                and result["generated_tokens"] == sum(len(record["output"]["generated_ids"]) for record in records),
                "actual generation/prefix cost mismatch")
        actual_cost["generation_requests"] += len(records)
        actual_cost["decision_prefix_forwards"] += result["decision_prefix_forwards"]
        actual_cost["generated_tokens"] += result["generated_tokens"]
        details = []
        for row, record in zip(rows, records):
            request = generation_request(row, state)
            require(record["row"] == row["order"] and record["state"] == state and record["attempts"] == 1
                    and record["request_id"] == request["request_id"] and record["request_sha256"] == digest(request)
                    and record["source_row_sha256"] == row["hashes"]["source_row"]
                    and math.isfinite(record["gold_vs_other_margin"]), "generation row/margin binding")
            parsed = diagnostic.generation(request, record["output"], tokenizer)
            require(parsed == record["parsed"], "generation parse drift")
            details.append(dict(row=row["order"], **row["audit"], action=parsed["action"],
                                correct=parsed["action"] == diagnostic.carrier.ACTIONS[row["audit"]["target"]],
                                valid=parsed["action"] is not None, gold_vs_other_margin=record["gold_vs_other_margin"]))
        summaries[state] = dict(n=ROWS, correct=sum(item["correct"] for item in details),
                               valid=sum(item["valid"] for item in details), action_counts=dict(Counter(str(item["action"]) for item in details)),
                               key_modes=[dict(slot=slot, mode=mode, n=8, correct=sum(item["correct"] for item in details
                                   if (item["slot"], item["mode"]) == (slot, mode))) for slot in range(8) for mode in range(2)],
                               templates=[dict(template=template, n=16, correct=sum(item["correct"] for item in details
                                   if item["template"] == template)) for template in range(8)], details=details)
    require(fits[ARMS[0]]["initial_lora_sha256"] == fits[ARMS[1]]["initial_lora_sha256"], "paired initialization changed")
    require(all(numerics[ARMS[0]][index]["dtypes"] == numerics[ARMS[1]][index]["dtypes"] for index in (0, 1)),
            "paired gradient/optimizer dtypes differ")
    return dict(version=VERSION, status="SUPPLEMENTARY_OBJECTIVE_DIAGNOSTIC_ONLY", fits=fits, states=summaries,
                optimizer_steps=512, generation_requests=384, decision_prefix_forwards=384, held_queries=0,
                actual_cost=actual_cost, first_last_numerics=numerics,
                gate_evaluation="none; original Q0 unchanged", requested_scope=SCOPE,
                interpretation="Conditional key-mode binding, not global action bias or format improvement; no automatic followup.")


def execute(out, timeout_seconds=MAX_SECONDS, *, allow_gpu=False):
    require(allow_gpu is True, "explicit --allow-gpu required")
    require(type(timeout_seconds) is int and 60 <= timeout_seconds <= MAX_SECONDS, "60..1800 second cap required")
    started = time.time()
    out = Path(out).resolve(strict=True)
    require(not any((out / name).exists() for name in ("STARTED.json", "FAILED.json", "COMPLETED.json")), "no retry/resume")
    out, prepared, rows, tokenizer = verify_prepared(out)
    config = prepared["runtime_config"]
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"], "Main reserved GPU required")
    deadline = min(started + timeout_seconds, config["lease_cutoff_unix"])
    require(time.time() < deadline - CLEANUP_RESERVE - 5, "execution deadline before launch")
    out.joinpath("stages").mkdir(exist_ok=False)
    write(out, "STARTED.json", dict(started=started, deadline=deadline, prepared_sha256=file_hash(out / "PREPARED.json"),
                                   controller=diagnostic.carrier.process_identity(os.getpid())))
    try:
        for stage in STAGES:
            remaining = deadline - time.time() - CLEANUP_RESERVE
            require(remaining > 5, "deadline before next worker")
            worker_deadline = min(time.time() + WORKER_SECONDS, deadline - CLEANUP_RESERVE)
            timeout = worker_deadline - time.time()
            write(out, stage + ".job.json", dict(stage=stage, deadline=worker_deadline,
                  started_sha256=file_hash(out / "STARTED.json"), controller=diagnostic.carrier.process_identity(os.getpid())))
            supervisor.run_worker([sys.executable, "-B", "-m", "gpu.astra_semantic_objective_probe", "worker", "--out", str(out),
                                  "--stage", stage, "--allow-gpu"], log_path=out / (stage + ".log"), timeout=timeout, device=config["gpu_uuid"])
            cleanup = read(out / (stage + ".cleanup.json"))
            require(cleanup["owned_group_empty"] and cleanup["gpu_processes_absent"], "cleanup unverified")
        report = reduce(out, prepared, rows, tokenizer)
        require(time.time() < deadline and prepared["sources"] == source_pins(), "overall completion deadline/source drift")
        report.update(prepared_sha256=file_hash(out / "PREPARED.json"), elapsed_seconds=time.time() - started)
        write(out, "report.json", report)
        write(out, "COMPLETED.json", dict(status=report["status"], report_sha256=file_hash(out / "report.json"), finished=time.time()))
        return report
    except BaseException as error:
        write(out, "FAILED.json", dict(error_type=type(error).__name__, error=str(error), preserve_attempt=True, automatic_retry=False))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "execute", "worker"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--original")
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--approved-intake")
    parser.add_argument("--builder-preflight-reference")
    parser.add_argument("--timeout-seconds", type=int, default=MAX_SECONDS)
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        require(args.original and args.gpu_uuid, "original/GPU required")
        result = prepare(args.original, args.out, args.gpu_uuid, args.approved_intake, args.builder_preflight_reference)
    elif args.command == "execute":
        result = execute(args.out, args.timeout_seconds, allow_gpu=args.allow_gpu)
    else:
        result = worker(args.out, args.stage, allow_gpu=args.allow_gpu)
    if result is not None:
        print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
