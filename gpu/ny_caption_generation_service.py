"""Independent owner-local scorer for source-bound standalone generations."""

import argparse
from pathlib import Path

from gpu import ny_caption_data as data
from gpu.ny_caption_life_service import LifeSession, load_session, serve
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import KIND, process_generation


class GenerationSession(LifeSession):
    def process(self, request):
        return process_generation(self, request, receipt_root=self.life_root,
            expected_binding=self.session_binding['controller'],
            expected_backend_state=self.session_binding['backend'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game-manifest', 'data-manifest', 'image-map', 'judge-config', 'encoder-manifest',
                 'pixel-config', 'relevance-config', 'receipt-root', 'binding-config',
                 'binding-config-sha256', 'agent-id', 'output', 'socket'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--seconds', type=int, default=5400)
    parser.add_argument('--top-k', type=int, default=50)
    parser.add_argument('--resume-state')
    parser.add_argument('--resume-state-sha256')
    args = parser.parse_args()
    data.require(0 < args.seconds <= 21600 and args.top_k == 50, 'bounded_top50_standalone_service')
    binding = data.bound(dict(path=str(Path(args.binding_config).resolve()), sha256=args.binding_config_sha256))
    data.require(set(binding) == {'controller', 'backend'}, 'operator_pinned_generation_binding')
    plan = binding['controller']['plan']
    data.require(plan['condition'] == args.agent_id and plan['top_k'] == 50
        and plan['reference_count'] == 64, 'same_condition_top50_rule')
    args.life_root = str(Path(args.receipt_root).resolve(strict=True))
    session = load_session(args, session_class=GenerationSession, source_mode=KIND, session_binding=binding)
    data.private_write(session.output / 'GENERATION_SERVICE_BOUND.json', dict(
        source=data.file_ref(Path(__file__).resolve()), binding=data.file_ref(Path(args.binding_config).resolve()),
        receipt_root=args.life_root, learner_or_training_LOADED=False))
    serve(session, args.socket, args.seconds)


if __name__ == '__main__':
    main()
