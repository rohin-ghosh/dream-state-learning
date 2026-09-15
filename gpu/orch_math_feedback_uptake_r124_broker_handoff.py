"""Wait for actual A2 release and old broker exit; preserve its queue and claims."""

import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_math_feedback_uptake_r121_astra as custody


SOURCE = Path('/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1')
ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/A2')
OUTPUT = Path('/tmp/orch_math_feedback_uptake_r124_A2_broker_20260915_attempt1')
read, write, sha = custody.base.loads, custody.base.write, custody.base.sha


def ready(released, old_actor_absent, old_broker_absent, lock_absent, successor_plan):
    return all((released, old_actor_absent, old_broker_absent, lock_absent, successor_plan))


def main():
    custody.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    OUTPUT.mkdir(exist_ok=False)
    prior = read((SOURCE/'LAUNCH_R121_ATTEMPT3.json').read_text())
    binding = read((SOURCE/'BINDING_R121_ATTEMPT3.json').read_text())
    store = custody.base.Store(Path(__file__).resolve().parents[1])
    original_root = Path(binding['original_config']['path']).parent.parent
    end = time.time()+3600
    while time.time()<end:
        released = store.exists(ROOT/'RELEASED.json')
        plan_exists = store.exists(ROOT/'PLAN.json')
        old_broker_absent = not Path('/proc',str(prior['identity']['pid'])).exists()
        lock_absent = not store.exists(original_root/'parent_claude/RUNNER.lock')
        old_actor_absent = False
        if released:
            release = read(store.shell('cat '+str(ROOT/'RELEASED.json')).stdout)
            old_actor_absent = store.shell('test ! -e /proc/'+str(release['actor']['pid']),check=False).returncode == 0
        if ready(released,old_actor_absent,old_broker_absent,lock_absent,plan_exists):
            plan = read(store.shell('cat '+str(ROOT/'PLAN.json')).stdout)
            custody.require(plan['branch']=='A2' and plan['index']==5 and plan['original_root']==str(original_root), 'same_A2_queue')
            binding['plan']=dict(path=str(ROOT/'PLAN.json'),sha256=store.hash(ROOT/'PLAN.json'))
            path=OUTPUT/'BINDING.json'
            write(path,binding)
            command=list(prior['argv'])
            command[command.index('--binding')+1]=str(path)
            with (OUTPUT/'BROKER.log').open('x') as log:
                process=subprocess.Popen(command,cwd=SOURCE,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(SOURCE)),
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                write(OUTPUT/'LAUNCH.json',dict(pid=process.pid,argv=command,binding_sha256=sha(path),
                    release_sha256=store.hash(ROOT/'RELEASED.json'),created_unix=time.time(),no_signal=True,
                    old_queue_preserved=True,no_provider_retry=True))
            return
        time.sleep(5)
    write(OUTPUT/'NOT_RUN.json',dict(reason='ACTUAL_RELEASE_OR_BROKER_LOCK_NOT_READY_WITHIN_HOUR',no_signal=True))


if __name__=='__main__':main()
