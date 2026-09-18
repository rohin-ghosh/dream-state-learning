"""Bounded TRAIN metadata census. No imports of learner code or remote writes."""

import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import sys
import time


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def safe_open(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_regular_path')
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            next_descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
    finally:
        os.close(descriptor)


class Reader:
    def __init__(self):
        self.metadata_bytes = 0
        self.journal_bytes = 0
        self.record_count = 0

    def raw(self, path, record=False):
        with os.fdopen(safe_open(path), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'regular_file')
            maximum = 32 * 1024 * 1024 if record else 1024 * 1024
            require(before.st_size <= maximum, 'per_file_cap')
            if record:
                require(self.record_count < 256 and self.journal_bytes + before.st_size <= 64 * 1024 * 1024,
                    'TRAIN_read_cap')
                self.record_count += 1
                self.journal_bytes += before.st_size
            else:
                require(self.metadata_bytes + before.st_size <= 32 * 1024 * 1024, 'metadata_cap')
                self.metadata_bytes += before.st_size
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
            require(len(raw) == before.st_size and (before.st_ino, before.st_size, before.st_mtime_ns)
                == (after.st_ino, after.st_size, after.st_mtime_ns), 'stable_bounded_bytes')
            return raw

    def document(self, path, record=False):
        raw = self.raw(path, record)
        return json.loads(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def identity(pid):
    root = Path('/proc') / str(pid)
    before = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    raw = (root / 'cmdline').read_bytes()
    require(len(raw) <= 65536, 'bounded_argv')
    after = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and after[0] not in ('Z', 'X'), 'stable_live_identity')
    argv = raw.rstrip(b'\0').decode().split('\0')
    require(Path(argv[0]).name.startswith('python') and 'native' in argv
        and any(argument in ('gpu.orch_r125_continual_guard', 'gpu.orch_r158_matched_node4')
            for argument in argv), 'exact_native_not_supervisor')
    return dict(pid=pid, start_ticks=after[19], state=after[0], argv_sha256=hashlib.sha256(raw).hexdigest(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), uid=root.stat().st_uid,
        cwd=os.readlink(root / 'cwd')), argv


def names(directory):
    result = []
    with os.scandir(directory) as entries:
        for entry in entries:
            require(len(result) < 20000, 'directory_entry_cap')
            result.append(entry.name)
    return sorted(result)


def record(reader, root, index, manifest):
    directory = root / 'stream/records'
    document, reference = reader.document(directory / f'{index:020d}.json', record=True)
    intent, intent_reference = reader.document(directory / f'{index:020d}.intent.json')
    payload = {key: value for key, value in document.items() if key != 'sha256'}
    require(document['index'] == index and document['schema'] == manifest['schema']
        and document['journal_id'] == manifest['journal_id'] and document['sha256'] == digest(payload),
        'record_content_binding')
    require(intent == dict(schema=document['schema'], journal_id=document['journal_id'], index=index,
        previous_sha256=document['previous_sha256'], record_sha256=document['sha256']), 'record_intent_binding')
    return document, dict(record=reference, intent=intent_reference, index=index, kind=document['kind'],
        chain_sha256=document['sha256'], previous_sha256=document['previous_sha256'])


def checkpoint(reader, path):
    document, reference = reader.document(path)
    projection = {key: document[key] for key in ('schema', 'base_sha256', 'created_unix',
        'optimizer_steps', 'adapter_path', 'optimizer_rng_path', 'checkpoint_sha256',
        'adapter_state_sha256') if key in document}
    projection.update(reference=reference, adapter_files=document.get('adapter_files'),
        experiment_digest=digest(document.get('experiment')))
    presence = {}
    for filename in ('adapter/adapter_model.safetensors', 'adapter/adapter_config.json', 'optimizer_rng.pt'):
        candidate = Path(path).parent / filename
        try:
            info = candidate.lstat()
            presence[filename] = dict(regular=stat.S_ISREG(info.st_mode), bytes=info.st_size)
        except FileNotFoundError:
            presence[filename] = dict(present=False)
    projection['presence_only'] = presence
    return document, projection


def observe_life(life):
    reader = Reader()
    result = dict(life_id=life['life_id'], node=life['node'], source_root=life['storage_root'],
        status='INCOMPLETE_CUSTODY', observed_unix=time.time())
    try:
        root = Path(life['storage_root'])
        current, argv = identity(life['inventory_identity']['pid'])
        result['native_identity'] = current
        result['historical_start_ticks_equal'] = current['start_ticks'] == str(life['inventory_identity']['start_ticks'])
        require(root == Path(life['process_plan_root']), 'registered_alias_requires_separate_witness')
        config_paths = [Path(argument) for argument in argv if argument.startswith('/localhome/local-rohing/')
            and argument.endswith('.json')]
        require(0 < len(config_paths) <= 4, 'bounded_native_configs')
        plans, configs = [], []
        source_candidates = {current['cwd']}
        for path in config_paths:
            config, reference = reader.document(path)
            configs.append(dict(reference=reference, keys=sorted(config), source_fields={key: value
                for key, value in config.items() if key in ('source_root', 'native_source', 'native_source_path',
                    'source_path', 'source_dir', 'source_manifest', 'source_manifest_path')}))
            for key in ('source_root', 'source_dir'):
                if isinstance(config.get(key), str):
                    source_candidates.add(config[key])
            if config.get('root') == str(root):
                plans.append((config, reference))
            if config.get('plan_path'):
                plan, plan_ref = reader.document(config['plan_path'])
                require(plan_ref['sha256'] == config['plan_sha256'], 'current_plan_pin')
                if plan.get('root') == str(root):
                    plans.append((plan, plan_ref))
        require(plans, 'native_exact_registered_root')
        result['native_configurations'] = configs
        result['current_plans'] = [reference for plan, reference in plans]
        registry_plan, registry_ref = reader.document(life['birth_plan']['path'])
        require(registry_ref['sha256'] == life['birth_plan']['sha256'], 'registered_plan_unchanged')
        result['registry_birth_plan'] = registry_ref
        manifest, manifest_ref = reader.document(root / 'stream/JOURNAL.json')
        result['journal'] = manifest_ref
        initial_record, initial_ref = record(reader, root, 0, manifest)
        require(initial_record['previous_sha256'] == digest(manifest)
            and initial_record['kind'] == 'COMMITTED' and initial_record['document'].get('kind') == 'BIRTH',
            'original_BIRTH_record')
        result['initial_record'] = initial_ref
        initial_state = initial_record['document']['state']
        require(initial_state['sha256'] == digest(initial_state['state']), 'initial_state_binding')
        birth_history = initial_state['state']['history']
        context = {key: birth_history[key] for key in ('system_prompt', 'birth_prompt')}
        result['birth_context_digest'] = digest(context)
        original_candidates = [root.parent / 'control1/PLAN.json', root.parent / 'control/PLAN.json',
            root.parent / 'PLAN.json', root / 'PLAN.json']
        originals = []
        for path in original_candidates:
            if path.is_file():
                plan, reference = reader.document(path)
                originals.append(dict(reference=reference, root_matches=plan.get('root') == str(root),
                    birth_context_matches=all(plan.get(key) == value for key, value in context.items())))
        result['original_plan_candidates'] = originals
        result['registry_plan_birth_context_matches'] = all(registry_plan.get(key) == value for key, value in context.items())
        try:
            initial_commit, initial_projection = checkpoint(reader, root / 'checkpoints/initial/COMMIT.json')
            require(digest(initial_commit['checkpoint_sha256']) == initial_state['state']['model_state_sha256']
                and initial_commit['optimizer_steps'] == 0, 'initial_COMMIT_BIRTH_binding')
            result['initial_commit'] = initial_projection
        except FileNotFoundError:
            result['initial_commit'] = dict(present=False)
        entries = names(root / 'stream/records')
        indices = [int(name[:-5]) for name in entries if re.fullmatch(r'\d{20}\.json', name)]
        require(indices, 'TRAIN_records_present')
        tail = max(indices)
        result['tail_index_at_listing'] = tail
        next_previous = None
        last = None
        for index in range(tail, max(-1, tail - 254), -1):
            if index == 0:
                break
            current_record, reference = record(reader, root, index, manifest)
            if next_previous is not None:
                require(current_record['sha256'] == next_previous, 'contiguous_reverse_TRAIN_suffix')
            next_previous = current_record['previous_sha256']
            if index == tail:
                result['tail'] = reference
            if current_record['kind'] == 'SLEEP_COMPLETE':
                body = current_record['document']
                state = body['resume_state']
                require(state['sha256'] == digest(state['state']), 'completed_resume_state')
                cycle = body['cycle']
                commit, projection = checkpoint(reader, root / 'checkpoints' / f'sleep_{cycle:06d}/COMMIT.json')
                require(body['status'] == 'COMPLETE' and body['checkpoint'] == commit
                    and state['state']['model_state_sha256'] == digest(commit['checkpoint_sha256']),
                    'actual_completed_COMMIT_not_orphan')
                require(len(state['state']['sleep_receipts']) == cycle
                    and state['state']['sleep_frontier'] == len(state['state']['rows']), 'completed_sleep_frontier')
                result['completed_boundary'] = dict(cycle=cycle, record=reference, checkpoint=projection,
                    resume_state_sha256=state['sha256'], sleep_frontier=state['state']['sleep_frontier'],
                    rows=len(state['state']['rows']), generations=len(state['state']['rows']))
                last = cycle
                break
        result['last_completed_sleep'] = last
        result['source_candidates'] = sorted(source_candidates)
        source_pins = []
        for source in sorted(source_candidates):
            if not source.startswith('/localhome/local-rohing/'):
                continue
            path = Path(source) / 'gpu/orch_r125_continual_native.py'
            if path.is_file():
                raw = reader.raw(path)
                source_pins.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
        result['native_source_pins'] = source_pins
        after, unused = identity(current['pid'])
        require(all(current[key] == after[key] for key in ('pid', 'start_ticks', 'argv_sha256', 'boot_id', 'cwd')),
            'native_identity_unchanged_during_read')
        result['identity_rechecked'] = True
        result['status'] = 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED' if last is not None else 'FRONTIER_OUTSIDE_READ_CAP'
        result['observed_unix'] = time.time()
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, reason=str(error))
    result['reads'] = dict(metadata_bytes=reader.metadata_bytes, journal_bytes=reader.journal_bytes,
        record_count=reader.record_count)
    return result


if __name__ == '__main__':
    request = json.loads(sys.argv[1])
    require(1 <= len(request['lives']) <= 6, 'bounded_registered_node_scope')
    require(all(life['node'] == request['node'] and life['node'] in ('ovx2', 'a100', 'a40r')
        for life in request['lives']), 'no_node5_or_unregistered_read')
    print(json.dumps(dict(hostname=socket.gethostname(), node=request['node'], observed_unix=time.time(),
        lives=[observe_life(life) for life in request['lives']], no_signals=True, no_writes=True), sort_keys=True))
