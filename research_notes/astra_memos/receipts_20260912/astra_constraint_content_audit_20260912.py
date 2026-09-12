"""Read-only terminal-content audit; not a replacement checker or training export."""
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path('/tmp/astra_constraint_verified_terminal_20260912')
PREP = ROOT / 'astra_constraint_check_preparation_20260912_attempt1'
PAIR = ROOT / 'astra_constraint_check_20260912_attempt1'
ARCHIVE = Path('/tmp/astra_constraint_verified_terminal_20260912.tgz')
OUTPUT = Path('/tmp/astra_constraint_content_audit_20260912.json')
ARCHIVE_SHA = '7935c254ac16cfbf33c8cbf9386e9a947ec9b02e50d28e9f03987efb3bbbda89'


def digest(content):
    return hashlib.sha256(content).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def inventory(root):
    expected = read(root / 'artifact_hashes.json')['files']
    require({path.name for path in root.iterdir()} == set(expected) | {'artifact_hashes.json'}, 'inventory set mismatch')
    for name, expected_hash in expected.items():
        require(Path(name).name == name and not (root / name).is_symlink(), 'unsafe inventory path')
        require(digest((root / name).read_bytes()) == expected_hash, 'inventory hash mismatch: ' + name)
    return digest((root / 'artifact_hashes.json').read_bytes())


def coordinate_only(record):
    normalized = copy.deepcopy(record)
    changes = []
    if isinstance(normalized, dict) and isinstance(normalized.get('checks'), list):
        for check_index, check in enumerate(normalized['checks']):
            if not isinstance(check, dict) or not isinstance(check.get('cells'), list):
                continue
            for cell_index, cell in enumerate(check['cells']):
                if not isinstance(cell, list):
                    continue
                for axis, value in enumerate(cell):
                    if type(value) is str and len(value) == 1 and value in '1234':
                        cell[axis] = int(value)
                        changes.append(dict(path=['checks', check_index, 'cells', cell_index, axis], before=value, after=int(value)))
    return normalized, changes


