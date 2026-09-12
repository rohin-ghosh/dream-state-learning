"""Minimal caller-side ancestry recording; no runner, trainer or semantic gate.

Public APIs (keyword arguments without defaults are deliberately mandatory):
  prepare_birth(life_dir, *, model_dir, expected_model_id, expected_model_files,
                loaded_adapter_path, exposure_status, other_influences)
  verify_birth(life_dir, *, model_dir, expected_model_id, expected_model_files,
               expected_manifest_sha256, loaded_adapter_path,
               exposure_status, other_influences)
  record_sleep(life_dir, checkpoint, *, previous_manifest, previous_sha256,
               ledger_path, corpus_path, gate_receipt_path,
               expected_gate_sha256, trainer_receipt_path,
               expected_trainer_sha256, adapter_dir, exposure_status,
               other_influences)

All return LifeCheckpoint; all rejections raise LifeLineageError. Birth needs
an existing EMPTY life directory, an actual loader adapter path of None, and
an explicit empty other-influence inventory. verify_birth is a pre-first-wake
check: even preexisting logs/sleep directories are rejected. model_dir must be
the loader's actual local model directory, not merely a claimed model name.
expected_model_id must come from the external trusted pin inventory and equal
"Qwen/Qwen2.5-7B-Instruct"; neither a filename nor a successful load sets it.
expected_model_files maps every runtime filename to an EXTERNALLY trusted
SHA256, including config, all weight shards/index, and tokenizer files. No
helper generates these pins. Tiny fixture bytes are not authenticated models.

Only HF base ingestion resolves leaf symlinks: it opens and pins the resolved
actual regular files, then COPIES them into lineage/birth/model. Directory
symlinks, all other input symlinks, and symlinks in the bundle remain forbidden.
Use the returned model_dir for loading; reverify the actual loader state before
admission. This module cannot introspect a GPU/model object or prove a caller's
report of in-memory loaded bytes. External pins must identify the fixed Qwen
base; trusting pins generated from arbitrary claimed bytes defeats that gate.

Sleep supports ONLY preschool_records_v1 with the exact corpus keys currently
emitted by that recipe: recipe, corpus, principles=[], n_new,
n_dropped_legacy. Corpus items must exactly match, in order, unique admitted
child note_after rows formatted as:
    Program {episode_id}.\\nMy measured action record: {text.strip()}
For reasoning rg/ episode IDs, the exact producer bytes are instead:
    Situation {episode_id}.\\nMy measured action record: {text}
Reasoning text is not stripped. Its statusless ACT must precede the NOTE_AFTER and
follow its episode_occurrence reservation; scores and derived measurements
must match the ACT. Recognized ledger influences are act, note_after, note,
thought, parent_turn and episode_occurrence. A literal note is child-visible
state only: it requires reasoning-ledger provenance and a reserved training
episode, and cannot serve as either admission record or ACT source. It carries
no inferred generation receipt. Unknown kinds (including episode_end) fail closed
rather than silently diverging from the gate inventory.
No paraphrasing, alternative recipe, or summary-to-admission inference occurs.

Required gate-receipt JSON (all keys mandatory, extras rejected):
  schema_version: 1, recipe: "preschool_records_v1", decision: "ADMIT",
  exposure_status: "UNEXPOSED", previous_manifest_sha256, ledger_sha256,
  corpus_sha256, admissions: [{record_line, record_sha256,
                              source_line, source_sha256}, ...]
Line numbers are ZERO-based physical JSONL lines; hashes include the final LF.
Each admission maps the corresponding corpus item to one note_after and its
unique earlier act row. The gate must supply this receipt AND its externally
selected expected_gate_sha256. Existing articulation summary receipts alone
are insufficient; this module does not mint gate approvals. Matching row hashes
and join fields verifies linkage, NOT the gate's semantic admission decision.

A trained checkpoint additionally requires a separately pinned trainer receipt:
  schema_version: 1, corpus_recipe: "preschool_records_v1",
  supervision: "child_only_v1", status: "COMPLETED",
  previous_manifest_sha256, corpus_sha256, gate_receipt_sha256,
  train_metadata_sha256,
  adapter_files: {actual adapter config/weight filenames: SHA256, ...},
  rows: [{record_sha256, source_sha256, masked_prefix_tokens,
          supervised_prefix_tokens, supervised_child_tokens,
          supervised_padding_tokens}, ...]
All keys are required; rows match gate admissions in corpus order. Prefix and
padding supervision counts must be integer zero; masked-prefix and supervised-
child counts must be positive integers. The TRAINER must derive these counts
from labels actually consumed after truncation/causal shifting, excluding any
token crossing from prefix into child text. This module binds the externally
pinned receipt to corpus, gate, lineage, and actual checkpoint bytes; it does
not replay tokenization or prove training execution. It never generates a
trainer receipt from strings or assumes every corpus byte is a loss target.
Unchanged corpus strings retain the harness prefix as context, not supervision.
Legacy metadata/absent trainer receipts cannot establish a trained binding.
train_metadata_sha256 pins the ACTUAL adapter_dir/train_meta.json, which is
also snapshotted. It must report source_recipe="preschool_records_v1",
loss_target="child_body_only", the exact source_corpus_sha256, a supported
v1_frozen_child_target[_seeded] recipe, and positive integer n_texts, epochs,
steps, tokens, supervised_tokens and masked_nonpadding_tokens. Row counts and
per-epoch supervised totals must agree with it; masked prefix totals cannot
exceed masked nonpadding totals. Native aggregate metadata alone is NOT a
row-linked receipt. Counts must come from actual training, not reconstructed
strings, guessed tokenizer lengths, or post-hoc clean declarations.

The source ledger must inventory all influences for this minimal workflow:
act, note_after, note, thought, parent_turn and episode_occurrence rows only. Additional influence
streams are unsupported, so other_influences must explicitly be empty. Parent
turns stay in the immutable evidence ledger, never as corpus rows; verbatim or
whitespace-normalized parent copies are rejected too. Semantic paraphrases
and factual entailment remain the upstream gate's responsibility. Never report
an empty inventory if lessons, retrieved text, or other influences are omitted.

Sleep snapshots the complete gate-bound ledger, every parent_turn as an explicit
parent_turn source, admitted source/record lines and occurrence reservations,
corpus, gate/trainer receipts, and actual adapter config/weights under a NEW sleep_XXXX
directory. Later ledgers must retain the previous snapshot as an exact byte
prefix. Earlier snapshots are never rewritten. Files are read-only copies,
not hardlinks; hashes detect tampering, but owner chmod is not WORM storage.
Failed attempts retain partial artifacts and cannot be reused automatically.
Previous manifests must descend from this helper's externally verified birth;
the externally selected previous_sha256 transitively pins that birth. Adapter
configs may name the fixed model ID or the exact returned birth model_dir.
Every prior sleep's bound gate/trainer/native-metadata evidence is rechecked;
legacy ancestry without body-only evidence is not upgraded by a new receipt.
record_sleep is only for a runner-accepted checkpoint: adapter_dir must be the
runner-owned final directory with a nonempty regular DONE file, no CANDIDATE,
and no REJECTED_* markers. DONE is snapshotted as separate selection evidence;
it is NOT added to the frozen trainer receipt's adapter_files mapping. A marker
alone proves neither training nor acceptance: the caller must not pass an
unpromoted trainer staging directory whose trainer-owned marker is also DONE.

Scope is ancestry recording only. No promotion, training/corpus-use proof,
architecture change, C11 protocol, semantic entailment or scientific claim is
provided. Main owns loader honesty, complete influence inventory, trusted pin
selection, row-linked gate emission, actual training inputs and integration.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from . import lineage_guard as guard


RECIPE = "preschool_records_v1"
MAX_TEXT_BYTES = 32 * 1024 * 1024
_BASE_NAMES = {
    "config.json", "tokenizer.json", "tokenizer_config.json", "generation_config.json",
    "special_tokens_map.json", "added_tokens.json", "vocab.json", "merges.txt",
    "model.safetensors", "pytorch_model.bin", "model.safetensors.index.json",
    "pytorch_model.bin.index.json",
}
_INERT_NAMES = {"README.md", ".gitattributes", "LICENSE"}
_SHARD = re.compile(r"(?:model-\d{5}-of-\d{5}\.safetensors|"
                    r"pytorch_model-\d{5}-of-\d{5}\.bin)\Z")


class LifeLineageError(guard.LineageGuardError):
    """Missing or contradictory caller evidence; never an eligible fallback."""


@dataclass(frozen=True)
class LifeCheckpoint:
    ancestry: guard.EligibilityReceipt
    model_dir: str
    adapter_dir: str | None
    ledger_snapshot: str | None


def _require(condition, message):
    if not condition:
        raise LifeLineageError(message)


def _api(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except LifeLineageError:
            raise
        except (guard.LineageGuardError, OSError, ValueError, TypeError,
                KeyError, RecursionError) as error:
            raise LifeLineageError(str(error)) from error
    return checked


def _absolute(path):
    path = Path(path)
    _require(".." not in path.parts, "path traversal")
    path = path if path.is_absolute() else Path.cwd() / path
    guard._scan(str(path))
    return path


@contextmanager
def _directory(path):
    path = _absolute(path)
    anchor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with guard._directory(path.parts[1:], anchor) as descriptor:
            yield descriptor
    finally:
        os.close(anchor)


def _names(path):
    with _directory(path) as descriptor:
        return set(os.listdir(descriptor))


@contextmanager
def _input(path):
    path = _absolute(path)
    with _directory(path.parent) as directory:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_size > 0,
                 f"expected nonempty regular input: {path}")
        yield stream
        after = os.fstat(stream.fileno())
        _require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                 == (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                 f"input changed while reading: {path}")


def _read(path):
    with _input(path) as stream:
        content = stream.read(MAX_TEXT_BYTES + 1)
    _require(len(content) <= MAX_TEXT_BYTES, "text evidence exceeds supported bound")
    return content


def _digest(content):
    return hashlib.sha256(content).hexdigest()


def _hash_file(path):
    digest = hashlib.sha256()
    with _input(path) as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json(content):
    value = json.loads(content, object_pairs_hook=guard._json_object,
                       parse_constant=guard._invalid_constant)
    guard._scan(value)
    _require(isinstance(value, dict), "expected JSON object")
    return value


def _mkdir(path):
    with _directory(path.parent) as directory:
        os.mkdir(path.name, mode=0o700, dir_fd=directory)


@contextmanager
def _output(path):
    with _directory(path.parent) as directory:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
    with os.fdopen(descriptor, "wb") as stream:
        yield stream
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


def _write(path, content):
    with _output(path) as stream:
        stream.write(content)
    return _digest(content)


def _copy(source, destination, expected):
    guard._hash(expected)
    digest = hashlib.sha256()
    with _input(source) as incoming, _output(destination) as outgoing:
        while chunk := incoming.read(1024 * 1024):
            outgoing.write(chunk)
            digest.update(chunk)
        _require(digest.hexdigest() == expected, "snapshot SHA256 mismatch")
    return expected


def _declarations(exposure_status, other_influences):
    guard._unexposed(exposure_status)
    _require(isinstance(other_influences, (tuple, list)) and not other_influences,
             "unknown/unsupported additional influences")


def _base_inputs(model_dir, expected, expected_model_id):
    _require(expected_model_id == guard.BASE_MODEL, "external pinned model ID mismatch")
    model_dir = _absolute(model_dir)
    names = _names(model_dir) - _INERT_NAMES
    _require(isinstance(expected, dict) and set(expected) == names,
             "externally pinned model inventory must match actual runtime files")
    _require({"config.json", "tokenizer.json", "tokenizer_config.json"} <= names,
             "missing pinned config/tokenizer files")
    _require(all(name in _BASE_NAMES or _SHARD.fullmatch(name) for name in names),
             "unsupported model file or adapter influence")
    resolved = {}
    for name in sorted(names):
        guard._hash(expected[name])
        actual = (model_dir / name).resolve(strict=True)
        _require(_hash_file(actual) == expected[name], f"external model pin mismatch: {name}")
        resolved[name] = actual
    config = _json(_read(resolved["config.json"]))
    _require(config.get("model_type") == "qwen2" and not config.get("auto_map"),
             "unsupported fixed model config")
    _require(config.get("architectures", ["Qwen2ForCausalLM"]) == ["Qwen2ForCausalLM"],
             "unsupported model architecture")
    tokenizer = _json(_read(resolved["tokenizer_config.json"]))
    _require(not tokenizer.get("auto_map"), "custom tokenizer code unsupported")
    _json(_read(resolved["tokenizer.json"]))
    weights = {name for name in names if name in ("model.safetensors", "pytorch_model.bin")
               or _SHARD.fullmatch(name)}
    indices = {name for name in names if name.endswith(".index.json")}
    _require(bool(weights), "missing pinned model weights")
    if indices:
        _require(len(indices) == 1 and all(_SHARD.fullmatch(name) for name in weights),
                 "ambiguous weight inventory")
        index = _json(_read(resolved[next(iter(indices))]))
        mapping = index.get("weight_map")
        _require(isinstance(mapping, dict) and mapping
                 and all(isinstance(name, str) for name in mapping.values())
                 and set(mapping.values()) == weights, "weight index/shard inventory mismatch")
    else:
        _require(weights in ({"model.safetensors"}, {"pytorch_model.bin"}),
                 "sharded weights require their pinned index")
    return resolved


def _binding(root, path, digest, role=None, references=None):
    value = {"path": path.relative_to(root).as_posix(), "sha256": digest,
             "exposure_status": "UNEXPOSED"}
    if role is not None:
        value["role"] = role
    if references is not None:
        value["source_sha256"] = sorted(set(references))
    return value


def _manifest(kind, parents, sources, artifacts, corpora):
    return {"schema_version": 1, "base_model": guard.BASE_MODEL, "kind": kind,
            "exposure_status": "UNEXPOSED", "parents": parents, "sources": sources,
            "artifacts": artifacts, "trained_corpus": corpora}


def _publish(root, destination, manifest):
    content = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
    digest = _write(destination, content)
    return guard.validate_manifest(destination.relative_to(root), root=root,
                                   expected_sha256=digest)


def _birth_state(life, loaded_adapter_path, exposure_status, other_influences):
    _declarations(exposure_status, other_influences)
    _require(loaded_adapter_path is None, "fresh birth requires actual loaded adapter None")
    return _absolute(life)


def _tree_files(directory):
    files = set()
    with _directory(directory) as descriptor:
        for name in os.listdir(descriptor):
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            path = directory / name
            if stat.S_ISDIR(info.st_mode):
                children = _tree_files(path)
                _require(bool(children), "unknown empty directory at birth")
                files.update(children)
            else:
                _require(stat.S_ISREG(info.st_mode), "symlink/nonregular birth influence")
                files.add(path)
    return files


@_api
def prepare_birth(life_dir, *, model_dir, expected_model_id, expected_model_files, loaded_adapter_path,
                  exposure_status, other_influences):
    """Create immutable birth copies only in a strictly fresh nursery directory."""
    life = _birth_state(life_dir, loaded_adapter_path, exposure_status, other_influences)
    _require(not _names(life), "birth life directory is not empty")
    inputs = _base_inputs(model_dir, expected_model_files, expected_model_id)
    root = life / "lineage"
    destination = root / "birth"
    for directory in (root, destination, destination / "model"):
        _mkdir(directory)
    artifacts = []
    for name, source in inputs.items():
        target = destination / "model" / name
        digest = _copy(source, target, expected_model_files[name])
        artifacts.append(_binding(root, target, digest, "base_model", []))
    receipt = _publish(root, destination / "manifest.json",
                       _manifest("fresh_base", [], [], artifacts, []))
    return verify_birth(life, model_dir=model_dir, expected_model_id=expected_model_id,
                        expected_model_files=expected_model_files,
                        expected_manifest_sha256=receipt.manifest.sha256,
                        loaded_adapter_path=loaded_adapter_path, exposure_status=exposure_status,
                        other_influences=other_influences)


@_api
def verify_birth(life_dir, *, model_dir, expected_model_id, expected_model_files, expected_manifest_sha256,
                 loaded_adapter_path, exposure_status, other_influences):
    """Recheck the actual reported local loader bytes and the recorded birth."""
    life = _birth_state(life_dir, loaded_adapter_path, exposure_status, other_influences)
    _base_inputs(model_dir, expected_model_files, expected_model_id)
    root = life / "lineage"
    receipt = guard.validate_manifest("birth/manifest.json", root=root,
                                      expected_sha256=guard._hash(expected_manifest_sha256))
    expected = {f"birth/model/{name}": digest for name, digest in expected_model_files.items()}
    _require(len(receipt.manifests) == 1
             and {item.path: item.sha256 for item in receipt.files} == expected,
             "birth manifest does not match externally pinned model inventory")
    manifest = _json(_read(root / "birth/manifest.json"))
    _require(manifest["kind"] == "fresh_base", "not a fresh-base manifest")
    allowed = {root / name for name in expected} | {root / "birth/manifest.json"}
    _require(_tree_files(life) == allowed, "unknown influences or populated sleep at birth")
    return LifeCheckpoint(receipt, str(root / "birth/model"), None, None)


def _reasoning_join(source, record, source_index, reservations, rows):
    from .preschool_reasoning import POLICY_VERSION, facts_from_act, _measurement

    for field in ("score", "occurrence_id", "occurrence_index"):
        _require(field in source and field in record
                 and json.dumps(source[field]) == json.dumps(record[field]),
                 f"record/source mismatch: {field}")
    occurrence = source["occurrence_id"]
    _require(isinstance(occurrence, str) and occurrence in reservations,
             "missing occurrence reservation")
    visit_index = reservations[occurrence]
    _require(visit_index < source_index, "occurrence reservation must precede ACT")
    visit = rows[visit_index]
    for field in ("episode_id", "occurrence_id", "occurrence_index"):
        _require(json.dumps(source[field]) == json.dumps(visit[field]),
                 f"occurrence reservation mismatch: {field}")
    _require(visit.get("slot_kind") == "note_after", "unsupported admitted occurrence slot")
    _require(re.fullmatch(re.escape(occurrence) + rf"#t{source['tick']}a[1-9]\d*",
                          source["execution_id"]), "occurrence execution mismatch")
    facts = facts_from_act(source)
    _require(facts.measured, "unmeasured reasoning outcome")
    for field, value in _measurement(facts).items():
        _require(field in record and json.dumps(record[field]) == json.dumps(value),
                 f"reasoning measurement mismatch: {field}")
    _require("status" not in source or source["status"] == record["status"],
             "record/source status mismatch")
    _require(record.get("speaker") == "child" and record.get("policy_version") == POLICY_VERSION,
             "reasoning record is not a current child record")
    return visit_index


def _admissions(ledger, corpus_bytes, gate_bytes, previous_sha256):
    gate = _json(gate_bytes)
    guard._fields(gate, {"schema_version", "recipe", "decision", "exposure_status",
                         "previous_manifest_sha256", "ledger_sha256", "corpus_sha256",
                         "admissions"})
    _require(type(gate["schema_version"]) is int and gate["schema_version"] == 1,
             "unsupported gate receipt version")
    _require(gate["recipe"] == RECIPE and gate["decision"] == "ADMIT",
             "unsupported recipe or non-admission gate receipt")
    guard._unexposed(gate["exposure_status"])
    _require(gate["previous_manifest_sha256"] == previous_sha256
             and gate["ledger_sha256"] == _digest(ledger)
             and gate["corpus_sha256"] == _digest(corpus_bytes), "gate input hash mismatch")
    corpus = _json(corpus_bytes)
    guard._fields(corpus, {"recipe", "corpus", "principles", "n_new", "n_dropped_legacy"})
    _require(corpus["recipe"] == RECIPE and corpus["principles"] == [],
             "unsupported corpus recipe or added principles")
    items = corpus["corpus"]
    _require(isinstance(items, list) and items and all(isinstance(item, str) for item in items)
             and len(set(items)) == len(items), "invalid/duplicate corpus items")
    for field in ("n_new", "n_dropped_legacy"):
        _require(type(corpus[field]) is int and corpus[field] >= 0, "invalid corpus count")
    _require(corpus["n_new"] <= len(items), "invalid new-record count")
    admissions = gate["admissions"]
    _require(isinstance(admissions, list) and len(admissions) == len(items),
             "gate must link every admitted corpus item")
    lines = ledger.splitlines(keepends=True)
    _require(lines and all(line.endswith(b"\n") and not line.endswith(b"\r\n")
                           for line in lines), "ledger requires complete LF-delimited rows")
    rows = [_json(line) for line in lines]
    if any(row.get("kind") == "note" for row in rows):
        from .preschool_reasoning import FAMILIES_FILE, ReasoningGateError, _validate_influences

        try:
            _validate_influences(rows, _json(_read(FAMILIES_FILE)))
        except ReasoningGateError as error:
            raise LifeLineageError(str(error)) from error
    reservations, occurrence_indices = {}, set()
    for index, row in enumerate(rows):
        _require(row.get("kind") in ("act", "note_after", "note", "thought", "parent_turn", "episode_occurrence"),
                 "unsupported/unknown ledger influence")
        if "exposure_status" in row:
            guard._unexposed(row["exposure_status"])
        if row["kind"] == "parent_turn":
            _require(isinstance(row.get("text"), str) and row["text"].strip(),
                     "missing parent-turn text")
        if row["kind"] == "episode_occurrence":
            occurrence_index = row.get("occurrence_index")
            episode = row.get("episode_id")
            _require(type(occurrence_index) is int and occurrence_index > 0
                     and occurrence_index not in occurrence_indices,
                     "invalid/ambiguous occurrence reservation")
            _require(isinstance(episode, str) and episode.strip()
                     and row.get("occurrence_id") == f"{episode}#occ{occurrence_index}",
                     "invalid occurrence reservation identity")
            reservations[row["occurrence_id"]] = index
            occurrence_indices.add(occurrence_index)
    parent_texts = [" ".join(row["text"].casefold().split()) for row in rows
                    if row["kind"] == "parent_turn"]
    linked = {index: (lines[index], "parent_turn") for index, row in enumerate(rows)
              if row["kind"] == "parent_turn"}
    seen = set()
    for item, admission in zip(items, admissions):
        guard._fields(admission, {"record_line", "record_sha256", "source_line", "source_sha256"})
        record_index, source_index = admission["record_line"], admission["source_line"]
        _require(type(record_index) is int and type(source_index) is int
                 and 0 <= source_index < record_index < len(rows), "invalid gate row linkage")
        for index, field in ((record_index, "record_sha256"), (source_index, "source_sha256")):
            _require(guard._hash(admission[field]) == _digest(lines[index]),
                     "gate row SHA256 mismatch")
        record, source = rows[record_index], rows[source_index]
        _require(record.get("kind") == "note_after" and source.get("kind") == "act",
                 "corpus must link child records to environment outcomes, not parent text")
        _require(record.get("speaker", "child") == "child", "admitted record is not child-authored")
        for field in ("execution_id", "episode_id", "action", "outcome"):
            _require(isinstance(source.get(field), str) and source[field].strip()
                     and record.get(field) == source[field], f"record/source mismatch: {field}")
        _require(type(source.get("tick")) is int and type(record.get("tick")) is int
                 and source["tick"] == record["tick"],
                 "record/source tick or status mismatch")
        reasoning = source["episode_id"].startswith("rg/")
        if reasoning:
            visit_index = _reasoning_join(source, record, source_index, reservations, rows)
            linked[visit_index] = (lines[visit_index], "experienced_event")
        else:
            _require(source.get("status") == "success" and record.get("status") == "success",
                     "record/source status mismatch")
        execution = source["execution_id"]
        _require(execution not in seen, "duplicate admission")
        seen.add(execution)
        for kind in ("act", "note_after"):
            _require(sum(row.get("kind") == kind and row.get("execution_id") == execution
                         for row in rows) == 1, "ambiguous execution/record linkage")
        text = record.get("text")
        _require(isinstance(text, str) and text.strip(), "empty admitted child text")
        normalized = " ".join(text.casefold().split())
        _require(not any(parent in normalized or normalized in parent for parent in parent_texts),
                 "parent text cannot be corpus")
        prefix, body = ("Situation", text) if reasoning else ("Program", text.strip())
        _require(item == f"{prefix} {record['episode_id']}.\nMy measured action record: {body}",
                 "corpus is not the exact admitted child-record recipe")
        linked[source_index] = (lines[source_index], "environment_outcome")
        linked[record_index] = (lines[record_index], "experienced_event")
    return linked


def _accepted_marker(adapter_dir):
    adapter_dir = _absolute(adapter_dir)
    names = _names(adapter_dir)
    _require("DONE" in names and "CANDIDATE" not in names
             and not any(name.startswith("REJECTED_") for name in names),
             "record_sleep requires final DONE, not pending/ambiguous/rejected adapter")
    return _read(adapter_dir / "DONE")


def _adapter_inputs(adapter_dir, base_dir):
    adapter_dir = _absolute(adapter_dir)
    _accepted_marker(adapter_dir)
    names = _names(adapter_dir)
    weights = names & {"adapter_model.safetensors", "adapter_model.bin"}
    _require(len(weights) == 1 and "adapter_config.json" in names,
             "missing/ambiguous actual adapter weights/config")
    _require(names <= weights | {"adapter_config.json", "README.md", "train_meta.json", "DONE"},
             "unsupported adapter input")
    config = _json(_read(adapter_dir / "adapter_config.json"))
    _require(config.get("peft_type") == "LORA"
             and config.get("base_model_name_or_path") in (guard.BASE_MODEL, str(base_dir)),
             "adapter is not LoRA for the fixed base")
    return {name: (adapter_dir / name, _hash_file(adapter_dir / name))
            for name in sorted(weights | {"adapter_config.json"})}


def _trainer_evidence(content, gate_bytes, corpus_bytes, previous_sha256, adapter, metadata_bytes):
    receipt = _json(content)
    guard._fields(receipt, {"schema_version", "corpus_recipe", "supervision", "status",
                            "previous_manifest_sha256", "corpus_sha256", "gate_receipt_sha256",
                            "train_metadata_sha256", "adapter_files", "rows"})
    _require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1
             and receipt["corpus_recipe"] == RECIPE and receipt["supervision"] == "child_only_v1"
             and receipt["status"] == "COMPLETED", "unsupported/incomplete child-only trainer receipt")
    _require(receipt["previous_manifest_sha256"] == previous_sha256
             and receipt["corpus_sha256"] == _digest(corpus_bytes)
             and receipt["gate_receipt_sha256"] == _digest(gate_bytes)
             and receipt["train_metadata_sha256"] == _digest(metadata_bytes),
             "trainer receipt input binding mismatch")
    expected_files = {name: digest for name, (_, digest) in adapter.items()}
    _require(receipt["adapter_files"] == expected_files, "trainer receipt adapter binding mismatch")
    rows = receipt["rows"]
    admissions = _json(gate_bytes)["admissions"]
    _require(isinstance(rows, list) and len(rows) == len(admissions),
             "trainer receipt must cover every admitted row")
    metadata = _json(metadata_bytes)
    _require(metadata.get("recipe") in ("v1_frozen_child_target", "v1_frozen_child_target_seeded")
             and metadata.get("source_recipe") == RECIPE
             and metadata.get("loss_target") == "child_body_only"
             and metadata.get("source_corpus_sha256") == _digest(corpus_bytes),
             "actual trainer metadata does not bind body-only preschool training")
    for field in ("n_texts", "epochs", "steps", "tokens", "supervised_tokens", "masked_nonpadding_tokens"):
        _require(type(metadata.get(field)) is int and metadata[field] > 0,
                 "actual trainer metadata lacks completed mask counts")
    _require(metadata["n_texts"] == len(rows)
             and metadata["tokens"] == metadata["supervised_tokens"] + metadata["masked_nonpadding_tokens"],
             "actual trainer metadata count mismatch")
    for row, admission in zip(rows, admissions):
        guard._fields(row, {"record_sha256", "source_sha256", "masked_prefix_tokens",
                           "supervised_prefix_tokens", "supervised_child_tokens",
                           "supervised_padding_tokens"})
        _require(row["record_sha256"] == admission["record_sha256"]
                 and row["source_sha256"] == admission["source_sha256"],
                 "trainer receipt admitted row/source mismatch")
        for field in ("supervised_prefix_tokens", "supervised_padding_tokens"):
            _require(type(row[field]) is int and row[field] == 0,
                     "trainer receipt supervises prefix/padding or lacks mask evidence")
        for field in ("masked_prefix_tokens", "supervised_child_tokens"):
            _require(type(row[field]) is int and row[field] > 0,
                     "trainer receipt lacks positive child-only mask evidence")
    _require(sum(row["supervised_child_tokens"] for row in rows) * metadata["epochs"]
             == metadata["supervised_tokens"]
             and sum(row["masked_prefix_tokens"] for row in rows) * metadata["epochs"]
             <= metadata["masked_nonpadding_tokens"], "trainer row masks disagree with actual training totals")


def _prior_training(root, validated):
    bindings = {item.path: item.sha256 for item in validated.files}
    for binding in validated.manifests:
        if binding.path == "birth/manifest.json":
            continue
        _require(re.fullmatch(r"sleep_\d{4,}/manifest\.json", binding.path),
                 "unsupported prior training ancestry")
        content = _read(root / binding.path)
        _require(_digest(content) == binding.sha256, "prior manifest changed")
        manifest = _json(content)
        _require(len(manifest["parents"]) == 1, "prior sleep must bind exactly one predecessor")
        local = {item["path"] for field in ("sources", "artifacts", "trained_corpus")
                 for item in manifest[field]}
        directory = Path(binding.path).parent
        evidence = {}
        for name in ("ledger.jsonl", "corpus.json", "gate_receipt.json",
                     "trainer_receipt.json", "adapter/train_meta.json", "adapter/DONE"):
            path = (directory / name).as_posix()
            _require(path in local and path in bindings, "prior sleep lacks bound training evidence")
            evidence[name] = _read(root / path)
            _require(_digest(evidence[name]) == bindings[path], "prior training evidence changed")
        adapter = _adapter_inputs(root / directory / "adapter", root / "birth/model")
        for name, (_, digest) in adapter.items():
            path = (directory / "adapter" / name).as_posix()
            _require(path in local and bindings.get(path) == digest, "prior adapter is not bound")
        parent_hash = manifest["parents"][0]["sha256"]
        _admissions(evidence["ledger.jsonl"], evidence["corpus.json"],
                    evidence["gate_receipt.json"], parent_hash)
        _trainer_evidence(evidence["trainer_receipt.json"], evidence["gate_receipt.json"],
                          evidence["corpus.json"], parent_hash, adapter, evidence["adapter/train_meta.json"])


@_api
def record_sleep(life_dir, checkpoint, *, previous_manifest, previous_sha256,
                 ledger_path, corpus_path, gate_receipt_path, expected_gate_sha256,
                 trainer_receipt_path, expected_trainer_sha256, adapter_dir,
                 exposure_status, other_influences):
    """Record one ancestry-only sleep snapshot; never train or promote it."""
    _declarations(exposure_status, other_influences)
    _require(isinstance(checkpoint, str) and re.fullmatch(r"sleep_\d{4,}", checkpoint),
             "unsupported checkpoint name")
    root = _absolute(life_dir) / "lineage"
    guard._relative_path(previous_manifest)
    _require(re.fullmatch(r"(?:birth|sleep_\d{4,})/manifest\.json", previous_manifest),
             "previous manifest must be a birth/sleep checkpoint")
    previous = guard.validate_manifest(previous_manifest, root=root,
                                       expected_sha256=guard._hash(previous_sha256))
    _require(any(item.path == "birth/manifest.json" for item in previous.manifests)
             and {"birth/model/config.json", "birth/model/tokenizer.json",
                  "birth/model/tokenizer_config.json"} <= {item.path for item in previous.files},
             "previous lineage lacks this helper's pinned birth inventory")
    _prior_training(root, previous)
    gate_bytes = _read(gate_receipt_path)
    _require(_digest(gate_bytes) == guard._hash(expected_gate_sha256), "external gate pin mismatch")
    ledger, corpus_bytes = _read(ledger_path), _read(corpus_path)
    linked = _admissions(ledger, corpus_bytes, gate_bytes, previous_sha256)
    if previous_manifest != "birth/manifest.json":
        prior_ledger = str(Path(previous_manifest).parent / "ledger.jsonl")
        bindings = {item.path: item.sha256 for item in previous.files}
        _require(prior_ledger in bindings, "previous sleep lacks a validated source-ledger snapshot")
        old = _read(root / prior_ledger)
        _require(_digest(old) == bindings[prior_ledger] and ledger.startswith(old),
                 "source ledger is not append-only")
    adapter = _adapter_inputs(adapter_dir, root / "birth/model")
    acceptance_bytes = _accepted_marker(adapter_dir)
    trainer_bytes = _read(trainer_receipt_path)
    _require(_digest(trainer_bytes) == guard._hash(expected_trainer_sha256),
             "external trainer pin mismatch")
    metadata_bytes = _read(_absolute(adapter_dir) / "train_meta.json")
    _trainer_evidence(trainer_bytes, gate_bytes, corpus_bytes, previous_sha256, adapter, metadata_bytes)
    destination = root / checkpoint
    _mkdir(destination)
    _mkdir(destination / "adapter")
    sources = []
    target = destination / "ledger.jsonl"
    sources.append(_binding(root, target, _write(target, ledger), "experienced_event"))
    for index, (content, role) in sorted(linked.items()):
        target = destination / f"row_{index:08d}.jsonl"
        sources.append(_binding(root, target, _write(target, content), role))
    references = [source["sha256"] for source in sources]
    target = destination / "gate_receipt.json"
    artifacts = [_binding(root, target, _write(target, gate_bytes), "selection_decision", references)]
    target = destination / "trainer_receipt.json"
    artifacts.append(_binding(root, target, _write(target, trainer_bytes), "selection_decision", references))
    target = destination / "adapter/train_meta.json"
    artifacts.append(_binding(root, target, _write(target, metadata_bytes), "selection_decision", references))
    target = destination / "adapter/DONE"
    artifacts.append(_binding(root, target, _write(target, acceptance_bytes), "selection_decision", references))
    for name, (path, digest) in adapter.items():
        target = destination / "adapter" / name
        artifacts.append(_binding(root, target, _copy(path, target, digest), "lora_adapter", references))
    target = destination / "corpus.json"
    corpora = [_binding(root, target, _write(target, corpus_bytes), references=references)]
    manifest = _manifest("descendant", [{"path": previous_manifest, "sha256": previous_sha256}],
                         sources, artifacts, corpora)
    _require(_accepted_marker(adapter_dir) == acceptance_bytes, "adapter acceptance changed during recording")
    receipt = _publish(root, destination / "manifest.json", manifest)
    return LifeCheckpoint(receipt, str(root / "birth/model"), str(destination / "adapter"),
                          str(destination / "ledger.jsonl"))
