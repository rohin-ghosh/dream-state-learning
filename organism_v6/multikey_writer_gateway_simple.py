"""V10R1: CPU fixtures plus an explicitly scheduled four-fit HF executor.

``config-template`` and ``profile-plan`` do not load a model. ``prepare`` pins
local snapshots, checks native CPython builds, runs tokenizer preflight and the CPU suite, and writes a
fresh immutable run. Only ``execute --allow-gpu`` launches GPU workers. Each
fit and each adapter's generation/scoring operation uses a fresh process.
``replay-real`` checks sealed receipts and recomputes the full gate report.
CPU fixtures always remain CPU_FIXTURE_ONLY, never scientific gate evidence.

This gateway uses synthetic researcher-authored material, not a clean lineage.
Local cache hashes establish byte identity, not official model authentication;
the official external model pin remains unresolved. Supply an authoritative
``lease_end_unix`` and a ``lease_cutoff_unix`` no later than six hours before
that end. Earlier cutoffs are allowed; both template timestamps are unset and
fail closed. Node 3: end 2026-09-26 03:03 UTC (1790391780), latest cutoff
2026-09-25 21:03 UTC (1790370180). The separate three-A40-hour cap is unchanged.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time


VERSION = "mwg10r1-cpu-v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
ORIENTATIONS = ((0, 0, 1, 1, 0, 1, 0, 1), (0, 1, 1, 0, 1, 0, 0, 1))
MAPS = ("W+", "W-")
CONDITIONS = ("OFF", *MAPS)
CANDIDATES = ("ACT: a0\n", "ACT: a1\n")
RECIPE = {
    "rank": 8, "alpha": 16, "dropout": 0.05, "lr": 3e-5,
    "epochs": 2, "batch_size": 1, "max_length": 2048,
    "packing": False, "svd_init": False, "context_masked": True,
    "rows": 128, "optimizer_steps": 256,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
}
SCOPE_HASHES = {
    "v9": "eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955",
    "v10": "12a077950730c3abaef32b04a861d901ef4bae25a22e640b152472f5f364f549",
    "v10r1": "6cba6518184e7c8d12d7c23088895a565b84ae5ee067eaa63aac4440b91ea1aa",
}
CONSENSUS_HASHES = {
    "v9": "cd3e243b01e439ce2facb19ed745ee265572e75d7785eeb35fc1efdbb2977158",
    "v10": "147aebaaf0b974a37897acc724c6fe27c8e82c6f94db0c1e775eba3d57a1ce7e",
    "v10r1": "5792ec9acbf9e2da26f34ff8303bce06a496a3c9f5010162b0e4491db93ea9a2",
}
TEMPLATES = (
    (
        "Tool {tool}; mode {mode}. Choose its action.\n",
        "Select an action for tool {tool} operating in {mode}.\n",
        "Device {tool} is using mode {mode}. Supply the action.\n",
        "Given tool {tool} and mode {mode}, act.\n",
        "Operation request: {tool}, mode {mode}.\n",
        "Tool identifier: {tool}. Operating mode: {mode}.\n",
        "Resolve the action: tool={tool}; mode={mode}.\n",
        "Use the learned action for {tool} in {mode}.\n",
        "For {tool}, the selected mode is {mode}; choose now.\n",
        "Which action applies to tool {tool} under {mode}?\n",
        "Action needed for ({tool}, {mode}).\n",
        "Tool {tool} runs in {mode}: respond with the action.\n",
    ),
    (
        "Unit {tool} has setting {mode}. Return its action.\n",
        "Respond for unit {tool} with setting {mode}.\n",
        "Unit code {tool}; active setting {mode}. Act now.\n",
        "Determine an action for unit {tool} at {mode}.\n",
        "Setting {mode} is active on unit {tool}.\n",
        "Handle unit {tool} in setting {mode}.\n",
        "Unit={tool}, setting={mode}; choose an action.\n",
        "Act for unit {tool} using setting {mode}.\n",
        "The unit is {tool}; its setting is {mode}. Action?\n",
        "An action is required: unit {tool}, setting {mode}.\n",
        "Under setting {mode}, what should unit {tool} do?\n",
        "Issue the action belonging to unit {tool} at {mode}.\n",
    ),
)
PROTECTED_KINDS = {"child", "parent", "compilergym", "pcfl", "c11"}
PENDING = ["real_tokenizer_preflight", "four_real_HF_fits",
           "fresh_process_generation_and_scoring_loads", "measured_A40_cap",
           "real_raw_requests_and_stage_receipts", "bound_CPU_suite_and_review_receipts",
           "integration_review"]
SOURCE_PATHS = ("organism_v6/multikey_writer_gateway_simple.py",
                "tests/test_multikey_writer_gateway_simple.py",
                "gpu/multikey_writer_gateway_simple.sh")
REAL_VERSION = "mwg10r1-hf-v1"
LEASE_FINISH_BUFFER_SECONDS = 6 * 3600
EVIDENCE_BOUNDARY = dict(material_origin="synthetic_researcher_authored", clean_lineage=False,
                         official_model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY")
PACKAGES = ("torch", "transformers", "peft", "tokenizers", "safetensors", "numpy")
EXECUTION_RECIPE = dict(RECIPE, optimizer="AdamW", betas=[.9, .999], eps=1e-8,
                        weight_decay=.01, scheduler="none", gradient_accumulation=1,
                        gradient_clipping=None, dtype="bfloat16", attention="eager",
                        gradient_checkpointing=False, shuffle_each_epoch=False,
                        deterministic_algorithms=True, allow_tf32=False,
                        cublas_workspace_config=":4096:8", adamw_foreach=False, adamw_fused=False)
REQUEST_CONTRACT = dict(generation=dict(do_sample=False, max_new_tokens=32, chat_template=False),
                        scoring=dict(full_continuation=True, include_eos=True, log_softmax_dtype="float32"),
                        cache="none", output_retries=0)


class ContractError(ValueError):
    """A non-reportable integrity or contract failure."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(canonical(value))


def exact_keys(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), "field allowlist")


def seeded_order(values, seed, domain):
    return sorted(values, key=lambda value: digest([domain, seed, value]))


def action(root, slot, mode, mapping):
    require(mapping in MAPS, "unknown map")
    return ORIENTATIONS[root][slot] ^ mode ^ (mapping == "W-")


def fit_projection(rows, seed):
    return [{"context": row["context"], "target": CANDIDATES[row["target"]],
             "mask": "context_only", "order": order, "seed": seed,
             "recipe": dict(RECIPE)} for order, row in enumerate(rows)]


def best_shortcut(rows, fields):
    groups = defaultdict(Counter)
    for row in rows:
        groups[tuple(row[field] for field in fields)][row["target"]] += 1
    require(Counter(row["target"] for row in rows)[0] == len(rows) // 2,
            "unbalanced labels")
    return sum(max(counts.values()) for counts in groups.values()), len(rows)


def build_material(identifier_seed=100, train_order_seed=200,
                   held_order_seed=300, request_seed=400, fit_seeds=(0, 1)):
    require(len(fit_seeds) == 2 and fit_seeds[0] != fit_seeds[1], "root seeds differ")
    seeds = [identifier_seed, train_order_seed, held_order_seed, request_seed, *fit_seeds]
    require(all(type(seed) is int and 0 <= seed < 2**32 for seed in seeds), "seed range")
    config = dict(identifier_seed=identifier_seed, train_order_seed=train_order_seed,
                  held_order_seed=held_order_seed, request_seed=request_seed,
                  fit_seeds=list(fit_seeds))
    material = dict(version=VERSION, config=config, recipe=dict(RECIPE),
                    fit_cap=4, A40_hours_cap=3.0, training_run_replication=False,
                    root_seed_confounded=True, execution_node_policy="one_node",
                    templates=TEMPLATES, roots=[], nuisance_fields=["template"])
    for root in range(2):
        tools = ["u" + digest([identifier_seed, root, slot])[:12] for slot in range(8)]
        neighbours = [tool[:-1] + ("0" if tool[-1] != "0" else "1") for tool in tools]
        require(len(set(tools + neighbours)) == 16, "identifier collision")
        root_data = dict(tools=tools, neighbours=neighbours,
                         orientation=list(ORIENTATIONS[root]), train={}, held=[], spill=[])
        for mapping in MAPS:
            keys = seeded_order(list(itertools.product(range(8), range(2), range(8))),
                                train_order_seed, ["train", root])
            root_data["train"][mapping] = [
                dict(slot=slot, mode=mode, stratum=slot // 4, template=template,
                     orientation=ORIENTATIONS[root][slot],
                     context=TEMPLATES[root][template].format(tool=tools[slot], mode=f"m{mode}"),
                     target=action(root, slot, mode, mapping))
                for slot, mode, template in keys]
        keys = seeded_order(list(itertools.product(range(8), range(2), range(8, 12))),
                            held_order_seed, ["held", root])
        root_data["held"] = [dict(
            slot=slot, mode=mode, stratum=slot // 4, template=template,
            context=TEMPLATES[root][template].format(tool=tools[slot], mode=f"m{mode}"),
            seed=int(digest([request_seed, root, slot, mode, template])[:8], 16))
            for slot, mode, template in keys]
        prefix = "Tool" if root == 0 else "Unit"
        for family in ("missing", "unsupported", "neighbour", "unrelated"):
            for index in range(16 if family == "neighbour" else 8):
                if family == "missing":
                    prompt = f"{prefix} {tools[index]}. Choose an action.\n"
                elif family == "unsupported":
                    prompt = f"{prefix} {tools[index]}, mode m2. Choose an action.\n"
                elif family == "neighbour":
                    prompt = f"{prefix} {neighbours[index // 2]}, mode m{index % 2}. Choose an action.\n"
                else:
                    prompt = (f"{prefix} interface check. Copy exactly the following line, "
                              f"without explanation: ACT: native_{index}\n")
                root_data["spill"].append(dict(
                    family=family, index=index, context=prompt,
                    expected=f"ACT: native_{index}" if family == "unrelated" else None,
                    seed=int(digest([request_seed, root, family, index])[:8], 16)))
        material["roots"].append(root_data)
    return json.loads(canonical(material))


def validate_material(material):
    require(canonical(material) == canonical(build_material(**material["config"])),
            "material differs from frozen generator")
    receipt = {"training_rows": 0, "primary_items": 0, "shortcut_counts": []}
    all_tools = [tool for root in material["roots"] for tool in root["tools"]]
    require(len(set(all_tools)) == 16, "root identifier overlap")
    require(len(set(itertools.chain.from_iterable(TEMPLATES))) == 24, "template overlap")
    for root_index, root in enumerate(material["roots"]):
        for mapping in MAPS:
            train = root["train"][mapping]
            held = [dict(row, target=action(root_index, row["slot"], row["mode"], mapping),
                         orientation=ORIENTATIONS[root_index][row["slot"]]) for row in root["held"]]
            require(len(train) == 128 and len(held) == 64, "fixed counts")
            receipt["training_rows"] += len(train)
            for panel in (train, held):
                for fields in ((), ("slot",), ("mode",), ("stratum",),
                               ("stratum", "mode"), ("template",), ("template", "mode")):
                    correct, total = best_shortcut(panel, fields)
                    require(2 * correct == total, "shortcut exceeds chance")
                    receipt["shortcut_counts"].append([root_index, mapping, len(panel),
                                                       list(fields), correct, total])
                correct, total = best_shortcut(panel, ("orientation", "mode"))
                require(correct == total, "positive joint oracle")
        receipt["primary_items"] += 3 * len(root["held"])
    return receipt


