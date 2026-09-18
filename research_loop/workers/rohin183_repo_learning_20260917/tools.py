"""Real bounded repository reads and immutable workspace proposals, no execution."""

import json
import os
from pathlib import Path
import re

from gpu.orch_r127_pilot_console import _directory, _read, _inbox
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require,digest,write,permitted_path


READ_LIMIT=4096
WRITE_LIMIT=8192
WORKSPACE_LIMIT=8*1024**2
ACTION_LIMIT=512


def request(text):
    require(type(text) is str and len(text)<=32768,'bounded_actual_child_response')
    actions=[]
    for line in text.splitlines():
        if line.startswith('repo_read '):
            parts=line.split()
            require(len(parts) in (2,3),'read_path_and_optional_offset')
            actions.append(dict(action='read',path=parts[1],offset=int(parts[2]) if len(parts)==3 else 0))
        elif line.startswith('repo_list '):
            parts=line.split()
            require(len(parts) in (2,3),'list_prefix_and_optional_page')
            actions.append(dict(action='list',path=parts[1],page=int(parts[2]) if len(parts)==3 else 0))
        elif line.startswith('repo_action '):
            value=json.loads(line[len('repo_action '):])
            require(type(value) is dict,'JSON_tool_request_object')
            actions.append(value)
    require(len(actions)<=1,'one_actual_action_per_child_response')
    return actions[0] if actions else None


def manifest(config):
    path=Path(config['snapshot_manifest']['path'])
    require(path.stat().st_size<=8*1024**2 and not path.is_symlink(),'bounded_manifest')
    raw=path.read_bytes()
    require(digest(raw)==config['snapshot_manifest']['sha256'],'exact_safe_manifest')
    value=json.loads(raw)
    require(value['schema']=='R183_SAFE_WORKING_TREE_SNAPSHOT_V1' and value['files'],'safe_snapshot_schema')
    require(all(permitted_path(name) for name in value['files']),'all_visible_paths_satisfy_current_exclusions')
    return value


def execute(config,action,origin,sequence):
    require(type(sequence) is int and 0<=sequence<ACTION_LIMIT,'finite_child_tool_budget')
    require(origin['actor']=='child' and origin['split']=='TRAIN' and re.fullmatch('[0-9a-f]{64}',origin['record_sha256']),
        'actual_TRAIN_response_origin')
    kind=action.get('action')
    require(kind in ('read','list','note','propose','workspace_read'),'connected_tools_only')
    path=action.get('path','')
    require(type(path) is str and len(path)<=512 and not Path(path).is_absolute() and '..' not in Path(path).parts,
        'relative_sandbox_path')
    table=manifest(config)['files']
    result=dict(schema='R183_ACTUAL_TOOL_RESULT_V1',status='COMPLETE',action=kind,request=action,
        origin=origin,sequence=sequence,model_produced_result=False,executed_code=False)
    if kind=='read':
        require(path in table,'visible_snapshot_path_only')
        offset=action.get('offset',0)
        require(type(offset) is int and 0<=offset<=table[path]['bytes'],'bounded_byte_offset')
        target=Path(config['snapshot'])/path
        with _directory(target.parent) as directory:
            raw=_read(directory,target.name,2*1024**2)
        require(len(raw)==table[path]['bytes'] and digest(raw)==table[path]['sha256'],'actual_pinned_file_bytes')
        excerpt=raw[offset:offset+READ_LIMIT]
        result.update(path=path,source_sha256=digest(raw),source_bytes=len(raw),offset=offset,
            returned_bytes=len(excerpt),content=excerpt.decode('utf-8',errors='replace'),
            next_offset=offset+len(excerpt) if offset+len(excerpt)<len(raw) else None)
    elif kind=='list':
        page=action.get('page',0)
        require(type(page) is int and 0<=page<=1000,'bounded_list_page')
        prefix='' if path in ('','.') else path.rstrip('/')+'/'
        names=sorted(name for name in table if name.startswith(prefix))
        result.update(paths=names[page*30:(page+1)*30],total_paths=len(names),page=page,
            next_page=page+1 if (page+1)*30<len(names) else None)
    elif kind in ('note','propose'):
        require(permitted_path(path) or re.fullmatch(r'[A-Za-z0-9_-]+\.md',path),'safe_proposal_target')
        content=action.get('content')
        require(type(content) is str and 0<len(content.encode())<=WRITE_LIMIT,'bounded_actual_proposal_bytes')
        workspace=Path(config['workspace'])
        used=sum(item.stat().st_size for item in workspace.rglob('*') if item.is_file())
        require(used+len(content.encode())+16384<=WORKSPACE_LIMIT,'workspace_disk_admission_before_write')
        folder=workspace/('proposals' if kind=='propose' else 'notes')
        destination=folder/(f'{sequence:06d}_'+digest(path.encode())[:16]+'.md')
        reference=write(destination,content.encode())
        proposal=write(folder/(f'{sequence:06d}.json'),dict(target=path,content=reference,origin=origin,
            actual_write=True,applied_to_repository=False,executed=False))
        result.update(workspace_path=str(destination),written_sha256=reference['sha256'],written_bytes=reference['bytes'],
            proposal=proposal,target=path,applied_to_repository=False,content=content)
    else:
        require(re.fullmatch(r'(notes|proposals)/[0-9]{6}_[0-9a-f]{16}\.md',path),'own_immutable_workspace_note')
        target=Path(config['workspace'])/path
        with _directory(target.parent) as directory:
            raw=_read(directory,target.name,WRITE_LIMIT)
        result.update(workspace_path=str(target),content=raw.decode('utf-8'),source_sha256=digest(raw))
    receipt=write(Path(config['receipts'])/f'ACTION_{sequence:06d}.json',result)
    text=json.dumps(result,ensure_ascii=False,separators=(',',':'))
    if len(text)>7000:
        result.pop('content',None)
        text=json.dumps(result,ensure_ascii=False,separators=(',',':'))
    publication=_inbox(config['root'],'Tool',text,{key:receipt[key] for key in ('path','sha256')})
    return write(Path(config['receipts'])/f'PUBLICATION_{sequence:06d}.json',dict(result=receipt,publication=publication))
