import pytest

from organism_v6 import orch_code_bounded as code


@pytest.mark.parametrize('expression', ['__import__(1)', 'x.__class__', '(lambda: 1)()',
                                      '2**100000', 'range(100000000)', '[0]*100000000',
                                      '"string"', '{1:2}', '[x for x in [1] for y in [2]]'])
def test_unsafe_rejected(expression):
    with pytest.raises((ValueError, SyntaxError)):
        code.evaluate(expression, {'x': [1]})


def test_finite_operations():
    assert code.evaluate('sum([x*x for x in values if x > 0])', {'values': [-1, 2, 3]}) == 13
    assert code.evaluate('values[::-1]', {'values': [1, 2]}) == [2, 1]
    assert code.evaluate('0 if value == 0 else 10/value', {'value': 0}) == 0


def test_oracle_and_projection():
    record = dict(task_id=1, text='sum input', code='def total(values):\n return sum(values)',
                  test_setup_code='', test_list=['assert total([1,2]) == 3'] * 3)
    task = code.extract_task(record)
    assert code.check(task, 'sum(values)')['success']
    assert not code.check(task, 'len(values)')['success']
    messages, student = code.prompt(task, 'rich', [])
    assert messages[1:] == student and '150–400' not in str(student)
    assert 'def total' not in str(student)
    assert code.parse_action('I add.\n{"expression":"sum(values)"}')[0] == 'sum(values)'


def test_reference_mismatch_rejected():
    with pytest.raises(ValueError, match='mismatch'):
        code.extract_task(dict(task_id=2, text='', code='def f(x):\n return x', test_setup_code='',
                               test_list=['assert f(1) == 2'] * 3))


def test_json_roundtrip_preserves_tuple_oracle():
    import json
    task = code.extract_task(dict(task_id=3, text='', code='def f(values):\n return tuple(values)',
                             test_setup_code='', test_list=['assert f([1,2]) == (1,2)'] * 3))
    assert code.check(json.loads(json.dumps(task)), 'tuple(values)')['success']
    assert not code.check(json.loads(json.dumps(task)), 'values')['success']


def test_native_mounted_names_and_template_contract():
    from pathlib import Path
    from types import SimpleNamespace
    from gpu.orch_code_bounded_screen import mounted_parameters
    parameters = {'layer.lora_A.default.weight': SimpleNamespace(requires_grad=False),
                  'layer.lora_B.default.weight': SimpleNamespace(requires_grad=False),
                  'layer.weight': SimpleNamespace(requires_grad=False)}
    model = SimpleNamespace(named_parameters=lambda: iter(parameters.items()))
    assert list(mounted_parameters(model)) == list(parameters)[:2]
    parameters['layer.weight'].requires_grad = True
    with pytest.raises(ValueError):
        mounted_parameters(model)
    source = Path('gpu/orch_code_bounded_screen.py').read_text()
    assert 'return_dict=False' in source and 'max_new_tokens=512' in source


def test_source_provenance(tmp_path):
    import io
    import tarfile
    from gpu.orch_code_bounded_source import verify_archive
    archive = tmp_path / 'source.tar'
    with tarfile.open(archive, 'w') as stream:
        member = tarfile.TarInfo('own.py')
        member.size = 1
        stream.addfile(member, io.BytesIO(b'1'))
    (tmp_path / 'own.py').write_text('1')
    assert verify_archive(archive, tmp_path) == 1
    (tmp_path / 'own.py').write_text('2')
    with pytest.raises(ValueError):
        verify_archive(archive, tmp_path)


def test_all_frozen_oracles_have_prospective_reference_parity():
    import json
    from pathlib import Path
    root = Path('research_notes/analysis/orch_code_bounded_20260914_attempt1')
    document = json.loads((root / 'TASKS.json').read_text())
    records = [json.loads(line) for line in (root / 'mbpp.jsonl').read_text().splitlines()]
    assert len(records) == document['total'] == 974
    assert code.sha((root / 'mbpp.jsonl').read_text()) == document['source_sha256']
    assert document['eligible_count'] + len(document['exclusions']) == 974
    for task in document['tasks']:
        original = next(record for record in records if record['task_id'] == task['id'])
        assert json.loads(json.dumps(code.extract_task(original))) == task
