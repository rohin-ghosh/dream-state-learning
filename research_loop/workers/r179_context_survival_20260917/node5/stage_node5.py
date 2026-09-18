"""Read-only NODE5 handoff preparation; deliberately has no activation path."""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time


HOST = '[REDACTED_HOST]'
RELATIVE_OUTPUT = 'research_loop/workers/r179_context_survival_20260917/node5'
CENSUS = 'research_loop/workers/rohin162_context_console_20260917/SOURCE_CENSUS_1789663949490665603.json'
SOURCE_FILES = (
    'gpu/orch_r125_continual_native.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_plain_context.py',
    'gpu/orch_r166_corrected_retelling.py',
)
LABELS = {0: 'C1', 1: 'C2', 2: 'run1', 3: 'C3', 4: 'C4', 5: 'C5', 6: 'pilot', 7: 'repo_reader'}
MAX_DOCUMENT = 64 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 512 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(document):
    return digest_bytes(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def read_document(path, limit=MAX_DOCUMENT):
    with Path(path).open('rb') as handle:
        raw = handle.read(limit + 1)
    require(len(raw) <= limit, 'bounded_document')
    return json.loads(raw), {'path': str(path), 'sha256': digest_bytes(raw), 'bytes': len(raw)}


def identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=process_id, start_ticks=fields[19], state=fields[0],
                parent_pid=int(fields[1]), group=int(fields[2]), uid=process.stat().st_uid,
                argv_sha256=digest_bytes(process.joinpath('cmdline').read_bytes()),
                cwd=str(process.joinpath('cwd').resolve()),
                cgroup_sha256=digest_bytes(process.joinpath('cgroup').read_bytes()))


def same_identity(expected, actual):
    return all(str(expected[key]) == str(actual[key]) for key in
               ('pid', 'start_ticks', 'uid', 'argv_sha256', 'cwd')) and actual['state'] != 'Z'


def safe_child(root, path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_scoped_path')
    path.relative_to(root)
    return path


def source_metadata(root):
    result = {}
    for relative in SOURCE_FILES:
        path = Path(root) / relative
        if not path.exists():
            result[relative] = {'exists': False}
            continue
        require(path.stat().st_size <= 1024 * 1024, 'bounded_source')
        raw = path.read_bytes()
        tree = ast.parse(raw)
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in ('prepare_sleep', 'finish_sleep', 'run', 'commit_sleep',
                                 'restore', 'checkpoint', 'render', 'compact', 'evict_oldest', '__init__'):
                    functions.setdefault(node.name, []).append(dict(line=node.lineno,
                        ast_sha256=digest_bytes(ast.dump(node, include_attributes=False).encode())))
        entry = dict(path=str(path), exists=True, sha256=digest_bytes(raw), functions=functions)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                    target.id == 'INVITATION' for target in node.targets):
                invitation = ast.literal_eval(node.value)
                require(isinstance(invitation, str), 'literal_invitation')
                entry['invitation_sha256'] = digest_bytes(invitation.encode())
        result[relative] = entry
    return result


def tail_metadata(path):
    with Path(path).open('rb') as handle:
        handle.seek(max(0, Path(path).stat().st_size - 4096))
        suffix = handle.read(4096)
    position = suffix.rfind(b',"index":')
    require(position >= 0, 'canonical_journal_metadata_tail')
    metadata = json.loads(b'{' + suffix[position + 1:])
    require(set(metadata) == {'index', 'journal_id', 'kind', 'previous_sha256', 'schema', 'sha256'},
            'metadata_only_journal_tail')
    require(Path(path).name == f"{metadata['index']:020d}.json", 'record_filename_binding')
    return metadata


def hash_file(path, expected, budget):
    require(not path.is_symlink(), 'checkpoint_no_symlink')
    size = path.stat().st_size
    require(size <= budget[0], 'bounded_checkpoint_hash_budget')
    hasher = hashlib.sha256()
    consumed = 0
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            consumed += len(chunk)
            require(consumed <= size, 'checkpoint_not_growing')
            hasher.update(chunk)
    require(consumed == size and hasher.hexdigest() == expected, 'checkpoint_exact_file_hash')
    budget[0] -= consumed
    return dict(path=str(path), bytes=size, sha256=hasher.hexdigest(), verified=True)


def history_metadata(history):
    require(history['state_sha256'] == digest({key: value for key, value in history.items()
                                              if key != 'state_sha256'}), 'full_history_integrity')
    return dict(state_sha256=history['state_sha256'], events=len(history['events']),
                operations=len(history['operations']), events_sha256=digest(history['events']),
                operations_sha256=digest(history['operations']), frontier_sha256=digest(history['frontier']),
                system_prompt_sha256=digest_bytes(history['system_prompt'].encode()),
                birth_prompt_sha256=digest_bytes(history['birth_prompt'].encode()),
                content_exported=False)


