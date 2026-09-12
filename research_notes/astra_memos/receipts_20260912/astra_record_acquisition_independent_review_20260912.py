import ast
import hashlib
import json
import math
import re
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


BASE = Path('/tmp')
STEM = 'astra_record_acquisition_independent_review_20260912'
CAPSULE = BASE / 'astra_rulegame_record_acquisition_terminal_20260912.tgz'
EXPECTED = 'f7faf00c65ba67c76a3778750fcc9b093d544cd4543df160635200c5940c8e27'
WRITE = BASE / 'astra_rulegame_record_write_terminal_20260912/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2'
FORMATION = BASE / 'astra_rulegame_v3_formation_terminal_20260912/astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1/formation/data'
CELLS = ('OFF', 'P', 'A')
CONTEXTS = ('FULL', 'MAPPING_SENTENCE_REMOVED')


def unique(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, ('duplicate JSON key', key)
        result[key] = value
    return result


def decode(payload):
    return json.loads(payload, object_pairs_hook=unique)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def value_sha(value):
    return sha((json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode())


def main():
    validation_path = BASE / 'astra_acquisition_terminal_validation_20260912.json'
    validation = decode(validation_path.read_bytes())
    assert sha(CAPSULE.read_bytes()) == EXPECTED == validation['archive_sha256']
    files = {}
    with tarfile.open(CAPSULE) as archive:
        members = archive.getmembers()
        assert len(members) == len(validation['files']) == 119
        assert sum(member.size for member in members) < 64 * 1024 * 1024
        for member in members:
            assert member.isfile() and member.name not in files and member.name.startswith('metadata/')
            assert not any(part in ('', '.', '..') for part in member.name.split('/')) and '\\' not in member.name
            assert PurePosixPath(member.name).suffix not in {'.safetensors', '.bin', '.pt', '.pth', '.ckpt', '.pyc', '.pyo'}
            payload = archive.extractfile(member).read()
            assert sha(payload) == validation['files'][member.name]
            files[member.name] = payload
        assert set(files) == set(validation['files'])

    def read(path):
        return decode(files['metadata/' + path])

    def digest(path):
        return sha(files['metadata/' + path])

    def local(path):
        return decode(path.read_bytes())

    plan = read('root/plan.json')
    assert digest('root/plan.json') == read('root/plan.sha256.json')['sha256']
    protocol = plan['protocol']
    assert protocol['cells'] == list(CELLS) and protocol['contexts'] == list(CONTEXTS)
    assert protocol['requests'] == 24 and protocol['candidate_forwards'] == 48 and protocol['generations'] == 0
    assert protocol['strict_improvement'] and protocol['eos'] and protocol['report_all_cross_arm']
    assert protocol['own_record_acquisition'] == 'each adapter: both own records individually improve sum AND margin versus OFF, per context'
    assert protocol['stronger_P_specific'] == 'both P-owned records individually improve sum AND margin versus OFF AND A, per context'
    source_checks = {}
    for path, expected in plan['source_pins'].items() | plan['scoring_pins'].items():
        matches = [name for name in files if name.startswith('metadata/source/') and name.endswith('_' + Path(path).name)]
        assert len(matches) == 1 and sha(files[matches[0]]) == expected
        source_checks[path] = expected
    assert sha((BASE / 'astra_rulegame_record_acquisition_20260912.py').read_bytes()) == plan['self_sha256']
    assert plan['source_root'].endswith('/610c6edd05ce9c85720ee6e992889badecc2c158')
    writeplan = local(WRITE / 'plan.json')
    assert sha((WRITE / 'plan.json').read_bytes()) == plan['write_plan_sha256'] == '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
    assert sha((WRITE / 'run/result.json').read_bytes()) == plan['lineage']['result_sha256']
    assert plan['model_files'] == writeplan['model_files']
    diagnostic_source = files[next(name for name in files if name.endswith('_rulegame_parenting_diagnostic.py'))].decode()
    relation = next(ast.literal_eval(node.value) for node in ast.parse(diagnostic_source).body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'RELATION_DEFINITION' for target in node.targets))
    needle = '\n' + relation
    records = {}
    for record in plan['records']:
        key, arm, ordinal = record['record_id'], record['origin_arm'], record['ordinal']
        assert key == arm + str(ordinal) and key not in records
        raw = record['raw']
        truth = decode(raw)
        assert set(truth) == {'try', 'observed', 'predicted', 'relation'}
        assert type(truth['observed']) is bool and type(truth['predicted']) is bool
        assert len(truth['try']) == 3 and all(type(value) is int for value in truth['try'])
        expected_relation = 'matched' if truth['predicted'] == truth['observed'] else 'mismatched'
        assert truth['relation'] == expected_relation
        matches = list(re.finditer(r'"relation"\s*:\s*"(matched|mismatched)"', raw))
        assert len(matches) == 1
        start, end = matches[0].span(1)
        replacement = 'mismatched' if expected_relation == 'matched' else 'matched'
        foil = raw[:start] + replacement + raw[end:]
        assert decode(foil) == dict(truth, relation=replacement)
        foil_spec = dict(text=foil, truth_span=[start, end], foil_span=[start, start + len(replacement)],
            truth_byte_span=[len(raw[:start].encode()), len(raw[:end].encode())],
            foil_byte_span=[len(raw[:start].encode()), len((raw[:start] + replacement).encode())],
            original_relation=expected_relation, foil_relation=replacement)
        assert foil_spec == record['foil']
        for full, removed in [('context', 'removed_context'), ('prompt', 'removed_prompt')]:
            assert record[full].count(needle) == 1
            assert record[removed] == record[full].replace(needle, '', 1)
        source = record['source']
        assert source == local(WRITE / f'material/provenance/{arm}.sources.json')[ordinal]
        corpus_row = local(WRITE / f'material/corpora/{arm}.json')['corpus'][ordinal]
        assert corpus_row['spans'] == [[record['context'], False, 'record_context'], [raw, True, 'own_raw_record']]
        tokens = local(WRITE / f'material/provenance/{arm}.tokens.json')['rows'][ordinal]
        assert record['training_ids'] == tokens['input_ids'] and record['training_labels'] == tokens['labels']
        for path, expected in source['files'].items():
            assert sha((FORMATION / path).read_bytes()) == expected
        original_request = local(FORMATION / f"calls/{source['call_id']}.request.json")['request']
        original_response = local(FORMATION / f"calls/{source['call_id']}.response.json")['response']
        assert original_request['prompt'] == record['prompt'] and original_response['text'] == raw
        assert original_response['rendered_prompt'] == record['context']
        observed_match = re.search(r'Observed fields: (\{[^\n]+\})', record['prompt'])
        observed = decode(observed_match[1])
        assert truth['try'] == observed['values'] and truth['observed'] == observed['observed'] and truth['predicted'] == observed['predicted']
        records[key] = dict(record, decoded_truth=truth, mapping_deleted_chars=len(needle),
            mapping_deleted_bytes=len(needle.encode()), conditional_prefix_limit='earlier correct raw target fields are teacher-forced before relation')
    assert list(records) == ['P0', 'P1', 'A0', 'A1']

    def check_candidate(request, candidate):
        context, raw = request['rendered_prompt'], candidate['text']
        complete = context + raw
        prefix = request['payload']['prompt_input_ids']
        ids, labels, targets = candidate['input_ids'], candidate['labels'], candidate['response_ids']
        offsets = candidate['token_offsets_char']
        assert ids == prefix + targets and labels == [-100] * len(prefix) + targets
        assert 0 < len(prefix) < len(ids) <= 4096 and targets[-1] == 151645 and 151645 not in targets[:-1]
        assert candidate['eos_position'] == len(ids) - 1 and candidate['terminal_eos_zero_width']
        assert candidate['label_positions'] == list(range(len(prefix), len(ids)))
        assert candidate['predictor_positions'] == list(range(len(prefix) - 1, len(ids) - 1))
        assert len(offsets) == len(ids) and offsets[-1] == [len(complete), len(complete)]
        cursor = 0
        for index, (start, end) in enumerate(offsets[:-1]):
            assert start == cursor and start < end <= len(complete)
            assert not start < len(context) < end
            assert labels[index] == (-100 if end <= len(context) else ids[index])
            cursor = end
        assert cursor == len(complete)
        assert candidate['token_offsets_utf8'] == [[len(complete[:start].encode()), len(complete[:end].encode())] for start, end in offsets]
        span = records[request['record_id']]['foil']['truth_span' if candidate['candidate_id'] == 'truth' else 'foil_span']
        assert candidate['relation_char_span'] == span
        positions = [index for index, (start, end) in enumerate(offsets[:-1]) if start < len(context) + span[1] and end > len(context) + span[0]]
        assert positions == candidate['relation_label_positions'] and min(positions) >= len(prefix)

    requests = plan['requests']
    assert len(requests) == 8
    for index, request in enumerate(requests):
        record = records[request['record_id']]
        full = request['context_condition'] == 'FULL'
        assert request['call_id'] == f'{index:04d}' and request['record_id'] == ['P0', 'P1', 'A0', 'A1'][index // 2]
        assert request['context_condition'] == CONTEXTS[index % 2]
        assert request['origin_arm'] == record['origin_arm']
        assert request['version'] == plan['version'] and request['operation'] == 'score_raw_record_relation'
        assert request['prompt'] == record['prompt' if full else 'removed_prompt']
        assert request['rendered_prompt'] == record['context' if full else 'removed_context']
        assert [candidate['candidate_id'] for candidate in request['candidates']] == ['truth', 'foil']
        assert request['candidates'][0]['text'] == record['raw'] and request['candidates'][1]['text'] == record['foil']['text']
        for candidate in request['candidates']:
            check_candidate(request, candidate)
        if full:
            assert request['candidates'][0]['input_ids'] == record['training_ids']
            assert request['candidates'][0]['labels'] == record['training_labels']
        else:
            for left, right in zip(requests[index - 1]['candidates'], request['candidates']):
                assert left['response_ids'] == right['response_ids']

    result = dict(status='RAW_AUDIT_IN_PROGRESS', capsule_sha256=EXPECTED,
        plan_sha256=digest('root/plan.json'), validation_sha256=sha(validation_path.read_bytes()),
        verified_metadata_files=len(files), source_hashes_verified=source_checks, protocol=protocol,
        records=records, requests=requests, cells={}, comparisons=[], context_differences=[], contradictions=[],
        disclosure='Authored formation/write collectors, not acquisition driver/collector. Main already saw complete driver results; this is not a blinded review. Raw vectors reduced independently; no existing reducer imported/executed.')
    differences = []

    def compare(expected, stored, path):
        if isinstance(expected, dict):
            assert isinstance(stored, dict) and set(expected) <= set(stored), path
            for key, value in expected.items():
                compare(value, stored[key], path + '/' + key)
        elif isinstance(expected, list):
            assert len(expected) == len(stored), path
            for index, (left, right) in enumerate(zip(expected, stored)):
                compare(left, right, path + '/' + str(index))
        elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
            delta = abs(expected - stored)
            differences.append(delta)
            if delta > 1e-9:
                result['contradictions'].append(dict(path=path, independent=expected, stored=stored, difference=delta))
        elif expected != stored:
            result['contradictions'].append(dict(path=path, independent=expected, stored=stored))

    worker_windows = []
    common_max = 0.0
    for cell in CELLS:
        root = f'root/run/{cell}/'
        spec = read(f'root/run/{cell}.spec.json')
        assert spec['requests'] == requests and spec['device'] == plan['device'] == '2'
        for key in ('model', 'model_files', 'scoring_pins', 'source_pins', 'source_root', 'self_sha256', 'protocol'):
            assert spec[key] == plan[key]
        fit = plan['lineage']['fits'].get(cell)
        assert spec['adapter'] == (fit['adapter'] if fit else None)
        assert spec['adapter_files'] == (fit['files'] if fit else {})
        if fit:
            fit_manifest_path = WRITE / f'fits/{cell}/adapter/train_manifest.json'
            assert sha(fit_manifest_path.read_bytes()) == fit['manifest_sha256']
            assert local(fit_manifest_path)['steps'] == fit['steps'] == 12
            assert local(WRITE / f'fits/{cell}/receipt.json')['files'] == fit['files']
        identity = read(root + 'data/identity.json')
        assert identity == dict(version=plan['version'], backend='HF teacher-forced score; not vLLM generation',
            model=plan['model'], model_files=plan['model_files'], adapter=spec['adapter'], adapter_files=spec['adapter_files'],
            scorer_pins=spec['scoring_pins'], model_authentication_certified=False)
        process, supervision = read(root + 'process.json'), read(root + 'supervision.json')
        isolation, ready = read(root + 'data/isolation.json'), read(root + 'data/backend.ready.json')
        runtime = ready['runtime']
        assert runtime['adapter_count'] == (0 if cell == 'OFF' else 1)
        assert not runtime['training'] and runtime['trainable_parameters'] == 0 and not runtime['use_cache'] and not runtime['generation']
        assert runtime['load_dtype'] == 'bf16' and runtime['attention'] == 'eager'
        assert runtime['scorer'] == 'semantic_carrier_diagnostic.score'
        assert isolation['spec_sha256'] == digest(f'root/run/{cell}.spec.json')
        assert isolation['pid'] == isolation['pgid'] == process['pid'] == process['pgid'] == ready['pid']
        assert isolation['parent_pid'] == read('root/run/controller.json')['pid']
        assert not isolation['training'] and isolation['generations'] == 0
        assert 0 < process['timeout'] <= 600 and supervision['device'] == process['device'] == '2'
        assert all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
        assert supervision['returncode'] == 0 and supervision['error'] is None
        assert read(root + 'data/backend.cleanup.json')['closed']
        audit = read(root + 'data/native_audit.json')
        assert audit == dict(candidate_forwards=16, generations=0, native_forward_inputs=True,
            native_prefix_offsets_masks_eos=True, ok=True, protocol=plan['version'], requests=8)
        manifest = read(root + 'data/manifest.json')
        for path, expected in manifest['files'].items():
            assert digest(root + 'data/' + path) == expected
        previous = ready['ready']
        assert previous >= process['started']
        rows, raw = [], []
        costs = dict(requests=0, candidate_forwards=0, scored_target_tokens=0, native_input_tokens=0, padded_forward_tokens=0, call_seconds=0.0)
        assert len([name for name in files if name.startswith('metadata/' + root + 'data/calls/') and name.endswith('.request.json')]) == 8
        for request in requests:
            stem = root + 'data/calls/' + request['call_id']
            sent, received = read(stem + '.request.json'), read(stem + '.response.json')
            response = received['response']
            assert sent['request'] == request and sent['identity'] == identity
            assert sent['request_sha256'] == value_sha(request) and received['response_sha256'] == value_sha(response)
            assert previous <= sent['started'] <= received['ended'] <= process['started'] + supervision['reserved_seconds']
            previous = received['ended']
            candidates, vectors = request['candidates'], response['token_logprobs']
            width = max(len(candidate['input_ids']) for candidate in candidates)
            assert len(response['native_forwards']) == len(vectors) == 2
            scores = {}
            for candidate, vector, forwarded in zip(candidates, vectors, response['native_forwards']):
                assert forwarded == dict(input_ids=[candidate['input_ids'] + [candidate['response_ids'][-1]] * (width - len(candidate['input_ids']))],
                    attention_mask=[[1] * width], position_ids=[list(range(width))], use_cache=False)
                assert len(vector) == len(candidate['response_ids']) and all(type(value) in (int, float) and math.isfinite(value) and value <= 0 for value in vector)
                total = math.fsum(vector)
                scores[candidate['candidate_id']] = dict(sum_logprob=total, mean_logprob=total / len(vector), scored_tokens=len(vector), token_logprobs=vector)
            common = 0
            for left, right in zip(candidates[0]['response_ids'], candidates[1]['response_ids']):
                if left != right:
                    break
                common += 1
            mismatch = max((abs(vectors[0][index] - vectors[1][index]) for index in range(common)), default=0)
            common_max = max(common_max, mismatch)
            assert mismatch <= 1e-6
            assert math.exp(scores['truth']['sum_logprob']) + math.exp(scores['foil']['sum_logprob']) <= 1 + 1e-6
            row = dict(record_id=request['record_id'], origin_arm=request['origin_arm'], context_condition=request['context_condition'],
                truth=scores['truth'], foil=scores['foil'], truth_foil_margin=scores['truth']['sum_logprob'] - scores['foil']['sum_logprob'])
            rows.append(row)
            raw.append(dict(call_id=request['call_id'], request_sha256=sent['request_sha256'], response_sha256=received['response_sha256'],
                started=sent['started'], ended=received['ended'], native_forwards=response['native_forwards'],
                common_target_prefix_tokens=common, common_prefix_max_logprob_difference=mismatch))
            costs['requests'] += 1
            costs['candidate_forwards'] += 2
            costs['scored_target_tokens'] += sum(len(candidate['response_ids']) for candidate in candidates)
            costs['native_input_tokens'] += sum(len(candidate['input_ids']) for candidate in candidates)
            costs['padded_forward_tokens'] += 2 * width
            costs['call_seconds'] += received['ended'] - sent['started']
        reduced = dict(cell=cell, rows=rows, costs=costs, capture_sha256=digest(root + 'data/manifest.json'))
        compare(reduced, read(root + 'reduction.json'), cell)
        result['cells'][cell] = dict(reduced, raw_receipts=raw, runtime=runtime, supervision=supervision,
            process=process, process_to_ready_seconds=ready['ready'] - process['started'],
            adapter_sha256=spec['adapter_files'].get('adapter_model.safetensors'))
        worker_windows.append((process['started'], process['started'] + supervision['reserved_seconds'], process['pid']))

    indexed = {cell: {(row['record_id'], row['context_condition']): row for row in result['cells'][cell]['rows']} for cell in CELLS}

    def gain(left, right, key):
        target, control = indexed[left][key], indexed[right][key]
        assert target['truth']['scored_tokens'] == control['truth']['scored_tokens']
        log_delta = target['truth']['sum_logprob'] - control['truth']['sum_logprob']
        margin_delta = target['truth_foil_margin'] - control['truth_foil_margin']
        return dict(sum_logprob_delta=log_delta, mean_logprob_delta=target['truth']['mean_logprob'] - control['truth']['mean_logprob'],
            margin_delta=margin_delta, both_improve=log_delta > 0 and margin_delta > 0)

    for record_id in records:
        for context in CONTEXTS:
            key = record_id, context
            result['comparisons'].append(dict(record_id=record_id, context_condition=context,
                P_vs_OFF=gain('P', 'OFF', key), A_vs_OFF=gain('A', 'OFF', key), P_vs_A=gain('P', 'A', key)))
        for cell in CELLS:
            full, removed = indexed[cell][record_id, 'FULL'], indexed[cell][record_id, 'MAPPING_SENTENCE_REMOVED']
            result['context_differences'].append(dict(cell=cell, record_id=record_id, direction='removed minus FULL',
                truth_sum_delta=removed['truth']['sum_logprob'] - full['truth']['sum_logprob'],
                truth_mean_delta=removed['truth']['mean_logprob'] - full['truth']['mean_logprob'],
                margin_delta=removed['truth_foil_margin'] - full['truth_foil_margin']))
    decisions = {}
    for context in CONTEXTS:
        own_ll, own_joint, details = {}, {}, {}
        for arm in ('P', 'A'):
            details[arm] = [gain(arm, 'OFF', (arm + str(index), context)) for index in range(2)]
            own_ll[arm] = all(row['sum_logprob_delta'] > 0 for row in details[arm])
            own_joint[arm] = all(row['both_improve'] for row in details[arm])
        stronger = all(gain('P', control, ('P' + str(index), context))['both_improve'] for index in range(2) for control in ('OFF', 'A'))
        shared = all(gain(arm, 'OFF', ('P' + str(index), context))['both_improve'] for arm in ('P', 'A') for index in range(2))
        decisions[context] = dict(own_truth_LL_improvement_descriptive=own_ll, own_record_acquisition_vs_OFF=own_joint,
            stronger_P_specific_selective_carriage=stronger, both_adapters_gain_on_P_records=shared, individual_own_rows=details)
    terminal = read('root/run/result.json')
    assert terminal['status'] == 'COMPLETE_TRAINED_RECORD_ACQUISITION_CHECK' and terminal['requests'] == 24 and terminal['candidate_forwards'] == 48 and terminal['generations'] == 0
    compare(result['comparisons'], terminal['summary']['all_record_comparisons'], 'summary/comparisons')
    for context, decision in decisions.items():
        compare({key: decision[key] for key in ('own_record_acquisition_vs_OFF', 'stronger_P_specific_selective_carriage', 'both_adapters_gain_on_P_records')}, terminal['summary']['contexts'][context], 'summary/' + context)
    result['criteria'] = decisions
    result['own_joint_context_pattern'] = {}
    for arm in ('P', 'A'):
        full_pass = decisions['FULL']['own_record_acquisition_vs_OFF'][arm]
        removed_pass = decisions['MAPPING_SENTENCE_REMOVED']['own_record_acquisition_vs_OFF'][arm]
        pattern = ('both' if full_pass and removed_pass else 'FULL_only' if full_pass else
                   'MAPPING_SENTENCE_REMOVED_only' if removed_pass else 'neither_demonstrated')
        result['own_joint_context_pattern'][arm] = pattern
    compare(result['own_joint_context_pattern'], terminal['summary']['own_acquisition_context_pattern'], 'summary/context_pattern')
    controller = read('root/run/controller.json')
    launch, release = read('launch/launch.json'), read('collection/release.json')
    custody, collection_audit = read('collection/custody.json'), read('collection/audit.json')
    assert release['full_release'] and release['error_type'] is None and validation['full_release']
    assert release['gpu']['gpu_uuid'] == launch['gpu']['gpu_uuid']
    assert controller['pid'] == launch['pid'] and controller['plan_sha256'] == digest('root/plan.json')
    assert controller['hard_end'] <= min(controller['started_wall'] + 1800, plan['deadline'], plan['lease_cutoff'])
    assert plan['lease_cutoff'] == plan['supplied_lease_end'] - 21600
    assert custody['launch_sha256'] == digest('launch/launch.json') and custody['plan_sha256'] == digest('root/plan.json')
    for name, expected in custody['input_hashes'].items():
        assert sha(files[name]) == expected
    assert collection_audit['verified'] and collection_audit['controller_within_bound'] and collection_audit['verified_worker_cost_complete']
    assert len({item[2] for item in worker_windows}) == 3
    assert all(left[1] <= right[0] for left, right in zip(worker_windows, worker_windows[1:]))
    totals = {key: sum(result['cells'][cell]['costs'][key] for cell in CELLS) for key in result['cells']['OFF']['costs']}
    compare(totals, collection_audit['totals'], 'collection/totals')
    worker_seconds = sum(result['cells'][cell]['supervision']['reserved_seconds'] for cell in CELLS)
    assert abs(worker_seconds - collection_audit['observed_verified_worker_seconds']) < 1e-8
    assert worker_seconds <= terminal['controller_seconds'] == custody['controller_seconds'] <= 1800
    result['costs'] = dict(totals, worker_seconds=worker_seconds, controller_seconds=terminal['controller_seconds'],
        full_launch_to_release_seconds=custody['full_launch_to_release_seconds'],
        full_A40_minutes=custody['full_launch_to_release_seconds'] / 60,
        release_utc=datetime.fromtimestamp(release['observed_wall'], timezone.utc).isoformat(),
        collection_seconds=validation['collection_seconds'], accounting=custody['accounting'])
    result['numeric_checks'] = dict(max_stored_reduction_difference=max(differences, default=0),
        common_prefix_max_logprob_difference=common_max, vector_count=48,
        reaggregation_tolerance=1e-9, decision_tolerance='none: strict positive deltas, no retuning')
    result['status'] = 'PASS_RAW_NUMERICAL_AND_CUSTODY_AUDIT' if not result['contradictions'] else 'CONTRADICTIONS'
    result['limits'] = [
        'Logprob-vector arithmetic checked independently; no logits, tokenizer/model/native rerun or weight-byte verification here.',
        'Native forward/mask/EOS, loaded-state and immutable-inventory receipts audited, not model-origin or semantic-nonleakage certification.',
        'Teacher forcing supplies earlier correct raw fields; relation scores are conditional, not autonomous predictions or pre-TRY competence.',
        'Removing only the mapping sentence leaves other schema/action/outcome scaffolding and changes length/positions.',
        'Joint-criterion failure is not absence of parameter learning; strong OFF discrimination/saturation can coexist with truth-likelihood gains.',
        'No alternate criterion rescue, dose change, heldout acquisition claim, parenting/P1/H1/H2/G5 promotion or automatic launch.',
    ]
    with (BASE / (STEM + '.json')).open('w') as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
    print('status', result['status'], 'numeric', result['numeric_checks'])
    for record in records:
        for context in CONTEXTS:
            print(record, context, [(cell, round(indexed[cell][record, context]['truth']['sum_logprob'], 9), round(indexed[cell][record, context]['truth_foil_margin'], 9)) for cell in CELLS])
    print('criteria', decisions)
    print('costs', result['costs'])


if __name__ == '__main__':
    main()
