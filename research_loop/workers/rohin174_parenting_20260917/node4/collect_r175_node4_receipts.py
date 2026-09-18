"""Bounded read-only parent exposure, child identity, and environment evidence."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('node4_receipt_base', HOME / 'r175_node4_operator.py')
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
ACTIVATION = HOME / 'activation_20260917T2057Z'
WITHDRAWAL_SHA = 'da4145a7f976d47f63c4af3ddc2ec72056a76706be79e7325f261eda442e7217'
STAGES = {
    0: '/localhome/local-rohing/orch_r179_node4_20260917t1814z/lane0',
    1: '/localhome/local-rohing/orch_r179_node4_20260917t1810z/lane1',
    3: '/localhome/local-rohing/orch_r179_node4_recovery_20260917t2000z/lane3',
    4: '/localhome/local-rohing/orch_r179_node4_20260917t1810z/lane4',
}


def latest(output, pattern):
    for path in sorted(output.glob(pattern), reverse=True):
        try:
            return path, base.read(path)
        except json.JSONDecodeError:
            continue
    raise ValueError('no_complete_snapshot:' + str(output))


def render_binding(publication, snapshot):
    delivered = snapshot['delivered'].get(publication['publication']['id'])
    if delivered is None:
        return None
    base.require(snapshot['split'] == 'TRAIN' and delivered['speaker'] == 'Astra'
        and delivered['inbox_sha256'] == publication['publication']['sha256']
        and delivered['text_sha256'] == publication['message_sha256'], 'exact_actual_rendered_publication')
    return dict(delivered, journal_id=snapshot['journal_id'])


def parent_rows():
    rows = []
    for physical in (0, 1, 3, 4):
        lane = ACTIVATION / f'physical{physical}'
        output = lane / 'parent'
        poll_path, poll = latest(output, 'POLL_*.json')
        snapshot = poll['snapshot']
        status_path, status = latest(output, 'STATUS_*.json')
        started = base.read(output / 'STARTED.json')
        try:
            actor = base.identity(started['pid'])
            base.same_parent(started['actor'], actor)
            live = True
        except (FileNotFoundError, ProcessLookupError, ValueError):
            live, actor = False, None
        publications = []
        for path in sorted(output.glob('PUBLICATION_*_RECEIPT.json')):
            receipt = base.read(path)
            intent = base.read(path.with_name(path.name.replace('_RECEIPT', '_INTENT')))
            base.require(receipt['message_sha256'] == intent['message_sha256'], 'publication_intent_receipt_binding')
            rendered = render_binding(receipt, snapshot)
            publications.append(dict(receipt=receipt, path=str(path), sha256=base.sha(path), words=intent['words'],
                rendered=rendered, completed_sleeps_since_exposure=(snapshot['sleep_count'] - rendered['sleep_count'])
                    if rendered else None,
                third_sleep_target=rendered['sleep_count'] + 3 if rendered else None,
                fourth_sleep_target=rendered['sleep_count'] + 4 if rendered else None,
                withdrawal_completion_not_inferred=True))
        base.require(physical != 1 or len(publications) <= 1, 'H_exactly_one_published_total')
        evidence = [dict(record_index=event['record_index'], record_sha256=event['record_sha256'],
            commit_record_index=event.get('commit_record_index'), commit_record_sha256=event.get('commit_record_sha256'),
            quote=event['text'][:240]) for event in snapshot['events'] if event['actor'] == 'child'][-2:]
        rows.append(dict(physical=physical, arm=base.ARMS[physical], root=base.ROOTS[physical],
            parent_live=live, parent_actor=actor, parent_status=status['status'],
            status_observed_unix=status['observed_unix'], status_path=str(status_path),
            snapshot_path=str(poll_path), snapshot_sha256=base.sha(poll_path),
            snapshot_head_sha256=snapshot['head_sha256'], request_count=snapshot['request_count'],
            response_count=snapshot['response_count'], completed_sleep_count=snapshot['sleep_count'],
            publication_count=len(publications), publications=publications, peer_pair=None,
            own_committed_TRAIN_evidence=evidence, executor_available_not_claimed=True,
            new_parent_turns_withheld=status.get('new_parent_turns_withheld', False)))
    return rows


def remote_metadata(rows):
    requests = [dict(root=row['root'], **publication['rendered']) for row in rows
        for publication in row['publications'] if publication['rendered']]
    script = '''import hashlib,json,os,time
from pathlib import Path
def read(path):
    path=Path(path)
    assert not path.is_symlink() and path.is_file() and path.stat().st_size<=16*1024*1024
    return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def actor(pid):
    root=Path('/proc',str(pid))
    before=(root/'stat').read_text().rsplit(')',1)[1].split()
    argv=[part.decode() for part in (root/'cmdline').read_bytes().split(b'\\0') if part]
    after=(root/'stat').read_text().rsplit(')',1)[1].split()
    assert before[19]==after[19]
    return dict(pid=pid,start_ticks=after[19],argv=argv,cwd=str((root/'cwd').resolve()),uid=root.stat().st_uid,state=after[0])
children=[]
for physical,stage in stages.items():
    loaded=read(Path(stage)/'LOADED_RECEIPT.json')
    expected=loaded['actor']
    try:
        actual=actor(expected['pid'])
        live=all(actual[key]==expected[key] for key in ('pid','start_ticks','argv','cwd','uid')) and actual['state'] not in ('Z','X')
    except (FileNotFoundError,ProcessLookupError):
        actual,live=None,False
    guard_path=Path(stage)/'control/GUARD.json'
    guard=read(guard_path)
    assert sha(guard['plan_path'])==guard['plan_sha256']
    plan=read(guard['plan_path'])
    assert plan['physical']==physical and plan['root']==roots[physical] and guard['hard_end_unix']==wall
    children.append(dict(physical=physical,identity_live=live,actor=actual,loaded=loaded,
        loaded_receipt_path=str(Path(stage)/'LOADED_RECEIPT.json'),loaded_receipt_sha256=sha(Path(stage)/'LOADED_RECEIPT.json'),
        handoff_complete=read(Path(stage)/'HANDOFF_COMPLETE.json') if (Path(stage)/'HANDOFF_COMPLETE.json').exists() else None,
        plan_path=guard['plan_path'],plan_sha256=guard['plan_sha256'],
        runtime_caps={key:plan[key] for key in ('context_limit','segment_tokens','segments_per_sleep','new_presentations','rehearsal_presentations','hard_end_unix')},
        explicit_tool_manifest_fields={key:value for key,value in plan.items() if 'tool' in key or 'executor' in key}))
matches=[]
inaccessible=0
tokens=('orch_r132_kernel_bridge','orch_r141_kernel','orch_r148_kernel','orch_r155_kernel','orch_r158_kernel_execution')
for root in Path('/proc').iterdir():
    if root.name.isdigit():
        try:
            if root.stat().st_uid!=2524: continue
            argv=(root/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
            if any(token in argv for token in tokens): matches.append(dict(pid=int(root.name),argv=argv[:2000]))
        except (FileNotFoundError,ProcessLookupError): pass
        except PermissionError: inaccessible+=1
rendered=[]
for reference in requests:
    assert reference['root'] in roots.values()
    path=Path(reference['root'])/'stream/records'/f"{reference['record_index']:020d}.json"
    record=read(path)
    digest=hashlib.sha256(json.dumps({key:value for key,value in record.items() if key!='sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert record['kind']=='REQUEST' and record['document']['split']=='TRAIN' and record['sha256']==digest==reference['record_sha256']
    assert record['index']==reference['record_index'] and record['journal_id']==reference['journal_id']
    started=record['document'].get('started_unix')
    assert isinstance(started,(int,float)) and not isinstance(started,bool)
    rendered.append(dict(reference=reference,request_started_unix=started,record_path=str(path),record_file_sha256=sha(path)))
proofs=[]
proof_root=Path('/localhome/local-rohing/orch_r179_node4_proof_20260917t2006z')
for physical,pid in ((0,279649),(1,279651),(3,279653),(4,279654)):
    path=proof_root/f'WATCH_{physical}.jsonl'
    assert path.stat().st_size<=1024*1024
    lines=path.read_text().splitlines()
    try: process=actor(pid)
    except (FileNotFoundError,ProcessLookupError): process=None
    proofs.append(dict(physical=physical,latest=json.loads(lines[-1]) if lines else None,observer_actor=process,
        path=str(path),file_sha256=sha(path)))
print(json.dumps(dict(observed_unix=time.time(),children=children,rendered_requests=rendered,
    retained_sleep_proof_monitors=proofs,
    kernel_service_scan=dict(scope='known_R132_R141_R148_R155_R158_argv_for_UID2524_only',matches=matches,inaccessible_processes=inaccessible,
        historical_R158_PIDs_present={str(pid):Path('/proc',str(pid)).exists() for pid in (4042560,4048159,4048160)}),
    model_calls=0,signals_sent=0,journal_writes=0,sealed_output_reads=0)))
'''
    return base.ssh(f'stages={STAGES!r}\nroots={base.ROOTS!r}\nwall={base.WALL!r}\nrequests={requests!r}\n' + script)


def apply_control_withdrawal(rows, withdrawal):
    base.require(withdrawal['status'] == 'WITHDRAWN_BEFORE_INGESTION'
        and withdrawal['root'] == base.ROOTS[1] and withdrawal['native_pid'] == 294158
        and withdrawal['native_start_ticks'] == '24386173' and withdrawal['native_resumed'] is True
        and withdrawal['native_restart'] is False and withdrawal['adapter_optimizer_rng_untouched'] is True,
        'exact_Main_unconsumed_control_withdrawal')
    control = next(row for row in rows if row['physical'] == 1)
    base.require(control['parent_live'] is False, 'H_operator_must_remain_off')
    publications = control['publications']
    base.require(len(publications) == 1, 'only_one_historical_H_publication')
    publication = publications[0]
    base.require(publication['receipt']['publication']['id'] == withdrawal['inbox_id']
        and publication['receipt']['publication']['sha256'] == withdrawal['publication_sha256']
        and publication['rendered'] is None, 'withdrawal_exact_publication_not_exposure')
    publication['current_delivery_disposition'] = 'WITHDRAWN_BEFORE_INGESTION'
    control.update(last_parent_runtime_status=control['parent_status'],
        parent_status='OFF_WITHDRAWN_BEFORE_INGESTION', current_policy='UNPARENTED_PENDING_ROHIN',
        historical_publication_count=control['publication_count'], current_pending_publications=0,
        actual_baseline_exposures=0, replay_republish_delivery_recovery_forbidden=True)


def collect():
    rows = parent_rows()
    remote = remote_metadata(rows)
    revoked_path = HOME / 'H_AUTHORITY_REVOKED_20260917T2103Z.json'
    revoked = base.read(revoked_path) if revoked_path.exists() else None
    withdrawal_path = HOME.parent / 'RAW_CONTROL_WITHDRAWAL_RECEIPT.json'
    withdrawal_reference = None
    if withdrawal_path.exists():
        base.require(base.sha(withdrawal_path) == WITHDRAWAL_SHA, 'exact_Main_withdrawal_receipt_pin')
        withdrawal = base.read(withdrawal_path)
        apply_control_withdrawal(rows, withdrawal)
        withdrawal_reference = dict(path=str(withdrawal_path), sha256=WITHDRAWAL_SHA, receipt=withdrawal)
    return dict(schema='R175_NODE4_ACTUAL_PARENT_AND_ENVIRONMENT_RECEIPT_V1', addressed_to='Main',
        observed_unix=time.time(), parent_rows=rows, remote=remote,
        counts=dict(historical_new_R175_publications=sum(row['publication_count'] for row in rows),
            active_arm_publications=sum(row['publication_count'] for row in rows if row['physical'] != 1),
            H_withdrawn_before_ingestion=int(withdrawal_reference is not None),
            pending_H_publications=0 if withdrawal_reference else None,
            actual_rendered_R175=sum(bool(publication['rendered']) for row in rows for publication in row['publications']),
            verified_deliveries_by_physical={str(row['physical']): sum(bool(publication['rendered'])
                for publication in row['publications']) for row in rows},
            exact_R179_loaded=len(remote['children']), live_children=sum(row['identity_live'] for row in remote['children'])),
        H_historical_control_preserved=True,
        H_current_policy='UNPARENTED_PENDING_ROHIN' if revoked else 'BASELINE_THEN_HANDS_OFF',
        H_stop_receipt=revoked, H_withdrawal_owner='Main' if revoked else None,
        H_poststop_exposure_requires_Main_receipt=bool(revoked) and withdrawal_reference is None,
        H_withdrawal_reference=withdrawal_reference,
        environment_gap='No bound executor verified in these native plans; known prior kernel service absent when scan is empty.',
        no_new_tools_connected=True, task_caps_raised=False, peers_not_applicable=True,
        new_training_or_scientific_retention_claim=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=0)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    base.require(output.parent == HOME and 0 <= arguments.seconds <= 86400, 'owned_bounded_observer')
    output.mkdir(exist_ok=False)
    base.write(output / 'STARTED.json', dict(actor=base.identity(__import__('os').getpid()),
        source_sha256=base.sha(__file__), observed_unix=time.time(), seconds=arguments.seconds, signals_sent=0))
    end = min(time.time() + arguments.seconds, base.WALL)
    for sequence in range(2881):
        try:
            result = collect()
            base.write(output / f'RECEIPT_{sequence:06d}.json', result)
            print(json.dumps(dict(sequence=sequence, counts=result['counts'], observed_unix=result['observed_unix'])), flush=True)
        except Exception as error:
            base.write(output / f'ERROR_{sequence:06d}.json', dict(error_type=type(error).__name__, error=str(error), observed_unix=time.time()))
            print(json.dumps(dict(sequence=sequence, status='OBSERVER_ERROR_NOT_CHILD_FAILURE', error=str(error))), flush=True)
        if time.time() >= end:
            break
        time.sleep(min(30, max(0, end - time.time())))
