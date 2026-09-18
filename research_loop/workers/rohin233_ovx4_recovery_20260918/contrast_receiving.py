"""Finite receiving-side rerun of exact DEVELOPMENT contrasts, never game attempts."""

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from research_loop.workers.rohin233_ovx4_recovery_20260918.dual_judge import DualScalar
from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate, put


CASE_HASH='6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba'
TYPES=('word_shuffled','scene_description','nonsense','truncated','mid_tier','other_contest')


def validate_cases(cases):
    data.require(len(cases)==600 and len({row['contest'] for row in cases})==20,'same600_cases20_contests')
    data.require(collections.Counter(row['kind'] for row in cases)=={kind:100 for kind in TYPES},'six_equal_case_types')
    data.require(data.digest([row['case_id'] for row in cases])==CASE_HASH,'exact_predeclared_case_identity')
    data.require(all(data.digest({key:value for key,value in row.items() if key!='case_id'})==row['case_id'] for row in cases),
        'case_id_binds_private_case_bytes')


def evaluate(judge,cases):
    keys=list(dict.fromkeys((row['scene'],row[side]) for row in cases for side in ('good','contrast')))
    data.require(all(judge.token_count(scene,caption)<=judge.max_length for scene,caption in keys),'all600_cases_untruncated')
    values={}
    for start in range(0,len(keys),8):
        batch=keys[start:start+8]
        values.update(zip(batch,judge.score([dict(scene=scene,caption=caption) for scene,caption in batch])))
    records=[]
    for row in cases:
        records.append(dict(case_id=row['case_id'],kind=row['kind'],good_score=values[(row['scene'],row['good'])],
            contrast_score=values[(row['scene'],row['contrast'])]))
    summary={}
    for kind in TYPES:
        group=[row for row in records if row['kind']==kind]
        wins=sum(row['good_score']>row['contrast_score'] for row in group)
        ties=sum(row['good_score']==row['contrast_score'] for row in group)
        summary[kind]=dict(scored=len(group),wins=wins,ties=ties,losses=len(group)-wins-ties)
    return summary,records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    config=json.loads(parser.parse_args().config.read_bytes())
    validate(config)
    root=Path(config['root'])
    cases=data.bound(config['cases'])
    validate_cases(cases)
    started=time.time()
    judge=DualScalar(config['old_scalar']['path'],config['primary_scalar']['path'])
    put(root/'LOADED.json',dict(unix=time.time(),pid=os.getpid(),physical=config['physical'],
        actual_service_loaded_sha256=config['service_loaded']['sha256'],weight_proofs=judge.weight_proofs,
        inference_only=True,game_requests=0,private_rows_to_parents=False))
    by_type,records=evaluate(judge,cases)
    data.private_write(root/'SCORES.private.json',records)
    put(root/'COMPLETE.json',dict(unix=time.time(),pid=os.getpid(),started_unix=started,
        elapsed_seconds=time.time()-started,primary_step=15625,primary_rank=8,
        adapter_sha256=judge.weight_proofs['r210_15625']['artifact_sha256'],case_ids_sha256=CASE_HASH,
        cases_file_sha256=config['cases']['sha256'],cases=600,contests=20,by_type=by_type,
        actual_service_loaded_sha256=config['service_loaded']['sha256'],
        execution='SEPARATE_RECEIVING_PROCESS_IDENTICAL_DUAL_JUDGE_SOURCE_AND_ARTIFACTS_NOT_LIVE_GAME_RPC',
        new_player_attempts=0,historical_player_rescoring=False,FINAL_read=False,
        claim='CONSTRUCTED_DEVELOPMENT_DIAGNOSTIC_NOT_HUMOR_VALIDATION_OR_WINNER_SELECTION'))


if __name__=='__main__':
    main()
