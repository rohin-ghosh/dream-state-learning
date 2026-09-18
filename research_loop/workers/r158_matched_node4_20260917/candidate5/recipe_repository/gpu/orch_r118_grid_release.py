"""Release only the two authorized grid predecessors at complete DEV boundaries."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import time

from gpu import orch_r118_grid_shared_run as successor
from gpu import orch_r111_grid_release as process


APPROVAL = Path('/localhome/local-rohing/orch_r118_shared_adoption_source_20260915_v1')
ROSTER_SHA = '595f91e74065b69baee7e0be895fde98ab6bf872896848fea9a674118014f375'
EIGHT_SHA = '5bff8653270e7e83c87bf045c72912331c4265e3368b7c7b9e052a528bd377ca'
PAIR = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915')
SPECS = {
    'F4': dict(native=804107, guard=804050,
        native_cwd='/localhome/local-rohing/orch_r118_f4_wait600_source_20260915_v3',
        guard_cwd='/localhome/local-rohing/orch_r118_f4_wait600_source_20260915_v3',
        native_tail=['-m', 'gpu.orch_r118_f4_wait600', 'resident'],
        guard_tail=['-m', 'gpu.orch_r118_f4_wait600', 'guard']),
    'A4': dict(native=374239, guard=374024,
        native_cwd='/localhome/local-rohing/orch_r115_grid_source_20260915_v1',
        guard_cwd='/localhome/local-rohing',
        native_tail=['-m', 'gpu.orch_r115_grid_native', 'resident', '--root', str(PAIR/'A4')],
        guard_tail=['/localhome/local-rohing/orch_r115_grid_pair_20260915/launch_r116/orch_r116_grid_launch.py',
                    'guard', '--root', str(PAIR/'A4')]),
}
shared, grid, require = successor.shared, successor.grid, successor.require


def authorization(branch):
    require(branch in SPECS, 'owned_grid_pair_only')
    require(shared.sha(APPROVAL/'ROSTER.json') == ROSTER_SHA and
            shared.sha(APPROVAL/'EIGHT_READY.json') == EIGHT_SHA, 'actual_all8_Main_readiness_binding')
    roster = shared.read(APPROVAL/'ROSTER.json')
    prepared = shared.read(APPROVAL/'EIGHT_READY.json')
    require(set(roster) == set(shared.BRANCHES) and prepared['readiness'] == roster,
            'exact_eight_ready_sources')
    for binding in roster.values():
        require(shared.sha(binding['path']) == binding['sha256'], 'unchanged_ready_receipt')
    root = PAIR/branch
    ready = shared.read(root/'SHARED_CLIENT_READY.json')
    require(ready['root'] == str(root) and ready['inherited_bounds'] == prepared['branch_bounds'][branch],
            'same_root_and_bounds')
    require(shared.sha(ready['executable']['source']) == ready['executable']['sha256'] ==
            shared.sha(Path(successor.__file__)), 'exact_READY_successor_validator')
    return root, ready


def pin(branch, root):
    spec = SPECS[branch]
    config = shared.read(root/'CONFIG.json')
    require(successor.branch_for(config) == branch, 'original_allocation')
    identities = {}
    for role in ('native', 'guard'):
        pid = spec[role]
        directory = Path('/proc')/str(pid)
        identity = process.identity(directory)
        require(identity['uid'] == os.getuid() and str((directory/'cwd').resolve()) == spec[role+'_cwd'],
                'exact_own_process_cwd_uid')
        arguments = [part.decode() for part in (directory/'cmdline').read_bytes().split(b'\0') if part]
        expected = spec[role+'_tail']
        require(arguments[-len(expected):] == expected, 'exact_own_command')
        if role == 'native':
            require(('CUDA_VISIBLE_DEVICES='+config['uuid']).encode() in
                    (directory/'environ').read_bytes().split(b'\0'), 'same_assigned_GPU_UUID')
        identities[role] = dict(identity, role=role, cwd=spec[role+'_cwd'], command=arguments)
    return identities


def try_boundary(root, complete):
    try:
        snapshot = successor.capture_boundary(root, complete)
    except (ValueError, FileNotFoundError, json.JSONDecodeError):
        return None
    dev = root/'readouts'/f'{snapshot["completed_cycle"]:04d}'/'dev'/'COMPLETE.json'
    if not dev.is_file():
        return None
    for row in successor.read_ledger(root):
        if row['kind'] == 'PARENT' and not (
            root/'parent_claude'/f'P{row["number"]:04d}.claim'/'PUBLISHED.json').is_file():
            return None
    snapshot['dev_complete'] = grid.ref(dev)
    return snapshot


def preserved(root, snapshot):
    files = dict(snapshot['captures'])
    for key in ('complete', 'train_complete', 'ledger', 'carry', 'dev_complete'):
        binding = snapshot[key]
        files[str(Path(binding['path']).relative_to(root))] = binding['sha256']
    for name in ('CONFIG.json', 'SHARED_CLIENT_READY.json'):
        files[name] = shared.sha(root/name)
    for folder in ('parent_queue', 'parent_claude', 'parent_received'):
        for path in (root/folder).rglob('*.json'):
            if path.is_file():
                files[str(path.relative_to(root))] = shared.sha(path)
    return files


def release(branch):
    root, ready = authorization(branch)
    identities = pin(branch, root)
    output = root/'R118_SHARED_RELEASE'
    output.mkdir()
    shared.write(output/'ARMED.json', dict(branch=branch, root=str(root), identities=identities,
        authorization=dict(roster_sha256=ROSTER_SHA, eight_ready_sha256=EIGHT_SHA),
        ready=grid.ref(root/'SHARED_CLIENT_READY.json'), source=grid.ref(Path(__file__)),
        bounded_by=ready['inherited_bounds'], armed_unix=time.time(), no_quality_selection=True))
    descriptors = {role: os.pidfd_open(identity['pid']) for role, identity in identities.items()}
    stopped = set()
    seen = set()
    try:
        while time.time() < ready['inherited_bounds']['train_end_unix']:
            fresh = set(root.glob('cycles/*/CYCLE_COMPLETE.json')) - seen
            if not fresh:
                time.sleep(.001)
                continue
            seen.update(fresh)
            for role in ('native', 'guard'):
                expected = identities[role]
                current = process.identity(Path('/proc')/str(expected['pid']))
                require(all(current[key] == expected[key] for key in current), 'identity_unchanged_before_stop')
                signal.pidfd_send_signal(descriptors[role], signal.SIGSTOP)
                stopped.add(role)
            for role in stopped:
                directory = Path('/proc')/str(identities[role]['pid'])
                for unused in range(100):
                    if (directory/'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't'):
                        break
                    time.sleep(.001)
                else:
                    raise ValueError('exact_own_process_not_stopped')
            snapshot = try_boundary(root, max(fresh, key=lambda path: path.parent.name))
            if snapshot is None:
                for role in tuple(stopped):
                    signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                    stopped.remove(role)
                continue
            files = preserved(root, snapshot)
            shared.write(output/'BOUNDARY_OBSERVED.json', snapshot)
            shared.write(output/'PRESERVED.json', files)
            for role in ('guard', 'native'):
                signal.pidfd_send_signal(descriptors[role], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                stopped.remove(role)
                poller = select.poll(); poller.register(descriptors[role], select.POLLIN)
                require(bool(poller.poll(30000)), 'own_exit_required_no_force_kill')
                until = time.time()+5
                while Path('/proc', str(identities[role]['pid'])).exists() and time.time() < until:
                    time.sleep(.05)
                require(not Path('/proc', str(identities[role]['pid'])).exists(), 'predecessor_reaped_required')
            require(all(shared.sha(root/name) == expected for name, expected in files.items()),
                    'all_preserved_bytes_unchanged_after_release')
            receipt = dict(status='RELEASED', branch=branch, root=str(root),
                released_unix=time.time(), predecessors=list(identities.values()),
                boundary=grid.ref(output/'BOUNDARY_OBSERVED.json'),
                complete=snapshot['complete'], ledger=snapshot['ledger'], carry=snapshot['carry'],
                native_charged=snapshot['native_charged'], parent_charged=snapshot['parent_charged'],
                next_cycle=snapshot['next_cycle'], all_charged_captures_preserved=True,
                no_calls_retried=True, all_predecessors_exited=True, bounds=ready['inherited_bounds'])
            shared.write(output/'RELEASED.json', receipt)
            shared.write(root/'R118_SHARED_HANDOFF_BRANCH.json', dict(root=str(root),
                bounds=ready['inherited_bounds'], release=grid.ref(output/'RELEASED.json'),
                predecessors=list(identities.values()), preserved_files=files, next_cycle=snapshot['next_cycle']))
            return receipt
        shared.write(output/'NO_BOUNDARY.json', dict(status='NOT_RELEASED', native_unchanged=True,
            observed_unix=time.time(), reason='original_TRAIN_deadline'))
    finally:
        for role in stopped:
            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
        for descriptor in descriptors.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('branch', choices=tuple(SPECS))
    args = parser.parse_args()
    print(json.dumps(release(args.branch), sort_keys=True))