def saved_metadata(logical_root, storage_root):
    records = storage_root / 'stream/records'
    paths = sorted(path for path in records.glob('*.json') if re.fullmatch(r'[0-9]{20}\.json', path.name))
    require(paths, 'existing_live_storage_journal')
    head_before = tail_metadata(paths[-1])
    selected = None
    for path in reversed(paths[-256:]):
        if tail_metadata(path)['kind'] == 'SLEEP_COMPLETE':
            selected = path
            break
    require(selected is not None, 'saved_boundary_in_bounded_256_record_window')
    record, reference = read_document(selected)
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'saved_record_integrity')
    intent, intent_reference = read_document(selected.with_name(selected.stem + '.intent.json'), 8192)
    require(intent == dict(schema=record['schema'], journal_id=record['journal_id'], index=record['index'],
                           previous_sha256=record['previous_sha256'], record_sha256=record['sha256']),
            'saved_record_intent_binding')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(document['status'] == 'COMPLETE' and envelope['sha256'] == digest(state), 'saved_state_integrity')
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'complete_saved_sleep')
    cycle = document['cycle']
    checkpoint_root = logical_root / 'checkpoints' / f'sleep_{cycle:06d}'
    stored_checkpoint_root = storage_root / 'checkpoints' / f'sleep_{cycle:06d}'
    checkpoint, checkpoint_reference = read_document(stored_checkpoint_root / 'COMMIT.json', 1024 * 1024)
    require(document['checkpoint'] == checkpoint, 'exact_checkpoint_document')
    require(digest(checkpoint['checkpoint_sha256']) == state['model_state_sha256'], 'state_model_binding')
    require(checkpoint['checkpoint_sha256']['optimizer'] == checkpoint['checkpoint_sha256']['rng'],
            'single_saved_optimizer_rng_payload')
    budget = [MAX_CHECKPOINT_BYTES]
    optimizer_path = safe_child(checkpoint_root, checkpoint['optimizer_rng_path'])
    optimizer = hash_file(storage_root / optimizer_path.relative_to(logical_root),
                          checkpoint['checkpoint_sha256']['optimizer'], budget)
    adapter_path = safe_child(checkpoint_root, checkpoint['adapter_path'])
    stored_adapter = storage_root / adapter_path.relative_to(logical_root)
    require(set(checkpoint['adapter_files']) == {path.name for path in stored_adapter.iterdir() if path.is_file()},
            'complete_adapter_inventory')
    adapter_files = []
    for name, checksum in sorted(checkpoint['adapter_files'].items()):
        require(Path(name).name == name, 'flat_adapter_file')
        adapter_files.append(hash_file(stored_adapter / name, checksum, budget))
    require(digest(checkpoint['adapter_files']) == checkpoint['checkpoint_sha256']['adapter'], 'adapter_bundle_hash')
    last_paths = sorted(path for path in records.glob('*.json') if re.fullmatch(r'[0-9]{20}\.json', path.name))
    head_after = tail_metadata(last_paths[-1])
    return dict(head_before=head_before, head_after=head_after,
        at_saved_head_when_observed=head_before == head_after == tail_metadata(selected),
        boundary=reference, boundary_intent=intent_reference, record_sha256=record['sha256'],
        cycle=cycle, state_sha256=envelope['sha256'], state_fields=sorted(state),
        state_field_sha256={key: digest(value) for key, value in state.items()},
        full_history=history_metadata(state['history']), rows=len(state['rows']),
        sleep_frontier=state['sleep_frontier'], pending=None, deadline_unix=state['deadline_unix'],
        checkpoint=checkpoint_reference, optimizer_steps=checkpoint['optimizer_steps'],
        adapter_state_sha256=checkpoint['adapter_state_sha256'], model_state_sha256=state['model_state_sha256'],
        checkpoint_bundle=checkpoint['checkpoint_sha256'], optimizer_rng=optimizer,
        adapter_files=adapter_files, payload_deserialized=False, historical_content_exported=False,
        whole_journal_chain_verified=False, executable_boundary_admission=False)


