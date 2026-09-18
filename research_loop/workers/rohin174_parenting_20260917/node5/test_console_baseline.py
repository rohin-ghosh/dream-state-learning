import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from console_baseline import load_runtime, lock_owner, merge_seed, parent_census, publish_baseline, read, ref, retire_exact, write


HERE = Path(__file__).resolve().parent
ROOT = HERE / 'ACTIVATION_A_1789678829928180897'
MANIFEST = read(ROOT / 'run1_MANIFEST.json')
RUNTIME, POLICY, PROVENANCE = load_runtime(MANIFEST)
specification = importlib.util.spec_from_file_location('arm_fixtures',
    Path(MANIFEST['source']) / 'tests/test_node5_r175_activation.py')
fixtures = importlib.util.module_from_spec(specification)
specification.loader.exec_module(fixtures)


def baseline():
    return dict(authorship='NODE5_CODEX_AUTHORED_UNDER_MAIN_CONSOLE_DELEGATION', response=fixtures.reply())


def test_actual_lossless_parser_and_owned_tick_remain_strict():
    assert POLICY.tick.__code__.co_filename == MANIFEST['source'] + '/gpu/orch_r166_parent_policy.py'
    assert PROVENANCE['strict_validators_preserved']
    response = baseline()['response']
    response['rationale'] = json.loads(response['rationale'])
    current = fixtures.state(5)
    assert POLICY.decision(response, current, POLICY.memory(fixtures.seed(), [], current))['object_id']
    response['rationale']['object_id'] = 'UPPERCASE'
    with pytest.raises(ValueError):
        POLICY.decision(response, current, POLICY.memory(fixtures.seed(), [], current))


def test_console_publication_is_not_fake_API_or_render(tmp_path):
    current = fixtures.state(5)
    config = fixtures.config(tmp_path)
    publication = dict(id='fixture', sha256='e' * 64, path='/inbox/fixture.json')
    with patch.object(POLICY.parent, 'publish', return_value=publication) as publish:
        result = publish_baseline(POLICY, Path(MANIFEST['source']), config, tmp_path, fixtures.seed(),
                                  current, baseline(), dict(path='/cpu/baseline', sha256='a' * 64))
        assert result['status'] == 'PUBLISHED' and result['model'] is None and result['API_calls'] == 0
        assert not read(tmp_path / 'FIRST_PUBLICATION.json')['rendered']
        assert not (tmp_path / 'FIRST_RENDERED_REQUEST.json').exists()
        assert publish.call_count == 1
        with pytest.raises(FileExistsError):
            publish_baseline(POLICY, Path(MANIFEST['source']), config, tmp_path, fixtures.seed(),
                             current, baseline(), dict(path='/cpu/baseline', sha256='a' * 64))
        assert publish.call_count == 1


def test_unknown_publication_preserved_no_retry(tmp_path):
    with patch.object(POLICY.parent, 'publish', side_effect=ValueError('transport_lost')) as publish:
        with pytest.raises(ValueError, match='NO_RETRY'):
            publish_baseline(POLICY, Path(MANIFEST['source']), fixtures.config(tmp_path), tmp_path,
                             fixtures.seed(), fixtures.state(5), baseline(), {})
        result = read(next(tmp_path.glob('parent_*/RESULT.json')))
        assert result['status'] == 'PUBLICATION_UNKNOWN'
        assert next(tmp_path.glob('parent_*/PUBLISH_INTENT.json')).exists()
        assert publish.call_count == 1


def test_bad_quote_and_cap_fail_before_publication(tmp_path):
    response = baseline()
    details = json.loads(response['response']['rationale'])
    details['perception']['quote'] = 'Never observed'
    response['response']['rationale'] = json.dumps(details)
    with patch.object(POLICY.parent, 'publish') as publish:
        with pytest.raises(ValueError):
            publish_baseline(POLICY, Path(MANIFEST['source']), fixtures.config(tmp_path), tmp_path,
                             fixtures.seed(), fixtures.state(5), response, {})
        publish.assert_not_called()
        assert not list(tmp_path.glob('parent_*'))


