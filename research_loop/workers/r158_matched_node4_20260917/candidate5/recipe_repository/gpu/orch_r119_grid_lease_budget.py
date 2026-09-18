"""Prospective cumulative headroom without resetting historical GRID charges."""

import hashlib
import math


DIRECTIVE = 'only crash/lease wall ends life; explicitly logged prospective lease-budget headroom; cumulative used unchanged, no replay/reset'
HISTORICAL = {'NATIVE': 1858, 'PARENT': 298}
RATES = {'NATIVE': 16, 'PARENT': 4}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def counts(rows):
    require(all(row['kind'] in HISTORICAL for row in rows), 'known_charge_kind')
    result = {}
    for kind in HISTORICAL:
        numbers = [row['number'] for row in rows if row['kind'] == kind]
        require(numbers == list(range(1, len(numbers) + 1)), 'contiguous_cumulative_charges')
        result[kind] = len(numbers)
    return result


def authorize(*, root, ledger_bytes, rows, config_sha256, lease_end, hard_end, now):
    require(all(math.isfinite(value) for value in (lease_end, hard_end, now)), 'finite_clocks')
    require(now < hard_end <= lease_end - 21600, 'actual_lease_minus_margin')
    used = counts(rows)
    seconds = math.ceil(hard_end - now)
    return dict(schema='R119_GRID_LEASE_BUDGET_V1', root=str(root), directive=DIRECTIVE,
        config_sha256=config_sha256, historical_caps=dict(HISTORICAL), cumulative_used=used,
        ledger_prefix_bytes=len(ledger_bytes), ledger_prefix_sha256=hashlib.sha256(ledger_bytes).hexdigest(),
        authorized_unix=now, lease_end_unix=lease_end, hard_end_unix=hard_end,
        prospective_caps={kind: max(HISTORICAL[kind], used[kind]) + seconds * RATES[kind] + 1024
                          for kind in HISTORICAL},
        headroom_rate_per_second=dict(RATES), headroom_is_not_target_dose=True,
        optimizer_reset=False, counter_reset=False, final_calls_added=0,
        lifetime_cycle_limit=None, policy='continue_until_crash_or_lease_wall_no_budget_dose_target')


def validate(document, *, root, ledger_bytes, rows, config_sha256, lease_end, hard_end):
    require(document['schema'] == 'R119_GRID_LEASE_BUDGET_V1' and document['root'] == str(root), 'bound_life')
    require(document['config_sha256'] == config_sha256, 'original_CONFIG_unchanged')
    require(document['lease_end_unix'] == lease_end and document['hard_end_unix'] == hard_end,
            'no_lease_extension')
    length = document['ledger_prefix_bytes']
    require(len(ledger_bytes) >= length and hashlib.sha256(ledger_bytes[:length]).hexdigest()
            == document['ledger_prefix_sha256'], 'historical_charges_unchanged')
    used = counts(rows)
    expected = authorize(root=root, ledger_bytes=ledger_bytes[:length],
        rows=[row for row in rows if row['number'] <= document['cumulative_used'][row['kind']]],
        config_sha256=config_sha256, lease_end=lease_end, hard_end=hard_end,
        now=document['authorized_unix'])
    require(expected == document, 'exact_prospective_authorization')
    require(all(document['cumulative_used'][kind] <= used[kind] <= document['prospective_caps'][kind]
                for kind in HISTORICAL), 'monotone_cumulative_counters')
    return document['prospective_caps']
