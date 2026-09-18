"""Warm exact scene-aware judge; restore complete state before future-only scoring."""

import argparse
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import ny_caption_data as data
from gpu.ny_caption_game import DevelopmentManifest
from gpu.ny_caption_life_service import LifeSession, restoration_evidence
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_relative_game import build_game
from gpu.ny_caption_similarity import FrozenCPUEncoder
from research_loop.workers.rohin233_ovx4_recovery_20260918.dual_judge import DualScalar, EpochJudge, EpochSessionMixin, attach_epoch
from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import verified_source
from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate, put
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract
from research_loop.workers.rohin233_ovx4_recovery_20260918.warm_service import await_handoff


class NativeEpoch(EpochSessionMixin,LifeSession):
    pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    config=json.loads(parser.parse_args().config.read_bytes())
    validate(config)
    root=Path(config['root'])
    source=verified_source(config['checkpoint_root'],config['checkpoint_complete_sha256'],
        config['checkpoint_adapter_sha256'],config['checkpoint_config_sha256'])
    for relative,expected in data.bound(config['source_manifest']).items():
        data.require(data.file_ref(root/'source'/relative)['sha256']==expected,'immutable_receiving_runtime')
    started=time.time()
    old=data.bound(config['old_scalar'])
    checkpoint=Path(config['checkpoint_root'])
    primary=data.private_write(root/'primary_scalar.json',dict(old,selected_adapter_root=str(checkpoint/'adapter'),
        adapter={name:data.file_ref(checkpoint/'adapter'/name) for name in old['adapter']}))
    dual=DualScalar(config['old_scalar']['path'],primary['path'])
    manifest=DevelopmentManifest.from_mapping(data.bound(config['game_manifest']))
    encoder=FrozenCPUEncoder(config['encoder_manifest'],threads=2)
    pixels=PixelConfig(**data.bound(config['pixel_config']))
    records=data.bound(config['reference_panels'])
    old_panels={record['selected'][0]['scene']:record['scores'] for record in records}
    data.require(len(records)==len(manifest.contests)==3,'same_three_development_panels')
    if config.get('old_panel_scores'):
        data.require(old_panels==data.bound(config['old_panel_scores']),'exact_unchanged_reference_panel_selection')
    primary_panels={}
    for record in records:
        data.require(len(record['selected'])==len(record['scores'])==64,'same64_reference_identities')
        scene=record['selected'][0]['scene']
        data.require(all(item['scene']==scene for item in record['selected']),'reference_scene_join')
        primary_panels[scene]=dual.score(record['selected'])
    data.private_write(root/'PRIMARY_PANEL_SCORES.private.json',primary_panels)
    put(root/'MODEL_WARM.json',dict(unix=time.time(),pid=os.getpid(),deadline_unix=config['deadline_unix'],
        primary_step=15625,source=source,weight_proofs=dual.weight_proofs,model_load_seconds=time.time()-started,
        reference_panel_source_sha256=config['reference_panels']['sha256'],session_writer=False))
    handoff=await_handoff(config)
    sockets=root/'sockets'
    sockets.mkdir(exist_ok=True)
    if config['kind']=='p3':
        hub=SimpleNamespace(sessions={},registry={})
    else:
        from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub, serve
        hub=Hub(sockets,dict(complete=True,rows=[]),None,None,None)
    if config['kind']=='base':
        from research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch import EpochSession
        class BaseEpoch(EpochSessionMixin,EpochSession):
            pass
    evidence=[]
    for identifier,reference in handoff['sessions'].items():
        state=data.bound(reference)
        game=build_game(manifest,dual,primary_panels,pixels,encoder,top_k=50,
            agent_id=state['game']['agent_id'],lane=state['game']['lane'],
            relevance_threshold=config['relevance_threshold'])
        game._judge=EpochJudge(dual,primary_panels,old_panels,game._judge.relevance,manifest)
        session_type=BaseEpoch if config['kind']=='base' else NativeEpoch
        output=Path(config['outputs'][identifier])
        session=session_type(game,state['life_root'],output,state['scene_ids'],resume_state=state,
            source_mode=state['source_mode'],session_binding=state['session_binding'])
        if config['kind']=='base':
            session.transition=data.bound(config['transition'])
            hub.base=session
        else:
            hub.sessions[identifier]=session
            hub.registry[identifier]=state['session_binding']
        binding=attach_epoch(session,root/'epochs'/identifier,identifier,reference,dual.reference,dual.old_reference)
        evidence.append(dict(player=identifier,epoch_sha256=session.epoch_ledger.epoch_sha256,
            epoch_binding=binding,**restore_contract(state,session.snapshot()),**restoration_evidence(session,reference)))
    put(root/'LOADED.json',dict(unix=time.time(),pid=os.getpid(),physical=config['physical'],
        deadline_unix=config['deadline_unix'],primary_step=15625,primary_rank=8,source=source,
        shadow_step=6250,shadow_seconds_per_player=3600,sessions=evidence,weight_proofs=dual.weight_proofs,
        historical_rescoring=False,scorer_not_learner=True,raw_result_receipts_unchanged=True))
    if config['kind']=='p3':
        from gpu.ny_caption_life_service import serve as serve_native
        listener=root/'listener'
        listener.mkdir()
        callback=SimpleNamespace(output=listener,process=hub.sessions['p3'].process)
        serve_native(callback,config['socket'],int(config['deadline_unix']-time.time()))
    else:
        serve(hub,config['deadline_unix'])


if __name__=='__main__':
    main()
