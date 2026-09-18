"""Recover P3's CPU parent after a poll timeout without signalling its child."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / 'rohin233_focus_20260918'
sys.path.insert(0, str(PREVIOUS))
import p3_parent_v2 as previous


BRIEF = '''Recovery intervention, September 18, 2026 16:42 UTC. P3 has been
repeating plans while its parent was disconnected. Change the immediate object:
one scene, one actual funny caption now, not a plan, not a promise, not code.
Use scene 1: a man and a pregnant woman beside a crib with a money-themed mobile.
Ask for the joke itself in English, in the caption's own words. Do not supply
the joke. Keep this turn short; do not bundle math, reading, and several tasks.
Silence from the judge is not a verdict and is not a reason to stop guessing.
Do not claim feedback arrived unless an attributed Tool receipt is visible.
After a real caption, vary the next comic direction using its actual result.
If another intention appears, identify the missing caption and change your
question rather than repeating the same reminder. Keep the diverse curriculum
over subsequent turns. No training exclusions, fabricated scores or human turns.
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recover_poll(remote, deadline, record, clock=time.time, sleeper=time.sleep):
    def call(physical, request):
        failures = 0
        while True:
            try:
                return remote(physical, request)
            except subprocess.TimeoutExpired:
                if physical != 3 or request.get('op') != 'poll':
                    raise
                failures += 1
                remaining = deadline - clock()
                record(dict(kind='P3_POLL_TIMEOUT', observed_unix=clock(),
                            failures=failures, remaining_seconds=max(0, remaining),
                            publication_retried=False, learner_signals=[]))
                if remaining <= 0:
                    raise
                sleeper(min(15, remaining))
    return call


def load():
    module, policy, config, predecessor_manifest = previous.load()
    original_prompt = policy.prompt

    def prompt(*arguments, **keywords):
        instruction, payload = original_prompt(*arguments, **keywords)
        return instruction + '\n\n' + BRIEF, payload

    policy.prompt = prompt
    deadline = min(config['hard_end_unix'], module.base.WALL)
    manifest = dict(policy='R233_P3_POLL_RECOVERY_V1', physical=3,
        classification='NON_MATERIAL_TRANSPORT_REPAIR_AND_AUTHORIZED_PARENT_INTERVENTION',
        entrypoint_sha256=sha(__file__),
        predecessor_manifest_sha256=sha(PREVIOUS / 'P3_VALIDATION_MANIFEST.json'),
        predecessor_manifest=predecessor_manifest, hard_end_unix=deadline,
        cadence_responses=1, reasoning_effort='xhigh', preserved_ledger=True,
        learner_signals=[], child_training='UNCHANGED')
    return module, policy, config, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'serve'))
    parser.add_argument('--manifest-sha256')
    options = parser.parse_args()
    module, policy, config, manifest = load()
    if options.action == 'validate':
        print(json.dumps(manifest, sort_keys=True, indent=2))
        return
    approved = HERE / 'P3_RECOVERY_MANIFEST.json'
    if sha(approved) != options.manifest_sha256 or json.loads(approved.read_text()) != manifest:
        raise ValueError('exact_recovery_manifest_required')
    if time.time() >= manifest['hard_end_unix']:
        raise ValueError('existing_authorized_deadline_expired')

    def record(event):
        with (HERE / 'P3_TRANSPORT.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')

    module.remote = recover_poll(module.remote, manifest['hard_end_unix'], record)
    record(dict(kind='P3_RECOVERY_START', observed_unix=time.time(),
                manifest_sha256=options.manifest_sha256, learner_signals=[]))
    previous.previous.serve(3, module, policy, config,
                           manifest['predecessor_manifest']['predecessor_config_sha256'])


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()
