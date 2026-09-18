"""Explicit CPU-only successor; never stops predecessors or launches a native."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

from c2_parent_continue import FLEET, validate_config_change
from checkpoint_tail_parent_binding import ORIGINAL_SOURCE, ROOT, WALL


OWN = Path(__file__).resolve().parent


def validate_inputs(manifest):
    for filename, expected in manifest['local_source_sha256'].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError('exact_parent_helper_and_view_bytes')
    config = json.loads(Path(manifest['config_path']).read_bytes())
    previous = json.loads(Path(manifest['predecessor_config_path']).read_bytes())
    validate_config_change(previous, config)
    if config['root'] != ROOT or config['source_root'] != ORIGINAL_SOURCE or config['hard_end_unix'] != WALL:
        raise ValueError('same_original_C2_parent_view_and_lease')
    if Path(manifest['output']).exists():
        raise ValueError('no_reuse_of_parent_output')
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    arguments = parser.parse_args()
    if hashlib.sha256(arguments.manifest.read_bytes()).hexdigest() != arguments.manifest_sha256:
        raise ValueError('exact_prepared_parent_manifest')
    manifest = json.loads(arguments.manifest.read_bytes())
    validate_inputs(manifest)
    with (OWN / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
        fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        spec = importlib.util.spec_from_file_location('c2_checkpoint_tail_original_parent', FLEET / 'r202_parent.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_remote = module.parent.remote
        original_snapshot = module.snapshot
        output = Path(manifest['output'])

        def remote(repository, binding, script):
            pin_checks = 'import hashlib; from pathlib import Path;\n'
            for filename, expected in manifest['remote_helper_sha256'].items():
                pin_checks += ('assert hashlib.sha256(Path(' + repr(filename) + ').read_bytes()).hexdigest() == '
                    + repr(expected) + ', "pinned_parent_remote_helper";\n')
            prefix = ('import sys; sys.path.insert(0, ' + repr(manifest['remote_operator']) + ');\n'
                'from checkpoint_tail_parent_binding import verify; verify('
                + repr(binding['native_binding_path']) + ', ' + repr(binding['native_binding_sha256']) + ');\n')
            return original_remote(repository, binding, pin_checks + prefix + script)

        def snapshot(repository, binding):
            while time.time() < WALL:
                try:
                    state = original_snapshot(repository, binding)
                    with (output / 'CHECKPOINT_TAIL_LAST_POLL.json').open('w') as stream:
                        json.dump(dict(observed_unix=time.time(), response_count=state['response_count'],
                            record_count=state['record_count'], head_sha256=state['head_sha256'],
                            native_binding_sha256=binding['native_binding_sha256']), stream)
                    return state
                except (RuntimeError, ValueError, TimeoutError, subprocess.TimeoutExpired) as error:
                    with (output / 'CHECKPOINT_TAIL_POLL_RETRIES.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(observed_unix=time.time(), error_type=type(error).__name__,
                            retry_scope='READ_ONLY_SNAPSHOT', native_signals=[])) + '\n')
                    time.sleep(min(5, max(0, WALL - time.time())))
            raise TimeoutError('C2_parent_lease_margin_reached')

        module.parent.remote = remote
        module.snapshot = snapshot
        sys.argv = [str(FLEET / 'r202_parent.py'), '--config', manifest['config_path'],
            '--output', manifest['output'], '--policy-addendum', manifest['policy_addendum']]
        module.main()


if __name__ == '__main__':
    main()
