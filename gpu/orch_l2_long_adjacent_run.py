"""One-shot LONG C1 readout using imported adjacent/native infrastructure."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from gpu import orch_guided_native as native
from gpu import orch_l2_adjacent_run as infrastructure
from gpu.orch_l2_shared_run import spend, write
from organism_v6 import orch_l2_adjacent as adjacent
from organism_v6 import orch_l2_long_adjacent as diagnostic


ROOT = Path('/tmp/orch_l2_long_adjacent_20260915_attempt1')
SHARED = Path('/tmp/orch_l2_shared_20260914_attempt1')
RUNTIME = Path(__file__).resolve().parents[1]
FILES = ('gpu/orch_l2_long_adjacent_run.py', 'organism_v6/orch_l2_long_adjacent.py',
         'tests/test_orch_l2_long_adjacent.py', 'gpu/orch_l2_adjacent_run.py',
         'organism_v6/orch_l2_adjacent.py')
DEVICES = {'PREVIOUS': (0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
           'OUTPUT': (1, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b')}
SCANNER_FILES = {'scanner.py': '6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b',
                 'service_exceptions.json': '4a96b33797ab47ed7a1685de0ffe6c7ec4d210c143b720b85519b0ca05265391'}
require = adjacent.require
read = adjacent.read
file_hash = adjacent.bridge.file_sha256
immutable = infrastructure.immutable


def own_root(root):
    require(root == ROOT and root.resolve() == ROOT and RUNTIME == root / 'source_runtime_v2',
            'exact_own_remote_root_and_runtime_required')
    return root


def code_hashes():
    return {name: file_hash(RUNTIME / name) for name in FILES}


def copy_input(source, destination):
    expected = file_hash(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    require(file_hash(destination) == expected, 'input_copy_hash_drift')
    return expected


def scan(root, side, label):
    index, uuid = DEVICES[side]
    for name, expected in SCANNER_FILES.items():
        require(file_hash(root / 'inputs' / name) == expected, 'full_scanner_binding_changed')
    with (root / 'inputs/service_exceptions.json').open() as exceptions:
        result = subprocess.run(['python3', str(root / 'inputs/scanner.py'), str(index), uuid],
                                stdin=exceptions, capture_output=True, text=True, timeout=45,
                                env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    report = json.loads(result.stdout)
    rows = [list(map(str.strip, row.split(','))) for row in report['gpus'].splitlines()]
    target = next(row for row in rows if row[0] == str(index))
    report['safe'] = (result.returncode == 0 and report['clear'] and not report['owners']
                      and not report['unresolved'] and target[1] == uuid and 'A100' in target[2]
                      and int(target[5]) <= 2)
    report['stderr'] = result.stderr
    write(root / 'scans' / f'{time.time_ns()}_{label}_{side}.json', report)
    require(report['safe'], 'full_scanner_not_clear:' + side)
    return report


def prepare(root):
    own_root(root)
    require(not (root / 'PROTOCOL.json').exists() and not (root / 'LIFETIME.json').exists(), 'no_reprepare')
    selection = diagnostic.select_first(SHARED)
    inputs = root / 'inputs'
    inputs.mkdir(exist_ok=True)
    names = ('INITIAL.json', 'COHORT.json', 'SOURCE.json', 'LEGACY_READOUT.json', 'PREPARE.json',
             'PREPARE_RUNTIME_V2.json', 'LONG/cycle1/sleep/COMPLETE.json',
             'LONG/cycle1/sleep/LOADED.json', 'LONG/cycle1/sleep/LOSSES.jsonl') + tuple(SCANNER_FILES)
    copied = {}
    for name in names:
        destination = inputs / name
        copied[name] = copy_input(SHARED / name, destination)
    require(diagnostic.select_first(inputs) == selection, 'selection_copy_drift')
    inspected = adjacent.verify_inputs(inputs, RUNTIME)
    identities = {}
    for side in diagnostic.SIDES:
        original = selection['previous' if side == 'PREVIOUS' else 'output']
        adjacent.bridge.AdapterIdentity.from_document(original)
        destination = root / side / 'adapter'
        if not destination.exists():
            shutil.copytree(original['path'], destination)
        identities[side] = adjacent.bridge.AdapterIdentity.from_document(
            dict(original, path=str(destination))).document()
    model_dir = read(inputs / 'PREPARE.json')['model_dir']
    model_files = infrastructure.verify_model_files(model_dir, read(root / 'MODEL_FILES_A100.json'))
    cpu = read(root / 'CPU_TEST_RECEIPT.json')
    require(cpu['passed'] is True and cpu['code_sha256'] == code_hashes(), 'bound_CPU_tests_required')
    scans = {side: scan(root, side, 'prepare') for side in diagnostic.SIDES}
    protocol = dict(name=root.name, created_unix=time.time(), selection=selection, inputs=inspected,
                    input_files=copied, shared_root=str(SHARED), input_root=str(inputs),
                    model_dir=model_dir, model_files=model_files, identities=identities,
                    code_sha256=code_hashes(), cpu_receipt_sha256=file_hash(root / 'CPU_TEST_RECEIPT.json'),
                    preflight=scans, devices=DEVICES, claim=diagnostic.CLAIM, disclosure=diagnostic.DISCLOSURE,
                    parent=None, training=False, replay=False, regenerate_cohort=False,
                    native_processes=2, maximum_calls=inspected['budget']['worst_case_total'],
                    assigned_gpu_hours_limit=2, lifetime_seconds=3600, restart_allowed=False,
                    policy='Original launch-attempt lifetime includes scanning/load; no clock reset; no additional tasks')
    immutable(root / 'SELECTION.json', selection)
    immutable(root / 'PROTOCOL.json', protocol)
    return dict(status='CPU_PROVENANCE_READY_AWAITING_MAIN_BUILDER_RECEIPT', native_calls=0,
                protocol_sha256=file_hash(root / 'PROTOCOL.json'), budget=inspected['budget'], selection=selection)


def verify(root):
    protocol = read(root / 'PROTOCOL.json')
    require(read(root / 'SELECTION.json') == protocol['selection'], 'selection_binding_changed')
    require(code_hashes() == protocol['code_sha256'], 'runtime_addition_drift')
    require(file_hash(root / 'CPU_TEST_RECEIPT.json') == protocol['cpu_receipt_sha256'], 'CPU_receipt_drift')
    inputs = root / 'inputs'
    for name, expected in protocol['input_files'].items():
        require(file_hash(inputs / name) == expected, 'copied_input_changed:' + name)
    require(diagnostic.select_first(inputs) == protocol['selection'], 'checkpoint_or_cohort_drift')
    require(adjacent.verify_inputs(inputs, RUNTIME) == protocol['inputs'], 'native_runtime_or_input_drift')
    infrastructure.verify_model_files(protocol['model_dir'], protocol['model_files'])
    for identity in protocol['identities'].values():
        adjacent.bridge.AdapterIdentity.from_document(identity)
    return protocol


def deadline(lifetime):
    require(time.time() < lifetime['deadline_unix'], 'original_lifetime_exhausted_no_restart')


def child(root, side):
    own_root(root)
    output = root / side / 'readout'
    output.mkdir(exist_ok=False)
    protocol = verify(root)
    lifetime = read(root / 'LIFETIME.json')
    deadline(lifetime)
    expected_uuid = DEVICES[side][1]
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == expected_uuid, 'exact_UUID_CVD_required')
    require(os.getppid() == lifetime['process'][1]
            and infrastructure.process_start(os.getppid()) == lifetime['process'][2], 'fresh_guardian_owner_required')
    require(Path('/proc/self').stat().st_uid == os.getuid(), 'own_process_uid_required')
    registration = root / side / 'PROCESS.json'
    while not registration.exists():
        deadline(lifetime)
        time.sleep(0.05)
    process_record = read(registration)
    require(process_record['process'] == list(native.process_identity()), 'exact_fresh_child_registration')
    observed = subprocess.check_output(['nvidia-smi', '-i', str(DEVICES[side][0]), '--query-gpu=uuid',
                                        '--format=csv,noheader'], text=True).strip()
    require(observed == expected_uuid, 'physical_UUID_drift')
    apps = subprocess.check_output(['nvidia-smi', '-i', expected_uuid, '--query-compute-apps=pid,gpu_uuid',
                                   '--format=csv,noheader'], text=True)
    require(expected_uuid not in apps, 'existing_compute_owner')
    identity = adjacent.bridge.AdapterIdentity.from_document(protocol['identities'][side])
    binding = adjacent.bridge.StageBinding(root.name, side, 1, 'sealed_readout', identity,
                                          False, True, file_hash(root / 'PROTOCOL.json'))
    write(output / 'REQUEST.json', dict(binding=asdict(binding), process=native.process_identity(),
          CVD=expected_uuid, uid=os.getuid(), parent_process=lifetime['process'], deadline_unix=lifetime['deadline_unix']))
    try:
        loaded = native.load_readout(binding, model_dir=protocol['model_dir'], device='cuda:0',
            gpu_uuid=expected_uuid, context=native.StageContext(), check=lambda label: deadline(lifetime),
            predecessor_processes=(tuple(protocol['selection']['predecessor_process']), tuple(lifetime['process'])))
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
              runtime=loaded.engine.runtime, phase='readout'))
        local_calls = 0

        def generate(messages, **metadata):
            nonlocal local_calls
            deadline(lifetime)
            require(local_calls < protocol['inputs']['budget']['worst_case_per_side'], 'per_side_call_cap')
            index = spend(root, 'LONG_ADJACENT', protocol['maximum_calls'], dict(side=side, metadata=metadata))
            local_calls += 1
            capture = dict(messages=messages, metadata=metadata, index=index, process=loaded.process)
            write(output / f'CALL_{index:04d}.json', capture)
            try:
                with (root / 'FIRST_NATIVE_CALL.json').open('x') as stream:
                    json.dump(dict(unix=time.time(), side=side, process=loaded.process, gpu_uuid=expected_uuid), stream)
            except FileExistsError:
                pass
            try:
                response = loaded.engine.generate(messages, max_new_tokens=512)
                response['generated_text_tokens'] = len(response['token_ids']) - int(response['terminal'])
                capture['response'] = response
                return response
            except BaseException as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output / f'CALL_{index:04d}.json', capture)

        inputs = root / 'inputs'
        result = adjacent.evaluate(read(inputs / 'COHORT.json'), read(inputs / 'SOURCE.json'),
            read(inputs / 'LEGACY_READOUT.json'), 1, generate, output, lambda name, value: write(output / name, value))
        loaded.verify_unchanged()
        deadline(lifetime)
        write(output / 'COMPLETE.json', dict(status='COMPLETE', side=side, input_adapter=identity.document(),
              process=loaded.process, native_calls=local_calls, finished_unix=time.time(),
              claim=diagnostic.CLAIM, **result))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), process=native.process_identity()))
        raise


def launch(root):
    own_root(root)
    protocol = verify(root)
    main = read(root / 'MAIN_PRE_GPU_RECEIPT.json')
    require(main['protocol_sha256'] == file_hash(root / 'PROTOCOL.json') and '[Builder]' in main['text']
            and 'L2-LONG-ADJACENT' in main['text'] and main['protocol_sha256'] in main['text'],
            'Main_logged_bound_Builder_receipt_required')
    started = time.time()
    lifetime = dict(started_unix=started, deadline_unix=started + 3600, process=native.process_identity(),
                    protocol_sha256=file_hash(root / 'PROTOCOL.json'), maximum_calls=protocol['maximum_calls'],
                    assigned_gpu_hours_limit=2, restart_allowed=False)
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, sort_keys=True, indent=2)
    children, logs = [], []
    status, error_text = 'FAILED', None

    def stop(signum, frame):
        raise infrastructure.StopNative('guardian_signal:' + str(signum))

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
        signal.signal(signum, stop)
    signal.alarm(3600)
    try:
        for side in diagnostic.SIDES:
            scan(root, side, 'launch')
        deadline(lifetime)
        for side in diagnostic.SIDES:
            log = (root / f'{side}_native.log').open('x')
            logs.append(log)
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=DEVICES[side][1], CUDA_DEVICE_ORDER='PCI_BUS_ID',
                               PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                               CUDA_CACHE_PATH=str(root / 'cache' / side / 'cuda'),
                               XDG_CACHE_HOME=str(root / 'cache' / side))
            process = subprocess.Popen([sys.executable, '-m', 'gpu.orch_l2_long_adjacent_run', 'child',
                '--root', str(root), '--side', side], env=environment, stdout=log, stderr=subprocess.STDOUT, cwd=RUNTIME)
            start = infrastructure.process_start(process.pid)
            children.append((side, process, start))
            immutable(root / side / 'PROCESS.json', dict(process=[lifetime['process'][0], process.pid, start],
                      uid=os.getuid(), CVD=DEVICES[side][1], command='gpu.orch_l2_long_adjacent_run child'))
        while any(process.poll() is None for side, process, start in children):
            deadline(lifetime)
            require(all(process.poll() in (None, 0) for side, process, start in children), 'native_child_failed_no_retry')
            time.sleep(1)
        require(all(process.returncode == 0 for side, process, start in children), 'native_pair_failed')
        deadline(lifetime)
        status = 'COMPLETE'
    except BaseException as error:
        error_text = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        for side, process, start in children:
            infrastructure.terminate_owned(process, start)
        for log in logs:
            log.close()
        signal.alarm(0)
        finished = time.time()
        calls = root / 'CALLS_LONG_ADJACENT.jsonl'
        write(root / 'TERMINAL.json', dict(status=status, error=error_text, started_unix=started,
              finished_unix=finished, assigned_gpu_hours=2 * (finished - started) / 3600,
              native_calls=len(calls.read_text().splitlines()) if calls.exists() else 0,
              exits={side: process.returncode for side, process, start in children}, claim=diagnostic.CLAIM))
        for side in diagnostic.SIDES:
            scan(root, side, 'release')
    return summarize(root)


def summarize(root):
    protocol = verify(root)
    terminal = read(root / 'TERMINAL.json')
    require(terminal['status'] == 'COMPLETE', 'both_native_states_must_complete')
    sides = {side: read(root / side / 'readout/COMPLETE.json') for side in diagnostic.SIDES}
    require(sides['PREVIOUS']['process'] != sides['OUTPUT']['process'], 'two_distinct_fresh_processes')
    for side, result in sides.items():
        require(result['input_adapter'] == protocol['identities'][side], 'mounted_saved_state_identity')
    episodes = {side: [read(root / side / 'readout' / f'EPISODE_{index:02d}.json')
                      for index in range(1, 17)] for side in diagnostic.SIDES}
    paired = diagnostic.paired_rows(episodes['PREVIOUS'], episodes['OUTPUT'])
    inputs = root / 'inputs'
    cohort, source = read(inputs / 'COHORT.json'), read(inputs / 'SOURCE.json')
    reference = adjacent.routing(cohort, source, 1, adjacent.shared.readout.first_port,
                                lambda name, value: write(root / 'reference' / name, value))
    held_masters = {world['master'] for world in cohort['held'][1]}
    records = [record for collection in source['collections'] if collection['world']['master'] in held_masters
               for record in collection['records']]
    events = [edge['event'] for world in cohort['held'][1] for edge in world['edges']]
    result = dict(protocol_sha256=file_hash(root / 'PROTOCOL.json'), selection=protocol['selection'],
                  terminal=terminal, sides=sides, paired=paired, reference=dict(native_calls=0, **reference),
                  source=dict(attempts=len(records), failed_attempts=sum(not record['accepted'] for record in records),
                              event_denominator=len(events), unavailable_events=[event for event in events if event not in source['store']]),
                  claim=diagnostic.CLAIM, disclosure=diagnostic.DISCLOSURE,
                  historical_counts_context_only=[11, 8, 9, 9], historical_cohorts_differ=True,
                  episode_success_delta=sides['OUTPUT']['successes'] - sides['PREVIOUS']['successes'])
    write(root / 'SUMMARY.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch', 'child', 'summarize'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--side', choices=diagnostic.SIDES)
    options = parser.parse_args()
    root = own_root(options.root)
    result = child(root, options.side) if options.phase == 'child' else globals()[options.phase](root)
    if result is not None:
        print(json.dumps(result, sort_keys=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
