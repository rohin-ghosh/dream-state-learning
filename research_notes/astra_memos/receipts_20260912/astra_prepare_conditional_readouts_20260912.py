from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


source = Path.home() / 'astra_sources/90e181a4b0a02cfe655bc76ba480eac9166222b4'
sys.path.insert(0, str(source))
from organism_v6 import conditional_behavior_readout as readout

assert Path(readout.__file__).resolve() == source / 'organism_v6/conditional_behavior_readout.py'
assert hashlib.sha256(Path(readout.__file__).read_bytes()).hexdigest() == 'b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df'
parent = Path.home() / 'astra_diagnostics/astra_conditional_behavior_20260912_attempt2'
fit_root = parent / 'fits_root0_attempt1'
assert readout.base.digest(fit_root / 'plan.json') == '680e5239cd90c15b72de998d22c09cf5aa451d2e71111d99e940532e43510f11'
fit_plan = readout.base.read(fit_root / 'plan.json')
release = readout.base.read(fit_root / 'run/main_release.json')
assert release['full_release'] and release['controller_absent']
assert release['full_reservation_seconds'] == 464.397178
root = parent / 'readouts_root0_attempt1'
root.mkdir()
phases = []
reference = None
for state in ('OFF', 'AUTH', 'DERANGED'):
    adapter = None if state == 'OFF' else fit_root / 'run' / state / 'adapter'
    for phase in ('generate', 'score'):
        destination = root / f'{state}_{phase}'
        plan = readout.prepare(parent / 'material', destination, fit_plan['model'], fit_plan['model_files'],
                               state, phase, adapter, '0', datetime(2026, 9, 26, 3, 3, tzinfo=timezone.utc).timestamp(),
                               prospect_contrast=readout.PROSPECT_CONTRAST if phase == 'score' else None)
        assert len(plan['requests']) == (224 if phase == 'generate' else 64)
        if phase == 'score':
            assert sum(len(row['candidates']) for row in plan['requests']) == 192
        reference = reference or plan
        for field in ('model_files', 'source_hashes', 'material_inventory', 'device'):
            assert plan[field] == reference[field]
        phases.append(dict(state=state, phase=phase, root=str(destination), plan_sha256=readout.base.digest(destination / 'plan.json')))
        print(json.dumps(dict(status='NATIVE_CPU_PHASE_PREPARED', **phases[-1])), flush=True)
manifest = dict(source_root=str(source), phases=phases, source_hashes=reference['source_hashes'],
                model_files=reference['model_files'], material_inventory=reference['material_inventory'],
                assay_version=readout.ASSAY_VERSION, prior_fit_full_reservation_seconds=464.397178,
                controller_seconds=4500, external_collection_margin_seconds=300, total_ceiling_seconds=5400,
                prepared_utc=datetime.now(timezone.utc).isoformat(), generation_calls=672, candidate_forwards=576,
                source_commit='90e181a4b0a02cfe655bc76ba480eac9166222b4', device='0',
                status='NATIVE_CPU_PREPARED_NOT_LAUNCHED', preparation_script_sha256=readout.base.digest(__file__))
readout.base.write_json(root / 'manifest.json', manifest)
readout.base.write_json(root / 'manifest.sha256.json', dict(sha256=readout.base.digest(root / 'manifest.json')))
print(json.dumps(dict(status=manifest['status'], root=str(root), manifest_sha256=readout.base.digest(root / 'manifest.json'))), flush=True)
