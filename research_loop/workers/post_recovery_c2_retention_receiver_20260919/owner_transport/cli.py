"""C2 owner transport entrypoints. Mutations require explicit pinned Main inputs."""

import argparse
import json
from pathlib import Path
import sys

import common as core
from common import literal, pinned, read, reference, require, write_once

sys.path.insert(0, str(core.REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'inspect', 'disable', 'fence', 'owner-check', 'rebind',
        'publisher', 'serve', 'enable-successor', 'coordinate'))
    for name in ('plan', 'plan-sha256', 'approval', 'approval-sha256', 'dependency', 'dependency-sha256',
            'binding', 'binding-sha256', 'receipt', 'receipt-sha256', 'manifest', 'manifest-sha256',
            'service-receipt', 'service-receipt-sha256', 'configuration', 'configuration-sha256', 'execution-sha256'):
        parser.add_argument('--' + name)
    arguments = parser.parse_args()
    def selected(name):
        path, expected = getattr(arguments, name), getattr(arguments, name + '_sha256')
        require(path is not None and expected is not None, 'explicit_' + name + '_reference')
        return dict(path=path, sha256=expected)
    operation = arguments.operation
    if operation == 'coordinate':
        from integration import build
        from coordinator import coordinate
        configuration = pinned(selected('configuration'))
        require(arguments.execution_sha256 is not None, 'exact_Main_execution_approval')
        result = coordinate(configuration, build(configuration, arguments.execution_sha256))
    elif operation in ('publisher', 'serve'):
        from successor import publisher, serve
        result = publisher(selected('receipt'), selected('manifest')) if operation == 'publisher' else serve(selected('receipt'))
    elif operation == 'owner-check':
        from owner import LinuxCPU
        from transport import owner_exchange
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024, 'bounded_owner_request')
        result = owner_exchange(json.loads(raw), selected('dependency'), LinuxCPU())
    else:
        from owner import LinuxCPU, disable, fence, inventory, validate
        from transport import Remote
        plan = pinned(selected('plan'))
        if operation == 'prepare':
            directory = literal(plan['transaction_dir'])
            require(directory.parent == core.HERE / 'transactions' and not directory.exists(), 'new_own_transaction_only')
            directory.mkdir(mode=0o700, parents=True)
            validate(plan)
            result = write_once(directory / 'PLAN.json', plan)
        elif operation == 'inspect':
            result = dict(schema='C2_OFFLINE_OWNER_PLAN_INSPECTION_V1', inventory=inventory(plan),
                actual_fence=False, readiness_granted=False, native_actions=[])
        else:
            approval = pinned(selected('approval'))
            if operation == 'disable':
                result = disable(plan, approval)
            elif operation == 'fence':
                result = fence(plan, approval, LinuxCPU(), Remote())
            elif operation == 'rebind':
                from successor import rebind
                result = rebind(plan, approval, selected('dependency'), selected('binding'), LinuxCPU(), Remote())
            else:
                from successor import enable_successor
                result = enable_successor(plan, approval, selected('receipt'), selected('service_receipt'))
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
