"""Fixed additive-loss pairing over the frozen EXTRA_MEMORY schedule; CPU only."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


SELF = Path(__file__).resolve()
SCHEMA = "astra_additive_replay_material_20260913_v1"
ENCODING_SCHEMA = "astra_additive_replay_encoding_20260913_v1"
PROTOCOL_PATH = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md"
PROTOCOL_PIN = "724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9"
REPAIR_CORE_PATH = "/tmp/astra_own_replay_repair_core_20260913.py"
REPAIR_CORE_PIN = "9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93"
REPAIR_RUNNER_PIN = "f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe"
ARMS = ("ADDITIVE", "MEMORY_ONLY")
MEMORY_COUNTS = (14, 8, 8)
PASSES, REPLAY_COUNT = 8, 24
OBJECTIVES = {"ADDITIVE": "sum_of_separate_mean_token_ce", "MEMORY_ONLY": "memory_mean_token_ce"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repair_core():
    require(digest(REPAIR_CORE_PATH) == REPAIR_CORE_PIN, "frozen pairing source differs")
    spec = importlib.util.spec_from_file_location("additive_frozen_repair_core", REPAIR_CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pairs_for(mixture):
    count = len(mixture["memory_rows"])
    memory = mixture["arms"]["EXTRA_MEMORY"]["rows"][count:]
    replay = mixture["arms"]["REPLAY"]["rows"][count:]
    require(len(memory) == len(replay) == REPLAY_COUNT, "exact24 existing pairs required; no new selection")
    return [dict(memory_row_id=left["row_id"], replay_row_id=right["row_id"])
            for left, right in zip(memory, replay)]


def build(repair_plan, repair_bound, *, protocol_path=PROTOCOL_PATH):
    require(digest(protocol_path) == PROTOCOL_PIN, "additive protocol differs")
    old = repair_core()
    seed = repair_plan["specification"]["seed"]
    require(type(seed) is int and seed in (0, 1, 2) and repair_plan["self_sha256"] == REPAIR_RUNNER_PIN,
            "original completed repair source/seed required")
    mixture, training = repair_bound["mixture"], repair_bound["saved_training"]
    old.validate_material(mixture)
    require(mixture["seed"] == seed and mixture["status"] == "READY" and
            mixture["parent"] == repair_plan["parent"] == repair_bound["parent"] == repair_bound["memory_plan"]["parent"] and
            len(mixture["memory_rows"]) == MEMORY_COUNTS[seed] and len(mixture["replay_rows"]) == REPLAY_COUNT,
            "fixed admitted source bank/original recipient differs")
    require(value_hash(mixture) == repair_plan["input_hashes"]["mixture.json"], "historical source mixture differs")
    require(set(training) == {"EXTRA_MEMORY", "REPLAY"}, "both existing encodings required")
    for arm, prepared in training.items():
        require(repair_bound["saved_training_sha256"][arm] == repair_plan["input_hashes"][f"training_{arm}.json"], "bound original file-byte hash differs")
        require(value_hash(prepared) == repair_plan["input_hashes"][f"training_{arm}.json"], "historical encoding pin differs")
        require(prepared["arm"] == arm and prepared["seed"] == prepared["fit_seed"] == seed and
                prepared["material_sha256"] == mixture["material_sha256"], "historical encoding identity differs")
    material = dict(schema=SCHEMA, seed=seed, parent=copy.deepcopy(mixture["parent"]),
        protocol=dict(path=str(protocol_path), sha256=PROTOCOL_PIN), repair_plan_sha256=value_hash(repair_plan),
        repair_runner_sha256=REPAIR_RUNNER_PIN, repair_core_sha256=REPAIR_CORE_PIN,
        source_input_hashes=copy.deepcopy(repair_plan["input_hashes"]), mixture=copy.deepcopy(mixture),
        saved_training=copy.deepcopy(training), saved_training_sha256=copy.deepcopy(repair_bound["saved_training_sha256"]), pairs=pairs_for(mixture),
        counts=dict(memory=MEMORY_COUNTS[seed], replay=24, rows_per_arm=MEMORY_COUNTS[seed] + 24,
                    updates_per_arm=PASSES * (MEMORY_COUNTS[seed] + 24)),
        limitation="Matched memory occurrence dose/order, not tokens/FLOPs/RNG or trajectories; no new source capture or teacher target.")
    material["material_sha256"] = value_hash(material)
    validate_material(material)
    return material


def validate_material(material):
    require(material["schema"] == SCHEMA and value_hash({key: value for key, value in material.items() if key != "material_sha256"}) ==
            material["material_sha256"], "additive material hash differs")
    require(material["protocol"]["sha256"] == PROTOCOL_PIN and material["repair_runner_sha256"] == REPAIR_RUNNER_PIN and
            material["repair_core_sha256"] == REPAIR_CORE_PIN, "material source pins differ")
    old, mixture = repair_core(), material["mixture"]
    old.validate_material(mixture)
    seed = material["seed"]
    require(type(seed) is int and seed in (0, 1, 2) and seed == mixture["seed"] and material["parent"] == mixture["parent"], "seed/parent differs")
    require(len(mixture["memory_rows"]) == MEMORY_COUNTS[seed] and len(mixture["replay_rows"]) == 24 and
            material["pairs"] == pairs_for(mixture), "fixed source pair mapping differs")
    require(material["counts"] == dict(memory=MEMORY_COUNTS[seed], replay=24, rows_per_arm=MEMORY_COUNTS[seed] + 24,
            updates_per_arm=PASSES * (MEMORY_COUNTS[seed] + 24)), "fixed dose differs")
    require(value_hash(mixture) == material["source_input_hashes"]["mixture.json"], "source mixture pin differs")
    for arm in ("EXTRA_MEMORY", "REPLAY"):
        prepared = material["saved_training"][arm]
        rows = mixture["arms"][arm]["rows"]
        require(material["saved_training_sha256"][arm] == material["source_input_hashes"][f"training_{arm}.json"], "original byte binding differs")
        require(value_hash(prepared) == material["source_input_hashes"][f"training_{arm}.json"] and
                prepared["encoding_sha256"] == value_hash({key: value for key, value in prepared.items() if key != "encoding_sha256"}),
                "source encoding hash differs")
        require([item["group"] for item in prepared["items"]] == [row["row_id"] for row in rows] and
                [audit["row_id"] for audit in prepared["encoding"]] == [row["row_id"] for row in rows] and
                len(prepared["epoch_order"]) == PASSES and all(Counter(order) == Counter(row["row_id"] for row in rows)
                    for order in prepared["epoch_order"]), "existing occurrence/epoch schedule differs")


def prepared_from_saved(material, arm):
    validate_material(material)
    require(arm in ARMS, "unknown additive arm")
    primary = material["saved_training"]["EXTRA_MEMORY"]
    replay = material["saved_training"]["REPLAY"]
    count = material["counts"]["memory"]
    replay_audits = copy.deepcopy(replay["encoding"][count:])
    result = copy.deepcopy(primary)
    result.pop("encoding_sha256")
    result.update(schema=ENCODING_SCHEMA, arm=arm, material_sha256=material["material_sha256"],
                  replay_items=copy.deepcopy(replay["items"][count:]), replay_encoding=replay_audits,
                  pairs=copy.deepcopy(material["pairs"]), objective=OBJECTIVES[arm],
                  source_encoding_sha256=primary["encoding_sha256"], pair_sha256=value_hash(material["pairs"]))
    repetitions = PASSES if arm == "ADDITIVE" else 0
    replay_total = repetitions * sum(len(audit["input_ids"]) for audit in replay_audits)
    replay_target = repetitions * sum(len(audit["supervised_ids"]) for audit in replay_audits)
    result["token_accounting"] = dict(memory_presentations=primary["updates"], replay_presentations=repetitions * 24,
        memory_total_tokens=primary["train_tokens_seen"], memory_supervised_tokens=primary["actual_supervised_tokens"],
        memory_context_tokens=primary["actual_context_tokens"], replay_total_tokens=replay_total,
        replay_supervised_tokens=replay_target, replay_context_tokens=replay_total - replay_target,
        total_forward_sequences=primary["updates"] + repetitions * 24,
        total_forward_tokens=primary["train_tokens_seen"] + replay_total,
        total_supervised_tokens=primary["actual_supervised_tokens"] + replay_target,
        total_context_tokens=primary["actual_context_tokens"] + replay_total - replay_target)
    source_counts = Counter(row["source_row_id"] for row in material["mixture"]["arms"]["EXTRA_MEMORY"]["rows"])
    result["memory_source_presentations"] = {key: PASSES * value for key, value in sorted(source_counts.items())}
    result["encoding_sha256"] = value_hash(result)
    return result


def encode(material, arm, tokenizer, trainer, helper, probe, fit_seed):
    validate_material(material)
    require(type(fit_seed) is int and fit_seed == material["seed"], "unchanged original fit seed required")
    old = repair_core()
    for source_arm in ("EXTRA_MEMORY", "REPLAY"):
        actual = old.encode(material["mixture"], source_arm, tokenizer, trainer, helper, probe, fit_seed)
        require(encoded(actual) == encoded(material["saved_training"][source_arm]), "native original context/target/mask/order differs")
    return prepared_from_saved(material, arm)
