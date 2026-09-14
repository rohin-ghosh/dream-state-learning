"""Independent local replay reduction of ROOT/{collect,readout}; no tensor IO.

--collection DIRECTORY explicitly reuses an earlier collection instead of
ROOT/collect. Its sibling source/ tree authenticates its original code bytes;
the readout runtime must support replay of that recorded collection helper.

The result checks recorded readonly state joins, not live adapter/base tensors.
Missing observations retain the four-task denominators and are never successes.
This is post-run output verification, not a launch approval or scientific gate.
"""

import argparse
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SCHEMA = 'DEV_EVENT_TWO_HOP_INDEPENDENT_REDUCTION_V1'
driver = task = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_runtime(source_root=None):
    global driver, task
    from tools.astra_adult_cycle_reduce import NoNativeImports

    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, NoNativeImports())
    if source_root is not None:
        source_root = Path(source_root).resolve()
        sys.path.insert(0, str(source_root))
    driver = importlib.import_module('gpu.astra_event_two_hop')
    task = importlib.import_module('organism_v6.experienced_event_two_hop')
    if source_root is not None:
        for module, relative in ((driver, 'gpu/astra_event_two_hop.py'),
                (task, 'organism_v6/experienced_event_two_hop.py'),
                (driver.source, 'gpu/astra_experienced_event_microloop.py')):
            require(Path(module.__file__).resolve() == source_root / relative,
                    'captured_source_already_loaded_mismatch_run_in_fresh_process')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def terminal(directory, phase, code_root=None):
    names = [name for name in ('RESULT.json', 'FAILED.json') if (directory / name).exists()]
    require(len(names) == 1, 'one_terminal_receipt_required:' + phase)
    receipt = read(directory / names[0])
    status = 'FAILED' if names[0] == 'FAILED.json' else 'COMPLETE'
    require(receipt.get('schema') == driver.SCHEMA and receipt.get('phase') == phase
        and receipt.get('status') == status and receipt.get('fits') == 0
        and receipt.get('parent_present') is False and receipt.get('automatic_training') is False,
        'terminal_stage_contract:' + phase)
    code_files = (task.__file__, driver.__file__, driver.source.__file__) if code_root is None else (
        code_root / 'organism_v6/experienced_event_two_hop.py', code_root / 'gpu/astra_event_two_hop.py',
        code_root / 'gpu/astra_experienced_event_microloop.py')
    require(all(receipt.get(key) == digest(path) for key, path in zip(
        ('helper_sha256', 'entry_sha256', 'native_engine_sha256'), code_files)), 'recorded_code_hash_drift')
    if phase == 'collect':
        require(receipt['helper_sha256'] in (digest(task.__file__), getattr(driver, 'ORIGINAL_COLLECTION_HELPER', None)),
                'collection_helper_not_supported_by_readout_runtime')
    return receipt, dict(status=status, receipt_file=names[0], receipt_sha256=digest(directory / names[0]),
        error=receipt.get('error'), fits=0)


def native_calls(directory, receipt, cap):
    paths = sorted(directory.glob('CALL_*.json'))
    require([path.name for path in paths] == ['CALL_%03d.json' % index for index in range(len(paths))],
            'native_call_inventory_or_order')
    calls = [read(path) for path in paths]
    require(len(calls) == receipt.get('model_calls') and len(calls) <= cap, 'native_call_count_drift')
    require(all(call.get('call_index') == index for index, call in enumerate(calls)), 'native_call_index_drift')
    return calls


