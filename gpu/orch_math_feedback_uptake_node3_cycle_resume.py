"""New node3 BASE parenting lives; exact host/UUID admission, no LoRA or fitting."""

import argparse
import json
import os
from pathlib import Path
import signal
import shutil
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


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_cycle_resume_20260915_attempt1')
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


def preserved_stage(lane, cycle, phase):
    if (cycle, phase) != (1, 'experience'):
        return False
    ready = common.read(lane / 'READY.json')
    for name, digest in ready['files'].items():
        require(common.sha(lane / name) == digest, 'preserved_stage_input_binding')
    stage = lane / 'cycle1/experience'
    complete, after = common.read(stage / 'COMPLETE.json'), common.read(stage / 'AFTER.json')
    require(complete['status'] == 'COMPLETE' and after['actual_mounted_base_verified'], 'genuine_completed_stage')
    require(complete['process'] == after['process'], 'original_complete_after_identity')
    require(complete['carry_sha256'] == common.sha(stage / 'CARRY.json'), 'genuine_own_carry')
    require(len(list(stage.glob('CALL_*.json'))) == 6, 'six_preserved_calls')
    return True


def prepare(root):
    bind()
    require(root == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    source = Path(__file__).parents[1]
    tests = common.read(source / 'CPU_RESULT.json')
    require(tests['passed'] and tests['tests'] >= 73, 'cycle_resume_cpu_gate')
    previous = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_recovery_20260915_attempt1/campaign_node3_style1')
    require(common.read(previous/'GUARDIAN_FAILED.json')['error'] == 'strict_fresh_admission', 'only_admission_failure')
    require(common.read(previous/'TERMINAL.json')['status'] == 'FAILED', 'prior_guard_terminal')
    require(not (previous/'cycle1/readout').exists() and not (previous/'cycle2').exists(), 'remaining_stages_unattempted')
    old_activation = common.read(previous / 'ACTIVATION.json')
    require(not (Path('/proc')/str(old_activation['guardian']['pid'])).exists(), 'prior_guardian_absent')
    prior_ready = common.read(previous/'READY.json')
    for path, digest in prior_ready['source_files'].items():
        require(common.sha(path) == digest, 'old_native_source_preserved')
    for name, digest in prior_ready['files'].items():
        require(common.sha(previous/name) == digest, 'old_native_input_preserved')
    complete = common.read(previous/'cycle1/experience/COMPLETE.json')
    require(not (Path('/proc')/str(complete['process'][1])).exists(), 'old_completed_native_absent')
    for bucket, count in (('NATIVE',6),('PARENT',2)):
        ledger=[json.loads(line) for line in (previous/f'CALLS_{bucket}.jsonl').read_text().splitlines()]
        require(len(ledger) == count and [row['index'] for row in ledger] == list(range(count)), 'spent_ledger_continuity')
    parents = sorted((previous/'base_parent_queue_r107').glob('*.response.json'))
    require(len(parents) == 2, 'two_preserved_parent_responses')
    parent_bindings = {}
    for path in parents:
        response=common.read(path)
        require(response['status'] == 'COMPLETE', 'actual_parent_complete')
        for name, digest in response['archive']['files'].items():
            archive=Path(response['archive']['remote_root'])/name
            require(common.sha(archive) == digest, 'preserved_parent_transcript_hash')
            parent_bindings[str(archive)]=digest
    inventory = reuse.source_inventory(source)
    common.write(root/'FAMILY_READY.json',dict(source_files=inventory,cpu_result=tests,
        library_manifest_sha256=common.sha(LIBRARY/'SOURCE_SHA256.json'),
        predecessor_ready_sha256=common.sha(previous/'READY.json'),
        predecessor_terminal_sha256=common.sha(previous/'TERMINAL.json'),
        additional_native_calls=0,additional_parent_calls=0,spent_native=6,remaining_native=22,
        spent_parents=2,remaining_parents=2,parent_transcript_bindings=parent_bindings,
        prepared_unix=time.time(),repair='skip_completed_C1_experience_resume_unattempted_stages'))
    lane=root/'campaign_node3_style1'
    lane.mkdir(exist_ok=False)
    (lane/'base_parent_queue_r107').mkdir()
    for name in ('COHORT.json','PREVIOUS_CARRY.json','HISTORICAL_FIRST_CALL.json','CALLS_NATIVE.jsonl','CALLS_PARENT.jsonl'):
        (lane/name).write_bytes((previous/name).read_bytes())
    shutil.copytree(previous/'cycle1/experience',lane/'cycle1/experience')
    copied={str(path.relative_to(lane)):common.sha(path) for path in (lane/'cycle1/experience').rglob('*') if path.is_file()}
    common.write(lane/'RECOVERY.json',dict(original_root=str(previous),original_activation=old_activation,
        original_ready_sha256=common.sha(previous/'READY.json'),original_terminal_sha256=common.sha(previous/'TERMINAL.json'),
        source_stage=str(previous/'cycle1/experience'),copied_stage_hashes=copied,
        parent_transcript_bindings=parent_bindings,spent_native=6,remaining_native=22,
        spent_parents=2,remaining_parents=2,no_deadline_or_counter_reset=True,
        no_optimizer_or_weight_reset=True,process_discontinuity=True))
    files={name:common.sha(lane/name) for name in ('COHORT.json','PREVIOUS_CARRY.json','HISTORICAL_FIRST_CALL.json','RECOVERY.json')}
    files.update(copied)
    common.write(lane/'READY.json',dict(prior_ready,source_files=inventory,files=files,
        family_ready_sha256=common.sha(root/'FAMILY_READY.json'),prepared_unix=time.time(),
        repair='completed_C1_context_continuity_admission_only'))
    require(preserved_stage(lane,1,'experience'), 'preserved_stage_verified')
    print(json.dumps(dict(family_ready_sha256=common.sha(root/'FAMILY_READY.json'),
        ready_sha256=common.sha(lane/'READY.json'))))


def native(root, index, cycle, phase):
    require(index == 1, 'only_completed_cycle_lane1')
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
    require(index == 1, 'only_completed_cycle_lane1')
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
                if preserved_stage(lane, cycle, phase):
                    common.write(lane/'PRESERVED_C1_EXPERIENCE.json',dict(verified_unix=time.time(),new_native_calls=0,new_parent_calls=0))
                    continue
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
    parser.add_argument('--index',type=int,choices=(1,))
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
