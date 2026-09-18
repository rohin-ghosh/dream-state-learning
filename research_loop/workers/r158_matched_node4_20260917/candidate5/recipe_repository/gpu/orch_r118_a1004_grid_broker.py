"""A100-only queue transport for the existing fixed-v4 Astra grid parent."""

import argparse
from pathlib import Path
import subprocess
from types import FunctionType

from gpu import orch_r115_grid_astra as astra
from gpu import orch_r118_a1004_grid_run as run


class Store(astra.transport.Store):
    def shell(self, script, check=True):
        return subprocess.run(['bash', str(self.repository / 'gpu/a100_ssh.sh'), script],
            text=True, capture_output=True, timeout=20, check=check)

    def copy(self, source, destination):
        subprocess.run(['bash', str(self.repository / 'gpu/a100_scp.sh'), str(source), str(destination)],
            capture_output=True, timeout=20, check=True)


def serve(config_path, launch_path, prompt_root, principles_path):
    config = astra.transport.loads(Path(config_path).read_text())
    run.require(config['remote_root'] == str(run.ROOT) and config['life_id'] == run.LIFE_ID,
                'exact_new_A1004_parent_lane')
    namespace = dict(astra.transport.serve.__globals__, Store=Store, evaluate=astra.evaluate,
                     validate_launch=astra.authorize)
    namespace['process_request'] = FunctionType(astra.transport.process_request.__code__, namespace,
        'process_request', astra.transport.process_request.__defaults__)
    bound = FunctionType(astra.transport.serve.__code__, namespace, 'serve', astra.transport.serve.__defaults__)
    return bound(config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
