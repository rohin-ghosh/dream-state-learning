"""Hash-bound descriptive reduction; no semantic or causal learning verdict."""

import argparse
from collections import defaultdict
from pathlib import Path
import statistics

from gpu import orch_r124_route_behavior_probe as probe


def load_condition(directory, prompts, export):
    complete = probe.read(directory / 'COMPLETE.json')
    condition = directory.name
    source_condition = 'AFTER' if condition == 'AFTER_LORA_OFF' else condition
    loaded = probe.read(directory / 'LOADED.json')
    probe.require(complete['condition'] == loaded['condition'] == condition, 'actual_condition_binding')
    probe.require(loaded['adapter']['state_sha256'] == export['checkpoints'][source_condition]['adapter_state_sha256']
                  and loaded['adapter']['base_sha256'] == probe.BASE_SHA, 'actual_mounted_checkpoint')
    probe.require(loaded['fresh_process'] and loaded['parent_free'] and loaded['context_free'],
                  'fresh_parent_free_loaded_stage')
    probe.require(complete['base_adapter_unchanged'] and complete['prompts_sha256'] == export['prompts_sha256'],
                  'completed_unchanged_state_and_prompts')
    probe.require(complete['native_calls'] == 32 and complete['parent_calls'] == complete['optimizer_steps'] == 0,
                  'read_only_complete_condition')
    expected = {row['id']: row for row in prompts}
    rows = {}
    for reference in complete['calls']:
        path = Path(reference['path'])
        probe.require(path.parent == directory / 'calls', 'own_condition_capture')
        probe.require(probe.sha(path) == reference['sha256'], 'complete_capture_hash')
        row = probe.read(path)
        probe.require(row['condition'] == condition, 'capture_condition_binding')
        probe.require(row['id'] in expected and row['id'] not in rows, 'unique_expected_prompt')
        prompt = expected[row['id']]
        probe.require(row['messages_sha256'] == prompt['messages_sha256']
                      and row['response']['messages'] == prompt['messages'], 'identical_prompt_bytes')
        probe.require(row['status'] == 'COMPLETE' and row['trainingAllowed'] is False and row['parent_free'],
                      'uncontaminated_readout')
        rows[row['id']] = row
    probe.require(set(rows) == set(expected), 'all_fixed_prompts_captured')
    return rows


def paired_rows(conditions):
    probe.require(set(conditions) == set(probe.CONDITIONS), 'three_actual_conditions')
    ids = set(conditions['BEFORE'])
    probe.require(all(set(rows) == ids for rows in conditions.values()), 'matched_prompt_sets')
    result = []
    for identity in sorted(ids):
        before, after, off = [conditions[condition][identity] for condition in probe.CONDITIONS]
        probe.require(before['messages_sha256'] == after['messages_sha256'] == off['messages_sha256'],
                      'same_prompt_all_conditions')
        result.append(dict(id=identity, style=before['style'], context=before['context'],
            prompt_sha256=before['messages_sha256'],
            before=before['metrics'], after=after['metrics'], after_lora_off=off['metrics'],
            output_changed=before['response']['raw'] != after['response']['raw'],
            action_changed=before['metrics']['action'] != after['metrics']['action'],
            after_differs_from_base=after['response']['raw'] != off['response']['raw'],
            generated_token_delta=after['metrics']['generated_tokens'] - before['metrics']['generated_tokens'],
            rationale_token_delta=after['metrics']['rationale_tokens'] - before['metrics']['rationale_tokens']))
    return result


def primary_pairs(before_rows, after_rows):
    probe.require(set(before_rows) == set(after_rows), 'matched_primary_prompt_sets')
    result = []
    for identity in sorted(before_rows):
        before, after = before_rows[identity], after_rows[identity]
        probe.require(before['messages_sha256'] == after['messages_sha256'], 'same_primary_prompt')
        result.append(dict(id=identity, style=before['style'], context=before['context'],
            prompt_sha256=before['messages_sha256'], before=before['metrics'], after=after['metrics'],
            output_changed=before['response']['raw'] != after['response']['raw'],
            action_changed=before['metrics']['action'] != after['metrics']['action'],
            generated_token_delta=after['metrics']['generated_tokens'] - before['metrics']['generated_tokens'],
            rationale_token_delta=after['metrics']['rationale_tokens'] - before['metrics']['rationale_tokens']))
    return result


