"""Non-material admission regressions; synthetic inventories and no live operations."""

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


specification = importlib.util.spec_from_file_location(
    'r169_refresh_admission_v2', Path(__file__).with_name('refresh_admission_v2.py'))
admission = importlib.util.module_from_spec(specification)
specification.loader.exec_module(admission)


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


@pytest.fixture
def fixture(tmp_path):
    repository = tmp_path / 'repo'
    branch = repository / 'research_loop/workers/r167_legacy_parent_rollout/approved'
    branch.mkdir(parents=True)
    output = branch / 'parent'
    output.mkdir()
    config = branch / 'CONFIG.json'
    config.write_text('{}')
    cwd = tmp_path / 'frozen_source'
    (cwd / 'gpu').mkdir(parents=True)
    source = cwd / 'gpu/orch_r133_programme_parent.py'
    source.write_text('FROZEN_PARENT = True\n')
    executable = str(Path(sys.executable).resolve())
    process = dict(pid=123456, ticks='123', uid=os.getuid(), cwd=str(cwd), state='S',
        argv=[executable, '-B', '-m', admission.MODULE, '--config', str(config),
              '--repository', str(repository), '--output', str(output)])
    inventory = tmp_path / 'APPROVED.json'

    def authorize(current):
        inventory.write_text(json.dumps(dict(processes=[current])))
        return reference(inventory)

    arguments = dict(inventory_ref=authorize(process), repository=str(repository),
        python_executable=executable, expected_uid=os.getuid(), source_ref=reference(source),
        config_ref=reference(config))
    return dict(process=process, arguments=arguments, authorize=authorize, repository=repository,
                branch=branch, source=source, config=config, output=output, inventory=inventory)


def invoke(fixture):
    return admission.admit_parent(fixture['process'], **fixture['arguments'])


def test_exact_module_admits_without_mutating_input(fixture):
    original = deepcopy(fixture['process'])
    result = invoke(fixture)
    assert result['mode'] == 'module'
    assert result['status'] == 'READ_ONLY_ADMISSION_NOT_TERMINATION_OR_SERVING'
    assert fixture['process'] == original
    result['identity']['argv'].append('local_mutation')
    assert fixture['process'] == original


def test_exact_scoped_standalone_admits(fixture):
    source = fixture['branch'] / 'PARENT.py'
    source.write_text('FROZEN_PARENT = True\n')
    process = fixture['process']
    process['argv'][2:4] = [str(source)]
    fixture['arguments'].update(inventory_ref=fixture['authorize'](process), source_ref=reference(source))
    assert invoke(fixture)['mode'] == 'standalone'


@pytest.mark.parametrize('change', ['script_argument_m', 'foreign_module', 'extra_flag',
    'duplicate_output', 'reordered_options', 'missing_B', 'python_c', 'script_named_parent_argument'])
def test_unknown_argv_is_refused_even_if_inventory_lists_it(fixture, change):
    argv = fixture['process']['argv']
    if change == 'script_argument_m':
        argv.insert(2, '/tmp/nonparent.py')
    elif change == 'foreign_module':
        argv[3] = 'gpu.orch_r125_continual_native'
    elif change == 'extra_flag':
        argv.append('--once')
    elif change == 'duplicate_output':
        argv.extend(['--output', argv[-1]])
    elif change == 'reordered_options':
        argv[4:8] = argv[6:8] + argv[4:6]
    elif change == 'missing_B':
        argv.remove('-B')
    elif change == 'python_c':
        argv[2:4] = ['-c', 'pass']
    else:
        argv[2:4] = ['/tmp/nonparent.py', str(fixture['branch'] / 'PARENT.py')]
    fixture['arguments']['inventory_ref'] = fixture['authorize'](fixture['process'])
    with pytest.raises(ValueError):
        invoke(fixture)


