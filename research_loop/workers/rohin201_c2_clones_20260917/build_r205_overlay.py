import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
TARGET = ROOT / 'r205_ready'
CHANGED = (
    'gpu/orch_r184_think_act_learn.py',
    'organism_v6/orch_r125_continual_stream.py',
    'gpu/orch_r125_cpu_experiment.py',
    'gpu/orch_r153_community_exchange.py',
    'gpu/orch_r153_community_transport.py',
    'tests/test_orch_r184_think_act_learn.py',
    'tests/test_orch_r125_cpu_experiment.py',
    'tests/test_orch_r153_community_exchange.py',
)


def main():
    if (TARGET / 'READY.json').exists():
        raise RuntimeError('Frozen release already exists')
    ready = json.loads((ROOT / 'r204_ready/READY.json').read_text())
    members = {}
    with tarfile.open(ROOT / 'r204_ready/runtime_overlay.tar.gz') as archive:
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
    ready.update(schema='R205_MAIN_TESTED_SOURCE_OVERLAY_V1',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        predecessor_archive_sha256=ready['archive_sha256'],
        archive_sha256=hashlib.sha256((TARGET / 'runtime_overlay.tar.gz').read_bytes()).hexdigest(),
        files={name: hashlib.sha256(data).hexdigest() for name, data in sorted(members.items())},
        cpu_validation=dict(stream_stage_hold_unittest=71, transport_exchange_cpu_pytest=142,
            result='PASS', counts_are_separate_invocations=True),
        original_C2='Same life at next exact complete boundary; preserve current state, all inboxes, working state and journal. No fabricated console turn or automatic redelivery.',
        console_reply='Fresh authenticated Rohin inbox gets a dedicated ACT prose reply before the requested ordinary stage; no tool dispatch, no claim of human receipt; eligible child words only under existing filters.',
        pinning_status='R206 full historical Rohin message pinning is not in this overlay; separate follow-up, do not delay direct reply repair.')
    ready['required_driver_options']['console_reply_policy'] = 'R205_CONSOLE_REPLY_ACT_V1'
    (TARGET / 'READY.json').write_text(json.dumps(ready, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(path=str(TARGET), files=len(members), archive_sha256=ready['archive_sha256'])))


if __name__ == '__main__':
    main()
