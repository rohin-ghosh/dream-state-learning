"""Source-bound CPU curriculum handoff; no native, scorer, or debate signals."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from retirement import identity, save, sha, stamp
from classroom import load_helpers, shared_prompt, MATH


def verify_old(root, config, current):
    expected = config['old_parent']
    previous_r233 = config.get('resume_r233') is True
    script = str(root / ('r233_classroom_operator_v1/classroom.py' if previous_r233 else 'r231_parent_operator_v1/r230_curriculum.py'))
    output = str(root / ('r233_classroom_handoff_v1/live' if previous_r233 else 'r230_curriculum_live_v1'))
    if (current['pid'] != expected['pid'] or current['start_ticks'] != expected['start_ticks']
            or current['command_sha256'] != expected['command_sha256']
            or script not in current['args'] or output not in current['args']
            or 'native' in current['args'] or '-m' in current['args']):
        raise ValueError('only the exact superseded CPU curriculum writer may be signalled')


def execute(root, output, config_path):
    config = json.loads(config_path.read_bytes())
    helper, bound = load_helpers(root, config)
    old = identity(config['old_parent']['pid'])
    verify_old(root, config, old)
    output.mkdir(parents=True, exist_ok=False)
    source = Path(bound[MATH[0]]['source'])
    texts = [shared_prompt(name, stage, intervention, variation) for name in MATH for stage in range(5)
        for intervention in (False, True) for variation in range(4)]
    code = ('import json,sys; from organism_v6.orch_r125_plain_context import has_scaffolding; '
        'texts=json.load(sys.stdin); assert all(text.isascii() and len(text)<2200 and not has_scaffolding(text) for text in texts); '
        'print(len(texts))')
    verified = subprocess.run([old['args'][0], '-B', '-c', code], cwd=source,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
        text=True, input=json.dumps(texts), capture_output=True, check=True, timeout=30)
    save(output / 'GATE.json', dict(observed_utc=stamp(), pinned_plain_parent_prompts_verified=int(verified.stdout),
        seven_protected_native_bindings_verified=True, helper_pins=config['helper_pins'],
        curriculum_source_sha256=sha(Path(__file__).with_name('classroom.py')),
        handoff_source_sha256=sha(Path(__file__)), config_sha256=sha(config_path)))
    previous_output = root / ('r233_classroom_handoff_v1/live' if config.get('resume_r233') else 'r230_curriculum_live_v1')
    if config.get('resume_r233'):
        from classroom import inherited, restore, MEMBERS
        previous = {name: inherited(helper, root, root / 'r230_curriculum_live_v1', name) for name in MEMBERS}
        restore(helper, root, previous_output, previous)
    subprocess.run(['cp', '-a', '--reflink=auto', str(previous_output),
        str(output / 'PRIVATE_previous_curriculum')], check=True)
    descriptor = os.pidfd_open(old['pid'])
    try:
        verify_old(root, config, identity(old['pid']))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        if not poller.poll(15000):
            raise ValueError('prior writer exit not observed; new writer forbidden')
    finally:
        os.close(descriptor)
    save(output / 'CPU_WRITER_RETIRED.json', dict(pid=old['pid'], start_ticks=old['start_ticks'],
        command_sha256=old['command_sha256'], observed_utc=stamp(), exit_observed=True,
        signal='SIGTERM', source_bound=True, native_signals=0, debate_signals=0, tool_relay_signals=0))
    log = (output / 'CONTROLLER.log').open('xb')
    live_output = previous_output if config.get('resume_r233') else output / 'live'
    command = [old['args'][0], '-B', str(Path(__file__).with_name('classroom.py')), 'serve',
        '--root', str(root), '--output', str(live_output), '--config', str(config_path)]
    if config.get('resume_r233'):
        command.append('--resume')
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
    time.sleep(3)
    if process.poll() is not None:
        if config.get('resume_r233'):
            save(output / 'REPAIR_REQUIRED.json', dict(observed_utc=stamp(), native_signals=0,
                reason='new_CPU_resume_failed_old_v1_has_no_resume_support_no_duplicate_publisher_started'))
            raise ValueError('CPU resume failed; preserved current publications need repair')
        recovery_log = (output / 'ROLLBACK.log').open('xb')
        recovery = subprocess.Popen(old['args'], stdin=subprocess.DEVNULL, stdout=recovery_log,
            stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
        save(output / 'ROLLBACK.json', dict(pid=recovery.pid, observed_utc=stamp(),
            restored_old_cpu_command=True, reason='new_controller_exited_before_startup', native_signals=0))
        raise ValueError('new CPU parent failed; old CPU writer command restored')
    current = identity(process.pid)
    save(output / 'ATTACHED.json', dict(pid=process.pid, start_ticks=current['start_ticks'], observed_utc=stamp(),
        command_sha256=current['command_sha256'], old_pid=old['pid'], new_controller_alive=True,
        native_signals=0, old_raw_targets_private=True, no_new_native_launch=True))
    print(json.dumps(json.loads((output / 'ATTACHED.json').read_bytes())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    options = parser.parse_args()
    execute(options.root, options.output, options.config)
