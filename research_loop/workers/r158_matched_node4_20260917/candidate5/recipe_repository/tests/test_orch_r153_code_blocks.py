import json
from pathlib import Path

import pytest

from gpu import orch_r153_code_blocks as parser
from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r140_pilot_tool_service as service
from gpu import orch_r132_kernel_bridge as bridge
from organism_v6.orch_r125_experiment_request import make_request


@pytest.mark.parametrize('opening,closing', [ ('```python', '```'), ('```', '```'),
    ('```python experiment', '```'), ('~~~python', '~~~'), ('````python', '````'),
    ('  ```PYTHON ', '  ```'), ('```triton', '```')])
def test_plain_first_code_block_variants(opening, closing):
    raw = 'I will test this.\n' + opening + '\nprint(2)\n' + closing + '\n'
    result = parser.extract(raw)
    assert result['source'] == 'print(2)\n'
    assert result['raw_source'] == raw[result['span_start']:result['span_end']]
    assert result['transformations'] == []
    assert service.experiment(raw, code_policy=parser.POLICY) == (True, 'print(2)\n')


def test_first_block_only_and_no_scanning_nested_peer_text():
    raw = '```python\nprint(1)\n```\n```python\nprint(2)\n```'
    assert parser.extract(raw)['source'] == 'print(1)\n'
    assert parser.extract('````text\n' + raw + '\n````')['source'] is None
    assert parser.extract('> ```python\n> print(1)\n> ```')['attempted'] is False


def test_ascii_punctuation_keeps_raw_and_valid_unicode_literals():
    raw = '```python\nprint（“hello”）\nprint("中文—原文") # comment—kept\n```'
    result = parser.extract(raw)
    assert result['source'] == 'print("hello")\nprint("中文—原文") # comment—kept\n'
    assert result['raw_source'] == 'print（“hello”）\nprint("中文—原文") # comment—kept\n'
    assert len(result['transformations']) == 4
    assert result['raw_source_sha256'] != result['source_sha256']
    assert 'source' not in parser.metadata(result)


@pytest.mark.parametrize('raw', ['print(1)', '```python\nprint(1)', '```python\n```',
    '```shell\nrm things\n```'])
def test_no_execution_for_no_block_incomplete_empty_or_unsupported(raw):
    assert parser.extract(raw)['source'] is None


def test_CRLF_is_preserved_without_false_equivalence():
    result = parser.extract('```python\r\nprint(1)\r\n```\r\n')
    assert result['source'] == 'print(1)\r\n'


def chain(root, raw, split='TRAIN', terminal=True):
    directory = root / 'stream/records'
    directory.mkdir(parents=True)
    records = []
    request = dict(split=split, resume_state={})
    response = dict(request_sha256=cpu.digest(dict(split=split)),
                    response=dict(raw=raw, terminal=terminal, truncated=not terminal))
    previous = '0' * 64
    for index, kind, document in ((0, 'REQUEST', request), (1, 'RESPONSE', response),
                                  (2, 'COMMITTED', dict(source_sha256=cpu.digest(response)))):
        record = dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32,
                      index=index, kind=kind, document=document, previous_sha256=previous)
        record['sha256'] = cpu.digest(record)
        previous = record['sha256']
        (directory / f'{index:020d}.json').write_text(json.dumps(record))
        records.append(record)
    return records


def test_CPU_and_kernel_origin_bind_same_transformation_without_journal_mutation(tmp_path):
    raw = '```python\nprint（“hi”）\n```\n```python\nprint(99)\n```'
    records = chain(tmp_path, raw)
    before = {path.name: path.read_bytes() for path in (tmp_path / 'stream/records').iterdir()}
    source = parser.extract(raw)['source']
    request = make_request(source, dict(kind='TRAIN_CHILD_RESPONSE', record_index=1,
                                       record_sha256=records[1]['sha256']))
    proof = cpu.verify_origin(request, tmp_path, code_policy=parser.POLICY)
    assert proof['code_transformation']['raw_source_sha256'] == parser.sha('print（“hi”）\n')
    assert proof['code_transformation']['source_sha256'] == parser.sha(source)
    kernel = bridge.child_request(tmp_path, 1, code_policy=parser.POLICY)
    assert kernel['source'] == source
    assert kernel['task'] == 'triton_add_f32_v1'
    assert before == {path.name: path.read_bytes() for path in (tmp_path / 'stream/records').iterdir()}
    with pytest.raises(ValueError, match='explicit_experiment'):
        cpu.verify_origin(request, tmp_path)
    altered = make_request('print(99)\n', request['origin'])
    with pytest.raises(ValueError, match='explicit_experiment'):
        cpu.verify_origin(altered, tmp_path, code_policy=parser.POLICY)


@pytest.mark.parametrize('split,terminal', [('DEV', True), ('FINAL', True), ('HELD', True), ('TRAIN', False)])
def test_forgiving_syntax_never_weakens_TRAIN_complete_origin(tmp_path, split, terminal):
    records = chain(tmp_path, '```python\nprint(1)\n```', split, terminal)
    request = make_request('print(1)\n', dict(kind='TRAIN_CHILD_RESPONSE', record_index=1,
                                           record_sha256=records[1]['sha256']))
    with pytest.raises(ValueError):
        cpu.verify_origin(request, tmp_path, code_policy=parser.POLICY)


def test_policy_is_explicit_and_bounded():
    with pytest.raises(ValueError, match='bounded'):
        parser.extract('x' * (parser.MAX_BYTES + 1))
    with pytest.raises(ValueError, match='known_code_policy'):
        service.code_policy({'code_policy': 'permissive'})
