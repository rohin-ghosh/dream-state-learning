import json
from pathlib import Path

import pytest

from research_loop.workers.rohin183_repo_learning_20260917 import tools
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import digest,write


def fixture(tmp_path,monkeypatch):
    source=tmp_path/'snapshot'
    reference=write(source/'README.md',b'Actual fixture repository bytes.\n')
    manifest=write(tmp_path/'manifest.json',dict(schema='R183_SAFE_WORKING_TREE_SNAPSHOT_V1',
        files={'README.md':{key:reference[key] for key in ('bytes','sha256')}}))
    config=dict(root=str(tmp_path/'life'),workspace=str(tmp_path/'workspace'),snapshot=str(source),
        snapshot_manifest=manifest,receipts=str(tmp_path/'receipts'))
    Path(config['workspace']).mkdir()
    delivered=[]
    def inbox(root,speaker,text,source_receipt):
        assert root==config['root'] and speaker=='Tool'
        assert set(source_receipt)=={'path','sha256'}
        delivered.append(json.loads(text))
        return dict(id='fixture_only',sha256=digest(text.encode()),path=str(tmp_path/'fixture_inbox'))
    monkeypatch.setattr(tools,'_inbox',inbox)
    return config,dict(actor='child',split='TRAIN',record_index=2,record_sha256='a'*64),delivered


def test_actual_file_bytes_and_write_proposal_are_not_execution(tmp_path,monkeypatch):
    config,origin,delivered=fixture(tmp_path,monkeypatch)
    tools.execute(config,dict(action='read',path='README.md'),origin,0)
    assert delivered[0]['content']=='Actual fixture repository bytes.\n'
    assert delivered[0]['origin']==origin
    tools.execute(config,dict(action='propose',path='gpu/change.py',content='proposed = True\n'),origin,1)
    proposal=delivered[1]
    assert Path(proposal['workspace_path']).read_text()=='proposed = True\n'
    assert not proposal['applied_to_repository'] and not proposal['executed_code']
    assert not (Path(config['snapshot'])/'gpu/change.py').exists()


@pytest.mark.parametrize('action',[dict(action='read',path='../credentials'),dict(action='read',path='/etc/passwd'),
    dict(action='read',path='gpu/hosts.env'),dict(action='read',path='README.md',offset=-1),
    dict(action='shell',path='README.md'),dict(action='workspace_read',path='../snapshot/README.md'),
    dict(action='propose',path='gpu/code.py',content='x'*8193)])
def test_visibility_path_and_budget_denials(tmp_path,monkeypatch,action):
    config,origin,delivered=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):
        tools.execute(config,action,origin,0)
    assert not delivered


def test_changed_source_and_symlink_parent_refused(tmp_path,monkeypatch):
    config,origin,delivered=fixture(tmp_path,monkeypatch)
    (Path(config['snapshot'])/'README.md').write_text('changed')
    with pytest.raises(ValueError,match='pinned_file'):
        tools.execute(config,dict(action='read',path='README.md'),origin,0)
    assert not delivered


def test_only_explicit_single_action_is_dispatched():
    assert tools.request('My plan is to read a file.') is None
    assert tools.request('repo_read README.md')==dict(action='read',path='README.md',offset=0)
    assert tools.request('repo_action {"action":"note","path":"state.md","content":"finding"}')['action']=='note'
    with pytest.raises(ValueError,match='one_actual_action'):
        tools.request('repo_read README.md\nrepo_list .')
