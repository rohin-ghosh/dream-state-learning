"""Predetermined ordinary TRAIN anchors, not held capability or richness data."""

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import re

from organism_v6 import orch_code_bounded as code
from organism_v6 import orch_r107_capability as excluded_panel


SCHEMA = 'R107_BASE_ORDINARY_ANCHORS_V1'
COHORT = 'ANCHOR_TRAIN_R107_20260915_A1'
FAMILIES = ('code', 'math', 'simulated_tools', 'concise_answer')
BASE_SHA = excluded_panel.BASE_SHA256
TOOLS = {
    'lookup_catalog': {'sku': 'string', 'warehouse': 'string'},
    'mark_priority': {'ticket': 'string', 'level': ['low', 'normal', 'urgent']},
    'plan_pickup': {'zone': 'string', 'day': 'string', 'parcels': 'positive_integer'},
    'format_report': {'topic': 'string', 'style': ['brief', 'detailed'], 'limit': 'positive_integer'},
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def code_specs():
    return [
        ('Return the cube of number.', 'number * number * number',
         [({'number': -4}, -64), ({'number': -1}, -1), ({'number': 0}, 0), ({'number': 5}, 125)]),
        ('Return the arithmetic mean of first and second.', '(first + second) / 2',
         [({'first': 2, 'second': 10}, 6), ({'first': 7, 'second': 13}, 10),
          ({'first': -4, 'second': 6}, 1), ({'first': 0, 'second': 0}, 0)]),
        ('Return the remainder when number is divided by positive divisor.', 'number % divisor',
         [({'number': 9, 'divisor': 4}, 1), ({'number': 17, 'divisor': 5}, 2),
          ({'number': 0, 'divisor': 7}, 0), ({'number': 23, 'divisor': 6}, 5)]),
        ('Return number divided by positive divisor, rounded down to an integer.', 'number // divisor',
         [({'number': 29, 'divisor': 5}, 5), ({'number': 7, 'divisor': 3}, 2),
          ({'number': 0, 'divisor': 2}, 0), ({'number': -9, 'divisor': 4}, -3)]),
        ('Return the perimeter of a rectangle with sides width and height.', '2 * (width + height)',
         [({'width': 3, 'height': 7}, 20), ({'width': 2, 'height': 9}, 22),
          ({'width': 0, 'height': 4}, 8), ({'width': 1, 'height': 1}, 4)]),
        ('Return the volume of a box with sides width, height and depth.', 'width * height * depth',
         [({'width': 2, 'height': 3, 'depth': 4}, 24), ({'width': 1, 'height': 5, 'depth': 7}, 35),
          ({'width': 0, 'height': 8, 'depth': 3}, 0), ({'width': 3, 'height': 3, 'depth': 3}, 27)]),
        ('For nonnegative number, return the sum of integers from zero through number.', 'number * (number + 1) // 2',
         [({'number': 0}, 0), ({'number': 1}, 1), ({'number': 4}, 10), ({'number': 7}, 28)]),
        ('Convert hours and additional minutes to a total number of minutes.', 'hours * 60 + minutes',
         [({'hours': 2, 'minutes': 17}, 137), ({'hours': 0, 'minutes': 8}, 8),
          ({'hours': 3, 'minutes': 0}, 180), ({'hours': 1, 'minutes': 42}, 102)]),
        ('Count strictly negative entries in numbers.', 'len([item for item in numbers if item < 0])',
         [({'numbers': [-2, 0, -5, 7]}, 2), ({'numbers': []}, 0),
          ({'numbers': [0, 1, 2]}, 0), ({'numbers': [-1, -1, -1]}, 3)]),
        ('Return the largest absolute value in numbers, or zero for an empty list.',
         'max([abs(item) for item in numbers]) if numbers else 0',
         [({'numbers': [-8, 3]}, 8), ({'numbers': []}, 0),
          ({'numbers': [2, -1, 9]}, 9), ({'numbers': [0, 0]}, 0)]),
        ('Return the sum of odd integers in numbers.', 'sum([item for item in numbers if item % 2 != 0])',
         [({'numbers': [-3, -2, 1, 4, 7]}, 5), ({'numbers': []}, 0),
          ({'numbers': [2, 4]}, 0), ({'numbers': [3, 3, 5]}, 11)]),
        ('Return a new list adding one to every entry in numbers.', '[item + 1 for item in numbers]',
         [({'numbers': [-2, 0, 4]}, [-1, 1, 5]), ({'numbers': []}, []),
          ({'numbers': [9]}, [10]), ({'numbers': [1, 1]}, [2, 2])]),
        ('Return entries at indices zero, two, four and so on from numbers.', 'numbers[::2]',
         [({'numbers': [4, 7, 1, 9, 2]}, [4, 1, 2]), ({'numbers': []}, []),
          ({'numbers': [8]}, [8]), ({'numbers': [3, 6]}, [3])]),
        ('Return the sum of integers from start through end, inclusive; start is at most end.',
         'sum(range(start, end + 1))',
         [({'start': 3, 'end': 6}, 18), ({'start': -2, 'end': 2}, 0),
          ({'start': 4, 'end': 4}, 4), ({'start': 0, 'end': 3}, 6)]),
        ('Return a new list replacing each negative entry in numbers with zero.',
         '[max(0, item) for item in numbers]',
         [({'numbers': [-3, 0, 5]}, [0, 0, 5]), ({'numbers': []}, []),
          ({'numbers': [-2, -1]}, [0, 0]), ({'numbers': [7, 8]}, [7, 8])]),
        ('Return Manhattan distance from the origin using horizontal and vertical coordinates.',
         'abs(horizontal) + abs(vertical)',
         [({'horizontal': -4, 'vertical': 3}, 7), ({'horizontal': 0, 'vertical': 0}, 0),
          ({'horizontal': 2, 'vertical': -8}, 10), ({'horizontal': -1, 'vertical': -5}, 6)]),
    ]


def task(family, index, question, prompt, oracle):
    document = dict(id=f'{COHORT}_{family.upper()}_{index:02d}', family=family,
        cohort=COHORT, split='TRAIN', question=question, prompt=prompt, oracle=oracle,
        source='PREDETERMINED_ORDINARY_TRAIN_TASK', trainingAllowed=False)
    document['question_sha256'] = digest(' '.join(question.split()).casefold())
    document['prompt_sha256'] = digest([dict(role='user', content=prompt)])
    document['content_sha256'] = digest(document)
    return document


def tasks():
    groups = {family: [] for family in FAMILIES}
    for index, (question, expression, cases) in enumerate(code_specs()):
        prompt = (question + '\nArguments: ' + ', '.join(cases[0][0]) + '.\n'
            'Respond with exactly one JSON object with a string field "expression". '
            'No Markdown, prose or function definition. Use only numeric arithmetic, comparisons, '
            'lists, indexing/slicing, one-generator list comprehensions, conditional expressions '
            'and calls sum,min,max,len,abs,range. No attributes, imports or arbitrary calls.')
        groups['code'].append(task('code', index, question, prompt,
            dict(reference_expression=expression, cases=[dict(inputs=inputs, expected=expected) for inputs, expected in cases])))
    for index in range(16):
        base = 19 + index * 3
        if index % 4 == 0:
            question = f'A hall has {base} rows of 6 seats. Exactly {base + 7} seats are reserved. How many seats remain unreserved?'
            answer = base * 6 - (base + 7)
        elif index % 4 == 1:
            question = f'A tank starts with {base} liters. It gains 7 liters per minute for 4 minutes and then loses 11 liters. How many liters remain?'
            answer = base + 28 - 11
        elif index % 4 == 2:
            question = f'A store packs {base} cartons with 8 clips each and adds 13 loose clips. How many clips are packed in total?'
            answer = base * 8 + 13
        else:
            question = f'A team has {base * 5 + 24} credits. It spends 24 credits and divides the remainder equally among 5 members. How many credits does each receive?'
            answer = base
        groups['math'].append(task('math', index, question, question + '\nReturn only the numeric answer, without units or explanation.', dict(answer=str(answer))))
    for index in range(16):
        serial = 431 + index
        if index % 4 == 0:
            question = f'Look up SKU B{serial} in warehouse west{index + 1}.'
            oracle = dict(tool='lookup_catalog', arguments=dict(sku=f'B{serial}', warehouse=f'west{index + 1}'))
        elif index % 4 == 1:
            question = f'Mark ticket T{serial} as urgent.'
            oracle = dict(tool='mark_priority', arguments=dict(ticket=f'T{serial}', level='urgent'))
        elif index % 4 == 2:
            question = f'Plan pickup in zone north{index + 1} on Tuesday for {index + 3} parcels.'
            oracle = dict(tool='plan_pickup', arguments=dict(zone=f'north{index + 1}', day='Tuesday', parcels=index + 3))
        else:
            question = f'Format a brief report on topic cedar{serial} limited to {index + 2} entries.'
            oracle = dict(tool='format_report', arguments=dict(topic=f'cedar{serial}', style='brief', limit=index + 2))
        prompt = ('These are inert simulated tools; do not execute anything. Schemas: ' +
            json.dumps(TOOLS, sort_keys=True, separators=(',', ':')) + '\nRequest: ' + question +
            '\nReturn only JSON with exactly "tool" and "arguments" keys. No Markdown or explanation.')
        groups['simulated_tools'].append(task('simulated_tools', index, question, prompt, oracle))
    words = ('harbor', 'violet', 'canyon', 'meadow', 'lantern', 'planet', 'ribbon', 'copper',
             'falcon', 'timber', 'breeze', 'velvet', 'puzzle', 'garden', 'marble', 'winter')
    for index, word in enumerate(words):
        if index % 4 == 0:
            question, answer = f'Convert {word} to uppercase.', word.upper()
        elif index % 4 == 1:
            question, answer = f'Convert {word.upper()} to lowercase.', word
        elif index % 4 == 2:
            question, answer = f'Reverse the letters of {word}.', word[::-1]
        else:
            question, answer = f'Write the first three letters of {word}.', word[:3]
        groups['concise_answer'].append(task('concise_answer', index, question,
            question + '\nOutput only the result, with no whitespace or punctuation.', dict(answer=answer)))
    return [groups[family][index] for index in range(16) for family in FAMILIES]


def exclusions(suite):
    denied = excluded_panel.tasks()
    require(len(suite) == 64 and len({row['id'] for row in suite}) == 64, 'fixed64_unique_train_tasks')
    for field in ('id', 'prompt_sha256', 'content_sha256'):
        require(not {row[field] for row in suite} & {row[field] for row in denied}, 'held_panel_overlap')
    denied_questions = {digest(' '.join(line.split()).casefold()) for row in denied
                        for line in row['prompt'].splitlines() if line.strip()}
    require(not {row['question_sha256'] for row in suite} & denied_questions, 'held_question_overlap')
    require(len({row['question_sha256'] for row in suite}) == 64, 'duplicate_train_question')
    require(all(row['cohort'] == COHORT and row['id'].startswith(COHORT + '_') and row['split'] == 'TRAIN'
                for row in suite), 'only_exact_fresh_train_cohort')
    return dict(status='PASS', allowed_cohort=COHORT, allowed_task_ids=[row['id'] for row in suite],
        excluded_capability_suite_sha256=digest(denied), excluded_task_ids=[row['id'] for row in denied],
        excluded_prompt_hashes=[row['prompt_sha256'] for row in denied],
        denied_other_cohorts='ALL_IDS_AND_CONTENT_OUTSIDE_EXACT_PREDETERMINED64_ALLOWLIST',
        source_disclosure='New synthetic TRAIN questions; exact disjointness, not broad semantic-independence proof',
        parent=False, teacher=False, l2=False, held_inputs=False)


def messages(row):
    expected = next((entry for entry in tasks() if entry['id'] == row.get('id')), None)
    require(expected is not None and digest(row) == digest(expected), 'fixed_task_changed')
    return [dict(role='user', content=row['prompt'])]


def strict_json(raw):
    def pairs(items):
        document = {}
        for key, value in items:
            require(key not in document, 'duplicate_json_key')
            document[key] = value
        return document
    def constant(unused):
        raise ValueError('nonfinite_json')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def same(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(same(left, right) for left, right in zip(actual, expected))
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    return actual == expected


def score(row, raw):
    messages(row)
    require(isinstance(raw, str), 'native_text_required')
    if not raw.strip():
        return dict(passed=False, category='missing_answer')
    if len(raw) > 131072:
        return dict(passed=False, category='oversize')
    family, oracle = row['family'], row['oracle']
    if family == 'concise_answer':
        passed = raw == oracle['answer']
        return dict(passed=passed, category='correct' if passed else 'exact_constraint_failure')
    if family == 'math':
        value = raw.strip()
        if len(value) > 64 or not re.fullmatch(r'[+-]?(?:\d+/\d+|\d+(?:\.\d*)?|\.\d+)', value):
            return dict(passed=False, category='invalid_numeric_format')
        try:
            passed = Fraction(value) == Fraction(oracle['answer'])
        except (ValueError, ZeroDivisionError):
            return dict(passed=False, category='invalid_numeric_format')
        return dict(passed=passed, category='correct' if passed else 'wrong_answer')
    try:
        document = strict_json(raw)
    except (ValueError, RecursionError):
        return dict(passed=False, category='invalid_json')
    if family == 'simulated_tools':
        valid = isinstance(document, dict) and set(document) == {'tool', 'arguments'}
        valid = valid and isinstance(document['tool'], str) and document['tool'] in TOOLS and isinstance(document['arguments'], dict)
        if valid:
            schema, arguments = TOOLS[document['tool']], document['arguments']
            valid = set(arguments) == set(schema)
            if valid:
                valid = all((isinstance(arguments[key], str) and arguments[key] in kind) if isinstance(kind, list)
                    else (isinstance(arguments[key], str) and 0 < len(arguments[key]) <= 100) if kind == 'string'
                    else (type(arguments[key]) is int and 0 < arguments[key] <= 1000) for key, kind in schema.items())
        passed = bool(valid and same(document, oracle))
        return dict(passed=passed, category='correct' if passed else 'wrong_tool_or_arguments' if valid else 'invalid_tool_schema',
                    schema_valid=bool(valid), mock_only=True)
    if not isinstance(document, dict) or set(document) != {'expression'} or not isinstance(document['expression'], str):
        return dict(passed=False, category='invalid_expression_schema')
    count = 0
    try:
        code.validate_expression(document['expression'])
        for case in oracle['cases']:
            count += int(same(code.evaluate(document['expression'], deepcopy(case['inputs'])), case['expected']))
    except (ValueError, SyntaxError, TypeError, KeyError, ArithmeticError, IndexError, RecursionError):
        return dict(passed=False, category='unsafe_or_invalid_expression', cases_passed=count,
                    cases_total=len(oracle['cases']), arbitrary_execution=False)
    passed = count == len(oracle['cases'])
    return dict(passed=passed, category='correct' if passed else 'wrong_answer', cases_passed=count,
                cases_total=len(oracle['cases']), arbitrary_execution=False)


def outcome(row, response, eos):
    tokens = response['token_ids']
    require(response['messages'] == messages(row) and isinstance(response['raw'], str), 'native_prompt_or_text_changed')
    require(isinstance(tokens, list) and len(tokens) <= 512 and all(type(value) is int and value >= 0 for value in tokens), 'native_token_bound')
    terminal, truncated = response['terminal'], response['truncated']
    require(type(terminal) is bool and type(truncated) is bool and terminal == (tokens[-1:] == [eos])
            and eos not in tokens[:-1] and truncated == (not terminal and len(tokens) == 512), 'native_completion_flags')
    machine = score(row, response['raw'])
    return dict(machine=machine, verified_anchor=terminal and machine['passed'],
        completion='truncated' if truncated else 'complete' if terminal else 'incomplete',
        generated_tokens=len(tokens), content_tokens=len(tokens) - int(terminal),
        category=machine['category'] if terminal else 'truncated' if truncated else 'incomplete')
