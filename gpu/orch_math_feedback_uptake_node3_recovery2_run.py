"""New node3 BASE parenting lives; exact host/UUID admission, no LoRA or fitting."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

import gpu
import organism_v6

gpu.__path__.insert(0, str(Path(__file__).parent))
organism_v6.__path__.insert(0, str(Path(__file__).parents[1] / 'organism_v6'))

from gpu import orch_math_feedback_uptake_base_run as reuse
from gpu import orch_math_feedback_uptake_node3_recovery_native as driver
from gpu import orch_math_feedback_uptake_response_contract as response_contract
from gpu import orch_rich_hot_a100_minor_scan as scanner
from gpu import orch_rich_hot_node3_base107_engine as direct
from gpu import orch_oracle_repair_guard as existing
from organism_v6 import orch_math_feedback_uptake_node3 as policy
from organism_v6 import orch_rich_hot_node3 as node_limits


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_recovery2_20260915_attempt1')
LIBRARY = Path('/localhome/local-rohing/orch_rich_hot_node3_20260915_base107_refill1536')
CANONICAL = Path('/tmp/orch_route_parent_campaign_20260915_canonical102')
common = reuse.common
require = policy.base.require


def bind():
    def allocation(index):
        require(index in policy.DEVICES, 'only_allocated_node3_1_2')
        return policy.DEVICES[index]
    scanner.pinned.policy = SimpleNamespace(DEVICES=policy.DEVICES, HOST_SHA=policy.HOST_SHA, require=require, allocation=allocation)
    require(scanner.pinned.host_identity() == policy.HOST_SHA, 'exact_node3_host_hash')


def scan(root, index):
    bind()
    if os.geteuid() == 0:
        return scanner.scan(index, root / 'SERVICE_IDENTITY.json')
    output = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(LIBRARY / 'source'), 'python3', '-B', str(Path(__file__)), 'scan', '--root', str(root),
        '--index', str(index)], capture_output=True, text=True, timeout=90, check=True)
    report = json.loads(output.stdout)
    require(report['gpu']['index'] == index and report['gpu']['uuid'] == policy.DEVICES[index], 'exact_uuid')
    require(report['host_sha256'] == policy.HOST_SHA and 'device_minor' in report, 'full_host_minor')
    return report


def validate(root):
    bind()
    require(root == ROOT and root.resolve() == root, 'exact_node3_root')
    ready = common.read(root / 'FAMILY_READY.json')
    for name, digest in ready['source_files'].items():
        require(common.sha(name) == digest, 'immutable_node3_sources')
    require(common.sha(LIBRARY / 'SOURCE_SHA256.json') == ready['library_manifest_sha256'], 'library_manifest')
    existing.verify_sources(LIBRARY / 'source', LIBRARY / 'SOURCE_SHA256.json')
    return dict(bundle=existing.BUNDLE, model_dir=existing.MODEL)


def prepare(root):
    bind()
    require(root == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    source = Path(__file__).parents[1]
    tests = common.read(source / 'CPU_RESULT.json')
    require(tests['passed'] and tests['tests'] >= 67, 'recovery_cpu_gate')
    original = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_20260915_attempt1')
    failed_admission = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_recovery_20260915_attempt1/campaign_node3_style2')
    require(common.read(failed_admission/'GUARDIAN_FAILED.json')['error'] == 'strict_fresh_admission', 'only_admission_failure')
    require(common.read(failed_admission/'TERMINAL.json')['status'] == 'FAILED', 'prior_guard_terminal')
    require(not list(failed_admission.glob('cycle*/*/REQUEST.json')), 'zero_native_stages_after_admission_failure')
    require(not list((failed_admission/'base_parent_queue_r107').glob('*.request.json')), 'zero_parent_after_admission_failure')
    require(not (Path('/proc')/str(common.read(failed_admission/'ACTIVATION.json')['guardian']['pid'])).exists(), 'old_admission_guardian_absent')
    inventory = reuse.source_inventory(source)
    family = dict(source_files=inventory, cpu_result=tests,
        library_manifest_sha256=common.sha(LIBRARY / 'SOURCE_SHA256.json'),
        original_family_sha256=common.sha(original / 'FAMILY_READY.json'),
        failed_admission_root=str(failed_admission), failed_admission_sha256=common.sha(failed_admission/'TERMINAL.json'),
        additional_native_calls=0, additional_parent_calls=0, preserved_native_cap=28,
        prior_native_calls=1, remaining_native_calls=27, parent_cap=4,
        prepared_unix=time.time(), repair='metadata_transport_only_no_regenerated_first_response')
    common.write(root / 'FAMILY_READY.json', family)
    for index in (2,):
        previous = original / f'campaign_node3_style{index}'
        terminal = common.read(previous / 'TERMINAL.json')
        failed = common.read(previous / 'cycle1/experience/FAILED.json')
        after = common.read(previous / 'cycle1/experience/FAILED_AFTER.json')
        require(terminal['status'] == 'FAILED' and failed['error'] == 'no_silent_input_truncation', 'exact_transport_failure')
        require(after['actual_mounted_base_verified'] and after['adapter'] is None and after['training_updates'] == 0, 'unchanged_genuine_base_after_failure')
        calls = list(previous.glob('cycle*/*/CALL_*.json'))
        require(len(calls) == 1 and calls[0].name == 'CALL_000.json', 'exact_one_prior_call')
        call = common.read(calls[0])
        require('response' in call and 'error' not in call, 'actual_historical_response')
        require(not list((previous / 'base_parent_queue_r107').glob('*.request.json')), 'zero_prior_parents')
        require(not (Path('/proc') / str(failed['process'][1])).exists(), 'old_native_absent')
        old_activation = common.read(previous / 'ACTIVATION.json')
        require(not (Path('/proc') / str(old_activation['guardian']['pid'])).exists(), 'old_guardian_absent')
        ledger = (previous / 'CALLS_NATIVE.jsonl').read_text()
        require(len(ledger.splitlines()) == 1 and json.loads(ledger)['index'] == 0, 'one_spent_counter')
        lane = root / f'campaign_node3_style{index}'
        lane.mkdir(exist_ok=False)
        (lane / 'base_parent_queue_r107').mkdir()
        for name in ('COHORT.json','PREVIOUS_CARRY.json'):
            (lane / name).write_bytes((previous / name).read_bytes())
        (lane / 'CALLS_NATIVE.jsonl').write_text(ledger)
        (lane / 'HISTORICAL_FIRST_CALL.json').write_bytes(calls[0].read_bytes())
        common.write(lane / 'RECOVERY.json', dict(original_root=str(previous),
            source_call_path=str(calls[0]), source_call_sha256=common.sha(calls[0]),
            original_ready_sha256=common.sha(previous / 'READY.json'),
            original_terminal_sha256=common.sha(previous / 'TERMINAL.json'),
            original_failed_after_sha256=common.sha(previous / 'cycle1/experience/FAILED_AFTER.json'),
            original_engine_sha256=common.sha(Path(direct.__file__)),
            original_activation=old_activation, spent=1, remaining=27,
            original_failures_preserved=True, process_discontinuity=True,
            no_optimizer_or_weight_reset=True, no_new_cohort=True))
        prior_ready = common.read(previous / 'READY.json')
        common.write(lane / 'READY.json', dict(prior_ready,source_files=inventory,
            family_ready_sha256=common.sha(root / 'FAMILY_READY.json'),
            files={name:common.sha(lane/name) for name in ('COHORT.json','PREVIOUS_CARRY.json','RECOVERY.json','HISTORICAL_FIRST_CALL.json')},
            repair='metadata_only_historical_call_import', prepared_unix=time.time()))
    print(json.dumps(dict(family_ready_sha256=common.sha(root/'FAMILY_READY.json'),
        lanes={str(index):common.sha(root/f'campaign_node3_style{index}/READY.json') for index in (2,)})))


def native(root, index, cycle, phase):
    require(index == 2, 'only_failed_admission_lane2')
    scope = policy.configured(index)
    prepared = validate(root)
    lane = root / f'campaign_node3_style{index}'
    class BaseEngine(response_contract.engine_class(direct.Engine)):
        def __init__(self, options, tokenizer, check):
            require(options.adapter_dir is None and options.gpu_uuid == scope.UUID, 'direct_base_options')
            super().__init__(options.model_dir, tokenizer, device=options.device, check=check)
    driver.policy = scope
    driver.common = SimpleNamespace(**dict(vars(common), validate=lambda original: validate(original)))
    driver.seam = SimpleNamespace(**dict(vars(driver.seam), Engine=BaseEngine, BUNDLE_SHA=node_limits.BUNDLE_SHA))
    driver.run(lane, cycle, phase)


def guard(root, index, expected_ready):
    require(index == 2, 'only_failed_admission_lane2')
    validate(root)
    lane = root / f'campaign_node3_style{index}'
    require(common.sha(lane / 'READY.json') == expected_ready, 'lane_ready')
    ready = common.read(lane / 'READY.json')
    require(ready['family_ready_sha256'] == common.sha(root / 'FAMILY_READY.json'), 'family_ready')
    publication = common.read(lane / 'PUBLICATION.json')
    require(publication['ready_sha256'] == expected_ready and publication['entry_sha256'] == common.sha(root / 'ALLOCATION.md'), 'published_allocation')
    lifetime = common.read(root / 'ORIGINAL_MATH_LIFETIME.json')
    prior_activation = common.read(lane / 'RECOVERY.json')['original_activation']
    started = prior_activation['started_unix']
    activation = dict(started_unix=started, recovery_started_unix=time.time(), native_deadline_unix=prior_activation['native_deadline_unix'],
        hard_deadline_unix=prior_activation['hard_deadline_unix'], index=index,
        guardian=common.process_identity(Path('/proc') / str(os.getpid())), ready_sha256=expected_ready,
        no_older_counter_reset=True, aggregate_native_cap=2162, aggregate_parent_cap=50)
    with (lane / 'ACTIVATION.json').open('x') as stream:
        json.dump(activation, stream, indent=2)
    child = identity = log = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle in (1,2):
            for phase in ('experience','readout'):
                output = lane / f'cycle{cycle}' / phase
                require(not output.exists(), 'no_native_retry')
                until = min(time.time()+600, activation['native_deadline_unix'])
                admitted = False
                attempt = 0
                while time.time() < until:
                    try:
                        report = scan(root,index)
                        common.write(lane / f'ADMISSION_C{cycle}_{phase}_{attempt}.json',report)
                        admitted = report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
                    except subprocess.CalledProcessError as error:
                        common.write(lane / f'ADMISSION_ERROR_C{cycle}_{phase}_{attempt}.json',dict(error=str(error),stderr=error.stderr,no_waiver=True))
                    if admitted:
                        break
                    attempt += 1
                    time.sleep(2)
                require(admitted and time.time() < activation['native_deadline_unix'], 'strict_fresh_admission')
                log = (lane / f'C{cycle}_{phase}.log').open('x')
                child = subprocess.Popen([existing.PYTHON,'-B',str(Path(__file__)),'native','--root',str(root),'--index',str(index),'--cycle',str(cycle),'--native-phase',phase],
                    cwd=LIBRARY/'source',start_new_session=True,stdout=log,stderr=subprocess.STDOUT,
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES=policy.DEVICES[index],PYTHONPATH=str(LIBRARY/'source'),HF_HUB_OFFLINE='1',
                        TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'))
                identity=common.process_identity(Path('/proc')/str(child.pid))
                common.write(lane/f'LAUNCH_C{cycle}_{phase}.json',dict(identity=identity,uuid=policy.DEVICES[index],started_unix=time.time()))
                while child.poll() is None:
                    require(time.time()<activation['hard_deadline_unix']-120,'bounded_hard_deadline')
                    time.sleep(2)
                require(child.returncode == 0,'native_failure_no_retry')
                complete,after=common.read(output/'COMPLETE.json'),common.read(output/'AFTER.json')
                require(complete['status']=='COMPLETE' and after['actual_mounted_base_verified'],'actual_complete_after')
                require(complete['process']==[identity['boot_id'],identity['pid'],int(identity['start_ticks'])] == after['process'],'actual_process')
                require(len(list(output.glob('CALL_*.json')))==(6 if phase=='experience' else 8),'complete_denominators')
                common.write(lane/f'COMPLETE_C{cycle}_{phase}.json',dict(complete_sha256=common.sha(output/'COMPLETE.json'),after_sha256=common.sha(output/'AFTER.json'),finished_unix=time.time()))
                log.close()
                child=identity=log=None
        status='COMPLETE'
    except BaseException as error:
        common.write(lane/'GUARDIAN_FAILED.json',dict(type=type(error).__name__,error=str(error),finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child,identity)
        if log is not None:
            log.close()
        common.write(lane/'TERMINAL.json',dict(status=status,finished_unix=time.time(),peer_processes_signalled=0))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','service','scan','guard','native'))
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--index',type=int,choices=(2,))
    parser.add_argument('--cycle',type=int,choices=(1,2))
    parser.add_argument('--native-phase',choices=('experience','readout'))
    parser.add_argument('--ready-sha256')
    args=parser.parse_args()
    if args.phase=='service':
        bind();scanner.pinned.service(args.root/'SERVICE_IDENTITY.json')
    elif args.phase=='scan':
        print(json.dumps(scan(args.root,args.index)))
    elif args.phase=='prepare':
        prepare(args.root)
    elif args.phase=='guard':
        guard(args.root,args.index,args.ready_sha256)
    else:
        native(args.root,args.index,args.cycle,args.native_phase)