def context(directory, receipt, world):
    require(read(directory / 'WORLD.json') == world and receipt.get('world_sha256') == task.document_sha256(world)
        and read(directory / 'TASKS.json') == task.build_tasks(world), 'world_or_public_task_drift')
    parent = receipt['source']
    require(read(directory / 'INPUTS.json') == parent and parent.get('parent_adapter_state_sha256') == driver.PARENT_STATE
        and bool(parent.get('parent_training_result_sha256')) and bool(parent.get('parent_after_result_sha256'))
        and {'adapter_model.safetensors', 'adapter_config.json'} <= set(parent.get('parent_adapter_files', {})),
        'parent_input_binding_drift')
    readonly = dict(loaded_state=receipt.get('loaded_adapter_state_sha256'),
        after_state=receipt.get('adapter_state_after'), parent_state=parent['parent_adapter_state_sha256'],
        frozen_base_unchanged=receipt.get('frozen_base_unchanged'),
        parent_training_result_sha256=parent['parent_training_result_sha256'],
        parent_after_result_sha256=parent['parent_after_result_sha256'],
        adapter_files=parent['parent_adapter_files'], verification='RECORDED_JOINS_ONLY_NO_TENSORS_OR_WEIGHT_FILES_READ')
    readonly['matched'] = (readonly['loaded_state'] == readonly['after_state'] == driver.PARENT_STATE
                           and readonly['frozen_base_unchanged'] is True)
    if receipt['status'] == 'COMPLETE':
        require(readonly['matched'], 'readonly_state_join_drift')
    return parent, readonly


def expected_call(index, role, condition, task_index, messages, response, error):
    return dict(call_index=index, role=role, condition=condition, task_index=task_index,
        adapter_off=condition == 'OFF_OWN_TEXT' and role == 'actor', messages=messages, response=response, error=error)


def reduce_collection(directory):
    code_root = directory.parent / 'source'
    receipt, report = terminal(directory, 'collect', code_root if code_root.is_dir() else None)
    calls = native_calls(directory, receipt, 8)
    report.update(event_denominator=4, accepted_events=None, native_calls=len(calls), replay_verified=False)
    if not (directory / 'COLLECTION.json').exists():
        require(receipt['status'] == 'FAILED', 'completed_collection_document_missing')
        report['evidence_status'] = 'FAILED_BEFORE_COLLECTION_DOCUMENT'
        return report, None, receipt
    document = task.replay_collection(read(directory / 'COLLECTION.json'))
    require(digest(directory / 'COLLECTION.json') == receipt.get('collection_sha256'), 'collection_file_hash_drift')
    parent, readonly = context(directory, receipt, document['world'])
    expected = [expected_call(index, 'collection', None, None, capture['messages'], capture['response'], capture['error'])
                for index, capture in enumerate(document['captures'])]
    require(calls == expected and receipt.get('accepted_events') == document['accepted_events'], 'collection_native_capture_drift')
    if receipt['status'] == 'COMPLETE':
        require(document['ready'] and document['model_calls'] == 8
            and all(call['error'] is None for call in calls), 'complete_source_exposures_required')
    report.update(accepted_events=document['accepted_events'], ready=document['ready'], replay_verified=True,
        collection_sha256=digest(directory / 'COLLECTION.json'), readonly=readonly,
        records=[dict(event=record['edge']['event'], accepted=record['accepted'], error=record['error'],
                      actual_transition=record['transition']) for record in document['records']])
    return report, document, receipt


def output_diagnostic(episode):
    actors = [trace for trace in episode['traces'] if trace['kind'] == 'actor']
    if not actors or episode['reached_goal']:
        return None
    trace = actors[-1]
    response = trace.get('response')
    response = response if type(response) is dict else {}
    raw = response.get('raw')
    lines = raw.rstrip('\n').splitlines() if type(raw) is str else []
    command_lines = sum(re.fullmatch(r'(READ EVENT E_|ROUTE P_)[A-Z2-7]{10}', line) is not None for line in lines)
    if trace.get('error') is not None:
        category = 'ACTOR_CALLBACK_ERROR'
    elif response.get('terminal') is not True or response.get('truncated') is not False:
        category = 'NONTERMINAL_OR_TRUNCATED'
    elif episode['terminal_reason'] == 'invalid_command' and type(raw) is str:
        category = ('NODE_AS_PORT' if re.fullmatch(r'ROUTE N_[A-Z2-7]{10}\n*', raw) else
                    'MULTI_COMMAND_OUTPUT' if command_lines >= 2 else 'OTHER_INVALID_COMMAND')
    else:
        category = 'OTHER_EPISODE_FAILURE'
    return dict(classification=category, raw=raw, terminal=response.get('terminal'),
                truncated=response.get('truncated'), command_like_lines=command_lines)


