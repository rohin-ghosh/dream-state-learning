"""Independent captured-data audit; no production checker import or target export."""
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path('/tmp/astra_constraint_v2_terminal_20260912')
ARCHIVE = Path('/tmp/astra_constraint_v2_terminal_20260912.tgz')
OUTPUT = Path('/tmp/astra_constraint_v2_content_audit_20260912.json')
ARCHIVE_SHA = '476788fb5204ab45dfcc22644382f1519493ce6224ccbce8298616c0d1073692'
MODULE_SHA = '59d66791155c076b40430e5f408e8f044a71f0a9823005e2dee4705aaf87e859'
CARD_SHA = '2821fddeb0e88c1262446b7a1339a0a580394b845bd119cda4fedbd427edf541'
OLD_TASK_SHA = 'e6420ee4a2d840dd5efed4722ae20235b2bc24a0dc27037ea406e3c3eb8e88b4'
CLAUSE = 'Each coordinate component must be an unquoted JSON integer 1..4; do not use numeric strings. '


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def inventory(root):
    files = read(root / 'artifact_hashes.json')['files']
    require({path.name for path in root.iterdir()} == set(files) | {'artifact_hashes.json'}, 'inventory set mismatch')
    for name, digest in files.items():
        require(Path(name).name == name and not (root / name).is_symlink(), 'unsafe artifact path')
        require(sha((root / name).read_bytes()) == digest, 'artifact hash mismatch: ' + str(root / name))
    return sha((root / 'artifact_hashes.json').read_bytes())


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key: ' + key)
        value[key] = item
    return value


def parse_raw(text):
    try:
        return json.loads(text, object_pairs_hook=unique_object), None
    except json.JSONDecodeError as error:
        return None, dict(category='json_syntax_error', reason=str(error))
    except ValueError as error:
        return None, dict(category='duplicate_json_key', reason=str(error))


def is_pair(value):
    return isinstance(value, list) and len(value) == 2 and all(type(axis) is int and 1 <= axis <= 4 for axis in value)


