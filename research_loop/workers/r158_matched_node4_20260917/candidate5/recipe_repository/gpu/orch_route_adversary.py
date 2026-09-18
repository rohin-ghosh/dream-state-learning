"""Bounded read-only native inference; all interventions frozen before mounting actors."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import orch_route_adversary as probe


source = portable.source
OLD_ROOT = Path('/tmp/astra_goal_quality_train_20260914_attempt2')
OLD_COMMIT = '7f9d4251ae1ff4c5ff9138adf267d081fffa6331'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
STATES = dict(FULL_TARGET='e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf',
    NEW_TRAJECTORY_LOSS_OFF='4f0dccf5b7cf37b872eafc3a50990e0cdfda027fb0140f0aad999f27606e4ee3',
    ORIGINAL37EC=portable.PARENT_STATE)
OWN_FILES = ('gpu/orch_route_adversary.py', 'gpu/orch_route_adversary_guard.sh',
    'organism_v6/orch_route_adversary.py', 'tests/test_orch_route_adversary.py',
    'research_notes/analysis/orch_route_adversary_20260914_protocol.md')
LEASE = '2026-09-19T00:00:00+00:00'
SERVICE_FILE = Path('/tmp/astra_goal_scale_20260914_attempt1/service_exceptions.json')
SERVICE_SHA = 'c45c8724dc88ab42bd594e1dfb7d1bb68726507d7af997fc306aafc300d49cbc'


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def process_identity(path, boot):
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(path.name), pgid=int(fields[2]), sid=int(fields[3]),
                start_ticks=int(fields[19]), uid=path.stat().st_uid, boot_id=boot), fields[0], int(fields[1])


def verify_service(path, identity, parent, services):
    binding = services.get(int(path.name))
    source.require(binding is not None and identity == binding['identity'] and parent == binding['ppid'],
                   'unreadable_process_not_bound_service')
    for name in ('comm', 'cmdline', 'cgroup'):
        source.require(source.file_hash(path / name) == binding[name + '_sha256'], 'service_identity_bytes_drift')


def scan(index, uuid):
    source.require(source.file_hash(SERVICE_FILE) == SERVICE_SHA, 'operational_service_binding_drift')
    services = {entry['identity']['pid']: entry for entry in source.read(SERVICE_FILE).values()}
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
        '--format=csv,noheader,nounits'], text=True)
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory',
        '--format=csv,noheader,nounits'], text=True)
    gpu_rows = [line.split(', ') for line in inventory.splitlines()]
    source.require(any(row[0] == str(index) and row[1] == uuid for row in gpu_rows), 'physical_uuid_index_drift')
    holders = [line for line in processes.splitlines() if uuid in line]
    cvd_rows, unreadable, service_matches = [], [], []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            before, state, parent = process_identity(proc, boot)
            if state == 'Z':
                continue
            try:
                entries = (proc / 'environ').read_bytes().split(b'\0')
            except PermissionError:
                verify_service(proc, before, parent, services)
                after, state, parent = process_identity(proc, boot)
                source.require(before == after and state != 'Z', 'service_process_changed_during_scan')
                verify_service(proc, after, parent, services)
                service_matches.append(before)
                continue
            after, state, unused_parent = process_identity(proc, boot)
            source.require(before == after, 'process_identity_changed_during_scan')
            cvd = [entry.decode(errors='replace').split('=', 1)[1] for entry in entries
                   if entry.startswith(b'CUDA_VISIBLE_DEVICES=')]
            for value in cvd:
                devices = value.split(',')
                if str(index) in devices or uuid in devices or 'all' in devices or any(
                        uuid.startswith(device) for device in devices if device.startswith('GPU-')):
                    cvd_rows.append(dict(identity=before, cvd=value))
        except (FileNotFoundError, ProcessLookupError):
            pass
        except Exception as error:
            unreadable.append(dict(pid=int(proc.name), error_type=type(error).__name__, message=str(error)))
    return dict(utc=datetime.now(timezone.utc).isoformat(), index=index, uuid=uuid,
        inventory=inventory, gpu_processes=processes, holders=holders, cvd_rows=cvd_rows,
        unresolved_same_uid_processes=unreadable, bound_service_identities=service_matches,
        service_binding_sha256=SERVICE_SHA, scope='ALL_UID_GPU_HOLDERS_AND_SAME_UID_LIVE_CVD',
        free=not holders and not cvd_rows and not unreadable)


def input_files(options):
    source.require((OLD_ROOT / 'source_commit.txt').read_text().strip() == OLD_COMMIT, 'frozen_quality_source_required')
    prepared = source.read(OLD_ROOT / 'prepare/RESULT.json')
    arguments = prepared['arguments']
    source.require(arguments['bundle_sha'] == BUNDLE_SHA, 'exact_portable_bundle_required')
    manifest = portable.read_manifest(arguments['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    verified = portable.verify_base_files(arguments['bundle'], arguments['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    archives, selected, missing = [], {}, []
    for shard, location in enumerate(arguments['shard_roots']):
        directory = Path(location) / 'expose'
        data_path, result_path = directory / 'DATA.json', directory / 'RESULT.json'
        data, receipt = source.read(data_path), source.read(result_path)
        source.require(receipt['output_files']['DATA.json'] == source.file_hash(data_path)
            and receipt['phase'] == 'expose' and receipt['status'] == 'COMPLETE'
            and receipt['loaded_adapter_state_sha256'] == portable.PARENT_STATE,
            'native_exposure_inventory_drift')
        archives.append(dict(path=str(data_path), sha256=source.file_hash(data_path),
                             result_sha256=source.file_hash(result_path)))
        for world_index, collection in enumerate(data['collections']):
            for record_index, record in enumerate(collection['records']):
                if not record['accepted']:
                    missing.append(dict(shard=shard, world_index=world_index, record_index=record_index,
                        address=record['edge']['event'], error=record['error'],
                        collection_sha256=collection['collection_sha256']))
            if (shard, world_index) in probe.SELECTION:
                runtime = scale.runtime(shard)
                source.require(collection['master'] in runtime['PROBE_MASTERS'], 'probe_only_selection_required')
                runtime['replay_collection'](collection)
                selected[shard, world_index] = collection
    source.require(len(missing) == 4 and sum(item['world_index'] >= 8 for item in missing) == 1,
                   'fixed_historical_missing_source_population_required')
    cases = [probe.build_case(selected[selection], seed, condition, goal)
             for seed, selection in zip(probe.SEEDS, probe.SELECTION)
             for condition in probe.CONDITIONS for goal in (0, 1)]
    models = {}
    for arm, state in STATES.items():
        if arm == 'ORIGINAL37EC':
            adapter = Path(arguments['bundle']) / 'adapter'
            files = manifest['adapter_files']
            receipt_sha = BUNDLE_SHA
        else:
            train = OLD_ROOT / arm / 'train'
            receipt = source.read(train / 'RESULT.json')
            source.require(receipt['status'] == 'COMPLETE' and receipt['updates'] == 2928
                and receipt['adapter_state_after'] == state, 'exact_saved_child_required')
            adapter, files, receipt_sha = train / 'adapter', receipt['adapter_files'], source.file_hash(train / 'RESULT.json')
        portable.verify_inventory(adapter, files)
        models[arm] = dict(adapter_dir=str(adapter), state=state, files=files, receipt_sha256=receipt_sha)
    tree = Path(__file__).resolve().parents[1]
    own_hashes = {name: source.file_hash(tree / name) for name in OWN_FILES}
    return dict(schema='ORCH_ROUTE_ADVERSARY_FROZEN_V1', cases=cases,
        cases_sha256=probe.hop.document_sha256(cases), old_source_commit=OLD_COMMIT,
        new_source_commit=options.commit, source_archive_sha256=source.file_hash(options.archive),
        own_hashes=own_hashes, portable_contract=portable.contract(),
        old_prepare_sha256=source.file_hash(OLD_ROOT / 'prepare/RESULT.json'), archives=archives,
        historical_missing_sources=missing, selected_worlds=[list(item) for item in probe.SELECTION],
        bundle=arguments['bundle'], bundle_sha=BUNDLE_SHA, model_dir=arguments['model_dir'],
        expected_base_sha256=manifest['expected_base_sha256'], base_verification=verified,
        models=models, max_native_calls_per_arm=48, max_total_native_calls=144,
        max_seconds_per_arm=2400, lease_conservative_utc=LEASE, claim=probe.CLAIM,
        fits=0, updates=0, parent_present=False,
        source_text_policy='EXACT_ORIGINAL_EXCEPT_DECLARED_SYNTHETIC_COUNTERFACTUAL_INFERENCE_ONLY')


def prepare(options):
    root = Path(options.root)
    source.require(not (root / 'PREPARE.json').exists(), 'new_preparation_required')
    document = input_files(options)
    controls = [probe.first_available_reference(case) for case in document['cases']]
    tokenizer = source.native.load_local_tokenizer(document['model_dir'])
    lengths = []
    for result in controls:
        for capture in result['native']:
            tokens = tokenizer.apply_chat_template(capture['messages'], tokenize=True,
                add_generation_prompt=True, return_dict=False)
            source.require(0 < len(tokens) <= 2048, 'untruncated_native_prompt_required')
            lengths.append(len(tokens))
    document['tokenization'] = dict(prompts=len(lengths), max_tokens=max(lengths), context_limit=2048,
                                    max_new_tokens=160, model_calls=0)
    write(root / 'REFERENCE.json', dict(policy='FIRST_CURRENT_AVAILABLE_DISPLAYED_PORT',
        native_calls=0, cases=controls, summary=probe.summarize(controls)))
    write(root / 'PREPARE.json', document)
    print(json.dumps(dict(status='PREPARED_NO_MODEL', cases=len(document['cases']),
        cases_sha256=document['cases_sha256'], prepare_sha256=source.file_hash(root / 'PREPARE.json'),
        tokenization=document['tokenization'])), flush=True)


def execute(options):
    root, started = Path(options.root), time.time()
    prepared_path = root / 'PREPARE.json'
    source.require(source.file_hash(prepared_path) == options.prepare_sha, 'frozen_prepare_hash_required')
    prepared = source.read(prepared_path)
    source.require(prepared['new_source_commit'] == options.commit, 'exact_new_source_commit_required')
    source.require(prepared['source_archive_sha256'] == source.file_hash(options.archive), 'archive_drift')
    tree = Path(__file__).resolve().parents[1]
    source.require(all(source.file_hash(tree / name) == digest for name, digest in prepared['own_hashes'].items()),
                   'probe_source_drift')
    source.require(prepared['portable_contract'] == portable.contract(), 'portable_helper_drift')
    source.require(probe.hop.document_sha256(prepared['cases']) == prepared['cases_sha256'], 'case_drift')
    source.require(os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'explicit_uuid_cvd_required')
    source.require(started + 2400 < datetime.fromisoformat(LEASE).timestamp() - 21600, 'lease_six_hour_guard')
    arm = options.arm
    output = root / arm
    output.mkdir(exist_ok=False)
    write(output / 'START.json', dict(pid=os.getpid(), parent_pid=os.getppid(), gpu_uuid=options.gpu_uuid,
        cvd=os.environ['CUDA_VISIBLE_DEVICES'], started_unix=started, hard_deadline_unix=started+2400,
        prepare_sha256=options.prepare_sha, source_commit=options.commit))
    model = prepared['models'][arm]
    calls, results = [], []
    deadline = started + 2340

    def check(label):
        source.require(time.time() < deadline, 'bounded_native_deadline:' + label)

    try:
        portable.verify_inventory(model['adapter_dir'], model['files'])
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        arguments = portable.read_bundle(prepared['bundle'], expected_manifest_sha256=BUNDLE_SHA,
            model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=options.gpu_uuid)
        arguments.adapter_dir = model['adapter_dir']
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        source.require(parameters and _state_hash(parameters) == model['state'], 'exact_mounted_adapter_state')
        source.require(not any(parameter.requires_grad for parameter in engine.model.parameters()), 'readonly_actor_required')
        write(output / 'MOUNTED.json', dict(state=model['state'], runtime=engine.runtime,
            gpu_uuid=options.gpu_uuid, pid=os.getpid(), frozen_base=True, all_requires_grad_false=True))
        for index, case in enumerate(prepared['cases']):
            def generate(messages):
                check('call')
                source.require(len(calls) < 48, 'finite_native_call_cap')
                capture = dict(index=len(calls), case_index=index, messages=deepcopy(messages), response=None, error=None)
                calls.append(capture)
                try:
                    capture['response'] = deepcopy(engine.generate(messages, max_new_tokens=160))
                    return deepcopy(capture['response'])
                except Exception as error:
                    capture['error'] = dict(type=type(error).__name__, message=str(error))
                    raise
                finally:
                    write(output / f"CALL_{capture['index']:03d}.json", capture)

            result = probe.run_case(case, generate)
            results.append(result)
            write(output / f'CASE_{index:03d}.json', result)
        source.require(sum(item['native_calls'] for item in results) == len(calls), 'native_call_join')
        engine.verify_base()
        final_state = _state_hash(parameters)
        source.require(final_state == model['state'], 'readonly_adapter_drift')
        portable.verify_inventory(model['adapter_dir'], model['files'])
        write(output / 'RESULT.json', dict(status='COMPLETE_NOT_PROMOTED', arm=arm,
            cases_sha256=prepared['cases_sha256'], prepare_sha256=options.prepare_sha,
            source_commit=options.commit, native_calls=len(calls), fits=0, updates=0,
            scripted_read_turns=96, summary=probe.summarize(results), adapter_state_before=model['state'],
            adapter_state_after=final_state, frozen_base_unchanged=True, claim=probe.CLAIM,
            seconds=time.time()-started, result_files={path.name: source.file_hash(path)
                for path in sorted(output.glob('CASE_*.json'))}, raw_call_files={path.name: source.file_hash(path)
                for path in sorted(output.glob('CALL_*.json'))}))
    except Exception as error:
        write(output / 'FAILED.json', dict(status='FAILED_NOT_RETRIED', error=type(error).__name__,
            message=str(error), native_calls=len(calls), completed_cases=len(results), seconds=time.time()-started))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('prepare', 'run', 'scan'), required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--commit')
    parser.add_argument('--archive')
    parser.add_argument('--arm', choices=tuple(STATES))
    parser.add_argument('--gpu-index', type=int)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--prepare-sha')
    options = parser.parse_args()
    if options.phase == 'scan':
        result = scan(options.gpu_index, options.gpu_uuid)
        print(json.dumps(result, sort_keys=True))
        source.require(result['free'], 'assigned_gpu_not_free')
    elif options.phase == 'prepare':
        prepare(options)
    else:
        execute(options)


if __name__ == '__main__':
    main()
