"""Single existing-ledger P7 overseer with an explicit one-turn reading repair."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from lease_horizon import cpu_horizon


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
FLEET = REPO / 'research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET'
WALL = cpu_horizon()
sys.path.insert(0, str(FLEET))
import parent_c as base
from parent_repairs import single_parent
from r225_parent import resume_reference
from r229_overseer import INSTRUCTION


def reading_response(brief, reply):
    return dict(speak=True, message=brief['next_turn_requested_text'], rationale=json.dumps(dict(
        latest=dict(record_index=reply['record_index'], record_sha256=reply['record_sha256'], quote=reply['text'][:160]),
        comparison='Operator-authorized released reading object and English artifact request, not a model-authored '
        'claim. Earlier real replies remain real; the expired route and unsupported improvements are qualified. '
        'No feelings or answer supplied; no change to learner eligibility.')))


def remote(request):
    command = '/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r233_p7_recovery_20260918/renewed/p7_endpoint.py'
    result = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command], input=json.dumps(request),
        capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    return json.loads(result.stdout)


def serve():
    output = OWN / 'private/overseer'
    output.mkdir(exist_ok=True)
    with single_parent(FLEET / 'r210_parent7'), single_parent(FLEET / 'r225_parent7'):
        base.BUNDLE = Path(base.read(FLEET / 'r210_parent7/BINDING.json')['bundle'])
        base.runtime()
        from gpu.orch_r133_programme_parent import strong
        reference = resume_reference(output) or resume_reference(FLEET / 'r229_parent7')
        base.write(output / f'STARTED_{time.time_ns()}.json', dict(pid=os.getpid(), hard_end_unix=WALL,
            native_signals=[], source_path=__file__, existing_ledger=True))
        while time.time() < WALL:
            try:
                observation = remote(dict(op='poll', reference=reference))
                reference = observation['reference']
                base.write(output / f'POLL_{time.time_ns()}.json', observation)
                if observation['reply'] is not None:
                    attempt = output / f'turn_{time.time_ns()}'
                    attempt.mkdir()
                    inputs = {key: observation[key] for key in ('reply', 'earlier', 'actual_birth_and_route',
                        'previous_messages', 'actual_child_returns')}
                    base.write(attempt / 'SOURCE.json', inputs)
                    brief = base.read(OWN / 'BRIEF.json')
                    first_done = any(entry['message'] == brief['next_turn_requested_text']
                        for entry in observation['publications'])
                    if not first_done:
                        response = reading_response(brief, observation['reply'])
                        origin = dict(origin='OPERATOR_AUTHORIZED_RELEASED_READING_NOT_MODEL_GENERATED', response=response)
                    else:
                        instruction = INSTRUCTION.replace('Never impose a recipe or repeat the old reading/feelings protocol.',
                            'The latest R233 brief authorizes concrete reading and English requests, not a rote therapy protocol.')
                        instruction += (' Follow the R233 recovery brief over earlier curriculum preferences. Ask for a real '
                            'artifact, not a promised plan. Keep subsequent turns varied. Treat returned child replies as '
                            'historical until a current receiver is verified. English is a request, never a training exclusion.')
                        response, model, usage = strong(json.dumps(inputs, ensure_ascii=False), attempt,
                            WALL, instruction, reasoning_effort='low')
                        origin = dict(origin='EXISTING_BOUND_PARENT_PROVIDER', response=response, model=model, usage=usage)
                    base.write(attempt / 'RESPONSE.json', origin)
                    result = remote(dict(op='advance', reference=reference, response=response,
                        expected_publication=observation['publications'][-1]['publication']['id']))
                    base.write(attempt / 'NEXT.json', result)
            except Exception as error:
                base.write(output / f'ERROR_{time.time_ns()}.json', dict(error_type=type(error).__name__,
                    error=str(error)[:1800], observed_unix=time.time(), native_signals=[]))
            time.sleep(5)


if __name__ == '__main__':
    serve()
