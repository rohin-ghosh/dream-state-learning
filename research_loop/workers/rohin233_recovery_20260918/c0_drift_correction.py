"""One operator-parent language self-check; no row filtering or life control."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path('/localhome/local-rohing/orch_r216_C0_20260918_attempt2')
SOURCE = ROOT / 'source_r233_lease_continuation'
OUTPUT = ROOT / 'r233_language_self_check_20260918T2031Z'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def cjk_count(text):
    return sum('\u3400' <= character <= '\u9fff' for character in text)


def make_text(quote):
    return ('Language self-check on your own recent reply. You wrote ' + json.dumps(quote, ensure_ascii=False)
        + '. Notice the shift into Chinese. Keep the same idea and the same math or reading object; '
        'write that content now in English. Do not promise a translation: provide the actual answer or paragraph. '
        'Then say briefly what changed in your language and how you checked it. '
        'This is a request for your own correction, not a row-exclusion rule.')


def main():
    process = Path('/proc/881309')
    fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    if fields[19] != '98332476' or fields[0] in ('Z', 'X'):
        raise ValueError('same_current_C0_native_required')
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r127_pilot_console import publish_parent
    from organism_v6.orch_r125_plain_context import has_scaffolding

    records = ROOT / 'raw/stream/records'
    responses = []
    for path in reversed(sorted(records.glob('[0-9]' * 20 + '.json'))):
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 4096))
            tail = stream.read()
        position = tail.rfind(b',"index":')
        if position < 0:
            raise ValueError('canonical_record_header')
        metadata = json.loads(b'{' + tail[position + 1:])
        if metadata['kind'] != 'RESPONSE':
            continue
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError('bounded_child_response')
        record = json.loads(path.read_bytes())
        if (record['journal_id'] != 'e0c3b033023e43c7a3dfa494d68011af'
                or digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']):
            raise ValueError('exact_C0_response_source')
        document = record['document']
        text = document['response']['raw']
        if not isinstance(text, str):
            raise ValueError('literal_child_response_text_required')
        responses.append(dict(index=record['index'], sha256=record['sha256'],
            cjk=cjk_count(text), characters=len(text), text=text))
        if len(responses) == 3:
            break
    candidates = [entry for entry in responses if entry['cjk']]
    if not candidates:
        raise ValueError('no_current_CJK_evidence_do_not_invent_drift')
    latest = candidates[0]
    start = next(index for index, character in enumerate(latest['text']) if cjk_count(character))
    quote = latest['text'][start:start + 120]
    text = make_text(quote)
    if has_scaffolding(text):
        raise ValueError('plain_parent_turn_required')
    intent = dict(text=text, speaker='Astra', operator_parent_turn=True,
        authority='User September18 20:26 C0 language self-check, no exclusions',
        source_responses=[{key: value for key, value in entry.items() if key != 'text'} for entry in responses],
        created_utc=datetime.now(timezone.utc).isoformat(), row_filters_changed=False,
        native_signals=[], raw_other_history_exported=False)
    OUTPUT.mkdir(mode=0o700, exist_ok=False)
    with (OUTPUT / 'INTENT.json').open('x') as stream:
        json.dump(intent, stream, ensure_ascii=False, sort_keys=True, indent=2)
    publication = publish_parent(ROOT / 'raw', 'Astra', text)
    receipt = dict(intent, publication=publication, rendered=False, child_correction_observed=False)
    with (OUTPUT / 'PUBLISHED.json').open('x') as stream:
        json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
