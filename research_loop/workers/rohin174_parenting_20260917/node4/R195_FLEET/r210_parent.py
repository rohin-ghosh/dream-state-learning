"""Fresh R210 parent phase using existing frozen response validators and provider."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import parent_c as base
from parent_repairs import evidence_prompt, single_parent, tick_once


def remote(physical, request):
    command = '/localhome/local-rohing/v2/venv/bin/python -B ' + base.REMOTE.rsplit('/', 1)[0] + '/MATH_C/r210_parent_endpoint.py'
    result = subprocess.run(['bash', str(base.REPO / 'gpu/a40r_ssh.sh'), command],
        input=json.dumps(dict(request, physical=physical)), capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])
    return json.loads(result.stdout)


def prepare(physical):
    if physical == 7 and (base.OWN / 'R211_PARENT7_STOPPED.json').exists():
        raise ValueError('R211_isolation_parent_suspended')
    output = base.OWN / f'r210_parent{physical}'
    output.mkdir()
    previous = base.OWN / ('new_parent_C' if physical == 6 else f'parent_physical{physical}')
    config = base.read(previous / 'CONFIG.json')
    binding = (dict(bundle=str(base.BUNDLE), remote=base.REMOTE) if physical == 6
        else base.read(previous / 'BINDING.json'))
    reference = base.REPO / 'research_notes/analysis/ROHIN_C2_CONVERSATION_2026-09-17.md'
    assert base.sha(reference) == base.CLEAN_CONVERSATION_SHA
    programme = (
        'R210 is NEW ENRICHMENT after the completed guided52-54/withdrawn55-57 screen. '
        'All prior state and history are preserved; do not claim the same control continues. '
        'Respond to this child using its actual own evidence. Rohin is a genuine human inbox speaker; '
        'do not impersonate him, replay his words, or provide a parent answer as the child console reply. '
        'If stalled on inherited V, spend at most TWO delivered parent turns asking for the exact formula '
        'and the n=3 substitution in plain English, then verify the child calculation against an actual Tool receipt. '
        'After two failed turns explicitly set aside V as unresolved, retaining history, and invite a NEW object '
        'in the assigned environment. Do not claim a proposed Python calculation, repo_read, or LoRA change happened. '
        'Name a relevant fabrication once, then ask for evidence rather than repeatedly admonish. '
        'NFKC is glyph normalization, not syntax repair. Use own English prose. '
        'Only actual attributed peer turns count; no invented peer exchange, tool, captions or scorer. '
        'No private judge text, scores or sealed material. No new caption environment before Main bridge READY '
        'and factual scene/tool contract is delivered. Keep existing assigned environment for now. '
        'Separate scientific environment effects from parent-style claims. '
        + (previous / 'PROGRAMME.txt').read_text().split('Three guided')[0])
    if physical == 3:
        environment = base.read(base.OWN / 'caption_client/CHILD_ENVIRONMENT.json')
        programme = ('NEW R210 caption-game enrichment after the finished prior control. '
            'Only the following CHILD_ENVIRONMENT is available. No inherited mathematics, Python tasks, '
            'fake tools, references, private judge scores or original C2 story test. '
            'Support actual child caption actions and feedback. Actual feedback arrives synchronously before LEARN. '
            'Do not claim a judge result before its attributed tool receipt. '
            'This changes environment and is not the previous parent-style control. '
            'Use exact child RESPONSE evidence, keep own English prose, and do not fabricate tool/LoRA changes. '
            + json.dumps(environment, ensure_ascii=False))
    (output / 'PROGRAMME.txt').write_text(programme)
    (output / 'PRINCIPLES.txt').write_text('PRIVATE PARENT REFERENCE ONLY. Do not bulk-forward, replay the original C2 story test, '
        'or import later C2 answers. Use this teaching reference, not evaluator judgments.\n\n' + reference.read_text())
    config.update(source_root=binding['remote'] + '/r210/source', branch='R210_' + config['branch'],
        programme_path=str(output / 'PROGRAMME.txt'), programme_sha256=base.sha(output / 'PROGRAMME.txt'),
        principles_path=str(output / 'PRINCIPLES.txt'), principles_sha256=base.sha(output / 'PRINCIPLES.txt'))
    base.write(output / 'CONFIG.json', config)
    base.write(output / 'BINDING.json', binding)
    base.BUNDLE = Path(binding['bundle'])
    base.runtime().validate(config)


def serve(physical):
    if physical == 7 and (base.OWN / 'R211_PARENT7_STOPPED.json').exists():
        raise ValueError('R211_isolation_parent_suspended')
    output = base.OWN / f'r210_parent{physical}'
    with single_parent(output):
        config = base.read(output / 'CONFIG.json')
        binding = base.read(output / 'BINDING.json')
        base.BUNDLE = Path(binding['bundle'])
        base.remote = lambda request: remote(physical, request)
        policy = base.runtime()
        original_prompt = policy.prompt

        def precise_prompt(*arguments, **keywords):
            instruction, payload = original_prompt(*arguments, **keywords)
            return evidence_prompt(instruction, payload, arguments[1])

        policy.prompt = precise_prompt
        attempts = output / 'turns'
        attempts.mkdir(exist_ok=True)
        base.write(output / f'STARTED_{time.time_ns()}.json', dict(pid=os.getpid(), started_unix=time.time(),
            physical=physical, config_sha256=base.sha(output / 'CONFIG.json'), phase='R210_ENRICHMENT'))
        reference = None
        seed = base.read(output / 'SEED.json') if (output / 'SEED.json').exists() else None
        while time.time() < base.WALL:
            observation = remote(physical, dict(op='poll', reference=reference))
            reference = observation['reference']
            state = observation['snapshot']
            if observation['receipts']:
                base.write(output / f'OBSERVED_{time.time_ns()}.json', dict(receipts=observation['receipts'],
                    opening_rendered=observation['opening_rendered'], observed_unix=time.time()))
            loaded = any(entry['kind'] == 'LOADED' for entry in observation['receipts'])
            if loaded and (physical != 7 or observation['console_replied']) and not observation['opening_published']:
                message = ("I am Astra, your attached parent in a NEW R210 enrichment phase. The earlier guided and withdrawn "
                    "screen has ended; your state and history remain. Rohin's inbox is genuine human input; my turn is separate. "
                    "I am here now. If V remains your live uncertainty, what exact formula and n=3 substitution can you state "
                    "in plain English before trying the real Python tool? We will spend at most two turns on that, then keep "
                    "it as unresolved history and choose a NEW object in your assigned environment. Only actual tool feedback counts.")
                publication = remote(physical, dict(op='opening', message=message))
                base.write(output / 'OPENING.json', dict(publication=publication, observed_unix=time.time(),
                    operator_intro_not_model_response=True))
            if observation['opening_rendered'] and state['caught_up']:
                if seed is None:
                    seed = dict(schema='R166_PARENT_SUCCESSOR_V1', journal_id=state['journal_id'], attempts=[],
                        object_delivered_turns={}, last_response_count=state['response_count'],
                        last_request_count=state['request_count'], prospective_request_count=state['request_count'],
                        credits={}, grammar_delivered=False)
                    base.write(output / 'SEED.json', seed)
                status = tick_once(policy, base.REPO, config, attempts, seed, state)
                if status['status'] not in ('WAITING_FOR_NEW_CHILD_BOUNDARY', 'EXISTING_BOUNDARY_ATTEMPT_PRESERVED'):
                    base.write(output / f'STATUS_{time.time_ns()}.json', status)
            time.sleep(4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'serve'))
    parser.add_argument('--physical', type=int, choices=(2, 3, 5, 6, 7), required=True)
    options = parser.parse_args()
    globals()[options.action](options.physical)
