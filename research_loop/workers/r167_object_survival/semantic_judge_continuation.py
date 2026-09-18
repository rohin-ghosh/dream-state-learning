import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import semantic_judge as original


protocol = original.protocol
SCHEMA = 'R167_SEMANTIC51_UNCONSUMED_CONTINUATION_V1'
REPRESENTATION = 'LITERAL_VALIDATOR_EVIDENCE_V1'
REPEATABLE_FAILURES = ('real_evidence_span_not_fabricated', 'exact_annotation_for_one_packet',
    'frozen_annotation_labels', 'bounded_evidence_spans', 'bounded_uncertainty', 'separate_attention_rubric',
    'transport_response_not_parent_publication', 'exact_bounded_parent_response',
    'JSONDecodeError', 'TimeoutError', 'HTTPError')
FAILURE_POLICY = dict(consecutive_same_class=3, repeatable_classes=list(REPEATABLE_FAILURES),
    success_resets=True, different_class_resets=True, unknown_or_scope_failure='IMMEDIATE_STOP',
    ordering='CONTROLLER_TERMINAL_RECEIPT_ORDER_AFTER_UPLOAD_ATTEMPT', score_values_consulted=False)
INSTRUCTION = original.INSTRUCTION + '''
Representation clarification, not a new scoring rubric: rendered_span_evidence
contains the exact literal strings checked for response, input, and TRAIN quotes.
It renders only the unchanged supplied packet. For TRAIN, newline-separated
five-gram witnesses are NOT continuous prose. Quote a verbatim substring within
one supplied line; do not reconstruct sentences by merging overlapping arrays,
add punctuation, change capitalization, or insert ellipses. If the supplied
evidence is insufficient, preserve uncertainty. Do not invent missing prose.
The original rubric, semantic labels and strict quote validator are unchanged.
'''


def rendered_evidence(packet):
    original.packet_validate(packet)
    return dict(response=packet['response'], input='\n'.join(message['content'] for message in packet['messages']),
        TRAIN='\n'.join(' '.join(gram) for definition in packet['TRAIN_fingerprint'].values()
            for field in ('anchors', 'training_grams') for gram in definition[field]))


def request(packet, rubric):
    return protocol.canonical(dict(packet=packet, frozen_rubric=rubric,
        rendered_span_evidence=rendered_evidence(packet))).decode()


def judge_one(packet, rubric, directory, deadline, provider_call, configuration):
    payload = request(packet, rubric)
    protocol.require(time.time() < deadline, 'unexpired_call')
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError('semantic_provider_120_second_limit')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(120, deadline-time.time()))
    try:
        response, model, usage = provider_call(payload, directory, deadline,
            instruction=INSTRUCTION, reasoning_effort='high')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    protocol.require(model == original.MODEL, 'actual_judge_model')
    result = original.annotation(response, packet)
    return dict(opaque_id=packet['opaque_id'], annotation=result, judge_model=model, effort='high',
        configuration=configuration, usage=usage, max_output_tokens=4096,
        response_sha256=protocol.digest(response), request_sha256=protocol.digest(protocol.parse(payload)),
        representation=REPRESENTATION, rendered_evidence_sha256=protocol.digest(rendered_evidence(packet)),
        annotation_frozen_unix=time.time(), parent_access=False)


def partition(inventory, settlement):
    all_refs = {item['path']:item for item in inventory['packets']}
    consumed = settlement['consumed']
    protocol.require(len(all_refs) == 60 and len(consumed) == 9
        and len({item['packet']['path'] for item in consumed}) == 9, 'exact_original60_consumed9')
    for item in consumed:
        protocol.require(all_refs.get(item['packet']['path']) == item['packet'], 'no_relabelled_consumed_packet')
    used = {item['packet']['path'] for item in consumed}
    return [item for item in inventory['packets'] if item['path'] not in used]


def failure_class(error):
    reason = str(error)
    if reason in REPEATABLE_FAILURES:
        return reason
    return type(error).__name__ if type(error).__name__ in REPEATABLE_FAILURES else 'IMMEDIATE_SCOPE_OR_UNKNOWN_FAILURE'


