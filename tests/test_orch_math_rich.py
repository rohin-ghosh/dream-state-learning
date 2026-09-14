from fractions import Fraction
import pytest

from organism_v6 import orch_math_rich as math


def test_exact_numeric_oracle_not_float_or_arbitrary_code():
    assert math.number('1,250.50') == Fraction(2501, 2)
    assert math.final_value('I compute.\nFINAL: 3/2') == Fraction(3, 2)
    assert math.final_value('FINAL: 2\nactually 3') is None
    assert math.final_value('FINAL: 1/0') is None
    assert math.final_value('FINAL: __import__("os")') is None


def test_validation_precedes_mining():
    assert math.family('A rectangle has 20% more area') == math.VALIDATION[0]
    assert math.family('Jane is 20 years old and earns 10 per hour') == math.VALIDATION[1]
    assert math.family('A worker earns 10 per hour') == 'work_rates'


def test_reference_reasoning_never_in_student_or_guided_prompt():
    task = dict(question='There are 2 boxes of 3. How many?', gold='6')
    for kind in ('rich', 'terse', 'correction', 'record'):
        guided, student = math.prompt(task, kind, 'My initial attempt. FINAL: 5')
        assert not any('exact-answer checker' in turn['content'] for turn in student)
        assert not any(turn['role'] == 'system' for turn in student)
        assert '6' not in str(guided)


def test_fixed_denominator_missing_calls_are_not_eligible():
    tasks = [dict(id=f'{family}-{index}', family=family) for family in math.MINING for index in range(8)]
    assert math.reduce_screen(tasks, [])['denominator'] == 32
    assert all(not counts['eligible'] for counts in math.reduce_screen(tasks, [])['families'].values())
    with pytest.raises(ValueError, match='denominator'):
        math.reduce_screen(tasks[:-1], [])


def test_correct_verbose_target_still_unadmitted():
    task = dict(id='test', family='work_rates', gold='6')
    result = dict(raw='I reason.\nFINAL: 6', token_ids=list(range(201)), terminal=True,
                  truncated=False, prompt_tokens=50)
    row = math.capture(task, 'rich', result, [])
    assert row['candidate'] and not row['admitted']
    with pytest.raises(ValueError, match='substantive'):
        math.admit(row, dict(status='PASS', target_sha256=row['target_sha256'], reason='A heading',
                            evidence_spans=['I reason.']), True)


def test_outcome_failure_never_admitted_even_with_semantic_pass():
    task = dict(id='test', family='work_rates', gold='6')
    result = dict(raw='I reason.\nFINAL: 5', token_ids=list(range(201)), terminal=True,
                  truncated=False, prompt_tokens=50)
    row = math.capture(task, 'rich', result, [])
    review = dict(status='PASS', target_sha256=row['target_sha256'], reason='test',
                  evidence_spans=['I reason.'], first_person=True, grounded_operations=True,
                  checkable_expectation=True, reusable_content=True, no_padding=True)
    assert not math.admit(row, review, True)['admitted']


def test_manifest_strips_reference_solutions_and_freezes_unique_tasks():
    questions = ('What is 20% of ', 'A person earns per hour ', 'Half of ', 'Each box has ')
    records = [dict(question=f'{prefix}{index}?', answer='REFERENCE SECRET REASONING #### 2')
               for prefix in questions for index in range(10)]
    document = math.build_tasks(records + records)
    assert len(document['tasks']) == 32
    assert 'REFERENCE' not in str(document)
    assert len({task['id'] for task in document['tasks']}) == 32
    assert document == math.build_tasks(records + records)


def test_source_verifier_binds_bytes_not_cross_host_uid(tmp_path):
    import io
    import tarfile
    from gpu.orch_math_rich_source import verify_archive
    archive = tmp_path / 'source.tar'
    directory = tmp_path / 'source'
    directory.mkdir()
    (directory / 'code.py').write_text('print(1)\n')
    with tarfile.open(archive, 'w') as stream:
        member = tarfile.TarInfo('code.py')
        member.uid, member.gid, member.size = 999999, 888888, 9
        stream.addfile(member, io.BytesIO(b'print(1)\n'))
    assert verify_archive(archive, directory) == 1
    (directory / 'code.py').write_text('print(2)\n')
    with pytest.raises(ValueError, match='source_bytes_changed'):
        verify_archive(archive, directory)


def test_portable_hash_keeps_mounted_default_namespace_and_is_readonly():
    from types import SimpleNamespace
    from gpu.orch_math_rich_screen import mounted_adapter_parameters
    parameters = {'base.layer.lora_A.default.weight': SimpleNamespace(requires_grad=False),
                  'base.layer.lora_B.default.weight': SimpleNamespace(requires_grad=False),
                  'base.layer.weight': SimpleNamespace(requires_grad=False)}
    model = SimpleNamespace(named_parameters=lambda: iter(parameters.items()))
    assert list(mounted_adapter_parameters(model)) == list(parameters)[:2]
    parameters['base.layer.weight'].requires_grad = True
    with pytest.raises(ValueError, match='readonly'):
        mounted_adapter_parameters(model)


def test_reducer_preserves_denominator_before_calls(tmp_path):
    import json
    from gpu.orch_math_rich_reduce import reduction
    tasks = [dict(id=f'{family}-{index}', family=family) for family in math.MINING for index in range(8)]
    (tmp_path / 'TASKS.json').write_text(json.dumps(dict(tasks=tasks)))
    report, rows = reduction(tmp_path)
    assert report['denominator'] == 32 and not report['complete']
    assert not report['eligible_scale_families'] and not report['fit_ready']
    assert report['class_metrics']['correction']['attempted'] == 0
    assert rows == []
