"""Lease-clock A4 broker custody without touching frozen shared owner sources."""

import hashlib
from pathlib import Path


PIN = '0c38e16db0656b478acc11f75a3e119735fb5b0a9845bfb4a1d0db854cb0427d'


def source():
    path = Path(__file__).with_name('orch_r119_grid_parent.py')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('immutable_HTTP_parent_source')
    text = raw.decode()
    changes = {
        "choices=('a40r', 'ovx2')": "choices=('ovx3',)",
        "('migration_a40r7_r119', 'learned_fork_r119')": "('shared_continuation_r119',)",
        "('R119_A40R7_CONTINUATION_TERMINAL.json',\n                                   'R119_LEARNED_GRID_TERMINAL.json')": "('R119_GRID_SHARED_TERMINAL.json',)",
        "config['remote_root'].startswith('/localhome/local-rohing/orch_r118_node3_')":
            "config['remote_root'] == '/localhome/local-rohing/orch_r115_grid_pair_20260915/A4'",
        "    strong_source = inspect.getsource(astra.existing.strong)":
            "    require(args.after_parent == 40 and config['life_id'] == 'F4_ASTRA' and config['max_parent_calls'] == 298, 'preserved_A4_pending_caps')\n"
            "    store = Store(transport.ROOT)\n"
            "    for reference in ready['startup_bindings'].values():\n"
            "        require(store.hash(Path(reference['path'])) == reference['sha256'], 'actual_shared_startup_binding')\n"
            "    strong_source = inspect.getsource(astra.existing.strong)",
    }
    for before, after in changes.items():
        if text.count(before) != 1:
            raise ValueError('exact_shared_broker_delta')
        text = text.replace(before, after)
    return text


if __name__ == '__main__':
    exec(compile(source(), __file__, 'exec'), {'__name__': '__main__', '__file__': __file__})
