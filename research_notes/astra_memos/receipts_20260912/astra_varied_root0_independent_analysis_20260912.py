import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import tarfile
import xml.etree.ElementTree as ET


BASE = Path('/tmp/astra_varied_pair_root0_terminal_20260912')
ARCHIVE = Path('/tmp/astra_varied_pair_root0_terminal_20260912.tgz')
VALIDATION = Path('/tmp/astra_varied_pair_root0_terminal_20260912.tgz.validation.json')
PREPARE = Path('/tmp/astra_varied_memory_native_prepare_20260912.json')
OUTPUT = Path('/tmp/astra_varied_root0_independent_analysis_20260912.json')
PREFIX = 'astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/fits_root0_attempt1'
ROOT = BASE / PREFIX
EXPECTED_CAPSULE = 'cce875ffcc8c00ccda781efe7de895e2ff68aa914afc9bb000b061d1aef545c0'
ARMS = ('FOUR_VIEW', 'SINGLE_VIEW')
COLORS = {'red', 'green', 'blue', 'yellow'}
CHECKS = []
READ_HASHES = {}


def require(condition, description):
    if not condition:
        raise ValueError(description)
    CHECKS.append(description)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    path = Path(path)
    require(path.name not in {'reduction.json', 'usage.json', 'arm-result.json',
                              'capture-result.json'}, 'No stored reduction used: ' + str(path))
    data = path.read_bytes()
    READ_HASHES[str(path)] = digest(data)
    return json.loads(data)


def parse_arithmetic(text, expected):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    action_lines = [line for line in lines if line.startswith('ACT:')]
    matches = [re.fullmatch(r'ACT:\s*([+-]?\d+)', line) for line in action_lines]
    valid = len(matches) == 1 and matches[0] is not None
    action = int(matches[0].group(1)) if valid else None
    prediction = re.fullmatch(r'PREDICT:\s*([+-]?\d+)', lines[0]) if lines else None
    ordered = bool(len(lines) == 2 and prediction and
                   re.fullmatch(r'ACT:\s*([+-]?\d+)', lines[1]) and valid)
    return {
        'action_valid': valid,
        'action': action,
        'correct_action': valid and action == expected,
        'predict_before_act': ordered,
        'prediction': int(prediction.group(1)) if prediction else None,
        'strict_two_line_protocol': ordered,
    }


def parse_color(text):
    answer = text.strip()
    return answer if answer in COLORS else None


def parser_self_tests():
    fixtures = [
        ('PREDICT: 24\nACT: 24', 24, True, True, True),
        ('ACT: 24', 24, True, True, False),
        ('ACT: 24\nPREDICT: 24', 24, True, True, False),
        ('PREDICT: 24\nACT: 23', 24, True, False, True),
        ('PREDICT: 1\nACT: 24', 24, True, True, True),
        ('ACT: 24\nACT: 24', 24, False, False, False),
        ('ACT: 24.0', 24, False, False, False),
        ('REACT: 24', 24, False, False, False),
        ('yellow: 12\nyellow: 12\nyellow', 24, False, False, False),
        ('yellow\nyellow\nyellow\nyellow\nyellow', 24, False, False, False),
        ('PREDICT: -2\nACT: -2', -2, True, True, True),
    ]
    for text, expected, valid, correct, adherence in fixtures:
        parsed = parse_arithmetic(text, expected)
        require((parsed['action_valid'], parsed['correct_action'], parsed['predict_before_act'])
                == (valid, correct, adherence), 'Arithmetic parser fixture: ' + repr(text))
    for text, expected in [('yellow', 'yellow'), (' green\n', 'green'),
                           ('yellow yellow', None), ('blue.', None), ('ACT: 12', None)]:
        require(parse_color(text) == expected, 'Color parser fixture: ' + repr(text))
    return len(fixtures) + 5