def parse_output(text, truncated=False):
    require(text is None or isinstance(text, str), "output type")
    raw = b"" if text is None else text.encode("utf-8")
    multiple = len(re.findall(rb"(?:^|\n)[ \t]*ACT:", raw)) >= 2
    stripped = raw.strip(b" \t\r\n")
    value = {b"ACT: a0": 0, b"ACT: a1": 1}.get(stripped)
    return {"action": None if truncated else value, "multiple_ACT": multiple}


def native_correct(text, expected, truncated=False):
    return (text is not None and not truncated and
            text.encode("utf-8").strip(b" \t\r\n") == expected.encode("utf-8"))


def encode_candidate(tokenizer, context, target):
    require(target in CANDIDATES, "candidate bytes")
    require(type(tokenizer.eos_token_id) is int, "missing EOS")
    text = context + target
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    exact_keys(encoded, ("input_ids", "offset_mapping"))
    ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
    require(ids and len(ids) == len(offsets), "token offsets")
    require(tokenizer.eos_token_id not in ids, "duplicate EOS")
    cursor = 0
    boundary = len(context)
    labels = []
    for token, (start, stop) in zip(ids, offsets):
        require(start == cursor and start < stop <= len(text), "coverage/truncation")
        require(not start < boundary < stop, "boundary-straddling token")
        labels.append(-100 if stop <= boundary else token)
        cursor = stop
    require(cursor == len(text) and tokenizer.decode(ids) == text, "tokenizer round trip")
    require(labels[0] == -100 and any(label != -100 for label in labels), "causal loss mask")
    require(len(ids) + 1 <= RECIPE["max_length"], "maximum length/truncation")
    return dict(input_ids=ids + [tokenizer.eos_token_id],
                labels=labels + [tokenizer.eos_token_id])


def token_pair(tokenizer, context):
    pairs = [encode_candidate(tokenizer, context, target) for target in CANDIDATES]
    masks = [[label != -100 for label in pair["labels"]] for pair in pairs]
    require(masks[0] == masks[1], "candidate token count/mask mismatch")
    prefix = [[token for token, label in zip(pair["input_ids"], pair["labels"])
               if label == -100] for pair in pairs]
    require(prefix[0] == prefix[1], "candidate-dependent context")
    return pairs


class FixtureTokenizer:
    """Character-token fake used only by the explicitly CPU-only fixture path."""

    eos_token_id = 0

    def __call__(self, text, **kwargs):
        return dict(input_ids=[ord(character) + 1 for character in text],
                    offset_mapping=[(index, index + 1) for index in range(len(text))])

    def decode(self, ids):
        return "".join(chr(token - 1) for token in ids)


def oracle_prompt(root, mapping, context):
    lines = ["Explicit action table:"]
    for slot, tool in enumerate(root["tools"]):
        for mode in range(2):
            target = root["orientation"][slot] ^ mode ^ (mapping == "W-")
            lines.append(f"{tool} m{mode} -> ACT: a{target}")
    return "\n".join(lines) + "\nTask:\n" + context


def request_payload(kind, identity, adapter, prompt, seed, token_counts=None):
    require(kind in {"primary_generate", "primary_score", "oracle_generate",
                     "spill_generate", "spill_score"}, "operation kind")
    exact_keys(identity, ("model", "model_sha256", "tokenizer_sha256", "run_sha256"))
    require(identity["model"] == MODEL, "frozen base")
    require(all(re.fullmatch(r"[0-9a-f]{64}", identity[key]) for key in
                ("model_sha256", "tokenizer_sha256", "run_sha256")), "pinned identity")
    require(adapter == "OFF" or re.fullmatch(r"[0-9a-f]{64}", adapter), "adapter hash")
    require(kind != "oracle_generate" or adapter == "OFF", "oracle must use OFF")
    scoring = kind.endswith("score")
    return dict(kind=kind, identity=dict(identity), adapter=adapter, prompt=prompt,
                seed=seed, candidates=list(CANDIDATES) if scoring else [],
                parameters=({"full_continuation": True, "include_eos": True,
                             "token_counts": token_counts} if scoring else
                            {"do_sample": False, "max_new_tokens": 32}))


def build_requests(material, identity, adapters, tokenizer=None, preflight=None):
    validate_material(material)
    require(set(adapters) == {f"{root}/{mapping}" for root in range(2) for mapping in MAPS},
            "four adapter identities")
    require(len(set(adapters.values())) == 4, "distinct adapter trees")
    requests = []
    for root_index, root in enumerate(material["roots"]):
        for condition in CONDITIONS:
            adapter = "OFF" if condition == "OFF" else adapters[f"{root_index}/{condition}"]
            for panel, rows in (("primary", root["held"]), ("spill", root["spill"])):
                for index, row in enumerate(rows):
                    pairs = (preflight["context_pairs"][digest(row["context"])] if preflight is not None
                             else token_pair(tokenizer, row["context"]))
                    counts = [sum(label != -100 for label in pair["labels"]) for pair in pairs]
                    for operation in ("generate", "score"):
                        payload = request_payload(f"{panel}_{operation}", identity, adapter,
                                                  row["context"], row["seed"], counts)
                        requests.append(dict(id=digest(payload), payload=payload,
                                             audit=[root_index, condition, panel, index]))
        for mapping in MAPS:
            for index, row in enumerate(root["held"]):
                payload = request_payload("oracle_generate", identity, "OFF",
                                          oracle_prompt(root, mapping, row["context"]), row["seed"])
                requests.append(dict(id=digest(payload), payload=payload,
                                     audit=[root_index, mapping, "oracle", index]))
    require(len(requests) == 1504 and len({row["id"] for row in requests}) == 1504,
            "request crossing/collision")
    return requests


def validate_record(request, record):
    exact_keys(record, ("request", "attempts"))
    require(record["request"] == request["payload"], "cache payload mismatch")
    attempts = record["attempts"]
    require(isinstance(attempts, list) and 1 <= len(attempts) <= 2, "retry cap")
    if len(attempts) == 2:
        exact_keys(attempts[0], ("infrastructure_failure", "output"))
        require(isinstance(attempts[0]["infrastructure_failure"], str) and
                bool(attempts[0]["infrastructure_failure"]) and attempts[0]["output"] is None,
                "retry requires preserved pre-output failure")
    output = attempts[-1]
    if request["payload"]["kind"].endswith("score"):
        exact_keys(output, ("token_logprobs",))
        values = output["token_logprobs"]
        counts = request["payload"]["parameters"]["token_counts"]
        require(isinstance(values, list) and len(values) == 2, "two likelihoods")
        require(all(isinstance(part, list) and len(part) == count for part, count in zip(values, counts)),
                "full candidate likelihood required")
        require(all(type(value) in (int, float) and math.isfinite(value) and value <= 0
                    for part in values for value in part), "non-finite/invalid likelihood")
        totals = [sum(part) for part in values]
        require(all(math.isfinite(total) for total in totals), "non-finite summed likelihood")
        return totals
    exact_keys(output, ("text", "truncated"))
    require(output["text"] is None or isinstance(output["text"], str), "raw UTF-8 output")
    require(type(output["truncated"]) is bool, "truncation flag")
    return output


def validate_requests(material, requests):
    require(len(requests) == 1504, "request denominator")
    coordinates = set()
    identities, adapters = set(), {}
    for request in requests:
        exact_keys(request, ("id", "payload", "audit"))
        audit = request["audit"]
        require(isinstance(audit, list) and len(audit) == 4, "request audit")
        root_index, condition, panel, index = audit
        require(type(root_index) is int and root_index in (0, 1) and type(index) is int,
                "root/item coordinate")
        require(panel in ("primary", "spill", "oracle") and condition in CONDITIONS,
                "panel/condition")
        require(panel != "oracle" or condition in MAPS, "oracle map")
        root = material["roots"][root_index]
        rows = root["spill"] if panel == "spill" else root["held"]
        require(0 <= index < len(rows), "item coordinate")
        row = rows[index]
        payload = request["payload"]
        exact_keys(payload, ("kind", "identity", "adapter", "prompt", "seed", "candidates", "parameters"))
        operation = payload["kind"].split("_")[-1]
        require(operation in (("generate",) if panel == "oracle" else ("generate", "score")),
                "typed operation")
        coordinate = tuple(audit) + (operation,)
        require(coordinate not in coordinates, "duplicate request coordinate")
        coordinates.add(coordinate)
        prompt = oracle_prompt(root, condition, row["context"]) if panel == "oracle" else row["context"]
        counts = None
        if operation == "score":
            counts = payload["parameters"].get("token_counts")
            require(isinstance(counts, list) and len(counts) == 2 and counts[0] == counts[1] and
                    all(type(count) is int and 1 <= count <= 2048 for count in counts), "candidate counts")
        expected = request_payload(f"{panel}_{operation}", payload["identity"], payload["adapter"],
                                   prompt, row["seed"], counts)
        require(payload == expected and request["id"] == digest(expected), "serialized request projection")
        identities.add(digest(payload["identity"]))
        if condition == "OFF" or panel == "oracle":
            require(payload["adapter"] == "OFF", "OFF state")
        else:
            require(payload["adapter"] != "OFF", "missing adapter")
            key = (root_index, condition)
            require(key not in adapters or adapters[key] == payload["adapter"], "adapter identity drift")
            adapters[key] = payload["adapter"]
    require(len(coordinates) == 1504 and len(identities) == 1 and len(set(adapters.values())) == 4,
            "crossing/model/adapter identities")


def log_q(logs, target):
    maximum = max(logs)
    return logs[target] - maximum - math.log(sum(math.exp(value - maximum) for value in logs))


def balanced_accuracy(outputs, targets):
    require(len(outputs) == len(targets) and set(targets) == {0, 1}, "fixed BA denominator")
    return statistics.mean(sum(output == target for output, expected in zip(outputs, targets)
                               if expected == target) / targets.count(target) for target in (0, 1))


def classify(gates):
    exact_keys(gates, ("oracle_ok", "optimization_ok", "binding_ok", "interface_ok", "spill_ok"))
    require(all(type(value) is bool for value in gates.values()), "boolean gates")
    if not gates["oracle_ok"]:
        return "ASSAY_INVALID"
    if not gates["optimization_ok"]:
        return "OPTIMIZATION_INCONCLUSIVE"
    if not gates["interface_ok"]:
        return "INTERFACE_INVALID"
    if gates["binding_ok"] and not gates["spill_ok"]:
        return "BINDING_WITH_SPILL"
    return "MULTIKEY_BINDING_PASS" if all(gates.values()) else "GATEWAY_NEGATIVE"


