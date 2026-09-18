"""One frozen C2 THINK -> ACT after its own receipt-bound caption game feedback.

Main alone dispatches the assigned GPU. Keep generate_c2.py alongside this file.
Read only proposal receipts, scored own actions, and public game outcomes; never
open the judge configuration, reference panels, private data, or game snapshots.
This is inference context continuation, not an exact-state life or learning run.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time


FROZEN_GENERATOR_SHA256 = '610c8959f95c49ba7f92910a203b62db76f8b599978a55e4035d23d834360e65'
GENERATOR_PATH = Path(__file__).with_name('generate_c2.py')
if hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest() != FROZEN_GENERATOR_SHA256:
    raise RuntimeError('frozen_generator_hash_mismatch')
SPEC = importlib.util.spec_from_file_location('r209_frozen_generator', GENERATOR_PATH)
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)

POLICY = 'R209_FROZEN_C2_OWN_GAME_FEEDBACK_FOLLOWUP_V1'
EXTRACTION_POLICY = 'R209_SINGLE_OBJECT_LITERAL_FIELDS_CLOSING_PAREN_V1'
SUMMARY_FIELDS = ('ok', 'accepted', 'status', 'rank', 'reference_count', 'top_k', 'raw_score',
                  'q', 'pixel_count', 'relevance_score', 'relevance_threshold')
FEEDBACK_FIELDS = SUMMARY_FIELDS + ('contest_id', 'acceptance_mode', 'scoring_status', 'rejection_reason')
PARENT_FOLLOWUP = (
    'Parent follow-up: This is a new opportunity. The environment message contains actual results '
    'for your previous caption, not reference captions or parent quality judgments. Your previous '
    'ACT is retained verbatim, including any wire-format error. No previous caption text was repaired. '
    'Rank is within a fixed development panel, not a probability or global contest rank; raw_score '
    'is not calibrated q. THINK about this feedback and choose your own next direction and count. '
    'You may revise, change scenes, or offer zero to ten captions. Use only the same three factual '
    'scenes. Then ACT with a plain JSON array of objects containing exactly contest_id and text, '
    'at most fifty whitespace-separated words per caption. Do not add commentary, fences, or scores. '
    'THINK now; ACT will be requested next.'
)
require = generator.require


def read_receipt(path, sources, name):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and path.stat().st_size <= 2_097_152, 'bounded_receipt_required')
    raw = path.read_bytes()
    sources[name] = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    return generator.decode(raw)


def literal(raw, span):
    require(isinstance(span, list) and len(span) == 2 and all(type(value) is int for value in span)
            and 0 <= span[0] < span[1] <= len(raw), 'literal_span_required')
    value = generator.decode(raw[span[0]:span[1]])
    require(isinstance(value, str), 'literal_string_required')
    return value


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def bind_previous(previous, scored_actions, game_output, scenes, manifest_ref):
    previous, game_output = Path(previous), Path(game_output)
    sources = {}
    bound = read_receipt(previous/'INPUT.json', sources, 'previous_input')
    loaded = read_receipt(previous/'LOADED.json', sources, 'previous_loaded')
    frozen = read_receipt(previous/'FROZEN_AFTER.json', sources, 'previous_frozen_after')
    request = read_receipt(previous/'ACT_INPUT.json', sources, 'previous_act_input')
    generated = read_receipt(previous/'ACT_GENERATION.json', sources, 'previous_act_generation')
    stage = read_receipt(previous/'ACT_RECEIPT.json', sources, 'previous_act_receipt')
    thought = read_receipt(previous/'THINK_GENERATION.json', sources, 'previous_think_generation')
    require(bound['policy'] == generator.POLICY and bound['generator']['sha256'] == FROZEN_GENERATOR_SHA256
            and bound['factual_scenes'] == scenes and bound['game_manifest']['sha256'] == manifest_ref['sha256'],
            'same_original_proposal_and_game_manifest_required')
    provenance = bound['provenance']
    require(provenance['checkpoint']['sha256'] == generator.COMMIT_SHA256
            and provenance['source_complete'] == 51, 'same_C2_checkpoint51_required')
    for identity in (provenance, loaded, frozen):
        require(identity['base_sha256'] == generator.BASE_SHA256
                and identity['adapter_state_sha256'] == generator.ADAPTER_STATE_SHA256,
                'same_frozen_C2_not_judge_required')
    require(frozen['all_parameters_frozen'] is True, 'previous_frozen_after_required')
    expected = [dict(role='system', content=generator.PARENT_OPENER),
                dict(role='user', content='Factual game scenes:\n' + generator.canonical(scenes).decode()),
                dict(role='user', content=generator.THINK_INSTRUCTION),
                dict(role='assistant', content=thought['raw']),
                dict(role='user', content=generator.ACT_INSTRUCTION)]
    require(request['phase'] == 'ACT' and request['messages'] == expected
            and generated['messages'] == expected and isinstance(generated['raw'], str)
            and generated['terminal'] is True and generated['truncated'] is False,
            'complete_original_ACT_with_exact_context_required')
    require(stage['input']['sha256'] == sources['previous_act_input']['sha256']
            and stage['generation']['sha256'] == sources['previous_act_generation']['sha256'],
            'previous_ACT_receipt_hash_mismatch')
    actions = read_receipt(scored_actions, sources, 'scored_actions')
    summary = read_receipt(game_output/'PUBLIC_RESULT.json', sources, 'public_result')
    game_loaded = read_receipt(game_output/'LOADED.json', sources, 'game_loaded')
    require(isinstance(actions, list) and 1 <= len(actions) <= generator.MAX_CAPTIONS, 'bounded_actual_actions_required')
    require(summary['status'] == 'COMPLETE_REAL_DEVELOPMENT_GAME'
            and summary['actions_sha256'] == sources['scored_actions']['sha256']
            and summary['attempts'] == len(actions) and len(summary['per_attempt']) == len(actions)
            and game_loaded['game_manifest']['sha256'] == manifest_ref['sha256'], 'completed_same_game_actions_required')
    feedback = []
    valid_batch = None
    for index, action in enumerate(actions):
        require(set(action) == {'contest_id', 'text', 'origin'}, 'exact_scored_action_fields')
        generator.parse_captions(generator.canonical([{key: action[key] for key in ('contest_id', 'text')}]).decode(),
                                 {scene['contest_id'] for scene in scenes})
        origin = action['origin']
        require(origin['actor'] == 'C2' and origin['stage'] == 'ACT' and origin['source_complete'] == 51
                and origin['model_generated'] is True and origin['text_repaired'] is False
                and origin['checkpoint_sha256'] == generator.COMMIT_SHA256
                and origin['adapter_state_sha256'] == generator.ADAPTER_STATE_SHA256, 'own_unrepaired_C2_action_required')
        wire_valid = origin.get('original_wire_format_valid', True)
        require(type(wire_valid) is bool, 'explicit_wire_validity')
        if not wire_valid:
            require(len(actions) == 1 and origin['extraction_policy'] == EXTRACTION_POLICY
                    and origin['raw_generation_sha256'] == sources['previous_act_generation']['sha256'],
                    'explicit_original_wire_invalid_extraction_required')
            require(literal(generated['raw'], origin['contest_id_span']) == action['contest_id']
                    and literal(generated['raw'], origin['text_span']) == action['text'], 'literal_text_changed')
            extracted = read_receipt(Path(scored_actions).parent/'RECEIPT.json', sources, 'literal_extraction')
            failure = read_receipt(previous/'FAILED.json', sources, 'previous_wire_failure')
            require(extracted['status'] == 'LITERAL_CAPTION_FIELDS_EXTRACTED'
                    and extracted['original_caption_text_unchanged'] is True
                    and extracted['raw_generation_changed'] is False
                    and extracted['actions_sha256'] == sources['scored_actions']['sha256']
                    and extracted['malformed_generation_sha256'] == sources['previous_act_generation']['sha256']
                    and failure['status'] == 'FAILED_PRESERVED_NO_REPAIR_OR_RETRY', 'wire_failure_and_extraction_binding')
        else:
            require(origin['generation_sha256'] == sources['previous_act_generation']['sha256']
                    and origin['input_sha256'] == sources['previous_act_input']['sha256']
                    and origin['action_index'] == index, 'original_valid_action_binding')
            if valid_batch is None:
                valid_batch = generator.parse_captions(generated['raw'], {scene['contest_id'] for scene in scenes})
            require(len(valid_batch) == len(actions) and valid_batch[index] ==
                    {key: action[key] for key in ('contest_id', 'text')}, 'scored_caption_changed')
        saved_action = read_receipt(game_output/'actions'/f'{index:04d}.json', sources, f'action_{index}')
        outcome = read_receipt(game_output/'outcomes'/f'{index:04d}.json', sources, f'outcome_{index}')
        require(saved_action['action'] == action and outcome['actor'] == 'environment'
                and outcome['child_training_target'] is False and finite(outcome['unix']), 'actual_environment_action_outcome_join')
        result = outcome['result']
        require(result['contest_id'] == action['contest_id'] and result['ok'] is True
                and type(result['accepted']) is bool and result['acceptance_mode'] == 'relative_rank'
                and result['q'] is None, 'actual_relative_result_not_probability')
        require(all(type(result[key]) is int for key in ('rank', 'reference_count', 'top_k', 'pixel_count'))
                and 1 <= result['rank'] <= result['reference_count'] + 1
                and 1 <= result['top_k'] <= result['reference_count'] + 1 and result['pixel_count'] >= 0
                and all(finite(result[key]) for key in ('raw_score', 'relevance_score', 'relevance_threshold')),
                'finite_actual_relative_feedback_required')
        projection = {key: result.get(key) for key in SUMMARY_FIELDS}
        require(generator.canonical(projection) == generator.canonical(summary['per_attempt'][index]),
                'public_result_outcome_mismatch')
        feedback.append(dict(action_index=index, action={key: action[key] for key in ('contest_id', 'text')},
                             original_wire_format_valid=wire_valid, text_repaired=False,
                             result={key: result[key] for key in FEEDBACK_FIELDS if key in result}, unix=outcome['unix']))
    require(summary['accepted'] == sum(row['result']['accepted'] for row in feedback)
            and summary['new_pixels'] == sum(row['result']['status'] == 'new_pixel' for row in feedback),
            'public_aggregate_outcome_mismatch')
    payload = dict(actor='environment', attempts=feedback,
                   totals={key: summary[key] for key in ('attempts', 'accepted', 'new_pixels')},
                   completed_unix=summary['completed_unix'])
    return dict(sources=sources, feedback=payload, previous_loaded=loaded,
                context_before=expected + [dict(role='assistant', content=generated['raw'])])


def dataset_row(stream, message, *, phase, actor, source, generation=None):
    row = dict(message=deepcopy(message), phase=phase, actor=actor, source=source,
               external_text_masked=actor != 'C2', child_training_target=False, training_applied=False,
               learning_or_retention_claim=False, recorded_unix=time.time())
    if generation is not None:
        row.update(prompt_tokens=generation['prompt_tokens'], token_ids=generation['token_ids'],
                   generated_tokens=len(generation['token_ids']), terminal=generation['terminal'],
                   truncated=generation['truncated'])
    stream.write(generator.canonical(row) + b'\n')
    stream.flush()
    os.fsync(stream.fileno())


def opportunity(backend, scenes, provenance, binding, output):
    before_ref = generator.write(output/'CONTEXT_BEFORE.json', binding['context_before'])
    feedback_ref = generator.write(output/'FEEDBACK.json', binding['feedback'])
    messages = deepcopy(binding['context_before'])
    messages += [dict(role='user', content='Actual environment feedback (receipt fields):\n' +
                     generator.canonical(binding['feedback']).decode()), dict(role='user', content=PARENT_FOLLOWUP)]
    stages = []
    with (output/'DATASET.jsonl').open('xb') as dataset:
        os.chmod(output/'DATASET.jsonl', 0o600)
        for index, message in enumerate(messages):
            actor = 'environment' if index == len(messages)-2 else 'C2' if message['role'] == 'assistant' else 'parent'
            source = feedback_ref if actor == 'environment' else before_ref if index < len(messages)-2 else dict(policy=POLICY)
            dataset_row(dataset, message, phase='PRIOR_CONTEXT' if index < len(messages)-2 else 'FOLLOWUP_INPUT',
                        actor=actor, source=source)
        try:
            for phase, limit in (('THINK', generator.THINK_TOKENS), ('ACT', generator.ACT_TOKENS)):
                request_ref = generator.write(output/(phase+'_INPUT.json'), dict(phase=phase, messages=deepcopy(messages),
                                              max_new_tokens=limit, started_unix=time.time()))
                generation = backend.generate(deepcopy(messages), max_new_tokens=limit)
                generation_ref = generator.write(output/(phase+'_GENERATION.json'), generation)
                require(generation['messages'] == messages and isinstance(generation['raw'], str), 'generation_input_binding')
                require(type(generation['prompt_tokens']) is int and 0 < generation['prompt_tokens'] <= generator.CONTEXT_LIMIT
                        and isinstance(generation['token_ids'], list) and 0 < len(generation['token_ids']) <= limit
                        and all(type(token) is int and token >= 0 for token in generation['token_ids'])
                        and type(generation['terminal']) is bool and type(generation['truncated']) is bool,
                        'actual_bounded_generation_counters_required')
                message = dict(role='assistant', content=generation['raw'])
                messages.append(message)
                dataset_row(dataset, message, phase=phase, actor='C2', source=generation_ref, generation=generation)
                stages.append(dict(phase=phase, input=request_ref, generation=generation_ref,
                                   prompt_tokens=generation['prompt_tokens'], generated_tokens=len(generation['token_ids']),
                                   terminal=generation['terminal'], truncated=generation['truncated'], finished_unix=time.time()))
                generator.write(output/(phase+'_RECEIPT.json'), stages[-1])
                generator.write(output/('CONTEXT_AFTER_'+phase+'.json'), messages)
                require(generation['terminal'] and not generation['truncated'], 'incomplete_generation_no_repair_or_retry')
                if phase == 'THINK':
                    message = dict(role='user', content=generator.ACT_INSTRUCTION)
                    messages.append(message)
                    dataset_row(dataset, message, phase='ACT_INPUT', actor='parent', source=dict(policy=generator.POLICY))
        finally:
            generator.write(output/'CONTEXT_AFTER.json', messages)
            generator.write(output/'FROZEN_AFTER.json', backend.verify_unchanged())
    captions = generator.parse_captions(generation['raw'], {scene['contest_id'] for scene in scenes})
    actions = []
    for index, caption in enumerate(captions):
        origin = dict(actor='C2', stage='ACT', policy=POLICY, source_complete=51, action_index=index,
                      checkpoint_sha256=provenance['checkpoint']['sha256'], adapter_state_sha256=generator.ADAPTER_STATE_SHA256,
                      input_sha256=stages[-1]['input']['sha256'], generation_sha256=stages[-1]['generation']['sha256'],
                      caption_sha256=hashlib.sha256(caption['text'].encode()).hexdigest(), feedback_sha256=feedback_ref['sha256'],
                      previous_generation_sha256=binding['sources']['previous_act_generation']['sha256'],
                      original_wire_format_valid=True, model_generated=True, text_repaired=False, learning_or_retention_claim=False)
        actions.append(dict(caption, origin=origin))
    result = dict(policy=POLICY, status='CAPTIONS_GENERATED' if actions else 'NO_PROPOSALS', action_count=len(actions),
                  actions=generator.write(output/'actions.json', actions), stages=stages, feedback=feedback_ref,
                  dataset=generator.file_ref(output/'DATASET.jsonl'), context_before=before_ref,
                  context_after=generator.file_ref(output/'CONTEXT_AFTER.json'),
                  total_prompt_tokens=sum(stage['prompt_tokens'] for stage in stages),
                  total_generated_tokens=sum(stage['generated_tokens'] for stage in stages),
                  generation_calls=2, judge_calls=0, training_updates=0, previous_context_truncated=False,
                  private_panels_loaded=False, exact_state_continuation_claim=False,
                  learning_or_retention_demonstrated=False, completed_unix=time.time())
    generator.write(output/'RESULT.json', result)
    return result


def run(args):
    output = Path(args.output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    phase = 'BIND_ACTUAL_FEEDBACK'
    try:
        scenes, manifest_ref = generator.load_scenes(args.game_manifest)
        binding = bind_previous(args.previous_proposals, args.scored_actions, args.game_output, scenes, manifest_ref)
        provenance = generator.verify_checkpoint(args.adapter_root)
        generator.write(output/'INPUT.json', dict(policy=POLICY, game_manifest=manifest_ref, factual_scenes=scenes,
                        provenance=provenance, sources=binding['sources'], generator=generator.file_ref(__file__),
                        frozen_generator=generator.file_ref(GENERATOR_PATH), parent_followup=PARENT_FOLLOWUP,
                        context_selection='ALL_ORIGINAL_ACT_CONTEXT_PLUS_VERBATIM_ACT_AND_OWN_ACTUAL_FEEDBACK',
                        learning_or_retention_claim=False, exact_state_continuation_claim=False))
        phase = 'FROZEN_MODEL_LOAD'
        backend = generator.FrozenC2(args.base_root, args.adapter_root, args.device)
        generator.write(output/'LOADED.json', dict(loaded_unix=time.time(), pid=os.getpid(), provenance=provenance, **backend.identity))
        for key in ('base_sha256', 'adapter_state_sha256', 'tokenizer', 'decoder'):
            require(backend.identity[key] == binding['previous_loaded'][key], 'same_frozen_model_tokenizer_decoder_required')
        phase = 'ONE_FOLLOWUP_THINK_ACT'
        result = opportunity(backend, scenes, provenance, binding, output)
        print(json.dumps(dict(status=result['status'], action_count=result['action_count'], actions=result['actions'])))
        return 0 if result['action_count'] else 2
    except Exception as error:
        generator.write(output/'FAILED.json', dict(policy=POLICY, phase=phase, error_type=type(error).__name__,
                        reason=str(error) if isinstance(error, generator.ProposalError) else None,
                        json_error_position=error.pos if isinstance(error, json.JSONDecodeError) else None,
                        status='FAILED_PRESERVED_NO_REPAIR_OR_RETRY', failed_unix=time.time(),
                        raw_and_input_files_preserved=True, exact_state_continuation_claim=False,
                        learning_or_retention_demonstrated=False))
        print(json.dumps(dict(status='FAILED_PRESERVED_NO_REPAIR_OR_RETRY', phase=phase, error_type=type(error).__name__,
                              output=str(output))), file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game-manifest', 'base-root', 'adapter-root', 'previous-proposals', 'scored-actions', 'game-output', 'output'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--device', choices=['cuda:0'], default='cuda:0')
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
