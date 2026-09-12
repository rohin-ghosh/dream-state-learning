"""Inference-only DEVELOPMENT_CALIBRATION, never W0 rescue or writing evidence.

Old held-out material becomes calibration material. No memory, behavior,
parenting, training or clean-lineage inference is supported. Only an explicitly
pinned failed W0 seal with exactly the declared empty-to-nonempty launcher.out
drift may be consumed. The parent is never modified, resealed or marked passed.
"""
from __future__ import annotations

import argparse
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from . import multikey_writer_gateway_simple as w0


LABEL = "DEVELOPMENT_CALIBRATION"
INSTRUCTION = "Reply with exactly one line: ACT: a0 or ACT: a1. Do not include explanations."
CONDITIONS = (("raw_original_32", False, False, 32),
              ("chat_original_32", True, False, 32),
              ("raw_explicit_32", False, True, 32),
              ("chat_explicit_32", True, True, 32),
              ("raw_original_256", False, False, 256))
BOUNDARY = dict(label=LABEL, evidence_label="EVALUATION_ONLY", evaluation_only=True, clean_lineage=False,
                training=False, adapters=False, parent_passed=False,
                official_model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY",
                scope="interface/truncation only; old held-out is calibration material")
MAX_REQUESTS = 320
MAX_SECONDS = 3600


def _inventory(root):
    root = w0.checked_path(root)
    found = {}
    for path in sorted(root.rglob("*")):
        w0.require(not path.is_symlink(), "inventory symlink")
        if path.is_dir():
            continue
        w0.require(path.is_file(), "nonregular inventory entry")
        found[path.relative_to(root).as_posix()] = w0.file_hash(path)
    return found


def _sources():
    paths = [Path(__file__), Path(w0.__file__),
             Path(__file__).resolve().parents[1] / "tests/test_writer_interface_calibration.py"]
    return dict(files={str(path.resolve()): w0.file_hash(path) for path in paths},
                strict_parser_sha256=w0.sha(inspect.getsource(w0.parse_output).encode()))


def inspect_failed_parent(parent, expected_seal_sha256):
    """Validate bytes, not scientific success; permit precisely one pinned defect."""
    root = w0.checked_path(parent)
    seal_path = root / "REAL_EXECUTION_SEAL.json"
    w0.require(w0.file_hash(seal_path) == expected_seal_sha256, "original failed seal pin mismatch")
    manifest = w0.validate_prepared(root, check_source=False)
    seal = w0.load_json(seal_path)
    w0.require(seal["version"] == w0.REAL_VERSION and seal["evidence"] == "REAL_GPU_EXECUTION",
               "expected original completed-execution seal, not parent success")
    current = _inventory(root)
    files = {name: digest for name, digest in current.items() if name != "REAL_EXECUTION_SEAL.json"}
    w0.require(set(files) == set(seal["files"]), "parent inventory changed beyond logger bytes")
    changed = {name: dict(sealed_sha256=seal["files"][name], current_sha256=digest)
               for name, digest in files.items() if digest != seal["files"][name]}
    w0.require(set(changed) == {"launcher.out"}, "only declared launcher.out drift is allowed")
    w0.require(changed["launcher.out"]["sealed_sha256"] == w0.sha(b"")
               and (root / "launcher.out").stat().st_size > 0, "expected empty-to-report logger drift")
    material = w0.load_json(root / "material.json")
    requests = w0.load_json(root / "requests.json")
    identity = dict(model=w0.MODEL, model_sha256=manifest["config"]["model_sha256"],
                    tokenizer_sha256=manifest["config"]["tokenizer_sha256"], run_sha256=w0.digest(manifest))
    w0.validate_requests(material, requests)
    w0.require(requests == w0.build_requests(material, identity,
        w0.load_json(root / "adapter_hashes.json"),
        preflight=w0.load_json(root / "tokenizer_preflight.json")), "parent material/request binding")
    report = w0.load_json(root / "report_real.json")
    w0.require(w0.file_hash(root / "report_real.json") == seal["report_sha256"], "parent report hash")
    w0.require(report["scientific_label"] == report["result"]["label"] == "ASSAY_INVALID"
               and len(report["result"]["roots"]) == 2, "expected declared invalid parent report")
    for row in report["result"]["roots"]:
        w0.require(set(row["cells"]) == set(w0.MAPS)
                   and all(row["cells"][mapping]["oracle_BA"] == 0 for mapping in w0.MAPS),
                   "expected four zero-oracle parent cells")
    resource = w0.load_json(root / "RESOURCE_RECEIPT.json")
    expected_stages = list(manifest["fits"]) + [f"eval_{state}_{operation}"
        for state in ("OFF", "0_0", "0_1", "1_0", "1_1") for operation in ("generate", "score")]
    w0.require(resource["stages"] == expected_stages and len(expected_stages) == 14
               and resource["manifest_sha256"] == w0.digest(manifest), "parent phase inventory")
    receipt = dict(**BOUNDARY, parent_root=str(root), original_seal_sha256=expected_seal_sha256,
        original_seal=seal, current_inventory=current, changed_logger_inventory=changed,
        logger_current_size=(root / "launcher.out").stat().st_size,
        parent_declared_label="ASSAY_INVALID", parent_replay_status="FAILED_LOGGER_DRIFT",
        validation_scope="prepared material/request custody and declared failure; not a rescued full replay")
    return manifest, material, requests, receipt


