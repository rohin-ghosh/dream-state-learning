"""Bounded single-HTTP-attempt teacher collection, isolated from all trainers."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import tomllib
import urllib.error
import urllib.request

from gpu.orch_l2_shared_run import write
from gpu.orch_route_parent_campaign_providers import NoRedirect
from organism_v6 import orch_route_parent_campaign_teacher_exemplar as policy


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def prepare(root):
    policy.route.require(not (root / 'ROSTER.json').exists(), 'prospective_freeze_only')
    math = Path('research_notes/analysis/orch_math_pipeline_l2_20260915_attempt1')
    route = Path('research_notes/analysis/orch_route_parent_campaign_20260915_monitor_v2/matched_complete')
    provider = Path('research_notes/analysis/orch_route_parent_campaign_20260915_monitor_v2/provider_strong')
    provenance = read(math / 'DATA_PROVENANCE.json')
    policy.route.require(provenance['prospective'] and not provenance['outcomes_read']
        and provenance['cohort_sha256'] == sha(math / 'COHORT.json'), 'existing_math_roster_provenance')
    qualification = read(provider / 'RECEIPT.json')
    policy.route.require(qualification['verified'] and qualification['actual_primary_model'] == policy.MODEL
        and qualification['envelope_sha256'] == sha(provider / 'stdout.json'), 'actual_provider_qualification')
    tasks, checks, exclusion = policy.freeze_tasks(read(math / 'COHORT.json'), read(route / 'COHORT.json'), read(route / 'SOURCE.json'))
    for ordinal, prompt in enumerate(tasks):
        folder = root / 'prompts' / f'{ordinal:02d}'
        folder.mkdir(parents=True)
        write(folder / 'USER.json', prompt)
        (folder / 'SYSTEM.txt').write_text(policy.SYSTEM)
    write(root / 'PRIVATE_CHECKS.json', checks)
    roster = dict(source_label=policy.LABEL, split='TRAIN', tasks=tasks, exclusion=exclusion,
        prompt_is_training_target=False, trainer_ingestion=False, mainline_teacher_bytes=False,
        intended_target=None, provider=policy.MODEL, task_count=len(tasks),
        source_files={str(path): sha(path) for path in (math / 'COHORT.json', math / 'DATA_PROVENANCE.json',
            route / 'COHORT.json', route / 'SOURCE.json', provider / 'RECEIPT.json', provider / 'stdout.json')},
        frozen_utc=datetime.now(timezone.utc).isoformat())
    write(root / 'ROSTER.json', roster)
    write(root / 'QUARANTINE.json', dict(source_label=policy.LABEL, root=str(root.resolve()),
        forbidden_sinks=['ONGOING_L1', 'SELF_GENERATED_L1', 'CURRENT_PARENT_LIVES', 'MAINLINE_TRAINERS'],
        future_fit_protocol='MAIN_ONLY_NOT_YET_DECLARED', contains_teacher_prompts=True,
        prompt_is_training_target=False, approved_for_ingestion=False, zero_gpu_allocation=True))


def timeout_handler(signum, frame):
    raise TimeoutError('teacher_single_attempt_wall_timeout')


def request_once(prompt, root, folder, deadline, config):
    provider = config['model_providers'][config['model_provider']]
    policy.route.require(config['model'] == policy.MODEL and provider['wire_api'] == 'responses'
        and provider['base_url'] == 'https://[REDACTED_HOST]/v1'
        and provider['env_key'] == 'NVIDIA_API_KEY', 'unchanged_verified_provider_configuration')
    key = os.environ[provider['env_key']]
    payload = dict(model=config['model'], input=json.dumps(policy.validate_prompt(prompt), sort_keys=True),
        instructions=policy.SYSTEM, tools=[], tool_choice='none', store=False, max_output_tokens=8192,
        reasoning=dict(effort=config['model_reasoning_effort']))
    write(folder / 'REQUEST.json', payload)
    write(folder / 'DISPATCH.json', dict(source_label=policy.LABEL, task_id=prompt['task_id'],
        requested_model=policy.MODEL, http_attempts_reserved=1, retries=0, maximum_output_tokens=8192,
        request_sha256=sha(folder / 'REQUEST.json'), started_utc=datetime.now(timezone.utc).isoformat(),
        deadline_unix=min(deadline, time.time() + 120), tools=[], trainer_ingestion=False))
    request = urllib.request.Request(provider['base_url'] + '/responses', data=json.dumps(payload).encode(),
        headers={'Authorization': '[REDACTED_SECRET]' + key, 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    signal.setitimer(signal.ITIMER_REAL, max(0.1, min(120, deadline - time.time())))
    try:
        with opener.open(request, timeout=max(0.1, min(120, deadline - time.time()))) as response:
            raw = response.read().decode()
            write(folder / 'HTTP.json', dict(status=response.status,
                request_id=response.headers.get('x-request-id'), http_attempts=1))
        (folder / 'RAW_RESPONSE.json').write_text(raw.replace(key, '[REDACTED]'))
        return json.loads(raw)
    except urllib.error.HTTPError as error:
        (folder / 'RAW_ERROR_RESPONSE.txt').write_text(error.read().decode(errors='replace').replace(key, '[REDACTED]'))
        write(folder / 'HTTP.json', dict(status=error.code, http_attempts=1))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def run(root):
    budget, roster, publication = (read(root / name) for name in ('BUDGET.json', 'ROSTER.json', 'PUBLICATION.json'))
    policy.route.require(publication['pre_provider_pass'] and publication['roster_sha256'] == sha(root / 'ROSTER.json')
        and publication['budget_sha256'] == sha(root / 'BUDGET.json'), 'pre_provider_publication_gate')
    for name, expected in publication['source_sha256'].items():
        policy.route.require(sha(name) == expected, 'frozen_teacher_source_changed')
    policy.route.require(len(roster['tasks']) == 16 and budget['selected_providers'] == [policy.MODEL]
        and budget['selected_maximum_calls'] == 16 and budget['maximum_output_tokens_per_call'] == 8192,
        'bounded_selected_teacher_allocation')
    deadline = budget['hard_deadline_unix']
    calls = root / 'calls'
    calls.mkdir(exist_ok=False)
    checks = read(root / 'PRIVATE_CHECKS.json')
    config_path = Path.home() / '.codex/nvidia-astra.config.toml'
    config = tomllib.loads(config_path.read_text())
    signal.signal(signal.SIGALRM, timeout_handler)
    write(root / 'START.json', dict(utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
        deadline_unix=deadline, source_label=policy.LABEL, roster_sha256=sha(root / 'ROSTER.json'),
        config_sha256=sha(config_path), provider=policy.MODEL, model_calls_maximum=16, gpu_calls=0))
    records = []
    for ordinal, prompt in enumerate(roster['tasks']):
        if time.time() >= deadline - 2:
            break
        folder = calls / f'{ordinal:02d}'
        folder.mkdir(exist_ok=False)
        result = dict(ordinal=ordinal, task_id=prompt['task_id'], domain=prompt['domain'],
            source_label=policy.LABEL, trainer_ingestion=False, single_attempt=True,
            eligible_for_future_curation=False)
        try:
            envelope = request_once(prompt, root, folder, deadline, config)
            result.update(actual_model=envelope.get('model'), usage=envelope.get('usage'),
                provider_status=envelope.get('status'), envelope_sha256=sha(folder / 'RAW_RESPONSE.json'))
            exemplar = policy.parse_response(envelope)
            write(folder / 'TEACHER_EXEMPLAR.json', exemplar)
            check = policy.check_answer(exemplar, checks[prompt['task_id']])
            write(folder / 'ANSWER_CHECK.json', check)
            result.update(status='COMPLETE', answer_check=check, eligible_for_future_curation=check['final_answer_correct'])
        except Exception as error:
            result.update(status='FAILED_PRESERVED_NO_RETRY', error_type=type(error).__name__,
                error=str(error).replace(os.environ.get('NVIDIA_API_KEY', '\x00'), '[REDACTED]'))
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write(folder / 'RECEIPT.json', result)
        records.append(result)
        write(root / 'STATUS.json', dict(source_label=policy.LABEL, attempted=len(records), intended=16,
            complete=sum(row['status'] == 'COMPLETE' for row in records),
            answer_check_correct=sum(row.get('answer_check', {}).get('final_answer_correct', False) for row in records),
            maximum_attempts=16, deadline_unix=deadline, updated_utc=result['finished_utc'],
            trainer_ingestion=False, records=records))
        with Path('research_loop/workers/ROUTE_PARENT_CAMPAIGN.md').open('a') as journal:
            journal.write('\n' + result['finished_utc'] + ' — TEACHER_DISTILLATION task' + str(ordinal) +
                ' ' + result['status'] + ',actual_model=' + str(result.get('actual_model')) +
                ',source=' + str(folder) + ',singleattempt; raw prompt/response/error preserved; '
                'zero trainer/mainline ingestion; method proofs not independently verified.\n')
    write(root / 'TERMINAL.json', dict(source_label=policy.LABEL, attempted=len(records), intended=16,
        status='COMPLETE_COLLECTION' if len(records) == 16 else 'HARD_DEADLINE_PARTIAL',
        complete=sum(row['status'] == 'COMPLETE' for row in records),
        finished_utc=datetime.now(timezone.utc).isoformat(), trainer_ingestion=False, gpu_calls=0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run'))
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    root = Path(args.root)
    (prepare if args.phase == 'prepare' else run)(root)


if __name__ == '__main__':
    main()
