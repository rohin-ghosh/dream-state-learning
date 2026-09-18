"""New finite campaign contract around the unchanged R167 probe generator."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

import prep_common as common
from gpu import orch_r167_fleet_eval as prior


ROOT=common.REMOTE_ROOT
SCHEMA='R172_EMPTY_CONTEXT_CONDITION_V1'
USED=False
IMPORT_PID=os.getpid()


def device_uuid(lease, physical):
    devices = lease['uuid_by_index']
    return devices[physical] if isinstance(devices, list) else devices[str(physical)]


def validate_receiver_identity(config, lease):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    common.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == sidecar.HOST_SHA256
        and type(config['physical']) is int and config['physical'] in (0, 1)
        and config['gpu_uuid'] == sidecar.DEVICES[config['physical']], 'node2_devices_only')
    common.require(lease['node'] == 'ovx'
        and device_uuid(lease, config['physical']) == config['gpu_uuid']
        and lease['hard_deadline_unix'] == lease['lease_end_unix']-21600
        and common.END <= lease['hard_deadline_unix'], 'unchanged_existing_lease_and_device')


def validate_loaded_sources(source_root):
    from gpu import orch_r130_checkpoint_benchmark as native_engine
    from gpu import orch_r130_benchmark_sidecar as sidecar
    modules = {'r172_runner.py': Path(__file__), 'prep_common.py': Path(common.__file__),
        'gpu/orch_r167_fleet_eval.py': Path(prior.__file__),
        'gpu/orch_r167_object_probe_queue.py': Path(prior.queue.__file__),
        'gpu/orch_r167_object_survival_eval.py': Path(prior.protocol.__file__),
        'gpu/orch_r130_checkpoint_benchmark.py': Path(native_engine.__file__),
        'gpu/orch_r130_benchmark_sidecar.py': Path(sidecar.__file__)}
    common.require(all(path.resolve() == Path(source_root)/name for name, path in modules.items()),
        'actual_imports_from_frozen_receiving_tree')


def verify_source_closure(source_root, source_freeze):
    from gpu import orch_r130_checkpoint_benchmark as native_engine
    source_root = Path(source_root)
    files = source_freeze['files']
    required = {'r172_runner.py', 'r172_scheduler.py', 'prep_common.py',
        'gpu/orch_r167_fleet_eval.py', 'gpu/orch_r167_object_probe_queue.py',
        'gpu/orch_r167_object_survival_eval.py', 'gpu/orch_r130_checkpoint_benchmark.py',
        'gpu/orch_r130_benchmark_sidecar.py', 'gpu/orch_rich_hot_node2_scan.py'}
    required.update(native_engine.REQUIRED_SOURCES)
    required.update({'tests/test_orch_r167_fleet_eval.py', 'test_runner_preparation.py'})
    common.require(required <= set(files), 'complete_frozen_generator_source_closure')
    for name, checksum in files.items():
        path = Path(name)
        common.require(not path.is_absolute() and '..' not in path.parts,
            'relative_frozen_source_path')
        common.require(common.ref(source_root / path)['sha256'] == checksum,
            'immutable_receiving_source_closure')
    for directory in ('gpu', 'organism_v6'):
        common.require((source_root / directory).is_dir(), 'required_model_source_directory')
        common.require(all(str(path.relative_to(source_root)) in files
            for path in (source_root / directory).rglob('*.py')), 'complete_python_source_closure')


def validate_manifest(manifest):
    common.require(set(manifest) == {'schema', 'adapter_path', 'commit_path', 'commit_sha256'}
        and manifest['schema'] == 'R130_CHECKPOINT_MANIFEST_V1'
        and manifest['adapter_path'] == 'adapter' and manifest['commit_path'] == 'COMMIT.original.json',
        'exact_captured_manifest_paths')


def verified_checkpoint(manifest, directory, read_ledger, life_id, operation):
    from gpu import orch_r130_checkpoint_benchmark as native_engine
    validate_manifest(manifest)
    directory = Path(directory)
    adapter = directory / 'adapter'
    paths = list(adapter.iterdir())
    common.require(all(path == path.resolve() and path.is_file() for path in paths),
        'regular_receiving_adapter_files')
    read_ledger.reserve(operation + ':metadata', life_id, 'metadata',
        (directory / manifest['commit_path']).stat().st_size)
    read_ledger.reserve(operation + ':adapter', life_id, 'adapter',
        sum(path.stat().st_size for path in paths))
    return native_engine.verify_checkpoint(manifest, directory)


def receiving_allowance(config):
    allowance = common.bound(config['receiving_read_allowance'])
    common.require(allowance['status'] == 'GLOBAL_PRECHARGED_RECEIVING_ALLOWANCE'
        and allowance['life_id'] == config['life_id'] and allowance['capture'] == config['capture']
        and allowance['proposal_sha256'] == common.PROPOSAL_SHA
        and re.fullmatch('[a-f0-9]{64}', allowance['allowance_id']) is not None,
        'receiver_verification_preIO_global_binding')
    for kind in ('metadata', 'adapter'):
        copies = allowance['global_reservations'][kind]
        origin, copy = copies['original'], copies['receiving_copy']
        common.require(origin['sha256'] == copy['sha256']
            and Path(copy['path']).is_relative_to(ROOT/'control/global_reservations')
            and Path(copy['path']) == Path(copy['path']).resolve(), 'same_byte_global_reservation_copy')
        reservation = common.bound(copy)
        amount = allowance[kind+'_bytes']
        common.require(reservation['status'] == 'CHARGED_BEFORE_IO_NO_REFUND'
            and reservation['kind'] == kind and reservation['life_id'] == config['life_id']
            and type(amount) is int and 0 < amount == reservation['bytes'] <= 2*common.GIB
            and reservation['failures_charged'] is True, 'exact_original_receiving_allocation')
    return allowance, common.Ledger(ROOT/'receiving_reads'/allowance['allowance_id'],
        dict(metadata=allowance['metadata_bytes'], adapter=allowance['adapter_bytes'],
            per_life=2*common.GIB, discovery=0), [config['life_id']])


def validate_go(go_path,pipeline_ref,source_ref,cpu_ref):
    common.require(go_path is not None,'separate_Main_execution_GO_required')
    go=common.read(go_path)
    common.require(go.get('status')=='MAIN_R172_EXECUTION_GO' and go.get('no_reset') is True,
        'preparation_scope_is_not_execution_GO')
    common.require(go.get('pipeline')==pipeline_ref and go.get('source_freeze')==source_ref and go.get('cpu_gate')==cpu_ref,
        'exact_new_pipeline_source_CPU_binding')
    common.require(go.get('call_cap')==576 and go.get('token_cap')==294912 and go.get('process_cap')==192
        and go.get('physical_slots')==[0,1] and go.get('provider_calls')==0 and go.get('absolute_end_unix')==common.END,
        'fixed_new_execution_envelope')
    review=common.bound(go['independent_review'])
    common.require(review.get('status')=='APPROVE' and review.get('independent') is True
        and review.get('reviewer') not in (None,'','R172_author') and review.get('pipeline')==pipeline_ref
        and review.get('source_freeze')==source_ref and review.get('cpu_gate')==cpu_ref,'bound_independent_scope_review')
    release=common.bound(go['old_release'])
    common.require(release.get('status')=='RESOURCE_ONLY_NO_MODEL_CALLS'
        and release.get('live_bound_owners')==0 and release.get('matching_old_root_live_processes')==[]
        and release.get('old_reserved_without_terminal_count')==0
        and release.get('missing_controller_launch_records')==[],'actual_old_owner_release_not_clock')
    return go


def validate_cell(config_path,go_path=None,execution=False):
    config=common.read(config_path)
    common.require(config['schema']==SCHEMA and config['root']==str(ROOT),'exact_R172_configuration')
    pipeline=common.bound(config['pipeline'])
    common.require(pipeline['schema']=='R172_PREPARED_ROLLING_CAMPAIGN_V1'
        and pipeline['proposal_sha256']==common.PROPOSAL_SHA and pipeline['call_cap']==576
        and pipeline['token_cap']==294912 and pipeline['absolute_end_unix']==common.END,'new_finite_pipeline')
    lives=[life for life in pipeline['lives'] if life['life_id']==config['life_id']]
    common.require(len(lives)==1 and len(pipeline['lives'])==24,'exact_24_declared_identity')
    common.require(config['physical'] in (0,1) and config['condition']==prior.queue.CONDITIONS[config['physical']],
        'fixed_physical_condition_binding')
    if execution:
        validate_go(go_path,config['pipeline'],config['source_freeze'],config['cpu_gate'])
    registered=common.bound(config['registration'])
    plan,life_root,source,authority=prior.queue.initialized(registered['plan']['path'])
    common.require(registered==common.read(life_root/'REGISTERED.json') and plan['life_id']==config['life_id']
        and plan['source_root']==lives[0]['proposed_storage_root'] and plan['sleep_count']==3,'per_life_original_source_registration')
    common.require(config['sleep'] in prior.queue.milestones(plan),'three_consecutive_enrolled_sleeps_only')
    capture=common.bound(config['capture'])
    capture_root=ROOT/'lives'/config['life_id']/'captures'/f"{config['sleep']:06d}"
    common.require(Path(config['capture']['path']) == capture_root/'COMPLETE.json'
        and capture_root == capture_root.resolve(), 'exact_local_checkpoint_capture')
    for field, filename in (('manifest','MANIFEST.json'),('birth','BIRTH.private.json'),('boundary','BOUNDARY.json')):
        common.require(Path(capture[field]['path']) == capture_root/filename, 'capture_local_metadata_confinement')
    boundary=common.bound(capture['boundary'])
    common.require(boundary['life_id']==config['life_id'] and boundary['sleep']==config['sleep']
        and boundary['source_root']==plan['source_root'] and boundary['birth_plan']==plan['birth_plan']
        and boundary['source_authority']==plan['source_authority'],'exact_capture_birth_source_checkpoint')
    context=common.bound(capture['birth'])
    common.require(set(context)=={'system_prompt','birth_prompt'} and prior.protocol.digest(context)==boundary['context_sha256'],
        'empty_history_original_birth_only')
    transfer=common.bound(config['transfer'])
    common.require(transfer['status']=='EXACT_RECEIVING_COPY_VERIFIED' and transfer['capture']==config['capture']
        and transfer['life_id']==config['life_id'] and transfer['sleep']==config['sleep']
        and transfer['proposal_sha256']==common.PROPOSAL_SHA,'receiving_exact_copy_receipt')
    manifest=common.bound(capture['manifest'])
    validate_manifest(manifest)
    directory=Path(capture['manifest']['path']).parent
    commit_path=directory/manifest['commit_path']
    common.require(common.ref(commit_path)['sha256']==manifest['commit_sha256']==boundary['commit']['sha256'],
        'original_COMMIT_hash_join')
    commit=common.read(commit_path)
    common.require(commit['base_sha256']==prior.queue.BASE,'frozen_base')
    if config['sleep']==0:
        common.require(commit['optimizer_steps']==0,'original_zero_update_initial')
        baseline=common.bound(config['baseline_authority'])
        common.require(baseline['life_id']==config['life_id'] and baseline['condition']==config['condition']
            and baseline['status']=='NEW_BASELINE_AUTHORIZED' and baseline['prior_failed_or_uncertain'] is False,
            'no_unverified_baseline_reuse_or_consumed_retry')
    else:
        common.require(commit['created_unix']>plan['frozen_unix'],'prospective_completed_checkpoint')
    witness=common.bound(config['TRAIN_freeze'])
    common.require(witness['status']=='PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE' and witness['model_calls']==0
        and witness['frozen_unix']<time.time() and common.ref(witness['evidence']['path'])==witness['evidence'],
        'private_original_language_witness_freeze')
    rubric=common.bound(config['rubric'])
    common.require(rubric['methods']==prior.METHODS and rubric['parent_access'] is False and rubric['provider_calls']==0,
        'unchanged_private_rubric_no_judge_budget')
    source_freeze=common.bound(config['source_freeze'])
    common.require(Path(config['source_root'])==Path(__file__).resolve().parent,'actual_new_source_directory')
    verify_source_closure(config['source_root'], source_freeze)
    validate_loaded_sources(config['source_root'])
    gate=common.bound(config['cpu_gate'])
    common.require(gate['status']=='ACTUAL_RECEIVING_CPU_PASS' and gate['source_freeze']==config['source_freeze']
        and gate['exit_status']==0 and gate['python']==config['python']
        and gate['python_sha256']==config['python_sha256'] and gate['command']
        and gate['CUDA_VISIBLE_DEVICES']=='' and gate['model_calls']==0 and gate['provider_calls']==0
        and common.ref(gate['test_output']['path'])==gate['test_output'],
        'fresh_receiving_CPU_gate')
    lease=common.bound(config['lease'])
    validate_receiver_identity(config,lease)
    common.require(hashlib.sha256(Path(config['python']).resolve(strict=True).read_bytes()).hexdigest()==config['python_sha256'],
        'exact_receiving_interpreter')
    common.require(common.ref(config['service_path'])['sha256']==config['service_sha256'],'strict_existing_service_pin')
    allowance, read_ledger = receiving_allowance(config)
    operation = ('native' if os.environ.get('R172_EXECUTION_SHA256') else 'preflight') + ':' + prior.queue.key(
        config['life_id'], config['sleep'], config['condition'])
    checkpoint=verified_checkpoint(manifest,directory,read_ledger,config['life_id'],operation)
    return config,pipeline,checkpoint,context,prior.queue.key(config['life_id'],config['sleep'],config['condition'])


def reserve(root,config,lease_end,now):
    root=Path(root)
    key=prior.queue.key(config['life_id'],config['sleep'],config['condition'])
    with common.lock(root/'execution_budget.lock'):
        rows=[common.read(path) for path in (root/'ledger').glob('*.RESERVED.json')]
        common.require(key not in {row['key'] for row in rows} and len(rows)<192,'finite_once_only_192_processes')
        common.require(all(row['pipeline'] == config['pipeline'] and row['calls_charged'] == 3
            and row['tokens_charged'] == 1536 for row in rows), 'preserved_same_pipeline_charges')
        common.require(all(row['capture'] == config['capture'] and row['pipeline'] == config['pipeline']
            for row in rows if row['life_id'] == config['life_id'] and row['sleep'] == config['sleep']),
            'paired_conditions_exact_same_capture_and_pipeline')
        kind='baseline' if config['sleep']==0 else 'forward'
        common.require(sum(row['kind']==kind for row in rows)<(48 if kind=='baseline' else 144),'separate_baseline_forward_caps')
        first=root/'FIRST_ADMISSION.json'
        start=common.read(first)['first_admission_unix'] if first.exists() else now
        hard_end=min(start+14400,common.END,lease_end-21600)
        common.require(now+915<hard_end,'full_job_inside_non_sliding_window')
        if not first.exists():
            common.write(first,dict(first_admission_unix=start,hard_end_unix=hard_end,no_reset=True))
        record=dict(key=key,life_id=config['life_id'],sleep=config['sleep'],condition=config['condition'],kind=kind,
            pipeline=config['pipeline'],calls_charged=3,tokens_charged=1536,physical=config['physical'],reserved_unix=now,
            deadline_unix=min(now+900,hard_end),execution=config['execution_ref'],capture=config['capture'])
        return common.write(root/'ledger'/(key+'.RESERVED.json'),record)


def start(config_path,go_path):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config,pipeline,checkpoint,context,key=validate_cell(config_path,go_path,True)
    attempt=ROOT/'attempts'/key
    attempt.mkdir(parents=True,mode=0o700,exist_ok=False)
    common.write(attempt/'ONCE.json',dict(execution=common.ref(config_path),go=common.ref(go_path),no_retry=True))
    with common.lock(Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')/f"physical{config['physical']}.lock"):
        report=sidecar.scan(config)
        common.write(attempt/'ACTUAL_ADMISSION.private.json',report)
        if not report['clear'] or report['blocking_reasons']:
            common.write(attempt/'REFUSED.json',dict(status='ADMISSION_REFUSED_NO_RETRY',calls_charged=0))
            return
        reservation=reserve(ROOT,dict(config,execution_ref=common.ref(config_path)),common.bound(config['lease'])['lease_end_unix'],time.time())
        duration=max(1,int(common.bound(reservation)['deadline_unix']-time.time()))
        environment=dict(PATH=os.environ.get('PATH','/usr/bin:/bin'),HOME=os.environ['HOME'],PYTHONPATH=config['source_root'],
            CUDA_VISIBLE_DEVICES=config['gpu_uuid'],PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',R172_EXECUTION_SHA256=common.ref(config_path)['sha256'],
            R172_GO_SHA256=common.ref(go_path)['sha256'])
        command=['timeout','--signal=TERM','--kill-after=15s',str(duration),config['python'],'-B','-m','r172_runner',
            'native','--config',str(config_path),'--go',str(go_path)]
        with (attempt/'stdout.private.txt').open('xb') as output,(attempt/'stderr.private.txt').open('xb') as errors:
            process=subprocess.Popen(command,cwd=config['source_root'],env=environment,stdin=subprocess.DEVNULL,stdout=output,stderr=errors)
            common.write(attempt/'TIMEOUT.json',dict(identity=sidecar.identity(process.pid),observed_unix=time.time()))
            returncode=process.wait()
        if returncode==0 and (attempt/'sealed/COMPLETE.json').exists():
            common.write(ROOT/'ledger'/(key+'.COMPLETE.json'),dict(status='COMPLETE',calls=3,reservation=reservation,completed_unix=time.time()))
        else:
            common.write(ROOT/'ledger'/(key+'.FAILED.json'),dict(status='FAILED_CHARGED_NO_RETRY',returncode=returncode,reservation=reservation))


def native(config_path,go_path):
    global USED
    common.require(not USED and os.getpid()==IMPORT_PID and os.environ.get('R172_EXECUTION_SHA256')==common.ref(config_path)['sha256']
        and os.environ.get('R172_GO_SHA256')==common.ref(go_path)['sha256'],'fresh_native_exact_GO_and_config')
    config,pipeline,checkpoint,context,key=validate_cell(config_path,go_path,True)
    common.require(os.environ.get('CUDA_VISIBLE_DEVICES')==config['gpu_uuid'],'one_visible_device')
    reservation=common.read(ROOT/'ledger'/(key+'.RESERVED.json'))
    common.require(reservation['execution']==common.ref(config_path),'charge_before_native')
    from gpu import orch_r130_checkpoint_benchmark as native_engine
    from gpu import orch_r130_benchmark_sidecar as sidecar
    USED=True
    output=ROOT/'attempts'/key/'sealed'
    output.mkdir(mode=0o700)
    common.write(output/'PROCESS.json',dict(identity=sidecar.identity(os.getpid()),observed_unix=time.time()))
    checksum=common.ref(config_path)['sha256']
    def check(label):
        common.require(time.time()<reservation['deadline_unix'] and common.ref(config_path)['sha256']==checksum,'config_and_original_job_wall')
    engine_plan=dict(model_dir=config['model_dir'],gpu_uuid=config['gpu_uuid'])
    allowance, read_ledger = receiving_allowance(config)
    read_ledger.reserve('native_model_load:'+key,config['life_id'],'adapter',sum(
        (Path(checkpoint['adapter_path'])/name).stat().st_size for name in checkpoint['adapter_files']))
    engine=native_engine._load_engine(engine_plan,checkpoint,check)
    prior.generate_probes(engine,config['condition'],context,output,checkpoint,engine_plan,check)
    check('complete')
    common.write(output/'COMPLETE.json',dict(status='COMPLETE',calls=3,execution_sha256=checksum,parent_access=False,
        checkpoint_commit_sha256=checkpoint['commit_sha256'],completed_unix=time.time()))


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('start','native'))
    parser.add_argument('--config',required=True)
    parser.add_argument('--go',required=True)
    arguments=parser.parse_args()
    (start if arguments.action=='start' else native)(Path(arguments.config),Path(arguments.go))


if __name__=='__main__':
    main()
