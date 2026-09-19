"""Fixed synthetic32 diagnostic; CPU scoring only, never a broad benchmark.

Public runner API: tasks(), messages(task), score(task, raw), digest(value).
Private task oracles must never be serialized into model messages. Code uses
the existing capability-free interpreter; tool calls are JSON comparisons only.

capture(task, arm, response, checkpoint_sha256=..., base_sha256=...,
        lora_enabled=...) creates a reducer record. Arms are ON/OFF. A normal
response contains raw, messages, token_ids, terminal, truncated, prompt_tokens,
and max_new_tokens; context and eos_token_id are optional additional checks.
None records missing execution; an error dictionary can retain partial output.
reduce_paired(records, checkpoint_sha256=..., base_sha256=...,
              max_new_tokens=...) recomputes outcomes, preserving missing cells.

The native runner owns genuine disable_adapter behavior, fresh process custody,
before/after weight hashes, caps, and allocation. Matching reported metadata is
not independent proof of those runtime properties. No training/held datasets,
parents, provider calls, native execution, or semantic thinking heuristics here.
"""

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
import re

from organism_v6 import orch_code_bounded as bounded_code


SCHEMA = 'ORCH_R107_CAPABILITY_V1'
FAMILIES = ('code', 'math', 'toolcall', 'concise_instruction')
ARMS = ('ON', 'OFF')
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
BASE_SHA256 = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SOURCE = 'FIXED_SYNTHETIC_DIAGNOSTIC_NOT_TRAIN'
CAPS = (512, 1536)
TOOL_SCHEMAS = {
    'weather': {'city': 'string', 'unit': ['C', 'F']},
    'convert': {'value': 'number', 'from_unit': ['km', 'm', 's', 'min'],
                'to_unit': ['km', 'm', 's', 'min']},
    'search_documents': {'query': 'string', 'limit': 'integer1to5'},
    'set_timer': {'seconds': 'integer1to3600', 'label': 'string'},
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _messages(task):
    return [dict(role='user', content=task['prompt'])]


def _task(family, index, prompt, oracle):
    result = dict(id=f'R107_{family.upper()}_{index:02d}', family=family, prompt=prompt,
                  oracle=oracle, source=SOURCE, trainingAllowed=False)
    result['content_sha256'] = digest(result)
    result['prompt_sha256'] = digest(_messages(result))
    return result


def tasks():
    """Return a fresh, fixed list of32 tasks, with private machine oracles."""
    code_specs = [
        ('Return the square of value.', ['value'],
         [({'value': -3}, 9), ({'value': 0}, 0), ({'value': 4}, 16), ({'value': 11}, 121)]),
        ('Return the absolute difference between left and right.', ['left', 'right'],
         [({'left': -5, 'right': 3}, 8), ({'left': 8, 'right': -2}, 10),
          ({'left': 4, 'right': 4}, 0), ({'left': 0, 'right': -7}, 7)]),
        ('Return the sum of even integers in values; an empty sum is zero.', ['values'],
         [({'values': []}, 0), ({'values': [1, 2, 3, 4]}, 6),
          ({'values': [-4, -1, 0, 6]}, 2), ({'values': [2, 2, 3]}, 4)]),
        ('Return values as a list in ascending order, preserving duplicates.', ['values'],
         [({'values': []}, []), ({'values': [3, -1, 3, 0]}, [-1, 0, 3, 3]),
          ({'values': [7]}, [7]), ({'values': [5, 2, 1]}, [1, 2, 5])]),
        ('Clamp value to the inclusive interval [lower, upper].', ['value', 'lower', 'upper'],
         [({'value': -4, 'lower': -2, 'upper': 5}, -2),
          ({'value': 8, 'lower': -2, 'upper': 5}, 5),
          ({'value': 3, 'lower': -2, 'upper': 5}, 3),
          ({'value': 2, 'lower': 2, 'upper': 2}, 2)]),
        ('Return the list values in reverse order.', ['values'],
         [({'values': []}, []), ({'values': [1, 4, 2]}, [2, 4, 1]),
          ({'values': [-2]}, [-2]), ({'values': [5, 5, 0]}, [0, 5, 5])]),
        ('Count entries in values that are greater than or equal to threshold.', ['values', 'threshold'],
         [({'values': [], 'threshold': 2}, 0), ({'values': [1, 2, 2, 4], 'threshold': 2}, 3),
          ({'values': [-3, -1, 0], 'threshold': -1}, 2), ({'values': [1, 1], 'threshold': 5}, 0)]),
        ('Return the dot product of equal-length lists left_values and right_values; empty lists yield zero.',
         ['left_values', 'right_values'],
         [({'left_values': [], 'right_values': []}, 0),
          ({'left_values': [1, 2], 'right_values': [3, 4]}, 11),
          ({'left_values': [-2, 5, 0], 'right_values': [4, -1, 9]}, -13),
          ({'left_values': [3], 'right_values': [7]}, 21)]),
    ]
    result = []
    for index, (text, arguments, cases) in enumerate(code_specs):
        prompt = text + '\nArguments: ' + ', '.join(arguments) + '.\n'
        prompt += ('Return only a JSON object with one string key "expression". '
                   'Use a bounded expression, not a function definition. Allowed: numeric literals, '
                   'arithmetic, comparisons, conditional expressions, lists, indexing/slicing, '
                   'one-generator list comprehensions, and calls sum,min,max,len,abs,sorted,range. '
                   'No attributes, imports, strings inside the expression, or arbitrary calls.')
        result.append(_task('code', index, prompt,
            dict(arguments=arguments, cases=[dict(inputs=inputs, expected=expected) for inputs, expected in cases])))
    math_specs = [('Compute 17 + 28.', '45'), ('Compute 94 - 37.', '57'),
        ('Compute 13 * 7.', '91'), ('Compute 144 / 12.', '12'),
        ('What is 15 percent of 80?', '12'), ('Compute 3/4 + 5/8.', '11/8'),
        ('A vehicle covers 126 kilometers in 3 hours. What is its average speed in kilometers per hour?', '42'),
        ('Five identical notebooks cost 35 credits. How many credits do three cost?', '21')]
    for index, (text, answer) in enumerate(math_specs):
        result.append(_task('math', index, text + '\nReply with only the number (integer, decimal, or fraction).',
                            dict(answer=answer)))
    tool_specs = [
        ('Get weather in Oslo in Celsius.', 'weather', dict(city='Oslo', unit='C')),
        ('Get weather in Kyoto in Fahrenheit.', 'weather', dict(city='Kyoto', unit='F')),
        ('Convert 2.5 kilometers to meters.', 'convert', dict(value=2.5, from_unit='km', to_unit='m')),
        ('Convert 180 seconds to minutes.', 'convert', dict(value=180, from_unit='s', to_unit='min')),
        ('Search documents for lunar geology and return at most 3 results.', 'search_documents', dict(query='lunar geology', limit=3)),
        ('Search documents for amber protocol and return at most 1 result.', 'search_documents', dict(query='amber protocol', limit=1)),
        ('Set a timer for 2 minutes labelled tea.', 'set_timer', dict(seconds=120, label='tea')),
        ('Set a timer for 45 seconds labelled stretch.', 'set_timer', dict(seconds=45, label='stretch')),
    ]
    for index, (request, tool, arguments) in enumerate(tool_specs):
        prompt = ('Mock tools (argument schemas): ' + json.dumps(TOOL_SCHEMAS, separators=(',', ':')) +
                  '\n' + request + '\nReturn only JSON {"tool":"name","arguments":{...}}; no extra keys. Do not execute anything.')
        result.append(_task('toolcall', index, prompt, dict(tool=tool, arguments=arguments)))
    short_specs = [
        ('Write blue in uppercase. Output only the resulting word, with no whitespace or punctuation.', 'BLUE'),
        ('Write ORBIT in lowercase. Output only the resulting word, with no whitespace or punctuation.', 'orbit'),
        ('Reverse the letters in drawer. Output only the resulting word, with no whitespace or punctuation.', 'reward'),
        ('Return the first three letters of planet, with no other characters.', 'pla'),
        ('From cedar, birch, maple, return only the second item, with no whitespace or punctuation.', 'birch'),
        ('Sort 8, 2, 5 in ascending order. Output only the numbers separated by commas, without whitespace.', '2,5,8'),
        ('Write the initials of quiet silver river in uppercase, without separators or other characters.', 'QSR'),
        ('Remove all hyphens from re-do-able. Output only the resulting word, with no whitespace or punctuation.', 'redoable'),
    ]
    for index, (prompt, answer) in enumerate(short_specs):
        result.append(_task('concise_instruction', index, prompt, dict(answer=answer)))
    return result


def _validate_task(task):
    require(isinstance(task, dict), 'task_dictionary_required')
    expected = next((item for item in tasks() if item['id'] == task.get('id')), None)
    require(expected is not None and digest(task) == digest(expected), 'fixed_task_content_or_hash_drift')


def messages(task):
    """Only this public projection, never task/oracle JSON, enters the model."""
    _validate_task(task)
    return _messages(task)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def _json(raw):
    def reject_constant(value):
        raise ValueError('nonfinite_json_constant:' + value)
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=reject_constant)