def summarize(rows, conditions=('before', 'after', 'after_lora_off')):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['style'], row['context']].append(row)
    summaries = []
    for (style, context), items in sorted(grouped.items()):
        summary = dict(style=style, context=context, count=len(items),
            outputs_changed=sum(row['output_changed'] for row in items),
            actions_changed=sum(row['action_changed'] for row in items))
        if 'after_lora_off' in conditions:
            summary['after_outputs_different_from_base'] = sum(row['after_differs_from_base'] for row in items)
        for condition in conditions:
            summary[condition] = dict(
                median_generated_tokens=statistics.median(row[condition]['generated_tokens'] for row in items),
                median_rationale_tokens=statistics.median(row[condition]['rationale_tokens'] for row in items),
                responses_with_rationale=sum(row[condition]['rationale_tokens'] > 0 for row in items),
                truncated=sum(row[condition]['truncated'] for row in items),
                terminal=sum(row[condition]['terminal'] for row in items),
                mean_repeated_fourgram_fraction=statistics.mean(
                    row[condition]['repeated_fourgram_fraction'] for row in items))
        summaries.append(summary)
    return summaries


def reduce(plan_path, output):
    plan = probe.read(plan_path)
    probe.require(plan['schema'] == probe.SCHEMA, 'diagnostic_plan')
    result = dict(schema='R124_MATCHED_ROUTE_DESCRIPTIVE_RESULTS_V1', plan=probe.reference(plan_path),
        checkpoint_selection='LATEST_CONSECUTIVE_AT_EXPORT_NOT_SELECTED_ON_RESPONSES',
        training_or_parent_calls=0, optimizer_steps=0, raw_text_location='NODE_LOCAL_CALL_FILES',
        causal_parenting_effect='UNPROVEN_NO_MATCHED_UNPARENTED_TWIN_IN_THIS_ASSAY',
        retained_improvement='UNPROVEN', semantic_coherence='UNJUDGED', branches={})
    for branch, bundle in sorted(plan['bundles'].items()):
        export, prompts = probe.verify_bundle(bundle['root'])
        directory = Path(plan['output']) / branch
        missing = [condition for condition in probe.CONDITIONS
                   if not (directory / condition / 'COMPLETE.json').exists()]
        if missing:
            result['branches'][branch] = dict(status='INCOMPLETE', missing_conditions=missing)
            if all(condition not in missing for condition in ('BEFORE', 'AFTER')):
                primary = {condition: load_condition(directory / condition, prompts, export)
                           for condition in ('BEFORE', 'AFTER')}
                rows = primary_pairs(primary['BEFORE'], primary['AFTER'])
                result['branches'][branch]['within_sleep_comparison'] = dict(
                    status='VERIFIED_BEFORE_AFTER_ONLY', checkpoints=export['checkpoints'],
                    prompts_sha256=export['prompts_sha256'], pairs=rows,
                    summaries=summarize(rows, conditions=('before', 'after')),
                    base_comparison='UNVERIFIED', causal_parenting_effect='UNPROVEN')
            continue
        conditions = {condition: load_condition(directory / condition, prompts, export)
                      for condition in probe.CONDITIONS}
        rows = paired_rows(conditions)
        result['branches'][branch] = dict(status='COMPLETE', checkpoints=export['checkpoints'],
            prompts_sha256=export['prompts_sha256'], summaries=summarize(rows), pairs=rows,
            condition_receipts={condition: probe.reference(directory / condition / 'COMPLETE.json')
                                for condition in probe.CONDITIONS})
    probe.write(output, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = reduce(arguments.plan, arguments.output)
    print({branch: value['status'] for branch, value in result['branches'].items()})
