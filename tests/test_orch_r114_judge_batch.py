import json

import pytest

from gpu import orch_r114_judge_batch as batch


def fixture(tmp_path):
    tasks = [dict(id=f'private_task_{index}', question=f'Public question {index}', gold='SECRET')
        for index in range(8)]
    batch.write(tmp_path / 'COHORT.json', dict(held=[tasks]))
    directory = tmp_path / 'cycle1/readout'
    batch.write(directory / 'COMPLETE.json', dict(status='COMPLETE', fresh_process=True, parent_calls=0))
    for index, task in enumerate(tasks):
        batch.write(directory / f'CALL_{index:03d}.json', dict(task_id=task['id'], purpose='held',
            response=dict(raw='Observed child text.'), condition='PRIVATE', input_adapter='PRIVATE'))
    return directory


def test_blind_requests_keep_provenance_separate(tmp_path):
    fixture(tmp_path)
    result = batch.select_documents(tmp_path, [1])
    assert len(result) == 8
    for row in result:
        text = json.dumps(row['request'])
        assert 'SECRET' not in text and 'PRIVATE' not in text and 'private_task' not in text
        assert 'source_sha256' in row['private_provenance']


def test_cannot_annotate_partial_readout(tmp_path):
    directory = fixture(tmp_path)
    (directory / 'COMPLETE.json').write_text(json.dumps(dict(status='FAILED', fresh_process=True, parent_calls=0)))
    with pytest.raises(ValueError, match='completed_parent_free_readout'):
        batch.select_documents(tmp_path, [1])


def test_missing_child_call_is_not_silently_omitted(tmp_path):
    directory = fixture(tmp_path)
    (directory / 'CALL_000.json').unlink()
    with pytest.raises(ValueError, match='eight_distinct_held_calls'):
        batch.select_documents(tmp_path, [1])


@pytest.mark.parametrize('raw', ['not json', '{}', '[]', 'null', '{"status":"COMPLETE"}'])
def test_bad_annotation_is_unresolved_not_negative(raw):
    result = batch.interpret(dict(kind='held', task_text='task', child_text='child'), raw, False)
    assert result['status'] == 'UNRESOLVED' and result['shifts'] is None


def test_output_cap_is_unresolved():
    result = batch.interpret(dict(kind='held', task_text='task', child_text='child'), '{}', True)
    assert result['reason'] == 'judge_output_cap'


def test_no_overwrite_of_evidence(tmp_path):
    batch.write(tmp_path / 'receipt.json', dict(status='old'))
    with pytest.raises(FileExistsError):
        batch.write(tmp_path / 'receipt.json', dict(status='new'))


def test_judge_only_owns_reserved_gpu4():
    scanner = batch.bind_scanner()
    assert scanner.minor.pinned.policy.DEVICES == {4: batch.UUID}
    with pytest.raises(ValueError, match='only_allocated_gpu4'):
        scanner.minor.pinned.policy.allocation(7)
