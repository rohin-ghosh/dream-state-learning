"""Non-material CPU publisher restoration; never controls a native or training rows."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import urllib.error

from remote_io import require


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORIGINAL = HERE.parent / 'rohin231_curriculum_birth_20260918'
RECOVERY = ORIGINAL / 'recovery_20260918T1646Z'
GAP_PREFIX = 'My parent publisher was offline; you kept running.'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    path = Path(path)
    if path.exists():
        require(read(path) == document, 'immutable_recovery_receipt_changed')
        return
    with path.open('x') as output:
        json.dump(document, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write('\n')


def save(path, document):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def ref(record):
    return dict(index=record['index'], sha256=record['sha256'])


class BindingError(RuntimeError):
    pass


def remote(arm, request, native=None):
    command = 'PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= ' + \
        '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote((HERE / 'remote_io.py').read_text())
    child = subprocess.run(['bash', str(REPO / 'gpu/ovx4_ssh.sh'), command],
                           input=json.dumps(dict(request, arm=arm, native=native)), text=True,
                           capture_output=True, timeout=100)
    if child.returncode:
        if child.returncode == 2 and child.stdout.startswith('{'):
            raise BindingError(read_error(child.stdout))
        raise RuntimeError('ovx4_parent_transport_exit_' + str(child.returncode))
    return json.loads(child.stdout)


def read_error(output):
    result = json.loads(output)
    return result.get('fatal', 'remote_error') + ':' + result.get('reason', '')


def seed(arm):
    directory = ORIGINAL / ('private/parent' if arm == 'learner' else 'r232_pair/private/frozen_parent')
    complete = sorted(path.parent for path in directory.glob('cycle_*/METRICS.json')
                      if (path.parent / 'STAGE_RECEIPT.json').exists())
    latest = complete[-1]
    payload = read(latest / 'INPUT.json')
    events = payload['actual_committed_child_ACTs']
    last = events[-1]
    return dict(stage=read(latest / 'STAGE_RECEIPT.json')['stage'], events=events,
                assessments=[read(path / 'METRICS.json') for path in complete],
                messages=[read(path)['response']['message'] for path in sorted(directory.glob('*/RESULT.json'))],
                next_index=last['stage_record']['index'] + 1,
                previous_sha256=last['stage_record']['sha256'],
                last_parent_cycle=last['cycle'], first_turn=True, deliveries=[],
                request=None, response=None, committed=None, act_stage=None,
                pending_turn=None, old_ledger=str(directory),
                old_latest=read(directory / 'LATEST.json'),
                seed_sources={str(path): sha(path) for path in
                              (latest / 'INPUT.json', latest / 'METRICS.json', latest / 'STAGE_RECEIPT.json')})


def rendered(document, delivery):
    publication = delivery['receipt']['publication']
    text = 'Astra: ' + delivery['text']
    exact = any(message.get('role') == 'user' and text in message.get('content', '')
                for message in document.get('messages', []))
    bound = any(item.get('source_sha256') == publication['sha256'] and
                item.get('event_id') == 'parent:inbox:' + publication['id']
                for item in document.get('parent_provenance', []))
    return exact and bound


def consume(state, records, directory):
    for record in records:
        kind, document = record['kind'], record.get('document', {})
        if kind == 'INBOX':
            for delivery in state['deliveries']:
                publication = delivery['receipt']['publication']
                if document['message']['id'] == publication['id']:
                    require(document['source_sha256'] == publication['sha256'] and
                            document['message']['text'] == delivery['text'], 'exact_inbox_binding')
                    delivery['inbox'] = ref(record)
        elif kind == 'REQUEST':
            state['request'], state['response'], state['committed'], state['act_stage'] = record, None, None, None
            for delivery in state['deliveries']:
                if delivery.get('inbox') and rendered(document, delivery):
                    delivery.setdefault('render', dict(ref(record), started_unix=document['started_unix']))
        elif kind == 'RESPONSE':
            state['response'], state['committed'] = record, None
        elif kind == 'COMMITTED':
            state['committed'] = record
        elif kind == 'R184_STAGE' and document.get('stage') == 'ACT':
            request, response, committed = (state[key] for key in ('request', 'response', 'committed'))
            require(all((request, response, committed)), 'complete_ACT_sources_required')
            require(response['document']['request_sha256'] == request['document']['pending_sha256'],
                    'ACT_response_request_binding')
            require(committed['document']['source_sha256'] == document['source_sha256'] and
                    committed['document']['segment'] == document['segment'] == request['document']['segment'],
                    'ACT_commit_stage_binding')
            state['act_stage'] = record
            state['events'].append(dict(cycle=state['events'][-1]['cycle'] + 1, response=response,
                                        request_index=request['index'], stage_record=ref(record)))
        elif kind == 'R184_ACT' and state['act_stage']:
            request, response, committed, stage = (state[key] for key in
                                                   ('request', 'response', 'committed', 'act_stage'))
            require(document['origin']['record_index'] == response['index'] and
                    document['origin']['record_sha256'] == response['sha256'] and
                    document['source_sha256'] == stage['document']['source_sha256'], 'ACT_origin_binding')
            for delivery in state['deliveries']:
                if delivery.get('render') and not delivery.get('act') and rendered(request['document'], delivery):
                    delivery['act'] = dict(request=ref(request), response=ref(response), committed=ref(committed),
                                           stage=ref(stage), event=ref(record),
                                           started_unix=request['document']['started_unix'],
                                           finished_unix=response['document']['finished_unix'])
                    proof = dict(publication=delivery['receipt']['publication'], inbox=delivery['inbox'],
                                 first_render=delivery['render'], act=delivery['act'], native=state['native'],
                                 provider_response_sha256=delivery['receipt']['provider_response_sha256'],
                                 parent_process=delivery['parent_process'], exact_text_and_source_bound=True,
                                 causal_improvement_claim=False, sealed_scores_visible=False,
                                 native_signals=0, semantic_row_exclusions=False)
                    write(directory / ('DELIVERY_' + delivery['receipt']['publication']['id'] + '.json'), proof)


def source_parent(arm, state, deadline, directory):
    sys.path.insert(0, str(ORIGINAL))
    spec = importlib.util.spec_from_file_location('reused_pair_parent', ORIGINAL / 'r232_pair/PARENT_SOURCE.py')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.OWN, parent.REPO, parent.END, parent.PRIVATE = ORIGINAL, REPO, deadline, directory
    original_instruction = parent.instruction

    def instruction():
        text = original_instruction().replace((ORIGINAL / 'BIRTH_SPEC_SOURCE.md').read_text(),
                                              (ORIGINAL / 'r232_pair/BIRTH_SPEC_R232.md').read_text())
        text += ('\nR232 is an explicit later environment epoch, not a retroactive birth change. '
                 'Teach exploration inside THINK from this child\'s actual results. Same help opportunity '
                 'and90-word budget; do not copy a correction from the other child. No extra stage. '
                 'This is a parent-publisher repair, NOT a birth or child restart. All historical ACTs '
                 'remain evidence, including malformed ones. Assess the latest actual ACT, not stale feedback. '
                 'Use concrete corrective feedback and one actionable task within the same current object. '
                 'Never infer improvement, stages, or memory from publisher restoration.')
        if state['first_turn']:
            text += (' Your FIRST new message MUST begin exactly: ' + GAP_PREFIX +
                     ' Then give concrete feedback on this child\'s most recent ACT and a specific task. '
                     'Do not claim the child paused, forgot, restarted, or changed its learning policy.')
        return text

    parent.instruction, parent.write = instruction, write
    parent.remote = lambda request: remote(arm, request, state['native'])
    return parent


def assess(state, result, parent):
    event = state['events'][-1]
    text = parent.actual_response(event['response'])
    metrics = deepcopy(result['metrics'])
    excerpt = metrics.get('evidence_excerpt', '')
    metrics.update(evidence_verified=bool(excerpt) and excerpt in text, cycle=event['cycle'],
                   source_response_sha256=event['response']['sha256'])
    if state['assessments'] and state['assessments'][-1]['cycle'] != event['cycle'] - 1:
        metrics['unobserved_assessment_gap'] = True
    assessments = state['assessments'] + [metrics]
    consecutive = []
    for item in reversed(assessments):
        if consecutive and item['cycle'] != consecutive[-1]['cycle'] - 1:
            break
        consecutive.append(item)
    consecutive.reverse()
    evidence = metrics.get('transition_evidence', [])
    valid = bool(evidence) and all(isinstance(item, str) and item and any(
        item in entry['response']['document']['response']['raw'] for entry in state['events']) for item in evidence)
    eligible = parent.stage0_metrics(consecutive)['advance_eligible'] if state['stage'] == 0 else valid
    proposed, previous = metrics['proposed_stage'], state['stage']
    stage = proposed if proposed < previous or proposed == previous + 1 and eligible and valid else previous
    return metrics, dict(previous_stage=previous, stage=stage, proposed_stage=proposed,
                         stage0_metrics=parent.stage0_metrics(consecutive), evidence_verified=valid,
                         learning_recipe_changed=False, assessment_type='attributed_parent_judgment',
                         response_sha256=event['response']['sha256'])


def turn_due(state):
    if state['first_turn']:
        return True
    stage = state['stage']
    text = state['events'][-1]['response']['document']['response']['raw']
    spacing = 1 if stage <= 2 else 2 if stage == 3 else 3
    return (stage != 5 or '?' in text) and state['events'][-1]['cycle'] - state['last_parent_cycle'] >= spacing


def provider_failure(error, previous_429s):
    explicit_429 = isinstance(error, urllib.error.HTTPError) and error.code == 429
    attempts = previous_429s + 1 if explicit_429 else previous_429s
    return dict(explicit_429=explicit_429, rejected_429_attempts=attempts,
                retry_permitted=explicit_429 and attempts < 5,
                outcome='EXPLICIT_429_REJECTION' if explicit_429 else 'AMBIGUOUS_OR_UNVALIDATED_NO_REDISPATCH',
                retry_seconds=2 ** (attempts - 1) if explicit_429 and attempts < 5 else None)


def unresolved_provider_attempts(directory):
    unresolved = []
    for turn in sorted(directory.glob('turn_*')):
        if (turn / 'PUBLICATION.json').exists() or not (turn / 'DISPATCH.json').exists():
            continue
        error = turn / 'http_error_response.txt'
        try:
            explicitly_rejected = str(read(error).get('error', {}).get('code')) == '429'
        except (FileNotFoundError, ValueError):
            explicitly_rejected = False
        if not explicitly_rejected:
            unresolved.append(str(turn))
    return unresolved


def run(arm):
    os.umask(0o077)
    directory = HERE / 'private' / arm
    directory.mkdir(parents=True, exist_ok=True)
    lock = (directory / 'PUBLISHER.lock').open('a+')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'existing_provider_credential_required')
    allocation = read(RECOVERY / 'ALLOCATION_DATE_CORRECTION.json')
    deadline = allocation['hard_end_unix']
    require(deadline == allocation['lease_end_unix'] - 21600 and time.time() < deadline,
            'unchanged_existing_allocation_bound')
    binding = remote(arm, dict(action='bind'))
    process = dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
                   boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                   started_utc=datetime.now(timezone.utc).isoformat(), argv=[sys.executable, '-B', __file__, '--arm', arm],
                   cwd=str(REPO), lock=str(directory / 'PUBLISHER.lock'), native=binding['native'],
                   env_nonsecret=dict(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', PYTHONUNBUFFERED='1'),
                   secret_env_names=['NVIDIA_API_KEY'], deadline_unix=deadline,
                   provider_model='openai/openai/gpt-6-astra', provider_tools=[], native_signals=0,
                   sources={str(path): sha(path) for path in (HERE / 'parent_service.py', HERE / 'remote_io.py',
                       ORIGINAL / 'r232_pair/PARENT_SOURCE.py', REPO / 'gpu/orch_route_parent_campaign_providers.py',
                       RECOVERY / 'ALLOCATION_DATE_CORRECTION.json')})
    write(directory / ('PROCESS_' + str(process['pid']) + '_' + process['start_ticks'] + '.json'), process)
    state_path = directory / 'STATE.json'
    state = read(state_path) if state_path.exists() else seed(arm)
    if 'native' in state:
        require(state['native'] == binding['native'], 'restart_native_binding_changed')
    state['native'] = binding['native']
    state.setdefault('provider_inflight', None)
    state.setdefault('provider_blocked', None)
    state.setdefault('provider_429_attempts', 0)
    state.setdefault('publication_blocked', None)
    state.setdefault('transport_blocked', None)
    unresolved = [turn for turn in unresolved_provider_attempts(directory) if turn != state['pending_turn']]
    if unresolved or state['provider_inflight']:
        state['provider_blocked'] = dict(reason='preserved_provider_attempt_requires_operator_resolution',
                                         attempts=unresolved, inflight=state['provider_inflight'])
    parent = source_parent(arm, state, deadline, directory)
    save(state_path, state)
    failures = 0
    while time.time() < deadline:
        phase = 'read_only_poll'
        try:
            if state['transport_blocked']:
                return
            if state['pending_turn'] is None or state['publication_blocked']:
                observed = remote(arm, dict(action='poll', next_index=state['next_index'],
                                             previous_sha256=state['previous_sha256']), state['native'])
                candidate = deepcopy(state)
                consume(candidate, observed['records'], directory)
                candidate.update(next_index=observed['next_index'], previous_sha256=observed['previous_sha256'])
                state.clear()
                state.update(candidate)
                save(state_path, state)
                save(directory / 'STATUS.json', dict(observed_unix=time.time(), parent_process=process,
                     next_index=state['next_index'], cycle=state['events'][-1]['cycle'], stage=state['stage'],
                     new_publications=len(state['deliveries']), act_receipts=sum(bool(item.get('act')) for item in state['deliveries']),
                     failures=failures, caught_up=observed['caught_up'], provider_blocked=state['provider_blocked'],
                     publication_blocked=state['publication_blocked'], transport_blocked=state['transport_blocked'],
                     health='BLOCKED_PROVIDER' if state['provider_blocked'] else
                            'BLOCKED_PUBLICATION' if state['publication_blocked'] else 'OBSERVING'))
                failures = 0
                if not observed['caught_up']:
                    continue
                if state['provider_blocked'] or state['publication_blocked'] or not turn_due(state):
                    time.sleep(3)
                    continue
                turn = directory / ('turn_' + str(state['events'][-1]['cycle']).zfill(6) + '_' + str(time.time_ns()))
                payload = dict(stage=state['stage'], cycle=state['events'][-1]['cycle'],
                               actual_committed_child_ACTs=state['events'], prior_parent_assessments=state['assessments'],
                               actual_previous_parent_messages=state['messages'],
                               scope='own actual child ACT and parent turns only; sealed/readout data unavailable',
                               recovery=dict(first_new_turn=state['first_turn'], vm_reboot_utc='2026-09-18T22:50:45Z',
                                             last_prior_publisher_observation=state['old_latest'], native_never_restarted=True,
                                             backlog_retained_without_replaying_stale_parent_messages=True))
                state['provider_inflight'] = str(turn)
                save(state_path, state)
                phase = 'provider'
                result = parent.generate(turn, payload)
                if state['first_turn']:
                    require(result['response']['message'].startswith(GAP_PREFIX), 'first_turn_must_acknowledge_gap')
                metrics, stage_receipt = assess(state, result, parent)
                write(turn / 'METRICS.json', metrics)
                write(turn / 'STAGE_RECEIPT.json', stage_receipt)
                state['pending_turn'] = str(turn)
                state['provider_inflight'] = None
                save(state_path, state)
            turn = Path(state['pending_turn'])
            result = read(turn / 'RESULT.json')
            phase = 'publication'
            publication = parent.publish(turn, result, state['native']['journal_id'])
            state['deliveries'].append(dict(receipt=publication, text=result['response']['message'],
                                             directory=str(turn), parent_process=process))
            state['assessments'].append(read(turn / 'METRICS.json'))
            state['stage'] = read(turn / 'STAGE_RECEIPT.json')['stage']
            state['messages'].append(result['response']['message'])
            state['last_parent_cycle'] = read(turn / 'INPUT.json')['cycle']
            state['pending_turn'], state['first_turn'] = None, False
            state['provider_429_attempts'] = 0
            save(state_path, state)
            print(json.dumps(dict(published=publication['publication']['id'], arm=arm, parent_pid=os.getpid())), flush=True)
            failures = 0
        except BindingError as error:
            save(directory / 'STATUS.json', dict(observed_unix=time.time(), parent_process=process,
                 health='FATAL_BINDING_REJECTION', error_type=type(error).__name__, reason=str(error),
                 provider_blocked=state['provider_blocked'], native_signals=0))
            raise
        except Exception as error:
            failures += 1
            retry_seconds = min(8, 2 ** (failures - 1))
            if phase == 'provider':
                decision = provider_failure(error, state['provider_429_attempts'])
                state['provider_429_attempts'] = decision['rejected_429_attempts']
                attempt = Path(state['provider_inflight'])
                if attempt.exists():
                    write(attempt / 'FAILURE_DISPOSITION.json', decision)
                if decision['retry_permitted']:
                    state['provider_inflight'] = None
                else:
                    state['provider_blocked'] = dict(decision, attempt=str(attempt))
                state['provider_inflight'] = None
                retry_seconds = decision['retry_seconds'] if decision['retry_permitted'] else 3
                save(state_path, state)
            elif phase == 'publication':
                state['publication_blocked'] = dict(reason='publication_transport_outcome_requires_read_only_reconciliation',
                                                    pending_turn=state['pending_turn'], error_type=type(error).__name__)
                save(state_path, state)
            elif failures >= 5:
                state['transport_blocked'] = dict(reason='five_consecutive_read_only_poll_failures',
                                                  error_type=type(error).__name__, failures=failures)
                save(state_path, state)
            write(directory / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
                  observed_unix=time.time(), pending_turn=state['pending_turn'], failures=failures,
                  phase=phase, retry_seconds=retry_seconds, native_signals=0, provider_blocked=state['provider_blocked'],
                  publication_blocked=state['publication_blocked'], transport_blocked=state['transport_blocked']))
            save(directory / 'STATUS.json', dict(observed_unix=time.time(), parent_process=process,
                 health='BLOCKED_TRANSPORT' if state['transport_blocked'] else
                        'BLOCKED_PROVIDER' if state['provider_blocked'] else
                        'BLOCKED_PUBLICATION' if state['publication_blocked'] else 'BOUNDED_RETRY',
                 error_type=type(error).__name__, phase=phase, failures=failures, retry_seconds=retry_seconds,
                 provider_blocked=state['provider_blocked'], publication_blocked=state['publication_blocked'],
                 transport_blocked=state['transport_blocked'], native_signals=0))
            print(json.dumps(dict(error_type=type(error).__name__, arm=arm,
                                 retry=not any(state[key] for key in
                                               ('provider_blocked', 'publication_blocked', 'transport_blocked')))), flush=True)
            if state['transport_blocked']:
                return
            time.sleep(retry_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=('learner', 'frozen'), required=True)
    run(parser.parse_args().arm)
