import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


index = read(ROOT / 'INDEX.json')
fresh_path = ROOT / 'activation4_followup/C2.json'
fresh = read(fresh_path)
custody = fresh['refreshed_custody']
assert custody['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
assert custody['last_completed_sleep'] == 32 and custody['registry_plan_birth_context_matches']
assert fresh['all_checked_pins_match']
assert fresh['native_identity']['pid'] == 4077813 and fresh['native_identity']['start_ticks'] == '17169605'
assert fresh['source_root'] == '/localhome/local-rohing/orch_r166_retelling_C2_20260917_activation4/source'
observation = dict(status='IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED', life_id='C2',
    source_root=custody['source_root'], last_completed_sleep=custody['last_completed_sleep'],
    observed_unix=custody['observed_unix'], native_identity=fresh['native_identity'],
    TRAIN_and_source_custody=ref(fresh_path), journal_tail_index=custody['tail_index_at_listing'],
    scope='Captured activation4 owner/tail snapshot, not ongoing registration or execution authority.',
    grants_source_read_copy_or_GPU_authority=False)
new_observation = ROOT / 'observations/C2_activation4.json'
write(new_observation, observation)
for row in index['lives']:
    if row['life_id'] == 'C2' and row['node'] == 'ovx3':
        row.update(native_identity=fresh['native_identity'], last_completed_sleep=32,
            source_custody=ref(fresh_path), TRAIN_custody=ref(fresh_path),
            frontier_observed_unix=custody['observed_unix'], journal=custody['journal'],
            birth_record=custody['initial_record'], initial_commit=custody['initial_commit'],
            completed_boundary=custody['completed_boundary'], tail_index=custody['tail_index_at_listing'],
            static_runtime_source_file_count=len(fresh['source_files']), cumulative_reads=custody['reads'],
            registration_observation_candidate=ref(new_observation),
            ownership_disposition='NEW_ACTIVATION4_OWNER_VERIFIED_AT_CAPTURE_NO_REGISTRATION_DONE')
    elif row['life_id'] in ['C1', 'C4'] and row['node'] == 'ovx3':
        row['ownership_disposition'] = 'PRIOR_OWNER_MATCHED_FINAL_CHECK_PENDING_HANDOFF_RECHECK_BEFORE_BINDING'
    elif 'native_identity' in row:
        row['ownership_disposition'] = 'SAME_OWNER_MATCHED_FINAL_CHECK_SNAPSHOT_ONLY'
    if 'cumulative_reads' in row:
        assert row['cumulative_reads']['journal_bytes'] <= 64 * 1024 ** 2
        assert row['cumulative_reads']['metadata_bytes'] <= 32 * 1024 ** 2
owners_path = ROOT / 'activation4_followup/OWNER_IDENTITIES.json'
assert all(item['same_identity'] for item in read(owners_path)['owner_identity_check'])
assert ref(Path(index['registry']['path'])) == index['registry']
delivery = dict(schema='R167_FLEET_CUSTODY_CURRENT_DELIVERY_V2', prepared_unix=time.time(),
    previous_index=ref(ROOT / 'INDEX.json'), registry=index['registry'], registry_unchanged=True,
    superseded_observation_for_new_binding=ref(ROOT / 'observations/C2.json'),
    ownership_refresh=ref(owners_path), banach_metadata_projection=ref(ROOT / 'activation4_followup/BANACH_METADATA_PROJECTION.json'),
    updated_handoff=ref(ROOT / 'HANDOFF_CURRENT.md'), counts=index['counts'], lives=index['lives'],
    no_registration_or_source_authority_issued=True, handoff_sensitive_lives=['C1', 'C4'],
    tests=ref(ROOT / 'closure_attempt1/CPU.log'), source_tests_passed=8,
    model_calls=0, signals=0, remote_writes=0, held_or_evaluation_files_opened=0,
    C5_release_request=ref(ROOT / 'BANACH_RELEASE_REQUEST.md'))
write(ROOT / 'CURRENT_DELIVERY.json', delivery)
print('CURRENT_DELIVERY SHA256', ref(ROOT / 'CURRENT_DELIVERY.json')['sha256'])
print('Total cumulative TRAIN bytes',sum(row.get('cumulative_reads', {}).get('journal_bytes',0) for row in delivery['lives']))
print('Total cumulative metadata bytes',sum(row.get('cumulative_reads', {}).get('metadata_bytes',0) for row in delivery['lives']))
