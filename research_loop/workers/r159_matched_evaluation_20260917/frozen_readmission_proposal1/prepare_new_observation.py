import json
from pathlib import Path
import subprocess


DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = DIRECTORY.parent.parents[2]


def main():
    program = '''
import hashlib, json, os, socket, sys, time
from pathlib import Path
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
source = root/'preparation/runtime_generation3/source'
original_control = root/'control/candidate5_initial3_runtime3'
operator = root/'control/initial3_execution_generation1'
destination = root/'control/frozen_readmission_generation2'
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789628385
sys.path.insert(0, str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\\n')
    path.chmod(0o400)
destination.mkdir(mode=0o700, parents=True, exist_ok=False)
config_path = original_control/'parented_frozen.EXECUTION.proposed.json'
config = evaluator.read(config_path)
old_once = operator/'parented_frozen.DISPATCH_ONCE.json'
old_log = operator/'parented_frozen.dispatch.private.log'
assert old_once.is_file() and old_log.is_file()
assert evaluator.sha(old_log) == 'bd1f76e9d27ed73296518c1b62a0daa2509117bb77f328e7de6ab30021c1737a'
assert not (root/'ledger/parented_frozen_0.RESERVED.json').exists()
assert not (root/'attempts/parented_frozen_0').exists()
old_hashes = dict(once=evaluator.ref(old_once), refusal_log=evaluator.ref(old_log),
    old_go=evaluator.ref(original_control/'parented_frozen.MAIN_GO.json'))
report = sidecar.scan(dict(config, physical=1, gpu_uuid=sidecar.DEVICES[1]))
full = dict(schema='R159_NEW_PHYSICAL1_OBSERVATION_V1', status='NEW_OBSERVATION_NOT_HISTORICAL_REFUSAL',
    observed_unix=time.time(), report=report, historical_reason_recovered=False)
write(destination/'PHYSICAL1_NEW_SCAN.private.json', full)
owned = []
for process in report['processes']:
    try:
        raw = Path('/proc',str(process['pid']),'cmdline').read_bytes()
        args = [part.decode(errors='replace') for part in raw.split(b'\\0') if part]
        if 'gpu.orch_r159_matched_evaluation' not in args or 'evaluate' not in args or '--config' not in args:
            continue
        path = args[args.index('--config')+1]
        if path not in (str(original_control/'parented_learning.EXECUTION.proposed.json'),
                        str(original_control/'unparented_learning.EXECUTION.proposed.json')):
            continue
        owned.append(dict(identity=sidecar.identity(process['pid']), command_sha256=process['command_sha256'],
            source_config=path, cvd=process.get('cvd'), target1_device_open=process.get('target_device_open',False),
            unreadable=process.get('unreadable')))
    except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError):
        continue
foreign_from_evaluator = any(process['target1_device_open'] for process in owned)
proposed_physical = 1 if report['clear'] else 0 if foreign_from_evaluator else None
config_ref = None
if proposed_physical is not None:
    proposed = dict(config, physical=proposed_physical, gpu_uuid=sidecar.DEVICES[proposed_physical])
    evaluator.validate_sources(proposed)
    evaluator.candidate_check(proposed, evaluator.validate_plan(proposed['campaign']))
    write(destination/'parented_frozen.EXECUTION.proposed.json', proposed)
    config_ref = evaluator.ref(destination/'parented_frozen.EXECUTION.proposed.json')
assert old_hashes == dict(once=evaluator.ref(old_once), refusal_log=evaluator.ref(old_log),
    old_go=evaluator.ref(original_control/'parented_frozen.MAIN_GO.json'))
metadata = dict(schema='R159_FROZEN_PRE_NATIVE_READMISSION_PROPOSAL_V1',
    status='PROPOSAL_ONLY_REQUIRES_NEW_MAIN_GO', observed_unix=time.time(),
    observation_label=full['status'], full_scan=evaluator.ref(destination/'PHYSICAL1_NEW_SCAN.private.json'),
    clear=report['clear'], blocking_reasons=report['blocking_reasons'], gpu=report['gpu'],
    scanner_euid=report['scanner_euid'], own_evaluators=owned,
    current_evaluator_opens_target1=foreign_from_evaluator, historical_reason_recovered=False,
    original_artifacts_unchanged=old_hashes, frozen_reserved=False, frozen_samples_exist=False,
    proposed_physical=proposed_physical, proposed_execution=config_ref,
    requires_serial_release_of_all_existing_evaluations=proposed_physical == 0,
    fresh_full_admission_required=True, new_operator_once_required=True,
    reuse_old_GO_forbidden=True, main_GO_issued=False, dispatched=False,
    source_changed=False, process_actions=False, hard_end_unix=1789632000,
    latest_dispatch_strictly_before_unix=1789628385, call_cap=672, checkpoint_cap=12)
write(destination/'PROPOSAL.json', metadata)
print(json.dumps(dict(metadata=metadata, full_current_report=full,
    configuration=evaluator.read(config_ref['path']) if config_ref else None),sort_keys=True))
'''
    with (DIRECTORY / 'PREPARE.stderr').open('xb') as errors:
        result = subprocess.run(['bash',str(REPOSITORY/'gpu/ovx_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B -'], input=program.encode(),
            stdout=subprocess.PIPE, stderr=errors, check=True, timeout=120)
    returned = json.loads(result.stdout)
    for name, value in [('PROPOSAL.json',returned['metadata']),
                        ('PHYSICAL1_NEW_SCAN.private.json',returned['full_current_report']),
                        ('parented_frozen.EXECUTION.proposed.json',returned['configuration'])]:
        if value is not None:
            with (DIRECTORY/name).open('x') as stream:
                json.dump(value,stream,sort_keys=True,indent=2)
                stream.write('\n')
    print(json.dumps(returned['metadata'],sort_keys=True))


if __name__ == '__main__':
    main()