def build_requests(material, parent_requests, tokenizer):
    """First held row per (tool,mode), in original order, for every root/map."""
    indexed = {tuple(request["audit"]): request for request in parent_requests
               if request["payload"]["kind"] == "oracle_generate"}
    result = []
    for root_index, root in enumerate(material["roots"]):
        first = {}
        for index, row in enumerate(root["held"]):
            first.setdefault((row["slot"], row["mode"]), index)
        w0.require(len(first) == 16, "fixed tool/mode coverage")
        for mapping in w0.MAPS:
            for index in first.values():
                row = root["held"][index]
                parent = indexed[root_index, mapping, "oracle", index]
                original = w0.oracle_prompt(root, mapping, row["context"])
                w0.require(parent["payload"]["prompt"] == original, "original oracle prompt mismatch")
                pair_id = w0.digest([parent["id"], root_index, mapping, index])
                for name, chat, explicit, cap in CONDITIONS:
                    prompt = (INSTRUCTION + "\n" if explicit else "") + original
                    rendered = (tokenizer.tokenizer.apply_chat_template(
                        [{"role": "user", "content": prompt}], tokenize=False,
                        add_generation_prompt=True) if chat else prompt)
                    ids = tokenizer(rendered, add_special_tokens=False,
                                    return_offsets_mapping=True)["input_ids"]
                    w0.require(isinstance(rendered, str) and isinstance(ids, list) and ids
                               and all(type(token) is int and token >= 0 for token in ids)
                               and len(ids) + cap <= 2048, "bounded actual prompt tokens")
                    request = dict(pair_id=pair_id, parent_request_id=parent["id"], root=root_index,
                        mapping=mapping, held_index=index, tool=root["tools"][row["slot"]],
                        mode=row["mode"], condition=name, chat_template=chat, explicit_instruction=explicit,
                        max_new_tokens=cap, do_sample=False, seed=0, prompt=prompt,
                        rendered_prompt=rendered, prompt_input_ids=ids,
                        expected=w0.action(root_index, row["slot"], row["mode"], mapping))
                    result.append(dict(request_id=w0.digest(request), **request))
    w0.require(len(result) == MAX_REQUESTS and len({row["pair_id"] for row in result}) == 64,
               "fixed 64 paired prompts / 320 requests")
    return result


def _separate(path, roots):
    path = w0.checked_path(path)
    for root in roots:
        other = Path(root).resolve()
        w0.require(not path.is_relative_to(other) and not other.is_relative_to(path), "output root overlap")
    return path


