"""Resume the existing C2 CPU parent after a host reboot, never the child."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
PREVIOUS = OWN.parent / 'rohin233_recovery_node4_20260918'
sys.path.insert(0, str(PREVIOUS))
from checkpoint_tail_parent_strong import validate_manifest
from deadline_resume import sha


GAP = ('The parent-publisher VM rebooted at 22:50 UTC on September 18. The missing parent turns '
    'were an operator outage, not a verdict about you. I am back. For your next ACT, give an actual '
    'checked calculation: in the five-cycle with edges AB, BC, CD, DE, EA, is {A,C,E} independent? '
    'Check every pair, then give a largest independent set and explain why it cannot be larger. '
    'Write the calculation and answer themselves, not a plan or a print statement. You may ask '
    'me a factual question if you need help. Prefer English; all authentic child rows still train.')


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def prepare(session):
    old_path = PREVIOUS / 'private/checkpoint_tail_parent_r233_control/MANIFEST.json'
    old_manifest = read(old_path)
    previous = read(old_manifest['config_path'])
    old_output = Path(old_manifest['output'])
    for filename, expected in old_manifest['local_source_sha256'].items():
        if sha(filename) != expected:
            raise ValueError('existing_parent_source_changed:' + filename)
    session.mkdir(exist_ok=False)
    reserved = max([previous['start_after_response_count']] + [read(path)['response_count']
        for path in old_output.glob('parent_*/SOURCE.json')])
    config = dict(previous, predecessor_output=str(old_output),
        predecessor_started_sha256=sha(old_output / 'STARTED.json'), start_after_response_count=reserved)
    config_path = session / 'CONFIG.json'
    write(config_path, config)
    brief = session / 'BRIEF.md'
    brief.write_text(Path(old_manifest['policy_addendum']).read_text() + '\n\n'
        'The operator acknowledged a VM reboot gap on September 18 at 22:50 UTC. Do not blame the child. '
        'Resume responsive, concrete math, reading, writing and game objects. The immediate operator turn '
        'asks for all-pairs checking of the five-cycle independent-set problem. Credit only actual work.\n')
    pins = dict(old_manifest['local_source_sha256'])
    pins.update({str(path): sha(path) for path in (config_path, brief, Path(__file__))})
    manifest = dict(old_manifest, config_path=str(config_path),
        predecessor_config_path=old_manifest['config_path'], output=str(session / 'parent'),
        policy_addendum=str(brief), local_source_sha256=pins,
        status='POST_REBOOT_CPU_PARENT_ONLY', reboot_gap_acknowledgment_sha256=hashlib.sha256(GAP.encode()).hexdigest())
    path = session / 'MANIFEST.json'
    write(path, manifest)
    validate_manifest(manifest)
    return path


def checked_publish(manifest_path):
    manifest = read(manifest_path)
    config = validate_manifest(manifest)
    output = manifest_path.parent
    if (output / 'GAP_RESULT.json').exists():
        return read(output / 'GAP_RESULT.json')
    if (output / 'GAP_INTENT.json').exists():
        raise ValueError('unresolved_publication_reconcile_before_retry')
    sys.path.insert(0, str(REPO))
    from gpu import orch_r133_programme_parent as parent
    original_remote = parent.remote

    def remote(repository, binding, script):
        prefix = ('import sys;sys.path.insert(0,' + repr(manifest['remote_operator']) + ');'
            'from checkpoint_tail_parent_binding import verify;verify('
            + repr(binding['native_binding_path']) + ',' + repr(binding['native_binding_sha256']) + ');\n')
        return original_remote(repository, binding, prefix + script)

    parent.remote = remote
    with (PREVIOUS / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
        fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with Path(config['existing_parent_lock']).open('r') as parent_lock:
            fcntl.flock(parent_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            from checkpoint_tail_parent_strong import FLEET, scoped_source
            import types
            module = types.ModuleType('reboot_priority_check')
            module.__file__ = str(FLEET / 'r202_parent.py')
            exec(compile(scoped_source((FLEET / 'r202_parent.py').read_bytes()), module.__file__, 'exec'), module.__dict__)
            if module.ordinary_pending(REPO, config):
                raise ValueError('ordinary_Rohin_turn_pending_parent_must_wait')
            write(output / 'GAP_INTENT.json', dict(message=GAP, created_unix=time.time(),
                native_binding_sha256=config['native_binding_sha256'], native_signals=[]))
            publication = parent.publish(REPO, config, GAP)
            result = dict(publication=publication, message=GAP, published_unix=time.time(),
                native_signals=[], provider_generated=False, render_pending=True)
            write(output / 'GAP_RESULT.json', result)
            return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'publish', 'run'))
    parser.add_argument('--session', type=Path, required=True)
    options = parser.parse_args()
    session = options.session.resolve()
    manifest = session / 'MANIFEST.json'
    if options.mode == 'prepare':
        print(prepare(session), flush=True)
    elif options.mode == 'publish':
        print(json.dumps(checked_publish(manifest)), flush=True)
    else:
        validate_manifest(read(manifest))
        os.execv(sys.executable, [sys.executable, '-B', str(PREVIOUS / 'checkpoint_tail_parent_strong.py'),
            '--manifest', str(manifest), '--manifest-sha256', sha(manifest)])


if __name__ == '__main__':
    main()
