"""Freeze four new payloads without modifying or dispatching existing copies."""

import json
from pathlib import Path
import tarfile

from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import (
    ARMS, OWN, BASE_SOURCE_SHA, confinement, retain_bridge,
)
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write, digest, require


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def build():
    baseline_manifest = ROOT / 'R184_EXPLICIT_SOURCE.json'
    require(digest(baseline_manifest.read_bytes()) == BASE_SOURCE_SHA, 'frozen_explicit_manifest')
    manifest = json.loads(baseline_manifest.read_bytes())
    baseline = {}
    for name, expected in manifest['source_pins'].items():
        raw = (ROOT / 'r184_explicit_source' / name).read_bytes()
        require(digest(raw) == expected, 'frozen_baseline:' + name)
        baseline[name] = raw
    files = dict(baseline)
    native_name = 'gpu/orch_r125_continual_native.py'
    driver_name = 'gpu/orch_r184_think_act_learn.py'
    canonical = {name: (REPO / name).read_bytes() for name in (native_name, driver_name,
        'tests/test_orch_r125_continual_native.py', 'tests/test_orch_r184_think_act_learn.py')}
    native = canonical[native_name].decode()
    loaded = native.index("journal.record('LOADED'")
    require(native.index("if plan.get('think_act_learn') is not None:", loaded)
        < native.index('for readout_cycle in range(completed_sleeps+1):', loaded),
        'canonical_dispatch_before_historical_backfill')
    files.update(canonical)
    files[driver_name] = retain_bridge(canonical[driver_name], baseline[driver_name])
    for name in ('r186_copy.py', 'test_r186_copy.py'):
        files[OWN + '/' + name] = (ROOT / name).read_bytes()
    protected = {name: value for name, value in manifest['source_pins'].items()
        if name not in (native_name, driver_name, 'gpu/r184_node2_confinement.py',
            'tests/test_orch_r184_think_act_learn.py')}
    outputs = {}
    for label in ARMS:
        changed = dict(files)
        changed['gpu/r184_node2_confinement.py'] = confinement(baseline['gpu/r184_node2_confinement.py'], label)
        require(all(digest(changed[name]) == expected for name, expected in protected.items()),
            'all_noncanonical_runtime_dependencies_preserved')
        source = ROOT / ('r186_' + label + '_source')
        require(not source.exists(), 'immutable_new_source')
        for name, raw in changed.items():
            write(source / name, raw)
        pinfile = ROOT / ('R186_' + label.upper() + '_SOURCE.json')
        write(pinfile, dict(schema='R186_SAVED41_SOURCE_V1', label=label,
            baseline_manifest_sha256=BASE_SOURCE_SHA, source_pins={name: digest(raw) for name, raw in changed.items()},
            protected_pins=protected, canonical_pins={name: digest(raw) for name, raw in canonical.items()},
            frozen_bridge_sha256=digest(baseline['gpu/r184_cpu_bridge.py']),
            exact_frozen_cpu_adapter=True, complete_episode_encoder_integrated=False))
        archive_path = ROOT / ('R186_' + label.upper() + '.tar.gz')
        with tarfile.open(archive_path, 'x:gz') as archive:
            archive.add(source, arcname='source')
            archive.add(pinfile, arcname='SOURCE.json')
            archive.add(ROOT / 'r186_receive.py', arcname='receive.py')
            archive.add(ROOT / 'R186_SCOPE.md', arcname='SCOPE.md')
        outputs[label] = dict(source_root=str(source), manifest= str(pinfile),
            manifest_sha256=digest(pinfile.read_bytes()), archive=str(archive_path),
            archive_sha256=digest(archive_path.read_bytes()), source_file_count=len(changed))
    print(json.dumps(write(ROOT / 'R186_BUILD.json', outputs), sort_keys=True))


if __name__ == '__main__':
    build()
