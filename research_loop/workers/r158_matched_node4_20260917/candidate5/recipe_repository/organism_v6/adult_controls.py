"""Bounded, parent-free adult running/shadow controls; no runner or GPU code.

prepare_adult requires an EXTERNALLY trusted clean manifest pin. It reuses
lineage_guard and life_lineage's preschool_records_v1 admission and
child_only_v1 trainer-evidence verifiers;
neither consistent hashes nor this helper establish truthful source history.
Only that existing INITIAL child-only corpus recipe is supported. Subsequent
adult corpus admission and loss-target checks remain main's responsibility;
a candidate key is byte binding, not training-execution or admission proof. The caller owns
trusted pin selection, actual model/trainer inputs, and honest gate execution.

Nonweight policy: start a fresh adult ledger. Inherit only the pinned initial
LoRA and the admitted child-only corpus as compiler prior. Childhood ledgers
and row snapshots are inspected as provenance evidence, NEVER returned as
context. No childhood notes, parent turns, briefs, retrieval or lesson state
are copied into the adult life. wake_context returns only the supplied gym
birth prompt, without opening parent/waking-brief files. Adults are exposed
to their task; this module never manufactures new UNEXPOSED ancestry claims.

Integration (main owns all runner edits):
  1. Before opening logs/models, prepare_adult(..., startup_config=vars(args),
     explicit_flags=sys.argv[1:]). Pass identical config and resume=True only
     on deliberate resume; omit transient resume transport flags from config.
  2. Replace adult latest_adapter calls with select_adapter(control), and
     adult brief/head construction with wake_context(control, gym.birth_prompt()).
     Load the pinned base at control.model_dir (including the trainer's
     V6_MODEL environment, set before backend import); do not silently load
     a different cached model under the same model name.
     Seed compile prior from list(initial_prior(control)) only when there is
     no earlier ADULT corpus (compare checkpoint numbers, not directory sort).
     Retain these initial items in every candidate corpus. Both modes use the
     same compiler/trainer; do not insert a fake sleep_0000. The current generic
     compile_sleep loses the child-only recipe, and gate_sleep(enforce) replaces
     its corpus: main must wire preservation and the intended loss-target path.
  3. Use the existing staging-to-CANDIDATE helper, not its gate-to-DONE path.
     Capture candidate_key BEFORE gate evaluation. A cached gate must carry
     this exact key; never attach a fresh key to an old cached score/decision.
  4. record_decision(..., evaluated_key=that_key, accepted=bool, reason=code)
     commits a separate immutable receipt. Only accepted running candidates
     get a copied promoted adapter with DONE. Never mutate the raw candidate
     into DONE. Use get_decision for completed sleeps; partial/stale output
     errors are preserved for inspection, not automatically repaired.
  5. Reload via select_adapter, not the raw candidate path. Shadow keeps the
     initial adapter for waking; a disposable gate-only candidate evaluation
     is allowed and must never replace the live waking adapter.

Runner-specific boundaries: get_decision(control, episode_checkpoint) replaces
raw adapter final-marker tests; decision.promoted_adapter replaces raw DONE
scans in committed_gate_probes. Snapshot the candidate key before both canary
and probe calls and check it BEFORE any cached-probe read. Measure adapter-OFF
on the pinned base under gate_base, not the seeded ep0000 model; bind an initial
adapter gate measurement separately. This module does not choose gate floors.
No parent setup or deliver_lesson call is allowed in the adult branch; if the
child note-after slot is used, add only its slot sentence equally in both modes.
The current trainer emits aggregate train_meta.json, not the required row-linked
trainer_receipt.json: neither this module nor a relabelled aggregate makes one.

All startup values and mode are frozen. Stateful accesses recheck cached initial
inputs/evidence and control bytes; prepare/resume also traverses ancestry via
lineage_guard. This includes hashing the pinned base runtime files, not just
LoRA files; context/property accessors do no I/O. No symlink inputs/outputs.
Copies are read-only, not WORM:
consume the checked bytes or revalidate at use. A caller must not bypass this
API with legacy marker scans, brief reads or promotion code in adult mode.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from . import life_lineage as lineage
from . import lineage_guard as guard


SCHEMA = "adult-parent-free-v1"
NONWEIGHT_POLICY = "fresh-adult-ledger; initial-child-corpus-only; no-inherited-notes-or-briefs"
_REASONS = {"OK", "SCORE", "BREVITY", "CANARY", "GATE"}
_DECISION_FIELDS = {"schema", "startup_sha256", "checkpoint", "candidate_key",
                    "inputs", "previous", "accepted", "reason", "promoted"}
_INACTIVE = {"parent_url": None, "parent_mode": "brief", "clone_group": None,
             "clone_id": 0, "clone_count": 1, "clone_coordinator": 0,
             "clone_barrier_timeout": 7200.0, "clone_round_timeout": 10800.0,
             "artifact_lesson": "none"}


class AdultControlError(ValueError):
    """Unsupported policy, mismatched evidence, or stale/partial adult state."""


@dataclass(frozen=True)
class AdultControl:
    life_dir: str
    mode: str
    initial_adapter: str
    initial_corpus: str
    startup_json: str
    startup_sha256: str
    inputs: tuple[guard.FileBinding, ...]

    @property
    def model_dir(self):
        return str(Path(json.loads(self.startup_json)["lineage_root"]) / "birth" / "model")


@dataclass(frozen=True)
class AdultDecision:
    checkpoint: int
    accepted: bool
    reason: str
    candidate_key: str
    promoted_adapter: str | None


def _require(condition, message):
    if not condition:
        raise AdultControlError(message)


def _api(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AdultControlError:
            raise
        except (guard.LineageGuardError, OSError, ValueError, TypeError,
                KeyError, AttributeError, RecursionError) as error:
            raise AdultControlError(str(error)) from error
    return checked


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode() + b"\n"


def _sha(content):
    return hashlib.sha256(content).hexdigest()


def _read_json(path):
    content = lineage._read(path)
    value = json.loads(content, object_pairs_hook=guard._json_object,
                       parse_constant=guard._invalid_constant)
    _require(isinstance(value, dict), "expected a JSON object")
    return value


@_api
def validate_options(startup_config, explicit_flags=()):
    """Accept parser's inert defaults, but reject explicit parent/lesson/clone flags."""
    _require(isinstance(startup_config, dict), "startup config must be a dict")
    _require(isinstance(explicit_flags, (list, tuple)), "explicit flags must be an argv sequence")
    _encode(startup_config)
    for flag in explicit_flags:
        _require(isinstance(flag, str), "invalid explicit flag")
        name = flag.split("=", 1)[0].replace("-", "_").lstrip("_")
        if flag.startswith("--"):
            _require(not (name.startswith(("parent", "clone", "lesson"))
                          or "lesson" in name
                          or any(known.startswith(name) for known in (*_INACTIVE, "parent_model"))),
                     "adult mode forbids parent/lesson/clone flags")
    for name, value in startup_config.items():
        _require(isinstance(name, str), "non-string config key")
        normalized = name.replace("-", "_")
        _require(not re.search(r"(^|_)(api_key|access_token|auth_token|secret|password|credential)(_|$)",
                               normalized), "credentials cannot enter frozen startup config")
        if normalized == "parent_model":
            _require(isinstance(value, str), "invalid inert parent model default")
        elif normalized in _INACTIVE:
            _require(type(value) is type(_INACTIVE[normalized])
                     and value == _INACTIVE[normalized], f"adult mode forbids {name}")
        elif normalized.startswith(("parent", "clone", "lesson")) or "lesson" in normalized:
            raise AdultControlError(f"unsupported adult option: {name}")
    _require(startup_config.get("arm", "B") == "B",
             "adult running/shadow both require training arm B")
    for name in ("seed", "train_seed", "rank"):
        if name in startup_config and not (name == "train_seed" and startup_config[name] is None):
            _require(type(startup_config[name]) is int, f"invalid {name} in startup config")
    _require(startup_config.get("rank", 1) > 0, "rank must be positive")


