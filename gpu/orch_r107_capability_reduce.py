"""Offline reduction of immutable R107 cells, including disclosed repair joins."""

import argparse
import json
from pathlib import Path

from gpu import orch_r107_capability_run as run
from organism_v6 import orch_r107_capability as policy


def reduce(root):
    plan = run.read(root / 'PLAN.json')
    output = root / 'readout'
    complete = run.read(output / 'COMPLETE.json')
    after = run.read(output / 'AFTER.json')
    loaded = run.read(output / 'LOADED.json')
    assert complete['status'] == 'COMPLETE'
    assert complete['total_completed_cells'] == 64
    assert after['unchanged'] is True and after['frozen_base_verified'] is True
    assert after['process'] == loaded['process'] == complete['process']
    assert after['observed'] == loaded['observed'] == plan['adapter']
    assert after['training_updates'] == complete['training_updates'] == 0
    assert not after['parent_present'] and not complete['parent_present']
    tasks = policy.tasks()
    assert policy.digest(tasks) == plan['suite_sha256'] == complete['suite_sha256']
    sources = [dict(path=str(path), sha256=run.sha(path)) for path in sorted(output.glob('CALL_*.json'))]
    sources.extend(plan.get('retained_calls', []))
    records = []
    for item in sources:
        path = Path(item['path'])
        assert run.sha(path) == item['sha256']
        call = run.read(path)
        assert call['status'] == 'COMPLETE'
        task = tasks[call['position']]
        assert task['id'] == call['task_id'] and call['messages'] == policy.messages(task)
        arm = {'LORA_ON': 'ON', 'LORA_OFF': 'OFF'}[call['condition']]
        response = dict(call['response'], max_new_tokens=call['max_new_tokens'])
        records.append(policy.capture(task, arm, response,
            checkpoint_sha256=plan['adapter']['state_sha256'], base_sha256=plan['base_sha256'],
            lora_enabled=arm == 'ON'))
    result = policy.reduce_paired(records, checkpoint_sha256=plan['adapter']['state_sha256'],
        base_sha256=plan['base_sha256'], max_new_tokens=plan['max_new_tokens'])
    assert result['all_pairs_complete'] and result['recorded_cells'] == 64
    result.update(native_calls=0, parent_calls=0, raw_text_included=False,
        process_boundary_disclosure='Three cells retained from V2; CODE01 ON/OFF pair crosses fresh processes.',
        actual_inference_cells=64, aggregate_reserved_cap=plan.get('aggregate_reserved_cap', 64),
        source_receipts=sources, plan_sha256=run.sha(root / 'PLAN.json'),
        complete_sha256=run.sha(output / 'COMPLETE.json'), after_sha256=run.sha(output / 'AFTER.json'),
        loaded_sha256=run.sha(output / 'LOADED.json'), reducer_sha256=run.sha(__file__),
        adapter_files_verified=run.bridge.AdapterIdentity.from_document(plan['adapter']).verify().document())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = reduce(options.root)
    with options.output.open('x') as destination:
        json.dump(result, destination, indent=2, sort_keys=True)
        destination.write('\n')
    print(json.dumps(dict(overall=result['overall'], families=result['families']), sort_keys=True))
