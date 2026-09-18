"""Two focused parent turns through the existing C0 curriculum handoff."""

import argparse
import json
from pathlib import Path
import sys
import time

import focus


PREVIOUS = Path('/localhome/local-rohing/orch_r230_c0_operator_20260918/curriculum_current')
SUPPORT = PREVIOUS.parent/'receipt_cycle_fix'
DIRECTORY = focus.STORE/'C0_R233_READING'
OLD_PID = 2929240
OLD_START = 95395597


def reading_question(excerpt):
    return ('C0, your reading-turn ACT2490 returned odd-number mathematics, not a reading answer. '
        'Keep mathematics as an ongoing object, but take just this reading question now. '
        'This paragraph is visible context, not a memory test.\n\n' + excerpt +
        '\n\nName one concrete action the horse takes while Iona speaks, or say exactly what '
        'you are unsure about in the paragraph. Use your own English words; no headings or '
        'method description are needed. After your answer we will try a short piece of writing.')


def writing_question(excerpt, response_index):
    return (f'C0, continuing from your actual reply at RESPONSE{response_index}, now try writing '
        'rather than another mathematical calculation. The supplied story remains visible, '
        'so this is not a retention test.\n\n' + excerpt +
        '\n\nWrite a short new paragraph about someone trying to be heard, tied to one detail '
        'in this passage. Make clear what you invent rather than attributing it to the passage. '
        'Use your own natural English; there is no required format. Mathematics remains available afterwards.')


def focused_topic(original, state, first_number):
    selected = original(state)
    if selected is None:
        return None
    return {first_number: 'reading', first_number + 1: 'writing'}.get(state['publications'], selected)


def handoff():
    sys.path.insert(0, str(SUPPORT))
    import c0_receipt
    before = c0_receipt.identity()
    actual = focus.process(OLD_PID)
    focus.require(actual and actual['start_ticks'] == OLD_START
        and str(PREVIOUS) in actual['argv'] and actual['state'] not in ('T', 'Z', 'X'), 'exact_previous_C0_publisher')
    anchor = c0_receipt.checked_record(c0_receipt.ROOT/'raw/stream/records/00000000000000002490.json')
    focus.require(anchor['sha256'] == 'acbf7d97c05156a3dd81f7d707ecf9c40e536c5b48345b17b4cd7031e1f762f2', 'actual_reading_math_nonanswer')
    DIRECTORY.mkdir(mode=0o700)
    focus.write(DIRECTORY/'BEFORE_HANDOFF.public.json', dict(observed_utc=focus.utc(), identity=before,
        previous_publisher={key: value for key, value in actual.items() if key != 'argv'},
        source_sha256=focus.file_sha(Path(__file__)), signals=0, original_math_parent_unchanged=True))
    focus.write(PREVIOUS/'CANCEL_CURRICULUM_SERVICE', dict(requested_utc=focus.utc(),
        expected_pid=OLD_PID, expected_start_ticks=OLD_START,
        operation='Supported curriculum-publisher-only handoff for R233 focused reading then writing', learner_signals=0))
    for attempt in range(60):
        current = focus.process(OLD_PID)
        stopped = current is None or current['start_ticks'] != OLD_START or current['state'] == 'Z'
        if stopped and (PREVIOUS/'EXIT.json').is_file():
            state = focus.read(PREVIOUS/'EXIT.json')['state']
            focus.write(DIRECTORY/'HANDOFF.public.json', dict(completed_utc=focus.utc(), identity=c0_receipt.identity(),
                previous_exit_sha256=focus.file_sha(PREVIOUS/'EXIT.json'), first_focused_number=state['publications'],
                inherited_pending=state['pending'] is not None, learner_signals=0, publisher_signals=0))
            return
        time.sleep(1)
    raise ValueError('previous_publisher_exit_unverified_no_replacement_started')


def serve():
    sys.path.insert(0, str(SUPPORT))
    import curriculum_parent as parent
    first = focus.read(DIRECTORY/'HANDOFF.public.json')['first_focused_number']
    original_choose, original_prompt = parent.choose_topic, parent.prompt
    selected_number = None

    def choose(state):
        nonlocal selected_number
        selected_number = state['publications']
        return focused_topic(original_choose, state, first)

    def prompt(topic, step, excerpts, last_response=None):
        if selected_number == first:
            return reading_question(excerpts[0])
        if selected_number == first + 1:
            return writing_question(excerpts[0], (last_response or {}).get('index'))
        return original_prompt(topic, step, excerpts, last_response)

    parent.choose_topic, parent.prompt = choose, prompt
    try:
        parent.run(DIRECTORY, PREVIOUS, Path(__file__), resume_directory=PREVIOUS)
    except Exception as error:
        focus.write(DIRECTORY/'FAILED.public.json', dict(failed_utc=focus.utc(), error_type=type(error).__name__,
            error=str(error)[:250], learner_signals=0, automatic_restart=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('handoff', 'serve'))
    args = parser.parse_args()
    handoff() if args.action == 'handoff' else serve()
