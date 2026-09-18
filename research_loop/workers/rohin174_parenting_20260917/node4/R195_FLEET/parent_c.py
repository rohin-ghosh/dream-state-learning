"""New MATH-C questions-only parent; reuse the existing R175 C runtime."""

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

from parent_repairs import evidence_prompt, single_parent, tick_once


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
BUNDLE = OWN.parents[1] / 'node3/source_C'
REMOTE = '/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/MATH_C'
WALL = 1789754400
CLEAN_CONVERSATION_SHA = '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def remote(request):
    command = '/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE + '/parent_endpoint.py'
    completed = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command],
        input=json.dumps(request), capture_output=True, text=True, timeout=45)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-600:])
    return json.loads(completed.stdout)


def prepare():
    manifest = read(BUNDLE / 'ARM_BUNDLE.json')
    assert manifest['arm'] == 'C'
    assert all(sha(BUNDLE / name) == proof['sha256'] for name, proof in manifest['files'].items())
    output = OWN / 'new_parent_C'
    output.mkdir()
    programme = ('New MATH-C mathematical environment, questions-only self-derivation. Remain with the child\'s live object, '
        'not a supplied puzzle or creative/story test. Actual confined Python: read-only SymPy1.14.0/mpmath1.3.0, '
        'no Torch/GPU/network/home. A listing is not execution. Distinguish builder environment smoke from the child\'s own tool feedback. '
        'Rohin PART ONE is already the first new input; do not impersonate or replay Rohin. Opening introduces Astra as a NEW parent. '
        'Ask at most120 words, cadence3 committed responses. Three guided completed cycles52-54 then no parent publications during55-57. '
        'MATH-C also has structured THINK R202, so it is not a parent-only contrast.')
    (output / 'PROGRAMME.txt').write_text(programme)
    principles = (REPO / 'research_notes/analysis/R202_STRUCTURED_THINK_2026-09-17.txt').read_text()
    (output / 'PRINCIPLES.txt').write_text(principles)
    config = dict(schema='R133_PROGRAMME_PARENT_V1', node='a40r', root=REMOTE + '/life', source_root=REMOTE + '/source',
        programme='raw_parented', branch='R202_MATH_C', programme_path=str(output / 'PROGRAMME.txt'),
        programme_sha256=sha(output / 'PROGRAMME.txt'), principles_path=str(output / 'PRINCIPLES.txt'),
        principles_sha256=sha(output / 'PRINCIPLES.txt'), hard_end_unix=WALL,
        cadence_responses=3, cadence_label='SPARSE', parent_style='questions-only self-derivation',
        parent_reasoning_effort='low', poll_interval_seconds=3, schedule_on='response', community_learner=False,
        r166_schema='R166_PARENT_SUCCESSOR_V1', object_turn_limit=3,
        r175_schema='ROHIN175_PARENT_ARMS_V1', r175_arm='C', r175_word_limit=120)
    write(output / 'CONFIG.json', config)
    write(output / 'SOURCE.json', dict(bundle=str(BUNDLE), manifest_sha256=sha(BUNDLE / 'ARM_BUNDLE.json'),
        original_runtime_unmodified=True, actual_provider_execution_not_yet_started=True))


def runtime():
    sys.path.insert(0, str(BUNDLE))
    for name in ('gpu', 'organism_v6'):
        package = types.ModuleType(name)
        package.__path__ = [str(BUNDLE / name)]
        package.__package__ = name
        sys.modules[name] = package
    original = OWN.parents[1] / 'node3/takeover.py'
    function = next(node for node in ast.parse(original.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == 'project_artifact_writer')
    namespace = dict(ast=ast, types=types, Path=Path, json=json, sys=sys, hashlib=hashlib,
        require=lambda condition, reason: condition or (_ for _ in ()).throw(ValueError(reason)))
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(original), 'exec'), namespace)
    namespace['project_artifact_writer'](BUNDLE)
    from gpu import orch_r166_parent_policy as policy
    from gpu import orch_r133_programme_parent as parent
    from gpu import orch_route_parent_campaign_providers as provider
    assert all(Path(module.__file__).resolve().is_relative_to(BUNDLE) for module in (policy, parent, provider))
    assert 'bound_r175_arm' in policy.tick.__code__.co_consts
    path = REPO / 'gpu/orch_r175_parent_response.py'
    specification = importlib.util.spec_from_file_location('existing_response_adapter', path)
    adapter = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(adapter)
    provider.response_schema = adapter.compatible_parser(provider.response_schema)
    policy.community.response_schema = provider.response_schema
    parent.publish = lambda repository, config, message: remote(dict(op='publish', message=message))
    return policy


