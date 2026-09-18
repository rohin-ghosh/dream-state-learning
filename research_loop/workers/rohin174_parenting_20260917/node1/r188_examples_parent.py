"""R188 reported methods on existing parent turns; never a new baseline."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import time

from inventory_node1 import Reader, digest, require
from parent_custody import write
from r184_effort_parent import bind as effort_bind
from parent_runner import receiving_cpu


POLICY_SHA = '19e813b21d2b43d3ea274eb1783d7f2a2ce0f5b703f6fda94051d5cda21c978f'
POLICY = 'R188_REPORTED_WORKED_EXAMPLES_V1'


def policy_module(path):
    require(digest(Reader().raw(path)) == POLICY_SHA, 'exact_Main_R188_examples')
    definition = importlib.util.spec_from_file_location('bound_R188_examples', path)
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    return module


def bind(spec, path):
    parent, config, selected = effort_bind(spec, path)
    policy = policy_module(spec['r188_examples_source'])
    previous_prompt, previous_publish = parent['prompt'], parent['publish']

    def prompt(actual_config, state):
        instruction, payload = previous_prompt(actual_config, state)
        return policy.append_parent_examples(instruction.encode()).decode(), payload

    def publish(repository, actual_config, message):
        publication = previous_publish(repository, actual_config, message)
        write(Path(spec['output']).parent / ('R188_PARENT_TURN_' + publication['id'] + '.json'),
            dict(policy=POLICY, policy_sha256=POLICY_SHA, publication=publication,
                 message_sha256=digest(message.encode()), observed_unix=time.time(),
                 provider_output=True, request_exposure_verified=False, baseline_introduction=False))
        return publication

    parent['prompt'], parent['publish'] = prompt, publish
    return parent, config, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    spec = json.loads(Reader().raw(arguments.spec))
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
