"""CPU-only ordinary TRAIN anchors, exclusion checks and native workflow mocks."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

import pytest

from organism_v6 import orch_r107_base_anchors as policy
from gpu import orch_r107_base_anchors_run as runner


def reference(row):
    if row['family'] == 'code':
        return json.dumps(dict(expression=row['oracle']['reference_expression']))
    if row['family'] == 'simulated_tools':
        return json.dumps(row['oracle'])
    return row['oracle']['answer']


def test_fixed64_round_robin_disjoint_train_suite():
    suite = policy.tasks()
    assert suite == policy.tasks() and len(suite) == 64
    assert Counter(row['family'] for row in suite) == {family: 16 for family in policy.FAMILIES}
    assert [row['family'] for row in suite[:4]] == list(policy.FAMILIES)
    assert policy.exclusions(suite)['status'] == 'PASS'
    assert all(row['split'] == 'TRAIN' and not row['trainingAllowed'] for row in suite)
    assert all(policy.messages(row) == [dict(role='user', content=row['prompt'])] for row in suite)
    assert all('oracle' not in json.dumps(policy.messages(row)) for row in suite)


@pytest.mark.parametrize('position', range(64))
def test_independent_reference_cases_and_answers_pass(position):
    row = policy.tasks()[position]
    assert policy.score(row, reference(row))['passed']


def test_held_panel_task_and_unregistered_cohort_rejected():
    suite = policy.tasks()
    suite[0] = policy.excluded_panel.tasks()[0]
    with pytest.raises(ValueError, match='overlap'):
        policy.exclusions(suite)
    row = deepcopy(policy.tasks()[0])
    row['cohort'] = 'other'
    with pytest.raises(ValueError, match='fixed_task_changed'):
        policy.messages(row)


@pytest.mark.parametrize('expression', [
    "__import__('os').system('false')", 'number.real', '(lambda number: number)(1)',
    'sum(range(1000000))', '[item for item in range(257)]', 'open(1)',
])
def test_generated_code_never_arbitrarily_executes(expression):
    row = policy.tasks()[0]
    assert not policy.score(row, json.dumps(dict(expression=expression)))['passed']


def test_strict_output_no_prose_or_fence_salvage():
    row = policy.tasks()[0]
    assert policy.score(row, '```json\n' + reference(row) + '\n```')['category'] == 'invalid_json'
    assert policy.score(row, '{"expression":"1","expression":"2"}')['category'] == 'invalid_json'
    math_row = policy.tasks()[1]
    assert not policy.score(math_row, 'Answer: ' + reference(math_row))['passed']
    short_row = policy.tasks()[3]
    assert not policy.score(short_row, reference(short_row) + '\n')['passed']


def test_mock_tool_schema_boolean_and_wrong_args_rejected():
    row = next(row for row in policy.tasks() if row['family']=='simulated_tools' and row['oracle']['tool']=='plan_pickup')
    wrong = deepcopy(row['oracle'])
    wrong['arguments']['parcels'] = True
    result = policy.score(row, json.dumps(wrong))
    assert not result['passed'] and not result['schema_valid'] and result['mock_only']
    wrong['arguments']['parcels'] = 999
    assert policy.score(row, json.dumps(wrong))['category'] == 'wrong_tool_or_arguments'


def response(row, terminal=True):
    return dict(messages=policy.messages(row), raw=reference(row), prompt_tokens=3,
        token_ids=[7,99] if terminal else [7]*512, terminal=terminal, truncated=not terminal)


def test_correct_looking_truncated_output_not_anchor():
    row = policy.tasks()[1]
    result = policy.outcome(row, response(row, False), 99)
    assert result['machine']['passed'] and not result['verified_anchor']
    assert result['completion'] == 'truncated' and result['content_tokens'] == 512


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    snapshot = tmp_path/'source'
    for relative in runner.REQUIRED_SOURCES:
        destination = snapshot/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        copyfile(runner.SOURCE_ROOT/relative,destination)
    monkeypatch.setattr(runner,'SOURCE_ROOT',snapshot)
    predecessor=tmp_path/'predecessor'
    monkeypatch.setattr(runner,'PREDECESSOR',predecessor)
    model=tmp_path/'model'
    runner.write(model/'config.json',dict(model_type='qwen2',max_position_embeddings=32768))
    runner.write(model/'tokenizer.json',{})
    runner.write(model/'tokenizer_config.json',{})
    runner.write(predecessor/'PLAN.json',dict(model_dir=str(model)))
    monkeypatch.setattr(runner.ownership,'host_identity',lambda:runner.ownership.continual.combined.HOST_SHA)
    monkeypatch.setattr(runner.time,'time',lambda:runner.ownership.TRAIN_CUTOFF+2000)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','')
    tokenizer=SimpleNamespace(eos_token_id=99,apply_chat_template=lambda *args,**kwargs:[1,2,3])
    monkeypatch.setattr(runner.common.native.source.native,'load_local_tokenizer',lambda unused:tokenizer)
    def forbidden(*args,**kwargs):
        pytest.fail('CPU prepare cannot construct Engine')
    monkeypatch.setattr(runner,'Engine',forbidden)
    root=tmp_path/'anchors'
    cpu_log=tmp_path/'cpu.log'
    cpu_log.write_text('tests passed')
    runner.prepare(root,cpu_log)
    runner.write(root/'PUBLICATION.json',dict(ready_sha256=runner.sha(root/'READY.json'),
        own_cpu_tests_passed=True,dated_builder_publication='[Builder] own CPU tests',board_allocation='A1000 only'))
    return root


def test_prepare_binds_isolated_sources_and64_calls(prepared):
    plan=runner.read(prepared/'PLAN.json')
    assert runner.validate(plan,runner.time.time()) is plan
    assert set(plan['sources'])==set(runner.REQUIRED_SOURCES)
    assert plan['hard_deadline_unix']-plan['lifetime_started_unix']==1800
    assert len(runner.read(prepared/'RESERVATIONS.json')['cells'])==64
    assert runner.read(prepared/'READY.json')['native_calls']==0
    assert runner.ready_check(prepared,plan)['status']=='PASS'


@pytest.mark.parametrize('field,value', [
    ('adapter','adapter'),('call_cap',65),('max_new_tokens',1536),('parent_calls',1),
    ('training_updates',1),('automatic_fit',True),('parent_access',True),
    ('physical_index',1),('gpu_uuid','other'),('suite_sha256','other'),('gpu_hours_cap',1),
])
def test_plan_scope_not_expandable(prepared,field,value):
    plan=runner.read(prepared/'PLAN.json')
    plan[field]=value
    with pytest.raises(ValueError):
        runner.validate(plan,runner.time.time())


def test_snapshot_hash_guard_stays_strict(prepared):
    plan=runner.read(prepared/'PLAN.json')
    file=runner.SOURCE_ROOT/runner.REQUIRED_SOURCES[0]
    file.write_bytes(file.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='source_hash_drift'):
        runner.validate(plan,runner.time.time())


@pytest.mark.parametrize('fail', [False,True])
def test_mock_native64_noadapter_retains_failures_and_manifest_gate(prepared,monkeypatch,fail):
    plan=runner.read(prepared/'PLAN.json')
    runner.write(prepared/'ADMISSION.json',dict(plan_sha256=runner.sha(prepared/'PLAN.json'),snapshot={}))
    monkeypatch.setattr(runner.ownership,'validate_scan',lambda unused,now:None)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES',runner.GPU_UUID)
    monkeypatch.setenv('HF_HUB_OFFLINE','1')
    monkeypatch.setenv('TRANSFORMERS_OFFLINE','1')
    generated=[]
    verified=[]
    class FakeEngine:
        def __init__(self,options,tokenizer,check):
            assert options.adapter_dir is None and options.phase=='readout'
            assert options.expected_base_sha256==policy.BASE_SHA
            self.model=SimpleNamespace(named_parameters=lambda:[('weight',SimpleNamespace(requires_grad=False))])
            self.check=check
        def verify_base(self):
            self.check('base_hash')
            verified.append(True)
        def generate(self,messages,max_new_tokens):
            position=len(generated)
            assert max_new_tokens==512
            assert runner.read(prepared/f'readout/CALL_{position:03d}.json')['status']=='RESERVED'
            row=policy.tasks()[position]
            assert messages==policy.messages(row)
            generated.append(row['id'])
            if fail:
                raise TimeoutError('mock failure')
            return response(row)
    monkeypatch.setattr(runner,'Engine',FakeEngine)
    if fail:
        with pytest.raises(TimeoutError):
            runner.run(prepared)
    else:
        runner.run(prepared)
    manifest=runner.read(prepared/'ANCHOR_MANIFEST.json')
    rows=runner.read(prepared/'ANCHOR_ROWS.json')
    assert len(verified)==2 and not manifest['automatic_fit'] and not manifest['trainingAllowed']
    assert len(generated)==(1 if fail else 64)
    assert manifest['verified_anchors']==len(rows)==(0 if fail else 64)
    assert manifest['status']==('WITHHELD_UNVERIFIED_EXECUTION' if fail else 'VERIFIED_ANCHOR_MANIFEST_READY')
    assert all(not row['trainingAllowed'] and row['source_actor']['adapter'] is None for row in rows)
    assert all(row['target_sha256']==hashlib.sha256(row['target'].encode()).hexdigest() for row in rows)
    assert all(entry['shortfall']==(4 if fail else 0) for entry in manifest['families'].values())
    assert (prepared/'readout/AFTER.json').exists()
    with pytest.raises(FileExistsError):
        runner.run(prepared)
    assert len(generated)==(1 if fail else 64)


def test_wrong_host_hash_rejected_before_preparation(tmp_path,monkeypatch):
    monkeypatch.setattr(runner.ownership,'host_identity',lambda:'0'*64)
    with pytest.raises(ValueError,match='pinned_host_required'):
        runner.prepare(tmp_path,tmp_path/'unused')
