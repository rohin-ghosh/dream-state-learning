"""Freeze local historical judgments and bind only exact owner receipts."""

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import collector


HERE = Path(__file__).resolve().parent
ORIGINAL = collector.ORIGINAL


def horizon(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())


def prepare():
    os.umask(0o077)
    if (HERE / 'private/CONFIG.json').exists():
        raise ValueError('immutable_config_already_prepared')
    if collector.process(974386):
        raise ValueError('original_pid_requires_fresh_disposition')
    descriptor = os.open(ORIGINAL / 'operator/SINGLE_READER.lock', os.O_RDONLY | os.O_NOFOLLOW)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock_stat = os.fstat(descriptor)
    registry_path = ORIGINAL / 'private/TARGETS.json'
    registry = json.loads(registry_path.read_text())
    if len(registry) != 18 or len({row['root'] for row in registry if row.get('root')}) != 16:
        raise ValueError('registry_coverage_changed')
    horizons = {
        'node2': horizon('2026-09-20T18:00:00'),
        'node5': horizon('2026-09-20T18:00:00'),
        'node3': horizon('2026-09-24T18:00:00'),
        'node4': horizon('2026-09-25T18:00:00'),
        'ovx4': horizon('2026-09-30T17:59:30'),
    }
    receipts = {}
    for name, relative in (
        ('C2', 'rohin233_recovery_node4_20260918/C2_CHECKPOINT_TAIL_LOADED.json'),
        ('P3', 'rohin233_recovery_20260918/P3_RETRY_BINDING.json'),
        ('pair', 'post_recovery_pair_evidence_20260918/RUNTIME_BINDINGS.json'),
    ):
        source = HERE.parent / relative
        raw = source.read_bytes()
        receipts[name] = json.loads(raw)
        collector.save(HERE / 'private/owner_receipts' / (name + '.json'), receipts[name])
        receipts[name]['owner_receipt_sha256'] = collector.sha(source)
        if source.read_bytes() != raw:
            raise ValueError('owner_receipt_changed_during_capture')
    by_label = {row['label']: row for row in registry}
    c2 = receipts['C2']
    p3 = receipts['P3']
    bindings = {
        'C2': dict(root=c2['root'], journal_id=c2['journal_id'], pid=c2['native']['pid'],
            start_ticks=c2['native']['start_ticks'], source=c2['source_root'],
            guard_sha256=c2['guard_sha256'], loaded_index=c2['loaded']['index'],
            loaded_sha256=c2['loaded']['sha256'], until_unix=horizons['node5'],
            owner_receipt_sha256=c2['owner_receipt_sha256']),
        'GAME1_P3': dict(root=by_label['GAME1_P3']['root'], until_unix=horizons['node4'],
            **{key: p3[key] for key in ('journal_id', 'pid', 'start_ticks', 'source',
                'guard_sha256', 'loaded_index', 'loaded_sha256', 'owner_receipt_sha256')}),
    }
    for arm in receipts['pair']['arms']:
        label = {'learner': 'FRESH_R231', 'frozen': 'R232_SIBLING_FROZEN'}[arm['label']]
        bindings[label] = dict(root=arm['canonical_root'], source=arm['source_cwd'],
            until_unix=horizons['ovx4'], owner_receipt_sha256=receipts['pair']['owner_receipt_sha256'],
            **{key: arm[key] for key in ('journal_id', 'pid', 'start_ticks', 'guard_sha256',
                'loaded_index', 'loaded_sha256')})
        if Path(arm['logical_transport']).name != by_label[label]['wrapper']:
            raise ValueError('pair_transport_not_registered')
    entries = []
    imported = []
    for row in registry:
        label = row['label']
        entry = dict(label=label, registry_status=row.get('status'))
        if label in bindings:
            bound = bindings[label]
            if row['root'] != bound['root'] or (row.get('journal_id') and row['journal_id'] != bound['journal_id']):
                raise ValueError('owner_receipt_not_registered')
            bound['wrapper'] = row['wrapper']
            entry['binding'] = bound
        source_dir = ORIGINAL / 'private' / label
        if (source_dir / 'ANNOTATIONS.json').exists():
            pins = {}
            destination = HERE / 'private/history' / label
            destination.mkdir(parents=True, mode=0o700)
            for name in ('EVIDENCE.json', 'ANNOTATIONS.json'):
                source = source_dir / name
                before = collector.sha(source)
                destination.joinpath(name).write_bytes(source.read_bytes())
                if collector.sha(destination / name) != before or collector.sha(source) != before:
                    raise ValueError('historical_before_copy_after_mismatch')
                pins[name] = before
            collector.save(destination / 'PINS.json', pins)
            report, refs = collector.history(label)
            if label in bindings and len(refs) > 80:
                raise ValueError('historical_proof_exceeds_bounded_reader')
            imported.append(dict(label=label, pins=pins, reference_count=len(refs),
                best_previously_adjudicated_level=report['highest_verified_level']))
        entries.append(entry)
    caption = collector.process(4091776)
    if not caption or caption['start_ticks'] != '187238579' or caption['state'] == 'Z':
        raise ValueError('separate_caption_collector_identity_changed')
    source_pins = {name: collector.sha(HERE / name) for name in (
        'collector.py', 'remote.py', 'prepare.py', 'contract/audit.py', 'contract/reader.py', 'contract/review_queue.py')}
    config = dict(entries=entries, horizons=horizons, source_pins=source_pins,
        old_process=dict(pid=974386, start_ticks=183697151),
        old_lock_identity=[lock_stat.st_dev, lock_stat.st_ino], caption_collector=caption)
    collector.save(HERE / 'private/CONFIG.json', config)
    collector.save(HERE / 'public/PREFLIGHT.json', dict(observed_utc=collector.utc(__import__('time').time()),
        original_process_absent=True, original_exit=json.loads((ORIGINAL / 'operator/EXIT.json').read_text()),
        original_lock_free=True, original_lock_identity=config['old_lock_identity'],
        registry_sha256=collector.sha(registry_path), imported_manual_ledgers=imported,
        exact_bound_labels=sorted(bindings), source_pins=source_pins,
        conservative_observer_horizons={key: collector.utc(value) for key, value in horizons.items()},
        separate_caption_collector_untouched=caption, native_signals=0, model_calls=0, remote_writes=0))
    os.close(descriptor)
    print(json.dumps(dict(prepared=True, bound_labels=sorted(bindings), imported=len(imported))))


if __name__ == '__main__':
    prepare()
