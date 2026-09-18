from pathlib import Path
from gpu import orch_r166_retelling_handoff as handoff
import json
import subprocess
import time

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_20260917_activation3')
targets = [
    ('C1', 2578597, '14835459', 'b72eb9477226a44f34ee0c14dc6ed24d50deafa8d49df7afcdd70b0d8b35d5d6'),
    ('C2', 2610332, '14878521', '0b453e18ced670fafb7aa24280c74df2231a4ba4b84920b4c7ee9bbc5a8b138a'),
    ('C4', 2619696, '14891073', '94b55e16db1fea8de4af96ce66987b762746280d32b7a49dc6c2a2876661af94'),
    ('C5', 2578735, '14835679', '10019c8d0fabf1ea69f55b1c5bcb1c652743afc68ea6da48221e44286ae74bbf'),
]
for agent, pid, ticks, candidate_sha in targets:
    output = operator.parent / ('orch_r166_retelling_' + agent + '_20260917_activation3')
    try:
        assert handoff.saved.identity(pid)['start_ticks'] == ticks
        request = handoff.stage(agent, operator.parent / (
            'orch_r157_community_' + agent + '_20260917_attempt1/control/GUARD.json'),
            pid, operator / 'R150_DIRECTIVE.md', operator / 'CPU.json', output,
            scope_document=operator / 'R153_SCOPE.json', followup_directive=operator / 'R153_DIRECTIVE.md',
            addendum=operator / 'R154_ADDENDUM.md', candidate_request=operator.parent / (
                'orch_r166_retelling_' + agent + '_20260917_activation2/REQUEST.json'),
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
        receipt = dict(agent=agent, status='READY_ACTUAL_SUCCESSOR_SUBPROCESS_CPU_NO_SIGNALS_NO_GO',
            request=request, ready=handoff.saved.reference(output / 'readiness/READY.json'),
            required_GO_binding=ready['required_GO_binding'],
            subprocess=handoff.saved.reference(operator / (agent + '_SUBPROCESS.json')),
            observed_unix=time.time())
    except Exception as error:
        receipt = dict(agent=agent, status='REFUSED_NO_RETRY', output=str(output),
            error_type=type(error).__name__, reason=str(error), observed_unix=time.time())
    handoff.saved.write(operator / (agent + '_PREPARATION.json'), receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
