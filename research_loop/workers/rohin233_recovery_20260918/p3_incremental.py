"""P3 publisher with incremental verified transport; all parent ledger guards remain."""

import argparse
import json
import subprocess
import sys
import time

import p3_recovery as previous


HERE = previous.HERE
ENDPOINT = '/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/r233_recovery/p3_endpoint.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    parser.add_argument('--manifest-sha256')
    options = parser.parse_args()
    module, policy, config, manifest = previous.load()
    manifest.update(policy='R233_P3_INCREMENTAL_TRANSPORT_V2',
                    entrypoint_sha256=previous.sha(__file__),
                    prompt_wrapper_sha256=previous.sha(HERE / 'p3_recovery.py'),
                    endpoint_sha256=previous.sha(HERE / 'p3_endpoint.py'),
                    pinned_child_pid=237705, pinned_child_start_ticks='27878033')
    if options.action == 'validate':
        print(json.dumps(manifest, sort_keys=True, indent=2))
        return
    approved = HERE / 'P3_INCREMENTAL_MANIFEST.json'
    if previous.sha(approved) != options.manifest_sha256 or json.loads(approved.read_text()) != manifest:
        raise ValueError('exact_incremental_manifest_required')
    if time.time() >= manifest['hard_end_unix']:
        raise ValueError('existing_authorized_deadline_expired')

    def record(event):
        with (HERE / 'P3_TRANSPORT.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')

    def remote(physical, request):
        if physical != 3 or request.get('op') not in ('poll', 'publish'):
            raise ValueError('P3_poll_publish_only')
        command = '/localhome/local-rohing/v2/venv/bin/python -B ' + ENDPOINT
        result = subprocess.run(['bash', str(module.base.REPO / 'gpu/a40r_ssh.sh'), command],
            input=json.dumps(dict(request, physical=physical)), capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(result.stderr[-1200:])
        return json.loads(result.stdout)

    module.remote = previous.recover_poll(remote, manifest['hard_end_unix'], record)
    record(dict(kind='P3_INCREMENTAL_START', observed_unix=time.time(),
                manifest_sha256=options.manifest_sha256, learner_signals=[]))
    previous.previous.previous.serve(3, module, policy, config,
        manifest['predecessor_manifest']['predecessor_config_sha256'])


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()
