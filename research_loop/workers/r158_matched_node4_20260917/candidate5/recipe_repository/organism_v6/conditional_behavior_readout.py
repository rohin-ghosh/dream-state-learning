"""Fixed root0 conditional readouts; no fits, promotion, or L1/Q0/H1 verdict.

prepare is local-tokenizer CPU work. run requires Main's explicit GPU allocation.
Each state/phase has a fresh root/process and reuses the existing supervisor.
reduce is replay only; missing or invalid evidence returns INCOMPLETE.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import threading
import time

from . import conditional_behavior_corpus as corpus
from . import fundamental_teaching_corpus as fundamental
from . import fundamental_teaching_readout as generic
from . import rulegame_parenting_diagnostic as base
from . import semantic_carrier_diagnostic as carrier


STATES = ("OFF", "AUTH", "DERANGED")
PHASES = ("generate", "score")
SETTINGS = dict(temperature=0.0, seed=20260912, max_tokens=64)
PROSPECT_CONTRAST = "dual-map-belief-endpoints-v2"
ASSAY_VERSION = "conditional-dual-map-fixed-endpoints-v2-20260912"
MATERIAL_PINS = {
    "candidate.json": "5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c",
    "AUTH.json": "344ec17779696b184468d96ce26ef89e8d3bd0cb5b8dbfde84a4b8dc1c437d48",
    "DERANGED.json": "060255b11551b55b20d39f91301cc4e0362134af321bc740134b86e3ca6d511d",
}
TOKEN_TOTALS = dict(input=11248, target=1888)
RESOURCE_BUDGET = dict(total_a40_seconds=5400, fit_pair_seconds=1200,
                       readout_workers=6, seconds_per_worker=600, margin_seconds=600,
                       scope="Main enforces fits+readouts+cleanup total; ceiling, not throughput prediction")
LIMITS = ("One root0 authored diagnostic; known diagnostic controls, eight unique copy prompts. "
          "No confirmation, child experience, clean lineage, composition, Q0, L1 or H1 verdict. "
          "OFF is shared, not independent observations per comparison. Local hashes do not prove origin.")


def sources():
    names = ("conditional_behavior_readout.py", "conditional_behavior_corpus.py", "train_adapter_v3.py",
             "fundamental_teaching_readout.py", "fundamental_teaching_corpus.py",
             "semantic_carrier_diagnostic.py", "multikey_writer_gateway_simple.py",
             "writer_interface_calibration.py", "rulegame_parenting_diagnostic.py",
             "run_reasoning_neutral.py", "model_backend.py", "reasoning_neutral_probe.py")
    return {name: base.digest(base.REPO / "organism_v6" / name) for name in names}


def controls():
    indexed = {row["id"]: row for row in fundamental.build_candidate()["eval"]}
    rows = []
    for index in range(16):
        source = indexed[f"eval-addition-{index:03d}"]
        rows.append(dict(id="control-" + source["id"], family="addition", context=source["context"],
                         expected=source["expected"], source=source,
                         source_module="fundamental_teaching_corpus.py"))
    copies = [row for row in carrier.build_items() if row["kind"] == "native_action_copy"]
    base.require(len(copies) == 16 and len({row["prompt"] for row in copies}) == 8, "copy source panel changed")
    for index, source in enumerate(copies):
        rows.append(dict(id=f"control-copy-{index:02d}", family="copy", context=source["prompt"],
                         expected=source["expected"], source=source,
                         source_module="semantic_carrier_diagnostic.py"))
    return rows


def read_material(directory):
    directory = Path(directory).expanduser().resolve(strict=True)
    manifest = base.read(directory / "manifest.json")
    inventory = manifest["files"]
    required = {*MATERIAL_PINS, "recipe.json", "native_audit.json", "teacher_forcing_interface.json"}
    base.require(required <= set(inventory), "incomplete prepared material inventory")
    for name, digest in inventory.items():
        base.require(Path(name).name == name and base.digest(directory / name) == digest, "material file changed")
    base.require(all(inventory[name] == digest for name, digest in MATERIAL_PINS.items()), "not pinned attempt2 material")
    candidate = base.read(directory / "candidate.json")
    corpus.audit_candidate(candidate)
    base.require(candidate["root"] == 0 and candidate["spellings"] ==
                 dict(actions=["dax", "wug"], outcomes=["fep", "nup"]), "root0 attempt2 spellings required")
    recipe = base.read(directory / "recipe.json")
    base.require(recipe == corpus.training_recipe(learning_rate=1e-4, seed=0), "prepared recipe changed")
    native = base.read(directory / "native_audit.json")
    base.require(native["status"] == "NATIVE_TOKEN_MATCH_VERIFIED" and
                 native["candidate_sha256"] == corpus.digest(candidate), "native audit not bound to candidate")
    for name in ("conditional_behavior_corpus.py", "train_adapter_v3.py"):
        base.require(native["source_sha256"][name] == base.digest(base.REPO / "organism_v6" / name),
                     "executed material source differs")
    base.require(native["no_truncation"] is True and native["loss_bearing_padding"] is False,
                 "native loss/truncation contract")
    for arm in corpus.ARMS:
        base.require(base.read(directory / f"{arm}.json") == {"corpus": native["corpora"][arm]},
                     "native training corpus mismatch")
        base.require(native["input_tokens_per_epoch"][arm] == TOKEN_TOTALS["input"] and
                     native["target_tokens_per_epoch"][arm] == TOKEN_TOTALS["target"], "native token totals differ")
    base.require(base.read(directory / "teacher_forcing_interface.json") == corpus.teacher_forcing_interface(candidate),
                 "teacher forcing interface changed")
    return dict(directory=str(directory), inventory=inventory, manifest_sha256=base.digest(directory / "manifest.json"),
                candidate=candidate, recipe=recipe, native=native)


def load_tokenizer(model, native):
    model = Path(model)
    pins = native["tokenizer_file_hashes"]
    base.require({"config.json", "tokenizer.json", "tokenizer_config.json"} <= set(pins), "missing tokenizer pins")
    for name, digest in pins.items():
        base.require(Path(name).name == name and base.digest(model / name) == digest, "tokenizer pin changed")
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(model), local_files_only=True, trust_remote_code=False)


def audit_encoding(material, tokenizer):
    actual = corpus.audit_tokenizer(material["candidate"], tokenizer)
    for field in ("corpora", "rows", "optimizer_update_rows", "input_tokens_per_epoch", "target_tokens_per_epoch"):
        base.require(actual[field] == material["native"][field], f"native {field} differs from prepared audit")


def fit_contract(adapter, state, model, material):
    base.require(state in STATES, "unknown state")
    if state == "OFF":
        base.require(adapter is None, "OFF must not have an adapter")
        return {}
    base.require(adapter is not None, "trained state requires saved adapter")
    adapter = Path(adapter)
    manifest = base.read(adapter / "train_manifest.json")
    base.require((adapter / "DONE").is_file() and manifest["empty"] is False and
                 "warm_start" not in manifest and not manifest["config"].get("init_adapter"), "fresh completed fit required")
    base.require(all(manifest["config"].get(key) == value for key, value in material["recipe"].items()), "fit recipe changed")
    base.require(Path(manifest["base_model"]).resolve() == Path(model).resolve(), "fit base differs")
    base.require(manifest["steps"] == manifest["micro_batches"] == 128 and manifest["epochs_run"] == 4 and
                 manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "incomplete fit counts")
    recorded = manifest["corpus"]
    base.require(recorded["sha256"] == material["inventory"][f"{state}.json"] and
                 recorded["n_items"] == recorded["n_encoded"] == 128 and recorded["n_skipped_no_target"] == 0,
                 "fit corpus mismatch")
    base.require(all(manifest["truncation"][key] == 0 for key in
                     ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit dropped material")
    base.require(manifest["tokens"]["total"] == TOKEN_TOTALS["input"] and
                 manifest["tokens"]["target"] == TOKEN_TOTALS["target"] and
                 manifest["tokens"]["context"] == TOKEN_TOTALS["input"] - TOKEN_TOTALS["target"] and
                 manifest["train_tokens_seen"] == 4 * TOKEN_TOTALS["input"], "fit token counts differ")
    config = base.read(adapter / "adapter_config.json")
    base.require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == .05 and
                 set(config["target_modules"]) == set(corpus.trainer.ALL_PROJ) and
                 config.get("bias", "none") == "none" and not config.get("modules_to_save") and
                 not config.get("use_dora", False) and not config.get("use_rslora", False) and
                 not config.get("rank_pattern") and not config.get("alpha_pattern") and
                 not config.get("layers_to_transform"), "saved adapter config differs")
    files = base.tree_hashes(adapter)
    base.require("adapter_model.safetensors" in files and "adapter_model.bin" not in files, "one saved adapter required")
    return files


def generation_requests(candidate, state):
    base.require(state in STATES, "unknown state")
    rows = []
    for split, cases in (("train", candidate["train"]["AUTH"]), ("dev", candidate["dev"]), ("control", controls())):
        for case in cases:
            rows.append(dict(call_id=f"{len(rows):04d}", case_id=case["id"], split=split,
                             role=split, arm=state, prompt=case["context"], **SETTINGS))
    base.require(len(rows) == len({row["case_id"] for row in rows}) == 224, "complete unique generation panel required")
    return rows


def render(tokenizer, text):
    rendered = tokenizer.apply_chat_template([dict(role="user", content=text)], tokenize=False, add_generation_prompt=True)
    prefix = tokenizer.encode(rendered, add_special_tokens=False)
    base.require(prefix, "empty input prefix")
    return rendered, prefix


def native_generation(tokenizer, requests):
    result = []
    for request in requests:
        rendered, prefix = render(tokenizer, request["prompt"])
        base.require(len(prefix) + SETTINGS["max_tokens"] <= base.MAX_MODEL_LEN, "native context overflow")
        result.append(dict(call_id=request["call_id"], rendered_prompt=rendered, prompt_token_ids=prefix))
    return result


def contrast_candidates(candidate, *, prospect_contrast):
    base.require(prospect_contrast == PROSPECT_CONTRAST,
                 "score preparation requires explicit prospect_contrast='dual-map-belief-endpoints-v2'")
    indexed = {row["id"]: row for row in candidate["dev"]}
    result = {}
    for family in ("belief", "outcome"):
        maps = corpus.ARMS if family == "belief" else ("AUTH",)
        for endpoints in candidate["twins"]["dev"][family]:
            choices = [dict(candidate_id=f"{arm}_X{index}", text=corpus.response_text(indexed[case_id], arm),
                            source_case_id=case_id, source_map=arm)
                       for arm in maps for index, case_id in enumerate(endpoints)]
            base.require(len({choice["text"] for choice in choices}) == len(choices), "distinct complete candidates required")
            for case_id in endpoints:
                result[case_id] = choices
    return result


def candidate_pairs(candidate, choices):
    indexed = {row["id"]: row for row in candidate["dev"]}
    endpoints = [choice["source_case_id"] for choice in choices[:2]]
    pairs = {}
    for arm in corpus.ARMS:
        pairs[arm] = []
        for case_id in endpoints:
            matches = [choice["candidate_id"] for choice in choices
                       if choice["text"] == corpus.response_text(indexed[case_id], arm)]
            base.require(len(matches) == 1, "map endpoint must identify exactly one scored complete candidate")
            pairs[arm].append(matches[0])
    return pairs


def scoring_requests(candidate, state, tokenizer, *, prospect_contrast):
    base.require(state in STATES, "unknown state")
    choices = contrast_candidates(candidate, prospect_contrast=prospect_contrast)
    eos = tokenizer.eos_token_id
    base.require(type(eos) is int and eos >= 0, "native EOS required")
    rows = []
    for case in candidate["dev"]:
        rendered, prefix = render(tokenizer, case["context"])
        candidates = []
        for choice in choices[case["id"]]:
            text = choice["text"]
            target = tokenizer.encode(text, add_special_tokens=False)
            base.require(target and eos not in target and len(prefix) + len(target) + 1 <= base.MAX_MODEL_LEN,
                         "invalid/overlong complete candidate")
            response = target + [eos]
            candidates.append(dict(**choice, response_ids=response,
                                   input_ids=prefix + response, labels=[-100] * len(prefix) + response))
        rows.append(dict(call_id=f"{len(rows):04d}", case_id=case["id"], role="score", arm=state,
                         assay_version=ASSAY_VERSION, operation=case["operation"],
                         candidate_pairs=candidate_pairs(candidate, choices[case["id"]]),
                         prompt=case["context"], rendered_prompt=rendered,
                         payload=dict(prompt_input_ids=prefix), candidates=candidates))
    base.require(len(rows) == 64, "complete dev likelihood panel required")
    return rows


def prepare(material_path, out, model, model_files, state, phase, adapter, device, lease_end, *,
            tokenizer=None, prospect_contrast=None):
    base.require(state in STATES and phase in PHASES, "unknown state/phase")
    base.require(isinstance(device, str) and re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device), "one device required")
    lease_end = float(lease_end)
    base.require(math.isfinite(lease_end) and lease_end > time.time() + base.WORKER_SECONDS + base.CLEANUP_RESERVE + 10,
                 "insufficient lease for existing supervisor")
    material = read_material(material_path)
    model = str(Path(model).expanduser().resolve(strict=True))
    base.require(model_files == base.model_hashes(model), "model file pins differ")
    adapter = str(Path(adapter).expanduser().resolve(strict=True)) if adapter is not None else None
    adapter_files = fit_contract(adapter, state, model, material)
    tokenizer = tokenizer or load_tokenizer(model, material["native"])
    audit_encoding(material, tokenizer)
    candidate = material["candidate"]
    requests = generation_requests(candidate, state) if phase == "generate" else scoring_requests(
        candidate, state, tokenizer, prospect_contrast=prospect_contrast)
    base.require(phase == "score" or prospect_contrast is None, "likelihood choice applies only to score phase")
    destination = Path(out).expanduser().resolve()
    for source in (Path(model), Path(material["directory"]), *([Path(adapter)] if adapter else [])):
        base.require(destination != source and destination not in source.parents and source not in destination.parents,
                     "output overlaps immutable inputs")
    plan = dict(schema=1, material=material["directory"], material_inventory=material["inventory"],
                material_manifest_sha256=material["manifest_sha256"], candidate_sha256=corpus.digest(candidate),
                source_hashes=sources(), model=model, model_files=model_files, adapter=adapter, adapter_files=adapter_files,
                state=state, phase=phase, device=device, lease_end=lease_end, controls=controls(), requests=requests,
                native_inputs=native_generation(tokenizer, requests) if phase == "generate" else [],
                worker_seconds=base.WORKER_SECONDS, resource_budget=RESOURCE_BUDGET,
                prospect_contrast=prospect_contrast, assay_version=ASSAY_VERSION if phase == "score" else None,
                claim_limits=LIMITS)
    plan["identity"] = base.expected_identity(plan, adapter) if phase == "generate" else dict(
        backend="hf_complete_candidate", model_input=model, adapter_input=adapter, adapter_files=adapter_files)
    root = base.fresh_directory(destination, model)
    base.write_json(root / "plan.json", plan)
    base.write_json(root / "plan.sha256.json", dict(sha256=base.digest(root / "plan.json")))
    return plan


def verify(root, *, tokenizer=None):
    root = Path(root)
    base.require(base.digest(root / "plan.json") == base.read(root / "plan.sha256.json")["sha256"], "plan changed")
    plan = base.read(root / "plan.json")
    base.require(plan["source_hashes"] == sources() and plan["schema"] == 1 and plan["claim_limits"] == LIMITS and
                 plan["worker_seconds"] == base.WORKER_SECONDS and plan["resource_budget"] == RESOURCE_BUDGET, "source/bounds changed")
    material = read_material(plan["material"])
    base.require(plan["material_inventory"] == material["inventory"] and
                 plan["material_manifest_sha256"] == material["manifest_sha256"] and
                 plan["candidate_sha256"] == corpus.digest(material["candidate"]), "prepared material changed")
    base.require(plan["state"] in STATES and plan["phase"] in PHASES and plan["controls"] == controls(), "panel changed")
    base.require(isinstance(plan["device"], str) and re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", plan["device"]) and
                 type(plan["lease_end"]) is float and math.isfinite(plan["lease_end"]), "device/lease changed")
    base.require(base.model_hashes(plan["model"]) == plan["model_files"], "base model bytes changed")
    base.require(fit_contract(plan["adapter"], plan["state"], plan["model"], material) == plan["adapter_files"], "adapter changed")
    tokenizer = tokenizer or load_tokenizer(plan["model"], material["native"])
    audit_encoding(material, tokenizer)
    if plan["phase"] == "generate":
        base.require(plan["prospect_contrast"] is None and plan["assay_version"] is None, "generation likelihood option changed")
        expected = generation_requests(material["candidate"], plan["state"])
        identity = base.expected_identity(plan, plan["adapter"])
        base.require(plan["native_inputs"] == native_generation(tokenizer, expected), "native prefixes changed")
    else:
        base.require(plan["assay_version"] == ASSAY_VERSION, "likelihood assay version changed")
        expected = scoring_requests(material["candidate"], plan["state"], tokenizer,
                                    prospect_contrast=plan["prospect_contrast"])
        identity = dict(backend="hf_complete_candidate", model_input=plan["model"],
                        adapter_input=plan["adapter"], adapter_files=plan["adapter_files"])
        base.require(plan["native_inputs"] == [], "score native input field changed")
    base.require(plan["requests"] == expected and plan["identity"] == identity, "requests/identity changed")
    return plan, material, tokenizer


class HFScorer:
    def __init__(self, plan):
        import torch
        from transformers import AutoModelForCausalLM
        self.torch = torch
        self.model = AutoModelForCausalLM.from_pretrained(plan["model"], local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.bfloat16, attn_implementation="eager")
        if plan["adapter"] is not None:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, plan["adapter"], is_trainable=False)
            base.require(len(self.model.peft_config) == 1, "one scoring adapter required")
        self.model.requires_grad_(False)
        self.model.to("cuda:0")
        self.model.eval()
        self.model.config.use_cache = False

    def score(self, request):
        values = []
        for group in scoring_groups(request):
            result = carrier.score(self.torch, self.model, dict(request, candidates=group))
            values.extend(result["token_logprobs"])
        return dict(token_logprobs=values)

    def close(self):
        del self.model
        self.torch.cuda.empty_cache()
        return True


def scoring_groups(request):
    expected = 4 if request["operation"] == "PROSPECT" else 2
    base.require(request["operation"] in corpus.OPERATIONS and len(request["candidates"]) == expected and
                 request["assay_version"] == ASSAY_VERSION, "versioned candidate count differs")
    return [request["candidates"][offset:offset + 2] for offset in range(0, expected, 2)]


def validate_scores(request, response):
    scoring_groups(request)
    values = response["token_logprobs"]
    base.require(len(values) == len(request["candidates"]), "complete candidate score sequences required")
    for candidate, scores in zip(request["candidates"], values, strict=True):
        base.require(len(scores) == len(candidate["response_ids"]) and
                     all(type(value) in (int, float) and math.isfinite(value) and value <= 0 for value in scores),
                     "invalid/incomplete candidate logprobs")
    base.require(sum(math.exp(sum(scores)) for scores in values) <= 1 + 1e-6, "candidate mass exceeds one")


def capture_scores(plan, path, factory=None):
    path = Path(path)
    (path / "calls").mkdir()
    backend = None
    try:
        backend = (factory or HFScorer)(plan)
        base.write_json(path / "identity.json", dict(backend=plan["identity"], model_files=plan["model_files"],
                                                    adapter_files=plan["adapter_files"]))
        base.write_json(path / "backend.ready.json", dict(pid=os.getpid(), ready=time.monotonic()))
        for request in plan["requests"]:
            stem = path / "calls" / request["call_id"]
            base.write_json(str(stem) + ".request.json", dict(request=request, started=time.monotonic(),
                identity=plan["identity"], prompt_sha256=base.value_hash(request["prompt"])))
            response = backend.score(request)
            base.write_json(str(stem) + ".response.json", dict(response=response, ended=time.monotonic(),
                                                             response_sha256=base.value_hash(response)))
            validate_scores(request, response)
    except BaseException as error:
        base.write_json(path / "failure.json", dict(type=type(error).__name__, error=str(error)))
        raise
    finally:
        closed, cleanup_error = False, None
        try:
            closed = backend.close() if backend is not None else False
        except Exception as error:
            cleanup_error = str(error)
        base.write_json(path / "backend.cleanup.json", dict(closed=closed, error=cleanup_error,
                        scope="owned scoring process; supervisor checks release"))
        base.require(closed is True, "scoring cleanup unverified")
    base.capture_manifest(path)


def worker(root):
    root = Path(root).resolve()
    parent_pid = os.getppid()
    plan, _, _ = verify(root)
    base.require(parent_pid > 1 and base.supervisor.selected_device() == plan["device"], "live supervisor/device required")
    receipt = root / "run" / "worker" / "process.json"
    deadline = time.monotonic() + 5
    while not receipt.exists() and time.monotonic() < deadline:
        time.sleep(.05)
    base.require(base.read(receipt)["pid"] == os.getpid() == os.getpgrp() and os.getppid() == parent_pid, "supervisor ownership required")
    stop = threading.Event()
    deadline = time.monotonic() + base.WORKER_SECONDS

    def interrupted(signum, frame):
        raise RuntimeError(f"worker interrupted by signal {signum}")

    def watch_parent():
        while not stop.wait(.2):
            if os.getppid() != parent_pid or time.monotonic() >= deadline or time.time() >= plan["lease_end"] - 10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return

    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    watcher = threading.Thread(target=watch_parent, daemon=True)
    watcher.start()
    try:
        path = base.fresh_directory(root / "run" / "data", plan["model"])
        if plan["phase"] == "generate":
            generic.capture(plan, path)
        else:
            capture_scores(plan, path)
    finally:
        stop.set()
        watcher.join()
        for number, handler in handlers.items():
            signal.signal(number, handler)


def run(root, *, allow_gpu=False):
    base.require(allow_gpu, "Main allocation and explicit --allow-gpu required")
    root = Path(root).resolve()
    plan, _, _ = verify(root)
    stage = base.fresh_directory(root / "run", plan["model"])
    command = [sys.executable, "-B", "-m", "organism_v6.conditional_behavior_readout", "_worker",
               "--root", str(root), "--allow-gpu"]
    return base.supervise(root, plan, stage / "worker", command, stage / "data" / "calls")


def score_controls(outputs):
    registered = controls()
    base.require(set(outputs) == {row["id"] for row in registered}, "complete controls required")
    rows = []
    for case in registered:
        raw = outputs[case["id"]]
        base.require(isinstance(raw, str), "raw control string required")
        spill = bool(re.search(r"\b(?:PREDICT|COMPARE|POLICY|NEXT)\s*:", raw))
        if case["family"] == "addition":
            scored = generic.score_addition(raw, case["expected"])
            valid, correct = scored["action_valid"], scored["correct_action"]
            exact = raw in (f"ACT: {case['expected']}", f"ACT: {case['expected']}\n")
        else:
            exact = raw in (f"ACT: {case['expected']}", f"ACT: {case['expected']}\n")
            match = re.fullmatch(r"ACT: (-[a-z0-9]+)\n?", raw)
            valid = match is not None and match[1] in carrier.COPY_ACTIONS
            correct = exact
        rows.append(dict(case_id=case["id"], family=case["family"], prompt=case["context"], raw_text=raw,
                         valid=valid, correct=correct, exact=exact, tag_spill=spill))
    families = {}
    for family in ("addition", "copy"):
        subset = [row for row in rows if row["family"] == family]
        groups = defaultdict(list)
        for row in subset:
            groups[row["prompt"]].append(row)
        families[family] = dict(total=16, unique_prompts=len(groups),
            **{key: sum(row[key] for row in subset) for key in ("valid", "correct", "exact", "tag_spill")},
            unique_all_correct=sum(all(row["correct"] for row in group) for group in groups.values()),
            unique_any_spill=sum(any(row["tag_spill"] for row in group) for group in groups.values()))
    return dict(rows=rows, families=families, copied_prompt_executions=16, unique_copy_prompts=8)


def score_generations(candidate, outputs, state):
    expected = generation_requests(candidate, state)
    base.require(set(outputs) == {row["case_id"] for row in expected}, "complete 224 output IDs required")
    primary = {}
    for split in ("train", "dev"):
        selected = {row["case_id"]: outputs[row["case_id"]] for row in expected if row["split"] == split}
        primary[split] = {arm: corpus.score_outputs(candidate, selected, split=split, assigned_arm=arm) for arm in corpus.ARMS}
    control_outputs = {row["case_id"]: outputs[row["case_id"]] for row in expected if row["split"] == "control"}
    return dict(primary=primary, controls=score_controls(control_outputs), actual_generations=224,
                shared_off=state == "OFF", own_map=state if state != "OFF" else None)


def score_interactions(candidate, records, state, *, prospect_contrast):
    base.require(state in STATES, "unknown state")
    choices = contrast_candidates(candidate, prospect_contrast=prospect_contrast)
    indexed = {row["id"]: row for row in candidate["dev"]}
    base.require(set(records) == set(indexed), "complete 64 dev likelihood IDs required")
    totals = {}
    for case_id, record in records.items():
        base.require(set(record) == {choice["candidate_id"] for choice in choices[case_id]} and
                     all(math.isfinite(value) and value <= 0 for value in record.values()),
                     "finite complete candidate totals required")
    for operation, family in (("PROSPECT", "belief"), ("REVISE", "outcome")):
        pairs = []
        for first, second in candidate["twins"]["dev"][family]:
            base.require(choices[first] == choices[second], "fixed candidate strings differ between pair inputs")
            identifiers = candidate_pairs(candidate, choices[first])
            contrasts = {}
            for arm, (first_target, second_target) in identifiers.items():
                contrasts[arm] = (records[first][first_target] - records[first][second_target] -
                                  (records[second][first_target] - records[second][second_target]))
            pairs.append(dict(case_ids=[first, second], candidate_pairs=identifiers, oriented_nats=contrasts))
        oriented = {arm: dict(mean_nats=sum(row["oriented_nats"][arm] for row in pairs) / len(pairs)) for arm in corpus.ARMS}
        for row in oriented.values():
            row["at_least_one_nat"] = row["mean_nats"] >= 1
        totals[operation] = dict(family=family, total=16, pairs=pairs, map_oriented=oriented)
    return dict(operations=totals, candidate_logprob_sums=records, scored_cases=64, candidate_forwards=192,
                assay_version=ASSAY_VERSION,
                orientation="for EACH map, endpoint0-correct minus endpoint1-correct at x0, minus SAME fixed-string difference at x1",
                prospect_contrast=prospect_contrast,
                prospect_note="Four distinct complete candidates: both AUTH endpoints AND both DERANGED endpoints, scored in every state including OFF.",
                aggregate="arithmetic mean of all16 registered pairs per operation; full continuation sums including EOS")


def replay(plan, candidate, path, tokenizer):
    path = Path(path)
    base.require(not (path / "failure.json").exists() and base.read(path / "backend.cleanup.json")["closed"] is True,
                 "capture failed or cleanup unverified")
    base.require(base.read(path / "manifest.json")["files"] == base.tree_hashes(path, ("manifest.json",)), "capture changed")
    base.require(base.read(path / "identity.json") == dict(backend=plan["identity"], model_files=plan["model_files"],
                 adapter_files=plan["adapter_files"]), "capture identity mismatch")
    expected_files = {request["call_id"] + suffix for request in plan["requests"] for suffix in (".request.json", ".response.json")}
    base.require({item.name for item in (path / "calls").iterdir()} == expected_files, "missing/extra raw pairs")
    outputs, records = {}, {}
    cost = dict(requests=0, native_input_tokens=0, native_output_tokens=0, output_token_ceiling=0,
                candidate_forwards=0, scored_target_tokens=0, padded_forward_tokens=0, call_seconds=0.0)
    last_ended = 0.0
    for index, request in enumerate(plan["requests"]):
        stem = path / "calls" / request["call_id"]
        sent, received = base.read(str(stem) + ".request.json"), base.read(str(stem) + ".response.json")
        response = received["response"]
        base.require(sent["request"] == request and sent["identity"] == plan["identity"] and
                     sent["prompt_sha256"] == base.value_hash(request["prompt"]) and
                     received["response_sha256"] == base.value_hash(response), "raw request/response pin mismatch")
        base.require(math.isfinite(sent["started"]) and math.isfinite(received["ended"]) and
                     last_ended <= sent["started"] <= received["ended"], "invalid call timing")
        last_ended = received["ended"]
        cost["requests"] += 1
        cost["call_seconds"] += received["ended"] - sent["started"]
        if plan["phase"] == "generate":
            base.validate_response(request, response)
            native = plan["native_inputs"][index]
            base.require(all(response[field] == native[field] for field in ("rendered_prompt", "prompt_token_ids")), "native input changed")
            text = tokenizer.decode(response["output_token_ids"], skip_special_tokens=True, clean_up_tokenization_spaces=False)
            base.require(text == response["text"], "raw token/text mismatch")
            outputs[request["case_id"]] = response["text"]
            cost["native_input_tokens"] += len(response["prompt_token_ids"])
            cost["native_output_tokens"] += len(response["output_token_ids"])
            cost["output_token_ceiling"] += request["max_tokens"]
        else:
            validate_scores(request, response)
            records[request["case_id"]] = {choice["candidate_id"]: sum(values) for choice, values in
                                          zip(request["candidates"], response["token_logprobs"], strict=True)}
            cost["candidate_forwards"] += len(request["candidates"])
            cost["scored_target_tokens"] += sum(len(row["response_ids"]) for row in request["candidates"])
            cost["native_input_tokens"] += sum(len(row["input_ids"]) for row in request["candidates"])
            cost["padded_forward_tokens"] += sum(2 * max(len(row["input_ids"]) for row in group) for group in scoring_groups(request))
    if plan["phase"] == "generate":
        base.require(base.usage(path) == base.read(path / "usage.json"), "generation usage changed")
    result = score_generations(candidate, outputs, plan["state"]) if plan["phase"] == "generate" else score_interactions(
        candidate, records, plan["state"], prospect_contrast=plan["prospect_contrast"])
    return dict(result=result, cost=cost)


def reduce(root, *, tokenizer=None):
    try:
        root = Path(root).resolve()
        plan, material, tokenizer = verify(root, tokenizer=tokenizer)
        receipt = base.read(root / "run" / "worker" / "supervision.json")
        base.require(all(receipt[key] is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
                     receipt["returncode"] == 0 and receipt["device"] == plan["device"] and
                     math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0, "supervision/release incomplete")
        data = replay(plan, material["candidate"], root / "run" / "data", tokenizer)
        return dict(status="COMPLETE_PHASE", complete=True, root=str(root), state=plan["state"], phase=plan["phase"],
                    plan_sha256=base.digest(root / "plan.json"), material_inventory=material["inventory"],
                    source_hashes=plan["source_hashes"], model_files=plan["model_files"], adapter_files=plan["adapter_files"],
                    reserved_seconds=receipt["reserved_seconds"], resource_budget=RESOURCE_BUDGET,
                    assay_version=plan["assay_version"],
                    **data, supplies_l1_verdict=False, claim_limits=LIMITS)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        return dict(status="INCOMPLETE", complete=False, root=str(root), error=f"{type(error).__name__}: {error}",
                    supplies_l1_verdict=False, claim_limits=LIMITS)


def summarize(reductions):
    try:
        base.require(len(reductions) == 6 and all(row["complete"] for row in reductions), "six complete state/phase reductions required")
        indexed = {(row["state"], row["phase"]): row for row in reductions}
        base.require(set(indexed) == {(state, phase) for state in STATES for phase in PHASES}, "duplicate/missing state phase")
        reference = reductions[0]
        base.require(all(all(row[key] == reference[key] for key in ("material_inventory", "source_hashes", "model_files")) for row in reductions),
                     "states do not share source/material/base")
        for state in STATES:
            base.require(indexed[state, "generate"]["adapter_files"] == indexed[state, "score"]["adapter_files"], "generation/score adapter differs")
            base.require(indexed[state, "score"]["assay_version"] == ASSAY_VERSION, "score assay version differs")
        base.require(indexed["OFF", "generate"]["adapter_files"] == {} and
                     all(indexed[state, "generate"]["adapter_files"] for state in corpus.ARMS), "state adapter identities invalid")
        comparisons = {}
        off = indexed["OFF", "generate"]["result"]
        for state in corpus.ARMS:
            actual = indexed[state, "generate"]["result"]
            comparisons[state] = dict(
                auth_minus_off_semantic={operation: (actual["primary"]["dev"]["AUTH"]["operations"][operation]["auth_joint_semantic"] -
                    off["primary"]["dev"]["AUTH"]["operations"][operation]["auth_joint_semantic"]) / 32 for operation in corpus.OPERATIONS},
                controls={family: {key: dict(delta_count=actual["controls"]["families"][family][key] - off["controls"]["families"][family][key],
                    denominator=16, no_more_than_point05_loss=actual["controls"]["families"][family][key] >= off["controls"]["families"][family][key])
                    for key in ("valid", "correct", "exact")} for family in ("addition", "copy")})
            comparisons[state]["copy_unique"] = dict(denominator=8,
                delta_all_correct=actual["controls"]["families"]["copy"]["unique_all_correct"] - off["controls"]["families"]["copy"]["unique_all_correct"],
                interpretation="eight unique prompts; each must pass both registered executions")
            comparisons[state]["spill"] = {family: dict(total=16, maximum=0,
                actual=actual["controls"]["families"][family]["tag_spill"],
                within_point05=actual["controls"]["families"][family]["tag_spill"] == 0) for family in ("addition", "copy")}
        cost_keys = reductions[0]["cost"].keys()
        cost = {key: sum(row["cost"][key] for row in reductions) for key in cost_keys}
        return dict(status="COMPLETE_ROOT0_READOUT_NOT_L1_VERDICT", complete=True, comparisons=comparisons,
                    thresholds=corpus.threshold_requirements(), reductions=reductions,
                    actual_generation_calls=672, actual_scoring_requests=192, candidate_forwards=576,
                    assay_version=ASSAY_VERSION,
                    cost=cost, readout_reserved_seconds=sum(row["reserved_seconds"] for row in reductions),
                    resource_budget=RESOURCE_BUDGET, fits_and_total_budget_enforced_by="Main, not this readout-only reducer",
                    supplies_l1_verdict=False, claim_limits=LIMITS)
    except (KeyError, TypeError, ValueError) as error:
        return dict(status="INCOMPLETE", complete=False, error=str(error), supplies_l1_verdict=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "reduce", "summarize", "_worker"))
    for name in ("material", "out", "model", "model-pins", "adapter", "root"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--roots", nargs="+", type=Path)
    parser.add_argument("--state", choices=STATES)
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--prospect-contrast", choices=(PROSPECT_CONTRAST,))
    parser.add_argument("--device")
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.stage == "prepare":
        base.require(all(getattr(args, key) is not None for key in
                         ("material", "out", "model", "model_pins", "state", "phase", "device", "lease_end")), "missing prepare arguments")
        result = prepare(args.material, args.out, args.model, base.read(args.model_pins), args.state, args.phase,
                         args.adapter, args.device, args.lease_end, prospect_contrast=args.prospect_contrast)
    elif args.stage == "summarize":
        base.require(args.roots is not None, "six --roots required")
        result = summarize([reduce(root) for root in args.roots])
    else:
        base.require(args.root is not None, "--root required")
        if args.stage == "_worker":
            base.require(args.allow_gpu, "explicit --allow-gpu required")
            result = worker(args.root)
        else:
            result = run(args.root, allow_gpu=args.allow_gpu) if args.stage == "run" else reduce(args.root)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
