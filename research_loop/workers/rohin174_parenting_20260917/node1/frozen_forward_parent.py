"""Prospective R178 A/1 parenting only; frozen children and their no-sleep conditions are not changed."""

import argparse
import json
import os
from pathlib import Path
import time

from forward_parent import bind
from inventory_node1 import Reader, digest, require
from parent_custody import write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    arguments = parser.parse_args()
    spec = json.loads(Reader().raw(arguments.spec))
    require(spec['physical'] in (0, 1) and spec['arm'] == 'A'
            and spec['phase'] == 'R178_PROSPECTIVE_FROZEN_PARENT_CURRICULUM', 'explicit_two_control_parent_scope')
    parent, unused_config, unused_selected = bind(spec, arguments.spec)
    original_prompt = parent['prompt']

    def prompt(config, state):
        instruction, payload = original_prompt(config, state)
        marker = '\nThe common Rohin/Fable observation-to-action introduction has already been published.'
        require(instruction.count(marker) == 1, 'replace_only_inapplicable_learning_baseline_note')
        instruction = instruction.split(marker, 1)[0]
        instruction += ('\nThis is a prospective parent-curriculum phase. At the first actual turn give one concise '
                        'observation-to-action invitation grounded in the latest child object; after that continue '
                        'the object without repeating an introduction. The two frozen controls did not receive the '
                        'common Fable baseline. No training, sleep, adapter change, or matched prior curriculum is '
                        'implied. Do not claim weight learning or fabricate a result. Retain all existing attribution '
                        'and masking; give genuine object-grounded help at each response boundary.\n')
        return instruction, payload

    parent['prompt'] = prompt
    write(arguments.spec.parent / 'RUNNER_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
          phase=spec['phase'], child_actions=0, spec_sha256=digest(Reader().raw(arguments.spec))))
    parent['serve'](Path(spec['config']), Path(spec['repository']), Path(spec['output']))


if __name__ == '__main__':
    main()
