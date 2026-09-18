"""Summarize an existing bounded observation without reading private readouts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write


def timestamp(value):
    if value is None:
        return None
    moment = datetime.fromtimestamp(value, timezone.utc)
    return dict(unix=value, UTC=moment.isoformat(), PDT=moment.astimezone(ZoneInfo('America/Los_Angeles')).isoformat())


def summarize(path):
    raw = path.read_bytes()
    observation = json.loads(raw)
    result = dict(observed=timestamp(observation['observed_unix']), observation_path=str(path),
        observation_sha256=hashlib.sha256(raw).hexdigest(), copies={},
        first_tool_blocked_attempts_preserved_and_stopped=True,
        unused_lr32_pre_native_admission_failure_preserved=True,
        source_changes_to_running_copies=False, new_parent_launched_by_Ampere=False,
        complete_episode_encoder_integrated=False, learning_improvement_claim=False,
        node4_R187_status='MAIN_CODE_17_TESTS_PASS_AWAIT_GAUSS_SLOT_LEASE_AND_REAL_CPU_GATE',
        probe_release_status='NO_SLOT_RELEASED_NATIVE_EXIT_AND_FRESH_CLEAR_REQUIRED')
    for label, copy in observation['copies'].items():
        loaded = next((item for item in copy['events'] if item['kind'] == 'LOADED'), {})
        act = next((item for item in copy['events'] if item['kind'] == 'R184_ACT'), {})
        updates = [item for item in copy['events'] if item['kind'] == 'UPDATE']
        result['copies'][label] = dict(base=copy['base'], native=copy['native'], plan=copy['plan'],
            source_manifest_sha256=copy['source_manifest_sha256'], source_file_count=copy['source_file_count'],
            source_pins_unchanged=copy['source_pins_unchanged'], loaded=timestamp(loaded.get('loaded_unix')),
            loaded_record_sha256=loaded.get('record_sha256'), actual_plasticity=loaded.get('plasticity'),
            first_ACT=dict(persisted=timestamp(act.get('persisted_unix')), outcome=act.get('outcome'),
                record_sha256=act.get('record_sha256')),
            first_optimizer_update=timestamp(updates[0]['finished_unix']) if updates else None,
            latest_observed_optimizer_step=updates[-1]['optimizer_step'] if updates else None,
            confinement_CPU_receipt=copy['receipts'].get('control/CONFINEMENT_CPU.json'),
            failure_or_exit_receipts={name: receipt for name, receipt in copy['receipts'].items()
                if 'FAILED' in name or 'EXIT' in name})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('observation', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(write(arguments.output, summarize(arguments.observation)), sort_keys=True))
