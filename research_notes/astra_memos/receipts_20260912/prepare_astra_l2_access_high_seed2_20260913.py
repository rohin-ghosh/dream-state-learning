"""Native-tokenizer preparation only; no model load, generation or optimizer."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


SOURCE = "/localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1"


def prepare(probe_path, probe_pin, collection_path):
    if os.environ.get("CUDA_VISIBLE_DEVICES"):
        raise ValueError("prepare must not reserve CUDA")
    if hashlib.sha256(Path(probe_path).read_bytes()).hexdigest() != probe_pin:
        raise ValueError("probe pin mismatch")
    specification = importlib.util.spec_from_file_location("access_high_seed2", probe_path)
    probe = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(probe)
    source = probe.frozen_source(SOURCE)
    probe.collection_metadata(collection_path)
    runtime = probe.load_module("_access_archived_runtime", source / "gpu/astra_l2_public_record_dev.py")
    runtime.offline()
    probe.require(probe.digest(probe.ROOT / "SEAL.json") == probe.SEAL_PIN, "original seal pin differs")
    terminal, files = runtime.custody(probe.ROOT, probe.PLAN_PIN)
    probe.require(terminal["status"] == "COMPLETE", "original incomplete")
    plan, core, trainer, public_probe, reflection, world = runtime.verify(probe.ROOT, probe.PLAN_PIN)
    probe.require(plan["spec"]["source_files"] == probe.SOURCE_FILES and plan["base_sha256"] == probe.BASE_PIN and
                  {name: entry["sha256"] for name, entry in plan["spec"]["helpers"].items()} == probe.HELPERS,
                  "original bindings differ")
    tokenizer = public_probe.native_tokenizer(plan["spec"]["model"])
    probe.require(tokenizer.chat_template == plan["chat_template"], "tokenizer template drift")
    cases = probe.build_cases(runtime, core, trainer, public_probe, plan, world, tokenizer, probe.ROOT)
    probe.require(runtime.custody(probe.ROOT, probe.PLAN_PIN)[1] == files and
                  probe.digest(probe.ROOT / "SEAL.json") == probe.SEAL_PIN, "old root changed")
    return dict(status="PASS_NATIVE_CPU_ENCODING", cases=len(cases), forwards=0, updates=0,
                probe_sha256=probe_pin, case_sha256=probe.value_hash(cases), plan_sha256=probe.PLAN_PIN,
                learner_seed=probe.LEARNER_SEED, learning_rate=probe.LEARNING_RATE,
                target_lengths=sorted({len(candidate["target_ids"]) for case in cases for candidate in case["candidates"]}),
                max_length=max(len(candidate["input_ids"]) for case in cases for candidate in case["candidates"]))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe_path")
    parser.add_argument("probe_pin")
    parser.add_argument("collection_path")
    options = parser.parse_args()
    print(json.dumps(prepare(**vars(options)), sort_keys=True), flush=True)
