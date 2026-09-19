"""Persistent frozen-base player or independent scorer on two assigned GPUs."""

import argparse
from dataclasses import asdict
import datetime
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_game import DevelopmentManifest
from gpu.ny_caption_generation_service import GenerationSession
from gpu.ny_caption_life_service import restoration_evidence, serve
from research_loop.workers.rohin221_continuous_caption_20260918.adapters import BaseBackend, SocketScorer
from research_loop.workers.rohin221_continuous_caption_20260918.collect import hourly
from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller, Plan, file_ref, write
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import KIND


BASE_ROOT = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
CONDITION = 'R224_CONTINUOUS_FROZEN_BASE'


def wait_for(path, deadline):
    while not path.exists():
        if time.time() >= deadline:
            raise TimeoutError('bounded_service_initialization_deadline')
        time.sleep(1)


def device_proof(physical):
    proof = {}
    for index in range(8):
        try:
            descriptor = os.open(f'/dev/nvidia{index}', os.O_RDWR)
        except OSError as error:
            proof[str(index)] = dict(opened=False, errno=error.errno)
        else:
            os.close(descriptor)
            proof[str(index)] = dict(opened=True)
    data.require(proof[str(physical)]['opened'] and sum(item['opened'] for item in proof.values()) == 1,
                 'one_assigned_device_open_seven_denied')
    return proof


def prepare_assets(root):
    assets = root / 'assets'
    inventory = json.loads((assets / 'INVENTORY.json').read_bytes())
    for relative, checksum in inventory.items():
        data.require(data.file_ref((assets / relative).resolve())['sha256'] == checksum, 'exact_scoring_asset')
    rule = json.loads((assets / 'RULE.json').read_bytes())
    manifest = DevelopmentManifest.from_mapping(json.loads((assets / 'GAME_MANIFEST.json').read_bytes()))
    scenes = [dict(contest_id=contest.contest_id, canonical_scene=contest.canonical_scene) for contest in manifest.contests]
    return assets, rule, manifest, scenes


def run_base(root, deadline, scenes, rule):
    plan = Plan(condition=CONDITION, rule_sha256=data.digest(rule), opportunities=96)
    plan.validate()
    player = root / 'player'
    (player / 'private/generations').mkdir(parents=True, exist_ok=True, mode=0o700)
    started = time.time()
    write(root / 'BASE_MODEL_LOADING.json', dict(pid=os.getpid(), unix=started, base_root=BASE_ROOT,
        visible_device=os.environ['CUDA_VISIBLE_DEVICES'], source=file_ref(__file__)))
    backend = BaseBackend(BASE_ROOT)
    loaded = time.time()
    binding = dict(rule_sha256=plan.rule_sha256, top_k=50, reference_count=64,
                   relevance=True, novelty=True, condition=CONDITION)
    scorer = SocketScorer(root / 'scoring.sock', binding, output=root / 'scorer')
    with Controller(player, plan, backend, scorer, scenes, extract_batches) as controller:
        write(root / 'BASE_LOADED.json', dict(pid=os.getpid(), unix=loaded, elapsed_seconds=loaded-started,
            kind=backend.kind, actual_identity=backend.state_receipt(), plan=asdict(plan),
            learning=False, optimizer_created=False, prior_history_reset=False,
            predicted_first_feedback_utc=datetime.datetime.fromtimestamp(loaded+180, datetime.timezone.utc).isoformat(),
            ETA_basis='actual_base_LOAD_plus_provisional180s_for_parallel_scorer_and_first_generation'))
        controller.step()
        wait_for(root / 'scorer/LISTENING.json', min(deadline, loaded + 600))
        while time.time() < deadline and controller.state['completed_opportunities'] < plan.opportunities:
            before = len(controller.state['events'])
            controller.step()
            public = json.loads((player / 'ATTEMPTS.public.json').read_bytes())
            write(root / 'HOURLY.public.json', hourly(public))
            if len(controller.state['events']) > before:
                event = controller.state['events'][-1]
                write(root / 'PROGRESS.public.json', dict(pid=os.getpid(), unix=time.time(),
                    opportunities_completed=controller.state['completed_opportunities'],
                    actual_last_attempt=event, persistent_model_and_history=True))
                if before == 0:
                    data.private_write(root / 'FIRST_FEEDBACK.public.json', dict(unix=time.time(),
                        source=event['source'], scored=event['scored'], accepted=event['accepted'],
                        novel=event['novel'], score_receipt_sha256=event.get('score_receipt_sha256'),
                        planned=event['planned'], parsed=event['parsed'], fault=event['fault']))
        write(root / 'BASE_FINISHED.json', dict(pid=os.getpid(), unix=time.time(),
            completed_opportunities=controller.state['completed_opportunities'],
            reason='opportunity_budget' if controller.state['completed_opportunities'] >= plan.opportunities else 'hard_wall',
            state_preserved=True))


