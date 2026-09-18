"""Prepare exact saved-state recovery without launching or signalling anything."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def copy_bound(source, destination):
    before = sha(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert sha(source) == sha(destination) == before, 'stable_before_copy_after'
    return dict(path=str(destination), sha256=before, bytes=destination.stat().st_size)


def prepare(payload):
    assert os.getuid() == 1352
    root = Path('/localhome/local-rohing/orch_r233_ovx4_recovery_20260918') / payload['attempt']
    root.mkdir(mode=0o700, exist_ok=False)
    previous_base = Path('/localhome/local-rohing/orch_r226_base_schedule_20260918/r232_epoch3')
    old_config = json.loads((previous_base / 'EPOCH.json').read_bytes())
    roots = {'shared2': Path('/localhome/local-rohing/orch_r226_shared_caption_20260918/attempt2'),
        'shared3': Path('/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918'),
        'base': Path(old_config['source_root']).parent}
    receipts = []
    for role, old_root in roots.items():
        output = root / role
        output.mkdir(mode=0o700)
        old_source = old_root / 'source'
        files = (old_config['frozen_source_files'] if role == 'base'
            else json.loads((old_root / 'SOURCE_MANIFEST.json').read_bytes())['files'])
        for relative, expected in files.items():
            assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
            assert sha(old_source / relative) == expected, 'unchanged_frozen_source:' + relative
            copy_bound(old_source / relative, output / 'source' / relative)
        new_files = {}
        for relative, content in payload['new_files'].items():
            destination = output / 'source' / relative
            assert not destination.exists() and not Path(relative).is_absolute() and '..' not in Path(relative).parts
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
            new_files[relative] = sha(destination)
        manifest = dict(files, **new_files)
        save(output / 'SOURCE_MANIFEST.json', manifest)
        if role.startswith('shared'):
            sessions = {}
            registry = json.loads((old_root / 'NATIVE_REGISTRY.json').read_bytes())
            for item in registry['rows']:
                name = item['session_id']
                source = old_root / 'sessions' / name / 'SESSION_STATE.private.json'
                state = json.loads(source.read_bytes())
                assert state['phase'] == 'COMPLETE' and state['session_binding'] == item
                sessions[name] = copy_bound(source, output / 'preserved' / name / 'SESSION_STATE.private.json')
            registry_ref = copy_bound(old_root / 'NATIVE_REGISTRY.json', output / 'NATIVE_REGISTRY.json')
            config = dict(schema='R233_EXACT_SHARED_RECOVERY_V1', physical=int(role[-1]),
                deadline_unix=payload['deadline_unix'], allocation=payload['allocation'],
                service_root=str(old_root), recovery_root=str(output), source_root=str(output / 'source'),
                source_files=manifest, sessions=sessions, registry=registry_ref)
            save(output / 'CONFIG.private.json', config)
            receipts.append(dict(role=role, source_files=len(manifest), sessions=len(sessions),
                states=[dict(session_id=name, sha256=reference['sha256']) for name, reference in sessions.items()],
                source_manifest_sha256=sha(output / 'SOURCE_MANIFEST.json')))
        else:
            original = Path(old_config['original_root'])
            inputs = {'PRESERVED_CONTROLLER.private.json': original / 'player/private/state.json',
                'PRESERVED_SCORER.private.json': original / 'scorer/SESSION_STATE.private.json',
                'PRESERVED_LAUNCH_PLAN.json': original / 'LAUNCH_PLAN.json',
                'PRESERVED_CURRENT.json': Path(old_config['phase_root']) / 'CURRENT.json'}
            bound = {name: copy_bound(source, output / name)['sha256'] for name, source in inputs.items()}
            state = json.loads((output / 'PRESERVED_CONTROLLER.private.json').read_bytes())
            scorer = json.loads((output / 'PRESERVED_SCORER.private.json').read_bytes())
            assert state['pending'] is None and scorer['phase'] == 'COMPLETE'
            assert set(scorer['seen']) == {event['source']['request_id'] for event in state['events']}
            config = dict(old_config, epoch='R233_FROZEN_BASE_RECOVERY_4',
                deadline_unix=payload['deadline_unix'], allocation=payload['allocation'],
                previous_root=str(previous_base), previous_exit_unix=1789739969,
                source_root=str(output / 'source'), input_files=bound, frozen_source_files=files,
                new_source_files={'source/' + name: value for name, value in new_files.items()},
                total_opportunities=state['binding']['plan']['opportunities'],
                authorizes='Current explicit scoped recovery; renew finite runtime only, not the lease or per-opportunity recipe')
            config.pop('archive_sha256', None)
            scorer_root = output / 'scorer'
            scorer_root.mkdir(mode=0o700)
            assets = (previous_base / 'scorer/assets').resolve()
            shutil.copytree(assets, scorer_root / 'assets', symlinks=False)
            for original_file in assets.rglob('*'):
                if original_file.is_file():
                    assert sha(original_file) == sha(scorer_root / 'assets' / original_file.relative_to(assets))
            save(output / 'EPOCH.json', config)
            receipts.append(dict(role=role, source_files=len(manifest), state=bound,
                ACT_attempts=len(state['events']), seen=len(scorer['seen']),
                opportunity=state['opportunity'], stage=state['stage'], total_generated_tokens=state['total_generated_tokens'],
                source_manifest_sha256=sha(output / 'SOURCE_MANIFEST.json'), no_history_reset=True))
    receipt = dict(unix=time.time(), status='PREPARED_NOT_DISPATCHED', roles=receipts,
        allocation=payload['allocation'], deadline_unix=payload['deadline_unix'],
        signals=[], GPU_work=False)
    save(root / 'PREPARED.json', receipt)
    return receipt
