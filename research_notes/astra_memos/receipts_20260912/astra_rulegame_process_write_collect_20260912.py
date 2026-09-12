"""Main-only process-v2 metadata custody; no tokenizer/model/fit, kills or retries."""
from __future__ import annotations


import argparse
import array


import datetime as dt


import hashlib


import importlib.util


import io


import json


import math


import os


from pathlib import Path, PurePosixPath


import re


import signal


import stat
import struct


import sys


import tarfile


import time


import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
DRIVER = Path('/tmp/astra_rulegame_process_write_20260912.py')
DRIVER_SHA = 'a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9'
LAUNCHER = Path('/tmp/astra_launch_rulegame_process_write_20260912.py')
LAUNCHER_SHA = 'b4e2ee193f4ba7cc9138c0652498e3318cb4e685c12a9fbe2f5cf9442b05fee6'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
PLAN_SHA = '67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44'
SOURCE_ID = '4c3064c1c3eef068951e9c3b2ca46630754564e7'
ROOT_NAME = 'astra_rulegame_process_write_v2_20260912_attempt1'
PROTOCOL = 'rulegame_grounded_process_pair_v2'
WRITE_PROTOCOL = 'rulegame_process_write_v2_20260912'
ORIGIN = 'UNRESOLVED_LOCAL_HASHES_ONLY'
CONDITIONING = 'CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT'
ARMS, DEVICE = ('P', 'A'), '2'
EXPECTED_TOKENS = {'P': {'total': 760, 'target': 32}, 'A': {'total': 758, 'target': 31}}
MAX_FILE, MAX_TOTAL, MAX_FILES = 32*1024*1024, 256*1024*1024, 2048
MAX_WEIGHTS = 256*1024*1024
SECRET_KEYS = {'password', 'passwd', 'secret', 'api_key', 'access_token', 'refresh_token',
               'authorization', 'private_key', 'hf_token', 'aws_secret_access_key', 'client_secret'}


def allowed_paths():
    names = {'plan.json', 'plan.sha256.json', 'material/manifest.json', 'material/export_manifest.json',
        'material/provenance/pair.json', 'material/audit/candidate.json', 'material/audit/main_review.json',
        'material/audit/token_receipts.json', 'run/controller.json', 'run/result.json', 'run/failure.json'}
    excluded = {'material/audit/candidate.json', 'material/audit/main_review.json', 'material/audit/token_receipts.json'}
    weights = set()
    for arm in ARMS:
        names.update({f'material/corpora/{arm}.json', f'material/provenance/{arm}.tokens.json', f'run/{arm}.launch.json'})
        excluded.update({f'material/corpora/{arm}.json', f'material/provenance/{arm}.tokens.json', f'fits/{arm}/full_tokens.json'})
        names.update(f'run/{arm}/{name}' for name in ('process.json', 'supervision.json', 'stdout.log'))
        names.update(f'fits/{arm}/{name}' for name in ('attempt.json', 'full_tokens.json', 'pre_update_trainability.json',
            'post_update_trainability.json', 'receipt.json', 'manifest.json'))
        names.update(f'fits/{arm}/forwards/{index:04d}.json' for index in range(1, 13))
        names.update(f'fits/{arm}/adapter/{name}' for name in ('DONE', 'adapter_config.json', 'README.md',
            'train_manifest.json', 'train_meta.json', 'adapter_model.safetensors'))
        weights.add(f'fits/{arm}/adapter/adapter_model.safetensors')
    return names, excluded, weights


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unaliased(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'symlink path rejected')
    return path


def payload(path, limit=MAX_FILE):
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
                'special/hardlinked/oversized file rejected')
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')
        require(len(data) == before.st_size and all(getattr(before, key) == getattr(after, key)
                == getattr(path.stat(), key) for key in fields), 'file changed during read')
    return data


def digest(path):
    return hashlib.sha256(payload(path)).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def read(path):
    def reject(value):
        raise ValueError('nonfinite JSON rejected')
    return json.loads(payload(path), object_pairs_hook=unique, parse_constant=reject)


