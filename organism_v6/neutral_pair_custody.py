"""Read-only custody checks for the existing evaluation-only neutral probe.

Snapshots bind configured local source bytes, not loaded GPU state or ancestry.
Callers retain the original snapshot and receipts and publish DONE only after
validate_pair succeeds. These checks do not make a writable filesystem immutable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


_ROOT = Path(__file__).resolve().parent.parent
_MODULES = (
    "__init__", "neutral_pair_custody", "run_reasoning_neutral",
    "reasoning_neutral_probe", "model_backend", "reasoning_gym_gym",
    "gym_backend", "batch_loop", "state", "ledger", "preschool",
    "preschool_reasoning",
)
_PROBE_MODULES = (
    "reasoning_neutral_probe", "reasoning_gym_gym", "gym_backend",
    "batch_loop", "state", "ledger", "preschool", "preschool_reasoning",
)
_BOOTSTRAP = "organism_v6/bootstrap_reasoning_gym.txt"
_REQUIRED = {"configuration.json", "results.json", "source_check.json", "generations.jsonl"}
_CONFIG_FIELDS = {
    "evidence_label", "episode_ids", "gen_seed", "seed_salt", "budget_ticks",
    "wake_max_tokens", "scratchpad_max_tokens", "total_token_budget", "max_episodes",
    "birth_prompt", "source_identity", "sources", "hashes_before", "code_hashes_before",
    "gym_configuration", "reasoning_gym_version", "protected_roots", "probe_root",
    "origin_verification",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _json(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def _read(path):
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object,
                       parse_constant=_invalid_constant)
    _require(isinstance(value, dict), "JSON object required")
    _json(value)
    return value


def _directory(path):
    path = Path(path).absolute()
    _require(not any(item.is_symlink() for item in (path, *path.parents)), "symlink directory")
    _require(path.is_dir(), "missing evidence directory")
    return path.resolve(strict=True)


def _file(root, name):
    _require(isinstance(name, str) and bool(name) and name not in (".", "..")
             and "/" not in name and "\\" not in name and "\x00" not in name,
             "unsafe artifact path")
    path = root / name
    _require(not path.is_symlink() and path.is_file(), "missing or unsafe artifact: " + name)
    _require(path.resolve(strict=True).parent == root, "artifact escapes directory")
    return path


def source_snapshot():
    """Return a JSON-safe snapshot of this runner's local execution closure."""
    from .reasoning_gym_gym import BOOTSTRAP_PATH

    _require(Path(BOOTSTRAP_PATH).absolute() == _ROOT / _BOOTSTRAP,
             "bootstrap outside trusted source root")
    names = ["organism_v6/" + module + ".py" for module in _MODULES] + [_BOOTSTRAP]
    files = {}
    for name in names:
        path = _ROOT / name
        _directory(path.parent)
        files[name] = _digest(_file(path.parent, path.name))
    return dict(schema="neutral-pair-source-v1", source_root=str(_ROOT),
                bootstrap_path=_BOOTSTRAP, sha256=files)


def verify_source_snapshot(snapshot):
    """Reject missing, redirected, or changed source snapshot entries."""
    _require(isinstance(snapshot, dict) and _json(snapshot) == _json(source_snapshot()),
             "source snapshot mismatch")


def _configuration(directory, condition):
    from .preschool_reasoning import _identity_status

    config = _read(_file(directory, "configuration.json"))
    _require(_CONFIG_FIELDS <= config.keys(), "missing configuration fields")
    _require(config["evidence_label"] == "EVALUATION_ONLY", "wrong configuration label")
    identity = config["source_identity"]
    _require(_identity_status(identity) == "RECORDED_BACKEND", "invalid configured backend identity")
    expected_sources = {"model", "adapter"} if condition == "on" else {"model"}
    for field in ("sources", "hashes_before"):
        _require(isinstance(config[field], dict) and set(config[field]) == expected_sources,
                 "wrong condition sources")
    _require((identity["adapter_input"] is not None) == (condition == "on"), "wrong adapter condition")
    for name in expected_sources:
        source = config["sources"][name]
        _require(isinstance(source, str) and Path(source).is_absolute(), "invalid source path")
        _require(Path(identity[name + "_input"]).resolve() == Path(source).resolve(),
                 "configured source identity mismatch")
        inventory = config["hashes_before"][name]
        _require(isinstance(inventory, dict) and bool(inventory)
                 and all(isinstance(key, str) and _sha(value) for key, value in inventory.items()),
                 "invalid source inventory")
    if condition == "on":
        _require(all(config["hashes_before"]["adapter"].get(name) == digest
                     for name, digest in identity["adapter_files"].items()), "adapter hashes mismatch")
    check = _read(_file(directory, "source_check.json"))
    _require(check.get("evidence_label") == "EVALUATION_ONLY"
             and _json(check.get("hashes_after")) == _json(config["hashes_before"])
             and _json(check.get("code_hashes_after")) == _json(config["code_hashes_before"])
             and "error" not in check and "error_type" not in check
             and check.get("unchanged", True) is True, "failed source check")
    return config


