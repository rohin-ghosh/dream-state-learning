import copy
import hashlib
import json
import random
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


BASE = Path('/tmp')
STEM = 'astra_interleaved_memory_independent_review_20260912'
ARCHIVE = BASE / 'astra_interleaved_memory_root0_terminal_20260912.tgz'
EXPECTED = '9aa7fb67b3f68afa3d4520e1f4b7cfcc41322367ef1cf6ee83396a7c60cdbf64'
PREFIX = 'fits_root0_attempt1/'
ORIGINAL = BASE / 'astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1'
ARMS = ('SINGLE_VIEW', 'FOUR_VIEW')
MEMORY_TEMPLATES = (
    'Which color does the log assign to {device}?',
    'What is the color assigned to {device} in the log?',
    'According to the log, which color is assigned to {device}?',
    'Name the color that the log assigns to {device}.',
)
CUES = (
    'Look up {device} in the log and give its color.',
    'Consult the log: {device} has which color?',
    'In the log entry for {device}, what color is listed?',
)
COLORS = {'blue', 'green', 'red', 'yellow'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, ('duplicate JSON key', key)
        result[key] = value
    return result


def decoded(payload):
    return json.loads(payload, object_pairs_hook=unique)


def memory_score(text, expected):
    answer = text.strip().lower()
    if answer.endswith('.'):
        answer = answer[:-1]
    valid = answer in COLORS
    return dict(normalized=answer, answer=answer if valid else None, valid=valid,
                correct=valid and answer == expected)


def arithmetic_score(text, expected):
    matches = {}
    for label in ('ACT', 'PREDICT'):
        values = []
        for index, line in enumerate(text.splitlines()):
            if re.match(r'^[ \t]*' + label + r'\b', line):
                match = re.fullmatch(r'[ \t]*' + label + r':[ \t]*([+-]?[0-9]+)[ \t]*', line)
                values.append((index, int(match[1]) if match else None))
        matches[label] = values
    acts, predicts = matches['ACT'], matches['PREDICT']
    action_valid = len(acts) == 1 and acts[0][1] is not None
    prediction_valid = len(predicts) == 1 and predicts[0][1] is not None
    first_act = acts[0][1] if acts else None
    first_predict = predicts[0][1] if predicts else None
    before = bool(action_valid and prediction_valid and predicts[0][0] < acts[0][0])
    correct = action_valid and first_act == expected
    return dict(act_count=len(acts), predict_count=len(predicts), first_act=first_act,
                first_predict=first_predict, action_valid=action_valid, prediction_valid=prediction_valid,
                correct_action=correct, predict_before_act=before,
                adherence=bool(correct and before and first_predict == expected))


def main():
    assert memory_score(' Red. \n', 'red')['correct']
    assert not memory_score('red red', 'red')['valid']
    assert arithmetic_score('PREDICT: 3\nACT: 3', 3)['adherence']
    assert not arithmetic_score('ACT: 3\nPREDICT: 3', 3)['adherence']
    assert not arithmetic_score('PREDICT: 3\nACT: 3\nACT: 3', 3)['action_valid']
    validation_path = BASE / 'astra_interleaved_memory_validation_20260912.json'
    validation = decoded(validation_path.read_bytes())
    assert digest(ARCHIVE.read_bytes()) == EXPECTED == validation['sha256']
    files = {}
    with tarfile.open(ARCHIVE) as archive:
        members = archive.getmembers()
        assert len(members) == len(validation['files']) == 548
        assert sum(member.size for member in members) < 64 * 1024 * 1024
        for member in members:
            parts = member.name.split('/')
            assert member.isfile() and member.name not in files
            assert not member.name.startswith('/') and not any(part in ('', '.', '..') for part in parts)
            assert '\\' not in member.name and member.name.startswith(PREFIX)
            assert PurePosixPath(member.name).suffix not in validation['excluded_suffixes']
            payload = archive.extractfile(member).read()
            assert digest(payload) == validation['files'][member.name]
            files[member.name] = payload
    assert set(files) == set(validation['files'])

    def read(name):
        return decoded(files[PREFIX + name])

    def filehash(name):
        return digest(files[PREFIX + name])

    plan = read('plan.json')
    assert filehash('plan.json') == read('plan.sha256.json')['sha256'] == validation['plan_sha256']
    assert plan['seed'] == 0 and plan['device'] == '1' and plan['arm_order'] == list(ARMS)
    assert plan['panels'] == {'dev': 48, 'exact': 16, 'lexical': 48} and plan['total_calls'] == 224
    assert plan['confirmation_calls'] == 0 and not plan['outcome_selective_skips']
    assert plan['reduce_only_after_both_captures']
    provenance_checks = {}
    for path, expected in plan['parent']['provenance'].items():
        relative = path.split('astra_fundamental_teaching_20260912_attempt1/')[1]
        local = ORIGINAL / relative
        assert digest(local.read_bytes()) == expected
        provenance_checks[relative] = expected
    original_plan = decoded((ORIGINAL / 'plan.json').read_bytes())
    original_teach_bytes = (ORIGINAL / 'teach.json').read_bytes()
    assert digest(original_teach_bytes) == '2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c'
    originals = decoded(original_teach_bytes)['corpus']
    original_rows = decoded((ORIGINAL / 'candidate/train_teach.json').read_bytes())
    assert digest(encoded(original_rows)) == 'd44585d4081819248f18774f12d8e1260e61af6fa6aaa260afbe3833e10838ab'
    assert len(originals) == len(original_rows) == 80
    chat_prefix, chat_suffix = originals[0]['spans'][0][0].split(original_rows[0]['context'])
    memory_rows = [row for row in original_rows if row['kind'] == 'memory']
    addition_rows = [row for row in original_rows if row['kind'] == 'addition'][:16]
    assert len(memory_rows) == len(addition_rows) == 16
    lookup = {row['case_id']: (index, row) for index, row in enumerate(original_rows)}
    colors = {row['device']: row['response'] for row in memory_rows}
    source_reconstruction = {}
    native_original_rows = {row['case_id']: row for row in original_plan['row_audits']['teach']}
    result = dict(capsule_sha256=EXPECTED, validation_sha256=digest(validation_path.read_bytes()),
                  metadata_files_verified=len(files), archive_safety='PASS: exact unique regular-file inventory, safe relative paths, no links or excluded weights; read in memory',
                  plan_sha256=filehash('plan.json'), source_commit=plan['source_commit'],
                  provenance_files_verified=provenance_checks, arms={}, contradiction_flags=[],
                  authorship='Independent raw reduction, not fresh-author audit: authored older related replay code. No Main outcomes supplied; some sealed reductions were visible during schema inspection. No existing scorer/builder imported or executed.')
    for arm in ARMS:
        reconstructed = []
        group_members = {}
        for copy_index in range(4):
            for block in range(8):
                group = f'interleaved-r{copy_index}-b{block:02d}'
                members = [memory_rows[2 * block], addition_rows[(2 * block + 2 * copy_index) % 16],
                           memory_rows[2 * block + 1], addition_rows[(2 * block + 2 * copy_index + 1) % 16]]
                group_members[group] = [row['case_id'] for row in members]
                for slot, source in enumerate(members):
                    index, original_row = lookup[source['case_id']]
                    item = copy.deepcopy(originals[index])
                    assert item['spans'][1][0] == source['response'] and item['spans'][1][1] is True
                    assert item['spans'][0][1] is False and item['meta']['source_event_ids'] == source['source_event_ids']
                    context = source['context']
                    if arm == 'FOUR_VIEW' and source['kind'] == 'memory':
                        context = MEMORY_TEMPLATES[copy_index].format(device=source['device'])
                    item['spans'][0][0] = item['spans'][0][0].replace(source['context'], context)
                    item.update(group=group, order=slot)
                    item['meta']['interleaved_replay'] = dict(
                        id=f"{source['case_id']}-copy-{copy_index}", case_id=source['case_id'],
                        source_record_id=source['id'], source_row_index=index,
                        source_row_sha256=digest(encoded(original_row)), copy_index=copy_index,
                        batch_group=group, batch_slot=slot)
                    reconstructed.append(item)
        material_sha = digest(encoded({'corpus': reconstructed}))
        assert material_sha == plan['material_files'][arm + '.json'], ('material reconstruction', arm)
        schedules, presentations = [], Counter()
        for epoch in range(10):
            groups = sorted(group_members)
            random.Random(epoch).shuffle(groups)
            source_steps = defaultdict(set)
            for step, group in enumerate(groups):
                ids = group_members[group]
                assert len(set(ids)) == 4
                for case_id in ids:
                    source_steps[case_id].add(step)
                    presentations[case_id] += 1
                target_mass = {kind: sum(native_original_rows[key]['target_tokens'] for key in ids
                    if lookup[key][1]['kind'] == kind) for kind in ('memory', 'addition')}
                assert target_mass['memory'] == 4
                schedules.append(dict(epoch=epoch, step=step, group=group, sources=ids, target_tokens_by_kind=target_mass))
            assert set(map(len, source_steps.values())) == {4}
        assert len(schedules) == 320 and set(presentations.values()) == {40}
        native_cost = plan['native_cpu_audit']['padded_costs']['0'][arm]
        assert dict(presentations) == native_cost['source_presentations']
        source_reconstruction[arm] = dict(material_sha256=material_sha, schedules=schedules,
                                        padded_slots_native_receipt=native_cost['padded_input_slots'])
        denoms = Counter(sum(row['target_tokens_by_kind'].values()) for row in schedules)
        assert denoms == {32: 200, 30: 120}
        source_reconstruction[arm]['target_denominator_distribution'] = dict(denoms)
        assert sum(sum(row['target_tokens_by_kind'].values()) for row in schedules) == 10000
        if arm == 'SINGLE_VIEW':
            padded = sum(4 * max(native_original_rows[key]['input_tokens'] for key in row['sources']) for row in schedules)
            assert padded == native_cost['padded_input_slots'] == 76960
            source_reconstruction[arm]['padded_slots_recomputed_from_original_native_lengths'] = padded
        stage = 'run/' + arm + '/'
        fit = read(stage + 'fit-result.json')
        manifest = read(stage + 'adapter/train_manifest.json')
        warm = manifest['warm_start']
        assert filehash(stage + 'adapter/train_manifest.json') == fit['manifest_sha256']
        assert manifest['corpus']['sha256'] == material_sha
        assert manifest['steps'] == manifest['micro_batches'] == 320 and manifest['epochs_run'] == 10
        assert manifest['nonfinite_batches'] == 0 and not manifest['empty']
        assert manifest['config']['seed'] == 0 and manifest['config']['batch_size'] == 4
        assert manifest['config']['lr'] == .0003 and manifest['config']['grad_accum'] == 1
        assert manifest['config']['rank'] == 8 and not manifest['config']['pack'] and manifest['config']['add_eos']
        assert warm['parent_path'] == fit['parent'] == plan['parent']['parent']
        assert warm['parent_files'] == warm['parent_files_after'] == fit['parent_files'] == plan['parent']['parent_files']
        assert warm['source_state'] == warm['initialized_state'] == plan['parent_state'] and not warm['dtype_conversions']
        assert warm['initialized_loaded_state_check'] and warm['parent_unchanged'] and warm['base_frozen']
        assert warm['adapter_count'] == 1 and warm['phase_seed'] == 0
        assert warm['parent_cumulative_steps'] == 80 and warm['cumulative_steps'] == 400
        assert warm['optimizer_initial_state_entries'] == 0 and not warm['optimizer_state_restored']
        assert warm['optimizer_initialization'] == 'fresh_per_write'
        assert all(manifest['truncation'][key] == 0 for key in ('items_truncated', 'context_tokens_dropped', 'target_tokens_dropped', 'items_split'))
        assert manifest['packing']['n_groups'] == 32 and manifest['packing']['n_sequences'] == 128
        assert len(warm['source_state']) == len(warm['final_state']) == 392
        changed = sum(warm['source_state'][key]['sha256'] != value['sha256'] for key, value in warm['final_state'].items())
        assert changed > 0
        for name, expected in fit['adapter_files'].items():
            if PREFIX + stage + 'adapter/' + name in files:
                assert filehash(stage + 'adapter/' + name) == expected
        accounting = plan['accounting'][arm]
        assert fit['accounting'] == accounting
        assert manifest['train_tokens_seen'] == manifest['tokens']['total'] * 10 == accounting['input_presentations']
        assert manifest['tokens']['target'] * 10 == accounting['target_presentations'] == 10000
        assert manifest['tokens']['target_by_view'] == {'memory': 128, 'addition': 872}
        arm_result = dict(fit=dict(accounting=accounting, tokens=manifest['tokens'],
                                  padded_slots_native_receipt=native_cost['padded_input_slots'],
                                  train_seconds=manifest['train_seconds'], trainer_wall_seconds=manifest['wall_seconds'],
                                  parent_sha256=warm['parent_files']['adapter_model.safetensors'],
                                  child_sha256=fit['adapter_files']['adapter_model.safetensors'],
                                  changed_tensor_hashes=changed, initialized_equals_parent=True,
                                  fresh_optimizer=True, trainable_parameters=manifest['lora']['trainable_params']), panels={})
        for panel, count in plan['panels'].items():
            panelroot = stage + panel + '/'
            panelplan = read(panelroot + 'plan.json')
            assert filehash(panelroot + 'plan.json') == read(panelroot + 'plan.sha256.json')['sha256']
            assert panelplan['model_files'] == plan['model_files']
            assert panelplan['adapter_files'] == fit['adapter_files'] and panelplan['adapter'] == fit['adapter']
            assert panelplan['device'] == '1' and panelplan['model'] == plan['model']
            for key in ('cases', 'requests', 'native_inputs', 'source_hashes'):
                assert panelplan[key] == plan['templates'][panel][key]
            data = panelroot + 'run/data/'
            capture = read(data + 'manifest.json')
            for name, expected in capture['files'].items():
                assert filehash(data + name) == expected
            identity = read(data + 'identity.json')
            assert identity == dict(backend=panelplan['identity'], model_files=plan['model_files'], adapter_files=fit['adapter_files'])
            assert read(data + 'backend.cleanup.json')['closed']
            process = read(panelroot + 'run/worker/process.json')
            supervision = read(panelroot + 'run/worker/supervision.json')
            ready = read(data + 'backend.ready.json')
            assert ready['pid'] == process['pid'] and ready['ready'] >= process['started']
            previous = ready['ready']
            rows = []
            assert len(panelplan['requests']) == len(panelplan['cases']) == len(panelplan['native_inputs']) == count
            request_names = [name for name in files if name.startswith(PREFIX + data + 'calls/') and name.endswith('.request.json')]
            assert len(request_names) == count
            for request, case, native in zip(panelplan['requests'], panelplan['cases'], panelplan['native_inputs']):
                sent = read(data + 'calls/' + request['call_id'] + '.request.json')
                received = read(data + 'calls/' + request['call_id'] + '.response.json')
                response = received['response']
                assert sent['request'] == request and sent['identity'] == panelplan['identity']
                assert sent['prompt_sha256'] == digest(encoded(request['prompt']))
                assert received['response_sha256'] == digest((json.dumps(response, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode())
                assert previous <= sent['started'] <= received['ended'] <= process['started'] + supervision['reserved_seconds']
                previous = received['ended']
                assert response['prompt_token_ids'] == native['prompt_token_ids'] and response['rendered_prompt'] == native['rendered_prompt']
                assert request['case_id'] == case['id'] and request['prompt'] == case['context']
                assert response['rendered_prompt'] == chat_prefix + case['context'] + chat_suffix
                assert request['temperature'] == 0 and request['seed'] == 20260912 and request['max_tokens'] == 64
                if case['kind'] == 'addition':
                    match = re.fullmatch(r'Add (\d+) and (\d+)\.\nSubmit the sum using ACT: <integer>\.', case['context'])
                    assert match
                    expected = int(match[1]) + int(match[2])
                    scoring = arithmetic_score(response['text'], expected)
                else:
                    expected = colors[case['device']]
                    assert re.findall(r'device-\d{3}', request['prompt']) == [case['device']]
                    assert not re.search(r'\b(?:blue|green|red|yellow|unknown)\b', request['prompt'], re.I)
                    scoring = memory_score(response['text'], expected)
                assert expected == case['expected']
                row = dict(case_id=case['id'], kind=case['kind'], expected=expected, raw_text=response['text'],
                           device=case.get('device'), family=case.get('family'), prompt=request['prompt'],
                           input_tokens=len(response['prompt_token_ids']), output_tokens=len(response['output_token_ids']),
                           seconds=received['ended'] - sent['started'], finish_reason=response['finish_reason'],
                           hit_token_cap=len(response['output_token_ids']) >= request['max_tokens'],
                           output_token_ids_sha256=digest(encoded(response['output_token_ids'])), **scoring)
                rows.append(row)
            arithmetic = [row for row in rows if row['kind'] == 'addition']
            memories = [row for row in rows if row['kind'] != 'addition']
            memory_counts = dict(total=len(memories), correct=sum(row['correct'] for row in memories), invalid=sum(not row['valid'] for row in memories))
            if panel == 'dev':
                counts = dict(total=count, memory=memory_counts, addition=dict(total=32,
                    adherence=sum(row['adherence'] for row in arithmetic), correct_action=sum(row['correct_action'] for row in arithmetic),
                    invalid_action=sum(not row['action_valid'] for row in arithmetic)))
            elif panel == 'exact':
                counts = dict(memory_counts, answer_counts=dict(Counter(row['answer'] if row['valid'] else '<invalid>' for row in memories)))
            else:
                families = {str(family): dict(total=16, correct=sum(row['correct'] for row in rows if row['family'] == family),
                    invalid=sum(not row['valid'] for row in rows if row['family'] == family)) for family in range(3)}
                assert Counter(row['family'] for row in rows) == {0: 16, 1: 16, 2: 16}
                counts = dict(memory_counts, by_family=families)
            reduction = read(panelroot + 'reduction.json')
            if counts != reduction['counts']:
                result['contradiction_flags'].append(dict(arm=arm, panel=panel, reason='stored counts differ', computed=counts, stored=reduction['counts']))
            indexed = {row['case_id']: row for row in reduction['rows']}
            assert len(indexed) == count
            for row in rows:
                for key, value in indexed[row['case_id']].items():
                    if key in row and row[key] != value:
                        result['contradiction_flags'].append(dict(arm=arm, panel=panel, case_id=row['case_id'], key=key, computed=row[key], stored=value))
            assert reduction['complete'] and reduction['native_token_text_audit']
            assert reduction['plan_sha256'] == filehash(panelroot + 'plan.json')
            assert reduction['capture_sha256'] == filehash(data + 'manifest.json')
            assert validation['audits'][arm][panel]['reduction_sha256'] == filehash(panelroot + 'reduction.json')
            usage_all = read(data + 'usage.json')
            assert len(usage_all) == 1
            usage = next(iter(usage_all.values()))
            costs = dict(requests=count, native_input_tokens=sum(row['input_tokens'] for row in rows),
                         native_output_tokens=sum(row['output_tokens'] for row in rows),
                         generation_seconds=sum(row['seconds'] for row in rows), output_token_ceiling=count * 64)
            for key, value in costs.items():
                assert abs(value - usage[key]) < 1e-7
            arm_result['panels'][panel] = dict(counts=counts, rows=rows, costs=costs,
                cap_hits=sum(row['hit_token_cap'] for row in rows), finish_reasons=dict(Counter(row['finish_reason'] for row in rows)),
                worker_seconds=supervision['reserved_seconds'], startup_seconds=ready['ready']-process['started'])
        result['arms'][arm] = arm_result
    assert source_reconstruction[ARMS[0]]['schedules'] == source_reconstruction[ARMS[1]]['schedules']
    result['source_reconstruction'] = source_reconstruction
    result['paired_raw_comparison'] = {}
    for panel in plan['panels']:
        single = result['arms']['SINGLE_VIEW']['panels'][panel]['rows']
        four = result['arms']['FOUR_VIEW']['panels'][panel]['rows']
        assert [row['case_id'] for row in single] == [row['case_id'] for row in four]
        result['paired_raw_comparison'][panel] = dict(total=len(single),
            identical_texts=sum(left['raw_text'] == right['raw_text'] for left, right in zip(single, four)),
            identical_token_sequences=sum(left['output_token_ids_sha256'] == right['output_token_ids_sha256'] for left, right in zip(single, four)))
    all_contexts = [row['context'] for row in original_rows]
    for filename in ('train_control.json', 'eval.json'):
        all_contexts.extend(row['context'] for row in decoded((ORIGINAL / 'candidate' / filename).read_bytes()))
    all_contexts.extend(template.format(device=device) for template in MEMORY_TEMPLATES for device in colors)
    normalized = lambda text: ' '.join(re.findall(r'\w+', text.casefold()))
    excluded = {normalized(context) for context in all_contexts}
    cues = plan['templates']['lexical']['cases']
    assert len({normalized(row['context']) for row in cues}) == 48
    for row in cues:
        assert row['context'] == CUES[row['family']].format(device=row['device'])
        assert normalized(row['context']) not in excluded
    result['lexical_exclusion_check'] = '48 unique normalized cues, disjoint from original train/control/eval and all four training templates; same16 facts'
    workers, worker_seconds = [], 0.0
    for name in files:
        if name.endswith('/supervision.json'):
            supervision = decoded(files[name])
            process = decoded(files[name.replace('supervision.json', 'process.json')])
            assert all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
            assert supervision['returncode'] == 0 and supervision['error'] is None and supervision['device'] == '1'
            assert process['device'] == '1' and process['pgid'] == process['pid'] and 0 < process['timeout'] <= 600
            worker_seconds += supervision['reserved_seconds']
            workers.append(dict(path=name, process=process, supervision=supervision))
    assert len(workers) == len({item['process']['pid'] for item in workers}) == 8
    workers.sort(key=lambda item: item['process']['started'])
    for before, after in zip(workers, workers[1:]):
        assert before['process']['started'] + before['supervision']['reserved_seconds'] <= after['process']['started']
    terminal = read('run/terminal.json')
    release = read('run/main_release.json')
    launch = read('launch/launch.json')
    assert terminal['status'] == 'COMPLETE' and terminal['error'] is None
    assert terminal['continuous_reservation'] and terminal['deadline_met'] and terminal['release_verified']
    assert not terminal['gate_evaluated'] and not terminal['automatic_progression'] and not terminal['budget_extended']
    assert release['full_release'] and release['controller_absent']
    assert release['plan_sha256'] == filehash('plan.json') and release['terminal_sha256'] == filehash('run/terminal.json')
    assert release['launch_sha256'] == filehash('launch/launch.json') and release['xml_sha256'] == filehash('run/main_release.xml')
    assert release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid']
    assert release['device'] == launch['device'] == plan['device']
    assert release['controller_pid'] == launch['pid'] == terminal['controller_pid']
    assert launch['script_sha256'] == plan['source_hashes']['interleaved_pair']
    assert launch['reservation_sha256'] == filehash('run/reservation.json')
    assert launch['plan_sha256'] == filehash('plan.json')
    assert launch['source'] == plan['source_root'] and plan['source_commit'] in launch['source']
    assert abs(worker_seconds - terminal['worker_reserved_seconds']) < 1e-7
    assert worker_seconds <= terminal['reserved_seconds'] <= release['observation']['full_reservation_seconds']
    assert terminal['effective_deadline'] <= terminal['started'] + plan['pair_seconds'] + .01
    watches = {}
    for part in ('start', 'terminal'):
        path = BASE / f'astra_interleaved_watch_{part}_20260912.json'
        payload = path.read_bytes()
        watches[part] = decoded(payload)
        binding = watches[part].get('contract', watches[part])
        assert binding['launch_sha256'] == filehash('launch/launch.json')
        result.setdefault('external_watch_sha256', {})[part] = digest(payload)
    assert watches['start']['watchdog_sha256'] == read('launch/watchdog_launch.json')['watchdog_sha256']
    assert watches['terminal']['success'] and not watches['terminal']['signals_attempted']
    assert watches['start']['contract']['reservation_sha256'] == filehash('run/reservation.json')
    assert watches['start']['contract']['pid'] == terminal['controller_pid']
    assert watches['start']['contract']['runner_sha256'] == launch['script_sha256']
    assert watches['start']['contract']['effective_deadline'] == terminal['effective_deadline']
    result['inherited_baseline_counts_not_recounted'] = plan['parent']['baseline_counts']
    result['watchdog'] = watches
    result['workers'] = workers
    result['costs'] = dict(worker_seconds=worker_seconds, controller_seconds=terminal['reserved_seconds'],
        full_release_seconds=release['observation']['full_reservation_seconds'],
        final_collection_observation_seconds=validation['observation']['full_reservation_seconds'],
        release_utc=release['release_utc'], release=release, bounds=dict(controller=plan['pair_seconds'], cleanup=plan['cleanup_seconds'], custody=plan['external_custody_seconds']))
    four = result['arms']['FOUR_VIEW']['panels']
    thresholds = dict(dev_memory=(four['dev']['counts']['memory']['correct'], 15),
        exact_memory=(four['exact']['counts']['correct'], 15), habit=(four['dev']['counts']['addition']['adherence'], 30),
        ACT=(four['dev']['counts']['addition']['correct_action'], 31))
    thresholds.update({f'lexical_{family}': (four['lexical']['counts']['by_family'][str(family)]['correct'], 15) for family in range(3)})
    result['thresholds'] = {key: dict(actual=value, minimum=minimum, pass_threshold=value >= minimum) for key, (value, minimum) in thresholds.items()}
    for key, minimum in [('dev_memory_min', 15), ('exact_memory_min', 15), ('dev_habit_min', 30), ('dev_act_min', 31), ('each_lexical_family_min', 15)]:
        assert plan['progression'][key] == minimum
    assert plan['progression']['qualifying_arm'] == 'FOUR_VIEW' and not plan['progression']['automatic_progression']
    result['technical_receipt_audit'] = 'PASS' if not result['contradiction_flags'] else 'CONTRADICTIONS'
    result['FOUR_prespecified_progression_criteria_met'] = not result['contradiction_flags'] and all(value >= minimum for value, minimum in thresholds.values())
    result['progression_owner'] = 'Main; eligibility only, no automatic launch'
    result['limits'] = [
        'No native tokenizer rerun or weight-byte read; stored IDs, native-mask/token audit summary and state/hash receipts checked, not an independent native recomputation.',
        'Training corpus bytes independently reconstructed to sealed hashes; source schedule independently derived, but no per-step execution trace is archived.',
        'Native audit full row masks/IDs and batch denominators are hash-bound but absent as standalone material/token_audit files in this capsule.',
        'Base origin UNRESOLVED_LOCAL_HASHES_ONLY; local equality is not origin authentication.',
        'Root0, authored toy facts, lexical cues share16 facts; no confirmation, freeze, G3/P1/H2 promotion or parenting efficacy.',
    ]
    with (BASE / (STEM + '.json')).open('w') as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
    for arm, value in result['arms'].items():
        print(arm)
        for panel, data in value['panels'].items():
            print(panel, data['counts'], 'caps', data['cap_hits'], 'costs', data['costs'])
    print('thresholds', result['thresholds'])
    print('contradictions', result['contradiction_flags'])
    print('cost', {key:value for key,value in result['costs'].items() if key != 'release'})


if __name__ == '__main__':
    main()
