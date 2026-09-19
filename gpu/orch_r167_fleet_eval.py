"""Fixed-cell fleet probes. Private results, no learner or parent interfaces."""

import argparse
from copy import deepcopy
import hashlib
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from gpu import orch_r167_object_probe_queue as queue


protocol = queue.protocol
require = protocol.require
SCHEMA = 'R167_FIXED_FLEET_EVALUATOR_V1'
ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
IMPORT_PID = os.getpid()
USED = False
FIELDS = {'schema', 'pipeline', 'root', 'life_id', 'sleep', 'condition', 'capture', 'registration',
    'TRAIN_freeze', 'transfer', 'methods', 'source_root', 'sources', 'python', 'python_sha256',
    'model_dir', 'physical', 'gpu_uuid', 'service_path', 'service_sha256', 'lease', 'cpu_gate', 'builder',
    'release', 'authority', 'max_job_seconds'}
METHODS = dict(schema=SCHEMA, prompts=list(queue.PROBES), conditions=list(queue.CONDITIONS),
    max_new_tokens=512, calls_per_condition=3, call_cap=504, token_cap=258048,
    initial_and_next_completed_sleeps=3, fresh_process_per_checkpoint_condition=True,
    independent_birth_only_context_per_prompt=True, source='ORIGINAL_LANGUAGE_TRAIN_CHILD_WITNESSES',
    parent_history_in_prompt=False, evidence_in_prompt=False, private_outputs=True,
    lexical='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE',
    semantic_identity='CONDITION_BLIND_TWO_DISTINCTIVE_NONREDUNDANT_OBJECT_DETAILS_WITH_TRAIN_GROUNDING',
    leakage='ADJUDICATE_AGAINST_EXACT_BIRTH_SYSTEM_AND_PROBE_BEFORE_UNCUED_IDENTITY_CLAIM',
    recurrence='FAITHFUL_RECURRENCE_SUFFICIENT_FOR_IDENTITY_NO_NOVELTY_OR_EOS_REQUIREMENT',
    continuation='SEPARATE_FAITHFUL_RECURRENCE_AND_COHERENT_EXTENSION_FROM_IDENTITY',
    truncation='PRESERVE_FLAG_NOT_ABSENT_MEMORY',
    attention='REPORTED_TRAIN_GROUNDED_CHOICE_WHAT_HOW_HOW_MUCH_NOT_DEMONSTRATED_CAPABILITY',
    primary='PROMPT1_ON_NOT_OFF_EXPLORATORY_WITH_INITIAL_BASELINE_RECORDED',
    secondary='PROMPT2_AND_PROMPT3_SEPARATE_NOT_CONJOINED_WITH_PRIMARY',
    missing='UNSCORABLE_OR_MISSING_NOT_NEGATIVE', multiplicity='ALL_FIXED_CELLS_NO_OPTIONAL_STOPPING',
    semantic_status='RAW_GENERATION_THEN_PRIVATE_CONDITION_BLIND_ADJUDICATION_NO_PUBLIC_SCORES')


def expected_go(config_path, authority):
    return dict(schema=SCHEMA, status='MAIN_CONDITIONAL_FIXED_CELL_GO',
        execution=protocol.ref(config_path), authority=authority, calls=3, max_new_tokens=512, no_retry=True)


def registered_cell(config, pipeline, registration, life_plan):
    matches = [life for life in pipeline['lives'] if life['life_id'] == config['life_id']]
    require(len(matches) == 1 and matches[0]['status'] == 'SOURCE_CANDIDATE', 'registered_custody_candidate_only')
    life = matches[0]
    require(life_plan['life_id'] == life['life_id'] and life_plan['source_root'] == life['storage_root']
        and life_plan['birth_plan'] == life['birth_plan'] and life_plan['sleep_count'] == 3
        and life_plan['model_call_cap'] == 24 and life_plan['generated_token_cap'] == 12288,
        'same_life_birth_budget_and_next_three')
    key = queue.key(config['life_id'], config['sleep'], config['condition'])
    slots = [dict(key=queue.key(config['life_id'], sleep, condition), life_id=config['life_id'],
        sleep=sleep, condition=condition, model_calls=3) for sleep in queue.milestones(life_plan)
        for condition in queue.CONDITIONS]
    require(registration['slots'] == slots and any(slot['key'] == key for slot in slots), 'exact_registered_cell_no_relabel')
    return key, life