def _equal(actual, expected):
    if type(expected) is bool or type(actual) is bool:
        return type(actual) is type(expected) and actual == expected
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _equal(left, right) for left, right in zip(actual, expected))
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            _equal(actual[key], value) for key, value in expected.items())
    return actual == expected


def _tool_schema(document):
    if not isinstance(document, dict) or set(document) != {'tool', 'arguments'}:
        return False
    tool, arguments = document['tool'], document['arguments']
    if not isinstance(tool, str) or tool not in TOOL_SCHEMAS or not isinstance(arguments, dict):
        return False
    schema = TOOL_SCHEMAS[tool]
    if set(arguments) != set(schema):
        return False
    for name, kind in schema.items():
        value = arguments[name]
        if isinstance(kind, list):
            valid = isinstance(value, str) and value in kind
        elif kind == 'string':
            valid = isinstance(value, str) and 0 < len(value) <= 200
        elif kind == 'number':
            valid = type(value) in (int, float) and abs(value) <= 1e12 and math.isfinite(value)
        else:
            valid = type(value) is int and 1 <= value <= (5 if kind == 'integer1to5' else 3600)
        if not valid:
            return False
    return True


def score(task, raw):
    """Score response text only; completion/truncation gating is in capture."""
    _validate_task(task)
    require(isinstance(raw, str), 'raw_string_required')
    if not raw.strip():
        return dict(passed=False, category='missing_answer')
    if len(raw) > 131072:
        return dict(passed=False, category='output_size_limit')
    family, oracle = task['family'], task['oracle']
    if family == 'concise_instruction':
        passed = raw == oracle['answer']
        return dict(passed=passed, category='correct' if passed else 'exact_constraint_failure',
                    exact_characters_required=True)
    if family == 'math':
        text = raw.strip()
        if len(text) > 64 or not re.fullmatch(r'[+-]?(?:\d+/\d+|\d+(?:\.\d*)?|\.\d+)', text):
            return dict(passed=False, category='invalid_numeric_format')
        try:
            answer = Fraction(text)
        except (ValueError, ZeroDivisionError):
            return dict(passed=False, category='invalid_numeric_format')
        passed = answer == Fraction(oracle['answer'])
        return dict(passed=passed, category='correct' if passed else 'wrong_answer', parsed_number=str(answer))
    try:
        document = _json(raw)
    except (ValueError, RecursionError):
        return dict(passed=False, category='invalid_json')
    if family == 'toolcall':
        if not _tool_schema(document):
            return dict(passed=False, category='invalid_tool_schema', schema_valid=False, mock_only=True)
        passed = _equal(document, oracle)
        return dict(passed=passed, category='correct' if passed else 'wrong_tool_or_arguments',
                    schema_valid=True, mock_only=True)
    if not isinstance(document, dict) or set(document) != {'expression'} or not isinstance(document['expression'], str):
        return dict(passed=False, category='invalid_expression_schema')
    passed_cases = 0
    try:
        bounded_code.validate_expression(document['expression'])
        for case in oracle['cases']:
            observed = bounded_code.evaluate(document['expression'], deepcopy(case['inputs']))
            passed_cases += int(_equal(observed, case['expected']))
    except (ValueError, SyntaxError, TypeError, KeyError, ArithmeticError, IndexError, RecursionError):
        return dict(passed=False, category='unsafe_or_invalid_expression', passed_cases=passed_cases,
                    total_cases=len(oracle['cases']), arbitrary_execution=False)
    passed = passed_cases == len(oracle['cases'])
    return dict(passed=passed, category='correct' if passed else 'wrong_answer',
                passed_cases=passed_cases, total_cases=len(oracle['cases']), arbitrary_execution=False)


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _response_result(task, response):
    unknown = dict(generated_tokens=None, content_tokens=None, prompt_tokens=None)
    if response is None:
        return dict(completion='missing', category='missing', passed=False, machine_outcome=None,
                    generation_metrics=unknown)
    require(isinstance(response, dict), 'response_dictionary_required')
    failed = 'error' in response
    tokens = response.get('token_ids')
    if tokens is None and failed:
        return dict(completion='execution_error', category='execution_error', passed=False,
                    machine_outcome=None, generation_metrics=unknown)
    require(isinstance(tokens, list) and all(type(token) is int and token >= 0 for token in tokens), 'native_token_ids_required')
    require(type(response.get('terminal')) is bool and type(response.get('truncated')) is bool, 'native_completion_flags_required')
    terminal, truncated = response['terminal'], response['truncated']
    require(not (terminal and truncated) and (not terminal or bool(tokens)), 'inconsistent_completion_flags')
    require(type(response.get('max_new_tokens')) is int and response['max_new_tokens'] in CAPS and
            len(tokens) <= response['max_new_tokens'], 'native_cap_violation')
    require(not truncated or len(tokens) == response['max_new_tokens'], 'truncation_cap_mismatch')
    if not failed:
        require(truncated == (not terminal and len(tokens) == response['max_new_tokens']), 'truncation_flag_mismatch')
    require(type(response.get('prompt_tokens')) is int and response['prompt_tokens'] > 0, 'prompt_token_count_required')
    require(response.get('messages') == messages(task), 'exact_prompt_mismatch')
    if 'context' in response:
        require(type(response['context']) is int and
            response['prompt_tokens'] + len(tokens) <= response['context'] <= 32768, 'native_context_violation')
    if 'eos_token_id' in response:
        eos = response['eos_token_id']
        require(type(eos) is int and eos >= 0 and
            (tokens[-1:] == [eos]) == terminal and eos not in tokens[:-1], 'native_eos_mismatch')
    metrics = dict(generated_tokens=len(tokens), content_tokens=len(tokens) - int(terminal),
                   prompt_tokens=response['prompt_tokens'])
    if failed:
        return dict(completion='execution_error', category='execution_error', passed=False,
                    machine_outcome=None, generation_metrics=metrics)
    require(isinstance(response.get('raw'), str), 'native_raw_required')
    outcome = score(task, response['raw'])
    completion = 'truncated' if truncated else 'complete' if terminal else 'incomplete'
    return dict(completion=completion, category=outcome['category'] if completion == 'complete' else completion,
                passed=completion == 'complete' and outcome['passed'], machine_outcome=outcome,
                generation_metrics=metrics)


