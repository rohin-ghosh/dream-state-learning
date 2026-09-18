import ast
import copy
import json
import signal
from pathlib import Path
from unittest.mock import patch

import pytest

import legacy_takeover as legacy
import node4_rollout as rollout
from test_legacy_takeover import FakeOperations


def binding(pid=1399872):
    coverage = json.loads(legacy.read(rollout.COVERAGE))
    row = next(item for item in coverage['still_original_live_parented']
        if item['parent']['identity']['pid'] == pid)
    parent = row['parent']
    return dict(branch=parent['fields']['branch'], node='a40r', root=parent['fields']['root'],
        parent=parent['identity'], native=row['native'], original_config=parent['config'],
        old_output=parent['output'], entrypoint=rollout.SLOTS[parent['fields']['branch']][0])


@pytest.mark.parametrize('pid', [1399872, 716608, 3603888])
def test_exact_three_scope(pid):
    expected = binding(pid)
    rollout.verify_identity(expected, dict(expected['parent'], state='S'))


@pytest.mark.parametrize('damage', ['branch', 'node', 'root', 'entrypoint', 'native', 'parent',
    'start_ticks', 'uid', 'argv', 'cwd', 'output', 'config', 'zombie'])
def test_reject_identity_root_runner_drift(damage):
    expected = copy.deepcopy(binding())
    observed = copy.deepcopy(expected['parent'])
    if damage in ('branch', 'node', 'root', 'entrypoint'):
        expected[damage] = 'other'
    elif damage in ('native', 'parent'):
        expected[damage]['pid'] += 1
    elif damage in ('start_ticks', 'uid', 'argv', 'cwd'):
        observed[damage] = 'different'
    elif damage == 'output':
        expected['old_output'] = '/other'
    elif damage == 'config':
        expected['original_config']['path'] = '/other'
    else:
        observed['state'] = 'Z'
    with pytest.raises(ValueError):
        rollout.verify_identity(expected, observed)


@pytest.mark.parametrize('failure', ['busy', 'ledger', 'pin', 'expiry'])
def test_pretermination_failure_continues_exact_parent(failure):
    expected = binding()
    operations = FakeOperations()
    operations.observed = dict(expected['parent'], state='S')
    operations.busy = failure == 'busy'
    with pytest.raises(ValueError):
        with rollout.quiesce(expected, operations):
            raise ValueError(failure)
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert operations.closed


def test_original_custody_implementation_preserved():
    def functions(path):
        return {node.name: node for node in ast.parse(Path(path).read_text()).body
            if isinstance(node, ast.FunctionDef)}
    original = functions(legacy.__file__)
    adapted = functions(rollout.__file__)
    assert ast.dump(original['quiesce']) == ast.dump(adapted['quiesce'])
    source = ast.unparse(original['execute'])
    source = source.replace("'-m', 'gpu.orch_r133_programme_parent'", "'-m', binding['entrypoint']")
    assert ast.dump(ast.parse(source).body[0]) == ast.dump(adapted['execute'])


def test_wrong_native_never_admitted():
    expected = binding()
    census = dict(hostname='[REDACTED_HOST]', processes=[])
    with patch.object(rollout.subprocess, 'run') as run:
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps(census)
        with pytest.raises(ValueError, match='exact_live_native_required'):
            rollout.native_check(expected)


@pytest.mark.parametrize('pid', [1399872, 3603888])
def test_actual_original_runner_startup_without_provider(tmp_path, pid):
    expected = binding(pid)
    original = json.loads(legacy.bound(expected['original_config']))
    expected.update(python='/usr/bin/python3.12', successor_cwd=expected['parent']['cwd'])
    source = Path(expected['successor_cwd']) / 'gpu/orch_r133_programme_parent.py'
    previous = legacy.ledger(expected['old_output'], original, legacy.ref(source)['sha256'])
    principles = legacy.INDEX.parent / 'KERNEL0_RESUMED_SPARSE2_1045188/PRINCIPLES.md'
    candidate = dict(original, principles_path=str(principles), principles_sha256=legacy.ref(principles)['sha256'])
    proposed = legacy.successor_config(original, candidate, previous, expected['old_output'])
    path = tmp_path / 'CONFIG.json'
    path.write_text(json.dumps(proposed))
    result = rollout.cpu_preflight(expected, path)
    assert result['cursor'] == previous['reserved']
    assert result['actual_startup'] and result['provider_calls'] == result['publications'] == 0
