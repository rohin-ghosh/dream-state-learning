"""Append-only reconciliation of one authenticated pre-publication rejection."""

import copy
import hashlib
from pathlib import Path
import types

import p3_retry_observe as observer


HERE = Path(__file__).resolve().parent
ATTEMPT = 'parent_000000000312'
RECEIPT = HERE / 'P3_RETRY_PUBLICATION_RESOLUTION.json'


def rejection(result, intent):
    observer.require(result['status'] == 'PUBLICATION_UNKNOWN'
        and result.get('publication') is None and result.get('error_type') == 'RuntimeError'
        and '/p3_endpoint.py", line 53, in main\n    predecessor.host()\n' in result['error']
        and '/MATH_C/math_c.py", line 59, in host\n' in result['error'],
        'exact_historical_prepublication_host_rejection')
    observer.require(intent == dict(speaker='Astra', message=result['message']), 'same_original_publication_intent')
    return hashlib.sha256(result['message'].encode()).hexdigest()


def validate(directory, evidence):
    directory = Path(directory)
    result, source = observer.read(directory / 'RESULT.json'), observer.read(directory / 'SOURCE.json')
    message_sha = rejection(result, observer.read(directory / 'PUBLISH_INTENT.json'))
    observer.require(directory.name == ATTEMPT and evidence['attempt'] == ATTEMPT
        and evidence['resolution'] == 'NOT_PUBLISHED_PREPUBLICATION_HOST_REJECTION'
        and evidence['journal_id'] == source['journal_id'] == observer.JOURNAL_ID
        and result['source_sha256'] == observer.digest(directory / 'SOURCE.json')
        and evidence['source_sha256'] == result['source_sha256']
        and evidence['result_sha256'] == observer.digest(directory / 'RESULT.json')
        and evidence['intent_sha256'] == observer.digest(directory / 'PUBLISH_INTENT.json')
        and evidence['message_sha256'] == message_sha, 'pinned_original_attempt_resolution')
    remote = evidence['remote']
    observer.require(remote['message_sha256'] == message_sha and remote['matches'] == []
        and remote['endpoint_sha256'] == evidence['endpoint_sha256']
        and remote['authority']['journal_id'] == observer.JOURNAL_ID
        and remote['authority']['pid'] == 699464
        and remote['authority']['start_ticks'] == '33078516'
        and remote['authority']['loaded'] is False
        and remote['authority']['complete_index'] == 5243,
        'same_authenticated_preload_endpoint_and_inbox_audit')
    return source, result


def project(attempts, evidence, source, result):
    projected = [copy.deepcopy(attempt) for attempt in attempts]
    matches = 0
    for attempt in projected:
        if attempt['result']['status'] != 'PUBLICATION_UNKNOWN':
            continue
        observer.require(attempt['source'] == source and attempt['result'] == result,
            'other_uncertain_publication_requires_own_resolution')
        matches += 1
        attempt['result'].update(status='VALIDATION_FAILED',
            historical_status='PUBLICATION_UNKNOWN',
            publication_resolution=evidence['resolution'],
            publication_resolution_sha256=observer.content_digest(evidence))
    observer.require(matches == 1, 'exactly_one_pinned_resolution')
    return projected


def bind(policy, output):
    evidence = observer.read(RECEIPT)
    source, result = validate(Path(output) / ATTEMPT, evidence)
    original = policy.local_attempts

    def local_attempts(directory):
        observer.require(Path(directory) == Path(output), 'same_original_parent_ledger')
        validate(Path(output) / ATTEMPT, evidence)
        return project(original(directory), evidence, source, result)

    namespace = dict(policy.tick.__globals__, local_attempts=local_attempts)
    policy.tick = types.FunctionType(policy.tick.__code__, namespace,
        policy.tick.__name__, policy.tick.__defaults__, policy.tick.__closure__)
    policy.local_attempts = local_attempts
    return observer.digest(RECEIPT)
