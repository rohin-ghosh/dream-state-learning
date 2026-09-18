"""Read-only last-complete/suffix accounting; never reconcile or replay updates."""

import hashlib
import json
from pathlib import Path
import re
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and not path.is_symlink(), 'canonical_original')
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(path):
    return json.loads(Path(path).read_text())


def suffix_summary(records, saved_index, saved_steps):
    suffix = [record for record in records if record['index'] > saved_index]
    updates = [record for record in suffix if record['kind'] == 'UPDATE']
    steps = [record['document']['optimizer_step'] for record in updates]
    require(steps == list(range(saved_steps+1, saved_steps+len(steps)+1)), 'consecutive_unsaved_updates')
    counts = {}
    for record in suffix:
        counts[record['kind']] = counts.get(record['kind'], 0)+1
    inbox = [dict(index=record['index'], record_sha256=record['sha256'],
        source_id=record['document'].get('source_id'), source_sha256=record['document'].get('source_sha256'))
        for record in suffix if record['kind'] == 'INBOX']
    snapshots = bool(updates) and all(all(key in record['document'] for key in
        ('adapter_state_sha256', 'optimizer_sha256', 'rng_sha256')) for record in updates)
    return dict(counts=counts, unsaved_updates=len(updates), saved_optimizer_steps=saved_steps,
        last_observed_optimizer_step=steps[-1] if steps else saved_steps, complete_per_update_snapshots=snapshots,
        post_saved_inbox_receipts=inbox, suffix_replayed=False, original_suffix_removed=False,
        exact_interrupted_state_recoverable_from_UPDATE_records=not updates or snapshots,
        classification='UNSAVED_UPDATES_REQUIRE_EXPLICIT_SAVED_STATE_RECOVERY' if updates and not snapshots else 'NO_UNSAVED_UPDATE_GAP')


def inspect(root, physical):
    old_root = Path('/localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1')
    staged = read(old_root / ('control'+str(physical)) / 'STAGED.json')
    config_path = Path(staged['old_config'])
    require(reference(config_path)['sha256'] == staged['old_config_sha256'], 'original_guard_unchanged')
    config = read(config_path)
    plan = read(config['plan_path'])
    require(reference(config['plan_path'])['sha256'] == config['plan_sha256'], 'original_plan_unchanged')
    journal = Path(plan['root']) / 'stream'
    manifest = read(journal / 'JOURNAL.json')
    previous = digest(manifest)
    paths = sorted(path for path in (journal / 'records').glob('*.json') if re.fullmatch(r'\d{20}\.json', path.name))
    records = []
    for index, path in enumerate(paths):
        record = read(path)
        require(record['index'] == index and record['journal_id'] == manifest['journal_id']
            and record['previous_sha256'] == previous and record['sha256'] == digest({key: value for key, value in record.items()
                                                                                 if key != 'sha256'}), 'complete_published_chain')
        previous = record['sha256']
        records.append(record)
    saved = next(record for record in reversed(records) if record['kind'] == 'SLEEP_COMPLETE')
    cycle = saved['document']['cycle']
    checkpoint_path = Path(plan['root']) / 'checkpoints' / ('sleep_%06d' % cycle) / 'COMMIT.json'
    checkpoint = read(checkpoint_path)
    summary = suffix_summary(records, saved['index'], checkpoint['optimizer_steps'])
    dispatch = [reference(path) for path in sorted((Path(plan['root']) / 'readouts').glob('*_DISPATCH.json'))]
    terminal = {}
    for name in ('EXIT.json', 'SERVICE_EXIT.json', 'SUPERVISOR_FAILED.json'):
        path = config_path.parent / name
        if path.exists():
            terminal[name] = dict(reference=reference(path), document=read(path))
    actors = {}
    for role, expected in staged['processes'].items():
        path = Path('/proc', str(expected['pid']), 'stat')
        if path.exists():
            fields = path.read_text().rsplit(') ', 1)[1].split()
            actors[role] = dict(pid=expected['pid'], state=fields[0], start_ticks=fields[19],
                same_ticks=fields[19] == expected['start_ticks'])
        else:
            actors[role] = dict(pid=expected['pid'], absent=True)
    proof_path = root / ('preflight'+str(physical)) / 'STATE_CPU.json'
    proof = read(proof_path)
    require(proof['status'] == 'PASS' and proof['checkpoint_ref'] == reference(checkpoint_path)
        and proof['optimizer_steps'] == checkpoint['optimizer_steps'], 'historical_candidate_actual_CPU_matches_last_saved')
    return dict(physical=physical, logical_life=plan['root'], observed_unix=time.time(), actors=actors,
        saved=dict(cycle=cycle, index=saved['index'], record_ref=reference(paths[saved['index']]),
            state_sha256=saved['document']['resume_state']['sha256'], checkpoint_ref=reference(checkpoint_path),
            optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256']),
        head=dict(index=records[-1]['index'], kind=records[-1]['kind'], reference=reference(paths[-1])),
        full_published_chain_verified=True, snapshot_head_may_advance=True, suffix=summary,
        existing_readout_dispatch_refs=dispatch, terminal=terminal, source_ref=reference(Path(plan['source_root']) /
            'gpu/orch_r125_continual_native.py'), state_CPU_ref=reference(proof_path),
        source_or_original_artifacts_changed=False, learner_signals=0, recovery_execution_authorized_by_this_receipt=False)


if __name__ == '__main__':
    root = Path(sys.argv[1])
    require(root == Path('/localhome/local-rohing/orch_r179_node3_wall_20260917t1752z_2'), 'one_preflight_root')
    print(json.dumps(dict(schema='R179_NODE3_RECOVERY_PREPARATION_V1', rows=[inspect(root, physical)
        for physical in (0,1,2,3,4,7)], observed_unix=time.time(), models=0, signals=0,
        status='READONLY_PREFIX_SUFFIX_AND_SAVED_CPU_ACCOUNTED_NOT_RECOVERY_GO'), sort_keys=True))
