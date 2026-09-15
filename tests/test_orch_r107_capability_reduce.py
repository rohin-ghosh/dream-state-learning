import json

import pytest

from gpu import orch_r107_capability_reduce as reducer


def captured(root, name, process, task):
    folder = root / name
    folder.mkdir(exist_ok=True)
    (folder / 'LOADED.json').write_text(json.dumps(dict(process=process)))
    path = folder / f'{task}.json'
    path.write_text(json.dumps(dict(task_id=task)))
    return dict(path=str(path), sha256=reducer.run.sha(path))


def test_unrepaired_readout_has_no_invented_retained_cells(tmp_path):
    sources = [captured(tmp_path, 'fresh', ['boot', 10, 20], 'task0')]
    report = reducer.process_provenance(sources, 0)
    assert report['retained_cells'] == 0
    assert report['native_process_count'] == 1
    assert report['cross_process_task_ids'] == []
    assert 'none' in report['process_boundary_disclosure']
    assert 'CODE01' not in report['process_boundary_disclosure']


def test_crossing_is_derived_from_bound_call_and_loaded_receipts(tmp_path):
    sources = [captured(tmp_path, 'old', ['boot', 10, 20], 'task0'),
        captured(tmp_path, 'new', ['boot', 11, 30], 'task0'),
        captured(tmp_path, 'new', ['boot', 11, 30], 'task1')]
    report = reducer.process_provenance(sources, 1)
    assert report['cross_process_task_ids'] == ['task0']
    assert report['native_process_count'] == 2
    assert report['retained_cells'] == 1


def test_changed_call_receipt_rejected(tmp_path):
    item = captured(tmp_path, 'fresh', ['boot', 10, 20], 'task0')
    item['sha256'] = '0' * 64
    with pytest.raises(AssertionError):
        reducer.process_provenance([item], 0)
