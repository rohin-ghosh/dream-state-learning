"""Parent-text-only effort questions; existing arm, provider and publication guards."""

import argparse
import ast
import json
import os
from pathlib import Path
import time

from forward_parent import bind as forward_bind
from inventory_node1 import Reader, digest, require
from parent_custody import write
from parent_runner import compile_parent, receiving_cpu


POLICY = 'R184_THINK_ACT_EFFORT_QUESTIONS_V1'
INSTRUCTION = (
    '\nR184_THINK_ACT_EFFORT_QUESTIONS_V1 (private policy label; do not show the label). '
    'At the next eligible parent turn, continue the actual object in the latest visible child response. '
    'Do not repeat any introduction or common baseline; preserve pending attributed messages. '
    'Ask both directions: would more thinking resolve a specific uncertainty, or would a small attempt '
    'provide better evidence? Do not automatically push action: sometimes invite staying with the '
    'question when further thought could settle something, and ask what it could settle. '
    'Include three grounded action/carry questions: What thinking or doing step do you choose next? '
    'What observation would make you change that choice? What finding, uncertainty and unfinished next '
    'step will you carry into the following turn? Ask these questions; never answer them for the child, '
    'supply a solution or invent an outcome. Keep your actual child-facing message entirely questions '
    'within the existing arm word/byte cap. This eligible effort-question turn requires speak=true, '
    'not a silent no-op; all schema, visibility, object-budget and safety validators still apply. '
    'Publication alone never means the child read a message.\n'
)


def effort_loop(raw, filename, cursor, first_cadence):
    require(type(first_cadence) is int and first_cadence in (1, 2, 3), 'existing_first_turn_cadence')
    tree = ast.parse(raw, filename)
    serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
    matches = [node for node in ast.walk(serve) if isinstance(node, ast.If) and
               ast.unparse(node.test) == "state['response_count'] < max(1, last_count + config['cadence_responses'])"]
    require(len(matches) == 1, 'exact_existing_response_guard')
    matches[0].test = ast.parse("state['response_count'] < max(1, last_count + (" + str(first_cadence)
        + " if calls == 0 else config['cadence_responses']))", mode='eval').body
    return compile_parent(ast.unparse(ast.Module(body=[serve], type_ignores=[])), filename, cursor)


def bind(spec, path):
    parent, config, selected = forward_bind(spec, path)
    exec(effort_loop(Reader().raw(spec['legacy_source']).decode(), spec['legacy_source'],
                    spec['reserved_response_count'], spec['r184_first_cadence']), parent)
    previous_prompt, previous_publish = parent['prompt'], parent['publish']

    def prompt(actual_config, state):
        instruction, payload = previous_prompt(actual_config, state)
        if spec['physical'] in (0, 1):
            marker = '\nThe common Rohin/Fable observation-to-action introduction has already been published.'
            require(instruction.count(marker) == 1, 'exact_learning_only_note')
            instruction = instruction.split(marker, 1)[0]
            instruction += ('\nThis frozen control already has prospective parent prompts published; do not '
                            'repeat an introduction or imply they were rendered. Frozen/no-adapter/no-sleep '
                            'conditions are unchanged; do not claim matched historical curriculum.\n')
        return instruction + INSTRUCTION, payload

    def publish(repository, actual_config, message):
        publication = previous_publish(repository, actual_config, message)
        write(Path(spec['output']).parent / ('R184_PARENT_TURN_' + publication['id'] + '.json'),
              dict(policy=POLICY, policy_sha256=digest(INSTRUCTION.encode()), publication=publication,
                   message=message, message_sha256=digest(message.encode()), observed_unix=time.time(),
                   question_marks=message.count('?'), provider_output=True, request_exposure_verified=False))
        return publication

    parent['prompt'], parent['publish'] = prompt, publish
    return parent, config, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    spec = json.loads(Reader().raw(arguments.spec))
    require(spec['physical'] in range(8) and spec['r184_effort_policy'] == POLICY, 'node1_parent_only_policy')
    parent, config, selected = bind(spec, arguments.spec)
    if arguments.preflight:
        from gpu import orch_route_parent_campaign_providers as provider
        checks = receiving_cpu(parent, config, provider, dict(selected, cadence=spec['r184_first_cadence']), spec)
        print(json.dumps(dict(status='PASS', checks=checks, policy=POLICY, cpu_fixture_only=True)))
        return
    write(arguments.spec.parent / 'RUNNER_STARTED.json', dict(pid=os.getpid(), policy=POLICY,
          observed_unix=time.time(), spec_sha256=digest(Reader().raw(arguments.spec)), child_actions=0))
    parent['serve'](Path(spec['config']), Path(spec['repository']), Path(spec['output']))


if __name__ == '__main__':
    main()
