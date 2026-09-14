"""CPU-only retained-byte recovery of the aggregate-capacity ERROR, not native work.

Non-material resource repair: no constructors, reselection, changed anchors or
source authentication. Uses the producer's snapshot/pin and exclusive-write
helpers; execution is detached into a readonly source snapshot under RLIMIT_AS.
The only permitted production-source difference is the exact two-line 512 MiB
to 2 GiB separation capacity repair. Original evidence is never modified.
"""

import argparse
from dataclasses import asdict, fields
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from gpu import astra_stage2a_cpu_separation as snapshot_helper


MEMORY_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
MAX_BLOB_BYTES = 32 * 1024 * 1024
MAX_ALLOCATION_BYTES = 64 * 1024 * 1024
MAX_INDEX_BYTES = 8 * 1024 * 1024
MAX_INDEX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_DECODE_NODES = 100000
SEPARATION_PATH = "organism_v6/composition_birth_stage2a_separation.py"
SEPARATION_TEST_PATH = "tests/test_composition_birth_stage2a_separation.py"
REPLAY_PATH = "gpu/astra_stage2a_separation_replay.py"
REPLAY_TEST_PATH = "tests/test_astra_stage2a_separation_replay.py"
ORIGINAL_SEPARATION_SHA256 = "78371c3b991305f53631c09c4842b84f36b3a23731a41250ab2b5908b45c04a4"
KIND = "CPU_RETAINED_SEPARATION_CAPACITY_RECOVERY_NOT_NATIVE_READINESS"
INDEX_NAMES = ("allocation.json",) + tuple(f"birth_p{index:02d}.json" for index in range(32)) + tuple(
    f"intervention_{skill}_k{index}.json" for skill in ("seek", "prospect", "check", "continue")
    for index in range(8)) + tuple(f"chain_h{index:02d}.json" for index in range(16))
CONTROL_NAMES = ("SNAPSHOT.json", "manifest.json", "report.json")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def valid_digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def read_regular(path, limit):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, "bounded_regular_file_required")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                and len(raw) == before.st_size, "file_changed_during_read")
    return raw


def unique_object(entries):
    result = {}
    for key, value in entries:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def read_json(path):
    raw = read_regular(path, MAX_INDEX_BYTES)
    value = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda value: require(False, "nonfinite_json_forbidden"))
    return raw, value


def relative_path(root, relative):
    require(type(relative) is str and relative and not Path(relative).is_absolute()
            and all(part not in (".", "..") for part in relative.split("/")), "safe_relative_path_required")
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(), "symlink_or_path_escape")
    return path


def source_pins():
    pins = snapshot_helper.source_pins()
    for relative in (REPLAY_PATH, REPLAY_TEST_PATH):
        pins[relative] = digest(read_regular(ROOT / relative, MAX_INDEX_BYTES))
    return dict(sorted(pins.items()))


def capacity_repair(original):
    require(digest(original) == ORIGINAL_SEPARATION_SHA256, "unreviewed_original_separation_source")
    replacements = ((b'"total_bytes": 512 * 1024 * 1024,', b'"total_bytes": 2 * 1024 * 1024 * 1024,'),
                    (b"aggregate supplied bytes <=512 MiB (counting", b"aggregate supplied bytes <=2 GiB (counting"))
    for old, new in replacements:
        require(original.count(old) == 1, "capacity_repair_context_mismatch")
        original = original.replace(old, new)
    return original


