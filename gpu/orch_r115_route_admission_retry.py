"""Preserve an admission-only failure before retrying unchanged route code."""

import argparse
import hashlib
import json
from pathlib import Path
import time


LANES = {'a100_2': 2, 'a100_3': 3, 'a100_6': 3}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(campaign, proc_root=Path('/proc')):
    require(not (campaign / 'LAUNCH.json').exists() and not (campaign / 'ACTOR_READY.json').exists(),
        'admission_only_no_native_launch')
    require(not (campaign / 'native.log').exists() and not list(campaign.glob('PARENT_*.json')),
        'no_native_or_parent_calls')
    require(not list((campaign / 'parent_queue').iterdir()), 'empty_recovery_parent_queue')
    require(read(campaign / 'TERMINAL.json')['status'] == 'FAILED', 'failed_admission_terminal')
    root = campaign.parent.parent
    failure = read(campaign / 'GUARDIAN_FAILED.json')['error']
    scanner_failed = failure.get('type') == 'CalledProcessError' and all(value in failure.get('message', '')
        for value in ('gpu.orch_r109_route_scan', "'scan'", str(root / 'SERVICE_IDENTITY.json')))
    require(failure == dict(type='ValueError', message='strict_privileged_clear') or scanner_failed,
        'exact_admission_failure')
    recipe = read(campaign / 'RECOVERY.json')
    require(sha(root / 'RESERVATIONS.jsonl') == recipe['old_reservations_sha256'], 'unchanged_charges')
    for directory in proc_root.glob('[0-9]*'):
        try:
            command = (directory / 'cmdline').read_bytes()
        except FileNotFoundError:
            continue
        require(not (b'gpu.orch_r111_route_recovery' in command and str(root).encode() in command),
            'old_recovery_process_still_alive')
    paths = [campaign / name for name in ('TERMINAL.json', 'GUARDIAN_FAILED.json', 'RELEASE.json')]
    paths.extend(sorted(campaign.glob('ADMISSION_*.json')))
    manifest = {path.name: sha(path) for path in paths}
    destination = campaign / 'admission_retry_r115_1034'
    destination.mkdir()
    with (destination / 'MANIFEST.json').open('x') as stream:
        json.dump(dict(preserved_unix=time.time(), files=manifest,
            recovery_recipe_sha256=sha(campaign / 'RECOVERY.json'),
            reservation_sha256=recipe['old_reservations_sha256'], native_calls=0,
            parent_calls=0, optimizer_updates=0, same_code_recipe_budget=True), stream, indent=2)
    for path in paths:
        path.rename(destination / path.name)
    require(all(sha(destination / name) == expected for name, expected in manifest.items()),
        'preserved_failed_evidence')
    return dict(archive=str(destination), preserved_files=len(manifest),
        recipe_sha256=sha(campaign / 'RECOVERY.json'), charges_unchanged=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', choices=LANES, required=True)
    lane = parser.parse_args().lane
    root = Path(f'/localhome/local-rohing/orch_r109_route_20260915_{lane}_attempt{LANES[lane]}')
    print(json.dumps(preserve(root / 'recovery_r113_v1' / ('campaign_' + lane))))
