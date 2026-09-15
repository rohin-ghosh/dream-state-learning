import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "gpu_artifacts_local/orch_rich_intensity_20260915_attempt3/FIRST_READY_CALLS.tar.gz"
SEED = "RICH-BLIND-SEMANTICS/20260915/fixed-first24/v1"


def add_file(path, text):
    if path.exists():
        if path.read_bytes() != text.encode():
            raise RuntimeError(f"Refusing to replace existing snapshot: {path.name}")
        return
    patch = "*** Begin Patch\n*** Add File: " + str(path.relative_to(ROOT)) + "\n"
    patch += "".join("+" + line + "\n" for line in text.splitlines())
    patch += "*** End Patch\n"
    subprocess.run(["apply_patch"], input=patch, text=True, cwd=ROOT, check=True, capture_output=True)


def schema(value):
    if isinstance(value, dict):
        return {key: schema(item) for key, item in value.items()}
    if isinstance(value, list):
        unique = {json.dumps(schema(item), sort_keys=True) for item in value}
        return {"array_count": len(value), "item_schemas": [json.loads(item) for item in sorted(unique)]}
    return type(value).__name__


def main():
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        names = [f"run/shard{shard}/CALL_{call:04d}.json" for shard in range(6) for call in range(1, 5)]
        members = {member.name: member for member in archive.getmembers()}
        if not all(name in members and members[name].isfile() for name in names):
            raise RuntimeError("Incomplete first-four-per-shard packet")
        names.sort(key=lambda name: hashlib.sha256((SEED + name).encode()).hexdigest())
        mapping = [{"opaque_id": f"R{index:02d}", "archive_member": name, "size": members[name].size}
                   for index, name in enumerate(names, 1)]
        add_file(OUTPUT / "source_mapping.json", json.dumps({"seed": SEED, "rows": mapping}, indent=2) + "\n")
        schemas = {}
        for entry in mapping:
            raw = archive.extractfile(entry["archive_member"]).read()
            decoded = raw.decode("utf-8")
            add_file(OUTPUT / "raw" / (entry["opaque_id"] + ".json"), decoded if decoded.endswith("\n") else decoded + "\n")
            entry["original_sha256"] = hashlib.sha256(raw).hexdigest()
            entry["snapshot_sha256"] = hashlib.sha256((OUTPUT / "raw" / (entry["opaque_id"] + ".json")).read_bytes()).hexdigest()
            schemas[entry["opaque_id"]] = schema(json.loads(raw))
        add_file(OUTPUT / "provenance.json", json.dumps({
            "archive": str(ARCHIVE.relative_to(ROOT)),
            "archive_sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
            "seed": SEED,
            "selection": "CALL_0001..CALL_0004 inclusive, each shard0..shard5; no other member content read",
            "raw_preservation": "Source bytes preserved in original archive; snapshots differ only by a final newline if absent",
            "rows": mapping,
        }, indent=2) + "\n")
        print(json.dumps(schemas, indent=2))


if __name__ == "__main__":
    main()
