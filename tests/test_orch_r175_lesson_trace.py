import json

import pytest

from gpu import orch_r175_lesson_trace as trace


def fixture(tmp_path):
    directory = tmp_path / 'stream/records'
    directory.mkdir(parents=True)
    records = []

    def append(kind, document):
        record = dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32, index=len(records),
                      kind=kind, document=document, previous_sha256=records[-1]['sha256'] if records else '0' * 64)
        record['sha256'] = trace.digest(record)
        (directory / f'{len(records):020d}.json').write_text(json.dumps(record))
        records.append(record)
        return record

    append('SLEEP_COMPLETE', dict(cycle=40, checkpoint={'adapter_path': '/kept/checkpoint'}))
    append('INBOX', dict(message=dict(id='rohin', split='TRAIN', actor='parent', speaker='Rohin', text='Choose a step.'),
                         source_sha256='f' * 64))
    return records, append


def request(visible):
    messages = [dict(role='system', content='system'), dict(role='user', content='birth')]
    if visible:
        messages.append(dict(role='user', content='Rohin: Choose a step.'))
    return dict(split='TRAIN', segment=123, messages=messages, render_receipt={'all_history_tokens_masked': True})


def run(tmp_path, records):
    return trace.trace(tmp_path, 'a' * 32, 0, records[0]['sha256'], 'rohin')


def test_publication_not_exposure(tmp_path):
    records, append = fixture(tmp_path)
    append('REQUEST', request(False))
    result = run(tmp_path, records)
    assert result['first_rendered_guidance'] is None
    assert result['status'] == 'AWAITING_GUIDANCE_EXPOSURE'


def test_bound_commit_only_and_four_responses_then_sleep(tmp_path):
    records, append = fixture(tmp_path)
    for segment in range(4):
        document = dict(request(True), segment=segment)
        append('REQUEST', document)
        response = dict(request_sha256=trace.digest(document), finished_unix=1000 + segment,
                        response=dict(raw='No result obtained; next I will test.', token_ids=[1, 2]))
        append('RESPONSE', response)
        append('COMMITTED', dict(source_sha256=trace.digest(response), segment=segment))
    append('SLEEP_COMPLETE', dict(cycle=42, checkpoint={'adapter_path': '/kept/new'}))
    result = run(tmp_path, records)
    assert result['guided_committed_responses'] == 4
    assert result['guided_generated_tokens'] == 8
    assert result['first_eligible_completed_sleep']['cycle'] == 42
    assert not result['success_claim']


def test_rejects_tamper_and_wrong_anchor(tmp_path):
    records, append = fixture(tmp_path)
    with pytest.raises(ValueError, match='external_anchor_hash'):
        trace.trace(tmp_path, 'a' * 32, 0, 'f' * 64, 'rohin')
    path = tmp_path / 'stream/records/00000000000000000001.json'
    altered = json.loads(path.read_text())
    altered['document']['message']['text'] = 'invented'
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='record_hash'):
        run(tmp_path, records)


def test_uncommitted_response_not_counted(tmp_path):
    records, append = fixture(tmp_path)
    document = request(True)
    append('REQUEST', document)
    append('RESPONSE', dict(request_sha256=trace.digest(document), finished_unix=1000,
                           response=dict(raw='I will test.', token_ids=[1])))
    result = run(tmp_path, records)
    assert result['guided_committed_responses'] == 0
    assert result['first_eligible_completed_sleep'] is None


def test_refuses_sealed_root(tmp_path):
    with pytest.raises(ValueError, match='TRAIN_root_only'):
        trace.trace(tmp_path / 'sealed', 'a' * 32, 0, 'f' * 64, 'rohin')
