"""Versioned recovery broker: atomic parent publication, unchanged old policy."""

import argparse
from pathlib import Path
import shlex

from gpu import orch_r109_grid_broker as old


ATOMIC_WRITE = ('import pathlib,sys,os; p=pathlib.Path(sys.argv[1]); '
    'p.parent.mkdir(parents=True,exist_ok=True); '
    't=p.with_name(p.name+".atomic-"+str(os.getpid())); '
    'f=t.open("xb"); f.write(sys.stdin.buffer.read()); f.flush(); os.fsync(f.fileno()); f.close(); '
    'os.link(t,p); t.unlink()')


class AtomicStore(old.Store):
    def write(self,path,value):
        self.shell('python3 -c '+shlex.quote(ATOMIC_WRITE)+' '+shlex.quote(str(path)),
            old.json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode())

    def exists(self,path):
        if Path(path)==old.ROOT/'TERMINAL.json':
            path=old.ROOT/'RECOVERY_V3_TERMINAL.json'
        return super().exists(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--wrappers',type=Path,required=True)
    parser.add_argument('--buffer',type=Path,required=True)
    args=parser.parse_args()
    old.require(old.sha(old.__file__)=='23d6c95699f0416b4b87416846f30ce694b0b353c1034ef26f24cbebe29d036a',
        'exact_old_broker_source')
    old.Store=AtomicStore
    old.serve(args.wrappers,'ovx',args.buffer)