def _initial(lineage_root, manifest_path, expected_manifest_sha256,
             initial_adapter_dir, initial_corpus_path):
    root = lineage._absolute(lineage_root)
    guard._hash(expected_manifest_sha256)
    receipt = guard.validate_manifest(manifest_path, root=root,
                                      expected_sha256=expected_manifest_sha256)
    _require(re.fullmatch(r"sleep_\d{4,}/manifest\.json", str(manifest_path)),
             "initial manifest must be a recorded child sleep")
    manifest = _read_json(root / manifest_path)
    _require(manifest["kind"] == "descendant" and len(manifest["parents"]) == 1,
             "unsupported initial lineage shape")
    checkpoint = (root / manifest_path).parent
    corpus_path = lineage._absolute(initial_corpus_path)
    adapter_dir = lineage._absolute(initial_adapter_dir)
    corpus_binding = manifest["trained_corpus"]
    _require(len(corpus_binding) == 1
             and corpus_binding[0]["path"] == str((checkpoint / "corpus.json").relative_to(root)),
             "initial manifest must bind exactly its child corpus")
    bound = {item.path: item.sha256 for item in receipt.files}
    _require("birth/manifest.json" in {item.path for item in receipt.manifests}
             and {"birth/model/config.json", "birth/model/tokenizer.json",
                  "birth/model/tokenizer_config.json"} <= set(bound),
             "missing externally pinned birth inventory")
    actual = lineage._adapter_inputs(adapter_dir, root / "birth/model")
    declared = {item["path"]: item["sha256"] for item in manifest["artifacts"]
                if item["role"] == "lora_adapter"}
    expected = {str((checkpoint / "adapter" / name).relative_to(root)): digest
                for name, (_, digest) in actual.items()}
    _require(declared == expected, "actual adapter/config does not match pinned manifest")
    corpus = lineage._read(corpus_path)
    _require(_sha(corpus) == corpus_binding[0]["sha256"], "initial corpus pin mismatch")
    gate_path = checkpoint / "gate_receipt.json"
    trainer_path = checkpoint / "trainer_receipt.json"
    ledger_path = checkpoint / "ledger.jsonl"
    selected = {str((root / item.path)): item.sha256 for item in receipt.manifests}
    selected.update({str(root / item.path): item.sha256 for item in receipt.files})
    for item in manifest["sources"] + manifest["artifacts"] + manifest["trained_corpus"]:
        selected[str(root / item["path"])] = item["sha256"]
    metadata_path = checkpoint / "adapter/train_meta.json"
    _require({str(gate_path), str(ledger_path), str(trainer_path), str(metadata_path)} <= set(selected),
             "initial corpus lacks bound gate/source/trainer snapshots")
    for path, digest in selected.items():
        _require(lineage._hash_file(path) == digest, "initial evidence changed after validation")
    lineage._prior_training(root, receipt)
    actual_metadata = adapter_dir / "train_meta.json"
    _require(lineage._hash_file(actual_metadata) == selected[str(metadata_path)],
             "actual trainer metadata does not match pinned manifest")
    selected[str(actual_metadata)] = selected[str(metadata_path)]
    for path, digest in actual.values():
        selected[str(path)] = digest
    selected[str(corpus_path)] = _sha(corpus)
    return adapter_dir, corpus_path, tuple(guard.FileBinding(path, digest)
                                         for path, digest in sorted(selected.items()))


