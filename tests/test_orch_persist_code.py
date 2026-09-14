import importlib.util
import json

import pytest

from organism_v6 import orch_persist_code as ledger


def solution(task):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    return [
        f'sum(affine(ge(values,{threshold}),{factor},{offset}))',
        f'sum(unique(clip(affine(values,{factor},{offset}),{low},{high})))',
        f'sum(affine(ge(unique(values),{threshold}),{factor},{offset}))',
        f'len(ge(affine(clip(values,{low},{high}),{factor},{offset}),{threshold}))',
    ][task['kind']]


def test_all_distinct_l1_tasks_and_independent_oracle():
    tasks = ledger.build_tasks()
    assert len({task['spec'] for task in tasks}) == 64
    assert tasks == ledger.build_tasks()
    assert all(ledger.check_expression(task, solution(task))['success'] for task in tasks)


@pytest.mark.parametrize('family', ledger.PARTITION['L2proposal'] + ledger.PARTITION['heldL3proposal'])
def test_proposal_families_cannot_be_generated(family):
    with pytest.raises(ValueError):
        ledger.build_tasks(family)


@pytest.mark.parametrize('expression', [
    '__import__("os").system("true")', 'values.__class__', '[0]*1000000',
    'sum(value for value in values)', 'open(1)', '2**1000', 'ge(values)',
    'sum(values, start=2)', 'True', 'sum', 'values', 'sum(affine(values,1001,0))',
])
def test_arbitrary_code_and_noninteger_returns_rejected(expression):
    with pytest.raises((ValueError, SyntaxError, TypeError)):
        ledger.evaluate(expression, [1, 2])


def test_persistent_code_records_feedback_and_regressions(tmp_path):
    codebase = ledger.Codebase(tmp_path / 'codebase')
    tasks = ledger.build_tasks(count=2)
    failure = codebase.patch(tasks[0], 'sum(values)')
    assert not failure['success'] and 'expected' in failure
    assert not codebase.functions
    with pytest.raises(ValueError):
        codebase.record(tasks[0]['id'], 'unsourced', 0)
    assert codebase.patch(tasks[0], solution(tasks[0]))['success']
    codebase.record(tasks[0]['id'], 'child fixture, never a training corpus', 1)
    result = codebase.patch(tasks[1], solution(tasks[1]))
    assert result['success'] and result['regressions_pass'] and result['previous_functions'] == 1
    spec = importlib.util.spec_from_file_location('generated_ledger', codebase.directory / 'ledger.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for task in tasks:
        for values in task['inputs']:
            assert getattr(module, task['id'])(values) == ledger.expected(task, values)
    assert json.loads((codebase.directory / 'records.json').read_text())[0]['call_id'] == 1


def test_parent_instruction_absent_from_student_prefix():
    task = ledger.build_tasks(count=1)[0]
    messages, prefix = ledger.messages(task, [], 'RICH', 'sum(values)', {'success': False})
    assert messages[1:] == prefix
    assert '150–400' in messages[0]['content']
    assert '150–400' not in json.dumps(prefix)
    assert 'My preceding attempt' in prefix[0]['content']


def test_action_parser_never_repairs_generated_bytes():
    assert ledger.parse_action('I expect a check.\n{"expression":"sum(values)"}')[0] == {'expression': 'sum(values)'}
    with pytest.raises(ValueError):
        ledger.parse_action('{"expression":"sum(values)", "extra":1}')
    with pytest.raises(ValueError):
        ledger.parse_action('```json\n{"expression":"sum(values)"}\n```')


class FakeTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return list(range(100))

    def encode(self, text, **kwargs):
        return list(range(len(text.split())))


class FakeEngine:
    def __init__(self, texts):
        self.texts = iter(texts)
        self.requests = []

    def generate(self, messages, max_new_tokens):
        self.requests.append(messages)
        assert max_new_tokens == 512
        return dict(raw=next(self.texts), prompt_tokens=100, token_ids=[1] * 200,
                    terminal=True, truncated=False, messages=messages)


def test_native_collection_reuses_own_records_and_correction_only(tmp_path):
    from gpu import orch_persist_code_screen as driver

    tasks = ledger.build_tasks(count=2)
    engine = FakeEngine([
        json.dumps({'expression': 'sum(values)'}),
        json.dumps({'expression': solution(tasks[0])}),
        json.dumps({'record': 'fixture child record'}),
        json.dumps({'expression': solution(tasks[1])}),
        json.dumps({'record': 'second fixture record'}),
    ])
    result = driver.collect(engine, FakeTokenizer(), tmp_path, 'TERSE', tasks)
    assert result['successes'] == result['own_records'] == 2
    assert result['corrections'] == 1 and result['model_calls'] == 5
    assert result['semantic_admitted_rows'] == 0 and not result['trainingAllowed']
    fourth = json.loads((tmp_path / 'CALL_003.json').read_text())
    assert fourth['visible_record_ids'] == [2]
    assert 'fixture child record' in json.dumps(fourth['student_prefix'])
    assert 'Be terse' not in json.dumps(fourth['student_prefix'])


def test_native_collection_bounded_format_failure_and_no_fake_success(tmp_path):
    from gpu import orch_persist_code_screen as driver

    engine = FakeEngine(['invalid action'] * 5)
    result = driver.collect(engine, FakeTokenizer(), tmp_path, 'RICH', ledger.build_tasks(count=1))
    assert result['model_calls'] == 5 and result['successes'] == 0
    assert result['episodes'][0]['stop'] == 'repair_budget_exhausted'
    assert len(list(tmp_path.glob('CALL_*.json'))) == 5


def test_format_failure_is_not_grounded_oracle_correction(tmp_path):
    from gpu import orch_persist_code_screen as driver

    tasks = ledger.build_tasks(count=1)
    engine = FakeEngine(['invalid', json.dumps({'expression': solution(tasks[0])}),
                         json.dumps({'record': 'child fixture'})])
    result = driver.collect(engine, FakeTokenizer(), tmp_path, 'TERSE', tasks)
    assert result['successes'] == 1 and result['corrections'] == 0


def test_archive_checks_bytes_not_remote_uid(tmp_path):
    import tarfile
    from gpu import orch_persist_code_screen as driver

    source = tmp_path / 'source'
    source.mkdir()
    path = source / 'module.py'
    path.write_text('answer = 42\n')
    archive = tmp_path / 'source.tar.gz'
    with tarfile.open(archive, 'w:gz') as packed:
        metadata = packed.gettarinfo(path, arcname='module.py')
        metadata.uid = 98765
        with path.open('rb') as content:
            packed.addfile(metadata, content)
    assert driver.verify_archive(archive, source) == 1
    path.write_text('answer = 43\n')
    with pytest.raises(ValueError):
        driver.verify_archive(archive, source)
