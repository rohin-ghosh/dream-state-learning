"""Source-bound model-parent mailbox; credentials remain on the operator VM."""

import argparse
import json
from pathlib import Path
import sys

from retirement import PROTECTED, record, save, sha


MODEL = 'openai/openai/gpt-6-astra'
OUTPUTS = ('r233_classroom_handoff_v1/live', 'r233_all_five_caption_epochs_v1')


def message(result, request_sha256):
    response = result['response']
    text = response['message']
    if (result['request_sha256'] != request_sha256 or result['model'] != MODEL
            or response['speak'] is not True or not isinstance(text, str)
            or not text.isascii() or not 0 < len(text.split()) <= 90 or len(text) >= 2200
            or not result.get('usage')):
        raise ValueError('exact_authenticated_bounded_model_parent_required')
    for field in ('provider_response_sha256', 'provider_dispatch_sha256'):
        value = result[field]
        if len(value) != 64 or any(character not in '0123456789abcdef' for character in value):
            raise ValueError('actual_provider_evidence_required')
    return text


def own_observation(helper, root, name):
    paths = list(helper.records(root, name))[-128:]
    actual = []
    tool_messages = []
    request_seen = False
    for path, kind in reversed(paths):
        if kind == 'R184_ACT' and len(actual) < 2:
            act = record(path)
            origin = act['document']['origin']
            response = record(path.with_name(f"{origin['record_index']:020d}.json"))
            if (origin['kind'] != 'TRAIN_CHILD_RESPONSE' or response['kind'] != 'RESPONSE'
                    or response['sha256'] != origin['record_sha256']):
                raise ValueError('own_actual_response_origin_required')
            raw = response['document']['response']['raw']
            actual.append(dict(ACT=dict(index=act['index'], sha256=act['sha256']),
                RESPONSE=dict(index=response['index'], sha256=response['sha256']),
                excerpt=raw[:6000], excerpt_truncated=len(raw) > 6000))
        if kind == 'REQUEST' and not request_seen:
            request_seen = True
            request = record(path)
            messages = request['document']['messages']
            tool_messages = [dict(REQUEST=dict(index=request['index'], sha256=request['sha256']),
                excerpt=value['content'][:4000]) for value in messages
                if isinstance(value.get('content'), str) and value['content'].startswith('Tool: ')][-3:]
        if len(actual) == 2 and request_seen:
            break
    return dict(life=name, actual_outputs=actual, actually_rendered_Tool_messages=tool_messages,
        missing_feedback_not_inferred_as_success=not bool(tool_messages))


def model_text(helper, root, name, directory, policy_text, current):
    request_path = directory / 'PROVIDER_REQUEST.json'
    if not request_path.exists():
        group = ('r213_math_a', 'r213_math_b_fork', 'r213_math_c') if name.startswith('r213_math_') else (name,)
        prior = current['publication']
        if sha(Path(prior['path'])) != prior['sha256']:
            raise ValueError('prior_published_history_must_remain_authenticated')
        save(request_path, dict(life=name, policy_text=policy_text,
            previous_parent=dict(id=prior['id'], sha256=prior['sha256'], text=prior['text']),
            observations=[own_observation(helper, root, member) for member in group],
            parent_kind='MODEL_PROVIDER_REQUEST_NOT_YET_PUBLISHED',
            original_history_unchanged=True, native_controls=0))
    result_path = directory / 'PROVIDER_RESULT.json'
    if not result_path.exists():
        return None
    return message(json.loads(result_path.read_bytes()), sha(request_path))


def jobs(root):
    found = []
    for output in OUTPUTS:
        for name in PROTECTED:
            for directory in sorted((root / output / name).glob('turn_*')):
                request = directory / 'PROVIDER_REQUEST.json'
                if request.exists() and not any((directory / filename).exists()
                        for filename in ('PROVIDER_RESULT.json', 'PROVIDER_FAILED.json', 'PUBLISHED.json')):
                    found.append(dict(relative=str(directory.relative_to(root)),
                        request_sha256=sha(request), request=json.loads(request.read_bytes())))
    return found


def accept(root, value):
    selected = [job for job in jobs(root) if job['relative'] == value['relative']]
    if len(selected) != 1:
        raise ValueError('exact_pending_source_bound_job_required')
    job = selected[0]
    message(value['result'], job['request_sha256'])
    save(root / job['relative'] / 'PROVIDER_RESULT.json', value['result'])
    return dict(accepted=True, request_sha256=job['request_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('pending', 'accept'))
    parser.add_argument('--root', required=True, type=Path)
    options = parser.parse_args()
    print(json.dumps(jobs(options.root) if options.mode == 'pending'
        else accept(options.root, json.load(sys.stdin))))