def next_streak(previous, classification):
    if classification is None:
        return dict(failure_class=None, consecutive=0, stop=False)
    if classification not in REPEATABLE_FAILURES:
        return dict(failure_class=classification, consecutive=1, stop=True)
    consecutive = previous['consecutive'] + 1 if previous['failure_class'] == classification else 1
    return dict(failure_class=classification, consecutive=consecutive, stop=consecutive >= 3)


def validate(plan_path, require_key=False):
    plan = protocol.read(plan_path)
    protocol.require(set(plan) == {'schema','original_plan','settlement','remaining_packets','source_root','source_pins',
        'CPU_gate','private_vm_root','private_remote_root','call_cap','original_call_cap','original_charged',
        'max_output_tokens','concurrency','timeout_seconds','deadline_unix','representation','instruction_sha256',
        'unchanged_validator_sha256','visibility','failure_policy'}, 'exact_continuation_plan')
    protocol.require(plan['schema'] == SCHEMA and (plan['call_cap'],plan['original_call_cap'],plan['original_charged'],
        plan['max_output_tokens'],plan['concurrency'],plan['timeout_seconds']) == (51,60,9,4096,2,120), 'same_total_budget_no_extra_calls')
    protocol.bound(plan['original_plan'])
    base, inventory = original.validate(plan['original_plan']['path'], require_key)
    settlement = protocol.bound(plan['settlement'])
    protocol.require(settlement['status'] == 'STOPPED_ADMISSIONS_ALL_WORKERS_SETTLED'
        and settlement['original_plan'] == plan['original_plan']
        and settlement['driver_gone'] is True and settlement['live_workers'] == 0, 'settled_stopped_prior_owner')
    once = protocol.bound(settlement['original_once'])
    protocol.require(once['plan'] == plan['original_plan'] and plan['deadline_unix'] == once['deadline_unix']
        and once['deadline_unix'] == once['started_unix'] + 5400, 'original_90minute_clock_not_reset')
    protocol.require(plan['remaining_packets'] == partition(inventory, settlement), 'exact51_unconsumed_only')
    consumed_by_path = {item['reservation']['path']:item for item in settlement['consumed']}
    actual_reserved = list(Path(base['private_vm_root']).glob('*/RESERVED.json'))
    protocol.require({str(path) for path in actual_reserved} == set(consumed_by_path), 'original_charges_unchanged')
    for path in actual_reserved:
        item = consumed_by_path[str(path)]
        reservation = protocol.bound(item['reservation'])
        protocol.require(reservation['packet'] == item['packet'] and reservation['calls_charged'] == 1,
                         'exact_original_charge_witness')
    root = protocol.regular(plan['private_vm_root'])
    protocol.require(root.parent == Path('/tmp') and root.name.startswith('orch_r167_semantic_51_')
        and root != Path(base['private_vm_root']), 'new_private_VM_namespace')
    remote = protocol.regular(plan['private_remote_root'])
    protocol.require(remote.parent == protocol.CAMPAIGN/'private_appendices'
        and remote.name.startswith('semantic51_'), 'new_private_node2_namespace')
    protocol.require(plan['visibility'] == base['visibility'] and plan['failure_policy'] == FAILURE_POLICY,
                     'predeclared_structural_threshold_no_score_selection')
    source = Path(plan['source_root'])
    protocol.require(Path(original.__file__).resolve() == source / 'semantic_judge.py'
        and Path(protocol.__file__).resolve() == source / 'gpu/orch_r167_object_survival_eval.py',
        'actual_base_imports_from_exact_frozen_source')
    required = {'semantic_judge.py','semantic_judge_continuation.py','gpu/orch_route_parent_campaign_providers.py'}
    protocol.require(required <= set(plan['source_pins']) and protocol.sha(__file__) == plan['source_pins']['semantic_judge_continuation.py'],
        'actual_frozen_continuation')
    for name, checksum in plan['source_pins'].items():
        protocol.require(not Path(name).is_absolute() and '..' not in Path(name).parts and protocol.sha(source/name)==checksum, 'source_pin')
    protocol.require(plan['source_pins']['semantic_judge.py'] == base['source_pins']['semantic_judge.py']
        and plan['source_pins']['gpu/orch_route_parent_campaign_providers.py'] == base['source_pins']['gpu/orch_route_parent_campaign_providers.py'],
        'unchanged_validator_and_provider_module')
    protocol.require(all(plan['source_pins'].get(name) == checksum for name, checksum in base['source_pins'].items()),
                     'entire_original_runtime_closure_preserved')
    import inspect
    protocol.require(plan['unchanged_validator_sha256'] == protocol.hashlib.sha256(inspect.getsource(original.annotation).encode()).hexdigest()
        and plan['instruction_sha256'] == protocol.hashlib.sha256(INSTRUCTION.encode()).hexdigest()
        and plan['representation'] == REPRESENTATION, 'no_validator_weakening_representation_bound')
    gate=protocol.bound(plan['CPU_gate'])
    protocol.require(gate['status']=='PASS' and gate['provider_calls']==0 and gate['source_pins_sha256']==protocol.digest(plan['source_pins']), 'CPU_source_gate')
    return plan, base, inventory, settlement


