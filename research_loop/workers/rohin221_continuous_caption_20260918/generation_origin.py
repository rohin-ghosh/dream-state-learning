"""Owner-local standalone generation receipts; never a native journal origin."""

from pathlib import Path

from gpu import ny_caption_data as data
from research_loop.workers.rohin221_continuous_caption_20260918.controller import digest


KIND = 'STANDALONE_GENERATION'


def generation_origin(source, think_source=None):
    origin = dict(kind=KIND, request_id=source['request_id'], generation=source['generation'],
        request_sha256=source['request_sha256'], response_sha256=source['response_sha256'])
    if think_source is not None:
        origin['think'] = generation_origin(think_source)
    return origin


def validate_generation_origin(origin, *, receipt_root, expected_binding, expected_backend_state,
                               stage='ACT'):
    """Validate owner-bound files, stage, inputs, outputs, model and exact source pins."""
    keys = {'kind', 'request_id', 'generation', 'request_sha256', 'response_sha256'}
    data.require(type(origin) is dict and keys <= set(origin) <= keys | {'think'}
                 and origin['kind'] == KIND, 'standalone_origin_schema')
    root = Path(receipt_root).resolve(strict=True)
    path = Path(origin['generation']['path'])
    data.require(path.is_absolute() and path == path.resolve(strict=True)
        and path.is_relative_to(root) and path.is_file() and not path.is_symlink()
        and path.stat().st_size <= 1048576, 'confined_bounded_generation_receipt')
    document = data.bound(origin['generation'])
    request, generated = document['request'], document['generated']
    data.require(digest(request) == origin['request_id'] == origin['request_sha256']
        and digest(generated) == origin['response_sha256'], 'generation_request_response_hashes')
    data.require(request['binding'] == expected_binding
        and request['backend_state'] == expected_backend_state
        and request['condition'] == expected_binding['plan']['condition']
        and request['stage'] == stage, 'same_condition_model_source_stage')
    data.require(generated['messages'] == request['messages']
        and type(generated['raw']) is str and len(generated['raw'].encode()) <= 65536,
        'actual_generation_input_output')
    tokens = generated['token_ids']
    budget_key = 'think_tokens' if stage == 'THINK' else 'act_tokens'
    data.require(type(tokens) is list and all(type(token) is int and token >= 0 for token in tokens)
        and request['max_new_tokens'] == expected_binding['plan'][budget_key]
        and len(tokens) <= request['max_new_tokens']
        and type(generated['prompt_tokens']) is int
        and 0 < generated['prompt_tokens'] <= expected_binding['plan']['context_tokens']
        and all(type(generated[key]) is bool for key in ('terminal', 'truncated')),
        'actual_generation_token_and_termination_receipt')
    data.require(type(document['finished_unix']) in (int, float)
        and document['finished_unix'] > 0, 'generation_completion_time')
    validated = dict(raw=generated['raw'], origin=origin, stage=stage,
        source_sha256=origin['response_sha256'], generated_tokens=len(tokens),
        request=request, finished_unix=document['finished_unix'], think=None)
    if 'think' in origin:
        data.require(stage == 'ACT' and 'think' not in origin['think'], 'single_THINK_ancestor_only')
        think = validate_generation_origin(origin['think'], receipt_root=root,
            expected_binding=expected_binding, expected_backend_state=expected_backend_state, stage='THINK')
        data.require(think['request']['opportunity'] == request['opportunity']
            and think['finished_unix'] <= document['finished_unix'], 'same_opportunity_prior_THINK')
        validated['think'] = think
    return validated


def process_generation(session, request, *, receipt_root, expected_binding, expected_backend_state):
    """Main's generation service callback; session must be independently bound."""
    data.require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'exact_generation_request')
    binding = dict(controller=expected_binding, backend=expected_backend_state)
    data.require(session.source_mode == KIND and session.session_binding == binding
        and session.life_root == Path(receipt_root).resolve()
        and digest(session.scene_ids) == expected_binding['scenes_sha256'], 'independent_standalone_session_binding')
    verified = validate_generation_origin(request['origin'], receipt_root=receipt_root,
        expected_binding=expected_binding, expected_backend_state=expected_backend_state)
    think_tokens = verified['think']['generated_tokens'] if verified['think'] else 0
    data.require(request['metrics'] == dict(THINK=think_tokens if verified['request']['attempt'] == 1 else 0,
        ACT=verified['generated_tokens'], LEARN=0), 'actual_standalone_tokens_no_learning_claim')
    result = session.process_verified(request, verified['raw'], identifier=request['origin']['request_id'],
        think_resolver=lambda: verified['think'])
    return dict(result, request_id=request['origin']['request_id'],
        rule_sha256=expected_binding['plan']['rule_sha256'], condition=expected_binding['plan']['condition'])
