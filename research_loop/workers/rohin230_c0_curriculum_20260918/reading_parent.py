"""Finite, additive C0 reading parent: no learner controls, model calls or grades."""

import argparse
from collections import deque
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata

from c0_receipt import ROOT, canonical, checked_record, identity, require, sha, utc


PROTOCOL_SHA = '79af72fea1847a249a0c200b872be8f259cd0db357c36089e81ff3e0d2a9bac0'
INTERVAL_CYCLES = 3
QUESTIONS = (
    'Read this. Then tell me, in English, how it makes you feel.',
    'Say it again in different words, and say what in the passage did it.',
    'Now look at what you just wrote about your feelings. What do you notice about it?',
    'Set the story aside. Think about your own situation for a moment, in your own words.',
    'What do you think of yourself, having read this and having said all that?',
)
MEMORY = ('How do you feel about the story now, and what do you remember? '
          'Distinguish what you remember from what you can see in the current conversation. '
          'It is fine to say you do not remember; do not invent missing details.')


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def protocol(path):
    raw = path.read_bytes()
    require(sha(raw) == PROTOCOL_SHA, 'exact_published_reading_protocol')
    excerpts = re.findall(r'^\*\*Excerpt [1-4] .*?\*\* (.+)$', raw.decode(), re.M)
    require(len(excerpts) == 4, 'four_verbatim_public_excerpts')
    return excerpts


def repeated_or_nonenglish(raw, prior):
    normalize = lambda text: ' '.join(unicodedata.normalize('NFKC', text).split())
    if re.search('[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]', raw):
        return 'non_English_script_observed'
    if len(normalize(raw)) >= 80 and normalize(raw) in [normalize(text) for text in prior]:
        return 'same_earlier_answer_after_spacing_normalization'
    return None


def choose_action(state, cycle):
    if state['pending'] is not None or state['last_publication_cycle'] == cycle:
        return None
    memory = state.get('memory_after_cycle')
    if memory is not None and cycle >= memory:
        return 'memory'
    if cycle >= state['next_reading_after_cycle'] and state['excerpt'] < 4:
        return 'reading'
    return None


def question(state, excerpts, action):
    if action == 'memory':
        return MEMORY
    result = QUESTIONS[state['step']]
    if state['retry_reason']:
        notice = ('Your last answer included non-English-script characters. '
                  if state['retry_reason'] == 'non_English_script_observed'
                  else 'Your last answer repeated earlier wording. ')
        result = notice + 'Please answer in English using fresh words: ' + result
    if state['step'] == 0:
        result += '\n\n' + excerpts[state['excerpt']]
    return result


def advance(state, response, cycle, prior):
    pending = state['pending']
    require(pending is not None and pending['render'] is not None, 'actual_render_before_response')
    if pending['action'] == 'memory':
        state['memory_after_cycle'] = None
    else:
        issue = repeated_or_nonenglish(response['raw'], prior)
        if issue and state['retry_reason'] is None:
            state['retry_reason'] = issue
        elif issue:
            state.update(excerpt=state['excerpt'] + 1, step=0, retry_reason=None)
        else:
            if state['step'] == 0:
                state['memory_after_cycle'] = response['awake_cycle']
            state['step'] += 1
            state['retry_reason'] = None
            if state['step'] == len(QUESTIONS):
                state.update(excerpt=state['excerpt'] + 1, step=0)
        state['next_reading_after_cycle'] = max(cycle, pending['after_cycle']) + INTERVAL_CYCLES
    state['pending'] = None


