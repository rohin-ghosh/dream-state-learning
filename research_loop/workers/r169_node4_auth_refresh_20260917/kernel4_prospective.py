"""Explicit prospective kernel4 source replacement, not an old-code restore."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import tomllib

import refresh_node4 as raw3


custody = raw3.custody
HERE = raw3.HERE
LABEL = 'PROSPECTIVE_PARENT_SOURCE_REPLACEMENT_NOT_EXACT_OLD_CODE_RESTORE'
OLD_HOME = raw3.REPOSITORY / 'research_notes/analysis/orch_r136_node4_20260916'
OLD_OUTPUT = OLD_HOME / 'kernel4_parent_v1'
OLD_CONFIG = OLD_HOME / 'KERNEL4_PARENT_CONFIG.json'
ROOT = '/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1'
BRANCH = 'r137_kernel4_sparse2_free_coach'
POLICY = raw3.LEGACY.parent / 'r167_parent_policy_candidates_20260917/R154_ATTENTION_V2/KERNEL0_RESUMED_SPARSE2_1045188/PRINCIPLES.md'
POLICY_SHA = 'c94f92d5c994cab3594b06ca1163e8d211ccb5760b29b2999a2d26f5a831c248'
EXPECTED = json.loads(custody.read(raw3.LEGACY / 'NODE4_FINAL_STATUS.json'))['kernel4']['parent']
NUDGE_RECEIPT = HERE.parent / 'r158_kernel_execution_20260917/astra_publication_receipts/astra_main_nudge_20260917t0422z/LANE4_PUBLISHED.json'
NUDGE_SHA = 'a4226c6638e2c91b9fcee333cc0ff05716e5c0bc84d5f101c469753831798dd7'


def verify(observed):
    custody.require(all(observed[key] == EXPECTED[key] for key in
        ('pid', 'start_ticks', 'argv', 'uid', 'cwd')), 'exact_kernel4_parent_identity')
    custody.require(observed['uid'] == os.getuid() and observed['state'] not in ('Z', 'X'), 'live_owned_kernel4')


def terminal_ledger(output=OLD_OUTPUT):
    output = Path(output)
    config = json.loads(custody.read(OLD_CONFIG))
    started = json.loads(custody.read(output / 'STARTED.json'))
    custody.require(started['branch'] == BRANCH and started['programme'] == 'kernel'
        and started['config_sha256'] == custody.ref(OLD_CONFIG)['sha256'], 'bound_original_startup')
    cursor = config.get('start_after_response_count', 0)
    files, publications, pending, statuses, failures = {}, {}, [], {}, []
    directories = sorted(output.glob('parent_*'))
    custody.require(len(directories) <= 10000, 'bounded_attempt_count')
    total = 0
    for directory in directories:
        custody.require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt_only')
        source = json.loads(custody.read(directory / 'SOURCE.json'))
        result = json.loads(custody.read(directory / 'RESULT.json'))
        intent = json.loads(custody.read(directory / 'DISPATCH_INTENT.json'))
        reserved = source['response_count']
        custody.require(type(reserved) is int and reserved >= cursor, 'monotonic_reserved_SOURCE_cursor')
        custody.require(result['branch'] == BRANCH and result['programme'] == 'kernel'
            and result['source_head_sha256'] == source['head_sha256']
            and result['source_response_count'] == reserved and result['retry'] is False
            and result['finished_unix'] >= result['started_unix'], 'terminal_result_bound_to_source')
        custody.require(intent['source_response_count'] == reserved and intent['retries'] == 0
            and intent['source_sha256'] == custody.ref(directory / 'SOURCE.json')['sha256']
            and intent['system_sha256'] == custody.ref(directory / 'SYSTEM.txt')['sha256']
            and intent['prompt_sha256'] == custody.ref(directory / 'PROMPT.txt')['sha256'], 'bound_reserved_intent')
        status = result['status']
        if status == 'PUBLISHED':
            publication = result['inbox_publication']
            custody.require(result['actual_model'] == raw3.MODEL and result['response']['speak'] is True
                and result['sent_unix'] >= result['started_unix']
                and publication['path'] == ROOT + '/stream/inbox/' + publication['id'] + '.json'
                and len(publication['sha256']) == 64, 'known_terminal_publication')
            custody.require(publication['id'] not in publications, 'unique_publication_ids')
            publications[publication['id']] = publication
            if not (directory / 'DELIVERED.json').exists():
                pending.append(publication['id'])
        elif status == 'SILENT':
            custody.require(result['actual_model'] == raw3.MODEL and result['response']['speak'] is False
                and result['response']['message'] == ''
                and not any(key in result for key in ('sent_unix', 'inbox_publication')), 'known_terminal_silence')
        else:
            custody.require(status == 'MISSING' and result.get('error_type') == 'HTTPError'
                and result.get('error_code') == 'parent_call_or_delivery_failed'
                and not any(key in result for key in ('sent_unix', 'inbox_publication', 'response', 'usage'))
                and not (directory / 'stdout.json').exists(), 'unknown_publication_refuse')
            error = json.loads(custody.read(directory / 'http_error_response.txt'))['error']
            custody.require(error.get('code') in (429, '429') and error.get('type') == 'budget_exceeded',
                            'only_evidenced_terminal_provider_budget_denial')
            dispatch = json.loads(custody.read(directory / 'DISPATCH.json'))
            request = json.loads(custody.read(directory / 'API_REQUEST.json'))
            custody.require(dispatch['attempts'] == 1 and dispatch['retries'] == 0
                and dispatch['requested_model'] == raw3.MODEL and request['model'] == raw3.MODEL,
                'single_canonical_denied_request_no_replay')
            failures.append(dict(attempt=directory.name, reserved=reserved,
                disposition='TERMINAL_PROVIDER_DENIAL_RESERVED_NEVER_REPLAY',
                evidence=custody.ref(directory / 'http_error_response.txt')))
        statuses[status] = statuses.get(status, 0) + 1
        cursor = reserved
        children = list(directory.iterdir())
        custody.require(len(children) <= 128, 'bounded_attempt_files')
        for path in children:
            content = custody.read(path)
            total += len(content)
            custody.require(total <= 512 * 1024**2, 'bounded_total_artifact_bytes')
            files[str(path.relative_to(output))] = custody.digest(content)
    return dict(reserved=cursor, clock='response_count', attempts=len(directories), files=files,
        started_sha256=custody.ref(output / 'STARTED.json')['sha256'], statuses=statuses,
        publications=publications, pending_inbox_ids=pending, terminal_denials=failures)


def external_publications():
    receipt = json.loads(custody.bound(dict(path=str(NUDGE_RECEIPT), sha256=NUDGE_SHA)))
    custody.require(receipt['before']['root'] == ROOT and receipt['speaker'] == 'Astra'
        and receipt['status'] == 'PUBLISHED_NOT_RENDERED_OR_EXECUTED'
        and receipt['observed_unix'] == 1789618892.511736, 'exact_prior_Main_nudge_receipt')
    publication = receipt['inbox_publication']
    return {publication['id']: publication}


def verify_inbox(rows, ledger, external=None):
    known = dict(ledger['publications'])
    custody.require(not (set(known) & set(external or {})), 'no_duplicate_external_publication')
    known.update(external or {})
    parents = {row['id']: row for row in rows if row['actor'] == 'parent' or row['speaker'] == 'Astra'}
    custody.require(len(parents) == sum(row['actor'] == 'parent' or row['speaker'] == 'Astra' for row in rows),
                    'unique_observed_parent_inbox_ids')
    custody.require(set(parents) == set(known), 'unknown_or_missing_parent_publication_refuse')
    for identifier, publication in known.items():
        custody.require(parents[identifier]['sha256'] == publication['sha256']
            and parents[identifier]['path'] == publication['path']
            and parents[identifier]['actor'] == 'parent' and parents[identifier]['speaker'] == 'Astra'
            and parents[identifier]['split'] == 'TRAIN', 'exact_published_inbox_custody')


def inbox_snapshot():
    script = """
