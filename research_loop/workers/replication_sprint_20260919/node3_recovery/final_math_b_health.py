"""Final bounded read-only MathB health and latest ACT evidence; no launch path."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork')
CONTROL = ROOT / 'control_ws6_pending_math_b_20260919T144429Z'
PID = 2890010
START_TICKS = '53597510'
GPU = 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def observe():
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524, 'original_node_owner')
    guard_path = CONTROL / 'GUARD_BUILDER1450.json'
    guard_bytes = guard_path.read_bytes()
    require(hashlib.sha256(guard_bytes).hexdigest() == 'd51e90bfea4306030ece342db7fc3d9d03790679a1ef1b7517bdac26b7e90ba0', 'original_guard')
    guard = json.loads(guard_bytes)
    process = Path('/proc') / str(PID)
    command = (process / 'cmdline').read_bytes()
    stat = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    expected_command = ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
        'gpu.ws6_math_b_pending_entry', 'native', '--config', str(guard_path)]
    require(command.rstrip(b'\0').decode().split('\0') == expected_command
        and stat[19] == START_TICKS and stat[0] not in ('Z', 'X') and process.stat().st_uid == 2524,
        'same_healthy_native_identity')
    apps = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader'],
        capture_output=True, text=True, check=True, timeout=20).stdout
    compute = [dict(pid=int(line.split(',')[0]), gpu_uuid=line.split(',')[1].strip())
        for line in apps.splitlines() if line.strip()]
    require([item['pid'] for item in compute if item['gpu_uuid'] == GPU] == [PID], 'exclusive_original_gpu2')
    failures = [name for name in ('EXIT.json', 'OUTER_FAILED.json', 'OUTER_EXIT.json') if (CONTROL / name).exists()]
    require(not failures, 'no_new_exit_or_failure')
    records = ROOT / 'raw/stream/records'
    paths = sorted(path for path in records.iterdir() if re.fullmatch(r'\d{20}\.json', path.name))
    budget = [0]

    def read(index):
        path = records / f'{index:020d}.json'
        size = path.stat().st_size
        require(size <= 64 * 1024**2 and budget[0] + size <= 256 * 1024**2, 'bounded_record_read')
        raw = path.read_bytes()
        budget[0] += len(raw)
        value = json.loads(raw)
        require(value['index'] == index and value['sha256'] == digest({key: item for key, item in value.items()
            if key != 'sha256'}), 'record_digest')
        intent = json.loads(path.with_name(path.stem + '.intent.json').read_bytes())
        require(intent == dict({key: value[key] for key in ('schema', 'journal_id', 'index', 'previous_sha256')},
            record_sha256=value['sha256']), 'record_intent')
        return value

    head_index = int(paths[-1].stem)
    latest_act = None
    latest_request = None
    window = []
    for path in reversed(paths[-128:]):
        with path.open('rb') as handle:
            handle.seek(max(0, path.stat().st_size - 8192))
            matches = re.findall(rb',"index":(\d+),"journal_id":"[^"]+","kind":"([^"]+)"', handle.read())
        require(bool(matches) and int(matches[-1][0]) == int(path.stem), 'bounded_metadata_index')
        kind = matches[-1][1].decode()
        window.append(dict(index=int(path.stem), kind=kind, bytes=path.stat().st_size))
        if kind not in ('REQUEST', 'R184_ACT'):
            continue
        record = read(int(path.stem))
        if record['kind'] == 'REQUEST' and latest_request is None:
            latest_request = dict(index=record['index'], sha256=record['sha256'])
        if record['kind'] == 'R184_ACT' and latest_act is None:
            latest_act = record
        if latest_act is not None and latest_request is not None:
            break
    require(latest_act is not None, 'actual_recent_ACT_required')
    origin = latest_act['document']['origin']
    require(origin['kind'] == 'TRAIN_CHILD_RESPONSE', 'actual_child_response_origin')
    response = read(origin['record_index'])
    require(response['kind'] == 'RESPONSE' and response['sha256'] == origin['record_sha256'], 'ACT_response_binding')
    request = None
    for index in range(response['index'] - 1, max(9555, response['index'] - 12), -1):
        candidate = read(index)
        if candidate['kind'] != 'REQUEST':
            continue
        if digest({key: value for key, value in candidate['document'].items() if key != 'resume_state'}) == response['document']['request_sha256']:
            request = candidate
            break
    require(request is not None, 'actual_request_response_digest_binding')
    commits = []
    for index in range(response['index'] + 1, latest_act['index']):
        candidate = read(index)
        if candidate['kind'] == 'COMMITTED' and candidate['document']['source_sha256'] == latest_act['document']['source_sha256']:
            commits.append(dict(index=index, sha256=candidate['sha256']))
    require(len(commits) == 1, 'exact_COMMITTED_before_ACT')
    receipt = latest_act['document'].get('receipt', {})
    capacity = os.statvfs(ROOT)
    result = dict(utc=datetime.now(timezone.utc).isoformat(), host=os.uname().nodename, read_only=True,
        native=dict(pid=PID, start_ticks=stat[19], state=stat[0], command_sha256=hashlib.sha256(command).hexdigest()),
        compute_apps=compute, head_index=head_index, latest_request=latest_request,
        latest_ACT=dict(index=latest_act['index'], sha256=latest_act['sha256'],
            record_mtime_utc=datetime.fromtimestamp((records / f"{latest_act['index']:020d}.json").stat().st_mtime,
                timezone.utc).isoformat(), document_keys=sorted(latest_act['document']),
            receipt_summary={key: value for key, value in receipt.items()
                if isinstance(value, (str, int, float, bool)) or value is None}),
        ACT_RESPONSE=dict(index=response['index'], sha256=response['sha256']),
        ACT_REQUEST=dict(index=request['index'], sha256=request['sha256']),
        ACT_COMMITTED=commits[0], ACT_outcome=latest_act['document']['outcome'],
        guard_sha256=hashlib.sha256(guard_bytes).hexdigest(), hard_end_unix=guard['hard_end_unix'],
        failures=failures, owner_available_bytes=capacity.f_bavail * capacity.f_frsize,
        owner_available_blocks=capacity.f_bavail, record_bytes_read=budget[0],
        metadata_only_window=window, full_journal_verification_claim=False,
        math_success_claim=False, parent_restoration_claim=False, native_signals=0, provider_calls=0)
    print(json.dumps(result, sort_keys=True), flush=True)


def main():
    here = Path(__file__).resolve().parent
    source = Path(__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0] + '\nobserve()\n'
    response = subprocess.run(['bash', 'gpu/ovx2_ssh.sh', 'env PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        cwd=here.parents[3], input=source, capture_output=True, text=True, timeout=90)
    require(response.returncode == 0, response.stderr)
    value = json.loads(response.stdout)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = here / ('MATH_B_FINAL_HEALTH_' + stamp + '.json')
    with destination.open('x') as output:
        output.write(response.stdout)
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps(dict(receipt=str(destination), **value), sort_keys=True))


if __name__ == '__main__':
    main()
