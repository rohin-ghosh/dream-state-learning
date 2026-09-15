"""Prospective broker custody for lease-budget eras; historical claims retained."""

import hashlib
from pathlib import Path


SOURCE_SHA = '0c38e16db0656b478acc11f75a3e119735fb5b0a9845bfb4a1d0db854cb0427d'


def source():
    path = Path(__file__).with_name('orch_r119_grid_parent.py')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('original_broker_bytes')
    text = raw.decode()
    pairs = {
        "('migration_a40r7_r119', 'learned_fork_r119')": "('lease_budget_r119_base', 'lease_budget_r119_learned')",
        "'R119_A40R7_CONTINUATION_TERMINAL.json',\n                                   'R119_LEARNED_GRID_TERMINAL.json'":
            "'R119_LEASE_BASE_TERMINAL.json',\n                                   'R119_LEASE_LEARNED_TERMINAL.json'",
        "'actual_native_ready_lease_margin')":
            "'actual_native_ready_lease_margin')\n    require(ready['parent_cap'] == config['max_parent_calls'] and ready.get('lease_budget'), 'explicit_lease_budget_broker_cap')",
    }
    for before, after in pairs.items():
        if text.count(before) != 1:
            raise ValueError('exact_broker_custody_delta')
        text = text.replace(before, after)
    return text


if __name__ == '__main__':
    exec(compile(source(), __file__, 'exec'), {'__name__': '__main__', '__file__': __file__})
