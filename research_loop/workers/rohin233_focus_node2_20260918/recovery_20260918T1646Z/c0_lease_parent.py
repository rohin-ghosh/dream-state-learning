"""Explicit lease-bound CPU publisher handoff; never control the learner."""

from datetime import datetime, timezone
import time

import c0_parent
from recover import LEASE_SOURCE, LEASE_SHA, read, require, sha


HORIZON = datetime(2026, 9, 20, 18, tzinfo=timezone.utc).timestamp()


def extend_source(source, floor):
    result = c0_parent.replacements_original(source, floor)
    seam = "deadline = min(plan['hard_end_unix'] - 60, time.time() + 21600)"
    require(result.count(seam) == 1, 'exact_existing_parent_deadline')
    return result.replace(seam, 'deadline = ' + repr(HORIZON - 60))


def main():
    require(sha(LEASE_SOURCE) == LEASE_SHA, 'original_authoritative_existing_lease')
    authority = read(LEASE_SOURCE)
    require(time.time() < HORIZON <= authority['hard_deadline_unix'] < authority['lease_end_unix'],
        'conservative_existing_lease_not_extension')
    c0_parent.OLD = c0_parent.HERE / 'C0_CURRICULUM'
    c0_parent.SERVICE = c0_parent.HERE / 'C0_CURRICULUM_LEASE'
    require((c0_parent.OLD / 'CANCEL_CURRICULUM_SERVICE').is_file(), 'supported_CPU_publisher_handoff')
    c0_parent.replacements_original = c0_parent.replacements
    c0_parent.replacements = extend_source
    c0_parent.serve(priority_topic='recall')


if __name__ == '__main__':
    main()