@pytest.mark.parametrize('target', ['output', 'config', 'source', 'cwd', 'repository'])
def test_symlink_aliases_refused(fixture, tmp_path, target):
    process = fixture['process']
    aliases = dict(output=fixture['output'], config=fixture['config'], source=fixture['source'],
                   cwd=Path(process['cwd']), repository=fixture['repository'])
    alias = tmp_path / ('alias_' + target)
    alias.symlink_to(aliases[target], target_is_directory=aliases[target].is_dir())
    if target in ('output', 'config', 'repository'):
        process['argv'][process['argv'].index('--' + target) + 1] = str(alias)
    elif target == 'cwd':
        process['cwd'] = str(alias)
    else:
        process['argv'][2:4] = [str(alias)]
    fixture['arguments']['inventory_ref'] = fixture['authorize'](process)
    with pytest.raises(ValueError, match='path_alias_refused'):
        invoke(fixture)


@pytest.mark.parametrize('target', ['--config', '--output'])
def test_lexical_traversal_is_not_canonical(fixture, target):
    process = fixture['process']
    position = process['argv'].index(target) + 1
    original = Path(process['argv'][position])
    process['argv'][position] = str(original.parent / '..' / original.parent.name / original.name)
    fixture['arguments']['inventory_ref'] = fixture['authorize'](process)
    with pytest.raises(ValueError, match='canonical_absolute_path_required'):
        invoke(fixture)


def test_standalone_traversal_escape_refused(fixture):
    process = fixture['process']
    process['argv'][2:4] = [str(fixture['branch'].parent / '../foreign/PARENT.py')]
    fixture['arguments']['inventory_ref'] = fixture['authorize'](process)
    with pytest.raises(ValueError, match='canonical_absolute_path_required'):
        invoke(fixture)


def test_config_output_cannot_cross_branches(fixture):
    output = fixture['branch'].parent / 'different/parent'
    output.mkdir(parents=True)
    fixture['process']['argv'][-1] = str(output)
    fixture['arguments']['inventory_ref'] = fixture['authorize'](fixture['process'])
    with pytest.raises(ValueError, match='same_direct_legacy_branch_config_output'):
        invoke(fixture)


@pytest.mark.parametrize('field,value', [('pid', 999), ('ticks', '124'), ('uid', 999),
    ('cwd', '/tmp'), ('argv', ['other']), ('pid', True), ('uid', True)])
def test_identity_or_owner_drift_refused(fixture, field, value):
    fixture['process'][field] = value
    with pytest.raises(ValueError):
        invoke(fixture)


@pytest.mark.parametrize('state', ['T', 't', 'Z', 'X', '', None])
def test_stopped_dead_or_unknown_state_refused(fixture, state):
    fixture['process']['state'] = state
    with pytest.raises(ValueError, match='running_unstopped_parent_only'):
        invoke(fixture)


@pytest.mark.parametrize('target', ['source', 'config', 'inventory'])
def test_byte_drift_refuses(fixture, target):
    with fixture[target].open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError, match='file_hash_mismatch'):
        invoke(fixture)


def test_duplicate_inventory_pid_refused(fixture):
    fixture['inventory'].write_text(json.dumps(dict(processes=[fixture['process']] * 2)))
    fixture['arguments']['inventory_ref'] = reference(fixture['inventory'])
    with pytest.raises(ValueError, match='unique_inventory_pid'):
        invoke(fixture)


def test_duplicate_json_key_refused(fixture):
    fixture['inventory'].write_text('{"processes": [], "processes": []}')
    fixture['arguments']['inventory_ref'] = reference(fixture['inventory'])
    with pytest.raises(ValueError, match='duplicate_inventory_key'):
        invoke(fixture)


def test_source_cannot_be_replaced_with_fifo(fixture):
    fixture['source'].unlink()
    os.mkfifo(fixture['source'])
    with pytest.raises(ValueError, match='bounded_regular_file'):
        invoke(fixture)


def test_no_runtime_operation_entrypoints():
    assert not any(hasattr(admission, name) for name in ('refresh', 'serve', 'main', 'signal', 'subprocess'))
