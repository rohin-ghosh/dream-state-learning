"""Receiver-only transport over the preserved original parent state and policy."""

import argparse
import ast
import copy
from datetime import datetime
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import types

import metadata_rebind as metadata
import node3_route_binding as route
import r184_effort_parent as effort
import r188_parent as examples
import snapshot_transport
import takeover as base

STATE = base.HERE / 'r188/receiving_parents'
WRAPPERS = {'node2': 'gpu/ovx_ssh.sh', 'node4': 'gpu/a40r_ssh.sh'}
HOSTS = {'node2': '[REDACTED_HOST]'}
NAMES = {0: 'support_free', 1: 'creative_reread', 2: 'brain_free', 3: 'brain_guided', 4: 'creative_free', 7: 'creative_select'}


def post(message):
    heading = '# COORDINATION — Codex ⇄ Fable direct channel'
    addition = '\n## [Builder/Tesla → Main/Gauss/Ampere — receiving parent] ' + datetime.now().astimezone().isoformat() + '\n\n' + message + '\n'
    patch = '*** Begin Patch\n*** Update File: ' + str(base.REPO / 'research_loop/COORDINATION.md') + '\n@@\n ' + heading + '\n'
    patch += ''.join('+' + line + '\n' for line in addition.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)


def remote(binding, script):
    wrapper = WRAPPERS[binding['target_node']]
    base.require(binding['ssh_wrapper'] == wrapper, 'receiver_wrapper_only')
    prefix = 'import socket,sys\nassert socket.gethostname()==' + repr(binding['host']) + '\nsys.path.insert(0,' + repr(binding['source_root']) + ')\n'
    result = subprocess.run(['bash', str(base.REPO / wrapper), 'python3 -B -'], input=prefix + script,
        text=True, capture_output=True, timeout=90)
    base.require(result.returncode == 0, 'receiving_read_failed:' + result.stderr[-250:])
    return json.loads(result.stdout)


def verify(binding):
    script = 'binding=' + repr(binding) + '\n' + '''
import hashlib,json,os,time
from pathlib import Path
root=Path(binding['root']); source=Path(binding['source_root'])
path=root/'stream/records'/('%020d.json'%binding['loaded']['index'])
record=json.loads(path.read_text())
assert record['kind']=='LOADED' and record['sha256']==binding['loaded']['record_sha256']
assert hashlib.sha256(path.read_bytes()).hexdigest()==binding['loaded']['file_sha256']
process=Path('/proc')/str(binding['native']['pid'])
stat=(process/'stat').read_text().rsplit(')',1)[1].split()
assert stat[0]!='Z' and stat[19]==str(binding['native']['startticks'])
assert str((process/'cwd').resolve())==str(source)
arguments=(process/'cmdline').read_bytes().split(b'\\0')
assert b'gpu.orch_r125_continual_guard' in arguments and b'native' in arguments and b'--config' in arguments
guard=Path(os.fsdecode(arguments[arguments.index(b'--config')+1]))
assert hashlib.sha256(guard.read_bytes()).hexdigest()==binding['guard_sha256']
console=source/'gpu/orch_r127_pilot_console.py'
assert hashlib.sha256(console.read_bytes()).hexdigest()==binding['console_sha256']
from gpu.orch_r127_pilot_console import publish_parent
import inspect
assert Path(inspect.getsourcefile(publish_parent)).resolve()==console.resolve()
print(json.dumps(dict(status='RECEIVING_LOADED_LIVE_IDENTITY_VERIFIED',observed_unix=time.time(),
    root=str(root),source=str(source),pid=binding['native']['pid'],loaded_index=record['index'],
    loaded_sha256=record['sha256'],console_path=str(console),console_sha256=binding['console_sha256'],
    publication_calls=0,child_signals=0)))
'''
    return remote(binding, script)


def rebase(physical, state):
    if physical in (1, 2):
        restored = base.read(base.HERE / 'r188' / ('physical' + str(physical)) / 'REMOTE_RESTORED.json')['document']
        state = examples.rebase_snapshot(state, restored)
    final = next(row for row in base.read(base.HERE / 'r188/FINAL_SOURCE_CENSUS.json')['rows'] if row['physical'] == physical)
    return examples.rebase_snapshot(state, dict(saved_index=final['latest_complete_index'], counts=final['suffix_accounting']))


