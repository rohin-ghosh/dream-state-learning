import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

BASE = Path('/localhome/local-rohing')
PRIOR = BASE / 'orch_r166_retelling_operator_20260917_activation4'
OPERATOR = BASE / 'orch_r166_retelling_operator_20260917_activation5'
PINS = {
    'gpu/orch_r166_retelling_handoff.py': '655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681',
    'tests/test_orch_r166_retelling_handoff.py': 'a6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660',
    'gpu/orch_r166_corrected_retelling.py': '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc',
    'tests/test_orch_r166_corrected_retelling.py': 'b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e',
}
TARGETS = [('C1', 2578597, '14835459', 'f3b52b3b48e877fe965073cf69ab689a561da7bbc9c7280254aa99bb0551ec1f'),
           ('C4', 2619696, '14891073', '66de6e831217b9e55f4eda78bfe0fcac37f5921e47ba7852eedcca7fc15f8730')]
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
for relative, expected in PINS.items():
    assert hashlib.sha256((PRIOR / 'source' / relative).read_bytes()).hexdigest() == expected
sys.path.insert(0, str(PRIOR / 'source'))
from gpu import orch_r166_retelling_handoff as handoff

assert not OPERATOR.exists()
diagnoses = []
for agent, pid, ticks, candidate_sha in TARGETS:
    prior = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation4')
    failure_path = prior / 'ACTIVATION_FAILED.json'
    assert handoff.saved.sha(failure_path) == '643dbc73532d49f1f361c838e7a30410dc799a04a6f0c29ee29a79659965272f'
    failure = handoff.saved.read(failure_path)
    assert failure['reason'] == 'no_boundary_old_native_left_running'
    assert not failure['termination_intent_recorded'] and not failure['original_exit_confirmed']
    assert not any((prior / name).exists() for name in ('TERMINATION_INTENT.json', 'OWNER_RETIRED.json', 'ACTUAL_BOUNDARY_READY.json', 'control'))
    request = handoff.saved.read(prior / 'REQUEST.json')
    for process in request['pair'].values():
        handoff.saved.same(process)
    assert handoff.saved.identity(pid)['start_ticks'] == ticks
    fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    assert fields[0] not in ('T', 't', 'Z', 'X')
    dispatch = handoff.saved.read(prior / 'MAIN_DISPATCH.json')
    assert not Path('/proc', str(dispatch['pid'])).exists()
    diagnoses.append(dict(agent=agent, failure=handoff.saved.reference(failure_path),
        failure_content=failure, original_pair=request['pair'], native_state=fields[0],
        no_pause_branch_reached=True, no_retirement=True, old_operator_absent=True,
        observed_unix=time.time(), exact_reason='600s without latest-record SLEEP_COMPLETE plus matching readout metadata; no historical-window replay'))
print(json.dumps(dict(status='TIMEOUT_ONLY_ORIGINALS_UNPAUSED', diagnoses=diagnoses)), flush=True)
OPERATOR.mkdir()
shutil.copytree(PRIOR / 'source', OPERATOR / 'source')
for name in ('CPU.json', 'R150_DIRECTIVE.md', 'R153_SCOPE.json', 'R153_DIRECTIVE.md', 'R154_ADDENDUM.md'):
    shutil.copyfile(PRIOR / name, OPERATOR / name)
    assert handoff.saved.sha(PRIOR / name) == handoff.saved.sha(OPERATOR / name)
    (OPERATOR / name).chmod(0o444)
assert handoff.saved.files(PRIOR / 'source') == handoff.saved.files(OPERATOR / 'source')
handoff.saved.write(OPERATOR / 'DIAGNOSIS.json', dict(diagnoses=diagnoses, source_pins=PINS))
for agent, pid, ticks, candidate_sha in TARGETS:
    output = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation5')
    request_ref = handoff.stage(agent, BASE / ('orch_r157_community_' + agent + '_20260917_attempt1/control/GUARD.json'),
        pid, OPERATOR / 'R150_DIRECTIVE.md', OPERATOR / 'CPU.json', output,
        scope_document=OPERATOR / 'R153_SCOPE.json', followup_directive=OPERATOR / 'R153_DIRECTIVE.md',
        addendum=OPERATOR / 'R154_ADDENDUM.md',
        candidate_request=BASE / ('orch_r166_retelling_' + agent + '_20260917_activation4/REQUEST.json'),
        candidate_sha256=candidate_sha)
    source = output / 'source'
    environment = handoff.saved.environment(source)
    assert environment['CUDA_VISIBLE_DEVICES'] == ''
    command = [str(handoff.saved.PYTHON), '-B', '-m', handoff.MODULE, 'preflight', '--output', str(output)]
    result = subprocess.run(command, cwd=source, env=environment, text=True, capture_output=True, timeout=240)
    handoff.saved.write(OPERATOR / (agent + '_SUBPROCESS.json'), dict(command=command, cwd=str(source),
        returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, observed_unix=time.time(),
        CUDA_VISIBLE_DEVICES=environment['CUDA_VISIBLE_DEVICES']))
    assert result.returncode == 0, result.stderr
    ready = json.loads(result.stdout)
    assert ready == handoff.saved.read(output / 'readiness/READY.json')
    staged = handoff.saved.read(output / 'REQUEST.json')
    for process in staged['pair'].values():
        handoff.saved.same(process)
    native_state = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[0]
    assert native_state not in ('T', 't', 'Z', 'X')
    receipt = dict(agent=agent, current_pair=staged['pair'], native_state=native_state,
        status='READY_ACTUAL_SUCCESSOR_SUBPROCESS_CPU_NO_SIGNALS_NO_GO', request=request_ref,
        ready=handoff.saved.reference(output / 'readiness/READY.json'), required_GO_binding=ready['required_GO_binding'],
        subprocess=handoff.saved.reference(OPERATOR / (agent + '_SUBPROCESS.json')), observed_unix=time.time())
    handoff.saved.write(OPERATOR / (agent + '_PREPARATION.json'), receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
