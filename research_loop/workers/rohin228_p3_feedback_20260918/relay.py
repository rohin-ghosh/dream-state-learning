"""Source-bound Tool feedback relay; never scores or controls a learner."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from gpu.orch_r127_pilot_console import _inbox
from organism_v6.orch_r125_plain_context import has_scaffolding


POLICY = 'R228_ATTRIBUTED_CAPTION_FEEDBACK_V1'


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def load(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('bounded_regular_source_required')
    payload = path.read_bytes()
    return json.loads(payload), dict(path=str(path.resolve()), sha256=hashlib.sha256(payload).hexdigest())


def write_once(path, document):
    payload = json.dumps(document, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError('immutable_projection_changed')
        return
    temporary = path.with_suffix('.partial')
    with temporary.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()


def source_response(life, origin):
    record, reference = load(life / 'stream/records' / f"{origin['record_index']:020d}.json")
    if record['kind'] != 'RESPONSE' or record['sha256'] != origin['record_sha256'] or record['sha256'] != digest(
            {key: value for key, value in record.items() if key != 'sha256'}):
        raise ValueError('actual_child_response_required')
    return record['document']['response']['raw'], reference


def display(value):
    text = str(value)
    if has_scaffolding(text):
        return '[metadata-shaped text omitted from display; original retained in source receipt]'
    return text[:500] + (' [display truncated]' if len(text) > 500 else '')


def messages(document):
    report = document['report']
    origin = document['origin']
    header = (f"Caption-game judgment for your ACT response {origin['record_index']} "
        f"({origin['record_sha256'][:12]}). This reports an existing attempt, not a new submission.")
    sources = report.get('caption_sources', [])
    lines = []
    for ordinal, entry in enumerate(report.get('feedback', []), 1):
        result = entry.get('result', {})
        source_index = entry.get('caption_source_index')
        source = sources[source_index] if type(source_index) is int and 0 <= source_index < len(sources) else {}
        source_stage = source.get('stage', 'ACT')
        raw = (document.get('salvaged_THINK') or {}).get('raw', '') if source_stage == 'THINK' else document.get('raw_act', '')
        start, end = source.get('start'), source.get('end')
        text = None
        if type(start) is int and type(end) is int and 0 <= start < end <= len(raw):
            candidate = raw[start:end]
            if hashlib.sha256(candidate.encode()).hexdigest() != source.get('text_sha256'):
                raise ValueError('caption_span_hash_mismatch')
            text = candidate
        label = f"Caption {ordinal}, scene {display(entry.get('contest_id', 'not recorded'))}, source {source_stage}"
        if text is not None:
            label += ': ' + json.dumps(display(text), ensure_ascii=False)
        if result.get('ok') and type(result.get('accepted')) is bool:
            rank = result.get('rank')
            panel = result.get('reference_count')
            ranking = f'{rank}/{panel + 1}' if type(rank) is int and type(panel) is int else 'not recorded'
            line = (f"{label}\nRank {ranking}; accepted={str(result['accepted']).lower()}; "
                f"novelty={display(result.get('status', 'not recorded'))}; "
                f"cached={str(bool(result.get('replayed'))).lower()}.")
            if result.get('rejection_reason'):
                line += ' Reason: ' + display(result['rejection_reason']) + '.'
        else:
            line = label + '\nNo judgment: ' + display(result.get('error') or result.get('status') or
                report.get('error') or 'no valid per-caption score returned') + '.'
        lines.append(line)
    if not lines:
        reason = report.get('error') or report.get('format_metrics', {}).get('reason') or 'no scorable caption was identified'
        lines.append('No judgment: ' + display(reason) + '. No rank, acceptance or novelty is known for this attempt. '
            'Write the captions themselves for the scene you choose; do not wait for an unreported score.')
    output = [header + '\n' + '\n'.join(lines[start:start + 6]) for start in range(0, len(lines), 6)]
    if any(has_scaffolding('Tool: ' + text) for text in output):
        raise ValueError('feedback_must_survive_plain_context')
    return output


def publish(life, output, document, reference):
    raw, response = source_response(life, document['origin'])
    if 'raw_act' in document and document['raw_act'] != raw:
        raise ValueError('unaltered_child_ACT_required')
    publications = []
    for ordinal, text in enumerate(messages(document)):
        projection = dict(schema=POLICY, result=reference, response=response,
            chunk=ordinal, text=text, scoring_calls=0, original_result_unchanged=True)
        identifier = digest(projection)
        path = output / 'projections' / (identifier + '.json')
        write_once(path, projection)
        receipt_path = output / 'published' / (identifier + '.json')
        if receipt_path.exists():
            continue
        receipt = dict(path=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        existing = None
        for inbox in (life / 'stream/inbox').glob('*.json'):
            incoming, inbox_reference = load(inbox)
            if incoming.get('source_receipt') == receipt and incoming.get('text') == text:
                existing = dict(id=incoming['id'], **inbox_reference)
                break
        publication = existing or _inbox(life, 'Tool', text, receipt)
        saved = dict(policy=POLICY, publication=publication, result=reference,
            origin=document['origin'], chunk=ordinal, published_unix=time.time(),
            recovered_existing_inbox=existing is not None, learner_signals=[], scoring_calls=0)
        write_once(receipt_path, saved)
        publications.append(saved)
    return publications


def journal_paths(life):
    return sorted(path for path in (life / 'stream/records').glob('*.json')
        if path.stem.isdigit())


def initial_cursor(life, backfill_records=128):
    indices = [int(path.stem) for path in journal_paths(life)]
    return max(0, max(indices, default=0) - backfill_records)


def pending_results(sessions, processed):
    documents = []
    for root in sessions:
        for path in root.glob('attempts/*/RESULT.json'):
            status = path.stat()
            identity = (status.st_ino, status.st_size, status.st_mtime_ns)
            if path in processed:
                if processed[path] != identity:
                    raise ValueError('immutable_result_changed')
                continue
            document, reference = load(path)
            documents.append((document, reference, path, identity))
    return sorted(documents, key=lambda item: item[0].get('unix', 0))


def run(arguments):
    life, output = arguments.life.resolve(), arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for directory in ('projections', 'published'):
        (output / directory).mkdir(exist_ok=True)
    with (output / 'WRITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        cursor = initial_cursor(life)
        write_once(output / f'STARTED_{os.getpid()}.json', dict(policy=POLICY, pid=os.getpid(),
            life=str(life), started_unix=time.time(), end_unix=arguments.end_unix,
            poll_seconds=arguments.poll_seconds, learner_signals=[], scoring_calls=0,
            journal_start_after=cursor, historical_results_backfilled=True))
        processed = {}
        while True:
            for document, reference, path, identity in pending_results(arguments.session, processed):
                for receipt in publish(life, output, document, reference):
                    print(json.dumps(receipt, sort_keys=True), flush=True)
                processed[path] = identity
            records = journal_paths(life)
            for path in records:
                index = int(path.stem)
                if index <= cursor:
                    continue
                record, reference = load(path)
                if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
                    raise ValueError('journal_record_hash_mismatch')
                if record['kind'] == 'R184_ACT':
                    environment = record['document'].get('outcome', {}).get('environment', {})
                    if environment.get('report', {}).get('error') and not environment['report'].get('feedback'):
                        document = dict(environment, origin=record['document']['origin'])
                        for receipt in publish(life, output, document, reference):
                            print(json.dumps(receipt, sort_keys=True), flush=True)
                cursor = index
            if arguments.once or time.time() >= arguments.end_unix:
                return
            time.sleep(arguments.poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--life', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--session', action='append', required=True, type=Path)
    parser.add_argument('--end-unix', type=float, required=True)
    parser.add_argument('--poll-seconds', type=float, default=2)
    parser.add_argument('--once', action='store_true')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