def cell_gates(cell):
    return dict(
        oracle_ok=cell["oracle_BA"] >= .90,
        optimization_ok=all(value >= .50 for value in cell["key_NLL_gains"]),
        binding_ok=(cell["BA"] >= .80 and cell["OFF_gain"] >= .20 and
                    cell["BA"] - cell["opposite_BA"] >= .50 and
                    sum(value >= .50 for value in cell["key_margins"]) >= 12 and
                    all(row["accuracy"] >= .75 and row["margin_keys"] >= 6 for row in cell["strata"])),
        interface_ok=(cell["validity"] >= .95 and cell["multiple_ACT_rate"] == 0 and
                      all(row["validity"] >= .875 for row in cell["strata"])),
        spill_ok=all(row["mean_binary_TV"] <= .05 and row["legal_ACT_rate_change"] <= .05
                     for row in cell["spill"].values()))


def asymmetry_ok(plus_mean, minus_mean):
    return abs(plus_mean - minus_mean) <= .25


def reduce_records(material, requests, records):
    """Arithmetic only; caller must not confuse fixture labels with run finality."""
    validate_material(material)
    validate_requests(material, requests)
    require(len(requests) == 1504 and len({row["id"] for row in requests}) == 1504,
            "fixed request denominator")
    require(set(records) == {row["id"] for row in requests}, "missing/extra raw records")
    indexed = {}
    for request in requests:
        require(request["id"] == digest(request["payload"]), "request hash")
        key = tuple(request["audit"]) + (request["payload"]["kind"].split("_")[-1],)
        require(key not in indexed, "duplicate panel coordinate")
        indexed[key] = validate_record(request, records[request["id"]])

    def generation(root, condition, panel, index):
        return indexed[root, condition, panel, index, "generate"]

    def parsed(root, condition, panel, index):
        return parse_output(**generation(root, condition, panel, index))

    root_reports = []
    for root_index, root in enumerate(material["roots"]):
        gates = dict.fromkeys(("oracle_ok", "optimization_ok", "binding_ok", "interface_ok", "spill_ok"), True)
        cells = {}
        off = [parsed(root_index, "OFF", "primary", index)["action"] for index in range(64)]
        native_indices = [index for index, row in enumerate(root["spill"]) if row["family"] == "unrelated"]
        for condition in CONDITIONS:
            correct = sum(native_correct(expected=root["spill"][index]["expected"],
                                         **generation(root_index, condition, "spill", index))
                          for index in native_indices)
            gates["interface_ok"] &= correct == 8
        for mapping in MAPS:
            targets = [action(root_index, row["slot"], row["mode"], mapping) for row in root["held"]]
            outputs = [parsed(root_index, mapping, "primary", index) for index in range(64)]
            actions = [output["action"] for output in outputs]
            oracle = [parsed(root_index, mapping, "oracle", index)["action"] for index in range(64)]
            gains, margins = defaultdict(list), defaultdict(list)
            for index, (row, target) in enumerate(zip(root["held"], targets)):
                baseline = indexed[root_index, "OFF", "primary", index, "score"]
                fitted = indexed[root_index, mapping, "primary", index, "score"]
                key = (row["slot"], row["mode"])
                gains[key].append(log_q(fitted, target) - log_q(baseline, target))
                margins[key].append(fitted[target] - fitted[1 - target])
            key_gains = {key: statistics.median(values) for key, values in gains.items()}
            key_margins = {key: statistics.median(values) for key, values in margins.items()}
            ba = balanced_accuracy(actions, targets)
            opposite = balanced_accuracy(actions, [1 - target for target in targets])
            off_gain = ba - balanced_accuracy(off, targets)
            validity = sum(value is not None for value in actions) / 64
            multiple = sum(output["multiple_ACT"] for output in outputs) / 64
            oracle_ba = balanced_accuracy(oracle, targets)
            strata = []
            for stratum in range(2):
                indices = [index for index, row in enumerate(root["held"]) if row["stratum"] == stratum]
                strata.append(dict(accuracy=sum(actions[index] == targets[index] for index in indices) / 32,
                                   validity=sum(actions[index] is not None for index in indices) / 32,
                                   margin_keys=sum(value >= .5 for key, value in key_margins.items()
                                                   if key[0] // 4 == stratum)))
            spill = {}
            for family in ("missing", "unsupported", "neighbour", "unrelated"):
                indices = [index for index, row in enumerate(root["spill"]) if row["family"] == family]
                tv = statistics.mean(abs(math.exp(log_q(indexed[root_index, mapping, "spill", index, "score"], 0)) -
                                         math.exp(log_q(indexed[root_index, "OFF", "spill", index, "score"], 0)))
                                     for index in indices)
                change = statistics.mean(int(parsed(root_index, mapping, "spill", index)["action"] is not None) -
                                         int(parsed(root_index, "OFF", "spill", index)["action"] is not None)
                                         for index in indices)
                spill[family] = dict(mean_binary_TV=tv, legal_ACT_rate_change=change)
            cells[mapping] = dict(BA=ba, opposite_BA=opposite, OFF_gain=off_gain,
                                  oracle_BA=oracle_ba, validity=validity, multiple_ACT_rate=multiple,
                                  mean_NLL_gain=statistics.mean(list(itertools.chain.from_iterable(gains.values()))),
                                  key_NLL_gains=[key_gains[key] for key in sorted(key_gains)],
                                  key_margins=[key_margins[key] for key in sorted(key_margins)],
                                  strata=strata, spill=spill)
            for name, passed in cell_gates(cells[mapping]).items():
                gates[name] &= passed
        asymmetry = abs(cells["W+"]["mean_NLL_gain"] - cells["W-"]["mean_NLL_gain"])
        gates["optimization_ok"] &= asymmetry_ok(cells["W+"]["mean_NLL_gain"], cells["W-"]["mean_NLL_gain"])
        root_reports.append(dict(gates=gates, cells=cells, mean_gain_asymmetry=asymmetry,
                                 OFF_multiple_ACT_rate=sum(parsed(root_index, "OFF", "primary", index)["multiple_ACT"]
                                                            for index in range(64)) / 64))
    combined = {key: all(root["gates"][key] for root in root_reports) for key in root_reports[0]["gates"]}
    return dict(label=classify(combined), gates=combined, roots=root_reports)


def tree_hash(path):
    root = Path(path)
    require(root.is_dir() and not root.is_symlink(), "adapter tree")
    entries = []
    for child in sorted(root.rglob("*")):
        require(not child.is_symlink(), "tree symlink")
        if child.is_dir():
            continue
        require(child.is_file(), "non-regular tree entry")
        entries.append([child.relative_to(root).as_posix(), sha(child.read_bytes())])
    require(entries, "empty adapter tree")
    return digest(entries)


def checked_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts, "parent traversal")
    for parent in (path, *path.parents):
        require(not parent.is_symlink(), "symlink in path")
    return path


def run_path(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "relative run artifact required")
    root = checked_path(root)
    path = checked_path(root / relative)
    require(path.is_relative_to(root) and path != root, "artifact escaped run")
    return path


def create_run(path, protected):
    exact_keys(protected, PROTECTED_KINDS)
    root = checked_path(path)
    for value in protected.values():
        require(isinstance(value, str) and value, "protected root")
        protected_root = Path(value).resolve()
        require(not root.is_relative_to(protected_root) and not protected_root.is_relative_to(root),
                "protected-root overlap")
    require(root.parent.is_dir(), "existing parent required")
    root.mkdir(exist_ok=False)
    return root


def write_once(root, relative, value):
    root = checked_path(root)
    path = checked_path(root / relative)
    require(path.is_relative_to(root) and path != root, "output containment")
    require(path.parent.is_dir(), "output parent missing")
    with path.open("xb") as stream:
        stream.write(canonical(value))


def scope_receipt():
    base = Path(__file__).resolve().parents[1]
    receipt = {}
    for version, expected in SCOPE_HASHES.items():
        path = base / "research_loop" / "changes" / f"chg_20260911_multikey_writer_gateway_{version}_simple" / "exact_scope.md"
        require(sha(path.read_bytes()) == expected, "inherited scope changed")
        receipt[version] = expected
    return receipt


def inheritance_receipt():
    base = Path(__file__).resolve().parents[1]
    decisions = {}
    for version, expected in CONSENSUS_HASHES.items():
        path = base / "research_loop" / "changes" / f"chg_20260911_multikey_writer_gateway_{version}_simple" / "architecture_consensus.json"
        require(sha(path.read_bytes()) == expected, "inherited consensus changed")
        decisions[str(path.relative_to(base))] = expected
    for name in ("2026-09-11_v10r1_preimplementation_risk_audit.md",
                 "2026-09-11_v10r1_fit_variance_decision.md",
                 "2026-09-11_v10r1_seed2_congruence_review.md"):
        path = base / "research_notes" / name
        decisions[str(path.relative_to(base))] = sha(path.read_bytes())
    return dict(scopes=scope_receipt(), decision_hashes=decisions,
                authority="Standing builder authorization; no legacy human_required metadata gate",
                evidence="CPU_FIXTURE_ONLY")


def fixture_records(material, requests):
    records = {}
    for request in requests:
        root_index, condition, panel, index = request["audit"]
        payload = request["payload"]
        row = material["roots"][root_index]["spill" if panel == "spill" else "held"][index]
        target = 0 if panel == "spill" or condition == "OFF" else action(root_index, row["slot"], row["mode"], condition)
        if payload["kind"].endswith("score"):
            logs = [-3.0, -3.0]
            if panel == "primary" and condition != "OFF":
                logs[target], logs[1 - target] = -1.0, -5.0
            counts = payload["parameters"]["token_counts"]
            output = dict(token_logprobs=[[value / count] * count for value, count in zip(logs, counts)])
        else:
            text = row["expected"] if panel == "spill" and row["expected"] else f"ACT: a{target}\n"
            output = dict(text=text, truncated=False)
        records[request["id"]] = dict(request=payload, attempts=[output])
    return records


def cpu_fixture(path, protected):
    inherited = inheritance_receipt()
    root = create_run(path, protected)
    material = build_material()
    geometry = validate_material(material)
    sources = {}
    base = Path(__file__).resolve().parents[1]
    for name in ("organism_v6/multikey_writer_gateway_simple.py",
                 "tests/test_multikey_writer_gateway_simple.py", "gpu/multikey_writer_gateway_simple.sh"):
        sources[name] = sha((base / name).read_bytes())
    adapters = {}
    for root_index in range(2):
        for mapping_index, mapping in enumerate(MAPS):
            directory = root / f"fixture_adapter_{root_index}_{mapping_index}"
            directory.mkdir()
            write_once(directory, "NOT_A_REAL_ADAPTER.json", dict(root=root_index, mapping=mapping, fixture=True))
            adapters[f"{root_index}/{mapping}"] = tree_hash(directory)
    identity = dict(model=MODEL, model_sha256=digest("CPU_FAKE_MODEL"),
                    tokenizer_sha256=digest("CPU_CHARACTER_TOKENIZER"),
                    run_sha256=digest([str(root), material, sources]))
    requests = build_requests(material, identity, adapters, FixtureTokenizer())
    records = fixture_records(material, requests)
    fits = {}
    for root_index, root_data in enumerate(material["roots"]):
        for mapping in MAPS:
            fit = fit_projection(root_data["train"][mapping], material["config"]["fit_seeds"][root_index])
            encoded = [encode_candidate(FixtureTokenizer(), row["context"], row["target"]) for row in fit]
            fits[f"{root_index}/{mapping}"] = dict(
                input=fit, input_sha256=digest(fit), encoded_sha256=digest(encoded),
                tokenizer_kind="CPU_FAKE_CHARACTER", planned_optimizer_steps=len(fit) * RECIPE["epochs"])
    manifest = dict(version=VERSION, evidence="CPU_FIXTURE_ONLY", scientific_execution_ready=False,
                    pending=PENDING, material=material, identity=identity, adapters=adapters,
                    source_hashes=sources, inherited=inherited, protected=protected, output_root=str(root))
    report = dict(evidence="CPU_FIXTURE_ONLY", scientific_label=None,
                  fixture_result=reduce_records(material, requests, records), pending=PENDING)
    artifacts = {"manifest.json": manifest, "requests.json": requests, "raw.json": records,
                 "geometry.json": geometry, "fits.json": fits, "report.json": report,
                 "mwg10r1_inheritance_receipt.json": inherited}
    for name, value in artifacts.items():
        write_once(root, name, value)
    write_once(root, "CPU_FIXTURE_SEAL.json", dict(
        evidence="CPU_FIXTURE_ONLY", hashes={name: digest(value) for name, value in artifacts.items()},
        adapter_hashes=adapters))
    return report


def replay_fixture(path):
    root = checked_path(path)
    seal = json.loads(checked_path(root / "CPU_FIXTURE_SEAL.json").read_bytes())
    exact_keys(seal, ("evidence", "hashes", "adapter_hashes"))
    require(seal["evidence"] == "CPU_FIXTURE_ONLY", "fixture seal only")
    require(set(seal["hashes"]) == {"manifest.json", "requests.json", "raw.json", "geometry.json", "fits.json", "report.json",
                                   "mwg10r1_inheritance_receipt.json"}, "seal artifacts")
    data = {}
    for name, expected in seal["hashes"].items():
        raw = checked_path(root / name).read_bytes()
        require(sha(raw) == expected, "artifact hash changed")
        data[name] = json.loads(raw)
        require(canonical(data[name]) == raw, "noncanonical artifact")
    manifest = data["manifest.json"]
    require(manifest["evidence"] == "CPU_FIXTURE_ONLY" and not manifest["scientific_execution_ready"],
            "fixture cannot claim execution readiness")
    require(manifest["inherited"] == data["mwg10r1_inheritance_receipt.json"], "inheritance receipt mismatch")
    require(manifest["inherited"]["scopes"] == SCOPE_HASHES, "wrong effective scope")
    require(manifest["output_root"] == str(root), "run relocation")
    require(manifest["adapters"] == seal["adapter_hashes"], "adapter receipt mismatch")
    for root_index in range(2):
        for mapping_index, mapping in enumerate(MAPS):
            require(tree_hash(root / f"fixture_adapter_{root_index}_{mapping_index}") ==
                    manifest["adapters"][f"{root_index}/{mapping}"], "adapter tree changed")
    expected_requests = build_requests(manifest["material"], manifest["identity"], manifest["adapters"], FixtureTokenizer())
    require(canonical(expected_requests) == canonical(data["requests.json"]), "request projection changed")
    require(validate_material(manifest["material"]) == data["geometry.json"], "geometry receipt changed")
    require(set(data["fits.json"]) == {f"{root_index}/{mapping}" for root_index in range(2) for mapping in MAPS},
            "four fit projections")
    for root_index, root_data in enumerate(manifest["material"]["roots"]):
        for mapping in MAPS:
            fit = fit_projection(root_data["train"][mapping], manifest["material"]["config"]["fit_seeds"][root_index])
            encoded = [encode_candidate(FixtureTokenizer(), row["context"], row["target"]) for row in fit]
            expected = dict(input=fit, input_sha256=digest(fit), encoded_sha256=digest(encoded),
                            tokenizer_kind="CPU_FAKE_CHARACTER", planned_optimizer_steps=256)
            require(data["fits.json"][f"{root_index}/{mapping}"] == expected, "fit projection changed")
    report = dict(evidence="CPU_FIXTURE_ONLY", scientific_label=None,
                  fixture_result=reduce_records(manifest["material"], expected_requests, data["raw.json"]), pending=PENDING)
    require(digest(report) == seal["hashes"]["report.json"], "reducer replay mismatch")
    return report


def source_hashes():
    base = Path(__file__).resolve().parents[1]
    return {name: sha((base / name).read_bytes()) for name in SOURCE_PATHS}


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def snapshot_inventory(path):
    """Hash local HF snapshot bytes, including regular-file cache symlink targets."""
    root = Path(path).resolve(strict=True)
    require(root.is_dir(), "snapshot directory")
    entries = []
    for child in sorted(root.rglob("*")):
        if child.is_dir():
            require(not child.is_symlink(), "snapshot directory symlink")
            continue
        require(child.resolve(strict=True).is_file(), "non-regular snapshot file")
        entries.append([child.relative_to(root).as_posix(), file_hash(child)])
    require(entries, "empty snapshot")
    return dict(path=str(root), sha256=digest(entries), files=entries)


def environment_identity():
    return dict(python=platform.python_version(), packages={name: importlib.metadata.version(name) for name in PACKAGES})


def native_build_preflight():
    require(platform.python_implementation() == "CPython", "native build requires CPython")
    configured = os.environ.get("CC")
    compiler = shutil.which(configured) if configured else (shutil.which("gcc") or shutil.which("clang"))
    require(compiler is not None, "native build compiler missing (CC or gcc/clang)")
    compiler = str(Path(compiler).resolve(strict=True))
    paths = sysconfig.get_paths()
    includes = sorted({str(Path(paths[key]).resolve()) for key in ("include", "platinclude") if paths.get(key)})
    require(paths.get("include") and (Path(paths["include"]) / "Python.h").is_file(),
            "native build CPython development header missing: Python.h")
    require(any((Path(directory) / "pyconfig.h").is_file() for directory in includes),
            "native build CPython development header missing: pyconfig.h")
    headers = [[str(header), file_hash(header)] for directory in includes
               for header in sorted(Path(directory).rglob("*.h")) if header.is_file()]
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True, timeout=30)
    require(version.returncode == 0, "native build compiler version check failed: " + version.stderr)
    source = "#include <Python.h>\nint main(void) { return PY_MAJOR_VERSION == 3 ? 0 : 1; }\n"
    command = [compiler, "-std=c11", "-fPIC", "-c", "probe.c", "-o", "probe.o"]
    command.extend("-I" + directory for directory in includes)
    with tempfile.TemporaryDirectory(prefix="mwg-native-preflight-") as directory:
        (Path(directory) / "probe.c").write_text(source)
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=30)
        require(result.returncode == 0 and (Path(directory) / "probe.o").is_file(),
                "native build Python.h compilation failed: " + result.stderr)
    return dict(kind="CPU_NATIVE_BUILD_PREFLIGHT", python=platform.python_version(),
                triton_version=importlib.metadata.version("triton"),
                python_executable=str(Path(sys.executable).resolve()),
                compiler=compiler, compiler_sha256=file_hash(compiler),
                compiler_version=version.stdout, compiler_version_stderr=version.stderr,
                sysconfig_cc=sysconfig.get_config_var("CC"), include_directories=includes, headers=headers,
                environment={key: os.environ.get(key) for key in
                             ("CC", "PATH", "CPATH", "C_INCLUDE_PATH", "COMPILER_PATH", "GCC_EXEC_PREFIX")},
                command=command, source_sha256=sha(source.encode()), returncode=result.returncode,
                stdout=result.stdout, stderr=result.stderr, model_loaded=False, real_GPU_executed=False)


