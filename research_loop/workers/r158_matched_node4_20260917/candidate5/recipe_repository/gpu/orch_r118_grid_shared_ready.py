"""Publish native GRID READY metadata without common initialization or GPU work.

Only SHARED_CLIENT_READY.json is written in each existing life root. Original
CONFIG, ledgers, live broker/life sources, CARRY and terminal receipts are untouched.
The CPU receipt must bind the entire Python closure and executable help smoke test.
"""

import argparse
import ast
from pathlib import Path
import time

from gpu import orch_r118_grid_shared_run as run


shared = run.shared
require = shared.require
COMMON_ROOT = run.COMMON_ROOT
SOURCE_FILES = ('gpu/orch_r118_grid_shared_run.py', 'gpu/orch_r118_grid_shared_ready.py',
                'gpu/orch_r116_grid_shared_client.py', 'gpu/orch_r118_f4_wait600.py',
                'gpu/orch_r116_shared_learner.py', 'gpu/orch_r111_route_shared.py')
PREDECESSOR_SOURCE = Path('/localhome/local-rohing/orch_r115_grid_source_20260915_v1')


def source_closure(source, entries):
    """Static repository import closure, including lazy imports and package files."""
    source = Path(source).resolve(strict=True)
    pending = [Path(entry) for entry in entries]
    found = {}

    def add_module(module):
        if not module:
            return
        relative = Path(*module.split('.'))
        for candidate in (relative.with_suffix('.py'), relative / '__init__.py',
                          Path('gpu') / relative.with_suffix('.py'),
                          Path('organism_v6') / relative.with_suffix('.py')):
            if (source / candidate).is_file():
                pending.append(candidate)
                break

    while pending:
        relative = pending.pop()
        require(not relative.is_absolute() and '..' not in relative.parts, 'local_source_paths_only')
        name = str(relative)
        if name in found:
            continue
        path = source / relative
        require(path.is_file() and path.resolve() == path, 'no_missing_or_symlinked_source:' + name)
        found[name] = shared.sha(path)
        for parent in relative.parents:
            package = parent / '__init__.py'
            if str(parent) != '.' and (source / package).is_file():
                pending.append(package)
        tree = ast.parse(path.read_text(), filename=name)
        package = list(relative.parent.parts)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add_module(alias.name)
            elif isinstance(node, ast.ImportFrom):
                prefix = package[:len(package) - node.level + 1] if node.level else []
                prefix += node.module.split('.') if node.module else []
                module = '.'.join(prefix)
                add_module(module)
                for alias in node.names:
                    if alias.name != '*':
                        add_module('.'.join(prefix + [alias.name]))
            elif isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
                called = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', None)
                if called in ('import_module', '__import__') and isinstance(node.args[0].value, str):
                    add_module(node.args[0].value)
    return dict(sorted(found.items()))


def verify_closure(successor_source, tests):
    source = Path(successor_source).resolve(strict=True)
    reference = tests['source_closure']
    path = Path(reference['path']).resolve(strict=True)
    require(path.parent == source and shared.sha(path) == reference['sha256'], 'bound_full_source_manifest')
    manifest = shared.read(path)
    require(manifest['schema'] == 'R118_GRID_SHARED_SOURCE_CLOSURE_V1' and manifest['root'] == str(source), 'source_manifest_root')
    actual = {str(path.relative_to(source)): shared.sha(path) for path in source.rglob('*.py') if path.is_file()}
    require(actual == manifest['files'] and all((source / name).resolve() == source / name for name in actual),
            'complete_python_closure_unchanged')
    computed = source_closure(source, manifest['entries'])
    require(computed == actual, 'complete_static_import_closure')
    sources = {name: shared.sha(source / name) for name in SOURCE_FILES}
    require(tests['source_files'] == sources and tests['passed'] is True and tests['native_cpu'] is True
            and tests['cuda_initialized'] is False and tests['tests_failed'] == 0
            and tests['tests_skipped'] == 0 and tests['tests_run'] > 0, 'bound_native_CPU_tests')
    executable = tests['entrypoint']
    require(executable['module'] == run.MODULE and executable['help_exit_code'] == 0
            and executable['sha256'] == sources['gpu/orch_r118_grid_shared_run.py'], 'actual_executable_help_test')
    return dict(path=str(path), sha256=reference['sha256'], files=len(actual))


def verify_predecessor(root, config, source):
    root, source = Path(root).resolve(strict=True), Path(source).resolve(strict=True)
    manifest_path = source / 'R115_SOURCE_SHA256.json'
    require(shared.sha(manifest_path) == config['source_manifest_sha256'], 'original_source_manifest_binding')
    for name, expected in shared.read(manifest_path).items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and (source / name).resolve() == source / name and shared.sha(source / name) == expected,
                'original_source_unchanged:' + name)
    for name, expected in config['inputs'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and shared.sha(root / name) == expected, 'original_input_unchanged:' + name)
    return dict(path=str(source), manifest_sha256=config['source_manifest_sha256'])