@_api
def prepare_adult(life_dir, *, mode, startup_config, lineage_root, manifest_path,
                  expected_manifest_sha256, initial_adapter_dir, initial_corpus_path,
                  explicit_flags=(), resume=False):
    """Freeze a fresh adult startup, or precisely validate an explicit resume."""
    _require(mode in ("running", "shadow"), "unsupported adult mode")
    _require(type(resume) is bool, "resume must be an explicit boolean")
    validate_options(startup_config, explicit_flags)
    _require(startup_config.get("adult_mode", mode) == mode, "adult mode/config mismatch")
    life = lineage._absolute(life_dir)
    if "life_dir" in startup_config:
        _require(lineage._absolute(startup_config["life_dir"]) == life,
                 "life directory differs from frozen startup config")
    adapter, corpus, bindings = _initial(lineage_root, manifest_path, expected_manifest_sha256,
                                        initial_adapter_dir, initial_corpus_path)
    _require(not adapter.is_relative_to(life) and not corpus.is_relative_to(life),
             "initial childhood inputs must be outside the fresh adult life")
    inputs = {item.path: item.sha256 for item in bindings}
    for name in ("gate_panel", "curriculum", "neutral_probe_panel"):
        if startup_config.get(name) is not None:
            path = lineage._absolute(startup_config[name])
            digest = lineage._hash_file(path)
            _require(inputs.get(str(path), digest) == digest,
                     "startup config file conflicts with a pinned initial input")
            inputs[str(path)] = digest
    bindings = tuple(guard.FileBinding(path, digest) for path, digest in sorted(inputs.items()))
    value = dict(schema=SCHEMA, life_dir=str(life), mode=mode, config=startup_config,
                 nonweight_policy=NONWEIGHT_POLICY, initial_adapter=str(adapter),
                 initial_corpus=str(corpus), lineage_root=str(lineage._absolute(lineage_root)),
                 manifest_path=str(manifest_path), manifest_sha256=expected_manifest_sha256,
                 inputs=[dict(path=item.path, sha256=item.sha256) for item in bindings])
    content = _encode(value)
    control = AdultControl(str(life), mode, str(adapter), str(corpus), content.decode(),
                           _sha(content), bindings)
    if resume:
        _verify(control)
        _history(control)
    else:
        if not life.exists():
            lineage._mkdir(life)
        _require(not lineage._names(life), "adult life must be empty; use explicit validated resume")
        directory = life / "adult_control"
        lineage._mkdir(directory)
        lineage._mkdir(directory / "decisions")
        lineage._write(directory / "startup.json", content)
        _verify(control)
    return control


