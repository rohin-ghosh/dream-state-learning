"""Bounded exhaustion reductions; never transport native raw call payloads."""

import argparse
import json
from pathlib import Path
import shlex
import time

from gpu.orch_rich_hot_node1_exhaustion_roll import remote
from gpu.orch_rich_hot_node1_observe import MAX_MANIFEST_BYTES, require_metadata_only


COLLECT = r'''
from collections import Counter
from pathlib import Path
import fcntl, hashlib, json, os, time
root=Path(ROOT)
now=time.time()
def metadata(path):
 return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
summary=[]
for index in INDICES:
 shard=root/f'shard{index}'
 paths=sorted(path for path in shard.glob('CALL_*.json') if path.stem[5:].isdigit())
 rows=[json.loads(path.read_text()) for path in paths]
 entry=dict(index=index,calls=len(rows),failed_calls=len(list(shard.glob('CALL_*_FAILED.json'))),
  worker_failed=(shard/'FAILED.json').exists(),complete=(shard/'RESULT.json').exists(),live=False)
 for candidate in [ROOT]+PREVIOUS:
  launch=Path(candidate)/f'LAUNCH_{index}.json'
  if not launch.exists():continue
  record=json.loads(launch.read_text());identity=record.get('identity',record);pid=identity['pid']
  process=Path('/proc')/str(pid)
  try:
   command=(process/'cmdline').read_bytes()
   if candidate.encode() not in command or b'rich_hot_' not in command:continue
   if 'start_ticks' in identity and (process/'stat').read_text().rsplit(')',1)[1].split()[19]!=identity['start_ticks']:continue
   uuid=record['uuid']
   if ('CUDA_VISIBLE_DEVICES='+uuid).encode() not in (process/'environ').read_bytes().split(b'\0'):continue
   if os.getpgid(pid)!=pid or os.getsid(pid)!=pid:continue
   entry.update(live=True,pid=pid,uuid=uuid,live_root=candidate,phase_version=record.get('phase_version'))
   break
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if rows:
  started=min(row['started_unix'] for row in rows)
  assessments=[row['approach_assessment'] for row in rows]
  entry.update(first_started_unix=started,last_finished_unix=max(row['finished_unix'] for row in rows),
   raw_calls_per_hour_since_start=len(rows)*3600/max(1,now-started),
   content_tokens=sum(len(row['response']['token_ids'])-int(row['response']['terminal']) for row in rows),
   arm=rows[0]['arm'],completed_phase_versions=sorted({row['phase_version'] for row in rows}),
   self_reported_at_least_two=sum((item['self_reported_worked_approach_count'] or 0)>=2 for item in assessments),
   self_reported_rejections=sum(item['self_reported_rejected_approach_count'] for item in assessments),
   missing_approach_self_reports=sum(item['self_reported_worked_approach_count'] is None for item in assessments),
   repetition_flagged_calls=sum(item['repetition_failure_signal'] for item in assessments),
   semantic_verified_worked_approach_count=None,semantic_status='UNREVIEWED',qualified_per_hour=None,
   actual_context_and_output_bounds_pass=all(row['max_new_tokens']==min(16384,32768-row['response']['prompt_tokens'])
    and len(row['response']['token_ids'])<=row['max_new_tokens'] for row in rows))
  stages=sorted({row.get('stage','route_turn') for row in rows})
  entry['stage_counts']={stage:sum(row.get('stage','route_turn')==stage for row in rows) for stage in stages}
  entry['oracle_correct_by_stage']={stage:sum(row.get('outcome',{}).get('correct',False)
   for row in rows if row.get('stage','route_turn')==stage) for stage in stages} if MATH else None
  if MATH:
   sources={row['task_id']:row for row in rows if row.get('stage')=='source'}
   second_passes=[row for row in rows if row.get('stage')=='own_second_pass']
   entry['completed_own_second_pass_pairs']=len(second_passes)
   entry['own_second_pass_content_matches']=all(row['task_id'] in sources and
    [message['content'] for message in row['messages'] if message['role']=='assistant']==
    [sources[row['task_id']]['response']['raw']] for row in second_passes)
   if second_passes:
    second=second_passes[0]
    entry['first_second_pass_budget']=dict(prompt_tokens=second['response']['prompt_tokens'],
     output_cap=second['max_new_tokens'],task_id=second['task_id'],
     content_tokens=len(second['response']['token_ids'])-int(second['response']['terminal']))
  first=rows[0];assessment=first['approach_assessment']
  entry['first_native_proof']=dict(metadata(paths[0]),phase_version=first['phase_version'],arm=first['arm'],
   task_id=first['task_id'],global_call=first['global_call'],finished_unix=first['finished_unix'],
   prompt_tokens=first['response']['prompt_tokens'],output_cap=first['max_new_tokens'],context=32768,
   content_tokens=len(first['response']['token_ids'])-int(first['response']['terminal']),
   output_sha256=hashlib.sha256(first['response']['raw'].encode()).hexdigest(),
   self_reported_worked_approach_count=assessment['self_reported_worked_approach_count'],
   self_reported_rejected_approach_count=assessment['self_reported_rejected_approach_count'],
   repetition_failure_signal=assessment['repetition_failure_signal'],semantic_status='UNREVIEWED')
 checkpoint=root/f'CHECKPOINT_{index}.json'
 if checkpoint.exists():
  record=json.loads(checkpoint.read_text())
  previous=Path(record.get('prior_root',record.get('original_root')))
  entry['prior_captures_hash_preserved']=all(hashlib.sha256((previous/name).read_bytes()).hexdigest()==digest
   for name,digest in record['files'].items())
  entry['safe_boundary']=record.get('safe_episode_boundary',not record.get('unfinished_calls')
   and not record.get('pending_source_second_pass_pairs'))
  entry['completed_task_overlap']=len(set(record.get('completed_tasks',[])) & {row['task_id'] for row in rows}) if MATH else None
  entry['checkpoint']=metadata(checkpoint)
 if not MATH:
  episodes=[json.loads(path.read_text()) for path in shard.glob('EPISODE_*.json')]
  entry.update(completed_episodes=len(episodes),verifier_correct_episodes=sum(row['correct'] for row in episodes))
 summary.append(entry)
ledger=Path(LEDGER)/'CALL_RESERVATIONS.jsonl'
reservations=[]
if ledger.exists():
 with ledger.open() as stream:
  fcntl.flock(stream,fcntl.LOCK_SH)
  reservations=[json.loads(line)['global_call'] for line in stream if line.strip()]
print(json.dumps(dict(root=ROOT,observed_unix=now,summary=summary,reserved_calls=len(reservations),
 ledger_contiguous=reservations==list(range(1,len(reservations)+1)),
 source_manifest=metadata(root/'SOURCE_SHA256.json'),raw_storage='GENERATION_NODE_ONLY')))
'''