def expected_go(plan_path):
    return dict(schema=SCHEMA,status='MAIN_SEMANTIC51_EXECUTION_GO',plan=protocol.ref(plan_path),calls=51,
        original_total_cap=60,original_consumed=9,provider_model=original.MODEL,max_concurrent=2,no_retries=True)


def worker(plan_path, packet_id):
    plan, base, inventory, settlement=validate(plan_path,True)
    references=[item for item in plan['remaining_packets'] if Path(item['path']).stem==packet_id]
    protocol.require(len(references)==1,'no_consumed_or_unregistered_packet')
    root=Path(plan['private_vm_root']);directory=root/packet_id
    once=protocol.read(root/'ONCE.json')
    protocol.require(protocol.bound(once['go'])==expected_go(plan_path) and once['plan']==protocol.ref(plan_path),'worker_bound_GO')
    protocol.require(protocol.read(directory/'RESERVED.json')['packet']==references[0],'charged_exact_packet')
    os.umask(0o077)
    protocol.write(directory/'WORKER_ONCE.json',dict(packet=references[0],entered_unix=time.time(),attempts=1))
    raw=original.remote_read(base,references[0]);protocol.write(directory/'PACKET.private.json',raw)
    packet=protocol.parse(raw);rubric=original.remote_read(base,base['rubric']).decode()
    protocol.require(time.time()+120<plan['deadline_unix'],'full_original_clock_window')
    from gpu import orch_route_parent_campaign_providers as providers
    protocol.require(Path(providers.__file__).resolve()==Path(plan['source_root'])/'gpu/orch_route_parent_campaign_providers.py','actual_frozen_provider')
    result=judge_one(packet,rubric,directory,min(time.time()+120,plan['deadline_unix']),providers.strong,base['provider_config'])
    protocol.write(directory/'ANNOTATION.private.json',result)


