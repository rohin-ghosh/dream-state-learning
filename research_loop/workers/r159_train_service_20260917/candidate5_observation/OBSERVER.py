import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

DIRECTORY = Path('/tmp/r159_service_observation_candidate5_20260917T054314Z')
DEADLINE = 1789624994
LIMIT = 64*1024**2
REMOTE = r'''
import base64, datetime, hashlib, json, math, os, pathlib, stat, sys
options=json.loads(sys.argv[1]); consumed=0; artifacts={}
base=pathlib.Path('/localhome/local-rohing/orch_r159_train_service_candidate5_20260917')
campaign=pathlib.Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path,limit=1048576,retain=False):
    global consumed
    path=pathlib.Path(path)
    assert path.is_absolute() and path.resolve()==path and not any(part.is_symlink() for part in (path,*path.parents))
    assert 'readout' not in str(path).lower() and 'sealed' not in str(path).lower()
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(descriptor); assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
        pseudo=str(path).startswith('/proc/')
        allowance=limit if pseudo else before.st_size+1
        assert consumed+allowance<=options['allowance'], 'observer_read_budget'
        consumed+=allowance
        raw=os.read(descriptor,allowance)
        after=os.fstat(descriptor)
        assert pseudo or (len(raw)==before.st_size and (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns))
    finally: os.close(descriptor)
    reference=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    if retain: artifacts[str(path)]=dict(reference,raw_base64=base64.b64encode(raw).decode())
    return raw,reference
def document(path,retain=False):
    raw,reference=read(path,retain=retain)
    return json.loads(raw),reference
def record(root,index,retain=False):
    value,reference=document(root/'stream/records'/f'{index:020d}.json',retain)
    assert value['schema']=='R125_STREAM_JOURNAL_V1' and value['index']==index
    assert value['sha256']==digest({key:item for key,item in value.items() if key!='sha256'})
    return value,reference
def publication(root,source_path,retain=False):
    source,source_ref=document(source_path,retain)
    published,published_ref=document(source_path.parent/'PUBLICATION.json',retain)
    message_path=root/'stream/inbox'/(published['id']+'.json')
    assert str(message_path)==published['path']
    message,message_ref=document(message_path,retain)
    assert message_ref['sha256']==published['sha256'] and message['actor']=='environment' and message['split']=='TRAIN'
    assert message['source_receipt']==dict(path=str(source_path),sha256=source_ref['sha256'])
    assert message['id']==published['id'] and message['speaker']=='Tool'
    return source,message,published,[source_ref,published_ref,message_ref]
def rendered(request,message,published):
    body=request['document']; assert request['kind']=='REQUEST' and body['split']=='TRAIN'
    resume=body['resume_state']; assert resume['sha256']==digest(resume['state'])
    assert body['history_sha256']==digest(resume['state']['history'])
    expected=dict(event_id='environment:inbox:'+message['id'],actor='environment',split='TRAIN',
        text='Tool: '+message['text'],phase='feedback',episode_id='continual_stream',source_id=published['path'],
        source_sha256=published['sha256'],origin='TRAIN_COLLECTION')
    return expected in resume['state']['history']['events'] and dict(role='user',content=expected['text']) in body['messages']
report=dict(schema='R159_READ_ONLY_SERVICE_OBSERVATION_V1',host=os.uname().nodename,
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=[],results=[],failures=[])
assert report['host']=='[REDACTED_HOST]'
if options['first']:
    unused,reference=read(base/'orch_r159_train_service.py',131072)
    assert reference['sha256']=='dd8ed5a733b5631347605b2b4415cf5eb3531c8ebe93860e5522314afd4a8b1b'
    report['service_source']=reference
lock_raw,_=read('/proc/locks',131072)
for arm,pid,config_hash in [('parented_learning',582687,'5309535519f3834d5f618ef0dc6fcb7ea8787e22648ad6ceed86ec73d0685a9d'),
    ('unparented_learning',582691,'3ba9c1a6bae6550b80f140f3eb3d93035c11363c150bdb488df8110393321e1c'),
    ('parented_frozen',722599,'217e1b3eea20173918960ca801ca04202a11b2d0547249ef216f1b9e86d00991')]:
    root=campaign/arm; config,config_ref=document(base/(arm+'.CONFIG.json'),options['first'])
    assert config_ref['sha256']==config_hash and config['root']==str(root) and config['deadline_unix']==1789644600
    prior=options['arms'].get(arm,dict(next_index=0,previous='0'*64,seen_results=[],feedback={},exposed=[]))
    prior.setdefault('followups',{})
    prior.setdefault('continuation_done',[])
    if arm=='parented_learning': prior['followups'].setdefault('74',str(root/'train_environment/task_000000/answer_00000000000000000067/RESULT.json'))
    if arm=='unparented_learning':
        prior['followups'].setdefault('72',str(root/'train_environment/task_000000/answer_00000000000000000066/RESULT.json'))
        prior['followups']['132']=str(root/'train_environment/task_000000/answer_00000000000000000073/RESULT.json')
    summary=dict(arm=arm,root=str(root),pid=pid,config=config_ref,events=[])
    process_path=pathlib.Path('/proc')/str(pid)
    summary['process_exists']=process_path.exists()
    if summary['process_exists']:
        command,_=read(process_path/'cmdline',16384)
        summary['command']=command.replace(b'\0',b' ').decode()
        assert str(base/'orch_r159_train_service.py') in summary['command'] and str(base/(arm+'.CONFIG.json')) in summary['command']
    lock_inode=(root/'train_service_r159/OWNER.lock').stat().st_ino
    summary['owner_lock_observed']=any(' FLOCK ' in line and f' {pid} ' in line and f':{lock_inode} ' in line for line in lock_raw.decode().splitlines())
    newest=None
    for unused in range(512):
        path=root/'train_service_r159'/f"{prior['next_index']:08d}.json"
        if not path.exists(): break
        event,event_ref=document(path)
        assert event['schema']=='R159_TRAIN_SERVICE_EVENT_V1' and event['index']==prior['next_index']
        assert event['previous_sha256']==prior['previous'] and event['sha256']==digest({key:value for key,value in event.items() if key!='sha256'})
        assert event['state']['config_sha256']==digest(config)
        prior.update(next_index=event['index']+1,previous=event['sha256'])
        newest=event
        if event['kind'] not in ('POLL','BUDGET_RESERVED','CURSOR_CONSUMED'):
            summary['events'].append(dict(reference=event_ref,kind=event['kind'],details=event['details'],state=event['state']))
        state=event['state']
        if event['kind']=='OWN_RESPONSE_EXPOSED' and event['details']['response_index'] not in prior['exposed']:
            response_index=event['details']['response_index']; prior['exposed'].append(response_index)
            task,message,published,refs=publication(root,pathlib.Path(state['task']['source']['path']))
            requested,request_ref=record(root,response_index-1)
            assert rendered(requested,message,published)
            summary.setdefault('actual_task_renderings',[]).append(dict(task_index=state['task_index'],response_index=response_index,request=request_ref,task=refs[0]))
        if state.get('feedback'):
            prior['feedback'][str(state['task_index'])]=state['feedback']
        if event['kind']=='FEEDBACK_ACTUALLY_RENDERED':
            evidence=prior['feedback'][str(state['task_index'])]
            result,message,published,refs=publication(root,pathlib.Path(evidence['source']['path']),True)
            requested,request_ref=record(root,state['cursor']-1,True)
            assert rendered(requested,message,published)
            summary.setdefault('actual_feedback_renderings',[]).append(dict(task_index=state['task_index'],request=request_ref,receipt=refs[0]))
            prior['followups'][str(state['cursor']-1)]=evidence['source']['path']
        if event['kind']=='ACTION_COMPLETE' and event['details'].get('action')=='check' and state.get('feedback'):
            result_path=pathlib.Path(state['feedback']['source']['path'])
            if str(result_path) in prior['seen_results']: continue
            prior['seen_results'].append(str(result_path))
            result,message,published,refs=publication(root,result_path,True)
            response_index=result['origin']['response_index']; triple=[record(root,index,True) for index in (response_index-1,response_index,response_index+1)]
            request,response,committed=[pair[0] for pair in triple]
            assert [value['kind'] for value in (request,response,committed)]==['REQUEST','RESPONSE','COMMITTED']
            for previous,following in ((request,response),(response,committed)):
                assert following['journal_id']==previous['journal_id']==state['identity']['journal_id'] and following['previous_sha256']==previous['sha256']
            requested={key:value for key,value in request['document'].items() if key!='resume_state'}
            assert requested['split']=='TRAIN' and response['document']['request_sha256']==digest(requested)
            assert committed['document']['source_sha256']==digest(response['document'])
            generation=response['document']['response']; checkpoint=committed['document']['state']
            assert checkpoint['sha256']==digest(checkpoint['state'])
            row=checkpoint['state']['rows'][-1]
            assert row['actor']=='child' and row['split']=='TRAIN' and row['target']==generation['raw'] and row['token_ids']==generation['token_ids']
            assert row['prefix']==requested['messages'] and row['prefix_loss'] is False and row['target_loss'] is True
            assert result['origin']==dict(response_index=response_index,response_sha256=response['sha256'],commit_sha256=committed['sha256'])
            assert result['schema']=='R158_TRAIN_GYM_RESULT_V1' and result['split']=='TRAIN' and math.isfinite(result['score'])
            assert result['accepted'] is (result['score']==1.0)
            task,task_message,task_published,task_refs=publication(root,result_path.parent.parent/'TASK.json',True)
            assert result['task_id']==task['task_id'] and result['binding']==task['binding'] and rendered(request,task_message,task_published)
            intent,intent_ref=document(result_path.parent/'INTENT.json',True)
            assert intent==dict(response_index=response_index,response_sha256=response['sha256'],generated_sha256=hashlib.sha256(generation['raw'].encode()).hexdigest(),answer=result['answer'],task_sha256=task_refs[0]['sha256'],replay_allowed=False)
            report['results'].append(dict(root=str(root),task_index=state['task_index'],task_id=result['task_id'],response_index=response_index,
                accepted=result['accepted'],score=result['score'],qualifying_own_complete=generation['terminal'] is True and generation['truncated'] is False,
                result=refs[0],publication=refs[1],message=refs[2],intent=intent_ref,triple=[pair[1] for pair in triple],task=task_refs[0]))
        if event['kind']=='TERMINAL': report['failures'].append(dict(root=str(root),terminal=state['terminal'],event=event_ref))
    if newest:
        summary['latest']=dict(index=newest['index'],kind=newest['kind'],state=newest['state'])
    for request_index,result_path in prior['followups'].items():
        if request_index in prior['continuation_done']: continue
        index=int(request_index)
        if not (root/'stream/records'/f'{index+2:020d}.json').exists(): continue
        request,request_ref=record(root,index,True)
        assert request['kind']=='REQUEST' and request['document']['split']=='TRAIN'
        response,response_ref=record(root,index+1,True)
        committed,commit_ref=record(root,index+2,True)
        assert response['kind']=='RESPONSE' and committed['kind']=='COMMITTED'
        assert response['previous_sha256']==request['sha256'] and committed['previous_sha256']==response['sha256']
        requested={key:value for key,value in request['document'].items() if key!='resume_state'}
        assert response['document']['request_sha256']==digest(requested) and committed['document']['source_sha256']==digest(response['document'])
        checkpoint=committed['document']['state']; assert checkpoint['sha256']==digest(checkpoint['state'])
        row=checkpoint['state']['rows'][-1]; generation=response['document']['response']
        assert row['split']=='TRAIN' and row['actor']=='child' and row['target']==generation['raw'] and row['token_ids']==generation['token_ids']
        assert row['prefix']==requested['messages'] and row['prefix_loss'] is False and row['target_loss'] is True
        outcome,message,published,refs=publication(root,pathlib.Path(result_path),True)
        assert rendered(request,message,published)
        summary.setdefault('post_feedback_continuations',[]).append(dict(result=refs[0],accepted_anchor=outcome['accepted'],
            request=request_ref,response=response_ref,committed=commit_ref,target_sha256=hashlib.sha256(generation['raw'].encode()).hexdigest(),
            terminal=generation['terminal'],truncated=generation['truncated'],semantic_reflection_review=False,eligibility_claim=False))
        prior['continuation_done'].append(request_index)
    if not summary['process_exists'] or not summary['owner_lock_observed']:
        report['failures'].append(dict(root=str(root),process_exists=summary['process_exists'],owner_lock_observed=summary['owner_lock_observed']))
    summary['cursor']=prior; report['arms'].append(summary)
report['read_bytes']=consumed; report['artifacts']=list(artifacts.values())
print(json.dumps(report,sort_keys=True,separators=(',',':')))
'''


