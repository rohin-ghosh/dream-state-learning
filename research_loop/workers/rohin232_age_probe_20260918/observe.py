"""Sanitized fixed-token curves; no source transcripts or private reference panels."""

import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time


CONDITIONS = ('source51', 'currentC2', 'base')


def utc(value):
    return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_bytes())


def reference(path):
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)


def aggregate(root):
    now = time.time()
    capture = read(root/'sources/CAPTURE.json')
    report = dict(schema='R232_AGE_PROBE_PUBLIC_V1', observed_utc=utc(now),
        observer_sha256=reference(Path(__file__))['sha256'], planned_generated_tokens_per_condition=6144,
        per_scene_seed_budget=1024, scenes=3, seeds=[23201,23202],
        cohort='fixed_fresh_context_parent_free_no_update_inference',
        scoring='frozen_widegap6250_rank_le_50_AND_relevance_then_embedding_novelty',
        literal_caption_quality_reviewed=0, raw_accepted_strings_are_not_certified_jokes=True,
        new_pixels_are_summed_events_in_independent_seed_archives_not_global_unique_ideas=True,
        scoring_time_attribution='entire_response_generated_tokens_charged_before_feedback',
        source_capture={key: capture[key] for key in ('head_index','head_sha256','sources')},
        selection=read(root/'SELECTION.json'), freshness=read(root/'FRESHNESS_VERIFIED.json'),
        source_manifest=reference(root/'SOURCE_MANIFEST.json'), conditions=[])
    for condition in CONDITIONS:
        output = root/'players'/condition
        row = dict(condition=condition, status='NOT_LOADED', current_process_alive=False,
            generated_tokens=0, completed_cells=0, generated_response_count=0,
            newly_scored_strings=0, cached_strings=0, accepted_new_scores=0,
            new_pixel_events=0, repeated_accepted_events=0, generation_seconds=0,
            elapsed_post_load_seconds=None, ETA_finish_utc=None, incomplete_budget_tokens=6144,
            seed_curves={}, cells=[])
        loaded_path = output/'LOADED.json'
        if loaded_path.exists():
            loaded = read(loaded_path)
            row.update(status='LOADED', pid=loaded['pid'], loaded_utc=utc(loaded['unix']),
                loaded_receipt=reference(loaded_path), identity=loaded['identity'],
                source_age=loaded['source_age'], current_process_alive=Path('/proc',str(loaded['pid'])).exists(),
                elapsed_post_load_seconds=max(0,now-loaded['unix']))
        records = []
        for path in output.glob('*/*.json'):
            if path.name == 'RESULT.json':
                result = read(path)
                row['completed_cells'] += int(result['status'] == 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET')
                row['cells'].append(dict(seed=result['seed'],contest_id=result['contest_id'],
                    status=result['status'],generated_tokens=result['generated_tokens'],
                    initial_context_sha256=result['initial_context_sha256'],result=reference(path)))
            elif path.stem.isdigit():
                record = read(path)
                records.append((record['generation']['started_unix'], path, record))
        seed_totals = {seed:dict(tokens=0,pixels=0,accepted=0) for seed in (23201,23202)}
        for _, path, record in sorted(records):
            event, generation = record['event'], record['generation']
            row['generated_tokens'] += event['actual_generated_tokens']
            row['generated_response_count'] += 1
            row['generation_seconds'] += generation['finished_unix']-generation['started_unix']
            seed = int(path.parent.name.rsplit('_',1)[1])
            seed_totals[seed]['tokens'] += event['actual_generated_tokens']
            per_event = Counter()
            for value in event['score']['results']:
                outcome = value['result']
                if outcome.get('cached'):
                    row['cached_strings'] += 1
                    continue
                if outcome.get('rank') is not None:
                    row['newly_scored_strings'] += 1
                accepted = outcome.get('accepted') is True
                novel = accepted and outcome.get('status') == 'new_pixel'
                row['accepted_new_scores'] += int(accepted)
                row['new_pixel_events'] += int(novel)
                row['repeated_accepted_events'] += int(accepted and outcome.get('status') == 'repeat')
                per_event['accepted'] += int(accepted)
                per_event['pixels'] += int(novel)
            seed_totals[seed]['accepted'] += per_event['accepted']
            seed_totals[seed]['pixels'] += per_event['pixels']
            row['seed_curves'].setdefault(str(seed),[]).append(dict(
                cumulative_generated_tokens=seed_totals[seed]['tokens'],
                cumulative_new_pixels=seed_totals[seed]['pixels'],
                cumulative_accepted_strings=seed_totals[seed]['accepted'],
                marginal_new_pixels=per_event['pixels'],stage=event['origin']['stage'],
                response_sha256=event['origin']['response_sha256'],actual_response_tokens=event['actual_generated_tokens']))
        queue_paths=list((root/'queue').glob(condition+'-*.request.json'))
        queued_by_cell={}
        for path in queue_paths:
            request=read(path)
            key=(request['identity']['contest_id'],request['identity']['seed'])
            queued_by_cell[key]=max(queued_by_cell.get(key,0),request['origin']['generated_tokens_after'])
        row['generated_tokens_including_pending_feedback']=sum(queued_by_cell.values())
        row['pending_score_request_count']=sum(not path.with_name(path.name.replace('.request.json','.result.json')).exists() for path in queue_paths)
        row['incomplete_budget_tokens']=6144-row['generated_tokens_including_pending_feedback']
        if row['generated_tokens'] and row['elapsed_post_load_seconds']:
            rate=row['generated_tokens']/row['elapsed_post_load_seconds']
            row['end_to_end_tokens_per_second']=rate
            row['generation_only_tokens_per_second']=row['generated_tokens']/row['generation_seconds']
            row['ETA_finish_utc']=utc(now+max(0,6144-row['generated_tokens'])/rate)
            row['ETA_basis']='measured_end_to_end_tokens_per_second_including_scoring_and_cell_resets; excludes_final_identity_hash'
            row['status']='GENERATING_AND_SCORED' if row['current_process_alive'] else 'PROCESS_EXITED_NEEDS_RESULT'
        failure=root/(condition+'_FAILED.json')
        if failure.exists():
            error=read(failure)
            row.update(status='FAILED_PRESERVED',failure_type=error['error_type'],failure_receipt=reference(failure))
        complete=output/'COMPLETE.json'
        if complete.exists():
            value=read(complete)
            row.update(status='COMPLETE' if row['completed_cells']==6 else 'INCOMPLETE_CELLS',
                completed_utc=utc(value['unix']),complete_receipt=reference(complete),
                unchanged_identity=value['unchanged_identity'],elapsed_seconds=value['elapsed_seconds'],ETA_finish_utc=None)
        row['marginal_discovery_per_256_tokens']={}
        for seed,points in row['seed_curves'].items():
            bins=[]
            for boundary in range(256,3073,256):
                if not points or points[-1]['cumulative_generated_tokens']<boundary:
                    break
                previous=sum(point['marginal_new_pixels'] for point in points if point['cumulative_generated_tokens']<=boundary-256)
                current=sum(point['marginal_new_pixels'] for point in points if point['cumulative_generated_tokens']<=boundary)
                bins.append(dict(generated_token_boundary=boundary,cumulative_new_pixels=current,marginal_new_pixels=current-previous))
            row['marginal_discovery_per_256_tokens'][seed]=bins
        report['conditions'].append(row)
    judge=root/'JUDGE_LOADED.json'
    if judge.exists():
        document=read(judge)
        report['judge']={key:document[key] for key in ('pid','unix','top_k','reference_count','panel_sha256','rule_sha256','fresh_development_panels')}
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(aggregate(args.root),sort_keys=True))


if __name__ == '__main__':
    main()
