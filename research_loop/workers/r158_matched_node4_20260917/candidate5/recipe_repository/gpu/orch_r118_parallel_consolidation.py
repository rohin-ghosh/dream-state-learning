"""Prospective all-eight consolidation and in-process Gloo launcher.

Owners call ``consolidate`` collectively with their existing raw engines, a
finite-timeout Gloo group and F1's existing AdamW (None on all seven workers).
Main supplies an immutable, generation-specific activation document only after
the previous serial commit/readouts and all eight safe handoffs. This module
can prepare an inert plan and explicitly arm it at that future boundary. It
never alters CONFIG or retries training. The explicit fresh-session dispatcher
executes owner-pinned strict-guard commands only after all eight safe releases.
"""

import argparse
import fcntl
import inspect
import json
import math
import os
import random
import subprocess
from pathlib import Path
from datetime import timedelta
import time

from gpu import orch_r116_shared_learner as shared
from gpu import orch_r116_shared_parallel_sleep as parallel


SCHEMA = 'R118_PARALLEL_CONSOLIDATION_V1'
HARD_END = 1789491720
TRAIN_END = 1789491600
if os.environ.get('ORCH_R119_LEASE_CLOCK') or os.environ.get('ORCH_R119_LEASE_CLOCK_SHA256'):
    from gpu import orch_r119_lease_clock
    _lease_clock = orch_r119_lease_clock.from_environment(os.environ, __file__)
    TRAIN_END = _lease_clock['train_end_unix']
    HARD_END = _lease_clock['hard_end_unix']
BRANCHES = shared.BRANCHES
LAUNCH_SCHEMA = 'R118_PARALLEL_INPLACE_LAUNCH_V1'
SESSION_SCHEMA = 'R118_PARALLEL_FRESH_EXEC_V1'
CAMPAIGN_SCHEMA = 'R118_PARALLEL_CAMPAIGN_V1'
require, read, sha, write = shared.require, shared.read, shared.sha, shared.write


