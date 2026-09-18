"""Archive failed original C2 suffix and resume complete45 with pinned Main R193."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import time


LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OLD = Path('/localhome/local-rohing/orch_r153_r188_C2_20260917_recovery1')
NEW = Path('/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1')
MATH = Path('/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z')
GATE_SHA = 'c7821ed5b02651ed624c6dbe29a488bd15496440b59364e98e52ff2afe705e82'
MANIFEST_SHA = '4c7db8b0a79df2ffb1ca53c20760098d4ec0768c1ec8e02ba05a0260436727fe'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def metadata(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        raw = stream.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def process_absent(pid):
    require(not Path('/proc', str(pid)).exists(), 'old_native_supervisor_not_absent')


def stage():
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'NODE5_owner_only')
    for pid in (2718196, 2718170):
        process_absent(pid)
    require(read(OLD / 'control/EXIT.json')['exit_code'] == 1, 'actual_native_failure')
    require(sha(NEW / 'main/MANIFEST.json') == MANIFEST_SHA, 'pinned_Main_closure')
    main = read(NEW / 'main/MANIFEST.json')
    source = NEW / 'source'
    if not source.exists():
        shutil.copytree(OLD / 'source', source)
    for name, expected in {**main['source_files'], **main['test_files']}.items():
        require(sha(NEW / 'main' / name) == expected, 'Main_payload_changed')
        target = source / name
        if target.exists():
            target.chmod(0o644)
        shutil.copyfile(NEW / 'main' / name, target)
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    start, end = text.index('    def _cpu(self, origin):'), text.index('    def act(self):')
    prior = (OLD / 'source/gpu/orch_r184_think_act_learn.py').read_text()
    prior_start, prior_end = prior.index('    def _cpu(self, origin):'), prior.index('    def act(self):')
    driver.write_text(text[:start] + prior[prior_start:prior_end] + text[end:])
    compile(driver.read_text(), str(driver), 'exec')
    sys.path.insert(0, str(source))
    from gpu import orch_r184_think_act_learn as scaffold
    require('gpu.r184_cpu_bridge' in scaffold.ThinkActLearn._cpu.__code__.co_names, 'external_bridge_preserved')
    records = [(path, metadata(path)) for path in sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))]
    completed = [(path, entry) for path, entry in records if entry['kind'] == 'SLEEP_COMPLETE']
    complete_path, complete_meta = completed[-1]
    complete = read(complete_path)['document']
    require(complete_meta['index'] == 5406 and complete['cycle'] == 45
            and complete_meta['sha256'] == '4f93c7380d23012acad2e2751840d951afdc5384153df38f08748e6bfacb2cd2', 'latest_actual_complete45')
    saved = complete['resume_state']
    require(saved['state']['pending'] is None and saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'complete45_exact_history')
    require(records[-1][1]['index'] == 5451 and records[-1][1]['kind'] == 'UPDATE', 'unchanged_failed_suffix')
    require(shutil.disk_usage(NEW).free > 4 * 1024**3, 'disk_for_full_preservation')
    registered = set()
    for path, entry in records:
        if entry['index'] <= 5406 and entry['kind'] == 'INBOX':
            registered.add(read(path)['document']['message']['id'])
    inbox = []
    for path in sorted((LIFE / 'stream/inbox').glob('*.json')):
        message = read(path)
        include = message['id'] in registered or message.get('speaker') != 'Tool'
        inbox.append(dict(id=message['id'],name=path.name,speaker=message.get('speaker'),sha256=sha(path),
                          include=include,registered_before45=message['id'] in registered))

    def ignore(directory, names):
        relative = Path(directory).relative_to(LIFE)
        excluded = []
        for name in names:
            if relative == Path('.') and name in ('SAVED_STATE.json', 'CHECKPOINT.json', 'PRESERVATION_RECEIPT.json'):
                excluded.append(name)
            elif relative == Path('stream') and name == 'WRITER.lock':
                excluded.append(name)
            elif relative == Path('stream/records') and name[:20].isdigit() and int(name[:20]) > 5406:
                excluded.append(name)
            elif relative == Path('stream/inbox') and not any(item['name'] == name and item['include'] for item in inbox):
                excluded.append(name)
            elif relative.parts[:2] == ('community_cpu', 'spool') and len(relative.parts) == 3 and name == 'rootfs':
                excluded.append(name)
        return excluded

    prepared = NEW / 'prepared_life'
    if prepared.exists():
        require(not (NEW / 'control').exists() and not (NEW / 'PREPARED.json').exists(), 'preparation_only_not_live_retry')
        prepared.rename(NEW / 'preserved_partial_filesystem_copy')
    shutil.copytree(LIFE, prepared, ignore=ignore, symlinks=True)
    (prepared / 'stream/WRITER.lock').touch(mode=0o600, exist_ok=False)
    write(prepared / 'SAVED_STATE.json', saved)
    write(prepared / 'CHECKPOINT.json', complete['checkpoint'])
    checkpoint_files = {str(path.relative_to(LIFE / 'checkpoints/sleep_000045')): sha(path)
                        for path in (LIFE / 'checkpoints/sleep_000045').rglob('*') if path.is_file()}
    for name, expected in checkpoint_files.items():
        require(sha(prepared / 'checkpoints/sleep_000045' / name) == expected, 'exact_checkpoint45_copy')
    for path, entry in records:
        if entry['index'] <= 5406:
            require(sha(prepared / 'stream/records' / path.name) == sha(path), 'exact_prefix_copy')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    old_guard = read(OLD / 'control/GUARD.json')
    plan = read(old_guard['plan_path'])
    plan.update(source_root=str(source), rehearsal_presentations=0)
    plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
    plan['think_act_learn'].update(continuity_policy='R193_CONTINUITY_V1', think_segments=1,
        cpu_gate_root=str(MATH / 'gate'), cpu_gate_sha256=GATE_SHA,
        environment_facts='The current confined Python tool has the standard library plus read-only SymPy 1.14.0 and mpmath 1.3.0. '
        'No network, GPU, home access, or Torch is provided. Earlier missing-SymPy feedback describes the older environment. '
        'Installation does not establish execution: only actual tool receipts do. Incomplete or truncated code is not executed or automatically retried.')
    plan['think_act_learn'].pop('outcome_policy', None)
    scaffold.validate_config(plan['think_act_learn'])
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests.test_orch_r184_think_act_learn', '-v'],
                            cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source)),
                            capture_output=True, text=True, timeout=90)
    (NEW / 'CPU.log').write_text(result.stdout + result.stderr)
    require(result.returncode == 0, 'actual_source_R193_CPU')
    control = NEW / 'control'
    control.mkdir()
    cpu = dict(passed=True, source_pins=pins, log_sha256=sha(NEW / 'CPU.log'), external_bridge_preserved=True,
               Main_manifest_sha256=MANIFEST_SHA, observed_unix=time.time())
    write(NEW / 'CPU.json', cpu)
    write(control / 'RECEIVING_CPU.json', cpu)
    write(control / 'PLAN.json', plan)
    shutil.copyfile(old_guard['lease_path'], NEW / 'LEASE.json')
    require(sha(NEW / 'LEASE.json') == old_guard['lease_sha256'], 'unchanged_lease')
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True,
        cpu_receipt_path=str(NEW / 'CPU.json'), cpu_receipt_sha256=sha(NEW / 'CPU.json'), declared_unix=time.time()))
    guard = dict(old_guard, source_pins=pins, resume=True, copy_raw=str(LIFE), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), attempt_dir=str(control), lease_path=str(NEW / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    journal = read(LIFE / 'stream/JOURNAL.json')
    write(NEW / 'BRIDGE.json', dict(raw_root=str(LIFE), journal_id=journal['journal_id'],
        socket='/tmp/r193_node5_c2_recovery1.sock', gate_root=str(MATH / 'gate'), gate_sha256=GATE_SHA,
        cpu_source=str(MATH / 'source'), native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), stop_unix=plan['hard_end_unix']))
    write(NEW / 'PREPARED.json', dict(checkpoint=45, cutoff=5406, optimizer_steps=4620,
        saved_state_sha256=sha(prepared / 'SAVED_STATE.json'), checkpoint_files=checkpoint_files,
        failed_suffix=[dict(index=entry['index'],kind=entry['kind'],record_sha256=entry['sha256'],file_sha256=sha(path))
                       for path, entry in records if entry['index'] > 5406],
        discarded_recorded_updates=5,possible_unlogged_failed_update=True,inputs=inbox,
        original_root_inode=LIFE.stat().st_ino,source_pins=pins,guard_sha256=sha(control / 'GUARD.json'),
        preservation='FULL_OLD_ROOT_TO_BE_ARCHIVED; no retrospective tool replay',created_unix=time.time()))
    print(json.dumps(dict(status='PREPARED_MAIN_R193_TESTED', root=str(NEW), checkpoint=45,
                         receipt_sha256=sha(NEW / 'PREPARED.json'), guard_sha256=sha(control / 'GUARD.json'))))


def launch():
    proof = read(NEW / 'PREPARED.json')
    for pid in (2718196, 2718170):
        process_absent(pid)
    require(LIFE.stat().st_ino == proof['original_root_inode'], 'original_root_unchanged')
    require(not (NEW / 'ARCHIVE_INTENT.json').exists(), 'fresh_archive_only')
    process = Path('/proc/2849330')
    fields = (process / 'stat').read_text().split(') ', 1)[1].split()
    require(int(fields[19]) == 22524815 and 'c2_math_bridge_phase.py' in (process / 'cmdline').read_text(), 'old_CPU_bridge_identity')
    require(not (process / 'task/2849330/children').read_text().strip(), 'old_CPU_bridge_idle')
    pidfd = os.pidfd_open(2849330)
    try:
        write(NEW / 'OLD_CPU_BRIDGE_STOP_INTENT.json', dict(pid=2849330,start=22524815,time=time.time(),native_signals=0))
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)
        require(bool(select.select([pidfd], [], [], 10)[0]), 'old_CPU_bridge_exit')
    finally:
        os.close(pidfd)
    write(NEW / 'OLD_CPU_BRIDGE_EXITED.json', dict(pid=2849330,time=time.time()))
    archive = NEW / 'archived_failed46_life'
    write(NEW / 'ARCHIVE_INTENT.json', dict(original=str(LIFE),archive=str(archive),cutoff=5406,
        checkpoint=45,discarded_recorded_updates=5,possible_unlogged_failed_update=True,time=time.time()))
    LIFE.rename(archive)
    (NEW / 'prepared_life').rename(LIFE)
    write(NEW / 'RESTORED.json', dict(root=str(LIFE),archive=str(archive),checkpoint=45,cutoff=5406,
        optimizer_steps=4620,loss_labelled=True,retrospective_tool_execution=False,time=time.time()))
    source = NEW / 'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_guard as guard
    guard.validate(NEW / 'control/GUARD.json')
    processes = {}
    for name, argv, cwd in (
        ('cpu_bridge',[sys.executable,'-B',str(NEW/'r193_c2_bridge.py'),'--config',str(NEW/'BRIDGE.json')],NEW),
        ('supervisor',[sys.executable,'-B','-m','gpu.r188_node5_confinement','dispatch','--config',str(NEW/'control/GUARD.json')],source)):
        with (NEW / (name + '.log')).open('x') as log:
            child = subprocess.Popen(argv,cwd=cwd,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        processes[name] = dict(pid=child.pid,start=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19])
        if name == 'cpu_bridge':
            deadline = time.monotonic() + 30
            while not list((NEW/'bridge_receipts').glob('READY*')):
                require(child.poll() is None and time.monotonic() < deadline, 'math_bridge_ready_before_GPU')
                time.sleep(.1)
    write(NEW / 'STARTED.json', dict(processes=processes,checkpoint=45,continuity_policy='R193_CONTINUITY_V1',
        source=str(source),root=str(LIFE),guard_sha256=sha(NEW/'control/GUARD.json'),time=time.time(),loaded=False))
    print(json.dumps(read(NEW / 'STARTED.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage','launch'))
    arguments = parser.parse_args()
    require(Path(__file__).resolve().parent == NEW, 'owned_recovery_root')
    stage() if arguments.action == 'stage' else launch()
