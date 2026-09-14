import datetime
import hashlib
import json
import subprocess
import time
from pathlib import Path

root = Path('/tmp/astra_goal_quality_train_20260914_attempt2')
deadline = 1789430064
for observation in range(19):
    jobs = []
    for arm, guardian in [('FULL_TARGET', 86063), ('NEW_TRAJECTORY_LOSS_OFF', 86064)]:
        directory = root / arm
        losses = directory / 'train/LOSSES.jsonl'
        updates = []
        for line in losses.read_text().splitlines()[-202:]:
            try:
                updates.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        receipts = {}
        for phase in ('train', 'after'):
            for name in ('RESULT.json', 'FAILED.json'):
                path = directory / phase / name
                if path.exists():
                    data = json.loads(path.read_text())
                    receipts[f'{phase}/{name}'] = dict(
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        **{key: data.get(key) for key in (
                            'status', 'phase', 'updates', 'model_calls', 'error',
                            'adapter_state_after', 'loaded_adapter_state_sha256',
                            'gpu_assigned_wall_seconds', 'actual_supervised_tokens',
                            'reference_supervised_tokens', 'finished_unix')})
        markers = {}
        for name in ('stage_pids.txt', 'completed_utc.txt', 'GUARD_ABORT.txt', 'deadline_epoch.txt'):
            path = directory / 'launch' / name
            if path.exists():
                markers[name] = path.read_text().strip()
        jobs.append(dict(arm=arm, guardian_pid=guardian,
                         guardian_alive=Path(f'/proc/{guardian}').exists(),
                         last_update=updates[-1], receipts=receipts, markers=markers,
                         after_calls=len(list((directory / 'after').glob('CALL_*.json')))))
    processes = subprocess.check_output(['ps', '-eo', 'pid,ppid,etime,args'], text=True)
    native = [line for line in processes.splitlines()
              if '-m gpu.astra_goal_quality_train ' in line and str(root) in line]
    print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          jobs=jobs, native_processes=native,
                          gpu_processes=subprocess.check_output([
                              'nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_memory',
                              '--format=csv,noheader'], text=True).splitlines())), flush=True)
    if all(not job['guardian_alive'] for job in jobs):
        break
    if any('GUARD_ABORT.txt' in job['markers'] or any('FAILED' in name for name in job['receipts'])
           for job in jobs):
        break
    if time.time() >= deadline:
        break
    time.sleep(300)
