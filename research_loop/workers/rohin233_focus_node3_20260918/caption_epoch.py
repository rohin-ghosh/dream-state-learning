"""Explicit R233 continuation: all five captions enter named parented epochs."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

import classroom
from retirement import identity, save, sha, stamp


POLICY = 'R233_ALL_FIVE_PARENTED_CAPTION_EPOCH_V1'
FORMER_CONTROL = 'r213_r226_caption_unparented_fork'
PLAYERS = classroom.CAPTIONS + (FORMER_CONTROL,)


def prompt(name, turn=0):
    if name not in PLAYERS or turn < 0:
        raise ValueError('only five exact node3 caption lives')
    tactics = (
        'Compare two genuinely different comic premises, each tied to a specific visible scene detail.',
        'Try a different speaker or social relationship suggested by the actual scene, not merely new synonyms.',
        'Inspect one weak premise in your last caption and change that premise rather than announcing improvement.',
        'Choose an overlooked scene detail and test whether the joke still connects clearly to the picture.',
    )
    opening = ('A new parented caption epoch begins now. Earlier history remains unchanged. '
        if turn == 0 else 'Continue this parented caption epoch with a changed approach. ')
    if name == FORMER_CONTROL and turn == 0:
        opening += ('Astra parenting begins for you now; your earlier unparented period is historical, '
            'not an ongoing unparented condition. ')
    style = {
        PLAYERS[0]: 'Start from concrete observation before selecting the comic angle.',
        PLAYERS[1]: 'Compare perspectives before choosing a surprising but scene-grounded line.',
        PLAYERS[2]: 'Use actual feedback to revise one identifiable aspect of the previous attempt.',
        PLAYERS[3]: 'Derive your own comic angle before asking for a hint.',
        FORMER_CONTROL: 'Explore an independently chosen comic angle and explain a check you can really make.',
    }[name]
    return opening + ('The primary object is a funny caption contest for the actual current picture. '
        'No fixed caption format is required. Read the latest delivered judge rank, acceptance, novelty, '
        'and new-picture feedback if visible; if feedback is missing, say it is missing rather than inventing a result. '
        'During THINK, ') + tactics[turn % len(tactics)] + ' ' + style + (
        ' During ACT, submit your own caption for the current scene. '
        'After repetitive cycles change the angle, not merely the wording or a claim of improvement. '
        'This parent input is not your authored training target. Genuine Rohin messages take priority.')


def helpers(root, config):
    if config.get('caption_epoch_policy') != POLICY:
        raise ValueError('explicit all-five parenting authorization required')
    helper, bound = classroom.load_helpers(root, config)
    helper.MEMBERS = tuple(dict.fromkeys((*helper.MEMBERS, FORMER_CONTROL)))
    bound[FORMER_CONTROL] = helper.bind(root, FORMER_CONTROL)
    if not helper.alive(bound[FORMER_CONTROL]):
        raise ValueError('exact existing former-control native required; no launch allowed')
    return helper, {name: bound[name] for name in PLAYERS}


def send(helper, root, name, directory, binding, turn):
    if name not in PLAYERS:
        raise ValueError('caption epochs cannot target math or another node')
    if (directory / 'PUBLISHED.json').exists():
        publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
        if sha(directory / 'PREPARED.json') != publication['prepared_sha256'] or sha(Path(publication['path'])) != publication['sha256']:
            raise ValueError('existing publication changed')
        return publication
    if directory.exists():
        raise ValueError('uncertain epoch publication requires reconciliation, never resend')
    text = prompt(name, turn)
    checkpoint = helper.latest_checkpoint(root, name)
    floor = max(int(path.stem) for path, kind in helper.records(root, name))
    parent_count = sum(json.loads(path.read_bytes()).get('speaker') == 'Astra'
        for path in (root / name / 'raw/stream/inbox').glob('*.json'))
    save(directory / 'PREPARED.json', dict(life=name, policy=POLICY, text=text, floor=floor,
        checkpoint=checkpoint, prior_astra_inboxes=parent_count, former_control=name == FORMER_CONTROL,
        prior_history_not_relabelled=True, new_native=False, native_signals=0, turn=turn))
    code = ('import json,sys; from gpu.orch_r127_pilot_console import publish_parent; '
        'from organism_v6.orch_r125_plain_context import has_scaffolding; '
        'text=json.load(sys.stdin)["text"]; assert text.isascii() and len(text)<2200 and not has_scaffolding(text); '
        'print(json.dumps(publish_parent(sys.argv[1],"Astra",text)))')
    result = subprocess.run([classroom.config_python(binding), '-B', '-c', code, str(root / name / 'raw')],
        input=json.dumps(dict(text=text)), text=True, capture_output=True, check=True, timeout=20,
        cwd=binding['source'], env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=binding['source'],
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1'))
    publication = dict(json.loads(result.stdout), text=text, prepared_sha256=sha(directory / 'PREPARED.json'),
        published_utc=stamp())
    save(directory / 'PUBLISHED.json', publication)
    return publication


def open_epochs(root, output, config):
    helper, bound = helpers(root, config)
    for name in PLAYERS:
        publication = send(helper, root, name, output / name / 'turn_0000', bound[name], 0)
        print(json.dumps(dict(life=name, id=publication['id'], sha256=publication['sha256'],
            published_utc=publication['published_utc'], rendered_not_inferred=True)), flush=True)


def attachment_path(output, resume, pid):
    started = output / 'FORMER_CONTROL_PARENT_STARTED.json'
    if not resume:
        return started
    previous = json.loads(started.read_bytes())
    if Path('/proc', str(previous['pid'])).exists():
        raise ValueError('old_parent_must_be_absent_before_explicit_resume')
    return output / 'former_control_attachments' / (str(pid) + '.json')


def serve_former_control(root, output, config, resume=False):
    helper, bound = helpers(root, config)
    lock = (root / 'R233_FORMER_CONTROL_PARENT.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    name = FORMER_CONTROL
    binding = bound[name]
    first = output / name / 'turn_0000'
    if not (first / 'PUBLISHED.json').exists():
        raise ValueError('actual explicitly authorized epoch opener required first')
    humans = {path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
        if json.loads(path.read_bytes()).get('speaker') == 'Rohin'}
    own = identity(os.getpid())
    started_path = attachment_path(output, resume, os.getpid())
    save(started_path, dict(pid=os.getpid(), start_ticks=own['start_ticks'],
        code_sha256=sha(Path(__file__)), started_utc=stamp(), sole_life=name,
        previous_unparented_epoch_preserved=True, parented_epoch_policy=POLICY, native_signals=0,
        other_four_parents_unchanged=True, actual_new_native_launch=False))
    while helper.alive(binding) and time.time() < binding['deadline'] - 60:
        turns = sorted((output / name).glob('turn_*'))
        current = turns[-1]
        prepared = json.loads((current / 'PREPARED.json').read_bytes())
        publication = json.loads((current / 'PUBLISHED.json').read_bytes())
        if publication['prepared_sha256'] != sha(current / 'PREPARED.json') or sha(Path(publication['path'])) != publication['sha256']:
            raise ValueError('unchanged source-bound prior publication required')
        delivery = helper.actual_delivery(root, name, publication, prepared['floor'])
        cycles = classroom.completed_cycles(helper, root, name, prepared['checkpoint']['index'])
        new_humans = [path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
            if path.stem not in humans and json.loads(path.read_bytes()).get('speaker') == 'Rohin']
        state = dict(pid=os.getpid(), observed_utc=stamp(), parent_id=publication['id'], delivery=delivery,
            completed_cycles=len(cycles), native_signals=0, learning_exclusions=0,
            sole_life=name, actual_parented_epoch=True)
        if new_humans:
            state.update(status='PARENT_SENDS_YIELD_TO_GENUINE_HUMAN', human_ids=new_humans)
        elif classroom.due(delivery, cycles):
            next_turn = prepared['turn'] + 1
            following = output / name / f'turn_{next_turn:04d}'
            metrics = classroom.repetition_metrics(helper, root, name, prepared['floor'])
            sent = send(helper, root, name, following, binding, next_turn)
            save(following / 'PRIOR_RECEIPTS.json', dict(delivery=delivery, cycles=cycles, metrics=metrics,
                parent_approach_changed=True, three_cycle_forced=len(cycles) >= 3, learning_exclusions=0))
            state.update(status='NEW_PARENT_PUBLISHED_RENDER_PENDING', new_parent_id=sent['id'])
        else:
            state['status'] = 'WAIT_RESPONSE_OR_THREE_CYCLE_PARENT_CHANGE'
        partial = output / 'FORMER_CONTROL_PARENT_HEARTBEAT.partial'
        partial.write_text(json.dumps(state, sort_keys=True, indent=2) + '\n')
        partial.replace(output / 'FORMER_CONTROL_PARENT_HEARTBEAT.json')
        time.sleep(15)


def projection(root, output, config):
    helper, bound = helpers(root, config)
    rows = []
    for name in PLAYERS:
        directory = output / name / 'turn_0000'
        prepared = json.loads((directory / 'PREPARED.json').read_bytes())
        publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
        if sha(directory / 'PREPARED.json') != publication['prepared_sha256'] or sha(Path(publication['path'])) != publication['sha256']:
            raise ValueError('epoch source must remain exact')
        rows.append(dict(life=name, native_pid=bound[name]['native_pid'], native_alive=helper.alive(bound[name]),
            parent_id=publication['id'], parent_sha256=publication['sha256'], published_utc=publication['published_utc'],
            prior_astra_inboxes=prepared['prior_astra_inboxes'], former_control=prepared['former_control'],
            delivery=helper.actual_delivery(root, name, publication, prepared['floor']),
            checkpoint_before_parent=prepared['checkpoint'], previous_history_unchanged=True))
    return dict(observed_utc=stamp(), policy=POLICY, rows=rows, code_sha256=sha(Path(__file__)),
        new_natives=0, native_signals=0, learning_policy_changes=0,
        former_control_not_an_unparented_control_after_this_input=True,
        preexisting_four_parent_controller_unchanged=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('open', 'serve-former-control', 'project'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--resume', action='store_true')
    options = parser.parse_args()
    configuration = json.loads(options.config.read_bytes())
    if options.mode == 'open':
        open_epochs(options.root, options.output, configuration)
    elif options.mode == 'serve-former-control':
        serve_former_control(options.root, options.output, configuration, options.resume)
    else:
        result = projection(options.root, options.output, configuration)
        save(options.receipt, result)
        print(json.dumps(dict(observed_utc=result['observed_utc'], published=len(result['rows']),
            rendered=sum(bool(row['delivery']['REQUEST']) for row in result['rows']))))