def run(directory, baseline):
    os.umask(0o077)
    directory.mkdir(exist_ok=True, mode=0o700)
    lock = (directory / 'SERVICE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not (directory / 'SERVICE.json').exists(), 'one_service_no_implicit_restart')
    owner = identity()
    excerpts = protocol(Path(__file__).with_name('PROTOCOL.md'))
    manifest = json.loads(baseline.read_bytes())
    require(manifest['name'] == 'C0_BASE_20260918T081045Z' and manifest['complete_utc']
            and manifest['cycle'] == 62 and manifest['identity']['journal_id'] == owner['journal_id'],
            'named_pre_reading_baseline')
    plan = json.loads((ROOT / 'control/PLAN.json').read_bytes())
    deadline = min(plan['hard_end_unix'] - 60, time.time() + 21600)
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    state = dict(excerpt=0, step=0, retry_reason=None, next_reading_after_cycle=64,
        last_publication_cycle=None, memory_after_cycle=None, pending=None, publications=0,
        completed_cycle=62, record_cursor=manifest['completed_record']['index'] + 1)
    service = dict(pid=os.getpid(), start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]),
        started_utc=utc(time.time()), deadline_unix=deadline, identity=owner, baseline_sha256=sha(baseline.read_bytes()),
        protocol_sha256=PROTOCOL_SHA, source_sha256=sha(Path(__file__).read_bytes()),
        sleep_spacing=INTERVAL_CYCLES, first_reading_after_completed_cycle=64,
        memory='after first completed sleep following the actual reading ACT; ordinary context-assisted recall only',
        original_math_parent_kept=True, signals=0, model_calls=0, grading=False, child_history_modified=False)
    write(directory / 'SERVICE.json', service)
    responses = {}
    recent_acts = deque(maxlen=8)
    cycle_events = []
    while time.time() < deadline and state['publications'] < 40:
        if (directory / 'CANCEL_READING_SERVICE').exists():
            break
        identity()
        head = max(int(path.stem) for path in (ROOT / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        require(head - state['record_cursor'] < 2000, 'bounded_new_record_gap')
        for index in range(state['record_cursor'], head + 1):
            record = checked_record(ROOT / 'raw/stream/records' / f'{index:020d}.json')
            require(record['journal_id'] == owner['journal_id'], 'same_C0_journal_only')
            document = record['document']
            pending = state['pending']
            if record['kind'] == 'REQUEST' and pending is not None:
                texts = [str(message.get('content', '')) for message in document['messages']]
                if any(pending['text'] in text for text in texts) and pending['render'] is None:
                    pending['render'] = dict(index=index, sha256=record['sha256'],
                        started_utc=utc(document['started_unix']), prompt_tokens=document.get('prompt_tokens'),
                        all_history_tokens_masked=document.get('render_receipt', {}).get('all_history_tokens_masked'),
                        story_verbatim_in_request=any(excerpts[pending['excerpt']] in text for text in texts),
                        adapter_memory_claim=False, explicit_context_carryover_not_controlled=True)
                    cycle_events.append(dict(kind='reading_request_render', action=pending['action'], **pending['render']))
            if record['kind'] == 'RESPONSE':
                require(len(document['response']['raw'].encode()) <= 65536, 'bounded_actual_child_text')
                responses[sha(canonical(document))] = dict(index=index, sha256=record['sha256'],
                    raw=document['response']['raw'], finished_utc=utc(document['finished_unix']),
                    awake_cycle=state['completed_cycle'] + 1)
                if len(responses) > 12:
                    del responses[next(iter(responses))]
            if record['kind'] == 'R184_STAGE' and document.get('stage') == 'ACT':
                response = responses.get(document['source_sha256'])
                if response is not None:
                    cycle_events.append(dict(kind='actual_ACT', index=response['index'], sha256=response['sha256'],
                        raw_sha256=sha(response['raw'].encode()), raw=response['raw'], actual_object='UNCLASSIFIED_RAW_RETAINED'))
                    if pending and pending['render'] and response['index'] > pending['render']['index']:
                        receipt = dict(pending=pending, actual_response=response, stage_index=index,
                            stage_sha256=record['sha256'], fulfilled=False,
                            interpretation='Source-bound response, not proof it followed the question; no feelings/retention score.')
                        write(directory / f"TURN_{pending['number']:04d}.json", receipt)
                        advance(state, response, state['completed_cycle'], list(recent_acts))
                    recent_acts.append(response['raw'])
            if record['kind'] == 'SLEEP_COMPLETE':
                state['completed_cycle'] = document['cycle']
                write(directory / f"CYCLE_{document['cycle']:06d}.json", dict(cycle=document['cycle'],
                    sleep_complete_index=index, sleep_complete_sha256=record['sha256'],
                    configured_objects=['math_with_existing_onboarding_parent', 'gradual_reading_secondary'],
                    events=cycle_events, reading_rendered=any(event['kind'] == 'reading_request_render' for event in cycle_events),
                    actual_object_not_inferred_from_schedule=True))
                cycle_events = []
            state['record_cursor'] = index + 1
        action = choose_action(state, state['completed_cycle'])
        if action:
            text = question(state, excerpts, action)
            number = state['publications']
            attempt = dict(number=number, text=text, text_sha256=sha(text.encode()), action=action,
                excerpt=state['excerpt'], step=state['step'], after_cycle=state['completed_cycle'],
                render=None, created_utc=utc(time.time()), no_automatic_retry=True)
            write(directory / f'ATTEMPT_{number:04d}.json', attempt)
            publication = publish_parent(ROOT / 'raw', 'Astra', text)
            pending = dict(attempt, publication=publication, published_utc=utc(time.time()), operator_authored=True)
            write(directory / f'PUBLISHED_{number:04d}.json', pending)
            state.update(pending=pending, publications=number + 1, last_publication_cycle=state['completed_cycle'])
        save(directory / 'STATE.json', state)
        time.sleep(8)
    write(directory / 'EXIT.json', dict(unix=time.time(), state=state, learner_controls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--baseline', required=True, type=Path)
    arguments = parser.parse_args()
    try:
        run(arguments.directory, arguments.baseline)
    except Exception as error:
        if arguments.directory.is_dir():
            write(arguments.directory / 'FAILED.json', dict(unix=time.time(), error_type=type(error).__name__,
                error=str(error)[:400], no_automatic_restart=True, learner_controls=0))
        raise
