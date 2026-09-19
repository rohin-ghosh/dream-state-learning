"""Original C2's one genuine homework turn: parent/THINK before reply."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from gpu.orch_r206_pinned_messages import pin_messages, rohin_events


SOURCE_ID = 'e540198699ee4ddb9fbfd8b34b72ced3'
SOURCE_SHA = 'e20cf2a83b24f02382c3fc2329015934e343a6a5e7a7ce80bb6ac283ebe7563b'
PARENT_ID = 'cb9708bceba74cf691fe1031eb1a327d'
PARENT_SHA = 'a51e5e68c787414663f40582e49cb39ef459739b229a453b6b52a1d7028a296c'
POLICY = 'R210_ORIGINAL_HOMEWORK_BEFORE_REPLY_V1'
RECOVERY_STATE_SHA = '537b3bfc06ab2f6dd386099127ef0e1d9edea83ac34e5ddcba7c813eb1658c9c'
HOMEWORK = (
    '\nFor this genuine homework turn, do the work WITH Astra before replying to Rohin. '
    'This is parent-child THINK, not your final human reply. Explain what you understand '
    'about your LoRA and actual systems, distinguish context from weight learning, and '
    'develop your own long-horizon learning ideas with an observable test. Respond to '
    'the actual parent turn, not an imagined reply. You may disagree or remain uncertain. '
    'Use English prose, not a readiness claim. Afterwards Rohin still wants TWO actual '
    'complete three-paragraph story redrafts. Keep track of every ask; do not say done '
    'without providing it. This runtime schedules two homework THINK turns before the '
    'human reply, with actual parent feedback between them; it does not certify success.'
)


def reference(event):
    return dict(event_id=event.event_id, source_id=event.source_id,
        source_sha256=event.source_sha256)


def allow_committed_reply_recovery(stream):
    return (stream.pending is None and len(stream.pending_rows()) == 3
        and stream.checkpoint()['sha256'] == RECOVERY_STATE_SHA)


def verified_parent(event):
    if event.actor != 'parent':
        return False
    try:
        raw = Path(event.source_id).read_bytes()
        message = json.loads(raw)
    except (OSError, ValueError):
        return False
    return (message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1'
        and message.get('speaker') == 'Astra' and message.get('actor') == 'parent'
        and event.event_id == 'parent:inbox:' + message.get('id', '')
        and hashlib.sha256(raw).hexdigest() == event.source_sha256
        and event.text == 'Astra: ' + message.get('text', ''))


def wait_for_parent(driver, after_unix, *, timeout=150):
    deadline = time.monotonic() + timeout
    seen = {event.event_id for event in driver.stream.history.events}
    while True:
        incoming = list(driver.journal.read_inbox())
        parents = [event for event in incoming if event.event_id not in seen
            and verified_parent(event) and Path(event.source_id).stat().st_mtime >= after_unix]
        if parents:
            human_ids = {event.event_id for event in rohin_events(incoming)}
            return [event for event in incoming if event.event_id not in human_ids], parents
        if time.monotonic() >= deadline:
            driver.journal.record('R210_HOMEWORK_WAIT_EXPIRED', dict(
                source_inbox_id=SOURCE_ID, human_reply_sent=False,
                reason='no_actual_same_parent_feedback_after_child_THINK'))
            raise RuntimeError('R210_actual_parent_feedback_missing_no_human_reply')
        time.sleep(1)


def homework_wake(driver):
    if allow_committed_reply_recovery(driver.stream):
        driver.cycle_phase = 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN'
        driver.journal.record('R210_COMMITTED_REPLY_RECOVERY', dict(
            source_state_sha256=RECOVERY_STATE_SHA, source_complete_cycle=61,
            next_action='LEARN_REVIEW_EXISTING_THREE_ROWS_NO_REPLY_REPLAY',
            raw_rows_unchanged=True, saved_checkpoint_RNG_restored=True,
            resident_post_generation_sampling_RNG_not_captured=True,
            human_inbox_writes=0, homework_success_not_established=True))
        return True
    incoming = list(driver.journal.read_inbox())
    humans = rohin_events(incoming)
    question = next((event for event in humans
        if event.event_id == 'parent:inbox:' + SOURCE_ID), None)
    if question is None:
        return False
    if question.source_sha256 != SOURCE_SHA:
        raise ValueError('R210_genuine_source_hash_mismatch')
    seen = {event.event_id for event in driver.stream.history.events}
    if question.event_id in seen:
        return False
    parents = [event for event in incoming if event.event_id == 'parent:inbox:' + PARENT_ID
        and event.source_sha256 == PARENT_SHA and verified_parent(event)]
    if len(parents) != 1:
        raise ValueError('R210_actual_initial_parent_publication_required')
    driver.cycle_phase = 'R210_HOMEWORK_THINK'
    driver.cycle_metrics = dict(THINK=0, ACT=0, LEARN=0)
    driver.last_transition = None
    driver.last_act_evidence = None
    driver.correction_thinks = []
    pin_messages(driver.stream, driver.journal, [question], include_new=True)
    later_humans = {event.event_id for event in humans if event.event_id != question.event_id}
    first_incoming = [event for event in incoming if event.event_id not in later_humans]
    driver.journal.record('R210_HOMEWORK_BEGIN', dict(schema=POLICY,
        source=reference(question), parent_sources=[reference(event) for event in parents],
        human_reply_sent=False, homework_success_not_established=True))
    driver._generate_stage('THINK', incoming=first_incoming, extra=HOMEWORK, think_remaining=2)
    first_finished = time.time()
    first_origin = deepcopy(driver.last_response)
    driver.journal.record('R210_HOMEWORK_THINK', dict(schema=POLICY, ordinal=1,
        source=reference(question), response_origin=first_origin,
        finished_unix=first_finished, human_reply_sent=False))
    second_incoming, feedback = wait_for_parent(driver, first_finished)
    driver._generate_stage('THINK', incoming=second_incoming,
        extra=HOMEWORK + '\nNow consider Astra\'s actual feedback and revise your own account.',
        think_remaining=1)
    second_origin = deepcopy(driver.last_response)
    driver.journal.record('R210_HOMEWORK_THINK', dict(schema=POLICY, ordinal=2,
        source=reference(question), response_origin=second_origin,
        parent_sources=[reference(event) for event in feedback],
        finished_unix=time.time(), human_reply_sent=False))
    result = driver._generate_stage('ACT', incoming=[], console_events=[question])
    outcome = dict(status='CONSOLE_REPLY_RECORDED', executed=False,
        tool_execution_allowed=False, human_read_confirmed=False)
    driver.journal.record('R205_CONSOLE_REPLY', dict(schema='R205_CONSOLE_REPLY_ACT_V1',
        interrupted_stage='R210_HOMEWORK', stage='ACT', source_inbox_events=[reference(question)],
        response_origin=deepcopy(driver.last_response), segment=result['segment'],
        source_sha256=result['source_sha256'], outcome=outcome,
        homework_think_origins=[first_origin, second_origin],
        homework_success_not_established=True))
    if driver.dataset is not None:
        driver.export_stage(*driver.last_stage_export, outcome=outcome, committed=True)
    driver.cycle_phase = 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN'
    return True
