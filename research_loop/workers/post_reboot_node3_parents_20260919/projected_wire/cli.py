"""Offline-capable operator commands; no service launcher or network listener."""

import argparse
import os
from pathlib import Path
import sys

from .contract import MAX_TRANSFER_BYTES, bounded, canonical, collect, decode, source_digest, validate_receipt
from .custody import OwnerStore, load_binding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('source-digest', 'collect', 'install'))
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--binding-sha256')
    parser.add_argument('--store', type=Path)
    arguments = parser.parse_args()
    if arguments.operation == 'source-digest':
        print(source_digest())
        return
    if arguments.binding is None or arguments.binding_sha256 is None:
        parser.error('owner binding and independently pinned digest required')
    binding = load_binding(arguments.binding, os.getuid(), arguments.binding_sha256)
    raw = bounded(sys.stdin.buffer.read(MAX_TRANSFER_BYTES + 1))
    value = decode(raw)
    if arguments.operation == 'collect':
        result = collect(binding, value)
    else:
        if arguments.store is None:
            parser.error('existing owner-only custody store required')
        validate_receipt(value, binding)
        store = OwnerStore(arguments.store, os.getuid())
        try:
            result = dict(attestation_sha256=store.install(value), binding_sha256=value['binding_sha256'])
        finally:
            store.close()
    sys.stdout.buffer.write(bounded(canonical(result)))


if __name__ == '__main__':
    main()
