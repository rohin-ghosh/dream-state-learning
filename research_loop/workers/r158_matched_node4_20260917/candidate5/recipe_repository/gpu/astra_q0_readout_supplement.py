"""One separately sealed R1 DERANGED128 readout; never resume the aborted root."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from gpu import astra_pairwise_q0_fulldose as q0


VERSION = "astra-q0-final-readout-supplement-v1"
Q0_SHA256 = "f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca"
MAX_SECONDS, CLEANUP_SECONDS, COLLECTION_SECONDS = 3600, 45, 180
IDENTITY_SECONDS = 30
STATE, SNAPSHOT = "P_DERANGED", 128
FAILED_STAGE = "09_eval_P_DERANGED_128"
STAGES = ("00_audit", "01_eval_OFF_0", "02_fit_P_AUTH", "03_eval_P_AUTH_32",
          "04_eval_P_AUTH_64", "05_eval_P_AUTH_128", "06_fit_P_DERANGED",
          "07_eval_P_DERANGED_32", "08_eval_P_DERANGED_64")
SCOPE = "EXCLUDED_DIAGNOSTIC_DEV_SUPPLEMENT_NOT_PRIMARY_NOT_CLEAN_NOT_PARENTING"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def source_pins():
    q0.require(Path(q0.__file__).resolve() == q0.repository() / "gpu/astra_pairwise_q0_fulldose.py"
               and q0.file_hash(q0.__file__) == Q0_SHA256, "immutable full-dose executor")
    pins = q0.native_source_pins()
    for name in ("gpu/astra_q0_readout_supplement.py", "tests/test_astra_q0_readout_supplement.py"):
        pins[name] = q0.file_hash(q0.repository() / name)
    return pins


def confined(root, relative):
    path = Path(relative)
    q0.require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == relative,
               "relative confined artifact")
    result = root / path
    q0.require(result.resolve(strict=True).is_relative_to(root.resolve(strict=True))
               and not any(parent.is_symlink() for parent in (result, *result.parents) if parent != root.parent),
               "artifact path/symlink escape")
    return result


def stage_data(root, stage, manifest, prepared, started):
    job = read_json(root / "jobs" / (stage + ".json"))
    done = read_json(root / "stages" / stage / "DONE.json")
    receipt = read_json(root / "receipts" / (stage + ".json"))
    cleanup = read_json(root / "logs" / (stage + ".cleanup.json"))
    ticket = job["ticket"]
    q0.require(ticket["ticket_sha256"] == q0.digest({key: value for key, value in ticket.items() if key != "ticket_sha256"})
               and ticket["prepared_sha256"] == q0.digest(prepared)
               and ticket["evidence_kind"] == q0.NATIVE_KIND
               and q0.native_stage_name(ticket) == stage, "original ticket/material identity")
    q0.require(job["manifest_sha256"] == q0.file_hash(root / "manifest.json")
               and job["started_sha256"] == q0.file_hash(root / "STARTED.json")
               and done["load"]["job_sha256"] == q0.file_hash(root / "jobs" / (stage + ".json"))
               and done["load"]["ticket_sha256"] == receipt["ticket_sha256"] == ticket["ticket_sha256"],
               "original job/load/receipt binding")
    q0.require(receipt["done_sha256"] == q0.file_hash(root / "stages" / stage / "DONE.json")
               and receipt["cleanup_sha256"] == q0.file_hash(root / "logs" / (stage + ".cleanup.json"))
               and receipt["log_sha256"] == q0.file_hash(root / "logs" / (stage + ".log")), "original receipt hashes")
    load = done["load"]
    q0.require(load == read_json(root / "stages" / stage / "LOAD.json"), "original LOAD/DONE identity")
    q0.require(load["allocation"] == prepared["allocation"] and load["recipe"] == prepared["recipe"]
               and load["source_pins"] == manifest["source_pins"]
               and load["inputs"] == manifest["inputs"], "original load source/allocation")
    q0.require(receipt["pid"] == cleanup["pid"] == load["identity"]["pid"]
               and receipt["process_start"] == load["identity"]["start_ticks"]
               and receipt["load_id"] == load["load_id"] and receipt["attempts"] == 1
               and receipt["status"] == "FINISHED" and receipt["cleanup"] == "COMPLETE"
               and cleanup["owned_group_empty"] is True and cleanup["gpu_processes_absent"] is True
               and cleanup["reservation_release_verified"] is True
               and cleanup["device"] == manifest["config"]["gpu_uuid"]
               and started["started"] <= receipt["start"] <= done["finished"] <= receipt["finish"] < started["deadline"]
               and done["finished"] < job["deadline"], "original successful stage release/clock")
    events = []
    for event in done["events"]:
        q0.require(Path(event["path"]).name == event["path"], "flat original event")
        path = root / "stages" / stage / "events" / event["path"]
        q0.require(q0.file_hash(path) == event["sha256"], "original raw event hash")
        events.append((event["path"], read_json(path)))
    result = done["result"]
    if ticket["kind"] == "fit":
        q0.require([value for name, value in events if name.endswith("_step.json")] == result["steps"]
                   and [value for name, value in events if name.endswith("_initial.json")] == [result["initial"]],
                   "original fit event join")
        after = [value for name, value in events if name.endswith("_canary_after.json")]
        q0.require(len(after) == 1 and after[0]["result"] == result["canary"]
                   and after[0]["delta"] == result["canary_raw"]["delta"], "original raw canary join")
        natural, model_calls = 128 + 4 * result["updates"] + 16, 128 + 4 * result["updates"] + 16
    elif ticket["kind"] == "eval":
        q0.require([value for name, value in events if name.endswith("_readout.json")] == result,
                   "original readout event join")
        q0.require(load["adapter"] == job.get("adapter") == receipt["adapter"], "original readout adapter")
        natural = sum(record["operation"] == "prefix" for record in result)
        model_calls = natural + sum(len(record["output"]["generated_ids"]) for record in result if record["operation"] == "generate")
    else:
        natural = model_calls = 128
    q0.require(done["counters"] == dict(natural_prefix_forwards=natural, model_forward_calls=model_calls),
               "original successful-stage counters")
    return job, done, receipt


def admit_original(original, custody_path, custody_sha256, *, seal_sha256, finalized_sha256):
    root = Path(original).resolve(strict=True)
    q0.require(root.is_dir() and q0.file_hash(custody_path) == custody_sha256, "Main custody receipt pin")
    q0.require(isinstance(read_json(custody_path), dict), "Main custody receipt must be JSON object")
    files = q0.inventory(root)
    q0.require(files.get("SEAL.json") == seal_sha256 and files.get("FINALIZED.json") == finalized_sha256,
               "Main-pinned original seal/finalization")
    seal, finalized = read_json(root / "SEAL.json"), read_json(root / "FINALIZED.json")
    q0.require(seal["version"] == q0.VERSION and seal["evidence_kind"] == q0.NATIVE_KIND
               and seal["classification"] == "PENDING_DURABLE_FINALIZATION"
               and {name: value for name, value in files.items() if name not in ("SEAL.json", "FINALIZED.json")} == seal["files"]
               and finalized["seal_sha256"] == files["SEAL.json"], "closed original seal and inventory")
    manifest, prepared, started, resource = [read_json(root / name) for name in
                                            ("manifest.json", "prepared.json", "STARTED.json", "RESOURCE.json")]
    q0.require(manifest["version"] == q0.VERSION and prepared["version"] == q0.VERSION
               and manifest["allocation"] == prepared["allocation"] == q0.allocation_spec("R1")
               and manifest["recipe"] == prepared["recipe"] == q0.recipe_for("R1")
               and manifest["config"]["allocation"] == prepared["allocation"], "only original R1 allocation")
    q0.require(read_json(root / "PREPARED.json") == dict(manifest_sha256=files["manifest.json"], prepared_sha256=files["prepared.json"])
               and manifest["prepared_sha256"] == q0.digest(prepared), "original preparation seal")
    q0.require(tuple(resource["stages"]) == STAGES and resource["gpu_release_verified"] is True
               and resource["version"] == q0.VERSION and resource["allocation"] == prepared["allocation"]
               and finalized["evidence_durable_unix"] < started["deadline"]
               and finalized["elapsed_seconds"] < q0.MAX_SECONDS
               and "FINALIZATION_ABORT.json" not in files and "FAILED.json" in files, "original finalized release and nine stages")
    primary = read_json(root / "reduction.json")
    q0.require(primary["candidate"]["label"] == "NONREPORTABLE_RUNTIME_ABORT"
               and primary["scientific_claim"] is False, "original primary remains abort")
    failed_prefix = "stages/" + FAILED_STAGE + "/"
    q0.require(not any(name.startswith(failed_prefix) and name != failed_prefix + "CLAIMED.json" for name in files),
               "failed stage must have no load/readout/completion")
    log = (root / "logs" / (FAILED_STAGE + ".log")).read_text()
    q0.require(all(text in log for text in ("gpu_identity", "TimeoutExpired", "--query-gpu=uuid,name,driver_version"))
               and re.search(r"timed out after 15(?:\.0)? seconds", log),
               "specific pre-load identity-query timeout chronology")
    failed_cleanup = read_json(root / "logs" / (FAILED_STAGE + ".cleanup.json"))
    failed_claim = read_json(root / "stages" / FAILED_STAGE / "CLAIMED.json")
    q0.require(failed_cleanup["pid"] == failed_claim["identity"]["pid"]
               and failed_cleanup["device"] == manifest["config"]["gpu_uuid"]
               and all(failed_cleanup[key] is True for key in
                       ("owned_group_empty", "gpu_processes_absent", "reservation_release_verified")),
               "failed original worker released")
    successful, receipts = {}, {}
    previous_finish = started["started"]
    process_ids, load_ids = set(), set()
    for sequence, stage in enumerate(STAGES):
        job, done, receipt = stage_data(root, stage, manifest, prepared, started)
        q0.require(job["ticket"]["sequence"] == sequence and job["prior_receipts"] == receipts
                   and receipt["start"] >= previous_finish, "original serial receipt order")
        identity = (receipt["pid"], receipt["process_start"])
        q0.require(identity not in process_ids and receipt["load_id"] not in load_ids, "original fresh process identities")
        process_ids.add(identity)
        load_ids.add(receipt["load_id"])
        previous_finish = receipt["finish"]
        receipts[stage + ".json"] = files["receipts/" + stage + ".json"]
        successful[stage] = done
        if job["ticket"]["kind"] == "eval" and job["ticket"]["arm"] != "OFF":
            fit_stage = STAGES[2] if job["ticket"]["arm"] == "P_AUTH" else STAGES[6]
            q0.require(job["adapter"] == successful[fit_stage]["result"]["snapshots"][str(job["ticket"]["snapshot"])],
                       "historical readout belongs to saved fit snapshot")
    with q0.tensor_store(root):
        for arm, stage in (("P_AUTH", STAGES[2]), (STATE, STAGES[6])):
            q0.validate_fit(successful[stage]["result"], prepared, dict(arm=arm, diagnostic_only=False),
                            successful[STAGES[0]]["result"]["initial"], q0.PRODUCTION_POLICY)
    failed_job = read_json(root / "jobs" / (FAILED_STAGE + ".json"))
    ticket = failed_job["ticket"]
    q0.require(ticket["ticket_sha256"] == q0.digest({key: value for key, value in ticket.items() if key != "ticket_sha256"})
               and ticket["sequence"] == 9 and ticket["kind"] == "eval" and ticket["arm"] == STATE
               and ticket["snapshot"] == 128 and ticket["prepared_sha256"] == q0.digest(prepared)
               and failed_job["prior_receipts"] == receipts
               and failed_job["manifest_sha256"] == files["manifest.json"]
               and failed_job["started_sha256"] == files["STARTED.json"], "missing final job binding")
    adapter = successful[STAGES[6]]["result"]["snapshots"]["128"]
    q0.require(failed_job["adapter"] == adapter
               and adapter["path"] == "stages/06_fit_P_DERANGED/snapshots/128", "only saved DERANGED128")
    diagnostic, _, _ = q0.historical_helpers()
    adapter_path = confined(root, adapter["path"])
    q0.require(diagnostic.w0.tree_hash(adapter_path) == adapter["adapter_sha256"], "complete saved adapter bytes")
    return dict(original_root=str(root), files=files, adapter=adapter, custody_sha256=custody_sha256,
                original_primary_label="NONREPORTABLE_RUNTIME_ABORT", allocation=prepared["allocation"],
                campaign_sha256=prepared["campaign_sha256"])


def prepare(out, original, custody_path, custody_sha256, config, *, seal_sha256, finalized_sha256, joined=False):
    pins = source_pins()
    admission = admit_original(original, custody_path, custody_sha256, seal_sha256=seal_sha256, finalized_sha256=finalized_sha256)
    manifest, prepared, _ = q0.native_verify(admission["original_root"])
    q0.validate_native_config(config)
    allowed = {"gpu_uuid", "lease_end_unix", "lease_cutoff_unix", "builder_preflight_reference", "approved_intake"}
    q0.require({key: value for key, value in config.items() if key not in allowed}
               == {key: value for key, value in manifest["config"].items() if key not in allowed},
               "same original node/model/tokenizer/environment and learner")
    q0.native_input_pins(config, manifest["public_binding"])
    root = Path(out).resolve()
    protected = [Path(admission["original_root"]), q0.repository(), Path(config["model_path"]).resolve(),
                 Path(config["tokenizer_path"]).resolve()]
    q0.require(root.parent.is_dir() and not root.exists()
               and all(not root.is_relative_to(path) and not path.is_relative_to(root) for path in protected),
               "fresh disjoint supplemental output")
    requests = q0.request_inventory(prepared, STATE, SNAPSHOT)
    plan = dict(version=VERSION, scope=SCOPE, config=config, source_pins=pins, admission=admission,
                prepared_sha256=q0.digest(prepared), requests_sha256=q0.digest(requests), joined_diagnostic=bool(joined),
                seconds_cap=MAX_SECONDS, cleanup_seconds=CLEANUP_SECONDS, collection_seconds=COLLECTION_SECONDS,
                identity_query_seconds=IDENTITY_SECONDS, attempts=1, updates=0, state=STATE, snapshot=SNAPSHOT)
    root.mkdir()
    (root / "custody.json").write_bytes(Path(custody_path).read_bytes())
    for name, value in (("manifest.json", plan), ("prepared.json", prepared), ("requests.json", requests)):
        q0.write_once(root, name, value)
    q0.write_once(root, "PREPARED.json", {name: q0.file_hash(root / name) for name in
                                         ("manifest.json", "prepared.json", "requests.json", "custody.json")})
    return plan


def verify(root):
    root = Path(root).resolve(strict=True)
    q0.require(read_json(root / "PREPARED.json") == {name: q0.file_hash(root / name) for name in
               ("manifest.json", "prepared.json", "requests.json", "custody.json")}, "supplement preparation seal")
    plan = read_json(root / "manifest.json")
    q0.require(plan["version"] == VERSION and plan["scope"] == SCOPE and plan["source_pins"] == source_pins()
               and (plan["seconds_cap"], plan["cleanup_seconds"], plan["collection_seconds"], plan["identity_query_seconds"],
                    plan["attempts"], plan["updates"], plan["state"], plan["snapshot"])
               == (3600, 45, 180, 30, 1, 0, STATE, 128), "supplement fixed source/scope/profile")
    admission = admit_original(plan["admission"]["original_root"], root / "custody.json", plan["admission"]["custody_sha256"],
                               seal_sha256=plan["admission"]["files"]["SEAL.json"],
                               finalized_sha256=plan["admission"]["files"]["FINALIZED.json"])
    q0.require(admission == plan["admission"], "original evidence changed")
    original, prepared, tokenizer = q0.native_verify(admission["original_root"])
    allowed = {"gpu_uuid", "lease_end_unix", "lease_cutoff_unix", "builder_preflight_reference", "approved_intake"}
    q0.require({key: value for key, value in plan["config"].items() if key not in allowed}
               == {key: value for key, value in original["config"].items() if key not in allowed}, "recovery config drift")
    q0.native_input_pins(plan["config"], original["public_binding"])
    q0.require(q0.digest(prepared) == plan["prepared_sha256"] and prepared == read_json(root / "prepared.json")
               and q0.request_inventory(prepared, STATE, SNAPSHOT) == read_json(root / "requests.json")
               and q0.digest(read_json(root / "requests.json")) == plan["requests_sha256"], "unaltered original requests")
    return plan, prepared, tokenizer


def gpu_identity_30s(config):
    q0.require(q0.hashlib.sha256(platform.node().encode()).hexdigest() == config["node"], "wrong recovery node")
    command = ["nvidia-smi", "-i", config["gpu_uuid"], "--query-gpu=uuid,name,driver_version", "--format=csv,noheader,nounits"]
    began = time.time()
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    rows = [[field.strip() for field in line.split(",")] for line in result.stdout.splitlines() if line.strip()]
    q0.require(len(rows) == 1 and len(rows[0]) == 3, "single recovery GPU identity")
    uuid, name, driver = rows[0]
    q0.require(uuid == config["gpu_uuid"] and name in ("NVIDIA A40", "A40") and driver == config["driver_version"],
               "pinned recovery A40 GPU/driver")
    return dict(node=config["node"], gpu_uuid=uuid, gpu_name=name, driver_version=driver, command=command,
                timeout_seconds=30, started=began, finished=time.time(), stdout=result.stdout)


def load_snapshot(plan, prepared):
    diagnostic, _, _ = q0.historical_helpers()
    config = plan["config"]
    diagnostic.w0.assert_gpu_idle(config)
    torch = q0.configure_worker_torch(diagnostic, config, prepared)
    model = diagnostic.w0.load_hf_model(config, torch)
    q0.require(not diagnostic.w0.lora_tensors(model), "fresh base without old adapter")
    adapter = plan["admission"]["adapter"]
    path = confined(Path(plan["admission"]["original_root"]), adapter["path"])
    q0.require(diagnostic.w0.tree_hash(path) == adapter["adapter_sha256"], "saved adapter changed before loading")
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, str(path), is_trainable=False, local_files_only=True)
    actual = diagnostic.w0.tensor_digest(diagnostic.w0.lora_tensors(model))
    q0.require(actual == adapter["lora_sha256"], "actual saved LoRA tensor identity")
    model.requires_grad_(False)
    model.eval()
    return model, actual


def worker(out, *, allow_gpu=False):
    q0.require(allow_gpu is True, "worker requires --allow-gpu")
    root = Path(out).resolve(strict=True)
    started = read_json(root / "STARTED.json")
    job = read_json(root / "job.json")
    q0.require(job["started_sha256"] == q0.file_hash(root / "STARTED.json")
               and job["manifest_sha256"] == q0.file_hash(root / "manifest.json")
               and job["controller"] == q0.process_identity(os.getppid())
               and job["deadline"] == started["deadline"] - CLEANUP_SECONDS, "new live parent/job/deadline")
    q0.write_once(root, "CLAIMED.json", dict(identity=q0.process_identity(os.getpid()), timestamp=time.time()))
    budget = q0.Budget(started["started"], job["deadline"], clock=time.time)
    plan, prepared, tokenizer = verify(root)
    budget.check()
    q0.require(job["deadline"] - time.time() > IDENTITY_SECONDS, "identity query needs bounded remaining time")
    hardware = gpu_identity_30s(plan["config"])
    budget.check()
    model, lora_sha256 = load_snapshot(plan, prepared)
    budget.check()
    load = dict(identity=q0.process_identity(os.getpid()), job_sha256=q0.file_hash(root / "job.json"),
                manifest_sha256=q0.file_hash(root / "manifest.json"), source_pins=plan["source_pins"],
                prepared_sha256=plan["prepared_sha256"], requests_sha256=plan["requests_sha256"],
                adapter=plan["admission"]["adapter"], actual_lora_sha256=lora_sha256,
                allocation=prepared["allocation"], hardware=hardware, loaded=time.time())
    q0.write_once(root, "LOAD.json", load)
    events = []
    (root / "events").mkdir()

    def emit(name, payload):
        budget.check()
        q0.require(name == "readout", "no training event allowed")
        path = f"{len(events):04d}.json"
        q0.write_once(root / "events", path, payload)
        events.append(dict(path=path, sha256=q0.file_hash(root / "events" / path)))

    with q0.native_forward_counter(model) as counters:
        records = q0.evaluate(model, prepared, STATE, SNAPSHOT, tokenizer, q0.native_generate, budget, emit)
    budget.check()
    diagnostic, _, _ = q0.historical_helpers()
    path = confined(Path(plan["admission"]["original_root"]), plan["admission"]["adapter"]["path"])
    q0.require(diagnostic.w0.tree_hash(path) == plan["admission"]["adapter"]["adapter_sha256"]
               and source_pins() == plan["source_pins"], "post-readout source/adapter custody")
    done = dict(version=VERSION, load=load, records=records, events=events, counters=dict(counters),
                updates=0, training_forwards=0, finished=time.time())
    q0.write_once(root, "DONE.json", done)
    return dict(status="CAPTURED_NOT_RELEASED", records=len(records))


def joined_scores(plan, prepared, current, tokenizer):
    original = Path(plan["admission"]["original_root"])
    off = q0.indexed_readout(prepared, read_json(original / "stages" / STAGES[1] / "DONE.json")["result"], "OFF", 0, tokenizer)
    auth = q0.indexed_readout(prepared, read_json(original / "stages" / STAGES[5] / "DONE.json")["result"], "P_AUTH", 128, tokenizer)
    cells = {arm: q0.cell_gates(prepared, records, off, arm, q0.PRODUCTION_POLICY)
             for arm, records in (("P_AUTH", auth), (STATE, current))}
    complements, wrong_root = dict(exact=0, held=0), 0
    for row in prepared["rows"]:
        first, second = auth[row["id"]]["identity"], current[row["id"]]["identity"]
        opposite = {first, second} == {"MEM2REG", "GVN"}
        if row["panel"] in complements:
            complements[row["panel"]] += opposite and first == ("MEM2REG", "GVN")[q0.target(row, "P_AUTH")]
        elif row["panel"] == "wrong_root":
            wrong_root += opposite
    passed = all(cell["passed"] for cell in cells.values()) and complements["exact"] >= 112 and complements["held"] >= 48 and wrong_root <= 3
    return dict(scope="POST_ABORT_JOINED_DIAGNOSTIC_ENDPOINT_NOT_ORIGINAL_PRIMARY", endpoint_passed=passed,
                cells=cells, complements=complements, complement_denominators=dict(exact=128, held=64),
                wrong_root_opposites=wrong_root, wrong_root_denominator=64,
                origins={"OFF": plan["admission"]["files"]["stages/" + STAGES[1] + "/DONE.json"],
                         "P_AUTH": plan["admission"]["files"]["stages/" + STAGES[5] + "/DONE.json"],
                         STATE: "SUPPLEMENT_DONE_SHA256_IN_REPORT"})


def candidate_report(root, plan, prepared, tokenizer):
    resource = read_json(root / "RESOURCE.json")
    base = dict(version=VERSION, scope=SCOPE, original_primary_label="NONREPORTABLE_RUNTIME_ABORT",
                original_seal_sha256=plan["admission"]["files"]["SEAL.json"],
                original_reduction_sha256=plan["admission"]["files"]["reduction.json"],
                custody_sha256=plan["admission"]["custody_sha256"], manifest_sha256=q0.file_hash(root / "manifest.json"),
                original_primary_changed=False, primary_three_root_complete=False, scientific_claim=False,
                resource=resource, joined_diagnostic=None)
    if (root / "FAILED.json").exists():
        return dict(base, status="SUPPLEMENT_ABORT", failures=read_json(root / "FAILED.json"))
    started, job, done, claimed = [read_json(root / name) for name in ("STARTED.json", "job.json", "DONE.json", "CLAIMED.json")]
    load = done["load"]
    cleanup = read_json(root / "worker.cleanup.json")
    process = read_json(root / "worker.process.json")
    q0.require(done["version"] == VERSION and done["updates"] == done["training_forwards"] == 0
               and load == read_json(root / "LOAD.json") and load["identity"] == claimed["identity"], "readout-only actual load")
    q0.require(load["manifest_sha256"] == job["manifest_sha256"] == base["manifest_sha256"]
               and load["job_sha256"] == q0.file_hash(root / "job.json")
               and job["started_sha256"] == q0.file_hash(root / "STARTED.json")
               and job["controller"] == started["controller"]
               and load["source_pins"] == plan["source_pins"]
               and load["prepared_sha256"] == plan["prepared_sha256"]
               and load["requests_sha256"] == plan["requests_sha256"]
               and load["adapter"] == plan["admission"]["adapter"]
               and load["actual_lora_sha256"] == load["adapter"]["lora_sha256"]
               and load["allocation"] == prepared["allocation"], "supplement plan/load/adapter binding")
    identity = load["identity"]
    q0.require(identity["pid"] == identity["pgid"] == identity["session"] == resource["worker_pid"]
               == process["pid"] == process["pgid"] == cleanup["pid"]
               and identity["ppid"] == started["controller"]["pid"]
               and identity["start_ticks"] > 0 and process["device"] == cleanup["device"] == plan["config"]["gpu_uuid"]
               and cleanup["owned_group_empty"] is True and cleanup["gpu_processes_absent"] is True
               and cleanup["reservation_release_verified"] is True and resource["gpu_release_verified"] is True,
               "actual supplemental process exit/release")
    hardware = load["hardware"]
    q0.require(hardware["timeout_seconds"] == 30 and hardware["node"] == plan["config"]["node"]
               and hardware["gpu_uuid"] == plan["config"]["gpu_uuid"]
               and hardware["driver_version"] == plan["config"]["driver_version"]
               and hardware["gpu_name"] in ("A40", "NVIDIA A40"), "30s identity receipt")
    q0.require(started["started"] <= claimed["timestamp"] <= hardware["started"] <= hardware["finished"]
               <= load["loaded"] <= done["finished"] <= resource["finished"] < started["deadline"]
               and done["finished"] < job["deadline"] == started["deadline"] - CLEANUP_SECONDS
               and started["deadline"] == min(started["started"] + MAX_SECONDS, plan["config"]["lease_cutoff_unix"])
               and resource["seconds_cap"] == MAX_SECONDS and 0 <= resource["elapsed_seconds"] < MAX_SECONDS,
               "supplement clock and resource limits")
    event_records = []
    q0.require(len(done["events"]) == 584 and len({event["path"] for event in done["events"]}) == 584, "all584 raw events")
    for index, event in enumerate(done["events"]):
        q0.require(event["path"] == f"{index:04d}.json"
                   and q0.file_hash(root / "events" / event["path"]) == event["sha256"], "ordered raw event receipt")
        event_records.append(read_json(root / "events" / event["path"]))
    q0.require(event_records == done["records"] and len(list((root / "events").iterdir())) == 584,
               "complete event/result barrier")
    expected = q0.request_inventory(prepared, STATE, SNAPSHOT)
    q0.require([{key: value for key, value in record.items() if key != "output"} for record in done["records"]] == expected,
               "original request order unchanged")
    current = q0.indexed_readout(prepared, done["records"], STATE, SNAPSHOT, tokenizer)
    tokens = sum(len(record["output"]["generated_ids"]) for record in done["records"] if record["operation"] == "generate")
    q0.require(done["counters"] == dict(natural_prefix_forwards=288, model_forward_calls=288 + tokens), "actual readout forward counts")
    report = dict(base, status="SUPPLEMENT_READOUT_COMPLETE", done_sha256=q0.file_hash(root / "DONE.json"),
                  records=584, prefix_readouts=288, generations=296, generated_tokens=tokens,
                  updates=0, training_forwards=0, counters=done["counters"])
    if plan["joined_diagnostic"]:
        report["joined_diagnostic"] = joined_scores(plan, prepared, current, tokenizer)
        report["joined_diagnostic"]["origins"][STATE] = report["done_sha256"]
    return report


def execute(out, *, allow_gpu=False):
    q0.require(allow_gpu is True, "execute requires --allow-gpu")
    root = Path(out).resolve(strict=True)
    q0.require(set(q0.inventory(root)) == {"manifest.json", "prepared.json", "requests.json", "custody.json", "PREPARED.json"},
               "fresh supplement; no resume or retry")
    began, mono = time.time(), time.monotonic()
    plan = read_json(root / "manifest.json")
    deadline = min(began + MAX_SECONDS, plan["config"]["lease_cutoff_unix"])
    started = dict(started=began, deadline=deadline, controller=q0.process_identity(os.getpid()))
    q0.write_once(root, "STARTED.json", started)
    failures, worker_pid, released = [], None, False
    prepared = tokenizer = None
    diagnostic, supervisor, _ = q0.historical_helpers()
    try:
        plan, prepared, tokenizer = verify(root)
        q0.require(time.time() + MAX_SECONDS - (time.monotonic() - mono) + COLLECTION_SECONDS <= plan["config"]["lease_cutoff_unix"],
                   "full supplement and separate collection window")
        q0.require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["config"]["gpu_uuid"]
                   and os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "explicit reserved recovery environment")
        diagnostic.w0.assert_output_fds_outside_run(root)
        diagnostic.w0.assert_output_fds_outside_run(Path(plan["admission"]["original_root"]))
        job = dict(controller=started["controller"], manifest_sha256=q0.file_hash(root / "manifest.json"),
                   started_sha256=q0.file_hash(root / "STARTED.json"), deadline=deadline - CLEANUP_SECONDS)
        q0.write_once(root, "job.json", job)
        remaining = min(job["deadline"] - time.time(), MAX_SECONDS - CLEANUP_SECONDS - (time.monotonic() - mono))
        q0.require(remaining > IDENTITY_SECONDS, "remaining supplement worker budget")
        command = [sys.executable, "-B", "-m", "gpu.astra_q0_readout_supplement", "worker", "--out", str(root), "--allow-gpu"]
        with q0.controller_termination():
            worker_pid = supervisor.run_worker(command, log_path=root / "worker.log", timeout=remaining, device=plan["config"]["gpu_uuid"])
        verify(root)
    except BaseException as error:
        failures.append(dict(type=type(error).__name__, reason=str(error)))
    try:
        released = supervisor.gpu_processes_absent(plan["config"]["gpu_uuid"])
        q0.require(released, "supplement GPU release unverified")
    except BaseException as error:
        failures.append(dict(type=type(error).__name__, reason=str(error)))
    if time.time() >= deadline or time.monotonic() - mono >= MAX_SECONDS:
        failures.append(dict(type="Deadline", reason="supplement controller budget exhausted"))
    resource = dict(worker_pid=worker_pid, gpu_release_verified=released, finished=time.time(),
                    elapsed_seconds=time.monotonic() - mono, seconds_cap=MAX_SECONDS, collection_seconds=COLLECTION_SECONDS)
    q0.write_once(root, "RESOURCE.json", resource)
    if failures:
        q0.write_once(root, "FAILED.json", failures)
    try:
        report = candidate_report(root, plan, prepared, tokenizer)
    except BaseException as error:
        q0.require(not failures, "failed supplement reduction")
        q0.write_once(root, "FAILED.json", [dict(type=type(error).__name__, reason=str(error))])
        report = candidate_report(root, plan, prepared, tokenizer)
    q0.write_once(root, "REPORT.json", report)
    q0.write_once(root, "SEAL.json", dict(version=VERSION, files=q0.durable_inventory(root), status="CANDIDATE_PENDING_FINALIZATION"))
    q0.sync_directory(root)
    finalized = dict(seal_sha256=q0.file_hash(root / "SEAL.json"), finished=time.time(), elapsed_seconds=time.monotonic() - mono)
    q0.write_once(root, "FINALIZED.json", finalized)
    q0.sync_directory(root)
    publication = None
    if time.time() >= deadline or time.monotonic() - mono >= MAX_SECONDS:
        publication = dict(seal_sha256=q0.file_hash(root / "SEAL.json"), finalized_sha256=q0.file_hash(root / "FINALIZED.json"),
                           observed=time.time(), elapsed_seconds=time.monotonic() - mono)
        q0.write_once(root, "PUBLICATION_ABORT.json", publication)
        q0.sync_directory(root)
    return effective_report(report, finalized, started, publication)


def effective_report(report, finalized, started, publication=None):
    if not (math.isfinite(finalized["finished"]) and math.isfinite(finalized["elapsed_seconds"])
            and finalized["finished"] < started["deadline"] and finalized["elapsed_seconds"] < MAX_SECONDS):
        report = dict(report, status="SUPPLEMENT_ABORT", joined_diagnostic=None, finalization_failure="supplement durable publication deadline")
    if publication is not None:
        q0.require(publication["observed"] >= started["deadline"] or publication["elapsed_seconds"] >= MAX_SECONDS,
                   "late publication witness")
        report = dict(report, status="SUPPLEMENT_ABORT", joined_diagnostic=None, finalization_failure="supplement publication deadline")
    return dict(report=report, report_sha256=q0.digest(report), finalized=finalized, publication=publication)


def replay(out):
    root = Path(out).resolve(strict=True)
    seal, finalized = read_json(root / "SEAL.json"), read_json(root / "FINALIZED.json")
    q0.require(seal["version"] == VERSION and seal["status"] == "CANDIDATE_PENDING_FINALIZATION"
               and {name: value for name, value in q0.inventory(root).items() if name not in ("SEAL.json", "FINALIZED.json", "PUBLICATION_ABORT.json")} == seal["files"]
               and finalized["seal_sha256"] == q0.file_hash(root / "SEAL.json"), "supplement complete sealed custody")
    plan, prepared, tokenizer = verify(root)
    report = candidate_report(root, plan, prepared, tokenizer)
    q0.require(q0.canonical(report) == (root / "REPORT.json").read_bytes(), "exact supplementary replay")
    resource = report["resource"]
    q0.require(finalized["finished"] >= resource["finished"] and finalized["elapsed_seconds"] >= resource["elapsed_seconds"],
               "finalization follows resource completion")
    publication = read_json(root / "PUBLICATION_ABORT.json") if (root / "PUBLICATION_ABORT.json").exists() else None
    if publication is not None:
        q0.require(publication["seal_sha256"] == q0.file_hash(root / "SEAL.json")
                   and publication["finalized_sha256"] == q0.file_hash(root / "FINALIZED.json"), "publication witness custody")
    return effective_report(report, finalized, read_json(root / "STARTED.json"), publication)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "execute", "worker", "replay"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--original-root")
    parser.add_argument("--custody")
    parser.add_argument("--custody-sha256")
    parser.add_argument("--original-seal-sha256")
    parser.add_argument("--original-finalized-sha256")
    parser.add_argument("--config")
    parser.add_argument("--joined-diagnostic", action="store_true")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        q0.require(all((args.original_root, args.custody, args.custody_sha256, args.original_seal_sha256,
                        args.original_finalized_sha256, args.config)), "original-root/custody/seal/finalized pins/config required")
        result = prepare(args.out, args.original_root, args.custody, args.custody_sha256, read_json(args.config),
                         seal_sha256=args.original_seal_sha256, finalized_sha256=args.original_finalized_sha256,
                         joined=args.joined_diagnostic)
    elif args.command == "replay":
        result = replay(args.out)
    else:
        result = (execute if args.command == "execute" else worker)(args.out, allow_gpu=args.allow_gpu)
    print(q0.canonical(result).decode(), end="")


if __name__ == "__main__":
    main()
