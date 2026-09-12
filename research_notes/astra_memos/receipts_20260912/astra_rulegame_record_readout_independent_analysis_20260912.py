"""Independent stdlib raw reduction. No native replay, tokenizer or model imports."""
import ast
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import tarfile
import xml.etree.ElementTree as ET
import zlib

CAPSULE = Path('/tmp/astra_rulegame_record_readout_terminal_20260912.tgz')
CAPSULE_SHA = 'f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458'
EXTRACTED = Path('/tmp/astra_rulegame_record_readout_terminal_20260912')
ROOT = EXTRACTED / 'astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1'
OUTPUT = Path('/tmp/astra_rulegame_record_readout_independent_analysis_20260912.json')
LOCAL_SOURCE = Path('/data/home/rohing/dream-state/organism_v6')
CELLS = ('OFF', 'P_ON', 'A_ON')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_sha(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()).hexdigest()


def verify_archive():
    require(sha(CAPSULE) == CAPSULE_SHA, 'capsule SHA mismatch')
    validation = read(str(CAPSULE) + '.validation.json')
    require(validation['sha256'] == CAPSULE_SHA, 'validation SHA mismatch')
    seen = {}
    with tarfile.open(CAPSULE, 'r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and '..' not in path.parts and member.isfile() and not member.linkname and
                member.name not in seen and member.name in validation['files'], 'unsafe/extra archive member')
            payload = archive.extractfile(member).read()
            seen[member.name] = hashlib.sha256(payload).hexdigest()
            require(len(payload) == member.size and sha(EXTRACTED / member.name) == seen[member.name], 'extracted bytes differ')
    require(seen == validation['files'] and len(seen) == 232, 'archive inventory mismatch')
    return validation


def literal_sources(plan):
    nodes = {}
    hashes = {}
    for filename in ('nursery_dialogue.py', 'rulegame_parenting_diagnostic.py', 'rulegame.py'):
        source = LOCAL_SOURCE / filename
        expected = next(value for key, value in plan['source_pins'].items() if key.endswith('/' + filename))
        require(sha(source) == expected, 'local protocol source differs from capture pin: ' + filename)
        hashes[filename] = expected
        nodes[filename] = {target.id: item.value for item in ast.parse(source.read_text()).body if isinstance(item, ast.Assign)
                           for target in item.targets if isinstance(target, ast.Name)}
    diagnostic = nodes['rulegame_parenting_diagnostic.py']
    boot = ast.literal_eval(nodes['nursery_dialogue.py']['CHILD_BOOT']) + ast.literal_eval(diagnostic['BOOT'].right)
    instruction = ast.literal_eval(diagnostic['RECORD']) + '\n' + ast.literal_eval(diagnostic['RELATION_DEFINITION'])
    return boot, instruction, hashes


def truth(rule, triple):
    first, middle, last = triple
    if rule == 2:
        return first + last == 2 * middle
    if rule == 3:
        return first == middle or first == last or middle == last
    if rule == 4:
        return not any(value % 2 for value in triple)
    require(rule == 5, 'outside fixed readout rules')
    return any(value == 0 for value in triple)


def quiz_panel(rule, eid):
    generator = random.Random(eid + '/quiz')
    positives, negatives = [], []
    while len(positives) < 3 or len(negatives) < 3:
        triple = tuple(generator.randint(0, 9) for _ in range(3))
        (positives if truth(rule, triple) else negatives).append(triple)
    panel = positives[:3] + negatives[:3]
    generator.shuffle(panel)
    return panel


