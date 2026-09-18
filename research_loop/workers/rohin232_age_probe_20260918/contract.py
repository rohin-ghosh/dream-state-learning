"""Finite parent-free inference contract; no training or live-life controls."""

from copy import deepcopy
import hashlib
import json
import math


POLICY = 'R232_FRESH_DEVELOPMENT_FIXED_TOKENS_V1'
SEEDS = (23201, 23202)
BUDGET = 1024
DECODER = dict(do_sample=True, temperature=0.8, top_p=0.95, top_k=0,
               num_beams=1, repetition_penalty=1.0)
SYSTEM = (
    'You are writing original cartoon captions in a development game. '
    'Only the active scene described here is available in this opportunity. '
    'Explore ideas in THINK and offer the captions themselves in ACT. '
    'Use English. You may write naturally: no required fields, count, or JSON. '
    'Feedback is provisional rank among 64 development references, relevance, '
    'and embedding novelty; acceptance requires rank at most 50 and relevance. '
    'Acceptance is not proof of humor. There is no parent in this probe.'
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def initial_messages(scene):
    if set(scene) != {'contest_id', 'canonical_scene'}:
        raise ValueError('scene_only_no_source_state')
    return [dict(role='system', content=SYSTEM), dict(role='user',
        content='Active scene 1:\n' + scene['canonical_scene'])]


def run_cell(backend, scene, seed, score, emit, *, budget=BUDGET):
    if type(budget) is not int or budget <= 0:
        raise ValueError('positive_integer_budget')
    backend.seed(seed)
    messages = initial_messages(scene)
    initial_sha = digest(messages)
    generated_tokens = 0
    prompt_tokens = 0
    events = []
    stage = 'THINK'
    while generated_tokens < budget:
        limit = min(128 if stage == 'THINK' else 256, budget - generated_tokens)
        instruction = ('THINK: Explore possible caption ideas for this active scene.' if stage == 'THINK'
            else 'ACT: Offer your captions for the active scene. You may continue or revise after feedback.')
        request = messages + [dict(role='user', content=instruction)]
        generation = backend.generate(deepcopy(request), max_new_tokens=limit)
        tokens = generation['token_ids']
        if generation['messages'] != request or not isinstance(generation['raw'], str):
            raise ValueError('generation_request_binding')
        if not isinstance(tokens, list) or len(tokens) > limit or any(type(token) is not int or token < 0 for token in tokens):
            raise ValueError('actual_generation_budget')
        if type(generation['prompt_tokens']) is not int or generation['prompt_tokens'] <= 0:
            raise ValueError('actual_prompt_count')
        if not tokens:
            return dict(status='INCOMPLETE_ZERO_TOKEN_GENERATION', generated_tokens=generated_tokens,
                budget=budget, initial_context_sha256=initial_sha, events=events)
        before = generated_tokens
        generated_tokens += len(tokens)
        prompt_tokens += generation['prompt_tokens']
        origin = dict(request_sha256=digest(request), response_sha256=digest(generation),
            text_sha256=hashlib.sha256(generation['raw'].encode()).hexdigest(), stage=stage,
            generated_tokens_before=before, generated_tokens_after=generated_tokens)
        receipt = score(generation['raw'], stage, origin)
        event = dict(origin=origin, actual_generated_tokens=len(tokens),
            prompt_tokens=generation['prompt_tokens'], requested_max_new_tokens=limit,
            terminal=generation['terminal'], truncated=generation['truncated'], score=receipt,
            token_bin_end=256 * math.ceil(generated_tokens / 256))
        emit(dict(request=request, generation=generation, event=event))
        events.append(event)
        messages = request + [dict(role='assistant', content=generation['raw']),
            dict(role='user', content='Tool feedback:\n' + receipt['feedback'])]
        stage = 'ACT' if stage == 'THINK' else 'THINK'
    return dict(status='COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET', budget=budget,
        generated_tokens=generated_tokens, prompt_tokens=prompt_tokens,
        initial_context_sha256=initial_sha, events=events,
        no_updates=True, parent_tokens=0, learn_or_other_reply_tokens=0)


def select_fresh(packet, exposure, *, count=3):
    if packet['pool'] != 'agent_development' or any(packet[key] is not False for key in
            ('FINAL_included', 'historical_captions_included', 'ratings_included')):
        raise ValueError('development_images_only')
    if exposure['complete'] is not True or exposure['unresolved_request_content']:
        raise ValueError('complete_source_exposure_audit_required')
    excluded = set(exposure['excluded_contest_ids'])
    selected = [row for row in packet['tasks'] if str(row['contest_id']) not in excluded][:count]
    if len(selected) != count:
        raise ValueError('insufficient_fresh_development_images')
    return selected
