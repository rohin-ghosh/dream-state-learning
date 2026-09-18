"""Source-specific R142 BASE-only guard; unchanged physical7 admission and wall."""

import argparse
import json
from pathlib import Path
import sys
from types import FunctionType

from gpu import orch_r133_code_feedback_guard as frozen
from gpu import orch_r141_code_interface_guard as prior
from gpu import orch_r142_base_reasoning_collection as collection


GPU_UUID = prior.GPU_UUID
HARD_END_UNIX, NEXT_RESERVED_UNIX = prior.HARD_END_UNIX, prior.NEXT_RESERVED_UNIX
validate_scope = prior.validate_scope
_namespace = dict(frozen.__dict__, __file__=__file__, collection=collection, validate_scope=validate_scope)
validate = FunctionType(frozen.validate.__code__, _namespace, 'validate')
_namespace['validate'] = validate
scan = FunctionType(frozen.scan.__code__, _namespace, 'scan')
_constants = frozen.supervise.__code__.co_consts
collection.require(_constants.count('gpu.orch_r133_code_feedback_guard') == 1, 'exact_single_native_module_constant')
_supervise_code = frozen.supervise.__code__.replace(co_consts=tuple(
    'gpu.orch_r142_base_reasoning_guard' if value == 'gpu.orch_r133_code_feedback_guard' else value
    for value in _constants))
supervise = FunctionType(_supervise_code, _namespace, 'supervise')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('scan', 'supervise', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'scan':
        print(json.dumps(scan(args.config), sort_keys=True))
    elif args.action == 'native':
        config, authorization = validate(args.config)
        frozen.await_startup(config, sys.stdin)
        frozen.validate_native_entry(args.config, config)
        collection.collect(Path(config['output_root']), authorization, expected_gpu_uuid=GPU_UUID)
    else:
        supervise(args.config)


if __name__ == '__main__':
    main()
