"""Provisional development game: fixed within-contest references, scalar rank, novelty."""

import argparse
import json
import random
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_game import CaptionGame, DevelopmentManifest, GameConfig, RelativeJudgeResult, VisualResult
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_scalar_judge import ScalarJudge, relative_position


POLICY = 'R207_FIXED_DEVELOPMENT_REFERENCE_RANK_V1'


class RelativeRankJudge:
    def __init__(self, scalar, panels, top_k):
        data.require(panels and all(isinstance(scene, str) and scores for scene, scores in panels.items()),
                     'nonempty_fixed_scene_reference_panels')
        for scores in panels.values():
            relative_position(0.0, scores, top_k)
        self.scalar, self.panels, self.top_k = scalar, panels, top_k

    def __call__(self, scene, caption):
        data.require(scene in self.panels, 'unregistered_development_scene')
        score = self.scalar.score([dict(scene=scene, caption=caption)])[0]
        result = relative_position(score, self.panels[scene], self.top_k)
        return RelativeJudgeResult(**{key: result[key] for key in ('raw_score', 'rank', 'reference_count', 'top_k')})


def prepare_references(source_manifest, game_manifest, scalar, *, panel_size=64, seed=207):
    data.require(type(panel_size) is int and 8 <= panel_size <= 512, 'bounded_development_reference_panel')
    manifest = data.load_manifest(source_manifest)
    allowed = set(manifest['pools']['agent_development'])
    requested = {contest.contest_id for contest in game_manifest.contests}
    data.require(requested == allowed, 'only_exact_agent_development_references_not_FINAL_or_judge_pools')
    panels, records = {}, []
    for contest in game_manifest.contests:
        reference = manifest['contests'][contest.contest_id]['rows']
        data.require(data.file_ref(Path(reference['path']).resolve())['sha256'] == reference['sha256'],
                     'development_reference_rows_unchanged')
        eligible = {}
        with Path(reference['path']).open() as stream:
            for line in stream:
                row = json.loads(line)
                data.require(row['contest_id'] == contest.contest_id, 'reference_contest_join')
                caption = data.normalize_caption(row['caption'])
                if caption and len(caption.split()) <= 50:
                    eligible.setdefault(caption, row)
        captions = sorted(eligible)
        random.Random(f'{seed}:{contest.contest_id}').shuffle(captions)
        selected, excluded = [], 0
        for caption in captions:
            if scalar.token_count(contest.canonical_scene, caption) > scalar.max_length:
                excluded += 1
                continue
            selected.append(dict(scene=contest.canonical_scene, caption=caption))
            if len(selected) == panel_size:
                break
        data.require(len(selected) == panel_size, 'enough_untruncated_development_references')
        scores = scalar.score(selected)
        data.require(contest.canonical_scene not in panels, 'distinct_scene_panel_identity')
        panels[contest.canonical_scene] = scores
        records.append(dict(contest_id=contest.contest_id, source_rows_sha256=reference['sha256'],
                            selected=selected, scores=scores, overlength_skipped=excluded))
    return panels, records


def build_game(game_manifest, scalar, panels, pixel_config, encoder, *, top_k=8,
               agent_id='C2-development', lane='DEVELOPMENT', inspect_provider=None):
    data.require(encoder.model_id == pixel_config.embedding_model_id
                 and encoder.revision == pixel_config.embedding_revision, 'actual_pixel_encoder_matches_config')
    if inspect_provider is None:
        def inspect_provider(image, question):
            raise RuntimeError('Live image inspection not configured; no fabricated observation')
    return CaptionGame(agent_id, lane, game_manifest, GameConfig(acceptance_mode='relative_rank'),
                       pixel_config, embed=encoder, judge=RelativeRankJudge(scalar, panels, top_k),
                       inspect_provider=inspect_provider,
                       count_tokens=lambda text: len(scalar.tokenizer.encode(text, add_special_tokens=False)))


