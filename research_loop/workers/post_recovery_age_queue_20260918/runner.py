"""Frozen equal-token evaluations; adopted judge is a separately bound epoch."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from research_loop.workers.rohin232_age_probe_20260918 import contract, runtime
from research_loop.workers.rohin233_kept_age_probe_20260918 import probe
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.post_recovery_age_queue_20260918 import epoch


def verify(config):
    epoch.require_config(config, time.time())
    root = Path(config['root'])
    identity = probe.same_battery(root)
    for relative, expected in runtime.read(root / 'SOURCE_MANIFEST.json').items():
        data.require(epoch.sha(root / 'source' / relative) == expected, 'entire_evaluation_source_closure')
    data.require(epoch.sha(root / 'SOURCE_MANIFEST.json') == config['source_manifest_sha256'], 'admitted_source_manifest')
    for name in ('condition', 'source_parent_text_loaded', 'parent_tokens'):
        data.require(identity[name] == config['identity'][name], 'same_parent_free_condition')
    data.require(epoch.sha(root / 'FRESHNESS_VERIFIED.json') == config['freshness_sha256']
        and runtime.read(root / 'FRESHNESS_VERIFIED.json')['eligible'], 'bound_recorded_exposure_audit')
    data.require(epoch.sha(config['primary_config']) == config['primary_config_sha256'], 'adopted_scalar_config')
    primary = runtime.read(config['primary_config'])
    data.require(epoch.sha(primary['adapter']['adapter_model.safetensors']['path']) == epoch.ADAPTER_SHA,
        'adopted_adapter_bytes')
    return root, identity


def judge(config):
    from gpu.ny_caption_game import DevelopmentManifest
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    root, identity = verify(config)
    manifest = DevelopmentManifest.from_mapping(runtime.read(root / 'GAME_MANIFEST.json'))
    assets = root / 'assets'
    rule = runtime.read(assets / 'RULE.json')
    scalar = ScalarJudge(config['primary_config'], batch_size=8)
    original = runtime.read(root / 'judge/REFERENCE_PANELS.private.json')
    shared = Path(config['epoch_root'])
    panel_cache = shared / 'PRIMARY_PANELS.private.json'
    epoch_receipt = shared / 'JUDGE_EPOCH.json'
    selection_sha = epoch.digest([row['selected'] for row in original])
    if not epoch_receipt.exists():
        panels, rows = epoch.rescore_panels(original, scalar)
        panel_ref = runtime.write(panel_cache, rows)
        binding = dict(schema='R233_ADOPTED_PARENT_FREE_AGE_EPOCH_V1', primary_rank=8,
            primary_step=15625, adapter_sha256=epoch.ADAPTER_SHA,
            primary_config_sha256=config['primary_config_sha256'],
            original_game_sha256=probe.GAME_SHA, original_panel_sha256=probe.PANEL_SHA,
            selected_strings_sha256=selection_sha, primary_panels_sha256=panel_ref['sha256'],
            token_budget=6144, seeds=list(epoch.SEEDS), parent_tokens=0, training_updates=0,
            score_selection='HUMAN_ADOPTED_NOT_OUTCOME_SELECTED', old_results_modified=False)
        runtime.write(epoch_receipt, binding)
    binding = runtime.read(epoch_receipt)
    data.require(binding['primary_config_sha256'] == config['primary_config_sha256']
        and binding['selected_strings_sha256'] == selection_sha
        and binding['adapter_sha256'] == epoch.ADAPTER_SHA
        and epoch.sha(panel_cache) == binding['primary_panels_sha256'], 'immutable_shared_adopted_panels')
    panels = probe.panel_scores(runtime.read(panel_cache), manifest)
    epoch_sha = epoch.digest(binding)
    encoder = FrozenCPUEncoder(data.file_ref(assets / 'embedding_snapshot.json'), threads=2)
    pixels = PixelConfig(**runtime.read(assets / 'pixel_config.json'))
    runtime.write(root / 'JUDGE_LOADED.json', dict(pid=os.getpid(), unix=time.time(),
        judge_epoch_sha256=epoch_sha, binding=binding, scalar=scalar.reference,
        source_parent_text_loaded=False, reference_captions_visible_to_player=False))
    games = {}
    while time.time() < config['deadline_unix']:
        for request_path in sorted((root / 'queue').glob('*.request.json')):
            output = request_path.with_name(request_path.name.replace('.request.json', '.result.json'))
            if output.exists():
                continue
            request = runtime.read(request_path)
            cell = request['identity']
            condition, seed, contest = cell['condition'], cell['seed'], cell['contest_id']
            data.require(condition == identity['condition'] and seed in epoch.SEEDS
                and contest in {item.contest_id for item in manifest.contests}, 'declared_source_scene_seed')
            data.require(request['raw_sha256'] == hashlib.sha256(request['raw'].encode()).hexdigest()
                and request['origin']['text_sha256'] == request['raw_sha256'], 'actual_generated_proposal')
            if seed not in games:
                games[seed] = build_game(manifest, scalar, panels, pixels, encoder, top_k=50,
                    agent_id=f'{condition}-{seed}', lane='R233_ADOPTED_PARENT_FREE_AGE',
                    relevance_threshold=rule['relevance_threshold'])
            scene = next(item for item in manifest.contests if item.contest_id == contest)
            actions, parsed = extract_batches(request['raw'], [dict(contest_id=contest,
                canonical_scene=scene.canonical_scene)], active_scene=contest,
                explicit_candidates_only=request['origin']['stage'] == 'THINK')
            results = []
            for action in actions:
                for caption in action['captions']:
                    outcome = games[seed].submit_caption(contest, caption)
                    results.append(dict(caption_sha256=hashlib.sha256(caption.encode()).hexdigest(), result=outcome))
            feedback = []
            for number, row in enumerate(results, 1):
                outcome = row['result']
                feedback.append(f"Caption {number}: rank {outcome.get('rank')} of 65; accepted {outcome.get('accepted')}; "
                    f"novelty {outcome.get('status')}; relevance {outcome.get('relevance_score')}; cached {outcome.get('cached', False)}.")
            if not feedback:
                feedback.append('No caption was scored in this output. Offer the captions themselves for the active scene; no fixed format is required.')
            runtime.write(output, dict(request_sha256=contract.digest(request), unix=time.time(),
                judge_epoch_sha256=epoch_sha, results=results, parsed=parsed, feedback='\n'.join(feedback),
                new_pixels=sum(row['result'].get('status') == 'new_pixel'
                    and not row['result'].get('cached', False) for row in results)))
        if (root / 'players' / identity['condition'] / 'COMPLETE.json').exists():
            break
        time.sleep(0.1)
    runtime.write(root / 'JUDGE_EXIT.json', dict(unix=time.time(), pid=os.getpid(), judge_epoch_sha256=epoch_sha))


def player(config):
    root, identity = verify(config)
    source = None
    if not config['plain_base']:
        source = runtime.read(root / 'sources/CAPTURE.json')['sources'][0]
        data.require(source['source_name'] == identity['source_name']
            and source['absolute_sleep'] == identity['absolute_sleep']
            and source['sleep_complete_sha256'] == identity['sleep_complete_sha256'], 'same_completed_adapter_source')
    condition = identity['condition']
    output = root / 'players' / condition
    started = time.time()
    backend = runtime.Backend(source, root)
    loaded = runtime.wait(root / 'JUDGE_LOADED.json', config['deadline_unix'])
    epoch_sha = loaded['judge_epoch_sha256']
    data.require(loaded['binding']['adapter_sha256'] == epoch.ADAPTER_SHA, 'adopted_loaded_judge')
    runtime.write(output / 'LOADED.json', dict(unix=time.time(), pid=os.getpid(), condition=condition,
        model_load_seconds=time.time() - started, source_age=source, identity=backend.identity,
        policy=contract.POLICY, snapshot_context_used=False, parent_tokens=0,
        source_parent_text_loaded=False, judge_epoch_sha256=epoch_sha,
        actual_visible_device=os.environ['CUDA_VISIBLE_DEVICES']))
    results = []
    for scene in runtime.read(root / 'GAME_MANIFEST.json')['contests']:
        for seed in epoch.SEEDS:
            cell = output / f"{scene['contest_id']}_{seed}"
            counter = 0
            def score(raw, stage, origin):
                nonlocal counter
                counter += 1
                key = f"{condition}-{scene['contest_id']}-{seed}-{counter:04d}"
                request = dict(identity=dict(condition=condition, seed=seed, contest_id=scene['contest_id']),
                    raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), origin=origin)
                runtime.write(root / 'queue' / f'{key}.request.json', request)
                return epoch.bound_result(request,
                    runtime.wait(root / 'queue' / f'{key}.result.json', config['deadline_unix']), epoch_sha)
            def emit(value):
                runtime.write(cell / f'{counter:04d}.json', value)
            result = contract.run_cell(backend, scene, seed, score, emit)
            result.update(contest_id=scene['contest_id'], seed=seed)
            runtime.write(cell / 'RESULT.json', result)
            results.append(result)
    runtime.write(output / 'COMPLETE.json', dict(unix=time.time(), condition=condition, cells=results,
        actual_generated_tokens=sum(item['generated_tokens'] for item in results),
        unchanged_identity=backend.verify(), elapsed_seconds=time.time() - started,
        judge_epoch_sha256=epoch_sha, source_age=source, parent_tokens=0, training_updates=0,
        raw_acceptance_not_certified_literal_jokes=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--mode', choices=['player', 'judge'], required=True)
    options = parser.parse_args()
    data.require(epoch.sha(options.config) == options.config_sha256, 'pinned_operator_configuration')
    config = runtime.read(options.config)
    root, identity = verify(config)
    runtime.write(root / (options.mode + '_DEVICE_PROOF.json'), runtime.device_proof(config[options.mode + '_physical']))
    try:
        (player if options.mode == 'player' else judge)(config)
    except Exception as error:
        runtime.write(root / (options.mode + '_FAILED.json'), dict(unix=time.time(),
            error_type=type(error).__name__, error=str(error), result='INCOMPLETE_NOT_ZERO'))
        raise


if __name__ == '__main__':
    main()
