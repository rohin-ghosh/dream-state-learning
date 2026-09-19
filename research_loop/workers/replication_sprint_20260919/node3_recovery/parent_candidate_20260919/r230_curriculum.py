"""Checkpoint-bound operator enrichment; no native controls or learning changes."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from r209_node3_audit import metadata, read_record

MATH = ('r213_math_a', 'r213_math_b_fork', 'r213_math_c')
CAPTIONS = tuple('r213_r226_caption_' + treatment + '_fork'
    for treatment in ('observation', 'perspective', 'revision', 'selfderive'))
MEMBERS = MATH + CAPTIONS
STAGES = ('READ', 'RECALL', 'SOCRATIC', 'WRITE', 'SELF_STUDY')
PASSAGES = (
    'At closing time, a caretaker found one small mitten beside the empty classroom. '
    'She left the hall light on and waited. When a child returned with a bare hand, '
    'she gave back the mitten without mentioning how long she had stayed.',
    'The apprentice erased a line he had worked on all morning. His teacher did not replace it. '
    'She moved a chair beside him and asked which part he still trusted. '
    'He pointed to one word, and they began there.',
    'Two neighbors planted a tree whose shade would not reach their benches for years. '
    'After one neighbor moved away, the other still watered both sides. '
    'The first new leaf was small enough to miss unless someone was looking.',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)


def ref(record):
    return dict(index=record['index'], sha256=record['sha256'])


def prompt(name, turn):
    if name not in MEMBERS or type(turn) is not int or turn < 0:
        raise ValueError('only_seven_parented_node3_lives')
    stage = STAGES[turn % len(STAGES)]
    passage = PASSAGES[(turn // len(STAGES)) % len(PASSAGES)]
    if name in MATH:
        task = ('Keep your current shared math problem and actual peer debate. This brief reading strand '
            'adds to that work; it does not replace the problem or decide its answer. ')
    else:
        task = ('Keep the funny-caption contest primary, with the actual current scene and real judge feedback. '
            'Do this short reading strand during THINK; at ACT return to an actual caption for that scene. '
            'Do not substitute the reading for the scene or invent scores. ')
    exercises = {
        'READ': ('Short fictional passage written by your parent: ' + passage
            + ' In a few ordinary sentences, retell the choice and the feeling the passage conveys. '
            'What detail supports your reading, and what remains uncertain?'),
        'RECALL': ('After the intervening sleep, what do you remember from the short reading? '
            'Retell its central choice without merely promising to remember. Has your interpretation '
            'of its feeling changed? Say when you are unsure. This is not proof of memory independent '
            'of context that may still be visible.'),
        'SOCRATIC': ('Study question about this research: your language-model base is frozen and learning '
            'changes a private adapter during sleep. The study asks whether such learning, grounded in '
            'tasks and external feedback, improves transfer to a new verifiable task. That is a hypothesis, '
            'not a result established by this summary; you have not been given the full paper here. '
            'What do you know, what evidence is missing, and what should you ask the parent? '
            'How could a person confuse repetition with understanding, and could the same error affect your claim?'),
        'WRITE': ('Write two or three original sentences connected to the reading you recall: '
            'change one choice or consequence while keeping a recognizable connection. '
            'Explain that connection briefly. This is fiction, not an account of a tool result or another speaker.'),
        'SELF_STUDY': ('Compare one thing you recently planned with what you actually wrote or checked. '
            'Notice repetition, unclear language, or an unsupported claim. Choose one small check '
            'you can genuinely perform on the current task. If needed, ask a real question; '
            'do not fabricate the parent reply or pretend that proposed code ran.'),
    }
    return task + exercises[stage] + ' Use your own words; no schema or special answer labels are required.'


def records(root, name, floor=-1):
    for path in sorted((root / name / 'raw/stream/records').glob('[0-9]' * 20 + '.json')):
        if int(path.stem) > floor:
            yield path, metadata(path)


def latest_checkpoint(root, name):
    for path, kind in reversed(list(records(root, name))):
        if kind == 'SLEEP_COMPLETE':
            record = read_record(path)
            hashes = record['document']['checkpoint_sha256']
            if set(hashes) != {'adapter', 'optimizer', 'rng'} or any(len(value) != 64 for value in hashes.values()):
                raise ValueError('native_complete_checkpoint_binding_required')
            return dict(ref(record), checkpoint_sha256=hashes,
                optimizer_steps=record['document']['optimizer_steps'],
                native_status=record['document']['status'])
    return None


def bind(root, name):
    if name not in MEMBERS:
        raise ValueError('unparented_and_other_nodes_excluded')
    active = json.loads((root / name / 'ACTIVE_RUNTIME.json').read_bytes())
    source, control = Path(active['source']), Path(active['control'])
    guard = json.loads((control / 'GUARD.json').read_bytes())
    writer_sha = sha(source / 'gpu/orch_r127_pilot_console.py')
    if guard['source_pins']['gpu/orch_r127_pilot_console.py'] != writer_sha:
        raise ValueError('unchanged_pinned_parent_publisher')
    loaded = next(read_record(path) for path, kind in reversed(list(records(root, name))) if kind == 'LOADED')
    plan = json.loads((control / 'PLAN.json').read_bytes())
    return dict(source=str(source), control=str(control), writer_sha256=writer_sha,
        native_pid=loaded['document']['pid'], loaded=ref(loaded), deadline=plan['hard_end_unix'],
        plan_learning_policy=plan.get('learn_row_policy'), think_learning_policy=plan['think_act_learn'].get('learn_row_policy'),
        resident_selectors={key: value for key, value in plan['think_act_learn'].items() if 'filter' in key})


def alive(binding):
    process = Path('/proc', str(binding['native_pid']))
    try:
        return ((process / 'stat').read_text().rsplit(')', 1)[1].split()[0] not in ('Z', 'X')
            and str(Path(binding['control']) / 'GUARD.json').encode() in (process / 'cmdline').read_bytes().split(b'\0'))
    except FileNotFoundError:
        return False


def actual_delivery(root, name, publication, floor):
    expected = 'Astra: ' + publication['text']
    inbox, request, request_key = None, None, None
    for path, kind in records(root, name, floor):
        if kind not in ('INBOX', 'REQUEST', 'RESPONSE'):
            continue
        record = read_record(path)
        document = record['document']
        if kind == 'INBOX' and document.get('message', {}).get('id') == publication['id']:
            if document['source_sha256'] != publication['sha256']:
                raise ValueError('exact_published_parent_source')
            inbox = ref(record)
        if kind == 'REQUEST' and inbox and request is None and any(message.get('role') == 'user'
                and message.get('content') == expected for message in document['messages']):
            if not document['render_receipt']['all_history_tokens_masked']:
                raise ValueError('parent_input_must_stay_masked')
            request = dict(ref(record), started_unix=document['started_unix'], all_history_tokens_masked=True)
            request_key = hashlib.sha256(json.dumps({key: value for key, value in document.items()
                if key != 'resume_state'}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if kind == 'RESPONSE' and request and document['request_sha256'] == request_key:
            return dict(INBOX=inbox, REQUEST=request, RESPONSE=ref(record),
                child_raw_sha256=hashlib.sha256(document['response']['raw'].encode()).hexdigest(),
                curriculum_success_not_inferred=True, actual_training_not_established=True)
    return dict(INBOX=inbox, REQUEST=request, RESPONSE=None)


def ready_for_next(delivery, checkpoint):
    return bool(delivery.get('RESPONSE') and checkpoint
        and checkpoint['index'] > delivery['RESPONSE']['index'] and checkpoint['native_status'] == 'COMPLETE')


def publish(root, name, turn, binding, checkpoint, directory):
    text = prompt(name, turn)
    floor = max(int(path.stem) for path in (root / name / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    prepared = dict(life=name, turn=turn, stage=STAGES[turn % len(STAGES)], text=text, floor=floor,
        before_addition_checkpoint=checkpoint, binding=binding, operator_phase='R230_PARENTED_ENRICHMENT',
        former_withdrawn_phase_not_relabelled=True, checkpoint_forced=False, native_signals=0)
    save(directory / 'PREPARED.json', prepared)
    code = ('import json,sys; from gpu.orch_r127_pilot_console import publish_parent; '
        'from organism_v6.orch_r125_plain_context import has_scaffolding; '
        'text=json.load(sys.stdin)["text"]; '
        'assert text.isascii() and len(text)<2200 and not has_scaffolding(text); '
        'print(json.dumps(publish_parent(sys.argv[1],"Astra",text)))')
    result = subprocess.run(['/localhome/local-rohing/v2/venv/bin/python', '-B', '-c', code,
        str(root / name / 'raw')], input=json.dumps(dict(text=text)), text=True, capture_output=True,
        cwd=binding['source'], env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=binding['source'],
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1'), timeout=20, check=True)
    publication = dict(json.loads(result.stdout), text=text, published_utc=datetime.now(timezone.utc).isoformat(),
        prepared_sha256=sha(directory / 'PREPARED.json'))
    save(directory / 'PUBLISHED.json', publication)
    return publication


def run(root, output, curriculum):
    output.mkdir(parents=True, exist_ok=True)
    lock = (root / 'R230_CURRICULUM_WRITER.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    bound = {name: bind(root, name) for name in MEMBERS}
    original_humans = {name: {path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
        if json.loads(path.read_bytes()).get('speaker') == 'Rohin'} for name in MEMBERS}
    save(output / 'STARTED.json', dict(pid=os.getpid(), started_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), approved_curriculum_sha256=sha(curriculum), bindings=bound,
        parented_lives=list(MEMBERS), unparented_excluded=['r213_r226_caption_unparented_fork'],
        existing_math_debate_worker_unchanged=True, role='CURRICULUM_ONLY_NOT_DUPLICATE_DEBATE_OR_TOOL_FEEDBACK',
        native_signals=0, native_restarts=0, source_or_learning_policy_changes=0,
        seed_packet_delivered=False, seed_packet_owner='Leibniz', scientific_success_claimed=False))
    while time.time() < max(item['deadline'] for item in bound.values()) - 60:
        rows = []
        for name in MEMBERS:
            binding = bound[name]
            row = dict(life=name, native_pid=binding['native_pid'], native_alive=alive(binding))
            rows.append(row)
            if not row['native_alive'] or time.time() >= binding['deadline'] - 60:
                row['state'] = 'NATIVE_ENDED_OR_OPERATOR_WALL_NO_CONTROL_ACTION'
                continue
            new_human = [path.stem for path in (root / name / 'raw/stream/inbox').glob('*.json')
                if path.stem not in original_humans[name] and json.loads(path.read_bytes()).get('speaker') == 'Rohin']
            if new_human:
                row.update(state='YIELD_CURRICULUM_TO_NEW_HUMAN_NOT_CHILD_PAUSE', human_inbox_ids=new_human)
                continue
            turns = sorted((output / name).glob('turn_[0-9][0-9][0-9][0-9]'))
            checkpoint = latest_checkpoint(root, name)
            if not checkpoint:
                row['state'] = 'WAITING_FOR_NATURAL_COMPLETE_CHECKPOINT'
                continue
            turn = 0
            if turns:
                previous = turns[-1]
                prepared = json.loads((previous / 'PREPARED.json').read_bytes())
                if not (previous / 'PUBLISHED.json').exists():
                    row['state'] = 'UNCERTAIN_PUBLICATION_REQUIRES_RECONCILIATION_NO_DUPLICATE'
                    continue
                publication = json.loads((previous / 'PUBLISHED.json').read_bytes())
                if sha(previous / 'PREPARED.json') != publication['prepared_sha256']:
                    raise ValueError('immutable_curriculum_publication')
                delivery = actual_delivery(root, name, publication, prepared['floor'])
                row.update(turn=prepared['turn'], stage=prepared['stage'], parent_id=publication['id'], delivery=delivery)
                if not ready_for_next(delivery, checkpoint):
                    row['state'] = 'WAITING_FOR_ACTUAL_RESPONSE_THEN_NATURAL_SLEEP'
                    continue
                if not (previous / 'AFTER_SLEEP.json').exists():
                    save(previous / 'AFTER_SLEEP.json', dict(delivery=delivery, after_sleep_checkpoint=checkpoint,
                        target_training_not_inferred=True))
                turn = prepared['turn'] + 1
            directory = output / name / f'turn_{turn:04d}'
            publication = publish(root, name, turn, binding, checkpoint, directory)
            row.update(state='PUBLISHED_NOT_YET_RENDERED', turn=turn, stage=STAGES[turn % len(STAGES)],
                parent_id=publication['id'], checkpoint_before_addition=checkpoint)
        heartbeat = dict(pid=os.getpid(), observed_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
            unparented_parent_writes=0, native_signals=0, seed_packet_delivered=False)
        temporary = output / 'HEARTBEAT.partial'
        temporary.write_text(json.dumps(heartbeat, sort_keys=True, indent=2) + '\n')
        temporary.replace(output / 'HEARTBEAT.json')
        time.sleep(15)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--curriculum', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.root.resolve(), arguments.output.resolve(), arguments.curriculum.resolve())
