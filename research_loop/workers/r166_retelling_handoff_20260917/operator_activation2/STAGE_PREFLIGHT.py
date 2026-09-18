from pathlib import Path
from gpu import orch_r166_retelling_handoff as handoff
import json
import time

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_20260917_activation2')
targets = [
    ('C1', 2578597, '14835459', 'a98fbd127ccfa9924f564de2bdff6a09918e7508b365b8a211c225c32b154a7f'),
    ('C2', 2610332, '14878521', 'e044db79e92236e55bd5a1c9f7af20c9534cece79ed67f8a4f9a76da8b12bf7d'),
    ('C4', 2619696, '14891073', 'e3bb789135b16e80494088876c625f23905351cda703bc0201ba9c24f61838f6'),
    ('C5', 2578735, '14835679', 'c0ac95bfbddbb0bbc8ee79a85c81606ab4c990359401c125a8210958536e1cbf'),
]
for agent, pid, ticks, candidate_sha in targets:
    output = operator.parent / ('orch_r166_retelling_' + agent + '_20260917_activation2')
    try:
        assert handoff.saved.identity(pid)['start_ticks'] == ticks
        request = handoff.stage(agent, operator.parent / (
            'orch_r157_community_' + agent + '_20260917_attempt1/control/GUARD.json'),
            pid, operator / 'R150_DIRECTIVE.md', operator / 'CPU.json', output,
            scope_document=operator / 'R153_SCOPE.json', followup_directive=operator / 'R153_DIRECTIVE.md',
            addendum=operator / 'R154_ADDENDUM.md', candidate_request=operator.parent / (
                'orch_r166_retelling_' + agent + '_20260917_r154_attempt1/REQUEST.json'),
            candidate_sha256=candidate_sha)
        ready = handoff.preflight(output)
        receipt = dict(agent=agent, status='READY_CPU_PROVEN_NO_SIGNALS_NO_GO', request=request,
            ready=handoff.saved.reference(output / 'readiness/READY.json'),
            required_GO_binding=ready['required_GO_binding'], observed_unix=time.time())
    except Exception as error:
        receipt = dict(agent=agent, status='REFUSED_NO_RETRY', output=str(output),
            error_type=type(error).__name__, reason=str(error), observed_unix=time.time())
    handoff.saved.write(operator / (agent + '_PREPARATION.json'), receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
