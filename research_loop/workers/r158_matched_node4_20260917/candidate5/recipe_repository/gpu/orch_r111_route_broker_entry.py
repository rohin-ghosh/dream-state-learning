"""Use immutable parent source with the existing authorized wrapper checkout."""

import argparse
from pathlib import Path

from gpu import orch_r110_claude_broker as transport
from gpu import orch_r111_route_astra_broker as astra


def serve(config, launch_receipt, prompt_root, principles, repository, provider):
    repository = repository.resolve(strict=True)
    for relative in ('gpu/ovx3_ssh.sh', 'gpu/ovx3_scp.sh'):
        transport.require(transport.sha(repository/relative) == transport.sha(transport.ROOT/relative),
                          'authorized_wrapper_source_binding')
    original = transport.Store

    class ExistingWrapperStore(original):
        def __init__(self, unused):
            super().__init__(repository)

    transport.Store = ExistingWrapperStore
    try:
        backend = transport if provider == 'fable' else astra
        return backend.serve(config, launch_receipt, prompt_root, principles)
    finally:
        transport.Store = original


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'launch-receipt', 'prompt-root', 'principles', 'repository'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--provider', choices=('fable', 'astra'), required=True)
    serve(**vars(parser.parse_args()))
