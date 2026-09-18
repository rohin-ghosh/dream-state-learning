"""One typed preload recovery; reuse retirement and unchanged strict dispatch."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import time


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def eligibility(failure, admission, attempt_names, owners_present, boundary_sha, expected_sha):
    require(failure.get('reason') == 'original_privileged_clear_admission' and
            failure.get('retired') is True and failure.get('terminated') is True,
            'typed_preload_refusal_only')
    require(admission.get('clear') is False and admission.get('scanner_euid') == 0 and
            admission.get('blocking_reasons') == ['process_identity_drift:2438435'], 'exact_run1_refusal')
    require(not owners_present, 'all_original_owners_absent')
    require(not set(attempt_names).intersection({'LAUNCH.json', 'NATIVE.log', 'NATIVE_EXIT.json',
        'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json'}), 'no_prior_native_dispatch')
    require(boundary_sha == expected_sha, 'same_complete_boundary_no_suffix')


def validate(output, saved, plan):
    binding = read(output / 'READMISSION_BINDING.json')
    original = Path(binding['original'])
    require(original == Path('/localhome/local-rohing/orch_r181_node5_run1_1789682149719422427') and
            plan['physical'] == 2 and plan['root'] == '/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1',
            'only_run1_typed_preload_recovery')
    for name, expected in binding['files'].items():
        require(ref(original / name) == expected, 'unchanged_preserved_refusal_' + name)
    previous = read(original / 'READY.json')
    owners = list(previous['pair'].values()) + [read(original / 'OPERATOR_STARTED.json')['identity']]
    present = [entry['pid'] for entry in owners if Path('/proc', str(entry['pid'])).exists()]
    require(not Path('/proc/2438435').exists(), 'original_scanner_drift_process_gone')
    boundary = saved.saved_boundary(plan['root'])
    require(boundary is not None and boundary['cycle'] == 48, 'saved_sleep48_only')
    eligibility(read(original / 'EXECUTION_FAILED.json'), read(original / 'attempt/ADMISSION.json'),
        [path.name for path in (original / 'attempt').iterdir()], present,
        boundary['record']['sha256'], binding['boundary_sha256'])
    return previous, boundary


def prepare(output, saved, plan):
    previous, boundary = validate(output, saved, plan)
    original = Path(read(output / 'READMISSION_BINDING.json')['original'])
    shutil.copyfile(original / 'OWNER_RETIRED.json', output / 'OWNER_RETIRED.json')
    return previous['pair'], dict(historical_only=True, source=ref(original / 'READY.json'),
        clear_GPU_admission='FRESH_ORIGINAL_GUARD_BEFORE_ANY_LAUNCH', saved_cycle=boundary['cycle'])


def execute(output, operator):
    saved, config, plan = operator.validate_successor(output)
    validate(output, saved, plan)
    descriptor = os.open(operator.BASE / 'orch_r157_run1_HANDOFF.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'READMISSION_ONCE').mkdir()
        validate(output, saved, plan)
        operator.write(output / 'READMISSION_INTENT.json', dict(binding=ref(output / 'READMISSION_BINDING.json'),
            source=ref(output / 'SOURCE_MANIFEST.json'), native_signals=0, reset=False,
            replay=False, observed_unix=time.time()))
        operator.supervise(output)
    except BaseException as error:
        operator.write(output / 'READMISSION_FAILED.json', dict(reason=str(error),
            no_retry=True, observed_unix=time.time()))
        raise
    finally:
        os.close(descriptor)
