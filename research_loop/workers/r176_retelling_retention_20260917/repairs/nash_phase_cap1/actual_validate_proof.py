"""Run only the unchanged validator with actual persisted read charges, never start."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
GO_PATH = Path('/__R176_I1_memory_fixture_NOT_GO_never_written__')
REVIEW_PATH = '/__R176_I1_memory_fixture_NOT_REVIEW_never_written__'
RUNNER_SHA = '4ff1c97b374930b2b6e4c96d2f8d24fbedcdccfaae8c07471edd52720d7a6952'
HELPER_SHA = '1fcb8f90a1f98ad38389af87b1527c11c018da65369588ec720005fa24229681'


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':')).encode()


class NoModelImports:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'peft', 'tensorflow', 'jax', 'vllm'}:
            raise RuntimeError('CPU_proof_model_import_forbidden')
        return None


def main():
    os.umask(0o077)
    sys.dont_write_bytecode = True
    request_raw = sys.stdin.buffer.read(512 * 1024)
    request = json.loads(request_raw)
    proof_root = Path(request['proof_root'])
    if not proof_root.is_relative_to(ROOT / 'metadata_repair_actual_proof1'):
        raise RuntimeError('exact_new_proof_root')
    proof_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    bootstrap = dict(charged_bytes=request['staging_charge_bytes'], reads=0, active=True, busy=False,
        staging_charge_bytes=request['staging_charge_bytes'])

    def write(path, document):
        raw = canonical(document)
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())

    def is_private_write(path):
        return Path(os.fsdecode(path)).absolute().is_relative_to(proof_root)

    def guard(event, arguments):
        if event in {'os.remove', 'os.rename', 'os.rmdir', 'os.chown', 'os.truncate', 'os.kill',
                'os.killpg', 'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
                'socket.connect', 'socket.bind'}:
            raise RuntimeError('CPU_proof_side_effect_forbidden')
        if event in {'os.mkdir', 'os.chmod'} and arguments and not isinstance(arguments[0], int):
            if not is_private_write(arguments[0]):
                raise RuntimeError('CPU_proof_external_write_forbidden')
        if event != 'open' or not arguments or not isinstance(arguments[0], (str, bytes)):
            return
        path = Path(os.fsdecode(arguments[0])).absolute()
        mode = arguments[1] if len(arguments) > 1 else None
        flags = arguments[2] if len(arguments) > 2 else 0
        writing = isinstance(mode, str) and any(marker in mode for marker in 'wax+')
        writing = writing or isinstance(flags, int) and flags & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writing:
            if not is_private_write(path):
                raise RuntimeError('CPU_proof_external_write_forbidden')
            return
        if not bootstrap['active'] or bootstrap['busy'] or not path.is_relative_to(ROOT) or not path.is_file():
            return
        bootstrap['busy'] = True
        try:
            size = path.stat().st_size
            if path != path.resolve() or bootstrap['charged_bytes'] + size > request['bootstrap']['document']['bytes']:
                raise RuntimeError('CPU_proof_bootstrap_cap')
            write(proof_root / ('BOOTSTRAP_READ_%06d.json' % bootstrap['reads']), dict(path=str(path), bytes=size,
                authority=request['bootstrap']['reference'], status='CHARGED_BEFORE_READ_NO_REFUND'))
            bootstrap['charged_bytes'] += size
            bootstrap['reads'] += 1
        finally:
            bootstrap['busy'] = False

    sys.addaudithook(guard)
    sys.meta_path.insert(0, NoModelImports())
    write(proof_root / 'REQUEST.private.json', request)
    sys.path[:0] = [str(ROOT / 'runner_candidate1/source'), str(ROOT / 'receiving_source1/source')]
    import r176_runner as runner
    import preparation_io as common

    common.require(common.sha(Path(runner.__file__).read_bytes()) == RUNNER_SHA
        and common.sha(Path(common.__file__).read_bytes()) == HELPER_SHA, 'unchanged_reviewed_runner_helper')
    public_raw = Path(request['candidate_public']['path']).read_bytes()
    common.require(common.sha(public_raw) == request['candidate_public']['sha256'], 'exact_new_candidate_receipt')
    public = json.loads(public_raw)
    execution = request['execution']
    common.require(execution in public['executions'], 'exact_two_opaque_configs')
    config_raw = Path(execution['path']).read_bytes()
    common.require(common.sha(config_raw) == execution['sha256'], 'exact_new_config_bytes')
    config = json.loads(config_raw)
    config['execution'] = execution
    phase = request['phase']
    reader = runner.phase_reader(config, phase, proof_root)
    original_authorities = reader.authority
    for kind in ('metadata', 'adapter'):
        entry = request['proof_allowances'][kind]
        document = entry['document']
        common.require(common.digest(document) == entry['reference']['sha256'] and document['scope_sha256'] == common.SCOPE_SHA
            and document['status'] == 'PRECHARGED_NO_REFUND' and document['life_id'] == 'C2'
            and document['kind'] == kind, 'real_separate_proof_reservation')
        original_cap = original_authorities[kind]['document']['bytes']
        common.require(document['bytes'] == original_cap if kind == 'metadata' else document['bytes'] <= original_cap,
            'no_relaxation_of_actual_phase_caps')
    adapter_authority = request['proof_allowances']['adapter']['document']
    common.require(adapter_authority['execution_sha256'] == execution['sha256']
        and adapter_authority['phase'] == phase and adapter_authority['sleep'] == 33,
        'exact_supplemental_proof_pair_phase')
    reader.authority = request['proof_allowances']

    go = {field: public[field] for field in ('executions', 'source', 'runner_sha256', 'cpu_gate',
        'runner_cpu_gate', 'old_release')}
    go.update(status='MAIN_R176_EXECUTION_GO', no_reset=True, call_cap=72, token_cap=36864,
        process_cap=24, physical_slots=[0, 1], absolute_end_unix=common.END, active_seconds_max=5400,
        gpu_slot_seconds_max=10800, provider_calls=0, baseline_new_calls=0,
        independent_review=dict(path=REVIEW_PATH, sha256='in-memory-NOT-AUTHORIZATION'))
    review = dict(go, status='APPROVE', independent=True, reviewer='SYNTHETIC_CPU_FIXTURE_NOT_REVIEW_APPROVAL')
    original_bound = runner.bound
    original_read_bytes = Path.read_bytes

    def memory_bound(reference):
        return review if reference['path'] == REVIEW_PATH else original_bound(reference)

    def memory_read_bytes(path):
        return common.canonical(go) if path == GO_PATH else original_read_bytes(path)

    runner.bound = memory_bound
    Path.read_bytes = memory_read_bytes
    forbidden = {(str(Path(runner.__file__)), name) for name in ('start', 'enter', 'native_run', 'reserve')}
    forbidden.add((str(runner.MODEL_SOURCE / 'gpu/orch_r130_benchmark_sidecar.py'), 'scan'))

    def profile(frame, event, argument):
        if event == 'call' and (frame.f_code.co_filename, frame.f_code.co_name) in forbidden:
            raise RuntimeError('CPU_proof_execution_entrypoint_forbidden')

    bootstrap['active'] = False
    runner.charge_open_reads(reader, runner.MODEL_SOURCE, config)
    sys.setprofile(profile)
    try:
        runner.validate(config, GO_PATH)
        status, reason = 'COMPLETE_ACTUAL_VALIDATOR_PASS', None
    except Exception as error:
        status = 'ACTUAL_VALIDATOR_FAILED_PRESERVED_NO_RETRY'
        safe = {'delegated_read_cap', 'CPU_proof_side_effect_forbidden', 'CPU_proof_external_write_forbidden',
            'CPU_proof_model_import_forbidden', 'CPU_proof_execution_entrypoint_forbidden'}
        reason = str(error) if str(error) in safe else type(error).__name__
    finally:
        sys.setprofile(None)
    result = dict(schema='R176_I1_COMPLETE_ACTUAL_VALIDATOR_CHARGED_CPU_PROOF_V1', status=status, reason=reason,
        observed_unix=time.time(), execution=execution, phase=phase, runner_sha256=RUNNER_SHA,
        preparation_io_sha256=HELPER_SHA, candidate_public=request['candidate_public'],
        phase_cap_bytes={kind: original_authorities[kind]['document']['bytes'] for kind in ('metadata', 'adapter')},
        proof_cap_bytes={kind: reader.authority[kind]['document']['bytes'] for kind in ('metadata', 'adapter')},
        phase_charge_counters_bytes=reader.charged, persisted_read_records=reader.sequence,
        all_phase_charges_persisted=status == 'COMPLETE_ACTUAL_VALIDATOR_PASS',
        read_ledger_path=str(reader.root / 'reads'), bootstrap=bootstrap,
        metadata_headroom_bytes=reader.authority['metadata']['document']['bytes'] - reader.charged['metadata'],
        production_allowances_consumed=False, original_phase_authorities_validated=True,
        separate_supplemental_proof_authorities=request['proof_allowances'],
        actual_reader_charge_and_write_unchanged=True, both_authorization_inputs_synthetic_in_memory_only=True,
        authorization_fixtures_written_to_disk=False, full_actual_validate_called=True,
        model_calls=0, provider_calls=0, scanner_invocations=0, execution_attempts_consumed=0,
        GPU_admission_attempted=False, execution_authorized=False, private_content_exported=False,
        source=public['source'], cpu_gate=public['cpu_gate'], runner_cpu_gate=public['runner_cpu_gate'])
    public_result = dict(result)
    public_result['separate_supplemental_proof_authorities'] = {
        kind: entry['reference'] for kind, entry in request['proof_allowances'].items()}
    write(proof_root / 'PUBLIC_METADATA.json', public_result)
    print(json.dumps(public_result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='CPU_PROOF_SETUP_ERROR_PRESERVED_NO_RETRY', error_type=type(error).__name__,
            model_calls=0, provider_calls=0, execution_authorized=False, private_content_exported=False)))
        sys.exit(2)
