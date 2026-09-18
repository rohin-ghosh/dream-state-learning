"""One shared Astra curriculum with individual records; resident debate unchanged."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from retirement import PROTECTED, identity, metadata, record, save, sha


MATH = ('r213_math_a', 'r213_math_b_fork', 'r213_math_c')
CAPTIONS = tuple(name for name in PROTECTED if 'caption_' in name and 'unparented' not in name)
MEMBERS = MATH + CAPTIONS
STAGES = ('MATH', 'READ', 'PROBE', 'WRITE', 'GAME')
PASSAGE = ('Mira drew a map of the garden from memory. Jun walked one path and found a locked gate. '
    'They marked that gate instead of throwing away the map. Later, a neighbor used the corrected route '
    'to carry a small plant to the sunny side.')


def utc():
    return datetime.now(timezone.utc).isoformat()


def shared_prompt(name, round_number, intervention=False, variation=0):
    if name not in MATH or type(round_number) is not int or round_number < 0:
        raise ValueError('only the three actual node3 math children')
    stage = STAGES[round_number % len(STAGES)]
    tasks = {
        'MATH': 'Keep the actual current shared math object from the debate parent. State one argument '
            'you can check completely, address an actual peer argument, and say what remains unresolved. '
            'Do not revive the retired switch task or substitute a new equation silently.',
        'READ': 'Shared short reading: ' + PASSAGE + ' Retell the cause and consequence in your own words. '
            'Distinguish what the story says from an inference.',
        'PROBE': 'Recall the shared garden-map reading if it is visible or remembered; say if it is not. '
            'What evidence would distinguish a useful partial model from a wholly wrong one? '
            'Compare that question with one genuinely checked case in your current math debate.',
        'WRITE': 'Write a brief original scene related to the garden-map reading, changing one choice '
            'and its consequence. Then identify what you preserved and what you changed. '
            'Label the scene as invented, not a tool receipt or another person\'s reply.',
        'GAME': 'A small shared word game: privately choose a common object, give your two actual peers '
            'two informative clues without naming it, and consider how to test a proposed guess. '
            'Do not invent their guesses. This text game has no external judge or score.',
    }
    styles = {
        MATH[0]: 'Keep your explanation concise and check completeness.',
        MATH[1]: 'Walk through a concrete case and distinguish a plan from an executed check.',
        MATH[2]: 'Derive your own check before comparing with the peers.',
    }
    prefix = ('Astra is one shared classroom parent for Math A, Math B, and Math C; '
        'each keeps its own records and authors its own words. ')
    changes = (
        'Change the approach now: contrast two genuinely different cases instead of repeating a promise. ',
        'Change the approach now: return to an earlier abandoned branch and give one concrete check of it. ',
        'Change the approach now: identify a possible counterexample and narrow the claim it would contradict. ',
        'Change the approach now: separate what you actually checked from what remains only a plan. ',
    )
    extra = ('Three completed cycles without a new parent intervention have elapsed. '
        + changes[variation % len(changes)]) if intervention else ''
    return prefix + extra + tasks[stage] + ' ' + styles[name] + (
        ' Use this enrichment during THINK while keeping the actual bounded math debate and own conclusion. '
        'Only actual peer deliveries count; no claim of agreement or executed code is supplied by this parent. '
        'Ordinary prose is fine. Genuine Rohin instructions have priority.')


def completed_cycles(helper, root, name, after):
    return [dict(index=value['index'], sha256=value['sha256'])
        for path, kind in helper.records(root, name, after) if kind == 'SLEEP_COMPLETE'
        and (value := record(path))['document'].get('status') == 'COMPLETE']


def repetition_metrics(helper, root, name, after):
    outputs = []
    for path, kind in helper.records(root, name, after):
        if kind == 'R184_ACT':
            act = record(path)
            origin = act['document']['origin']
            response = record(path.with_name(f"{origin['record_index']:020d}.json"))
            if origin['kind'] != 'TRAIN_CHILD_RESPONSE' or response['sha256'] != origin['record_sha256']:
                raise ValueError('authentic own ACT source required')
            raw = response['document']['response']['raw']
            outputs.append(dict(index=response['index'], sha256=response['sha256'],
                text_sha256=hashlib.sha256(raw.encode()).hexdigest()))
    last = outputs[-3:]
    return dict(last_three=last, exact_repeat=len(last) == 3 and len({item['text_sha256'] for item in last}) == 1,
        semantic_repetition_not_inferred=True, learning_exclusions=0)


def due(delivery, cycles):
    rendered_response = delivery.get('RESPONSE')
    return bool(len(cycles) >= 3 or rendered_response and cycles
        and cycles[-1]['index'] > rendered_response['index'])


def answered(delivery, cycles):
    response = delivery.get('RESPONSE')
    return bool(response and cycles and cycles[-1]['index'] > response['index'])


def restore(helper, root, output, current):
    rounds = sorted((output / 'classroom').glob('round_*.json'))
    round_number = int(rounds[-1].stem.removeprefix('round_')) + 1 if rounds else 0
    math_round = dict.fromkeys(MATH, -1)
    caption_turn = {name: current[name]['old_turn'] + 1 for name in CAPTIONS}
    sequence = dict.fromkeys(MEMBERS, 0)
    for name in MEMBERS:
        turns = sorted((output / name).glob('turn_*'))
        if not turns:
            continue
        directory = turns[-1]
        if not (directory / 'PUBLISHED.json').exists():
            raise ValueError('uncertain publication must be reconciled, never duplicated')
        prepared = json.loads((directory / 'PREPARED.json').read_bytes())
        publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
        if sha(directory / 'PREPARED.json') != publication['prepared_sha256'] or sha(Path(publication['path'])) != publication['sha256']:
            raise ValueError('resumed parent source changed')
        current[name] = dict(directory=str(directory), floor=prepared['floor'], publication=publication,
            baseline=prepared['before_checkpoint']['index'], stage=prepared['stage'])
        sequence[name] = int(directory.name.removeprefix('turn_')) + 1
        if name in MATH:
            math_round[name] = round_number if prepared['stage'] == 'R233_CLASSROOM_' + STAGES[round_number % len(STAGES)] else round_number - 1
        else:
            caption_turn[name] += len(turns)
    return round_number, math_round, caption_turn, sequence


def load_helpers(root, config, recovering=False):
    for relative, digest in config['helper_pins'].items():
        if sha(root / relative) != digest:
            raise ValueError('frozen operator helper changed: ' + relative)
    sys.path[:0] = [str(root / config['helper_directory']), str(root)]
    helper = importlib.import_module('r230_curriculum')
    bound = {name: helper.bind(root, name) for name in MEMBERS}
    live = [item for item in bound.values() if helper.alive(item)]
    if not live or not recovering and len(live) != len(MEMBERS):
        raise ValueError('all seven protected parented natives must be alive')
    return helper, bound


def publish(helper, root, name, text, stage, directory, bound, before):
    if name not in MEMBERS:
        raise ValueError('unparented control and other nodes cannot receive parent input')
    floor = max(int(path.stem) for path, kind in helper.records(root, name))
    save(directory / 'PREPARED.json', dict(life=name, floor=floor, text=text, stage=stage,
        operator_phase='R233_SHARED_CLASSROOM_CAPTION_PRESERVATION', before_checkpoint=before,
        binding=bound, native_signals=0, learning_exclusions=0))
    code = ('import json,sys; from gpu.orch_r127_pilot_console import publish_parent; '
        'from organism_v6.orch_r125_plain_context import has_scaffolding; '
        'text=json.load(sys.stdin)["text"]; assert text.isascii() and len(text)<2200 and not has_scaffolding(text); '
        'print(json.dumps(publish_parent(sys.argv[1],"Astra",text)))')
    result = subprocess.run([config_python(bound), '-B', '-c', code, str(root / name / 'raw')],
        input=json.dumps(dict(text=text)), text=True, capture_output=True, check=True, timeout=20,
        cwd=bound['source'], env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=bound['source'],
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1'))
    publication = dict(json.loads(result.stdout), text=text, published_utc=utc(),
        prepared_sha256=sha(directory / 'PREPARED.json'))
    save(directory / 'PUBLISHED.json', publication)
    return dict(directory=str(directory), floor=floor, publication=publication,
        baseline=before['index'], stage=stage)


def config_python(binding):
    args = Path('/proc', str(binding['native_pid']), 'cmdline').read_bytes().split(b'\0')
    python = args[0].decode()
    if not Path(python).name.startswith('python'):
        raise ValueError('verified native Python executable required')
    return python


def inherited(helper, root, old_output, name):
    turns = sorted((old_output / name).glob('turn_[0-9][0-9][0-9][0-9]'))
    if not turns:
        raise ValueError('prior parent history must be retained')
    directory = turns[-1]
    prepared = json.loads((directory / 'PREPARED.json').read_bytes())
    publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
    if sha(directory / 'PREPARED.json') != publication['prepared_sha256'] or sha(Path(publication['path'])) != publication['sha256']:
        raise ValueError('prior publication source changed')
    return dict(directory=str(directory), floor=prepared['floor'], publication=publication,
        baseline=prepared['before_addition_checkpoint']['index'], old_turn=prepared['turn'], stage=prepared['stage'])


def serve(root, output, config, resume=False, recovering=False):
    if recovering and not resume:
        raise ValueError('recovering_attachment_requires_preserved_parent_state')
    helper, bound = load_helpers(root, config, recovering)
    lock = (root / 'R230_CURRICULUM_WRITER.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    current = {name: inherited(helper, root, root / 'r230_curriculum_live_v1', name) for name in MEMBERS}
    original_humans = {name: {path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
        if json.loads(path.read_bytes()).get('speaker') == 'Rohin'} for name in MEMBERS}
    if resume:
        original_humans = {name: set(values) for name, values in json.loads((output / 'STARTED.json').read_bytes())['original_humans'].items()}
        if set(original_humans) != set(MEMBERS):
            raise ValueError('exact prior human frontier required')
    own = identity(os.getpid())
    attachment = output / 'attachments' / (str(os.getpid()) + '.json') if resume else output / 'STARTED.json'
    save(attachment, dict(pid=os.getpid(), start_ticks=own['start_ticks'], started_utc=utc(),
        code_sha256=sha(Path(__file__)), config_sha256=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        bindings=bound, original_humans={name: sorted(values) for name, values in original_humans.items()},
        one_shared_parent='Astra', separate_authenticated_math_debate_service_retained=True,
        all_old_publications_preserved=True, native_signals=0, learning_policy_changes=0))
    round_number = 0
    math_round = dict.fromkeys(MATH, -1)
    caption_turn = {name: current[name]['old_turn'] + 1 for name in CAPTIONS}
    sequence = dict.fromkeys(MEMBERS, 0)
    if resume:
        round_number, math_round, caption_turn, sequence = restore(helper, root, output, current)
    deadline = min(item['deadline'] for item in bound.values() if helper.alive(item)) - 60
    while time.time() < deadline:
        rows = []
        math_complete = []
        for name in MEMBERS:
            if recovering and not helper.alive(bound[name]):
                bound[name] = helper.bind(root, name)
            item = current[name]
            row = dict(life=name, native_alive=helper.alive(bound[name]), stage=item['stage'])
            rows.append(row)
            if not row['native_alive']:
                row['state'] = 'NATIVE_ENDED_NO_REFILL'
                continue
            new_humans = [path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
                if path.stem not in original_humans[name] and json.loads(path.read_bytes()).get('speaker') == 'Rohin']
            delivery = helper.actual_delivery(root, name, item['publication'], item['floor'])
            cycles = completed_cycles(helper, root, name, item['baseline'])
            row.update(parent_id=item['publication']['id'], delivery=delivery, completed_cycles=len(cycles))
            if new_humans:
                row.update(state='PARENT_SENDS_YIELD_TO_GENUINE_HUMAN', human_ids=new_humans)
                continue
            if name in MATH and math_round[name] == round_number and answered(delivery, cycles):
                math_complete.append(name)
                row['state'] = 'OWN_RESPONSE_RECORDED_WAIT_SHARED_PACKET'
                if len(cycles) < 3:
                    continue
            if not due(delivery, cycles):
                row['state'] = 'WAIT_NATIVE_RESPONSE_OR_THREE_CYCLE_PARENT_CHANGE'
                continue
            before = helper.latest_checkpoint(root, name)
            metrics = repetition_metrics(helper, root, name, item['floor'])
            intervention = len(cycles) >= 3
            if name in MATH:
                text = shared_prompt(name, round_number, intervention, sequence[name])
                stage = 'R233_CLASSROOM_' + STAGES[round_number % len(STAGES)]
                math_round[name] = round_number
            else:
                text = helper.prompt(name, caption_turn[name])
                stage = 'R233_CAPTION_' + helper.STAGES[caption_turn[name] % len(helper.STAGES)]
                if intervention:
                    text = ('Change the approach after three completed cycles: use a different concrete detail '
                        'from the actual scene and check your last real judge feedback. Do not repeat a scoring '
                        'claim without its receipt. ') + text
                caption_turn[name] += 1
            directory = output / name / f'turn_{sequence[name]:04d}'
            save(directory / 'PRIOR_DELIVERY_AND_METRICS.json', dict(delivery=delivery, cycles=cycles,
                metrics=metrics, three_cycle_parent_change=intervention, previous_parent_id=item['publication']['id']))
            current[name] = publish(helper, root, name, text, stage, directory, bound[name], before)
            sequence[name] += 1
            row.update(state='PUBLISHED_NOT_YET_RENDERED', new_parent_id=current[name]['publication']['id'],
                new_stage=stage, three_cycle_parent_change=intervention)
        if set(math_complete) == set(MATH):
            save(output / 'classroom' / f'round_{round_number:04d}.json', dict(round=round_number,
                stage=STAGES[round_number % len(STAGES)], completed_utc=utc(), rows=[row for row in rows if row['life'] in MATH],
                curriculum_success_not_inferred=True, debate_conclusion_not_inferred=True))
            round_number += 1
        heartbeat = dict(observed_utc=utc(), pid=os.getpid(), shared_round=round_number, rows=rows,
            native_signals=0, unparented_writes=0, learning_exclusions=0,
            peer_and_tool_readers_unchanged=True, node4_admitted=False)
        partial = output / 'HEARTBEAT.partial'
        partial.write_text(json.dumps(heartbeat, sort_keys=True, indent=2) + '\n')
        partial.replace(output / 'HEARTBEAT.json')
        time.sleep(15)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('validate', 'serve'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--recovering', action='store_true')
    options = parser.parse_args()
    configuration = json.loads(options.config.read_bytes())
    if options.mode == 'validate':
        helper, bindings = load_helpers(options.root, configuration)
        print(json.dumps(dict(cpu_import_and_source_gate=True, protected_parented_natives=len(bindings),
            helper_pins=configuration['helper_pins'], classroom_code_sha256=sha(Path(__file__)))))
    else:
        serve(options.root, options.output, configuration, options.resume, options.recovering)
