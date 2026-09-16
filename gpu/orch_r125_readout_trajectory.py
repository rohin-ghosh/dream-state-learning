"""Read-only CPU reduction of retained R125 fresh-process readout directories.

Use --checkpoint0 DIR and repeat --readout DIR for subsequent checkpoints.
Raw-free JSON goes to stdout only; --compact omits per-output diagnostic rows.
Original node-local plan/checkpoint paths are provenance,
not files to open: this works on copied receipts without models, journals or RNG.
Hashes detect corruption, not forgery; runtime isolation and weight immutability
remain runner attestations. This adds diagnostics, not a new scientific gate.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from gpu.orch_r125_continual_readout import MAX_NEW_TOKENS, SCHEMA as READOUT_SCHEMA, SUITE_SHA256
from organism_v6 import orch_r107_capability as policy
from organism_v6.orch_r125_plain_context import MARKERS


SCHEMA = 'R125_READOUT_TRAJECTORY_V1'
JOURNAL_MARKERS = MARKERS + ('[cost]', '[budget]',
    'History omission notice (not a child assertion)')
DECODER = dict(do_sample=False, num_beams=1, repetition_penalty=1.0)
PROVENANCE = ('schema', 'pid', 'ppid', 'process', 'host_sha256', 'plan_path',
    'plan_sha256', 'checkpoint_path', 'checkpoint_commit_sha256', 'checkpoint_sha256',
    'adapter_state_sha256', 'optimizer_steps', 'base_sha256', 'suite_sha256', 'source',
    'output_path', 'gpu_uuid', 'max_new_tokens', 'decoder', 'parent_present',
    'history_present', 'train_ingestion', 'training_updates', 'raw_reasoning_preserved')
require = policy.require


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_JSON_key:' + key)
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('nonfinite_JSON:' + value)


def _read(path):
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite)
        require(isinstance(value, dict), 'JSON_object_required')
        return value, hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError) as error:
        raise ValueError(f'{path}: {error}') from error


def _same(actual, expected, reason):
    require(policy.digest(actual) == policy.digest(expected), reason)


def _hash(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None,
        'SHA256_required')


def _provenance(record, expected):
    require(all(key in record for key in PROVENANCE), 'missing_provenance')
    _same({key: record[key] for key in PROVENANCE}, expected, 'provenance_mismatch')


def _repetition(sequence):
    grams = [tuple(sequence[index:index + 4]) for index in range(max(0, len(sequence) - 3))]
    repeated = len(grams) - len(set(grams))
    return dict(windows=len(grams), repeated_windows=repeated,
        fraction=repeated / len(grams) if grams else 0.0)


def _metrics(record, file_sha256):
    response, capture = record['response'], record['capture']
    raw = response['raw']
    markers = {marker: raw.count(marker) for marker in JOURNAL_MARKERS}
    return dict(task_id=record['task_id'], family=record['family'], arm=record['arm'],
        source_sha256=file_sha256, response_sha256=capture['response_sha256'],
        raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        token_ids_sha256=policy.digest(response['token_ids']),
        task_sha256=capture['task_sha256'], prompt_sha256=capture['prompt_sha256'],
        raw=raw, generated_tokens=len(response['token_ids']),
        completion=capture['result']['completion'], cap_hit=response['truncated'],
        fixed_task_pass=capture['result']['passed'] if response['terminal'] else None,
        repeated_token_4gram=_repetition(response['token_ids']),
        repeated_whitespace_4gram=_repetition(raw.split()),
        journal_marker_counts=markers, journal_marker_present=any(markers.values()))


def _panel(path):
    directory = Path(path).resolve(strict=True)
    require(directory.is_dir(), 'readout_directory_required')
    require(not (directory / 'FAILED.json').exists(), 'failed_panel')
    sources = {}

    def read(name):
        record, sources[name] = _read(directory / name)
        return record

    request = read('REQUEST.json')
    require(all(key in request for key in PROVENANCE), 'missing_provenance')
    provenance = {key: request[key] for key in PROVENANCE}
    for key in ('host_sha256', 'plan_sha256', 'checkpoint_commit_sha256',
            'adapter_state_sha256', 'base_sha256', 'suite_sha256'):
        _hash(request[key])
    checkpoint_hashes = request['checkpoint_sha256']
    require(isinstance(checkpoint_hashes, dict)
        and set(checkpoint_hashes) == {'adapter', 'optimizer', 'rng'}, 'checkpoint_hashes')
    for value in checkpoint_hashes.values():
        _hash(value)
    require(checkpoint_hashes['optimizer'] == checkpoint_hashes['rng'], 'optimizer_RNG_binding')
    for key in ('pid', 'ppid', 'optimizer_steps'):
        require(type(request[key]) is int and request[key] >= 0, 'invalid_' + key)
    process = request['process']
    require(isinstance(process, list) and len(process) == 3
        and isinstance(process[0], str) and bool(process[0])
        and type(process[1]) is int and process[1] == request['pid'] > 0
        and type(process[2]) is int and process[2] >= 0, 'process_identity')
    for key in ('plan_path', 'checkpoint_path', 'output_path'):
        require(isinstance(request[key], str) and Path(request[key]).is_absolute(), 'absolute_' + key)
    checkpoint = Path(request['checkpoint_path'])
    require(checkpoint.name == 'COMMIT.json' and checkpoint.parent.parent.name == 'checkpoints',
        'checkpoint_path')
    root = checkpoint.parent.parent.parent
    original_output = Path(request['output_path'])
    require(original_output != root / 'readouts' and original_output.is_relative_to(root / 'readouts')
        and '..' not in original_output.parts and '..' not in checkpoint.parts, 'output_path')
    require(isinstance(request['gpu_uuid'], str) and request['gpu_uuid'].startswith('GPU-'), 'gpu_uuid')
    fixed = dict(schema=READOUT_SCHEMA, suite_sha256=SUITE_SHA256, source=policy.SOURCE,
        base_sha256=policy.BASE_SHA256, max_new_tokens=MAX_NEW_TOKENS, decoder=DECODER,
        parent_present=False, history_present=False, train_ingestion=False,
        training_updates=0, raw_reasoning_preserved=True)
    _same({key: request[key] for key in fixed}, fixed, 'fixed_readout_configuration')
    complete = read('COMPLETE.json')
    _provenance(complete, provenance)
    require(complete.get('status') == 'COMPLETE' and complete.get('before_after_verified') is True,
        'completed_verified_panel_required')
    require(type(complete.get('calls')) is int and complete['calls'] == 64
        and type(complete.get('task_count')) is int and complete['task_count'] == 32, 'all64_cells_required')
    snapshot = dict(adapter_state_sha256=request['adapter_state_sha256'],
        base_sha256=request['base_sha256'], frozen_base_verified=True,
        checkpoint_files_verified=True, gpu_uuid=request['gpu_uuid'], readonly=True,
        status='PASS', pid=request['pid'])
    for name in ('BEFORE.json', 'AFTER.json'):
        observed = read(name)
        _same({key: observed.get(key) for key in snapshot}, snapshot, 'snapshot_attestation_mismatch')
        if name == 'AFTER.json':
            require(observed.get('unchanged') is True, 'changed_after_snapshot')
    names = {f'CALL_{index:03d}.json' for index in range(64)}
    manifest = complete.get('call_files')
    require(isinstance(manifest, dict) and set(manifest) == names, 'exact_call_manifest_required')
    require({item.name for item in directory.glob('CALL_*.json')} == names, 'unexpected_call_files')
    require({item.name for item in (directory / 'reservations').glob('CALL_*.json')} == names,
        'exact_reservations_required')
    records, outputs, configuration = [], [], []
    for position, task in enumerate(policy.tasks()):
        arms = ('ON', 'OFF') if position % 2 == 0 else ('OFF', 'ON')
        for offset, arm in enumerate(arms):
            name = f'CALL_{position * 2 + offset:03d}.json'
            record = read(name)
            _hash(manifest[name])
            require(sources[name] == manifest[name], 'call_source_hash_mismatch:' + name)
            _provenance(record, provenance)
            identity = dict(position=position, task_id=task['id'], family=task['family'],
                arm=arm, condition='LORA_' + arm, messages=policy.messages(task))
            _same({key: record.get(key) for key in identity}, identity, 'call_pair_or_prompt_mismatch')
            require(record.get('status') == 'COMPLETE' and 'error' not in record
                and 'error_type' not in record, 'completed_call_required')
            reservation = read('reservations/' + name)
            _provenance(reservation, provenance)
            _same({key: reservation.get(key) for key in identity}, identity, 'reservation_mismatch')
            require(reservation.get('status') == 'RESERVED'
                and reservation.get('started_unix') == record.get('started_unix'), 'reservation_status_or_time')
            response = record['response']
            require('eos_token_id' in response and response.get('max_new_tokens') == MAX_NEW_TOKENS,
                'fixed_response_decoder_required')
            expected = policy.capture(task, arm, response,
                checkpoint_sha256=request['adapter_state_sha256'], base_sha256=request['base_sha256'],
                lora_enabled=arm == 'ON')
            _same(record['capture'], expected, 'capture_hash_or_outcome_mismatch')
            require(expected['result']['completion'] in ('complete', 'truncated'), 'incomplete_response')
            records.append(expected)
            outputs.append(dict(_metrics(record, sources[name]), source_file=name))
            configuration.append(dict(task_id=task['id'], arm=arm, messages=record['messages'],
                prompt_tokens=response['prompt_tokens'], eos_token_id=response['eos_token_id'],
                context=response.get('context')))
    scores = policy.reduce_paired(records, checkpoint_sha256=request['adapter_state_sha256'],
        base_sha256=request['base_sha256'], max_new_tokens=MAX_NEW_TOKENS)
    require(scores['all_cells_recorded'] and scores['recorded_cells'] == 64, 'recorded_pairs_required')
    _same(complete.get('paired_scores'), scores, 'paired_scores_mismatch')
    return dict(directory=str(directory), provenance=provenance, sources=sources,
        outputs=outputs, configuration=configuration, root=str(root))


def _change(current, reference):
    comparable = current['fixed_task_pass'] is not None and reference['fixed_task_pass'] is not None
    return dict(exact_response_changed=current['raw'] != reference['raw'],
        generated_tokens_delta=current['generated_tokens'] - reference['generated_tokens'],
        cap_hit_delta=int(current['cap_hit']) - int(reference['cap_hit']),
        fixed_task_pass_delta=int(current['fixed_task_pass']) - int(reference['fixed_task_pass'])
            if comparable else None,
        repeated_token_4gram_fraction_delta=current['repeated_token_4gram']['fraction']
            - reference['repeated_token_4gram']['fraction'],
        repeated_whitespace_4gram_fraction_delta=current['repeated_whitespace_4gram']['fraction']
            - reference['repeated_whitespace_4gram']['fraction'],
        journal_marker_present_delta=int(current['journal_marker_present'])
            - int(reference['journal_marker_present']))


def reduce_trajectory(checkpoint0, readouts=()):
    """Validate all supplied panels before returning any diagnostic results.

