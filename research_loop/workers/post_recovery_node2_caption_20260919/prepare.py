"""Exact original-source overlay preparation; templates confer no admission."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from verify_saved import BASE, GUARD_SHA, PLAN_SHA, require


HERE = Path(__file__).resolve().parent
NEW_SOURCE = BASE / 'source_checkpoint_tail_20260919_v2'
NEW_CONTROL = BASE / 'control_checkpoint_tail_20260919_v2'
READER_SHA = '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e'
SEAM = b'        runtime.ControlJournal = journal_type(plan)\n'
ADDITION = (b'        from gpu.caption_tail_runtime import bind_journal\n'
    b'        runtime.ControlJournal = bind_journal(runtime.ControlJournal, plan)\n')


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def publish(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)


def document(path, value):
    publish(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def selection(root):
    return dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(root),
        journal_id='1840899d7847437093d41eae072b8d26', complete_index=8527,
        complete_sha256='9bce737fd97a81cb8bee4a0be486db7ee9ae633887e90ab614d04f7d55fce430',
        life_id='R226_CAPTION_UNPARENTED', max_tail_records=4096, max_tail_bytes=512 * 1024 * 1024,
        sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)],
        persist_complete_anchors=False)


def plan_template(old):
    plan = deepcopy(old)
    authorization = plan.pop('authorized_wall_extension')
    require(authorization['new_deadline_unix'] == plan['hard_end_unix'] == 1789927200,
        'same_deadline_consumed_authorization_candidate_only')
    plan['source_root'] = str(NEW_SOURCE)
    plan['startup_context']['path'] = str(NEW_SOURCE / 'context/R205_STARTUP.md')
    plan['checkpoint_tail_recovery'] = selection(Path(plan['root']) / 'stream')
    return plan


def main():
    require(checksum((HERE / 'original/GUARD.json').read_bytes()) == GUARD_SHA, 'original_guard_pin')
    require(checksum((HERE / 'original/PLAN.json').read_bytes()) == PLAN_SHA, 'original_plan_pin')
    guard = json.loads((HERE / 'original/GUARD.json').read_bytes())
    old_plan = json.loads((HERE / 'original/PLAN.json').read_bytes())
    reader = (HERE.parent / 'rohin233_recovery_node4_20260918/checkpoint_tail_runtime.py').read_bytes()
    require(checksum(reader) == READER_SHA, 'tested_reader_exact_preimage')
    blobs = {}
    for name, expected in guard['source_pins'].items():
        content = (HERE / 'original/source' / name).read_bytes()
        require(checksum(content) == expected, 'original_source_pin:' + name)
        blobs[name] = content
    require(blobs['gpu/r233_node2_recovery.py'].count(SEAM) == 1, 'one_exact_install_seam')
    blobs['gpu/r233_node2_recovery.py'] = blobs['gpu/r233_node2_recovery.py'].replace(SEAM, SEAM + ADDITION)
    blobs['gpu/checkpoint_tail_runtime.py'] = reader
    blobs['gpu/caption_tail_runtime.py'] = (HERE / 'caption_tail_runtime.py').read_bytes()
    context = (HERE / 'STARTUP_ORIGINAL.md').read_bytes()
    require(checksum(context) == old_plan['startup_context']['sha256'], 'startup_context_unchanged')
    blobs['context/R205_STARTUP.md'] = context
    prepared = HERE / 'prepared_v2'
    require(not prepared.exists(), 'never_overwrite_prepared_epoch')
    for name, content in blobs.items():
        publish(prepared / 'source' / name, content)
    pins = {name: checksum(content) for name, content in sorted(blobs.items()) if name.endswith('.py')}
    delta = {name: dict(before=guard['source_pins'].get(name), after=after)
        for name, after in pins.items() if after != guard['source_pins'].get(name)}
    require(set(delta) == {'gpu/r233_node2_recovery.py', 'gpu/checkpoint_tail_runtime.py',
        'gpu/caption_tail_runtime.py'}, 'minimal_three_file_reader_only_delta')
    plan = plan_template(old_plan)
    document(prepared / 'PLAN_CANDIDATE.json', plan)
    document(prepared / 'GUARD_REQUIREMENTS.json', dict(schema='NOT_AN_EXECUTABLE_GUARD_V1',
        derivable=dict(schema=guard['schema'], source_pins=pins, host_sha256=guard['host_sha256'],
            copy_raw=guard['copy_raw'], resume=True, hard_end_unix=plan['hard_end_unix'],
            next_reserved_unix=guard['next_reserved_unix'], attempt_dir=str(NEW_CONTROL),
            plan_path=str(NEW_CONTROL / 'PLAN.json'), plan_sha256=checksum((prepared / 'PLAN_CANDIDATE.json').read_bytes())),
        required_fresh=['allocation_path', 'allocation_sha256', 'lease_path', 'lease_sha256',
            'CPU provenance over this exact closure', 'Builder entry', 'original privileged admission',
            'original confinement/device checks', 'unused one-shot control directory',
            'capacity and failed readout reconciliation by main'],
        old_guard_reusable=False, approved=False, launch_ready=False))
    document(prepared / 'MANIFEST.json', dict(schema='CAPTION_READER_SOURCE_OVERLAY_V1',
        original_guard_sha256=GUARD_SHA, original_plan_sha256=PLAN_SHA,
        source=str(NEW_SOURCE), control=str(NEW_CONTROL), source_pins=pins, delta=delta,
        all_files={name: checksum(content) for name, content in sorted(blobs.items())},
        same_deadline=plan['hard_end_unix'], reader_sha256=READER_SHA,
        prefix_work='FULL_RAW_BYTE_HASH_NO_HISTORICAL_BODY_REPLAY',
        original_admission_unchanged=True, launch_ready=False))
    for path in prepared.rglob('*'):
        if path.is_file():
            path.chmod(0o444)
    for path in sorted((path for path in prepared.rglob('*') if path.is_dir()),
            key=lambda path: len(path.parts), reverse=True):
        path.chmod(0o555)
    prepared.chmod(0o555)
    print(json.dumps(dict(prepared=str(prepared), python_files=len(pins), delta=delta)))


if __name__ == '__main__':
    main()
