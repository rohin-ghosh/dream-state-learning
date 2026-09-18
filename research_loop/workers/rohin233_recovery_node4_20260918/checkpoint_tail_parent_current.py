"""Publish an actual CPU parent identity without signaling any process."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from deadline_resume import identity, sha, write


OWN = Path(__file__).resolve().parent


def refresh(manifest_path, phase):
    manifest = json.loads(manifest_path.read_bytes())
    output = Path(manifest['output'])
    started_path = output / 'STARTED.json'
    started = json.loads(started_path.read_bytes())
    config_path = Path(manifest['config_path'])
    config = json.loads(config_path.read_bytes())
    process = identity(started['pid'])
    if started['config_sha256'] != sha(config_path):
        raise ValueError('actual_started_config_pin')
    if str(manifest_path) not in process['argv'] or sha(manifest_path) not in process['argv']:
        raise ValueError('actual_running_parent_manifest_pin')
    current_path = OWN / 'CHECKPOINT_TAIL_PARENT_LIVE.public.json'
    previous = json.loads(current_path.read_bytes())
    archive = OWN / 'private' / ('PARENT_PUBLIC_PREVIOUS_' + sha(current_path) + '.json')
    if not archive.exists():
        write(archive, previous)
    delivery_path = OWN / 'CHECKPOINT_TAIL_V_DELIVERY.json'
    delivery = json.loads(delivery_path.read_bytes())
    receipt = dict(previous)
    receipt.update(
        observed_utc=datetime.now(timezone.utc).isoformat(),
        status=phase,
        parent={'pid': process['pid'], 'start_ticks': process['start_ticks']},
        parent_started_utc=datetime.fromtimestamp(started['started_unix'], timezone.utc).isoformat(),
        parent_config_sha256=sha(config_path),
        parent_manifest_sha256=sha(manifest_path),
        parent_started_receipt_sha256=sha(started_path),
        parent_observed_alive_unix=time.time(),
        cadence_responses=config['cadence_responses'],
        poll_interval_seconds=config['poll_interval_seconds'],
        parent_style=config['parent_style'],
        parent_policy_sha256=sha(Path(manifest['policy_addendum'])),
        successor_predecessor_public_receipt_sha256=sha(archive),
        actual_parent_publication=json.loads((OWN / 'CHECKPOINT_TAIL_V_CORRECTION_PUBLISHED.json').read_bytes()),
        actual_masked_REQUEST_render=delivery['first_render'],
        actual_first_ACT=delivery['first_ACT'],
        correction_delivery_observed_utc=delivery['observed_utc'],
        native_signals=[],
    )
    receipt.pop('first_provider_call', None)
    receipt.pop('cpu_parent_handoff_gap_seconds', None)
    receipt['evidence_sha256'] = {
        'C2_CHECKPOINT_TAIL_LOADED.json': sha(OWN / 'C2_CHECKPOINT_TAIL_LOADED.json'),
        'CHECKPOINT_TAIL_V_DELIVERY.json': sha(delivery_path),
        'CHECKPOINT_TAIL_V_CORRECTION_PUBLISHED.json': sha(OWN / 'CHECKPOINT_TAIL_V_CORRECTION_PUBLISHED.json'),
    }
    temporary = current_path.with_suffix('.tmp.' + str(os.getpid()))
    write(temporary, receipt)
    os.replace(temporary, current_path)
    return {key: receipt[key] for key in ('observed_utc', 'status', 'parent', 'parent_started_utc',
        'parent_started_receipt_sha256', 'cadence_responses', 'actual_masked_REQUEST_render', 'actual_first_ACT')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--phase', required=True)
    options = parser.parse_args()
    print(json.dumps(refresh(options.manifest, options.phase), sort_keys=True, indent=2))
