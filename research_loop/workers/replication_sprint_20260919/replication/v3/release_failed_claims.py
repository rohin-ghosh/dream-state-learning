"""Archive only the verified dead CPU proof's reservations; never reset its guards."""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

import execution as common
from construct_candidate import require


HERE = Path(__file__).resolve().parent
AUDITS = common.BASE / 'post_sampling_claim_dispositions_20260919'


def expected_unit(root, job, role, launch, launch_sha):
    unit = 'orch-sampling-' + job['job_id'][:16] + '-' + role + '-proof.service'
    argv = [str(common.PYTHON), '-B', str(root / 'runtime/sealed_runner.py'),
        '--config', str(Path(job['root']) / 'CONFIG.json'), '--config-sha256', launch['job_configs'][job['job_id']],
        '--launch-sha256', launch_sha, '--role', role, '--mode', 'proof']
    return dict(unit=unit, argv=argv, job_id=job['job_id'], role=role)


def observe_unit(unit):
    fields = ('Id', 'LoadState', 'ActiveState', 'SubState', 'Result', 'ExecMainStatus', 'ExecMainPID',
        'MainPID', 'ControlPID', 'ControlGroup', 'InvocationID', 'User', 'Group', 'Transient', 'ExecStart')
    result = subprocess.run(['systemctl', 'show', unit, '--property=' + ','.join(fields)],
        capture_output=True, text=True, timeout=10, check=False)
    require(result.returncode == 0, 'owned_unit_identity_observation_required')
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def validate_unit(state, expected):
    require(state.get('Id') == expected['unit'] and state.get('LoadState') == 'loaded'
        and state.get('Transient') == 'yes' and state.get('User') == state.get('Group') == '1352'
        and state.get('InvocationID'), 'exact_owned_transient_identity')
    arguments = re.fullmatch(r'\{ path=([^;]+?) ; argv\[\]=(.*?) ; ignore_errors=.*\}', state.get('ExecStart', ''))
    require(arguments is not None and arguments.group(1) == str(common.PYTHON)
        and shlex.split(arguments.group(2)) == expected['argv'], 'exact_owned_cpu_proof_command')
    terminal = state.get('ActiveState') in ('failed', 'inactive') or (
        state.get('ActiveState') == 'active' and state.get('SubState') == 'exited')
    require(terminal and state.get('MainPID') == '0' and state.get('ControlPID') == '0'
        and state.get('Result') in ('success', 'exit-code', 'timeout', 'signal', 'core-dump')
        and int(state.get('ExecMainPID', '0')) > 0, 'owned_cpu_proof_terminal')


def verify_no_processes(state):
    require(not Path('/proc', state['ExecMainPID']).exists(), 'recorded_proof_pid_still_present')
    group = state.get('ControlGroup')
    if group:
        require(group.startswith('/') and '..' not in Path(group).parts, 'canonical_systemd_control_group')
        root = Path('/sys/fs/cgroup') / group.lstrip('/')
        if root.exists():
            events = dict(line.split() for line in (root / 'cgroup.events').read_text().splitlines())
            require(events.get('populated') == '0' and not (root / 'cgroup.procs').read_text().strip(),
                'proof_cgroup_must_be_empty')