def validate(config_path, go_path=None):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    from gpu import orch_r130_checkpoint_benchmark as native
    config = protocol.read(config_path)
    require(set(config) == FIELDS and config['schema'] == SCHEMA and config['root'] == str(ROOT), 'exact_fleet_configuration')
    require(protocol.sha(config['authority']['path']) == config['authority']['sha256'], 'exact_Main_conditional_authority')
    if go_path is not None:
        require(os.environ.get('R167_FLEET_GO_SHA256') == protocol.sha(go_path)
            and protocol.read(go_path) == expected_go(config_path, config['authority']), 'exact_delegated_GO')
    pipeline = protocol.bound(config['pipeline'])
    require(pipeline['schema'] == 'R167_FLEET_SOURCE_GENERATION2_V1'
        and pipeline['call_cap'] == 504 and pipeline['token_cap'] == 258048
        and len(pipeline['lives']) == 21 and pipeline['hard_end_unix'] == 1789659000
        and pipeline['physical_slots'] == [0, 1], 'fixed504_21life_window')
    registered = protocol.bound(config['registration'])
    life_plan = protocol.bound(registered['plan'])
    key, life = registered_cell(config, pipeline, registered, life_plan)
    authority = protocol.bound(life_plan['source_authority'])
    custody = protocol.bound(authority['registration_observation'])
    require(authority['status'] == 'MAIN_SOURCE_READ_COPY_GO' and authority['read_end_unix'] <= pipeline['hard_end_unix']
        and custody['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED' and custody['identity_rechecked'] is True
        and custody['registry_plan_birth_context_matches'] is True
        and custody['last_completed_sleep'] + 1 == life_plan['first_sleep']
        and custody['source_root'] == life['storage_root'] and custody['observed_unix'] <= life_plan['frozen_unix'],
        'trusted_source_registration_not_partial_custody')
    capture = protocol.bound(config['capture'])
    require(capture['status'] == 'IMMUTABLE_ADAPTER_BIRTH_CUSTODY', 'complete_capture_only')
    boundary = protocol.bound(capture['boundary'])
    require(boundary['life_id'] == config['life_id'] and boundary['sleep'] == config['sleep']
        and boundary['source_root'] == life['storage_root'] and boundary['birth_plan'] == life['birth_plan']
        and boundary['source_authority'] == life_plan['source_authority'], 'exact_source_checkpoint_boundary')
    manifest = protocol.bound(capture['manifest'])
    context = protocol.bound(capture['birth'])
    require(set(context) == {'system_prompt', 'birth_prompt'} and protocol.digest(context) == boundary['context_sha256'],
        'exact_original_birth_no_other_context')
    transfer = protocol.bound(config['transfer'])
    require(transfer['status'] == 'EXACT_RECEIVING_COPY_VERIFIED' and transfer['life_id'] == config['life_id']
        and transfer['sleep'] == config['sleep'] and transfer['capture'] == config['capture']
        and transfer['source_plan_sha256'] == config['pipeline']['sha256'], 'receiving_transfer_binding')
    checkpoint = native.verify_checkpoint(manifest, Path(capture['manifest']['path']).parent)
    require(Path(checkpoint['adapter_path']) == ROOT / 'lives' / config['life_id'] / 'captures' /
        f"{config['sleep']:06d}" / 'adapter', 'immutable_copied_adapter_only')
    commit = protocol.read(checkpoint['commit_path'])
    require(checkpoint['commit_sha256'] == boundary['commit']['sha256'], 'original_COMMIT_join')
    if config['sleep'] == 0:
        require(commit['optimizer_steps'] == 0, 'zero_update_initial')
    else:
        require(commit['created_unix'] > life_plan['frozen_unix'], 'prospective_checkpoint_after_registration')
    frozen = protocol.bound(config['TRAIN_freeze'])
    require(frozen['status'] == 'PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE'
        and frozen['model_calls'] == 0 and queue.finite(frozen['frozen_unix'])
        and 0 < frozen['frozen_unix'] <= time.time()
        and protocol.sha(frozen['evidence']['path']) == frozen['evidence']['sha256'],
        'private_preoutput_TRAIN_freeze')
    require(protocol.bound(config['methods']) == METHODS, 'frozen_probe_specific_methods')
    source = protocol.regular(config['source_root'])
    require(source == Path(__file__).resolve().parents[1] and
        {'gpu/orch_r167_fleet_eval.py', 'tests/test_orch_r167_fleet_eval.py'} | set(native.REQUIRED_SOURCES)
        <= set(config['sources']), 'actual_complete_frozen_runtime')
    for name, checksum in config['sources'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and protocol.sha(source/name) == checksum,
            'frozen_source_pin')
    require(all(str(path.relative_to(source)) in config['sources'] for directory in ('gpu', 'organism_v6')
        for path in (source/directory).rglob('*.py')), 'complete_python_closure')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == sidecar.HOST_SHA256
        and type(config['physical']) is int and config['physical'] in (0,1)
        and config['gpu_uuid'] == sidecar.DEVICES[config['physical']], 'node2_devices_only')
    require(protocol.sha(config['python']) == config['python_sha256'], 'exact_existing_interpreter')
    require(protocol.sha(config['service_path']) == config['service_sha256'], 'existing_service_identity_pin')
    lease = protocol.bound(config['lease'])
    require(lease['node'] == 'ovx' and lease['uuid_by_index'][config['physical']] == config['gpu_uuid']
        and lease['hard_deadline_unix'] == lease['lease_end_unix']-21600
        and pipeline['hard_end_unix'] <= lease['hard_deadline_unix'], 'existing_lease_no_extension')
    require(type(config['max_job_seconds']) is int and 60 <= config['max_job_seconds'] <= 900, 'finite_job_window')
    gate = protocol.bound(config['cpu_gate'])
    require(gate['status'] == 'PASS' and gate['helper_sha256'] == protocol.sha(__file__)
        and gate['tests_sha256'] == config['sources']['tests/test_orch_r167_fleet_eval.py'], 'receiving_CPU_gate')
    builder = protocol.bound(config['builder'])
    require(builder['status'] == 'CPU_AND_PROVENANCE_PASS' and builder['cpu_gate'] == config['cpu_gate']
        and builder['pipeline'] == config['pipeline'] and builder['authority'] == config['authority'], 'dated_builder_gate')
    release = protocol.bound(config['release'])
    require(release['status'] == 'ALL38_RETROSPECTIVE_NATIVE_TIMEOUT_WRAPPERS_RELEASED'
        and release['complete'] == 38 and release['failed'] == 0 and release['unresolved'] == 0, 'previous_exact_release')
    return config, pipeline, checkpoint, context, key