def _verify(control):
    _require(isinstance(control, AdultControl), "expected frozen AdultControl")
    content = control.startup_json.encode()
    _require(_sha(content) == control.startup_sha256, "invalid startup fingerprint")
    value = json.loads(content)
    _require(value["mode"] == control.mode and value["life_dir"] == control.life_dir
             and value["initial_adapter"] == control.initial_adapter
             and value["initial_corpus"] == control.initial_corpus
             and value["inputs"] == [dict(path=item.path, sha256=item.sha256) for item in control.inputs],
             "control does not match frozen startup")
    directory = Path(control.life_dir) / "adult_control"
    _require(lineage._names(directory) == {"startup.json", "decisions"}, "partial/unknown control state")
    _require(lineage._read(directory / "startup.json") == content, "startup config/cache changed")
    for item in control.inputs:
        _require(lineage._hash_file(item.path) == item.sha256, "initial input/evidence cache changed")
    actual = lineage._adapter_inputs(control.initial_adapter, control.model_dir)
    bound = {item.path: item.sha256 for item in control.inputs}
    model_dir = Path(control.model_dir)
    _require(lineage._names(model_dir) == {Path(path).name for path in bound
                                          if Path(path).parent == model_dir},
             "pinned base runtime inventory changed")
    _require(all(bound.get(str(path)) == digest for path, digest in actual.values()),
             "initial adapter inventory changed")
    for name in lineage._names(Path(control.life_dir)):
        if name.startswith("sleep_"):
            _require(re.fullmatch(r"sleep_\d{4,}", name) and int(name[6:]) > 0,
                     "invalid adult sleep; no sleep_0000 inheritance")
            _require(name == _checkpoint(int(name[6:])), "noncanonical adult sleep")
            adapter = Path(control.life_dir) / name / "adapter"
            if adapter.exists():
                _require("DONE" not in lineage._names(adapter), "raw adult candidate cannot be DONE")


def _checkpoint(checkpoint):
    _require(type(checkpoint) is int and checkpoint > 0, "checkpoint must be a positive integer")
    return f"sleep_{checkpoint:04d}"


