"""Explicit, receipt-backed TRAIN-only ReasoningGym turns for matched lives."""

import argparse
import hashlib
from importlib.metadata import version
import inspect
import json
import math
import os
from pathlib import Path
import re
import time

from gpu import orch_r127_pilot_console as console
from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
from gpu.orch_r125_stream_journal import _digest, require


FAMILIES = ('countdown', 'knights_knaves', 'mini_sudoku')
PACKAGE_VERSION = '0.1.25'
MAX_TASKS = 24


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encoded(value) + b'\n')
        stream.flush()
        os.fchmod(stream.fileno(), 0o400)
        os.fsync(stream.fileno())


def task_id(index):
    require(type(index) is int and 0 <= index < MAX_TASKS, 'bounded_prospective_TRAIN_task')
    return f'rg/{FAMILIES[index % len(FAMILIES)]}/{1500000 + index}'


def dataset(index):
    from organism_v6.reasoning_gym_gym import ReasoningGymGym
    require(version('reasoning-gym') == PACKAGE_VERSION, 'pinned_reasoning_gym_version')
    gym = ReasoningGymGym(strict_verifier=True)
    identifier = task_id(index)
    require(gym.split_of(identifier) == 'train', 'TRAIN_only_no_gate_exam_canary')
    family, seed = identifier.split('/')[1:]
    source, entry = gym._item(family, int(seed))
    package = Path(inspect.getfile(type(source))).resolve().parents
    package_root = next(path for path in package if path.name == 'reasoning_gym')
    pins = {str(path.relative_to(package_root)): sha(path) for path in sorted(package_root.rglob('*.py'))}
    binding = dict(package_version=PACKAGE_VERSION, package_source_sha256=_digest(pins),
                   split_ledger_sha256=sha(Path(inspect.getfile(ReasoningGymGym)).with_name('reasoning_gym_families.json')))
    return source, entry, binding


def parse_answer(raw, *, terminal, truncated):
    require(type(raw) is str and len(raw) <= 65536 and type(terminal) is bool and type(truncated) is bool,
            'bounded_actual_generation')
    require(not (terminal and truncated), 'consistent_generation_boundary')
    declarations = list(re.finditer(
        r'(?im)(?P<xml><answer>)|^[ \t]*(?:ACT|ANSWER|FINAL ANSWER)[ \t]*[:：]', raw))
    if not declarations:
        return None
    declaration = declarations[-1]
    suffix = raw[declaration.end():]
    if declaration.group('xml'):
        closing = re.search(r'</answer>', suffix, re.IGNORECASE)
        if closing is None:
            return None
        answer = suffix[:closing.start()].strip()
    else:
        ending = re.search(r'\r?\n', suffix)
        if ending is None and (truncated or not terminal):
            return None
        answer = (suffix[:ending.start()] if ending else suffix).strip()
    return answer if 0 < len(answer) <= 4096 else None


def verify_triple(records, task_text):
    require(len(records) == 3 and all(type(record) is dict for record in records), 'three_actual_records')
    request, response, committed = records
    require([record['kind'] for record in records] == ['REQUEST', 'RESPONSE', 'COMMITTED'], 'committed_TRAIN_only')
    for previous, following in zip(records, records[1:]):
        require(following['index'] == previous['index'] + 1 and following['journal_id'] == previous['journal_id']
                and following['previous_sha256'] == previous['sha256'], 'adjacent_same_journal')
    for record in records:
        require(record['schema'] == 'R125_STREAM_JOURNAL_V1'
                and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
                'record_hash')
    requested = {key: value for key, value in request['document'].items() if key != 'resume_state'}
    received = response['document']
    require(requested['split'] == 'TRAIN' and received['request_sha256'] == _digest(requested)
            and committed['document']['source_sha256'] == _digest(received), 'TRAIN_request_response_commit_join')
    require(any(task_text in message.get('content', '') for message in requested['messages']), 'task_actually_rendered')
    generation = received['response']
    state = committed['document']['state']
    require(state['sha256'] == _digest(state['state']), 'committed_state_hash')
    row = state['state']['rows'][-1]
    require(row['split'] == 'TRAIN' and row['actor'] == 'child' and row['target'] == generation['raw']
            and row['token_ids'] == generation['token_ids'] and row['source_sha256'] == _digest(received)
            and row['prefix'] == requested['messages'] and row['prefix_loss'] is False and row['target_loss'] is True,
            'actual_own_training_row_join')
    return generation


def grade(source, entry, answer):
    score = source.score_answer(answer=answer, entry=entry)
    require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1, 'real_finite_verifier_score')
    return dict(score=float(score), accepted=score == 1.0)