def run(args):
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    output = Path(args.output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    game_ref = data.file_ref(Path(args.game_manifest).resolve())
    manifest = DevelopmentManifest.from_mapping(data.bound(game_ref))
    data_ref = data.file_ref(Path(args.data_manifest).resolve())
    captions_ref = data.file_ref(Path(args.captions).resolve())
    actions = data.bound(captions_ref)
    data.require(isinstance(actions, list) and 1 <= len(actions) <= 100, 'bounded_caption_actions')
    allowed = {contest.contest_id for contest in manifest.contests}
    data.require(all(isinstance(action, dict) and set(action) == {'contest_id', 'text', 'origin'}
                     and action['contest_id'] in allowed and isinstance(action['text'], str)
                     and isinstance(action['origin'], dict) for action in actions), 'explicit_caption_origin_and_contest')
    started = time.time()
    scalar = ScalarJudge(args.judge_config, batch_size=args.batch_size)
    panels, private = prepare_references(data_ref, manifest, scalar, panel_size=args.panel_size, seed=args.seed)
    panel_ref = data.private_write(output / 'REFERENCE_PANELS.private.json', private)
    encoder_ref = data.file_ref(Path(args.encoder_manifest).resolve())
    encoder = FrozenCPUEncoder(encoder_ref, threads=2)
    pixel_config = PixelConfig(**json.loads(Path(args.pixel_config).read_text()))
    game = build_game(manifest, scalar, panels, pixel_config, encoder, top_k=args.top_k,
                      agent_id=args.agent_id, lane=args.lane)
    data.private_write(output / 'LOADED.json', dict(policy=POLICY, loaded_unix=time.time(),
                       scalar=scalar.reference, game_manifest=game_ref, encoder=encoder_ref,
                       panel_sha256=panel_ref['sha256'], panel_size=args.panel_size, top_k=args.top_k,
                       novelty='FROZEN_MINILM_EMBEDDING_ONLY_PROVISIONAL', tau=None,
                       FINAL_read=False, locked_validation_read=False))
    results = []
    for index, action in enumerate(actions):
        data.private_write(output / 'actions' / f'{index:04d}.json', dict(action=action, unix=time.time()))
        result = game.submit_caption(action['contest_id'], action['text'])
        results.append(result)
        data.private_write(output / 'outcomes' / f'{index:04d}.json', dict(result=result, unix=time.time(),
                           actor='environment', child_training_target=False))
        data.private_write(output / 'snapshots' / f'{index:04d}.json', game.snapshot())
        if not result.get('ok'):
            break
    summary = dict(policy=POLICY, status='COMPLETE_REAL_DEVELOPMENT_GAME' if len(results) == len(actions)
                   and all(row.get('ok') for row in results) else 'FAILED_PRESERVED',
                   completed_unix=time.time(), elapsed_seconds=time.time() - started,
                   attempts=len(results), accepted=sum(row.get('accepted') is True for row in results),
                   new_pixels=sum(row.get('status') == 'new_pixel' for row in results),
                   per_attempt=[{key: row.get(key) for key in ('ok', 'accepted', 'status', 'rank', 'reference_count',
                                'top_k', 'raw_score', 'q', 'pixel_count')} for row in results],
                   label='PROVISIONAL_FIXED_PANEL_TOP_K_NOT_CALIBRATED_HUMOR_OR_GLOBAL_CONTEST_RANK',
                   learning_or_retention_demonstrated=False, scene_fit_demonstrated=False,
                   pixel_config=data.file_ref(Path(args.pixel_config).resolve()), actions_sha256=captions_ref['sha256'])
    data.private_write(output / 'PUBLIC_RESULT.json', summary)
    print(data.canonical(summary).decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game-manifest', 'data-manifest', 'judge-config', 'encoder-manifest', 'pixel-config', 'captions', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--agent-id', default='C2-development')
    parser.add_argument('--lane', default='DEVELOPMENT')
    parser.add_argument('--panel-size', type=int, default=64)
    parser.add_argument('--top-k', type=int, default=8)
    parser.add_argument('--seed', type=int, default=207)
    parser.add_argument('--batch-size', type=int, default=8)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
