import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r167_object_survival_20260917')
CONTROL = ROOT / 'control_generation3'
MANIFEST_SHA = '31d14f957712bd091d64071ed5a7059b76f2c06c370be7e56db37425959d575d'
HELPER_SHA = '12e971f547a05319ac6aa478e7cdea07b0d84fe8e285e28e5f574d4bdfb017ce'
LAUNCHER_SHA = 'aceb4cc36e5fc5fcce623fe008bc7d7499a54cf97eda8f01cb3e9ca81ab4c130'
SOURCE = ROOT / 'runtime_generation5' / 'source'
OPERATION = CONTROL / 'operation1'
ORDER = (8, 25, *range(9, 25), 0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def jobs_for_slot(manifest, physical):
    assert physical in (0, 1)
    selected = [job for job in manifest['jobs'] if job['physical'] == physical]
    condition = 'LORA_ON' if physical == 0 else 'LORA_OFF'
    assert [job['key'] for job in selected] == [f'{milestone}_{condition}' for milestone in ORDER]
    return selected


def setup():
    assert sha(CONTROL / 'MANIFEST.json') == MANIFEST_SHA
    manifest = read(CONTROL / 'MANIFEST.json')
    assert manifest['calls'] == 114 and manifest['job_cap'] == 38 and manifest['generated_token_cap'] == 58368
    assert manifest['maximum_wall_seconds'] == 10800
    assert sha(SOURCE / 'gpu/orch_r167_object_survival_eval.py') == HELPER_SHA
    assert sha(ROOT / 'runtime_generation5/launch.py') == LAUNCHER_SHA
    for physical in (0, 1):
        jobs_for_slot(manifest, physical)
    OPERATION.mkdir(mode=0o700)
    go_root = OPERATION / 'gos'
    go_root.mkdir(mode=0o700)
    approved = []
    for job in manifest['jobs']:
        assert ref(job['execution']['path']) == job['execution']
        go = dict(schema='R167_OBJECT_SURVIVAL_V1', status='MAIN_GO', execution=job['execution'])
        go_ref = write(go_root / (job['key'] + '.MAIN_GO.json'), go)
        approved.append(dict(job, go=go_ref))
    authority = dict(status='EXPLICIT_MAIN_EXECUTOR_GO', schema='R167_OBJECT_SURVIVAL_V1',
        manifest=ref(CONTROL / 'MANIFEST.json'), approved=approved, calls=114, generated_token_cap=58368,
        maximum_wall_seconds=10800, physical_slots=[0, 1], created_unix=time.time(),
        scope='Main exact generation3 GO under standing builder/Rohin152-154; not model ratification',
        no_source_substitution=True, no_retry=True, no_preemption=True, parent_access=False)
    authority_ref = write(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json', authority)
    return dict(status='38_EXACT_GOS_STAGED_NO_NATIVE_YET', authority=authority_ref,
                go_count=38, model_calls=0)


def released_terminal(job, sidecar):
    directory = OPERATION / 'launches' / job['key']
    disposition = directory / 'DISPOSITION.json'
    if not disposition.exists():
        return False
    attempt = ROOT / 'attempts' / job['key']
    terminal = ROOT / 'ledger' / (job['key'] + '.COMPLETE.json')
    if not terminal.exists():
        return False
    assert read(disposition)['status'] == 'METADATA_ONLY'
    identities = [read(directory / 'WRAPPER.json')['identity'],
                  read(attempt / 'LAUNCH.json')['identity'],
                  read(attempt / 'sealed' / 'PROCESS.json')['identity']]
    return all(sidecar.gone(identity) for identity in identities)


def run_slot(physical, authority, sidecar):
    jobs = jobs_for_slot(dict(jobs=authority['approved']), physical)
    for job in jobs:
        assert ref(job['execution']['path']) == job['execution'] and ref(job['go']['path']) == job['go']
        directory = OPERATION / 'launches' / job['key']
        config = read(job['execution']['path'])
        command = [config['python'], '-B', str(ROOT / 'runtime_generation5/launch.py'), 'start',
            '--config', job['execution']['path'], '--go', job['go']['path'], '--go-sha256', job['go']['sha256'],
            '--source', str(SOURCE), '--directory', str(directory)]
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        write(OPERATION / (job['key'] + '.START_OUTPUT.private.json'), dict(
            stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace')))
        write(OPERATION / (job['key'] + '.START.json'), dict(returncode=result.returncode,
            go=job['go'], execution=job['execution'], observed_unix=time.time()))
        assert result.returncode == 0, 'approved_launcher_start_failed_no_retry'
        started = json.loads(result.stdout)
        write(OPERATION / (job['key'] + '.WRAPPER_START.json'), started)
        until = time.monotonic() + 1100
        while time.monotonic() < until:
            if released_terminal(job, sidecar):
                write(OPERATION / (job['key'] + '.RELEASED.json'), dict(status='COMPLETE_AND_IDENTITIES_RELEASED',
                    key=job['key'], observed_unix=time.time()))
                break
            if (directory / 'DISPATCH_ERROR.json').exists():
                raise RuntimeError('dispatch_failed_no_retry')
            if (directory / 'DISPOSITION.json').exists() and read(directory / 'DISPOSITION.json').get('status') != 'METADATA_ONLY':
                raise RuntimeError('admission_refused_no_retry')
            if sidecar.gone(started['identity']) and not (directory / 'DISPOSITION.json').exists():
                raise RuntimeError('wrapper_gone_without_disposition_uncertain')
            time.sleep(1)
        else:
            raise RuntimeError('metadata_wait_exhausted_no_retry_no_signal')
    return dict(physical=physical, status='ALL_19_CONDITION_JOBS_COMPLETE', completed_unix=time.time())


def run():
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r130_benchmark_sidecar as sidecar
    authority = read(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json')
    assert authority['manifest'] == ref(CONTROL / 'MANIFEST.json') and authority['manifest']['sha256'] == MANIFEST_SHA
    write(OPERATION / 'CONTROLLER_ONCE.json', dict(identity=sidecar.identity(os.getpid()), started_unix=time.time(),
        authority=ref(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json')))
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(run_slot, physical, authority, sidecar): physical for physical in (0, 1)}
        for future in as_completed(jobs):
            physical = jobs[future]
            try:
                write(OPERATION / f'PHYSICAL{physical}.COMPLETE.json', future.result())
            except BaseException as error:
                write(OPERATION / f'PHYSICAL{physical}.BLOCKED.json', dict(status='BLOCKED_NO_RETRY_NO_SIGNAL',
                    error_type=type(error).__name__, observed_unix=time.time()))


def observe():
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r167_object_survival_eval as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    authority = read(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json')
    keys = {}
    for job in authority['approved']:
        attempt = ROOT / 'attempts' / job['key']
        item = dict(physical=job['physical'], once=(attempt / 'ONCE.json').exists(),
            reserved=(ROOT / 'ledger' / (job['key'] + '.RESERVED.json')).exists(),
            complete=(ROOT / 'ledger' / (job['key'] + '.COMPLETE.json')).exists(),
            failed=(ROOT / 'ledger' / (job['key'] + '.FAILED.json')).exists(),
            unresolved_artifact=(attempt / 'UNRESOLVED.json').exists(),
            released=(OPERATION / (job['key'] + '.RELEASED.json')).exists())
        if (attempt / 'ACTUAL_ADMISSION.private.json').exists():
            admission = read(attempt / 'ACTUAL_ADMISSION.private.json')
            item['admission'] = dict(reference=ref(attempt / 'ACTUAL_ADMISSION.private.json'),
                clear=admission['clear'], blocking_reason_count=len(admission['blocking_reasons']))
        if (attempt / 'sealed' / 'PROCESS.json').exists():
            identity = read(attempt / 'sealed' / 'PROCESS.json')['identity']
            item['native'] = dict(identity=identity, gone=sidecar.gone(identity))
        keys[job['key']] = item
    return dict(status='METADATA_ONLY', observed_unix=time.time(),
        ledger=evaluator.status(ROOT, read(CONTROL / 'MANIFEST.json')['plan']['sha256']),
        keys=keys, authority=ref(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json'),
        blocked_slots=[physical for physical in (0, 1) if (OPERATION / f'PHYSICAL{physical}.BLOCKED.json').exists()])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('setup', 'run', 'observe'))
    args = parser.parse_args()
    result = globals()[args.action]()
    if result is not None:
        print(json.dumps(result, sort_keys=True))
