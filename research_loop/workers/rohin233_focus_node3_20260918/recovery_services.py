"""Attach existing CPU-only services after exact kept-native recovery."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from recovery import current_control, read, utc
from recovery_proof import project
from retirement import PROTECTED, identity, save, sha


def start(output, name, command, source, environment):
    receipt = output / (name + '.json')
    if receipt.exists():
        raise ValueError('no_duplicate_service_attachment:' + name)
    with (output / (name + '.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
    save(receipt, dict(observed_utc=utc(), process=identity(process.pid), provider_requests=0,
        native_signals=0, publication_not_yet_verified=True))
    return process


def wait_for(root, output, deadline, names):
    while time.time() < deadline:
        proof = project(root)
        temporary = output / 'NATIVE_WAIT.partial'
        temporary.write_text(json.dumps(proof, sort_keys=True) + '\n')
        temporary.replace(output / 'NATIVE_WAIT.json')
        live = {row['life'] for row in proof['lives'] if row['status'] == 'LOADED_ALIVE'}
        if set(names) <= live:
            return proof
        time.sleep(10)
    raise ValueError('parent_attachment_expired_without_required_exact_natives')


def run(root, output, python, parents_only=False):
    output.mkdir(parents=True, exist_ok=True)
    lock = (root / 'R233_RECOVERY_SERVICES.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plans = {name: read(current_control(root / name) / 'PLAN.json') for name in PROTECTED}
    deadline = min(plan['hard_end_unix'] for plan in plans.values()) - 120
    if deadline - time.time() < 3600:
        raise ValueError('services_need_viable_current_authorized_horizon')
    relay_source = root / 'r228_feedback_relay_20260918T0908Z'
    native_source = Path(plans['r213_r226_caption_observation_fork']['source_root'])
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTHONPATH=os.pathsep.join((str(native_source), str(root), str(relay_source))))
    if not parents_only:
        start(output, 'feedback', [python, '-B', str(relay_source / 'node3_feedback.py'), '--root', str(root),
            '--output', str(relay_source / 'output'), '--formatter-sha256', sha(relay_source / 'relay.py'),
            '--end-unix', str(deadline)], relay_source, environment)
    wait_for(root, output, deadline, ('r213_r226_caption_observation_fork',))
    parent_source = root / 'r233_recovery_parents_v2'
    environment['PYTHONPATH'] = os.pathsep.join((str(parent_source), str(root)))
    start(output, 'classroom', [python, '-B', str(parent_source / 'classroom.py'), 'serve', '--resume', '--recovering',
        '--root', str(root), '--output', str(root / 'r233_classroom_handoff_v1/live'),
        '--config', str(root / 'r233_classroom_operator_v2/CONFIG_PRIVATE.json')], parent_source, environment)
    wait_for(root, output, deadline, ('r213_r226_caption_unparented_fork',))
    start(output, 'caption_gpu7', [python, '-B', str(parent_source / 'caption_epoch.py'),
        'serve-former-control', '--resume', '--root', str(root),
        '--output', str(root / 'r233_all_five_caption_epochs_v1'),
        '--config', str(root / 'r233_caption_epoch_operator_v1/CONFIG_PRIVATE.json')], parent_source, environment)
    proof = wait_for(root, output, deadline, ('r213_math_a', 'r213_math_b_fork', 'r213_math_c'))
    start(output, 'math_debate', [python, '-B', str(parent_source / 'debate_resume.py'),
        '--root', str(root), '--output', str(root / 'r231_math_parent_live_v2'),
        '--initial', str(root / 'r231_math_operator_v2/R229_MATH_PARENT_FIRST_RENDER_20260918T093031Z.json'),
        '--result', str(root / 'r231_math_parent_live_v2/phase_004/exchange_2/RESULT.json')],
        parent_source, environment)
    save(output / 'ATTACHED_NOT_RENDER_PROOF.json', dict(observed_utc=utc(), parent_provider_requests=0,
        all_eight_native_proof=proof, native_signals=0, checked_new_renders=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--python', required=True)
    parser.add_argument('--parents-only', action='store_true')
    options = parser.parse_args()
    run(options.root, options.output, options.python, options.parents_only)