def capture_recovery(original, current_pins):
    controls, input_pins = {}, {}
    for name in CONTROL_NAMES:
        raw, controls[name] = read_json(relative_path(original, name))
        input_pins[name] = {"sha256": digest(raw), "length": len(raw)}
    report, manifest = controls["report.json"], controls["manifest.json"]
    require(report.get("status") == "ERROR" and report.get("error") == "aggregate_byte_bound_exceeded"
            and not any(name in report for name in ("counts", "core_collisions", "signature_collisions")),
            "original_capacity_error_without_join_required")
    require(manifest.get("kind") == "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS"
            and report.get("kind") == manifest["kind"] and report.get("native_authorized") is False
            and report.get("scientific_claims") is False, "original_source_only_attempt_required")
    for name, count in (("expected_birth_records", 512), ("expected_intervention_members", 64),
                        ("expected_chain_members", 32), ("expected_chain_boundaries", 240)):
        require(type(manifest.get(name)) is int and manifest[name] == count, "original_population_manifest_mismatch")
    pins = controls["SNAPSHOT.json"]["source_pins"]
    require(type(pins) is dict and pins == manifest["source_pins"] == report["source_pins"],
            "original_source_pin_manifest_mismatch")
    require(set(current_pins) == set(pins) | {REPLAY_PATH, REPLAY_TEST_PATH}, "source_pin_set_changed")
    for relative, expected in pins.items():
        require(valid_digest(expected), "invalid_original_source_pin")
        raw = read_regular(relative_path(original / "source", relative), MAX_INDEX_BYTES)
        require(digest(raw) == expected, "original_source_snapshot_changed: " + relative)
        if relative == SEPARATION_PATH:
            require(digest(capacity_repair(raw)) == current_pins[relative], "noncapacity_separation_change")
        elif relative != SEPARATION_TEST_PATH:
            require(current_pins[relative] == expected, "source_pin_changed: " + relative)
    require(SEPARATION_PATH in pins, "original_separation_pin_required")
    observed = {path.name for pattern in ("birth_*.json", "intervention_*.json", "chain_*.json")
                for path in original.glob(pattern)} | {"allocation.json"}
    require(observed == set(INDEX_NAMES), "exact_retained_index_set_required")
    total = 0
    for name in INDEX_NAMES:
        raw = read_regular(relative_path(original, name), MAX_INDEX_BYTES)
        total += len(raw)
        require(total <= MAX_INDEX_TOTAL_BYTES, "aggregate_index_byte_bound_exceeded")
        input_pins[name] = {"sha256": digest(raw), "length": len(raw)}
    return {"kind": KIND, "original_root": str(original), "original_files": input_pins,
            "original_source_pins": pins, "source_pins": current_pins,
            "repair": {"classification": "NON_MATERIAL_RESOURCE_REPAIR", "aggregate_before": 512 * 1024 * 1024,
                       "aggregate_after": MEMORY_LIMIT_BYTES, "per_blob_bytes": MAX_BLOB_BYTES,
                       "original_separation_sha256": pins[SEPARATION_PATH],
                       "repaired_separation_sha256": current_pins[SEPARATION_PATH]},
            "address_space_limit_bytes": MEMORY_LIMIT_BYTES, "constructors_rerun": False,
            "source_authenticated": False, "native_authorized": False, "cpu_only": True}


def type_registry():
    from organism_v6.composition_birth_stage2a_core_inputs import BirthCoreInputs
    from organism_v6.composition_birth_stage2a_held_core_inputs import InterventionCoreInputs
    from organism_v6.composition_birth_stage2a_chain_core_inputs import ChainCoreInputs, ChainCoreBoundary
    return {cls.__module__ + "." + cls.__qualname__: cls
            for cls in (BirthCoreInputs, InterventionCoreInputs, ChainCoreInputs, ChainCoreBoundary)}


