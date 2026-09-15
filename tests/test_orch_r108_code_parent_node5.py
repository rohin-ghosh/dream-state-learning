import json
import subprocess
import sys

import pytest

from gpu import orch_r108_code_parent_node5 as node5


@pytest.mark.parametrize('index', [4, 5])
def test_node5_fresh_caps_cohort_and_visibility_in_isolated_process(index):
    script = f'''
import json
from gpu import orch_r108_code_parent_node5 as node5
root, arm = node5.configure({index})
policy = node5.policy
rows = policy.tasks(arm)
config = policy.allocation(arm)
schedule = policy.schedule(rows, arm)
bound = node5.run.lifetime(config, node5.LEASE_END)
assert len(rows) == 600 and len(set(row['prompt_sha256'] for row in rows)) == 600
assert all(row['task_id'].startswith('R110_NODE5_CODE_') for row in rows)
assert set(row['prompt_sha256'] for row in rows).isdisjoint(row['prompt_sha256'] for row in node5.SOURCE_TASKS(arm))
assert config['uuid'] == node5.DEVICES[{index}] and config['wrapper'] == 'ovx3'
assert bound['started_unix'] == node5.START and bound['lease_end_unix'] == node5.LEASE_END
assert bound['hard_deadline_unix'] == 1789491720 and bound['native_deadline_unix'] == 1789491600
assert bound['hard_deadline_unix'] <= node5.LEASE_END - 21600
assert sum(row['kind'] == 'NATIVE' for row in schedule) == config['native_cap']
assert sum(row['kind'] == 'PARENT' for row in schedule) == config['parent_cap']
task = rows[0]
record = dict(response=dict(raw='My own observation', terminal=True, truncated=False))
payload = policy.parent_payload(arm, task, 2, [record, record], '', [])
assert policy.validate_parent_payload(payload) == payload
assert 'expected' not in json.dumps(payload) and 'reference_expression' not in json.dumps(payload)
other = policy.tasks(node5.ARMS[5 if {index} == 4 else 4])
assert [row['prompt_sha256'] for row in rows] == [row['prompt_sha256'] for row in other]
assert len(node5.read.__name__) > 0
print(json.dumps(dict(native=config['native_cap'], parent=config['parent_cap'], fresh_tasks=len(rows))))
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)['fresh_tasks'] == 600


@pytest.mark.parametrize('index', [0, 1, 2, 3, 6, 7, True])
def test_node5_exact_owned_slots_only(index):
    with pytest.raises(ValueError):
        node5.root_for(index)


def test_privileged_scanner_subprocess_uses_node5_binding(monkeypatch, tmp_path):
    from types import SimpleNamespace
    config = dict(index=4, uuid=node5.DEVICES[4])
    report = dict(gpu=config, host_sha256=node5.HOST_SHA, scanner_euid=0, device_minor=4, clear=False)
    calls = []
    monkeypatch.setattr(node5.policy, 'allocation', lambda arm: config)
    monkeypatch.setattr(node5.os, 'geteuid', lambda: 2524)
    monkeypatch.setattr(node5.subprocess, 'run', lambda args, **kwargs: calls.append(args) or SimpleNamespace(stdout=json.dumps(report)))
    assert node5.scan(tmp_path, 'node5_segment') == report
    assert 'gpu.orch_r108_code_parent_node5' in calls[0]
    assert calls[0][-3:] == ['scan', '--index', '4']
    assert 'gpu.orch_r108_code_parent_r109_scan' not in calls[0]
