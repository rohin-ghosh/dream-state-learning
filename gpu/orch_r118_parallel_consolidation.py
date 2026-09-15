"""Prospective all-eight consolidation hook; no CLI activation or process launch.

Owners call ``consolidate`` collectively with their existing raw engines, a
finite-timeout Gloo group and F1's existing AdamW (None on all seven workers).
Main supplies an immutable, generation-specific activation document only after
the previous serial commit/readouts and all eight safe handoffs. This module
does not create that document, alter CONFIG, restart actors, or retry training.
"""

import fcntl
import inspect
import math
import os
from pathlib import Path
import time

from gpu import orch_r116_shared_learner as shared
from gpu import orch_r116_shared_parallel_sleep as parallel


SCHEMA = 'R118_PARALLEL_CONSOLIDATION_V1'
HARD_END = 1789491720
TRAIN_END = 1789491600
BRANCHES = shared.BRANCHES
require, read, sha, write = shared.require, shared.read, shared.sha, shared.write


def integration_contract():
    return dict(schema=SCHEMA, status='PROSPECTIVE_NOT_ACTIVATED',
        entrypoint='consolidate', rank_order=list(BRANCHES), process_launch=False,
        owner_hooks={
            'Main': 'Create pinned activation after serial commit/readouts and all8 safe handoffs; never during START without COMPLETE.',
            'all8': 'Keep raw engine/LoRA objects and RNG; stop collection at two-episode submission barrier; supply live process identity and safe certificate.',
            'F1': 'Pass the SAME existing AdamW and original save_checkpoint(destination,generation,metrics) callback; do not reconstruct optimizer.',
            'workers': 'Pass optimizer=None and save_checkpoint=None; no optimizer allocation.',
            'group': 'Caller-owned Gloo group, rank order F1..A4, finite timeout <=180s, no fork of CUDA engines.',
            'rows': 'Each rank runs pinned prepare_native_cohort against identical COMMON and original F1 anchor order; native prefix masking unchanged.',
            'after_return': 'All8 in-place LoRA broadcasts verified; collective reload ACKs durable before return. Owners retain fresh-process DEV/FINAL/open scheduling.',
            'committed_restart': 'Only at an idle common boundary: restore_committed restores adapter and existing F1 optimizer in place plus each saved rank RNG; never during an unfinished sleep.',
            'failure': 'No retry/reset/replay. Preserve START, UPDATES, sidecars and FAILED. Only recover_complete may repair COMPLETE->STATE without training.'},
        activation_fields=['schema','status','root','generation','pins','source_files',
                           'participants','deadline_unix','commit_reserve_seconds'],
        pin_files=['CONFIG.json','STATE.json','ADOPTION.json','INITIALIZED.json'],
        participant_fields=['branch','root','generation','checkpoint_sha256','identity',
                            'status','bounds','preserved_files','submission_sha256'],
        participant_status='SAFE_FOR_PARALLEL',
        bounds_fields=['train_end_unix','hard_end_unix','native_used','native_cap','parent_used','parent_cap'],
        participant_note='participants maps branch to {path,sha256}; preserved_files maps root-relative ledgers/CARRY/cursors to hashes, owner-produced at boundary; identity is live boot_id/pid/start_ticks.',
        algorithm='Average-gradient batch8 AdamW, NOT serial-equivalent; partial tail averages active ranks only.',
        accounting='NEW16/OLD1, 42 anchors, .75 child/.25 anchor per rank; add actual logical optimizer steps and actual target tokens, not presentations as optimizer steps.',
        publication='Original CHECKPOINT.json and optimizer_rng.pt keys preserved; hashed PARALLEL_RNG.pt and all8 manifest added in one renamed checkpoint directory, then COMPLETE, then STATE.',
        deadlines='Immutable minimum of activation, all8 TRAIN/lease bounds and 17:00UTC; hard ceiling17:02UTC; reserve for commit; no sliding deadlines.',
        native_gpu_tested=False, measured_speedup=None)


