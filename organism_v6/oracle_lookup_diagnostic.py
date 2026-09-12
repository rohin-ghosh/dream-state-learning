"""Development-only irrelevant-table lookup diagnostic; 64 new inference calls.

Replay the frozen full-table calibration baseline, then supply one authentic
key-selected table row. Not W0 rescue, qualification, training, persistence,
parenting evidence or clean ancestry. Local pins do not authenticate origin.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from . import writer_interface_calibration as cal
from . import multikey_writer_gateway_simple as w0


MAX_REQUESTS = 64
MAX_SECONDS = 3600
BOUNDARY = dict(label="DEVELOPMENT_ORACLE_LOOKUP_DIAGNOSTIC", evidence_label="EVALUATION_ONLY",
    clean_lineage=False, training=False, adapters=False, parent_passed=False,
    official_model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY",
    scope="irrelevant-table retrieval diagnostic only; no qualification or persistent learning")


def _sources():
    return dict(module_sha256=w0.file_hash(__file__), calibration=cal._sources())


def calibration_source(root):
    """Replay in the real producer checkout when unchanged helpers relocate."""
    spec = w0.load_json(root / "manifest.json")
    original = spec["sources"]
    current = cal._sources()
    suffixes = ("organism_v6/writer_interface_calibration.py",
                "organism_v6/multikey_writer_gateway_simple.py",
                "tests/test_writer_interface_calibration.py")
    w0.require(len(original["files"]) == len(current["files"]) == 3
               and original["strict_parser_sha256"] == current["strict_parser_sha256"], "calibration producer source shape")
    producer_roots = set()
    for suffix in suffixes:
        old = [(path, digest) for path, digest in original["files"].items() if path.endswith("/" + suffix)]
        new = [(path, digest) for path, digest in current["files"].items() if path.endswith("/" + suffix)]
        w0.require(len(old) == len(new) == 1 and old[0][1] == new[0][1]
                   and w0.file_hash(old[0][0]) == old[0][1]
                   and w0.file_hash(new[0][0]) == new[0][1], "original/imported calibration producer bytes differ")
        producer_roots.add(str(Path(old[0][0]).parents[1]))
    w0.require(len(producer_roots) == 1, "one retained producer checkout required")
    if original == current:
        cal.replay(root)
        return cal.validate_prepared(root)
    producer_root = producer_roots.pop()
    completed = subprocess.run([sys.executable, "-B", "-m", "organism_v6.writer_interface_calibration",
        "replay", "--run", str(root)], cwd=producer_root,
        env=dict(os.environ, PYTHONPATH=producer_root, PYTHONDONTWRITEBYTECODE="1",
                 HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1"),
        capture_output=True, text=True, check=True, timeout=60)
    w0.require(json.loads(completed.stdout) == w0.load_json(root / "report.json"), "original producer replay report mismatch")
    parent, material, requests, receipt = cal.inspect_failed_parent(spec["parent_root"], spec["parent_seal_sha256"])
    w0.require(parent["config"] == spec["config"] and receipt == w0.load_json(root / "parent_source.json"),
               "failed parent source changed")
    return spec, material, requests


def source(calibration, seal_sha256):
    root = w0.checked_path(calibration)
    w0.require(w0.file_hash(root / "CALIBRATION_SEAL.json") == seal_sha256, "calibration seal pin mismatch")
    spec, material, parent_requests = calibration_source(root)
    requests = w0.load_json(root / "requests.json")
    baseline = [request for request in requests if request["condition"] == "chat_explicit_32"]
    w0.require(len(baseline) == 64, "exact frozen baseline required")
    records = [w0.load_json(root / (request["request_id"] + ".json")) for request in baseline]
    return spec, material, parent_requests, requests, records


def build_requests(material, calibration_requests, tokenizer):
    """Select first held key prospectively, never consulting generated outcomes."""
    baselines = [request for request in calibration_requests if request["condition"] == "chat_explicit_32"]
    expected_order = []
    for root_index, root in enumerate(material["roots"]):
        first = {}
        for index, row in enumerate(root["held"]):
            first.setdefault((row["slot"], row["mode"]), index)
        w0.require(len(first) == 16, "complete tool/mode keys required")
        expected_order.extend((root_index, mapping, index) for mapping in w0.MAPS for index in first.values())
    w0.require([(row["root"], row["mapping"], row["held_index"]) for row in baselines] == expected_order
               and len(baselines) == 64, "fixed ordered 64 calibration inputs required")
    result = []
    for baseline in baselines:
        root = material["roots"][baseline["root"]]
        row = root["held"][baseline["held_index"]]
        original = w0.oracle_prompt(root, baseline["mapping"], row["context"])
        w0.require(baseline["prompt"] == cal.INSTRUCTION + "\n" + original
                   and baseline["tool"] == root["tools"][row["slot"]] and baseline["mode"] == row["mode"]
                   and baseline["expected"] == w0.action(baseline["root"], row["slot"], row["mode"], baseline["mapping"]),
                   "baseline context/key/target mismatch")
        table, context = original.split("\nTask:\n", 1)
        prefix = f"{root['tools'][row['slot']]} m{row['mode']} -> "
        selected = [line for line in table.splitlines()[1:] if line.startswith(prefix)]
        w0.require(len(selected) == 1, "unique authentic key-selected row required")
        prompt = cal.INSTRUCTION + "\nExplicit action table:\n" + selected[0] + "\nTask:\n" + context
        rendered = tokenizer.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                          tokenize=False, add_generation_prompt=True)
        ids = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)["input_ids"]
        w0.require(isinstance(rendered, str) and isinstance(ids, list) and ids
                   and all(type(token) is int and token >= 0 for token in ids) and len(ids) + 32 <= 2048,
                   "bounded actual token IDs required")
        request = dict(pair_id=baseline["pair_id"], baseline_request_id=baseline["request_id"],
            root=baseline["root"], mapping=baseline["mapping"], held_index=baseline["held_index"],
            tool=baseline["tool"], mode=baseline["mode"], expected=baseline["expected"],
            selected_row=selected[0], context=context, condition="single_row_chat_explicit_32",
            prompt=prompt, rendered_prompt=rendered, prompt_input_ids=ids,
            max_new_tokens=32, do_sample=False, seed=0)
        result.append(dict(request_id=w0.digest(request), **request))
    return result


def reduce_records(requests, records, baseline_records):
    w0.require(len(requests) == len(records) == len(baseline_records) == 64, "incomplete paired diagnostic")
    actual = {record["request_id"]: record for record in records}
    baseline = {record["request_id"]: record for record in baseline_records}
    w0.require(len(actual) == len(baseline) == 64
               and set(actual) == {row["request_id"] for row in requests}
               and set(baseline) == {row["baseline_request_id"] for row in requests}, "duplicate/missing paired output")
    cells, pairs = {}, {}
    for request in requests:
        paired = {}
        for condition, record in (("full_table_replayed", baseline[request["baseline_request_id"]]),
                                  ("single_row", actual[request["request_id"]])):
            w0.require(type(record["truncated"]) is bool and isinstance(record["text"], str), "typed actual output required")
            parsed = w0.parse_output(record["text"], record["truncated"])
            outcome = dict(correct=parsed["action"] == request["expected"], valid=parsed["action"] is not None,
                           truncated=record["truncated"], multiple=parsed["multiple_ACT"])
            cell = cells.setdefault(f"{request['root']}/{request['mapping']}/{condition}",
                                    dict(total=0, correct=0, valid=0, truncated=0, multiple=0))
            cell["total"] += 1
            for name, value in outcome.items():
                cell[name] += int(value)
            paired[condition] = dict(request_id=record["request_id"], **outcome)
        pairs[request["pair_id"]] = paired
    w0.require(len(cells) == 8 and all(cell["total"] == 16 for cell in cells.values()) and len(pairs) == 64,
               "fixed paired denominators")
    return dict(**BOUNDARY, new_inference_requests=64, replayed_baselines=64,
                cells=cells, paired_prompt_ids=pairs)


def prepare(out, *, calibration, calibration_seal_sha256, log_dir, deadline_unix, gpu_uuid):
    parent_spec, material, parent_requests, calibration_requests, baseline = source(calibration, calibration_seal_sha256)
    config = dict(parent_spec["config"], gpu_uuid=gpu_uuid)
    w0.require(type(deadline_unix) in (int, float) and math.isfinite(deadline_unix)
               and time.time() < deadline_unix <= config["lease_cutoff_unix"], "prospective deadline within lease required")
    protected = [calibration, parent_spec["parent_root"], config["model_path"], config["tokenizer_path"],
                 parent_spec["log_dir"], *config["protected"].values()]
    root = cal._separate(out, protected)
    logs = cal._separate(log_dir, [root, *protected])
    w0.require(root.parent.is_dir() and logs.parent.is_dir() and not root.exists() and not logs.exists(),
               "fresh output/log directories required")
    pins, sources = w0.pin_local_inputs(config), _sources()
    w0.require(pins == parent_spec["input_pins"], "calibrated local model/tokenizer/environment pins required")
    tokenizer = w0.load_local_tokenizer(config)
    w0.require(cal.build_requests(material, parent_requests, tokenizer) == calibration_requests, "calibration tokenizer drift")
    requests = build_requests(material, calibration_requests, tokenizer)
    source(calibration, calibration_seal_sha256)
    w0.require(w0.pin_local_inputs(config) == pins and sources == _sources(), "prepare input/source drift")
    root.mkdir()
    logs.mkdir()
    for name, value in (("requests.json", requests), ("baseline_records.json", baseline)):
        w0.write_once(root, name, value)
    spec = dict(version="oracle-lookup-diagnostic-v1", **BOUNDARY, output_root=str(root), log_dir=str(logs),
        calibration_root=str(w0.checked_path(calibration)), calibration_seal_sha256=calibration_seal_sha256,
        failed_w0_root=parent_spec["parent_root"], config=config, input_pins=pins, sources=sources,
        deadline_unix=deadline_unix, max_requests=MAX_REQUESTS, max_seconds=MAX_SECONDS,
        artifacts={name: w0.file_hash(root / name) for name in ("requests.json", "baseline_records.json")})
    w0.write_once(root, "manifest.json", spec)
    w0.write_once(root, "PREPARED.json", dict(**BOUNDARY, manifest_sha256=w0.digest(spec), model_loaded=False))
    return dict(status="PREPARED_DEVELOPMENT_ONLY", **BOUNDARY)


def validate(root):
    root = w0.checked_path(root)
    spec = w0.load_json(root / "manifest.json")
    w0.require(w0.load_json(root / "PREPARED.json")["manifest_sha256"] == w0.digest(spec)
               and spec["output_root"] == str(root) and spec["sources"] == _sources(), "manifest/source drift")
    w0.require(all(spec.get(key) == value for key, value in BOUNDARY.items())
               and spec["max_requests"] == 64 and spec["max_seconds"] == 3600, "diagnostic bounds changed")
    w0.require(set(spec["artifacts"]) == {"requests.json", "baseline_records.json"}
               and all(w0.file_hash(root / name) == digest for name, digest in spec["artifacts"].items()), "artifact drift")
    parent, material, parent_requests, calibration_requests, baseline = source(spec["calibration_root"], spec["calibration_seal_sha256"])
    w0.require(spec["config"] == dict(parent["config"], gpu_uuid=spec["config"]["gpu_uuid"])
               and spec["failed_w0_root"] == parent["parent_root"] and spec["input_pins"] == parent["input_pins"]
               and baseline == w0.load_json(root / "baseline_records.json"), "calibrated source binding changed")
    protected = [spec["calibration_root"], parent["parent_root"], parent["log_dir"], spec["config"]["model_path"],
                 spec["config"]["tokenizer_path"], *spec["config"]["protected"].values()]
    cal._separate(root, protected)
    cal._separate(spec["log_dir"], [root, *protected])
    return spec, material, parent_requests, calibration_requests


def worker(root, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required")
    root = w0.checked_path(root)
    spec, material, parent_requests, calibration_requests = validate(root)
    started = w0.load_json(root / "STARTED.json")
    w0.require(started["manifest_sha256"] == w0.digest(spec)
               and started["deadline_unix"] <= min(started["wall_start"] + MAX_SECONDS,
                   spec["deadline_unix"], spec["config"]["lease_cutoff_unix"]), "worker startup/deadline binding")
    w0.assert_output_fds_outside_run(root)
    w0.write_once(root, "WORKER_CLAIMED.json", dict(pid=os.getpid()))
    w0.require(w0.pin_local_inputs(spec["config"]) == spec["input_pins"], "worker local input drift")
    w0.gpu_identity(spec["config"])
    tokenizer = w0.load_local_tokenizer(spec["config"])
    w0.require(cal.build_requests(material, parent_requests, tokenizer) == calibration_requests, "baseline tokenizer drift")
    requests = build_requests(material, calibration_requests, tokenizer)
    w0.require(requests == w0.load_json(root / "requests.json"), "lookup tokenizer/request drift")
    torch = w0.configure_torch(spec["config"], 0)
    w0.require(time.time() < started["deadline_unix"] - 5, "deadline before model load")
    model = w0.load_hf_model(spec["config"], torch)
    model.eval()
    model.requires_grad_(False)
    w0.require(not model.training and not any(parameter.requires_grad for parameter in model.parameters()), "no gradients permitted")
    records = []
    for request in requests:
        w0.require(time.time() < started["deadline_unix"] - 5, "request deadline exhausted")
        record = cal._generate(torch, model, tokenizer, request)
        w0.write_once(root, request["request_id"] + ".json", record)
        records.append(record)
    w0.require(w0.pin_local_inputs(spec["config"]) == spec["input_pins"], "inputs changed during inference")
    validate(root)
    w0.write_once(root, "report.json", reduce_records(requests, records, w0.load_json(root / "baseline_records.json")))


def replay(root):
    root = w0.checked_path(root)
    spec, _, _, _ = validate(root)
    seal = w0.load_json(root / "LOOKUP_SEAL.json")
    inventory = cal._inventory(root)
    del inventory["LOOKUP_SEAL.json"]
    w0.require(inventory == seal["files"], "lookup inventory changed")
    resource = w0.load_json(root / "RESOURCE.json")
    w0.require(resource["GPU_count"] == 1 and 0 <= resource["elapsed_seconds"] <= 3600
               and resource["log_path"] == str(Path(spec["log_dir"]) / "worker.log")
               and w0.file_hash(resource["log_path"]) == resource["log_sha256"], "resource/log drift")
    requests = w0.load_json(root / "requests.json")
    report = reduce_records(requests, [w0.load_json(root / (row["request_id"] + ".json")) for row in requests],
                            w0.load_json(root / "baseline_records.json"))
    w0.require(report == w0.load_json(root / "report.json"), "report mismatch")
    return report


def execute(root, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required")
    begin, wall_start = time.monotonic(), time.time()
    root = w0.checked_path(root)
    spec, _, _, _ = validate(root)
    for path in (root, spec["calibration_root"], spec["failed_w0_root"]):
        w0.assert_output_fds_outside_run(path)
    w0.require(set(cal._inventory(root)) == {"manifest.json", "PREPARED.json", "requests.json", "baseline_records.json"},
               "fresh prepared diagnostic only; no retries")
    deadline = min(wall_start + 3600, spec["deadline_unix"], spec["config"]["lease_cutoff_unix"])
    w0.require(deadline > time.time() + 10, "execution deadline expired")
    w0.require(w0.pin_local_inputs(spec["config"]) == spec["input_pins"], "execution input drift")
    hardware = w0.gpu_identity(spec["config"])
    w0.assert_gpu_idle(spec["config"])
    w0.write_once(root, "STARTED.json", dict(manifest_sha256=w0.digest(spec), wall_start=wall_start, deadline_unix=deadline))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=spec["config"]["gpu_uuid"],
        CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false")
    command = [sys.executable, "-B", "-m", "organism_v6.oracle_lookup_diagnostic", "_worker", "--run", str(root), "--allow-gpu"]
    log_path = Path(spec["log_dir"]) / "worker.log"
    try:
        with log_path.open("xb") as log:
            process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], env=environment,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                remaining = min(3600 - (time.monotonic() - begin), deadline - time.time()) - 5
                w0.require(remaining > 0, "hard cap exhausted")
                returncode = process.wait(timeout=remaining)
            except BaseException:
                w0.stop_owned_process(process)
                raise
        w0.require(returncode == 0, "lookup worker failed; no retry")
        validate(root)
        elapsed = time.monotonic() - begin
        w0.require(elapsed <= 3600 and time.time() <= deadline, "one A40-hour/deadline cap")
        w0.write_once(root, "RESOURCE.json", dict(**BOUNDARY, GPU_count=1, elapsed_seconds=elapsed,
            hardware=hardware, deadline_unix=deadline, log_path=str(log_path), log_sha256=w0.file_hash(log_path)))
        w0.write_once(root, "LOOKUP_SEAL.json", dict(**BOUNDARY, files=cal._inventory(root)))
        return replay(root)
    except BaseException as error:
        w0.write_once(root, "FAILED.json", dict(**BOUNDARY, error_type=type(error).__name__, error=str(error)))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("out", "calibration", "calibration-seal-sha256", "log-dir", "gpu-uuid"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--deadline-unix", type=float, required=True)
    for name in ("execute", "_worker", "replay"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name != "replay":
            command.add_argument("--allow-gpu", action="store_true")
    args = vars(parser.parse_args(argv))
    operation = args.pop("command")
    if operation == "prepare":
        result = prepare(**args)
    elif operation == "replay":
        result = replay(args["run"])
    else:
        result = (execute if operation == "execute" else worker)(args["run"], args["allow_gpu"])
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
