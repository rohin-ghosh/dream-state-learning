"""Read bounded post-LOAD C2 stage receipts; never replay the historical journal."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

from deadline_resume import identity, read, require, sha
from receipt_window import digest, header, read_record


CONTROL = Path('/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/control')
GUARD = '29d1aa615820332deaa826bd8505209ef89c9fed5aea0f6fe98e7690d0867ffb'
JOURNAL = '260be8b8710a42559b291797c6e14983'


def collect():
    require(sha(CONTROL/'GUARD.json') == GUARD, 'exact_admitted_guard')
    config = read(CONTROL/'GUARD.json')
    require(sha(config['plan_path']) == config['plan_sha256'], 'same_plan')
    plan = read(config['plan_path'])
    actor = identity(1139778)
    require(actor['start_ticks'] == '30025875' and actor['cwd'] == plan['source_root']
        and actor['argv'][-3:] == ['native','--config',str(CONTROL/'GUARD.json')], 'same_loaded_native')
    records = Path(plan['root'])/'stream/records'
    selected = []
    headers = []
    for index in range(11504, 12004):
        path = records/f'{index:020d}.json'
        if not path.exists():
            break
        metadata = header(path)
        require(metadata['journal_id'] == JOURNAL and metadata['index'] == index, 'same_contiguous_tail')
        headers.append(metadata)
        if metadata['kind'] in ('LOADED','R184_STAGE','RESPONSE','COMMITTED','CONTEXT_COMMITTED',
                'SLEEP_RECIPE','TARGET_ELIGIBILITY','SLEEP_COMPLETE','R184_ACT'):
            record = read_record(path,JOURNAL)
            intent = read(path.with_name(f'{index:020d}.intent.json'))
            require(intent['record_sha256'] == record['sha256'], 'actual_record_intent')
            selected.append(record)
    stages = []
    for stage in (record for record in selected if record['kind'] == 'R184_STAGE'):
        source = stage['document']['source_sha256']
        responses = [record for record in selected if record['kind']=='RESPONSE'
            and digest(record['document']) == source]
        commits = [record for record in selected if record['kind'] in ('COMMITTED','CONTEXT_COMMITTED')
            and record['document'].get('source_sha256') == source]
        require(len(responses)==len(commits)==1, 'unique_response_and_commit_for_actual_stage')
        response, commit = responses[0], commits[0]
        candidates = [entry for entry in headers if entry['kind']=='REQUEST' and entry['index']<response['index']]
        require(bool(candidates), 'actual_REQUEST_before_response')
        request = read_record(records/f'{candidates[-1]["index"]:020d}.json', JOURNAL)
        require(response['document']['request_sha256'] == digest({key:value
            for key,value in request['document'].items() if key!='resume_state'}), 'request_response_digest')
        text = response['document']['response']['raw']
        stages.append(dict(stage=stage['document']['stage'],
            request=dict(index=request['index'],sha256=request['sha256']),
            response=dict(index=response['index'],sha256=response['sha256']),
            commit=dict(index=commit['index'],sha256=commit['sha256']),
            stage_record=dict(index=stage['index'],sha256=stage['sha256']),
            text_sha256=digest(text),characters=len(text),text_excerpt=text[:1600]))
    recipes = [dict(index=record['index'],sha256=record['sha256'],document=record['document'])
        for record in selected if record['kind'] in ('SLEEP_RECIPE','TARGET_ELIGIBILITY')]
    sleeps = [dict(index=record['index'],sha256=record['sha256'],document={key:value
        for key,value in record['document'].items() if key!='resume_state'})
        for record in selected if record['kind']=='SLEEP_COMPLETE']
    require(identity(1139778)==actor, 'same_incarnation_after_read')
    return dict(schema='R233_C2_POST_RECOVERY_RECEIPTS_V1',observed_utc=datetime.now(timezone.utc).isoformat(),
        native=actor,journal_id=JOURNAL,guard_sha256=GUARD,stages=stages,recipes=recipes,sleeps=sleeps,
        latest_index=headers[-1]['index'],native_signals=[],journal_writes=0,
        first_ACT_verified=any(stage['stage']=='ACT' for stage in stages),
        no_semantic_exclusions_plan=plan['learn_row_policy']=='R227_ALL_AUTHENTIC_CHILD_ROWS_V1')


if __name__ == '__main__':
    print(json.dumps(collect(),sort_keys=True,indent=2))
