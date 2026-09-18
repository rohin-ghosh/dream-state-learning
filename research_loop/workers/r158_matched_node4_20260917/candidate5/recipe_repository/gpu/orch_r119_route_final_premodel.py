"""Single authorized pre-model FINAL admission repair; preserve original science."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'immutable_reference')
    return json.loads(Path(reference['path']).read_bytes())


def load(reference, name):
    require(sha(reference['path']) == reference['sha256'], 'immutable_source')
    spec = importlib.util.spec_from_file_location(name, reference['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def zero_input(root):
    root = Path(root)
    for name in ('RESERVATIONS.jsonl', 'DISPATCH.json', 'ADMISSION.json', 'FINISHED.json',
                 'TIMEOUT.json', 'sealed_final_readouts'):
        require(not (root / name).exists(), 'any_input_or_dispatch_evidence_prohibits_recovery')
    live = []
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            continue
        if str(root).encode() in arguments and b'readout' in arguments:
            live.append(int(directory.name))
    require(not live, 'live_evaluator_prohibits_recovery')
    return dict(model_dispatch_receipt=False,ledger_exists=False,capture_directory_exists=False,
                live_matching_evaluator_pids=live,model_inputs_charged=0)


def verify(control, final):
    require(control['source']['sha256'] == sha(__file__), 'exact_new_source')
    config = final.validate_config(control['config'])
    final.window(config, time.time())
    require(config['source'] == control['scheduler'] and config['native_calls'] == 48
            and config['end_unix'] <= final.END, 'unchanged_original_evaluation')
    require(config['parent_calls'] == config['optimizer_steps'] == config['training_rows'] == 0,
            'evaluation_only')
    root = Path(config['root'])
    require(control['preserved']['ATTEMPT.json']['path'] == str(root / 'ATTEMPT.json')
            and control['preserved']['FAILED.json']['path'] == str(root / 'FAILED.json'),
            'actual_failed_root')
    for reference in control['preserved'].values():
        require(sha(reference['path']) == reference['sha256'], 'old_evidence_byte_identical')
    failure = bound(control['preserved']['FAILED.json'])
    require(failure['exception_type'] == 'ValueError' and failure['error_sha256'] ==
            hashlib.sha256(b'strict_fresh_CLEAR').hexdigest(), 'only_premodel_scan_failure')
    proof = zero_input(root)
    attempt = bound(control['preserved']['ATTEMPT.json'])
    selected = final.selection_checkpoint(config, time.time())
    require(attempt['selection'] == final.ref(config['selection_path'])
            and attempt['checkpoint'] == selected['checkpoint'], 'same_1700_selection')
    release = final.release_evidence(config)
    require(Path(config['sealed_final']['path']).resolve() == (root / 'SEALED_FINAL.json').resolve(),
            'same_materialized_sealed_source_without_content_read')
    return config, dict(zero_input=proof,release=release,selection=attempt['selection'],
        checkpoint=attempt['checkpoint'],inventory_CPU_materialized_before_failed_admission=True,
        held_input_dispatched_to_model=False,scientific_runtime=control['scheduler'])


def scan(control, final):
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_only')
    config, proof = verify(control, final)
    for name, expected in bound(control['scanner_source_map']).items():
        require(sha(name) == expected, 'frozen_scanner_source_closure')
    scanner = load(control['scanner'], 'prior_tested_concurrent_scan')
    sys.path.insert(0, control['scanner_import_root'])
    request = dict(root=config['root'], attempt_directory=control['directory'],
                   dependencies=control['scanner_dependencies'])

    def evaluation_window(unused):
        final.window(config, time.time())

    function = FunctionType(scanner.scan.__code__, dict(scanner.scan.__globals__,
        validate_window=evaluation_window), 'same_combined_proof_FINAL_window', scanner.scan.__defaults__)
    lifecycle = SimpleNamespace(verify_plan=lambda root: final.read(Path(root) / 'PLAN.json'))
    return function(request, lifecycle)


def execute(control, reference, final):
    require(control.get('launch_authorized') is True, 'Main_launch_permission_required')
    cpu = bound(control['cpu'])
    require(cpu['returncode'] == 0 and cpu['source_sha256'] == sha(__file__), 'own_CPU_provenance')
    directory = Path(control['directory'])
    root = Path(final.bound(control['config'])['root'])
    with (root / 'SCHEDULER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config, proof = verify(control, final)
        final.write(directory / 'REPAIR_ATTEMPT.json', dict(started_unix=time.time(),proof=proof))

        def admission(same_config):
            command = ['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                       sys.executable,'-B',str(Path(__file__).resolve()),'scan','--control',
                       reference['path'],'--control-sha256',reference['sha256']]
            result = subprocess.run(command,capture_output=True,text=True,check=True,
                                    timeout=min(100,config['end_unix']-time.time()))
            report = json.loads(result.stdout)
            require(report['clear'] is True and time.time()-report['scanned_unix'] < 30,'strict_fresh_CLEAR')
            zero_input(root)
            final.write(root / 'ADMISSION.json',report)
            return final.ref(root / 'ADMISSION.json')

        def checked_require(value, reason):
            if reason == 'prior_attempt_preserved_no_replay':
                verify(control,final)
            else:
                final.require(value,reason)

        def preserved_write(path, value):
            target = directory / 'EVALUATION_ATTEMPT.json' if Path(path) == root / 'ATTEMPT.json' else path
            final.write(target,value)

        def already_materialized(same_config, now):
            final.window(same_config,now)
            verify(control,final)

        dispatch = FunctionType(final.dispatch.__code__,dict(final.dispatch.__globals__,
            require=checked_require,write=preserved_write,admission=admission,
            materialize=already_materialized),'same_frozen_FINAL_dispatch',final.dispatch.__defaults__)
        try:
            return dispatch(config)
        except BaseException as error:
            final.write(directory / 'REPAIR_FAILED.json',dict(failed_unix=time.time(),
                exception_type=type(error).__name__,error_sha256=hashlib.sha256(str(error).encode()).hexdigest(),
                no_retry=True,old_failed_preserved=True))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('verify','scan','execute'))
    parser.add_argument('--control',required=True)
    parser.add_argument('--control-sha256',required=True)
    args = parser.parse_args()
    reference = dict(path=args.control,sha256=args.control_sha256)
    control = bound(reference)
    final = load(control['scheduler'],'same_frozen_FINAL')
    if args.phase == 'verify':
        config, result = verify(control,final)
    elif args.phase == 'scan':
        result = scan(control,final)
    else:
        result = execute(control,reference,final)
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
