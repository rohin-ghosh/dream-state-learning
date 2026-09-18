"""Bounded real-component DEVELOPMENT wiring smoke, without a child or training."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

from gpu.ny_caption_development import parse_actions, require, save_once
from gpu.ny_caption_game import CaptionGame, DevelopmentManifest, GameConfig
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_similarity import bound, file_pin


SCHEMA = 'NY_STAGE1_REAL_TOOLS_SMOKE_V1'
REFERENCE_FIELDS = ('game_manifest', 'judge_config', 'similarity_runtime',
                    'vision_packet', 'tokenizer_manifest', 'verifier_scope')


def validate_bundle(reference):
    bundle = bound(reference)
    require(set(bundle) == {'schema', 'mode', 'agent_id', 'lane', 'visual_endpoint',
                           'game', 'judge_budget', *REFERENCE_FIELDS}, 'exact_smoke_bundle_fields')
    require(bundle['schema'] == SCHEMA and bundle['mode'] == 'DEVELOPMENT', 'development_smoke_only')
    require(bundle['lane'] in ('PARENTED', 'UNPARENTED'), 'current_development_lineages')
    require(type(bundle['agent_id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,60}', bundle['agent_id']),
            'explicit_agent_namespace')
    require(type(bundle['visual_endpoint']) is str and
            re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}/?', bundle['visual_endpoint']),
            'local_Qwen_endpoint_only')
    require(1 <= int(bundle['visual_endpoint'].rsplit(':', 1)[1].rstrip('/')) <= 65535,
            'valid_local_service_port')
    documents = {name: bound(bundle[name]) for name in REFERENCE_FIELDS}
    manifest = DevelopmentManifest.from_mapping(documents['game_manifest'])
    from gpu.ny_caption_judge import validate_checkpoint
    from gpu.ny_caption_similarity import LABEL_MODEL, LABEL_SYSTEM, MODEL_ID, MODEL_REVISION
    from gpu.ny_caption_vision import ImagePacket
    judge, unused_training, unused_root = validate_checkpoint(bundle['judge_config'])
    game_config = GameConfig(**bundle['game'])
    require(game_config.tau == judge['tau']['threshold'], 'frozen_judge_threshold_required')
    require(game_config.transport_retries == 0 and game_config.visual_call_limit <= 8 and
            game_config.max_submissions_per_contest <= 8, 'bounded_smoke_no_transport_retry')
    similarity = documents['similarity_runtime']
    require(similarity['schema'] == 'NY_FROZEN_SIMILARITY_RUNTIME_V1' and
            similarity['verifier_required'] is True and similarity['provisional_model_annotations'] is True and
            similarity['label_prompt_sha256'] == hashlib.sha256(LABEL_SYSTEM.encode()).hexdigest(),
            'calibrated_real_similarity_required')
    pixels = PixelConfig(**similarity['pixel_config'])
    require(pixels.embedding_model_id == MODEL_ID and pixels.embedding_revision == MODEL_REVISION,
            'actual_frozen_sentence_encoder')
    packet = ImagePacket(documents['vision_packet'])
    for contest in manifest.contests:
        packet.expected(contest.image)
    scope = documents['verifier_scope']
    require(scope['schema'] == 'NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1' and
            scope['issuer'] == 'Main/Astra' and scope['no_reset'] is True and
            scope['provider_model'] == LABEL_MODEL and
            type(scope['active_seconds_max']) is int and 0 < scope['active_seconds_max'] <= 3600 and
            type(scope['absolute_end_unix']) in (float, int) and
            time.time() < scope['absolute_end_unix'] < float('inf') and
            scope['allowed_pool'] == 'agent_development' and scope['lane_id'] == bundle['agent_id'] and
            scope['label_call_cap'] == scope['pair_label_cap'] == 0 and
            0 < scope['verification_call_cap'] <= 32 and scope['retries'] == 0 and
            scope['locked_validation_reads'] == scope['FINAL_reads'] == 0,
            'separate_development_verifier_scope_not_training_labels')
    budget = bundle['judge_budget']
    require(set(budget) == {'max_model_examples', 'max_model_tokens', 'max_seconds'}, 'explicit_judge_smoke_limits')
    for name, ceiling in (('max_model_examples', 64), ('max_model_tokens', 32768), ('max_seconds', 600)):
        require(type(budget[name]) is int and 0 < budget[name] <= ceiling, 'bounded_judge:' + name)
    validate_tokenizer(documents['tokenizer_manifest'])
    return bundle, documents


def validate_tokenizer(manifest):
    require(set(manifest) == {'schema', 'model_id', 'revision', 'root', 'files'} and
            manifest['schema'] == 'NY_CHILD_TOKENIZER_V1' and
            manifest['model_id'] == 'Qwen/Qwen2.5-7B-Instruct' and
            re.fullmatch('[0-9a-f]{40}', manifest['revision']), 'pinned_child_tokenizer')
    root = Path(manifest['root'])
    require(root.is_absolute() and root == root.resolve(), 'canonical_tokenizer_root')
    required = {'tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt'}
    require(required <= set(manifest['files']) <= required | {'special_tokens_map.json', 'config.json'},
            'tokenizer_only_inventory')
    for name, checksum in manifest['files'].items():
        path = root / name
        require(not path.is_symlink() and path.is_file() and file_pin(path)['sha256'] == checksum,
                'pinned_tokenizer_bytes')
    require({path.name for path in root.iterdir()} == set(manifest['files']), 'no_unbound_tokenizer_files')
    return root


def load_game(bundle, documents, output):
    from transformers import AutoTokenizer
    from gpu.ny_caption_judge import load_cpu_judge
    from gpu.ny_caption_similarity import AstraAnnotator, CallBudget, FrozenCPUEncoder, SameJokeVerifier
    from gpu.ny_caption_vision import ImagePacket, LocalHTTPProvider
    tokenizer = AutoTokenizer.from_pretrained(str(validate_tokenizer(documents['tokenizer_manifest'])),
                                             local_files_only=True, trust_remote_code=False)
    similarity = documents['similarity_runtime']
    encoder = FrozenCPUEncoder(similarity['encoder_manifest'], threads=2)
    pixel_config = PixelConfig(**similarity['pixel_config'])
    require(encoder.model_id == pixel_config.embedding_model_id and
            encoder.revision == pixel_config.embedding_revision, 'loaded_encoder_matches_calibration')
    judge = load_cpu_judge(bundle['judge_config'], **bundle['judge_budget'])
    budget = CallBudget(output / 'verifier', bundle['verifier_scope'])
    verifier = SameJokeVerifier(AstraAnnotator(budget), lane_id=bundle['agent_id'], resolution=pixel_config.resolution)
    receipt_count = 0

    def receipt_sink(receipt):
        nonlocal receipt_count
        save_once(output / 'vision_receipts' / f'{receipt_count:04d}.json', receipt)
        receipt_count += 1

    vision = LocalHTTPProvider(bundle['visual_endpoint'], ImagePacket(documents['vision_packet']),
                               receipt_sink=receipt_sink, timeout=90)
    return CaptionGame(bundle['agent_id'], bundle['lane'],
        DevelopmentManifest.from_mapping(documents['game_manifest']), GameConfig(**bundle['game']), pixel_config,
        embed=encoder, judge=judge, inspect_provider=vision,
        count_tokens=lambda text: len(tokenizer.encode(text, add_special_tokens=False)), same_joke_verifier=verifier)


def validated_actions(document, manifest):
    require(type(document) is dict and set(document) == {'mode', 'actions'} and
            document['mode'] == 'DEVELOPMENT', 'development_actions_only')
    actions = document['actions']
    require(type(actions) is list and 0 < len(actions) <= 8, 'bounded_nonempty_smoke_actions')
    contests = {contest.contest_id for contest in manifest.contests}
    for action in actions:
        parsed = parse_actions(json.dumps(action, ensure_ascii=False))
        require(type(action) is dict and parsed == [action] and action['contest_id'] in contests,
                'explicit_allowed_game_action')
    return actions


def run_actions(game, actions, output):
    results = []
    for index, action in enumerate(actions):
        save_once(output / 'requests' / f'{index:04d}.json', dict(action=action, dispatched_unix=time.time()))
        if action['tool'] == 'inspect_image':
            result = game.inspect_image(action['contest_id'], action['question'])
        else:
            result = game.submit_caption(action['contest_id'], action['text'])
        save_once(output / 'results' / f'{index:04d}.json', dict(result=result, received_unix=time.time(),
            actor='environment', child_training_target=False))
        save_once(output / 'snapshots' / f'{index:04d}.json', game.snapshot())
        results.append(result)
        if result.get('ok') is not True:
            break
    return dict(schema=SCHEMA, status='COMPLETE_REAL_TOOL_SMOKE' if len(results) == len(actions) and
                all(result.get('ok') is True for result in results) else 'STOPPED_ON_TOOL_ERROR_NO_RETRY',
                attempted_actions=len(results), requested_actions=len(actions),
                child_generation_calls=0, child_training_updates=0, parenting_calls=0,
                scoring_validation_claim=False, final_launch_authorized=False)


def execute(bundle_ref, actions_ref, output, *, loader=load_game):
    output = Path(output).absolute()
    require(output == output.resolve(), 'canonical_private_smoke_output')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    save_once(output / 'STARTED.json', dict(schema=SCHEMA, bundle=bundle_ref, actions=actions_ref,
        started_unix=time.time(), no_automatic_retry=True, models_loaded=False))
    try:
        bundle, documents = validate_bundle(bundle_ref)
        actions = validated_actions(bound(actions_ref), DevelopmentManifest.from_mapping(documents['game_manifest']))
        game = loader(bundle, documents, output)
        result = run_actions(game, actions, output)
        save_once(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        save_once(output / 'FAILED.json', dict(status='FAILED_PRESERVED_NO_RETRY',
            error_type=type(error).__name__, finished_unix=time.time(), private_error_text_disclosed=False))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--bundle-sha256', required=True)
    parser.add_argument('--actions', required=True)
    parser.add_argument('--actions-sha256', required=True)
    parser.add_argument('--output', required=True)
    arguments = parser.parse_args()
    result = execute(dict(path=str(Path(arguments.bundle).resolve()), sha256=arguments.bundle_sha256),
        dict(path=str(Path(arguments.actions).resolve()), sha256=arguments.actions_sha256), arguments.output)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'COMPLETE_REAL_TOOL_SMOKE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
