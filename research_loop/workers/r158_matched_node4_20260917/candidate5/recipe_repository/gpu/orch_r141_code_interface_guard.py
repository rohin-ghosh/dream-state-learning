"""R141 source-specific adapter of the immutable physical7 R133/R136 guard."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import FunctionType

from gpu import orch_r133_code_feedback_guard as frozen
from gpu import orch_r141_code_interface as collection


GPU_UUID = frozen.GPU_UUID
HARD_END_UNIX = datetime(2026, 9, 16, 5, 40, tzinfo=timezone.utc).timestamp()
NEXT_RESERVED_UNIX = datetime(2026, 9, 16, 6, tzinfo=timezone.utc).timestamp()


def validate_scope(config, now):
    frozen.validate_scope(config, now)
    collection.require(config['hard_end_unix'] <= HARD_END_UNIX
                       and config['next_reserved_unix'] == NEXT_RESERVED_UNIX,
                       'R141_0540_ceiling_0600_reservation')


_namespace = dict(frozen.__dict__, __file__=__file__, collection=collection,
                  validate_scope=validate_scope)
validate = FunctionType(frozen.validate.__code__, _namespace, 'validate')
_namespace['validate'] = validate
scan = FunctionType(frozen.scan.__code__, _namespace, 'scan')
_constants = frozen.supervise.__code__.co_consts
collection.require(_constants.count('gpu.orch_r133_code_feedback_guard') == 1,
                   'exact_single_frozen_native_module_constant')
_supervise_code = frozen.supervise.__code__.replace(co_consts=tuple(
    'gpu.orch_r141_code_interface_guard' if value == 'gpu.orch_r133_code_feedback_guard' else value
    for value in _constants))
supervise = FunctionType(_supervise_code, _namespace, 'supervise')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('scan', 'supervise', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'scan':
        print(json.dumps(scan(arguments.config), sort_keys=True))
    elif arguments.action == 'native':
        config, authorization = validate(arguments.config)
        frozen.await_startup(config, sys.stdin)
        frozen.validate_native_entry(arguments.config, config)
        collection.collect(Path(config['output_root']), authorization, expected_gpu_uuid=GPU_UUID)
    else:
        supervise(arguments.config)


if __name__ == '__main__':
    main()
