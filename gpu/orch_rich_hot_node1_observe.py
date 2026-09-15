"""Read-only native snapshots and continuity checks for the rolling deployment."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import time

from gpu.orch_rich_hot_node1_roll import ORIGINAL, REVISED, floor, remote


COLLECT = r'''
from pathlib import Path
import hashlib,json,time
root=Path(ROOT)
files={}
def capture(path):
 if path.exists():files[str(path.relative_to(root))]=path.read_text()
for pattern in ('CHECKPOINT_*.json','V1_RELEASE_*.json','ADMISSION_*.json','LAUNCH_*.json',
 'PREPARED.json','PROVENANCE.json','CONTINUATION.json','LIFETIME.json','SOURCE_SHA256.json',
 'PROTOCOL.json','PUBLICATION.json','LEASE.json'):
 for path in root.glob(pattern):capture(path)
summary=[]
for index in INDICES:
 directory=root/f'shard{index}'
 for name in ('ACTOR_READY.json','PROGRESS.json','RESULT.json','FAILED.json'):
  capture(directory/name)
 paths=sorted(path for path in directory.glob('CALL_*.json') if path.stem[5:].isdigit())
 rows=[json.loads(path.read_text()) for path in paths]
 for path in paths[:8]:capture(path)
 entry=dict(index=index,calls=len(rows),failed_calls=len(list(directory.glob('CALL_*_FAILED.json'))),
  progress=json.loads((directory/'PROGRESS.json').read_text()) if (directory/'PROGRESS.json').exists() else None,
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
 if ORIGINAL:
  checkpoint_path=root/f'CHECKPOINT_{index}.json'
  if checkpoint_path.exists():
   checkpoint=json.loads(checkpoint_path.read_text())
   original=Path(ORIGINAL)
   entry['v1_preserved']=all(hashlib.sha256((original/path).read_bytes()).hexdigest()==expected
    for path,expected in checkpoint['files'].items())
   entry['v1_completed_tasks']=len(checkpoint['completed_tasks'])
   entry['overlap_task_ids']=sorted(set(checkpoint['completed_tasks']) & {row['task_id'] for row in rows})
   entry['v1_unfinished_calls']=checkpoint['unfinished_calls']
   entry['v1_pending_pairs']=checkpoint['pending_source_second_pass_pairs']
  entry['phase_versions']=sorted({row.get('phase_version','MISSING') for row in rows})
  entry['within_token_limits']=all(row['max_new_tokens']==8192 and
    row['response']['prompt_tokens']+len(row['response']['token_ids'])<=16384 for row in rows)
 summary.append(entry)
ledger=Path(LEDGER)/'CALL_RESERVATIONS.jsonl'
reservations=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
result=dict(observed_unix=time.time(),root=ROOT,summary=summary,files=files,
 ledger_count=len(reservations),ledger_ids_contiguous=[row['global_call'] for row in reservations]==list(range(1,len(reservations)+1)))
if ORIGINAL:
 result['lifetime_identical']=(root/'LIFETIME.json').read_bytes()==(Path(ORIGINAL)/'LIFETIME.json').read_bytes()
print(json.dumps(result))
'''


def snapshot(output):
    output.mkdir(exist_ok=False)
    manifest = dict(observed_unix=time.time(), floor=floor(), nodes={})
    for name, wrapper, root, indices, original, ledger in [
        ('node1', 'gpu/a40r_ssh.sh', REVISED, list(range(8)), ORIGINAL, ORIGINAL),
        ('node3', 'gpu/ovx2_ssh.sh', '/localhome/local-rohing/orch_rich_hot_node3_20260915_route_v2',
         [3, 4, 5], None, '/localhome/local-rohing/orch_rich_hot_node3_20260915_attempt1'),
    ]:
        config = dict(ROOT=root, INDICES=indices, ORIGINAL=original, LEDGER=ledger)
        code = '\n'.join(key + '=' + repr(value) for key, value in config.items()) + '\n' + COLLECT
        result = json.loads(remote(wrapper, 'python3 -c ' + shlex.quote(code), timeout=120))
        files = result.pop('files')
        result['files'] = {}
        for relative, content in files.items():
            path = output / name / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            data = content.encode()
            with path.open('xb') as stream:
                stream.write(data)
            result['files'][relative] = hashlib.sha256(data).hexdigest()
        manifest['nodes'][name] = result
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(json.dumps({name: {key: value for key, value in result.items() if key != 'files'}
        for name, result in manifest['nodes'].items()}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    snapshot(parser.parse_args().output)
