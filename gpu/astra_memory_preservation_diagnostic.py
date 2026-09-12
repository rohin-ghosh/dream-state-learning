"""Bounded whole-text CE versus frozen-OFF preservation diagnostic."""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from gpu.astra_mini_sudoku_diagnostic import check_free
from organism_v6 import memory_preservation as preservation
from organism_v6 import run_reasoning_neutral as supervisor


SOURCE = Path(__file__).resolve().parents[1]
TAG = "bank0__F_r16k16__across__sleep4__r8"
ADAPTER = "adapters/bank0/F_r16k16/across/sleep4/r8"
CAP_SECONDS = 3600


def write_new(path, value):
    preservation.write_new(path, value)


def tokenizer_preflight(model, contents, anchors):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    encoded = preservation.encode_corpus(tokenizer, contents[preservation.CORPUS])
    rows = preservation.anchor_tokens(tokenizer, anchors)
    return dict(memory_order_sha256=preservation.object_hash(encoded), anchor_input_ids=rows,
                input_tokens_per_epoch=249995, supervised_tokens_per_epoch=237071,
                truncated_items=0, boundary_straddles=0)


def prepare(root, original, model, strength):
    preservation.require(strength in (0.0, 0.1), "only prospectively selected coefficients")
    contents = preservation.read_source(original)
    anchors = preservation.make_anchors(contents)
    preservation.require(not root.exists(), "run directory already exists")
    preservation.require(not root.is_relative_to(original) and not original.is_relative_to(root),
                         "overlapping source and destination")
    inventory = preservation.model_inventory(model)
    token_receipt = tokenizer_preflight(model, contents, anchors)
    root.mkdir()
    for name in preservation.INPUT_HASHES:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((original / name).read_bytes())
    write_new(root / "anchors.json", anchors)
    plan = dict(status="PREPARED_NOT_TRAINED", root=str(root), original=str(original),
                model=str(model), model_files=inventory, coefficient=strength,
                source=str(SOURCE), source_files={name: preservation.digest(SOURCE / name)
                for name in ("organism_v6/memory_preservation.py", "organism_v6/memory_dose.py",
                             "gpu/astra_memory_preservation_diagnostic.py")},
                anchors_sha256=preservation.digest(root / "anchors.json"),
                token_preflight=token_receipt,
                worker_cap_seconds=CAP_SECONDS, clean_lineage=False,
                model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY")
    write_new(root / "plan.json", plan)
    verify(root)
    return plan


def verify(root):
    plan = preservation.load(root / "plan.json")
    preservation.require(plan["status"] == "PREPARED_NOT_TRAINED", "preparation status")
    preservation.require(plan["root"] == str(root) and plan["source"] == str(SOURCE), "root/source changed")
    preservation.require(plan["coefficient"] in (0.0, 0.1), "unselected coefficient")
    contents = preservation.read_source(root)
    preservation.read_source(plan["original"])
    preservation.validate_anchors(root / "anchors.json", contents)
    preservation.require(preservation.digest(root / "anchors.json") == plan["anchors_sha256"], "anchors changed")
    for name, expected in plan["source_files"].items():
        preservation.require(preservation.digest(SOURCE / name) == expected, "source changed: " + name)
    preservation.require(preservation.model_inventory(plan["model"]) == plan["model_files"], "model changed")
    return plan


def validate_fit(root, plan):
    adapter = root / ADAPTER
    preservation.require((adapter / "DONE").is_file(), "fit incomplete")
    meta = preservation.load(adapter / "train_meta.json")
    expected = dict(coefficient=plan["coefficient"], ce_coefficient=1.0, n_items=12924,
                    steps=9693, total_steps=9693, tokens=749985, supervised_tokens=711213,
                    rank=8, alpha=16, dropout=0.05, epochs=3, lr=1e-4, bsz=4, seed=2,
                    max_len=512, boundary_straddles=0, truncated_items=0,
                    cache_used=plan["coefficient"] > 0, native_source_sha256=preservation.SOURCE_SHA,
                    anchors_sha256=plan["anchors_sha256"],
                    memory_order_sha256=plan["token_preflight"]["memory_order_sha256"])
    preservation.require(all(meta.get(key) == value for key, value in expected.items()), "fit recipe/dose mismatch")
    preservation.require(all(math.isfinite(meta[key]) for key in ("final_loss", "final_objective", "wall_seconds")),
                         "nonfinite fit metadata")
    if plan["coefficient"] > 0:
        preservation.require(meta["cache_metadata"]["input_ids"] == plan["token_preflight"]["anchor_input_ids"],
                             "cache tokens differ from preflight")
    expected_visits = [9693 // 48 + (index < 9693 % 48) for index in range(48)]
    if plan["coefficient"] == 0:
        expected_visits = [0] * 48
    preservation.require(meta["anchor_visits"] == expected_visits, "anchor schedule mismatch")
    return meta


def run_stages(root):
    plan = verify(root)
    adapter = root / ADAPTER
    preservation.require(not adapter.exists() and not (root / "eval").exists(), "stages already exist")
    common = ["--source-root", plan["original"], "--anchors", str(root / "anchors.json"), "--model", plan["model"]]
    module = [sys.executable, "-B", "-m", "organism_v6.memory_preservation"]
    cache_args = []
    if plan["coefficient"] > 0:
        subprocess.run(module + ["cache"] + common + ["--out-new", str(root / "off_cache"), "--execute"], check=True)
        cache_args = ["--cache", str(root / "off_cache")]
    adapter.parent.mkdir(parents=True)
    subprocess.run(module + ["train"] + common + cache_args + ["--out-new", str(adapter),
                   "--coefficient", str(plan["coefficient"]), "--execute"], check=True)
    validate_fit(root, plan)
    prefix = [sys.executable, "-B", str(SOURCE / "organism_v6/memory_dose.py")]
    subprocess.run(prefix + ["evaluate", "--run-dir", str(root), "--bank", "0", "--adapter", str(adapter),
                   "--tag", TAG, "--model", "hf", "--lambdas", "1", "--adjacent-subset", "4",
                   "--batch-size", "16", "--seed", "0", "--cell", "F_r16k16", "--arm", "across",
                   "--sleep", "4", "--rank", "8"], check=True)
    evaluation = preservation.load(root / "eval" / (TAG + "__lam1.json"))
    preservation.require(evaluation["n_cues"] == 1313 and evaluation["template_check"]
                         and evaluation["abstain_check"]["ok"], "native evaluation incomplete")
    subprocess.run(prefix + ["report", "--run-dir", str(root), "--seed", "0"], check=True)
    verify(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--original")
    parser.add_argument("--model")
    parser.add_argument("--coefficient", type=float, choices=(0.0, 0.1))
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--device", choices=("0", "2"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if args.prepare:
        if args.original is None or args.model is None or args.coefficient is None or args.execute:
            parser.error("prepare requires original/model/coefficient and forbids execute")
        print(json.dumps(prepare(root, Path(args.original).expanduser().resolve(),
                                Path(args.model).expanduser().resolve(), args.coefficient), sort_keys=True))
        return
    if not args.execute or args.device is None:
        parser.error("execution requires --execute and --device")
    if args.worker:
        run_stages(root)
        return
    command = [sys.executable, "-B", "-m", "gpu.astra_memory_preservation_diagnostic",
               "--root", str(root), "--device", args.device, "--execute"]
    logs = root / "logs"
    if args.controller:
        try:
            supervisor.run_worker(command + ["--worker"], log_path=logs / "worker.log",
                                  timeout=CAP_SECONDS, device=args.device)
        except BaseException as error:
            write_new(logs / "failure.json", dict(status="WORKER_FAILED", error=repr(error)))
            raise
        write_new(logs / "result.json", dict(status="WORKER_COMPLETED", finished_utc=datetime.datetime.now(
            datetime.timezone.utc).isoformat()))
        return
    plan = verify(root)
    metadata, xml = check_free(args.device)
    logs.mkdir(exist_ok=False)
    environment = {key: os.environ[key] for key in ("HOME", "USER", "LOGNAME", "PATH", "LD_LIBRARY_PATH", "TMPDIR")
                   if key in os.environ}
    environment.update(CUDA_VISIBLE_DEVICES=args.device, PYTHONPATH=str(SOURCE), PYTHONNOUSERSITE="1",
                       PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                       V6_MODEL=plan["model"], CUDA_HOME="/usr/local/cuda-13.0", OMP_NUM_THREADS="1",
                       TOKENIZERS_PARALLELISM="false")
    environment["PATH"] = "/usr/local/cuda-13.0/bin:" + environment["PATH"]
    with (logs / "controller.log").open("xb") as output:
        process = subprocess.Popen(command + ["--controller"], cwd=SOURCE, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    receipt = dict(metadata, pid=process.pid, node=3, device=args.device,
                   coefficient=plan["coefficient"], status="LAUNCHED_NOT_COMPLETED",
                   started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   source=str(SOURCE), command=command + ["--controller"], worker_seconds_cap=CAP_SECONDS,
                   plan_sha256=preservation.digest(root / "plan.json"), clean_lineage=False)
    write_new(logs / "launch_receipt.json", receipt)
    with (logs / "gpu_before.xml").open("x") as stream:
        stream.write(xml)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
