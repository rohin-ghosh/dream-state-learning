import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r167_object_survival_20260917')
OPERATION = ROOT / 'control_generation3' / 'operation1'
SOURCE = ROOT / 'runtime_generation5' / 'source'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def gone(sidecar, identity):
    try:
        return sidecar.gone(identity)
    except ProcessLookupError:
        return not (Path('/proc') / str(identity['pid'])).exists()


def remaining_jobs(authority, completed, invoked):
    jobs = [job for job in authority['approved'] if job['physical'] == 1]
    expected = [f'{milestone}_LORA_OFF' for milestone in (8, 25, *range(9, 25), 0)]
    assert [job['key'] for job in jobs] == expected
    assert completed == {'8_LORA_OFF', '25_LORA_OFF'}
    remaining = jobs[2:]
    assert not {job['key'] for job in remaining} & invoked
    return remaining


def all_released(key, sidecar):
    attempt = ROOT / 'attempts' / key
    launcher = OPERATION / 'launches' / key
    assert (ROOT / 'ledger' / (key + '.COMPLETE.json')).exists()
    identities = [read(attempt / 'sealed' / 'PROCESS.json')['identity'],
                  read(attempt / 'LAUNCH.json')['identity'], read(launcher / 'WRAPPER.json')['identity']]
    return all(gone(sidecar, identity) for identity in identities)


def run():
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r130_benchmark_sidecar as sidecar
    from gpu import orch_r167_object_survival_eval as evaluator
    assert evaluator.sha(evaluator.__file__) == '12e971f547a05319ac6aa478e7cdea07b0d84fe8e285e28e5f574d4bdfb017ce'
    assert sha(ROOT / 'control_generation3/MANIFEST.json') == '31d14f957712bd091d64071ed5a7059b76f2c06c370be7e56db37425959d575d'
    assert sha(ROOT / 'runtime_generation5/launch.py') == 'aceb4cc36e5fc5fcce623fe008bc7d7499a54cf97eda8f01cb3e9ca81ab4c130'
    assert sha(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json') == '1adf441acda98c2c791792936b48c7b3e7143cf0d1c5e4f5bc1ea813790c3585'
    assert read(OPERATION / 'PHYSICAL1.BLOCKED.json')['error_type'] == 'ProcessLookupError'
    authority = read(OPERATION / 'MAIN_EXECUTION_AUTHORITY.json')
    completed = {path.name.removesuffix('.COMPLETE.json') for path in (ROOT / 'ledger').glob('*_LORA_OFF.COMPLETE.json')}
    invoked = {path.name for path in (ROOT / 'attempts').iterdir() if path.is_dir()}
    invoked |= {path.name for path in (OPERATION / 'launches').iterdir() if path.is_dir()}
    jobs = remaining_jobs(authority, completed, invoked)
    assert all(all_released(key, sidecar) for key in completed)
    directory = OPERATION / 'unused_off_resume1'
    directory.mkdir(mode=0o700)
    write(directory / 'ONCE.json', dict(status='ONLY_UNUSED_AUTHORIZED_KEYS', keys=[job['key'] for job in jobs],
        original_failure_sha256=sha(OPERATION / 'PHYSICAL1.BLOCKED.json'), completed_predecessors=sorted(completed),
        identity=sidecar.identity(os.getpid()), created_unix=time.time(), consumed_job_retries=0))
    try:
        for job in jobs:
            config_path, go_path = job['execution']['path'], job['go']['path']
            assert sha(config_path) == job['execution']['sha256'] and sha(go_path) == job['go']['sha256']
            launcher_directory = OPERATION / 'launches' / job['key']
            assert not launcher_directory.exists() and not (ROOT / 'attempts' / job['key']).exists()
            config = read(config_path)
            command = [config['python'], '-B', str(ROOT / 'runtime_generation5/launch.py'), 'start',
                '--config', config_path, '--go', go_path, '--go-sha256', job['go']['sha256'],
                '--source', str(SOURCE), '--directory', str(launcher_directory)]
            result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
            write(directory / (job['key'] + '.START.private.json'), dict(returncode=result.returncode,
                stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace')))
            assert result.returncode == 0
            started = json.loads(result.stdout)
            until = time.monotonic() + 1100
            while time.monotonic() < until:
                disposition = launcher_directory / 'DISPOSITION.json'
                if disposition.exists():
                    assert read(disposition)['status'] == 'METADATA_ONLY', 'admission_refusal_no_retry'
                    assert (ROOT / 'ledger' / (job['key'] + '.COMPLETE.json')).exists()
                    if all_released(job['key'], sidecar):
                        write(OPERATION / (job['key'] + '.RELEASED.json'), dict(status='COMPLETE_AND_IDENTITIES_RELEASED',
                            key=job['key'], observed_unix=time.time(), observer='unused_off_resume1'))
                        break
                assert not (launcher_directory / 'DISPATCH_ERROR.json').exists()
                assert not (gone(sidecar, started['identity']) and not disposition.exists())
                time.sleep(1)
            else:
                raise RuntimeError('metadata_wait_exhausted_no_retry')
        write(directory / 'COMPLETE.json', dict(status='17_UNUSED_OFF_JOBS_COMPLETE', completed_unix=time.time()))
    except BaseException as error:
        write(directory / 'BLOCKED.json', dict(status='BLOCKED_NO_RETRY_NO_SIGNAL', error_type=type(error).__name__,
            observed_unix=time.time()))


if __name__ == '__main__':
    run()
