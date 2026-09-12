#!/usr/bin/env -S python3 -B
"""Read captured A1 bank0 results; print JSON; never load a model or write files."""
import sys
sys.dont_write_bytecode = True

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path

FROZEN = Path('/tmp/astra_seed_bank0_evidence_20260912/experiment_code/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d')
CELL = 'F_r16k16'
KEY = 'F_r16k16__across__r8__lam1'
ADAPTER = 'adapters/bank0/F_r16k16/across/sleep4/r8'
CORPUS = 'corpora/bank0/F_r16k16/across/sleep4/corpus.json'
EVAL = 'eval/bank0__F_r16k16__across__sleep4__r8__lam1.json'
SOURCE_HASH = 'ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3'
BASE_EVAL_HASH = '970e1be480133cb81d62b53e9762bd4ef77b5c0b1d11e3a85d21b7e3dab64386'
INPUT_HASHES = {
    CORPUS: 'f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d',
    'manifest.json': 'b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f',
    'distractor.json': '4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc',
    'banks/bank0.json': '87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31',
    'banks/bank1.json': 'b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362',
    'banks/bank2.json': 'a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4',
}
FIT = dict(recipe='memory_dose_v1 (mirrors train_adapter.py v1)', model='Qwen/Qwen2.5-7B-Instruct',
           rank=8, alpha=16, dropout=0.05, epochs=3, bsz=4, max_len=512, seed=2,
           steps=9693, total_steps=9693, n_items=12924, tokens=749985, supervised_tokens=711213,
           boundary_straddles=0, truncated_items=0, measure_only=False, synthetic=True,
           corpus_sha='15adaeff18a685c0', items_sha='55e5bca9dadd19ea', ordering='chronological',
           writer='occurrences', representation='frames', shuffled=False,
           tokenization='joint context+target (encode_item)',
           targets=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def module(relative, expected):
    path = FROZEN / relative
    if digest(path) != expected:
        raise ValueError('frozen source hash mismatch: ' + relative)
    spec = importlib.util.spec_from_file_location('frozen_' + path.stem, path)
    imported = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported)
    return imported


def validate_cues(evaluation, bank):
    rows = evaluation['cues']
    indexed = {row['cue_id']: row for row in rows}
    if len(rows) != 1313 or len(indexed) != 1313:
        raise ValueError('expected 1313 unique cues')
    owners = {owner['id']: owner for owner in bank['owners']}
    if len(owners) != 64 or collections.Counter(owner['dose'] for owner in owners.values()) != {0:16,1:16,4:16,16:16}:
        raise ValueError('owner roster/dose count mismatch')
    expected = {(kind, owner['id']) for owner in owners.values()
                for kind in (['frame'] if owner['dose'] == 0 else ['frame','frame_similar','frame_bicycle'])}
    actual = [(row['kind'], row['owner']) for row in rows if row['kind'] in ('frame','frame_similar','frame_bicycle')]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('missing/duplicate frame controls')
    for row in rows:
        if row['kind'] in ('frame','frame_similar','frame_bicycle'):
            owner = owners[row['owner']]
            if row['a'] != owner['colour'] or row['dose'] != owner['dose'] or row.get('abstain') != [' not']:
                raise ValueError('frame source join mismatch: ' + row['cue_id'])
            if row['kind'] == 'frame_similar' and row.get('cue_id_used') != owner['similar_id']:
                raise ValueError('look-alike ID mismatch: ' + row['cue_id'])
        for side in ('OFF','ON'):
            scores = row[side]
            if set(scores['p_raw']) != set(row['cand_tokens']) or set(scores['logp']) != set(row['cand_tokens']):
                raise ValueError('candidate set mismatch: ' + row['cue_id'])
            values = [*scores['p_raw'].values(), *scores['logp'].values(), scores['mass']]
            if 'abstain' in row:
                values.append(scores['p_abstain'])
                if scores['p_abstain'] < 0:
                    raise ValueError('negative abstention probability')
            if not all(type(value) in (int,float) and math.isfinite(value) for value in values):
                raise ValueError('nonfinite/malformed scores: ' + row['cue_id'])
            if min(scores['p_raw'].values()) < 0 or scores['mass'] < 0:
                raise ValueError('invalid probability/mass: ' + row['cue_id'])
            if row['kind'] in ('frame','frame_similar','frame_bicycle') and (sum(scores['p_raw'].values()) <= 0 or scores['mass'] <= 0):
                raise ValueError('undefined frame probability/mass: ' + row['cue_id'])
    return indexed


