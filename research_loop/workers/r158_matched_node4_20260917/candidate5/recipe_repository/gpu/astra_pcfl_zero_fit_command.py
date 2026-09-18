"""Offline preparation and explicit execution for the scoped C0 diagnostic."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_dev as driver


OFFLINE = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "VLLM_NO_USAGE_STATS")


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_json(path, value):
    with Path(path).open("xb") as stream:
        stream.write(driver.canonical(value) + b"\n")


def offline_tokenizer(model_path):
    driver.require(all(os.environ.get(name) == "1" for name in OFFLINE), "offline environment required")
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)


def measure(roots_path, model_path, output_dir):
    driver.require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "measurement must disable CUDA")
    root = Path(output_dir)
    root.mkdir(parents=False, exist_ok=False)
    started = time.monotonic()
    try:
        roots = read_json(roots_path)
        plan = driver.build_tasks(roots)
        tokenizer = offline_tokenizer(model_path)
        binding = {"model_path": str(Path(model_path).resolve()),
                   "tokenizer_files": {name: file_hash(Path(model_path) / name) for name in sorted(driver.native.TOKENIZER_FILES)},
                   "chat_template_sha256": driver.native.text_hash(tokenizer.chat_template)}
        write_json(root / "plan.json", plan)
        measurement = driver.measure_tokenizer(plan, tokenizer, binding)
        write_json(root / "measurements.json", measurement)
        result = {"stage": "ACTUAL_OFFLINE_MEASUREMENTS", "plan_sha256": plan["sha256"],
                  "measurements_sha256": measurement["sha256"], "elapsed_seconds": time.monotonic() - started,
                  "roots_file_sha256": file_hash(roots_path), "command_sha256": file_hash(__file__),
                  "model_calls": 0, "updates": 0, "full_v22_release": False}
        write_json(root / "receipt.json", result)
        return result
    except Exception as error:
        write_json(root / "failure.json", {"stage": "MEASURE", "type": type(error).__name__, "message": str(error),
                                            "elapsed_seconds": time.monotonic() - started, "model_calls": 0})
        raise


def prepare(measurement_dir, model_binding_path, gpu_uuid, output_dir, manifest_path, cap_seconds, validity_seconds):
    driver.require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "preparation must disable CUDA")
    driver.require(0 < cap_seconds <= 36000 and 0 < validity_seconds <= 36000, "bounded time required")
    driver.require(not Path(output_dir).exists() and not Path(manifest_path).exists(), "fresh manifest/output required")
    plan = read_json(Path(measurement_dir) / "plan.json")
    measured = read_json(Path(measurement_dir) / "measurements.json")
    model = measured["binding"]["model_path"]
    tokenizer = offline_tokenizer(model)
    sources = driver.source_snapshot()
    sources[str(Path(__file__).resolve())] = file_hash(__file__)
    actor = {"schema": driver.native.SCHEMA, **measured["binding"],
             "model_binding": {"path": str(Path(model_binding_path).resolve()), "sha256": file_hash(model_binding_path)},
             "source_files": sources, "tokenizer_probe": {"text": "PCFL OFFLINE TOKENIZER PROBE\n",
                  "token_ids": tokenizer.encode("PCFL OFFLINE TOKENIZER PROBE\n", add_special_tokens=False)},
             "environment": driver.native.environment_identity(), "gpu_uuid": gpu_uuid,
             "engine": dict(driver.native.ENGINE), "output_dir": str(Path(output_dir) / "actor"),
             "deadline": time.monotonic() + validity_seconds, "device_seconds_cap": cap_seconds,
             "max_input_tokens": 14336, "max_output_tokens": 2048, "max_calls": 1952}
    manifest = driver.build_manifest(plan, measured, actor, wall_seconds=cap_seconds,
                                     device_seconds=cap_seconds, output_dir=output_dir)
    driver.validate_manifest(manifest, tokenizer)
    write_json(manifest_path, manifest)
    return {"stage": "PREPARED_NOT_LAUNCHED", "manifest_sha256": manifest["sha256"],
            "manifest_file_sha256": file_hash(manifest_path), "model_calls": 0, "updates": 0,
            "full_v22_release": False}


def run(manifest_path, manifest_sha256):
    driver.require(file_hash(manifest_path) == manifest_sha256, "manifest file drift")
    manifest = read_json(manifest_path)
    driver.require(manifest["test_only"] is False, "CLI refuses synthetic manifests")
    driver.require(os.environ.get("CUDA_VISIBLE_DEVICES") == manifest["actor"]["gpu_uuid"], "allocated GPU differs")
    driver.require(not Path(manifest["output_dir"]).exists(), "attempt already exists")
    tokenizer = offline_tokenizer(manifest["actor"]["model_path"])
    return driver.Diagnostic(manifest, tokenizer).run()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="stage", required=True)
    measurement = commands.add_parser("measure")
    measurement.add_argument("--roots", required=True)
    measurement.add_argument("--model", required=True)
    measurement.add_argument("--output", required=True)
    preparation = commands.add_parser("prepare")
    for name in ("measurements", "model-binding", "gpu-uuid", "output", "manifest"):
        preparation.add_argument("--" + name, required=True)
    preparation.add_argument("--cap-seconds", required=True, type=int)
    preparation.add_argument("--validity-seconds", required=True, type=int)
    execution = commands.add_parser("run")
    execution.add_argument("--manifest", required=True)
    execution.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    if args.stage == "measure":
        result = measure(args.roots, args.model, args.output)
    elif args.stage == "prepare":
        result = prepare(args.measurements, args.model_binding, args.gpu_uuid, args.output, args.manifest,
                         args.cap_seconds, args.validity_seconds)
    else:
        result = run(args.manifest, args.manifest_sha256)
    print(driver.canonical({key: value for key, value in result.items() if key not in ("results", "panels")}).decode())
    if args.stage == "run" and result["status"] != "COMPLETE_AWAITING_OUTER_RELEASE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