def verify_condition(output_dir, condition, spec_sha256, expected_receipt=None):
    """Validate one worker receipt and its complete flat probe artifact set."""
    _require(condition in ("off", "on") and _sha(spec_sha256), "invalid condition/spec digest")
    root = _directory(output_dir)
    failure = root / "PAIR_FAILED.json"
    _require(not failure.exists() and not failure.is_symlink(), "pair has failure evidence")
    directory = _directory(root / condition)
    receipt = _read(_file(root, condition + "_WORKER_DONE.json"))
    _require(receipt.get("evidence_label") == "EVALUATION_ONLY"
             and receipt.get("condition") == condition and receipt.get("spec_sha256") == spec_sha256,
             "worker receipt mismatch")
    _require(type(receipt.get("pid")) is int and receipt["pid"] > 0, "invalid worker pid")
    if expected_receipt is not None:
        _require(_json(receipt) == _json(expected_receipt), "original receipt changed")
    for name in ("results", "manifest"):
        expected = receipt.get(name + "_sha256")
        _require(_sha(expected) and _digest(_file(directory, name + ".json")) == expected,
                 "worker evidence digest mismatch")
    manifest = _read(_file(directory, "manifest.json"))
    _require(set(manifest) == {"evidence_label", "sha256"}
             and manifest["evidence_label"] == "EVALUATION_ONLY", "invalid manifest")
    inventory = manifest["sha256"]
    _require(isinstance(inventory, dict) and _REQUIRED <= inventory.keys(), "missing required artifacts")
    _require("failure.json" not in inventory and not (directory / "failure.json").exists(),
             "condition has failure evidence")
    for name, expected in inventory.items():
        _require(_sha(expected) and _digest(_file(directory, name)) == expected, "artifact digest mismatch")
    _require({path.name for path in directory.iterdir()} == set(inventory) | {"manifest.json"},
             "unmanifested artifacts")
    config = _configuration(directory, condition)
    episodes = config["episode_ids"]
    _require(isinstance(episodes, list) and bool(episodes)
             and all(isinstance(episode, str) and episode for episode in episodes)
             and len(set(episodes)) == len(episodes), "invalid episode panel")
    results = _read(_file(directory, "results.json"))
    rows = results.get("episodes")
    _require(results.get("evidence_label") == "EVALUATION_ONLY"
             and isinstance(rows, list) and len(rows) == len(episodes), "invalid episode results")
    for index, (episode, row) in enumerate(zip(episodes, rows)):
        ledger = f"episode_{index:04d}.jsonl"
        _require(isinstance(row, dict) and row.get("episode_id") == episode
                 and row.get("ledger") == ledger and ledger in inventory, "missing/mismatched episode ledger")
    return receipt


def _shared(config):
    shared = json.loads(_json(config))
    shared["source_identity"].pop("adapter_input")
    shared["source_identity"].pop("adapter_files")
    shared["sources"].pop("adapter", None)
    shared["hashes_before"].pop("adapter", None)
    return shared


def validate_pair(output_dir, spec_sha256, receipts, snapshot):
    """Revalidate original receipts/sources; return condition -> receipt SHA256.

    The caller must provide the original two receipt dictionaries collected at
    worker completion, not reload replacements before calling this function.
    """
    _require(isinstance(receipts, dict) and set(receipts) == {"off", "on"}, "both original receipts required")
    verify_source_snapshot(snapshot)
    root = _directory(output_dir)
    configs, digests = {}, {}
    for condition in ("off", "on"):
        _require(isinstance(receipts[condition], dict), "missing original receipt")
        verify_condition(root, condition, spec_sha256, receipts[condition])
        configs[condition] = _configuration(root / condition, condition)
        digests[condition] = _digest(_file(root, condition + "_WORKER_DONE.json"))
    _require(receipts["off"]["pid"] != receipts["on"]["pid"], "worker pid reused")
    _require(_json(_shared(configs["off"])) == _json(_shared(configs["on"])),
             "shared configuration mismatch")
    for config in configs.values():
        _require(isinstance(config["birth_prompt"], str)
                 and hashlib.sha256(config["birth_prompt"].encode()).hexdigest()
                 == snapshot["sha256"][_BOOTSTRAP], "bootstrap snapshot mismatch")
        code = config["code_hashes_before"]
        required = {str(_ROOT / ("organism_v6/" + module + ".py")) for module in _PROBE_MODULES}
        _require(isinstance(code, dict) and required <= code.keys(), "missing probe code inventory")
        for name, expected in code.items():
            _require(isinstance(name, str) and Path(name).is_absolute() and _sha(expected), "invalid code entry")
            path = Path(name)
            _require(_ROOT in path.parents and path == path.resolve(strict=True),
                     "code outside trusted source root or noncanonical path")
            parent = _directory(path.parent)
            _require(_digest(_file(parent, path.name)) == expected, "probe code drift")
            relative = str(path.relative_to(_ROOT))
            if relative in snapshot["sha256"]:
                _require(snapshot["sha256"][relative] == expected, "probe code snapshot mismatch")
    verify_source_snapshot(snapshot)
    for condition in ("off", "on"):
        verify_condition(root, condition, spec_sha256, receipts[condition])
        _require(_digest(_file(root, condition + "_WORKER_DONE.json")) == digests[condition],
                 "receipt changed during validation")
    return digests
