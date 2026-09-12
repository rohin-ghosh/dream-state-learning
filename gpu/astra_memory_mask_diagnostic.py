"""Run one bounded same-input prefix-mask memory diagnostic on node3."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free
from gpu.prepare_memory_mask_run import CORPUS_PATH, RECEIPT
from organism_v6 import run_reasoning_neutral as supervisor


SOURCE = Path(__file__).resolve().parents[1]


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def verify_inputs(root):
    receipt = json.loads((root / RECEIPT).read_text())
    if receipt["status"] != "PREPARED_NOT_TRAINED" or receipt["destination"] != str(root):
        raise ValueError("wrong preparation receipt")
    for directory, entries in ((root, receipt["inputs"]),
                               (Path(receipt["source"]), receipt["source_inputs"])):
        for name, digest in entries.items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError("changed input: " + str(directory / name))
    return receipt


def validate_fit(meta, corpus, receipt):
    counts = receipt["counts"]
    if counts["truncated_items"] != 0:
        raise ValueError("preparation reported truncation")
    expected = dict(rank=8, alpha=16, dropout=0.05, epochs=3, lr=1e-4, seed=2,
                    bsz=4, steps=9693, total_steps=9693, n_items=12924,
                    tokens=3 * counts["input_tokens_per_epoch"],
                    supervised_tokens=3 * counts["supervised_per_epoch"],
                    boundary_straddles=counts["boundary_straddles"], truncated_items=0,
                    max_len=512, measure_only=False,
                    corpus_sha=corpus["sha"], items_sha=corpus["items_sha"],
                    model="Qwen/Qwen2.5-7B-Instruct",
                    recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
                    targets=["q_proj", "k_proj", "v_proj", "o_proj",
                             "gate_proj", "up_proj", "down_proj"],
                    ordering="chronological", writer="occurrences", representation="frames",
                    shuffled=False, tokenization="joint context+target (encode_item)")
    if any(meta.get(key) != value for key, value in expected.items()):
        raise ValueError("fit dose, mask identity or configuration mismatch")
    if meta["throughput"]["grad_checkpoint"] is not False:
        raise ValueError("unexpected checkpointing change")
    if not math.isfinite(meta["final_loss"]):
        raise ValueError("nonfinite final loss")


def run_stages(root):
    receipt = verify_inputs(root)
    adapter = root / "adapters/bank0/F_r16k16/across/sleep4/r8"
    if adapter.exists():
        raise ValueError("adapter already exists")
    if (root / "eval").exists() or (root / "report").exists():
        raise ValueError("evaluation or report already exists")
    corpus_path = root / CORPUS_PATH
    script = str(SOURCE / "organism_v6/memory_dose.py")
    prefix = [sys.executable, "-B", script]
    subprocess.run(prefix + ["train", "--run-dir", str(root), "--corpus", str(corpus_path),
                   "--out", str(adapter), "--model", "hf", "--rank", "8", "--epochs", "3",
                   "--lr", "1e-4", "--seed", "2", "--no-reuse"], check=True)
    if not (adapter / "DONE").is_file():
        raise ValueError("missing fit completion")
    validate_fit(json.loads((adapter / "train_meta.json").read_text()),
                 json.loads(corpus_path.read_text()), receipt)
    tag = "bank0__F_r16k16__across__sleep4__r8"
    subprocess.run(prefix + ["evaluate", "--run-dir", str(root), "--bank", "0",
                   "--adapter", str(adapter), "--tag", tag, "--model", "hf", "--lambdas", "1",
                   "--adjacent-subset", "4", "--batch-size", "16", "--seed", "0",
                   "--cell", "F_r16k16", "--arm", "across", "--sleep", "4", "--rank", "8"], check=True)
    evaluation = json.loads((root / "eval" / (tag + "__lam1.json")).read_text())
    if evaluation["n_cues"] != 1313 or not evaluation["template_check"] or not evaluation["abstain_check"]["ok"]:
        raise ValueError("incomplete native evaluation")
    subprocess.run(prefix + ["report", "--run-dir", str(root), "--seed", "0"], check=True)
    verify_inputs(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--device", choices=("0", "2"), required=True)
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve(strict=True)
    if args.worker:
        run_stages(root)
        return
    command = [sys.executable, "-B", str(Path(__file__).resolve()),
               "--root", str(root), "--device", args.device]
    logs = root / "logs"
    if args.controller:
        try:
            supervisor.run_worker(command + ["--worker"], log_path=logs / "worker.log",
                                  timeout=2700, device=args.device)
            result = dict(status="WORKER_COMPLETED", finished_utc=datetime.datetime.now(
                datetime.timezone.utc).isoformat())
        except BaseException as error:
            write_new(logs / "failure.json", dict(status="WORKER_FAILED", error=repr(error)))
            raise
        write_new(logs / "result.json", result)
        return
    verify_inputs(root)
    metadata, xml = check_free(args.device)
    logs.mkdir(exist_ok=False)
    environment = {key: os.environ[key] for key in (
        "HOME", "USER", "LOGNAME", "PATH", "LD_LIBRARY_PATH", "TMPDIR") if key in os.environ}
    environment.update(CUDA_VISIBLE_DEVICES=args.device, PYTHONPATH=str(SOURCE),
                       PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1",
                       TRANSFORMERS_OFFLINE="1", V6_MODEL="Qwen/Qwen2.5-7B-Instruct",
                       CUDA_HOME="/usr/local/cuda-13.0", OMP_NUM_THREADS="1", TOKENIZERS_PARALLELISM="false")
    environment["PATH"] = "/usr/local/cuda-13.0/bin:" + environment["PATH"]
    with (logs / "controller.log").open("xb") as output:
        process = subprocess.Popen(command + ["--controller"], cwd=SOURCE, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    write_new(logs / "launch_receipt.json", dict(metadata, pid=process.pid,
              started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              node=3, device=args.device, source=str(SOURCE), command=command + ["--controller"],
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              status="LAUNCHED_NOT_COMPLETED", worker_seconds_cap=2700, clean_lineage=False))
    with (logs / "gpu_before.xml").open("x") as stream:
        stream.write(xml)
    print((logs / "launch_receipt.json").read_text())


if __name__ == "__main__":
    main()
