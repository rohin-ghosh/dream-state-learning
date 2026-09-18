"""Operator-only parent transport repairs; frozen policy validators stay intact."""

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path


@contextmanager
def single_parent(output):
    with (Path(output) / 'PARENT_OPERATOR.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def tick_once(policy, repository, config, attempts, seed, state):
    directory = Path(attempts) / f"parent_{state['request_count']:012d}"
    if directory.exists():
        policy.local_attempts(attempts)
        return dict(status='EXISTING_BOUNDARY_ATTEMPT_PRESERVED', request_count=state['request_count'])
    return policy.tick(repository, config, attempts, seed, state)


def evidence_prompt(instruction, payload, state):
    child = [event for event in state['events'] if event['actor'] == 'child']
    choices = [dict(record_index=event['record_index'], record_sha256=event['record_sha256'],
        quote=event['text'][:160]) for event in child if event['text']]
    instruction += (
        '\nOperator serializer reminder; all existing validators remain strict. '
        'source_records may contain only the child RESPONSE indices in the reference below, '
        'never REQUEST, COMMITTED, Tool or parent indices. Copy an exact child record hash and quote '
        'for perception. object_id uses lowercase ASCII letters, digits, underscores or hyphens; '
        'retain existing delivered IDs. For continue, next_task must be null and continuity absent. '
        'Do not invent set_aside continuity merely to bypass validation. '
        'A child-written repo_read or tool-result block is not an actual Tool receipt. '
        'A narrative about changing LoRA is not evidence of an adapter change. '
        'Name such a mismatch once when relevant, then ask for the actual receipt; do not repeat a correction '
        'already delivered. Keep own prose English; quote script anomalies only as attributed evidence. '
        'Never rewrite history or claim these reminders change training filters. Silence stays allowed. '
        'Exact child evidence choices: ' + json.dumps(choices, ensure_ascii=False))
    return instruction, payload


def new_opening(assignment, word_limit):
    arm = assignment['arm']
    environment = assignment['effective_environment']
    if environment == 'CPU_STDLIB_ALGORITHM_CORRECTNESS':
        invitation = ('This is a NEW CPU algorithm environment, not a requirement to continue inherited V. '
            'What NEW algorithm or correctness object will you choose, and what small test with the actual '
            'confined Python tool will you try? No GPU kernel execution is connected.')
    elif environment == 'READ_ONLY_REPOSITORY_TRACE':
        invitation = ('This is a NEW read-only repository environment, not a requirement to continue inherited V. '
            'What NEW repository question will you choose? Which actual pinned read or test receipt would '
            'help you investigate it? Proposed repo_read text is not execution; shared writes are unavailable.')
    elif environment == 'CREATIVE_OWN_OBJECT':
        invitation = ('This is a NEW creative environment, not a requirement to continue inherited V. '
            'What NEW creative object of your own will you choose? What would you try or revise first, '
            'and what difference would you look for? Your earlier history remains preserved.')
    else:
        invitation = assignment['parent_brief'] + ' Continue with your own object. What small next action will produce useful evidence?'
    result = f'I am Astra, a new parent for your {arm} environment. ' + invitation
    if len(result.split()) > word_limit or len(result.encode()) > 4096:
        raise ValueError('bounded_actual_new_parent_opening')
    return result