import hashlib,json
from pathlib import Path
root=Path(ROOT)/'stream/inbox'
files=sorted(root.glob('*.json')); assert len(files)<1000
rows=[]
for path in files:
 assert not path.is_symlink() and path.stat().st_size<1048576
 raw=path.read_bytes(); doc=json.loads(raw)
 rows.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),
  id=doc.get('id'),speaker=doc.get('speaker'),actor=doc.get('actor'),split=doc.get('split')))
print(json.dumps(rows))
"""
    result = subprocess.run(['bash', str(raw3.REPOSITORY / 'gpu/a40r_ssh.sh'), 'python3 -B -'],
        input=('ROOT=' + repr(ROOT) + '\n' + script).encode(), capture_output=True, timeout=45)
    custody.require(result.returncode == 0, 'remote_inbox_metadata_failed')
    return json.loads(result.stdout)


def candidate_config(old, ledger):
    custody.require(old['branch'] == BRANCH and old['root'] == ROOT and old['node'] == 'a40r'
        and old['physical'] == 4 and old['programme'] == 'kernel' and old['cadence_responses'] == 2
        and old['parent_style'] == 'experimental-coach' and old['cadence_label'] == 'SPARSE'
        and old['source_root'] == ROOT.removesuffix('/run1') + '/source1'
        and old['hard_end_unix'] > time.time(), 'exact_original_life_cadence_and_wall')
    return dict(old, parent_module_sha256=raw3.PARENT_SHA,
        principles_path=str(POLICY), principles_sha256=POLICY_SHA,
        predecessor_output=str(OLD_OUTPUT), predecessor_started_sha256=ledger['started_sha256'],
        start_after_response_count=ledger['reserved'])


def current_binding():
    binding = json.loads(custody.read(raw3.PREVIOUS / 'BINDING.json'))
    native = json.loads(custody.read(HERE / 'NODE4_NATIVE_INITIAL.json'))
    native = next(row for row in native['processes'] if row['pid'] == 3496993)
    binding.update(branch=BRANCH, root=ROOT, parent=EXPECTED, native=native, old_output=str(OLD_OUTPUT))
    return binding


def verify_preserved(ledger):
    custody.require(custody.ref(OLD_OUTPUT / 'STARTED.json')['sha256'] == ledger['started_sha256'],
                    'old_startup_unchanged')
    for name, expected in ledger['files'].items():
        custody.require(custody.ref(OLD_OUTPUT / name)['sha256'] == expected, 'all_old_artifacts_byte_identical')


def prepare(home):
    home.mkdir(mode=0o700)
    verify(custody.identity(EXPECTED['pid']))
    old = json.loads(custody.read(OLD_CONFIG))
    ledger = terminal_ledger()
    rows = inbox_snapshot()
    verify_inbox(rows, ledger, external_publications())
    binding = current_binding()
    native = raw3.original.native_check(binding)
    custody.require(custody.ref(POLICY)['sha256'] == POLICY_SHA, 'approved_R154_attention_policy')
    config = candidate_config(old, ledger)
    custody.write(home / 'CONFIG.json', config)
    cpu = raw3.original.cpu_preflight(binding, home / 'CONFIG.json')
    custody.require(cpu['cursor'] == ledger['reserved'] and cpu['model'] == raw3.MODEL,
                    'actual_CPU_startup_cursor_model')
    source_root = Path(binding['successor_cwd'])
    custody.require(custody.ref(source_root / 'gpu/orch_r133_programme_parent.py')['sha256'] == raw3.PARENT_SHA
        and custody.ref(source_root / 'gpu/orch_r136_node4_parent.py')['sha256'] == raw3.ADAPTER_SHA,
        'known_prospective_parent_and_adapter')
    pins = cpu['imports'] + [custody.ref(__file__), custody.ref(raw3.__file__), custody.ref(custody.__file__),
        custody.ref(raw3.original.__file__), custody.ref(OLD_CONFIG), custody.ref(POLICY),
        custody.ref(old['programme_path']), custody.ref(home / 'CONFIG.json'),
        custody.ref(OLD_HOME / 'KERNEL4_PARENT_DISPATCH.json'), custody.ref(NUDGE_RECEIPT)]
    custody.write(home / 'PREPARED.json', dict(label=LABEL, binding=binding, ledger=ledger,
        changed_config_fields=sorted(key for key in config if config[key] != old.get(key)),
        old_source_match_claimed=False, original_source_gap_retained=True, pins=pins,
        cpu=cpu, inbox=rows, external_publications_preserved=external_publications(),
        native=native, no_signals=True, observed_unix=time.time()))


@contextmanager
def paused(operations=None):
    operations = operations or custody.Operations()
    observed = operations.identity(EXPECTED['pid'])
    verify(observed)
    custody.require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    custody.require(operations.children_absent(EXPECTED['pid']), 'child_present_no_signal')
    descriptor = operations.open(EXPECTED['pid'])
    stopped = False
    try:
        verify(operations.identity(EXPECTED['pid']))
        operations.signal(descriptor, signal.SIGSTOP)
        stopped = True
        for attempt in range(100):
            if operations.identity(EXPECTED['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        operations.childless_stopped(EXPECTED['pid'])
        verify(operations.identity(EXPECTED['pid']))
        yield descriptor, operations
    finally:
        if stopped:
            try:
                operations.signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        operations.close(descriptor)


def execute(home):
    gate = json.loads(custody.read(HERE / 'KERNEL4_CPU_GATE.json'))
    custody.require(gate['status'] == 'PASS' and gate['label'] == LABEL, 'scoped_prospective_CPU_gate')
    for pin in gate['pins']:
        custody.bound(pin)
    prepared = json.loads(custody.read(home / 'PREPARED.json'))
    for pin in prepared['pins']:
        custody.bound(pin)
    custody.require(prepared['label'] == LABEL and prepared['old_source_match_claimed'] is False,
                    'explicit_prospective_replacement_only')
    custody.require(bool(os.environ.get('NVIDIA_API_KEY')), 'privately_sourced_current_key')
    provider = tomllib.loads((Path.home() / '.codex/nvidia-astra.config.toml').read_text())
    custody.require(provider['model'] == raw3.MODEL, 'canonical_model_only')
    binding = prepared['binding']
    raw3.original.native_check(binding)
    custody.require(not (home / 'TERMINATION_ONCE.json').exists() and not (home / 'parent').exists(),
                    'fresh_attempt_no_termination_replay')
    with (HERE / 'KERNEL4_OPERATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with paused() as (descriptor, operations):
            ledger = terminal_ledger()
            custody.require(ledger == prepared['ledger'], 'ledger_changed_new_candidate_required')
            inbox = inbox_snapshot()
            verify_inbox(inbox, ledger, external_publications())
            for pin in prepared['pins']:
                custody.bound(pin)
            old = json.loads(custody.read(OLD_CONFIG))
            candidate = json.loads(custody.read(home / 'CONFIG.json'))
            custody.require(candidate == candidate_config(old, ledger), 'narrow_source_policy_cursor_only')
            operations.childless_stopped(EXPECTED['pid'])
            custody.write(home / 'TERMINATION_ONCE.json', dict(label=LABEL, parent=EXPECTED,
                ledger=ledger, verified_parent_inbox_ids=sorted(ledger['publications']), observed_unix=time.time()))
            operations.signal(descriptor, signal.SIGTERM)
            operations.signal(descriptor, signal.SIGCONT)
            custody.require(operations.exited(descriptor), 'pidfd_exit_required_no_successor')
            custody.write(home / 'PREDECESSOR_EXIT.json', dict(pid=EXPECTED['pid'],
                pidfd_exit_confirmed=True, observed_unix=time.time()))
        verify_preserved(ledger)
        for pin in prepared['pins']:
            custody.bound(pin)
        command = [binding['python'], '-B', '-m', 'gpu.orch_r136_node4_parent',
            '--config', str(home / 'CONFIG.json'), '--repository', str(raw3.REPOSITORY),
            '--output', str(home / 'parent')]
        environment = dict(os.environ, PYTHONPATH=binding['successor_cwd'], PYTHONDONTWRITEBYTECODE='1')
        with (home / 'PARENT.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=binding['successor_cwd'], env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        custody.write(home / 'SPAWNED.json', dict(pid=process.pid, label=LABEL,
            command=command, observed_unix=time.time()))
        for attempt in range(100):
            if (home / 'parent/STARTED.json').exists() or process.poll() is not None:
                break
            time.sleep(0.1)
        custody.require(process.poll() is None, 'successor_live_required')
        started = json.loads(custody.read(home / 'parent/STARTED.json'))
        custody.require(started['pid'] == process.pid and started['model'] == raw3.MODEL
            and started['config_sha256'] == custody.ref(home / 'CONFIG.json')['sha256'], 'bound_actual_startup')
        inherited = (Path('/proc') / str(process.pid) / 'environ').read_bytes().split(b'\0')
        custody.require(b'NVIDIA_API_KEY='[REDACTED_SECRET]'NVIDIA_API_KEY'].encode() in inherited,
                        'current_credential_inherited')
        verify_preserved(ledger)
        verify_inbox(inbox_snapshot(), ledger, external_publications())
        custody.write(home / 'RUNNING.json', dict(label=LABEL, parent=custody.identity(process.pid),
            current_key_equality_verified=True, credential_values_recorded=False,
            started=custody.ref(home / 'parent/STARTED.json'), reserved_cursor=ledger['reserved'],
            preserved_files=len(ledger['files']), pending_inbox_ids_untouched=ledger['pending_inbox_ids'],
            no_child_signals=True, no_old_source_match_claim=True, observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'execute'))
    parser.add_argument('--attempt', required=True)
    arguments = parser.parse_args()
    custody.require(arguments.attempt.isalnum(), 'simple_fresh_attempt_name')
    home = HERE / arguments.attempt
    try:
        (prepare if arguments.action == 'prepare' else execute)(home)
    except Exception as error:
        if home.exists():
            custody.write(home / ('REFUSAL_' + str(time.time_ns()) + '.json'),
                dict(error_type=type(error).__name__,
                    reason=str(error) if isinstance(error, ValueError) else 'operational_failure',
                    termination_latched=(home / 'TERMINATION_ONCE.json').exists()))
        print(json.dumps(dict(status='REFUSED', error_type=type(error).__name__)))
        raise SystemExit(1)
    print(json.dumps(dict(status=arguments.action.upper() + '_OK', label=LABEL, attempt=str(home))))
