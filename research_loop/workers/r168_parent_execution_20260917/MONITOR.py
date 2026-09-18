"""Bounded read-only R168 adopted-parent phases. No restart or publication."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files


STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
OUTPUT=STAGE/'OBSERVATIONS'
MANUAL=ROOT/'research_loop/workers/r168_community_prompt_final_20260917'
PRIOR=ROOT/'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2'
DEADLINE=1789636920
MARKER='R168_FINAL_R154_TWO_BOUNDARY_TEACHING_V2'


def ref(path):
    return dict(path=str(path.resolve()),sha256=files.sha(path))


def phases():
    results=[]
    for branch in ('C2','C3','C4'):
        receipts=STAGE/'ROLLOUT'/branch
        started=json.loads(files.read_file(receipts/'STARTED.json'))
        observed=files.identity(started['successor']['pid'])
        assert observed['start_ticks']==started['successor']['start_ticks'] and observed['argv']==started['command']
        transfer=json.loads(files.read_file(receipts/'LEDGER_TRANSFER.json'))
        inherited={entry['attempt'] for entry in transfer['attempts']}
        output=Path(started['output'])
        fresh=[]
        for attempt in sorted(output.glob('parent_*')):
            if attempt.name in inherited:continue
            entry=dict(attempt=attempt.name)
            for name in ('SOURCE.json','PROMPT.json','RESULT.json','DELIVERED.json'):
                path=attempt/name
                if not path.exists():continue
                document=json.loads(files.read_file(path))
                entry[name]=ref(path)
                if name=='SOURCE.json':entry['response_count']=document['response_count']
                elif name=='PROMPT.json':
                    entry['new_policy_present']=MARKER in document['instruction']
                    entry['final_policy_precedence']=document['instruction'].rfind(MARKER)>document['instruction'].rfind('silence is useful')
                elif name=='RESULT.json':
                    entry.update(status=document['status'],publication=document.get('publication'),
                        message=document.get('message'),rationale=document.get('rationale'),error_type=document.get('error_type'))
                else:
                    result=json.loads(files.read_file(attempt/'RESULT.json'))
                    assert document['result_sha256']==files.sha(attempt/'RESULT.json')
                    assert document['publication']==result['publication'] and document['status']=='RENDERED'
                    assert document['rendered']['inbox_sha256']==result['publication']['sha256']
                    assert document['rendered']['text_sha256']==hashlib.sha256(result['message'].encode()).hexdigest()
                    entry['rendered']=document
            fresh.append(entry)
        log=receipts/'PARENT.log'
        assert log.stat().st_size<=2097152
        results.append(dict(branch=branch,parent=observed,reserved_response_count=transfer['reserved_response_count'],
            next_due_response_count=max([transfer['reserved_response_count']]+[entry.get('response_count',0) for entry in fresh])+2,
            fresh_attempts=fresh,log_tail=log.read_text()[-2000:]))
    return results


def tail_counts():
    source_path=PRIOR/'OBSERVE.py'
    tree=ast.parse(files.read_file(source_path))
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='tail_counts')
    assignment=next(node for node in function.body if isinstance(node,ast.Assign)
                    and any(isinstance(target,ast.Name) and target.id=='script' for target in node.targets))
    template=assignment.value.func.value.value
    assert type(template) is str and 'children=CHILDREN' in template
    children={branch:json.loads(files.read_file(STAGE/'ROLLOUT'/branch/'OPERATIONAL_GO.json'))['child']['child']
              for branch in ('C2','C3','C4')}
    config=json.loads(files.read_file(STAGE/'C2/CONFIG.json'))
    result=parent.remote(STAGE/'local_source',config,template.replace('CHILDREN',repr(children)))
    result['reader_source']=ref(source_path)
    return result


def main():
    OUTPUT.mkdir(mode=0o700)
    community.write(OUTPUT/'STARTED.json',dict(pid=os.getpid(),started_unix=time.time(),deadline_unix=DEADLINE,
        source=ref(Path(__file__)),no_signals=True,no_provider_calls=True,no_publications=True,
        local_interval_seconds=20,remote_interval_seconds=180,manual_interval_seconds=120,
        manual_source_read_budget=268435456))
    last_tail=0
    last_manual=0
    manual_bytes=0
    last_manual_report=None
    latest=None
    status='BOUNDED_OBSERVER_COMPLETE_NO_RENDER_INFERENCE'
    for index in range(128):
        if time.time()>=DEADLINE or (OUTPUT/'STOP_OBSERVER').exists():break
        report=dict(observed_unix=time.time())
        try:
            report['parents']=phases()
            if time.time()-last_tail>=180:
                try:report['tail_counts']=tail_counts()
                except Exception as error:report['tail_error']=dict(type=type(error).__name__,message=str(error))
                last_tail=time.time()
            if (time.time()-last_manual>=120 and manual_bytes+134217728<=268435456
                    and (last_manual_report is None or last_manual_report['status']!='RENDERED')):
                result=subprocess.run([sys.executable,'-B',str(MANUAL/'OBSERVE_MANUAL.py')],cwd=ROOT,
                    env=dict(os.environ,PYTHONPATH=str(ROOT)),capture_output=True,text=True,timeout=50)
                if result.returncode:
                    report['manual_observer_error']=dict(exit_code=result.returncode,stderr=result.stderr[-2000:])
                else:
                    document=json.loads(result.stdout)
                    manual_bytes+=document['observation']['bytes_read_this_poll']
                    last_manual_report=dict(status=document['observation']['status'],receipt=dict(path=document['path'],sha256=document['sha256']),
                        observed_unix=document['observation']['observed_unix'],actual_read_bytes_this_observer=manual_bytes)
                    report['manual_observation']=last_manual_report
                last_manual=time.time()
        except Exception as error:
            report['observer_error']=dict(type=type(error).__name__,message=str(error),not_parent_failure=True)
        path=OUTPUT/f'OBSERVATION_{index:04d}.json'
        community.write(path,report)
        latest=ref(path)
        rendered=[dict(branch=entry['branch'],attempt=attempt['attempt'],rendered=attempt['rendered'])
            for entry in report.get('parents',[]) for attempt in entry['fresh_attempts']
            if attempt.get('rendered') and attempt.get('new_policy_present') and attempt.get('final_policy_precedence')]
        print(json.dumps(dict(observed_unix=report['observed_unix'],receipt=latest,rendered=rendered,
            manual=report.get('manual_observation'),phases={entry['branch']:[dict(attempt=attempt['attempt'],
            status=attempt.get('status'),marker=attempt.get('new_policy_present'),rendered=bool(attempt.get('rendered')))
            for attempt in entry['fresh_attempts']] for entry in report.get('parents',[])})),flush=True)
        if rendered and not (OUTPUT/'FIRST_RENDERED.json').exists():
            community.write(OUTPUT/'FIRST_RENDERED.json',dict(observed_unix=time.time(),source=latest,rendered=rendered,
                claim='actual_parent_reported_REQUEST_rendering_not_learning_or_floor_compliance'))
        if len({entry['branch'] for entry in rendered})==3:
            status='THREE_ADOPTED_PARENTS_HAVE_NEW_RENDERED_TURNS'
            break
        time.sleep(max(0,min(20,DEADLINE-time.time())))
    community.write(OUTPUT/'TERMINAL.json',dict(status=status,finished_unix=time.time(),latest=latest,
        last_manual_observation=last_manual_report,actual_manual_source_read_bytes=manual_bytes,no_parent_or_native_changes=True))


if __name__=='__main__':
    main()
