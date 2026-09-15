"""Existing private Astra broker with exact snapshot and wrapper-only transport."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake_base_broker as existing
from gpu import orch_r107_route_parent_long_broker as old
from gpu.orch_r107_route_parent_long_protocol import parsing_context
from organism_v6 import orch_r109_route as policy


class Store(existing.transport.Store):
    def __init__(self, repository, root, lane):
        super().__init__(repository, root)
        self.host = policy.HOSTS[policy.LANES[lane]['host']]

    def shell(self, command, check=True):
        return subprocess.run(['bash',str(self.repository/self.host['wrapper']),command],
            capture_output=True,text=True,timeout=90,check=check)

    def copy(self, source, destination, recursive=False):
        return subprocess.run(['bash',str(self.repository/self.host['scp'])] + (['-r'] if recursive else []) +
            [str(source),str(destination)],capture_output=True,text=True,timeout=120,check=True)


@contextmanager
def binding(principles):
    previous = existing.policy
    digest = existing.transport.parent.policy.digest
    existing.policy = SimpleNamespace(require=policy.require, validate_parent_payload=policy.validate_parent_payload,
        PARENT_INSTRUCTION=policy.PARENT_INSTRUCTIONS+'\n\nEXACT SHARED PRINCIPLES:\n'+principles)
    existing.transport.parent.policy.digest = policy.digest
    try:
        with existing.parent_context(), parsing_context():
            yield
    finally:
        existing.policy = previous
        existing.transport.parent.policy.digest = digest


def process(store, campaign, path, buffer, receipts, ready_sha, principles, deadline):
    import shutil
    identifier = path.name.removesuffix('.request.json')
    policy.require(re.fullmatch(r'GUIDED_SLEEP_C[1-9][0-9]*_P[1-9][0-9]*',identifier), 'own_parent_identifier')
    response_path = path.with_name(identifier+'.response.json')
    if store.exists(response_path) or store.shell('mkdir '+shlex.quote(str(path)+'.claim'),check=False).returncode:
        return
    policy.require(not any(buffer.iterdir()), 'single_bounded_buffer')
    incoming = buffer/'incoming.json'
    store.copy('NODE:'+str(path),incoming)
    request = existing.transport.parent.read(incoming)
    policy.require(request['ready_sha256'] == ready_sha, 'ready_binding')
    policy.validate_parent_payload(request['payload'])
    directory = buffer/identifier
    status, plan, error = 'FAILED', None, None
    try:
        with binding(principles):
            plan = existing.transport.strong.evaluate(request,directory,{},timeout=min(120,deadline-time.time()))
        status = 'COMPLETE'
    except Exception as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    directory.mkdir(exist_ok=True)
    if not (directory/'REQUEST.json').exists():
        shutil.copyfile(incoming,directory/'REQUEST.json')
    existing.transport.parent.write(directory/'TRANSPORT_RESULT.json',dict(status=status,error=error,finished_unix=time.time()))
    archive = store.archive(directory,campaign.name,identifier)
    response = dict(status=status,plan=plan,error=error,archive=archive,
        request_sha256=existing.transport.parent.sha(incoming),principles_sha256=policy.PRINCIPLES_SHA)
    local = buffer/'response.json'
    existing.transport.parent.write(local,response)
    store.copy(local,'NODE:'+str(response_path)+'.partial')
    observed = store.shell('sha256sum '+shlex.quote(str(response_path)+'.partial')).stdout.split()[0]
    policy.require(observed == existing.transport.parent.sha(local), 'response_hash')
    store.shell('test ! -e '+shlex.quote(str(response_path))+' && mv '+shlex.quote(str(response_path)+'.partial')+' '+shlex.quote(str(response_path)))
    existing.transport.parent.write(receipts/(identifier+'.json'),dict(status=status,archive=archive,
        response_sha256=observed,principles_sha256=policy.PRINCIPLES_SHA,raw_embedded=False))
    shutil.rmtree(directory)
    incoming.unlink()
    local.unlink()


def serve(repository,root,lane,buffer,receipts):
    policy.allocation(lane)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and str(buffer).startswith('/tmp/'),'cpu_bounded_buffer')
    buffer.mkdir(exist_ok=False)
    receipts.mkdir(parents=True,exist_ok=True)
    store = Store(repository,root,lane)
    campaign = root/('campaign_'+lane)
    ready = json.loads(store.shell('cat '+shlex.quote(str(campaign/'READY.json'))).stdout)
    ready_sha = store.shell('sha256sum '+shlex.quote(str(campaign/'READY.json'))).stdout.split()[0]
    policy.require(store.exists(campaign/'PUBLICATION.json'),'published_before_parent')
    principles = (repository/policy.PRINCIPLES_PATH).read_text()
    policy.require(existing.transport.parent.sha(repository/policy.PRINCIPLES_PATH) == policy.PRINCIPLES_SHA,'exact_principles')
    while time.time() < ready['hard_deadline_unix'] and not store.exists(campaign/'TERMINAL.json'):
        for relative,digest in ready['provider_files'].items():
            policy.require(existing.transport.parent.sha(repository/relative) == digest,'provider_source_frozen')
        names = store.shell('find '+shlex.quote(str(campaign/'parent_queue'))+' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
        policy.require(len(names) <= ready['parent_cap'],'bounded_parent_total')
        for name in sorted(names):
            process(store,campaign,Path(name),buffer,receipts,ready_sha,principles,ready['hard_deadline_unix'])
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('repository','root','buffer','receipts'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--lane',required=True,choices=policy.LANES)
    serve(**vars(parser.parse_args()))
