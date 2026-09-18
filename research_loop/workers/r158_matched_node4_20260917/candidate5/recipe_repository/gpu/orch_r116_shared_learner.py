"""Node-local eight-branch barrier and single-owner LoRA consolidation."""

from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from organism_v6 import orch_r107_parented_replay as replay


BRANCHES = ('F1', 'F2', 'F3', 'F4', 'A1', 'A2', 'A3', 'A4')
ANCHOR_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
PHASES = frozenset(('experience', 'episode', 'presleep', 'reflection', 'open_turn',
                    'open_train', 'open_continue', 'open_observation', 'continuation', 'metacognition'))
METRICS = ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'COORDINATOR.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield root


def checked_checkpoint(checkpoint):
    for field in ('path', 'optimizer_path'):
        require(Path(checkpoint[field]).is_absolute(), 'absolute_checkpoint_path')
        require(sha(checkpoint[field]) == checkpoint[field + '_sha256'],
                'checkpoint_or_optimizer_hash_mismatch')
    return deepcopy(checkpoint)


def initialize(root, branch_specs, checkpoint, *, owner='F1', excluded_ids=(),
               anchor_sha256=ANCHOR_SHA, prior_metrics, initial_history):
    require(set(branch_specs) == set(BRANCHES), 'exact_eight_branches_required')
    require(owner == 'F1', 'declared_single_optimizer_owner_F1')
    require(anchor_sha256 == ANCHOR_SHA, 'same_broad_anchor_inventory')
    require(len({str(Path(spec['root']).resolve()) for spec in branch_specs.values()}) == 8,
            'distinct_branch_roots')
    exclusions = set(excluded_ids)
    for spec in branch_specs.values():
        require(Path(spec['root']).is_absolute() and spec['train_ids'], 'bound_branch_train_inventory')
        require(not exclusions.intersection(spec['train_ids']), 'held_train_overlap')
    require(set(prior_metrics) == set(METRICS), 'explicit_pretransition_counters_required')
    require(all(value is None or type(value) is int and value >= 0 for value in prior_metrics.values()),
            'unknown_history_is_null_not_zero')
    require(set(initial_history).issubset(BRANCHES), 'bound_initial_history_branches')
    for branch, rows in initial_history.items():
        for row in rows:
            validate_row(row, branch_specs[branch], exclusions)
    config = dict(schema='R116_SHARED_LEARNER_V1', branches=branch_specs, owner=owner,
                  excluded_ids=sorted(exclusions), anchor_sha256=anchor_sha256,
                  episodes_per_branch=2, new_presentations=16, rehearsal_presentations=1,
                  anchor_loss_weight=.25, initial_checkpoint=checked_checkpoint(checkpoint),
                  pretransition_metrics=prior_metrics, initial_history=initial_history)
    with locked(root) as root:
        if (root / 'CONFIG.json').exists():
            require(read(root / 'CONFIG.json') == config, 'shared_configuration_is_immutable')
            return read(root / 'STATE.json')
        write(root / 'CONFIG.json', config)
        state = dict(generation=0, checkpoint=checkpoint, **prior_metrics,
                     config_sha256=sha(root / 'CONFIG.json'),
                     **{'shared_' + name: 0 for name in METRICS})
        write(root / 'STATE.json', state)
        return state


def validate_row(row, spec, exclusions, *, generation=None, checkpoint_sha256=None):
    source = Path(row['source_call_path']).resolve()
    require(source.is_relative_to(Path(spec['root']).resolve()), 'source_outside_branch')
    require(not any('readout' in part.lower() or part.lower() in ('dev', 'final')
                    for part in source.parts), 'readout_path_never_experience')
    require(sha(source) == row['source_call_sha256'], 'source_capture_hash_mismatch')
    call = read(source)
    metadata = call.get('request') or call
    if generation is not None:
        require(metadata.get('shared_generation') == generation
                and metadata.get('shared_checkpoint_sha256') == checkpoint_sha256,
                'capture_must_bind_actual_shared_child')
    phase = metadata.get('phase', metadata.get('purpose'))
    require(phase in PHASES, 'readout_phase_never_experience')
    require(metadata.get('split', 'TRAIN') == 'TRAIN', 'held_split_never_experience')
    require(not metadata.get('attached_readout') and not metadata.get('attached_evaluation')
            and not metadata.get('evaluation_origin'), 'readout_open_turn_never_experience')
    task_id = metadata.get('task_id', call.get('task_id'))
    require(task_id == row['episode_id'] and task_id in spec['train_ids']
            and task_id not in exclusions, 'only_bound_train_tasks')
    replay.verify_source(row, call)
    return row


