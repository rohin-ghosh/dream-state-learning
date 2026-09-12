"""Prepared CPU-only process readout auditor: explicit complete capsule required."""
import argparse
import ast
from collections import Counter
import datetime as dt
import fnmatch
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import tarfile
import xml.etree.ElementTree as ET
import zlib

STEM = Path('/tmp/astra_process_readout_independent_review_20260912')
DRIVER_SHA = '46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46'
COLLECTOR_SHA = '303b1518da794832d6cc22609239be46b9f7587485efe21cbd706ff8827c1468'
PRIOR_AUDITOR_SHA = 'ab9cda5e0d6bbcfa882c5268bc9357c34859cac079353e48761f2038d38134bc'
CELLS = ('OFF', 'P_ON', 'A_ON')
PROTOCOLS = ('strict_v1', 'interaction_v2', 'interaction_v3')
ROOT = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(value):
    def reject_constant(constant):
        raise ValueError('nonfinite JSON constant: ' + constant)
    return json.loads(value, object_pairs_hook=unique, parse_constant=reject_constant)


def read(path):
    return decode(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_sha(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()).hexdigest()


class CapsulePath:
    def __init__(self, name, files):
        self.namepath, self.files = PurePosixPath(name), files

    def __truediv__(self, name):
        return CapsulePath(str(self.namepath / name), self.files)

    def __lt__(self, other):
        return str(self.namepath) < str(other.namepath)

    @property
    def name(self):
        return self.namepath.name

    def is_file(self):
        return str(self.namepath) in self.files

    def read_bytes(self):
        return self.files[str(self.namepath)]

    def read_text(self):
        return self.read_bytes().decode('utf-8')

    def with_name(self, name):
        return CapsulePath(str(self.namepath.with_name(name)), self.files)

    def relative_to(self, other):
        return self.namepath.relative_to(other.namepath)

    def glob(self, pattern):
        return [CapsulePath(name, self.files) for name in sorted(self.files)
                if PurePosixPath(name).parent == self.namepath and fnmatch.fnmatch(PurePosixPath(name).name, pattern)]

    def rglob(self, pattern):
        return [CapsulePath(name, self.files) for name in sorted(self.files)
                if name.startswith(str(self.namepath) + '/') and fnmatch.fnmatch(PurePosixPath(name).name, pattern)]


def parse_observed_action(text):
    try:
        return parse_action(text, 'interaction_v3')
    except ValueError as error:
        return dict(kind='invalid', reason=str(error))


def record_verdict(text, execution):
    verdict = judge_record(text, execution)
    try:
        record = decode(text)
    except (ValueError, TypeError):
        record = None
    return dict(record=record, **verdict)


def parse_action(text, protocol="strict_v1"):
    require(protocol in PROTOCOLS, "unknown interaction protocol")
    if protocol in ("interaction_v2", "interaction_v3"):
        require(not re.search(r"\[\s*OUTCOME\s*\]", text, re.IGNORECASE), "imagined OUTCOME in response")
        intents = list(re.finditer(r"\b(?:ACT|TRY|QUIZ)\s*:", text, re.IGNORECASE))
        if intents:
            require(len(intents) == 1, "multiple action markers")
            require(not re.search(r"^\s*DONE\b", text, re.MULTILINE | re.IGNORECASE), "action and DONE coexist")
            marker = intents[0]
            start = text.rfind("\n", 0, marker.start()) + 1
            line = text[start:].splitlines()[0]
            if not marker.group().startswith("ACT"):
                require(marker.start() == start and line.startswith(("TRY: ", "QUIZ: ")),
                        "noncanonical alias line")
                text = text[:start] + "ACT: " + line.replace(":", "", 1) + text[start + len(line):]
        require(not re.search(r"^\s*(?:TRY|QUIZ)\b", text, re.MULTILINE | re.IGNORECASE),
                "unanchored or additional action")
    markers = list(re.finditer(r"\bACT\s*:", text, re.IGNORECASE))
    if not markers:
        if re.fullmatch(r"\s*DONE\s*:?\s*", text):
            return {"kind": "done"}
        raise ValueError("missing canonical ACT")
    require(len(markers) == 1, "multiple ACT markers")
    marker = markers[0]
    start = text.rfind("\n", 0, marker.start()) + 1
    line = text[start:].splitlines()[0]
    require(line.startswith("ACT: ") and marker.start() == start, "noncanonical ACT line")
    require(not re.search(r"^\s*DONE\b", text, re.MULTILINE), "ACT and DONE coexist")
    action = line[5:].strip()
    triple = re.fullmatch(r"TRY\s+([+-]?[0-9]+)\s*,\s*([+-]?[0-9]+)\s*,\s*([+-]?[0-9]+)", action)
    prediction_lines = re.findall(r"^PREDICT:\s*([^\n]*)", text[:start], re.MULTILINE)
    ambiguous = len(prediction_lines) > 1 or any(value.strip() not in ("T", "F") for value in prediction_lines)
    predicted = prediction_lines[0].strip() == "T" if prediction_lines and not ambiguous else None
    if triple:
        return dict(kind="try", action=action, values=[int(value) for value in triple.groups()],
                    predicted=predicted, prediction_ambiguous=ambiguous)
    if action == "QUIZ ?":
        return dict(kind="reveal", action=action)
    quiz = re.fullmatch(r"QUIZ\s+([TF](?:\s*,\s*[TF]){5})", action)
    require(quiz is not None, "ACT needs exactly three integers or six literal T/F labels")
    return dict(kind="quiz", action=action)

def judge_record(text, execution):
    failures = []
    try:
        record = decode(text)
        require(isinstance(record, dict) and set(record) == {"try", "observed", "predicted", "relation"},
                "record schema")
        require(type(record["try"]) is list and len(record["try"]) == 3
                and all(type(value) is int for value in record["try"]), "record triple types")
        require(record["try"] == execution["values"], "action mismatch")
        require(type(record["observed"]) is bool and record["observed"] == execution["observed"], "outcome mismatch")
        require(not execution["prediction_ambiguous"], "ambiguous source prediction")
        require(record["predicted"] is None or type(record["predicted"]) is bool, "prediction type")
        require(record["predicted"] is execution["predicted"], "prediction mismatch")
        relation = ("unavailable" if execution["predicted"] is None else
                    "matched" if execution["predicted"] == execution["observed"] else "mismatched")
        require(record["relation"] == relation, "relation mismatch")
    except (ValueError, TypeError, KeyError) as error:
        failures.append(str(error))
    return dict(eligible=not failures, failures=failures)

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
            if action['kind'] == 'try' and tries >= 3:
                action = dict(kind='invalid', reason='TRY budget exhausted')
            elif action['kind'] == 'reveal' and revealed:
                action = dict(kind='invalid', reason='quiz already revealed')
            elif action['kind'] == 'quiz' and not revealed:
                action = dict(kind='invalid', reason='quiz not revealed')
            marker = re.search(r'(?m)^(?:ACT|TRY|QUIZ): ', text)
            first_action = marker.start() if marker else len(text)
            code.update(action=action, predict_lines_anywhere=re.findall(r'^PREDICT:\s*([^\n]*)', text, re.M),
                predict_lines_before_first_ACT=re.findall(r'^PREDICT:\s*([^\n]*)', text[:first_action], re.M),
                contains_TRY=bool(re.search(r'(?m)^(?:ACT: TRY\b|TRY: )', text)))
            if action['kind'] == 'done':
                terminal = 'done'
                break
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
                answers = [label.strip() == 'T' for label in action['action'][4:].strip().split(',')]
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
    return dict(reconstructed_events=events, calls=cursor, roles=dict(roles), quiz_correct=quiz_correct, quiz_denominator=24, quiz_accuracy=quiz_correct / 24,
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


def open_complete_capsule(path, expected, validation_path):
    require(sha(path) == expected, 'Main capsule pin mismatch')
    validation = read(validation_path)
    require(validation['archive_sha256'] == expected and validation['status'] == 'COLLECTED_COMPLETE'
            and validation['full_release'] and validation['science_aggregate_available'], 'complete release required before outcomes')
    files = {}
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        require(len(members) <= 2000 and sum(member.size for member in members) <= 64 * 1024 * 1024, 'metadata bound')
        for member in members:
            require(member.isfile() and member.name not in files and '\\' not in member.name
                    and all(part not in ('', '.', '..') for part in member.name.split('/'))
                    and member.name.startswith('metadata/'), 'unsafe member')
            require(PurePosixPath(member.name).suffix.lower() not in ('.safetensors', '.bin', '.pt', '.pth', '.pyc', '.pyo'), 'weight/bytecode member')
            payload = archive.extractfile(member).read()
            require(hashlib.sha256(payload).hexdigest() == validation['files'].get(member.name), 'member hash mismatch')
            files[member.name] = payload
    require(set(files) == set(validation['files']), 'inventory mismatch')
    root = CapsulePath('metadata/root', files)
    require(not (root / 'run/failure.json').is_file(), 'failure marker: no partial scoring')
    terminal = read(root / 'run/result.json')
    require(terminal['status'] == 'COMPLETE_EXPLORATORY_READOUT' and set(terminal['cells']) == set(CELLS), 'all three cells required')
    for cell in CELLS:
        for name in ('result.json', 'manifest.json', 'events.jsonl', 'identity.json', 'native_audit.json', 'backend.cleanup.json'):
            require((root / 'run' / cell / 'data' / name).is_file(), 'missing complete endpoint')
    return root, validation


def checked_source(root, expected, suffix=None):
    matches = [payload for name, payload in root.files.items() if name.startswith('metadata/source/')
               and (suffix is None or name.endswith(suffix)) and hashlib.sha256(payload).hexdigest() == expected]
    require(len(matches) == 1, 'missing/ambiguous archived source pin')
    return matches[0].decode()


def source_literals(root, plan):
    checked_source(root, DRIVER_SHA)
    checked_source(root, COLLECTOR_SHA)
    checked_source(root, plan['write_driver_sha256'])
    nodes, hashes = {}, {}
    for filename in ('nursery_dialogue.py', 'rulegame_parenting_diagnostic.py', 'rulegame.py'):
        pins = [pin for name, pin in plan['source_pins'].items() if name.endswith('/' + filename)]
        require(len(pins) == 1, 'source binding ambiguous')
        source = checked_source(root, pins[0], filename)
        tree = ast.parse(source)
        nodes[filename] = {target.id: item.value for item in tree.body if isinstance(item, ast.Assign)
                           for target in item.targets if isinstance(target, ast.Name)}
        hashes[filename] = pins[0]
        if filename == 'rulegame_parenting_diagnostic.py':
            local = ast.parse(Path(__file__).read_text())
            for function in ('parse_action', 'judge_record'):
                archived = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function)
                copied = next(node for node in local.body if isinstance(node, ast.FunctionDef) and node.name == function)
                require(ast.dump(archived) == ast.dump(copied), 'frozen shared syntax helper changed')
    diagnostic = nodes['rulegame_parenting_diagnostic.py']
    boot = ast.literal_eval(nodes['nursery_dialogue.py']['CHILD_BOOT']) + ast.literal_eval(diagnostic['BOOT'].right)
    instruction = ast.literal_eval(diagnostic['RECORD']) + '\n' + ast.literal_eval(diagnostic['RELATION_DEFINITION'])
    return boot, instruction, hashes


def descriptive_metrics(cell):
    events, calls = cell['reconstructed_events'], cell['raw_codes']
    tasks = []
    for task in cell['tasks']:
        eid = task['eid']
        probes = [row for row in events if row['kind'] == 'execution' and row['eid'] == eid and row['action_kind'] == 'try']
        records = [row for row in events if row['kind'] == 'record' and row['eid'] == eid]
        wake = [row for row in calls if row['eid'] == eid and row['role'] == 'wake']
        predicted = [row for row in probes if type(row['predicted']) is bool and not row['prediction_ambiguous']]
        correct = sum(row['predicted'] == row['observed'] for row in predicted)
        distinct = len({tuple(row['values']) for row in probes})
        tasks.append(dict(eid=eid, quiz_items=6, quiz_items_correct=task['correct_items'], valid_quiz=task['valid_quiz'],
            invalid_or_absent_quiz=not task['valid_quiz'], wake_responses=len(wake),
            predict_emitting_responses=sum(bool(row['predict_lines_anywhere']) for row in wake),
            predict_lines=sum(len(row['predict_lines_anywhere']) for row in wake),
            protocol_invalid_actions=sum(row['kind'] == 'protocol_invalid' and row['eid'] == eid for row in events),
            executed_probes=len(probes), distinct_probe_triples=distinct, repeated_probe_triples=len(probes)-distinct,
            allotted_probe_opportunities=3, valid_predicted_probes=len(predicted), correct_predicted_probes=correct,
            probes_without_unambiguous_prediction=len(probes)-len(predicted), prediction_accuracy=correct/len(predicted) if predicted else None,
            actual_records=len(records), faithful_records=sum(row['eligible'] for row in records),
            invalid_records=sum(not row['eligible'] for row in records), allotted_record_opportunities=3))
    excluded = {'eid', 'valid_quiz', 'invalid_or_absent_quiz', 'prediction_accuracy'}
    totals = {key:sum(row[key] for row in tasks) for key in tasks[0] if key not in excluded}
    ratio = lambda numerator, denominator: totals[numerator]/totals[denominator] if totals[denominator] else None
    return dict(tasks=tasks, totals=totals, quiz_accuracy_fixed24=totals['quiz_items_correct']/24,
        invalid_or_absent_quiz_tasks=sum(row['invalid_or_absent_quiz'] for row in tasks),
        prediction_accuracy=ratio('correct_predicted_probes', 'valid_predicted_probes'),
        prediction_fraction_executed_probes=ratio('valid_predicted_probes', 'executed_probes'),
        prediction_fraction_allotted12=totals['valid_predicted_probes']/12,
        faithful_record_fraction_actual=ratio('faithful_records', 'actual_records'),
        faithful_record_fraction_allotted12=totals['faithful_records']/12)


def audit(args):
    global ROOT
    ROOT, validation = open_complete_capsule(args.capsule, args.capsule_sha256, args.validation)
    plan, lineage, terminal = (read(ROOT / name) for name in ('plan.json', 'run/lineage.json', 'run/result.json'))
    require(sha(ROOT / 'plan.json') == args.plan_sha256 == read(ROOT / 'plan.sha256.json')['sha256'], 'Main plan seal')
    require(plan['self_sha256'] == DRIVER_SHA and plan['version'] == 'context_distilled_process_parent_free_readout_v1'
            and plan['write_protocol'] == 'rulegame_process_write_v2_20260912'
            and plan['material_protocol'] == 'rulegame_grounded_process_pair_v2'
            and plan['conditioning'] == 'CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT', 'wrong experiment/objective')
    require(lineage == plan['lineage'] and lineage['write_plan_sha256'] == plan['write_plan_sha256'], 'writer lineage seal')
    protocol = plan['protocol']
    require(protocol['cells'] == list(CELLS) and protocol['interaction_protocol'] == 'interaction_v3'
            and protocol['quiz_items_total'] == 24 and protocol['max_calls'] == 96
            and protocol['parent_calls'] == 0 and protocol['restatement_calls'] == 0
            and protocol['task_prefix'] == '' and not protocol['record_training'] and not protocol['record_feedback_into_wake'], 'readout visibility/denominators')
    boot, instruction, sources = source_literals(ROOT, plan)
    cells = {cell:reduce_cell(cell, plan, lineage, boot, instruction) for cell in CELLS}
    controller = read(ROOT / 'run/controller.json')
    windows = []
    for cell, reduced in cells.items():
        stage = ROOT / 'run' / cell
        metrics = descriptive_metrics(reduced)
        receipt = terminal['cells'][cell]
        for key, value in metrics.items():
            require(receipt['process_metrics'][key] == value, 'stored descriptive metric differs: ' + cell + '/' + key)
        require(receipt['result'] == read(stage / 'data/result.json') and receipt['capture_sha256'] == sha(stage / 'data/manifest.json')
                and receipt['spec_sha256'] == sha(ROOT / 'run' / (cell + '.spec.json'))
                and receipt['supervision_sha256'] == sha(stage / 'supervision.json'), 'controller cell seal')
        process, supervision = read(stage / 'process.json'), reduced['supervision']
        ready = read(stage / 'data/backend.ready.json')
        require(ready['pid'] == process['pid'] and 0 <= ready['ready']-process['started'] <= 180, 'backend readiness/identity')
        reduced['backend_ready_seconds'] = ready['ready']-process['started']
        require(all(supervision[key] for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
                and supervision['returncode'] == 0 and supervision['error'] is None, 'worker failure')
        require(process['device'] == supervision['device'] == plan['device'] and 0 < process['timeout'] <= 600
                and reduced['identity']['isolation']['parent_pid'] == controller['pid'], 'worker identity/bounds')
        windows.append((process['started'], process['started']+supervision['reserved_seconds']))
        for request in sorted((stage / 'data/calls').glob('*.request.json')):
            sent, received = read(request), read(request.with_name(request.name.replace('.request.', '.response.')))
            require(windows[-1][0] <= sent['started'] <= received['ended'] <= windows[-1][1]
                    and received['ended']-sent['started'] <= 120, 'call outside owned window/cap')
        reduced['descriptive_metrics'] = metrics
    require(all(first[1] <= second[0] for first, second in zip(windows, windows[1:])), 'cell workers overlapped/reordered')
    means = {cell:row['quiz_correct']/24 for cell,row in cells.items()}
    contrasts = dict(P_minus_OFF=means['P_ON']-means['OFF'], A_minus_OFF=means['A_ON']-means['OFF'], P_minus_A=means['P_ON']-means['A_ON'])
    require(all(math.isclose(terminal[key], value, abs_tol=1e-12) for key,value in contrasts.items()), 'stored contrast differs')
    collection = CapsulePath('metadata/collection', ROOT.files)
    release, custody = read(collection / 'release.json'), read(collection / 'custody.json')
    launch = read(CapsulePath('metadata/launch/launch.json', ROOT.files))
    full = release['observed_wall']-dt.datetime.fromisoformat(launch['started_utc']).timestamp()
    require(release['full_release'] and custody['launch_sha256'] == sha(CapsulePath('metadata/launch/launch.json', ROOT.files))
            and custody['readout_plan_sha256'] == args.plan_sha256 and math.isclose(full, custody['full_launch_to_release_seconds'], abs_tol=1e-5), 'release identity/cost')
    gpu = ET.fromstring((collection / 'release.xml').read_bytes()).find('gpu')
    require(gpu.findtext('uuid') == release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid'] and len(gpu.find('processes')) == 0, 'full release XML')
    require(controller['pid'] == launch['pid'] and controller['plan_sha256'] == args.plan_sha256
            and controller['hard_end'] == min(controller['started_wall']+1800, plan['deadline'], plan['lease_cutoff'])
            and controller['cleanup_reserve'] == 140 and terminal['controller_seconds'] <= 1800
            and controller['started_wall']+terminal['controller_seconds'] <= controller['hard_end']+.001, 'controller bounds')
    workers = sum(row['supervision']['reserved_seconds'] for row in cells.values())
    costs = {key:sum(row['costs'][key] for row in cells.values()) for key in cells['OFF']['costs']}
    require(costs['generation_seconds'] <= workers <= terminal['controller_seconds'] <= full
            and math.isclose(workers, custody['observed_worker_seconds'], abs_tol=1e-6)
            and costs['requests'] <= 96 and costs['output_token_ceiling'] <= 27600 and validation['collection_seconds'] <= 300, 'nested costs/ceilings')
    aligned = {cell:{(row['role'],row['eid'],row['tick']):row for row in data['raw_codes']} for cell,data in cells.items()}
    shared = sorted(set(aligned['P_ON']) & set(aligned['A_ON']))
    comparisons = [dict(role=key[0], eid=key[1], tick=key[2],
        text_equal=aligned['P_ON'][key]['text'] == aligned['A_ON'][key]['text'],
        prompt_equal=aligned['P_ON'][key]['prompt_sha256'] == aligned['A_ON'][key]['prompt_sha256']) for key in shared]
    return dict(status='PASS_RAW_RECOUNT', capsule_sha256=args.capsule_sha256, plan_sha256=args.plan_sha256,
        validation_sha256=sha(args.validation), inventory_files=len(ROOT.files), source_literals=sources,
        cells=cells, contrasts=contrasts, treatment_call_alignment=comparisons,
        unaligned_treatment_calls={cell:[list(key) for key in sorted(set(aligned[cell])-set(shared))] for cell in ('P_ON','A_ON')},
        costs=dict(raw=costs, workers_seconds=workers, controller_seconds=terminal['controller_seconds'],
            full_reservation_seconds=full, full_A40_minutes=full/60, collection_seconds=validation['collection_seconds'],
            accounting='Generation inside workers inside controller inside launch-to-observed-release; collection overlaps, do not add.'),
        lineage=lineage, protocol=protocol, claims=plan['claims'], model_origin=plan['model_origin'],
        disclosure='Prior related collectors, saved-weight audit, and record-readout raw auditor authored by this reviewer; process driver authored by Planck. Shared frozen syntax/record judge, independent world/prompt/score reconstruction. Not blind or fresh-author.',
        limits=['Context-distilled complete own wake+EOS objective, not raw RECORD; selected material and shared OFF, exploratory contrasts.',
                'Boot requests prediction: emission is not spontaneous cognition. Diversity is not information gain; record faithfulness is not prediction competence.',
                'No live/partial data, native tokenizer/model/GPU/SSH/Git/network calls. Native/weight checks rely on bound receipts, not new execution.',
                'No clean-lineage, model-authentication, semantic-nonleakage, operational-parenting, G3/P1/G5/H1/H2 promotion.'])


def self_test():
    examples = [('PREDICT: T\nACT: TRY 1,2,3', 'try'), ('TRY: 1,2,3', 'try'), ('QUIZ: ?', 'reveal'),
                ('DONE', 'done'), ('ACT: TRY 1,2,3\nACT: QUIZ ?', 'invalid'), ('[OUTCOME] True\nACT: TRY 1,2,3', 'invalid'),
                ('hello', 'invalid'), ('ACT: QUIZ T,F,T,F,T,F', 'quiz')]
    for text, expected in examples:
        require(parse_observed_action(text)['kind'] == expected, 'synthetic grammar')
    require(parse_observed_action('ACT: TRY 1,2,3\nPREDICT: T')['predicted'] is None, 'post-action prediction')
    require(parse_observed_action('PREDICT: T\nPREDICT: F\nACT: TRY 1,2,3')['prediction_ambiguous'], 'ambiguous prediction')
    for rule in range(2,6):
        panel = quiz_panel(rule, f'rule{rule}/astra-minimum-20260912/readout')
        require(len(panel) == 6 and sum(truth(rule,triple) for triple in panel) == 3, 'synthetic fixed quiz')
    execution = dict(values=[1,2,3], observed=True, predicted=None, prediction_ambiguous=False)
    require(record_verdict('{"try":[1,2,3],"observed":true,"predicted":null,"relation":"unavailable"}', execution)['eligible'], 'null record')
    require(not record_verdict('{"try":[1,2,3],"observed":false,"predicted":null,"relation":"unavailable"}', execution)['eligible'], 'false record')
    print(json.dumps(dict(status='PREPARATION_FIXTURES_PASS', checks=16, real_capsules_read=0, outcomes_read=0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--capsule', type=Path)
    parser.add_argument('--capsule-sha256')
    parser.add_argument('--validation', type=Path)
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.self_test:
        require(args.capsule is None, 'fixtures never read capsules')
        return self_test()
    require(all((args.capsule, args.capsule_sha256, args.validation, args.plan_sha256)), 'Main complete capsule and pins required; no discovery')
    result = audit(args)
    output = STEM.with_suffix('.json')
    if output.exists():
        require(read(output)['status'] == 'PREPARED_AWAITING_MAIN_CAPSULE', 'completed review already exists')
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'], calls=result['costs']['raw']['requests'], output=str(output))))


if __name__ == '__main__':
    main()
