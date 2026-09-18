"""Resume the original xhigh P3 parent ledger on its verified renewed native."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import p3_incremental
import p3_lease_parent


HERE = p3_incremental.HERE
END_UNIX = p3_lease_parent.END_UNIX
REMOTE_ENDPOINT = str(Path(p3_incremental.ENDPOINT).with_name('p3_continued_endpoint.py'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    options = parser.parse_args()
    module, policy, original, predecessor = p3_incremental.previous.load()
    config = p3_lease_parent.bind(policy, original)
    policy.validate(config)
    binding_path = HERE / 'P3_CONTINUED_BINDING.json'
    binding = json.loads(binding_path.read_bytes())
    manifest = dict(policy='R233_P3_VERIFIED_CONTINUATION_PARENT_V1',
        hard_end_unix=END_UNIX, predecessor_manifest=predecessor,
        binding=binding, binding_sha256=p3_incremental.previous.sha(binding_path),
        source_pins={name: p3_incremental.previous.sha(HERE / name) for name in
            ('p3_continued_parent.py', 'p3_continued_endpoint.py', 'p3_lease_parent.py',
             'p3_endpoint.py', 'p3_recovery.py')},
        preserved_ledger=True, reasoning_effort='xhigh', cadence_responses=1,
        learner_signals=[], authority='User exact-COMPLETE renewal authorization 2026-09-18T17:59:12Z')
    if options.action == 'validate':
        print(json.dumps(manifest, sort_keys=True, indent=2))
        return
    manifest_path = HERE / 'P3_CONTINUED_PARENT_MANIFEST.json'
    if manifest != json.loads(manifest_path.read_bytes()) or time.time() >= END_UNIX:
        raise ValueError('exact_current_P3_continuation_parent_manifest')
    module.base.WALL = END_UNIX
    output = module.base.OWN / 'r210_parent3'
    policy.local_attempts(output / 'turns')
    original_path = output / 'CONFIG.json'
    original_read, original_sha = module.base.read, module.base.sha
    module.base.read = lambda path: config if Path(path) == original_path else original_read(path)
    module.base.sha = lambda path: p3_incremental.previous.sha(manifest_path) if Path(path) == original_path else original_sha(path)
    module.base.runtime = lambda: policy

    def record(event):
        with (HERE / 'P3_TRANSPORT.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')

    def remote(physical, request):
        if physical != 3 or request.get('op') not in ('poll', 'publish'):
            raise ValueError('P3_poll_publish_only')
        result = subprocess.run(['bash', str(module.base.REPO / 'gpu/a40r_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE_ENDPOINT],
            input=json.dumps(dict(request, physical=physical)), capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr[-2000:])
        return json.loads(result.stdout)

    module.remote = p3_incremental.previous.recover_poll(remote, END_UNIX, record)
    record(dict(kind='P3_CONTINUED_PARENT_START', pid=os.getpid(), observed_unix=time.time(),
        native_pid=binding['pid'], hard_end_unix=END_UNIX, learner_signals=[]))
    module.serve(3)


if __name__ == '__main__':
    main()