def submit(root, branch, generation, checkpoint_sha256, episode_ids, rows):
    require(branch in BRANCHES and len(episode_ids) == 2, 'two_episodes_per_branch')
    require(rows, 'empty_experience_submission')
    with locked(root) as root:
        config, state = read(root / 'CONFIG.json'), read(root / 'STATE.json')
        require(state['config_sha256'] == sha(root / 'CONFIG.json'), 'configuration_hash')
        require(generation == state['generation'], 'stale_or_future_generation')
        require(checkpoint_sha256 == state['checkpoint']['path_sha256'], 'common_child_required')
        spec = config['branches'][branch]
        require(all(identifier in spec['train_ids'] for identifier in episode_ids), 'bound_episode_ids')
        for row in rows:
            validate_row(row, spec, config['excluded_ids'], generation=generation,
                         checkpoint_sha256=checkpoint_sha256)
            require(row['episode_id'] in episode_ids, 'row_outside_two_episode_cycle')
        identities = [row['source_call_sha256'] for row in rows]
        require(len(identities) == len(set(identities)), 'duplicate_source_in_submission')
        receipt = dict(branch=branch, generation=generation, checkpoint_sha256=checkpoint_sha256,
                       episode_ids=list(episode_ids), rows=rows)
        path = root / f'generation_{generation:06d}' / (branch + '.json')
        if path.exists():
            require(read(path) == receipt, 'submission_changed_after_barrier_arrival')
        else:
            write(path, receipt)
        return dict(path=str(path), sha256=sha(path), generation=generation)


def schedule(new_count, old_count, anchor_count=42):
    require(new_count > 0 and old_count >= 0 and anchor_count == 42, 'valid_sleep_inventory')
    items = [('NEW', index) for presentation in range(16) for index in range(new_count)]
    items.extend(('REHEARSAL', index) for index in range(old_count))
    for step, (kind, index) in enumerate(items):
        anchors = list(range(step, 42, len(items))) if step < 42 else [step % 42]
        yield dict(kind=kind, index=index, child_weight=.75, anchors=anchors,
                   anchor_weight=.25 / len(anchors))


def barrier_status(root):
    root = Path(root)
    state = read(root / 'STATE.json')
    require(state['config_sha256'] == sha(root / 'CONFIG.json'), 'configuration_hash')
    folder = root / f"generation_{state['generation']:06d}"
    present = [branch for branch in BRANCHES if (folder / (branch + '.json')).exists()]
    return dict(generation=state['generation'], present=present,
                missing=[branch for branch in BRANCHES if branch not in present], state=state)


def recover_published_checkpoint(root):
    with locked(root) as root:
        state = barrier_status(root)['state']
        complete = root / f"generation_{state['generation']:06d}" / 'sleep' / 'COMPLETE.json'
        require(complete.exists(), 'no_complete_checkpoint_to_recover')
        receipt = read(complete)
        next_state = receipt['state']
        require(receipt['source_checkpoint'] == state['checkpoint']
                and next_state['generation'] == state['generation'] + 1
                and next_state['config_sha256'] == state['config_sha256'], 'recovery_lineage_mismatch')
        checked_checkpoint(next_state['checkpoint'])
        for name in METRICS:
            require(next_state['shared_' + name] == state['shared_' + name] + receipt['metrics'][name],
                    'recovery_counter_mismatch')
            expected = None if state[name] is None else state[name] + receipt['metrics'][name]
            require(next_state[name] == expected, 'recovery_lifetime_counter_mismatch')
        write(root / 'STATE.json', next_state, replace=True)
        return dict(status='RECOVERED_PUBLISHED_CHECKPOINT', state=next_state, optimizer_updates_replayed=0)


def pooled_rows(root, generation):
    config = read(root / 'CONFIG.json')
    rows, seen = [], set()
    for branch in BRANCHES:
        receipt = read(root / f'generation_{generation:06d}' / (branch + '.json'))
        for row in receipt['rows']:
            validate_row(row, config['branches'][branch], config['excluded_ids'],
                         generation=generation, checkpoint_sha256=receipt['checkpoint_sha256'])
            require(row['source_call_sha256'] not in seen, 'duplicate_source_between_branches')
            seen.add(row['source_call_sha256'])
            rows.append(row)
    return rows


