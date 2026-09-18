from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from gpu import orch_r118_grid_parallel_stage as stage


def fixture_owner(tmp_path):
    root = tmp_path / 'A4'
    return dict(branch='A4', root=str(root), handoff={'path':'/actual/HANDOFF.json','sha256':'handoff'},
        inherited_bounds=dict(train_end_unix=100, native_used=567, parent_used=40),
        boundary={'settled_pending_consolidation':{'path':'/actual/PENDING.json','sha256':'pending'}},
        source_files={'/frozen/source.py':'exact'}, cwd=str(tmp_path / 'runtime'),
        bootstrap_path=str(root / 'parallel_exec_1513/FRESH_BOOTSTRAP.json'), device=dict(kind='cuda',physical=7,uuid='uuid'),
        runtime_plan_bindings=dict(schema='R118_GRID_PARALLEL_EXEC_V1', root=str(root), branch='A4',
            common_root='/COMMON', directory=str(root / 'parallel_exec_1513'),
            bounds={'native_cap':1858,'parent_cap':298}, boundary={'path':'/actual/BOUNDARY.json','sha256':'boundary'}))


def test_exact_dispatch_command_env_no_placeholders_or_reserved_overrides(tmp_path):
    owner = fixture_owner(tmp_path)
    before = deepcopy(owner)
    reference = stage.write(tmp_path / 'PLAN.json', {'campaign':'actual pinned plan'})
    result = stage.dispatch_owner(owner, reference)
    assert result['command'][-4:] == ['--plan',reference['path'],'--sha256',reference['sha256']]
    assert all('PLACEHOLDER' not in part and 'MAIN_' not in part for part in result['command'])
    assert result['env']['CUDA_VISIBLE_DEVICES'] == ''
    assert not any(name.startswith('R118_PARALLEL_') for name in result['env'])
    assert result['boundary'] == owner['boundary']
    assert result['GPU_started'] is False
    assert owner == before


def test_plan_preserves_pending_and_only_adds_campaign_FINAL_custody(tmp_path):
    owner = fixture_owner(tmp_path)
    campaign = dict(path='/Main/CAMPAIGN.json',sha256='actual')
    previous = dict(path='/old/FINAL_PLAN.json',sha256='old')
    timers = [dict(pid=1533431),dict(pid=1533432)]
    plan = stage.assemble(owner,campaign,previous,timers,tmp_path / 'separate_eval/A4')
    assert all(plan[name] == value for name,value in owner['runtime_plan_bindings'].items())
    assert plan['campaign'] == campaign and plan['previous_final_plan'] == previous
    assert 'bootstrap_path' not in plan
    assert set(plan) - set(owner['runtime_plan_bindings']) == {
        'campaign','previous_final_plan','old_final_identities','final_output'}


@pytest.mark.parametrize('pids', [(1519259,1533432),(1533431,1533431),(1533431,)])
def test_selector_or_duplicate_missing_timers_rejected(tmp_path,pids):
    with pytest.raises(ValueError,match='never_selector'):
        stage.assemble(fixture_owner(tmp_path),{}, {}, [dict(pid=pid) for pid in pids],tmp_path / 'eval')


@pytest.mark.parametrize('change', [dict(root='/OTHER'),dict(first_generation=0),dict(deadline_unix=101),
                                  dict(deadline_unix=1),dict(source_files={'/frozen/source.py':'wrong'})])
def test_wrong_or_extended_campaign_rejected(tmp_path,change):
    campaign=dict(root='/COMMON',first_generation=1,deadline_unix=100,source_files={'/frozen/source.py':'exact'})
    campaign.update(change)
    with pytest.raises(ValueError):
        stage.validate_campaign(campaign,fixture_owner(tmp_path),clock=lambda:2)


def test_valid_campaign_and_immutable_outputs(tmp_path):
    campaign=dict(root='/COMMON',first_generation=1,deadline_unix=100,source_files={'/frozen/source.py':'exact'})
    stage.validate_campaign(campaign,fixture_owner(tmp_path),clock=lambda:2)
    path = tmp_path / 'receipt.json'
    reference = stage.write(path,dict(status='NOT_LAUNCHED'))
    assert stage.checked(reference)['status'] == 'NOT_LAUNCHED'
    with pytest.raises(FileExistsError):
        stage.write(path,dict(status='OVERWRITE'))
    path.write_text(json.dumps({'changed':True}))
    with pytest.raises(ValueError,match='pinned_metadata'):
        stage.checked(reference)


def test_stager_help_has_no_model_or_GPU_import():
    result=subprocess.run([sys.executable,'-B',stage.__file__,'--help'],capture_output=True,text=True)
    assert result.returncode == 0 and '{prepare,stage}' in result.stdout
