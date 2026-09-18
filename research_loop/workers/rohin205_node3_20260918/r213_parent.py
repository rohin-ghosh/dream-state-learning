"""In-cycle English parenting; never signals or changes a learner process."""

import argparse
import fcntl
import os
from pathlib import Path
import sys
import time

from r209_filter_resume import ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record
from r213_policy import ASSIGNMENTS, prompt


def main(name):
    arm = ROOT / name
    output = arm / 'r213_parent'
    output.mkdir(mode=0o700, exist_ok=True)
    lock = os.open(output / 'PUBLISHER.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    active_path = arm / 'ACTIVE_RUNTIME.json'
    active = read(active_path) if active_path.exists() else dict(source=str(arm / 'source'), control=str(arm / 'control'))
    control = Path(active['control'])
    source = Path(active['source'])
    plan = read(control / 'PLAN.json')
    require(plan['physical'] == ASSIGNMENTS[name][0], 'exact_assigned_GPU')
    require(sha(ROOT / 'PARENT_REFERENCE.md') == '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d',
        'clean_fixed_parent_reference')
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    from organism_v6.orch_r125_plain_context import has_scaffolding
    write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), assignment=ASSIGNMENTS[name],
        plan_sha256=sha(control / 'PLAN.json'), parent_reference_sha256=sha(ROOT / 'PARENT_REFERENCE.md'),
        reused_history=not name.startswith('r213_'), native_signals=0, automatic_restart=False,
        old_peer_topology_retained=not name.startswith('r213_')))
    turn, last_act, pending = 0, -1, None
    while time.time() < plan['hard_end_unix'] - 30:
        paths = [(path, metadata(path)) for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))]
        loaded_path = next((path for path, kind in reversed(paths) if kind == 'LOADED'), None)
        if loaded_path is None:
            time.sleep(1)
            continue
        loaded = read_record(loaded_path)
        native_pid = loaded['document']['pid']
        try:
            command = Path('/proc', str(native_pid), 'cmdline').read_bytes().split(b'\0')
            status = Path('/proc', str(native_pid), 'stat').read_text().rsplit(')', 1)[1].split()[0]
            live = str(control / 'GUARD.json').encode() in command and status not in ('Z', 'X')
        except FileNotFoundError:
            live = False
        if not live:
            break
        if pending is not None and not pending['rendered']:
            for path, kind in reversed(paths):
                if int(path.stem) <= pending['floor']:
                    break
                if kind != 'REQUEST':
                    continue
                request = read_record(path)
                if any(pending['text'] in item.get('content', '') for item in request['document']['messages']):
                    require(request['document']['render_receipt']['all_history_tokens_masked'], 'parent_context_only')
                    write(output / f'RENDERED_{pending["turn"]:03d}.json', dict(observed_unix=time.time(),
                        publication_id=pending['id'], request_index=request['index'], request_sha256=request['sha256'],
                        exact_text_rendered=True, all_history_tokens_masked=True, native_pid=native_pid))
                    pending['rendered'] = True
                    break
        latest_act = next((int(path.stem) for path, kind in reversed(paths) if kind == 'R184_ACT'), -1)
        if pending is None or pending['rendered'] and latest_act > last_act:
            text = prompt(name, turn)
            require(not has_scaffolding(text), 'existing_renderer_visible_parent')
            if turn == 0:
                write(output / 'PHASE_START.json', dict(observed_unix=time.time(), floor=int(paths[-1][0].stem),
                    native_pid=native_pid, plan_sha256=sha(control / 'PLAN.json'),
                    plasticity=plan.get('plasticity'), new_presentations=plan.get('new_presentations'),
                    historical_phases_preserved=True, fresh_matched_control_claim=False,
                    assignment=ASSIGNMENTS[name], native_signals=0,
                    peer_limit=('R213_GROUP_NATIVE_THINK_RECEIVER' if name.endswith('_fork') else
                        'OLD_R210_NATIVE_TOPOLOGY_NOT_RECONFIGURABLE_WITHOUT_RESTART'
                        if not name.startswith('r213_') else 'R213_TRIO_THINK_ONLY_RECEIVER')))
            publication = publish_parent(arm / 'raw', 'Astra', text)
            write(output / f'PUBLICATION_{turn:03d}.json', dict(observed_unix=time.time(), publication=publication,
                text=text, after_act_index=latest_act, native_pid=native_pid,
                English_ASCII_only=True, actual_render_pending=True))
            pending = dict(id=publication['id'], text=text, turn=turn, floor=int(paths[-1][0].stem), rendered=False)
            turn += 1
            last_act = latest_act
        time.sleep(2)
    write(output / 'EXIT.json', dict(observed_unix=time.time(), publications=turn,
        reason='existing_run_wall_or_native_no_longer_current', native_signals=0))
    os.close(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('arm', choices=tuple(ASSIGNMENTS))
    main(parser.parse_args().arm)