def train(engine, optimizer, rows, history, anchors, output, check, context_limit=16384):
    from gpu import orch_guided_native as native

    require(len(anchors) == 42, 'all42_anchors_required')
    encoded, previous = [], []
    rejected = []
    for kind, source, destination in (('NEW', rows, encoded), ('REHEARSAL', history, previous)):
        for row in source:
            try:
                destination.append(replay.encode_row(row, engine.tokenizer, context_limit))
            except ValueError as error:
                rejected.append(dict(kind=kind, source=row['source_call_sha256'], error=str(error)))
    write(Path(output) / 'ENCODING.json', dict(new=len(encoded), old=len(previous), rejected=rejected))
    require(encoded, 'no_encodable_new_child_rows')
    native.development.enable_existing_adapter(engine)
    engine.model.train()
    engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    engine.model.enable_input_require_grads()
    engine.model.config.use_cache = False
    steps, child_tokens, anchor_tokens = 0, 0, 0
    try:
        with (Path(output) / 'UPDATES.jsonl').open('x') as log:
            for allocation in schedule(len(encoded), len(previous)):
                check('shared_optimizer_update')
                item = (encoded if allocation['kind'] == 'NEW' else previous)[allocation['index']]
                batch = [(item, allocation['child_weight'])]
                batch.extend((anchors[index]['encoded'], allocation['anchor_weight'])
                             for index in allocation['anchors'])
                optimizer.zero_grad(set_to_none=True)
                for item, weight in batch:
                    inputs = engine.torch.tensor([item.input_ids], dtype=engine.torch.long, device=engine.device)
                    labels = engine.torch.tensor([item.labels], dtype=engine.torch.long, device=engine.device)
                    with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                        loss = engine.model(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs),
                                            labels=labels).loss * weight
                    require(bool(engine.torch.isfinite(loss)), 'nonfinite_shared_loss')
                    loss.backward()
                optimizer.step()
                steps += 1
                child_tokens += len(batch[0][0].target_ids)
                anchor_tokens += sum(len(item.target_ids) for item, weight in batch[1:])
                log.write(json.dumps(dict(step=steps, allocation=allocation,
                    child_token_exposures=child_tokens, anchor_token_exposures=anchor_tokens)) + '\n')
                log.flush()
    finally:
        engine.model.requires_grad_(False)
        engine.model.eval()
        engine.model.gradient_checkpointing_disable()
        engine.model.config.use_cache = True
    engine.verify_base()
    return dict(optimizer_steps=steps, child_token_exposures=child_tokens,
                anchor_token_exposures=anchor_tokens, encoded_new_rows=len(encoded),
                encoded_rehearsal_rows=len(previous), anchor_loss_weight=.25,
                new_presentations=16, rehearsal_presentations=1, rejected=rejected)


def consolidate(root, owner, loaded_checkpoint_sha256, engine, optimizer, anchors,
                save_checkpoint, check, train_call=train):
    require(owner == 'F1', 'only_F1_owns_optimizer')
    with locked(root) as root:
        status = barrier_status(root)
        if status['missing']:
            return dict(status='WAITING', missing=status['missing'])
        state = status['state']
        require(loaded_checkpoint_sha256 == state['checkpoint']['path_sha256'], 'owner_loaded_common_child')
        checked_checkpoint(state['checkpoint'])
        generation = state['generation']
        output = root / f'generation_{generation:06d}' / 'sleep'
        output.mkdir(exist_ok=True)
        require(not (output / 'START.json').exists(), 'partial_sleep_requires_explicit_recovery_no_replay')
        rows = pooled_rows(root, generation)
        config = read(root / 'CONFIG.json')
        history = []
        for branch, previous in config['initial_history'].items():
            history.extend(validate_row(row, config['branches'][branch], config['excluded_ids'])
                           for row in previous)
        history.extend(row for prior in range(generation) for row in pooled_rows(root, prior))
        require(not {row['source_call_sha256'] for row in history}.intersection(
            row['source_call_sha256'] for row in rows), 'old_capture_resubmitted_as_new')
        write(output / 'START.json', dict(generation=generation, pid=os.getpid(), started_unix=time.time(),
              checkpoint=state['checkpoint'], row_count=len(rows), rehearsal_rows=len(history), owner=owner))
        metrics = train_call(engine, optimizer, rows, history, anchors, output, check)
        checkpoint = checked_checkpoint(save_checkpoint(output / 'checkpoint', generation + 1, metrics))
        next_state = dict(generation=generation + 1, checkpoint=checkpoint,
                          config_sha256=state['config_sha256'])
        for name in METRICS:
            next_state[name] = None if state[name] is None else state[name] + metrics[name]
            next_state['shared_' + name] = state['shared_' + name] + metrics[name]
        write(output / 'COMPLETE.json', dict(metrics=metrics, state=next_state,
              completed_unix=time.time(), same_optimizer=True, source_checkpoint=state['checkpoint']))
        write(root / 'STATE.json', next_state, replace=True)
        return dict(status='COMPLETE', state=next_state, metrics=metrics)
