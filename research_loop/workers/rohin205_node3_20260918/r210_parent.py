"""Source-bound operator-authored R210 parenting; never impersonate Rohin."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

from r209_node3_audit import metadata, read_record


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
ARMS = ('conversational', 'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3')
REFERENCE = '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'
PHASE = 'R210_PARENTED_COMPLEMENTARY_EXPERIENCE'
FORMULA = ('Your inherited candidate is S_n = n(n+1)(2n+1)(3n^2+Vn-1)/30. '
    'First state whether S_n means the sum of fourth powers. If so, work n=3 in ordinary prose: '
    'compare 1^4+2^4+3^4 with the candidate after substituting n=3, retaining every factor, '
    'and solve the resulting equation for V. Verify separately at n=2. '
    'A code block or assertion that it ran is not verification: this life has no connected executor. '
    'After two guided attempts, move to the new environment object even if V remains unresolved; '
    'preserve that uncertainty rather than claiming success.')


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def new_object(name):
    if name in ('conversational', 'lr3'):
        return ('New object R210_CREATIVE_REDRAFT: author one complete three-paragraph story about a learning '
            'agent encountering an observation that changes its next choice. Each iteration is a full redraft, '
            'not another section. Relate it to your own learning and another learning agent; leave the '
            'alive-versus-pattern-driven interpretation open. Pick one substantive revision and explain what '
            'changed. This is Astra\'s feedback, not a new Rohin message or a claim of human review; you may disagree.')
    if name == 'peer_repo':
        return ('New object R210_REPO_PREFIX_VS_TARGET: trace the supplied real prose_exclusions function. '
            'Would CJK text in external prefix alone exclude an English own target? Contrast that with CJK in '
            'the annotated own target. Cite the exact read path and propose two tests. This is pinned-source '
            'reasoning only, not repository execution, an applied patch, or a passing test receipt.')
    if name == 'lr03':
        return ('New object R210_REPO_REHEARSAL_BRANCH: trace the supplied real select_rehearsal_rows function. '
            'Contrast absent, zero and positive rehearsal budgets on a tiny explicit list. Name one invariant '
            'and one counterexample candidate. Only the excerpt is available: no live repository tool, '
            'code executor, applied patch or passing-test claim is justified.')
    return ('New object R210_MATH_DIFFERENCES: compare two tiny integer sequences that agree on three terms '
        'but differ on a fourth. Define both rules, work the fourth term, and state why three observations '
        'alone do not prove a universal rule. Use your own prose reasoning; no sandbox or scientific '
        'verification receipt exists. Contrast your reasoning experience with peers\' repository or creative work.')


def main(name):
    arm = ROOT / name
    output = arm / 'r210_parent'
    output.mkdir(mode=0o700)
    reference = (ROOT / 'PARENT_REFERENCE.md').read_bytes()
    if hashlib.sha256(reference).hexdigest() != REFERENCE:
        raise ValueError('exact_clean_parent_reference')
    plan = json.loads((arm / 'control/PLAN.json').read_bytes())
    sys.path.insert(0, str(arm / 'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    excerpt = ''
    if name in ('peer_repo', 'lr03'):
        relative, function = ('organism_v6/orch_r203_prose_target_filter.py', 'prose_exclusions') if name == 'peer_repo' else ('gpu/orch_r125_continual_native.py', 'select_rehearsal_rows')
        source = arm / 'r210_enrichment/source' / relative
        text = source.read_text()
        node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == function)
        excerpt = ast.get_source_segment(text, node)
        write(output / 'PINNED_SOURCE.json', dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            function=function, excerpt=excerpt, executed=False, applied=False))
        excerpt = '\n\nActual pinned source, not execution:\n```python\n' + excerpt + '\n```'
    write(output / 'STARTED.json', dict(pid=__import__('os').getpid(), observed_unix=time.time(), phase=PHASE,
        operator_authored_not_adaptive_parent_model=True, reference_sha256=REFERENCE,
        previous_phase_artifacts_untouched=True, no_withdrawn_control_claim_after_first_delivery=True,
        no_human_impersonation=True, new_object=new_object(name)))
    pending = None
    turn = 0
    last_act = -1
    intervention = False
    rendered = set()
    seen_requests = set()
    while time.time() < plan['hard_end_unix'] - 60:
        paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        loaded = next((read_record(path) for path in reversed(paths) if metadata(path) == 'LOADED'), None)
        active = json.loads((arm / 'ACTIVE_RUNTIME.json').read_bytes()) if (arm / 'ACTIVE_RUNTIME.json').exists() else dict(control=str(arm / 'control'))
        live = False
        if loaded is not None:
            try:
                live = str(Path(active['control']) / 'GUARD.json').encode() in Path('/proc', str(loaded['document']['pid']), 'cmdline').read_bytes().split(b'\0')
            except FileNotFoundError:
                pass
        act_paths = [path for path in paths if metadata(path) == 'R184_ACT']
        current_act = int(act_paths[-1].stem) if act_paths else -1
        for path in paths[-100:]:
            if path.name in seen_requests or metadata(path) != 'REQUEST':
                continue
            seen_requests.add(path.name)
            if pending is None or pending['id'] in rendered:
                continue
            request = read_record(path)
            document = request['document']
            if any(pending['text'] in message.get('content', '') for message in document['messages']):
                if not document['render_receipt']['all_history_tokens_masked']:
                    raise ValueError('parent_prefix_must_be_masked')
                write(output / ('RENDERED_' + pending['id'] + '.json'), dict(observed_unix=time.time(),
                    phase=PHASE, request_index=request['index'], request_sha256=request['sha256'],
                    publication_id=pending['id'], exact_text_rendered=True, all_history_tokens_masked=True))
                rendered.add(pending['id'])
        if live and (pending is None or pending['id'] in rendered and current_act > last_act):
            recent = [read_record(path) for path in reversed(paths) if metadata(path) == 'RESPONSE'][:2]
            if turn == 0:
                intervention = len(recent) == 2 and all('V' in item['document']['response']['raw'] for item in recent)
                text = ('I am Astra, not Rohin. This delivery begins explicit R210 parented enrichment. '
                    'Earlier guided/withdrawn results remain historical; this is no longer a parent-withdrawn '
                    'condition. Keep your current presentation counts, learning rate and anchor unchanged. '
                    'Use English for new self-authored prose; do not translate or rewrite historical raw targets. ')
                text += FORMULA if intervention else new_object(name) + excerpt
            elif intervention and turn == 1:
                text = ('Astra, R210 guided verification attempt two: show the actual n=3 arithmetic and an '
                    'independent n=2 substitution in prose. State which equality holds or fails. The runtime '
                    'reports no connected executor, so do not say a program ran. If this remains unresolved, '
                    'retain that uncertainty; my next turn moves us to a new working object.')
            elif intervention and turn == 2:
                text = 'Astra, R210: two guided attempts are enough; do not continue V by repetition or claim success without evidence. ' + new_object(name) + excerpt
            else:
                text = ('Astra, R210: for your new object, what did your last actual output establish, what '
                    'remains unresolved, and what one revision or manual check would change your next action? '
                    'Distinguish your observation from a peer assertion and from real tool execution. '
                    'Keep the historical V note separate; do not restart that loop.')
            publication = publish_parent(arm / 'raw', 'Astra', text)
            write(output / f'PUBLICATION_{turn:03d}.json', dict(observed_unix=time.time(), phase=PHASE,
                publication=publication, text=text, after_act_index=current_act, native_pid=loaded['document']['pid'],
                basis_responses=[dict(index=item['index'], sha256=item['sha256']) for item in recent],
                V_two_turn_intervention=intervention and turn < 2, new_object=new_object(name),
                source_bound=True, rendered=False, scientific_verification_claimed=False))
            pending = dict(id=publication['id'], text=text)
            last_act = current_act
            turn += 1
        time.sleep(2)
    write(output / 'EXIT.json', dict(observed_unix=time.time(), publications=turn,
        rendered_publications=len(rendered), reason='existing_runtime_wall'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('arm', choices=ARMS)
    main(parser.parse_args().arm)
