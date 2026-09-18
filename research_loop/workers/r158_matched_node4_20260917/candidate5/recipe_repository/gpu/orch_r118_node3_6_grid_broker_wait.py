"""Next broker snapshot: bounded same-lock waiting, no retry or native changes."""

import argparse
from pathlib import Path
from types import FunctionType

from gpu import orch_r111_route_astra_broker as wait_source
from gpu import orch_r115_grid_astra as astra
from gpu import orch_r118_node3_6_grid_broker as previous


def evaluator():
    code = wait_source.evaluate.__code__
    replacements = {'F1': 'F4', 'route': 'grid', 'F1_only': 'F4_only'}
    previous.run.require(all(code.co_consts.count(key) == 1 for key in replacements),
                         'exact_wait_evaluator_family_constants')
    code = code.replace(co_consts=tuple(replacements.get(value, value) if isinstance(value, str)
                                       else value for value in code.co_consts))
    return FunctionType(code, dict(wait_source.evaluate.__globals__, parse=astra.parse,
        transport=astra.transport, authorize=astra.authorize), 'evaluate', wait_source.evaluate.__defaults__,
        closure=wait_source.evaluate.__closure__)


evaluate = evaluator()
evaluate.__kwdefaults__ = wait_source.evaluate.__kwdefaults__


def serve(config_path, launch_path, prompt_root, principles_path):
    config = astra.transport.loads(Path(config_path).read_text())
    previous.run.require(config['remote_root'] == str(previous.run.ROOT)
        and config['life_id'] == previous.run.LIFE_ID, 'exact_new_node3_6_parent_lane')
    namespace = dict(astra.transport.serve.__globals__, Store=previous.Store,
                     evaluate=evaluate, validate_launch=astra.authorize)
    namespace['process_request'] = FunctionType(astra.transport.process_request.__code__, namespace,
        'process_request', astra.transport.process_request.__defaults__)
    return FunctionType(astra.transport.serve.__code__, namespace, 'serve',
                        astra.transport.serve.__defaults__)(config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