Checkpoint0 must have zero optimizer steps. Later panels have unique, increasing
steps (input order is irrelevant). No artifact discovery or best-retry selection.
    Valid cap-hitting responses are retained. Missing, failed, malformed and
    unexplained nonterminal outputs are rejected, not scored wrong.
    """
    try:
        require(policy.digest(policy.tasks()) == SUITE_SHA256, 'fixed_synthetic32_suite')
        panels = [_panel(path) for path in (checkpoint0, *readouts)]
        baseline = panels[0]
        require(baseline['provenance']['optimizer_steps'] == 0, 'checkpoint0_zero_steps_required')
        panels.sort(key=lambda panel: panel['provenance']['optimizer_steps'])
        steps = [panel['provenance']['optimizer_steps'] for panel in panels]
        require(len(steps) == len(set(steps)), 'duplicate_checkpoint_steps')
        require(len({panel['provenance']['checkpoint_commit_sha256'] for panel in panels}) == len(panels),
            'duplicate_checkpoint_commit')
        configuration = baseline['configuration']
        reference = {(row['task_id'], row['arm']): row for row in baseline['outputs']}
        for panel in panels:
            require(panel['root'] == baseline['root'], 'different_child_root')
            _same(panel.pop('configuration'), configuration, 'cross_checkpoint_prompt_or_decoder_drift')
            indexed = {(row['task_id'], row['arm']): row for row in panel['outputs']}
            for row in panel['outputs']:
                row['versus_OFF'] = _change(row, indexed[(row['task_id'], 'OFF')])
                row['versus_checkpoint0'] = _change(row, reference[(row['task_id'], row['arm'])])
            panel['arms'] = {}
            for arm in policy.ARMS:
                selected = [row for row in panel['outputs'] if row['arm'] == arm]
                panel['arms'][arm] = dict(outputs=len(selected),
                    generated_tokens=sum(row['generated_tokens'] for row in selected),
                    cap_hit_outputs=sum(row['cap_hit'] for row in selected),
                    fixed_task_scored_outputs=sum(row['fixed_task_pass'] is not None for row in selected),
                    fixed_task_passes=sum(row['fixed_task_pass'] is True for row in selected),
                    journal_marker_outputs=sum(row['journal_marker_present'] for row in selected),
                    journal_marker_output_fraction=sum(row['journal_marker_present'] for row in selected) / len(selected),
                    journal_marker_counts=dict(sum((Counter(row['journal_marker_counts']) for row in selected), Counter())),
                    changes={comparison: dict(exact_response_changes=sum(row[comparison]['exact_response_changed'] for row in selected),
                        generated_tokens_delta=sum(row[comparison]['generated_tokens_delta'] for row in selected),
                        cap_hits_delta=sum(row[comparison]['cap_hit_delta'] for row in selected),
                        fixed_task_comparable_outputs=sum(row[comparison]['fixed_task_pass_delta'] is not None for row in selected),
                        fixed_task_passes_delta=sum(row[comparison]['fixed_task_pass_delta']
                            for row in selected if row[comparison]['fixed_task_pass_delta'] is not None))
                        for comparison in ('versus_OFF', 'versus_checkpoint0')})
                for metric in ('repeated_token_4gram', 'repeated_whitespace_4gram'):
                    windows = sum(row[metric]['windows'] for row in selected)
                    repeated = sum(row[metric]['repeated_windows'] for row in selected)
                    panel['arms'][arm][metric] = dict(windows=windows, repeated_windows=repeated,
                        fraction=repeated / windows if windows else 0.0)
        for panel in panels:
            for row in panel['outputs']:
                del row['raw']
        return dict(schema=SCHEMA, claim_boundary='Descriptive fixed-suite diagnostics only; '
            'not cognition, retention-success, or causal-generalization labels. Runtime properties '
            'are retained attestations, not independently verified by this CPU reducer.',
            definitions=dict(generated_tokens='Length of retained token_ids, including terminal EOS when present.',
                cap_hit='Valid terminal=false, truncated=true response with exactly max_new_tokens token IDs. '
                    'Retained as data, not rejected or labeled failure.',
                fixed_task_scores='Terminal responses only; cap-hit scores and score deltas involving cap hits '
                    'are null. Counts include explicit scored/comparable denominators; other diagnostics use all outputs.',
                exact_response_change='Exact raw string inequality; no normalization.',
                repeated_4gram_fraction='(windows - unique windows) / windows; zero for fewer than four items. '
                    'Token IDs include EOS; whitespace items use raw.split().',
                journal_markers='Case-sensitive literal substring occurrences in raw output only.',
                checkpoint0_comparison='Same task and same arm at the explicit zero-step checkpoint.',
                source_hashes='SHA256 of retained receipt bytes; response/task/prompt hashes use the existing policy digest. '
                    'Original node-local paths are not dereferenced.'),
            journal_markers=list(JOURNAL_MARKERS), checkpoints=panels)
    except (KeyError, TypeError, OSError) as error:
        raise ValueError(f'malformed_or_missing_readout_evidence: {error}') from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint0', type=Path, required=True)
    parser.add_argument('--readout', type=Path, action='append', default=[])
    parser.add_argument('--compact', action='store_true',
        help='Emit raw-free checkpoint summaries and source hashes without per-output rows.')
    options = parser.parse_args(argv)
    try:
        report = reduce_trajectory(options.checkpoint0, options.readout)
    except ValueError as error:
        parser.error(str(error))
    if options.compact:
        for panel in report['checkpoints']:
            del panel['outputs']
    print(json.dumps(report, sort_keys=True, indent=None if options.compact else 2, allow_nan=False))


if __name__ == '__main__':
    main()
