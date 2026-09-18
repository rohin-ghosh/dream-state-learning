"""Pinned R175 bundle on the actual legacy parent loop; no child lifecycle actions."""

import argparse
import ast
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest import mock


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def compile_parent(raw, filename, cursor):
    require(type(cursor) is int and cursor >= 0, 'actual_reserved_cursor')
    tree = ast.parse(raw, filename)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve']
    require(len(functions) == 1, 'one_actual_parent_loop')
    assignments = [node for node in functions[0].body if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == 'last_count']
    require(len(assignments) == 1, 'one_preserved_parent_cursor')
    assignments[0].value = ast.Call(func=ast.Name(id='max', ctx=ast.Load()),
                                  args=[assignments[0].value, ast.Constant(cursor)], keywords=[])
    return compile(ast.fix_missing_locations(tree), filename, 'exec')


def load(spec):
    for path, expected in spec['pins'].items():
        require(sha(path) == expected, 'actual_receiving_source_pin:' + path)
    bundle = Path(spec['bundle']).resolve()
    sys.path.insert(0, str(bundle))
    from gpu import orch_route_parent_campaign_providers as provider
    from gpu import orch_r175_parent_arms as arms
    require(Path(provider.__file__).resolve() == bundle / arms.PROVIDER_PATH
            and Path(arms.__file__).resolve() == bundle / 'gpu/orch_r175_parent_arms.py',
            'actual_bundle_imports_not_old_snapshot')
    config = json.loads(Path(spec['config']).read_text())
    selected = arms.specification(spec['arm'])
    require(config['r175_schema'] == arms.SCHEMA and config['r175_arm'] == spec['arm']
            and config['r175_word_limit'] == selected['words']
            and config['cadence_responses'] == selected['cadence']
            and config['schedule_on'] == 'response' and config['root'] == spec['root'],
            'exact_main_arm_cap_response_clock')
    parent = dict(__name__='r175_actual_legacy_parent', __file__=spec['legacy_source'])
    exec(compile_parent(Path(spec['legacy_source']).read_text(), spec['legacy_source'],
                        spec['reserved_response_count']), parent)
    parent['strong'] = provider.strong
    parent['STRONG'] = provider.STRONG
    prior_prompt = parent['prompt']
    instruction_addition = arms.instruction(spec['arm'])

    def prompt(actual_config, state):
        instruction, payload = prior_prompt(actual_config, state)
        return instruction + instruction_addition, payload

    parent['prompt'] = prompt
    parent['validate'](config)
    return parent, config, provider, selected


def instrument(parent, spec, selected):
    original_strong, original_publish = parent['strong'], parent['publish']
    active = {}

    def strong(payload, output, deadline, instruction):
        active['output'] = Path(output)
        withdrawal = Path(spec['output']).parent / 'PARENT_WITHDRAWAL.json'
        require(not withdrawal.exists(), 'explicit_parent_withdrawal_no_new_turn')
        return original_strong(payload, output, deadline, instruction)

    def publish(repository, actual_config, message):
        require(len(message.split()) <= selected['words'] and len(message.encode()) <= 4096,
                'actual_child_facing_cap')
        started = time.time()
        publication = original_publish(repository, actual_config, message)
        write(active['output'] / 'ARM_PUBLISHED.json', dict(arm=spec['arm'], root=spec['root'],
              policy_sha256=spec['policy_sha256'], assignment_sha256=spec['assignment_sha256'],
              parent_pid=os.getpid(), publication=publication,
              message_sha256=hashlib.sha256(message.encode()).hexdigest(),
              word_count=len(message.split()), word_cap=selected['words'], byte_count=len(message.encode()),
              publication_started_unix=started, publication_returned_unix=time.time(),
              request_exposure_verified=False, config_sha256=sha(spec['config'])))
        return publication

    parent['strong'], parent['publish'] = strong, publish