def bind_clean_reference():
    output = OWN / 'new_parent_C'
    source = REPO / 'research_notes/analysis/ROHIN_C2_CONVERSATION_2026-09-17.md'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CLEAN_CONVERSATION_SHA, 'exact_authorized_parent_reference'
    reference = output / 'ROHIN_C2_CONVERSATION_R203.md'
    with reference.open('xb') as copied:
        copied.write(raw)
    principles = output / 'PRINCIPLES_R203.txt'
    private_notice = (
        '\n\nPrivate parent reference, not a new child input. Only the clean conversation follows; '
        'there are no evaluator judgments. Use it to understand Rohin\'s teaching approach. '
        'Do not relay, quote, paraphrase, or assign the original C2 creative/story test to MATH-C. '
        'Do not inject later C2 answers or pretend these exchanges occurred with this clone. '
        'Stay with MATH-C\'s own mathematical investigation and actual tool feedback.\n\n')
    with principles.open('x') as target:
        target.write((output / 'PRINCIPLES.txt').read_text() + private_notice + raw.decode())
    config = read(output / 'CONFIG.json')
    config.update(principles_path=str(principles), principles_sha256=sha(principles))
    write(output / 'CONFIG_R203.json', config)
    write(output / 'CLEAN_REFERENCE_BOUND.json', dict(source=str(source), source_sha256=sha(reference),
        frozen_copy=str(reference), config_sha256=sha(output / 'CONFIG_R203.json'),
        bound_unix=time.time(), parent_private_only=True, no_new_child_publication=True))


def serve(output=None):
    output = Path(output) if output is not None else OWN / 'new_parent_C'
    with single_parent(output):
        return serve_locked(output)


def serve_locked(output):
    config_path = output / 'CONFIG_R203.json'
    if not config_path.exists():
        config_path = output / 'CONFIG.json'
    config = read(config_path)
    policy = runtime()
    policy.validate(config)
    original_prompt = policy.prompt

    def precise_prompt(*arguments, **keywords):
        instruction, payload = original_prompt(*arguments, **keywords)
        snapshot = arguments[1]
        child_indices = [event['record_index'] for event in snapshot['events'] if event['actor'] == 'child']
        instruction += ('\nSerializer reminder, not a change to parenting style or validation: '
            'object_id must match [a-z0-9][a-z0-9_-]{0,95}; lowercase letters only, including variable names. '
            'Keep existing delivered IDs unchanged. When disposition is continue, next_task MUST be null '
            'and continuity MUST be absent. Put responsive questions in message instead. '
            'Only set_aside uses next_task and continuity, with the existing exact evidence requirements. '
            f'Allowed source_records indices are ONLY these child RESPONSE indices: {child_indices}. '
            'Do not put environment, Tool, REQUEST or COMMIT record indices in source_records. '
            'Perception must quote a supplied child event with its exact RESPONSE index and hash. '
            'Do not claim tool success without its actual receipt. Silence remains allowed.')
        return evidence_prompt(instruction, payload, snapshot)

    policy.prompt = precise_prompt
    attempts = output / 'turns'
    attempts.mkdir(exist_ok=True)
    write(output / ('STARTED_' + str(time.time_ns()) + '.json'), dict(pid=os.getpid(), started_unix=time.time(),
        arm=config['r175_arm'], cadence=config['cadence_responses'], words=config['r175_word_limit'],
        original_C2_access=False, actual_policy=policy.__file__,
        config_path=str(config_path), config_sha256=sha(config_path)))
    reference = None
    seed = read(output / 'SEED.json') if (output / 'SEED.json').exists() else None
    while time.time() < WALL:
        observation = remote(dict(op='poll', reference=reference))
        reference = observation['reference']
        state = observation['snapshot']
        if observation['withdrawal_closed'] or observation['completed_cycle'] >= 54:
            if not (output / 'WITHDRAWN.json').exists():
                write(output / 'WITHDRAWN.json', dict(observed_unix=time.time(), cycle=observation['completed_cycle'],
                    status='NO_FURTHER_PARENT_PUBLICATIONS', final_reference=reference))
            return
        if observation['first_input_rendered'] and not observation['opening_published']:
            publication = remote(dict(op='opening'))
            write(output / 'OPENING.json', dict(publication=publication, observed_unix=time.time(),
                operator_intro_not_model_response=True))
        if observation['opening_rendered']:
            if seed is None:
                seed = dict(schema='R166_PARENT_SUCCESSOR_V1', journal_id=state['journal_id'], attempts=[],
                    object_delivered_turns={}, last_response_count=state['response_count'],
                    last_request_count=state['request_count'], prospective_request_count=state['request_count'],
                    credits={}, grammar_delivered=False)
                write(output / 'SEED.json', seed)
            status = tick_once(policy, REPO, config, attempts, seed, state)
            if status['status'] not in ('WAITING_FOR_NEW_CHILD_BOUNDARY', 'AWAITING_RENDER',
                                       'EXISTING_BOUNDARY_ATTEMPT_PRESERVED'):
                write(output / ('STATUS_' + str(time.time_ns()) + '.json'), status)
        time.sleep(3)


if __name__ == '__main__':
    {'prepare': prepare, 'serve': serve, 'bind_clean_reference': bind_clean_reference}[sys.argv[1]]()