def capture(task, arm, response, *, checkpoint_sha256, base_sha256, lora_enabled):
    _validate_task(task)
    require(arm in ARMS and type(lora_enabled) is bool and lora_enabled == (arm == 'ON'), 'ON_OFF_control_mismatch')
    require(_hash(checkpoint_sha256) and base_sha256 == BASE_SHA256, 'frozen_checkpoint_base_binding_required')
    return dict(schema=SCHEMA, suite_sha256=digest(tasks()), task_id=task['id'], family=task['family'], arm=arm,
        task_sha256=task['content_sha256'], prompt_sha256=task['prompt_sha256'], checkpoint_sha256=checkpoint_sha256,
        base_sha256=base_sha256, lora_enabled=lora_enabled, response=deepcopy(response),
        response_sha256=digest(response), result=_response_result(task, response), thinking_metrics=None)


def _summarize(rows):
    results = [row['result'] for row in rows]
    counts = Counter(result['completion'] for result in results)
    metrics = [result['generation_metrics'] for result in results]
    return dict(denominator=len(rows), recorded=sum(row['recorded'] for row in rows),
        completion_counts={status: counts[status] for status in ('complete', 'missing', 'execution_error', 'incomplete', 'truncated')},
        outcome_categories=dict(Counter(result['category'] for result in results)),
        passed=sum(result['passed'] for result in results), all_responses_complete=counts['complete'] == len(rows),
        generation_metrics={key: dict(known_sum=sum(item[key] for item in metrics if item[key] is not None),
            known_count=sum(item[key] is not None for item in metrics), unknown_count=sum(item[key] is None for item in metrics))
            for key in ('generated_tokens', 'content_tokens', 'prompt_tokens')})


