"""One fixed model, independent source-bound native and generation game states."""

import argparse
import json
import os
from pathlib import Path
import selectors
import socketserver
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_generation_service import GenerationSession
from gpu.ny_caption_life import POLICY, HELP, child_act
from gpu.ny_caption_life_service import LifeSession, restoration_evidence, scoring_rule
from research_loop.workers.rohin221_continuous_caption_20260918.journal_bundle import MAX_BYTES, import_records
from research_loop.workers.rohin221_continuous_caption_20260918.run_base_cohort import (
    BASE_ROOT, device_proof, prepare_assets,
)


class Hub:
    def __init__(self, root, registry, game_factory, scenes, rule):
        self.root, self.game_factory, self.scenes, self.rule = Path(root), game_factory, scenes, rule
        self.registry, self.sessions = {}, {}
        for item in registry['rows']:
            identifier = item['session_id']
            data.require(identifier not in self.registry and identifier.replace('_', '').isalnum(),
                         'unique_safe_owner_session_name')
            self.registry[identifier] = item
            output = self.root / 'sessions' / identifier
            output.mkdir(parents=True, mode=0o700, exist_ok=False)
            mirror = self.root / 'mirrors' / identifier
            game = game_factory(identifier)
            session = LifeSession(game, mirror, output, scenes, session_binding=item)
            self.sessions[identifier] = session
            data.private_write(output / 'SCORER_SESSION_BOUND.json', dict(session_id=identifier,
                source_life_root=item['life_root'], journal_id=item['journal']['journal_id'],
                native_LOADED_claim=False, independent_game=True, **restoration_evidence(session, None)))
        self.base = None

    def native(self, envelope):
        data.require(type(envelope) is dict and set(envelope) == {'session_id', 'request', 'records'},
                     'trusted_proxy_envelope_only')
        identifier = envelope['session_id']
        data.require(identifier in self.registry, 'owner_registered_session')
        config, session = self.registry[identifier], self.sessions[identifier]
        request = envelope['request']
        data.require(set(request) == {'origin', 'metrics'}, 'native_request_schema')
        import_records(session.life_root, envelope['records'], config['journal']['journal_id'])
        child_act(session.life_root, request['origin'])
        result = session.process(request)
        result['source_transport'] = dict(session_id=identifier, journal_id=config['journal']['journal_id'],
            source_life_root=config['life_root'], records_sha256=data.digest(envelope['records']),
            authenticated_operator_transport=True, child_network_access=False)
        return result

    def generation(self, request):
        if self.base is None:
            config_path = self.root / 'BASE_CONFIG.json'
            config = data.bound(data.file_ref(config_path))
            binding = data.bound(config['binding'])
            resume = data.bound(config['resume'])
            data.require(resume['phase'] == 'COMPLETE', 'complete_base_session_adoption')
            session = GenerationSession(self.game_factory('R224_CONTINUOUS_FROZEN_BASE'),
                config['receipt_root'], config['output'], self.scenes, resume_state=resume,
                source_mode='STANDALONE_GENERATION', session_binding=binding)
            self.base = session
            data.private_write(self.root / 'BASE_SESSION_RESTORED.json', dict(unix=time.time(),
                **restoration_evidence(session, config['resume'])))
        return self.base.process(request)


def serve(hub, deadline):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            payload = self.rfile.readline(MAX_BYTES * 2 + 1)
            data.require(payload.endswith(b'\n') and len(payload) <= MAX_BYTES * 2, 'bounded_proxy_payload')
            request = json.loads(payload)
            origin = request.get('request', request).get('origin')
            try:
                response = self.server.callback(request)
            except Exception as error:
                response = dict(policy=POLICY, origin=origin, report=dict(ok=False,
                    error='SOURCE_OR_SCORER_FAILURE_NO_AUTOMATIC_RETRY',
                    error_type=type(error).__name__, reason=str(error)[:160], feedback=[]))
            encoded = data.canonical(response) + b'\n'
            data.require(len(encoded) <= 262144, 'bounded_public_feedback')
            self.wfile.write(encoded)

    with selectors.DefaultSelector() as selector:
        servers = []
        try:
            for name, callback in [('native.sock', hub.native), ('base.sock', hub.generation)]:
                path = hub.root / name
                data.require(not path.exists(), 'new_shared_socket')
                server = socketserver.UnixStreamServer(str(path), Handler)
                server.callback = callback
                server.timeout = 1
                os.chmod(path, 0o600)
                selector.register(server, selectors.EVENT_READ)
                servers.append(server)
            data.private_write(hub.root / 'LISTENING.json', dict(pid=os.getpid(), unix=time.time(),
                deadline_unix=deadline, sessions=list(hub.sessions), serialized_GPU_calls=True))
            while time.time() < deadline:
                for key, unused in selector.select(timeout=1):
                    key.fileobj.handle_request()
        finally:
            for server in servers:
                server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--physical', type=int, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    data.require(0 < args.deadline - time.time() <= 21600, 'bounded_existing_lease_service')
    root = args.root.resolve()
    data.private_write(root / 'DEVICE_PROOF.json', device_proof(args.physical))
    started = time.time()
    assets, rule, manifest, scenes = prepare_assets(root)
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    original = data.bound(data.file_ref(assets / 'base_manifest.json'))
    base_ref = data.private_write(root / 'base_manifest.json', dict(original, root=BASE_ROOT))
    runtime = data.private_write(root / 'scalar_runtime.json', dict(schema='R207_SCALAR_RUNTIME_V1',
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
    registry = data.bound(data.file_ref(root / 'NATIVE_REGISTRY.json'))
    data.require(registry['complete'], 'complete_actual_owner_registry')
    hub = Hub(root, registry, game_factory, scenes, rule)
    data.private_write(root / 'CHILD_ENVIRONMENT.json', dict(scenes=[dict(number=number,
        scene=scene['canonical_scene']) for number,scene in enumerate(scenes, 1)], help=HELP,
        scoring=scoring_rule(50), rule_sha256=data.digest(rule)))
    data.private_write(root / 'LOADED.json', dict(pid=os.getpid(), unix=time.time(),
        model_load_seconds=time.time()-started, physical=args.physical, service_kind='SHARED_SCORER_NOT_LEARNER',
        models_loaded=1, encoders_loaded=1, independent_native_sessions=len(hub.sessions),
        rule_sha256=data.digest(rule), source=data.file_ref(Path(__file__).resolve()),
        registry=data.file_ref(root / 'NATIVE_REGISTRY.json'), top_k=50, reference_count=64,
        parent_private_panel_access=False, original_panel_sha256=rule['original_panel_sha256']))
    serve(hub, args.deadline)


if __name__ == '__main__':
    main()
