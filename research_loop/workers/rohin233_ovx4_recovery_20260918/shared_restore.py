"""Restore authentic native game sessions using the unchanged frozen scorer."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_life_service import LifeSession, restoration_evidence
from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub, serve
from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import BASE_ROOT, device_proof, prepare_assets
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import allocation_guard, restore_contract, verify_files


class RestoredHub(Hub):
    def __init__(self, root, registry, game_factory, scenes, rule, recovery):
        self.root, self.game_factory, self.scenes, self.rule = Path(root), game_factory, scenes, rule
        self.registry, self.sessions, self.restored = {}, {}, []
        self.base = None
        for item in registry['rows']:
            identifier = item['session_id']
            data.require(identifier not in self.registry and identifier.replace('_', '').isalnum(), 'unique_safe_owner_session_name')
            reference = recovery['sessions'][identifier]
            state = data.bound(reference)
            output = self.root / 'sessions' / identifier
            mirror = self.root / 'mirrors' / identifier
            data.require(output.is_dir() and mirror.is_dir(), 'existing_saved_session_and_authentic_mirror')
            self.registry[identifier] = item
            session = LifeSession(game_factory(identifier), mirror, output, scenes,
                resume_state=state, session_binding=item)
            evidence = restore_contract(state, session.snapshot())
            self.sessions[identifier] = session
            self.restored.append(dict(session_id=identifier, **evidence,
                **restoration_evidence(session, reference)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    allocation_guard(config, config['physical'])
    root, recovery = Path(config['service_root']), Path(config['recovery_root'])
    verify_files(Path(config['source_root']), config['source_files'])
    lock = (recovery / 'service.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    data.private_write(recovery / 'DEVICE_PROOF.json', device_proof(config['physical']))
    started = time.time()
    assets, rule, manifest, scenes = prepare_assets(root)
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    original = data.bound(data.file_ref(assets / 'base_manifest.json'))
    base_ref = data.private_write(recovery / 'base_manifest.json', dict(original, root=BASE_ROOT))
    runtime = data.private_write(recovery / 'scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
        base_model=base_ref, selected_adapter_root=str(assets / 'adapter'),
        adapter={name: data.file_ref((assets / 'adapter' / name).resolve()) for name in rule['adapter']},
        config=dict(max_length=rule['max_length']), source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar = ScalarJudge(runtime['path'], batch_size=8)
    encoder = FrozenCPUEncoder(data.file_ref((assets / 'embedding_snapshot.json').resolve()), threads=2)
    panels = data.bound(data.file_ref(assets / 'PANEL_SCORES.private.json'))
    pixels = PixelConfig(**data.bound(data.file_ref(assets / 'pixel_config.json')))

    def game_factory(identifier):
        return build_game(manifest, scalar, panels, pixels, encoder, top_k=50, agent_id=identifier,
            lane='R210_LIVE_DEVELOPMENT', relevance_threshold=rule['relevance_threshold'])

    registry = data.bound(config['registry'])
    data.require(registry['complete'], 'complete_actual_owner_registry')
    hub = RestoredHub(root, registry, game_factory, scenes, rule, config)
    data.private_write(recovery / 'LOADED.json', dict(pid=os.getpid(), unix=time.time(),
        physical=config['physical'], deadline_unix=config['deadline_unix'],
        model_load_seconds=time.time()-started, rule_sha256=data.digest(rule), top_k=50,
        reference_count=64, restored_sessions=hub.restored, source=data.file_ref(Path(__file__).resolve()),
        service_kind='EXACT_RESTORED_SHARED_SCORER_NOT_LEARNER', historical_rescoring=False))
    serve(hub, config['deadline_unix'])


if __name__ == '__main__':
    main()
