"""English-only parenting through ordinary inbox delivery, never model control."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

from r209_filter_resume import ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record


ARMS = ('conversational', 'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3')
OBJECTS = {
    'conversational': (
        'Conversation homework: in three English sentences, identify one observation from an actual conversation, one uncertainty, and one question you would ask. Do not invent a human reply. If there is no new human message, say so and complete this homework.',
        'Conversation homework: revise one of your three sentences so observation and inference are separate. Explain the change briefly and ask one genuine question. No formulas or code.',
        'Conversation homework: describe one everyday observation in two sentences and give two possible explanations. Keep the distinction between observation and guess clear.'),
    'peer_math': (
        'New finite-list object: compare the lists [1, 2, 3, 4] and [1, 2, 3, 8]. Name the first position that differs and count the positions that agree. Stop there; no inherited formula or universal-rule claim.',
        'New ordering object: write two different orders of a red token, a blue token and a green token. State which two positions changed. Work only with these three tokens.'),
    'peer_repo': (
        "New source-reading object: the supplied exact line reads row['target']. Does that expression read the target or the external prefix? Compare an English target with non-English external context against a non-English target. Propose two cases; do not claim tests ran.",
        'New source-reading object: write two test names in English, one for keeping an English own target and one for a non-English own target. Explain the expected behavior using the supplied actual source line, without executing or editing anything.'),
    'p32': (
        'New tiny object: there are two tokens, one red and one blue. Write one complete English sentence naming the color of the first token. A fragment is not a completed answer; do not return to the previous algebra task.',
        'New tiny object: a box is empty and a cup contains one bead. Write one complete English sentence saying which object contains the bead. Do not add a formula or code.'),
    'lr03': (
        'New branch-reading object: for the actual supplied function and old rows [one, two], describe what happens when the presentation setting is absent, zero, and one. Give one short English sentence per case; no execution claim.',
        'New branch-reading object: what does the supplied validation do with a presentation setting of two? Distinguish a rejected input from returning an empty list. This is source reasoning, not a test run.'),
    'lr3': (
        'New creative object: write a complete three-paragraph story, one sentence per paragraph. An agent chooses an action, notices an unexpected observation, then changes its next action. No algebra or code; leave whether the agent is alive or pattern-driven open.',
        'New creative revision: rewrite the whole three-paragraph miniature, changing the observation and the resulting action. Name the change in one short English sentence. Do not append another section or claim human review.'),
}


def prompt(name, turn, repeated_algebra=False, excerpt=''):
    task = OBJECTS[name][(turn // 2) % len(OBJECTS[name])]
    text = ('Astra, not Rohin. R212 parent feedback during ordinary running cycles. '
        'The two-turn intervention on the inherited algebra task is over; do not extend it or restate its formula. '
        'Leave that unresolved history unchanged. ')
    if repeated_algebra:
        text += 'Your latest actual output returned to that old task instead of the new object. Change tasks now; do not repeat the old claim as a solution. '
    text += task + ' '
    if excerpt:
        text += 'Actual pinned source excerpt, not execution:\n```python\n' + excerpt + '\n```\n'
    text += ('Choose your own brief periodic LANGUAGE CHECK: inspect one new sentence for unwanted script, missing spaces or repeated fragments, then return to this task. '
        'Use English for your own new prose. The filter is a backstop, not feedback or proof of correctness. '
        'Do not translate or rewrite historical targets. No code executor is connected. Keep your learning settings unchanged. ')
    if name == 'conversational':
        text += ('A genuine new Rohin question takes priority over homework: answer it directly in the normal console ACT path, without waiting for sleep or a parent. '
            'I am not supplying a Rohin message. Between actual human messages, use normal THINK to prepare and normal ACT to deliver the homework; LEARN records your own reflection. '
            'Do not pretend a person replied or read your work.')
    require(text.isascii(), 'R212_parent_English_ASCII_only')
    return text


def main(name):
    arm = ROOT / name
    output = arm / 'r212_parent'
    output.mkdir(mode=0o700)
    lock = os.open(output / 'PUBLISHER.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source = Path(read(arm / 'ACTIVE_RUNTIME.json')['source'])
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    from organism_v6.orch_r125_plain_context import has_scaffolding
    plan = read(Path(read(arm / 'ACTIVE_RUNTIME.json')['control']) / 'PLAN.json')
    excerpt = ''
    if name == 'peer_repo':
        path = source / 'organism_v6/orch_r203_prose_target_filter.py'
        excerpt = next(line for line in path.read_text().splitlines() if "evidence = scan_target(row['target'])" in line)
        write(output / 'SOURCE.json', dict(path=str(path), sha256=sha(path), exact_excerpt=excerpt))
    elif name == 'lr03':
        import ast
        path = source / 'gpu/orch_r125_continual_native.py'
        original = path.read_text()
        function = next(item for item in ast.parse(original).body if isinstance(item, ast.FunctionDef)
            and item.name == 'select_rehearsal_rows')
        excerpt = ast.get_source_segment(original, function)
        write(output / 'SOURCE.json', dict(path=str(path), sha256=sha(path), exact_excerpt=excerpt))
    write(output / 'STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
        max_parent_turns_per_object=2, cadence='FIRST_NORMAL_REQUEST_THEN_AT_MOST_ONCE_PER_NEW_ACT_AFTER_RENDER',
        source_root=str(source), no_runtime_signals=True, no_native_changes=True, parents_English_only=True))
    pending, last_act, turn = None, -1, 0
    while time.time() < plan['hard_end_unix'] - 60:
        paths = [(path, metadata(path)) for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))]
        loaded = read_record(next(path for path, kind in reversed(paths) if kind == 'LOADED'))
        control = Path(read(arm / 'ACTIVE_RUNTIME.json')['control'])
        try:
            command = Path('/proc', str(loaded['document']['pid']), 'cmdline').read_bytes().split(b'\0')
            live = str(control / 'GUARD.json').encode() in command
        except FileNotFoundError:
            live = False
        acts = [path for path, kind in paths if kind == 'R184_ACT']
        latest_act = int(acts[-1].stem) if acts else -1
        if pending is not None and not pending['rendered']:
            for path, kind in reversed(paths):
                if int(path.stem) <= pending['after_index']:
                    break
                if kind != 'REQUEST':
                    continue
                request = read_record(path)
                if any(pending['text'] in item.get('content', '') for item in request['document']['messages']):
                    require(request['document']['render_receipt']['all_history_tokens_masked'], 'parent_context_only')
                    write(output / ('RENDERED_' + pending['id'] + '.json'), dict(observed_unix=time.time(),
                        publication_id=pending['id'], request_index=request['index'], request_sha256=request['sha256'],
                        exact_text_rendered=True, all_history_tokens_masked=True))
                    pending['rendered'] = True
                    break
        if live and (pending is None or pending['rendered'] and latest_act > last_act):
            response_path = next(path for path, kind in reversed(paths) if kind == 'RESPONSE')
            response = read_record(response_path)
            raw = response['document']['response']['raw']
            repeated = bool(re.search(r'\bV\b|S_[n1-9]|sympy|17\.397', raw, re.IGNORECASE))
            text = prompt(name, turn, repeated, excerpt)
            require(not has_scaffolding(text), 'parent_prompt_visible_under_existing_renderer')
            publication = publish_parent(arm / 'raw', 'Astra', text)
            write(output / f'PUBLICATION_{turn:03d}.json', dict(observed_unix=time.time(), text=text,
                publication=publication, after_act_index=latest_act, source_response_index=response['index'],
                source_response_sha256=response['sha256'], actual_output_algebra_marker=repeated,
                object=OBJECTS[name][(turn // 2) % len(OBJECTS[name])], object_attempt=turn % 2 + 1,
                operator_authored=True, English_ASCII_only=True, native_pid=loaded['document']['pid']))
            pending = dict(id=publication['id'], text=text, rendered=False, after_index=int(paths[-1][0].stem))
            turn += 1
            last_act = latest_act
        time.sleep(3)
    os.close(lock)
    write(output / 'EXIT.json', dict(observed_unix=time.time(), reason='existing_wall', publications=turn))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('arm', choices=ARMS)
    main(parser.parse_args().arm)