def parse_observed_action(text):
    markers = list(re.finditer(r'\b(?:ACT|TRY|QUIZ)\s*:', text, flags=re.I))
    if len(markers) > 1:
        return dict(kind='invalid', reason='multiple action markers')
    require(len(markers) == 1 and not re.search(r'\[\s*OUTCOME\s*\]', text, flags=re.I), 'unhandled raw action grammar')
    lines = text.splitlines()
    action_lines = [index for index, line in enumerate(lines) if line.startswith('ACT: ')]
    require(len(action_lines) == 1, 'raw response outside observed canonical grammar')
    position = action_lines[0]
    action = lines[position][5:].strip()
    predictions = [line[len('PREDICT:'):].strip() for line in lines[:position] if line.startswith('PREDICT:')]
    ambiguous = len(predictions) > 1 or any(item not in ('T', 'F') for item in predictions)
    predicted = predictions[0] == 'T' if predictions and not ambiguous else None
    triple = re.fullmatch(r'TRY ([+-]?\d+),([+-]?\d+),([+-]?\d+)', action)
    if triple:
        return dict(kind='try', action=action, values=[int(value) for value in triple.groups()],
                    predicted=predicted, prediction_ambiguous=ambiguous)
    if action == 'QUIZ ?':
        return dict(kind='reveal', action=action)
    require(re.fullmatch(r'QUIZ [TF](?:,[TF]){5}', action), 'unhandled quiz grammar')
    return dict(kind='quiz', action=action)


def record_verdict(text, execution):
    reason, record = None, None
    try:
        record = json.loads(text, object_pairs_hook=unique)
        checks = [
            (type(record) is dict and set(record) == {'try', 'observed', 'predicted', 'relation'}, 'record schema'),
            (type(record.get('try')) is list and len(record['try']) == 3 and all(type(value) is int for value in record['try']), 'record triple types'),
            (record.get('try') == execution['values'], 'action mismatch'),
            (type(record.get('observed')) is bool and record['observed'] == execution['observed'], 'outcome mismatch'),
            (not execution['prediction_ambiguous'], 'ambiguous source prediction'),
            (record.get('predicted') is None or type(record['predicted']) is bool, 'prediction type'),
            (record.get('predicted') is execution['predicted'], 'prediction mismatch'),
            (record.get('relation') == ('unavailable' if execution['predicted'] is None else
                'matched' if execution['predicted'] == execution['observed'] else 'mismatched'), 'relation mismatch')]
        reason = next((message for okay, message in checks if not okay), None)
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        reason = 'invalid JSON/schema: ' + str(error)
    return dict(record=record, eligible=reason is None, failures=[reason] if reason else [])


