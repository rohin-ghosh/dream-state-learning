"""CPU-only source derivation for the separately allocated Node5 grid pair."""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


SOURCE_MANIFEST_SHA = '40f0ff7884492041df7a953045dc1f1fccf09220188de90acbe207b6de41fe56'
PINS = {
    'organism_v6/orch_r109_grid.py': '1cdd5dba8ec27a54285127b976a808984e29566f9cc1d3b2d20ffd00245b7146',
    'gpu/orch_r109_grid_run.py': '1199d9a6a68755c40225c55b4221e5e897016e3a6630ed0c5ce6c55076cc6c11',
    'gpu/orch_r109_grid_broker.py': '23d6c95699f0416b4b87416846f30ce694b0b353c1034ef26f24cbebe29d036a',
    'tests/test_orch_r109_grid.py': '1624ddddbc3c3d96f5dec5b2fb5ddcb6a2c76d5d642201769aa47dbcff0e7e2b',
}
OLD_ROOT = '/localhome/local-rohing/orch_r109_grid_20260915_attempt1'
LEASE_END = datetime(2026, 9, 17, 4, 4, tzinfo=timezone.utc).timestamp()
HARD_END = datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc).timestamp()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def native_root(index):
    require(type(index) is int and index in (6, 7), 'node5_allocated_pair_only')
    return f'/localhome/local-rohing/orch_r109_grid_node5_{index}_20260915_attempt1'


def render(snapshot, index, gpu_uuid, host_sha256):
    """Return derived bytes; identity inputs must come from trusted native discovery."""
    root = native_root(index)
    require(isinstance(gpu_uuid, str) and re.fullmatch(
        r'GPU-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', gpu_uuid), 'native_uuid_required')
    require(isinstance(host_sha256, str) and re.fullmatch(r'[0-9a-f]{64}', host_sha256),
        'native_host_identity_required')
    require(HARD_END <= LEASE_END - 6*3600, 'lease_margin')
    source = {}
    for name, expected in PINS.items():
        raw = (Path(snapshot)/name).read_bytes()
        require(sha(raw) == expected, 'immutable_source_pin:'+name)
        source[name] = raw.decode()
    name = 'organism_v6/orch_r109_grid.py'
    lines = source[name].splitlines(keepends=True)
    assignments = [node for node in ast.parse(source[name]).body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'LANES' for target in node.targets)]
    require(len(assignments) == 1, 'one_lane_registry')
    assignment = assignments[0]
    order = ['segment', 'hundred_segments', 'episode']
    allocation = dict(index=index, uuid=gpu_uuid, host_sha256=host_sha256,
        lease_end=LEASE_END, style='supportive' if index == 6 else 'critical',
        order=order if index == 6 else list(reversed(order)))
    lines[assignment.lineno-1:assignment.end_lineno] = [f'LANES = {repr({"ovx3": allocation})}\n']
    source[name] = ''.join(lines)
    for name in ('gpu/orch_r109_grid_run.py', 'gpu/orch_r109_grid_broker.py'):
        require(source[name].count(OLD_ROOT) == 1, 'one_root_binding')
        source[name] = source[name].replace(OLD_ROOT, root)
    name = 'tests/test_orch_r109_grid.py'
    source[name] = source[name].replace("'ovx'", "'ovx3'")
    result = {name: text.encode() for name, text in source.items()}
    for name, raw in result.items():
        compile(raw, name, 'exec')
    return result, dict(schema='R110_GRID_NODE5_SOURCE_DERIVATION_V1', native_root=root,
        lane='ovx3', allocation=allocation, original_source_manifest_sha256=SOURCE_MANIFEST_SHA,
        parent_source_pins=PINS, derived_source_pins={name:sha(raw) for name, raw in result.items()},
        wrapper='gpu/ovx3_ssh.sh', native_per_lane=1858, parent_per_lane=298,
        pair_native_cap=3716, pair_parent_cap=596, pair_gpu_hours_cap=16,
        bounds_accounting='Node5 pair only; no refund or reset of original two lanes',
        native_end_utc='2026-09-15T16:57:00Z', hard_end_utc='2026-09-15T17:02:00Z',
        weights='FROZEN_BASE_NO_ADAPTER', ready_for_GPU=False,
        pending=['native CPU tests including tokenizer/base', 'portable bundle provenance',
            'prior-owner/no-refill evidence', 'dated Builder preGPU receipt',
            'fresh privileged scoped GPU admission'],
        interpretation='Additional descriptive style/cadence lives on identical frozen geometries; '
            'not new independent held tasks or evidence of weight learning')


def materialize(snapshot, output, index, gpu_uuid, host_sha256):
    """Build a new source-only directory, never alter an existing or live root."""
    snapshot = Path(snapshot)
    output = Path(output)
    require(not output.exists(), 'new_output_only')
    manifest_raw = (snapshot/'SOURCE_SHA256.json').read_bytes()
    require(sha(manifest_raw) == SOURCE_MANIFEST_SHA, 'exact_parent_manifest')
    manifest = json.loads(manifest_raw)
    derived, document = render(snapshot, index, gpu_uuid, host_sha256)
    inputs = {}
    for name, expected in manifest.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'safe_source_path')
        path = snapshot/relative
        require(not path.is_symlink(), 'regular_source_only')
        raw = path.read_bytes()
        require(sha(raw) == expected, 'parent_source_drift:'+name)
        inputs[name] = derived.get(name, raw)
    require(set(derived) <= set(inputs), 'derived_files_in_parent_manifest')
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in inputs.items():
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    for name, value in (
        ('SOURCE_SHA256.json', {name:sha(raw) for name, raw in inputs.items()}),
        ('NODE5_DERIVATION.json', document),
    ):
        with (output/name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
    return document