def budget(root, pipeline_hash):
    rows = [protocol.read(path) for path in (root/'ledger').glob('*.RESERVED.json')]
    require(all(row['pipeline_sha256'] == pipeline_hash and row['calls_charged'] == 3
        and row['tokens_charged'] == 1536 for row in rows), 'existing_charges_unchanged')
    require(len({row['key'] for row in rows}) == len(rows) <= 168, 'unique_fixed_cells')
    return dict(calls_charged=len(rows)*3, tokens_charged=len(rows)*1536,
        complete=len(list((root/'ledger').glob('*.COMPLETE.json'))),
        failed=len(list((root/'ledger').glob('*.FAILED.json'))), reserved=len(rows))


def reserve(config_path, config, pipeline, key):
    root = Path(config['root'])
    with protocol.lock(root/'budget.lock'):
        counts = budget(root, config['pipeline']['sha256'])
        require(counts['calls_charged'] + 3 <= 504 and counts['tokens_charged'] + 1536 <= 258048, 'fixed_aggregate_budget')
        now = time.time()
        require(1789637400 <= now and now + config['max_job_seconds'] + 15 < pipeline['hard_end_unix'], 'full_job_before_absolute_wall')
        reservation = dict(key=key, execution=protocol.ref(config_path), pipeline_sha256=config['pipeline']['sha256'],
            physical=config['physical'], calls_charged=3, tokens_charged=1536, reserved_unix=now,
            deadline_unix=min(now+config['max_job_seconds'], pipeline['hard_end_unix']), no_retry=True)
        (root/'ledger').mkdir(exist_ok=True, mode=0o700)
        return protocol.write(root/'ledger'/(key+'.RESERVED.json'), reservation)


