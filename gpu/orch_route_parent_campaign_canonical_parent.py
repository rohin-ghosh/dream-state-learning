"""Single-attempt Astra broker with node-only durable raw transcripts."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from gpu import orch_route_parent_campaign_providers as providers
from gpu.orch_l2_shared_run import write
from gpu.orch_route_parent_campaign_mirror import inventory
from organism_v6 import orch_route_parent_campaign_canonical as policy


ROOT = policy.ROOT
PATTERN = re.compile(r'(?P<index>\d{4})_(?P<arm>GUIDED|NO_LORA)_C(?P<cycle>[1-8])\.request\.json')
SYSTEM = ('You are a supportive-positive training-wheels route-learning parent. '
          'Focus on this provided episode only. Scaffold evidence-grounded approaches, '
          'reconsideration of rejected paths, and coherent explanations. Never invent '
          'observations or supply a gold route. Failures are not correct answers. '
          'No tools. Return only JSON with speak (boolean), message (at most 90 words), '
          'rationale (string); if silent, message must be empty.')


def validated_request(name, request):
    match = PATTERN.fullmatch(name)
    policy.require(match is not None and int(match['index']) < policy.CAPS['parent_calls_per_lane'],
                   'bounded_canonical_request_identity')
    policy.require(set(request) == {'id', 'payload'} and request['id'] == name.removesuffix('.request.json'),
                   'exact_request_binding')
    supplied = dict(request['payload'])
    policy.require(supplied.pop('cell') == policy.CELL, 'same_registered_strong_curriculum')
    return policy.parent_payload(supplied)


def remote(host, command, timeout=30):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', host, command], text=True, timeout=timeout)


def serve(host, deadline):
    policy.require(time.time() < deadline <= policy.CAMPAIGN_DEADLINE, 'unchanged_campaign_deadline')
    while time.time() < deadline - 30:
        names = remote(host, f'find {ROOT}/parent_queue -maxdepth 1 -name "*.request.json" -printf "%f\\n"')
        for name in sorted(names.splitlines()):
            if not PATTERN.fullmatch(name):
                continue
            identity = name.removesuffix('.request.json')
            destination = f'{ROOT}/parent_queue/{identity}.response.json'
            if remote(host, f'test ! -f {destination} || echo DELIVERED').strip():
                continue
            policy.require(time.time() < deadline - 30, 'provider_dispatch_deadline')
            request = json.loads(remote(host, f'cat {ROOT}/parent_queue/{name}'))
            payload = validated_request(name, request)
            raw_root = f'{ROOT}/parent_raw/{identity}'
            claim = remote(host, f'mkdir -p {ROOT}/parent_raw; mkdir {raw_root} && echo CLAIMED')
            policy.require(claim.strip() == 'CLAIMED', 'prior_attempt_must_not_retry')
            directory = Path(tempfile.mkdtemp(prefix='orch_route_parent_campaign_pending_'))
            verified = False
            try:
                write(directory / 'REQUEST.json', request)
                prompt = json.dumps(payload, sort_keys=True)
                (directory / 'prompt.txt').write_text(prompt)
                (directory / 'system.txt').write_text(SYSTEM)
                started = time.time()
                write(directory / 'ATTEMPT.json', dict(id=identity, started_unix=started,
                    model=providers.STRONG, request_sha256=policy.digest(request), attempts=1,
                    retries=0, deadline_unix=deadline, max_output_tokens=4096))
                subprocess.run(['scp', '-q', str(directory / 'ATTEMPT.json'), host + ':' + raw_root + '/ATTEMPT.json'], check=True)
                try:
                    response, model, usage = providers.strong(prompt, directory, deadline, SYSTEM)
                    write(directory / 'RECEIPT.json', dict(verified=True, actual_model=model,
                        usage=usage, started_unix=started, finished_unix=time.time(),
                        transcript_quarantined_from_ongoing_L1=True))
                except Exception as error:
                    response = dict(error=str(error), speak=False, message='', rationale='NO_SUBSTITUTE')
                    write(directory / 'ERROR.json', dict(error_type=type(error).__name__, error=str(error),
                        started_unix=started, finished_unix=time.time(), retries=0))
                write(directory / (identity + '.response.json'), dict(id=identity,
                    request_sha256=policy.digest(request), result=response))
                write(directory / 'MANIFEST.json', inventory(directory))
                subprocess.run(['rsync', '-a', str(directory) + '/', host + ':' + raw_root + '/'], check=True, timeout=60)
                result = json.loads(remote(host, f'python3 {ROOT}/source/gpu/orch_route_parent_campaign_mirror.py '
                    f'{raw_root} --manifest {raw_root}/MANIFEST.json'))
                policy.require(result['verified'], 'node_transcript_hash_verification_required')
                verified = True
                remote(host, f'cp {raw_root}/{identity}.response.json {destination}.partial && mv {destination}.partial {destination}')
                print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), id=identity,
                    node_raw=raw_root, mirrored=True, provider_error=bool(response.get('error')))), flush=True)
            finally:
                if verified:
                    shutil.rmtree(directory)
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--deadline', required=True, type=float)
    args = parser.parse_args()
    serve(args.host, args.deadline)