def reduce_root(root, label, rate, native, preparation):
    output = dict(label=label, root=str(root), expected_lr=rate, errors=[], warnings=[], hashes={}, metrics=None)
    errors = output['errors']
    check = lambda condition, message: errors.append(message) if not condition else None
    evaluation = None
    try:
        receipt = load(root/'seed_run_receipt.json')
        _, inputs, _, _, metadata = preparation.inspect_source(root, CELL, banks=[0])
        for relative, expected in INPUT_HASHES.items():
            content = inputs[relative]
            actual = hashlib.sha256(content).hexdigest()
            output['hashes'][relative] = actual
            check(actual == expected, 'source hash mismatch: ' + relative)
            check(receipt['inputs'].get(relative) == dict(sha256=actual, bytes=len(content)), 'receipt binding: ' + relative)
        for field, expected in dict(source_bank_seed=1, training_seed=2, base_model=FIT['model'], cell=CELL,
                                    arm='across', sleep=4, clean_lineage_eligible=False,
                                    label='SYNTHETIC_DIAGNOSTIC_NOT_CLEAN_LINEAGE').items():
            check(receipt.get(field) == expected, 'receipt.' + field)
        check(0 in receipt['banks'] and receipt['corpora']['0'] == metadata['0'], 'receipt bank0 corpus metadata')
        fit = load(root/ADAPTER/'train_meta.json')
        evaluation = load(root/EVAL)
        output['hashes']['eval'] = digest(root/EVAL)
        output['hashes']['fit'] = digest(root/ADAPTER/'train_meta.json')
        output['hashes']['receipt'] = digest(root/'seed_run_receipt.json')
        if label == 'baseline':
            check(output['hashes']['eval'] == BASE_EVAL_HASH, 'baseline eval differs from frozen receipt')
            check(output['hashes']['fit'] == 'b046eb082ec8bc488d202e94fc1a09108e35b00d32a45bf2464534a8b5e3493c', 'baseline fit differs from frozen receipt')
        else:
            check(output['hashes']['eval'] != BASE_EVAL_HASH, 'baseline eval copied into treatment slot; not new evidence')
        check((root/ADAPTER/'DONE').read_text().strip() == 'ok', 'missing/non-fit DONE')
        for field, expected in dict(FIT, lr=rate).items():
            check(field in fit and type(fit[field]) is type(expected) and fit[field] == expected, 'fit.' + field)
        check(fit['throughput'].get('grad_checkpoint') is False, 'fit gradient checkpointing')
        output['fit'] = {field:fit.get(field) for field in ('lr','seed','rank','epochs','steps','tokens','supervised_tokens','wall_seconds')}
        expected_meta = dict(cell=CELL, arm='across', sleep=4, rank=8)
        for field, expected in dict(bank=0, model='hf', lam=1.0, n_cues=1313, synthetic=True,
                                    template_check=True, boundary_straddles=512, meta=expected_meta,
                                    tokenization='joint prompt+candidate (joint_candidate_ids)').items():
            check(evaluation.get(field) == expected, 'eval.' + field)
        check(evaluation['abstain_check'].get('ok') is True, 'eval abstain_check')
        remote_adapter = str(Path(receipt['destination_run'])/ADAPTER)
        check(evaluation['adapter'] == evaluation['adapter_arg'] == remote_adapter, 'eval/receipt remote adapter binding')
        check(evaluation['tag'] == 'bank0__F_r16k16__across__sleep4__r8', 'eval tag')
        for field in ('corpus_sha','items_sha','ordering','writer','representation','shuffled','rank','recipe'):
            check(evaluation['adapter_meta'].get(field) == fit[field], 'eval adapter_meta.' + field)
        bank = load(root/'banks/bank0.json')
        validate_cues(evaluation, bank)
        output['rounded_zero_nonframe_scores'] = {
            side: [row['cue_id'] for row in evaluation['cues']
                   if row['kind'] not in ('frame','frame_similar','frame_bicycle')
                   and (sum(row[side]['p_raw'].values()) == 0 or row[side]['mass'] == 0)]
            for side in ('OFF','ON')}
        summary = native.summarize_eval(evaluation, bank)
        gates = native.evaluate_gates(summary, seed=0)
        dose = summary['per_dose'][16]
        output['metrics'] = dict(eval_s=evaluation['seconds'], cues=evaluation['n_cues'],
            acquisition={field:dose[field] for field in ('n','frame_p_off','frame_p_on','frame_d_p','frame_mass_off','frame_mass_on','I_d_frame')},
            G9=gates['G9_frame_binding'], G11=gates['G11_abstention'],
            controls={field:value for field,value in summary['controls'].items() if field.startswith(('frame_spill','abstain_'))},
            frame_dose_curve={dose:summary['per_dose'][dose]['frame_d_p'] for dose in (0,1,4,16)})
        report_path = root/'report/report.json'
        output['report'] = dict(present=report_path.exists())
        if report_path.exists():
            report = load(report_path)
            entry = report['results'][KEY]
            output['hashes']['report'] = digest(report_path)
            output['report'].update(banks=entry['banks'], n_evals=report['n_evals'], compared='per_bank.0.gates.G9_frame_binding', pooled_ignored=len(entry['banks']) > 1)
            check(0 in entry['banks'] and entry['ref_sleep'] == 4, 'report bank0/ref_sleep')
            check(entry['per_bank']['0']['gates']['G9_frame_binding'] == gates['G9_frame_binding'], 'report bank0 G9 mismatch')
            check(report['gates_thresholds']['frame_spill'] == native.GATES['frame_spill'], 'report G9 threshold changed')
            if label != 'baseline':
                check(entry['banks'] == [0] and entry['sleeps'] == [4] and report['n_evals'] == 1, 'treatment report contains extra banks/evals')
            if entry['banks'] == [0]:
                check(entry['frame']['G9_frame_binding'] == gates['G9_frame_binding'], 'report single-bank frame G9 mismatch')
        else:
            output['warnings'].append('native report absent; metrics reduced from raw eval only')
        output['operational'] = {}
        for filename in ('launch_receipt.json','controller_result.json'):
            path = root/'logs'/filename
            if path.exists():
                output['operational'][filename] = load(path)
        output['warnings'].append('controller/cleanup outcome is separate from scientific artifacts; main reconciles reservations')
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ZeroDivisionError) as error:
        errors.append(type(error).__name__ + ': ' + str(error))
    output['valid'] = not errors
    output['metrics_status'] = 'validated_artifact' if output['valid'] else 'invalid_or_incomplete_artifact_do_not_use_as_matched_evidence'
    return output, evaluation


