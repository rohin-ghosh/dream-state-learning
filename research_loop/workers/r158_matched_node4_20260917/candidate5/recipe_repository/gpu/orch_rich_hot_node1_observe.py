"""Metadata-only observations; raw captures remain on their generation nodes."""

import argparse
import json
from pathlib import Path
import shlex
import time

from gpu.orch_rich_hot_node1_roll import ORIGINAL, REVISED, floor, remote


MAX_MANIFEST_BYTES = 512 * 1024
RAW_KEYS = {'files', 'raw', 'messages', 'response', 'token_ids', 'content', 'task'}


def require_metadata_only(value):
    if isinstance(value, dict):
        if RAW_KEYS.intersection(value):
            raise ValueError('raw_payload_forbidden_in_vm_observation')
        for nested in value.values():
            require_metadata_only(nested)
    elif isinstance(value, list):
        for nested in value:
            require_metadata_only(nested)


COLLECT = r'''
from pathlib import Path
import fcntl,hashlib,json,time
root=Path(ROOT)
remote_files={}
def capture(path):
 if path.exists():
  digest=hashlib.sha256()
  with path.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
  remote_files[str(path.relative_to(root))]=dict(sha256=digest.hexdigest(),bytes=path.stat().st_size)
for pattern in ('CHECKPOINT_*.json','V1_RELEASE_*.json','ADMISSION_*.json','LAUNCH_*.json',
 'PREPARED.json','PROVENANCE.json','CONTINUATION.json','LIFETIME.json','SOURCE_SHA256.json',
 'PROTOCOL.json','PUBLICATION.json','LEASE.json','guard_7_FAILED_TRANSIENT01.log'):
 for path in root.glob(pattern):capture(path)
summary=[]
for index in INDICES:
 directory=root/f'shard{index}'
 for name in ('ACTOR_READY.json','PROGRESS.json','RESULT.json','FAILED.json'):
  capture(directory/name)
 paths=sorted(path for path in directory.glob('CALL_*.json') if path.stem[5:].isdigit())
 rows=[json.loads(path.read_text()) for path in paths]
 for path in paths[:8]:capture(path)
 for path in paths[:8]:
  row=json.loads(path.read_text())
  if row.get('episode_receipt'):capture(directory/row['episode_receipt'])
 progress=json.loads((directory/'PROGRESS.json').read_text()) if (directory/'PROGRESS.json').exists() else None
 if progress is not None:
  progress={key:value for key,value in progress.items() if key in ('index','calls','batch','condition','stage',
   'phase_version','generated_tokens','category','task_id','updated_unix') and isinstance(value,(str,int,float,bool,type(None)))}
 entry=dict(index=index,calls=len(rows),failed_calls=len(list(directory.glob('CALL_*_FAILED.json'))),
  progress=progress,
  complete=(directory/'RESULT.json').exists(),failed=(directory/'FAILED.json').exists())
 launch=root/f'LAUNCH_{index}.json'
 if launch.exists():
  record=json.loads(launch.read_text());identity=record.get('identity',record);pid=identity['pid']
  process=Path('/proc')/str(pid)
  try:
   command=(process/'cmdline').read_bytes()
   entry['pid']=pid
   entry['live_owned']=str(root).encode() in command and b'rich_hot_' in command and (
    'start_ticks' not in identity or (process/'stat').read_text().rsplit(')',1)[1].split()[19]==identity['start_ticks'])
  except (FileNotFoundError,ProcessLookupError):entry['live_owned']=False
 if rows:
  entry.update(first_started=min(row['started_unix'] for row in rows),
   last_finished=max(row['finished_unix'] for row in rows))
  entry['raw_calls_per_hour_observed']=len(rows)*3600/(entry['last_finished']-entry['first_started'])
  entry['content_tokens']=sum(len(row['response']['token_ids'])-int(row['response']['terminal']) for row in rows)
  entry['oracle_correct_calls']=sum(row.get('outcome',{}).get('correct',False) for row in rows) if ORIGINAL else None
  entry['phase_versions']=sorted({row.get('phase_version','MISSING') for row in rows})
 if not ORIGINAL:
  episodes=[json.loads(path.read_text()) for path in directory.glob('EPISODE_*.json')]
  entry['completed_episodes']=len(episodes)
  entry['verifier_correct_episodes']=sum(row['correct'] for row in episodes)
  entry['distinct_raw_texts']=len({row['response']['raw'] for row in rows})
 if ORIGINAL:
  checkpoint_path=root/f'CHECKPOINT_{index}.json'
  if checkpoint_path.exists():
   checkpoint=json.loads(checkpoint_path.read_text())
   original=Path(ORIGINAL)
   entry['v1_preserved']=all(hashlib.sha256((original/path).read_bytes()).hexdigest()==expected
    for path,expected in checkpoint['files'].items())
   entry['v1_completed_tasks']=len(checkpoint['completed_tasks'])
   entry['overlap_task_count']=len(set(checkpoint['completed_tasks']) & {row['task_id'] for row in rows})
   entry['v1_unfinished_call_count']=len(checkpoint['unfinished_calls'])
   entry['v1_pending_pair_count']=len(checkpoint['pending_source_second_pass_pairs'])
  entry['phase_versions']=sorted({row.get('phase_version','MISSING') for row in rows})
  entry['within_token_limits']=all(row['max_new_tokens']==8192 and
    row['response']['prompt_tokens']+len(row['response']['token_ids'])<=16384 for row in rows)
 summary.append(entry)
ledger=Path(LEDGER)/'CALL_RESERVATIONS.jsonl'
with ledger.open() as stream:
 fcntl.flock(stream,fcntl.LOCK_SH)
 reservation_ids=[json.loads(line)['global_call'] for line in stream if line.strip()]
result=dict(observed_unix=time.time(),root=ROOT,summary=summary,remote_files=remote_files,
 raw_storage='GENERATION_NODE_ONLY_NO_VM_COPY',
 ledger_count=len(reservation_ids),ledger_ids_contiguous=reservation_ids==list(range(1,len(reservation_ids)+1)))
if ORIGINAL:
 result['lifetime_identical']=(root/'LIFETIME.json').read_bytes()==(Path(ORIGINAL)/'LIFETIME.json').read_bytes()
print(json.dumps(result))
'''


