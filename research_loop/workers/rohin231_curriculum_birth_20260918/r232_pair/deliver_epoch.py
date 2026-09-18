"""Symmetric later Tool epoch; no native signals or retroactive birth edits."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time


LEARNER = Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')
FROZEN = Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    sys.path.insert(0, str(LEARNER / 'source'))
    from gpu.orch_r125_stream_journal import _digest
    from gpu.orch_r127_pilot_console import _inbox
    source = json.loads((FROZEN / 'EPOCH_SOURCE.json').read_bytes())
    paragraph = (FROZEN / 'EXPLORATION_PARAGRAPH.txt').read_text()
    assert hashlib.sha256(paragraph.encode()).hexdigest() == source['added_paragraph_sha256']
    text = ('R232 exploration curriculum — a later environment epoch, not a replacement of your '
        'original birth prompt. Source: authorized birth document revision f236ffa32. This guidance '
        'stays inside THINK; it adds no stage, tool, answer or claimed result.\n\n' + paragraph)
    observed, all_records = {}, {}
    for name, root in (('learner', LEARNER), ('frozen', FROZEN)):
        assert sha(root / 'BIRTH_PROMPT.txt') == source['original_birth_sha256']
        manifest = json.loads((root / 'raw/stream/JOURNAL.json').read_bytes())
        previous = _digest(manifest)
        records = []
        for index, path in enumerate(sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())):
            record = json.loads(path.read_bytes())
            assert record['index'] == index and record['previous_sha256'] == previous
            assert record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'})
            previous = record['sha256']
            records.append(record)
        loaded = [record for record in records if record['kind'] == 'LOADED']
        assert len(loaded) == 1
        assert any(record['kind'] == 'SLEEP_REQUEST' for record in records), 'later_epoch_not_initial_prompt'
        latest_phase = next(record['kind'] for record in reversed(records) if record['kind'] in ('REQUEST', 'SLEEP_REQUEST'))
        assert latest_phase == 'SLEEP_REQUEST', 'publish_only_during_current_sleep_or_readout_not_inflight_stage'
        pid = loaded[0]['document']['pid']
        assert (Path('/proc') / str(pid) / 'cmdline').exists()
        observed[name] = dict(journal_id=manifest['journal_id'], loaded=loaded[0],
            cut_record_index=records[-1]['index'], cut_record_sha256=previous,
            update_receipts=sum(record['kind'] == 'UPDATE' for record in records),
            completed_sleeps=sum(record['kind'] == 'SLEEP_COMPLETE' for record in records),
            actual_child_generated_tokens=sum(len(record['document']['response'].get('token_ids', []))
                for record in records if record['kind'] == 'RESPONSE'),
            snapshot_unix=time.time(), native_pid=pid)
        all_records[name] = records
    frozen_loaded_unix = observed['frozen']['loaded']['document']['loaded_unix']
    before = [record for record in all_records['learner'] if record['kind'] == 'UPDATE'
              and record['document']['finished_unix'] <= frozen_loaded_unix]
    observed['learner']['updates_completed_before_frozen_LOADED'] = len(before)
    observed['learner']['last_pre_pair_UPDATE'] = (dict(index=before[-1]['index'], sha256=before[-1]['sha256'],
        optimizer_step=before[-1]['document']['optimizer_step'], finished_unix=before[-1]['document']['finished_unix']) if before else None)
    publications = {}
    for name, root in (('learner', LEARNER), ('frozen', FROZEN)):
        directory = root / 'r232_epoch'
        directory.mkdir(exist_ok=False)
        source_path = directory / 'SOURCE.json'
        source_path.write_text(json.dumps(source, sort_keys=True, indent=2) + '\n')
        (directory / 'MESSAGE.txt').write_text(text)
        receipt = _inbox(root / 'raw', 'Tool', text, dict(path=str(source_path), sha256=sha(source_path)))
        publications[name] = dict(publication=receipt, delivered_unix=time.time(), text_sha256=sha(directory / 'MESSAGE.txt'),
            source_sha256=sha(source_path), actor='environment', speaker='Tool')
        (directory / 'PUBLICATION.json').write_text(json.dumps(publications[name], sort_keys=True, indent=2) + '\n')
    result = dict(schema='R232_SYMMETRIC_LATER_EPOCH_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        source=source, before_publication=observed, publications=publications,
        loaded_stagger_seconds=frozen_loaded_unix - observed['learner']['loaded']['document']['loaded_unix'],
        original_births_unchanged=True, native_signals=0, first_rendered_requests='PENDING_ACTUAL_RECEIPTS')
    with (FROZEN / 'EPOCH_PUBLICATION.json').open('x') as output:
        json.dump(result, output, indent=2, sort_keys=True)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