def verify_capsule():
    validation = read_json(VALIDATION)
    archive_hash = digest(ARCHIVE.read_bytes())
    require(archive_hash == EXPECTED_CAPSULE == validation['sha256'], 'Capsule SHA256 binding')
    expected = validation['files']
    names = set()
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        for member in archive:
            name = member.name
            relative = PurePosixPath(name)
            require(not relative.is_absolute() and '..' not in relative.parts and
                    str(relative) == name, 'Safe archive name: ' + name)
            require(member.isfile() and name not in names, 'Unique regular member: ' + name)
            names.add(name)
            local = BASE / name
            require(all(not parent.is_symlink() for parent in [local, *local.parents]),
                    'No extracted symlink traversal: ' + name)
            require(local.is_file() and name in expected, 'Manifest/extracted member exists: ' + name)
            member_data = archive.extractfile(member).read()
            require(digest(member_data) == expected[name] == digest(local.read_bytes()),
                    'Tar/manifest/extracted SHA256 agree: ' + name)
    extracted = {str(path.relative_to(BASE)) for path in BASE.rglob('*') if path.is_file()}
    require(names == set(expected) == extracted and len(names) == 331, 'Exact 331-file inventory')
    return {'sha256': archive_hash, 'files_verified': len(names), 'reextracted': False,
            'validation_sha256': READ_HASHES[str(VALIDATION)]}


