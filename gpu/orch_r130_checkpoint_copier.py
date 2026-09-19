"""Bounded read-only source checkpoint copying into the existing node2 intake.

Only three registered original roots and existing SSH wrappers are admitted.
Source programs use standard-library reads of COMMIT.json and its adapter file
inventory only. They never inspect TRAIN, open optimizer/RNG payloads, write on
a source node, import torch, request a checkpoint, or signal a process.
"""

from datetime import datetime, timezone
import hashlib
import inspect
import io
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

from gpu import orch_r130_checkpoint_scheduler as scheduler


SCHEMA = 'R130_BOUNDED_ORIGINAL_CHECKPOINT_COPIER_V1'
ROOT = '/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1'
WRAPPERS = {'legacy': 'ovx3_ssh.sh', 'pilot': 'ovx3_ssh.sh', 'kernel': 'a40r_ssh.sh'}
require = scheduler.require
sha = scheduler.sha
read = scheduler.read
write = scheduler.write


def source_regular(path, root):
    path, root = Path(path), Path(root)
    if not path.is_absolute() or '..' in path.parts or any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('source_regular_absolute_path')
    if not path.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise ValueError('source_path_outside_registered_root')
    return path


def source_commit(path, params):
    path = source_regular(path, params['checkpoint_root'])
    raw = path.read_bytes()
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('bounded_native_commit_bytes')
    document = json.loads(raw)
    if document['schema'] != params['native_schema'] or document['base_sha256'] != params['base_sha256']:
        raise ValueError('native_base_contract')
    state = document['adapter_state_sha256']
    if not isinstance(state, str) or len(state) != 64 or any(character not in '0123456789abcdef' for character in state):
        raise ValueError('native_adapter_state_hash')
    created = document['created_unix']
    if type(created) not in (int, float) or not math.isfinite(created) or not 0 < created <= time.time():
        raise ValueError('native_created_timestamp')
    if type(document['optimizer_steps']) is not int or document['optimizer_steps'] < 0:
        raise ValueError('native_optimizer_step_metadata')
    files = document['adapter_files']
    if not isinstance(files, dict) or not {'adapter_config.json', 'adapter_model.safetensors'} <= set(files):
        raise ValueError('native_adapter_inventory')
    for name, checksum in files.items():
        if Path(name).name != name or name in ('.', '..') or not isinstance(checksum, str) or len(checksum) != 64:
            raise ValueError('native_inventory_names_and_hashes')
    adapter = source_regular(path.parent / 'adapter', params['checkpoint_root'])
    actual = {item.name for item in adapter.iterdir()}
    if actual != set(files):
        raise ValueError('source_adapter_file_inventory')
    for name in files:
        item = source_regular(adapter / name, params['checkpoint_root'])
        if not item.is_file():
            raise ValueError('source_adapter_regular_file')
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if document['checkpoint_sha256']['adapter'] != digest:
        raise ValueError('native_inventory_digest')
    return raw, document


def source_baseline(params):
    baseline = source_regular(params['initial_commit_path'], params['checkpoint_root'])
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != params['initial_commit_sha256']:
        raise ValueError('registered_initial_COMMIT_changed')


def discover(params):
    source_baseline(params)
    candidates = []
    ignored = 0
    paths = sorted(Path(params['checkpoint_root']).glob('*/COMMIT.json'))
    if len(paths) > 4096:
        raise ValueError('bounded_native_checkpoint_inventory')
    for path in paths:
        try:
            raw, document = source_commit(path, params)
            candidates.append(dict(lineage_id=params['lineage_id'], commit_path=str(path),
                commit_sha256=hashlib.sha256(raw).hexdigest(), created_unix=document['created_unix'],
                adapter_state_sha256=document['adapter_state_sha256'], adapter_files=document['adapter_files']))
        except (ValueError, KeyError, FileNotFoundError, NotADirectoryError, OSError):
            ignored += 1
    if not candidates:
        raise ValueError('no_complete_native_checkpoint')
    chosen = max(candidates, key=lambda item: (item['created_unix'], item['commit_sha256']))
    return dict(status='COMMITTED_CHECKPOINT_SELECTED', selected=chosen,
        inspected_commits=len(paths), incomplete_or_invalid_commits=ignored, observed_unix=time.time())


