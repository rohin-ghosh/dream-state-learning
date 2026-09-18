"""Public live receipts and requested aggregate diagnostics; no private examples."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess

from observe_r209 import save


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import datetime,hashlib,json,pathlib,os,subprocess
result=dict(schema='R210_LIVE_TRAINING_RECEIPT_V1',observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=[],node2_operations=0,node2_owner='Jason',aggregate_diagnostics_only=True)
def diagnostic(directory,phase,rank):
 complete=directory/'COMPLETE.json'
 if not complete.exists():return None
 receipt=json.loads(complete.read_bytes());contrast=json.loads((directory/'CONTRAST.private.json').read_bytes());selection=json.loads((directory/'SPEARMAN.private.json').read_bytes())
 return dict(phase=phase,rank=rank,checkpoint=directory.name,optimizer_step=receipt['optimizer_step'],completed_utc=receipt['completed_utc'],selection_Spearman=selection['macro_mean_rating_spearman'],case_ids_sha256=contrast['case_ids_sha256'],contrast_by_type={kind:{key:values[key] for key in ['scored','wins','ties','losses','tie_half_accuracy']} for kind,values in contrast['by_type'].items()},source_receipt=str(complete),private_examples_exported=False)
for rank in [8,16]:
 prior=pathlib.Path(f'/localhome/local-rohing/orch_r209_ovx5_allpair1m_rank{rank}_20260918_candidate1')
 root=pathlib.Path(f'/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank{rank}_20260918_continuation1')
 retry=pathlib.Path(f'/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank{rank}_20260918_continuation2')
 if (retry/'DISPATCH_ATTEMPT.json').exists():root=retry
 row=dict(rank=rank,root=str(root),receipts={},native_processes=[],diagnostics=[])
 names=['RECEIVING_CPU.json','R210_TRANSITION.json','CONFINEMENT_CPU.json','ADMISSION.json','BLOCKED_ADMISSION.json','OUTER_EXIT.json','training/LOADED.json','training/NEW_MIX_STARTED.json','training/PHASE_STOPPED.json','training/COMPLETED.json']
 for name in names:
  path=root/name
  if path.exists():
   document=json.loads(path.read_bytes())
   if name=='RECEIVING_CPU.json':document={key:document.get(key) for key in ['passed','actual_Torch_CPU_tests','CUDA_initialized','observed_unix','restore_step','new_mix_first_step']}
   row['receipts'][name]=document
 for pattern,label in [('UPDATE_*.json','latest_update'),('ETA_*.json','latest_ETA')]:
  paths=sorted((root/'training').glob(pattern))
  if paths:
   try:row[label]=json.loads(paths[-1].read_bytes())
   except json.JSONDecodeError:
    if len(paths)>1:row[label]=json.loads(paths[-2].read_bytes())
 for process in pathlib.Path('/proc').glob('[0-9]*'):
  try:
   arguments=(process/'cmdline').read_bytes().decode().split('\0');fields=(process/'stat').read_text().rsplit(')',1)[1].split()
   if str(root/'r210_mixed_train.py') in arguments and str(root) in arguments and 'torch.distributed.run' not in arguments and fields[0] not in ['Z','X']:
    row['native_processes'].append(dict(pid=int(process.name),state=fields[0],start_ticks=fields[19]))
  except (OSError,UnicodeDecodeError):pass
 row['live']=len(row['native_processes'])==4 and 'training/NEW_MIX_STARTED.json' in row['receipts'] and 'OUTER_EXIT.json' not in row['receipts']
 row['declared_crossed_fraction']=0.25
 row['trainer_sha256']=hashlib.sha256((root/'r210_mixed_train.py').read_bytes()).hexdigest()
 row['full_state_checkpoints']=[]
 for directory in sorted((root/'training').glob('checkpoint_step_*')):
  complete=directory/'COMPLETE.json'
  receipt=json.loads(complete.read_bytes()) if complete.exists() else {}
  ranks=[]
  for local_rank in range(4):
   metadata=directory/f'RANK_{local_rank}.json'
   state=directory/f'optimizer_rng_rank_{local_rank}.private.pt'
   if metadata.exists() and state.exists() and state.stat().st_size:
    ranks.append(json.loads(metadata.read_bytes()))
  step=receipt.get('optimizer_step',ranks[0]['optimizer_updates'] if ranks else None)
  row['full_state_checkpoints'].append(dict(path=str(directory),optimizer_step=step,complete_receipt_present=complete.exists(),all_four_rank_states_present=len(ranks)==4 and all(item['optimizer_updates']==step for item in ranks),adapter_present=any((directory/'adapter').glob('*.safetensors')),validation='public_rank_step_receipts_and_file_presence_not_tensor_readback'))
 for directory in sorted((prior/'checkpoint_diagnostics').glob('*')):
  if directory.is_dir():
   item=diagnostic(directory,'R209_PRESERVED',rank)
   if item:row['diagnostics'].append(item)
 for directory in sorted((root/'training/checkpoint_diagnostics').glob('*')):
  if directory.is_dir():
   item=diagnostic(directory,'R210_MIX',rank)
   if item:row['diagnostics'].append(item)
 result['arms'].append(row)
result['nvml']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader'],text=True,timeout=15).strip().splitlines()
print(json.dumps(result))
'''


def clarify_continuity(arm):
    transition = arm['receipts']['R210_TRANSITION.json']
    loaded = arm['receipts'].get('training/LOADED.json', {})
    first_mix = arm['receipts'].get('training/NEW_MIX_STARTED.json', {})
    arm['continuity'] = dict(
        description='SAME_CHECKPOINT_MODEL_OPTIMIZER_RNG_RESTORE_WITH_EXPLICIT_R209_REWIND',
        uninterrupted_continuity=False,
        rollback_to_saved_checkpoint=True,
        restored_checkpoint_step=transition['resume_step'],
        discarded_documented_updates=transition['discarded_documented_updates'],
        discarded_documented_pair_draws=transition['discarded_documented_pair_draws'],
        additional_unlogged_completed_updates_bounds=transition['additional_unlogged_completed_updates_bounds'],
        additional_partial_inflight_work_possible=transition['additional_inflight_work_possible'],
        raw_reset_flags_scope='saved_checkpoint_state_not_continuity_from_latest_R209_update',
        original_raw_receipts_preserved=True,
    )
    for field, timestamp in [('loaded_utc', loaded.get('loaded_unix')), ('first_mix_utc', first_mix.get('started_unix'))]:
        arm[field] = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat() if timestamp is not None else None
    update = arm.get('latest_update', {})
    counts = update.get('pair_types', {})
    total = sum(counts.values())
    arm['live_crossed_fraction'] = counts.get('CROSSED_SCENE_ASSUMPTION', 0) / total if arm['live'] and total else None
    arm['live_crossed_fraction_denominator'] = dict(
        scope='latest_completed_R210_update_pair_count_not_loss_weight_or_entire_history',
        optimizer_step=update.get('completed_updates'),
        crossed=counts.get('CROSSED_SCENE_ASSUMPTION'),
        total=total,
    )


def checkpoint_coverage(arm):
    diagnosed = {item['optimizer_step'] for item in arm['diagnostics'] if item['phase'] == 'R210_MIX'
        and len(item['contrast_by_type']) == 6
        and all(values['scored'] == 100 for values in item['contrast_by_type'].values())
        and item.get('selection_Spearman') is not None}
    saved = [item for item in arm['full_state_checkpoints']
        if item['all_four_rank_states_present'] and item['adapter_present']]
    arm['checkpoint_diagnostic_coverage'] = dict(
        observed_checkpoint_directories=len(arm['full_state_checkpoints']),
        full_states_present=len(saved),
        diagnosed_full_states=sum(item['optimizer_step'] in diagnosed for item in saved),
        saved_steps_without_complete_diagnostics=[item['optimizer_step'] for item in saved if item['optimizer_step'] not in diagnosed],
        incomplete_state_directories=[item['path'] for item in arm['full_state_checkpoints'] if item not in saved],
        required_diagnostics='selection_Spearman_and_same600_cases_100_per_six_types',
        pending_receipt_is_not_launch_authorization=True,
    )


def replace(path, document):
    content=json.dumps(document,indent=2,sort_keys=True)+'\n'
    if not path.exists():
        save(path,document)
        return
    patch='*** Begin Patch\n*** Update File: '+str(path)+'\n@@\n'+''.join('-'+line+'\n' for line in path.read_text().splitlines())
    patch+=''.join('+'+line+'\n' for line in content.splitlines())+'*** End Patch\n'
    subprocess.run(['apply_patch'],input=patch,text=True,capture_output=True,check=True)


def main():
    result=subprocess.run(['bash','gpu/ovx5_ssh.sh','/usr/bin/python3 -B -c '+shlex.quote(REMOTE)],capture_output=True,text=True,check=True,timeout=40)
    document=json.loads(result.stdout)
    for arm in document['arms']:
        clarify_continuity(arm)
        checkpoint_coverage(arm)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=HERE/('R210_OBSERVATION_'+stamp+'.json')
    save(target,document)
    replace(HERE/'R210_STATUS.json',document)
    for arm in document['arms']:
        print(json.dumps({key:arm.get(key) for key in ['rank','root','live','native_processes','live_crossed_fraction','latest_update','latest_ETA','diagnostics']}))
    print('SAVED',target)


if __name__=='__main__':
    main()
