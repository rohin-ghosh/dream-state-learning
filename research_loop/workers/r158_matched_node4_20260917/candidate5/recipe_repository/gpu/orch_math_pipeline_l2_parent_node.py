"""Same parent calls with node-owned transcripts and one bounded local buffer."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time
import tomllib

from gpu import orch_math_pipeline_l2_parent as parent
from gpu import orch_math_pipeline_l2_parent_strong as strong


def manifest(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob('*')) if path.is_file()}


class Store:
    def __init__(self, repository, root):
        self.repository = repository
        self.root = root

    def shell(self, command, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu/a100_ssh.sh'), command],
            capture_output=True, text=True, timeout=60, check=check)

    def copy(self, source, destination, recursive=False):
        return subprocess.run(['bash', str(self.repository / 'gpu/a100_scp.sh')] + (['-r'] if recursive else []) +
            [str(source), str(destination)], capture_output=True, text=True, timeout=90, check=True)

    def exists(self, path):
        return self.shell('test -f ' + shlex.quote(str(path)), check=False).returncode == 0

    def archive(self, directory, campaign, identifier):
        assert campaign.startswith('campaign_') and '/' not in campaign
        assert identifier.startswith(('GUIDED_SLEEP_C', 'FROZEN_C')) and '/' not in identifier
        expected = manifest(directory)
        assert expected
        destination = self.root / 'parent_transcripts' / campaign / identifier
        self.shell('mkdir -p ' + shlex.quote(str(destination)))
        for relative in expected:
            target = destination / relative
            self.shell('mkdir -p ' + shlex.quote(str(target.parent)))
            if self.exists(target):
                result = self.shell('sha256sum ' + shlex.quote(str(target)))
                assert result.stdout.split()[0] == expected[relative], 'never_overwrite_different_lineage_bytes'
            else:
                self.copy(directory / relative, 'NODE:' + str(target))
        result = self.shell('sha256sum ' + ' '.join(shlex.quote(str(destination / name)) for name in expected))
        observed = {Path(line.split(maxsplit=1)[1].strip()).relative_to(destination).as_posix(): line.split()[0]
            for line in result.stdout.splitlines()}
        assert observed == expected, 'node_transcript_hash_verification_failed_no_local_cleanup'
        return dict(remote_root=str(destination), files=expected, all_verified=True, verified_unix=time.time())


def process_request(store, request_path, buffer, receipts, config, deadline):
    if time.time() >= deadline:
        return
    campaign = request_path.parent.parent.name
    identifier = request_path.name.removesuffix('.request.json')
    assert request_path.parent.name == 'parent_queue' and request_path.parent.parent.parent == store.root
    response_path = request_path.with_name(identifier + '.response.json')
    if store.exists(response_path):
        return
    claim = request_path.with_name(identifier + '.node_broker_claim')
    claimed = store.shell('mkdir ' + shlex.quote(str(claim)), check=False)
    if claimed.returncode:
        return
    assert not any(buffer.iterdir()), 'only_one_bounded_parent_buffer'
    local_request = buffer / 'incoming.json'
    directory = buffer / identifier
    store.copy('NODE:' + str(request_path), local_request)
    request = parent.read(local_request)
    status, plan, error = 'FAILED', None, None
    try:
        plan = strong.evaluate(request, directory, config, timeout=min(720, max(1, deadline - time.time())))
        status = 'COMPLETE'
    except Exception as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    directory.mkdir(exist_ok=True)
    response = directory / 'BROKER_RESPONSE.json'
    parent.write(response, dict(id=request['id'], request_sha256=parent.policy.digest(request),
        status=status, plan=plan, error=error))
    receipt = store.archive(directory, campaign, identifier)
    remote_response = Path(receipt['remote_root']) / 'BROKER_RESPONSE.json'
    store.shell('test ! -e ' + shlex.quote(str(response_path)) + ' && cp ' + shlex.quote(str(remote_response)) +
        ' ' + shlex.quote(str(response_path)) + '.partial && mv ' + shlex.quote(str(response_path)) +
        '.partial ' + shlex.quote(str(response_path)))
    result = store.shell('sha256sum ' + shlex.quote(str(response_path)))
    assert result.stdout.split()[0] == parent.sha(response)
    receipt.update(campaign=campaign, identifier=identifier, response_status=status,
        response_sha256=parent.sha(response), parent_source_sha256=parent.sha(Path(parent.__file__)),
        raw_text_in_repository=False)
    receipts.mkdir(parents=True, exist_ok=True)
    parent.write(receipts / f'{campaign}_{identifier}.json', receipt)
    shutil.rmtree(directory)
    local_request.unlink()


def serve(repository, root, buffer, receipts, deadline):
    assert str(buffer).startswith('/tmp/') and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    buffer.mkdir(parents=True, exist_ok=True)
    store = Store(repository, root)
    config = tomllib.loads((Path.home() / '.codex/config.toml').read_text())
    while time.time() < deadline:
        result = store.shell('find ' + shlex.quote(str(root)) + '/campaign_*/parent_queue -maxdepth 1 -name "*.request.json"')
        for name in sorted(result.stdout.splitlines()):
            process_request(store, Path(name), buffer, receipts, config, deadline)
        time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    options = parser.parse_args()
    serve(options.repository, options.root, options.buffer, options.receipts, options.deadline)
