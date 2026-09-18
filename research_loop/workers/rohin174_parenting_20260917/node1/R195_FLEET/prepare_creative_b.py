"""Stage fixed inputs and inspect actual receiving capability, without signals."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import time


OWN = Path(__file__).resolve().parent
REMOTE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MANIFEST_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'
SNAPSHOT_SHA = '9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34'
READY_SHA = '197df573816ffa95460881593fcebf6591c299be8ce7de16b7aa51309c727391'
OVERLAY_SHA = '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1'
GUARD = Path('/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay/lanes/lane7/identity_repair/control/GUARD.json')
GUARD_SHA = 'bebd9405765e439fea4490aafef78b958e7d8377e294c6b3c014c8ef34fc3e17'
PROFILE_SOURCE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/cpu_source_20260918t0212z')
GATE = '/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0212z/gate'
GATE_SHA = 'ca755cbd60be96fa310bff0c8149ed8777159e0e09dbd437c076190f7577356d'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    with Path(path).open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write('\n')


def unpack(archive_path, destination, expected):
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        require(len(members) == len(expected) == len({member.name for member in members}), 'exact_archive_members')
        for member in members:
            path = Path(member.name)
            require(member.isfile() and member.name in expected and not path.is_absolute()
                    and '..' not in path.parts, 'regular_bound_archive_member')
            require(hashlib.file_digest(archive.extractfile(member), 'sha256').hexdigest()
                    == expected[member.name], 'member_bytes')
            target = destination / member.name
            if target.exists():
                require(destination == OWN / 'source' and target.is_file()
                        and not target.is_symlink(), 'only_owned_source_overlay_replacement')
                target.chmod(0o600)
        archive.extractall(destination, filter='data')
    require(all(sha(destination / name) == digest for name, digest in expected.items()), 'received_bytes')


def remote_prepare(finish=False):
    require(OWN == REMOTE and socket.gethostname() == '[REDACTED_HOST]'
            and os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node1_CPU_operator')
    for name, expected in [('MANIFEST.json', MANIFEST_SHA), ('SNAPSHOT.tar', SNAPSHOT_SHA),
                           ('READY.json', READY_SHA), ('runtime_overlay.tar.gz', OVERLAY_SHA)]:
        require(sha(OWN / name) == expected, 'fixed_input_' + name)
    require(sha(GUARD) == GUARD_SHA, 'selected_original_guard')
    guard = read(GUARD)
    original_plan = read(guard['plan_path'])
    require(original_plan['physical'] == 7 and original_plan['hard_end_unix'] == 1790442300
            and original_plan['lease_end_unix'] == 1790463900, 'selected_slot_wall')
    source = OWN / 'source'
    old_source = Path(original_plan['source_root'])
    require({str(path.relative_to(old_source)): sha(path) for path in old_source.rglob('*.py')}
            == guard['source_pins'], 'actual_existing_node1_closure')
    require(shutil.disk_usage(OWN).free > 8 * 1024**3, 'receiving_disk_margin')
    capture = read(OWN / 'MANIFEST.json')
    if finish:
        require(not (OWN / 'SOURCE.json').exists(), 'unconsumed_receiving_assembly')
        overlay = read(OWN / 'READY.json')['files']
        previous = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
        require(set(guard['source_pins']).issubset(previous)
                and all(value in (guard['source_pins'].get(name), overlay.get(name))
                        for name, value in previous.items()), 'prior_copy_only_original_or_Main_bytes')
        require(all(sha(OWN / 'snapshot' / entry['relative']) == entry['sha256']
                    for entry in capture['files']), 'prior_capture_unchanged')
    else:
        unpack(OWN / 'SNAPSHOT.tar', OWN / 'snapshot',
               {entry['relative']: entry['sha256'] for entry in capture['files']})
        shutil.copytree(old_source, source)
    for path in [source, *source.rglob('*')]:
        require(not path.is_symlink() and path.stat().st_uid == os.getuid(), 'owned_new_source_only')
        path.chmod(0o700 if path.is_dir() else 0o600)
    ready = read(OWN / 'READY.json')
    unpack(OWN / 'runtime_overlay.tar.gz', source, ready['files'])
    for name, expected in [
        ('orch_r125_cpu_confinement_probe.py', '9117c4d72cdbb700e351f4625e763f96cf94341a3cf6d2a2cf3445687bfae48b'),
        ('orch_r125_bounded_capture.py', 'b45825aad250ad0305b1f2d2c1b475690a4c6dda89045f97d5ee63da1294119d')]:
        require(sha(PROFILE_SOURCE / 'gpu' / name) == expected, 'actual_gate_source')
        require('gpu/' + name not in ready['files'], 'no_Main_override')
        (source / 'gpu' / name).chmod(0o600)
        shutil.copy2(PROFILE_SOURCE / 'gpu' / name, source / 'gpu' / name)
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(OWN / 'SOURCE.json', dict(source_root=str(source), source_pins=pins,
        Main_overlay_unchanged=all(pins[name] == expected for name, expected in ready['files'].items()),
        source_snapshot_manifest_sha256=MANIFEST_SHA, Main_archive_sha256=OVERLAY_SHA))
    sys.path.insert(0, str(source))
    from gpu import orch_r125_cpu_experiment as cpu
    from organism_v6.orch_r125_continual_stream import ContinualStream
    from gpu.orch_r125_continual_native import NativeChild
    import torch
    require(cpu.digest(cpu.verify_gate(GATE)) == GATE_SHA, 'real_node1_gate_bound_to_receiving_source')
    saved = read(OWN / 'snapshot/complete/SLEEP_COMPLETE.json')['document']['resume_state']
    context = read(OWN / 'snapshot/console/CONTEXT_COMMITTED.json')['document']['state']
    restored = ContinualStream.restore(context, expected_sha256=capture['console_state_sha256'])
    require(restored.checkpoint() == context and saved['state']['rows'] == context['state']['rows']
            and saved['state']['sleep_frontier'] == context['state']['sleep_frontier'], 'exact_context_no_new_training')
    checkpoint = read(OWN / 'snapshot/complete/COMMIT.json')
    checkpoint['adapter_path'] = str(OWN / 'snapshot/complete/adapter')
    checkpoint['optimizer_rng_path'] = str(OWN / 'snapshot/complete/optimizer_rng.pt')
    NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 4908 and payload['optimizer']['state']
            and payload['parameter_names'] and len(payload['cuda_rng']) == 1, 'whole_saved_optimizer_RNG')
    require(not torch.cuda.is_initialized(), 'CPU_only_restore')
    capability = subprocess.run(['setpriv', '--no-new-privs', 'sudo', '-n', '/usr/bin/true'],
        capture_output=True, text=True, timeout=15)
    report = dict(status='STAGED_EXACT_SOURCE_CPU_VERIFIED_NOT_RECEIVER_READY', observed_unix=time.time(),
        source_manifest_sha256=sha(OWN / 'SOURCE.json'), snapshot_manifest_sha256=MANIFEST_SHA,
        Main_archive_sha256=OVERLAY_SHA, cycle=51, optimizer_steps=4908,
        console_record=5846, console_state_sha256=context['sha256'], console_new_training_rows=0,
        cuda_initialized=False, gate_root=GATE, gate_sha256=GATE_SHA,
        confined_sudo_probe_returncode=capability.returncode,
        confined_sudo_probe_stderr=capability.stderr[:1000],
        direct_CPU_dispatch_compatible_with_no_new_privileges=capability.returncode == 0,
        blockers=['Pinned capture lacks full journal prefix/intent chain required for native resume in a new root',
                  'Existing namespace clone binding and external CPU bridge must be bound before retirement; Main runtime bytes not edited'],
        preserved_support_boundary=None, retired=False, launched=False, LOADED=False,
        THINK=None, parent_publication=None, signals_sent=0, original_C2_calls=0,
        hard_end_unix=1790442300, lease_end_unix=1790463900)
    write(OWN / 'RECEIVING_PREPARATION.json', report)
    print(json.dumps(report, sort_keys=True))


def stage():
    repo = OWN.parents[4]
    capture = OWN.parents[1] / 'node5/R195_FLEET/MSG201/C2_SNAPSHOT_20260918T021847Z'
    main = repo / 'research_loop/workers/rohin201_c2_clones_20260917/main_ready'
    require((repo / 'gpu/a100_ssh.sh').is_file(), 'repository_root')
    inputs = [(capture / 'MANIFEST.json', MANIFEST_SHA), (capture / 'SNAPSHOT.tar', SNAPSHOT_SHA),
              (main / 'READY.json', READY_SHA), (main / 'runtime_overlay.tar.gz', OVERLAY_SHA)]
    for path, expected in inputs:
        require(sha(path) == expected, 'local_input_' + path.name)
    archive_path = OWN / 'CREATIVE_B_TRANSFER.tar'
    with tarfile.open(archive_path, 'x') as archive:
        for path, unused_hash in inputs:
            archive.add(path, arcname=path.name)
        archive.add(Path(__file__), arcname='prepare_creative_b.py')
    transfer_sha = sha(archive_path)
    receive = f'''import hashlib,pathlib,sys,tarfile
root=pathlib.Path({str(REMOTE)!r});root.mkdir(mode=0o700)
path=root/'TRANSFER.tar'
with path.open('xb') as output:
 while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk)
with path.open('rb') as handle:assert hashlib.file_digest(handle,'sha256').hexdigest()=={transfer_sha!r}
with tarfile.open(path) as archive:
 assert all(member.isfile() and pathlib.Path(member.name).name==member.name for member in archive.getmembers())
 archive.extractall(root,filter='data')
print('TRANSFER_VERIFIED')
'''
    with archive_path.open('rb') as incoming:
        subprocess.run(['bash', 'gpu/a100_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(receive)],
                       cwd=repo, stdin=incoming, check=True, timeout=240)
    command = f'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 {PYTHON} -B {REMOTE}/prepare_creative_b.py remote-prepare'
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=repo,
                            capture_output=True, text=True, timeout=240)
    with (OWN / 'CREATIVE_B_RECEIVING.stdout').open('x') as handle:
        handle.write(result.stdout)
    with (OWN / 'CREATIVE_B_RECEIVING.stderr').open('x') as handle:
        handle.write(result.stderr)
    require(result.returncode == 0, 'receiving_preparation_failed_see_scoped_stderr')
    write(OWN / 'CREATIVE_B_RECEIVING.json', json.loads(result.stdout))
    print(result.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'remote-prepare', 'remote-finish'))
    arguments = parser.parse_args()
    stage() if arguments.action == 'stage' else remote_prepare(arguments.action == 'remote-finish')