def snapshot(output):
    base = '/localhome/local-rohing/orch_rich_hot_'
    configurations = [
        ('node1', 'gpu/a40r_ssh.sh', base + 'node1_20260915_exhaustion_v1', list(range(8)),
         [base + 'node1_20260915_v2'], base + 'node1_20260915_attempt1', True),
        ('node3', 'gpu/ovx2_ssh.sh', base + 'node3_20260915_exhaustion_v1', [3, 4, 5],
         [base + 'node3_20260915_route_v2_batch03', base + 'node3_20260915_route_v2_batch02'],
         base + 'node3_20260915_exhaustion_v1', False),
    ]
    manifest = dict(schema='EXHAUSTION_METADATA_ONLY_V1', observed_unix=time.time(), nodes={})
    for name, wrapper, root, indices, previous, ledger, math in configurations:
        config = dict(ROOT=root, INDICES=indices, PREVIOUS=previous, LEDGER=ledger, MATH=math)
        code = '\n'.join(key + '=' + repr(value) for key, value in config.items()) + '\n' + COLLECT
        result = json.loads(remote(wrapper, 'python3 -c ' + shlex.quote(code), timeout=120))
        require_metadata_only(result)
        manifest['nodes'][name] = result
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ValueError('compact_manifest_size_limit')
    output.mkdir(exist_ok=False)
    with (output / 'MANIFEST.json').open('xb') as stream:
        stream.write(encoded)
    print(json.dumps(dict(manifest=str(output / 'MANIFEST.json'),bytes=len(encoded),raw_files_copied=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    snapshot(parser.parse_args().output)
