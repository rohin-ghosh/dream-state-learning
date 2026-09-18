"""Warm an identical scorer, then acquire only a drained COMPLETE session."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_life_service import LifeSession, restoration_evidence
from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate, put
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract


def read(path):
    return json.loads(Path(path).read_bytes())


def await_handoff(config):
    root = Path(config['root'])
    while not (root / 'HANDOFF.json').exists():
        if time.time() >= config['deadline_unix']:
            raise TimeoutError('lease_boundary')
        time.sleep(.1)
    handoff = read(root / 'HANDOFF.json')
    if Path('/proc', str(config['predecessor_pid'])).exists():
        raise ValueError('predecessor_must_release_writer_first')
    return handoff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    config = read(parser.parse_args().config)
    validate(config)
    root = Path(config['root'])
    prior = data.bound(config['prior_config'])
    started = time.time()
    if config['kind'] == 'p3':
        from gpu.ny_caption_life_service import load_session, serve
        arguments = argparse.Namespace(**prior['arguments'], output=str(root / 'warm'),
            resume_state=None, resume_state_sha256=None, top_k=50)
        warm = load_session(arguments)
        put(root / 'MODEL_WARM.json', dict(unix=time.time(), pid=os.getpid(), ready_to_restore=True,
            session_writer=False, model_load_seconds=time.time()-started, deadline_unix=config['deadline_unix']))
        handoff = await_handoff(config)
        reference = handoff['sessions']['p3']
        state = data.bound(reference)
        session = LifeSession(warm.game, state['life_root'], root / 'session', state['scene_ids'],
            resume_state=state, source_mode=state['source_mode'], session_binding=state['session_binding'])
        evidence = {**restore_contract(state, session.snapshot()), **restoration_evidence(session, reference)}
        put(root / 'LOADED.json', dict(unix=time.time(), pid=os.getpid(), physical=config['physical'],
            deadline_unix=config['deadline_unix'], sessions=[evidence], historical_rescoring=False))
        serve(session, config['socket'], int(config['deadline_unix']-time.time()))
        return

    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import BASE_ROOT, prepare_assets
    from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub, serve
    from research_loop.workers.rohin233_ovx4_recovery_20260918.shared_restore import RestoredHub
    original = Path(prior['service_root']) if config['kind'] == 'shared' else Path(prior['original_root'])
    assets_root = original if config['kind'] == 'shared' else Path(config['prior_config']['path']).parent / 'scorer'
    assets, rule, manifest, scenes = prepare_assets(assets_root)
    original_base = data.bound(data.file_ref((assets / 'base_manifest.json').resolve()))
    base = data.private_write(root / 'base_manifest.json', dict(original_base, root=BASE_ROOT))
    runtime = data.private_write(root / 'scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
        base_model=base, selected_adapter_root=str(assets / 'adapter'),
        adapter={name:data.file_ref((assets / 'adapter' / name).resolve()) for name in rule['adapter']},
        config=dict(max_length=rule['max_length']), source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar = ScalarJudge(runtime['path'], batch_size=8)
    encoder = FrozenCPUEncoder(data.file_ref((assets / 'embedding_snapshot.json').resolve()), threads=2)
    panels = data.bound(data.file_ref((assets / 'PANEL_SCORES.private.json').resolve()))
    pixels = PixelConfig(**data.bound(data.file_ref((assets / 'pixel_config.json').resolve())))

    def game_factory(identifier):
        return build_game(manifest, scalar, panels, pixels, encoder, top_k=50, agent_id=identifier,
            lane='R210_LIVE_DEVELOPMENT', relevance_threshold=rule['relevance_threshold'])

    put(root / 'MODEL_WARM.json', dict(unix=time.time(), pid=os.getpid(), ready_to_restore=True,
        session_writer=False, model_load_seconds=time.time()-started, deadline_unix=config['deadline_unix']))
    handoff = await_handoff(config)
    sockets = root / 'sockets'
    sockets.mkdir(exist_ok=True)
    if config['kind'] == 'shared':
        registry = data.bound(prior['registry'])
        hub = RestoredHub(original, registry, game_factory, scenes, rule, dict(sessions=handoff['sessions']))
        evidence = hub.restored
        hub.root = sockets
    else:
        from research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch import EpochSession
        reference = handoff['sessions']['base']
        state = data.bound(reference)
        session = EpochSession(game_factory('R224_CONTINUOUS_FROZEN_BASE'), state['life_root'],
            original / 'scorer', scenes, resume_state=state, source_mode=state['source_mode'],
            session_binding=state['session_binding'])
        session.transition = read(Path(config['prior_config']['path']).parent / 'TRANSITION.private.json')
        evidence = [{**restore_contract(state, session.snapshot()), **restoration_evidence(session, reference)}]
        hub = Hub(sockets, dict(complete=True, rows=[]), game_factory, scenes, rule)
        hub.base = session
    put(root / 'LOADED.json', dict(unix=time.time(), pid=os.getpid(), physical=config['physical'],
        deadline_unix=config['deadline_unix'], sessions=evidence, historical_rescoring=False))
    serve(hub, config['deadline_unix'])


if __name__ == '__main__':
    main()
