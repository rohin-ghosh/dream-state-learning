from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT.parent
REPO = ROOT.parents[3]


def read(path):
    return json.loads(path.read_text())


def pair(value):
    return {key: value[key] for key in ['path', 'sha256']}


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


release_path = ROOT / 'RECOVERY_RELEASE.json'
frontier_path = ROOT / 'CURRENT_FRONTIER.json'
source_path = ROOT / 'RUNTIME_SOURCE.json'
release, frontier, source = [read(path) for path in [release_path, frontier_path, source_path]]
batch_path = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
batch = read(batch_path)
life = next(row for row in batch['lives'] if row['life_id'] == 'C5')
native = {key: frontier['native_identity'][key] for key in ['pid', 'start_ticks', 'boot_id']}
assert release['status'] == 'EXACT_RECOVERY_COMMITTED'
assert frontier['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
assert frontier['identity_rechecked'] and frontier['current_plan_exact_storage_root']
assert frontier['registry_plan_birth_context_matches'] and frontier['completed_birth_context_matches_initial']
assert frontier['completed_history_TRAIN_only'] and frontier['queue_checkpoint_path_matches_storage_root']
assert native == release['native_identity'] == source['native_identity']
assert release['observed_unix'] <= frontier['observed_unix'] and batch['frozen_unix'] <= frontier['observed_unix']
assert release['source_root'] == frontier['source_root'] == life['storage_root']
assert release['birth_plan'] == pair(frontier['registry_birth_plan']) == life['birth_plan']
assert pair(release['journal']) == pair(frontier['journal'])
assert source['all_checked_pins_match']
assert frontier['initial_commit']['optimizer_steps'] == 0
assert frontier['initial_commit']['schema'] == 'R125_NATIVE_CONTINUITY_V1'
assert frontier['reads']['journal_bytes'] <= 64 * 1024 ** 2
assert frontier['reads']['metadata_bytes'] <= 32 * 1024 ** 2
assert reference(batch_path) == read(ROOT / 'ACQUISITION.json')['registry']

observation = dict(status='IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED', life_id='C5',
    source_root=frontier['source_root'], last_completed_sleep=frontier['last_completed_sleep'],
    observed_unix=frontier['observed_unix'], native_identity=native,
    journal=pair(frontier['journal']), birth_plan=pair(frontier['registry_birth_plan']),
    recovery_release=reference(release_path), custody=reference(frontier_path),
    runtime_source_custody=reference(source_path), captured_tail=frontier['tail'],
    scope='Authenticated BIRTH/INITIAL and reverse suffix at captured tail, not full historical replay or an ongoing live claim.',
    grants_source_read_copy_or_GPU_authority=False)
observation_path = ROOT / 'REGISTRATION_OBSERVATION.json'
write(observation_path, observation)
canonical = dict(source_root=life['storage_root'], journal=pair(frontier['journal']),
    birth_plan=pair(frontier['registry_birth_plan']), recovery_release=reference(release_path),
    registration_observation=reference(observation_path))
for key in ['journal', 'birth_plan', 'recovery_release', 'registration_observation']:
    assert set(canonical[key]) == {'path', 'sha256'}
delivery = dict(schema='R167_C5_EUCLID_CUSTODY_INDEX_V1', recipient='Euclid',
    status='RECOVERY_RELEASE_AND_COMPLETED_FRONTIER_VERIFIED', life_id='C5',
    registry=reference(batch_path), canonical_queue_refs=canonical, native_identity=native,
    runtime_source_root=source['source_root'], runtime_source_custody=reference(source_path),
    checked_static_runtime_files=len(source['source_files']), all_checked_source_pins_match=True,
    last_completed_sleep=frontier['last_completed_sleep'],
    prospective_first_sleep=frontier['last_completed_sleep'] + 1, prospective_sleep_count=3,
    prospective_sleep_ids=list(range(frontier['last_completed_sleep'] + 1, frontier['last_completed_sleep'] + 4)),
    release_observed_unix=release['observed_unix'], frontier_observed_unix=frontier['observed_unix'],
    frontier_observed_utc=datetime.fromtimestamp(frontier['observed_unix'], timezone.utc).isoformat(),
    latest_captured_tail_index=frontier['tail_index_at_listing'], latest_captured_tail_kind=frontier['tail']['kind'],
    completed_sleep_record=frontier['completed_boundary']['record'],
    completed_checkpoint=frontier['completed_boundary']['checkpoint']['reference'],
    original_birth_record=frontier['initial_record'], initial_checkpoint=frontier['initial_commit']['reference'],
    original_birth_fields_match=True, initial_checkpoint_state_bound=True,
    restored_saved_sleep=release['saved_completed_sleep'], restored_optimizer_steps=release['saved_optimizer_steps'],
    actual_committed_generation_segments=[item['segment'] for item in release['real_committed_generations']],
    actual_invitation_record=release['actual_invitation_record'],
    actual_invitation_committed_record=release['actual_invitation_commit'],
    semantic_correctness_or_retention_claim=False, no_new_sleep_needed_for_release=True,
    cumulative_reads=frontier['reads'], cpu_tests=reference(ROOT / 'CPU.log'), cpu_tests_passed=8,
    acquisition=reference(ROOT / 'ACQUISITION.json'),
    preserved_first_check=reference(ROOT.parent / 'c5_recovery_attempt1/RECOVERY_RELEASE.json'),
    queue_or_registry_writes=0, remote_writes=0, signals=0, model_calls=0,
    held_or_evaluation_access=False, source_copy_or_GPU_authority_issued=False,
    remaining_scope='Main source-owner read/copy authority and exact plan freeze/receiving custody remain separate.',
    fleet_disposition='Supersedes C5 pending-release row only. Repo_reader remains explicit partial; do not make it a fleet-wide gate. Other lives retain their own evidence/ownership requirements.')
output = DESTINATION / 'EUCLID_C5_CUSTODY_INDEX.json'
write(output, delivery)
print('EUCLID_C5_CUSTODY_INDEX SHA256', reference(output)['sha256'])
print('Recovery release SHA256', reference(release_path)['sha256'])
print('Registration observation SHA256', reference(observation_path)['sha256'])
print('Canonical queue refs', json.dumps(canonical, sort_keys=True))