def config_template():
    return dict(
        model=MODEL, model_path="/absolute/local/pinned-snapshot",
        tokenizer_path="/absolute/local/pinned-snapshot", model_revision="REPLACE_WITH_40_HEX_REVISION",
        tokenizer_revision="REPLACE_WITH_40_HEX_REVISION", model_sha256="REPLACE_WITH_INVENTORY_HASH",
        tokenizer_sha256="REPLACE_WITH_INVENTORY_HASH", node="REPLACE_WITH_HOSTNAME_SHA256",
        gpu_uuid="GPU-REPLACE", driver_version="REPLACE", lease_end_unix=0, lease_cutoff_unix=0,
        environment=dict(python="REPLACE", packages={name: "REPLACE" for name in PACKAGES}),
        seeds=dict(identifier_seed=100, train_order_seed=200, held_order_seed=300, request_seed=400, fit_seeds=[0, 1]),
        protected={kind: f"/absolute/{kind}/root" for kind in sorted(PROTECTED_KINDS)},
        builder_preflight_reference="REPLACE_WITH_DATED_BUILDER_NOTE_REFERENCE",
        approved_intake="chg_20260911_multikey_writer_gateway_v10r1_simple",
        requested_scope="four clean-base rank8 fits; frozen V10R1 panels; no parenting or C11")


