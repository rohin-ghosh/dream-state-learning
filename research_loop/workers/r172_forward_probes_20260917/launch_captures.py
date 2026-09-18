"""Start only the four already-budgeted source metadata/capture workers."""

import base64
import hashlib
import json
import os
from pathlib import Path

import prep_common as common
import prepare


def main():
    os.umask(0o077)
    scope,proposal,ledger=prepare.setup()
    source=prepare.HERE/'capture_worker.py'
    checksum=common.ref(source)['sha256']
    freeze={name:common.ref(prepare.HERE/name) for name in ('capture_worker.py','transfer.py')}
    common.write(prepare.PREP/'CAPTURE_SOURCE_FREEZE.json',dict(status='CPU_CAPTURE_SOURCE_FROZEN',files=freeze,
        cpu_log=common.ref(prepare.HERE/'PREPARATION_CPU_04.txt'),model_calls=0))
    for node in ('a100','ovx2','ovx3','a40r'):
        lives=[life['life_id'] for life in proposal['lives'] if life['node']==node
            and (prepare.PREP/'enrollment'/(life['life_id']+'.json')).exists()
            and common.read(prepare.PREP/'enrollment'/(life['life_id']+'.json'))['status']=='REGISTERED_PRIVATE_CUSTODY_NO_GPU_GO']
        payload={name:base64.b64encode((prepare.HERE/name).read_bytes()).decode() for name in freeze}
        request=dict(node=node,lives=lives,source_sha256=checksum)
        ledger.reserve('capture_worker_launch:'+node,'_campaign','metadata',2*prepare.MIB)
        script=f'''import base64,json,os,subprocess,time
from pathlib import Path
os.umask(0o077)
root=Path({str(common.REMOTE_ROOT)!r})
for name,data in {payload!r}.items():
 with (root/'source'/name).open('xb') as stream:stream.write(base64.b64decode(data))
request=root/'requests'/('capture_'+{node!r}+'.json')
with request.open('x') as stream:json.dump({request!r},stream,sort_keys=True)
launch=root/'capture_launches'/{node!r}
launch.mkdir(parents=True,mode=0o700,exist_ok=False)
environment={{'PATH':'/usr/bin:/bin','HOME':os.environ['HOME'],'PYTHONPATH':str(root/'source'),'PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}}
with (launch/'stdout.private.txt').open('xb') as output,(launch/'stderr.private.txt').open('xb') as errors:
 process=subprocess.Popen(['/usr/bin/python3','-B',str(root/'source/capture_worker.py'),'--request',str(request)],cwd=root/'source',env=environment,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,start_new_session=True)
fields=Path(f'/proc/{{process.pid}}/stat').read_text().rsplit(')',1)[1].split()
identity=dict(pid=process.pid,start_ticks=fields[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
result=dict(status='BOUNDED_METADATA_CAPTURE_WORKER_STARTED',node={node!r},lives={len(lives)},identity=identity,observed_unix=time.time(),gpu_calls=0,provider_calls=0)
with (launch/'LAUNCH.json').open('x') as stream:json.dump(result,stream,sort_keys=True)
print(json.dumps(result))
'''
        result=json.loads(prepare.wrapper(node,'capture_launch_'+node,'python3 -B -',script.encode()))
        common.write(prepare.PREP/'capture_launches'/(node+'.json'),result)
        print(json.dumps(result))


if __name__=='__main__':
    main()