def snapshot(output):
    output.mkdir(exist_ok=False)
    manifest = dict(schema='RICH_HOT_METADATA_ONLY_V1', observed_unix=time.time(), floor=floor(), nodes={},
                    raw_storage='GENERATION_NODE_ONLY_NO_VM_COPY')
    for name, wrapper, root, indices, original, ledger in [
        ('node1', 'gpu/a40r_ssh.sh', REVISED, list(range(8)), ORIGINAL, ORIGINAL),
        ('node3', 'gpu/ovx2_ssh.sh', '/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2',
         [3, 4, 5], None, '/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1'),
        ('node3_batch02', 'gpu/ovx2_ssh.sh', '/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2_batch02',
         [3, 4, 5], None, '/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1'),
        ('node3_batch03', 'gpu/ovx2_ssh.sh', '/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2_batch03',
         [3, 4, 5], None, '/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1'),
    ]:
        config = dict(ROOT=root, INDICES=indices, ORIGINAL=original, LEDGER=ledger)
        code = '\n'.join(key + '=' + repr(value) for key, value in config.items()) + '\n' + COLLECT
        result = json.loads(remote(wrapper, 'python3 -c ' + shlex.quote(code), timeout=120))
        require_metadata_only(result)
        manifest['nodes'][name] = result
    require_metadata_only(manifest)
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ValueError('compact_manifest_size_limit')
    with (output / 'MANIFEST.json').open('xb') as stream:
        stream.write(encoded)
    print(json.dumps(dict(manifest=str(output / 'MANIFEST.json'), bytes=len(encoded),
                         node_count=len(manifest['nodes']), raw_files_copied=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    snapshot(parser.parse_args().output)