def _candidate_inputs(control, checkpoint, candidate_dir, corpus_path):
    sleep = Path(control.life_dir) / _checkpoint(checkpoint)
    adapter = lineage._absolute(candidate_dir)
    corpus_path = lineage._absolute(corpus_path)
    _require(adapter == sleep / "adapter" and corpus_path == sleep / "corpus.json",
             "candidate/corpus must belong to this adult checkpoint")
    names = lineage._names(adapter)
    _require("CANDIDATE" in names and "DONE" not in names,
             "expected unpromoted CANDIDATE, never trainer DONE")
    with lineage._directory(adapter) as descriptor:
        info = os.stat("CANDIDATE", dir_fd=descriptor, follow_symlinks=False)
        _require(stat.S_ISREG(info.st_mode), "invalid candidate marker")
    weights = names & {"adapter_model.safetensors", "adapter_model.bin"}
    _require(len(weights) == 1 and names <= weights | {
        "adapter_config.json", "CANDIDATE", "README.md", "train_meta.json"},
        "unsupported candidate contents")
    config = _read_json(adapter / "adapter_config.json")
    _require(config.get("peft_type") == "LORA" and config.get("base_model_name_or_path")
             in (guard.BASE_MODEL, control.model_dir), "candidate changed fixed base/adapter kind")
    startup = json.loads(control.startup_json)["config"]
    if "rank" in startup:
        _require(type(config.get("r")) is int and config["r"] == startup["rank"],
                 "candidate rank differs from frozen startup")
    metadata = _read_json(adapter / "train_meta.json") if "train_meta.json" in names else {}
    if startup.get("train_seed") is not None:
        _require(type(metadata.get("seed")) is int and metadata["seed"] == startup["train_seed"],
                 "candidate training seed differs from frozen startup")
    corpus = _read_json(corpus_path)
    _require(isinstance(corpus.get("corpus"), list) and corpus["corpus"]
             and all(isinstance(text, str) and text.strip() for text in corpus["corpus"]),
             "candidate corpus must contain nonempty text")
    _require(set(_read_json(control.initial_corpus)["corpus"]) <= set(corpus["corpus"]),
             "candidate corpus must retain the pinned initial child corpus")
    files = weights | {"adapter_config.json"} | (names & {"train_meta.json"})
    return dict(adapter={name: lineage._hash_file(adapter / name) for name in sorted(files)},
                corpus_sha256=lineage._hash_file(corpus_path))


def _decision_path(control, checkpoint):
    return Path(control.life_dir) / "adult_control" / "decisions" / _checkpoint(checkpoint)


def _key(control, checkpoint, inputs, previous):
    return _sha(_encode(dict(startup_sha256=control.startup_sha256,
                             checkpoint=checkpoint, inputs=inputs, previous=previous)))


def _history(control):
    directory = Path(control.life_dir) / "adult_control" / "decisions"
    indices = []
    for name in lineage._names(directory):
        _require(re.fullmatch(r"sleep_\d{4,}", name), "unknown/partial decision output")
        index = int(name[6:])
        _require(name == _checkpoint(index), "noncanonical/duplicate checkpoint")
        indices.append(index)
    previous = control.startup_sha256
    records = []
    for checkpoint in sorted(indices):
        destination = _decision_path(control, checkpoint)
        record = _read_json(destination / "decision.json")
        _require(set(record) == _DECISION_FIELDS, "unexpected decision shape")
        _require(record["schema"] == SCHEMA and record["startup_sha256"] == control.startup_sha256
                 and type(record["checkpoint"]) is int and record["checkpoint"] == checkpoint
                 and record["previous"] == previous, "stale decision config/history")
        _require(type(record["accepted"]) is bool and type(record["promoted"]) is bool
                 and record["reason"] in _REASONS
                 and (record["reason"] == "OK") == record["accepted"], "invalid gate outcome")
        _require(record["promoted"] == (control.mode == "running" and record["accepted"]),
                 "shadow/rejected decision cannot promote")
        sleep = Path(control.life_dir) / _checkpoint(checkpoint)
        inputs = _candidate_inputs(control, checkpoint, sleep / "adapter", sleep / "corpus.json")
        _require(record["inputs"] == inputs and record["candidate_key"] ==
                 _key(control, checkpoint, inputs, previous), "stale candidate/corpus cache")
        names = {"decision.json"}
        if record["promoted"]:
            names.add("adapter")
            promoted = destination / "adapter"
            _require(lineage._names(promoted) == set(inputs["adapter"]) | {"DONE"},
                     "partial/unknown promotion output")
            for name, digest in inputs["adapter"].items():
                _require(lineage._hash_file(promoted / name) == digest, "promoted adapter changed")
            _require(lineage._read(promoted / "DONE") == (record["candidate_key"] + "\n").encode(),
                     "promotion marker does not match evaluated candidate")
        _require(lineage._names(destination) == names, "partial/unknown decision output")
        previous = _sha(_encode(record))
        records.append(record)
    return records