def validate_config(config):
    exact_keys(config, config_template())
    require(config["model"] == MODEL, "frozen model")
    for key in ("model_path", "tokenizer_path"):
        require(isinstance(config[key], str) and Path(config[key]).is_absolute(), "absolute snapshot path")
    for key in ("model_revision", "tokenizer_revision"):
        require(isinstance(config[key], str) and re.fullmatch(r"[0-9a-f]{40}", config[key]), "pinned revision")
    for key in ("model_sha256", "tokenizer_sha256"):
        require(isinstance(config[key], str) and re.fullmatch(r"[0-9a-f]{64}", config[key]), "snapshot content hash")
    require(isinstance(config["node"], str) and re.fullmatch(r"[0-9a-f]{64}", config["node"]), "pinned node hash")
    require(isinstance(config["gpu_uuid"], str) and re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", config["gpu_uuid"]), "GPU UUID")
    require(isinstance(config["driver_version"], str) and re.fullmatch(r"[0-9.]+", config["driver_version"]), "driver version")
    for key in ("lease_end_unix", "lease_cutoff_unix"):
        require(type(config[key]) in (int, float) and math.isfinite(config[key])
                and config[key] > 0, f"positive finite {key} required")
    require(config["lease_cutoff_unix"] <= config["lease_end_unix"] - LEASE_FINISH_BUFFER_SECONDS,
            "lease cutoff must be at least six hours before authoritative lease end")
    exact_keys(config["environment"], ("python", "packages"))
    exact_keys(config["environment"]["packages"], PACKAGES)
    require(all(isinstance(value, str) and value and "REPLACE" not in value for value in
                [config["environment"]["python"], *config["environment"]["packages"].values()]), "dependency versions")
    exact_keys(config["seeds"], ("identifier_seed", "train_order_seed", "held_order_seed", "request_seed", "fit_seeds"))
    validate_material(build_material(**config["seeds"]))
    exact_keys(config["protected"], PROTECTED_KINDS)
    require(all(isinstance(value, str) and Path(value).is_absolute() for value in config["protected"].values()), "protected roots")
    require(config["approved_intake"] == "chg_20260911_multikey_writer_gateway_v10r1_simple", "declared intake")
    require(config["requested_scope"] == config_template()["requested_scope"], "declared scope")
    require(isinstance(config["builder_preflight_reference"], str) and config["builder_preflight_reference"]
            and "REPLACE" not in config["builder_preflight_reference"], "builder preflight reference")
    return config


def profile_plan():
    return dict(version=REAL_VERSION, gpu_executed=False, fits=4, rows_per_fit=128,
                steps_per_fit=256, total_optimizer_steps=1024, A40_hours_cap=3.0,
                lease_finish_buffer_seconds=LEASE_FINISH_BUFFER_SECONDS, **EVIDENCE_BOUNDARY,
                processes=dict(fit=4, generation=5, scoring=5),
                requests=dict(primary_generation=384, oracle_generation=256,
                              spill_generation=240, primary_score=384, spill_score=240),
                profile="first 8 steps of each scheduled fit; never an extra fit",
                actual_GPU_seconds=None, scope="Seen-key conditional-policy carriage only")


def load_json(path):
    raw = checked_path(path).read_bytes()
    result = json.loads(raw)
    require(canonical(result) == raw, "noncanonical JSON artifact")
    return result


class HFFastTokenizer:
    def __init__(self, tokenizer):
        require(tokenizer.is_fast, "fast offset-capable tokenizer required")
        self.tokenizer = tokenizer
        self.eos_token_id = tokenizer.eos_token_id

    def __call__(self, text, **kwargs):
        result = self.tokenizer(text, **kwargs)
        return {key: result[key] for key in ("input_ids", "offset_mapping")}

    def decode(self, ids):
        return self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)


def load_local_tokenizer(config):
    from transformers import AutoTokenizer
    return HFFastTokenizer(AutoTokenizer.from_pretrained(
        config["tokenizer_path"], local_files_only=True, trust_remote_code=False, use_fast=True))


def pin_local_inputs(config):
    validate_config(config)
    require(environment_identity() == config["environment"], "environment changed")
    model = snapshot_inventory(config["model_path"])
    tokenizer = model if Path(config["model_path"]).resolve() == Path(config["tokenizer_path"]).resolve() else snapshot_inventory(config["tokenizer_path"])
    require(model["sha256"] == config["model_sha256"], "model snapshot changed")
    require(tokenizer["sha256"] == config["tokenizer_sha256"], "tokenizer snapshot changed")
    model_config = json.loads((Path(config["model_path"]) / "config.json").read_bytes())
    require(model_config.get("model_type") == "qwen2" and model_config.get("num_hidden_layers") == 28
            and model_config.get("hidden_size") == 3584, "Qwen2.5-7B configuration")
    return dict(model=model, tokenizer=tokenizer, environment=config["environment"])


def real_preflight(material, tokenizer):
    encoded_fits = {}
    context_pairs = {}
    generation_encodings = {}
    for root_index, root in enumerate(material["roots"]):
        for mapping_index, mapping in enumerate(MAPS):
            rows = fit_projection(root["train"][mapping], material["config"]["fit_seeds"][root_index])
            encoded_fits[f"fit_{root_index}_{mapping_index}"] = [encode_candidate(tokenizer, row["context"], row["target"]) for row in rows]
            for row in rows:
                context_pairs[digest(row["context"])] = token_pair(tokenizer, row["context"])
        for row in root["held"] + root["spill"]:
            context = row["context"]
            pairs = token_pair(tokenizer, context)
            context_pairs[digest(context)] = pairs
            prompt_ids = tokenizer(context, add_special_tokens=False, return_offsets_mapping=True)["input_ids"]
            prefix = [token for token, label in zip(pairs[0]["input_ids"], pairs[0]["labels"]) if label == -100]
            require(prompt_ids == prefix, "generation/scoring prefix mismatch")
            require(len(prompt_ids) + 32 <= 2048, "generation prompt length")
            generation_encodings[digest(context)] = prompt_ids
        for mapping in MAPS:
            for row in root["held"]:
                context = oracle_prompt(root, mapping, row["context"])
                ids = tokenizer(context, add_special_tokens=False, return_offsets_mapping=True)["input_ids"]
                require(ids and len(ids) + 32 <= 2048 and tokenizer.eos_token_id not in ids
                        and tokenizer.decode(ids) == context, "oracle tokenizer preflight")
                generation_encodings[digest(context)] = ids
    require(len(encoded_fits) == 4 and all(len(rows) == 128 for rows in encoded_fits.values()), "four encoded fits")
    return dict(kind="REAL_LOCAL_TOKENIZER", eos_token_id=tokenizer.eos_token_id,
                encoded_fits=encoded_fits, context_pairs=context_pairs,
                generation_encodings=generation_encodings,
                fitted=False, model_loaded=False)


def prepare_real(path, config, run_tests=True):
    require(run_tests, "CPU suite may not be bypassed")
    validate_config(config)
    require(config["lease_cutoff_unix"] > time.time(), "lease expired")
    native_build = native_build_preflight()
    pins = pin_local_inputs(config)
    tokenizer = load_local_tokenizer(config)
    material = build_material(**config["seeds"])
    preflight = real_preflight(material, tokenizer)
    inherited = inheritance_receipt()
    inherited["evidence"] = "REAL_EXECUTION_PREPARATION_ONLY"
    root = create_run(path, config["protected"])
    sources = source_hashes()
    artifacts = {"material.json": material, "tokenizer_preflight.json": preflight,
                 "native_build_preflight.json": native_build,
                 "profile_plan.json": profile_plan(), "mwg10r1_inheritance_receipt.json": inherited}
    fits = {}
    for root_index, root_data in enumerate(material["roots"]):
        for mapping_index, mapping in enumerate(MAPS):
            fit_id = f"fit_{root_index}_{mapping_index}"
            rows = fit_projection(root_data["train"][mapping], config["seeds"]["fit_seeds"][root_index])
            artifacts[f"{fit_id}_input.json"] = rows
            fits[fit_id] = dict(root=root_index, mapping=mapping, seed=config["seeds"]["fit_seeds"][root_index],
                               input_file=f"{fit_id}_input.json", input_sha256=digest(rows),
                               encoded_sha256=digest(preflight["encoded_fits"][fit_id]))
    blueprint_identity = dict(model=MODEL, model_sha256=config["model_sha256"], tokenizer_sha256=config["tokenizer_sha256"],
                              run_sha256=digest([str(root), material, config, sources]))
    placeholders = {f"{fit['root']}/{fit['mapping']}": digest(["PLANNED_NOT_TRAINED", fit_id, fit["input_sha256"]])
                    for fit_id, fit in fits.items()}
    artifacts["request_blueprint.json"] = dict(
        adapter_hashes_are_placeholders=True, identity=blueprint_identity, adapters=placeholders,
        requests=build_requests(material, blueprint_identity, placeholders, preflight=preflight))
    for name, value in artifacts.items():
        write_once(root, name, value)
    manifest = dict(version=REAL_VERSION, evidence="PREPARED_NOT_EXECUTED", output_root=str(root),
                    **EVIDENCE_BOUNDARY,
                    config=config, recipe=EXECUTION_RECIPE, fit_cap=4, A40_hours_cap=3.0,
                    request_contract=REQUEST_CONTRACT,
                    training_run_replication=False, root_seed_confounded=True,
                    source_hashes=sources, inputs=pins, fits=fits,
                    artifact_hashes={name: digest(value) for name, value in artifacts.items()})
    write_once(root, "manifest.json", manifest)
    base = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-B", "-m", "unittest", "tests.test_multikey_writer_gateway_simple", "-v"]
    result = subprocess.run(command, cwd=base, capture_output=True, timeout=180,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    with (root / "cpu_suite.stdout").open("xb") as stream:
        stream.write(result.stdout)
    with (root / "cpu_suite.stderr").open("xb") as stream:
        stream.write(result.stderr)
    require(source_hashes() == sources, "source changed during preparation")
    receipt = dict(manifest_sha256=digest(manifest), source_hashes=sources, command=command,
                   returncode=result.returncode, stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr),
                   real_GPU_executed=False)
    write_once(root, "mwg10r1_cpu_suite_receipt.json", receipt)
    require(result.returncode == 0, "CPU suite failed; preserve prepared artifacts")
    write_once(root, "mwg10r1_output_gate_receipt.json", dict(
        manifest_sha256=digest(manifest), tokenizer_preflight_sha256=digest(preflight),
        geometry=validate_material(material), real_tokenizer_pass=True, model_loaded=False))
    write_once(root, "mwg10r1_review_receipt.json", dict(
        status="NOT_AN_INDEPENDENT_APPROVAL", manifest_sha256=digest(manifest),
        source_hashes=sources, builder_preflight_reference=config["builder_preflight_reference"],
        authority="Standing builder scope; main integration owner schedules; no inferred scientific pass"))
    receipt_names = ("mwg10r1_cpu_suite_receipt.json", "mwg10r1_output_gate_receipt.json", "mwg10r1_review_receipt.json")
    write_once(root, "PREPARED_SEAL.json", dict(
        manifest_sha256=digest(manifest), receipt_hashes={name: file_hash(root / name) for name in receipt_names}))
    return dict(status="PREPARED_NOT_EXECUTED", run=str(root), manifest_sha256=digest(manifest),
                real_GPU_executed=False, next="main schedules execute --allow-gpu")