def reduce_cell(cell, plan, lineage, boot, instruction):
    stage, data = ROOT / 'run' / cell, ROOT / 'run' / cell / 'data'
    spec = read(ROOT / 'run' / (cell + '.spec.json'))
    identity, isolation = read(data / 'identity.json'), read(data / 'isolation.json')
    backend = identity['backend']
    require(identity['cell'] == spec['cell'] == cell and identity['stage'] == 'evaluation' and
        identity['model_files'] == spec['model_files'] == plan['model_files'] and backend['model_input'] == plan['model'], 'base identity binding')
    fit = lineage['fits'][cell[0]] if cell != 'OFF' else None
    require(spec['adapter'] == backend['adapter_input'] == (fit['adapter'] if fit else None) and
        spec['adapter_files'] == (fit['files'] if fit else {}) and
        backend['adapter_files'] == ({name: fit['files'][name] for name in ('adapter_config.json', 'adapter_model.safetensors')} if fit else {}), 'adapter identity binding')
    process = read(stage / 'process.json')
    require(isolation['parent_calls'] == 0 and isolation['task_prefix'] == '' and isolation['record_training'] is False and
        isolation['spec_sha256'] == sha(ROOT / 'run' / (cell + '.spec.json')) and
        isolation['pid'] == isolation['pgid'] == process['pid'] == process['pgid'], 'worker isolation/identity receipt')
    inventory = {path.relative_to(data).as_posix(): sha(path) for path in data.rglob('*') if path.is_file() and path.name != 'manifest.json'}
    require(inventory == read(data / 'manifest.json')['files'], 'capture inventory')
    request_paths = sorted((data / 'calls').glob('*.request.json'))
    roles, costs, calls, events, tasks, executions, records = Counter(), {}, [], [], [], [], []
    cursor, last_end = 0, 0.

    def ask(role, eid, tick, prompt):
        nonlocal cursor, last_end
        path = request_paths[cursor]
        call_id = f'{cursor:04d}'
        require(path.name == call_id + '.request.json', 'call order')
        sent, received = read(path), read(path.with_name(call_id + '.response.json'))
        request, response = sent['request'], received['response']
        expected = dict(call_id=call_id, role=role, arm=cell, eid=eid, tick=tick, prompt=prompt,
            seed=(zlib.crc32(f'{eid}/{tick}'.encode()) ^ (20260912 ^ (0 if role == 'wake' else 0x5A5A))) & 0x7fffffff,
            max_tokens=400 if role == 'wake' else 100, temperature=.7, protocol='interaction_v3',
            stop=['\n[OUTCOME]'] if role == 'wake' else [], include_stop_str_in_output=False)
        require(request == expected and sent['identity'] == backend and sent['prompt_sha256'] == value_sha(prompt) and
            received['response_sha256'] == value_sha(response), 'raw request/context/seed/identity/response mismatch: ' + cell + call_id)
        require(all(math.isfinite(value) for value in (sent['started'], received['ended'])) and
            last_end <= sent['started'] <= received['ended'], 'call timing')
        require(0 < len(response['prompt_token_ids']) and len(response['prompt_token_ids']) + request['max_tokens'] <= 16384 and
            len(response['output_token_ids']) <= request['max_tokens'], 'token cap')
        last_end = received['ended']
        metrics = dict(requests=1, native_input_tokens=len(response['prompt_token_ids']), native_output_tokens=len(response['output_token_ids']),
            output_token_ceiling=request['max_tokens'], generation_seconds=received['ended'] - sent['started'])
        totals = costs.setdefault(role, dict.fromkeys(metrics, 0))
        for key, value in metrics.items():
            totals[key] += value
        code = dict(call_id=call_id, role=role, eid=eid, tick=tick, text=response['text'], prompt_sha256=sent['prompt_sha256'],
            output_ids_sha256=value_sha(response['output_token_ids']), finish_reason=response.get('finish_reason'), stop_reason=response.get('stop_reason'),
            output_cap_hit=metrics['native_output_tokens'] == request['max_tokens'], **metrics)
        calls.append(code)
        roles[role] += 1
        cursor += 1
        return call_id, response['text'], code

    for rule in range(2, 6):
        eid = f'rule{rule}/astra-minimum-20260912/readout'
        panel = quiz_panel(rule, eid)
        labels = [truth(rule, triple) for triple in panel]
        tail, tries, revealed, correct, quiz_valid, terminal = ['A fresh mystery box.'], 0, False, 0, False, 'wake_budget'
        task_exec, answers, invalid = [], None, None
        for tick in range(1, 6):
            prompt = boot + f'\nTask: {eid}\nGoal: Induce the hidden rule and answer the quiz.\nResponse: {tick}/5\n' + '\n'.join(tail)
            prompt += f'\nHarness state: remaining TRY budget: {3 - tries}. ' + (
                'Quiz already revealed; submit six T/F labels with ACT: QUIZ.' if revealed else 'Quiz reveal still needed before scoring: ACT: QUIZ ?.')
            prompt += '\nEmit one action only; never supply [OUTCOME] or simulate a world reply.'
            call_id, text, code = ask('wake', eid, tick, prompt)
            tail.append(text)
            action = parse_observed_action(text)
            first_action = text.find('ACT: ')
            code.update(action=action, predict_lines_anywhere=re.findall(r'^PREDICT:\s*([^\n]*)', text, re.M),
                predict_lines_before_first_ACT=re.findall(r'^PREDICT:\s*([^\n]*)', text[:first_action], re.M),
                contains_TRY=bool(re.search(r'ACT: TRY\b', text)))
            if action['kind'] == 'invalid':
                terminal, invalid = 'protocol_invalid', dict(call_id=call_id, raw=text, reason=action['reason'])
                events.append(dict(kind='protocol_invalid', arm=cell, eid=eid, call_id=call_id, failure=action['reason']))
                break
            kind, reward = action['kind'], 0.
            if kind == 'try':
                require(tries < 3, 'TRY budget')
                observed = truth(rule, action['values'])
                outcome = 'the box says: ' + str(observed) + ' for (' + ','.join(map(str, action['values'])) + ')'
                tries += 1
            elif kind == 'reveal':
                require(not revealed, 'duplicate reveal')
                outcome = f'INVALID: quiz needs 6 answers (T/F) for {panel}'
                revealed = True
            else:
                require(revealed, 'quiz before reveal')
                answers = [label == 'T' for label in action['action'][5:].split(',')]
                correct = sum(answer == label for answer, label in zip(answers, labels))
                reward, quiz_valid, terminal = correct / 6, True, 'first_quiz'
                outcome = f'quiz score: {reward:.2f}'
            execution = dict(action, kind='execution', action_kind=kind, arm=cell, eid=eid, tick=tick,
                call_id=call_id, execution_id=f'{cell}:{eid}#t{tick}', reward=reward, outcome=outcome,
                raw_response=text, canonical_action='ACT: ' + action['action'])
            if kind == 'try':
                execution['observed'] = observed
                executions.append(execution)
                task_exec.append(execution)
            events.append(execution)
            tail.append('[OUTCOME] ' + outcome)
            if kind == 'try':
                facts = {key: execution[key] for key in ('values', 'observed', 'predicted')}
                record_prompt = f'Task: {eid}\nExecution: {eid}#t{tick}\nActual emitted output:\n{text}'
                record_prompt += f'\nActual world response:\n{outcome}\nObserved fields: {json.dumps(facts)}\n{instruction}'
                record_id, record_text, record_code = ask('record', eid, tick, record_prompt)
                verdict = record_verdict(record_text, execution)
                record_code.update(verdict=verdict, source_call_id=call_id)
                record_event = dict(kind='record', arm=cell, eid=eid, execution_id=execution['execution_id'], source_call_id=call_id,
                    call_id=record_id, text=record_text, eligible=verdict['eligible'], failures=verdict['failures'])
                events.append(record_event)
                records.append(record_event)
            if kind == 'quiz':
                break
        task = dict(arm=cell, eid=eid, tries=tries, quiz_accuracy=correct / 6, valid_quiz=quiz_valid, terminal=terminal)
        events.append(dict(kind='task', **task))
        tasks.append(dict(task, quiz_panel=panel, correct_labels=labels, submitted_labels=answers, correct_items=correct,
            invalid=invalid, probes=[dict(values=item['values'], observed=item['observed'], predicted=item['predicted']) for item in task_exec]))
    require(cursor == len(request_paths) and len(list((data / 'calls').glob('*.json'))) == 2 * cursor, 'executed calls not consumed exactly')
    require(events == [json.loads(line) for line in (data / 'events.jsonl').read_text().splitlines()], 'independent world/record events differ')
    faithful, quiz_correct = sum(row['eligible'] for row in records), sum(row['correct_items'] for row in tasks)
    stored = read(data / 'result.json')
    task_keys = ('arm', 'eid', 'tries', 'quiz_accuracy', 'valid_quiz', 'terminal')
    require(stored['tasks'] == [{key: task[key] for key in task_keys} for task in tasks] and stored['calls'] == cursor and
        stored['roles'] == dict(roles) and stored['faithful_records'] == faithful and stored['allotted_record_opportunities'] == 12 and
        math.isclose(stored['mean_quiz_accuracy'], quiz_correct / 24, abs_tol=1e-15), 'sealed result comparison failed')
    native_usage = read(data / 'usage.json')
    for role, count in costs.items():
        require(native_usage[role] == dict(count, by_arm={cell: count}), 'nested usage mismatch')
    totals = {key: sum(count[key] for count in costs.values()) for key in next(iter(costs.values()))}
    predictions = [item for item in executions if item['predicted'] is not None]
    tries_in_text = [row for row in calls if row.get('contains_TRY')]
    native = read(data / 'native_audit.json')
    require(native['ok'] and native['calls'] == cursor and read(data / 'backend.cleanup.json')['closed'], 'native audit/cleanup receipt')
    return dict(calls=cursor, roles=dict(roles), quiz_correct=quiz_correct, quiz_denominator=24, quiz_accuracy=quiz_correct / 24,
        valid_quizzes=sum(row['valid_quiz'] for row in tasks), tasks=tasks,
        faithful_records=faithful, allotted_record_denominator=12, executed_record_denominator=len(records),
        record_failures=[row for row in records if not row['eligible']],
        predictions=dict(executed_TRYs=len(executions), explicit_valid=len(predictions), null=len(executions) - len(predictions),
            ambiguous=sum(row['prediction_ambiguous'] for row in executions), correct=sum(row['predicted'] == row['observed'] for row in predictions),
            predicted_true=sum(row['predicted'] is True for row in predictions), predicted_false=sum(row['predicted'] is False for row in predictions),
            TRY_containing_response_denominator=len(tries_in_text), invalid_TRY_responses=sum(row['action']['kind'] == 'invalid' for row in tries_in_text),
            TRY_responses_with_any_PREDICT=sum(bool(row['predict_lines_anywhere']) for row in tries_in_text),
            TRY_responses_with_pre_ACT_PREDICT=sum(bool(row['predict_lines_before_first_ACT']) for row in tries_in_text)),
        observed_TRY_true=sum(row['observed'] for row in executions), observed_TRY_false=sum(not row['observed'] for row in executions),
        costs_by_role=costs, costs=totals, output_cap_hits=sum(row['output_cap_hit'] for row in calls),
        finish_reasons=dict(Counter(row['finish_reason'] for row in calls)), raw_codes=calls,
        parent_free_prompt_reconstruction=True, independent_events_and_sealed_result_match=True,
        identity=dict(backend=backend, model_files=spec['model_files'], adapter_files=spec['adapter_files'], worker_pid=process['pid'], isolation=isolation),
        native_token_audit_receipt=native, supervision=read(stage / 'supervision.json'))


