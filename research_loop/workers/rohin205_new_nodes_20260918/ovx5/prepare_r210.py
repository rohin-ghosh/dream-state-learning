"""Prepare exact pilot-state continuations; never stop an owner or expose private rows."""

import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from ddp_pilot import require, sha, write


STAGE = Path(__file__).resolve().parent


def main():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import torch
    os.umask(0o077)
    for rank in [8, 16]:
        prior = Path(f'/localhome/local-rohing/orch_r209_ovx5_allpair1m_rank{rank}_20260918_candidate1')
        root = Path(f'/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank{rank}_20260918_continuation1')
        root.mkdir(mode=0o700)
        packet = json.loads((prior/'PACKET.json').read_bytes())
        old = json.loads((prior/'PILOT_CONFIG.json').read_bytes())
        for name, reference in packet['files'].items():
            require(sha(prior/name) == reference['sha256'], 'exact_frozen_TRAIN_and_source')
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(prior/name, target)
        for name in ['PACKET.json','BASE_MANIFEST.source.json','SELECTION_ROWS.private.jsonl','ddp_pilot.py']:
            shutil.copy2(prior/name, root/name)
        for name in ['r210_mixed_train.py','four_gpu_admission.py','test_r210_mixed_train.py','test_ddp_pilot.py']:
            shutil.copy2(STAGE/name, root/name)
        for name in ['ny_caption_contrast.py','ny_caption_scalar_judge.py']:
            require(not (root/'gpu'/name).exists(), 'new_diagnostic_source_not_overwriting_packet_links')
            shutil.copy2(STAGE/'gpu'/name, root/'gpu'/name)
        os.link(STAGE/'CASES.private.json', root/'CASES.private.json')
        checkpoint = prior/'training/pilot_checkpoint'
        shutil.copytree(checkpoint, root/'resume_checkpoint', copy_function=os.link)
        manifest = {str(path.relative_to(checkpoint)):sha(path) for path in checkpoint.rglob('*') if path.is_file()}
        write(root/'CHECKPOINT_MANIFEST.json',dict(source=str(checkpoint),files=manifest))
        steps = []
        for local_rank in range(4):
            path=root/'resume_checkpoint'/f'optimizer_rng_rank_{local_rank}.private.pt'
            receipt=json.loads((checkpoint/f'RANK_{local_rank}.json').read_bytes())
            require(sha(path)==receipt['optimizer_sha256'],'saved_optimizer_RNG_receipt_hash')
            payload=torch.load(path,map_location='cpu',weights_only=False)
            step=payload['completed_updates'];steps.append(step)
            require(payload['global_pair_cursor']==step*64,'saved_sampler_cursor')
            require({int(value['step'].item()) for value in payload['optimizer']['state'].values()}=={step},'saved_real_AdamW_steps')
        require(len(set(steps))==1 and not torch.cuda.is_initialized(),'all_ranks_same_complete_step_CPU_only')
        pinned=['PACKET.json','BASE_MANIFEST.source.json','ddp_pilot.py','r210_mixed_train.py','four_gpu_admission.py',
            'SELECTION_ROWS.private.jsonl','CASES.private.json','CHECKPOINT_MANIFEST.json','gpu/ny_caption_contrast.py','gpu/ny_caption_scalar_judge.py']
        pinned += ['resume_checkpoint/'+name for name in manifest]
        config=dict(old,schema='R210_EXACT_STATE_CROSSED_SCENE_CONTINUATION_V1',entrypoint='r210_mixed_train.py',
            unit_prefix=f'orch-r210-ovx5-mixed-rank{rank}-continuation1-',pilot_end_unix=time.time()+3600,
            runtime_max_seconds=int(old['training_end_unix']-time.time()),source_pin={name:sha(root/name) for name in pinned},
            prior_root=str(prior),resume_step=steps[0],checkpoint_manifest_sha256=sha(root/'CHECKPOINT_MANIFEST.json'),
            fresh_optimizer_at_candidate_birth=False,phase='R210_EXACT_OPTIMIZER_RNG_CONTINUATION',
            new_candidate=False,mixture=dict(global_pairs=64,within_pairs=48,crossed_pairs=16,
                per_rank_pairs=16,per_rank_crossed_pairs=4,donor_strength='top20pct_by_empirical_mean_then_votes_within_TRAIN_contest',
                positive_strength='same_top20pct_rule',different_scene_groups=True,
                reliability='min_source_votes_cap100_not_observed_relevance',negative_label='CONSTRUCTED_ASSUMPTION_NOT_PROOF'),
            checkpoints='first_new_mix_update,every1000,3907,7813,11719,15625,and_requested_safe_boundary',
            diagnostics='same600_case_digest_and_modelselection_Spearman_every_checkpoint_including_nonimprovements',
            scientific_comparison_caveat='same_mix_rank8_resumes145_rank16_resumes144_not_identical_retained_prefix_lengths')
        write(root/'PILOT_CONFIG.json',config)
        result=subprocess.run([sys.executable,'-B',str(root/'test_r210_mixed_train.py')],cwd=root,capture_output=True,text=True,check=False,timeout=60)
        (root/'RECEIVING_CPU.log').write_text(result.stdout+result.stderr)
        require(result.returncode==0 and 'skipped' not in result.stderr,'five_actual_receiving_tests_no_skips')
        write(root/'RECEIVING_CPU.json',dict(passed=True,actual_Torch_CPU_tests=5,CUDA_initialized=False,
            observed_unix=time.time(),config_sha256=sha(root/'PILOT_CONFIG.json'),all4_rank_checkpoint_states_verified=True,
            restore_step=steps[0],new_mix_first_step=steps[0]+1,source_pin=config['source_pin']))
        print(json.dumps(dict(root=str(root),rank=rank,status='CPU_READY_NOT_LIVE',resume_step=steps[0],first_mix_step=steps[0]+1,config_sha256=sha(root/'PILOT_CONFIG.json'))),flush=True)


if __name__ == '__main__':
    main()
