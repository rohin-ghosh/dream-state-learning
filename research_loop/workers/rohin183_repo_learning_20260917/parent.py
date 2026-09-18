"""One finite local Astra parent using existing provider and attributed console."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from gpu.orch_r133_programme_parent import prompt,publish
from gpu.orch_route_parent_campaign_providers import strong,STRONG
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest,require


ROOT=Path(__file__).resolve().parent
REPOSITORY=ROOT.parents[2]


def should_call(responses,last_response,calls,last_call,now,pending):
    return not pending and calls<12 and responses>=max(1,last_response+3 if calls else 1) and now-last_call>=300


def serve():
    config=json.loads((ROOT/'PARENT_CONFIG.json').read_bytes())
    require(config['schema']=='R183_BOUNDED_ASTRA_PARENT_V1' and config['node']=='ovx' and config['maximum_calls']==12,'one_bounded_ovx_parent')
    for key in ('programme','principles'):
        require(digest(Path(config[key+'_path']).read_bytes())==config[key+'_sha256'],'pinned_parent_'+key)
    feed=(ROOT/'parent_feed.py').read_text()
    require(digest(feed.encode())==config['feed_sha256'],'pinned_incremental_feed')
    require(bool(os.environ.get('NVIDIA_API_KEY')),'existing_private_parent_key_required')
    output=ROOT/'parent1'
    output.mkdir(mode=0o700)
    write(output/'STARTED.json',dict(pid=os.getpid(),started_unix=time.time(),model=STRONG,
        config_sha256=digest((ROOT/'PARENT_CONFIG.json').read_bytes()),maximum_calls=12,
        maximum_provider_output_tokens=12*4096,provider_key_present=True,provider_key_exported=False,
        actual_provider_calls=0,formal_R184_driver=False))
    state=dict(cursor=0,previous=None,journal_id=None,waiting=None)
    events=[]
    responses=calls=last_response=0
    last_call=0
    pending=None
    while time.time()+125<config['hard_end_unix']:
        argument=shlex.quote(json.dumps(state,separators=(',',':')))
        command=['bash',str(REPOSITORY/'gpu/ovx_ssh.sh'),'python3 -B - '+argument]
        try:
            result=subprocess.run(command,input=feed,text=True,capture_output=True,timeout=45)
            require(result.returncode==0,'TRAIN_feed_transport_failed_no_retry')
            snapshot=json.loads(result.stdout)
            if not snapshot['ready']:
                time.sleep(10)
                continue
            responses+=snapshot['new_responses']
            events=(events+snapshot['events'])[-8:]
            state.update({key:snapshot[key] for key in ('cursor','previous','journal_id')})
            if state['waiting'] and snapshot['waiting_registered']:
                state['waiting']['registered']=True
            if pending and snapshot['rendered']:
                write(pending/'RENDERED.json',dict(observed_unix=time.time(),**snapshot['rendered']))
                state['waiting']=None
                pending=None
            now=time.time()
            if should_call(responses,last_response,calls,last_call,now,pending):
                directory=output/f'call_{calls:03d}'
                directory.mkdir()
                calls+=1
                last_response=responses
                last_call=now
                view=dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',events=events)
                instruction,payload=prompt(config,view)
                write(directory/'SOURCE.json',dict(**view,response_count=responses,cursor=state['cursor'],head_sha256=state['previous']))
                write(directory/'INTENT.json',dict(started_unix=now,call_number=calls,retry=False,model=STRONG,
                    parent_source_sha256=digest(Path(__file__).read_bytes())))
                response,model,usage=strong(payload,directory,min(config['hard_end_unix'],now+125),instruction,reasoning_effort='medium')
                write(directory/'RESPONSE.json',dict(response=response,actual_model=model,usage=usage,finished_unix=time.time()))
                if response['speak']:
                    write(directory/'PUBLISH_INTENT.json',dict(message_sha256=digest(response['message'].encode()),issued_unix=time.time(),no_retry=True))
                    publication=publish(REPOSITORY,config,response['message'])
                    write(directory/'PUBLICATION.json',dict(publication=publication,published_unix=time.time(),model=model,
                        rendered_verified=False))
                    state['waiting']=dict(id=publication['id'],message=response['message'],registered=False)
                    pending=directory
                else:
                    write(directory/'SILENT.json',dict(completed_unix=time.time()))
            if calls>=12 and not pending:
                break
            time.sleep(10)
        except BaseException as error:
            write(output/'STOPPED_NO_RETRY.json',dict(observed_unix=time.time(),error_type=type(error).__name__,
                error=str(error)[:500],calls_reserved=calls,pending_publication=pending is not None))
            raise
    write(output/'EXIT.json',dict(finished_unix=time.time(),calls_reserved=calls,reason='bounded_budget_or_wall'))


if __name__=='__main__':
    serve()
