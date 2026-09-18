"""Narrow C2 sleep33 runtime candidate; no action without separately bound GO."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import preparation_io as common


ROOT = common.REMOTE
MODEL_SOURCE = ROOT/'receiving_source1/source'
PAYLOAD = ROOT/'receiving_transfers/C2_000033/payload'
GENERATOR_SHA = '383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011'
COMMIT_SHA = '38067e8619851f556e49b3e3c26f307fd1b4abfd700fcb64d4cdde18a91dc70f'
IMPORT_PID = os.getpid()
USED = False


def reference(path):
    path = Path(path)
    return dict(path=str(path),sha256=common.sha(path.read_bytes()))


def bound(entry):
    path = Path(entry['path'])
    common.require(path.is_absolute() and path == path.resolve() and path.is_file(), 'exact_bound_regular_file')
    raw = path.read_bytes()
    common.require(common.sha(raw) == entry['sha256'], 'exact_bound_bytes')
    return json.loads(raw)


def key(config):
    common.require(config['life_id'] == 'C2' and config['sleep'] == 33 and
        config['condition'] in ('LORA_ON','LORA_OFF'), 'narrow_fixed_C2_sleep33_only')
    return 'C2_sleep000033_'+config['condition']


def validate_go(go, execution, source, runner_sha, cpu_gate, runner_cpu_gate, review):
    common.require(go.get('status') == 'MAIN_R176_EXECUTION_GO' and go.get('no_reset') is True,
        'preparation_is_not_execution_GO')
    common.require(go.get('call_cap') == 72 and go.get('token_cap') == 36864 and go.get('process_cap') == 24 and
        go.get('physical_slots') == [0,1] and go.get('absolute_end_unix') == common.END and
        go.get('active_seconds_max') == 5400 and go.get('gpu_slot_seconds_max') == 10800 and
        go.get('provider_calls') == 0 and go.get('baseline_new_calls') == 0, 'exact_R176_execution_envelope')
    common.require(execution in go.get('executions',[]) and go.get('source') == source and
        go.get('runner_sha256') == runner_sha and go.get('cpu_gate') == cpu_gate and
        go.get('runner_cpu_gate') == runner_cpu_gate, 'exact_execution_source_CPU_binding')
    common.require(review.get('status') == 'APPROVE' and review.get('independent') is True and
        review.get('reviewer') not in (None,'','R176_author','R172_author') and
        review.get('executions') == go['executions'] and review.get('source') == source and
        review.get('runner_sha256') == runner_sha and review.get('cpu_gate') == cpu_gate and
        review.get('runner_cpu_gate') == runner_cpu_gate, 'fresh_bound_integration_review_required')


def reserve(root,config,go_reference,now,lease_end):
    root = Path(root)
    cell = key(config)
    with common.lock(root/'execution_budget.lock'):
        rows = [json.loads(path.read_bytes()) for path in (root/'ledger').glob('*.RESERVED.json')]
        common.require(all(row['calls_charged'] == 3 and row['tokens_charged'] == 1536 and
            row['proposal_sha256'] == common.PINS['PROPOSAL.json'] for row in rows),'preserved_R176_charges')
        common.require(cell not in {row['key'] for row in rows} and len(rows)<24 and
            sum(row['calls_charged'] for row in rows)+3 <= 72,'finite_fixed_once_only_calls')
        common.require(all(row['capture'] == config['capture'] and row['source'] == config['source']
            for row in rows if row['life_id'] == 'C2' and row['sleep'] == 33), 'same_capture_source_for_both_conditions')
        first = root/'FIRST_ADMISSION.json'
        first_start = json.loads(first.read_bytes())['first_admission_unix'] if first.exists() else now
        end = min(first_start+5400,common.END,lease_end-21600)
        common.require(math.isfinite(now) and now+915<end,'full_job_inside_original_non_sliding_wall')
        if not first.exists():
            common.write(first,dict(first_admission_unix=first_start,hard_end_unix=end,no_reset=True))
        return common.write(root/'ledger'/(cell+'.RESERVED.json'),dict(key=cell,life_id='C2',sleep=33,
            condition=config['condition'],physical=config['physical'],capture=config['capture'],source=config['source'],
            proposal_sha256=common.PINS['PROPOSAL.json'],calls_charged=3,tokens_charged=1536,
            deadline_unix=min(now+900,end),reserved_unix=now,execution=config['execution'],go=go_reference))


def phase_reader(config,phase,attempt):
    prefix = 'ON' if config['condition'] == 'LORA_ON' else 'OFF'
    authorities = config['allowances'][phase]
    for kind in ('metadata','adapter'):
        document = authorities[kind]['document']
        common.require(common.digest(document) == authorities[kind]['reference']['sha256'] and
            document['scope_sha256'] == common.SCOPE_SHA and document['status'] == 'PRECHARGED_NO_REFUND'
            and document['life_id'] == 'C2' and document['kind'] == kind,'explicit_phase_global_authority')
    common.require(authorities['adapter']['document']['read_pass'] == prefix+'_'+phase+'_verification' and
        authorities['adapter']['document']['sleep'] == 33,'exact_condition_read_pass')
    return common.Reader(attempt/(phase+'_reads'),authorities,[])


def charge_open_reads(reader,model_source,config):
    busy = False
    source = Path(model_source)
    routes = {'model_load':None}
    explicit = {Path(config[field]['path']) for field in ('source','cpu_gate','runner_cpu_gate','capture','lease')}
    explicit.add(Path(config['service_path']))
    explicit.add(Path(config['python']).resolve())
    explicit.add(Path(__file__).resolve())
    def audit(event,arguments):
        nonlocal busy
        if busy or event!='open' or not arguments or not isinstance(arguments[0],(str,bytes)):
            return
        path = Path(os.fsdecode(arguments[0])).absolute()
        mode = arguments[1] if len(arguments)>1 else None
        if isinstance(mode,str) and any(marker in mode for marker in ('w','a','x','+')):
            return
        if not (path.is_relative_to(ROOT) or path.is_relative_to(source) or path in explicit):
            return
        if not path.is_file():
            return
        busy = True
        try:
            common.require(path == path.resolve(),'regular_exact_runtime_source')
            if path.is_relative_to(PAYLOAD/'adapter') and routes['model_load'] is not None:
                routes['model_load'].observe_open(path)
            else:
                reader.charge(path,'adapter' if path.is_relative_to(PAYLOAD/'adapter') else 'metadata',path.stat().st_size)
        finally:
            busy = False
    sys.addaudithook(audit)
    return routes


class ModelLoadAccounting:
    def __init__(self,root,allowance,adapter_paths):
        self.reader = common.Reader(root,{'adapter':allowance},adapter_paths)
        self.precharged = {}
        self.opened = set()
        for path in adapter_paths:
            path = Path(path)
            common.require(path == path.resolve() and path.is_file(),'exact_model_load_source')
            size = path.stat().st_size
            self.reader.charge(path,'adapter',size)
            self.precharged[path] = size

    def observe_open(self,path):
        path = Path(path)
        common.require(path in self.precharged and path.stat().st_size == self.precharged[path],
            'declared_precharged_model_load_file')
        if path in self.opened:
            self.reader.charge(path,'adapter',self.precharged[path])
        self.opened.add(path)


def validate(config,go_path):
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu import orch_r130_benchmark_sidecar as sidecar
    from gpu import orch_r167_fleet_eval as prior
    common.require(Path(native.__file__).resolve() == MODEL_SOURCE/'gpu/orch_r130_checkpoint_benchmark.py' and
        Path(prior.__file__).resolve() == MODEL_SOURCE/'gpu/orch_r167_fleet_eval.py' and
        Path(sidecar.__file__).resolve() == MODEL_SOURCE/'gpu/orch_r130_benchmark_sidecar.py', 'actual_bound_module_roots')
    source = bound(config['source'])
    common.require(source['scope_sha256'] == common.SCOPE_SHA,'new_R176_source_scope')
    common.require(all(config[field] == source['runtime'][field] for field in
        ('model_dir','python','python_sha256','service_path','service_sha256','lease')),
        'exact_prepared_runtime_resource_bindings')
    for name, checksum in source['source_pins'].items():
        common.require(common.sha((MODEL_SOURCE/name).read_bytes()) == checksum,'unchanged_receiving_source_closure')
    common.require(source['source_pins']['gpu/orch_r167_fleet_eval.py'] == GENERATOR_SHA,'frozen_three_prompt_generator')
    cpu = bound(config['cpu_gate'])
    common.require(cpu['status'] == 'ACTUAL_C2_SLEEP33_RECEIVING_CPU_PASS' and cpu['source_freeze'] == source['source_pins']
        and cpu['failures'] == cpu['errors'] == cpu['model_calls'] == cpu['provider_calls'] == 0
        and cpu['python'] == config['python'] and cpu['python_sha256'] == config['python_sha256'],
        'actual_receiving_copy_CPU_gate')
    runner_cpu = bound(config['runner_cpu_gate'])
    common.require(runner_cpu['status'] == 'ACTUAL_R176_NARROW_RUNNER_CPU_PASS' and
        runner_cpu['runner_sha256'] == common.sha(Path(__file__).read_bytes()) and
        runner_cpu['model_calls'] == runner_cpu['provider_calls'] == 0 and runner_cpu['failures'] == runner_cpu['errors'] == 0
        and runner_cpu['python'] == config['python'] and runner_cpu['python_sha256'] == config['python_sha256']
        and runner_cpu['CUDA_VISIBLE_DEVICES'] == '' and runner_cpu['command'],
        'actual_narrow_runner_CPU_gate')
    go = json.loads(Path(go_path).read_bytes())
    review = bound(go['independent_review'])
    validate_go(go,config['execution'],config['source'],common.sha(Path(__file__).read_bytes()),
        config['cpu_gate'],config['runner_cpu_gate'],review)
    release = bound(go['old_release'])
    common.require(release['live_bound_owners'] == 0 and release['matching_old_root_live_processes'] == [] and
        release['old_reserved_without_terminal_count'] == 0 and release['missing_controller_launch_records'] == [],
        'actual_prior_ownership_release')
    common.require(common.sha(socket.gethostname().encode()) == sidecar.HOST_SHA256 and
        type(config['physical']) is int and config['physical'] in (0,1) and
        config['gpu_uuid'] == sidecar.DEVICES[config['physical']], 'exact_node2_physical_slots')
    lease = bound(config['lease'])
    devices = lease['uuid_by_index']
    device = devices[config['physical']] if isinstance(devices,list) else devices[str(config['physical'])]
    common.require(lease['node'] == 'ovx' and device == config['gpu_uuid'] and
        lease['hard_deadline_unix'] == lease['lease_end_unix']-21600 and common.END <= lease['hard_deadline_unix'],
        'unchanged_lease_margin')
    common.require(common.sha(Path(config['python']).resolve().read_bytes()) == config['python_sha256'] and
        common.sha(Path(config['service_path']).read_bytes()) == config['service_sha256'],'exact_interpreter_service')
    copy = bound(config['capture'])
    common.require(copy['status'] == 'RECEIVING_COPY_COMPLETE' and copy['payload_path'] == str(PAYLOAD), 'same_exact_receiving_capture')
    manifest = json.loads((PAYLOAD/'MANIFEST.json').read_bytes())
    common.require(manifest == dict(schema='R130_CHECKPOINT_MANIFEST_V1',adapter_path='adapter',
        commit_path='COMMIT.original.json',commit_sha256=COMMIT_SHA),'exact_fixed_native_manifest')
    checkpoint = native.verify_checkpoint(manifest,PAYLOAD)
    context = json.loads((PAYLOAD/'BIRTH.private.json').read_bytes())
    common.require(set(context) == {'system_prompt','birth_prompt'} and
        common.sha((PAYLOAD/'BIRTH.private.json').read_bytes()) == copy['files']['BIRTH.private.json']['sha256'],
        'original_birth_only_context_binding')
    rubric = bound(cpu['private_rubric_ref'])
    common.require(rubric['methods'] == prior.METHODS and rubric['parent_access'] is False and rubric['provider_calls'] == 0,
        'unchanged_private_rubric')
    return checkpoint,context,lease


def enter(config_path,go_path,native=False):
    common.require(go_path is not None and Path(go_path).is_file(),'separate_Main_execution_GO_required')
    go = json.loads(Path(go_path).read_bytes())
    common.require(go.get('status') == 'MAIN_R176_EXECUTION_GO' and go.get('no_reset') is True,
        'preparation_is_not_execution_GO')
    config = json.loads(Path(config_path).read_bytes())
    config['execution'] = reference(config_path)
    common.require(config['execution'] in go.get('executions',[]),'GO_bound_exact_config')
    cell = key(config)
    attempt = ROOT/'attempts'/cell
    if not native:
        attempt.mkdir(parents=True,mode=0o700,exist_ok=False)
        common.write(attempt/'ONCE.json',dict(execution=config['execution'],go=reference(go_path),no_retry=True))
    else:
        common.require((attempt/'ONCE.json').is_file() and os.environ.get('R176_EXECUTION_SHA256') == config['execution']['sha256']
            and os.environ.get('R176_GO_SHA256') == reference(go_path)['sha256'], 'fresh_native_bound_parent_launch')
    phase = 'native' if native else 'preflight'
    reader = phase_reader(config,phase,attempt)
    routes = charge_open_reads(reader,MODEL_SOURCE,config)
    return config,attempt,reader,routes


def start(config_path,go_path):
    config,attempt,reader,routes = enter(config_path,go_path)
    checkpoint,context,lease = validate(config,go_path)
    from gpu import orch_r130_benchmark_sidecar as sidecar
    shared = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
    with common.lock(shared/f"physical{config['physical']}.lock"):
        report = sidecar.scan(config)
        common.write(attempt/'ACTUAL_ADMISSION.private.json',report)
        if not report['clear'] or report['blocking_reasons']:
            common.write(attempt/'REFUSED.json',dict(status='ADMISSION_REFUSED_NO_RETRY',calls_charged=0))
            return
        reservation = reserve(ROOT,config,reference(go_path),time.time(),lease['lease_end_unix'])
        record = bound(reservation)
        environment = dict(PATH=os.environ.get('PATH','/usr/bin:/bin'),HOME=os.environ['HOME'],
            PYTHONPATH=str(MODEL_SOURCE),CUDA_VISIBLE_DEVICES=config['gpu_uuid'],PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1',
            MKL_NUM_THREADS='1',R176_EXECUTION_SHA256=config['execution']['sha256'],R176_GO_SHA256=reference(go_path)['sha256'])
        command = ['timeout','--signal=TERM','--kill-after=15s',str(max(1,int(record['deadline_unix']-time.time()))),
            config['python'],'-B',str(Path(__file__).resolve()),'native','--config',str(config_path),'--go',str(go_path)]
        with (attempt/'stdout.private.txt').open('xb') as output,(attempt/'stderr.private.txt').open('xb') as errors:
            process = subprocess.Popen(command,cwd=MODEL_SOURCE,env=environment,stdin=subprocess.DEVNULL,stdout=output,stderr=errors)
            common.write(attempt/'TIMEOUT.json',dict(identity=sidecar.identity(process.pid),observed_unix=time.time()))
            code = process.wait()
        status = 'COMPLETE' if code == 0 and (attempt/'sealed/COMPLETE.json').is_file() else 'FAILED_CHARGED_NO_RETRY'
        common.write(ROOT/'ledger'/(key(config)+'.TERMINAL.json'),dict(status=status,calls_charged=3,returncode=code,
            reservation=reservation,observed_unix=time.time(),parent_access=False))


def native_run(config_path,go_path):
    global USED
    common.require(not USED and os.getpid() == IMPORT_PID,'fresh_condition_process')
    config,attempt,reader,routes = enter(config_path,go_path,True)
    common.require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['gpu_uuid'],'single_bound_GPU')
    checkpoint,context,lease = validate(config,go_path)
    reservation = json.loads((ROOT/'ledger'/(key(config)+'.RESERVED.json')).read_bytes())
    common.require(reservation['execution'] == config['execution'] and reservation['calls_charged'] == 3,'charged_before_model_load')
    from gpu import orch_r130_checkpoint_benchmark as engine_source
    from gpu import orch_r167_fleet_eval as prior
    USED = True
    output = attempt/'sealed'
    output.mkdir(mode=0o700,exist_ok=False)
    calls = 0
    def check(label):
        nonlocal calls
        common.require(time.time()<reservation['deadline_unix'] and reference(config_path)==config['execution'],
            'exact_config_original_deadline')
        if label == 'call':
            calls += 1
            common.require(calls<=3,'three_calls_no_retry')
    allowance = config['allowances']['model_load']
    prefix = 'ON' if config['condition'] == 'LORA_ON' else 'OFF'
    common.require(common.digest(allowance['document']) == allowance['reference']['sha256'] and
        allowance['document']['read_pass'] == prefix+'_model_load' and allowance['document']['life_id'] == 'C2'
        and allowance['document']['sleep'] == 33 and allowance['document']['scope_sha256'] == common.SCOPE_SHA
        and allowance['document']['status'] == 'PRECHARGED_NO_REFUND' and allowance['document']['kind'] == 'adapter',
        'separate_original_model_load_pass')
    common.write(attempt/'MODEL_LOAD_PRECHARGE.json',dict(allowance=allowance,
        bytes=sum((Path(checkpoint['adapter_path'])/name).stat().st_size for name in checkpoint['adapter_files']),
        charged_before_load=True,observed_unix=time.time()))
    routes['model_load'] = ModelLoadAccounting(attempt/'model_load_reads',allowance,
        [Path(checkpoint['adapter_path'])/name for name in checkpoint['adapter_files']])
    plan = dict(model_dir=config['model_dir'],gpu_uuid=config['gpu_uuid'])
    engine = engine_source._load_engine(plan,checkpoint,check)
    prior.generate_probes(engine,config['condition'],context,output,checkpoint,plan,check)
    check('complete')
    common.require(calls==3,'complete_three_prompt_condition')
    common.write(output/'COMPLETE.json',dict(status='COMPLETE',calls=3,execution=config['execution'],
        checkpoint_commit_sha256=COMMIT_SHA,completed_unix=time.time(),parent_access=False))


if __name__=='__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=('start','native'))
    parser.add_argument('--config',required=True)
    parser.add_argument('--go',required=True)
    arguments = parser.parse_args()
    (start if arguments.action=='start' else native_run)(Path(arguments.config),Path(arguments.go))
