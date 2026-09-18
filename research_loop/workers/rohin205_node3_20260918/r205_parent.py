"""Reference-bound sparse questions: three guided cycles, then withdrawal."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import time


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', type=Path, required=True)
    arm = parser.parse_args().arm
    plan = json.loads((arm / 'control/PLAN.json').read_bytes())
    reference = (arm.parent / 'PARENT_REFERENCE.md').read_bytes()
    reference_sha = hashlib.sha256(reference).hexdigest()
    if reference_sha != '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d':
        raise ValueError('clean_reference_changed')
    sys.path.insert(0, str(arm / 'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    receipts = arm / 'parent_receipts'
    receipts.mkdir(mode=0o700)
    initial = ('I am Astra. Lessons from a separate C2 conversation inform my questions, not your answers: '
        'compare competing explanations against concrete cases, distinguish a useful conjecture from proof, '
        'and revise a conclusion rather than merely agreeing with me. Choose a small question about counting, '
        'divisibility, or sums; define its objects, derive a claim from those definitions, and work two small cases. '
        'What counterexample would make you change your mind? Make a concrete mathematical attempt, not a plan '
        'to think forever. There is no connected code executor; never label reasoning as a sandbox result. '
        'I offer questions during the first three cycles, then withdraw for three. No peer exchange is active. ')
    if arm.name == 'frozen_c2':
        initial += 'Your inherited C2 adapter and its 4908 optimizer steps remain fixed; only context and own notes can change.'
    elif arm.name == 'fresh_math':
        initial += 'You are fresh Qwen with a new LoRA, not C2 and not a recipient of its past answers.'
    else:
        initial += 'You inherit fixed C2 checkpoint51 and its separate context5846 cut. The frozen base is unchanged; only your own new eligible words update LoRA.'
    if arm.name in ('peer_math', 'peer_repo'):
        initial = initial.replace('No peer exchange is active.', 'Source-bound peer carried state may arrive during THINK. Predict what transfers, then check a concrete case in your own task; only your own restatement may train.')
    if arm.name == 'peer_repo':
        source = arm / 'source/gpu/orch_r125_continual_native.py'
        text = source.read_text()
        function = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)
            and node.name == 'select_rehearsal_rows')
        excerpt = '\n'.join(text.splitlines()[function.lineno - 1:function.end_lineno])
        initial += (' Your paired environment is read-only repository reasoning, not an applied patch. '
            'Inspect this actual frozen select_rehearsal_rows excerpt. Predict its result for absent, zero, '
            'one, and invalid rehearsal_presentations; reason-check those cases and propose a focused test. '
            'No code execution is connected and no change is applied.\n\n```python\n' + excerpt + '\n```')
        write(receipts / 'REPO_SOURCE.json', dict(path=str(source),
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(), excerpt=excerpt, executed=False, applied=False))
    if arm.name == 'conversational':
        initial = ('I am Astra. This is your conversational branch from a fixed C2 snapshot, not the original live C2. '
            'Your genuine earlier Rohin messages remain attributed external inputs; no message from me is a Rohin turn. '
            'When Rohin writes, answer his actual question directly in your own words, keep your own conclusions, '
            'and ask when a distinction matters. You may disagree with reasons. Between turns, pursue your own '
            'inquiry without pretending a person replied. Your base stays frozen; eligible new own words may '
            'update LoRA. R206 carries actual Rohin input verbatim and masked across sleep and compaction. '
            'No code executor or peer is connected. I have the clean reference transcript as background and '
            'will not paste later original-C2 replies or impersonate Rohin. I now leave the console to actual turns.')
    start = 0 if arm.name == 'fresh_math' else 51
    published = set()
    seen = set()
    withdrawn = False
    if arm.name in ('peer_math', 'peer_repo'):
        (arm / 'peer_state').mkdir(mode=0o700)
    while time.time() < plan['hard_end_unix']:
        if (arm / 'control/EXIT.json').exists() or (arm / 'control/OUTER_FAILED.json').exists():
            return
        if (arm / 'raw/stream/inbox').is_dir() and 'birth' not in published:
            result = publish_parent(arm / 'raw', 'Astra', initial)
            write(receipts / 'INITIAL.json', dict(publication=result, observed_unix=time.time(),
                reference_sha256=reference_sha, reference_read_in_full=True, bulk_reference_copied=False,
                parent_kind='OPERATOR_AUTHORED_REFERENCE_BOUND_QUESTIONS_NOT_ADAPTIVE_MODEL', guided_cycles=3, withdrawn_cycles=3))
            published.add('birth')
            if arm.name == 'conversational':
                write(receipts / 'DIRECT_CONSOLE_HANDOFF.json', dict(observed_unix=time.time(),
                    automatic_followups=0, actual_Rohin_messages_only=True, reference_sha256=reference_sha))
                return
        for path in sorted((arm / 'raw/stream/records').glob('*.json'))[-80:]:
            if path.name.endswith('.intent.json') or path.name in seen:
                continue
            seen.add(path.name)
            with path.open('rb') as handle:
                handle.seek(max(0, path.stat().st_size - 8192))
                tail = handle.read()
            if b'"kind":"R184_LEARN_COMPLETE"' not in tail:
                continue
            record = json.loads(path.read_bytes())
            cycle = record['document']['cycle']
            if arm.name in ('peer_math', 'peer_repo'):
                write(arm / 'peer_state' / (str(cycle).zfill(6) + '.json'), record)
            if cycle >= start + 3 and not withdrawn:
                write(receipts / 'WITHDRAWN.json', dict(after_completed_cycle=cycle, observed_unix=time.time(),
                    pending_guidance=0, no_future_publications=True))
                withdrawn = True
                if arm.name not in ('peer_math', 'peer_repo'):
                    return
            if cycle in (start + 1, start + 2) and cycle not in published:
                question = ('Which step in your own last derivation needs justification, and which small case '
                    'could refute it? Separate what you calculated from what you have proved; choose one next attempt.'
                    if cycle == start + 1 else 'What did your last attempt actually establish? Preserve the useful '
                    'correction in your own words and try one changed case. I now withdraw; choose your next three attempts yourself.')
                result = publish_parent(arm / 'raw', 'Astra', question)
                write(receipts / ('AFTER_' + str(cycle) + '.json'), dict(publication=result,
                    observed_unix=time.time(), source_record_sha256=record['sha256'], reference_sha256=reference_sha))
                published.add(cycle)
        time.sleep(0.2)


if __name__ == '__main__':
    main()