def make_poll(physical, binding, runner=subprocess.run):
    prepared = base.read(base.HERE / 'parents' / ('physical' + str(physical)) / 'PREPARATION.json')
    old_root = prepared['assignment']['active_child_root']
    first = True

    def run(command, **kwargs):
        base.require(command == ['bash', str(base.REPO / 'gpu/ovx2_ssh.sh'), 'python3 -B -'], 'expected_snapshot_transport')
        line = 'root=' + repr(old_root) + '\n'
        base.require(kwargs['input'].count(line) == 1, 'exact_one_root_binding')
        kwargs['input'] = kwargs['input'].replace(line, 'root=' + repr(binding['root']) + '\n')
        kwargs['input'] = 'import socket\nassert socket.gethostname()==' + repr(binding['host']) + '\n' + kwargs['input']
        base.require(binding['ssh_wrapper'] == WRAPPERS[binding['target_node']], 'receiver_only_wrapper')
        return runner(['bash', str(base.REPO / binding['ssh_wrapper']), 'python3 -B -'], **kwargs)

    namespace = dict(snapshot_transport.__dict__, subprocess=types.SimpleNamespace(run=run))
    original = types.FunctionType(snapshot_transport.poll.__code__, namespace, 'poll')

    def poll(requested_physical, cursor=None):
        nonlocal first
        base.require(requested_physical == physical, 'single_life_receiver')
        observed = original(physical, None if first else cursor)
        first = False
        observed['snapshot'] = rebase(physical, observed['snapshot'])
        return observed

    return poll


def console_commands(binding):
    prefix = 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(binding['source_root']) + ' /localhome/local-rohing/v2/venv/bin/python -B -m '
    root = ' --root ' + shlex.quote(binding['root'])
    return dict(follow='bash ' + binding['ssh_wrapper'] + ' ' + shlex.quote(prefix + 'gpu.orch_r125_stream_console' + root + ' --follow'),
        rohin_publish='bash ' + binding['ssh_wrapper'] + ' ' + shlex.quote(prefix + 'gpu.orch_r127_pilot_console parent' + root + ' --speaker Rohin --text ' + shlex.quote('YOUR ACTUAL ROHIN MESSAGE')),
        test_publications=0, speaker='Rohin', old_source_frozen=True)


def receiver_validator(original, expected):
    tree = ast.parse(inspect.getsource(original))
    candidates = [node for node in ast.walk(tree) if isinstance(node, ast.Tuple)
        and all(isinstance(item, ast.Constant) for item in node.elts)
        and tuple(item.value for item in node.elts) == ('ovx2', 'a40r', 'ovx3', 'a100')]
    base.require(len(candidates) == 1, 'one_transport_allowlist_only')
    candidates[0].elts.append(ast.Constant(value='ovx'))
    namespace = dict(original.__globals__)
    exec(compile(ast.fix_missing_locations(tree), '<owned-receiving-transport-allowlist>', 'exec'), namespace)
    validator = namespace[original.__name__]

    def validate(config):
        base.require(all(config[key] == expected[key] for key in ('node', 'root', 'source_root', 'hard_end_unix')), 'exact_receiver_configuration')
        return validator(config)

    return validate


def prepare(physical, handoff_path):
    handoff = base.read(handoff_path)
    base.require(handoff['status'] == 'ACTUAL_RECEIVING_LOADED' and handoff['source_original_physical'] == physical, 'actual_owner_loaded_handoff')
    folder = route.folder_for(physical)
    owned = STATE / ('physical' + str(physical))
    stopped = base.read(base.HERE / 'r188/final_parent_handoff' / ('physical' + str(physical) + '.json'))
    base.require(stopped['status'] == 'SETTLED_ORIGINAL_PARENT_STOPPED', 'old_parent_settled_stopped')
    original = base.read(folder / 'CONFIG.json')
    binding = dict(target_node=handoff['target_node'], host=handoff.get('host') or HOSTS[handoff['target_node']],
        root=handoff['physical_receiving_root'], source_root=handoff['source_root'],
        ssh_wrapper=handoff['parent_rebind']['ssh_wrapper'], loaded=handoff['loaded'], native=handoff['native'],
        guard_sha256=handoff['guard_sha256'], console_sha256=handoff['rohin_console_source_sha256'],
        hard_end_unix=handoff['hard_end_unix'], handoff=base.reference(handoff_path))
    base.require(time.time() < binding['hard_end_unix'], 'existing_receiver_wall')
    checked = verify(binding)
    config = copy.deepcopy(original)
    config.update(node=Path(binding['ssh_wrapper']).stem.removesuffix('_ssh'), root=binding['root'],
        source_root=binding['source_root'], hard_end_unix=binding['hard_end_unix'])
    base.write(owned / 'BINDING.json', binding)
    base.write(owned / 'LOADED_VERIFIED.json', checked)
    base.write(folder / 'CONFIG_REHOME_V1.json', config)
    base.write(owned / 'CONSOLE.json', console_commands(binding))
    base.write(owned / 'PREPARED.json', dict(status='PARENT_TRANSPORT_PREPARED_NOT_STARTED',
        physical=physical, arm=config['r175_arm'], cadence=config['cadence_responses'],
        old_config=base.reference(folder / 'CONFIG.json'), new_config=base.reference(folder / 'CONFIG_REHOME_V1.json'),
        preserved_seed=base.reference(folder / 'SEED.json'), original_output=str(folder / 'parent'),
        final_ledger=base.reference(base.HERE / 'r188/final_parent_handoff' / ('physical' + str(physical) + '.json')),
        no_new_introduction=True, no_counter_reseed=True, existing_receiver_lease_only=True))
    return checked