def compare(left, right, labels):
    result = dict(pair=labels, errors=[])
    try:
        first = {row['cue_id']:row for row in left['cues']}
        second = {row['cue_id']:row for row in right['cues']}
        result['missing_ids'] = sorted(first.keys()-second.keys())
        result['extra_ids'] = sorted(second.keys()-first.keys())
        result['cue_order_equal'] = list(first) == list(second)
        fields = ('bank','model','lam','n_cues','meta','template_check','abstain_check','tokenization','boundary_straddles','synthetic','tag','adapter_meta')
        result['eval_metadata_changed'] = [field for field in fields if left.get(field) != right.get(field)]
        changed, off_changed, order_changed = [], [], []
        maximum = {field:0.0 for field in ('p_raw','mass','logp','p_abstain')}
        for identity in first.keys() & second.keys():
            before, after = first[identity], second[identity]
            strip = lambda row: {key:value for key,value in row.items() if key not in ('OFF','ON')}
            if strip(before) != strip(after):
                changed.append(identity)
            if list(before['cand_tokens']) != list(after['cand_tokens']) or any(list(before[side]['p_raw']) != list(after[side]['p_raw']) for side in ('OFF','ON')):
                order_changed.append(identity)
            old, new = before['OFF'], after['OFF']
            if old != new:
                off_changed.append(identity)
            if old.keys() != new.keys():
                result['errors'].append('OFF field-set mismatch: ' + identity)
            for field in maximum:
                if field not in old or field not in new:
                    continue
                if isinstance(old[field],dict):
                    if old[field].keys() != new[field].keys():
                        result['errors'].append('OFF candidate-set mismatch: ' + identity)
                    values = [abs(old[field][key]-new[field][key]) for key in old[field].keys() & new[field].keys()]
                else:
                    values = [abs(old[field]-new[field])]
                maximum[field] = max([maximum[field], *values])
        result.update(cue_metadata_changed_ids=sorted(changed), candidate_order_changed_ids=sorted(order_changed),
                      off_changed_ids=sorted(off_changed), off_changed_count=len(off_changed), off_max_abs=maximum)
        result['cue_metadata_match'] = not any((result['missing_ids'],result['extra_ids'],changed,order_changed,result['eval_metadata_changed'],result['errors']))
        result['off_exact_at_serialized_precision'] = not any((result['missing_ids'],result['extra_ids'],off_changed,result['errors']))
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        result['errors'].append(type(error).__name__ + ': ' + str(error))
        result['cue_metadata_match'] = False
        result['off_exact_at_serialized_precision'] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('low3', type=Path, nargs='?')
    parser.add_argument('low1', type=Path, nargs='?')
    parser.add_argument('--baseline-only', action='store_true', help='validate only historical evidence; not an LR comparison')
    args = parser.parse_args()
    if (args.baseline_only and (args.low3 or args.low1)) or (not args.baseline_only and (not args.low3 or not args.low1)):
        parser.error('supply baseline low3 low1, or baseline --baseline-only')
    native = module('organism_v6/memory_dose.py', SOURCE_HASH)
    preparation = module('gpu/prepare_memory_seed_run.py', '1f216a2ca7392f47cb2067121350606dc227beb8ee887a2d794169bf2cf24d9e')
    specifications = [(args.baseline,'baseline',1e-4)]
    if not args.baseline_only:
        specifications += [(args.low3,'low3',3e-5),(args.low1,'low1',1e-5)]
    rows, evaluations = [], []
    for root, label, rate in specifications:
        row, evaluation = reduce_root(root, label, rate, native, preparation)
        rows.append(row)
        evaluations.append(evaluation)
    pairs = [compare(evaluations[left],evaluations[right],[rows[left]['label'],rows[right]['label']])
             for left,right in itertools.combinations(range(len(rows)),2)]
    valid = all(row['valid'] for row in rows) and all(pair['cue_metadata_match'] and pair.get('cue_order_equal') for pair in pairs)
    result = dict(mode='baseline_only' if args.baseline_only else 'three_rate_descriptive_diagnostic', valid=valid,
                  native_source_sha256=SOURCE_HASH, rows=rows, comparisons=pairs,
                  off_match=all(pair['off_exact_at_serialized_precision'] for pair in pairs) if pairs else None,
                  model_authentication='UNRESOLVED_LOCAL_HASHES_ONLY',
                  notes=['Read-only CPU reduction; no model loads, writes, campaign-analyzer edits, or resource actions.',
                         'Native G9 unchanged: bootstrap2000/seed0/n16; lower bound>0 and spill<=0.03.',
                         'OFF drift has no invented tolerance; use each fit own OFF. Same rounded scores do not authenticate weights.',
                         'Baseline may have a pooled three-bank report: only per_bank.0 G9 is compared.',
                         'No independent-seed, clean-lineage, or working selective-writer claim. Main owns cleanup reconciliation.'])
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if valid else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(json.dumps(dict(valid=False, error=type(error).__name__ + ': ' + str(error))))
        sys.exit(2)
