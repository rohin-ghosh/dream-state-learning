"""Rebind the unchanged live sources after a local observer-host reboot."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time

import collector


def prepare_recovery():
    os.umask(0o077)
    config_path = collector.HERE / 'private/CONFIG.json'
    config = json.loads(config_path.read_text())
    prior = json.loads((collector.HERE / 'operator/PROCESS.json').read_text())
    observations = []
    for role, expected in (('original', config['old_process']), ('previous_observer', prior)):
        observed = collector.process(expected['pid'])
        if collector.same_process(observed, expected):
            raise ValueError(role + '_still_alive')
        observations.append(dict(role=role, expected=expected, observed=observed, same_live_identity=False))
    descriptors = collector.acquire_locks(config)
    try:
        archive = collector.HERE / 'private/recovery' / time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        collector.save(archive / 'CONFIG.json', config)
        collector.save(archive / 'PROCESS.json', prior)
        bound = [entry for entry in config['entries'] if entry.get('binding')]
        def probe(entry):
            return collector.remote(entry['binding'], [], probe=True)
        with ThreadPoolExecutor(max_workers=2) as workers:
            captured = list(workers.map(probe, bound))
        verified = []
        for entry, proof in zip(bound, captured):
            target = entry['binding']
            target.update({key: proof['identity'][key] for key in ('boot_id', 'source_manifest_sha256')})
            verified.append(dict(label=entry['label'], source_epoch_id=collector.epochs.source_epoch(entry['label'], target),
                identity=proof['identity'], loaded_sha256=proof['loaded_sha256'],
                owner_receipt_sha256=target['owner_receipt_sha256'], horizon_utc=collector.utc(target['until_unix'])))
        own_stat = os.fstat(descriptors[1])
        config['own_lock_identity'] = [own_stat.st_dev, own_stat.st_ino]
        config['source_pins'].update({name: collector.sha(collector.HERE / name) for name in
            ('collector.py', 'remote.py', 'epochs.py', 'recover.py', 'receipt.py')})
        config['recovered_utc'] = collector.utc(time.time())
        collector.save(config_path, config)
        boot_time = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
        collector.save(collector.HERE / 'public/RECOVERY_PREFLIGHT.json', dict(observed_utc=config['recovered_utc'],
            boot_id=collector.process(os.getpid())['boot_id'], host_boot_utc=collector.utc(boot_time),
            old_handles=observations, exact_fresh_bindings=verified, locks_free_before_start=True,
            lock_identities=[config['old_lock_identity'], config['own_lock_identity']],
            source_pins=config['source_pins'], config_sha256=collector.sha(config_path),
            caption_observation=dict(expected=config['caption_collector'], observed=collector.process(config['caption_collector']['pid']), actions=0),
            retention_rollout_deployed_by_observer=False, remote_writes=0, native_signals=0, model_calls=0,
            note='Disk Python-source manifest is an observed epoch boundary, not proof of loaded code or retention deployment. Old unversioned cursor/evidence remain preserved; fresh epoch starts its own queue.'))
        print(json.dumps(dict(fresh_bound_labels=[entry['label'] for entry in bound], config_sha256=collector.sha(config_path))))
    finally:
        for descriptor in descriptors:
            os.close(descriptor)


if __name__ == '__main__':
    prepare_recovery()
