"""Freeze one committed shared checkpoint for the scheduled sealed readouts."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time


CUT = datetime(2026, 9, 15, 17, tzinfo=timezone.utc).timestamp()
DEADLINE = CUT + 20 * 60
BRANCHES = ('F1', 'F2', 'F3', 'F4', 'A1', 'A2', 'A3', 'A4')
METRICS = ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures')
SCHEMA = 'R118_FINAL_SELECTION_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def checkpoint_valid(reference, root, config):
    allowed = (root, Path(config['branches']['F1']['root']).resolve(strict=True))
    for field in ('path', 'optimizer_path'):
        candidate = Path(reference[field])
        require(candidate.is_absolute(), 'absolute_checkpoint_reference')
        candidate = candidate.resolve(strict=True)
        require(any(candidate.is_relative_to(parent) for parent in allowed), 'checkpoint_outside_owner')
        require(sha(candidate) == reference[field + '_sha256'], 'checkpoint_or_optimizer_changed')
    checkpoint = read(reference['path'])
    require(checkpoint.get('complete') is True, 'complete_checkpoint_required')
    require(checkpoint.get('optimizer_rng_sha256') == reference['optimizer_path_sha256'],
            'checkpoint_optimizer_binding')


def validate_selection(root, *, config_sha256, initialized_sha256, adoption_sha256, clock=time.time):
    require(CUT <= clock() < DEADLINE, 'FINAL_selection_clock_gate')
    root = Path(root).resolve(strict=True)
    pins = {'CONFIG.json': config_sha256, 'INITIALIZED.json': initialized_sha256,
            'ADOPTION.json': adoption_sha256}
    selected = read(root / 'FINAL_SELECTION.json')
    require(selected.get('schema') == SCHEMA and selected.get('lineage_sha256') == pins
            and selected.get('scheduled_unix') == CUT and selected.get('shared_root') == str(root)
            and selected.get('evaluation_deadline_unix') == DEADLINE, 'existing_selection_binding')
    require(CUT <= selected['selected_unix'] < DEADLINE
            and selected['branches'] == list(BRANCHES), 'selection_time_and_roster')
    for name, expected in pins.items():
        require(sha(root / name) == expected, 'shared_lineage_binding')
    config = read(root / 'CONFIG.json')
    snapshot = selected['state_reference']
    snapshot_path = Path(snapshot['path']).resolve(strict=True)
    require(snapshot_path.parent == root / 'final_selection'
            and sha(snapshot_path) == snapshot['sha256'], 'immutable_state_snapshot')
    state = read(snapshot_path)
    require(state['generation'] == selected['generation'] and state['checkpoint'] == selected['checkpoint']
            and state['config_sha256'] == config_sha256, 'selected_state_binding')
    require(all(selected['shared_metrics'][metric] == state['shared_' + metric]
                and selected['lifetime_metrics'][metric] == state[metric] for metric in METRICS),
            'selected_metrics_binding')
    if state['generation']:
        completed = selected['committed_sleep']
        expected = root / f"generation_{state['generation'] - 1:06d}" / 'sleep' / 'COMPLETE.json'
        require(Path(completed['path']).resolve(strict=True) == expected
                and sha(expected) == completed['sha256'], 'committed_sleep_reference')
        receipt = read(expected)
        require(receipt['state'] == state and receipt['same_optimizer'] is True
                and receipt['completed_unix'] <= CUT, 'committed_sleep_binding')
    else:
        require(state['checkpoint'] == config['initial_checkpoint'] and selected['committed_sleep'] is None
                and all(state['shared_' + metric] == 0 for metric in METRICS), 'initial_selection_binding')
    checkpoint_valid(selected['checkpoint'], root, config)
    return selected


def select(root, *, config_sha256, initialized_sha256, adoption_sha256, clock=time.time):
    now = clock()
    require(CUT <= now < DEADLINE, 'FINAL_selection_clock_gate')
    root = Path(root).resolve(strict=True)
    pins = {'CONFIG.json': config_sha256, 'INITIALIZED.json': initialized_sha256,
            'ADOPTION.json': adoption_sha256}
    for name, expected in pins.items():
        require(sha(root / name) == expected, 'shared_lineage_binding')
    config = read(root / 'CONFIG.json')
    require(config['owner'] == 'F1' and set(config['branches']) == set(BRANCHES), 'exact_shared_learner')
    with (root / 'FINAL_SELECTION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output = root / 'FINAL_SELECTION.json'
        if output.exists():
            return validate_selection(root, config_sha256=config_sha256,
                initialized_sha256=initialized_sha256, adoption_sha256=adoption_sha256, clock=clock)
        state_path = root / 'STATE.json'
        state_bytes = state_path.read_bytes()
        state_sha = hashlib.sha256(state_bytes).hexdigest()
        state = json.loads(state_bytes)
        require(state['config_sha256'] == config_sha256, 'state_configuration_binding')
        generation = state['generation']
        require(type(generation) is int and generation >= 0, 'generation_required')
        for metric in METRICS:
            value = state['shared_' + metric]
            require(type(value) is int and value >= 0, 'shared_counters_required')
        if generation == 0:
            require(state['checkpoint'] == config['initial_checkpoint'], 'initial_checkpoint_binding')
            require(all(state['shared_' + metric] == 0 for metric in METRICS), 'no_uncommitted_credit')
            require(all(state[metric] == config['pretransition_metrics'][metric] for metric in METRICS),
                    'prior_counters_preserved')
            completed = None
        else:
            path = root / f'generation_{generation - 1:06d}' / 'sleep' / 'COMPLETE.json'
            complete = read(path)
            require(complete['state'] == state and complete.get('same_optimizer') is True,
                    'published_state_requires_completed_sleep')
            require(complete['completed_unix'] <= CUT, 'no_post_cut_checkpoint')
            completed = dict(path=str(path), sha256=sha(path))
        checkpoint_valid(state['checkpoint'], root, config)
        require(sha(state_path) == state_sha, 'state_changed_during_selection')
        require(clock() < DEADLINE, 'selection_deadline')
        snapshot = root / 'final_selection' / ('state_' + state_sha + '.json')
        snapshot.parent.mkdir(exist_ok=True)
        if snapshot.exists():
            require(read(snapshot) == state, 'snapshot_never_overwritten')
        else:
            write_new(snapshot, state)
        selected = dict(schema=SCHEMA, scheduled_unix=CUT, selected_unix=now,
            evaluation_deadline_unix=DEADLINE, shared_root=str(root), generation=generation,
            checkpoint=state['checkpoint'], committed_sleep=completed,
            state_reference=dict(path=str(snapshot), sha256=sha(snapshot)),
            observed_state_reference=dict(path=str(state_path), sha256=state_sha), lineage_sha256=pins,
            lifetime_metrics={metric: state[metric] for metric in METRICS},
            shared_metrics={metric: state['shared_' + metric] for metric in METRICS},
            branches=list(BRANCHES), selection_rule='latest_observed_committed_pre_cut_checkpoint',
            sealed_tasks_read=False, parent_calls=0, optimizer_updates=0,
            new_evaluation_scope_not_old_lifetime_extension=True)
        write_new(output, selected)
        return selected


def wait_select(root, **kwargs):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_selector')
    while time.time() < CUT:
        time.sleep(max(0, min(30, CUT - time.time())))
    return select(root, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('select', 'wait'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--initialized-sha256', required=True)
    parser.add_argument('--adoption-sha256', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    require(sha(__file__) == args.source_sha256, 'immutable_selector_source')
    action = wait_select if args.action == 'wait' else select
    selected = action(args.root, config_sha256=args.config_sha256,
        initialized_sha256=args.initialized_sha256, adoption_sha256=args.adoption_sha256)
    print(json.dumps(dict(path=str(args.root / 'FINAL_SELECTION.json'),
        sha256=sha(args.root / 'FINAL_SELECTION.json'), generation=selected['generation'])))


if __name__ == '__main__':
    main()
