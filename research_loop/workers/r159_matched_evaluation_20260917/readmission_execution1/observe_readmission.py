import json
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')


def main():
    assert socket.gethostname() == '[REDACTED_HOST]'
    sys.path.insert(0, str(ROOT / 'preparation/runtime_generation3/source'))
    from gpu import orch_r159_matched_evaluation as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    operator = ROOT / 'control/frozen_readmission_generation2/operator1'
    result = dict(observed_unix=time.time(), ledger=evaluator.ledger_status(ROOT, evaluator.ORIGINAL_PLAN_SHA256),
                  held_content_read=False, new_scans=0, process_actions=False, operator=str(operator))
    for name in ('DISPATCH_LAUNCH', 'WRAPPER_STARTED', 'DISPOSITION', 'DISPATCH_ERROR', 'VALIDATION', 'CPU_GATE'):
        path = operator / f'{name}.json'
        if path.is_file():
            result[name] = evaluator.read(path)
    admission = operator / 'ACTUAL_ADMISSION.private.json'
    if admission.is_file():
        captured = evaluator.read(admission)
        report = captured['report']
        result['actual_admission'] = dict(reference=evaluator.ref(admission), observed_unix=captured['observed_unix'],
            label=captured['label'], clear=report['clear'], blocking_reasons=report['blocking_reasons'],
            gpu=report['gpu'], scanner_euid=report['scanner_euid'])
    attempt = ROOT / 'attempts/parented_frozen_0'
    launch = attempt / 'LAUNCH.json'
    if launch.is_file():
        result['native_launch'] = evaluator.read(launch)
    for suffix in ('RESERVED', 'COMPLETE', 'FAILED'):
        path = ROOT / f'ledger/parented_frozen_0.{suffix}.json'
        if path.is_file():
            result[suffix] = dict(reference=evaluator.ref(path), metadata=evaluator.read(path))
    sealed = attempt / 'sealed'
    if sealed.is_dir():
        names = [path.name for path in sealed.iterdir()]
        result['private_artifact_counts'] = {kind: sum(name.startswith('CALL_') and name.endswith('.'+kind+'.private.json')
            for name in names) for kind in ('RESERVED', 'RAW', 'SCORE')}
    result['gpu_processes'] = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_gpu_memory',
        '--format=csv,noheader,nounits'], text=True, timeout=20).splitlines()
    proposal = ROOT / 'control/unparented_readmission_generation2'
    result['unparented_proposal'] = evaluator.read(proposal / 'PROPOSAL.json')
    result['unparented_proposal_reference'] = evaluator.ref(proposal / 'PROPOSAL.json')
    result['observed_unix'] = time.time()
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
