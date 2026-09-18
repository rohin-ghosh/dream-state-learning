"""Scoped R233 CPU parent successor; no native launch or signal operations."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

from c2_parent_continue import FLEET, validate_config_change
from checkpoint_tail_parent_binding import ORIGINAL_SOURCE, ROOT, WALL


OWN = Path(__file__).resolve().parent
ORIGINAL_SHA = 'a771108236484e9e67fd1ace0cd4a4c9eb29ac34c198a4200e655b4ff3ce9e35'
OLD_RULE = "r'(?i)\\bn\\s*=\\s*4\\b|\\b354\\b|\\bV\\s*=\\s*3\\b'"
NEW_RULE = "r'(?i)\\bn\\s*=\\s*4\\b|\\b354\\b'"
STYLE = 'R233 source-grounded V correction and actual next artifact; responsive each completed response; active Rohin first'


def scoped_source(source):
    if hashlib.sha256(source).hexdigest() != ORIGINAL_SHA:
        raise ValueError('pinned_original_parent_source')
    text = source.decode()
    if text.count(OLD_RULE) != 1:
        raise ValueError('one_explicit_superseded_V_prohibition')
    return text.replace(OLD_RULE, NEW_RULE, 1)


def validate_config(previous, proposed):
    if (proposed['parent_style'] != STYLE or proposed['cadence_label'] != 'PERSISTENT'
            or proposed.get('minimum_duration_seconds') != 3600):
        raise ValueError('exact_R233_parent_treatment')
    normalized = dict(proposed, parent_style=previous['parent_style'], cadence_label=previous['cadence_label'])
    if 'minimum_duration_seconds' in previous:
        normalized['minimum_duration_seconds'] = previous['minimum_duration_seconds']
    else:
        normalized.pop('minimum_duration_seconds')
    validate_config_change(previous, normalized)
    if any(proposed[key] != previous[key] for key in ('native_binding_path', 'native_binding_sha256')):
        raise ValueError('same_actual_native_binding')
    if proposed['cadence_responses'] != 1 or proposed['root'] != ROOT or proposed['source_root'] != ORIGINAL_SOURCE:
        raise ValueError('same_C2_response_cadence_and_parent_view')


def validate_manifest(manifest):
    for filename, expected in manifest['local_source_sha256'].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError('exact_R233_parent_closure')
    proposed = json.loads(Path(manifest['config_path']).read_bytes())
    previous = json.loads(Path(manifest['predecessor_config_path']).read_bytes())
    validate_config(previous, proposed)
    if Path(manifest['output']).exists():
        raise ValueError('new_parent_output_preserves_history')
    return proposed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    arguments = parser.parse_args()
    if hashlib.sha256(arguments.manifest.read_bytes()).hexdigest() != arguments.manifest_sha256:
        raise ValueError('exact_new_parent_manifest')
    manifest = json.loads(arguments.manifest.read_bytes())
    validate_manifest(manifest)
    output = Path(manifest['output'])
    source_path = FLEET / 'r202_parent.py'
    module = types.ModuleType('r233_scoped_C2_parent')
    module.__file__ = str(source_path)
    exec(compile(scoped_source(source_path.read_bytes()), str(OWN / 'checkpoint_tail_parent_strong.py') + ':scoped_r202', 'exec'), module.__dict__)
    with (OWN / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
        fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        original_remote = module.parent.remote
        original_snapshot = module.snapshot
        original_prompt = module.parent.prompt

        def remote(repository, binding, script):
            checks = 'import hashlib;from pathlib import Path;\n'
            for filename, expected in manifest['remote_helper_sha256'].items():
                checks += ('assert hashlib.sha256(Path(' + repr(filename) + ').read_bytes()).hexdigest() == '
                    + repr(expected) + ', "pinned_parent_remote_helper";\n')
            checks += ('import sys;sys.path.insert(0,' + repr(manifest['remote_operator']) + ');\n'
                'from checkpoint_tail_parent_binding import verify;verify(' + repr(binding['native_binding_path'])
                + ',' + repr(binding['native_binding_sha256']) + ');\n')
            return original_remote(repository, binding, checks + script)

        def snapshot(repository, binding):
            while time.time() < WALL:
                try:
                    state = original_snapshot(repository, binding)
                    receipt = dict(observed_unix=time.time(), response_count=state['response_count'],
                        record_count=state['record_count'], head_sha256=state['head_sha256'],
                        native_binding_sha256=binding['native_binding_sha256'])
                    temporary = output / 'CHECKPOINT_TAIL_LAST_POLL.tmp'
                    temporary.write_text(json.dumps(receipt))
                    os.replace(temporary, output / 'CHECKPOINT_TAIL_LAST_POLL.json')
                    return state
                except (RuntimeError, ValueError, TimeoutError, subprocess.TimeoutExpired) as error:
                    with (output / 'CHECKPOINT_TAIL_POLL_RETRIES.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(observed_unix=time.time(), error_type=type(error).__name__,
                            retry_scope='READ_ONLY_SNAPSHOT', native_signals=[])) + '\n')
                    time.sleep(min(5, max(0, WALL - time.time())))
            raise TimeoutError('C2_parent_lease_margin_reached')

        def prompt(binding, state):
            instruction, payload = original_prompt(binding, state)
            pending = module.ordinary_pending(module.REPOSITORY, binding)
            receipt = dict(observed_unix=time.time(), pending_ordinary_Rohin_ids=pending,
                source_head_sha256=state['head_sha256'], response_count=state['response_count'],
                historical_answered_messages_do_not_suppress=True)
            with (output / 'R233_HUMAN_PRIORITY.jsonl').open('a') as stream:
                stream.write(json.dumps(receipt) + '\n')
            payload += '\nCurrent source-bound ordinary Rohin reply priority (rechecked again before publish):\n'
            payload += json.dumps(receipt)
            return instruction, payload

        module.parent.remote = remote
        module.snapshot = snapshot
        module.parent.prompt = prompt
        sys.argv = [str(source_path), '--config', manifest['config_path'], '--output', manifest['output'],
            '--policy-addendum', manifest['policy_addendum']]
        module.main()


if __name__ == '__main__':
    main()
