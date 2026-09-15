"""Prospective A3 terminal-only custody overlay; original provider bytes and ledger."""

import argparse
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r108_code_parent_r118_astra_shared as shared


def terminal_path(path, root, service):
    path, root, service = Path(path), Path(root), Path(service)
    return service / 'GUARD_TERMINAL.json' if path in (root / 'TERMINAL.json', root / 'SHARED_TERMINAL.json') else path


def serve(config_path, launch_path, prompt_root, principles_path, custody_path):
    astra = shared.astra
    config = astra.transport.loads(Path(config_path).read_text())
    launch = astra.transport.loads(Path(launch_path).read_text())
    custody = astra.transport.loads(Path(custody_path).read_text())
    root, service = Path(config['remote_root']), Path(custody['service'])
    astra.transport.require(root == shared.ROOT and service.is_absolute()
        and custody['root'] == str(root), 'only_own_A3_parallel_custody')
    store = astra.transport.Store(astra.transport.ROOT)
    shared.verify_gate(store, config, launch)
    astra.transport.require(store.hash(service / 'RUNTIME.json') == custody['runtime_sha256'],
        'exact_future_runtime_custody')
    runtime = astra.transport.loads(store.shell('cat ' + shlex.quote(str(service / 'RUNTIME.json'))).stdout)
    astra.transport.require(runtime['schema'] == 'R118_CODE_PARALLEL_RUNTIME_V1' and runtime['root'] == str(root),
        'same_root_no_parent_reallocation')
    authorization = runtime['authorization']
    astra.transport.require(store.hash(authorization['path']) == authorization['sha256'], 'Main_custody_hash')
    approved = astra.transport.loads(store.shell('cat ' + shlex.quote(authorization['path'])).stdout)
    astra.transport.require(approved['status'] == 'MAIN_ALL8_COORDINATED_GO' and approved['action'] == 'LAUNCH'
        and approved['branches']['A3']['service'] == str(service), 'Main_actual_parallel_authorization')

    class Store(astra.transport.Store):
        def exists(self, path):
            return super().exists(terminal_path(path, root, service))

    namespace = dict(astra.transport.serve.__globals__, evaluate=astra.evaluate,
        validate_launch=astra.authorize, Store=Store)
    namespace['process_request'] = FunctionType(astra.transport.process_request.__code__, namespace,
        'process_request', astra.transport.process_request.__defaults__)
    FunctionType(astra.transport.serve.__code__, namespace, 'serve', astra.transport.serve.__defaults__)(
        config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'launch-receipt', 'prompt-root', 'principles', 'custody'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles, args.custody)
