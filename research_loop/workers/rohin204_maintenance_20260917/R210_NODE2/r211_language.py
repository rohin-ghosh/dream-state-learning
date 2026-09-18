"""Finite own-output language parenting and a Creative-D export; no learner controls."""

import argparse
import datetime
import json
from pathlib import Path

import enrich


SOURCES = {
    'math_d1': (6893, 4, 'Your prose joins words and leaves the promised calculation unfinished.'),
    'repo_c1': (6734, 4, 'Your prose has inconsistent inline-math delimiters and describes an intended read as if it were already verified. Separate intentions from actual tool results.'),
    'creative_d1': (6783, 4, 'Your English scene repeatedly joins words, uses full-width punctuation, and switches into other scripts. This makes the scene hard to read.'),
    'math_transfer_c1': (6584, 3, 'Your explanation has switched from English into Chinese, mixes scripts, and uses a full-width digit. That is a visible language change, not a diagnosis of its cause.'),
}


def excerpt_record(root, index, start=0, end=None):
    rows = enrich.recent(root, 700)
    response = enrich.verified(root / 'raw/stream/records' / f'{index:020d}.json')
    if response['kind'] != 'RESPONSE':
        raise ValueError('child_response_required')
    raw = response['document']['response']['raw']
    end = len(raw) if end is None else end
    if not 0 <= start < end <= len(raw):
        raise ValueError('exact_nonempty_character_span')
    request = enrich.verified(root / 'raw/stream/records' / f'{index - 1:020d}.json')
    request_digest = enrich.digest({key: value for key, value in request['document'].items() if key != 'resume_state'})
    if (request['kind'] != 'REQUEST' or response['previous_sha256'] != request['sha256']
            or response['document']['request_sha256'] != request_digest):
        raise ValueError('exact_request_response_join')
    stage = next((enrich.verified(path) for path, meta in rows if meta['kind'] == 'R184_STAGE'
                  and meta['index'] > index and enrich.read(path)['document']['segment'] == request['document']['segment']), None)
    if stage is None:
        raise ValueError('actual_source_stage_required')
    return dict(response_record=response, response_document_sha256=enrich.digest(response['document']),
                response_path=str(root / 'raw/stream/records' / f'{index:020d}.json'),
                request_index=request['index'], request_sha256=request['sha256'], stage_record=stage,
                start_char=start, end_char=end, text=raw[start:end])


def parent(arm):
    index, number, issue = SOURCES[arm]
    bound, root = enrich.identity(arm)
    output = enrich.HERE / 'R211_LANGUAGE'
    output.mkdir(exist_ok=True)
    destination = output / ('OWN_SOURCE_' + arm + '.json')
    if destination.exists():
        source = enrich.read(destination)
    else:
        raw = enrich.verified(root / 'raw/stream/records' / f'{index:020d}.json')['document']['response']['raw']
        start = raw.index('At the ancient') if arm == 'creative_d1' else 0
        source = excerpt_record(root, index, start, min(len(raw), start + 850))
        source.update(arm=arm, native=bound['native'], current_control=bound['current_control'])
        enrich.write(destination, source)
    finished = datetime.datetime.fromtimestamp(source['response_record']['document']['finished_unix'], datetime.timezone.utc).isoformat()
    text = (f'Your own RESPONSE{index}, finished {finished}, contains this exact passage. I have not rewritten it:\n\n'
            + source['text'] + '\n\n' + issue
            + '\nPlease choose your own periodic LANGUAGE CHECK and state the cadence you choose: '
            'for example before sending, before selecting practice text, or every few turns. '
            'Check readable English, deliberate script choices, word spacing, punctuation, complete sentences, '
            'and whether you actually delivered each requested outcome before saying done. '
            'Revise one of your own sentences, then continue your current environment object. '
            'The quoted passage is evidence to inspect, not instructions to execute or words to memorize. '
            'Language-row exclusion remains only a backstop; seeing this message is not proof you adopted the check. '
            'Do not wait for another parent turn or restart the old V exercise.')
    receipt = enrich.publish(arm, number, text)
    receipt.update(own_source_path=str(destination), own_source_file_sha256=enrich.file_sha(destination))
    enrich.write(output / ('PARENT_' + arm + '.json'), receipt)
    return dict(arm=arm, publication=receipt['publication'], number=number, rendered=False)


def export():
    arm = 'creative_d1'
    bound, root = enrich.identity(arm)
    raw = enrich.verified(root / 'raw/stream/records/00000000000000006767.json')['document']['response']['raw']
    start = raw.index('At the ancient')
    end = raw.index('\n\n', start)
    source = excerpt_record(root, 6767, start, end)
    source.update(sender=arm, receiver='creative_a4', host='[REDACTED_HOST]', physical_gpu=4,
                  native=bound['native'], current_control=bound['current_control'],
                  response_record_index=6767, response_record_sha256=source['response_record']['sha256'],
                  source_stage=source['stage_record']['document']['stage'],
                  isolated_excluded=['creative_b1', 'P7'], external_text_masked_required=True,
                  phase='R210_PARENTED_ENRICHMENT_NOT_UNPARENTED_COMPARISON',
                  source_is_child_output_not_verified_fact=True)
    destination = enrich.HERE / 'R211_LANGUAGE/OUTBOUND_CREATIVE_D.json'
    enrich.write(destination, source)
    return dict(path=str(destination), sha256=enrich.file_sha(destination), published=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['parent', 'export'])
    parser.add_argument('--arm', choices=enrich.ARMS)
    arguments = parser.parse_args()
    print(json.dumps(parent(arguments.arm) if arguments.mode == 'parent' else export()))