@_api
def initial_prior(control):
    """Return only admitted child corpus strings, never the source ledger or briefs."""
    _verify(control)
    return tuple(_read_json(control.initial_corpus)["corpus"])


@_api
def wake_context(control, birth_prompt):
    """No file reads: the adult's only supplied bootstrap is its gym birth prompt."""
    _require(isinstance(control, AdultControl), "expected frozen AdultControl")
    _require(isinstance(birth_prompt, str) and birth_prompt.strip(), "empty gym birth prompt")
    return birth_prompt


@_api
def select_adapter(control):
    """Latest validated running promotion, otherwise the pinned initial adapter."""
    _verify(control)
    for record in reversed(_history(control)):
        if record["promoted"]:
            return str(_decision_path(control, record["checkpoint"]) / "adapter")
    return control.initial_adapter


@_api
def candidate_key(control, checkpoint, *, candidate_dir, corpus_path):
    """Bind BEFORE gate evaluation; caches must retain this original key."""
    _verify(control)
    _checkpoint(checkpoint)
    records = _history(control)
    prior = [record for record in records if record["checkpoint"] < checkpoint]
    previous = _sha(_encode(prior[-1])) if prior else control.startup_sha256
    inputs = _candidate_inputs(control, checkpoint, candidate_dir, corpus_path)
    return _key(control, checkpoint, inputs, previous)


def _result(control, record):
    promoted = str(_decision_path(control, record["checkpoint"]) / "adapter") if record["promoted"] else None
    return AdultDecision(record["checkpoint"], record["accepted"], record["reason"],
                         record["candidate_key"], promoted)


@_api
def get_decision(control, checkpoint):
    """Validated completed decision or None; partial output is never a cache miss."""
    _verify(control)
    _checkpoint(checkpoint)
    return next((_result(control, record) for record in _history(control)
                 if record["checkpoint"] == checkpoint), None)


@_api
def record_decision(control, checkpoint, *, candidate_dir, corpus_path,
                    evaluated_key, accepted, reason):
    """Commit an outcome once; running acceptance alone creates a mountable copy."""
    _verify(control)
    _checkpoint(checkpoint)
    _require(type(accepted) is bool and isinstance(reason, str) and reason in _REASONS
             and (reason == "OK") == accepted, "invalid gate outcome/reason")
    records = _history(control)
    prior = [record for record in records if record["checkpoint"] < checkpoint]
    previous = _sha(_encode(prior[-1])) if prior else control.startup_sha256
    inputs = _candidate_inputs(control, checkpoint, candidate_dir, corpus_path)
    key = _key(control, checkpoint, inputs, previous)
    _require(key == evaluated_key, "stale gate cache: candidate/config/history changed")
    record = dict(schema=SCHEMA, startup_sha256=control.startup_sha256, checkpoint=checkpoint,
                  candidate_key=key, inputs=inputs, previous=previous, accepted=accepted,
                  reason=reason, promoted=control.mode == "running" and accepted)
    existing = next((item for item in records if item["checkpoint"] == checkpoint), None)
    if existing is not None:
        _require(existing == record, "conflicting existing gate decision")
        return _result(control, existing)
    _require(not records or checkpoint > records[-1]["checkpoint"], "out-of-order decision")
    destination = _decision_path(control, checkpoint)
    lineage._mkdir(destination)
    if record["promoted"]:
        promoted = destination / "adapter"
        lineage._mkdir(promoted)
        for name, digest in inputs["adapter"].items():
            lineage._copy(Path(candidate_dir) / name, promoted / name, digest)
        lineage._write(promoted / "DONE", (key + "\n").encode())
    _require(_candidate_inputs(control, checkpoint, candidate_dir, corpus_path) == inputs,
             "candidate changed while recording decision")
    lineage._write(destination / "decision.json", _encode(record))
    _history(control)
    return _result(control, record)
