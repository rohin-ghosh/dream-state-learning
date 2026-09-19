"""Exact-incarnation parent transport; visibility is measured, not a cadence gate."""

from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork')
CONTROL = ROOT / 'control_checkpoint_tail_20260919_v2'
STORE = ROOT / 'parent_checkpoint_tail_20260919'
HELPERS = Path('/localhome/local-rohing/orch_rohin233_focus_node2_20260918')
PID, START, LOADED = 1800978, 101994417, 8529
HARD_END = 1789927200
PINS = {
    HELPERS / 'focus.py': '9fe17b0af9ba8ebb2f6d651c52a1c1b456a0329eb871618a8bf06aab7e62dd77',
    CONTROL / 'PLAN.json': '96f81a410f62a5d4444fee8c6d6b36f77f31509ccdc563619fd595805d955222',
    CONTROL / 'GUARD.json': '1887d4d3047aca82fd5d0335453174020ba870c7fdcaa60a73ac48e37b85afeb',
}
PUBLISHER_SHA = 'be7cfab563dcfe31590329e930b73238e26d39c7b03eb16c1859cc3e91f0b683'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    require(path.is_file() and not path.is_symlink(), 'regular_bound_file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_answer(inbox_index, acts, requests, text):
    for act in acts:
        request = requests.get(act['request_sha256'])
        if request is None or request['index'] <= inbox_index:
            continue
        document = request['document']
        visible = any(text in message.get('content', '') for message in document['messages'])
        if visible:
            require(document['render_receipt']['all_history_tokens_masked'], 'external_parent_tokens_masked')
        return dict(actual_act=act, request_index=request['index'], request_sha256=request['sha256'],
                    parent_visible_in_act=visible, uptake_established=False)
    return None


def identity():
    require(time.time() < HARD_END - 60, 'original_lease_remaining')
    for path, expected in PINS.items():
        require(sha(path) == expected, 'bound_source_or_control_changed')
    sys.path.insert(0, str(HELPERS))
    import focus
    owner = focus.process(PID)
    require(owner and owner['start_ticks'] == START and owner['uid'] == 2524
            and owner['state'] not in ('T', 'Z', 'X') and str(CONTROL / 'GUARD.json') in owner['argv'],
            'exact_live_caption_native')
    plan = focus.read(CONTROL / 'PLAN.json')
    require(plan['physical'] == 2 and plan['hard_end_unix'] == HARD_END
            and plan['learn_row_policy'] == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'unchanged_caption_policy')
    source = Path(plan['source_root'])
    require(sha(source / 'gpu/orch_r127_pilot_console.py') == PUBLISHER_SHA, 'bound_atomic_publisher')
    loaded = focus.checked_record(ROOT / 'raw/stream/records' / f'{LOADED:020d}.json')
    require(loaded['kind'] == 'LOADED' and loaded['document']['pid'] == PID, 'loaded_native_binding')
    return focus, plan, dict(native=owner, loaded_index=LOADED, loaded_sha256=loaded['sha256'],
                            journal_id=loaded['journal_id'], hard_end_unix=HARD_END)


def observe(pending=None):
    focus, plan, owner = identity()
    directory = ROOT / 'raw/stream/records'
    paths = sorted(directory.glob('[0-9]' * 20 + '.json'))
    window = 4096 if pending else 384
    headers = [focus.metadata(path) for path in paths[-window:] if int(path.stem) >= LOADED]
    selected = {header['index']: focus.checked_record(directory / f"{header['index']:020d}.json")
                for header in headers if header['kind'] in ('RESPONSE', 'R184_STAGE', 'INBOX')}
    stages = {item['document'].get('source_sha256'): item for item in selected.values()
              if item['kind'] == 'R184_STAGE'}
    acts, tools = [], []
    for item in selected.values():
        if item['kind'] == 'RESPONSE':
            stage = stages.get(focus.sha(focus.canonical(item['document'])))
            if stage and stage['document']['stage'] == 'ACT':
                raw = item['document']['response']['raw']
                require(isinstance(raw, str) and len(raw.encode()) <= 32768, 'bounded_actual_act')
                acts.append(dict(index=item['index'], sha256=item['sha256'], raw=raw,
                                 raw_sha256=focus.sha(raw.encode()), stage_index=stage['index'],
                                 request_sha256=item['document']['request_sha256'],
                                 finished_utc=datetime.fromtimestamp(item['document']['finished_unix'], timezone.utc).isoformat()))
        if item['kind'] == 'INBOX' and item['document'].get('message', {}).get('actor') == 'environment':
            message = item['document']['message']
            tools.append(dict(index=item['index'], sha256=item['sha256'], actor=message.get('actor'),
                              speaker=message.get('speaker'), id=message.get('id')))
    result = dict(observed_utc=focus.utc(), identity=owner, head=headers[-1],
                  latest_act=acts[-1] if acts else None, visible_tool_receipts_metadata_only=tools[-4:],
                  tool_content_or_scores_exported=False, native_changes=0)
    if pending:
        inbox = next((item for item in selected.values() if item['kind'] == 'INBOX'
                      and item['document'].get('message', {}).get('id') == pending['publication']['id']), None)
        if inbox:
            message = inbox['document']['message']
            require(message['actor'] == 'parent' and message['speaker'] == 'Astra'
                    and message['text'] == pending['text'] and message.get('source_receipt') is None
                    and inbox['document']['source_sha256'] == pending['publication']['sha256'], 'verified_parent_inbox')
            result['inbox'] = dict(index=inbox['index'], sha256=inbox['sha256'])
            requests = {}
            wanted = {act['request_sha256'] for act in acts if act['index'] > inbox['index']}
            for header in headers:
                if header['kind'] != 'REQUEST' or header['index'] <= inbox['index']:
                    continue
                request = focus.checked_record(directory / f"{header['index']:020d}.json")
                digest = focus.sha(focus.canonical({key: value for key, value in request['document'].items()
                                                   if key != 'resume_state'}))
                if digest in wanted:
                    requests[digest] = request
                    answer = choose_answer(inbox['index'], acts, requests, pending['text'])
                    if answer:
                        result['answer'] = answer
                        break
        elif headers[0]['index'] > pending['source_index']:
            result['unresolved_publication_outside_window'] = True
    return result


def publish(request):
    focus, plan, owner = identity()
    number, text = request['number'], request['text']
    require(type(number) is int and 35 <= number < 640, 'original_paid_parent_ceiling')
    require(isinstance(text, str) and 0 < len(text.encode()) <= 4096 and len(text.split()) <= 90, 'bounded_parent_message')
    source = focus.checked_record(ROOT / 'raw/stream/records' / f"{request['source_index']:020d}.json")
    require(source['kind'] == 'RESPONSE' and source['sha256'] == request['source_sha256'], 'source_bound_parent_turn')
    STORE.mkdir(mode=0o700, exist_ok=True)
    with (STORE / 'PUBLISH.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        intent = STORE / f'INTENT_{number:04d}.json'
        receipt = STORE / f'PUBLISHED_{number:04d}.json'
        body = dict(number=number, text_sha256=focus.sha(text.encode()), source_index=source['index'], source_sha256=source['sha256'])
        if intent.exists():
            require(focus.read(intent) == body, 'conflicting_parent_publication')
            require(receipt.exists(), 'ambiguous_publication_no_automatic_retry')
            return focus.read(receipt)
        focus.write(intent, body)
        sys.path.insert(0, plan['source_root'])
        from gpu.orch_r127_pilot_console import publish_parent
        publication = publish_parent(ROOT / 'raw', 'Astra', text)
        result = dict(publication=publication, observed_utc=focus.utc(), identity=owner,
                      source_index=source['index'], source_sha256=source['sha256'], native_changes=0)
        focus.write(receipt, result)
        return result


def main(request):
    require(request.get('operation') in ('poll', 'publish'), 'parent_only_operation')
    return observe(request.get('pending')) if request['operation'] == 'poll' else publish(request)


if __name__ == '__main__':
    print(json.dumps(main(json.load(sys.stdin)), sort_keys=True))
