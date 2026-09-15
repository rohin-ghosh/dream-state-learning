"""Prospective high-effort parent custody, retaining all historical claims."""

import argparse
import inspect
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import FunctionType


def replace_one(source, before, after):
    if source.count(before) != 1:
        raise ValueError('exact_parent_source_site:' + before)
    return source.replace(before, after, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--wrapper', choices=('a40r', 'ovx2'), required=True)
    parser.add_argument('--era', required=True)
    parser.add_argument('--terminal', required=True)
    parser.add_argument('--after-parent', type=int, required=True)
    parser.add_argument('--ready', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime))
    from gpu import orch_r118_node3_6_grid_broker_http as http
    transport, astra = http.astra.transport, http.astra
    require = transport.require
    require(args.era in ('migration_a40r7_r119', 'learned_fork_r119')
            and args.terminal in ('R119_A40R7_CONTINUATION_TERMINAL.json',
                                   'R119_LEARNED_GRID_TERMINAL.json'), 'owned_custody_era')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_parent_only')
    config = transport.loads(args.config.read_text())
    ready = transport.loads(args.ready.read_text())
    require(ready['status'] == 'PASS' and ready['root'] == config['remote_root']
            and ready['hard_end_unix'] == config['deadline_unix']
            and ready['hard_end_unix'] <= ready['lease_end_unix'] - 21600,
            'actual_native_ready_lease_margin')
    transport.NODE5_HARD_WALL_UNIX = ready['hard_end_unix']
    require(config['remote_root'].startswith('/localhome/local-rohing/orch_r118_node3_')
            and config['family'] == 'grid', 'owned_grid_root')

    class Store(transport.Store):
        def shell(self, command, check=True):
            return subprocess.run(['bash', str(self.repository / ('gpu/' + args.wrapper + '_ssh.sh')), command],
                text=True, capture_output=True, timeout=30, check=check)

        def copy(self, source, destination):
            subprocess.run(['bash', str(self.repository / ('gpu/' + args.wrapper + '_scp.sh')),
                str(source), str(destination)], capture_output=True, timeout=30, check=True)

    strong_source = inspect.getsource(astra.existing.strong)
    strong_source = replace_one(strong_source, "config['model_reasoning_effort']", "'high'")
    strong_source = replace_one(strong_source, 'timeout_seconds=120', 'timeout_seconds=570')
    strong_source = replace_one(strong_source, 'min(120, deadline - time.time())',
                                'min(570, deadline - time.time())')
    strong_namespace = dict(astra.existing.strong.__globals__, parse_strong=astra.parse)
    exec(compile(strong_source, __file__ + ':high570', 'exec'), strong_namespace)

    def evaluate(*values, **kwargs):
        return http.evaluate(*values, **kwargs, runner=strong_namespace['strong'])

    namespace = dict(transport.serve.__globals__, Store=Store, evaluate=evaluate,
                     validate_launch=astra.authorize)
    original = FunctionType(transport.process_request.__code__, namespace, 'process_request',
                             transport.process_request.__defaults__)

    def prospective(store, config, launch, name, buffer, prompt_root, principles_path):
        identifier = name.removesuffix('.request.json')
        require(identifier.startswith('P') and identifier[1:].isdigit(), 'parent_number')
        if int(identifier[1:]) <= args.after_parent:
            return 'HISTORICAL_NO_REDISPATCH'
        root = Path(config['remote_root'])
        if store.exists(root / 'parent_received' / (identifier + '.json')):
            return 'ALREADY_DISPOSED_NO_REDISPATCH'
        return original(store, config, launch, name, buffer, prompt_root, principles_path)

    namespace['process_request'] = prospective
    source = replace_one(inspect.getsource(transport.serve),
        "store.exists(root / 'TERMINAL.json')", "store.exists(root / '" + args.terminal + "')")
    source = replace_one(source, "remote_binding = ledger / 'CONFIG.json'",
                         "remote_binding = root / '" + args.era + "' / 'BROKER_CONFIG.json'")
    exec(compile(source, __file__ + ':prospective_era', 'exec'), namespace)
    namespace['serve'](args.config, args.launch_receipt, Path('/data/home/rohing/courier/swarm/prompts'),
        args.runtime / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')


if __name__ == '__main__':
    main()