def publish(root, successor_source, tests_receipt, *, predecessor_source=PREDECESSOR_SOURCE):
    root, source = Path(root).resolve(strict=True), Path(successor_source).resolve(strict=True)
    tests_receipt = Path(tests_receipt).resolve(strict=True)
    require(not (root / 'SHARED_CLIENT_READY.json').exists(), 'readiness_already_published_no_overwrite')
    config = shared.read(root / 'CONFIG.json')
    require(config['root'] == str(root), 'exact_original_root')
    branch = run.branch_for(config)
    require(config['base_sha256'] == run.grid.policy.game.BASE_SHA, 'original_base')
    bounds = run.inherited_bounds(config)
    predecessor = verify_predecessor(root, config, predecessor_source)
    tests = shared.read(tests_receipt)
    closure = verify_closure(source, tests)
    train = shared.read(root / 'TRAIN.json')
    train_ids = [task['id'] for task in train]
    excluded = [task['id'] for split in ('DEV', 'FINAL') for task in shared.read(root / (split + '.json'))]
    legacy = shared.read(root / 'LEGACY_READOUT.json')
    excluded += ['OLD-' + item['event'] for item in legacy['old_bank']]
    excluded += ['AUDIT-' + case['case_sha256'] for case in legacy['held']['cases']]
    require(len(train_ids) == len(set(train_ids)) == 16 and all(task['split'] == 'TRAIN' for task in train), 'same_sixteen_train_tasks')
    require(not set(train_ids).intersection(excluded), 'all_held_excluded')
    receipt = dict(schema='R116_SHARED_CLIENT_READY_V1', branch=branch, root=str(root),
        train_ids=train_ids, excluded_ids=sorted(set(excluded)), successor_source=str(source),
        source_files={name: shared.sha(source / name) for name in SOURCE_FILES}, source_closure=closure,
        predecessor_plan_sha256=shared.sha(root / 'CONFIG.json'), predecessor_plan_filename='CONFIG.json',
        predecessor_source=predecessor, inherited_bounds=bounds, common_root=COMMON_ROOT,
        tests_receipt=dict(path=str(tests_receipt), sha256=shared.sha(tests_receipt)), command_module=run.MODULE,
        executable=dict(module=run.MODULE, source=str(source / 'gpu/orch_r118_grid_shared_run.py'),
            sha256=shared.sha(source / 'gpu/orch_r118_grid_shared_run.py')),
        ready_for_initialization=True, active_shared_client=False, optimizer_owner='F1', local_optimizer_steps=0,
        original_counters_preserved=True, parent_wait_seconds=bounds['parent_wait_seconds'],
        native_capture_fields=['shared_generation', 'shared_checkpoint_sha256', 'task_id'],
        training_phases=sorted(run.client.TRAIN_PHASES), readout_open_excluded=True,
        activation_sidecar='SHARED_ACTIVATION.json', activation_schema='R118_GRID_SHARED_ACTIVATION_V1',
        activation_fields=['schema', 'all_eight_ready_and_safe', 'ready_sha256', 'predecessor_plan_sha256',
            'inherited_bounds', 'shared_learner', 'boundary', 'predecessor_identities'],
        activation_binding_fields=['branch', 'root', 'config_sha256', 'adoption_path', 'adoption_sha256'],
        boundary_command=f'{run.grid.PYTHON} -B -m {run.MODULE} boundary --root {root} --complete {root}/cycles/NNNN/CYCLE_COMPLETE.json',
        activation_command=f'CUDA_VISIBLE_DEVICES= PYTHONPATH={source}:{source}/gpu {run.grid.PYTHON} -B -m {run.MODULE} guard --root {root}',
        boundary_contract='Main retires current native AND guard at a complete two-episode+DEV cycle; all reservations terminal, CARRY and ledger byte-identical, next_cycle unchanged. Boundary command sends no signals.',
        boundary_reference_fields=['path', 'sha256'],
        predecessor_identity_fields=['pid', 'uid', 'start_ticks', 'boot_id'],
        transition='ALL_EIGHT_READY_AND_SAFE_COMMON_BOUNDARY_NO_HOTPATCH',
        broker_transition_note='Main/Hubble/Laplace must explicitly bind successor broker terminal to SHARED_TERMINAL.json; preserve old TERMINAL.json and F4 R118_WAIT600_TERMINAL.json.',
        common_configuration_required_for_readiness=False, observed_unix=time.time())
    shared.write(root / 'SHARED_CLIENT_READY.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--successor-source', type=Path, required=True)
    parser.add_argument('--tests-receipt', type=Path, required=True)
    parser.add_argument('--predecessor-source', type=Path, default=PREDECESSOR_SOURCE)
    args = parser.parse_args()
    result = publish(args.root, args.successor_source, args.tests_receipt, predecessor_source=args.predecessor_source)
    print(result['branch'], str(args.root / 'SHARED_CLIENT_READY.json'), shared.sha(args.root / 'SHARED_CLIENT_READY.json'))


if __name__ == '__main__':
    main()