def episode_metrics(entry):
    episode, score = entry['episode'], entry['score']
    return dict(task_index=entry['task_index'], goal=entry['task']['goal'],
        strict_arrival=score['strict_success'], reached_goal=score['reached_goal'], current=episode['current'],
        first_route=episode['routes'][0] if episode['routes'] else None, routes=episode['route_calls'],
        actor_calls=episode['actor_calls'], memory_calls=episode['memory_calls'],
        read_addresses=[trace['address'] for trace in episode['traces'] if trace['kind'] == 'memory'],
        terminal_reason=episode['terminal_reason'], episode_sha256=episode['episode_sha256'],
        output_diagnostic=output_diagnostic(episode))


def reduce_readout(directory, collection, collection_receipt, collection_report):
    receipt, report = terminal(directory, 'readout')
    protocol = receipt.get('arguments', {}).get('protocol', 'original')
    require(protocol in getattr(task, 'PROTOCOLS', ('original',)), 'unknown_recorded_readout_protocol')
    parent, readonly = context(directory, receipt, collection['world'])
    require(parent == collection_receipt['source'] and receipt.get('collection_result_sha256') == collection_report['receipt_sha256']
        and read(directory / 'COLLECTION_SOURCE.json') == collection, 'collection_readout_source_join_drift')
    calls = native_calls(directory, receipt, 112)
    store = task.exact_text_store(collection)
    tasks = task.build_tasks(collection['world'])
    expected, panels, reduced = [], {}, {}
    missing = False
    for condition in driver.CONDITIONS:
        entries = []
        for index, public in enumerate(tasks):
            path = directory / ('%s_EPISODE_%02d.json' % (condition, index))
            if not path.exists():
                missing = True
                continue
            require(not missing, 'nonprefix_episode_inventory')
            entry = read(path)
            require(entry.get('condition') == condition and entry.get('task_index') == index and entry.get('task') == public,
                    'condition_task_or_order_drift')
            require(entry['episode'].get('protocol', 'original') == protocol, 'episode_readout_protocol_drift')
            verified = task.replay_episode(collection['world'], public, entry['episode'])
            require(task.score_episode(collection['world'], public, verified) == entry['score'], 'episode_score_drift')
            origin = ('PARAMETRIC_UNWRITTEN' if condition == 'ON_PARAMETRIC' else
                      'DECLARED_UNAVAILABLE_SERVICE' if condition == 'ON_UNAVAILABLE' else 'ACTUAL_OWN_EVENT_TEXT')
            require(entry.get('memory_origin') == origin, 'memory_origin_drift')
            for trace in verified['traces']:
                if trace['kind'] == 'actor':
                    expected.append(expected_call(len(expected), 'actor', condition, index,
                        trace['messages'], trace['response'], trace['error']))
                elif trace['kind'] == 'memory':
                    if condition == 'ON_PARAMETRIC':
                        expected.append(expected_call(len(expected), 'memory', condition, index,
                            driver.memory_messages(trace['address']), trace['response'], trace['error']))
                    else:
                        raw = 'MEMORY UNAVAILABLE' if condition == 'ON_UNAVAILABLE' else store[trace['address']]
                        require(trace['response'] == raw and trace['error'] is None, 'nonparametric_memory_text_drift')
            entries.append(entry)
        panels[condition] = dict(denominator=4, correct=sum(entry['score']['strict_success'] for entry in entries),
            reached_goal=sum(entry['score']['reached_goal'] for entry in entries),
            actor_calls=sum(entry['score']['actor_calls'] for entry in entries),
            memory_calls=sum(entry['score']['memory_calls'] for entry in entries),
            terminal_reasons=dict(Counter(entry['score']['terminal_reason'] for entry in entries)), episodes=entries)
        reduced[condition] = dict(panels[condition], episodes=[episode_metrics(entry) for entry in entries], observed_episodes=len(entries))
        reduced[condition]['output_failure_classes'] = dict(Counter(
            episode['output_diagnostic']['classification'] for episode in reduced[condition]['episodes']
            if episode['output_diagnostic'] is not None))
        if len(entries) != 4:
            reduced[condition].update(correct=None, reached_goal=None, status='INCOMPLETE_OBSERVATIONS')
    require(calls[:len(expected)] == expected, 'native_role_condition_prompt_response_or_adapter_scope_drift')
    counts = dict(Counter(call['role'] for call in calls))
    require(set(counts) <= {'actor', 'memory'} and counts.get('actor', 0) <= 96 and counts.get('memory', 0) <= 16,
            'native_role_budget_drift')
    if not missing:
        require(calls == expected and read(directory / 'PANELS.json') == panels
            and receipt.get('panels') == panels and receipt.get('native_calls_by_role') == counts, 'panel_summary_or_native_count_drift')
    if receipt['status'] == 'COMPLETE':
        require(not missing and all(call['error'] is None for call in calls), 'complete_readout_required')
    report.update(panels=reduced, native_calls=len(calls),
        native_calls_by_role={role: counts.get(role, 0) for role in ('actor', 'memory')}, readonly=readonly,
        replay_verified=True, unmatched_native_calls=len(calls) - len(expected), matched_collection_source=True)
    if protocol != 'original':
        report['protocol'] = protocol
    return report


