"""Resume the same C0 parent ledger only after its new native really loads."""

import time

import c0_parent
from c0_lease_parent import HORIZON
from observe import observation
from recover import LEASE_SOURCE, LEASE_SHA, locations, read, require, sha


def main(previous_directory=None, service_directory=None):
    root, _, _, _ = locations('C0')
    require(sha(LEASE_SOURCE) == LEASE_SHA and HORIZON <= read(LEASE_SOURCE)['hard_deadline_unix'], 'same_existing_lease')
    old = read(root / 'control_r233_lease_continuation/OLD_IDENTITY.json')
    limit = time.time() + 1800
    while time.time() < limit:
        observed = observation('C0')
        if observed['status'] == 'LOADED' and observed['native']['pid'] != old['pid']:
            break
        time.sleep(2)
    else:
        raise ValueError('new_C0_LOAD_not_observed_no_duplicate_publisher')
    c0_parent.OLD = previous_directory or c0_parent.HERE / 'C0_CURRICULUM_LEASE'
    c0_parent.SERVICE = service_directory or c0_parent.HERE / 'C0_CURRICULUM_AFTER_CONTINUATION'
    original = c0_parent.replacements

    def replace(source, floor):
        result = original(source, floor)
        seam = "deadline = min(plan['hard_end_unix'] - 60, time.time() + 21600)"
        require(result.count(seam) == 1, 'same_curriculum_horizon_seam')
        return result.replace(seam, 'deadline = ' + repr(HORIZON - 60)).replace(
            "ROOT/'control_r233_recovery/PLAN.json'", "ROOT/'control_r233_lease_continuation/PLAN.json'").replace(
            "ROOT/'source_r233_recovery'", "ROOT/'source_r233_lease_continuation'")

    c0_parent.replacements = replace
    c0_parent.serve()


if __name__ == '__main__':
    main()
