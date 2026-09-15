"""Prospective A3 HTTP broker terminal routing after exact Main shared adoption."""

import argparse
import json
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r108_code_parent_r115_astra as astra


ROOT=Path('/localhome/local-rohing/orch_r108_code_parent_r115_node5_6_20260915_attempt1')


def terminal_path(path,root=ROOT):
    path=Path(path)
    return root/'SHARED_TERMINAL.json' if path==root/'TERMINAL.json' else path


def verify_gate(store,config,launch):
    astra.transport.require(config['remote_root']==str(ROOT),'own_A3_shared_broker_only')
    reference=launch['shared_activation']
    astra.transport.require(reference['path']==str(ROOT/'SHARED_ACTIVATION.json')
        and store.hash(reference['path'])==reference['sha256'],'explicit_actual_shared_activation')
    script='''import pathlib,json,hashlib
path=pathlib.Path(PATH)
read=lambda item:json.loads(pathlib.Path(item).read_text())
sha=lambda item:hashlib.sha256(pathlib.Path(item).read_bytes()).hexdigest()
activation=read(path)
assert activation['schema']=='R118_CODE_ACTIVATION_V1'
binding=activation['shared_learner']
assert binding['branch']=='A3'
assert sha(activation['initialization']['path'])==activation['initialization']['sha256']
initialized=read(activation['initialization']['path'])
assert initialized['schema']=='R118_SHARED_INITIALIZED_V1' and initialized['bindings']['A3']==binding
assert sha(binding['adoption_path'])==binding['adoption_sha256']
assert sha(pathlib.Path(binding['root'])/'CONFIG.json')==binding['config_sha256']
assert read(pathlib.Path(binding['root'])/'CONFIG.json')['owner']=='F1'
print('BOUND_MAIN_ADOPTION')
'''.replace('PATH',repr(reference['path']))
    astra.transport.require(store.shell('python3 -c '+shlex.quote(script)).stdout.strip()=='BOUND_MAIN_ADOPTION',
        'actual_Main_adoption_precedes_broker')


def serve(config_path,launch_path,prompt_root,principles_path):
    config=astra.transport.loads(Path(config_path).read_text())
    launch=astra.transport.loads(Path(launch_path).read_text())
    store=astra.transport.Store(astra.transport.ROOT)
    verify_gate(store,config,launch)

    class SharedStore(astra.transport.Store):
        def exists(self,path):
            return super().exists(terminal_path(path))

    namespace=dict(astra.transport.serve.__globals__,evaluate=astra.evaluate,
        validate_launch=astra.authorize,Store=SharedStore)
    namespace['process_request']=FunctionType(astra.transport.process_request.__code__,namespace,
        'process_request',astra.transport.process_request.__defaults__)
    FunctionType(astra.transport.serve.__code__,namespace,'serve',astra.transport.serve.__defaults__)(
        config_path,launch_path,prompt_root,principles_path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--prompt-root',type=Path,required=True)
    parser.add_argument('--principles',type=Path,required=True)
    args=parser.parse_args()
    serve(args.config,args.launch_receipt,args.prompt_root,args.principles)
