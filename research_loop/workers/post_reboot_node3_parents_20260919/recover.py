"""Non-material repair: resume five caption providers through surviving publishers."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from node_bridge import CAPTIONS


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRIOR = REPO / 'research_loop/workers/rohin233_focus_node3_20260918'
sys.path[:0] = [str(REPO), str(PRIOR)]
from adaptive_parent import message
from model_parent import INSTRUCTION
from retirement import identity, save, sha
from service_horizon import CEILING


GAP = ('My operator-side parent provider was offline after the VM reboot at '
    '22:50:45 UTC on 2026-09-18; your native process kept running.')
TASK = ('This is restoration of the existing R233 caption parent, not a new curriculum. '
    'The newest current_observation supersedes stale observations in the queued request. '
    'Make this turn about exactly one concrete caption for the current actual scene and the '
    'most recent actually visible judge feedback. If no usable judgment exists, name that '
    'specific failure and request one caption submission, not a plan or a claim of scoring. '
    'Ask the child to author the caption itself; do not supply its training answer. '
    'Do not spend this turn on reading, study methodology, memory policies, or meta discussion. '
    'Do not invent a scene, judge execution, feedback, scores, or successful uptake. '
    'Only child-visible TRAIN/Tool excerpts are supplied; never access or request sealed '
    'evaluation scores, keys, panels, or references. No row filtering or native controls. ')


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)


def remote(value):
    code = (HERE / 'node_bridge.py').read_text()
    command = 'python3 -B -c ' + shlex.quote(code)
    process = subprocess.run(['bash', str(REPO / 'gpu/ovx2_ssh.sh'), command],
        input=json.dumps(value), text=True, capture_output=True, timeout=90, check=True)
    return json.loads(process.stdout)


def instruction(first):
    return INSTRUCTION + ' ' + TASK + (
        'Begin the message with this exact operator acknowledgment, then the concrete task: ' + GAP
        if first else 'The operator gap was already acknowledged; do not repeat it.')


def attempt_directory(directory, now):
    attempts = [directory, *sorted(directory.glob('retry_[0-9][0-9][0-9][0-9]'))]
    latest = attempts[-1]
    if not (latest / 'DISPATCH.json').exists():
        return latest, None
    rejection = latest / 'http_error_response.txt'
    failure = latest / 'FAILED.json'
    if rejection.exists() and failure.exists() and not (latest / 'stdout.json').exists():
        error = json.loads(rejection.read_bytes()).get('error', {})
        if (str(error.get('code')) == '429'
                and json.loads(failure.read_bytes()).get('error_type') == 'HTTPError'):
            if now - failure.stat().st_mtime < min(60, 15 * len(attempts)):
                return None, 'CONFIRMED_429_BACKOFF'
            following = directory / f'retry_{len(attempts):04d}'
            following.mkdir(exist_ok=True)
            return following, None
    return None, 'UNCERTAIN_OR_FAILED_PROVIDER_ATTEMPT_NO_RETRY'


def generate(job, baseline, first):
    from gpu.orch_route_parent_campaign_providers import strong
    life = job['request']['life']
    if life not in CAPTIONS:
        raise ValueError('five_caption_forks_only')
    directory = HERE / 'private/requests' / job['request_sha256']
    directory.mkdir(parents=True, exist_ok=True)
    result_path = directory / 'RESULT.json'
    if not result_path.exists():
        attempt, blocked = attempt_directory(directory, time.time())
        if blocked:
            return dict(life=life, status=blocked, request_sha256=job['request_sha256'])
        prompt = dict(queued_request=job['request'], current_observation=job['current_observation'],
            operator_gap=dict(reboot_utc='2026-09-18T22:50:45Z', first_restored_turn=first))
        if not (attempt / 'SOURCE_REQUEST_PRIVATE.json').exists():
            save(attempt / 'SOURCE_REQUEST_PRIVATE.json', job)
        try:
            response, model, usage = strong(json.dumps(prompt), attempt,
                min(CEILING, baseline['bindings'][life]['deadline']),
                instruction=instruction(first), reasoning_effort='xhigh')
            result = dict(request_sha256=job['request_sha256'], response=response, model=model,
                usage=usage, provider_response_sha256=sha(attempt / 'stdout.json'),
                provider_dispatch_sha256=sha(attempt / 'DISPATCH.json'), completed_unix=time.time())
            text = message(result, job['request_sha256'])
            if first and not text.startswith(GAP):
                raise ValueError('first_turn_requires_operator_gap_acknowledgment')
            if 'caption' not in text.lower():
                raise ValueError('concrete_caption_task_required')
            save(result_path, result)
        except Exception as error:
            atomic(attempt / 'FAILED.json', dict(error_type=type(error).__name__, utc=utc(),
                http_status=getattr(error, 'code', None),
                retry_only_definitive_429=True, uncertain_attempt_retry=False, published=False))
            return dict(life=life, status='PROVIDER_FAILED_NOT_PUBLISHED', error_type=type(error).__name__)
    result = json.loads(result_path.read_bytes())
    response = remote(dict(mode='accept', bindings=baseline['bindings'], publishers=baseline['publishers'],
        life=life, relative=job['relative'], result=result))
    atomic(directory / 'MAILBOX_ACCEPTED.json', response)
    return dict(life=life, status='PROVIDER_ACCEPTED_NOT_UPTAKE', relative=job['relative'],
        request_sha256=job['request_sha256'])


def run():
    os.umask(0o077)
    if not os.environ.get('NVIDIA_API_KEY'):
        raise ValueError('existing_provider_key_must_be_supplied_in_environment')
    (HERE / 'private/requests').mkdir(parents=True, exist_ok=True)
    (HERE / 'locks').mkdir(exist_ok=True)
    locks = []
    for name in ('SUPERVISOR', *CAPTIONS):
        lock = (HERE / 'locks' / (name + '.lock')).open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    snapshot = remote(dict(mode='snapshot'))
    baseline_path = HERE / 'BINDINGS.json'
    baseline = {key: snapshot[key] for key in ('bindings', 'publishers', 'helper_sha256')}
    if baseline_path.exists():
        if json.loads(baseline_path.read_bytes()) != baseline:
            raise ValueError('saved_incarnation_changed_no_automatic_rebind')
    else:
        save(baseline_path, baseline)
    started = dict(utc=utc(), process=identity(os.getpid()),
        vm_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        sources={str(path.relative_to(REPO)): sha(path) for path in
            (Path(__file__), HERE / 'node_bridge.py', PRIOR / 'model_parent.py',
             PRIOR / 'adaptive_parent.py', REPO / 'gpu/orch_route_parent_campaign_providers.py')},
        native_signals=0, native_restarts=0, math_parent_changes=0, learning_row_filter_changes=0,
        credentials_persisted_or_sent_to_node=False, service_end_unix=CEILING)
    save(HERE / 'private' / ('STARTED_' + str(os.getpid()) + '_' + str(time.time_ns()) + '.json'), started)
    atomic(HERE / 'STARTED.json', started)
    first_path = HERE / 'FIRST_TURNS.json'
    first_turns = json.loads(first_path.read_bytes()) if first_path.exists() else {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        while time.time() < CEILING:
            try:
                snapshot = remote(dict(mode='snapshot', bindings=baseline['bindings'], publishers=baseline['publishers']))
                if snapshot['helper_sha256'] != baseline['helper_sha256']:
                    raise ValueError('pinned_node_helpers_changed')
                pending = []
                for job in snapshot['jobs']:
                    life = job['request']['life']
                    if life not in first_turns:
                        first_turns[life] = job['relative']
                        atomic(first_path, first_turns)
                    pending.append(executor.submit(generate, job, baseline,
                        job['relative'] == first_turns[life]))
                outcomes = [future.result() for future in pending]
                receipts = remote(dict(mode='receipts', bindings=baseline['bindings'],
                    publishers=baseline['publishers'], first_turns=first_turns))
                atomic(HERE / 'FIRST_RECEIPTS.json', receipts)
                atomic(HERE / 'STATUS.json', dict(utc=utc(), process=started['process']['pid'],
                    state='CADENCE_RUNNING', outcomes=outcomes,
                    verified_first_ACT_chains=sum(row['state'] == 'ACT_CHAIN_VERIFIED'
                        for row in receipts['receipts']), expected_forks=5,
                    task_uptake_established=False, math_parent_changes=0,
                    native_signals=0, learning_row_filter_changes=0))
                print(json.dumps(dict(utc=utc(), outcomes=outcomes)), flush=True)
            except (subprocess.SubprocessError, OSError) as error:
                atomic(HERE / 'STATUS.json', dict(utc=utc(), state='TRANSPORT_ERROR_NO_NATIVE_ACTION',
                    error_type=type(error).__name__))
            time.sleep(10)


if __name__ == '__main__':
    run()
