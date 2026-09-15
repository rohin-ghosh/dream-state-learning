"""Inactive callable GRID successor; Main activates each all-eight boundary."""

from copy import deepcopy
from dataclasses import replace
import gc
from pathlib import Path
import time

from gpu import orch_r118_grid_parallel_handoff as handoff


run, parallel = handoff.run, handoff.parallel
shared, require = run.shared, run.require


def model_objects(decoder):
    loaded = decoder.loaded
    require(loaded.optimizer is None, 'GRID_never_constructs_optimizer')
    return (id(loaded.engine), id(loaded.engine.model),
            tuple((name, id(parameter)) for name, parameter in loaded.engine.model.named_parameters()))


def adopt_in_place(decoder, session, result, before):
    require(model_objects(decoder) == before, 'same_engine_model_and_parameter_objects')
    require(result['status'] == 'COMPLETE_ALL8_INPLACE', 'all8_checkpoint_commit_required')
    next_session = run.client.prepare(session['shared_root'], session['branch'],
                                      config_sha256=session['config_sha256'])
    require(all(next_session[name] == session[name] for name in
            ('branch', 'branch_root', 'shared_root', 'config_sha256')) and
            next_session['generation'] == session['generation'] + 1, 'exact_next_shared_generation')
    state = handoff.committed(next_session)
    require(result['state'] == state, 'hook_and_committed_state_match')
    folder = Path(session['shared_root']) / f"generation_{session['generation']:06d}/sleep"
    reload = shared.read(folder / 'ALL8_RELOAD.json')
    require(reload['state'] == state and len(reload['acknowledgments']) == 8 and
            {item['branch'] for item in reload['acknowledgments']} == set(shared.BRANCHES),
            'all_eight_actual_inplace_acknowledgments')
    for item in reload['acknowledgments']:
        require(item['in_place'] is True and item['checkpoint_sha256'] == next_session['checkpoint_sha256'],
                'acknowledged_committed_child')
    own = next(item for item in reload['acknowledgments'] if item['branch'] == session['branch'])
    require(own['identity'] == parallel.process_identity(), 'own_actual_inplace_ack')
    loaded = decoder.loaded
    require(loaded.binding.adapter.document() == session['adapter'], 'prior_binding_retained_until_verified')
    identity = run.client.native.bridge.AdapterIdentity.from_document(next_session['adapter'])
    observed = run.client.native.observe_adapter(loaded.engine, identity)
    require(observed == identity, 'actual_inplace_adapter_matches_checkpoint')
    for unused, parameter in loaded.engine.model.named_parameters():
        parameter.requires_grad_(False)
    loaded.binding = replace(loaded.binding, adapter=identity, cycle=next_session['generation'])
    loaded.observed = observed
    decoder.verify_base()
    return next_session, dict(generation=next_session['generation'],
        checkpoint_sha256=next_session['checkpoint_sha256'], resident_reload=True,
        reload_mode='ALL8_VERIFIED_INPLACE_NO_SECOND_LOAD', optimizer_owner='F1',
        local_optimizer_steps=0, same_model_objects=True, rng_reinitialized=False)


def fresh_dev(decoder, root, cycle, session, *, readout=run.spawn_readout):
    decoder.verify_base()
    before = model_objects(decoder)
    engine = decoder.loaded.engine
    try:
        engine.model.to('cpu')
        gc.collect()
        engine.torch.cuda.empty_cache()
        readout(root, cycle, 'dev', session)
    finally:
        engine.model.to(engine.device)
    require(model_objects(decoder) == before, 'offload_preserves_resident_model_objects')
    decoder.verify_base()


def permit(reference, root, session, *, clock=time.time):
    document = handoff.checked(reference)
    require(document['schema'] == 'R118_GRID_PARALLEL_ENTRY_V1' and
            document['status'] == 'MAIN_ALL8_COORDINATED_GO' and
            set(document['branches']) == set(shared.BRANCHES), 'Main_all8_explicit_entry_only')
    require(document['issued_unix'] <= clock() < document['expires_unix'] <= run.grid.TRAIN_END,
            'original_TRAIN_deadline_not_extended')
    own = document['branches'][session['branch']]
    require(own['root'] == str(root) and own['generation'] == session['generation'] and
            own['checkpoint_sha256'] == session['checkpoint_sha256'], 'entry_bound_to_committed_child')
    require(own['rng_provenance'] in ('SAME_PROCESS_RETAINED', 'EXPLICIT_NEW_PROCESS_STARTUP_NOT_INHERITED'),
            'no_claim_to_unsaved_predecessor_rank_RNG')
    require(own['native_identity'] == parallel.process_identity(), 'entry_bound_to_actual_process')
    candidate = handoff.checked(own['candidate'])
    require(candidate['status'] == 'CPU_ONLY_NOT_ARMED' and candidate['activation_authorized'] is False,
            'exact_CPU_candidate_binding')
    for name, digest in candidate['source_files'].items():
        parallel.checked_file(name, digest)
    require(all(str(Path(module.__file__).resolve()) in candidate['source_files'] for module in
                (handoff, parallel)) and str(Path(__file__).resolve()) in candidate['source_files'],
            'entry_source_closure_includes_live_hook')
    certificate = handoff.checked(own['supervision_certificate'])
    require(certificate['identity'] == own['native_identity'] and certificate['root'] == str(root) and
            certificate['branch'] == session['branch'], 'entry_supervision_exact_branch')
    handoff.supervision(certificate)
    return own


