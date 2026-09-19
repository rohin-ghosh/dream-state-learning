"""Validate Main's exported V3 proof artifacts locally; never contact a node."""

import hashlib
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
SPRINT = HERE.parent
CANDIDATE = SPRINT / 'replication'
OPERATIONS = SPRINT / 'operations'
FREEZE_SHA256 = 'd6c99489e68497af4dbbfd4f3c347ac73d09cdfb592c57341b7103db713b283b'
PROOF_SHA256 = 'af813b207130fe637676bda10576c3e6d4f4a27bfe400b7b0151cd60fb5312ed'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt_sha(value):
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    return hashlib.sha256(payload).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def review():
    paths = {
        'freeze': CANDIDATE / 'SAMPLING_SOURCE_FREEZE_V3.json',
        'authorization': CANDIDATE / 'SAMPLING_EXECUTION_AUTHORIZATION_V3.json',
        'registry': CANDIDATE / 'SAMPLING_REGISTRY_V3.json',
        'originals': CANDIDATE / 'ORIGINALS_RECEIPT.json',
        'prepared': OPERATIONS / 'SAMPLING_V3_PREPARED.json',
        'proof_summary': OPERATIONS / 'SAMPLING_V3_PROOFS.json',
        'custody': OPERATIONS / 'SAMPLING_V3_CUSTODY_EVIDENCE.json',
        'claim_release': OPERATIONS / 'SAMPLING_V2_FAILED_CLAIMS_RELEASE.json',
        'builder': OPERATIONS / 'BUILDER_ENTRIES.txt',
    }
    before = {name: sha(path) for name, path in paths.items()}
    documents = {name: read(path) for name, path in paths.items() if name != 'builder'}
    freeze = documents['freeze']
    registry = documents['registry']
    authorization = documents['authorization']
    prepared = documents['prepared']
    summary = documents['proof_summary']
    evidence = documents['custody']
    completion = evidence['completion']
    root = Path(registry['root'])
    require(before['freeze'] == FREEZE_SHA256 == prepared['source_freeze_sha256'], 'exact_source_freeze')
    require(before['registry'] == prepared['registry_sha256'], 'exact_prepared_registry')
    require(before['authorization'] == freeze['cpu_repair_sha256'], 'exact_authorization_bytes')
    require(registry['cpu_repair'] == authorization and registry['proof_only'] is False
        and authorization['model_execution_authorized'] is True
        and authorization['model_dispatch_requires_fresh_custody'] is True, 'explicit_v3_scope')
    require(registry['execution_incarnation_sha256'] == freeze['execution_incarnation_sha256']
        == root.name and summary['root'] == evidence['root'] == str(root), 'one_v3_incarnation')
    for name, expected in freeze['files'].items():
        require(sha(CANDIDATE / name) == expected, 'frozen_runtime:' + name)
    require(evidence['status'] == 'SIX_REAL_ROLE_PROOFS_VERIFIED_NO_MODELS', 'actual_role_evidence')
    require(receipt_sha(completion) == PROOF_SHA256 == evidence['proofs_complete_sha256']
        == summary['proof_sha256'], 'exact_joined_completion_bytes')
    require(completion['model_loaded'] is False
        and completion['status'] == summary['status'] == 'CPU_PROOFS_COMPLETE_MAIN_REVIEW_REQUIRED',
        'proof_completion_not_science')
    require(completion['diagnostic_epoch_sha256'] == registry['diagnostic_epoch_sha256']
        == freeze['diagnostic_epoch_sha256'], 'same_scientific_epoch')
    require(completion['deadline_unix'] == summary['deadline_unix'] <= registry['hard_end_unix'],
        'unchanged_wall_and_lease_bound')
    jobs = {job['job_id']: job for job in registry['jobs']}
    staged = {job['job_id']: job for job in prepared['jobs']}
    expected_keys = {job_id + ':' + role for job_id in jobs for role in ('judge', 'player')}
    require(len(expected_keys) == 6 and set(completion['proof_files']) == expected_keys, 'all_six_roles')
    require(len(evidence['roles']) == 6 and {role['key'] for role in evidence['roles']} == expected_keys,
        'exact_role_denominators')
    rows = []
    for item in evidence['roles']:
        job_id, role = item['key'].split(':')
        job = jobs[job_id]
        proof = item['proof']
        reference = completion['proof_files'][item['key']]
        view = Path(job['root']) / 'view'
        require(item['path'] == reference['path'] == str(view / (role + '_CUSTODY_PROOF.json')),
            'correct_role_receipt_path')
        require(receipt_sha(proof) == item['sha256'] == reference['sha256'], 'exact_role_proof_bytes')
        require(proof['config_sha256'] == staged[job_id]['config_sha256']
            and proof['launch_sha256'] == completion['launch_sha256']
            and proof['diagnostic_epoch_sha256'] == registry['diagnostic_epoch_sha256'], 'role_config_launch_epoch_join')
        require(proof['role'] == role and proof['status'] == 'PROVED_NO_MODEL_LOADED'
            and proof['model_loaded'] is False, 'successful_non_model_role')
        require(proof['uid'] == registry['original_policy']['expected_uid']
            and proof['boot_id'] == registry['original_policy']['receiving_boot_id'], 'original_uid_and_boot')
        original = documents['originals']['rows'][job['arm']]
        expected_denials = {
            str(root / 'CUSTODY_CANARY'),
            str(Path(original['root']) / 'judge/REFERENCE_PANELS.private.json'),
            original['files']['PRIMARY_PANELS.private.json']['path'],
            '/proc/1/root', registry['claims_namespace'],
            '/localhome/local-rohing/post_reboot_probe_queue_20260919/inputs',
        }
        if role == 'player':
            expected_denials.update(str(view / relative) for relative in (
                'judge/REFERENCE_PANELS.private.json', 'epoch/PRIMARY_PANELS.private.json', 'epoch/JUDGE_EPOCH.json'))
        require(set(proof['private_denials']) == expected_denials
            and all(value is True for value in proof['private_denials'].values()), 'every_original_path_denied')
        device = registry['role_devices'][role]['physical']
        require(set(proof['device_opens']) == {str(index) for index in range(8)}, 'eight_device_denominators')
        require({index for index, outcome in proof['device_opens'].items() if outcome['opened'] is True}
            == {str(device)}, 'only_original_assigned_device_opened')
        unit_name = 'orch-sampling-' + job_id[:16] + '-' + role + '-proof'
        state = completion['unit_states'][unit_name]
        require(state['LoadState'] == 'loaded' and state['Result'] == 'success'
            and state['ExecMainStatus'] == '0' and state['SubState'] == 'exited'
            and int(state['ExecMainPID']) == proof['pid'], 'same_successful_unit_pid')
        require(prepared['observed_unix'] <= proof['observed_unix'] <= completion['observed_unix'],
            'proof_after_staging_before_completion')
        rows.append(dict(arm=job['arm'], role=role, pid=proof['pid'], sha256=item['sha256'],
            config_sha256=proof['config_sha256'], private_denials=len(expected_denials),
            assigned_device=device, other_devices_denied=7, model_loaded=False,
            observed_unix=proof['observed_unix']))
    release = documents['claim_release']
    require(release['status'] == 'DEAD_CPU_PROOF_CLAIMS_ARCHIVED_GUARDS_PRESERVED'
        and release['failed_guards_unchanged'] is True and release['automatic_retry_enabled'] is False,
        'old_failure_preserved')
    require(release['evidence']['prior_guard_refs'] == authorization['prior_refs']
        and release['evidence']['no_models'] is True, 'preserved_v2_source_and_guards')
    for uuid, claim in release['claims'].items():
        expected = authorization['claim_observation']['claims'][uuid]
        require(claim['sha256'] == expected['sha256'] and claim['original'] == expected['path']
            and claim['claim']['job_id'] == authorization['claim_observation']['job_id'], 'same_archived_claim')
    builder = paths['builder'].read_text()
    require(any('[Builder]' in line and 'PRE-GPU' in line and FREEZE_SHA256 in line
        and PROOF_SHA256 in line and root.name in line for line in builder.splitlines()), 'dated_bound_builder_decision')
    after = {name: sha(path) for name, path in paths.items()}
    require(before == after, 'artifacts_stable_during_review')
    return dict(status='V3_SOURCE_AND_ACTUAL_CUSTODY_REVIEW_PASS',
        observed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        scope='LOCAL_REVIEW_OF_MAIN_EXPORTED_PRIMARY_ARTIFACTS_NO_RECEIVING_COMMANDS',
        source_freeze_sha256=FREEZE_SHA256, joined_proof_sha256=PROOF_SHA256,
        execution_incarnation_sha256=root.name, scientific_epoch_sha256=registry['diagnostic_epoch_sha256'],
        role_results=rows, artifact_sha256=before,
        same_original_uid_boot_devices_private_denials=True, independent_model_calls=False,
        preexisting_placeholder_race_guard='sealed preparation creates every underlying private target before PREPARED',
        exact_mount_table_exported=False, scientific_outcome_claimed=False,
        remaining_block_seconds_at_review=completion['deadline_unix'] - time.time(),
        model_dispatch_owner='Main; fixed existing block, fresh original admission still required')


if __name__ == '__main__':
    result = review()
    destination = HERE / 'V3_RECEIVING_REVIEW.json'
    with destination.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
