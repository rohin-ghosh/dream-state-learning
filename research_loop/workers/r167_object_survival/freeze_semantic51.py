import inspect
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import semantic_judge_continuation as continuation


protocol=continuation.protocol


def build():
    worker=Path(__file__).resolve().parent
    old=worker/'semantic60_generation3'
    old_plan=protocol.read(old/'PLAN.json')
    old_root=Path(old_plan['private_vm_root'])
    destination=worker/'semantic51_generation1'
    destination.mkdir(mode=0o700)
    stop=protocol.read(old/'STRUCTURAL_STOP_SETTLED.json')
    protocol.require(stop['reserved']==9 and stop['provider_response_files']==9 and stop['validator_passed']==1
        and stop['validator_failed']==8, 'exact_settled9_metadata')
    protocol.require(not Path('/proc/673115').exists(),'stopped_old_driver_gone')
    consumed=[]
    for path in sorted(old_root.glob('*/RESERVED.json')):
        record=protocol.read(path)
        annotation=path.parent/'ANNOTATION.private.json'
        consumed.append(dict(packet=record['packet'],reservation=protocol.ref(path),
            worker_once=protocol.ref(path.parent/'WORKER_ONCE.json'),dispatch=protocol.ref(path.parent/'DISPATCH.json'),
            original_controller_terminal='COMPLETE' if (path.parent/'COMPLETE.json').exists() else
                'FAILED' if (path.parent/'FAILED.json').exists() else 'UNKNOWN_EXIT_CODE_CONTROLLER_WAS_STOPPED',
            annotation=protocol.ref(annotation) if annotation.exists() else None,
            disposition='FROZEN_ANNOTATION_PRESERVED' if annotation.exists() else 'INVALID_ANNOTATION_MISSING_NO_RETRY'))
    settlement=dict(status='STOPPED_ADMISSIONS_ALL_WORKERS_SETTLED',original_plan=protocol.ref(old/'PLAN.json'),
        original_once=protocol.ref(old_root/'ONCE.json'),stop_receipt=protocol.ref(old/'STRUCTURAL_STOP_SETTLED.json'),
        driver_gone=True,live_workers=0,consumed=consumed,observed_unix=time.time(),invalid_remain_missing=True,
        annotation_values_read=False,map_read=False)
    settlement_ref=protocol.write(destination/'SETTLEMENT.json',settlement)
    inventory=protocol.bound(old_plan['packet_inventory'])
    remaining=continuation.partition(inventory,settlement)
    source=destination/'source';shutil.copytree(old/'source',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('semantic_judge_continuation.py','test_semantic_judge_continuation.py'):
        shutil.copyfile(worker/name,source/name)
    pins={str(path.relative_to(source)):protocol.sha(path) for path in sorted(source.rglob('*.py'))}
    pins_ref=protocol.write(destination/'SOURCE_PINS.json',pins)
    with (destination/'CPU_TESTS.txt').open('wb') as log:
        result=subprocess.run([sys.executable,'-B','-m','unittest','test_semantic_judge_continuation','test_semantic_judge','-v'],
            cwd=source,env=dict(os.environ,PYTHONPATH=str(source)),stdout=log,stderr=log,timeout=60)
    protocol.require(result.returncode==0 and b'Ran 28 tests' in (destination/'CPU_TESTS.txt').read_bytes(),'frozen_source_28CPU_PASS')
    gate=protocol.write(destination/'CPU_GATE.json',dict(status='PASS',tests=28,provider_calls=0,
        source_pins_sha256=protocol.digest(pins),source_pins=pins_ref,test_receipt=protocol.ref(destination/'CPU_TESTS.txt')))
    once=protocol.read(old_root/'ONCE.json')
    plan=dict(schema=continuation.SCHEMA,original_plan=protocol.ref(old/'PLAN.json'),settlement=settlement_ref,
        remaining_packets=remaining,source_root=str(source),source_pins=pins,CPU_gate=gate,
        private_vm_root='/tmp/orch_r167_semantic_51_generation1_private',
        private_remote_root=str(protocol.CAMPAIGN/'private_appendices/semantic51_generation1'),
        call_cap=51,original_call_cap=60,original_charged=9,max_output_tokens=4096,concurrency=2,timeout_seconds=120,
        deadline_unix=once['deadline_unix'],representation=continuation.REPRESENTATION,
        instruction_sha256=protocol.hashlib.sha256(continuation.INSTRUCTION.encode()).hexdigest(),
        unchanged_validator_sha256=protocol.hashlib.sha256(inspect.getsource(continuation.original.annotation).encode()).hexdigest(),
        visibility=old_plan['visibility'],failure_policy=continuation.FAILURE_POLICY)
    plan_ref=protocol.write(destination/'PLAN.json',plan)
    result=subprocess.run([sys.executable,'-B',str(source/'semantic_judge_continuation.py'),'validate',
        '--plan',str(destination/'PLAN.json')],cwd=source,env=dict(os.environ,PYTHONPATH=str(source)),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    protocol.write(destination/'VALIDATION.json',result.stdout)
    protocol.require(result.returncode==0,'actual_frozen_CLI_validation')
    go=continuation.expected_go(destination/'PLAN.json');go['status']='PREPARATION_ONLY_NOT_EXECUTION_GO'
    protocol.write(destination/'MAIN_GO.template.json',go)
    receipt=dict(status='SEMANTIC51_FROZEN_CPU_READY_AWAITING_NEW_GO',plan=plan_ref,CPU_gate=gate,source_pins=pins_ref,
        helper=protocol.ref(source/'semantic_judge_continuation.py'),tests=protocol.ref(source/'test_semantic_judge_continuation.py'),
        original_validator_module=protocol.ref(source/'semantic_judge.py'),unchanged_validator_sha256=plan['unchanged_validator_sha256'],
        original_packets=60,consumed_excluded=9,remaining_exact_original_packets=51,provider_calls_new=0,
        original_total_call_cap=60,remaining_output_token_cap=51*4096,maximum_concurrency=2,per_call_seconds=120,
        original_deadline_unix=plan['deadline_unix'],clock_extended=False,rubric_changed=False,
        source_response_bytes_rewritten=False,invalid_annotations_salvaged=False,failure_policy=continuation.FAILURE_POLICY,
        configuration_sha256=old_plan['provider_config']['sha256'],model=continuation.original.MODEL,effort='high',
        private_vm_root=plan['private_vm_root'],private_node2_root=plan['private_remote_root'],map_read=False,
        private_annotation_upload=True,unblinding='SEPARATE_POST_FREEZE_ONLY')
    protocol.write(destination/'READINESS.json',receipt)
    print(protocol.json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    build()
