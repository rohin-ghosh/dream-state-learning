"""Node-side compact measurement; never exports child or provider raw text."""

import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


def read(path):
    return json.loads(path.read_text())


def reference(path):
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def collect(root,lane):
    campaign=root/('campaign_'+lane)
    now=time.time()
    result=dict(lane=lane,root=str(root),observed_utc=datetime.fromtimestamp(now,timezone.utc).isoformat(),raw_embedded=False)
    for name in ('READY.json','LAUNCH.json','ACTOR_READY.json','STATUS.json','COMPLETE.json','TERMINAL.json','FAILED.json'):
        path=campaign/name
        if path.exists():
            value=read(path)
            result[name]={key:value[key] for key in ('pid','lane','uuid','started_unix','loaded_unix','phase','native_completed',
                'parent_completed','train_segments','train_episodes','held_episodes','sleeps','optimizer_updates','triples',
                'hard_deadline_unix','native_cap','parent_cap','base_sha256','principles_sha256','status') if key in value}
            result[name].update(reference(path))
            if 'error' in value:
                result[name]['error_type']=value['error']['type']
    counts=Counter()
    window=Counter()
    first=None
    for path in sorted((campaign/'native').glob('CALL_*.json')):
        value=read(path)
        counts['reserved']+=1
        if value.get('status')!='COMPLETE':
            counts[value.get('status','PENDING')]+=1
            continue
        response=value['response']
        raw=response['raw']
        protocol_only=bool(re.fullmatch(r'(?:ROUTE \S+|READ EVENT \S+|EVENT \S+ AT \S+ DID \S+ GOT \S+ EVIDENCE \S+)\s*',raw))
        values={'completed':1,'tokens_including_eos':len(response['token_ids']),
            'protocol_only_structural':int(protocol_only),'truncated':int(response['truncated']),
            'reflection':int(value['purpose']=='reflection'),
            'reflection_lexical_stop':int(bool(response.get('reflection_guard',{})) and
                response['reflection_guard'].get('stop_reason')=='repetition')}
        counts.update(values)
        if value['finished_unix']>=now-600:
            window.update(values)
        if first is None:
            first=dict(reference(path),started_unix=value['started_unix'],finished_unix=value['finished_unix'],
                tokens_including_eos=len(response['token_ids']),full_prompt_prefix_verified=response['full_prompt_prefix_verified'],
                input_truncated=response['input_truncated'])
    result['native_counts']=dict(counts)
    result['first_native']=first
    duration=min(600,max(0,now-first['started_unix'])) if first else 0
    result['throughput_600s']=dict(window,observed_seconds=duration,full_600s_available=duration>=600,
        raw_calls_per_hour=3600*window['completed']/duration if duration else None,
        qualified_functional_count=None,qualified_functional_per_hour=None,semantic_sample_denominator=0)
    parents=sorted(campaign.glob('PARENT_*.json'))
    result['parent_responses']=len(parents)
    modes=Counter()
    classes=Counter()
    first_parent=None
    for path in parents:
        value=read(path)
        modes[value.get('mode','UNKNOWN')]+=1
        archive=Path(value['archive']['remote_root'])
        complete=read(archive/'COMPLETE.json')
        plan=read(archive/'PLAN.json')
        rationale=plan['rationale'].lower()
        for name in ('perception','persistence','metacognition','curiosity','goal','reflection','action steering','affective'):
            classes[name]+=int(name in rationale)
        if first_parent is None:
            first_parent=dict(reference(path),observed_unix=value['observed_unix'],
                provider_finished_unix=complete['finished_unix'],actual_model=complete['actual_primary_model'],
                response_sha256=value['response_sha256'],raw_response_sha256=complete['raw_response_sha256'],
                principles_sha256=value['principles_sha256'])
    result['first_parent']=first_parent
    result['parent_modes']=dict(modes)
    result['intervention_class_text_mentions_not_semantic_verification']=dict(classes)
    result['triples_retained']=len(list((campaign/'triples').glob('*.json')))
    result['behavior_add_stop_shift_verified']=None
    result['behavior_audit_status']='UNKNOWN_PENDING_AUTHOR_AUDIT_NO_OUTCOME_CRITERION'
    sleeps=[]
    for path in sorted((campaign/'sleeps').glob('*/COMPLETE.json')):
        value=read(path)
        sleeps.append(dict(reference(path),**{key:value[key] for key in ('optimizer_updates','before_adapter_sha256',
            'after_adapter_sha256','inherited_step','final_step','finished_unix','no_optimizer_reset')}))
    result['learned_sleeps']=sleeps
    process_rows=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    uuid=result.get('LAUNCH.json',{}).get('uuid')
    result['current_compute_pids']=[int(line.split(',')[1]) for line in process_rows.splitlines() if line.split(',')[0].strip()==uuid]
    result['observer_does_not_change_gpu_or_source']=True
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--lane',required=True)
    args=parser.parse_args()
    print(json.dumps(collect(args.root,args.lane),sort_keys=True))
