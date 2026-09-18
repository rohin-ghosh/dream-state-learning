"""Spawn exactly one already CPU-verified native supervisor and its tool broker."""

import json
import os
from pathlib import Path
import subprocess
import time


ROOT=Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
PYTHON='/localhome/local-rohing/v2/venv/bin/python'


def main():
    os.umask(0o077)
    (ROOT/'SPAWN_ONCE').mkdir()
    cpu=json.loads((ROOT/'control/RECEIVING_CPU.json').read_bytes())
    if not cpu['passed']:
        raise ValueError('actual_receiving_CPU_required')
    environment=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(ROOT/'source'),PYTHONDONTWRITEBYTECODE='1',TMPDIR='/tmp')
    children={}
    commands=dict(broker=[PYTHON,'-B','-m','research_loop.workers.rohin183_repo_learning_20260917.broker','--config',str(ROOT/'TOOLS.json')],
        supervisor=[PYTHON,'-B','-m','research_loop.workers.rohin183_repo_learning_20260917.confinement','dispatch','--config',str(ROOT/'control/GUARD.json')])
    for name,argv in commands.items():
        with (ROOT/(name.upper()+'.log')).open('x') as log:
            process=subprocess.Popen(argv,cwd=ROOT/'source',env=environment,stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        ticks=Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
        children[name]=dict(pid=process.pid,startticks=ticks,argv=argv)
    receipt=dict(schema='R183_CHILD_SERVICES_SPAWNED_V1',spawned_unix=time.time(),processes=children,
        child_loaded_verified=False,first_read_verified=False,parent_started=False)
    with (ROOT/'SERVICES_SPAWNED.json').open('x') as output:
        json.dump(receipt,output,sort_keys=True)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    main()
