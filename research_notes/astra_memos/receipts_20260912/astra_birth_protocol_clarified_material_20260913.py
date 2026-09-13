"""Versioned prompt clarification; original cases, public labels and scoring remain fixed."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

BASE_PATH = Path('/tmp/astra_birth_protocol_probe_material_20260913.py')
BASE_SHA = '2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b'
if hashlib.sha256(BASE_PATH.read_bytes()).hexdigest() != BASE_SHA:
    raise ValueError('original practice material changed')
specification = importlib.util.spec_from_file_location('original_protocol_practice_material', BASE_PATH)
base = importlib.util.module_from_spec(specification)
specification.loader.exec_module(base)
spec, process, rulegame = base.spec, base.process, base.rulegame
STATES, FAMILIES, ORIGIN = base.STATES, base.FAMILIES, base.ORIGIN
SCHEMA = 'birth_protocol_practice16_clarified_v1_20260913'
CLARIFICATION = '''
Protocol clarification: perform the particular action requested above. Actions named in the harness-state reminder are not additional requests.
When asked for a forecast and a TRY (including repeating an observed triple), output exactly two lines:
PREDICT: X
ACT: TRY a,b,c
Replace X with the single letter T or F and a,b,c with the requested three integers. Use the supplied forecast, or the public observed result when repeating. Do not output X, a,b,c, function calls, TRUE/FALSE words, or a QUIZ instead of the requested TRY.
When asked to reveal an unrevealed quiz, output exactly ACT: QUIZ ?.
When asked to serialize revealed quiz labels, output ACT: QUIZ followed by the six supplied T/F letters separated by commas.
Do not omit the requested ACT line or add explanations.'''
require = base.require
digest = base.digest


def build_candidate():
    candidate = deepcopy(base.build_candidate())
    candidate['schema'] = SCHEMA
    for case in candidate['cases']:
        if case['role'] == 'wake':
            case['context'] += CLARIFICATION
    return candidate


def check_candidate(candidate):
    require(candidate == build_candidate(), 'fixed clarification changed')
    original = base.build_candidate()
    base.check_candidate(original)
    for case, old in zip(candidate['cases'], original['cases'], strict=True):
        require({key: value for key, value in case.items() if key != 'context'} ==
                {key: value for key, value in old.items() if key != 'context'}, 'case/target/source changed')
        require(base.validate_output(old, case['auth_example_target'])['instruction_compliant'], 'target invalid')
    return dict(ok=True, candidate_sha256=digest(candidate), total_requests=32, requests_per_state=16,
                modification='uniform grammar appended to twelve wake prompts; four records unchanged')


def call_map(candidate):
    check_candidate(candidate)
    requests = base.call_map(base.build_candidate())
    contexts = {case['id']: case['context'] for case in candidate['cases']}
    for state in STATES:
        for request in requests[state]:
            request['prompt'] = contexts[request['case_id']]
    return requests


def check_outputs(candidate, outputs):
    check_candidate(candidate)
    return base.check_outputs(base.build_candidate(), outputs)
