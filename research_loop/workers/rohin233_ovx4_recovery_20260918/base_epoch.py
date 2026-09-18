"""Explicit allocation-only continuation using the prior immutable runtime."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import inspect
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_generation_service import GenerationSession
from gpu.ny_caption_life_service import restoration_evidence
from research_loop.workers.rohin221_continuous_caption_20260918.adapters import BaseBackend, SocketScorer
from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller, Plan, digest, file_ref, write
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import generation_origin, validate_generation_origin
from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import BASE_ROOT, device_proof, prepare_assets
from research_loop.workers.rohin221_continuous_caption_20260918.scene_schedule import verified_active_scene


def read(path):
    return json.loads(Path(path).read_bytes())


def retained_summary(state, scorer):
    return dict(opportunity=state['opportunity'], attempt=state['attempt'], stage=state['stage'],
        completed_opportunities=state['completed_opportunities'], ACT_attempts=len(state['events']),
        total_generated_tokens=state['total_generated_tokens'], history_sha256=digest(state['history']),
        events_sha256=digest(state['events']), generations_sha256=digest(state['generations']),
        think_source_sha256=digest(state.get('think_source')), seen_count=len(scorer['seen']),
        seen_sha256=data.digest(sorted(scorer['seen'])), game_sha256=data.digest(scorer['game']),
        policy_sha256=data.digest(scorer['policy']))


def migrate(previous, scorer, backend, binding, visible_device, epoch):
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import relocated_reference
    data.require(previous['pending'] is None and previous['stage'] in ('THINK', 'ACT'),
        'no_unresolved_generation_or_score_resubmission')
    data.require(scorer['phase'] == 'COMPLETE' and scorer['session_binding'] ==
        dict(controller=previous['binding'], backend=previous['backend_state']), 'exact_complete_session_binding')
    identifiers = [event['source']['request_id'] for event in previous['events']]
    data.require(len(set(identifiers)) == len(identifiers) and set(scorer['seen']) == set(identifiers),
        'complete_unique_seen_controller_prefix')
    expected_backend = deepcopy(previous['backend_state'])
    expected_backend['identity']['visible_device'] = visible_device
    if 'source' in expected_backend:
        data.require(set(expected_backend['source']) == set(backend['source']), 'same_backend_source_roles')
        for name in expected_backend['source']:
            expected_backend['source'][name] = relocated_reference(expected_backend['source'][name], backend['source'][name])
    data.require(backend == expected_backend and backend['identity']['all_parameters_frozen']
        and not backend['identity']['optimizer_created'] and backend['identity']['lora_parameters'] == 0,
        'only_actual_physical_device_change_frozen_backend')
    expected_binding = deepcopy(previous['binding'])
    total = binding['plan']['opportunities']
    data.require(type(total) is int and previous['binding']['plan']['opportunities'] <= total <= 1000000,
        'bounded_remaining_or_additional_opportunity_allocation')
    expected_binding['plan']['opportunities'] = total
    for name in ('controller', 'parser'):
        if name in expected_binding:
            expected_binding[name] = relocated_reference(expected_binding[name], binding[name])
    data.require(binding == expected_binding, 'only_total_horizon_change_same_per_opportunity_budgets')
    migrated = deepcopy(previous)
    migrated['binding'], migrated['backend_state'] = binding, backend
    migrated.setdefault('source_adoptions', []).append(dict(epoch=epoch,
        previous_binding_sha256=digest(previous['binding']), previous_backend_sha256=digest(previous['backend_state']),
        change='finite_runtime_renewal_and_byte_identical_source_relocation', fresh_context_reset=False, uninterrupted_claim=False))
    resumed_scorer = deepcopy(scorer)
    resumed_scorer['session_binding'] = dict(controller=binding, backend=backend)
    data.require(retained_summary(previous, scorer) == retained_summary(migrated, resumed_scorer),
        'all_history_counts_ids_think_novelty_preserved')
    return migrated, resumed_scorer


def verified_request(request, session, transition):
    data.require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'exact_generation_request')
    current = session.session_binding
    origin = request['origin']
    predecessor = transition['predecessor_think_origin']
    if predecessor is not None and origin.get('think') == predecessor:
        actual = validate_generation_origin({key: value for key, value in origin.items() if key != 'think'},
            receipt_root=session.life_root, expected_binding=current['controller'], expected_backend_state=current['backend'])
        prior = validate_generation_origin(predecessor, receipt_root=session.life_root,
            expected_binding=transition['previous_binding'], expected_backend_state=transition['previous_backend'], stage='THINK')
        data.require(actual['request']['opportunity'] == prior['request']['opportunity'] == transition['opportunity']
            and prior['finished_unix'] <= actual['finished_unix'], 'only_exact_saved_same_opportunity_THINK')
        actual['think'] = prior
    else:
        actual = validate_generation_origin(origin, receipt_root=session.life_root,
            expected_binding=current['controller'], expected_backend_state=current['backend'])
    think_tokens = actual['think']['generated_tokens'] if actual['think'] else 0
    data.require(request['metrics'] == dict(THINK=think_tokens if actual['request']['attempt'] == 1 else 0,
        ACT=actual['generated_tokens'], LEARN=0), 'actual_standalone_tokens_no_learning')
    active = verified_active_scene(actual['request'], session.scene_ids)
    if actual['think'] is not None:
        data.require(verified_active_scene(actual['think']['request'], session.scene_ids) == active,
            'same_saved_THINK_ACT_scene_assignment')
    return actual, active


class EpochSession(GenerationSession):
    def process(self, request):
        verified, active = verified_request(request, self, self.transition)
        result = self.process_verified(request, verified['raw'], identifier=request['origin']['request_id'],
            think_resolver=lambda: verified['think'], active_scene=active)
        return dict(result, request_id=request['origin']['request_id'],
            rule_sha256=self.session_binding['controller']['plan']['rule_sha256'],
            condition=self.session_binding['controller']['plan']['condition'])


def wait(path, deadline):
    while not path.exists():
        if time.time() >= deadline:
            raise TimeoutError('bounded_epoch_initialization')
        time.sleep(0.25)
    return read(path)


def check_input(root, config):
    for relative, expected in config['input_files'].items():
        data.require(file_ref(root / relative)['sha256'] == expected, 'immutable_epoch_input_hash')
    source = Path(config['source_root'])
    for relative, expected in config['frozen_source_files'].items():
        data.require(file_ref(source / relative)['sha256'] == expected, 'prior_runtime_source_unchanged')
    for relative, expected in config['new_source_files'].items():
        data.require(file_ref(root / relative)['sha256'] == expected, 'new_epoch_driver_unchanged')


def run_player(root, config):
    original = Path(config['original_root'])
    previous = read(root / 'PRESERVED_CONTROLLER.private.json')
    scorer_state = read(root / 'PRESERVED_SCORER.private.json')
    unused, rule, unused_manifest, scenes = prepare_assets(original)
    data.require(data.digest(rule) == previous['binding']['plan']['rule_sha256'], 'original_frozen_game_rule')
    started = time.time()
    backend = BaseBackend(BASE_ROOT)
    identity = backend.state_receipt()
    plan = Plan(**dict(previous['binding']['plan'], opportunities=config['total_opportunities']))
    binding = deepcopy(previous['binding'])
    binding['plan'] = asdict(plan)
    binding['controller'] = file_ref(inspect.getsourcefile(Controller))
    binding['parser'] = file_ref(inspect.getsourcefile(extract_batches))
    state, resumed_scorer = migrate(previous, scorer_state, identity, binding,
        os.environ['CUDA_VISIBLE_DEVICES'], config['epoch'])
    transition = dict(opportunity=previous['opportunity'], previous_binding=previous['binding'],
        previous_backend=previous['backend_state'], predecessor_think_origin=
        generation_origin(previous['think_source']) if previous['stage'] == 'ACT' else None)
    if transition['predecessor_think_origin'] is not None:
        validate_generation_origin(transition['predecessor_think_origin'],
            receipt_root=original / 'player/private/generations', expected_binding=previous['binding'],
            expected_backend_state=previous['backend_state'], stage='THINK')
    write(root / 'TRANSITION.private.json', transition)
    write(root / 'MIGRATED_CONTROLLER.private.json', state)
    write(root / 'MIGRATED_SCORER.private.json', resumed_scorer)
    write(root / 'BINDING.json', dict(controller=binding, backend=identity))
    write(root / 'BASE_MODEL_LOADED.json', dict(pid=os.getpid(), unix=time.time(),
        identity=identity, model_load_seconds=time.time()-started, deadline_unix=config['deadline_unix']))
    wait(root / 'scorer/LISTENING.json', min(config['deadline_unix'], time.time()+240))
    restored = read(root / 'scorer/BASE_SESSION_RESTORED.json')
    expected = retained_summary(previous, scorer_state)
    data.require(restored['restored_seen_count'] == expected['seen_count'] and
        restored['restored_game_snapshot_sha256'] == expected['game_sha256'] and
        restored['restored_policy_snapshot_sha256'] == expected['policy_sha256'], 'actual_exact_scorer_restore_before_player')
    data.require(file_ref(original / 'player/private/state.json')['sha256'] ==
        config['input_files']['PRESERVED_CONTROLLER.private.json'], 'idle_controller_has_not_changed')
    wait(root / 'PARENT_BRIDGE_READY.json', min(config['deadline_unix'], time.time()+240))
    write(original / 'player/private/state.json', state)
    scorer = SocketScorer(root / 'scorer/base.sock', dict(rule_sha256=plan.rule_sha256,
        top_k=50, reference_count=64, relevance=True, novelty=True, condition=plan.condition), output=original / 'scorer')
    first_event = None
    with Controller(original / 'player', plan, backend, scorer, scenes, extract_batches) as controller:
        data.require(retained_summary(controller.state, resumed_scorer) == expected, 'actual_controller_restore')
        loaded = dict(pid=os.getpid(), unix=time.time(), backend=identity, controller_binding=binding,
            phase_start_opportunity=previous['opportunity'], prior_opportunities=previous['completed_opportunities'],
            prior_ACT_attempts=len(previous['events']), preserved=expected, learning=False, optimizer_created=False,
            fresh_context_reset=False, historical_rescoring=False, runtime_epoch=config['epoch'],
            previous_exit_unix=config['previous_exit_unix'], gap_seconds=time.time()-config['previous_exit_unix'],
            deadline_unix=config['deadline_unix'], allocation_changed=True)
        write(root / 'LOADED.json', loaded)
        write(Path(config['phase_root']) / 'CURRENT.json', dict(unix=time.time(), root=str(root),
            scorer_root=str(root / 'scorer'), loaded=loaded, preceding_failed_root=config['previous_root']))
        while time.time() < config['deadline_unix'] and controller.state['completed_opportunities'] < plan.opportunities:
            before = len(controller.state['events'])
            controller.step()
            if first_event is not None and not (root / 'FIRST_FEEDBACK_RENDERED.json').exists():
                for generation in controller.state['generations'][-2:]:
                    if generation['finished_unix'] <= first_event['finished_unix']:
                        continue
                    receipt_path = original / 'player/private/generations' / (generation['request_id']+'.json')
                    receipt = read(receipt_path)
                    feedback = first_event['feedback_message']
                    if feedback in receipt['request']['messages']:
                        write(root / 'FIRST_FEEDBACK_RENDERED.json', dict(unix=time.time(),
                            generation_request_id=generation['request_id'], generation_receipt=file_ref(receipt_path),
                            input_sha256=digest(receipt['request']['messages']),
                            feedback_message_sha256=digest(feedback), score_receipt_sha256=first_event['score_receipt_sha256'],
                            exact_saved_feedback_in_actual_generation_input=True, raw_payload_included=False))
            if len(controller.state['events']) > before:
                event = controller.state['events'][-1]
                write(root / 'LATEST_ATTEMPT.json', event)
                if first_event is None:
                    first_event = dict(event, feedback_message=controller.state['history'][-1])
                    write(root / 'FIRST_ATTEMPT.json', event)
                    write(root / 'FIRST_SCORE_PUBLIC.json', dict(unix=time.time(), epoch=config['epoch'],
                        opportunity=event['opportunity'], attempt=event['attempt'], source=event['source'],
                        score_receipt_sha256=event['score_receipt_sha256'],
                        counts={key:event[key] for key in ('parsed','scored','accepted','novel','cached','unknown')},
                        next_stage=controller.state['stage'], no_historical_resubmission=True))
        write(root / 'FINISHED.json', dict(unix=time.time(), completed_opportunities=controller.state['completed_opportunities'],
            deadline_unix=config['deadline_unix'], preserved_state=file_ref(original / 'player/private/state.json')))


def run_scorer(root, config):
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub, serve
    scorer_root = root / 'scorer'
    assets, rule, manifest, scenes = prepare_assets(scorer_root)
    started = time.time()
    original_base = data.bound(data.file_ref(assets / 'base_manifest.json'))
    base_ref = data.private_write(scorer_root / 'base_manifest.json', dict(original_base, root=BASE_ROOT))
    runtime = data.private_write(scorer_root / 'scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
        base_model=base_ref, selected_adapter_root=str(assets / 'adapter'),
        adapter={name:data.file_ref((assets / 'adapter' / name).resolve()) for name in rule['adapter']},
        config=dict(max_length=rule['max_length']), source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar = ScalarJudge(runtime['path'], batch_size=8)
    encoder = FrozenCPUEncoder(data.file_ref((assets / 'embedding_snapshot.json').resolve()), threads=2)
    panels = data.bound(data.file_ref(assets / 'PANEL_SCORES.private.json'))
    pixels = PixelConfig(**data.bound(data.file_ref(assets / 'pixel_config.json')))
    def game_factory(identifier):
        return build_game(manifest, scalar, panels, pixels, encoder, top_k=50, agent_id=identifier,
            lane='R210_LIVE_DEVELOPMENT', relevance_threshold=rule['relevance_threshold'])
    binding = wait(root / 'BINDING.json', min(config['deadline_unix'], time.time()+240))
    resumed = read(root / 'MIGRATED_SCORER.private.json')
    original = Path(config['original_root'])
    session = EpochSession(game_factory('R224_CONTINUOUS_FROZEN_BASE'), original / 'player/private/generations',
        original / 'scorer', scenes, resume_state=resumed, source_mode='STANDALONE_GENERATION', session_binding=binding)
    session.transition = read(root / 'TRANSITION.private.json')
    actual = restoration_evidence(session, data.file_ref(root / 'MIGRATED_SCORER.private.json'))
    data.require(actual['restored_seen_count'] == len(resumed['seen']) and
        actual['restored_game_snapshot_sha256'] == data.digest(resumed['game']) and
        actual['restored_policy_snapshot_sha256'] == data.digest(resumed['policy']), 'actual_scorer_novelty_policy_exact')
    write(scorer_root / 'BASE_SESSION_RESTORED.json', dict(unix=time.time(), **actual,
        original_resume_state_input_sha256=config['input_files']['PRESERVED_SCORER.private.json']))
    hub = Hub(scorer_root, dict(complete=True, rows=[]), game_factory, scenes, rule)
    hub.base = session
    write(scorer_root / 'LOADED.json', dict(pid=os.getpid(), unix=time.time(), model_load_seconds=time.time()-started,
        rule_sha256=data.digest(rule), physical=config['scorer_physical'], runtime_epoch=config['epoch'],
        service_kind='DEDICATED_EXISTING_BASE_SESSION_NOT_LEARNER', source=file_ref(__file__), **actual))
    serve(hub, config['deadline_unix'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=['player', 'scorer'], required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    config = read(root / 'EPOCH.json')
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import allocation_guard
    allocation_guard(config, config[args.mode+'_physical'])
    check_input(root, config)
    proof = device_proof(config[args.mode+'_physical'])
    write(root / (args.mode+'_DEVICE_PROOF.json'), proof)
    try:
        (run_player if args.mode == 'player' else run_scorer)(root, config)
    except Exception as error:
        write(root / (args.mode+'_FAILED.json'), dict(unix=time.time(), error_type=type(error).__name__, error=str(error)[:240]))
        raise


if __name__ == '__main__':
    main()
