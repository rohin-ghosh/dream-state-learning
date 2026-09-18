"""Bounded three-seed acquisition screen, not the complete retention campaign."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import astra_pcfl_event_sequence_v2_fit as fit
from gpu import astra_pcfl_event_sequence_v2_outer as outer
from gpu import astra_pcfl_event_sequence_v2_readout as readout


SCHEMA = "pcfl.event_sequence.v2.acquisition_campaign.v1"
BATCH_SECONDS = 7200
BUDGET = {"learner_seeds": 3, "fits": 3, "updates": 600, "presentations": 2400,
          "readout_calls": 96, "parents": 0, "batch_seconds": BATCH_SECONDS}


def pin(path):
    return {"path": str(Path(path).resolve()), "sha256": fit.file_hash(path)}


def utc():
    return datetime.now(timezone.utc).isoformat()


def isolated_output(output, input_pin, allocation_pin):
    output = Path(output).resolve()
    for protected in (Path(input_pin["path"]).resolve().parent, Path(allocation_pin["path"]).resolve().parent,
                      Path(outer.__file__).resolve().parent):
        fit.require(not output.is_relative_to(protected) and not protected.is_relative_to(output), "outer/input/source overlap")


def prepare(args):
    from transformers import AutoTokenizer
    root = Path(args.root).resolve()
    fit.require(not root.exists(), "fresh campaign root required")
    os.environ.update({name: "1" for name in fit.OFFLINE})
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    prior_pin = {"path": args.prior_inputs, "sha256": args.prior_inputs_sha256}
    allocation_pin = {"path": args.allocation, "sha256": args.allocation_sha256}
    prior, template = fit.read_pin(prior_pin), fit.read_pin(allocation_pin)
    fit.require(prior["schema"] == "pcfl.event_sequence.fit.v1/inputs", "known source input schema required")
    outer.lifecycle.validate_allocation(template)
    outer.lifecycle.check_node(template)
    fit.same(sys.executable, template["python"], "native interpreter differs")
    fit.same(fit.environment(), prior["environment"], "native environment differs")
    shutdown = {"path": args.shutdown, "sha256": args.shutdown_sha256}
    fit.same(pin(shutdown["path"]), shutdown, "shutdown binding differs")
    replay = fit.read_pin(prior["replay_receipt"])
    fit.same(pin(prior["archive"]["path"]), prior["archive"], "archive bytes differ")
    fit.require(prior["archive"]["sha256"] == fit.prefix.ARCHIVE_SHA256, "original source archive required")
    imported = fit.prefix.build_import(fit.prefix.load_evidence(prior["archive"]["path"]), replay, replay["sha256"])
    for key in ("model_binding", "base_state_receipt"):
        fit.read_pin(prior[key])
    tokenizer = AutoTokenizer.from_pretrained(prior["model_path"], local_files_only=True, trust_remote_code=False)
    gpu_rows = subprocess.run(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"],
                              check=True, capture_output=True, text=True, timeout=20).stdout.splitlines()
    gpu_ids = {int(row.split(",")[0]): row.split(",")[1].strip() for row in gpu_rows}
    fit.require(len(args.gpus) == 3 and len(set(args.gpus)) == 3 and all(index in gpu_ids for index in args.gpus), "three distinct observed GPUs required")
    root.mkdir()
    (root / "inputs").mkdir()
    (root / "runs").mkdir()
    entries = []
    for seed, gpu in enumerate(args.gpus):
        directory = root / "inputs" / f"seed{seed}"
        directory.mkdir()
        run_root = root / "runs" / f"seed{seed}"
        run_root.mkdir()
        material = fit.sequence.export_material(imported, imported["sha256"], tokenizer, learner_seed=seed)
        fit.write(directory / "material.json", material)
        allocation = {**template, "gpu_index": gpu, "gpu_uuid": gpu_ids[gpu], "outer_sha256": fit.file_hash(outer.__file__)}
        outer.lifecycle.validate_allocation(allocation)
        deadline = time.monotonic() + 90
        checks = {"queue": outer.lifecycle.check_queue(allocation, deadline),
                  "gpu": outer.lifecycle.check_gpu(allocation, deadline),
                  "cvd": outer.lifecycle.check_cvd(allocation, deadline, release=True)}
        fit.write(directory / "prepare_resources.json", checks)
        fit.require(checks["queue"]["matched"] and checks["gpu"]["empty"] and checks["cvd"]["clear"], "resource checks failed; no launch")
        fit.write(directory / "allocation.json", allocation)
        inputs = {key: prior[key] for key in ("model_path", "model_binding", "base_state_receipt", "replay_receipt", "archive", "environment")}
        inputs.update(schema=fit.SCHEMA + "/inputs", gpu_uuid=gpu_ids[gpu], source_files=fit.source_files(),
                      predecessor=None, learner_seed=seed, material=pin(directory / "material.json"))
        fit.write(directory / "fit_inputs.json", inputs)
        cold = {key: value for key, value in inputs.items() if key != "predecessor"}
        cold.update(schema=readout.SCHEMA + "/inputs", source_files=readout.source_files(), shutdown_binding=shutdown, fit_receipt=None)
        fit.write(directory / "c0_inputs.json", cold)
        entry = {"seed": seed, "gpu": gpu, "allocation": pin(directory / "allocation.json"),
                 "fit_inputs": pin(directory / "fit_inputs.json"), "c0_inputs": pin(directory / "c0_inputs.json"),
                 "material": pin(directory / "material.json"), "spec_sha256": material["spec"]["sha256"], "run_root": str(run_root)}
        isolated_output(run_root / "fit_outer", entry["fit_inputs"], entry["allocation"])
        isolated_output(run_root / "no_write_outer", entry["c0_inputs"], entry["allocation"])
        outer._inputs(entry["fit_inputs"]["path"], entry["fit_inputs"]["sha256"], entry["allocation"]["path"],
                      entry["allocation"]["sha256"], allocation["outer_sha256"], "A200", time.monotonic() + 90,
                      output=run_root / "fit_outer/fit")
        entries.append(entry)
    manifest = {"schema": SCHEMA, "status": "PREPARED_NOT_EXECUTED", "prepared_at": utc(),
                "source_files": {**readout.source_files(), str(Path(outer.__file__).resolve()): fit.file_hash(outer.__file__),
                                 str(Path(__file__).resolve()): fit.file_hash(__file__),
                                 str(Path(outer.lifecycle.__file__).resolve()): fit.file_hash(outer.lifecycle.__file__)},
                "prior_inputs": prior_pin, "allocation_template": allocation_pin, "entries": entries,
                "budget": BUDGET,
                "limits": fit.sequence.LIMITS, "descendants_enabled": False, "automatic_promotion": False}
    fit.write(root / "manifest.json", manifest)
    print(fit.prefix.canonical({"status": manifest["status"], "manifest": pin(root / "manifest.json"), "entries": entries}).decode(), flush=True)


def validate_campaign(manifest, root):
    fit.require(manifest["schema"] == SCHEMA and manifest["status"] == "PREPARED_NOT_EXECUTED", "prepared manifest required")
    fit.same(manifest["budget"], BUDGET, "fixed campaign budget differs")
    entries = manifest["entries"]
    fit.require(len(entries) == 3 and [entry["seed"] for entry in entries] == [0, 1, 2]
                and all(type(entry["seed"]) is int and type(entry["gpu"]) is int for entry in entries), "exact three ordered learner seeds required")
    fit.require(len({entry["gpu"] for entry in entries}) == 3, "three distinct allocated GPUs required")
    for entry in entries:
        directory = root / "inputs" / f"seed{entry['seed']}"
        fit.same(entry["run_root"], str(root / "runs" / f"seed{entry['seed']}"), "fixed run root differs")
        values = {}
        for name, filename in (("allocation", "allocation.json"), ("fit_inputs", "fit_inputs.json"),
                               ("c0_inputs", "c0_inputs.json"), ("material", "material.json")):
            fit.same(entry[name]["path"], str(directory / filename), "campaign entry path differs")
            values[name] = fit.read_pin(entry[name])
        allocation, trained, cold, material = (values[name] for name in ("allocation", "fit_inputs", "c0_inputs", "material"))
        fit.same(allocation["gpu_index"], entry["gpu"], "campaign allocated GPU label differs")
        fit.same([trained["learner_seed"], cold["learner_seed"], material["spec"]["learner_seed"]],
                 [entry["seed"]] * 3, "campaign learner labels differ from inputs/material")
        fit.same(material["spec"]["sha256"], entry["spec_sha256"], "campaign material spec differs")
        fit.same([trained["material"], cold["material"]], [entry["material"]] * 2, "campaign material pins differ")
        fit.same([trained["gpu_uuid"], cold["gpu_uuid"]], [allocation["gpu_uuid"]] * 2, "campaign GPU identity differs")
        fit.require(trained["schema"] == fit.SCHEMA + "/inputs" and cold["schema"] == readout.SCHEMA + "/inputs"
                    and trained["predecessor"] is None and cold["fit_receipt"] is None, "campaign requires fresh C0/A200 inputs")
        for name in ("model_path", "model_binding", "base_state_receipt", "replay_receipt", "archive", "environment"):
            fit.same(trained[name], cold[name], "campaign fit/C0 identity differs: " + name)
        isolated_output(Path(entry["run_root"]) / "fit_outer", entry["fit_inputs"], entry["allocation"])


def run(args):
    root = Path(args.root).resolve()
    manifest_pin = {"path": str(root / "manifest.json"), "sha256": args.manifest_sha256}
    manifest = fit.read_pin(manifest_pin)
    validate_campaign(manifest, root)
    for path, checksum in manifest["source_files"].items():
        fit.same(fit.file_hash(path), checksum, "frozen campaign source differs")
    fit.write(root / "started.json", {"started_at": utc(), "pid": os.getpid(), "manifest": manifest_pin})
    started = time.monotonic()
    results = []
    try:
        for entry in manifest["entries"]:
            directory = root / "inputs" / f"seed{entry['seed']}"
            run_root = Path(entry["run_root"])
            allocation = fit.read_pin(entry["allocation"])
            for stage, state, input_pin in (("fit", None, entry["fit_inputs"]),
                                             ("readout", "NO_WRITE", entry["c0_inputs"]),
                                             ("readout", "A200", None)):
                fit.require(time.monotonic() - started <= BATCH_SECONDS - outer.TOTAL_SECONDS, "batch cap leaves insufficient worker budget")
                fit.require(time.time() + outer.TOTAL_SECONDS < allocation["lease_end"] - max(21600, allocation["lease_margin_seconds"]), "lease finish margin")
                if state == "A200":
                    cold = fit.read_pin(entry["c0_inputs"])
                    cold["fit_receipt"] = pin(run_root / "fit_outer/fit/completed.json")
                    fit.write(directory / "a200_inputs.json", cold)
                    input_pin = pin(directory / "a200_inputs.json")
                fit.read_pin(input_pin)
                output = run_root / ("fit_outer" if stage == "fit" else f"{state.lower()}_outer")
                isolated_output(output, input_pin, entry["allocation"])
                result = outer.controller(input_pin["path"], input_pin["sha256"], entry["allocation"]["path"],
                                          entry["allocation"]["sha256"], str(output), outer_sha256=allocation["outer_sha256"],
                                          phase="A200", stage=stage, state=state)
                summary = {"seed": entry["seed"], "gpu": entry["gpu"], "stage": stage, "state": state,
                           "status": result["status"], "collection": pin(output / "collection.json"),
                           "gpu_released": result["gpu_released"], "finished_at": utc()}
                results.append(summary)
                print(fit.prefix.canonical(summary).decode(), flush=True)
                fit.require(result["status"] == "COMPLETED" and result["gpu_released"] is True and result["errors"] == [], "failed stage; no automatic retry")
        fit.write(root / "completed.json", {"status": "ACQUISITION_CAPTURED_NOT_QUALIFIED", "results": results,
                                          "elapsed_seconds": time.monotonic() - started, "finished_at": utc(),
                                          "descendants_enabled": False, "automatic_promotion": False})
    except BaseException as error:
        fit.write(root / "stopped.json", {"status": "STOPPED", "results": results, "finished_at": utc(),
                                        "error_type": type(error).__name__, "error": str(error), "no_automatic_retry": True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preparation = subparsers.add_parser("prepare")
    for name in ("root", "prior-inputs", "prior-inputs-sha256", "allocation", "allocation-sha256", "shutdown", "shutdown-sha256"):
        preparation.add_argument("--" + name, required=True)
    preparation.add_argument("--gpus", type=int, nargs=3, required=True)
    execution = subparsers.add_parser("run")
    execution.add_argument("--root", required=True)
    execution.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else run)(args)


if __name__ == "__main__":
    main()
