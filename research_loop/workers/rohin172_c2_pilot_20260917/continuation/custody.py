"""Explicitly bound saved-bundle custody; no checkpoint discovery or remote actions."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from gpu import orch_r125_continual_native as native
from gpu import orch_r161_native_executor as exact
from organism_v6.orch_r125_continual_stream import ContinualStream


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PILOT = ROOT.parent / 'PILOT_CONFIG_V1.json'
PILOT_SHA256 = 'ee32ad40a7867c378ecd1f3e3b7885739c10a7f0d06f434f5308ba50dfa9ad97'
ARMS = ('C2_UPDATES_ON', 'C2_UPDATES_OFF')
SCHEMA = 'R172_CONTINUATION_SIDECAR_V1'
FIELDS = ('actual_observation_or_no_result', 'tentative_judgment_and_uncertainty',
          'unfinished_next_action')
require = native.require
digest = native.digest


def encoded(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bytes(path, limit=512 * 1024**2):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_nontraversing_path')
    with exact._directory(path.parent) as directory:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(descriptor, 'rb') as handle:
            before = os.fstat(handle.fileno())
            require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, 'bounded_regular_file')
            raw = handle.read(before.st_size + 1)
            after = os.fstat(handle.fileno())
            current = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns,
                                      item.st_ctime_ns, item.st_mode)
            require(signature(before) == signature(after) == signature(current)
                    and len(raw) == before.st_size, 'file_changed_during_read')
            return raw


def write_once(path, document=None, *, raw=None, mode=0o444):
    path = Path(path)
    require((document is None) != (raw is None), 'one_receipt_representation')
    path.parent.mkdir(parents=True, exist_ok=True)
    with exact._directory(path.parent) as directory:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(encoded(document) if raw is None else raw)
            handle.flush()
            os.fchmod(handle.fileno(), mode)
            os.fsync(handle.fileno())
        os.fsync(directory)


def pilot():
    raw = read_bytes(PILOT, 65536)
    require(sha(raw) == PILOT_SHA256, 'exact_PILOT_CONFIG_V1_SHA256')
    return exact._json(raw)


def relative(name):
    path = Path(name)
    require(type(name) is str and name and not path.is_absolute() and path.as_posix() == name
            and '..' not in path.parts and '.' not in path.parts, 'safe_bundle_relative_name')
    return path


def inventory(root):
    root = Path(root)
    require(root.is_absolute(), 'absolute_bundle_root')
    with exact._directory(root):
        pass
    files, directories, total = {}, {}, 0
    for parent, children, names in os.walk(root, followlinks=False):
        for name in sorted(children + names):
            path = Path(parent) / name
            metadata = path.lstat()
            require(not stat.S_ISLNK(metadata.st_mode), 'no_bundle_symlinks')
            key = path.relative_to(root).as_posix()
            require(stat.S_IMODE(metadata.st_mode) <= 0o777, 'no_privileged_file_modes')
            if stat.S_ISDIR(metadata.st_mode):
                directories[key] = stat.S_IMODE(metadata.st_mode)
            else:
                require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1, 'unshared_regular_bundle_file')
                total += metadata.st_size
                require(total <= 2 * 1024**3 and len(files) < 16384, 'bounded_saved_bundle')
                files[key] = dict(sha256=sha(read_bytes(path)), bytes=metadata.st_size,
                                  mode=stat.S_IMODE(metadata.st_mode))
    return dict(files=files, directories=directories)


def source_pins():
    from gpu import orch_r144_sleep_targets, orch_r108_guided_native, orch_r145_suffix_boundary
    from gpu import orch_r137_node4_containment, ny_caption_generation_profile
    del orch_r144_sleep_targets, orch_r108_guided_native, orch_r145_suffix_boundary
    del orch_r137_node4_containment, ny_caption_generation_profile
    paths = {PILOT, ROOT.parent / 'README.md', *ROOT.glob('*.py'), *ROOT.glob('*.md'),
             *REPO.glob('tests/test_orch_r172_continuation*.py')}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == '.py' and path.is_relative_to(REPO):
                paths.add(path)
    return {path.relative_to(REPO).as_posix(): sha(read_bytes(path)) for path in sorted(paths)}


def verify_pins(pins):
    require(type(pins) is dict and pins, 'nonempty_source_pins')
    for name, expected in pins.items():
        require(sha(read_bytes(REPO / relative(name))) == expected, 'source_pin_changed:' + name)
    required = source_pins()
    require(set(required) <= set(pins), 'complete_loaded_source_pin_inventory')


def validate_binding(binding):
    config = pilot()
    require(binding['schema'] == 'R172_MAIN_BOUND_SAVED_BUNDLE_V1'
            and binding['pilot_sha256'] == PILOT_SHA256, 'explicit_fixed_pilot_binding')
    require(binding['source_life'] == config['source_life']
            and binding['source_journal_id'] == config['source_journal_id'], 'exact_C2_source_identity')
    require(binding['selection_authority'] == 'Main'
            and binding['first_guided_sleep_bound'] is True, 'Main_bound_endpoint_required_no_selection')
    require(binding['checkpoint_cycle'] > config['pre_intervention_checkpoint']['cycle']
            and binding['checkpoint']['sha256'] != config['pre_intervention_checkpoint']['sleep_record_sha256'],
            'pre40_is_preservation_only_not_withdrawal_source')
    require(Path(binding['checkpoint']['path']).parent.name == f"sleep_{binding['checkpoint_cycle']:06d}"
            and Path(binding['checkpoint']['path']).name == 'COMMIT.json'
            and Path(binding['checkpoint']['path']).is_relative_to(Path(binding['source_life']) / 'checkpoints'),
            'externally_bound_saved_sleep_path')
    root = Path(binding['snapshot_root'])
    require(root.is_absolute() and not root.is_relative_to(Path(config['source_life'])),
            'read_only_preserved_bundle_not_live_life')
    require(binding['snapshot_complete'] is True and binding['raw_history_complete'] is True
            and binding['workspace_complete'] is True, 'complete_snapshot_attestation_required')
    files = binding['inventory']['files']
    require({'checkpoint/COMMIT.json', 'checkpoint/optimizer_rng.pt', 'stream.json',
             'plan.json', 'endpoint.json', 'withdrawal.json', 'anchors.json'} <= set(files),
            'all_saved_state_components_required')
    require(any(name.startswith('history/') for name in files)
            and 'workspace' in binding['inventory']['directories'], 'raw_history_and_workspace_required')
    for name in (*files, *binding['inventory']['directories']):
        relative(name)
    require(files['checkpoint/COMMIT.json']['sha256'] == binding['checkpoint']['sha256'],
            'checkpoint_reference_matches_manifest')
    return config


def load_bundle(binding, *, saved_root=None):
    config = validate_binding(binding)
    root = Path(binding['snapshot_root']) if saved_root is None else Path(saved_root)
    observed = inventory(root)
    expected = deepcopy(binding['inventory'])
    if saved_root is not None:
        for metadata in expected['files'].values():
            metadata['mode'] = 0o444
        expected['directories'] = {name: 0o755 for name in expected['directories']}
    require(observed == expected, 'exact_complete_snapshot_inventory')
    read = lambda name: exact._json(read_bytes(root / name))
    commit_raw = read_bytes(root / 'checkpoint/COMMIT.json')
    commit = exact._checkpoint_document(Path(binding['checkpoint']['path']), commit_raw)
    require(commit['base_sha256'] == native.BASE_SHA256, 'frozen_base_identity')
    require({name.removeprefix('checkpoint/adapter/') for name in binding['inventory']['files']
             if name.startswith('checkpoint/adapter/')} == set(commit['adapter_files']), 'complete_adapter_inventory')
    for name, expected in commit['adapter_files'].items():
        require(binding['inventory']['files']['checkpoint/adapter/' + name]['sha256'] == expected,
                'exact_saved_adapter_bytes')
    require(binding['inventory']['files']['checkpoint/optimizer_rng.pt']['sha256']
            == commit['checkpoint_sha256']['optimizer'], 'exact_optimizer_and_rng_bytes')
    plan, endpoint, withdrawal = read('plan.json'), read('endpoint.json'), read('withdrawal.json')
    stream_document = read('stream.json')
    stream = ContinualStream.restore(stream_document, expected_sha256=stream_document['sha256'])
    require(stream.pending is None and stream.sleep_frontier == len(stream.rows)
            and stream.model_state_sha256 == digest(commit['checkpoint_sha256']), 'completed_sleep_exact_stream_state')
    require(stream.history.checkpoint()['system_prompt'] == plan['system_prompt']
            and stream.history.checkpoint()['birth_prompt'] == plan['birth_prompt']
            and stream.experiment == commit.get('experiment'), 'saved_history_plan_experiment_join')
    require(plan['base_sha256'] == native.BASE_SHA256 and plan['new_presentations'] == 16
            and plan['rehearsal_presentations'] == 1 and plan['anchor_lambda'] == 0.25,
            'supported_inherited_native_sleep_recipe')
    adapter_config = read('checkpoint/adapter/adapter_config.json')
    require(adapter_config['r'] == 8 and adapter_config.get('bias') == 'none', 'saved_rank8_LoRA_only')
    require(endpoint['first_completed_guided_sleep'] is True
            and endpoint['checkpoint'] == binding['checkpoint']
            and endpoint['rendered_rohin_inbox_id'] == config['already_published_guidance']['rohin_inbox_id'],
            'bound_rendered_exposure_endpoint_not_inbox_publication')
    responses = endpoint['committed_response_source_sha256']
    require(len(responses) >= 4 and len(responses) == len(set(responses))
            and set(responses) <= {row['source_sha256'] for row in stream.rows}, 'four_actual_committed_responses')
    response_order = [row['source_sha256'] for row in stream.rows]
    require(response_order[response_order.index(responses[0]):] == responses,
            'complete_guided_response_suffix_no_episode_selection')
    require(endpoint['exposure_receipt'].startswith('history/')
            and endpoint['exposure_receipt'] in binding['inventory']['files'], 'preserved_exposure_receipt')
    exposure = read(endpoint['exposure_receipt'])
    require(exposure['first_response_source_sha256'] == responses[0]
            and exposure['rohin_inbox_id'] == config['already_published_guidance']['rohin_inbox_id']
            and sha(exposure['bound_rohin_text'].encode()) == exposure['bound_rohin_text_sha256']
            and exposure['bound_rohin_text'].strip()
            and exposure['request_sha256'] == digest(exposure['request'])
            and any(exposure['bound_rohin_text'] in message['content']
                    for message in exposure['request']['rendered']['messages']), 'actual_bound_rendered_Rohin_exposure')
    require(endpoint['generated_tokens'] == sum(len(row['token_ids']) for row in stream.rows
            if row['source_sha256'] in responses), 'actual_guided_generated_token_join')
    require(0 <= endpoint['generated_tokens'] <= 4096 and 0 <= endpoint['elapsed_seconds'] <= 14400,
            'unchanged_guided_endpoint_budget')
    require(withdrawal['adequacy_bound_by'] == 'Main' and withdrawal['adequate'] is True,
            'empty_or_inadequate_carry_failure_no_reselection')
    events = {event.event_id: event for event in stream.history.events}
    carry = events[withdrawal['carry_event_id']]
    require(carry.actor == 'child' and carry.text.strip(), 'actual_nonempty_child_carry')
    rows = [row for row in stream.rows if row['source_sha256'] == carry.source_sha256]
    require(len(rows) == 1 and rows[0]['target'] == carry.text and rows[0]['token_ids'], 'carry_from_actual_saved_response')
    require(set(withdrawal['semantic_spans']) == set(FIELDS), 'all_three_carry_fields_required')
    for field, span in withdrawal['semantic_spans'].items():
        require(type(span) is list and len(span) == 2 and all(type(value) is int for value in span)
                and 0 <= span[0] < span[1] <= len(carry.text) and carry.text[span[0]:span[1]].strip(),
                'actual_nonempty_semantic_span:' + field)
    evidence = [events[name] for name in withdrawal['evidence_event_ids']]
    require(len(evidence) == len({event.event_id for event in evidence}), 'no_duplicate_environment_evidence')
    for event in evidence:
        require(event.actor == 'environment' and event.text.strip(), 'actual_environment_evidence_only')
        reference = withdrawal['evidence_receipts'][event.event_id]
        require(reference in binding['inventory']['files'] and reference.startswith('history/'),
                'evidence_receipt_in_preserved_history')
        receipt = read(reference)
        require(receipt['event'] == asdict(event) and receipt['delivered_to_child'] is True
                and receipt['source_kind'] in ('actual_environment_execution', 'delivered_calculation_check'),
                'real_delivered_evidence_not_offline_score_or_invented_outcome')
    return dict(binding=binding, commit=commit, stream=stream_document, plan=plan, endpoint=endpoint,
                withdrawal=withdrawal, carry=asdict(carry), evidence=[asdict(event) for event in evidence])


def stage(binding_path, binding_sha256, destination):
    binding_raw = read_bytes(Path(binding_path), 16 * 1024**2)
    require(sha(binding_raw) == binding_sha256, 'explicit_Main_binding_SHA256')
    binding = exact._json(binding_raw)
    validate_binding(binding)
    destination = Path(destination)
    require(destination.is_absolute() and destination.is_relative_to(ROOT)
            and destination != ROOT and '..' not in destination.parts, 'own_disjoint_staging_directory')
    require(not any(path.is_symlink() for path in (destination, *destination.parents)), 'no_destination_symlink')
    destination.mkdir(parents=True, exist_ok=False)
    try:
        bundle = load_bundle(binding)
        write_once(destination / 'MAIN_BINDING.json', raw=binding_raw)
        pins = source_pins()
        write_once(destination / 'SOURCE_PINS.json', pins)
        for arm in ARMS:
            saved = destination / arm / 'saved'
            saved.mkdir(parents=True)
            for name in sorted(binding['inventory']['directories'], key=lambda value: len(Path(value).parts)):
                (saved / name).mkdir(exist_ok=True)
                (saved / name).chmod(0o755)
            for name, metadata in binding['inventory']['files'].items():
                raw = read_bytes(Path(binding['snapshot_root']) / name)
                require(sha(raw) == metadata['sha256'] and len(raw) == metadata['bytes'], 'source_changed_before_copy')
                write_once(saved / name, raw=raw)
            write_once(destination / arm / 'ARM.json', dict(schema=SCHEMA, arm=arm,
                updates_enabled=arm == ARMS[0], binding_sha256=binding_sha256,
                pilot_sha256=PILOT_SHA256, initial_inventory_sha256=digest(binding['inventory']),
                generation_rng_initialization='exact_saved_RNG_cloned_not_reseeded',
                continuation=pilot()['continuation']))
            load_bundle(binding, saved_root=saved)
        require(inventory(Path(binding['snapshot_root'])) == binding['inventory'], 'source_unchanged_after_copy')
        verify_pins(pins)
        result = dict(schema=SCHEMA, status='STAGED_BYTES_NOT_RUNTIME_ADMISSION', arms=list(ARMS),
                      source_selected_by_sidecar=False, source_checkpoint=binding['checkpoint'],
                      binding_sha256=binding_sha256, source_pins_sha256=digest(pins),
                      exact_bytes_copied=True, original_modes=binding['inventory'],
                      tensor_restore_tested=False, generation_or_GPU_launch=False,
                      history_sha256=bundle['stream']['state']['history']['state_sha256'])
        write_once(destination / 'STAGED.json', result)
        return result
    except BaseException as error:
        write_once(destination / 'FAILED.json', dict(schema=SCHEMA, status='PRESERVED_NO_RETRY',
                   error_type=type(error).__name__, error=str(error), GPU_launch=False))
        raise


def admitted_from_saved(saved, binding, fork_binding):
    saved = Path(saved)
    reference = binding['checkpoint']
    raw = read_bytes(saved / 'checkpoint/COMMIT.json')
    require(sha(raw) == reference['sha256'], 'unchanged_original_commit_no_path_rewrite')
    document = exact._checkpoint_document(Path(reference['path']), raw)
    admitted = exact.AdmittedCheckpoint(encoded(fork_binding), encoded(reference), raw,
        tuple((name, read_bytes(saved / 'checkpoint/adapter' / name)) for name in document['adapter_files']),
        read_bytes(saved / 'checkpoint/optimizer_rng.pt'))
    admitted.decode()
    return admitted


def materialize_workspace(arm_root, binding):
    arm_root = Path(arm_root)
    require(arm_root.name in ARMS and arm_root.is_relative_to(ROOT), 'own_staged_arm_only')
    destination = arm_root / 'workspace'
    require(not any(path.is_symlink() for path in (destination, *destination.parents)), 'no_workspace_symlink')
    destination.mkdir(exist_ok=False)
    for name in sorted(binding['inventory']['directories'], key=lambda value: len(Path(value).parts)):
        if name.startswith('workspace/'):
            (destination / Path(name).relative_to('workspace')).mkdir(exist_ok=True)
    for name, metadata in binding['inventory']['files'].items():
        if name.startswith('workspace/'):
            raw = read_bytes(arm_root / 'saved' / name)
            require(sha(raw) == metadata['sha256'], 'exact_saved_workspace_bytes')
            write_once(destination / Path(name).relative_to('workspace'), raw=raw, mode=metadata['mode'])
    for name, mode in sorted(binding['inventory']['directories'].items(), reverse=True):
        if name == 'workspace' or name.startswith('workspace/'):
            (destination / Path(name).relative_to('workspace')).chmod(mode)
    result = inventory(destination)
    expected = dict(files={name.removeprefix('workspace/'): value
                          for name, value in binding['inventory']['files'].items()
                          if name.startswith('workspace/')},
                    directories={name.removeprefix('workspace/'): value
                                 for name, value in binding['inventory']['directories'].items()
                                 if name.startswith('workspace/')})
    require(result == expected, 'exact_working_workspace_inventory_and_modes')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--binding-sha256', required=True)
    parser.add_argument('--destination', type=Path, required=True)
    arguments = parser.parse_args(argv)
    print(json.dumps(stage(arguments.binding, arguments.binding_sha256, arguments.destination), sort_keys=True))


if __name__ == '__main__':
    main()
