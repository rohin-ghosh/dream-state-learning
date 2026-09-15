"""Unactivated cooperative F2/A2 parallel-loop successor; caller owns live actors."""

from copy import deepcopy
from dataclasses import replace
import inspect
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_math_feedback_uptake_r118_parallel_boundary as boundary


previous, hook = boundary.previous, boundary.hook
shared, client, require = previous.shared, previous.client, previous.require
SCHEMA = 'R118_MATH_PARALLEL_AUTHORIZATION_V1'


def contract():
    return dict(schema='R118_MATH_PARALLEL_CANDIDATE_V1', status='CPU_CANDIDATE_NOT_ACTIVATED',
        entrypoint='gpu.orch_math_feedback_uptake_r118_parallel_run.run',
        hook_signature=str(inspect.signature(hook.launch_at_boundary)), rank_order=list(hook.BRANCHES),
        math_ranks={branch: hook.BRANCHES.index(branch) for branch in client.BRANCHES},
        source_hook_sha256=shared.sha(hook.__file__), actor_replacement=False,
        integration='SAME raw engine/process/RNG; Herschel launch_at_boundary owns finite loopback Gloo.',
        blockers=['Current immutable actors do not call this cooperative hook.',
                  'Main must bind an agreed future source boundary and all8 activation.',
                  'Authentic guard and FINAL timer coverage must remain bound; no implicit rebind.',
                  'Future FINAL drain must use parallel_safe_snapshot; old accepted-wait drain is not parallel-safe.'],
        optimizer_owner='F1', worker_optimizer=None, worker_serializer=None,
        train='Original two sequential episodes/open turns/presleep/reflection, accepted submit once.',
        after_sleep='Verify broadcast in place, update readonly identity, fresh DEV, settle original cursor.',
        algorithm='Eight-rank average-gradient AdamW; NOT serial-equivalent.',
        inherited_bounds=previous.ready.bounds(), legacy_morning_final_dispatched=False,
        final='Existing separately bound deadline drain and canonical evaluator; no FINAL writer here.',
        native_calls=0, GPU_tested=False, measured_speedup=None)


def authorize(reference, handoff, engine, protected_refs, clock=time.time):
    document = boundary.checked(reference)
    require(document['schema'] == SCHEMA and document['authorized'] is True,
            'prospective_explicit_authorization_required')
    require(document['handoff_sha256'] == shared.digest(handoff)
            and document['branch'] == engine.session['branch'], 'exact_handoff_authorization')
    require(document['inherited_bounds'] == previous.ready.bounds()
            and document['protected_refs'] == protected_refs == handoff['protected_refs'],
            'no_guard_FINAL_or_bounds_change')
    require(document['source_files'], 'frozen_source_closure_required')
    for name, digest in document['source_files'].items():
        hook.checked_file(name, digest)
    for name in (__file__, boundary.__file__, hook.__file__, previous.__file__, client.__file__):
        require(str(Path(name).resolve()) in document['source_files'], 'successor_source_pin_required')
    require(clock() < previous.math.NATIVE-120, 'original_native_launch_bound')
    return boundary.accept_in_process(handoff, engine)


def adopt_broadcast(engine, following, result):
    prior = engine.session
    require(result['status'] == 'COMPLETE_ALL8_INPLACE'
            and following['generation'] == prior['generation']+1
            and result['state']['generation'] == following['generation']
            and result['state']['checkpoint'] == following['checkpoint'], 'one_actual_committed_publication')
    require(following['branch'] == prior['branch'] and following['branch_root'] == prior['branch_root']
            and following['shared_root'] == prior['shared_root']
            and following['config_sha256'] == prior['config_sha256'], 'same_branch_common_and_config')
    client.current(following)
    require(engine.loaded.optimizer is None, 'no_math_optimizer')
    expected = client.native.bridge.AdapterIdentity.from_document(following['adapter'])
    expected.verify()
    observed = client.native.observe_adapter(engine.loaded.engine, expected)
    require(observed == expected, 'actual_broadcast_hash_before_session_update')
    require(not any(parameter.requires_grad for parameter in engine.model.parameters()),
            'readonly_flags_restored_after_parallel')
    engine.loaded.binding = replace(engine.loaded.binding, cycle=following['generation'], adapter=expected)
    engine.loaded.observed = observed
    engine.session = deepcopy(following)
    engine.poisoned = False
    engine.verify_base()
    return dict(**client.binding(following), actual_adapter=observed.document(),
        resident_process=client.native.process_identity(), optimizer=None, in_place=True,
        reloaded_from_disk=False)