def validate_prepared(root, check_source=True):
    root = checked_path(root)
    seal = load_json(root / "PREPARED_SEAL.json")
    manifest = load_json(root / "manifest.json")
    require(manifest["version"] == REAL_VERSION and manifest["output_root"] == str(root), "real manifest identity")
    require(digest(manifest) == seal["manifest_sha256"], "manifest seal")
    require(set(seal["receipt_hashes"]) == {"mwg10r1_cpu_suite_receipt.json", "mwg10r1_output_gate_receipt.json",
                                          "mwg10r1_review_receipt.json"}, "complete prepared receipt set")
    validate_config(manifest["config"])
    require(manifest["recipe"] == EXECUTION_RECIPE and manifest["fit_cap"] == 4
            and manifest["A40_hours_cap"] == 3.0 and manifest["request_contract"] == REQUEST_CONTRACT,
            "frozen execution recipe/cap")
    if check_source:
        require(manifest["source_hashes"] == source_hashes(), "source changed after prepare")
        require("native_build_preflight.json" in manifest["artifact_hashes"], "native build preflight receipt missing")
    for name, expected in manifest["artifact_hashes"].items():
        require(Path(name).name == name and file_hash(checked_path(root / name)) == expected, "prepared artifact changed")
    for name, expected in seal["receipt_hashes"].items():
        require(Path(name).name == name and file_hash(checked_path(root / name)) == expected, "preflight receipt changed")
    suite = load_json(root / "mwg10r1_cpu_suite_receipt.json")
    require(suite["manifest_sha256"] == digest(manifest) and suite["returncode"] == 0
            and suite["source_hashes"] == manifest["source_hashes"], "CPU suite binding")
    require(file_hash(root / "cpu_suite.stdout") == suite["stdout_sha256"] and
            file_hash(root / "cpu_suite.stderr") == suite["stderr_sha256"], "CPU log identity")
    material = load_json(root / "material.json")
    require(material == build_material(**manifest["config"]["seeds"]), "material/config binding")
    validate_material(material)
    require(set(manifest["fits"]) == {f"fit_{root}_{mapping}" for root in range(2) for mapping in range(2)}, "four planned fits")
    preflight = load_json(root / "tokenizer_preflight.json")
    blueprint = load_json(root / "request_blueprint.json")
    require(blueprint["adapter_hashes_are_placeholders"] is True and
            blueprint["requests"] == build_requests(material, blueprint["identity"], blueprint["adapters"], preflight=preflight),
            "prefit request blueprint")
    return manifest


def gpu_identity(config):
    require(sha(platform.node().encode("utf-8")) == config["node"], "wrong execution node")
    result = subprocess.run(
        ["nvidia-smi", "-i", config["gpu_uuid"], "--query-gpu=uuid,name,driver_version", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=True, timeout=15)
    rows = [[field.strip() for field in line.split(",")] for line in result.stdout.splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) == 3, "single GPU identity")
    uuid, name, driver = rows[0]
    require(uuid == config["gpu_uuid"] and name in ("NVIDIA A40", "A40")
            and driver == config["driver_version"], "pinned A40 GPU/driver")
    return dict(node=config["node"], gpu_uuid=uuid, gpu_name=name, driver_version=driver)


def remaining_budget(started_monotonic, lease_cutoff, now_monotonic=None, now_wall=None):
    now_monotonic = time.monotonic() if now_monotonic is None else now_monotonic
    now_wall = time.time() if now_wall is None else now_wall
    return min(10800 - (now_monotonic - started_monotonic), lease_cutoff - now_wall)


def stop_owned_process(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)


def launch_worker(root, job, started_monotonic, config):
    require(remaining_budget(started_monotonic, config["lease_cutoff_unix"]) > 5, "A40/lease budget exhausted")
    stage = job["stage"]
    require(re.fullmatch(r"(?:fit_[01]_[01]|eval_(?:OFF|[01]_[01])_(?:generate|score))", stage), "stage name")
    job_file = f"{stage}_job.json"
    write_once(root, job_file, job)
    write_once(root, f"{stage}_STARTED.json", dict(stage=stage, job_sha256=digest(job), wall_start=time.time()))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=config["gpu_uuid"],
                       CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED=str(job["seed"]),
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    base = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-B", "-m", "organism_v6.multikey_writer_gateway_simple",
               "_worker", "--job", str(root / job_file)]
    begin = time.monotonic()
    with (root / f"{stage}.log").open("xb") as log:
        process = subprocess.Popen(command, cwd=base, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            seconds = remaining_budget(started_monotonic, config["lease_cutoff_unix"]) - 5
            require(seconds > 0, "budget exhausted before worker")
            returncode = process.wait(timeout=seconds)
        except BaseException:
            stop_owned_process(process)
            raise
    elapsed = time.monotonic() - begin
    write_once(root, f"{stage}_PROCESS.json", dict(
        stage=stage, job_sha256=digest(job), worker_pid=process.pid,
        returncode=returncode, elapsed_seconds=elapsed, log_sha256=file_hash(root / f"{stage}.log")))
    require(returncode == 0, f"{stage} failed; no retry or replacement fit")
    require(remaining_budget(started_monotonic, config["lease_cutoff_unix"]) >= 0, "A40/lease cap exceeded")
    receipt = load_json(root / f"{stage}_DONE.json")
    require(receipt["job_sha256"] == digest(job) and receipt["worker_pid"] == process.pid,
            "worker receipt binding")
    return receipt


def configure_torch(config, seed):
    import torch
    import numpy
    require(environment_identity() == config["environment"], "worker environment mismatch")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == config["gpu_uuid"] and
            os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "worker CUDA isolation/determinism")
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "exactly one visible GPU")
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    return torch


def load_hf_model(config, torch):
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(
        config["model_path"], local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.bfloat16, attn_implementation="eager")
    model.to("cuda:0")
    model.config.use_cache = False
    return model


def lora_tensors(model):
    return {name: parameter.detach().float().cpu().clone()
            for name, parameter in model.named_parameters() if ".lora_A." in name or ".lora_B." in name}


def tensor_digest(values):
    return digest([[name, list(value.shape), sha(value.numpy().tobytes())] for name, value in sorted(values.items())])


def validate_trainables(model):
    trainables = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    require(len(trainables) == 28 * 7 * 2, "unexpected LoRA trainable set")
    require(all(".lora_A." in name or ".lora_B." in name for name, _ in trainables), "base parameter trainable")
    return trainables


def finite_train_step(torch, model, optimizer, encoded):
    ids = torch.tensor([encoded["input_ids"]], dtype=torch.long, device="cuda:0")
    labels = torch.tensor([encoded["labels"]], dtype=torch.long, device="cuda:0")
    require((labels[:, 1:] != -100).any().item(), "targetless fit row")
    output = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=labels, use_cache=False)
    require(torch.isfinite(output.loss).item(), "non-finite loss; no batch skipped")
    optimizer.zero_grad(set_to_none=True)
    output.loss.backward()
    require(all(parameter.grad is not None and torch.isfinite(parameter.grad).all().item()
                for _, parameter in validate_trainables(model)), "non-finite/missing gradient")
    optimizer.step()
    require(all(torch.isfinite(parameter).all().item() for _, parameter in validate_trainables(model)), "non-finite LoRA update")
    torch.cuda.synchronize()
    return float(output.loss.detach().cpu())


def fit_worker(job, root, torch, tokenizer, base_receipt):
    from peft import LoraConfig, get_peft_model
    fit_path = run_path(root, job["input_file"])
    require(file_hash(fit_path) == job["input_sha256"], "worker fit input hash")
    rows = load_json(fit_path)
    require(len(rows) == 128, "128 rows per fit")
    for index, row in enumerate(rows):
        exact_keys(row, ("context", "target", "mask", "order", "seed", "recipe"))
        require(row["order"] == index and row["seed"] == job["seed"] and row["recipe"] == RECIPE
                and row["mask"] == "context_only" and row["target"] in CANDIDATES, "fit input projection")
    encoded = [encode_candidate(tokenizer, row["context"], row["target"]) for row in rows]
    require(digest(encoded) == job["encoded_sha256"], "worker encoding differs from preflight")
    base = load_hf_model(job["config"], torch)
    config = LoraConfig(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                        target_modules=list(RECIPE["target_modules"]), task_type="CAUSAL_LM",
                        init_lora_weights=True)
    model = get_peft_model(base, config)
    trainables = validate_trainables(model)
    initial = lora_tensors(model)
    require(all(torch.count_nonzero(value).item() == 0 for name, value in initial.items() if ".lora_B." in name),
            "nonstandard LoRA initialization")
    optimizer = torch.optim.AdamW([parameter for _, parameter in trainables], lr=3e-5,
                                 betas=(.9, .999), eps=1e-8, weight_decay=.01, foreach=False, fused=False)
    model.train()
    stage = job["stage"]
    write_once(root, f"{stage}_LOAD.json", dict(base_receipt, adapter="OFF_CLEAN_BASE",
                                             trainables=[name for name, _ in trainables], initial_lora_sha256=tensor_digest(initial)))
    losses = []
    begin = time.monotonic()
    with (root / f"{stage}_steps.jsonl").open("xb") as log:
        for epoch in range(2):
            for row_index, row in enumerate(encoded):
                require(time.time() < job["deadline_unix"] - 5, "fit deadline")
                loss = finite_train_step(torch, model, optimizer, row)
                losses.append(loss)
                log.write(canonical(dict(step=len(losses), epoch=epoch, row=row_index,
                                         loss=loss, seconds=time.monotonic() - begin)))
                log.flush()
                if len(losses) == 8:
                    elapsed = time.monotonic() - begin
                    write_once(root, f"{stage}_PROFILE.json", dict(
                        steps=8, seconds=elapsed, projected_256_step_seconds=elapsed * 32,
                        extra_fits=0, estimate_only=True, max_reserved_A40_hours=3.0))
    require(len(losses) == 256, "exact optimizer-step count")
    final = lora_tensors(model)
    update_norm = math.sqrt(sum(float((final[name] - initial[name]).square().sum()) for name in initial))
    require(math.isfinite(update_norm) and update_norm > 0, "no finite real parameter update")
    adapter_path = run_path(root, job["adapter_directory"])
    require(not adapter_path.exists(), "adapter output exists")
    adapter_path.mkdir()
    model.save_pretrained(str(adapter_path), safe_serialization=True)
    require((adapter_path / "adapter_model.safetensors").is_file() and
            (adapter_path / "adapter_config.json").is_file(), "complete safetensors adapter")
    return dict(base_receipt, stage=stage, fit_input_sha256=job["input_sha256"],
                encoded_sha256=job["encoded_sha256"], optimizer_steps=256,
                target_tokens=sum(sum(label != -100 for label in row["labels"]) for row in encoded) * 2,
                initial_lora_sha256=tensor_digest(initial), final_lora_sha256=tensor_digest(final),
                update_norm=update_norm, mean_loss=statistics.mean(losses),
                adapter_sha256=tree_hash(adapter_path), trainables=[name for name, _ in trainables],
                recipe=EXECUTION_RECIPE, steps_sha256=file_hash(root / f"{stage}_steps.jsonl"))


def score_request(torch, model, tokenizer, payload):
    results = []
    pairs = token_pair(tokenizer, payload["prompt"])
    require([sum(label != -100 for label in pair["labels"]) for pair in pairs] ==
            payload["parameters"]["token_counts"], "scoring preflight token counts")
    for encoded in pairs:
        ids = torch.tensor([encoded["input_ids"]], dtype=torch.long, device="cuda:0")
        with torch.inference_mode():
            logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
            probabilities = torch.log_softmax(logits[0].float(), dim=-1)
            values = [float(probabilities[index - 1, token].cpu())
                      for index, (token, label) in enumerate(zip(encoded["input_ids"], encoded["labels"])) if label != -100]
        require(all(math.isfinite(value) for value in values), "non-finite scoring")
        results.append(values)
    return dict(token_logprobs=results), dict(candidate_input_ids=[pair["input_ids"] for pair in pairs],
                                            candidate_labels=[pair["labels"] for pair in pairs])