def dispatch(config_path, go_path):
    require(go_path is not None, 'explicit_Main_GO_required')
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config, pipeline, checkpoint, context, key = validate(config_path, go_path)
    root = Path(config['root'])
    attempt = root/'attempts'/key
    attempt.mkdir(parents=True, mode=0o700, exist_ok=False)
    protocol.write(attempt/'ONCE.json', dict(execution=protocol.ref(config_path), go=protocol.ref(go_path), entered_unix=time.time()))
    shared = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
    with protocol.lock(shared/f"physical{config['physical']}.lock"):
        require(not any(protocol.read(path)['physical'] == config['physical'] and not any(
            path.with_name(path.name.replace('.RESERVED.', '.'+kind+'.')).exists() for kind in ('COMPLETE','FAILED'))
            for path in (root/'ledger').glob('*.RESERVED.json')), 'prior_physical_unresolved')
        report = sidecar.scan(config)
        protocol.write(attempt/'ACTUAL_ADMISSION.private.json', report)
        if not report['clear'] or report['blocking_reasons']:
            protocol.write(attempt/'REFUSED.json', dict(status='DEVICE_BUSY_NO_RETRY', calls_charged=0))
            return dict(status='DEVICE_BUSY_NO_RETRY', calls_charged=0)
        validate(config_path, go_path)
        reservation = reserve(config_path, config, pipeline, key)
        environment = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=str(root/'empty_home'),
            CUDA_VISIBLE_DEVICES=config['gpu_uuid'], PYTHONPATH=config['source_root'], PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
            R167_FLEET_GO_SHA256=protocol.sha(go_path), R167_FLEET_EXECUTION_SHA256=protocol.sha(config_path))
        process = None
        try:
            with (attempt/'runner.private.log').open('x') as log:
                process = subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s',str(config['max_job_seconds'])+'s',
                    config['python'],'-B','-m','gpu.orch_r167_fleet_eval','evaluate','--config',str(config_path),'--go',str(go_path)],
                    cwd=attempt, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
                protocol.write(attempt/'LAUNCH.json', dict(identity=sidecar.identity(process.pid), execution=protocol.ref(config_path),
                    calls_charged=3, observed_unix=time.time()))
                returncode = process.wait()
            complete = protocol.read(attempt/'sealed/COMPLETE.json')
            require(returncode == 0 and complete['calls'] == 3 and complete['execution_sha256'] == protocol.sha(config_path)
                and protocol.released(process, attempt, sidecar), 'actual_native_complete_and_released')
            protocol.write(root/'ledger'/(key+'.COMPLETE.json'), dict(status='COMPLETE', reservation=reservation,
                calls=3, completed_unix=time.time()))
        except BaseException:
            if protocol.released(process, attempt, sidecar):
                protocol.write(root/'ledger'/(key+'.FAILED.json'), dict(status='FAILED_NO_RETRY', reservation=reservation))
            else:
                protocol.write(attempt/'UNRESOLVED.json', dict(status='UNRESOLVED_NO_RETRY', reservation=reservation))
            raise
    return dict(status='METADATA_ONLY', **budget(root, config['pipeline']['sha256']))


def generate_probes(engine, condition, context, output, checkpoint, engine_plan, check):
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu.orch_r107_capability_run import readonly_condition
    before = native._snapshot(engine, engine_plan, checkpoint)
    protocol.write(output/'BEFORE.private.json', before)
    for position, prompt in enumerate(queue.PROBES):
        check('call')
        messages = protocol.messages(context, prompt)
        original = deepcopy(messages)
        tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        protocol.write(output/f'{position}.RESERVED.private.json', dict(position=position, max_new_tokens=512))
        with readonly_condition(engine.model, condition):
            native._require_readonly(engine.model, condition)
            response = engine.generate(messages, max_new_tokens=512)
        protocol.write(output/f'{position}.RAW.private.json', response)
        require(messages == original, 'no_cross_probe_context_mutation')
        native._validate_response(response, original, len(tokens), engine.tokenizer.eos_token_id)
    after = native._snapshot(engine, engine_plan, checkpoint)
    require(after == before, 'unchanged_adapter_and_frozen_base')
    protocol.write(output/'AFTER.private.json', after)


