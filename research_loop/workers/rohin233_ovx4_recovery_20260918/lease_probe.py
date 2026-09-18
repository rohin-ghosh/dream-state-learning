"""Lease-aware admission for unchanged finite, parent-free age evaluation."""

import argparse
import hashlib
import json
from pathlib import Path
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    config=json.loads(parser.parse_args().config.read_bytes())
    if not time.time()<config['deadline_unix']<=config['lease_boundary_unix']-21600:
        raise ValueError('six_hour_lease_margin')
    if (config['mode'],config['physical']) not in (('player',4),('judge',5)):
        raise ValueError('actual_vacated_owned_slots_only')
    root=Path(config['root'])
    manifest=json.loads((root/'SOURCE_MANIFEST.json').read_bytes())
    if any(hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()!=checksum for name,checksum in manifest.items()):
        raise ValueError('frozen_probe_source_bytes')
    from research_loop.workers.rohin233_kept_age_probe_20260918 import probe
    from research_loop.workers.rohin232_age_probe_20260918 import runtime
    identity=probe.same_battery(root)
    if not json.loads((root/'FRESHNESS_VERIFIED.json').read_bytes())['eligible'] or identity['source_parent_text_loaded']:
        raise ValueError('fresh_parent_free_source')
    runtime.write(root/(config['mode']+'_DEVICE_PROOF.json'),runtime.device_proof(config['physical']))
    runtime.write(root/(config['mode']+'_LEASE_ADMITTED.json'),dict(unix=time.time(),
        deadline_unix=config['deadline_unix'],physical=config['physical'],mode=config['mode'],
        fixed_battery_unchanged=True,source_context_loaded=False,scientific_token_limit_unchanged=True))
    (probe.player if config['mode']=='player' else probe.judge)(root,config['deadline_unix'])


if __name__ == '__main__':
    main()