def generate_request(torch, model, tokenizer, payload):
    from transformers import GenerationConfig
    encoded = tokenizer(payload["prompt"], add_special_tokens=False, return_offsets_mapping=True)
    ids = torch.tensor([encoded["input_ids"]], dtype=torch.long, device="cuda:0")
    require(ids.shape[1] + 32 <= 2048, "generation length")
    config = GenerationConfig(do_sample=False, max_new_tokens=32, eos_token_id=tokenizer.eos_token_id,
                              pad_token_id=tokenizer.eos_token_id, use_cache=True)
    with torch.inference_mode():
        generated = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), generation_config=config)
    continuation = generated[0, ids.shape[1]:].tolist()
    ended = bool(continuation) and continuation[-1] == tokenizer.eos_token_id
    content = continuation[:-1] if ended else continuation
    text = tokenizer.decode(content)
    return dict(text=text, truncated=len(continuation) >= 32 and not ended), dict(
        prompt_input_ids=encoded["input_ids"], generated_ids=continuation,
        decoded_with_terminal_eos=tokenizer.decode(continuation), eos_terminated=ended)


def evaluation_worker(job, root, torch, tokenizer, base_receipt):
    from peft import PeftModel
    payloads = load_json(run_path(root, job["requests_file"]))
    require(digest(payloads) == job["requests_sha256"], "worker request input")
    require(payloads, "empty evaluation stage")
    model = load_hf_model(job["config"], torch)
    if job["adapter_sha256"] != "OFF":
        adapter_path = run_path(root, job["adapter_directory"])
        require(tree_hash(adapter_path) == job["adapter_sha256"], "adapter hash before fresh load")
        model = PeftModel.from_pretrained(model, str(adapter_path), is_trainable=False)
        require(tensor_digest(lora_tensors(model)) == job["expected_lora_sha256"], "fresh-reload LoRA tensor mismatch")
    else:
        require(not lora_tensors(model), "OFF model has adapter")
    model.requires_grad_(False)
    model.eval()
    write_once(root, f"{job['stage']}_LOAD.json", dict(base_receipt, adapter=job["adapter_sha256"],
                                                      operation=job["operation"], training=False))
    output_dir = run_path(root, job["raw_directory"])
    output_dir.mkdir(exist_ok=False)
    for payload in payloads:
        require(time.time() < job["deadline_unix"] - 5, "evaluation deadline")
        require(payload["adapter"] == job["adapter_sha256"] and
                payload["kind"].endswith(job["operation"]), "typed worker input")
        torch.manual_seed(payload["seed"])
        torch.cuda.manual_seed_all(payload["seed"])
        random.seed(payload["seed"])
        if job["operation"] == "score":
            output, trace = score_request(torch, model, tokenizer, payload)
        else:
            output, trace = generate_request(torch, model, tokenizer, payload)
        torch.cuda.synchronize()
        request_id = digest(payload)
        record = dict(request=payload, attempts=[output])
        validate_record(dict(payload=payload), record)
        write_once(output_dir, request_id + ".json", record)
        write_once(output_dir, request_id + "_trace.json", dict(request_sha256=request_id, **trace))
    return dict(base_receipt, stage=job["stage"], adapter_sha256=job["adapter_sha256"],
                operation=job["operation"], requests_sha256=job["requests_sha256"],
                request_count=len(payloads), raw_tree_sha256=tree_hash(output_dir))


def worker_main(job_path):
    job_path = checked_path(job_path)
    root = job_path.parent
    job = load_json(job_path)
    require(re.fullmatch(r"(?:fit_[01]_[01]|eval_(?:OFF|[01]_[01])_(?:generate|score))", job["stage"]), "worker stage")
    started = load_json(root / f"{job['stage']}_STARTED.json")
    execution = load_json(root / "EXECUTION_STARTED.json")
    require(started["job_sha256"] == digest(job) and execution["manifest_sha256"] == job["manifest_sha256"],
            "worker not bound to scheduled stage")
    write_once(root, f"{job['stage']}_CLAIMED.json", dict(job_sha256=digest(job), worker_pid=os.getpid()))
    require(job["version"] == REAL_VERSION and job["source_hashes"] == source_hashes(), "worker source identity")
    require(job["recipe"] == EXECUTION_RECIPE, "worker recipe")
    require(time.time() < job["deadline_unix"] - 5, "worker deadline")
    pins = pin_local_inputs(job["config"])
    hardware = gpu_identity(job["config"])
    tokenizer = load_local_tokenizer(job["config"])
    torch = configure_torch(job["config"], job["seed"])
    base_receipt = dict(backend="HF_LOCAL_PINNED", worker_pid=os.getpid(), job_sha256=digest(job),
                        manifest_sha256=job["manifest_sha256"], environment_sha256=digest(pins["environment"]),
                        model_sha256=pins["model"]["sha256"], tokenizer_sha256=pins["tokenizer"]["sha256"],
                        hardware=hardware, seed=job["seed"], source_hashes=job["source_hashes"])
    if job["operation"] == "fit":
        receipt = fit_worker(job, root, torch, tokenizer, base_receipt)
    else:
        require(job["operation"] in ("generate", "score"), "worker operation")
        receipt = evaluation_worker(job, root, torch, tokenizer, base_receipt)
    write_once(root, f"{job['stage']}_DONE.json", receipt)
    return dict(stage=job["stage"], status="DONE")


def assert_gpu_idle(config):
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"],
                            capture_output=True, text=True, check=True, timeout=15)
    require(all(line.split(",")[0].strip() != config["gpu_uuid"] for line in result.stdout.splitlines()),
            "selected GPU has existing compute processes; main must resolve ownership")


def execute_real(path, allow_gpu=False):
    require(allow_gpu, "GPU execution requires explicit --allow-gpu; main schedules")
    root = checked_path(path)
    manifest = validate_prepared(root)
    config = manifest["config"]
    require(not (root / "EXECUTION_STARTED.json").exists(), "execution already attempted; no rescue or refit")
    require(native_build_preflight() == load_json(root / "native_build_preflight.json"),
            "native build environment changed after prepare")
    pins = pin_local_inputs(config)
    hardware = gpu_identity(config)
    assert_gpu_idle(config)
    tokenizer = load_local_tokenizer(config)
    material = load_json(root / "material.json")
    preflight = load_json(root / "tokenizer_preflight.json")
    require(real_preflight(material, tokenizer) == preflight, "real preflight changed")
    begin = time.monotonic()
    wall_start = time.time()
    require(config["lease_cutoff_unix"] - wall_start > 5, "insufficient lease time")
    deadline = min(wall_start + 10800, config["lease_cutoff_unix"])
    write_once(root, "EXECUTION_STARTED.json", dict(
        manifest_sha256=digest(manifest), hardware=hardware, wall_start=wall_start,
        deadline_unix=deadline, A40_hours_cap=3.0, parent_pid=os.getpid(),
        environment_sha256=digest(pins["environment"])))
    stages = []
    common = dict(version=REAL_VERSION, config=config, recipe=EXECUTION_RECIPE,
                  manifest_sha256=digest(manifest), source_hashes=manifest["source_hashes"], deadline_unix=deadline)
    try:
        adapters, fit_receipts = {}, {}
        for fit_id, fit in manifest["fits"].items():
            job = dict(common, stage=fit_id, operation="fit", seed=fit["seed"],
                       input_file=fit["input_file"], input_sha256=fit["input_sha256"],
                       encoded_sha256=fit["encoded_sha256"], adapter_directory=f"adapter_{fit_id}")
            receipt = launch_worker(root, job, begin, config)
            stages.append(fit_id)
            fit_receipts[fit_id] = receipt
            require(receipt["optimizer_steps"] == 256 and receipt["update_norm"] > 0, "incomplete real fit")
            adapters[f"{fit['root']}/{fit['mapping']}"] = receipt["adapter_sha256"]
        require(len(adapters) == 4 and len(set(adapters.values())) == 4, "four completed unique adapters")
        identity = dict(model=MODEL, model_sha256=config["model_sha256"],
                        tokenizer_sha256=config["tokenizer_sha256"], run_sha256=digest(manifest))
        requests = build_requests(material, identity, adapters, tokenizer)
        validate_requests(material, requests)
        write_once(root, "requests.json", requests)
        write_once(root, "adapter_hashes.json", adapters)
        states = [("OFF", "OFF", None)] + [(fit_id.removeprefix("fit_"), fit_receipts[fit_id]["adapter_sha256"], fit_id)
                                            for fit_id in manifest["fits"]]
        for state, adapter_hash, fit_id in states:
            for operation in ("generate", "score"):
                stage = f"eval_{state}_{operation}"
                payloads = [request["payload"] for request in requests if request["payload"]["adapter"] == adapter_hash
                            and request["payload"]["kind"].endswith(operation)]
                write_once(root, f"{stage}_input.json", payloads)
                job = dict(common, stage=stage, operation=operation, seed=0,
                           requests_file=f"{stage}_input.json", requests_sha256=digest(payloads),
                           adapter_sha256=adapter_hash, adapter_directory=None if fit_id is None else f"adapter_{fit_id}",
                           expected_lora_sha256=None if fit_id is None else fit_receipts[fit_id]["final_lora_sha256"],
                           raw_directory=f"raw_{stage}")
                launch_worker(root, job, begin, config)
                stages.append(stage)
        elapsed = time.monotonic() - begin
        require(remaining_budget(begin, config["lease_cutoff_unix"]) >= 0 and len(stages) == 14, "complete bounded execution")
        write_once(root, "RESOURCE_RECEIPT.json", dict(
            manifest_sha256=digest(manifest), elapsed_reserved_GPU_seconds=elapsed,
            A40_hours=elapsed / 3600, GPU_count=1, wall_start=wall_start, wall_end=time.time(),
            deadline_unix=deadline, stages=stages, fit_count=4, optimizer_steps=1024, hardware=hardware))
        report = validate_real_evidence(root, manifest)
        write_once(root, "report_real.json", report)
        files = {}
        for child in sorted(root.rglob("*")):
            require(not child.is_symlink(), "run symlink before seal")
            if child.is_file():
                files[child.relative_to(root).as_posix()] = file_hash(child)
        write_once(root, "REAL_EXECUTION_SEAL.json", dict(version=REAL_VERSION, files=files,
                                                         report_sha256=digest(report), evidence="REAL_GPU_EXECUTION"))
        replay_real(root)
        return report
    except BaseException as error:
        if not (root / "NONREPORTABLE_ABORT.json").exists():
            write_once(root, "NONREPORTABLE_ABORT.json", dict(
                evidence="INCOMPLETE_REAL_EXECUTION", scientific_label=None, error=str(error),
                completed_stages=stages, elapsed_reserved_GPU_seconds=time.monotonic() - begin,
                no_retry=True))
        raise


