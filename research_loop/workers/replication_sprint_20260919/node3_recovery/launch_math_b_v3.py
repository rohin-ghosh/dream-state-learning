"""Bind the published V3 bytes and request exactly one original guarded dispatch."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COMMIT = 'd4a90aad5f5eaad7b01be0f1d2587fc4de4cff8f'
DOCUMENT = 'research_loop/workers/replication_sprint_20260919/operations/BUILDER_ENTRIES.txt'
CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T144429Z')
INTERPRETER = '/localhome/local-rohing/v2/venv/bin/python'
SOURCE_HASH = '7a5a7d7fe44b1053a90d1c7b18a5eabf3ed3d63409844e3f56071f84fcefb88a'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(4 * 1024**2):
            value.update(block)
    return value.hexdigest()


def write_once(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return dict(path=str(path), sha256=checksum(path))


def process_and_gpu_check():
    compute = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
        '--format=csv,noheader'], check=True, capture_output=True, text=True, timeout=20).stdout
    require(not compute.strip(), 'compute_present_do_not_signal_or_launch')
    devices = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
        '--format=csv,noheader,nounits'], check=True, capture_output=True, text=True, timeout=20).stdout
    selected = [line.split(', ') for line in devices.splitlines() if line.startswith('2, ')]
    require(len(selected) == 1 and selected[0][1] == 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'
        and int(selected[0][2]) <= 1, 'original_GPU2_identity_and_occupancy')
    natives = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit() or int(process.name) in (os.getpid(), os.getppid()):
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            arguments = (process / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if any(argument in ('native', 'child', 'dispatch') for argument in arguments):
                natives.append(dict(pid=int(process.name), argv=arguments,
                    start_ticks=(process / 'stat').read_text().rsplit(')', 1)[1].split()[19]))
        except FileNotFoundError:
            continue
    require(not natives, 'native_or_wrapper_present_no_signal_or_duplicate')
    return dict(observed_unix=time.time(), compute_apps=compute, gpu_inventory=devices, native_processes=natives)


def remote_main(payload):
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == os.getgid() == 2524,
        'original_node_and_owner')
    publication = payload['publication']
    require(publication['git_commit'] == COMMIT
        and publication['entry'].startswith('[Builder] 2026-09-19T14:50Z')
        and hashlib.sha256(publication['entry'].encode()).hexdigest() == publication['entry_sha256'],
        'exact_published_Builder_entry')
    require(not (CONTROL / 'BUILDER1450_DISPATCH_INTENT.json').exists()
        and not (CONTROL / 'OUTER_STARTED.json').exists(), 'no_automatic_retry')
    ready = payload['ready']
    require(ready['control'] == str(CONTROL) and ready['source_pins_sha256'] == SOURCE_HASH,
        'exact_V3_control_and_source')
    for key in ('plan', 'startup_manifest', 'receiving_cpu', 'candidate_guard', 'actual_journal_cpu',
            'original_entry_chain_cpu', 'original_native_plan_validation'):
        descriptor = ready[key]
        require(Path(descriptor['path']).parent == CONTROL
            and checksum(descriptor['path']) == descriptor['sha256'], 'current_receipt_' + key)
    for key in ('plan', 'startup_manifest', 'receiving_cpu', 'candidate_guard', 'actual_journal_cpu',
            'original_entry_chain_cpu'):
        require(ready[key]['sha256'] in publication['entry'], 'published_binding_' + key)
    require(SOURCE_HASH in publication['entry'], 'published_source_closure')
    candidate = json.loads((CONTROL / 'GUARD_CANDIDATE.json').read_bytes())
    require(checksum(candidate['allocation_path']) == candidate['allocation_sha256'], 'candidate_allocation_hash')
    allocation = json.loads(Path(candidate['allocation_path']).read_bytes())
    plan = json.loads((CONTROL / 'PLAN.json').read_bytes())
    source = Path(plan['source_root'])
    sys.path.insert(0, str(source))
    from pending_sleep_contract import digest
    require(digest(candidate['source_pins']) == SOURCE_HASH and len(candidate['source_pins']) == 204,
        'exact_204_source_closure')
    for relative, expected in candidate['source_pins'].items():
        require(checksum(source / relative) == expected, 'source_hash_' + relative)
    require(plan['hard_end_unix'] == 1790272800 and time.time() < plan['hard_end_unix']
        < plan['lease_end_unix'] == 1790391780, 'unchanged_unexpired_wall_and_recorded_lease')
    require(plan['physical'] == 2 and plan['gpu_uuid'] == 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
        'unchanged_physical_GPU2')
    require(checksum(candidate['lease_path']) == candidate['lease_sha256'], 'original_lease_bytes')
    original = json.loads((CONTROL / 'ORIGINAL_PLAN.json').read_bytes())
    active = json.loads((CONTROL.parent / 'ACTIVE_RUNTIME.json').read_bytes())
    require(active['source'] == original['source_root']
        and active['control'] == str(CONTROL.parent / 'control_r233_recovery_20260918_policy_lease_ceiling'),
        'original_active_binding_unchanged')
    records = Path(candidate['copy_raw']) / 'stream' / 'records'
    names = sorted(path.name for path in records.iterdir()
        if len(path.name) == 25 and path.name[:20].isdigit() and path.name.endswith('.json'))
    require(len(names) == 9556 and names[-1] == f'{9555:020d}.json'
        and not any(path.name.endswith('.partial') for path in records.iterdir()), 'retained_head_and_no_partial')
    complete = json.loads((records / f'{9476:020d}.json').read_bytes())
    head = json.loads((records / f'{9555:020d}.json').read_bytes())
    require(complete['sha256'] == ready['original_complete_sha256']
        and head['sha256'] == ready['original_head_sha256'], 'exact_COMPLETE_and_head')
    checkpoint = complete['document']['checkpoint']
    checkpoint_root = Path(candidate['copy_raw']) / 'checkpoints' / 'sleep_000192'
    require(json.loads((checkpoint_root / 'COMMIT.json').read_bytes()) == checkpoint, 'saved_COMMIT')
    for name, expected in checkpoint['adapter_files'].items():
        require(checksum(checkpoint_root / 'adapter' / name) == expected, 'saved_adapter_' + name)
    require(checksum(checkpoint_root / 'optimizer_rng.pt') == checkpoint['checkpoint_sha256']['optimizer']
        == checkpoint['checkpoint_sha256']['rng'] and checkpoint['optimizer_steps'] == 9740,
        'durable9740_optimizer_RNG')
    capacity = os.statvfs(CONTROL)
    require(capacity.f_bavail * capacity.f_frsize > 3 * 1024**3, 'owner_available_safety_headroom')
    before = process_and_gpu_check()
    publication_pin = write_once(CONTROL / 'BUILDER1450_PUBLICATION.json', publication)
    allocation.update(builder_entry_logged=True, builder_publication=publication_pin)
    allocation_pin = write_once(CONTROL / 'ALLOCATION_BUILDER1450.json', allocation)
    final_guard = dict(candidate, allocation_path=allocation_pin['path'], allocation_sha256=allocation_pin['sha256'])
    require({key for key in final_guard if final_guard[key] != candidate[key]}
        == {'allocation_path', 'allocation_sha256'}, 'only_allocation_guard_delta')
    guard_pin = write_once(CONTROL / 'GUARD_BUILDER1450.json', final_guard)
    from gpu import orch_r125_continual_guard as guard
    checked_guard, checked_plan = guard.validate(Path(guard_pin['path']))
    require(checked_guard == final_guard and checked_plan == plan, 'original_guard_pass')
    fresh = process_and_gpu_check()
    command = [INTERPRETER, '-B', '-m', 'gpu.ws6_math_b_pending_entry', 'dispatch', '--config', guard_pin['path']]
    intent = dict(utc=datetime.now(timezone.utc).isoformat(), guard=guard_pin, allocation=allocation_pin,
        publication=publication_pin, source_sha256=SOURCE_HASH, command=command, cwd=str(source),
        precheck=before, immediate_prelaunch=fresh, owner_available_bytes=capacity.f_bavail * capacity.f_frsize,
        automatic_retry=False, parent_started=False, seven_native_parent_prerequisite_unchanged=True,
        admission_method='original_dispatch_privileged_scan_and_confinement_no_bypass')
    intent_pin = write_once(CONTROL / 'BUILDER1450_DISPATCH_INTENT.json', intent)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    with (CONTROL / 'BUILDER1450_DISPATCH.log').open('xb') as output:
        detached = subprocess.run(['setsid', '-f'] + command, cwd=source, env=environment,
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=10)
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), status='ONE_ORIGINAL_DISPATCH_REQUESTED_NOT_YET_LOADED',
        intent=intent_pin, detached_launcher_returncode=detached.returncode, guard=guard_pin,
        admission_or_recovery_success_claimed=False, automatic_retry=False, parent_started=False)
    write_once(CONTROL / 'BUILDER1450_DISPATCH_REQUESTED.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--remote':
        try:
            remote_main(json.loads(sys.stdin.readline()))
        except BaseException as error:
            failure = dict(utc=datetime.now(timezone.utc).isoformat(), status='STOP_NO_AUTOMATIC_RETRY',
                error_type=type(error).__name__, error=str(error))
            write_once(CONTROL / 'BUILDER1450_LAUNCHER_FAILED.json', failure)
            print(json.dumps(failure, sort_keys=True), flush=True)
            raise
        return
    raw = subprocess.run(['git', 'show', COMMIT + ':' + DOCUMENT], cwd=REPO,
        check=True, capture_output=True).stdout
    entries = [entry for entry in raw.decode().splitlines() if entry.startswith('[Builder] 2026-09-19T14:50Z')]
    require(len(entries) == 1, 'one_exact_Builder1450_entry')
    publication = dict(git_commit=COMMIT, repo_path=DOCUMENT, entry=entries[0],
        entry_sha256=hashlib.sha256(entries[0].encode()).hexdigest(),
        document_sha256=hashlib.sha256(raw).hexdigest())
    ready = json.loads((HERE / 'MATH_B_RELOCATION_V3_READY.json').read_bytes())
    payload = dict(publication=publication, ready={key: value for key, value in ready.items() if key != 'source_pins'})
    own_source = Path(__file__).read_text()
    program = own_source.rsplit("if __name__ == '__main__':", 1)[0]
    program += '\ntry:\n    remote_main(' + repr(payload) + ')\n'
    program += "except BaseException as error:\n    write_once(CONTROL / 'BUILDER1450_LAUNCHER_FAILED.json', dict(utc=datetime.now(timezone.utc).isoformat(), status='STOP_NO_AUTOMATIC_RETRY', error_type=type(error).__name__, error=str(error)))\n    raise\n"
    with (HERE / 'MATH_B_BUILDER1450_DISPATCH.stderr').open('xb') as errors:
        result = subprocess.run(['bash', 'gpu/ovx2_ssh.sh',
            'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 ' + INTERPRETER + ' -B -'],
            cwd=REPO, input='__file__ = ' + repr(str(CONTROL / 'launch_math_b_v3.py')) + '\n' + program,
            text=True, stdout=subprocess.PIPE, stderr=errors, timeout=180)
    write_once(HERE / 'MATH_B_BUILDER1450_DISPATCH_RESULT.json', dict(
        utc=datetime.now(timezone.utc).isoformat(), returncode=result.returncode, stdout=result.stdout))
    print(result.stdout, end='')
    require(result.returncode == 0, 'remote_binding_or_dispatch_failed_no_retry')


if __name__ == '__main__':
    main()