def dispatch(plan_path, go_path):
    plan,base,inventory,settlement=validate(plan_path,True)
    protocol.require(protocol.read(go_path)==expected_go(plan_path),'new_exact_execution_GO')
    protocol.require(time.time()+330<plan['deadline_unix'],'remaining_original_clock')
    root=Path(plan['private_vm_root']);root.mkdir(mode=0o700,exist_ok=False);os.umask(0o077)
    protocol.write(root/'ONCE.json',dict(plan=protocol.ref(plan_path),go=protocol.ref(go_path),started_unix=time.time(),
        original_deadline_unix=plan['deadline_unix'],call_cap=51))
    remote_base=dict(base,private_remote_root=plan['private_remote_root'])
    stop=root/'ADMISSIONS_STOP.json'
    admission_lock=threading.Lock()
    streak=dict(failure_class=None,consecutive=0,stop=False)
    terminal_order=0
    def terminal(directory, document, filename, classification):
        nonlocal streak, terminal_order
        with admission_lock:
            result=protocol.write(directory/filename,document)
            streak=next_streak(streak,classification)
            protocol.write(root/f'TERMINAL_ORDER_{terminal_order:03d}.json',dict(terminal=result,**streak))
            terminal_order+=1
            if streak['stop'] and not stop.exists():
                protocol.write(stop,dict(status='PREDECLARED_STRUCTURAL_ADMISSION_STOP',
                    observed_unix=time.time(),trigger=result,policy=FAILURE_POLICY,**streak))
            return result
    def invoke(reference):
        packet_id=Path(reference['path']).stem;directory=root/packet_id;directory.mkdir(mode=0o700)
        with admission_lock:
            if stop.exists() or time.time()+330>=plan['deadline_unix']:
                return protocol.write(directory/'NOT_STARTED.json',dict(status='MISSING_NOT_ADMITTED_NOT_NEGATIVE',calls_charged=0))
            protocol.write(directory/'RESERVED.json',dict(packet=reference,calls_charged=1,reserved_unix=time.time()))
        try:
            with (directory/'worker.private.log').open('wb') as log:
                subprocess.run([sys.executable,'-B',str(Path(plan['source_root'])/'semantic_judge_continuation.py'),
                    'worker','--plan',str(plan_path),'--packet-id',packet_id],cwd=plan['source_root'],
                    env=dict(os.environ,PYTHONPATH=plan['source_root']),stdout=log,stderr=log,timeout=155,check=True)
            annotation=directory/'ANNOTATION.private.json'
            uploaded=original.remote_upload(remote_base,packet_id+'.ANNOTATION.private.json',annotation.read_bytes())
            return terminal(directory,dict(status='COMPLETE',calls_charged=1,
                annotation=protocol.ref(annotation),uploaded=uploaded),'COMPLETE.json',None)
        except BaseException as error:
            worker_failure=directory/'WORKER_FAILURE.json'
            classification=protocol.read(worker_failure)['failure_class'] if worker_failure.exists() else failure_class(error)
            return terminal(directory,dict(status='FAILED_OR_UNCERTAIN_NO_RETRY',calls_charged=1,
                error_type=type(error).__name__,failure_class=classification),'FAILED.json',classification)
    with ThreadPoolExecutor(max_workers=2) as executor:
        terminals=list(executor.map(invoke,plan['remaining_packets']))
    frozen=protocol.write(root/'ANNOTATION_FREEZE.json',dict(status='ANNOTATIONS_FROZEN_NO_MAP_READ',plan=protocol.ref(plan_path),
        original_settlement=plan['settlement'],terminals=terminals,frozen_unix=time.time(),unblinded=False))
    uploaded=original.remote_upload(remote_base,'ANNOTATION_FREEZE.json',Path(frozen['path']).read_bytes())
    complete=sum(Path(item['path']).name=='COMPLETE.json' for item in terminals)
    charged=sum(protocol.bound(item)['calls_charged'] for item in terminals)
    receipt=dict(status='CONTINUATION_TERMINAL_PRIVATE_ANNOTATIONS_FROZEN',new_calls_charged=charged,
        original_consumed=9,combined_calls_charged=9+charged,total_cap=60,complete_annotations=complete,
        failed_or_uncertain=charged-complete,unadmitted=51-charged,admission_stopped=stop.exists(),
        annotation_freeze=uploaded,parent_access=False,unblinding_performed=False)
    protocol.write(root/'PUBLIC_METADATA.json',receipt)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('validate','worker','dispatch'))
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--go',type=Path);parser.add_argument('--packet-id')
    args=parser.parse_args()
    try:
        if args.action=='validate':
            validate(args.plan,True);result=dict(status='READY_NOT_GO',calls_cap=51,provider_calls=0)
        elif args.action=='worker':
            worker(args.plan,args.packet_id);result=dict(status='ANNOTATION_FROZEN_PRIVATE')
        else:
            result=dispatch(args.plan,args.go)
        print(protocol.json.dumps(result,sort_keys=True))
    except BaseException as error:
        if args.action=='worker' and original.re.fullmatch('[a-f0-9]{48}',args.packet_id or ''):
            try:
                failed_plan=protocol.read(args.plan)
                directory=protocol.regular(failed_plan['private_vm_root'])/args.packet_id
                if directory.parent.parent==Path('/tmp') and directory.parent.name.startswith('orch_r167_semantic_51_') and directory.is_dir():
                    protocol.write(directory/'WORKER_FAILURE.json',dict(failure_class=failure_class(error),error_type=type(error).__name__))
            except BaseException:
                pass
        print(protocol.json.dumps(dict(status='REFUSED_OR_FAILED_PRIVATE_DETAILS_WITHHELD',error_type=type(error).__name__)))
        raise SystemExit(1)