def validate_real_evidence(root, manifest):
    """CPU replay over all real raw files and bound load/fit/process receipts."""
    require(not (root / "NONREPORTABLE_ABORT.json").exists(), "aborted run is non-reportable")
    config = manifest["config"]
    material = load_json(root / "material.json")
    preflight = load_json(root / "tokenizer_preflight.json")
    require(preflight["kind"] == "REAL_LOCAL_TOKENIZER" and not preflight["fitted"] and not preflight["model_loaded"],
            "real tokenizer pre-model receipt")
    resource = load_json(root / "RESOURCE_RECEIPT.json")
    started = load_json(root / "EXECUTION_STARTED.json")
    require(resource["manifest_sha256"] == digest(manifest) and started["manifest_sha256"] == digest(manifest), "resource binding")
    require(resource["fit_count"] == 4 and resource["optimizer_steps"] == 1024 and resource["GPU_count"] == 1
            and 0 < resource["elapsed_reserved_GPU_seconds"] <= 10800 and resource["A40_hours"] <= 3
            and resource["wall_end"] <= min(started["deadline_unix"], config["lease_cutoff_unix"]), "bounded resource evidence")
    require(resource["A40_hours"] == resource["elapsed_reserved_GPU_seconds"] / 3600
            and resource["hardware"]["gpu_uuid"] == config["gpu_uuid"]
            and resource["hardware"]["node"] == config["node"], "resource identity/arithmetic")
    expected_stages = list(manifest["fits"]) + [f"eval_{state}_{operation}" for state in ("OFF", "0_0", "0_1", "1_0", "1_1")
                                             for operation in ("generate", "score")]
    require(resource["stages"] == expected_stages, "stage order/count")
    adapters = load_json(root / "adapter_hashes.json")
    require(len(adapters) == 4 and len(set(adapters.values())) == 4, "four adapter hashes")
    identity = dict(model=MODEL, model_sha256=config["model_sha256"], tokenizer_sha256=config["tokenizer_sha256"], run_sha256=digest(manifest))
    requests = load_json(root / "requests.json")
    expected = build_requests(material, identity, adapters, preflight=preflight)
    require(requests == expected, "real request schedule")
    records = {}
    worker_pids = []
    elapsed_processes = 0
    for stage in expected_stages:
        job = load_json(root / f"{stage}_job.json")
        receipt = load_json(root / f"{stage}_DONE.json")
        process = load_json(root / f"{stage}_PROCESS.json")
        load = load_json(root / f"{stage}_LOAD.json")
        launch = load_json(root / f"{stage}_STARTED.json")
        require(job["manifest_sha256"] == digest(manifest) and job["config"] == config and job["recipe"] == EXECUTION_RECIPE,
                "stage configuration")
        require(job["source_hashes"] == manifest["source_hashes"], "stage source binding")
        require(all(row["job_sha256"] == digest(job) for row in (receipt, process, load, launch)), "stage receipt binding")
        require(receipt["backend"] == load["backend"] == "HF_LOCAL_PINNED" and
                receipt["hardware"] == load["hardware"] == resource["hardware"] == started["hardware"], "real HF hardware/load evidence")
        require(receipt["model_sha256"] == load["model_sha256"] == config["model_sha256"] and
                receipt["tokenizer_sha256"] == load["tokenizer_sha256"] == config["tokenizer_sha256"] and
                receipt["environment_sha256"] == load["environment_sha256"] == digest(config["environment"]), "load identity")
        require(receipt["source_hashes"] == load["source_hashes"] == manifest["source_hashes"], "load/fit source hashes")
        require(process["returncode"] == 0 and process["worker_pid"] == receipt["worker_pid"] == load["worker_pid"], "fresh worker receipt")
        require(file_hash(root / f"{stage}.log") == process["log_sha256"], "worker log hash")
        require(process["elapsed_seconds"] > 0, "measured process time")
        elapsed_processes += process["elapsed_seconds"]
        worker_pids.append(process["worker_pid"])
        if stage.startswith("fit_"):
            fit = manifest["fits"][stage]
            require(receipt["optimizer_steps"] == 256 and receipt["recipe"] == EXECUTION_RECIPE and
                    math.isfinite(receipt["update_norm"]) and receipt["update_norm"] > 0, "exact real update")
            require(receipt["seed"] == job["seed"] == fit["seed"] and receipt["fit_input_sha256"] == fit["input_sha256"] and
                    receipt["encoded_sha256"] == fit["encoded_sha256"], "fit identity/seed")
            adapter_hash = tree_hash(root / f"adapter_{stage}")
            require(adapter_hash == receipt["adapter_sha256"] == adapters[f"{fit['root']}/{fit['mapping']}"], "adapter tree receipt")
            require(file_hash(root / f"{stage}_steps.jsonl") == receipt["steps_sha256"], "step trace hash")
            steps = [json.loads(line) for line in (root / f"{stage}_steps.jsonl").read_bytes().splitlines()]
            require(len(steps) == 256 and [row["step"] for row in steps] == list(range(1, 257)) and
                    all(row["epoch"] == index // 128 and row["row"] == index % 128 and math.isfinite(row["loss"])
                        for index, row in enumerate(steps)), "exact step trace/no skips")
            require(load["adapter"] == "OFF_CLEAN_BASE", "fit is not clean-base")
            profile = load_json(root / f"{stage}_PROFILE.json")
            require(profile["steps"] == 8 and profile["extra_fits"] == 0 and profile["seconds"] >= 0,
                    "bounded in-fit profile")
        else:
            require(load["training"] is False and load["adapter"] == job["adapter_sha256"], "eval fresh-load state")
            payloads = load_json(run_path(root, job["requests_file"]))
            require(digest(payloads) == job["requests_sha256"] == receipt["requests_sha256"] and
                    len(payloads) == receipt["request_count"], "eval input binding")
            require(payloads == [request["payload"] for request in requests
                                 if request["payload"]["adapter"] == job["adapter_sha256"] and
                                 request["payload"]["kind"].endswith(job["operation"])], "typed evaluation subset")
            directory = run_path(root, job["raw_directory"])
            require(tree_hash(directory) == receipt["raw_tree_sha256"], "raw tree binding")
            require(len(list(directory.iterdir())) == 2 * len(payloads), "raw/trace count")
            for payload in payloads:
                request_id = digest(payload)
                require(request_id not in records, "duplicate raw request")
                records[request_id] = load_json(directory / f"{request_id}.json")
                trace = load_json(directory / f"{request_id}_trace.json")
                require(trace["request_sha256"] == request_id, "raw token trace binding")
                if job["operation"] == "score":
                    pairs = preflight["context_pairs"][digest(payload["prompt"])]
                    require(trace["candidate_input_ids"] == [pair["input_ids"] for pair in pairs] and
                            trace["candidate_labels"] == [pair["labels"] for pair in pairs], "score tokens differ from training preflight")
                else:
                    require(trace["prompt_input_ids"] == preflight["generation_encodings"][digest(payload["prompt"])], "generation input tokens")
    require(len(set(worker_pids)) == 14, "fresh process per fit and generation/scoring load")
    require(elapsed_processes <= resource["elapsed_reserved_GPU_seconds"], "process/resource accounting")
    result = reduce_records(material, requests, records)
    return dict(version=REAL_VERSION, evidence="REAL_GPU_EXECUTION", scientific_label=result["label"],
                **EVIDENCE_BOUNDARY,
                result=result, manifest_sha256=digest(manifest), request_count=len(records),
                A40_hours=resource["A40_hours"], fit_count=4, training_run_replication=False,
                root_seed_confounded=True, scope="Four fitted seen-key conditional-policy instances; not retention, parenting, or reliability")


def replay_real(path):
    root = checked_path(path)
    manifest = validate_prepared(root, check_source=False)
    seal = load_json(root / "REAL_EXECUTION_SEAL.json")
    require(seal["version"] == REAL_VERSION and seal["evidence"] == "REAL_GPU_EXECUTION", "real seal required")
    found = set()
    for child in root.rglob("*"):
        require(not child.is_symlink(), "run symlink")
        if child.is_file() and child.name != "REAL_EXECUTION_SEAL.json":
            found.add(child.relative_to(root).as_posix())
    require(found == set(seal["files"]), "sealed file inventory changed")
    for name, expected in seal["files"].items():
        path = checked_path(root / name)
        require(path.is_relative_to(root) and file_hash(path) == expected, "sealed bytes changed")
    report = validate_real_evidence(root, manifest)
    require(digest(report) == seal["report_sha256"] == file_hash(root / "report_real.json"), "real reducer replay mismatch")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture", help="seal synthetic CPU-only artifacts, never a scientific run")
    fixture.add_argument("--out", required=True)
    for kind in sorted(PROTECTED_KINDS):
        fixture.add_argument(f"--protected-{kind}", required=True)
    replay = commands.add_parser("replay", help="read-only replay of a CPU fixture seal")
    replay.add_argument("--run", required=True)
    commands.add_parser("config-template", help="print required execution configuration; no model loads")
    commands.add_parser("profile-plan", help="print bounded four-fit work counts; no GPU profiling launched")
    commands.add_parser("environment", help="print local dependency versions without model/GPU loading")
    inventory = commands.add_parser("inventory", help="hash a local snapshot without network/model loading")
    inventory.add_argument("--snapshot", required=True)
    prepare = commands.add_parser("prepare", help="local real tokenizer and CPU checks; never loads a model")
    prepare.add_argument("--config", required=True)
    prepare.add_argument("--out", required=True)
    execute = commands.add_parser("execute", help="main-scheduled real four-fit experiment; requires --allow-gpu")
    execute.add_argument("--run", required=True)
    execute.add_argument("--allow-gpu", action="store_true")
    real_replay = commands.add_parser("replay-real", help="read-only replay of a sealed real experiment")
    real_replay.add_argument("--run", required=True)
    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("--job", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "config-template":
            result = config_template()
        elif args.command == "profile-plan":
            result = profile_plan()
        elif args.command == "environment":
            result = environment_identity()
        elif args.command == "inventory":
            result = snapshot_inventory(args.snapshot)
        elif args.command == "prepare":
            result = prepare_real(args.out, json.loads(Path(args.config).read_bytes()))
        elif args.command == "execute":
            result = execute_real(args.run, args.allow_gpu)
        elif args.command == "replay-real":
            result = replay_real(args.run)
        elif args.command == "_worker":
            result = worker_main(args.job)
        elif args.command == "replay":
            result = replay_fixture(args.run)
        else:
            result = cpu_fixture(args.out, {kind: getattr(args, f"protected_{kind}") for kind in PROTECTED_KINDS})
        sys.stdout.buffer.write(canonical(result))
        return 0
    except (ContractError, OSError, KeyError, TypeError, ValueError, RuntimeError,
            ImportError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"NONREPORTABLE_ABORT: {error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