def assess(record, case):
    result = dict(format_valid=False, cases_with_valid_citation=0, valid_citations=0,
                  invalid_citations=0, whole_structured_record_clean=False, reasons=[], citations=[])
    try:
        require(isinstance(record, dict) and set(record) == {'case_id', 'checks', 'lesson'}, 'record keys')
        require(isinstance(record['case_id'], str) and isinstance(record['lesson'], str) and record['lesson'].strip(), 'string fields')
        require(isinstance(record['checks'], list) and 1 <= len(record['checks']) <= 3, 'check cardinality')
        for check in record['checks']:
            require(isinstance(check, dict) and set(check) == {'group', 'cells', 'digit'}, 'check keys')
            require(check['group'] in ('row', 'column', 'box') and type(check['digit']) is int and 1 <= check['digit'] <= 4, 'group/digit')
            require(isinstance(check['cells'], list) and len(check['cells']) == 2 and
                    all(isinstance(cell, list) and len(cell) == 2 and
                        all(type(value) is int and 1 <= value <= 4 for value in cell) for cell in check['cells']), 'coordinate integer schema')
    except ValueError as error:
        result['reasons'].append(str(error))
        return result
    result['format_valid'] = True
    if record['case_id'] != case['case_id']:
        result['reasons'].append('wrong case ID')
        return result
    seen = set()
    for check in record['checks']:
        first, second = check['cells']
        units = []
        for row, column in (first, second):
            units.append({'row': row, 'column': column, 'box': [(row - 1) // 2 + 1, (column - 1) // 2 + 1]}[check['group']])
        values = [case['candidate'][row - 1][column - 1] for row, column in check['cells']]
        distinct = first != second
        same_unit = units[0] == units[1]
        values_match = values == [check['digit'], check['digit']]
        valid = distinct and same_unit and values_match
        key = (check['group'], check['digit'], tuple(sorted(map(tuple, check['cells']))))
        repeated = key in seen
        if valid and not repeated:
            seen.add(key)
            result['valid_citations'] += 1
        elif not valid:
            result['invalid_citations'] += 1
        result['citations'].append(dict(**check, actual_values=values, unit_ids=units,
                                       distinct=distinct, same_unit=same_unit, values_match_claim=values_match,
                                       valid=valid, repeated=repeated))
    result['cases_with_valid_citation'] = int(result['valid_citations'] > 0)
    result['whole_structured_record_clean'] = result['valid_citations'] == len(record['checks'])
    return result


def main():
    require(not OUTPUT.exists(), 'fresh audit output required')
    require(digest(ARCHIVE.read_bytes()) == ARCHIVE_SHA, 'archive SHA mismatch')
    prep_digest = inventory(PREP)
    cases, config, preflight = read(PREP / 'cases.json'), read(PREP / 'config.json'), read(PREP / 'preflight.json')
    require(len(cases) == 8, 'exactly eight cases')
    for case in cases:
        require(case['question_sha256'] == digest(case['question'].encode()), 'question hash mismatch')
        encoded = (json.dumps(case['candidate'], sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()
        require(case['candidate_sha256'] == digest(encoded), 'candidate hash mismatch')
    for key in ('question_sha256', 'candidate_sha256'):
        require(len({case[key] for case in cases}) == 8, 'duplicate ' + key)
    probe = {'checks': [{'cells': [['1', '4'], ['01', ' 2'], ['5', '2.0']], 'digit': '1'}], 'lesson': '3'}
    converted, changes = coordinate_only(probe)
    require(converted['checks'][0]['cells'] == [[1, 4], ['01', ' 2'], ['5', '2.0']] and
            converted['checks'][0]['digit'] == '1' and converted['lesson'] == '3' and len(changes) == 2,
            'normalization scope self-check')
    completed = read(PAIR / 'COMPLETED.json')
    rows, totals, evidence = [], {}, {}
    for mode in ('process', 'format'):
        root = PAIR / mode
        evidence[mode] = dict(inventory_sha256=inventory(root), cleanup=read(PAIR / f'{mode}.cleanup.json'))
        arm_config, result = read(root / 'config.json'), read(root / 'results.json')
        require(arm_config == dict(config, mode=mode, preparation_sha256=prep_digest), 'arm configuration mismatch')
        require(result['status'] == 'COMPLETE' and result['generation_calls'] == 8, 'arm completion mismatch')
        events = [json.loads(line) for line in (root / 'generations.jsonl').read_text().splitlines()]
        require([event['kind'] for event in events] == ['request', 'raw_return', 'output'] * 8, 'not eight calls')
        arm_rows = []
        for index, case in enumerate(cases):
            request, raw, output = events[index * 3:index * 3 + 3]
            require(all(event['request_index'] == index for event in (request, raw, output)), 'request index mismatch')
            expected = preflight['prompts'][mode][index]
            require(all(request[key] == value for key, value in expected.items()), 'frozen prompt mismatch')
            require(len(raw['requests']) == 1 and len(raw['requests'][0]['outputs']) == 1, 'raw cardinality')
            native_request, native_output = raw['requests'][0], raw['requests'][0]['outputs'][0]
            require(native_request['prompt'] == expected['rendered_prompt'] and native_request['finished'], 'native prompt/completion')
            require(native_output['text'] == output['text'] == result['records'][index]['text'], 'raw text disagreement')
            require(digest(output['text'].encode()) == output['output_sha256'], 'raw hash mismatch')
            require(native_output['finish_reason'] == output['finish_reason'] == 'stop' and
                    len(native_output['token_ids']) == output['actual_output_tokens'] <= 128, 'stop/output tokens')
            require(len(native_request['prompt_token_ids']) == output['actual_prompt_tokens'] == expected['prompt_tokens'], 'prompt tokens')
            require(output['case_id'] == case['case_id'], 'case mismatch')
            record = json.loads(output['text'], object_pairs_hook=unique_object)
            normalized, changes = coordinate_only(record)
            strict, posthoc = assess(record, case), assess(normalized, case)
            official = result['records'][index]['score']
            require(strict['format_valid'] == official['format_valid'] and
                    strict['cases_with_valid_citation'] == official['grounded'] and
                    strict['whole_structured_record_clean'] == official['whole_structured_record_clean'], 'strict independent recount differs')
            row = dict(mode=mode, case_id=case['case_id'], candidate=case['candidate'],
                       question_sha256=case['question_sha256'], candidate_sha256=case['candidate_sha256'],
                       raw_text=output['text'], output_sha256=output['output_sha256'],
                       coordinate_only_changes=changes, posthoc_record=normalized,
                       strict=strict, posthoc=posthoc, lesson=record['lesson'],
                       lesson_assessment='Future-check instruction, not an asserted completed check or board fact; not machine-verified or training-approved.',
                       actual_output_tokens=output['actual_output_tokens'])
            rows.append(row)
            arm_rows.append(row)
        totals[mode] = {phase: {field: sum(row[phase][field] for row in arm_rows) for field in
                       ('format_valid', 'cases_with_valid_citation', 'invalid_citations', 'whole_structured_record_clean')}
                       for phase in ('strict', 'posthoc')}
        totals[mode]['coordinate_strings_changed'] = sum(len(row['coordinate_only_changes']) for row in arm_rows)
        require(totals[mode]['strict']['cases_with_valid_citation'] == completed['arms'][mode]['cases_with_valid_citation'] and
                totals[mode]['strict']['format_valid'] == completed['arms'][mode]['format_count'], 'official terminal totals differ')
    payload = dict(schema='posthoc-coordinate-only-content-audit-v1', archive_sha256=ARCHIVE_SHA,
                   preparation_inventory_sha256=prep_digest, evidence=evidence, cases=rows, totals=totals,
                   original_strict_results_unchanged=True, training_approved=False, fit=False,
                   normalization='Only single-character string 1..4 components inside checks[].cells become integers; nothing else changes.',
                   verification='Local captured inventories, raw text/token receipts, board hashes, independent predicates. Absolute remote model/source paths not rehashed; no live GPU verification.',
                   task=config['task'], cards=config['cards'], token_metadata={key: preflight[key] for key in
                   ('card_tokens', 'package_tokens_equal', 'input_tokens_equal')})
    with OUTPUT.open('x') as target:
        json.dump(payload, target, indent=2, ensure_ascii=False, allow_nan=False)
        target.write('\n')
    print(json.dumps(totals, indent=2))


if __name__ == '__main__':
    main()
