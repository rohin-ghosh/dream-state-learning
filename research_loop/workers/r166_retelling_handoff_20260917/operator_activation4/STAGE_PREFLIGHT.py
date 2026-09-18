from pathlib import Path
from gpu import orch_r166_retelling_handoff as handoff
import json
import subprocess
import time

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_20260917_activation4')
targets = [
    ('C1', 2578597, '14835459', '8f05b7b6c8ff2d16b131555caa562d39fb1e47f5c8829260117e4d70168a745b'),
    ('C2', 2610332, '14878521', '3869df77e9a2d862b4e16c84b47626fc0360696bf06b46dd0c80fd3bdb9a530c'),
    ('C4', 2619696, '14891073', '996876da3ddab29129481bf43dab60a27983f97549d430f0e8f221751d20054c'),
]
for agent, pid, ticks, candidate_sha in targets:
    output = operator.parent / ('orch_r166_retelling_' + agent + '_20260917_activation4')
    try:
        assert handoff.saved.identity(pid)['start_ticks'] == ticks
        request = handoff.stage(agent, operator.parent / (
            'orch_r157_community_' + agent + '_20260917_attempt1/control/GUARD.json'),
            pid, operator / 'R150_DIRECTIVE.md', operator / 'CPU.json', output,
            scope_document=operator / 'R153_SCOPE.json', followup_directive=operator / 'R153_DIRECTIVE.md',
            addendum=operator / 'R154_ADDENDUM.md', candidate_request=operator.parent / (
                'orch_r166_retelling_' + agent + '_20260917_activation3/REQUEST.json'),
            candidate_sha256=candidate_sha)
        source = output / 'source'
        environment = handoff.saved.environment(source)
        assert environment['CUDA_VISIBLE_DEVICES'] == ''
        command = [str(handoff.saved.PYTHON), '-B', '-m', handoff.MODULE,
                   'preflight', '--output', str(output)]
        result = subprocess.run(command, cwd=source, env=environment, text=True,
                                capture_output=True, timeout=240)
        handoff.saved.write(operator / (agent + '_SUBPROCESS.json'), dict(
            command=command, cwd=str(source), returncode=result.returncode,
            stdout=result.stdout, stderr=result.stderr, observed_unix=time.time(),
            CUDA_VISIBLE_DEVICES=environment['CUDA_VISIBLE_DEVICES']))
        assert result.returncode == 0, result.stderr
        ready = json.loads(result.stdout)
        assert ready == handoff.saved.read(output / 'readiness/READY.json')
        staged = handoff.saved.read(output / 'REQUEST.json')
        for process in staged['pair'].values():
            handoff.saved.same(process)
        native_state = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[0]
        assert native_state not in ('T', 't', 'Z', 'X')
        receipt = dict(current_pair=staged['pair'], native_state=native_state, agent=agent, status='READY_ACTUAL_SUCCESSOR_SUBPROCESS_CPU_NO_SIGNALS_NO_GO',
            request=request, ready=handoff.saved.reference(output / 'readiness/READY.json'),
            required_GO_binding=ready['required_GO_binding'],
            subprocess=handoff.saved.reference(operator / (agent + '_SUBPROCESS.json')),
            observed_unix=time.time())
    except Exception as error:
        staged = handoff.saved.read(output / 'REQUEST.json')
        for process in staged['pair'].values():
            handoff.saved.same(process)
        native_state = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[0]
        assert native_state not in ('T', 't', 'Z', 'X')
        receipt = dict(current_pair=staged['pair'], native_state=native_state, agent=agent, status='REFUSED_NO_RETRY', output=str(output),
            error_type=type(error).__name__, reason=str(error), observed_unix=time.time())
    handoff.saved.write(operator / (agent + '_PREPARATION.json'), receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