def witness(board, group, cells, digit):
    require(group in ('row', 'column', 'box') and len(cells) == 2 and all(is_pair(cell) for cell in cells), 'audit witness shape')
    values = [board[row - 1][column - 1] for row, column in cells]
    units = [{'row': row, 'column': column, 'box': [(row - 1) // 2 + 1, (column - 1) // 2 + 1]}[group]
             for row, column in cells]
    return dict(group=group, cells=cells, digit=digit, actual_values=values, unit_ids=units,
                distinct=cells[0] != cells[1], same_unit=units[0] == units[1], values_match_claim=values == [digit, digit],
                content_valid=cells[0] != cells[1] and units[0] == units[1] and values == [digit, digit])


def assess(record, parse_error, case):
    result = dict(format_valid=False, grounded=0, invalid_citations=0, valid_citations=0,
                  whole_structured_record_clean=False, category=None, citations=[])
    if parse_error:
        return dict(result, **parse_error)
    try:
        require(isinstance(record, dict) and set(record) == {'case_id', 'checks', 'lesson'}, 'record schema')
        require(isinstance(record['case_id'], str) and isinstance(record['lesson'], str) and record['lesson'].strip(), 'string fields')
        require(isinstance(record['checks'], list) and 1 <= len(record['checks']) <= 3, 'checks cardinality')
        for check in record['checks']:
            require(isinstance(check, dict) and set(check) == {'group', 'cells', 'digit'}, 'check keys')
            require(check['group'] in ('row', 'column', 'box') and type(check['digit']) is int and 1 <= check['digit'] <= 4, 'group/digit')
            cells = check['cells']
            if is_pair(cells):
                raise ValueError('single_coordinate_pair')
            if isinstance(cells, list) and len(cells) == 4 and all(type(value) is int for value in cells):
                raise ValueError('flat_four_coordinates')
            if isinstance(cells, list) and len(cells) == 2 and all(isinstance(cell, dict) for cell in cells):
                raise ValueError('coordinate_objects_not_arrays')
            require(isinstance(cells, list) and len(cells) == 2 and all(is_pair(cell) for cell in cells), 'coordinate_schema_other')
    except ValueError as error:
        return dict(result, category=str(error))
    result['format_valid'] = True
    if record['case_id'] != case['case_id']:
        return dict(result, category='wrong_case_id')
    seen = set()
    for check in record['checks']:
        citation = witness(case['candidate'], check['group'], check['cells'], check['digit'])
        result['citations'].append(citation)
        key = (check['group'], check['digit'], tuple(sorted(map(tuple, check['cells']))))
        if citation['content_valid'] and key not in seen:
            seen.add(key)
            result['valid_citations'] += 1
        elif not citation['content_valid']:
            result['invalid_citations'] += 1
    result['grounded'] = int(result['valid_citations'] > 0)
    result['whole_structured_record_clean'] = result['valid_citations'] == len(record['checks'])
    result['category'] = 'strict_schema_valid'
    return result


def coordinate_only(record):
    value = copy.deepcopy(record)
    changes = 0
    if isinstance(value, dict) and isinstance(value.get('checks'), list):
        for check in value['checks']:
            if isinstance(check, dict) and isinstance(check.get('cells'), list):
                for cell in check['cells']:
                    if isinstance(cell, list):
                        for index, item in enumerate(cell):
                            if type(item) is str and len(item) == 1 and item in '1234':
                                cell[index] = int(item)
                                changes += 1
    return value, changes


def literal_witness(text, record, case):
    groups, digits = re.findall(r'"group"\s*:\s*"(row|column|box)"', text), re.findall(r'"digit"\s*:\s*([1-4])\b', text)
    if len(groups) != 1 or len(digits) != 1:
        return dict(assessable=False, reason='not exactly one explicit group and digit')
    cells, convention = None, None
    if record and len(record.get('checks', [])) == 1:
        value = record['checks'][0].get('cells')
        if isinstance(value, list) and len(value) == 2 and all(is_pair(cell) for cell in value):
            cells, convention = value, 'original_nested_pairs'
        elif isinstance(value, list) and len(value) == 4 and all(type(axis) is int and 1 <= axis <= 4 for axis in value):
            cells, convention = [value[:2], value[2:]], 'POSTHOC_flat_four_grouped_consecutively'
        elif isinstance(value, list) and len(value) == 2 and all(isinstance(cell, dict) and set(cell) == {'row', 'column'} for cell in value):
            cells, convention = [[cell['row'], cell['column']] for cell in value], 'POSTHOC_coordinate_object_fields'
    if cells is None:
        repeated = re.findall(r'"cells"\s*:\s*(\[\s*[1-4]\s*,\s*[1-4]\s*\])', text)
        if len(repeated) == 2:
            cells, convention = [json.loads(value) for value in repeated], 'POSTHOC_both_duplicate_cells_occurrences_not_last_key_wins'
        else:
            adjacent = re.search(r'"cells"\s*:\s*(\[\s*[1-4]\s*,\s*[1-4]\s*\])\s*,\s*(\[\s*[1-4]\s*,\s*[1-4]\s*\])', text)
            if adjacent:
                cells, convention = [json.loads(value) for value in adjacent.groups()], 'POSTHOC_adjacent_pairs_in_invalid_JSON'
    if cells is None:
        return dict(assessable=False, reason='only one coordinate pair; no second cell invented')
    return dict(assessable=True, interpretation=convention,
                original_record_valid=False if convention.startswith('POSTHOC') else None,
                **witness(case['candidate'], groups[0], cells, int(digits[0])))


def self_check():
    board = [[1, 1, 3, 4], [1, 4, 2, 3], [2, 3, 4, 1], [4, 2, 1, 2]]
    for group, cells, digit in [('row', [[4, 2], [4, 4]], 2), ('column', [[1, 1], [2, 1]], 1), ('box', [[1, 2], [2, 1]], 1)]:
        require(witness(board, group, cells, digit)['content_valid'], 'independent witness positive self-check')
    require(not witness(board, 'row', [[1, 1], [2, 1]], 1)['content_valid'], 'group self-check')
    require(not witness(board, 'row', [[1, 1], [1, 1]], 1)['content_valid'], 'distinct-cell self-check')
    original = {'checks': [{'cells': [['1', '4'], ['01', ' 2']], 'digit': '1'}], 'lesson': '3'}
    value, changes = coordinate_only(original)
    require(changes == 2 and value['checks'][0]['cells'] == [[1, 4], ['01', ' 2']] and
            value['checks'][0]['digit'] == '1' and value['lesson'] == '3', 'coordinate-only scope self-check')


def main():
    require(not OUTPUT.exists(), 'fresh JSON output required')
    self_check()
    require(sha(ARCHIVE.read_bytes()) == ARCHIVE_SHA, 'capsule hash mismatch')
    rows, totals, evidence, baseline, pids = [], {}, {}, None, []
    for seed in (7101, 7102, 7103):
        prep = ROOT / f'astra_constraint_v2_preparation_20260912_seed{seed}_attempt1'
        pair = ROOT / f'astra_constraint_v2_20260912_seed{seed}_attempt1'
        prep_hash = inventory(prep)
        config, cases, check = read(prep / 'config.json'), read(prep / 'cases.json'), read(prep / 'preflight.json')
        require(config['schema'] == 'constraint-check-v2' and config['generation_seed'] == seed == check['generation_seed'], 'prep seed/version')
        require(config['generation_seed_role'] == 'generation_sampling_only_not_learner_or_optimizer', 'seed role')
        require(config['episode_ids'] == [f'rg/mini_sudoku/{value}' for value in range(1851100, 1851108)], 'IDs')
        require(sha(json.dumps(config['cards'], sort_keys=True).encode()) == CARD_SHA, 'cards changed')
        require(config['task'].count(CLAUSE) == 1 and sha(config['task'].replace(CLAUSE, '').encode()) == OLD_TASK_SHA, 'task change beyond clause')
        require([value for key, value in config['sources'].items() if key.endswith('/organism_v6/constraint_check_diagnostic.py')] == [MODULE_SHA], 'module receipt')
        require(config['protocol'] == dict(cases=8, calls_per_arm=8, max_tokens=128, max_input_and_output=4096,
                temperature=.7, arm_seconds=900, total_seconds=1800, worker_wait_seconds=840, cleanup_reserve_seconds=60), 'protocol')
        shared = dict(cases=cases, expected_files=config['expected_files'], model_path=config['model_path'],
                      sources=config['sources'], cards=config['cards'], task=config['task'], protocol=config['protocol'], boundary=config['boundary'])
        if baseline is None:
            baseline = shared
        require(shared == baseline, 'cross-seed board/model/source/card/settings mismatch')
        require(len(cases) == 8 and len({case['question_sha256'] for case in cases}) == 8 and
                len({case['candidate_sha256'] for case in cases}) == 8, 'duplicate/missing cases')
        for case in cases:
            require(sha(case['question'].encode()) == case['question_sha256'] and
                    sha(encoded(case['candidate'])) == case['candidate_sha256'], 'actual question/board hash')
        completed, started = read(pair / 'COMPLETED.json'), read(pair / 'STARTED.json')
        require(completed['generation_seed'] == started['generation_seed'] == seed and completed['status'] == 'COMPLETE'
                and started['preparation_sha256'] == prep_hash and completed['generation_calls'] == 16, 'pair completion/seed')
        evidence[str(seed)] = dict(preparation_inventory_sha256=prep_hash, elapsed_seconds=completed['elapsed_seconds'], arms={})
        for mode in ('process', 'format'):
            root = pair / mode
            arm_hash = inventory(root)
            result, arm_config, runtime = read(root / 'results.json'), read(root / 'config.json'), read(root / 'runtime.json')
            require(arm_config == dict(config, mode=mode, preparation_sha256=prep_hash), 'arm config/pair mismatch')
            require(result['status'] == 'COMPLETE' and result['generation_calls'] == 8 and result['generation_seed'] == runtime['generation_seed'] == seed,
                    'arm terminal/seed mismatch')
            require(result['preparation_sha256'] == prep_hash and result['mode'] == mode and result['synthetic'] is False, 'arm identity')
            pids.append(runtime['pid'])
            cleanup, process = read(pair / f'{mode}.cleanup.json'), read(pair / f'{mode}.process.json')
            require(cleanup['pid'] == process['pid'] == runtime['pid'] and all(cleanup[key] for key in
                    ('owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified')), 'captured cleanup mismatch')
            events = [json.loads(line) for line in (root / 'generations.jsonl').read_text().splitlines()]
            require([event['kind'] for event in events] == ['request', 'raw_return', 'output'] * 8, 'eight raw calls required')
            current = []
            for index, case in enumerate(cases):
                request, raw, output = events[index * 3:index * 3 + 3]
                expected = check['prompts'][mode][index]
                board_text = '\n'.join(' '.join(map(str, values)) for values in case['candidate'])
                expected_prompt = f"{config['task']}\n\nParent card:\n{config['cards'][mode]}\n\ncase_id: {case['case_id']}\nCandidate:\n{board_text}"
                require(expected['prompt'] == expected_prompt and expected['seed'] == seed and expected['max_tokens'] == 128, 'case/card/seed prompt')
                require(all(request[key] == value for key, value in expected.items()) and request['temperature'] == .7, 'request settings')
                require(request['source_identity']['model_input'] == config['model_path'] and request['source_identity']['adapter_input'] is None, 'configured model/adapter')
                require(all(event['request_index'] == index for event in (request, raw, output)), 'request index')
                require(not raw['synthetic'] and len(raw['requests']) == 1 and len(raw['requests'][0]['outputs']) == 1, 'native output cardinality')
                native_request, native_output = raw['requests'][0], raw['requests'][0]['outputs'][0]
                require(native_request['finished'] and native_request['prompt'] == expected['rendered_prompt'], 'rendered input')
                require(native_output['text'] == output['text'] == result['records'][index]['text'] and sha(output['text'].encode()) == output['output_sha256'], 'raw text/hash')
                require(native_output['finish_reason'] == output['finish_reason'] == 'stop' and native_output['stop_reason'] == output['stop_reason'], 'native stop')
                require(len(native_output['token_ids']) == output['actual_output_tokens'] <= 128 and
                        len(native_request['prompt_token_ids']) == output['actual_prompt_tokens'] == expected['prompt_tokens'] and
                        output['actual_prompt_tokens'] + 128 <= 4096, 'native token bounds')
                require(output['generation_seed'] == seed and output['case_id'] == case['case_id'] and not output['input_truncated'] and not output['output_rewritten'], 'output identity/truncation')
                record, error = parse_raw(output['text'])
                strict = assess(record, error, case)
                normalized, changes = coordinate_only(record)
                posthoc = assess(normalized, error, case)
                official = result['records'][index]['score']
                for key in ('format_valid', 'grounded', 'invalid_citations', 'valid_citations', 'whole_structured_record_clean'):
                    require(strict[key] == official[key], 'independent strict recount differs: ' + key)
                require(official['training_approved'] is False and official['lesson_machine_verified'] is False, 'approval boundary')
                lessons = re.findall(r'"lesson"\s*:\s*("(?:[^"\\]|\\.)*")', output['text'])
                require(len(lessons) == 1, 'one explicit lesson expected for manual assessment')
                row = dict(seed=seed, mode=mode, case_id=case['case_id'], episode_id=case['episode_id'],
                           candidate=case['candidate'], candidate_sha256=case['candidate_sha256'],
                           raw_text=output['text'], output_sha256=output['output_sha256'], strict=strict,
                           coordinate_only_posthoc=posthoc, coordinate_string_changes=changes,
                           quoted_single_digit_tokens_in_raw=re.findall(r'"[1-4]"', output['text']),
                           literal_witness_posthoc=literal_witness(output['text'], record, case),
                           lesson=json.loads(lessons[0]), lesson_extraction='verbatim string only; no claim of valid enclosing JSON',
                           actual_prompt_tokens=output['actual_prompt_tokens'], actual_output_tokens=output['actual_output_tokens'])
                rows.append(row)
                current.append(row)
            summary = dict(strict_grounded=sum(row['strict']['grounded'] for row in current),
                           strict_format=sum(row['strict']['format_valid'] for row in current),
                           coordinate_only_grounded=sum(row['coordinate_only_posthoc']['grounded'] for row in current),
                           coordinate_string_changes=sum(row['coordinate_string_changes'] for row in current),
                           literal_witness_assessable=sum(row['literal_witness_posthoc']['assessable'] for row in current),
                           literal_witness_content_valid=sum(row['literal_witness_posthoc'].get('content_valid', False) for row in current),
                           categories=dict(Counter(row['strict']['category'] for row in current)),
                           actual_prompt_tokens=sum(row['actual_prompt_tokens'] for row in current),
                           actual_output_tokens=sum(row['actual_output_tokens'] for row in current))
            official_total = completed['arms'][mode]
            require(summary['strict_grounded'] == result['cases_with_valid_citation'] == official_total['cases_with_valid_citation'] and
                    summary['strict_format'] == result['format_count'] == official_total['format_count'] and
                    summary['actual_output_tokens'] == official_total['actual_output_tokens'] and
                    summary['actual_prompt_tokens'] == official_total['actual_prompt_tokens'], 'terminal totals mismatch')
            totals[f'{seed}/{mode}'] = summary
            evidence[str(seed)]['arms'][mode] = dict(inventory_sha256=arm_hash, pid=runtime['pid'], cleanup=cleanup,
                                                   standalone_card_tokens=check['card_tokens'][mode])
    require(len(set(pids)) == 6, 'six distinct captured model workers required')
    require(len(rows) == 48, '48 raw outputs required')
    payload = dict(schema='independent-v2-content-audit-v1', archive_sha256=ARCHIVE_SHA, verification_failures=[],
                   evidence=evidence, totals=totals, records=rows,
                   categories=dict(Counter(row['strict']['category'] for row in rows)),
                   lesson_counts=dict(Counter(row['lesson'] for row in rows)),
                   original_results_unchanged=True, training_approved=False, fit=False,
                   verification_scope='captured inventories/configuration/raw tokens/text/boards only; no live GPU or remote model/source rehash',
                   posthoc_boundary='Coordinate-string-only lane does not repair syntax. Literal-witness lane groups explicit coordinates under named conventions, never creates a repaired record or target.',
                   source_module_sha256=MODULE_SHA, cards_sha256=CARD_SHA)
    with OUTPUT.open('x') as target:
        json.dump(payload, target, ensure_ascii=False, indent=2, allow_nan=False)
        target.write('\n')
    print(json.dumps(dict(totals=totals, categories=payload['categories'], lesson_counts=payload['lesson_counts']), indent=2))


if __name__ == '__main__':
    main()
