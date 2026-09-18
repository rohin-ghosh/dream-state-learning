"""One additional frozen age with the exact original battery and reference panels."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import ny_caption_data as data
from research_loop.workers.rohin232_age_probe_20260918 import contract, runtime
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches


PANEL_SHA = '4adab198a81f2492fff5471d0a7a20de41c06f59c7a492d7ef35746f84d346aa'
RULE_SHA = '7127a82613c6c75ed561b180ad394a657acbc194cb27cca72bc3b0a686d6444a'
GAME_SHA = '31e3c9919524deacc1d8255caa65f5121744ef6f0465988576b2d1b7ad281274'


def same_battery(root):
    identity=runtime.read(root/'CONDITION.json')
    if identity['condition']!='C0' or identity['absolute_sleep']!=84:
        raise ValueError('this_dispatch_is_exact_C0_sleep84_only')
    if data.file_ref(root/'GAME_MANIFEST.json')['sha256']!=GAME_SHA:
        raise ValueError('original_three_scene_manifest_unchanged')
    if data.file_ref(root/'judge/REFERENCE_PANELS.private.json')['sha256']!=PANEL_SHA:
        raise ValueError('original_private_panels_unchanged')
    if contract.digest(runtime.read(root/'assets/RULE.json'))!=RULE_SHA:
        raise ValueError('original_scoring_rule_unchanged')
    for relative,expected in identity['preregistered_source_files'].items():
        if data.file_ref(root/'source'/relative)['sha256']!=expected:
            raise ValueError('preregistered_battery_source_bytes_unchanged')
    return identity


def panel_scores(rows, scenes):
    expected={scene.canonical_scene for scene in scenes.contests}
    panels={}
    for row in rows:
        if len(row['selected'])!=64 or len(row['scores'])!=64:
            raise ValueError('original_64_reference_panel')
        scene=row['selected'][0]['scene']
        if any(item['scene']!=scene for item in row['selected']) or scene in panels:
            raise ValueError('unambiguous_original_panel_scene')
        panels[scene]=row['scores']
    if set(panels)!=expected:
        raise ValueError('same_three_panel_scenes')
    return panels


def judge(root, deadline):
    from gpu.ny_caption_game import DevelopmentManifest
    from gpu.ny_caption_pixels import PixelConfig
    from gpu.ny_caption_relative_game import build_game
    from gpu.ny_caption_scalar_judge import ScalarJudge
    from gpu.ny_caption_similarity import FrozenCPUEncoder
    identity=same_battery(root)
    manifest=DevelopmentManifest.from_mapping(runtime.read(root/'GAME_MANIFEST.json'))
    assets=root/'assets'
    rule=runtime.read(assets/'RULE.json')
    base_ref=runtime.write(root/'judge/base_manifest.json',dict(runtime.read(assets/'base_manifest.json'),root=runtime.BASE_ROOT))
    scalar_config=runtime.write(root/'judge/scalar_runtime.json',dict(schema='R207_SCALAR_RUNTIME_V1',base_model=base_ref,
        selected_adapter_root=str(assets/'adapter'),adapter={name:data.file_ref(assets/'adapter'/name) for name in rule['adapter']},
        config=dict(max_length=rule['max_length']),source_judge_config_sha256=rule['original_judge_config_sha256']))
    scalar=ScalarJudge(scalar_config['path'],batch_size=8)
    panels=panel_scores(runtime.read(root/'judge/REFERENCE_PANELS.private.json'),manifest)
    encoder=FrozenCPUEncoder(data.file_ref(assets/'embedding_snapshot.json'),threads=2)
    pixels=PixelConfig(**runtime.read(assets/'pixel_config.json'))
    runtime.write(root/'JUDGE_LOADED.json',dict(pid=os.getpid(),unix=time.time(),top_k=50,reference_count=64,
        rule_sha256=RULE_SHA,panel_sha256=PANEL_SHA,scalar=scalar.reference,fresh_development_panels=True,
        panel_origin='EXACT_ORIGINAL_R232_BYTES_NOT_RESELECTED_OR_RESCORED',existing_games_modified=False))
    games={}
    while time.time()<deadline:
        for request_path in sorted((root/'queue').glob('*.request.json')):
            output_path=request_path.with_name(request_path.name.replace('.request.json','.result.json'))
            if output_path.exists():
                continue
            request=runtime.read(request_path)
            cell=request['identity']
            condition,seed,contest=cell['condition'],cell['seed'],cell['contest_id']
            data.require(condition==identity['condition'] and seed in contract.SEEDS and
                contest in {item.contest_id for item in manifest.contests},'registered_extension_cell')
            data.require(request['raw_sha256']==hashlib.sha256(request['raw'].encode()).hexdigest()
                and request['origin']['text_sha256']==request['raw_sha256'],'actual_extension_proposal')
            if seed not in games:
                games[seed]=build_game(manifest,scalar,panels,pixels,encoder,top_k=50,
                    agent_id=f'{condition}-{seed}',lane='R232_DEVELOPMENT_EVALUATION',relevance_threshold=rule['relevance_threshold'])
            scene=next(item for item in manifest.contests if item.contest_id==contest)
            actions,parsed=extract_batches(request['raw'],[dict(contest_id=contest,canonical_scene=scene.canonical_scene)],
                active_scene=contest,explicit_candidates_only=request['origin']['stage']=='THINK')
            results=[]
            for action in actions:
                for caption in action['captions']:
                    outcome=games[seed].submit_caption(contest,caption)
                    results.append(dict(caption_sha256=hashlib.sha256(caption.encode()).hexdigest(),result=outcome))
            feedback=[]
            for number,row in enumerate(results,1):
                result=row['result']
                feedback.append(f"Caption {number}: rank {result.get('rank')} of 65; accepted {result.get('accepted')}; "
                    f"novelty {result.get('status')}; relevance {result.get('relevance_score')}; cached {result.get('cached', False)}.")
            if not feedback:
                feedback.append('No caption was scored in this output. Offer the captions themselves for the active scene; no fixed format is required.')
            runtime.write(output_path,dict(request_sha256=contract.digest(request),unix=time.time(),results=results,
                parsed=parsed,feedback='\n'.join(feedback),new_pixels=sum(row['result'].get('status')=='new_pixel'
                    and not row['result'].get('cached',False) for row in results)))
        if (root/'players'/identity['condition']/'COMPLETE.json').exists():
            break
        time.sleep(0.1)
    runtime.write(root/'JUDGE_EXIT.json',dict(unix=time.time(),pid=os.getpid(),independent_games=len(games)))


def player(root,deadline):
    identity=same_battery(root)
    condition=identity['condition']
    freshness=runtime.read(root/'FRESHNESS_VERIFIED.json')
    data.require(freshness['eligible'] is True,'C0_source_exposure_verified')
    manifest=runtime.read(root/'GAME_MANIFEST.json')
    source=runtime.read(root/'sources/CAPTURE.json')['sources'][0]
    data.require(source['source_name']=='C0' and source['absolute_sleep']==identity['absolute_sleep'], 'exact_frozen_C0_cut')
    output=root/'players'/condition
    started=time.time()
    backend=runtime.Backend(source,root)
    runtime.write(output/'LOADED.json',dict(unix=time.time(),pid=os.getpid(),condition=condition,
        model_load_seconds=time.time()-started,source_age=source,identity=backend.identity,
        policy=contract.POLICY,snapshot_context_used=False,actual_visible_device=os.environ['CUDA_VISIBLE_DEVICES']))
    runtime.wait(root/'JUDGE_LOADED.json',deadline)
    results=[]
    for contest in manifest['contests']:
        scene={key:contest[key] for key in ('contest_id','canonical_scene')}
        for seed in contract.SEEDS:
            cell=output/f"{scene['contest_id']}_{seed}"
            counter=0
            def score(raw,stage,origin):
                nonlocal counter
                counter+=1
                key=f"{condition}-{scene['contest_id']}-{seed}-{counter:04d}"
                request=dict(identity=dict(condition=condition,seed=seed,contest_id=scene['contest_id']),
                    raw=raw,raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),origin=origin)
                runtime.write(root/'queue'/f'{key}.request.json',request)
                receipt=runtime.wait(root/'queue'/f'{key}.result.json',deadline)
                data.require(receipt['request_sha256']==contract.digest(request),'actual_bound_extension_feedback')
                return receipt
            def emit(value):
                runtime.write(cell/f'{counter:04d}.json',value)
            result=contract.run_cell(backend,scene,seed,score,emit)
            result.update(contest_id=scene['contest_id'],seed=seed)
            runtime.write(cell/'RESULT.json',result)
            results.append(result)
    runtime.write(output/'COMPLETE.json',dict(unix=time.time(),condition=condition,cells=results,
        actual_generated_tokens=sum(item['generated_tokens'] for item in results),unchanged_identity=backend.verify(),
        elapsed_seconds=time.time()-started,raw_acceptance_not_certified_literal_jokes=True))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--mode',choices=['player','judge'],required=True)
    parser.add_argument('--physical',type=int,required=True)
    parser.add_argument('--deadline',type=float,required=True)
    args=parser.parse_args()
    data.require(0<args.deadline-time.time()<=7200,'bounded_extension_runtime')
    runtime.write(args.root/f'{args.mode}_DEVICE_PROOF.json',runtime.device_proof(args.physical))
    try:
        if args.mode=='judge':
            judge(args.root,args.deadline)
        else:
            player(args.root,args.deadline)
    except Exception as error:
        runtime.write(args.root/f'{args.mode}_FAILED.json',dict(unix=time.time(),error_type=type(error).__name__,error=str(error)))
        raise


if __name__=='__main__':
    main()
