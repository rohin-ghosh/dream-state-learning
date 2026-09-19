"""R165 non-material frozen serialization repair; no launcher or implicit replay."""

import argparse
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import time


BASE = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
ROOT = BASE / 'parented_frozen'
SOURCE = BASE / 'source'
OPERATION_ONCE = BASE.parent / 'orch_r165_frozen_boundary_recovery_20260917/FROZEN_SLEEP1_BOUNDARY_CONSUMED'
ARM = 'parented_frozen'
HOST = 'a4u8g-0105'
UUID = 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397'
STREAM = 'organism_v6/orch_r150_matched_stream.py'
HELPER = 'gpu/orch_r165_frozen_boundary_recovery.py'
NATIVE = 'gpu/orch_r125_continual_native.py'
STREAM_SHA = '99f1fc1b1c02d789d7d22e58cb98f2e36cd43f051e5e7a08b1afcabde7ed2866'
NATIVE_SHA = 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'
PINS = {
    'initial': (ROOT / 'checkpoints/initial/COMMIT.json',
        '68580b9e6f4db25d0bc8b5a2107eec7507863d617065ff8b3f6d7c352a97417c'),
    'orphan': (ROOT / 'checkpoints/sleep_000001/COMMIT.json',
        '1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977'),
    'tail': (ROOT / 'stream/records/00000000000000000013.json',
        '0a8711cb081396df3ac12f1ccd6ab1fb5005f62fddab6b589f1561fac6408f08'),
    'failure': (BASE / 'attempts/run-parented_frozen-attempt2/NATIVE_FAILED.json',
        '10ad0e99cddb7d29aed773412efb2f0f863b404c0ed6f3e8037fb140ed3d2dc9'),
    'exit': (BASE / 'attempts/run-parented_frozen-attempt2/NATIVE_EXIT.json',
        '31fc60d263af446374b274a5531a658b557c330c7c4632e498acf32ab47eef10'),
    'lifecycle': (BASE / 'attempts/run-parented_frozen-attempt2/LIFECYCLE.json',
        'a982a7fb02f7cd8c1c4eb24d9ed69fde4e017b8e76ccfd6d6c283d6e4766b107'),
}
OLD_PREDICATE = "and references['adapter'] == previous['checkpoint_sha256']['adapter'],"
NEW_PREDICATE = 'and frozen_checkpoint_identity(previous, checkpoint),'
IMPORT = 'from gpu.orch_r165_frozen_boundary_recovery import frozen_checkpoint_identity\n'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(safe_bytes(path)).hexdigest()


def safe_bytes(path, expected_sha256=None, *, reason='immutable_file_bytes'):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_unlinked_read')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for component in path.parts[1:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                             dir_fd=directory)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'admitted_regular_file')
            raw = stream.read()
            after = os.fstat(stream.fileno())
            fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            require(all(getattr(before, field) == getattr(after, field) for field in fields)
                    and len(raw) == before.st_size, 'file_changed_during_admitted_read')
    finally:
        os.close(directory)
    if expected_sha256 is not None:
        require(hashlib.sha256(raw).hexdigest() == expected_sha256, reason)
    return raw


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def regular(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve()
            and not any(item.is_symlink() for item in (path, *path.parents))
            and path.is_file(), 'regular_absolute_reference')
    return path


