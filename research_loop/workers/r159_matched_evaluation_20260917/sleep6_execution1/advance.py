import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


DIRECTORY = Path(__file__).resolve().parent
ARMS = ('parented_learning', 'unparented_learning')


def ready_keys(snapshot, now):
    if now >= 1789642780:
        return []
    output = []
    for arm in ARMS:
        for previous,following in ((1,2),(2,4)):
            before = snapshot['keys'][arm+'_'+str(previous)]
            after = snapshot['keys'][arm+'_'+str(following)]
            if (before.get('completion') and before.get('native_gone') is True
                    and before.get('timeout_gone') is True and before.get('wrapper_gone') is True
                    and before.get('DISPOSITION',{}).get('result',{}).get('status') == 'METADATA_ONLY'
                    and not before.get('failed') and not before.get('DISPATCH_ERROR')
                    and after.get('operator_exists') is False):
                output.append(arm+'_'+str(following))
    return output


def command(*args):
    result = subprocess.run([sys.executable,'-B',str(DIRECTORY/'run.py'),*args],
        stdout=subprocess.PIPE,text=True,check=True,timeout=280)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds',type=int,default=120)
    args = parser.parse_args()
    assert 0 < args.seconds <= 300
    end = time.monotonic()+args.seconds
    while True:
        snapshot = command('observe')
        summary = dict(observed_unix=snapshot['observed_unix'],ledger=snapshot['ledger'],keys={key:dict(
            outputs=value.get('output_artifact_count'),complete=bool(value.get('completion')),
            failed=value.get('failed',False),native_gone=value.get('native_gone'),
            refused=value.get('DISPOSITION',{}).get('result',{}).get('status') == 'DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION')
            for key,value in snapshot['keys'].items()})
        print(json.dumps(summary,sort_keys=True),flush=True)
        ready = ready_keys(snapshot,time.time())
        if ready:
            launch = command('dispatch',*ready)
            print(json.dumps(dict(new_once_launch=launch),sort_keys=True),flush=True)
        if all(value.get('completion') and value.get('native_gone') and value.get('timeout_gone')
               and value.get('wrapper_gone') for value in snapshot['keys'].values()):
            break
        if time.monotonic() >= end:
            break
        time.sleep(min(15,max(0,end-time.monotonic())))


if __name__ == '__main__':
    main()