def publication_proof(binding, publication, record_index=None):
    script = 'root=' + repr(binding['root']) + '\npublication=' + repr(publication) + '\nindex=' + repr(record_index) + '\n' + '''
import hashlib,json,time
from pathlib import Path
stream=Path(root)/'stream'; path=stream/'inbox'/(publication['id']+'.json')
inbox=json.loads(path.read_text()); digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest==publication['sha256'] and inbox['actor']=='parent' and inbox['split']=='TRAIN'
result=dict(inbox_path=str(path),inbox_sha256=digest,inbox_id=inbox['id'],persisted_unix=path.stat().st_mtime,observed_unix=time.time())
if index is not None:
    path=stream/'records'/('%020d.json'%index); record=json.loads(path.read_text()); document=record['document']
    assert record['kind']=='REQUEST' and document['render_receipt']['all_history_tokens_masked'] is True
    matches=[message for message in document['messages'] if inbox['text'] in message.get('content','')]
    assert matches
    result.update(record_index=index,record_sha256=record['sha256'],record_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        request_started_unix=document.get('started_unix'),record_persisted_unix=path.stat().st_mtime,
        rendered_messages=matches,render_receipt=document['render_receipt'])
print(json.dumps(result))
'''
    return remote(binding, script)


def expose(physical, binding, output, state, old_attempts):
    owned = STATE / ('physical' + str(physical))
    first_path = owned / 'FIRST_PUBLICATION.json'
    if not first_path.exists():
        for attempt in sorted(Path(output).glob('parent_*')):
            if attempt.name in old_attempts or not (attempt / 'RESULT.json').exists():
                continue
            result = base.read(attempt / 'RESULT.json')
            if result['status'] != 'PUBLISHED':
                continue
            base.require(result['source_sha256'] == base.sha(attempt / 'SOURCE.json') and
                base.read(attempt / 'PUBLISH_INTENT.json')['message'] == result['message'], 'published_source_intent_bound')
            actual = publication_proof(binding, result['publication'])
            base.write(first_path, dict(status='ACTUAL_RECEIVING_PARENT_PUBLISHED', publication=result['publication'],
                actual=actual, result=base.reference(attempt / 'RESULT.json'), source=base.reference(attempt / 'SOURCE.json'),
                prompt=base.reference(attempt / 'PROMPT.json'), message_sha256=hashlib.sha256(result['message'].encode()).hexdigest()))
            post(f"{NAMES[physical]} receiving parent ACTUAL PUB {result['publication']['id']}, persisted {actual['persisted_unix']}; `{first_path.relative_to(base.REPO)}`. Not yet a rendered claim; no introduction replay.")
            break
    rendered = owned / 'FIRST_RENDERED_REQUEST.json'
    if first_path.exists() and not rendered.exists():
        first = base.read(first_path)
        delivery = state['delivered'].get(first['publication']['id'])
        if delivery is not None:
            base.require(delivery['text_sha256'] == first['message_sha256'], 'exact_receiving_message')
            proof = publication_proof(binding, first['publication'], delivery['record_index'])
            base.write(rendered, dict(status='ACTUAL_RECEIVING_PARENT_RENDERED', proof=proof, delivered=delivery,
                publication=base.reference(first_path), learned_outcome_claim=False))
            post(f"{NAMES[physical]} receiving parent ACTUAL RENDERED REQUEST{delivery['record_index']} SHA{delivery['record_sha256']}; `{rendered.relative_to(base.REPO)}`. Mask verified; source/prompt/inbox bound, no learning claim.")


