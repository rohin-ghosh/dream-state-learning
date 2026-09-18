"""Log own CPU/provenance and start exactly one finite TRAIN-only parent."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest,require


ROOT=Path(__file__).resolve().parent
REPOSITORY=ROOT.parents[2]


def main():
    os.umask(0o077)
    require(not (ROOT/'PARENT_CONFIG.json').exists(),'fresh_parent_only')
    command=[sys.executable,'-B','-m','unittest','research_loop.workers.rohin183_repo_learning_20260917.test_parent','-q']
    result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR='/tmp'))
    log=write(ROOT/'PARENT_CPU.log',result.stdout.encode())
    require(result.returncode==0,'parent_CPU_gate')
    plan=json.loads((ROOT/'control_bundle/control/PLAN.json').read_bytes())
    config=dict(schema='R183_BOUNDED_ASTRA_PARENT_V1',node='ovx',programme='repo_reader',branch='r183_repo_learning_physical2',
        root=plan['root'],source_root=plan['source_root'],hard_end_unix=plan['hard_end_unix'],maximum_calls=12,
        minimum_call_interval_seconds=300,cadence_responses=3,first_response_threshold=1,
        parent_style='responsive_to_actual_repository_evidence',cadence_label='SPARSE',CPU=log,
        feed_sha256=digest((ROOT/'parent_feed.py').read_bytes()),local_only_credentials=True,
        formal_R184_driver=False)
    for key,name in (('programme','PARENT_PROGRAMME.md'),('principles','PARENT_PRINCIPLES.md')):
        config[key+'_path']=str(ROOT/name)
        config[key+'_sha256']=digest((ROOT/name).read_bytes())
    reference=write(ROOT/'PARENT_CONFIG.json',config)
    with (ROOT/'PARENT_PROCESS.log').open('x') as stream:
        process=subprocess.Popen([sys.executable,'-B','-m','research_loop.workers.rohin183_repo_learning_20260917.parent'],
            cwd=REPOSITORY,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    ticks=Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    print(json.dumps(write(ROOT/'PARENT_SPAWNED.json',dict(pid=process.pid,startticks=ticks,spawned_unix=time.time(),
        config=reference,provider_calls_verified=0,publication_verified=False)),sort_keys=True))


if __name__=='__main__':
    main()
