"""Prospective low-effort Astra subparent; existing HTTP slots and immutable claims."""

import argparse
import ast
import inspect
import json
import os
from pathlib import Path
import shlex
import signal
import tempfile
import time
from types import FunctionType

from gpu import orch_r111_route_astra_broker as prior

transport = prior.transport
require = transport.require
ROOT = '/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1'


def runner():
    source = inspect.getsource(prior.existing.strong)
    require(source.count("reasoning=dict(effort=config['model_reasoning_effort'])") == 1,
            'exact_existing_effort_site')
    source = source.replace("reasoning=dict(effort=config['model_reasoning_effort'])", "reasoning=dict(effort='low')")
    require(source.count('max_output_tokens=4096') == 1, 'exact_existing_output_site')
    source = source.replace('max_output_tokens=4096', 'max_output_tokens=512')
    source = source.replace('maximum_output_tokens=4096', 'maximum_output_tokens=512')
    source = source.replace('timeout_seconds=120', 'timeout_seconds=20')
    source = source.replace('min(120, deadline - time.time())', 'min(20, deadline - time.time())')
    namespace = dict(prior.existing.strong.__globals__, parse_strong=prior.parse)
    exec(compile(ast.parse(source), __file__+':bound_low_HTTP', 'exec'), namespace)
    return namespace['strong']


def evaluate(request, directory, deadline, **kwargs):
    started = time.time()
    result = prior.evaluate(request,directory,deadline,runner=runner(),**kwargs)
    result.update(parent_effort='low', output_budget=512, provider_timeout_seconds=20,
                  prospective_provider_era='R119_ASTRA_LOW_NONBLOCKING',
                  elapsed_seconds=time.time()-started)
    transport.write(Path(directory)/'FAST_RECEIPT.json',dict(parent_effort='low',output_budget=512,
        provider_timeout_seconds=20,elapsed_seconds=result['elapsed_seconds'],
        original_result_sha256=transport.sha(Path(directory)/'RESULT.json')))
    return result


def serve(args):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CPU_only_provider')
    config=json.loads(args.config.read_text())
    launch=json.loads(args.launch_receipt.read_text())
    transport.validate_config(config)
    prior.authorize(config,launch,time.time())
    require(config['remote_root']==ROOT and config['parent_effort']=='low'
            and config['max_output_tokens']==512, 'explicit_fast_A1_configuration')
    for name in ('gpu/ovx3_ssh.sh','gpu/ovx3_scp.sh'):
        require(transport.sha(args.repository/name)==transport.sha(transport.ROOT/name), 'authorized_wrapper_bytes')
    store=transport.Store(args.repository)
    plan_path=Path(ROOT)/'R121_INDEPENDENT_PLAN_V2.json'
    require(store.hash(plan_path)==args.plan_sha256, 'actual_native_plan')
    lock=Path(ROOT)/'parent_claude/RUNNER.lock'
    require(store.shell('mkdir '+shlex.quote(str(lock)),check=False).returncode==0, 'exclusive_old_queue_lock')
    def stop(signum,frame):
        raise KeyboardInterrupt('owned_provider_stop')
    signal.signal(signal.SIGTERM,stop)
    namespace=dict(transport.process_request.__globals__,evaluate=evaluate)
    process=FunctionType(transport.process_request.__code__,namespace,'process_request',transport.process_request.__defaults__)
    buffer=Path(tempfile.mkdtemp(prefix='orch_r121_astra_'))
    started=dict(pid=os.getpid(),started_unix=time.time(),plan_sha256=args.plan_sha256,
        config_sha256=transport.sha(args.config),source_sha256=transport.sha(__file__),
        parent_effort='low',max_output_tokens=512,provider_timeout_seconds=20,
        attempts_per_request=1,old_claims_preserved=True,nonblocking_child=True)
    transport.write(args.ready,started)
    with tempfile.TemporaryDirectory(prefix='orch_r121_astra_config_') as temporary:
        path=Path(temporary)/'CONFIG.json'
        transport.write(path,config)
        destination=Path(ROOT)/'parent_claude'/('CONFIG_R121_'+transport.digest(config)+'.json')
        require(not store.exists(destination), 'new_prospective_config_namespace')
        store.copy(path,'NODE:'+str(destination))
    try:
        while time.time()<config['deadline_unix']:
            if store.exists(Path(ROOT)/'R121_INDEPENDENT_TERMINAL.json'):
                break
            require(store.hash(plan_path)==args.plan_sha256, 'plan_not_hotpatched')
            listing=store.shell('find '+shlex.quote(str(Path(ROOT)/'parent_queue'))+
                ' -maxdepth 1 -type f -name "*.request.json" -printf "%f\\n"')
            for name in sorted(listing.stdout.splitlines()):
                process(store,config,launch,name,buffer,args.prompt_root,args.principles)
            time.sleep(.5)
    finally:
        store.shell('rmdir '+shlex.quote(str(lock)),check=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('config','launch-receipt','repository','prompt-root','principles','ready'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--plan-sha256',required=True)
    serve(parser.parse_args())


if __name__=='__main__':
    main()
