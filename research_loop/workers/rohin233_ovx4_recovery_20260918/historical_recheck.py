"""Historical teaching/game diagnostic only; cannot mutate a player or score ledger."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_game import DevelopmentManifest, RelativeJudgeResult
from gpu.ny_caption_relevance import RelevanceGate
from gpu.ny_caption_scalar_judge import relative_position
from gpu.ny_caption_similarity import FrozenCPUEncoder
from research_loop.workers.rohin233_ovx4_recovery_20260918.dual_judge import DualScalar
from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate, put


def p3_history(snapshot_reference,result_directories):
    from gpu.ny_caption_life import _child_stage
    state=data.bound(snapshot_reference)
    proof={}
    verified_responses={}
    faults={}
    for directory in result_directories:
        for path in sorted(Path(directory).glob('*/RESULT.json')):
            document=data.bound(data.file_ref(path))
            for source in document['report'].get('caption_sources',[]):
                try:
                    origin=source['origin']
                    identity=(origin['record_sha256'],source['stage'])
                    if identity not in verified_responses:
                        verified_responses[identity]=_child_stage(state['life_root'],origin,source['stage'])
                    raw=verified_responses[identity]
                    text=raw[source['start']:source['end']]
                    data.require(hashlib.sha256(text.encode()).hexdigest()==source['text_sha256'],'historical_exact_child_span')
                    proof[(source['contest_id'],text)]=dict(origin=origin,stage=source['stage'],start=source['start'],end=source['end'],
                        text_sha256=source['text_sha256'],result_sha256=data.file_ref(path)['sha256'])
                except (ValueError,KeyError,OSError) as error:
                    name=type(error).__name__
                    faults[name]=faults.get(name,0)+1
    scenes={row['contest_id']:row['canonical_scene'] for row in state['game']['manifest_bindings']}
    rows=[]
    for item in state['game']['submissions']:
        source=proof.get((item['contest_id'],item['caption']))
        rows.append(dict(player='P3',designation='HISTORICAL_GAME_RECHECK_NOT_NEW_EXPLORATION',
            contest_id=item['contest_id'],scene=scenes[item['contest_id']],caption=item['caption'],
            caption_sha256=hashlib.sha256(item['caption'].encode()).hexdigest(),old_result=item['result'],
            original_snapshot_sha256=snapshot_reference['sha256'],source=source,
            parent_correction_eligible=source is not None))
    return rows,dict(rows=len(rows),parent_source_verified=sum(row['parent_correction_eligible'] for row in rows),
        source_verification_failures=faults,unverified_rows_not_delivered_to_parent=True)


def seed_history(packet_reference,generation_root):
    from research_loop.workers.rohin221_continuous_caption_20260918.controller import digest as generation_digest
    packet=data.bound(packet_reference)
    rows=[]
    for item in packet['examples']:
        source=item['source']
        path=Path(generation_root)/(source['request_sha256']+'.json')
        data.require(data.file_ref(path)['sha256']==source['generation_file_sha256'],'seed_exact_original_generation_file')
        document=data.bound(data.file_ref(path))
        data.require(generation_digest(document['request'])==source['request_sha256'] and generation_digest(document['generated'])==source['response_sha256'],
            'seed_generation_request_response_binding')
        raw=document['generated']['raw']
        span=source['literal_span']
        text=raw[span['start']:span['end']]
        data.require(hashlib.sha256(text.encode()).hexdigest()==span['text_sha256'] and text==item['caption'],
            'same_supplied_seed_literal_not_rewritten')
        rows.append(dict(player='FROZEN_BASE_SEED',seed_id=item['seed_id'],designation='SUPPLIED_TEACHING_CONTEXT_HISTORICAL_RECHECK',
            contest_id=item['scene']['contest_id'],scene=item['scene']['description'],caption=item['caption'],
            caption_sha256=item['caption_sha256'],old_result=item['historical_result'],source=source,
            original_snapshot_sha256=packet_reference['sha256'],parent_correction_eligible=True))
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    config=json.loads(parser.parse_args().config.read_bytes())
    validate(config)
    root=Path(config['root'])
    rows=data.bound(config['p3_rows'])+seed_history(config['seed_packet'],config['generation_root'])
    data.require(0<len(rows)<=500,'bounded_historical_correction_batch')
    service=data.bound(config['service_config'])
    manifest=DevelopmentManifest.from_mapping(data.bound(service['game_manifest']))
    scenes={item.contest_id:item.canonical_scene for item in manifest.contests}
    data.require(all(row['scene']==scenes[row['contest_id']] for row in rows),'historical_same_development_scene')
    data.require(all(hashlib.sha256(row['caption'].encode()).hexdigest()==row['caption_sha256'] for row in rows),'same_historical_caption_bytes')
    judge=DualScalar(service['old_scalar']['path'],config['primary_scalar']['path'])
    panels=data.bound(config['primary_panels'])
    encoder=FrozenCPUEncoder(service['encoder_manifest'],threads=2)
    relevance=RelevanceGate(encoder,service['relevance_threshold'])
    put(root/'LOADED.json',dict(unix=time.time(),pid=os.getpid(),rows=len(rows),weight_proofs=judge.weight_proofs,new_player_attempts=0))
    scores=judge.score([dict(scene=row['scene'],caption=row['caption']) for row in rows])
    public=[]
    correction=[]
    for row,score in zip(rows,scores):
        rank=relative_position(score,panels[row['scene']],50)
        result=RelativeJudgeResult(**{key:rank[key] for key in ('raw_score','rank','reference_count','top_k')},
            relevance_score=relevance.score(row['scene'],row['caption']),relevance_threshold=relevance.threshold)
        item=dict(player=row['player'],seed_id=row.get('seed_id'),caption_sha256=row['caption_sha256'],
            original_snapshot_sha256=row['original_snapshot_sha256'],old_rank=row['old_result']['rank'],
            old_raw_accepted=row['old_result']['accepted'],old_novelty_status=row['old_result']['status'],
            new_rank=result.rank,new_rank_relevance_pass=result.accepted,new_relevance_score=result.relevance_score,
            parent_correction_eligible=row['parent_correction_eligible'],novelty_re_evaluated=False,
            new_player_attempts=0,original_receipts_unchanged=True,source=row['source'])
        public.append(item)
        if row['parent_correction_eligible']:
            correction.append(dict(item,caption=row['caption'],scene=row['scene'],
                notice='Historical score-only correction under human-directed judge15625; not a new attempt, novelty award, or humor proof.'))
    data.private_write(root/'PARENT_CORRECTIONS.private.json',correction)
    put(root/'COMPLETE.json',dict(unix=time.time(),pid=os.getpid(),primary_step=15625,adapter_sha256=judge.weight_proofs['r210_15625']['artifact_sha256'],
        row_count=len(rows),parent_verified_rows=len(correction),rows=public,original_receipts_unchanged=True,
        new_player_attempts=0,novelty_mutations=0,parent_publication_actions=0,FINAL_read=False,
        parent_delivery='OWNER_REQUIRED_NOT_PUBLISHED_BY_DIAGNOSTIC'))


if __name__=='__main__':
    main()
