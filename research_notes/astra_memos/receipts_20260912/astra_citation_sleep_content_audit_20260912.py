#!/usr/bin/env python3
"""Offline, posthoc content audit; reads captures, never loads model weights."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SOURCE = Path('/tmp/astra_citation_sleep_terminal_20260912')
OUTPUT = Path('/tmp/astra_citation_sleep_content_audit_20260912')
EXPECTED_TREE_SHA256 = 'fbc50647ea103ab96d588f8ef7116e018b0a27979cafb9c49f3ddd1d0469b6ba'
RUN = 'astra_citation_sleep_20260912_attempt1'
PREP = 'astra_citation_sleep_preparation_20260912_attempt1'
LAUNCH = 'astra_citation_sleep_20260912_attempt1_launch'
ARMS = ('off', 'full', 'syntax')


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def require(condition, description):
    if not condition:
        raise ValueError(description)


def load(relative):
    return json.loads((SOURCE / relative).read_bytes())


def inventory():
    paths = sorted(SOURCE.rglob('*'))
    require(not any(path.is_symlink() for path in paths), 'Unexpected source symlink')
    return {str(path.relative_to(SOURCE)): sha256(path.read_bytes())
            for path in paths if path.is_file()}


class ObjectPairs(list):
    pass


def literal_check(text, board):
    found = re.search(r'"checks"\s*:\s*\[\s*(?=\{)', text)
    require(found is not None, 'No literal check object in captured output')
    start = found.end()
    pairs, end = json.JSONDecoder(object_pairs_hook=ObjectPairs).raw_decode(text, start)
    require(isinstance(pairs, ObjectPairs), 'Expected a literal JSON object')
    keys = [key for key, value in pairs]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    result = {
        'byte_span': [len(text[:start].encode()), len(text[:end].encode())],
        'literal_text': text[start:end],
        'literal_sha256': sha256(text[start:end].encode()),
        'duplicate_keys': duplicates,
        'well_shaped_literal_check': False,
        'literal_witness_true': False,
    }
    if duplicates:
        result['reason'] = 'duplicate keys; not merged into a coordinate pair'
        return result
    fields = dict(pairs)
    result['fields'] = fields
    cells = fields.get('cells')
    digit = fields.get('digit')
    group = fields.get('group')
    coordinates_ok = (
        type(cells) is list and len(cells) == 2
        and all(type(cell) is list and len(cell) == 2
                and all(type(component) is int and 1 <= component <= 4
                        for component in cell) for cell in cells)
        and cells[0] != cells[1]
    )
    if not (set(fields) == {'group', 'cells', 'digit'} and coordinates_ok
            and group in ('row', 'column', 'box')
            and type(digit) is int and 1 <= digit <= 4):
        result['reason'] = 'not one well-shaped two-coordinate literal check'
        return result
    values = [board[row - 1][column - 1] for row, column in cells]
    same_group = {
        'row': cells[0][0] == cells[1][0],
        'column': cells[0][1] == cells[1][1],
        'box': ((cells[0][0] - 1) // 2, (cells[0][1] - 1) // 2)
        == ((cells[1][0] - 1) // 2, (cells[1][1] - 1) // 2),
    }[group]
    result.update({
        'well_shaped_literal_check': True,
        'actual_board_values': values,
        'same_declared_group': same_group,
        'values_equal_each_other': values[0] == values[1],
        'both_values_equal_declared_digit': values == [digit, digit],
        'digit_matches_first_cell': values[0] == digit,
        'digit_matches_second_cell': values[1] == digit,
        'literal_witness_true': same_group and values == [digit, digit],
        'reason': 'literal witness true' if same_group and values == [digit, digit]
        else '; '.join(reason for reason, applies in [
            ('coordinates outside the same declared group', not same_group),
            ('board values do not both equal the declared digit', values != [digit, digit]),
        ] if applies),
    })
    return result


def prefix_length(left, right):
    return next((index for index, (first, second) in enumerate(zip(left, right))
                 if first != second), min(len(left), len(right)))


def self_tests():
    board = [[1, 1, 3, 4], [1, 2, 3, 4], [3, 4, 1, 2], [4, 3, 2, 1]]
    def example(group, cells, digit):
        return '{"checks":[' + compact({'group': group, 'cells': cells, 'digit': digit}) + '][]}'
    for group, cells in [('row', [[1, 1], [1, 2]]),
                         ('column', [[1, 1], [2, 1]]),
                         ('box', [[1, 1], [2, 1]])]:
        require(literal_check(example(group, cells, 1), board)['literal_witness_true'], group)
    for cells, digit in [([[1, 1], [3, 3]], 1), ([[1, 1], [1, 2]], 2),
                         ([[1, 1], [1, 1]], 1), ([[0, 1], [1, 2]], 1),
                         ([[True, 1], [1, 2]], 1), ([1, 2], 1)]:
        require(not literal_check(example('box', cells, digit), board)['literal_witness_true'],
                'False witness accepted')
    duplicate = '{"checks":[{"group":"box","cells":[1,1],"cells":[1,2],"digit":1}]}'
    require(literal_check(duplicate, board)['duplicate_keys'] == ['cells'], 'Duplicate key lost')
    require(prefix_length(b'abc', b'abd') == 2, 'Byte prefix test')


def audit():
    self_tests()
    files = inventory()
    tree_digest = sha256(compact(files).encode())
    require(tree_digest == EXPECTED_TREE_SHA256, 'Source tree differs from pinned capture')
    manifests_checked = 0
    omitted = []
    for relative in files:
        if not relative.endswith('/artifact_hashes.json'):
            continue
        for name, expected in load(relative)['files'].items():
            target = str(Path(relative).parent / name)
            if target not in files:
                require(name == 'adapter_model.safetensors', 'Unexpected missing artifact')
                omitted.append({'path': target, 'captured_sha256_not_locally_verified': expected})
            else:
                require(files[target] == expected, 'Artifact hash mismatch: ' + target)
                manifests_checked += 1
    config = load(PREP + '/config.json')
    preflight = load(PREP + '/preflight.json')
    provenance = load(PREP + '/provenance.json')
    panel_rows = load(PREP + '/panel.json')
    panel = {row['case_id']: row for row in panel_rows}
    completed = load(RUN + '/COMPLETED.json')
    native = load(LAUNCH + '/MAIN_TERMINAL_AUDIT.json')
    launch = load(LAUNCH + '/launch.json')
    require(len(panel) == 8 and len(omitted) == 2, 'Unexpected panel or weight inventory')
    require(provenance['panel'] == panel_rows, 'Provenance panel differs')
    require(native['report_sha256'] == files[RUN + '/COMPLETED.json'], 'Terminal report hash')
    prep_hash = files[PREP + '/artifact_hashes.json']
    require(native['preparation_sha256'] == launch['preparation_sha256'] == prep_hash,
            'Preparation binding mismatch')
    require(completed['status'] == 'COMPLETE' and completed['synthetic'] is False,
            'Unexpected completion status')
    require(completed['boundary'] == config['boundary'] == launch['boundary'], 'Boundary differs')
    require(launch['protocol'] == config['protocol'], 'Protocol differs')
    prefix = preflight['prefix'].encode()
    require(len(prefix) == 75 and sha256(prefix) == preflight['prefix_sha256'], 'Prefix binding')
    original = provenance['original_raw_text']
    original_native = provenance['original_raw_return']['requests'][0]['outputs'][0]
    require(original_native['text'] == original, 'Original raw text differs')
    require(sha256(original.encode()) == provenance['output_sha256'], 'Original output hash')
    require(original.encode()[:75] == prefix, 'Training prefix not exact source bytes')
    require(provenance['source_pair']['transfer']['candidate'] == panel['t02']['candidate'],
            'Selected source board differs')
    require(preflight['continuation_present'] is False and preflight['eos_appended'] is False,
            'Unexpected continuation or EOS')
    partition = preflight['partition']
    require(''.join(token['text'] for token in partition).encode() == prefix, 'Partition text')
    require(partition[-1]['end_byte'] == 75, 'Boundary byte offset')
    require(original_native['token_ids'][:29] == [token['token_id'] for token in partition[:29]]
            and original_native['token_ids'][29] != partition[-1]['token_id'],
            'Standalone prefix token boundary differs from expected capture')
    original_check = literal_check(original, panel['t02']['candidate'])
    trained = original_check['fields']
    training = {}
    for arm in ('full', 'syntax'):
        corpus = load(PREP + '/' + arm + '.corpus.json')
        spans = corpus['corpus'][0]['spans']
        proof = preflight['proof'][arm]
        manifest_path = RUN + '/fit_' + arm + '/train_manifest.json'
        manifest = load(manifest_path)
        meta = load(RUN + '/fit_' + arm + '/train_meta.json')
        receipt = load(RUN + '/fit_' + arm + '/fit_receipt.json')
        command = load(RUN + '/fit_' + arm + '.command.json')
        require(len(corpus['corpus']) == 1 and corpus['unique_experiences'] == 1,
                'Unexpected training experiences')
        require(''.join(span[0] for span in spans[1:]).encode() == prefix, 'Corpus prefix')
        selected_request = next(request for request in preflight['evaluation_requests']
                                if request['case_id'] == 't02')
        require(spans[0][0] == selected_request['rendered_prompt']
                and proof['input_ids'][:234] == selected_request['prompt_token_ids'], 'Training context')
        require([span[1] for span in spans[1:]] == [token[arm] for token in partition], 'Span mask')
        require(proof['input_ids'][-30:] == [token['token_id'] for token in partition], 'Target IDs')
        expected_labels = [-100] * 234 + [token['token_id'] if token[arm] else -100
                                         for token in partition]
        require(proof['labels'] == expected_labels, 'Label mask differs')
        supervised = sum(label != -100 for label in proof['labels'])
        require(len(proof['input_ids']) == proof['input_tokens'] == 264, 'Input token count')
        require(supervised == proof['supervised_tokens'] == receipt['supervised_tokens_per_presentation'],
                'Supervised label count')
        require(manifest['steps'] == meta['steps'] == receipt['steps'] == 32, 'Training step count')
        require(manifest['epochs_run'] == corpus['explicit_presentations'] == 32, 'Presentation count')
        require(manifest['train_tokens_seen'] == meta['tokens'] == receipt['input_tokens'] == 8448,
                'Training input count')
        require(receipt == completed['fits'][arm] and receipt['manifest_sha256'] == files[manifest_path],
                'Fit receipt binding')
        require(command['config'] == manifest['config'] and command['fresh_base'] is True,
                'Command/manifest configuration differs')
        require(command['corpus_sha256'] == manifest['corpus']['sha256']
                == files[PREP + '/' + arm + '.corpus.json'], 'Corpus hash binding')
        require(all(flag in command['argv'] for flag in ('--no-eos', '--no-pack', '--no-shuffle-groups')),
                'Expected training flags absent')
        require(manifest['config']['add_eos'] is False and manifest['config']['pack'] is False,
                'Unexpected training configuration')
        training[arm] = {
            'input_tokens_per_presentation': 264, 'supervised_labels_per_presentation': supervised,
            'steps': 32, 'input_tokens_seen': 8448, 'supervised_labels_over_presentations': 32 * supervised,
            'captured_train_meta': meta, 'captured_actual_config': manifest['config'],
            'captured_truncation': manifest['truncation'],
            'isolation_check': manifest['packing']['isolation_check'],
            'fresh_base_asserted_in_command': command['fresh_base'],
        }
    require(preflight['proof']['full']['input_ids'] == preflight['proof']['syntax']['input_ids'],
            'Full and syntax input IDs differ')
    summaries = {}
    records = []
    prepared_requests = {request['case_id']: request for request in preflight['evaluation_requests']}
    for arm in ARMS:
        relative = RUN + '/' + arm + '/generations.jsonl'
        events = [json.loads(line) for line in (SOURCE / relative).read_bytes().splitlines()]
        event_counts = dict(Counter(event['kind'] for event in events))
        require(event_counts == {'request': 8, 'raw_return': 8, 'output': 8}, 'Event counts differ')
        indexed = {kind: {event['request_index']: event for event in events if event['kind'] == kind}
                   for kind in ('request', 'raw_return', 'output')}
        require(all(set(bucket) == set(range(8)) for bucket in indexed.values()), 'Request index mismatch')
        result = load(RUN + '/' + arm + '/results.json')
        runtime = load(RUN + '/' + arm + '/runtime.json')
        require(result['records'] == completed['reads'][arm]['records'], 'Completed records differ')
        require(result['counts'] == completed['reads'][arm]['counts'], 'Completed scores differ')
        require(result['preparation_sha256'] == prep_hash, 'Result preparation binding')
        require(result['generation_calls'] == 8 and result['synthetic'] is False, 'Result capture count')
        identity = result['identity']
        if arm == 'off':
            require(identity['adapter_input'] is None and identity['adapter_files'] == {}, 'OFF adapter')
        else:
            require(identity['adapter_input'].endswith('/fit_' + arm), 'ON adapter input')
            require(identity['adapter_files'] == completed['fits'][arm]['adapter_files'], 'ON adapter pins')
        arm_records = []
        for index in range(8):
            request = indexed['request'][index]
            raw = indexed['raw_return'][index]
            output = indexed['output'][index]
            case_id = request['case_id']
            require(case_id == f't{index + 1:02}', 'Case order differs')
            require(request['source_identity'] == identity, 'Per-request loader identity differs')
            require(all(request[key] == value for key, value in prepared_requests[case_id].items()),
                    'Prepared/native request differs')
            require(request['temperature'] == 0.0 and request['max_tokens'] == 128
                    and request['seed'] == 7101, 'Actual request settings differ')
            require(sha256(request['prompt'].encode()) == request['prompt_sha256'], 'Prompt hash')
            require(sha256(request['rendered_prompt'].encode()) == request['rendered_sha256'], 'Rendered hash')
            require(raw['synthetic'] is False and len(raw['requests']) == 1, 'Native raw request count')
            captured_request = raw['requests'][0]
            require(captured_request['finished'] is True and len(captured_request['outputs']) == 1,
                    'Native output count/finish differs')
            captured = captured_request['outputs'][0]
            require(captured_request['prompt'] == request['rendered_prompt'], 'Native prompt text differs')
            require(captured_request['prompt_token_ids'] == request['prompt_token_ids'], 'Prompt IDs differ')
            require(captured['text'] == output['text'], 'Output text changed from native return')
            require(output['actual_prompt_tokens'] == len(captured_request['prompt_token_ids']) == 234,
                    'Prompt token count differs')
            require(output['actual_output_tokens'] == len(captured['token_ids']), 'Output token count differs')
            require(output['finish_reason'] == captured['finish_reason'] == 'stop', 'Finish reason differs')
            require(output['stop_reason'] == captured['stop_reason'] is None, 'Stop reason differs')
            require(output['output_rewritten'] is False and output['input_truncated'] is False,
                    'Rewrite/truncation flag differs')
            require(output['usage_source'] == 'NATIVE_VLLM_TOKEN_IDS', 'Usage attribution differs')
            payload = output['text'].encode()
            require(sha256(payload) == output['output_sha256'], 'Output byte hash differs')
            primary = result['records'][index]
            require(primary['case_id'] == case_id and primary['capture']
                    == {key: value for key, value in output.items() if key != 'kind'}, 'Reduction differs')
            board_text = request['prompt'].split('\nCandidate:\n', 1)[1]
            board = [[int(value) for value in line.split()] for line in board_text.splitlines()]
            require(board == panel[case_id]['candidate'], 'Actual displayed board differs from panel')
            require(sha256((json.dumps(board) + '\n').encode()) == panel[case_id]['candidate_sha256'],
                    'Candidate board hash differs')
            literal = literal_check(output['text'], board)
            fields = literal.get('fields', {})
            geometry = literal['well_shaped_literal_check'] and fields['group'] == trained['group'] \
                and fields['cells'] == trained['cells']
            item = {
                'arm': arm, 'case_id': case_id, 'raw_output_text': output['text'],
                'raw_output_sha256': output['output_sha256'],
                'board_sha256': panel[case_id]['candidate_sha256'],
                'output_tokens': len(captured['token_ids']), 'last_output_token_id': captured['token_ids'][-1],
                'raw_first_75_bytes_text': payload[:75].decode(),
                'raw_first_75_bytes_sha256': sha256(payload[:75]),
                'source_prefix_lcp_bytes': prefix_length(payload, prefix),
                'exact_source_75byte_prefix': payload.startswith(prefix),
                'bytes_15_to_75_equal_source': payload[15:75] == prefix[15:75],
                'exact_trained_group_and_ordered_cells': geometry,
                'exact_trained_check_including_digit': geometry and fields['digit'] == trained['digit'],
                'ends_malformed_suffix': payload.endswith(b'][]}'),
                'bytes_after_offset_75': payload[75:].decode(),
                'literal_check_posthoc_only': literal,
                'captured_primary_score_unchanged': primary['score'],
            }
            arm_records.append(item)
        prompt_total = sum(indexed['output'][index]['actual_prompt_tokens'] for index in range(8))
        token_total = sum(item['output_tokens'] for item in arm_records)
        require(prompt_total == completed['reads'][arm]['actual_prompt_tokens'], 'Prompt aggregate')
        require(token_total == completed['reads'][arm]['actual_output_tokens'], 'Output aggregate')
        for partition_name, counts in result['counts'].items():
            subset = [item for item in arm_records if partition_name == 'all8'
                      or (partition_name == 't02' and item['case_id'] == 't02')
                      or (partition_name == 'other7_exposed_development' and item['case_id'] != 't02')]
            require(len(subset) == counts['denominator'], 'Score denominator differs')
            for key, value in counts.items():
                if key != 'denominator':
                    require(sum(item['captured_primary_score_unchanged'][key] for item in subset) == value,
                            'Captured score aggregation differs')
        def count(field):
            return sum(item[field] for item in arm_records)
        literals = [item['literal_check_posthoc_only'] for item in arm_records]
        summaries[arm] = {
            'captured_primary_counts_unchanged': result['counts'], 'event_counts': event_counts,
            'actual_prompt_tokens': prompt_total, 'actual_output_tokens': token_total,
            'output_tokens_per_case': [item['output_tokens'] for item in arm_records],
            'terminal_token_ids': sorted({item['last_output_token_id'] for item in arm_records}),
            'exact_trained_geometry': count('exact_trained_group_and_ordered_cells'),
            'exact_trained_check_including_digit': count('exact_trained_check_including_digit'),
            'exact_source_75byte_prefix': count('exact_source_75byte_prefix'),
            'bytes_15_to_75_equal_source': count('bytes_15_to_75_equal_source'),
            'source_prefix_lcp_bytes_per_case': [item['source_prefix_lcp_bytes'] for item in arm_records],
            'malformed_suffix_count': count('ends_malformed_suffix'),
            'well_shaped_literal_checks': sum(item['well_shaped_literal_check'] for item in literals),
            'literal_true_case_ids': [item['case_id'] for item in arm_records
                                      if item['literal_check_posthoc_only']['literal_witness_true']],
            'same_declared_group': sum(item.get('same_declared_group', False) for item in literals),
            'both_values_equal_declared_digit': sum(item.get('both_values_equal_declared_digit', False)
                                                    for item in literals),
            'digit_matches_first_cell': sum(item.get('digit_matches_first_cell', False) for item in literals),
            'literal_geometry_histogram': dict(Counter(compact({'group': item['fields']['group'],
                'cells': item['fields']['cells']}) for item in literals if item['well_shaped_literal_check'])),
            'captured_loader_identity': identity,
            'runtime_backend_settings_snapshot': runtime['backend_settings'],
        }
        require(result['counts']['all8']['format_valid'] == result['counts']['all8']['grounded'] == 0,
                'Primary result differs from requested diagnostic')
        records.extend(arm_records)
    require(completed['calls'] == launch['generation_calls'] == len(records) == 24, 'Total call count')
    off_text = {item['case_id']: item['raw_output_text'] for item in records if item['arm'] == 'off'}
    for arm in ('full', 'syntax'):
        summaries[arm]['raw_outputs_changed_vs_off'] = sum(
            item['raw_output_text'] != off_text[item['case_id']] for item in records if item['arm'] == arm)
    require([summaries[arm]['exact_trained_geometry'] for arm in ARMS] == [0, 8, 1], 'Geometry regression')
    require([summaries[arm]['literal_true_case_ids'] for arm in ARMS] == [[], ['t02'], []], 'Witness regression')
    require(inventory() == files, 'Source changed during audit')
    return {
        'schema': 'posthoc-literal-content-audit-v1', 'date': '2026-09-12',
        'scope': 'Read-only captured-content diagnosis; not success, requalification, or new training approval.',
        'source_root': str(SOURCE), 'source_tree_sha256': tree_digest,
        'source_tree_hash_encoding': 'SHA256(UTF-8 sorted compact JSON mapping relative file path to byte SHA256)',
        'source_file_sha256': files, 'script_sha256': sha256(Path(__file__).read_bytes()),
        'verification': {'self_tests': 'PASS', 'present_manifest_entries_checked': manifests_checked,
                         'native_event_counts_and_reductions_match_captures': True,
                         'source_unchanged_during_read': True, 'weights_loaded': False,
                         'repo_access': False, 'network_used': False, 'gpu_used': False},
        'native_assertions_attributed_not_rerun': {key: value for key, value in native.items()
                                                  if key not in ('xml', 'gpu')},
        'excluded_adapter_weights': omitted,
        'verification_limitations': [
            'NATIVE status, source/model/actual-adapter verification and release are assertions of the captured terminal audit, not rerun here.',
            'Base weights, adapter weights, tokenizer files and original upstream raw log are outside this local capture; their reported hashes are not fresh byte verification.',
            'Captured source-code pins, remote paths, GPU state, model origin and upstream authorship are not independently authenticated by this audit.',
            'Runtime backend_settings.adapter is null in all arms; actual captured request/result adapter_input and adapter_files identify full/syntax. Neither snapshot is a fresh weight test.',
        ],
        'boundary_unchanged': completed['boundary'],
        'training': training,
        'source_prefix': {
            'text': prefix.decode(), 'bytes': 75, 'sha256': sha256(prefix), 'target_token_count': 30,
            'same_264_input_ids_both_arms': True, 'case_id_masked_both_arms': True,
            'syntax_masks_group_four_coordinate_components_and_digit': True,
            'source_raw_text': original, 'source_raw_text_sha256': provenance['output_sha256'],
            'source_continuation_excluded_from_training': original.encode()[75:].decode(),
            'last_partition_token': partition[-1], 'eos_appended': False,
            'source_vs_standalone_prefix_token_boundary': {
                'first_29_token_ids_equal': True,
                'source_token_ids_at_offset_29': original_native['token_ids'][29:33],
                'standalone_prefix_token_id_at_offset_29': partition[-1]['token_id'],
                'conclusion': 'Exact source byte prefix is not an exact source token-ID prefix; standalone cutoff changes the boundary token. No absent tokenizer was loaded to decode source tokens.',
            },
            'original_literal_check_posthoc_only': original_check,
            'original_request_temperature': provenance['original_request']['temperature'],
            'original_request_prompt_tokens': provenance['original_request']['prompt_tokens'],
            'original_prompt_differs_from_current_training_prompt': provenance['original_request']['rendered_prompt']
            != load(PREP + '/full.corpus.json')['corpus'][0]['spans'][0][0],
            'source_prefix_boundary_observation': 'Source bytes [0,75) stop after the checks list, before the comma, lesson field and closing outer brace. Both ON outputs instead append []} at byte 75; no continuation/EOS target constrains that boundary.',
        },
        'actual_generation_settings_from_captured_requests': {'temperature': 0.0, 'seed': 7101,
            'max_tokens': 128, 'prompt_tokens_each': 234, 'all_finish_reason': 'stop',
            'all_stop_reason': None, 'all_output_rewritten': False, 'all_input_truncated': False,
            'loader_defaults_not_request_settings': {'temperature': 0.7, 'max_tokens': 400}},
        'method': {
            'literal_extraction': 'Decode the already-present first check object substring with duplicate keys preserved. Never close/repair the outer record, merge duplicate cells keys, change coordinates/digit/group, or reinterpret the cited group.',
            'literal_truth': 'Two distinct integer one-based in-bounds coordinates in the named row/column/2x2 box, both actual displayed candidate values equal the literal digit.',
            'geometry': 'Exact group plus ordered coordinate pair; excludes digit and case_id.',
            'prefix': 'Raw UTF-8 bytes: exact source prefix and longest common prefix. bytes_15_to_75_equal_source compares a separate fixed slice after the case_id value, omitting bytes [0,15); outputs are never rewritten.',
            'strict_scores': 'Copied unchanged and sums verified against native captures/COMPLETED; literal truth is posthoc content annotation only.',
        },
        'arms': summaries, 'records': records,
        'interpretation': [
            'No qualified utility: all three strict format/grounded/whole-record counts remain zero. This does not establish no learning: both reloaded ON arms visibly change raw output structure, and full concentrates on the trained geometry.',
            'Full shows citation-template/geometry copying, not demonstrated duplicate-finding transfer; its sole true embedded witness is the selected training case t02. Both arms have zero true literal witnesses on the other seven exposed development cases.',
            'Syntax produces varied coordinates, but equal values alone do not make its declared box witness true; four digit-matching pairs cross box boundaries, and t03 names the wrong digit for a same-box pair.',
            'Incomplete-prefix training versus complete-record evaluation is a plausible output-contract limitation, not a demonstrated sole cause. It does not excuse false witnesses, repair outputs, or change primary scores.',
            'Observed changes are compatible with adapter learning/copying, not evidence of generalization, clean ancestry, internalization, P1, or semantically grounded prose lessons. Syntax saw the same values under teacher forcing and had fewer supervised labels.',
        ],
        'recommendation': 'Prefer the next selected RuleGame complete concrete record path, with its existing authorization/provenance/control gates, rather than another unchanged-prompt or seed hunt. A prospective output contract should cover the complete intended record and its ending; preserve these failures separately. This audit implements no path, proposes no new GPU diagnostic, and grants no new training approval.',
    }


def markdown(report, json_hash):
    lines = [
        '# Posthoc terminal citation-sleep content audit — 2026-09-12', '',
        '**Content diagnosis only — not success or requalification. Outputs and primary scores are unchanged.**', '',
        '## Unchanged primary result and observed pattern', '',
        '| Arm | Strict format / grounded | Exact trained geometry | Exact 75-byte source prefix | True literal witness | Output tokens |',
        '|---|---|---:|---:|---|---|',
    ]
    for arm in ARMS:
        summary = report['arms'][arm]
        primary = summary['captured_primary_counts_unchanged']['all8']
        witnesses = ', '.join(summary['literal_true_case_ids']) or 'none'
        lines.append(f"| {arm.upper()} | {primary['format_valid']}/8 / {primary['grounded']}/8 | "
                     f"{summary['exact_trained_geometry']}/8 | {summary['exact_source_75byte_prefix']}/8 | "
                     f"{witnesses} | {summary['output_tokens_per_case']} = {summary['actual_output_tokens']} |")
    lines.extend([
        '', 'Whole-record-clean, valid-citation and invalid-citation primary counts are also zero in every arm: schema rejection prevented citation scoring. The posthoc annotation is not a replacement score.', '',
        '- FULL repeats `box [[3,3],[3,4]]` in 8/8, but only t02 has matching values and digit. Digits in case order: **3,1,4,1,4,1,2,4**; 7/8 match the first cited cell, with t04 instead matching the second. This is not invariant copying of digit 1.',
        '- SYNTAX repeats that geometry in 1/8 (t06). Its other geometries are `[[2,2],[3,3]]` ×5, `[[3,3],[4,3]]` ×1, `[[3,3],[4,1]]` ×1, `[[2,2],[3,1]]` ×1; all declare box. None is a true literal witness.',
        '- OFF has zero well-shaped two-coordinate literal checks: t01/t03 repeat the `cells` key; the other six supply one flat coordinate. No duplicate keys are merged into a pair. t02/t07 also have malformed lesson placement.',
        '- Both ON arms change all 8 raw outputs versus OFF and emit a well-shaped **inner check** in 8/8 but a malformed **whole record** in 8/8: final suffix `][]}`, with `[]}` beginning at zero-based byte 75. Neither ON arm emits a lesson field.',
        '', '## Literal facts on the actual displayed boards', '',
        'Only the already-present inner JSON object is decoded. Coordinates, declared group and digit are not repaired or reinterpreted; no outer brace is added. Values below come from the captured request board, matched to the panel and its hash.', '',
        '| Arm/case | Literal cells (group always box) | Digit | Board values | Same box? | Literal witness true? |',
        '|---|---|---:|---|---|---|',
    ])
    for item in report['records']:
        if item['arm'] == 'off':
            continue
        literal = item['literal_check_posthoc_only']
        fields = literal['fields']
        lines.append(f"| {item['arm']}/{item['case_id']} | {compact(fields['cells'])} | {fields['digit']} | "
                     f"{compact(literal['actual_board_values'])} | {'yes' if literal['same_declared_group'] else 'no'} | "
                     f"{'yes (posthoc only)' if literal['literal_witness_true'] else 'no'} |")
    lines.extend([
        '', 'SYNTAX t01/t02/t05/t07 name two values equal to their digit, but across different boxes. t03 cites a genuine same-box pair of 4s while declaring 3; changing the digit would be a repair and is not done. FULL t02 is the sole literal positive; the other seven cases are exposed development, not holdout.', '',
        '## Exact source-prefix/target boundary', '',
        'Training target, exactly 75 UTF-8 bytes:', '',
        '```text', report['source_prefix']['text'], '```', '',
        'The source response continued with:', '',
        '```text', report['source_prefix']['source_continuation_excluded_from_training'], '```', '',
        'That continuation, the lesson and the closing outer brace are absent from training; EOS is not appended. The 30-token target ends at `}]` (token 25439), closing the check and checks list but not the record. The current prompt still requires case_id/checks/lesson. All ON records reach the malformed continuation at byte 75, not the 128-token generation budget.', '',
        'The byte-exact cutoff is **not a token-ID-exact source prefix**: the first 29 IDs agree, then the standalone target uses 25439, whereas the captured source continues with IDs `[92,28503,27495,3252]`. This further localizes a boundary difference without decoding unavailable tokenizer files or proving causality.', '',
        '- **Raw byte comparison:** FULL source-prefix LCP in t01…t08 order is `[14,75,14,14,14,14,14,14]`; SYNTAX is `[14,52,14,14,14,14,14,14]`. OFF differs at byte 11 in all eight. Case-id differences are not silently normalized.',
        '- Comparing source bytes `[15,75)` (the slice after the case-id value; bytes `[0,15)` omitted) gives FULL 3/8 and SYNTAX 1/8 exact matches, including the digit. This is explicitly a substring comparison, not output rewriting or complete-record success.',
        '- The selected original t02 inner citation is literally true, but its prose reminder has **no semantic grounding claim**. Its source request had 332 prompt tokens and temperature 0.7; current requests have 234 and 0.0. Do not treat the selected earlier response as a matched current baseline.', '',
        '## Captured training and native settings', '',
        '- Both views have identical **264 input IDs** and the same teacher-forced content; one experience, 32 presentations/steps, 8,448 input tokens each. FULL: 27 supervised labels/presentation (864 total); SYNTAX: 21 (672 total). Both mask case_id; syntax additionally masks group, four coordinate components and digit. Not supervised-dose matched; not content withheld.',
        '- Command and train-manifest settings agree: fresh-base asserted; rank 8, alpha 16, dropout 0.05, lr 1e-4, AdamW, bf16, seed 1729; `--no-eos --no-pack --no-shuffle-groups`, max length 4096, all seven projection modules/all layers. No recorded truncation. Isolation check is recorded as not run (one-item, no packing), not passed.',
        '- Recounted **24 request + 24 raw-return + 24 output events**, one native completion each, matching per-case reductions and COMPLETED. Requests actually specify **temperature 0.0, seed 7101, max_tokens 128**, overriding loader defaults 0.7/400. OFF outputs total 367 tokens; each ON arm 256; **879 total**, 5,616 prompt tokens.',
        '- Every capture finishes `stop`, stop_reason null, rewrite/truncation flags false. Both ON arms are 32 output IDs/case, ending in token ID 151645; no retokenization or fresh generation was performed.',
        '- Request/result identities bind FULL and SYNTAX to their distinct fit adapter hashes; OFF has no adapter. The generic runtime snapshot has `adapter: null` in all arms and must not be mistaken for their actual per-request loader identities.', '',
        '**NATIVE caption — attributed, not rerun:** the captured terminal audit says `NATIVE_CITATION_SLEEP_REPLAY_AND_RELEASE_PASS`, native reduction equal, source/model/actual adapters verified and released. Here only archived bytes, manifest chains and raw-event reductions were checked. Weights (both adapters and base), tokenizer, upstream log, remote state and GPU release were not independently rerun/authenticated; adapter weights are excluded from this capture.', '',
        '## Interpretation and next direction', '',
        'There is **no qualified utility**, not evidence of **no learning**. Reloaded ON outputs visibly change structure; FULL strongly concentrates on trained geometry, while literal transfer remains absent. An incomplete-prefix objective against a complete-record contract is a plausible limitation, **not a proven sole cause** and not an excuse for false citations. Equal inputs with different masks/doses and one selected exposed experience do not establish generalization, internalization, clean ancestry or P1.', '',
        report['recommendation'], '',
        '## Reproduction and exact bindings', '',
        '`python3 -B /tmp/astra_citation_sleep_content_audit_20260912.py`', '',
        'The standalone standard-library script writes only its named sibling `.json` and `.md`, runs local logic self-checks, and requires the pinned 56-file source tree. It never accesses the repo, network, git, GPU or model weights. JSON includes all 24 verbatim outputs, first-75-byte hashes, literal byte spans, unchanged scores and the complete source-file hash map.', '',
        f"- Source-tree SHA256: `{report['source_tree_sha256']}` (sorted compact JSON map of relative path → byte SHA256).",
        f"- Prefix SHA256: `{report['source_prefix']['sha256']}`.",
        f"- COMPLETED SHA256: `{report['source_file_sha256'][RUN + '/COMPLETED.json']}`.",
        f"- Terminal-audit SHA256: `{report['source_file_sha256'][LAUNCH + '/MAIN_TERMINAL_AUDIT.json']}`.",
        f"- Script SHA256: `{report['script_sha256']}`.",
        f'- JSON SHA256: `{json_hash}`.',
        '',
    ])
    return '\n'.join(lines)


def main():
    report = audit()
    json_bytes = ('{\n' + ',\n'.join('  ' + json.dumps(key) + ': ' + compact(report[key])
                                    for key in sorted(report)) + '\n}\n').encode()
    text = markdown(report, sha256(json_bytes))
    for suffix in ('.json', '.md'):
        require(not OUTPUT.with_suffix(suffix).is_symlink(), 'Refusing output symlink')
    OUTPUT.with_suffix('.json').write_bytes(json_bytes)
    OUTPUT.with_suffix('.md').write_text(text, encoding='utf-8')
    print(compact({'status': 'POSTHOC_CONTENT_AUDIT_PASS_NOT_REQUALIFICATION',
                   'source_tree_sha256': report['source_tree_sha256'],
                   'json_sha256': sha256(json_bytes), 'md_sha256': sha256(text.encode()),
                   'geometry_counts': {arm: report['arms'][arm]['exact_trained_geometry'] for arm in ARMS},
                   'literal_true_case_ids': {arm: report['arms'][arm]['literal_true_case_ids'] for arm in ARMS}}))


if __name__ == '__main__':
    main()