def inspect_row(row):
    result = dict(label=row['label'], physical=row['physical'], logical_root=row['life_root'],
                  storage_root=row['storage_root'], observed_unix=time.time(), stopped=False, restarted=False)
    try:
        current = identity(row['identity']['pid'])
        require(same_identity(row['identity'], current), 'registered_identity_not_live_or_changed')
        result['identity'] = current
        result['ancestry'] = []
        parent_id = current['parent_pid']
        for unused in range(3):
            if parent_id <= 1:
                break
            parent = identity(parent_id)
            result['ancestry'].append(parent)
            parent_id = parent['parent_pid']
        config, config_ref = read_document(row['config_ref']['path'], 1024 * 1024)
        plan, plan_ref = read_document(row['plan_ref']['path'], 1024 * 1024)
        require(config_ref['sha256'] == row['config_ref']['sha256'], 'current_guard_bytes')
        require(plan_ref['sha256'] == row['plan_ref']['sha256'] == config['plan_sha256'], 'current_plan_bytes')
        require(plan['root'] == row['life_root'] and plan['source_root'] == row['source_root'], 'root_source_identity')
        result.update(config_ref=config_ref, plan_ref=plan_ref,
            plan={key: plan.get(key) for key in ('root', 'source_root', 'physical', 'gpu_uuid',
                'hard_end_unix', 'lease_end_unix', 'context_limit', 'segment_tokens', 'segments_per_sleep',
                'presentation_version', 'presleep_variant')},
            prior_wall_extension_present='authorized_wall_extension' in plan,
            preupdate_recovery_present='preupdate_recovery' in plan,
            compaction_invitation_sha256=digest_bytes(plan['compaction_invitation'].encode()),
            plan_field_sha256={key: digest(value) for key, value in plan.items()},
            source=source_metadata(row['source_root']), source_pins_sha256=digest(config.get('source_pins')))
        result['saved'] = saved_metadata(Path(row['life_root']), Path(row['storage_root']))
        require(same_identity(current, identity(current['pid'])), 'identity_changed_during_observation')
        result['status'] = 'PREPARED_METADATA_ONLY_PENDING_MAIN_GO'
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result.update(status='COMPATIBILITY_BLOCKED', error_type=type(error).__name__,
                      error=str(error) if isinstance(error, ValueError) else 'metadata_read_or_shape_failure')
    return result


def capture(root):
    census, census_ref = read_document(root / CENSUS)
    roster, roster_ref = read_document(census['roster_ref']['path'])
    require(roster_ref['sha256'] == census['roster_ref']['sha256'], 'bound_roster')
    census_rows = {row['life_root']: row for node in census['nodes'] if node['node'] == 'ovx3' for row in node['rows']}
    rows = []
    for row in roster['rows']:
        if row['node'] != 'ovx3' or row['life_root'] not in census_rows:
            continue
        require(len(row['natives']) == 1, 'one_registered_actor_per_life')
        native = row['natives'][0]
        require(native['plan_ref'] == census_rows[row['life_root']]['plan_ref'], 'census_plan_binding')
        storage = {entry['storage_root'] for entry in row['registrations']}
        require(len(storage) == 1, 'one_storage_root')
        rows.append(dict(label=LABELS[row['physical']], physical=row['physical'], life_root=row['life_root'],
            storage_root=storage.pop(), identity=native['identity'], config_ref=native['config_ref'],
            plan_ref=native['plan_ref'], source_root=row['current_source_root']))
    require(len(rows) == 8 and {row['physical'] for row in rows} == set(LABELS), 'exact_eight_assigned_lives')
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + ' --remote'
    finished = subprocess.run(['bash', str(root / 'gpu/ovx3_ssh.sh'), command],
                              input=json.dumps(rows), text=True, capture_output=True, timeout=180)
    require(finished.returncode == 0, 'node_wrapper_failed_no_stderr_or_credentials_exported')
    output = json.loads(finished.stdout)
    document = dict(schema='R179_NODE5_READONLY_HANDOFF_PREPARATION_V1',
        observed_at=datetime.now(timezone.utc).isoformat(), census_ref=census_ref, roster_ref=roster_ref,
        probe_sha256=digest_bytes(Path(__file__).read_bytes()), rows=output,
        main_go=None, activation_authorized=False, remote_writes=False, signal_or_restart=False,
        limitations=['Moving live observation, not an admitted boundary.',
            'Saved artifact hashes checked; optimizer/RNG payload not deserialized or loaded.',
            'Full history retained remotely; no child text, sealed readout, or credentials exported.',
            'No source mutation, GPU model load, provider call, or historical journal change.'])
    destination = root / RELATIVE_OUTPUT / f'PREPARATION_{time.time_ns()}.json'
    with destination.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
    print(destination)
    for entry in output:
        saved = entry.get('saved', {})
        print(entry['label'], entry['status'], 'pid', entry.get('identity', {}).get('pid'),
              'sleep', saved.get('cycle'), 'optimizer_steps', saved.get('optimizer_steps'), entry.get('error', ''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    arguments = parser.parse_args()
    if arguments.remote:
        require(socket.gethostname() == HOST, 'node5_only')
        rows = json.load(sys.stdin)
        require(len(rows) == 8 and {row['physical'] for row in rows} == set(LABELS), 'exact_node5_scope')
        print(json.dumps([inspect_row(row) for row in rows], sort_keys=True, allow_nan=False))
    else:
        capture(Path.cwd())


if __name__ == '__main__':
    main()
