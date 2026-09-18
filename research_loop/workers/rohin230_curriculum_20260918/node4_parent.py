"""Rebind existing node-4 CPU parents; never signal a learner process."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PARENTS = REPO / 'research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET'
ALLOWED = (2, 3, 5, 6)
POLICY = 'R230_NODE4_PARENT_CURRICULUM_V1'
BRIEF = '''Current R230 developmental enrichment brief from Rohin, 2026-09-18.
This supersedes earlier task-exclusive programme restrictions, not provenance,
confinement, your assigned questioning style, or genuine human conversation.
Keep the existing concrete object. Add checkable math, reading and post-sleep
recall, Socratic probing, and writing tied to the supplied reading. Connect
these subjects responsively instead of demanding a four-part response template.
Persistent early parenting should leave little aimless time: a short useful
question, evidence-based credit, or a correction is enough. Do not repeat a
stock reminder. For a caption player, keep actual funny captions and real
judgments central; brief enrichment must not replace ongoing game opportunities.
If no judgment has arrived, that is silence, not a verdict: keep guessing.
Ask for the promised artifact itself when an ACT only promises to produce it.
Accept ordinary prose and uncertainty. Never demand that the child claim a
particular emotion, memory, success, consciousness or human-like experience.
Reading progression: deliver a short passage, ask its reaction, ask it to
retell and point to a detail, reflect on that reaction, consider its own
actual situation, then reflect on itself. After a completed sleep ask what
it remembers and whether its reaction changed; distinguish recall, inference,
subject change and an honest 'I do not remember'. If the text remains visible,
do not call this proof of adapter-only retention. Keep math active throughout.
Model philosophy: what do you know, need to know, are you sure, what actual
check could settle it, should you ask? Ground answers about the system in
known mechanics: frozen Qwen2.5-7B-Instruct base, a private LoRA adapter,
Think/Act/Learn cycles and sleep training on its own eligible trajectories.
Do not invent the current optimizer state, permissions or execution results.
The paper asks whether taught skills persist outside teaching context (H1),
and whether parental experience plus sleep improves learning on a new task
against frozen and unparented controls (H2). Neither hypothesis is established
by this briefing. Distinguish psychology/intelligence extrapolations from
observed evidence. Ask about the paper without supplying sealed test answers.
Rohin's current policy is no semantic row exclusion. This parent briefing does
not change live learning eligibility or dosage; do not claim it did. English
is requested, not enforced by dropping rows. No learner pauses or restarts.
The excerpt below is teaching material, a close retelling, not a child's memory.
Use a bounded excerpt compatible with your current word limit, or spread the
reading across clearly labelled turns. Tie new writing to what was actually read.
'''


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def checked_argv(arguments, physical):
    expected = [str(PARENTS / 'r210_parent.py'), 'serve', '--physical', str(physical)]
    if physical not in ALLOWED or arguments[-4:] != expected:
        raise ValueError('exact_existing_CPU_parent_only')
    return arguments


def pending_attempts(output):
    return [str(path.parent) for path in (output / 'turns').glob('*/SOURCE.json')
            if not (path.parent / 'RESULT.json').exists()]


def prepare(physical, reading):
    if physical not in ALLOWED:
        raise ValueError('exclude_P7_unparented_and_reserved_lives')
    target = HERE / f'physical{physical}'
    target.mkdir(exist_ok=True)
    old_path = PARENTS / f'r210_parent{physical}/CONFIG.json'
    original = read(old_path)
    if sha(original['programme_path']) != original['programme_sha256']:
        raise ValueError('original_programme_binding')
    programme = target / 'PROGRAMME.txt'
    if not programme.exists():
        with programme.open('x') as stream:
            stream.write(Path(original['programme_path']).read_text() + '\n\n' + BRIEF + '\n' + reading)
    config_path = target / 'CONFIG.json'
    if not config_path.exists():
        updated = dict(original, programme_path=str(programme), programme_sha256=sha(programme))
        write_once(config_path, updated)
        write_once(target / 'PREPARED.json', dict(policy=POLICY, prepared_unix=time.time(),
            old_config_sha256=sha(old_path), config_sha256=sha(config_path),
            original_programme_sha256=original['programme_sha256'],
            new_programme_sha256=sha(programme), changed_fields=['programme_path', 'programme_sha256'],
            learner_signals=[], training_changes=[]))
    return config_path


def runtime(physical):
    sys.path.insert(0, str(PARENTS))
    import r210_parent
    config_path = HERE / f'physical{physical}/CONFIG.json'
    old_path = PARENTS / f'r210_parent{physical}/CONFIG.json'
    binding = read(PARENTS / f'r210_parent{physical}/BINDING.json')
    r210_parent.base.BUNDLE = Path(binding['bundle'])
    original_read = r210_parent.base.read
    original_sha = r210_parent.base.sha
    r210_parent.base.read = lambda path: original_read(config_path if Path(path) == old_path else path)
    r210_parent.base.sha = lambda path: original_sha(config_path if Path(path) == old_path else path)
    return r210_parent, config_path


def validate(physical):
    module, config_path = runtime(physical)
    module.base.runtime().validate(read(config_path))
    print(json.dumps(dict(policy=POLICY, physical=physical, validated_config_sha256=sha(config_path))))


def serve(physical):
    module, config_path = runtime(physical)
    write_once(HERE / f'physical{physical}/STARTED_{time.time_ns()}.json', dict(
        policy=POLICY, pid=os.getpid(), physical=physical, started_unix=time.time(),
        config_sha256=sha(config_path), learner_signals=[], same_parent_identity='Astra'))
    module.serve(physical)


def rebind(physical, pid):
    target = HERE / f'physical{physical}'
    output = PARENTS / f'r210_parent{physical}'
    config_path = target / 'CONFIG.json'
    subprocess.run([sys.executable, '-B', __file__, 'validate', '--physical', str(physical)], check=True)
    with (target / 'REBIND.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (target / 'REBOUND.json').exists():
            raise ValueError('already_rebound_do_not_duplicate')
        process = Path('/proc') / str(pid)
        arguments = checked_argv(process.joinpath('cmdline').read_bytes().decode().strip('\0').split('\0'), physical)
        ticks = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19]
        descriptor = os.pidfd_open(pid)
        stopped = False
        started = time.time()
        try:
            while time.time() - started < 180:
                checked_argv(process.joinpath('cmdline').read_bytes().decode().strip('\0').split('\0'), physical)
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                stopped = True
                for attempt in range(100):
                    status = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[0]
                    if status in ('T', 't'):
                        break
                    time.sleep(.01)
                else:
                    raise RuntimeError('CPU_parent_not_quiescent')
                pending = pending_attempts(output)
                if pending:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    time.sleep(2)
                    continue
                write_once(target / 'HANDOFF.json', dict(policy=POLICY, old_parent_pid=pid,
                    old_start_ticks=ticks, checked_parent_argv=arguments,
                    pending_attempts=pending, config_sha256=sha(config_path),
                    checked_unix=time.time(), learner_signals=[]))
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(5000):
                    raise RuntimeError('old_CPU_parent_did_not_exit')
                with (target / 'PARENT.log').open('a') as log:
                    new = subprocess.Popen([sys.executable, '-B', __file__, 'serve', '--physical', str(physical)],
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write_once(target / 'REBOUND.json', dict(policy=POLICY, old_parent_pid=pid,
                    parent_pid=new.pid, rebound_unix=time.time(), config_sha256=sha(config_path),
                    learner_signals=[], new_parent_delivery='not_yet_verified'))
                print(json.dumps(read(target / 'REBOUND.json')))
                return
            raise TimeoutError('CPU_parent_busy_preserve_existing_parent')
        finally:
            if stopped:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'rebind', 'serve'))
    parser.add_argument('--physical', type=int, choices=ALLOWED, required=True)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--reading', type=Path)
    options = parser.parse_args()
    if options.action == 'prepare':
        if options.reading is None:
            parser.error('prepare requires --reading')
        prepare(options.physical, options.reading.read_text())
    elif options.action == 'rebind':
        if options.pid is None:
            parser.error('rebind requires exact --pid')
        rebind(options.physical, options.pid)
    else:
        globals()[options.action](options.physical)


if __name__ == '__main__':
    main()