def reduce_root(root, source_root=None, collection_path=None):
    root = Path(root)
    if source_root is None and (root / 'source').is_dir():
        source_root = root / 'source'
    load_runtime(source_root)
    report = dict(schema=SCHEMA, root=str(root), status='INCOMPLETE', expected_fits=0,
        expected_event_denominator=4, expected_task_denominators={condition: 4 for condition in driver.CONDITIONS},
        tensor_loading=False, approval_gate=False, claim=driver.CLAIM, stages={},
        runtime_source_root=str(Path(source_root).resolve()) if source_root is not None else 'WORKTREE')
    collection_directory = Path(collection_path) if collection_path is not None else root / 'collect'
    if collection_path is not None:
        report.update(reused_collection=True, collection_directory=str(collection_directory))
    try:
        if not any((collection_directory / name).exists() for name in ('RESULT.json', 'FAILED.json')):
            report['stages']['collect'] = dict(status='MISSING_TERMINAL_RECEIPT', event_denominator=4)
            return report
        collected, collection, receipt = reduce_collection(collection_directory)
        report['stages']['collect'] = collected
        if collected['status'] == 'FAILED':
            report.update(status='FAILED', failure_stage='collect')
            report['stages']['readout'] = dict(status='NOT_ADMISSIBLE_AFTER_FAILED_COLLECTION',
                task_denominators=report['expected_task_denominators'])
            return report
        if not any((root / 'readout' / name).exists() for name in ('RESULT.json', 'FAILED.json')):
            report['stages']['readout'] = dict(status='MISSING_TERMINAL_RECEIPT', task_denominators=report['expected_task_denominators'])
            return report
        reduced = reduce_readout(root / 'readout', collection, receipt, collected)
        report['stages']['readout'] = reduced
        report.update(status=reduced['status'], total_native_calls=collected['native_calls'] + reduced['native_calls'])
        if collection_path is not None:
            report.update(reused_collection_native_calls=collected['native_calls'], new_native_calls=reduced['native_calls'])
    except (ValueError, KeyError, TypeError, OSError) as error:
        report.update(status='INVALID', verification_error=str(error))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--source-root', help='Defaults to ROOT/source when present; use a fresh process.')
    parser.add_argument('--collection', help='Existing collection directory; defaults to ROOT/collect.')
    parser.add_argument('--output')
    options = parser.parse_args(argv)
    report = reduce_root(options.root, options.source_root, options.collection)
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n'
    if options.output:
        with Path(options.output).open('x', encoding='utf-8') as stream:
            stream.write(rendered)
    else:
        print(rendered, end='')
    return 0 if report['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
