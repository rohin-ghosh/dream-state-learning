"""CPU-only native tokenizer compatibility before Main's access diagnostic."""
import importlib.util
import json
from pathlib import Path
import sys


sys.dont_write_bytecode = True
probe_path, probe_pin, collection_path = sys.argv[1:]
spec = importlib.util.spec_from_file_location("access_probe", probe_path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
probe.require(probe.digest(probe_path) == probe_pin, "probe pin mismatch")
source = probe.frozen_source("/localhome/local-rohing/astra_sources/l2_public_record_20260913_attempt1")
probe.collection_metadata(collection_path)
runtime = probe.load_module("_access_archived_runtime", source / "gpu/astra_l2_public_record_dev.py")
runtime.offline()
terminal, files = runtime.custody(probe.ROOT, probe.PLAN_PIN)
probe.require(terminal["status"] == "COMPLETE", "original incomplete")
plan, core, trainer, public_probe, reflection, world = runtime.verify(probe.ROOT, probe.PLAN_PIN)
tokenizer = public_probe.native_tokenizer(plan["spec"]["model"])
cases = probe.build_cases(runtime, core, trainer, public_probe, plan, world, tokenizer, probe.ROOT)
probe.require(runtime.custody(probe.ROOT, probe.PLAN_PIN)[1] == files, "old root changed")
result = dict(status="PASS_NATIVE_CPU_ENCODING", cases=len(cases), forwards=0, updates=0,
              probe_sha256=probe_pin, case_sha256=probe.value_hash(cases), plan_sha256=probe.PLAN_PIN,
              target_lengths=sorted({len(candidate["target_ids"]) for case in cases for candidate in case["candidates"]}),
              max_length=max(len(candidate["input_ids"]) for case in cases for candidate in case["candidates"]))
print(json.dumps(result, sort_keys=True), flush=True)
