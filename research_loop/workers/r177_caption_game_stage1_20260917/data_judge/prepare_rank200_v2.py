"""One bounded local CPU preparation; TRAIN/registered DEV only, aggregate output."""

from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import statistics
import time

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import rank200_calibration_v2 as instrument


def prepare():
    work = Path(__file__).resolve().parent
    payload = work/'private/bt_qwen_v2/PAYLOAD'
    destination = work/'rank200_reference_v2'
    data.require(not destination.exists(), 'fresh_rank200_preparation_no_overwrite')
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_preparation')
    reader = instrument.Reader()
    started = time.time()
    registration = data.private_write(destination/'REGISTRATION.json', dict(contract=instrument.CONTRACT,
        frozen_unix=started, source={name: data.file_ref(work/name) for name in
            ('rank200_calibration_v2.py', 'prepare_rank200_v2.py', 'test_rank200_calibration_v2.py')},
        authority='Main/Astra Builder under user standing directives', new_human_ratification=False,
        before_new_candidate_model_scoring=True, old_BTv2_artifacts_unchanged=True))
    data.private_write(destination/'ATTEMPT_STARTED.json', dict(started_unix=started, registration=registration,
        pid=os.getpid(), no_automatic_retry=True, GPU_calls=0, model_calls=0))
    try:
        original = reader.json(data.file_ref(payload/'data/ORIGINAL_MANIFEST.private.json'))
        plan = reader.json(data.file_ref(payload/'data/DEVELOPMENT_PLAN.private.json'))
        manifest = reader.json(data.file_ref(payload/'data/DATA_MANIFEST.private.json'))
        catalog = reader.json(data.file_ref(payload/'data/SCENE_CATALOG.private.json'))
        downloaded = reader.json(original['downloaded'])
        data.require(plan['schema'] == 'NY_PREDECLARED_DEVELOPMENT_JUDGE_PLAN_V1'
            and plan['FINAL_consumed'] is False and plan['locked_judge_validation_consumed'] is False,
            'registered_development_only_plan')
        roles = plan['subsets']
        data.require(set(roles) == {'judge_train', 'model_selection', 'probability_calibration', 'threshold_selection', 'development_audit'}
            and len(roles['judge_train']) == 180, 'same180_contest_fitting_pool')
        selected = [name for names in roles.values() for name in names]
        data.require(len(selected) == len(set(selected)) and set(selected) <= set(original['pools']['judge_train']+original['pools']['judge_dev']),
            'no_locked_or_FINAL_contests_selected')
        tables = {data.filename_contest(entry['name']): entry['reference'] for entry in downloaded['files']
            if entry['name'].endswith('.csv') and data.filename_contest(entry['name']) in set(selected)}
        data.require(set(tables) == set(selected), 'actual_original_CSV_for_every_permitted_contest')
        summaries, prepared, panel_candidates = defaultdict(list), {}, {}
        missing = Counter()
        for role, names in roles.items():
            for name in names:
                data.require(time.time()-started < 600, 'finite_CPU_preparation_wall')
                summary, unique, by_rank = instrument.raw_contest(reader.read(tables[name]), name)
                reference = dict(manifest['contests'][name]['rows'], path=str(payload/'data/rows'/(name+'.jsonl')))
                clean = [json.loads(line) for line in reader.read(reference).splitlines()]
                joined = instrument.join_clean(clean, unique, summary['original_rows'])
                facts = catalog['scenes'][name]['facts']
                data.require(data.digest(facts) == catalog['scenes'][name]['facts_sha256'], 'unchanged_neutral_scene_projection')
                scene = data.released_judge_scene(facts)
                summary['clean_rows'] = len(joined)
                summary['clean_rows_with_exact_unique_original_rank'] = sum(row['published_rank'] is not None for row in joined)
                summary['raw_rows_not_in_clean_pool'] = summary['original_rows']-len(joined)
                summaries[role].append(summary)
                missing[role] += sum(row['published_rank'] is None for row in joined)
                reference = data.private_write(destination/'private/rows'/(name+'.jsonl'),
                    b''.join(data.canonical(row)+b'\n' for row in joined))
                prepared[name] = dict(rows=reference, role=role, original_CSV=tables[name],
                    original_contest_rows=summary['original_rows'], canonical_scene=scene)
                if role == 'judge_train':
                    panel_candidates[name] = [dict(row, scene=scene) for row in joined
                        if row['published_rank'] in instrument.CONTRACT['panel_ranks']]
        panel = instrument.fixed_panel(panel_candidates)
        panel_ref = data.private_write(destination/'private/REFERENCE_PANEL.private.json', dict(registration=registration,
            selection='HASH_FIXED_FOUR_FITTING_CONTESTS_EXACT_RELEASED_RANKS_190_200_210', rows=panel,
            panel_pool='judge_train', caption_text_forbidden_to_Main_and_children=True, technical_access_control_claim=False))
        plan_ref = data.private_write(destination/'private/PREPARED_DATA.private.json', dict(registration=registration,
            source_manifest=data.file_ref(payload/'data/ORIGINAL_MANIFEST.private.json'),
            original_development_plan=data.file_ref(payload/'data/DEVELOPMENT_PLAN.private.json'),
            subsets=roles, contests=prepared, panel=panel_ref, FINAL_used=False, locked_validation_used=False))
        aggregates = {}
        for role, entries in summaries.items():
            aggregates[role] = dict(contests=len(entries), original_rows=sum(item['original_rows'] for item in entries),
                clean_rows=sum(item['clean_rows'] for item in entries),
                invalid_rating_rows=sum(item['invalid_rating_rows'] for item in entries),
                missing_unique_rank_joins=missing[role], source_rank_mean_increases=sum(item['source_rank_mean_increases'] for item in entries),
                rank200_positive_vote_mass=instrument.summarize([item['literal_rank200_positive_vote_mass'] for item in entries]),
                rank200_mean_rating=instrument.summarize([item['literal_rank200_mean'] for item in entries]),
                top200_positive_vote_mass=instrument.summarize([item['full_top200_positive_vote_mass'] for item in entries]),
                rank200_coverage=instrument.summarize([item['literal_rank200_coverage'] for item in entries]),
                contests_rank200_meets_old_030_mass=sum(item['rank200_meets_old_point_mass'] for item in entries),
                contests_perfect_q_old_030_at_005_possible=sum(item['perfect_q_old_point_possible'] for item in entries),
                original_rank200_missing=sum(not item['literal_rank200_available'] for item in entries),
                source_rank_origin=dict(Counter(item['source_rank_origin'] for item in entries)))
        old = reader.json(data.file_ref(work/'portable/bt_qwen_v2/judge_config.json'))
        values = old['calibration']['values']
        report = dict(schema='NY_RANK200_CPU_DIAGNOSTIC_PUBLIC_V1', status='CPU_PREPARED_NOT_NEW_MODEL_SUCCESS',
            registration=registration, prepared_data=plan_ref, private_panel=panel_ref,
            panel_count=len(panel), panel_contests=4, counts_and_aggregates=aggregates,
            old_vote_q_calibration=dict(blocks=len(values), output_min=min(values), output_max=max(values),
                distinct_outputs=len(set(values)), original_tau=old['tau'], unchanged=True),
            q_range_does_not_alone_explain_feasibility='Threshold is tested against observed vote mass, not by whether predicted q reaches0.30.',
            reference_transform_cannot_improve_ranking=True, model_scoring_performed=False,
            rank_quality_operating_point_status='BLOCKED_UNSCORED_VERSIONED_CANDIDATE',
            full_judge_usable=False, no_new_human_validation_gate=True,
            original_rank_field_used=True, raw_quarantined_rows_not_sent_to_model=True,
            captions_disclosed=False, contest_ids_disclosed=False, FINAL_used=False, locked_validation_used=False,
            reused_development_only=True, charged_read_bytes=reader.charged, model_calls=0, GPU_calls=0,
            started_unix=started, completed_unix=time.time())
        reference = data.private_write(destination/'PUBLIC_DIAGNOSTIC.json', report)
        data.private_write(destination/'COMPLETED.json', dict(report=reference, completed_unix=time.time(), status=report['status']))
        print(json.dumps(dict(report=reference, **{key: value for key, value in report.items() if key not in ('registration', 'prepared_data', 'private_panel')})), flush=True)
    except BaseException as error:
        data.private_write(destination/'FAILED.json', dict(error_type=type(error).__name__, reason=str(error)[:300],
            observed_unix=time.time(), no_retry=True, charged_read_bytes=reader.charged))
        raise


if __name__ == '__main__':
    prepare()
