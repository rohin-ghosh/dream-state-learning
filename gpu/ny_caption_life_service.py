"""One-life local caption judge, with private panels outside the learner source."""

import argparse
import json
import os
from pathlib import Path
import socketserver
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_action_policy import CaptionActionPolicy
from gpu.ny_caption_game import DevelopmentManifest
from gpu.ny_caption_life import HELP, LIMIT, POLICY, child_act, extract_batch
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_relative_game import build_game, prepare_references
from gpu.ny_caption_scalar_judge import ScalarJudge
from gpu.orch_r125_stream_journal import _decode
from gpu.orch_r189_outcome_allocation import SCHEMA as OUTCOME_POLICY, validate_tokens


DEFAULT_TOP_K = 50


def scoring_rule(top_k):
    data.require(type(top_k) is int and 1 <= top_k <= 65, 'rank_bar_between_one_and_65')
    return (f'Provisional acceptance: rank <= {top_k} of 65 (your caption plus 64 human captions), '
            'AND weak scene relevance AND new-pixel novelty. Every rank is retained for later analysis.')


class LifeSession:
    def __init__(self, game, life_root, output, scene_ids):
        self.game, self.life_root, self.output = game, Path(life_root).resolve(), Path(output).resolve()
        self.scene_ids = scene_ids
        self.policy = CaptionActionPolicy(game, outcome_policy=OUTCOME_POLICY)
        self.seen = set()

    def process(self, request):
        data.require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'exact_local_request')
        validate_tokens(request['metrics'])
        origin = request['origin']
        raw = child_act(self.life_root, origin)
        identifier = origin['record_sha256']
        data.require(identifier not in self.seen, 'duplicate_ACT_no_automatic_resubmit')
        target = self.output / 'attempts' / identifier
        target.mkdir(parents=True, mode=0o700, exist_ok=False)
        self.seen.add(identifier)
        data.private_write(target / 'REQUEST.json', dict(request=request, raw_act=raw, unix=time.time()))
        data.private_write(target / 'BEFORE.json', dict(game=self.game.snapshot(), policy=self.policy.snapshot()))
        format_metrics = None
        try:
            action, format_metrics = extract_batch(raw, self.scene_ids)
            report = (self.policy.submit(action, cycle_metrics=request['metrics']) if action else
                      dict(ok=False, error=format_metrics['unscored_reason'], feedback=[], help=HELP))
        except ValueError as error:
            action = None
            report = dict(ok=False, error=str(error), feedback=[], help=HELP, requested_count=0)
        report['format_metrics'] = format_metrics
        document = dict(policy=POLICY, origin=origin, raw_act=raw, action=action, report=report,
                        child_training_target=False, unix=time.time(), no_tau_gate=True)
        data.private_write(target / 'RESULT.json', document)
        data.private_write(target / 'AFTER.json', dict(game=self.game.snapshot(), policy=self.policy.snapshot()))
        reference = data.file_ref(target / 'RESULT.json')
        return dict(policy=POLICY, origin=origin, report=report, receipt_sha256=reference['sha256'])


def load_session(args):
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    scoring = scoring_rule(args.top_k)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    manifest_ref = data.file_ref(Path(args.game_manifest).resolve())
    manifest = DevelopmentManifest.from_mapping(data.bound(manifest_ref))
    scalar = ScalarJudge(args.judge_config, batch_size=8)
    panels, private = prepare_references(data.file_ref(Path(args.data_manifest).resolve()), manifest,
        scalar, data.bound(data.file_ref(Path(args.image_map).resolve())), panel_size=64, seed=207)
    data.private_write(output / 'REFERENCE_PANELS.private.json', private)
    encoder_ref = data.file_ref(Path(args.encoder_manifest).resolve())
    encoder = FrozenCPUEncoder(encoder_ref, threads=2)
    pixels = PixelConfig(**json.loads(Path(args.pixel_config).read_text()))
    relevance = data.bound(data.file_ref(Path(args.relevance_config).resolve()))
    data.require(relevance['policy'] == 'R209_MINILM_SCENE_CAPTION_COSINE_V1'
                 and relevance['encoder']['sha256'] == encoder_ref['sha256'], 'same_measured_relevance_gate')
    game = build_game(manifest, scalar, panels, pixels, encoder, top_k=args.top_k,
                      agent_id=args.agent_id, lane='R210_LIVE_DEVELOPMENT',
                      relevance_threshold=relevance['threshold'])
    scenes = [dict(number=index, scene=contest.canonical_scene)
              for index, contest in enumerate(manifest.contests, 1)]
    data.private_write(output / 'CHILD_ENVIRONMENT.json', dict(policy=POLICY, scenes=scenes, help=HELP,
        scoring=scoring))
    session = LifeSession(game, args.life_root, output, [contest.contest_id for contest in manifest.contests])
    data.private_write(output / 'LOADED.json', dict(policy=POLICY, pid=os.getpid(), unix=time.time(),
        life_root=str(session.life_root), game_manifest=manifest_ref, scalar=scalar.reference,
        source=data.file_ref(Path(__file__).resolve()), panel_size=64, top_k=args.top_k, tau=None,
        FINAL_read=False, locked_validation_read=False, parent_private_panel_access=False))
    return session


def serve(session, socket_path, seconds):
    path = Path(socket_path)
    data.require(not path.exists() and path.is_absolute(), 'new_absolute_local_socket')

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(125)
            raw = self.rfile.readline(LIMIT + 1)
            data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_request_line')
            request = _decode(raw)
            try:
                result = session.process(request)
            except Exception as error:
                result = dict(policy=POLICY, origin=request.get('origin'), report=dict(ok=False,
                    error='REQUEST_FAILED_NO_RETRY', error_type=type(error).__name__, feedback=[]))
            encoded = data.canonical(result) + b'\n'
            data.require(len(encoded) <= LIMIT, 'bounded_feedback')
            self.wfile.write(encoded)

    with socketserver.UnixStreamServer(str(path), Handler) as server:
        os.chmod(path, 0o600)
        server.timeout = 1
        data.private_write(session.output / 'LISTENING.json', dict(socket=str(path), pid=os.getpid(),
            unix=time.time(), deadline_unix=time.time() + seconds))
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            server.handle_request()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game-manifest', 'data-manifest', 'image-map', 'judge-config', 'encoder-manifest',
                 'pixel-config', 'relevance-config', 'life-root', 'agent-id', 'output', 'socket'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--seconds', type=int, default=5400)
    parser.add_argument('--top-k', type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()
    data.require(0 < args.seconds <= 21600, 'bounded_service_lifetime')
    serve(load_session(args), args.socket, args.seconds)


if __name__ == '__main__':
    main()