def main():
    validation = verify_archive()
    plan, lineage, terminal = read(ROOT / 'plan.json'), read(ROOT / 'run/lineage.json'), read(ROOT / 'run/result.json')
    require(sha(ROOT / 'plan.json') == validation['plan_sha256'] == read(ROOT / 'plan.sha256.json')['sha256'], 'plan seal')
    boot, instruction, sources = literal_sources(plan)
    cells = {cell: reduce_cell(cell, plan, lineage, boot, instruction) for cell in CELLS}
    for cell, reduced in cells.items():
        require(terminal['cells'][cell]['capture_sha256'] == sha(ROOT / 'run' / cell / 'data/manifest.json') and
            terminal['cells'][cell]['result'] == read(ROOT / 'run' / cell / 'data/result.json'), 'controller/capture result binding')
        supervision = reduced['supervision']
        require(all(supervision[key] for key in ('ok', 'reservation_release_verified', 'owned_group_empty', 'gpu_processes_absent')) and
            supervision['returncode'] == 0, 'supervised cleanup')
    comparisons = []
    for first, second in zip(cells['P_ON']['raw_codes'], cells['A_ON']['raw_codes']):
        require((first['role'], first['eid'], first['tick']) == (second['role'], second['eid'], second['tick']), 'unaligned P/A calls')
        comparisons.append(dict(call_id=first['call_id'], role=first['role'], text_equal=first['text'] == second['text'],
            prompt_equal=first['prompt_sha256'] == second['prompt_sha256'], output_ids_equal=first['output_ids_sha256'] == second['output_ids_sha256']))
    release = read(ROOT / 'run/main_release.json')
    launch = read(ROOT.with_name(ROOT.name + '_launch') / 'launch.json')
    full = (dt.datetime.fromisoformat(release['release_utc']) - dt.datetime.fromisoformat(launch['started_utc'])).total_seconds()
    require(math.isclose(full, release['full_reservation_seconds'], abs_tol=1e-5) and
        release['terminal_sha256'] == sha(ROOT / 'run/result.json') and release['xml_sha256'] == sha(ROOT / 'run/main_release.xml') and
        release['launch_sha256'] == sha(ROOT.with_name(ROOT.name + '_launch') / 'launch.json'), 'release custody/cost')
    gpu = ET.fromstring((ROOT / 'run/main_release.xml').read_bytes()).find('gpu')
    require(gpu.findtext('uuid') == release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid'] and
        len(gpu.find('processes')) == 0, 'release XML')
    workers = sum(row['supervision']['reserved_seconds'] for row in cells.values())
    generation = sum(row['costs']['generation_seconds'] for row in cells.values())
    require(math.isclose(workers, release['observed_worker_seconds'], abs_tol=1e-6) and
        terminal['controller_seconds'] == release['controller_seconds'] and generation <= workers <= terminal['controller_seconds'] <= full,
        'nested clock accounting')
    total_cost = {key: sum(cell['costs'][key] for cell in cells.values()) for key in cells['OFF']['costs']}
    result = dict(status='PASS_RAW_RECOUNT', capsule_sha256=CAPSULE_SHA, capsule_metadata_files=232,
        validation_sha256=sha(str(CAPSULE) + '.validation.json'), plan_sha256=sha(ROOT / 'plan.json'), source_literals_verified=sources,
        method='Independent stdlib raw-action/world/record/quiz and exact prompt reconstruction. No native reducer/tokenizer/model called.',
        disclosure='Author wrote formation/write collectors and saved-weight audit, not readout driver/collector. Main summary was visible before analysis.',
        cells=cells, executed_calls=sum(row['calls'] for row in cells.values()), max_call_ceiling=96,
        P_A_raw_comparison=dict(aligned_calls=len(comparisons), text_equal=sum(row['text_equal'] for row in comparisons),
            prompt_equal=sum(row['prompt_equal'] for row in comparisons), output_ids_equal=sum(row['output_ids_equal'] for row in comparisons),
            differences=[row for row in comparisons if not all(row[key] for key in ('text_equal', 'prompt_equal', 'output_ids_equal'))]),
        costs=dict(raw_totals=total_cost, worker_seconds=workers, controller_seconds=terminal['controller_seconds'],
            full_launch_to_release_seconds=full, full_A40_minutes=full / 60, collection_seconds=validation['collection_seconds'],
            collection_seconds_at_release=release['collection_seconds_at_release'], release_utc=release['release_utc'],
            accounting='Generation is inside workers, inside controller, inside launch-to-observed-vacancy. Role/by_arm usage duplicates are not added twice; collection overlaps reservation.'),
        limits='Weights excluded: verified lineage/spec/identity hash agreement, not a new native rehash. Native token audit PASS is attested, not rerun. Exploratory selected-record shared-OFF readout, not adaptation/utility or semantic certification.')
    with OUTPUT.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], calls=result['executed_calls'], cells={cell: {key: row[key] for key in
        ('quiz_correct', 'faithful_records', 'predictions', 'costs', 'record_failures')} for cell, row in cells.items()},
        P_A=result['P_A_raw_comparison'], costs=result['costs']), indent=2))


if __name__ == '__main__':
    main()
