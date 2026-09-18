"""One original-xhigh-ledger turn, explicitly queued before retry LOAD."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import p3_lease_parent
import p3_retry_observe as observer
import p3_retry_publication_resolution as resolution


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MODE = 'PRELOAD_PARENT_QUEUE'
CONTEXT = (
    '\nRohin explicitly requests ONE Astra parent turn queued now for the recovering learner. '
    'This is PRELOAD_PARENT_QUEUE, not a live-inference turn: retry1 has no LOAD yet. '
    'The shown child quotes are authenticated preserved historical outputs, including a failed '
    'attempt tail; they are not new outputs during downtime and do not establish retained learning. '
    'The working-state recovery is COMPLETE5243/sleep153 in the original journal. '
    'Briefly acknowledge the recovery interruption and ground one responsive contribution in '
    'the latest shown actual child output. Retain the same role, policy, object history and '
    'caption activity. No fabricated child feedback, Tool judgment or claim of rendering now. '
    'The turn will await native inbox ingestion after LOAD. Use the existing required parent '
    'response/rationale validation, and no invented source record or Rohin speech.'
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-read', action='store_true')
    parser.add_argument('--resume-source', action='store_true')
    options = parser.parse_args()
    observer.require(bool(os.environ.get('NVIDIA_API_KEY')), 'inherited_provider_environment_required')
    observer.require(not (options.resume_read and options.resume_source), 'one_explicit_resume_mode')
    prefix = ('P3_RETRY_PRELOAD_GENERATE' if options.resume_source else
        'P3_RETRY_PRELOAD_READ2' if options.resume_read else 'P3_RETRY_PRELOAD')
    if options.resume_source:
        observer.require((HERE / 'P3_RETRY_PRELOAD_READ2_FINISHED.json').is_file()
            and (HERE / 'P3_RETRY_PRELOAD_SOURCE.json').is_file()
            and resolution.RECEIPT.is_file()
            and not (HERE / 'P3_RETRY_PRELOAD_RESULT.json').exists(),
            'resume_only_authenticated_source_after_ledger_reconciliation')
    if options.resume_read:
        observer.require((HERE / 'P3_RETRY_PRELOAD_FINISHED.json').is_file()
            and not (HERE / 'P3_RETRY_PRELOAD_SOURCE.json').exists()
            and not (HERE / 'P3_RETRY_PRELOAD_RESULT.json').exists(),
            'resume_only_failed_read_before_any_provider_attempt')
    observer.require(not (HERE / (prefix + '_STARTED.json')).exists(), 'one_preload_attempt_only')
    module, policy, original, unused = p3_lease_parent.load_on_renewed_wall()
    config = p3_lease_parent.bind(policy, original)
    policy.validate(config)
    output = module.base.OWN / 'r210_parent3'
    resolution.bind(policy, output / 'turns')
    with (output / 'PARENT_OPERATOR.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deadline = min(observer.END_UNIX, time.time() + 600)
        observer.immutable(HERE / (prefix + '_STARTED.json'), dict(mode=MODE, pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()[19],
            started_unix=time.time(), deadline_unix=deadline,
            source_sha256=observer.digest(Path(__file__)), publications_limit=1, native_signals=[]))
        try:
            authority = None

            def remote(request):
                command = '/localhome/local-rohing/v2/venv/bin/python -B ' + str(observer.CPU / 'p3_retry_preload_endpoint.py')
                response = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command],
                    input=json.dumps(dict(request, mode=MODE, physical=3, deadline_unix=deadline)), capture_output=True,
                    text=True, check=True, timeout=120)
                return json.loads(response.stdout)

            reference = (observer.read(HERE / 'P3_RETRY_PRELOAD_POLL.private.json')['reference']
                if options.resume_source else None)
            for poll in range(64):
                observer.require(time.time() < deadline, 'bounded_preload_snapshot_deadline')
                observed = remote(dict(op='poll', reference=reference))
                reference = observed['reference']
                authority = observed['preload_authority']
                state = observed['snapshot']
                temporary = HERE / 'P3_RETRY_PRELOAD_POLL.private.next'
                temporary.write_text(json.dumps(dict(reference=reference, authority=authority,
                    caught_up=state['caught_up'], request_count=state['request_count'],
                    response_count=state['response_count'], head_sha256=state['head_sha256'], poll=poll + 1)) + '\n')
                temporary.replace(HERE / 'P3_RETRY_PRELOAD_POLL.private.json')
                if state['caught_up']:
                    break
            observer.require(state['caught_up'], 'bounded_preserved_snapshot_must_be_caught_up')
            child = next(event for event in reversed(state['events']) if event['actor'] == 'child')
            observer.immutable(HERE / 'P3_RETRY_PRELOAD_AUTHORITY.private.json', authority)
            observer.immutable(HERE / 'P3_RETRY_PRELOAD_SOURCE.json', dict(mode=MODE,
                journal_id=state['journal_id'], head_sha256=state['head_sha256'],
                latest_child_record_index=child['record_index'], latest_child_record_sha256=child['record_sha256'],
                latest_child_text_sha256=hashlib.sha256(child['text'].encode()).hexdigest(),
                latest_child_is_preserved_history=True, complete_index=5243, sleep=153,
                native_pid=authority['pid'], native_start_ticks=authority['start_ticks'], loaded=False))
            directory = output / 'turns' / f"parent_{state['request_count']:012d}"
            observer.require(not directory.exists(), 'preserve_existing_original_ledger_attempt')
            original_prompt = policy.prompt
            from parent_repairs import evidence_prompt

            def prompt(*arguments, **keywords):
                instruction, payload = original_prompt(*arguments, **keywords)
                return evidence_prompt(instruction + CONTEXT, payload, arguments[1])

            policy.prompt = prompt
            original_strong = policy.parent.strong

            def strong(payload, directory, hard_end, instruction, **keywords):
                return original_strong(payload, directory, min(hard_end, deadline), instruction, **keywords)

            policy.parent.strong = strong
            module.base.remote = lambda request: remote(dict(request, authority=authority))
            seed = observer.read(output / 'SEED.json')
            status = policy.tick(REPO, config, output / 'turns', seed, state)
            result = observer.read(directory / 'RESULT.json') if directory.is_dir() else None
            receipt = dict(mode=MODE, status=status['status'], attempt=directory.name,
                source_receipt_sha256=observer.digest(HERE / 'P3_RETRY_PRELOAD_SOURCE.json'),
                provider_response=(directory / 'stdout.json').is_file(),
                api_request_sha256=observer.digest(directory / 'API_REQUEST.json') if (directory / 'API_REQUEST.json').is_file() else None,
                result_sha256=observer.digest(directory / 'RESULT.json') if result else None,
                publication=result.get('publication') if result else None,
                queued_not_rendered=bool(result and result.get('status') == 'PUBLISHED'),
                original_ledger=True, original_provider=True, reasoning_effort='xhigh', native_signals=[])
            observer.immutable(HERE / 'P3_RETRY_PRELOAD_RESULT.json', receipt)
            print(json.dumps(receipt, sort_keys=True))
        finally:
            observer.immutable(HERE / (prefix + '_FINISHED.json'), dict(finished_unix=time.time(),
                pid=os.getpid(), native_signals=[]))


if __name__ == '__main__':
    main()
