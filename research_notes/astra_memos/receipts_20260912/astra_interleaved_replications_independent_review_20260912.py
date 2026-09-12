"""CPU-only prepared auditor. No results until both Main-pinned capsules pass preflight."""
import argparse
import copy
import hashlib
import json
import math
import random
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath


BASE = Path('/tmp')
STEM = 'astra_interleaved_replications_independent_review_20260912'
ROOT0_AUDITOR = BASE / 'astra_interleaved_memory_independent_review_20260912.py'
ROOT0_AUDITOR_SHA = '0b22bdfd5af3f3a36bc36c5f8da93276a28e7ee0ac7255c885ba476a203404b2'
DRIVER_SHA = 'dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f'
SOURCE = '22b7e528f6f62358981ed2264d30ee7242926160'
SEED0_PLAN_SHA = '4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388'
SEED0_REVIEW_SHA = '522633241ad3910a4d0ee1fd156d31aa3eb7756495cc5efbbe2cc3c97865f522'
PARENT_PINS = {
    1: ('f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252',
        '248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335',
        'f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a'),
    2: ('54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae',
        'fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c',
        'eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825'),
}
ARMS = ('SINGLE_VIEW', 'FOUR_VIEW')
PANELS = {'dev': 48, 'exact': 16, 'lexical': 48}
INPUTS = {'SINGLE_VIEW': 66160, 'FOUR_VIEW': 67120}
EXCLUDED = {'.bin', '.ckpt', '.pt', '.pth', '.pyc', '.pyo', '.safetensors'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key: ' + key)
        value[key] = item
    return value


def decode(payload):
    return json.loads(payload, object_pairs_hook=unique)


def canonical(value, pretty=False):
    return (json.dumps(value, sort_keys=True, indent=2 if pretty else None,
                       ensure_ascii=False, allow_nan=False) + '\n').encode()


def helpers():
    payload = ROOT0_AUDITOR.read_bytes()
    require(sha(payload) == ROOT0_AUDITOR_SHA, 'frozen root0 auditor changed')
    namespace = {'__name__': 'frozen_root0_scoring_helpers'}
    exec(compile(payload, str(ROOT0_AUDITOR), 'exec'), namespace)
    return namespace


def safe_members(archive, validation):
    members = archive.getmembers()
    require(len(members) == len(validation['files']), 'archive inventory count mismatch')
    require(sum(member.size for member in members) <= 64 * 1024 * 1024, 'metadata bound exceeded')
    files = {}
    for member in members:
        parts = member.name.split('/')
        require(member.isfile() and member.name not in files and '\\' not in member.name
                and all(part not in ('', '.', '..') for part in parts), 'unsafe/duplicate/nonregular member')
        require(PurePosixPath(member.name).suffix not in EXCLUDED, 'weight/bytecode member')
        payload = archive.extractfile(member).read()
        require(sha(payload) == validation['files'].get(member.name), 'member hash mismatch')
        files[member.name] = payload
    require(set(files) == set(validation['files']), 'archive inventory mismatch')
    prefixes = {name.split('/')[0] for name in files}
    require(len(prefixes) == 1, 'one run root required')
    prefix = next(iter(prefixes)) + '/'
    return files, prefix


def terminal_preflight(plan, terminal, release, seed):
    require(type(seed) is int and seed in PARENT_PINS, 'only seeds1/2 are predeclared')
    require(plan['schema'] == 'INTERLEAVED_MEMORY_REPLICATION_V1' and plan['seed'] == seed, 'wrong replication schema/seed')
    require(plan['source_commit'] == SOURCE and plan['source_root'].endswith('/' + SOURCE), 'wrong source')
    require(plan['source_hashes']['interleaved_replication'] == DRIVER_SHA, 'wrong replication driver')
    require(tuple(plan['parent_pin']) == PARENT_PINS[seed], 'wrong original parent pins')
    require(plan['config']['seed'] == seed and plan['native_cpu_audit']['selected_seed'] == seed, 'seed crossed between fit/schedule')
    require(plan['arm_order'] == list(ARMS) and plan['panels'] == PANELS and plan['total_calls'] == 224, 'fixed workload changed')
    require(plan['confirmation_calls'] == 0 and not plan['outcome_selective_skips']
            and plan['reduce_only_after_both_captures'], 'selection/visibility contract changed')
    require(terminal['status'] == 'COMPLETE' and terminal['error'] is None and terminal['seed'] == seed, 'not COMPLETE: no scoring')
    require(all(terminal[key] for key in ('release_verified', 'deadline_met', 'worker_accounting_complete')), 'incomplete technical receipt')
    require(not terminal['automatic_progression'] and not terminal['gate_evaluated'] and not terminal['budget_extended'], 'unexpected progression/budget')
    require(set(terminal['arms']) == set(terminal['captured']) == set(ARMS), 'both terminal arms required')
    for arm in ARMS:
        require(set(terminal['arms'][arm]['readouts']) == set(terminal['captured'][arm]['captures']) == set(PANELS), 'all panels required before scoring')
    require(release['full_release'] and release['controller_absent'], 'full release missing')
    require(release['device'] == terminal['device'] == plan['device'], 'device mismatch')


def preflight(entry, gate_sha):
    seed = entry['seed']
    archive_path, validation_path = Path(entry['capsule']), Path(entry['validation'])
    archive_bytes, validation_bytes = archive_path.read_bytes(), validation_path.read_bytes()
    require(sha(archive_bytes) == entry['capsule_sha256'], 'Main capsule pin mismatch')
    require(sha(validation_bytes) == entry['validation_sha256'], 'Main validation pin mismatch')
    validation = decode(validation_bytes)
    require(validation['sha256'] == entry['capsule_sha256'] and validation['terminal_status'] == 'COMPLETE', 'collection not complete')
    require(validation['seed'] == seed and validation['plan_sha256'] == entry['plan_sha256'], 'collection seed/plan mismatch')
    with tarfile.open(archive_path) as archive:
        files, prefix = safe_members(archive, validation)
    read = lambda name: decode(files[prefix + name])
    digest = lambda name: sha(files[prefix + name])
    plan, terminal, release = read('plan.json'), read('run/terminal.json'), read('run/main_release.json')
    require(digest('plan.json') == entry['plan_sha256'] == read('plan.sha256.json')['sha256'], 'plan seal differs')
    terminal_preflight(plan, terminal, release, seed)
    require(Path(plan['root']).name + '/' == prefix, 'run-root prefix differs')
    require(validation['original_parent_plan_sha256'] == PARENT_PINS[seed][0], 'validation parent pin differs')
    gate = plan['seed0_gate']
    require(gate['sha256'] == validation['seed0_gate_sha256'] == gate_sha, 'Main seed0 gate differs')
    require(gate['owner'] == 'Main' and gate['decision'] == 'ALLOW_SEEDS_1_2' and gate['raw_review_verdict'] == 'PASS', 'Main gate missing')
    require(SEED0_PLAN_SHA in gate['evidence_hashes'].values() and SEED0_REVIEW_SHA in gate['evidence_hashes'].values(), 'gate evidence identity differs')
    parent = Path(entry['parent_local_root'])
    for relative, expected in zip(('plan.json', 'fit_teach/verified.json', 'readouts/teach/plan.json'), PARENT_PINS[seed]):
        require(sha((parent / relative).read_bytes()) == expected, 'corresponding original parent metadata differs')
    original = decode((parent / 'plan.json').read_bytes())
    require(original['config']['seed'] == seed and original['model_files'] == plan['model_files'], 'parent seed/base differs')
    require(plan['parent']['parent'] == plan['parentroot'] + '/fit_teach/adapter', 'parent path not original fork')
    for remote, expected in plan['parent']['provenance'].items():
        require(remote.startswith(plan['parentroot'] + '/'), 'parent provenance escapes parent')
        relative = remote[len(plan['parentroot']) + 1:]
        require(sha((parent / relative).read_bytes()) == expected, 'parent provenance hash mismatch')
    fit = decode((parent / 'fit_teach/verified.json').read_bytes())
    require(fit['adapter_files'] == plan['parent']['parent_files'], 'parent weight/config identity differs')
    prior_manifest = decode((parent / 'fit_teach/adapter/train_manifest.json').read_bytes())
    require(prior_manifest['steps'] == 80 and prior_manifest['config']['seed'] == seed and 'warm_start' not in prior_manifest, 'not original80-step parent')
    for arm in ARMS:
        for panel, total in PANELS.items():
            start = prefix + f'run/{arm}/{panel}/run/data/calls/'
            for suffix in ('.request.json', '.response.json'):
                require(sum(name.startswith(start) and name.endswith(suffix) for name in files) == total, 'incomplete raw panel: no scoring')
    return dict(entry=entry, files=files, prefix=prefix, read=read, digest=digest, plan=plan,
                terminal=terminal, release=release, validation=validation)


def schedule_and_material(plan, material_root, helper):
    require(sha((material_root / 'plan.json').read_bytes()) == 'd5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e', 'material anchor plan differs')
    original = decode((material_root / 'teach.json').read_bytes())
    require(sha((material_root / 'teach.json').read_bytes()) == '2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c', 'original material hash differs')
    rows = decode((material_root / 'candidate/train_teach.json').read_bytes())
    require(sha(canonical(rows, True)) == 'd44585d4081819248f18774f12d8e1260e61af6fa6aaa260afbe3833e10838ab', 'source rows changed')
    originals = {row['case_id']: (index, row) for index, row in enumerate(rows)}
    native = {row['case_id']: row for row in decode((material_root / 'plan.json').read_bytes())['row_audits']['teach']}
    memories = [row for row in rows if row['kind'] == 'memory']
    additions = [row for row in rows if row['kind'] == 'addition'][:16]
    require(len(memories) == len(additions) == 16, 'fixed source membership')
    groups, result = {}, {}
    for arm in ARMS:
        items = []
        for copy_index in range(4):
            for block in range(8):
                group = f'interleaved-r{copy_index}-b{block:02d}'
                members = [memories[2 * block], additions[(2 * block + 2 * copy_index) % 16], memories[2 * block + 1], additions[(2 * block + 2 * copy_index + 1) % 16]]
                groups[group] = dict(source_ids=[row['case_id'] for row in members],
                    copy_indices=[copy_index] * 4, item_indices=list(range(len(items), len(items) + 4)),
                    target_tokens_by_kind={kind: sum(native[row['case_id']]['target_tokens'] for row in members if row['kind'] == kind) for kind in ('memory', 'addition')})
                for slot, row in enumerate(members):
                    index, source = originals[row['case_id']]
                    item = copy.deepcopy(original['corpus'][index])
                    context = helper['MEMORY_TEMPLATES'][copy_index].format(device=row['device']) if arm == 'FOUR_VIEW' and row['kind'] == 'memory' else row['context']
                    item['spans'][0][0] = item['spans'][0][0].replace(row['context'], context)
                    item.update(group=group, order=slot)
                    item['meta']['interleaved_replay'] = dict(id=row['case_id'] + f'-copy-{copy_index}', case_id=row['case_id'], source_record_id=row['id'], source_row_index=index,
                        source_row_sha256=sha(canonical(source, True)), copy_index=copy_index, batch_group=group, batch_slot=slot)
                    items.append(item)
        require(sha(canonical({'corpus': items}, True)) == plan['material_files'][arm + '.json'], 'reconstructed corpus differs')
        updates, presented = [], Counter()
        for epoch in range(10):
            order = sorted(groups)
            random.Random(plan['seed'] * 1000 + epoch).shuffle(order)
            for batch, group in enumerate(order):
                updates.append(dict(epoch=epoch, batch=batch, group=group, **groups[group]))
                presented.update(groups[group]['source_ids'])
        require(len(updates) == 320 and len(presented) == 32 and set(presented.values()) == {40}, 'schedule source budgets')
        require(sha(canonical(updates)) == plan['native_cpu_audit']['schedule_sha256'], 'selected-seed native schedule hash differs')
        native_cost = plan['native_cpu_audit']['padded_costs'][arm]
        require(dict(presented) == native_cost['source_presentations'] and native_cost['padded_input_slots'] == 76960, 'native scheduled costs differ')
        result[arm] = dict(schedule_sha256=sha(canonical(updates)), updates=updates, padded_slots=native_cost['padded_input_slots'])
    return {row['device']: row['response'] for row in memories}, result


def recount_counts(panel, rows):
    memory = [row for row in rows if row['kind'] != 'addition']
    counts = dict(total=len(memory), correct=sum(row['correct'] for row in memory), invalid=sum(not row['valid'] for row in memory))
    if panel == 'dev':
        arithmetic = [row for row in rows if row['kind'] == 'addition']
        return dict(total=len(rows), memory=counts, addition=dict(total=len(arithmetic), adherence=sum(row['adherence'] for row in arithmetic),
                    correct_action=sum(row['correct_action'] for row in arithmetic), invalid_action=sum(not row['action_valid'] for row in arithmetic)))
    if panel == 'exact':
        return dict(counts, answer_counts=dict(Counter(row['answer'] if row['valid'] else '<invalid>' for row in rows)))
    require(Counter(row['family'] for row in rows) == {0: 16, 1: 16, 2: 16}, 'lexical family denominators')
    return dict(counts, by_family={str(family): dict(total=16, correct=sum(row['correct'] for row in rows if row['family'] == family),
                invalid=sum(not row['valid'] for row in rows if row['family'] == family)) for family in range(3)})


def thresholds(arms):
    panels = arms['FOUR_VIEW']['panels']
    dev, exact, lexical = (panels[name]['counts'] for name in ('dev', 'exact', 'lexical'))
    checks = {'dev_memory': (dev['memory']['correct'], 15), 'exact_memory': (exact['correct'], 15),
              'habit': (dev['addition']['adherence'], 30), 'ACT': (dev['addition']['correct_action'], 31)}
    checks.update({f'lexical_{family}': (lexical['by_family'][str(family)]['correct'], 15) for family in range(3)})
    return {name: dict(actual=value, minimum=minimum, passed=value >= minimum) for name, (value, minimum) in checks.items()}


def recount(package, material_root, helper):
    read, digest, plan = package['read'], package['digest'], package['plan']
    seed, files, prefix = plan['seed'], package['files'], package['prefix']
    labels, schedule = schedule_and_material(plan, material_root, helper)
    original_corpus = decode((material_root / 'teach.json').read_bytes())['corpus']
    original_rows = decode((material_root / 'candidate/train_teach.json').read_bytes())
    chat_prefix, chat_suffix = original_corpus[0]['spans'][0][0].split(original_rows[0]['context'])
    result = dict(seed=seed, capsule_sha256=package['entry']['capsule_sha256'], plan_sha256=digest('plan.json'), source=SOURCE,
        original_parent_pins=list(PARENT_PINS[seed]), parent_weight_sha256=plan['parent']['parent_files']['adapter_model.safetensors'],
        inherited_baseline_not_recounted=plan['parent']['baseline_counts'], schedules=schedule, arms={}, contradictions=[])
    worker_seconds, windows = 0.0, []
    for name, payload in files.items():
        if not name.endswith('/supervision.json'):
            continue
        supervision = decode(payload)
        process = decode(files[name.replace('supervision.json', 'process.json')])
        require(all(supervision[key] for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
                and supervision['returncode'] == 0 and supervision['error'] is None, 'worker unsuccessful')
        require(process['device'] == supervision['device'] == plan['device'] and process['pgid'] == process['pid'] and 0 < process['timeout'] <= 600, 'worker identity/bounds')
        worker_seconds += supervision['reserved_seconds']
        windows.append((process['started'], process['started'] + supervision['reserved_seconds'], process['pid']))
    windows.sort()
    require(len(windows) == len({row[2] for row in windows}) == 8 and all(left[1] <= right[0] for left, right in zip(windows, windows[1:])), 'eight sequential distinct workers')
    for arm in ARMS:
        stage = f'run/{arm}/'
        fit, manifest = read(stage + 'fit-result.json'), read(stage + 'adapter/train_manifest.json')
        warm = manifest['warm_start']
        require(digest(stage + 'adapter/train_manifest.json') == fit['manifest_sha256'], 'fit manifest seal')
        require(manifest['config'] == plan['config'] and manifest['config']['seed'] == seed and manifest['config']['batch_size'] == 4
                and manifest['config']['lr'] == .0003 and manifest['config']['rank'] == 8, 'fit recipe changed')
        require(manifest['steps'] == manifest['micro_batches'] == 320 and manifest['epochs_run'] == 10 and manifest['nonfinite_batches'] == 0
                and not manifest['empty'] and math.isfinite(manifest['final_loss']), 'fit budget/finiteness')
        require(manifest['train_tokens_seen'] == INPUTS[arm] and manifest['tokens']['target'] == 1000
                and manifest['tokens']['target_by_view'] == {'memory': 128, 'addition': 872}, 'native token counts')
        require(manifest['corpus']['sha256'] == plan['material_files'][arm + '.json'] and manifest['corpus']['n_encoded'] == 128, 'fit corpus identity')
        require(all(manifest['truncation'][key] == 0 for key in ('items_truncated', 'context_tokens_dropped', 'target_tokens_dropped', 'items_split')), 'fit drop/truncation')
        require(warm['parent_path'] == fit['parent'] == plan['parent']['parent']
                and warm['parent_files'] == warm['parent_files_after'] == fit['parent_files'] == plan['parent']['parent_files'], 'parent mutation/arm chaining')
        require(warm['source_state'] == warm['initialized_state'] == plan['parent_state'] and not warm['dtype_conversions'], 'warm tensor mismatch')
        require(warm['phase_seed'] == seed and warm['parent_cumulative_steps'] == 80 and warm['cumulative_steps'] == 400
                and warm['base_frozen'] and warm['adapter_count'] == 1 and warm['parent_unchanged']
                and warm['optimizer_initial_state_entries'] == 0 and not warm['optimizer_state_restored'], 'fresh seed-matched optimizer/history')
        require(warm['initialized_loaded_state_check'] and warm['optimizer_initialization'] == 'fresh_per_write', 'warm loaded state/fresh optimizer')
        require(manifest['config']['grad_accum'] == 1 and not manifest['config']['pack'] and manifest['config']['add_eos'], 'native training configuration')
        require(len(warm['source_state']) == len(warm['final_state']) == 392, 'tensor inventory cardinality')
        changed = sum(warm['source_state'][key]['sha256'] != value['sha256'] for key, value in warm['final_state'].items())
        require(changed > 0 and fit['accounting'] == plan['accounting'][arm], 'write state/accounting')
        for name, expected_hash in fit['adapter_files'].items():
            if prefix + stage + 'adapter/' + name in files:
                require(digest(stage + 'adapter/' + name) == expected_hash, 'adapter metadata identity')
        arm_result = dict(fit_accounting=fit['accounting'], child_sha256=fit['adapter_files']['adapter_model.safetensors'],
            train_seconds=manifest['train_seconds'], trainer_wall_seconds=manifest['wall_seconds'],
            changed_tensor_hashes=changed, trainable_parameters=manifest['lora']['trainable_params'], panels={})
        for panel, total in PANELS.items():
            panelroot = stage + panel + '/'
            prepared = read(panelroot + 'plan.json')
            data = panelroot + 'run/data/'
            require(digest(panelroot + 'plan.json') == read(panelroot + 'plan.sha256.json')['sha256'], 'panel plan seal')
            require(prepared['adapter_files'] == fit['adapter_files'] and prepared['adapter'] == fit['adapter']
                    and prepared['model_files'] == plan['model_files'] and prepared['device'] == plan['device'], 'loaded identities changed')
            for key in ('cases', 'requests', 'native_inputs', 'source_hashes'):
                require(prepared[key] == plan['templates'][panel][key], 'panel interface changed')
            require(read(data + 'identity.json') == dict(backend=prepared['identity'], model_files=plan['model_files'], adapter_files=fit['adapter_files']), 'capture identity')
            require(read(data + 'backend.cleanup.json')['closed'], 'backend not closed')
            for relative, expected in read(data + 'manifest.json')['files'].items():
                require(digest(data + relative) == expected, 'capture hash mismatch')
            process, supervision = read(panelroot + 'run/worker/process.json'), read(panelroot + 'run/worker/supervision.json')
            ready = read(data + 'backend.ready.json')
            require(ready['pid'] == process['pid'] and ready['ready'] >= process['started'], 'backend process differs')
            previous, rows = ready['ready'], []
            require(len(prepared['cases']) == len(prepared['requests']) == len(prepared['native_inputs']) == total, 'panel cardinality')
            for case, request, native in zip(prepared['cases'], prepared['requests'], prepared['native_inputs']):
                sent = read(data + 'calls/' + request['call_id'] + '.request.json')
                received = read(data + 'calls/' + request['call_id'] + '.response.json')
                response = received['response']
                require(sent['request'] == request and sent['identity'] == prepared['identity'] and request['case_id'] == case['id']
                        and request['prompt'] == case['context'], 'raw request mismatch')
                require(sent['prompt_sha256'] == sha(canonical(request['prompt'])) and received['response_sha256'] == sha(canonical(response)), 'raw value hash')
                require(previous <= sent['started'] <= received['ended'] <= process['started'] + supervision['reserved_seconds'], 'raw call outside worker')
                previous = received['ended']
                require(response['rendered_prompt'] == native['rendered_prompt'] and response['prompt_token_ids'] == native['prompt_token_ids'], 'native prefix differs')
                require(response['rendered_prompt'] == chat_prefix + request['prompt'] + chat_suffix, 'chat rendering changed')
                require(request['seed'] == 20260912 and request['temperature'] == 0 and request['max_tokens'] == 64, 'readout recipe changed')
                if case['kind'] == 'addition':
                    operands = re.fullmatch(r'Add (\d+) and (\d+)\.\nSubmit the sum using ACT: <integer>\.', request['prompt'])
                    require(operands is not None, 'arithmetic prompt unsupported')
                    expected = int(operands[1]) + int(operands[2])
                    score = helper['arithmetic_score'](response['text'], expected)
                else:
                    expected = labels[case['device']]
                    template = ('Recall the logged color of {device}.' if panel == 'dev' else
                                helper['MEMORY_TEMPLATES'][0] if panel == 'exact' else helper['CUES'][case['family']])
                    require(request['prompt'] == template.format(device=case['device']), 'memory interface changed')
                    require(re.findall(r'device-\d{3}', request['prompt']) == [case['device']] and not re.search(r'\b(blue|green|red|yellow|unknown)\b', request['prompt'], re.I), 'memory prompt leakage')
                    score = helper['memory_score'](response['text'], expected)
                require(expected == case['expected'], 'source label differs')
                rows.append(dict(case_id=case['id'], kind=case['kind'], family=case.get('family'), device=case.get('device'),
                    expected=expected, raw_text=response['text'], prompt=request['prompt'], **score,
                    input_tokens=len(response['prompt_token_ids']), output_tokens=len(response['output_token_ids']),
                    output_ids_sha256=sha(canonical(response['output_token_ids'])), seconds=received['ended']-sent['started'],
                    finish_reason=response['finish_reason'], cap_hit=len(response['output_token_ids']) >= 64))
            counts = recount_counts(panel, rows)
            reduced = read(panelroot + 'reduction.json')
            require(package['validation']['audits'][arm][panel] == dict(raw_pairs=total,
                capture_sha256=digest(data + 'manifest.json'), reduction_sha256=digest(panelroot + 'reduction.json')), 'collector panel binding')
            require(reduced['complete'] and reduced['native_token_text_audit'] and reduced['plan_sha256'] == digest(panelroot + 'plan.json')
                    and reduced['capture_sha256'] == digest(data + 'manifest.json'), 'reduction/native audit binding')
            if counts != reduced['counts']:
                result['contradictions'].append(dict(arm=arm, panel=panel, raw_counts=counts, stored_counts=reduced['counts']))
            stored = {row['case_id']: row for row in reduced['rows']}
            require(len(stored) == total, 'stored case IDs duplicate/missing')
            for row in rows:
                for key, expected in stored[row['case_id']].items():
                    if key in row and row[key] != expected:
                        result['contradictions'].append(dict(arm=arm, panel=panel, case=row['case_id'], field=key))
            costs = dict(requests=total, native_input_tokens=sum(row['input_tokens'] for row in rows), native_output_tokens=sum(row['output_tokens'] for row in rows),
                         generation_seconds=sum(row['seconds'] for row in rows), output_token_ceiling=total*64)
            usage = read(data + 'usage.json')
            require(len(usage) == 1, 'unexpected role')
            for key, expected in costs.items():
                require(abs(expected-next(iter(usage.values()))[key]) < 1e-7, 'raw usage mismatch')
            arm_result['panels'][panel] = dict(counts=counts, rows=rows, costs=costs, cap_hits=sum(row['cap_hit'] for row in rows))
        result['arms'][arm] = arm_result
    launch, release, terminal = read('launch/launch.json'), package['release'], package['terminal']
    require(launch['script_sha256'] == DRIVER_SHA and launch['seed'] == seed and launch['parent_plan_sha256'] == PARENT_PINS[seed][0], 'launch source/parent/seed')
    require(release['plan_sha256'] == digest('plan.json') and release['terminal_sha256'] == digest('run/terminal.json')
            and release['launch_sha256'] == digest('launch/launch.json') and release['xml_sha256'] == digest('run/main_release.xml'), 'release hash mismatch')
    require(release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid'] and release['controller_pid'] == launch['pid'] == terminal['controller_pid'], 'release UUID/PID differs')
    require(abs(worker_seconds-terminal['worker_reserved_seconds']) < 1e-7 and worker_seconds <= terminal['reserved_seconds'] <= release['observation']['full_reservation_seconds'], 'nested clocks')
    result['costs'] = dict(worker_seconds=worker_seconds, controller_seconds=terminal['reserved_seconds'], release_observation=release['observation'],
        final_collection_observation=package['validation']['observation'], release_utc=release['release_utc'])
    result['four_thresholds'] = thresholds(result['arms'])
    result['technical_audit'] = 'PASS' if not result['contradictions'] else 'CONTRADICTIONS'
    result['four_criteria_met'] = not result['contradictions'] and all(check['passed'] for check in result['four_thresholds'].values())
    result['paired_raw_comparison'] = {}
    for panel in PANELS:
        single = result['arms']['SINGLE_VIEW']['panels'][panel]['rows']
        four = result['arms']['FOUR_VIEW']['panels'][panel]['rows']
        require([row['case_id'] for row in single] == [row['case_id'] for row in four], 'cross-arm case order')
        result['paired_raw_comparison'][panel] = dict(total=len(single), identical_texts=sum(left['raw_text'] == right['raw_text'] for left,right in zip(single,four)),
            identical_output_ids=sum(left['output_ids_sha256'] == right['output_ids_sha256'] for left,right in zip(single,four)))
    return result


def recount_prior(package, labels, helper):
    root = Path(package['entry']['parent_local_root']) / 'readouts/teach'
    read = lambda name: decode((root / name).read_bytes())
    parent = package['plan']['parent']
    for relative, expected in parent['readout_files'].items():
        require(sha((root / relative).read_bytes()) == expected, 'prior readout inventory changed')
    prepared, reduction = read('plan.json'), read('reduction.json')
    require(prepared == parent['readout'] and prepared['adapter_files'] == parent['parent_files'], 'original baseline load identity')
    for key in ('cases', 'requests', 'native_inputs'):
        require(prepared[key] == package['plan']['templates']['dev'][key], 'original dev endpoint changed')
    require(sha((root / 'run/data/manifest.json').read_bytes()) == reduction['capture_sha256'], 'prior capture binding')
    rows = []
    for case, request in zip(prepared['cases'], prepared['requests']):
        sent = read('run/data/calls/' + request['call_id'] + '.request.json')
        response = read('run/data/calls/' + request['call_id'] + '.response.json')['response']
        require(sent['request'] == request, 'prior raw request identity')
        if case['kind'] == 'addition':
            operands = re.fullmatch(r'Add (\d+) and (\d+)\.\nSubmit the sum using ACT: <integer>\.', request['prompt'])
            require(operands is not None, 'prior arithmetic prompt')
            expected = int(operands[1]) + int(operands[2])
            score = helper['arithmetic_score'](response['text'], expected)
        else:
            expected = labels[case['device']]
            score = helper['memory_score'](response['text'], expected)
        require(case['expected'] == expected, 'prior label differs')
        rows.append(dict(case_id=case['id'], kind=case['kind'], expected=expected, raw_text=response['text'], **score))
    counts = recount_counts('dev', rows)
    require(len(rows) == 48 and counts == parent['baseline_counts'] == reduction['counts'], 'raw baseline contradiction')
    return dict(counts=counts, rows=rows, capture_sha256=reduction['capture_sha256'],
        inventory_files=len(parent['readout_files']), new_calls=0, inherited=True)


def authorized_specification():
    pins = ('e3014e7b362c983e6bba053fa91605a3307959861f2838ec35cf3637f4e6b60d',
            '0a46c83632af87b3988bfd685d2ebde9f4682dfa56d9ff68861c65774d924447')
    entries = []
    for seed, capsule_sha in enumerate(pins, 1):
        capsule = BASE / f'astra_interleaved_memory_seed{seed}_terminal_20260912.tgz'
        validation = Path(str(capsule) + '.validation.json')
        payload = validation.read_bytes()
        entries.append(dict(seed=seed, capsule=str(capsule), capsule_sha256=capsule_sha,
            validation=str(validation), validation_sha256=sha(payload), plan_sha256=decode(payload)['plan_sha256'],
            parent_local_root=str(BASE / 'astra_fundamental_followup_terminal_20260912' /
                'astra_fundamental_replications_20260912_attempt1' / f'seed{seed}')))
    return dict(schema='INTERLEAVED_REPLICATION_REVIEW_INPUT_V1', replications=entries,
        material_anchor_local_root=str(BASE / 'astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1'),
        seed0_gate_sha256='d9e4ae52b6ca7d42a21a9ac61e5c8b05dc02eedd499cc34e5de0b07b130d4f9f',
        provenance='Capsule pins supplied by Main; validation file hashes measured locally, plans cross-checked within pinned capsules.')


def audit_watch(packages):
    path = BASE / 'astra_interleaved_memory_replication_watch_receipts_20260912.tgz'
    expected = '2f09fc740c78edd8ea4acf0bd7c3bf875bcd8b12d7f9500a1e3f9d746a8953fc'
    require(sha(path.read_bytes()) == expected, 'watch capsule Main pin')
    files, names = {}, set()
    with tarfile.open(path) as archive:
        for member in archive:
            parts = member.name.rstrip('/').split('/')
            require(all(part not in ('', '.', '..') for part in parts) and '\\' not in member.name
                    and member.name not in names and (member.isdir() or member.isfile()), 'unsafe watch member')
            names.add(member.name)
            if member.isfile():
                require(member.size < 1024 * 1024, 'watch metadata size')
                files[member.name] = archive.extractfile(member).read()
    require(len(files) == 4, 'watch inventory')
    result = dict(capsule_sha256=expected, files={name:sha(value) for name,value in files.items()}, seeds={})
    for package in packages:
        seed = package['plan']['seed']
        prefix = f'astra_interleaved_replication_watch_seed{seed}_20260912_attempt1/'
        start, terminal = (decode(files[prefix + name]) for name in ('watch.json', 'terminal.json'))
        binding = start['contract']
        require(binding['seed'] == seed and binding['pid'] == package['terminal']['controller_pid']
                and binding['plan_sha256'] == package['digest']('plan.json'), 'watch run binding')
        require(terminal['launch_sha256'] == binding['launch_sha256'] == package['digest']('launch/launch.json'), 'watch launch binding')
        require(terminal['status'] == 'CONTROLLER_EXIT_OBSERVED' and terminal['success']
                and terminal['observation'] == 'ABSENT' and terminal['signals_attempted'] == []
                and terminal['observed_end_unix'] < terminal['effective_deadline'], 'watch completion/signals')
        result['seeds'][str(seed)] = dict(start=start, terminal=terminal)
    return result


def self_test():
    helper = helpers()
    tests = 0
    for text, expected in [('blue', True), (' BLUE. ', True), ('blue blue', False), ('ACT: blue', False)]:
        require(helper['memory_score'](text, 'blue')['correct'] == expected, 'memory fixture')
        tests += 1
    require(helper['arithmetic_score']('PREDICT: 3\nACT: 3', 3)['adherence'], 'habit positive fixture')
    require(not helper['arithmetic_score']('ACT: 3\nPREDICT: 3', 3)['adherence'], 'habit order fixture')
    require(not helper['arithmetic_score']('ACT: 3\nACT: 3', 3)['action_valid'], 'duplicate action fixture')
    tests += 3
    for seed in (1, 2):
        plan = dict(schema='INTERLEAVED_MEMORY_REPLICATION_V1', seed=seed, source_commit=SOURCE, source_root='/fixture/'+SOURCE,
            source_hashes={'interleaved_replication': DRIVER_SHA}, parent_pin=list(PARENT_PINS[seed]), config={'seed': seed},
            native_cpu_audit={'selected_seed': seed}, arm_order=list(ARMS), panels=PANELS, total_calls=224, confirmation_calls=0,
            outcome_selective_skips=False, reduce_only_after_both_captures=True, device='fixture-device')
        terminal = dict(status='COMPLETE', error=None, seed=seed, release_verified=True, deadline_met=True, worker_accounting_complete=True,
            automatic_progression=False, gate_evaluated=False, budget_extended=False, device='fixture-device',
            arms={arm:{'readouts':dict(PANELS)} for arm in ARMS}, captured={arm:{'captures':dict(PANELS)} for arm in ARMS})
        release = dict(full_release=True, controller_absent=True, device='fixture-device')
        terminal_preflight(plan, terminal, release, seed)
        tests += 1
        for mutate in ('partial', 'missing_panel', 'wrong_parent', 'wrong_seed'):
            wrong_plan, wrong_terminal = copy.deepcopy(plan), copy.deepcopy(terminal)
            if mutate == 'partial': wrong_terminal['status'] = 'PARTIAL'
            if mutate == 'missing_panel': del wrong_terminal['captured']['FOUR_VIEW']['captures']['lexical']
            if mutate == 'wrong_parent': wrong_plan['parent_pin'] = list(PARENT_PINS[3-seed])
            if mutate == 'wrong_seed': wrong_plan['config']['seed'] = 0
            try:
                terminal_preflight(wrong_plan, wrong_terminal, release, seed)
            except ValueError:
                tests += 1
            else:
                raise AssertionError('fixture incorrectly accepted: ' + mutate)
    print(json.dumps(dict(status='PREPARATION_FIXTURES_PASS', checks=tests, real_capsules_read=0, outcomes_read=0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--authorized-capsules', action='store_true')
    parser.add_argument('--extend-existing-review', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        require(args.manifest is None, 'self-test never reads capsules')
        return self_test()
    if args.authorized_capsules:
        require(args.manifest is None, 'choose one input mode')
        specification = authorized_specification()
        payload = canonical(specification)
    else:
        require(args.manifest is not None and args.manifest_sha256 is not None, 'Main-supplied manifest and hash required; no automatic data discovery')
        payload = args.manifest.read_bytes()
        require(sha(payload) == args.manifest_sha256, 'Main input manifest pin differs')
        specification = decode(payload)
    require(specification['schema'] == 'INTERLEAVED_REPLICATION_REVIEW_INPUT_V1', 'wrong input schema')
    entries = specification['replications']
    require([entry['seed'] for entry in entries] == [1, 2], 'both predeclared seeds in order required')
    packages = [preflight(entry, specification['seed0_gate_sha256']) for entry in entries]
    helper = helpers()
    results = [recount(package, Path(specification['material_anchor_local_root']), helper) for package in packages]
    for package, result in zip(packages, results):
        labels = {row['device']: row['expected'] for row in result['arms']['FOUR_VIEW']['panels']['exact']['rows']}
        result['baseline_raw_recount'] = recount_prior(package, labels, helper)
        result.pop('inherited_baseline_not_recounted')
        result['custody'] = dict(inventory_count=len(package['files']), device=package['plan']['device'],
            gpu_uuid=package['release']['gpu']['gpu_uuid'], source_hashes=package['plan']['source_hashes'],
            model_files=package['plan']['model_files'], material_files=package['plan']['material_files'],
            origin=package['plan']['origin'], native_cpu_audit=package['plan']['native_cpu_audit'])
    watch = audit_watch(packages) if args.authorized_capsules else None
    result = dict(status='COMPLETE_INDEPENDENT_RECOUNT' if all(row['technical_audit'] == 'PASS' for row in results) else 'CONTRADICTIONS',
        input_manifest_sha256=sha(payload), input_specification=specification, watchdog=watch, replications=results,
        automatic_progression=False, disclosure='Authored older related replay code and root0 raw audit; not a blind/fresh-author review.',
        limits=['Same16 facts across memory panels/lexical48; no novel facts, general FOUR superiority, parenting/G3/freeze/P1 or H2 promotion.',
                'No tokenizer/model/native/GPU/SSH/Git execution; weight and native token/state evidence audited via receipts.',
                'Selected-seed schedule reconstructed; actual per-step execution is not independently traced. Native FOUR padded costs are receipt-level evidence.'])
    output = BASE / (STEM + '.json')
    if output.exists():
        previous = decode(output.read_bytes())
        if previous.get('status') != 'PREPARED_AWAITING_MAIN_CAPSULES':
            require(args.extend_existing_review and previous['input_manifest_sha256'] == result['input_manifest_sha256']
                and [row['arms'] for row in previous['replications']] == [row['arms'] for row in results],
                'completed review may only be explicitly extended with unchanged raw arm results and inputs')
    output.write_bytes(canonical(result, True))
    print(json.dumps({'status':result['status'], 'seeds':[row['seed'] for row in results], 'output':str(output)}))


if __name__ == '__main__':
    main()