def process_identity():
    fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                pid=os.getpid(), start_ticks=int(fields[19]))


def checked_file(path, expected):
    path = Path(path)
    require(path.is_absolute() and not path.is_symlink() and sha(path) == expected,
            'immutable_file_hash_or_path')
    return path


def fsync_tree(folder):
    for path in sorted(Path(folder).rglob('*')):
        require(not path.is_symlink(), 'checkpoint_symlink')
        if path.is_file():
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
    for path in [*reversed(sorted(Path(folder).rglob('*'))), Path(folder)]:
        if path.is_dir():
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


def state_hash(value):
    from organism_v6.pcfl_vertical_train import _state_hash
    def normalize(item):
        if type(item).__module__.startswith('numpy'):
            return dict(numpy_dtype=str(item.dtype), shape=list(item.shape), values=item.tolist())
        if isinstance(item, dict):
            return {key: normalize(entry) for key, entry in item.items()}
        if isinstance(item, (tuple, list)):
            return tuple(normalize(entry) for entry in item)
        return item
    return _state_hash(normalize(value))


def reference(folder):
    result = {}
    for key, name in (('path', 'CHECKPOINT.json'), ('optimizer_path', 'optimizer_rng.pt')):
        path = Path(folder) / name
        result[key], result[key + '_sha256'] = str(path), sha(path)
    return shared.checked_checkpoint(result)


def advance_state(state, checkpoint, metrics):
    result = dict(generation=state['generation'] + 1, checkpoint=checkpoint,
                  config_sha256=state['config_sha256'])
    for name in shared.METRICS:
        require(type(metrics[name]) is int and metrics[name] >= 0, 'actual_nonnegative_counter')
        require(state[name] is None or type(state[name]) is int and state[name] >= 0, 'prior_counter')
        require(type(state['shared_' + name]) is int and state['shared_' + name] >= 0, 'prior_shared_counter')
        result[name] = None if state[name] is None else state[name] + metrics[name]
        result['shared_' + name] = state['shared_' + name] + metrics[name]
    return result