def audit_failed_proof(repair):
    require(repair['claim_disposition_authorization'], 'explicit_dead_claim_disposition_authorization')
    common.verify_prior_failed_cpu_proof(dict(cpu_repair=repair,
        diagnostic_epoch_sha256=repair['diagnostic_epoch_sha256'], block_id=common.digest(repair)))
    root = Path(repair['prior_root'])
    document = common.read(root / 'REGISTRY.json')
    require(set(repair['claim_observation']['claims']) == {device['uuid'] for device in document['role_devices'].values()},
        'only_the_original_two_claims')
    for uuid, reference in repair['claim_observation']['claims'].items():
        require(reference['path'] == str(common.CLAIMS / (uuid + '.json')), 'original_claim_namespace_only')
    for name, checksum in common.read(root / 'SOURCE_FREEZE.json')['files'].items():
        common.regular(root / 'runtime' / name, checksum)
    original = common.load_v4()
    common.verify_host(document, original)
    launch = common.read(root / 'BLOCK_LAUNCH.json')
    units = []
    for job in document['jobs']:
        common.regular(Path(job['root']) / 'CONFIG.json', launch['job_configs'][job['job_id']])
        view = Path(job['root']) / 'view'
        require(not (view / 'JUDGE_LOADED.json').exists()
            and not list((view / 'players').glob('*/LOADED.json')), 'no_model_load_receipts')
        for role in ('judge', 'player'):
            expected = expected_unit(root, job, role, launch, repair['prior_refs']['BLOCK_LAUNCH.json']['sha256'])
            state = observe_unit(expected['unit'])
            validate_unit(state, expected)
            marker = common.read(view / (role + '_proof_STARTED.json'))
            require(marker['pid'] == int(state['ExecMainPID']) and marker['role'] == role
                and marker['mode'] == 'proof' and marker['config_sha256'] == launch['job_configs'][job['job_id']]
                and marker['launch_sha256'] == repair['prior_refs']['BLOCK_LAUNCH.json']['sha256']
                and marker['diagnostic_epoch_sha256'] == repair['diagnostic_epoch_sha256'],
                'same_invocation_as_preserved_role_start')
            verify_no_processes(state)
            units.append(dict(expected=expected, state=state, start_marker=marker,
                cgroup_empty=True, recorded_pid_absent=True))
    require(len(units) == 6 and len({row['state']['InvocationID'] for row in units}) == 6, 'six_exact_owned_invocations')
    inventory = original.gpu_inventory()
    original.validate_admission(common.original_inventory_config(document), inventory)
    return dict(observed_unix=time.time(), units=units, inventory=inventory,
        prior_guard_refs=repair['prior_refs'], block_id=document['block_id'], no_models=True)


def disposition(repair, release=False, namespace=common.CLAIMS, audit_parent=AUDITS, auditor=audit_failed_proof):
    observation = repair['claim_observation']
    with common.shared_lock(namespace):
        evidence = auditor(repair)
        require(evidence['block_id'] == observation['job_id'], 'same_failed_block')
        paths = []
        claims = {}
        for uuid, expected in observation['claims'].items():
            path = Path(namespace) / (uuid + '.json')
            common.regular(path, expected['sha256'])
            claim = common.read(path)
            require(claim['job_id'] == observation['job_id']
                and claim['created_unix'] == observation['created_unix']
                and claim['hold_until_unix'] == observation['hold_until_unix']
                and claim['diagnostic_epoch_sha256'] == repair['diagnostic_epoch_sha256'], 'ownership_matched_dead_claim')
            archive = path.with_name(uuid + '.failed.' + observation['job_id'] + '.json')
            require(not archive.exists(), 'failed_claim_archive_never_overwritten')
            paths.append((path, archive, expected['sha256']))
            claims[uuid] = dict(claim=claim, original=str(path), archive=str(archive), sha256=expected['sha256'])
        require(len(paths) == 2, 'both_original_reserved_lanes')
        result = dict(status='VERIFIED_DEAD_CPU_PROOF_CLAIMS_NOT_RELEASED', evidence=evidence, claims=claims,
            repair_sha256=common.digest(repair), failed_guards_unchanged=True, automatic_retry_enabled=False)
        if not release:
            return result
        audit_root = Path(audit_parent) / common.digest(dict(repair=repair, claim_hashes=observation['claims']))
        require(not audit_root.exists(), 'claim_disposition_never_repeated')
        audit_root.mkdir(mode=0o700, parents=True)
        common.write_once(audit_root / 'INTENT.json', result)
        for source, archive, expected_sha in paths:
            common.regular(source, expected_sha)
            source.rename(archive)
            common.regular(archive, expected_sha)
        directory = os.open(namespace, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        for reference in repair['prior_refs'].values():
            common.regular(Path(reference['path']), reference['sha256'])
        result.update(status='DEAD_CPU_PROOF_CLAIMS_ARCHIVED_GUARDS_PRESERVED', audit_root=str(audit_root))
        common.write_once(audit_root / 'COMPLETE.json', result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repair', type=Path, required=True)
    parser.add_argument('--repair-sha256', required=True)
    parser.add_argument('--seal', type=Path, required=True)
    parser.add_argument('--seal-sha256', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--release', action='store_true')
    args = parser.parse_args()
    common.regular(args.repair, args.repair_sha256)
    common.regular(args.seal, args.seal_sha256)
    seal = common.read(args.seal)
    require(seal['cpu_repair_sha256'] == args.repair_sha256
        and seal['files'] == {name: common.sha(HERE / name) for name in common.RUNTIME_NAMES}, 'sealed_disposition_source')
    repair = common.read(args.repair)
    print(common.json.dumps(disposition(repair, release=args.release), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
