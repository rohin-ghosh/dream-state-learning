"""A100-only asynchronous Astra delivery; bounded VM buffer and node custody."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_math_feedback_uptake_r121_astra as low
from gpu import orch_math_feedback_uptake_r122_a100 as lane


delivery, shared = low.delivery, low.base
REPOSITORY = Path(__file__).resolve().parents[1]


def remote(command, check=True):
    return subprocess.run(['bash', str(REPOSITORY / 'gpu/a100_ssh.sh'), command],
        capture_output=True, text=True, check=check, timeout=40)


def copy(source, destination):
    subprocess.run(['bash', str(REPOSITORY / 'gpu/a100_scp.sh'), '-r', str(source), str(destination)],
        check=True, capture_output=True, timeout=60)


def config_for(plan, request):
    payload = request['payload']
    lane.require(payload['life_id'] == f'R122_A100_{plan["index"]}'
        and payload['task_provenance']['split'] == 'TRAIN'
        and payload['task_provenance']['cohort_sha256'] == plan['file_sha256'], 'actual_lane_TRAIN_binding')
    return dict(branch='F2', family='math', remote_root=plan['root'], life_id=payload['life_id'],
        deadline_unix=plan['native_end'], max_parent_calls=plan['prospective_parent_capacity'],
        max_output_tokens=1024, max_budget_usd=1, min_available_bytes=1024**3,
        train_tasks={payload['task_id']: payload['task_provenance']['task_sha256']},
        excluded_task_ids=[], cohort_sha256=payload['task_provenance']['cohort_sha256'],
        principles_sha256=shared.PRINCIPLES_V2_SHA256,
        fallback_parent_fields=shared.FALLBACK_PARENT_FIELDS['F2'])


def evaluate(request, directory, plan):
    config = config_for(plan, request)
    def validate_config(actual):
        lane.require(actual == config and actual['deadline_unix'] <= lane.NATIVE,
            'exact_A100_lease_not_node5_clock')
    facade = SimpleNamespace(**dict(vars(shared), validate_config=validate_config))
    namespace = dict(delivery.astra_evaluate.__globals__, shared=facade,
        tomllib=SimpleNamespace(loads=low.low_settings))
    function = FunctionType(delivery.astra_evaluate.__code__, namespace, 'a100_low_once',
        delivery.astra_evaluate.__defaults__)
    function.__kwdefaults__ = delivery.astra_evaluate.__kwdefaults__
    launch = dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=True,
        authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='R122 direct A1005-7 allocation',
        config_sha256=shared.digest(config), not_before_unix=plan['created_unix'])
    return function(request, directory, min(time.time() + 570, plan['native_end']), config=config,
        launch=launch, prompt_root=shared.MUTABLE_PROMPT_ROOT,
        principles_path=REPOSITORY / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')


def serve(index, service):
    lane.require(index in lane.DEVICES and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_owned_A100_only')
    root = lane.ROOT / f'lane{index}'
    plan_raw = remote('cat ' + shlex.quote(str(root / 'PLAN.json'))).stdout
    plan = json.loads(plan_raw)
    lane.require(plan['index'] == index and plan['root'] == str(root) and plan['optimizer_loaded'] is False, 'explicit_readonly_fork')
    plan['file_sha256'] = __import__('hashlib').sha256(plan_raw.encode()).hexdigest()
    service.mkdir(parents=True, exist_ok=False)
    with (service / 'LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lane.require(remote('mkdir ' + shlex.quote(str(root / 'BROKER.lock')), check=False).returncode == 0,
            'single_remote_broker_custody')
        shared.write(service / 'READY.json', dict(pid=os.getpid(), plan_sha256=plan['file_sha256'],
            root=str(root), configured_model=delivery.STRONG, effort='low', max_output_tokens=1024,
            parent_ttl=600, child_wait_seconds=0, source_sha256=shared.sha(__file__), started_unix=time.time()))
        copy(service / 'READY.json', 'NODE:' + str(root / 'BROKER_READY.json'))
        while time.time() < plan['native_end']:
            if remote('test -e ' + shlex.quote(str(root / 'RESIDENT_TERMINAL.json')), check=False).returncode == 0:
                break
            names = remote('find ' + shlex.quote(str(root / 'queue')) + ' -maxdepth 1 -name "*.request.json"').stdout.splitlines()
            for name in sorted(names):
                path = Path(name)
                lane.require(path.parent == root / 'queue', 'owned_queue_only')
                if remote('mkdir ' + shlex.quote(str(path.with_suffix('.claim'))), check=False).returncode:
                    continue
                request = json.loads(remote('cat ' + shlex.quote(name)).stdout)
                lane.require(request['payload']['task_provenance']['cohort_sha256'] == plan['file_sha256'], 'native_plan_file_hash')
                with tempfile.TemporaryDirectory(prefix='orch_math_r122_parent_') as temporary:
                    directory = Path(temporary) / request['id']
                    if time.time() >= request['lane_deadline_unix'] - 30:
                        directory.mkdir()
                        result = dict(status='MISSING', plan=None, actual_model=None, provider_dispatched=False,
                            error='TTL_EXPIRED_BEFORE_PROVIDER_NO_RETRY', request_sha256=shared.digest(request), finished_unix=time.time())
                        shared.write(directory / 'REQUEST.json', request)
                        shared.write(directory / 'RESULT.json', result)
                    else:
                        result = evaluate(request, directory, plan)
                    files = {item.name: shared.sha(item) for item in directory.iterdir() if item.is_file()}
                    destination = root / 'parent_transcripts' / request['id']
                    lane.require(remote('test ! -e ' + shlex.quote(str(destination)), check=False).returncode == 0, 'no_raw_overwrite')
                    copy(directory, 'NODE:' + str(destination))
                    proof = remote('sha256sum ' + ' '.join(shlex.quote(str(destination / key)) for key in files)).stdout
                    observed = {Path(line.split(maxsplit=1)[1]).name: line.split()[0] for line in proof.splitlines()}
                    lane.require(observed == files, 'every_raw_transcript_node_hash_verified')
                    response = dict(result, guidance=(result.get('plan') or {}).get('guidance', ''),
                        archive=dict(root=str(destination), files=files))
                    output = Path(temporary) / 'response.json'
                    shared.write(output, response)
                    target = path.with_name(path.name.replace('.request.json', '.response.json'))
                    copy(output, 'NODE:' + str(target) + '.pending')
                    lane.require(remote('sha256sum ' + shlex.quote(str(target) + '.pending')).stdout.split()[0] == shared.sha(output), 'response_hash')
                    remote('test ! -e ' + shlex.quote(str(target)) + ' && mv ' + shlex.quote(str(target) + '.pending') + ' ' + shlex.quote(str(target)))
                    shared.write(service / (request['id'] + '.json'), dict(status=result['status'],
                        actual_model=result.get('actual_model'), response_sha256=shared.sha(output),
                        finished_unix=result['finished_unix'], archive=response['archive'], raw_local_deleted_after_verified=True))
            time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int, choices=(5, 6, 7), required=True)
    parser.add_argument('--service', type=Path, required=True)
    args = parser.parse_args()
    serve(args.index, args.service)
