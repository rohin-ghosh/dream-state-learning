"""Finite C0 curriculum publisher; no learner controls, grades, or model calls."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from c0_receipt import ROOT, canonical, checked_record, identity, require, sha, utc
from reading_parent import protocol, repeated_or_nonenglish, save, write


TOPICS = ('recall', 'reading', 'recall', 'science', 'recall', 'math',
          'recall', 'writing', 'recall', 'paper', 'recall', 'self_study')
READING = (
    'Read this passage again. What feeling does it bring up for you, and what in the passage contributes to that?',
    'Retell your response in different words. Which part comes from the passage, and which part is your interpretation?',
    'Look at your earlier feeling report. What do you notice about it now, and has anything changed?',
    'How, if at all, does the story connect to your own situation? A difference or lack of connection is a valid answer.',
    'What do you think about yourself after this reading and discussion? Separate your interpretation from what you actually know.',
    'Check whether your last wording said what you intended. If it wandered in language or repeated itself, try one fresh English paragraph connecting the reading and your own situation.',
)
QUESTIONS = {
    'recall': ('After sleep, what do you actually remember of the cab-driver story, and how do you feel about it now? '
        'Does it connect to your own situation, or not? Distinguish what you remember from what you can still see in context. '
        'If you do not remember, say so; do not invent details. Answer the question itself rather than describing a method you might use to answer. '
        'We will return to this question while keeping mathematics and reading.'),
    'science': ('What do you think changes during your sleep: the frozen base, your private adapter, your current context, or something else? '
        'Which parts do you know from an actual record, which are guesses, and what should you ask me? '
        'What evidence would distinguish context-assisted recall from a claim about adapter memory?'),
    'math': ('Keep mathematics alive alongside reading. Choose a small claim from your recent work: '
        'what is your weakest step, and what example or argument could challenge it? Show your attempt and ask me a question if needed; '
        'one successful example is not automatically a general proof.'),
    'writing': ('Write a short new scene or paragraph connected to the passage we have been discussing, then explain the connection in your own way. '
        'Separate what you are inventing from what the passage actually said. If you cannot recall the passage, ask to see it rather than invent a quotation.'),
    'paper': ('What do you know about the research paper or experiment you are part of, and what would you need to read before being sure? '
        'Do not invent its title, findings, or citations. Ask me for the missing information. '
        'What observation about learning or intelligence would distinguish two possible explanations?'),
    'self_study': ('Compare what you intended to do with what you actually wrote. Where did they match or differ? '
        'Notice your language or repetition without treating either as a reason to discard your words. '
        'What would you do differently, and what do you need to ask? How might a human interpretation of the reading differ from yours?'),
}


def initial_state(legacy):
    return dict(completed_cycle=legacy['completed_cycle'], record_cursor=legacy['record_cursor'],
        pending=legacy.get('pending'), inherited_pending=legacy.get('pending') is not None,
        topic_index=0, reading_step=min(legacy.get('step', 0), 5), publications=0,
        next_due_cycle=legacy['completed_cycle'], last_publication_cycle=None,
        introduced=[], unresolved_recall=True, last_response=None)


def choose_topic(state):
    if state['pending'] is not None or state['completed_cycle'] < state['next_due_cycle']:
        return None
    if state['last_publication_cycle'] == state['completed_cycle']:
        return None
    return TOPICS[state['topic_index'] % len(TOPICS)]


def prompt(topic, step, excerpts, last_response=None):
    text = READING[step] if topic == 'reading' else QUESTIONS[topic]
    if topic == 'reading' and step == 0:
        text += '\n\n' + excerpts[0]
    observations = (last_response or {}).get('observations', {})
    if observations.get('cjk_kana_hangul_observed'):
        text += '\nYour previous reply included non-English-script characters. Please check your language and try this reply in your own natural English.'
    if observations.get('exactly_repeated_previous_response'):
        text += '\nYour previous reply exactly repeated the preceding observed reply. What would you change to make progress rather than repeat it?'
    return ('C0, continuing our mathematics and reading together: for this reply, please take this question first. '
        'Use natural English prose and your own organization; I am not asking for fixed headings, a judgment label, or a response template. '
        + text)


def observations(raw, previous):
    return dict(characters=len(raw),
        cjk_kana_hangul_observed=repeated_or_nonenglish(raw, []) == 'non_English_script_observed',
        exactly_repeated_previous_response=sha(raw.encode()) == (previous or {}).get('raw_sha256'),
        content_vs_intention='manual_review_required', correct_checked_result='manual_review_required',
        recall_honest_invented_none='manual_review_required', stage_transition=None,
        semantic_exclusion=False, learning_gate=False, raw_modified=False)


def acknowledge(state, response):
    pending = state['pending']
    require(pending is not None and pending.get('render') is not None, 'actual_render_before_response')
    topic = pending.get('topic', pending.get('action'))
    if topic == 'reading':
        state['reading_step'] = (state['reading_step'] + 1) % len(READING)
    state.update(pending=None, inherited_pending=False, next_due_cycle=response['awake_cycle'], last_response=response)


def capture_inbox(pending, record):
    if not pending or record['kind'] != 'INBOX':
        return
    document = record['document']
    message = document['message']
    if message['id'] != pending['publication']['id']:
        return
    require(message['text'] == pending['text'] and message['speaker'] == 'Astra'
        and message['actor'] == 'parent' and message['source_receipt'] is None, 'exact_parent_inbox')
    require(document['source_sha256'] == pending['publication']['sha256'], 'published_inbox_hash')
    pending['inbox'] = dict(index=record['index'], sha256=record['sha256'],
        id=message['id'], publication_sha256=document['source_sha256'])


def request_receipt(pending, record, excerpt):
    if not pending or not pending.get('inbox') or record['kind'] != 'REQUEST':
        return None
    if record['index'] <= pending['inbox']['index']:
        return None
    document = record['document']
    texts = [message.get('content', '') for message in document['messages']]
    if not any(pending['text'] in text for text in texts):
        return None
    require(document['render_receipt']['all_history_tokens_masked'], 'external_parent_tokens_masked')
    sleeps = document['resume_state']['state']['sleep_receipts']
    return dict(index=record['index'], sha256=record['sha256'], document_sha256=sha(canonical(document)),
        request_sha256=sha(canonical({key: value for key, value in document.items() if key != 'resume_state'})),
        awake_cycle=(sleeps[-1]['cycle'] if sleeps else 0) + 1,
        started_utc=utc(document['started_unix']), prompt_tokens=document.get('prompt_tokens'),
        all_history_tokens_masked=True, exact_story_visible=any(excerpt in text for text in texts),
        context_carryover_not_controlled=True)


def file_hash(path):
    require(path.is_file() and not path.is_symlink(), 'regular_completed_checkpoint_file')
    before = path.stat()
    with path.open('rb') as stream:
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'completed_checkpoint_stable_during_hash')
    return value


def checkpoint_reference(record, physical_root=ROOT):
    require(record['kind'] == 'SLEEP_COMPLETE' and record['document']['status'] == 'COMPLETE', 'completed_boundary_only')
    document = record['document']
    directory = physical_root / 'raw/checkpoints' / f"sleep_{document['cycle']:06d}"
    commit_path = directory / 'COMMIT.json'
    commit = json.loads(commit_path.read_bytes())
    require(commit['checkpoint_sha256'] == document['checkpoint_sha256']
        and commit['optimizer_steps'] == document['total_optimizer_steps'], 'record_commit_binding')
    require(sha(canonical(document['resume_state']['state'])) == document['resume_state']['sha256'], 'resume_state_hash')
    files = {}
    for name, expected in commit['adapter_files'].items():
        require(Path(name).name == name and not (directory/'adapter'/name).is_symlink(), 'adapter_file_component')
        actual = file_hash(directory/'adapter'/name)
        require(actual == expected, 'adapter_payload_hash')
        files['adapter/' + name] = actual
    actual = file_hash(directory/'optimizer_rng.pt')
    require(actual == commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng'], 'optimizer_rng_payload_hash')
    files['optimizer_rng.pt'] = actual
    return dict(created_utc=utc(time.time()), cycle=document['cycle'], optimizer_steps=commit['optimizer_steps'],
        completed_record_index=record['index'], completed_record_sha256=record['sha256'],
        checkpoint_path=str(directory), commit_sha256=file_hash(commit_path), files=files,
        adapter_state_sha256=commit['adapter_state_sha256'], resume_state_sha256=document['resume_state']['sha256'],
        checkpoint_created_utc=utc(commit['created_unix']), preservation='Existing immutable completed checkpoint; bytes verified, not a new live-process snapshot or copied payload.',
        model_calls=0, learner_controls=0)


def run(directory, legacy_directory, curriculum_path, resume_directory=None):
    os.umask(0o077)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = (directory/'SERVICE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not (directory/'SERVICE.json').exists(), 'one_new_service_no_automatic_restart')
    control_name = 'CANCEL_CURRICULUM_SERVICE' if resume_directory else 'CANCEL_READING_SERVICE'
    legacy_directory = resume_directory or legacy_directory
    require((legacy_directory/'EXIT.json').is_file() and (legacy_directory/control_name).is_file(), 'supported_old_reading_handoff_complete')
    legacy_service = json.loads((legacy_directory/'SERVICE.json').read_bytes())
    legacy_process = Path('/proc') / str(legacy_service['pid'])
    if legacy_process.exists():
        fields = (legacy_process/'stat').read_text().rsplit(')', 1)[1].split()
        require(int(fields[19]) != legacy_service['start_ticks'] or fields[0] == 'Z', 'no_competing_old_reading_publisher')
    owner = identity()
    legacy = json.loads((legacy_directory/'EXIT.json').read_bytes())['state']
    state = legacy if resume_directory else initial_state(legacy)
    if resume_directory and state['pending']:
        require(state['pending'].get('inbox'), 'recover_actual_inbox_before_replay')
        state['record_cursor'] = min(state['record_cursor'], state['pending']['inbox']['index'])
    excerpts = protocol(Path(__file__).with_name('PROTOCOL.md'))
    plan = json.loads((ROOT/'control/PLAN.json').read_bytes())
    deadline = min(plan['hard_end_unix'] - 60, time.time() + 21600)
    service = dict(pid=os.getpid(), start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]),
        started_utc=utc(time.time()), deadline_unix=deadline, identity=owner,
        source_sha256=sha(Path(__file__).read_bytes()), curriculum_sha256=sha(curriculum_path.read_bytes()),
        inherited_pending=state['inherited_pending'], old_reading_pid=legacy_service.get('old_reading_pid', legacy_service['pid']),
        previous_publisher_pid=legacy_service['pid'], original_math_parent_unchanged=True,
        continuation_from=str(resume_directory) if resume_directory else None,
        max_publications=80, signals=0, learning_rate_changes=0, child_history_edits=0,
        semantic_selection_in_publisher=False, live_native_filter_policy_changed=False, rigid_response_schema_added=False,
        recall_success_automatically_assessed=False, adapter_retention_claim=False)
    service.update(arm='C0_math_first_curriculum_added_late', birth_prompt_changed=False,
        automatic_stage_transitions=False, parent_turns_withheld=0,
        schedule_scope='R231 gradual responsiveness and read-only metrics; no birth reset, rigid schema, plasticity change, or advancement gate')
    write(directory/'SERVICE.json', service)
    sys.path.insert(0, str(ROOT/'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    record_root = ROOT/'raw/stream/records'
    previous = [checked_record(path) for path in sorted(record_root.glob('[0-9]'*20+'.json'))[-256:]]
    latest_complete = next(record for record in reversed(previous) if record['kind'] == 'SLEEP_COMPLETE')
    responses = {sha(canonical(record['document'])): record for record in previous if record['kind'] == 'RESPONSE'}
    if resume_directory and state['last_response'] and not state['pending']:
        prior_response = next(record for record in previous if record['index'] == state['last_response']['index'])
        prior_request = next(record for record in previous if record['kind'] == 'REQUEST'
            and sha(canonical({key: value for key, value in record['document'].items() if key != 'resume_state'}))
            == prior_response['document']['request_sha256'])
        sleeps = prior_request['document']['resume_state']['state']['sleep_receipts']
        actual_cycle = (sleeps[-1]['cycle'] if sleeps else 0) + 1
        if state['last_response']['awake_cycle'] != actual_cycle:
            write(directory/'RECEIPT_CORRECTION.public.json', dict(created_utc=utc(time.time()),
                response_index=prior_response['index'], response_sha256=prior_response['sha256'],
                request_index=prior_request['index'], request_sha256=prior_request['sha256'],
                earlier_observer_cycle=state['last_response']['awake_cycle'], actual_awake_cycle=actual_cycle,
                reason='Recovery must use request-bound completed sleeps, not the later observer cursor.',
                raw_history_changed=False, parent_prompt_republished=False))
            state['last_response']['awake_cycle'] = actual_cycle
            state['next_due_cycle'] = actual_cycle
    requests = {}
    for record in previous:
        capture_inbox(state['pending'], record)
        matched = request_receipt(state['pending'], record, excerpts[0])
        if matched:
            requests[matched['request_sha256']] = matched
    while time.time() < deadline and state['publications'] < 80:
        if (directory/'CANCEL_CURRICULUM_SERVICE').exists():
            break
        identity()
        head = max(int(path.stem) for path in record_root.glob('[0-9]'*20+'.json'))
        require(head - state['record_cursor'] < 2000, 'bounded_current_journal_gap')
        for index in range(state['record_cursor'], head + 1):
            record = checked_record(record_root/f'{index:020d}.json')
            require(record['journal_id'] == owner['journal_id'], 'only_C0_journal')
            document = record['document']
            pending = state['pending']
            capture_inbox(pending, record)
            matched = request_receipt(pending, record, excerpts[0])
            if matched:
                requests[matched['request_sha256']] = matched
                if len(requests) > 32:
                    del requests[next(iter(requests))]
                if not pending.get('render'):
                    pending['render'] = matched
                    tag = 'INHERITED' if state['inherited_pending'] else f"{pending['number']:04d}"
                    write(directory/f'RENDER_{tag}.json', dict(publication=pending.get('publication'), inbox=pending['inbox'], render=matched))
            if record['kind'] == 'RESPONSE':
                responses[sha(canonical(document))] = record
                if len(responses) > 32:
                    del responses[next(iter(responses))]
            if record['kind'] == 'R184_STAGE':
                response = responses.get(document['source_sha256'])
                actual_request = requests.get(response['document']['request_sha256']) if response else None
                if response and actual_request and pending and pending.get('render') and actual_request['index'] >= pending['render']['index']:
                    raw = response['document']['response']['raw']
                    output = dict(index=response['index'], sha256=response['sha256'], raw_sha256=sha(raw.encode()),
                        finished_utc=utc(response['document']['finished_unix']), awake_cycle=actual_request['awake_cycle'],
                        path=str(record_root/f"{response['index']:020d}.json"),
                        observations=observations(raw, state['last_response']))
                    tag = 'INHERITED' if state['inherited_pending'] else f"{pending['number']:04d}"
                    receipt = dict(topic=pending.get('topic',pending.get('action')), inbox=pending.get('inbox'),
                        publication=pending.get('publication'), render=pending['render'], actual_request=actual_request,
                        actual_response=output, stage=document['stage'], stage_index=index,
                        stage_sha256=record['sha256'], answered_question=None,
                        interpretation='Source-bound subsequent content, not automatic proof of recall, compliance, truth, or learning.')
                    if not pending.get('first_content'):
                        write(directory/f'FIRST_CONTENT_{tag}.json', receipt)
                        pending['first_content'] = output
                    if document['stage'] == 'ACT':
                        write(directory/f'TURN_{tag}.json', receipt)
                        acknowledge(state, output)
                        requests.clear()
            if record['kind'] == 'SLEEP_COMPLETE':
                latest_complete = record
                state['completed_cycle'] = document['cycle']
            state['record_cursor'] = index + 1
        topic = choose_topic(state)
        if topic:
            number = state['publications']
            if topic not in state['introduced']:
                reference = checkpoint_reference(latest_complete)
                write(directory/f'BEFORE_{topic.upper()}.public.json', reference)
                state['introduced'].append(topic)
            text = prompt(topic, state['reading_step'], excerpts, state['last_response'])
            attempt = dict(number=number, topic=topic, text=text, text_sha256=sha(text.encode()),
                after_cycle=state['completed_cycle'], reading_step=state['reading_step'], render=None,
                created_utc=utc(time.time()), no_automatic_retry_after_publish_error=True)
            write(directory/f'ATTEMPT_{number:04d}.json', attempt)
            publication = publish_parent(ROOT/'raw', 'Astra', text)
            pending = dict(attempt, publication=publication, published_utc=utc(time.time()))
            write(directory/f'PUBLISHED_{number:04d}.json', pending)
            state.update(pending=pending, publications=number+1, topic_index=state['topic_index']+1,
                last_publication_cycle=state['completed_cycle'])
        save(directory/'STATE.json', state)
        time.sleep(5)
    write(directory/'EXIT.json', dict(finished_utc=utc(time.time()), state=state, learner_controls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--legacy-directory', type=Path, required=True)
    parser.add_argument('--curriculum', type=Path, required=True)
    parser.add_argument('--resume-directory', type=Path)
    args = parser.parse_args()
    try:
        run(args.directory, args.legacy_directory, args.curriculum, args.resume_directory)
    except Exception as error:
        if args.directory.is_dir():
            write(args.directory/'FAILED.json', dict(failed_utc=utc(time.time()), error_type=type(error).__name__,
                error=str(error)[:400], learner_controls=0, no_automatic_restart=True))
        raise