def prepare(out, *, parent, parent_seal_sha256, log_dir, deadline_unix):
    w0.require(type(deadline_unix) in (int, float) and math.isfinite(deadline_unix)
               and deadline_unix > time.time(), "prospective finite deadline required")
    manifest, material, parent_requests, receipt = inspect_failed_parent(parent, parent_seal_sha256)
    config = manifest["config"]
    w0.require(deadline_unix <= config["lease_cutoff_unix"], "deadline exceeds pinned lease cutoff")
    protected = [parent, config["model_path"], config["tokenizer_path"], *config["protected"].values()]
    root = _separate(out, protected)
    logs = _separate(log_dir, [*protected, root])
    w0.require(root.parent.is_dir() and logs.parent.is_dir() and not root.exists() and not logs.exists(),
               "fresh output/log directories with existing parents required")
    sources = _sources()
    pins = w0.pin_local_inputs(config)
    w0.require(pins == manifest["inputs"], "runtime inputs differ from W0 pinned inventory")
    tokenizer = w0.load_local_tokenizer(config)
    requests = build_requests(material, parent_requests, tokenizer)
    w0.require(inspect_failed_parent(parent, parent_seal_sha256)[3] == receipt
               and sources == _sources() and w0.pin_local_inputs(config) == pins,
               "source drift during prepare")
    root.mkdir()
    logs.mkdir()
    w0.write_once(root, "parent_source.json", receipt)
    w0.write_once(root, "requests.json", requests)
    spec = dict(version="writer-interface-calibration-v1", **BOUNDARY, output_root=str(root),
        log_dir=str(logs), parent_root=str(w0.checked_path(parent)), parent_seal_sha256=parent_seal_sha256,
        config=config, input_pins=pins, sources=sources, deadline_unix=deadline_unix,
        max_requests=MAX_REQUESTS, max_seconds=MAX_SECONDS, GPU_count=1, A40_hours_cap=1,
        instruction=INSTRUCTION, conditions=[list(condition) for condition in CONDITIONS],
        artifacts={name: w0.file_hash(root / name) for name in ("parent_source.json", "requests.json")})
    w0.write_once(root, "manifest.json", spec)
    w0.write_once(root, "PREPARED.json", dict(manifest_sha256=w0.digest(spec), model_loaded=False, **BOUNDARY))
    return dict(status="PREPARED_CALIBRATION_ONLY", manifest_sha256=w0.digest(spec), **BOUNDARY)


def validate_prepared(root):
    root = w0.checked_path(root)
    spec = w0.load_json(root / "manifest.json")
    w0.require(w0.load_json(root / "PREPARED.json")["manifest_sha256"] == w0.digest(spec)
               and spec["output_root"] == str(root), "calibration manifest binding")
    w0.require(all(spec.get(key) == value for key, value in BOUNDARY.items())
               and spec["max_requests"] == 320 and spec["max_seconds"] == 3600
               and spec["GPU_count"] == spec["A40_hours_cap"] == 1
               and spec["instruction"] == INSTRUCTION
               and spec["conditions"] == [list(condition) for condition in CONDITIONS], "frozen calibration contract")
    w0.require(spec["sources"] == _sources(), "calibration source changed")
    for name, digest in spec["artifacts"].items():
        w0.require(name in ("parent_source.json", "requests.json")
                   and w0.file_hash(root / name) == digest, "calibration artifact changed")
    w0.require(set(spec["artifacts"]) == {"parent_source.json", "requests.json"}, "artifact inventory")
    parent, material, parent_requests, receipt = inspect_failed_parent(spec["parent_root"], spec["parent_seal_sha256"])
    w0.require(parent["config"] == spec["config"] and receipt == w0.load_json(root / "parent_source.json"),
               "failed parent inventory/config changed after calibration prepare")
    protected = [spec["parent_root"], spec["config"]["model_path"], spec["config"]["tokenizer_path"],
                 *spec["config"]["protected"].values()]
    _separate(root, protected)
    _separate(spec["log_dir"], [root, *protected])
    return spec, material, parent_requests


def reduce_records(requests, records):
    w0.require(len(requests) == MAX_REQUESTS and len(records) == MAX_REQUESTS, "incomplete calibration")
    by_id = {row["request_id"]: row for row in records}
    w0.require(len(by_id) == MAX_REQUESTS and set(by_id) == {row["request_id"] for row in requests},
               "duplicate/missing calibration output")
    cells, pairs = {}, {}
    for request in requests:
        record = by_id[request["request_id"]]
        w0.require(type(record["truncated"]) is bool and isinstance(record["text"], str),
                   "typed actual generation outcome required")
        parsed = w0.parse_output(record["text"], record["truncated"])
        name = f"{request['root']}/{request['mapping']}/{request['condition']}"
        cell = cells.setdefault(name, dict(total=0, correct=0, valid=0, truncated=0, multiple=0))
        cell["total"] += 1
        cell["correct"] += int(parsed["action"] == request["expected"])
        cell["valid"] += int(parsed["action"] is not None)
        cell["truncated"] += int(record["truncated"])
        cell["multiple"] += int(parsed["multiple_ACT"])
        pairs.setdefault(request["pair_id"], {})[request["condition"]] = dict(
            request_id=request["request_id"], parent_request_id=request["parent_request_id"],
            correct=parsed["action"] == request["expected"], valid=parsed["action"] is not None,
            truncated=record["truncated"], multiple=parsed["multiple_ACT"])
    w0.require(len(cells) == 20 and all(cell["total"] == 16 for cell in cells.values())
               and len(pairs) == 64 and all(len(pair) == 5 for pair in pairs.values()), "fixed paired denominators")
    return dict(**BOUNDARY, cells=cells, paired_prompt_ids=pairs, total_requests=MAX_REQUESTS)


