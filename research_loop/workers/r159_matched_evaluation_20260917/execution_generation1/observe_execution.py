import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
SOURCE = ROOT / 'preparation/runtime_generation3/source'
CONTROL = ROOT / 'control/candidate5_initial3_runtime3'
OPERATOR = ROOT / 'control/initial3_execution_generation1'


def main():
    assert socket.gethostname() == '[REDACTED_HOST]'
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r159_matched_evaluation as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    ledger = evaluator.ledger_status(ROOT, evaluator.ORIGINAL_PLAN_SHA256)
    configs = {str(CONTROL / f'{arm}.EXECUTION.proposed.json'): arm for arm in evaluator.ARMS}
    gpu_rows = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_gpu_memory',
        '--format=csv,noheader,nounits'], text=True, timeout=20)
    targets = {}
    for line in gpu_rows.splitlines():
        fields = [field.strip() for field in line.split(',')]
        if len(fields) == 3 and fields[1] in sidecar.DEVICES.values():
            targets[int(fields[0])] = dict(gpu_uuid=fields[1], used_gpu_memory_mib=fields[2])
    result = dict(status='METADATA_ONLY', observed_unix=time.time(), ledger=ledger, arms={},
        hard_end_unix=1789632000, latest_dispatch_strictly_before_unix=1789628385,
        held_contents_read=False, process_actions=False)
    processes = {arm: [] for arm in evaluator.ARMS}
    for directory in Path('/proc').glob('[0-9]*'):
        try:
            raw = (directory / 'cmdline').read_bytes()
            args = [part.decode(errors='replace') for part in raw.split(b'\0') if part]
            if 'gpu.orch_r159_matched_evaluation' not in args or '--config' not in args:
                continue
            config = args[args.index('--config')+1]
            if config not in configs:
                continue
            identity = sidecar.identity(int(directory.name))
            state = (directory / 'stat').read_text().rsplit(')', 1)[1].split()[0]
            processes[configs[config]].append(dict(identity=identity, process_state=state,
                phase='evaluate' if 'evaluate' in args else 'dispatch',
                command_sha256=hashlib.sha256(raw).hexdigest(), gpu=targets.get(identity['pid'])))
        except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError):
            continue
    for arm in evaluator.ARMS:
        key = arm+'_0'
        attempt = ROOT / 'attempts' / key
        metadata = dict(processes=processes[arm], reserved=False, completed=False, failed=False)
        for name in ('DISPATCH_ONCE', 'DISPATCH_LAUNCH', 'VALIDATION'):
            path = OPERATOR / f'{arm}.{name}.json'
            if path.is_file():
                metadata[name.lower()] = evaluator.read(path)
        claim = ROOT / 'ledger' / f'{key}.RESERVED.json'
        if claim.is_file():
            entry = evaluator.read(claim)
            metadata.update(reserved=True, calls_charged=entry['calls_charged'],
                reservation=evaluator.ref(claim), execution=entry['execution'])
        for suffix, name in (('COMPLETE', 'completed'), ('FAILED', 'failed')):
            path = ROOT / 'ledger' / f'{key}.{suffix}.json'
            if path.is_file():
                terminal = evaluator.read(path)
                assert terminal['reservation_sha256'] == evaluator.sha(claim)
                metadata[name] = True
                metadata[name+'_receipt'] = evaluator.ref(path)
                metadata[name+'_observed_unix'] = terminal['observed_unix']
                if name == 'completed':
                    completion = terminal['completion']
                    assert evaluator.sha(completion['path']) == completion['sha256']
                    metadata['sealed_completion_reference'] = completion
        launch = attempt / 'LAUNCH.json'
        if launch.is_file():
            metadata['runner_launch'] = evaluator.read(launch)
        sealed = attempt / 'sealed'
        if sealed.is_dir():
            names = os.listdir(sealed)
            metadata['private_artifact_counts'] = {
                kind.lower(): sum(name.startswith('CALL_') and name.endswith('.'+kind+'.private.json') for name in names)
                for kind in ('RESERVED','RAW','SCORE')}
        result['arms'][arm] = metadata
    result['observed_unix'] = time.time()
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
