"""R115 F2 enacted environment and strict TRAIN-only contextual custody."""

import ast
from fractions import Fraction
import hashlib
import json
import operator
from pathlib import Path
import re

from organism_v6 import orch_math_feedback_uptake_r114 as previous


require, digest, sha = previous.require, previous.digest, previous.sha
ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1')
AREA = Path('research_notes/analysis') / ROOT.name
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
BOOT = '2c05ffec-1b4c-472f-9688-2a37543a6f4a'
DEVICES = {1: previous.original.MEMBERS['FABLE']['uuid'], 5: previous.original.MEMBERS['ASTRA']['uuid']}
MODELS = {1: 'claude-fable-5-1', 5: 'openai/openai/gpt-6-astra'}
JUDGE_SHA = '0466c6fa8bbd8c75f8e2d4c625498423835b2b5285e58c4f703069e8b6c532fd'
NATIVE_CAP = 1168
PARENT_CAP = 384
CYCLES = 43
ENVIRONMENT = ('The environment can return the current problem with INSPECT, or evaluate a finite arithmetic '
    'expression on a line CALCULATE: expression. It executes those requests and returns its observation. '
    'These are available actions, not requirements; you may also stop.')
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv}


def calculate(expression):
    require(isinstance(expression, str) and 0 < len(expression) <= 200, 'bounded_expression')
    tree = ast.parse(expression, mode='eval')
    require(len(list(ast.walk(tree))) <= 40, 'bounded_expression_tree')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            require(abs(node.value) <= 10**12, 'bounded_operand')
            return Fraction(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        require(isinstance(node, ast.BinOp) and type(node.op) in OPERATORS, 'arithmetic_only')
        result = Fraction(OPERATORS[type(node.op)](visit(node.left), visit(node.right)))
        require(abs(result.numerator) <= 10**24 and result.denominator <= 10**24, 'bounded_result')
        return result
    return str(visit(tree.body))


def enact(task, raw):
    matches = re.findall(r'^\s*(INSPECT|CALCULATE:\s*[^\n]+)\s*$', raw, flags=re.MULTILINE)
    observations = []
    for action in matches[:4]:
        try:
            text = task['question'] if action == 'INSPECT' else calculate(action.split(':', 1)[1].strip())
            status = 'ENACTED'
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError) as error:
            text, status = type(error).__name__ + ': invalid arithmetic request', 'ENVIRONMENT_ERROR'
        observations.append(dict(action=action, status=status, observation=text,
            action_sha256=hashlib.sha256(action.encode()).hexdigest(), source_question_sha256=task['question_sha256']))
    return observations


def event(actor, text, split, source):
    require(actor in ('child', 'parent', 'environment'), 'known_actor')
    require(split in ('TRAIN', 'DEV', 'FINAL', 'PROBE'), 'known_origin')
    return dict(actor=actor, text=text, split=split, source_sha256=digest(source))


class Experience:
    def __init__(self):
        self.events = []

    def append(self, item):
        require(item['split'] == 'TRAIN', 'readout_and_attached_open_never_buffer_or_rows')
        self.events.append(item)

    def payload(self, task, life_id, cycle, episode, phase, cohort_sha256):
        require(task['split'] == 'TRAIN', 'train_only_parent')
        return dict(schema='r111_train_public_v1', life_id=life_id, cycle=cycle, episode=episode,
            phase=phase, game='math', task_id=task['id'],
            task_provenance=dict(split='TRAIN', task_sha256=task['question_sha256'], cohort_sha256=cohort_sha256),
            events=[dict(sequence=index, actor=item['actor'], text=item['text'],
                source_sha256=item['source_sha256'], visibility='TRAIN_PUBLIC') for index, item in enumerate(self.events)])


def messages(experience, invitation, carry=None):
    result = [dict(role='system', content=previous.original.SYSTEM)]
    if carry:
        require(carry['split'] == 'TRAIN' and carry['actor'] == 'child', 'own_train_reflection_only')
        result.append(dict(role='user', content='Your recorded earlier reflection (not a verified fact):\n' + carry['text']))
    for item in experience.events:
        require(item['split'] == 'TRAIN', 'train_context_only')
        result.append(dict(role='assistant' if item['actor'] == 'child' else 'user', content=item['text']))
    result.append(dict(role='user', content=invitation))
    return result


def readout_messages(task, purpose, response=None):
    require(task['split'] in ('DEV', 'FINAL', 'PROBE'), 'readout_origin')
    if purpose == 'open_turn':
        require(response is not None, 'attached_actual_readout')
        return [dict(role='system', content=previous.original.SYSTEM),
            dict(role='user', content=task['question']), dict(role='assistant', content=response['raw']),
            dict(role='user', content=ENVIRONMENT), dict(role='user', content=previous.OPEN_TURN)]
    return previous.messages('focused' if purpose == 'focused' else 'held', task['question'])


def reflection_generate(engine, prompt, response, request, config, *, now, context_cap=8192):
    from gpu import orch_r110_claude_broker as broker
    settings = broker.reflection_call_settings(response, request, 8192, config=config, now=now)
    if settings['status'] == 'KEEP_ORIGINAL':
        settings['effective_max_new_tokens'] = config.get('fallback_parent_fields', {}).get(
            'REFLECTION', {}).get('max_new_tokens', 8192)
    cap = min(context_cap, settings['effective_max_new_tokens'])
    require(cap > 0, 'reflection_context_budget')
    return engine.generate(prompt, max_new_tokens=cap), dict(settings, actual_decoder_cap=cap)


def contract(repository):
    from gpu import orch_r110_claude_broker as broker
    result = previous.contract(repository)
    fields = json.loads((Path(repository)/'F2_INITIAL_FIELDS.json').read_text())['fields']
    result.update(schema='R115_F2_NATIVE_ELICITATION_V1', authorization='WATCHER_RELAYED_ROHIN_DONE',
        authorization_reference='R115 direct user: actual USER GO received audit complete',
        cycles=CYCLES, core_native_cap=NATIVE_CAP, parent_slot_cap=PARENT_CAP,
        sleep0_native_calls=34, native_calls_per_cycle=26, morning_final_reserved_calls=16,
        planned_native_calls=34+CYCLES*26+16, planned_parent_slots=CYCLES*6,
        final_attached_open=True, dev_attached_open=True, no_readout_into_rows_or_buffer=True,
        judge_prompt_sha256=JUDGE_SHA, actual_anchor_lambda=None,
        environment=ENVIRONMENT, environment_code_sha256=sha(__file__),
        fixed_parent_template_sha256=hashlib.sha256(broker.fixed_parent_template().encode()).hexdigest(),
        transport_contract_sha256=hashlib.sha256(broker.SYSTEM_CONTRACT.encode()).hexdigest(),
        fields_reread_each_parent_call=True, broker_reflection_settings_reach_decoder=True,
        parent_fields=fields, reflection_initial_cap=fields['REFLECTION']['max_new_tokens'],
        runtime_prompt_root='/data/home/rohing/courier/swarm/prompts',
        episode_generation_cap=2048, train_open_cap=1024, readout_open_cap=1024,
        presleep_generation_cap=4096, reflection_generation_cap=8192,
        no_context_truncation=True, context_aware_effective_generation_caps=True,
        native_runtime_implemented=True, sleep_updates_implemented=False, weight_updates=0)
    return result
