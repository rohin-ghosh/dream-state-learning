"""Fixed semantic Q0: CPU prepare/preflight, opt-in four-fit execution, CPU replay.

Exactly 1712 W0 requests; the verified external carrier is eligibility evidence,
never writer data. Grammar is reused DEV grammar, not globally novel. No C11,
clean-lineage, parenting, retention, or automatic successor claim is supported.
Main supplies a pinned protocol and verified carrier-proof/output files. No old
carrier replay is invoked from this checkout. A launch must inherit the pinned
GPU UUID in CUDA_VISIBLE_DEVICES to retain main's advertised reservation. Main
owns the full device/queue precheck and final reservation-release audit.

One controller has a three-hour/lease bound. Each fresh stage reuses the carrier
GNU timeout/owned-group primitive with at most one hour including cleanup reserve.
Its escaped-group, killed-supervisor, early-orphan-descendant and kernel-wait
limitations still apply; this is not an independent cgroup guard.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import itertools
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time

from . import multikey_writer_gateway_simple as w0
from . import semantic_carrier_diagnostic as carrier
from . import writer_interface_calibration as cal


VERSION = "semantic-writer-Q0-20260912-v1"
RECIPE_SHA256 = "c86ea11f7977df288c033304f081105d5bfacdbc9635c259ca0635f2102829cc"
CARRIER_REPLAY_SHA256 = "e99f4ca68fc720fcea0d602ae2d562bdfc7306354fccb055a97b1ac7036df3bd"
CARRIER_CAPSULE_SHA256 = "053bea4b16428d401d5e7532fc2c68d8cd91063d90e31bb6fc1a9a9526c478ad"
MAX_SECONDS = 10800
STATES = {f"r{root}_{name}": (root, mapping) for root in range(2)
          for name, mapping in (("plus", "W+"), ("minus", "W-"))}
FAMILIES = {"missing": 8, "unsupported": 8, "neighbour": 16, "wrong_root": 64}
COUNTS = dict(total=1712, generate=880, score=832, candidate_forwards=1664,
              OFF=400, per_adapter=328, fits=4, steps_per_fit=256)
BOUNDARY = dict(clean_lineage=False, training_run_replication=False, root_seed_confounded=True,
    grammar="reused_w0_DEV_8_train_4_held_forms", material_origin="namespaced_synthetic_researcher_authored",
    acquisition_metric="conditional_two_candidate_logq_gain", raw_target_sum_gain="diagnostic_only",
    formal_C11_custody="DEFERRED", automatic_followup=False,
    scope="four supervised seen-key semantic policy instances; not parenting or retention",
    official_model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY")


def config_template():
    return dict(model=w0.MODEL, model_path="/absolute/local/base-snapshot", tokenizer_path="/absolute/local/base-snapshot",
        model_revision="REPLACE_40_HEX", tokenizer_revision="REPLACE_40_HEX",
        model_sha256="REPLACE_64_HEX", tokenizer_sha256="REPLACE_64_HEX",
        environment={"python": "REPLACE", "packages": {}}, node="REPLACE_NODE_SHA256",
        gpu_uuid="GPU-REPLACE", driver_version="REPLACE", lease_end_unix=0, lease_cutoff_unix=0, deadline_unix=0,
        protected_paths=[], approved_intake="REPLACE_MAIN_PROTOCOL_REFERENCE",
        builder_preflight_reference="REPLACE_DATED_BUILDER_NOTE",
        requested_scope="semantic Q0 four fresh fits and 1712 requests; C11 deferred; no followup",
        protocol_path="/absolute/frozen-protocol.md", protocol_sha256="REPLACE_64_HEX",
        carrier_proof_path="/absolute/verified-carrier-proof.json", carrier_proof_sha256="REPLACE_64_HEX")


def proof_template():
    return dict(version="main-verified-semantic-carrier-v1", verified_by_main=False,
        verification_reference="REPLACE_MAIN_VERIFICATION_REFERENCE", carrier_source_ref="241dd86e",
        verified_replay_sha256=CARRIER_REPLAY_SHA256, capsule_sha256=CARRIER_CAPSULE_SHA256,
        model_sha256="REPLACE_64_HEX", tokenizer_sha256="REPLACE_64_HEX",
        output_path="/absolute/original-carrier-report.json", output_sha256="REPLACE_64_HEX")


def read_json(path):
    return json.loads(Path(path).read_text())


def validate_config(config):
    w0.exact_keys(config, config_template())
    w0.require(w0.digest(w0.EXECUTION_RECIPE) == RECIPE_SHA256, "frozen full recipe drift")
    w0.require(config["model"] == w0.MODEL and config["requested_scope"] == config_template()["requested_scope"], "frozen scope/base")
    for key in ("approved_intake", "builder_preflight_reference"):
        w0.require(isinstance(config[key], str) and config[key] and "REPLACE" not in config[key], key)
    for key, length in (("model_revision", 40), ("tokenizer_revision", 40), ("model_sha256", 64),
                        ("tokenizer_sha256", 64), ("node", 64), ("protocol_sha256", 64), ("carrier_proof_sha256", 64)):
        w0.require(isinstance(config[key], str) and re.fullmatch(f"[0-9a-f]{{{length}}}", config[key]), key)
    for key in ("model_path", "tokenizer_path", "protocol_path", "carrier_proof_path"):
        w0.require(isinstance(config[key], str) and Path(config[key]).is_absolute(), key)
    w0.require(isinstance(config["protected_paths"], list) and all(isinstance(path, str) and Path(path).is_absolute()
               for path in config["protected_paths"]), "protected paths")
    w0.require(re.fullmatch(r"GPU-[0-9a-fA-F-]{36}", config["gpu_uuid"]) and
               re.fullmatch(r"[0-9.]+", config["driver_version"]), "GPU/driver identity")
    for key in ("lease_end_unix", "lease_cutoff_unix", "deadline_unix"):
        w0.require(type(config[key]) in (int, float) and math.isfinite(config[key]) and config[key] > 0, key)
    w0.require(config["deadline_unix"] <= config["lease_cutoff_unix"] <= config["lease_end_unix"] - 21600, "lease six-hour buffer")


def verified_carrier(config):
    w0.require(w0.file_hash(config["carrier_proof_path"]) == config["carrier_proof_sha256"], "carrier proof hash")
    proof = read_json(config["carrier_proof_path"])
    w0.exact_keys(proof, proof_template())
    w0.require(proof["verified_by_main"] is True and proof["version"] == proof_template()["version"]
        and proof["carrier_source_ref"] == "241dd86e" and proof["verified_replay_sha256"] == CARRIER_REPLAY_SHA256
        and proof["capsule_sha256"] == CARRIER_CAPSULE_SHA256, "complete main-verified carrier required")
    w0.require(isinstance(proof["verification_reference"], str) and proof["verification_reference"]
        and "REPLACE" not in proof["verification_reference"], "carrier verification reference")
    w0.require(proof["model_sha256"] == config["model_sha256"] and proof["tokenizer_sha256"] == config["tokenizer_sha256"],
               "carrier/writer base identity mismatch")
    w0.require(Path(proof["output_path"]).is_absolute() and w0.file_hash(proof["output_path"]) == proof["output_sha256"],
               "carrier output hash")
    output = read_json(proof["output_path"])
    w0.require(output["label"] == "SEMANTIC_EXACT_ROW_SURFACE_OK" and output["valid"] == 64
        and output["truncated"] == output["multiple"] == 0 and output["optimizer_steps"] == 0
        and output["complementary_swaps"] == {"generate": 32, "score": 32}
        and output["native_copy_correct"] == {"0": 8, "1": 8}
        and set(output["cells"]) == {f"{root}/{mapping}" for root in range(2) for mapping in w0.MAPS}
        and all(cell[operation]["correct"] == 16 for cell in output["cells"].values() for operation in ("generate", "score")),
        "frozen complete carrier outcome")
    return dict(proof=proof, output=output, verification="main-verified original-source replay; not rerun here")


def sources():
    base = Path(__file__).resolve().parents[1]
    paths = (Path(__file__), base / "tests/test_semantic_writer_diagnostic.py", Path(w0.__file__),
             Path(carrier.__file__), Path(cal.__file__), Path(carrier.neutral.__file__), Path(carrier.TIMEOUT_BINARY))
    return {str(path.resolve()): w0.file_hash(path) for path in paths}


def pin_inputs(config):
    validate_config(config)
    evidence = verified_carrier(config)
    w0.require(w0.file_hash(config["protocol_path"]) == config["protocol_sha256"], "frozen protocol hash")
    environment = w0.environment_identity()
    w0.require(config["environment"] == environment, "environment pins")
    snapshots, cache = {}, {}
    for kind in ("model", "tokenizer"):
        path = str(Path(config[kind + "_path"]).resolve(strict=True))
        if path not in cache:
            cache[path] = w0.snapshot_inventory(path)
        snapshots[kind] = cache[path]
        w0.require(cache[path]["sha256"] == config[kind + "_sha256"], kind + " snapshot drift")
        w0.require(not any("adapter" in Path(name).name.lower() for name, _ in cache[path]["files"]), "clean-base snapshot only")
    model = read_json(Path(config["model_path"]) / "config.json")
    w0.require(model.get("model_type") == "qwen2" and model.get("num_hidden_layers") == 28
               and model.get("hidden_size") == 3584, "Qwen2.5-7B architecture")
    return dict(**snapshots, environment=environment, carrier_evidence_sha256=w0.digest(evidence),
                protocol_sha256=config["protocol_sha256"], carrier_proof_sha256=config["carrier_proof_sha256"])


def build_material():
    material = w0.build_material()
    material.update(version=VERSION, namespace=VERSION, boundary=BOUNDARY)
    for root_index, root in enumerate(material["roots"]):
        tools = ["sq0_" + w0.digest([VERSION, 100, root_index, slot])[:24] for slot in range(8)]
        neighbours = [tool[:-1] + ("0" if tool[-1] != "0" else "1") for tool in tools]
        replacements = dict(zip(root["tools"] + root["neighbours"], tools + neighbours))
        root["tools"], root["neighbours"] = tools, neighbours
        for row in itertools.chain(*root["train"].values(), root["held"], root["spill"]):
            if row.get("family") == "unrelated":
                action = carrier.COPY_ACTIONS[row["index"]]
                row.update(family="copy", expected=f"ACT: {action}",
                           context=f"Copy exactly one executable action line and no other text:\nACT: {action}\n")
            else:
                for old, new in replacements.items():
                    row["context"] = row["context"].replace(old, new)
                row["context"] = carrier.INSTRUCTION + "\n" + row["context"]
    return material


def validate_material(material):
    w0.require(material == build_material(), "frozen semantic material drift")
    old = w0.build_material()
    forbidden = {tool for root in old["roots"] + carrier.build_material()["roots"] for tool in root["tools"]}
    identifiers = [tool for root in material["roots"] for tool in root["tools"] + root["neighbours"]]
    w0.require(len(identifiers) == len(set(identifiers)) == 32 and not set(identifiers) & forbidden, "disjoint keys/neighbours")
    for root_index, root in enumerate(material["roots"]):
        for mapping in w0.MAPS:
            held = [dict(row, target=w0.action(root_index, row["slot"], row["mode"], mapping)) for row in root["held"]]
            w0.require(len(root["train"][mapping]) == 128 and len(held) == 64, "128/64 topology")
            for panel in (root["train"][mapping], held):
                for fields in ((), ("slot",), ("mode",), ("stratum",), ("stratum", "mode"), ("template",), ("template", "mode")):
                    correct, total = w0.best_shortcut(panel, fields)
                    w0.require(correct * 2 == total, "shortcut balance")


def render(tokenizer, text):
    rendered = tokenizer.tokenizer.apply_chat_template([{"role": "user", "content": text}],
                                                       tokenize=False, add_generation_prompt=True)
    prefix = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)["input_ids"]
    w0.require(prefix and all(type(token) is int and token >= 0 for token in prefix)
               and len(prefix) + 32 <= 2048 and tokenizer.decode(prefix) == rendered, "exact bounded chat prefix")
    return dict(prompt=text, rendered_prompt=rendered, prompt_input_ids=prefix, max_new_tokens=32, do_sample=False)


def build_panel(material, tokenizer):
    validate_material(material)
    requests, fits, cache = [], {}, {}

    def encoded(text):
        if text not in cache:
            payload = render(tokenizer, text)
            pairs = [carrier.encode_candidate(tokenizer, payload["rendered_prompt"], payload["prompt_input_ids"], target)
                     for target in carrier.CANDIDATES]
            cache[text] = payload, pairs
        return cache[text]

    def add(state, owner, probe, family, index, row):
        if family == "copy":
            payload, pairs = render(tokenizer, row["context"]), []
            carrier.encode_candidate(tokenizer, payload["rendered_prompt"], payload["prompt_input_ids"], row["expected"] + "\n")
        else:
            payload, pairs = encoded(row["context"])
        for operation in (("generate",) if family == "copy" else ("generate", "score")):
            request = dict(namespace=VERSION, state=state, operation=operation,
                audit=dict(owner_root=owner, probe_root=probe, family=family, index=index),
                payload=dict(payload, seed=row["seed"]), candidates=pairs if operation == "score" else [])
            requests.append(dict(request_id=w0.digest(request), **request))

    for root_index, root in enumerate(material["roots"]):
        states = ["OFF", *[state for state, (owner, _) in STATES.items() if owner == root_index]]
        for state in states:
            for index, row in enumerate(root["held"]):
                add(state, root_index, root_index, "primary", index, row)
            for row in root["spill"]:
                add(state, root_index, root_index, row["family"], row["index"], row)
        for state, (owner, mapping) in STATES.items():
            if owner != root_index:
                continue
            rows = []
            for index, row in enumerate(root["train"][mapping]):
                payload, pairs = encoded(row["context"])
                rows.append(dict(order=index, payload=payload, target=carrier.CANDIDATES[row["target"]], encoded=pairs[row["target"]]))
            fits[state] = dict(root=owner, mapping=mapping, seed=root_index, rows=rows, recipe=w0.EXECUTION_RECIPE)
            for index, row in enumerate(material["roots"][1 - owner]["held"]):
                add(state, owner, 1 - owner, "wrong_root", index, row)
    validate_counts(requests)
    return requests, fits


def coordinate(request):
    audit = request["audit"]
    return request["state"], audit["probe_root"], audit["family"], audit["index"], request["operation"]


def validate_counts(requests):
    w0.require(len(requests) == len({row["request_id"] for row in requests}) == len({coordinate(row) for row in requests}) == 1712,
               "1712 unique requests/coordinates")
    w0.require(Counter(row["operation"] for row in requests) == {"generate": 880, "score": 832}, "operation denominators")
    w0.require(Counter(row["state"] for row in requests) == {"OFF": 400, **{state: 328 for state in STATES}}, "state denominators")
    expected = Counter()
    for root in range(2):
        for state in ["OFF", *[name for name, (owner, _) in STATES.items() if owner == root]]:
            for family, count in {"primary": 64, "missing": 8, "unsupported": 8, "neighbour": 16, "copy": 8}.items():
                for operation in (("generate",) if family == "copy" else ("generate", "score")):
                    expected[state, root, family, operation] = count
    for state, (owner, _) in STATES.items():
        for operation in ("generate", "score"):
            expected[state, 1 - owner, "wrong_root", operation] = 64
    actual = Counter((row["state"], row["audit"]["probe_root"], row["audit"]["family"], row["operation"]) for row in requests)
    w0.require(actual == expected, "family crossing")
    for row in requests:
        body = {key: value for key, value in row.items() if key != "request_id"}
        w0.require(row["request_id"] == w0.digest(body) and row["namespace"] == VERSION, "request bytes/namespace")
        owner = row["audit"]["probe_root"] if row["state"] == "OFF" else STATES[row["state"]][0]
        w0.require(row["audit"]["owner_root"] == owner, "adapter owner/probe root")


def prepare(out, config):
    validate_config(config)
    w0.require(config["deadline_unix"] > time.time(), "prospective deadline")
    evidence = verified_carrier(config)
    protected = [config[key] for key in ("model_path", "tokenizer_path", "protocol_path", "carrier_proof_path")]
    root = cal._separate(out, [*protected, evidence["proof"]["output_path"], *config["protected_paths"]])
    w0.require(root.parent.is_dir() and not root.exists(), "fresh output directory required")
    source, pins = sources(), pin_inputs(config)
    tokenizer = w0.load_local_tokenizer(config)
    material = build_material()
    requests, fits = build_panel(material, tokenizer)
    w0.require(source == sources() and pins == pin_inputs(config), "prepare source/input drift")
    root.mkdir()
    for name, data in (("material.json", material), ("requests.json", requests), ("fits.json", fits), ("carrier_evidence.json", evidence)):
        w0.write_once(root, name, data)
    with (root / "protocol.txt").open("xb") as stream:
        stream.write(Path(config["protocol_path"]).read_bytes())
    manifest = dict(version=VERSION, boundary=BOUNDARY, counts=COUNTS, recipe=w0.EXECUTION_RECIPE,
        config=config, output_root=str(root), sources=source, input_pins=pins,
        artifacts={name: w0.file_hash(root / name) for name in
                   ("material.json", "requests.json", "fits.json", "carrier_evidence.json", "protocol.txt")})
    w0.write_once(root, "manifest.json", manifest)
    w0.write_once(root, "PREPARED.json", dict(manifest_sha256=w0.digest(manifest), model_loaded=False, gpu_accessed=False))
    return dict(status="CPU_PREPARED_MAIN_REVIEW_REQUIRED", counts=COUNTS, manifest_sha256=w0.digest(manifest), boundary=BOUNDARY)


def validate(root, tokenizer=None):
    root = w0.checked_path(root)
    manifest = w0.load_json(root / "manifest.json")
    validate_config(manifest["config"])
    w0.require(manifest["version"] == VERSION and manifest["boundary"] == BOUNDARY and manifest["counts"] == COUNTS
        and manifest["recipe"] == w0.EXECUTION_RECIPE and manifest["output_root"] == str(root)
        and manifest["sources"] == sources() and w0.load_json(root / "PREPARED.json")["manifest_sha256"] == w0.digest(manifest),
        "manifest/source binding")
    w0.require(set(manifest["artifacts"]) == {"material.json", "requests.json", "fits.json", "carrier_evidence.json", "protocol.txt"},
               "prepared artifact inventory")
    for name, digest in manifest["artifacts"].items():
        w0.require(w0.file_hash(root / name) == digest, "prepared artifact drift")
    w0.require(w0.load_json(root / "carrier_evidence.json") == verified_carrier(manifest["config"])
               and w0.file_hash(root / "protocol.txt") == manifest["config"]["protocol_sha256"], "eligibility/protocol binding")
    material = w0.load_json(root / "material.json")
    tokenizer = tokenizer or w0.load_local_tokenizer(manifest["config"])
    requests, fits = build_panel(material, tokenizer)
    w0.require(requests == w0.load_json(root / "requests.json") and fits == w0.load_json(root / "fits.json"), "tokenizer/panel/fit drift")
    return manifest, material, requests, fits, tokenizer


def generation(request, output, tokenizer):
    ids = output["generated_ids"]
    w0.require(isinstance(ids, list) and all(type(token) is int and token >= 0 for token in ids) and len(ids) <= 32, "raw token accounting")
    ended = bool(ids) and ids[-1] == tokenizer.eos_token_id
    body = ids[:-1] if ended else ids
    w0.require(tokenizer.eos_token_id not in body and output["eos_terminated"] is ended
        and output["truncated"] is (len(ids) == 32 and not ended) and output["text"] == tokenizer.decode(body)
        and output["decoded_with_terminal_eos"] == tokenizer.decode(ids)
        and output["request_id"] == request["request_id"], "raw generation/prefix binding")
    parsed = carrier.strict_output(output["text"], output["truncated"], ended,
                                  carrier.COPY_ACTIONS if request["audit"]["family"] == "copy" else carrier.ACTIONS)
    return dict(action=parsed["action"], multiple_ACT=parsed["multiple"], truncated=output["truncated"])


def score_sums(request, output):
    values = output["token_logprobs"]
    w0.require(isinstance(values, list) and len(values) == 2, "two complete candidates")
    totals = []
    for candidate, part in zip(request["candidates"], values):
        w0.require(isinstance(part, list) and len(part) == len(candidate["response_ids"])
            and all(type(value) in (int, float) and math.isfinite(value) and value <= 0 for value in part), "candidate token likelihood accounting")
        total = sum(part)
        w0.require(math.isfinite(total), "finite candidate sum")
        totals.append(total)
    return totals


def reduce_records(material, requests, records, tokenizer):
    validate_material(material)
    validate_counts(requests)
    by_id = {record["request_id"]: record for record in records}
    w0.require(len(records) == len(by_id) == 1712 and set(by_id) == {row["request_id"] for row in requests}, "complete raw records")
    indexed, details = {}, []
    for request in requests:
        record = by_id[request["request_id"]]
        w0.require(record["request_sha256"] == w0.digest(request) and record["attempts"] == 1, "record binding/no retry")
        output = record["output"]
        value = generation(request, output, tokenizer) if request["operation"] == "generate" else score_sums(request, output)
        indexed[coordinate(request)] = value
        details.append(dict(request_id=request["request_id"], coordinate=list(coordinate(request)), result=value))

    def parsed(state, probe, family, index):
        return indexed[state, probe, family, index, "generate"]

    def choice(state, probe, family, index):
        action = parsed(state, probe, family, index)["action"]
        return carrier.ACTIONS.index(action) if action in carrier.ACTIONS else None

    roots = []
    for root_index, root in enumerate(material["roots"]):
        gates = dict.fromkeys(("oracle_ok", "optimization_ok", "binding_ok", "interface_ok", "spill_ok"), True)
        cells, copies = {}, {}
        owner_states = [name for name, (owner, _) in STATES.items() if owner == root_index]
        for state in ["OFF", *owner_states]:
            copies[state] = sum(parsed(state, root_index, "copy", index)["action"] == action
                                for index, action in enumerate(carrier.COPY_ACTIONS))
            gates["interface_ok"] &= copies[state] == 8
        for state in owner_states:
            mapping = STATES[state][1]
            targets = [w0.action(root_index, row["slot"], row["mode"], mapping) for row in root["held"]]
            actions = [choice(state, root_index, "primary", index) for index in range(64)]
            off = [choice("OFF", root_index, "primary", index) for index in range(64)]
            gains, margins, raw_gains = defaultdict(list), defaultdict(list), []
            for index, (row, target) in enumerate(zip(root["held"], targets)):
                baseline = indexed["OFF", root_index, "primary", index, "score"]
                fitted = indexed[state, root_index, "primary", index, "score"]
                key = row["slot"], row["mode"]
                gains[key].append(w0.log_q(fitted, target) - w0.log_q(baseline, target))
                margins[key].append(fitted[target] - fitted[1 - target])
                raw_gains.append(fitted[target] - baseline[target])
            key_gains = {key: statistics.median(values) for key, values in gains.items()}
            key_margins = {key: statistics.median(values) for key, values in margins.items()}
            strata = []
            for stratum in range(2):
                indices = [index for index, row in enumerate(root["held"]) if row["stratum"] == stratum]
                strata.append(dict(accuracy=sum(actions[index] == targets[index] for index in indices) / 32,
                    validity=sum(actions[index] is not None for index in indices) / 32,
                    margin_keys=sum(value >= .5 for key, value in key_margins.items() if key[0] // 4 == stratum)))
            spill = {}
            for family, count in FAMILIES.items():
                probe, baseline_family = (1 - root_index, "primary") if family == "wrong_root" else (root_index, family)
                tvs, changes = [], []
                for index in range(count):
                    fitted = indexed[state, probe, family, index, "score"]
                    baseline = indexed["OFF", probe, baseline_family, index, "score"]
                    tvs.append(abs(math.exp(w0.log_q(fitted, 0)) - math.exp(w0.log_q(baseline, 0))))
                    changes.append(int(choice(state, probe, family, index) is not None)
                                   - int(choice("OFF", probe, baseline_family, index) is not None))
                spill[family] = dict(mean_binary_TV=statistics.mean(tvs), max_binary_TV=max(tvs), item_TV=tvs,
                    legal_ACT_rate_change=abs(statistics.mean(changes)), signed_legal_ACT_rate_change=statistics.mean(changes), n=count)
            ba = w0.balanced_accuracy(actions, targets)
            cell = dict(BA=ba, OFF_gain=ba - w0.balanced_accuracy(off, targets),
                opposite_BA=w0.balanced_accuracy(actions, [1 - target for target in targets]),
                key_NLL_gains=[key_gains[key] for key in sorted(key_gains)], key_margins=[key_margins[key] for key in sorted(key_margins)],
                mean_NLL_gain=statistics.mean(list(itertools.chain.from_iterable(gains.values()))),
                raw_target_sum_gains=raw_gains, raw_target_sum_mean_gain=statistics.mean(raw_gains),
                validity=sum(action is not None for action in actions) / 64,
                multiple_ACT_rate=sum(parsed(state, root_index, "primary", index)["multiple_ACT"] for index in range(64)) / 64,
                truncations=sum(parsed(state, root_index, "primary", index)["truncated"] for index in range(64)), strata=strata, spill=spill)
            cells[mapping] = cell
            for name, passed in cell_gates(cell).items():
                gates[name] &= passed
        gates["optimization_ok"] &= w0.asymmetry_ok(cells["W+"]["mean_NLL_gain"], cells["W-"]["mean_NLL_gain"])
        roots.append(dict(gates=gates, cells=cells, native_copy_correct=copies,
                          mean_gain_asymmetry=abs(cells["W+"]["mean_NLL_gain"] - cells["W-"]["mean_NLL_gain"])))
    combined = {key: all(root["gates"][key] for root in roots) for key in roots[0]["gates"]}
    return dict(label=w0.classify(combined), boundary=BOUNDARY, counts=COUNTS, gates=combined, roots=roots,
                oracle_ok_meaning="external main-verified carrier prerequisite, not a W0 oracle score", details=details)


def cell_gates(cell):
    w0.require(len(cell["key_NLL_gains"]) == len(cell["key_margins"]) == 16 and len(cell["strata"]) == 2
               and set(cell["spill"]) == set(FAMILIES), "nonvacuous all-cell metrics")
    return dict(optimization_ok=all(value >= .50 for value in cell["key_NLL_gains"]),
        binding_ok=cell["BA"] >= .80 and cell["OFF_gain"] >= .20 and cell["BA"] - cell["opposite_BA"] >= .50
            and sum(value >= .50 for value in cell["key_margins"]) >= 12
            and all(row["accuracy"] >= .75 and row["margin_keys"] >= 6 for row in cell["strata"]),
        interface_ok=cell["validity"] >= .95 and cell["multiple_ACT_rate"] == 0
            and all(row["validity"] >= .875 for row in cell["strata"]),
        spill_ok=all(row["mean_binary_TV"] <= .05 and row["legal_ACT_rate_change"] <= .05 for row in cell["spill"].values()))


def stage_plan():
    return [("off_generate", "OFF", "generate"), ("off_score", "OFF", "score"),
            *[("fit_" + state, state, "fit") for state in STATES],
            *[("eval_" + state + "_" + operation, state, operation) for state in STATES for operation in ("generate", "score")]]


def worker_command(root, stage):
    return [sys.executable, "-B", "-m", "organism_v6.semantic_writer_diagnostic", "_worker",
            "--run", str(root), "--stage", stage, "--allow-gpu"]


def validate_parent(root, stage, job, manifest):
    directory = root / "stages" / stage
    started = w0.load_json(directory / "STARTED.json")
    execution = w0.load_json(root / "STARTED.json")
    w0.require(started["job_sha256"] == w0.digest(job) and job["manifest_sha256"] == w0.digest(manifest)
        and execution["manifest_sha256"] == w0.digest(manifest) and started["controller_pid"] == execution["controller_pid"]
        and started["controller_start_ticks"] == execution["controller_start_ticks"]
        and started["wall_start"] <= time.time() < job["deadline_unix"] == started["deadline_unix"] <= execution["deadline_unix"]
        and job["deadline_unix"] <= started["wall_start"] + carrier.MAX_SECONDS, "stage startup/deadline binding")
    wait_until = time.monotonic() + 2
    while not (directory / "SUPERVISOR.json").exists() and time.monotonic() < wait_until:
        time.sleep(.01)
    supervisor = w0.load_json(directory / "SUPERVISOR.json")
    parent = carrier.process_identity(os.getppid())
    controller = carrier.process_identity(started["controller_pid"])
    command = [carrier.TIMEOUT_BINARY, "--signal=KILL", f"{supervisor['timeout_seconds']:.3f}s", *worker_command(root, stage)]
    actual = (Path("/proc") / str(parent["pid"]) / "cmdline").read_bytes().split(b"\0")[:-1]
    w0.require(parent == supervisor["identity"] and parent["ppid"] == started["controller_pid"]
        and parent["pgid"] == parent["session"] == parent["pid"] == os.getpgrp() == os.getsid(0)
        and controller["start_ticks"] == started["controller_start_ticks"] and supervisor["command"] == command
        and actual == [part.encode() for part in command] and supervisor["deadline_unix"] == job["deadline_unix"]
        and started["wall_start"] <= supervisor["launch_wall"]
        and 0 < supervisor["timeout_seconds"] <= job["deadline_unix"] - supervisor["launch_wall"] - carrier.CLEANUP_RESERVE_SECONDS,
        "new-module timeout/controller binding")


def fit_model(torch, config):
    from peft import LoraConfig, get_peft_model
    base = w0.load_hf_model(config, torch)
    w0.require(not w0.lora_tensors(base), "fit must start without an adapter")
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
        target_modules=list(w0.RECIPE["target_modules"]), task_type="CAUSAL_LM", init_lora_weights=True))
    trainables = w0.validate_trainables(model)
    initial = w0.lora_tensors(model)
    w0.require(all(torch.count_nonzero(value).item() == 0 for name, value in initial.items() if ".lora_B." in name), "standard zero-B init")
    optimizer = torch.optim.AdamW([parameter for _, parameter in trainables], lr=3e-5,
        betas=(.9, .999), eps=1e-8, weight_decay=.01, foreach=False, fused=False)
    model.train()
    return model, optimizer, initial


def train_rows(torch, model, optimizer, rows, directory, deadline):
    w0.require(len(rows) == 128 and [row["order"] for row in rows] == list(range(128)), "fixed fit row order")
    losses = []
    begin = time.monotonic()
    with (directory / "steps.jsonl").open("xb") as stream:
        for epoch in range(2):
            for index, row in enumerate(rows):
                w0.require(time.time() < deadline - 5, "fit deadline")
                loss = w0.finite_train_step(torch, model, optimizer, row["encoded"])
                w0.require(math.isfinite(loss), "finite training loss")
                losses.append(loss)
                stream.write(w0.canonical(dict(step=len(losses), epoch=epoch, row=index, loss=loss, seconds=time.monotonic() - begin)))
                stream.flush()
    w0.require(len(losses) == 256, "exact 256 steps")
    return dict(optimizer_steps=256, mean_loss=statistics.mean(losses), steps_sha256=w0.file_hash(directory / "steps.jsonl"),
                target_tokens=2 * sum(len(row["encoded"]["response_ids"]) for row in rows))


def load_eval_model(config, torch, root, state, adapter_hash, expected_lora):
    model = w0.load_hf_model(config, torch)
    w0.require(not w0.lora_tensors(model), "fresh OFF base before evaluation")
    if state != "OFF":
        from peft import PeftModel
        path = root / "stages" / ("fit_" + state) / "adapter"
        w0.require(w0.tree_hash(path) == adapter_hash, "adapter artifact identity")
        model = PeftModel.from_pretrained(model, str(path), is_trainable=False)
        w0.require(w0.tensor_digest(w0.lora_tensors(model)) == expected_lora, "fresh adapter reload identity")
    model.requires_grad_(False)
    model.eval()
    w0.require(not model.training and not any(parameter.requires_grad for parameter in model.parameters()), "evaluation without gradients")
    return model


def worker(root, stage, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required")
    root = w0.checked_path(root)
    manifest, _, requests, fits, tokenizer = validate(root)
    w0.require(stage in {name for name, _, _ in stage_plan()}, "declared stage")
    directory = root / "stages" / stage
    job = w0.load_json(directory / "JOB.json")
    expected = next((state, operation) for name, state, operation in stage_plan() if name == stage)
    w0.require((job["state"], job["operation"]) == expected, "fixed stage state/operation")
    validate_parent(root, stage, job, manifest)
    identity = carrier.process_identity(os.getpid())
    w0.write_once(directory, "CLAIMED.json", dict(identity=identity, job_sha256=w0.digest(job), parent_timeout_pid=os.getppid()))
    w0.require(pin_inputs(manifest["config"]) == manifest["input_pins"], "worker input drift")
    hardware = w0.gpu_identity(manifest["config"])
    state, operation = expected
    seed = fits[state]["seed"] if operation == "fit" else 0
    torch = w0.configure_torch(manifest["config"], seed)
    w0.require(time.time() < job["deadline_unix"] - 5, "model load deadline")
    common = dict(identity=identity, parent_timeout_pid=os.getppid(), job_sha256=w0.digest(job), manifest_sha256=w0.digest(manifest),
        sources_sha256=w0.digest(manifest["sources"]), model_sha256=manifest["config"]["model_sha256"],
        tokenizer_sha256=manifest["config"]["tokenizer_sha256"], environment_sha256=w0.digest(manifest["config"]["environment"]),
        state=state, operation=operation, seed=seed, hardware=hardware)
    if operation == "fit":
        w0.require(job["fit_sha256"] == w0.digest(fits[state]) and job["adapter_sha256"] == "OFF", "clean fit input binding")
        model, optimizer, initial = fit_model(torch, manifest["config"])
        load = dict(common, training=True, adapter_sha256="OFF_CLEAN_BASE", initial_lora_sha256=w0.tensor_digest(initial))
        w0.write_once(directory, "LOAD.json", load)
        result = train_rows(torch, model, optimizer, fits[state]["rows"], directory, job["deadline_unix"])
        final = w0.lora_tensors(model)
        update = math.sqrt(sum(float((final[name] - initial[name]).square().sum()) for name in initial))
        w0.require(math.isfinite(update) and update > 0, "finite nonzero adapter update")
        path = directory / "adapter"
        path.mkdir()
        model.save_pretrained(str(path), safe_serialization=True)
        w0.require((path / "adapter_model.safetensors").is_file() and (path / "adapter_config.json").is_file(), "complete adapter")
        result.update(adapter_sha256=w0.tree_hash(path), final_lora_sha256=w0.tensor_digest(final), update_norm=update,
                      fit_sha256=w0.digest(fits[state]), recipe=w0.EXECUTION_RECIPE)
    else:
        selected = [row for row in requests if row["state"] == state and row["operation"] == operation]
        w0.require(job["request_ids"] == [row["request_id"] for row in selected], "frozen stage request subset")
        if state == "OFF":
            w0.require(job["adapter_sha256"] == "OFF" and job["expected_lora_sha256"] is None, "OFF without adapter")
        else:
            fit = w0.load_json(root / "stages" / ("fit_" + state) / "DONE.json")
            w0.require(job["adapter_sha256"] == fit["result"]["adapter_sha256"]
                       and job["expected_lora_sha256"] == fit["result"]["final_lora_sha256"], "logical-slot adapter binding")
        model = load_eval_model(manifest["config"], torch, root, state, job["adapter_sha256"], job["expected_lora_sha256"])
        load = dict(common, training=False, adapter_sha256=job["adapter_sha256"], expected_lora_sha256=job["expected_lora_sha256"])
        w0.write_once(directory, "LOAD.json", load)
        raw = directory / "raw"
        raw.mkdir()
        for request in selected:
            w0.require(time.time() < job["deadline_unix"] - 5, "evaluation deadline")
            torch.manual_seed(request["payload"]["seed"])
            torch.cuda.manual_seed_all(request["payload"]["seed"])
            w0.random.seed(request["payload"]["seed"])
            begin = time.monotonic()
            output = (cal._generate(torch, model, tokenizer, dict(request["payload"], request_id=request["request_id"]))
                      if operation == "generate" else carrier.score(torch, model, request))
            torch.cuda.synchronize()
            record = dict(request_id=request["request_id"], request_sha256=w0.digest(request), adapter_sha256=job["adapter_sha256"],
                load_id=w0.digest(load), attempts=1, seconds=time.monotonic() - begin, output=output)
            w0.write_once(raw, request["request_id"] + ".json", record)
            generation(request, output, tokenizer) if operation == "generate" else score_sums(request, output)
        result = dict(request_count=len(selected), raw_sha256=w0.tree_hash(raw))
    w0.require(sources() == manifest["sources"] and time.time() < job["deadline_unix"], "stage completion source/deadline")
    w0.write_once(directory, "DONE.json", dict(**common, load_id=w0.digest(load), result=result))


def run_stage(root, manifest, requests, fits, stage, state, operation, deadline, adapters):
    directory = root / "stages" / stage
    directory.mkdir()
    wall = time.time()
    stage_deadline = min(deadline, wall + carrier.MAX_SECONDS)
    adapter = adapters.get(state)
    job = dict(version=VERSION, state=state, operation=operation, manifest_sha256=w0.digest(manifest), deadline_unix=stage_deadline,
        adapter_sha256="OFF" if operation == "fit" or state == "OFF" else adapter["adapter_sha256"],
        expected_lora_sha256=None if operation == "fit" or state == "OFF" else adapter["final_lora_sha256"],
        fit_sha256=w0.digest(fits[state]) if operation == "fit" else None,
        request_ids=[] if operation == "fit" else [row["request_id"] for row in requests if row["state"] == state and row["operation"] == operation])
    w0.write_once(directory, "JOB.json", job)
    w0.write_once(directory, "STARTED.json", dict(wall_start=wall, deadline_unix=stage_deadline, job_sha256=w0.digest(job),
        controller_pid=os.getpid(), controller_start_ticks=carrier.process_identity(os.getpid())["start_ticks"]))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=manifest["config"]["gpu_uuid"],
        CUBLAS_WORKSPACE_CONFIG=":4096:8", PYTHONHASHSEED="0", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    begin = time.monotonic()
    status = carrier.run_bounded_worker(worker_command(root, stage), directory, environment, stage_deadline)
    w0.write_once(directory, "COST.json", dict(returncode=status, seconds=time.monotonic() - begin, wall_finish=time.time()))
    w0.require(status == 0, "worker failed; no retry")
    return w0.load_json(directory / "DONE.json")


def off_copy_gate(root, requests, tokenizer):
    selected = [row for row in requests if row["state"] == "OFF" and row["operation"] == "generate" and row["audit"]["family"] == "copy"]
    w0.require(len(selected) == 16, "sixteen OFF copies")
    for request in selected:
        record = w0.load_json(root / "stages/off_generate/raw" / (request["request_id"] + ".json"))
        parsed = generation(request, record["output"], tokenizer)
        w0.require(parsed["action"] == carrier.COPY_ACTIONS[request["audit"]["index"]], "OFF copy failed; zero fits")


def replay(root):
    root = w0.checked_path(root)
    manifest, material, requests, fits, tokenizer = validate(root)
    seal = w0.load_json(root / "SEAL.json")
    inventory = cal._inventory(root)
    del inventory["SEAL.json"]
    w0.require(inventory == seal["files"] and seal["manifest_sha256"] == w0.digest(manifest), "sealed inventory drift")
    records, adapters, identities = [], {}, set()
    costs = 0
    started = w0.load_json(root / "STARTED.json")
    resource = w0.load_json(root / "RESOURCE.json")
    w0.require(started["manifest_sha256"] == w0.digest(manifest) and 0 <= resource["seconds"] <= MAX_SECONDS
        and resource["GPU_count"] == 1 and started["wall_start"] <= resource["wall_finish"] <= started["deadline_unix"]
        <= min(started["wall_start"] + MAX_SECONDS, manifest["config"]["deadline_unix"]), "controller resource binding")
    previous_finish = started["wall_start"]
    for stage, state, operation in stage_plan():
        directory = root / "stages" / stage
        job, load, done, cost, cleanup, supervisor, stage_start, claimed = [w0.load_json(directory / name) for name in
            ("JOB.json", "LOAD.json", "DONE.json", "COST.json", "CLEANUP.json", "SUPERVISOR.json", "STARTED.json", "CLAIMED.json")]
        w0.require(job["manifest_sha256"] == w0.digest(manifest) and (job["state"], job["operation"]) == (state, operation)
            and done["job_sha256"] == load["job_sha256"] == stage_start["job_sha256"] == claimed["job_sha256"] == w0.digest(job)
            and done["load_id"] == w0.digest(load) and done["identity"] == load["identity"] == claimed["identity"], "stage/load binding")
        w0.require(load["manifest_sha256"] == w0.digest(manifest) and load["sources_sha256"] == w0.digest(manifest["sources"])
            and load["model_sha256"] == manifest["config"]["model_sha256"] and load["tokenizer_sha256"] == manifest["config"]["tokenizer_sha256"]
            and load["environment_sha256"] == w0.digest(manifest["config"]["environment"]), "model/tokenizer/load identity")
        parent = supervisor["identity"]
        command = [carrier.TIMEOUT_BINARY, "--signal=KILL", f"{supervisor['timeout_seconds']:.3f}s", *worker_command(root, stage)]
        w0.require(stage_start["controller_pid"] == started["controller_pid"] == parent["ppid"]
            and stage_start["controller_start_ticks"] == started["controller_start_ticks"]
            and parent["pid"] == parent["pgid"] == parent["session"] == load["identity"]["ppid"]
            == load["identity"]["pgid"] == load["identity"]["session"]
            and supervisor["command"] == command and parent["start_ticks"] > 0
            and previous_finish <= stage_start["wall_start"] <= supervisor["launch_wall"] <= cost["wall_finish"] <= resource["wall_finish"]
            and supervisor["deadline_unix"] == stage_start["deadline_unix"] == job["deadline_unix"]
            <= stage_start["wall_start"] + carrier.MAX_SECONDS
            and 0 < supervisor["timeout_seconds"] <= job["deadline_unix"] - supervisor["launch_wall"] - carrier.CLEANUP_RESERVE_SECONDS,
            "replay timeout/controller binding")
        w0.require(cleanup["owned_group_empty"] is True and cleanup["error"] is None and cleanup["cancellation_signal"] is None
            and cleanup["pid"] == supervisor["identity"]["pid"] == load["parent_timeout_pid"] == claimed["parent_timeout_pid"]
            and cost["returncode"] == 0 and 0 <= cost["seconds"] <= carrier.MAX_SECONDS
            and stage_start["wall_start"] <= cost["wall_finish"] <= job["deadline_unix"] <= started["deadline_unix"], "stage cleanup/cost binding")
        previous_finish = cost["wall_finish"]
        identities.add((load["identity"]["pid"], load["identity"]["start_ticks"]))
        costs += cost["seconds"]
        if operation == "fit":
            result = done["result"]
            steps = [json.loads(line) for line in (directory / "steps.jsonl").read_text().splitlines()]
            w0.require(load["training"] is True and load["adapter_sha256"] == "OFF_CLEAN_BASE" and load["seed"] == fits[state]["seed"]
                and job["fit_sha256"] == result["fit_sha256"] == w0.digest(fits[state]) and result["recipe"] == w0.EXECUTION_RECIPE
                and result["optimizer_steps"] == len(steps) == 256 and math.isfinite(result["update_norm"]) and result["update_norm"] > 0
                and result["steps_sha256"] == w0.file_hash(directory / "steps.jsonl")
                and all(row["step"] == index + 1 and row["epoch"] == index // 128 and row["row"] == index % 128
                        and math.isfinite(row["loss"]) for index, row in enumerate(steps)), "exact frozen fit")
            w0.require(w0.tree_hash(directory / "adapter") == result["adapter_sha256"], "adapter hash drift")
            adapters[state] = result
        else:
            adapter = "OFF" if state == "OFF" else adapters[state]["adapter_sha256"]
            w0.require(load["training"] is False and job["adapter_sha256"] == load["adapter_sha256"] == adapter, "evaluation adapter binding")
            if state != "OFF":
                w0.require(load["expected_lora_sha256"] == job["expected_lora_sha256"] == adapters[state]["final_lora_sha256"], "fresh reload LoRA identity")
            selected = [row for row in requests if row["state"] == state and row["operation"] == operation]
            w0.require(job["request_ids"] == [row["request_id"] for row in selected] and done["result"]["request_count"] == len(selected)
                       and w0.tree_hash(directory / "raw") == done["result"]["raw_sha256"], "exact evaluation subset")
            w0.require(len(list((directory / "raw").iterdir())) == len(selected), "no extra raw records")
            for request in selected:
                record = w0.load_json(directory / "raw" / (request["request_id"] + ".json"))
                w0.require(record["load_id"] == done["load_id"] and record["adapter_sha256"] == adapter
                           and type(record["seconds"]) in (int, float) and math.isfinite(record["seconds"]) and record["seconds"] >= 0,
                           "raw load/cost binding")
                records.append(record)
    w0.require(len(identities) == 14 and len({value["adapter_sha256"] for value in adapters.values()}) == 4
               and costs <= resource["seconds"], "four fresh adapters/fourteen fresh workers/budget")
    off_copy_gate(root, requests, tokenizer)
    report = reduce_records(material, requests, records, tokenizer)
    w0.require(report == w0.load_json(root / "report.json"), "exact report replay")
    return report


def execute(root, allow_gpu=False):
    w0.require(allow_gpu is True, "explicit --allow-gpu required; main reviews before launch")
    begin, wall = time.monotonic(), time.time()
    root = w0.checked_path(root)
    manifest, material, requests, fits, tokenizer = validate(root)
    w0.require(set(cal._inventory(root)) == {"manifest.json", "PREPARED.json", *manifest["artifacts"]}, "fresh prepared run; no retry")
    w0.require(os.environ.get("CUDA_VISIBLE_DEVICES") == manifest["config"]["gpu_uuid"], "controller must retain pinned GPU reservation environment")
    w0.assert_output_fds_outside_run(root)
    w0.require(pin_inputs(manifest["config"]) == manifest["input_pins"], "execution input drift")
    deadline = min(wall + MAX_SECONDS, manifest["config"]["deadline_unix"])
    w0.require(deadline > time.time() + 10, "fresh execution deadline")
    hardware = w0.gpu_identity(manifest["config"])
    w0.assert_gpu_idle(manifest["config"])
    w0.write_once(root, "STARTED.json", dict(manifest_sha256=w0.digest(manifest), wall_start=wall, deadline_unix=deadline,
        controller_pid=os.getpid(), controller_start_ticks=carrier.process_identity(os.getpid())["start_ticks"]))
    (root / "stages").mkdir()
    completed, adapters = [], {}
    try:
        for stage, state, operation in stage_plan():
            if stage == "fit_r0_plus":
                off_copy_gate(root, requests, tokenizer)
            w0.require(time.time() < deadline - 10, "controller deadline")
            done = run_stage(root, manifest, requests, fits, stage, state, operation, deadline, adapters)
            completed.append(stage)
            if operation == "fit":
                adapters[state] = done["result"]
        records = [w0.load_json(root / "stages" / stage / "raw" / (row["request_id"] + ".json"))
                   for stage, state, operation in stage_plan() if operation != "fit"
                   for row in requests if row["state"] == state and row["operation"] == operation]
        report = reduce_records(material, requests, records, tokenizer)
        w0.require(pin_inputs(manifest["config"]) == manifest["input_pins"] and sources() == manifest["sources"], "completion input/source drift")
        seconds = time.monotonic() - begin
        w0.require(seconds <= MAX_SECONDS and time.time() <= deadline, "three-hour/lease bound")
        w0.write_once(root, "report.json", report)
        w0.write_once(root, "RESOURCE.json", dict(GPU_count=1, seconds=seconds, wall_finish=time.time(), hardware=hardware,
            controller_reservation=manifest["config"]["gpu_uuid"], release_audit="MAIN_OWNS_FINAL_RELEASE", stages=completed))
        w0.write_once(root, "SEAL.json", dict(manifest_sha256=w0.digest(manifest), files=cal._inventory(root)))
        replayed = replay(root)
        w0.require(time.monotonic() - begin <= MAX_SECONDS and time.time() <= deadline, "post-replay controller deadline")
        return replayed
    except BaseException as error:
        w0.write_once(root, "FAILED.json", dict(error_type=type(error).__name__, error=str(error), completed_stages=completed,
            no_retry=True, boundary=BOUNDARY, release_audit="MAIN_OWNS_FINAL_RELEASE"))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("config-template")
    commands.add_parser("carrier-proof-template")
    prep = commands.add_parser("prepare")
    prep.add_argument("--config", required=True)
    prep.add_argument("--out", required=True)
    for name in ("preflight", "execute", "_worker", "replay"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name in ("execute", "_worker"):
            command.add_argument("--allow-gpu", action="store_true")
        if name == "_worker":
            command.add_argument("--stage", required=True)
    args = parser.parse_args(argv)
    if args.command == "config-template":
        result = config_template()
    elif args.command == "carrier-proof-template":
        result = proof_template()
    elif args.command == "prepare":
        result = prepare(args.out, read_json(args.config))
    elif args.command == "preflight":
        manifest, _, _, _, _ = validate(args.run)
        w0.require(pin_inputs(manifest["config"]) == manifest["input_pins"], "native CPU input preflight")
        result = dict(status="CPU_PREFLIGHT_OK_MAIN_LAUNCH_DECISION_PENDING", counts=COUNTS, boundary=BOUNDARY)
    elif args.command == "_worker":
        result = worker(args.run, args.stage, args.allow_gpu)
    else:
        result = execute(args.run, args.allow_gpu) if args.command == "execute" else replay(args.run)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