def write_new(path, data):
    descriptor = os.open(unaliased(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    write_new(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def load(path, pin, name):
    data = payload(path)
    require(hashlib.sha256(data).hexdigest() == pin, 'dependency hash differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def utc(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timezone required')
    return parsed.timestamp()


def scan_text(data, name):
    text = data.decode('utf-8')
    lower = PurePosixPath(name).name.lower()
    require(not any(word in lower for word in ('secret', 'credential', '.env', 'private_key')),
            'credential filename rejected')
    require(not re.search(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:hf_|sk-)[A-Za-z0-9_-]{20,}|'
                          r'(?i:authorization\s*[:=]\s*[\"\x27]?bearer\s+\S+)', text), 'credential payload rejected')
    if name.endswith('.json'):
        def inspect(pairs):
            for key, value in pairs:
                require(key.lower() not in SECRET_KEYS, 'credential JSON field rejected')
            return unique(pairs)
        json.loads(text, object_pairs_hook=inspect)
    require(not re.search(r'(?im)^\s*(?:export\s+)?(?:HF_TOKEN|API_KEY|PASSWORD|AWS_SECRET_ACCESS_KEY)\s*=', text),
            'credential assignment rejected')
    require(not re.search(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|https?://[^\s/:]+:[^\s/@]+@|'
        r'(?i:(?:password|passwd|api[_-]?key|client_secret|access_token|refresh_token)\s*[:=]\s*["\x27]?\S+)', text),
        'credential value rejected')
    if name.endswith('.json'):
        json.loads(text, object_pairs_hook=unique, parse_constant=lambda value: require(False, 'nonfinite metadata JSON'))


def inventory(root, logs):
    allowed, raw, weights = allowed_paths()
    files, hashes, excluded = {}, {}, {}
    count, total = 0, 0
    for base, prefix, permitted in ((root, 'metadata/run', allowed),
            (logs, 'metadata/launch', {'launch.json', 'gpu.xml', 'controller.log'})):
        directories = {str(parent) for name in permitted for parent in PurePosixPath(name).parents if str(parent) != '.'}
        def inaccessible(error):
            raise error
        for directory, children, names in os.walk(base, followlinks=False, onerror=inaccessible):
            for name in children + names:
                count += 1
                require(count <= MAX_FILES, 'filesystem entry limit')
                path = unaliased(Path(directory) / name)
                relative = path.relative_to(base).as_posix()
                require(path.is_dir() or path.is_file(), 'special filesystem entry rejected')
                if path.is_dir():
                    require(relative in directories, 'unknown metadata directory: ' + relative)
                    continue
                require(relative in permitted, 'unknown metadata file: ' + relative)
                member = prefix + '/' + relative
                if base == root and relative in weights:
                    require(path.stat().st_size <= MAX_WEIGHTS, 'weight byte limit')
                    excluded[member] = dict(sha256=file_hash(path), reason='weight_bytes_native_only')
                    continue
                data = payload(path)
                scan_text(data, member)
                total += len(data)
                require(total <= MAX_TOTAL, 'metadata total byte limit')
                checksum = hashlib.sha256(data).hexdigest()
                if base == root and relative in raw:
                    excluded[member] = dict(sha256=checksum, reason='raw_or_token_material_native_only')
                else:
                    files[member], hashes[member] = path, checksum
    require(files, 'empty metadata inventory')
    return files, hashes, excluded


def process_snapshot():
    rows = []
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
        except FileNotFoundError:
            continue
        rows.append(dict(pid=int(path.parent.name), ppid=int(fields[1]), pgid=int(fields[2]), session=int(fields[3])))
    return rows


def status(root, plan_sha256, launch_root, launch_sha256):
    root, logs = unaliased(root), unaliased(launch_root)
    require(plan_sha256 == PLAN_SHA and root.name == ROOT_NAME, 'wrong Main process-write plan/root')
    require(root.is_dir() and logs.is_dir() and logs == root.with_name(root.name+'_launch'), 'exact sibling launcher root required')
    require(digest(logs / 'launch.json') == launch_sha256, 'launch hash differs')
    launch = read(logs / 'launch.json')
    require(launch['root'] == str(root) and launch['plan_sha256'] == plan_sha256 and launch['driver_sha256'] == DRIVER_SHA
        and type(launch['pid']) is int and launch['pid'] > 1 and utc(launch['started_utc']) <= time.time(), 'launch identity differs')
    owned = {launch['pid']}
    expected = {root / 'run' / arm / 'process.json' for arm in ARMS}
    require(set(root.glob('**/process.json')) <= expected, 'unexpected process receipt')
    for path in expected:
        if unaliased(path).exists():
            process = read(path)
            require(type(process['pid']) is int and process['pid'] > 1 and process['pgid'] == process['pid']
                and process['pid'] not in owned, 'distinct owned worker/session leader required')
            owned.add(process['pid'])
    observed = process_snapshot()
    descendants = set(owned)
    while True:
        extended = descendants | {row['pid'] for row in observed if row.get('ppid') in descendants}
        if extended == descendants:
            break
        descendants = extended
    live = [row for row in observed if row['pid'] in descendants or any(row[key] in owned for key in ('pgid', 'session'))]
    markers = {name: unaliased(root / 'run' / name).is_file() for name in ('result.json', 'failure.json')}
    return dict(ready=not live and sum(markers.values()) == 1, owned_ids=sorted(owned), live_owned=live,
        markers=markers, launch=launch, terminal_bodies_read=False, model_loaded=False, vacancy_queried=False)


def check_uuid(gpu, xml, expected):
    devices = ET.fromstring(xml).findall('gpu')
    require(len(devices) == 1 and devices[0].findtext('uuid') == gpu['gpu_uuid'] == expected, 'GPU UUID differs')
    processes = devices[0].find('processes')
    require(processes is not None and not list(processes) and not (processes.text or '').strip(), 'GPU not vacant')


def bind(root, plan_sha256, logs, launch):
    require(digest(root / 'plan.json') == read(root / 'plan.sha256.json')['sha256'] == plan_sha256 == PLAN_SHA, 'plan seal differs')
    bridge = load(DRIVER, DRIVER_SHA, 'process_write_collection_frozen_driver')
    checked, plan, diagnostic, exporter, trainer = bridge.checked_plan(root, plan_sha256)
    require(checked == root and plan['schema'] == 2 and plan['protocol'] == WRITE_PROTOCOL and plan['material_protocol'] == PROTOCOL
        and Path(plan['source_root']).name == SOURCE_ID and plan['device'] == DEVICE
        and plan['python'] == os.path.abspath(sys.executable), 'new native process plan/schema/source/device differs')
    require(all({key: plan['tokens'][arm]['tokens'][key] for key in expected} == expected
        for arm, expected in EXPECTED_TOKENS.items()), 'actual native input/target counts differ: P760/32 A758/31')
    require(digest(LAUNCHER) == launch['launcher_sha256'] == LAUNCHER_SHA, 'Main launcher source differs')
    expected = dict(node=3, device=DEVICE, phase='process_v2_context_distillation_write', source=plan['source_root'],
        root=str(root), plan_sha256=plan_sha256, driver_sha256=DRIVER_SHA, continuous_reservation=True,
        controller_seconds=1200, cleanup_reserve=140, worker_cap_seconds=600, external_collection_margin_seconds=300,
        arms=list(ARMS), seed=2, fresh_base=True, updates_per_arm=12, model_origin=ORIGIN, adaptation_test=False)
    require(all(launch.get(key) == value for key, value in expected.items()), 'Main launcher protocol/recipe differs')
    require(launch['command'] == [plan['python'], '-B', str(DRIVER), 'write', '--root', str(root),
        '--plan-sha256', plan_sha256, '--allow-gpu'], 'Main launcher command differs')
    require(re.fullmatch('[0-9a-f]{64}', launch['native_cpu_sha256']), 'native CPU-test hash missing')
    check_uuid(launch['gpu'], payload(logs / 'gpu.xml'), launch['gpu']['gpu_uuid'])
    return bridge, plan, diagnostic, exporter, trainer


def material_audit(root, plan, bridge, diagnostic, exporter):
    material = root / 'material'
    candidate = read(material / 'audit/candidate.json')
    review = read(material / 'audit/main_review.json')
    audit = read(material / 'audit/token_receipts.json')
    tokens = {arm: read(material / 'provenance' / (arm+'.tokens.json')) for arm in ARMS}
    corpora = {arm: read(material / 'corpora' / (arm+'.json')) for arm in ARMS}
    require(candidate == read(plan['fixed_candidate_path']) and review == read(plan['main_review_path']), 'source candidate/Main review join differs')
    require(candidate['candidate_sha256'] == plan['candidate_sha256'] and candidate['protocol'] == PROTOCOL
        and candidate['status'] == 'AVAILABLE_PENDING_MAIN_REVIEW', 'available explicit V2 candidate required')
    capture = Path(plan['formation_root']) / 'formation/data'
    require(exporter.inspect_capture(capture, protocol=exporter.PROTOCOL_V2) == candidate, 'fixed slots/source replay/teacher exclusion changed')
    exporter._review(candidate, review, protocol=exporter.PROTOCOL_V2)
    pair = dict(protocol=PROTOCOL, status='PAIRED_CPU_TOKEN_AUDITED_MAIN_REVIEWED', corpora=corpora,
        audit=dict(audit, candidate=candidate, main_review=review))
    bridge.check_pair(pair, candidate, review, tokens, diagnostic)
    teacher_spans = exporter.records._payload_spans([row['raw_text'] for row in candidate['teacher_sources_audit_only']], 'interaction_v3')
    rows = {}
    for arm in ARMS:
        require({key: value for key, value in tokens[arm].items() if key not in ('rows', 'batch')} == plan['tokens'][arm], 'plan/exposure receipt differs')
        rows[arm] = []
        for index, (item, row) in enumerate(zip(corpora[arm]['corpus'], tokens[arm]['rows'], strict=True)):
            require(len(item['spans']) == 2 and item['spans'][0][1:] == [False, 'parent_removed_wake_context']
                and item['spans'][1][1:] == [True, 'complete_own_raw_wake'], 'teacher or restatement training span forbidden')
            for span in item['spans']:
                exporter.records._check_payload(span[0], teacher_spans, 'collector teacher exclusion')
            require(0 < row['context_tokens'] < row['input_tokens'] <= 4096
                and len(row['input_ids']) == len(row['labels']) == row['input_tokens']
                and row['labels'][:row['context_tokens']] == [-100]*row['context_tokens']
                and row['labels'][row['context_tokens']:] == row['input_ids'][row['context_tokens']:]
                and row['target_tokens'] == row['raw_target_tokens']+1
                and row['input_tokens'] == row['context_tokens']+row['target_tokens'], 'sealed causal mask/EOS exposure differs')
            transformed = audit['receipts'][arm][index]['transformed_training']
            eos = transformed['target_with_eos'][-1]
            require(type(eos) is int and eos >= 0 and eos not in transformed['raw_target_token_ids']
                and len(transformed['raw_target_token_ids']) == row['raw_target_tokens'], 'exactly one target EOS required')
            rows[arm].append(dict(slot_id=item['meta']['slot_id'], source_call_id=item['meta']['source_call_id'],
                context_sha256=hashlib.sha256(item['spans'][0][0].encode()).hexdigest(),
                raw_target_sha256=hashlib.sha256(item['spans'][1][0].encode()).hexdigest(),
                input_tokens=row['input_tokens'], target_tokens=row['target_tokens'], raw_target_tokens=row['raw_target_tokens']))
        for index in range(12):
            bridge.forward_receipt(bridge.expected_forward_batch(tokens[arm], [0, 1]), tokens[arm], index)
    return dict(protocol=PROTOCOL, candidate_sha256=candidate['candidate_sha256'], main_review_sha256=plan['main_review_sha256'],
        rows=rows, native_tokenizer_reloaded=False, original_native_and_transformed_separate=True,
        conditioning=CONDITIONING, lexical_teacher_exclusion=True, semantic_certification=False,
        counts=EXPECTED_TOKENS, claims=bridge.CLAIMS)


def finite_weights(path, expected_sha):
    descriptor = os.open(unaliased(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    checksum, reports = hashlib.sha256(), []
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 8 < before.st_size <= MAX_WEIGHTS, 'unsafe weight file')
        first = stream.read(8)
        header_size = struct.unpack('<Q', first)[0]
        require(0 < header_size <= min(16*1024*1024, before.st_size-8), 'invalid weight header size')
        header_bytes = stream.read(header_size)
        scan_text(header_bytes, 'metadata/weight_header.json')
        header = json.loads(header_bytes, object_pairs_hook=unique)
        checksum.update(first + header_bytes)
        position = 0
        types = {'F32': ('I', 4, 0x7f800000), 'F16': ('H', 2, 0x7c00), 'BF16': ('H', 2, 0x7f80)}
        for name, tensor in sorted(((name, value) for name, value in header.items() if name != '__metadata__'),
                                  key=lambda item: item[1]['data_offsets'][0]):
            require(tensor['dtype'] in types and name.endswith(('.lora_A.weight', '.lora_B.weight')), 'unexpected saved tensor type')
            code, size, mask = types[tensor['dtype']]
            start, end = tensor['data_offsets']
            require(type(start) is int and type(end) is int and start == position < end
                and end-start == math.prod(tensor['shape'])*size, 'weight offsets/shape differ')
            remaining = end-start
            while remaining:
                block = stream.read(min(1024*1024, remaining))
                require(block and len(block) % size == 0, 'short or misaligned weight data')
                values = array.array(code)
                values.frombytes(block)
                if sys.byteorder != 'little':
                    values.byteswap()
                require(not any(value & mask == mask for value in values), 'nonfinite saved weight payload')
                checksum.update(block)
                remaining -= len(block)
            reports.append(dict(name=name, dtype=tensor['dtype'], shape=tensor['shape'], values=math.prod(tensor['shape']), finite=True))
            position = end
        require(reports and stream.tell() == before.st_size and not stream.read(1), 'weight file trailing bytes or empty tensors')
        after = os.fstat(stream.fileno())
        require(all(getattr(before, key) == getattr(after, key) == getattr(path.stat(), key)
            for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')), 'weights changed during scan')
    require(checksum.hexdigest() == expected_sha, 'weight hash changed during finite scan')
    return dict(sha256=expected_sha, bytes=before.st_size, tensors=reports, finite=True,
        method='streamed IEEE exponent-bit audit; no torch/model load', archived_weight_bytes=False)


def audit(root, plan_sha256, plan, launch, bridge, diagnostic, trainer):
    run = root / 'run'
    successful = (run / 'result.json').is_file()
    require(successful != (run / 'failure.json').is_file(), 'exactly one terminal required')
    terminal = read(run / ('result.json' if successful else 'failure.json'))
    require(terminal['status'] in (('PAIRED_ADAPTERS_SAVED_READOUT_PENDING',) if successful else ('FAILED', 'PARTIAL_FAILED'))
        and terminal['readout'] == ('OUT_OF_SCOPE' if successful else 'NOT_RUN') and finite(terminal['controller_seconds']), 'terminal protocol/cost differs')
    if successful:
        require(terminal['protocol'] == WRITE_PROTOCOL and terminal['conditioning'] == CONDITIONING and terminal['model_origin'] == ORIGIN
            and terminal['claims'] == bridge.CLAIMS and terminal['semantic_no_answer_certification'] is False
            and terminal['model_authentication_certified'] is False, 'terminal claim boundary differs')
    else:
        require(terminal['retry'] is False, 'failed run must not retry')
    controller = read(run / 'controller.json')
    require(controller['pid'] == launch['pid'] and controller['plan_sha256'] == plan_sha256 and controller['worker_seconds'] == 600
        and controller['cleanup_reserve'] == 140 and finite(controller['started_wall'])
        and controller['hard_end'] == min(controller['started_wall']+1200, plan['deadline'], plan['lease_cutoff'])
        and utc(launch['started_utc']) <= controller['started_wall'], 'controller ownership/window differs')
    bounded = terminal['controller_seconds'] <= 1200 and controller['started_wall']+terminal['controller_seconds'] <= controller['hard_end']+.001
    require(not successful or bounded, 'successful controller exceeded inclusive cap')
    completed = terminal['arms'] if successful else terminal['completed']
    require(set(completed) in (set(), {'P'}, {'P', 'A'}) and (not successful or set(completed) == set(ARMS)), 'paired completion differs')
    reports, processes, costs = {}, [], []
    for arm in ARMS:
        stage, fit = run / arm, root / 'fits' / arm
        required = [stage/'process.json', stage/'supervision.json', fit/'attempt.json', fit/'manifest.json', fit/'receipt.json', fit/'adapter/DONE']
        present = all(path.is_file() for path in required)
        if not present:
            require(not successful and arm not in completed, 'completed arm missing fit/worker evidence')
            reports[arm] = dict(verified=False, missing=[str(path.relative_to(root)) for path in required if not path.is_file()], finite_weights=None)
            continue
        process, supervision, worker_launch = read(stage/'process.json'), read(stage/'supervision.json'), read(run/(arm+'.launch.json'))
        command = [plan['python'], '-B', str(DRIVER), '_worker', '--root', str(root), '--arm', arm,
            '--plan-sha256', plan_sha256, '--launch-token', worker_launch['token'], '--allow-gpu']
        require(re.fullmatch('[0-9a-f]{32}', worker_launch['token']) and worker_launch['plan_sha256'] == plan_sha256
            and worker_launch['hard_end'] == controller['hard_end'] and worker_launch['controller_pid'] == controller['pid']
            and worker_launch['command'] == process['argv'] == command and process['device'] == DEVICE
            and type(process['pid']) is int and process['pid'] > 1 and process['pgid'] == process['pid']
            and finite(process['started']) and finite(process['timeout']) and 0 < process['timeout'] <= 600, 'actual worker ownership/command/cap differs')
        require(supervision['device'] == DEVICE and supervision['returncode'] == 0 and supervision['error'] is None
            and all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
            and finite(supervision['reserved_seconds']) and supervision['reserved_seconds'] <= process['timeout']+140, 'worker cleanup/cost invalid')
        require(read(fit/'attempt.json') == dict(arm=arm, plan_sha256=plan_sha256, init_adapter=None, pid=process['pid']), 'fit/worker attempt differs')
        require(read(fit/'manifest.json')['files'] == diagnostic.tree_hashes(fit, ('manifest.json',)), 'sealed fit changed')
        validated = bridge.validate_fit(root, arm, plan, diagnostic, trainer)
        require(validated == read(fit/'receipt.json') and validated['steps'] == validated['observed_forward_batches'] == 12
            and validated['adapter'] == str(fit/'adapter'), 'saved fit/forward receipt differs')
        if arm in completed:
            require(completed[arm] == dict(validated, fit_manifest_sha256=digest(fit/'manifest.json'),
                supervision_sha256=digest(stage/'supervision.json')), 'controller/saved fit receipt join differs')
        weight_report = finite_weights(fit/'adapter/adapter_model.safetensors', validated['files']['adapter_model.safetensors'])
        manifest = read(fit/'adapter/train_manifest.json')
        reports[arm] = dict(verified=True, worker_pid=process['pid'], fit_receipt_sha256=digest(fit/'receipt.json'),
            adapter_files=validated['files'], finite_weights=weight_report, steps=manifest['steps'], epochs=manifest['epochs_run'],
            micro_batches=manifest['micro_batches'], exposure=validated['exposure'], tokens=manifest['tokens'],
            train_seconds=manifest.get('train_seconds'), worker_reserved_seconds=supervision['reserved_seconds'])
        processes.append(process)
        costs.append(supervision['reserved_seconds'])
    require(len({process['pid'] for process in processes}) == len(processes) and all(process['pid'] != launch['pid'] for process in processes), 'workers reused controller/worker PID')
    require(all(left['started']+cost <= right['started'] for left, cost, right in zip(processes, costs, processes[1:])), 'worker windows overlap/reorder')
    require(set(root.glob('**/supervision.json')) <= {run/arm/'supervision.json' for arm in ARMS}, 'unexpected supervision')
    aggregate = None
    if successful:
        require(all(reports[arm]['verified'] for arm in ARMS), 'both verified fits required before aggregate')
        require(terminal['exposure'] == {arm: plan['tokens'][arm]['exposure'] for arm in ARMS}, 'terminal exposure differs')
        aggregate = dict(optimizer_updates=24, epochs_per_arm=12, rows_per_arm=2,
            full_target_tokens_seen=sum(reports[arm]['exposure']['full_target_tokens_seen'] for arm in ARMS),
            input_tokens_seen=sum(plan['tokens'][arm]['train_tokens_seen'] for arm in ARMS),
            padded_input_tokens_seen=sum(reports[arm]['exposure']['padded_input_tokens_seen'] for arm in ARMS),
            target_matched=False, input_matched=False, efficacy=None)
    return dict(status=terminal['status'], write_success=successful, arms=reports, aggregate=aggregate,
        controller_seconds=terminal['controller_seconds'], controller_within_bound=bounded,
        observed_verified_worker_seconds=sum(costs) if costs else None, worker_cost_complete=len(costs)==2,
        readout='OUT_OF_SCOPE', claims=bridge.CLAIMS, model_origin=ORIGIN, conditioning=CONDITIONING)


def vacancy(plan, expected_uuid):
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'Main must use env -u CUDA_VISIBLE_DEVICES for vacancy/queue queries')
    checker = load(Path(plan['source_root'])/'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'process_write_release_checker')
    gpu, xml = checker.check_free(DEVICE)
    check_uuid(gpu, xml, expected_uuid)
    return gpu, xml


def validate_archive(path, hashes):
    seen, total = set(), 0
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            require(member.isfile() and not member.issym() and not member.islnk() and not name.is_absolute()
                and '..' not in name.parts and str(name) == member.name and member.name.startswith('metadata/')
                and member.name in hashes and member.name not in seen and member.size <= MAX_FILE, 'unsafe/unexpected archive member')
            total += member.size
            require(total <= MAX_TOTAL and len(seen) < MAX_FILES, 'archive size/member bound')
            stream = archive.extractfile(member)
            data = stream.read(MAX_FILE+1)
            require(len(data) == member.size and hashlib.sha256(data).hexdigest() == hashes[member.name], 'archive member hash differs')
            scan_text(data, member.name)
            seen.add(member.name)
    require(seen == set(hashes), 'archive incomplete')


def pack(path, files, hashes):
    descriptor = os.open(unaliased(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream, tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name, source in sorted(files.items()):
            data = payload(source)
            require(hashlib.sha256(data).hexdigest() == hashes[name], 'metadata changed during archive')
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o600
            archive.addfile(member, io.BytesIO(data))
    pin = file_hash(path)
    validate_archive(path, hashes)
    require(file_hash(path) == pin, 'archive changed during validation')
    return pin


def collect(root, plan_sha256, launch_root, launch_sha256, out):
    started, wall = time.monotonic(), time.time()
    root, logs, output = unaliased(root), unaliased(launch_root), unaliased(out)
    observed = status(root, plan_sha256, logs, launch_sha256)
    require(observed['ready'], 'terminal AND whole owned process/session release required before fit reads')
    require(output.parent == root.parent and output not in (root, logs) and not output.exists(), 'exclusive fresh sibling output required; no retries')
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'Main must collect with CUDA_VISIBLE_DEVICES unset')
    own_pin = digest(__file__)
    output.mkdir(mode=0o700)
    write_json(output/'started.json', dict(plan_sha256=plan_sha256, launch_sha256=launch_sha256, started_wall=wall,
        collector_sha256=own_pin, collection_limit_seconds=300, retry=False))
    try:
        files, hashes, exclusions = inventory(root, logs)
        original_hashes = dict(hashes)
        bridge, plan, diagnostic, exporter, trainer = bind(root, plan_sha256, logs, observed['launch'])
        material = material_audit(root, plan, bridge, diagnostic, exporter)
        report = audit(root, plan_sha256, plan, observed['launch'], bridge, diagnostic, trainer)
        require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned process/session reappeared')
        gpu, xml = vacancy(plan, observed['launch']['gpu']['gpu_uuid'])
        release_time = time.time()
        require(inventory(root, logs)[1:] == (original_hashes, exclusions), 'run evidence changed during audit')
        full_seconds = release_time-utc(observed['launch']['started_utc'])
        require(finite(full_seconds), 'invalid launch-to-vacancy time')
        write_json(output/'audit.json', report)
        write_json(output/'material_summary.json', material)
        write_json(output/'custody.json', dict(plan_sha256=plan_sha256, launch_sha256=launch_sha256, implementation=plan['implementation'],
            exporter_source_hashes=plan['exporter_source_hashes'], model_files=plan['model_files'], excluded_native_files=exclusions,
            model_origin=ORIGIN, weights_in_capsule=False, original_raw_and_token_material_in_capsule=False,
            credential_policy='Strict path allowlist plus known credential rejection, not a universal secret detector'))
        write_new(output/'release.xml', xml.encode())
        write_json(output/'release.json', dict(full_release_snapshot=True, owned_ids=observed['owned_ids'], gpu=gpu,
            observed_wall=release_time, plan_sha256=plan_sha256, launch_sha256=launch_sha256,
            xml_sha256=digest(output/'release.xml'), full_launch_to_release_seconds=full_seconds,
            collection_seconds_at_snapshot=time.monotonic()-started,
            accounting='Full wall-clock launch-to-observed-vacancy; worker/controller clocks are nested subsets, never additive'))
        for name in ('started.json', 'audit.json', 'material_summary.json', 'custody.json', 'release.xml', 'release.json'):
            path = output/name
            data = payload(path)
            member = 'metadata/collection/'+name
            scan_text(data, member)
            files[member], hashes[member] = path, hashlib.sha256(data).hexdigest()
        archive = output/'metadata.tgz'
        pin = pack(archive, files, hashes)
        require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned session reappeared after packing')
        bridge.checked_plan(root, plan_sha256)
        require(inventory(root, logs)[1:] == (original_hashes, exclusions) and all(digest(path) == hashes[name] for name, path in files.items()),
            'metadata/weight/source changed after packing')
        require(file_hash(archive) == pin and digest(__file__) == own_pin and digest(LAUNCHER) == LAUNCHER_SHA,
            'archive/collector/launcher changed')
        final_gpu, final_xml = vacancy(plan, observed['launch']['gpu']['gpu_uuid'])
        final_release = time.time()
        require(time.monotonic()-started <= 300, 'collection cap exceeded')
        require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned session appeared at publication')
        write_new(output/'final_release.xml', final_xml.encode())
        result = dict(status='COLLECTED_PAIRED_WRITE' if report['write_success'] else 'COLLECTED_FAILURE_NO_AGGREGATE',
            archive=str(archive), archive_sha256=pin, files=hashes, full_release=True, aggregate_available=report['aggregate'] is not None,
            final_vacancy=dict(gpu=final_gpu, xml_sha256=hashlib.sha256(final_xml.encode()).hexdigest(), observed_wall=final_release),
            full_launch_to_final_vacancy_seconds=final_release-utc(observed['launch']['started_utc']),
            collection_seconds=time.monotonic()-started, plan_sha256=plan_sha256, collector_sha256=own_pin,
            weights_in_capsule=False, retry=False, model_origin=ORIGIN, readout='OUT_OF_SCOPE')
        write_json(output/'validation.json', result)
        return {key: value for key, value in result.items() if key != 'files'}
    except BaseException as error:
        write_json(output/'failure.json', dict(error_type=type(error).__name__, aggregate=None, retry=False,
            collection_seconds=time.monotonic()-started, partial_artifacts_preserved=True))
        raise


def file_hash(path):
    result, size = hashlib.sha256(), 0
    path = unaliased(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'unsafe archive hash input')
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(data)
            require(size <= MAX_TOTAL + 16*1024*1024, 'archive byte bound exceeded')
            result.update(data)
        after = os.fstat(stream.fileno())
        require(size == before.st_size and all(getattr(before, key) == getattr(after, key) == getattr(path.stat(), key)
                for key in ('st_ino', 'st_dev', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'archive changed during hashing')
    return result.hexdigest()


class CollectionExpired(BaseException):
    pass


def finish(**kwargs):
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing timer conflicts')
    def expired(number, frame):
        raise CollectionExpired('300s external custody window exhausted')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        return collect(**kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'finish'))
    for name in ('root', 'plan-sha256', 'launch-root', 'launch-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--out')
    args = vars(parser.parse_args(argv))
    action = args.pop('action')
    if action == 'status':
        require(args.pop('out') is None, 'status never writes an output')
        result = status(**args)
        result.pop('launch')
    else:
        require(args.get('out') is not None, 'finish needs --out')
        result = finish(**args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
