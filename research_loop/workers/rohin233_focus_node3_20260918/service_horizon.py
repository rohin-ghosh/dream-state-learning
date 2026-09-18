"""Explicit CPU-service budget, independent of resident native alarm deadlines."""

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

from retirement import PROTECTED


CEILING = datetime(2026, 9, 24, 18, tzinfo=timezone.utc).timestamp()


def service_deadline(root, requested, legacy):
    if requested is None:
        return legacy
    if not math.isfinite(requested) or not time.time() + 60 < requested <= CEILING:
        raise ValueError('explicit_finite_authorized_CPU_service_horizon_required')
    for name in PROTECTED:
        active = json.loads((root / name / 'ACTIVE_RUNTIME.json').read_bytes())
        control = Path(active['control'])
        if control.parent.resolve() != (root / name).resolve():
            raise ValueError('exact_kept_life_control_required')
        plan = json.loads((control / 'PLAN.json').read_bytes())
        guard = json.loads((control / 'GUARD.json').read_bytes())
        if requested > min(plan['lease_end_unix'], guard['next_reserved_unix']) - 21600:
            raise ValueError('unchanged_physical_lease_and_reservation_margin_required')
    return requested