def _generate(torch, model, tokenizer, request):
    from transformers import GenerationConfig
    ids = torch.tensor([request["prompt_input_ids"]], dtype=torch.long, device="cuda:0")
    config = GenerationConfig(do_sample=False, max_new_tokens=request["max_new_tokens"],
        eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.eos_token_id, use_cache=True)
    with torch.inference_mode():
        generated = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), generation_config=config)
    continuation = generated[0, ids.shape[1]:].tolist()
    ended = bool(continuation) and continuation[-1] == tokenizer.eos_token_id
    w0.require(len(continuation) <= request["max_new_tokens"], "generation exceeded token cap")
    return dict(request_id=request["request_id"], text=tokenizer.decode(continuation[:-1] if ended else continuation),
        truncated=len(continuation) >= request["max_new_tokens"] and not ended,
        generated_ids=continuation, decoded_with_terminal_eos=tokenizer.decode(continuation), eos_terminated=ended)


def worker(root, allow_gpu=False):
    w0.require(allow_gpu is True, "worker requires explicit --allow-gpu")
    root = w0.checked_path(root)
    started = w0.load_json(root / "STARTED.json")
    spec, material, parent_requests = validate_prepared(root)
    w0.assert_output_fds_outside_run(root)
    w0.assert_output_fds_outside_run(w0.checked_path(spec["parent_root"]))
    w0.require(started["manifest_sha256"] == w0.digest(spec), "worker startup binding")
    w0.require(started["deadline_unix"] <= min(started["wall_start"] + MAX_SECONDS,
               spec["deadline_unix"], spec["config"]["lease_cutoff_unix"]), "worker deadline exceeds hard cap")
    w0.require(time.time() < started["deadline_unix"] - 5, "worker deadline")
    w0.write_once(root, "WORKER_CLAIMED.json", dict(pid=os.getpid(), manifest_sha256=w0.digest(spec)))
    pins = w0.pin_local_inputs(spec["config"])
    w0.require(pins == spec["input_pins"], "local model/tokenizer/environment drift")
    hardware = w0.gpu_identity(spec["config"])
    tokenizer = w0.load_local_tokenizer(spec["config"])
    requests = build_requests(material, parent_requests, tokenizer)
    w0.require(requests == w0.load_json(root / "requests.json"), "tokenizer/template/request drift")
    torch = w0.configure_torch(spec["config"], 0)
    w0.require(time.time() < started["deadline_unix"] - 5, "deadline before model load")
    model = w0.load_hf_model(spec["config"], torch)
    model.eval()
    model.requires_grad_(False)
    w0.require(not model.training and not any(parameter.requires_grad for parameter in model.parameters()),
               "model-only inference, no gradients")
    w0.write_once(root, "MODEL_LOADED.json", dict(**BOUNDARY, hardware=hardware, input_pins=pins,
                                                 worker_pid=os.getpid(), model_loaded=True))
    records = []
    for request in requests:
        w0.require(time.time() < started["deadline_unix"] - 5, "request deadline exhausted")
        record = _generate(torch, model, tokenizer, request)
        w0.write_once(root, request["request_id"] + ".json", record)
        records.append(record)
    w0.require(w0.pin_local_inputs(spec["config"]) == pins, "inputs changed during inference")
    validate_prepared(root)
    w0.require(time.time() < started["deadline_unix"] - 5, "final worker deadline")
    w0.write_once(root, "report.json", reduce_records(requests, records))
    return dict(status="CALIBRATION_COMPLETE", **BOUNDARY)


def replay(root):
    """Read-only calibration replay; never invokes or repairs W0 replay."""
    root = w0.checked_path(root)
    seal = w0.load_json(root / "CALIBRATION_SEAL.json")
    w0.require(all(seal.get(key) == value for key, value in BOUNDARY.items()), "calibration-only seal required")
    found = _inventory(root)
    del found["CALIBRATION_SEAL.json"]
    w0.require(found == seal["files"], "calibration sealed inventory changed")
    spec, _, _ = validate_prepared(root)
    resource = w0.load_json(root / "RESOURCE.json")
    started = w0.load_json(root / "STARTED.json")
    w0.require(resource["GPU_count"] == 1 and 0 <= resource["elapsed_seconds"] <= MAX_SECONDS
               and resource["A40_hours"] == resource["elapsed_seconds"] / 3600
               and resource["deadline_unix"] == started["deadline_unix"]
               and resource["deadline_unix"] <= min(started["wall_start"] + MAX_SECONDS,
                   spec["deadline_unix"], spec["config"]["lease_cutoff_unix"]), "resource bound mismatch")
    w0.require(resource["log_path"] == str(Path(spec["log_dir"]) / "worker.log")
               and w0.file_hash(resource["log_path"]) == resource["log_sha256"], "external worker log changed")
    requests = w0.load_json(root / "requests.json")
    report = reduce_records(requests, [w0.load_json(root / (request["request_id"] + ".json")) for request in requests])
    w0.require(report == w0.load_json(root / "report.json"), "sealed report mismatch")
    return report