def fit_accounting(plan):
    prepare = read_json(PREPARE)
    require(READ_HASHES[str(PREPARE)] == plan['native_prepare_sha256'], 'Native preparation receipt pin')
    result = {}
    for arm in ARMS:
        manifest_path = ROOT / 'run' / arm / 'adapter/train_manifest.json'
        manifest = read_json(manifest_path)
        fit = read_json(ROOT / 'run' / arm / 'fit-result.json')
        meta = read_json(ROOT / 'run' / arm / 'adapter/train_meta.json')
        config = manifest['config']
        warm = manifest['warm_start']
        tokens = manifest['tokens']
        require(config == plan['config'], arm + ' actual configuration equals plan')
        require(fit['manifest_sha256'] == READ_HASHES[str(manifest_path)] ==
                fit['adapter_files']['train_manifest.json'], arm + ' fit manifest seals')
        require(manifest['corpus']['sha256'] == plan['material_files'][arm + '.json'], arm + ' corpus pin')
        require(manifest['steps'] == manifest['micro_batches'] == meta['steps'] == 320 and
                manifest['epochs_run'] == config['epochs'] == 10, arm + ' completed 320 steps/10 epochs')
        require(manifest['nonfinite_batches'] == 0 and not manifest['empty'], arm + ' finite nonempty fit')
        require(manifest['corpus']['n_items'] == manifest['corpus']['n_encoded'] == 128 and
                manifest['corpus']['n_skipped_no_target'] == 0, arm + ' all 128 records encoded')
        require(all(manifest['truncation'][key] == 0 for key in
                    ['items_truncated', 'context_tokens_dropped', 'target_tokens_dropped',
                     'items_split', 'segments_from_splits']), arm + ' no truncation/splitting')
        require(manifest['packing']['n_groups'] == 32 and manifest['packing']['n_sequences'] == 128 and
                manifest['packing']['mode'] == 'one_item_per_sequence' and
                config['batch_size'] == 4 and config['grad_accum'] == 1 and not config['pack'],
                arm + ' 32 four-sequence groups per epoch, no packing/accumulation')
        require(config['dropout'] == 0.05 and config['shuffle_groups'] and config['add_eos'] and
                not config['chat_template'], arm + ' dropout/group shuffle/EOS configuration')
        require(warm['parent_path'] == fit['parent'] == plan['parent']['parent'], arm + ' original parent path')
        require(warm['parent_files'] == warm['parent_files_after'] == fit['parent_files'] ==
                plan['parent']['parent_files'] and warm['parent_unchanged'], arm + ' parent receipt hashes unchanged')
        require(warm['source_state'] == warm['initialized_state'] == plan['parent_state'] and
                not warm['dtype_conversions'] and len(warm['source_state']) == 392,
                arm + ' 392 exact initialized/source tensor receipt entries')
        require(set(warm['final_state']) == set(warm['source_state']), arm + ' final tensor names')
        changed = sum(warm['final_state'][name]['sha256'] != entry['sha256']
                      for name, entry in warm['source_state'].items())
        require(all(warm['final_state'][name]['shape'] == entry['shape']
                    for name, entry in warm['source_state'].items()), arm + ' final tensor shapes')
        require(warm['optimizer_initial_state_entries'] == 0 and not warm['optimizer_state_restored'] and
                not warm['optimizer_state_saved'] and warm['adapter_count'] == 1 and warm['base_frozen'] and
                warm['phase_seed'] == 0 and warm['phase_steps'] == 320 and
                warm['parent_cumulative_steps'] == 80 and warm['cumulative_steps'] == 400,
                arm + ' fresh optimizer, one adapter, 80+320 cumulative receipt')
        for filename, expected in fit['adapter_files'].items():
            path = manifest_path.parent / filename
            if path.exists():
                require(digest(path.read_bytes()) == expected, arm + ' local adapter metadata: ' + filename)
        accounting = {
            'items': manifest['corpus']['n_items'], 'epochs': manifest['epochs_run'],
            'steps': manifest['steps'], 'cumulative_steps': warm['cumulative_steps'],
            'input_per_epoch': tokens['total'], 'context_per_epoch': tokens['context'],
            'target_per_epoch': tokens['target'],
            'input_presentations': tokens['total'] * manifest['epochs_run'],
            'context_presentations': tokens['context'] * manifest['epochs_run'],
            'target_presentations': tokens['target'] * manifest['epochs_run'],
            'presentations_per_source': config['batch_size'] * manifest['epochs_run'],
        }
        require(tokens['total'] == tokens['target'] + tokens['context'], arm + ' token total identity')
        require(accounting == fit['accounting'] == plan['accounting'][arm], arm + ' independently recomputed accounting')
        require(accounting['input_presentations'] == manifest['train_tokens_seen'] == meta['tokens'] ==
                prepare['token_totals'][arm]['input_tokens'], arm + ' input token receipts agree')
        require(accounting['target_presentations'] == prepare['token_totals'][arm]['target_tokens'] and
                accounting['context_presentations'] == prepare['token_totals'][arm]['context_tokens'],
                arm + ' target/context preparation receipts agree')
        result[arm] = {
            'accounting': accounting, 'native_tokens_by_view_per_epoch': tokens['target_by_view'],
            'groups_per_epoch': manifest['packing']['n_groups'],
            'source_specific_update_opportunities': manifest['epochs_run'],
            'grouping_scope': '10 opportunities assumes declared same-source four-row groups; material audit belongs to Main',
            'parent': fit['parent'], 'parent_adapter_sha256': fit['parent_files']['adapter_model.safetensors'],
            'adapter_sha256': fit['adapter_files']['adapter_model.safetensors'],
            'tensor_receipt_entries': len(warm['source_state']), 'changed_final_tensor_entries': changed,
            'train_seconds': manifest['train_seconds'], 'fit_wall_seconds': manifest['wall_seconds'],
            'final_loss_not_memory_score': manifest['final_loss'],
            'weights_reloaded': False, 'fit_receipt_verified': True,
        }
    return result


def memory_sources(plan):
    sources = {}
    for case in plan['templates']['exact']['cases']:
        source = case['source_record']
        require(source['kind'] == 'device_color' and source['color'] in COLORS, 'Valid memory source record')
        require(source['text'] == 'The log records ' + source['device'] + ' as ' + source['color'] + '.',
                'Source text/label agree: ' + source['id'])
        require(case['expected'] == source['color'] and case['source_event_ids'] == [source['id']] and
                case['device'] == source['device'], 'Case/source binding: ' + source['id'])
        require(source['id'] not in sources, 'Unique memory source: ' + source['id'])
        sources[source['id']] = source
    require(len(sources) == 16, 'Sixteen source-bound facts, not 32')
    return sources