def run_loop(*, root, decoder, session, boundary, entry_reference, config, anchor_module,
             anchor_root, certificate_for_submission, activation_for_certificate,
             check=run.check_deadline, clock=time.time):
    root = Path(root).resolve(strict=True)
    own = permit(entry_reference, root, session, clock=clock)
    handoff.validate_snapshot(boundary)
    require(boundary['session'] == session and handoff.reference(own['boundary']['path']) == own['boundary']
            and handoff.checked(own['boundary']) == boundary, 'exact_settled_handoff_document')
    require(config == shared.read(root / 'CONFIG.json') and
            run.inherited_bounds(config) == boundary['bounds'], 'original_caps_and_parent_wait')
    decoder.verify_base()
    require(decoder.loaded.binding.adapter.document() == session['adapter'], 'actual_loaded_committed_child')
    roster = shared.read(root / 'TRAIN.json')
    pending = boundary.get('recovery_mode') == 'PENDING_CONSOLIDATION'
    cycle = boundary['completed_cycle'] if pending else boundary['next_cycle']
    while clock() < run.grid.TRAIN_END and (pending or run.can_train(root)):
        check('grid_parallel_cycle')
        folder = root / 'parallel_cycles' / f'{cycle:04d}'
        require(not (folder / 'STARTED.json').exists(), 'no_parallel_cycle_replay')
        shared.write(folder / 'STARTED.json', dict(cycle=cycle, session=run.client.call_binding(session),
            entry=entry_reference, rng_provenance=own['rng_provenance'], started_unix=clock()))
        try:
            submitted = collect_or_adopt(root, decoder, config, session, boundary, cycle, roster, pending)
            if pending:
                shared.write(folder / 'ADOPTED_PENDING.json', dict(submitted=boundary['pending_submission'],
                    train_calls=0, parent_calls=0, duplicate_submissions=0, generation=session['generation']))
            pending = False
            certificate_ref = certificate_for_submission(session, cycle, submitted)
            certificate = handoff.checked(certificate_ref)
            handoff.supervision(certificate)
            require(certificate['identity'] == parallel.process_identity() and
                    certificate['branch'] == session['branch'] and certificate['root'] == str(root) and
                    certificate['generation'] == session['generation'] and
                    certificate['checkpoint_sha256'] == session['checkpoint_sha256'],
                    'actual_owner_participant')
            activation = activation_for_certificate(certificate_ref, check)
            before = model_objects(decoder)
            result = parallel.launch_at_boundary(activation_path=activation['path'],
                activation_sha256=activation['sha256'], branch=session['branch'],
                engine=decoder.loaded.engine, optimizer=None, anchor_module=anchor_module,
                anchor_root=anchor_root, save_checkpoint=None, check=check)
            session, reloaded = adopt_in_place(decoder, session, result, before)
            shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'RELOADED.json', reloaded)
            fresh_dev(decoder, root, cycle, session)
            shared.write(root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json', dict(cycle=cycle,
                shared_generation=session['generation'], shared_checkpoint_sha256=session['checkpoint_sha256'],
                optimizer_owner='F1', local_optimizer_steps=0, optimizer_steps=0,
                parallel_backend=True, serial_adamw_equivalent=False, finished_unix=clock()))
            cycle += 1
        except Exception as error:
            shared.write(folder / 'FAILED.json', dict(error=type(error).__name__ + ': ' + str(error),
                replay_permitted=False, serial_fallback=False, finished_unix=clock()))
            raise
    return dict(status='TRAIN_BOUND_REACHED', next_cycle=cycle, session=deepcopy(session),
                FINAL_owner='EXPLICIT_REBOUND_EVAL_ONLY_TIMER', no_automatic_FINAL=True)


def collect_or_adopt(root, decoder, config, session, boundary, cycle, roster, pending):
    if pending:
        require(boundary.get('recovery_mode') == 'PENDING_CONSOLIDATION' and
                cycle == boundary['completed_cycle'] and session == boundary['session'], 'one_exact_pending_boundary')
        handoff.validate_snapshot(boundary)
        resumed = resume_pending(session, check=run.check_deadline)
        submitted = handoff.checked(boundary['pending_submission'])
        require(resumed['cycle'] == cycle and resumed['submission']['path'] == submitted['submission']['path'] and
                resumed['submission']['sha256'] == submitted['submission']['sha256'],
                'central_reuses_exact_accepted_pending_submission')
        return submitted
    life = run.life_class(session['branch'])(root, decoder, config, cycle, session)
    submitted = run.client.run_cycle_and_submit(life, run.cycle_tasks(roster, cycle),
                                                shared.read(root / 'CARRY.json'))
    shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json', submitted)
    return submitted


def resume_pending(session, *, check):
    import os
    require(callable(getattr(parallel, 'resume_pending_consolidation', None)), 'central_pending_resume_API_required')
    return parallel.resume_pending_consolidation(root=session['shared_root'], branch=session['branch'],
        session_path=Path(os.environ['R118_PARALLEL_SESSION']),
        session_sha256=os.environ['R118_PARALLEL_SESSION_SHA256'], check=check)
