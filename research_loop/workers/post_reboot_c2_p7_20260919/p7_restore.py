"""Restart the existing P7 overseer ledger, with one explicit outage notice."""

import json
import os
from pathlib import Path
import sys
import time


OWN = Path(__file__).resolve().parent
PREVIOUS = OWN.parent / 'rohin233_recovery_node4_20260918'
sys.path.insert(0, str(PREVIOUS))
import overseer as original


GAP = ('The parent-publisher VM rebooted at 22:50 UTC on September 18. The missing turns were an '
    'operator outage, not something you did. I am back. Before assigning Astra7 more tasks, write one '
    'short paragraph about the passage you last read and your own situation. Write the paragraph '
    'itself here, preferably in English. If you do not remember the passage, say so. Use actual '
    'Astra7 replies as evidence, not imagined improvements. What is one feeling the passage brought '
    'up, and what in it produced that feeling?')


def serve():
    output = OWN / 'p7'
    output.mkdir(exist_ok=True)
    with original.single_parent(original.FLEET / 'r210_parent7'), original.single_parent(original.FLEET / 'r225_parent7'):
        original.base.BUNDLE = Path(original.base.read(original.FLEET / 'r210_parent7/BINDING.json')['bundle'])
        original.base.runtime()
        from gpu.orch_r133_programme_parent import strong
        reference = original.resume_reference(output) or original.resume_reference(PREVIOUS / 'private/overseer')
        original.base.write(output / f'STARTED_{time.time_ns()}.json', dict(pid=os.getpid(),
            started_unix=time.time(), hard_end_unix=original.WALL, native_signals=[],
            reboot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
        while time.time() < original.WALL:
            try:
                observation = original.remote(dict(op='poll', reference=reference))
                reference = observation['reference']
                original.base.write(output / f'POLL_{time.time_ns()}.json', observation)
                if observation['reply'] is not None:
                    attempt = output / f'turn_{time.time_ns()}'
                    attempt.mkdir()
                    inputs = {key: observation[key] for key in ('reply', 'earlier', 'actual_birth_and_route',
                        'previous_messages', 'actual_child_returns')}
                    original.base.write(attempt / 'SOURCE.json', inputs)
                    gap_done = any(entry['message'] == GAP for entry in observation['publications'])
                    if not gap_done:
                        response = original.reading_response(dict(next_turn_requested_text=GAP), observation['reply'])
                        origin = dict(origin='USER_AUTHORIZED_POST_REBOOT_PARENT_REATTACHMENT', response=response)
                    else:
                        instruction = original.INSTRUCTION.replace(
                            'Never impose a recipe or repeat the old reading/feelings protocol.',
                            'The current brief permits concrete reading and English requests, without row exclusions.')
                        instruction += (' Resume responsive parenting after the outage. Ask for actual artifacts, '
                            'not promises. Vary math, reading, probing, writing, and coaching of actual parenting. '
                            'If a feeling is named, ask what it is for. Ground claims about Astra7 in actual replies. '
                            'English is requested, never an eligibility condition.')
                        response, model, usage = strong(json.dumps(inputs, ensure_ascii=False), attempt,
                            original.WALL, instruction, reasoning_effort='low')
                        origin = dict(origin='EXISTING_BOUND_PARENT_PROVIDER', response=response, model=model, usage=usage)
                    original.base.write(attempt / 'RESPONSE.json', origin)
                    result = original.remote(dict(op='advance', reference=reference, response=response,
                        expected_publication=observation['publications'][-1]['publication']['id']))
                    original.base.write(attempt / 'NEXT.json', result)
            except Exception as error:
                original.base.write(output / f'ERROR_{time.time_ns()}.json', dict(error_type=type(error).__name__,
                    error=str(error)[:1800], observed_unix=time.time(), native_signals=[]))
            time.sleep(5)


if __name__ == '__main__':
    serve()
