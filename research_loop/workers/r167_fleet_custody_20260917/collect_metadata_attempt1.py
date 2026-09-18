import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time


FILE_CAP = 8 * 1024 * 1024
LIFE_CAP = 32 * 1024 * 1024
PROC_CAP = 4096
ENTRY_CAP = 16384
TAIL_CAP = 512
TAIL_COUNT = 256


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def identity(info):
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def regular(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('absolute_path_required')
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError('symlink_refused')
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('regular_file_required')
    return info


class Reader:
    def __init__(self):
        self.bytes = 0
        self.files = []

    def charge(self, count):
        if self.bytes + count > LIFE_CAP:
            raise ValueError('life_read_cap')
        self.bytes += count

    def read(self, path):
        before = regular(path)
        if before.st_size > FILE_CAP:
            raise ValueError('file_read_cap:size=' + str(before.st_size))
        self.charge(before.st_size)
        with open(path, 'rb') as stream:
            raw = stream.read(before.st_size)
            if identity(os.fstat(stream.fileno())) != identity(before):
                raise ValueError('file_changed')
        if identity(regular(path)) != identity(before) or len(raw) != before.st_size:
            raise ValueError('file_changed')
        self.files.append(dict(path=str(path), sha256=digest(raw), bytes=len(raw), stat=identity(before)))
        return raw

    def document(self, path):
        return json.loads(self.read(path))

    def envelope(self, path):
        before = regular(path)
        suffix = b''
        with open(path, 'rb') as stream:
            for offset in range(1, min(TAIL_CAP, before.st_size) + 1):
                self.charge(1)
                stream.seek(-offset, 2)
                suffix = stream.read(1) + suffix
                if suffix.startswith(b',"index":'):
                    break
            else:
                raise ValueError('envelope_suffix_not_found_within_cap')
            if identity(os.fstat(stream.fileno())) != identity(before):
                raise ValueError('envelope_changed')
        if identity(regular(path)) != identity(before):
            raise ValueError('envelope_changed')
        value = json.loads(b'{' + suffix[1:])
        if set(value) != {'index', 'journal_id', 'kind', 'previous_sha256', 'schema', 'sha256'}:
            raise ValueError('unexpected_envelope_keys')
        if value['index'] != int(Path(path).stem) or value['schema'] != 'R125_STREAM_JOURNAL_V1':
            raise ValueError('unexpected_envelope_identity')
        return dict(path=str(path), file_bytes=before.st_size, suffix_bytes=len(suffix),
                    suffix_sha256=digest(suffix), envelope=value,
                    declared_record_digest_not_recomputed=True)


def proc_bytes(path, cap):
    with open(path, 'rb') as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise ValueError('proc_read_cap')
    return raw


def process(pid):
    raw = proc_bytes('/proc/' + str(pid) + '/stat', 4096)
    fields = raw.rsplit(b')', 1)[1].split()
    arguments = proc_bytes('/proc/' + str(pid) + '/cmdline', 4096).decode().strip('\0').split('\0')
    return dict(pid=pid, start_ticks=fields[19].decode(), state=fields[0].decode(),
                parent_pid=int(fields[1]), cwd=os.readlink('/proc/' + str(pid) + '/cwd'),
                arguments=arguments)


def candidate_processes():
    candidates = []
    scanned = 0
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit():
            continue
        scanned += 1
        if scanned > PROC_CAP:
            raise ValueError('proc_census_cap')
        try:
            comm = proc_bytes(entry.path + '/comm', 256)
            if b'python' not in comm.lower():
                continue
            item = process(int(entry.name))
            arguments = item['arguments']
            if 'gpu.orch_r125_continual_guard' in arguments and 'native' in arguments:
                candidates.append(item)
            elif 'gpu.orch_r125_continual_native' in arguments:
                candidates.append(item)
        except (OSError, ValueError, UnicodeError):
            continue
    return candidates, scanned


def names(directory):
    path = Path(directory)
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError('directory_symlink_refused')
    result = []
    for entry in os.scandir(path):
        if len(result) >= ENTRY_CAP:
            raise ValueError('directory_entry_cap')
        result.append(entry.name)
    return result


def collect(row, candidates, boot):
    reader = Reader()
    output = dict(life_id=row['life_id'], source_root=row['storage_root'],
                  process_plan_root=row['process_plan_root'], observed_start_unix=time.time(),
                  inventory_identity=row['inventory_identity'], findings={}, missing_reasons=[])

    def attempt(label, action):
        try:
            output['findings'][label] = action()
        except Exception as error:
            output['missing_reasons'].append(label + ':' + type(error).__name__ + ':' + str(error))

    birth = {}

    def birth_read():
        raw = reader.read(row['birth_plan']['path'])
        birth.update(json.loads(raw))
        return dict(path=row['birth_plan']['path'], sha256=digest(raw),
                    registry_sha256_matches=digest(raw) == row['birth_plan']['sha256'],
                    plan_root=birth.get('root'), source_root=birth.get('source_root'),
                    plan_root_matches=birth.get('root') == row['process_plan_root'],
                    birth_context_present=isinstance(birth.get('context'), dict),
                    historical_registry_plan_not_independently_proven_original_birth=True)

    attempt('birth_plan', birth_read)

    def native_read():
        matches = []
        needles = {'continual_run1': ['run1'], 'pilot': ['pilot'], 'repo_reader': ['repo_reader']}.get(
            row['life_id'], [row['life_id']])
        for candidate in candidates:
            arguments = candidate['arguments']
            option = '--config' if '--config' in arguments else '--plan'
            if option not in arguments:
                continue
            path = arguments[arguments.index(option) + 1]
            if 'C5' in path or not any(needle in path for needle in needles):
                continue
            config = reader.document(path) if option == '--config' else None
            plan_path = config['plan_path'] if config else path
            raw = reader.read(plan_path)
            plan = json.loads(raw)
            if plan.get('root') not in {row['storage_root'], row['process_plan_root']}:
                continue
            before = process(candidate['pid'])
            if before['start_ticks'] != candidate['start_ticks']:
                raise ValueError('pid_reused')
            source = Path(plan['source_root'])
            checked = []
            if config:
                if digest(raw) != config['plan_sha256']:
                    raise ValueError('current_plan_hash_mismatch')
                pins = config['source_pins']
                if len(pins) > 1024:
                    raise ValueError('source_file_count_cap')
                for relative, expected in sorted(pins.items()):
                    relative_path = Path(relative)
                    if relative_path.is_absolute() or '..' in relative_path.parts or relative_path.suffix != '.py':
                        raise ValueError('non_python_source_pin_refused')
                    actual = digest(reader.read(source / relative_path))
                    checked.append(dict(path=relative, sha256=actual, expected_sha256=expected, matches=actual == expected))
            after = process(candidate['pid'])
            if before != after:
                raise ValueError('process_changed_during_source_read')
            matches.append(dict(native_identity=dict(pid=before['pid'], start_ticks=before['start_ticks'], boot_id=boot),
                state=before['state'], parent_pid=before['parent_pid'], cwd=before['cwd'],
                entry_module=arguments[arguments.index('-m') + 1], config_path=path if config else None,
                plan_path=plan_path, plan_sha256=digest(raw), plan_root=plan['root'],
                storage_root_matches=plan['root'] == row['storage_root'], source_root=str(source),
                source_files=checked, all_declared_source_pins_match=bool(checked) and all(item['matches'] for item in checked),
                in_memory_source_not_attested=True,
                inventory_pid_start_match=before['pid'] == row['inventory_identity']['pid'] and before['start_ticks'] == row['inventory_identity']['start_ticks']))
        if len(matches) != 1:
            raise ValueError('exact_current_native_match_count=' + str(len(matches)))
        return matches[0]

    attempt('current_native', native_read)
    root = Path(row['storage_root'])

    def checkpoint(directory):
        commit_path = directory / 'COMMIT.json'
        raw = reader.read(commit_path)
        commit = json.loads(raw)
        files = []
        for filename in ['adapter_config.json', 'adapter_model.safetensors']:
            path = directory / 'adapter' / filename
            try:
                info = regular(path)
                files.append(dict(path=str(path), present=True, bytes=info.st_size, payload_read=False))
            except OSError:
                files.append(dict(path=str(path), present=False, payload_read=False))
        return dict(path=str(commit_path), sha256=digest(raw), schema=commit.get('schema'),
                    optimizer_steps=commit.get('optimizer_steps'), adapter_path=commit.get('adapter_path'),
                    adapter_path_matches=commit.get('adapter_path') == str(directory / 'adapter'),
                    checkpoint_sha256=commit.get('checkpoint_sha256'),
                    adapter_declared_files=commit.get('adapter_files'), files=files,
                    tensor_optimizer_rng_payloads_read=False)

    attempt('initial_checkpoint', lambda: checkpoint(root / 'checkpoints' / 'initial'))

    def frontier():
        header = reader.document(root / 'stream' / 'JOURNAL.json')
        record_names = names(root / 'stream' / 'records')
        indices = sorted(int(name[:-5]) for name in record_names if re.fullmatch(r'\d{20}\.json', name))
        selected = None
        tail = []
        for index in reversed(indices[-TAIL_COUNT:]):
            envelope = reader.envelope(root / 'stream' / 'records' / f'{index:020d}.json')
            value = envelope['envelope']
            if value['journal_id'] != header['journal_id']:
                raise ValueError('journal_id_mismatch')
            tail.append(envelope)
            if value['kind'] == 'SLEEP_COMPLETE':
                intent = reader.document(root / 'stream' / 'records' / f'{index:020d}.intent.json')
                expected = {key: value[key] for key in ['schema', 'journal_id', 'index', 'previous_sha256']}
                expected['record_sha256'] = value['sha256']
                if intent != expected:
                    raise ValueError('sleep_complete_intent_mismatch')
                selected = envelope
                break
        directories = names(root / 'checkpoints')
        sleeps = sorted(name for name in directories if re.fullmatch(r'sleep_\d{6}', name))
        latest = checkpoint(root / 'checkpoints' / sleeps[-1]) if sleeps else None
        return dict(journal_header=header, record_count=len(indices),
                    indices_contiguous=indices == list(range(len(indices))),
                    highest_record=indices[-1] if indices else None,
                    observed_sleep_complete=selected, tail_envelopes=tail,
                    latest_sleep_directory=sleeps[-1] if sleeps else None, latest_commit=latest,
                    checkpoint_and_sleep_record_causal_binding_verified=False,
                    full_journal_and_resume_state_not_read=True)

    attempt('frontier_metadata', frontier)
    output['missing_reasons'].extend([
        'Full TRAIN journal/resume-state and original birth-context linkage not acquired: raw response/loss payloads excluded.',
        'Latest COMMIT directory is not itself a verified completed frontier; SLEEP_COMPLETE declared digest is not a recomputed payload digest.',
        'Source-owner authority and exact queue registration remain separate; no verified registration_observation emitted.'])
    output.update(status='METADATA_ONLY_PARTIAL_CUSTODY_NOT_QUEUE_ADMISSION',
                  observed_end_unix=time.time(), metadata_bytes_read=reader.bytes, file_receipts=reader.files)
    return output


if __name__ == '__main__':
    spec = json.loads(base64.b64decode(sys.argv[1]))
    if [row['life_id'] for row in spec['lives']] != ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader']:
        raise ValueError('exact_seven_life_scope')
    boot = proc_bytes('/proc/sys/kernel/random/boot_id', 128).decode().strip()
    candidates, scanned = candidate_processes()
    for row in spec['lives']:
        result = collect(row, candidates, boot)
        result.update(schema='R167_FLEET_METADATA_CUSTODY_V1', collector_sha256=spec['collector_sha256'],
                      batch_plan_sha256=spec['batch_plan_sha256'], proc_entries_scanned=scanned,
                      caps=dict(file_bytes=FILE_CAP, life_bytes=LIFE_CAP, directory_entries=ENTRY_CAP,
                                proc_entries=PROC_CAP, envelope_bytes=TAIL_CAP, envelope_count=TAIL_COUNT),
                      gpu_calls=0, remote_writes=0, signals=0, held_or_readout_files_opened=0)
        print(json.dumps(result, sort_keys=True), flush=True)