class RetainedDecoder:
    """Decode only the four inert core-input dataclasses, never arbitrary imports."""

    def __init__(self, original):
        self.original = original
        self.registry = type_registry()
        self.cache = {}
        self.lengths = {}
        self.limits = {}
        self.reference_bytes = 0
        self.unique_bytes = 0
        self.nodes = 0

    def blob(self, reference, *, max_bytes=MAX_BLOB_BYTES):
        require(type(reference) is dict and set(reference) == {"bytes_sha256", "length"}, "exact_blob_reference_required")
        checksum, length = reference["bytes_sha256"], reference["length"]
        require(max_bytes in (MAX_BLOB_BYTES, MAX_ALLOCATION_BYTES), "declared_blob_capacity_required")
        require(valid_digest(checksum) and type(length) is int and 0 < length <= max_bytes,
                "bounded_blob_digest_and_length_required")
        self.reference_bytes += length
        require(self.reference_bytes <= MEMORY_LIMIT_BYTES, "retained_reference_byte_bound_exceeded")
        if checksum not in self.cache:
            raw = read_regular(relative_path(self.original, "artifacts/" + checksum), max_bytes)
            require(len(raw) == length and digest(raw) == checksum, "retained_blob_hash_or_length_mismatch")
            self.cache[checksum] = raw
            self.lengths[checksum] = length
            self.limits[checksum] = max_bytes
            self.unique_bytes += length
        require(self.lengths[checksum] == length, "duplicate_blob_length_mismatch")
        return self.cache[checksum]

    def decode(self, value, depth=0):
        self.nodes += 1
        require(depth <= 12 and self.nodes <= MAX_DECODE_NODES, "retained_decode_bound_exceeded")
        if type(value) in (str, int) or value is None:
            return value
        require(type(value) is dict, "retained_tagged_value_required")
        if set(value) == {"bytes_sha256", "length"}:
            return self.blob(value)
        if set(value) == {"tuple"}:
            require(type(value["tuple"]) is list and len(value["tuple"]) <= 58, "bounded_retained_tuple_required")
            return tuple(self.decode(item, depth + 1) for item in value["tuple"])
        require(set(value) == {"dataclass", "fields"} and type(value["dataclass"]) is str
                and value["dataclass"] in self.registry, "explicit_core_input_dataclass_required")
        cls, entries = self.registry[value["dataclass"]], value["fields"]
        names = [field.name for field in fields(cls)]
        require(type(entries) is list and len(entries) == len(names)
                and all(type(entry) is list and len(entry) == 2 and entry[0] == name
                        for entry, name in zip(entries, names)), "exact_retained_dataclass_fields_required")
        decoded = {name: self.decode(item, depth + 1) for name, item in entries}
        for name, item in decoded.items():
            if name.endswith("_bytes") or name == "checker_payload":
                require(type(item) is bytes, "retained_bytes_field_required")
            elif name in ("decision_index", "semantic_route_depth"):
                require(type(item) is int and 0 <= item <= 29, "retained_integer_field_required")
            elif name == "boundaries":
                boundary_type = self.registry["organism_v6.composition_birth_stage2a_chain_core_inputs.ChainCoreBoundary"]
                require(type(item) is tuple and all(type(boundary) is boundary_type for boundary in item),
                        "retained_chain_boundaries_required")
            else:
                require(type(item) is str and (not name.endswith("_sha256") or valid_digest(item)),
                        "retained_string_field_required")
        return cls(**decoded)

    def verify_unchanged(self):
        for checksum, length in self.lengths.items():
            raw = read_regular(relative_path(self.original, "artifacts/" + checksum), self.limits[checksum])
            require(len(raw) == length and digest(raw) == checksum, "retained_blob_changed_during_replay")


def load_inputs(original, recovery):
    decoder = RetainedDecoder(original)
    birth, intervention, chain = {}, [], []
    for name in INDEX_NAMES:
        raw, packed = read_json(relative_path(original, name))
        require({"sha256": digest(raw), "length": len(raw)} == recovery["original_files"][name],
                "retained_index_pin_mismatch")
        if name == "allocation.json":
            decoder.blob(packed, max_bytes=MAX_ALLOCATION_BYTES)
        elif name.startswith("birth_"):
            require(type(packed) is dict and set(packed) == {"shared", "records"}
                    and type(packed["records"]) is list and len(packed["records"]) == 16,
                    "exact_birth_index_shape_required")
            decoder.blob(packed["shared"])
            for encoded in packed["records"]:
                record = decoder.decode(encoded)
                require(type(record) is decoder.registry["organism_v6.composition_birth_stage2a_core_inputs.BirthCoreInputs"],
                        "birth_index_type_mismatch")
                identity = (record.unit_id, record.arm)
                require(record.unit_id.split("/")[0] == name[6:-5] and identity not in birth,
                        "birth_index_identity_mismatch")
                birth[identity] = record
        elif name.startswith("intervention_"):
            require(type(packed) is list and len(packed) == 2, "exact_intervention_index_shape_required")
            for encoded in packed:
                record = decoder.decode(encoded)
                require(type(record) is decoder.registry["organism_v6.composition_birth_stage2a_held_core_inputs.InterventionCoreInputs"]
                        and record.world == name[13:-5], "intervention_index_identity_mismatch")
                intervention.append(record)
        else:
            record = decoder.decode(packed)
            require(type(record) is decoder.registry["organism_v6.composition_birth_stage2a_chain_core_inputs.ChainCoreInputs"]
                    and record.world == name[6:-5], "chain_index_identity_mismatch")
            chain.append(record)
    return birth, tuple(intervention), tuple(chain), decoder


