"""Prospective, evaluation-only public-evidence route sensitivity diagnostic."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
from itertools import permutations
import json
import os
from pathlib import Path
import re
import time

from organism_v6 import orch_full_rich as rich
from organism_v6 import orch_route_parent_campaign as canonical
from gpu.orch_r127_route_transfer_reduce import document_sha256 as digest, paired_summary


SCHEMA = 'R130_PUBLIC_EVIDENCE_DIAGNOSTIC_V1'
PREFIX = 'ORCH-ROUTE-PARENT-20260915-R130-EVIDENCE-'
CONDITIONS = ('SEED', 'GUIDED_C6', 'UNPARENTED_C6')
VARIANTS = ('A', 'B')
PAIR_COUNT = 16
MAX_NEW_TOKENS = 512
CONTEXT_LIMIT = 8192
CALLS_PER_CONDITION = PAIR_COUNT * 2
TOTAL_CALLS = CALLS_PER_CONDITION * len(CONDITIONS)
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SEED_SHA = 'd13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f'
PROVENANCE = 'FRESH_ENVIRONMENT_VERIFIED_ORACLE_NOT_CHILD_MEMORY'
SYSTEM = (
    'Use the public route task and the supplied environment-verified EVENT records. '
    'Identifiers are opaque and case-sensitive. Each offered port leads to a different '
    'one of the two intermediate nodes appearing as AT in the downstream records. '
    'Each intermediate node has exactly one outgoing route; exactly one two-route path '
    'reaches GOAL. The unshown root transition obeys this same bijection. '
    'All records needed for this decision are already supplied. Choose the first route. '
    'Output exactly ROUTE <listedport>, optionally followed by a newline. '
    'No READ, explanation, simulated feedback, or additional action.'
)
DECODER = dict(max_new_tokens=MAX_NEW_TOKENS, context_limit=CONTEXT_LIMIT,
               do_sample=False, num_beams=1, repetition_penalty=1.0)
SOURCE_CLOSURE = ('gpu/orch_r130_route_evidence_probe.py', 'gpu/orch_r127_route_transfer_reduce.py',
    'gpu/orch_route_parent_campaign_run.py', 'gpu/orch_guided_native.py',
    'gpu/astra_experienced_event_microloop.py', 'organism_v6/orch_guided_bridge.py',
    'organism_v6/orch_full_rich.py', 'organism_v6/orch_replication.py',
    'organism_v6/orch_route_parent_campaign.py', 'organism_v6/experienced_event_two_hop.py',
    'organism_v6/experienced_event_microloop.py', 'organism_v6/experienced_event_read_route.py',
    'organism_v6/pcfl_vertical_dev.py', 'gpu/astra_portable_actor_bundle.py',
    'gpu/orch_l2_shared_run.py', 'gpu/orch_oracle_repair_guard.py',
    'gpu/astra_experienced_event_cue_sleep.py', 'gpu/astra_reader_audit_lesson_train.py',
    'gpu/astra_pchain2_native.py', 'organism_v6/pcfl_vertical_train.py',
    'organism_v6/orch_l2_guided.py', 'organism_v6/orch_l2_shared.py',
    'organism_v6/experienced_event_goal_replay_layout.py')
HISTORICAL_ENGINE_CONTRACTS = tuple(name for name in SOURCE_CLOSURE if name not in (
    'gpu/orch_r130_route_evidence_probe.py', 'gpu/orch_r127_route_transfer_reduce.py'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
            and Path(value['path']).is_absolute() and valid_hash(value['sha256']), 'exact_input_reference_required')
    require(sha(value['path']) == value['sha256'], 'input_file_hash_mismatch')
    return read(value['path'])


def write_new(path, value):
    path = Path(path)
    require(re.fullmatch(r'(MANIFEST|LOADED|BINDING|COMPLETE|FAILED|CLAIM_\d{3}|CALL_\d{3})\.json', path.name)
            is not None, 'evaluation_artifact_only_no_TRAIN_or_adapter_writes')
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def identifiers(world):
    return {value for edge in world['edges'] for value in edge.values()}


def validate_world(world):
    require(world['master'].startswith(PREFIX) and len(world['nodes']) == 5
            and len(set(world['nodes'])) == 5 and len(world['edges']) == 4, 'fresh_two_hop_world_required')
    for node in world['nodes']:
        require(re.fullmatch(r'N_[A-Z2-7]{10}', node) is not None, 'opaque_node_required')
    for field, prefix in (('port', 'P'), ('event', 'E'), ('receipt', 'R')):
        values = [edge[field] for edge in world['edges']]
        require(len(set(values)) == 4 and all(re.fullmatch(prefix + r'_[A-Z2-7]{10}', value)
                is not None for value in values), 'unique_opaque_edge_identifiers_required')
    root, middles, goals = world['nodes'][0], world['nodes'][1:3], world['nodes'][3:]
    roots = [edge for edge in world['edges'] if edge['node'] == root]
    require(len(roots) == 2 and {edge['outcome'] for edge in roots} == set(middles),
            'root_bijection_required')
    downstream = [edge for edge in world['edges'] if edge['node'] in middles]
    require(len(downstream) == 2 and {edge['node'] for edge in downstream} == set(middles)
            and {edge['outcome'] for edge in downstream} == set(goals), 'distinct_two_hop_goals_required')
    return world


def transition(world, current, port):
    matches = [edge for edge in world['edges'] if edge['node'] == current and edge['port'] == port]
    require(len(matches) == 1, 'one_legal_environment_transition_required')
    edge = matches[0]
    return dict(source=current, port=port, destination=edge['outcome'], receipt=edge['receipt'])


def gold_action(world, task):
    validate_world(world)
    require(set(task) == {'node', 'goal', 'ports', 'events'} and task['node'] == world['nodes'][0]
            and task['goal'] in world['nodes'][3:] and len(task['ports']) == 2
            and set(task['ports']) == {edge['port'] for edge in world['edges'] if edge['node'] == task['node']},
            'matched_public_task_required')
    winning = []
    for port in task['ports']:
        first = transition(world, task['node'], port)
        onward = [edge for edge in world['edges'] if edge['node'] == first['destination']]
        require(len(onward) == 1, 'unique_second_route_required')
        second = transition(world, first['destination'], onward[0]['port'])
        if second['destination'] == task['goal']:
            record = dict(routes=[first, second], correct=True)
            require(rich.readout.score(world, task, record), 'canonical_route_scorer_disagrees')
            winning.append(port)
    require(len(winning) == 1, 'unique_gold_action_required')
    return 'ROUTE ' + winning[0]


def evidence_record(world, edge):
    observed = transition(world, edge['node'], edge['port'])
    raw = rich.hop.micro._event(edge)
    return dict(event=edge['event'], raw=raw, receipt=rich.hop.micro.RECEIPT_WIRE.format(**observed),
        world_sha256=digest(world), available=True, provenance=PROVENANCE, trainingAllowed=False)


def validate_evidence(world, task, records):
    require(isinstance(records, list) and len(records) == 3 and len(task['events']) == 3,
            'exact_three_supplied_records_required')
    require([record['event'] for record in records] == task['events'] and len(set(task['events'])) == 3,
            'evidence_address_or_order_mismatch')
    parsed = []
    for record in records:
        require(record['available'] is True and record['trainingAllowed'] is False
                and record['provenance'] == PROVENANCE and record['world_sha256'] == digest(world),
                'unavailable_or_mismatched_evidence')
        matches = [edge for edge in world['edges'] if edge['event'] == record['event']]
        require(len(matches) == 1, 'evidence_event_not_in_world')
        edge = matches[0]
        expected = dict(event=edge['event'], **transition(world, edge['node'], edge['port']))
        require(rich.hop.micro.parse_event_line(record['raw']) == expected,
                'evidence_not_environment_grounded')
        require(record['receipt'] == rich.hop.micro.RECEIPT_WIRE.format(**transition(world, edge['node'], edge['port'])),
                'receipt_not_environment_grounded')
        parsed.append(expected)
    roots = [entry for entry in parsed if entry['source'] == task['node']]
    downstream = [entry for entry in parsed if entry['source'] != task['node']]
    require(len(roots) == 1 and len(downstream) == 2
            and {entry['source'] for entry in downstream} == set(world['nodes'][1:3]),
            'one_anchor_and_two_downstream_records_required')
    return parsed


def public_gold_actions(task, parsed):
    roots = [entry for entry in parsed if entry['source'] == task['node']]
    downstream = {entry['source']: entry['destination'] for entry in parsed if entry['source'] != task['node']}
    require(len(roots) == 1 and len(downstream) == 2, 'public_packet_ambiguous')
    possible = set()
    for destinations in permutations(downstream):
        assignment = dict(zip(task['ports'], destinations))
        if assignment.get(roots[0]['port']) == roots[0]['destination']:
            possible.update('ROUTE ' + port for port, middle in assignment.items()
                            if downstream[middle] == task['goal'])
    require(len(possible) == 1, 'public_evidence_does_not_determine_action')
    return possible


def render(task, records):
    content = rich.readout.display(task['node'], task, list(task['ports']))
    content += '\n\nENVIRONMENT-VERIFIED EVENT RECORDS\n' + ''.join(record['raw'] for record in records)
    return [dict(role='system', content=SYSTEM), dict(role='user', content=content)]


def validate_pair(pair):
    require(pair['schema'] == SCHEMA and pair['trainingAllowed'] is False and pair['parent_present'] is False
            and set(pair['worlds']) == set(VARIANTS) and set(pair['records']) == set(VARIANTS),
            'evaluation_only_pair_required')
    require(pair['order'] in (['A', 'B'], ['B', 'A']), 'pair_order_required')
    parsed, actions, messages = {}, {}, {}
    for variant in VARIANTS:
        world = validate_world(pair['worlds'][variant])
        require(world['master'] == pair['pair_id'], 'pair_world_identity_mismatch')
        parsed[variant] = validate_evidence(world, pair['task'], pair['records'][variant])
        actions[variant] = gold_action(world, pair['task'])
        require(public_gold_actions(pair['task'], parsed[variant]) == {actions[variant]},
                'public_gold_and_environment_disagree')
        messages[variant] = render(pair['task'], pair['records'][variant])
    differences = [(left, right) for left, right in zip(parsed['A'], parsed['B']) if left != right]
    require(len(differences) == 1 and {field for field in differences[0][0]
            if differences[0][0][field] != differences[0][1][field]} == {'destination'}
            and differences[0][0]['source'] == pair['task']['node'], 'one_action_relevant_GOT_value_required')
    left_tokens, right_tokens = (messages[variant][1]['content'].split() for variant in VARIANTS)
    require(len(left_tokens) == len(right_tokens)
            and sum(left != right for left, right in zip(left_tokens, right_tokens)) == 1,
            'exactly_one_public_value_may_change')
    require(actions['A'] != actions['B'], 'intervention_must_change_gold_action')
    left_world, right_world = pair['worlds']['A'], pair['worlds']['B']
    left_fixed, right_fixed = deepcopy(left_world), deepcopy(right_world)
    for world in (left_fixed, right_fixed):
        for edge in world['edges']:
            if edge['node'] == pair['task']['node']:
                edge['outcome'] = None
    require(left_fixed == right_fixed, 'only_complemented_root_destination_swap_allowed')
    return dict(actions=actions, messages=messages)


def build_pairs(exclusions):
    require(isinstance(exclusions, list) and all(isinstance(value, str) for value in exclusions)
            and len(exclusions) == len(set(exclusions)), 'explicit_unique_exclusion_ids_required')
    seen, pairs = set(exclusions), []
    for index in range(PAIR_COUNT):
        master = PREFIX + f'W{index:02d}'
        original = canonical.runtime(master)['build_world'](master)
        require(not identifiers(original).intersection(seen), 'prospective_namespace_collision')
        seen.update(identifiers(original))
        worlds = {variant: deepcopy(original) for variant in VARIANTS}
        swapped = 'A' if (index // 4) % 2 else 'B'
        worlds[swapped]['edges'][0]['outcome'], worlds[swapped]['edges'][1]['outcome'] = (
            original['edges'][1]['outcome'], original['edges'][0]['outcome'])
        event_indexes = [0, 2, 3]
        rotation = index % 3
        event_indexes = event_indexes[rotation:] + event_indexes[:rotation]
        ports = [edge['port'] for edge in original['edges'][:2]]
        if (index // 2) % 2:
            ports.reverse()
        task = dict(node=original['nodes'][0], goal=original['nodes'][3 + index % 2], ports=ports,
                    events=[original['edges'][ordinal]['event'] for ordinal in event_indexes])
        pair = dict(schema=SCHEMA, pair_id=master, task=task, worlds=worlds,
            records={variant: [evidence_record(worlds[variant], worlds[variant]['edges'][ordinal])
                              for ordinal in event_indexes] for variant in VARIANTS},
            order=['A', 'B'] if (index // 8) % 2 == 0 else ['B', 'A'],
            trainingAllowed=False, parent_present=False)
        validate_pair(pair)
        pairs.append(pair)
    return pairs


def selected_checkpoints(exported):
    require(exported['schema'] == 'R127_CANONICAL_FRESH_TRANSFER_V1'
            and exported['selection'] == 'FIXED_C2_C4_C6_NOT_SELECTED_ON_TRANSFER_OUTCOMES', 'fixed_R127_export_required')
    selected = {}
    for condition in CONDITIONS:
        entry = deepcopy(exported['conditions'][condition])
        require(entry['cycle'] == (0 if condition == 'SEED' else 6)
                and entry['arm'] == ('SEED' if condition == 'SEED' else condition.split('_')[0])
                and type(entry['updates']) is int and entry['updates'] >= 0, 'fixed_terminal_checkpoint_required')
        adapter = entry['adapter']
        require(adapter['base_sha256'] == BASE_SHA and valid_hash(adapter['state_sha256'])
                and bool(adapter['files']), 'frozen_Qwen_plus_LoRA_required')
        require(adapter['path'] == f'conditions/{condition}/adapter', 'export_adapter_path_mismatch')
        if condition == 'SEED':
            require(adapter['state_sha256'] == SEED_SHA and entry['updates'] == 0, 'fixed_seed_required')
        for filename, expected in adapter['files']:
            require(Path(filename).name == filename and valid_hash(expected)
                    and exported['files'][adapter['path'] + '/' + filename] == expected, 'adapter_file_binding_mismatch')
        selected[condition] = dict(cycle=entry['cycle'], updates=entry['updates'], adapter=adapter)
    return selected


def make_manifest(exported, exclusions):
    manifest = dict(schema=SCHEMA, conditions=selected_checkpoints(exported), pairs=build_pairs(exclusions),
        exclusions_sha256=digest(sorted(exclusions)), decoder=deepcopy(DECODER),
        max_native_calls=TOTAL_CALLS, calls_per_condition=CALLS_PER_CONDITION,
        source_native_calls=0, trainingAllowed=False, optimizer_steps=0, training_rows=0, parent_calls=0,
        final_tasks_used=False, selection='FIXED_TERMINAL_C6_NOT_BEST_R127_SCORE',
        evidence_provenance=PROVENANCE, scope='SMALL_L1_PAPER_MECHANISM_DIAGNOSTIC_NOT_NEW_L2_ARCHITECTURE')
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest):
    require(manifest['schema'] == SCHEMA and set(manifest['conditions']) == set(CONDITIONS)
            and manifest['trainingAllowed'] is False and manifest['final_tasks_used'] is False,
            'evaluation_only_manifest_required')
    require(all(type(manifest[field]) is int and manifest[field] == 0 for field in
                ('optimizer_steps', 'training_rows', 'parent_calls', 'source_native_calls')), 'no_training_or_parent_calls')
    require(manifest['decoder'] == DECODER and manifest['max_native_calls'] == TOTAL_CALLS
            and manifest['calls_per_condition'] == CALLS_PER_CONDITION, 'matched_decoder_and_budget_required')
    require(manifest['selection'] == 'FIXED_TERMINAL_C6_NOT_BEST_R127_SCORE'
            and manifest['evidence_provenance'] == PROVENANCE, 'prospective_diagnostic_contract_required')
    require(len(manifest['pairs']) == PAIR_COUNT and len({pair['pair_id'] for pair in manifest['pairs']}) == PAIR_COUNT,
            'complete_sixteen_pair_panel_required')
    for condition, entry in manifest['conditions'].items():
        require(type(entry['cycle']) is int and entry['cycle'] == (0 if condition == 'SEED' else 6)
                and type(entry['updates']) is int and entry['updates'] >= 0
                and entry['adapter']['base_sha256'] == BASE_SHA and valid_hash(entry['adapter']['state_sha256'])
                and entry['adapter']['path'] == f'conditions/{condition}/adapter'
                and isinstance(entry['adapter']['files'], list) and bool(entry['adapter']['files']),
                'fixed_checkpoint_identity_required')
        names = []
        for filename, expected in entry['adapter']['files']:
            require(isinstance(filename, str) and filename not in ('', '.', '..')
                    and Path(filename).name == filename and valid_hash(expected), 'adapter_file_binding_mismatch')
            names.append(filename)
        require(len(names) == len(set(names)), 'duplicate_adapter_file')
    require(manifest['conditions']['SEED']['adapter']['state_sha256'] == SEED_SHA
            and manifest['conditions']['SEED']['updates'] == 0, 'fixed_seed_required')
    seen = set()
    for pair in manifest['pairs']:
        validate_pair(pair)
        current = identifiers(pair['worlds']['A'])
        require(not current.intersection(seen), 'cross_pair_identifier_collision')
        seen.update(current)


def prepare(export_path, exclusions_path, output):
    output = Path(output)
    manifest = make_manifest(read(export_path), read(exclusions_path))
    manifest.update(source_export=reference(export_path), exclusions=reference(exclusions_path))
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'MANIFEST.json', manifest)
    return manifest


def planned_calls(manifest):
    return [(pair, variant) for pair in manifest['pairs'] for variant in pair['order']]


def evaluate_condition(manifest, condition, generate, emit):
    validate_manifest(manifest)
    require(condition in CONDITIONS, 'fixed_condition_required')
    records = []
    for ordinal, (pair, variant) in enumerate(planned_calls(manifest), 1):
        messages = render(pair['task'], pair['records'][variant])
        record = dict(schema=SCHEMA, condition=condition, pair_id=pair['pair_id'], variant=variant,
            manifest_sha256=digest(manifest), checkpoint_state_sha256=manifest['conditions'][condition]['adapter']['state_sha256'],
            messages=deepcopy(messages), messages_sha256=digest(messages), decoder=deepcopy(DECODER),
            trainingAllowed=False, parent_present=False, logical_call=ordinal, status='CHARGED_NO_RETRY')
        emit(f'CLAIM_{ordinal:03d}.json', record)
        try:
            response = generate(deepcopy(messages), max_new_tokens=MAX_NEW_TOKENS)
            record['response'] = deepcopy(response)
            require(isinstance(response, dict) and response.get('messages') == messages, 'native_response_prompt_mismatch')
            record['status'] = 'COMPLETE'
        except Exception as error:
            record.update(status='FAILED', error_type=type(error).__name__)
            emit(f'CALL_{ordinal:03d}.json', record)
            raise
        emit(f'CALL_{ordinal:03d}.json', record)
        records.append(record)
    return records


def response_action(response, task):
    if response.get('terminal') is not True or response.get('truncated') is not False:
        return None
    try:
        parsed = rich.hop.commands.parse_command(response.get('raw'))
    except (TypeError, ValueError):
        return None
    return 'ROUTE ' + parsed['value'] if parsed['kind'] == 'ROUTE' and parsed['value'] in task['ports'] else None


def reduce_records(manifest, groups, *, bootstrap_samples=2000, seed=0):
    validate_manifest(manifest)
    require(set(groups).issubset(CONDITIONS), 'unexpected_condition')
    require(type(bootstrap_samples) is int and bootstrap_samples >= 100 and type(seed) is int, 'bootstrap_settings_required')
    result = dict(schema=SCHEMA, status='INCOMPLETE', comparisons=None, conditions={},
        claim_scope='WITHIN_CHECKPOINT_CONTENT_ALIGNED_FIRST_ACTION_ONLY_NOT_LATENT_METACOGNITION',
        causal_parenting_claim=False, paper_scope=manifest['scope'], evidence_provenance=PROVENANCE)
    for condition in CONDITIONS:
        records = groups.get(condition, [])
        result['conditions'][condition] = dict(status='INCOMPLETE', calls=len(records))
        if len(records) != CALLS_PER_CONDITION or any(record.get('status') != 'COMPLETE' for record in records):
            continue
        per_pair = {}
        valid, correct, truncated, prompt_tokens, generated_tokens = 0, 0, [], [], []
        for ordinal, (record, (pair, variant)) in enumerate(zip(records, planned_calls(manifest)), 1):
            messages = render(pair['task'], pair['records'][variant])
            require(record['condition'] == condition and record['pair_id'] == pair['pair_id']
                    and record['variant'] == variant and record['logical_call'] == ordinal
                    and record['manifest_sha256'] == digest(manifest)
                    and record['checkpoint_state_sha256'] == manifest['conditions'][condition]['adapter']['state_sha256']
                    and record['messages'] == messages and record['messages_sha256'] == digest(messages)
                    and record['response']['messages'] == messages and record['decoder'] == DECODER
                    and record['trainingAllowed'] is False and record['parent_present'] is False,
                    'record_binding_or_pair_mismatch')
            response = record['response']
            action = response_action(response, pair['task'])
            success = action == gold_action(pair['worlds'][variant], pair['task'])
            valid += int(action is not None)
            correct += int(success)
            per_pair.setdefault(pair['pair_id'], []).append(dict(action=action, correct=success))
            prompt_tokens.append(response.get('prompt_tokens'))
            generated_tokens.append(len(response['token_ids']) if isinstance(response.get('token_ids'), list) else None)
            truncated.append(int(response['truncated']) if type(response.get('truncated')) is bool else None)
        metrics = {}
        for pair_id, entries in per_pair.items():
            both_valid = all(entry['action'] is not None for entry in entries)
            metrics[pair_id] = dict(both_correct=int(all(entry['correct'] for entry in entries)),
                first_action_accuracy=sum(entry['correct'] for entry in entries) / 2,
                valid_action_switch=int(both_valid and entries[0]['action'] != entries[1]['action']),
                both_wrong=int(both_valid and not any(entry['correct'] for entry in entries)),
                any_invalid=int(not both_valid))
        result['conditions'][condition] = dict(status='COMPLETE', calls=len(records), pairs=PAIR_COUNT,
            checkpoint=deepcopy(manifest['conditions'][condition]), valid_actions=valid, correct_first_actions=correct,
            pair_counts={metric: sum(values[metric] for values in metrics.values())
                         for metric in ('both_correct', 'valid_action_switch', 'both_wrong', 'any_invalid')},
            per_pair=metrics, telemetry={name: dict(total=None if any(value is None for value in values) else sum(values),
                observed_calls=sum(value is not None for value in values), missing_calls=sum(value is None for value in values))
                for name, values in (('prompt_tokens', prompt_tokens), ('generated_tokens_including_eos', generated_tokens),
                                     ('truncated_responses', truncated))})
    if not all(entry['status'] == 'COMPLETE' for entry in result['conditions'].values()):
        return result
    result.update(status='COMPLETE', comparisons={})
    for left, right in (('GUIDED_C6', 'UNPARENTED_C6'), ('GUIDED_C6', 'SEED'), ('UNPARENTED_C6', 'SEED')):
        result['comparisons'][left + '_minus_' + right] = {}
        for metric in ('both_correct', 'first_action_accuracy', 'valid_action_switch'):
            differences = {pair_id: values[metric] - result['conditions'][right]['per_pair'][pair_id][metric]
                for pair_id, values in result['conditions'][left]['per_pair'].items()}
            result['comparisons'][left + '_minus_' + right][metric] = paired_summary(
                differences, PAIR_COUNT, bootstrap_samples, seed)
    result['uncertainty'] = 'Paired-world, pointwise descriptive bootstrap; fixed lineages/oracle packet; no multiplicity adjustment.'
    return result


def validate_source_files(source_root, source_files, historical_files):
    source_root = Path(source_root).resolve()
    require(isinstance(source_files, dict) and set(SOURCE_CLOSURE).issubset(source_files),
            'source_manifest_minimum_closure_required')
    require(isinstance(historical_files, dict), 'R127_historical_engine_manifest_required')
    for name, expected in source_files.items():
        require(isinstance(name, str) and bool(name), 'relative_source_path_required')
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts
                and relative.as_posix() == name and relative.suffix == '.py', 'source_path_escape_or_alias')
        path = source_root / relative
        require(path.resolve() == path and path.is_relative_to(source_root) and path.is_file(),
                'source_symlink_escape_or_missing_file:' + name)
        require(valid_hash(expected) and sha(path) == expected, 'source_closure_drift:' + name)
    for name in HISTORICAL_ENGINE_CONTRACTS:
        require(valid_hash(historical_files.get(name)), 'R127_historical_engine_hash_required:' + name)
        require(source_files[name] == historical_files[name], 'historical_engine_contract_drift:' + name)
    return source_root


def validate_plan(plan_path):
    plan = read(plan_path)
    require(plan['schema'] == SCHEMA and plan['trainingAllowed'] is False
            and all(type(plan[field]) is int and plan[field] == 0 for field in ('optimizer_steps', 'parent_calls', 'training_rows')),
            'evaluation_only_native_plan_required')
    require(time.time() < plan['hard_end_unix'] <= plan['lease_end_unix'] - 21600, 'bounded_lease_wall_required')
    manifest = checked(plan['manifest'])
    validate_manifest(manifest)
    require(manifest['exclusions_sha256'] == digest(sorted(checked(manifest['exclusions']))), 'exclusions_drift')
    exported = checked(manifest['source_export'])
    require(selected_checkpoints(exported) == manifest['conditions'], 'export_checkpoint_drift')
    source_root = validate_source_files(plan['source_root'], plan['source_files'], exported.get('original_source_files'))
    require((source_root / 'gpu/orch_r130_route_evidence_probe.py').resolve() == Path(__file__).resolve(),
            'executing_pinned_probe_required')
    require(Path(plan['output']).is_absolute() and Path(plan['model_dir']).is_absolute()
            and str(plan['gpu_uuid']).startswith('GPU-'), 'explicit_runtime_binding_required')
    bundle = Path(manifest['source_export']['path']).parent
    for entry in manifest['conditions'].values():
        adapter = bundle / entry['adapter']['path']
        require(adapter.resolve().is_relative_to(bundle.resolve()), 'adapter_path_escape')
        for filename, expected in entry['adapter']['files']:
            require(sha(adapter / filename) == expected, 'checkpoint_file_drift')
    return plan, manifest, bundle


def stage(plan_path, condition):
    plan, manifest, bundle = validate_plan(plan_path)
    require(condition in CONDITIONS and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'explicit_offline_condition_device_required')
    from gpu import orch_guided_native as native
    from gpu import orch_route_parent_campaign_run as runtime

    require(runtime.policy.CAPS['context'] == CONTEXT_LIMIT, 'frozen_context_limit_required')
    output = Path(plan['output']) / condition
    output.mkdir(parents=True, exist_ok=False)
    identity_data = manifest['conditions'][condition]['adapter']
    identity = native.bridge.AdapterIdentity.from_document(dict(identity_data, path=str(bundle / identity_data['path'])))
    binding = native.bridge.StageBinding(output.parent.name + '_' + condition, native.bridge.ARMS[0], 0,
        'sealed_readout', identity, False, True, sha(plan_path))
    write_new(output / 'BINDING.json', asdict(binding))

    def check(phase):
        require(time.time() < plan['hard_end_unix'], 'native_wall_expired:' + phase)

    try:
        loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['gpu_uuid'],
            context=native.StageContext(), check=check, engine_factory=runtime.Engine)
        require(loaded.optimizer is None and loaded.observed == identity, 'readonly_exact_adapter_required')
        write_new(output / 'LOADED.json', dict(adapter=loaded.observed.document(), process=loaded.process,
            condition=condition, parent_present=False, fresh_process=True, optimizer_steps=0))

        def generate(messages, *, max_new_tokens):
            check('generation')
            return loaded.engine.generate(messages, max_new_tokens=max_new_tokens)

        records = evaluate_condition(manifest, condition, generate, lambda name, value: write_new(output / name, value))
        loaded.verify_unchanged()
        write_new(output / 'COMPLETE.json', dict(status='COMPLETE', condition=condition, calls=len(records),
            call_refs=[reference(output / f'CALL_{ordinal:03d}.json') for ordinal in range(1, len(records) + 1)],
            adapter=loaded.observed.document(), unchanged=True, manifest_sha256=digest(manifest),
            optimizer_steps=0, training_rows=0, parent_calls=0, trainingAllowed=False))
    except Exception as error:
        write_new(output / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
                                              trainingAllowed=False, no_retry=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'stage'))
    parser.add_argument('--export', type=Path)
    parser.add_argument('--exclusions', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--condition', choices=CONDITIONS)
    args = parser.parse_args()
    if args.action == 'prepare':
        require(args.export is not None and args.exclusions is not None and args.output is not None, 'prepare_paths_required')
        prepare(args.export, args.exclusions, args.output)
    elif args.action == 'validate':
        validate_plan(args.plan)
        print('R130_CPU_VALIDATED_NO_NATIVE_CALLS')
    else:
        stage(args.plan, args.condition)


if __name__ == '__main__':
    main()
