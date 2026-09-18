import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def read(path):
    return json.loads(path.read_text())


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


batch_path = REPO / 'research_loop/workers/r167_object_survival/fleet_generation1/BATCH_PLAN.json'
batch = read(batch_path)
wanted = ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader']
observations = ROOT / 'observations'
observations.mkdir(exist_ok=False)
rows = []
for life in batch['lives']:
    name = life['life_id']
    row = dict(life_id=name, node=life['node'], storage_root=life['storage_root'],
               registry_birth_plan=life['birth_plan'])
    if name not in wanted or life['node'] != 'ovx3':
        row['status'] = ('PENDING_BANACH_EXACT_RECOVERY_RELEASE' if name == 'C5' and life['node'] == 'ovx3'
                         else 'OUTSIDE_REQUESTED_NODE5_FIRST_PASS')
        rows.append(row)
        continue
    source_path = ROOT / 'closure_attempt1' / (name + '.json')
    source = read(source_path)
    custody_path = ROOT / 'train_attempt1' / (name + '.json')
    custody = read(custody_path)['custody']
    if name == 'repo_reader':
        custody, custody_path = source['alias_custody'], source_path
    assert custody['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
    assert custody['identity_rechecked'] and custody['completed_history_TRAIN_only']
    assert custody['completed_birth_context_matches_initial'] and source['all_checked_pins_match']
    assert source['native_identity'] == {key: custody['native_identity'][key]
                                         for key in ['pid', 'start_ticks', 'boot_id']}
    reads = dict(custody['reads'])
    reads['metadata_bytes'] = max(reads['metadata_bytes'], source['cumulative_metadata_bytes'])
    blockers = []
    if not custody['registry_plan_birth_context_matches']:
        blockers.append('REGISTRY_PLAN_BIRTH_DIFFERS_FROM_AUTHENTICATED_INITIAL_HISTORY')
    if custody['initial_commit'].get('present') is False:
        blockers.append('INITIAL_COMMIT_ABSENT_FROM_RESTORED_STORAGE_ROOT')
    if custody.get('queue_checkpoint_path_matches_storage_root') is False:
        blockers.append('LOGICAL_CHECKPOINT_PATH_DIFFERS_FROM_QUEUE_REQUIRED_PHYSICAL_STORAGE_PATH')
    if name == 'continual_run1':
        fields = read(ROOT / 'closure_attempt1/RUN1_FIELD_BINDING.json')
        reads = fields['reads']
        row['exact_field_comparison'] = reference(ROOT / 'closure_attempt1/RUN1_FIELD_BINDING.json')
        row['matching_original_birth_plan'] = custody['original_plan_candidates'][0]['reference']
    assert reads['metadata_bytes'] <= 32 * 1024 ** 2 and reads['journal_bytes'] <= 64 * 1024 ** 2
    row.update(status='CUSTODY_METADATA_READY_FOR_OWNER_PLAN' if not blockers else 'CUSTODY_VERIFIED_QUEUE_BLOCKERS',
        native_identity=source['native_identity'], last_completed_sleep=custody['last_completed_sleep'],
        frontier_observed_unix=custody['observed_unix'], journal=custody['journal'],
        birth_record=custody['initial_record'], initial_commit=custody['initial_commit'],
        completed_boundary=custody['completed_boundary'], tail_index=custody['tail_index_at_listing'],
        source_custody=reference(source_path), TRAIN_custody=reference(custody_path),
        static_runtime_source_file_count=len(source['source_files']), all_static_pins_match=True,
        cumulative_reads=reads, blockers=blockers)
    if not blockers:
        observation = dict(status='IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED', life_id=name,
            source_root=life['storage_root'], last_completed_sleep=custody['last_completed_sleep'],
            observed_unix=custody['observed_unix'], native_identity=source['native_identity'],
            TRAIN_custody=reference(custody_path), source_custody=reference(source_path),
            journal_tail_index=custody['tail_index_at_listing'],
            scope='Captured journal-tail snapshot; authenticated birth and reverse suffix, not full historical replay.',
            grants_source_read_copy_or_GPU_authority=False)
        observation_path = observations / (name + '.json')
        write(observation_path, observation)
        row['registration_observation_candidate'] = reference(observation_path)
    rows.append(row)

files = []
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and not any(part.startswith('test_tmp') or part == '__pycache__'
                                  for part in path.relative_to(ROOT).parts):
        files.append(reference(path))
original_batch = read(ROOT / 'ACQUISITION.json')['batch']
assert reference(batch_path) == original_batch
index = dict(schema='R167_FLEET_CUSTODY_EVIDENCE_INDEX_V1', prepared_unix=time.time(),
    registry=reference(batch_path), registry_unchanged=True,
    api=reference(REPO / 'research_loop/workers/r167_object_survival/FLEET_PROSPECTIVE_API.md'),
    counts=dict(registry_lives=21, acquired=7, authentic_frontiers=7,
                queue_compatible_metadata_candidates=5, queue_blocked=2, C5_owner_release_pending=1,
                outside_first_pass=13),
    cpu_tests=reference(ROOT / 'closure_attempt1/CPU.log'), cpu_tests_passed=8,
    no_GPU_calls=True, no_remote_writes=True, no_signals=True, no_evaluation_or_held_access=True,
    registry_queue_mutations=0, grants_source_copy_or_GPU_authority=False,
    lives=rows, artifacts=files)
write(ROOT / 'INDEX.json', index)
print(json.dumps(index['counts'], sort_keys=True))
print('INDEX SHA256', reference(ROOT / 'INDEX.json')['sha256'])
print('Cumulative TRAIN bytes', sum(row.get('cumulative_reads', {}).get('journal_bytes', 0) for row in rows))
print('Cumulative metadata bytes', sum(row.get('cumulative_reads', {}).get('metadata_bytes', 0) for row in rows))
