import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
TARGET = ROOT / 'r206_ready'
CHANGED = (
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_plain_context.py',
    'gpu/orch_r184_think_act_learn.py',
    'gpu/orch_r194_console_reflection.py',
    'gpu/orch_r206_pinned_messages.py',
    'tests/test_orch_r124_train_history.py',
    'tests/test_orch_r184_think_act_learn.py',
    'tests/test_orch_r194_console_reflection.py',
)


def main():
    if (TARGET / 'READY.json').exists():
        raise RuntimeError('Frozen release already exists')
    ready = json.loads((ROOT / 'r205_ready/READY.json').read_text())
    members = {}
    with tarfile.open(ROOT / 'r205_ready/runtime_overlay.tar.gz') as archive:
        for entry in archive.getmembers():
            if entry.isfile():
                members[entry.name] = archive.extractfile(entry).read()
    for name in CHANGED:
        members[name] = (REPO / name).read_bytes()
    with tarfile.open(TARGET / 'runtime_overlay.tar.gz', 'w:gz') as archive:
        for name, data in sorted(members.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(data))
    ready.update(schema='R206_MAIN_TESTED_SOURCE_OVERLAY_V1',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        predecessor_archive_sha256=ready['archive_sha256'],
        archive_sha256=hashlib.sha256((TARGET / 'runtime_overlay.tar.gz').read_bytes()).hexdigest(),
        files={name: hashlib.sha256(data).hexdigest() for name, data in sorted(members.items())},
        cpu_validation=dict(history_stream_stage_hold_unittest=117,
            presentation_journal_native_pytest=152, subtests=214, result='PASS',
            known_preexisting_deselected='tests/test_orch_r125_plain_context.py::test_all_scaffolding_rows_skip_training_without_fabricating_progress (incomplete fixture plan: new_presentations)',
            predecessor_transport_exchange_cpu_pytest=142, counts_overlap=True),
        pinning_status='Source-hash-verified attributed Rohin inputs retained in full, once, alongside system/birth/working-state across compaction, eviction and sleep; old known inboxes backfilled without re-answering. No human target loss. Hold mode also pins.',
        pin_budget='Pinned messages count against the same pre-generation threshold. If protected content alone cannot fit, fail explicitly rather than truncate a vital message or exceed the threshold. No context-window increase.')
    ready['required_driver_options']['pinned_messages_policy'] = 'R206_VERBATIM_ROHIN_MESSAGES_V1'
    (TARGET / 'READY.json').write_text(json.dumps(ready, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(path=str(TARGET), files=len(members), archive_sha256=ready['archive_sha256'])))


if __name__ == '__main__':
    main()