def integration_contract():
    return dict(schema=SCHEMA, status='PROSPECTIVE_NOT_ACTIVATED',
        entrypoint='consolidate', rank_order=list(BRANCHES), process_launch=False,
        fresh_exec=dict(publisher='publish_fresh_sessions',dispatcher='dispatch_fresh_sessions',
            bootstrap='bootstrap_fresh_actor',collection_gate='wait_fresh_collection_go',
            authorization='PROSPECTIVE_ONLY: explicit dispatch after all8 committed+mounted+freshDEV+settledcursor+RELEASED',
            optimizer='Fresh F1 AdamW object restores exact saved state; same object within successor; peers None.',
            first_peer_rng='NEW deterministic session-binding/rank seeds, never old peer RNG preservation.',
            later_rng='Restore all8 hashed PARALLEL_RNG.pt; never reseed a parallel continuation.',
            env=['R118_PARALLEL_SESSION','R118_PARALLEL_SESSION_SHA256','R118_PARALLEL_BRANCH']),
        campaign=dict(publisher='prepare_campaign',watcher='watch_campaign',
            owner_callback='await_campaign_activation(campaign_path,campaign_sha256,branch,certificate,check)',
            safe_ref='safe_directory/generation_NNNNNN/BRANCH.ref.json',
            activation_ref='activation_directory/generation_NNNNNN.ref.json',
            automation='one Main CPU watcher; automatic all8 validated arm each generation; fixed cutoff; no failed-arm retry'),
        inplace_launcher='launch_at_boundary creates/destroys its own Gloo group inside existing owner processes; no fork/spawn/optimizer factory.',
        launch_workflow=['prepare_launch_plan: immutable PREPARED_NOT_ACTIVE, permits a future generation while serial runs.',
                         'arm_launch: explicit Main call after exact target STATE + all8 SAFE submissions + retained guard/FINAL identities; never current unfinished sleep.',
                         'launch_at_boundary: each owner atomically joins once, verifies all8, initializes loopback FileStore Gloo, consolidates, tears down group, returns same objects.'],
        launch_certificate_fields={
            'launch_device':['kind=cuda','physical=group rank','uuid=original GPU UUID','cuda_visible_devices=exact current single-GPU value'],
            'retained_supervision':['native_identity=same certificate identity','guard_identity=live guard boot_id/pid/start_ticks',
                'guard_binding={path,sha256} of existing identity/policy evidence',
                'final_identity_bindings=[{identity:live FINAL actor or timer identity,evidence:{path,sha256}}]',
                'owner_verified_safe_for_parallel=true after owner-specific checks']},
        launch_defaults=dict(join_timeout_seconds=90,collective_timeout_seconds=120,commit_reserve_seconds=120),
        launch_failure='Each namespace is single-use. Any JOIN/FAILED forbids automatic retry or serial fallback. Return to family readouts only after COMPLETE_ALL8_INPLACE.',
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


def live_identity(identity):
    require(type(identity['pid']) is int and type(identity['start_ticks']) is int, 'native_identity_types')
    fields = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
    require(identity['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            and identity['start_ticks'] == int(fields[19]), 'retained_process_identity_not_live')


def predecessor_released(identity):
    require(type(identity['pid']) is int and identity['pid'] > 0
            and type(identity['start_ticks']) is int and identity['start_ticks'] > 0,
            'predecessor_identity_types')
    if identity['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        return
    try:
        fields = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
    except FileNotFoundError:
        return
    require(int(fields[19]) != identity['start_ticks'] or fields[0] in ('Z', 'X'),
            'predecessor_still_live_no_dispatch')


def fresh_common(document):
    root = Path(document['root']).resolve(strict=True)
    require(set(document['pins']) == {'CONFIG.json','STATE.json','ADOPTION.json','INITIALIZED.json'},
            'fresh_exact_common_pins')
    for name, digest in document['pins'].items():
        checked_file(root / name, digest)
    for name, digest in document['source_files'].items():
        checked_file(name, digest)
    for module in (__file__, parallel.__file__, shared.__file__):
        require(str(Path(module).resolve()) in document['source_files'], 'fresh_runtime_source_pins')
    config, state = read(root / 'CONFIG.json'), read(root / 'STATE.json')
    require(state['generation'] > 0 and state == document['state']
            and state['config_sha256'] == document['pins']['CONFIG.json'], 'fresh_committed_STATE_only')
    require(config['owner'] == 'F1' and config['episodes_per_branch'] == 2
            and config['new_presentations'] == 16 and config['rehearsal_presentations'] == 1
            and config['anchor_loss_weight'] == .25 and config['anchor_sha256'] == shared.ANCHOR_SHA
            and set(config['branches']) == set(BRANCHES), 'fresh_unchanged_recipe')
    shared.checked_checkpoint(state['checkpoint'])
    checkpoint = read(state['checkpoint']['path'])
    require(checkpoint.get('complete') is True
            and checkpoint['optimizer_rng_sha256'] == state['checkpoint']['optimizer_path_sha256'],
            'fresh_committed_checkpoint_complete_required')
    complete = read(root / f"generation_{state['generation'] - 1:06d}" / 'sleep/COMPLETE.json')
    require(complete['state'] == state and complete['same_optimizer'] is True, 'fresh_previous_COMPLETE_required')
    require(not (root / f"generation_{state['generation']:06d}" / 'sleep/START.json').exists(),
            'fresh_no_unfinished_sleep_replay')
    return config, state


def preserved_boundary_reference(root, envelope, binding):
    path = checked_file(binding['path'],binding['sha256'])
    require(path.resolve().is_relative_to(root), 'fresh_boundary_under_own_root')
    relative = str(path.resolve().relative_to(root))
    require(envelope['preserved_files'].get(relative) == binding['sha256'], 'fresh_boundary_evidence_preserved')
    return path


def postcommit_evaluation_boundary(common, branch, owner, envelope, config, state):
    """Accept a retained failed/missing evaluation, never unfinished TRAIN."""
    root = Path(envelope['root']).resolve(strict=True)
    boundary = owner['boundary']
    disposition = read(preserved_boundary_reference(root,envelope,boundary['postcommit_eval_disposition']))
    cursor = read(preserved_boundary_reference(root,envelope,boundary['settled_cursor']))
    checkpoint_sha = state['checkpoint']['path_sha256']
    require(disposition['schema'] == 'R118_POSTCOMMIT_EVAL_DISPOSITION_V1'
            and disposition['status'] == 'TERMINAL_POSTCOMMIT_EVALUATION'
            and disposition['root'] == str(root) and disposition['branch'] == branch
            and disposition['generation'] == state['generation']
            and disposition['checkpoint_sha256'] == checkpoint_sha
            and disposition['replay_train'] is False, 'fresh_exact_postcommit_eval_disposition')
    previous = Path(common) / f"generation_{state['generation'] - 1:06d}"
    complete_ref, submission_ref = disposition['committed_sleep'], disposition['accepted_submission']
    require(Path(complete_ref['path']) == previous / 'sleep/COMPLETE.json'
            and Path(submission_ref['path']) == previous / (branch + '.json'), 'fresh_exact_already_trained_paths')
    complete = read(checked_file(complete_ref['path'],complete_ref['sha256']))
    submission = read(checked_file(submission_ref['path'],submission_ref['sha256']))
    require(complete['state'] == state and complete['same_optimizer'] is True
            and submission['generation'] == state['generation'] - 1 and submission['branch'] == branch
            and submission['checkpoint_sha256'] == complete['source_checkpoint']['path_sha256']
            and len(submission['episode_ids']) == len(set(submission['episode_ids'])) == 2
            and set(submission['episode_ids']).issubset(config['branches'][branch]['train_ids'])
            and submission['rows'], 'fresh_TRAIN_already_in_canonical_commit')
    require(not (Path(common) / f"generation_{state['generation']:06d}" / (branch + '.json')).exists(),
            'fresh_new_generation_submission_cannot_be_discarded')
    preserved_boundary_reference(root,envelope,disposition['native_terminal'])
    evaluations = disposition['evaluations']
    require(set(evaluations) == {'DEV','OPEN'}
            and set(evaluations.values()).issubset({'COMPLETE','FAILED','INTERRUPTED','MISSING','NOT_ATTEMPTED'})
            and any(value != 'COMPLETE' for value in evaluations.values()) and disposition['evaluation_evidence'],
            'fresh_truthful_terminal_eval_not_fake_COMPLETE')
    for evidence in disposition['evaluation_evidence']:
        preserved_boundary_reference(root,envelope,evidence)
    require(cursor['schema'] == 'R118_POSTCOMMIT_RECOVERED_CURSOR_V1'
            and cursor['root'] == str(root) and cursor['branch'] == branch
            and cursor['accepted_generation'] == state['generation'] - 1
            and cursor['accepted_submission_sha256'] == submission_ref['sha256']
            and cursor['checkpoint_sha256'] == checkpoint_sha
            and cursor['action'] == 'NEXT_NEW_CYCLE_AFTER_CANONICAL_BOOTSTRAP', 'fresh_recovered_cursor_binding')
    require(type(cursor['completed_train_cycle']) is int and cursor['completed_train_cycle'] >= 0
            and type(cursor['next_cycle']) is int
            and cursor['next_cycle'] == cursor['completed_train_cycle'] + 1 == envelope['next_cycle'],
            'fresh_next_new_cycle_no_replay')
    require(cursor['pending_train_calls'] == [] and cursor['pending_train_submissions'] == [],
            'fresh_unfinished_TRAIN_cannot_recover_as_eval')
    for kind in ('native','parent'):
        require(type(cursor[kind + '_used']) is int
                and cursor[kind + '_used'] == envelope['bounds'][kind + '_used'], 'fresh_recovery_charges_unchanged')
    require(boundary.get('canonical_reload_required') is True
            and boundary.get('mounted_checkpoint_sha256') in (None,checkpoint_sha),
            'fresh_recovery_requires_actual_canonical_bootstrap')


def pending_consolidation_boundary(common, branch, owner, envelope, config, state):
    """Validate two finished current-child episodes awaiting their first sleep."""
    root = Path(envelope['root']).resolve(strict=True)
    boundary = owner['boundary']
    binding = boundary['settled_pending_consolidation']
    pending = read(preserved_boundary_reference(root,envelope,binding))
    cursor = read(preserved_boundary_reference(root,envelope,boundary['settled_cursor']))
    checkpoint_sha = state['checkpoint']['path_sha256']
    require(pending['schema'] == 'R118_SETTLED_PENDING_CONSOLIDATION_V1'
            and pending['status'] == 'SETTLED_PENDING_CONSOLIDATION'
            and pending['root'] == str(root) and pending['branch'] == branch
            and pending['generation'] == state['generation']
            and pending['checkpoint_sha256'] == checkpoint_sha
            and pending['trained'] is False and pending['replay_calls'] is False,
            'fresh_exact_untrained_pending_generation')
    episodes = pending['episode_ids']
    require(len(episodes) == len(set(episodes)) == 2
            and set(episodes).issubset(config['branches'][branch]['train_ids'])
            and not set(episodes).intersection(config['excluded_ids']), 'fresh_pending_exact_two_TRAIN_episodes')
    completions = pending['episode_completions']
    require(len(completions) == 2 and {item['episode_id'] for item in completions} == set(episodes)
            and all(item['status'] == 'COMPLETE' for item in completions), 'fresh_no_mid_episode_pending_handoff')
    for item in completions:
        preserved_boundary_reference(root,envelope,item['evidence'])
    row_document = read(preserved_boundary_reference(root,envelope,pending['rows']))
    rows = row_document['rows'] if isinstance(row_document,dict) else row_document
    require(isinstance(rows,list) and rows, 'fresh_pending_nonempty_immutable_rows')
    terminal_sources = {}
    for terminal in pending['terminal_calls']:
        require(terminal['status'] in ('COMPLETE','FAILED','MISSING','CANCELLED'), 'fresh_pending_all_calls_terminal')
        path = preserved_boundary_reference(root,envelope,terminal)
        require(str(path) not in terminal_sources, 'fresh_pending_unique_terminal_call_paths')
        terminal_sources[str(path)] = terminal['sha256']
    sources = []
    for row in rows:
        shared.validate_row(row,config['branches'][branch],config['excluded_ids'],
                            generation=state['generation'],checkpoint_sha256=checkpoint_sha)
        require(row['episode_id'] in episodes
                and terminal_sources.get(row['source_call_path']) == row['source_call_sha256'],
                'fresh_pending_rows_from_terminal_calls_only')
        sources.append(row['source_call_sha256'])
    require(len(sources) == len(set(sources)) and {row['episode_id'] for row in rows} == set(episodes),
            'fresh_pending_no_duplicate_or_missing_episode_rows')
    old_sources = {row['source_call_sha256'] for row in config.get('initial_history',{}).get(branch,[])}
    for generation in range(state['generation']):
        previous = read(Path(common) / f'generation_{generation:06d}' / (branch + '.json'))
        old_sources.update(row['source_call_sha256'] for row in previous['rows'])
    require(not old_sources.intersection(sources), 'fresh_pending_excludes_already_trained_sources')
    expected = dict(branch=branch,generation=state['generation'],checkpoint_sha256=checkpoint_sha,
                    episode_ids=episodes,rows=rows)
    path = Path(common) / f"generation_{state['generation']:06d}" / (branch + '.json')
    submission = pending['submission']
    if submission is None:
        require(not path.exists(), 'fresh_pending_unpublished_must_be_absent')
    else:
        require(Path(submission['path']) == path
                and read(checked_file(path,submission['sha256'])) == expected, 'fresh_pending_exact_existing_submission')
    require(cursor['schema'] == 'R118_PENDING_CONSOLIDATION_CURSOR_V1'
            and cursor['root'] == str(root) and cursor['branch'] == branch
            and cursor['generation'] == state['generation'] and cursor['checkpoint_sha256'] == checkpoint_sha
            and cursor['action'] == 'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS', 'fresh_pending_cursor_binding')
    require(type(pending['cycle']) is int and pending['cycle'] >= 0
            and cursor['cycle'] == pending['cycle'] and type(cursor['next_cycle']) is int
            and cursor['next_cycle'] == pending['cycle'] + 1 == envelope['next_cycle'], 'fresh_pending_cycle_not_advanced_or_replayed')
    require(cursor['inflight_native_calls'] == [] and cursor['inflight_parent_calls'] == [], 'fresh_pending_no_inflight_calls')
    for kind in ('native','parent'):
        require(type(cursor[kind + '_used']) is int and cursor[kind + '_used'] == envelope['bounds'][kind + '_used'],
                'fresh_pending_charges_unchanged')
    require(boundary.get('canonical_reload_required') is True
            and boundary.get('mounted_checkpoint_sha256') in (None,checkpoint_sha), 'fresh_pending_canonical_reload_required')
    return dict(generation=state['generation'],cycle=pending['cycle'],next_cycle=cursor['next_cycle'],
                episode_ids=episodes,rows=rows,submission=submission,pending_reference=binding)


def fresh_releases(document):
    config, state = fresh_common(document)
    require(set(document['owners']) == set(BRANCHES), 'fresh_all8_owners_required')
    paths = set()
    for rank, branch in enumerate(BRANCHES):
        owner = document['owners'][branch]
        envelope = read(checked_file(**dict(path=owner['handoff']['path'], expected=owner['handoff']['sha256'])))
        root = Path(config['branches'][branch]['root']).resolve(strict=True)
        require(envelope['root'] == str(root) and envelope['bounds'] == owner['inherited_bounds'],
                'fresh_original_root_and_bounds')
        bounds = envelope['bounds']
        require(0 < document['startup_deadline_unix'] <= min(bounds['train_end_unix'], TRAIN_END)
                and bounds['train_end_unix'] <= bounds['hard_end_unix'] <= HARD_END,
                'fresh_original_lifetime')
        for kind in ('native','parent'):
            require(type(bounds[kind + '_used']) is int and type(bounds[kind + '_cap']) is int
                    and 0 <= bounds[kind + '_used'] <= bounds[kind + '_cap'], 'fresh_original_charges')
        release = read(checked_file(envelope['release']['path'], envelope['release']['sha256']))
        require(release.get('status') == 'RELEASED' and envelope['predecessors'], 'fresh_actual_RELEASED_required')
        for identity in envelope['predecessors']:
            predecessor_released(identity)
        require(type(envelope['next_cycle']) is int and envelope['next_cycle'] >= 0
                and envelope['preserved_files'], 'fresh_settled_cursor_and_preservation')
        for relative, digest in envelope['preserved_files'].items():
            target = root / relative
            require(not Path(relative).is_absolute() and '..' not in Path(relative).parts
                    and target.resolve().is_relative_to(root), 'fresh_preserved_path_escape')
            checked_file(target, digest)
        boundary = owner['boundary']
        require(boundary['committed_checkpoint_sha256'] == state['checkpoint']['path_sha256'], 'fresh_committed_checkpoint')
        require(sum(key in boundary for key in ('fresh_dev','postcommit_eval_disposition','settled_pending_consolidation')) == 1,
                'fresh_one_eval_disposition_path')
        if 'settled_pending_consolidation' in boundary:
            pending_consolidation_boundary(document['root'],branch,owner,envelope,config,state)
        elif 'postcommit_eval_disposition' in boundary:
            postcommit_evaluation_boundary(document['root'],branch,owner,envelope,config,state)
        else:
            require(boundary['mounted_checkpoint_sha256'] == state['checkpoint']['path_sha256'], 'fresh_committed_and_mounted_checkpoint')
            for name in ('fresh_dev','settled_cursor'):
                preserved_boundary_reference(root,envelope,boundary[name])
        command = owner['command']
        require(isinstance(command, list) and command and all(isinstance(item,str) and item for item in command)
                and Path(command[0]).is_absolute(), 'fresh_exact_exec_argv')
        require(Path(owner['cwd']).is_absolute() and Path(owner['cwd']).is_dir(), 'fresh_exact_cwd')
        require(owner['source_files'] and all(document['source_files'].get(name) == digest
                for name,digest in owner['source_files'].items()), 'fresh_owner_closure_pins')
        require(all(isinstance(key,str) and isinstance(value,str) and not key.startswith('R118_PARALLEL_')
                for key,value in owner['env'].items()), 'fresh_reserved_environment')
        bootstrap = Path(owner['bootstrap_path'])
        require(bootstrap.is_absolute() and bootstrap.resolve().is_relative_to(root)
                and str(bootstrap) not in paths, 'fresh_unique_owned_bootstrap_path')
        paths.add(str(bootstrap))
        device = owner['device']
        require(device['physical'] == rank and device['kind'] == document['mode'], 'fresh_original_rank_device')
        if document['mode'] == 'cuda':
            require(bool(device['uuid']), 'fresh_exact_GPU_uuid')
    return config, state


def publish_fresh_sessions(*, root, output, owners, source_files, startup_deadline_unix,
                           mode='cuda', clock=time.time):
    """Pin owner safe releases and exact strict-guard commands; never spawn here."""
    root, output = Path(root).resolve(strict=True), Path(output).absolute()
    require(not output.resolve().is_relative_to(root) and not output.exists(), 'fresh_session_outside_common')
    require(mode in ('cuda','cpu') and math.isfinite(startup_deadline_unix)
            and clock() < startup_deadline_unix <= TRAIN_END, 'fresh_fixed_startup_deadline')
    document = dict(schema=SESSION_SCHEMA,status='PUBLISHED_NOT_DISPATCHED',root=str(root),
        state=read(root / 'STATE.json'), owners=owners, source_files=source_files, mode=mode,
        startup_deadline_unix=startup_deadline_unix,
        pins={name:sha(root / name) for name in ('CONFIG.json','STATE.json','ADOPTION.json','INITIALIZED.json')},
        algorithm='average-gradient batch8 AdamW NOT serial-equivalent',
        first_peer_rng='NEW_DETERMINISTIC_ACTIVATION_RANK_STREAMS_NOT_OLD_PEER_RNG',
        owner_legacy_rng='SAVED_TORCH_CPU_CUDA; legacy Python/NumPy unsaved, explicitly seeded',
        next_parallel_rng='RESTORE_ALL8_HASHED_SIDECAR')
    fresh_releases(document)
    require(all(not Path(owner['bootstrap_path']).exists() for owner in owners.values()), 'fresh_no_old_bootstrap')
    binding = shared.digest(document)
    document['seed_binding_sha256'] = binding
    document['rank_seeds'] = {branch:int(shared.digest(dict(binding=binding,rank=rank))[:16],16) % (2**32)
                              for rank,branch in enumerate(BRANCHES)}
    write(output, document)
    return dict(path=str(output),sha256=sha(output),status=document['status'])


def fresh_session(path, digest):
    path = checked_file(path,digest)
    document = read(path)
    require(document['schema'] == SESSION_SCHEMA and document['status'] == 'PUBLISHED_NOT_DISPATCHED',
            'fresh_session_schema')
    core = {key:value for key,value in document.items() if key not in ('seed_binding_sha256','rank_seeds')}
    require(shared.digest(core) == document['seed_binding_sha256'], 'fresh_seed_binding')
    require(document['rank_seeds'] == {branch:int(shared.digest(dict(binding=document['seed_binding_sha256'],rank=rank))[:16],16) % (2**32)
                                     for rank,branch in enumerate(BRANCHES)}, 'fresh_rank_seeds')
    return document, path.parent / (path.stem + '.dispatch')


def bootstrap_fresh_actor(*, root, branch, engine, optimizer, session_path, session_sha256):
    """Startup-only exact restore. No Gloo, optimizer step, model reload or call."""
    document, control = fresh_session(session_path,session_sha256)
    require(str(Path(root).resolve(strict=True)) == document['root'] and branch in BRANCHES, 'fresh_actor_binding')
    require(time.time() < document['startup_deadline_unix'] and not (control / 'FAILED.json').exists(), 'fresh_startup_deadline_or_failure')
    start = read(control / 'START.json')
    require(start['session_sha256'] == session_sha256, 'fresh_dispatch_before_bootstrap')
    live_identity(start['identity'])
    _, state = fresh_common(document)
    owner, rank = document['owners'][branch], BRANCHES.index(branch)
    receipt_path = Path(owner['bootstrap_path'])
    require(not receipt_path.exists(), 'fresh_bootstrap_once_no_rng_reset')
    write(control / (branch + '.BOOTSTRAP_START.json'),dict(identity=process_identity(),session_sha256=session_sha256))
    require(not engine.torch.distributed.is_initialized(), 'fresh_owner_must_not_initialize_Gloo')
    device = engine.torch.device(engine.device)
    require(device.type == document['mode'], 'fresh_actual_engine_device')
    if device.type == 'cuda':
        require(engine.torch.cuda.device_count() == 1, 'fresh_single_original_GPU')
        properties = engine.torch.cuda.get_device_properties(device)
        require(str(properties.uuid) == owner['device']['uuid'], 'fresh_GPU_uuid_mismatch')
        require(all(callable(getattr(engine.model,name,None)) for name in
                    ('gradient_checkpointing_enable','enable_input_require_grads','disable_input_require_grads')),
                'fresh_native_serial_training_path_required')
    parameters = tuple(engine.model.named_parameters())
    lora = {name:parameter for name,parameter in parameters if parallel.is_lora(name)}
    require(lora and all(not parameter.requires_grad for name,parameter in parameters if name not in lora), 'fresh_frozen_base')
    from organism_v6.orch_guided_bridge import AdapterIdentity
    checkpoint = read(state['checkpoint']['path'])
    require(state_hash(lora) == AdapterIdentity.from_document(checkpoint['adapter']).state_sha256,
            'fresh_exact_loaded_canonical_LoRA')
    original = engine.torch.load(state['checkpoint']['optimizer_path'],map_location='cpu',weights_only=False)
    require(set(original) == {'optimizer','cpu_rng','cuda_rng'}, 'fresh_original_optimizer_RNG_schema')
    if rank == 0:
        require(isinstance(optimizer,engine.torch.optim.AdamW), 'fresh_only_F1_AdamW')
        owned = [parameter for group in optimizer.param_groups for parameter in group['params']]
        require(len(owned) == len(lora) and all(actual is expected for actual,expected in zip(owned,lora.values())),
                'fresh_optimizer_exact_existing_LoRA_parameters')
        optimizer.load_state_dict(original['optimizer'])
    else:
        require(optimizer is None, 'fresh_peers_have_no_optimizer')
    validate_loaded(engine,optimizer,state,rank)
    seed = document['rank_seeds'][branch]
    if 'parallel' in checkpoint:
        verify_parallel_checkpoint(state['checkpoint'])
        payload = engine.torch.load(Path(state['checkpoint']['path']).parent / 'PARALLEL_RNG.pt',map_location='cpu',weights_only=False)
        require(len(payload['rng']) == 8 and state_hash(payload['lora']) == state_hash(lora)
                and state_hash(payload['optimizer']) == state_hash(original['optimizer']), 'fresh_all8_sidecar_continuity')
        rng = payload['rng'][rank]
        random.setstate(rng['python'])
        engine.torch.set_rng_state(rng['cpu'])
        if device.type == 'cuda':
            require(rng['cuda'] is not None, 'fresh_saved_rank_CUDA_RNG_required')
            engine.torch.cuda.set_rng_state(rng['cuda'],device)
        if rng['numpy'] is not None:
            import numpy
            numpy.random.set_state(rng['numpy'])
        provenance, seed = 'RESTORED_ALL8_PARALLEL_SIDECAR', None
    else:
        random.seed(seed)
        import numpy
        numpy.random.seed(seed)
        if rank == 0:
            engine.torch.set_rng_state(original['cpu_rng'])
            if device.type == 'cuda':
                require(len(original['cuda_rng']) == 1, 'fresh_single_F1_saved_CUDA_stream')
                engine.torch.cuda.set_rng_state(original['cuda_rng'][0],device)
            provenance = 'RESTORED_F1_TORCH_NEW_UNSAVED_PYTHON_NUMPY'
        else:
            engine.torch.manual_seed(seed)
            if device.type == 'cuda':
                engine.torch.cuda.manual_seed(seed)
            provenance = 'NEW_DETERMINISTIC_RANK_STREAM_NOT_OLD_PEER_RNG'
    import numpy
    require(all(name == before and parameter is original_parameter for (name,parameter),(before,original_parameter)
                in zip(engine.model.named_parameters(),parameters)), 'fresh_same_engine_parameter_identity')
    result = dict(schema=SESSION_SCHEMA,status='BOOTSTRAP_VERIFIED',branch=branch,rank=rank,
        session_sha256=session_sha256,identity=process_identity(),generation=state['generation'],
        checkpoint_sha256=state['checkpoint']['path_sha256'],adapter_state_sha256=state_hash(lora),
        optimizer_sha256=state_hash(optimizer.state_dict()) if optimizer is not None else None,
        optimizer_steps=[float(item['step']) for item in optimizer.state.values() if 'step' in item] if optimizer is not None else [],
        optimizer_count=int(optimizer is not None),optimizer_updates_replayed=0,
        postcommit_eval_disposition=owner['boundary'].get('postcommit_eval_disposition'),
        settled_pending_consolidation=owner['boundary'].get('settled_pending_consolidation'),
        startup_action=('RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS'
                        if 'settled_pending_consolidation' in owner['boundary'] else 'COLLECT_NEW_TWO_EPISODES'),
        canonical_adapter_actually_verified=True,
        rng_provenance=provenance,new_stream_seed=seed,seed_binding_sha256=document['seed_binding_sha256'],
        rng_sha256=state_hash(dict(python=random.getstate(),numpy=numpy.random.get_state(),
            cpu=engine.torch.get_rng_state(),cuda=engine.torch.cuda.get_rng_state(device) if device.type == 'cuda' else None)),
        torch_cpu_rng_sha256=state_hash(engine.torch.get_rng_state()),
        training_path='per-sleep same LoRA train + nonreentrant checkpointing + input gradients; no context trimming',
        device=owner['device'],time_unix=time.time())
    write(receipt_path,result)
    return result


def wait_fresh_collection_go(session_path, session_sha256, branch, check=None):
    document, control = fresh_session(session_path,session_sha256)
    require(branch in BRANCHES, 'fresh_known_branch')
    while True:
        if check is not None:
            check('fresh_all8_collection_gate')
        require(not (control / 'FAILED.json').exists(), 'fresh_dispatch_failed_no_collection')
        if (control / 'GO.json').exists():
            go = read(control / 'GO.json')
            require(go['session_sha256'] == session_sha256 and set(go['bootstraps']) == set(BRANCHES), 'fresh_exact_all8_GO')
            binding = go['bootstraps'][branch]
            own = read(checked_file(binding['path'],binding['sha256']))
            require(own['identity'] == process_identity() and own['branch'] == branch, 'fresh_GO_same_native')
            return go
        require(time.time() < document['startup_deadline_unix'], 'fresh_fixed_startup_timeout')
        time.sleep(.1)


def resume_pending_consolidation(*, root, branch, session_path, session_sha256, check=None):
    """After bootstrap GO, reuse settled rows; never collect or train here."""
    document, control = fresh_session(session_path,session_sha256)
    require(str(Path(root).resolve(strict=True)) == document['root'] and branch in BRANCHES, 'pending_resume_exact_session')
    owner = document['owners'][branch]
    require('settled_pending_consolidation' in owner['boundary'], 'pending_resume_only_declared_branches')
    wait_fresh_collection_go(session_path,session_sha256,branch,check=check)
    bootstrap = read(owner['bootstrap_path'])
    require(bootstrap['identity'] == process_identity() and bootstrap['session_sha256'] == session_sha256
            and bootstrap['startup_action'] == 'RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS',
            'pending_resume_same_bootstrapped_native')
    config, state = fresh_common(document)
    envelope = read(checked_file(owner['handoff']['path'],owner['handoff']['sha256']))
    prepared = pending_consolidation_boundary(document['root'],branch,owner,envelope,config,state)
    require(time.time() < min(TRAIN_END,envelope['bounds']['train_end_unix']), 'pending_resume_original_TRAIN_bound')
    write(control / (branch + '.PENDING_RESUME_START.json'),dict(session_sha256=session_sha256,
        pending=prepared['pending_reference'],identity=process_identity(),time_unix=time.time()))
    try:
        if check is not None:
            check('resume_settled_pending_submission_no_collection')
        submission = prepared['submission']
        reused = submission is not None
        if submission is None:
            submission = shared.submit(Path(root),branch,prepared['generation'],state['checkpoint']['path_sha256'],
                                       prepared['episode_ids'],prepared['rows'])
        result = dict(status='PENDING_CONSOLIDATION_READY_NO_NEW_CALLS',branch=branch,generation=prepared['generation'],
            cycle=prepared['cycle'],next_cycle=prepared['next_cycle'],episode_ids=prepared['episode_ids'],
            submission=submission,existing_submission_reused=reused,rows_sha256=shared.digest(prepared['rows']),
            row_count=len(prepared['rows']),new_native_calls=0,optimizer_updates=0,session_sha256=session_sha256,
            identity=process_identity(),time_unix=time.time())
        write(control / (branch + '.PENDING_RESUME_COMPLETE.json'),result)
        return dict(result,rows=prepared['rows'])
    except BaseException as error:
        write(control / (branch + '.PENDING_RESUME_FAILED.json'),dict(session_sha256=session_sha256,
            error=type(error).__name__ + ': ' + str(error),time_unix=time.time(),no_retry=True))
        raise


def dispatch_fresh_sessions(*, session_path, session_sha256):
    """Explicit single-use owner-command launch; never activates from publication."""
    document, control = fresh_session(session_path,session_sha256)
    require(time.time() < document['startup_deadline_unix'], 'fresh_dispatch_deadline')
    with (Path(document['root']) / 'COORDINATOR.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        fresh_releases(document)
        require(all(not Path(owner['bootstrap_path']).exists() for owner in document['owners'].values()), 'fresh_no_old_bootstrap')
        write(control / 'START.json',dict(session_sha256=session_sha256,identity=process_identity(),time_unix=time.time()))
        launched, receipts = {}, {}
        try:
            for branch in BRANCHES:
                owner = document['owners'][branch]
                environment = dict(os.environ,**owner['env'])
                environment.update(R118_PARALLEL_SESSION=str(Path(session_path).absolute()),
                    R118_PARALLEL_SESSION_SHA256=session_sha256,R118_PARALLEL_BRANCH=branch)
                with (control / (branch + '.log')).open('xb') as log:
                    process = subprocess.Popen(owner['command'],cwd=owner['cwd'],env=environment,
                        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                launched[branch] = process
                write(control / (branch + '.EXEC.json'),dict(branch=branch,pid=process.pid,
                    command_sha256=shared.digest(owner['command']),session_sha256=session_sha256,time_unix=time.time()))
            while len(receipts) < 8:
                require(time.time() < document['startup_deadline_unix'], 'fresh_fixed_startup_timeout')
                for branch, process in launched.items():
                    require(process.poll() in (None,0), 'fresh_owner_command_failed_' + branch)
                    owner = document['owners'][branch]
                    path = Path(owner['bootstrap_path'])
                    if not path.exists():
                        continue
                    receipt = read(path)
                    require(receipt['status'] == 'BOOTSTRAP_VERIFIED' and receipt['session_sha256'] == session_sha256
                            and receipt['branch'] == branch and receipt['rank'] == BRANCHES.index(branch)
                            and receipt['checkpoint_sha256'] == document['state']['checkpoint']['path_sha256']
                            and receipt['optimizer_count'] == int(branch == 'F1'), 'fresh_bound_native_bootstrap')
                    expected_action = ('RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS'
                        if 'settled_pending_consolidation' in owner['boundary'] else 'COLLECT_NEW_TWO_EPISODES')
                    require(receipt['startup_action'] == expected_action, 'fresh_exact_startup_action')
                    live_identity(receipt['identity'])
                    receipts[branch] = dict(path=str(path),sha256=sha(path))
                if len(receipts) < 8:
                    time.sleep(.1)
            require(len({tuple(read(item['path'])['identity'][key] for key in ('boot_id','pid','start_ticks'))
                         for item in receipts.values()}) == 8, 'fresh_eight_distinct_natives')
            fresh_common(document)
            result = dict(status='ALL8_BOOTSTRAPPED_COLLECTION_GO',session_sha256=session_sha256,
                          bootstraps=receipts,time_unix=time.time(),optimizer_count=1)
            write(control / 'GO.json',result)
            return result
        except BaseException as error:
            write(control / 'FAILED.json',dict(session_sha256=session_sha256,error=type(error).__name__ + ': ' + str(error),
                  spawned={branch:process.pid for branch,process in launched.items()},time_unix=time.time(),retry_allowed=False))
            raise


def prepare_campaign(*, root, output, first_generation, pins, source_files, activation_directory,
                     safe_directory, deadline_unix, mode='CUDA_INPLACE', join_timeout_seconds=90,
                     collective_timeout_seconds=120, commit_reserve_seconds=120):
    root, output = Path(root).resolve(strict=True), Path(output).absolute()
    require(type(first_generation) is int and first_generation >= 1
            and first_generation >= read(root / 'STATE.json')['generation'], 'campaign_future_first_generation')
    require(not output.resolve().is_relative_to(root), 'campaign_outside_COMMON')
    require(set(pins) == {'CONFIG.json','ADOPTION.json','INITIALIZED.json'}, 'campaign_lineage_pins')
    for name,digest in pins.items():
        checked_file(root / name,digest)
    for name,digest in source_files.items():
        checked_file(name,digest)
    require(str(Path(__file__).resolve()) in source_files, 'campaign_coordinator_pinned')
    for directory in (activation_directory,safe_directory):
        require(Path(directory).is_absolute() and not Path(directory).resolve().is_relative_to(root), 'campaign_inboxes_outside_COMMON')
    require(Path(activation_directory).resolve() != Path(safe_directory).resolve(), 'campaign_distinct_inboxes')
    require(mode in ('CUDA_INPLACE','CPU_TEST_ONLY') and math.isfinite(deadline_unix)
            and time.time() < deadline_unix <= TRAIN_END, 'campaign_fixed_original_deadline')
    require(type(join_timeout_seconds) is int and 5 <= join_timeout_seconds <= 180
            and type(collective_timeout_seconds) is int and 5 <= collective_timeout_seconds <= 180
            and type(commit_reserve_seconds) is int and 30 <= commit_reserve_seconds <= 600, 'campaign_finite_timeouts')
    document = dict(schema=CAMPAIGN_SCHEMA,status='PREPARED_NOT_ACTIVE',root=str(root),
        first_generation=first_generation,pins=pins,source_files=source_files,
        activation_directory=str(activation_directory),safe_directory=str(safe_directory),
        deadline_unix=deadline_unix,mode=mode,join_timeout_seconds=join_timeout_seconds,
        collective_timeout_seconds=collective_timeout_seconds,commit_reserve_seconds=commit_reserve_seconds,
        retry_after_attempt=False,actors_launched_by_watcher=False)
    write(output,document)
    return dict(path=str(output),sha256=sha(output),status=document['status'])


def campaign_document(path, digest):
    document = read(checked_file(path,digest))
    require(document['schema'] == CAMPAIGN_SCHEMA and document['status'] == 'PREPARED_NOT_ACTIVE', 'campaign_schema')
    for name,value in document['pins'].items():
        checked_file(Path(document['root']) / name,value)
    for name,value in document['source_files'].items():
        checked_file(name,value)
    return document, Path(path).parent / (Path(path).stem + '.watch')


def publish_campaign_safe(campaign_path, campaign_sha256, branch, certificate):
    document, control = campaign_document(campaign_path,campaign_sha256)
    require(branch in BRANCHES and time.time() < document['deadline_unix']
            and not (control / 'FAILED.json').exists(), 'campaign_live_bounded_publication')
    native = read(checked_file(certificate['path'],certificate['sha256']))
    state = read(Path(document['root']) / 'STATE.json')
    require(native['branch'] == branch and native['generation'] == state['generation'] >= document['first_generation']
            and native['checkpoint_sha256'] == state['checkpoint']['path_sha256']
            and native['status'] == 'SAFE_FOR_PARALLEL', 'campaign_exact_current_certificate')
    live_identity(native['identity'])
    path = Path(document['safe_directory']) / f"generation_{state['generation']:06d}" / (branch + '.ref.json')
    if path.exists():
        require(read(path) == certificate, 'campaign_cannot_replace_published_certificate')
    else:
        write(path,certificate)
    return dict(path=str(path),sha256=sha(path))


def await_campaign_activation(campaign_path, campaign_sha256, branch, certificate, check=None):
    publish_campaign_safe(campaign_path,campaign_sha256,branch,certificate)
    document, control = campaign_document(campaign_path,campaign_sha256)
    generation = read(certificate['path'])['generation']
    inbox = Path(document['activation_directory']) / f'generation_{generation:06d}.ref.json'
    while True:
        if check is not None:
            check('parallel_campaign_activation_wait')
        require(not (control / 'FAILED.json').exists(), 'campaign_failed_no_retry')
        require(time.time() < document['deadline_unix'], 'campaign_original_deadline')
        if inbox.exists():
            activation = read(inbox)
            native = read(checked_file(activation['path'],activation['sha256']))
            require(native['generation'] == generation and native['participants'][branch] == certificate,
                    'campaign_exact_certificate_activation')
            return activation
        time.sleep(.2)


def watch_campaign(*, campaign_path, campaign_sha256, session_path, session_sha256,
                   clock=time.time, pause=time.sleep):
    """Main's one CPU watcher: one automatic arm per genuine all8 generation."""
    document, control = campaign_document(campaign_path,campaign_sha256)
    session, dispatch = fresh_session(session_path,session_sha256)
    go = read(dispatch / 'GO.json')
    require(go['status'] == 'ALL8_BOOTSTRAPPED_COLLECTION_GO' and go['session_sha256'] == session_sha256
            and set(go['bootstraps']) == set(BRANCHES), 'campaign_after_actual_all8_startup_GO')
    require(session['root'] == document['root'] and session['state']['generation'] == document['first_generation'],
            'campaign_fresh_session_generation')
    require(all(document['source_files'].get(name) == digest for name,digest in session['source_files'].items()),
            'campaign_same_frozen_session_closure')
    require(document['deadline_unix'] <= min(owner['inherited_bounds']['train_end_unix'] for owner in session['owners'].values()),
            'campaign_inherited_TRAIN_end')
    require(clock() < document['deadline_unix'], 'campaign_original_deadline')
    write(control / 'START.json',dict(campaign_sha256=campaign_sha256,session_sha256=session_sha256,
                                    identity=process_identity(),time_unix=clock()))
    root, generation = Path(document['root']), document['first_generation']
    armed = False
    try:
        while clock() < document['deadline_unix'] - document['commit_reserve_seconds']:
            require(not list(dispatch.glob('*.PENDING_RESUME_FAILED.json')), 'campaign_pending_resume_failed_no_retry')
            state = read(root / 'STATE.json')
            folder = control / f'generation_{generation:06d}'
            sleep = root / f'generation_{generation:06d}' / 'sleep'
            require(not list(folder.glob('FAILED_*.json')) and not (sleep / 'FAILED.json').exists(),
                    'campaign_failed_generation_no_retry')
            require(state['generation'] in (generation,generation + 1), 'campaign_no_skipped_generation')
            if state['generation'] == generation + 1:
                complete = read(sleep / 'COMPLETE.json')
                require(armed and complete['state'] == state and complete['same_optimizer'] is True,
                        'campaign_only_own_exact_COMPLETE_advances')
                generation, armed = generation + 1, False
                continue
            safe = Path(document['safe_directory']) / f'generation_{generation:06d}'
            found = [branch for branch in BRANCHES if (safe / (branch + '.ref.json')).exists()
                     and (root / f'generation_{generation:06d}' / (branch + '.json')).exists()]
            phase = 'ARMED_WAIT_COMMIT' if armed else 'WAIT_ALL8_SAFE_AND_SUBMISSIONS'
            if not armed and len(found) == 8:
                require(not (sleep / 'START.json').exists(), 'campaign_existing_START_no_replay')
                participants = {branch:read(safe / (branch + '.ref.json')) for branch in BRANCHES}
                write(folder / 'ARM_ATTEMPT.json',dict(generation=generation,participants=participants,time_unix=clock()))
                plan = prepare_launch_plan(root=root,output=folder / 'LAUNCH_PLAN.json',generation=generation,
                    **{key:document[key] for key in ('pins','source_files','mode','deadline_unix',
                        'join_timeout_seconds','collective_timeout_seconds','commit_reserve_seconds')})
                activation = arm_launch(plan_path=plan['path'],plan_sha256=plan['sha256'],participants=participants,clock=clock)
                write(Path(document['activation_directory']) / f'generation_{generation:06d}.ref.json',activation)
                armed, phase = True, 'ARMED_WAIT_COMMIT'
            if armed:
                activation = read(folder / 'ACTIVATION.json')
                joins = len(list(folder.glob('JOIN_*.json')))
                require(clock() < activation['launch']['join_deadline_unix'] or joins == 8,
                        'campaign_missing_join_terminal_no_retry')
            write(control / 'HEARTBEAT.json',dict(generation=generation,phase=phase,ready_branches=found,
                deadline_unix=document['deadline_unix'],time_unix=clock(),armed=armed),replace=True)
            pause(1)
        result = dict(status='DEADLINE_NO_MORE_ARMS',generation=generation,last_generation_armed=armed,
                      deadline_unix=document['deadline_unix'],time_unix=clock(),signals_sent=0)
        write(control / 'TERMINAL.json',result)
        return result
    except BaseException as error:
        write(control / 'FAILED.json',dict(generation=generation,error=type(error).__name__ + ': ' + str(error),
            time_unix=clock(),no_retry=True,signals_sent=0))
        raise


def prepare_launch_plan(*, root, output, generation, pins, source_files, deadline_unix,
                        mode='CUDA_INPLACE', join_timeout_seconds=90,
                        collective_timeout_seconds=120, commit_reserve_seconds=120):
    """Write an inert plan outside COMMON. No readiness, signals, PG or GPU work.

    ``pins`` contains CONFIG/ADOPTION/INITIALIZED only: future STATE and native
    identities are bound by ``arm_launch`` after the owners' real safe handoffs.
    A plan may target g+1 while serial g is still running; it cannot activate g.
    """
    root = Path(root).resolve(strict=True)
    output = Path(output)
    require(output.is_absolute() and output.name == 'LAUNCH_PLAN.json'
            and not output.resolve().is_relative_to(root), 'inert_plan_outside_COMMON')
    require(set(pins) == {'CONFIG.json','ADOPTION.json','INITIALIZED.json'}, 'immutable_launch_lineage_pins')
    for name, expected in pins.items():
        checked_file(root / name, expected)
    require(mode in ('CUDA_INPLACE','CPU_TEST_ONLY'), 'explicit_device_mode')
    require(type(generation) is int and generation >= read(root / 'STATE.json')['generation'], 'future_generation_not_past')
    require(type(join_timeout_seconds) is int and 5 <= join_timeout_seconds <= 180
            and type(collective_timeout_seconds) is int and 5 <= collective_timeout_seconds <= 180
            and type(commit_reserve_seconds) is int and 30 <= commit_reserve_seconds <= 600, 'finite_launch_timeouts')
    require(math.isfinite(deadline_unix) and deadline_unix <= TRAIN_END, 'original_launch_deadline')
    for path, expected in source_files.items():
        checked_file(path, expected)
    require(str(Path(__file__).resolve()) in source_files, 'launcher_source_pinned')
    config = read(root / 'CONFIG.json')
    require(config['owner'] == 'F1' and config['anchor_sha256'] == shared.ANCHOR_SHA
            and set(config['branches']) == set(BRANCHES), 'same_F1_and_42anchors')
    document = dict(schema=LAUNCH_SCHEMA,status='PREPARED_NOT_ACTIVE',root=str(root),generation=generation,
        pins=dict(pins),source_files=dict(source_files),mode=mode,deadline_unix=deadline_unix,
        join_timeout_seconds=join_timeout_seconds,collective_timeout_seconds=collective_timeout_seconds,
        commit_reserve_seconds=commit_reserve_seconds,
        rank_order=list(BRANCHES),physical_slots=dict(zip(BRANCHES,range(8))),
        branch_roots={branch:config['branches'][branch]['root'] for branch in BRANCHES},
        rendezvous='NEW_SINGLE_USE_FILESTORE_LOOPBACK_GLOO',activation_authorized=False,
        optimizer='existing_F1_AdamW_peers_None',serial_adamw_equivalent=False)
    write(output, document)
    return dict(path=str(output),sha256=sha(output),status=document['status'])


def validate_launch_participant(certificate, branch, mode):
    rank = BRANCHES.index(branch)
    device = certificate['launch_device']
    require(device['physical'] == rank, 'original_branch_physical_slot')
    if mode == 'CUDA_INPLACE':
        require(device['kind'] == 'cuda' and isinstance(device['uuid'],str)
                and device['uuid'].startswith('GPU-') and device['cuda_visible_devices'] in (str(rank),device['uuid']),
                'exact_existing_single_GPU_visibility')
    else:
        require(device == dict(kind='cpu',physical=rank,cuda_visible_devices=''), 'CPU_fixture_no_GPU_binding')
    supervision = certificate['retained_supervision']
    live_identity(supervision['guard_identity'])
    require(supervision['native_identity'] == certificate['identity']
            and supervision['final_identity_bindings'], 'native_and_FINAL_identity_bindings_required')
    for entry in supervision['final_identity_bindings']:
        live_identity(entry['identity'])
        checked_file(entry['evidence']['path'],entry['evidence']['sha256'])
    checked_file(supervision['guard_binding']['path'],supervision['guard_binding']['sha256'])
    require(supervision['owner_verified_safe_for_parallel'] is True, 'owner_final_guard_handoff_required')


def arm_launch(*, plan_path, plan_sha256, participants, clock=time.time):
    """Explicit future-boundary operation, not called by plan preparation.

    Main supplies eight owner-produced SAFE references. Each extends the base
    certificate with launch_device and retained_supervision (live guard/native,
    live FINAL actor/timer plus hashed identity/policy evidence). This validates
    their bindings, not family-specific safe-drain semantics. Writes only the
    new sidecar namespace; no CONFIG/STATE mutation or actor signals.
    """
    plan_path = checked_file(plan_path,plan_sha256)
    plan = read(plan_path)
    require(plan['schema'] == LAUNCH_SCHEMA and plan['status'] == 'PREPARED_NOT_ACTIVE'
            and plan['rank_order'] == list(BRANCHES), 'exact_inert_launch_plan')
    root = Path(plan['root']).resolve(strict=True)
    folder = plan_path.parent
    require(not folder.is_relative_to(root), 'launch_namespace_outside_COMMON')
    with (root / 'COORDINATOR.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = read(root / 'STATE.json')
        require(state['generation'] == plan['generation'], 'future_STATE_not_committed_yet')
        require(set(participants) == set(BRANCHES), 'all8_ready_before_arm')
        for branch in BRANCHES:
            entry = participants[branch]
            certificate = read(checked_file(entry['path'],entry['sha256']))
            validate_launch_participant(certificate,branch,plan['mode'])
        for name, expected in plan['pins'].items():
            checked_file(root / name,expected)
        deadline = min(plan['deadline_unix'],*(read(participants[branch]['path'])['bounds']['train_end_unix'] for branch in BRANCHES))
        now = clock()
        join_end = min(now + plan['join_timeout_seconds'],deadline - plan['commit_reserve_seconds'])
        require(join_end > now and now + plan['collective_timeout_seconds'] < deadline - plan['commit_reserve_seconds'],
                'insufficient_original_bound_for_group_start')
        require(not (folder / 'ACTIVATION.json').exists() and not (folder / 'RENDEZVOUS').exists()
                and not list(folder.glob('JOIN_*.json')), 'single_use_launch_namespace')
        activation = dict(schema=SCHEMA,status='ACTIVATE_PARALLEL_AT_SAFE_BOUNDARY',root=str(root),generation=state['generation'],
            pins=dict(plan['pins'],**{'STATE.json':sha(root / 'STATE.json')}),source_files=plan['source_files'],
            participants=participants,deadline_unix=deadline,commit_reserve_seconds=plan['commit_reserve_seconds'],
            launch=dict(schema=LAUNCH_SCHEMA,plan_path=str(plan_path),plan_sha256=plan_sha256,mode=plan['mode'],
                        store_path=str(folder / 'RENDEZVOUS'),armed_unix=now,join_deadline_unix=join_end,
                        collective_timeout_seconds=plan['collective_timeout_seconds'],rank_order=list(BRANCHES)))
        pending = folder / 'ACTIVATION.pending.json'
        write(pending,activation)
        validate_activation(root,pending,sha(pending),clock)
        os.rename(pending,folder / 'ACTIVATION.json')
        fsync_tree(folder)
        return dict(path=str(folder / 'ACTIVATION.json'),sha256=sha(folder / 'ACTIVATION.json'),
                    generation=state['generation'],status='ARMED_NO_PROCESSES_LAUNCHED',join_deadline_unix=join_end)


def launch_status(activation_path, activation_sha256):
    activation_path = checked_file(activation_path,activation_sha256)
    document = read(activation_path)
    folder = activation_path.parent
    return dict(schema=LAUNCH_SCHEMA,generation=document['generation'],activation_sha256=activation_sha256,
        joined=[branch for branch in BRANCHES if (folder / ('JOIN_' + branch + '.json')).exists()],
        returned=[branch for branch in BRANCHES if (folder / ('RETURN_' + branch + '.json')).exists()],
        failures=[path.name for path in sorted(folder.glob('FAILED_*.json'))],
        join_deadline_unix=document['launch']['join_deadline_unix'],read_only=True)


def launch_at_boundary(*, activation_path, activation_sha256, branch, engine, optimizer,
                       anchor_module, anchor_root, save_checkpoint, check, anchors=None,
                       clock=time.time, sleeper=time.sleep):
    """Run inside each owner hook, without creating a model process or optimizer.

    The same raw engine and AdamW survive group initialization, consolidation,
    teardown and return. A JOIN is a single-use dispatch receipt, not a restart
    token. Missing peers/timeouts poison this launch namespace; never rejoin it.
    Existing default distributed groups are rejected, not destroyed/replaced.
    """
    activation_path = checked_file(activation_path,activation_sha256)
    document = read(activation_path)
    launch, folder = document['launch'], activation_path.parent
    require(branch in BRANCHES and launch['schema'] == LAUNCH_SCHEMA
            and launch['rank_order'] == list(BRANCHES), 'exact_launch_rank_contract')
    plan = read(checked_file(launch['plan_path'],launch['plan_sha256']))
    require(Path(launch['plan_path']).parent == folder and Path(launch['store_path']) == folder / 'RENDEZVOUS'
            and plan['generation'] == document['generation'] and plan['source_files'] == document['source_files']
            and plan['root'] == document['root'] and plan['mode'] == launch['mode'], 'launch_plan_binding')
    require(not engine.torch.distributed.is_initialized(), 'do_not_replace_owner_process_group')
    require(os.environ.get('GLOO_SOCKET_IFNAME') in (None,'lo'), 'loopback_only_inplace_group')
    context = validate_activation(document['root'],activation_path,activation_sha256,clock)
    certificate = context['certificates'][branch]
    require(certificate['identity'] == process_identity(), 'join_is_exact_owner_process')
    validate_launch_participant(certificate,branch,launch['mode'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES','') == certificate['launch_device']['cuda_visible_devices'],
            'owner_GPU_visibility_must_not_change')
    device_type = engine.torch.device(engine.device).type
    if launch['mode'] == 'CPU_TEST_ONLY':
        require(device_type == 'cpu' and not engine.torch.cuda.is_initialized(), 'CPU_launch_cannot_use_GPU')
    else:
        require(device_type == 'cuda' and engine.torch.cuda.is_initialized(), 'already_loaded_owner_CUDA_engine')
        import subprocess
        actual_uuid = subprocess.run(['nvidia-smi','-i',str(BRANCHES.index(branch)),
            '--query-gpu=uuid','--format=csv,noheader'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
        require(actual_uuid == certificate['launch_device']['uuid'], 'original_physical_UUID')
    require((branch == 'F1' and isinstance(optimizer,engine.torch.optim.AdamW) and callable(save_checkpoint))
            or (branch != 'F1' and optimizer is None and save_checkpoint is None), 'exact_existing_optimizer_owner')
    require(clock() < launch['join_deadline_unix'], 'fixed_join_deadline_expired')
    require(not list(folder.glob('FAILED_*.json')), 'failed_launch_cannot_retry')
    join_path = folder / ('JOIN_' + branch + '.json')
    write(join_path,dict(schema=LAUNCH_SCHEMA,branch=branch,rank=BRANCHES.index(branch),identity=process_identity(),
        activation_sha256=activation_sha256,checkpoint_sha256=context['state']['checkpoint']['path_sha256'],
        observed_unix=clock(),same_engine=True,optimizer_present=optimizer is not None))
    created_group = False
    old_interface = os.environ.get('GLOO_SOCKET_IFNAME')
    try:
        while True:
            check('parallel_launch_join_wait')
            require(clock() < launch['join_deadline_unix'], 'fixed_join_deadline_expired')
            require(not list(folder.glob('FAILED_*.json')), 'peer_launch_failed_no_retry')
            if all((folder / ('JOIN_' + member + '.json')).exists() for member in BRANCHES):
                for rank, member in enumerate(BRANCHES):
                    joined = read(folder / ('JOIN_' + member + '.json'))
                    require(joined['branch'] == member and joined['rank'] == rank
                            and joined['activation_sha256'] == activation_sha256
                            and joined['identity'] == context['certificates'][member]['identity']
                            and joined['checkpoint_sha256'] == context['state']['checkpoint']['path_sha256']
                            and joined['observed_unix'] < launch['join_deadline_unix'], 'all8_join_binding')
                    live_identity(joined['identity'])
                break
            sleeper(min(.1,max(0,launch['join_deadline_unix'] - clock())))
        require(not engine.torch.distributed.is_initialized(), 'owner_group_created_during_wait')
        os.environ['GLOO_SOCKET_IFNAME'] = 'lo'
        remaining = min(launch['collective_timeout_seconds'],
                        context['deadline'] - document['commit_reserve_seconds'] - clock())
        require(remaining > 0, 'original_group_deadline')
        engine.torch.distributed.init_process_group('gloo',init_method=(folder / 'RENDEZVOUS').as_uri(),
            rank=BRANCHES.index(branch),world_size=8,timeout=timedelta(seconds=remaining))
        created_group = True
        group = engine.torch.distributed.group.WORLD
        collective = Collectives(engine.torch,group)
        if anchors is None:
            def load_anchors():
                inventory = anchor_module.load_inventory(Path(anchor_root),engine.tokenizer)
                return [row for family in sorted(inventory) for row in inventory[family]]
            anchors = collective.all('original_F1_anchor_order',load_anchors)
        result = consolidate(root=document['root'],activation_path=activation_path,activation_sha256=activation_sha256,
            branch=branch,engine=engine,optimizer=optimizer,group=group,anchor_module=anchor_module,
            anchors=anchors,anchor_root=anchor_root,save_checkpoint=save_checkpoint,check=check,clock=clock)
        collective.all('return_receipt',lambda: write(folder / ('RETURN_' + branch + '.json'),
            dict(schema=LAUNCH_SCHEMA,branch=branch,identity=process_identity(),activation_sha256=activation_sha256,
                 checkpoint_sha256=result['state']['checkpoint']['path_sha256'],observed_unix=clock(),
                 same_engine=True,same_optimizer=branch=='F1',owner_readouts_required=True)))
        return result
    except Exception as error:
        failure = folder / ('FAILED_' + branch + '.json')
        if not failure.exists():
            write(failure,dict(schema=LAUNCH_SCHEMA,branch=branch,identity=process_identity(),
                activation_sha256=activation_sha256,observed_unix=clock(),error=type(error).__name__+': '+str(error),
                replay_permitted=False,actor_signals_sent=0))
        raise
    finally:
        if created_group:
            engine.torch.distributed.destroy_process_group()
        if old_interface is None:
            os.environ.pop('GLOO_SOCKET_IFNAME',None)
        else:
            os.environ['GLOO_SOCKET_IFNAME'] = old_interface


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    commands.add_parser('contract')
    prepare = commands.add_parser('prepare-launch')
    prepare.add_argument('--request',type=Path,required=True)
    prepare.add_argument('--output',type=Path,required=True)
    arm = commands.add_parser('arm-future-boundary')
    arm.add_argument('--plan',type=Path,required=True)
    arm.add_argument('--plan-sha256',required=True)
    arm.add_argument('--participants',type=Path,required=True)
    arm.add_argument('--execute-future-boundary',action='store_true',required=True)
    status = commands.add_parser('launch-status')
    status.add_argument('--activation',type=Path,required=True)
    status.add_argument('--activation-sha256',required=True)
    publish = commands.add_parser('publish-fresh-sessions')
    publish.add_argument('--request',type=Path,required=True)
    publish.add_argument('--output',type=Path,required=True)
    dispatch = commands.add_parser('dispatch-fresh-sessions')
    dispatch.add_argument('--session',type=Path,required=True)
    dispatch.add_argument('--session-sha256',required=True)
    dispatch.add_argument('--execute-owner-safe-release',action='store_true',required=True)
    campaign = commands.add_parser('prepare-campaign')
    campaign.add_argument('--request',type=Path,required=True)
    campaign.add_argument('--output',type=Path,required=True)
    watch = commands.add_parser('watch-campaign')
    watch.add_argument('--campaign',type=Path,required=True)
    watch.add_argument('--campaign-sha256',required=True)
    watch.add_argument('--session',type=Path,required=True)
    watch.add_argument('--session-sha256',required=True)
    watch.add_argument('--execute-bounded-auto-arm',action='store_true',required=True)
    args = parser.parse_args()
    if args.action == 'contract':
        result = integration_contract()
    elif args.action == 'prepare-launch':
        result = prepare_launch_plan(output=args.output,**read(args.request))
    elif args.action == 'arm-future-boundary':
        result = arm_launch(plan_path=args.plan,plan_sha256=args.plan_sha256,participants=read(args.participants))
    elif args.action == 'publish-fresh-sessions':
        result = publish_fresh_sessions(output=args.output,**read(args.request))
    elif args.action == 'dispatch-fresh-sessions':
        result = dispatch_fresh_sessions(session_path=args.session,session_sha256=args.session_sha256)
    elif args.action == 'prepare-campaign':
        result = prepare_campaign(output=args.output,**read(args.request))
    elif args.action == 'watch-campaign':
        result = watch_campaign(campaign_path=args.campaign,campaign_sha256=args.campaign_sha256,
                               session_path=args.session,session_sha256=args.session_sha256)
    else:
        result = launch_status(args.activation,args.activation_sha256)
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