def recount_panel(plan, fits, sources, arm, panel):
    directory = ROOT / 'run' / arm / panel
    actual = read_json(directory / 'plan.json')
    seal = read_json(directory / 'plan.sha256.json')
    require(seal['sha256'] == READ_HASHES[str(directory / 'plan.json')], arm + '/' + panel + ' plan seal')
    for key in ['cases', 'requests', 'native_inputs', 'output_token_ceiling']:
        require(actual[key] == plan['templates'][panel][key], arm + '/' + panel + ' sealed template: ' + key)
    require(actual['identity']['adapter_files']['adapter_model.safetensors'] == fits[arm]['adapter_sha256'],
            arm + '/' + panel + ' readout uses its own fitted adapter')
    data = directory / 'run/data'
    capture = read_json(data / 'manifest.json')
    for name, expected in capture['files'].items():
        require(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts,
                'Capture path safety: ' + name)
        require(digest((data / name).read_bytes()) == expected, arm + '/' + panel + ' capture hash: ' + name)
    cases = {case['id']: case for case in actual['cases']}
    native = {item['call_id']: item for item in actual['native_inputs']}
    require(len(cases) == len(actual['cases']) == len(native) == len(actual['requests']), 'Unique cases/native IDs')
    expected_ids = {request['call_id'] for request in actual['requests']}
    require(len(expected_ids) == len(actual['requests']) and
            {path.name.split('.')[0] for path in (data / 'calls').glob('*.request.json')} == expected_ids and
            {path.name.split('.')[0] for path in (data / 'calls').glob('*.response.json')} == expected_ids,
            arm + '/' + panel + ' exact raw pair coverage')
    rows = []
    for request in actual['requests']:
        call_id = request['call_id']
        incoming = read_json(data / 'calls' / (call_id + '.request.json'))
        outgoing = read_json(data / 'calls' / (call_id + '.response.json'))
        response = outgoing['response']
        require(incoming['request'] == request and incoming['identity'] == actual['identity'], 'Request and adapter identity: ' + arm + '/' + panel + '/' + call_id)
        require(incoming['prompt_sha256'] == digest((json.dumps(request['prompt']) + '\n').encode()), 'Prompt value seal: ' + call_id)
        require(outgoing['response_sha256'] == digest((json.dumps(response, sort_keys=True) + '\n').encode()),
                'Response value seal: ' + call_id)
        require(response['prompt_token_ids'] == native[call_id]['prompt_token_ids'] and
                response['rendered_prompt'] == native[call_id]['rendered_prompt'], 'Prepared prompt bytes: ' + call_id)
        require(request['seed'] == 20260912 and request['temperature'] == 0 and request['max_tokens'] == 64,
                'Deterministic cap64 request: ' + call_id)
        case = cases[request['case_id']]
        require(request['prompt'] == case['context'], 'Case prompt equals requested prompt: ' + call_id)
        duration = outgoing['ended'] - incoming['started']
        require(math.isfinite(duration) and duration >= 0, 'Nonnegative raw call duration: ' + call_id)
        row = {
            'call_id': call_id, 'case_id': case['id'], 'source_event_ids': case['source_event_ids'],
            'raw': response['text'], 'finish_reason': response['finish_reason'],
            'input_tokens': len(response['prompt_token_ids']), 'output_tokens': len(response['output_token_ids']),
            'length_finish': response['finish_reason'] == 'length',
            'reached_token_ceiling': len(response['output_token_ids']) >= request['max_tokens'],
            'request_seconds': duration,
        }
        if case['kind'] == 'addition':
            operands = re.fullmatch(r'Add ([+-]?\d+) and ([+-]?\d+)\.\nSubmit the sum using ACT: <integer>\.', request['prompt'])
            require(operands is not None, 'Recognized independently parsed arithmetic prompt')
            expected = sum(int(value) for value in operands.groups())
            require(expected == case['expected'], 'Recomputed sum equals sealed expectation: ' + call_id)
            row.update(kind='addition', expected=expected, operands=[int(value) for value in operands.groups()])
            row.update(parse_arithmetic(response['text'], expected))
        else:
            require(case['kind'] in {'memory', 'memory_recall'} and len(case['source_event_ids']) == 1,
                    'Memory case schema')
            source = sources[case['source_event_ids'][0]]
            require(case['expected'] == source['color'] and case['device'] == source['device'] and
                    source['device'] in request['prompt'], 'Memory dev/exact source binding: ' + call_id)
            color = parse_color(response['text'])
            row.update(kind='memory', expected=source['color'], device=source['device'],
                       color=color, valid_color=color is not None, correct=color == source['color'])
        rows.append(row)
    memory = [row for row in rows if row['kind'] == 'memory']
    arithmetic = [row for row in rows if row['kind'] == 'addition']
    require(len(memory) == 16 and len(arithmetic) == (32 if panel == 'dev' else 0), 'Panel denominators')
    return {
        'rows': rows, 'calls': len(rows),
        'memory': {'correct': sum(row['correct'] for row in memory), 'total': len(memory),
                   'invalid': sum(not row['valid_color'] for row in memory),
                   'colors': dict(Counter(row['color'] for row in memory)),
                   'correct_devices': [row['device'] for row in memory if row['correct']],
                   'failed_devices': [row['device'] for row in memory if not row['correct']]},
        'arithmetic': {'total': len(arithmetic), 'correct_act': sum(row['correct_action'] for row in arithmetic),
                       'valid_act': sum(row['action_valid'] for row in arithmetic),
                       'habit': sum(row['predict_before_act'] for row in arithmetic),
                       'failed_cases': [row['case_id'] for row in arithmetic if not row['correct_action']],
                       'raw_histogram': dict(Counter(row['raw'] for row in arithmetic))},
        'finish_reasons': dict(Counter(row['finish_reason'] for row in rows)),
        'length_capped_calls': sum(row['length_finish'] for row in rows),
        'calls_at_token_ceiling': sum(row['reached_token_ceiling'] for row in rows),
        'input_tokens': sum(row['input_tokens'] for row in rows),
        'output_tokens': sum(row['output_tokens'] for row in rows),
        'output_token_ceiling': sum(request['max_tokens'] for request in actual['requests']),
        'request_seconds': sum(row['request_seconds'] for row in rows),
    }