def pack(params, selected):
    source_baseline(params)
    raw, document = source_commit(selected['commit_path'], params)
    if hashlib.sha256(raw).hexdigest() != selected['commit_sha256']:
        raise ValueError('selected_COMMIT_bytes_changed')
    if document['adapter_state_sha256'] != selected['adapter_state_sha256'] or document['adapter_files'] != selected['adapter_files']:
        raise ValueError('selected_adapter_provenance_changed')
    contents = {'COMMIT.json': raw}
    total = len(raw)
    directory = Path(selected['commit_path']).parent
    for name, checksum in sorted(document['adapter_files'].items()):
        path = source_regular(directory / 'adapter' / name, params['checkpoint_root'])
        if total + path.stat().st_size > 512 * 1024 * 1024:
            raise ValueError('bounded_adapter_copy_bytes')
        payload = path.read_bytes()
        total += len(payload)
        if hashlib.sha256(payload).hexdigest() != checksum:
            raise ValueError('source_adapter_file_hash_mismatch')
        contents['adapter/' + name] = payload
    after, after_document = source_commit(selected['commit_path'], params)
    if after != raw or after_document != document:
        raise ValueError('source_COMMIT_changed_during_copy')
    for name, checksum in document['adapter_files'].items():
        if hashlib.sha256((directory / 'adapter' / name).read_bytes()).hexdigest() != checksum:
            raise ValueError('source_adapter_changed_during_copy')
    source_baseline(params)
    receipt = dict(schema='R130_SOURCE_READONLY_COPY_RECEIPT_V1', lineage_id=params['lineage_id'],
        checkpoint_root=params['checkpoint_root'], original_commit_path=selected['commit_path'],
        original_commit_sha256=selected['commit_sha256'], initial_commit_sha256=params['initial_commit_sha256'],
        adapter_state_sha256=document['adapter_state_sha256'], adapter_files=document['adapter_files'],
        before_after_verified=True, source_writes=False, optimizer_or_TRAIN_opened=False)
    contents['SOURCE_COPY_RECEIPT.json'] = (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as stream:
        for name, payload in sorted(contents.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(payload), 0o600, 0
            stream.addfile(info, io.BytesIO(payload))
    return archive.getvalue()


def source_command(params, selected=None):
    definitions = '\n\n'.join(inspect.getsource(function)
        for function in (source_regular, source_commit, source_baseline, discover, pack))
    program = 'from pathlib import Path\nimport hashlib,io,json,math,sys,tarfile,time\n' + definitions
    program += '\nparams=json.loads(sys.argv[1])\n'
    if selected is None:
        program += 'print(json.dumps(discover(params)))\n'
        arguments = [json.dumps(params)]
    else:
        program += 'sys.stdout.buffer.write(pack(params,json.loads(sys.argv[2])))\n'
        arguments = [json.dumps(params), json.dumps(selected)]
    return 'PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= python3 -B -c ' + shlex.quote(program) + ' ' + ' '.join(shlex.quote(argument) for argument in arguments)


def destination_command(config, action, payload):
    program = '''from pathlib import Path
import json,os,sys,time
from gpu import orch_r130_checkpoint_scheduler as scheduler
helper=scheduler.sidecar
params=json.loads(sys.argv[1]); action=sys.argv[2]
root=Path(params['root']); config_path=root/'SCHEDULER_CONFIG_V1.json'
helper.require(helper.sha(config_path)==params['scheduler_config_sha256'],'scheduler_config_pin')
config=helper.read(config_path)
helper.require(config['registry_sha256']==scheduler.REGISTRY_SHA256 and helper.sha(config['registry_path'])==scheduler.REGISTRY_SHA256,'frozen_registry')
helper.require(helper.sha(config['lineages_path'])==config['lineages_sha256'],'pinned_enrollment')
lineages=scheduler.enrolled_lineages(helper.read(config['lineages_path']))
helper.require(params['lineage_id'] in ('legacy','pilot','kernel') and params['lineage_id'] in lineages,'registered_original_only')
helper.require(lineages[params['lineage_id']]['initial_commit_sha256']==params['initial_commit_sha256'],'source_root_baseline_identity')
helper.require(time.time()<config['hard_end_unix']-180,'remaining_scheduler_dispatch_wall')
output=Path(config['output_root'])
helper.require(not (output/'FAILED.json').exists() and not (output/'COMPLETE.json').exists(),'scheduler_not_terminal')
helper.require(not helper.gone(helper.read(output/'STARTED.json')['identity']),'scheduler_must_be_live')
key=scheduler.key_for(params['lineage_id'],params['commit_sha256'])
if action=='known':
    known=False
    for path in (Path(config['inbox_root'])/'ready').glob('*.json'):
        item=helper.read(path)
        if item.get('lineage_id')==params['lineage_id'] and item.get('commit_sha256')==params['commit_sha256']:
            scheduler.candidate(config,lineages,path); known=True; break
    print(json.dumps(dict(status='ALREADY_STAGED' if known else 'NEEDS_COPY',key=key)))
elif action=='stage':
    archive=root/'incoming'/('future_'+params['lineage_id']+'_'+params['commit_sha256']+'.tar')
    raw=sys.stdin.buffer.read(513*1024*1024)
    helper.require(len(raw)<=512*1024*1024 and helper.hashlib.sha256(raw).hexdigest()==params['archive_sha256'],'copied_archive_hash')
    if archive.exists(): helper.require(helper.sha(archive)==params['archive_sha256'],'existing_archive_exact_bytes')
    else: helper.write(archive,raw)
    destination=Path(config['inbox_root'])/'copies'/(params['lineage_id']+'_'+params['commit_sha256'])
    if not destination.exists():
        staging=destination.parent/('.staging_'+key+'_'+str(os.getpid()))
        helper.extract_regular_archive(archive,staging,params['archive_sha256'])
        helper.checkpoint_manifest(staging,params['commit_sha256'])
        proof=helper.read(staging/'SOURCE_COPY_RECEIPT.json')
        helper.require(proof['original_commit_sha256']==params['commit_sha256'] and proof['initial_commit_sha256']==params['initial_commit_sha256'] and proof['lineage_id']==params['lineage_id'] and proof['before_after_verified'] is True,'source_copy_receipt_binding')
        checkpoint=helper.runner.verify_checkpoint(helper.read(staging/'manifest.json'),staging)
        helper.require(checkpoint['adapter_state_sha256']==params['adapter_state_sha256'],'native_adapter_state_declaration_preserved')
        helper.require(set(path.name for path in staging.iterdir())=={'COMMIT.json','adapter','manifest.json','SOURCE_COPY_RECEIPT.json'},'adapter_only_copy_no_optimizer')
        os.rename(staging,destination)
    manifest=destination/'manifest.json'
    checkpoint=helper.runner.verify_checkpoint(helper.read(manifest),destination)
    helper.require(checkpoint['commit_sha256']==params['commit_sha256'] and checkpoint['adapter_state_sha256']==params['adapter_state_sha256'],'final_copy_identity')
    ready=dict(schema=scheduler.READY_SCHEMA,lineage_id=params['lineage_id'],manifest_path=str(manifest),manifest_sha256=helper.sha(manifest),commit_sha256=params['commit_sha256'])
    raw=(json.dumps(ready,sort_keys=True,indent=2)+'\\n').encode()
    checksum=helper.hashlib.sha256(raw).hexdigest(); path=Path(config['inbox_root'])/'ready'/(checksum+'.json')
    if not path.exists():
        temporary=Path(config['inbox_root'])/('.ready_'+key+'_'+str(os.getpid()))
        helper.write(temporary,raw); os.link(temporary,path); temporary.unlink()
    scheduler.candidate(config,lineages,path)
    print(json.dumps(dict(status='COPIED_AND_READY_VERIFIED',lineage_id=params['lineage_id'],commit_sha256=params['commit_sha256'],archive_sha256=params['archive_sha256'],manifest_sha256=helper.sha(manifest),ready_sha256=helper.sha(path),copy_receipt_sha256=helper.sha(destination/'SOURCE_COPY_RECEIPT.json'),key=key)))
else: raise ValueError('only_known_or_stage')
'''
    params = dict(payload, root=ROOT, scheduler_config_sha256=config['scheduler_config_sha256'])
    return ('CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(config['destination_source_root'])
        + ' /localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(program)
        + ' ' + shlex.quote(json.dumps(params)) + ' ' + shlex.quote(action))


def validate(config_path):
    require(os.environ.get('R130_COPIER_ADMISSION_SHA256') == sha(config_path), 'copier_admission_binding')
    config = read(config_path)
    repository = Path(__file__).resolve().parents[1]
    require(config['schema'] == SCHEMA and config['copier_sha256'] == sha(__file__), 'copier_source_binding')
    require(config['scheduler_config_sha256'] == 'a22dfa29a16ef419de3cb2e2ad2740b673700c4669c9ecbfc76de1238dea0805'
        and config['destination_source_root'] == ROOT + '/source6_scheduler', 'existing_scheduler_only')
    require(config['destination_wrapper'] == str(repository / 'gpu/ovx_ssh.sh')
        and sha(config['destination_wrapper']) == config['destination_wrapper_sha256'], 'only_existing_node2_wrapper')
    require(time.time() < config['hard_end_unix'] <= config['created_unix'] + 7200
        and config['hard_end_unix'] <= config['scheduler_hard_end_unix'] - 180,
        'bounded_copy_wall_before_last_dispatch')
    require(config['copy_lead_seconds'] == 180 and config['dispatch_seconds'] == 1800 and config['max_cycles'] == 4,
        'bounded_copy_cadence')
    for name in ('builder_entry', 'cpu_gate'):
        require(sha(config[name + '_path']) == config[name + '_sha256'], name + '_binding')
    gate = read(config['cpu_gate_path'])
    require(gate['status'] == 'PASS' and gate['test_exit_code'] == 0 and gate['copier_sha256'] == sha(__file__)
        and sha(gate['test_log_path']) == gate['test_log_sha256'], 'copy_CPU_gate')
    require(Path(config['builder_entry_path']).read_text().startswith('## [Builder] 2026-09-16'), 'copy_builder_gate')
    require([item['lineage_id'] for item in config['sources']] == ['legacy', 'pilot', 'kernel'], 'only_three_original_roots')
    for source in config['sources']:
        require(source['wrapper_path'] == str(repository / 'gpu' / WRAPPERS[source['lineage_id']])
            and sha(source['wrapper_path']) == source['wrapper_sha256'], 'only_bound_source_wrapper')
        require(sha(source['prior_selection_path']) == source['prior_selection_sha256'], 'historical_source_binding')
        original = next(item for item in read(source['prior_selection_path'])['checkpoints']
            if item['label'] == source['lineage_id'] + '_initial')
        require(source['initial_commit_path'] == original['path']
            and source['checkpoint_root'] == str(Path(original['path']).parent.parent)
            and source['initial_commit_sha256'] == original['commit_sha256'], 'same_registered_original_root')
        require(source['native_schema'] == scheduler.sidecar.runner.NATIVE_SCHEMA
            and source['base_sha256'] == scheduler.sidecar.runner.BASE_SHA256, 'fixed_source_native_contract')
    output = Path(config['output_root'])
    require(output.parent == Path('/tmp/r130-deploy-20260916') and output.name.startswith('bounded_copy_')
        and not output.is_symlink(), 'private_local_copy_output')
    return config


def copy_one(config, source, directory):
    params = {key: source[key] for key in ('lineage_id', 'checkpoint_root', 'initial_commit_path',
        'initial_commit_sha256', 'native_schema', 'base_sha256')}
    discovered = subprocess.run(['bash', source['wrapper_path'], source_command(params)],
        capture_output=True, check=True, timeout=60)
    selection = scheduler.sidecar.runner.parse_json(discovered.stdout)
    selected = selection['selected']
    write(directory / (source['lineage_id'] + '.SELECTION.private.json'), selection)
    payload = dict(lineage_id=source['lineage_id'], initial_commit_sha256=source['initial_commit_sha256'],
        commit_sha256=selected['commit_sha256'], adapter_state_sha256=selected['adapter_state_sha256'])
    result = subprocess.run(['bash', config['destination_wrapper'], destination_command(config, 'known', payload)],
        capture_output=True, check=True, timeout=60)
    known = scheduler.sidecar.runner.parse_json(result.stdout)
    if known['status'] == 'ALREADY_STAGED':
        return dict(status='ALREADY_STAGED', lineage_id=source['lineage_id'], commit_sha256=selected['commit_sha256'])
    require(known['status'] == 'NEEDS_COPY', 'copy_status_protocol')
    archive = directory / (source['lineage_id'] + '.tar')
    with archive.open('xb') as stream:
        subprocess.run(['bash', source['wrapper_path'], source_command(params, selected)],
            stdout=stream, stderr=subprocess.PIPE, check=True, timeout=120)
    payload['archive_sha256'] = sha(archive)
    with archive.open('rb') as stream:
        result = subprocess.run(['bash', config['destination_wrapper'], destination_command(config, 'stage', payload)],
            stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=120)
    receipt = scheduler.sidecar.runner.parse_json(result.stdout)
    require(receipt['status'] == 'COPIED_AND_READY_VERIFIED' and receipt['commit_sha256'] == selected['commit_sha256'],
        'verified_stage_receipt')
    return receipt


def next_copy(now, scheduler_end):
    dispatch = (math.floor((now + 180) / 1800) + 1) * 1800
    return dispatch - 180 if dispatch + 180 < scheduler_end else None


def run(config_path):
    config = validate(config_path)
    root = Path(config['output_root'])
    root.mkdir(mode=0o700, exist_ok=False)
    write(root / 'STARTED.json', dict(status='BOUNDED_COPY_CADENCE_RUNNING', config_sha256=sha(config_path),
        hard_end_unix=config['hard_end_unix'], observed_unix=time.time()))
    for cycle in range(config['max_cycles']):
        config = validate(config_path)
        directory = root / f'cycle_{cycle:02d}'
        directory.mkdir(mode=0o700)
        statuses = []
        for source in config['sources']:
            try:
                validate(config_path)
                require(time.time() + 300 < config['hard_end_unix'], 'remaining_bounded_copy_wall')
                status = copy_one(config, source, directory)
            except Exception as error:
                status = dict(status='COPY_FAILED_NO_READY_ASSUMED', lineage_id=source['lineage_id'], error_type=type(error).__name__)
            write(directory / (source['lineage_id'] + '.STATUS.json'), status)
            statuses.append(status)
        following = next_copy(time.time(), config['scheduler_hard_end_unix'])
        write(directory / 'COMPLETE.json', dict(status='COPY_CYCLE_FINISHED', copies=statuses,
            next_copy_unix=following, observed_unix=time.time()))
        if following is None or cycle + 1 == config['max_cycles'] or following >= config['hard_end_unix']:
            break
        time.sleep(max(0, following - time.time()))
    write(root / 'COMPLETE.json', dict(status='BOUNDED_COPY_CADENCE_FINISHED', observed_unix=time.time()))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    options = parser.parse_args()
    try:
        run(options.config)
    except BaseException as error:
        print(json.dumps(dict(status='COPY_CONTROLLER_FAILED', error_type=type(error).__name__)))
        raise SystemExit(1)