def test_seed_retains_reserved_failed_source_without_counter_reset(tmp_path):
    original = fixtures.seed()
    original['last_response_count'] = 3
    original['last_request_count'] = 3
    write(tmp_path / 'SEED.json', original)
    directory = tmp_path / 'parent_000000000005'
    directory.mkdir()
    write(directory / 'SOURCE.json', fixtures.state(5))
    write(directory / 'RESULT.json', dict(status='PROVIDER_FAILED',
        source_sha256=ref(directory / 'SOURCE.json')['sha256'], error='HTTP404'))
    combined = merge_seed(POLICY, tmp_path, fixtures.state(5))
    assert len(combined['attempts']) == 1
    assert combined['last_response_count'] == 3
    assert POLICY.memory(combined, [], fixtures.state(5))['last_response_count'] == 5
    assert read(tmp_path / 'SEED.json') == original


@pytest.mark.parametrize('reject', [False, True])
def test_CPU_exact_owner_same_inode_flock_transfer_or_resume(tmp_path, reject):
    lock_path = tmp_path / 'PARENT.lock'
    lock_path.touch()
    process = subprocess.Popen([sys.executable, '-B', '-c',
        'import fcntl,sys,time; stream=open(sys.argv[1],"r+"); '
        'fcntl.flock(stream,fcntl.LOCK_EX); print("ready",flush=True); time.sleep(60)', str(lock_path)],
        stdout=subprocess.PIPE, text=True, start_new_session=True)
    result = None
    try:
        assert process.stdout.readline().strip() == 'ready'
        row = dict(RUNTIME.identity(process.pid), label='run1')
        original_inode = lock_path.stat().st_ino
        assert lock_owner(lock_path, process.pid)['inode'] == original_inode

        def revalidate(watchdog_identity):
            assert watchdog_identity['pid'] != process.pid
            if reject:
                raise ValueError('CPU_refusal_before_retirement')

        if reject:
            with pytest.raises(ValueError, match='CPU_refusal'):
                retire_exact(RUNTIME, row, lock_path, tmp_path, revalidate)
            assert process.poll() is None
            assert not (tmp_path / 'PARENT_RETIRE_INTENT.json').exists()
            deadline = time.monotonic() + 2
            while RUNTIME.identity(process.pid)['state'] in ('T', 't') and time.monotonic() < deadline:
                time.sleep(.01)
            assert RUNTIME.identity(process.pid)['state'] not in ('T', 't')
        else:
            result = retire_exact(RUNTIME, row, lock_path, tmp_path, revalidate)
            process.wait(timeout=2)
            assert process.returncode == -signal.SIGTERM
            assert os.fstat(result).st_ino == lock_path.stat().st_ino == original_inode
            assert (tmp_path / 'PARENT_EXITED.json').exists()
            assert (tmp_path / 'GENUINE_PARENT_LOCK_ACQUIRED.json').exists()
    finally:
        if result is not None:
            os.close(result)
        if process.poll() is None:
            process.send_signal(signal.SIGCONT)
            process.terminate()
        process.wait(timeout=3)


def test_census_excludes_only_exact_own_watchdog_not_competing_parent(tmp_path):
    config = tmp_path / 'CONFIG.json'
    binding = tmp_path / 'BINDING.json'
    write(config, dict(root=str(tmp_path / 'life')))
    write(binding, dict(config=str(config)))
    command = [sys.executable, '-B', '-c', 'import time; time.sleep(30)',
               'parent_cpu_controller', '--binding', str(binding)]
    parent = subprocess.Popen(command, start_new_session=True)
    watcher = subprocess.Popen(command)
    try:
        time.sleep(.05)
        root = str(tmp_path / 'life')
        assert parent_census(root, os.getpid()) == sorted([parent.pid, watcher.pid])
        identity = RUNTIME.identity(watcher.pid)
        assert parent_census(root, os.getpid(), identity) == [parent.pid]
        with pytest.raises(ValueError, match='exact_own_watchdog'):
            parent_census(root, os.getpid(), dict(identity, start_ticks=identity['start_ticks'] + 1))
    finally:
        parent.terminate()
        watcher.terminate()
        parent.wait(timeout=3)
        watcher.wait(timeout=3)
