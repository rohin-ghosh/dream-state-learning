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
from gpu import orch_math_feedback_uptake_stopped_native as driver
from gpu import orch_math_feedback_uptake_response_contract as response_contract
from gpu import orch_rich_hot_a100_minor_scan as scanner
from gpu import orch_rich_hot_node3_base107_engine as direct
from gpu import orch_oracle_repair_guard as existing
from organism_v6 import orch_math_feedback_uptake_node3_extra as policy
from organism_v6 import orch_rich_hot_node3 as node_limits


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_node3_extra_20260915_attempt1')
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
    require(tests['passed'] and tests['tests'] >= 55, 'node_cpu_gate')
    provider = common.read(source / 'PROVIDER_BINDINGS.json')
    pasteur = common.read(source / 'PASTEUR_READY.json')
    require(pasteur['source_sha256'] == common.sha(source / 'gpu/orch_reflection_repetition_stop.py'), 'pasteur_source')
    require(pasteur['test_sha256'] == common.sha(source / 'tests/test_orch_reflection_repetition_stop.py'), 'pasteur_tests')
    inventory = reuse.source_inventory(source)
    documents = [common.read(root / 'PRIOR_PARENTING_COHORT.json')]
    paths = sorted(set(LIBRARY.parent.glob('orch_rich*node3*/COHORT.json')) | set(LIBRARY.parent.glob('orch_rich*node3*/CORPUS_MANIFEST.json')))
    paths += [CANONICAL / 'COHORT.json']
    documents.extend(common.read(path) for path in paths)
    identifiers, questions = reuse.exclusions.exclusions(documents)
    questions = policy.add_declared_question_hashes(documents, questions)
    scopes = ('L1_ALL_SOURCE', 'L1_READOUT', 'L2_ALL_SOURCE', 'L2_READOUT', 'RETENTION')
    require(len(identifiers) >= 2856, 'complete_source_registry')
    require(len(questions) >= 2868, 'all_prior_question_hash_schemas')
    cohort = policy.base.history.make_cohort([dict(scope=scope, complete_pool=True, ids=sorted(identifiers),
        question_sha256=sorted(questions)) for scope in scopes])
    cohort.pop('retention')
    tokenizer = reuse.seam.native.source.native.load_local_tokenizer(existing.MODEL)
    prompt_lengths = [len(tokenizer.apply_chat_template(policy.base.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held'),
        tokenize=True, add_generation_prompt=True, return_dict=False)) for group in cohort['train'] + cohort['held'] for task in group]
    require(max(prompt_lengths) < 2048, 'actual_tokenizer_prompt_bounds')
    base = reuse.seam.portable.verify_base_files(existing.BUNDLE, existing.MODEL, expected_manifest_sha256=node_limits.BUNDLE_SHA)
    require(base['expected_base_sha256'] == policy.base.BASE_SHA, 'actual_base_provenance')
    family = dict(source_files=inventory, cpu_result=tests, library_manifest_sha256=common.sha(LIBRARY / 'SOURCE_SHA256.json'),
        source_manifests={str(path): common.sha(path) for path in paths}, prior_parenting_cohort_sha256=common.sha(root / 'PRIOR_PARENTING_COHORT.json'),
        excluded_ids=len(identifiers), excluded_questions=len(questions), base_verification=base,
        actual_prompt_lengths=prompt_lengths, prepared_unix=time.time(), native_calls=0, parent_calls=0,
        added_native_calls=56, added_parent_calls=8, aggregate_native_cap=2218, aggregate_parent_cap=58,
        max_additional_gpu_hours=1, original_math_gpu_hours_ceiling=24, lifetime=common.read(root / 'ORIGINAL_MATH_LIFETIME.json'))
    common.write(root / 'FAMILY_READY.json', family)
    releases = common.read(root / 'PRIOR_RELEASE_INPUTS.json')
    for index in (0,3):
        release = releases[str(index)]
        require(release['uuid'] == policy.DEVICES[index] and release['main_reassigned'], 'prior_rank_binding')
        terminal = Path(release['terminal_path'])
        require(common.sha(terminal) == release['terminal_sha256'], 'bound_prior_terminal')
        require(not (Path('/proc') / str(release['prior_pid'])).exists(), 'prior_native_or_guardian_still_active')
        lane = root / f'campaign_node3_style{index}'
        lane.mkdir(exist_ok=False)
        (lane / 'base_parent_queue_r107').mkdir()
        common.write(lane / 'COHORT.json', cohort)
        common.write(lane / 'PREVIOUS_CARRY.json', None)
        common.write(lane / 'PRIOR_RELEASE.json', dict(main_assignment='2026-09-15T08:03 freed0/3 direct user expansion',
            prior_release=release, terminal_path=str(terminal),
            terminal_sha256=common.sha(terminal), prior_terminal_kind=release['terminal_kind'],
            old_guardian_absent=True, no_outcome_based_stop_by_this_worker=True))
        common.write(lane / 'READY.json', dict(index=index, uuid=policy.DEVICES[index], style=policy.STYLES[index][0],
            source_files=inventory, provider_files=provider, files={name: common.sha(lane / name) for name in ('COHORT.json','PREVIOUS_CARRY.json','PRIOR_RELEASE.json')},
            family_ready_sha256=common.sha(root / 'FAMILY_READY.json'), native_cap=28, parent_cap=4, cycles=2,
            pasteur_ready=pasteur, no_adapter=True, no_optimizer=True, no_controls=True,
            cpu_tests_passed=True, prepared_unix=time.time()))
    print(json.dumps(dict(family_ready_sha256=common.sha(root / 'FAMILY_READY.json'),
        lanes={str(index):common.sha(root / f'campaign_node3_style{index}/READY.json') for index in (0,3)})))


def native(root, index, cycle, phase):
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
    validate(root)
    lane = root / f'campaign_node3_style{index}'
    require(common.sha(lane / 'READY.json') == expected_ready, 'lane_ready')
    ready = common.read(lane / 'READY.json')
    require(ready['family_ready_sha256'] == common.sha(root / 'FAMILY_READY.json'), 'family_ready')
    publication = common.read(lane / 'PUBLICATION.json')
    require(publication['ready_sha256'] == expected_ready and publication['entry_sha256'] == common.sha(root / 'ALLOCATION.md'), 'published_allocation')
    lifetime = common.read(root / 'ORIGINAL_MATH_LIFETIME.json')
    started = time.time()
    activation = dict(started_unix=started, native_deadline_unix=min(started + 1620, lifetime['native_deadline_unix']),
        hard_deadline_unix=min(started + 1800, lifetime['hard_deadline_unix']), index=index,
        guardian=common.process_identity(Path('/proc') / str(os.getpid())), ready_sha256=expected_ready,
        no_older_counter_reset=True, aggregate_native_cap=2218, aggregate_parent_cap=58)
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
                until = min(time.time()+180, activation['native_deadline_unix'])
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
    parser.add_argument('--index',type=int,choices=(0,3))
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
