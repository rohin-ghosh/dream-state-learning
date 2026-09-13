"""Build exact prospective specifications; no native execution or launch."""
import hashlib
import json
from pathlib import Path
import shutil


REPO = Path("/data/home/rohing/dream-state")
REMOTE_SOURCE = "/localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1"
REMOTE_PROTOCOL = "/tmp/ASTRA_L2_LR_COMPARISON_PROTOCOL_2026-09-13.md"
EXPECTED_RUNTIME = "dce8cd88b82bd51ec4f12e482ce70dc220453cb85dcaeb758206c7b5200a4277"
LOCAL_SOURCE = Path("/tmp/astra_l2_lr_source_20260913_attempt1")
LOCAL_SPECS = Path("/tmp/astra_l2_lr_specs_20260913_attempt1")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


original = json.loads(Path("/tmp/astra_l2_public_record_spec_20260913_attempt1.json").read_text())
assert digest(REPO / "gpu/astra_l2_public_record_dev.py") == EXPECTED_RUNTIME
assert not LOCAL_SOURCE.exists() and not LOCAL_SPECS.exists()
LOCAL_SOURCE.mkdir()
LOCAL_SPECS.mkdir()
source_files = {}
for name, old_pin in original["source_files"].items():
    source = REPO / name
    checksum = digest(source)
    assert name == "gpu/astra_l2_public_record_dev.py" or checksum == old_pin
    target = LOCAL_SOURCE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    source_files[name] = checksum
devices = {}
for line in Path("/tmp/astra_l2_lr_gpu_inventory_20260913.txt").read_text().splitlines():
    index, gpu_uuid, memory = [field.strip() for field in line.split(",")]
    assert index not in devices and gpu_uuid.startswith("GPU-")
    devices[int(index)] = gpu_uuid
assert set(devices) == {0, 1, 2, 4, 5, 6} and len(set(devices.values())) == 6
protocol_pin = digest(REPO / "research_notes/astra_memos/ASTRA_L2_LR_COMPARISON_PROTOCOL_2026-09-13.md")
specs = []
for learner_seed, indices in enumerate(((0, 1), (2, 4), (5, 6))):
    for label, learning_rate, gpu_index in zip(("low", "high"), (3e-5, 1e-4), indices):
        spec = dict(original, source=REMOTE_SOURCE, source_files=source_files, learner_seed=learner_seed,
                    learning_rate=learning_rate, gpu_index=gpu_index, gpu_uuid=devices[gpu_index],
                    protocol=dict(path=REMOTE_PROTOCOL, sha256=protocol_pin))
        name = f"seed{learner_seed}_{label}"
        path = LOCAL_SPECS / f"{name}.json"
        with path.open("x") as stream:
            stream.write(json.dumps(spec, sort_keys=True, allow_nan=False) + "\n")
        specs.append(dict(name=name, spec_path=str(path), spec_sha256=digest(path),
                          gpu_index=gpu_index, gpu_uuid=devices[gpu_index], learner_seed=learner_seed,
                          learning_rate=learning_rate,
                          root=f"/localhome/local-rohing/astra_diagnostics/l2_lr_{name}_20260913_attempt1"))
with (LOCAL_SPECS / "roster.json").open("x") as stream:
    stream.write(json.dumps(dict(source=REMOTE_SOURCE, source_files=source_files, protocol_sha256=protocol_pin,
                                specs=specs), sort_keys=True) + "\n")
print(json.dumps(dict(source=str(LOCAL_SOURCE), specs=str(LOCAL_SPECS), roots=len(specs),
                      roster_sha256=digest(LOCAL_SPECS / "roster.json")), sort_keys=True))