def receiving_cpu(parent, config, provider, selected, spec):
    instruction, unused = parent['prompt'](config, dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[]))
    require('ROHIN175_OBSERVATION_TO_ACTION_BASELINE_V1' in instruction, 'actual_prompt_baseline')
    require(('at most ' + str(selected['words']) + ' words') in instruction, 'actual_prompt_cap')
    if selected['words'] != 90:
        require('90-word' not in instruction and 'at most90 words' not in instruction
                and 'at most 90 words' not in instruction, 'no_operative_old_cap')
    message = ' '.join(['word'] * selected['words'])
    response = dict(speak=True, message=message, rationale='PRIVATE_CPU_FIXTURE')
    provider.response_schema(json.dumps(response))
    for invalid in (' '.join(['word'] * (selected['words'] + 1)), 'x' * 4097, '\u00e9' * 2049):
        with_exception = dict(response, message=invalid)
        try:
            provider.response_schema(json.dumps(with_exception))
        except ValueError:
            pass
        else:
            raise ValueError('actual_provider_cap_not_enforced')
    saved = dict(parent)
    checks = []
    try:
        with tempfile.TemporaryDirectory(prefix='cpu_actual_loop_', dir=Path(spec['config']).parent) as temp:
            for mode in ('reserved', 'below_cadence', 'published', 'silent', 'failed', 'publication_cap'):
                output = Path(temp) / mode
                count = spec['reserved_response_count']
                if mode == 'below_cadence':
                    count += selected['cadence'] - 1
                elif mode != 'reserved':
                    count += selected['cadence']
                state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[], consumed_inbox={},
                             response_count=count, record_count=0, head_sha256='0' * 64)
                parent.update(saved)
                parent['snapshot'] = mock.Mock(return_value=state)
                parent['remote'] = mock.Mock(side_effect=AssertionError('CPU_remote_forbidden'))
                parent['publish'] = mock.Mock(return_value=dict(id='CPU_SYNTHETIC', path='/CPU_ONLY', sha256='1' * 64))
                publication_mock = parent['publish']

                def fixture_strong(payload, directory, deadline, actual_instruction):
                    inspect.signature(provider.strong).bind(payload, directory, deadline, actual_instruction)
                    require(actual_instruction == instruction, 'actual_loop_instruction_not_default')
                    require('PRIVATE_CPU_FIXTURE' not in payload, 'private_rationale_not_in_prompt')
                    if mode == 'failed':
                        raise ValueError('CPU_explicit_failure_no_retry')
                    actual_response = dict(response)
                    if mode == 'silent':
                        actual_response.update(speak=False, message='')
                    if mode == 'publication_cap':
                        actual_response['message'] = 'x' * 4097
                    else:
                        actual_response = provider.response_schema(json.dumps(actual_response))
                    return actual_response, provider.STRONG, dict(cpu_only=True)

                parent['strong'] = mock.create_autospec(provider.strong, side_effect=fixture_strong)
                strong_mock = parent['strong']
                instrument(parent, dict(spec, output=str(output)), selected)
                parent['serve'](Path(spec['config']), Path(spec['repository']), output, once=True)
                if mode in ('reserved', 'below_cadence'):
                    require(strong_mock.call_count == 0 and not list(output.glob('parent_*')), 'cursor_cadence_no_replay')
                else:
                    result = json.loads((output / 'parent_000000/RESULT.json').read_text())
                    expected = dict(published='PUBLISHED', silent='SILENT', failed='MISSING', publication_cap='MISSING')[mode]
                    require(strong_mock.call_count == 1 and result['status'] == expected and result['retry'] is False,
                            'actual_loop_strong_signature_and_terminal:' + mode)
                    require(result['source_response_count'] == count, 'actual_response_cursor_bound')
                    require(publication_mock.call_count == int(mode == 'published'), 'bounded_single_publication')
                    if mode == 'published':
                        require(publication_mock.call_args.args[2] == message, 'only_message_published_no_private_rationale')
                        marker = json.loads((output / 'parent_000000/ARM_PUBLISHED.json').read_text())
                        require(not marker['request_exposure_verified'], 'publication_not_rendered')
                checks.append(mode)
    finally:
        parent.clear()
        parent.update(saved)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    spec = json.loads(arguments.spec.read_text())
    parent, config, provider, selected = load(spec)
    if arguments.preflight:
        checks = receiving_cpu(parent, config, provider, selected, spec)
        print(json.dumps(dict(status='PASS', execution_kind='CPU_ONLY', arm=spec['arm'],
                              word_cap=selected['words'], cadence=selected['cadence'],
                              baseline_in_actual_prompt=True, provider_calls=0, signals=0,
                              actual_loop_checks=checks, actual_strong_signature=True,
                              bundle=spec['bundle'], config_sha256=sha(spec['config']))))
        return
    directory = arguments.spec.parent
    require(not (directory / 'RUNNER_STARTED.json').exists(), 'new_parent_runner_once')
    write(directory / 'RUNNER_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
          spec_sha256=sha(arguments.spec), source_pins=spec['pins'], root=spec['root'],
          arm=spec['arm'], reserved_response_count=spec['reserved_response_count']))
    instrument(parent, spec, selected)
    parent['serve'](Path(spec['config']), Path(spec['repository']), Path(spec['output']))


if __name__ == '__main__':
    main()