def serve(physical, preflight=False):
    folder = route.folder_for(physical)
    owned = STATE / ('physical' + str(physical))
    binding = base.read(owned / 'BINDING.json')
    config_path = folder / 'CONFIG_REHOME_V1.json'
    verify(binding)
    poll = make_poll(physical, binding)
    snapshot_transport.poll = poll
    config = base.read(config_path)
    output = folder / 'parent'
    old_attempts = {path.name for path in output.glob('parent_*')}
    effort.exposure = lambda requested, destination, state: expose(requested, binding, destination, state, old_attempts)
    effort.STATE = STATE

    def runtime(requested, unused):
        base.require(requested == physical, 'same_receiver_life')
        bundle = base.HERE / ('source_' + config['r175_arm'])
        sys.path.insert(0, str(bundle))
        base.project_artifact_writer(bundle)
        module = importlib.import_module('gpu.orch_r133_programme_parent')
        module.validate = receiver_validator(module.validate, config)
        loader = examples.runtime if physical in (1, 2) else effort.runtime
        parent, provider, actual, helper = loader(physical, config_path)
        parent.snapshot = lambda repository, current_config: poll(physical)['snapshot']
        original_publish = parent.publish

        def publish(repository, current_config, message):
            base.require(all(current_config[key] == config[key] for key in ('node', 'root', 'source_root', 'hard_end_unix')), 'exclusive_receiver_publication')
            return original_publish(repository, current_config, message)

        parent.publish = publish
        return parent, provider, actual, helper

    if preflight:
        parent, provider, actual, helper = runtime(physical, config_path)
        policy = importlib.import_module('gpu.orch_r166_parent_policy')
        observed = poll(physical)
        for unused in range(12):
            if observed['snapshot']['caught_up']:
                break
            observed = poll(physical, observed['cursor'])
        base.require(observed['snapshot']['caught_up'], 'bounded_receiver_bootstrap_not_caught_up')
        state = observed['snapshot']
        memory = policy.memory(base.read(folder / 'SEED.json'), policy.local_attempts(output), state)
        instruction, payload = policy.prompt(actual, state, memory)
        base.require(instruction.count(effort.MARKER) == 1, 'same_effort_prompt')
        base.require(policy.community.response_schema is provider.response_schema, 'strict_compatible_parser_bound')
        return dict(status='RECEIVING_PARENT_CPU_AND_READONLY_PREFLIGHT_PASS', physical=physical,
            journal_id=state['journal_id'], response_count=state['response_count'], request_count=state['request_count'],
            sleep_count=state['sleep_count'], arm=actual['r175_arm'], cadence=actual['cadence_responses'],
            awaiting_render=memory['awaiting_render'], last_response_count=memory['last_response_count'],
            provider_calls=0, publication_calls=0)

    sequence = time.time_ns()

    def read(path):
        return base.read(config_path if Path(path) == folder / 'CONFIG.json' else path)

    def sha(path):
        return base.sha(config_path if Path(path) == folder / 'CONFIG.json' else path)

    def write(path, document):
        path = Path(path)
        if path == output / 'STARTED.json':
            path = owned / 'STARTED.json'
            document = dict(document, receiving_binding=base.reference(owned / 'BINDING.json'),
                preserved_output=str(output), original_attempts=sorted(old_attempts), old_source_frozen=True)
        elif path.parent == folder and path.name.startswith('STATUS_'):
            path = owned / path.name
        elif path.name in ('TERMINAL.json', 'SERVICE_FAILED.json'):
            path = owned / (str(sequence) + '_' + path.name)
        base.write(path, document)

    namespace = dict(metadata.__dict__, STATE=folder.parent.parent, runtime=runtime, hashlib=hashlib,
        read=read, sha=sha, write=write, HARD_END=binding['hard_end_unix'], __file__=__file__)
    try:
        types.FunctionType(metadata.serve.__code__, namespace, 'serve')(physical)
    except BaseException as error:
        base.write(owned / ('FAILED_%d.json' % time.time_ns()), dict(error_type=type(error).__name__,
            reason=str(error)[-300:] if isinstance(error, ValueError) else 'inspect_owned_trace',
            no_publication_retry=True, observed_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'preflight', 'serve'))
    parser.add_argument('--physical', type=int, choices=base.PHYSICALS, required=True)
    parser.add_argument('--handoff')
    arguments = parser.parse_args()
    if arguments.action == 'prepare':
        result = prepare(arguments.physical, arguments.handoff)
    else:
        result = serve(arguments.physical, preflight=arguments.action == 'preflight')
    if result is not None:
        print(json.dumps(result, sort_keys=True))
