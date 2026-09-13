"""Fixed CPU practice material; no model, launcher, selection, or training interface."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

from organism_v6 import rulegame, rulegame_parenting_diagnostic as spec, rulegame_process_material as process

SCHEMA = 'birth_protocol_practice16_v1_20260913'
ORIGIN = 'SOURCE_AUTHORED_PROTOCOL_PRACTICE_NOT_CLEAN'
STATES = ('OFF', 'AUTH')
FAMILIES = ('try_serialization', 'quiz_format', 'record', 'revision')
require = spec.require


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _triple(values):
    return ','.join(map(str, values))


def _execution(public):
    parsed = spec.parse_action(public['previous_wake'], 'interaction_v3')
    match = re.fullmatch(r'the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)', public['outcome'])
    require(parsed['kind'] == 'try' and match is not None and parsed['values'] == list(map(int, match.groups()[1:])), 'public action/outcome mismatch')
    return dict(parsed, eid=public['id'], tick=1, outcome=public['outcome'], observed=match[1] == 'True')


def _target(public):
    family = public['family']
    if family == 'record':
        execution = _execution(public)
        predicted, observed = execution['predicted'], execution['observed']
        relation = 'unavailable' if predicted is None else 'matched' if predicted == observed else 'mismatched'
        return json.dumps({'try': execution['values'], 'observed': observed, 'predicted': predicted, 'relation': relation}, separators=(',', ':'))
    if family == 'quiz_format':
        return 'ACT: QUIZ '+(','.join(public['supplied_labels']) if public['revealed'] else '?')
    values = public['values']
    require(family != 'revision' or values == _execution(public)['values'], 'revision must repeat observed triple')
    forecast = _execution(public)['observed'] if family == 'revision' else public['supplied_forecast']
    return f"PREDICT: {'T' if forecast else 'F'}\nACT: TRY {_triple(values)}"


def _context(public):
    family = public['family']
    if family == 'record':
        return spec.record_prompt(_execution(public), public['previous_wake'], 'interaction_v3')
    intro = f"Protocol practice {public['id']}. No external memory. Emit only the requested canonical line(s).\n"
    if family == 'try_serialization':
        body = f"Serialize supplied forecast {'T' if public['supplied_forecast'] else 'F'} for supplied triple {_triple(public['values'])}.\nThis supplied forecast is not a claim about a hidden rule. Put PREDICT before ACT: TRY."
    elif family == 'revision':
        body = f"Earlier response:\n{public['previous_wake']}\n[OUTCOME] {public['outcome']}\nRepeat exactly the previously observed triple {_triple(public['values'])}; predict its observed result before acting. This repeat is not a claim of informative exploration."
    elif public['revealed']:
        body = f"Earlier response: ACT: QUIZ ?\n[OUTCOME] {public['reveal_outcome']}\nSupplied ordered labels: {','.join(public['supplied_labels'])}.\nSerialize these labels only; this scaffold does not test induction or quiz accuracy."
    else:
        body = 'Request the quiz reveal now; do not supply labels or make another TRY.'
    state = ('Quiz already revealed; submit six T/F labels with ACT: QUIZ.' if public['revealed'] else 'Quiz reveal still needed before scoring: ACT: QUIZ ?.')
    return intro+body+f"\nHarness state: remaining TRY budget: {public['remaining_tries']}. "+state+'\nEmit one action only; never supply [OUTCOME] or simulate a world reply.'


def build_candidate():
    cases = []
    def add(public, source, pair=None):
        family = public['family']
        cases.append(dict(id=public['id'], family=family, pair=pair, role='record' if family == 'record' else 'wake',
            tick=1 if family in ('record', 'try_serialization') else 2 if family == 'revision' else 5 if public['revealed'] else 4,
            public=public, context=_context(public), auth_example_target=_target(public), source=source,
            scaffolded=family in ('try_serialization', 'quiz_format'), derivation=dict(
                basis='supplied fields/state, not hidden-rule truth' if family in ('try_serialization', 'quiz_format') else
                'exact public executed action/observation/prior prediction' if family == 'record' else 'repeat public observation, never hidden-rule inference',
                input_fields=sorted(public), no_future_feedback=True, informative_choice_claim=False)))
    for index, (values, forecast) in enumerate((([2,5,8], True), ([3,6,9], False), ([-2,0,4], True), ([7,7,1], False))):
        add(dict(id=f'practice-try-{index}', family='try_serialization', values=values, supplied_forecast=forecast,
            remaining_tries=3, revealed=False), dict(kind='specification_scaffold', functions=['parse_action'], rule_index=None))
    for index in range(4):
        public = dict(id=f'practice-quiz-{index}', family='quiz_format', remaining_tries=0, revealed=index >= 2)
        source = dict(kind='specification_scaffold', functions=['parse_action', 'play_task'], rule_index=None)
        if index >= 2:
            eid = f'rule{index+4}/birth-protocol-practice-v1/quiz-{index}'
            game = rulegame.RuleGame()
            reward, outcome = game.evaluate(SimpleNamespace(eid=eid), 'QUIZ ?')
            public.update(reveal_outcome=outcome, supplied_labels=list('TFTFTF' if index == 2 else 'FTFTFT'))
            source.update(eid=eid, rule_index=index+4, functions=['RuleGame.evaluate', 'RuleGame.quiz_triples'],
                action='QUIZ ?', reward=reward, outcome=outcome, revealed_triples=[list(row) for row in game.quiz_triples(eid)])
        add(public, source)
    records = ((6, [2,1,3], True), (7, [0,9,0], True), (8, [5,1,2], None), (9, [1,2,3], None))
    revisions = ((6, [1,3,5], True, 'revision-pair-0'), (7, [1,3,5], True, 'revision-pair-0'),
                 (8, [6,1,6], False, 'revision-pair-1'), (9, [6,1,6], False, 'revision-pair-1'))
    for family, recipes in (('record', records), ('revision', revisions)):
        for index, recipe in enumerate(recipes):
            rule_index, values, prediction = recipe[:3]
            eid = f'rule{rule_index}/birth-protocol-practice-v1/{family}-{index}'
            wake = (f"PREDICT: {'T' if prediction else 'F'}\n" if prediction is not None else '')+f'ACT: TRY {_triple(values)}'
            reward, outcome = rulegame.RuleGame().evaluate(SimpleNamespace(eid=eid), f'TRY {_triple(values)}')
            public = dict(id=f'practice-{family}-{index//2 if family == "revision" else index}', family=family,
                previous_wake=wake, outcome=outcome, values=values, remaining_tries=2, revealed=False)
            add(public, dict(kind='generator_authored_public_observation', functions=['RuleGame.evaluate', 'parse_action']+(['record_prompt'] if family == 'record' else []),
                eid=eid, rule_index=rule_index, action=f'TRY {_triple(values)}', previous_wake=wake, outcome=outcome, reward=reward), recipe[3] if family == 'revision' else None)
            cases[-1]['id'] = f'practice-{family}-{index}'
    return dict(schema=SCHEMA, origin=ORIGIN, status='CPU_READY_QUEUE_NOT_LAUNCH_AUTHORIZED', cases=cases,
        sources={Path(module.__file__).name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for module in (spec, rulegame, process)},
        partition=dict(name='practice_only_v1', generator_rules=[6,7,8,9], excluded_rules=[0,1,2,3,4,5],
            outcome_based_selection=False, confirmation=False, no_claim_of_global_tuple_novelty=True),
        claims=dict(induction=False, selective_retention=False, efficacy=False, new_birth_fit=False))


def validate_output(case, text):
    public = case['public']
    require(case['family'] == public['family'], 'case/public family mismatch')
    require(case['context'] == _context(public), 'public context/derivation mismatch')
    result = dict(parser_valid=False, public_contract_correct=False, exact_target=text == _target(public), failures=[])
    try:
        if case['family'] == 'record':
            judged = spec.judge_record(text, _execution(public))
            result.update(parser_valid=isinstance(spec.decode(text), dict), public_contract_correct=judged['eligible'], failures=judged['failures'])
        else:
            parsed = spec.parse_action(text, 'interaction_v3')
            require(parsed['kind'] != 'try' or public['remaining_tries'] > 0, 'TRY budget exhausted')
            require(parsed['kind'] != 'quiz' or public['revealed'], 'quiz before reveal')
            require(parsed['kind'] != 'reveal' or not public['revealed'], 'repeated reveal')
            result['parser_valid'] = True
            if case['family'] in ('revision', 'try_serialization'):
                parsed = process.validate_wake(text, protocol=process.PROTOCOL_V2)
                expected = spec.parse_action(_target(public), 'interaction_v3')
                result['public_contract_correct'] = parsed == expected
            else:
                result['public_contract_correct'] = parsed == spec.parse_action(_target(public), 'interaction_v3')
    except (ValueError, TypeError, KeyError) as error:
        result['failures'].append(str(error))
    result['instruction_compliant'] = result['public_contract_correct'] and text.rstrip('\n') == _target(public)
    return result


def check_candidate(candidate):
    require(candidate == build_candidate(), 'fixed candidate/source/partition changed; no outcome-based replacement')
    cases = candidate['cases']
    require(Counter(row['family'] for row in cases) == dict.fromkeys(FAMILIES, 4) and len({row['id'] for row in cases}) == 16, 'fixed16 inventory')
    require(all(validate_output(row, row['auth_example_target'])['instruction_compliant'] for row in cases), 'AUTH parser/truth control failed')
    for pair in ('revision-pair-0', 'revision-pair-1'):
        rows = [row for row in cases if row['pair'] == pair]
        require(len(rows) == 2 and {row['auth_example_target'].splitlines()[0] for row in rows} == {'PREDICT: T', 'PREDICT: F'}, 'revision contrast missing')
        require({key:value for key,value in rows[0]['public'].items() if key != 'outcome'} ==
                {key:value for key,value in rows[1]['public'].items() if key != 'outcome'}, 'non-evidence revision cue changed')
    return dict(ok=True, candidate_sha256=digest(candidate), requests_per_state=16, total_requests=32, no_native_audit=True)


def call_map(candidate):
    check_candidate(candidate)
    requests = []
    for index, case in enumerate(candidate['cases']):
        role, tick = case['role'], case['tick']
        requests.append(dict(call_id=f'{index:04d}', case_id=case['id'], role=role, arm='protocol_practice', eid=case['public']['id'], tick=tick,
            prompt=case['context'], seed=spec._seed_for(case['public']['id'], tick, spec.GEN_SEED ^ (0x5A5A if role == 'record' else 0)),
            temperature=.7, max_tokens=spec.TOKENS[role], **spec.interaction_settings('interaction_v3', role)))
    return {state: deepcopy(requests) for state in STATES}


def check_outputs(candidate, outputs):
    check_candidate(candidate)
    require(set(outputs) == set(STATES) and all(set(outputs[state]) == {row['id'] for row in candidate['cases']} for state in STATES), 'all32 outputs required')
    return {state: {row['id']: validate_output(row, outputs[state][row['id']]) for row in candidate['cases']} for state in STATES}
