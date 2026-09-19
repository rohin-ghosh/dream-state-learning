"""Pure continual replay, append-only corpus binding, and checkpoint transactions."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


ARMS = ('FULL', 'OFF')
CHECKPOINT_UPDATES = 128


def abort_applies(marker, controller_session):
    return not controller_session or marker.get('controller_session') == controller_session


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    sync_directory(path.parent)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@dataclass(frozen=True)
class ContinualLayout(GoalReplayLayout):
    def training_indexes(self, update):
        if type(update) is not int or update < 1:
            raise ValueError('positive_global_update_required')
        offset = update - 1
        return (offset % 128, 128 + offset % 82,
                210 + (2 * offset) % self.trajectory_rows,
                210 + (2 * offset + 1) % self.trajectory_rows)


def rank_positions(rank, world_size=2):
    partitions = {1: ((0, 1, 2, 3),), 2: ((0, 2), (1, 3)), 3: ((0, 3), (1,), (2,))}
    if world_size not in partitions or not 0 <= rank < world_size:
        raise ValueError('supported_rank_partition_required')
    return partitions[world_size][rank]


def initial_state(rows, manifest_sha256):
    return dict(schema='COMBINED_CONTINUAL_CORPUS_V1', version=0, rows=rows,
                initial_manifest_sha256=manifest_sha256, ingested=[], duplicates=[])


def append_batch(state, packet, *, held_math, held_route, held_question_hashes=()):
    if packet.get('schema') != 'COMBINED_CONTINUAL_ADMITTED_BATCH_V1':
        raise ValueError('explicit_admitted_batch_schema_required')
    batch_id = packet['batch_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', batch_id):
        raise ValueError('unsafe_batch_id')
    binding = digest(packet)
    for previous in state['ingested']:
        if previous['batch_id'] == batch_id:
            if previous['sha256'] != binding:
                raise ValueError('batch_id_rebound')
            return state
    if packet.get('author_qualified') is not True or not packet.get('provenance'):
        raise ValueError('explicit_author_qualification_required')
    if packet.get('origin') != 'EXTERNAL_GENERATION' or packet.get('parenting_or_l2_experience') is not False:
        raise ValueError('parenting_l2_experience_quarantined')
    if not packet.get('rows') or packet.get('rows_sha256') != digest(packet['rows']):
        raise ValueError('bound_nonempty_rows_required')
    rows = list(state['rows'])
    seen = {entry['target_sha256'] for entry in rows}
    duplicates = list(state['duplicates'])
    for index, entry in enumerate(packet['rows']):
        row = entry['row']
        if entry['encoding'] == 'math':
            target = row['target']
            if not (row.get('admitted') is True and row.get('semantic_status') == 'PASS'
                    and row.get('outcome_pass') is True and row.get('token_contract_pass') is True):
                raise ValueError('math_admission_required')
            if row['call']['raw'] != target or row['target_sha256'] != entry['target_sha256']:
                raise ValueError('raw_target_binding_drift')
            if row['task_id'] in held_math:
                raise ValueError('held_math_contamination')
            prefix = row['student_prefix']
            if not prefix or prefix[-1]['role'] != 'user' or any(message['role'] == 'system' for message in prefix):
                raise ValueError('neutral_math_prefix_required')
            for message in prefix:
                question = message['content']
                hashes = (hashlib.sha256(question.encode()).hexdigest(),
                          hashlib.sha256(' '.join(question.split()).encode()).hexdigest())
                if set(hashes) & set(held_question_hashes):
                    raise ValueError('held_question_contamination')
            review = row['review']
            if not (review.get('full_text_read') is True and review.get('status') == 'PASS'
                    and review.get('neutral_prefix_compatible') is True
                    and review.get('target_sha256') == entry['target_sha256']):
                raise ValueError('bound_individual_review_required')
            for field, value in (('student_prefix_sha256', prefix),):
                expected = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                if review.get(field) != expected:
                    raise ValueError('individual_review_source_binding_drift')
            if not re.fullmatch(r'[0-9a-f]{64}', review.get('raw_call_sha256', '')):
                raise ValueError('native_archive_call_binding_required')
        elif entry['encoding'] == 'rich_route':
            student = row['student']
            target = student['target']
            if not (row.get('admitted') is True and row.get('semantic_status') == 'PASS'
                    and student.get('parent_guidance_removed') is True):
                raise ValueError('rich_route_admission_required')
            if student['messages'][-1] != dict(role='assistant', content=target):
                raise ValueError('route_target_binding_drift')
        else:
            raise ValueError('new_batch_encoding_not_authorized')
        if hashlib.sha256(target.encode()).hexdigest() != entry['target_sha256']:
            raise ValueError('target_hash_drift')
        serialized = json.dumps(entry, ensure_ascii=False)
        if any(identity in serialized for identity in held_route):
            raise ValueError('held_route_contamination')
        if entry['target_sha256'] in seen:
            duplicates.append(dict(batch_id=batch_id, index=index, target_sha256=entry['target_sha256']))
        else:
            rows.append(entry)
            seen.add(entry['target_sha256'])
    return dict(state, version=state['version'] + 1, rows=rows, duplicates=duplicates,
                ingested=state['ingested'] + [dict(batch_id=batch_id, sha256=binding,
                    added=len(rows) - len(state['rows']), provenance=packet['provenance'])])


def commit_checkpoint(staging, destination, metadata):
    staging, destination = Path(staging), Path(destination)
    if destination.exists():
        raise ValueError('immutable_checkpoint_already_exists')
    required = ('optimizer.pt', 'rank0.pt', 'rank1.pt', 'adapter/adapter_config.json',
                'adapter/adapter_model.safetensors')
    if not all((staging / name).is_file() for name in required):
        raise ValueError('checkpoint_components_missing')
    files = {}
    for path in sorted(staging.rglob('*')):
        if path.is_symlink():
            raise ValueError('checkpoint_symlink_forbidden')
        if path.is_file():
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
            files[str(path.relative_to(staging))] = file_hash(path)
    manifest = dict(schema='COMBINED_CONTINUAL_CHECKPOINT_V1', metadata=metadata, files=files)
    atomic_json(staging / 'COMMIT.json', manifest)
    sync_directory(staging / 'adapter')
    sync_directory(staging)
    os.rename(staging, destination)
    sync_directory(destination.parent)
    return manifest


def verify_checkpoint(directory):
    directory = Path(directory)
    if directory.is_symlink() or '.pending' in directory.name:
        raise ValueError('uncommitted_checkpoint')
    manifest = json.loads((directory / 'COMMIT.json').read_text())
    if manifest['schema'] != 'COMBINED_CONTINUAL_CHECKPOINT_V1':
        raise ValueError('checkpoint_schema_drift')
    required = {'optimizer.pt', 'rank0.pt', 'rank1.pt', 'adapter/adapter_config.json',
                'adapter/adapter_model.safetensors'}
    if not required <= manifest['files'].keys():
        raise ValueError('checkpoint_components_missing')
    actual = {str(path.relative_to(directory)) for path in directory.rglob('*')
              if path.is_file() and path.name != 'COMMIT.json'}
    if actual != set(manifest['files']):
        raise ValueError('checkpoint_file_inventory_drift')
    for name, expected in manifest['files'].items():
        path = directory / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
            raise ValueError('unsafe_checkpoint_path')
        if file_hash(path) != expected:
            raise ValueError('checkpoint_hash_drift')
    return manifest


def pair_boundary(full, off):
    keys = ('update', 'corpus_sha256', 'corpus_version', 'exposure_counts', 'reference_tokens')
    if any(full[key] != off[key] for key in keys):
        raise ValueError('paired_checkpoint_exposure_drift')
    return full['update']
