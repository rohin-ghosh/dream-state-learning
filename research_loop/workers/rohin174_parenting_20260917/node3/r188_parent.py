"""Restore parent read cursors after explicit rollback, without resending baselines."""

import argparse
import copy
import hashlib
import importlib
import inspect
from pathlib import Path
import time
import types

import r184_effort_parent as effort
import node3_route_binding as route
import snapshot_transport
import takeover as base
from observe_r181_receipts import post


STATE = base.HERE / 'r188'
OLD_RUNTIME = effort.runtime
OLD_EXPOSURE = effort.exposure


def rebase_snapshot(snapshot, restored):
    result = copy.deepcopy(snapshot)
    counts = restored['counts']
    for field, kind in (('request_count', 'REQUEST'), ('response_count', 'RESPONSE')):
        result[field] += counts['discarded_' + kind]
    for delivery in result['delivered'].values():
        if delivery['record_index'] > restored['saved_index']:
            delivery['request_count'] += counts['discarded_REQUEST']
    result['R188_explicit_rollback'] = dict(saved_index=restored['saved_index'], counts=counts,
        unbroken_exact_continuation=False, counters='observed lifetime counts, not retained learning')
    return result


def exposure(physical, output, state):
    OLD_EXPOSURE(physical, output, state)
    folder = STATE / ('physical' + str(physical))
    for name in ('FIRST_PUBLICATION', 'FIRST_RENDERED_REQUEST'):
        evidence = folder / (name + '.json')
        reported = folder / ('R188_' + name + '.json')
        if evidence.exists() and not reported.exists():
            first = base.read(folder / 'FIRST_PUBLICATION.json')
            prompt = base.read(first['prompt']['path'])
            base.require('R188_REPORTED_WORKED_EXAMPLES_V1' in prompt['instruction'], 'actual_R188_prompt')
            base.write(reported, dict(evidence=base.reference(evidence), source_prompt=first['prompt'],
                example_provenance='Rohin188 reported example, not recipient success', observed_unix=time.time()))
            post(f"R188 restored node3 GPU{physical} {name}: `{reported.relative_to(base.REPO)}`; source-bound reported example plus own-object application, not a new baseline or learned-outcome claim.")


def runtime(physical, config_path):
    parent, provider, config, helper = OLD_RUNTIME(physical, config_path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    pin = base.read(STATE / 'PARENT_EXAMPLES_PIN.json')
    base.require(base.sha(pin['path']) == pin['sha256'], 'exact_Main_R188_examples')
    examples = base.load_file(pin['path'], 'private_Main_R188_examples')
    prior_prompt = policy.prompt
    restored = base.read(STATE / ('physical' + str(physical)) / 'REMOTE_RESTORED.json')['document']

    def prompt(current_config, state, memory):
        instruction, payload = prior_prompt(current_config, state, memory)
        instruction += '\nR188 permits one attributed reported example before the own-object questions; never supply the task answer. '
        instruction += 'This life explicitly rolled back a partial sleep; do not describe unbroken exact continuation or retained discarded updates.\n'
        return examples.append_parent_examples(instruction.encode()).decode(), payload

    policy.prompt = prompt
    original_tick = inspect.getclosurevars(policy.tick).nonlocals['original_tick']
    bindings = inspect.getclosurevars(original_tick).nonlocals
    bindings['dispatch'].__globals__['prompt'] = prompt
    base.require(bindings['strict_tick'].__globals__['prompt'] is prompt, 'normal_and_corrective_R188_prompt')
    return parent, provider, config, helper


def preflight(physical):
    namespace = dict(effort.__dict__, runtime=runtime, __file__=str(Path(__file__).resolve()))
    result = types.FunctionType(effort.preflight.__code__, namespace, 'preflight')(physical)
    result.update(r188_examples=base.read(STATE / 'PARENT_EXAMPLES_PIN.json'),
        no_baseline_resend=True, read_cursor_rebuilt_after_explicit_rollback=True)
    return result


def serve(physical):
    folder = route.folder_for(physical)
    owned = STATE / ('physical' + str(physical))
    restored = base.read(owned / 'REMOTE_RESTORED.json')['document']
    original_poll = snapshot_transport.poll
    first = True

    def poll(requested_physical, cursor=None):
        nonlocal first
        base.require(requested_physical == physical, 'one_restored_parent_scope')
        result = original_poll(physical, None if first else cursor)
        first = False
        result['snapshot'] = rebase_snapshot(result['snapshot'], restored)
        return result

    snapshot_transport.poll = poll
    effort.STATE = STATE
    effort.exposure = exposure
    offset = max((int(path.stem.split('_')[1]) for path in folder.glob('STATUS_*.json')), default=-1) + 1

    def preserved_write(path, document):
        path = Path(path)
        if path == folder / 'parent/STARTED.json':
            path = owned / 'STARTED.json'
            document = dict(document, wrapper=base.reference(__file__), r188_examples=base.read(STATE / 'PARENT_EXAMPLES_PIN.json'),
                restored=base.reference(owned / 'REMOTE_RESTORED.json'), read_cursor_rebuilt=True,
                discarded_suffix_counts=restored['counts'], unbroken_exact_continuation=False,
                config=base.reference(folder / 'CONFIG.json'), seed=base.reference(folder / 'SEED.json'))
        elif path.parent == folder and path.name.startswith('STATUS_'):
            path = folder / ('STATUS_%06d.json' % (offset + int(path.stem.split('_')[1])))
        base.write(path, document)

    namespace = dict(effort.previous.current.metadata.__dict__, STATE=folder.parent.parent,
        runtime=runtime, hashlib=hashlib, write=preserved_write, __file__=str(Path(__file__).resolve()))
    try:
        types.FunctionType(effort.previous.current.metadata.serve.__code__, namespace, 'serve')(physical)
    except BaseException as error:
        base.write(owned / 'PARENT_SERVICE_FAILED.json', dict(error_type=type(error).__name__,
            reason=str(error)[-500:], observed_unix=time.time()))
        raise


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'serve'))
    parser.add_argument('--physical', type=int, choices=(1, 2), required=True)
    options = parser.parse_args()
    result = globals()[options.action](options.physical)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
