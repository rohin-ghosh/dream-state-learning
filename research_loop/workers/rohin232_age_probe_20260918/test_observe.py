import json
import os
import time

from research_loop.workers.rohin232_age_probe_20260918.observe import aggregate


def put(root, name, value):
    path=root/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


def test_report_counts_pending_all_stage_tokens_and_separates_cache(tmp_path):
    put(tmp_path,'sources/CAPTURE.json',dict(head_index=1,head_sha256='a'*64,sources=[]))
    for name in ['SELECTION.json','FRESHNESS_VERIFIED.json','SOURCE_MANIFEST.json']:
        put(tmp_path,name,{})
    put(tmp_path,'players/source51/LOADED.json',dict(pid=os.getpid(),unix=time.time()-10,identity={},source_age={}))
    outcomes=[dict(caption_sha256='b'*64,result=dict(rank=1,accepted=True,status='new_pixel',cached=False)),
        dict(caption_sha256='c'*64,result=dict(rank=2,accepted=True,status='repeat',cached=False)),
        dict(caption_sha256='b'*64,result=dict(rank=1,accepted=True,status='new_pixel',cached=True))]
    event=dict(actual_generated_tokens=128,origin=dict(stage='THINK',response_sha256='d'*64),score=dict(results=outcomes))
    put(tmp_path,'players/source51/scene_23201/0001.json',dict(event=event,
        generation=dict(started_unix=1,finished_unix=3,raw='NEVER_PUBLIC_RAW_PAYLOAD')))
    for number,end in [(1,128),(2,256)]:
        put(tmp_path,f'queue/source51-scene-23201-{number:04d}.request.json',dict(
            identity=dict(contest_id='scene',seed=23201),origin=dict(generated_tokens_after=end)))
    put(tmp_path,'queue/source51-scene-23201-0001.result.json',{})
    result=aggregate(tmp_path)
    row=result['conditions'][0]
    assert row['generated_tokens']==128 and row['generated_tokens_including_pending_feedback']==256
    assert row['pending_score_request_count']==1 and row['incomplete_budget_tokens']==5888
    assert row['newly_scored_strings']==2 and row['accepted_new_scores']==2
    assert row['new_pixel_events']==1 and row['repeated_accepted_events']==1 and row['cached_strings']==1
    assert 'NEVER_PUBLIC_RAW_PAYLOAD' not in json.dumps(result)
    assert row['seed_curves']['23201'][0]['cumulative_generated_tokens']==128
    assert row['marginal_discovery_per_256_tokens']['23201']==[]
