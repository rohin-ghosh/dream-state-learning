"""Bounded C0-only observation and one explicit operator-authored parent brief."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r216_C0_20260918_attempt2')
RECEIPTS = Path('/localhome/local-rohing/orch_r225_c0_colleague_receipts_20260918')
PID = 2561156
START_TICKS = 94173182
GPU_UUID = 'GPU-d304a15c-516a-16a0-a926-a560304077cc'
LOADED_SHA = 'bfd5c0cce84abe72354adbe87de1916906be968db9c75ce108e7383c3834f1f9'
ACT_SHA = '89afc04145edd2d5f939b37bb63bb7dc9b401401ae73c3b22b61a64df92e92cb'
EXCERPT = r'S_n = \sum_{i=1}^{n} (2ni - 1)'
BRIEF = (
    'Astra, with a colleague-style question rather than an answer: You are C0, '
    'the separate snapshot51 descendant, not the continuing original C2. '
    'What question do you actually want to investigate now, and what do you '
    'need to ask me before you can make progress? Your ACT at source record597 '
    'wrote this exact expression: ' + EXCERPT + '. '
    'If that is still your object, what does your written summation give for '
    'one small input you choose? Does it enumerate the terms you intended? '
    'Ask yourself which part has been demonstrated and which is only asserted; '
    'show one actual check rather than restating the conclusion. If you have '
    'already chosen a different object, probe its weakest step instead. '
    'Ask one genuine follow-up question in your reply; I will not supply the '
    'solution for you. After this one check, choose whether to continue or quit '
    'and name the next question, rather than repeat an unchanged attempt. '
    'Use English; if your own notation or wording is unclear, identify it and '
    'check it. No code executor is connected, so distinguish a hand calculation '
    'from a tool result. This is an attributed parent suggestion, not evidence '
    'that an answer is correct and not a replacement for your own reasoning.'
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def utc(unix):
    return datetime.fromtimestamp(unix, timezone.utc).isoformat()


def checked_record(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 32 * 1024**2,
            'bounded_regular_record')
    raw = path.read_bytes()
    record = json.loads(raw)
    require(record['index'] == int(path.stem) and record['sha256'] == sha(canonical(
        {key: value for key, value in record.items() if key != 'sha256'})), 'actual_record_hash')
    return record


def identity():
    plan = json.loads((ROOT / 'control/PLAN.json').read_bytes())
    require(plan['physical'] == 4 and plan['gpu_uuid'] == GPU_UUID, 'protected_C0_slot')
    loaded = checked_record(ROOT / 'raw/stream/records/00000000000000000001.json')
    require(loaded['sha256'] == LOADED_SHA and loaded['document']['pid'] == PID, 'exact_C0_loaded')
    fields = Path(f'/proc/{PID}/stat').read_text().rsplit(')', 1)[1].split()
    command = Path(f'/proc/{PID}/cmdline').read_bytes().split(b'\0')
    require(int(fields[19]) == START_TICKS and b'gpu.r216_c0_runtime' in command
            and str(ROOT / 'control/GUARD_PUBLISHED.json').encode() in command,
            'same_native_identity_not_reused_PID')
    return dict(pid=PID, start_ticks=START_TICKS, process_state=fields[0], physical_gpu=4,
        gpu_uuid=GPU_UUID, loaded_index=1, loaded_sha256=LOADED_SHA,
        loaded_utc=utc(loaded['document']['loaded_unix']), journal_id=loaded['journal_id'],
        guard_sha256=sha((ROOT / 'control/GUARD_PUBLISHED.json').read_bytes()),
        adapter_at_load=loaded['document']['adapter_sha256'], node='node2', root=str(ROOT))


def response_receipt(record, records):
    document = record['document']
    source_sha = sha(canonical(document))
    following = [item for item in records if record['index'] < item['index'] <= record['index'] + 32]
    stage = next((item for item in following if item['kind'] == 'R184_STAGE'
                  and item['document'].get('source_sha256') == source_sha), None)
    raw = document['response']['raw']
    require(isinstance(raw, str) and len(raw.encode()) <= 65536, 'bounded_actual_raw')
    return dict(index=record['index'], record_sha256=record['sha256'], source_document_sha256=source_sha,
        raw=raw, raw_sha256=sha(raw.encode()), finished_utc=utc(document['finished_unix']),
        stage=stage['document']['stage'] if stage else 'UNVERIFIED',
        stage_index=stage['index'] if stage else None, stage_sha256=stage['sha256'] if stage else None)


def observe():
    owner = identity()
    paths = sorted((ROOT / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))[-192:]
    require(sum(path.stat().st_size for path in paths) <= 256 * 1024**2, 'bounded_tail_bytes')
    records = [checked_record(path) for path in paths]
    for previous, record in zip(records, records[1:]):
        require(record['index'] == previous['index'] + 1 and record['previous_sha256'] == previous['sha256']
                and record['journal_id'] == previous['journal_id'] == owner['journal_id'], 'contiguous_current_tail')
    outputs = [response_receipt(record, records) for record in records if record['kind'] == 'RESPONSE']
    result = dict(observed_utc=utc(time.time()), identity=owner, read_limit_records=192,
        last_record={key: records[-1][key] for key in ('index', 'kind', 'sha256')},
        last_three_outputs=outputs[-3:], latest_ACT=next((item for item in reversed(outputs)
            if item['stage'] == 'ACT'), None), learner_controls=0, model_calls=0,
        brief_text_sha256=sha(BRIEF.encode()), brief_publication=None, brief_render=None)
    publication_path = RECEIPTS / 'PUBLISHED.json'
    if publication_path.exists():
        publication = json.loads(publication_path.read_bytes())
        result['brief_publication'] = publication
        for record in records:
            if record['kind'] == 'INBOX' and record['document'].get('source_sha256') == publication['publication']['sha256']:
                result['brief_inbox'] = {key: record[key] for key in ('index', 'kind', 'sha256')}
            if record['kind'] == 'REQUEST' and any(BRIEF in str(message.get('content', ''))
                    for message in record['document'].get('messages', [])):
                result['brief_render'] = dict(index=record['index'], record_sha256=record['sha256'],
                    started_utc=utc(record['document']['started_unix']),
                    prompt_tokens=record['document'].get('prompt_tokens'),
                    all_history_tokens_masked=record['document'].get('render_receipt', {}).get('all_history_tokens_masked'),
                    exact_complete_text_present=True)
                break
    return result


def publish():
    owner = identity()
    record = checked_record(ROOT / 'raw/stream/records/00000000000000000597.json')
    require(record['sha256'] == ACT_SHA and EXCERPT in record['document']['response']['raw'],
            'literal_child_excerpt_not_invented')
    RECEIPTS.mkdir(mode=0o700, exist_ok=True)
    with (RECEIPTS / 'ATTEMPT.json').open('x') as stream:
        json.dump(dict(unix=time.time(), identity=owner, brief=BRIEF, no_automatic_retry=True), stream)
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    publication = publish_parent(ROOT / 'raw', 'Astra', BRIEF)
    result = dict(published_utc=utc(time.time()), publication=publication,
        source_record_index=597, source_record_sha256=ACT_SHA, brief=BRIEF,
        brief_sha256=sha(BRIEF.encode()), operator_authored=True, learner_signals=0,
        parent_process_reconfigured=False, rendered=False)
    with (RECEIPTS / 'PUBLISHED.json').open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('observe', 'publish'))
    arguments = parser.parse_args()
    print(json.dumps(observe() if arguments.mode == 'observe' else publish(), sort_keys=True, indent=2))
