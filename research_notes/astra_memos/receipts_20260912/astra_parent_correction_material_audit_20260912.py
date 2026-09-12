import collections
import difflib
import hashlib
import json
import re
import tarfile
import zlib
from pathlib import Path


ROOT = Path('/data/home/rohing/dream-state')
TERMINAL = Path('/tmp/astra_parent_correction_terminal_20260912/astra_P1_fresh_correction_20260912_attempt1')
STEM = Path('/tmp/astra_parent_correction_material_audit_20260912')
MARK = re.compile(r'^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$', re.MULTILINE)
IDS = [f'rg/mini_sudoku/{seed}' for seed in range(1850100, 1850132)]
BOARD_ROW = re.compile(r'^[ \t]*[0-4_.](?:[ \t]+[0-4_.]){3}[ \t]*$')


def digest(content):
    return hashlib.sha256(content).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def file_hash(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            hasher.update(block)
    return hasher.hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def inventory(path):
    manifest = load(path / 'artifact_hashes.json')['files']
    require({entry.name for entry in path.iterdir()} == set(manifest) | {'artifact_hashes.json'}, 'inventory names')
    for name, expected in manifest.items():
        require(Path(name).name == name and not (path / name).is_symlink(), 'inventory path')
        require(file_hash(path / name) == expected, f'file hash {name}')
    return dict(path=str(path), inventory_sha256=file_hash(path / 'artifact_hashes.json'), files=manifest)


def act_spans(text):
    return [dict(start_byte=len(text[:match.start()].encode()), end_byte=len(text[:match.end()].encode()),
                 raw=text[match.start():match.end()], action=match.group(2).strip())
            for match in MARK.finditer(text) if match.group(1) == 'ACT']


def format_valid(action):
    lines = action.replace(';', '\n').strip().splitlines()
    return len(lines) == 4 and all(BOARD_ROW.fullmatch(line) and
        all(cell in '1234' for cell in line.split()) for line in lines)


def parse_board(text):
    lines = text.replace(';', '\n').strip().splitlines()
    if len(lines) != 4 or any(not re.fullmatch(r'\s*\d+(?:\s+\d+){3}\s*', line) for line in lines):
        return None
    return [[int(cell) for cell in line.split()] for line in lines]


def public_check(question, action):
    givens = [[0 if cell in ('_', '.', '0') else int(cell) for cell in line.split()]
              for line in question.splitlines() if BOARD_ROW.fullmatch(line)]
    require(len(givens) == 4, 'exact original public puzzle')
    board = parse_board(action)
    if board is None:
        return dict(valid=False, matrix_parseable=False, strict_action_format_valid=format_valid(action))
    expected = {1, 2, 3, 4}
    units = [('row', index + 1, row) for index, row in enumerate(board)]
    units += [('column', column + 1, [board[row][column] for row in range(4)]) for column in range(4)]
    units += [('box', f'r{row + 1}-{row + 2}c{column + 1}-{column + 2}',
               [board[row + vertical][column + horizontal] for vertical in range(2) for horizontal in range(2)])
              for row in (0, 2) for column in (0, 2)]
    violations = [dict(kind=kind, index=index, values=values,
                       duplicates=[value for value, count in sorted(collections.Counter(values).items()) if count > 1],
                       missing=sorted(expected - set(values)), out_of_domain=sorted(set(values) - expected))
                  for kind, index, values in units if set(values) != expected]
    changed = [dict(row=row + 1, column=column + 1, given=givens[row][column], actual=board[row][column])
               for row in range(4) for column in range(4) if givens[row][column] and givens[row][column] != board[row][column]]
    return dict(valid=not violations and not changed, matrix_parseable=True, board=board, original_givens=givens,
                strict_action_format_valid=format_valid(action), unit_violations=violations, changed_givens=changed,
                givens_retained=sum(bool(cell) for row in givens for cell in row) - len(changed),
                givens_total=sum(bool(cell) for row in givens for cell in row))


def unique_rows(rows, kind, key):
    selected = [row for row in rows if row['kind'] == kind]
    result = {row[key]: row for row in selected}
    require(len(result) == len(selected), f'duplicate {kind}')
    return result


def source_span(capture, pointer, text, status, reason):
    require(capture['text'].count(text) == 1, 'ambiguous span')
    start = capture['text'].index(text)
    return dict(pointer=pointer, request_index=capture['request_index'], output_sha256=capture['output_sha256'],
                prompt_sha256=capture['prompt_sha256'], start_byte=len(capture['text'][:start].encode()),
                end_byte=len(capture['text'][:start + len(text)].encode()), text=text,
                span_sha256=digest(text.encode()), classification=status, reason=reason,
                training_approved=False)


def audit_arm(mode):
    directory = TERMINAL / mode
    sealed = inventory(directory)
    records = load(directory / 'captures.json')
    config = load(directory / 'config.json')
    results = load(directory / 'results.json')
    require(config['mode'] == mode and not config['synthetic'], 'native mode')
    require([record['episode_id'] for record in records] == config['episode_ids'] == IDS, 'ordered 32 episodes')
    ledger_bytes = (directory / 'ledger.jsonl').read_bytes()
    ledger_lines = ledger_bytes.splitlines(keepends=True)
    ledger = [json.loads(line) for line in ledger_lines]
    generations = [json.loads(line) for line in (directory / 'generations.jsonl').read_bytes().splitlines()]
    events = unique_rows(ledger, 'act', 'execution_id')
    scratches = unique_rows(ledger, 'scratchpad', 'execution_id')
    requests = unique_rows(generations, 'request', 'request_index')
    outputs = unique_rows(generations, 'output', 'request_index')
    checks = unique_rows(generations, 'live_input_check', 'request_index')
    require([row['capture'] for row in ledger if row['kind'] == 'correction_capture'] == records, 'embedded captures')
    prefixes = {}
    running = hashlib.sha256()
    for line, row in zip(ledger_lines, ledger):
        prefixes.setdefault(running.hexdigest(), len(prefixes))
        if row['kind'] == 'scratchpad' and row['generation']['batch_index'] == 0:
            require(row['generation']['ledger_prefix_sha256'] == running.hexdigest(), 'batch ledger prefix')
        running.update(line)
    batches = collections.defaultdict(list)
    for scratch in scratches.values():
        batches[scratch['generation']['batch_id']].append(scratch)
    for batch_id, group in batches.items():
        group.sort(key=lambda item: item['generation']['batch_index'])
        generation = group[0]['generation']
        require([row['generation']['batch_index'] for row in group] == list(range(generation['batch_size'])), 'batch completeness')
        require(generation['ledger_prefix_sha256'] in prefixes, 'prefix exists')
        for row in group:
            require(all(row['generation'][key] == generation[key] for key in
                ('batch_size', 'ledger_prefix_sha256', 'backend_identity_sha256', 'max_tokens', 'temperature', 'base_seed', 'seed_salt')), 'batch common fields')
        receipt = dict(ledger_sha256=generation['ledger_prefix_sha256'], execution_ids=[row['execution_id'] for row in group],
            prompt_sha256=[row['generation']['prompt_sha256'] for row in group],
            output_sha256=[row['generation']['output_sha256'] for row in group], identity=generation['backend_identity'],
            max_tokens=generation['max_tokens'], seeds=[row['generation']['seed'] for row in group])
        require(digest(encoded(receipt)) == batch_id, 'batch identity')
    all_captures, cells, candidates, execution_ids = [], [], [], []
    for record_index, record in enumerate(records):
        episode = record['episode_id']
        require(digest(record['question'].encode()) == record['question_sha256'], 'original question hash')
        require([wake['tick'] for wake in record['wakes']] == [1, 2], 'two wakes')
        captures = [wake['generation'] for wake in record['wakes']] + [scratch['capture'] for scratch in record['scratchpads']]
        for capture in captures:
            index = capture['request_index']
            require(all(capture[key] == requests[index][key] for key in
                ('prompt', 'rendered_prompt', 'prompt_sha256', 'prompt_tokens', 'seed', 'max_tokens', 'temperature')), 'request join')
            require(all(capture[key] == outputs[index][key] for key in ('text', 'output_sha256')), 'output join')
            for field, hash_field in (('prompt', 'prompt_sha256'), ('rendered_prompt', 'rendered_sha256'), ('text', 'output_sha256')):
                require(digest(capture[field].encode()) == capture[hash_field], f'{field} hash')
            require(capture['prompt_tokens'] + capture['max_tokens'] <= 4096 and capture['temperature'] == .7, 'headroom/temperature')
            require(checks[index]['fits'] and checks[index]['output_headroom'] == capture['max_tokens'] and
                all(checks[index][key] == capture[key] for key in ('prompt', 'rendered_prompt', 'prompt_tokens')), 'live check')
            require(record['question'] in capture['prompt'], 'original question visible')
            require(config['packages'][mode] in capture['prompt'], 'teacher exposure')
            identity = requests[index]['source_identity']
            require(identity['model_input'] == config['model_path'] and identity['adapter_input'] is None and identity['adapter_files'] == {}, 'configured no-adapter source')
        all_captures.extend(captures)
        wake_cells = []
        for wake in record['wakes']:
            capture = wake['generation']
            require(capture['max_tokens'] == 400 and capture['seed'] == ((zlib.crc32(f'{episode}/{wake["tick"]}'.encode()) ^ 7101) & 0x7fffffff), 'wake seed')
            require(act_spans(capture['text']) == wake['raw_act_spans'], 'raw ACT exact bytes')
            require([span['action'] for span in wake['raw_act_spans']] == [action['action'] for action in wake['actions']], 'all raw ACT order')
            for action in wake['actions']:
                require(events[action['execution_id']] == action, 'action ledger join')
                require(action['episode_id'] == episode and action['occurrence_id'] == record['occurrence_id'] and action['tick'] == wake['tick'], 'action episode/tick')
                require(all(action['generation'][key] == capture[key] for key in ('prompt_sha256', 'output_sha256', 'seed', 'max_tokens', 'temperature')), 'action generation')
                require(action['generation']['identity'] == requests[capture['request_index']]['source_identity'], 'action loader source')
                execution_ids.append(action['execution_id'])
            first = wake['actions'][0] if wake['actions'] else None
            wake_cells.append(dict(n_actions=len(wake['actions']), first_score=first['score'] if first else None,
                first_native_accepted=bool(first and first['score'] == 1),
                first_native_partial=bool(first and 0 < first['score'] < 1),
                first_action_format_valid=bool(first and format_valid(first['action'])),
                public_first_valid=bool(first and public_check(record['question'], first['action'])['valid']),
                all_scores=[action['score'] for action in wake['actions']],
                all_public_valid=[public_check(record['question'], action['action'])['valid'] for action in wake['actions']]))
        require(record['summary']['ticks'] == 2 and record['summary']['episode_id'] == episode and
                record['summary']['n_acts'] == sum(wake['n_actions'] for wake in wake_cells), 'summary joins')
        first_actions = record['wakes'][0]['actions']
        require(len(first_actions) == len(record['scratchpads']) == len(record['injections']), 'one scratch per first ACT')
        second_prompt = record['wakes'][1]['generation']['prompt']
        for action, scratch, binding in zip(first_actions, record['scratchpads'], record['injections']):
            row, capture = scratch['record'], scratch['capture']
            require(scratches[action['execution_id']] == row and row['speaker'] == 'child', 'own scratch ledger join')
            require(all(row[key] == action[key] for key in ('execution_id', 'episode_id', 'occurrence_id', 'tick', 'action', 'score', 'outcome')), 'scratch action source')
            generation = row['generation']
            require(all(generation[key] == capture[key] for key in ('prompt', 'prompt_sha256', 'output_sha256', 'seed', 'max_tokens', 'temperature')), 'scratch capture generation')
            require(capture['text'] == row['text'] and capture['max_tokens'] == 100, 'scratch raw bytes')
            require(generation['seed'] == ((zlib.crc32(row['execution_id'].encode()) ^ 7101 ^ generation['seed_salt']) & 0x7fffffff), 'scratch seed')
            require(digest(encoded(generation['backend_identity'])) == generation['backend_identity_sha256'] and
                generation['backend_identity'] == requests[capture['request_index']]['source_identity'], 'scratch identity')
            feedback = re.fullmatch(r'attempt (\d+): verifier score ([0-9.]+) \((.*?)\)', action['outcome'])
            require(feedback is not None, 'public measured feedback')
            verdict = 'accepted' if action['score'] == 1 else 'not accepted; partial credit' if action['score'] > 0 else 'not accepted'
            require(feedback[2] == f'{action["score"]:.2f}' and feedback[3] == verdict, 'display rounding')
            block = '\n'.join([f'Situation: {episode}', f'Execution: {action["execution_id"]}', f'Attempt: {feedback[1]}',
                'ACT submitted: ' + json.dumps(action['action'], ensure_ascii=False), f'Displayed verifier score: {feedback[2]}',
                f'Feedback: {verdict}', '', 'Scratchpad:'])
            require(capture['prompt'] == record['wakes'][0]['generation']['prompt'].rstrip('\n') + '\n\n' + block, 'public-only scratch prompt construction')
            expected_block = f'[Scratchpad from {action["execution_id"]} after first-wake public outcome]\n' + row['text']
            require(binding['block'] == expected_block and binding['execution_id'] == action['execution_id'] and
                binding['scratchpad_sha256'] == digest(row['text'].encode()) and binding['block_sha256'] == digest(expected_block.encode()) and
                binding['next_prompt_sha256'] == digest(second_prompt.encode()) and
                second_prompt.encode()[binding['start_byte']:binding['end_byte']] == expected_block.encode(), 'second prompt exact injection')
            require(record['wakes'][0]['generation']['request_index'] < capture['request_index'] < record['wakes'][1]['generation']['request_index'], 'causal request order')
        accepted = [wake['first_native_accepted'] for wake in wake_cells]
        qualifying = all(wake['n_actions'] == 1 for wake in wake_cells) and accepted == [False, True] and bool(record['scratchpads'][0]['record']['text'].strip())
        cells.append(dict(episode_id=episode, wakes=wake_cells, qualifying_correction=qualifying,
            multi_act=any(wake['n_actions'] > 1 for wake in wake_cells),
            transition=('success' if accepted[0] else 'failure') + '_to_' + ('success' if accepted[1] else 'failure')))
        if qualifying:
            candidates.append(candidate_audit(mode, record_index, record))
    indices = [capture['request_index'] for capture in all_captures]
    require(len(indices) == len(set(indices)) and set(indices) == set(requests) == set(outputs) == set(checks), 'complete generation joins')
    require(len(execution_ids) == len(set(execution_ids)) and set(execution_ids) == set(events), 'complete unique execution joins')
    summary = dict(denominator=32, ticks=64,
        first_act_solves=[sum(cell['wakes'][tick]['first_native_accepted'] for cell in cells) for tick in (0, 1)],
        first_act_formats=[sum(cell['wakes'][tick]['first_action_format_valid'] for cell in cells) for tick in (0, 1)],
        first_act_native_partial=[sum(cell['wakes'][tick]['first_native_partial'] for cell in cells) for tick in (0, 1)],
        first_act_failure_opportunities=sum(bool(cell['wakes'][0]['n_actions']) and not cell['wakes'][0]['first_native_accepted'] for cell in cells),
        qualifying_corrections=len(candidates), multi_act_episodes=sum(cell['multi_act'] for cell in cells),
        all_actions=len(events), generation_requests=len(all_captures), generated_tokens=sum(capture['output_tokens'] for capture in all_captures),
        package_presentations=sum(request['teacher_presentations'] for request in requests.values()),
        cumulative_package_tokens=sum(request['teacher_presentations'] * request['teacher_tokens'] for request in requests.values()))
    require(all(results[key] == value for key, value in summary.items()), 'stored endpoints vs independent replay')
    require([candidate['capture_sha256'] for candidate in candidates] == [row['capture_sha256'] for row in results['candidates']], 'candidate hash join')
    for cell, original in zip(cells, results['episodes']):
        require(cell['episode_id'] == original['episode_id'] and cell['qualifying_correction'] == original['qualifying_correction'] and cell['multi_act'] == original['multi_act'], '32 stored cells')
        for wake, original_wake in zip(cell['wakes'], original['wakes']):
            require(all(wake[key] == original_wake[key] for key in ('n_actions', 'first_native_accepted', 'first_native_partial', 'first_action_format_valid')), 'stored per-wake cell')
    summary.update(wake_requests=64, scratchpad_requests=len(scratches),
        actions_by_wake=[sum(cell['wakes'][tick]['n_actions'] for cell in cells) for tick in (0, 1)],
        missing_action_cells=sum(any(not wake['n_actions'] for wake in cell['wakes']) for cell in cells),
        transition_counts=dict(collections.Counter(cell['transition'] for cell in cells)),
        first_act_solve_ids=[[cell['episode_id'] for cell in cells if cell['wakes'][tick]['first_native_accepted']] for tick in (0, 1)],
        public_first_valid=[sum(cell['wakes'][tick]['public_first_valid'] for cell in cells) for tick in (0, 1)])
    return dict(mode=mode, evidence=sealed, independent_replay='PASS_STDLIB_ONLY_NO_MODEL_NO_VERIFIER', summary=summary,
                cells=cells, candidates=candidates, question_hashes=[record['question_sha256'] for record in records]), config


def candidate_audit(mode, index, record):
    episode = record['episode_id']
    first, second = record['wakes']
    scratch = record['scratchpads'][0]['capture']
    pointer = f'/{index}/scratchpads/0/capture/text'
    first_check = public_check(record['question'], first['actions'][0]['action'])
    second_check = public_check(record['question'], second['actions'][0]['action'])
    require(not first_check['valid'] and second_check['valid'], 'candidate independently public-valid correction')
    raw_scratch_act = act_spans(scratch['text'])[0]['action']
    quoted = raw_scratch_act.startswith('"') and raw_scratch_act.endswith('"')
    inspected_payload = raw_scratch_act[1:-1] if quoted else raw_scratch_act
    require(public_check(record['question'], inspected_payload)['valid'], 'scratch contains publicly valid board')
    claims, exclusions, eligible = [], [], []
    def claim(text, status, reason):
        claims.append(source_span(scratch, pointer, text, status, reason))
    if mode == 'process':
        claim('The previous attempt had some numbers repeated in rows and columns,', 'CONTRADICTED_IN_PART',
              'No row repeats a number. Column 4 repeats 1 (r2/r3). Splitting the conjunction exposes a false row diagnosis; a correct later board does not repair it.')
        claim('and the last row did not fit the constraints.', 'SUPPORTED', 'Last row [1,5,3,2] contains out-of-domain 5 and lacks 4.')
        claim('I need to ensure each row, column, and 2x2 subgrid contains each number from 1 to 4 exactly once.', 'SUPPORTED_RULE_REMINDER_NOT_VERIFIED_INTROSPECTION',
              'Public rules explicitly require this. It echoes the visible rules/process instruction and is not evidence of an independently discovered method or executed check.')
        decision = 'EXCLUDE_UNCHANGED_SCRATCHPAD_AS_TRUTHFUL_DIAGNOSTIC_LESSON'
        exclusions.append(dict(scope='entire unchanged Scratchpad as a factual diagnostic target', reason='false within-row duplication claim; retain raw artifact, do not silently sanitize'))
    elif episode.endswith('118'):
        claim('I changed the last row', 'SUPPORTED', 'Last row changes [4,3,2,1] to [2,3,1,4]. Other rows also change; the text does not claim only the last row changed.')
        claim('to see if the pattern would work differently.', 'UNSUPPORTED_AS_VERIFIED_MOTIVE',
              'An expressed hypothesis/intention, not an observable causal explanation. It is not contradicted merely because motives cannot be verified.')
        claim('This time, I tried to break the pattern', 'UNSUPPORTED_VAGUE_SELF_EXPLANATION',
              'No defined pattern or observable test identifies this mental operation; not proof of learning or diagnosis.')
        claim('but still keep the numbers unique in rows, columns, and subgrids.', 'SUPPORTED_BEHAVIOR_NOT_VERIFIED_MOTIVE',
              'Both first and proposed boards satisfy all 12 units. The original failure was changed givens r4c3=1 and r4c4=4, not unit uniqueness; that cause is omitted.')
        decision = 'PRESERVE_RAW_HYPOTHESIS_NOT_ESTABLISHED_DIAGNOSTIC_LESSON'
        exclusions.append(dict(scope='whole Scratchpad as a validated causal lesson or unchanged executable ACT',
            reason='unverified/vague intention; misses original-given error; Scratchpad ACT has literal outer quotes, which are not silently removed'))
    else:
        claim("The previous attempt had some numbers in the right place but wasn't fully correct.", 'SUPPORTED',
              'Four of five ORIGINAL givens retained; invalid 5, changed r2c4 given, column/box conflicts. Also 12/16 cells match the later independently public-valid board; no reference key used.')
        claim('I need to ensure each row, column, and 2x2 subgrid contains the numbers 1-4 exactly once.', 'SUPPORTED_RULE_REMINDER_NOT_VERIFIED_INTROSPECTION',
              'Correct public rule reminder, not a specific failure diagnosis. Directly available in the question even under sham; not evidence process teacher supplied a superior lesson.')
        decision = 'UNCHANGED_MODEST_RULE_REMINDER_PLUS_VALID_OWN_SOLUTION_SURVIVES_CONTENT_SCREEN_ONLY'
        eligible.append(source_span(scratch, pointer, scratch['text'], 'WHOLE_RAW_CANDIDATE_FOR_LATER_CONSIDERATION_ONLY',
            'No contradicted factual claim detected. PREDICT is an uncalibrated forecast, not an outcome fact. Preserve all raw bytes; not admission, demonstrated usefulness, learning, or a truthful-reflection certificate.'))
    prediction = next(match.group(0) for match in MARK.finditer(scratch['text']) if match.group(1) == 'PREDICT')
    claim(prediction, 'UNSUPPORTED_AS_CALIBRATED_FORECAST_NOT_A_FALSE_OUTCOME_REPORT',
          'Prediction is child output, not an observed score; the Scratchpad ACT was never executed. Later wake2 gets 1.0. Do not relabel this as authoritative reward or measured calibration.')
    eligible.append(source_span(second['generation'], f'/{index}/wakes/1/generation/text', second['raw_act_spans'][0]['raw'],
        'EXACT_OWN_ACT_FOR_LATER_CONSIDERATION_ONLY', 'Minimal standalone own-output action line independently satisfies original givens plus all 12 units. Not an explanatory lesson; no corpus constructed.'))
    eligible.append(source_span(scratch, pointer, inspected_payload, 'EXACT_OWN_BOARD_SUBSTRING_FOR_LATER_CONSIDERATION_ONLY',
        'Already present before wake2; same board as the second action. If quoted, this is explicitly the inner byte span, not a claim the unchanged ACT parses. Not an independent second example.'))
    for item in claims:
        if item['classification'] == 'SUPPORTED' or item['classification'].startswith('SUPPORTED_RULE'):
            eligible.append(dict(item, classification='SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR',
                reason=item['reason'] + ' A fragment annotation only; retain and expose its full raw context.'))
    exclusions.extend([
        dict(scope='failed first ACT as a positive solution; false/unverified claims as factual targets', reason='preserve as evidence/negative experience only, not a blanket positive-target export'),
        dict(scope='teacher package, public question, outcome wrapper, injection header', reason='not child-authored supervised target bytes'),
        dict(scope='PREDICT as verified reward; duplicate Scratchpad/wake2 board as two independent examples', reason='unmeasured forecast and same-episode re-emission'),
    ])
    tokens = lambda text: re.findall(r'\w+', text.lower())
    question_words = tokens(record['question'])
    package = load(TERMINAL / mode / 'config.json')['packages'][mode]
    overlaps = []
    for label, source in [('teacher_package', tokens(package)), ('public_question', question_words)]:
        matches = difflib.SequenceMatcher(None, tokens(scratch['text']), source, autojunk=False).get_matching_blocks()
        overlaps.extend(dict(source=label, words=match.size, normalized_text=' '.join(tokens(scratch['text'])[match.a:match.a + match.size]))
                        for match in matches if match.size >= 4)
    return dict(episode_id=episode, mode=mode, capture_index=index, capture_sha256=digest(encoded(record)),
        question=record['question'], question_sha256=record['question_sha256'],
        first_action=first['actions'][0]['action'], first_output=first['generation']['text'], first_public_check=first_check,
        second_action=second['actions'][0]['action'], second_output=second['generation']['text'], second_public_check=second_check,
        native_scores=[first['actions'][0]['score'], second['actions'][0]['score']],
        scratchpad_raw=scratch['text'], scratchpad_output_sha256=scratch['output_sha256'],
        scratchpad_act_raw=raw_scratch_act, scratchpad_act_strict_format_valid=format_valid(raw_scratch_act),
        quoted_inner_board_inspected_explicitly=quoted, scratchpad_board_matches_wake2=inspected_payload == second['actions'][0]['action'],
        scratchpad_act_executed=False, injection=record['injections'][0],
        generation_chain=[dict(request_index=capture['request_index'], prompt_sha256=capture['prompt_sha256'], output_sha256=capture['output_sha256'])
                          for capture in (first['generation'], scratch, second['generation'])],
        claims=claims, eligible_span_annotations=eligible, exclusions=exclusions, decision=decision,
        lexical_overlap_4plus_words=overlaps,
        echo_assessment='All prompts include a teacher package and the public rules. Generic rule repetition is observable; causal attribution or absence of subtler influence is not established. No full teacher-package copy detected in these candidate Scratchpads.',
        training_approved=False, useful_training_demonstrated=False)


def main():
    arms, configs = {}, {}
    for mode in ('process', 'sham'):
        arms[mode], configs[mode] = audit_arm(mode)
    require(arms['process']['question_hashes'] == arms['sham']['question_hashes'], 'paired original questions')
    initial = inventory(Path('/tmp/astra_parent_correction_process_20260912/process'))
    require(initial['files'] == arms['process']['evidence']['files'], 'initial vs terminal process byte identity')
    source_archive = Path('/tmp/astra_parent_correction_source_30cdad8e.tar.gz')
    source_matches = []
    with tarfile.open(source_archive, 'r:gz') as archive:
        for source, expected in configs['process']['sources'].items():
            if '/astra_sources/' not in source:
                continue
            relative = source.split('/30cdad8e10fe99873787a0f6ba7bb32d9ac42fb6/', 1)[1]
            member = archive.getmember(relative)
            source_bytes = archive.extractfile(member).read()
            require(digest(source_bytes) == expected == configs['sham']['sources'][source], 'original source pin')
            current = ROOT / relative
            source_matches.append(dict(recorded_path=source, archived_member=relative, sha256=expected,
                current_checkout_sha256=file_hash(current) if current.is_file() else None))
    require(any(row['archived_member'] == 'organism_v6/parent_correction_diagnostic.py' for row in source_matches), 'collector source present')
    native_path = Path('/tmp/astra_parent_correction_native_replay_20260912.jsonl')
    native_replays = [json.loads(line) for line in native_path.read_bytes().splitlines()]
    require(len(native_replays) == 2, 'native replay pair')
    for replay, mode in zip(native_replays, ('process', 'sham')):
        require(all(replay[key] == arms[mode]['summary'][key] for key in
            ('first_act_solves', 'first_act_formats', 'first_act_native_partial', 'qualifying_corrections', 'multi_act_episodes', 'all_actions')), 'native replay agreement')
    capsule = Path('/tmp/astra_parent_correction_terminal_20260912.tgz')
    capsule_hash = file_hash(capsule)
    require(capsule_hash == 'bd4f7c5d035f423f27c262efbb17cc90bcab57cb30a45d894f7b3c98db65dd5b', 'terminal capsule')
    pair_cells = []
    for process, sham in zip(arms['process']['cells'], arms['sham']['cells']):
        require(process['episode_id'] == sham['episode_id'], 'paired IDs')
        pair_cells.append(dict(episode_id=process['episode_id'], process=process, sham=sham))
    pair_solves = []
    for tick in (0, 1):
        pair_solves.append(dict(both=sum(row['process']['wakes'][tick]['first_native_accepted'] and row['sham']['wakes'][tick]['first_native_accepted'] for row in pair_cells),
            process_only=sum(row['process']['wakes'][tick]['first_native_accepted'] and not row['sham']['wakes'][tick]['first_native_accepted'] for row in pair_cells),
            sham_only=sum(not row['process']['wakes'][tick]['first_native_accepted'] and row['sham']['wakes'][tick]['first_native_accepted'] for row in pair_cells),
            neither=sum(not row['process']['wakes'][tick]['first_native_accepted'] and not row['sham']['wakes'][tick]['first_native_accepted'] for row in pair_cells)))
    report = dict(schema='astra-parent-correction-material-audit-v1', audit_date='2026-09-12', scope='READ_ONLY_DEV_PUBLIC_CONSTRAINT_MATERIAL_DIAGNOSIS',
        boundary=dict(formal_C11='DEFERRED', admission=False, training=False, model_calls=0, GPU_calls=0, network_calls=0,
            repo_edits=False, reference_answer_used=False, final_gym_used=False, no_gate_lowering=True,
            byte_span_convention='UTF-8 zero-based half-open offsets into the specified decoded text field, not the serialized JSON file'),
        decision='NO_PROCESS_ADVANTAGE; PROCESS_RAW_DIAGNOSIS_CONTRADICTED; SHAM1850124_WHOLE_RAW_MODEST_CANDIDATE_ONLY',
        arms=arms, paired_cells=pair_cells, paired_first_act_acceptance=pair_solves,
        sources=dict(initial_process=initial, capsule=dict(path=str(capsule), sha256=capsule_hash),
            original_source_archive=dict(path=str(source_archive), sha256=file_hash(source_archive), joined_files=source_matches),
            native_replay=dict(path=str(native_path), sha256=file_hash(native_path), independent_summary_agreement=True),
            prospective_memo=dict(path=str(ROOT / 'research_notes/astra_memos/ASTRA_FRESH_PARENT_CORRECTION_2026-09-12.md'),
                sha256=file_hash(ROOT / 'research_notes/astra_memos/ASTRA_FRESH_PARENT_CORRECTION_2026-09-12.md')),
            audit_script=dict(path=__file__, sha256=file_hash(__file__))),
        limits=['Integrity and recorded loader identity are not model-origin authentication or global freshness certification.',
            'Original repo sources were hash-joined from local archive; remote native package/base bytes were not independently re-read.',
            'Token totals and headroom are receipt-consistent, not retokenized; no tokenizer/model imported.',
            'Only the three qualifying Scratchpads receive semantic claim review; other cells are endpoint/constraint replay, not material certification.',
            'All three Scratchpads already contain their later solved board. Same-episode reuse is not independently correct diagnosis, causal reflection benefit, persistence, or learning.',
            'Fixed 97-token package per call; unequal actual requests and output tokens prevent a matched realized-dose claim.'],
        next_comparison=dict(status='RECOMMENDATION_ONLY_NOT_AUTHORIZATION_OR_CORPUS',
            proposal='If Main elects existing gated V3 sleep: compare unchanged sham1850124 whole raw Scratchpad against its exact child-authored corrected ACT-only span, with identical source episode, base lineage, optimization/exposure opportunities and a common no-sleep/OFF baseline; report the unavoidable raw-token difference. Use fresh-process teacher-free OFF/ON evaluation on fixed disjoint problems, not this already-solved item.',
            question='Does the supported raw rule reminder plus own solution yield more teacher-free transfer than rehearsal of the same own solution alone?',
            exclusions='Do not pool process false-diagnosis text, upgrade sham118 speculative motives to truth, add a curriculum/guard, or infer H1/P1 from one item.',
            limitation='A one-item DEV comparison may fail or be inconclusive; it cannot establish broad reflection truth, usefulness, or process-teacher superiority.'))
    json_path = STEM.with_suffix('.json')
    json_path.write_text(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + '\n')
    markdown = render_markdown(report, file_hash(json_path))
    STEM.with_suffix('.md').write_text(markdown)
    print(json.dumps(dict(status='PASS', outputs={str(path): file_hash(path) for path in
        (STEM.with_suffix('.md'), json_path, Path(__file__))}, summary={mode: arms[mode]['summary'] for mode in arms}), sort_keys=True))


def render_markdown(report, json_hash):
    lines = ['# Parent correction: bounded public-constraint/material audit', '',
        '2026-09-12. DEV diagnosis only; formal C11 deferred. No repo edits, git, network, GPU, launches, kills, training, admission, corpus construction, or gate changes.', '',
        '## Material decision', '',
        '- **No observed signal favoring process.** Both arms move from 1/32 to 2/32 first-ACT solves. Qualifying corrections are process 1, sham 2; raw multi-ACT episodes 15 vs 7. This is descriptive, not an equivalence claim.',
        '- **Process 1850124: do not use unchanged Scratchpad as a truthful diagnostic lesson.** Its row-repetition claim is false despite a publicly valid proposed solution.',
        '- **Sham 1850118: preserve raw exploration, not a validated diagnostic lesson.** Actual last-row change and unit uniqueness are supported; motives/pattern explanation are not verified. It omits that the first board failed original givens, and its Scratchpad ACT has literal quotes.',
        '- **Sham 1850124: one unchanged modest lesson candidate survives content screening.** Its correctness observation and public rule reminder are supported, and its proposed board is valid. Preserve the WHOLE raw Scratchpad, including its uncalibrated PREDICT. No factual contradiction found is not a usefulness, introspection-truth, learning, or admission certificate.',
        '- All three Scratchpads already contain the exact subsequently solved board. Wake2 is consistent with reuse/re-emission of own text; correction does not isolate an explanatory or learning mechanism.', '',
        '## Evidence and replay', '',
        'Independent deterministic standard-library-only replay checks sealed file inventory, all 32 capture/ledger joins per arm, every request/output/live-headroom record, raw ACT order, own source identities, Scratchpad batch receipt and exact ledger prefix, public-outcome request construction, same-episode injection byte spans and chronology. No native verifier, model, reference answer, or final-gym data used.',
        'Original process copy and terminal process are byte-identical. Both replay summaries agree with Main\'s original-source native replay. Original repo source files are joined to 30cdad8e10fe99873787a0f6ba7bb32d9ac42fb6 via their archived bytes, not inferred from current checkout or git. Remote package/base bytes and origin authentication remain outside this audit.', '',
        f'- Terminal capsule: `{report["sources"]["capsule"]["path"]}` SHA-256 `{report["sources"]["capsule"]["sha256"]}`.',
        f'- Main CPU replay: `{report["sources"]["native_replay"]["path"]}` SHA-256 `{report["sources"]["native_replay"]["sha256"]}`.',
        f'- Machine-readable full audit: `{STEM.with_suffix(".json")}` SHA-256 `{json_hash}`.',
        f'- Deterministic audit script: `{__file__}` SHA-256 `{report["sources"]["audit_script"]["sha256"]}`.', '',
        '## Endpoints (first ACT, denominator 32 per arm)', '',
        '| Endpoint | Process | Sham |', '|---|---:|---:|']
    for key in ('first_act_solves', 'first_act_formats', 'first_act_native_partial', 'first_act_failure_opportunities',
                'qualifying_corrections', 'multi_act_episodes', 'all_actions', 'actions_by_wake', 'wake_requests',
                'scratchpad_requests', 'generation_requests', 'generated_tokens', 'cumulative_package_tokens'):
        lines.append(f'| {key} | {report["arms"]["process"]["summary"][key]} | {report["arms"]["sham"]["summary"][key]} |')
    lines.extend(['', 'Format includes 1–4 domain validity, not just a rectangular board. Native partial scores are not constraint-validity certificates. The reported 0.68 for 1850124 is rounded from 0.675; 1850118 sham reports 0.34 from 0.3375.',
        'All raw wake ACTs remain recorded. Multi-ACT cells are nonqualifying even when a later ACT solves; ACT strings within Scratchpad are NOT executed actions. Native first-ACT endpoints and all-action best scores must not be substituted for each other.',
        'Each request contains the fixed 97-token package. Process/sham have 99/96 actual package presentations and 12007/9449 generated tokens: equal wake opportunities do not mean equal realized dose. Token counts are receipt-checked, not retokenized.', '',
        f'Paired first-ACT acceptance (wake1, wake2): `{json.dumps(report["paired_first_act_acceptance"], sort_keys=True)}`.', '',
        '## Candidate-level public checks and exact own claims', ''])
    for mode in ('process', 'sham'):
        for candidate in report['arms'][mode]['candidates']:
            lines.extend([f'### {mode} {candidate["episode_id"]}', '',
                f'Capture hash `{candidate["capture_sha256"]}`; question hash `{candidate["question_sha256"]}`.',
                f'Scratchpad SHA-256 `{candidate["scratchpad_output_sha256"]}`. Generation indices: `{[item["request_index"] for item in candidate["generation_chain"]]}`.', '',
                '**Original public givens**', '```text', '\n'.join(' '.join(str(cell) if cell else '_' for cell in row) for row in candidate['first_public_check']['original_givens']), '```',
                f'First ACT: `{candidate["first_action"]}`.',
                f'Second ACT: `{candidate["second_action"]}`.',
                'Second ACT independently passes all original givens, all four rows, all four columns and all four 2×2 boxes.',
                f'First ACT changed givens: `{json.dumps(candidate["first_public_check"]["changed_givens"], sort_keys=True)}`.',
                f'First ACT unit violations: `{json.dumps(candidate["first_public_check"]["unit_violations"], sort_keys=True)}`.', '',
                '**WHOLE raw own Scratchpad (unaltered)**', '```text', candidate['scratchpad_raw'], '```',
                'The code fence is presentation only; the JSON raw field/hash is authoritative for trailing newline bytes.', ''])
            for claim in candidate['claims']:
                lines.append(f'- `{claim["text"]}` — **{claim["classification"]}**. {claim["reason"]}')
            lines.extend(['', f'Decision: **{candidate["decision"]}**.',
                f'Teacher/rule echoes: {candidate["echo_assessment"]} Direct 4+-word normalized overlaps: `{json.dumps(candidate["lexical_overlap_4plus_words"], sort_keys=True)}`.', '',
                '**Minimal exact spans for later consideration, NOT admission or a rewritten lesson**',
                'Offsets are UTF-8 zero-based half-open bytes into the named decoded `captures.json` text field, not serialized JSON offsets. All selected text, parent-output hashes and span hashes are in JSON; no examples are assembled.'])
            for span in candidate['eligible_span_annotations']:
                lines.append(f'- `{span["pointer"]}` bytes `[{span["start_byte"]},{span["end_byte"]})`: **{span["classification"]}**, span SHA-256 `{span["span_sha256"]}`. {span["reason"]}')
            lines.append('')
    lines.extend(['## All 32 paired cells', '',
        'Scores list EVERY ACT in order. `M` means at least one multi-ACT wake; `Q` means qualifying one-ACT-each correction. Blank flags imply neither. Format and public-validity bits are available per wake in JSON.', '',
        '| ID suffix | Process wake1 / wake2 native scores | Flags | Sham wake1 / wake2 native scores | Flags |',
        '|---|---|---|---|---|'])
    for row in report['paired_cells']:
        format_cell = lambda cell: ' / '.join(str(wake['all_scores']) for wake in cell['wakes'])
        flags = lambda cell: ('M' if cell['multi_act'] else '') + ('Q' if cell['qualifying_correction'] else '')
        lines.append(f'| {row["episode_id"].split("/")[-1]} | {format_cell(row["process"])} | {flags(row["process"])} | {format_cell(row["sham"])} | {flags(row["sham"])} |')
    lines.extend(['', '## Smallest next comparison (recommendation only)', '', report['next_comparison']['proposal'], '',
        report['next_comparison']['question'], '', report['next_comparison']['exclusions'], '', report['next_comparison']['limitation'], '',
        'Keep the entire original text and ledger as evidence. Do not silently replace the false process diagnosis with an auditor-written truthful lesson; do not remove quotes/predictions and call the result unchanged. Span annotations identify possible future scopes, not an admitted corpus. Existing provenance/contamination/claim gates still apply; no new broad guard or curriculum is proposed.', ''])
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
