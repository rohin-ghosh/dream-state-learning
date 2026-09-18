"""Immutable private schema-doc repair over the already bound R175 parent runtime."""

import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import takeover as base
from takeover import HERE, REPO, MODEL, HARD_END, HELPER_SHA, ASSIGNMENT_SHA, require, read, write, sha, reference

STATE = HERE / 'metadata_errata_v1'
ERRATA_SHA = 'cd51e8bacdfa171127c537502c2159f59e1e0fdfa80f4ec7ed684e3e65ff22b9'
BASE_SHA = '95e304db8c3005602b57e953e3213e00137b5107b5af0f4a344d9d4202041e46'


def runtime(physical, config_path):
    require(sha(HERE / 'takeover.py') == BASE_SHA, 'immutable_preexisting_adapter')
    require(sha(STATE / 'PARENT_METADATA_ERRATA_V1.md') == ERRATA_SHA, 'exact_private_errata')
    parent, provider, config, helper = base.runtime(physical, config_path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    original_prompt = policy.prompt
    metadata = (STATE / 'PARENT_METADATA_ERRATA_V1.md').read_text()
    encoding = (STATE / 'RESPONSE_ENCODING_ERRATUM.md').read_text()
    constraint = (STATE / 'EXECUTABLE_TASK_CONSTRAINT.md').read_text()
    def prompt(current_config, state, memory_state):
        instruction, payload = original_prompt(current_config, state, memory_state)
        instruction += '\nPARENT-PRIVATE VALIDATOR DOCUMENTATION; NOT CHILD-FACING BOILERPLATE:\n' + metadata + '\n' + encoding
        instruction += '\nVerified-capability constraint for this parent:\n' + constraint
        return instruction, payload
    policy.prompt = prompt
    return parent, provider, config, helper


def prepare():
    helper, rows = base.release()
    require(sha(HERE / 'takeover.py') == BASE_SHA, 'base_source_unchanged')
    for physical, assignment in rows.items():
        old = HERE / 'parents' / ('physical' + str(physical))
        new = STATE / 'parents' / ('physical' + str(physical))
        old_config = read(old / 'CONFIG.json')
        config = copy.deepcopy(old_config)
        config.update(predecessor_output=str(old / 'parent'),
            predecessor_started_sha256=sha(old / 'parent/STARTED.json'),
            private_metadata_errata=dict(path=str(STATE / 'PARENT_METADATA_ERRATA_V1.md'),sha256=ERRATA_SHA),
            private_encoding_erratum=reference(STATE / 'RESPONSE_ENCODING_ERRATUM.md'),
            executable_task_constraint=reference(STATE / 'EXECUTABLE_TASK_CONSTRAINT.md'),
            parent_only_nonmaterial_repair=True)
        write(new / 'CANDIDATE_CONFIG.json', config)
    print(json.dumps(dict(status='PRIVATE_ERRATA_CANDIDATES_READY_NO_SIGNALS',errata_sha256=ERRATA_SHA)))


def preflight(physical, final=False):
    folder = STATE / 'parents' / ('physical' + str(physical))
    path = folder / ('CONFIG.json' if final else 'CANDIDATE_CONFIG.json')
    parent, provider, config, helper = runtime(physical, path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    state = dict(events=[],delivered={},journal_id='CPU',split='TRAIN',response_count=100,request_count=100,sleep_count=0,caught_up=True,head_sha256='0'*64)
    seed=dict(journal_id='CPU',object_delivered_turns={},last_response_count=100,last_request_count=100,prospective_request_count=100,credits={},grammar_delivered=False,attempts=[])
    instruction, payload = policy.prompt(config,state,policy.memory(seed,[],state))
    require('next_task' in instruction and 'MUST be JSON null' in instruction and '[a-z0-9]' in instruction, 'private_validator_constraints_present')
    normalized = ' '.join(instruction.split())
    require('JSON-encoded string' in normalized and 'not been verified' in normalized, 'transport_and_executable_capability_documented')
    response=dict(speak=False,message='',rationale='{}')
    require(provider.response_schema(json.dumps(response))==response,'existing_string_transport_accepted')
    response['rationale']={}
    try:
        provider.response_schema(json.dumps(response))
    except ValueError:
        pass
    else:
        raise ValueError('validator_must_not_accept_nested_rationale')
    require(config['r175_arm']==base.release()[1][physical]['arm'] and config['schedule_on']=='response', 'same_bound_arm_clock')
    return dict(status='NONMATERIAL_PRIVATE_ERRATA_CPU_PASS',physical=physical,config=reference(path),
        errata_sha256=ERRATA_SHA,encoding=reference(STATE/'RESPONSE_ENCODING_ERRATUM.md'),
        constraint=reference(STATE/'EXECUTABLE_TASK_CONSTRAINT.md'),patched_policy=reference(policy.__file__),
        patched_provider=reference(provider.__file__),validators_unchanged=True,provider_calls=0)


def modern_ledger(output, original):
    output=Path(output)
    old=output.parent
    seed=read(old/'SEED.json')
    requests=seed['last_request_count']
    responses=seed['last_response_count']
    attempts=[]
    pins=[]
    pending=list(seed.get('legacy_pending_ids_preserved',[]))
    for directory in sorted(output.glob('parent_*')):
        source_path,result_path=directory/'SOURCE.json',directory/'RESULT.json'
        require(source_path.exists() and result_path.exists(),'inflight_attempt_preserve_and_retry')
        source,result=read(source_path),read(result_path)
        require(result['source_sha256']==sha(source_path),'same_modern_source')
        require(result['status'] in ('PUBLISHED','SILENT','PROVIDER_FAILED','VALIDATION_FAILED'),'uncertain_publication_no_takeover')
        requests=max(requests,source['request_count'])
        responses=max(responses,source['response_count'])
        attempts.append(dict(source=source,result=result))
        pins.append(dict(source=reference(source_path),result=reference(result_path)))
        if result['status']=='PUBLISHED':
            require((old/'FIRST_PUBLICATION.json').exists(),'finish_first_publication_receipt_before_handoff')
            pending.append(result['publication']['id'])
    return dict(request_cursor=requests,response_cursor=responses,attempts=attempts,pins=pins,
                previous_seed=reference(old/'SEED.json'),pending_existing_inbox_ids=pending)


def rebind(physical):
    import snapshot_transport
    require(bool(os.environ.get('NVIDIA_API_KEY')),'private_inherited_credential')
    old=HERE/'parents'/('physical'+str(physical))
    new=STATE/'parents'/('physical'+str(physical))
    require(not (new/'TERMINATION_ONCE.json').exists(),'no_duplicate_rebind')
    spawned=read(old/'SPAWNED.json')
    expected=spawned['identity']
    bootstrap=snapshot_transport.poll(physical,read(old/'LIVE_BOOTSTRAP_READY.json')['cursor'])
    require(bootstrap['snapshot']['caught_up'],'fresh_snapshot_caught_up')
    write(new/'LIVE_BOOTSTRAP_READY.json',bootstrap)
    checked=subprocess.run([sys.executable,'-B',__file__,'preflight','--physical',str(physical)],capture_output=True,text=True,timeout=30)
    require(checked.returncode==0,'private_errata_preflight_before_pause')
    original=read(old/'CONFIG.json')
    base.ledger=modern_ledger
    descriptor,reserved=base.quiet_pause(expected,str(old/'parent'),original,time.monotonic()+150)
    terminated=False
    try:
        require(bootstrap['snapshot']['response_count']>=reserved['response_cursor'],'no_lifetime_counter_rewind')
        write(new/'PREDECESSOR_SETTLED_LEDGER.json',reserved)
        seed=copy.deepcopy(read(old/'SEED.json'))
        seed['attempts']+=reserved['attempts']
        seed['last_response_count']=reserved['response_cursor']
        seed['last_request_count']=reserved['request_cursor']
        seed['legacy_ledger']=reference(new/'PREDECESSOR_SETTLED_LEDGER.json')
        write(new/'SEED.json',seed)
        config=read(new/'CANDIDATE_CONFIG.json')
        config.update(start_after_response_count=reserved['response_cursor'],start_after_request_count=reserved['request_cursor'],predecessor_seed=reference(new/'SEED.json'))
        write(new/'CONFIG.json',config)
        for name in ('FIRST_PUBLICATION.json','FIRST_RENDERED_REQUEST.json','AUDIT_AT_3_SLEEPS.json','WITHDRAWAL_STARTED.json','WITHDRAWAL_COMPLETE.json'):
            if (old/name).exists():
                write(new/name,(old/name).read_text())
        checked=subprocess.run([sys.executable,'-B',__file__,'preflight','--physical',str(physical),'--final'],capture_output=True,text=True,timeout=30)
        require(checked.returncode==0,'final_errata_preflight')
        write(new/'CPU_PREFLIGHT.json',json.loads(checked.stdout))
        require(base.same(expected,base.identity(expected['pid'])) and modern_ledger(str(old/'parent'),original)==reserved,'quiet_identity_and_ledger_unchanged')
        write(new/'TERMINATION_ONCE.json',dict(identity=expected,at_unix=time.time(),reason='nonmaterial_private_schema_documentation_repair',errata_sha256=ERRATA_SHA,child_signals=0))
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
        signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        terminated=True
        require(bool(select.select([descriptor],[],[],20)[0]),'one_parent_lead_exit_before_successor')
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'serve','--physical',str(physical)]
        process=subprocess.Popen(command,cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=''),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        receipt=dict(status='PRIVATE_METADATA_REBIND_STARTED_NOT_DELIVERY',physical=physical,arm=config['r175_arm'],identity=base.identity(process.pid),predecessor=expected,config=reference(new/'CONFIG.json'),errata_sha256=ERRATA_SHA,started_unix=time.time(),child_restarts=0,validators_unchanged=True,pending_ids_preserved=reserved['pending_existing_inbox_ids'])
        write(new/'SPAWNED.json',receipt)
        return receipt
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        os.close(descriptor)

def serve(physical):
    import snapshot_transport
    folder = STATE / 'parents' / ('physical' + str(physical))
    try:
        require(bool(os.environ.get('NVIDIA_API_KEY')), 'private_inherited_credential')
        parent, provider, config, helper = runtime(physical, folder / 'CONFIG.json')
        policy = importlib.import_module('gpu.orch_r166_parent_policy')
        seed = read(folder / 'SEED.json')
        output = folder / 'parent'
        observed = read(folder / 'LIVE_BOOTSTRAP_READY.json')
        cursor = observed['cursor']
        sequence = 0
        first = read(folder / 'FIRST_PUBLICATION.json') if (folder / 'FIRST_PUBLICATION.json').exists() else None
        with policy.community.parent_lock(output):
            write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
                config_sha256=sha(folder / 'CONFIG.json'), model=MODEL, branch=config['branch'],
                programme=config['programme'], schedule_on='response', arm=config['r175_arm'],
                actual_tick=reference(policy.__file__), actual_provider=reference(provider.__file__),
                legacy_ledger=seed['legacy_ledger'], no_child_restart=True))
            while time.time() < HARD_END:
                observed = snapshot_transport.poll(physical, cursor)
                cursor, state = observed['cursor'], observed['snapshot']
                if first is not None and not (folder / 'FIRST_RENDERED_REQUEST.json').exists():
                    delivery = state['delivered'].get(first['publication']['id'])
                    if delivery is not None:
                        require(delivery['text_sha256'] == first['message_sha256'], 'exact_first_rendered_message')
                        write(folder / 'FIRST_RENDERED_REQUEST.json', dict(status='VERIFIED_RENDERED_TRAIN_REQUEST',
                            physical=physical, arm=config['r175_arm'], publication=reference(folder / 'FIRST_PUBLICATION.json'),
                            delivered=delivery, snapshot_head=state['head_sha256'], journal_id=state['journal_id'],
                            verified_by=reference(HERE / ('source_' + config['r175_arm']) / 'gpu/orch_r166_parent_snapshot.py'),
                            observed_unix=time.time(), baseline_sleep_count=delivery['sleep_count']))
                rendered_path = folder / 'FIRST_RENDERED_REQUEST.json'
                withdrawing = False
                if rendered_path.exists():
                    anchor = read(rendered_path)
                    if state['sleep_count'] >= anchor['baseline_sleep_count'] + 3:
                        if not (folder / 'AUDIT_AT_3_SLEEPS.json').exists():
                            write(folder / 'AUDIT_AT_3_SLEEPS.json', dict(status='THREE_ACTUAL_COMPLETED_SLEEPS_EVIDENCE_REVIEW_DUE',
                                baseline=reference(rendered_path), observed_sleep_count=state['sleep_count'],
                                changed_intention_per_cycle='UNKNOWN_UNTIL_ACTUAL_TRAIN_EVIDENCE_INSPECTION',
                                compaction_carry='UNKNOWN_UNTIL_ACTUAL_COMPACTION_INSPECTION',
                                recent_events=state['events'], snapshot_head=state['head_sha256'], no_invented_outcomes=True))
                        if not (folder / 'WITHDRAWAL_STARTED.json').exists():
                            write(folder / 'WITHDRAWAL_STARTED.json', dict(started_unix=time.time(),
                                start_sleep_count=state['sleep_count'], resume_after_sleep_count=state['sleep_count']+1,
                                no_new_parent_turns=True, peer_service='NOT_ACTIVE_ASSIGNED_ONLY',
                                old_invitations_remain_visible=True, clean_context_claim=False))
                    withdrawal_path = folder / 'WITHDRAWAL_STARTED.json'
                    if withdrawal_path.exists() and not (folder / 'WITHDRAWAL_COMPLETE.json').exists():
                        withdrawal = read(withdrawal_path)
                        if state['sleep_count'] >= withdrawal['resume_after_sleep_count']:
                            write(folder / 'WITHDRAWAL_COMPLETE.json', dict(observed_unix=time.time(),
                                actual_sleep_count=state['sleep_count'], started=reference(withdrawal_path)))
                        else:
                            withdrawing = True
                status = dict(status='ONE_COMPLETED_SLEEP_PARENT_WITHDRAWAL') if withdrawing else policy.tick(REPO, config, output, seed, state)
                write(folder / ('STATUS_%06d.json' % sequence), dict(status=status['status'], observed_unix=time.time(),
                    physical=physical, response_count=state['response_count'], request_count=state['request_count'],
                    sleep_count=state['sleep_count'], caught_up=state['caught_up'], head_sha256=state['head_sha256'],
                    actual_tick='gpu.orch_r166_parent_policy.tick', cadence=config['cadence_responses']))
                if first is None:
                    for attempt in sorted(output.glob('parent_*')):
                        result_path = attempt / 'RESULT.json'
                        if not result_path.exists():
                            continue
                        result = read(result_path)
                        if result['status'] == 'PUBLISHED':
                            first = dict(status='PUBLISHED_RENDER_NOT_YET_VERIFIED', physical=physical,
                                arm=config['r175_arm'], config=reference(folder / 'CONFIG.json'), result=reference(result_path),
                                source=reference(attempt / 'SOURCE.json'), prompt=reference(attempt / 'PROMPT.json'),
                                requested_model=MODEL, actual_model=result['model'], publication=result['publication'],
                                message_sha256=hashlib.sha256(result['message'].encode()).hexdigest(),
                                source_response_count=read(attempt / 'SOURCE.json')['response_count'], schedule_on='response',
                                published_observed_unix=time.time(), helper_sha256=HELPER_SHA, assignments_sha256=ASSIGNMENT_SHA)
                            write(folder / 'FIRST_PUBLICATION.json', first)
                            break
                sequence += 1
                time.sleep(max(2, config.get('poll_interval_seconds', 0.25)))
            write(folder / 'TERMINAL.json', dict(status='UNCHANGED_1650_PDT_PARENT_STOP', at_unix=time.time()))
    except BaseException as error:
        if not (folder / 'SERVICE_FAILED.json').exists():
            write(folder / 'SERVICE_FAILED.json', dict(status='PARENT_SERVICE_FAILED', error_type=type(error).__name__,
                reason=str(error)[:500] if isinstance(error, ValueError) else 'inspect_owned_operational_receipts', at_unix=time.time()))
        raise


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('prepare','preflight','rebind','serve'))
    parser.add_argument('--physical',type=int,choices=base.PHYSICALS)
    parser.add_argument('--final',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare': prepare()
    elif args.action=='preflight': print(json.dumps(preflight(args.physical,args.final),sort_keys=True))
    elif args.action=='rebind': print(json.dumps(rebind(args.physical),sort_keys=True))
    else: serve(args.physical)


if __name__=='__main__': main()
