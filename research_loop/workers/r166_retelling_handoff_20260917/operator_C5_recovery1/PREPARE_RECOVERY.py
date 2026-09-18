from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import time
from gpu import orch_r166_retelling_handoff as handoff

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_C5_20260917_recovery1')
predecessor = operator.parent / 'orch_r166_retelling_C5_20260917_activation3'
output = operator.parent / 'orch_r166_retelling_C5_20260917_recovery1'
saved = handoff.saved
require = handoff.require
handoff.cpu_operator()
cpu = operator / 'CPU.json'
dependencies = handoff.validate_cpu(cpu)
require(saved.sha(predecessor / 'REQUEST.json') ==
        '610008ad692d4705c119f9cc745364e6140bfdd5c02208b27ead3ac5c63d3df9', 'exact_failed_C5_candidate')
request = saved.read(predecessor / 'REQUEST.json')
old_source = Path(request['source_root'])
require(saved.files(old_source) == request['source_files'], 'failed_source_untouched')
handoff.require_retired(request['pair'])
failed = saved.read(predecessor / 'ACTIVATION_FAILED.json')
require(failed['original_exit_confirmed'] is True and failed['termination_intent_recorded'] is True
        and failed['no_retry'] is True, 'confirmed_previous_retirement')
require(saved.read(predecessor / 'attempt/NATIVE_EXIT.json')['returncode'] == 1,
        'failed_native_exit_confirmed')
require(saved.sha(predecessor / 'attempt/NATIVE.log') ==
        saved.read(operator / 'EXPECTED_FAILURE.json')['native_log_sha256'], 'exact_pre_model_trace')
require(not (predecessor / 'attempt/DISPATCH_ONCE').exists()
        and (predecessor / 'attempt/DISPATCH_ONCE.json').is_file(), 'preserved_marker_failure')
launch = saved.read(predecessor / 'attempt/LAUNCH.json')
for pid in (launch['pid'], saved.read(predecessor / 'MAIN_DISPATCH.json')['pid']):
    require(not Path('/proc', str(pid)).exists(), 'predecessor_execution_absent')
old_plan = saved.bound(request['old_plan'])
boundary = saved.saved_boundary(old_plan['root'])
proof = saved.read(predecessor / 'control/SAVED_PROOF.json')
require(boundary is not None and boundary['index'] == 2899 and boundary['cycle'] == 28
        and boundary['reference']['sha256'] == '82f540efda67a3766b87339d21172c146f2b3cfef376498127d66aab726c4c61'
        and boundary['state_sha256'] == proof['stream_sha256'] ==
        'a92a4a111ef7493adfc3b479ee1005f94f2579d3460e9486ef27d5d3b407d9b3'
        and proof['optimizer_steps'] == 2478, 'exact_saved28_no_post_boundary_work')
require(saved.sha(proof['checkpoint_path']) == proof['checkpoint_sha256'] ==
        '948721092756e429c0ca808720a14d8aa27c113ec4bbf8e0f3e5077437d39a88', 'exact_saved_checkpoint')
require(not output.exists(), 'fresh_recovery_namespace_only')
output.mkdir(mode=0o700)
source = output / 'source'
shutil.copytree(old_source, source)
for directory in (source, source / 'gpu', source / 'tests'):
    directory.chmod(0o755)
for name in (handoff.RELATIVE, handoff.TEST_RELATIVE):
    (source / name).chmod(0o644)
    shutil.copyfile(operator / 'source' / name, source / name)
inventory = saved.files(source)
require(set(inventory) == set(request['source_files']) and all(
    inventory[name] == checksum for name, checksum in request['source_files'].items()
    if name not in (handoff.RELATIVE, handoff.TEST_RELATIVE)), 'only_reviewed_marker_repair_and_tests')
require(all(inventory[name] == checksum for name, checksum in dependencies.items())
        and inventory[handoff.POLICY_TEST_RELATIVE] == handoff.POLICY_TEST_SHA256, 'all_closure_pins')
saved.freeze(source)
evidence = dict(schema='R166_C5_PREMODEL_RECOVERY_CUSTODY_V1',
    predecessor=saved.reference(predecessor / 'REQUEST.json'),
    original_retirement=saved.reference(predecessor / 'OWNER_RETIRED.json'),
    original_failure=saved.reference(predecessor / 'ACTIVATION_FAILED.json'),
    native_exit=saved.reference(predecessor / 'attempt/NATIVE_EXIT.json'),
    native_trace=saved.reference(predecessor / 'attempt/NATIVE.log'),
    saved_proof=saved.reference(predecessor / 'control/SAVED_PROOF.json'),
    boundary=boundary['reference'], checkpoint=saved.reference(proof['checkpoint_path']),
    previous_GO_is_not_reused=True, no_model_before_failure=True,
    no_new_GO=True, no_signals=True, no_dispatch=True, created_unix=time.time())
saved.write(output / 'RECOVERY_CUSTODY.json', evidence)
new_request = deepcopy(request)
new_request.update(source_root=str(source), source_files=inventory, cpu=saved.reference(cpu),
    candidate_predecessor=saved.reference(predecessor / 'REQUEST.json'),
    recovery_custody=saved.reference(output / 'RECOVERY_CUSTODY.json'), created_unix=time.time(),
    status='STAGED_C5_RETIRED_OWNER_RECOVERY_NO_GO')
saved.write(output / 'REQUEST.json', new_request)
command = [str(saved.PYTHON), '-B', '-m', handoff.MODULE, 'prepare', '--output', str(output)]
result = subprocess.run(command, cwd=source, env=saved.environment(source),
    capture_output=True, text=True, timeout=240)
saved.write(operator / 'C5_SUBPROCESS.json', dict(command=command, cwd=str(source),
    returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, observed_unix=time.time()))
require(result.returncode == 0, result.stderr)
prepared = json.loads(result.stdout)
actual_proof = saved.bound(prepared['proof'])
require(actual_proof == proof and saved.saved_boundary(old_plan['root']) == boundary,
        'identical_cpu_loaded_state_and_no_new_work')
require(saved.files(old_source) == request['source_files'], 'failed_source_still_untouched')
handoff.require_retired(request['pair'])
ready = dict(schema='R166_C5_RETIRED_OWNER_RECOVERY_PREPARATION_V1',
    status='CPU_PREPARED_NO_GO_RETIRED_OWNER_EXECUTION_AUTHORITY_REQUIRED',
    request=saved.reference(output / 'REQUEST.json'), custody=saved.reference(output / 'RECOVERY_CUSTODY.json'),
    prepared=saved.reference(output / 'control/PREPARED.json'),
    source_manifest_sha256=saved.digest(inventory), config=prepared['config'], plan=prepared['plan'],
    proof=prepared['proof'], policy=prepared['policy'],
    subprocess=saved.reference(operator / 'C5_SUBPROCESS.json'),
    optimizer_steps=2478, cycle=28, boundary_index=2899, hard_end_unix=1789776000,
    ordinary_execute_requires_live_predecessor_and_must_not_be_used=True,
    no_GO=True, no_dispatch=True, no_reset=True, observed_unix=time.time())
saved.write(output / 'RECOVERY_READY.json', ready)
print(json.dumps(dict(ready=saved.reference(output / 'RECOVERY_READY.json'), document=ready), sort_keys=True))