def bootstrap(options):
    original, out = Path(options.original).resolve(), Path(options.out).resolve()
    require(not out.is_relative_to(original) and not original.is_relative_to(out), "exclusive_new_output_outside_original_required")
    pins = source_pins()
    recovery = capture_recovery(original, pins)
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source"
    snapshot.mkdir()
    for relative, expected in pins.items():
        raw = read_regular(relative_path(ROOT, relative), MAX_INDEX_BYTES)
        require(digest(raw) == expected, "source_changed_before_snapshot")
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        snapshot_helper.write_once(target, raw)
        target.chmod(0o444)
    for name, value in (("SNAPSHOT.json", {"source_pins": pins, "created_unix": time.time()}), ("RECOVERY.json", recovery)):
        target = out / name
        snapshot_helper.write_once(target, snapshot_helper.encode(value))
        target.chmod(0o444)
    for directory in sorted((path for path in snapshot.rglob("*") if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    snapshot.chmod(0o555)
    return subprocess.run([sys.executable, "-B", str(snapshot / REPLAY_PATH), "--original", str(original),
                           "--out", str(out), "--snapshot-manifest", str(out / "SNAPSHOT.json")],
                          cwd=snapshot, check=False,
                          env=dict(os.environ, PYTHONPATH=str(snapshot), PYTHONDONTWRITEBYTECODE="1",
                                   CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")).returncode


def execute(options):
    out, original = Path(options.out).resolve(), Path(options.original).resolve()
    require(ROOT == out / "source" and Path(options.snapshot_manifest).resolve() == out / "SNAPSHOT.json",
            "retained_snapshot_execution_required")
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    started = time.time()
    require(not (out / "report.json").exists() and not (out / "report.sha256").exists(), "exclusive_new_replay_required")
    snapshot_helper.write_once(out / "REPLAY_STARTED.json", snapshot_helper.encode({"started_unix": started}))
    report = {"kind": KIND, "cpu_only": True, "native_authorized": False, "source_authenticated": False,
              "constructors_rerun": False, "scientific_claims": False, "address_space_limit_bytes": MEMORY_LIMIT_BYTES}
    try:
        snapshot_raw, manifest = read_json(out / "SNAPSHOT.json")
        recovery_raw, recovery = read_json(out / "RECOVERY.json")
        report.update(snapshot_manifest_sha256=digest(snapshot_raw), recovery_manifest_sha256=digest(recovery_raw),
                      original_files=recovery["original_files"], source_pins=manifest["source_pins"])
        require(source_pins() == manifest["source_pins"], "source_pin_mismatch_before_import")
        require(capture_recovery(original, manifest["source_pins"]) == recovery, "recovery_evidence_changed")
        from organism_v6 import composition_birth_stage2a_separation as separation
        birth, intervention, chain, decoder = load_inputs(original, recovery)
        print(json.dumps({"stage": "retained_inputs_verified", "birth_records": len(birth),
                          "intervention_members": len(intervention), "chain_worlds": len(chain),
                          "unique_bytes": decoder.unique_bytes, "elapsed_seconds": time.time() - started}),
              flush=True)
        joined = separation.check_held_birth_separation(birth_inputs=birth, intervention_inputs=intervention,
                                                       chain_core_inputs=chain)
        require(joined.counts["chain_boundaries"] == 240, "source_chain_boundary_count_changed")
        decoder.verify_unchanged()
        require(source_pins() == manifest["source_pins"] and capture_recovery(original, manifest["source_pins"]) == recovery,
                "source_or_recovery_evidence_changed_during_replay")
        require(read_regular(out / "SNAPSHOT.json", MAX_INDEX_BYTES) == snapshot_raw
                and read_regular(out / "RECOVERY.json", MAX_INDEX_BYTES) == recovery_raw,
                "replay_manifest_changed_during_execution")
        report.update(status="SEPARATED" if joined.separated else "COLLISION", counts=dict(joined.counts),
                      core_collisions=[asdict(item) for item in joined.core_collisions],
                      signature_collisions=[asdict(item) for item in joined.signature_collisions],
                      retained_reference_bytes=decoder.reference_bytes, retained_unique_bytes=decoder.unique_bytes,
                      retained_unique_blobs=len(decoder.cache), retained_blob_lengths=decoder.lengths)
    except Exception as error:
        report.update(status="ERROR", error=str(error), traceback=traceback.format_exc())
    report.update(elapsed_seconds=time.time() - started, finished_unix=time.time(),
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    raw = snapshot_helper.encode(report)
    snapshot_helper.write_once(out / "report.json", raw)
    snapshot_helper.write_once(out / "report.sha256", (digest(raw) + "  report.json\n").encode("ascii"))
    print(json.dumps({"status": report["status"], "report_sha256": digest(raw), "out": str(out)}), flush=True)
    return 0 if report["status"] == "SEPARATED" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--snapshot-manifest")
    options = parser.parse_args()
    return execute(options) if options.snapshot_manifest else bootstrap(options)


if __name__ == "__main__":
    raise SystemExit(main())
