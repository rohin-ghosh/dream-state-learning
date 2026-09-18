"""Snapshot and execute full source-only held/birth separation, never native work."""

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
MEMORY_LIMIT_BYTES = 1536 * 1024 * 1024


def encode(value):
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def write_once(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def source_pins():
    paths = [*ROOT.glob("organism_v6/composition_birth_stage2a*.py"),
             *ROOT.glob("tests/test_composition_birth_stage2a*.py"),
             *ROOT.glob("research_notes/analysis/*stage2a*.md"), Path(__file__).resolve()]
    paths.extend(path for path in (ROOT / "organism_v6/__init__.py", ROOT / "tests/__init__.py",
                                   ROOT / "gpu/__init__.py") if path.exists())
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def bootstrap(options):
    out = Path(options.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source"
    snapshot.mkdir()
    pins = source_pins()
    for relative, expected in pins.items():
        raw = (ROOT / relative).read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError("source_changed_before_snapshot")
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        write_once(target, raw)
        target.chmod(0o444)
    manifest = out / "SNAPSHOT.json"
    write_once(manifest, encode({"source_pins": pins, "created_unix": time.time()}))
    manifest.chmod(0o444)
    for directory in sorted((path for path in snapshot.rglob("*") if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    snapshot.chmod(0o555)
    return subprocess.run([sys.executable, "-B", str(snapshot / "gpu" / Path(__file__).name),
                           "--out", str(out), "--master", options.master, "--snapshot-manifest", str(manifest)],
                          cwd=snapshot, env=dict(os.environ, PYTHONPATH=str(snapshot), CUDA_VISIBLE_DEVICES="",
                                                PYTHONDONTWRITEBYTECODE="1"), check=False).returncode


def execute(options):
    started = time.time()
    out = Path(options.out).resolve()
    manifest_path = Path(options.snapshot_manifest).resolve()
    if manifest_path != out / "SNAPSHOT.json" or ROOT != out / "source":
        raise ValueError("snapshot_execution_required")
    pins = json.loads(manifest_path.read_bytes())["source_pins"]
    if source_pins() != pins:
        raise ValueError("source_pin_mismatch_before_import")
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    from organism_v6 import composition_birth_stage2a_allocation as allocation_api
    from organism_v6 import composition_birth_stage2a_chain_core_inputs as chain_api
    from organism_v6 import composition_birth_stage2a_core_inputs as birth_core_api
    from organism_v6 import composition_birth_stage2a_custody as custody_api
    from organism_v6 import composition_birth_stage2a_held as held_api
    from organism_v6 import composition_birth_stage2a_held_core_inputs as intervention_api
    from organism_v6 import composition_birth_stage2a_separation as separation_api
    from organism_v6 import composition_birth_stage2a_targets as targets_api

    master = options.master.encode("ascii")
    artifacts = out / "artifacts"
    artifacts.mkdir()

    def retain(value):
        if type(value) is bytes:
            digest = sha256(value).hexdigest()
            destination = artifacts / digest
            if not destination.exists():
                write_once(destination, value)
            elif destination.read_bytes() != value:
                raise ValueError("content_address_collision")
            return {"bytes_sha256": digest, "length": len(value)}
        if is_dataclass(value):
            return {"dataclass": type(value).__module__ + "." + type(value).__qualname__,
                    "fields": [[field.name, retain(getattr(value, field.name))] for field in fields(value)]}
        if isinstance(value, Mapping):
            return {"mapping": [[retain(key), retain(item)] for key, item in sorted(value.items())]}
        if type(value) is tuple:
            return {"tuple": [retain(item) for item in value]}
        if value is None or type(value) in (str, int, bool):
            return value
        raise ValueError("unsupported_artifact_type")

    write_once(out / "manifest.json", encode({"kind": "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS",
               "master_hex": master.hex(), "source_pins": pins, "started_unix": started,
               "expected_birth_records": 512, "expected_intervention_members": 64,
               "expected_chain_members": 32, "expected_chain_boundaries": 240,
               "address_space_limit_bytes": MEMORY_LIMIT_BYTES}))
    report = {"kind": "CPU_SOURCE_SEPARATION_NOT_NATIVE_READINESS", "native_authorized": False,
              "scientific_claims": False, "source_pins": pins}
    try:
        allocation = allocation_api.allocate_stage2a(master=master)
        allocation_api.verify_stage2a(allocation, master=master)
        write_once(out / "allocation.json", encode(retain(allocation.custody_bytes)))
        births, interventions, chains = {}, [], []
        for world, roles in allocation.role_tokens_by_world("birth_train").items():
            custody = custody_api.BirthSourceCustody(world=world, role_tokens=roles, display_master=master)
            packed = {"shared": retain(custody.shared_bytes), "records": []}
            for case in custody.cases:
                producer = birth_core_api.BirthCoreInputProducer(case=case, role_tokens=roles)
                for paired in targets_api.serialize_birth_case(case, role_tokens=roles):
                    for record in (paired.closed, paired.atom_local):
                        result = producer.build(record)
                        births[record.unit.unit_id, record.arm] = result
                        packed["records"].append(retain(result))
            write_once(out / ("birth_" + world + ".json"), encode(packed))
            print(json.dumps({"domain": "birth", "world": world, "records": len(births),
                              "elapsed_seconds": time.time() - started}), flush=True)
        for world, roles in allocation.role_tokens_by_world("dose_intervention").items():
            pair = held_api.build_intervention_pair(world=world, role_tokens=roles)
            packed = []
            for member in pair.members:
                result = intervention_api.build_intervention_core_inputs(member=member, role_tokens=roles)
                interventions.append(result)
                packed.append(retain(result))
            write_once(out / ("intervention_" + world + ".json"), encode(packed))
        for world, roles in allocation.role_tokens_by_world("dose_chain").items():
            chain = held_api.build_chain_world(world=world, role_tokens=roles)
            result = chain_api.build_chain_core_inputs(chain_world=chain, role_tokens=roles)
            chains.append(result)
            write_once(out / ("chain_" + world + ".json"), encode(retain(result)))
            print(json.dumps({"domain": "chain", "world": world, "worlds": len(chains),
                              "elapsed_seconds": time.time() - started}), flush=True)
        joined = separation_api.check_held_birth_separation(
            birth_inputs=births, intervention_inputs=interventions, chain_core_inputs=chains)
        if joined.counts["chain_boundaries"] != 240:
            raise ValueError("source_chain_boundary_count_changed")
        if source_pins() != pins:
            raise ValueError("source_changed_during_separation")
        report.update(status="SEPARATED" if joined.separated else "COLLISION", counts=dict(joined.counts),
                      core_collisions=retain(joined.core_collisions),
                      signature_collisions=retain(joined.signature_collisions))
    except Exception as error:
        report.update(status="ERROR", error=str(error), traceback=traceback.format_exc())
    report.update(elapsed_seconds=time.time() - started, finished_unix=time.time(),
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_once(out / "report.json", encode(report))
    print(json.dumps({key: value for key, value in report.items() if key != "source_pins"}), flush=True)
    return 0 if report["status"] == "SEPARATED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--master", required=True)
    parser.add_argument("--snapshot-manifest")
    options = parser.parse_args()
    raise SystemExit(execute(options) if options.snapshot_manifest else bootstrap(options))
