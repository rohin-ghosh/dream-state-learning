"""Stop only the explicitly identified defective judge service; preserve its files."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from gpu import ny_caption_data as data


REMOTE = '''import hashlib,json,subprocess,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v4')
unit='orch-r177-judge-train-ae63319aa8ce8a81968985b3.service'
pid=3941679
ticks='23974474'
def ref(path):
 raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
assert (Path('/proc')/str(pid)/'stat').read_text().split(') ')[1].split()[19]==ticks
assert (Path('/proc')/str(pid)/'cgroup').read_text().strip()=='0::/system.slice/'+unit
actual=subprocess.check_output(['sudo','-n','systemctl','show',unit,'--property=MainPID','--value'],text=True).strip()
assert actual==str(pid)
checkpoint=root/'training/checkpoints/step_000100'
preserved={name:ref(checkpoint/name) for name in ['humor/model.safetensors','scene_fit/model.safetensors']}
progress=sorted((root/'training/progress').glob('*.json'))[-1]
before=json.loads(progress.read_bytes())
started=json.loads((root/'training/TRAINING_STARTED.json').read_bytes())['started_unix']
requested=time.time()
subprocess.run(['sudo','-n','systemctl','stop',unit],check=True,timeout=20)
assert not Path('/proc',str(pid)).exists()
assert all(ref(Path(item['path']))==item for item in preserved.values())
print(json.dumps(dict(status='STOPPED_OWN_DEFECTIVE_SCENE_FIT_RUN_NOT_PROMOTABLE',unit=unit,pid=pid,startticks=ticks,
 stop_requested_unix=requested,stopped_unix=time.time(),model_loaded_elapsed_seconds=requested-started,
 last_progress=before,progress_ref=ref(progress),preserved_checkpoint_files=preserved,
 exact_final_optimizer_steps_unknown=True,reason='FIRST_DISTINCT_SCENE_NEGATIVE_SAMPLER_SHORTCUT',
 locked_validation_consumed=False,development_audit_started=(root/'training/VALIDATION_ONCE.json').exists(),
 learner_processes_signalled=False,source_or_old_receipts_modified=False)))
'''


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    latch = data.private_write(root/'evidence/V4_STOP_REQUESTED.json', dict(requested_unix=time.time(),
        explicit_user_scope='Stop or finish defective v4 at an existing checkpoint before corrected candidate',
        target_pid=3941679, target_startticks='23974474', no_retry=True))
    result = subprocess.run(['bash', str(root.parents[3]/'gpu/a40r_ssh.sh'), 'python3 -B -c '+shlex.quote(REMOTE)],
        capture_output=True, timeout=35, check=True)
    receipt = data.private_write(root/'evidence/V4_STOPPED_FOR_SAMPLER_REPAIR.json', json.loads(result.stdout))
    print(json.dumps(dict(receipt=receipt, body=json.loads(result.stdout))))