def directory(root, index):
    root = Path(root)
    require(root.is_absolute() and root.resolve() == root and not any(path.is_symlink() for path in (root, *root.parents)),
            'canonical_life_root')
    require(root.parent.name.startswith('orch_r158_') and root.name in
            ('parented_learning', 'parented_frozen', 'unparented_learning'), 'only_new_matched_lives')
    task_id(index)
    return root / 'train_environment' / f'task_{index:06d}'


def offer(root, index):
    output = directory(root, index)
    source, entry, binding = dataset(index)
    del source
    text = ('Environment puzzle, training task ' + str(index + 1) + ':\n' + entry['question'].strip()
            + '\nWhen you want a check, write Answer: followed by your answer, or put a multiline answer '
              'inside <answer>...</answer>. You can investigate and revise; a proposal is not a verified result.')
    require(len(text) <= 12000, 'bounded_question')
    output.mkdir(parents=True, mode=0o700)
    receipt = dict(schema='R158_TRAIN_GYM_TASK_V1', task_id=task_id(index), task_index=index,
                   split='TRAIN', text=text, binding=binding, created_unix=time.time(), answer_key_published=False)
    path = output / 'TASK.json'
    write(path, receipt)
    write(output / 'PUBLICATION_INTENT.json', dict(receipt_sha256=sha(path), replay_allowed=False))
    publication = console._inbox(root, 'Tool', text, dict(path=str(path), sha256=sha(path)))
    write(output / 'PUBLICATION.json', publication)
    return dict(task_id=task_id(index), publication=publication, rendered=False)


def check(root, index, response_index):
    output = directory(root, index)
    task_path = output / 'TASK.json'
    task = json.loads(task_path.read_bytes())
    require(task['task_id'] == task_id(index) and task['split'] == 'TRAIN', 'exact_TRAIN_task')
    publication = json.loads((output / 'PUBLICATION.json').read_bytes())
    message_path = Path(publication['path'])
    require(message_path.parent == Path(root) / 'stream/inbox' and sha(message_path) == publication['sha256'],
            'original_task_publication')
    message = json.loads(message_path.read_bytes())
    require(message['actor'] == 'environment' and message['split'] == 'TRAIN' and message['text'] == task['text']
            and message['source_receipt'] == dict(path=str(task_path), sha256=sha(task_path)), 'published_task_receipt_binding')
    require(type(response_index) is int and response_index > 0, 'response_index')
    with _open_stream_directory(root, 'records') as (descriptor, unused_path):
        records = [_read_record(descriptor, number) for number in (response_index - 1, response_index, response_index + 1)]
    generation = verify_triple(records, task['text'])
    answer = parse_answer(generation['raw'], terminal=generation['terminal'], truncated=generation['truncated'])
    if answer is None:
        return dict(status='NO_COMPLETE_ANSWER', checked=False, response_index=response_index)
    attempt = output / f'answer_{response_index:020d}'
    attempt.mkdir(mode=0o700)
    write(attempt / 'INTENT.json', dict(response_index=response_index, response_sha256=records[1]['sha256'],
        generated_sha256=hashlib.sha256(generation['raw'].encode()).hexdigest(), answer=answer, task_sha256=sha(task_path),
        replay_allowed=False))
    source, entry, binding = dataset(index)
    require(binding == task['binding'] and entry['question'].strip() in task['text'], 'same_generator_and_question')
    result = grade(source, entry, answer)
    result.update(schema='R158_TRAIN_GYM_RESULT_V1', task_id=task_id(index), split='TRAIN', answer=answer,
        origin=dict(response_index=response_index, response_sha256=records[1]['sha256'], commit_sha256=records[2]['sha256']),
        generation_boundary=dict(terminal=generation['terminal'], truncated=generation['truncated']),
        binding=binding, finished_unix=time.time(), answer_key_published=False)
    result_path = attempt / 'RESULT.json'
    write(result_path, result)
    text = ('Training puzzle check: ' + ('accepted' if result['accepted'] else 'not accepted')
            + f"; verifier score {result['score']:.3f}. This is a real check of your submitted answer."
            + ' The reference answer is not shown.')
    write(attempt / 'PUBLICATION_INTENT.json', dict(result_sha256=sha(result_path), replay_allowed=False))
    publication = console._inbox(root, 'Tool', text, dict(path=str(result_path), sha256=sha(result_path)))
    write(attempt / 'PUBLICATION.json', publication)
    return dict(status='CHECKED', accepted=result['accepted'], result_path=str(result_path), publication=publication)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('offer', 'check'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--task-index', type=int, required=True)
    parser.add_argument('--response-index', type=int)
    arguments = parser.parse_args()
    result = offer(arguments.root, arguments.task_index) if arguments.action == 'offer' else check(
        arguments.root, arguments.task_index, arguments.response_index)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
