"""Prospective private parent prompt only; retain existing arms and clocks."""

import hashlib
import importlib.util
import json
from pathlib import Path


SCHEMA = 'R184_NODE5_EFFORT_BOTH_DIRECTIONS_V1'
TEXT = ('Parents during development ask effort questions in both directions, without '
        'answers: would more thought resolve a real uncertainty, would an attempt be '
        'more useful, or is this worth staying with? No extra parent intervention is '
        'required to enter the next cycle.')


def publication_refs(output, result):
    matches = [path for path in Path(output).glob('parent_*/RESULT.json')
               if json.loads(path.read_bytes()) == result]
    if len(matches) != 1:
        raise ValueError('R184_unique_actual_publication_receipt')
    directory = matches[0].parent
    prompt = json.loads((directory / 'PROMPT.json').read_bytes())
    if SCHEMA not in prompt['instruction'] or TEXT not in prompt['instruction']:
        raise ValueError('R184_actual_outbound_effort_prompt')
    return {name: dict(path=str(directory / filename),
        sha256=hashlib.sha256((directory / filename).read_bytes()).hexdigest())
        for name, filename in (('source','SOURCE.json'),('result','RESULT.json'),('prompt','PROMPT.json'))}


def install(policy, source):
    path = Path(source) / 'R184_EFFORT_PHASE.json'
    if not path.exists():
        return None
    phase = json.loads(path.read_bytes())
    if phase['schema'] != SCHEMA or phase['label'] not in ('C1','C3','C4','C5','run1','pilot','repo_reader'):
        raise ValueError('R184_exact_nonC2_parent_scope')
    plan = Path(source) / 'R184_FIXED_FIRST_COMPARISON.md'
    if hashlib.sha256(plan.read_bytes()).hexdigest() != phase['fixed_plan_sha256']:
        raise ValueError('R184_fixed_plan_pin')
    if TEXT not in ' '.join(plan.read_text().split()):
        raise ValueError('R184_exact_fixed_effort_paragraph')
    original = policy.prompt
    examples_path = Path(source) / 'R188_EXAMPLES_PHASE.json'
    examples = None
    examples_suffix = ''
    if examples_path.exists():
        binding = json.loads(examples_path.read_bytes())
        module_path = Path(source) / 'gpu/orch_r188_parent_examples.py'
        if hashlib.sha256(module_path.read_bytes()).hexdigest() != binding['main_module_sha256']:
            raise ValueError('R188_exact_Main_examples_source')
        specification = importlib.util.spec_from_file_location('bound_r188_examples', module_path)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        examples_suffix = module.parent_policy_suffix()
        examples = dict(marker=module.MARKER,provenance=module.PROVENANCE,
            module_sha256=binding['main_module_sha256'],phase_sha256=hashlib.sha256(examples_path.read_bytes()).hexdigest())

    def effort_prompt(config, state, memory_state):
        instruction, payload = original(config, state, memory_state)
        return instruction + '\n\n' + SCHEMA + '\n' + TEXT + examples_suffix, payload

    policy.prompt = effort_prompt
    return dict(schema=SCHEMA, phase_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        fixed_plan_sha256=phase['fixed_plan_sha256'], wrapper_file=__file__,
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_prompt_file=original.__code__.co_filename,
        cadence_word_limits_clocks_pending_and_child_unchanged=True, examples=examples)