def evaluate(config_path, go_path):
    global USED
    require(go_path is not None, 'explicit_Main_GO_required')
    require(os.getpid() == IMPORT_PID and not USED, 'fresh_process_one_checkpoint_condition')
    require(os.environ.get('R167_FLEET_EXECUTION_SHA256') == protocol.sha(config_path), 'fresh_dispatch_binding')
    config, pipeline, checkpoint, context, key = validate(config_path, go_path)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['gpu_uuid'], 'single_visible_device')
    reservation = protocol.read(ROOT/'ledger'/(key+'.RESERVED.json'))
    require(reservation['execution'] == protocol.ref(config_path), 'charge_before_native')
    USED = True
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu import orch_r130_benchmark_sidecar as sidecar
    output = ROOT/'attempts'/key/'sealed'
    output.mkdir(mode=0o700)
    protocol.write(output/'PROCESS.json', dict(identity=sidecar.identity(os.getpid()), observed_unix=time.time()))
    config_hash = protocol.sha(config_path)
    def check(label):
        require(time.time() < reservation['deadline_unix'] and protocol.sha(config_path) == config_hash, 'immutable_config_and_wall')
    engine_plan = dict(model_dir=config['model_dir'], gpu_uuid=config['gpu_uuid'])
    engine = native._load_engine(engine_plan, checkpoint, check)
    generate_probes(engine, config['condition'], context, output, checkpoint, engine_plan, check)
    check('complete')
    protocol.write(output/'COMPLETE.json', dict(status='COMPLETE', execution_sha256=config_hash, calls=3,
        checkpoint_commit_sha256=checkpoint['commit_sha256'], completed_unix=time.time(), parent_access=False,
        semantic_status='NOT_YET_ADJUDICATED', receipts={path.name:protocol.sha(path) for path in output.iterdir() if path.is_file()}))
    return dict(status='COMPLETE', calls=3)


def launch(config_path, go_path, directory, worker=False):
    require(go_path is not None, 'explicit_Main_GO_required')
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config, pipeline, checkpoint, context, key = validate(config_path, go_path)
    require(directory == ROOT/'launches'/key, 'exact_once_wrapper_directory')
    if not worker:
        directory.mkdir(parents=True, mode=0o700, exist_ok=False)
        protocol.write(directory/'INITIATOR.json', dict(identity=sidecar.identity(os.getpid())))
        with (directory/'wrapper.private.log').open('x') as log:
            process = subprocess.Popen([sys.executable,'-B','-m','gpu.orch_r167_fleet_eval','wrapper',
                '--config',str(config_path),'--go',str(go_path),'--directory',str(directory)],
                cwd=directory,env=dict(os.environ,PYTHONPATH=config['source_root']),stdin=subprocess.DEVNULL,
                stdout=log,stderr=log,start_new_session=True)
        return dict(status='WRAPPER_STARTED_NOT_ADMITTED', identity=sidecar.identity(process.pid))
    time.sleep(5)
    require(sidecar.gone(protocol.read(directory/'INITIATOR.json')['identity']), 'initiator_detached_before_admission')
    protocol.write(directory/'WRAPPER.json', dict(identity=sidecar.identity(os.getpid()), created_unix=time.time()))
    try:
        result = dispatch(config_path, go_path)
        protocol.write(directory/'DISPOSITION.json', result)
        return result
    except BaseException as error:
        protocol.write(directory/'DISPATCH_ERROR.json', dict(status='FAILED_NO_RETRY', error_type=type(error).__name__))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('validate','start','wrapper','evaluate'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--go', type=Path)
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    if args.action == 'validate':
        validate(args.config, args.go)
        result = dict(status='CPU_PROVENANCE_READY', calls=0)
    elif args.action in ('start','wrapper'):
        result = launch(args.config, args.go, args.directory, worker=args.action == 'wrapper')
    else:
        result = evaluate(args.config, args.go)
    print(protocol.json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
