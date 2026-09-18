"""Fixed-root caption parent transport: inspect and authenticated INBOX only."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import focus


ROOT = Path('/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork')
PID = 2884345
START = 95317660
EPOCH = focus.STORE/'CAPTION_R233_EPOCH.private.json'


def stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def identity():
    actual = focus.process(PID)
    focus.require(actual and actual['start_ticks'] == START and actual['uid'] == 2524
        and str(ROOT/'control/GUARD.json') in actual['argv'] and actual['state'] not in ('T', 'Z', 'X'), 'exact_live_caption_native')
    plan = focus.read(ROOT/'control/PLAN.json')
    focus.require(plan['physical'] == 2 and plan['learn_row_policy'] == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'existing_slot_and_policy')
    return dict(pid=PID, start_ticks=START, state=actual['state'], cmdline_sha256=actual['cmdline_sha256'],
        root=str(ROOT), physical_gpu=2, plan_sha256=focus.file_sha(ROOT/'control/PLAN.json'),
        guard_sha256=focus.file_sha(ROOT/'control/GUARD.json'), hard_end_unix=plan['hard_end_unix'])


def request_digest(document):
    return focus.sha(focus.canonical({key: value for key, value in document.items() if key != 'resume_state'}))


def inspect(pending=None):
    owner = identity()
    directory = ROOT/'raw/stream/records'
    paths = sorted(directory.glob('[0-9]'*20+'.json'))
    headers = [focus.metadata(path) for path in paths[-256:]]
    loaded_headers = [focus.metadata(path) for path in paths[:8]]
    loaded = focus.checked_record(directory/f"{next(item['index'] for item in loaded_headers if item['kind']=='LOADED'):020d}.json")
    focus.require(loaded['document']['pid'] == PID, 'loaded_exact_native')
    selected = {header['index']: focus.checked_record(directory/f"{header['index']:020d}.json")
        for header in headers if header['kind'] in ('RESPONSE', 'R184_STAGE', 'INBOX')}
    stages = [item for item in selected.values() if item['kind'] == 'R184_STAGE']
    acts = []
    tools, parents = [], []
    for item in selected.values():
        if item['kind'] == 'RESPONSE':
            stage = next((candidate for candidate in stages if candidate['document'].get('source_sha256') == focus.sha(focus.canonical(item['document']))), None)
            if stage and stage['document']['stage'] == 'ACT':
                raw = item['document']['response']['raw']
                focus.require(isinstance(raw, str) and len(raw.encode()) <= 32768, 'bounded_actual_caption')
                acts.append(dict(index=item['index'], sha256=item['sha256'], raw=raw, raw_sha256=focus.sha(raw.encode()),
                    request_sha256=item['document']['request_sha256'], finished_utc=stamp(item['document']['finished_unix']),
                    stage_index=stage['index'], stage_sha256=stage['sha256']))
        if item['kind'] == 'INBOX':
            message = item['document'].get('message', {})
            projection = dict(index=item['index'], sha256=item['sha256'], actor=message.get('actor'),
                speaker=message.get('speaker'), id=message.get('id'), source_sha256=item['document'].get('source_sha256'))
            if message.get('actor') == 'environment':
                tools.append(projection)
            if message.get('actor') == 'parent':
                parents.append(projection)
    result = dict(observed_utc=focus.utc(), identity=owner, loaded_index=loaded['index'], loaded_sha256=loaded['sha256'],
        journal_id=loaded['journal_id'], head=headers[-1], latest_act=acts[-1] if acts else None,
        visible_tool_receipts_metadata_only=tools[-4:], parent_inboxes=parents,
        tool_content_or_scores_exported=False, native_changes=0)
    if pending:
        inbox = next((item for item in selected.values() if item['kind'] == 'INBOX'
            and item['document'].get('message', {}).get('id') == pending['publication']['id']), None)
        if inbox:
            message = inbox['document']['message']
            focus.require(message['actor'] == 'parent' and message['speaker'] == 'Astra'
                and message['text'] == pending['text'] and message.get('source_receipt') is None
                and inbox['document']['source_sha256'] == pending['publication']['sha256'], 'actual_parent_inbox')
            result['inbox'] = dict(index=inbox['index'], sha256=inbox['sha256'])
            requests = []
            for header in headers:
                if header['kind'] != 'REQUEST' or header['index'] <= inbox['index']:
                    continue
                request = focus.checked_record(directory/f"{header['index']:020d}.json")
                document = request['document']
                if any(pending['text'] in message.get('content', '') for message in document['messages']):
                    focus.require(document['render_receipt']['all_history_tokens_masked'], 'external_parent_tokens_masked')
                    requests.append(dict(index=request['index'], sha256=request['sha256'], request_sha256=request_digest(document),
                        started_utc=stamp(document['started_unix']), prompt_tokens=document['prompt_tokens'], all_history_tokens_masked=True))
            if requests:
                result['render'] = requests[0]
                answer = next((act for act in acts if act['request_sha256'] in {request['request_sha256'] for request in requests}), None)
                if answer:
                    result['answer'] = answer
    return result


def main(request):
    operation = request['operation']
    focus.require(operation in ('poll', 'begin', 'publish'), 'parent_only_operation')
    if operation == 'poll':
        return inspect(request.get('pending'))
    if operation == 'begin':
        observation = inspect()
        focus.require(not observation['parent_inboxes'], 'no_existing_caption_parent_in_bounded_tail')
        epoch = dict(started_utc=focus.utc(), policy='R233_EXISTING_CAPTION_STRONG_PARENT_V1',
            preceding_unparented_history_immutable=True, preceding_history_is_not_this_parented_control=True,
            baseline={key: observation[key] for key in ('identity', 'head', 'loaded_index', 'loaded_sha256', 'journal_id')},
            historical_records_rewritten=0, learner_signals=0, new_gpu_or_birth=False)
        focus.write(EPOCH, epoch)
        return epoch
    epoch = focus.read(EPOCH)
    actual = identity()
    focus.require(actual['plan_sha256'] == epoch['baseline']['identity']['plan_sha256'], 'unchanged_existing_plan')
    text = request['text']
    focus.require(isinstance(text, str) and 0 < len(text.encode()) <= 4096 and len(text.split()) <= 90, 'bounded_parent_message')
    intent = focus.STORE/f"CAPTION_R233_PUBLISH_{request['number']:04d}.private.json"
    focus.write(intent, dict(created_utc=focus.utc(), text_sha256=focus.sha(text.encode()), no_automatic_retry=True))
    plan = focus.read(ROOT/'control/PLAN.json')
    sys.path.insert(0, plan['source_root'])
    from gpu.orch_r127_pilot_console import publish_parent
    publication = publish_parent(ROOT/'raw', 'Astra', text)
    return dict(published_utc=focus.utc(), publication=publication, text_sha256=focus.sha(text.encode()),
        source_actor='Astra parent', unchanged_tool_route=True, learner_signals=0)


if __name__ == '__main__':
    print(json.dumps(main(json.load(sys.stdin)), sort_keys=True))
