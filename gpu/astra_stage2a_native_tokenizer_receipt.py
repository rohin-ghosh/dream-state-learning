"""CPU-only, supplied-input TOKENIZER receipt; no CLI, loader or launch path.

Non-material preparation integration, not a new qualification definition.
Main supplies bound objects, complete terminal source reports, an explicit local
model directory and an already loaded tokenizer. Only an explicit function call
invokes that tokenizer's existing CPU interface; importing performs no work.
No allocator, constructor replay, model, torch/CUDA, network or subprocess is
used. Injected Python interfaces are trusted code, not sandboxed by this module.

PER_ARM_MAX is selected here prospectively, before measurement. All 512 records
and 512 conditional paired batches are retained, not executed. Package metadata
is installed-distribution evidence, never a wheel archive attestation. Neither
file matching nor this receipt authorizes native training or scientific claims.
Failures leave a read-only attempt, including the original source reports.
Read-only files are an accidental-overwrite guard, not a security boundary.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata
import json
import math
from pathlib import Path, PurePosixPath

from gpu import astra_stage2a_native_prepare as prepare
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ASTRA_STAGE2A_NATIVE_TOKENIZER_RECEIPT_V1"
QUALIFICATION_SCHEMA = "ASTRA_STAGE2A_V6_FULL_POPULATION_CPU_V1"
SEPARATION_KIND = "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS"
PADDING_POLICY = "PER_ARM_MAX"
REPOSITORY = "Qwen/Qwen2.5-7B-Instruct"
REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
OFFICIAL_RECEIPT_SHA256 = "e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019"
EXECUTION_PINS = {
    "research_notes/analysis/2026-09-14_stage2a_binding_successor_v6_typed_boundary.md":
        "119b97eb418e7b9586c1425c091b846f7eb7f100ab337ca03cc8b92df2b7b0b6",
    "research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v2.md":
        "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74",
}
REQUIRED_FILES = ("config.json", "generation_config.json", "tokenizer.json",
                  "tokenizer_config.json", "merges.txt", "vocab.json")
RUNTIME_VERSIONS = {"torch": "2.13.0+cu130", "transformers": "5.5.3",
                    "peft": "0.20.0", "vllm": "0.27.1", "tokenizers": "0.22.2"}
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_INPUT_BYTES = 4 * 1024 * 1024 * 1024
MAX_OUTPUT_BYTES = 2 * 1024 * 1024 * 1024
FAILURE_RESERVE_BYTES = 64 * 1024
MAX_SOURCE_FILES = 4096
ARMS = ("CLOSED", "ATOM_LOCAL")
QUALIFICATION_UNUSED_SEPARATION_FILES = frozenset({
    "organism_v6/composition_birth_stage2a_separation.py",
    "tests/test_composition_birth_stage2a_separation.py",
})


@dataclass(frozen=True, repr=False)
class TokenizerReceipt:
    output_dir: Path
    receipt_sha256: str
    prepared_birth: prepare.PreparedBirth


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _digest(raw):
    return sha256(raw).hexdigest()


def _sha(value):
    return type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite_json_number:" + value)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def _encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii") + b"\n"


def retain(value):
    """Lossless tagged values; tuple/map keys and bytes never become strings."""
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is bytes:
        return {"bytes_hex": value.hex()}
    if is_dataclass(value) and not isinstance(value, type):
        return {"dataclass": type(value).__module__ + "." + type(value).__qualname__,
                "fields": [[field.name, retain(getattr(value, field.name))] for field in fields(value)]}
    if isinstance(value, Mapping):
        return {"mapping": [[retain(key), retain(item)] for key, item in value.items()]}
    if type(value) is tuple:
        return {"tuple": [retain(item) for item in value]}
    if type(value) is list:
        return {"list": [retain(item) for item in value]}
    raise ValueError("unsupported_receipt_value:" + type(value).__name__)


class _Attempt:
    def __init__(self, output_dir):
        path = Path(output_dir).absolute()
        _require(path.parent.is_dir(), "output_parent_must_exist")
        path.mkdir(exist_ok=False)
        self.path = path
        self.read_bytes = 0
        self.written_bytes = 0
        self.files = {}

    def read(self, path):
        path = Path(path)
        _require(path.is_file(), "input_regular_file_required:" + str(path))
        remaining = min(MAX_FILE_BYTES, MAX_INPUT_BYTES - self.read_bytes)
        _require(0 <= path.stat().st_size <= remaining, "input_byte_bound_exceeded")
        with path.open("rb") as stream:
            raw = stream.read(remaining + 1)
        self.read_bytes += len(raw)
        _require(len(raw) <= remaining, "input_byte_bound_exceeded")
        return raw

    def write(self, name, raw):
        _require(len(raw) <= MAX_FILE_BYTES
                 and self.written_bytes + len(raw) <= MAX_OUTPUT_BYTES - FAILURE_RESERVE_BYTES,
                 "output_byte_bound_exceeded")
        destination = self.path / name
        with destination.open("xb") as stream:
            stream.write(raw)
        destination.chmod(0o444)
        self.written_bytes += len(raw)
        self.files[name] = {"sha256": _digest(raw), "bytes": len(raw)}

    def json(self, name, value):
        self.write(name, _encode(value))

    def freeze(self):
        for path in self.path.iterdir():
            path.chmod(0o444)
        self.path.chmod(0o555)


def _relative(name):
    _require(type(name) is str and bool(name) and "\\" not in name, "invalid_manifest_path")
    path = PurePosixPath(name)
    _require(not path.is_absolute() and name != "." and ".." not in path.parts and str(path) == name,
             "invalid_manifest_path")
    return name


def _gate_documents(attempt, directory, label):
    documents = {}
    for name in ("report.json", "manifest.json", "SNAPSHOT.json"):
        raw = attempt.read(Path(directory) / name)
        attempt.write(label + "_" + name, raw)
        documents[name] = _json(raw)
    return documents["report.json"], documents["manifest.json"], documents["SNAPSHOT.json"]


def _check_source_pins(attempt, report, manifest, snapshot, master, *, dispositions=None):
    pins = report.get("source_pins")
    _require(type(pins) is dict and 0 < len(pins) <= MAX_SOURCE_FILES, "complete_source_pins_required")
    _require(pins == manifest.get("source_pins") == snapshot.get("source_pins"), "source_gate_pin_mismatch")
    _require(manifest.get("master_hex") == master.hex(), "source_gate_master_mismatch")
    required = {str(path.relative_to(ROOT)) for path in ROOT.glob("organism_v6/composition_birth_stage2a*.py")}
    required.update(EXECUTION_PINS)
    _require(required <= pins.keys(), "incomplete_source_gate_pins")
    for name, digest in pins.items():
        _require(_sha(digest), "invalid_source_digest")
        expected = (dispositions or {}).get(name, {}).get("current_sha256", digest)
        _require(_digest(attempt.read(ROOT / _relative(name))) == expected, "source_hash_incompatible:" + name)
    for name, digest in EXECUTION_PINS.items():
        _require(pins.get(name) == digest, "selected_execution_pin_mismatch")
    return pins


def _capture_recovery(attempt, replay, original, recovery):
    old_pins = recovery.get("original_source_pins")
    _require(type(old_pins) is dict and 0 < len(old_pins) <= MAX_SOURCE_FILES, "bounded_original_source_pins_required")
    paths = [original / name for name in (*replay.CONTROL_NAMES, *replay.INDEX_NAMES)]
    paths.extend(original / "source" / _relative(name) for name in old_pins)
    sizes = [path.stat().st_size for path in paths]
    _require(all(0 <= size <= MAX_FILE_BYTES for size in sizes)
             and attempt.read_bytes + sum(sizes) <= MAX_INPUT_BYTES, "input_byte_bound_exceeded")
    attempt.read_bytes += sum(sizes)
    captured = replay.capture_recovery(original, recovery["source_pins"])
    captured["original_root"] = recovery["original_root"]
    _require(captured == recovery, "recovery_original_or_current_inputs_changed")
    return captured


def _verify_replay_blobs(attempt, original, report):
    blob_lengths = report.get("retained_blob_lengths")
    _require(type(blob_lengths) is dict and 0 < len(blob_lengths) <= 16384
             and report.get("retained_unique_blobs") == len(blob_lengths)
             and all(_sha(checksum) and type(length) is int and 0 < length <= MAX_FILE_BYTES
                     for checksum, length in blob_lengths.items()), "complete_replay_blob_pins_required")
    _require(report.get("retained_unique_bytes") == sum(blob_lengths.values()), "replay_blob_byte_count_mismatch")
    for checksum, length in blob_lengths.items():
        _require(len(_artifact(attempt, original, checksum)) == length, "replay_retained_blob_length_mismatch")


def _separation_documents(attempt, directory, master, separation_original_dir=None):
    directory = Path(directory)
    if not (directory / "RECOVERY.json").exists():
        _require(separation_original_dir is None, "relocation_requires_recovery_manifest")
        report, manifest, snapshot = _gate_documents(attempt, directory, "separation")
        return report, manifest, snapshot, directory, None
    from gpu import astra_stage2a_separation_replay as replay

    documents = {}
    for name in ("report.json", "SNAPSHOT.json", "RECOVERY.json"):
        raw = attempt.read(directory / name)
        attempt.write("separation_" + name, raw)
        documents[name] = _json(raw)
    report, snapshot, recovery = (documents[name] for name in ("report.json", "SNAPSHOT.json", "RECOVERY.json"))
    _require(report.get("kind") == recovery.get("kind") == replay.KIND
             and report.get("status") == "SEPARATED" and "error" not in report,
             "complete_separation_SEPARATED_required")
    _require(report.get("snapshot_manifest_sha256") == attempt.files["separation_SNAPSHOT.json"]["sha256"]
             and report.get("recovery_manifest_sha256") == attempt.files["separation_RECOVERY.json"]["sha256"]
             and report.get("source_pins") == snapshot.get("source_pins") == recovery.get("source_pins")
             and report.get("original_files") == recovery.get("original_files"), "replay_manifest_binding_mismatch")
    _require(type(recovery.get("original_root")) is str and Path(recovery["original_root"]).is_absolute(),
             "explicit_original_separation_root_required")
    original = Path(separation_original_dir if separation_original_dir is not None else recovery["original_root"]).resolve(strict=True)
    pins = recovery["source_pins"]
    _require(type(pins) is dict and 0 < len(pins) <= MAX_SOURCE_FILES, "complete_replay_source_pins_required")
    for name, checksum in pins.items():
        _require(_sha(checksum) and _digest(attempt.read(ROOT / _relative(name))) == checksum,
                 "replay_source_hash_incompatible:" + name)
    captured = _capture_recovery(attempt, replay, original, recovery)
    original_report, original_manifest, original_snapshot = _gate_documents(attempt, original, "original_separation")
    _require(original_manifest.get("master_hex") == master.hex(), "source_gate_master_mismatch")
    _require(original_report.get("status") == "ERROR" and original_report.get("error") == "aggregate_byte_bound_exceeded",
             "original_capacity_error_required")
    _verify_replay_blobs(attempt, original, report)
    attempt.json("recovery_recapture.json", captured)
    attempt.json("separation_location.json", {"recorded_original_root": recovery["original_root"],
                 "actual_original_root": str(original),
                 "original_RECOVERY_sha256": attempt.files["separation_RECOVERY.json"]["sha256"],
                 "normalization": "Only captured original_root restored to recorded original_root for equality."})
    manifest = {"master_hex": master.hex(), "source_pins": pins, "kind": replay.KIND}
    return report, manifest, snapshot, original, recovery


def _qualification_dispositions(attempt, directory, qualified, recovery):
    if recovery is None:
        return {}
    from gpu import astra_stage2a_separation_replay as replay

    old_pins, current_pins = recovery["original_source_pins"], recovery["source_pins"]
    qualified_pins = qualified.get("source_pins", {})
    dispositions = {}
    for name in QUALIFICATION_UNUSED_SEPARATION_FILES:
        if name not in qualified_pins or qualified_pins[name] == current_pins.get(name):
            continue
        _require(qualified_pins[name] == old_pins.get(name) and name in current_pins,
                 "qualification_separation_exception_not_original")
        raw = attempt.read(Path(directory) / "source" / name)
        _require(_digest(raw) == qualified_pins[name], "qualification_original_source_snapshot_changed")
        if name == replay.SEPARATION_PATH:
            _require(_digest(replay.capacity_repair(raw)) == current_pins[name], "noncapacity_separation_change")
        dispositions[name] = {"qualification_sha256": qualified_pins[name], "current_sha256": current_pins[name],
            "reason": "Unused by qualification runner/oracles and its explicit integrity suites; separation-only capacity repair validated by capture_recovery.",
            "binding": "successful separation RECOVERY.json and source_pins"}
        attempt.write("qualification_original_" + Path(name).name, raw)
    return dispositions


def _artifact(attempt, directory, digest):
    _require(_sha(digest), "artifact_digest_required")
    raw = attempt.read(Path(directory) / "artifacts" / digest)
    _require(_digest(raw) == digest, "source_artifact_hash_mismatch")
    return raw


def _source_gates(attempt, qualification_dir, separation_dir, bound_allocation, compiled, master,
                  separation_original_dir=None):
    qualified, qualification_manifest, qualification_snapshot = _gate_documents(attempt, qualification_dir, "qualification")
    separated, separation_manifest, separation_snapshot, separation_artifacts, recovery = _separation_documents(
        attempt, separation_dir, master, separation_original_dir)
    _require(qualified.get("schema") == QUALIFICATION_SCHEMA
             and qualification_manifest.get("schema") == QUALIFICATION_SCHEMA
             and qualified.get("kind") == qualification_manifest.get("kind") == "CPU_FULL_POPULATION_NOT_NATIVE_READINESS"
             and qualified.get("status") == "PASS" and qualified.get("failures") == [],
             "complete_qualification_PASS_required")
    _require(separated.get("kind") == separation_manifest.get("kind")
             and (recovery is not None or separated.get("kind") == SEPARATION_KIND)
             and separated.get("status") == "SEPARATED" and "error" not in separated,
             "complete_separation_SEPARATED_required")
    dispositions = _qualification_dispositions(attempt, qualification_dir, qualified, recovery)
    pins = _check_source_pins(attempt, qualified, qualification_manifest, qualification_snapshot, master,
                              dispositions=dispositions)
    separation_pins = _check_source_pins(attempt, separated, separation_manifest, separation_snapshot, master)
    _require(all(pins[name] == separation_pins[name] for name in pins.keys() & separation_pins.keys()
                 if name not in dispositions),
             "source_gate_cross_report_incompatibility")
    counts = qualified.get("counts", {})
    expected = {"pairs": 32, "cases": 64, "units": 256, "arm_records": 512,
                "paired_scoring_training_suite_exit_zero": 1}
    expected.update(dict.fromkeys(("foreign_arm", "foreign_case", "foreign_master", "foreign_roles",
                                  "boundary_crossing", "caller_field_observations", "caller_candidate_inventory",
                                  "caller_typed_occurrence_receipts"), 512))
    expected.update({"boundary_injection_route_actions_" + name: 512 for name in ("literal", "spacing", "compact")})
    expected.update({"boundary_injection_route_" + name: 512 for name in ("ordered_ids", "event_rows", "mixed")})
    _require(all(type(counts.get(key)) is int and counts[key] == value for key, value in expected.items())
             and type(counts.get("integrity_tests")) is int and counts["integrity_tests"] > 0,
             "incomplete_qualification_population_or_integrity")
    _require(qualified.get("commands") == {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32},
             "qualification_command_counts_mismatch")
    expected_separation = {"birth_records": 512, "birth_units": 256, "intervention_members": 64,
                           "chain_worlds": 16, "chain_members": 32, "chain_boundaries": 240,
                           "held_records": 304, "checked_envelopes": 816,
                           "core_collision_hashes": 0, "core_collision_pairs": 0,
                           "signature_collision_hashes": 0, "signature_collision_pairs": 0}
    _require(all(type(separated.get("counts", {}).get(key)) is int and separated["counts"][key] == value
                 for key, value in expected_separation.items()), "incomplete_separation_population")
    empty_collisions = [] if recovery is not None else {"tuple": []}
    _require(separated.get("core_collisions") == empty_collisions
             and separated.get("signature_collisions") == empty_collisions, "separation_collision_receipt_mismatch")
    _require(type(bound_allocation) is prepare.allocation.Stage2AAllocation, "bound_allocation_required")
    allocation_raw = bound_allocation.custody_bytes
    allocation_digest = _digest(allocation_raw)
    _require(bound_allocation.custody_sha256 == allocation_digest
             and _json(allocation_raw).get("master") == {"bytes_hex": master.hex(), "sha256": _digest(master)},
             "allocation_master_or_digest_mismatch")
    _require(_artifact(attempt, qualification_dir, allocation_digest) == allocation_raw,
             "qualified_allocation_mismatch")
    separation_allocation = _json(attempt.read(separation_artifacts / "allocation.json"))
    _require(separation_allocation == {"bytes_sha256": allocation_digest, "length": len(allocation_raw)}
             and _artifact(attempt, separation_artifacts, allocation_digest) == allocation_raw,
             "separated_allocation_mismatch")
    attempt.write("allocation.json", allocation_raw)
    pairs = prepare._curriculum_pairs(compiled, master)
    worlds = bound_allocation.role_tokens_by_world("birth_train")
    _require(len(compiled.pairs) == 32 and set(worlds) == {pair.world for pair in compiled.pairs},
             "compiled_allocation_world_mismatch")
    for pair in compiled.pairs:
        _require(dict(pair.role_tokens) == dict(worlds[pair.world]), "compiled_allocation_roles_mismatch")
    records = {pair.closed.unit.unit_id + "/" + row.arm: row for pair in pairs for row in (pair.closed, pair.atom_local)}
    _require(qualified.get("phases") == dict(Counter(record.unit.phase + "/" + record.arm for record in records.values())),
             "qualification_phase_counts_mismatch")
    rows = qualified.get("records")
    _require(type(rows) is list and len(rows) == 512
             and Counter(row.get("identity") for row in rows) == Counter(records.keys()),
             "complete_512_qualification_rows_required")
    required_artifacts = {"boundary", "shared", "candidates", "retained", "routes", "private_static_basis",
                          "private_record_basis", "typed_receipts", "core", "checker", "checker_receipt",
                          "foreign_master", "foreign_roles"}
    for index, row in enumerate(rows):
        _require(row.get("status") == "PASS" and required_artifacts <= row.get("artifacts", {}).keys()
                 and all(_sha(value) for value in row["artifacts"].values()), "incomplete_qualification_row")
        raw = _artifact(attempt, qualification_dir, row["artifacts"]["boundary"])
        boundary = _json(raw)
        record = records[row["identity"]]
        record_digest = _digest(prepare.canonical_json(source_inputs._digest_value(record)))
        provenance_raw = bytes.fromhex(boundary["source_provenance"]["bytes_hex"])
        provenance = _json(provenance_raw)
        _require(boundary.get("record_sha256") == record_digest
                 and boundary.get("unit_id") == record.unit.unit_id and boundary.get("arm") == record.arm
                 and boundary.get("source_prefix_sha256") == record.prefix_sha256
                 and boundary.get("public_messages") == [{"role": message.role, "content": message.content}
                                                           for message in record.prefix]
                 and boundary.get("shared_custody_sha256") == row["artifacts"]["shared"]
                 and boundary.get("source_provenance_sha256") == _digest(provenance_raw)
                 and provenance.get("record_sha256") == record_digest
                 and provenance.get("display_master_sha256") == _digest(master)
                 and provenance.get("role_tokens_sha256") == _digest(prepare.canonical_json(dict(worlds[boundary["world"]]))),
                 "qualified_boundary_input_mismatch")
        attempt.write(f"source_boundary_{index:03d}.json", raw)
    return {"qualification_status": "PASS", "separation_status": "SEPARATED",
            "qualification_source_pins": pins, "separation_source_pins": separation_pins,
            "qualification_dependency_dispositions": dispositions,
            "separation_artifacts_root": str(separation_artifacts),
            "separation_recorded_original_root": recovery["original_root"] if recovery is not None else None,
            "separation_RECOVERY_sha256": attempt.files["separation_RECOVERY.json"]["sha256"] if recovery is not None else None,
            "separation_recovery": recovery,
            "reconstructed_qualification": False,
            "limit": "Existing terminal reports consumed; only retained boundary/allocation artifacts reread, not full custody replay."}


def official_native_backend(raw):
    import tokenizers

    _require(tokenizers.__version__ == RUNTIME_VERSIONS["tokenizers"], "native_tokenizers_version_mismatch")
    _require(len(raw) <= MAX_FILE_BYTES, "official_backend_byte_bound_exceeded")
    return tokenizers.Tokenizer.from_str(raw.decode("utf-8"))


def canonical_official_backend(raw):
    return official_native_backend(raw).to_str().encode("utf-8")


def restore_official_backend(tokenizer, model_dir, official_files, output_dir):
    attempt = _Attempt(output_dir)
    try:
        raw = attempt.read(Path(model_dir) / "tokenizer.json")
        expected = official_files["tokenizer.json"]
        _require(_digest(raw) == expected["sha256"] and len(raw) == expected["size"],
                 "official_backend_file_mismatch")
        attempt.write("official.json", raw)
        before = tokenizer.backend_tokenizer.to_str().encode("utf-8")
        attempt.write("before.json", before)
        backend = official_native_backend(raw)
        reference = backend.to_str().encode("utf-8")
        attempt.write("reference.json", reference)
        attributes = ("chat_template", "padding_side", "eos_token", "eos_token_id", "pad_token", "pad_token_id")
        wrapper = {name: getattr(tokenizer, name) for name in attributes}
        special_ids = tuple(tokenizer.all_special_ids)
        tokenizer._tokenizer = backend
        after = tokenizer.backend_tokenizer.to_str().encode("utf-8")
        attempt.write("after.json", after)
        _require(tokenizer.backend_tokenizer is backend and after == reference,
                 "official_backend_restoration_failed")
        _require(wrapper == {name: getattr(tokenizer, name) for name in attributes}
                 and special_ids == tuple(tokenizer.all_special_ids), "backend_restoration_changed_wrapper")
        return {"kind": "EXACT_OFFICIAL_NATIVE_BACKEND_RESTORATION", "tokenizers": RUNTIME_VERSIONS["tokenizers"],
                "before_sha256": _digest(before), "reference_sha256": _digest(reference),
                "after_sha256": _digest(after), "official_sha256": _digest(raw), "wrapper": wrapper}
    finally:
        attempt.freeze()


def _tokenizer_binding(attempt, tokenizer, model_dir, official_manifest, loaded_files):
    model_dir = Path(model_dir).resolve(strict=True)
    _require(model_dir.is_dir(), "explicit_model_directory_required")
    raw = attempt.read(official_manifest)
    _require(_digest(raw) == OFFICIAL_RECEIPT_SHA256, "official_manifest_authentication_mismatch")
    official = _json(raw)
    _require(official.get("repository") == REPOSITORY and official.get("revision") == REVISION
             and official.get("status") == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING",
             "official_repository_revision_mismatch")
    _require(type(loaded_files) is tuple and set(REQUIRED_FILES) <= set(loaded_files)
             and len(loaded_files) == len(set(loaded_files)) and len(loaded_files) <= 32,
             "complete_explicit_loaded_file_roster_required")
    attempt.write("official_manifest.json", raw)
    files = {}
    documents = {}
    for name in loaded_files:
        _relative(name)
        _require("/" not in name and name in official["files"]
                 and not name.startswith("model") and name.endswith((".json", ".txt", ".jinja")),
                 "unmanifested_or_weight_file_forbidden")
        content = attempt.read(model_dir / name)
        expected = official["files"][name]
        _require(_digest(content) == expected["sha256"] and len(content) == expected["size"],
                 "official_file_mismatch:" + name)
        files[name] = {"sha256": _digest(content), "bytes": len(content)}
        attempt.write("model_" + name, content)
        if name in ("tokenizer_config.json", "tokenizer.json", "config.json"):
            documents[name] = _json(content)
    candidates = {path.name for path in model_dir.iterdir() if
                  path.name.startswith(("tokenizer", "chat_template", "special_tokens", "added_tokens"))}
    _require(candidates <= set(loaded_files), "undeclared_tokenizer_or_template_file")
    _require(type(getattr(tokenizer, "name_or_path", None)) is str
             and Path(tokenizer.name_or_path).resolve() == model_dir, "loaded_tokenizer_directory_mismatch")
    config = documents["tokenizer_config.json"]
    _require(type(config.get("chat_template")) is str
             and tokenizer.chat_template == config["chat_template"], "loaded_chat_template_mismatch")
    _require(getattr(tokenizer, "is_fast", False) is True and tokenizer.padding_side == "right",
             "fast_right_padding_tokenizer_required")
    backend_raw = tokenizer.backend_tokenizer.to_str().encode("utf-8")
    attempt.write("loaded_backend.json", backend_raw)
    reference_raw = canonical_official_backend(attempt.read(attempt.path / "model_tokenizer.json"))
    attempt.write("official_native_backend.json", reference_raw)
    _require(len(backend_raw) <= MAX_FILE_BYTES and backend_raw == reference_raw,
             "loaded_backend_differs_from_official_tokenizer")
    _require(documents["tokenizer.json"].get("padding") is None
             and documents["tokenizer.json"].get("truncation") is None, "implicit_backend_padding_or_truncation")
    for name in ("eos_token", "pad_token"):
        text = config.get(name)
        _require(type(text) is str and getattr(tokenizer, name) == text, "loaded_special_token_mismatch")
        expected_ids = [int(key) for key, value in config["added_tokens_decoder"].items() if value["content"] == text]
        _require(len(expected_ids) == 1 and type(getattr(tokenizer, name + "_id")) is int
                 and getattr(tokenizer, name + "_id") == expected_ids[0], "loaded_special_id_mismatch")
    special_ids = {entry["id"] for entry in documents["tokenizer.json"]["added_tokens"] if entry["special"]}
    _require(set(tokenizer.all_special_ids) == special_ids, "loaded_special_inventory_mismatch")
    attempt.write("loaded_chat_template.txt", tokenizer.chat_template.encode("utf-8"))
    return {"repository": REPOSITORY, "revision": REVISION, "model_directory": str(model_dir),
            "files": files, "loaded_class": type(tokenizer).__module__ + "." + type(tokenizer).__qualname__,
            "backend_sha256": _digest(backend_raw), "official_native_backend_sha256": _digest(reference_raw),
            "chat_template_sha256": _digest(tokenizer.chat_template.encode("utf-8")),
            "eos_token_id": tokenizer.eos_token_id, "pad_token_id": tokenizer.pad_token_id,
            "limit": "File bytes and serialized backend/template match; injected executable class is Main's trust boundary."}


def _package_metadata(attempt):
    packages = {}
    for name, expected in RUNTIME_VERSIONS.items():
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            packages[name] = {"installed": False, "version": None, "selected_version": expected,
                              "wheel_archive_sha256": None}
            continue
        recorded = {}
        for filename in ("METADATA", "WHEEL", "RECORD", "INSTALLER", "direct_url.json"):
            content = distribution.read_text(filename)
            if content is not None:
                raw = content.encode("utf-8")
                _require(len(raw) <= MAX_FILE_BYTES, "package_metadata_byte_bound_exceeded")
                destination = "package_" + name + "_" + filename
                attempt.write(destination, raw)
                recorded[filename] = attempt.files[destination]
        packages[name] = {"installed": True, "version": distribution.version,
                          "selected_version": expected, "matches_selected_version":
                          distribution.version == expected if expected is not None else None,
                          "metadata": recorded, "wheel_archive_sha256": None}
    return {"distributions": packages, "wheel_attestation": "NOT_PROVIDED",
            "limit": "Installed metadata text only, not original wheel bytes or runtime/CUDA qualification; Main adjudicates missing attestations and version mismatches."}


def prepare_tokenizer_receipt(*, bound_allocation, compiled_curriculum, master, tokenizer,
                              model_dir, official_manifest, loaded_files, qualification_dir,
                              separation_dir, output_dir, separation_original_dir=None):
    """Explicit future CPU preparation; callers cannot pass a green gate flag.

    Qualification contains report.json, manifest.json, SNAPSHOT.json and retained
    allocation/boundary artifacts. Separation accepts the original full format
    or a successful report.json + SNAPSHOT.json + RECOVERY.json; recovery uses
    original artifacts and the replay verifier, never constructor/decoder replay.
    Optional separation_original_dir relocates copied evidence; only the captured
    original_root is normalized back to its recorded value for comparison.
    Output's parent must exist and
    output itself must not. No reconstruction, training or native admission.
    Returns the original PreparedBirth for Main plus an immutable receipt path.
    Limits bound file I/O and existing 16,384-token mechanics, not execution
    time or process RSS of a caller-supplied Python tokenizer.
    """
    _require(type(master) is bytes and 0 < len(master) <= 4096, "bounded_explicit_master_required")
    attempt = _Attempt(output_dir)
    try:
        attempt.json("request.json", {"schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
                     "master_hex": master.hex(), "master_sha256": _digest(master),
                     "padding_policy": PADDING_POLICY, "selected_execution_pins": EXECUTION_PINS,
                     "limits": {"input_bytes": MAX_INPUT_BYTES, "file_bytes": MAX_FILE_BYTES,
                                "output_bytes": MAX_OUTPUT_BYTES, "failure_reserve_bytes": FAILURE_RESERVE_BYTES,
                                "context_tokens": 16384},
                     "executed_updates": 0, "model_loaded_by_wrapper": False})
        gates = _source_gates(attempt, qualification_dir, separation_dir, bound_allocation, compiled_curriculum, master,
                              separation_original_dir)
        binding = _tokenizer_binding(attempt, tokenizer, model_dir, official_manifest, loaded_files)
        packages = _package_metadata(attempt)
        helper_pins = {}
        for path in (Path(__file__), Path(prepare.__file__)):
            raw = attempt.read(path)
            helper_pins[str(path.relative_to(ROOT))] = _digest(raw)
            attempt.write("implementation_" + path.name, raw)
        prepared = prepare.prepare_birth(validated_curriculum=compiled_curriculum, tokenizer=tokenizer,
                                         master=master, padding_policy=PADDING_POLICY)
        _require(len(prepared.tokenized_pairs) == 256 and len(prepared.batches) == 512, "incomplete_preparation")
        attempt.write("source_preparation.json", prepared.receipt_bytes)
        for index, pair in enumerate(prepared.tokenized_pairs):
            attempt.json(f"token_rows_{index:03d}.json", retain(pair))
        totals = {stage: {arm: Counter() for arm in ARMS} for stage in ("D1", "D2")}
        for batch in prepared.batches:
            arms = {}
            for arm, value in (("CLOSED", batch.closed), ("ATOM_LOCAL", batch.atom_local)):
                _require(len(value.records) == 4 and value.padding_length == max(len(row.input_ids) for row in value.records),
                         "measured_four_sequence_per_arm_max_required")
                arms[arm] = {"record_unit_ids": [row.record.unit.unit_id for row in value.records],
                             "input_ids": value.input_ids, "labels": value.labels, "attention_mask": value.attention_mask,
                             "padding_length": value.padding_length, "accounting": dict(value.accounting)}
                totals[batch.presentation.stage][arm].update(value.accounting)
            attempt.json(f"batch_{batch.presentation.update_number:03d}.json",
                         {"presentation": retain(batch.presentation), "arms": arms,
                          "target_hashes": batch.target_hashes, "target_token_counts": batch.target_token_counts,
                          "residuals_CLOSED_minus_ATOM_LOCAL": dict(batch.residuals)})
        residuals = {stage: {key: counts["CLOSED"][key] - counts["ATOM_LOCAL"][key]
                             for key in counts["CLOSED"]} for stage, counts in totals.items()}
        for pins in (gates["qualification_source_pins"], gates["separation_source_pins"]):
            for name, digest in pins.items():
                expected = gates["qualification_dependency_dispositions"].get(name, {}).get("current_sha256", digest)
                _require(_digest(attempt.read(ROOT / name)) == expected, "source_changed_during_preparation")
        if gates["separation_recovery"] is not None:
            from gpu import astra_stage2a_separation_replay as replay

            original = Path(gates["separation_artifacts_root"])
            _capture_recovery(attempt, replay, original, gates["separation_recovery"])
            _verify_replay_blobs(attempt, original, _json(attempt.read(attempt.path / "separation_report.json")))
        for name, info in binding["files"].items():
            _require(_digest(attempt.read(Path(model_dir) / name)) == info["sha256"], "model_file_changed_during_preparation")
        _require(_digest(tokenizer.backend_tokenizer.to_str().encode("utf-8")) == binding["backend_sha256"]
                 and _digest(tokenizer.chat_template.encode("utf-8")) == binding["chat_template_sha256"]
                 and tokenizer.eos_token_id == binding["eos_token_id"] and tokenizer.pad_token_id == binding["pad_token_id"]
                 and tokenizer.padding_side == "right", "loaded_tokenizer_changed_during_preparation")
        for name, digest in helper_pins.items():
            _require(_digest(attempt.read(ROOT / name)) == digest, "helper_changed_during_preparation")
        receipt = {"schema": SCHEMA, "status": "TOKENIZER_PREPARATION_RECORDED", "source_gates": gates,
                   "tokenizer_binding": binding, "packages": packages, "padding_policy": PADDING_POLICY,
                   "preparation_implementation_pins": helper_pins,
                   "count_basis": prepare.COUNT_BASIS, "upstream_status_preserved": prepare.STATUS,
                   "records": 512, "conditional_paired_batches": 512, "executed_updates": 0,
                   "tape_fingerprint": prepared.tape_fingerprint,
                   "accounting_by_stage": {stage: {arm: dict(counts) for arm, counts in arms.items()}
                                            for stage, arms in totals.items()},
                   "residuals_CLOSED_minus_ATOM_LOCAL": residuals, "equal_total_compute_claimed": False,
                   "native_execution_authorized": False, "scientific_claims": False,
                   "files": dict(attempt.files), "bytes_read": attempt.read_bytes,
                   "artifact_bytes_before_receipt": attempt.written_bytes,
                   "limits": ["Evaluator-only; not actor/parent data.", "No full qualification replay or new qualification meaning.",
                              "Main owns native entrypoint, runtime/weight/adapter attestations and GPU gates."]}
        attempt.json("receipt.json", receipt)
        return TokenizerReceipt(attempt.path, attempt.files["receipt.json"]["sha256"], prepared)
    except Exception as error:
        raw = _encode({"schema": SCHEMA, "status": "ERROR", "error_type": type(error).__name__,
                       "error": str(error)[:4096], "native_execution_authorized": False})
        with (attempt.path / "failure.json").open("xb") as stream:
            stream.write(raw)
        raise
    finally:
        attempt.freeze()
