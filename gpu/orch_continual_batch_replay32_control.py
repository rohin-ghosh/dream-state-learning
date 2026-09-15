"""One bounded sampled pair; checkpoint-pause and always resume the owned feed."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_continual_batch_publish as publisher
from gpu.orch_continual_batch_remote_feed import read, sha, write_once, cleanup_verified_packets, failure_summary
from organism_v6 import orch_continual_batch as policy


def identity(pid):
    path = Path(f'/proc/{pid}')
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(uid=path.stat().st_uid, start_ticks=int(fields[19]), state=fields[0], ppid=int(fields[1]))


def live_descendants(pid):
    processes = {}
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            try:
                if path.stat().st_uid != os.getuid():
                    continue
                processes[int(path.name)] = identity(int(path.name))
            except (FileNotFoundError, ProcessLookupError):
                pass
    found = {pid}
    while True:
        expanded = found | {child for child, item in processes.items() if item['ppid'] in found}
        if expanded == found:
            break
        found = expanded
    return [child for child in found - {pid} if processes[child]['state'] != 'Z']


def signal_owned(config, event):
    observed = identity(config['old_pid'])
    policy.require(observed['uid'] == os.getuid() and observed['start_ticks'] == config['old_start_ticks'], 'exact_owned_feed_identity')
    descriptor = os.pidfd_open(config['old_pid'])
    try:
        policy.require(identity(config['old_pid'])['start_ticks'] == config['old_start_ticks'], 'pid_reuse')
        signal.pidfd_send_signal(descriptor, event)
    finally:
        os.close(descriptor)


def run(config_path):
    config = read(config_path); runtime = Path(config['runtime']); reductions = Path(config['reductions'])
    policy.require(Path(__file__).resolve().is_relative_to(runtime / 'source') and runtime.is_relative_to('/tmp'), 'outside_git_runtime')
    policy.require(all(sha(runtime / name) == digest for name, digest in config['runtime_files'].items()), 'controller_hash_drift')
    write_once(runtime / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time()))
    target = os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET']; native = config['native_root']
    os.environ['ORCH_CONTINUAL_BATCH_CODEX_REAL'] = config['codex_real']
    os.environ['PATH'] = str(runtime / 'provider_bin') + os.pathsep + os.environ['PATH']
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    publisher.RUNTIME_ROOT = runtime; publisher.LINE_REVIEWS = True; publisher.BRANCH_V3 = True
    local = runtime / 'review_batch_replay32'; workspace = local / 'review_workspace'
    paused = False; transfer = None

    def ssh(command):
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', target, command],
            cwd=runtime, capture_output=True, text=True, check=True, timeout=240)

    def rpc(phase):
        response = ssh(f'env CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH={native}/source '
            f'{config["native_python"]} -B -m gpu.orch_continual_batch_replay32 {phase} --root {native}')
        return json.loads(response.stdout)

    try:
        policy.require(time.time() + 660 < config['deadline_unix'], 'original_deadline_margin')
        policy.require(identity(config['old_pid'])['state'] not in ('T', 't'), 'do_not_take_over_an_existing_pause')
        write_once(reductions / 'PAUSE_IDENTITY.json', dict(pid=config['old_pid'], identity=identity(config['old_pid']),
                                                          paused_by=os.getpid(), deadline_unix=config['deadline_unix']))
        signal_owned(config, signal.SIGSTOP); paused = True
        while live_descendants(config['old_pid']):
            policy.require(time.time() + 660 < config['deadline_unix'], 'original_deadline_while_draining')
            time.sleep(2)
        write_once(reductions / 'PRIOR_PROVIDER_DRAINED.json', dict(observed_unix=time.time(), live_descendants=[],
                                                                  parent_still_paused=True))
        capture = rpc('packets'); packets = capture.pop('packets')
        write_once(reductions / 'CAPTURE.json', capture)
        available = lambda: int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                                    if line.startswith('MemAvailable:'))) * 1024
        while available() < 800 * 1024**2:
            policy.require(time.time() + 660 < config['deadline_unix'], 'memory_wait_deadline')
            time.sleep(5)
        reservation = rpc('reserve'); write_once(reductions / 'RESERVATION.json', reservation)
        workspace.mkdir(parents=True)
        with (workspace / 'REVIEW_INSTRUCTIONS.md').open('x') as stream:
            stream.write((runtime / 'REVIEW_INSTRUCTIONS.md').read_text())
        sampled = []
        for group, packet in enumerate(packets):
            directory = workspace / f'batch_000_{group}'; directory.mkdir()
            write_once(directory / 'PACKET.json', packet); write_once(directory / 'SCHEMA.json', publisher.schema())
            sampled.append([dict(target=''.join(line['text'] for line in row['target_source_lines']),
                target_sha256=row['target_sha256'], gold=row['gold'], student_prefix_sha256=row['student_prefix_sha256'],
                provenance=dict(raw_call_sha256=row['raw_call_sha256'])) for row in packet])
        publisher.ROOT = local
        errors = []
        with ThreadPoolExecutor(max_workers=2 if available() >= 2400 * 1024**2 else 1) as pool:
            futures = [pool.submit(publisher.review_group, 0, group, sampled[group]) for group in range(2)]
            for future in futures:
                try:
                    future.result()
                except Exception as error:
                    errors.append(failure_summary(error))
        write_once(workspace / 'CONTROL_ERRORS.json', errors)
        inventory = {str(path.relative_to(workspace)): sha(path) for path in sorted(workspace.rglob('*')) if path.is_file()}
        write_once(workspace / 'UPLOAD_INVENTORY.json', inventory)
        subprocess.run(['scp', '-r', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(workspace),
                        target + ':' + native + '/PROVIDER_UPLOAD'], cwd=runtime, check=True,
                       capture_output=True, text=True, timeout=180)
        try:
            result = rpc('finalize')
            transfer = result['transfer']; write_once(reductions / 'RESULT.json', result)
            with Path(config['journal']).open('a') as stream:
                stream.write(f'\n\n{datetime.now(timezone.utc).isoformat()} — Laplace/Main FULL25632 pilot: '
                    f'{result["decision"]}; admitted{result["admitted_rows"]}. Native manifest '
                    f'{result.get("native_manifest")}; compiled handoff {result.get("native_handoff")}. '
                    'No fit/readout executed; pending Laplace prospective isolated paired window, not mixed attribution.\n')
        finally:
            if transfer is None:
                try:
                    transfer = json.loads(ssh(f'cat {native}/PROVIDER_UPLOAD_VERIFIED.json').stdout)
                except Exception:
                    pass
            if transfer is not None:
                write_once(reductions / 'TRANSFER_VERIFIED.json', transfer)
                cleanup_verified_packets(local, transfer, sha(workspace / 'UPLOAD_INVENTORY.json'))
    except Exception as error:
        write_once(reductions / 'FAILED.json', dict(**failure_summary(error), temporary_packet_preserved=local.exists()))
    finally:
        if paused:
            signal_owned(config, signal.SIGCONT)
            write_once(reductions / 'FEED_RESUMED.json', dict(pid=config['old_pid'], observed_unix=time.time(),
                original_deadline_unix=config['deadline_unix'], budget_reset=False))


if __name__ == '__main__':
    run(Path(sys.argv[1]))
