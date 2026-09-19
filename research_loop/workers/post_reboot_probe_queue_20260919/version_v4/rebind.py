"""Explicit reviewed rebind only; never start or stop a process."""

import argparse
from pathlib import Path

from daemon import singleton, verify_freeze
import probe_runtime as runtime
from store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("state", "policy", "review", "freeze"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    review = runtime.read(args.review)
    verify_freeze(args.freeze, review["source_freeze_sha256"])
    with singleton(args.state):
        store = Store(args.state)
        try:
            store.verify_events()
            store.rebind(runtime.read(args.policy), review)
        finally:
            store.close()


if __name__ == "__main__":
    main()