def decode(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError('nonfinite_JSON:' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def read(path):
    return decode(safe_bytes(path))


def reference(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(safe_bytes(path)).hexdigest())


def bound(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'exact_file_reference')
    return decode(safe_bytes(ref['path'], ref['sha256'], reason='immutable_reference_bytes'))


def write_once(path, value):
    path = Path(path)
    require(path.parent == path.parent.resolve() and not path.is_symlink(), 'safe_new_receipt_path')
    with path.open('xb') as stream:
        stream.write(encoded(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def semantic_config(config):
    require(type(config) is dict, 'complete_adapter_config')
    result = deepcopy(config)
    targets = result.get('target_modules')
    require(type(targets) is list and targets and all(type(item) is str and item for item in targets)
            and len(set(targets)) == len(targets), 'unique_string_target_modules')
    result['target_modules'] = sorted(targets)
    return encoded(result)


def exact_value(left, right, torch):
    if type(left) is not type(right):
        return False
    if torch.is_tensor(left):
        return (left.device.type == right.device.type == 'cpu' and left.dtype == right.dtype
                and left.shape == right.shape and torch.equal(left, right))
    if type(left) is dict:
        return left.keys() == right.keys() and all(exact_value(left[key], right[key], torch) for key in left)
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(exact_value(before, after, torch) for before, after in zip(left, right))
    return left == right


def checkpoint_payload(checkpoint):
    from gpu.orch_r125_continual_native import BASE_SHA256
    from organism_v6.orch_r125_continual_stream import validate_experiment
    import torch

    adapter = Path(checkpoint['adapter_path'])
    commit = read(adapter.parent / 'COMMIT.json')
    require(encoded(commit) == encoded(checkpoint), 'checkpoint_exact_COMMIT')
    require(adapter.name == 'adapter' and adapter == adapter.resolve()
            and not adapter.is_symlink(), 'actual_adapter_directory')
    require(set(checkpoint['adapter_files']) == {'adapter_config.json', 'adapter_model.safetensors', 'README.md'},
            'known_complete_adapter_inventory')
    require(set(item.name for item in adapter.iterdir()) == set(checkpoint['adapter_files']),
            'no_unbound_adapter_entries')
    adapter_bytes = {name: safe_bytes(adapter / name, checksum, reason='adapter_file_binding')
                     for name, checksum in checkpoint['adapter_files'].items()}
    optimizer = Path(checkpoint['optimizer_rng_path'])
    require(optimizer == adapter.parent / 'optimizer_rng.pt', 'checkpoint_local_optimizer_RNG')
    require(checkpoint['base_sha256'] == BASE_SHA256, 'checkpoint_base')
    validate_experiment(checkpoint['experiment'])
    references = checkpoint['checkpoint_sha256']
    require(set(references) == {'adapter', 'optimizer', 'rng'}
            and references['adapter'] == digest(checkpoint['adapter_files']), 'adapter_file_binding')
    require(references['optimizer'] == references['rng'], 'optimizer_RNG_file_binding')
    optimizer_bytes = safe_bytes(optimizer, references['optimizer'], reason='optimizer_RNG_file_binding')
    require(type(checkpoint['optimizer_steps']) is int and checkpoint['optimizer_steps'] == 0,
            'frozen_checkpoint_zero_steps')
    payload = torch.load(io.BytesIO(optimizer_bytes), map_location='cpu', weights_only=True)
    require(type(payload) is dict and set(payload) == {'optimizer', 'parameter_names', 'optimizer_steps',
            'cpu_rng', 'cuda_rng', 'python_rng', 'experiment'}, 'complete_optimizer_RNG_payload')
    require(type(payload['optimizer_steps']) is int and payload['optimizer_steps'] == 0,
            'frozen_payload_zero_steps')
    require(type(payload['optimizer']) is dict and set(payload['optimizer']) == {'state', 'param_groups'}
            and payload['optimizer']['state'] == {}, 'frozen_empty_AdamW_state')
    names = payload['parameter_names']
    require(type(names) is list and names and all(type(name) is str for name in names)
            and len(set(names)) == len(names), 'unique_optimizer_parameter_order')
    groups = payload['optimizer']['param_groups']
    require(type(groups) is list and groups and all(type(group) is dict and type(group.get('params')) is list
            for group in groups), 'actual_optimizer_parameter_groups')
    indices = [index for group in groups for index in group['params']]
    require(all(type(index) is int for index in indices) and indices == list(range(len(names))),
            'optimizer_parameter_order_binding')
    require(encoded(payload['experiment']) == encoded(checkpoint['experiment']), 'optimizer_experiment_binding')
    require(torch.is_tensor(payload['cpu_rng']) and payload['cpu_rng'].dtype == torch.uint8
            and payload['cpu_rng'].ndim == 1 and payload['cpu_rng'].numel() > 0
            and type(payload['cuda_rng']) is list and payload['cuda_rng']
            and all(torch.is_tensor(state) and state.dtype == torch.uint8 and state.ndim == 1
                    and state.numel() > 0 for state in payload['cuda_rng'])
            and type(payload['python_rng']) is tuple, 'retained_complete_RNG_states')
    return payload, adapter_bytes


def frozen_checkpoint_identity(previous, checkpoint):
    import torch
    from safetensors.torch import load

    before_payload, before_bytes = checkpoint_payload(previous)
    after_payload, after_bytes = checkpoint_payload(checkpoint)
    require(previous['base_sha256'] == checkpoint['base_sha256']
            and previous['adapter_state_sha256'] == checkpoint['adapter_state_sha256'], 'frozen_model_identity')
    before_files, after_files = previous['adapter_files'], checkpoint['adapter_files']
    require(all(before_files[name] == after_files[name] for name in before_files if name != 'adapter_config.json'),
            'frozen_model_and_other_file_bytes')
    require(semantic_config(decode(before_bytes['adapter_config.json']))
            == semantic_config(decode(after_bytes['adapter_config.json'])), 'full_frozen_config_semantics')
    before_tensors = load(before_bytes['adapter_model.safetensors'])
    after_tensors = load(after_bytes['adapter_model.safetensors'])
    require(before_tensors and exact_value(before_tensors, after_tensors, torch), 'frozen_adapter_tensors')
    for key in ('optimizer', 'parameter_names', 'optimizer_steps', 'experiment'):
        require(exact_value(before_payload[key], after_payload[key], torch), 'frozen_optimizer_' + key)
    return True


def repair_stream(original):
    require(hashlib.sha256(original).hexdigest() == STREAM_SHA, 'exact_candidate5_stream_source')
    text = original.decode()
    require(text.count(OLD_PREDICATE) == 1 and IMPORT not in text, 'single_scoped_frozen_predicate')
    text = text.replace('from copy import deepcopy\n', 'from copy import deepcopy\n' + IMPORT, 1)
    result = text.replace(OLD_PREDICATE, NEW_PREDICATE, 1)
    require(result.replace(IMPORT, '', 1).replace(NEW_PREDICATE, OLD_PREDICATE, 1).encode() == original,
            'reversible_frozen_predicate_only')
    compile(result, STREAM, 'exec')
    return result.encode()


def inventory(source):
    source = Path(source)
    require(source.is_dir() and source == source.resolve(), 'canonical_source_directory')
    result = {}
    for path in sorted(source.rglob('*')):
        require(not path.is_symlink(), 'source_symlink_forbidden')
        if path.is_file():
            result[str(path.relative_to(source))] = sha(path)
        else:
            require(path.is_dir(), 'source_regular_files_only')
    return result


def stage_source(original, destination, expected_inventory):
    original, destination = Path(original), Path(destination)
    require(inventory(original) == expected_inventory, 'complete_original_inventory')
    require(expected_inventory.get(NATIVE) == NATIVE_SHA and expected_inventory.get(STREAM) == STREAM_SHA,
            'proven_candidate5_native_and_stream')
    require(HELPER not in expected_inventory, 'new_repair_not_recursive')
    require(destination.is_absolute() and not destination.exists() and not destination.is_symlink()
            and not destination.resolve().is_relative_to(original), 'new_inactive_source_only')
    replacement = repair_stream(safe_bytes(original / STREAM, STREAM_SHA))
    destination.mkdir(parents=False, exist_ok=False)
    for relative in expected_inventory:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original / relative, target)
    (destination / STREAM).write_bytes(replacement)
    shutil.copyfile(Path(__file__).resolve(), destination / HELPER)
    expected = dict(expected_inventory, **{STREAM: hashlib.sha256(replacement).hexdigest(),
                                         HELPER: sha(Path(__file__).resolve())})
    require(inventory(original) == expected_inventory and inventory(destination) == expected,
            'only_declared_source_delta')
    return dict(schema='R165_INACTIVE_SOURCE_REPAIR_V1', original_source=str(original),
        repaired_source=str(destination), original_files=expected_inventory, repaired_files=expected,
        changed_files=[STREAM], added_files=[HELPER], native_unchanged_sha256=NATIVE_SHA,
        source_frozen=False, GPU_launched=False)


def verify_repair(manifest):
    original, repaired = Path(manifest['original_source']), Path(manifest['repaired_source'])
    require(original == SOURCE and repaired != original and not repaired.is_relative_to(BASE),
            'isolated_repair_original_provenance')
    require(inventory(original) == manifest['original_files']
            and inventory(repaired) == manifest['repaired_files'], 'exact_original_and_repair_inventory')
    expected = dict(manifest['original_files'])
    expected[STREAM] = hashlib.sha256(repair_stream(safe_bytes(original / STREAM, STREAM_SHA))).hexdigest()
    expected[HELPER] = sha(Path(__file__).resolve())
    require(manifest['schema'] == 'R165_INACTIVE_SOURCE_REPAIR_V1'
            and expected == manifest['repaired_files'] and expected[NATIVE] == NATIVE_SHA,
            'only_reviewed_semantic_repair')
    import sys
    for name, module in tuple(sys.modules.items()):
        if name == 'gpu' or name == 'organism_v6' or name.startswith(('gpu.', 'organism_v6.')):
            filename = getattr(module, '__file__', None)
            if filename is not None:
                path = Path(filename).resolve()
                require(path.is_relative_to(repaired) and str(path.relative_to(repaired)) in expected,
                        'all_loaded_project_modules_from_repair_closure')
    return repaired


def journal_prefix(root):
    directory = Path(root) / 'stream/records'
    files = {path.name: reference(path) for path in sorted(directory.iterdir())}
    require(set(files) == {f'{index:020d}{suffix}.json' for index in range(14) for suffix in ('', '.intent')},
            'exact_original_pending_prefix_no_duplicate_boundary')
    files['JOURNAL.json'] = reference(Path(root) / 'stream/JOURNAL.json')
    return files


def transition(document, orphan):
    from organism_v6.orch_r150_matched_stream import MatchedStream

    original = deepcopy(document)
    state = document['state']
    require(state['matched']['arm'] == ARM and state['sleep_receipts'] == []
            and state['sleep_frontier'] == 0 and state['rows'], 'first_frozen_boundary_only')
    stream = MatchedStream.restore(document, expected_sha256=document['sha256'], expected_arm=ARM,
        expected_cohort_sha256=state['matched']['cohort_sha256'])
    require(stream.pending == 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()]),
            'exact_pending_sleep_frontier')
    frozen_checkpoint_identity(stream._initial_checkpoint, orphan)
    receipt = stream.frozen_boundary_receipt(orphan, frozen_base_verified=True, cycle=1)
    stream.pending = None
    records = []
    saved = stream.commit_sleep(receipt, lambda kind, value: records.append((kind, value)))
    require(len(records) == 1 and records[0][0] == 'SLEEP_COMPLETE', 'one_missing_transition_only')
    allowed = {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'}
    require({key: value for key, value in state.items() if key not in allowed}
            == {key: value for key, value in saved['state'].items() if key not in allowed}
            and document == original, 'exact_history_carry_counters_and_pending_input_preserved')
    require(saved['state']['model_state_sha256'] == digest(orphan['checkpoint_sha256']),
            'orphan_optimizer_and_RNG_checkpoint_selected')
    return dict(kind=records[0][0], document=records[0][1])


def prepare(plan_path, manifest_ref):
    from gpu import orch_r150_matched_native as matched
    from gpu import orch_r150_readout_custody as readouts

    manifest = bound(manifest_ref)
    verify_repair(manifest)
    plan_bytes = safe_bytes(plan_path)
    plan_ref = dict(path=str(plan_path), sha256=hashlib.sha256(plan_bytes).hexdigest())
    plan, cohort = matched.validate_plan(decode(plan_bytes))
    require(cohort == bound(plan['matched_cohort']), 'admitted_cohort_bytes')
    require(plan['root'] == str(ROOT) and plan['source_root'] == str(SOURCE)
            and plan['physical'] == 6 and plan['gpu_uuid'] == UUID and plan['matched_arm'] == ARM,
            'original_frozen_life_and_physical6_only')
    require(plan['hard_end_unix'] == 1789646400 and time.time() < plan['hard_end_unix'],
            'original_unextended_wall')
    refs = {name: dict(path=str(path), sha256=checksum) for name, (path, checksum) in PINS.items()}
    documents = {name: bound(ref) for name, ref in refs.items()}
    lifecycle = documents['lifecycle']
    require(lifecycle['status'] == 'SERVICE_EXIT_VERIFIED' and lifecycle['cgroup_empty_verified'] is True
            and lifecycle['service_returncode'] == 1, 'original_native_failed_and_reaped')
    prefix = journal_prefix(ROOT)
    tail = documents['tail']
    require(tail['kind'] == 'SLEEP_REQUEST' and tail['document']['cycle'] == 1, 'actual_pending_sleep1')
    proposed = transition(tail['document']['resume_state'], documents['orphan'])
    disposition = readouts.disposition(plan_path, plan, documents['orphan'], 1)
    require(disposition == 'NOT_STARTED', 'missing_sleep1_readout_not_completed_or_replayed')
    require(journal_prefix(ROOT) == prefix, 'pending_prefix_stable_during_prepare')
    return dict(schema='R165_FROZEN_BOUNDARY_PREPARATION_V1', status='CPU_PREPARED_NOT_APPLIED',
        plan=plan_ref, cohort=plan['matched_cohort'], repair_manifest=manifest_ref,
        evidence=refs, prefix=prefix, proposed_transition_sha256=digest(proposed),
        resume_checkpoint=refs['orphan'], preserved_optimizer_rng_sha256=documents['orphan']['checkpoint_sha256']['rng'],
        readout=dict(cycle=1, status='NOT_STARTED', completed=False,
                     next_action='UNCHANGED_FRESH_READOUT_BEFORE_NEXT_GENERATION'),
        GPU_launch_authorized=False, generation_calls=0, optimizer_updates=0,
        resume_admission='NEW_MAIN_GO_AND_REPAIR_AWARE_STRICT_DEVICE_SUPERVISOR_REQUIRED')


def validate_go(go, prepared_ref):
    import socket
    require(type(go) is dict and set(go) == {'schema', 'prepared', 'action', 'host', 'not_before', 'expires'},
            'exact_boundary_completion_GO')
    require(go['schema'] == 'R165_BOUNDARY_COMPLETION_MAIN_GO_V1' and go['prepared'] == prepared_ref
            and go['action'] == 'COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU' and go['host'] == socket.gethostname() == HOST,
            'new_Main_authorized_boundary_only')
    require(all(type(go[key]) in (int, float) for key in ('not_before', 'expires'))
            and go['not_before'] <= time.time() < go['expires'] <= 1789646400, 'current_bound_Main_GO')


def consume_operation(prepared_ref, main_go_ref, destination):
    marker = OPERATION_ONCE
    require(marker.is_absolute() and marker == marker.resolve(), 'fixed_unlinked_operation_marker')
    marker.mkdir(mode=0o700, parents=False, exist_ok=False)
    descriptor = os.open(marker.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    write_once(marker / 'CONSUMED.json', dict(schema='R165_FIXED_BOUNDARY_OPERATION_V1',
        operation='ORIGINAL_FROZEN_SLEEP1_ONLY', root=str(ROOT), orphan_commit_sha256=PINS['orphan'][1],
        prepared=prepared_ref, main_go=main_go_ref, receipts=str(destination), no_retry=True,
        consumed_unix=time.time()))


def complete_boundary(prepared_ref, main_go_ref, receipt_directory):
    from gpu.orch_r150_matched_journal import MatchedJournal

    prepared, go = bound(prepared_ref), bound(main_go_ref)
    validate_go(go, prepared_ref)
    destination = Path(receipt_directory)
    require(destination.is_absolute() and destination == destination.resolve()
            and not destination.is_relative_to(BASE), 'separate_recovery_receipts')
    manifest = bound(prepared['repair_manifest'])
    require(not destination.is_relative_to(Path(manifest['repaired_source'])), 'receipts_outside_repaired_source')
    consume_operation(prepared_ref, main_go_ref, destination)
    try:
        destination.mkdir(parents=False, exist_ok=False)
        write_once(destination / 'ONCE.json', dict(main_go=main_go_ref, prepared=prepared_ref,
            fixed_operation_marker=str(OPERATION_ONCE), no_retry=True))
        require(prepare(prepared['plan']['path'], prepared['repair_manifest']) == prepared, 'unchanged_prepared_recovery')
        with MatchedJournal(ROOT / 'stream', arm=ARM, cohort_sha256=prepared['cohort']['sha256']) as journal:
            require(prepare(prepared['plan']['path'], prepared['repair_manifest']) == prepared,
                    'exclusive_prepared_recovery_recheck')
            require(journal_prefix(ROOT) == prepared['prefix'], 'exclusive_original_prefix')
            latest = journal.latest_checkpoint()
            orphan = bound(prepared['evidence']['orphan'])
            proposed = transition(latest['document'], orphan)
            require(digest(proposed) == prepared['proposed_transition_sha256'], 'exact_prepared_transition')
            require(bound(main_go_ref) == go, 'unchanged_exact_GO_at_write')
            validate_go(go, prepared_ref)
            written = journal.record(proposed['kind'], proposed['document'])
            require(journal.latest_checkpoint()['document'] == proposed['document']['resume_state'],
                    'actual_completed_saved_boundary')
            for ref in prepared['prefix'].values():
                bound(ref)
            result = dict(schema='R165_BOUNDARY_COMPLETION_V1', status='SLEEP_COMPLETE_APPENDED',
                journal_record=written, prepared=prepared_ref, main_go=main_go_ref,
                operation_marker=reference(OPERATION_ONCE / 'CONSUMED.json'),
                resume_checkpoint=prepared['resume_checkpoint'], readout=prepared['readout'],
                generation_calls=0, optimizer_updates=0, GPU_launched=False, completed_unix=time.time())
            write_once(destination / 'COMPLETED.json', result)
            return result
    except BaseException as error:
        failure = dict(status='FAILED_OR_UNCERTAIN', error_type=type(error).__name__,
            error=str(error), no_retry=True, automatic_replay=False, fixed_operation_marker=str(OPERATION_ONCE))
        write_once(OPERATION_ONCE / 'FAILED.json', failure)
        if destination.is_dir():
            write_once(destination / 'FAILED.json', failure)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    stage = commands.add_parser('stage')
    stage.add_argument('--original', type=Path, required=True)
    stage.add_argument('--destination', type=Path, required=True)
    stage.add_argument('--inventory', type=Path, required=True)
    stage.add_argument('--output', type=Path, required=True)
    preview = commands.add_parser('prepare')
    preview.add_argument('--plan', type=Path, required=True)
    preview.add_argument('--manifest', type=Path, required=True)
    preview.add_argument('--manifest-sha256', required=True)
    preview.add_argument('--output', type=Path, required=True)
    completion = commands.add_parser('complete')
    completion.add_argument('--prepared', type=Path, required=True)
    completion.add_argument('--prepared-sha256', required=True)
    completion.add_argument('--main-go', type=Path, required=True)
    completion.add_argument('--main-go-sha256', required=True)
    completion.add_argument('--receipts', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.command == 'stage':
        result = stage_source(arguments.original, arguments.destination, read(arguments.inventory))
    elif arguments.command == 'prepare':
        result = prepare(arguments.plan, dict(path=str(arguments.manifest), sha256=arguments.manifest_sha256))
    else:
        result = complete_boundary(dict(path=str(arguments.prepared), sha256=arguments.prepared_sha256),
            dict(path=str(arguments.main_go), sha256=arguments.main_go_sha256), arguments.receipts)
        print(json.dumps(dict(status=result['status'], GPU_launched=False)))
        return
    write_once(arguments.output, result)
    print(json.dumps(dict(status=result.get('status', 'INACTIVE_SOURCE_STAGED'), output=reference(arguments.output))))


if __name__ == '__main__':
    main()
