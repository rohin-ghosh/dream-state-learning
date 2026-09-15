"""One-attempt real Astra broker; verified raw archives live on the owning node."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time

from gpu import orch_route_parent_campaign_providers as provider
from organism_v6 import orch_r109_grid as policy


ROOT = Path('/localhome/local-rohing/orch_r109_grid_20260915_attempt1')
require = policy.require


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Store:
    def __init__(self, wrappers, lane):
        require(lane in policy.LANES, 'allocated_wrapper')
        self.wrapper = Path(wrappers)/'gpu'/f'{lane}_ssh.sh'
        self.wrapper_sha256 = sha(self.wrapper)

    def shell(self, command, data=None, check=True):
        require(sha(self.wrapper) == self.wrapper_sha256, 'wrapper_source_drift')
        return subprocess.run(['bash',str(self.wrapper),command],input=data,capture_output=True,
            timeout=90,check=check)

    def read(self, path):
        return json.loads(self.shell('cat '+shlex.quote(str(path))).stdout)

    def exists(self, path):
        return self.shell('test -f '+shlex.quote(str(path)),check=False).returncode == 0

    def write(self, path, value):
        code = ('import pathlib,sys,os; p=pathlib.Path(sys.argv[1]); '
            'p.parent.mkdir(parents=True,exist_ok=True); '
            'f=p.open("xb"); f.write(sys.stdin.buffer.read()); f.flush(); os.fsync(f.fileno()); f.close()')
        self.shell('python3 -c '+shlex.quote(code)+' '+shlex.quote(str(path)),
            json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode())

    def archive(self, directory, identifier):
        expected = {path.name:sha(path) for path in directory.iterdir() if path.is_file()}
        destination = ROOT/'parent_transcripts'/identifier
        require(expected and all(Path(name).name == name for name in expected), 'flat_archive')
        self.shell('mkdir -p '+shlex.quote(str(destination)))
        for name, digest in expected.items():
            code = ('import pathlib,sys,os; p=pathlib.Path(sys.argv[1]); '
                'f=p.open("xb"); f.write(sys.stdin.buffer.read()); f.flush(); os.fsync(f.fileno()); f.close()')
            self.shell('python3 -c '+shlex.quote(code)+' '+shlex.quote(str(destination/name)),(directory/name).read_bytes())
        output = self.shell('sha256sum '+' '.join(shlex.quote(str(destination/name)) for name in sorted(expected))).stdout.decode()
        actual = {Path(line.split(maxsplit=1)[1]).name:line.split()[0] for line in output.splitlines()}
        require(actual == expected,'node_archive_hashes_before_local_cleanup')
        return str(destination), expected


def validate_request(request, ready_sha256, train_ids):
    require(set(request) == {'id','payload','payload_sha256','source_proposal','ready_sha256'}, 'exact_request_schema')
    identifier = request['id']
    require(isinstance(identifier,str) and len(identifier) == 5 and identifier[0] == 'P'
        and identifier[1:].isdigit() and 1 <= int(identifier[1:]) <= policy.bounds()['parent_per_lane'], 'request_budget')
    require(request['ready_sha256'] == ready_sha256 and request['payload_sha256'] == policy.digest(request['payload']),
        'request_source_binding')
    payload = request['payload']
    require(payload['task_id'] in train_ids and payload['split'] == 'TRAIN', 'known_train_request_only')
    policy.validate_parent(payload,dict(speak=False,message='',rationale='reflection: input validation'))
    path = Path(request['source_proposal']['path'])
    require(path.is_absolute() and path.parent == ROOT/'calls' and path.name.startswith('N') and path.suffix == '.json',
        'source_native_call_scope')
    return identifier


def process(store, request, ready_sha256, train_ids, buffer):
    identifier = validate_request(request,ready_sha256,train_ids)
    response_path = ROOT/'parent_queue'/(identifier+'.response.json')
    if store.exists(response_path):
        return 'already_complete_or_failed'
    claim = store.shell('mkdir '+shlex.quote(str(ROOT/'parent_claims'/identifier)),check=False)
    if claim.returncode:
        return 'already_claimed_no_redispatch'
    require(time.time() < policy.NATIVE_END-120,'parent_dispatch_cutoff')
    source_path = Path(request['source_proposal']['path'])
    observed_sha = store.shell('sha256sum '+shlex.quote(str(source_path))).stdout.decode().split()[0]
    require(observed_sha == request['source_proposal']['sha256'],'native_proposal_file_hash')
    source = store.read(source_path)
    require(source['status'] == 'COMPLETE' and source['split'] == 'TRAIN'
        and source['task_id'] == request['payload']['task_id'] and source['adapter'] is None
        and source['base_sha256'] == policy.BASE_SHA and source['response']['raw'] == request['payload']['child_proposal'],
        'actual_child_proposal_join')
    directory = Path(tempfile.mkdtemp(prefix=identifier+'_',dir=buffer))
    result = dict(id=identifier,request_sha256=policy.digest(request),status='FAILED',plan=None,
        actual_model=None,usage=None,started_unix=time.time(),provider_attempts=1,retries=0)
    try:
        style = ('Be supportive and patient; encourage independent decisions.' if request['payload']['style'] == 'supportive'
            else 'Be direct and constructively critical of unsupported decisions, without insults or humiliation.')
        plan, model, usage = provider.strong(json.dumps(request['payload'],sort_keys=True),directory,
            min(time.time()+125,policy.NATIVE_END),instruction=policy.principles()+'\n\n'+policy.PARENT_SYSTEM+' '+style)
        policy.validate_parent(request['payload'],plan)
        require(model == policy.STRONG and bool(usage),'real_strong_parent_only')
        result.update(status='COMPLETE',plan=plan,actual_model=model,usage=usage)
    except BaseException as error:
        result.update(error_type=type(error).__name__)
    result['finished_unix'] = time.time()
    (directory/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2))
    archive, files = store.archive(directory,identifier)
    result.update(archive_root=archive,files=files)
    store.write(response_path,result)
    remote = store.read(response_path)
    require(remote == result,'published_response_verified')
    shutil.rmtree(directory)
    return result['status']


def serve(wrappers, lane, buffer):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and Path(buffer).is_absolute()
        and Path(buffer).is_relative_to('/tmp'),'CPU_bounded_transient_buffer')
    Path(buffer).mkdir(parents=True,exist_ok=False)
    store = Store(wrappers,lane)
    ready = store.read(ROOT/'READY.json')
    ready_sha256 = store.shell('sha256sum '+shlex.quote(str(ROOT/'READY.json'))).stdout.decode().split()[0]
    publication = store.read(ROOT/'PUBLICATION.json')
    require(ready['lane'] == lane and ready['bounds'] == policy.bounds()
        and ready['principles_sha256'] == policy.PRINCIPLES_SHA
        and publication['ready_sha256'] == ready_sha256 and publication['own_tests_passed'] is True,
        'published_exact_parent_allocation')
    cohort = store.read(ROOT/'COHORT_PRIVATE.json')
    train_ids = {task['id'] for group in cohort['TRAIN'] for task in group}
    store.shell('mkdir -p '+shlex.quote(str(ROOT/'parent_claims')))
    handled = set()
    while time.time() < policy.NATIVE_END:
        if store.exists(ROOT/'TERMINAL.json'):
            return
        listing = store.shell('find '+shlex.quote(str(ROOT/'parent_queue'))+' -maxdepth 1 -name "P*.request.json"').stdout.decode()
        for name in sorted(listing.splitlines()):
            if name in handled:
                continue
            request = store.read(Path(name))
            status = process(store,request,ready_sha256,train_ids,buffer)
            handled.add(name)
            if status == 'FAILED':
                return
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wrappers',type=Path,required=True)
    parser.add_argument('--lane',choices=policy.LANES,required=True)
    parser.add_argument('--buffer',type=Path,required=True)
    args = parser.parse_args()
    serve(args.wrappers,args.lane,args.buffer)