def timing(plan):
    validation = read_json(VALIDATION)
    terminal = read_json(ROOT / 'run/terminal.json')
    launch = read_json(ROOT / 'launch/launch.json')
    release = read_json(ROOT / 'run/main_release.json')
    reservation = read_json(ROOT / 'run/reservation.json')
    require(all(value['plan_sha256'] == READ_HASHES[str(ROOT / 'plan.json')]
                for value in [terminal, launch, release, reservation]), 'Controller/launch/release plan bindings')
    require(terminal['status'] == release['terminal_status'] == 'COMPLETE' and terminal['error'] is None and
            terminal['release_verified'] and release['full_release'] and release['controller_absent'] and
            terminal['worker_accounting_complete'] and set(terminal['captured']) == set(ARMS), 'Historical terminal completion')
    require(release['terminal_sha256'] == READ_HASHES[str(ROOT / 'run/terminal.json')] and
            release['launch_sha256'] == READ_HASHES[str(ROOT / 'launch/launch.json')], 'Release custody bindings')
    release_xml = (ROOT / 'run/main_release.xml').read_bytes()
    require(digest(release_xml) == release['xml_sha256'], 'Release XML hash')
    xml = ET.fromstring(release_xml)
    matching = [gpu for gpu in xml.findall('gpu') if gpu.findtext('uuid') == release['gpu']['gpu_uuid']]
    require(len(matching) == 1 and not matching[0].findall('processes/process_info') and
            release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid'], 'Historical UUID-bound empty GPU process list')
    windows = []
    for arm in plan['arm_order']:
        for phase, relative in [('fit', 'fit-worker'), ('dev', 'dev/run/worker'), ('exact', 'exact/run/worker')]:
            directory = ROOT / 'run' / arm / relative
            supervision = read_json(directory / 'supervision.json')
            process = read_json(directory / 'process.json')
            require(supervision['ok'] and supervision['returncode'] == 0 and supervision['error'] is None and
                    supervision['owned_group_empty'] and supervision['gpu_processes_absent'] and
                    supervision['reservation_release_verified'], arm + '/' + phase + ' successful worker release receipt')
            windows.append({'arm': arm, 'phase': phase, 'started_monotonic': process['started'],
                            'seconds': supervision['reserved_seconds']})
    require(all(previous['started_monotonic'] + previous['seconds'] <= following['started_monotonic'] + 0.01
                for previous, following in zip(windows, windows[1:])), 'Sequential fit/dev/exact worker windows')
    worker = sum(window['seconds'] for window in windows)
    controller_wall = terminal['ended'] - terminal['started']
    controller = terminal['reserved_seconds']
    full = (datetime.fromisoformat(release['release_utc']) - datetime.fromisoformat(launch['started_utc'])).total_seconds()
    require(abs(worker - terminal['worker_reserved_seconds']) < 1e-6 and
            abs(controller_wall - controller) < 1e-3 and
            abs(full - release['timing']['full_reservation_seconds']) < 1e-5, 'Independent nested timing arithmetic')
    require(worker <= controller <= full and controller <= plan['pair_seconds'] and
            not release['timing']['late_observation'] and not release['timing']['budget_extended'],
            'Nested scopes and declared timing bounds')
    collector_observation = validation['completion_observation']['full_reservation_seconds']
    require(collector_observation >= full and not validation['completion_observation']['late_observation'] and
            not validation['completion_observation']['budget_extended'], 'Later collector observation remains within bounds')
    return {'workers': windows, 'worker_seconds': worker, 'controller_seconds': controller,
            'controller_wall_timestamp_seconds': controller_wall,
            'controller_clock_difference_seconds': controller_wall - controller,
            'full_reservation_seconds': full, 'full_a40_minutes': full / 60,
            'later_collector_observation_seconds': collector_observation,
            'later_collector_observation_a40_minutes': collector_observation / 60,
            'collector_observation_minus_release_seconds': collector_observation - full,
            'launch_utc': launch['started_utc'],
            'terminal_utc': datetime.fromtimestamp(terminal['ended'], timezone.utc).isoformat(),
            'release_utc': release['release_utc'], 'gpu_uuid': release['gpu']['gpu_uuid'],
            'source_receipt_identity': launch['source'], 'monetary_cost': None,
            'scope': 'Historical nested reservation receipts, not additive/billed/busy-time or live observation'}


def run():
    require(not OUTPUT.exists(), 'NEW output must not already exist')
    fixture_count = parser_self_tests()
    custody = verify_capsule()
    plan = read_json(ROOT / 'plan.json')
    require(read_json(ROOT / 'plan.sha256.json')['sha256'] == READ_HASHES[str(ROOT / 'plan.json')], 'Master plan seal')
    require(set(plan['arm_order']) == set(ARMS) and len(plan['arm_order']) == 2 and plan['total_calls'] == 128 and
            plan['new_off_calls'] == plan['new_hf_calls'] == plan['confirmation_calls'] == 0,
            'Two registered arms, 128 calls, no new OFF/HF/confirmation')
    fits = fit_accounting(plan)
    sources = memory_sources(plan)
    panels = {arm: {panel: recount_panel(plan, fits, sources, arm, panel)
                    for panel in ('dev', 'exact')} for arm in ARMS}
    cross_panel = {}
    for arm in ARMS:
        dev = {row['device']: row for row in panels[arm]['dev']['rows'] if row['kind'] == 'memory'}
        exact = {row['device']: row for row in panels[arm]['exact']['rows']}
        require(set(dev) == set(exact) == {source['device'] for source in sources.values()}, arm + ' identical fact identities')
        cross_panel[arm] = {
            'answer_disagreements': [device for device in dev if dev[device]['raw'] != exact[device]['raw']],
            'correct_both': [device for device in dev if dev[device]['correct'] and exact[device]['correct']],
            'wrong_both': [device for device in dev if not dev[device]['correct'] and not exact[device]['correct']],
        }
    time_result = timing(plan)
    gate = plan['progression']
    require(gate['qualifying_arm'] == 'FOUR_VIEW' and gate['single_scores_irrelevant'] and
            not gate['automatic_progression'] and not gate['gate_evaluated_by_wrapper'] and
            gate['decide_only_after_both_technical_complete'], 'Registered conjunctive FOUR_VIEW-only gate')
    observed = {'dev_memory': panels['FOUR_VIEW']['dev']['memory']['correct'],
                'exact_memory': panels['FOUR_VIEW']['exact']['memory']['correct'],
                'dev_habit': panels['FOUR_VIEW']['dev']['arithmetic']['habit'],
                'dev_act': panels['FOUR_VIEW']['dev']['arithmetic']['correct_act']}
    decisions = {key: {'observed': value, 'minimum': gate[key + '_min'], 'pass': value >= gate[key + '_min']}
                 for key, value in observed.items()}
    gate_pass = all(value['pass'] for value in decisions.values())
    all_panels = [panel for arm in panels.values() for panel in arm.values()]
    totals = {key: sum(panel[key] for panel in all_panels) for key in
              ['calls', 'length_capped_calls', 'calls_at_token_ceiling', 'input_tokens',
               'output_tokens', 'output_token_ceiling', 'request_seconds']}
    result = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'independence': 'Reviewer did not author runner/corpus. Raw text independently parsed; no stored reductions used for scoring.',
        'scope': '128 new calls; original-parent fit/native receipts; Main separately owns full parent/material audit.',
        'capsule': custody, 'plan_sha256': READ_HASHES[str(ROOT / 'plan.json')],
        'parser': {'self_test_fixtures': fixture_count,
                   'act_grammar': 'Exactly one standalone ACT: signed-integer line; duplicates/malformed ACT lines invalid.',
                   'habit_grammar': 'Exactly two nonempty lines: PREDICT: signed integer followed by ACT: signed integer; no prediction-correctness requirement.',
                   'memory_grammar': 'Whole stripped output must equal one lower-case color.',
                   'labels': 'Addition recomputed from prompt operands; memory from sealed exact-plan source_record, cross-checked against both panels; original material audit not repeated.'},
        'fits': fits, 'panels': panels, 'cross_panel': cross_panel, 'totals': totals,
        'progression': {'requirements': decisions, 'both_technical_complete': True, 'pass': gate_pass,
                        'eligible_next_seeds_after_gate': gate['eligible_next_seeds'] if gate_pass else [],
                        'scope': 'Independent gate evaluation, not a live launch-state check'},
        'timing': time_result, 'new_fits': 2, 'new_updates': sum(fit['accounting']['steps'] for fit in fits.values()),
        'new_off_calls': 0, 'new_hf_calls': 0, 'confirmation_calls': 0,
        'limitations': ['No tokenizer/model/native execution or independent measurement of actual tensor contents/freezing.',
                        'Full parent provenance/material semantics/group identities remain Main audit scope.',
                        'Native token totals are receipt recomputations, not retokenization.',
                        'Grouped four views/copies average within one update, dropout active; not 40 temporally separated updates/source.',
                        'Unequal input/context compute; prior SEQ107 changes batch/dose and is descriptive only.',
                        'No operational child SLEEP, H1/H2/G3, reliable coexistence, latent arithmetic erasure or authenticated origin claim.'],
        'technical_raw_review': 'PASS', 'checks_passed': len(CHECKS), 'checks': CHECKS,
        'read_artifact_sha256': READ_HASHES,
        'script_sha256': digest(Path(__file__).read_bytes()),
    }
    require(digest(ARCHIVE.read_bytes()) == EXPECTED_CAPSULE, 'Capsule unchanged at output seal')
    for name, expected in READ_HASHES.items():
        require(digest(Path(name).read_bytes()) == expected, 'Read artifact unchanged at output seal: ' + name)
    result['checks_passed'] = len(CHECKS)
    with OUTPUT.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'output': str(OUTPUT), 'sha256': digest(OUTPUT.read_bytes()),
                      'technical_raw_review': result['technical_raw_review'], 'progression': result['progression'],
                      'totals': totals, 'timing': time_result, 'checks_passed': len(CHECKS)}, indent=2))


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--self-test', action='store_true')
    options = arguments.parse_args()
    if options.self_test:
        print(json.dumps({'parser_fixtures_passed': parser_self_tests()}))
    else:
        run()
