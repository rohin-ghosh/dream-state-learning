"""Explicit CPU-only lease renewal, separate from the resident native wall."""

import json
from pathlib import Path
import time


WALL = 1790359200


def cpu_horizon(path=None, now=None):
    path = Path(path) if path is not None else Path(__file__).with_name('LEASE_AUTHORITY.json')
    document = json.loads(path.read_bytes())
    if (document['policy'] != 'R233_USER_REPORTED_DATE_ONLY_LEASE_MARGIN_V1'
            or document['node4_cpu_hard_end_unix'] != WALL
            or document['safety_margin_seconds'] != 21600
            or document['native_deadline_changed'] is not False
            or document['native_signals'] or document['training_policy_changes']):
        raise ValueError('exact_CPU_only_user_lease_authority')
    if (time.time() if now is None else now) >= WALL:
        raise ValueError('CPU_lease_safety_bound_expired')
    return WALL