def execute(root, allow_gpu=False):
    w0.require(allow_gpu is True, "execution requires explicit --allow-gpu")
    begin, wall_start = time.monotonic(), time.time()
    root = w0.checked_path(root)
    spec, _, _ = validate_prepared(root)
    w0.assert_output_fds_outside_run(root)
    w0.assert_output_fds_outside_run(w0.checked_path(spec["parent_root"]))
    w0.require(set(_inventory(root)) == {"manifest.json", "PREPARED.json", "parent_source.json", "requests.json"},
               "fresh prepared calibration required; no restart/rescue")
    deadline = min(wall_start + MAX_SECONDS, spec["deadline_unix"], spec["config"]["lease_cutoff_unix"])
    w0.require(deadline > time.time() + 10, "execution deadline expired")
    w0.require(w0.pin_local_inputs(spec["config"]) == spec["input_pins"], "execution inputs drift")
    hardware = w0.gpu_identity(spec["config"])
    w0.assert_gpu_idle(spec["config"])
    w0.write_once(root, "STARTED.json", dict(manifest_sha256=w0.digest(spec), deadline_unix=deadline,
                                           wall_start=wall_start, hardware=hardware))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=spec["config"]["gpu_uuid"],
        CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0", HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    command = [sys.executable, "-B", "-m", "organism_v6.writer_interface_calibration", "_worker",
               "--run", str(root), "--allow-gpu"]
    log_path = w0.checked_path(spec["log_dir"]) / "worker.log"
    try:
        with log_path.open("xb") as log:
            process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], env=environment,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                remaining = min(MAX_SECONDS - (time.monotonic() - begin), deadline - time.time()) - 5
                w0.require(remaining > 0, "hard cap exhausted before worker wait")
                returncode = process.wait(timeout=remaining)
            except BaseException:
                w0.stop_owned_process(process)
                raise
        w0.require(returncode == 0, "calibration worker failed; no retry")
        validate_prepared(root)
        elapsed = time.monotonic() - begin
        w0.require(elapsed <= MAX_SECONDS and time.time() <= deadline, "one A40-hour/deadline cap")
        requests = w0.load_json(root / "requests.json")
        report = reduce_records(requests, [w0.load_json(root / (request["request_id"] + ".json")) for request in requests])
        w0.require(report == w0.load_json(root / "report.json"), "calibration reducer mismatch")
        w0.write_once(root, "RESOURCE.json", dict(**BOUNDARY, elapsed_seconds=elapsed, A40_hours=elapsed / 3600,
            GPU_count=1, hardware=hardware, worker_pid=process.pid, deadline_unix=deadline,
            log_path=str(log_path), log_sha256=w0.file_hash(log_path)))
        w0.write_once(root, "CALIBRATION_SEAL.json", dict(**BOUNDARY, files=_inventory(root)))
        return replay(root)
    except BaseException as error:
        w0.write_once(root, "FAILED.json", dict(**BOUNDARY, error_type=type(error).__name__, error=str(error)))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="CPU/tokenizer only; no model")
    prep.add_argument("--out", required=True)
    prep.add_argument("--parent", required=True)
    prep.add_argument("--parent-seal-sha256", required=True)
    prep.add_argument("--log-dir", required=True)
    prep.add_argument("--deadline-unix", required=True, type=float)
    for name in ("execute", "_worker"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        command.add_argument("--allow-gpu", action="store_true")
    replay_command = commands.add_parser("replay", help="read-only calibration seal/count verification")
    replay_command.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.out, parent=args.parent, parent_seal_sha256=args.parent_seal_sha256,
                         log_dir=args.log_dir, deadline_unix=args.deadline_unix)
    elif args.command == "replay":
        result = replay(args.run)
    else:
        result = (execute if args.command == "execute" else worker)(args.run, args.allow_gpu)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
