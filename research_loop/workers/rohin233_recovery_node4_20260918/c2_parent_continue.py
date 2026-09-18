"""Reuse C2's sole existing parent with a renewed wall and actual-LOAD guard."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


OWN = Path(__file__).resolve().parent
FLEET = OWN.parents[2] / 'research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201'


def validate_config_change(previous, proposed):
    allowed = {'hard_end_unix', 'predecessor_output', 'predecessor_started_sha256',
        'start_after_response_count', 'native_binding_path', 'native_binding_sha256'}
    if {key: value for key, value in previous.items() if key not in allowed} != {
            key: value for key, value in proposed.items() if key not in allowed}:
        raise ValueError('C2_parent_behavior_and_sources_unchanged')
    if proposed['hard_end_unix'] != 1789927200 or proposed['start_after_response_count'] < previous['start_after_response_count']:
        raise ValueError('renewed_C2_wall_no_cursor_rollback')


def main():
    manifest = json.loads((OWN / 'private/C2_CPU_PARENT_MANIFEST.json').read_bytes())
    for filename, expected in manifest['local_source_sha256'].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError('pinned_C2_parent_source')
    config = json.loads(Path(manifest['config_path']).read_bytes())
    previous = json.loads(Path(manifest['predecessor_config_path']).read_bytes())
    validate_config_change(previous, config)
    spec = importlib.util.spec_from_file_location('c2_original_parent', FLEET / 'r202_parent.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_remote = module.parent.remote
    original_snapshot = module.snapshot
    output = Path(manifest['output'])

    def remote(repository, binding, script):
        prefix = ('import sys; sys.path.insert(0, ' + repr(manifest['remote_operator']) + '); '
            'from c2_parent_binding import verify; verify(' + repr(binding['native_binding_path']) + ', '
            + repr(binding['native_binding_sha256']) + ');\n')
        return original_remote(repository, binding, prefix + script)

    def snapshot(repository, binding):
        while time.time() < binding['hard_end_unix']:
            try:
                state = original_snapshot(repository, binding)
                with (output / 'LAST_POLL.json').open('w') as stream:
                    json.dump(dict(observed_unix=time.time(), response_count=state['response_count'],
                        record_count=state['record_count'], head_sha256=state['head_sha256'],
                        native_binding_sha256=binding['native_binding_sha256']), stream)
                return state
            except (RuntimeError, ValueError, TimeoutError, subprocess.TimeoutExpired) as error:
                with (output / 'POLL_RETRIES.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(observed_unix=time.time(), error_type=type(error).__name__,
                        error=str(error)[:200], native_signals=[])) + '\n')
                time.sleep(5)
        raise TimeoutError('C2_parent_lease_wall')

    module.parent.remote = remote
    module.snapshot = snapshot
    sys.argv = [str(FLEET / 'r202_parent.py'), '--config', manifest['config_path'],
        '--output', manifest['output'], '--policy-addendum', manifest['policy_addendum']]
    module.main()


if __name__ == '__main__':
    main()
