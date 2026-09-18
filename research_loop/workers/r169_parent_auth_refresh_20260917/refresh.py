"""Parent-only credential refresh with immutable attempts and reserved cursors."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import tomllib


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MODEL = 'openai/openai/gpt-6-astra'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    root = Path('/proc') / str(pid)
    before = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    argv = (root / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    after = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19], 'stable_process_identity')
    return dict(pid=pid, ticks=after[19], argv=argv, cwd=str((root / 'cwd').resolve()),
                uid=root.stat().st_uid, state=after[0])


def same_process(before, after):
    return all(before[key] == after[key] for key in ('pid', 'ticks', 'argv', 'cwd', 'uid'))


def source_for(process):
    argv = process['argv']
    if '-m' in argv:
        require(argv[argv.index('-m') + 1] == 'gpu.orch_r133_programme_parent', 'standard_parent_only')
        return Path(process['cwd']) / 'gpu/orch_r133_programme_parent.py'
    paths = [Path(value) for value in argv if value.endswith('/PARENT.py')]
    require(len(paths) == 1 and paths[0].is_relative_to(REPO / 'research_loop/workers/r167_legacy_parent_rollout'),
            'known_fixed_cursor_parent_only')
    return paths[0]


def patched_code(raw, filename, cursor):
    require(type(cursor) is int and cursor >= 0, 'nonnegative_reserved_cursor')
    tree = ast.parse(raw, filename)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve']
    require(len(functions) == 1, 'one_original_serve')
    assignments = [node for node in functions[0].body if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == 'last_count']
    require(len(assignments) == 1, 'one_initial_cursor_only')
    assignments[0].value = ast.Call(func=ast.Name(id='max', ctx=ast.Load()),
        args=[assignments[0].value, ast.Constant(cursor)], keywords=[])
    return compile(ast.fix_missing_locations(tree), filename, 'exec')


def settled(output, config):
    clock = 'request_count' if config.get('schedule_on') == 'request' else 'response_count'
    cursor = config.get('start_after_' + clock, 0)
    statuses, pending, pins = {}, [], {}
    started = json.loads((output / 'STARTED.json').read_text())
    require(started['branch'] == config['branch'] and started['programme'] == config['programme'], 'same_branch')
    directories = sorted(output.glob('parent_*'))
    require(len(directories) <= 10000, 'bounded_attempt_ledger')
    for directory in directories:
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt_directory')
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        require(source_path.exists() and result_path.exists(), 'unsettled_attempt_wait')
        require(source_path.stat().st_size <= 16 * 1024 * 1024 and result_path.stat().st_size <= 1024 * 1024,
                'bounded_attempt_metadata')
        source, result = json.loads(source_path.read_text()), json.loads(result_path.read_text())
        require(result['branch'] == config['branch'] and result['source_head_sha256'] == source['head_sha256']
                and result['source_response_count'] == source['response_count'], 'bound_result_source')
        require(result['status'] in ('MISSING', 'PUBLISHED', 'SILENT'), 'known_terminal_status')
        require(type(source[clock]) is int and source[clock] >= cursor, 'monotonic_reserved_cursor')
        cursor = source[clock]
        statuses[result['status']] = statuses.get(result['status'], 0) + 1
        if result['status'] == 'PUBLISHED' and not (directory / 'DELIVERED.json').exists():
            pending.append(result['inbox_publication']['id'])
        pins[str(source_path)] = sha(source_path)
        pins[str(result_path)] = sha(result_path)
    return dict(clock=clock, cursor=cursor, statuses=statuses, pending_inbox_ids=pending, pins=pins)


def load_parent(binding):
    require(sha(binding['source_copy']) == binding['source_sha256'], 'frozen_parent_source')
    require(sha(binding['provider_copy']) == binding['provider_sha256'], 'frozen_provider_source')
    require(sha(binding['config']) == binding['config_sha256'], 'unchanged_parent_config')
    require(sha(__file__) == binding['operator_sha256'], 'frozen_operator')
    provider = dict(__name__='r169_provider', __file__=binding['provider_copy'])
    exec(compile(Path(binding['provider_copy']).read_bytes(), binding['provider_copy'], 'exec'), provider)
    require(provider['STRONG'] == MODEL, 'canonical_model_route')
    parent = dict(__name__='r169_parent', __file__=binding['original_source'])
    exec(patched_code(Path(binding['source_copy']).read_bytes(), binding['original_source'], binding['cursor']), parent)
    parent['strong'], parent['STRONG'] = provider['strong'], provider['STRONG']
    parent['validate'](json.loads(Path(binding['config']).read_text()))
    return parent


def refresh(process):
    output = HERE / ('parent_' + str(process['pid']))
    descriptor, stopped, terminated = None, False, False
    try:
        output.mkdir(mode=0o700)
        require(process['uid'] == os.getuid() and process['state'] not in ('T', 't', 'Z'), 'owned_running_parent')
        argv = process['argv']
        original_output = Path(argv[argv.index('--output') + 1])
        require(original_output.is_relative_to(REPO / 'research_loop/workers/r167_legacy_parent_rollout'), 'legacy_scope')
        config_path = Path(argv[argv.index('--config') + 1])
        config = json.loads(config_path.read_text())
        require(time.time() < config['hard_end_unix'], 'existing_wall_not_extended')
        source_path = source_for(process)
        source = source_path.read_bytes()
        provider_path = REPO / 'gpu/orch_route_parent_campaign_providers.py'
        (output / 'SOURCE.py').write_bytes(source)
        (output / 'PROVIDER.py').write_bytes(provider_path.read_bytes())
        descriptor = os.pidfd_open(process['pid'])
        deadline = time.monotonic() + 150
        while True:
            require(same_process(process, identity(process['pid'])), 'exact_identity_before_pause')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            try:
                for attempt in range(100):
                    if identity(process['pid'])['state'] in ('T', 't'):
                        break
                    time.sleep(.01)
                require(identity(process['pid'])['state'] in ('T', 't'), 'confirmed_parent_pause')
                children = [part for path in (Path('/proc') / str(process['pid']) / 'task').glob('*/children')
                            for part in path.read_text().split()]
                require(not children, 'parent_transport_still_running')
                ledger = settled(original_output, config)
                break
            except (ValueError, FileNotFoundError):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                require(time.monotonic() < deadline, 'no_quiet_settled_boundary_no_restart')
                time.sleep(.5)
        binding = dict(original=process, original_source=str(source_path), source_copy=str(output/'SOURCE.py'),
            source_sha256=sha(output/'SOURCE.py'), provider_copy=str(output/'PROVIDER.py'),
            provider_sha256=sha(output/'PROVIDER.py'), config=str(config_path), config_sha256=sha(config_path),
            operator_sha256=sha(__file__), cursor=ledger['cursor'], output=str(output/'parent'),
            branch=config['branch'], previous_output=str(original_output))
        write(output / 'BINDING.json', binding)
        write(output / 'PREDECESSOR_LEDGER.json', ledger)
        command = [argv[0], '-B', str(Path(__file__).resolve()), 'serve', '--binding', str(output/'BINDING.json')]
        environment = dict(os.environ, PYTHONPATH=process['cwd'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        preflight = subprocess.run(command + ['--preflight'], env=environment, cwd=process['cwd'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        require(preflight.returncode == 0, 'receiving_CPU_preflight_failed')
        write(output / 'CPU_PREFLIGHT.json', dict(status='PASS', source_sha256=binding['source_sha256'],
            provider_sha256=binding['provider_sha256'], cursor=ledger['cursor'], model=MODEL))
        require(same_process(process, identity(process['pid'])), 'exact_identity_before_termination')
        require(settled(original_output, config) == ledger, 'ledger_unchanged_while_paused')
        write(output / 'TERMINATION_ONCE.json', dict(pid=process['pid'], ticks=process['ticks'], utc_unix=time.time()))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        stopped = False
        terminated = True
        require(bool(select.select([descriptor], [], [], 20)[0]), 'parent_exit_confirmed_before_successor')
        with (output / 'PARENT.log').open('xb') as log:
            successor = subprocess.Popen(command, env=environment, cwd=process['cwd'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(output / 'SPAWNED.json', dict(pid=successor.pid, command=command, utc_unix=time.time(),
            new_credential_inherited=True, pending_inbox_ids=ledger['pending_inbox_ids'], no_old_request_replay=True))
        return dict(branch=config['branch'], old_pid=process['pid'], new_pid=successor.pid, status='SPAWNED')
    except Exception as error:
        result = dict(old_pid=process['pid'], status='REFUSED', error_type=type(error).__name__,
                      reason=str(error) if isinstance(error, ValueError) else 'operational_failure', terminated=terminated)
        if output.exists() and not (output / 'REFUSED.json').exists():
            write(output / 'REFUSED.json', result)
        return result
    finally:
        if descriptor is not None:
            if stopped:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('discover', 'execute', 'serve'))
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    if args.action == 'serve':
        binding = json.loads(args.binding.read_text())
        parent = load_parent(binding)
        if not args.preflight:
            parent['serve'](Path(binding['config']), REPO, Path(binding['output']))
        return
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'credential_environment_required')
    config = tomllib.loads((Path.home()/'.codex/nvidia-astra.config.toml').read_text())
    require(config['model'] == MODEL, 'current_canonical_provider_configuration')
    if args.action == 'discover':
        processes = []
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():
                continue
            try:
                process = identity(int(path.name))
                argv = process['argv']
                if process['uid'] != os.getuid() or '--output' not in argv:
                    continue
                if not Path(argv[argv.index('--output')+1]).is_relative_to(REPO/'research_loop/workers/r167_legacy_parent_rollout'):
                    continue
                source_for(process)
                processes.append(process)
            except (OSError, ValueError):
                continue
        write(HERE/'DISCOVERED.json', dict(processes=processes, utc_unix=time.time()))
        print(json.dumps(dict(scoped_parents=len(processes))))
    else:
        processes = json.loads((HERE/'DISCOVERED.json').read_text())['processes']
        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(refresh, processes))
        write(HERE/'RESULTS.json', dict(results=results, utc_unix=time.time()))
        print(json.dumps(results))


if __name__ == '__main__':
    main()