def validate_activation(root, path, expected, clock=time.time):
    root = Path(root).resolve(strict=True)
    document = read(checked_file(path, expected))
    require(document['schema'] == SCHEMA and document['status'] == 'ACTIVATE_PARALLEL_AT_SAFE_BOUNDARY'
            and document['root'] == str(root), 'explicit_exact_activation_required')
    require(set(document['pins']) == {'CONFIG.json','STATE.json','INITIALIZED.json','ADOPTION.json'}, 'exact_common_pins')
    for name, digest in document['pins'].items():
        checked_file(root / name, digest)
    for name, digest in document['source_files'].items():
        checked_file(name, digest)
    for module in (__file__, parallel.__file__, shared.__file__):
        require(str(Path(module).resolve()) in document['source_files'], 'successor_and_backend_must_be_pinned')
    from organism_v6 import pcfl_vertical_train, orch_guided_bridge
    for module in (pcfl_vertical_train, orch_guided_bridge):
        require(str(Path(module.__file__).resolve()) in document['source_files'], 'checkpoint_validator_source_pin')
    config, state = read(root / 'CONFIG.json'), read(root / 'STATE.json')
    require(document['generation'] == state['generation'] and state['config_sha256'] == document['pins']['CONFIG.json'],
            'exact_generation_state')
    require(config['owner'] == 'F1' and config['episodes_per_branch'] == 2
            and config['new_presentations'] == 16 and config['rehearsal_presentations'] == 1
            and config['anchor_loss_weight'] == .25 and config['anchor_sha256'] == shared.ANCHOR_SHA,
            'unchanged_common_recipe')
    require(set(document['participants']) == set(config['branches']) == set(BRANCHES), 'all8_required')
    shared.checked_checkpoint(state['checkpoint'])
    if state['generation']:
        previous = read(root / f"generation_{state['generation'] - 1:06d}" / 'sleep/COMPLETE.json')
        require(previous['state'] == state and previous['same_optimizer'] is True,
                'previous_shared_commit_required')
    advance_state(state, state['checkpoint'], dict.fromkeys(shared.METRICS, 0))
    require(math.isfinite(document['deadline_unix']), 'finite_activation_deadline')
    deadline = min(TRAIN_END, document['deadline_unix'])
    certificates, identities = {}, set()
    for branch in BRANCHES:
        entry = document['participants'][branch]
        certificate = read(checked_file(entry['path'], entry['sha256']))
        branch_root = Path(config['branches'][branch]['root']).resolve(strict=True)
        require(Path(entry['path']).resolve().is_relative_to(branch_root), 'certificate_under_own_root')
        require(certificate['branch'] == branch and certificate['root'] == str(branch_root)
                and certificate['generation'] == state['generation']
                and certificate['checkpoint_sha256'] == state['checkpoint']['path_sha256']
                and certificate['status'] == 'SAFE_FOR_PARALLEL', 'participant_safe_binding')
        identity = certificate['identity']
        require(type(identity['pid']) is int and type(identity['start_ticks']) is int, 'native_identity_types')
        process = Path('/proc') / str(identity['pid']) / 'stat'
        actual = process.read_text().rsplit(')', 1)[1].split()
        require(identity['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                and identity['start_ticks'] == int(actual[19]), 'participant_process_not_live')
        identities.add((identity['boot_id'], identity['pid'], identity['start_ticks']))
        bounds = certificate['bounds']
        require(math.isfinite(bounds['train_end_unix']) and math.isfinite(bounds['hard_end_unix'])
                and bounds['train_end_unix'] <= bounds['hard_end_unix'] <= HARD_END, 'original_lease_bounds')
        for kind in ('native','parent'):
            require(type(bounds[kind + '_used']) is int and type(bounds[kind + '_cap']) is int
                    and 0 <= bounds[kind + '_used'] <= bounds[kind + '_cap'], 'original_charge_caps')
        require(certificate['preserved_files'], 'boundary_ledger_hashes_required')
        for relative, digest in certificate['preserved_files'].items():
            target = branch_root / relative
            require(not Path(relative).is_absolute() and '..' not in Path(relative).parts
                    and target.resolve().is_relative_to(branch_root), 'boundary_path_escape')
            checked_file(target, digest)
        submission = root / f"generation_{state['generation']:06d}" / (branch + '.json')
        receipt = read(checked_file(submission, certificate['submission_sha256']))
        require(receipt['branch'] == branch and receipt['generation'] == state['generation']
                and receipt['checkpoint_sha256'] == state['checkpoint']['path_sha256']
                and len(receipt['episode_ids']) == len(set(receipt['episode_ids'])) == 2
                and set(receipt['episode_ids']).issubset(config['branches'][branch]['train_ids']),
                'exact_two_episode_submission')
        for row in receipt['rows']:
            require(row['episode_id'] in receipt['episode_ids'], 'row_outside_submitted_episodes')
        deadline = min(deadline, bounds['train_end_unix'])
        certificates[branch] = certificate
    require(len(identities) == 8, 'eight_distinct_live_participants')
    shared.pooled_rows(root, state['generation'])
    reserve = document['commit_reserve_seconds']
    require(math.isfinite(deadline) and type(reserve) is int and 30 <= reserve <= 600
            and clock() < deadline - reserve, 'immutable_deadline_with_commit_reserve')
    output = root / f"generation_{state['generation']:06d}" / 'sleep'
    require(not (output / 'START.json').exists(), 'existing_sleep_no_replay_or_hotpatch')
    return dict(document=document, state=state, certificates=certificates, deadline=deadline)


class Collectives:
    def __init__(self, torch, group):
        self.dist, self.group = torch.distributed, group
        self.rank = self.dist.get_rank(group)
        self.world = self.dist.get_world_size(group)
        self.owner = self.dist.get_global_rank(group, 0) if group is not None else 0
        require(self.world == 8 and str(self.dist.get_backend(group)).lower() == 'gloo', 'eight_rank_gloo_required')

    def gather(self, value):
        result = [None] * self.world
        self.dist.all_gather_object(result, value, group=self.group)
        return result

    def all(self, stage, action):
        result, error = None, None
        try:
            result = action()
        except Exception as exception:
            error = type(exception).__name__ + ': ' + str(exception)
        errors = self.gather(error)
        if any(errors):
            raise RuntimeError(stage + ': ' + repr(dict(enumerate(errors))))
        return result

    def owner_call(self, stage, action):
        result = self.all(stage, lambda: action() if self.rank == 0 else None)
        payload = [result]
        self.dist.broadcast_object_list(payload, src=self.owner, group=self.group)
        return payload[0]


def validate_loaded(engine, optimizer, state, rank):
    from organism_v6.orch_guided_bridge import AdapterIdentity
    document = read(state['checkpoint']['path'])
    identity = AdapterIdentity.from_document(document['adapter'])
    parameters = {name: parameter for name, parameter in engine.model.named_parameters() if parallel.is_lora(name)}
    require(state_hash(parameters) == identity.state_sha256, 'engine_must_hold_original_common_adapter')
    require(document['optimizer_rng_sha256'] == state['checkpoint']['optimizer_path_sha256'], 'original_optimizer_binding')
    if rank == 0:
        require(isinstance(optimizer, engine.torch.optim.AdamW), 'existing_F1_AdamW_required')
        original = engine.torch.load(state['checkpoint']['optimizer_path'], map_location='cpu', weights_only=False)
        require(set(original) == {'optimizer','cpu_rng','cuda_rng'}, 'original_optimizer_rng_schema')
        require(state_hash(optimizer.state_dict()) == state_hash(original['optimizer']), 'existing_optimizer_continuity')
    else:
        require(optimizer is None, 'workers_cannot_own_optimizer')
    engine.verify_base()


def commit_checkpoint(output, state, backend, payload, metrics, save_checkpoint, participants, activation_sha256):
    destination, staging = output / 'checkpoint', output / 'checkpoint.pending'
    require(not destination.exists() and not staging.exists(), 'checkpoint_no_overwrite_or_replay')
    backend._identity_check()
    saved = save_checkpoint(staging, state['generation'] + 1, metrics)
    backend._identity_check()
    require(saved == reference(staging), 'original_serializer_reference_required')
    document = read(staging / 'CHECKPOINT.json')
    original = backend.torch.load(staging / 'optimizer_rng.pt', map_location='cpu', weights_only=False)
    require(set(original) == {'optimizer','cpu_rng','cuda_rng'}
            and state_hash(original['optimizer']) == state_hash(payload['optimizer'])
            and state_hash(original['cpu_rng']) == state_hash(payload['rng'][0]['cpu']), 'serializer_optimizer_rng_continuity')
    if payload['rng'][0]['cuda'] is not None:
        index = backend.torch.device(backend.engine.device).index
        index = backend.torch.cuda.current_device() if index is None else index
        require(state_hash(original['cuda_rng'][index]) == state_hash(payload['rng'][0]['cuda']), 'serializer_owner_cuda_rng')
    require(document['complete'] is True and document['optimizer_rng_sha256'] == sha(staging / 'optimizer_rng.pt')
            and document['adapter']['state_sha256'] == state_hash(payload['lora']), 'serializer_original_checkpoint_contract')
    from organism_v6.orch_guided_bridge import AdapterIdentity
    AdapterIdentity.from_document(document['adapter'])
    adapter_path = Path(document['adapter']['path'])
    require(adapter_path.is_relative_to(staging), 'serializer_adapter_inside_staging')
    backend.torch.save(payload, staging / 'PARALLEL_RNG.pt')
    sidecar = dict(schema=SCHEMA, generation=state['generation'] + 1,
        activation_sha256=activation_sha256, source_checkpoint=state['checkpoint'],
        source_manifest_sha256=backend.source_manifest_sha256, schedule_binding_sha256=backend.binding,
        parallel_rng_sha256=sha(staging / 'PARALLEL_RNG.pt'),
        ranks=[dict(branch=branch, identity=participants[branch]['identity'], rng_sha256=state_hash(payload['rng'][rank]))
               for rank, branch in enumerate(BRANCHES)], metrics=metrics,
        same_optimizer=True, serial_adamw_equivalent=False)
    write(staging / 'PARALLEL.json', sidecar)
    document['adapter']['path'] = str(destination / adapter_path.relative_to(staging))
    document['parallel'] = dict(schema=SCHEMA, manifest_sha256=sha(staging / 'PARALLEL.json'),
                                payload_sha256=sidecar['parallel_rng_sha256'])
    write(staging / 'CHECKPOINT.json', document, replace=True)
    fsync_tree(staging)
    os.rename(staging, destination)
    fsync_tree(output)
    return reference(destination)


def verify_parallel_checkpoint(checkpoint):
    shared.checked_checkpoint(checkpoint)
    folder = Path(checkpoint['path']).parent
    document = read(checkpoint['path'])
    require(document['complete'] is True and document['optimizer_rng_sha256'] == checkpoint['optimizer_path_sha256'], 'checkpoint_complete_optimizer')
    binding = document['parallel']
    require(binding['schema'] == SCHEMA and sha(folder / 'PARALLEL.json') == binding['manifest_sha256']
            and sha(folder / 'PARALLEL_RNG.pt') == binding['payload_sha256'], 'parallel_sidecar_hashes')
    sidecar = read(folder / 'PARALLEL.json')
    require(sidecar['parallel_rng_sha256'] == binding['payload_sha256']
            and [row['branch'] for row in sidecar['ranks']] == list(BRANCHES)
            and sidecar['serial_adamw_equivalent'] is False, 'all8_rng_and_algorithm_binding')
    from organism_v6.orch_guided_bridge import AdapterIdentity
    AdapterIdentity.from_document(document['adapter'])
    return sidecar


def consolidate(*, root, activation_path, activation_sha256, branch, engine, optimizer,
                group, anchor_module, anchors, anchor_root, save_checkpoint, check, clock=time.time):
    """Collective owner hook. Never call on a running serial generation.

    ``check(stage)`` retains each owner's existing lease checks. No optimizer
    factory is accepted. Caller supplies native serializer on rank0 only.
    An unsuccessful call is terminal for this generation; never call again to
    replay it. Metadata-only recovery is a separate explicit operation.
    """
    root = Path(root).resolve(strict=True)
    collective = Collectives(engine.torch, group)
    lock, output, started, backend, context = None, None, False, None, None
    def acquire():
        nonlocal lock
        lock = (root / 'COORDINATOR.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        collective.owner_call('exclusive_existing_coordinator_lock', acquire)
        context = collective.all('activation_and_native_barrier', lambda: validate_activation(root, activation_path, activation_sha256, clock))
        document, state = context['document'], context['state']
        output = root / f"generation_{state['generation']:06d}" / 'sleep'
        def participant_check():
            require(branch == BRANCHES[collective.rank], 'fixed_F1_rank_order')
            require(context['certificates'][branch]['identity'] == process_identity(), 'certificate_is_this_native_process')
            require((collective.rank == 0 and callable(save_checkpoint)) or
                    (collective.rank != 0 and save_checkpoint is None), 'F1_only_serializer')
            if collective.rank == 0:
                require(str(Path(inspect.getsourcefile(save_checkpoint)).resolve()) in document['source_files'],
                        'owner_serializer_hook_source_pin')
            native_group = group if group is not None else engine.torch.distributed.group.WORLD
            options = getattr(native_group, 'options', None)
            if options is None:
                options = native_group._get_backend(engine.torch.device('cpu')).options
            timeout = options._timeout.total_seconds()
            require(math.isfinite(timeout) and 0 < timeout <= 180, 'finite_group_timeout_at_most180')
            check('parallel_preflight')
            validate_loaded(engine, optimizer, state, collective.rank)
        collective.all('existing_engine_optimizer_identity', participant_check)
        bindings = collective.gather(parallel.digest(document))
        require(len(set(bindings)) == 1, 'all_rank_activation_agreement')
        prepared = collective.all('native_row_encoding', lambda: parallel.prepare_native_cohort(
            shared=shared, anchor_module=anchor_module, root=root, tokenizer=engine.tokenizer,
            anchors=anchors, anchor_root=anchor_root, expected_config_sha256=document['pins']['CONFIG.json'],
            expected_state_sha256=document['pins']['STATE.json'], source_files=document['source_files']))
        backend = parallel.ParallelSleep(engine, optimizer, group=group,
            **{key: prepared[key] for key in ('encoded_new','encoded_old','encoded_anchors','schedule','source_manifest_sha256')})
        def begin():
            validate_activation(root, activation_path, activation_sha256, clock)
            write(output / 'START.json', dict(schema=SCHEMA, generation=state['generation'], owner='F1',
                started_unix=clock(), checkpoint=state['checkpoint'], activation_sha256=activation_sha256,
                participants=context['certificates'], serial_adamw_equivalent=False,
                source_manifest_sha256=backend.source_manifest_sha256, deadline_unix=context['deadline'],
                planned_optimizer_steps=backend.total_steps))
            write(output / 'ENCODING.json', prepared['manifest'])
        collective.owner_call('immutable_start', begin)
        started = True
        def lease():
            require(clock() < context['deadline'] - document['commit_reserve_seconds'], 'training_deadline_no_replay')
            check('shared_parallel_optimizer_update')
        while backend.cursor < backend.total_steps:
            metrics = backend.run(max_steps=1, check=lease)
            def progress():
                write(output / 'updates' / f'{backend.cursor:06d}.json',
                      dict(observed_unix=clock(), metrics=metrics, activation_sha256=activation_sha256))
            collective.owner_call('durable_step_receipt', progress)
        metrics = backend.metrics()
        payload = backend.checkpoint()
        def publish():
            require(clock() < context['deadline'], 'checkpoint_deadline')
            check('shared_parallel_checkpoint')
            for name, expected in document['pins'].items():
                checked_file(root / name, expected)
            for collection in (document['source_files'], prepared['manifest'].get('submission_files', {})):
                for name, expected in collection.items():
                    checked_file(name, expected)
            checkpoint = commit_checkpoint(output, state, backend, payload, metrics, save_checkpoint,
                                           context['certificates'], activation_sha256)
            require(clock() < context['deadline'], 'publication_deadline')
            next_state = advance_state(state, checkpoint, metrics)
            write(output / 'COMPLETE.json', dict(schema=SCHEMA, state=next_state, metrics=metrics,
                completed_unix=clock(), same_optimizer=True, source_checkpoint=state['checkpoint'],
                activation_sha256=activation_sha256))
            fsync_tree(output)
            require(clock() < context['deadline'], 'state_publication_deadline')
            write(root / 'STATE.json', next_state, replace=True)
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return next_state
        next_state = collective.owner_call('atomic_original_checkpoint_publication', publish)
        collective.all('all8_published_adapter_verified', lambda: validate_loaded(engine, optimizer, next_state, collective.rank))
        collective.all('all8_sidecar_verified', lambda: verify_parallel_checkpoint(next_state['checkpoint']))
        acknowledgments = collective.gather(dict(branch=branch, identity=process_identity(),
            checkpoint_sha256=next_state['checkpoint']['path_sha256'], adapter_sha256=backend._adapter_digest(),
            observed_unix=clock(), in_place=True))
        collective.owner_call('reload_ack_commit', lambda: write(output / 'ALL8_RELOAD.json',
            dict(schema=SCHEMA, state=next_state, acknowledgments=acknowledgments)))
        return dict(status='COMPLETE_ALL8_INPLACE', state=next_state, metrics=metrics)
    except Exception as error:
        if collective.rank == 0 and output is not None and (started or (output / 'START.json').exists()):
            failure = output / ('POST_COMMIT_FAILED.json' if (output / 'COMPLETE.json').exists() else 'FAILED.json')
            if not failure.exists():
                write(failure, dict(schema=SCHEMA, observed_unix=clock(), error=type(error).__name__ + ': ' + str(error),
                    last_completed_logical_step=backend.cursor if backend is not None else None,
                    replay_permitted=False, activation_sha256=activation_sha256,
                    original_state_preserved=not (output / 'COMPLETE.json').exists()))
        raise
    finally:
        if lock is not None:
            lock.close()


def recover_complete(root, *, activation_path, activation_sha256):
    """Explicit COMPLETE->STATE metadata recovery; no engines, replay or RNG reset.

    This does not authorize family continuation: owners must verify/reload the
    committed adapter and preserve/restore the hashed rank-local RNG sidecar.
    """
    root = Path(root).resolve(strict=True)
    document = read(checked_file(activation_path, activation_sha256))
    require(document['schema'] == SCHEMA and document['root'] == str(root), 'exact_recovery_activation')
    with shared.locked(root):
        for name in ('CONFIG.json','INITIALIZED.json','ADOPTION.json'):
            checked_file(root / name, document['pins'][name])
        output = root / f"generation_{document['generation']:06d}" / 'sleep'
        complete = read(output / 'COMPLETE.json')
        start = read(output / 'START.json')
        require(complete['schema'] == start['schema'] == SCHEMA
                and complete['activation_sha256'] == start['activation_sha256'] == activation_sha256
                and complete['same_optimizer'] is True and complete['completed_unix'] < start['deadline_unix'],
                'complete_activation_deadline_binding')
        sidecar = verify_parallel_checkpoint(complete['state']['checkpoint'])
        require(sidecar['metrics'] == complete['metrics'] and sidecar['source_checkpoint'] == complete['source_checkpoint'],
                'completed_sidecar_metrics_binding')
        state = read(root / 'STATE.json')
        if state == complete['state']:
            return dict(status='ALREADY_PUBLISHED', state=state, optimizer_updates_replayed=0)
        checked_file(root / 'STATE.json', document['pins']['STATE.json'])
        require(state['generation'] == document['generation'] and complete['source_checkpoint'] == state['checkpoint']
                and advance_state(state, complete['state']['checkpoint'], complete['metrics']) == complete['state'],
                'complete_lineage_and_actual_counters')
        write(root / 'STATE.json', complete['state'], replace=True)
        return dict(status='RECOVERED_COMPLETE_METADATA_ONLY', state=complete['state'], optimizer_updates_replayed=0)


def restore_committed(*, root, engine, optimizer, group, branch, checkpoint_sha256):
    """Explicit collective restore of a committed idle boundary, never a replay.

    Copies into existing engine parameters and F1 AdamW, preserving identities.
    Workers get no optimizer object. Restores Python/NumPy/Torch/local-CUDA RNG
    for each original group rank. Caller retains lease and activation authority.
    """
    root = Path(root).resolve(strict=True)
    collective = Collectives(engine.torch, group)
    lock = None
    def acquire():
        nonlocal lock
        lock = (root / 'COORDINATOR.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        collective.owner_call('restore_exclusive_lock', acquire)
        def preflight():
            state = read(root / 'STATE.json')
            require(state['generation'] > 0 and state['checkpoint']['path_sha256'] == checkpoint_sha256,
                    'exact_committed_checkpoint_only')
            require(not (root / f"generation_{state['generation']:06d}" / 'sleep/START.json').exists(),
                    'no_restore_over_unfinished_sleep')
            complete = read(root / f"generation_{state['generation'] - 1:06d}" / 'sleep/COMPLETE.json')
            require(complete['state'] == state and complete['same_optimizer'] is True, 'committed_complete_required')
            sidecar = verify_parallel_checkpoint(state['checkpoint'])
            require(branch == BRANCHES[collective.rank], 'same_rank_for_rng_restore')
            require((collective.rank == 0 and isinstance(optimizer, engine.torch.optim.AdamW))
                    or (collective.rank != 0 and optimizer is None), 'only_existing_owner_optimizer')
            parameters = tuple(engine.model.named_parameters())
            lora = {name:parameter for name,parameter in parameters if parallel.is_lora(name)}
            require(all(not parameter.requires_grad for name,parameter in parameters if name not in lora), 'frozen_base_required')
            if optimizer is not None:
                owned = [parameter for entry in optimizer.param_groups for parameter in entry['params']]
                require(len(owned) == len(lora) and {id(parameter) for parameter in owned} ==
                        {id(parameter) for parameter in lora.values()}, 'same_parameter_optimizer_identity')
            payload = engine.torch.load(Path(state['checkpoint']['path']).parent / 'PARALLEL_RNG.pt',
                                        map_location='cpu', weights_only=False)
            require(payload['metrics'] == sidecar['metrics'] and payload['metrics']['complete'] is True
                    and payload['binding'] == sidecar['schedule_binding_sha256']
                    and payload['metrics']['source_manifest_sha256'] == sidecar['source_manifest_sha256'],
                    'committed_payload_binding')
            require(set(payload['lora']) == set(lora) and len(payload['rng']) == 8, 'exact_lora_and_rank_rng')
            for name,parameter in lora.items():
                value = payload['lora'][name]
                require(value.shape == parameter.shape and value.dtype == parameter.dtype and
                        bool(engine.torch.isfinite(value).all()), 'restore_lora_schema')
            rng = payload['rng'][collective.rank]
            require(state_hash(rng) == sidecar['ranks'][collective.rank]['rng_sha256'], 'rank_rng_binding')
            require((rng['cuda'] is None) == (engine.torch.device(engine.device).type != 'cuda'), 'same_rng_device_kind')
            engine.verify_base()
            return state, payload, lora, parameters
        state, payload, lora, parameters = collective.all('restore_committed_preflight', preflight)
        require(len(set(collective.gather(checkpoint_sha256))) == 1, 'restore_all8_checkpoint_agreement')
        def restore():
            import random
            with engine.torch.no_grad():
                for name,parameter in lora.items():
                    parameter.copy_(payload['lora'][name])
            if collective.rank == 0:
                optimizer.load_state_dict(payload['optimizer'])
            rng = payload['rng'][collective.rank]
            random.setstate(rng['python'])
            engine.torch.set_rng_state(rng['cpu'])
            if rng['cuda'] is not None:
                engine.torch.cuda.set_rng_state(rng['cuda'],engine.device)
            if rng['numpy'] is not None:
                import numpy
                numpy.random.set_state(rng['numpy'])
            require(all(name == before and parameter is original for (name,parameter),(before,original)
                        in zip(engine.model.named_parameters(),parameters)), 'restore_keeps_parameter_objects')
            validate_loaded(engine,optimizer,state,collective.rank)
        collective.all('restore_inplace_optimizer_and_rank_rng', restore)
        return dict(status='COMMITTED_STATE_RESTORED_INPLACE', generation=state['generation'],
                    branch=branch, optimizer_updates_replayed=0)
    finally:
        if lock is not None:
            lock.close()
