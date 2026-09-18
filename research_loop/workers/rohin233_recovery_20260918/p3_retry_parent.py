"""Resume the sole original xhigh parent ledger after verified retry1 LOAD."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

import p3_lease_parent
import p3_retry_observe as observer
import p3_retry_publication_resolution as resolution


HERE = Path(__file__).resolve().parent
REMOTE_ENDPOINT = str(observer.CPU / 'p3_retry_endpoint.py')


def bind_recovery_context(policy, binding):
    original_prompt = policy.prompt
    context = (
        '\nVerified operator recovery context: this is the original P3 journal, restored from '
        'COMPLETE5243/sleep153 after a failed native attempt. Retry1 LOAD '
        + str(binding['loaded_index']) + ' is authenticated. During the preceding replay, '
        'no new child inference, parent cadence or Tool judgment was verified. Preserved '
        'earlier child output is historical evidence, not new feedback during downtime. '
        'Continue as the same Astra parent with the same ledger and policy; briefly '
        'acknowledge the interruption when appropriate. Do not invent observations, '
        'judge feedback or learning success during the recovery gap.'
    )

    def prompt(*arguments, **keywords):
        instruction, payload = original_prompt(*arguments, **keywords)
        return instruction + context, payload

    policy.prompt = prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('validate', 'serve'))
    options = parser.parse_args()
    preload = HERE / 'P3_RETRY_PRELOAD_STARTED.json'
    if options.action == 'serve' and preload.is_file() and not (HERE / 'P3_RETRY_PRELOAD_FINISHED.json').is_file():
        started = observer.read(preload)
        while time.time() < started['deadline_unix']:
            process = Path('/proc') / str(started['pid'])
            if not process.exists() or (HERE / 'P3_RETRY_PRELOAD_FINISHED.json').is_file():
                break
            observer.require(process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19] == started['start_ticks'],
                'exact_preload_parent_identity')
            time.sleep(1)
        observer.require((HERE / 'P3_RETRY_PRELOAD_FINISHED.json').is_file(), 'preload_attempt_requires_reconciliation')
    module, policy, original, predecessor = p3_lease_parent.load_on_renewed_wall()
    config = p3_lease_parent.bind(policy, original)
    policy.validate(config)
    binding_path = HERE / 'P3_RETRY_BINDING.json'
    binding = observer.read(binding_path)
    observer.require(binding['source'] == str(observer.SOURCE) and binding['hard_end_unix'] == observer.END_UNIX
        and binding['journal_id'] == observer.JOURNAL_ID and binding['loaded_index'] > 5299,
        'verified_retry_only_binding')
    bind_recovery_context(policy, binding)
    output = module.base.OWN / 'r210_parent3'
    resolution_sha = resolution.bind(policy, output / 'turns')
    if options.action == 'serve' and preload.is_file():
        with (output / 'PARENT_OPERATOR.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            fcntl.flock(lock, fcntl.LOCK_UN)
    observer.require((output / 'SEED.json').is_file() and (output / 'turns').is_dir(), 'original_parent_ledger_required')
    manifest = dict(policy='R233_P3_RETRY1_ORIGINAL_PARENT_LEDGER_V1', hard_end_unix=observer.END_UNIX,
        requested_scope='CPU_PARENT_OBSERVER_RETRY1_NO_NATIVE_CONTROL',
        intake_sha256=observer.digest(HERE / 'P3_RETRY_INTAKE.md'), predecessor_manifest=predecessor,
        binding=binding, binding_sha256=observer.digest(binding_path), original_seed_sha256=observer.digest(output / 'SEED.json'),
        source_pins={name: observer.digest(HERE / name) for name in ('p3_retry_parent.py','p3_retry_endpoint.py',
            'p3_retry_observe.py','p3_retry_publication_resolution.py','p3_lease_parent.py',
            'p3_recovery.py','p3_incremental.py','p3_endpoint.py')},
        preserved_ledger=True, existing_single_parent_lock=True, reasoning_effort='xhigh', cadence_responses=1,
        historical_publication_resolution_sha256=resolution_sha,
        learner_signals=[], new_seed_or_opener=False, provider_policy_changed=False)
    if options.action == 'validate':
        print(json.dumps(manifest, sort_keys=True, indent=2))
        return
    observer.require(bool(os.environ.get('NVIDIA_API_KEY')), 'inherited_provider_environment_required')
    manifest_path = HERE / 'P3_RETRY_PARENT_MANIFEST.json'
    observer.require(manifest == observer.read(manifest_path) and time.time() < observer.END_UNIX,
        'immutable_retry_parent_manifest_and_horizon')
    module.base.WALL = observer.END_UNIX
    policy.local_attempts(output / 'turns')
    original_path = output / 'CONFIG.json'
    original_read, original_sha = module.base.read, module.base.sha
    module.base.read = lambda path: config if Path(path) == original_path else original_read(path)
    module.base.sha = lambda path: observer.digest(manifest_path) if Path(path) == original_path else original_sha(path)
    module.base.runtime = lambda: policy

    def record(event):
        with (HERE / 'P3_RETRY_TRANSPORT.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')

    def remote(physical, request):
        observer.require(physical == 3 and request.get('op') in ('poll','publish'), 'retry_P3_poll_publish_only')
        result = subprocess.run(['bash', str(module.base.REPO / 'gpu/a40r_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE_ENDPOINT],
            input=json.dumps(dict(request, physical=physical)), capture_output=True, text=True, timeout=120)
        if result.returncode:
            record(dict(kind='RETRY_PARENT_TRANSPORT_FAILED', operation=request['op'],
                observed_unix=time.time(), stderr_sha256=observer.content_digest(result.stderr), publication_retried=False))
            raise RuntimeError('retry_parent_transport_failed_no_publication_retry')
        value = json.loads(result.stdout)
        record(dict(kind='RETRY_PARENT_TRANSPORT_SUCCESS', operation=request['op'], observed_unix=time.time(),
            response_sha256=observer.content_digest(value), native_loaded_index=binding['loaded_index'],
            reference_sha256=value.get('reference', {}).get('sha256'), publication_id=value.get('id')))
        return value

    module.remote = p3_lease_parent.p3_incremental.previous.recover_poll(remote, observer.END_UNIX, record)
    record(dict(kind='P3_RETRY_PARENT_ACTIVE', pid=os.getpid(), observed_unix=time.time(),
        native_pid=binding['pid'], hard_end_unix=observer.END_UNIX, learner_signals=[]))
    module.serve(3)


if __name__ == '__main__':
    main()
