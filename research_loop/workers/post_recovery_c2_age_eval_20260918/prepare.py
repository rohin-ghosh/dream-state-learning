"""Prepare a separate C2 age block from already verified immutable sources."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time


BASE = Path('/localhome/local-rohing')
ROOT = BASE / 'orch_post_recovery_c2_age_eval_20260918'
TEMPLATE = BASE / 'orch_post_recovery_age_20260918_attempt3/base'
READY = BASE / 'orch_post_recovery_c2_age_sources_20260918/READY.json'
ARMS = ('base', 'c2sleep51', 'c2sleep117')
SOURCE_MANIFEST = 'bcdd5adbcd03bc52e0ae20ca400cd6b328bc9d89aeb19a3f1d9fbae20b3e5c7b'
EPOCH = '216f34224e27a2ced6671026c482041c3e6024aecbabd105341a365d2935268a'
ALLOWED = {'COMMIT.json', 'adapter/README.md', 'adapter/adapter_config.json', 'adapter/adapter_model.safetensors'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)


def source_entry(ready, arm):
    label, sleep = {'c2sleep51': ('C2_SLEEP51', 51), 'c2sleep117': ('C2_NOW', 117)}[arm]
    entries = [entry for entry in ready['sources'] if entry['label'] == label and entry['absolute_sleep'] == sleep]
    if len(entries) != 1:
        raise ValueError('exact_predeclared_source_not_latest_mutable_checkpoint')
    entry = entries[0]
    relative = Path(entry['source_relative'])
    if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'sources':
        raise ValueError('source_inside_receiving_root')
    if set(entry['copy_files']) != ALLOWED:
        raise ValueError('adapter_only_no_optimizer_rng_or_context')
    return entry


def verify_source(ready_path, entry):
    queued = ready_path.parent / entry['source_relative']
    if queued.is_symlink() or sha(queued / 'SOURCE.json') != entry['source_sha256']:
        raise ValueError('source_receipt_sha256')
    if sha(queued / 'EXPOSURE.json') != entry['exposure_sha256']:
        raise ValueError('exposure_receipt_sha256')
    source, exposure = read(queued / 'SOURCE.json'), read(queued / 'EXPOSURE.json')
    if (source['source_relative'] != queued.name or source['source_name'] != entry['label']
            or source['copy_files'] != entry['copy_files']
            or any(source[key] != entry[key] for key in ('absolute_sleep', 'sleep_complete_index',
                'sleep_complete_sha256', 'adapter_state_sha256', 'optimizer_steps'))):
        raise ValueError('exact_complete_adapter_source_join')
    if (exposure['eligible'] is not True or exposure['source_cut_index'] != source['sleep_complete_index']
            or exposure['source_cut_sha256'] != source['sleep_complete_sha256']
            or exposure['unresolved_requests'] or any(exposure['identifier_matches'].values())
            or any(exposure['semantic_matches'].values())):
        raise ValueError('same_source_recorded_exposure_eligibility')
    for name, expected in source['copy_files'].items():
        path = queued / name
        if path.is_symlink() or sha(path) != expected['sha256']:
            raise ValueError('source_file_identity')
    commit = read(queued / 'COMMIT.json')
    if (commit['adapter_state_sha256'] != source['adapter_state_sha256']
            or commit['optimizer_steps'] != source['optimizer_steps']):
        raise ValueError('adapter_commit_and_compute_join')
    return queued, source, exposure


def prepare(arm):
    if arm not in ARMS or time.time() >= 1790726400:
        raise ValueError('registered_arm_within_existing_receiving_bound')
    root = ROOT / arm
    if root.exists():
        raise ValueError('new_immutable_probe_root_only')
    if sha(TEMPLATE / 'SOURCE_MANIFEST.json') != SOURCE_MANIFEST:
        raise ValueError('reuse_exact_tested_evaluator_source')
    for relative, expected in read(TEMPLATE / 'SOURCE_MANIFEST.json').items():
        if sha(TEMPLATE / 'source' / relative) != expected:
            raise ValueError('unchanged_tested_evaluator_bytes')
    readiness = read(READY)
    ROOT.mkdir(mode=0o700, exist_ok=True)
    plan_path = ROOT / 'PLAN.json'
    if not plan_path.exists():
        write(plan_path, dict(arms=list(ARMS), source_readiness_sha256=sha(READY),
            deadline_unix=min(time.time() + 5400, 1790726400), source_manifest_sha256=SOURCE_MANIFEST,
            target_epoch_sha256=EPOCH, parent_tokens=0, frozen_parameters=True,
            source_selection_unix=readiness['selection']['selected_unix']))
    plan = read(plan_path)
    if plan['arms'] != list(ARMS) or plan['source_readiness_sha256'] != sha(READY):
        raise ValueError('predeclared_source_block_unchanged')
    if not (ROOT / 'epoch').exists():
        shutil.copytree(TEMPLATE.parent / 'epoch', ROOT / 'epoch')
    binding = read(ROOT / 'epoch/JUDGE_EPOCH.json')
    canonical = json.dumps(binding, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    if (hashlib.sha256(canonical.encode()).hexdigest() != EPOCH
            or sha(ROOT / 'epoch/PRIMARY_PANELS.private.json') != binding['primary_panels_sha256']):
        raise ValueError('exact_same_adopted_judge_epoch')
    root.mkdir(mode=0o700)
    for directory in ('source', 'assets', 'judge'):
        shutil.copytree(TEMPLATE / directory, root / directory, ignore=shutil.ignore_patterns('__pycache__'))
    for filename in ('GAME_MANIFEST.json', 'SELECTION.json', 'SOURCE_MANIFEST.json'):
        shutil.copyfile(TEMPLATE / filename, root / filename)
    identity = read(TEMPLATE / 'CONDITION.json')
    identity['condition'] = 'R233_C2_AGE_' + arm
    source = None
    if arm == 'base':
        shutil.copyfile(TEMPLATE / 'FRESHNESS_VERIFIED.json', root / 'FRESHNESS_VERIFIED.json')
    else:
        entry = source_entry(readiness, arm)
        queued, source, exposure = verify_source(READY, entry)
        destination = root / 'sources' / source['source_relative']
        for name, expected in source['copy_files'].items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(queued / name, target)
            if sha(target) != expected['sha256'] or sha(queued / name) != expected['sha256']:
                raise ValueError('immutable_source_before_copy_after')
        write(root / 'sources/CAPTURE.json', dict(sources=[source], source_context_loaded=False))
        shutil.copyfile(queued / 'EXPOSURE.json', root / 'FRESHNESS_VERIFIED.json')
        identity.update(source_name=source['source_name'], absolute_sleep=source['absolute_sleep'],
            sleep_complete_sha256=source['sleep_complete_sha256'], optimizer_loaded=False,
            source_parent_text_loaded=False, parent_tokens=0)
    write(root / 'CONDITION.json', identity)
    config = read(TEMPLATE / 'CONFIG.json')
    config.update(root=str(root), identity=identity, epoch_root=str(ROOT / 'epoch'),
        deadline_unix=plan['deadline_unix'], plain_base=arm == 'base',
        freshness_sha256=sha(root / 'FRESHNESS_VERIFIED.json'), source_readiness_sha256=sha(READY))
    write(root / 'CONFIG.json', config)
    (root / 'queue').mkdir()
    receipt = dict(arm=arm, root=str(root), config_sha256=sha(root / 'CONFIG.json'),
        source_manifest_sha256=SOURCE_MANIFEST, source_readiness_sha256=sha(READY),
        source_age=source['absolute_sleep'] if source else None, state='CPU_PREPARED_NOT_LOADED',
        existing_results_modified=False, source_life_signals=[])
    write(root / 'CPU_PREPARED.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=ARMS, required=True)
    print(json.dumps(prepare(parser.parse_args().arm)))