def run_scorer(root, deadline, assets, rule, manifest, scenes):
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    output = root / 'scorer'
    output.mkdir(mode=0o700, exist_ok=False)
    started = time.time()
    write(root / 'SCORER_MODEL_LOADING.json', dict(pid=os.getpid(), unix=started,
        visible_device=os.environ['CUDA_VISIBLE_DEVICES'], source=file_ref(__file__)))
    original = json.loads((assets / 'base_manifest.json').read_bytes())
    base_ref = data.private_write(output / 'base_manifest.json', dict(original, root=BASE_ROOT))
    adapter_refs = {name:data.file_ref((assets / 'adapter' / name).resolve()) for name in rule['adapter']}
    runtime_ref = data.private_write(output / 'scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
        base_model=base_ref, selected_adapter_root=str(assets / 'adapter'), adapter=adapter_refs,
        config=dict(max_length=rule['max_length']), source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar = ScalarJudge(runtime_ref['path'], batch_size=8)
    encoder_ref = data.file_ref((assets / 'embedding_snapshot.json').resolve())
    encoder = FrozenCPUEncoder(encoder_ref, threads=2)
    panels = json.loads((assets / 'PANEL_SCORES.private.json').read_bytes())
    pixels = PixelConfig(**json.loads((assets / 'pixel_config.json').read_bytes()))
    game = build_game(manifest, scalar, panels, pixels, encoder, top_k=50, agent_id=CONDITION,
        lane='R210_LIVE_DEVELOPMENT', relevance_threshold=rule['relevance_threshold'])
    binding_path = root / 'player/BINDING.public.json'
    wait_for(binding_path, min(deadline, started + 600))
    binding = data.bound(data.file_ref(binding_path))
    data.require(binding['controller']['plan']['rule_sha256'] == data.digest(rule), 'exact_rule_binding')
    session = GenerationSession(game, root / 'player/private/generations', output, scenes,
        source_mode=KIND, session_binding=binding)
    data.private_write(output / 'LOADED.json', dict(pid=os.getpid(), unix=time.time(), elapsed_seconds=time.time()-started,
        source=file_ref(__file__), service_kind='CAPTION_SCORER_NOT_LEARNER', source_mode=KIND,
        binding=data.file_ref(binding_path), rule_sha256=data.digest(rule), independent_game_state=True,
        reused_fixed_reference_scores=True, original_panel_sha256=rule['original_panel_sha256'],
        top_k=50, reference_count=64, tau=None, FINAL_read=False,
        **restoration_evidence(session, None)))
    serve(session, root / 'scoring.sock', max(1, int(deadline-time.time())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=['base', 'scorer'], required=True)
    parser.add_argument('--physical', type=int, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    data.require(0 < args.deadline-time.time() <= 7200, 'two_hour_operator_wall')
    data.private_write(root / (args.mode.upper()+'_DEVICE_PROOF.json'), dict(
        pid=os.getpid(), unix=time.time(), physical=args.physical, devices=device_proof(args.physical)))
    try:
        assets, rule, manifest, scenes = prepare_assets(root)
        if args.mode == 'base':
            run_base(root, args.deadline, scenes, rule)
        else:
            run_scorer(root, args.deadline, assets, rule, manifest, scenes)
    except Exception as error:
        write(root / (args.mode.upper()+'_FAILED.json'), dict(pid=os.getpid(), unix=time.time(),
            error_type=type(error).__name__, error=str(error)[:320], no_automatic_restart=True))
        raise


if __name__ == '__main__':
    main()