def save(path, raw):
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fchmod(output.fileno(), 0o400)
        os.fsync(output.fileno())


def main():
    DIRECTORY.mkdir(mode=0o700, exist_ok=True)
    previous = sorted(DIRECTORY.glob('POLL_*.json'))
    state = json.loads(previous[-1].read_bytes()) if previous else dict(total_bytes=131072, arms={}, next_poll_unix=0)
    wait = max(0, state['next_poll_unix']-time.time())
    if wait:
        assert time.time()+wait<DEADLINE, 'no_observer_extension'
        time.sleep(wait)
    assert time.time()<DEADLINE, '20_minute_observer_wall'
    remaining=LIMIT-state['total_bytes']
    assert remaining>1048576, '64MiB_observer_budget'
    options=dict(first=not previous or state.get('returncode')!=0, arms=state['arms'], allowance=min(4*1024**2,remaining//3))
    started=time.time()
    completed=subprocess.run(['bash','gpu/a40r_ssh.sh','python3','-B','-',shlex.quote(json.dumps(options))],
        input=REMOTE.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(25,DEADLINE-time.time()))
    assert len(completed.stdout)+len(completed.stderr)<8*1024**2, 'bounded_transport'
    poll=dict(schema='R159_IMMUTABLE_LOCAL_OBSERVATION_V1',started_unix=started,finished_unix=time.time(),
        returncode=completed.returncode,stdout_sha256=hashlib.sha256(completed.stdout).hexdigest(),
        stderr=completed.stderr.decode()[:8192],next_poll_unix=started+15,arms=state['arms'])
    poll['total_bytes']=state['total_bytes']+len(completed.stdout)+len(completed.stderr)
    if completed.returncode==0:
        report=json.loads(completed.stdout)
        poll['report']=report
        poll['arms']={item['arm']:item['cursor'] for item in report['arms']}
        poll['total_bytes']+=report['read_bytes']
    else:
        poll['stdout']=completed.stdout.decode()[:8192]
        poll['total_bytes']+=options['allowance']
    raw=(json.dumps(poll,sort_keys=True,separators=(',',':'))+'\n').encode()
    path=DIRECTORY/f'POLL_{len(previous):04d}.json'
    save(path,raw)
    summary=dict(receipt=str(path),sha256=hashlib.sha256(raw).hexdigest(),returncode=completed.returncode,total_bytes=poll['total_bytes'])
    if 'report' in poll:
        report=poll['report']; summary.update(at=report['observed_utc'],results=report['results'],failures=report['failures'],
            arms=[dict(arm=arm['arm'],process_exists=arm['process_exists'],owner_lock_observed=arm['owner_lock_observed'],
                latest={key:arm.get('latest',{}).get('state',{}).get(key) for key in ('offers','exposures','checked','check_calls','cursor','terminal')},
                rendered=arm.get('actual_task_renderings',[]),feedback_rendered=arm.get('actual_feedback_renderings',[]),
                post_feedback_continuations=arm.get('post_feedback_continuations',[])) for arm in report['arms']])
    else: summary['error']=poll['stderr']
    print(json.dumps(summary,sort_keys=True))
    if poll.get('report',{}).get('results') or poll.get('report',{}).get('failures'):
        return 2
    return 0 if completed.returncode==0 else 1


if __name__=='__main__':
    raise SystemExit(main())
