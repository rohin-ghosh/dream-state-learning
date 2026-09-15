"""Atomic publication for future requests of the original node3 grid life."""

import argparse
from pathlib import Path

from gpu import orch_r111_grid_atomic_broker as prior
from gpu import orch_r118_node3_5_grid_recover as recovery


ORIGINAL_STORE = prior.old.Store


class AtomicStore(prior.AtomicStore):
    def exists(self, path):
        if Path(path) == prior.old.ROOT / 'TERMINAL.json':
            path = prior.old.ROOT / recovery.TERMINAL
        return ORIGINAL_STORE.exists(self, path)


def serve(wrappers, buffer):
    old_store = prior.old.Store
    prior.old.require(prior.old.sha(prior.old.__file__) ==
        '23d6c95699f0416b4b87416846f30ce694b0b353c1034ef26f24cbebe29d036a',
        'exact_original_provider_policy')
    prior.old.Store = AtomicStore
    try:
        prior.old.serve(wrappers, 'ovx2', buffer)
    finally:
        prior.old.Store = old_store


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wrappers', type=Path, required=True)
    parser.add_argument('--buffer', type=Path, required=True)
    args = parser.parse_args()
    serve(args.wrappers, args.buffer)
