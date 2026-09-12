"""Fresh exact-row surface validation only; never memory, lineage, or fit release.

CPU: config-template, prepare, preflight, replay. Only execute --allow-gpu
starts a bounded clean-base worker. Main must review the prepared bytes first.
Non-material lifetime repair: Linux /proc and GNU /usr/bin/timeout required.
Controller cancellation cleans its owned group; timeout independently kills a
still-running worker's group. This is not a cgroup or escaped-process guard.
GNU timeout exits when its direct child exits: after controller loss, descendants
left behind by an early worker exit need external supervision. Killing timeout,
escaping the group, or uninterruptible kernel waits defeats a hard lifetime bound.
The CompilerGym preflight uses an already provisioned local CPU installation.
No old result, adapter, optimizer, training example, or automatic successor is
consumed. C11 custody is deferred; local hashes do not authenticate model origin.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from . import multikey_writer_gateway_simple as w0
from . import writer_interface_calibration as cal
from . import run_reasoning_neutral as neutral


VERSION = "semantic-carrier-surface-20260912-v1"
ACTIONS = ("-mem2reg", "-gvn")
CANDIDATES = tuple(f"ACT: {action}\n" for action in ACTIONS)
COPY_ACTIONS = ("-sroa", "-simplifycfg", "-instcombine", "-licm",
                "-loop-unroll", "-adce", "-bdce", "-argpromotion")
INSTRUCTION = ("Choose exactly one executable compiler action. Reply with exactly one line: "
               "ACT: -mem2reg or ACT: -gvn. Write no other text.")
MAX_TOKENS = 32
MAX_SECONDS = 3600
TIMEOUT_BINARY = "/usr/bin/timeout"
CLEANUP_RESERVE_SECONDS = 8
SMOKE = "cbench-v1/crc32"
BOUNDARY = dict(evaluation_only=True, training=False, adapters=False, clean_lineage=False,
                conditional_memory=False, fit_release=False, formal_C11_custody="DEFERRED",
                material_origin="fresh_namespace_synthetic_researcher_authored",
                official_model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY")


def config_template():
    return dict(model=w0.MODEL, model_path="/absolute/local/base-snapshot",
        tokenizer_path="/absolute/local/base-snapshot", model_revision="REPLACE_40_HEX",
        tokenizer_revision="REPLACE_40_HEX", model_sha256="REPLACE_64_HEX",
        tokenizer_sha256="REPLACE_64_HEX", environment={"python": "REPLACE", "packages": {}},
        node="REPLACE_NODE_SHA256", gpu_uuid="GPU-REPLACE", driver_version="REPLACE",
        lease_end_unix=0, lease_cutoff_unix=0, deadline_unix=0,
        compiler_python="/absolute/local/compiler-venv/bin/python",
        compiler_library_path="/absolute/local/compiler-libraries",
        protected_paths=[], approved_intake="REPLACE_MAIN_REVIEW_REFERENCE",
        builder_preflight_reference="REPLACE_DATED_BUILDER_NOTE",
        requested_scope="semantic carrier surface validation only; zero fits; C11 deferred")


def validate_config(config):
    w0.exact_keys(config, config_template())
    w0.require(config["model"] == w0.MODEL, "frozen clean base")
    w0.require(config["requested_scope"] == config_template()["requested_scope"], "surface-only scope")
    for name in ("approved_intake", "builder_preflight_reference"):
        w0.require(isinstance(config[name], str) and config[name] and "REPLACE" not in config[name], name)
    for name, length in (("model_revision", 40), ("tokenizer_revision", 40),
                         ("model_sha256", 64), ("tokenizer_sha256", 64), ("node", 64)):
        w0.require(isinstance(config[name], str) and re.fullmatch(f"[0-9a-f]{{{length}}}", config[name]), name)
    for name in ("model_path", "tokenizer_path", "compiler_python", "compiler_library_path"):
        w0.require(isinstance(config[name], str) and Path(config[name]).is_absolute(), name)
    w0.require(isinstance(config["protected_paths"], list) and all(
        isinstance(path, str) and Path(path).is_absolute() for path in config["protected_paths"]), "protected paths")
    w0.require(re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", config["gpu_uuid"]), "GPU UUID")
    w0.require(re.fullmatch(r"[0-9.]+", config["driver_version"]), "driver version")
    for name in ("lease_end_unix", "lease_cutoff_unix", "deadline_unix"):
        w0.require(type(config[name]) in (int, float) and math.isfinite(config[name]) and config[name] > 0, name)
    w0.require(config["deadline_unix"] <= config["lease_cutoff_unix"] <=
               config["lease_end_unix"] - 6 * 3600, "lease buffer/deadline")


def source_pins():
    base = Path(__file__).resolve().parents[1]
    paths = (Path(__file__), Path(w0.__file__), Path(cal.__file__), Path(neutral.__file__), Path(TIMEOUT_BINARY),
             base / "tests/test_semantic_carrier_diagnostic.py", base / "organism_v6/cgym_eval.py")
    return {str(path.resolve()): w0.file_hash(path) for path in paths}


def pin_inputs(config):
    validate_config(config)
    environment = w0.environment_identity()
    w0.require(environment == config["environment"], "environment pin mismatch")
    snapshots, cached = {}, {}
    for kind in ("model", "tokenizer"):
        path = str(Path(config[kind + "_path"]).resolve(strict=True))
        if path not in cached:
            cached[path] = w0.snapshot_inventory(path)
        snapshot = cached[path]
        w0.require(snapshot["sha256"] == config[kind + "_sha256"], kind + " snapshot drift")
        w0.require(not any("adapter" in Path(name).name.lower() for name, _ in snapshot["files"]),
                   "no adapter files in snapshots")
        snapshots[kind] = snapshot
    model_config = json.loads((Path(config["model_path"]) / "config.json").read_text())
    w0.require(model_config.get("model_type") == "qwen2" and model_config.get("num_hidden_layers") == 28
               and model_config.get("hidden_size") == 3584, "Qwen2.5-7B architecture")
    return dict(**snapshots, environment=environment,
                compiler_python_sha256=w0.file_hash(config["compiler_python"]))


def build_material():
    roots = []
    for root_index in range(2):
        root_id = "semroot_" + w0.digest([VERSION, "root", root_index])[:24]
        tools = ["semtool_" + w0.digest([VERSION, "tool", root_index, slot])[:24] for slot in range(8)]
        roots.append(dict(root_id=root_id, tools=tools))
    return dict(namespace=VERSION, roots=roots, split="oracle_surface_only_never_fit_primary_or_locality")


def build_items():
    items = []
    for root_index, root in enumerate(build_material()["roots"]):
        for mapping_index, mapping in enumerate(("W+", "W-")):
            for slot, tool in enumerate(root["tools"]):
                for mode in range(2):
                    expected = (slot + root_index + mode + mapping_index) % 2
                    task = f"For {tool}, the selected mode is m{mode}; choose now.\n"
                    row = f"{tool} m{mode} -> ACT: {ACTIONS[expected]}\n"
                    items.append(dict(kind="semantic_exact_row_carrier", root=root_index, mapping=mapping,
                        pair_id=w0.digest([VERSION, root_index, slot, mode]), expected=expected,
                        prompt=f"{INSTRUCTION}\nBinding:\n{row}Task:\n{task}"))
        for action in COPY_ACTIONS:
            items.append(dict(kind="native_action_copy", root=root_index, expected=action,
                prompt=f"Copy exactly one executable action line and no other text:\nACT: {action}\n"))
    return items


def encode_candidate(tokenizer, rendered, prefix_ids, target):
    """Mask exact whole continuation including LF and EOS; reject token joins."""
    w0.require(target in (*CANDIDATES, *(f"ACT: {action}\n" for action in COPY_ACTIONS)), "frozen candidate")
    eos = tokenizer.eos_token_id
    w0.require(type(eos) is int and eos >= 0, "missing EOS")
    text = rendered + target
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
    w0.require(len(ids) == len(offsets) and len(ids) > len(prefix_ids) > 0, "candidate token lengths")
    cursor, labels = 0, []
    for token, (start, stop) in zip(ids, offsets):
        w0.require(type(token) is int and token >= 0 and start == cursor and start < stop <= len(text),
                   "candidate offset coverage")
        w0.require(not start < len(rendered) < stop, "candidate boundary straddle")
        labels.append(-100 if stop <= len(rendered) else token)
        cursor = stop
    w0.require(cursor == len(text) and tokenizer.decode(ids) == text, "candidate exact roundtrip")
    w0.require(ids[:len(prefix_ids)] == prefix_ids and labels[:len(prefix_ids)] == [-100] * len(prefix_ids)
               and all(label != -100 for label in labels[len(prefix_ids):]), "candidate-dependent prefix")
    w0.require(eos not in ids[len(prefix_ids):], "response already contains EOS")
    response_ids = ids[len(prefix_ids):] + [eos]
    w0.require(tokenizer.decode(response_ids[:-1]) == target, "response roundtrip")
    w0.require(len(response_ids) <= MAX_TOKENS - 8 and len(ids) + 1 <= 2048, "candidate headroom")
    return dict(text=target, input_ids=ids + [eos], labels=labels + [eos], response_ids=response_ids)


def build_requests(tokenizer):
    result = []
    for item in build_items():
        rendered = tokenizer.tokenizer.apply_chat_template(
            [{"role": "user", "content": item["prompt"]}], tokenize=False, add_generation_prompt=True)
        prefix = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)["input_ids"]
        w0.require(prefix and all(type(token) is int and token >= 0 for token in prefix)
                   and len(prefix) + MAX_TOKENS <= 2048 and tokenizer.decode(prefix) == rendered,
                   "bounded exact chat prefix")
        payload = dict(prompt=item["prompt"], rendered_prompt=rendered, prompt_input_ids=prefix,
                       max_new_tokens=MAX_TOKENS, do_sample=False, seed=0)
        if item["kind"] == "native_action_copy":
            encode_candidate(tokenizer, rendered, prefix, f"ACT: {item['expected']}\n")
        for operation in (("generate", "score") if item["kind"] == "semantic_exact_row_carrier" else ("generate",)):
            candidates = ([encode_candidate(tokenizer, rendered, prefix, text) for text in CANDIDATES]
                          if operation == "score" else [])
            request = dict(namespace=VERSION, audit={key: value for key, value in item.items() if key != "prompt"},
                           operation=operation, payload=payload, candidates=candidates)
            result.append(dict(request_id=w0.digest(request), **request))
    w0.require(len(result) == 144 and len({row["request_id"] for row in result}) == 144, "144 unique requests")
    return result


def backend_preflight(config):
    evaluator = Path(__file__).resolve().with_name("cgym_eval.py")
    base = [config["compiler_python"], str(evaluator), "--benchmark", SMOKE]
    receipts = []
    for suffix in (["--list-actions"], *[["--passes=" + action] for action in ACTIONS]):
        command = base + suffix
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES="", LD_LIBRARY_PATH=config["compiler_library_path"]))
        parsed = json.loads(completed.stdout)
        w0.require(parsed.get("ok") is True, "backend smoke/registry failed")
        receipts.append(dict(command=command, stdout=completed.stdout, stderr=completed.stderr, parsed=parsed))
    registry = receipts[0]["parsed"]["actions"]
    w0.require(isinstance(registry, list) and len(registry) == len(set(registry))
               and all(action in registry for action in (*ACTIONS, *COPY_ACTIONS)), "registered native actions")
    return dict(benchmark=SMOKE, calls=receipts, interface_only=True, scores_visible_to_model=False)


def prepare(out, config):
    validate_config(config)
    w0.require(config["deadline_unix"] > time.time(), "prospective deadline")
    root = cal._separate(out, [config["model_path"], config["tokenizer_path"],
        config["compiler_python"], config["compiler_library_path"], *config["protected_paths"]])
    w0.require(root.parent.is_dir() and not root.exists(), "fresh output directory required")
    sources, pins = source_pins(), pin_inputs(config)
    tokenizer = w0.load_local_tokenizer(config)
    requests = build_requests(tokenizer)
    backend = backend_preflight(config)
    w0.require(sources == source_pins() and pins == pin_inputs(config), "prepare input/source drift")
    root.mkdir()
    for name, value in (("material.json", build_material()), ("requests.json", requests), ("backend.json", backend)):
        w0.write_once(root, name, value)
    spec = dict(version=VERSION, boundary=BOUNDARY, config=config, output_root=str(root), sources=sources,
        input_pins=pins, max_seconds=MAX_SECONDS, max_new_tokens=MAX_TOKENS,
        request_counts=dict(carrier_generate=64, carrier_score=64, copy_generate=16, candidate_forwards=128),
        artifacts={name: w0.file_hash(root / name) for name in ("material.json", "requests.json", "backend.json")})
    w0.write_once(root, "manifest.json", spec)
    w0.write_once(root, "PREPARED.json", dict(manifest_sha256=w0.digest(spec), model_loaded=False))
    return dict(status="PREPARED_SURFACE_ONLY_MAIN_REVIEW_REQUIRED", manifest_sha256=w0.digest(spec), **BOUNDARY)


def validate(root):
    root = w0.checked_path(root)
    spec = w0.load_json(root / "manifest.json")
    validate_config(spec["config"])
    w0.require(w0.load_json(root / "PREPARED.json")["manifest_sha256"] == w0.digest(spec)
               and spec["output_root"] == str(root) and spec["version"] == VERSION
               and spec["boundary"] == BOUNDARY and spec["sources"] == source_pins()
               and spec["max_seconds"] == MAX_SECONDS and spec["max_new_tokens"] == MAX_TOKENS,
               "manifest/source binding")
    w0.require(set(spec["artifacts"]) == {"material.json", "requests.json", "backend.json"}, "artifact inventory")
    for name, digest in spec["artifacts"].items():
        w0.require(w0.file_hash(root / name) == digest, "prepared artifact drift")
    w0.require(w0.load_json(root / "material.json") == build_material(), "fresh fixed material")
    tokenizer = w0.load_local_tokenizer(spec["config"])
    requests = build_requests(tokenizer)
    w0.require(w0.load_json(root / "requests.json") == requests, "tokenizer/request drift")
    return spec, requests, tokenizer


def strict_output(text, truncated=False, eos_terminated=True, actions=ACTIONS):
    w0.require(isinstance(text, str) and type(truncated) is bool and type(eos_terminated) is bool, "output types")
    stripped = text.encode("utf-8").strip(b" \t\r\n")
    multiple = text.count("ACT:") > 1
    choices = {f"ACT: {action}".encode(): action for action in actions}
    action = None if truncated or not eos_terminated or multiple else choices.get(stripped)
    return dict(action=action, multiple=multiple)


def check_generation(request, record, tokenizer):
    ids = record["generated_ids"]
    w0.require(isinstance(ids, list) and all(type(token) is int and token >= 0 for token in ids)
               and len(ids) <= MAX_TOKENS, "generation token accounting")
    ended = bool(ids) and ids[-1] == tokenizer.eos_token_id
    w0.require(tokenizer.eos_token_id not in (ids[:-1] if ended else ids), "early EOS")
    w0.require(record["eos_terminated"] is ended and record["truncated"] is (len(ids) == MAX_TOKENS and not ended)
               and record["text"] == tokenizer.decode(ids[:-1] if ended else ids)
               and record["decoded_with_terminal_eos"] == tokenizer.decode(ids), "raw generation mismatch")
    return strict_output(record["text"], record["truncated"], ended,
                         ACTIONS if request["audit"]["kind"] == "semantic_exact_row_carrier" else COPY_ACTIONS)


def candidate_choice(request, record):
    logs = record["token_logprobs"]
    w0.require(isinstance(logs, list) and len(logs) == 2, "two candidate records")
    sums = []
    for candidate, values in zip(request["candidates"], logs):
        w0.require(isinstance(values, list) and len(values) == len(candidate["response_ids"]), "candidate token accounting")
        finite = all(type(value) in (int, float) and math.isfinite(value) and value <= 0 for value in values)
        total = sum(values) if finite else None
        sums.append(total if total is not None and math.isfinite(total) else None)
    choice = None if None in sums or sums[0] == sums[1] else int(sums[1] > sums[0])
    return choice, sums


def reduce_records(requests, records, tokenizer):
    by_id = {record["request_id"]: record for record in records}
    w0.require(len(requests) == len(records) == len(by_id) == 144
               and set(by_id) == {request["request_id"] for request in requests}, "incomplete/duplicate records")
    cells, pairs, details = {}, {}, []
    valid = truncated = multiple = 0
    copies = {"0": 0, "1": 0}
    for request in requests:
        record = by_id[request["request_id"]]
        w0.require(record["request_sha256"] == w0.digest(request), "record request binding")
        audit, operation = request["audit"], request["operation"]
        if operation == "generate":
            parsed = check_generation(request, record, tokenizer)
            if audit["kind"] == "native_action_copy":
                copies[str(audit["root"])] += int(parsed["action"] == audit["expected"])
                continue
            choice = ACTIONS.index(parsed["action"]) if parsed["action"] in ACTIONS else None
            valid += int(choice is not None)
            truncated += int(record["truncated"])
            multiple += int(parsed["multiple"])
            detail = dict(raw_text=record["text"], raw_utf8_hex=record["text"].encode().hex())
        else:
            choice, sums = candidate_choice(request, record)
            detail = dict(candidate_sums=sums, candidate_token_counts=[len(row["response_ids"]) for row in request["candidates"]],
                          target_margin=None if None in sums else sums[audit["expected"]] - sums[1 - audit["expected"]])
        cell = cells.setdefault(f"{audit['root']}/{audit['mapping']}", {
            "generate": {"correct": 0, "confusion": [[0, 0, 0], [0, 0, 0]]},
            "score": {"correct": 0, "confusion": [[0, 0, 0], [0, 0, 0]]}})[operation]
        cell["correct"] += int(choice == audit["expected"])
        cell["confusion"][audit["expected"]][2 if choice is None else choice] += 1
        pairs.setdefault(audit["pair_id"], {}).setdefault(operation, {})[audit["mapping"]] = dict(
            choice=choice, expected=audit["expected"])
        details.append(dict(request_id=request["request_id"], choice=choice, expected=audit["expected"], **detail))
    swaps = {operation: sum(all(row["choice"] == row["expected"] for row in pair[operation].values())
                           and len(pair[operation]) == 2 for pair in pairs.values()) for operation in ("generate", "score")}
    agreement = sum(pair["generate"][mapping]["choice"] is not None and
                    pair["generate"][mapping]["choice"] == pair["score"][mapping]["choice"]
                    for pair in pairs.values() for mapping in ("W+", "W-"))
    passed = (len(cells) == 4 and len(pairs) == 32 and all(cell[operation]["correct"] >= 15
        for cell in cells.values() for operation in ("generate", "score")) and valid >= 61
        and truncated == multiple == 0 and min(swaps.values()) >= 29 and min(copies.values()) == 8)
    return dict(label="SEMANTIC_EXACT_ROW_SURFACE_OK" if passed else "ASSAY_INVALID_SEMANTIC_ACTION_SURFACE",
        boundary=BOUNDARY, requests=144, generation_calls=80, scoring_requests=64, candidate_forwards=128,
        cells=cells, valid=valid, truncated=truncated, multiple=multiple, complementary_swaps=swaps,
        native_copy_correct=copies, generation_score_agreement=agreement, details=details,
        confusion_columns=[*ACTIONS, "invalid_or_tie"], optimizer_steps=0)


def score(torch, model, request):
    result = []
    for candidate in request["candidates"]:
        ids = torch.tensor([candidate["input_ids"]], dtype=torch.long, device="cuda:0")
        with torch.inference_mode():
            logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
            probabilities = torch.log_softmax(logits[0].float(), dim=-1)
            values = [float(probabilities[index - 1, token].cpu())
                      for index, (token, label) in enumerate(zip(candidate["input_ids"], candidate["labels"])) if label != -100]
        result.append([value if math.isfinite(value) else None for value in values])
    return dict(token_logprobs=result)


class ControllerCancelled(RuntimeError):
    pass


def process_identity(pid):
    fields = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, ppid=int(fields[1]), pgid=int(fields[2]), session=int(fields[3]), start_ticks=int(fields[19]))


def worker_command(root):
    return [sys.executable, "-B", "-m", "organism_v6.semantic_carrier_diagnostic",
            "_worker", "--run", str(root), "--allow-gpu"]


def run_bounded_worker(command, root, environment, deadline):
    """Own exactly one new session; always clean the group, not just its leader."""
    process, cancelled, cleaning = None, None, False
    handlers = {}

    def cancel(signum, frame):
        nonlocal cancelled
        cancelled = signum
        if process is not None and not cleaning:
            raise ControllerCancelled(f"controller signal {signum}")

    try:
        for signum in (signal.SIGTERM, signal.SIGINT):
            handlers[signum] = signal.signal(signum, cancel)
        try:
            with (root / "worker.log").open("xb") as log:
                launch_wall = time.time()
                remaining = math.floor((deadline - launch_wall - CLEANUP_RESERVE_SECONDS) * 1000) / 1000
                w0.require(math.isfinite(remaining) and 0 < remaining <= MAX_SECONDS, "worker budget exhausted")
                if cancelled is not None:
                    raise ControllerCancelled(f"controller signal {cancelled}")
                wrapped = [TIMEOUT_BINARY, "--signal=KILL", f"{remaining:.3f}s", *command]
                process = subprocess.Popen(wrapped, cwd=Path(__file__).resolve().parents[1], env=environment,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                if cancelled is not None:
                    raise ControllerCancelled(f"controller signal {cancelled}")
                identity = process_identity(process.pid)
                w0.require(identity["pgid"] == identity["session"] == process.pid
                           and identity["ppid"] == os.getpid(), "owned timeout session")
                w0.write_once(root, "SUPERVISOR.json", dict(identity=identity, command=wrapped,
                    launch_wall=launch_wall, timeout_seconds=remaining, deadline_unix=deadline))
                returncode = process.wait(timeout=remaining)
        finally:
            cleaning = True
            if process is not None:
                error = None
                try:
                    group_empty = neutral._cleanup_group(process)
                except (OSError, ValueError, IndexError) as failure:
                    group_empty = False
                    error = f"{type(failure).__name__}: {failure}"
                w0.write_once(root, "CLEANUP.json", dict(pid=process.pid, owned_group_empty=group_empty,
                                                       cancellation_signal=cancelled, error=error))
                w0.require(group_empty, "owned worker group cleanup failed")
        if cancelled is not None:
            raise ControllerCancelled(f"controller signal {cancelled}")
        return returncode
    finally:
        for signum, previous in handlers.items():
            signal.signal(signum, previous)


def validate_worker_parent(root, started):
    receipt_deadline = min(time.monotonic() + 2, time.monotonic() + started["deadline_unix"] - time.time())
    while not (root / "SUPERVISOR.json").exists() and time.monotonic() < receipt_deadline:
        time.sleep(.01)
    supervisor = w0.load_json(root / "SUPERVISOR.json")
    parent = process_identity(os.getppid())
    controller = process_identity(started["controller_pid"])
    expected_command = [TIMEOUT_BINARY, "--signal=KILL", f"{supervisor['timeout_seconds']:.3f}s", *worker_command(root)]
    actual_command = (Path("/proc") / str(parent["pid"]) / "cmdline").read_bytes().split(b"\0")[:-1]
    w0.require(parent == supervisor["identity"] and parent["ppid"] == started["controller_pid"]
        and parent["pgid"] == parent["session"] == parent["pid"] == os.getpgrp() == os.getsid(0)
        and controller["start_ticks"] == started["controller_start_ticks"]
        and supervisor["command"] == expected_command
        and actual_command == [part.encode() for part in expected_command]
        and supervisor["deadline_unix"] == started["deadline_unix"]
        and started["wall_start"] <= supervisor["launch_wall"]
        and 0 < supervisor["timeout_seconds"] <= started["deadline_unix"] - supervisor["launch_wall"] - CLEANUP_RESERVE_SECONDS,
        "owned timeout/controller startup binding")


def worker(root, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required")
    root = w0.checked_path(root)
    spec, requests, tokenizer = validate(root)
    started = w0.load_json(root / "STARTED.json")
    w0.require(started["manifest_sha256"] == w0.digest(spec) and started["deadline_unix"] <=
        min(started["wall_start"] + MAX_SECONDS, spec["config"]["deadline_unix"])
        and started["wall_start"] <= time.time() < started["deadline_unix"], "owned worker deadline binding")
    validate_worker_parent(root, started)
    w0.write_once(root, "WORKER_CLAIMED.json", dict(pid=os.getpid()))
    w0.require(pin_inputs(spec["config"]) == spec["input_pins"], "worker input drift")
    w0.gpu_identity(spec["config"])
    torch = w0.configure_torch(spec["config"], 0)
    w0.require(time.time() < started["deadline_unix"] - 5, "model load deadline")
    model = w0.load_hf_model(spec["config"], torch)
    model.eval()
    model.requires_grad_(False)
    w0.require(not model.training and not getattr(model, "peft_config", None)
               and not any(parameter.requires_grad for parameter in model.parameters()), "no adapter/train")
    records = []
    for request in requests:
        w0.require(time.time() < started["deadline_unix"] - 5, "request deadline")
        if request["operation"] == "generate":
            record = cal._generate(torch, model, tokenizer, dict(request["payload"], request_id=request["request_id"]))
        else:
            record = dict(request_id=request["request_id"], **score(torch, model, request))
        record["request_sha256"] = w0.digest(request)
        w0.write_once(root, request["request_id"] + ".json", record)
        records.append(record)
    w0.require(pin_inputs(spec["config"]) == spec["input_pins"], "post-inference input drift")
    validate(root)
    w0.write_once(root, "report.json", reduce_records(requests, records, tokenizer))


def replay(root):
    root = w0.checked_path(root)
    spec, requests, tokenizer = validate(root)
    seal = w0.load_json(root / "SEAL.json")
    inventory = cal._inventory(root)
    del inventory["SEAL.json"]
    w0.require(inventory == seal["files"], "sealed inventory drift")
    required = {"manifest.json", "PREPARED.json", "material.json", "requests.json", "backend.json",
                "STARTED.json", "SUPERVISOR.json", "CLEANUP.json", "WORKER_CLAIMED.json",
                "worker.log", "RESOURCE.json", "report.json"}
    required.update(request["request_id"] + ".json" for request in requests)
    w0.require(set(inventory) == required and seal["boundary"] == BOUNDARY, "complete execution inventory")
    started = w0.load_json(root / "STARTED.json")
    supervisor = w0.load_json(root / "SUPERVISOR.json")
    cleanup = w0.load_json(root / "CLEANUP.json")
    w0.require(cleanup["owned_group_empty"] is True and cleanup["cancellation_signal"] is None
               and cleanup["error"] is None and cleanup["pid"] == supervisor["identity"]["pid"], "owned group cleanup receipt")
    resource = w0.load_json(root / "RESOURCE.json")
    w0.require(started["manifest_sha256"] == w0.digest(spec) and 0 <= resource["elapsed_seconds"] <= MAX_SECONDS
               and resource["GPU_count"] == 1 and started["wall_start"] <= resource["wall_finish"] <=
               started["deadline_unix"] <= min(started["wall_start"] + MAX_SECONDS, spec["config"]["deadline_unix"]),
               "resource budget/startup binding")
    report = reduce_records(requests, [w0.load_json(root / (row["request_id"] + ".json")) for row in requests], tokenizer)
    w0.require(report == w0.load_json(root / "report.json"), "report replay mismatch")
    return report


def execute(root, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required; main reviews material first")
    begin, wall_start = time.monotonic(), time.time()
    root = w0.checked_path(root)
    spec, _, _ = validate(root)
    w0.assert_output_fds_outside_run(root)
    w0.require(set(cal._inventory(root)) == {"manifest.json", "PREPARED.json", "material.json", "requests.json", "backend.json"},
               "fresh prepared run only; no retry/overwrite")
    deadline = min(wall_start + MAX_SECONDS, spec["config"]["deadline_unix"])
    w0.require(pin_inputs(spec["config"]) == spec["input_pins"], "execution input drift")
    w0.require(deadline > time.time() + 10, "execution deadline expired")
    hardware = w0.gpu_identity(spec["config"])
    w0.assert_gpu_idle(spec["config"])
    w0.write_once(root, "STARTED.json", dict(wall_start=wall_start, deadline_unix=deadline,
        controller_pid=os.getpid(), controller_start_ticks=process_identity(os.getpid())["start_ticks"],
        manifest_sha256=w0.digest(spec)))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=spec["config"]["gpu_uuid"],
        CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0", HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    try:
        returncode = run_bounded_worker(worker_command(root), root, environment, deadline)
        w0.require(returncode == 0, "worker failed; no retry")
        validate(root)
        elapsed = time.monotonic() - begin
        w0.require(elapsed <= MAX_SECONDS and time.time() <= deadline, "resource deadline exceeded")
        w0.write_once(root, "RESOURCE.json", dict(GPU_count=1, elapsed_seconds=elapsed,
                                                wall_finish=time.time(), hardware=hardware))
        w0.write_once(root, "SEAL.json", dict(files=cal._inventory(root), boundary=BOUNDARY))
        return replay(root)
    except BaseException as error:
        w0.write_once(root, "FAILED.json", dict(error_type=type(error).__name__, error=str(error), boundary=BOUNDARY))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("config-template")
    prep = commands.add_parser("prepare")
    prep.add_argument("--out", required=True)
    prep.add_argument("--config", required=True)
    for name in ("preflight", "execute", "_worker", "replay"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name in ("execute", "_worker"):
            command.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "config-template":
        result = config_template()
    elif args.command == "prepare":
        result = prepare(args.out, json.loads(Path(args.config).read_text()))
    elif args.command == "preflight":
        spec, requests, _ = validate(args.run)
        w0.require(pin_inputs(spec["config"]) == spec["input_pins"], "preflight input drift")
        result = dict(status="CPU_PREFLIGHT_OK_NOT_LAUNCH_AUTHORIZATION", requests=len(requests), boundary=BOUNDARY)
    elif args.command == "replay":
        result = replay(args.run)
    else:
        result = (execute if args.command == "execute" else worker)(args.run, args.allow_gpu)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