def dispatch_readout(root, session, cycle):
    """Reuse the original frozen evaluator, not its module imported in new source."""
    root = Path(root)
    receipt = shared.read(root/'SHARED_CLIENT_READY.json')
    source = Path(receipt['successor_source']).resolve(strict=True)
    require(receipt['branch'] == session['branch'] and receipt['root'] == str(root),
            'original_frozen_readout_root')
    for name, digest in receipt['source_files'].items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'readout_source_path_escape')
        hook.checked_file(source/relative, digest)
    require('gpu/orch_math_feedback_uptake_r118_shared_run.py' in receipt['source_files'],
            'original_native_readout_source_pin')
    binding = root/'shared_readout_bindings'/f'cycle_{cycle:03d}.json'
    shared.write(binding, dict(session=deepcopy(session), stage='cycle', cycle=cycle,
        resident_process=client.native.process_identity(), parent_free=True, never_rows_or_buffer=True))
    with binding.with_suffix('.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', '-m', previous.MODULE, 'readout',
            '--root', str(root), '--binding', str(binding)], cwd=source, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1',
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'))
        identity = previous.math.common.process_identity(Path('/proc')/str(child.pid))
        shared.write(binding.with_suffix('.process.json'), identity)
        try:
            require(child.wait(timeout=max(.01, previous.math.NATIVE-time.time())) == 0,
                    'fresh_original_readout_failed_no_retry')
        finally:
            if child.poll() is None:
                previous.math.common.stop_owned(child, identity)


def run_cycle(root, engine, cycle, tasks, carry, *, anchor_module, anchors,
              anchor_root, protected_refs, supervision, await_activation, check, clock=time.time):
    root = Path(root)
    require(clock() < previous.math.NATIVE-120, 'original_collection_cutoff')
    started = clock()
    collected = client.collect_cycle(root, engine, cycle, tasks, carry)
    output = root/f'cycle{cycle:03d}'
    certificate = boundary.submission_certificate(root, engine, cycle, collected['submission'], protected_refs, supervision)
    certificate_path = output/'PARALLEL_PARTICIPANT.json'
    shared.write(certificate_path, certificate)
    activation = await_activation(previous.ready.reference(certificate_path), previous.math.NATIVE-120)
    document = boundary.checked(activation)
    require(document['participants'][engine.session['branch']] == previous.ready.reference(certificate_path),
            'Main_activation_exact_new_submission_certificate')
    require(document['generation'] == engine.session['generation'], 'activation_generation_not_previous')
    boundary.unchanged(root, certificate['preserved_files'])
    boundary.fences(protected_refs)
    engine.verify_base()
    engine.poisoned = True
    result = hook.launch_at_boundary(activation_path=activation['path'],
        activation_sha256=activation['sha256'], branch=engine.session['branch'],
        engine=engine.loaded.engine, optimizer=None, anchor_module=anchor_module,
        anchors=anchors, anchor_root=anchor_root, save_checkpoint=None, check=check, clock=clock)
    following = client.prepare(engine.session['shared_root'], engine.session['branch'])
    mounted = adopt_broadcast(engine, following, result)
    shared.write(output/'SHARED_SLEEP.json', dict(status='COMPLETE', publication=following['checkpoint'],
        submission=collected['submission'], mounted=mounted, optimizer_owner='F1', local_optimizer_steps=0,
        algorithm='PARALLEL_AVERAGE_GRADIENT_NOT_SERIAL_EQUIVALENT',
        activation=activation, metrics=result['metrics'], finished_unix=clock()))
    dispatch_readout(root, engine.session, cycle)
    shared.write(output/'COMPLETE.json', dict(status='COMPLETE', cycle=cycle, started_unix=started,
        finished_unix=clock(), counters=shared.read(root/'COUNTERS.json'),
        label='SHARED_F1_PARALLEL_LORA_SLEEP', local_optimizer_steps=0, **client.binding(engine.session)))
    previous.math.atomic(root/'PROGRESS.json', dict(cycle=cycle, phase='CYCLE_COMPLETE',
        counters=shared.read(root/'COUNTERS.json'), observed_unix=clock(), **client.binding(engine.session)))
    return collected['carry']


def run(root, engine, *, handoff, authorization, anchor_module, anchors,
        anchor_root, protected_refs, supervision, await_activation, check, clock=time.time):
    """Invoke only from an agreed future resident source at its completed DEV seam."""
    root = Path(root)
    require(str(root) == handoff['root'] == engine.session['branch_root'], 'exact_handoff_root')
    start, carry = authorize(authorization, handoff, engine, protected_refs, clock)
    tasks = shared.read(root.parent/'TRAIN.json')
    for cycle in range(start, previous.math.policy.CYCLES+1):
        if clock() >= previous.math.NATIVE-120:
            return dict(status='NATIVE_CUTOFF', next_cycle=cycle, legacy_FINAL_dispatched=False)
        try:
            carry = run_cycle(root, engine, cycle, tasks[cycle-1], carry,
                anchor_module=anchor_module, anchors=anchors, anchor_root=anchor_root,
                protected_refs=protected_refs, supervision=supervision, await_activation=await_activation, check=check, clock=clock)
        except BaseException as error:
            engine.poisoned = True
            shared.write(root/f'cycle{cycle:03d}'/'PARALLEL_FAILED.json',
                dict(status='FAILED_NO_RETRY', error=type(error).__name__+': '+str(error),
                     counters=shared.read(root/'COUNTERS.json'), observed_unix=clock(), replay_permitted=False))
            raise
    return dict(status='ORIGINAL_CYCLES_COMPLETE', next_cycle=previous.math.policy.CYCLES+1,
        legacy_FINAL_dispatched=False)
