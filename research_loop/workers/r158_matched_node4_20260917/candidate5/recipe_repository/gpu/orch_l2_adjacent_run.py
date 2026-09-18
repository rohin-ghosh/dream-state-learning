"""One-shot two-process readout using SHORT's immutable V2 native seam."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_guided_native as native
from gpu.orch_l2_shared_run import spend, write
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_adjacent as adjacent
from organism_v6 import orch_l2_shared as shared


DEVICES = {'PREVIOUS': (0, 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0'),
           'OUTPUT': (1, 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4')}
OWN_FILES = ('gpu/orch_l2_adjacent_run.py', 'organism_v6/orch_l2_adjacent.py')
require = bridge.require


class StopNative(BaseException):
    pass


def immutable(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(adjacent.read(path) == document, 'immutable_adjacent_binding_changed')
    else:
        with path.open('x') as stream:
            json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')


def own_root(root):
    root = Path(root).resolve()
    require(root.parent == Path('/localhome/local-rohing') and root.name.startswith('orch_l2_adjacent_'),
            'unique_own_node2_root_required')
    return root


def device_free(side):
    index, expected = DEVICES[side]
    observed = subprocess.check_output(['nvidia-smi', '-i', str(index), '--query-gpu=uuid',
                                        '--format=csv,noheader'], text=True).strip()
    require(observed == expected, 'assigned_physical_UUID_drift')
    rows = subprocess.check_output(['nvidia-smi', '-i', str(index), '--query-compute-apps=gpu_uuid,pid',
                                    '--format=csv,noheader,nounits'], text=True).splitlines()
    require(not any(row.split(',')[0].strip() == expected for row in rows), 'assigned_GPU_has_existing_owner')
    return dict(index=index, uuid=expected)


def process_start(pid):
    return int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19])


def terminate_owned(process, start):
    if process.poll() is None:
        require(process_start(process.pid) == start, 'PID_reuse_do_not_signal')
        require(Path(f'/proc/{process.pid}').stat().st_uid == os.getuid(), 'foreign_PID_do_not_signal')
        process.send_signal(signal.SIGKILL)
        process.wait()


def select(root, shared_root):
    selection = adjacent.select_first(shared_root)
    if selection['status'] == 'SELECTED':
        immutable(root / 'SELECTION.json', selection)
    write(root / 'STATUS.json', selection)
    return selection


def verify_model_files(model_dir, reference):
    require(set(reference) == {'config.json', 'generation_config.json', 'tokenizer.json',
                              'tokenizer_config.json', 'special_tokens_map.json'}, 'exact_model_metadata_inventory')
    observed = {name: bridge.file_sha256(Path(model_dir) / name) if (Path(model_dir) / name).is_file() else None
                for name in reference}
    require(observed == reference, 'original_SHORT_tokenizer_or_config_drift')
    return observed


def prepare(root, shared_root, model_dir):
    runtime = Path(__file__).resolve().parents[1]
    selection = adjacent.read(root / 'SELECTION.json')
    require(adjacent.select_first(shared_root) == selection, 'bound_checkpoint_selection_drift')
    inspected = adjacent.verify_inputs(shared_root, runtime)
    require(selection['cohort_sha256'] == inspected['cohort_sha256'], 'selected_cohort_drift')
    cpu = adjacent.read(root / 'CPU_TEST_RECEIPT.json')
    code = {relative: bridge.file_sha256(runtime / relative) for relative in OWN_FILES}
    require(cpu['passed'] is True and cpu['code_sha256'] == code, 'own_CPU_receipt_required')
    identities = {}
    for side in adjacent.SIDES:
        identity = dict(selection['previous' if side == 'PREVIOUS' else 'output'], path=str(root / side / 'adapter'))
        identities[side] = bridge.AdapterIdentity.from_document(identity).document()
    require(Path(model_dir).is_absolute() and Path(model_dir).is_dir(), 'existing_local_native_base_required')
    model_files = verify_model_files(model_dir, adjacent.read(root / 'MODEL_FILES_A100.json'))
    document = dict(selection=selection, inputs=inspected, shared_root=str(shared_root), model_dir=str(model_dir),
                    identities=identities, code_sha256=code, model_files=model_files,
                    cpu_receipt_sha256=bridge.file_sha256(root / 'CPU_TEST_RECEIPT.json'),
                    created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), claim=adjacent.CLAIM)
    immutable(root / 'PREPARE_ADJACENT.json', document)
    return document


def child(root, side):
    root = own_root(root)
    output = root / side / 'readout'
    output.mkdir(parents=True, exist_ok=False)
    prepared = adjacent.read(root / 'PREPARE_ADJACENT.json')
    lifetime = adjacent.read(root / 'LIFETIME.json')
    selection = prepared['selection']
    shared_root = Path(prepared['shared_root'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == DEVICES[side][1], 'exact_single_UUID_CVD_required')
    device_free(side)
    adjacent.verify_inputs(shared_root, Path(__file__).resolve().parents[1])
    for relative, expected in prepared['code_sha256'].items():
        require(bridge.file_sha256(Path(__file__).resolve().parents[1] / relative) == expected, 'own_code_drift')
    verify_model_files(prepared['model_dir'], prepared['model_files'])
    identity = bridge.AdapterIdentity.from_document(prepared['identities'][side])
    binding = bridge.StageBinding(root.name, side, selection['cycle'], 'sealed_readout', identity,
                                  False, True, adjacent.digest(prepared))

    def check(label):
        if time.time() >= lifetime['deadline_unix']:
            raise StopNative('lifetime_deadline:' + label)

    write(output / 'REQUEST.json', dict(binding=asdict(binding), process=native.process_identity(),
          CVD=os.environ['CUDA_VISIBLE_DEVICES'], deadline_unix=lifetime['deadline_unix']))
    try:
        check('before_load')
        loaded = native.load_readout(binding, model_dir=prepared['model_dir'], device='cuda:0',
            gpu_uuid=DEVICES[side][1], context=native.StageContext(), check=check,
            predecessor_processes=(tuple(selection['predecessor_process']), tuple(lifetime['process'])))
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
              runtime=loaded.engine.runtime, phase='readout'))

        def generate(messages, **metadata):
            check('dispatch')
            index = spend(root, 'ADJACENT', adjacent.CALL_CAP, dict(side=side, metadata=metadata))
            capture = dict(messages=messages, metadata=metadata, index=index, process=loaded.process)
            write(output / f'CALL_{index:04d}.json', capture)
            first = root / 'FIRST_NATIVE_CALL.json'
            try:
                with first.open('x') as stream:
                    json.dump(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), side=side,
                                   process=loaded.process, gpu_uuid=DEVICES[side][1]), stream)
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

        result = adjacent.evaluate(adjacent.read(shared_root / 'COHORT.json'), adjacent.read(shared_root / 'SOURCE.json'),
            adjacent.read(shared_root / 'LEGACY_READOUT.json'), selection['cycle'], generate, output,
            lambda name, value: write(output / name, value))
        loaded.verify_unchanged()
        write(output / 'BINDING.json', asdict(binding))
        write(output / 'COMPLETE.json', dict(status='COMPLETE', side=side, input_adapter=identity.document(),
              process=loaded.process, finished_unix=time.time(), claim=adjacent.CLAIM, **result))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), process=native.process_identity()))
        raise


def launch(root):
    root = own_root(root)
    prepared = adjacent.read(root / 'PREPARE_ADJACENT.json')
    require(adjacent.read(root / 'SELECTION.json') == prepared['selection'], 'selection_changed_after_preparation')
    devices = {side: device_free(side) for side in adjacent.SIDES}
    started = time.time()
    lifetime = dict(started_unix=started, deadline_unix=started + adjacent.NATIVE_SECONDS,
                    assigned_gpu_hours_limit=2, learner_calls_limit=adjacent.CALL_CAP,
                    devices=devices, process=native.process_identity())
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, sort_keys=True, indent=2)
    children, logs = [], []
    status = 'FAILED'
    try:
        for side in adjacent.SIDES:
            log = (root / f'{side}_native.log').open('x')
            logs.append(log)
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=DEVICES[side][1], PYTHONDONTWRITEBYTECODE='1',
                               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                               CUDA_CACHE_PATH=str(root / 'cache' / side / 'cuda'),
                               XDG_CACHE_HOME=str(root / 'cache' / side))
            process = subprocess.Popen([sys.executable, '-m', 'gpu.orch_l2_adjacent_run', 'child',
                '--root', str(root), '--side', side], env=environment, stdout=log, stderr=subprocess.STDOUT,
                cwd=Path(__file__).resolve().parents[1])
            children.append((side, process, process_start(process.pid)))
        first_reported = False
        while any(process.poll() is None for unused, process, start in children):
            if not first_reported and (root / 'FIRST_NATIVE_CALL.json').exists():
                print(json.dumps(dict(event='FIRST_NATIVE_CALL', **adjacent.read(root / 'FIRST_NATIVE_CALL.json'))), flush=True)
                first_reported = True
            if time.time() >= lifetime['deadline_unix']:
                raise StopNative('lifetime_native_deadline')
            if any(process.poll() not in (None, 0) for unused, process, start in children):
                raise StopNative('checkpoint_process_failed_no_retry')
            time.sleep(min(1, max(0, lifetime['deadline_unix'] - time.time())))
        require(all(process.returncode == 0 for unused, process, start in children), 'native_pair_failed')
        status = 'COMPLETE'
    finally:
        for unused, process, start in children:
            terminate_owned(process, start)
        for log in logs:
            log.close()
        calls = root / 'CALLS_ADJACENT.jsonl'
        terminal = dict(status=status, finished_unix=time.time(), started_unix=started,
                        native_calls=len(calls.read_text().splitlines()) if calls.exists() else 0,
                        exits={side: process.returncode for side, process, unused in children}, claim=adjacent.CLAIM)
        write(root / 'TERMINAL.json', terminal)
        print(json.dumps(dict(event='TERMINAL', **terminal)), flush=True)


def summarize(root, original=None):
    selection = adjacent.read(root / 'SELECTION.json')
    prepared = adjacent.read(root / 'PREPARE_ADJACENT.json')
    shared_root = Path(prepared['shared_root'])
    cohort, source = adjacent.read(shared_root / 'COHORT.json'), adjacent.read(shared_root / 'SOURCE.json')
    reference_dir = root / 'reference'
    reference_dir.mkdir(exist_ok=True)
    reference = adjacent.routing(cohort, source, selection['cycle'], shared.readout.first_port,
                                 lambda name, value: write(reference_dir / name, value))
    held_masters = {world['master'] for world in cohort['held'][selection['cycle']]}
    source_records = [record for collection in source['collections'] if collection['world']['master'] in held_masters
                      for record in collection['records']]
    event_ids = [edge['event'] for world in cohort['held'][selection['cycle']] for edge in world['edges']]
    result = dict(selection=selection, claim=adjacent.CLAIM, reference=dict(native_calls=0, **reference),
                  source=dict(attempts=len(source_records), failed_attempts=sum(not record['accepted'] for record in source_records),
                              event_denominator=len(event_ids),
                              unavailable_events=[event for event in event_ids if event not in source['store']]),
                  original=adjacent.original_counts(original, selection) if original else
                  dict(status='PENDING_EXACT_ORIGINAL_READOUT_POINTER', contextual_only=True), sides={}, disagreements=[])
    for side in adjacent.SIDES:
        result['sides'][side] = adjacent.read(root / side / 'readout' / 'COMPLETE.json')
    require(result['sides']['PREVIOUS']['process'] != result['sides']['OUTPUT']['process'], 'distinct_native_processes')
    for index in range(1, 17):
        before = adjacent.read(root / 'PREVIOUS/readout' / f'EPISODE_{index:02d}.json')
        after = adjacent.read(root / 'OUTPUT/readout' / f'EPISODE_{index:02d}.json')
        require(before['task'] == after['task'], 'paired_task_drift')
        result['disagreements'].append(dict(episode=index, task=before['task'], previous=before['correct'],
            output=after['correct'], previous_reads=before['reads'], output_reads=after['reads'],
            previous_routes=before['routes'], output_routes=after['routes']))
    write(root / 'SUMMARY.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('inspect', 'select', 'prepare', 'launch', 'child', 'summarize'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--shared-root', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--side', choices=adjacent.SIDES)
    parser.add_argument('--original-readout', type=Path)
    options = parser.parse_args()
    root = options.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if options.phase == 'inspect':
        result = adjacent.verify_inputs(options.shared_root, Path(__file__).resolve().parents[1])
        write(root / 'CPU_INPUT_RECEIPT.json', result)
    elif options.phase == 'select':
        result = select(root, options.shared_root)
    elif options.phase == 'prepare':
        result = prepare(own_root(root), options.shared_root, options.model_dir)
    elif options.phase == 'launch':
        launch(root)
        return
    elif options.phase == 'child':
        child(root, options.side)
        return
    else:
        result = summarize(root, options.original_readout)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
