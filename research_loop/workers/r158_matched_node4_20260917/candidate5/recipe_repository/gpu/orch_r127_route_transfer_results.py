"""Read-only, fail-closed receipt verification for the frozen R127 producer."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from gpu import orch_r127_route_transfer_reduce as descriptive


SCHEMA = 'R127_CANONICAL_FRESH_TRANSFER_V1'
STAGES = ('SOURCE',) + descriptive.CONDITIONS
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SEED = 'd13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f'
HISTORICAL_RUNTIME = ('gpu/orch_guided_native.py', 'gpu/orch_route_parent_campaign_run.py',
    'organism_v6/orch_l2_guided.py', 'organism_v6/orch_full_rich.py',
    'organism_v6/orch_replication.py', 'organism_v6/experienced_event_two_hop.py')
digest = descriptive.document_sha256
UNBOUND = object()
ARTIFACT_ERRORS = (ValueError, KeyError, TypeError, IndexError, AttributeError, OSError)


class VerificationError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise VerificationError(code)


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def zero(value):
    return type(value) is int and value == 0


def nonnegative(value):
    return type(value) is int and value >= 0


def relative(root, name):
    require(isinstance(name, str) and bool(name), 'invalid_relative_path')
    part = Path(name)
    require(not part.is_absolute() and '..' not in part.parts and str(part) == name,
            'unsafe_relative_path')
    path = root / part
    require(path.resolve() == path and path.is_relative_to(root), 'symlink_or_path_escape')
    return path


def absolute(value):
    require(isinstance(value, str) and Path(value).is_absolute() and '..' not in Path(value).parts,
            'absolute_path_required')
    return Path(value).resolve()


class Reader:
    def __init__(self):
        self.files = {}

    def load(self, path, expected=UNBOUND, *, binary=False):
        path = Path(path)
        require(path.is_absolute() and path.resolve() == path and not path.is_symlink(),
                'symlink_or_path_escape')
        require(path.is_file(), 'missing_file')
        if expected is not UNBOUND:
            require(valid_hash(expected), 'invalid_file_hash')
        if binary:
            with path.open('rb') as stream:
                observed = hashlib.file_digest(stream, 'sha256').hexdigest()
            value = None
        else:
            data = path.read_bytes()
            observed = hashlib.sha256(data).hexdigest()
            try:
                value = json.loads(data, parse_constant=lambda unused: (_ for _ in ()).throw(ValueError()))
            except (ValueError, UnicodeError):
                raise VerificationError('invalid_json') from None
        require(expected is UNBOUND or observed == expected, 'file_hash_mismatch')
        require(str(path) not in self.files or self.files[str(path)] == observed, 'input_changed_during_read')
        self.files[str(path)] = observed
        return value

    def checked(self, reference, path):
        require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}, 'invalid_hashref')
        require(reference['path'] == str(path), 'hashref_path_mismatch')
        require(valid_hash(reference['sha256']), 'invalid_file_hash')
        return self.load(path, reference['sha256'])

    def ref(self, path):
        return dict(path=str(path), sha256=self.files[str(path)])

    def unchanged(self):
        for name, expected in list(self.files.items()):
            self.load(Path(name), expected, binary=True)


def inventory(folder, pattern):
    if not folder.exists():
        return []
    require(folder.is_dir() and folder.resolve() == folder, 'symlink_or_path_escape')
    paths = sorted(folder.glob(pattern))
    require(all(path.is_file() and path.resolve() == path for path in paths), 'invalid_artifact_path')
    return paths


def metadata(reader, plan_path):
    plan = reader.load(plan_path)
    require(plan['schema'] == SCHEMA and plan['wrapper'] == 'ovx' and plan['physical'] == 7,
            'plan_schema_or_device_mismatch')
    require(all(zero(plan[field]) for field in ('parent_calls', 'optimizer_steps', 'training_rows')),
            'plan_not_evaluation_only')
    require(plan['max_native_calls'] == 1472 and plan['response_cap'] == 512, 'plan_budget_mismatch')
    root, bundle, source_root = (absolute(plan[field]) for field in ('output', 'bundle', 'source_root'))
    require(root != bundle and not root.is_relative_to(bundle) and not bundle.is_relative_to(root),
            'overlapping_bundle_and_run')
    require(isinstance(plan['source_files'], dict) and bool(plan['source_files']), 'source_manifest_required')
    for name, expected in plan['source_files'].items():
        path = Path(name)
        require(path.is_absolute() and path.is_relative_to(source_root)
                and path.suffix in ('.py', '.sh'), 'unplanned_source_path')
        reader.load(path, expected, binary=True)
    exported = reader.load(relative(bundle, 'EXPORT.json'), plan['export_sha256'])
    require(exported['schema'] == SCHEMA and set(exported['conditions']) == set(descriptive.CONDITIONS),
            'export_conditions_mismatch')
    require(exported['selection'] == 'FIXED_C2_C4_C6_NOT_SELECTED_ON_TRANSFER_OUTCOMES',
            'checkpoint_selection_mismatch')
    for name in HISTORICAL_RUNTIME:
        path = relative(source_root, name)
        require(str(path) in plan['source_files'], 'historical_source_not_planned')
        reader.load(path, exported['original_source_files'][name], binary=True)
    require(str(relative(source_root, 'gpu/orch_r127_route_transfer.py')) in plan['source_files'],
            'producer_source_not_planned')
    expected_files = {'COHORT.json'}
    identities = {}
    for condition, entry in exported['conditions'].items():
        cycle = 0 if condition == 'SEED' else int(condition[-1])
        arm = 'SEED' if condition == 'SEED' else condition.rsplit('_', 1)[0]
        require(entry['cycle'] == cycle and entry['arm'] == arm and nonnegative(entry['updates']),
                'checkpoint_cycle_or_dose_mismatch')
        identity = entry['adapter']
        require(set(identity) == {'path', 'state_sha256', 'base_sha256', 'files'}
                and valid_hash(identity['state_sha256']) and identity['base_sha256'] == BASE,
                'checkpoint_identity_mismatch')
        require(identity['path'] == f'conditions/{condition}/adapter', 'checkpoint_path_mismatch')
        adapter_root = relative(bundle, identity['path'])
        names = []
        for filename, expected in identity['files']:
            require(isinstance(filename, str) and Path(filename).name == filename and valid_hash(expected),
                    'invalid_adapter_file')
            names.append(filename)
            name = identity['path'] + '/' + filename
            expected_files.add(name)
            require(exported['files'][name] == expected, 'checkpoint_export_hash_mismatch')
            reader.load(relative(adapter_root, filename), expected, binary=True)
        require(bool(names) and len(set(names)) == len(names)
                and {path.name for path in adapter_root.iterdir()} == set(names), 'adapter_manifest_mismatch')
        identities[condition] = dict(identity, path=str(adapter_root))
    require(identities['SEED']['state_sha256'] == SEED and zero(exported['conditions']['SEED']['updates']),
            'initial_adapter_mismatch')
    for arm in ('GUIDED', 'UNPARENTED'):
        history = exported['history'][arm]
        require(len(history) == 6, 'history_length_mismatch')
        initial = exported['conditions']['SEED']
        previous = dict(initial['adapter'], path=initial['original_adapter_path'])
        total = 0
        for cycle, entry in enumerate(history, 1):
            name = f'history/{arm}/C{cycle}.json'
            expected_files.add(name)
            require(entry['copied'] == name and entry['origin']['sha256'] == exported['files'][name],
                    'copied_history_binding_mismatch')
            receipt = reader.load(relative(bundle, name), exported['files'][name])
            require(receipt['status'] == 'COMPLETE' and receipt['arm'] == arm and receipt['cycle'] == cycle
                    and receipt['phase'] == 'sleep' and receipt['input_adapter'] == previous,
                    'historical_lineage_mismatch')
            require(nonnegative(receipt['updates']) and receipt['updates'] == entry['updates']
                    and receipt['output_adapter']['base_sha256'] == BASE, 'historical_dose_or_base_mismatch')
            total += receipt['updates']
            previous = receipt['output_adapter']
            if cycle in (2, 4, 6):
                selected = exported['conditions'][f'{arm}_C{cycle}']
                require(dict(selected['adapter'], path=selected['original_adapter_path']) == previous
                        and selected['updates'] == total and selected['original_sleep'] == entry['origin'],
                        'selected_checkpoint_lineage_mismatch')
    require(set(exported['files']) == expected_files, 'export_manifest_mismatch')
    cohort = reader.load(relative(bundle, 'COHORT.json'), exported['files']['COHORT.json'])
    require(exported['cohort_sha256'] == exported['files']['COHORT.json'], 'cohort_hash_mismatch')
    require(cohort['schema'] == SCHEMA and len(cohort['worlds']) == 16 and len(cohort['tasks']) == 32
            and cohort['trainingAllowed'] is False and cohort['final_tasks_used'] is False
            and cohort['parent_input_allowed'] is False, 'cohort_visibility_or_size_mismatch')
    masters = [world['master'] for world in cohort['worlds']]
    require(len(set(masters)) == 16, 'duplicate_world')
    keys = set()
    world_counts = [0] * 16
    for row in cohort['tasks']:
        index = row['world_index']
        require(type(index) is int and 0 <= index < 16 and row['world_id'] == masters[index]
                and row['trainingAllowed'] is False and row['split'] == 'DEV_DIAGNOSTIC', 'task_world_binding_mismatch')
        require(digest(row['task']) == row['task_sha256'] and valid_hash(row['initial_prompt_sha256']),
                'cohort_task_hash_mismatch')
        key = (row['world_id'], row['task_id'])
        require(key not in keys, 'duplicate_task')
        keys.add(key)
        world_counts[index] += 1
    require(world_counts == [2] * 16, 'two_tasks_per_world_required')
    return plan, exported, cohort, identities, root, bundle, source_root


def call_records(reader, root, condition, complete):
    folder = root / condition / 'calls'
    paths = inventory(folder, 'CALL_*.json')
    references = complete['calls']
    require(isinstance(references, list) and len(paths) == len(references)
            and 0 < len(paths) <= (128 if condition == 'SOURCE' else 192), 'call_manifest_count_mismatch')
    calls = []
    for path, reference in zip(paths, references):
        require(re.fullmatch(r'CALL_\d{5}\.json', path.name) is not None, 'invalid_call_filename')
        call = reader.checked(reference, path)
        require(call['condition'] == condition and call['status'] == 'COMPLETE', 'failed_or_wrong_condition_inference')
        require(isinstance(call.get('response'), dict) and call['response'].get('messages') == call['messages'],
                'call_response_prompt_mismatch')
        claim_path = root / 'claims' / path.name
        claim = reader.checked(call['claim'], claim_path)
        require(claim['condition'] == condition and claim['messages_sha256'] == digest(call['messages'])
                and claim['cap'] == 512 and claim['trainingAllowed'] is False and claim['no_retry'] is True,
                'call_claim_mismatch')
        calls.append(call)
    return calls, paths


def join_captures(captures, calls):
    require(len(captures) == len(calls), 'capture_call_count_mismatch')
    for capture, call in zip(captures, calls):
        require(capture['messages'] == call['messages'] and capture.get('response') == call['response'],
                'capture_call_full_response_mismatch')


def source_response_matches(recorded, capture):
    response = capture['response']
    require(capture['error'] is None, 'source_callback_failed')
    complete_generation = (isinstance(response, dict) and isinstance(response.get('raw'), str)
                           and response.get('terminal') is True and response.get('truncated') is False)
    return recorded == response if complete_generation else recorded is None


def source_store(reader, root, cohort, complete, calls):
    store_path = root / 'SOURCE/STORE.json'
    stored = reader.checked(complete['store'], store_path)
    require(isinstance(stored['store'], dict) and digest(stored['store']) == stored['source_store_sha256'],
            'source_store_content_hash_mismatch')
    require(stored['trainingAllowed'] is False and stored['worlds'] == 16 and stored['offered_events'] == 64,
            'source_store_metadata_mismatch')
    paths = inventory(root / 'SOURCE', 'WORLD_*.json')
    require([path.name for path in paths] == [f'WORLD_{index:02d}.json' for index in range(16)],
            'source_world_panel_mismatch')
    reconstructed, captures, complete_worlds = {}, [], 0
    for path, world in zip(paths, cohort['worlds']):
        collection = reader.load(path)
        payload = {name: value for name, value in collection.items() if name != 'collection_sha256'}
        require(digest(payload) == collection['collection_sha256'] and collection['world'] == world
                and collection['world_sha256'] == digest(world), 'source_collection_hash_mismatch')
        require(zero(collection['fits']) and collection['parent_present'] is False
                and collection['model_calls'] == len(collection['captures']), 'source_collection_state_mismatch')
        records = collection['records']
        require(len(records) == len(world['edges']) == 4 and collection['event_denominator'] == 4,
                'source_record_panel_mismatch')
        accepted = 0
        for index, (record, edge) in enumerate(zip(records, world['edges'])):
            require(record['edge'] == edge and type(record['accepted']) is bool, 'source_edge_binding_mismatch')
            own = [capture for capture in collection['captures'] if capture['record_index'] == index]
            require([capture['phase'] for capture in own] in (['action'], ['action', 'event']),
                    'source_capture_phase_mismatch')
            require(source_response_matches(record['action'], own[0]), 'source_action_response_mismatch')
            if len(own) == 2:
                require(source_response_matches(record['event'], own[1]), 'source_event_response_mismatch')
            else:
                require(record['event'] is None, 'uncaptured_source_event')
            if record['accepted']:
                require(len(own) == 2 and record['error'] is None and isinstance(record['event']['raw'], str),
                        'accepted_source_event_missing')
                raw = record['event']['raw']
                require(hashlib.sha256(raw.encode()).hexdigest() == record['source_raw_sha256'],
                        'source_raw_hash_mismatch')
                require(edge['event'] not in reconstructed, 'duplicate_source_event')
                reconstructed[edge['event']] = raw
                accepted += 1
        require(type(collection['ready']) is bool and collection['ready'] == (accepted == 4)
                and collection['accepted_events'] == accepted, 'source_ready_count_mismatch')
        complete_worlds += int(collection['ready'])
        captures.extend(collection['captures'])
    join_captures(captures, calls)
    require(reconstructed == stored['store'] and stored['accepted_events'] == len(reconstructed)
            and stored['complete_worlds'] == complete_worlds, 'source_store_reconstruction_mismatch')
    return stored


def verified_stage(reader, plan_path, plan, root, cohort, identity, condition, source):
    folder = root / condition
    loaded = reader.load(folder / 'LOADED.json')
    require(loaded['condition'] == condition and loaded['adapter'] == identity and loaded['parent_free'] is True
            and loaded['fresh_process'] is True and zero(loaded['optimizer_steps']), 'loaded_identity_or_state_mismatch')
    process = loaded['process']
    require(isinstance(process, list) and len(process) == 3 and isinstance(process[0], str)
            and type(process[1]) is int and process[1] > 0 and nonnegative(process[2]), 'invalid_process_identity')
    binding = reader.load(folder / 'BINDING.json')
    require(binding['adapter'] == identity and binding['plan_sha256'] == reader.files[str(plan_path)]
            and binding['parent_present'] is False and binding['fresh_process'] is True
            and binding['phase'] == 'sealed_readout' and zero(binding['cycle']), 'stage_binding_mismatch')
    launch = reader.load(root / f'{condition}_LAUNCH.json')
    require(launch['condition'] == condition and launch['pid'] == process[1], 'launch_process_mismatch')
    exited = reader.load(root / f'{condition}_EXIT.json')
    require(exited['condition'] == condition and zero(exited['returncode']) and exited['complete'] is True
            and exited['no_retry'] is True, 'failed_or_incomplete_exit')
    complete = reader.load(folder / 'COMPLETE.json')
    require(complete['status'] == 'COMPLETE' and complete['condition'] == condition and complete['adapter'] == identity
            and complete['unchanged'] is True
            and all(zero(complete[field]) for field in ('parent_calls', 'optimizer_steps', 'training_rows')),
            'complete_identity_or_state_mismatch')
    calls, call_paths = call_records(reader, root, condition, complete)
    if condition == 'SOURCE':
        require(complete['episodes'] == [] and not inventory(folder, 'EPISODE_*.json'), 'source_has_eval_episodes')
        stored = source_store(reader, root, cohort, complete, calls)
        episodes = []
    else:
        require(source is not None, 'source_not_verified')
        reader.checked(complete['store'], root / 'SOURCE/STORE.json')
        require(complete['store'] == source['reference'], 'condition_store_binding_mismatch')
        paths = inventory(folder, 'EPISODE_*.json')
        require([path.name for path in paths] == [f'EPISODE_{index:02d}.json' for index in range(32)]
                and len(complete['episodes']) == 32, 'episode_panel_incomplete')
        episodes, captures = [], []
        for path, reference, row in zip(paths, complete['episodes'], cohort['tasks']):
            episode = reader.checked(reference, path)
            require(all(episode[field] == row[field] for field in
                        ('world_id', 'task_id', 'task', 'task_sha256', 'initial_prompt_sha256')),
                    'episode_task_binding_mismatch')
            require(episode['condition'] == condition and episode['checkpoint_state_sha256'] == identity['state_sha256']
                    and episode['source_store_sha256'] == source['stored']['source_store_sha256']
                    and episode['parent_messages'] == [] and episode['trainingAllowed'] is False,
                    'episode_evaluation_binding_mismatch')
            require(type(episode['actor_calls']) is int and episode['actor_calls'] == len(episode['captures'])
                    and 1 <= episode['actor_calls'] <= 6, 'episode_trace_incomplete')
            require(digest(episode['captures'][0]['messages']) == row['initial_prompt_sha256'],
                    'episode_initial_prompt_mismatch')
            captures.extend(episode['captures'])
            episodes.append(episode)
        join_captures(captures, calls)
        stored = None
    evidence = dict(status='VERIFIED', calls=len(calls), episodes=len(episodes),
        checkpoint_state_sha256=identity['state_sha256'],
        complete=reader.ref(folder / 'COMPLETE.json'), loaded=reader.ref(folder / 'LOADED.json'),
        exit=reader.ref(root / f'{condition}_EXIT.json'),
        call_refs_sha256=digest(complete['calls']), episode_refs_sha256=digest(complete['episodes']))
    return evidence, episodes, stored, tuple(process), call_paths


def safe_error(error):
    return str(error) if isinstance(error, VerificationError) else 'malformed_or_unreadable_artifact'


def compact_analysis(value):
    result = {key: item for key, item in value.items() if key != 'episode_metrics'}
    result['conditions'] = {condition: {key: item for key, item in entry.items() if key != 'per_world'}
                            for condition, entry in value['conditions'].items()}
    for condition, entry in result['conditions'].items():
        coverage = {}
        for row in value['episode_metrics']:
            if row['condition'] == condition:
                for field, counts in row['coverage'].items():
                    totals = coverage.setdefault(field, dict(observed=0, missing=0, total=0))
                    for key in totals:
                        totals[key] += counts[key]
        entry['call_coverage'] = coverage
    result['comparisons'] = {name: dict(left=entry['left'], right=entry['right'],
        metrics={metric: {key: item for key, item in summary.items() if key != 'world_differences'}
                 for metric, summary in entry['metrics'].items()}) for name, entry in value['comparisons'].items()}
    return result


def reduce(plan_path, output, *, bootstrap_samples=2000, seed=0):
    """Write a new compact snapshot; incomplete or invalid evidence never yields contrasts."""
    reader = Reader()
    plan_path = absolute(str(plan_path))
    result = dict(schema='R127_VERIFIED_RESULTS_V1', status='INCOMPLETE', source_ready=False,
                  store_size=None, stages={condition: dict(status='NOT_STARTED') for condition in STAGES},
                  analysis=None, errors=[])
    root = bundle = source_root = None
    try:
        plan, exported, cohort, identities, root, bundle, source_root = metadata(reader, plan_path)
        result['inputs'] = dict(plan=reader.ref(plan_path), export=reader.ref(bundle / 'EXPORT.json'),
                                cohort=reader.ref(bundle / 'COHORT.json'), root=str(root))
        start = reader.load(root / 'START.json')
        reader.checked(start['plan'], plan_path)
        groups, processes, all_calls, source = {}, [], [], None
        for condition in STAGES:
            folder = root / condition
            state = result['stages'][condition]
            try:
                state.update(calls_seen=len(inventory(folder / 'calls', 'CALL_*.json')),
                             episodes_seen=len(inventory(folder, 'EPISODE_*.json')))
                if not folder.exists() and not (root / f'{condition}_EXIT.json').exists():
                    continue
                state['status'] = 'INCOMPLETE'
                identity = identities['SEED' if condition == 'SOURCE' else condition]
                evidence, episodes, stored, process, calls = verified_stage(
                    reader, plan_path, plan, root, cohort, identity, condition, source)
                require(process not in processes and process[1] != start['pid'], 'evaluation_process_reused')
                processes.append(process)
                all_calls.extend(calls)
                result['stages'][condition] = evidence
                if condition == 'SOURCE':
                    source = dict(stored=stored, reference=reader.ref(root / 'SOURCE/STORE.json'))
                    result.update(source_ready=True, store_size=len(stored['store']),
                        source=dict(source['reference'], source_store_sha256=stored['source_store_sha256'],
                            worlds=stored['worlds'], accepted_events=stored['accepted_events'],
                            offered_events=stored['offered_events'], complete_worlds=stored['complete_worlds']))
                else:
                    groups[condition] = episodes
            except ARTIFACT_ERRORS as error:
                state.update(status='INCOMPLETE', error=safe_error(error))
        if all(entry['status'] == 'VERIFIED' for entry in result['stages'].values()):
            claims = inventory(root / 'claims', 'CALL_*.json')
            require(len(claims) <= 1472 and [path.name for path in claims]
                    == [f'CALL_{index:05d}.json' for index in range(1, len(claims) + 1)], 'claim_history_not_contiguous')
            require(len(all_calls) == len(claims) and {path.name for path in all_calls} == {path.name for path in claims},
                    'uncharged_or_unjoined_calls')
            terminal_path = root / 'TERMINAL.json'
            if terminal_path.exists():
                terminal = reader.load(terminal_path)
                require(terminal['status'] == 'COMPLETE' and all(zero(terminal[field]) for field in
                        ('parent_calls', 'optimizer_steps', 'training_rows')), 'terminal_incomplete')
                exits = [reader.load(root / f'{condition}_EXIT.json') for condition in STAGES]
                require(terminal['results'] == exits, 'terminal_exit_mismatch')
            normalized = dict(evaluation_split='fresh_public_held', prospective=True, world_count=16,
                initial_state_sha256=SEED, source_store_sha256=source['stored']['source_store_sha256'],
                source_ready=True, store_size=len(source['stored']['store']), tasks=cohort['tasks'],
                conditions={condition: dict(checkpoint_state_sha256=entry['adapter']['state_sha256'],
                    cycle=entry['cycle'], updates=entry['updates']) for condition, entry in exported['conditions'].items()})
            analysis = descriptive.compare(normalized, groups, bootstrap_samples=bootstrap_samples, seed=seed)
            reader.unchanged()
            result.update(status='COMPLETE', analysis=compact_analysis(analysis))
    except ARTIFACT_ERRORS as error:
        result['errors'].append(safe_error(error))
    result['verified_file_count'] = len(reader.files)
    result['verified_files_sha256'] = digest(reader.files)
    if output is not None:
        output = Path(output).absolute()
        require(output.resolve() == output and str(output) not in reader.files, 'output_overlaps_input')
        require(all(location is None or not output.is_relative_to(location) for location in (bundle, source_root)),
                'output_overlaps_frozen_bundle_or_source')
        if root is not None:
            require(not any(output.is_relative_to(root / name) for name in STAGES + ('claims',)),
                    'output_overlaps_producer_artifacts')
        with output.open('x') as stream:
            json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = reduce(args.plan, args.output)
    print(json.dumps(dict(status=result['status'], output=str(args.output)), sort_keys=True))


if __name__ == '__main__':
    main()