def reduce_paired(records, *, checkpoint_sha256, base_sha256, max_new_tokens):
    """Recompute every supplied row; reject extras/duplicates or control drift.

All32tasks remain in each arm denominator. Discordance tables use complete
pairs only; missing/error/truncated pairs never become both-wrong observations.
Token counts assume a terminal response includes one EOS; supplying eos_token_id
also verifies that flag against IDs. Raw decoding itself belongs to the runner.
"""
    require(_hash(checkpoint_sha256) and base_sha256 == BASE_SHA256 and
            type(max_new_tokens) is int and max_new_tokens in CAPS, 'fixed_pair_configuration_required')
    suite = tasks()
    by_id = {task['id']: task for task in suite}
    indexed = {}
    for row in records:
        require(isinstance(row, dict) and row.get('task_id') in by_id and row.get('arm') in ARMS, 'unknown_task_or_arm')
        key = (row['task_id'], row['arm'])
        require(key not in indexed, 'duplicate_pair_cell_no_retry_selection')
        require(row.get('checkpoint_sha256') == checkpoint_sha256 and row.get('base_sha256') == base_sha256,
                'paired_identity_mismatch')
        response = row.get('response')
        if response is not None and 'max_new_tokens' in response:
            require(type(response['max_new_tokens']) is int and response['max_new_tokens'] == max_new_tokens,
                    'paired_budget_mismatch')
        expected = capture(by_id[key[0]], key[1], response, checkpoint_sha256=checkpoint_sha256,
                           base_sha256=base_sha256, lora_enabled=row.get('lora_enabled'))
        require(digest(row) == digest(expected), 'record_hash_or_outcome_drift')
        indexed[key] = row
    cells, pairs = [], []
    for task in suite:
        pair = {}
        for arm in ARMS:
            row = indexed.get((task['id'], arm))
            result = row['result'] if row is not None else _response_result(task, None)
            cell = dict(task_id=task['id'], family=task['family'], arm=arm, recorded=row is not None, result=result)
            cells.append(cell)
            pair[arm] = cell
        prompt_counts = [pair[arm]['result']['generation_metrics']['prompt_tokens'] for arm in ARMS]
        if all(count is not None for count in prompt_counts):
            require(prompt_counts[0] == prompt_counts[1], 'paired_prompt_token_mismatch')
        responses = [indexed.get((task['id'], arm), {}).get('response') for arm in ARMS]
        if all(isinstance(response, dict) and 'error' not in response for response in responses):
            for field in ('context', 'eos_token_id'):
                require(responses[0].get(field) == responses[1].get(field), 'paired_decode_configuration_mismatch')
        complete = all(pair[arm]['result']['completion'] == 'complete' for arm in ARMS)
        on_pass, off_pass = (pair[arm]['result']['passed'] for arm in ARMS)
        category = ('both_pass' if on_pass and off_pass else 'ON_only' if on_pass else
                    'OFF_only' if off_pass else 'both_fail') if complete else 'incomplete_pair'
        pairs.append(dict(task_id=task['id'], family=task['family'], complete=complete, category=category))

    def group(family=None):
        selected = [cell for cell in cells if family is None or cell['family'] == family]
        selected_pairs = [pair for pair in pairs if family is None or pair['family'] == family]
        counts = Counter(pair['category'] for pair in selected_pairs)
        return dict(arms={arm: _summarize([cell for cell in selected if cell['arm'] == arm]) for arm in ARMS},
            pairs=dict(denominator=len(selected_pairs), complete=sum(pair['complete'] for pair in selected_pairs),
                counts={name: counts[name] for name in ('both_pass', 'ON_only', 'OFF_only', 'both_fail', 'incomplete_pair')}))

    return dict(schema=SCHEMA, model_id=MODEL_ID, source=SOURCE, suite_sha256=digest(suite),
        checkpoint_sha256=checkpoint_sha256, base_sha256=base_sha256, max_new_tokens=max_new_tokens,
        expected_cells=64, recorded_cells=len(indexed), all_cells_recorded=len(indexed) == 64,
        all_pairs_complete=all(pair['complete'] for pair in pairs), overall=group(),
        families={family: group(family) for family in FAMILIES}, task_pairs=pairs,
        thinking_metrics=None, claim_boundary='Fixed synthetic32 diagnostic only; no broad capability, semantic thinking, training or causal-generalization proof.')
