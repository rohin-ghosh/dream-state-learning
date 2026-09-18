from pathlib import Path
from gpu import orch_r166_retelling_handoff as handoff
import json
import time

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_20260917_r154')
results = {}
for agent, pid, ticks in [('C1', 2578597, '14835459'), ('C2', 2610332, '14878521'),
                          ('C3', 2525436, '14761894'), ('C4', 2619696, '14891073'),
                          ('C5', 2578735, '14835679')]:
    output = operator.parent / ('orch_r166_retelling_' + agent + '_20260917_r154_attempt1')
    try:
        assert handoff.saved.identity(pid)['start_ticks'] == ticks
        reference = handoff.stage(agent, operator.parent / (
            'orch_r157_community_' + agent + '_20260917_attempt1/control/GUARD.json'),
            pid, operator / 'R150_DIRECTIVE.md', operator / 'CPU.json', output,
            scope_document=operator / 'R153_SCOPE.json', followup_directive=operator / 'R153_DIRECTIVE.md',
            addendum=operator / 'R154_ADDENDUM.md')
        request, config, plan = handoff.verify_request(output)
        for process in request['pair'].values():
            handoff.saved.same(process)
        results[agent] = dict(status='STAGED_VERIFIED_ORIGINAL_OWNER_ALIVE', request=reference,
            source_root=request['source_root'], source_files=len(request['source_files']),
            source_manifest_sha256=handoff.saved.digest(request['source_files']),
            native_sha256=request['source_files'][handoff.NATIVE_RELATIVE],
            policy_sha256=request['source_files'][handoff.POLICY_RELATIVE],
            actor=request['pair']['actor'], followup=request['followup'], addendum=request['addendum'],
            no_stop=True, no_GO=True, output=str(output))
    except Exception as error:
        results[agent] = dict(status='REFUSED_NO_RETRY', error_type=type(error).__name__,
            reason=str(error), output_exists=output.exists(), output=str(output))
receipt = dict(observed_unix=time.time(), results=results, scope='NEW_ISOLATED_SOURCE_ONLY')
handoff.saved.write(operator / 'STAGING_RESULTS.json', receipt)
print(json.dumps(receipt, sort_keys=True, indent=2))
